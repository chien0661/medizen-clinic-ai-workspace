---
id: TASK-032
type: feature
title: Audit FE + BE theo MediZen Modern design + function list v1.3 — gap analysis + tự tạo sub-tasks + tự implement
status: IN_PROGRESS
phase: "C-done-D-paused"
priority: High
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
branch: ""
jira_key: ""
tags: [audit, gap-analysis, refactor, fe, be, medizen-modern, function-list-v1.3, multi-clinic, security-nfr, phase-d, meta-task]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/"
  implementation_plan: "docs/tasks/TASK-032/refs/implementation-plan.md"
  figma: "https://stitch.withgoogle.com/projects/2542650746708884228"
  confluence: ""
  jira_ticket: ""
  other:
    - "../../../docs/clinic_management_function_list.md"
    - "docs/design/medizen-modern/MEDIZEN_FRESH_PROJECT.md"
    - "docs/design/medizen-modern/MENU_AND_SCREENS.md"
    - "docs/design/medizen-modern/SECURITY.md"
    - "docs/design/medizen-modern/TAB_MATRIX.md"
    - "docs/design/medizen-modern/MULTI_ROLE_UX.md"
    - "docs/design/medizen-modern/SITEMAP.md"
    - "docs/tasks/TASK-027/task.md"
    - "docs/tasks/TASK-029/task.md"
    - "docs/tasks/TASK-031/task.md"
---

# TASK-032: Audit FE + BE theo MediZen Modern design + function list v1.3 — Gap analysis + tự tạo sub-tasks + tự implement

## Description

**Meta-task** thực hiện 4 phases tuần tự:

1. **Phase A — FE Audit**: Rà soát toàn bộ codebase `clinic-cms-web` (port React/Tailwind từ TASK-017..026) so với MediZen Modern design (TASK-027/029/031 — 45 màn Stitch) + function list v1.3. Sinh báo cáo gap.
2. **Phase B — BE Audit**: Rà soát toàn bộ codebase `clinic-cms` (FastAPI + Postgres từ TASK-001..016) so với function list v1.3 (multi-clinic AUTH-018..022, BHYT toggle CFG-017, RX-016 stock chip, NAV-001..008 search, RBAC-015..018, NFR-024..046 security depth). Sinh báo cáo gap.
3. **Phase C — Synthesize + Plan**: Tổng hợp 2 báo cáo, ưu tiên gap theo critical/major/minor, tự tạo sub-tasks (TASK-033, TASK-034, ...) cho từng cluster công việc.
4. **Phase D — Self-implement**: Lần lượt complete các sub-tasks vừa tạo qua workflow `/complete-task` chuẩn (Implementation → Review → Testing → Documentation).

**Lý do làm task này**: Sau Phase BE (TASK-001..015) + FE port (TASK-017..026), team đã ship MVP. Phase Design (TASK-027..031) đem vào nhiều requirement mới mà code hiện hữu chưa cover:
- Multi-clinic per account (replace clinic_code at login)
- Multi-role UX (merge sidebar thay vì role switcher)
- BHYT feature toggle ảnh hưởng 11 UI areas + endpoint gating
- Security NFR depth (column encryption, hash chain audit, anomaly detection, crypto-shred)
- 45 MediZen Modern Stitch screens chưa port React
- Cmd+K palette, Clinic Switcher, Stock chip in prescription, Profile multi-tab

Task này đảm bảo **convergence** giữa code đã ship và spec hiện tại trước khi go-live thật.

## Requirements

### Phase A — FE Audit (clinic-cms-web)

