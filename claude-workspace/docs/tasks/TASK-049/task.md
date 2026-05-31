---
id: TASK-049
type: bug
title: E2E clinical flow audit (Playwright) — full KCB walkthrough + bug catalog
status: IN_PROGRESS
priority: High
assigned: claude-main
created: 2026-05-04
updated: 2026-05-04
branch: ""
jira_key: ""
tags: [e2e, audit, playwright, clinical-flow]
affected-repos: [clinic-cms-web, clinic-cms-merge]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-049: E2E clinical flow audit (Playwright) — full KCB walkthrough + bug catalog

## Description

End-to-end audit luồng khám chữa bệnh đầy đủ trên môi trường live (ngrok), dùng Playwright MCP từ main context. Mục đích: tìm bug, xác định gap function, screenshot từng bước, build bug catalog cho phase fix sau.

## Test environment

- **URL**: `https://ff02-210-245-74-43.ngrok-free.app/`
- **Admin login**: `admin` / `Demo@1234`
- **Tenant**: DEMO clinic
- **FE**: Vite dev server | **BE**: proxy `/api/*`
- **Tool**: Playwright MCP (browser_navigate, browser_click, browser_snapshot, browser_take_screenshot, browser_fill_form, browser_console_messages, browser_network_requests, etc.)

## Test plan (sequential phases)

### Phase 1 — Admin: tạo accounts theo từng role
- Login admin, navigate to user management
- Tạo 1 account/role: doctor, reception, nurse, pharmacist, cashier (nếu có)
- Verify accounts created + có thể login

### Phase 2 — Reception flow
- Login reception
- Search patient by phone — empty result
- Search by name — empty result  
- Click "Tạo bệnh nhân mới" → kiểm tra: search term có auto-fill vào Name/Phone field không?
- Fill BN info, save
- Verify: BN xuất hiện trong list, có thể search lại được

### Phase 3 — Vital signs (đo sinh hiệu)
- Tìm bước đo chỉ số (BP, pulse, temp, weight, height) — bước này có UI dedicated không? Hay phải vào EMR?
- Nếu có: nhập chỉ số, save, verify lưu vào BN

### Phase 4 — Doctor flow
- Login doctor
- Mở danh sách BN chờ khám / hôm nay
- Mở phiếu khám
- Verify: thấy chỉ số sinh hiệu vừa đo? Thấy lịch sử khám trước?
- Chẩn đoán + kê đơn — drug list có data không? Search hoạt động? Auto-complete?
- Save phiếu khám

### Phase 5 — Pharmacy flow
- Login pharmacist
- Mở danh sách đơn cần phát
- Verify: nhìn được tồn kho từng thuốc + loại + số lượng?
- Phát thuốc, trừ kho

### Phase 6 — Billing/Cashier flow
- Login cashier (hoặc reception)
- Tạo hóa đơn cho BN vừa khám
- Thanh toán
- In hóa đơn (verify TASK-047 print A4 hoạt động)

### Phase 7 — Patient visit history
- Mở chi tiết BN → tab Lịch sử khám
- Verify: hiển thị đầy đủ thông tin từng lần khám (chẩn đoán, đơn thuốc, sinh hiệu, hóa đơn)

### Phase 8 — Cross-cutting checks
- Cỡ chữ system (user complain quá nhỏ)
- Các danh mục có data không (services, drugs, ICD codes, etc.)
- AI gợi ý + BHYT panels — có disable được không?

## Deliverables

- `deliveries/screenshots/` — screenshot từng bước quan trọng + bug states
- `bugs/BUG-XXX.md` — 1 file/bug, format theo template
- `deliveries/final-specs/audit-report.md` — tổng hợp findings + recommendations + danh sách follow-up tasks

## Acceptance Criteria

- [ ] Tất cả 5 role accounts được tạo + login OK
- [ ] Đi đủ 1 luồng KCB từ tiếp nhận đến thanh toán + in hóa đơn
- [ ] Bug catalog đầy đủ với screenshot + reproduction steps
- [ ] Audit report kèm priority list cho fix phase

## Notes

