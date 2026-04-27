# API Specification — Auth Module (v1.0)

**Date**: 2026-04-27  
**Status**: Complete — 215/215 tests pass  
**Base URL**: `https://api.clinic.local/api/v1`  

---

## 1. POST /auth/login

Login with username + password, receive access + refresh tokens.

### Request

**Method**: `POST`  
**URL**: `/api/v1/auth/login`  
**Headers**:
```
Content-Type: application/json
X-Request-Id: <uuid> (optional, for tracing)
```

**Body Schema**:
```json
{
  "username": "string (1-100 chars, required)",
  "password": "string (8+ chars, required)",
  "clinic_code": "string (1-20 chars, required)"
}
```

**Validation Rules**:
- `username`: Required, 1-100 characters
- `password`: Required, 8+ characters
- `clinic_code`: Required, 1-20 characters (clinic identifier, not UUID)

### Response

**Success (200 OK)**:
```json
{
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJjbGluaWNfaWQiOiIzMzJlZWQ5Ni01YWNlLTQxZGUtYjkxZS05MDlhMzk2ZDFiMzUiLCJyb2xlcyI6W10sInBlcm1pc3Npb25zIjpbXSwidHlwZSI6ImFjY2VzcyIsImp0aSI6IjVmNmFlNjQ3LTljOGEtNDQ2NS05YjdlLWEwMWZhNWI4OTgyZiIsImlhdCI6MTcxNzM3MzAwMCwiZXhwIjoxNzE3Mzc0OTAwfQ.abc123...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJjbGluaWNfaWQiOiIzMzJlZWQ5Ni01YWNlLTQxZGUtYjkxZS05MDlhMzk2ZDFiMzUiLCJyb2xlcyI6W10sInBlcm1pc3Npb25zIjpbXSwidHlwZSI6InJlZnJlc2giLCJqdGkiOiI2ZGMwZjE4ZS1jN2JkLTQwYTAtYjVjOS1iYjE2YTQzOGU5YzAiLCJpYXQiOjE3MTczNzMwMDAsImV4cCI6MTcyNDU1MzAwMH0.def456...",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "full_name": "Dr. John Doe",
      "roles": [],
      "permissions": []
    }
  },
  "meta": {
    "timestamp": "2026-04-27T10:30:00Z"
  }
}
```

**JWT Claims (Access Token)** (15 min TTL):
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user_id
  "clinic_id": "332eed96-5ace-41de-b91e-909a396d1b35",
  "roles": [],
  "permissions": [],
  "type": "access",
  "jti": "5f6ae647-9c8a-4465-9b7e-a01fa5b8982f",  // token ID
  "iat": 1717373000,
  "exp": 1717374900
}
```

**JWT Claims (Refresh Token)** (7-30 days TTL):
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "clinic_id": "332eed96-5ace-41de-b91e-909a396d1b35",
  "type": "refresh",
  "jti": "6dc0f18e-c7bd-40a0-b5c9-bb16a438e9c0",
  "iat": 1717373000,
  "exp": 1724553000
}
```

**Error (401 Unauthorized)**:
```json
{
  "error": "AUTH_INVALID_CREDENTIALS",
  "detail": "Username, password, or clinic code is invalid",
  "meta": {
    "timestamp": "2026-04-27T10:30:05Z"
  }
}
```

**Error (423 Locked)**:
```json
{
  "error": "AUTH_USER_LOCKED",
  "detail": "Account is locked due to too many failed login attempts. Please contact administrator.",
  "meta": {
    "timestamp": "2026-04-27T10:30:05Z"
  }
}
```

**Error (429 Too Many Requests)**:
```json
{
  "detail": "Rate limit exceeded"
}
```

### Error Codes

| Code | HTTP | Trigger |
|------|------|---------|
| `AUTH_INVALID_CREDENTIALS` | 401 | Wrong clinic/username/password, clinic inactive, user inactive |
| `AUTH_USER_LOCKED` | 423 | ≥5 failed attempts in 15 min window |
| Rate limit | 429 | >10 requests/minute from same IP |
| Validation error | 422 | Missing/malformed field (Pydantic) |

### Examples

