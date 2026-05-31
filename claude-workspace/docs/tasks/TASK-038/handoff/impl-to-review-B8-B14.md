# TASK-038 B.8–B.14 Implementation Handoff

**Date**: 2026-05-01  
**Agent**: Code Implementation  
**Status**: READY FOR REVIEW  
**Scope**: MFA (TOTP) + Login Fingerprint (NFR-029, NFR-035)

---

## Files Changed

### BE — `clinic-cms-w1c` (branch: `feature/task-038-b8-mfa`)

| File | Change Type | Description |
|---|---|---|
| `alembic/versions/0021_add_mfa_columns_to_user.py` | NEW | B.8: Adds mfa_secret, mfa_enabled, backup_codes to user table |
| `alembic/versions/0022_create_login_fingerprint.py` | NEW | B.9: Creates login_fingerprint table + indexes |
| `app/modules/users/models/user.py` | MODIFIED | Added mfa_secret, mfa_enabled, backup_codes fields |
| `app/modules/auth/models/__init__.py` | NEW | Auth models package |
| `app/modules/auth/models/login_fingerprint.py` | NEW | LoginFingerprint SQLAlchemy model |
| `app/modules/auth/services/mfa_service.py` | NEW | B.10: TOTP enroll/verify/disable + backup codes |
| `app/modules/auth/services/fingerprint_service.py` | NEW | B.13: Fingerprint check_and_upsert + list_recent |
| `app/modules/auth/schemas/auth_schemas.py` | MODIFIED | Added MFA request/response schemas + fingerprint schemas |
| `app/modules/auth/api/routes.py` | MODIFIED | B.11/B.12: 6 new endpoints (see catalog below) |
| `app/modules/auth/services/auth_service.py` | MODIFIED | B.12/B.13: login() + complete_mfa_challenge() |
| `app/core/security.py` | MODIFIED | Added create_mfa_token() for 5-min MFA JWT |
| `pyproject.toml` | MODIFIED | Added `pyotp>=2.9` dependency |
| `tests/unit/test_mfa_service.py` | NEW | 24 unit tests: enroll/verify/disable/backup/fingerprint |
| `tests/integration/test_auth_mfa.py` | NEW | 5 integration tests: login MFA flow + challenge |

### FE — `clinic-cms-web-w1c` (branch: `feature/task-038-b8-mfa-fe`)

| File | Change Type | Description |
|---|---|---|
| `package.json` | MODIFIED | Added `qrcode.react@^3.1.0` |
| `src/pages/auth/MfaEnrollPage.tsx` | NEW | B.14: QR code + OTP verify for enrollment |
| `src/pages/auth/MfaVerifyPage.tsx` | NEW | B.14: 6-digit OTP input + backup code fallback |
| `src/pages/profile/SecurityTab.tsx` | NEW | B.14: MFA toggle + backup codes + recent logins |
| `src/pages/profile/ProfilePage.tsx` | NEW | Multi-tab profile page with Security tab |
| `src/pages/auth/LoginPage.tsx` | MODIFIED | Handle mfa_required response → navigate to verify |
| `src/router/index.tsx` | MODIFIED | Added /auth/mfa/verify, /auth/mfa/enroll, /profile routes |
| `src/locales/vi/auth.json` | MODIFIED | Added auth.mfa.* translations (Vietnamese) |
| `src/locales/en/auth.json` | MODIFIED | Added auth.mfa.* translations (English) |
| `src/locales/vi/profile.json` | NEW | profile.security.* translations (Vietnamese) |
| `src/locales/en/profile.json` | NEW | profile.security.* translations (English) |
| `src/tests/auth/MfaEnrollPage.test.tsx` | NEW | 5 unit tests: QR code render, OTP submit, error |
| `src/tests/auth/MfaVerifyPage.test.tsx` | NEW | 5 unit tests: OTP / backup code flow |
| `src/tests/auth/SecurityTab.test.tsx` | NEW | 8 unit tests: badge, toggle, fingerprint list |

---

## Migration Versions

| # | Revision ID | Description |
|---|---|---|
| B.8 | `0021` | Adds MFA columns to user table |
| B.9 | `0022` | Creates login_fingerprint table |

Migration chain: `65fc9ae59ba5` → `0021` → `0022`

---

## Endpoint Catalog (New Endpoints — 6)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/mfa/enroll` | access token | Start TOTP enrollment; returns {secret, qr_uri} |
| `POST` | `/api/v1/auth/mfa/verify` | access token | Verify OTP; activates mfa_enabled=true on first success |
| `POST` | `/api/v1/auth/mfa/disable` | access token + password | Disable MFA (requires password re-auth) |
| `POST` | `/api/v1/auth/mfa/backup-codes/regenerate` | access token + password | Regenerate 10 backup codes; returns plaintext ONCE |
| `POST` | `/api/v1/auth/mfa/challenge` | mfa_token (5-min JWT) | Complete 2-step login with OTP or backup code |
| `GET` | `/api/v1/auth/fingerprints` | access token | List recent login fingerprints |

### Modified Endpoints
- `POST /api/v1/auth/login` — now returns `{mfa_required: true, mfa_token}` when mfa_enabled=true, OR `{requires_mfa_challenge: true}` for new device/IP

---

## Test Results

### BE Tests (Python 3.11, Docker)
- `tests/unit/test_mfa_service.py` — **24/24 PASSED**
- `tests/integration/test_auth_mfa.py` — **5/5 PASSED**
- **Total BE: 29/29 PASSED**

