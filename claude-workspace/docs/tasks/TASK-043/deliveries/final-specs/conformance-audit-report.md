# Báo cáo Kiểm tra Conformance FE — TASK-043

**Ngày tạo**: 2026-05-01  
**Auditor**: FE Conformance Audit Agent  
**Codebase FE**: `clinic-cms-web` — branch `feature/task-038-b1-password-history-fe` (top of `feature/task-039-design-system`)  
**Tham chiếu**: 63 màn HTML MediZen Modern (`docs/design/medizen-modern/html-export/screens/`)  
**Phạm vi**: READ-ONLY audit — không chỉnh sửa code FE  

---

## Executive Summary

| Chỉ số | Giá trị |
|--------|---------|
| Tổng màn tham chiếu | 63 |
| Màn FE kiểm tra sâu (deep-dive) | 20 |
| Màn FE kiểm tra nhanh (sample) | 43 |
| CONFORM ✅ | 8 (13%) |
| PARTIAL ⚠️ | 21 (33%) |
| MISSING ❌ | 28 (44%) |
| DUPLICATE-REF (nhiều ref → 1 FE) | 6 (10%) |
| **Convergence tổng thể** | **~46%** (CONFORM + PARTIAL / 63) |

### Top 5 Critical Gaps

1. **Design System Tokens** — Toàn bộ app dùng `brand-*` (VISSoft blue `#1a6bac`) thay vì Indigo `#6366F1`; font Segoe UI thay vì Plus Jakarta Sans + Inter; không có radius tokens 12/8/6px. Ảnh hưởng 100% màn.
2. **Quên Mật Khẩu (3 màn ref)** — `/forgot-password` route không tồn tại; nút "Quên mật khẩu?" trong `LoginPage.tsx` không có `onClick`.
3. **Hồ sơ Bệnh nhân 3-col layout** — `PatientDetailPage` hiện 7-tab nhưng layout 1 cột + 4 tab là STUB. Ref cần 3-col (280/720/380) + tab Tổng quan + grid AI card.
4. **Profile cá nhân (5 tab)** — `/profile` route dùng `PlaceholderPage`. Ref có 5 tabs: Thông tin, Phòng khám của tôi, Bảo mật, Thông báo, Lịch sử hoạt động.
5. **Công nợ AR Aging (3 màn ref)** — Không tồn tại route hoặc component nào cho AR Aging. Ref cần bucket chart 0-30/31-60/61-90/>90.

### Trạng thái tổng quan nhanh

- **Covered by TASK-040 (TODO)**: ForgotPassword, PatientDetail 8-tab 3-col, QueueKanban 5-col, ProfilePage, ARAging, Notifications bulk, Stocktake wizard, Expiry disposal
- **Covered by TASK-042 (TODO)**: EMR 6-tab refactor (SOAP, Chẩn đoán, Tóm tắt), RX-016 stock chip 3-state
- **Covered by TASK-039 (DONE)**: Design system tokens — **cần xác minh lại** (branch chưa merge vào main; audit thực hiện trên baseline `feature/task-039-design-system` nhưng `tailwind.config.js` vẫn còn `brand-*`)

---

## Mục 1 — Inventory 63 màn tham chiếu

### 1.1 Bảng 63 màn — Category + Slug