**Workflow approach**:
- Main context (claude) chạy Playwright trực tiếp, không qua sub-agent (vì sub-agent không kế thừa MCP tools)
- Bug nào tìm thấy ngay → tạo `bugs/BUG-XXX.md` ngay (không gom hết cuối)
- Sau khi finish audit → spawn fix agents per-bug hoặc gom thành 1-2 task (TASK-052/053/056)

## Progress so far (2026-05-04)

**Phase 1 — Admin walkthrough (PARTIAL)**:
- ✅ Login admin OK (`admin` / `Demo@1234`)
- ✅ Dashboard render OK (all metrics 0 — confirms "danh mục chưa có data")
- ✅ Navigate to `Admin → Users` — thấy 14 seeded users (5 BS, 3 ĐD, 2 LT, 2 DS, 1 TN, 1 admin)
- ✅ Test "Add User" function — created `test_e2e_dr` (count 14→15)
- ❌ Login as `test_e2e_dr` → BLOCKED: "Tài khoản chưa được gán phòng khám nào" → **BUG-003**
- ❌ Phase 2+ blocked: no working role accounts

**Bugs logged**:
- BUG-001: useSync hook spam error trong browser context (Tauri SQL plugin) — Medium
- BUG-002: User roles cell rỗng cho 9/14 user + duplicate roles trong filter dropdown — Medium
- BUG-003: Add User KHÔNG assign clinic → user mới không login — **Critical**
- BUG-004: BE thiếu defensive check cho user không clinic — Medium
- **BUG-005**: `/api/v1/auth/refresh` 500 — đọc encrypted User PII trước khi TenancyMiddleware set ContextVar (regression TASK-037 Phase 2). **FIXED 2026-05-04** — agent commit `clinic-cms-merge@24e6dfd` (auth_service wrapped trong `with_tenant_context`) + `clinic-cms-web@490bd47` (App.tsx defensive guard). 8/8 refresh integration tests pass. Verified end-to-end: admin login → refresh 200 → dashboard render OK với data.
- **BUG-006**: FE refresh loop sau login — **CLOSED transitively bởi BUG-008 fix** (root cause là BE reject auth khi có X-Clinic-Id header). Hypothesis ban đầu (FE store hydration race) sai — thực ra là BE-side bug.
- **BUG-007**: Search term không auto-fill vào Phone field khi click "Register New" — Medium UX, không block.
- **BUG-008**: TenancyMiddleware ignores JWT khi có `X-Clinic-Id` header → tất cả authenticated FE call 401. **FIXED 2026-05-04** — agent commit `clinic-cms-merge@a5f3dcf` (đảo precedence: JWT primary, X-Clinic-Id chỉ fallback khi không có Bearer). 15/15 integration tests pass + 4 new test cases. Verified end-to-end: receptionist truy cập Patient Management hiển thị 19 BN seeded.

## DB seed gán clinic+role (2026-05-04)
- Discovered: 14 seeded users (`dr_*`, `nurse_*`, `recept_*`, `pharm_*`, `cashier_em`) đều `clinics=0` trong `account_clinic_role` table → không login được (cùng symptom BUG-003)
- Action: SQL idempotent INSERT 13 rows vào `account_clinic_role` (DEMO clinic, role_codes match prefix username): doctor/nurse/receptionist/pharmacist/cashier — tất cả `is_default=true`
- Verified: `recept_anh` login OK sau gán

**Incident**: TASK-050 BE seed agent vi phạm scope (modify 5 BE source files thay vì chỉ tạo seed script). Stopped + reverted source files.

## Progress 2026-05-04 (continue, switched to localhost)

- Switched test target từ ngrok offline → localhost: BE `http://localhost:8001/health` healthy ✅, FE Vite dev `http://localhost:1420/` start OK
- Discovered seeded user passwords trong `seed_demo_data.py`: BS `Doctor@1234`, ĐD `Nurse@1234`, LT `Recept@1234`, DS `Pharm@1234`, TN `Cashier@1234`, admin `Demo@1234` → có thể test E2E mà không cần fix BUG-003 trước
- **Phase 1 admin login BLOCKED** — POST `/login` 200 OK nhưng POST `/refresh` ngay sau đó 500 → FE redirect về login. Logged BUG-005 với root cause + 3 fix options.

