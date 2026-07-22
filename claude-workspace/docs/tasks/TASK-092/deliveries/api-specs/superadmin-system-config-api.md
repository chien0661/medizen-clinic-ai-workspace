# API Specification: Super Admin System Config

**Dự án:** Clinic CMS
**Task:** TASK-092
**Ngày:** 2026-07-22
**Base URL:** `/api/v1`

---

## Tổng quan

Tập hợp API cho quản lý cấu hình hệ thống toàn nền tảng. Tất cả endpoint đều yêu cầu:
- **Xác thực:** Bearer token (JWT)
- **Quyền:** `require_superuser: true` (JWT claim `is_superuser === true`)
- **Tenancy:** Non-tenant (global config, không RLS)

---

## 1. GET /superadmin/system-config

**Mục đích:** Lấy toàn bộ cấu hình hệ thống (tất cả 4 section)

### Request

```
GET /api/v1/superadmin/system-config
Authorization: Bearer {token}
```

### Parameters

Không có query/path parameters.

### Response — 200 OK

```json
{
  "feature_defaults": {
    "appointments": true,
    "pharmacy": true,
    "billing": true,
    "reports": true,
    "hr": true,
    "bhyt": false
  },
  "security_policy": {
    "password_min_length": 8,
    "require_uppercase": true,
    "require_lowercase": true,
    "require_digit": true,
    "require_special": false,
    "password_history_count": 5,
    "password_expiry_days": 0,
    "lockout_max_attempts": 5,
    "lockout_window_minutes": 15,
    "lockout_duration_minutes": 30,
    "access_token_expire_minutes": 15,
    "refresh_token_expire_days": 7,
    "idle_timeout_minutes": 0,
    "mfa_requirement": "optional",
    "sod_enforcement": false,
    "password_reset_ttl_minutes": 30,
    "email_otp_ttl_minutes": 5,
    "email_otp_max_attempts": 5
  },
  "email": {
    "email_provider": "console",
    "email_from": "no-reply@medizen.local",
    "email_from_name": "MediZen",
    "smtp_host": "",
    "smtp_port": null,
    "smtp_user": "",
    "smtp_password_is_set": false,
    "smtp_use_tls": true,
    "enable_email_notifications": true,
    "slack_webhook_url": "",
    "pagerduty_routing_key": ""
  },
  "system_info": {
    "system_name": "MediZen",
    "default_logo": "",
    "support_email": "",
    "support_phone": "",
    "default_locale": "vi",
    "default_timezone": "Asia/Ho_Chi_Minh",
    "currency": "VND",
    "date_format": "DD/MM/YYYY",
    "frontend_base_url": "http://localhost:1420",
    "maintenance_mode": false,
    "maintenance_message": "",
    "maintenance_allowed_ips": [],
    "audit_retention_days": 0,
    "environment": "dev",
    "app_version": "1.0.0"
  }
}
```

### Response — 401 Unauthorized

```json
{
  "detail": "Yêu cầu xác thực để truy cập tài nguyên này"
}
```

### Response — 403 Forbidden

```json
{
  "detail": "Not authenticated as superuser"
}
```

---

## 2. GET /superadmin/system-config/{section}

**Mục đích:** Lấy cấu hình theo 1 section (không fetch toàn bộ)

### Request

```
GET /api/v1/superadmin/system-config/{section}
Authorization: Bearer {token}
```

### Parameters

| Tên | Loại | Bắt buộc | Vị trí | Mô tả |
|-----|------|---------|--------|--------|
| `section` | String | Có | Path | Section name: `feature_defaults`, `security_policy`, `email`, `system_info` |

### Response — 200 OK (Example: section = email)

```json
{
  "email_provider": "console",
  "email_from": "no-reply@medizen.local",
  "email_from_name": "MediZen",
  "smtp_host": "",
  "smtp_port": null,
  "smtp_user": "",
  "smtp_password_is_set": false,
  "smtp_use_tls": true,
  "enable_email_notifications": true,
  "slack_webhook_url": "",
  "pagerduty_routing_key": ""
}
```

### Response — 404 Not Found

```json
{
  "detail": "Unknown section: invalid_section"
}
```

