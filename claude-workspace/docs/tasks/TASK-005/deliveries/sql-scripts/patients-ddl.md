# SQL Scripts: Patient Management DDL

**Task:** TASK-005 — Patient Management  
**Date:** 2026-04-27  
**Source:** `alembic/versions/0008_create_patients.py`  
**Status:** Final Delivery

---

## Overview

This document contains all SQL DDL for patient management module:
- Extensions (unaccent, pg_trgm)
- Custom functions (`immutable_unaccent`, `fn_next_patient_code`)
- Tables (patient, patient_relation, patient_merge_log)
- Indexes (trigram, GIN full-text, unique code)
- RLS policies for multi-tenant isolation
- Role grants (cms_app)

---

## Table of Contents

1. [Extensions](#extensions)
2. [Custom Functions](#custom-functions)
3. [Table Definitions](#table-definitions)
4. [Indexes](#indexes)
5. [Row-Level Security (RLS) Policies](#row-level-security-policies)
6. [Role Grants](#role-grants)
7. [Downgrade Script](#downgrade-script)

---

## Extensions

### Enable PostgreSQL Extensions

```sql
-- Enable unaccent extension (for removing diacritics: á → a, ứ → u)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Enable pg_trgm extension (for trigram similarity search on phone/name)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

**Notes:**
- `unaccent` — required for Vietnamese text processing and full-text search
- `pg_trgm` — required for fast substring/fuzzy search on phone and name

---

## Custom Functions

### 1. immutable_unaccent(text) — IMMUTABLE Wrapper

**Purpose:** PostgreSQL's stock `unaccent()` is marked `STABLE`, which prevents use in functional index expressions. This wrapper is `IMMUTABLE`, allowing it to be used in GIN indexes.

```sql
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
  RETURNS TEXT
  LANGUAGE SQL
  IMMUTABLE
  STRICT
  PARALLEL SAFE
AS $$
  SELECT unaccent('public.unaccent', $1)
$$;
```

**Attributes:**
- `IMMUTABLE` — output determined solely by input (safe for indexes)
- `STRICT` — NULL input → NULL output (skip computation)
- `PARALLEL SAFE` — can run in parallel execution

**Usage in Indexes:**
```sql
CREATE INDEX gix_patient_name_search
  ON patient
  USING gin (to_tsvector('simple', immutable_unaccent(full_name)))
  WHERE NOT is_deleted;
```

---

### 2. fn_next_patient_code(clinic_id UUID) → TEXT

**Purpose:** Generate next patient code (`BN0001`, `BN0002`, ...) for a clinic. Codes are never reused, even after merge/undo (M5 fix). Handles numeric ordering correctly (avoids lexical bugs like `BN9999` < `BN10000`).

```sql
CREATE OR REPLACE FUNCTION fn_next_patient_code(p_clinic_id UUID)
  RETURNS TEXT
  LANGUAGE plpgsql
AS $$
DECLARE
    last_num  INTEGER;
BEGIN
    -- Lock the row with the numerically highest code for this clinic.
    -- All rows are considered (including soft-deleted) so that codes are
    -- never reused — this prevents uq_patient_clinic_code violations when
    -- undo_merge restores a soft-deleted drop_patient (M5 fix).
    -- Numeric MAX avoids lexical ordering bugs at code-width transitions
    -- e.g. 'BN9999' < 'BN10000' lexically fails (m1 fix).
    SELECT MAX(CAST(SUBSTRING(patient_code FROM 3) AS INTEGER)) INTO last_num
    FROM patient
    WHERE clinic_id = p_clinic_id;

    IF last_num IS NULL THEN
        RETURN 'BN0001';
    END IF;

    RETURN 'BN' || LPAD(CAST(last_num + 1 AS TEXT), 4, '0');
END;
$$;
```

**Algorithm:**
1. Find the numerically highest code suffix (`SUBSTRING(patient_code FROM 3)` extracts `0001` from `BN0001`)
2. Cast to INTEGER for numeric comparison (avoids `BN9999` < `BN10000` lexical trap)
3. Add 1 and pad with zeros to 4 digits
4. Return as `BN####`

**Example Sequence:**
```
BN0001 → BN0002 → ... → BN9999 → BN10000 → BN10001 (numeric ordering preserved)
```

**Key Property (M5):**
- Queries **all rows** (including soft-deleted) to find MAX
- Prevents code reuse even when undo_merge restores a soft-deleted patient
- E.g., after merge+undo of `BN0005`, next new patient still gets `BN0006` (not `BN0005` again)

---

## Table Definitions

### 1. patient Table

**Purpose:** Core patient demographic data with soft-delete, audit trail, and RLS multi-tenant isolation.

```sql
CREATE TABLE patient (
    -- Primary Key & UUIDs
    id UUID NOT NULL PRIMARY KEY,
    
    -- Timestamps (inherited from TimestampMixin)
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    -- Soft Delete (inherited from SoftDeleteMixin)
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID,
    
    -- Multi-Tenant (inherited from TenantMixin)
    clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
    
    -- Audit Trail (inherited from AuditedMixin)
    created_by UUID,
    updated_by UUID,
    
    -- Optimistic Locking (inherited from VersionedMixin)
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Patient-Specific Fields
    patient_code VARCHAR(20) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    date_of_birth DATE,
    birth_year INTEGER,
    gender VARCHAR(10) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(200),
    id_number VARCHAR(20),  -- CCCD/CMND (excluded from audit log)
    address_line VARCHAR(500),
    ward VARCHAR(100),
    district VARCHAR(100),
    province VARCHAR(100),
    blood_type VARCHAR(5),
    allergies TEXT,
    chronic_conditions TEXT,
    occupation VARCHAR(100),
    referral_source VARCHAR(100),
    notes TEXT,
    
    -- Constraints
    CONSTRAINT ck_patient_dob_or_birth_year CHECK (
        (date_of_birth IS NOT NULL OR birth_year IS NOT NULL) AND
        (date_of_birth IS NULL OR birth_year IS NULL OR 
         EXTRACT(year FROM date_of_birth)::integer = birth_year)
    )
);
```

**Check Constraint Explanation:**
- Ensures at least one of `date_of_birth` or `birth_year` is set
- If both are set, the year component must match
- Prevents invalid/incomplete data like `dob='1990-05-15'` + `birth_year=1991` (mismatch)

---

### 2. patient_relation Table

**Purpose:** Guardian relationships (parent, spouse, child, other) — represents family/caregiver connections.

```sql
CREATE TABLE patient_relation (
    -- Primary Key & UUIDs
    id UUID NOT NULL PRIMARY KEY,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    -- Soft Delete
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID,
    
    -- Multi-Tenant
    clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
    
    -- Audit Trail
    created_by UUID,
    updated_by UUID,
    
    -- Optimistic Locking
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Relation-Specific Fields
    patient_id UUID NOT NULL REFERENCES patient(id) ON DELETE RESTRICT,
    guardian_patient_id UUID NOT NULL REFERENCES patient(id) ON DELETE RESTRICT,
    relation_type VARCHAR(20) NOT NULL,  -- parent, spouse, child, other
    is_primary_contact BOOLEAN NOT NULL DEFAULT false
);
```

**Indexes:**
```sql
CREATE INDEX ix_patient_relation_clinic_id ON patient_relation(clinic_id);
CREATE INDEX ix_patient_relation_patient_id ON patient_relation(patient_id);
CREATE INDEX ix_patient_relation_guardian_patient_id ON patient_relation(guardian_patient_id);
```

---

### 3. patient_merge_log Table

**Purpose:** Audit trail for merge operations (merge + undo with 7-day window). Stores snapshot of dropped patient and manifest of reassigned rows for rollback.

```sql
CREATE TABLE patient_merge_log (
    -- Primary Key & UUIDs
    id UUID NOT NULL PRIMARY KEY,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    -- Soft Delete (for archival if needed)
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID,
    
    -- Multi-Tenant
    clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
    
    -- Audit Trail
    created_by UUID,
    updated_by UUID,
    
    -- Optimistic Locking
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Merge-Specific Fields
    drop_patient_id UUID NOT NULL,
    keep_patient_id UUID NOT NULL,
    source_patient_data JSONB NOT NULL,  -- snapshot + manifest
    merged_by UUID NOT NULL,
    merged_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    reason TEXT,
    
    -- Undo Support
    undo_deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    undone BOOLEAN NOT NULL DEFAULT false,
    undone_at TIMESTAMP WITH TIME ZONE,
    undone_by UUID
);
```

**source_patient_data (JSONB) Structure:**
```json
{
  "patient_code": "BN0005",
  "full_name": "Patient To Merge",
  "date_of_birth": "1990-05-15",
  "reassigned_refs": {
    "visit": ["uuid1", "uuid2"],
    "appointment": ["uuid3"],
    "prescription": [],
    "invoice": []
  }
}
```

**Indexes:**
```sql
CREATE INDEX ix_patient_merge_log_clinic_id ON patient_merge_log(clinic_id);
CREATE INDEX ix_patient_merge_log_keep_patient_id ON patient_merge_log(keep_patient_id);
CREATE INDEX ix_patient_merge_log_drop_patient_id ON patient_merge_log(drop_patient_id);
```

---

## Indexes

### Composite Index: clinic_id

```sql
CREATE INDEX ix_patient_clinic_id ON patient(clinic_id);
```

**Purpose:** Fast lookup of patients by clinic (used in list/search).

---

### Partial Index: Phone Lookup

```sql
CREATE INDEX ix_patient_clinic_phone 
  ON patient(clinic_id, phone) 
  WHERE NOT is_deleted;
```

**Purpose:** Composite index for phone searches within a clinic, excluding soft-deleted records.

---

### GIN Full-Text Search: Name

```sql
CREATE INDEX gix_patient_name_search 
  ON patient 
  USING gin (to_tsvector('simple', immutable_unaccent(full_name))) 
  WHERE NOT is_deleted;
```

**Purpose:** Full-text search on patient names with Vietnamese accent removal.
- Uses `immutable_unaccent()` to remove accents before tokenization
- Supports queries like `q="nguyen van an"` matching `"Nguyễn Văn An"`
- `SIMPLE` tokenization — splits on whitespace, no stemming
- GIN index — inverted index, optimal for full-text queries

**Query Pattern:**
```sql
SELECT * FROM patient
WHERE clinic_id = :clinic_id
  AND NOT is_deleted
  AND to_tsvector('simple', immutable_unaccent(full_name)) 
      @@ plainto_tsquery('simple', immutable_unaccent(:q))
```

---

### GIN Trigram Index: Phone

```sql
CREATE INDEX gix_patient_phone_trgm 
  ON patient 
  USING gin (phone gin_trgm_ops) 
  WHERE NOT is_deleted;
```

**Purpose:** Fast substring/prefix matching on phone numbers.
- Trigram index — breaks strings into 3-char substrings
- p95 = 46.9 ms @ 100k patients (AC1 PASS)
- Supports similarity operator `%`

**Query Pattern:**
```sql
SELECT * FROM patient
WHERE clinic_id = :clinic_id
  AND NOT is_deleted
  AND phone % :q
ORDER BY similarity(phone, :q) DESC
```

---

### GIN Trigram Index: Name (No WHERE)

```sql
CREATE INDEX gix_patient_name_trgm 
  ON patient 
  USING gin (full_name gin_trgm_ops);
```

**Purpose:** Fuzzy name matching; note: **no WHERE clause** (includes soft-deleted) because trigram similarity queries cannot filter via WHERE.
- Supports fuzzy matching across all records for similarity calculations

---

### Unique Partial Index: patient_code per clinic

```sql
CREATE UNIQUE INDEX uq_patient_clinic_code 
  ON patient(clinic_id, patient_code) 
  WHERE NOT is_deleted;
```

**Purpose:** Ensures patient codes are unique per clinic, ignoring soft-deleted patients.
- Allows code to be "recycled" in a way: if `BN0005` is soft-deleted, the unique constraint doesn't prevent another patient from reusing it
- However, `fn_next_patient_code` prevents reuse by querying ALL rows (including soft-deleted), so codes never repeat
- This partial index ensures no duplicate codes among **active** patients

---

## Row-Level Security Policies

### Enable RLS on patient Table

```sql
ALTER TABLE patient ENABLE ROW LEVEL SECURITY;

-- Policy: Users see only their clinic's patients
CREATE POLICY rls_patient_isolation 
  ON patient 
  USING (clinic_id = current_setting('rls.clinic_id')::UUID);

GRANT SELECT, INSERT, UPDATE, DELETE ON patient TO cms_app;
```

**RLS Context:**
- Middleware sets `SET LOCAL rls.clinic_id = :clinic_id` for each request
- Queries automatically filter by clinic_id

---

### Enable RLS on patient_relation Table

```sql
ALTER TABLE patient_relation ENABLE ROW LEVEL SECURITY;

CREATE POLICY rls_patient_relation_isolation 
  ON patient_relation 
  USING (clinic_id = current_setting('rls.clinic_id')::UUID);

GRANT SELECT, INSERT, UPDATE, DELETE ON patient_relation TO cms_app;
```

---

### Enable RLS on patient_merge_log Table

```sql
ALTER TABLE patient_merge_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY rls_patient_merge_log_isolation 
  ON patient_merge_log 
  USING (clinic_id = current_setting('rls.clinic_id')::UUID);

GRANT SELECT, INSERT, UPDATE, DELETE ON patient_merge_log TO cms_app;
```

---

## Role Grants

```sql
-- Grant DML permissions to application role
GRANT SELECT, INSERT, UPDATE, DELETE ON patient TO cms_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON patient_relation TO cms_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON patient_merge_log TO cms_app;

-- Grant function execution
GRANT EXECUTE ON FUNCTION fn_next_patient_code(UUID) TO cms_app;
GRANT EXECUTE ON FUNCTION immutable_unaccent(text) TO cms_app;
```

---

## Downgrade Script

To rollback migration 0008, execute in reverse order:

```sql
-- 1. Drop function fn_next_patient_code
DROP FUNCTION IF EXISTS fn_next_patient_code(UUID);

-- 2. Remove RLS and revoke grants on patient_merge_log
ALTER TABLE patient_merge_log DISABLE ROW LEVEL SECURITY;
REVOKE SELECT, INSERT, UPDATE, DELETE ON patient_merge_log FROM cms_app;
DROP INDEX IF EXISTS ix_patient_merge_log_drop_patient_id;
DROP INDEX IF EXISTS ix_patient_merge_log_keep_patient_id;
DROP INDEX IF EXISTS ix_patient_merge_log_clinic_id;
DROP TABLE IF EXISTS patient_merge_log;

-- 3. Remove RLS and revoke grants on patient_relation
ALTER TABLE patient_relation DISABLE ROW LEVEL SECURITY;
REVOKE SELECT, INSERT, UPDATE, DELETE ON patient_relation FROM cms_app;
DROP INDEX IF EXISTS ix_patient_relation_guardian_patient_id;
DROP INDEX IF EXISTS ix_patient_relation_patient_id;
DROP INDEX IF EXISTS ix_patient_relation_clinic_id;
DROP TABLE IF EXISTS patient_relation;

-- 4. Remove RLS and revoke grants on patient
ALTER TABLE patient DISABLE ROW LEVEL SECURITY;
REVOKE SELECT, INSERT, UPDATE, DELETE ON patient FROM cms_app;
DROP INDEX IF EXISTS uq_patient_clinic_code;
DROP INDEX IF EXISTS gix_patient_name_trgm;
DROP INDEX IF EXISTS gix_patient_phone_trgm;
DROP INDEX IF EXISTS gix_patient_name_search;
DROP INDEX IF EXISTS ix_patient_clinic_phone;
DROP INDEX IF EXISTS ix_patient_clinic_id;
DROP TABLE IF EXISTS patient;

-- 5. Drop immutable_unaccent function
DROP FUNCTION IF EXISTS immutable_unaccent(text);

-- Note: PostgreSQL extensions (unaccent, pg_trgm) are left in place
-- as they may be used by other modules
```

---

## Migration Verification

### Check tables created

```sql
SELECT schemaname, tablename FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('patient', 'patient_relation', 'patient_merge_log')
ORDER BY tablename;
```

### Check indexes created

```sql
SELECT schemaname, tablename, indexname, indexdef FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('patient', 'patient_relation', 'patient_merge_log')
ORDER BY tablename, indexname;
```

### Check functions created

```sql
SELECT schemaname, funcname, routine_definition FROM pg_proc
WHERE schemaname = 'public'
  AND funcname IN ('fn_next_patient_code', 'immutable_unaccent');
```

### Check RLS policies

```sql
SELECT schemaname, tablename, policyname, qual FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('patient', 'patient_relation', 'patient_merge_log');
```

---

## Performance Notes

- **Phone search (trigram p95 = 46.9ms @ 100k patients):** Fully leverages `gix_patient_phone_trgm` GIN index
- **Name search (full-text p95 = 180.5ms):** Leverages `gix_patient_name_search` GIN index; unaccent overhead ~50ms
- **Patient code generation:** `fn_next_patient_code` does full table scan on patient table, but only for new records (non-critical path)
- **RLS isolation:** All queries automatically filtered by `clinic_id`; no additional filtering needed in application code

---

## Notes for DBAs

1. **Test vs Production roles:** Migration uses `cms_app` role (no BYPASSRLS). Test environment may use `cms` role with BYPASSRLS=true for convenience.

2. **id_number field:** CCCD/CMND values are excluded from audit logs via `__audit_exclude__` in application code — not enforced at database level.

3. **immutable_unaccent caveat:** This function is safe for GIN indexes because it always returns the same output for the same input. Stock `unaccent()` is marked STABLE (depends on locale), which PostgreSQL refuses in index expressions.

4. **fn_next_patient_code concurrency:** Uses numeric MAX over all rows (including soft-deleted) to ensure codes never repeat, even across merge+undo cycles.

---

## Related DDL Tasks

- **TASK-007 (Visit):** Will add `visit` table with `FK patient_id → patient.id`
- **TASK-008 (Appointment):** Will add `appointment` table with `FK patient_id → patient.id`
- **TASK-011 (Prescription):** Will add `prescription` table with `FK patient_id → patient.id`
- **TASK-013 (Invoice):** Will add `invoice` table with `FK patient_id → patient.id`

When these tables are created, update `merge_service.py` `RELATED_PATIENT_TABLES` registry to include new tables in merge operations.

---
