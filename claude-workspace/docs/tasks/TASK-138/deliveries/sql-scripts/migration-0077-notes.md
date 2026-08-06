# Migration 0077 Notes: Payroll Per-Session/Per-Shift + Per-Staff Commission

**File:** `alembic/versions/0077_payroll_session_shift_staff_commission.py`
**Date:** 2026-08-06
**Revision ID:** 0077
**Revises:** 0076
**Status:** Tested & Verified

---

## Summary

Migration 0077 implements the database schema changes for TASK-138:

1. **New pay types** (`per_session` and `per_shift`) via expansion of `staff_profile.pay_type` column
2. **Per-staff commission overrides** via new `commission_rule.staff_id` column
3. **Rebuilt uniqueness constraints** on `commission_rule` to accommodate per-staff dimension

---

## Changes in Detail

### 1. `staff_profile` Table Modifications

#### 1.1 Widen `pay_type` Column

**Before:** `VARCHAR(10)` (fits `monthly`, `hourly`)
**After:** `VARCHAR(20)` (fits `monthly`, `hourly`, `per_session` — 11 chars)

```sql
ALTER TABLE staff_profile
ALTER COLUMN pay_type TYPE VARCHAR(20);
```

**Reason:** The new `per_session` value is 11 characters long and would overflow the original 10-character limit.

**Data Impact:** None — existing `monthly` and `hourly` values unaffected.

#### 1.2 Add `session_rate` Column

```sql
ALTER TABLE staff_profile
ADD COLUMN session_rate NUMERIC(15, 2) NULL;
```

**Purpose:** Stores the unit rate (VND/day) for `pay_type='per_session'` staff members.

**Data Impact:** New rows will have `NULL`; existing rows are `NULL`. When a staff member is switched to `per_session` pay type, admin must populate this column.

#### 1.3 Add `shift_rate` Column

```sql
ALTER TABLE staff_profile
ADD COLUMN shift_rate NUMERIC(15, 2) NULL;
```

**Purpose:** Stores the unit rate (VND/shift) for `pay_type='per_shift'` staff members.

**Data Impact:** New rows will have `NULL`; existing rows are `NULL`.

### 2. `commission_rule` Table Modifications

#### 2.1 Add `staff_id` Column with Foreign Key

```sql
ALTER TABLE commission_rule
ADD COLUMN staff_id UUID NULL
    REFERENCES staff_profile(id) ON DELETE CASCADE;
```

**Purpose:** Adds per-staff override dimension to commission rules.

- `staff_id = NULL`: clinic-wide rule (existing TASK-128 behavior)
- `staff_id ≠ NULL`: per-staff override for that specific staff member

**Data Impact:** Existing rows will have `staff_id = NULL`, preserving existing clinic-wide rules.

**Cascade Delete:** If a staff member is deleted from `staff_profile`, their commission overrides are automatically deleted.

#### 2.2 Create Index on `staff_id`

```sql
CREATE INDEX ix_commission_rule_staff_id ON commission_rule(staff_id);
```

**Purpose:** Improves query performance when filtering rules by staff member.

#### 2.3 Drop and Rebuild Partial Unique Indexes

**Dropped (from migration 0073):**
```sql
DROP INDEX uq_commission_rule_clinic_service_type;
DROP INDEX uq_commission_rule_clinic_medicine;
```

**Created (new, with `staff_id` dimension):**

```sql
CREATE UNIQUE INDEX uq_commission_rule_clinic_service_type_staff
  ON commission_rule (clinic_id, service_type_id, COALESCE(staff_id, '00000000-0000-0000-0000-000000000000'::uuid))
  WHERE rule_type = 'service_type' AND is_deleted = false;

CREATE UNIQUE INDEX uq_commission_rule_clinic_medicine_staff
  ON commission_rule (clinic_id, COALESCE(staff_id, '00000000-0000-0000-0000-000000000000'::uuid))
  WHERE rule_type = 'medicine' AND is_deleted = false;
```

**Rationale:** The `COALESCE(..., zero-uuid)` trick allows NULL-safe uniqueness. A clinic can now have:
- 1 clinic-wide rule (staff_id = NULL) for a service_type
- N per-staff overrides (staff_id ≠ NULL) for the same service_type
- All coexist without violating the uniqueness constraint

The zero-UUID sentinel (`00000000-0000-0000-0000-000000000000`) represents "no staff override," folding NULL into a single uniqueness bucket per clinic/service_type pair.

**Example:**
```
Clinic A, service_type_001:
├─ Rule (staff_id = NULL, rate 10%)
├─ Rule (staff_id = dr_001, rate 15%)
├─ Rule (staff_id = dr_002, rate 12%)
└─ All satisfy uniqueness: NULL → 0000..., dr_001 → dr_001, dr_002 → dr_002 (3 distinct values)
```

**Partial Index Filters:**
- `WHERE rule_type = 'service_type'`: only index service-type rules
- `WHERE is_deleted = false`: exclude soft-deleted rules

This ensures the uniqueness constraint only applies to active, non-deleted rules.

---

## Downgrade Behavior

### Downgrade Steps

When running `alembic downgrade -1`:

1. **Delete per-staff override rows** (staff_id ≠ NULL)
   ```sql
   DELETE FROM commission_rule WHERE staff_id IS NOT NULL;
   ```
   **Reason:** Pre-0077 schema has no `staff_id` column; overrides have nowhere to live.

2. **Drop new partial unique indexes** (with `staff_id` dimension)

3. **Drop `staff_id` index** and **drop `staff_id` column**

