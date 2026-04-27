# Test Catalog — TASK-003: Auth Module

**Generated:** 2026-04-27
**Total Tests:** 188 (186 pre-existing + 2 new TASK-003 iter 2)
**Status:** 187 PASS / 1 FAIL (BUG-001)

---

## New Tests Added (TASK-003 Iteration 2)

### MAJOR-1: End-to-End Account Lockout — Real DB + Redis

**File:** `tests/integration/test_auth_lockout_real_db.py`
**Status:** FAIL (BUG-001)

| # | Test Name | Type | Status | Notes |
|---|-----------|------|--------|-------|
| 1 | `TestLockoutFlowRealDB::test_lockout_end_to_end` | Integration E2E | FAIL | BUG-001: is_locked=True rolled back with failed-login tx |

**What is tested (partially passing):**
- Creates real Clinic + User in DB
- Sends 5 wrong-password login attempts — each returns 401 ✓
- Verifies Redis lockout key exists with correct count and TTL ✓
- Asserts `User.is_locked=True` in DB — FAILS (BUG-001)
- Asserts 6th attempt returns 423 — FAILS (BUG-001)
- Asserts `audit_log` has `user.locked` entry — FAILS (BUG-001)

---

### MAJOR-2: Refresh Token Rotation Blacklist — Real Redis

**File:** `tests/integration/test_auth_refresh_rotation_real_redis.py`
**Status:** PASS

| # | Test Name | Type | Status | Notes |
|---|-----------|------|--------|-------|
| 2 | `TestRefreshRotationBlacklist::test_refresh_rotation_blacklists_old_jti` | Integration E2E | PASS | Full chain A→B→C verified |

**What is tested:**
- Creates real Clinic + User in DB ✓
- Login → refresh_token_A (jti_A) ✓
- /auth/refresh with A → refresh_token_B (jti_B) ✓
- Redis key `revoked:{jti_A}` exists with positive TTL ✓
- jti_B ≠ jti_A, token_B type = 'refresh' ✓
- Reuse of token_A → 401 ✓
- /auth/refresh with B → 200 (issues C) ✓
- Redis key `revoked:{jti_B}` exists with positive TTL ✓
- Reuse of token_B → 401 ✓

---

## Pre-existing TASK-003 Tests (38 tests from iteration 1)

### Login Endpoint Tests (`tests/integration/test_auth_login.py`)

| # | Test Name | Status |
|---|-----------|--------|
| 3 | `TestLoginEndpoint::test_successful_login_returns_200` | PASS |
| 4 | `TestLoginEndpoint::test_wrong_credentials_returns_401` | PASS |
| 5 | `TestLoginEndpoint::test_inactive_user_returns_401` | PASS |
| 6 | `TestLoginEndpoint::test_locked_user_returns_423` (mocked) | PASS |
| 7 | `TestLoginEndpoint::test_missing_fields_returns_422` | PASS |

### Refresh Endpoint Tests (`tests/integration/test_auth_refresh.py`)

| # | Test Name | Status |
|---|-----------|--------|
| 8 | `TestRefreshEndpoint::test_valid_refresh_returns_200` | PASS |
| 9 | `TestRefreshEndpoint::test_revoked_token_returns_401` | PASS |
| 10 | `TestRefreshEndpoint::test_invalid_token_returns_401` | PASS |
| 11 | `TestRefreshEndpoint::test_expired_jwt_returns_401` | PASS |
| 12 | `TestRefreshEndpoint::test_access_token_as_refresh_returns_401` | PASS |
| 13 | `TestRefreshEndpoint::test_garbage_string_returns_401` | PASS |

### Logout Endpoint Tests (`tests/integration/test_auth_logout.py`)

| # | Test Name | Status |
|---|-----------|--------|
| 14 | `TestLogoutEndpoint::test_valid_token_logout_returns_204` | PASS |
| 15 | `TestLogoutEndpoint::test_revoke_called_with_correct_jti` | PASS |
| 16 | `TestLogoutEndpoint::test_malformed_token_logout_returns_204` | PASS |
| 17 | `TestLogoutEndpoint::test_expired_token_logout_returns_204` | PASS |
| 18 | `TestLogoutEndpoint::test_subsequent_refresh_with_revoked_token_fails` | PASS |

### Change Password Tests (`tests/integration/test_change_password.py`)

| # | Test Name | Status |
|---|-----------|--------|
| 19 | `TestChangePasswordEndpoint::test_no_auth_returns_401` | PASS |
| 20 | `TestChangePasswordEndpoint::test_wrong_old_password_returns_401` | PASS |
| 21 | `TestChangePasswordEndpoint::test_correct_old_password_returns_204` | PASS |
| 22 | `TestChangePasswordEndpoint::test_missing_new_password_returns_422` | PASS |

### JWT Signature Tests (`tests/integration/test_jwt_signature.py`)

_(Multiple tests covering decode, alg=none rejection, expiry validation, signature tampering)_

### Rate Limit Tests (`tests/integration/test_auth_rate_limit.py`)

| # | Test Name | Status |
|---|-----------|--------|
| X | `TestRateLimit::test_eleventh_request_returns_429` | PASS |

---

## Coverage Summary

| File | Lines | Coverage | Target | Status |
|------|-------|----------|--------|--------|
| `auth_service.py` | 118 | 53% | >90% | FAIL |
| `lockout_service.py` | 42 | 83% | >80% | PASS |
| `routes.py` | 52 | 94% | >80% | PASS |
| `auth_schemas.py` | 27 | 100% | >80% | PASS |
| `security.py` | 32 | 94% | >80% | PASS |
| `token_blacklist.py` | 17 | 94% | >80% | PASS |
| **TOTAL** | **288** | **76%** | >80% | FAIL |

---

## Acceptance Criteria Status

| AC | Description | Status |
|----|-------------|--------|
| AC-1 | Login đúng → access + refresh, last_login_at, reset failed_count | PARTIAL (mocked test passes; real-DB path untested due to coverage gap) |
| AC-2 | Login sai 5 lần → account locked, return 423 Locked | FAIL (BUG-001) |
| AC-3 | Refresh token hợp lệ → token cũ vào blacklist | PASS (MAJOR-2 real-Redis test) |
| AC-4 | Logout → refresh token vào blacklist | PASS (mocked + real tests) |
| AC-5 | Tất cả endpoint có audit log | PARTIAL (audit write verified by code inspection; full per-endpoint verification not in current tests) |
| AC-6 | Coverage > 90% cho auth_service.py | FAIL (53%) |
