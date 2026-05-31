# Handoff: TASK-030 → Test

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Iteration**: 1 (review)
**Date**: 2026-05-01

## Decision

**APPROVED** — 0 CRITICAL, 0 MAJOR, 5 MINOR. Build/lint/type-check/tests all verified by reviewer (not just claimed by impl agent). Repo is launch-quality for greenfield landing.

See full review at `docs/tasks/TASK-030/handoff/review-report.md`.

## Repo state for testing

- Path: `../clinic-cms-landing/`
- Branch: `feature/TASK-030-landing-page`
- Latest commit: `685ccbb docs: add README + SEO_CHECKLIST`
- Build artefacts present: yes (`.next/` exists post-build)
- Tests baseline: vitest 7 files / 35 tests / 35 passing / 2.53s

## Test scope

Per task acceptance criteria + my review recommendations, focus on:

### Functional
1. Render all 12 sections from `app/page.tsx` — verify visually they match `docs/design/medizen-modern/LANDING_PAGE.md` and the HTML mockup at workspace commit `dacce0c`.
2. Form submission flow (FinalCTA) — happy path + each validation error case (empty name, bad phone, bad email, missing tos, etc.).
3. FAQ accordion — open/close all 8 items, single-collapse behavior, keyboard nav (Tab/Enter/Space/Esc).
4. Pricing monthly/yearly toggle — verify price text changes, year saving chip visible only on yearly mode.
5. Topbar — sticky behavior on scroll past 600px, mobile hamburger open/close, link anchors scroll to correct sections.
6. /en stub renders correctly + return link.

### SEO
1. Lighthouse SEO score — must be 100 (acceptance criterion).
2. Schema.org Validator (https://validator.schema.org/) — paste each JSON-LD block from rendered HTML, expect 0 errors. Schemas to verify: Organization, MedicalOrganization, SoftwareApplication, BreadcrumbList, FAQPage. (Product schema is defined in `schemas.ts` but not currently injected — note this; not blocking).
3. Rich Results Test (https://search.google.com/test/rich-results) — must detect ≥4 schema types per AC.
4. `/sitemap.xml` and `/robots.txt` accessible, valid XML/text.
5. `/opengraph-image` returns 1200×630 PNG with brand visible.
6. Mobile-Friendly Test pass.

### Accessibility
1. Lighthouse Accessibility score ≥ 95.
2. axe DevTools or Pa11y on running site — 0 critical/serious violations.
3. Keyboard-only navigation top-to-bottom — every interactive element reachable, focus rings visible, no traps.
4. Screen reader spot check (NVDA on Windows) — Topbar, Hero h1, Form labels, FAQ accordion announce correctly.
5. `prefers-reduced-motion` — DevTools Rendering tab → enable; verify all animations halt.
6. Color contrast spot-check via axe / Lighthouse — Slate-700 on white, Indigo-600 on white, white on Indigo-600.
7. Tap-target audit — every button/link ≥ 44×44px on mobile.

### Performance
1. Lighthouse Performance score ≥ 90 (mobile preset).
2. LCP < 2.5s (Hero element).
3. CLS < 0.1.
4. Bundle size — confirm First Load JS for `/` stays under ~160kB; current is 152kB.

### Build hygiene
1. Re-run `npm run build` from clean — must succeed.
2. Check for any new warnings beyond the known `metadataBase` benign warning on dynamic OG.

## Known minors NOT to flag as blocking

The following are pre-noted in review-report.md and should be deferred to TASK-031, NOT bounce the task:

- `app/en/page.tsx` hardcodes `medizen.vn/en` canonical instead of using env var.
- `<html lang>` on /en is `vi` (root layout) with `<main lang="en">` only.
- Pricing uses `<dl>...<dd>` without `<dt>`.
- CSP allows `'unsafe-inline'`/`'unsafe-eval'` for script-src.
- `buildProductSchema()` defined but not injected (SoftwareApplication already covers AggregateRating).
- SocialProof Image uses `unoptimized` for SVG placeholders.

## Deliverables expected from Test phase

- `docs/tasks/TASK-030/deliveries/test-cases/` — test scenarios
- `docs/tasks/TASK-030/deliveries/test-reports/test-report.md` — Lighthouse JSON, Rich Results screenshots, axe report, manual test logs
- `docs/tasks/TASK-030/handoff/test-to-documentation.md` (if pass) or `test-to-implementation.md` (if fail)

## Test strategy notes

- Run Lighthouse against `npm run start` (production build) on a clean port, NOT `npm run dev`. Dev mode adds overhead and inflates LCP.
- For Schema.org validator: easiest to `curl http://localhost:3000/` after `npm run start`, save the HTML, extract `<script type="application/ld+json">` blocks, paste into validator.
- For Rich Results: use the URL submission once a Vercel preview URL is available (TASK-031 dependency); meanwhile use the "Code" tab to paste raw HTML.
- Tests run on Windows; if axe-core CLI is awkward there, axe DevTools browser extension is fine.
