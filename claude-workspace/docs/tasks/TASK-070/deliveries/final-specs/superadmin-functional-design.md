# Thiết Kế Chi Tiết Tính Năng: Super Admin FE — Quản lý toàn hệ thống

**Dự án:** Clinic CMS
**Task:** TASK-070
**Phiên bản:** 1.0
**Ngày:** 2026-05-31
**Người thực hiện:** Documentation Agent
**Trạng thái:** Đã duyệt
**Tài liệu liên quan:** TASK-070 task.md, Test Report, Code Review Approval (2026-05-31)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-05-31 | Phiên bản đầu tiên — FE Super Admin functional design |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Kiến trúc xác thực & phân quyền](#3-kiến-trúc-xác-thực--phân-quyền)
- [4. Danh sách API được tiêu thụ](#4-danh-sách-api-được-tiêu-thụ)
- [5. Chi tiết từng trang](#5-chi-tiết-từng-trang)
- [6. Quy tắc nghiệp vụ](#6-quy-tắc-nghiệp-vụ)
- [7. SQL & Cơ sở dữ liệu](#7-sql--cơ-sở-dữ-liệu)
- [8. Xử lý lỗi](#8-xử-lý-lỗi)
- [9. Ghi chú và lưu ý khi kiểm thử](#9-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Super Admin là vai trò cấp platform (trên tất cả phòng khám) cho Clinic CMS. Super Admin có quyền quản lý toàn bộ hệ thống:
- Xem tổng quan thống kê (tất cả clinics, tất cả users, stats hệ thống)
- Tạo, sửa, vô hiệu hóa phòng khám
- Tạo tài khoản admin cho bất kỳ phòng khám nào
- Khóa/mở khóa tài khoản bất kỳ
- Reset mật khẩu người dùng bất kỳ
- Xem audit logs cross-tenant (tất cả clinic, tất cả action)

Tính năng này cung cấp giao diện Frontend quản lý (FE Super Admin), tiêu thụ 10 API endpoints từ Backend đã hoàn chỉnh.

### 1.2 Phạm vi

**Bao gồm:**
- Giao diện đăng nhập (sử dụng lại từ login chung, BE phát JWT với `is_superuser: true`)
- Sidebar section "Super Admin" (render conditions dựa trên `isSuperuser`)
- 4 trang Super Admin: Tổng quan, Phòng khám, Tài khoản, Audit Logs
- Route guard `<RequireSuperuser>` — kiểm soát truy cập URL `/superadmin/*`
- API client types `src/modules/superadmin/api.ts` — 10 endpoints

**Không bao gồm:**
- Backend API endpoints (đã được BE team hoàn chỉnh ở migration 0036, service layer)
- Cơ sở dữ liệu (FE chỉ tiêu thụ dữ liệu)
- User management page cho regular admin (TASK-051 đã xử lý)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Super Admin (End User)** | Người dùng có vai trò superadmin, quản lý toàn hệ thống. Tài khoản: `superadmin` / `Super@12345` |
| **Backend API** | `/api/v1/superadmin/*` endpoints — xác thực `is_superuser` JWT claim, RLS toàn hệ thống |
| **Auth Store** | `src/stores/authStore.ts` — lưu `isSuperuser` boolean từ JWT payload |
| **Route Guard** | `<RequireSuperuser>` component — kiểm soát quyền truy cập trang |
| **Sidebar Component** | `src/components/shell/Sidebar.tsx` — render "Super Admin" section có điều kiện |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng xác thực & phân quyền

```
[User Login]
    │  Nhập superadmin / Super@12345
    ▼
[Auth API] → Backend xác thực
    │  Phát JWT với is_superuser: true
    ▼
[localStorage] ← Lưu token + user.is_superuser
    │  authStore.setUser() ← {is_superuser: true, ...}
    ▼
[authStore.isSuperuser = true]
    │
    ├─► Sidebar render Super Admin section
    │
    └─► <RequireSuperuser> guard: cho phép truy cập /superadmin/*
        │
        ▼
    [SuperAdminDashboardPage]
    [SuperAdminClinicsPage]
    [SuperAdminAccountsPage]
    [SuperAdminAuditLogsPage]
        │
        ▼
    API calls → /api/v1/superadmin/*
    (Bearer token + is_superuser claim)
        │
        ▼
    [Backend RLS: toàn hệ thống]
    ← Dữ liệu cross-tenant
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Đăng nhập | User nhập `superadmin` / `Super@12345` vào form login chung |
| 2 | Backend xác thực | Backend kiểm tra credentials, phát JWT với claim `is_superuser: true` |
| 3 | Lưu JWT & user state | FE lưu token vào localStorage, authStore.setUser() gán `isSuperuser = true` |
| 4 | Render Sidebar | Sidebar component check `isSuperuser` — nếu true, render section "Super Admin" với 4 link |
| 5 | Điều hướng trang Super Admin | User click link "Tổng quan" / "Phòng khám" / ... → React Router navigate tới `/superadmin/*` |
| 6 | Route guard kiểm soát | `<RequireSuperuser>` component trong AppShell — nếu `!isSuperuser` → redirect `/dashboard` |
| 7 | Load trang & gọi API | Trang (Dashboard / Clinics / ...) mount → gọi API `/api/v1/superadmin/*` |
| 8 | Backend RLS | Backend check `is_superuser` claim từ JWT — if true, return cross-tenant data |
| 9 | Render data | Trang render stats cards, bảng clinics/accounts/audit-logs từ response |
| 10 | Logout | User logout → clear localStorage, authStore.isSuperuser = false → sidebar update |

---

## 3. Kiến trúc xác thực & phân quyền

### 3.1 JWT Claim `is_superuser`

Backend phát JWT với claim:

```json
{
  "sub": "superadmin",
  "is_superuser": true,
  "clinic_id": "00000000-0000-0000-00aa",
  "exp": 1234567890
}
```

**Quy tắc:**
- `is_superuser: true` → Super Admin (toàn hệ thống)
- `is_superuser: false` hoặc absent → Regular user (clinic-scoped)

### 3.2 authStore — Lưu isSuperuser

**File:** `src/stores/authStore.ts`

```typescript
interface User {
  id: string;
  username: string;
  email: string;
  is_superuser: boolean;  // ← Từ JWT
  clinic_id?: string;     // ← Null hoặc SYSTEM clinic ID
  clinic_name?: string;
  // ... other fields
}

interface AuthState {
  user: User | null;
  isSuperuser: boolean;   // ← Derived from user?.is_superuser
  token: string | null;
}

// setter
const setUser = (user: User) => {
  state.user = user;
  state.isSuperuser = user.is_superuser === true;
};
```

### 3.3 Route Guard — RequireSuperuser

**File:** `src/components/auth/RequireSuperuser.tsx`

Component này wrap các route `/superadmin/*`. Nếu `!authStore.isSuperuser`, redirect `/dashboard`.

```typescript
export const RequireSuperuser: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isSuperuser } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isSuperuser) {
      navigate('/dashboard');
    }
  }, [isSuperuser, navigate]);

  if (!isSuperuser) return null;
  return <>{children}</>;
};
```

**Sử dụng trong AppShell:**

```tsx
<Routes>
  {/* ... other routes */}
  <Route element={<RequireSuperuser><AppShell /></RequireSuperuser>}>
    <Route path="/superadmin" element={<SuperAdminDashboardPage />} />
    <Route path="/superadmin/clinics" element={<SuperAdminClinicsPage />} />
    <Route path="/superadmin/accounts" element={<SuperAdminAccountsPage />} />
    <Route path="/superadmin/audit-logs" element={<SuperAdminAuditLogsPage />} />
  </Route>
</Routes>
```

### 3.4 Sidebar — Render Có Điều Kiện

**File:** `src/components/shell/Sidebar.tsx`

```typescript
const { isSuperuser } = useAuthStore();

// ... trong JSX
{isSuperuser && (
  <div className="sidebar-section">
    <h3>Super Admin</h3>
    <NavLink to="/superadmin">Tổng quan</NavLink>
    <NavLink to="/superadmin/clinics">Phòng khám</NavLink>
    <NavLink to="/superadmin/accounts">Tài khoản</NavLink>
    <NavLink to="/superadmin/audit-logs">Audit Logs</NavLink>
  </div>
)}
```

**Kết quả:**
- Superadmin login → thấy "Super Admin" section
- Admin login → không thấy "Super Admin" section
- Regular user login → không thấy

---

## 4. Danh sách API được tiêu thụ

Tất cả API đều yêu cầu:
- **Header**: `Authorization: Bearer {token}`
- **JWT Claim**: `is_superuser: true` (BE kiểm tra)
- **Base Path**: `/api/v1/superadmin`

| STT | Phương thức | Đường dẫn | Mô tả |
|-----|------------|-----------|-------|
| 1 | GET | `/stats` | Lấy thống kê hệ thống: tổng clinics, tổng users, active users, locked users |
| 2 | GET | `/clinics` | Danh sách tất cả phòng khám với pagination |
| 3 | POST | `/clinics` | Tạo phòng khám mới (name, code, specialty) |
| 4 | PATCH | `/clinics/{id}` | Cập nhật / toggle trạng thái active/inactive phòng khám |
| 5 | GET | `/accounts` | Danh sách tất cả tài khoản (cross-tenant) với search & filter |
| 6 | POST | `/accounts` | Tạo tài khoản admin cho phòng khám (clinic_id, username, password, roles) |
| 7 | PATCH | `/accounts/{id}` | Khóa/mở khóa tài khoản, cập nhật is_active, is_locked |
| 8 | POST | `/accounts/{id}/reset-password` | Reset mật khẩu tài khoản (phát mật khẩu tạm thời hoặc set random) |
| 9 | GET | `/roles` | Danh sách roles toàn hệ thống (admin, doctor, nurse, v.v.) |
| 10 | GET | `/audit-logs` | Audit logs cross-tenant với filter clinic_id + action + pagination |

**Chi tiết**: Xem `docs/tasks/TASK-070/deliveries/api-specs/superadmin-api-reference.md`

---

## 5. Chi tiết từng trang

### 5.1 Trang 1: Dashboard Tổng Quan (`/superadmin`)

**File:** `src/pages/superadmin/SuperAdminDashboardPage.tsx`

**Nội dung:**

1. **Tựa đề**: "Super Admin — Tổng quan hệ thống"

2. **4 Stat Cards** (row 1):
   - Card 1: Tổng phòng khám (số lượng từ `/stats.total_clinics`)
   - Card 2: Tổng tài khoản (từ `/stats.total_accounts`)
   - Card 3: Tài khoản đang hoạt động (từ `/stats.active_accounts`)
   - Card 4: Tài khoản bị khóa (từ `/stats.locked_accounts`)

3. **Cảnh báo hệ thống** (row 2):
   - Nếu `warnings.inactive_clinics > 0` → Badge "Phòng khám không hoạt động: N"
   - Nếu `warnings.locked_accounts > 0` → Badge "Tài khoản bị khóa: N"
   - Click vào badge → điều hướng tới trang liên quan (Clinics / Accounts)

4. **Bảng Top 5 Phòng khám mới nhất** (row 3):
   - Cột: Tên phòng khám, Code, Specialty, Trạng thái, Ngày tạo
   - Dữ liệu từ `/clinics?limit=5&order_by=created_at DESC`
   - Click row → (optional) navigate tới chi tiết clinic

**API Calls:**
- `GET /superadmin/stats` — 1 lần khi mount
- `GET /superadmin/clinics?limit=5` — 1 lần khi mount

**Error Handling:**
- Nếu 401 → logout + redirect `/login`
- Nếu 403 → toast "Không có quyền truy cập"
- Nếu network error → toast "Lỗi kết nối, vui lòng thử lại"

---

### 5.2 Trang 2: Quản lý Phòng khám (`/superadmin/clinics`)

**File:** `src/pages/superadmin/SuperAdminClinicsPage.tsx`

**Nội dung:**

1. **Tựa đề**: "Quản lý phòng khám"

2. **Thanh công cụ** (row 1):
   - Search box: tìm theo name / code
   - Filter dropdown: Active / Inactive / All
   - Button "Tạo phòng khám" → modal

3. **Bảng Clinics** (row 2):
   - Cột: Tên phòng khám, Code, Specialty, Trạng thái, Số tài khoản, Ngày tạo, Thao tác
   - Pagination: 50 clinics/trang
   - Dữ liệu từ `GET /superadmin/clinics?search=&active=&skip=&limit=50`
   - Sort: có thể click header để sort theo tên / code / ngày tạo (nếu BE hỗ trợ)

4. **Thao tác per row**:
   - Inline toggle: "Kích hoạt" / "Vô hiệu" → PATCH `/superadmin/clinics/{id}` (is_active: true/false)
   - Nút "Xóa" (soft delete hoặc mark inactive) → confirm dialog

5. **Modal Tạo Phòng khám**:
   - Fields: Name (text), Code (text), Specialty (dropdown)
   - Validation:
     - Name: bắt buộc, 1-100 ký tự
     - Code: bắt buộc, duy nhất, 3-20 ký tự (alphanumeric + underscore)
     - Specialty: bắt buộc
   - Button: Tạo / Hủy
   - POST `/superadmin/clinics` → nếu success: refresh table + close modal + toast "Phòng khám mới tạo thành công"

---

### 5.3 Trang 3: Quản lý Tài khoản (`/superadmin/accounts`)

**File:** `src/pages/superadmin/SuperAdminAccountsPage.tsx`

**Nội dung:**

1. **Tựa đề**: "Quản lý tài khoản"

2. **Thanh công cụ** (row 1):
   - Filter Clinic: dropdown (All / clinic_1 / clinic_2 / ...) — gọi API `/superadmin/clinics` để populate
   - Search box: tìm theo username / email
   - Filter Status: All / Active / Locked / Inactive
   - Button "Tạo tài khoản" → form/modal

3. **Bảng Accounts** (row 2):
   - Cột: Username, Phòng khám, Roles (comma-separated), Trạng thái (badge), Đăng nhập gần nhất, Thao tác
   - **Lưu ý:** Không hiển thị cột "Họ tên" (FE cross-tenant không thể decrypt PII)
   - Pagination: 50 tài khoản/trang
   - Dữ liệu từ `GET /superadmin/accounts?clinic_id=&search=&skip=&limit=50&status=`

4. **Thao tác per row**:
   - Nút "Khóa / Mở khóa": PATCH `/superadmin/accounts/{id}` (is_locked: true/false)
   - Nút "Reset mật khẩu": confirm → POST `/superadmin/accounts/{id}/reset-password`
     - Hiển thị dialog: "Mật khẩu tạm: [password]" hoặc "Gửi mật khẩu qua email"
     - Copy to clipboard button
   - Nút "Xem chi tiết": (optional) navigate tới account detail page

5. **Modal Tạo Tài khoản**:
   - Fields:
     - Clinic (dropdown, bắt buộc): gọi `GET /superadmin/clinics`
     - Username (text, bắt buộc): 4-20 ký tự, duy nhất
     - Email (email, bắt buộc)
     - Mật khẩu (password, bắt buộc): 8+ ký tự, yêu cầu đặc biệt
     - Confirm password
     - Roles (multi-checkbox): admin, doctor, nurse, v.v. — gọi `GET /superadmin/roles`
     - Bắt buộc chọn ít nhất 1 role
   - Validation: backend xác thực lại
   - Button: Tạo / Hủy
   - POST `/superadmin/accounts` → success: refresh table + close modal + toast "Tài khoản tạo thành công"

---

### 5.4 Trang 4: Audit Logs (`/superadmin/audit-logs`)

**File:** `src/pages/superadmin/SuperAdminAuditLogsPage.tsx`

**Nội dung:**

1. **Tựa đề**: "Audit Logs — Lịch sử hoạt động"

2. **Thanh công cụ** (row 1):
   - Filter Clinic: dropdown (All / clinic_1 / ...)
   - Filter Action: dropdown (All / CREATE / UPDATE / DELETE / LOGIN / ...)
   - Date range picker: from date / to date (optional)
   - Button "Áp dụng" → filter tập dữ liệu

3. **Bảng Audit Logs** (row 2):
   - Cột: Thời gian, Clinic, User (username), Action, Entity, Mô tả (description)
   - Pagination: 50 logs/trang
   - Dữ liệu từ `GET /superadmin/audit-logs?clinic_id=&action=&skip=&limit=50&date_from=&date_to=`
   - **Read-only**: không có button edit/delete

4. **Thao tác per row**:
   - (Optional) Click row → modal xem chi tiết log (JSON payload nếu có)

---

## 6. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| **BR-001** | Chỉ user có `is_superuser: true` (JWT claim) mới thấy section "Super Admin" trong Sidebar. Nếu `is_superuser: false` hoặc absent, section bị ẩn hoàn toàn. | Sidebar không render "Super Admin" section. Regular user không biết feature này tồn tại. |
| **BR-002** | Nếu user không phải superadmin, truy cập trực tiếp URL `/superadmin/*` sẽ bị `<RequireSuperuser>` guard redirect về `/dashboard`. | Truy cập bị chặn, redirect tự động. Không crash, không 404, không error page. |
| **BR-003** | Super Admin không bị giới hạn tenant — xem toàn bộ clinics, tất cả accounts, tất cả audit logs (cross-tenant). Backend RLS bypass khi `is_superuser: true`. | BE trả lại dữ liệu toàn hệ thống cho FE. FE nhìn thấy 1283 clinics, 1832 accounts, v.v. |
| **BR-004** | Khi tạo clinic mới, phải cung cấp: `name` (bắt buộc), `code` (bắt buộc, duy nhất), `specialty` (bắt buộc). Validation ở FE + BE. | FE disable nút "Tạo" nếu form không hợp lệ. POST `/superadmin/clinics` bị 400/422 nếu thiếu hoặc sai. |
| **BR-005** | Khi tạo account mới, phải cung cấp: `clinic_id` (bắt buộc), `username` (bắt buộc, duy nhất), `password` (bắt buộc, 8+ ký tự), ít nhất 1 `role_code`. Email là bắt buộc. | FE validate form. POST `/superadmin/accounts` bị 400/422 nếu không hợp lệ. |
| **BR-006** | Khóa account (`is_locked: true`) → account đó không thể login được ngay lập tức. Password vẫn giữ nguyên. Mở khóa (`is_locked: false`) → account có thể login lại. | PATCH `/superadmin/accounts/{id}` update `is_locked`. BE kiểm tra flag này ở login endpoint. |
| **BR-007** | Reset mật khẩu → mật khẩu cũ không còn hiệu lực ngay sau khi reset. Account phải dùng mật khẩu mới (hoặc tạm thời) để login. | POST `/superadmin/accounts/{id}/reset-password` → BE phát mật khẩu mới. FE hiển thị cho super admin, có thể gửi email cho user. |

---

## 7. SQL & Cơ sở dữ liệu

**Không áp dụng** — TASK-070 là FE only feature.

- Backend migration 0036 (`clinic-cms-merge/alembic/versions/0036_super_admin.py`) đã tạo các bảng cần thiết: `superadmin`, `clinic`, `account`, `audit_log`.
- FE chỉ tiêu thụ dữ liệu qua API, không trực tiếp query database.
- Seed script: `clinic-cms-merge/scripts/seed_superadmin.py` — tạo superadmin user + 1283 demo clinics + 1832 demo accounts.

---

## 8. Xử lý lỗi

### 8.1 Các mã lỗi phổ biến

| Mã HTTP | Tình huống xảy ra | Thông báo trả về (Toast hoặc Snackbar) |
|---------|-------------------|---------|
| **200** | Request thành công | (Không thông báo, hoặc toast thành công nếu là action như tạo/sửa) |
| **400** | Tham số đầu vào không hợp lệ (ví dụ: code clinic trùng) | "Yêu cầu không hợp lệ: [mô tả lỗi từ BE]" |
| **401** | Token hết hạn hoặc không hợp lệ | Logout tự động + redirect `/login` + toast "Phiên làm việc hết hạn, vui lòng đăng nhập lại" |
| **403** | `is_superuser: false` nhưng vẫn gọi API superadmin (BE xác thực) | Toast "Bạn không có quyền truy cập tài nguyên này" + (có thể redirect `/dashboard`) |
| **404** | Resource không tồn tại (ví dụ: clinic ID không tồn tại) | Toast "Không tìm thấy dữ liệu" |
| **422** | Validation error (ví dụ: email không hợp lệ) | Toast "Lỗi xác thực: [chi tiết]" |
| **500** | Lỗi server (database, service, v.v.) | Toast "Lỗi hệ thống, vui lòng thử lại sau" |
| **Network Error** | Mất kết nối đến BE | Toast "Lỗi kết nối. Vui lòng kiểm tra internet và thử lại" |

### 8.2 Định dạng phản hồi lỗi từ Backend

```json
{
  "code": "INVALID_REQUEST",
  "message": "Clinic code must be unique"
}
```

hoặc (errors list):

```json
{
  "detail": [
    {
      "loc": ["body", "code"],
      "msg": "string",
      "type": "value_error"
    }
  ]
}
```

**FE xử lý:**
- Nếu response có `detail` (array) → parse từng error, hiển thị message concatenated
- Nếu response có `message` (string) → hiển thị trực tiếp
- Mặc định: `"Lỗi xảy ra. Vui lòng thử lại sau"`

### 8.3 Error Handling Flow

```
API call → Response 4xx/5xx
    │
    ├─ 401 → authStore.logout() → navigate('/login')
    │
    ├─ 403 → toast("Không có quyền...") → stay on page
    │
    ├─ 400 / 422 → toast(error.message) → stay on page, user can retry
    │
    ├─ 500 → toast("Lỗi hệ thống...") → stay on page, user can retry
    │
    └─ Network Error → toast("Lỗi kết nối...") → stay on page, user can retry
```

---

## 9. Ghi chú và lưu ý khi kiểm thử

### 9.1 Điểm quan trọng cần nắm

1. **Xác thực là server-authoritative**: FE sidebar & route guard dựa vào `isSuperuser` boolean, nhưng backend luôn kiểm tra JWT claim `is_superuser`. FE có thể bị spoof (DevTools), nhưng API sẽ bị từ chối.

2. **Super Admin thuộc SYSTEM clinic**: Tài khoản superadmin được liên kết với clinic ID cố định `00000000-0000-0000-00aa` (SYSTEM clinic, ẩn). FE không cần gửi `X-Clinic-Id` header cho superadmin APIs (BE xem từ JWT).

3. **Cross-tenant dữ liệu**: Super Admin thấy tất cả clinics, accounts, audit logs. Số lượng lớn (1283 clinics, 1832 accounts) → cần pagination chính xác.

4. **Họ tên (full_name) không hiển thị**: FE cross-tenant không thể decrypt PII encrypted ở DB. Trang accounts chỉ hiển thị username + email, không full_name.

5. **Token scope & session**: Nếu superadmin page gọi background API không-superadmin (ví dụ: dashboard widget từ clinic-scoped), token có thể expire. FE handle 401 → logout + redirect `/login`.

6. **Audit logs read-only**: Không có edit/delete/create action cho audit logs (chỉ view + filter).

### 9.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **TC-001: Regular admin login** | Username: `admin`, Password: `Demo@1234` | Sidebar không có "Super Admin" section |
| **TC-002: Superadmin login** | Username: `superadmin`, Password: `Super@12345` | Sidebar có "Super Admin" section với 4 links |
| **TC-003: Create clinic** | Name: "Clinic A", Code: "CLI_A", Specialty: "Tổng hợp" | Clinic xuất hiện trong bảng ngay lập tức |
| **TC-004: Duplicate code** | Name: "Clinic B", Code: "CLI_A" (trùng lặp) | Toast error "Code must be unique" |
| **TC-005: Lock account** | Account: user123 → is_locked = true | User123 không thể login (401) |
| **TC-006: Reset password** | Account: user456 → new_password = random | User456 login với mật khẩu mới thành công |
| **TC-007: Audit logs filter** | Clinic: "Clinic 1", Action: "CREATE" | Logs hiển thị chỉ CREATE actions của Clinic 1 |
| **TC-008: Unauthorized access** | Direct URL: `/superadmin` as regular admin | Redirect tới `/dashboard` |
| **TC-009: Non-superuser API call** | Call `GET /superadmin/clinics` with admin token | 403 Forbidden |
| **TC-010: Pagination** | Accounts page, page 2 (skip=50, limit=50) | Accounts 51-100 hiển thị |

### 9.3 Hạn chế hiện tại

1. **Họ tên không decrypt cross-tenant** — FE accounts table không hiển thị full_name (QAM trên BE). Follow-up: xem xét endpoint decrypt hoặc table cross-tenant với PII được obfuscate.

2. **Audit logs "Áp dụng" button cosmetic** — Filter re-fetch mỗi khi keystroke, không chờ click "Áp dụng". Acceptable UX, log issue nếu cần optimize.

3. **Session timeout trên superadmin pages** — Nếu background APIs (non-superadmin scoped) return 401, FE logout. Không phải bug, nhưng thể hiện BE token scope design. Follow-up: review token TTL + scoping.

4. **X-Clinic-Id header still sent** — FE gửi `X-Clinic-Id` header trên superadmin API calls (mặc dù BE bypass nó). Not harmful, follow-up: FE cleanup nếu cần.

### 9.4 Hướng phát triển

- **Phiên bản 2.0**: Export audit logs to CSV/Excel
- **Phiên bản 2.0**: Soft delete clinic (với cascade logic cho accounts)
- **Phiên bản 2.0**: Bulk actions (lock multiple accounts, create multiple clinics)
- **Phiên bản 2.0**: Advanced search & saved filters
- **Phiên bản 2.0**: Real-time dashboard updates (WebSocket)

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Code Review Lead | — | 2026-05-31 (APPROVED) |
| Test Lead | — | 2026-05-31 (PASS) |
| Documentation Agent | — | 2026-05-31 |
| Khách hàng / PO | — | |

---

**Hướng dẫn chạy & kiểm thử**

1. **Backend setup**:
   ```bash
   cd clinic-cms-merge
   alembic upgrade head
   python scripts/seed_superadmin.py
   ```

2. **Frontend setup**:
   ```bash
   cd clinic-cms-web
   git checkout feature/TASK-070-superadmin-fe
   npm install
   npm run dev
   ```

3. **Access**:
   - FE: `http://localhost:1420`
   - Login: `superadmin` / `Super@12345`

4. **Test unit tests**:
   ```bash
   npm run test -- src/tests/superadmin
   ```
