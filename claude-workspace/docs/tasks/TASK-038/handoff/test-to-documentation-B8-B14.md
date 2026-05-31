# TASK-038 B.8–B.14 Test Report

**Date**: 2026-05-01
**Agent**: Test agent
**Scope**: MFA (TOTP) + Login Fingerprint (NFR-029, NFR-035) — post-fix-mode verification
**Verdict**: **PARTIAL PASS** — all functional tests green; 2 FE lint/TS errors and pre-existing integration failures documented below

---

## 1. Test Counts — Final (Post-Fix + New Tests)

### Backend (Python 3.11, Docker)

| Suite | Tests | Result |
|---|---|---|
| `tests/unit/test_mfa_service.py` | 24 | 24 PASS |
| `tests/integration/test_auth_mfa.py` (original 5 + fix 2 + new 3) | 10 | 10 PASS |
| **MFA subtotal** | **34** | **34 PASS** |

#### Full BE unit suite

| Suite | Pass | Fail | Notes |
|---|---|---|---|
| `tests/unit/` (all) | 519 | **2** | Both failures are **pre-existing** (see §4) |

#### Full BE integration suite (`-m "not slow"`)

| Suite | Pass | Fail | Error | Notes |
|---|---|---|---|---|
| `tests/integration/` | 348 | 43 | 146 | All failures **pre-existing** (TASK-010/TASK-015 e2e DB-state ordering issues); MFA tests (10) pass cleanly in isolation |

### Frontend (Vitest + happy-dom)

| Suite | Tests | Result |
|---|---|---|
| Full `npm test -- --run` | 566 | 566 PASS |

---

## 2. New Tests Added (3 BE Integration Tests)

All 3 added to `tests/integration/test_auth_mfa.py`:

### `TestMfaTokenExpiredRejected::test_mfa_token_expired_rejected`
- Crafts a JWT with `exp = now - 6 minutes` (past the 5-min TTL)
- Asserts `complete_mfa_challenge` raises `ValueError("invalid_token")`
- **Result: PASS** — jose raises JWTError on expired token; service converts correctly

### `TestMfaTokenWrongTypeRejected::test_mfa_token_wrong_type_rejected`
- Submits a valid `access` token (type=`"access"`) to the MFA challenge endpoint
- Asserts `ValueError("invalid_token")` before any OTP check occurs
- **Result: PASS** — type claim guard at line 415 of `auth_service.py` rejects correctly

### `TestMfaOtpReplayWithinWindow::test_mfa_otp_replay_within_window_succeeds`
- Submits the same TOTP OTP code twice within the same 30-second window
- Documents CURRENT PERMISSIVE behavior: both submissions succeed
- **Result: PASS (expected permissive behavior)** — see §5 for hardening gap details

---

## 3. TypeScript / ESLint Check Results

**2 errors found** — both in stream C (MFA implementation) files, both are `no-unused-vars` violations:

| File | Line | Error | Severity |
|---|---|---|---|
| `src/pages/auth/MfaVerifyPage.tsx` | 49 | `'setClinicContext' is assigned a value but never used` | ESLint error / TS6133 |
| `src/pages/profile/ProfilePage.tsx` | 33 | `'t' is assigned a value but never used` | ESLint error / TS6133 |

**These are implementation bugs introduced by stream C** — not pre-existing. Both files were untracked (new files from this stream).

**Required fix before merge:** Remove unused destructure members:
- `MfaVerifyPage.tsx:49` — remove `setClinicContext` from the `useAuthStore()` destructure (or use it)
- `ProfilePage.tsx:33` — remove `t` from the `useTranslation()` destructure (or use it)

Note: These errors cause CI lint gate to fail with `--max-warnings 0`. FE vitest tests still pass because Vitest does not enforce TS strict mode at runtime.

---

## 4. Pre-Existing Failures (Not Caused by Stream C)

### BE Unit (2 failures)

| Test | Cause | Stream |
|---|---|---|
| `test_hr_service_logic.py::TestCheckInRejectsOtherUsersShiftId::test_check_in_rejects_other_users_shift_id` | Test expects `PermissionError` but service raises `NotFoundError` after FIX-4a in TASK-014 HR service | Pre-existing (TASK-014) |
| `test_tenancy_middleware.py::TestDevHeaders::test_clinic_id_only_no_user_allowed` | Tenancy middleware behavior change — pre-dates MFA branch | Pre-existing |

### BE Integration (43 failures + 146 errors)

