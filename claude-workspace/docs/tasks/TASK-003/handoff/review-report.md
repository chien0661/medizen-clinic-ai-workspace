# Code Review: TASK-003 — Auth (JWT Login/Refresh + Lockout)

**Reviewer:** Code Review Agent
**Date:** 2026-04-27
**Branch:** `feature/task-003-auth`
**Status:** APPROVED

## Review Summary

- **Files Reviewed:** 23 (10 new src, 4 modified, 6 new test, +1 migration, +1 pyproject)
- **Lines:** +1814 / -5
- **Tests:** 186 / 186 passed (`docker compose exec api pytest -q`) — 38 new
- **Lint (TASK-003 files only):** ruff `All checks passed`
- **Issues Found:** 7
  - Critical: 0
  - Major: 2
  - Minor: 5
- **Code Quality:** Good

## Critical Findings

None. Top three security focus areas were verified in detail:

1. **`SET LOCAL` f-string in `app/core/db.py`** — NOT injectable. Trace path: `current_clinic_id` is `ContextVar[UUID | None]` (declared at `db.py:23`); the only writer is `app/core/tenancy.py:202` which assigns the result of `UUID(x_clinic)` (line 157) or `UUID(str(raw_clinic))` (line 188). Both raise `ValueError` on malformed input and return 401 before reaching `get_db`. The f-string therefore only ever interpolates `UUID.__str__()` output (lowercase hex + dashes). Safe.
2. **JWT decode** (`security.py:113`) — explicitly passes `algorithms=[settings.JWT_ALGORITHM]`, blocking the classic `alg=none` python-jose pitfall. Signature/exp verified by jose. Test `test_decode_raises_on_wrong_signature` and `test_decode_raises_on_expired_token` confirm.
3. **Refresh rotation atomicity** (`auth_service.py:230-236`) — old `jti` is added to Redis blacklist BEFORE new tokens are minted. If process crashes between revoke and issue, old token is already blacklisted → no replay window. Correct ordering.

## Issues Found

### Issue 1: Lockout end-to-end behaviour is not actually exercised by tests
**File:** `tests/integration/test_auth_login.py:88-97`
**Severity:** Major
**Description:** `test_locked_user_returns_423` mocks `auth_service.login` to raise `ValueError("locked_user")` and asserts 423. It does NOT exercise the lockout-trigger path — i.e. submitting 5 wrong passwords against a real user and verifying that `is_locked` flips to True and the 6th request returns 423. AC explicitly requires "Login sai 5 lần → account locked, return 423 Locked".

**Suggestion:** Test Agent must add a service-layer integration test using the real DB + Redis fixtures: hit `auth_service.login(...)` 5× with wrong password and assert `user.is_locked is True` after the 5th call, plus 423 on the 6th call via HTTP.

**Rationale:** The implementation in `lockout_service.py:_lock_user` looks correct, but no test currently proves the wiring is intact. This is the most security-critical AC and must be verified end-to-end.

---

### Issue 2: Refresh-rotation blacklisting is not verified end-to-end
**File:** `tests/integration/test_auth_refresh.py`
**Severity:** Major
**Description:** No test confirms that, after a *successful* refresh, the old jti is actually present in the Redis blacklist (or that calling `/refresh` again with the same token then returns 401). `test_subsequent_refresh_with_revoked_token_fails` in `test_auth_logout.py` covers logout→refresh, but the rotation path itself is untested.

**Suggestion:** Add a test that:
  1. Calls `auth_service.refresh(token1)` against real Redis, captures `token2`.
  2. Calls `auth_service.refresh(token1)` again — must raise `revoked_token`.
  3. Optionally asserts `await is_revoked(jti1) is True`.

**Rationale:** Refresh rotation is a core security guarantee; without a test, a regression that drops the `revoke_token(jti, exp_dt)` line would silently ship.

---

### Issue 3: Rate limiter is in-process — does not work multi-worker
**File:** `app/core/rate_limit.py:28`
**Severity:** Minor (documented production gap, acceptable for v1)
**Description:** `Limiter(key_func=get_remote_address)` defaults to in-memory storage. With N uvicorn workers the effective allowance becomes 10×N per minute per IP. Per the implementation handoff this is an acknowledged v1 trade-off.

**Suggestion:** Document the production fix in the README or in `docs/operations/`: switch to `Limiter(..., storage_uri=settings.REDIS_URL)` before production deploy. Consider opening a follow-up task TASK-NNN.

**Rationale:** Acceptable for dev/single-worker, but reviewer must flag so it is not silently forgotten.

---

### Issue 4: Username enumeration via timing channel
**File:** `app/modules/auth/services/auth_service.py:104-109`
**Severity:** Minor
**Description:** When `username` does not exist (line 106) the function returns immediately without performing a password verification. When the user *does* exist, a bcrypt verify (cost 12, ~150-300 ms) runs. The wall-clock difference can leak username existence to a network observer.

**Suggestion (defer to follow-up):** Run a dummy bcrypt verify against a constant hash on the "user is None" branch to equalise timing. Lockout already mitigates online enumeration; this is defence-in-depth.

