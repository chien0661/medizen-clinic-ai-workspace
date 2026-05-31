---
id: TASK-038-B8-B14
type: functional-design
title: MFA (TOTP) + Login Fingerprint Functional Design
version: 1.0
status: DONE
date: 2026-05-01
scope: NFR-029 (Login Anomaly Detection), NFR-035 (MFA/2FA Enforcement)
---

# MFA (TOTP) + Login Fingerprint — Functional Design

**Task scope**: TASK-038 sub-tasks B.8 → B.14  
**Status**: ✅ DONE  
**Date completed**: 2026-05-01

---

## Mục đích

Thực hiện hai yêu cầu bảo mật không chức năng (NFR) trong TASK-038:

1. **NFR-029**: Phát hiện login bất thường khi IP/device/geo mới → yêu cầu xác minh danh tính (2FA/email OTP)
2. **NFR-035**: Bắt buộc kích hoạt MFA (TOTP + backup codes) để nâng cao bảo mật tài khoản người dùng

---

## Phạm vi (B.8 → B.14)

### **B.8**: Thêm cột MFA vào bảng `user`

Migration: `0021_add_mfa_columns_to_user`

```sql
ALTER TABLE "user" ADD COLUMN mfa_secret VARCHAR(255) NULL;
ALTER TABLE "user" ADD COLUMN mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE "user" ADD COLUMN backup_codes TEXT[] NULL;
```

- `mfa_secret`: Base32-encoded TOTP secret (32 ký tự = 160 bits entropy, RFC 6238)
- `mfa_enabled`: Cờ MFA đã kích hoạt
- `backup_codes`: Danh sách backup codes đã hash (bcrypt cost=12)

### **B.9**: Tạo bảng `login_fingerprint`

Migration: `0022_create_login_fingerprint`

```sql
CREATE TABLE login_fingerprint (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user" (id) ON DELETE CASCADE,
    ip VARCHAR(45) NOT NULL,  -- IPv6-safe
    device_hash VARCHAR(64) NOT NULL,  -- SHA-256(user_agent|screen|timezone)
    geo_country VARCHAR(2) NULL,  -- ISO 3166-1 alpha-2 (optional)
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    seen_count INT NOT NULL DEFAULT 1,
    
    UNIQUE (user_id, ip, device_hash)
);

CREATE INDEX ix_login_fingerprint_user_last_seen 
ON login_fingerprint (user_id, last_seen_at DESC);
```

Fingerprints được xem là "bình thường" nếu (user_id, ip, device_hash) xuất hiện trong vòng 30 ngày gần nhất.

### **B.10**: Dịch vụ TOTP và backup codes

File: `app/modules/auth/services/mfa_service.py`

**Chức năng**:
- `enroll(user_id)` → sinh TOTP secret → trả `{secret, qr_uri}` (chưa kích hoạt)
- `verify(user_id, otp, activate=False)` → xác minh 6-digit OTP (TOTP ±30s)
  - Nếu `activate=True` → set `user.mfa_enabled = true`
  - Nếu OTP không hợp lệ → raise `ValueError("invalid_otp")`
- `generate_backup_codes(user_id)` → sinh 10 codes (36-char alphabet, 10 chars)
  - Lưu bcrypt-hashed vào `user.backup_codes`
  - Trả plaintext đúng **1 lần duy nhất**
- `consume_backup_code(user_id, code)` → kiểm tra hash + xóa từ list
- `disable(user_id)` → xóa secret + backup codes, set `mfa_enabled = false`

**Bảo mật**:
- OTP `valid_window=1` (±30s) → phòng chống clock drift
- Backup codes: bcrypt cost=12, không bao giờ lưu plaintext
- TOTP secret: hiện lưu plaintext (TASK-037 sẽ mã hóa cột)

### **B.11**: 6 endpoint MFA

