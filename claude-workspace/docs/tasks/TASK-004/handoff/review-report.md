# Review Report: TASK-004 RBAC (Iteration 2)

**Reviewer**: Code Review Agent
**Date**: 2026-04-27
**Branch**: `feature/task-004-rbac`
**HEAD reviewed**: `bba9020` (iteration 2)
**Previous HEAD**: `97f7bce` (iteration 1)
**Iteration limit**: 3 (per PROJECT.md `Max Review Iterations`); this is iteration 2.

---

## Verdict: APPROVED

All CRITICAL findings from iteration 1 are VERIFIED resolved. All MAJOR findings are VERIFIED resolved or DEFERRED OK with sound rationale. Test suite runs cleanly: **273 passed, 0 failed** in 18.83s in the live Docker environment, executed by the reviewer this iteration (Docker was responsive).

---

## Test Run

`docker exec clinic_cms_api pytest -q --tb=line` against branch HEAD `bba9020`:

```
273 passed, 42 warnings in 18.83s
```

Execution corroborates the handoff's claimed numbers exactly. Reviewer was able to run pytest this iteration (unlike iteration 1 when Docker was unresponsive). C3 verified by direct execution, not just static analysis.

---

## Iteration-1 Findings — Verification Status

| ID | Finding | Status | Evidence |
|---|---|---|---|
| **C1** | `users_router` not registered + tightened 403 assertion | **VERIFIED** | `app/main.py` lines 17 & 48 import + `include_router(users_router)`; `tests/integration/test_role_modification.py:90` now `assert resp.status_code == 403`. |
| **C2** | Deterministic UUIDs + parameterised SQL | **VERIFIED** | `alembic/versions/0007_seed_permissions_and_roles.py` lines 87-92 use `uuid.uuid5(uuid.NAMESPACE_OID, code)`; all `op.execute` calls switched to `sa.text(...).bindparams(...)`; permissions inserted via `op.bulk_insert`. `rbac_seed_data.py` re-imports the migration so the same uuid5 IDs are exposed to test code. |
| **C3** | Reproducible test run | **VERIFIED** | Reviewer executed `pytest -q` against HEAD `bba9020`: 273 passed / 0 failed. `tests/unit/test_sync_endpoint.py` confirmed absent on this branch. |
| **M1** | `is_system` guard on PATCH/POST/DELETE role mutation | **VERIFIED** | `app/modules/users/api/routes.py` adds `if role.is_system: raise ForbiddenError(...)` on `update_role` (line 407), `add_role_permission` (line 482), and `remove_role_permission` (line 526). DELETE endpoint also now fetches and checks the role before attempting deletion. |
| **M2** | Real DB-backed e2e test through `app.main:app` | **VERIFIED** | `tests/integration/test_rbac_e2e_real_db.py` (478 lines, 5 tests) — no mocks, real Postgres + Redis, full assign→effective→revoke cycle, seed assertion (38 perms / 5 roles), Redis cache populate-then-invalidate verification, extra_deny soft-delete + active-deny verification, M4 idempotency check. |
| **M3** | `pharmacy.dispense` deferral | **DEFERRED OK** | Pharmacy module not built yet; handoff explicitly notes AC will close when that module ships. The e2e test exercises an equivalent permission gate (`user.manage`) through the real router. |
| **M4** | `add_extra_permission` idempotency | **VERIFIED** | `app/modules/users/services/rbac_service.py:272-274` — short-circuits when `existing.type == perm_type and existing.reason == reason`. e2e test `test_idempotent_extra_permission` validates: same `id` returned twice, exactly 1 active row in DB. |
| **m1** | JWT inflation not documented | **DEFERRED OK** | Acceptable; flagged for a future ADR. |
| **m2** | `_redis()` opens new connection per call | **DEFERRED OK** | Performance optimisation deferred behind benchmarking; correctness unaffected. |
| **m3** | GET endpoint perm gating | **VERIFIED** | Five GETs now have `dependencies=[Depends(require_permission("user.manage" or "role.manage"))]`: `/users/{id}/roles`, `/users/{id}/extra-permissions`, `/roles`, `/roles/{id}`, `/roles/{id}/permissions`. No existing test broke (273 pass). |
| **m4** | `clone_system_role` unused | **DEFERRED OK** | Intentional scaffolding for onboarding flow; documented in handoff. |
| **m5** | flush+audit ordering | **DEFERRED OK** | Follows existing TASK-002 pattern; no defect found. |
| **m6** | f-string SQL in migration 0007 | **VERIFIED** | Folded into C2; all SQL now parameterised via `sa.text().bindparams()` or `op.bulk_insert`. |

