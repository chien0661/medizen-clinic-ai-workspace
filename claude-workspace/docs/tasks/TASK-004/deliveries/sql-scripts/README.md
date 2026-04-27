# SQL Scripts — RBAC Schema and Seed (TASK-004)

## Overview

This directory contains DDL and seed DML for the RBAC module, extracted from Alembic migrations for DBA reference and operations documentation.

**Files:**
- `001-rbac-schema.sql` — DDL for 5 tables, RLS policies, indexes
- `002-rbac-seed.sql` — INSERT 38 permissions, 5 system roles, default role-permission mappings
- `README.md` — This file

## Important Note

**The canonical source for these scripts is the Alembic migrations, not these files.**

The Alembic migration code is:
- `/clinic-cms/alembic/versions/0006_setup_rbac.py` — Schema DDL
- `/clinic-cms/alembic/versions/0007_seed_permissions_and_roles.py` — Seed data

These SQL files are provided for:
- DBA reference and understanding
- Manual execution in non-standard scenarios (manual test DB, ops troubleshooting)
- Documentation and compliance purposes

**For regular deployment, always use Alembic:**
```bash
alembic upgrade head
```

## Schema Overview

### Tables

| Table | Rows | Purpose |
|-------|------|---------|
| `permission` | 38 | System-wide permission catalog (read-only seed) |
| `role` | 5+ | System roles (admin, doctor, nurse, pharmacist, receptionist) + custom clinic-scoped roles |
| `role_permission` | ~150 | M2M: role ↔ permission mappings |
| `user_role` | variable | M2M: user ↔ role assignments (multi-role per user) |
| `user_extra_permission` | variable | Per-user grant/deny overrides (independent of roles) |

### Key Design Decisions

1. **Deterministic UUIDs for System Roles**
   - UUIDs for the 5 system roles are derived via `uuid5(NAMESPACE_OID, role_code)`
   - This ensures consistent IDs across alembic upgrade/downgrade/re-run cycles
   - Enables safe downgrade paths

2. **Permission as Natural PK**
   - Permission table uses `code` as natural primary key (e.g., `'patient.read'`)
   - Simplifies foreign keys and reduces UUID overhead

3. **RLS (Row Level Security)**
   - `role` table: allows all system roles (clinic_id IS NULL) + clinic-scoped isolation
   - `user_role`, `user_extra_permission`: isolation via joined user.clinic_id
   - `permission`: no RLS (global catalog)

4. **Soft-Delete Pattern**
   - `role`, `user_role`, `user_extra_permission` use soft-delete (is_deleted flag)
   - Audit trail preserved for compliance
   - Partial unique indexes on non-deleted rows prevent duplicate constraints

5. **Multi-Role Support**
   - Users can have multiple roles simultaneously
   - Effective permissions = union of all role permissions + extra_grants − extra_denies
   - Implemented via user_role M2M table (composite with role_id, user_id)

## Executing These Scripts Manually

### Prerequisites
- PostgreSQL 15+
- Access to the clinic_cms database as a user with DDL permissions
- RLS and extensions enabled (should already be in place from TASK-001/TASK-002 migrations)

### Step 1: Schema (001-rbac-schema.sql)

```bash
psql -U postgres -d clinic_cms -f 001-rbac-schema.sql
```

This will:
- Create the `extra_perm_type` ENUM
- Create 5 tables with columns, constraints, indexes
- Enable RLS policies on 3 tables (role, user_role, user_extra_permission)
- Grant permissions to cms_app role

### Step 2: Seed Data (002-rbac-seed.sql)

```bash
psql -U postgres -d clinic_cms -f 002-rbac-seed.sql
```

This will:
- Insert 38 permissions from BA §13.5 catalog
- Insert 5 system roles with deterministic UUIDs
- Create 150+ role-permission mappings per BA §13.6 default matrix

**Idempotency:** Scripts use `ON CONFLICT DO NOTHING` for inserts, so re-running is safe.

## UUID Reference

If you need to reference system role IDs in queries or scripts:

```sql
-- System role UUIDs (deterministic, uuid5 derived)
SELECT 'admin'       as role_code, '0c47bb77-fd45-5b42-87c0-e4beaea00040'::UUID as id
UNION ALL SELECT 'doctor',      '2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID
UNION ALL SELECT 'nurse',       '8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID
UNION ALL SELECT 'pharmacist',  'd5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID
UNION ALL SELECT 'receptionist', '1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d'::UUID;
```

Or query directly from the DB:

```sql
SELECT id, code, name FROM role WHERE clinic_id IS NULL ORDER BY code;
```

## Common Queries for Verification

### Count permissions
```sql
SELECT COUNT(*) FROM permission;
-- Expected: 38
```

### Count system roles
```sql
SELECT COUNT(*) FROM role WHERE clinic_id IS NULL AND is_system = TRUE;
-- Expected: 5
```

### List admin permissions
```sql
SELECT rp.permission_code
FROM role_permission rp
JOIN role r ON rp.role_id = r.id
WHERE r.code = 'admin' AND r.clinic_id IS NULL
ORDER BY rp.permission_code;
-- Expected: 38 rows
```

### List doctor permissions
```sql
SELECT rp.permission_code
FROM role_permission rp
JOIN role r ON rp.role_id = r.id
WHERE r.code = 'doctor' AND r.clinic_id IS NULL
ORDER BY rp.permission_code;
-- Expected: 15 rows
```

## Troubleshooting

### Error: "User ID doesn't exist"
If you see FK constraint violations when inserting user_role or user_extra_permission, ensure that:
- The user exists in the `user` table with matching clinic_id
- The clinic_id in the user row matches the clinic_id context for RLS

### Error: "Partial unique index violation"
When re-running `002-rbac-seed.sql`, if you get duplicate key errors:
- The `ON CONFLICT DO NOTHING` should prevent this
- If it occurs, verify that the previous run completed successfully
- Check for stale soft-deleted rows: `SELECT * FROM role WHERE is_deleted = TRUE`

### RLS not blocking (seeing all clinic's data)
If RLS policies aren't isolating data:
- Verify `app.current_clinic_id` is set in the session: `SELECT current_setting('app.current_clinic_id', true)`
- Check that RLS is enabled: `SELECT * FROM pg_tables WHERE tablename IN ('role', 'user_role', 'user_extra_permission')`
- RLS policies are only enforced when `ALTER TABLE ... FORCE ROW LEVEL SECURITY` is active

## Related Documentation

- **Functional Design:** `../final-specs/rbac-functional-design.md`
- **API Specification:** `../api-specs/rbac-api-spec.md`
- **Test Report:** `../test-reports/rbac-test-report.md`
- **Alembic Migrations:** `../../clinic-cms/alembic/versions/0006_setup_rbac.py`, `0007_seed_permissions_and_roles.py`

## Support

For issues or questions:
1. Check the functional design for business rules
2. Review alembic migration code for implementation details
3. Check test cases in `../test-cases/` for expected behavior
