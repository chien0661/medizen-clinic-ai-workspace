---
id: TASK-030
type: feature
title: Landing Page MediZen — Repo riêng + implement với rich semantic annotations + SEO chuẩn
status: DONE
priority: High
assigned: chiendv
iteration: 1
created: 2026-05-01
updated: 2026-05-01
completed_implementation: 2026-05-01
completed_review: 2026-05-01
completed_testing: 2026-05-01
completed_documentation: 2026-05-01
branch: "feature/TASK-030-landing-page"
jira_key: ""
tags: [landing-page, marketing, frontend, seo, schema-org, accessibility, medizen, new-repo]
affected-repos: [clinic-cms-landing]
refs:
  detail_design: "../../design/medizen-modern/LANDING_PAGE.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/12631558811738458989"
  confluence: ""
  jira_ticket: ""
  stitch_project_id: "12631558811738458989"
  stitch_design_system_asset_id: "10014644980044777618"
  predecessor: "../TASK-028/task.md"
  html_mockup_commit: "dacce0c"
  other:
    - "../../design/medizen-modern/README.md"
    - "../TASK-028/task.md"
    - "../TASK-031/task.md  (TBD — Quality + lead capture endpoint)"
---

# TASK-030: Landing Page MediZen — Repo riêng + implement với rich semantic annotations + SEO chuẩn

## Description

Tạo **repository mới `clinic-cms-landing`** (sibling của `clinic-cms` + `clinic-cms-web`) chứa code marketing landing page MediZen, implement đầy đủ 12 sections theo spec `LANDING_PAGE.md` + Stitch design `12631558811738458989`, với:

- **Rich semantic annotations**: HTML5 semantic tags, ARIA roles/labels, microdata `itemscope`/`itemtype`, JSON-LD structured data (schema.org)
- **SEO chuẩn**: meta tags đầy đủ, Open Graph, Twitter Cards, canonical URLs, hreflang vi/en, sitemap.xml, robots.txt, structured data MedicalBusiness/SoftwareApplication/FAQPage/Product/Organization
- **Performance**: Core Web Vitals targets (LCP < 2.5s, INP < 200ms, CLS < 0.1), image optimization, font preloading, code splitting
- **Accessibility**: WCAG 2.1 AA compliance, keyboard nav, focus rings, screen reader friendly, color contrast ≥ 4.5:1

### Vì sao tách repo riêng (không nhúng vào `clinic-cms-web`)?

`clinic-cms-web` là **Tauri desktop app** dùng React SPA — không phù hợp host marketing landing public (không SSR, không SEO, bundle to). Marketing site cần:

| Yêu cầu | Tauri SPA (`clinic-cms-web`) | Next.js standalone (`clinic-cms-landing`) |
|---|---|---|
| SSR/SSG cho SEO | ❌ | ✅ |
| Crawler-friendly HTML | ❌ (JS-rendered) | ✅ |
| Deploy độc lập (Vercel/Netlify) | ❌ | ✅ |
| CDN edge caching | ❌ | ✅ |
| Bundle size | Không quan tâm (desktop) | Quan trọng |
| Dev velocity marketing team | Phải biết Tauri | Standard web stack |

→ **Quyết định**: Tạo repo `clinic-cms-landing` (Next.js 15 App Router + TypeScript + Tailwind), deploy Vercel.

### Tham chiếu input

- **Spec đầy đủ**: `docs/design/medizen-modern/LANDING_PAGE.md` (12 sections, copy vi, dimensions, CTAs)
- **Design tokens**: `docs/design/medizen-modern/README.md` (Indigo `#6366F1` / Slate `#0F172A` / Emerald `#10B981` / Plus Jakarta Sans + Inter / radius 12-8-6 / spacing 4-24)
- **Stitch project**: https://stitch.withgoogle.com/projects/12631558811738458989 (TASK-028 design)
- **HTML mockup tham khảo**: commit `dacce0c` (694 dòng visualizer trong `claude-workspace/`)

### Out of scope (deferred → TASK-031)

- A/B testing infrastructure
- Lead-capture backend endpoint (form submit hiện tại sẽ POST đến placeholder API hoặc Formspree/Tally)
- Google Analytics 4 / Hotjar / FB Pixel — chỉ chuẩn bị slot, không tích hợp tracking thật trong scope này
- Multi-language toggle vi/en thực sự (scope này chỉ vi; en placeholder route, content TBD)

## Stack quyết định