**Curl Request**:
```bash
curl -X POST https://api.clinic.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: 123e4567-e89b-12d3-a456-426614174000" \
  -d '{
    "username": "dr_john",
    "password": "SecurePass123!",
    "clinic_code": "CLI001"
  }'
```

**Curl Response (Success)**:
```bash
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "full_name": "Dr. John Doe",
      "roles": [],
      "permissions": []
    }
  },
  "meta": {"timestamp": "2026-04-27T10:30:00Z"}
}
```

---

## 2. POST /auth/refresh

Rotate refresh token — revoke old token, issue new access + refresh pair.

### Request

**Method**: `POST`  
**URL**: `/api/v1/auth/refresh`  
**Headers**:
```
Content-Type: application/json
```

**Body Schema**:
```json
{
  "refresh_token": "string (JWT, required)"
}
```

### Response

**Success (200 OK)**:
```json
{
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "full_name": "Dr. John Doe",
      "roles": [],
      "permissions": []
    }
  },
  "meta": {"timestamp": "2026-04-27T10:35:00Z"}
}
```

**Error (401 Unauthorized)**:
```json
{
  "error": "AUTH_TOKEN_INVALID|AUTH_TOKEN_EXPIRED|AUTH_TOKEN_REVOKED",
  "detail": "Token is invalid, expired, or has been revoked",
  "meta": {"timestamp": "2026-04-27T10:35:05Z"}
}
```

### Error Codes

| Code | HTTP | Trigger |
|------|------|---------|
| `AUTH_TOKEN_INVALID` | 401 | Malformed JWT, wrong algorithm, missing claims (jti/sub/clinic_id/exp), wrong token type (not "refresh"), user not found, user inactive/locked |
| `AUTH_TOKEN_EXPIRED` | 401 | Token exp < now |
| `AUTH_TOKEN_REVOKED` | 401 | Token jti in Redis blacklist (already used for refresh or logout) |

### Examples

**Curl Request**:
```bash
curl -X POST https://api.clinic.local/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

**Behavior Notes**:
- Old jti is revoked to Redis BEFORE new tokens are issued (no replay window)
- Attempting to refresh again with the same token returns 401 (`AUTH_TOKEN_REVOKED`)
- New refresh token has a new jti

---

## 3. POST /auth/logout

Revoke a refresh token (add jti to Redis blacklist). Best-effort operation.

### Request

**Method**: `POST`  
**URL**: `/api/v1/auth/logout`  
**Headers**:
```
Content-Type: application/json
```

**Body Schema**:
```json
{
  "refresh_token": "string (JWT, required)"
}
```

### Response

**Success (204 No Content)**:
```
(empty body)
```

### Behavior

- Attempts to decode token and extract jti
- Adds jti to Redis blacklist with TTL = token exp time
- Audit event logged (best-effort, exceptions swallowed)
- Always returns 204 (even if token invalid/expired/already revoked)
- No error responses

### Examples

**Curl Request**:
```bash
curl -X POST https://api.clinic.local/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

**Curl Response**:
```bash
HTTP/1.1 204 No Content
```

---

## 4. POST /auth/change-password

Change user password. Requires valid access token (via Authorization header and X-Clinic-Id).

### Request

**Method**: `POST`  
**URL**: `/api/v1/auth/change-password`  
**Headers** (Required):
```
Content-Type: application/json
Authorization: Bearer <access_token>
X-Clinic-Id: <clinic_uuid>
```

**Body Schema**:
```json
{
  "old_password": "string (8+ chars, required)",
  "new_password": "string (8+ chars, required)"
}
```

**Validation Rules**:
- `old_password`: Required, 8+ characters
- `new_password`: Required, 8+ characters, must differ from old_password

### Response

**Success (204 No Content)**:
```
(empty body)
```

**Error (401 Unauthorized)**:
```json
{
  "error": "AUTH_PASSWORD_MISMATCH|AUTH_TOKEN_INVALID",
  "detail": "Old password is incorrect or token is invalid",
  "meta": {"timestamp": "2026-04-27T10:40:00Z"}
}
```

**Error (422 Unprocessable Entity)**:
```json
{
  "detail": [
    {
      "loc": ["body", "new_password"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.string.too_short"
    }
  ]
}
```

### Error Codes

