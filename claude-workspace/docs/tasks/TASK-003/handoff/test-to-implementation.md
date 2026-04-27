# Handoff: TASK-003 → Code Implementation Agent

**From:** Test Agent
**To:** Code Implementation Agent
**Status:** IN_PROGRESS
**Date:** 2026-04-27

---

## Summary

Tests FAILED (187 pass / 188 total — 1 new test fails with a Critical implementation bug).

MAJOR-2 (refresh rotation blacklist) — PASS (1 test, real Redis, full chain verified).
MAJOR-1 (lockout end-to-end real DB) — FAIL (BUG-001 — Critical security defect).

---

## What Passed

- **186 pre-existing tests**: all pass (100%).
- **MAJOR-2** `test_auth_refresh_rotation_real_redis.py::TestRefreshRotationBlacklist::test_refresh_rotation_blacklists_old_jti` — PASS.
  - Full chain: login → refresh → assert old jti in Redis blacklist → reuse returns 401 → chain B→C → B revoked.

## What Failed

### MAJOR-1 — BUG-001 (Critical)

**Test:** `tests/integration/test_auth_lockout_real_db.py::TestLockoutFlowRealDB::test_lockout_end_to_end`

**Bug report:** `docs/tasks/TASK-003/bugs/BUG-001.md`

**Root cause (CRITICAL):** `_lock_user()` in `lockout_service.py` sets `User.is_locked=True` within the same SQLAlchemy session/transaction as the failed `login()` call. When `login()` raises `ValueError("invalid_credentials")`, FastAPI's `get_db` dependency catches it and calls `session.rollback()` — undoing **both** the `failed_login_count` update AND the `is_locked=True` update AND the `user.locked` audit row.

The Redis counter (`lockout:{clinic_id}:{username}`) correctly increments, but the DB `is_locked` flag never persists.

**Result:**
- `User.is_locked` remains `False` after 5 failed attempts.
- 6th attempt returns HTTP `401` (not `423 Locked`).
- `audit_log` row for `user.locked` is also rolled back.
- Acceptance criterion "Login sai 5 lần → account locked, return 423 Locked" **NOT MET**.

**Recommended fix:** In `_lock_user()`, open an **autonomous transaction** (new independent session from the SQLAlchemy engine) for the `is_locked=True` update and audit write, commit it before returning. The calling `login()` transaction may still rollback — but the lock update is already committed.

See `bugs/BUG-001.md` for detailed fix options.

---

## Coverage Gap (Additional Finding)

`auth_service.py` coverage: **53%** (required: **>90%**).

The existing test suite mocks the service layer for HTTP-layer tests, leaving most of `auth_service.py` uncovered. After BUG-001 is fixed, the implementation agent should ensure coverage is addressed — either via new service-layer tests (without HTTP mocking) or by converting mocked tests to real-DB tests.

Coverage by file (current state):

| File | Coverage | Target |
|------|----------|--------|
| `auth_service.py` | 53% | >90% |
| `lockout_service.py` | 83% | >80% |
| `routes.py` | 94% | >80% |
| `auth_schemas.py` | 100% | >80% |
| `security.py` | 94% | >80% |
| `token_blacklist.py` | 94% | >80% |

---

## Test Infrastructure Fix (already in place)

The test agent added `asyncio_default_test_loop_scope = "session"` to `pyproject.toml` to fix pytest-asyncio event loop scope mismatch (function-scoped test loops + session-scoped fixture loops caused `asyncpg` connection-cancel `RuntimeError` when running multiple real-DB tests in sequence). This change is safe — all 186 pre-existing tests still pass with session-scoped test loops.

---

## Files Changed by Test Agent

**New test files (DO NOT DELETE — used to verify bug fix):**
- `tests/integration/test_auth_lockout_real_db.py` — MAJOR-1 lockout flow (currently FAILS — will PASS after fix)
- `tests/integration/test_auth_refresh_rotation_real_redis.py` — MAJOR-2 rotation blacklist (PASSES)

**Config change:**
- `pyproject.toml` — added `asyncio_default_test_loop_scope = "session"` under `[tool.pytest.ini_options]`

---

## Next Steps for Code Implementation Agent

1. Fix `_lock_user()` in `app/modules/auth/services/lockout_service.py` using an autonomous transaction (see BUG-001.md Option A).
2. Verify `test_lockout_end_to_end` passes after the fix.
3. If possible, add direct service-layer tests for `auth_service.py` to reach >90% coverage.
4. Set status back to `IN_TESTING` when fix is ready.