4. **Recreate old partial unique indexes** (from migration 0073, without `staff_id` dimension):
   ```sql
   CREATE UNIQUE INDEX uq_commission_rule_clinic_service_type
     ON commission_rule (clinic_id, service_type_id)
     WHERE rule_type = 'service_type' AND is_deleted = false;
   
   CREATE UNIQUE INDEX uq_commission_rule_clinic_medicine
     ON commission_rule (clinic_id)
     WHERE rule_type = 'medicine' AND is_deleted = false;
   ```

5. **Drop `shift_rate` and `session_rate` columns** from `staff_profile`

6. **Narrow `pay_type` column** back to `VARCHAR(10)`
   ```sql
   ALTER TABLE staff_profile
   ALTER COLUMN pay_type TYPE VARCHAR(10);
   ```

### Downgrade Data Loss

**⚠️ Two caveats:**

1. **Per-staff commission overrides are discarded**: Step 1 deletes all rows where `staff_id ≠ NULL`. Clinic-wide rules (staff_id = NULL) survive.

   *Expected*: Per-staff overrides are a new feature; the pre-0077 schema cannot represent them.

2. **Downgrade fails if any staff has `pay_type` in (`per_session`, `per_shift`)**: Step 6 narrows the column to `VARCHAR(10)`, which cannot fit "per_session" (11 chars). The migration will abort with a data error.

   *Documented*: Migration docstring explicitly warns about this.

---

## Operational Notes for Production Deploy

### 1. Before Deployment

- **Backup database** (standard procedure)
- **Verify no staff with `pay_type` set to `per_session` or `per_shift`** if a downgrade might be needed soon (unlikely, but good to check)

### 2. Deployment Steps

```bash
# In production environment:
cd /path/to/clinic-cms-be

# Run migrations (including 0077)
alembic upgrade head

# Verify migration succeeded
alembic current  # Should show: 0077_payroll_session_shift_staff_commission
```

### 3. After Deployment

- **Verify new columns and indexes exist:**
  ```sql
  \d staff_profile;
  \d commission_rule;
  \di | grep commission_rule;
  ```

- **Test rate resolution** (create a per-staff override, check payroll calculation)

### 4. If Downgrade is Needed

```bash
# Downgrade by one migration (0077 → 0076)
alembic downgrade -1

# Verify:
alembic current  # Should show: 0076

# Check that per-staff commission overrides were discarded:
SELECT COUNT(*) FROM commission_rule WHERE staff_id IS NOT NULL;
-- Should return 0 (or error if column still exists)
```

**Expect data loss**: Any per-staff commission rules created after 0077 was deployed will be gone.

---

## Testing Verification (from Test Agent Report)

Migration 0077 was verified end-to-end against a disposable PostgreSQL 15 instance:

- ✅ **Fresh upgrade** (0001 → 0077): schema matches design (column widths, FK, new columns, rebuilt indexes)
- ✅ **Collision scenario upgrade**: clinic-wide rule + per-staff override for same service_type coexist without constraint violation
- ✅ **Downgrade with collision data**: previously aborted (duplicate-key error on index recreation), now succeeds after fix-round-1 m2 (delete per-staff rows before recreating old indexes)
- ✅ **Re-upgrade**: succeeds cleanly after downgrade
- ✅ **Downgrade with `per_session`/`per_shift` data**: fails as documented (pay_type narrowing step aborts if any row holds new pay types)

---

## Schema Comparison

### After Migration 0077 Upgrade

**staff_profile schema (relevant columns):**
```
Column        │ Type        │ Collation │ Nullable │ Default
──────────────┼─────────────┼───────────┼──────────┼─────────
pay_type      │ varchar(20) │           │ no       │ 'monthly'::character varying
base_salary   │ numeric     │           │ yes      │
hourly_rate   │ numeric     │           │ yes      │
session_rate  │ numeric     │           │ yes      │  ← NEW
shift_rate    │ numeric     │           │ yes      │  ← NEW
```

**commission_rule schema (relevant columns):**
```
Column        │ Type        │ Collation │ Nullable │ Default
──────────────┼─────────────┼───────────┼──────────┼─────────
rule_type     │ varchar     │           │ no       │
service_type_id │ uuid      │           │ yes      │
staff_id      │ uuid        │           │ yes      │  ← NEW (FK)
rate_percent  │ numeric     │           │ no       │
is_active     │ boolean     │           │ no       │ true
is_deleted    │ boolean     │           │ no       │ false
```

**Indexes on commission_rule:**
```
Index name                               │ Type   │ Table            │ Columns
─────────────────────────────────────────┼────────┼──────────────────┼────────────────────
ix_commission_rule_staff_id              │ BTREE  │ commission_rule  │ staff_id
uq_commission_rule_clinic_service_type_staff │ BTREE │ commission_rule │ clinic_id, service_type_id, COALESCE(staff_id, '00000000-0000-0000-0000-000000000000'::uuid)
uq_commission_rule_clinic_medicine_staff │ BTREE  │ commission_rule  │ clinic_id, COALESCE(staff_id, '00000000-0000-0000-0000-000000000000'::uuid)
```

---

## References

- **Implementation Plan:** `docs/tasks/TASK-138/refs/implementation-plan.md`
- **Functional Design:** `docs/tasks/TASK-138/deliveries/final-specs/payroll-session-shift-per-staff-commission-functional-design.md`
- **Code Review Report:** `docs/tasks/TASK-138/handoff/review-report.md` (Fix round 1, m2: downgrade order fix)
- **Test Report:** `docs/tasks/TASK-138/deliveries/test-reports/test-report.md` (MIG-01..MIG-05)

---

## Support

For issues or questions regarding this migration:
1. Check the docstring in the migration file itself (`alembic/versions/0077_*.py`)
2. Review test scenario MIG-05 in `test-report.md` if downgrade is involved
3. Escalate to the development team if data loss or constraint violations occur