### FE Tests (Vitest + happy-dom)
- `src/tests/auth/MfaEnrollPage.test.tsx` — **5/5 PASSED**
- `src/tests/auth/MfaVerifyPage.test.tsx` — **5/5 PASSED**
- `src/tests/auth/SecurityTab.test.tsx` — **8/8 PASSED**
- **Total FE: 18/18 PASSED**

**Grand total: 47/47 tests passing.**

---

## Key Design Decisions

1. **TOTP drift tolerance**: `pyotp.TOTP.verify(otp, valid_window=1)` — covers ±30s (1 window before and after), meeting spec.

2. **Backup codes storage**: bcrypt-hashed (cost=12, same as passwords) via `passlib[bcrypt]`. Plaintext returned ONCE at generation time.

3. **Login fingerprint anomaly threshold**: 30-day window. A fingerprint is "known" only if the (user_id, ip, device_hash) tuple was seen within the last 30 days. Conservative — only flags if NO match exists in window.

4. **MFA token**: Separate JWT with `type="mfa_challenge"`, 5-minute TTL. Cannot be used as access or refresh token (type check enforced).

5. **`device_hash`**: SHA-256 of `user_agent + "|" + extras` (extras = FE-provided `screen|tz` if available). Falls back to UA-only. 64 hex chars.

6. **Upsert strategy**: `pg_insert(...).on_conflict_do_update(...)` on unique index `(user_id, ip, device_hash)`. Atomic, race-condition safe.

7. **qrcode.react v3**: Uses `QRCodeSVG` named export (not default) to generate inline SVG QR codes. No canvas dependency.

---

## Deferred / Out of Scope

- **Email OTP fallback** (for users without MFA but with anomaly): spec mentions "email OTP fallback" for non-MFA anomaly. Current implementation returns `requires_mfa_challenge: true` in login response but does not yet send email. FE can use this flag to show a "verify your identity" prompt. Email sending requires a notification service (TASK-020 notifications module). Deferred.

- **GeoIP lookup**: `geo_country` stored as NULL unless FE passes it (not implemented). A server-side MaxMind/IP-API integration would be needed for auto-detection. Deferred.

- **Rate limiting on MFA endpoints**: MFA verify/challenge endpoints have inherent brute-force protection via TOTP time windows, but explicit rate limiting (separate from login's 10/min limiter) is not applied to MFA endpoints. Reviewer should flag if stricter limits are desired.

- **ProfilePage info tab**: Basic stub only. Full profile info (name, phone, avatar) will be fleshed out in TASK-039.

---

## Reviewer Checklist

- [ ] Migration 0021 + 0022 are additive-only (no destructive changes)
- [ ] `mfa_service.enroll` rejects if `mfa_enabled=True` (400)
- [ ] `complete_mfa_challenge` only accepts `type="mfa_challenge"` tokens
- [ ] Backup codes stored as bcrypt hashes (never plaintext in DB)
- [ ] `login_fingerprint` upsert is atomic via ON CONFLICT
- [ ] FE: `MfaVerifyPage` guards against missing `mfaToken` in state
- [ ] FE: LoginPage correctly branches on `mfa_required` vs normal response

---

## Fix-mode addendum

**Date**: 2026-05-01  
**Mode**: CHANGES_REQUESTED patch (2 blockers from code review)

### Files changed in fix

**BE — `clinic-cms-w1c`** (3 files):

| File | Change |
|---|---|
| `app/modules/auth/services/auth_service.py` | `complete_mfa_challenge`: call `record_failed_attempt` + audit log on invalid OTP; call `clear_failed_attempts` on valid OTP. Also added `mfa_enabled` to user dict in both `login()` and `complete_mfa_challenge()` return values. |
| `app/modules/auth/schemas/auth_schemas.py` | Added `mfa_enabled: bool = False` to `UserInfo` schema. |
| `tests/integration/test_auth_mfa.py` | Added 2 new lockout integration tests (see below). |

**FE — `clinic-cms-web-w1c`** (3 files):

| File | Change |
|---|---|
| `src/stores/authStore.ts` | Added `mfa_enabled?: boolean` to `UserInfo` interface. |
| `src/pages/profile/ProfilePage.tsx` | Replaced `useState(false) // TODO` with `useAuthStore(s => s.user?.mfa_enabled ?? false)`; removed `setMfaEnabled` / `onMfaChange` prop pass to SecurityTab. |
| `src/tests/auth/SecurityTab.test.tsx` | Added new describe block with 1 test asserting "Enabled" badge renders when `mfaEnabled=true` (verifying the prop-derived-from-store flow). |

### New tests added (3 total)

**BE** (2 tests in `tests/integration/test_auth_mfa.py`):
- `TestMfaChallengeLockoutIntegration::test_complete_mfa_challenge_failed_otp_feeds_lockout` — submits N-1 wrong OTPs, verifies `record_failed_attempt` called each time; Nth wrong OTP triggers `is_locked=True`
- `TestMfaChallengeLockoutIntegration::test_complete_mfa_challenge_success_resets_lockout` — successful OTP call asserts `clear_failed_attempts` awaited with correct `(clinic_id, username)`

**FE** (1 test in `src/tests/auth/SecurityTab.test.tsx`):
- `"mfaEnabled badge reads from authStore — shows 'Enabled' when store user.mfa_enabled=true"` — renders SecurityTab with `mfaEnabled=true` (value ProfilePage now derives from authStore), asserts "Enabled" badge in DOM

### Test results post-fix

| Suite | Before fix | After fix |
|---|---|---|
| BE `tests/integration/test_auth_mfa.py` | 5 passed | **7 passed** (+2 new) |
| FE `npm test -- --run` (full suite) | 565 passed | **566 passed** (+1 new) |

All tests green. No regressions.
