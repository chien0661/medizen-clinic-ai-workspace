---
id: TASK-053
type: feature
title: Khởi động FE + BE(merge), phân tích FE đã đáp ứng UI/UX chưa & rà soát toàn bộ chức năng
status: IN_PROGRESS
priority: High
assigned: Code Implementation Agent
created: 2026-05-30
updated: 2026-05-30
branch: ""
jira_key: ""
tags: [frontend, backend, audit, ui-ux, qa, integration]
affected-repos: [clinic-cms-web, clinic-cms-merge]
refs:
  detail_design: "docs/design/medizen-modern/MENU_AND_SCREENS.md"
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/design/medizen-modern/SITEMAP.md  # sitemap chuẩn — đối chiếu route FE"
    - "docs/design/medizen-modern/TAB_MATRIX.md  # ma trận tab theo màn hình"
    - "docs/design/medizen-modern/MULTI_ROLE_UX.md  # UX theo từng role — đối chiếu phân quyền FE"
    - "docs/design/medizen-modern/ACTION_FLOWS.md  # luồng thao tác chuẩn"
    - "docs/design/medizen-pro/DESIGN.md  # design system / visual spec"
    - "docs/design/medizen-pro/SCREENS.md  # danh sách màn hình chuẩn"
    - "docs/tasks/TASK-032/handoff/be-audit-report.md  # audit BE/FE trước đó — tránh lặp phát hiện cũ"
    - "docs/tasks/TASK-051/task.md  # UI typography + i18n vi default + print templates (gần nhất)"
    - "PROJECT.md  # build/run commands, module map, target ../clinic-cms-merge"
---

# TASK-053: Khởi động FE + BE(merge), phân tích FE đã đáp ứng UI/UX chưa & rà soát toàn bộ chức năng

> **Diễn giải từ yêu cầu gốc** (user, 2026-05-30): *"start FE + BE(merge), phân tích FE đã đáp ứng UI/UX chưa, rà soát toàn bộ chức năng"*. Đây là task **audit / phân tích** (không phải build mới) — đầu ra là **báo cáo** UI/UX gap + functional audit. Việc fix/build phát sinh sẽ tách thành sub-task / follow-up sau khi user duyệt.

## Description

Mục tiêu 3 phần:

1. **Khởi động môi trường FE + BE(merge)** — Dựng và chạy được cả frontend lẫn backend trên nhánh main worktree để có thể quan sát chức năng thực tế:
   - **BE**: `../clinic-cms-merge` (main worktree — "what's actually shipped on main"). Bring up Postgres + Redis + API + Arq worker qua Docker Compose. *(Lưu ý: hiện worktree đang checkout nhánh `fix/TASK-052-test-encryption-fixtures` — cần xác nhận/chuyển về main trước khi audit, xem Blockers.)*
   - **FE**: `../clinic-cms-web` (nhánh `main`) — Vite dev (`npm run dev`) hoặc Tauri dev, trỏ về API `:8000`.

2. **Phân tích FE đã đáp ứng UI/UX chưa** — Đối chiếu **màn hình/route đã implement** trên FE với **design spec chuẩn** (MediZen Modern + MediZen Pro):
   - So khớp sitemap/route, menu, ma trận tab (`TAB_MATRIX.md`), luồng thao tác (`ACTION_FLOWS.md`), UX đa role (`MULTI_ROLE_UX.md`).
   - Đánh giá visual/design-system: typography, spacing, component, responsive, i18n (vi default — theo TASK-051), trạng thái loading/empty/error, accessibility cơ bản.
   - Đánh dấu từng màn hình: **ĐẠT / THIẾU / LỆCH SPEC** kèm screenshot minh hoạ.

