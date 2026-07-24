# Test Report: TASK-107 - Bất biến phiên/RBAC (H-5/H-6/H-7)

**Test Agent:** Automation Tester
**Date:** 2026-07-24
**Status:** ✅ ALL IN-SCOPE PASSED (3/3 acceptance; 0 new regressions)

## Environment

- Worktree: `F:/MyProject/clinic-cms-workspace/_fix107-be`, branch `fix/TASK-107-auth-session-invariants` (base `origin/dev` @ f305496, HEAD f4f09b1).
- Isolated Docker stack, project `v107`: api `9974` / postgres `5474` / redis `6456` (standalone compose file with absolute paths — the checked-out `docker/docker-compose.yml` port mappings cannot be overridden via compose file merge since Compose concatenates `ports:` arrays rather than replacing them; used a full standalone file instead of `-f base -f override`).
- **Environment note (no source touched):** `docker/docker-start.sh` and `docker/postgres-init.sql` in this worktree checkout have CRLF line endings (`core.autocrlf=true`), which breaks `bash`/`set -e` inside the Linux container. Worked around by mounting an `tr -d '\r'`-normalized copy of `docker-start.sh` from the scratchpad over the container path — the tracked file in the worktree was never modified (`git status` stayed clean throughout).
- Alembic migrated to **head = 0067** (`user.tokens_valid_after`, single head off 0066). Seed completed (13 staff, 19 patients, etc.). API `/health` → 200.
- Teardown: `docker compose -p v107 down -v` (containers + volume + network removed). Confirmed no `v107*` containers remain.
- `docker_cms_w2e_*` (main/dev/w2e stack, ports 9999/5434/5436/6380/6382) verified untouched before and after — same containers, same "Up" duration, no restarts.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Acceptance (H-5/H-6/H-7, real DB+Redis) | 3 | 3 | 0 | 100% |
| Regression sweep (`-k "auth or rbac or user"`, `tests/integration`) | 196 | 183 | 13 | 93.4% (all 13 verified pre-existing, see below) |
| **TOTAL** | **199** | **186** | **13** | **93.5%** |

## Acceptance Criteria (H-5/H-6/H-7) — RAW RESULTS

- **H-5** — deactivate user → old access token → **401**: **PASS**
- **H-6** — change password → old access **401** AND old refresh **401** (new creds work): **PASS**
- **H-7** — revoke pivot-granted role → old token **403** AND fresh login lacks perm (**403**): **PASS**

```
tests/integration/test_auth_session_invariants_real_db.py::TestSessionInvariants::test_h5_deactivation_revokes_live_access_token PASSED
tests/integration/test_auth_session_invariants_real_db.py::TestSessionInvariants::test_h6_password_change_invalidates_prior_sessions PASSED
tests/integration/test_auth_session_invariants_real_db.py::TestSessionInvariants::test_h7_pivot_role_revocation_removes_permission PASSED
3 passed in 8.02s
```

## Regression Sweep — Failures Verified as Baseline (NOT new)

Ran `pytest -k "auth or rbac or user" tests/integration` on the fix branch: **13 failed, 183 passed**.
To verify none are regressions, built a second isolated stack (`v107base`, ports 9975/5475/6457) from
a fresh `origin/dev` worktree (no TASK-107 changes) and ran the identical command: **13 failed, 180 passed**
(same 13 test IDs; the fix branch has 3 extra passing tests — the new acceptance file itself).

