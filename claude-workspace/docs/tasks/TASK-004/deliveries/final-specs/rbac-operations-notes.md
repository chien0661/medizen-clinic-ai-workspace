# RBAC Operations & Troubleshooting Guide

**Version:** 1.0  
**Date:** 2026-04-28  
**Task:** TASK-004

---

## Overview

This document captures operational considerations for deploying and maintaining the RBAC module in production environments, along with troubleshooting guidance.

---

## Architecture Integration

### Dependencies

RBAC module (`app/modules/users/`) depends on:

1. **Auth Module (TASK-003)**
   - JWT token generation and validation
   - Password hashing (bcrypt cost 12)
   - Token refresh and revocation (Redis blacklist)
   - Required: `jwt_secret`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (15 min), `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (7-30)

2. **Audit Module (TASK-002)**
   - Audit log capture via `__auditable__=True` mixin
   - Logging for role assignments, permission changes, extra-permission grant/deny
   - Required: `audit_log` table and listeners already in place

3. **Tenancy Module (TASK-001)**
   - RLS enforcement via `app.current_clinic_id` session setting
   - User-clinic 1:1 relationship enforced via FK + RLS
   - Required: `clinic` table, RLS policies, `current_setting('app.current_clinic_id')` available

4. **Redis**
   - Permission cache (key: `user:perms:{user_id}`, TTL: 5 min)
   - Required: `REDIS_URL` environment variable, Redis 6.0+
   - Fallback: if Redis unavailable, permission checks query database on every request (graceful degradation)

5. **PostgreSQL 15+**
   - RLS policies on 3 tables
   - ENUM type `extra_perm_type` (grant|deny)
   - Partial unique indexes
   - Required: `pg_trgm`, `uuid-ossp` extensions

---

## Configuration

### Environment Variables

No new env vars required for TASK-004 (RBAC uses existing Auth/Redis config).

**Relevant existing vars:**
- `JWT_SECRET` — from Auth (TASK-003)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` — typically 15
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS` — typically 7-30
- `REDIS_URL` — format `redis://[host]:[port]/[db]`
- `DATABASE_URL` — PostgreSQL connection string

### Redis Cache TTL

**Current:** 5 minutes hardcoded in `app/modules/users/services/rbac_service.py`

To adjust cache TTL in future versions:
1. Add env var: `RBAC_PERMISSION_CACHE_TTL_SECONDS` (default: 300)
2. Update `rbac_service.get_effective_permissions()` to use `settings.RBAC_PERMISSION_CACHE_TTL_SECONDS`
3. Document the change in this file

---

## Deployment Checklist

### Pre-Deployment

- [ ] Alembic migrations tested on dev DB: `alembic upgrade head`
- [ ] Verify 38 permissions seeded: `SELECT COUNT(*) FROM permission` → expect 38
- [ ] Verify 5 system roles seeded: `SELECT COUNT(*) FROM role WHERE clinic_id IS NULL` → expect 5
- [ ] Verify admin role has all 38 permissions: `SELECT COUNT(*) FROM role_permission WHERE role_id = (SELECT id FROM role WHERE code='admin')` → expect 38
- [ ] RLS policies enabled on role, user_role, user_extra_permission tables
- [ ] Redis is running and accessible: `redis-cli PING` → expect PONG
- [ ] Test suite passes: `pytest tests/integration/test_rbac_e2e_extended.py -v` → expect 16+ passed

### Post-Deployment

- [ ] Create first admin user via API (requires manual DB insert for initial user_role binding, or bootstrap endpoint)
- [ ] Test login with admin user → verify JWT contains all 38 permissions
- [ ] Test permission check on API route (e.g., `/users` requires `user.manage`) → expect 403 for non-admin
- [ ] Test cache invalidation: assign new role → verify `user:perms:{user_id}` deleted from Redis
- [ ] Verify audit logs captured: check `audit_log` table for role/permission changes

---

## Troubleshooting

### Issue: User's permission hasn't changed after role assignment, getting 403

**Symptom:** 
- Admin assigns role to user
- User logs in, JWT contains old permissions
- User tries API call requiring new permission → 403 Forbidden

**Cause:** 
- JWT token has 15-minute lifetime (hardcoded in Auth module TASK-003)
- Cache TTL is 5 minutes, but JWT is the authority for the session

**Solution:**
- **Short-term:** User logs out and logs in again → new JWT generated with updated permissions
- **Alternative:** Admin refreshes user's JWT via refresh endpoint (already issued refresh token will have new perms on next refresh)
- **Check cache:** Verify Redis cache was invalidated after role change: `redis-cli GET user:perms:{user_id}` → should be `nil` immediately after assignment

**Prevention:**
- Educate users: permission changes take effect at next login or JWT refresh (max 15 minutes)
- Consider adding UI alert: "Permission changes may take up to 15 minutes to take effect"

### Issue: Role assignment fails with FK constraint violation

**Symptom:**
```
ERROR: insert or update on table "user_role" violates foreign key constraint "fk_user_role_role_id_role"
```

**Cause:**
- Role ID not found (typo in UUID, deleted soft role, clinic isolation mismatch)

