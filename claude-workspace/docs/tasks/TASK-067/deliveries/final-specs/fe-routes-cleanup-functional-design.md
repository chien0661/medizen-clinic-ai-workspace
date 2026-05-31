# Thiết Kế Chi Tiết Tính Năng: FE Routes Cleanup & useSync Browser Guard

**Dự án:** MediZen — Phần mềm quản lý phòng khám  
**Task:** TASK-067  
**Phiên bản:** 1.0  
**Ngày:** 2026-05-31  
**Người thực hiện:** Development Team  
**Trạng thái:** Đã duyệt  
**Tài liệu liên quan:** [TASK-053 UI/UX Audit](../../TASK-053/deliveries/final-specs/ui-ux-audit.md), [TASK-046 Security Panels](../../TASK-046/deliveries/final-specs/) 

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-05-31 | Phiên bản đầu tiên — FE routes cleanup + useSync browser guard |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Các thay đổi chi tiết](#3-các-thay-đổi-chi-tiết)
- [4. Danh sách API](#4-danh-sách-api)
- [5. Cấu trúc cơ sở dữ liệu](#5-cấu-trúc-cơ-sở-dữ-liệu)
- [6. SQL tổng hợp và truy vấn dữ liệu](#6-sql-tổng-hợp-và-truy-vấn-dữ-liệu)
- [7. Quy tắc nghiệp vụ](#7-quy-tắc-nghiệp-vụ)
- [8. Xử lý lỗi](#8-xử-lý-lỗi)
- [9. Ghi chú và lưu ý khi kiểm thử](#9-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

TASK-067 hoàn thiện giao diện người dùng (FE) dựa trên các điểm kiểm tra được phát hiện trong TASK-053 (UI/UX Audit). Tính năng này không yêu cầu thêm endpoint API từ Backend; chỉ làm rõ các route hiện có, tạo hub page cho báo cáo, và xử lý tình huống đặc biệt khi chạy FE trên trình duyệt.

**Phạm vi:**
- Thêm route `/admin/security` để expose Security Settings panels (từ TASK-046)
- Thêm route `/admin/bhyt` để access BHYT Config page
- Tạo `/reports` hub page với tab navigation (thay vì route rỗng)
- Cải thiện Profile tab "info" (hiển thị thông tin read-only) và "notifications" (hiển thị kênh thông báo)
- Redirect `/settings` → `/admin/settings` (tránh PlaceholderPage trống)
- Bảo vệ `useSync` hook khỏi lỗi Tauri khi chạy trên trình duyệt (browser guard)

### 1.2 Phạm vi

**Bao gồm:**
- Route wiring: `/admin/security`, `/admin/bhyt`, `/reports` (hub)
- Profile tab enhancements
- Settings root redirect
- useSync browser guard (skip Tauri sync init khi không có `window.__TAURI__`)

**Không bao gồm:**
- API endpoints mới
- Database schema changes
- Backend logic thay đổi
- Chức năng thực hiện chỉnh sửa profile (info edit form chỉ là read-only placeholder)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Người dùng cuối** | Admin, bác sĩ, nhân viên dùng FE web/desktop — cần access bảo mật, cấu hình BHYT, báo cáo. Khi chạy desktop (Tauri), sync data được bảo vệ. |
| **Hệ thống FE** | React SPA (clinic-cms-web) — quản lý routing, state, UI components |
| **Tauri shell** | Desktop container (nếu build desktop) — cung cấp `window.__TAURI__` API |
| **BE API** | Không thay đổi — FE chỉ wire các route hiện có |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng

```
[Người dùng truy cập FE]
    │
    ├─► /admin/security ──► SecuritySettingsPage (từ TASK-046)
    │                       ├─ MFA panel
    │                       ├─ Encryption panel
    │                       ├─ Login history panel
    │                       └─ Password panel
    │
    ├─► /admin/bhyt ──► BhytConfigPage (gated by bhyt_enabled flag)
    │
    ├─► /reports ──► ReportsHubPage (hub)
    │   │
    │   ├─► /reports/revenue ──► RevenueReportPage
    │   ├─► /reports/bhyt ──► BhytReportPage
    │   ├─► /reports/inventory ──► InventoryReportPage
    │   ├─► /reports/doctor-performance ──► DoctorPerformancePage
    │   ├─► /reports/visit-volume ──► VisitVolumePage
    │   ├─► /reports/prescriptions ──► PrescriptionAnalyticsPage
    │   └─► /reports/ar-aging ──► ARAgingReportPage
    │
    ├─► /profile ──► ProfilePage
    │   ├─ Tab "info": show read-only user fields + "Tính năng đang phát triển"
    │   ├─ Tab "security": MFA status, backup codes, login fingerprints
    │   ├─ Tab "notifications": toggle email/SMS/in-app (gated as "coming soon")
    │   └─ Tab "activity": activity log (stub)
    │
    └─► /settings ──► REDIRECT to /admin/settings

[useSync hook lifecycle]
    │
    ├─ Check: window.__TAURI__ exists?
    │   │
    │   ├─ YES (Desktop/Tauri) ──► Enable sync intervals + error handling
    │   │
    │   └─ NO (Browser/Web) ──► Skip all sync logic, silent mode
    │
    └─ Topbar shows "Online" (no ⚠️ warning)
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | **User navigates to /admin/security** | Router matches `/admin/security`, lazy-loads `SecuritySettingsPage`, renders security panels (MFA, encryption, login history, password). |
| 2 | **User navigates to /admin/bhyt** | Router matches `/admin/bhyt`, lazy-loads `BhytConfigPage`. Page checks `bhyt_enabled` feature flag; if OFF, shows feature unavailable message. |
| 3 | **User navigates to /reports** | Router matches `/reports`, lazy-loads `ReportsHubPage` (hub). Hub displays tab navigation linking to 6 report sub-routes. Sidebar "Báo cáo" stays active for all `/reports/*` paths. |
| 4 | **User clicks a report sub-tab** | Nav link to e.g. `/reports/revenue` triggers nested route. `ReportsHubPage` renders Outlet, and sub-route component renders inside. |
| 5 | **User navigates to /profile** | Router matches `/profile`, renders `ProfilePage` with 4 tabs: "My Clinics", "Info", "Security", "Notifications", "Activity". |
| 6 | **User clicks "Info" tab** | `InfoTab` component renders, shows read-only fields (full name, email, roles). Edit form stub shows "Tính năng đang phát triển" badge. |
| 7 | **User clicks "Notifications" tab** | `NotificationsTab` component renders, shows 3 disabled toggle channels (Email, SMS, In-app) with "coming soon" badge. |
| 8 | **User navigates to /settings** | Router has redirect rule: `/settings` → `/admin/settings` (via `<Navigate>`). Browser URL changes to `/admin/settings`. |
| 9 | **FE initializes on web/browser** | `useSync` hook executes `isTauriApp()` check. Detects `window.__TAURI__` is undefined. Sets `syncEnabled = false`. All sync intervals (every 30s, online check, pending count check) are skipped. Topbar never shows ⚠️. |
| 10 | **FE initializes on Tauri desktop** | `useSync` hook detects `window.__TAURI__` exists. Sets `syncEnabled = true`. Sync intervals activate. If sync fails, Topbar shows ⚠️ and error details. |

---

## 3. Các thay đổi chi tiết

### 3.1 Route `/admin/security`

**File:** `src/router/index.tsx`  
**Component:** `src/pages/admin/SecuritySettingsPage.tsx`

**Mô tả:**
- Tạo route mới `/admin/security`
- Lazy-load `SecuritySettingsPage`
- `SecuritySettingsPage` wrap lại `SecurityTab` từ profile module
- Expose MFA panels, login history, backup codes, password settings
- No route-level permission gate (rely on `<RequireAuth>` parent); BE enforces access control via API

**Acceptance Criteria:**
- ✓ Route `/admin/security` tồn tại
- ✓ Renders `SecuritySettingsPage`
- ✓ Displays MFA, Encryption, LoginHistory, Password panels
- ✓ Sidebar "Bảo mật & Mã hoá" link active khi ở `/admin/security`
- ✓ No console errors when navigating

### 3.2 Route `/admin/bhyt`

**File:** `src/router/index.tsx`  
**Component:** `src/pages/admin/BhytConfigPage.tsx`

**Mô tả:**
- Tạo route mới `/admin/bhyt`
- Lazy-load `BhytConfigPage`
- `BhytConfigPage` renders BHYT configuration form
- Feature flag `bhyt_enabled` gates sidebar link; BE enforces PATCH access
- No explicit route-level gate (matches existing codebase convention)

**Acceptance Criteria:**
- ✓ Route `/admin/bhyt` tồn tại
- ✓ Renders `BhytConfigPage`
- ✓ Sidebar link gated by `bhyt_enabled`
- ✓ No console errors

### 3.3 Hub Page `/reports`

**File:** `src/router/index.tsx`  
**Component:** `src/pages/reports/ReportsHubPage.tsx`

**Mô tả:**
- `ReportsHubPage` = hub index page (không phải redirect)
- Displays 6 tab buttons linking to `/reports/{revenue,bhyt,inventory,doctor-performance,visit-volume,prescriptions,ar-aging}`
- Nested route structure: `/reports` is parent route, sub-routes render inside `<Outlet />`
- Router changes: old flat `/reports/{path}` → nested routes under `/reports` parent
- Sidebar "Báo cáo" stays active for all `/reports/*` paths

**Acceptance Criteria:**
- ✓ `/reports` renders hub page with tab nav
- ✓ Each tab links to correct sub-route
- ✓ Sidebar "Báo cáo" highlight stays active on any `/reports/*` sub-route
- ✓ Browser back/forward navigation works
- ✓ Nested routes render inside `<Outlet />`

**ReportsHubPage tab structure:**

| Tab | Link | Description |
|-----|------|-------------|
| Doanh thu | `/reports/revenue` | Revenue report |
| BHYT | `/reports/bhyt` | BHYT report (gated by feature flag) |
| Kho hàng | `/reports/inventory` | Inventory report |
| Hiệu suất | `/reports/doctor-performance` | Doctor performance report |
| Khám bệnh | `/reports/visit-volume` | Visit volume report |
| Toa thuốc | `/reports/prescriptions` | Prescription analytics |
| AR Aging | `/reports/ar-aging` | AR aging report |

### 3.4 Profile Tabs Enhancement

**File:** `src/pages/profile/ProfilePage.tsx`

#### 3.4.1 "Info" Tab

**Mô tả:**
- Render read-only fields: `full_name`, `email`, `roles`
- Each field in disabled input (styled as gray box, not editable)
- Show badge "Chỉnh sửa thông tin — Tính năng đang phát triển"
- No form submission; future version will wire form handler

**Acceptance Criteria:**
- ✓ Shows user's full name, email, roles
- ✓ Fields are read-only (not editable)
- ✓ "Coming soon" badge visible
- ✓ No console errors on render

#### 3.4.2 "Notifications" Tab

**Mô tả:**
- Render 3 channel toggles: Email, SMS, In-app (disabled)
- Each toggle appears grayed out / disabled
- Show badge "Tính năng đang phát triển"
- Placeholder text explains intent: "Tuỳ chỉnh kênh nhận thông báo"
- Future: wire to `/api/v1/users/{id}/notification-prefs` (if BE implements)

**Acceptance Criteria:**
- ✓ Shows 3 channels (Email, SMS, In-app)
- ✓ Toggles are disabled/read-only
- ✓ "Coming soon" badge visible
- ✓ Placeholder text present

#### 3.4.3 "Activity" Tab

**Mô tả:**
- Render generic stub: "Lịch sử hoạt động" + description
- Show "Tính năng đang phát triển" badge
- No data display

**Acceptance Criteria:**
- ✓ Tab renders without errors
- ✓ Shows "coming soon" badge

### 3.5 `/settings` Redirect

**File:** `src/router/index.tsx`

**Mô tả:**
- Replace `<Route path="/settings" element={<PlaceholderPage />} />` with:
  ```jsx
  <Route path="/settings" element={<Navigate to="/admin/settings" replace />} />
  ```
- Redirect `/settings` → `/admin/settings` (client-side)
- Browser URL changes from `/settings` to `/admin/settings`
- `/admin/settings` renders `SettingsPage` (already exists)

**Acceptance Criteria:**
- ✓ Navigating to `/settings` redirects to `/admin/settings`
- ✓ No PlaceholderPage rendered
- ✓ URL updates in address bar

### 3.6 useSync Browser Guard

**File:** `src/hooks/useSync.ts`

**Mô tả:**
- Add helper function `isTauriApp()`: checks `window.__TAURI__` existence
- Compute `tauriActive = isTauriApp()` at hook start
- Combine with caller's `enabled` param: `syncEnabled = enabled && tauriActive`
- Replace all `if (!enabled)` checks in effects with `if (!syncEnabled)`
- When `syncEnabled = false` (browser mode), all sync intervals are skipped
- Topbar never shows ⚠️ sync error in browser mode
- Console logs 0 errors related to Tauri SQL

**isTauriApp() implementation:**

```typescript
function isTauriApp(): boolean {
  return typeof window !== "undefined" && "__TAURI__" in window;
}
```

**useSync changes:**
- Compute `tauriActive = isTauriApp()` once per hook call
- Set `syncEnabled = enabled && tauriActive`
- Update 4 effects: online check, periodic sync, pending count update
- All effects guard: `if (!syncEnabled) return;`
- Dependency arrays: add `syncEnabled` (remove `enabled`)

**Acceptance Criteria:**
- ✓ Running FE in browser: no Tauri SQL errors in console
- ✓ Running FE in browser: Topbar shows "Online" (no ⚠️)
- ✓ Running FE in desktop (Tauri): sync works normally
- ✓ Type check + lint pass
- ✓ Unit tests for `isTauriApp()` guard pass (5 new tests)

---

## 4. Danh sách API

**Không áp dụng — tính năng này không thêm endpoint API mới.**

Tất cả thay đổi là FE routing, không thêm BE API.

---

## 5. Cấu trúc cơ sở dữ liệu

**Không áp dụng — tính năng này không thay đổi schema database.**

---

## 6. SQL tổng hợp và truy vấn dữ liệu

**Không áp dụng — tính năng này không có logic tổng hợp dữ liệu.**

---

## 7. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-001 | Khi truy cập `/admin/security` hoặc `/admin/bhyt`, user phải đã xác thực (RequireAuth guard apply ở parent layout). | Redirect to login page. |
| BR-002 | Khi `bhyt_enabled = false`, sidebar link `/admin/bhyt` bị ẩn. Nếu user thử truy cập trực tiếp, FE renders "Feature not enabled" hoặc blank. BE PATCH endpoint từ chối request. | User sees feature unavailable message. |
| BR-003 | Khi navigate to `/settings`, browser tự động redirect to `/admin/settings` (client-side). | User lands on `/admin/settings` (SettingsPage). |
| BR-004 | Khi FE chạy trên web/browser (không Tauri): useSync hook không khởi tạo sync intervals. | Topbar shows "Online" status, 0 console errors. |
| BR-005 | Khi FE chạy trên Tauri desktop: useSync hook khởi tạo sync intervals bình thường. Nếu sync thất bại, Topbar shows ⚠️ warning. | User can see sync status and take action (retry, etc.). |
| BR-006 | Profile "Info", "Notifications", "Activity" tabs không có form submit. Các field là read-only với "Tính năng đang phát triển" badge. | User cannot edit; badge informs about future availability. |

---

## 8. Xử lý lỗi

### 8.1 Route-level errors

| Tình huống | Xử lý |
|-----------|-------|
| `/admin/security` accessed by unauthenticated user | RequireAuth guard redirects to login |
| `/admin/bhyt` accessed when `bhyt_enabled = false` | Sidebar link is hidden; direct access shows feature unavailable |
| Lazy-load timeout (network slow) | LoadingFallback renders spinner |

### 8.2 useSync errors (browser mode)

| Tình huống | Xử lý |
|-----------|-------|
| useSync detects `window.__TAURI__` absent (browser) | Set `syncEnabled = false`, skip all sync logic |
| useSync in browser: Tauri SQL plugin call attempted | Guard prevents call; no error thrown |
| Topbar sync indicator in browser | Shows "Online" (no ⚠️) |

### 8.3 General UI errors

| HTTP Code | Tình huống | Thông báo |
|-----------|-----------|----------|
| 401 | Token expired or invalid | User redirected to login |
| 403 | Insufficient permission to access route | Show "Access denied" message |
| 500 | Server error on profile fetch | Show "Failed to load profile" with retry button |

---

## 9. Ghi chú và lưu ý khi kiểm thử

### 9.1 Điểm quan trọng

1. **Route wiring**: Verify `/admin/security`, `/admin/bhyt`, `/reports` are properly lazy-loaded and render correct components.

2. **Sidebar navigation**: Test sidebar links are active state correct for each route. Especially:
   - "Bảo mật & Mã hoá" active when at `/admin/security`
   - "Cài đặt BHYT" active when at `/admin/bhyt` (if link visible)
   - "Báo cáo" active for any `/reports/*` path

3. **useSync browser guard**: When running FE in browser (http://localhost:1420):
   - Open DevTools Console
   - Wait 35 seconds
   - Verify: 0 Tauri SQL errors logged
   - Verify: Topbar shows "Online" with no ⚠️ warning icon

4. **Profile tabs**: Verify all tabs render without errors, fields are read-only, "coming soon" badges are visible.

5. **Nested routes**: When inside `/reports/revenue` page, verify:
   - Tab nav is still visible at top of hub
   - Sidebar "Báo cáo" is still active
   - Browser back button navigates to previous `/reports/*` route

### 9.2 Kịch bản kiểm thử

| Kịch bản | Bước | Kết quả kỳ vọng |
|---------|------|---|
| Access /admin/security | Click sidebar "Bảo mật & Mã hoá" | SecuritySettingsPage renders with MFA panel visible |
| Access /admin/bhyt | Click sidebar "BHYT Config" (if visible) | BhytConfigPage renders |
| Access /reports | Click sidebar "Báo cáo" | ReportsHubPage renders with tab nav; sidebar link stays active |
| Click report tab | Click "Doanh thu" tab in hub | Route changes to `/reports/revenue`; RevenueReportPage renders inside Outlet |
| Navigate to /profile | URL bar: /profile | ProfilePage renders with "My Clinics", "Info", "Security", "Notifications", "Activity" tabs |
| Click profile "Info" tab | Click "Thông tin cá nhân" tab | InfoTab renders; shows read-only full_name, email, roles; "coming soon" badge visible |
| Click profile "Notifications" tab | Click "Thông báo" tab | NotificationsTab renders; shows 3 disabled toggles; "coming soon" badge visible |
| Access /settings | URL bar: /settings | Browser redirects to `/admin/settings` automatically |
| useSync browser guard test | Open DevTools, wait 35s | Console shows 0 Tauri errors; Topbar "Online" status with no ⚠️ icon |
| Sidebar active state | Navigate through /reports/revenue, /reports/inventory, /admin/security, /admin/bhyt | Sidebar highlights correct section for each route |

### 9.3 Data requirements

- **Authenticated user** required for all tests (use demo login: admin / Demo@1234)
- **Feature flag** `bhyt_enabled = true` (if testing `/admin/bhyt`)
- **Profile data** should exist in auth store (from successful login)

### 9.4 Hạn chế hiện tại

1. **Profile "info" tab**: Form is read-only; actual profile edit feature deferred to future task
2. **Profile "notifications" tab**: Backend endpoint not yet implemented; toggles are disabled placeholders
3. **Profile "activity" tab**: No data; just a stub with "coming soon" badge
4. **useSync browser guard**: Check is done once at hook initialization; if somehow Tauri becomes available mid-session (unlikely), guard doesn't re-evaluate

### 9.5 Hướng phát triển

- Implement profile edit form (update `InfoTab` to render editable fields with validation + submit)
- Implement notification preferences API and wire UI toggles to backend
- Implement activity log tab (fetch user activity history from API)
- Add route-level permission gates for `/admin/security` and `/admin/bhyt` if needed in future

---

## Phê duyệt

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Trưởng nhóm kỹ thuật | Development Team | 2026-05-31 |
| Tester phụ trách | Test Agent | 2026-05-31 |
| Tài liệu | Documentation Agent | 2026-05-31 |
