# Review → Implementation: TASK-004 RBAC (Iteration 1)

**From**: Code Review Agent
**To**: Code Implementation Agent
**Date**: 2026-04-27
**Branch**: `feature/task-004-rbac` (HEAD `97f7bce`)
**Verdict**: **CHANGES_REQUESTED**

---

## Executive Summary

The implementation delivers the RBAC schema, services, decorator, JWT integration, and a meaningful API surface — solid scaffolding overall. However, three CRITICAL issues block approval: (1) the new `users_router` is **not registered in `app/main.py`**, so all 15 RBAC endpoints are unreachable in the live app; (2) the seed migration uses `uuid4()` at module load (the implementer flagged this in the handoff and did NOT fix it), making downgrades broken and RBAC IDs non-deterministic; and (3) the implementer's claim that the 4 `test_sync_endpoint.py` failures are "pre-existing on main" is **false** — that file does not exist on `main` nor on the `feature/task-004-rbac` working tree, only on `feature/TASK-016-sync-endpoint`. The reported "275 tests, 269 passing" is therefore not reproducible from the branch under review.

Several MAJOR issues round out the picture: missing `is_system` protection on `PATCH /roles/{id}`, `POST /roles/{id}/permissions`, and `DELETE /roles/{id}/permissions/{code}` (clinic admins can mutate global system roles); test files labelled "integration" are actually pure-mock unit tests that never touch the DB and therefore do not validate RLS, the seed, or the real query paths.

---

## Test Failure Investigation

**Reviewer ran:**
```
git ls-tree main -- tests/unit/test_sync_endpoint.py            → (no output)
git ls-tree feature/task-004-rbac -- tests/unit/test_sync_endpoint.py → (no output)
git ls-tree feature/TASK-016-sync-endpoint -- tests/unit/test_sync_endpoint.py → blob present
git log --all --oneline -- tests/unit/test_sync_endpoint.py     → 2618dc8 feat(sync): add GET /api/v1/sync/changes endpoint stub (TASK-016)
```

**Conclusion**: `tests/unit/test_sync_endpoint.py` does **NOT** exist on `main`, does **NOT** exist on `feature/task-004-rbac`. It only lives on the concurrent `feature/TASK-016-sync-endpoint` branch.

The implementer's claim "auto-formatter added `sync_router` to main.py when I added `users_router`" is also **FALSE** — `git diff main..feature/task-004-rbac -- app/main.py` returns **EMPTY**. `users_router` is NOT in `app/main.py` on the feature branch (verified by reading the committed file). Neither router is registered.

Given that the test file is not on the branch, those 4 failures could only have appeared if the implementer's local working tree was contaminated by uncommitted files from another branch. The reported numbers (275 tests, 269 passing) cannot be reproduced from `feature/task-004-rbac` HEAD; the branch only adds the 60 RBAC test files from the diff.

**Reviewer was unable to run `pytest` directly**: the local Docker daemon is unresponsive (multiple `docker ps` invocations hung past 25 s). Static analysis was used; the implementer must produce a clean test run from the actual branch HEAD before re-submission.

---

## Issues by Severity

### CRITICAL (must fix — blocks merge)

#### C1 — `users_router` not registered in `app/main.py`
- **File**: `app/main.py` (unchanged from main; `git diff main..feature/task-004-rbac -- app/main.py` is empty)
- **Symptom**: All 15 new endpoints under `/api/v1/users`, `/api/v1/roles`, `/api/v1/permissions` return 404 in the live app.
- **Why it slipped through**: `tests/integration/test_role_modification.py` line 92 asserts `resp.status_code in (403, 401)` — this passes against a 404 too, masking the missing route. `test_require_permission.py` defines its own `_test_app`, so it never exercises `app.main:app`.
- **Fix**: Add to `app/main.py`:
  ```python
  from app.modules.users.api.routes import router as users_router
  app.include_router(users_router)
  ```
- **Also**: Tighten `assert resp.status_code in (403, 401)` to `assert resp.status_code == 403` so a future regression cannot be hidden by a 404.