3. **Rà soát toàn bộ chức năng (functional audit FE ↔ BE)** — Rà từng module: chức năng FE có gọi đúng API BE thật không, có mock còn sót, có chức năng trong spec nhưng chưa có UI, có UI nhưng BE chưa có endpoint (gap), CRUD/permission/role-gating hoạt động đúng.
   - **Module FE hiện có**: admin, billing, dashboard, doctor, hr, notifications, pharmacy, reception, reports, search + pages (appointments, auth, patients, profile, queue).
   - **Module BE(merge) hiện có**: admin, appointments, audit, auth, bhyt, billing, hr, integrations, inventory, notifications, patients, pharmacy, prescriptions, reports, search, services, superadmin, users, visits, vitals.

## Requirements

- [ ] Dựng được BE `../clinic-cms-merge` (docker compose up: postgres + redis + api + worker), migrate `alembic upgrade head`, API `/docs` truy cập được tại `:8000`
- [ ] Xác nhận nhánh worktree BE đang audit (main vs feature branch) — ghi rõ trong báo cáo
- [ ] Chạy được FE `../clinic-cms-web` (`npm install` + `npm run dev`), đăng nhập & điều hướng qua các role chính
- [ ] **UI/UX gap matrix**: bảng `màn hình × (route, design-ref, trạng thái ĐẠT/THIẾU/LỆCH, ghi chú, screenshot)` → lưu `deliveries/final-specs/ui-ux-audit.md`
- [ ] **Functional audit matrix**: bảng `module/chức năng × (FE có UI?, gọi API thật?, BE có endpoint?, permission đúng?, còn mock?, trạng thái)` → lưu `deliveries/final-specs/functional-audit.md`
- [ ] **Gap & follow-up list**: tổng hợp các thiếu sót/lệch spec, phân loại (UI-only / BE-gap / integration / bug) + đề xuất sub-task; KHÔNG tự ý implement ngoài phạm vi
- [ ] Tuân thủ **Database Error Handling Protocol** (CLAUDE.md) nếu phát hiện lỗi data/query — dừng & báo user
- [ ] Tham chiếu `TASK-032` audit cũ để tránh lặp phát hiện

## Acceptance Criteria

- [ ] FE và BE(merge) cùng chạy được; có ghi chú lệnh dựng + cấu hình port/API base đã dùng
- [ ] `ui-ux-audit.md` bao phủ toàn bộ màn hình đã implement, mỗi màn có trạng thái ĐẠT/THIẾU/LỆCH + screenshot, đối chiếu rõ với design-ref
- [ ] `functional-audit.md` bao phủ toàn bộ module FE↔BE, chỉ rõ chức năng còn mock / thiếu API / lệch permission
- [ ] Gap report được trình bày để user duyệt; các hạng mục cần build/fix được tách thành follow-up rõ ràng (không lẫn vào task này)
- [ ] Mọi phát hiện đều có evidence (screenshot / network log / file:line) — không kết luận chung chung

## Progress Checklist

- [ ] Implementation (dựng môi trường + audit UI/UX + functional audit + gap report)
  - [x] **Bring up BE merge + xác nhận branch** (2026-05-30): stack `clinic_cms_w2e_*` đã chạy sẵn & healthy; API `:8001`/`:8002`, alembic `0036_super_admin` (head), 159 path. Nhánh worktree: `fix/TASK-052-test-encryption-fixtures` (không switch về main — tránh phá TASK-052).
  - [x] **Bring up FE** (2026-05-30): Vite dev `:1420` đã chạy sẵn, proxy `/api/*` → `:8001` OK. *(smoke đăng nhập theo role: chờ creds — bước screenshot)*
  - [x] **UI/UX audit matrix** → `deliveries/final-specs/ui-ux-audit.md` (static; route 55/57, 10 gap THIẾU/LỆCH)
  - [x] **Functional audit matrix (FE↔BE)** → `deliveries/final-specs/functional-audit.md` (159 path BE đối chiếu; 7 nhóm FE→BE GAP/DRIFT xác nhận)
  - [x] **Gap & follow-up list** → trong cả 2 deliverable (mục §5/§7)
  - [x] **Runtime screenshot verify** (Playwright, exhaustive) — XONG (2026-05-31): 42 screenshot, 5 role (admin/doctor/nurse/reception/pharmacist) + EMR flow (tạo visit runtime) + cả 7 màn verify GAP → `deliveries/test-reports/` + `runtime-verification.md`. **Phát hiện thêm**: 5 page production có **mock-fallback im lặng** (ARAging FULL-MOCK, ForgotPassword giả-success, Stocktake/Expiry giả-submit, DoctorDashboard mock chart) → đã bổ sung functional-audit §5.
    - Fix môi trường: Playwright MCP bị lock multi-instance → thêm `--isolated --headless` vào `.mcp.json` (xem memory `playwright-mcp-lock`).
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Design ref (UI/UX chuẩn)**: `docs/design/medizen-modern/` + `docs/design/medizen-pro/`
- **FE code (target)**: `../clinic-cms-web/src/` *(nhánh main)*
- **BE code (target)**: `../clinic-cms-merge/app/modules/` *(main worktree)*
- **UI/UX audit (deliverable)**: `docs/tasks/TASK-053/deliveries/final-specs/ui-ux-audit.md`
- **Functional audit (deliverable)**: `docs/tasks/TASK-053/deliveries/final-specs/functional-audit.md`
- **Screenshots / evidence**: `docs/tasks/TASK-053/deliveries/test-reports/`
- **Handoffs**: `docs/tasks/TASK-053/handoff/`
- **Bug reports (nếu có)**: `docs/tasks/TASK-053/bugs/`

