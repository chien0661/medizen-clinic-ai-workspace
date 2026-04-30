---
id: TASK-028
type: feature
title: Landing Page MediZen — Stitch project (design-only deliverable)
status: IN_PROGRESS
priority: Medium
assigned: 
iteration: 1
completed: 
created: 2026-04-30
updated: 2026-05-01
branch: ""
jira_key: ""
tags: [landing-page, marketing, stitch, design, frontend, medizen]
affected-repos: [clinic-cms-web]
refs:
  detail_design: "../../../design/medizen-modern/LANDING_PAGE.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/12631558811738458989"
  confluence: ""
  jira_ticket: ""
  stitch_project_id: "12631558811738458989"
  stitch_design_system_asset_id: "10014644980044777618"
  other:
    - "../../../design/medizen-modern/README.md"
    - "../../TASK-027/task.md"
---

# TASK-028: Landing Page MediZen — Stitch project (design-only deliverable)

## Description

**Deliverable duy nhất của task này**: Một **Stitch project mới** (`MediZen — Landing`) chứa design 12 sections của landing page MediZen, sinh qua Stitch MCP tools (`mcp__stitch__create_project`, `mcp__stitch__generate_screen_from_text`).

**KHÔNG bao gồm trong scope**:
- React/FE implementation (`clinic-cms-web/src/pages/landing/`) — tách thành task riêng (TASK-030 dự kiến)
- Lighthouse/SEO/OG tags — task riêng (TASK-031 dự kiến)
- HTML mockup — đã sinh ở commit `dacce0c` nhưng **không phải deliverable chính** của task này; coi là reference visualizer

**Input spec**:
- `docs/design/medizen-modern/LANDING_PAGE.md` — 12 sections (894 dòng spec) từ TASK-027
- Design system "MediZen Modern": Indigo `#6366F1` / Slate `#0F172A` / Emerald `#10B981` / Plus Jakarta Sans + Inter

**Output**:
- Stitch project URL (lưu vào `refs.figma:` field của task này)
- 12 screens trên Stitch project, mỗi screen tương ứng 1 section
- Screenshots/exports → `docs/tasks/TASK-028/deliveries/stitch-screens/`

Khác với TASK-027 (32 màn **app** trên Stitch project `5572301228665717471`), task này tạo **Stitch project MỚI riêng cho landing page** để tách app vs marketing site.

## Stitch project mới — design brief

**Tự động hoá qua Stitch MCP** (không còn cần user thao tác tay):

1. `mcp__stitch__create_project` — tên `MediZen — Landing`, template `web` / `marketing landing`
2. `mcp__stitch__create_design_system` — đăng ký token "MediZen Modern" (xem dưới)
3. `mcp__stitch__generate_screen_from_text` — sinh từng section một, dùng brief paste section bên dưới
4. `mcp__stitch__list_screens` + `mcp__stitch__get_screen` — confirm 12 screens được tạo
5. Lưu project URL/ID vào field `refs.figma:` của task này
6. Export screenshots → `docs/tasks/TASK-028/deliveries/stitch-screens/`

### Brief paste vào Stitch