- [ ] **A.1 Design system**: Compare current `tailwind.config.js` vs MediZen Modern tokens (Indigo `#6366F1`, Slate, Emerald, Amber, Red, Plus Jakarta Sans heading + Inter body, 12/8/6px radius)
- [ ] **A.2 App shell**: Topbar 56px (logo + ⌘K + 🔔 + clinic switcher + avatar) + Sidebar 240px Indigo accent — vs current shell layout
- [ ] **A.3 Multi-clinic UX (AUTH-018..022)**: 
  - Login KHÔNG có clinic_code field
  - Sau login → "Chọn phòng khám" if user has multi-clinic
  - Topbar Clinic Switcher dropdown (3 PK với role chip + "Hiện tại" current + footer actions)
  - Profile cá nhân tab "Phòng khám của tôi" — list + radio default
- [ ] **A.4 Multi-role merge sidebar (RBAC-015..018)**: User kiêm BS+QT thấy 1 sidebar merge (không có role switcher) với divider sections per role; default landing là Multi-role Dashboard
- [ ] **A.5 BHYT toggle UX (CFG-017)**: Verify 11 UI areas tôn trọng `clinic.bhyt_enabled`:
  - Cấu hình BHYT (config screen) — hide nếu OFF
  - Báo cáo Tab BHYT — hide tab nếu OFF
  - Tích hợp tab VSS — hide nếu OFF
  - Bảng giá BHYT column — hide nếu OFF
  - Tiếp nhận BN BHYT field — hide nếu OFF
  - Kê đơn BHYT line — hide nếu OFF
  - CLS BHYT chỉ định — hide nếu OFF
  - Hoá đơn BHYT line — hide nếu OFF
  - + 3 nơi khác trong TAB_MATRIX
- [ ] **A.6 Cmd+K palette (NAV-001..008)**: Modal overlay, search input, sub-mode prefix `/bn /thuoc /inv /rx /lk`, result group BN/Thuốc/Tính năng, keyboard nav, recent items
- [ ] **A.7 Stock chip in prescription (RX-016)**: Khi search thuốc trong tab Kê đơn, mỗi thuốc result hiển thị chip "Còn 1.250 viên" / "Sắp hết 45 viên" / "Hết hàng" + cảnh báo HSD
- [ ] **A.8 EMR 8 tabs**: Hiện tại bao nhiêu tab? Spec yêu cầu 8 tabs (vs 6 hiện hữu) — cần thêm tab Sinh hiệu, Chẩn đoán, Kê đơn (đã có) + AI Gợi ý, Lịch sử BHYT (mới?)
- [ ] **A.9 Phase D screens chưa port**: Quên MK, Danh sách BN, Hồ sơ BN 8 tabs, Phòng chờ Kanban, Báo cáo BHYT tab, Profile multi-tab, AR aging, Notifications full page, Pharmacy 4 sub (Catalog/PO/Kiểm kê/Xử lý hết hạn)
- [ ] **A.10 Vietnamese localization completeness**: Verify `i18n/vi.json` có đủ keys cho 45 màn mới

### Phase B — BE Audit (clinic-cms)

- [ ] **B.1 Multi-clinic per account model**:
  - `account` table KHÔNG còn FK to single clinic
  - `account_clinic_role` pivot table (account_id × clinic_id × role_id)
  - Login response trả về `clinics: [{id, name, role, is_default}]`
  - `POST /auth/select-clinic` set active clinic for session
  - `GET /auth/clinics` list user's clinics
  - `PATCH /auth/clinics/{id}/default` set default
- [ ] **B.2 BHYT toggle model (CFG-017)**:
  - `clinic` table có `bhyt_enabled BOOLEAN DEFAULT FALSE`
  - Middleware check: nếu `bhyt_enabled = false` → return 404 cho endpoints `/bhyt/*`, `/integrations/vss/*`, `/reports/bhyt/*`
  - Permission `bhyt:read` / `bhyt:write` chỉ effective khi flag ON
