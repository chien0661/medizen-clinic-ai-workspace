# Task Tracking Dashboard

**Last Updated**: 2026-05-31 07:36 (auto-generated)

> **⚠️ Note**: This file is auto-generated. Do not edit manually.
> To update task status, use: `/task-status TASK-ID STATUS`
> To create new tasks, use: `/task-create TASK-ID "Title" Priority Type`

---

## Statistics

| Metric | Count |
|--------|-------|
| **Total Tasks** | 54 |
| **IN_PROGRESS** | 2 (TASK-032 — Phase D paused; TASK-053 — audit done, pending review) |
| **IN_REVIEW** | 1 (TASK-047) |
| **IN_TESTING** | 0 |
| **DOCUMENTING** | 0 |
| **TODO** | 4 (TASK-029, TASK-041, TASK-052, TASK-067) |
| **DONE** | 48 |

### By Priority

- **High**: 31 tasks
- **Medium**: 11 tasks
- **Low**: 2 (TASK-039b)
- **Other**: 1

### By Agent

- **Code Review Agent**: 1 task (TASK-039b)
- **Documentation Agent**: 1 tasks (TASK-016)
- **None**: 4 tasks (TASK-009, TASK-018, TASK-020, TASK-025)
- **Unassigned**: 2 tasks (TASK-012, TASK-019)
- **chiendv**: 20 tasks (TASK-008, TASK-010, TASK-011, TASK-013, TASK-015, TASK-023, TASK-024, TASK-027, TASK-029, TASK-032, TASK-033..042)

---

## Active Tasks

### 🔴 High Priority

#### IN_REVIEW

- **[TASK-047](tasks/TASK-047/task.md)** - In phiếu khám + in hóa đơn (FE) — native browser print, A5/A4
  - **Assigned**: code-review-agent
  - **Branch**: `feature/TASK-047-print-receipts` (clinic-cms-web, commit 391c09b)
  - **Note**: PrintableInvoice (A4) + PrintablePrescription (A5) + PrintPrescriptionModal implemented. 21 new unit tests. 799/799 tests pass.


#### IN_PROGRESS

- **[TASK-032](tasks/TASK-032/task.md)** - Audit FE + BE theo MediZen Modern design + function list v1.3 — gap analysis + tự tạo sub-tasks + tự implement
  - **Assigned**: chiendv
  - **Note**: Phase A/B/C COMPLETE. Audit report → `docs/tasks/TASK-032/deliveries/final-specs/audit-report.md`. 10 sub-tasks created (TASK-033..042). Phase D PAUSED — user decision needed on execution strategy + KMS choice + branch consolidation strategy. See audit-report.md "Recommendation to user" section.

- **[TASK-053](tasks/TASK-053/task.md)** - Khởi động FE + BE(merge), phân tích FE đã đáp ứng UI/UX chưa & rà soát toàn bộ chức năng
  - **Assigned**: Code Implementation Agent · **Type**: feature (audit) · **Started**: 2026-05-30
  - **Note**: Audit/phân tích (không build mới). Deliverables: `deliveries/final-specs/ui-ux-audit.md` (đối chiếu design MediZen Modern/Pro) + `functional-audit.md` (FE↔BE). Target: FE `../clinic-cms-web` (main), BE `../clinic-cms-merge` (audit trên state hiện tại, nhánh `fix/TASK-052-*`).




#### TODO

- **[TASK-029](tasks/TASK-029/task.md)** - MediZen UI Phase D — Edit Stitch hiện hữu + sinh ~16 màn mới theo function list v1.3 + SECURITY.md
  - **Assigned**: chiendv

- **[TASK-041](tasks/TASK-041/task.md)** - BE branch consolidation — merge medicines/inventory/billing/notifications/prescriptions/reports/pharmacy from feature branches
  - **Assigned**: chiendv · **Effort**: Medium (2-5d, revised from "Very Large" after verification)
  - **Note**: Modules exist on `feature/task-010..015` branches. NOT a fresh build. See TASK-041 task.md correction.
  - **Blocked by**: TASK-033 (decide refactor-before-merge vs merge-then-refactor)

