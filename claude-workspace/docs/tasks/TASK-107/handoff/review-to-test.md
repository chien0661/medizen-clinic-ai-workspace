# Handoff: TASK-107 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED
**Date**: 2026-07-24
**Branch**: `fix/TASK-107-auth-session-invariants`
**Worktree**: `F:/MyProject/clinic-cms-workspace/_fix107-be`

## Summary
Security-critical fix for three auth/session/RBAC enforcement gaps (H-5 deactivation,
H-6 password change/reset, H-7 role revoke). Mechanism = version-check via
`user.tokens_valid_after` (DB source of truth) + Redis fast-path `sess:cutoff:{uid}` for
access tokens. Code review confirms all three invariants are correctly enforced across
the middleware, auth service, and RBAC service; migration 0067 is additive/nullable and a
single head. No CRITICAL/MAJOR issues.

## Key Findings (MINOR — awareness only)
- `set_session_cutoff` docstring is stale (claims fractional-epoch same-second rejection;
  callers floor to whole seconds → same-second tokens survive, the accepted <1s race).
- Fail-open on Redis for access tokens is a deliberate, documented tradeoff (refresh stays
  DB-enforced; access ≤15 min).
- Pivot stores role codes not IDs — roles sharing a code are indistinguishable on revoke
  (pre-existing design; codes expected unique).

## Focus Areas for Testing
1. **Run the suite against the real stack** — I could NOT re-run it (Docker `fix107` stack
   pg 5476 / redis 6458 was down; host `ruff` binary is wrong-arch). Bring up the isolated
   stack and confirm `test_auth_session_invariants_real_db.py` (3 tests) all pass, plus the
   auth+rbac regression sweep (~50 tests).
2. **H-5**: after deactivation, verify old access token → 401 on multiple protected routes
   (not just `/api/v1/users`); verify refresh token also blocked via `/auth/refresh`.
3. **H-6**: verify BOTH change-password AND password-reset paths stamp the cutoff (reset via
   `/auth/password-reset/confirm`); old access → 401 AND old refresh → 401; new creds work.
4. **H-7**: verify old token → 403 AND fresh login → 403 for pivot-granted role; also test a
   clinic-scoped role revoke (strips only that clinic's pivot row) vs a system role (strips
   all rows) to confirm scope semantics.
5. **Reactivation**: confirm a re-activated account's NEW login works while pre-deactivation
   tokens stay invalid.
6. **Fail-open sanity**: optional — with Redis unavailable, confirm access tokens degrade to
   expiry-bounded (not a hard lockout) while refresh remains DB-enforced.
7. Confirm the pre-existing failures noted in the implementation handoff are indeed
   pre-existing (identical on baseline `origin/dev`), not regressions from this change.
