# TASK-053 — Functional Audit: FE ↔ BE (clinic-cms-web ↔ clinic-cms-merge)

> **Ngày**: 2026-05-30 · **FE** `clinic-cms-web` @ `main` (`:1420`) · **BE** `clinic-cms-merge` (`:8001`, alembic `0036_super_admin`, **159 path** trong openapi)
> **Phương pháp**: grep mọi call-site `/api/v1/*` trong FE (loại test) → đối chiếu với `openapi.json` của BE (nguồn xác thực route đã đăng ký).
> **Lưu ý kỹ thuật**: BE có **auth middleware global** → mọi request `/api/v1/*` chưa auth trả **401 trước cả routing** (kể cả route không tồn tại). ⇒ KHÔNG thể dùng HTTP probe để phân biệt missing/exist; **openapi.json là nguồn xác thực duy nhất**.
>
> ✅ **Đã runtime-verify** (Playwright, 5 role, 42 screenshot) → `../test-reports/runtime-verification.md`. Runtime làm lộ thêm phát hiện **mock-fallback im lặng** (§5).

---

## 1. Kết luận nhanh

- ✅ **Phần lớn module FE đã wire API thật** — không còn mock data trong production code. File mock duy nhất (`src/modules/admin/mockData.ts`) chỉ import trong `admin.test.tsx` (test-only).
- ⚠️ **7 nhóm FE→BE GAP/DRIFT đã xác nhận** — FE gọi endpoint mà BE merge **chưa đăng ký** (xem §3). Đây là các "merge-time stub" / FE đi trước BE, trùng khớp 63 GAP của TASK-052.
- ℹ️ Các `PendingBEState` / `DevPlaceholder` trong `PatientDetailPage` là **fallback có chủ ý** (graceful degradation khi BE lỗi/chưa có), không phải fake data hiển thị như thật.

---

## 2. FE module → endpoint (real/mock)

| FE module / page | Endpoint BE gọi | Trạng thái |
|---|---|---|
| **auth** (Login/Mfa/ForgotPwd/ChangePwd/ClinicSelector) | `/auth/login` `/refresh` `/logout` `/change-password` `/select-clinic` `/clinics` `/clinics/{id}/default` `/fingerprints` `/mfa/{enroll,verify,challenge,disable,backup-codes/regenerate}` | REAL (1 GAP: password-reset — §3.1) |
| **dashboard** (`modules/dashboard/api.ts`) | `/reports/snapshots` `/reports/inventory-status` `/reports/revenue` `/reports/visit-volume` `/notifications/unread-count` | REAL |
| **patients** (List/Detail/Register/Merge) | `/patients` `/patients/{id}` `/patients/search` `/patients/merge` `/prescriptions` `/invoices` | REAL (Detail dùng PendingBEState fallback) |
| **appointments** | `/appointments` (+ slots/cancel/check-in/confirm) | REAL |
| **doctor / EMR** (`modules/doctor/api.ts`) | `/vitals/definitions` `/visits/{id}/vitals` `/medicines/search` `/visits/{id}/prescriptions` `/prescriptions/{id}` `/prescriptions/{id}/print` | REAL (1 DRIFT/BUG-003 — §3.6) |
| **pharmacy** (Pending/Substitute/Inventory/Adjustments/PurchaseIn) | `/pharmacy/pending-dispense` `/pharmacy/substitute-batch` `/inventory/items` `/inventory/adjustments` `/inventory/purchase-in` `/medicines` | REAL |
| **pharmacy** (Stocktake/Expiry) | `/inventory/stocktake` `/inventory/batches` `/inventory/batches/dispose` | ⚠️ 2 GAP — §3.3, §3.4 |
| **billing** (InvoiceList/Detail/Generate) | `/invoices` `/invoices/{id}` `/invoices/{id}/{payments,print,void,refund,submit}` | REAL |
| **hr** (Schedule/Leave/TimeLog/Attendance) | `/shifts` `/shift-templates` `/recurring-schedules` `/leave-requests` `/attendance` `/attendance/{check-in,check-out,export,me}` `/hr/timesheet` | REAL |
| **reports** (`modules/reports/api.ts` + pages) | `/reports/revenue` `/inventory-status` `/doctor-performance` `/visit-volume` `/prescription-breakdown` | REAL |
| **reports** (ARAging) | `/reports/ar-aging` `/reports/ar-aging/export` | ⚠️ GAP — §3.2 |
| **reports** (BHYT) | `/bhyt/funnel` `/bhyt/sync-status` | REAL (⚠️ lệch naming — §3.7) |
| **admin** (Users/Roles/Settings/Vitals/Services/Medicines/Audit) | `/users` `/roles` `/permissions` `/clinics/me/settings` `/vitals/definitions` `/services` `/medicines` `/admin/audit-logs` `/onboarding/*` `/settings/bhyt` | REAL |
| **admin** (VSS integration) | `/integrations/vss/status` `/integrations/vss/sync-log` · `/admin/integrations/vss/config` | REAL + ⚠️ 1 GAP — §3.5 |
| **notifications** | `/notifications` `/unread-count` `/{id}/read` `/{id}/dismiss` `/mark-all-read` | REAL |
| **search / command palette** | `/search` `/icd10/search` | REAL |
| **sync** (offline mirror — `src/sync/engine.ts`) | `/sync/changes` + generic `/{entity}` CRUD | ⚠️ GAP — §3.8 (sync layer chưa lên merge) |