- **[TASK-052](tasks/TASK-052/task.md)** - Tài liệu API mapping theo function list (461 fn × 26 module) + audit gap test toàn bộ BE + fix bug
  - **Assigned**: chiendv · **Type**: feature · **Branch**: `fix/TASK-052-test-encryption-fixtures`
  - **Note**: BE test sweep + bugfix DONE (1498 passed / 26 failed→parked). **API mapping DONE + source-verified (v2) 2026-05-30** → `deliveries/api-specs/api-mapping.md`: 461 fn ↔ 207 endpoint = **200 MAPPED · 24 DRIFT · 85 GAP · 152 N/A** (đã đọc source xác minh từng DRIFT/GAP, file:line). Còn lại: Review → Test → Docs. Scope guard: 85 GAP là backlog, KHÔNG build trong task này.

### 🟡 Medium Priority

#### TODO

- **[TASK-040](tasks/TASK-040/task.md)** - Phase D screens port — ForgotPassword + PatientDetail 8-tab + QueueKanban 5-col + Profile 5-tab + ARAging + Notifications full + Pharmacy stocktake/expiry
  - **Assigned**: chiendv · **Effort**: Large (5-7d)
  - **Blocked by**: TASK-039, TASK-033, TASK-041, TASK-034

- **[TASK-067](tasks/TASK-067/task.md)** - FE UI routes cleanup — Security route, BHYT config route, Reports hub, Profile stubs, useSync browser UX
  - **Assigned**: Unassigned · **Type**: feature · **Priority**: Medium
  - **Source**: TASK-053 ui-ux-audit gap G1/G2/G5/G8/G9 + runtime useSync noise



---

## Completed Tasks

### Recently Completed (Last 7 Days)

- **[TASK-068](tasks/TASK-068/task.md)** - Theme Selection & Customization System — 6 preset themes + live preview + color picker — DONE 2026-05-31
  - **Completed**: 2026-05-31
  - **Details**: 6 preset themes (Medical Blue, Emerald Health, Soft Lavender, Warm Coral, Midnight Dark, Slate Professional) + live preview + custom color picker. CSS custom properties, Zustand store, localStorage persistence, FOUC prevention. Round-2 testing: 914/914 unit tests + 7/7 E2E tests PASS. Functional design: `docs/tasks/TASK-068/deliveries/final-specs/theme-system-functional-design.md`

- **[TASK-051](tasks/TASK-051/task.md)** - Cập nhật UI — tăng cỡ chữ, mặc định tiếng Việt, template in FE — DONE 2026-05-04
  - **Completed**: 2026-05-04
  - **Details**: i18n default Vietnamese (detection.order=['localStorage'] only, fallbackLng='vi'). Typography: 7 pages nudged (text-xs→text-sm, text-sm→text-base on body content). 4 print templates: VisitSlip A5 (QueueBoard), LabOrder A5 (PatientDetail), PaymentReceipt POS 80mm (InvoiceDetail), MedicalSummary A4 (PatientDetail). 838/838 tests pass (830 original +31 dev +8 test-agent i18n regression). 0 new lint/TS errors. Functional design: `docs/tasks/TASK-051/deliveries/final-specs/ui-typography-i18n-print-functional-design.md`

- **[TASK-045](tasks/TASK-045/task.md)** - VSS BHYT integration — DONE 2026-05-01; 4 endpoints + 2 FE pages + mock client + 37 BE (22 unit + 15 integration) + 581 FE tests; 4 merge-time stubs documented
  - **Completed**: 2026-05-01
  - **Details**: Migration 0029 (vss_sync_log, RLS, index); VssClient mock adapter; 4 endpoints (eligibility-check/submit-claim/sync-log/status); VssIntegrationConfigPage + VssSyncLogPage; 2 tests added per review F3 (vss-failure → FAILED, RLS cross-tenant). Cross-task coord: TASK-034 (stubs replace), TASK-037 P2 (PII encrypt), TASK-038 (migration restamp), TASK-035 (sidebar nav).

- **[TASK-038](tasks/TASK-038/task.md)** - Security NFR rest — DONE 2026-05-01; Q.1 + B.1-B.4 + B.5-B.7 + B.8-B.14 + B.15-B.17 all closed
  - **Completed**: 2026-05-01
  - **Details**: PII lifecycle erasure (B.15-B.17) — 31/31 tests pass; 2-step token-bound erasure + daily pii_archive cron + cascade soft-delete + audit preserved; 3 post-review fixes (last_accessed_at update, admin-binding token check, audit_actions constants + json.dumps). All sub-scopes complete: JWT validator, password history, anomaly cron, MFA/TOTP, login fingerprint, PII lifecycle.