All failures are in `tests/integration/services/test_services_e2e.py` (TASK-010) and `tests/integration/reports/test_reports_e2e.py` (TASK-015). These tests share a database with no isolation between test sessions — failures are caused by DB state contamination when run together. Tests pass individually. The MFA stream did not touch any of these files.

**Confirmed**: `git log --oneline -- tests/integration/services/test_services_e2e.py` shows last commit `dc1f096` from TASK-010 (predates TASK-038 by multiple task cycles). No changes from stream C.

---

## 5. Migration Conflict — Status

**Status: CONFLICT EXISTS — not auto-resolved, not merged**

This branch's `alembic/versions/0021_add_mfa_columns_to_user.py` claims:
- `revision = "0021"`
- `down_revision = "65fc9ae59ba5"`

According to the code review, Streams A (`0021_multi_clinic_account`) and B (`0021_password_history`) also claim the same revision ID and down-revision. The conflict is a **merge-time blocker** — Alembic will refuse to upgrade once two `0021` files coexist in the same environment.

**Current state**: Only Stream C's file is present in this worktree. No auto-resolution was attempted. This is correct per task constraints.

**Action required**: Stream lead must coordinate renumbering before any of the three branches is merged to main. Recommended approach: renumber as `0021a / 0021b / 0021c` or chain them linearly (`0021 → 0022 → 0023`, adjusting this branch's `0022_create_login_fingerprint.py` to `0024`).

---

## 6. Remaining Hardening Items

These items were identified in the code review and are documented here for the Documentation agent to include in the security delivery:

### H-1: Backup code entropy — MEDIUM severity

- **Issue**: 10 chars from 36-char alphabet = log2(36¹⁰) ≈ **51.7 bits**. Target is ≥80 bits.
- **Mitigation**: Codes are bcrypt-hashed (cost=12) and one-time use — brute-force is infeasible in practice.
- **Recommendation**: Raise to 12 chars (≈62 bits) minimum, ideally 16 chars (≈82 bits) or switch to full base32 alphabet.
- **Blocking merge?**: No — but must be tracked as a hardening backlog item.

### H-2: OTP replay protection not implemented — LOW severity

- **Issue**: `pyotp.TOTP.verify(valid_window=1)` allows re-use of the same OTP within the 30-second window. RFC 6238 §5.2 recommends server-side "remember last consumed OTP step" per user.
- **Test**: `test_mfa_otp_replay_within_window_succeeds` documents the permissive behavior.
- **Mitigation**: Attacker must possess the live OTP (phishing/MITM scenario) within the same 30-second window; lockout after failed attempts limits brute-force.
- **Recommendation**: Add `last_used_otp_step: int | None` column to User model; compare in `mfa_service.verify()` and reject if step ≤ last_used.
- **Blocking merge?**: No — deferred to hardening backlog.

### H-3: mfa_token shares JWT_SECRET with access/refresh — INFO

- `type` claim separation prevents cross-use; acceptable trade-off.
- Document in threat model.

### H-4: TOTP secret stored plaintext — INFO

- Deferred to TASK-037 column-level encryption scope.
- Add TODO comment in `app/modules/users/models/user.py` with ticket reference.

### H-5: X-Forwarded-For not validated against trusted proxy — LOW

- Clients can spoof IP in anomaly detection.
- Out of B.8-B.14 scope; flag for hardening.

### H-6: FE lint errors — REQUIRED FIX BEFORE MERGE

- 2 unused variable errors (§3 above) will fail CI lint gate.

---

## 7. Summary

| Category | Status |
|---|---|
| MFA unit + integration tests (34) | ALL PASS |
| FE test suite (566) | ALL PASS |
| 3 new gap tests added | DONE |
| Migration conflict | CONFIRMED — not auto-resolved |
| FE TS/ESLint | 2 ERRORS in stream C files (lint gate will fail) |
| BE pre-existing failures | 2 unit + 43 integration (not caused by stream C) |
| Hardening gaps | 2 deferred items documented (entropy + replay) |

**Verdict: PARTIAL PASS**

All functional requirements for B.8–B.14 are implemented and tested. The 2 FE lint errors must be fixed before CI can pass. The migration revision conflict must be resolved before merge. All other items are either pre-existing or deferred with documented rationale.

The Documentation agent should capture:
1. FE lint errors as required pre-merge fixes
2. Migration conflict as merge gate
3. Hardening items H-1 through H-5 in the security delivery section