- [ ] **B.3 RX-016 Stock chip API**: `GET /medicines/{id}/stock-summary` returns `{available_qty, lot_count, earliest_expiry, status}` for prescription dropdown realtime
- [ ] **B.4 Cmd+K Search API (NAV-001..008)**: `GET /search?q=X&mode=bn|thuoc|inv|rx|lk` cross-table search với typo-tolerance + permission filter
- [ ] **B.5 Multi-role data (RBAC-015..018)**: User có nhiều roles → API trả về union of permissions, không single role_id; FE quyết định merge sidebar
- [ ] **B.6 Security NFR-024..046**:
  - **NFR-024 Column encryption**: PII columns (full_name, phone, address, dob, citizen_id, bhyt_no, ...) encrypt at rest with AES-256-GCM; envelope pattern with per-tenant DEK + master KEK from KMS
  - **NFR-025 Crypto-shred**: Tenant deletion = destroy DEK → all encrypted data unrecoverable
  - **NFR-031 Hash chain audit**: Audit log có `prev_hash`, mỗi entry hash = `SHA256(prev_hash + content)`, anti-tamper
  - **NFR-035 Anomaly detection**: Login anomaly (geo + behavior) → trigger 2FA challenge / lock account
  - **NFR-040 PII lifecycle**: Auto-archive PII 7 năm (Nghị định 13 VN), encrypt cold storage
  - **NFR-042 Bcrypt cost 12**: Verify password hashing cost
- [ ] **B.7 Notifications full page API**: `GET /notifications?type=&date=&unread=` paginated; bulk actions `POST /notifications/mark-read`
- [ ] **B.8 AR Aging report API**: `GET /reports/ar-aging?clinic_id=` returns buckets + per-patient breakdown
- [ ] **B.9 Pharmacy sub-features API**:
  - `POST /inventory/po` (purchase order)
  - `POST /inventory/stocktake` (kiểm kê wizard 3-step)
  - `GET /inventory/expired?days=30|60|90` + `POST /inventory/expired/disposal`

### Phase C — Synthesize + Plan

- [ ] **C.1** Tổng hợp Phase A + Phase B vào `deliveries/final-specs/audit-report.md` — bảng gap cluster theo CRITICAL / MAJOR / MINOR
- [ ] **C.2** Cluster gaps thành 6-10 sub-tasks (ví dụ):
  - TASK-033 Multi-clinic per account (BE+FE)
  - TASK-034 BHYT toggle wiring (BE+FE 11 areas)
  - TASK-035 Multi-role merge sidebar UX (FE)
  - TASK-036 Cmd+K Quick Search (BE search API + FE palette)
  - TASK-037 Security NFR depth — column encryption + hash chain audit (BE)
  - TASK-038 Security NFR — anomaly detection + PII lifecycle (BE)
  - TASK-039 MediZen Modern design system port (FE Tailwind tokens + components)
  - TASK-040 Phase D screens port (Quên MK, BN list, BN profile, Queue Kanban, Profile multi-tab, AR aging, Notifications)
  - TASK-041 Pharmacy sub-features (BE + FE 4 màn)
  - TASK-042 EMR 8-tab refactor (FE)
- [ ] **C.3** Tạo task files cho từng sub-task qua skill `/task-create` với priority + dependencies rõ
- [ ] **C.4** Update `dashboard.md` với 6-10 sub-tasks mới ở status TODO

### Phase D — Self-implement

- [ ] **D.1** Lần lượt `/complete-task TASK-033` → ... → TASK-04X qua workflow chuẩn (Impl → Review → Test → Doc)
- [ ] **D.2** Stop-and-ask user khi gặp ambiguity hoặc breaking change major (ví dụ: schema migration phá data, UX flow conflict)

## Acceptance Criteria

- [ ] Báo cáo audit FE + BE đầy đủ trong `deliveries/final-specs/audit-report.md` (≥30 gaps documented)
- [ ] Tối thiểu 6 sub-tasks (TASK-033..038) được tạo với task.md đầy đủ requirements + acceptance criteria
- [ ] Mỗi sub-task có rõ priority + estimated effort + dependencies
- [ ] Sub-tasks complete được ít nhất 50% tại thời điểm TASK-032 đóng (phần còn lại track riêng)
- [ ] Codebase post-implementation pass:
  - FE: dev server start OK, golden path multi-clinic + multi-role + BHYT toggle hoạt động
  - BE: tests pass 100%, migration apply clean, encrypt PII columns verified