```yaml
framework: Next.js 15 (App Router, RSC, Turbopack)
language: TypeScript 5.6+
styling: Tailwind CSS 3.4 + tailwindcss-animate
ui-primitives: Radix UI (Accordion cho FAQ, Dialog nếu cần)
icons: lucide-react
fonts: next/font với Plus Jakarta Sans + Inter (self-hosted)
form: react-hook-form + zod
seo:
  meta: next/metadata API
  jsonld: Inline <script type="application/ld+json">
  sitemap: next-sitemap hoặc app/sitemap.ts native
  robots: app/robots.ts native
  og-image: next/og (dynamic OG image generation)
analytics: Slot sẵn (GA4 placeholder), KHÔNG tích hợp scope này
deploy: Vercel (preview + production)
ci: GitHub Actions — build + lint + type-check + lighthouse-ci
node: ">= 20"
```

## Cấu trúc repo `clinic-cms-landing`

```
clinic-cms-landing/
├── .github/workflows/
│   ├── ci.yml                  # build + lint + type-check
│   └── lighthouse.yml          # lighthouse-ci on PR
├── app/
│   ├── layout.tsx              # Root layout: <html lang="vi">, fonts, JSON-LD Organization
│   ├── page.tsx                # Landing page (compose 12 sections)
│   ├── sitemap.ts              # Native sitemap
│   ├── robots.ts               # Native robots.txt
│   ├── opengraph-image.tsx     # Dynamic OG image (next/og)
│   ├── twitter-image.tsx       # Twitter card image
│   ├── icon.tsx                # Favicon
│   └── api/
│       └── lead/route.ts       # POST /api/lead — placeholder (TODO TASK-031)
├── components/
│   ├── sections/
│   │   ├── Topbar.tsx          # Sticky nav + lang toggle
│   │   ├── Hero.tsx            # Section 1
│   │   ├── SocialProof.tsx     # Section 2
│   │   ├── Problem.tsx         # Section 3
│   │   ├── Solution.tsx        # Section 4
│   │   ├── Comparison.tsx      # Section 5
│   │   ├── Workflow.tsx        # Section 6
│   │   ├── UseCases.tsx        # Section 7
│   │   ├── Pricing.tsx         # Section 8
│   │   ├── Testimonials.tsx    # Section 9
│   │   ├── FAQ.tsx             # Section 10 — Radix Accordion + FAQPage JSON-LD
│   │   ├── FinalCTA.tsx        # Section 11 — form + zod
│   │   └── Footer.tsx          # Section 12
│   ├── ui/                     # Button, Input, Accordion wrappers
│   └── seo/
│       ├── JsonLd.tsx          # Generic JSON-LD inserter
│       └── schemas.ts          # MedicalBusiness/SoftwareApp/FAQ/Organization helpers
├── lib/
│   ├── content.ts              # All copy strings (vi default, en stub)
│   └── seo.ts                  # Metadata builder helpers
├── public/
│   ├── og/                     # Static fallback OG images
│   ├── logos/                  # Customer logos (Section 2)
│   └── icons/                  # Feature icons SVG
├── styles/
│   └── globals.css             # Tailwind base + design tokens
├── next.config.mjs
├── tailwind.config.ts
├── tsconfig.json
├── package.json
├── .eslintrc.json
├── .prettierrc
├── README.md                   # Setup, deploy, SEO checklist, design system reference
└── LICENSE
```

## Requirements

### A. Repo setup
- [ ] Tạo repo mới `clinic-cms-landing` (sibling của `clinic-cms` + `clinic-cms-web` trong workspace)
- [ ] `git init` + initial commit + `.gitignore` chuẩn Next.js
- [ ] `package.json` scripts: `dev` / `build` / `start` / `lint` / `type-check` / `format`
- [ ] ESLint + Prettier config khớp convention `clinic-cms-web` (2-space indent, single quotes, semi)
- [ ] `tsconfig.json` strict mode + path aliases (`@/components/*`, `@/lib/*`, `@/app/*`)
- [ ] Tailwind config với design tokens MediZen Modern (extend theme với `colors.primary`, `colors.secondary`, fontFamily, borderRadius)
- [ ] `next.config.mjs` — image optimization, security headers (CSP, X-Frame-Options, Strict-Transport-Security), redirects nếu cần
- [ ] `README.md` chi tiết: setup local dev, deploy Vercel, design tokens reference, SEO checklist link

### B. Implementation 12 sections
Mỗi section là 1 component riêng, props đơn giản (content lấy từ `lib/content.ts`).