**Solution:**
1. Verify role exists: `SELECT id, code, clinic_id FROM role WHERE id = '{role_id}'`
2. If clinic_id is NOT NULL, ensure it matches user's clinic: `SELECT clinic_id FROM "user" WHERE id = '{user_id}'`
3. If role has `is_deleted = TRUE`, undelete it: `UPDATE role SET is_deleted = FALSE, deleted_at = NULL WHERE id = '{role_id}'`

### Issue: "System roles are immutable" 403 error when trying to modify system role

**Symptom:**
- User tries to PATCH a system role or add permission to system role → 403 Forbidden
- Message: "System roles are immutable; clone the role first"

**Expected Behavior:** Correct (by design).

**Workaround:**
- Clinic cannot modify system roles globally
- To customize permissions for a role in a clinic: use `clone_system_role(role_code)` service (scaffolded, not yet exposed as endpoint)
- Creates a clinic-scoped custom role with copy of system role's permissions
- Then modify the custom role as needed

**Prevention:**
- Document for clinic admins: system roles are read-only, must clone to customize
- Implement `POST /clinic/{id}/roles/clone-system` endpoint in TASK-onboarding

### Issue: User can't access endpoint despite having the permission in DB

**Symptom:**
- `user_role.user_id = {user_id}, role_id = {role_id}` exists in DB
- `role_permission.role_id = {role_id}, permission_code = '{perm_code}'` exists
- User gets 403 Forbidden for endpoint requiring that permission

**Cause:**
- User's JWT doesn't include the permission (stale JWT, cache not invalidated, or permissions not refreshed after role change)
- RLS policy blocking query

**Solution:**
1. Verify permission is in user's JWT: decode JWT at jwt.io or via `jwt.decode(token, secret)`
2. Verify DB has the permission: `SELECT * FROM role_permission WHERE role_id = '{role_id}' AND permission_code = '{perm_code}'`
3. If DB has it but JWT doesn't: 
   - User needs to refresh token (get new access token via refresh endpoint)
   - Or re-login
4. If DB doesn't have it: 
   - Admin needs to assign role or add extra_permission grant

### Issue: RLS blocking RBAC queries ("permission denied for schema rbac")

**Symptom:**
```
ERROR: permission denied for schema public
```
when querying role, user_role, or user_extra_permission tables.

**Cause:**
- `app.current_clinic_id` session variable not set
- User doesn't have SELECT grant on table

**Solution:**
1. Verify current_clinic_id is set in middleware: check `app/core/db.py` for `set_current_clinic_id()` call
2. Verify FastAPI dependency chain sets clinic context before DB query
3. Test directly:
   ```sql
   -- In psql as cms_app user
   SET app.current_clinic_id = '550e8400-e29b-41d4-a716-446655440001';
   SELECT COUNT(*) FROM role;  -- Should return 5 (system roles)
   ```

### Issue: Alembic downgrade 0007 leaves orphaned rows

**Symptom:**
- Run `alembic downgrade 0007` on dev DB with pre-existing legacy UUID role IDs
- System role rows (admin, doctor, etc.) still in role table (not deleted)
- Orphaned rows conflict with re-running `alembic upgrade 0007`

**Cause:**
- Downgrade uses `uuid5` derived IDs, but existing dev DB has `uuid4` IDs from prior seed
- Downgrade's DELETE WHERE id = '{uuid5}' doesn't match legacy rows

**Known Limitation:**
- This only affects dev databases with legacy seed data (created before UUID5 determinism fix in iteration 2)
- CI and prod installs always use fresh DB with uuid5 (no issue)

**Workaround:**
1. Manual cleanup on dev:
   ```sql
   DELETE FROM role WHERE code IN ('admin', 'doctor', 'nurse', 'pharmacist', 'receptionist');
   ```
2. Then re-run:
   ```bash
   alembic upgrade 0007
   ```
3. Or reset to clean DB:
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

**Prevention:**
- Developers should reset dev DB when switching branches (not an issue for CI/prod)
- Track in a future ticket: "Migrate legacy UUID role IDs to uuid5" (low priority)

### Issue: Extra-permission override not working (grant or deny isn't effective)

**Symptom:**
- Created extra_permission with type='deny' for user
- User still has the permission in JWT

**Cause:**
- Extra permission was created after JWT was issued
- JWT has 15-minute lifetime and caches old permissions
- Or extra-permission soft-delete wasn't flushed correctly

**Solution:**
1. Verify extra_permission exists in DB:
   ```sql
   SELECT * FROM user_extra_permission 
   WHERE user_id = '{user_id}' AND permission_code = '{perm_code}' AND is_deleted = FALSE;
   ```
2. Verify Redis cache was invalidated (should be):
   ```bash
   redis-cli GET user:perms:{user_id}  # Should return nil
   ```
3. User needs to:
   - Refresh JWT via refresh endpoint, or
   - Log out and log back in
4. If still not working:
   - Check `rbac_service.compute_effective_permissions()` logic in code
   - Verify extra_deny is subtracted from effective set

---