## Timestamps

- **Created**: 2026-05-30
- **Started**: 2026-05-30 (audit trên state hiện tại của `clinic-cms-merge`, nhánh `fix/TASK-052-*` — không switch về main để tránh phá việc TASK-052 đang dở)

## Notes

- **Scope guard**: Task này là **audit/phân tích** — đầu ra là báo cáo. KHÔNG sửa code FE/BE ngoài việc cần thiết để dựng môi trường. Mọi fix/build phát sinh → đề xuất user tách sub-task (theo precedent TASK-052).
- **Target codebase**: BE dùng `../clinic-cms-merge` (main worktree, theo PROJECT.md) — KHÔNG dùng `../clinic-cms` (stale feature branch). FE dùng `../clinic-cms-web` nhánh `main`.
- **i18n**: vi là default sau TASK-051 — kiểm tra chuỗi dịch khi audit UI.
- **Công cụ**: có thể dùng Playwright MCP để chụp screenshot & kiểm tra network request thực tế khi audit FE.

## Blockers

- ~~Playwright MCP lock~~ → RESOLVED (thêm `--isolated --headless`).
- ℹ️ Audit chạy trên `clinic-cms-merge` @ `fix/TASK-052-*` (không switch main để tránh phá TASK-052). Nhánh này chỉ sửa test fixture, không đổi runtime — kết quả audit tương đương main. Đã ghi rõ.

## Tóm tắt phát hiện (cho Review)

**Static + Runtime đều xong.** 3 deliverable:
- `deliveries/final-specs/ui-ux-audit.md` — route 55/57, 10 điểm THIẾU/LỆCH
- `deliveries/final-specs/functional-audit.md` — 7 nhóm FE→BE GAP/DRIFT + mock-fallback
- `deliveries/test-reports/runtime-verification.md` + 42 screenshot

**Top phát hiện cần follow-up (tách sub-task, KHÔNG fix trong task này):**
1. 🔴 **Mock-fallback im lặng** 5 page (ARAging hiện số bịa, ForgotPassword/Stocktake/Expiry giả-success, DoctorDashboard mock chart) — gỡ khi BE endpoint lên.
2. BE thiếu endpoint (trùng 85 GAP TASK-052 + TASK-041): `/auth/password-reset/*`, `/reports/ar-aging`, `/inventory/stocktake`, `/inventory/batches/dispose`, `/integrations/vss/config`.
3. BUG-003: `GET /visits/{id}/prescriptions` → 405.
4. UI: route thiếu cho Security settings + BHYT config; Reports 7-route vs spec 6-tab; tab BHYT/Profile còn stub.
5. UX: ẩn cảnh báo `useSync` khi chạy ngoài Tauri (hiện lộ lỗi kỹ thuật mọi trang).
