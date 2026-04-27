# Test Report: TASK-003 - Auth (JWT Login/Refresh + Lockout)

**Test Agent:** Test Agent (automated)
**Date:** 2026-04-27
**Status:** FAIL — 1 CRITICAL BUG FOUND

---

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| API Contract (mocked) | 18 | 18 | 0 | 100% |
| Integration — real Redis | 1 | 1 | 0 | 100% |
| Integration — real DB+Redis | 1 | 0 | 1 | 0% |
| Unit (security) | 20+ | 20+ | 0 | 100% |
| **TOTAL (new tests)** | **2** | **1** | **1** | **50%** |
| **TOTAL (all 188)** | **188** | **187** | **1** | **99.47%** |

---

## Acceptance Criteria Status

| AC | Description | Status | Notes |
|----|-------------|--------|-------|
| AC-1 | Login đúng → access + refresh, last_login_at, reset failed_count | PARTIAL | Mocked HTTP test passes; real-DB coverage only 53% |
| AC-2 | Login sai 5 lần → account locked, return 423 Locked | FAIL | BUG-001: is_locked never persists (rolled back with tx) |
| AC-3 | Refresh token hợp lệ → token cũ vào blacklist | PASS | MAJOR-2 real-Redis test proves end-to-end |
| AC-4 | Logout → refresh token vào blacklist | PASS | Existing + real-Redis chain tests |
| AC-5 | Tất cả endpoint có audit log | PARTIAL | Code inspection confirms write_audit calls; per-endpoint test not yet written |
| AC-6 | Coverage > 90% cho auth_service.py | FAIL | 53% actual (full suite with cov measurement) |

---

## Business Rules Validated (BA §22)

- FAIL BR-LOCKOUT: 5 failed logins → `is_locked=True` in DB + 423 on 6th attempt — NOT verified (BUG-001)
- PASS BR-REFRESH: Refresh rotation revokes old jti in Redis before issuing new — VERIFIED real Redis
- PASS BR-LOGOUT: Logout revokes refresh token jti — VERIFIED
- PASS BR-JWT: JWT decode pins algorithm (alg=none rejected) — VERIFIED unit test
- PASS BR-BCRYPT: bcrypt cost 12, constant-time verify — VERIFIED unit test

---

## Coverage Report

Measured with: `pytest --cov=app.modules.auth --cov=app.core.security --cov=app.core.token_blacklist --cov-report=term-missing`

| File | Stmts | Miss | Coverage | Target | Status |
|------|-------|------|----------|--------|--------|
| `app/modules/auth/api/routes.py` | 52 | 3 | **94%** | >80% | PASS |
| `app/modules/auth/schemas/auth_schemas.py` | 27 | 0 | **100%** | >80% | PASS |
| `app/modules/auth/services/auth_service.py` | 118 | 55 | **53%** | >90% | FAIL |
| `app/modules/auth/services/lockout_service.py` | 42 | 7 | **83%** | >80% | PASS |
| `app/core/security.py` | 32 | 2 | **94%** | >80% | PASS |
| `app/core/token_blacklist.py` | 17 | 1 | **94%** | >80% | PASS |
| **TOTAL** | **288** | **68** | **76%** | >80% | FAIL |

**auth_service.py uncovered lines:** 58, 69, 97-124, 133-141, 156-158, 204, 214-215, 220-232, 247, 286, 302-303, 325-345
(Login success path, refresh path, logout path, change-password path — all mocked at HTTP layer)

---

## Failures

### Failure 1 — BUG-001: Account Lockout DB Update Rolled Back

**Test:** `tests/integration/test_auth_lockout_real_db.py::TestLockoutFlowRealDB::test_lockout_end_to_end`
**Type:** Integration
**Severity:** Critical
**SRS Reference:** BA §22 (account lockout)

**Expected:**
- After 5 wrong-password attempts: `User.is_locked=True` in DB, 6th attempt → 423.

**Actual:**
- `User.is_locked` remains `False` in DB (update rolled back).
- 6th attempt → 401 (not 423).
- `audit_log` `user.locked` row also rolled back.
- Redis counter increments correctly (counter logic works).

**Root Cause:**
`_lock_user()` in `lockout_service.py` executes within the same SQLAlchemy session as the failing `login()` call. When `login()` raises `ValueError`, `get_db` issues `ROLLBACK`, undoing the `is_locked=True` update.

**Error:**
```
AssertionError: BUG-001: Expected is_locked=True after lockout threshold reached.
_lock_user() DB update is rolled back with the failed-login transaction.
assert False is True
 +  where False = <User...>.is_locked
```

**Bug Report:** `docs/tasks/TASK-003/bugs/BUG-001.md`

---

## Test Files Created (TASK-003 Iteration 2)

| File | Type | Tests | Status |
|------|------|-------|--------|
| `tests/integration/test_auth_lockout_real_db.py` | Integration E2E (real DB+Redis) | 1 | FAIL (BUG-001) |
| `tests/integration/test_auth_refresh_rotation_real_redis.py` | Integration E2E (real Redis) | 1 | PASS |

## Infrastructure Changes

| File | Change | Rationale |
|------|--------|-----------|
| `pyproject.toml` | Added `asyncio_default_test_loop_scope = "session"` | Fix asyncpg connection-cancel RuntimeError when multiple real-DB tests run in same session with function-scoped loops |

---

## What Passes

- **MAJOR-2 (refresh rotation):** Full real-Redis chain: login → refresh(A→B) → assert jti_A in Redis blacklist with TTL → reuse A returns 401 → refresh(B→C) → assert jti_B in Redis blacklist → reuse B returns 401.
- **186 pre-existing tests:** All pass (100%).
- JWT `alg=none` rejection verified.
- bcrypt constant-time verify verified.
- Rate limit (10/min) verified.
- Logout jti revocation verified (real Redis in chain test).

---

## Next Steps

1 critical bug requires implementation fix before DOCUMENTING:
- **BUG-001**: Fix `_lock_user()` to use autonomous transaction (separate session/commit) so the `is_locked=True` update survives the failed-login transaction rollback.
- After fix: `test_lockout_end_to_end` should pass, closing MAJOR-1.
- Also improve `auth_service.py` coverage to >90% (add direct service-layer tests).

**Task status → IN_PROGRESS**
**Assigned → Code Implementation Agent**
**Handoff:** `docs/tasks/TASK-003/handoff/test-to-implementation.md`

---

**Test Execution Time:** ~15 seconds (full suite with coverage)
**Total Tests:** 188
**Environment:** Docker (clinic_cms_api container), PostgreSQL + Redis