| HTTP | Path | Auth | Mô tả |
|------|------|------|-------|
| `POST` | `/api/v1/auth/mfa/enroll` | access token | Bắt đầu enrollment; trả `{secret, qr_uri}` |
| `POST` | `/api/v1/auth/mfa/verify` | access token | Xác minh OTP; kích hoạt nếu lần đầu |
| `POST` | `/api/v1/auth/mfa/disable` | access + password | Tắt MFA (yêu cầu re-auth password) |
| `POST` | `/api/v1/auth/mfa/backup-codes/regenerate` | access + password | Sinh 10 codes mới; trả plaintext 1 lần |
| `POST` | `/api/v1/auth/mfa/challenge` | mfa_token (5-min JWT) | Hoàn tất bước 2 login với OTP hoặc backup code |
| `GET` | `/api/v1/auth/fingerprints` | access token | Danh sách 20 fingerprints gần nhất |

### **B.12**: Hai bước login với MFA

**Luồng login khi `user.mfa_enabled = true`**:

```
1. POST /auth/login (username + password)
   ↓
   [Kiểm tra lockout, xác minh password, kiểm tra anomaly]
   ↓
   Trả: {
     "mfa_required": true,
     "mfa_token": "<JWT type=mfa_challenge exp=5min>",
     "clinic_code": "...",
     "user": {...}  // chỉ basic info, NOT access token
   }
   ↓
2. POST /auth/mfa/challenge (mfa_token + otp_code)
   ↓
   [Xác minh OTP, ghi fingerprint]
   ↓
   Trả: {
     "access_token": "...",
     "refresh_token": "...",
     "user": {...}
   }
```

**mfa_token JWT**:
- `type = "mfa_challenge"`
- `exp = now + 5 min`
- Chứa `sub` (user_id), `clinic_id`, `jti`, `iat`, `exp`
- **Không thể** dùng thay access token (check type khi xác minh)

### **B.13**: Phát hiện bất thường IP/device/geo

**Trigger anomaly**:
1. Sau khi xác minh password thành công → tính `device_hash = SHA-256(user_agent|extras)`
2. Kiểm tra bảng `login_fingerprint`: có record nào `(user_id, ip, device_hash)` trong 30 ngày không?
3. **Nếu không → anomaly detected**:
   - **User có MFA**: return `mfa_required: true` (bắt buộc OTP ở bước 2)
   - **User không MFA**: return `requires_mfa_challenge: true` + full tokens (FE hiển thị "xác minh danh tính", deferred email OTP)
4. Ghi fingerprint mới hoặc update `last_seen_at + seen_count++` nếu đã biết

**Device extras** (FE tính toán):
```javascript
device_extras = `${window.innerWidth}|${Intl.DateTimeFormat().resolvedOptions().timeZone}`
```

### **B.14**: FE — Trang MFA + Security tab

**MfaEnrollPage** (`/auth/mfa/enroll`):
- POST `/api/v1/auth/mfa/enroll` → QR code (từ `qr_uri`)
- Copy secret button (2s feedback)
- Input 6-digit OTP
- POST `/api/v1/auth/mfa/verify` → activate
- Redirect → `/profile?tab=security&mfaEnabled=true`

**MfaVerifyPage** (`/auth/mfa/verify`):
- Input OTP 6-digit HOẶC backup code
- POST `/api/v1/auth/mfa/challenge` → tokens
- Redirect → `/dashboard`
- Error: "Mã OTP hết hạn", "OTP không hợp lệ", "Backup code không hợp lệ"

**SecurityTab** (profile):
- Badge "Enabled" / "Disabled" (từ `authStore.user.mfa_enabled`)
- Button "Enable MFA" → navigate to enroll
- Button "Disable MFA" + password confirm
- Button "Regenerate backup codes" → show plaintext 1 lần + "Tôi đã lưu" checkbox
- List 20 fingerprints gần nhất:
  ```
  192.168.1.1 • Mac Safari • 2 giờ trước
  ```

**ProfilePage**:
- Multi-tab: "Thông tin", "Bảo mật", ...
- SecurityTab wired from `authStore.user.mfa_enabled`

---

## Schema changes

### Migration `0021_add_mfa_columns_to_user`

```python
def upgrade():
    op.add_column('user',
        sa.Column('mfa_secret', sa.VARCHAR(255), nullable=True))
    op.add_column('user',
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='FALSE'))
    op.add_column('user',
        sa.Column('backup_codes', sa.ARRAY(sa.Text()), nullable=True))

def downgrade():
    op.drop_column('user', 'backup_codes')
    op.drop_column('user', 'mfa_enabled')
    op.drop_column('user', 'mfa_secret')
```

