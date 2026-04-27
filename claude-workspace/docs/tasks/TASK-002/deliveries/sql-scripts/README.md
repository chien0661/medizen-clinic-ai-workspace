# SQL Scripts Delivery — TASK-002 Tenancy + RLS + Audit Log

**Date**: 2026-04-26  
**Status**: DONE  
**Branch**: `feature/task-002-tenancy` (commit f90e915)  

---

## Overview

TASK-002 introduces three migrations that implement multi-tenancy, row-level security, and audit infrastructure. This folder documents their purpose, application, and idempotency.

---

## Migration Files

All migrations are auto-versioned by Alembic. The source files live in:
```
clinic-cms/alembic/versions/
```

### 0002_create_audit_log.py

**Purpose**: Create append-only `audit_log` table with immutability trigger.

**What it does**:
1. Creates `audit_log` table with columns: id, clinic_id, user_id, request_id, action, entity_type, entity_id, old_data, new_data, changed_fields, ip_address, user_agent, created_at
2. Creates indexes:
   - `ix_audit_log_clinic_id_created_at` (queries by clinic + time)
   - `ix_audit_log_entity_type_entity_id` (queries by entity)
   - `ix_audit_log_user_id_created_at` (queries by actor)
   - `ix_audit_log_clinic_id` (RLS policy lookup)
3. Creates PostgreSQL function `fn_prevent_audit_modification()` — raises exception on UPDATE/DELETE
4. Creates triggers `tr_audit_log_update`, `tr_audit_log_delete` — enforce immutability

**Idempotency**: 
- `CREATE TABLE IF NOT EXISTS` — safe on rerun
- `CREATE OR REPLACE FUNCTION` — safe on rerun
- Triggers wrapped in `DROP IF EXISTS` before creation — safe on rerun

**Down**:
- Drops triggers (cascade)
- Drops function
- Drops table (cascade)

### 0003_setup_rls_policies.py

**Purpose**: Enable Row-Level Security and apply `tenant_isolation` policy.

**What it does**:
1. Calls helper `apply_rls_with_tenant_isolation(op, "audit_log")`
   - Executes: `ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;`
   - Executes: `ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;`
   - Executes: `CREATE POLICY tenant_isolation ON audit_log FOR ALL USING (clinic_id::text = current_setting('app.current_clinic_id', true) OR clinic_id IS NULL)`
   
2. (At this point, only `audit_log` exists. Future TASK-005+ will call the same helper in their migrations.)

**Policy logic**:
```sql
USING (clinic_id::text = current_setting('app.current_clinic_id', true) 
       OR clinic_id IS NULL)
```
- Row is visible if: `clinic_id` matches `current_setting('app.current_clinic_id')` OR `clinic_id IS NULL`
- Matching happens at query time — transparent filtering

**Idempotency**:
- `ALTER TABLE ... ENABLE` is idempotent (no error if already enabled)
- Policy `CREATE POLICY ... ON ... FOR ALL USING` — wrapped in `CREATE POLICY IF NOT EXISTS` (safe on rerun)

**Down**:
- Calls helper `remove_rls(op, "audit_log")`
- Executes: `DROP POLICY IF EXISTS tenant_isolation ON audit_log;`
- Executes: `ALTER TABLE audit_log NO FORCE ROW LEVEL SECURITY;`
- Executes: `ALTER TABLE audit_log DISABLE ROW LEVEL SECURITY;`

### 0004_create_app_role.py

**Purpose**: Create production application role `cms_app` (non-superuser, NOBYPASSRLS).

**What it does**:
1. Creates role `cms_app` idempotently:
   ```sql
   CREATE ROLE cms_app LOGIN PASSWORD 'cms_app_change_in_production'
     NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
   ```
   (Wrapped in `DO ... IF NOT EXISTS` for idempotency)

2. Grants permissions:
   - `CONNECT ON DATABASE cms`
   - `SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public`
   - `ALTER DEFAULT PRIVILEGES ... GRANT ... ON TABLES` (future-proof)
   - `USAGE ON ALL SEQUENCES IN SCHEMA public`
   - `ALTER DEFAULT PRIVILEGES ... GRANT USAGE ON SEQUENCES` (future-proof)

**Idempotency**:
- Role creation wrapped in `IF NOT EXISTS`
- GRANT statements are idempotent (no error if already granted)

**Production checklist**:
1. Run migration: `alembic upgrade head`
2. Change password:
   ```sql
   ALTER ROLE cms_app WITH PASSWORD '<secure-password-from-vault>';
   ```
3. Update `DATABASE_URL` env var:
   ```
   DATABASE_URL=postgresql+asyncpg://cms_app:<password>@host:5432/cms
   ```
4. Restart app

**Down**:
- Revokes all privileges from `cms_app`
- Does NOT drop role (it may own objects, cleanup requires manual `DROP ROLE cms_app`)

---

## Application Instructions

### Local Development

