# SQL Scripts Delivery — Auth Module (TASK-003)

**Date**: 2026-04-27  
**Status**: Complete  

---

## Overview

This directory contains the SQL migration and reference scripts for the Auth module. All schema changes are managed via Alembic (SQLAlchemy migration tool) and are version-controlled in the application repository.

---

## Migration Files

### Reference Migration: `0005_create_user.py`

**Location**: `clinic-cms/alembic/versions/0005_create_user.py`  
**Revision ID**: `0005`  
**Depends On**: `0004` (Clinic)  
**Status**: Applied to all development/staging/production databases  

**What It Creates**:
1. `user` table with all columns (auth + doctor-specific fields)
2. Partial unique indexes (username, email per clinic for non-deleted rows)
3. Composite index for common query pattern (clinic_id + is_active)
4. Row-Level Security (RLS) policy for tenant isolation
5. Database role grants (`cms_app`)

---

## How to Apply

### Development (Docker)

```bash
cd clinic-cms
docker compose up -d  # Start DB + app
docker compose exec api alembic upgrade head  # Run all pending migrations
```

### Manual Application (via psql)

If you need to apply migrations manually:

```bash
# Connect to PostgreSQL
psql -h <host> -U <user> -d <dbname>

# Create user table (if 0005 hasn't been applied)
-- (Run the DDL statements from 0005_create_user.py upgrade() function)

-- Or use Alembic directly
alembic upgrade 0005
```

### Reverting

```bash
alembic downgrade 0004  # Revert to pre-0005 state (drops user table)
```

---

## Schema Details

### Table: `user`

See `docs/tasks/TASK-003/deliveries/final-specs/auth-functional-design.md` Section 6 for full column definitions.

**Key Columns for Auth**:
- `password_hash` (VARCHAR 255): bcrypt hash, cost 12
- `is_active` (BOOLEAN): Admin flag to deactivate account
- `is_locked` (BOOLEAN): Auto-set after ≥5 failed login attempts
- `failed_login_count` (INT): Counter (reset after success or window expiry)
- `last_login_at` (TIMESTAMPTZ): Audit field
- `password_changed_at` (TIMESTAMPTZ): Password change timestamp

**Doctor-specific Columns**:
- `license_number` (VARCHAR 100)
- `specialty_subfield` (VARCHAR 200)

---

## Indexes Explained

### Partial Unique Index: `uq_user_clinic_username`

```sql
CREATE UNIQUE INDEX uq_user_clinic_username 
  ON "user" (clinic_id, username) 
  WHERE NOT is_deleted
```

**Why Partial?**
- Soft-deleted users don't count toward uniqueness
- Allows re-use of username if user is deleted (then restored with different password)
- Enforces username uniqueness **per clinic** (multi-tenant isolation)

**Query Pattern**:
```sql
SELECT * FROM "user" 
WHERE clinic_id = $1 AND username = $2 AND is_deleted = false
```

### Partial Unique Index: `uq_user_clinic_email`

```sql
CREATE UNIQUE INDEX uq_user_clinic_email 
  ON "user" (clinic_id, email) 
  WHERE email IS NOT NULL AND NOT is_deleted
```

**Why Partial?**
- Only enforces uniqueness when email is not NULL
- Allows multiple users with NULL email (staff without email contact)
- Soft-delete compatible

### Composite Index: `ix_user_clinic_id_is_active`

```sql
CREATE INDEX ix_user_clinic_id_is_active ON "user" (clinic_id, is_active)
```

**Use Case**: Query active users per clinic (common in user listing, role assignment)
```sql
SELECT * FROM "user" 
WHERE clinic_id = $1 AND is_active = true AND is_deleted = false
```

---

## Row-Level Security (RLS)

### Tenant Isolation Policy

Applied via `apply_rls_with_tenant_isolation(op, '"user"')` in migration 0005.

**Effect**:
```sql
-- Only users in the same clinic can see each other's records
-- PostgreSQL enforces this at the database level (not application level)

-- Example: User from Clinic A queries user table
SELECT * FROM "user" WHERE clinic_id = <Clinic B ID>  
-- → Returns empty (RLS filters rows)
```

**Configuration**: Done in `app/core/rls.py` (reference in migration)

---

## Database Role & Permissions