**Down-revision chain**: `65fc9ae59ba5 → 0021 → 0022`

### Migration `0022_create_login_fingerprint`

```python
def upgrade():
    op.create_table('login_fingerprint',
        sa.Column('id', sa.UUID(), default=gen_random_uuid(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('ip', sa.VARCHAR(45), nullable=False),
        sa.Column('device_hash', sa.VARCHAR(64), nullable=False),
        sa.Column('geo_country', sa.VARCHAR(2), nullable=True),
        sa.Column('last_seen_at', sa.TIMESTAMPTZ(), server_default=CURRENT_TIMESTAMP, nullable=False),
        sa.Column('seen_count', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'ip', 'device_hash', name='uq_fingerprint')
    )
    op.create_index('ix_login_fingerprint_user_last_seen',
        'login_fingerprint', ['user_id', 'last_seen_at'])
```

---

## API Contract

### `POST /api/v1/auth/mfa/enroll`

**Request**: `{ }`  
**Response (200)**:
```json
{
  "secret": "JBSWY3DPEBLW64TMMQ3D2IBMGU======",
  "qr_uri": "otpauth://totp/MediZen:user@example.com?secret=...&issuer=MediZen"
}
```

### `POST /api/v1/auth/mfa/verify`

**Request**:
```json
{
  "otp_code": "123456",
  "activate": true
}
```

**Response (200)**:
```json
{
  "mfa_enabled": true
}
```

**Error (400)**:
```json
{
  "error": "invalid_otp",
  "message": "Mã OTP không hợp lệ"
}
```

### `POST /api/v1/auth/mfa/disable`

**Request**:
```json
{
  "password": "current_password"
}
```

**Response (200)**:
```json
{
  "mfa_enabled": false
}
```

### `POST /api/v1/auth/mfa/backup-codes/regenerate`

**Request**:
```json
{
  "password": "current_password"
}
```

**Response (200)**:
```json
{
  "codes": ["ABC123DEF456", "XYZ789PQR012", ...]
}
```

**Note**: Plaintext trả duy nhất 1 lần. Lần sau API này call lại, chỉ trả `{codes: []}` (hoặc error nếu chính sách).

### `POST /api/v1/auth/mfa/challenge`

**Request**:
```json
{
  "otp_code": "123456",  // hoặc null nếu dùng backup code
  "backup_code": "ABC123DEF456"  // hoặc null nếu dùng OTP
}
```

**Response (200)**:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "user": {
    "id": "...",
    "username": "...",
    "mfa_enabled": true,
    ...
  }
}
```

**Error (401)**:
```json
{
  "error": "invalid_otp",
  "message": "Mã OTP không hợp lệ hoặc hết hạn"
}
```

### `GET /api/v1/auth/fingerprints`

**Query**: `?limit=20`  
**Response (200)**:
```json
{
  "fingerprints": [
    {
      "ip": "192.168.1.1",
      "device_hash": "abc123...",
      "geo_country": "VN",
      "last_seen_at": "2026-05-01T10:30:00Z",
      "seen_count": 5
    },
    ...
  ]
}
```

### `POST /auth/login` — Giải đáp MFA

**Request**: (không thay đổi)
```json
{
  "username": "user@example.com",
  "password": "...",
  "clinic_code": "..."
}
```

**Response khi MFA enabled (200)**:
```json
{
  "mfa_required": true,
  "mfa_token": "<JWT exp=5min type=mfa_challenge>",
  "clinic_code": "...",
  "user": {
    "id": "...",
    "username": "...",
    "mfa_enabled": true
  }
}
```

**Response khi login bình thường (200)**:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "clinic_code": "...",
  "user": {..., "mfa_enabled": false}
}
```

**Response khi anomaly (không MFA) (200)**:
```json
{
  "requires_mfa_challenge": true,  // Cờ cho FE
  "access_token": "...",  // Full tokens tạm
  "refresh_token": "...",
  "clinic_code": "...",
  "user": {..., "mfa_enabled": false}
}
```

---

## Hai bước login — Sơ đồ luồng

