# Thiết Kế Chi Tiết Tính Năng: FE Auth + App Shell + Design System + i18n

**Dự án:** Clinic CMS
**Task:** TASK-017
**Phiên bản:** 1.0
**Ngày:** 2026-04-27
**Người thực hiện:** Implementation Agent + Code Review Agent + Test Agent
**Trạng thái:** Hoàn thành — Phase A (unit/component test + static validation)
**Tài liệu liên quan:** TASK-003 (Auth API), TASK-016 (Tauri Foundation), clinic_cms_mockup.html

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-04-27 | Phiên bản đầu tiên — Phase A complete (169 tests pass) |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Nguồn dữ liệu đầu vào](#3-nguồn-dữ-liệu-đầu-vào)
- [4. Danh sách API](#4-danh-sách-api)
- [5. Chi tiết từng API](#5-chi-tiết-từng-api)
- [6. Cấu trúc cơ sở dữ liệu](#6-cấu-trúc-cơ-sở-dữ-liệu)
- [7. SQL tổng hợp và truy vấn dữ liệu](#7-sql-tổng-hợp-và-truy-vấn-dữ-liệu)
- [8. Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
- [9. Xử lý lỗi](#9-xử-lỏi)
- [10. Chiến lược cache](#10-chiến-lược-cache)
- [11. Ghi chú và lưu ý khi kiểm thử](#11-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Xây dựng lớp UI foundation cho ứng dụng Tauri CMS — bao gồm hệ thống xác thực người dùng (login, change password, token refresh tự động), app shell (sidebar + topbar + user menu), thành phần giao diện cơ bản (design system dựa trên TailwindCSS + shadcn/ui), đa ngôn ngữ (Tiếng Việt mặc định + Tiếng Anh), quản lý phiên (session persistence), và điều khiển quyền hạn (permission-based menu visibility).

Tính năng này là nền tảng cho tất cả các màn hình chức năng (TASK-018..024) và đảm bảo trải nghiệm người dùng nhất quán, bảo mật, và dễ sử dụng trên cả Windows (.msi) và macOS (.dmg).

### 1.2 Phạm vi

**Bao gồm:**
- Luồng xác thực: `/login` (username + password + clinic_code + remember me), `/change-password` (forced khi password expired), token refresh tự động (401 intercept)
- Lockout countdown UI (5 lần đăng nhập sai → 30s countdown, lock account)
- Secure token storage via Tauri v2 (secureStore API — TASK-016 foundation)
- App shell: Sidebar (collapse/expand, permission-gated nav, lucide-react icons), Topbar (clinic name, notification bell, user menu)
- Permission filtering: Doctor không thấy menu Pharmacy/Admin, v.v.
- Đa ngôn ngữ: i18next bootstrap (vi default + en), locale-specific formatting (date dd/MM/yyyy, currency VND)
- Theming: Light + Dark mode, persist via localStorage
- Error boundary: global error catcher + toast notification (Sonner)
- Design system primitives: Button, Input, Modal, Table, Toast, Form, Select, DatePicker (shadcn/ui) + TailwindCSS
- State management: Zustand (auth + clinic context) + TanStack Query (server cache)
- Routing: React Router v6 nested routes + lazy loading

**Không bao gồm:**
- Tauri binary build (.msi / .dmg) — deferred to CI (Phase C)
- Tauri runtime integration (app.rs event loop, IPC message handling, window lifecycle) — deferred to Phase B
- Lighthouse performance audit (FCP < 2s, TTI < 3s) — deferred to Phase C
- Backend API implementation (TASK-003)
- Sync engine detailed specs (TASK-016)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Người dùng cuối** | Nhân viên phòng khám (Tiếp tân, Bác sĩ, Dược sĩ, Quản trị) — truy cập CMS Tauri trên Windows/macOS |
| **Backend (TASK-003)** | Cung cấp `/api/v1/auth/{login,refresh,logout,change-password}` endpoints |
| **Tauri Foundation (TASK-016)** | Cung cấp `secure_store_*` IPC commands, health_check, get_app_config, sync engine |
| **Frontend screens (TASK-018+)** | Dùng foundation này (auth store, router, design system) để xây dựng các màn hình chức năng |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu — login + session persistence + permission filtering

```
┌─────────────────────────────────────────────────────────────────┐
│ APP STARTUP (App.tsx)                                           │
├─────────────────────────────────────────────────────────────────┤
│ 1. i18next init (vi default, en lazy)                           │
│ 2. authStore.loadFromStorage() → read tokens + user from       │
│    Tauri secure store (or sessionStorage in test/dev)          │
│ 3. If tokens exist & user restored → isAuthenticated = true    │
│ 4. If tokens exist but user JSON corrupt → isAuthenticated = true
│    (but user = null; permission gates hide menu until hydrated)│
│ 5. Mount AppRouter (React Router v6)                           │
└─────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ROUTE GUARD: RequireAuth (src/components/auth/RequireAuth.tsx) │
├─────────────────────────────────────────────────────────────────┤
│ if (isAuthenticated) → allow access (proceed to dashboard)     │
│ else → redirect to /login                                       │
└─────────────────────────────────────────────────────────────────┘
              │ (authenticated) ▼
┌─────────────────────────────────────────────────────────────────┐
│ APP SHELL (AppShell.tsx)                                        │
├─────────────────────────────────────────────────────────────────┤
│ ┌──────────────────┬──────────────────────────────────────────┐ │
│ │ Sidebar          │ Topbar                                   │ │
│ │ ├─ Dashboard ✓   │ ├─ Clinic Name: "Clinic CMS"           │ │
│ │ ├─ Doctor Menu   │ ├─ Notification Bell                     │ │
│ │ │ (filter via    │ ├─ Theme Toggle (Light/Dark)            │ │
│ │ │ RequirePermission)  │ └─ User Menu (Profile / Logout)    │ │
│ │ ├─ Pharmacy Menu │                                         │ │
│ │ │ (hidden if no  │                                         │ │
│ │ │  "pharmacy"    │                                         │ │
│ │ │  permission)   │                                         │ │
│ │ ├─ Admin Menu    │                                         │ │
│ │ │ (hidden if not │                                         │ │
│ │ │  admin role)   │                                         │ │
│ │ └─ Settings      │                                         │ │
│ └──────────────────┴──────────────────────────────────────────┘ │
│                    │                                            │
│                    ▼                                            │
│              Dashboard / Screen                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ LOGIN FLOW (LoginPage.tsx)                                      │
├─────────────────────────────────────────────────────────────────┤
│ 1. User enters username + password + clinic_code + remember_me │
│ 2. Client validates via Zod schema (i18n validation messages)  │
│ 3. POST /api/v1/auth/login {username, password, clinic_code}   │
│                            ▼                                    │
│    ┌─────────────┬──────────────┬──────────────────┐           │
│    │ 200 OK      │ 401 INVALID  │ 423 LOCKED       │ 429 RATE  │
│    ├─────────────┼──────────────┼──────────────────┼───────────┤
│    │ accessToken │ Show error   │ Show lockout     │ Show 30s  │
│    │ refreshToken│ Highlight    │ countdown        │ retry-after
│    │ user{id,    │ password     │ "Tài khoản bị    │ countdown │
│    │ full_name,  │ field        │ khóa do nhập     │ "Yêu cầu  │
│    │ roles,      │ incr counter │ sai quá nhiều    │ quá      │
│    │ permissions,│ (local state)│ lần"             │ nhanh"   │
│    │ password_   │              │                  │ Button   │
│    │ expired?}   │              │                  │ disabled │
│    │ clinic?     │              │                  │          │
│    │             │              │                  │          │
│    │ Store       │              │                  │          │
│    │ tokens via  │              │                  │          │
│    │ authStore.  │              │                  │          │
│    │ setTokens() │              │                  │          │
│    │ → Tauri sec │              │                  │          │
│    │ store       │              │                  │          │
│    │             │              │                  │          │
│    │ If         │              │                  │          │
│    │ password_ex │              │                  │          │
│    │ pired=true: │              │                  │          │
│    │ redirect    │              │                  │          │
│    │ to /change- │              │                  │          │
│    │ password    │              │                  │          │
│    │             │              │                  │          │
│    │ Else:       │              │                  │          │
│    │ redirect to │              │                  │          │
│    │ /dashboard  │              │                  │          │
│    │ (if memory: │              │                  │          │
│    │ restore to  │              │                  │          │
│    │ original    │              │                  │          │
│    │ location)   │              │                  │          │
│    └─────────────┴──────────────┴──────────────────┴───────────┘
│                            ▲
│                            │
│                   (see "Error Handling" §9)
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ TOKEN REFRESH (apiClient.ts intercept on 401)                   │
├─────────────────────────────────────────────────────────────────┤
│ 1. Any screen/API call gets 401                                │
│ 2. apiClient intercepts → calls refreshTokenOnce()             │
│ 3. POST /api/v1/auth/refresh {refresh_token}                   │
│    ├─ Success (200) → authStore.rotateTokens(new access/refresh)
│    │                → retry original request                    │
│    │                → return result to caller                   │
│    └─ Failure (401) → authStore.logout()                       │
│                    → window.location.hash = "#/login"          │
│                    → throw AUTH_SESSION_EXPIRED error          │
│ 4. Concurrent 401s deduplicated via refreshPromise singleton   │
│    (multiple calls wait on same refresh, no race)              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ LANGUAGE SWITCH (settingsStore + i18n)                         │
├─────────────────────────────────────────────────────────────────┤
│ 1. User clicks language toggle (top-right menu)                │
│ 2. settingsStore.setLanguage("en" | "vi")                      │
│ 3. i18n.changeLanguage() + localStorage persist "app.lang"     │
│ 4. All labels re-render via useTranslation() hook              │
│ 5. Date/currency format updates via format.ts helpers          │
│    (dd/MM/yyyy for both, VND always)                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ LOGOUT (user clicks "Logout" in topbar menu)                    │
├─────────────────────────────────────────────────────────────────┤
│ 1. Call authStore.logout()                                     │
│ 2. Clears tokens from secure store + in-memory state          │
│ 3. Deletes user from secure store                              │
│ 4. isAuthenticated = false → RequireAuth redirects to /login   │
│ 5. POST /api/v1/auth/logout {refresh_token} (best-effort)     │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Mô tả các bước chính

#### A. Login Flow

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | User input on /login | Nhập username, password, clinic_code (Zod validation), toggle remember-me checkbox |
| 2 | Client-side validation | Zod schema checks required fields + format (vi/en error messages from i18n) |
| 3 | POST /api/v1/auth/login | gửi {username, password, clinic_code} tới BE (không có remember-me — chỉ UI state) |
| 4a | Success (200 OK) | Nhận access_token, refresh_token, user{id, full_name, roles, permissions, password_expired?}, clinic? |
| 4b | Invalid creds (401) | Show error message; increment local login-attempt counter; if counter ≥ 5 → lockout countdown |
| 4c | Account locked (423) | Show lockout countdown (30s, decrement per 1s), disable Login button until expiry |
| 4d | Rate limit (429) | Show "Yêu cầu quá nhanh, vui lòng chờ {retry_after_seconds}s", disable button, countdown |
| 5 | Store tokens | Call authStore.setTokens() → write tokens + user JSON to Tauri secure store (or sessionStorage in test) |
| 6 | Check password_expired | If true → redirect to /change-password; else → redirect to /dashboard or remembered location |
| 7 | Sync clinic context | Extract clinic info from response, call authStore.setClinicContext() |

#### B. Change Password Flow

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Forced redirect | If password_expired=true on login response → navigate to /change-password |
| 2 | Form input | User enters old_password + new_password + confirm_password (Zod validation, password strength rules from i18n) |
| 3 | POST /api/v1/auth/change-password | gửi {old_password, new_password} |
| 4 | Success (200) | Clear force flag (or re-login); redirect to /dashboard |
| 5 | Failure (401 / 422) | Show error message; stay on /change-password |

#### C. Token Refresh (Auto 401 Intercept)

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | API response 401 | Any screen calls apiRequest() → response 401 |
| 2 | Check retry flag | If _isRetry=true → don't retry again (prevent loop); proceed to logout path |
| 3 | Get refresh_token | Read from secure store |
| 4 | POST /api/v1/auth/refresh | gửi {refresh_token} |
| 5 | Success (200) | Nhận access_token + refresh_token; call authStore.rotateTokens() (does NOT touch user); retry original request |
| 6 | Failure (401) | Call authStore.logout() → clear tokens + user → RequireAuth redirects to /login |
| 7 | Dedup concurrent calls | If multiple 401s fire simultaneously, refreshPromise singleton ensures only 1 refresh POST; all callers wait on same promise |

#### D. Session Persistence on App Restart

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | App startup | App.tsx imports i18n + authStore |
| 2 | Call loadFromStorage() | authStore.loadFromStorage() reads {accessToken, refreshToken, clinicId, clinicCode, user JSON} from secure store |
| 3 | Parse user JSON | Try JSON.parse(userJson); if corrupt → user = null (graceful degradation) |
| 4 | Restore state | set({accessToken, refreshToken, clinicId, clinicCode, user, isAuthenticated: true}) |
| 5 | Mount router | AppRouter mounts → RequireAuth checks isAuthenticated (true) → allow dashboard access |
| 6 | Permission filtering | Sidebar renders with RequirePermission gates → Doctor user has user.permissions=["doctor"] → Admin/Pharmacy menus hidden |
| 7 | Request fresh user | (TASK-018+ feature) If user was null/corrupted, TASK-018 can add /auth/me hydration before rendering sensitive screens |

#### E. Permission-Based Menu Filtering

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Sidebar renders | Sidebar.tsx lists all possible nav items (Dashboard, Doctor, Pharmacy, Admin, Settings) |
| 2 | RequirePermission wrapper | Each item is wrapped: `<RequirePermission permission="admin"><AdminNav /></RequirePermission>` |
| 3 | Check user.permissions | RequirePermission component reads authStore.user.permissions array |
| 4 | Exact match filter | Uses Array.includes() for exact match — "admin" permission required for admin items |
| 5 | Hide or show | If user has permission → render nav item + allow click; else → render fallback (null = hide) or custom fallback |
| 6 | Doctor example | Doctor login → user.permissions=["doctor"] → RequirePermission(permission="pharmacy") → no "pharmacy" in array → hidden |

#### F. Language Switch

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | User clicks toggle | Topbar language button (vi ↔ en) |
| 2 | settingsStore.setLanguage() | Update store + localStorage ("app.lang") |
| 3 | i18n.changeLanguage() | i18next re-loads locale bundles (both already loaded in memory at startup) |
| 4 | Re-render | All useTranslation() hooks trigger updates; text updates in-place |
| 5 | Format updates | format.ts helpers use Intl.DateTimeFormat(locale) → date separator changes; VND always used |

---

## 3. Nguồn dữ liệu đầu vào

Tính năng FE không có data ingestion từ external sources (Kafka, file import, v.v.). Dữ liệu đến từ:

1. **User input** — Login form: username, password, clinic_code, remember_me checkbox
2. **Backend API (TASK-003)** — `/api/v1/auth/{login,refresh,logout,change-password}` responses
3. **Tauri secure store (TASK-016)** — Persisted tokens + user JSON, read on app startup via `secureStore.ts` wrapper

Không áp dụng message queue / file import / ETL logic.

---

## 4. Danh sách API

Tất cả API bắt buộc xác thực qua header:
```
Authorization: Bearer {access_token}
```

**Base Path:** `/api/v1/auth`

Chú ý: Frontend **consumes** (gọi) các API này — BE (TASK-003) là provider.

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt |
|-----|------------|-----------|--------------|
| 1 | POST | `/api/v1/auth/login` | Xác thực username/password/clinic_code → cấp JWT access + refresh token |
| 2 | POST | `/api/v1/auth/refresh` | Cấp access_token mới từ refresh_token hiệu lực (khi access expired) |
| 3 | POST | `/api/v1/auth/logout` | Báo BE rằng user log out (best-effort; FE cũng xóa token locally) |
| 4 | POST | `/api/v1/auth/change-password` | Thay đổi mật khẩu (old_password → new_password) |

---

## 5. Chi tiết từng API

### 5.1 Đăng nhập (Login)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/auth/login` |
| **Mô tả** | Xác thực người dùng bằng username + password + clinic_code. Trả về JWT tokens (access + refresh) + user info (id, full_name, roles, permissions, password_expired flag) + clinic context. |
| **Xác thực** | Không bắt buộc (this is the login endpoint itself) — pass `skipAuth: true` in apiRequest options |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Ví dụ |
|---------|------|---------|-------|-------|
| `username` | String | Có | Tên đăng nhập (email hoặc mã nhân viên) | `"doctor01@clinic.local"` |
| `password` | String | Có | Mật khẩu | `"MyP@ssw0rd"` |
| `clinic_code` | String | Có | Mã phòng khám (multi-tenant identifier) | `"CLINIC001"` |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu từ LoginPage.tsx |
| 2 | BE kiểm tra credentials hợp lệ + account status |
| 3 | Nếu lỗi → trả về 401 (INVALID_CREDENTIALS) hoặc 423 (USER_LOCKED) hoặc 429 (RATE_LIMIT) |
| 4 | Nếu thành công → tạo JWT access (5-15 min expiry), refresh token (7-30 ngày), đóng gói user + clinic info |
| 5 | Trả 200 + response body với tokens + user + clinic |
| 6 | FE nhận → authStore.setTokens() → lưu tokens + user JSON vào Tauri secure store |
| 7 | FE check password_expired → redirect to /change-password hoặc /dashboard |

#### Kết quả trả về

**Thành công (200 OK):**

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

**Mô tả các trường kết quả:**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `access_token` | String | JWT token — attach to subsequent requests via `Authorization: Bearer` header. Expires in 5–15 minutes (BE-specific). |
| `refresh_token` | String | Long-lived JWT — used to obtain new access_token when expired. Expires in 7–30 days. |
| `user.id` | String | UUID or user ID — used for audit trails, clinic context binding. |
| `user.full_name` | String | Display name — shown in Topbar user menu + logs. |
| `user.roles` | Array<String> | List of role codes (e.g., `["DOCTOR", "ADMIN"]`). Used for high-level permission checks. |
| `user.permissions` | Array<String> | Fine-grained permission codes (e.g., `["doctor", "prescription", "pharmacy"]`). Used by RequirePermission to filter sidebar + component visibility. |
| `user.password_expired` | Boolean | **Optional** (per TASK-003 spec ambiguity). If true, FE redirects to /change-password before showing dashboard. If field absent or false, no forced change. |
| `clinic.id` | String | Clinic UUID — used to populate authStore.clinicId (multi-tenant routing header `X-Clinic-Id`). |
| `clinic.code` | String | Clinic code — used for display + context. |
| `clinic.name` | String | Clinic name — planned for Topbar (currently hardcoded "Clinic CMS" — TASK-018 to wire). |

**Lỗi (4xx/5xx):**

See Section 9 (Error Handling).

---

### 5.2 Refresh Token

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/auth/refresh` |
| **Mô tả** | Cấp access_token mới từ refresh_token hiệu lực. Được gọi tự động bởi apiClient khi nhận 401 response. |
| **Xác thực** | Không bắt buộc (refresh token là credentials) — pass `skipAuth: true` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Ví dụ |
|---------|------|---------|-------|-------|
| `refresh_token` | String | Có | Refresh token nhận từ login response | `"eyJhbGc..."` |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | apiClient nhận 401 trên request bất kỳ (không phải retry) |
| 2 | Gọi refreshTokenOnce() → POST /api/v1/auth/refresh {refresh_token} |
| 3 | BE kiểm tra refresh_token hợp lệ + chưa expired |
| 4 | Nếu lỗi → trả 401 (INVALID_TOKEN hoặc TOKEN_EXPIRED) → FE logout |
| 5 | Nếu thành công → tạo access_token mới (cùng user identity, cùng permissions), có thể rotate refresh_token |
| 6 | Trả 200 + {access_token, refresh_token} |
| 7 | FE nhận → authStore.rotateTokens(newAccess, newRefresh) → lưu vào secure store |
| 8 | FE retry original request với access_token mới |
| 9 | Nếu retry thành công → return result; nếu retry lại 401 → logout + redirect /login |

#### Kết quả trả về

**Thành công (200 OK):**

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

**Mô tả:**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `access_token` | String | New JWT access token — replaces old one. Same claims as before (user id, permissions) but newer expiry. |
| `refresh_token` | String | May be the same or rotated (BE-dependent). FE always updates it. |

**Lỗi (4xx/5xx):**

See Section 9.

---

### 5.3 Logout

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/auth/logout` |
| **Mô tả** | Báo BE rằng user log out (invalidate refresh token, audit trail). FE cũng xóa token locally bất kể response. |
| **Xác thực** | Bắt buộc — `Authorization: Bearer {access_token}` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `refresh_token` | String | Có | Refresh token hiện tại (để invalidate trên BE) |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | User clicks Logout in Topbar user menu |
| 2 | authStore.logout() called |
| 3 | FE clears tokens + user from secure store (synchronously in Zustand) |
| 4 | FE sends POST /api/v1/auth/logout (best-effort; ignore response) |
| 5 | RequireAuth redirects to /login immediately |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "code": "00",
  "message": "Logged out successfully"
}
```

---

### 5.4 Change Password

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/auth/change-password` |
| **Mô tả** | Thay đổi mật khẩu người dùng hiện tại. Có thể gọi từ /change-password forced screen hoặc từ Settings (TASK-019) sau khi confirm. |
| **Xác thực** | Bắt buộc — `Authorization: Bearer {access_token}` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Ví dụ |
|---------|------|---------|-------|-------|
| `old_password` | String | Có | Mật khẩu cũ (xác nhận người dùng) | `"OldP@ss123"` |
| `new_password` | String | Có | Mật khẩu mới (phải khác old + pass strength rules) | `"NewP@ss456"` |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | ChangePasswordPage.tsx form input + Zod validation |
| 2 | POST /api/v1/auth/change-password {old_password, new_password} |
| 3 | BE kiểm tra old_password match, strength rules, v.v. |
| 4 | Nếu lỗi (401 old-pwd sai, 422 strength) → trả error; FE shows validation message |
| 5 | Nếu thành công → BE updates password, invalidates all existing tokens (force re-login) |
| 6 | Trả 200 |
| 7 | FE redirects to /login (or auto-logout + redirect) |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "code": "00",
  "message": "Password changed successfully. Please log in again."
}
```

---

## 6. Cấu trúc cơ sở dữ liệu

**Không áp dụng — tính năng FE không trực tiếp thao tác cơ sở dữ liệu.** Lưu trữ trên client side qua Tauri secure store (xem TASK-016 deliverables).

**Client-side storage locations:**
- **Secure store** (tokens + user JSON): `${app_data_dir}/secure_tokens.json` (TASK-016 — currently plaintext, TODO: keyring crate)
- **localStorage** (theme, language preference): Browser `localStorage` within Tauri webview context

---

## 7. SQL tổng hợp và truy vấn dữ liệu

Không áp dụng — tính năng này không có logic tổng hợp dữ liệu.

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Test verification | Status |
|----|---------------|-------------------|--------|
| **BR-AUTH-001** | **Lockout sau 5 lần đăng nhập sai (countdown 30s)** — Khi user submit login form với password sai, FE increment local counter. Sau 5 lần, show lockout countdown (30s, disable button). Counter reset on successful login. BE may also return 423 (USER_LOCKED); FE shows same 30s countdown from response header `Retry-After`. | `apiClient.test.ts` (11 tests) + static review of LoginPage.tsx:122,186-196 (lockout state machine) | ✅ Verified |
| **BR-AUTH-002** | **Auto refresh token khi 401, dedupe concurrent calls** — Khi API response 401, apiClient intercepts (if not retry), calls refreshTokenOnce() → POST /auth/refresh. Concurrent 401s deduplicated via refreshPromise singleton (only 1 refresh POST per "batch"). If refresh succeeds → retry original request. If refresh fails (401 again) → logout + redirect /login. | `apiClient.test.ts` tests: happy-path-retry, recursion-guard, concurrent-dedup, refresh-failure-logout | ✅ Verified |
| **BR-AUTH-003** | **Persist session, fallback gracefully nếu user JSON corrupt** — On app startup, loadFromStorage() reads tokens + user JSON from secure store. If user JSON corrupt → parse throws → user = null (but tokens kept, isAuthenticated = true). Permission gates then hide gated items until user re-fetched (TASK-018). | `authStore.test.ts` (9 tests: persistence, corrupt JSON, rotateTokens preserve); `authStore.persistence.test.tsx` (3 tests: integration + RequirePermission gate after restore) | ✅ Verified |
| **BR-AUTH-004** | **Buộc đổi mật khẩu khi password_expired=true** — If login response has `password_expired: true`, FE redirects to /change-password instead of /dashboard. User must submit change-pwd form before accessing dashboard. | LoginPage.tsx:161-165 redirect logic; static review (Phase B integration test deferred) | ✅ FE-side verified; Phase B pending |
| **BR-PERM-001** | **Ẩn menu Pharmacy/Admin khi user không có permission** — Sidebar renders all nav items wrapped in RequirePermission components. RequirePermission checks user.permissions array (exact match via Array.includes()). If permission not in array → render fallback (null = hide). Example: Doctor user (permissions=["doctor"]) → Pharmacy menu hidden. | `RequirePermission.test.tsx` (6 tests); `authStore.persistence.test.tsx` test 3 (Doctor restored → pharmacy/admin hidden) | ✅ Verified |
| **BR-I18N-001** | **Mặc định ngôn ngữ vi, hỗ trợ chuyển en** — i18next bootstrap with fallback="vi". Both vi + en locale files loaded at startup. User can toggle via Topbar language button → settingsStore.setLanguage() + i18n.changeLanguage() + localStorage persist. | `i18n.test.ts` (11 tests: fallback, both bundles loaded, key translations); `vi-locale-diacritics.test.ts` (24 tests: byte-exact UTF-8 check, no transliteration, en/vi divergence sanity) | ✅ Verified |
| **BR-I18N-002** | **Định dạng tiền tệ luôn VND, ngày dd/MM/yyyy** — format.ts exports formatCurrency() + formatDate() using Intl APIs. Currency always returns "₫" symbol + VND code regardless of locale. Date format always dd/MM/yyyy regardless of locale. | `format.test.ts` (10 tests: currency always VND, date separator per locale, no locale-specific currency swap) | ✅ Verified |
| **BR-THEME-001** | **Light/dark theme, persist qua localStorage** — settingsStore toggleTheme() → update state + localStorage ("app.theme"). Tailwind dark mode CSS class applied to `<html>` element. On startup, loadTheme() reads localStorage + applies class. | `settingsStore.test.ts` (4 tests: theme toggle, localStorage persist, dark-mode CSS class applied) | ✅ Verified |
| **BR-SHELL-001** | **Sidebar collapse/expand state, persist per session** — Sidebar tracks open/collapsed state via settingsStore (or local component state). Used for UX preference (can be persisted to localStorage or reset per app restart). | Component render tests (visual; Phase B for full UX interaction) | ✅ Component verified |
| **BR-ERROR-001** | **Global error boundary catches exceptions, shows user-friendly toast** — ErrorBoundary wraps AppRouter. On exception → componentDidCatch() logs to console + shows fallback UI + optional toast. Errors do not crash app. | `ErrorBoundary.test.tsx` (4 tests: error caught, fallback rendered, logging called) | ✅ Verified |

---

## 9. Xử lý lỗi

### 9.1 HTTP error codes và FE hành vi

| Mã HTTP | Mã lỗi BE | Tình huống | FE hành vi |
|---------|-----------|-----------|-----------|
| 401 | INVALID_CREDENTIALS (login) | Username/password sai | Show error toast + increment counter. If counter ≥ 5 → show lockout countdown (30s), disable button. |
| 401 | TOKEN_EXPIRED (refresh/normal request) | Access token expired, refresh failed | Call authStore.logout() → RequireAuth redirects to /login. Show "Phiên làm việc hết hạn" toast. |
| 401 | INVALID_TOKEN (refresh) | Refresh token sai/revoked | Same as TOKEN_EXPIRED — logout + redirect. |
| 423 | USER_LOCKED | Account locked (too many failed attempts) | Show lockout countdown (read `Retry-After` from response header; default 30s). Disable Login button until expiry. |
| 429 | RATE_LIMIT | Rate limit exceeded (too many requests) | Show "Yêu cầu quá nhanh..." + countdown. Read `Retry-After` from header; default 60s. Disable button. |
| 422 | VALIDATION_ERROR (change-password) | New password doesn't meet strength rules | Show validation error message (from response) under password field. Stay on form. |
| 500 | INTERNAL_SERVER_ERROR | BE fault | Show toast "Lỗi hệ thống, vui lòng thử lại sau". Log error details to console. Allow user to retry. |
| Network error | (no code) | Network unreachable, CORS error, fetch timeout | Show toast "Không thể kết nối, kiểm tra kết nối mạng". ErrorBoundary catches if not handled. |

### 9.2 Định dạng phản hồi lỗi

FE expects BE to return error responses in format:

```json
{
  "code": "[error-code-string]",
  "message": "[user-friendly message in user's language, or vi/en key]",
  "data": {
    "details": "[optional field-level errors, e.g., {password: 'too weak'}]",
    "retry_after_seconds": "[for 429 rate-limit]"
  }
}
```

FE error handling (apiClient.ts:119+):

```ts
if (!response.ok) {
  let errorData: unknown;
  try {
    errorData = await response.json();
  } catch {
    throw new Error(`HTTP ${response.status}`);
  }
  const err = new Error(
    typeof errorData === "object" && errorData !== null && "message" in errorData
      ? String(errorData.message)
      : `HTTP ${response.status}`
  );
  throw err;
}
```

---

## 10. Chiến lược cache

### Mục đích

TanStack Query cấu hình tại app-level với `staleTime` mặc định. Không có cache invalidation rules cụ thể ở layer foundation này — defer to per-screen tasks (TASK-018+) để decide cache strategy cho từng API endpoint.

**Current setup (src/App.tsx):**
- QueryClientProvider wraps entire app
- Default staleTime = 5 min (dữ liệu coi là fresh 5 min; sau đó stale nhưng vẫn serve from cache)
- Default gcTime (formerly cacheTime) = 10 min (cache entries xóa sau 10 min idle)

Mỗi màn hình (TASK-018+) có thể override per-endpoint:
- useQuery({ queryKey: ["endpoint"], queryFn, staleTime: 0 }) — always fresh
- useQuery({ queryKey: ["endpoint"], queryFn, staleTime: 1000*60*30 }) — 30 min cache

Không có cache cho login response (access token store directly in secure store, không cache).
Không có cache invalidation hook ở level foundation.

---

## 11. Ghi chú và lưu ý khi kiểm thử

### 11.1 Điều đặc biệt về dữ liệu + hành vi

1. **Secure store v1 — PLAINTEXT, not production-ready**
   - Current implementation (`src-tauri/src/secure_store.rs`) writes tokens to `${app_data_dir}/secure_tokens.json` as plain UTF-8 text.
   - Emits `eprintln!` warning on first save: "WARNING: secure_store using plaintext fallback — UNSAFE for production".
   - Unix: file mode set to 0o600 (owner read/write only).
   - Windows: no explicit ACL applied (relies on default user ACL isolation).
   - **TODO(security):** Replace with `keyring` crate before deployment to production. Phase B integration testing should trigger Tauri runtime to verify warning.

2. **password_expired field — soft contract with BE**
   - TASK-003 spec ambiguous: does BE return `user.password_expired` on login response?
   - FE handles both cases: if field present + true → redirect to /change-password. If absent or false → no forced change.
   - Graceful degradation: user can proceed to dashboard even if password_expired field missing (no forced change UI, but BE may reject subsequent requests if password actually expired).
   - **Recommendation:** Phase B integration testing to confirm BE contract. If divergence found, raise bug + update TASK-003 spec.

3. **Topbar clinic name hardcoded**
   - Topbar.tsx shows literal "Clinic CMS" until TASK-018 wires clinic context from API.
   - Currently no placeholder for clinic.name from login response.
   - Acceptable as foundation; TASK-018 to implement.

4. **Phase B (Tauri runtime integration) deferred**
   - Current tests mock Tauri APIs via `src/tests/setup.ts`.
   - Real Tauri runtime testing (app startup, window lifecycle, IPC latency) deferred to CI.
   - Includes: login happy path in real app, lockout countdown UI (timer integration), token refresh with 5s TTL, session restore across app restart, secure-store warning verification.
   - Estimated 45–60 min in CI with Tauri dev tooling.

5. **Phase C (build + perf) deferred**
   - `npm run tauri:build` → `.msi` / `.dmg` binaries.
   - Lighthouse-style audit (FCP < 2s, TTI < 3s).
   - Deferred to CI per original review handoff.

### 11.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **Login thành công** | username="doctor01@clinic.local", password="correctpwd", clinic_code="CLINIC001" | 200 OK + tokens + user{roles=["DOCTOR"], permissions=["doctor"]} + redirect to /dashboard |
| **Sai mật khẩu lần 1–4** | Same username + wrong password, repeat 4x | 401 INVALID_CREDENTIALS; counter increments (visible in UI state); no lockout yet. |
| **Sai mật khẩu lần 5** | Same username + wrong password, 5th time | 401 INVALID_CREDENTIALS; counter = 5 → lockout countdown shows (30s). Login button disabled. |
| **BE returns 423 (locked)** | BE account locked due to external factors | 423 USER_LOCKED → FE shows 30s countdown, disable button (same UX as counter=5 path). |
| **BE returns 429 (rate limit)** | User submits > N requests/min | 429 RATE_LIMIT → FE shows "Yêu cầu quá nhanh" + retry-after countdown. Button disabled. |
| **Token auto-refresh (5s TTL)** | Access token expires after 5s; user triggers action at 6s | apiClient 401 intercept → doRefresh POST → new token → retry original request → success (test via mock timer advance in Phase B) |
| **Concurrent 401s** | 2 parallel API calls both get 401 | Only 1 refreshTokenOnce() → only 1 refresh POST sent; both calls wait on same refreshPromise; both get new token; both retry original requests. |
| **Refresh token expired** | User offline > 7 days; refresh_token expires; user tries to log back in | 401 on refresh POST → logout + redirect to /login. Force re-login. |
| **Permission gate (Doctor)** | Login as Doctor user (permissions=["doctor"]) | Doctor menu visible; Pharmacy + Admin menus hidden (RequirePermission filters them out). |
| **Language toggle** | Click en → vi → en | All labels update in-place. Date format (if shown) updates to dd/MM/yyyy. Confirm no mojibake (byte-exact UTF-8). |
| **Theme toggle** | Light → dark → light | CSS class `dark` added/removed from `<html>`. Persist to localStorage. Verify on reload. |
| **Logout** | Click Logout in user menu | authStore.logout() + POST /auth/logout (best-effort) + RequireAuth redirects to /login. Tokens cleared from secure store. |
| **Session persist** | Login → close app → restart | loadFromStorage() restores tokens + user → isAuthenticated = true → dashboard accessible. Doctor menus filter correctly. |
| **Corrupted user JSON** | Manually corrupt secure store user JSON → restart app | loadFromStorage() catches parse error → user = null (graceful). Tokens still valid; dashboard accessible (permission gates show nothing until /auth/me hydrated in TASK-018). |
| **Change password (forced)** | password_expired=true on login response | Redirect to /change-password before /dashboard. Submit old+new pwd → 200 → redirect to /login (or auto-logout + /login). |
| **Change password (success)** | Submit valid old+new pwd on /change-password form | 200 OK → redirect to /login (tokens invalidated by BE). |
| **Change password (weak new pwd)** | Submit weak password (too short, no special char, etc.) | 422 VALIDATION_ERROR → show field-level error. Stay on form. |

### 11.3 Hạn chế hiện tại

- **Tauri runtime integration deferred (Phase B):** Real IPC, window lifecycle, timer latency not tested. Mocking sufficient for Phase A validation.
- **Secure store plaintext:** v1 MVP only. Requires keyring crate migration before production.
- **password_expired ambiguity:** BE contract unclear. Graceful degradation implemented, but Phase B must confirm with actual BE response.
- **Clinic name hardcoded:** Will be wired in TASK-018.
- **No /auth/me endpoint:** User re-hydration not implemented. If user JSON corrupts mid-session, permission gates hide items until next login. TASK-018+ can add hydration.
- **Zod schema per-render:** Validation messages rebuilt on each render (performance neutral for small forms; OK for MVP).
- **Forgot password link:** Not implemented. Marked as button stub in LoginPage; TASK-018+ scope.

### 11.4 Hướng phát triển

- **Phase B:** Tauri runtime integration (app startup, IPC, timer, lifecycle events).
- **Phase C:** Binary build (.msi / .dmg) + Lighthouse perf audit (FCP, TTI targets).
- **TASK-018:** Screen-level implementations (dashboard, doctor, pharmacy, admin screens) — use foundation (auth, router, permission gates, design system).
- **TASK-018+:** /auth/me endpoint for user hydration; clinic-name dynamic wire; forgot-password flow; profile settings (theme, language, clinic selection).
- **Keyring migration:** Replace plaintext secure store with `keyring` crate (blocking issue for production deployment).

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày | Status |
|---------|--------|------|--------|
| Code Review Agent | — | 2026-04-27 | ✅ APPROVED (iter 2) |
| Test Agent | — | 2026-04-27 | ✅ PASSED (169/169 tests) |
| Documentation Agent | — | 2026-04-27 | ✅ COMPLETED |

