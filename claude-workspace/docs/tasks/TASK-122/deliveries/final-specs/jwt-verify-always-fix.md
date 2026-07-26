# TASK-122: JWT Signature Verification Always Applied (C-1 dev-bypass removed)

**Status:** DONE  
**Date Completed:** 2026-07-26  
**Branch:** `fix/TASK-122-jwt-verify-always` (base `origin/dev` @ `45c5b32`, head migration 0069)  
**Repo:** clinic-cms-be

---

## Executive Summary

Removed critical authentication bypass: the `TenancyMiddleware` accepted **unsigned/forged JWT tokens** whenever `ENVIRONMENT=development`. The unsafe decode function has been **completely removed**; the JWT authentication path now **unconditionally verifies HMAC signatures** in every environment. Forged tokens → 401; valid tokens → 200 (no regression).

---

## The Vulnerability (C-1)

### What was wrong
- `_decode_jwt_payload_unsafe()` in `app/core/tenancy.py` base64-decoded JWT payload segments **without verifying the signature**.
- The middleware called this when `ENVIRONMENT=development`, trusting unverified claims (`sub`, `is_superuser`, `clinic_id`) to make authentication/authorization decisions.
- `.env.example` defaults to `ENVIRONMENT=development` → a deploy that forgets to override ships completely open.
- An attacker could craft any token with `is_superuser=true` and gain admin/RLS-bypass access.

### Why it existed
The unsafe decode was a "convenience" for local development — developers could hand-craft unsigned tokens for testing without computing a real HMAC signature. It had **one call site only** and served **no legitimate non-authentication purpose**.

---

## The Fix

### Approach
1. **Deleted `_decode_jwt_payload_unsafe()` entirely** — removed the function and its unused `base64`/`json` imports.
2. **Removed the environment selector** — the `if _IS_DEVELOPMENT: ... else: ...` branch that chose between unsafe and verified decode is gone.
3. **Unified the auth path** — `TenancyMiddleware.dispatch` now calls **`_decode_jwt_payload_verified()`** unconditionally in every ENVIRONMENT (verified HS256 against `JWT_SECRET`).

### What unchanged
- **Dev-header fallback (`X-Clinic-Id`/`X-User-Id`)** — still present, still development-only, still requires no Bearer token. Does **not** set `is_superuser` and does not reintroduce the bypass. Marked for a separate hardening task (hard-fail `development` outside localhost, or drop headers entirely) but does not block this fix.

### Net Effect
- One JWT decode path in the entire auth flow: `_decode_jwt_payload_verified`, always used.
- No unverified claims are ever read for an auth/authz decision.
- Forged/unsigned/tampered tokens → `JWTError` → `{}` claims → 401 in every environment.

---

## Files Changed

| File | Changes |
|------|---------|
| `app/core/tenancy.py` | Removed `_decode_jwt_payload_unsafe()` and its dead imports; JWT branch now unconditionally calls verified decode; updated docstrings. |
| `tests/integration/test_jwt_signature.py` | Added `TestJWTSignatureVerificationInDevelopment` class with 3 tests exercising development-specific code path. |

---

## Test Results

### In-Scope Tests
**13/13 passed**
- 3 new tests in `TestJWTSignatureVerificationInDevelopment`:
  - Forged unsigned admin token in development → **401** (was 200 before fix)
  - Real token with truncated signature → **401** (was accepted before fix)
  - Properly HS256-signed valid token → **200** (no regression)
- 10 pre-existing auth/tenancy tests → all pass

### Regression Sweep
**63/72 passed** in broader auth/tenancy/erasure suite.  
9 failures are **pre-existing** fixture-setup issues in files untouched by this branch's diff (only `app/core/tenancy.py` changed). Verified identical failures on unmodified `origin/dev` (stashed the diff and re-ran).  
**0 new regressions.**

### Test Methodology
- Isolated Docker stack `z122` (api 9944, postgres 5444, redis 6426).
- `ENVIRONMENT=development` (the vulnerable setting).
- New `dev_client` fixture forces development without mocking away verification (unlike `prod_client`).
- Regression-proven: reverted fix locally, ran forged/truncated tests, confirmed they **failed** (catching the bug), reapplied fix.

---

## Static Analysis

| Tool | Result |
|------|--------|
| ruff | 0 new findings (2 pre-existing, unrelated to this change) |
| mypy | 0 new findings (1 pre-existing, pre-fix in jose imports) |

---

## Acceptance Criteria — All Met

| Criterion | Result |
|-----------|--------|
| Forged/unsigned/tampered token → 401 in every ENVIRONMENT | ✓ Verified in test |
| Valid signed token still works; no regression to auth flow | ✓ All pre-existing tests pass |
| Integration test: forged → 401, valid → 200 | ✓ Dedicated tests, reverse-validated |

---

## Follow-up Hardening Task (Out of Scope)

The `X-Clinic-Id`/`X-User-Id` dev-header fallback is **not equivalent to this bypass** (never sets superuser, requires no Bearer, development-only). However, the review recommends a separate hardening task to:
- Hard-fail if `ENVIRONMENT=development` is detected outside localhost, OR
- Drop the dev headers entirely and provide an alternative local testing mechanism.

This does not block the current fix but should be scheduled as a separate task for comprehensive auth-hardening.

---

## Verification Checklist for Review

- [x] `_decode_jwt_payload_unsafe()` fully removed / no unverified auth path remains
- [x] Repo-wide grep for JWT signature-bypass patterns — clean
- [x] Valid HS256-signed tokens still work in all environments
- [x] Forged/unsigned tokens → 401 in all environments (including development)
- [x] Tests genuinely exercise the development-specific code path (not mocked)
- [x] 0 new static-analysis findings
- [x] No regression to TASK-095 baseline or other auth tests