- [ ] **Section 0 (Topbar)** — sticky `<header role="banner">`, logo có `aria-label`, nav `<nav role="navigation" aria-label="Primary">`, CTA buttons có `aria-label` rõ. Lang toggle chuyển `<html lang>`.
- [ ] **Section 1 (Hero)** — `<section aria-labelledby="hero-heading">`, `<h1 id="hero-heading">`, primary CTA + secondary CTA. Image illustrator có `alt` mô tả "Bác sĩ sử dụng MediZen trên tablet". `next/image` với `priority` cho LCP.
- [ ] **Section 2 (SocialProof)** — `<section aria-label="Khách hàng tin dùng">`, logos array với `alt="<Tên phòng khám>"`. Mỗi logo grayscale + hover color, `loading="lazy"`.
- [ ] **Section 3 (Problem)** — 6 cards, `<h2>` section heading, mỗi card `<article>` với heading `<h3>` + `<p>`. Icon `aria-hidden="true"`.
- [ ] **Section 4 (Solution)** — 6 cards giống Problem nhưng tone tích cực, mỗi card có anchor link `<a href="#feature-N">` để deep-link.
- [ ] **Section 5 (Comparison)** — `<table>` với `<caption>` + `<thead>`/`<tbody>`, `scope="col"`/`scope="row"`. Tick/cross dùng SVG `<title>` (tooltip).
- [ ] **Section 6 (Workflow)** — `<ol role="list">` các bước. IntersectionObserver fade-in (CSS `prefers-reduced-motion: reduce` → disable animation).
- [ ] **Section 7 (UseCases)** — 3 personas, `<article>` mỗi card, role + pain + solution.
- [ ] **Section 8 (Pricing)** — 3 tier cards `<article>`, monthly/yearly toggle (controlled state). Mỗi tier có `<dl>` features list. Highlight "Phổ biến" với `<span aria-label="Gói được khuyên dùng">`.
- [ ] **Section 9 (Testimonials)** — `<blockquote>` + `<cite>`, avatar `alt="Ảnh BS [Tên]"`. Star rating dùng SVG có `<title>"5/5 sao"</title>`.
- [ ] **Section 10 (FAQ)** — Radix Accordion, mỗi item `aria-expanded`/`aria-controls` đầy đủ. **JSON-LD FAQPage** schema bắt buộc (8 Q&A).
- [ ] **Section 11 (FinalCTA)** — `<form>` với `<label>` cho mỗi input, `aria-required="true"`, `aria-invalid` khi lỗi zod. Submit POST `/api/lead` (placeholder route trả 200).
- [ ] **Section 12 (Footer)** — `<footer role="contentinfo">`, 4 columns navigation. Copyright `<small>`. Lang toggle duplicate. Social media links với `aria-label="MediZen Facebook"` etc.

### C. SEO annotations chuẩn

#### C.1. Metadata API (`app/layout.tsx` + `app/page.tsx`)
- [ ] `<title>` ≤ 60 ký tự — "MediZen — Quản lý phòng khám hiện đại cho phòng khám Việt Nam"
- [ ] `<meta name="description">` ≤ 160 ký tự — 1 câu value prop có CTA verb
- [ ] `<meta name="keywords">` — 8-10 keyword vi (phần mềm phòng khám, quản lý phòng khám, EMR Việt Nam, ...)
- [ ] `<link rel="canonical">` — `https://medizen.vn/`
- [ ] `<link rel="alternate" hreflang="vi">` + `<link rel="alternate" hreflang="en">` + `<link rel="alternate" hreflang="x-default">`
- [ ] `<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">`
- [ ] `<meta name="theme-color" content="#6366F1">`
- [ ] `<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">`

#### C.2. Open Graph + Twitter Cards
- [ ] `og:type=website`, `og:title`, `og:description`, `og:url`, `og:locale=vi_VN`, `og:locale:alternate=en_US`
- [ ] `og:image` — generate dynamic qua `app/opengraph-image.tsx` (next/og), 1200×630px, có brand mark + headline
- [ ] `og:image:alt` mô tả nội dung ảnh
- [ ] `twitter:card=summary_large_image`, `twitter:site`, `twitter:title`, `twitter:description`, `twitter:image`

#### C.3. JSON-LD structured data (file `components/seo/schemas.ts`)
Inject vào `<head>` qua `<script type="application/ld+json">`. Validate qua https://search.google.com/test/rich-results.

- [ ] **`Organization`** — name, url, logo, sameAs (LinkedIn/Facebook), contactPoint
- [ ] **`SoftwareApplication`** — applicationCategory=BusinessApplication, operatingSystem=Web, offers (Pricing tier)
- [ ] **`MedicalBusiness`** (hoặc `MedicalOrganization`) — vì target audience là cơ sở y tế, schema này boost EAT
- [ ] **`FAQPage`** — 8 Q&A từ Section 10 (mainEntity array)
- [ ] **`BreadcrumbList`** — Home (single page nhưng vẫn nên có)
- [ ] **`Product`** + `AggregateRating` — nếu có testimonial rating > 4.5

