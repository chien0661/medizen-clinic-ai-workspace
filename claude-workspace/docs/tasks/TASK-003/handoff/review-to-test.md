# Handoff: TASK-003 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED
**Date**: 2026-04-27

## Summary

Auth module passes code review with no critical security issues. The `SET LOCAL` f-string trace was verified safe (UUID-only writers via TenancyMiddleware), JWT decode pins the algorithm, refresh rotation revokes the old jti before issuing new tokens, and bcrypt cost 12 is used directly without passlib. 186/186 tests pass; lint clean on TASK-003 files. Two MAJOR test-gap findings are routed to you below — implementation is correct, but the most security-critical AC is not exercised end-to-end.

## Key Findings (from review-report.md)

- **Major #1**: `test_locked_user_returns_423` only mocks the service raising `locked_user`. The actual 5-fails → lockout → 423 chain (real DB + Redis) is NOT tested. AC explicitly demands this.
- **Major #2**: Refresh rotation has no test that proves the old jti is blacklisted after a *successful* refresh. Only logout→refresh-blacklist is tested.
- **Minor**: Slowapi limiter is in-process (multi-worker production gap). Username enumeration timing leak. `change-password` does not invalidate existing refresh tokens. Defensive UUID cast missing in `db.py:get_db`.
- **Coverage** not measured (tool not wired in docker pytest target — TASK-001 carryover).

## Focus Areas for Testing

Mandatory new tests (close MAJOR review gaps):

1. **End-to-end account lockout** — against real DB + Redis (per BA §22):
   - Create a user with known password.
   - POST `/api/v1/auth/login` 5× with wrong password → assert each returns 401.
   - Re-fetch user from DB → assert `is_locked is True` and `failed_login_count == 5`.
   - 6th attempt (any password) → assert 423 `LOCKED`.
   - Verify a `user.locked` audit row exists.
   - Verify `lockout:{clinic_id}:{username}` key in Redis with TTL ≈ `LOCKOUT_WINDOW_MINUTES * 60`.

2. **Refresh rotation blacklists old jti** — against real Redis:
   - Login → capture `refresh1`, decode to get `jti1`.
   - Call refresh with `refresh1` → capture `refresh2`.
   - Assert `await is_revoked(jti1) is True`.
   - Call refresh with `refresh1` again → assert 401 (revoked_token).
   - Decode `refresh2` → assert `jti2 != jti1` and type=="refresh".

Recommended additional tests:

3. **Audit completeness** — for each of login-success / login-failed / token-refreshed / logout / password-changed / user-locked, assert exactly one matching audit_log row with correct `action`, `entity_type="User"`, `entity_id`, `clinic_id`, `user_id`, `ip_address`.
4. **Rate limit lockout interaction** — verify that the rate limit (10/min) does NOT block legitimate retries from a different IP and that 429 carries the structured body shape with `Retry-After` header.
5. **change-password revokes nothing today** — explicitly assert current behaviour (existing refresh tokens still work after password change). This documents the MINOR finding so future work can close it intentionally.
6. **Case-insensitive username**: lockout key uses `username.lower()` but the user lookup in `_get_user` uses `User.username == username` (case-sensitive). Test what happens with `Admin` vs `admin` — confirm lockout aggregates correctly even if DB lookup is case-sensitive.
7. **Coverage instrumentation** (optional): if you have the bandwidth, wire `pytest --cov=app/modules/auth --cov=app/core/security --cov=app/core/token_blacklist --cov-report=term-missing` and confirm ≥ 90% on `auth_service.py` per AC.

## Files of Interest

- `app/modules/auth/services/auth_service.py` — primary service under test
- `app/modules/auth/services/lockout_service.py` — Redis counter logic
- `app/core/security.py` — JWT + bcrypt
- `app/core/token_blacklist.py` — Redis revocation
- `tests/integration/test_auth_*.py` — existing integration tests (mocked DB)

## Out of Scope for Test Phase

- Switching slowapi to Redis-backed storage (production deploy task)
- Password-change refresh revocation (product decision pending)
- RS256 / JWKS migration (already deferred to a future task per tenancy.py:9)
