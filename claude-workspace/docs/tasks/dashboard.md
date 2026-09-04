# Task Tracking Dashboard

**Last Updated**: 2026-09-04 21:24:23 (auto-generated)

> **⚠️ Note**: This file is auto-generated. Do not edit manually.
> To update task status, use: `/task-status TASK-ID STATUS`
> To create new tasks, use: `/task-create TASK-ID "Title" Priority Type`

---

## Statistics

| Metric | Count |
|--------|-------|
| **Total Tasks** | 149 |
| **TODO** | 20 |
| **IN_PROGRESS** | 10 |
| **IN_REVIEW** | 4 |
| **IN_TESTING** | 3 |
| **BLOCKED** | 1 |
| **DONE** | 111 |

### By Priority

- **High**: 96 tasks
- **Medium**: 47 tasks
- **Low**: 5 tasks

### By Agent

- **Code Implementation Agent**: 7 tasks (TASK-053, TASK-085, TASK-086, TASK-087, TASK-088, TASK-089, TASK-090)
- **Code Review Agent**: 2 tasks (TASK-039b, TASK-142)
- **Documentation Agent**: 43 tasks (TASK-016, TASK-064, TASK-065, TASK-066, TASK-067, TASK-070, TASK-079, TASK-080, TASK-082, TASK-083, TASK-084, TASK-092, TASK-093, TASK-094, TASK-096, TASK-097, TASK-098, TASK-099, TASK-101, TASK-104, TASK-105, TASK-106, TASK-107, TASK-108, TASK-109, TASK-110, TASK-111, TASK-112, TASK-113, TASK-114, TASK-115, TASK-116, TASK-117, TASK-118, TASK-119, TASK-120, TASK-121, TASK-122, TASK-123, TASK-124, TASK-139, TASK-145, TASK-146)
- **None**: 17 tasks (TASK-009, TASK-018, TASK-020, TASK-025, TASK-075, TASK-076, TASK-125, TASK-126, TASK-127, TASK-128, TASK-129, TASK-131, TASK-132, TASK-134, TASK-135, TASK-136, TASK-137)
- **Test Agent**: 3 tasks (TASK-077, TASK-081, TASK-141)
- **Unassigned**: 28 tasks (TASK-012, TASK-019, TASK-048, TASK-050, TASK-054, TASK-055, TASK-056, TASK-057, TASK-058, TASK-059, TASK-060, TASK-061, TASK-063, TASK-068, TASK-069, TASK-071, TASK-072, TASK-073, TASK-095, TASK-100, TASK-102, TASK-103, TASK-130, TASK-133, TASK-138, TASK-140, TASK-143, TASK-144)
- **chiendv**: 28 tasks (TASK-008, TASK-010, TASK-011, TASK-013, TASK-015, TASK-023, TASK-024, TASK-027, TASK-029, TASK-030, TASK-031, TASK-032, TASK-033, TASK-034, TASK-035, TASK-036, TASK-037, TASK-038, TASK-039, TASK-039c, TASK-040, TASK-041, TASK-042, TASK-043, TASK-044, TASK-052, TASK-062, TASK-091)
- **claude-main**: 2 tasks (TASK-049, TASK-147)
- **code-review-agent**: 1 tasks (TASK-047)
- **test-agent**: 1 tasks (TASK-078)

---

## Active Tasks

### 🔴 High Priority

#### TODO

- **[TASK-054](tasks/TASK-054/task.md)** - Billing correctness — VAT, BHYT split, change-due, VietQR, void→reverse stock, POS/A4 print, manual invoice
  - **Assigned**: Unassigned

- **[TASK-055](tasks/TASK-055/task.md)** - Subscription & clinic lifecycle (provider billing) — model + state machine + guard + admin actions + jobs
  - **Assigned**: Unassigned

- **[TASK-057](tasks/TASK-057/task.md)** - Self-signup & lead funnel — public signup form, email verify, lead management, convert lead→clinic, atomic clinic+admin
  - **Assigned**: Unassigned

- **[TASK-058](tasks/TASK-058/task.md)** - Clinical safety & inventory integrity — allergy warning, partial/reverse dispense, adjustment approval, vital trends, service-doctor map
  - **Assigned**: Unassigned

- **[TASK-061](tasks/TASK-061/task.md)** - Auth & RBAC gaps — clinic-admin password reset, forgot-password, clone-role via API, full SoD coverage
  - **Assigned**: Unassigned

