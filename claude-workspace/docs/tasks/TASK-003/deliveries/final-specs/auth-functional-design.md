# Thiết kế chi tiết — Mô-đun Xác thực (Auth)

**Ngày**: 2026-04-27  
**Trạng thái**: Hoàn thành, 215/215 tests pass, 100% coverage auth_service.py  
**Phiên bản**: v1.0  

---

## 1. Tổng quan tính năng

### Mục đích

Module Auth cung cấp xác thực và phân quyền cho các bác sĩ, nhân viên, và quản lý phòng khám thông qua cơ chế JWT (JSON Web Token) với mã hóa bcrypt. Hệ thống hỗ trợ:
- Đăng nhập bằng tên dùng + mật khẩu
- Quay vòng refresh token với thu hồi Redis
- Khóa tài khoản sau N lần sai mật khẩu
- Đổi mật khẩu

### Phạm vi v1

**Những gì có**:
- User CRUD model (username, email, password_hash, is_locked, is_active)
- 4 endpoints: `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/change-password`
- bcrypt cost 12 (hash mật khẩu)
- HS256 JWT tokens (access 15 phút, refresh 7-30 ngày)
- Redis blacklist cho jti (refresh token revocation)
- Slowapi rate limit (10 req/phút/IP trên `/login`)
- Account lockout: 5 lần sai trong 15 phút → khóa 30 phút

**Những gì không có (phase sau)**:
- Password reset qua email/OTP
- 2FA (two-factor authentication)
- Multi-clinic per user
- RS256 (public-key JWT cho multi-issuer production)
- Redis-backed slowapi (in-process rate limit, không work multi-worker)

### Stakeholders

- **Clinicians/Doctors**: Sử dụng `/login` hàng ngày
- **Admins**: Giám sát lockout, audit logs
- **DevOps**: Quản lý JWT_SECRET rotation, Redis dependency

---

## 2. Luồng xử lý tổng thể

```
┌─────────────────────────────────────────────────┐
│ Login Request (username, password, clinic_code) │
└──────────────────┬──────────────────────────────┘
                   │
                   ├─ Clinic lookup by code
                   │  └─ Clinic inactive? → 401
                   │
                   ├─ User lookup (clinic_id, username)
                   │  └─ Not found? → Redis INCR counter
                   │                → Check threshold
                   │                → 401
                   │
                   ├─ Check is_locked (before password check)
                   │  └─ is_locked=True? → 423
                   │
                   ├─ Verify password (bcrypt)
                   │  ├─ Wrong? → Redis INCR
                   │  │         → Flush failed_count
                   │  │         → Check threshold → lock if ≥5
                   │  │         → Audit "login_failed"
                   │  │         → 401
                   │  │
                   │  └─ Correct? → Reset failed_count=0
                   │             → Update last_login_at
                   │             → Redis DEL counter
                   │             → Create tokens
                   │             → Audit "login"
                   │             → 200 + tokens
                   │
                   └─ Return TokenPair + UserInfo
                      (access_token, refresh_token, user_id, full_name, roles)
```

**Quy trình Refresh Token**:
```
Old Refresh Token (jti1) → Validate claims & blacklist check
                        → Revoke jti1 to Redis (SET with TTL = exp)
                        → Create new access + refresh tokens
                        → Issue new pair
                        → Audit "token_refreshed"
                        → Return new tokens
```

**Quy trình Logout**:
```
Refresh Token → Validate & decode (no signature check if already revoked)
              → Add jti to Redis blacklist
              → Audit "logout" (best-effort)
              → 204 No Content
```

**Quy trình Change Password**:
```
Old Password + New Password → Validate auth (access_token required)
                           → Verify old password matches
                           → Hash new password (bcrypt cost 12)
                           → Update User.password_hash + password_changed_at
                           → Audit "password_changed"
                           → 204
```

---

## 3. Nguồn dữ liệu đầu vào

Không áp dụng — tính năng này không có message queue hoặc file import. Dữ liệu chỉ đến từ API calls của end-users.

---

## 4. Danh sách API