### Response — 401 Unauthorized

```json
{
  "detail": "Yêu cầu xác thực để truy cập tài nguyên này"
}
```

### Response — 403 Forbidden

```json
{
  "detail": "Not authenticated as superuser"
}
```

---

## 3. PUT /superadmin/system-config/{section}

**Mục đích:** Cập nhật cấu hình của 1 section (partial update, merge)

### Request

```
PUT /api/v1/superadmin/system-config/{section}
Authorization: Bearer {token}
Content-Type: application/json
```

### Parameters

| Tên | Loại | Bắt buộc | Vị trí | Mô tả |
|-----|------|---------|--------|--------|
| `section` | String | Có | Path | Section name: `feature_defaults`, `security_policy`, `email`, `system_info` |

### Request Body — Example 1: Update feature_defaults

```json
{
  "appointments": true,
  "pharmacy": true,
  "billing": true,
  "reports": true,
  "hr": false,
  "bhyt": false
}
```

### Request Body — Example 2: Update email (set new password)

```json
{
  "email_provider": "smtp",
  "email_from": "noreply@clinic.com",
  "email_from_name": "My Clinic",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "clinic@gmail.com",
  "smtp_password": "SecurePassword123!",
  "smtp_use_tls": true,
  "enable_email_notifications": true,
  "slack_webhook_url": "https://hooks.slack.com/services/...",
  "pagerduty_routing_key": ""
}
```

### Request Body — Example 3: Update email (keep old password)

```json
{
  "email_provider": "smtp",
  "email_from": "noreply@clinic.com",
  "email_from_name": "My Clinic",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "clinic@gmail.com",
  "smtp_use_tls": true,
  "enable_email_notifications": true,
  "slack_webhook_url": "",
  "pagerduty_routing_key": ""
}
```

*(Lưu ý: Không chứa `smtp_password` → BE giữ nguyên giá trị cũ)*

### Request Body — Example 4: Update security_policy

```json
{
  "password_min_length": 10,
  "require_uppercase": true,
  "require_lowercase": true,
  "require_digit": true,
  "require_special": true,
  "password_history_count": 8,
  "password_expiry_days": 30,
  "lockout_max_attempts": 3,
  "lockout_window_minutes": 10,
  "lockout_duration_minutes": 60,
  "access_token_expire_minutes": 30,
  "refresh_token_expire_days": 14,
  "idle_timeout_minutes": 30,
  "mfa_requirement": "required",
  "sod_enforcement": true,
  "password_reset_ttl_minutes": 60,
  "email_otp_ttl_minutes": 10,
  "email_otp_max_attempts": 3
}
```

### Request Body — Example 5: Update system_info

```json
{
  "system_name": "Clinic Plus",
  "default_logo": "https://cdn.example.com/logo.png",
  "support_email": "support@clinic.com",
  "support_phone": "+84-28-1234-5678",
  "default_locale": "vi",
  "default_timezone": "Asia/Ho_Chi_Minh",
  "currency": "VND",
  "date_format": "DD/MM/YYYY",
  "frontend_base_url": "https://clinic.example.com",
  "maintenance_mode": false,
  "maintenance_message": "",
  "maintenance_allowed_ips": ["203.0.113.0", "198.51.100.0"],
  "audit_retention_days": 365
}
```

### Response — 200 OK

**Example: Successful update of email section**

```json
{
  "email_provider": "smtp",
  "email_from": "noreply@clinic.com",
  "email_from_name": "My Clinic",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "clinic@gmail.com",
  "smtp_password_is_set": true,
  "smtp_use_tls": true,
  "enable_email_notifications": true,
  "slack_webhook_url": "https://hooks.slack.com/services/...",
  "pagerduty_routing_key": ""
}
```

### Response — 400 Bad Request

```json
{
  "detail": "Yêu cầu không hợp lệ: [chi tiết lỗi]"
}
```

### Response — 401 Unauthorized

```json
{
  "detail": "Yêu cầu xác thực để truy cập tài nguyên này"
}
```

### Response — 403 Forbidden

```json
{
  "detail": "Not authenticated as superuser"
}
```

### Response — 404 Not Found