| Code | HTTP | Trigger |
|------|------|---------|
| `AUTH_PASSWORD_MISMATCH` | 401 | old_password does not match user.password_hash |
| `AUTH_TOKEN_INVALID` | 401 | access_token invalid/expired/missing |
| Validation error | 422 | Field validation failure (Pydantic) |

### Examples

**Curl Request**:
```bash
curl -X POST https://api.clinic.local/api/v1/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Clinic-Id: 332eed96-5ace-41de-b91e-909a396d1b35" \
  -d '{
    "old_password": "OldPass123!",
    "new_password": "NewPass456!"
  }'
```

**Curl Response (Success)**:
```bash
HTTP/1.1 204 No Content
```

---

## Appendix A: JWT Encoding Details

### HS256 Algorithm

- **Secret**: `JWT_SECRET` from app settings (min 8 chars, default "change-me-in-production")
- **Algorithm**: HS256 (HMAC SHA-256)
- **Library**: `python-jose` (jose.jwt.encode/decode)

### Token Pair Structure

| Token Type | Duration | Rotation | Use |
|------------|----------|----------|-----|
| Access | 15 minutes | No (stateless) | Authorize protected API requests |
| Refresh | 7-30 days (config) | Yes (revoke old on each use) | Obtain new access token pair |

### Claims

**Access Token**:
```json
{
  "sub": "user_id (UUID)",
  "clinic_id": "clinic_id (UUID)",
  "roles": ["role_slug_1", ...],
  "permissions": ["perm_key_1", ...],
  "type": "access",
  "jti": "unique_token_id (UUID)",
  "iat": "issued_at (unix timestamp)",
  "exp": "expiry (unix timestamp)"
}
```

**Refresh Token**:
```json
{
  "sub": "user_id (UUID)",
  "clinic_id": "clinic_id (UUID)",
  "type": "refresh",
  "jti": "unique_token_id (UUID)",
  "iat": "issued_at (unix timestamp)",
  "exp": "expiry (unix timestamp)"
}
```

### Verification Rules

- **Signature**: Verified using `JWT_SECRET` + HS256
- **Algorithm**: Must be HS256 (reject `alg=none`)
- **Expiry**: `exp < now` → token expired
- **Type Check**: Access endpoints should not accept refresh tokens
- **Blacklist**: Check jti in Redis before accepting

---

## Appendix B: Authentication Flow Diagram

```
┌─────────────────────────────────────────────┐
│ Client                                       │
└──────────────────┬──────────────────────────┘
                   │
                   ├─ [1] POST /auth/login
                   │       (username, password, clinic_code)
                   │
                   │ API validates credentials
                   │ → Returns access_token (15m) + refresh_token (7d)
                   │
                   ├─ [2] Store tokens locally (secure storage)
                   │
                   ├─ [3] Use access_token for protected requests
                   │       Authorization: Bearer <access_token>
                   │
                   │ [3a] If 401 (token expired):
                   │       POST /auth/refresh
                   │       (refresh_token)
                   │       → Returns new access + refresh pair
                   │       → Old refresh jti added to Redis blacklist
                   │
                   │ [3b] If still 401 (refresh expired):
                   │       Prompt login again
                   │
                   ├─ [4] On logout:
                   │       POST /auth/logout
                   │       (refresh_token)
                   │       → Revokes jti to Redis
                   │
                   └─ [5] Clear local token storage
```

---

## Appendix C: Configuration & Environment

### Required Environment Variables

```bash
# JWT
JWT_SECRET=<your-production-secret>  # min 8 chars
JWT_ALGORITHM=HS256

# Token TTL
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7  # To 30

# Lockout
LOCKOUT_MAX_ATTEMPTS=5
LOCKOUT_WINDOW_MINUTES=15
LOCKOUT_DURATION_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Production Recommendations

1. **JWT_SECRET**: Rotate using a key management service; never hardcode in repo
2. **REDIS_URL**: Use managed Redis (e.g., Redis Enterprise, AWS ElastiCache)
3. **Rate Limit**: Switch `slowapi` storage to Redis-backed before multi-worker deploy
4. **HTTPS**: Always use HTTPS in production (JWT in Authorization header)
5. **Secure Cookies**: If using client-side storage, set `HttpOnly + Secure + SameSite=Strict`

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-27  
**API Version**: v1.0