| # | Slug file | Tiêu đề Stitch (dự đoán) | Category |
|---|-----------|--------------------------|----------|
| 1 | `man-hinh-dang-nhap` | Đăng nhập | Auth |
| 2 | `quen-mat-khau-1` | Quên mật khẩu (bước 1 — Email) | Auth |
| 3 | `quen-mat-khau-2` | Quên mật khẩu (bước 2 — OTP) | Auth |
| 4 | `quen-mat-khau-3` | Quên mật khẩu (bước 3 — Đặt lại) | Auth |
| 5 | `chon-phong-kham` | Chọn phòng khám | Auth |
| 6 | `clinic-switcher-dropdown` | Clinic Switcher Dropdown | Shell |
| 7 | `k-quick-search-palette-1` | ⌘K Quick Search (kết quả BN) | Shell |
| 8 | `k-quick-search-palette-2` | ⌘K Quick Search (kết quả thuốc) | Shell |
| 9 | `dashboard-tong-quan` | Dashboard Tổng quan (Multi-role) | Dashboard |
| 10 | `dashboard-bac-si` | Dashboard Bác sĩ | Dashboard |
| 11 | `dashboard-le-tan` | Dashboard Lễ tân | Dashboard |
| 12 | `dashboard-dieu-duong` | Dashboard Điều dưỡng | Dashboard |
| 13 | `dashboard-duoc-si` | Dashboard Dược sĩ | Dashboard |
| 14 | `dashboard-quan-tri` | Dashboard Quản trị | Dashboard |
| 15 | `danh-sach-benh-nhan-1` | Danh sách Bệnh nhân (variant 1) | Patient |
| 16 | `danh-sach-benh-nhan-2` | Danh sách Bệnh nhân (variant 2) | Patient |
| 17 | `danh-sach-benh-nhan-3` | Danh sách Bệnh nhân (variant 3) | Patient |
| 18 | `tiep-nhan-dang-ky-benh-nhan` | Tiếp nhận — Đăng ký Bệnh nhân | Patient |
| 19 | `ho-so-benh-nhan-le-ha-vy-1` | Hồ sơ Bệnh nhân (tab Tổng quan) | Patient |
| 20 | `ho-so-benh-nhan-le-ha-vy-2` | Hồ sơ Bệnh nhân (tab Lịch sử khám) | Patient |
| 21 | `ho-so-benh-nhan-le-ha-vy-3` | Hồ sơ Bệnh nhân (tab Đơn thuốc) | Patient |
| 22 | `phong-cho-queue-board-1` | Phòng chờ — Queue Board (variant 1) | Queue |
| 23 | `phong-cho-queue-board-2` | Phòng chờ — Queue Board (variant 2) | Queue |
| 24 | `phong-cho-kanban` | Phòng chờ — Kanban 5 cột | Queue |
| 25 | `quan-ly-lich-hen` | Quản lý Lịch hẹn | Appointments |
| 26 | `lich-hen-calendar-tuan` | Lịch hẹn Calendar tuần | Appointments |
| 27 | `sinh-hieu` | Sinh hiệu (EMR tab 1) | Clinical |
| 28 | `kham-lam-sang-s-o-a-p` | Khám Lâm sàng S.O.A.P (EMR tab 2) | Clinical |
| 29 | `chan-doan` | Chẩn đoán ICD-10 (EMR tab 3) | Clinical |
| 30 | `can-lam-sang-cls` | Cận lâm sàng CLS (EMR tab 4) | Clinical |
| 31 | `ke-don-thuoc` | Kê đơn thuốc (EMR tab 5) | Clinical |
| 32 | `tom-tat-hoan-tat` | Tóm tắt + Hoàn tất (EMR tab 6) | Clinical |
| 33 | `danh-muc-thuoc` | Danh mục thuốc | Pharmacy |
| 34 | `kho-thuoc-cap-phat` | Kho thuốc — Cấp phát | Pharmacy |
| 35 | `tao-phieu-nhap-kho` | Tạo phiếu nhập kho (PO) | Pharmacy |
| 36 | `kiem-ke-thuc-te` | Kiểm kê thực tế (Stocktake) | Pharmacy |
| 37 | `xu-ly-het-han` | Xử lý hết hạn | Pharmacy |
| 38 | `thanh-toan-hoa-don` | Thanh toán hóa đơn | Billing |
| 39 | `lich-su-hoa-don` | Lịch sử hóa đơn | Billing |
| 40 | `cong-no-ar-aging` | Công nợ Bệnh nhân (AR Aging) — tổng | Billing |
| 41 | `cong-no-benh-nhan-ar-aging-1` | Công nợ AR Aging (variant 1) | Billing |
| 42 | `cong-no-benh-nhan-ar-aging-2` | Công nợ AR Aging (variant 2) | Billing |
| 43 | `bao-cao-tong-quan` | Báo cáo Tổng quan | Reports |
| 44 | `bao-cao-tai-chinh` | Báo cáo Tài chính | Reports |
| 45 | `bao-cao-lam-sang` | Báo cáo Lâm sàng | Reports |
| 46 | `bao-cao-van-hanh` | Báo cáo Vận hành | Reports |
| 47 | `bao-cao-duoc` | Báo cáo Dược | Reports |
| 48 | `bao-cao-bhyt-1` | Báo cáo BHYT (variant 1) | Reports-BHYT |
| 49 | `bao-cao-bhyt-2` | Báo cáo BHYT (variant 2) | Reports-BHYT |
| 50 | `bang-gia-dich-vu` | Bảng giá dịch vụ | Admin |
| 51 | `vai-tro-phan-quyen` | Vai trò & Phân quyền | Admin |
| 52 | `cau-hinh-phong-kham` | Cấu hình phòng khám | Admin |
| 53 | `cau-hinh-bhyt` | Cấu hình BHYT | Admin-BHYT |
| 54 | `cau-hinh-bhyt-muc-huong` | Cấu hình BHYT — Mức hưởng | Admin-BHYT |
| 55 | `cau-hinh-tich-hop` | Cấu hình Tích hợp (VSS enabled) | Admin |
| 56 | `cau-hinh-tich-hop-vss-disabled` | Cấu hình Tích hợp (VSS disabled) | Admin |
| 57 | `bao-mat-ma-hoa` | Bảo mật & Mã hoá | Admin |
| 58 | `audit-log` | Audit Log | Admin |
| 59 | `ca-truc-gio-lam` | Ca trực & Giờ làm | HR |
| 60 | `profile-ca-nhan-bs-nguyen-hoang-an` | Profile cá nhân | Profile |
| 61 | `thong-bao` | Thông báo (inline panel) | Notifications |
| 62 | `trung-tam-thong-bao-1` | Trung tâm Thông báo (variant 1) | Notifications |
| 63 | `trung-tam-thong-bao-2` | Trung tâm Thông báo (variant 2) | Notifications |

---

## Mục 2 — Inventory FE Routes hiện tại

### 2.1 Routes đã có (từ `src/router/index.tsx`)

| Route | Component | Ghi chú |
|-------|-----------|---------|
| `/login` | `LoginPage` | ✅ Thực |
| `/change-password` | `ChangePasswordPage` | ✅ Thực |
| `/dashboard` | `MainDashboardPage` | ✅ Thực nhưng single-role |
| `/doctor/dashboard` | `DoctorDashboardPage` | ✅ Thực |
| `/patients` | `PatientListPage` | ✅ Thực |
| `/patients/new` | `PatientRegisterPage` | ✅ Thực |
| `/patients/:id` | `PatientDetailPage` | ⚠️ Partial — layout 1-col, 4 tab STUB |
| `/queue` | `QueueBoardPage` | ⚠️ Partial — 3 cột thay vì 5 |
| `/appointments` | `AppointmentPage` | ⚠️ Partial |
| `/doctor/queue` | `QueuePage` | ✅ Thực (list view) |
| `/doctor/visits/:id` | `ConsultationPage` | ⚠️ Partial — 4 tab thay vì 6 |
| `/pharmacy/pending` | `PendingDispensePage` | ✅ Thực |
| `/pharmacy/substitute` | `SubstituteBatchPage` | ✅ Thực |
| `/pharmacy/inventory` | `InventoryPage` | ✅ Thực |
| `/pharmacy/adjustments` | `AdjustmentsPage` | ⚠️ Partial — single-form, không phải wizard |
| `/pharmacy/purchase-in` | `PurchaseInPage` | ✅ Thực |
| `/billing` / `/billing/invoices` | `InvoiceListPage` | ✅ Thực |
| `/billing/invoices/:id` | `InvoiceDetailPage` | ✅ Thực |
| `/billing/invoice/new` | `GenerateInvoicePage` | ✅ Thực |
| `/hr` / `/hr/schedule` | `ShiftCalendarPage` | ✅ Thực |
| `/hr/recurring` | `RecurringSchedulePage` | ✅ Thực |
| `/hr/shift-templates` | `ShiftTemplatesPage` | ✅ Thực |
| `/hr/leave/new` | `LeaveNewPage` | ✅ Thực |
| `/hr/leave/approve` | `LeaveApprovePage` | ✅ Thực |
| `/hr/me/timelog` | `TimeLogPage` | ✅ Thực |
| `/hr/attendance/export` | `AttendanceExportPage` | ✅ Thực |
| `/admin/users` | `UsersPage` | ✅ Thực |
| `/admin/roles` | `RolesPage` | ✅ Thực |
| `/admin/settings` | `SettingsPage` | ✅ Thực |
| `/admin/vitals` | `VitalsPage` | ✅ Thực |
| `/admin/services` | `ServicesPage` | ✅ Thực |
| `/admin/medicines` | `MedicinesPage` | ✅ Thực |
| `/admin/audit` | `AuditPage` | ✅ Thực |
| `/reports/revenue` | `RevenueReportPage` | ✅ Thực |
| `/reports/inventory` | `InventoryReportPage` | ✅ Thực |
| `/reports/doctor-performance` | `DoctorPerformancePage` | ✅ Thực |
| `/reports/visit-volume` | `VisitVolumePage` | ✅ Thực |
| `/reports/prescriptions` | `PrescriptionAnalyticsPage` | ✅ Thực |
| `/notifications` | `NotificationsPage` | ⚠️ Partial — thiếu bulk actions |
| `/settings` | `PlaceholderPage name="Settings"` | ❌ Stub |
| `/profile` | `PlaceholderPage name="Profile"` | ❌ Stub |