```json
{
  "detail": "Unknown section: invalid_section"
}
```

### Response — 422 Unprocessable Entity (Validation Error)

```json
{
  "detail": "Validation failed: password_min_length must be >= 1"
}
```

**Các validation error phổ biến:**

| Field | Validation | Error Message |
|-------|-----------|---------------|
| `password_min_length` | >= 1 | "password_min_length must be >= 1" |
| `lockout_max_attempts` | >= 1 | "lockout_max_attempts must be >= 1" |
| `smtp_port` | 1 <= port <= 65535 | "smtp_port must be between 1 and 65535" |
| `mfa_requirement` | in ["off", "optional", "required"] | "mfa_requirement must be one of: off, optional, required" |
| `default_locale` | in ["vi", "en"] | "default_locale must be one of: vi, en" |
| `email_provider` (if smtp) | smtp_host != empty | "smtp_host is required when email_provider is smtp" |
| `email_provider` (if smtp) | smtp_port != empty | "smtp_port is required when email_provider is smtp" |

### Response — 500 Internal Server Error

```json
{
  "detail": "Lỗi hệ thống, vui lòng thử lại sau"
}
```

---

## Field Specifications by Section

### section = feature_defaults

All fields are **Boolean** (true/false), optional.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `appointments` | Boolean | true | Appointment scheduling feature |
| `pharmacy` | Boolean | true | Pharmacy management feature |
| `billing` | Boolean | true | Billing/invoicing feature |
| `reports` | Boolean | true | Reports/analytics feature |
| `hr` | Boolean | true | HR management feature |
| `bhyt` | Boolean | false | BHYT insurance integration |

### section = security_policy

| Field | Type | Default | Validation | Notes |
|-------|------|---------|-----------|-------|
| `password_min_length` | Integer | 8 | >= 1 | Minimum characters |
| `require_uppercase` | Boolean | true | — | Require A-Z |
| `require_lowercase` | Boolean | true | — | Require a-z |
| `require_digit` | Boolean | true | — | Require 0-9 |
| `require_special` | Boolean | false | — | Require !@#$%^&* |
| `password_history_count` | Integer | 5 | >= 1 | Keep N passwords |
| `password_expiry_days` | Integer | 0 | >= 0 | 0 = no expiry |
| `lockout_max_attempts` | Integer | 5 | >= 1 | Max login attempts |
| `lockout_window_minutes` | Integer | 15 | >= 1 | Failed attempt window |
| `lockout_duration_minutes` | Integer | 30 | >= 1 | Account lockout duration |
| `access_token_expire_minutes` | Integer | 15 | >= 1 | JWT access token TTL |
| `refresh_token_expire_days` | Integer | 7 | >= 1 | JWT refresh token TTL |
| `idle_timeout_minutes` | Integer | 0 | >= 0 | 0 = no timeout |
| `mfa_requirement` | Enum | optional | ["off", "optional", "required"] | MFA enforcement level |
| `sod_enforcement` | Boolean | false | — | Separation of duties |
| `password_reset_ttl_minutes` | Integer | 30 | >= 1 | Password reset link expiry |
| `email_otp_ttl_minutes` | Integer | 5 | >= 1 | Email OTP expiry |
| `email_otp_max_attempts` | Integer | 5 | >= 1 | Max OTP entry attempts |

### section = email

| Field | Type | Default | Validation | Notes |
|-------|------|---------|-----------|-------|
| `email_provider` | Enum | console | ["console", "noop", "smtp"] | Email provider |
| `email_from` | String | no-reply@medizen.local | Valid email | From address |
| `email_from_name` | String | MediZen | — | Display name |
| `smtp_host` | String | "" | Required if provider=smtp | SMTP server |
| `smtp_port` | Integer | null | 1-65535 if provider=smtp | SMTP port |
| `smtp_user` | String | "" | Required if provider=smtp | SMTP username |
| `smtp_password` | String | "" | Required if provider=smtp | SMTP password (write-only) |
| `smtp_use_tls` | Boolean | true | — | Use TLS |
| `enable_email_notifications` | Boolean | true | — | Enable email notifications |
| `slack_webhook_url` | String | "" | Valid URL if set | Slack webhook (optional) |
| `pagerduty_routing_key` | String | "" | — | PagerDuty routing key (optional) |