---

## 3. FE → BE GAP/DRIFT đã xác nhận (FE gọi, BE chưa đăng ký trong openapi)

| # | Endpoint FE gọi | Call-site FE | BE có? | Phân loại |
|---|---|---|---|---|
| 3.1 | `POST /api/v1/auth/password-reset/request` | `pages/auth/ForgotPasswordPage.tsx:48` | ❌ (auth có change-password nhưng KHÔNG có password-reset) | **GAP** — màn Quên mật khẩu không hoạt động end-to-end |
| 3.2 | `GET /api/v1/reports/ar-aging` + `/ar-aging/export` | `pages/reports/ARAgingReportPage.tsx:156,191` | ❌ (reports có revenue/inventory-status/doctor-performance/visit-volume/prescription-breakdown/snapshots/bhyt-summary) | **GAP** — báo cáo công nợ chưa có API |
| 3.3 | `GET/POST /api/v1/inventory/stocktake` | `pages/pharmacy/StocktakePage.tsx:134` | ❌ (inventory không có stocktake) | **GAP** — màn Kiểm kê chưa có API |
| 3.4 | `POST /api/v1/inventory/batches/dispose` | `pages/pharmacy/ExpiryProcessingPage.tsx:234` | ❌ (chỉ có `/batches`, `/batches/{id}`) | **GAP** — xử lý huỷ lô hết hạn chưa có API |
| 3.5 | `GET/PUT /api/v1/admin/integrations/vss/config` | `pages/admin/VssIntegrationConfigPage.tsx:114` | ❌ (BE có `/integrations/vss/{status,sync-log,eligibility-check,submit-claim}` — KHÔNG có `/config`, KHÔNG có prefix `/admin`) | **GAP/DRIFT** — lưu cấu hình VSS chưa có API đúng path |
| 3.6 | `GET /api/v1/visits/{id}/prescriptions` (→405) & fallback `GET /api/v1/prescriptions?visit_id=` | `modules/doctor/api.ts:157-164` (BUG-003 đã ghi nhận trong code) | ⚠️ `/visits/{id}/prescriptions` tồn tại nhưng **405** cho GET; **không có** collection `GET /prescriptions` | **DRIFT/BUG** — đọc đơn thuốc theo visit lỗi method; FE đã có fallback + empty-state |
| 3.7 | BHYT report: FE dùng `/bhyt/funnel` + `/bhyt/sync-status` | `pages/reports/BhytReportPage.tsx:56-57` | ✅ cả hai có; nhưng BE **cũng** expose `/reports/bhyt/summary` mà FE **không** dùng | **DRIFT (naming)** — verify FE dùng đúng endpoint định hướng |
| 3.8 | `GET /api/v1/sync/changes` + push `/{entity}` CRUD | `src/sync/engine.ts` (offline mirror) | ❌ không có `/sync/*` trên merge | **GAP** — tầng sync offline (TASK-016/017) chưa merge vào main |

