# Task Tracking Dashboard

**Last Updated**: 2026-07-24 (auto-generated; TASK-107 added to Completed)

> **⚠️ Note**: This file is auto-generated. Do not edit manually.
> To update task status, use: `/task-status TASK-ID STATUS`
> To create new tasks, use: `/task-create TASK-ID "Title" Priority Type`

---

## Statistics

| Metric | Count |
|--------|-------|
| **Total Tasks** | 97 |
| **TODO** | 11 |
| **IN_PROGRESS** | 10 |
| **IN_REVIEW** | 2 |
| **IN_TESTING** | 1 |
| **DOCUMENTING** | 0 |
| **BLOCKED** | 1 |
| **DONE** | 79 |

### By Priority

- **High**: 65 tasks
- **Medium**: 27 tasks
- **Low**: 4 tasks

### By Agent

- **Code Implementation Agent**: 7 tasks (TASK-053, TASK-085, TASK-086, TASK-087, TASK-088, TASK-089, TASK-090)
- **Code Review Agent**: 1 tasks (TASK-039b)
- **Documentation Agent**: 17 tasks (TASK-016, TASK-064, TASK-065, TASK-066, TASK-067, TASK-070, TASK-079, TASK-080, TASK-082, TASK-083, TASK-084, TASK-092, TASK-093, TASK-094, TASK-096, TASK-099, TASK-101)
- **None**: 6 tasks (TASK-009, TASK-018, TASK-020, TASK-025, TASK-075, TASK-076)
- **Test Agent**: 2 tasks (TASK-077, TASK-081)
- **Unassigned**: 18 tasks (TASK-012, TASK-019, TASK-048, TASK-050, TASK-054, TASK-055, TASK-056, TASK-057, TASK-058, TASK-059, TASK-060, TASK-061, TASK-063, TASK-068, TASK-069, TASK-071, TASK-072, TASK-073)
- **chiendv**: 28 tasks (TASK-008, TASK-010, TASK-011, TASK-013, TASK-015, TASK-023, TASK-024, TASK-027, TASK-029, TASK-030, TASK-031, TASK-032, TASK-033, TASK-034, TASK-035, TASK-036, TASK-037, TASK-038, TASK-039, TASK-039c, TASK-040, TASK-041, TASK-042, TASK-043, TASK-044, TASK-052, TASK-062, TASK-091)
- **claude-main**: 1 tasks (TASK-049)
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

- **[TASK-107](tasks/TASK-107/task.md)** - [High] Bất biến phiên/RBAC: vô hiệu hóa tài khoản, đổi mật khẩu, thu hồi role đều KHÔNG chấm dứt quyền
  - **Completed**: 2026-07-24
  - **Note**: Security fix (H-5/H-6/H-7 from E2E TASK-095). Version-check via `user.tokens_valid_after` (migration 0067) + Redis fast-path `sess:cutoff:{uid}`. H-5: deactivation revokes access token. H-6: password change/reset invalidates all sessions. H-7: role revoke syncs pivot + removes permission. 3/3 acceptance tests pass. Zero new regressions. Functional spec documented.

- **[TASK-106](tasks/TASK-106/task.md)** - [High] Report doctor-performance nhân bản Cartesian (over-count visits/revenue)
  - **Completed**: 2026-07-24
  - **Note**: Bug H-4 (E2E TASK-095). Fixed Cartesian product via CTEs pre-aggregating invoices/prescriptions → 1:1 join to visits. Visits_count/revenue now distinct, not inflated. 51/51 tests pass (13 integration reports + 6 unit + 32 other report tests).

- **[TASK-105](tasks/TASK-105/task.md)** - [High] Refund không đảo payment → report payment-methods đếm tiền đã-thu vĩnh viễn sai
  - **Completed**: 2026-07-24
  - **Note**: Bug H-3 (E2E TASK-095). Approach A: refund voids related payments (mirrors void_payment logic). Paid_total/balance_due reset to 0/grand_total. Payment-methods == revenue (reconciled). 81/81 tests pass (billing + reports).