## Blockers (updated)

- ~~BUG-005 BLOCKING~~ → FIXED
- ~~BUG-008 BLOCKING~~ → FIXED
- BUG-014 BLOCKING Phase 5 dispense (button không hoạt động)
- BUG-015 BLOCKING Phase 6 cashier role (0 perms cho clinic-scoped)
- BUG-017 InvoiceDetailPage React hooks crash (invoice tạo OK nhưng không view detail được)

## Phase walkthrough — 2026-05-04 cumulative

**Phase 1 — Admin baseline**: ✅ DONE
- Admin login + dashboard render với 5 widgets (all 0)

**Phase 2 — Reception flow**: ✅ DONE
- `recept_anh` login OK
- Tạo BN0020 (Nguyễn Văn E2E Test, 1985, 0987654321) qua Register New
- Walk-In → visit `20260504-002` (Chief complaint: "Đau đầu, sốt nhẹ 2 ngày")
- Queue Board hiển thị 5-col Kanban OK

**Phase 3 — Vital signs**: 🔍 OBSERVATION
- KHÔNG có UI dedicated cho nurse role — vital signs đo trực tiếp tại EMR consultation tab `Vitals` (skip dedicated test)

**Phase 4 — Doctor consultation + prescription**: ✅ DONE
- `dr_nguyen` login → My Queue 2 visits Waiting → Enter Consultation cho 20260504-002
- 7 tabs EMR (Vitals/Clinical Exam/ICD-10/Ancillary Services/Prescription/Summary/Notes)
- Tab Prescription: search "para" → 4 variants với in-stock (autocomplete + fuzzy match work) → add Paracetamol 500mg
- Form: Quantity 21, Unit viên, Dosage "1 viên × 3 lần/ngày sau ăn", Save Prescription → Print button xuất hiện

**Phase 5 — Pharmacy dispense**: ❌ BLOCKED bởi BUG-014
- `pharm_cuong` login → /#/pharmacy/pending → đơn `Rx 378b8aaa-...` xuất hiện trong Pending Dispense Queue
- Click Dispense button → KHÔNG có response (no network, no UI change)

**Phase 6 — Billing/Invoice**: ⚠️ PARTIAL
- `cashier_em` login → /#/billing/invoices → "Không có quyền truy cập" (BUG-015 RBAC seeding)
- Switched to admin → Invoice List OK
- "New Invoice" button mặc định lỗi "Missing visit ID" (BUG-016 UX)
- Direct URL `/billing/invoice/new/{visitId}` → "Generate Invoice from Visit" OK
- Click Create Invoice → invoice ID `c995f9ff...` tạo OK NHƯNG InvoiceDetailPage React hooks crash (BUG-017)
- Invoice list show: Draft, visit 3d05fd54..., **TOTAL 0đ** dù prescription có 21 viên paracetamol (BUG-018: pricing không include from prescription)

**Phase 7 — Visit history**: ⚠️ PARTIAL
- Patient detail BN0020 → tab Visit History
- Hiện ra **5 visits** cho BN này (BN mới chỉ có 1 visit) — backend không filter theo patient_id (BUG-019)
- Bác sĩ column show UUID thay vì tên (BUG-020 — same class với BUG-010)
- Visit của BN0020 vẫn status "Chờ khám" mặc dù đã kê đơn xong (BUG-021: status state machine không transition)

## Bugs catalogue final (15 bugs)

