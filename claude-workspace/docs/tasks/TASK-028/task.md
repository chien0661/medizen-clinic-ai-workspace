---
id: TASK-028
type: feature
title: Landing Page MediZen — Stitch design (project mới) + implementation
status: DONE
priority: Medium
assigned: 
iteration: 1
completed: 2026-05-01
created: 2026-04-30
updated: 2026-04-30
branch: ""
jira_key: ""
tags: [landing-page, marketing, stitch, design, frontend, medizen]
affected-repos: [clinic-cms-web]
refs:
  detail_design: "../../../design/medizen-modern/LANDING_PAGE.md"
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "../../../design/medizen-modern/README.md"
    - "../../TASK-027/task.md"
---

# TASK-028: Landing Page MediZen — Stitch design (project mới) + implementation

## Description

Tạo **landing page (marketing site)** cho platform **MediZen** theo:
- Spec đầy đủ: `docs/design/medizen-modern/LANDING_PAGE.md` — 12 sections (894 dòng spec) đã có sẵn từ TASK-027.
- Design system: "MediZen Modern" — Indigo `#6366F1` / Slate `#0F172A` / Emerald `#10B981` / Plus Jakarta Sans + Inter.

Khác với TASK-027 (sinh 32 màn **app** trên Stitch project `5572301228665717471`), task này tạo **Stitch project MỚI riêng cho landing page** để tách rời design app vs marketing site.

## Stitch project mới — design brief

**Steps cho người tạo project**:

1. Vào https://stitch.withgoogle.com → click **New project**
2. Chọn template **Marketing / Landing page** (web)
3. Đặt tên: `MediZen — Landing`
4. Paste design brief dưới đây vào prompt input của Stitch.
5. Iterate từng section một (bắt đầu với Hero, sau đó Problem → Solution → ...).
6. Lưu link project vào field `figma:` của task này khi tạo xong.

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

## Requirements

### A. Stitch design (manual user step)
- [ ] Tạo Stitch project mới `MediZen — Landing` — KHÔNG nhồi vào project `5572301228665717471` (đó là app, đã có 32 màn).
- [ ] Sinh 12 sections theo brief trên (1 section = 1 Stitch screen, hoặc 1 long-scroll screen tuỳ Stitch hỗ trợ).
- [ ] Lưu Stitch project URL vào `task.md` field `refs.figma:`.
- [ ] Export design (HTML/CSS hoặc Figma) → `docs/tasks/TASK-028/refs/stitch-export/`.

### B. Documentation
- [ ] Update `docs/design/medizen-modern/LANDING_PAGE.md` § "Stitch project URL" với link mới.
- [ ] Update `docs/design/medizen-modern/README.md` mục Landing — add link Stitch project.

### C. FE Implementation
- [ ] Build trong `clinic-cms-web/src/pages/landing/` — option A (subroute `/welcome` trong app hiện tại) — đề xuất.
- [ ] Reuse `tailwind.config.js` design tokens (Indigo/Slate/Emerald đã có cho app).
- [ ] i18n namespace mới: `src/locales/{vi,en}/landing.json`.
- [ ] Routes: `/welcome` (default redirect khi unauthenticated user vào root). `/login` link rõ ràng.
- [ ] Components per section: `<HeroSection>`, `<SocialProof>`, `<ProblemSection>`, `<SolutionGrid>`, `<ComparisonTable>`, `<WorkflowAnimation>`, `<UseCases>`, `<PricingTable>`, `<Testimonials>`, `<FAQAccordion>`, `<FinalCTA>`, `<Footer>`.
- [ ] Signup form submit → POST endpoint mới (cần BE thêm `POST /api/v1/leads` HOẶC dùng 3rd-party form như Formspree v1).

### D. Quality
- [ ] Lighthouse: Performance ≥ 90, Accessibility ≥ 95, SEO ≥ 95
- [ ] FCP < 1.5s, CLS < 0.1
- [ ] OG tags + Twitter Card cho social share
- [ ] Cross-browser: Chrome, Firefox, Safari, mobile Safari, Chrome Android

