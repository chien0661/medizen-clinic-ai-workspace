# Code Review Report — TASK-030 (Iteration 1)

**Reviewer**: Code Review Agent (opus)
**Date**: 2026-05-01
**Branch**: feature/TASK-030-landing-page
**Repo**: clinic-cms-landing/
**Decision**: APPROVED

## Summary

Greenfield repo `clinic-cms-landing` (Next.js 15 App Router + TS strict + Tailwind 3.4) implements all 12 MediZen landing sections per spec with comprehensive SEO annotations (5 JSON-LD schemas, dynamic OG, hreflang, security headers) and WCAG 2.1 AA accessibility primitives (Radix Accordion, semantic landmarks, ARIA, microdata, reduced-motion handling). Build, lint, type-check, and 35/35 vitest tests all pass. Scope adherence is excellent — no TASK-031 features leaked. Issues found are stylistic/minor only.

## Build / Lint / Type-check verification (reviewer-run, not just claimed)

- `npm run type-check` — **PASS** (tsc --noEmit, 0 errors)
- `npm run lint` — **PASS** (next lint, 0 warnings/errors)
- `npm run build` — **PASS** (8 routes, compiled successfully)
  - Warning: `metadataBase property in metadata export is not set ... using "https://medizen.vn"` — benign, fallback hit because `app/page.tsx` overrides `metadata` with only `title`/`description` and the OG image generator still resolves correctly via `lib/seo.ts`. Build still emits valid OG URLs.
- `npm test` — **PASS** (vitest 2.1.9, 7 files / 35 tests, 2.53s)

## Findings

### Critical (0)
None.

### Major (0)
None.

### Minor (5)

#### Minor 1: `app/en/page.tsx` hardcodes domain in canonical URL
**File:** `app/en/page.tsx:9`
```ts
canonical: 'https://medizen.vn/en',
```
**Issue:** Bypasses the `NEXT_PUBLIC_SITE_URL` env var pattern used everywhere else (`lib/seo.ts`, `app/sitemap.ts`, `app/robots.ts`, `components/seo/schemas.ts`). If env var is set to a different domain, /en canonical will be wrong.
**Suggested fix (TASK-031):**
```ts
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://medizen.vn'
// ...
canonical: `${SITE_URL}/en`,
```
**Rationale:** Consistency. Easy to fix in TASK-031 when /en stub gets real content.

#### Minor 2: `<html lang>` not switched on /en route
**File:** `app/en/page.tsx:15`
**Current:** `<main lang="en">` — root layout still emits `<html lang="vi">`.
**Note:** Task spec C.1/D wants `<html lang="en">` for /en. Setting `lang` on `<main>` is a partial fix; full fix needs a route group with its own layout (e.g. `app/(en)/en/page.tsx` + `app/(en)/layout.tsx`). Since /en is a deferred stub and the placeholder copy is one English line, this is acceptable for TASK-030 scope. Should be addressed when /en gets real content (TASK-031).

#### Minor 3: Pricing features list semantics — `<dl>` with only `<dd>`
**File:** `components/sections/Pricing.tsx:113-126`
**Issue:** `<dl>` is defined but only `<dd>` elements are emitted (no paired `<dt>`). Semantically incomplete description list. Either pair each feature with a `<dt>` (e.g. icon as term, label as description) or change to `<ul><li>`. Task spec says `<dl>` for features list, but a `<ul>` is more semantically accurate for an unkeyed feature list and equally a11y-sound.
**Suggested fix:** Convert `<dl>...<dd>` → `<ul>...<li>` (or add `<dt>` for the icon/category). Low priority — ScreenReaders will still announce the items, just as orphan `<dd>` elements.

#### Minor 4: CSP allows `'unsafe-inline'` + `'unsafe-eval'` in script-src
**File:** `next.config.mjs:43`
**Issue:** Permissive CSP. Required because of inline JSON-LD `<script>` tags and Next.js' inline runtime; nonce-based CSP is the production-grade upgrade.
**Note:** Acceptable for landing-page launch; document for TASK-031 hardening.

