# TASK-038 B.8–B.14 Code Review Report

**Date**: 2026-05-01
**Reviewer**: Code Review agent
**Scope**: MFA (TOTP) + Login Fingerprint (NFR-029, NFR-035)
**Decision**: **CHANGES_REQUESTED** (non-blocking for test phase, but must address before merge)

---

## A. Migration Safety

| Item | Status | Notes |
|---|---|---|
| `0021_add_mfa_columns_to_user.py` additive only | ✅ | All three columns nullable or with safe default; downgrade drops them cleanly |
| `mfa_secret VARCHAR(255) NULL` | ✅ | Nullable, no default — correct |
| `mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE` | ✅ | `server_default="FALSE"` ensures backfill on existing rows |
| `backup_codes TEXT[] NULL` | ✅ | `sa.ARRAY(sa.Text())` — nullable |
| `0022_create_login_fingerprint.py` schema | ✅ | UUID PK + `gen_random_uuid()`, FK→user with CASCADE, `ip VARCHAR(45)` (IPv6-safe), `device_hash VARCHAR(64)`, `geo_country VARCHAR(2)` nullable, `last_seen_at TIMESTAMPTZ`, `seen_count INT DEFAULT 1` |
| Unique index `(user_id, ip, device_hash)` | ✅ | Required for `ON CONFLICT` upsert |
| Secondary index `(user_id, last_seen_at)` | ✅ | Speeds up the 30-day window check + recent-logins list |
| Down-revision chain | ✅ | `65fc9ae59ba5 → 0021 → 0022` matches the existing single-head merge node |
| **MIGRATION CONFLICT — three concurrent `0021` revisions** | ❌ **CRITICAL** | Stream A (`0021_multi_clinic_account`), Stream B (`0021_password_history`), Stream C (this branch's `0021_add_mfa_columns_to_user`) all claim revision id `"0021"` AND down-revision `65fc9ae59ba5`. Alembic will refuse to upgrade once two of them coexist. **Action required at merge time:** renumber two of the three to e.g. `0021a / 0021b / 0021c` or chain them linearly (`0021 → 0022 → 0023 → 0024`). This branch's `0022` would also need to slide to `0024` or similar. **Do not merge until coordinated with TASK-038 stream lead.** |

---

## B. TOTP Security Correctness

| Item | Status | Notes |
|---|---|---|
| Secret entropy | ✅ | `pyotp.random_base32()` returns 32 base32 chars = 160 bits — meets RFC 6238 minimum |
| `provisioning_uri()` issuer + label | ✅ | Issuer = `"MediZen"`, account = `user.username`. Renders `otpauth://totp/MediZen:<username>?secret=...&issuer=MediZen` |
| `valid_window=1` in `pyotp.TOTP.verify` | ✅ | Covers ±30s drift (one period before, one after) |
| Time-constant compare | ✅ | `pyotp` uses `hmac.compare_digest` internally — no timing leak |
| `mfa_enabled=True` set on first successful verify only | ✅ | Guarded by `activate=True and not user.mfa_enabled` |
| **TOTP secret stored plaintext in `mfa_secret VARCHAR(255)`** | ⚠️ | Acknowledged in handoff — column-level encryption is TASK-037 scope. Acceptable for now; document as known gap in security delivery. **Recommendation:** add a TODO in the model + a follow-up ticket reference so it's not lost. |
| Backup codes — count = 10 | ✅ | `_BACKUP_CODE_COUNT = 10` |
| Backup codes — entropy | ⚠️ | 10 chars from a 36-char alphabet (uppercase + digits) = log2(36¹⁰) ≈ **51.7 bits**. Below the ≥80-bit checklist target. **Recommend** raising to 12 chars (≈62 bits) or using full base32 alphabet at 16 chars. Not catastrophic — bcrypt-hashed and one-time use mitigate brute-force — but flag for hardening. |
| Backup codes — bcrypt cost-12 hashed | ✅ | `_hash_backup_codes` calls `hash_password` which uses `bcrypt.hashpw(..., gensalt(rounds=12))` — same as user passwords |
| Plaintext returned ONCE on generation | ✅ | `generate_backup_codes` returns `plain_codes`; DB stores `_hash_backup_codes(plain_codes)` only |
| `consume_backup_code` removes used code | ✅ | `remaining.pop(idx)` + `user.backup_codes = remaining or None` |
| **Backup code regeneration overwrites without warning** | ⚠️ | `generate_backup_codes` unconditionally replaces the list. FE warns "newCodesWillInvalidateOld" but server has no audit hint that count went from N→10. Audit event is fine; suggest including `previous_count` in audit metadata for forensics. Minor. |

---

## C. Login Flow Integrity

| Item | Status | Notes |
|---|---|---|
| Two-step flow | ✅ | Step 1 returns `{mfa_required: true, mfa_token}` with NO access/refresh; Step 2 (`/mfa/challenge`) verifies and issues full pair |
| `mfa_token` 5-min TTL | ✅ | `_MFA_TOKEN_EXPIRE_MINUTES = 5` |
| `mfa_token` cannot be exchanged for access | ✅ | `complete_mfa_challenge` rejects if `claims.get("type") != "mfa_challenge"`; route handlers check `type == "access"` / `"refresh"` likewise |
| **`mfa_token` shares JWT_SECRET with access/refresh** | ⚠️ | All three token types signed with `settings.JWT_SECRET`. Type-claim separation prevents cross-use, but a single key compromise nukes everything. Spec checklist asks "different secret?" — **answer: NO, but mitigated by `type` claim guard**. Acceptable trade-off; document in the threat model. |
| `mfa_token` payload contents | ✅ | Contains `sub`, `clinic_id`, `type`, `jti`, `iat`, `exp` — NO permissions/roles. Correct. |
| Failed MFA attempts → lockout? | ❌ | `complete_mfa_challenge` raises `ValueError("invalid_otp")` on bad OTP/backup code but does **NOT** call `record_failed_attempt` or increment `failed_login_count`. This means an attacker who has the password can hammer OTPs at 10/min (the route limiter) without ever triggering account lockout. **Recommendation:** wire `record_failed_attempt` + `clear_failed_attempts` into the MFA challenge path the same way `auth_service.login` does. **Flag as required fix before merge.** |
| Race condition: `last_login_at` already updated before MFA verify | ⚠️ | `auth_service.login` flushes `last_login_at = now()` and resets `failed_login_count = 0` BEFORE returning `mfa_required`. If the user never completes MFA, `last_login_at` reflects a half-completed login. Cosmetic only — recommend deferring `last_login_at` update until after MFA succeeds. |
| Lockout check happens before password verify | ✅ | Pre-existing logic preserved |

---

## D. Fingerprint Anomaly Detection (B.13)

| Item | Status | Notes |
|---|---|---|
| Trigger logic — anomaly when no match in 30 days | ✅ | `cutoff = now - 30d`; query filters `last_seen_at >= cutoff`; `is_anomalous = existing is None` |
| Action on anomaly | ⚠️ | Returns `is_anomalous` → propagated to login response as `requires_mfa_challenge: true` for users WITHOUT MFA. **Issue:** the response field is set but no actual challenge is enforced server-side — a non-MFA user with a new device gets a full token pair AND a flag. FE is expected to honor the flag, but a malicious client can ignore it. The handoff acknowledges this (deferred email OTP). **Acceptable as deferred** but should be called out in the test report and security delivery. |
| Atomic upsert via `ON CONFLICT DO UPDATE` | ✅ | `pg_insert(...).on_conflict_do_update(index_elements=["user_id","ip","device_hash"], set_={...})` — race-safe |
| `seen_count` increment | ✅ | `LoginFingerprint.seen_count + 1` in SET clause |
| IPv6 storage | ✅ | `VARCHAR(45)` fits maximum IPv6 textual form (`xxxx:...:xxxx` + IPv4 mapping) |
| `device_hash` source | ✅ | SHA-256(`user_agent + "|" + extras`) where `extras` is FE-supplied `device_extras` (screen+tz). Falls back to UA-only when extras empty. 64 hex chars. |
| `device_extras` validation | ⚠️ | `LoginRequest.device_extras: str \| None, max_length=256` — fine, but no character whitelist. Hash absorbs any garbage so impact is nil. OK. |
| `geo_country` nullable | ✅ | Confirmed; MaxMind integration deferred as documented |
| **Privacy: IP stored plaintext** | ⚠️ | IP addresses are PII under GDPR/HIPAA. Encryption deferred to TASK-037 — acknowledged. |
| `X-Forwarded-For` parsing | ⚠️ | `_client_ip` takes first comma-separated value but does NOT validate against trusted-proxy list. If the API is exposed without a reverse-proxy header sanitizer, clients can spoof their IP and poison anomaly detection. **Recommend** adding a trusted-proxy CIDR check or rely on `request.client.host` only. Out of B.8-B.14 scope but flag for hardening. |

---

## E. Frontend Flows

| Item | Status | Notes |
|---|---|---|
| `MfaEnrollPage` — QR render via `QRCodeSVG` | ✅ | Inline SVG, no canvas dep; level "M" error correction |
| Copy-secret button + 2s feedback | ✅ | `navigator.clipboard.writeText` with `setCopied(true)` and timeout cleanup on unmount |
| 6-digit numeric OTP input + zod schema | ✅ | `inputMode="numeric"`, `pattern="[0-9]{6}"`, `maxLength=6`, `autoComplete="one-time-code"` |
| Redirect after enroll | ✅ | `navigate("/profile", { state: { tab: "security", mfaEnabled: true } })` — pre-selects Security tab |
| `MfaVerifyPage` — guards missing `mfaToken` | ✅ | Checks `if (!mfaToken)` before submit; shows expired-token error |
| `MfaVerifyPage` — backup code branch | ✅ | `useBackup` toggle, separate form with own zod schema |
| Stores tokens via `secureSet` + `useAuthStore.setTokens` | ✅ | Routes to `/dashboard` on success |
| `SecurityTab` — disable MFA password-gated | ✅ | POST `/mfa/disable` with body password |
| `SecurityTab` — backup codes regenerate one-time display | ✅ | `setBackupCodes(data.codes)` then a "✓ I've saved them" button clears state |
| `SecurityTab` — recent logins list | ✅ | GET `/auth/fingerprints?limit=20` rendered with relative time |
| **`ProfilePage.mfaEnabled` hardcoded `false`** | ❌ | Line 41: `const [mfaEnabled, setMfaEnabled] = useState(false); // TODO: load from user profile API`. The badge always shows "disabled" regardless of actual server state until user clicks enable/disable. **Fix:** wire to user profile / `/auth/me` (assuming endpoint exists). If endpoint doesn't exist yet, derive from a JWT claim or add to `/auth/login` user payload. **Required fix.** |
| LoginPage detects `mfa_required` | ✅ | Lines 161-165: checks `"mfa_required" in rawBody`, navigates to `/auth/mfa/verify` with `state: { mfaToken, clinicCode }` |
| Indigo design tokens (TASK-039) | ✅ | `bg-indigo-100 dark:bg-indigo-900/30`, `text-indigo-600 dark:text-indigo-400` consistently used |
| i18n vi + en for `auth.mfa.*` and `profile.security.*` | ✅ | All four locale files present |

---

## F. Test Quality

| Area | Coverage | Status |
|---|---|---|
| `_generate_raw_backup_codes` length + uniqueness | 2 tests | ✅ |
| `_hash_backup_codes` + `_check_backup_code` | 2 tests | ✅ |
| `mfa_service.enroll` happy + 2 error paths | 3 tests | ✅ |
| `mfa_service.verify` valid + invalid + no-secret | 3 tests | ✅ |
| `mfa_service.generate_backup_codes` | 2 tests | ✅ |
| `mfa_service.consume_backup_code` (valid/invalid/last-code/no-codes) | 4 tests | ✅ |
| `mfa_service.disable` | 2 tests | ✅ |
| Round-trip enroll→verify→generate→consume→disable | 1 test | ✅ |
| `compute_device_hash` deterministic + UA-sensitive + None-safe | 3 tests | ✅ |
| `check_and_upsert` anomaly true/false | 2 tests | ✅ |
| Integration: login no-MFA + new fingerprint → `requires_mfa_challenge` | 1 | ✅ |
| Integration: login with MFA → returns `mfa_token` | 1 | ✅ |
| Integration: challenge with valid OTP → tokens | 1 | ✅ |
| Integration: challenge with wrong OTP → invalid_otp | 1 | ✅ |
| Integration: challenge with backup code → tokens | 1 | ✅ |
| **Missing — replay attack (re-using same OTP twice within window)** | 0 | ⚠️ pyotp's `valid_window=1` allows reuse within 30s. RFC 6238 §5.2 recommends server-side "remember last consumed OTP per user" to prevent replay. Not implemented and not tested. **Flag for hardening backlog.** |
| **Missing — expired `mfa_token` rejection test** | 0 | ⚠️ Code path exists (jose raises on exp), but no explicit test asserts `invalid_token` for an expired-but-otherwise-valid `mfa_token`. Recommend adding. |
| **Missing — wrong-type token rejection** (e.g. passing access token to `/mfa/challenge`) | 0 | ⚠️ Code checks `type == "mfa_challenge"`, no test. Recommend adding. |
| **Missing — failed MFA attempt counting toward lockout** | 0 | ❌ See item C above — feature itself missing. |
| FE — `MfaEnrollPage` 5 tests (render, OTP submit, error, copy, loading) | ✅ | Per handoff |
| FE — `MfaVerifyPage` 5 tests (OTP, backup, expired, branching) | ✅ | Per handoff |
| FE — `SecurityTab` 8 tests (badges, toggle, disable, regenerate, fingerprints) | ✅ | Per handoff |

Total: **47/47 passing** (29 BE + 18 FE). Coverage breadth is good for happy paths and basic negatives; replay/expiry/lockout tests are the gap.

---

## G. Deferred / Out-of-Scope Acknowledgments

| Item | Verdict |
|---|---|
| Email OTP fallback for non-MFA anomaly | ✅ Reasonable defer (depends on TASK-020 notification service) |
| GeoIP / MaxMind country lookup | ✅ Reasonable defer (vendor selection + licensing) |
| Column-level encryption for `mfa_secret` and `ip` | ✅ Tracked under TASK-037 |
| Rate limiter on MFA endpoints separate from `/login` 10/min | ⚠️ Acceptable for now but worth a follow-up — see C lockout item |
| ProfilePage info tab stub | ✅ Reasonable defer to TASK-039 |

---

## Required Fixes Before Merge

1. **(❌ CRITICAL) Migration revision conflict** — coordinate with Stream A/B leads to renumber. This branch's migrations cannot land alongside the other two as-is.
2. **(❌)** Wire failed-MFA-challenge attempts into the lockout counter (`record_failed_attempt` + `failed_login_count`).
3. **(❌)** `ProfilePage.mfaEnabled` must load from server, not be hardcoded `false`.

## Recommended Hardening (non-blocking)

4. Raise backup-code entropy to ≥80 bits (12 chars min, or 16 hex).
5. Add server-side OTP replay protection (remember last-consumed OTP step per user).
6. Defer `last_login_at` update until after MFA challenge succeeds.
7. Add tests for: expired `mfa_token`, wrong-type token, OTP replay.
8. Add trusted-proxy validation for `X-Forwarded-For`.

---

## Summary

Implementation is solid in shape: TOTP correctness is good, bcrypt-hashed backup codes are correct, atomic fingerprint upsert is correct, and the FE flows are clean and i18n-complete. The two genuine functional defects are the missing MFA-challenge → lockout integration and the hardcoded `mfaEnabled=false` on ProfilePage. The migration revision-id collision is a merge-time blocker that the implementation team must coordinate, not a defect in the code itself.

**Decision: CHANGES_REQUESTED.** Hand off to Test agent in parallel — required fixes #2 and #3 can be patched while testing covers the rest. Fix #1 is a merge gate, not a test gate.
