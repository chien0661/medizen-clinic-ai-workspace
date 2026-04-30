# Test Report: TASK-028 — Landing Page MediZen Mockup

**Date**: 2026-05-01
**Status**: ✅ DONE (design-only phase)
**Mode**: Manual fallback after agent failure

---

## Background

Initial agent (`a3bfb39c27d25b3c8`) failed with `API Error: response exceeded 32000 output token maximum` when trying to write a single 1500-3000 line HTML file. Manual fallback: orchestrator wrote a more compact 694-line mockup that still covers all 12 sections.

## Deliverable

**File**: `docs/design/medizen-modern/landing-mockup.html`
**Size**: 694 lines, ~37 KB
**Format**: Single-file HTML5 with embedded `<style>` and minimal `<script>`

## Sections rendered (12/12)

| # | Section | Implementation |
|---|---|---|
| 0 | Sticky topbar (64px) | Logo MediZen, nav (Vấn đề/Tính năng/So sánh/Báo giá/FAQ), vi/en toggle, Đăng nhập + Đăng ký demo CTAs |
| 1 | HERO (~900px) | h1 với gradient accent, subhead, 2 CTAs, hero card mockup phải (KPI grid + queue) |
| 2 | Social proof bar | 7 placeholder logos + "50+ phòng khám" trust line |
| 3 | PROBLEM | 3x2 grid 6 pain cards (icons + text) |
| 4 | SOLUTION | 3x2 grid 6 feature cards (Indigo accents, "Tìm hiểu →" links) |
| 5 | COMPARISON table | 8-row Truyền thống vs MediZen, tick/cross |
| 6 | WORKFLOW timeline | 6-step horizontal timeline trên dark slate-900 bg với gradient line connector |
| 7 | USE CASES | 3-card grid (Nhỏ/Trung/Doanh nghiệp), card giữa featured |
| 8 | PRICING | 3-tier (Starter 490K/Pro 1290K/Enterprise) với monthly/yearly toggle, featured middle |
| 9 | TESTIMONIALS | 3 quote cards với star rating + avatar |
| 10 | FAQ | 8-item accordion |
| 11 | FINAL CTA + signup form | Gradient indigo→sky banner + 4-field form (Tên/SĐT/Email/Phòng khám) |
| 12 | Footer | 4-col grid trên slate-900, social icons, copyright |

## Design tokens applied

- **Indigo** `#6366F1` (primary CTAs, accents, brand mark gradient)
- **Slate** `#0F172A`/`#1E293B`/`#475569`/`#94A3B8`/`#E2E8F0`/`#F1F5F9`/`#F8FAFC` (text + bg scale)
- **Emerald** `#10B981` (success states, comparison ticks, positive deltas)
- **Amber** `#F59E0B` (warnings, "Đang chờ", testimonial stars)
- **Red** `#EF4444` (problem icons, "Sắp hết thuốc")
- **Sky** `#0EA5E9` (gradient blends, hero accent)
- **Plus Jakarta Sans** (700/600/800) — headings + brand
- **Inter** (400/500/600) — body
- **Roundness**: 12px cards, 8px buttons/inputs, 6px chips
- Spacing: 4px baseline, 24px gutter

## Responsive verification

3 breakpoints tested visually:
- **Desktop** (1280px+): 3-col grids, hero 2-col split
- **Tablet** (1024px and below): 2-col grids, hero stacked, timeline 3x2
- **Mobile** (640px and below): 1-col grids, nav hidden, table compact, timeline 1x6

## Animations

- **`reveal`** class: scroll-triggered IntersectionObserver fade-in + translateY(20px → 0)
- **FAQ accordion**: max-height transition 0 → 300px on click, icon `+` rotate 45deg
- **Hover**: cards lift `translateY(-2px)` + shadow upgrade
- **Buttons**: `:hover` color/transform/shadow combo
- **Hero card**: subtle gradient border via `::before` mask
- **Hero spark line**: pure CSS clip-path (no Recharts dependency for mockup)

## i18n

- **vi**: full Vietnamese copy với diacritics (Đăng nhập, Phòng khám, Lễ tân, Bệnh nhân...)
- **en**: language toggle visual only — text NOT swapped (mockup scope; full i18n deferred to FE implementation phase)

## Manual smoke test

Opening `landing-mockup.html` in Chrome:
- ✅ All 12 sections render top-to-bottom
- ✅ Sticky topbar stays on top while scrolling
- ✅ Smooth scroll on anchor links (#problem, #pricing, etc.)
- ✅ FAQ accordion opens/closes on click
- ✅ Billing toggle (monthly/yearly) and lang toggle (VI/EN) visually swap
- ✅ Reveal animations fire as elements enter viewport
- ✅ Mock signup form `onSubmit` shows confirmation toast (mock)
- ✅ No console errors

## Deferred (out of design-only scope)

- **Phase C — FE Implementation**: React/Tailwind components in `clinic-cms-web/src/pages/landing/`. Requires React Router route, i18n namespace `landing.json`, real lead capture form. Separate task.
- **Phase D — Quality**: Lighthouse 90+ audit, OG/Twitter Card meta, contact form BE endpoint, cross-browser test. Separate task.
- **Stitch project creation**: requires manual Google account login. User can use this HTML mockup as reference when creating Stitch project.

## Conclusion

Mockup HTML đầy đủ 12 sections theo spec, có thể mở browser xem ngay hoặc dùng làm reference cho:
1. Tạo Stitch project mới (paste section content + screenshot)
2. FE engineer implement React landing page
3. Marketing team review + iterate copy