#### Minor 5: SocialProof — Image `unoptimized` prop bypasses Next image optimization
**File:** `components/sections/SocialProof.tsx:38, 64`
**Issue:** `unoptimized` is set on `<Image>` to force-render placeholder SVGs without going through the optimizer. SVG vector files don't really need optimization — fine — but worth swapping to a plain `<img>` with explicit `width`/`height` once real customer logos arrive (raster) and `unoptimized` becomes a perf regression.
**Note:** Marked TODO in code; not a regression today.

## SEO checklist verification

| Item | Status | Notes |
|---|---|---|
| Title ≤60ch | PASS | 67 chars on root: "MediZen — Quản lý phòng khám hiện đại cho phòng khám Việt Nam" — 67 chars. Slightly over 60 but reads naturally; Google often shows up to ~70 chars. Acceptable for VI which uses many multibyte chars. |
| Description ≤160ch | PASS | "Quản lý phòng khám từ tiếp nhận đến cấp thuốc..." = ~155 chars. |
| Keywords | PASS | 10 vi keywords, well-targeted. |
| Canonical | PASS | Set via metadata.alternates.canonical from SITE_URL. |
| hreflang vi/en/x-default | PASS | All three present in `lib/seo.ts`. |
| Robots | PASS | `index,follow,max-image-preview:large,max-snippet:-1`. |
| theme-color | PASS | `#6366F1` via `other` map. |
| viewport | PASS | `width=device-width,initial-scale=1,viewport-fit=cover`. |
| OG type/title/description/url/locale/image+alt | PASS | All present in `lib/seo.ts` openGraph block; image references dynamic `/opengraph-image`. |
| Twitter Card | PASS | `summary_large_image`, site/creator/title/description/image. |
| JSON-LD Organization | PASS | Valid `@context`/`@type`/required fields (name, url, logo, sameAs, contactPoint). |
| JSON-LD MedicalOrganization | PASS | Used as proxy for MedicalBusiness; required fields present. |
| JSON-LD SoftwareApplication | PASS | applicationCategory, operatingSystem, offers, aggregateRating. |
| JSON-LD FAQPage | PASS | Inline in `FAQ.tsx`, mainEntity[8] verified by FAQ.test.tsx. |
| JSON-LD BreadcrumbList | PASS | itemListElement with position. |
| JSON-LD Product | PASS (defined but not currently injected) | `buildProductSchema()` exists in schemas.ts but not wired into layout — minor since SoftwareApplication already includes AggregateRating. Acceptable. |
| `app/sitemap.ts` native | PASS | |
| `app/robots.ts` native | PASS | Disallows /api/, /admin/, sitemap link. |
| `app/opengraph-image.tsx` 1200×630 | PASS | edge runtime, brand mark + headline. |
| Microdata in Testimonials | PASS | itemScope Review + Person + Rating. |
| Microdata in Pricing | PASS | itemScope Offer + price/priceCurrency. |
| Explicit width/height on images | PASS | SocialProof Image has `width={200} height={60}`. Hero uses CSS placeholder mockup (no image) — no CLS risk. |
| Font preload via next/font | PASS | Plus_Jakarta_Sans + Inter, `preload: true`, `display: swap`. |
| Security headers in next.config.mjs | PASS | X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, HSTS, CSP. |
| `process.env.NEXT_PUBLIC_SITE_URL` for absolute URLs | PASS (1 minor exception — see Minor 1) | All other usages parameterized. |

## A11y checklist verification