```
┌─────────────────────────────────────────────────────────────────┐
│ Bước 1: Xác minh mật khẩu + IP/device anomaly                  │
└─────────────────────────────────────────────────────────────────┘

  POST /auth/login (username, password)
    ↓
  ✓ Kiểm tra lockout
    ↓
  ✓ Xác minh mật khẩu
    ↓
  ✓ Tính device_hash = SHA-256(user_agent | screen | timezone)
    ↓
  ✓ Kiểm tra bảng login_fingerprint (30 ngày)
    ├─ Nếu tìm thấy (user_id, ip, device_hash): is_anomalous = false
    └─ Nếu không tìm: is_anomalous = true
    ↓
  ✓ Ghi/update fingerprint → upsert atomic via ON CONFLICT
    ↓
  [DECISION: MFA required?]
    ├─ user.mfa_enabled=true → bắt buộc OTP
    └─ is_anomalous=true && no MFA → cảnh báo (deferred email)
    ↓
  Trả {mfa_required: true/false, mfa_token, requires_mfa_challenge}

┌─────────────────────────────────────────────────────────────────┐
│ Bước 2: Xác minh OTP (nếu MFA required)                         │
└─────────────────────────────────────────────────────────────────┘

  POST /auth/mfa/challenge (mfa_token, otp_code)
    ↓
  ✓ Xác minh mfa_token type="mfa_challenge" + not expired
    ↓
  ✓ Xác minh OTP hoặc backup code
    ↓
  ✓ Ghi audit + update last_login_at
    ↓
  Trả {access_token, refresh_token, user}
```

---

## Fix-mode patches (sau Code Review)

**Date**: 2026-05-01  
**Mode**: CHANGES_REQUESTED (2 blockers + 1 recommend)

### Fix 1: Lockout integration vào MFA challenge

**File**: `app/modules/auth/services/auth_service.py`

`complete_mfa_challenge()` bây giờ call:
- `record_failed_attempt(clinic_id, username)` khi OTP sai
- `clear_failed_attempts(clinic_id, username)` khi OTP đúng
- Audit log mỗi lần

**Benefit**: Tránh hammer-attack OTP mà không trigger lockout.

### Fix 2: mfaEnabled từ authStore

**File**: `src/pages/profile/ProfilePage.tsx`

Thay thế `useState(false) // TODO` bằng:
```typescript
const mfaEnabled = useAuthStore(s => s.user?.mfa_enabled ?? false);
```

**Benefit**: Badge hiển thị state thực từ server, không hardcoded false.

### Fix 3: Thêm test — enabled badge

**File**: `src/tests/auth/SecurityTab.test.tsx`

Thêm test xác minh: khi `mfaEnabled=true` (từ store), badge hiển thị "Enabled".

---

## Test coverage

### Backend

- **Unit**: 24 tests (TOTP, backup codes, device_hash, fingerprint)
  - `test_mfa_service.py`: enroll, verify, generate, consume, disable, round-trip
  - `test_fingerprint_service.py`: check_and_upsert, list_recent, anomaly detection

- **Integration**: 10 tests (login flow + MFA challenge)
  - 5 original: login no-MFA, new fingerprint anomaly, MFA-enabled, challenge valid, challenge backup
  - 2 fix-mode: lockout integration trên failed/success OTP
  - 3 new gap tests: expired mfa_token, wrong-type token, OTP replay permissive behavior

**Total BE**: **34/34 PASS**

### Frontend

- **Unit**: 566 tests (vitest + happy-dom)
  - `MfaEnrollPage.test.tsx`: 5 tests (QR render, OTP submit, error, copy, loading)
  - `MfaVerifyPage.test.tsx`: 5 tests (OTP branch, backup branch, expired, guard)
  - `SecurityTab.test.tsx`: 9 tests (badges, toggle, disable, regenerate, fingerprints, enabled-from-store)

**Total FE**: **566/566 PASS**

---

## Migration conflict resolution

**Issue**: Ba streams (A, B, C) đều claim revision `0021` + down-revision `65fc9ae59ba5`:
- Stream A: `0021_multi_clinic_account`
- Stream B: `0021_password_history`
- Stream C (MFA): `0021_add_mfa_columns_to_user`

**Current state**: Chỉ Stream C có trong worktree. Conflict sẽ xuất hiện ở merge-time.

**Recommended resolution**:
1. Renumber thành `0021a / 0021b / 0021c` (parallel lineages)
2. HOẶC chain linearly: `0021 → 0022 → 0023` (Stream A/B/C lần lượt)
3. Adjust Stream C's `0022_create_login_fingerprint.py` → `0024` (nếu chain)

