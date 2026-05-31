# TASK-052 — Category B Triage (20 failures)

**Date**: 2026-05-29
**Method**: read-only inspection of `git diff` in `../clinic-cms-merge` (no files modified).

## Verdict: ALL 20 failures stem from uncommitted "super admin" WIP — NOT main regressions

The merge worktree has an **in-progress, uncommitted feature** (platform super admin):

```
?? alembic/versions/0036_super_admin.py
?? app/modules/superadmin/
?? scripts/seed_superadmin.py
 M app/core/rls.py            (+superadmin_bypass RLS policy)
 M app/core/db.py             (+app.is_superuser GUC)
 M app/core/permissions.py    (superuser bypass)
 M app/core/security.py
 M app/core/tenancy.py
 M app/main.py
 M app/modules/auth/api/routes.py
 M app/modules/auth/schemas/auth_schemas.py
 M app/modules/auth/services/auth_service.py   (+45)
 M app/modules/auth/services/lockout_service.py (+57)
 M app/modules/users/models/user.py
 D docker/docker-compose.w2e.yml
```

### Proven correlation
`app/core/rls.py` now adds a 2nd policy `superadmin_bypass` in
`apply_rls_with_tenant_isolation` and a matching DROP in `remove_rls`. So each
helper now issues **4** SQL statements, not 3 →
`tests/unit/test_rls_helpers.py::*::test_executes_three_statements` (×2) fail by
design. The remaining failures map cleanly to the same feature:

| Failing group | Caused by WIP in |
|---|---|
| `test_rls_helpers` (2) | `rls.py` (+superadmin_bypass policy → 4 stmts) |
| `test_rls_isolation` (3), `test_rls_admin_bypass` (2), `test_tenant_isolation_full` (2) | `rls.py` + `db.py` is_superuser GUC |
| `test_auth_mfa` (3), `test_auth_service_coverage` (3), `test_jwt_includes_perms` (2) | `auth_service.py`, `lockout_service.py`, `auth_schemas.py` |
| `admin/test_admin_e2e` (3) | `permissions.py` / auth changes |

## Recommendation

These are **not bugs on main** — they are tests going stale against an
in-flight feature. The correct owner is whoever is building super admin.

- **Do NOT** modify the super-admin WIP (incomplete) to make tests pass.
- **Do NOT** loosen/rewrite these tests yet — the feature's final behavior isn't
  locked (e.g. `test_executes_three_statements` should become `_four_statements`
  only once the policy set is final).
- Recommended: finish + commit the super-admin feature, then update these 20
  tests as part of THAT task. TASK-052 should treat them as out-of-scope and
  record them here.

## TASK-052 scope decision

TASK-052 owns **Category A** (encryption-fixture regression) — independent of the
WIP, touches only test fixtures. Category B is parked pending the super-admin
feature.