- **[TASK-104](tasks/TASK-104/task.md)** - [High] substitute_batch cho phép thay sang lô ĐÃ HẾT HẠN (bỏ qua FEFO)
  - **Completed**: 2026-07-24
  - **Note**: Bug H-2 (E2E TASK-095). Guard: expiry_date <= today → 409. Mirrors reserve_for_prescription guard. TASK-099 same-medicine guard intact. 22/22 tests pass (pharmacy integration + unit).

- **[TASK-098](tasks/TASK-098/task.md)** - [Critical] DELETE /patients/{id}/erase (NĐ13) luôn 500 và KHÔNG xóa
  - **Completed**: 2026-07-24
  - **Note**: Bug C-3 (E2E TASK-095). Fixed `:param::type` binding → `CAST(:param AS type)`. Cascade prescription via visit_id join. 1/1 integration test passes. Known gap: cascade incomplete for appointment/patient_relation/invoice/visit_exam/visit_service/prescription_item → follow-up task needed for full compliance.

- **[TASK-097](tasks/TASK-097/task.md)** - [Critical] Merge bệnh nhân mồ côi dữ liệu lâm sàng (visit/appointment/đơn/hóa đơn)
  - **Completed**: 2026-07-24
  - **Note**: Bug C-2 (E2E TASK-095). Added visit/appointment to RELATED_PATIENT_TABLES. Safety-net COUNT aborts transaction if orphans remain. 7/7 merge-specific tests pass. Prescription/invoice follow via visit_id (no direct patient_id).

- **[TASK-101](tasks/TASK-101/task.md)** - [Critical] Tạo lịch hẹn (FE) hỏng hoàn toàn — scheduled_at nối chuỗi sai → mọi create 422
  - **Completed**: 2026-07-23
  - **Note**: Bug C-6 (E2E TASK-095). Helper `buildScheduledAt()` fixed string concat → single valid ISO. Week + day view E2E verified live (Playwright 201 Created both flows). 5/5 unit tests pass.

- **[TASK-099](tasks/TASK-099/task.md)** - [Critical] substitute_batch cho phép đổi reservation sang lô của thuốc KHÁC
  - **Completed**: 2026-07-23
  - **Note**: Bug C-4 (E2E TASK-095). Guard rejects cross-medicine batch substitution (409). Allows legitimate FEFO same-medicine swap. 20/20 tests pass (integration + unit).

- **[TASK-096](tasks/TASK-096/task.md)** - [Critical] PATCH /patients/{id} luôn trả HTTP 500 (MissingGreenlet) + sibling dosage-form fix
  - **Completed**: 2026-07-23
  - **Note**: Bug C-1 (E2E TASK-095). Added `await db.refresh()` after flush in patient + dosage-form services → fixes expired `updated_at` MissingGreenlet. 6/6 new/regression tests pass; 99/104 full suite (5 pre-existing flakes).

- **[TASK-092](tasks/TASK-092/task.md)** - Nâng cấp màn hình Super Admin — tập trung quản lý hệ thống, tài khoản, người dùng & cấu hình hệ thống
  - **Completed**: 2026-07-22
  - **Note**: 3-group sidebar reorg + new System Config page (4 tabs: features, security, email, system-info) + backend system-config API + migration 0061. Functional design + API specs documented. All tests PASS (13/13 BE, 6/6 FE, 4/4 E2E).

- **[TASK-094](tasks/TASK-094/task.md)** - Fix prescription printing (default template + diagnosis) & add usage / dosage-unit fields
  - **Completed**: 2026-07-22
  - **Note**: 5 features (A-E) + 2 bug fixes implemented + tested live (87/87 BE, 61/61 FE pass). Functional design + API specs documented.

- **[TASK-091](tasks/TASK-091/task.md)** - Chuẩn hóa toàn bộ danh sách — phân trang cố định + xuất Excel đồng nhất
  - **Completed**: 2026-07-15

- **[TASK-093](tasks/TASK-093/task.md)** - Cảnh báo thuốc/kho phân cấp theo thời gian & số lượng (thuốc → dạng đóng gói → phòng khám)
  - **Completed**: 2026-07-18


---

## Bug Tracking

### Open Bugs (1)

- **[TASK-049](tasks/TASK-049/task.md)** - E2E clinical flow audit (Playwright) — full KCB walkthrough + bug catalog
  - **Priority**: High | **Assigned**: claude-main


---

**💡 Tip**: Click on any task ID to view full details.