## Performance Considerations

### Permission Cache Hit Rate

**Goal:** Minimize DB queries for permission checks.

**Current Strategy:**
- JWT payload includes all user permissions (signed, immutable)
- Redis cache as fallback when refreshing tokens
- TTL: 5 minutes

**Monitoring:**
- Track cache hit rate in auth logs (future feature)
- Alert if Redis is down for > 1 minute (fallback to DB query)
- Monitor JWT size for payload inflation

**Action Items (m1, m2 defer):**
- Once permission catalog > 100 items, consider permission bitmap instead of array
- Once multi-Redis (cluster) is deployed, implement ConnectionPool to reduce connection overhead

---

## Multi-Clinic Considerations

### Current State (TASK-004)

- User has 1-to-1 relationship with clinic
- System roles (admin, doctor, nurse, pharmacist, receptionist) are global, not clinic-scoped
- Clinic admins can create custom roles with clinic-scoped permissions

### Future (Phase 2)

- Support user per multiple clinics
- Each user has one set of base roles + per-clinic role assignments
- RLS queries must join through user-clinic M2M table
- Will require schema changes (user_clinic M2M table, migration to RBAC)

---

## Security Hardening

### Current Protections

1. **RLS:** Clinic isolation enforced at database level for user_role and user_extra_permission
2. **JWT Signing:** HS256 with strong secret (from Auth module)
3. **System Role Guard:** 403 error when attempting to modify system roles (is_system = TRUE)
4. **Audit Logging:** All role changes logged via `__auditable__` mixin

### Recommendations for Future

1. **Audit Alerting:** Set up alerts for:
   - Any system role modification attempt (should be 0)
   - Extra-deny on admin for high-risk permissions (manual review)
   - Mass role revocations

2. **Permission Audit Trail:** 
   - Track who granted/denied which permission to whom
   - Currently captured in `audit_log`, consider dashboard UI

3. **JWT Secrets Rotation:**
   - Coordinate with Auth module (TASK-003)
   - Plan for key rotation without invalidating all issued tokens

4. **Rate Limiting:**
   - Apply to `/auth/login` (already in place via slowapi)
   - Consider applying to role management endpoints (POST/DELETE on roles)

---

## Testing & QA

### Integration Test Coverage

- 16 new end-to-end tests in `tests/integration/test_rbac_e2e_extended.py`
- Real PostgreSQL + Redis (no mocks)
- 289 tests passing, 75% module coverage

**Critical test scenarios:**
- Multi-role union (user with doctor + nurse roles)
- Extra-deny override (deny overrides role grant)
- Cache invalidation (role change → cache deleted → next request queries DB)
- System role immutability (403 on update/delete)
- Permission check on route (403 for missing permission)

### UAT Checklist

- [ ] Doctor can view patients (patient.read)
- [ ] Nurse cannot void invoice (no invoice.void)
- [ ] Admin can create new role and assign permissions
- [ ] Manager can grant extra-permission (deny) to receptionist for invoice.void
- [ ] Receptionist immediately gets 403 on next login (after token refresh)
- [ ] Cannot delete system roles (admin, doctor, etc.)
- [ ] Cannot modify system role permissions

---

## Monitoring & Alerts

### Metrics to Track

1. **Cache Performance:**
   - Redis cache hit rate for user permissions
   - Cache miss rate (fallback to DB)

2. **JWT Size:**
   - Average JWT payload size
   - Max JWT payload size (admin = ~700 bytes)

3. **Permission Queries:**
   - DB queries for permission checks (should be minimal if cache working)
   - Query latency percentiles (p50, p95, p99)

4. **Error Rates:**
   - 403 Forbidden rate (expected, monitor for spikes)
   - FK constraint violations on user_role/user_extra_permission inserts
   - RLS policy violations

### Recommended Alerts

- Redis down for > 2 minutes (watch for fallback to DB)
- Cache miss rate > 20% (possible cache coherency issue)
- JWT size > 2 KB (permission inflation)
- 403 error rate > 5% above baseline (possible permission configuration issue)

---

## Maintenance Tasks

### Daily
- Monitor Redis connectivity and latency
- Check for any RLS policy violations in logs

### Weekly
- Review audit logs for unauthorized permission/role modifications
- Check cache hit/miss ratios
- Monitor JWT size trends

### Monthly
- Review system role usage: verify 5 system roles have expected permissions
- Audit custom clinic roles for compliance
- Plan for upcoming permission catalog expansions

### Quarterly
- Review security posture (JWT secrets age, audit alerting effectiveness)
- Plan for multi-clinic phase (schema changes)
- Evaluate need for permission bitmap optimization

---

## Related Documentation

- **Functional Design:** `rbac-functional-design.md`
- **API Specification:** `../api-specs/rbac-api-spec.md`
- **SQL Scripts:** `../sql-scripts/`
- **Auth Module (TASK-003):** JWT, password hashing, token refresh
- **Audit Module (TASK-002):** Audit logging infrastructure
- **Tenancy (TASK-001):** RLS, clinic isolation

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-28  
**Owner:** Documentation Agent (Claude Code)