> **Project**: MediZen — Marketing landing page for Vietnamese clinic management SaaS.
>
> **Audience**: Vietnamese clinic owners (B2B small-medium clinics, ~5-30 staff).
>
> **Tone**: Modern, trustworthy, clinical-but-warm. Không Lab-cold, không quá sales-y.
>
> **Design system "MediZen Modern"**:
> - Primary: Indigo `#6366F1`
> - Secondary: Slate `#0F172A`
> - Tertiary OK: Emerald `#10B981`
> - Warning: Amber `#F59E0B`
> - Danger: Red `#EF4444`
> - Page bg: `#F8FAFC` (slate-50)
> - Border: `#E2E8F0` (slate-200)
> - Heading font: **Plus Jakarta Sans** (700/600)
> - Body font: **Inter** (400/500)
> - Roundness: 12px cards / 8px inputs / 6px chips
> - Spacing: 4px baseline, 24px gutter
>
> **12 sections theo thứ tự** (đầy đủ spec ở `LANDING_PAGE.md`):
>
> 0. **Sticky topbar** (64px) — logo MediZen trái, nav giữa (Tính năng / So sánh / Báo giá / FAQ), CTA "Đăng nhập" + "Đăng ký demo" phải. vi/en toggle.
>
> 1. **HERO** (~900px) — Headline lớn 48-64px "Quản lý phòng khám hiện đại — chỉ trong 1 hệ thống". Subhead 18px mô tả 2 dòng. CTA primary "Dùng thử 14 ngày miễn phí" + secondary "Xem demo 5 phút". Background: subtle gradient indigo, illustration BS dùng tablet.
>
> 2. **Social proof bar** (120px) — "Được tin dùng bởi 50+ phòng khám tại Việt Nam" + 6-8 logo phòng khám greyscale.
>
> 3. **PROBLEM** (~700px) — 6 pain points của clinic owner truyền thống: thất lạc giấy tờ, thuốc hết hạn, chấm công thủ công, báo cáo cuối tháng mất 3 ngày, BS quên BN cũ, lễ tân ghi sai SĐT. Card grid 3x2, mỗi card có icon + heading + 1-line.
>
> 4. **SOLUTION** (~900px) — 6 tính năng MediZen nổi bật: EMR có schema động, FEFO inventory, Multi-role với merge sidebar, Báo cáo realtime, Audit log đầy đủ, Multi-tenant RLS. Card grid 3x2, icon lớn + body 2-3 dòng, mỗi card link "Tìm hiểu" → anchor.
>
> 5. **COMPARISON table** (~600px) — Bảng truyền thống vs MediZen, 8-10 dòng tính năng, tick/cross.
>
> 6. **WORKFLOW animation** (~700px) — Một ngày phòng khám: Tiếp nhận → Đo vital → BS khám → Cấp thuốc → Thanh toán → Báo cáo. Horizontal timeline với scroll-triggered animation.
>
> 7. **USE CASES** (~600px) — 3 personas: Phòng khám nhỏ 1-2 BS, Phòng khám đa khoa 5-10 BS, Chuỗi phòng khám multi-tenant. Mỗi card có pain + how MediZen solves + role mapping.
>
> 8. **PRICING** (~700px) — 3 tier: Starter (1 clinic, 5 user) / Professional (1 clinic, unlimited user) / Enterprise (multi-clinic). Monthly/yearly toggle, feature comparison checkmarks.
>
> 9. **TESTIMONIALS** (~500px) — 3 quote từ BS/chủ phòng khám, avatar circle, star rating 5/5, name + role + clinic name.
>
> 10. **FAQ** (~500px) — 8 accordion: bảo mật dữ liệu, offline, multi-clinic, migration, tích hợp BHYT, training, pricing, support.
>
> 11. **FINAL CTA + Signup form** (~600px) — Big banner "Bắt đầu nâng cấp phòng khám của bạn" + form 4 fields (Tên + SĐT + Email + Tên phòng khám) + submit "Đăng ký demo".
>
> 12. **FOOTER** (~300px) — 4 columns: About / Sản phẩm / Tài nguyên / Pháp lý. Logo, mạng xã hội, copyright, ngôn ngữ toggle.
>
> **Layout requirements**:
> - Responsive: desktop 1280px+, tablet 768px, mobile 375px
> - Smooth scroll + scroll-triggered fade-in animations
> - vi default, en alternate (top-right toggle)
> - Sticky header CTAs always visible
> - Footer dark mode (slate-900 bg)
>
> **Reference file**: `LANDING_PAGE.md` có spec chi tiết hơn từng section nếu Stitch cần thêm context.

## Requirements (scope = design-only)

### A. Stitch project (deliverable chính — qua MCP)
- [ ] `mcp__stitch__create_project` → tạo project `MediZen — Landing` (web / marketing template). KHÔNG dùng project `5572301228665717471` (đó là app TASK-027).
- [ ] `mcp__stitch__create_design_system` → đăng ký design system "MediZen Modern" với đầy đủ tokens (Indigo / Slate / Emerald / Plus Jakarta Sans / Inter / radius / spacing).
- [ ] `mcp__stitch__generate_screen_from_text` × 12 → sinh từng section theo brief (Sticky topbar + 12 sections = 13 screens, hoặc gộp vào 1 long-scroll screen tuỳ Stitch hỗ trợ).
- [ ] `mcp__stitch__apply_design_system` → confirm design tokens được apply nhất quán across all screens.
- [ ] Lưu Stitch project URL/ID vào `refs.figma:` field của task này.
- [ ] Export screenshots/HTML → `docs/tasks/TASK-028/deliveries/stitch-screens/`.

