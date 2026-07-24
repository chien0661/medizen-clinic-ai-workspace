# Review Report: TASK-107 — auth session/RBAC invariants (H-5/H-6/H-7)

**Reviewer**: Code Review Agent
**Date**: 2026-07-24
**Branch**: `fix/TASK-107-auth-session-invariants` (base `origin/dev` @ f305496)
**Worktree**: `F:/MyProject/clinic-cms-workspace/_fix107-be`
**Diff reviewed**: `git diff origin/dev...HEAD --unified=3` (9 files, +552/-6)

## Decision: APPROVED → IN_TESTING

Security-critical review of the fix for three auth/session/RBAC enforcement gaps.
Mechanism (version-check via `user.tokens_valid_after`, Redis fast-path for access
tokens + DB-authoritative for refresh) is sound and correctly wired. All three
invariants are genuinely enforced. No CRITICAL or MAJOR issues.

---

## Invariant enforcement — verified

### H-5 — deactivation revokes live access token ✓
- `user_service.update_user` detects `is_active` true→false (`deactivated = was_active
  and user.is_active is False`) and stamps `tokens_valid_after = now` + `set_session_cutoff`.
- `TenancyMiddleware` (`tenancy.py:222-230`) rejects any Bearer JWT whose `iat < cutoff`
  for `user_id` present. This is a **global** middleware; the whitelist (`tenancy.py:47-64`)
  contains only pre-auth endpoints (login/refresh/logout/reset/otp/health/docs), so **every
  authenticated route** passes through the cutoff check. Confirmed: no authenticated
  business route bypasses it.
- Re-activation does NOT clear `tokens_valid_after` — correct: tokens issued before
  deactivation stay invalid; new logins (iat > cutoff) work. No harmful lockout.

### H-6 — password change/reset invalidates prior sessions ✓
- `_apply_new_password` (`auth_service.py:767-787`) stamps cutoff + Redis fast-path, and is
  shared by BOTH `change_password` (action `user.password_changed`) and password-**reset**
  (`user.password_reset`) — verified both callers (auth_service.py:822, 908). Reset covered.
- Old **access** token → 401 at middleware. Old **refresh** token → 401 in
  `refresh()` (`auth_service.py:594-601`) via the **DB-authoritative** `iat <
  tokens_valid_after` check (necessary because a 7-day refresh token outlives the Redis TTL).
- Tokens carry `iat` (security.py:81/113), so the comparison is well-defined.

### H-7 — role revoke removes effective permission ✓
- `revoke_role` (`rbac_service.py:443-495`) now strips the role `code` from the
  `account_clinic_role.role_codes` pivot (clinic role → that clinic's row; system role
  → all the user's rows) with a fresh-list reassignment (correct SQLAlchemy ARRAY dirty
  tracking), deletes the legacy `user_role` row if present, and calls
  `invalidate_user_cache(user_id)` with no clinic → clears ALL clinic caches.
- `assignment_not_found` raised only when neither legacy nor pivot held the role — so
  revocation works for pivot-only, legacy-only, and both.
- `require_permission` recomputes from DB (`get_user_effective_permissions` merges legacy
  + pivot), so the old access token immediately drops the permission (403) and a fresh
  login lacks it too. Matches the pivot merge logic at rbac_service.py:220-241.

---

## Flagged items — verdicts

1. **Middleware fails OPEN on Redis error** (`get_session_cutoff`): **ACCEPT.**
   Refresh tokens remain DB-enforced regardless; access tokens are ≤15 min; fail-closed
   would lock out every user on a Redis outage (worse availability). Mirrors existing RBAC
   permission-cache resilience. Documented residual risk — reasonable engineering tradeoff.

2. **Same-second `iat` race (<1s)**: **ACCEPT.** Callers floor cutoff to whole seconds
   (`.replace(microsecond=0)`); a token minted in the exact same wall-clock second survives.
   Standard limitation of iat-based invalidation; invalidation realistically happens
   seconds-to-minutes after issuance. Tests explicitly `sleep(1.1)` to model the real
   threat window.

3. **System-role revocation strips from ALL clinics**: **ACCEPT — correct semantics.**
   A system role (`clinic_id IS NULL`) resolves in every clinic (effective-perms uses
   `Role.clinic_id == clinic_id OR IS NULL`), so removing it everywhere matches enforcement.
   Not over-stripping. (Caveat below.)

---

## Findings

### MINOR
- **Stale docstring** (`token_blacklist.py` `set_session_cutoff`): claims the cutoff is
  stored as a *fractional* epoch "so a token issued in the same second … is still correctly
  rejected." Both callers pass a value already floored to whole seconds, so same-second
  tokens actually **survive** (the accepted race in item 2). Behaviour is fine and matches
  the handoff; only the docstring is misleading. Doc-only.
- **Pivot stores role codes, not IDs** (pre-existing design): two distinct roles sharing a
  `code` would be indistinguishable on revoke. Not introduced by this change; role codes are
  expected globally unique. Noted for awareness only.
- **Inline imports** in `update_user` (`datetime`, `set_session_cutoff`, `# noqa: PLC0415`):
  acceptable to dodge a circular import, slightly inconsistent with module-level imports.
- **Redundant guard**: `if exp_ts is not None:` around the tva check in `refresh()`
  (auth_service.py:598) — `exp_ts` is already validated non-None at line 550. Harmless.

---

## Migration 0067
- Single head confirmed: only 0067 revises 0066; nothing revises 0067; one `0067*` file.
- Additive + nullable (`tokens_valid_after DateTime(timezone=True) NULL`), NULL = no cutoff
  (no behaviour change for untouched accounts). Clean `downgrade()`. No data migration.

## Security scan
- No hardcoded secrets, no sensitive data logged (logs use `user_id` only).
- **No SQL injection**: production path uses ORM; test raw SQL is fully parametrized
  (`:uid`/`:cid`/`:code` bound params; `'{admin}'` is a static array literal).
- Per-request cost: one O(1) Redis GET in the middleware hot path (fast-path, no DB query);
  acceptable. Refresh adds one DB column read — refresh is low-frequency. OK.

## Quality checks
- `ruff` / `mypy` on host: **NOT runnable** — host `ruff` binary is wrong-architecture
  (`Exec format error` / `WinError 193`), confirming the handoff's "host tooling may be
  broken" note. `python -m py_compile` on all 8 changed files **passes**. Handoff reports
  `ruff`/`mypy` 0-new from the implementation environment; spot-review of the diff found no
  obvious lint/type regressions.
- **Test suite NOT re-run**: isolated Docker stack `fix107` (pg 5476 / redis 6458) is not
  currently up. Handoff reports 3/3 new acceptance + 50/50 regression pass on that stack,
  and documents the pre-existing failures as verified identical on baseline `origin/dev`.
  Deferred to the Test Agent (IN_TESTING) to validate against real DB — see handoff.

## Tests
- `test_auth_session_invariants_real_db.py` drives `app.main:app` through the real router +
  real `TenancyMiddleware` + real Postgres/Redis (no mocks). Asserts each invariant against
  the acceptance criteria: H-5 old access→401; H-6 old access→401 AND old refresh→401 AND
  new creds→200; H-7 pivot cleared in DB AND old token→403 AND fresh login→403. Target user
  holds `admin` via pivot ONLY, so H-7 exercises the pivot-sync path specifically. Genuine
  assertions, not coverage-padding. Proper fixture teardown (DB rows + Redis keys).