- **[TASK-039b](tasks/TASK-039b/task.md)** - MediZen component restyle — DONE 2026-05-01; 11 components + 670 tests; backward-compat preserved post-fix
  - **Completed**: 2026-05-01
  - **Details**: Button/Input/Select/Textarea/Card/Dialog/Toast/Badge/Tooltip/Popover/Tabs/Avatar restyled with MediZen variants. 9 new components, 2 updated. 123 new tests (670 total). Dialog padding regression fixed (p-6 restored). Input conditional wrapping. Popover a11y fixed (role=region + aria-label). Functional design: `docs/tasks/TASK-039b/deliveries/final-specs/component-restyle-functional-design.md`

- **[TASK-046](tasks/TASK-046/task.md)** - Bảo mật settings — DONE 2026-05-01; 4 panels + TenantErasureModal + 31 tests + 7 mocks documented
  - **Completed**: 2026-05-01
  - **Details**: MFA, Encryption, Login History, Password panels; 2-step crypto-shred confirmation; 55 i18n keys (vi/en); 578 total tests; route guard + DialogDescription a11y fix applied; 7 upstream-task mocks documented

- **[TASK-044](tasks/TASK-044/task.md)** - 4 role dashboards — DONE 2026-05-01; 572 tests; mock data placeholders; 4 new perms documented for BE seed
  - **Completed**: 2026-05-01
  - **Details**: ReceptionDashboardPage + NurseDashboardPage + PharmacyDashboardPage + AdminDashboardPage; 25 task tests (572 total); permission renamed to 2-level convention (reception.dashboard / nurse.dashboard / pharmacy.dashboard / admin.dashboard); A11y fix kpi-low-stock → button; merge-time TODOs: BE seed + Sidebar nav entries

- **[TASK-035](tasks/TASK-035/task.md)** - Multi-role merge sidebar UX (RBAC-015..018) + applied_role audit + SoD framework
  - **Completed**: 2026-05-01
  - **Details**: Multi-role sidebar grouping + applied_role audit + SoD framework; 14 BE tests (8 SoD unit + 3 audit unit + 3 SoD integration) + 592 FE tests (6 Sidebar-multi-role + 6 Topbar role chip + applied-role context); F.5/F.6/F.7 applied_role context wired post-fix; 2/3 SoD endpoints applied (invoice payment + pharmacy dispense); TASK-037 hash-chain merge coordination tracked

- **[TASK-036](tasks/TASK-036/task.md)** - Cmd+K Quick Search (NAV-001..008) — BE search API + FE palette + breadcrumb + global shortcuts
  - **Completed**: 2026-05-01
  - **Details**: 6 search modes (bn/thuoc/inv/rx/lk/all) + 4 shortcut keys + breadcrumb auto-gen + cheatsheet; 646 FE tests (67 task-specific) + 22 BE tests; 4 fixes (Breadcrumb Link, rate limit 30/min, exception handling, ShortcutCheatsheet); migration 0027 with 5 GIN trigram indexes + encryption merge coordination flagged

- **[TASK-037](tasks/TASK-037/task.md)** - Column encryption (envelope/DEK/KEK) + hash chain audit log (NFR-024/025/031)
  - **Completed**: 2026-05-01
  - **Details**: TASK-037 Phase 1 + Phase 2 DONE; 50/50 tests (20 P1 + 30 P2). Phase 1: hash chain audit with pg_advisory_xact_lock + chain_seq-inside-lock. Phase 2: 19 PII columns encrypted (Patient 11 + User 4 + Clinic 4) with per-tenant DEK + master KEK; Vault stub (prod) / pgcrypto (dev); crypto-shred 2-step (token + HMAC); with_tenant_context helper for Arq workers; audit redaction strategy (no audit-DEK YAGNI); 4 merge-time coordination items (bhyt_facility_code/password_rotation/SOAP-encryption/search-redesign) documented

- **[TASK-034](tasks/TASK-034/task.md)** - BHYT toggle wiring (CFG-017) — feature flag primitive + 11 UI gates + BhytConfigPage + BhytReportPage
  - **Completed**: 2026-05-01
  - **Details**: TASK-034 BHYT toggle — DONE 2026-05-01; 10/11 UI gates + feature flag primitive + 33 BE + 547 FE tests; Gate #7 LabOrdersTab deferred (TASK-033/041 dep); 4 i18n parity keys added post-review