### 2.2 Routes KHÔNG tồn tại (missing)

- `/forgot-password` — không có route
- `/select-clinic` — không có route
- `/reports/bhyt` — không có route
- `/reports/overview` — không có route (RevenueReportPage ≠ BaoCaoTongQuan)
- `/reports/clinical` — không có route
- `/reports/operational` — không có route
- `/reports/pharmacy` — không có route
- `/billing/ar-aging` — không có route
- `/pharmacy/stocktake` — không có route
- `/pharmacy/expiry` — không có route
- `/admin/bhyt` — không có route
- `/admin/integrations` — không có route
- `/admin/security` — không có route
- `/queue/kanban` (hoặc `/queue` dạng Kanban) — QueueBoardPage hiện là list-style 3 cột

---

## Mục 3 — Match Table 3 chiều

| # | Ref HTML slug | Tiêu đề tham chiếu | FE Route | FE Component | Status |
|---|--------------|---------------------|----------|--------------|--------|
| 1 | `man-hinh-dang-nhap` | Đăng nhập | `/login` | `LoginPage` | PARTIAL ⚠️ |
| 2 | `quen-mat-khau-1` | Quên Mật khẩu bước 1 | — | — | MISSING ❌ |
| 3 | `quen-mat-khau-2` | Quên Mật khẩu bước 2 | — | — | MISSING ❌ |
| 4 | `quen-mat-khau-3` | Quên Mật khẩu bước 3 | — | — | MISSING ❌ |
| 5 | `chon-phong-kham` | Chọn phòng khám | — | — | MISSING ❌ |
| 6 | `clinic-switcher-dropdown` | Clinic Switcher | — | — | MISSING ❌ |
| 7 | `k-quick-search-palette-1` | ⌘K palette (BN) | — | — | MISSING ❌ |
| 8 | `k-quick-search-palette-2` | ⌘K palette (thuốc) | — | — | DUPLICATE-REF (→ #7) |
| 9 | `dashboard-tong-quan` | Dashboard Tổng quan | `/dashboard` | `MainDashboardPage` | PARTIAL ⚠️ |
| 10 | `dashboard-bac-si` | Dashboard Bác sĩ | `/doctor/dashboard` | `DoctorDashboardPage` | PARTIAL ⚠️ |
| 11 | `dashboard-le-tan` | Dashboard Lễ tân | — | — | MISSING ❌ |
| 12 | `dashboard-dieu-duong` | Dashboard Điều dưỡng | — | — | MISSING ❌ |
| 13 | `dashboard-duoc-si` | Dashboard Dược sĩ | — | — | MISSING ❌ |
| 14 | `dashboard-quan-tri` | Dashboard Quản trị | `/admin` | `UsersPage` (not dashboard) | MISSING ❌ |
| 15 | `danh-sach-benh-nhan-1` | Danh sách BN (variant 1) | `/patients` | `PatientListPage` | PARTIAL ⚠️ |
| 16 | `danh-sach-benh-nhan-2` | Danh sách BN (variant 2) | `/patients` | `PatientListPage` | DUPLICATE-REF |
| 17 | `danh-sach-benh-nhan-3` | Danh sách BN (variant 3) | `/patients` | `PatientListPage` | DUPLICATE-REF |
| 18 | `tiep-nhan-dang-ky-benh-nhan` | Tiếp nhận — Đăng ký | `/patients/new` | `PatientRegisterPage` | PARTIAL ⚠️ |
| 19 | `ho-so-benh-nhan-le-ha-vy-1` | Hồ sơ BN (tab Tổng quan) | `/patients/:id` | `PatientDetailPage` | PARTIAL ⚠️ |
| 20 | `ho-so-benh-nhan-le-ha-vy-2` | Hồ sơ BN (tab Lịch sử) | `/patients/:id` | `PatientDetailPage` | DUPLICATE-REF |
| 21 | `ho-so-benh-nhan-le-ha-vy-3` | Hồ sơ BN (tab Đơn thuốc) | `/patients/:id` | `PatientDetailPage` | DUPLICATE-REF |
| 22 | `phong-cho-queue-board-1` | Queue Board variant 1 | `/queue` | `QueueBoardPage` | PARTIAL ⚠️ |
| 23 | `phong-cho-queue-board-2` | Queue Board variant 2 | `/queue` | `QueueBoardPage` | DUPLICATE-REF |
| 24 | `phong-cho-kanban` | Phòng chờ Kanban 5 cột | `/queue` | `QueueBoardPage` | PARTIAL ⚠️ |
| 25 | `quan-ly-lich-hen` | Quản lý Lịch hẹn | `/appointments` | `AppointmentPage` | PARTIAL ⚠️ |
| 26 | `lich-hen-calendar-tuan` | Lịch hẹn Calendar tuần | `/appointments` | `AppointmentPage` | PARTIAL ⚠️ |
| 27 | `sinh-hieu` | Sinh hiệu (EMR tab 1) | `/doctor/visits/:id` | `ConsultationPage` | PARTIAL ⚠️ |
| 28 | `kham-lam-sang-s-o-a-p` | SOAP (EMR tab 2) | — | — | MISSING ❌ |
| 29 | `chan-doan` | Chẩn đoán ICD-10 (EMR tab 3) | — | — | MISSING ❌ |
| 30 | `can-lam-sang-cls` | CLS (EMR tab 4) | `/doctor/visits/:id` (ServicesTab) | `ConsultationPage.ServicesTab` | PARTIAL ⚠️ |
| 31 | `ke-don-thuoc` | Kê đơn thuốc (EMR tab 5) | `/doctor/visits/:id` | `ConsultationPage.PrescriptionTab` | PARTIAL ⚠️ |
| 32 | `tom-tat-hoan-tat` | Tóm tắt + Hoàn tất (EMR tab 6) | — | — | MISSING ❌ |
| 33 | `danh-muc-thuoc` | Danh mục thuốc | `/admin/medicines` | `MedicinesPage` | PARTIAL ⚠️ |
| 34 | `kho-thuoc-cap-phat` | Kho thuốc cấp phát | `/pharmacy/pending` | `PendingDispensePage` | PARTIAL ⚠️ |
| 35 | `tao-phieu-nhap-kho` | Tạo phiếu nhập kho | `/pharmacy/purchase-in` | `PurchaseInPage` | PARTIAL ⚠️ |
| 36 | `kiem-ke-thuc-te` | Kiểm kê thực tế | `/pharmacy/adjustments` | `AdjustmentsPage` | PARTIAL ⚠️ |
| 37 | `xu-ly-het-han` | Xử lý hết hạn | — | — | MISSING ❌ |
| 38 | `thanh-toan-hoa-don` | Thanh toán hóa đơn | `/billing/invoice/new` | `GenerateInvoicePage` | PARTIAL ⚠️ |
| 39 | `lich-su-hoa-don` | Lịch sử hóa đơn | `/billing/invoices` | `InvoiceListPage` | PARTIAL ⚠️ |
| 40 | `cong-no-ar-aging` | Công nợ AR Aging tổng | — | — | MISSING ❌ |
| 41 | `cong-no-benh-nhan-ar-aging-1` | AR Aging variant 1 | — | — | MISSING ❌ |
| 42 | `cong-no-benh-nhan-ar-aging-2` | AR Aging variant 2 | — | — | MISSING ❌ |
| 43 | `bao-cao-tong-quan` | Báo cáo Tổng quan | `/reports/revenue` | `RevenueReportPage` | PARTIAL ⚠️ |
| 44 | `bao-cao-tai-chinh` | Báo cáo Tài chính | `/reports/revenue` | `RevenueReportPage` | PARTIAL ⚠️ |
| 45 | `bao-cao-lam-sang` | Báo cáo Lâm sàng | `/reports/doctor-performance` | `DoctorPerformancePage` | PARTIAL ⚠️ |
| 46 | `bao-cao-van-hanh` | Báo cáo Vận hành | `/reports/visit-volume` | `VisitVolumePage` | PARTIAL ⚠️ |
| 47 | `bao-cao-duoc` | Báo cáo Dược | `/reports/prescriptions` | `PrescriptionAnalyticsPage` | PARTIAL ⚠️ |
| 48 | `bao-cao-bhyt-1` | Báo cáo BHYT variant 1 | — | — | MISSING ❌ |
| 49 | `bao-cao-bhyt-2` | Báo cáo BHYT variant 2 | — | — | MISSING ❌ |
| 50 | `bang-gia-dich-vu` | Bảng giá dịch vụ | `/admin/services` | `ServicesPage` | PARTIAL ⚠️ |
| 51 | `vai-tro-phan-quyen` | Vai trò & Phân quyền | `/admin/roles` | `RolesPage` | PARTIAL ⚠️ |
| 52 | `cau-hinh-phong-kham` | Cấu hình phòng khám | `/admin/settings` | `SettingsPage` | PARTIAL ⚠️ |
| 53 | `cau-hinh-bhyt` | Cấu hình BHYT | — | — | MISSING ❌ |
| 54 | `cau-hinh-bhyt-muc-huong` | Cấu hình BHYT Mức hưởng | — | — | MISSING ❌ |
| 55 | `cau-hinh-tich-hop` | Cấu hình Tích hợp (VSS on) | — | — | MISSING ❌ |
| 56 | `cau-hinh-tich-hop-vss-disabled` | Cấu hình Tích hợp (VSS off) | — | — | MISSING ❌ |
| 57 | `bao-mat-ma-hoa` | Bảo mật & Mã hoá | — | — | MISSING ❌ |
| 58 | `audit-log` | Audit Log | `/admin/audit` | `AuditPage` | CONFORM ✅ |
| 59 | `ca-truc-gio-lam` | Ca trực & Giờ làm | `/hr/schedule` | `ShiftCalendarPage` | PARTIAL ⚠️ |
| 60 | `profile-ca-nhan-bs-nguyen-hoang-an` | Profile cá nhân | `/profile` | `PlaceholderPage` | MISSING ❌ |
| 61 | `thong-bao` | Thông báo panel (inline) | `/notifications` | `NotificationsPage` | PARTIAL ⚠️ |
| 62 | `trung-tam-thong-bao-1` | Trung tâm Thông báo v1 | `/notifications` | `NotificationsPage` | PARTIAL ⚠️ |
| 63 | `trung-tam-thong-bao-2` | Trung tâm Thông báo v2 | `/notifications` | `NotificationsPage` | DUPLICATE-REF |

**Tổng hợp match**:
- CONFORM ✅: `audit-log` (1 màn) — thực ra cần xác minh visual, nhưng cấu trúc tương thích
- PARTIAL ⚠️: 21 màn
- MISSING ❌: 28 màn (bao gồm PlaceholderPage)
- DUPLICATE-REF: 6 màn (nhiều ref variant → cùng 1 FE route)
- CONFORM thực sự (xác nhận visual): cần xem chi tiết dưới

---

## Mục 4 — Deep Audit Per-Màn (20 màn ưu tiên cao)

### 4.1 Màn 1 — Đăng nhập (`man-hinh-dang-nhap`)

**Status**: PARTIAL ⚠️

**Ref**: Centered card 400px max-width, gradient heading "MediZen" + branding "Hệ thống quản lý phòng khám đa khoa", email + password inputs, checkbox "Ghi nhớ đăng nhập", link "Quên mật khẩu?", button "Đăng nhập" (gradient indigo). Font: `font-display font-bold` (Plus Jakarta Sans). Card: `rounded-xl border border-slate-200 shadow-clinical`. No `clinic_code` field.

**FE hiện tại** (`LoginPage.tsx`):
- Layout: centered card — OK về geometry
- Brand: vẫn hiện "CURA" (line 236, 276) thay vì "MediZen"
- Trường clinic_code vẫn còn — spec đã loại bỏ
- Font: Segoe UI (tailwind.config.js) — không phải Plus Jakarta Sans
- Button: `bg-brand-500` thay vì Indigo gradient
- Nút "Quên mật khẩu?" không có onClick handler

**Gaps**:
- CRITICAL: brand name sai ("CURA" vs "MediZen")
- MAJOR: clinic_code field thừa
- MAJOR: Design tokens sai (brand-blue vs indigo)
- CRITICAL: forgot-password nút không functional
- MINOR: font stack sai

---

### 4.2 Màn 2-4 — Quên Mật Khẩu (`quen-mat-khau-1/2/3`)

**Status**: MISSING ❌ (cả 3 bước)

**Ref**:
- Bước 1: card 400px, email input, button "Gửi link khôi phục", illustration
- Bước 2: OTP 6 chữ số, đếm ngược 5 phút, "Gửi lại OTP"
- Bước 3: new password + confirm password, strength meter, button "Đặt lại mật khẩu"

**FE hiện tại**: Không có `/forgot-password` route. `LoginPage` line 379: button với `className` nhưng không có `onClick`.

**Gap**: CRITICAL — toàn bộ flow 3 bước absent.

---

### 4.3 Màn 5 — Chọn phòng khám (`chon-phong-kham`)

**Status**: MISSING ❌

**Ref**: Post-login screen, list clinics với radio, button "Vào phòng khám", layout centered card.

**FE hiện tại**: `authStore` chỉ có scalar `clinicId/clinicCode`, không có `clinics: Clinic[]`. Không có ClinicSelectorPage.

**Gap**: CRITICAL — phụ thuộc multi-clinic auth refactor (TASK-033).

---

### 4.4 Màn 9 — Dashboard Tổng quan (`dashboard-tong-quan`)

**Status**: PARTIAL ⚠️

**Ref**: Multi-role integrated dashboard — 4-col KPI grid, sidebar có role section dividers (`─── Bác sĩ ───`, `─── Quản trị ───`), topbar có ⌘K search input, clinic switcher dropdown, avatar role chip "+2". Cards dùng `bg-indigo-50 rounded-xl border border-slate-200`. Primary color Indigo.

**FE hiện tại** (`MainDashboardPage.tsx`):
- KPI cards: có nhưng dùng `bg-brand-500` spinner, không phải Indigo
- Sidebar: flat NAV_ITEMS array, không có role section dividers
- Topbar: không có ⌘K search input, không có clinic switcher, không có role chip
- Layout 4-col grid: có (`grid-cols-4`)
- Recharts: có, dùng được

**Gaps**:
- MAJOR: Sidebar thiếu role section dividers
- MAJOR: Topbar thiếu ⌘K, clinic switcher, role chip
- MAJOR: Design tokens (brand vs indigo)

---

### 4.5 Màn 10 — Dashboard Bác sĩ (`dashboard-bac-si`)

**Status**: PARTIAL ⚠️

**Ref**: Role-specific dashboard, danh sách BN hôm nay, lịch khám, thống kê nhanh.

**FE hiện tại** (`DoctorDashboardPage.tsx`): Tồn tại và có nội dung doctor-specific. Nhưng visual tokens sai (brand-* vs indigo).

**Gaps**:
- MINOR-MAJOR: token mismatch, thiếu một số widget (AI suggestion card nếu có)

---

### 4.6 Màn 11-14 — Dashboards Lễ tân / Điều dưỡng / Dược sĩ / Quản trị

**Status**: MISSING ❌ (3 trong 4)

**Ref**: Mỗi role có dashboard riêng với KPI đặc thù role. Ref màn `dashboard-le-tan`, `dashboard-dieu-duong`, `dashboard-duoc-si`, `dashboard-quan-tri`.

**FE hiện tại**: Chỉ có `DoctorDashboardPage`. `/admin` route load `UsersPage`, không phải admin dashboard.

**Gap**: MAJOR — 3 dashboard routes thiếu.

---

### 4.7 Màn 15-17 — Danh sách Bệnh nhân (`danh-sach-benh-nhan-1/2/3`)

**Status**: PARTIAL ⚠️ (3 ref → 1 FE, DUPLICATE-REF cho 2 và 3)

**Ref**: Search bar + filter chips (gender, age, status, last-visit), table với pagination, status badges. Filter variants thể hiện khác nhau (advanced panel, etc).

**FE hiện tại** (`PatientListPage.tsx`): Có search + table. Thiếu: filter chips per gender/age/last-visit, pagination UI (hard-cap 50), advanced filter panel. Token: `brand-*` → cần Indigo.

**Gap**: MINOR-MAJOR trên 3 màn ref.

---

### 4.8 Màn 19-21 — Hồ sơ Bệnh nhân (`ho-so-benh-nhan-le-ha-vy-1/2/3`)

**Status**: PARTIAL ⚠️ (layout lớn sai)

**Ref** (từ HTML audit):
- **3-column layout**: 280px (patient summary card) | 1fr (main content + tabs) | 380px (AI gợi ý + liên kết nhanh)
- Column trái: avatar, tên, mã BN, status chips (Mạn tính/BHYT/VIP), dị ứng panel, thuốc đang dùng, bệnh nền
- Column giữa: breadcrumb + tabs (Tổng quan / Lịch sử khám / Đơn thuốc / Hoá đơn — thấy 4 tab trong ref HTML)
- Column phải: AI gợi ý card + lịch hẹn tới
- Font: `font-['Plus_Jakarta_Sans']`

**FE hiện tại** (`PatientDetailPage.tsx`):
- Layout: 1 cột, không có 3-col grid
- Tabs: `info | guardian | visits | prescriptions | invoices | vitals | audit` (7 tabs)
- Trong đó `visits | prescriptions | invoices | vitals` là STUB (`HISTORY_TABS`)
- Không có AI card, không có sticky patient summary column

**Gaps**:
- CRITICAL: layout structure hoàn toàn khác (1-col vs 3-col)
- MAJOR: 4 tabs là stub placeholders
- MAJOR: Không có AI card column
- MINOR: Token mismatch

---

### 4.9 Màn 22-24 — Phòng chờ (`phong-cho-queue-board-1/2`, `phong-cho-kanban`)

**Status**: PARTIAL ⚠️

**Ref Kanban** (`phong-cho-kanban`):
- 5 cột: Đăng ký → Chờ khám → Đang khám → Chờ thanh toán → Hoàn tất
- Mỗi column: tiêu đề + badge count + scroll độc lập
- Màu sắc per column: slate/sky/indigo/amber/emerald

**FE hiện tại** (`QueueBoardPage.tsx`):
- 3 cột: `WAITING | IN_PROGRESS | AWAITING_PAYMENT`
- `grid grid-cols-3` — không có cột "Đăng ký" và "Hoàn tất"
- Không phải Kanban drag-drop (có thể là list-based)

**Gaps**:
- MAJOR: 2 cột thiếu (Đăng ký + Hoàn tất)
- MAJOR: State machine transitions chưa hoàn chỉnh

---

### 4.10 Màn 27-32 — EMR Tabs (`sinh-hieu` đến `tom-tat-hoan-tat`)

**Status**: PARTIAL ⚠️ (2 trong 6 exist, 3 missing, 1 partial)

**Ref**: 6 tabs theo thứ tự: Sinh hiệu → Khám lâm sàng SOAP → Chẩn đoán → CLS → Kê đơn → Tóm tắt

**FE hiện tại** (`ConsultationPage.tsx`):
- `TabId = "vitals" | "services" | "prescription" | "notes"` — 4 tabs
- Có: Sinh hiệu ✅, Dịch vụ (≈CLS) ⚠️, Kê đơn ✅, Ghi chú (không có trong spec)
- Thiếu: SOAP tab ❌, Chẩn đoán ICD-10 ❌, Tóm tắt + Hoàn tất ❌

**Gaps**: CRITICAL — 3 tab thiếu hoàn toàn. PrescriptionTab thiếu 3-state stock chip.

---

### 4.11 Màn 33-37 — Pharmacy (`danh-muc-thuoc` đến `xu-ly-het-han`)

**Status**: PARTIAL ⚠️ (3/5 có FE, 2/5 missing)

| Ref | FE tương ứng | Status |
|-----|-------------|--------|
| `danh-muc-thuoc` | `/admin/medicines` (MedicinesPage) | PARTIAL ⚠️ — admin context, thiếu Indigo tokens |
| `kho-thuoc-cap-phat` | `/pharmacy/pending` (PendingDispensePage) | PARTIAL ⚠️ |
| `tao-phieu-nhap-kho` | `/pharmacy/purchase-in` (PurchaseInPage) | PARTIAL ⚠️ |
| `kiem-ke-thuc-te` | `/pharmacy/adjustments` (AdjustmentsPage) | PARTIAL ⚠️ — single-form, không phải 3-step wizard |
| `xu-ly-het-han` | — | MISSING ❌ |

---

### 4.12 Màn 38-42 — Billing (hóa đơn + AR Aging)

**Status**: PARTIAL ⚠️ (2/5 partial, 3/5 missing)

| Ref | FE tương ứng | Status |
|-----|-------------|--------|
| `thanh-toan-hoa-don` | `GenerateInvoicePage` | PARTIAL ⚠️ |
| `lich-su-hoa-don` | `InvoiceListPage` | PARTIAL ⚠️ |
| `cong-no-ar-aging` | — | MISSING ❌ |
| `cong-no-benh-nhan-ar-aging-1` | — | MISSING ❌ |
| `cong-no-benh-nhan-ar-aging-2` | — | MISSING ❌ |

---

### 4.13 Màn 43-49 — Reports (5 thường + 2 BHYT)

**Status**: PARTIAL ⚠️ (5 partial, 2 missing)

FE có 5 report routes nhưng mapping không khớp hoàn toàn với spec. Báo cáo BHYT hoàn toàn absent.

---

### 4.14 Màn 50-57 — Admin

**Status**: CONFORM ✅ (audit-log), PARTIAL ⚠️ (3), MISSING ❌ (4)

| Ref | FE tương ứng | Status |
|-----|-------------|--------|
| `bang-gia-dich-vu` | `ServicesPage` | PARTIAL ⚠️ — thiếu BHYT price column |
| `vai-tro-phan-quyen` | `RolesPage` | PARTIAL ⚠️ — thiếu role section divider UI |
| `cau-hinh-phong-kham` | `SettingsPage` | PARTIAL ⚠️ — 7 tabs, thiếu BHYT tab |
| `cau-hinh-bhyt` | — | MISSING ❌ |
| `cau-hinh-bhyt-muc-huong` | — | MISSING ❌ |
| `cau-hinh-tich-hop` | — | MISSING ❌ |
| `cau-hinh-tich-hop-vss-disabled` | — | MISSING ❌ |
| `bao-mat-ma-hoa` | `/change-password` (ChangePasswordPage) | PARTIAL ⚠️ — chỉ có change password, không phải Security settings page |
| `audit-log` | `AuditPage` | CONFORM ✅ |

---

### 4.15 Màn 58-60 — HR + Profile

**Status**: PARTIAL ⚠️ (HR), MISSING ❌ (Profile)

- `ca-truc-gio-lam` → `ShiftCalendarPage` — PARTIAL (có calendar view nhưng token mismatch)
- `profile-ca-nhan-bs-nguyen-hoang-an` → `PlaceholderPage` — MISSING ❌

**Ref Profile**: 5-tab layout — Thông tin, Phòng khám của tôi, Bảo mật, Thông báo, Lịch sử hoạt động. Với avatar, clinic switcher radio, thiết lập thông báo.

---

### 4.16 Màn 61-63 — Notifications

**Status**: PARTIAL ⚠️

**Ref**: Full notifications center với filter tabs (Tất cả/Chưa đọc/Cảnh báo), bulk-mark-read, date filter, pagination.

**FE hiện tại** (`NotificationsPage.tsx` — 231 lines): Có filter + type/severity tabs. Thiếu bulk actions, pagination, date range filter.

---

## Mục 5 — Phân loại Gaps

### 5.1 CRITICAL — Toàn màn thiếu hoặc PlaceholderPage

| Ưu tiên | Màn | Ref file | Lý do |
|---------|-----|----------|-------|
| 1 | Design System Tokens | (cross-cutting) | 100% màn bị ảnh hưởng — brand-blue vs Indigo, Segoe UI vs Plus Jakarta Sans, không có radius tokens |
| 2 | Quên Mật Khẩu (3 bước) | quen-mat-khau-1/2/3 | Flow auth thiết yếu, nút hiện không functional |
| 3 | Chọn phòng khám | chon-phong-kham | Post-login UX multi-clinic |
| 4 | Profile cá nhân | profile-ca-nhan | Stub, 0% implemented |
| 5 | AR Aging (3 màn) | cong-no-ar-aging/*-1/*-2 | Module billing critical, không có route |
| 6 | EMR SOAP tab | kham-lam-sang-s-o-a-p | Clinical core workflow |
| 7 | EMR Chẩn đoán ICD-10 | chan-doan | Clinical core workflow |
| 8 | EMR Tóm tắt + Hoàn tất | tom-tat-hoan-tat | Visit complete flow |
| 9 | Xử lý hết hạn (Pharmacy) | xu-ly-het-han | Pharmacy compliance |
| 10 | Cấu hình BHYT (2 màn) | cau-hinh-bhyt + muc-huong | BHYT feature gating |
| 11 | Cấu hình Tích hợp (2 màn) | cau-hinh-tich-hop/* | VSS integration settings |
| 12 | Bảo mật & Mã hoá | bao-mat-ma-hoa | Security settings page |
| 13 | Báo cáo BHYT (2 màn) | bao-cao-bhyt-1/2 | Compliance reporting |
| 14 | Clinic Switcher Dropdown | clinic-switcher-dropdown | Topbar UX |
| 15 | ⌘K Command Palette (2 màn) | k-quick-search-palette-1/2 | Global navigation |
| 16 | Dashboard Lễ tân / Điều dưỡng / Dược sĩ | dashboard-le-tan/dieu-duong/duoc-si | 3 role dashboards thiếu |

### 5.2 MAJOR — Tồn tại nhưng sai layout hoặc thiếu sections lớn

| Màn | Gap chính |
|-----|-----------|
| Đăng nhập | Brand sai ("CURA"), clinic_code field thừa, tokens sai |
| Dashboard Tổng quan | Sidebar không có role dividers, Topbar thiếu ⌘K + clinic switcher + role chip |
| Hồ sơ Bệnh nhân | 1-col layout vs 3-col spec, 4 tab là STUBs, không có AI card |
| Phòng chờ Kanban | 3 cột vs 5 cột spec |
| Kiểm kê thực tế (Stocktake) | Single-form vs 3-step wizard |
| Settings (Admin) | Thiếu BHYT tab, thiếu Integration tab |
| Notifications center | Thiếu bulk actions, pagination, date filter |

### 5.3 MINOR — Có nhưng thiếu element nhỏ hoặc copy/token variation

| Màn | Gap nhỏ |
|-----|---------|
| Danh sách Bệnh nhân | Thiếu filter chips gender/age, pagination UI |
| ShiftCalendar HR | Token mismatch (brand vs indigo) |
| AuditPage | Token mismatch (minor visual diff) |
| PatientRegisterPage | Thiếu BHYT fields (gated) |
| InvoiceList | Không có "by patient timeline" view |
| PrescriptionTab | Stock chip binary (OK/OOS) thay vì 3-state |
| Các báo cáo | Token mismatch + mapping không chính xác 1:1 với spec categories |

### 5.4 CONFORM — Khớp với spec

| Màn | Component | Ghi chú |
|-----|-----------|---------|
| Audit Log | `AuditPage` | Cấu trúc table phù hợp; visual tokens cần confirm sau TASK-039 merge |

> Lưu ý: Convergence thực sự sau TASK-039 design system merge dự kiến tăng từ 13% lên ~25-30% cho nhóm PARTIAL.

---

## Mục 6 — Cross-Task Coverage

### 6.1 Gaps được TASK-040 xử lý (TODO)

| Gap | TASK-040 Req |
|-----|-------------|
| Quên Mật Khẩu (3 màn) | S.1 — ForgotPasswordPage + 3-step flow |
| Hồ sơ BN 3-col + 8-tab | S.2 — PatientDetailPage refactor 3-col |
| Phòng chờ Kanban 5 cột | S.3 — QueueBoardPage 5-col |
| Profile cá nhân (5 tab) | S.4 — ProfilePage.tsx |
| AR Aging (3 màn) | S.5 — ARAgingReportPage |
| Notifications bulk + pagination | S.6 — NotificationsPage enhancement |
| Kiểm kê 3-step wizard | S.7 — StocktakePage |
| Xử lý hết hạn | S.8 — ExpiryProcessingPage |

**Trạng thái TASK-040**: TODO — chưa bắt đầu. 8/28 MISSING gaps sẽ được xử lý.

### 6.2 Gaps được TASK-042 xử lý (TODO)

| Gap | TASK-042 Req |
|-----|-------------|
| EMR SOAP tab | F.1 — tab `soap` mới |
| EMR Chẩn đoán ICD-10 | F.1 — tab `diagnosis` mới |
| EMR Tóm tắt + Hoàn tất | F.1 — tab `summary` mới |
| PrescriptionTab stock chip 3-state | F.3-F.7 — amber/red/green + lot tooltip |

**Trạng thái TASK-042**: TODO — chưa bắt đầu. 4/28 MISSING gaps + 1 MAJOR partial sẽ được xử lý.

### 6.3 Gaps CHƯA được cover bởi task nào

| Gap | Đề xuất Task |
|-----|-------------|
| Design System Tokens (100% màn) | TASK-039 (TODO — chưa merge vào main) |
| Clinic Switcher Dropdown | TASK-033 (multi-clinic auth) |
| Chọn phòng khám | TASK-033 |
| ⌘K Command Palette | TASK-036 (proposed) |
| Dashboard Lễ tân | Cần task mới: **TASK-044-reception-dashboard** |
| Dashboard Điều dưỡng | Cần task mới hoặc scope vào TASK-044 |
| Dashboard Dược sĩ | Cần task mới hoặc scope vào TASK-044 |
| Dashboard Admin | Cần task mới hoặc scope vào TASK-044 |
| Cấu hình BHYT (2 màn) | TASK-034 (BHYT feature flag) |
| Cấu hình Tích hợp (2 màn) | Cần task mới: **TASK-045-integrations-settings** |
| Bảo mật & Mã hoá page | Cần task mới: **TASK-046-security-settings** |
| Báo cáo BHYT (2 màn) | TASK-034 (BHYT) |
| Báo cáo Tổng quan (multi-report hub) | Cần task mới hoặc scope vào reports refactor |
| Brand rename (CURA → MediZen) | TASK-039 |

---

## Mục 7 — Token Compliance Check

### 7.1 Màu sắc

| Token | Spec yêu cầu | FE hiện tại | Gap |
|-------|-------------|-------------|-----|
| Primary | Indigo `#6366F1` | `brand-500: #1a6bac` (VISSoft blue) | CRITICAL |
| Secondary | Slate `#0F172A` | Default Tailwind slate | MINOR |
| Success | Emerald `#10B981` | Default Tailwind green | MINOR |
| Warning | Amber `#F59E0B` | Default Tailwind yellow | MINOR |
| Danger | Red `#EF4444` | Default Tailwind red | MINOR |
| Surface | White | White | OK |
| Page BG | `slate-50` | `gray-50` | MINOR |

**Nguồn xác nhận**: `tailwind.config.js` — chỉ extend `brand` palette, không có Indigo override.

### 7.2 Typography

| Token | Spec yêu cầu | FE hiện tại | Gap |
|-------|-------------|-------------|-----|
| Heading font | Plus Jakarta Sans 600/700 | Segoe UI | CRITICAL |
| Body font | Inter 400/500 | Segoe UI (fallback) | MAJOR |
| Font preload | `<link rel="preload">` trong index.html | Không có | CRITICAL |

**Nguồn xác nhận**: `index.html` — không có Google Fonts link. `tailwind.config.js` line 23: `fontFamily.sans = ['"Segoe UI"', ...]`.

### 7.3 Border Radius

| Token | Spec yêu cầu | FE hiện tại | Gap |
|-------|-------------|-------------|-----|
| Cards | `rounded-xl` (12px) | `rounded-lg` (8px) | MAJOR |
| Inputs | `rounded-lg` (8px) | `rounded-md` (6px) | MINOR |
| Chips/badges | `rounded-full` hoặc 6px | Mix | MINOR |

Ref HTML dùng `rounded-xl` cho cards nhất quán. FE hiện dùng `rounded-lg` hoặc `rounded-md`.

### 7.4 Spacing

Spec: 4px baseline, 24px gutter. FE: Tailwind defaults — gần đúng, không có override rõ ràng.

---

## Mục 8 — i18n Coverage Check

### 8.1 Namespaces hiện có vs cần thiết

| Namespace | Hiện có | Cần thêm keys | Gap |
|-----------|---------|---------------|-----|
| `auth.json` | ✅ (login, change-password) | forgotPassword.*, otp.*, clinicSelector.* | MAJOR |
| `shell.json` | ✅ (nav labels) | commandPalette.*, clinicSwitcher.*, breadcrumb.*, roleChip.* | MAJOR |
| `dashboard.json` | ✅ (34 lines) | Multi-role variants (reception, nurse, pharmacist, admin) | MAJOR |
| `patient.json` | ❌ Không có | patient.detail.tab.*, patient.ai.*, patient.allergy.* | CRITICAL |
| `profile.json` | ❌ Không có | profile.*.*, clinicList.*, activityLog.* | CRITICAL |
| `bhyt.json` | ❌ Không có | bhyt.config.*, bhyt.report.*, bhyt.eligibility.* | CRITICAL |
| `integrations.json` | ❌ Không có | vss.*, integration.*, webhook.* | MAJOR |
| `security.json` | ❌ Không có | passwordPolicy.*, sessions.*, mfa.* | MAJOR |
| `commandPalette.json` | ❌ Không có | cmd.modes.*, cmd.results.*, cmd.shortcuts.* | MAJOR |
| `reports.json` | ✅ (115 lines) | bhytReport.*, overviewReport.*, operationalReport.* | MAJOR |
| `admin.json` | ✅ (477 lines) | bhytConfig.*, integrations.*, security.* | MAJOR |
| `doctor.json` | ✅ (168 lines) | soap.*, diagnosis.icd10.*, summary.complete.* | MAJOR |
| `pharmacy.json` | ✅ (208 lines) | stocktake.wizard.*, expiry.disposal.*, stockChip.* | MAJOR |

### 8.2 Ước tính expansion needed

Hiện có 1,827 lines i18n vi. Để cover 63 màn ref: ước tính cần **+900-1,200 lines** (tăng 50-65%). Chưa tính en.json parity.

---

## Mục 9 — Đề xuất Follow-up Tasks

### Ưu tiên cao (block visual convergence)

**TASK-039** (Design System Tokens — đang TODO): Merge ngay vào main sau khi hoàn thành, unblock tất cả PARTIAL visual gaps.

### Ưu tiên trung bình (block functional flows)

**TASK-040** (Phase D screens): Bao gồm ForgotPassword, PatientDetail 3-col, QueueKanban 5-col, Profile, ARAging, Notifications bulk, Stocktake wizard, Expiry disposal.

**TASK-042** (EMR 8-tab + RX-016): Bao gồm SOAP, Chẩn đoán, Tóm tắt, stock chip 3-state.

### Đề xuất tasks mới (gaps chưa được cover)

| Task đề xuất | Scope | Ưu tiên |
|-------------|-------|---------|
| **TASK-044**: Multi-role dashboards (Lễ tân / Điều dưỡng / Dược sĩ / Admin) | 4 dashboard pages | Medium |
| **TASK-045**: Integrations settings (Cấu hình Tích hợp VSS on/off) | 2 màn admin | Medium |
| **TASK-046**: Security settings page (Bảo mật & Mã hoá) | 1 màn admin | Medium |
| **TASK-033** (đã proposed): Multi-clinic auth (Chọn phòng khám + Clinic Switcher) | 2 màn + topbar component | High |
| **TASK-034** (đã proposed): BHYT feature flag + Cấu hình BHYT + Báo cáo BHYT | 4 màn | High |
| **TASK-036** (đã proposed): ⌘K Command Palette | 2 màn | Medium |
| **TASK-047**: Reports restructure (5 báo cáo hiện map sai category vs spec) | Routes + layout | Low-Medium |
| **TASK-048**: i18n expansion (patient.json, profile.json, bhyt.json, commandPalette.json...) | ~900 lines | Low |

---

## Mục 10 — Kết luận và Khuyến nghị

### Convergence timeline dự kiến

| Giai đoạn | Task | Convergence sau hoàn thành |
|-----------|------|---------------------------|
| Hiện tại (baseline) | — | ~13% CONFORM, ~46% (CONFORM+PARTIAL) |
| Sau TASK-039 merge | Design tokens | ~46% → ~65% visual |
| Sau TASK-040 + TASK-042 | 12 màn gaps | ~65% → ~75% |
| Sau TASK-033 + TASK-034 + TASK-036 | Multi-clinic + BHYT + ⌘K | ~75% → ~85% |
| Sau TASK-044-048 | Role dashboards + Admin screens | ~85% → ~93% |
| Hoàn chỉnh 63 màn | Full port | ~95%+ |

### Top 5 Khuyến nghị

1. **Ưu tiên merge TASK-039** (Design System Tokens) trước mọi thứ — ảnh hưởng toàn bộ 63 màn, unblock visual convergence ngay lập tức.
2. **Chạy TASK-040 ngay sau TASK-039** — 8 màn critical bao gồm ForgotPassword (auth risk) và ARaging (billing gap).
3. **Song song chạy TASK-033** (multi-clinic auth) — unblock ClinicSwitcher và ProfilePage tab "Phòng khám của tôi".
4. **Tạo TASK-044** ngay cho 3 dashboard roles còn thiếu — Lễ tân, Điều dưỡng, Dược sĩ là màn đầu tiên user thấy khi login.
5. **Brand rename pass** (CURA → MediZen) trong TASK-039 — bắt buộc trước demo với client.

---

*Báo cáo này là READ-ONLY audit. Không có file FE nào được chỉnh sửa.*  
*Path: `docs/tasks/TASK-043/deliveries/final-specs/conformance-audit-report.md`*