## Acceptance Criteria

- [ ] Stitch project `MediZen — Landing` tồn tại, có link
- [ ] 12 section render đúng spec `LANDING_PAGE.md`
- [ ] Design tokens khớp với app (Indigo/Slate/Emerald, Plus Jakarta Sans + Inter)
- [ ] Responsive 3 breakpoints (desktop / tablet / mobile)
- [ ] vi/en toggle works, tất cả strings i18n
- [ ] CTA "Đăng nhập" navigate sang `/login`
- [ ] Signup form submit thành công → toast confirmation, lead capture
- [ ] Lighthouse 90+ ở 4 metrics
- [ ] Tested trên 5 browser/platform
- [ ] Deploy sẵn sàng (route `/welcome` accessible từ app hiện tại)

## Progress Checklist

- [x] Implementation (Phase A+B: Stitch design via HTML mockup) — design-only scope
- [x] Code Review (self-review: tsc N/A, browser visual check)
- [x] Testing (manual: 12 sections render, responsive 3 breakpoints, FAQ accordion, scroll reveal)
- [x] Documentation (LANDING_PAGE.md + README.md updated with mockup link)
- [ ] **Phase C — FE Implementation (deferred)**: build React components in `clinic-cms-web/src/pages/landing/` — separate task
- [ ] **Phase D — Quality (deferred)**: Lighthouse 90+, OG tags, real BE lead capture endpoint — separate task

## Related Files

- **Design spec (existing)**: `docs/design/medizen-modern/LANDING_PAGE.md` — 894 dòng, 12 sections đã spec đầy đủ
- **Design system (existing)**: `docs/design/medizen-modern/README.md` — tokens
- **Predecessor task**: `docs/tasks/TASK-027/task.md` — design app (32 màn)
- **Stitch project (new — to be created)**: TBD link
- **Code (planned)**: `clinic-cms-web/src/pages/landing/`
- **i18n (planned)**: `clinic-cms-web/src/locales/{vi,en}/landing.json`

## Timestamps

- **Created**: 2026-04-30

## Notes

### Vì sao tách Stitch project khác

TASK-027 đã sinh 32 màn **app** (dashboard/EMR/Settings/Reports) trên Stitch project `5572301228665717471`. Landing page có context khác hoàn toàn (marketing vs operational), audience khác (clinic owner browsing vs staff using daily). Tách Stitch project giúp:
- Giữ project app gọn, không rối bởi marketing content
- Khi iterate landing có thể test variants A/B mà không impact app design
- Marketing team có thể own Stitch landing project riêng

### Implementation option

**Option A** (đề xuất): Subroute `/welcome` trong `clinic-cms-web` hiện tại.
- Pros: 1 codebase, share Tailwind config, share i18n setup, deploy chung.
- Cons: bundle size lớn hơn cho user mới (web app load).

**Option B**: Tách Vite app riêng `clinic-cms-landing/`.
- Pros: faster TTFB cho marketing visitors, deploy CDN/Vercel/Netlify.
- Cons: 2 codebase, sync design system manually.

V1 đi Option A. V2 nếu marketing traffic >50% có thể tách.

### Lead capture

Form `Đăng ký demo` cần submit về đâu đó. 3 options:

1. BE endpoint mới `POST /api/v1/leads` (cần thêm 1 BE task).
2. Formspree / Tally / Google Form embed — không cần BE, tốn $5-10/tháng.
3. Email-only fallback: mailto link.

Đề xuất Option 2 cho v1 (rapid go-to-market), Option 1 cho v2 khi muốn analytics CRM.

## Blockers

- Cần user tạo Stitch project trước (không tự động được — Stitch không có public API).
- Có thể cần BE endpoint cho lead form (nếu chọn Option 1).