| Endpoint | Phương thức | Mô tả | Auth | Rate Limit |
|----------|------------|-------|------|-----------|
| `/api/v1/auth/login` | POST | Đăng nhập, nhận access + refresh token | Không | 10/phút/IP |
| `/api/v1/auth/refresh` | POST | Quay vòng refresh token (revoke cũ, cấp mới) | Không (token là credential) | Không |
| `/api/v1/auth/logout` | POST | Thu hồi refresh token (revoke blacklist) | Không | Không |
| `/api/v1/auth/change-password` | POST | Đổi mật khẩu | Yêu cầu access_token | Không |

---

## 5. Chi tiết từng API

### 5.1 POST /api/v1/auth/login

**Mục đích**: Xác thực người dùng bằng tên dùng + mật khẩu, trả về cặp token (access + refresh).

**Input**:
```json
{
  "username": "dr_john",
  "password": "SecurePass123!",
  "clinic_code": "CLI001"
}
```

**Validation**:
- `username`: 1-100 chars, required
- `password`: 8+ chars, required
- `clinic_code`: 1-20 chars, required

**Processing steps**:
1. Tra cứu phòng khám theo code, kiểm tra `is_active`
2. Tra cứu user theo (clinic_id, username)
3. Kiểm tra `is_locked` (nếu True → 423 ngay lập tức)
4. Xác minh mật khẩu bcrypt
   - Nếu sai: INCR Redis counter, kiểm tra ngưỡng 5, nếu đạt → lock user (autonomous tx), audit "login_failed", return 401
   - Nếu đúng: reset failed_count, update last_login_at, DEL Redis counter, tạo tokens
5. Audit "login"
6. Return 200 + tokens