```bash
# 1. Apply all migrations
cd clinic-cms
alembic upgrade head

# 2. Verify
alembic current  # Should show: 0004_create_app_role

# 3. Verify roles
psql -h localhost -U cms -d cms -c "SELECT rolname, usesuper, usebypassrls FROM pg_roles WHERE rolname IN ('cms', 'cms_app');"
# Expected output:
#  rolname  | usesuper | usebypassrls
# ----------+----------+--------------
#  cms      | t        | t
#  cms_app  | f        | f

# 4. Verify audit_log table
psql -h localhost -U cms -d cms -c "\dt audit_log"
# Expected: audit_log | table | cms
```

### CI/CD Pipeline

```bash
# In test setup (e.g., .github/workflows/ci.yml):
1. Docker Compose up (PostgreSQL + app container)
2. alembic upgrade head
3. pytest

# CI database starts with all tables + RLS + cms_app role ✓
```

### Staging / Production Deployment

```bash
# 1. Backup production database
pg_dump -h <prod-host> -U postgres -d cms | gzip > cms-$(date +%s).sql.gz

# 2. Apply migrations
alembic upgrade head

# 3. Change cms_app password (must be in vault / secrets manager)
psql -h <prod-host> -U postgres -d cms -c "ALTER ROLE cms_app WITH PASSWORD '<new-password>';"

# 4. Update environment variables on app server
# DATABASE_URL=postgresql+asyncpg://cms_app:<new-password>@<prod-host>:5432/cms

# 5. Restart app
docker pull clinic-cms:latest
docker-compose up -d

# 6. Verify (app startup logs)
docker logs clinic-cms_app | grep "db_role_security"
# Should NOT see CRITICAL warning if role is correct
```

---

## Rollback

### Single Migration Rollback

```bash
alembic downgrade -1  # Rolls back 0004 (most recent)
alembic downgrade 0003  # Rolls back to 0003 state
```

### Full Rollback (not recommended in production)

```bash
alembic downgrade base  # Rolls back everything
```

---

## Verification Queries

### Check audit_log table exists and has correct schema

```sql
SELECT column_name, data_type, is_nullable
  FROM information_schema.columns
 WHERE table_name = 'audit_log'
 ORDER BY ordinal_position;
```

### Check RLS enabled on audit_log

```sql
SELECT schemaname, tablename, rowsecurity
  FROM pg_tables
 WHERE tablename = 'audit_log';
-- Expected: rowsecurity = true
```

### Check tenant_isolation policy exists

```sql
SELECT policyname, cmd, qual
  FROM pg_policies
 WHERE tablename = 'audit_log';
-- Expected: policyname = 'tenant_isolation', cmd = 'ALL'
```

### Check cms_app role exists and is non-superuser

```sql
SELECT rolname, usesuper, usebypassrls, usecreatedb, usecreaterole, usecanlogin
  FROM pg_roles
 WHERE rolname = 'cms_app';
-- Expected: usesuper=f, usebypassrls=f, usecreatedb=f, usecanlogin=t
```

### Test RLS isolation (manual)

```bash
# Terminal 1: Connect as cms (superuser) — sees all data
psql -h localhost -U cms -d cms -c "SELECT COUNT(*) FROM audit_log;"
# Output: 3 (example)

# Terminal 2: Connect as cms_app, set clinic_id context, query same table
psql -h localhost -U cms_app -d cms -c "
  SET app.current_clinic_id TO 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx';
  SELECT COUNT(*) FROM audit_log WHERE clinic_id::text = current_setting('app.current_clinic_id');
"
# Output: 1 (only this clinic's records)
```

---

## Known Limitations (v1)

1. **JSONB in-place mutation**: In-place edits of JSONB columns (e.g., `record.meta["key"] = value`) are NOT detected by SQLAlchemy unless the column is declared with `MutableDict.as_mutable(JSONB)`. Downstream models must opt-in.

2. **Audit lag p99**: No async queue in v1. Audit writes are sync (same transaction). Phase 2 will use Arq for independent persistence and benchmark p99.

3. **Password default**: Migration 0004 sets `PASSWORD 'cms_app_change_in_production'` — this is a placeholder. **Production deployment MUST change it immediately** via `ALTER ROLE`.

---

## Dependencies

- PostgreSQL 13+ (tested on 14, 15)
- Alembic 1.8+
- SQLAlchemy 2.0+

---

## References

- **Deployment guide**: `docs/deployment/database-roles.md`
- **Functional design**: `docs/tasks/TASK-002/deliveries/final-specs/tenancy-audit-functional-design.md`
- **API spec**: `docs/tasks/TASK-002/deliveries/api-specs/tenancy-api.md`
- **Test report**: `docs/tasks/TASK-002/deliveries/test-reports/test-report.md`

---

**Created**: 2026-04-26  
**Branch**: `feature/task-002-tenancy`  
**Commit**: f90e915  
**Status**: Ready for merge
