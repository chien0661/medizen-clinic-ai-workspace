# FE-Consumed APIs — TASK-017 Contract Documentation

**Date:** 2026-04-27
**Status:** Phase A Complete (FE-side implementation + unit tests validated)
**Note:** This document covers the FE consumer-side contracts for the 4 auth endpoints. BE implementation per TASK-003.

---

## Overview

Frontend consumes 4 authentication endpoints from the Backend (TASK-003). This document specifies:
- Request shapes (as sent by FE via `apiClient.ts` or `LoginPage.tsx`)
- Expected response shapes (from BE)
- Error codes FE handles
- Known contract ambiguities or gaps

---

## 1. POST /api/v1/auth/login

### Request

```json
{
  "username": "doctor01@clinic.local",
  "password": "MyPassword123!",
  "clinic_code": "CLINIC001"
}
```

### Request TS Interface

```typescript
interface LoginRequest {
  username: string;        // email or staff code
  password: string;        // plaintext (sent over HTTPS)
  clinic_code: string;     // multi-tenant identifier
}
```

### Response (200 OK)

```json
{
  "code": "00",
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "user-uuid-123",
      "full_name": "Nguyễn Văn A",
      "roles": ["DOCTOR"],
      "permissions": ["doctor", "prescription"],
      "password_expired": false
    },
    "clinic": {
      "id": "clinic-uuid-456",
      "code": "CLINIC001",
      "name": "Phòng khám Đa khoa ABC"
    }
  }
}
```

### Response TS Interface

```typescript
interface LoginResponse {
  code: string;
  message: string;
  data: {
    access_token: string;      // JWT — attach to all subsequent requests
    refresh_token: string;     // Long-lived JWT for token refresh
    user: {
      id: string;              // User UUID
      full_name: string;       // Display name
      roles: string[];         // High-level roles (DOCTOR, ADMIN, etc.)
      permissions: string[];   // Fine-grained permissions (doctor, pharmacy, etc.)
      password_expired?: boolean; // **OPTIONAL** — see "Contract Ambiguity" below
    };
    clinic?: {                 // Optional clinic context
      id: string;
      code: string;
      name: string;
    };
  };
}
```

### Error Responses

| HTTP | Code | Message | FE Behavior |
|------|------|---------|-------------|
| 401 | INVALID_CREDENTIALS | "Invalid username or password" | Show error toast; increment login attempt counter. If counter ≥ 5 → show 30s lockout countdown. |
| 423 | USER_LOCKED | "Account locked due to multiple failed attempts. Try again after {retry_after_seconds}s." | Show lockout countdown (read `Retry-After` header or default 30s). Disable login button. |
| 429 | RATE_LIMIT | "Too many requests. Please try again after {retry_after_seconds}s." | Show rate-limit countdown. Disable button. Read `Retry-After` header or default 60s. |
| 400 | INVALID_REQUEST | "Missing required field: {field}" | Show validation error. Highlight missing field. |
| 500 | INTERNAL_ERROR | "Internal server error" | Show generic error toast; allow retry. |

### FE Implementation Notes

- Located in: `src/pages/auth/LoginPage.tsx`
- Token storage: `authStore.setTokens()` → writes to Tauri secure store (TASK-016)
- Redirect logic:
  - If `password_expired === true` → navigate to `/change-password`
  - Else → navigate to `/dashboard` or remembered location
- Remember-me: Checkbox state (UI-only; FE does not send to BE; tokens persisted regardless via secure store)

### Contract Ambiguity: password_expired Field

**Status:** Unclear per TASK-003 spec

**Issue:** Spec does not explicitly state whether BE returns `user.password_expired` on login response.

**FE Handling (graceful degradation):**
- If field present + value is `true` → forced redirect to `/change-password`
- If field absent or value is `false` → no forced change; proceed to dashboard
- If field missing but BE actually requires password change → user proceeds to dashboard; subsequent API calls may fail until password changed (BE-side validation)

**Recommendation for Phase B Integration:**
- Confirm BE returns `user.password_expired: boolean` in login response (default `false`)
- If BE omits field entirely, update contract and re-validate FE behavior
- If BE returns `true` but FE proceeds to dashboard → log warning; defer to TASK-018+ for BE/FE sync

---

## 2. POST /api/v1/auth/refresh

### Request

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Request TS Interface

```typescript
interface RefreshRequest {
  refresh_token: string;  // Long-lived JWT from login or previous refresh
}
```

### Response (200 OK)