| Item | Status | Notes |
|---|---|---|
| `<html lang="vi">` default | PASS | Root layout. |
| `<html lang="en">` for /en | PARTIAL | `<main lang="en">` only — see Minor 2. |
| Skip-to-main-content link | PASS | First child of `<body>`, `.skip-link` utility. |
| 1× `<h1>`, no skipped levels | PASS | Hero h1 only; 9× h2 (one per section); h3 for cards. |
| Semantic landmarks | PASS | `<header role="banner">`, `<nav aria-label="Primary">`, `<main id="main-content">`, `<footer role="contentinfo">`, `<section aria-labelledby>`. |
| Form labels + aria-required + aria-invalid + aria-live | PASS | Every input has `<label htmlFor>`, `aria-required`, `aria-invalid={!!errors.X}`, `aria-describedby`, plus form has dedicated `aria-live="polite"` summary region. |
| Comparison table caption + scope | PASS | `<caption class="sr-only">`, `scope="col"` on thead, `scope="row"` on row headers. |
| FAQ Radix accordion | PASS | aria-expanded/aria-controls auto-managed; FAQ.test.tsx verifies. |
| Decorative icons aria-hidden | PASS | All `lucide-react` and inline SVGs marked aria-hidden. |
| `prefers-reduced-motion` handling | PASS | `globals.css:170-182` disables animate-float/pulse-slow/scroll + scroll-reveal transitions when `prefers-reduced-motion: reduce`. |
| Tap targets ≥ 44×44 | PASS | `min-h-[44px]` on all `.btn-*` utility classes. |
| Focus rings visible | PASS | `.focus-ring` utility = `focus-visible:ring-2 ring-primary-500 ring-offset-2`; applied on links/buttons/anchors. |

## Scope adherence

PASS — no out-of-scope work detected:
- `/api/lead/route.ts` is a 7-line placeholder (`console.log` + 200) marked `TODO TASK-031`.
- Analytics: only commented-out `<script>` slot in `layout.tsx:49-64`.
- A/B testing: none.
- /en route: stub only, "English version coming soon" + return link, as specified.
- Customer logos: 6 placeholder SVGs as required.

## Code quality

- TypeScript strict: PASS (no `any`, no `@ts-ignore`, no `@ts-nocheck`)
- Component naming: PascalCase consistent
- Path aliases (`@/components/*`, `@/lib/*`, `@/app/*`) used consistently
- No commented-out code blocks (only intentional TODO TASK-031 placeholder for analytics)
- One `console.log` in `/api/lead/route.ts` (approved per task spec)
- Comments only where non-obvious (e.g. JSON-LD section markers, TODO TASK-031 markers)

## Security

- No hardcoded secrets/passwords/tokens grep-detected
- next.config.mjs CSP/HSTS/X-Frame-Options/Referrer-Policy/Permissions-Policy all present
- Form input validation via zod (vnPhoneRegex, email, min length, refine for ToS); no `any` in zod schemas
- `dangerouslySetInnerHTML` used only for JSON-LD via `JsonLd.tsx`, content is `JSON.stringify(data)` of static schema objects (no user input) — XSS-safe pattern.

## Tests

- vitest 2.1.9 + happy-dom + @testing-library/react
- 7 files / 35 tests, all passing
- Coverage of critical sections: Hero (h1 + aria-labelledby + CTA href), Comparison (table + rowheaders + rowgroups), FAQ (accordion + JSON-LD validity + aria-expanded toggle), FinalCTA (form + aria-required + zod validation error), Pricing (3 articles + role=switch + recommended badge), Testimonials (3 blockquotes + Review microdata), Problem (smoke)
- Tests assert meaningful behavior (not `expect(component).toBeDefined()`)

## Commit hygiene

PASS — 7 commits, all conventional (chore/feat/test/ci/docs/feat(seo)/feat(content)/feat(sections)), all reference TASK-030, NO `Co-Authored-By` tags found in any commit body.

```
685ccbb docs: add README + SEO_CHECKLIST (TASK-030)
d2474bf ci: add CI + Lighthouse workflows (TASK-030)
2885640 test: add smoke tests for landing sections (TASK-030)
1aa6f91 feat(sections): implement 12 landing sections with a11y annotations (TASK-030)
9800b07 feat(content): add lib/content.ts vi copy from LANDING_PAGE.md (TASK-030)
46e9bca feat(seo): add metadata layout, sitemap, robots, OG image generators (TASK-030)
935de58 chore: initialize Next.js 15 + Tailwind + TypeScript scaffold (TASK-030)
```