**Rationale:** Lockout caps enumeration to 5 attempts/window so risk is low; flag as MINOR for backlog.

---

### Issue 5: Defensive UUID cast in `get_db()` would harden the SET LOCAL path
**File:** `app/core/db.py:36-42`
**Severity:** Minor
**Description:** Today the f-string is safe only because every writer to `current_clinic_id`/`current_user_id` happens to construct a `UUID` first. If a future code path ever sets `current_clinic_id.set(some_string)` (e.g. from a worker, scheduled job, or test fixture) the protection collapses. Defence in depth.

**Suggestion:**
```python
if clinic_id:
    cid = UUID(str(clinic_id))   # raises if anything non-UUID slipped in
    await session.execute(text(f"SET LOCAL app.current_clinic_id = '{cid}'"))
```

**Rationale:** Cheap, makes the invariant explicit at the point that depends on it. Comment in db.py already notes "clinic_id is a validated UUID" — the assertion should be made local.

---

### Issue 6: `change-password` does not revoke existing refresh tokens
**File:** `app/modules/auth/services/auth_service.py:311-345`
**Severity:** Minor
**Description:** After a user changes their password, all previously issued refresh tokens (e.g. on a stolen device) remain valid until natural expiry (7 days). Common best practice is to revoke them on password change.

**Suggestion (follow-up task):** After `flush`, enumerate active refresh-token jtis for the user (or maintain a `refresh_token_version` claim and bump it; check version in `decode_token`). Out of scope for v1 if not in spec.

**Rationale:** Spec does not explicitly require this, but it is a common security expectation; flag for product to confirm.

---

### Issue 7: Audit on logout silently swallows all exceptions
**File:** `app/modules/auth/services/auth_service.py:302`
**Severity:** Minor (Nit)
**Description:** `except (ValueError, Exception): pass` catches everything. The bare `Exception` makes the `ValueError` redundant and hides programming errors (e.g. AttributeError on a misnamed field) from logs.

**Suggestion:** Replace with `except Exception: log.warning("logout_audit_failed", ...)` so failures are visible.

**Rationale:** "Audit failure must not block logout" is fine; "audit failure must be invisible" is not.

---

## Positive Observations

- bcrypt cost 12 is correct; `verify_password` uses constant-time `bcrypt.checkpw`; salts are random per call (test `test_two_hashes_of_same_password_differ`).
- JWT decode explicitly pins `algorithms=[settings.JWT_ALGORITHM]` — the `alg=none` pitfall is closed.
- Refresh rotation correctly revokes BEFORE issuing new tokens (no replay window).
- TenancyMiddleware whitelist correctly excludes `change-password` (auth required) while allowing self-authenticating endpoints.
- User model declares `__auditable__ = True` and `__audit_exclude__ = {"password_hash"}` — TASK-002 PII redaction will mask the hash in audit rows.
- Migration 0005: partial unique indexes per-clinic (correct for soft-deleted rows), RLS applied via `apply_rls_with_tenant_isolation`, cms_app grants present.
- Endpoint shapes match §2.4 design (`{"data": ...}` / `{"error": ..., "meta": ...}`).
- Status codes correct: 401 (auth), 423 (locked), 429 (rate limit), 422 (validation).
- Lockout key includes `clinic_id` and lower-cases username for case-insensitivity.
- Settings expose `JWT_SECRET` with `min_length=8`; default is `"change-me-in-production"` — should be rotated in deployment, not a code issue.

## Code Quality Metrics

- **Lint (TASK-003 files):** Pass
- **Maintainability:** Good — modular split (api/services/schemas), small functions, clear docstrings
- **Complexity:** Low — auth_service functions ≤ 50 LoC each, no deep nesting
- **Duplications:** None found
- **Test Coverage:** Not measured (coverage tool not wired in docker pytest config). 186/186 tests pass; 38 new for TASK-003. **Coverage measurement is a TASK-001 carryover deferral** — should be opened as a follow-up infra task, NOT a TASK-003 blocker.

## Decision

**APPROVED**

No critical security issues. The two MAJOR findings (#1, #2) are *test gaps* not implementation gaps — the underlying lockout/rotation logic is correct and well-structured. They should be closed by the Test Agent in IN_TESTING phase, and I am explicitly flagging them in the test-handoff focus areas. Minor issues are either documented production gaps (rate limit), defence-in-depth recommendations, or stylistic.

## Next Steps

1. Hand off to Test Agent (status → IN_TESTING).
2. Test Agent MUST add: (a) end-to-end lockout test (5 fails → 423 on 6th, real DB+Redis), (b) refresh-rotation test that verifies old jti is blacklisted after successful rotate.
3. Open a follow-up task for: Redis-backed rate limiter, coverage instrumentation, password-change refresh-token revocation, login timing equalisation.

---

**Review Time:** ~25 minutes
**Recommendations:** Wire `pytest --cov` in the docker test target before next sprint so coverage gates can actually be enforced (PROJECT.md threshold: 80% new code).