| # | Test | On fix branch | On origin/dev baseline | Root cause |
|---|------|---|---|---|
| 1 | `test_auth_service_coverage::test_login_inactive_clinic_raises` | FAIL | FAIL | Stale mock config (`scalars().all()` coroutine) — documented in impl handoff |
| 2 | `test_auth_service_coverage::test_login_success_resets_count_and_returns_tokens` | FAIL | FAIL | Same as above |
| 3 | `test_auth_service_coverage::test_change_password_success` | FAIL | FAIL | Same as above |
| 4 | `test_rbac_e2e_real_db::test_seed_integrity` | FAIL | FAIL | Hardcoded "38 permissions" predates migrations 0057/0058 |
| 5 | `test_rbac_e2e_extended::test_admin_has_all_38_permissions` | FAIL | FAIL | Same as above |
| 6 | `test_rbac_e2e_real_db::test_role_assignment_grants_access_then_revocation_blocks` | FAIL | FAIL | Fails at "Step 2 assign" — environmental, predates TASK-107 |
| 7 | `test_auth_lockout_real_db::test_lockout_end_to_end` | FAIL | FAIL | Not in diff scope; identical failure both branches |
| 8 | `test_auth_mfa::test_new_ip_sets_requires_mfa_challenge` | FAIL | FAIL | Not in diff scope |
| 9 | `test_auth_mfa::test_mfa_enabled_returns_mfa_token` | FAIL | FAIL | Not in diff scope |
| 10 | `test_auth_mfa::test_mfa_token_wrong_type_rejected` | FAIL | FAIL | Not in diff scope |
| 11 | `test_jwt_includes_perms::test_login_calls_rbac_service` | FAIL | FAIL | Not in diff scope |
| 12 | `test_jwt_includes_perms::test_login_jwt_contains_rbac_data` | FAIL | FAIL | Not in diff scope |
| 13 | `test_rls_admin_bypass::test_cms_app_role_is_not_superuser` | FAIL | FAIL | `cms_app` Postgres role password mismatch: migration `0004_create_app_role.py` hardcodes password `cms_app_change_in_production`; the test fixture (`_ensure_cms_app_role`) only sets password `cms_app` when the role doesn't already exist — on any freshly-migrated DB the migration wins first, so the test's connection auth-fails. Neither file is touched by the TASK-107 diff (`git diff origin/dev...HEAD --stat` confirms). |

**Conclusion:** Items 1–6 match the 6 pre-existing failures documented in the implementation/review handoffs.
Items 7–13 are additional failures surfaced by running the broader `auth service/mfa, jwt-perms` sweep the
review handoff asked for — none of the 7 touch files changed by TASK-107, and all 7 reproduce identically,
same test IDs, on a fresh `origin/dev` worktree with no TASK-107 code. **Zero new regressions.**

## Business Rules Validated

### H-5 — Account deactivation revokes live access
- ✅ Old access token → 401 immediately after `is_active` false transition — VERIFIED real Postgres+Redis

### H-6 — Password change invalidates prior sessions
- ✅ Old access token → 401 — VERIFIED
- ✅ Old refresh token → 401 (DB-authoritative `iat < tokens_valid_after`) — VERIFIED
- ✅ New credentials issue working tokens — VERIFIED

### H-7 — Role revoke removes effective permission (pivot sync)
- ✅ Pivot (`account_clinic_role.role_codes`) cleared in DB — VERIFIED
- ✅ Old access token → 403 — VERIFIED
- ✅ Fresh login lacks the revoked permission → 403 — VERIFIED

All acceptance criteria from `docs/tasks/TASK-107/task.md` VALIDATED ✓

## Coverage

### Migration
- ✅ Alembic reaches head = **0067** cleanly on a fresh DB (single head, no branch conflicts).

### Database Operations
- ✅ `user.tokens_valid_after` column read/write verified via real Postgres.
- ✅ Redis `sess:cutoff:{uid}` fast-path verified via real Redis (isolated container, no mocks).
- ✅ Pivot table (`account_clinic_role.role_codes`) revoke-sync verified.

## Test Files (pre-existing, from Implementation Agent — none created/modified by Test Agent)

- `tests/integration/test_auth_session_invariants_real_db.py` (3 acceptance scenarios: H-5, H-6, H-7)
- `tests/integration/test_auth_service_coverage.py` (regression, mock fixture patch for new field)

## Next Steps

All in-scope tests passed (3/3 acceptance; 13/13 pre-existing failures confirmed baseline-identical
on `origin/dev`, zero new). Ready to proceed to Documentation phase.

**Task status → DOCUMENTING.**

---

**Test Execution Time:** ~4 minutes (build + migrate + seed + 2 pytest runs on fix stack + 1 baseline stack build/run)
**Total Scenarios:** 199 (3 acceptance + 196 regression sweep)
**Environment:** isolated Docker (`v107`: api 9974 / pg 5474 / redis 6456), torn down after run; baseline comparison stack (`v107base`: api 9975 / pg 5475 / redis 6457), torn down after run. `w2e`/main/dev stack (9999/5434/5436/6380/6382) untouched throughout.