**Action**: Phải coordinate giữa 3 stream lead trước khi merge bất kỳ branch nào.

---

## Hardening backlog (deferred)

### H-1: Backup code entropy — MEDIUM

**Issue**: 10 chars từ 36-char alphabet = log₂(36¹⁰) ≈ 51.7 bits < 80-bit target.

**Mitigation**: bcrypt cost=12 + one-time use → brute-force infeasible.

**Recommend**: Bump lên 12+ chars (≈62+ bits) hoặc dùng base32 16 chars.

### H-2: OTP replay attack — LOW

**Issue**: RFC 6238 §5.2 recommend server-side "last consumed OTP step" memo.

**Current**: `pyotp.TOTP.verify(valid_window=1)` cho phép reuse trong 30s.

**Mitigation**: Attacker phải có live OTP + 30s window; lockout limits brute-force.

**Recommend**: Thêm `last_used_otp_step: int | None` column; reject nếu step ≤ last_used.

### H-3: TOTP secret plaintext — TASK-037

Deferred đến TASK-037 column-level encryption scope.

### H-4: Email OTP fallback — depends TASK-020

Anomaly detection hiện return flag `requires_mfa_challenge: true` nhưng không send email.

Cần notification service (TASK-020) → Email OTP fallback.

### H-5: GeoIP auto-detection — OUT-OF-SCOPE

`geo_country` stored as NULL trừ khi FE truyền.

MaxMind/IP-API integration deferred.

### H-6: Trusted proxy validation — X-Forwarded-For

Current: Lấy first IP từ `X-Forwarded-For` không validate trusted proxy list.

Risk: Client spoof IP → poison anomaly detection.

**Recommend**: Add trusted-proxy CIDR check hoặc rely `request.client.host` only.

---

## i18n coverage

**Namespace**: `auth.mfa.*` + `profile.security.*`

### `src/locales/vi/auth.json` — auth.mfa.*

```json
{
  "mfa": {
    "enroll_title": "Bảo mật tài khoản — Xác minh hai bước",
    "enroll_desc": "Quét mã QR bằng ứng dụng authenticator của bạn",
    "secret_label": "Khóa bí mật (lưu ở nơi an toàn)",
    "copy_button": "Sao chép",
    "verify_button": "Xác minh",
    "invalid_otp": "Mã OTP không hợp lệ",
    "expired_token": "Phiên MFA đã hết hạn. Vui lòng đăng nhập lại",
    "verify_page_title": "Nhập mã xác minh",
    "otp_placeholder": "123456",
    "backup_toggle": "Dùng backup code",
    "backup_placeholder": "ABC123DEF456",
    ...
  }
}
```

### `src/locales/vi/profile.json` — profile.security.*

```json
{
  "security": {
    "title": "Bảo mật",
    "mfa_status": "Xác minh hai bước",
    "mfa_enabled": "Đã bật",
    "mfa_disabled": "Chưa bật",
    "enable_button": "Bật MFA",
    "disable_button": "Tắt MFA",
    "disable_confirm": "Nhập mật khẩu để tắt MFA",
    "backup_codes_title": "Mã khôi phục",
    "regenerate_button": "Tạo mã mới",
    "saved_checkbox": "Tôi đã lưu các mã này",
    "recent_logins": "Các lần đăng nhập gần đây",
    ...
  }
}
```

Tương tự cho `src/locales/en/auth.json` + `en/profile.json`.

---

## Summary

TASK-038 B.8–B.14 (MFA + login fingerprint) hoàn tất:
- **Schema**: 2 migrations (MFA columns + fingerprint table)
- **BE Services**: mfa_service.py + fingerprint_service.py
- **API**: 6 endpoints MFA + updated `/auth/login`
- **FE**: MfaEnrollPage, MfaVerifyPage, SecurityTab, ProfilePage
- **Test**: 34/34 BE + 566/566 FE PASS
- **i18n**: `auth.mfa.*` + `profile.security.*` (vi + en)
- **Hardening**: 6 items deferred (entropy, replay, plaintext, email, GeoIP, X-Forwarded-For)

Sẵn sàng merge (sau migration conflict resolution + FE lint fix).
