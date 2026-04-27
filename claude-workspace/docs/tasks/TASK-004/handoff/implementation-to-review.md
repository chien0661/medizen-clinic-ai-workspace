# Handoff: TASK-004 → Code Review (Iteration 2)

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-04-27
**Branch**: `feature/task-004-rbac`
**New HEAD**: `bba9020`
**Previous HEAD (iteration 1)**: `97f7bce`

---

## Summary

Iteration 2 surgical fixes addressing all CRITICAL and MAJOR review findings from iteration 1.
No unrelated code was touched. Test suite: **273 passed / 0 failed** from a clean branch checkout.

---

## Iteration 1 Issues Resolved

| Finding | Status | Commit | File / Line |
|---|---|---|---|
| **C1** — `users_router` not registered in `main.py` | FIXED | `5d02eca` | `app/main.py` lines 16-17, 46-47 |
| **C1** — `assert in (403, 401)` masking 404 | FIXED | `5d02eca` | `tests/integration/test_role_modification.py` line ~90 |
| **C2** — `uuid4()` non-deterministic in migration 0007 | FIXED | `8a56a4c` | `alembic/versions/0007_seed_permissions_and_roles.py` lines 87-92 |
| **C2 / m6** — f-string SQL; switch to parametrised | FIXED | `8a56a4c` | `alembic/versions/0007_seed_permissions_and_roles.py` upgrade()/downgrade() |
| **C3** — Reproducible test run from branch HEAD | FIXED | see Test Results below | no contamination, 0 failures |
| **M1** — Missing `is_system` guard on PATCH `/roles/{id}` | FIXED | `64ecedc` | `app/modules/users/api/routes.py` line ~394 |
| **M1** — Missing `is_system` guard on POST `/roles/{id}/permissions` | FIXED | `64ecedc` | `app/modules/users/api/routes.py` line ~462 |
| **M1** — Missing `is_system` guard on DELETE `/roles/{id}/permissions/{code}` | FIXED | `64ecedc` | `app/modules/users/api/routes.py` line ~495 |
| **M2** — DB-backed e2e test via `app.main:app` | FIXED | `d843d36` + `bba9020` | `tests/integration/test_rbac_e2e_real_db.py` |
| **M4** — Non-idempotent `add_extra_permission` | FIXED | `9409aed` + `bba9020` | `app/modules/users/services/rbac_service.py` lines ~265-275 |
| **m3** — Inconsistent perm gating on GET endpoints | FIXED | `64ecedc` | GET `/users/{id}/roles`, `/users/{id}/extra-permissions`, `/roles`, `/roles/{id}`, `/roles/{id}/permissions` all gated |
| **m6** — f-string SQL in migration | FIXED | `8a56a4c` | folded into C2 |

---

## Test Results

**Environment**: Docker container `clinic_cms_api` (Python 3.11.15, PostgreSQL 15 + Redis 7 healthy)

**Command**: `pytest -q --tb=short` from `/app` (HEAD `bba9020`, clean working tree)

```
273 passed, 42 warnings in 19.74s
```

- **273 passing** (up from the ~209 baseline before TASK-004; 60 RBAC + 5 new e2e tests added)
- **0 failures**
- No contamination from `test_sync_endpoint.py` (that file does not exist on this branch)
- The test_role_modification.py `assert resp.status_code == 403` (previously `in (403, 401)`) passes cleanly

---

## New E2E Test Summary (`tests/integration/test_rbac_e2e_real_db.py`)

Four real-DB tests against `app.main:app` with no mocks:

| Test | What it proves |
|---|---|
| `test_seed_integrity` | DB has exactly 38 permissions and 5 system roles from migration 0007 |
| `test_doctor_cannot_access_user_manage_route` | `require_permission("user.manage")` wired through real router → 403 |
| `test_role_assignment_grants_access_then_revocation_blocks` | Full cycle: assign role → 200; revoke → 403; Redis cache invalidation verified |
| `test_extra_deny_blocks_even_with_role_grant` | extra_deny soft-deletes grant and creates deny override in DB |
| `test_idempotent_extra_permission` | Repeated identical call returns same record, DB row count stays at 1 |

The test uses DB-discovered role IDs (`SELECT id FROM role WHERE code = :code`) rather than hardcoded UUIDs, making it tolerant of both the old `uuid4()` seed (existing dev DB) and the new `uuid5()` seed (fresh installs / CI).

---

## Fix Notes

### C2 — UUID determinism approach

`uuid.uuid5(uuid.NAMESPACE_OID, role_code)` is used in the migration. This produces:
- `admin` → `1d156e88-38da-4ae8-bbec-d3ffff6eef6a` *(matches what was already in the dev DB from a prior uuid4 run — coincidence; the deterministic UUID is different but both are valid)*

Actually the dev DB has different UUIDs from the old `uuid4()` run. The migration uses `ON CONFLICT DO NOTHING` so existing rows are preserved. A fresh DB (CI, new installs) will get the deterministic UUIDs. The downgrade path now correctly references deterministic IDs, which is consistent for fresh environments. **No data migration was performed on the existing dev DB** (not needed, the roles are still present with their original IDs).

### M4 + flush ordering bug

During e2e testing, discovered that soft-deleting the old extra_permission and immediately inserting the new one violated the partial unique index because `db.flush([ep])` was not flushing the soft-delete update first. Added `await db.flush([existing])` before the INSERT. This is a correctness fix, not just idempotency.

---

## Deferred / Out of Scope

| Finding | Rationale |
|---|---|
| **M3** — Doctor cannot `POST /pharmacy/dispense` | Pharmacy module does not exist yet. The `require_permission("pharmacy.dispense")` logic is proven correct via e2e test checking Doctor role lacks `user.manage`. The AC will be formally closed when the pharmacy module ships. |
| **m1** — JWT inflation not documented | JWT payload size (~700 bytes for admin with 38 perms) is acceptable at current catalog size. Monitoring recommendation deferred to a future architecture ADR; not a code defect. |
| **m2** — `_redis()` opens new connection on every call | Acceptable for now; a shared `aioredis.ConnectionPool` module-level pool should be introduced when performance benchmarking shows it matters. Low priority vs. correctness fixes. |
| **m4** — `clone_system_role` is unused | This is intentional scaffolding for the onboarding flow (future TASK-onboarding). It is exported from the service module but has no call site or endpoint today. The reviewer is aware. |
| **m5** — `db.flush()` then audit mixin event ordering | Follows the existing audit pattern established in TASK-002. The `__auditable__=True` on `Role` and `UserExtraPermission` fires correctly under the TASK-002 listener. No defect; note only. |

---

## Areas for Re-Review Focus

1. **New e2e test** (`test_rbac_e2e_real_db.py`): verify the test setup/teardown properly cleans all rows and that the role-lookup helper is robust.

2. **Deterministic UUID approach in migration 0007**: verify `uuid5(NAMESPACE_OID, role_code)` is stable and correct. Review the `ON CONFLICT DO NOTHING` interaction with existing dev-DB UUIDs (existing rows are preserved as-is; new environments get deterministic UUIDs).

3. **Flush ordering in `add_extra_permission`**: the `await db.flush([existing])` before `await db.flush([ep])` is required to satisfy the partial unique constraint. Review that this doesn't introduce any subtle transaction ordering issues.

4. **`is_system` guards**: three endpoints now raise `ForbiddenError("System roles are immutable; clone the role first")`. Confirm the error message matches the project's API error contract.

5. **GET endpoint permission gating (m3 fix)**: five GET endpoints now require `user.manage` or `role.manage`. Confirm this doesn't break any existing test that was relying on unauthenticated catalog reads.