#### C.4. Microdata trong markup (bổ sung JSON-LD)
- [ ] Testimonial cards: `itemscope itemtype="https://schema.org/Review"` + `itemprop="author"`/`reviewBody`/`reviewRating`
- [ ] Pricing cards: `itemscope itemtype="https://schema.org/Offer"` + `itemprop="price"`/`priceCurrency=VND`
- [ ] Hero CTA button: `itemprop="potentialAction"` nếu liên kết flow demo

#### C.5. Sitemap + robots
- [ ] `app/sitemap.ts` — generate sitemap.xml với routes `/`, `/en` (placeholder), changefreq, priority
- [ ] `app/robots.ts` — allow all, link sitemap, disallow `/api/`

#### C.6. Performance + Core Web Vitals
- [ ] LCP < 2.5s — Hero image `priority`, font preload, critical CSS inline
- [ ] INP < 200ms — không heavy JS trên main thread, Section 6 animation idle-callback
- [ ] CLS < 0.1 — explicit width/height cho mọi image, font-display: swap với fallback metrics
- [ ] Total JS < 150KB gzip — kiểm bằng `next build` analyze
- [ ] Lighthouse target: Performance ≥ 90, SEO = 100, Accessibility ≥ 95, Best Practices ≥ 95

### D. Accessibility (WCAG 2.1 AA)
- [ ] Lang attribute đúng (`<html lang="vi">`, en variant `lang="en"`)
- [ ] Skip-to-main-content link đầu `<body>`
- [ ] Heading hierarchy: 1 `<h1>`, không skip level
- [ ] Color contrast ≥ 4.5:1 cho body text, ≥ 3:1 cho large text — verify Slate-700 on white, Indigo-600 on white, white on Indigo-600
- [ ] Focus ring visible (Tailwind `focus-visible:ring-2 ring-indigo-500`)
- [ ] Keyboard nav: Tab order hợp lý, Esc đóng accordion, Enter/Space trigger buttons
- [ ] `prefers-reduced-motion: reduce` → disable scroll animations
- [ ] Form errors có `aria-live="polite"` region
- [ ] Tất cả interactive elements ≥ 44×44px tap target

### E. Documentation
- [ ] `clinic-cms-landing/README.md` — quick start, deploy guide, design tokens reference, SEO checklist
- [ ] `clinic-cms-landing/docs/SEO_CHECKLIST.md` — chi tiết tất cả annotation đã làm + tools verify (Lighthouse, Rich Results Test, Schema.org Validator, Mobile-Friendly Test)
- [ ] Update `claude-workspace/PROJECT.md` § `repos:` — thêm `clinic-cms-landing` vào danh sách
- [ ] Update `docs/design/medizen-modern/LANDING_PAGE.md` § "Implementation status" — link repo + deploy URL
- [ ] Update `docs/tasks/TASK-028/task.md` — link forward "Implemented in TASK-030"

### F. CI/CD
- [ ] `.github/workflows/ci.yml` — build + lint + type-check on PR/push
- [ ] `.github/workflows/lighthouse.yml` — lighthouse-ci report on PR (perf/SEO/a11y thresholds gate)
- [ ] Vercel preview deployment trên mọi PR
- [ ] Production deploy trên `main` push

## Acceptance Criteria