### B. Documentation
- [ ] Update `docs/design/medizen-modern/LANDING_PAGE.md` § "Stitch project URL" với link mới.
- [ ] Update `docs/design/medizen-modern/README.md` mục Landing — add link Stitch project.

### C/D. Out of scope (deferred → separate tasks)
- FE Implementation (`clinic-cms-web/src/pages/landing/`) → **TASK-030 (TBD)**
- Lighthouse / SEO / OG tags / lead capture endpoint → **TASK-031 (TBD)**

## Acceptance Criteria

- [ ] Stitch project `MediZen — Landing` tồn tại, URL được lưu trong `refs.figma:`
- [ ] 12+ screens trên Stitch render đúng spec `LANDING_PAGE.md`
- [ ] Design system "MediZen Modern" được áp dụng nhất quán (Indigo/Slate/Emerald, Plus Jakarta Sans + Inter, radius/spacing đúng spec)
- [ ] Tất cả screens responsive (desktop 1280px+ minimum; tablet/mobile nếu Stitch hỗ trợ)
- [ ] Screenshots export đầy đủ ở `deliveries/stitch-screens/`
- [ ] LANDING_PAGE.md + README.md đã link Stitch project URL

## Progress Checklist

- [x] HTML mockup reference (commit `dacce0c`, 694 lines) — visualizer, không phải deliverable chính
- [x] **Stitch project created** — `MediZen — Landing` (ID `12631558811738458989`)
- [x] **Stitch design system registered** — `MediZen Modern` (asset ID `10014644980044777618`)
- [x] 12 sections sinh trên Stitch — **12/12 done** (all sections 1–12 generated; see `handoff/stitch-generation-progress.md` for screen IDs)
- [ ] Screenshots exported → `deliveries/stitch-screens/`
- [ ] Documentation links updated (LANDING_PAGE.md + README.md)

## Related Files

- **Design spec (existing)**: `docs/design/medizen-modern/LANDING_PAGE.md` — 894 dòng, 12 sections đã spec đầy đủ
- **Design system (existing)**: `docs/design/medizen-modern/README.md` — tokens
- **HTML mockup reference**: commit `dacce0c` — 694 dòng visualizer, KHÔNG phải deliverable chính
- **Predecessor task**: `docs/tasks/TASK-027/task.md` — design app (32 màn) trên Stitch project `5572301228665717471`
- **Stitch project (TO BE CREATED via MCP)**: TBD URL — sẽ được lưu vào `refs.figma:` của task này
- **Future tasks (deferred)**:
  - TASK-030 (TBD): FE Implementation `clinic-cms-web/src/pages/landing/`
  - TASK-031 (TBD): Quality + lead capture endpoint

## Notes

- Implemented in TASK-030 (`../clinic-cms-landing/`) — Next.js 15 repo with 12 sections, full SEO/a11y, branch `feature/TASK-030-landing-page`

## Timestamps

- **Created**: 2026-04-30
- **Re-scoped**: 2026-05-01 — narrowed to design-only (Stitch project), HTML mockup demoted to reference
- **Completed**: 2026-05-01 — all 12 sections generated on Stitch (sections 2–12 generated in this session)

## Notes

### Vì sao tách Stitch project khác

TASK-027 đã sinh 32 màn **app** (dashboard/EMR/Settings/Reports) trên Stitch project `5572301228665717471`. Landing page có context khác hoàn toàn (marketing vs operational), audience khác (clinic owner browsing vs staff using daily). Tách Stitch project giúp:
- Giữ project app gọn, không rối bởi marketing content
- Khi iterate landing có thể test variants A/B mà không impact app design
- Marketing team có thể own Stitch landing project riêng

### Vì sao re-scope task này (2026-05-01)

Lần đầu task này được tick DONE chỉ với HTML mockup (commit `dacce0c`). Nhưng **deliverable thực** mà spec yêu cầu là Stitch project — HTML mockup chỉ là visualizer. Task được re-scope rõ ràng:

- **In scope**: Stitch project + design system + 12 screens (qua MCP)
- **Out of scope**: FE code, Lighthouse, lead capture → tách thành TASK-030, TASK-031

Trước đây assumption "Stitch không có public API → cần user tạo tay" đã sai — Stitch MCP tools (`mcp__stitch__*`) đã có sẵn trong workspace này, có thể tự động hoá toàn bộ.

## Blockers

- (Resolved) ~~Cần user tạo Stitch project trước (không tự động được — Stitch không có public API).~~ → Stitch MCP đã có sẵn, không còn blocker.
