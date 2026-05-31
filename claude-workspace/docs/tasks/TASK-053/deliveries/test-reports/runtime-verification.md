# TASK-053 — Runtime Verification Report (Playwright)

> **Ngày**: 2026-05-30/31 · **Môi trường**: FE Vite dev `:1420` (browser, KHÔNG Tauri) → proxy BE `clinic-cms-merge` `:8001` · **Công cụ**: Playwright MCP (`--isolated --headless`)
> **Đăng nhập**: 5 role demo (admin/doctor/nurse/receptionist/pharmacist) — seed `seed_demo_data.py`. DB có data thật (47 BN, thuốc, hoá đơn…).
> **42 screenshot** lưu cùng thư mục này (`NN-*.png`).

---

## 1. Phát hiện QUAN TRỌNG — Mock-fallback im lặng (che giấu BE thiếu)

Khi chạy runtime, nhiều màn **trông hoạt động đầy đủ** nhưng thực chất FE **tự fallback sang mock / giả success** khi BE endpoint trả 404. Đây là phát hiện nặng hơn "màn lỗi" vì nó **đánh lừa** người xem demo. Pattern: `catch { return MOCK_DATA }` hoặc coi 404 = success.

| Màn | File:line | Hành vi runtime | Bằng chứng |
|---|---|---|---|
| **Báo cáo Công nợ AR** | `ARAgingReportPage.tsx:55,158-159` | Hiển thị **số liệu bịa** (15.2M/8.5M/4.3M/2.1M = 30.1M) + chart + bảng — `MOCK_DATA` trả về khi `/reports/ar-aging` 404 | `25-reports-ar-aging-GAP.png` |
| **Quên mật khẩu** | `ForgotPasswordPage.tsx:55,63` | Hiện **"thành công"** dù `/auth/password-reset/request` 404 (cố ý tránh email enumeration, nhưng cũng che việc BE chưa có) | `32-forgot-password-GAP.png` |
| **Kiểm kê kho** | `StocktakePage.tsx:140` | Bước Chuẩn bị load thật (77 mặt hàng từ `/inventory/items`); bước **Submit giả success** khi `/inventory/stocktake` không có | `10-pharmacy-stocktake-GAP.png` |
| **Xử lý hết hạn** | `ExpiryProcessingPage.tsx:236` | Đọc batches thật; **dispose giả success** khi `/inventory/batches/dispose` không có | `11-pharmacy-expiry-GAP.png` |
| **Dashboard Bác sĩ** | `DoctorDashboardPage.tsx:122` | Chart "tuần" dùng **mock hardcoded** (chưa có API) | `34-doctor-dashboard.png` |

> ⚠️ **Sửa lại nhận định trong functional-audit.md §5 (bản đầu)**: KHÔNG chỉ có `mockData.ts` (test-only). Có **mock inline trong 5 page production** dưới dạng fallback im lặng. Phải coi đây là khoản nợ kỹ thuật: khi BE endpoint lên (TASK-041/follow-up), cần **gỡ MOCK_DATA + bỏ giả-success** để lỗi thật nổi lên.

---

## 2. Màn render OK với data thật (BE có endpoint)

| Nhóm | Màn | Ghi chú |
|---|---|---|
| Auth | Login (`01`) | form chuẩn, không có field clinic_code (đúng spec) |
| Dashboard | Admin (`02`), Doctor (`34`), Reception (`40`), Pharmacist (`41`), Nurse (`42`) | role-aware, KPI render |
| Reception | Patients list (`03`, 47 BN thật), Register (`04`), Queue board (`05`), Appointments (`06`) | |
| Patient | Detail 8-tab (`33`) | tabs đủ; một số tab fallback `PendingBEState` |
| Pharmacy | Pending (`08`), Inventory (`09`), Adjustments (`12`), Purchase-in (`13`), Substitute (`14`) | |
| Billing | Invoices list (`07`) | |
| HR | Schedule (`15`) | |
| Admin | Users (`16`), Roles (`17`), Settings (`18`), Services (`19`), Medicines (`20`), Vitals (`21`), Audit (`22`), VSS config (`23`) | |
| Reports | Revenue (`24`), Doctor-perf (`26`), Visit-volume (`27`), Inventory (`28`), Prescriptions (`29`) | |
| EMR | Consultation (`38`), tab Kê đơn (`39`) | visit tạo runtime `#20260530-001` |
| Khác | Notifications (`30`), Profile (`31`), Doctor queue empty→withPatient (`36`,`37`) | |

---

## 3. Console errors — phân tích

Số "errors" tăng dần (lên ~190+) là do **MỘT lỗi lặp lại**:
```
[useSync] Sync error: Failed to load Tauri SQL plugin. Ensure app is running in Tauri context.
  at getDb (src/sync/database.ts:96) → pushChanges (engine.ts:125) → syncAll (engine.ts:195) → useSync.ts:37
```
- **Nguyên nhân**: chạy trong **browser thuần** (Vite), không phải Tauri shell → `@tauri-apps/plugin-sql` không load. Hook `useSync` fire mỗi ~30s → tích luỹ lỗi.
- **KHÔNG phải bug từng trang.** Khớp finding functional-audit §3.8 (sync offline cần Tauri + BE `/sync/*`).
- Trên status bar còn hiện icon ⚠️ "Sync error" tooltip (thấy ở mọi trang) — **UX nên ẩn/giảm nhẹ cảnh báo sync khi chạy ngoài Tauri**, vì hiện tại lộ lỗi kỹ thuật cho user.

---

## 4. Kết luận runtime

- **UI/UX**: tất cả route đã implement render đúng layout MediZen (teal, sidebar multi-role, typography 15px, vi default) — khớp ui-ux-audit static.
- **Functional**: xác nhận 7 nhóm gap; nhưng **làm rõ** rằng phần lớn gap được FE **che bằng mock/giả-success** (mục §1) thay vì lỗi lộ rõ → rủi ro "demo nhìn xong tưởng đã chạy".
- **Khuyến nghị bổ sung**:
  1. Lập checklist "gỡ mock-fallback" gắn với từng follow-up BE endpoint (ARAging, stocktake, expiry-dispose, forgot-password, doctor weekly chart).
  2. Ẩn/làm dịu cảnh báo `useSync` khi không ở Tauri context (hoặc disable hook trong web mode).
```