- [ ] Documentation cập nhật `PROJECT.md`, `MEDIZEN_FRESH_PROJECT.md`, function list nếu phát hiện gap mới

## Progress Checklist

- [x] Phase A — FE Audit (clinic-cms-web) → `handoff/fe-audit-report.md` (10 areas, ~30 gaps)
- [x] Phase B — BE Audit (clinic-cms) → `handoff/be-audit-report.md` (9 areas, ~25 gaps; **branch caveat: audit ran on `feature/task-006-settings`, missed modules from later branches — corrected in audit-report.md**)
- [x] Phase C — Synthesize + Plan → `deliveries/final-specs/audit-report.md` + 10 sub-tasks created (TASK-033..042)
- [ ] **PAUSED — User decision needed before Phase D** (see Notes below)
- [ ] Phase D — Self-implement sub-tasks (loop)
- [ ] Code Review (per sub-task)
- [ ] Testing (per sub-task)
- [ ] Documentation (final aggregate)

## Related Files

- **Input Specs**:
  - `docs/design/medizen-modern/` — toàn bộ design docs
  - `../../../docs/clinic_management_function_list.md` — function list v1.3
  - `docs/tasks/TASK-027/task.md`, `TASK-029/task.md`, `TASK-031/task.md` — design context
- **Code under audit**:
  - `clinic-cms/` — BE FastAPI + Postgres
  - `clinic-cms-web/` — FE React/Vite/Tailwind
- **Output**:
  - `deliveries/final-specs/audit-report.md`
  - `handoff/fe-audit-report.md`
  - `handoff/be-audit-report.md`
  - 6-10 sub-tasks trong `docs/tasks/TASK-033..04X/`
- **Tests**: `deliveries/test-cases/` (per sub-task)

## Timestamps

- **Created**: 2026-05-01

## Notes

### Strategy

**Audit-first, plan-second, implement-third** — không nhảy thẳng vào fix random gap. Lý do:
1. Gaps có thể overlap (ví dụ: multi-clinic ảnh hưởng cả Login UI + Auth API + Profile UI + Permission middleware)
2. Order matters — BE foundation (multi-clinic schema, encryption keys) phải xong trước khi FE port
3. Tránh churn — fix một gap có thể tạo gap khác nếu chưa thấy bigger picture

### Sub-task estimation

- TASK-033 (Multi-clinic): Large — schema migration + API rewrite + FE flows. ~3-5 days
- TASK-034 (BHYT toggle): Medium — middleware + 11 UI gates. ~2 days
- TASK-035 (Multi-role sidebar): Small — pure FE. ~1 day
- TASK-036 (Cmd+K): Medium — BE search + FE palette. ~2 days
- TASK-037 (Column encryption + hash chain): Large — schema + crypto + migration plan. ~5-7 days
- TASK-038 (Anomaly + lifecycle): Medium-Large — IP/behavior + cron jobs. ~3-4 days
- TASK-039 (Design system port): Medium — token rewrite + component restyle. ~2-3 days
- TASK-040 (Phase D screens): Large — 8-10 screens React port. ~5-7 days
- TASK-041 (Pharmacy sub): Medium — BE + 4 FE screens. ~3 days
- TASK-042 (EMR 8-tab): Small — refactor + add tabs. ~1-2 days

**Total estimated**: 27-39 days. Realistic for solo dev: 6-10 weeks at full focus.

### Stop-and-ask triggers

Stop và confirm với user trước khi:
- Migration phá hoặc transform existing data (PII encryption migration là 1 ví dụ)
- UX flow đổi nhiều (multi-clinic switcher có thể conflict với user mental model cũ)
- Add dependency mới lớn (KMS provider, encryption library)
- Touch hơn 50 files trong 1 sub-task