- **[TASK-072](tasks/TASK-072/task.md)** - FE v2.0 UI — Tạo branch và triển khai giao diện mới Indigo Premium
  - **Assigned**: Unassigned
  - **Branch**: `feature/TASK-072-ui-v2-indigo-premium`

- **[TASK-144](tasks/TASK-144/task.md)** - [High] Audit hash chain dùng advisory lock toàn cục — trần mở rộng ~12 phòng khám
  - **Assigned**: Unassigned

#### IN_PROGRESS

- **[TASK-032](tasks/TASK-032/task.md)** - Audit FE + BE theo MediZen Modern design + function list v1.3 — gap analysis + tự tạo sub-tasks + tự implement
  - **Assigned**: chiendv

- **[TASK-043](tasks/TASK-043/task.md)** - FE Stitch conformance audit — clinic-cms-web vs 63 màn HTML reference + E2E test
  - **Assigned**: chiendv

- **[TASK-052](tasks/TASK-052/task.md)** - Tài liệu API mapping theo function list (461 fn × 26 module) + audit gap test toàn bộ BE + fix bug
  - **Assigned**: chiendv
  - **Branch**: `fix/TASK-052-test-encryption-fixtures`

- **[TASK-053](tasks/TASK-053/task.md)** - Khởi động FE + BE(merge), phân tích FE đã đáp ứng UI/UX chưa & rà soát toàn bộ chức năng
  - **Assigned**: Code Implementation Agent

- **[TASK-089](tasks/TASK-089/task.md)** - Quản lý hồ sơ nhân sự — gắn tài khoản, lịch làm việc, chấm công
  - **Assigned**: Code Implementation Agent
  - **Branch**: `feature/TASK-089-staff-management`

- **[TASK-090](tasks/TASK-090/task.md)** - Quên mật khẩu (email) + OTP xác thực qua email
  - **Assigned**: Code Implementation Agent
  - **Branch**: `feature/TASK-090-auth-email`

#### IN_REVIEW

- **[TASK-029](tasks/TASK-029/task.md)** - MediZen UI Phase D — Edit Stitch hiện hữu + sinh ~16 màn mới theo function list v1.3 + SECURITY.md
  - **Assigned**: chiendv

- **[TASK-047](tasks/TASK-047/task.md)** - In phiếu khám + in hóa đơn (FE) — native browser print, A5/A4
  - **Assigned**: code-review-agent
  - **Branch**: `feature/TASK-047-print-receipts`

- **[TASK-141](tasks/TASK-141/task.md)** - Performance test toàn hệ thống — 10 phòng khám chạy song song luồng khám bệnh end-to-end
  - **Assigned**: Test Agent
  - **Branch**: `feature/TASK-141-perf-harness`

#### IN_TESTING

- **[TASK-081](tasks/TASK-081/task.md)** - PHẦN KHÁM BỆNH — form khám lâm sàng động (BT/Bất thường + ghi chú) + seed 13 mục
  - **Assigned**: Test Agent
  - **Branch**: `feature/TASK-081-examination-section`

#### BLOCKED

- **[TASK-050](tasks/TASK-050/task.md)** - Seed data cho các danh mục (services, ICD, drugs, units, etc.)
  - **Assigned**: Unassigned
  - **Branch**: `feature/TASK-050-seed-categories`

### 🟡 Medium Priority

#### TODO

- **[TASK-048](tasks/TASK-048/task.md)** - Rà soát + cleanup các tính năng FE đang gắn nhãn Beta
  - **Assigned**: Unassigned

- **[TASK-056](tasks/TASK-056/task.md)** - Reports dimensions + exports — payment-method/specialty/least-used/cost/no-show/demographic/duration/wait + CSV/PDF + data export (PDPA)
  - **Assigned**: Unassigned

- **[TASK-059](tasks/TASK-059/task.md)** - Appointments completeness + HR shift integration — reschedule, block schedule, HR conflict, smart queue, real slot capacity, no-show grace
  - **Assigned**: Unassigned

- **[TASK-060](tasks/TASK-060/task.md)** - Document storage (S3) & attachments — S3 wiring + patient/visit document upload + clinic logo
  - **Assigned**: Unassigned

- **[TASK-140](tasks/TASK-140/task.md)** - Test infra: fix integration-test fixture teardown bị RLS chặn — rò rỉ clinic/user vào DB e2e
  - **Assigned**: Unassigned