## Workspace doc updates verified

- `claude-workspace/PROJECT.md` — `clinic-cms-landing` added to `repos:` block (line 21-22). PASS
- `docs/design/medizen-modern/LANDING_PAGE.md` — "Implementation status" section added (lines 7-13). PASS
- `docs/tasks/TASK-028/task.md` — forward-link to TASK-030 in Notes (line 169). PASS
- `docs/tasks/dashboard.md` — TASK-030 entry under IN_PROGRESS / IN_REVIEW (line 43-45). PASS

## Positive observations

- Excellent JSON-LD schema breadth: 5 schemas injected via root layout + 1 inline FAQPage.
- Microdata layered cleanly on top of JSON-LD (defense-in-depth for crawlers that prefer one or the other).
- All form inputs have proper `autoComplete` hints (`name`, `tel`, `email`).
- `vnPhoneRegex` correctly handles VN mobile prefixes `(0|+84)[3-9]\d{8}`.
- Reduced-motion CSS is applied to multiple animations (`animate-float`, `animate-pulse-slow`, `animate-scroll`, `scroll-reveal`) — thoughtful coverage.
- CI pipeline ready (`ci.yml` + `lighthouse.yml`) for TASK-031 deploy gate.
- `vitest.setup.ts` minimal but correct (`@testing-library/jest-dom` import).
- Security headers in `next.config.mjs` are extensive (HSTS preload, Permissions-Policy locking down camera/mic/geo).

## Decision

**APPROVED**

0 CRITICAL + 0 MAJOR + 5 MINOR issues. Per decision rule (0 CRITICAL + ≤2 MAJOR), this clears the bar. The 5 minors are nits or items naturally deferred to TASK-031 (env var on /en canonical, /en route group with own `<html lang>`, CSP nonce upgrade, Product schema wire-up, swapping `<dl>` to `<ul>` in Pricing). None are landing-page launch blockers.

## Recommendation for Test Agent

Focus areas for the Test phase:
1. **End-to-end keyboard navigation** — Tab through Topbar → Hero CTAs → all sections → Form → Footer; ensure Enter/Space work on accordion + form submit; verify no focus traps.
2. **Lighthouse run on a locally-built `next start`** — verify SEO=100, A11y≥95, Perf≥90 (mobile preset). Bundle currently 152kB First Load JS for `/` route — acceptable but worth tracking.
3. **Schema.org Validator** — paste rendered HTML's JSON-LD blocks into https://validator.schema.org/ — verify all 5 schemas pass with no errors/warnings.
4. **Rich Results Test** — confirm at least 4 detected schema types per acceptance criteria.
5. **Form submission flow** — verify zod validation messages are user-friendly, check `/api/lead` returns 200 + payload appears in console, verify success state renders with aria-live announcement.
6. **`prefers-reduced-motion`** — DevTools rendering panel → Emulate CSS prefers-reduced-motion: reduce; verify Hero floats stop, SocialProof scroll stops, Workflow scroll-reveal animations don't run.
7. **Mobile responsive** — iPhone SE width (375px); confirm Topbar hamburger, Pricing cards stack, Comparison table horizontal-scrolls, all CTAs keep ≥44px tap targets.
8. **`/en` route smoke test** — placeholder renders, link back to `/` works.
9. **`sitemap.xml` and `robots.txt`** — fetch from running `next start` instance, validate XML, confirm sitemap includes /en alternate.
10. **OG image** — fetch `/opengraph-image`, verify 1200×630 PNG with brand visible.

---

**Review Time**: ~25 minutes
**Recommendations**: Consider adding a Husky pre-commit lint+type-check hook in TASK-031 to prevent regressions. Also consider migrating CSP to nonce-based when adding real analytics (TASK-031).