### Out of scope (explicit non-goals)

- KHÔNG redesign business logic core (visit state machine, billing logic, vital schema) — đã verified hoạt động trong TASK-025 E2E
- KHÔNG re-do testing strategy (Playwright + pytest đã đủ)
- KHÔNG migrate framework (vẫn FastAPI + React — không đổi sang Next.js / Django)
- KHÔNG add features mới ngoài function list v1.3 (sẽ là TASK-04X+ riêng)

## Blockers

- Phụ thuộc TASK-029/031 đã DONE (✓)
- Phụ thuộc function list v1.3 stable (✓)
- Phụ thuộc design docs MediZen Modern stable (✓)
- Nếu tìm thấy data corruption / security issue trong audit → escalate user trước khi fix (DO NOT silent-fix) — **TRIGGERED**: 3 CRITICAL security issues found (JWT default secret, no audit hash chain, all PII plaintext). See `deliveries/final-specs/audit-report.md` "Security risk highlights".

## Phase C — Findings & user decision points (2026-05-01)

### Audit summary
- **FE audit** (10 areas, ~30 gaps): design system off-spec, multi-clinic UX absent, multi-role sidebar missing, BHYT toggle entirely missing, Cmd+K palette missing, EMR only 4/8 tabs, 8 Phase D screens missing/stubbed, i18n incomplete for 45 new screens.
- **BE audit** (9 areas, ~25 gaps): multi-clinic schema not implemented, no BHYT toggle, no global search API, missing audit hash chain, all PII plaintext, no anomaly cron, no MFA, JWT default secret accepted in any env.
- **BE audit branch correction**: BE auditor scanned `feature/task-006-settings` branch and reported 6 modules missing. Verified via `git ls-tree feature/task-015-reports app/modules/` — modules **DO exist** on later feature branches (billing, inventory, notifications, prescriptions, pharmacy, reports). TASK-041 rescoped from "fresh build (10-15d)" to "branch consolidation (2-5d)".

### 10 sub-tasks created
| ID | Title | Effort | Risk |
|----|-------|--------|------|
| TASK-033 | Multi-clinic per account | Large | HIGH (schema migration of every user row) |
| TASK-034 | BHYT toggle wiring (CFG-017) | Medium-Large | LOW |
| TASK-035 | Multi-role sidebar + applied_role + SoD | Small-Medium | LOW |
| TASK-036 | Cmd+K Quick Search | Medium | LOW |
| TASK-037 | Column encryption + hash chain audit | Large | HIGH (KMS + data migration) |
| TASK-038 | JWT validator + password history + anomaly + 2FA + lifecycle | Medium-Large | LOW for quick-wins |
| TASK-039 | MediZen design system port | Medium | LOW |
| TASK-040 | Phase D screens port (8 screens) | Large | MEDIUM |
| TASK-041 | BE branch consolidation (revised scope) | Medium | MEDIUM |
| TASK-042 | EMR 8-tab + RX-016 stock chip enhance | Large | MEDIUM |

**Total estimate**: 30-45 days solo dev (~6-9 weeks full focus). See `deliveries/final-specs/audit-report.md` for full table + dependency graph.

### Stop-and-ask: 5 user decisions before Phase D
1. **Execution strategy**: Option 1 (critical-path sequential), 2 (parallel tracks if multi-dev), or 3 (slice-and-ship MVP+ — pick 2-3 sub-tasks)?
2. **TASK-041 merge strategy**: (a) merge feature branches sequentially to main first, (b) refactor each branch for multi-clinic individually then merge, (c) cherry-pick by module?
3. **TASK-037 KMS choice**: Vault, AWS KMS, or local-dev pgcrypto stub for MVP?
4. **Maintenance window for encryption migration**: ok to take ~30 min downtime, or need online migration strategy?
5. **TASK-038 Quick-win JWT validator**: ok to land as standalone <1 day commit immediately, ahead of full TASK-038?