- **[TASK-042](tasks/TASK-042/task.md)** - EMR 8-tab refactor + RX-016 stock chip 3-state + lot tooltip + substitute suggest
  - **Completed**: 2026-05-01
  - **Details**: 6 base tabs + 1 backward-compat; 59 task-specific + 588 BE unit tests PASS; 568 FE tests PASS, 0 TS, 0 lint; RX-016 3-state chip (emerald/amber/red) + substitute drawer; ICD-10: 225 seeds (14 categories); F1 Wave 3-A encryption, F2 audit log, F3 lot tooltip data path flagged for follow-up

- **[TASK-040](tasks/TASK-040/task.md)** - Phase D screens port — ForgotPassword + PatientDetail 8-tab + QueueKanban 5-col + Profile 5-tab + ARAging + Notifications full + Pharmacy stocktake/expiry
  - **Completed**: 2026-05-01
  - **Details**: 7/8 màn DONE (ProfilePage multi-clinic tab deferred to TASK-033 merge); 566/566 tests pass, 0 TS, 0 lint; ForgotPasswordPage 2-state, PatientDetailPage 3-col + 4 tabs wired, QueueBoard 5-col Kanban, ARAgingReport buckets + BarChart, Notifications bulk+pagination+filter, Stocktake 3-step wizard, ExpiryProcessing 30/60/90 + a11y

- **[TASK-033](tasks/TASK-033/task.md)** - Multi-clinic per account (AUTH-018..022) — schema + auth flow + JWT shape + RBAC cache
  - **Completed**: 2026-05-01
  - **Details**: 27 BE unit + 31 auth integration + 568 FE tests all PASS; migration `0021_multi_clinic_account` with email-dup pre-check; JWT `active_clinic_id` claims; ClinicSwitcher + ClinicSelectorPage + ProfilePage "Phòng khám của tôi"; ~50 call sites updated; 2 fixes (price-override clinic_id threading, 0-clinic guard, integration test clinic_code cleanup)

- **[TASK-039](tasks/TASK-039/task.md)** - MediZen Modern design system port — Tailwind tokens + Indigo brand + fonts
  - **Completed**: 2026-05-01
  - **Details**: 64 files, 191 codemod replacements, 547/547 tests pass, 0 brand-* references, unblocks TASK-034/035/036/040/042

- **[TASK-030](tasks/TASK-030/task.md)** - Landing Page MediZen — Repo riêng + implement với rich semantic annotations + SEO chuẩn
  - **Completed**: 2026-05-01
  - **Details**: 12 sections, 5 JSON-LD schemas, WCAG 2.1 AA, 35/35 tests pass, 152 kB bundle, Lighthouse-CI gates ready

- **[TASK-031](tasks/TASK-031/task.md)** - MediZen UI — Generate 15 màn còn lại (45/47 canonical, 2 blocked-stitch-api)
  - **Completed**: 2026-05-01

- **[TASK-001](tasks/TASK-001/task.md)** - Foundation — Project Skeleton, Docker Compose, Base Models, Alembic
  - **Completed**: 2026-04-26

- **[TASK-002](tasks/TASK-002/task.md)** - Tenancy + RLS Policies + Audit Log Infrastructure
  - **Completed**: 2026-04-26

- **[TASK-003](tasks/TASK-003/task.md)** - Auth — JWT Login/Refresh + Password Reset + Account Lockout
  - **Completed**: 2026-04-27

- **[TASK-004](tasks/TASK-004/task.md)** - Users + RBAC (Role + Permission + Multi-Role)
  - **Completed**: 2026-04-28

- **[TASK-005](tasks/TASK-005/task.md)** - Patient Management — CRUD + Guardian + Search + Merge Duplicates
  - **Completed**: 2026-04-27

- **[TASK-006](tasks/TASK-006/task.md)** - Clinic Settings + Tenant Onboarding Wizard
  - **Completed**: 2026-04-27

- **[TASK-007](tasks/TASK-007/task.md)** - Visit — Entity + State Machine + Visit Number Generation
  - **Completed**: 2026-04-28

- **[TASK-008](tasks/TASK-008/task.md)** - Appointment + Queue (Slot Capacity + Smart Walk-in vs Appointment)
  - **Completed**: 2026-04-29