#### IN_PROGRESS

- **[TASK-028](tasks/TASK-028/task.md)** - Landing Page MediZen — Stitch project (design-only deliverable)
  - **Assigned**: Unassigned

- **[TASK-062](tasks/TASK-062/task.md)** - Email infra & event-driven notifications — email provider + transactional/templates + visit-complete/stock-low/sub-expiring notify
  - **Assigned**: chiendv
  - **Branch**: `fix/TASK-052-test-encryption-fixtures`

#### IN_TESTING

- **[TASK-069](tasks/TASK-069/task.md)** - Tag system for medicines and services
  - **Assigned**: Unassigned
  - **Branch**: `feature/TASK-069-tag-system`

### 🟢 Low Priority

#### TODO

- **[TASK-063](tasks/TASK-063/task.md)** - Clinic config & platform-admin completeness — settings (holiday/lunch/prefixes/timezone/language) + platform role CRUD/clinic detail/system config/notes/activity feed
  - **Assigned**: Unassigned

#### IN_PROGRESS

- **[TASK-039c](tasks/TASK-039c/task.md)** - MediZen logo SVG + favicon + Tauri icon — TASK-039 F.8/F.9 follow-up
  - **Assigned**: chiendv
  - **Branch**: `feature/task-039c-logo-favicon`

---

## Completed Tasks

### Recently Completed (Last 7 Days)

- **[TASK-145](tasks/TASK-145/task.md)** - Rà soát + E2E luồng hủy/điều chỉnh hóa đơn & đơn thuốc khi kê nhầm
  - **Completed**: 2026-08-30

- **[TASK-146](tasks/TASK-146/task.md)** - Lịch sử khám hiển thị đầy đủ (kể cả bản ghi đã hủy) + E2E luồng khám sai → hủy → cấp lại
  - **Completed**: 2026-09-01


---

## Bug Tracking

### Open Bugs (10)

- **[TASK-049](tasks/TASK-049/task.md)** - E2E clinical flow audit (Playwright) — full KCB walkthrough + bug catalog
  - **Priority**: High | **Assigned**: claude-main

- **[TASK-095](tasks/TASK-095/task.md)** - Khóa sửa hồ sơ khám đã đóng (COMPLETED/CANCELLED) + sửa luồng hủy → sửa → xuất lại hóa đơn đã thanh toán
  - **Priority**: High | **Assigned**: Unassigned

- **[TASK-100](tasks/TASK-100/task.md)** - [Critical] IDOR liên tenant ở GET/PATCH /admin/clinics/{id} — đọc PII giải mã + sửa phòng khám khác
  - **Priority**: High | **Assigned**: Unassigned

- **[TASK-102](tasks/TASK-102/task.md)** - [Critical] App kết nối Postgres bằng role cms (rolbypassrls=t) — RLS bị bỏ qua toàn bộ runtime
  - **Priority**: High | **Assigned**: Unassigned

- **[TASK-103](tasks/TASK-103/task.md)** - [High] In đơn (server-side) thiếu chẩn đoán + tên bệnh nhân
  - **Priority**: Medium | **Assigned**: Unassigned

- **[TASK-130](tasks/TASK-130/task.md)** - FE: export/download + polling trả 401 sau khi access token hết hạn (không silent-refresh)
  - **Priority**: High | **Assigned**: Unassigned

- **[TASK-133](tasks/TASK-133/task.md)** - FE: tạo ca trùng giờ trả 409 nhưng UI không hiện thông báo lỗi
  - **Priority**: Low | **Assigned**: Unassigned

- **[TASK-142](tasks/TASK-142/task.md)** - [Critical] Dược sĩ cấp phát được đơn thuốc bác sĩ chưa duyệt — pending-dispense không lọc Prescription.status
  - **Priority**: High | **Assigned**: Code Review Agent

- **[TASK-143](tasks/TASK-143/task.md)** - [High] fn_next_patient_code không có khoá — race sinh trùng patient_code trả HTTP 500
  - **Priority**: High | **Assigned**: Unassigned

- **[TASK-147](tasks/TASK-147/task.md)** - FE thiếu bước "bác sĩ gửi đơn" — cấp phát thuốc bị chặn hoàn toàn sau TASK-142
  - **Priority**: High | **Assigned**: claude-main


---

**💡 Tip**: Click on any task ID to view full details.
