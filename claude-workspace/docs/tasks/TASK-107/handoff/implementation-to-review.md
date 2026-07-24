# Handoff: TASK-107 → Code Review

**From**: Code Implementation Agent (FIX MODE)
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-07-24
**Branch**: `fix/TASK-107-auth-session-invariants` (base `origin/dev` @ f305496, alembic head was 0066)

## Summary

Enforced three auth session / RBAC invariants (E2E findings H-5/H-6/H-7) that were
previously not enforced: deactivating an account, changing a password, and revoking
a role now all actually terminate the corresponding access. Cohesive fix across the
tenancy middleware, auth service, RBAC service, user service, and the User model.

## Mechanism chosen (architecture decision — FLAGGED)

**Version-check via a `tokens_valid_after` timestamp**, not blacklist-every-JTI
(the lower-risk option the task suggested when a decision arose).

- New nullable column **`user.tokens_valid_after`** (migration **0067**, additive/nullable,
  single head off 0066). It is the **durable source of truth**.
- A **Redis fast-path** key `sess:cutoff:{user_id}` (TTL = access-token lifetime + 60s)
  lets `TenancyMiddleware` reject stale **access tokens** with an O(1) Redis GET — no
  per-request DB query. Fails **open** on Redis error (mirrors the existing RBAC
  permission-cache resilience) so a Redis outage cannot lock out every user; long-lived
  refresh tokens remain enforced against the DB column regardless.
- Rule everywhere: **reject a token when its `iat` < the cutoff.**

### Known limitation (documented, standard for iat-based schemes)
JWT `iat` has 1-second resolution, so the cutoff is stored **floored to the whole
second**. Consequence: a token minted in the *exact same wall-clock second* as the
invalidating action survives (a <1s race), while a legitimate re-login/refresh in that
same second still works (usability preserved). In practice deactivation/rotation happens
seconds-to-minutes after a token was issued, so the token is always from an earlier
second and is rejected. A fully race-free alternative (embedded token-version counter)
was deliberately not taken — higher blast radius for a marginal gain.

## Per-defect fixes

- **H-5 (deactivate doesn't revoke live access token)** — `user_service.update_user`
  detects an `is_active` true→false transition and stamps `tokens_valid_after = now`
  + publishes the Redis cutoff. `TenancyMiddleware` now rejects any access token whose
  `iat` predates the cutoff (previously it only verified signature/expiry). Refresh
  path already returned `inactive_user`.
- **H-6 (password change doesn't invalidate prior sessions)** —
  `auth_service._apply_new_password` (shared by change-password AND reset) stamps
  `tokens_valid_after = now` + Redis cutoff. Old **access** token → 401 at the
  middleware; old **refresh** token → 401 in `auth_service.refresh` (new DB-authoritative
  `iat < tokens_valid_after` check, since a 7-day refresh token outlives the Redis TTL).
- **H-7 (role revoke is a no-op for pivot-granted roles)** — `rbac_service.revoke_role`
  now also strips the role's `code` from `account_clinic_role.role_codes` (clinic-scoped
  role → that clinic's pivot row; system role → all the user's pivot rows) and invalidates
  the permission cache across all clinics. `assignment_not_found` is raised only when the
  user held the role via *neither* the legacy table *nor* the pivot — so revocation now
  works for pivot-only, legacy-only, and both. Because `require_permission` recomputes
  effective permissions from the DB (not from JWT claims), the **old access token
  immediately drops the permission (403)** and a fresh login lacks it too.

## Files Changed

- `alembic/versions/0067_user_tokens_valid_after.py` — **new** migration (add nullable
  `user.tokens_valid_after`).
- `app/modules/users/models/user.py` — add `tokens_valid_after` column.
- `app/core/token_blacklist.py` — add `set_session_cutoff` / `get_session_cutoff`
  (Redis fast-path, floored-second epoch, fail-open on read).
- `app/core/tenancy.py` — middleware rejects access tokens with `iat < cutoff` (H-5/H-6).
- `app/modules/auth/services/auth_service.py` — `_apply_new_password` stamps cutoff
  (H-6); `refresh()` rejects refresh tokens issued before `tokens_valid_after` (H-6).
- `app/modules/users/services/user_service.py` — `update_user` stamps cutoff on
  deactivation (H-5).
- `app/modules/users/services/rbac_service.py` — `revoke_role` syncs the pivot +
  invalidates cache (H-7).
- `tests/integration/test_auth_session_invariants_real_db.py` — **new** real-DB/Redis
  acceptance tests for H-5/H-6/H-7.
- `tests/integration/test_auth_service_coverage.py` — mock fixture `_make_user` now sets
  `tokens_valid_after = None` (new model field; keeps the refresh() guard a no-op for
  mock users).

## Test Results (real Postgres + Redis, isolated Docker stack `fix107`: pg 5476 / redis 6458)

- **New acceptance tests: 3/3 pass** — H-5 (old access token → 401 after deactivation),
  H-6 (old access → 401 AND old refresh → 401 after password change; new creds work),
  H-7 (pivot cleared in DB; old token → 403 AND fresh login → 403).
- **Regression sweep (auth + rbac, 50 tests): all pass**, incl. refresh rotation
  blacklist, logout, rbac assign/pivot, require_permission, role modification.
- **1 regression found & fixed** during the run: the mock-based
  `test_refresh_success_returns_new_tokens` broke because its MagicMock user lacked the
  new field; fixed by adding `tokens_valid_after = None` to the `_make_user` fixture.
- **Pre-existing failures (NOT caused by this change — verified identical on baseline
  `origin/dev` with the same fully-migrated DB):** `test_auth_service_coverage`
  `test_login_inactive_clinic_raises`, `test_login_success_resets_count_and_returns_tokens`,
  `test_change_password_success` (stale mock config — `scalars().all()` coroutine);
  `test_rbac_e2e_real_db::test_seed_integrity` &
  `test_rbac_e2e_extended::test_admin_has_all_38_permissions` (hardcode "38 permissions"
  but later migrations 0057/0058 added `staff.manage`/`payroll.manage`);
  `test_rbac_e2e_real_db::test_role_assignment_grants_access_then_revocation_blocks`
  (fails at "Step 2 assign" on baseline too — environmental). These predate TASK-107.

## Static analysis

- `ruff` on all changed files: **0 new** (2 residual hits are pre-existing lines not in
  this diff — the `applied_role` SIM102 in tenancy.py and the feature-flags I001 import
  in rbac_service.py; confirmed absent from `git diff origin/dev`).
- `mypy app`: **0 new** (the only line touching a changed file is the pre-existing
  `jose` missing-stubs warning at tenancy.py; the two errors my first draft introduced in
  rbac_service.py were removed by rewriting the pivot update in plain ORM/Python).

## Areas for Review Focus

1. **Fail-open on Redis in the middleware** (`get_session_cutoff`) — confirm the
   security posture is acceptable (refresh tokens stay DB-enforced; access tokens are
   ≤15 min). Flip to fail-closed if policy demands it.
2. **Same-second `iat` race** — confirm the documented <1s window is acceptable vs a
   token-version counter.
3. **H-7 system-role removal scope** — a system role (`clinic_id IS NULL`) is stripped
   from *all* of the user's pivot rows; verify that matches intended semantics for a
   user who is a member of multiple clinics.
4. The `.replace(microsecond=0)` flooring also floors `password_changed_at` — harmless
   (second precision), but noting it.

## Not run
FE/UI unaffected (backend-only). No load/perf test of the extra per-request Redis GET.