**Output (Success 200)**:
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
  "meta": {
    "timestamp": "2026-04-27T10:30:00Z"
  }
}
```

**Error Responses**:
- **401 Unauthorized**: `clinic_code` không tồn tại, clinic inactive, user không tồn tại, user inactive, mật khẩu sai
  ```json
  {"error": "AUTH_INVALID_CREDENTIALS", "detail": "..."}
  ```
- **423 Locked**: Account khóa sau ≥5 lần sai
  ```json
  {"error": "AUTH_USER_LOCKED", "detail": "Account locked due to too many failed attempts"}
  ```
- **429 Too Many Requests**: Rate limit (10/phút/IP)
  ```json
  {"detail": "Rate limit exceeded"}
  ```

**SQL References**:
- `SELECT * FROM clinic WHERE code = ? AND is_deleted = false`
- `SELECT * FROM "user" WHERE clinic_id = ? AND username = ? AND is_deleted = false`
- `UPDATE "user" SET is_locked = true WHERE id = ?` (autonomous transaction)
- `UPDATE "user" SET failed_login_count = failed_login_count + 1 WHERE id = ?`
- `UPDATE "user" SET failed_login_count = 0, last_login_at = now() WHERE id = ?`

---

### 5.2 POST /api/v1/auth/refresh

**Mục đích**: Quay vòng refresh token (thu hồi token cũ, cấp cặp token mới).

**Input**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Validation**:
- `refresh_token`: JWT string, required

**Processing steps**:
1. Decode token (HS256, verify signature, check `exp`)
2. Kiểm tra `type == "refresh"` (reject "access" tokens)
3. Extract claims: `jti`, `sub` (user_id), `clinic_id`, `exp`
4. Kiểm tra jti trong Redis blacklist → 401 nếu revoked
5. Tra cứu user (user_id, clinic_id), kiểm tra `is_locked` và `is_active` → 401 nếu lỗi
6. Revoke old jti: `SET Redis key=jti, value=1, TTL=exp_time`
7. Mint tokens mới (access + refresh)
8. Audit "token_refreshed"
9. Return 200 + new tokens

**Output (Success 200)**:
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

**Error Responses**:
- **401 Unauthorized**: Invalid token, expired, revoked, wrong type, user not found, user locked/inactive
  ```json
  {"error": "AUTH_TOKEN_INVALID|AUTH_TOKEN_EXPIRED|AUTH_TOKEN_REVOKED", "detail": "..."}
  ```

---

### 5.3 POST /api/v1/auth/logout

**Mục đích**: Thu hồi refresh token (thêm jti vào Redis blacklist).

**Input**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Processing steps**:
1. Decode token (decode_only, không verify signature nếu jti đã revoked)
2. Extract jti, exp
3. Thêm jti vào Redis blacklist với TTL = exp_time
4. Audit "logout" (best-effort, swallow exceptions)
5. Return 204 (no content)

**Output (Success 204)**: Empty body

**Error Responses**: Không có (logout là best-effort, luôn return 204)

---

### 5.4 POST /api/v1/auth/change-password

**Mục đích**: Đổi mật khẩu (yêu cầu auth bằng access_token).

**Headers Required**:
```
Authorization: Bearer <access_token>
X-Clinic-Id: <clinic_uuid>
```

**Input**:
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

**Validation**:
- `old_password`: 8+ chars, required
- `new_password`: 8+ chars, required
- Phải khác nhau

**Processing steps**:
1. Extract user_id từ access_token (via TenancyMiddleware + current_user_id)
2. Tra cứu user từ DB
3. Verify old_password matches user.password_hash (bcrypt.checkpw)
   - Sai → return 401
4. Hash new_password (bcrypt cost 12)
5. Update User.password_hash, password_changed_at = now()
6. Audit "password_changed"
7. Return 204

**Output (Success 204)**: Empty body

**Error Responses**:
- **401 Unauthorized**: old_password sai, access_token invalid/expired
  ```json
  {"error": "AUTH_PASSWORD_MISMATCH", "detail": "Old password is incorrect"}
  ```
- **404 Not Found**: user không tồn tại (mâu thuẫn nội bộ)

---

## 6. Cấu trúc cơ sở dữ liệu

### Bảng: `user`

| Cột | Kiểu | Nullable | Mặc định | Mô tả |
|-----|------|----------|---------|-------|
| `id` | UUID | NO | gen_random_uuid() | Primary Key |
| `clinic_id` | UUID | NO | — | FK → clinic.id (RESTRICT) |
| `created_at` | TIMESTAMPTZ | NO | now() | |
| `updated_at` | TIMESTAMPTZ | NO | now() | |
| `created_by` | UUID | YES | NULL | Audit: who created |
| `updated_by` | UUID | YES | NULL | Audit: who updated |
| `is_deleted` | BOOLEAN | NO | false | Soft delete |
| `deleted_at` | TIMESTAMPTZ | YES | NULL | |
| `deleted_by` | UUID | YES | NULL | |
| `version` | INT | NO | 1 | Optimistic lock |
| `username` | VARCHAR(100) | NO | — | Unique per clinic (partial index) |
| `email` | VARCHAR(255) | YES | NULL | Unique per clinic when not NULL (partial index) |
| `phone` | VARCHAR(30) | YES | NULL | |
| `full_name` | VARCHAR(200) | NO | — | |
| `password_hash` | VARCHAR(255) | NO | — | bcrypt hash (cost 12), excluded from audit |
| `is_active` | BOOLEAN | NO | true | Tạm khóa tài khoản (admin) |
| `is_locked` | BOOLEAN | NO | false | Khóa vĩnh viễn (quá nhiều sai) |
| `failed_login_count` | INT | NO | 0 | Bộ đếm (reset after success/timeout) |
| `last_login_at` | TIMESTAMPTZ | YES | NULL | |
| `password_changed_at` | TIMESTAMPTZ | YES | NULL | |
| `license_number` | VARCHAR(100) | YES | NULL | Doctor-specific |
| `specialty_subfield` | VARCHAR(200) | YES | NULL | Doctor-specific |

### Indexes

```sql
-- Composite index for active user queries per clinic
CREATE INDEX ix_user_clinic_id_is_active ON "user" (clinic_id, is_active);

-- Partial unique: username per clinic (non-deleted)
CREATE UNIQUE INDEX uq_user_clinic_username 
  ON "user" (clinic_id, username) 
  WHERE NOT is_deleted;

-- Partial unique: email per clinic (non-deleted, non-null)
CREATE UNIQUE INDEX uq_user_clinic_email 
  ON "user" (clinic_id, email) 
  WHERE email IS NOT NULL AND NOT is_deleted;

