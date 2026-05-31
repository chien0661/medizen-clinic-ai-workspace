# TASK-052 — Follow-ups (parked items)

The BE test sweep surfaced issues that are out of scope for TASK-052 (would require
baking in uncommitted WIP, architectural redesign, or test-infra changes). Tracked here
for future tasks.

## 1. Super-admin feature — update its tests when it lands (21 failures)
The uncommitted super-admin WIP (`alembic/versions/0036_super_admin.py`,
`app/modules/superadmin/`, modified `rls.py`/`db.py`/`permissions.py`/`auth_service.py`/
`lockout_service.py`/`auth_schemas.py`/`user.py`) changes RLS + auth behavior. These tests
must be updated as part of THAT feature's task, not TASK-052:
- `tests/unit/test_rls_helpers.py` — expect 4 statements (ENABLE/FORCE/CREATE tenant_isolation/CREATE superadmin_bypass), not 3.
- `tests/integration/test_rls_isolation.py`, `test_rls_admin_bypass.py`, `test_tenant_isolation_full.py` — reconcile with `app.is_superuser` GUC + superadmin_bypass policy.
- `tests/integration/test_auth_mfa.py`, `test_auth_service_coverage.py`, `test_jwt_includes_perms.py`, `test_auth_lockout_real_db.py` — reconcile with auth/lockout WIP.
- `tests/integration/test_rbac_e2e_real_db.py` (seed_integrity), `test_rbac_e2e_extended.py` (test_admin_has_all_38_permissions) — permission/role counts changed (migration 0036 adds perms/roles; current DB = 66 perms / 7 roles). Update expected counts ONCE the super-admin migration is finalized & committed (don't bake in WIP numbers now).
- `test_rbac_e2e_real_db.py::test_role_assignment_grants_access_then_revocation_blocks` — Redis perm-cache assertion; verify against final permissions.py.

## 2. Encrypted-column search redesign (1 failure) — TASK-037 follow-up
`tests/integration/patients/test_rls_isolation_cms_app_role.py::test_rls_search_by_phone_cross_clinic_returns_zero`
does a trigram `phone % $1` query, but `phone` is now `EncryptedString` (BYTEA) →
`operator does not exist: bytea % unknown`. PII search on encrypted columns needs a strategy
(blind index / deterministic search token / decrypt-in-app). This is the "search-post-encryption"
item already flagged in TASK-037's functional design.

## 3. Test-infra: run app DB connection under non-BYPASSRLS role (4 failures)
Cross-tenant isolation HTTP tests assume RLS filters cross-tenant rows, but the app's test DB
connection uses the `cms` superuser role (BYPASSRLS). Post-encryption these now 500 (wrong-DEK
InvalidTag) instead of the production 404. Production is correct (RLS → 404). To test true
isolation, the app's test connection should use the non-BYPASSRLS `cms_app` role.
Affected: `patients/test_patients_api.py::{test_merge_cross_tenant_forbidden, test_tenant_isolation_via_http}`,
`patients/test_rls_isolation_cms_app_role.py::{test_rls_via_http_get_patient_cross_tenant_returns_404, test_rls_merge_cross_tenant_blocked_at_service_layer}`.
Do NOT "fix" by catching InvalidTag and returning 404 — that would mask real key/rotation errors.