**Summary: 7 VERIFIED, 6 DEFERRED OK, 0 NOT FIXED, 0 PARTIAL, 0 REGRESSION.**

---

## Special Checks

### 1. Deterministic UUIDs vs. existing dev DB

Confirmed: existing dev DB has **uuid4** UUIDs from a prior seed run (e.g. admin = `1d156e88-...`). Migration's `ON CONFLICT DO NOTHING` preserves them. Newly computed `uuid5(NAMESPACE_OID, "admin")` is `ae6c10d0-...` — different.

**On a fresh DB** (CI, prod first-deploy): upgrade inserts uuid5 IDs; downgrade deletes them by the same uuid5 IDs → symmetric. Correct.

**On the existing dev DB**: rows persist with old uuid4 IDs; `alembic downgrade 0007` would attempt `DELETE FROM role WHERE id = '<uuid5>'` and miss the existing rows, leaving them orphaned (with cascaded `role_permission` rows still present pointing at old role IDs).

This is acknowledged in the handoff as a one-time dev-only data anomaly. Test code mitigates the issue by discovering role IDs via `SELECT id FROM role WHERE code = :code` (see `test_rbac_e2e_real_db.py:_get_role_id_by_code`), so all 273 tests pass against the legacy dev DB. This is **acceptable** for the current state because:

- CI starts from a clean DB → no anomaly
- Prod is not yet deployed → no anomaly
- A dev who needs to reset can run `alembic downgrade base && alembic upgrade head`, with a one-line manual cleanup of any orphaned legacy rows

Recorded as a MINOR follow-up below.

### 2. Flush ordering in `add_extra_permission`

The `await db.flush([existing])` between the soft-delete UPDATE and the new INSERT is **necessary and correct**:

- The partial unique index `uq_user_extra_perm_user_code ON user_extra_permission (user_id, permission_code) WHERE NOT is_deleted` (verified at `alembic/versions/0006_setup_rbac.py:286-292`) requires no two rows with the same `(user_id, permission_code)` while both are `is_deleted = FALSE`.
- Without the explicit flush, SQLAlchemy could issue the INSERT before the UPDATE, violating the constraint at the DB.
- Audit log emission via `__auditable__=True` listeners fires on `after_flush`; both events fire in the right order — soft-delete logged before insert.
- Both writes share one transaction → rollback unwinds both → no partial-state leak.

The e2e test `test_extra_deny_blocks_even_with_role_grant` exercises this path and asserts the expected DB state (one soft-deleted grant + one active deny). It passes.

### 3. GET endpoint gating regression check

m3 fix added `Depends(require_permission(...))` to five GET endpoints. Could break existing tests that relied on un-gated reads. Confirmed no regressions: all 273 tests pass. None of the previous TASK-002/TASK-003 tests assert against these new RBAC endpoints; the role/permission catalog reads were always considered admin-only.

### 4. `is_system` error message contract

`ForbiddenError("System roles are immutable; clone the role first")` is valid per `app/core/exceptions.py:57-61`: free-form `message`, fixed `code="FORBIDDEN"`, `http_status=403`. Matches the project's error envelope.

### 5. e2e test quality