### `cms_app` Role Grants

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON "user" TO cms_app;
```

The application connects as `cms_app` role, which has full DML permissions on `user` table.

**Note**: DDL (CREATE, ALTER, DROP) is restricted to migration runner (usually `postgres` superuser).

---

## Data Validation & Constraints

### Foreign Key

```sql
CONSTRAINT fk_user_clinic_id_clinic
FOREIGN KEY (clinic_id) 
REFERENCES clinic(id) 
ON DELETE RESTRICT
```

- **Prevents**: Deleting a clinic while users exist
- **Action**: Raise foreign key violation error
- Alternative in future: `ON DELETE CASCADE` (delete all clinic users) or `ON DELETE SET NULL` (orphan users) — current design is safest

### Primary Key

```sql
CONSTRAINT pk_user
PRIMARY KEY (id)
```

`id` is a UUID, generated application-side or via `gen_random_uuid()`.

---

## Audit & Versioning

### Audit Columns (inherited from BaseEntity)

- `created_at`, `updated_at`: Timestamps
- `created_by`, `updated_by`: UUIDs of who made changes
- `version`: Optimistic lock counter (incremented on each update)

**Audit Log Table**: Separate `audit_log` table (TASK-002) captures all changes (INSERT, UPDATE, DELETE).

### Soft Delete

- `is_deleted` (BOOLEAN): Logical deletion flag
- `deleted_at` (TIMESTAMPTZ): When deleted
- `deleted_by` (UUID): Who deleted

**Query Pattern**: Always include `WHERE is_deleted = false` to exclude deleted records.

---

## Testing & Sample Data

### Create Test User

```sql
-- Create clinic first (from TASK-002)
INSERT INTO clinic (id, code, name, is_active, created_at, updated_at, is_deleted, version)
VALUES (
  '332eed96-5ace-41de-b91e-909a396d1b35',
  'CLI001',
  'Sample Clinic',
  true,
  now(),
  now(),
  false,
  1
);

-- Create test user
INSERT INTO "user" (
  id, clinic_id, username, full_name, password_hash, is_active, is_locked, 
  failed_login_count, created_at, updated_at, is_deleted, version
) VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  '332eed96-5ace-41de-b91e-909a396d1b35',
  'dr_john',
  'Dr. John Doe',
  '$2b$12$...',  -- bcrypt hash of "SecurePass123!"
  true,
  false,
  0,
  now(),
  now(),
  false,
  1
);
```

### Reset Lockout (Admin Manual Fix)

```sql
-- Unlock a user
UPDATE "user" 
SET is_locked = false, failed_login_count = 0, updated_at = now() 
WHERE id = '550e8400-e29b-41d4-a716-446655440000' 
AND clinic_id = '332eed96-5ace-41de-b91e-909a396d1b35';

-- Delete Redis lockout counter (if direct Redis access)
redis-cli DEL "lockout:332eed96-5ace-41de-b91e-909a396d1b35:dr_john"
```

---

## Performance Notes

### Index Statistics

For large user bases (>10k users):
```sql
-- Refresh index statistics (PostgreSQL query planner optimization)
ANALYZE "user";
```

### Partial Index Benefits

- Smaller index size (only non-deleted rows indexed)
- Faster inserts/updates (less overhead)
- Faster lookups on active users (partial index matches query predicate)

---

## Related Documentation

- **Functional Design**: `docs/tasks/TASK-003/deliveries/final-specs/auth-functional-design.md`
- **API Spec**: `docs/tasks/TASK-003/deliveries/api-specs/auth-api.md`
- **Base Model**: `clinic-cms/app/core/base_model.py` (BaseEntity, mixins)
- **RLS Config**: `clinic-cms/app/core/rls.py`
- **Alembic**: `clinic-cms/alembic/` (migration framework)

---

## Known Limitations & Future

1. **Email as unique per clinic**: Currently optional (NULL allowed). In v2, may require all users to have email.
2. **Doctor-specific fields**: Currently optional. Future phase may integrate with actual doctor registry.
3. **Multi-clinic users**: Not supported in v1. Phase 2 may allow one user across multiple clinics (different roles/permissions per clinic).
4. **Temporal auditing**: Current audit logs don't support full temporal queries ("who was active at time T?"). Phase 2 may add `validity_period` fields.

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-27  
**Created By**: Code Implementation Agent + Documentation Agent