> 3.1–3.5 trùng với các **"merge-time stub"** đã ghi nhận ở TASK-044/045/046 và **63 GAP** của TASK-052. FE được dựng trước, BE chưa build endpoint tương ứng.

---

## 4. BE-only — endpoint BE có, FE (clinic-cms-web) chưa tiêu thụ

| Nhóm BE | Endpoint | Ghi chú |
|---|---|---|
| **superadmin** (9) | `/superadmin/{accounts,clinics,roles,permissions,stats,audit-logs,...}` | Platform-level — clinic-cms-web KHÔNG có UI superadmin (đúng thiết kế; superadmin là app/portal riêng) |
| **admin audit chain** | `/admin/audit/verify-chain` | TASK-037 hash-chain verify — FE chưa có nút verify |
| **patients PII** | `/patients/{id}/erase`, `/erase/request`, `/patients/guardians/{rel_id}` | Erasure (TASK-038/046) — verify FE TenantErasure/Guardian đã wire chưa |
| **visits EMR** | `/visits/{id}/{soap,diagnosis,services,complete-emr,start,mark-paid}`, `/visit-services/{id}/{cancel,price}`, `/visits/call-next`, `/visits/queue` | EMR tabs FE có gọi soap/diagnosis/services? Cần verify từng tab (ConsultationPage) khớp đủ |
| **invoices** | `/invoices/{id}/{void,refund,submit}`, `/invoice-lines/{id}`, `/payments/{id}/void` | Verify FE InvoiceDetail có nút void/refund/submit |
| **medicines** | `/medicines/{id}/lots`, `/medicines/{id}/substitutes` | Dùng ở EMR/pharmacy — verify |
| **reports** | `/reports/bhyt/summary` | FE dùng `/bhyt/*` thay vì cái này (xem 3.7) |
| **onboarding** | `/onboarding/{services,users,shifts,inventory-csv,info}` | Wizard onboarding — verify đủ bước |

> *Danh sách BE-only mang tính cảnh báo* — cần verify từng cái ở bước runtime (một số có thể FE đã gọi qua path động mà grep tĩnh không bắt được).

---

## 5. Mock / placeholder còn wired vào màn hình

> ⚠️ **CẬP NHẬT sau runtime verify (xem `../test-reports/runtime-verification.md`)**: nhận định ban đầu "chỉ có mockData.ts test-only" là **SAI/thiếu**. Runtime cho thấy có **mock inline trong 5 page production** dạng **fallback im lặng** — màn trông chạy OK nhưng số liệu/kết quả là bịa khi BE 404. Đây là phát hiện nặng (đánh lừa demo).

| File:line | Loại | Đánh giá |
|---|---|---|
| `pages/reports/ARAgingReportPage.tsx:55,158` | `MOCK_DATA` trả về khi `/reports/ar-aging` 404 | 🔴 **FULL-MOCK** — runtime hiển thị 30.1M công nợ **bịa** + chart + bảng (ảnh `25`) |
| `pages/auth/ForgotPasswordPage.tsx:55,63` | coi 404 = success | 🔴 Hiện "thành công" dù BE chưa có (lý do tránh email-enum, nhưng che gap) |
| `pages/pharmacy/StocktakePage.tsx:140` | giả success khi submit | 🟠 Prep load thật (`/inventory/items`); **submit `/inventory/stocktake` giả OK** |
| `pages/pharmacy/ExpiryProcessingPage.tsx:236` | giả success khi dispose | 🟠 Đọc batches thật; **dispose `/inventory/batches/dispose` giả OK** |
| `pages/doctor/DoctorDashboardPage.tsx:122` | mock weekly chart hardcoded | 🟠 Chart tuần dùng số cứng |
| `src/modules/admin/mockData.ts` (`MOCK_VITALS`,`MOCK_SETTINGS`) | Mock data | ✅ Chỉ test (`tests/admin/admin.test.tsx`) |
| `PatientDetailPage.tsx` — `PendingBEState`/`DevPlaceholder` (bhyt tab) | Fallback/stub có chủ ý | ⚠️ Hiển thị khi query lỗi/chưa có; tab BHYT còn stub |