- [ ] Repo `clinic-cms-landing` tồn tại sibling của `clinic-cms` / `clinic-cms-web`, có initial commit + README
- [ ] `npm run dev` chạy local thành công, render đủ 12 sections theo design `LANDING_PAGE.md`
- [ ] `npm run build` pass không error/warning
- [ ] `npm run type-check` pass strict mode
- [ ] `npm run lint` pass với 0 warning
- [ ] **SEO Lighthouse score = 100**
- [ ] **Accessibility Lighthouse score ≥ 95**
- [ ] **Performance Lighthouse score ≥ 90** (mobile)
- [ ] Rich Results Test (https://search.google.com/test/rich-results) detect được ít nhất 4 schema types: Organization, SoftwareApplication, FAQPage, Review
- [ ] Schema.org Validator (https://validator.schema.org/) pass tất cả JSON-LD blocks
- [ ] Mobile-Friendly Test (https://search.google.com/test/mobile-friendly) pass
- [ ] `sitemap.xml` accessible at `/sitemap.xml`, valid XML
- [ ] `robots.txt` accessible at `/robots.txt`, link sitemap
- [ ] Dynamic OG image accessible at `/opengraph-image`, render đúng 1200×630
- [ ] Form Section 11 submit thành công đến `/api/lead` (placeholder), validation zod hoạt động
- [ ] FAQ accordion keyboard-navigable (Tab/Enter/Space/Arrow)
- [ ] Vercel preview deploy success, public URL truy cập được
- [ ] PROJECT.md updated với entry repo mới

## Progress Checklist

- [x] Implementation
- [x] Code Review (APPROVED — 0 CRITICAL / 0 MAJOR / 5 MINOR — see `handoff/review-report.md`)
- [x] Testing (PASS — 35/35 tests, 5 JSON-LD schemas, build exit 0 — see `deliveries/test-reports/test-report.md`)
- [x] Documentation (COMPLETE — functional design + SEO checklist + workspace docs updated — see `deliveries/final-specs/landing-page-functional-design.md`)

## Related Files

- **Input Specs**:
  - `docs/design/medizen-modern/LANDING_PAGE.md` (894 dòng — 12 sections spec)
  - `docs/design/medizen-modern/README.md` (design tokens)
  - Stitch project: https://stitch.withgoogle.com/projects/12631558811738458989
  - HTML mockup tham khảo: commit `dacce0c` (claude-workspace/)
- **Code (NEW REPO)**: `../clinic-cms-landing/` (sẽ tạo)
- **Tests**: `docs/tasks/TASK-030/deliveries/test-cases/`
- **Test Report**: `docs/tasks/TASK-030/deliveries/test-reports/test-report.md`
- **Final Specs**: `docs/tasks/TASK-030/deliveries/final-specs/`
- **Predecessor**: `docs/tasks/TASK-028/task.md` (design-only, Stitch project)
- **Successor**: TASK-031 (TBD — A/B testing, lead capture backend, analytics integration)

## Timestamps

- **Created**: 2026-05-01

## Notes

### Tại sao chọn Next.js 15 (App Router) thay vì Astro / Remix / Plain HTML?

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Next.js 15 App Router** | RSC giảm JS bundle, native metadata API, dynamic OG, mature SEO ecosystem, Vercel deploy 1-click | Learning curve App Router | ✅ chọn |
| Astro | Lighthouse 100 default, MPA + island | Marketing team ít quen, ít plugin VN | ❌ |
| Remix | SSR good | Vercel/Netlify deploy phức tạp hơn | ❌ |
| Plain HTML + Vite | Đơn giản nhất | Không SSR, OG tĩnh, sitemap manual | ❌ |

### Tại sao schema MedicalBusiness?

Audience target = chủ phòng khám VN (medical professional). Google EAT (Expertise/Authoritativeness/Trust) đặc biệt strict cho YMYL (Your Money Your Life) domains, trong đó có healthcare. Schema `MedicalBusiness` signal rõ MediZen là solution cho ngành y, boost relevance score cho query "phần mềm phòng khám", "EMR Việt Nam".

### Lưu ý khi commit (theo CLAUDE.md)

- KHÔNG `Co-Authored-By` tag
- Conventional commits: `feat: add Hero section`, `fix: correct OG image dimension`, `docs: update SEO checklist`, etc.
- Không commit secrets (chưa cần env trong scope này, nhưng future analytics keys sẽ vào `.env.local` ignored)

### Domain & deploy

- **Production domain**: `medizen.vn` (giả định — confirm với marketing/business team trước khi `<link rel="canonical">` finalize)
- **Vercel project**: `medizen-landing` hoặc tương tự
- **Preview URLs**: `<branch>-medizen-landing.vercel.app`

### Out-of-scope reminder

Task này **KHÔNG** bao gồm:
- Lead capture backend thật (placeholder `/api/lead` chỉ trả 200, log payload) → TASK-031
- Analytics tracking thật (chỉ chuẩn bị slot script) → TASK-031
- A/B testing infrastructure → TASK-031
- Multi-language en thực sự (chỉ vi default + en stub route) → TASK-031 hoặc task khác

## Blockers

- ~~Domain confirm~~: **Resolved (2026-05-01)** — dùng `process.env.NEXT_PUBLIC_SITE_URL` default `https://medizen.vn`, switchable qua env var khi marketing/business team confirm.
- ~~Logo customer thực tế~~: **Resolved (2026-05-01)** — dùng 6 placeholder grayscale rectangles (200×60px) + comment HTML `<!-- TODO: replace with real customer logo pending agreement -->`. Section 2 still passes a11y (logos có `alt="Logo phòng khám đối tác"` placeholder).

None blocking implementation start.