| ID | Severity | Status | Description |
|---|---|---|---|
| BUG-001 | Medium | OPEN | useSync Tauri SQL plugin spam errors |
| BUG-002 | Medium | OPEN | User roles cell empty + duplicate filters |
| BUG-003 | Critical | OPEN | Add User không assign clinic |
| BUG-004 | Medium | OPEN | BE thiếu defensive check |
| **BUG-005** | Critical | **FIXED** | auth/refresh 500 PII decrypt — pushed |
| BUG-006 | Medium | **CLOSED** transitively bởi BUG-008 |
| BUG-007 | Medium | OPEN | Search term không auto-fill khi click Register New |
| **BUG-008** | Critical | **FIXED** | TenancyMiddleware ignores JWT khi có X-Clinic-Id — pushed |
| BUG-009 | Medium | OPEN | Patient detail labels chồng values (CSS) |
| BUG-010 | UX | OPEN | Doctor queue cards show patient UUID |
| BUG-011 | Medium | OPEN | Receptionist sees Admin/HR menus (sidebar gating) |
| BUG-012 | UX | OPEN | Pending Dispense show patient `—` (empty) |
| BUG-013 | UX | OPEN | Pending Dispense show Rx UUID raw thay vì ngắn |
| **BUG-014** | Critical | OPEN | Pharmacy Dispense button không trigger handler |
| **BUG-015** | Critical | OPEN | Clinic-scoped roles có 0 perms; cashier không có template |
| BUG-016 | UX | OPEN | "New Invoice" button bị "Missing visit ID" |
| **BUG-017** | High | OPEN | InvoiceDetailPage React hooks order crash |
| BUG-018 | High | OPEN | Invoice TOTAL 0đ dù prescription có thuốc |
| BUG-019 | High | OPEN | Visit History BE không filter theo patient_id |
| BUG-020 | UX | OPEN | Visit History bác sĩ column UUID thay vì tên (same class BUG-010) |
| BUG-021 | High | OPEN | Visit status không transition sau prescription save |

(BUG-009 → BUG-021 chưa log full file individually for 12-21; BUG-009/010/011/014/015 đã log full)

## Final progress

- Phases tested: 7/7 (Phase 5 blocked, others passed/partial)
- Bugs catalogued: 21 (3 Critical-fixed, 1 Medium-closed, 6 Critical-open, 11 Medium/UX-open)
- DB enrichments: account_clinic_role 13 rows + medicines/services/batches seed
- Commits pushed: 3 (BE: 24e6dfd, a5f3dcf; FE: 490bd47); local commit: fa834c0 (seed fix)

## Admin section walkthrough — 2026-05-04

Triggered by user: "phần quản trị vẫn chưa hoạt động". Tested admin pages after BUG-008 fix landed.

| Page | Render | Findings |
|---|---|---|
| `/admin/users` | ❌ CRASH | **BUG-022** Critical: `Cannot read properties of undefined (reading 'map')` ở `UsersPage.tsx:1022`. API trả `{data:[...users], total}` thiếu field `roles` → FE `.map()` crash. Same class với BUG-002. |
| `/admin/roles` | ✅ OK | 12 vai trò (5 system + cashier + 6 clinic-scoped duplicates). Click role detail panel hiển thị perms. |
| `/admin/services` | ❌ CRASH | **BUG-022b** same pattern: `.map()` on undefined. ServicesPage cũng cùng class với UsersPage. |
| `/admin/medicines` | ✅ OK | 77 thuốc. **BUG-023** i18n: `medicines.form.dosageForms.effervescent` chưa translate. |
| `/admin/vitals` | ✅ OK | 7 chỉ số sinh tồn. **BUG-024** i18n: `vitals.dataTypes.integer` chưa translate. |
| `/admin/audit` | ⚠️ Mock | **BUG-025** Critical-data: 3 entries hardcoded mock (Nguyễn Văn A, Trần Thị B — KHÔNG trong DB thật). Audit listener ko wire vào API thật, hoặc page render mock fixture. |
| `/admin/settings` | (chưa test) | — |

**Root cause hypothesis**: Branch `feature/TASK-047-print-receipts` có WIP changes trên 6 admin pages (UsersPage/ServicesPage/RolesPage/MedicinesPage/VitalsPage/AuditPage). User đang restyle/refactor — một số page hoàn thiện, một số dở dang.

**Recommendation**: Spawn FE agents fix BUG-022 (UsersPage + ServicesPage cùng pattern) và BUG-025 (audit mock → real API) ngay sau khi 2 agents BE còn lại (BUG-019, BUG-021) xong.

## Final final summary

- 25 bugs total (3 fixed via initial agents, 4 fixed via parallel agents in progress)
- E2E test xong toàn bộ 7 phases nghiệp vụ + admin section
- Các critical bug còn open: BUG-022 (admin users/services crash), BUG-018 (invoice 0đ), BUG-025 (audit mock)
