# Thiết Kế Chi Tiết Tính Năng: Super Admin — Quản lý hệ thống, tài khoản & người dùng, cấu hình hệ thống

**Dự án:** Clinic CMS
**Task:** TASK-092
**Phiên bản:** 1.0
**Ngày:** 2026-07-22
**Người thực hiện:** Documentation Agent
**Trạng thái:** Đã duyệt
**Tài liệu liên quan:** TASK-092 task.md, implementation-plan.md, test-report.md, code-review.md

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-07-22 | Phiên bản đầu tiên — nâng cấp Super Admin với tái định hướng, cấu trúc 3 nhóm + màn Cấu hình hệ thống |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Cấu trúc điều hướng & nhóm chức năng](#2-cấu-trúc-điều-hướng--nhóm-chức-năng)
- [3. Route Guard & Xác thực](#3-route-guard--xác-thực)
- [4. Màn hình Cấu hình hệ thống (System Config)](#4-màn-hình-cấu-hình-hệ-thống-system-config)
- [5. Danh sách API được tiêu thụ](#5-danh-sách-api-được-tiêu-thụ)
- [6. Chi tiết API mới: Cấu hình hệ thống](#6-chi-tiết-api-mới-cấu-hình-hệ-thống)
- [7. Cấu trúc cơ sở dữ liệu](#7-cấu-trúc-cơ-sở-dữ-liệu)
- [8. Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
- [9. Xử lý lỗi](#9-xử-lý-lỗi)
- [10. Ghi chú và lưu ý khi kiểm thử](#10-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Nâng cấp và tái định hướng giao diện **Super Admin** để tập trung vào quản trị **cấp hệ thống**, tách biệt hoàn toàn khỏi các nghiệp vụ vận hành phòng khám. TASK-092 sắp xếp lại toàn bộ khu vực Super Admin quanh **4 nhóm chức năng chính**:

1. **Quản lý hệ thống** — quản trị toàn bộ phòng khám (clinics/tenants), trạng thái tenant, thông tin toàn hệ thống, thống kê và audit logs
2. **Tài khoản & Người dùng** — tài khoản đăng nhập cấp hệ thống (accounts), khóa/mở, gán phòng khám, quản lý người dùng platform-level
3. **Cấu hình hệ thống** — các cấu hình dùng chung toàn hệ thống (feature defaults, bảo mật, email/SMTP, thông tin vận hành)

Công việc kế thừa từ TASK-070 (Super Admin — quản lý toàn hệ thống: Dashboard + Clinics + Accounts + AuditLogs) và TASK-071 (Super Admin Analytics), với trọng tâm **gom, làm gọn và chuẩn hóa** trải nghiệm quanh 3 nhóm trên, cộng với màn **Cấu hình hệ thống mới**.

### 1.2 Phạm vi

**Bao gồm:**
- Tái tổ chức Sidebar Super Admin: từ danh sách phẳng 5 mục → 3 nhóm có tiêu đề (Quản lý hệ thống / Tài khoản & Người dùng / Cấu hình hệ thống)
- Gộp "Tài khoản" và "Người dùng" vào **1 màn duy nhất** (`SuperAdminAccountsPage` từ TASK-070)
- Màn **Cấu hình hệ thống mới** (`SuperAdminSystemConfigPage`, 4 tab): Feature flags mặc định, Bảo mật/Mật khẩu, Email/SMTP, Thông tin & Vận hành
- Endpoint backend mới: `GET`/`PUT /superadmin/system-config[/{section}]`
- Bảng `system_config` non-tenant, singleton (migration `0061_superadmin_system_config`)
- Cải tiến pagination: `GET /superadmin/clinics` từ "trả về toàn bộ" → server-side pagination với search, `GET /superadmin/audit-logs` sử dụng real `total` thay heuristic

**Không bao gồm:**
- i18n (siêu Admin của TASK-070/071 dùng hardcoded Vietnamese — TASK-092 giữ nhất quán)
- Enforcement của `security_policy`/`maintenance_mode` (Phase 4 sau, chỉ lưu + hiển thị)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Super Admin (End User)** | Người dùng có vai trò superadmin, quản lý toàn hệ thống. Truy cập qua JWT claim `is_superuser: true` |
| **Backend API** | `/api/v1/superadmin/*` endpoints — xác thực `is_superuser` claim, bypass RLS, tác động toàn hệ thống |
| **Auth Store** | `src/stores/authStore.ts` — lưu `isSuperuser` boolean từ JWT payload |
| **Route Guard** | `<RequireSuperuser>` component — kiểm soát quyền truy cập mọi trang `/superadmin/*` |
| **Sidebar Component** | `src/components/shell/Sidebar.tsx` — render "Super Admin" section với 3 nhóm có tiêu đề |

---

## 2. Cấu trúc điều hướng & nhóm chức năng

### 2.1 Sơ đồ Sidebar mới (3 nhóm)

```
┌─────────────────────────────────────────┐
│ QUẢN LÝ HỆ THỐNG                       │
├─────────────────────────────────────────┤
│ • Tổng quan       /superadmin           │
│ • Phòng khám      /superadmin/clinics   │
│ • Thống kê        /superadmin/analytics │
│ • Audit Logs      /superadmin/audit-logs│
│                                         │
├─────────────────────────────────────────┤
│ TÀI KHOẢN & NGƯỜI DÙNG                 │
├─────────────────────────────────────────┤
│ • Tài khoản       /superadmin/accounts  │
│                                         │
├─────────────────────────────────────────┤
│ CẤU HÌNH HỆ THỐNG                      │
├─────────────────────────────────────────┤
│ • Cấu hình hệ thống /superadmin/system-config │
└─────────────────────────────────────────┘
```

### 2.2 Mô tả từng nhóm & mục đích

| Nhóm | Mục | Route | Mục đích |
|------|-----|-------|---------|
| **Quản lý hệ thống** | Tổng quan | `/superadmin` | Xem dashboard tổng hợp hệ thống (số clinics, tài khoản, stats chung) |
| | Phòng khám | `/superadmin/clinics` | CRUD phòng khám/tenants, kích hoạt/vô hiệu hóa, gán feature flags per-clinic |
| | Thống kê | `/superadmin/analytics` | Dữ liệu phân tích cross-tenant (lượt khám, doanh thu, trend theo thời gian) |
| | Audit Logs | `/superadmin/audit-logs` | Xem log toàn hệ thống (tất cả action, tất cả clinic, tất cả user) |
| **Tài khoản & Người dùng** | Tài khoản | `/superadmin/accounts` | CRUD tài khoản platform-level, khóa/mở, reset password, gán clinic |
| **Cấu hình hệ thống** | Cấu hình hệ thống | `/superadmin/system-config` | Quản lý feature flags mặc định, bảo mật/mật khẩu, email/SMTP, thông tin vận hành |

---

## 3. Route Guard & Xác thực

### 3.1 Quyết định thiết kế: RequireSuperuser trên toàn bộ `/superadmin/*`

Mọi route `/superadmin/*` đều bọc guard `<RequireSuperuser>`:

```
route: /superadmin
  ├─ guard: RequireSuperuser (kiểm tra JWT claim is_superuser === true)
  │   ├─ /              → SuperAdminDashboardPage
  │   ├─ /clinics       → SuperAdminClinicsPage
  │   ├─ /analytics     → SuperAdminAnalyticsPage
  │   ├─ /audit-logs    → SuperAdminAuditLogsPage
  │   ├─ /accounts      → SuperAdminAccountsPage
  │   └─ /system-config → SuperAdminSystemConfigPage (MỚI)
  │
  └─ else: redirect /dashboard
```

### 3.2 Hành vi chi tiết

- **Superuser (JWT `is_superuser: true`)** → Render Sidebar 3 nhóm, truy cập tất cả trang `/superadmin/*` → Backend API trả dữ liệu cross-tenant (bypass RLS)
- **Non-superuser (JWT `is_superuser: false` hoặc không có)** → Sidebar ẩn section Super Admin, cố gắng truy cập `/superadmin/*` → route guard kiểm soát, redirect `/dashboard`; gọi API `/api/v1/superadmin/*` → Backend trả 403 Forbidden
- **Unauthenticated (không có token)** → Redirect `/login` (auth middleware FE)

---

## 4. Màn hình Cấu hình hệ thống (System Config)

### 4.1 Tổng quan & thiết kế tabbed

Màn `/superadmin/system-config` hiển thị **4 tab độc lập**, mỗi tab là 1 form với các trường cấu hình thuộc 1 section:

```
┌─────────────────────────────────────────────────────┐
│ Cấu hình hệ thống                                   │
├─────────────────────────────────────────────────────┤
│ [Tab 1] [Tab 2] [Tab 3] [Tab 4]                    │
├─────────────────────────────────────────────────────┤
│ Tab 1: Tính năng mặc định                          │
│ ┌─────────────────────────────────────────────────┐│
│ │ ☑ Lịch hẹn     ☑ Nhà thuốc   ☑ Thanh toán     ││
│ │ ☑ Báo cáo      ☑ Nhân sự     ☐ BHYT           ││
│ │                                                 ││
│ │                              [Lưu]            ││
│ └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### 4.2 Chi tiết từng Tab

#### **Tab 1: Tính năng mặc định (feature_defaults)**

Giá trị boolean (on/off) mặc định áp cho **phòng khám tạo mới**. Mỗi clinic sau khi tạo có thể override riêng qua tab "Phòng khám" → "Tính năng" (per-clinic override).

| Khóa | Nhãn | Kiểu | Mặc định | Ghi chú |
|------|------|------|---------|---------|
| `appointments` | Lịch hẹn | Boolean | ON | Feature appointment scheduling |
| `pharmacy` | Nhà thuốc | Boolean | ON | Feature pharmacy management |
| `billing` | Thanh toán | Boolean | ON | Feature billing/invoicing |
| `reports` | Báo cáo | Boolean | ON | Feature reports/analytics |
| `hr` | Nhân sự | Boolean | ON | Feature HR management |
| `bhyt` | BHYT | Boolean | OFF | Feature BHYT insurance integration |

**Hành vi lưu:** 
- Form validation: không có validation bắt buộc (tất cả toggles optional)
- Submit → `PUT /superadmin/system-config/feature_defaults` với body `{"appointments": true, "pharmacy": true, ...}`
- Response: 200 OK → show toast "Đã lưu"; reload page hoặc gọi GET lại để xác nhận persist
- Giá trị mới ảnh hưởng đến clinics **mới được tạo** (clinic cũ không bị ảnh hưởng)

#### **Tab 2: Bảo mật & Mật khẩu (security_policy)**

Lưu cấu hình chính sách bảo mật toàn hệ thống (mật khẩu, lockout, token, MFA). **Lưu ý:** các trường này được **lưu + hiển thị** nhưng chưa **enforce** (Phase 4 sau).

| Khóa | Nhãn | Kiểu | Mặc định | Ghi chú |
|------|------|------|---------|---------|
| `password_min_length` | Độ dài tối thiểu | Integer | 8 | Số ký tự tối thiểu của mật khẩu |
| `require_uppercase` | Yêu cầu chữ hoa | Boolean | true | Bắt buộc có ít nhất 1 ký tự A-Z |
| `require_lowercase` | Yêu cầu chữ thường | Boolean | true | Bắt buộc có ít nhất 1 ký tự a-z |
| `require_digit` | Yêu cầu chữ số | Boolean | true | Bắt buộc có ít nhất 1 ký tự 0-9 |
| `require_special` | Yêu cầu ký tự đặc biệt | Boolean | false | Bắt buộc có ký tự !@#$%^&* (optional) |
| `password_history_count` | Số lần mật khẩu lưu lại | Integer | 5 | Không cho phép dùng lại N mật khẩu gần nhất |
| `password_expiry_days` | Hết hạn sau (ngày) | Integer | 0 | 0 = vô hạn; N > 0 = buộc đổi sau N ngày |
| `lockout_max_attempts` | Tối đa lần đăng nhập sai | Integer | 5 | Khóa sau N lần đăng nhập sai |
| `lockout_window_minutes` | Cửa sổ đếm (phút) | Integer | 15 | Đếm lại số lần sai trong N phút |
| `lockout_duration_minutes` | Thời gian khóa (phút) | Integer | 30 | Khóa tài khoản trong N phút |
| `access_token_expire_minutes` | Hết hạn access token (phút) | Integer | 15 | JWT access token được phép trong N phút |
| `refresh_token_expire_days` | Hết hạn refresh token (ngày) | Integer | 7 | JWT refresh token được phép trong N ngày |
| `idle_timeout_minutes` | Timeout không hoạt động (phút) | Integer | 0 | 0 = vô hạn; N > 0 = logout sau N phút idle |
| `mfa_requirement` | Yêu cầu MFA | Enum | optional | Giá trị: `off`, `optional`, `required` |
| `sod_enforcement` | Áp dụng phân tách nhiệm vụ (SoD) | Boolean | false | Tách biệt role approval/execution |
| `password_reset_ttl_minutes` | Hết hạn link reset password (phút) | Integer | 30 | Link reset password hiệu lực trong N phút |
| `email_otp_ttl_minutes` | Hết hạn OTP email (phút) | Integer | 5 | OTP qua email hiệu lực trong N phút |
| `email_otp_max_attempts` | Tối đa nhập OTP | Integer | 5 | Cho phép nhập sai tối đa N lần |

**Hành vi lưu:**
- Form validation: số nguyên → range check (ví dụ `password_min_length` ≥ 1); enums → kiểm tra giá trị hợp lệ
- Submit → `PUT /superadmin/system-config/security_policy` 
- Response: 200 OK → toast + reload

**⚠️ Lưu ý enforcement:** Các cấu hình này được **lưu và hiển thị** trong UI, nhưng quá trình **enforce** (kiểm tra mật khẩu, khóa tài khoản khi hết hạn, v.v.) chưa được **wiring** vào code validation/middleware. Chỉ được recommend sau Phase 4.

#### **Tab 3: Email & Thông báo (email)**

Cấu hình SMTP, nhà cung cấp email, template thông báo.

| Khóa | Nhãn | Kiểu | Mặc định | Ghi chú |
|------|------|------|---------|---------|
| `email_provider` | Nhà cung cấp email | Enum | console | Giá trị: `console` (log), `noop` (không gửi), `smtp` (SMTP server) |
| `email_from` | Địa chỉ gửi | String | no-reply@medizen.local | Email "From" trong thư gửi |
| `email_from_name` | Tên hiển thị | String | MediZen | Tên hiển thị sender |
| `smtp_host` | Host SMTP | String | (trống) | Server SMTP (ví dụ: smtp.gmail.com) |
| `smtp_port` | Port SMTP | Integer | (trống) | Port kết nối (ví dụ: 587) |
| `smtp_user` | Username SMTP | String | (trống) | Tài khoản đăng nhập SMTP |
| `smtp_password` | Password SMTP | String | (trống) | **WRITE-ONLY** — không hiển thị lại, chỉ chấp nhận set mới |
| `smtp_use_tls` | Dùng TLS | Boolean | true | Bật TLS cho kết nối SMTP |
| `enable_email_notifications` | Kích hoạt thông báo email | Boolean | true | Gửi email notification hay không |
| `slack_webhook_url` | Slack Webhook URL | String | (trống) | Optional: webhook cho cảnh báo vận hành |
| `pagerduty_routing_key` | PagerDuty Routing Key | String | (trống) | Optional: key cho cảnh báo on-call |

**Hành vi smtp_password (Write-Only):**
- **Lần đầu set:** User nhập password vào field → form submit → BE lưu (hashed hoặc encrypted)
- **Lần reload sau:** Field hiển thị placeholder `••••••••` + hint "Đã thiết lập — để trống nếu không muốn đổi"
- **Thay đổi:** User clear field + nhập mật khẩu mới → PUT → BE cập nhật
- **Không thay:** User để trống field → PUT body **không chứa `smtp_password`** (FE omit nó) → BE giữ nguyên giá trị cũ
- **API response:** GET `/superadmin/system-config/email` trả `"smtp_password_is_set": true/false` (boolean flag thay cho plaintext)

**Hành vi lưu:**
- Form validation: `smtp_host`/`smtp_port` bắt buộc nếu `email_provider === "smtp"`; URL format check trên webhook URLs
- Submit → `PUT /superadmin/system-config/email`
- Response: 200 OK → toast + reload

**Nút "Gửi thử"** (optional, Phase 2+ nếu có):
- Kích hoạt action → gửi email test đến `email_from` hoặc inbox của superadmin
- Response: success/failure toast

#### **Tab 4: Thông tin & Vận hành (system_info)**

Cấu hình metadata hệ thống, localization, maintenance mode, v.v.

| Khóa | Nhãn | Kiểu | Mặc định | Ghi chú |
|------|------|------|---------|---------|
| `system_name` | Tên hệ thống | String | MediZen | Tên platform hiển thị trong UI |
| `default_logo` | Logo mặc định | URL | (trống) | URL logo hoặc upload |
| `support_email` | Email hỗ trợ | String | (trống) | Địa chỉ email support |
| `support_phone` | Điện thoại hỗ trợ | String | (trống) | Số điện thoại support |
| `default_locale` | Ngôn ngữ mặc định | Enum | vi | Giá trị: `vi`, `en` |
| `default_timezone` | Múi giờ mặc định | String | Asia/Ho_Chi_Minh | Timezone IANA (ví dụ: Asia/Ho_Chi_Minh, UTC) |
| `currency` | Đơn vị tiền | String | VND | Mã ISO 4217 (ví dụ: VND, USD) |
| `date_format` | Định dạng ngày | String | DD/MM/YYYY | Format hiển thị (ví dụ: DD/MM/YYYY, MM/DD/YYYY) |
| `frontend_base_url` | Frontend Base URL | URL | http://localhost:1420 | URL gốc FE (dùng trong link email, API callback) |
| `maintenance_mode` | Chế độ bảo trì | Boolean | false | **STORED-ONLY** — chưa enforce |
| `maintenance_message` | Thông báo bảo trì | Text | (trống) | Tin nhắn hiển thị khi bật maintenance |
| `maintenance_allowed_ips` | IPs được phép (bảo trì) | List<String> | [] | Danh sách IP được phép truy cập khi bảo trì |
| `audit_retention_days` | Giữ audit log (ngày) | Integer | 0 | 0 = vô hạn; N > 0 = xóa sau N ngày |
| `environment` | Environment | String (read-only) | (từ env var) | DEV / STAGING / PROD — hiển thị, không sửa |
| `app_version` | Phiên bản ứng dụng | String (read-only) | (từ build) | Version number — hiển thị, không sửa |

**Hành vi lưu:**
- Form validation: URL fields → URL format; list fields → comma-separated; read-only fields (environment, app_version) hiển thị disabled
- Submit → `PUT /superadmin/system-config/system_info`
- Response: 200 OK → toast + reload

**⚠️ maintenance_mode:** Cấu hình được **lưu + hiển thị**, nhưng quá trình **enforce** (middleware chặn request, hiển thị banner) chưa được wiring. Recommend Phase 4.

### 4.3 Hành vi chung của 4 tab

- **Form library:** React Hook Form + Zod validation (giống cách làm FE TASK-092)
- **Save behavior:** Mỗi tab có nút [Lưu] độc lập — click [Lưu] chỉ submit section đó, không submit toàn bộ form
- **After save:** 
  - 200 OK → Show toast "Đã lưu thành công"
  - 400/422 Validation Error → Show toast lỗi chi tiết (ví dụ "Port SMTP phải là số từ 1-65535")
  - 403 Forbidden → Redirect `/dashboard` (user mất superuser quyền)
  - 500 Error → Show toast "Lỗi hệ thống, vui lòng thử lại"
- **Persistence check:** Sau lưu thành công, có thể reload page → GET lại config → kiểm tra giá trị mới được persist

---

## 5. Danh sách API được tiêu thụ

### 5.1 API cũ (từ TASK-070/071)

| STT | Phương thức | Đường dẫn | Mô tả |
|-----|------------|-----------|--------|
| 1 | GET | `/api/v1/superadmin/stats` | Lấy dashboard tổng quan (số clinics, tài khoản, stats) |
| 2 | GET | `/api/v1/superadmin/clinics` | List clinics (server-side pagination: `search`, `skip`, `limit`) |
| 3 | POST | `/api/v1/superadmin/clinics` | Tạo clinic mới |
| 4 | PATCH | `/api/v1/superadmin/clinics/{id}` | Cập nhật clinic |
| 5 | GET | `/api/v1/superadmin/clinics/{id}/features` | Lấy feature flags của clinic |
| 6 | PUT | `/api/v1/superadmin/clinics/{id}/features` | Cập nhật feature flags của clinic |
| 7 | GET | `/api/v1/superadmin/accounts` | List tài khoản (server-side pagination) |
| 8 | POST | `/api/v1/superadmin/accounts` | Tạo tài khoản mới |
| 9 | PATCH | `/api/v1/superadmin/accounts/{id}` | Cập nhật tài khoản |
| 10 | POST | `/api/v1/superadmin/accounts/{id}/reset-password` | Reset password tài khoản |
| 11 | GET | `/api/v1/superadmin/audit-logs` | List audit logs (server-side pagination) |
| 12 | GET | `/api/v1/superadmin/analytics/{overview\|timeseries\|clinics}` | Dữ liệu phân tích |

### 5.2 API mới (TASK-092)

| STT | Phương thức | Đường dẫn | Mô tả |
|-----|------------|-----------|--------|
| 1 | GET | `/api/v1/superadmin/system-config` | Lấy toàn bộ cấu hình hệ thống (4 section) |
| 2 | GET | `/api/v1/superadmin/system-config/{section}` | Lấy cấu hình theo section (`feature_defaults`, `security_policy`, `email`, `system_info`) |
| 3 | PUT | `/api/v1/superadmin/system-config/{section}` | Cập nhật cấu hình theo section |

---

## 6. Chi tiết API mới: Cấu hình hệ thống

### 6.1 GET /api/v1/superadmin/system-config

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/superadmin/system-config` |
| **Mô tả** | Lấy toàn bộ cấu hình hệ thống (4 section cùng lúc) |
| **Xác thực** | Bắt buộc (`Authorization: Bearer {token}`) |
| **Quyền** | `require_superuser: true` |

#### Tham số đầu vào

Không có tham số.

#### Kết quả trả về

**Thành công (200 OK):**

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

**Mô tả các trường kết quả:**

- `feature_defaults`: Cấu hình feature flags mặc định áp cho clinic mới
- `security_policy`: Cấu hình chính sách bảo mật (password, lockout, token, MFA, v.v.)
- `email`: Cấu hình email/SMTP (lưu ý: `smtp_password_is_set` là boolean flag thay cho plaintext password)
- `system_info`: Cấu hình metadata hệ thống (tên, múi giờ, localization, maintenance, v.v.)

**Lỗi (403 Forbidden):**

```json
{
  "detail": "Not authenticated as superuser"
}
```

---

### 6.2 GET /api/v1/superadmin/system-config/{section}

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/superadmin/system-config/{section}` |
| **Mô tả** | Lấy cấu hình của 1 section (không fetch toàn bộ) |
| **Xác thực** | Bắt buộc |
| **Quyền** | `require_superuser: true` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị hợp lệ |
|---------|------|---------|-------|----------------|
| `section` | String (path param) | Có | Section cấu hình | `feature_defaults`, `security_policy`, `email`, `system_info` |

#### Kết quả trả về

**Thành công (200 OK)** — ví dụ `{section} = email`:

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

**Lỗi (404 Not Found):**

```json
{
  "detail": "Unknown section: invalid_section"
}
```

**Lỗi (403 Forbidden):**

```json
{
  "detail": "Not authenticated as superuser"
}
```

---

### 6.3 PUT /api/v1/superadmin/system-config/{section}

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `PUT /api/v1/superadmin/system-config/{section}` |
| **Mô tả** | Cập nhật cấu hình của 1 section |
| **Xác thực** | Bắt buộc |
| **Quyền** | `require_superuser: true` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị hợp lệ |
|---------|------|---------|-------|----------------|
| `section` | String (path param) | Có | Section cấu hình | `feature_defaults`, `security_policy`, `email`, `system_info` |

#### Request Body

**Ví dụ 1: Cập nhật `feature_defaults`**

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

**Ví dụ 2: Cập nhật `email` (set password mới)**

```json
{
  "email_provider": "smtp",
  "email_from": "noreply@clinic.com",
  "email_from_name": "My Clinic",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "clinic@gmail.com",
  "smtp_password": "new_password_here",
  "smtp_use_tls": true,
  "enable_email_notifications": true,
  "slack_webhook_url": "",
  "pagerduty_routing_key": ""
}
```

**Ví dụ 3: Cập nhật `email` (giữ password cũ)**

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

*(Lưu ý: không chứa `smtp_password` trong request → BE giữ nguyên giá trị cũ)*

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu PUT `/superadmin/system-config/{section}` |
| 2 | Kiểm tra token xác thực — từ chối nếu không hợp lệ (401) hoặc không phải superuser (403) |
| 3 | Kiểm tra section hợp lệ — if not in `[feature_defaults, security_policy, email, system_info]` → 404 |
| 4 | Validate request body theo schema của section — if invalid → 422 (chi tiết validation error) |
| 5 | Merge request body vào cấu hình hiện tại section (partial update) — giá trị không có trong request → giữ nguyên |
| 6 | Lưu vào database (table `system_config`, cột `data` JSONB) |
| 7 | (Optional) Ghi audit log: action=`UPDATE_SYSTEM_CONFIG`, section=`{section}`, old_value=..., new_value=... (password ẩn) |
| 8 | Trả kết quả updated section về client |

#### Kết quả trả về

**Thành công (200 OK)** — ví dụ `PUT /superadmin/system-config/email`:

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
  "slack_webhook_url": "",
  "pagerduty_routing_key": ""
}
```

**Lỗi (400/422 Validation Error):**

```json
{
  "detail": "Validation failed: smtp_port must be between 1 and 65535"
}
```

**Lỗi (404 Not Found):**

```json
{
  "detail": "Unknown section: invalid_section"
}
```

**Lỗi (403 Forbidden):**

```json
{
  "detail": "Not authenticated as superuser"
}
```

**Lỗi (500 Internal Error):**

```json
{
  "detail": "Database error occurred"
}
```

---

## 7. Cấu trúc cơ sở dữ liệu

### 7.1 Tổng quan

Hệ thống cấu hình được lưu trong **1 bảng singleton non-tenant** tên `system_config`. Không có `clinic_id`, không RLS (toàn nền tảng), chỉ superuser truy cập (guard ở API).

### 7.2 Bảng: `system_config`

**Mô tả:** Bảng singleton lưu cấu hình hệ thống theo section (key-value JSONB). Mỗi section là 1 dòng trong bảng.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | BIGINT | Có | Khóa chính, tự tăng |
| `section` | VARCHAR(50) | Có | Key của section (`feature_defaults`, `security_policy`, `email`, `system_info`). **Unique Key**. |
| `data` | JSONB | Có | Dữ liệu cấu hình của section (lưu dạng JSON) |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo bản ghi, giá trị mặc định `CURRENT_TIMESTAMP` |
| `updated_at` | TIMESTAMP | Có | Thời điểm cập nhật lần cuối, giá trị mặc định `CURRENT_TIMESTAMP`, tự động cập nhật khi UPDATE |

**Unique Key:** Cột `section` là unique → chỉ 1 dòng per section.

**Script tạo bảng (Alembic migration `0061_superadmin_system_config.py`):**

```python
# up()
op.create_table(
    'system_config',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('section', sa.String(50), nullable=False),
    sa.Column('data', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('section', name='uk_system_config_section')
)

# Seed default data
op.execute("""
    INSERT INTO system_config (section, data) VALUES
    ('feature_defaults', '{"appointments": true, "pharmacy": true, ...}'),
    ('security_policy', '{"password_min_length": 8, ...}'),
    ('email', '{"email_provider": "console", ...}'),
    ('system_info', '{"system_name": "MediZen", ...}')
    ON CONFLICT (section) DO NOTHING;
""")

# down()
op.drop_table('system_config')
```

**Lưu ý:** Migration trên branch là `0061`, nhưng khi merge vào `main` sẽ được **renumber thành `0064`** (sau TASK-093/094 chiếm 0061/0062/0063). Orchestration team xử lý việc renumber tại merge time.

### 7.3 Dữ liệu mặc định (seed)

Bảng được **seed 1 bộ giá trị mặc định** khi migration apply lần đầu:

```sql
INSERT INTO system_config (section, data) VALUES
(
  'feature_defaults',
  '{"appointments": true, "pharmacy": true, "billing": true, "reports": true, "hr": true, "bhyt": false}'
),
(
  'security_policy',
  '{
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
  }'
),
(
  'email',
  '{
    "email_provider": "console",
    "email_from": "no-reply@medizen.local",
    "email_from_name": "MediZen",
    "smtp_host": "",
    "smtp_port": null,
    "smtp_user": "",
    "smtp_use_tls": true,
    "enable_email_notifications": true,
    "slack_webhook_url": "",
    "pagerduty_routing_key": ""
  }'
),
(
  'system_info',
  '{
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
  }'
);
```

### 7.4 Ghi chú bảo mật

- **Bảng không có RLS** — guard được áp ở **API layer** (`require_superuser` dependency)
- **Bảng không có `clinic_id`** — global singleton (không tenant-scoped)
- **Audit exclusion** — cột `smtp_password` được exclude từ audit log để tránh lưu plaintext secret
- **Grant:** Chỉ role `cms_app` (backend app) được `SELECT`, `INSERT`, `UPDATE` trên bảng này

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-001 | Feature defaults được áp cho **clinic mới** khi tạo; clinic cũ không bị ảnh hưởng retroactively | Clinic cũ giữ feature flags hiện tại; chỉ clinic mới (khóa `created_at` > lần gọi API) dùng default mới |
| BR-002 | Cấu hình `security_policy` + `maintenance_mode` được **lưu + hiển thị** nhưng **chưa enforce** (Phase 4) | UI hiển thị cấu hình nhưng validation/lockout/timeout không chạy; recommend document là "advisory config" |
| BR-003 | Password SMTP phải **write-only** — không trả plaintext trong response GET, chỉ flag `smtp_password_is_set` | API trả boolean thay vì plaintext; FE omit trường khỏi PUT body nếu user không set password mới → BE giữ nguyên giá trị |
| BR-004 | Cấu hình `email` yêu cầu `smtp_host`/`smtp_port` bắt buộc **nếu** `email_provider === "smtp"` | Form validation: nếu provider=smtp mà host/port trống → 422 Validation Error |
| BR-005 | Field read-only (`environment`, `app_version`) không được sửa — FE hiển thị disabled, BE ignore PUT request nếu có | Nếu PUT request chứa field read-only, BE sẽ tự động **bỏ qua giá trị mới** (không throw error) |
| BR-006 | Mọi cập nhật `security_policy` được ghi audit log (action=UPDATE_SYSTEM_CONFIG, section=security_policy) — lưu ý **omit plaintext password nếu có** | Audit log chỉ ghi summary: "security_policy updated by superadmin@...", không ghi chi tiết field thay đổi để tránh lộ secret |
| BR-007 | Nếu update không cung cấp trường nào (partial update), giá trị cũ được **merge** vào request thay vì replace toàn bộ | Ví dụ: PUT `email` chỉ set `email_from` mới → BE merge vào, giữ nguyên `smtp_host`, `smtp_port`, v.v. |
| BR-008 | Superuser là **role duy nhất** được truy cập `/superadmin/*` endpoints; role khác (admin, doctor, v.v.) bị 403 | Non-superuser call GET/PUT `/superadmin/system-config` → 403 Forbidden |

---

## 9. Xử lý lỗi

### 9.1 Các mã lỗi phổ biến

| Mã HTTP | Tình huống xảy ra | Thông báo trả về |
|---------|-------------------|-----------------|
| 200 | Cập nhật thành công | `{...updated section data...}` |
| 400 | Tham số đầu vào không hợp lệ hoặc thiếu trường bắt buộc | "Yêu cầu không hợp lệ: [chi tiết lỗi]" |
| 401 | Token xác thực không hợp lệ hoặc đã hết hạn | "Yêu cầu xác thực để truy cập tài nguyên này" |
| 403 | Authenticated nhưng không phải superuser | "Not authenticated as superuser" |
| 404 | Section không hợp lệ (ví dụ `invalid_section`) | "Unknown section: invalid_section" |
| 422 | Giá trị trường không hợp lệ hoặc vi phạm validation | "Validation failed: [chi tiết lỗi]" (ví dụ "smtp_port must be between 1 and 65535") |
| 500 | Lỗi hệ thống nội bộ (database, cache, v.v.) | "Lỗi hệ thống, vui lòng thử lại sau" |

### 9.2 Định dạng phản hồi lỗi

**Lỗi HTTP (400/401/403/404/422/500):**

```json
{
  "detail": "[Mô tả lỗi chi tiết]"
}
```

**Ví dụ lỗi validation:**

```json
{
  "detail": "Validation failed: password_min_length must be >= 1"
}
```

---

## 10. Ghi chú và lưu ý khi kiểm thử

### 10.1 Điểm quan trọng cần nắm

- **Sidebar 3 nhóm**: Kiểm tra render đúng cấu trúc (Quản lý hệ thống / Tài khoản & Người dùng / Cấu hình hệ thống), không có mục clinic workflow (Nhà thuốc/Thanh toán/v.v.)
- **RequireSuperuser guard toàn bộ `/superadmin/*`**: Non-superuser không được truy cập, FE route guard redirect `/dashboard`, BE API trả 403
- **4 tab độc lập**: Mỗi tab có nút [Lưu] riêng, save 1 section không ảnh hưởng section khác
- **smtp_password write-only**: Không thể read plaintext, chỉ flag `smtp_password_is_set` + hint "Đã thiết lập"
- **Partial update (merge)**: PUT request chỉ set một số trường → giá trị khác được giữ nguyên
- **Feature defaults affect new clinics only**: Thay đổi default không retroactive cho clinic cũ
- **Security/Maintenance config stored-only**: Được lưu + hiển thị nhưng chưa enforce logic (Phase 4)
- **Migration renumbering**: `0061` trên branch sẽ renumber thành `0064` khi merge (sau 093/094)

### 10.2 Kịch bản kiểm thử chính

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **Login superuser** | Tài khoản superadmin | Sidebar render 3 nhóm, icon/text "Super Admin" visible |
| **Login non-superuser** | Tài khoản doctor/clinic-admin | Sidebar không show Super Admin section; cố gắng truy cập `/superadmin` → redirect `/dashboard` |
| **Tab 1: Toggle feature off** | HR off → [Lưu] | Toast "Đã lưu", reload → HR vẫn off; tạo clinic mới → feature_defaults có HR off |
| **Tab 2: Change password policy** | `password_min_length` 8 → 10 → [Lưu] | 200 OK, persist; **không** enforce ngay (tester đừng kỳ vọng existing user password bị check lại) |
| **Tab 3: Set SMTP password** | Host/Port/User/Password filled → [Lưu] | 200 OK; reload → host/port/user visible, password field empty + hint "Đã thiết lập" |
| **Tab 3: Update SMTP without password** | Form chỉ set `email_from` mới, skip password field → [Lưu] | 200 OK; BE không touch password (giữ cũ); reload → password_is_set vẫn true |
| **Tab 3: Send test email** (nếu có nút) | Click [Gửi thử] với SMTP valid | Success toast; test email nhận được ở inbox |
| **Tab 4: Timezone change** | Timezone: `Asia/Ho_Chi_Minh` → `Asia/Bangkok` → [Lưu] | 200 OK, persist; reload → timezone mới visible; app hiển thị thời gian theo timezone mới |
| **Non-superuser API call** | `GET /api/v1/superadmin/system-config` as doctor | 403 Forbidden: "Not authenticated as superuser" |
| **Invalid section** | `GET /api/v1/superadmin/system-config/invalid_section` | 404: "Unknown section: invalid_section" |
| **Validation error** | `PUT /superadmin/system-config/email` với `smtp_port: 99999` | 422: "Validation failed: smtp_port must be between 1 and 65535" |

### 10.3 Hạn chế hiện tại & lưu ý

#### **(a) SuperAdminClinicsPage — Status filter page-scoped**

**Vấn đề:** Dropdown "Trạng thái" (Active/Inactive) lọc **chỉ trang hiện tại**, không gọi server-side param `is_active`. 

**Tác dụng phụ:**
- Nếu trang 1 có 50 clinics inactive, tất cả hidden → display "0 / {total}" → có thể gây hiểu nhầm "không có dữ liệu"
- Empty state message "Không tìm thấy" xuất hiện nhưng thực ra có dữ liệu ở trang khác

**Cách kiểm thử:** 
- Lọc inactive → thấy danh sách giảm nhưng tổng số `{pagedClinics.length} / {total}` không khớp
- Khuyến nghị: scroll ngang để thấy full số liệu hoặc implement BE `is_active` query param (follow-up)

**Không phải bug** — documented limitation từ code review, giữ hiện tại để fit scope TASK-092.

#### **(b) security_policy + maintenance_mode — Stored-only, not enforced**

**Vấn đề:** Cấu hình được lưu + hiển thị UI nhưng logic **enforcement** chưa được wiring.

**Ví dụ:**
- Đặt `password_expiry_days: 30` → User cũ không bị logout tự động khi hết 30 ngày
- Đặt `maintenance_mode: true` → System vẫn hoạt động bình thường, không block request hay show banner
- Đặt `lockout_max_attempts: 3` → Lần đăng nhập sai thứ 4 không bị khóa tự động

**Kỳ vọng tester:** 
- Các cấu hình này là **advisory** (lưu ý, recommend dùng nhưng chưa enforce) — không test enforcement
- Phase 4 sẽ implement wiring (middleware, validation hooks, logout logic, v.v.)
- Hiện tại: lưu + hiển thị đủ để chứng minh tính năng end-to-end

#### **(c) bhyt platform default shadowed by Clinic.bhyt_enabled**

**Vấn đề:** Bảng `clinics` có cột legacy `bhyt_enabled` (per-clinic override). Tier-2 precedence của nó vượt tier-3 platform default.

**Tác dụng:** Thay đổi `bhyt` platform default không ảnh hưởng clinic cũ (vì cột `bhyt_enabled` đã set). Chỉ ảnh hưởng clinic **mới mà cột `bhyt_enabled` NULL**.

**Cách kiểm thử:**
- Thay `bhyt` default off → true
- Tạo clinic mới → kiểm tra `bhyt` feature = true (tier-3 fallback)
- Nhưng clinic cũ (với `bhyt_enabled` set) không đổi

**Không phải bug** — tier precedence designed, documented by implementer. Awareness only.

### 10.4 Kịch bản edge case / lỗi

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **Empty section fields** | Tab 3: SMTP fields all empty, provider=console | 200 OK; provider=console not require SMTP fields |
| **Special chars in fields** | System name: "MediZen & Co." → [Lưu] | 200 OK; persist; JSON escape properly |
| **Very long text** | Support email: 500-char string → [Lưu] | 200 OK if valid email format; 422 if invalid |
| **Concurrent updates** | 2 superusers PUT same section simultaneously | Last write wins (no optimistic lock) |
| **Reload without save** | Change field but don't click [Lưu], navigate away → back | Form reset to last saved values |
| **Session expire during edit** | User editing tab, token expire, try [Lưu] | 401 Unauthorized; redirect login |

---

## Hình ảnh & Screenshot

### Màn hình Cấu hình hệ thống — 4 tab

![Tính năng mặc định](../test-reports/screenshots/02-system-config-tab1-features.png)
*Tab 1: Tính năng mặc định*

![Email SMTP với password masked](../test-reports/screenshots/03-system-config-tab3-email-persisted-masked.png)
*Tab 3: Email & SMTP — password write-only masking*

### Sidebar 3 nhóm

![Sidebar Super Admin — 3 nhóm có tiêu đề](../test-reports/screenshots/01-superadmin-nav-groups.png)
*Sidebar: Quản lý hệ thống / Tài khoản & Người dùng / Cấu hình hệ thống*

### Non-superuser guard

![Non-superuser redirect](../test-reports/screenshots/04-nonsuperuser-guard-redirect.png)
*Non-superuser: route guard redirect `/dashboard`*

### CRUD end-to-end

![Clinics CRUD: create & toggle status](../test-reports/screenshots/05-clinics-crud-create-toggle.png)
*Clinics: tạo clinic mới, toggle status*

![Accounts CRUD: create & lock](../test-reports/screenshots/06-accounts-crud-create-lock.png)
*Accounts: tạo tài khoản mới, khóa tài khoản*

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày | Ghi chú |
|---------|--------|------|--------|
| Code Review | Code Review Agent | 2026-07-22 | Approved → IN_TESTING |
| Testing | Test Agent | 2026-07-22 | ALL PASS (13/13 BE, 6/6 FE, 4/4 E2E) |
| Documentation | Documentation Agent | 2026-07-22 | Documentation Complete |