> **Khoản nợ kỹ thuật**: khi BE endpoint lên (TASK-041/follow-up), phải **gỡ MOCK_DATA + bỏ giả-success** để lỗi thật nổi lên, tránh "demo nhìn tưởng đã chạy".

---

## 6. Trạng thái tích hợp theo module

| Module | Status | Ghi chú |
|---|---|---|
| auth | 🟢 REAL | trừ ForgotPassword (3.1 GAP) |
| dashboard (5 role + multi-role) | 🟢 REAL | qua reports/notifications API |
| patients (list/detail/register/merge) | 🟢 REAL | tab BHYT stub; prescriptions/invoices dùng fallback (3.6) |
| appointments / queue | 🟢 REAL | |
| doctor / EMR | 🟡 PARTIAL | BUG-003 đọc đơn thuốc (405 + fallback); verify đủ tab soap/diagnosis/services wire BE |
| pharmacy (dispense/substitute/inventory/adjust/purchase-in) | 🟢 REAL | |
| pharmacy (stocktake / expiry) | 🔴 NO-API | 3.3, 3.4 — FE xong, BE thiếu endpoint |
| billing | 🟢 REAL | verify nút void/refund/submit |
| hr | 🟢 REAL | |
| reports (revenue/inventory/doctor-perf/visit-volume/prescriptions) | 🟢 REAL | |
| reports (ar-aging) | 🔴 FULL-MOCK | 3.2 — BE thiếu; FE **fallback MOCK_DATA im lặng** (runtime hiện số bịa, ảnh `25`) |
| reports (bhyt) | 🟡 PARTIAL | 3.7 lệch naming endpoint |
| admin (users/roles/settings/vitals/services/medicines/audit) | 🟢 REAL | |
| admin (VSS config) | 🟡 PARTIAL | đọc status/log REAL; lưu config thiếu API (3.5) |
| notifications | 🟢 REAL | |
| sync (offline mirror) | 🔴 NO-API | 3.8 — chưa merge vào main |
| superadmin | ⚪ N/A | không có UI ở clinic-cms-web (đúng thiết kế) |

---

## 7. Đề xuất follow-up (tách sub-task — KHÔNG implement trong TASK-053)

**BE endpoint cần build (FE đã sẵn UI)** — gộp với 63 GAP của TASK-052:
1. `POST /auth/password-reset/{request,confirm}` (3.1)
2. `GET /reports/ar-aging` + `/export` (3.2)
3. `GET/POST /inventory/stocktake` (3.3)
4. `POST /inventory/batches/dispose` (3.4)
5. `GET/PUT /integrations/vss/config` (chuẩn hoá path — 3.5)
6. Fix BUG-003: cho phép `GET /visits/{id}/prescriptions` (bỏ 405) hoặc thêm collection `GET /prescriptions?visit_id=` (3.6)

**FE cần verify/sửa nhẹ:**
7. BHYT report: thống nhất dùng `/reports/bhyt/summary` hay `/bhyt/*` (3.7)
8. Tab BHYT PatientDetail + Profile info/notifications: hoàn thiện (đang stub)

**Runtime verify (bước kế của TASK-053):** đăng nhập theo từng role, chụp screenshot, kiểm network thực tế (Playwright) để xác nhận BE-only endpoints §4 thực sự được/không được FE gọi.

---

*Nguồn: grep call-site FE (`src/**`, loại `tests/`) + `openapi.json` BE (159 path). Cross-ref: TASK-052 api-mapping (63 GAP), TASK-044/045/046 merge-time stubs.*
