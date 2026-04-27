# Handoff: TASK-004 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED (iteration 2)
**Date**: 2026-04-27
**Branch**: `feature/task-004-rbac`
**HEAD**: `bba9020`

---

## Summary

RBAC implementation passed code review on iteration 2 after surgical fixes addressed all CRITICAL and MAJOR findings. 273 tests pass cleanly in the live Docker environment. Reviewer ran `docker exec clinic_cms_api pytest -q --tb=line` and confirmed 273 passed / 0 failed in 18.83s. Code is now ready for the Test Agent's deeper testing pass — full AC validation, coverage measurement, and any edge-case exploration.

---

## Scope of Required Testing

The reviewer's pass was a **focused re-review** of iteration-1 findings. The Test Agent should now do a **broader testing pass**:

1. **Run full test suite with coverage** — confirm new code meets the 80% threshold from PROJECT.md.
2. **Validate AC1–AC5 end-to-end** — see checklist below.
3. **Edge-case exploration** beyond what the implementation tests cover:
   - Multi-role users (assign 2+ roles, verify permission union)
   - Soft-deleted users still cached in Redis (cache TTL behavior)
   - Concurrent role assignment + revocation race conditions
   - JWT replay after role change (stale token still grants old perms? — by design, until token expiry)
   - extra_grant + extra_deny on same permission (deny wins)
   - extra_perm survives role revocation (per-user override is independent of role membership)
4. **Negative paths**:
   - PATCH `/roles/{id}` on system role → 403 with `code: "FORBIDDEN"`
   - POST `/roles/{id}/permissions` on system role → 403
   - DELETE `/roles/{id}/permissions/{code}` on system role → 403
   - GET `/roles` without `role.manage` → 403
   - Anonymous calls to any RBAC endpoint → 401

---

## AC Checklist for Test Agent

| AC | What to verify |
|---|---|
| **AC1** | DB seed: `SELECT COUNT(*) FROM permission` = 38; `SELECT COUNT(*) FROM role WHERE clinic_id IS NULL AND is_system = TRUE` = 5. All 5 expected role codes present (`admin, doctor, nurse, pharmacist, receptionist`). |
| **AC2** | Default role-permission mapping matches BA §13.6. Spot-check at least: admin has all 38, doctor has `vital.write`, pharmacist has `pharmacy.dispense`, nurse does NOT have `prescription.write`. |
| **AC3** | DEFERRED — pharmacy module not built. Confirm with manager before closing this AC. The equivalent test on `user.manage` for doctor returning 403 satisfies the spirit. |
| **AC4** | User with role granting permission X + extra_deny on X → API call requiring X returns 403. Existing test `test_extra_deny_blocks_even_with_role_grant` validates the DB state; add an end-to-end assertion that the user's actual API call is blocked. |
| **AC5** | Role assignment/revocation invalidates Redis cache; next request gets fresh permissions. `test_role_assignment_grants_access_then_revocation_blocks` covers this. Suggest a regression test where the user's old JWT (issued before revocation) fails on the protected route — by design, the JWT permission claim is computed fresh from cache on each request via `require_permission`, so this should already work. |

---

## Known DB / Redis Dependencies

- **PostgreSQL 15** with `pg_trgm` and `uuid-ossp` extensions, running in `clinic_cms_postgres` container (port 5432, db `cms`, user `cms`).
- **Redis 7** running in `clinic_cms_redis` container.
- All migrations through head (`0007`) must be applied. The seed migration is idempotent (`ON CONFLICT DO NOTHING`).
- Test infra uses NullPool + per-test fixture cleanup; see `tests/integration/test_rbac_e2e_real_db.py` for the canonical pattern.
- Rate limiter (`app.core.rate_limit.limiter`) is reset per test to avoid bleed between tests; the e2e fixture handles this.

---

## Recommended Starting Point

Begin with `tests/integration/test_rbac_e2e_real_db.py` — it's the highest-fidelity test in the suite and the cleanest demonstration of how to set up a real-DB scenario. All other RBAC tests (`tests/integration/test_rbac_*.py`, `tests/integration/test_role_modification.py`, etc.) are pure-mock unit tests and validate logic only — useful for fast feedback loops but not for AC validation.

For broader coverage, consider extending `test_rbac_e2e_real_db.py` with:
- Multi-role assignment scenario
- extra_perm survival across role revocation
- Concurrent assign+revoke (asyncio.gather race)
- JWT-replay stale-permission case

---

## Files Changed Since Iteration 1

| File | Change |
|---|---|
| `app/main.py` | +2 lines: import + register `users_router` |
| `alembic/versions/0007_seed_permissions_and_roles.py` | uuid4 → uuid5; f-string SQL → `op.bulk_insert` + `sa.text().bindparams()` |
| `app/modules/users/api/routes.py` | +38 lines: `is_system` guards on 3 mutation endpoints; `require_permission` on 5 GET endpoints |
| `app/modules/users/services/rbac_service.py` | +11 lines: idempotency check + flush ordering in `add_extra_permission` |
| `tests/integration/test_role_modification.py` | Tightened `assert in (403, 401)` → `== 403` |
| `tests/integration/test_rbac_e2e_real_db.py` | NEW — 478 lines, 5 real-DB e2e tests |

---

## Findings Carried Over (informational only)

The following iteration-1 findings were accepted as **DEFERRED OK** by review and may surface in the Test Agent's exploration:

- **m1 (JWT inflation)**: admin JWT carries 38 permission claims (~700 bytes). Acceptable now; Test Agent may want to capture an actual size measurement.
- **m2 (Redis connection per call)**: not optimal but functionally correct.
- **m4 (`clone_system_role` unused)**: dead code today; will be wired in onboarding flow.
- **m5 (audit ordering)**: validated by passing tests; no action required.

If the Test Agent finds a defect related to any of these, escalate as a new bug report rather than reopening the review.

---

## What to Submit Back

Standard test-agent deliverables per `.claude/agents/test.md`:
- Test plan + test cases (in `docs/tasks/TASK-004/deliveries/test-cases/`)
- Test report with results (in `docs/tasks/TASK-004/deliveries/test-reports/`)
- Coverage report (PROJECT.md threshold = 80% new code)
- Any defects → `docs/tasks/TASK-004/bugs/`
- On PASS → handoff to Documentation Agent