**Special handling for `smtp_password`:**
- **In GET response**: Replaced with `smtp_password_is_set: boolean` flag (never return plaintext)
- **In PUT request**: If not included → preserve old value; if included → update with new value
- **In audit log**: Never logged (excluded from audit table)

### section = system_info

| Field | Type | Default | Validation | Notes |
|-------|------|---------|-----------|-------|
| `system_name` | String | MediZen | — | Platform name |
| `default_logo` | String | "" | Valid URL if set | Logo URL |
| `support_email` | String | "" | Valid email if set | Support email |
| `support_phone` | String | "" | — | Support phone |
| `default_locale` | String | vi | ["vi", "en"] | Default language |
| `default_timezone` | String | Asia/Ho_Chi_Minh | Valid IANA timezone | Timezone |
| `currency` | String | VND | Valid ISO 4217 code | Currency code |
| `date_format` | String | DD/MM/YYYY | — | Date format |
| `frontend_base_url` | String | http://localhost:1420 | Valid URL | FE base URL |
| `maintenance_mode` | Boolean | false | — | Maintenance mode flag (stored-only) |
| `maintenance_message` | String | "" | — | Maintenance message |
| `maintenance_allowed_ips` | Array<String> | [] | Valid IP addresses | Whitelisted IPs |
| `audit_retention_days` | Integer | 0 | >= 0 | 0 = unlimited |
| `environment` | String | dev | — | **READ-ONLY** (from env var) |
| `app_version` | String | 1.0.0 | — | **READ-ONLY** (from build) |

**Read-only fields:**
- `environment` and `app_version` are always returned from server config, any value in PUT request is ignored
- FE should render these as disabled/non-editable inputs

---

## Behavior Notes

### Partial Update (Merge Semantics)

PUT request can omit any field. Fields not included in the request body **retain their current values**.

**Example:**
- Current email config: `{email_from: "old@example.com", smtp_host: "smtp.old.com", ...}`
- PUT body: `{email_from: "new@example.com"}` (no other fields)
- Result: `{email_from: "new@example.com", smtp_host: "smtp.old.com", ...}` (smtp_host unchanged)

### SMTP Password Handling

1. **GET response** always replaces `smtp_password` with `smtp_password_is_set: boolean`
2. **PUT request** omitting `smtp_password` field → server preserves existing password
3. **PUT request** including `smtp_password: "value"` → server updates to new password
4. Plaintext password **never returned** in any GET response or audit log

### Audit Logging

- All successful PUT operations are logged with action=`UPDATE_SYSTEM_CONFIG`, section=`{section}`
- `smtp_password` field is **excluded** from audit log to prevent plaintext secret exposure
- Audit log includes timestamp, superuser ID, section name, and summary of changes (field names, not values)

---

## Authentication & Authorization

All endpoints require:

1. **Valid JWT token** in `Authorization: Bearer {token}` header
   - Token must not be expired
   - Issuer must be recognized by backend
   - If invalid or expired → 401 Unauthorized

2. **Superuser claim** in JWT payload
   - JWT must include `is_superuser: true` claim
   - If claim is false or missing → 403 Forbidden
   - If user role is changed after token issued → old token still valid until expiry (consider shortening TTL)

---

## Caching & Invalidation

- **No client-side cache** recommended for system config (changed infrequently, but critical)
- **Server may cache** config in memory for 5-10 minutes to reduce database queries
- **Cache invalidation** happens immediately after successful PUT operation
- For strict consistency, client should call GET immediately after PUT to confirm persistence

---

## Rate Limiting (Optional, Phase 2+)

*(Not yet implemented; consider for future security hardening)*

- GET endpoints: 100 requests/minute per user
- PUT endpoints: 10 requests/minute per user
- Exceeding limit → 429 Too Many Requests

---

## Version History

| Phiên bản | Ngày | Thay đổi |
|-----------|------|---------|
| 1.0 | 2026-07-22 | Initial API spec — TASK-092 |

---

## Contact & Support

For API issues, contact: engineering@vissoft.vn