```json
{
  "code": "00",
  "message": "Token refreshed",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### Response TS Interface

```typescript
interface RefreshResponse {
  code: string;
  message: string;
  data: {
    access_token: string;    // New JWT access token
    refresh_token: string;   // May be rotated or same (BE-dependent)
  };
}
```

**Note:** FE does **NOT** expect `user` object in refresh response. The `apiClient.rotateTokens()` path deliberately excludes user updates to avoid stomping existing user state during mid-session token refresh.

### Error Responses

| HTTP | Code | Message | FE Behavior |
|------|------|---------|-------------|
| 401 | INVALID_TOKEN | "Refresh token invalid or expired" | Call `authStore.logout()` → clear tokens from secure store → redirect to `/login`. Show "Session expired" toast. |
| 401 | TOKEN_EXPIRED | "Token has expired" | Same as INVALID_TOKEN — logout + redirect. |
| 400 | INVALID_REQUEST | "Missing refresh_token" | Log error; logout + redirect. |
| 500 | INTERNAL_ERROR | "Internal server error" | Return false from `doRefresh()` → trigger logout path. |

### FE Implementation Notes

- Located in: `src/lib/apiClient.ts:doRefresh()` (line 30-55)
- Called automatically when any API response returns 401 (if not a retry already)
- Deduplication via `refreshPromise` singleton: concurrent 401s → only 1 refresh POST
- Retry logic: on refresh success, original request retried with new access token
- If refresh fails (401 again) → logout + redirect to `/login` with error
- Token storage: `authStore.rotateTokens()` writes new tokens to secure store

---

## 3. POST /api/v1/auth/logout

### Request

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Request TS Interface

```typescript
interface LogoutRequest {
  refresh_token: string;  // Invalidate this token on BE side
}
```

### Response (200 OK)

```json
{
  "code": "00",
  "message": "Logged out successfully"
}
```

### Error Responses

| HTTP | Code | Message | FE Behavior |
|------|------|---------|-------------|
| 401 | UNAUTHORIZED | "Invalid token" | Ignore; user already logged out locally (tokens cleared). |
| 500 | INTERNAL_ERROR | "Internal server error" | Ignore; tokens already cleared locally. |

### FE Implementation Notes

- Located in: `src/stores/authStore.ts:logout()` (line 79-92)
- Called from Topbar user menu (logout button click)
- **Important:** FE clears tokens from secure store **before** sending POST /logout (no dependency on BE response)
- POST request is "best-effort" for audit trail / token invalidation; FE does not wait or retry
- Redirect to `/login` happens immediately after `authStore.logout()` state change
- Requires `Authorization: Bearer {access_token}` header

---

## 4. POST /api/v1/auth/change-password

### Request

```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

### Request TS Interface

```typescript
interface ChangePasswordRequest {
  old_password: string;     // Current password (for verification)
  new_password: string;     // New password (must meet strength rules)
}
```

### Response (200 OK)

```json
{
  "code": "00",
  "message": "Password changed successfully. Please log in again."
}
```

### Error Responses

| HTTP | Code | Message | FE Behavior |
|------|------|---------|-------------|
| 401 | INVALID_PASSWORD | "Old password is incorrect" | Show error under password field. Stay on `/change-password` form. User can retry. |
| 422 | VALIDATION_ERROR | "Password must be at least 12 characters with uppercase, lowercase, number, and special character" | Show field-level validation error under new_password. Stay on form. User adjusts input. |
| 400 | INVALID_REQUEST | "Missing required fields" | Show error toast. Stay on form. |
| 500 | INTERNAL_ERROR | "Internal server error" | Show error toast. Allow retry. |

### FE Implementation Notes

- Located in: `src/pages/auth/ChangePasswordPage.tsx`
- Called from `/change-password` screen (forced after login if `password_expired=true`, or from Settings in TASK-019+)
- Validation: React Hook Form + Zod schema (password strength rules in i18n validation messages)
- On 200 OK: redirect to `/login` (or auto-logout + redirect)
  - BE may invalidate all existing tokens, forcing re-login with new password
  - If tokens not invalidated, user can proceed; next session uses new password
- Requires `Authorization: Bearer {access_token}` header

---

## Error Matrix Summary

| Scenario | Endpoint | HTTP Status | FE Action |
|----------|----------|-------------|-----------|
| Invalid credentials | `/login` | 401 | Increment counter; if ≥5 → lockout countdown. |
| Account locked (BE-side) | `/login` | 423 | Show lockout countdown (Retry-After header). |
| Rate limit | `/login` or any | 429 | Show rate-limit countdown. Disable button. |
| Access token expired | Any (except `/login`) | 401 | Auto-refresh via `refreshTokenOnce()`. |
| Refresh token expired | `/refresh` | 401 | Logout + redirect to `/login`. |
| Network error | Any | Network timeout/CORS | ErrorBoundary catches; show toast "Connection failed". Allow retry. |

---

## Known Gaps & Phase B Validation

1. **password_expired ambiguity** — See Section 1 contract ambiguity. Phase B integration test must verify BE contract.

2. **Token rotation on refresh** — Spec unclear whether refresh response includes a new `refresh_token` or reuses existing. FE always updates whichever comes back; safe either way.

3. **User hydration on session restore** — If user JSON corrupts, FE gracefully sets `user = null` but `isAuthenticated = true`. No auto-fetch of `/auth/me` yet. TASK-018+ can implement if needed.

4. **Clinic context optional** — BE may or may not return `clinic` object in login response. FE stores whatever is provided via `authStore.setClinicContext()`. If absent, `clinicId` / `clinicCode` remain null (acceptable for single-clinic deployments or TASK-018 to add clinic-selection UI).

5. **Header-based retry logic** — `Retry-After` header (RFC 7231) on 423 / 429 → FE reads or defaults to fixed intervals. Not formally spec'd with BE; Phase B to confirm header presence + format.

---

## Security Notes

- **Tokens transmitted over HTTPS only** — enforce in environment config and BE
- **Secure store v1 plaintext** — TASK-016 issue. TODO: keyring crate migration.
- **No hardcoded credentials in code** — verified by static analysis
- **No token logging in console** — ErrorBoundary logs errors; full tokens never logged
- **CORS / same-origin policy** — Tauri webview enforces; no explicit FE CORS config needed

---

**End of FE-Consumed APIs Documentation**