Read carefully (`tests/integration/test_rbac_e2e_real_db.py`):
- **Setup**: creates Clinic + 2 Users + 2 user_role assignments via real ORM/SQL, no fixtures over-mocked.
- **Teardown**: ordered DELETE (extra_perm → user_role → user → clinic) + Redis key cleanup. Correct dependency order.
- **Role lookup**: discovers IDs by code from DB → tolerant of uuid4 (legacy dev) or uuid5 (fresh) seeds.
- **Cache check**: actually queries Redis directly (`aioredis.from_url(settings.REDIS_URL).get(...)`) before and after revocation — not just "assume it works."
- **Real router**: uses `AsyncClient(transport=ASGITransport(app=app))` against `app.main:app` (no `_test_app` rebuild, no dependency overrides). This is exactly what M2 demanded.
- **Assertions**: precise — `== 403`, `== 200`, `== 204`, `== 201`. No loose `in (...)` patterns.

This test is high quality. Minor nit: `limiter.reset()` in the client fixture is blunt and could affect concurrent runs, but acceptable.

---

## Acceptance-Criteria Verification

| AC | Status | Evidence |
|---|---|---|
| AC1: 5 system roles + 38 perms seeded | **PASS** | `test_seed_integrity` asserts `perm_count == 38, role_count == 5` against live DB. |
| AC2: Default mapping per BA §13.6 | **PASS** | Iteration-1 LOGIC PASS unchanged; `ROLE_PERMISSIONS` dict in `0007_seed_permissions_and_roles.py` matches §13.6. |
| AC3: Doctor cannot POST /pharmacy/dispense (403) | **DEFER** | Pharmacy route doesn't exist; equivalent guard (`user.manage`) verified for doctor in e2e. Will close when pharmacy module ships. |
| AC4: extra_deny over role grant blocks | **PASS** | `test_extra_deny_blocks_even_with_role_grant` validates DB state after grant→deny sequence. Logic + test both PASS. |
| AC5: Role change effective in next request | **PASS** | `test_role_assignment_grants_access_then_revocation_blocks` covers full cycle and asserts Redis cache populated after first request, gone after revoke. |

---

## Optional Follow-Ups (do not block approval)

1. **Dev-DB UUID cleanup**: existing dev DBs have legacy uuid4 role IDs. A migration-time `UPDATE role SET id = uuid5_value WHERE code = 'admin' AND clinic_id IS NULL` (or equivalent) would harmonise them with the new deterministic IDs and make `alembic downgrade 0007` clean against legacy DBs. Low priority; out of scope for this task.
2. **JWT permission bitmap**: m1 from iteration 1. Once permission catalog approaches ~100, the inflated `Authorization` header becomes a real concern. Track in a future ADR.
3. **Redis pool**: m2. A module-level `aioredis.ConnectionPool` would eliminate connection setup cost per cache call. Defer until benchmarking shows it matters.
4. **`clone_system_role` wiring**: m4. Should be wired in TASK-onboarding when system roles need per-clinic customisation.

---

## Quality Gate Summary (PROJECT.md)

- **Coverage threshold (80% new code)**: not measured directly; pytest run did not include coverage flag. Test count grew from baseline ~209 to 273 (+64 RBAC tests including 5 real-DB e2e). Test density is high; the Test Agent should run with `--cov` to confirm threshold.
- **Test pass rate**: 273/273 = 100% PASS.
- **Review iteration limit**: 3. This is iteration 2 ending in APPROVED → no further review iteration needed.
- **Lint**: not run by reviewer; deferred to commit-push-pr / Test Agent stage.

---

## Items Explicitly Re-Confirmed

- Schema design from iteration 1 unchanged → still good.
- `effective = (role_perms ∪ extra_grants) − extra_denies` algorithm unchanged.
- Migration 0006 RLS + indexes unchanged.
- `auth_service.login`/`refresh` integration unchanged.
- `__auditable__=True` listeners fire correctly under TASK-002 patterns (validated by no test failures).

---

## Decision Rationale

All blocking issues resolved. The new e2e test in particular goes well beyond the minimum M2 ask — it exercises five distinct scenarios through the real app+DB+Redis stack and is written defensively (DB-discovered role IDs, explicit cache-presence assertions, ordered teardown). Iteration-2 surgical scope was honoured: 6 commits, 6 files touched, no unrelated changes. Ready for the Test Agent to run their broader test plan and validate ACs end-to-end.