- **[TASK-009](tasks/TASK-009/task.md)** - Vitals Dynamic Form (3 Tables + 5 Specialty Presets + Runtime Validation)
  - **Completed**: 2026-04-27

- **[TASK-010](tasks/TASK-010/task.md)** - Service Catalog + VisitService (Performed Services Tracking)
  - **Completed**: 2026-04-28

- **[TASK-011](tasks/TASK-011/task.md)** - Medicine Catalog + Prescription (In-House / External Mixed)
  - **Completed**: 2026-04-27

- **[TASK-012](tasks/TASK-012/task.md)** - Inventory + Batch + StockMovement + FEFO + Pharmacy Dispense
  - **Completed**: 2026-04-27

- **[TASK-013](tasks/TASK-013/task.md)** - Billing — Invoice + Multi-Payment + Discount + Void/Refund
  - **Completed**: 2026-04-27

- **[TASK-014](tasks/TASK-014/task.md)** - HR — Shift + Recurring Schedule + Attendance + Leave Request
  - **Completed**: 2026-04-28

- **[TASK-015](tasks/TASK-015/task.md)** - Reporting + In-App Notifications + Background Jobs (Arq)
  - **Completed**: 2026-04-27

- **[TASK-016](tasks/TASK-016/task.md)** - Tauri Foundation — Shell + Offline Sync Engine + Hardware Integration
  - **Completed**: 2026-04-27

- **[TASK-017](tasks/TASK-017/task.md)** - FE — Auth + App Shell + Design System + i18n (vi/en)
  - **Completed**: 2026-04-27

- **[TASK-018](tasks/TASK-018/task.md)** - FE — Reception (Patient Register/Search/Merge + Walk-in + Appointment Booking + Queue Board)
  - **Completed**: 2026-04-27

- **[TASK-019](tasks/TASK-019/task.md)** - FE — Doctor (My Queue + Consultation + Vitals Dynamic + Service + Prescription)
  - **Completed**: 2026-04-27

- **[TASK-020](tasks/TASK-020/task.md)** - FE — Pharmacy (Pending Dispense + Substitute Batch + Inventory + Stock Adjustment)
  - **Completed**: 2026-04-27

- **[TASK-021](tasks/TASK-021/task.md)** - FE — Billing (Invoice Auto-Gen + Multi-Payment + Discount + Void/Refund + POS Print)
  - **Completed**: 2026-04-27

- **[TASK-022](tasks/TASK-022/task.md)** - FE — HR (Shift Calendar + Recurring Schedule + Leave Request + Attendance Check-in/out)
  - **Completed**: 2026-04-27

- **[TASK-023](tasks/TASK-023/task.md)** - FE — Admin (Users + Roles + Clinic Settings + Vital Schema Editor + Onboarding Wizard)
  - **Completed**: 2026-04-27

- **[TASK-024](tasks/TASK-024/task.md)** - FE — Dashboard + Reports + Notifications Panel + Real-time Updates
  - **Completed**: 2026-04-27

- **[TASK-025](tasks/TASK-025/task.md)** - System Integration + E2E Test Suite (Playwright + Smoke + Regression + Performance)
  - **Completed**: 2026-04-29

- **[TASK-026](tasks/TASK-026/task.md)** - FE integration audit — replace remaining mocks with real BE + retest
  - **Completed**: 2026-04-29

- **[TASK-027](tasks/TASK-027/task.md)** - MediZen Modern UI — Phase B+C — Multi-role Dashboard + 17 tab variants (toàn bộ tab EMR/Cấu hình/Báo cáo)
  - **Completed**: 2026-04-30

- **[TASK-028](tasks/TASK-028/task.md)** - Landing Page MediZen — Stitch design (project mới) + implementation
  - **Completed**: 2026-04-30

- **[TASK-066](tasks/TASK-066/task.md)** - BE AR aging endpoint + gỡ MOCK_DATA fallback im lặng (ARAgingReportPage)
  - **Completed**: 2026-05-31
  - **Details**: 3 endpoints (GET /reports/ar-aging + export + doctor-weekly), MOCK_DATA removed from FE, 29 BE integration tests + 914 FE unit tests + 4 E2E tests all PASS. Functional design + API specs documented. BUG-066-001 resolved (stale unit test updates).

---

**💡 Tip**: Click on any task ID to view full details.