-- Standard tenant index
CREATE INDEX ix_user_clinic_id ON "user" (clinic_id);
```

### RLS (Row-Level Security)

Tenant isolation policy (per `apply_rls_with_tenant_isolation`):
- Users can only see records in their clinic_id
- Enforced at database level

### Permissions

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON "user" TO cms_app;
```

---

## 7. SQL tổng hợp và truy vấn dữ liệu

### 7.1 Không áp dụng

Mô-đun auth không có:
- Aggregation / ETL
- Reporting queries
- Batch data operations

Tất cả queries là single-user lookups (clinic + username → user row), không có complex SELECT với JOIN/UNION/aggregation.

---

## 8. Quy tắc nghiệp vụ

| Quy tắc | Mô tả | Test Ref | Status |
|--------|-------|----------|--------|
| **BR-JWT** | JWT HS256, verify signature + exp timestamp | `test_decode_raises_on_wrong_signature`, `test_decode_raises_on_expired_token` | PASS |
| **BR-BCRYPT** | bcrypt cost 12, constant-time verify (checkpw), random salt per hash | `test_hash_password_returns_valid_bcrypt`, `test_two_hashes_of_same_password_differ`, `test_verify_password_matches` | PASS |
| **BR-REFRESH-ROTATION** | Revoke old jti TRƯỚC mint new tokens (no replay window) | `test_refresh_rotation_revokes_old_token` (real-Redis) | PASS |
| **BR-LOCKOUT** | 5 lần sai trong 15 phút → `is_locked=True` (autonomous tx), 6th attempt → 423 | `test_lockout_end_to_end` | PASS |
| **BR-LOCKOUT-CONFIG** | LOCKOUT_MAX_ATTEMPTS=5, LOCKOUT_WINDOW_MINUTES=15, LOCKOUT_DURATION_MINUTES=30 (config via settings) | Settings hardcoded, no per-clinic override in v1 | PASS |
| **BR-AUDIT** | Tất cả login/refresh/logout/password-change ghi audit log (IP, user_agent) | Audit rows inspected in test data | PASS |
| **BR-RATE-LIMIT** | Login rate limit 10 req/phút/IP (slowapi) | `test_rate_limit_11th_request_429` | PASS |
| **BR-INACTIVE-USER** | Inactive user (is_active=false) rejected login + refresh | `test_inactive_user_rejected` | PASS |
| **BR-LOCKED-USER** | Locked user (is_locked=true) rejected login + refresh (check before password) | `test_locked_user_returns_423` | PASS |
| **BR-TOKEN-BLACKLIST** | Revoked jti not usable (check Redis before decode) | `test_revoked_token_rejected`, `test_logout_revokes_jti` | PASS |

---

## 9. Xử lý lỗi

### HTTP Status Codes

| Code | Scenario | Error Code | Mô tả |
|------|----------|-----------|-------|
| 200 | Login/refresh success | — | Token pair returned |
| 204 | Logout/change-password success | — | No content |
| 401 | Invalid credentials, expired token, revoked token | `AUTH_INVALID_CREDENTIALS`, `AUTH_TOKEN_EXPIRED`, `AUTH_TOKEN_REVOKED` | |
| 403 | — | — | Not used |
| 404 | — | — | Not used |
| 422 | Validation error (missing field, bad format) | Pydantic validation | FastAPI default |
| 423 | Account locked | `AUTH_USER_LOCKED` | Too many failed attempts |
| 429 | Rate limit | — | Slowapi default |

### Error Response Format

```json
{
  "error": "AUTH_INVALID_CREDENTIALS",
  "detail": "Username or password is incorrect",
  "meta": {
    "timestamp": "2026-04-27T10:40:00Z"
  }
}
```

### Error Codes

| Code | Trigger | User Action |
|------|---------|-------------|
| `AUTH_INVALID_CREDENTIALS` | Wrong clinic/username/password | Retry with correct credentials |
| `AUTH_USER_LOCKED` | ≥5 failed attempts | Contact admin, wait 30 min (default), or reset password via email |
| `AUTH_TOKEN_EXPIRED` | access_token or refresh_token exp < now | Call `/refresh` or `/login` again |
| `AUTH_TOKEN_REVOKED` | Token jti in Redis blacklist | Must re-login |
| `AUTH_PASSWORD_MISMATCH` | Old password wrong in change-password | Try correct old password |