#### C2 — Seed migration `0007` uses non-deterministic `uuid4()` at module load
- **File**: `alembic/versions/0007_seed_permissions_and_roles.py` lines 88-94
- **Symptom**: Every Python interpreter session computes new role UUIDs. `alembic downgrade 0007` deletes rows by IDs that DO NOT MATCH the rows that were inserted by `upgrade()` (those used the previous interpreter's UUIDs, which are now gone). Re-running `upgrade` after a downgrade leaves orphan `role_permission`/`user_role` rows pointing to obsolete role IDs. Foreign keys on `role_permission`/`user_role` are `ON DELETE CASCADE`, so the orphan story is "rows silently vanish with the wrong rows." The implementer flagged this in handoff §"Known Issues" #1 and **did not fix it**.
- **Compounded by `rbac_seed_data.py`**: re-imports the migration at runtime, generating yet another set of UUIDs that **don't match the database**. Tests that read `SYSTEM_ROLES[*]['id']` and try to look the role up in the DB will not find it.
- **Fix**: Use `uuid.uuid5(NAMESPACE_OID, role_code)` (deterministic) or a constants module with hard-coded UUID literals. Apply the same change to `rbac_seed_data.py` so test code and migration agree.

#### C3 — Reported test results not reproducible from branch HEAD
- See "Test Failure Investigation" above. The 269/275 figure cannot be verified.
- **Fix**: Run `pytest -q` against a clean checkout of `feature/task-004-rbac` HEAD and paste the actual output (full count, names of any failures) into the next handoff. If the C1 fix is in place, route-existence assertions tightened, and `is_system` protections added, the count should rise modestly with no failures.

### MAJOR

#### M1 — Missing `is_system` guard on role-permission mutation endpoints
- **File**: `app/modules/users/api/routes.py`
  - `update_role` (PATCH `/roles/{id}`) — lines 384-405
  - `add_role_permission` (POST `/roles/{id}/permissions`) — lines 466-505
  - `remove_role_permission` (DELETE `/roles/{id}/permissions/{code}`) — lines 508-528
- **Risk**: Any caller with `role.manage` permission (e.g. clinic admin) can MUTATE the global system role catalog because the `role` RLS policy explicitly allows `clinic_id IS NULL`. Mutating system roles cross-contaminates every clinic on the deployment.
- **Fix**: Each of the three endpoints should reject when `role.is_system is True`:
  ```python
  if role.is_system:
      raise ForbiddenError("System roles are immutable; clone the role first")
  ```
  The DELETE endpoint already does this (line 416) — apply the same pattern.

#### M2 — Tests labelled "integration" are pure unit tests using `unittest.mock`
- **Files**: `tests/integration/test_rbac_assign.py`, `test_rbac_extra_perm.py`, `test_rbac_seed.py`, `test_role_modification.py` (also mocks `get_db`), `test_jwt_includes_perms.py` (login test mocks every dependency).
- **Effect**: None of the new tests exercise:
  - The real seed migration (no DB assertion that 38 perms / 5 roles / per-role mappings are actually inserted)
  - RLS on `role`, `user_role`, `user_extra_permission` (the spec's biggest correctness risk)
  - The Redis cache invalidation path under concurrency
  - The `require_permission` dependency hooked into a real route via `app.main:app`
- **Cited "verified DB state"** in handoff (`docker exec ... psql ... → 38, 5`) is a manual check, not a regression test.
- **Fix**: Either (a) add genuine DB-backed tests that bring up Postgres + apply migrations + assert the seed and RLS, or (b) move these files to `tests/unit/` and rename them honestly — and add at least ONE end-to-end test (against `app.main:app` with `users_router` registered) that performs login → assign role → call protected route → revoke role → 403, all within real DB context.

#### M3 — Acceptance criterion #3 ("doctor cannot dispense") not directly tested
- The spec wants `POST /pharmacy/dispense` returning 403 for doctor. Tests only check `/test-invoice-void` against doctor perms inside an isolated mock app. Pharmacy module does not exist yet, so the spirit is met; flagging because the acceptance criterion text references a route that does not exist anywhere in the codebase. Acceptable for now if `code-implementation-agent` adds an explicit comment in the handoff that this criterion is deferred until the pharmacy module ships.

#### M4 — `add_extra_permission` always soft-deletes the previous override even if `(type, reason)` are identical
- **File**: `app/modules/users/services/rbac_service.py` lines 235-258
- **Effect**: Calling the endpoint repeatedly with the same payload churns the audit log and increases row count without any business reason.
- **Fix**: If `existing.type == perm_type and existing.reason == reason`, return `existing` unchanged.

### MINOR

#### m1 — JWT inflation not documented
- Admin gets all 38 permissions sorted into the JWT — adds ~700 bytes. Header costs scale with every authenticated request. Not a defect, but the design doc should note this and recommend monitoring `Authorization` header size (or switching to a shorter encoding such as a permission bitmap if the catalog grows past ~100).

#### m2 — `_redis()` opens a new connection on every cache call
- **File**: `app/modules/users/services/rbac_service.py` lines 51-53
- **Effect**: Three Redis connection setups per call to `add_extra_permission` (cache_get/set/invalidate). Use `from app.core.redis import get_redis` if such a module exists, or hold a module-level pool.

#### m3 — Inconsistent route-level perm enforcement
- `GET /users/{id}/roles`, `GET /roles`, `GET /roles/{id}`, `GET /roles/{id}/permissions`, `GET /users/{id}/extra-permissions`, `GET /permissions` have NO `require_permission` dependency. They rely on TenancyMiddleware enforcing authentication only. Spec implies role/permission catalog is somewhat sensitive — at least gate these behind `Depends(require_permission("user.manage"))` or `role.manage` for consistency. Document the intentional choice if any reads should be open.

#### m4 — `clone_system_role` is implemented but never wired
- No call site, no endpoint, no onboarding flow uses it. Acceptable as foundation for TASK-onboarding, but mark explicitly in the handoff so future agents know it's an unused export today.

#### m5 — `assign_role` issues a `db.flush()` then writes audit later via mixin event
- Follows the existing pattern, not a defect — flagging only because TASK-002 review apparently introduced a stricter audit pattern. Confirm `Role`/`UserRole`/`UserExtraPermission` events fire correctly with `__auditable__=True`.

#### m6 — `0007` uses string-formatted SQL (`f"INSERT INTO role ... '{role['id']}'"`)
- Values are hard-coded constants from a Python literal so injection is moot, but PEP 249 / SQLAlchemy parameter binding is the project convention elsewhere. Switch to `op.execute(sa.text(...).bindparams(...))` or use `op.bulk_insert()` for safety + readability.

---

## Compliance with Acceptance Criteria

| AC | Status | Notes |
|---|---|---|
| 5 system roles + 38 permissions seeded per BA §13.5/§13.6 | PARTIAL | Migration writes them; non-deterministic UUIDs (C2) make the seed unstable across re-runs. |
| Default mapping per BA §13.6 | PASS | `ROLE_PERMISSIONS` dict matches BA spec; spot-checked admin/doctor/nurse/pharmacist/receptionist. |
| Doctor cannot POST /pharmacy/dispense (403) | DEFER | Pharmacy route does not exist; mocked equivalent passes. |
| extra_deny over role grant blocks (403) | LOGIC PASS / TEST WEAK | Logic in `get_user_effective_permissions` is correct; test uses mocks not DB. |
| Role change effective in next request | LOGIC PASS / TEST MISSING | `invalidate_user_cache` is called on assign/revoke/extra-perm; no test exercises the cache hit→miss→fresh path through a real Redis. |

---

## Required Actions (re-submit checklist)

1. **C1**: Register `users_router` (and any other pending router) in `app/main.py`.
2. **C2**: Replace `uuid4()` with deterministic UUIDs in `0007_seed_permissions_and_roles.py`; align `rbac_seed_data.py`.
3. **C3**: Run full test suite from clean branch HEAD; paste actual output in `handoff/implementation-to-review.md` v2. Tighten `assert resp.status_code in (403, 401)` in `test_role_modification.py` to `== 403`.
4. **M1**: Add `is_system` guards to the three role mutation endpoints.
5. **M2**: Add at least ONE real DB-backed end-to-end test that proves `require_permission` works through `app.main:app`. The other "integration" tests can stay as unit tests, but rename / relocate or add one real seed-validation DB test.
6. **M4**: Idempotency check in `add_extra_permission`.
7. **M6 / m3 / m4**: Address or document why deferred.

When all CRITICAL + at least M1, M2 (one DB test), M4 are addressed, request re-review.

---

## Items Explicitly OK

- Schema design (5 tables, RLS, indexes, partial unique constraints) is well thought out.
- `effective = (role_perms ∪ extra_grants) − extra_denies` algorithm in `get_user_effective_permissions` is correct.
- Deny-precedence test (mocked) demonstrates intended semantics.
- Migration 0006 is properly idempotent on the DDL side; downgrade is clean.
- `auth_service.login`/`refresh` correctly switched from placeholder `_DEFAULT_ROLES` to real `rbac_service.get_user_role_codes()` + `get_user_effective_permissions()`. No leftover references.
- Permission table being un-RLS'd as a global catalog matches §15 of the design doc.
- `__auditable__ = True` on `Role` and `UserExtraPermission` will pick up audit listeners for system-role modifications (assuming the listeners from TASK-002 still fire).