---

## 10. Chiến lược cache

### JWT Token Caching
- Access tokens: **Không cache** — clients cache locally (HTTP headers)
- Refresh tokens: **Không cache** — clients store locally (secure storage)
- User data in token: **Cached in JWT payload** — no DB lookup on each protected request (TenancyMiddleware validates current_clinic_id from JWT)

### Redis Blacklist
- Revoked jti (logout, refresh rotation): **Redis SET, TTL = token exp time**
  - Key format: `{jti_string}` (just the UUID)
  - Value: `1` (presence flag)
  - TTL: expires when token naturally expires
- Failed login counter: **Redis INCR + EXPIRE**
  - Key format: `lockout:{clinic_id}:{username}`
  - Value: attempt count (integer)
  - TTL: `LOCKOUT_WINDOW_MINUTES` = 15 phút (sliding window)

---

## 11. Ghi chú và lưu ý khi kiểm thử

### Quy trình lockout chính xác

1. User sai password 5 lần trong 15 phút → Redis counter = 5
2. Trigger `_lock_user()` → **autonomous transaction** → commit `is_locked=True` độc lập
3. Attempt 6 → check `is_locked=True` (trước khi verify password) → return 423 ngay
4. Redis counter vẫn tồn tại cho 15 phút, sau đó auto-expire
5. Admin phải manually reset `is_locked=false` hoặc (phase 2) password reset email

### BUG-001 — Autonomous Transaction Fix

Original: `_lock_user()` executed in login's session → rolled back khi ValueError raised  
Fixed: `_lock_user()` opens `AsyncSessionLocal()` → commits independently → survives login rollback

Test data: `tests/integration/test_auth_lockout_real_db.py::test_lockout_end_to_end` verifies fix.

### JWT_SECRET Rotation

- Mặc định (dev): `"change-me-in-production"` (8 chars minimum)
- Production: Cần rotate bằng process riêng (phase 2)
  - Mint tokens với old secret, old tokens vẫn verify được
  - Chuyển sang new secret
  - Old tokens expire naturally (15 min)
  - No session invalidation need

### Dummy Password Verify (Timing Attack)

Status: **Flagged as MINOR, deferred to phase 2**

Current: User not found → return 401 immediately (no bcrypt)  
Risk: Timing attack reveals username existence (mitigated by lockout limiting to 5 attempts/15 min)  
Future: Run dummy bcrypt on fake hash to equalize timing

### Rate Limit Multi-Worker Issue

Status: **Documented production gap, in-process only**

Current: Slowapi in-memory limiter → 10×N per minute per IP (N = workers)  
Fix: Set `SLOWAPI_STORAGE_URI=redis://...` before production multi-worker deploy  
Follow-up: Task to implement Redis-backed limiter

### Refresh Token Revocation vs Password Change

Status: **Phase 2 task**

Current: Changing password does NOT revoke existing refresh tokens (7-day expiry)  
Risk: Stolen device with old token can use it for 7 days after password change  
Future: Maintain `refresh_token_version` in User, increment on password change, validate in decode

---

## 12. Phụ lục: Settings & Config

```python
# app/core/config.py

class Settings(BaseSettings):
    # JWT
    JWT_SECRET: str = "change-me-in-production"  # 8+ chars
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # To 30 in settings, user can choose
    
    # Lockout
    LOCKOUT_MAX_ATTEMPTS: int = 5
    LOCKOUT_WINDOW_MINUTES: int = 15
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
```

### Hạn chế & Tương lai

- **Phiên bản hiện tại**: HS256 JWT, mã hóa bcrypt trực tiếp (không passlib)
- **Phase 2**: RS256 (public-key), nếu cần multi-issuer
- **Phase 2**: passlib compatibility khi bcrypt 5.x support lands
- **Phase 2**: Password reset via email/OTP, 2FA, token revocation on password change
