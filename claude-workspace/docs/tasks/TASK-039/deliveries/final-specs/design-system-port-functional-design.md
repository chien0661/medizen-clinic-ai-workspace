# TASK-039: MediZen Modern Design System Port — Functional Design

**Task ID**: TASK-039  
**Ngày hoàn thành**: 2026-05-01  
**Status**: DONE ✓  
**Language**: Vietnamese (UI + tokens), English (code + config)

---

## Mục đích

Port toàn bộ hệ thống thiết kế VISSoft Clinic CMS từ brand cũ (VISSoft Blue + Segoe UI + CURA) sang **MediZen Modern** (Indigo Primary + Slate Neutral + Plus Jakarta Sans/Inter) theo Stitch design system asset `3512187121078190969`.

**Tại sao cần**:
- Rebrand toàn cầu: CURA → MediZen, Clinic CMS → MediZen, Shield icon → MediZen logo
- Visual blocker: Mọi task UI khác (TASK-034 BHYT, TASK-035 sidebar, TASK-036 Command Palette, TASK-040 Phase D, TASK-042 EMR) đều phụ thuộc vào tokens mới
- Unblock FE port: Tailwind config mới + brand rename cơ sở để downstream tasks bắt đầu

---

## Phạm vi

### ✅ Hoàn thành (11 items)

**Token rewrite** (`tailwind.config.js`):
- Indigo `#6366f1` (50–950) primary
- Slate `#0f172a` (50–950) secondary / neutral
- Emerald `#10b981`, Amber `#f59e0b`, Red `#ef4444`, Sky `#0ea5e9` — accent scales
- Surface tokens: white, bg-slate-50, border-slate-200
- Border radius: card 12px / input 8px / chip 6px
- Font family: Plus Jakarta Sans (display), Inter (body/sans)
- Spacing: 4px baseline / 24px gutter
- Dark mode: ✓ CSS variables + Tailwind `darkMode: 'class'` + dark variants on all colors

**Google Fonts** (`index.html`):
- Preconnect: fonts.googleapis.com + fonts.gstatic.com
- Plus Jakarta Sans 600/700 + Inter 400/500

**CSS Variables** (`src/styles.css`):
- `--color-brand: #6366f1` (indigo-500)
- `--color-bg: #f8fafc` (slate-50)
- `--color-border: #e2e8f0` (slate-200)
- Dark mode: indigo-400, slate-900, slate-200 updated (nit fix: unquoted hex in dark vars)

**Token export** (`src/lib/tokens.ts`):
- New file exporting `colors`, `chartColors`, `borderRadius`, `spacing`, `fontFamily` as named + default exports
- TypeScript `as const` for strict typing
- 18 design-tokens unit tests ✓ (100% pass)

**Codemod** — brand rebranding:
- `bg-brand-*` / `text-brand-*` / `border-brand-*` / `ring-brand-*` / `from-brand-*` / `to-brand-*` / `via-brand-*` / `fill-brand-*` / `stroke-brand-*` / `accent-brand-*` → corresponding `indigo-*` variants
- **191 replacements** across 57 files, **0 remaining** `brand-*` references

**Brand text rename**:
- "CURA" → "MediZen" (3 occurrences LoginPage.tsx)
- "Clinic CMS" → "MediZen" (Sidebar, Topbar, HomePage, index.html `<title>`, router comment)
- `<title>MediZen</title>` + description "MediZen Desktop Client"
- JSDoc comments hygiene: "Clinic CMS" → "MediZen" in i18n.ts

**Recharts color palette**:
- Primary: `#6366f1` (indigo-500) — already in place
- Secondary: `#8b5cf6` (violet) → `#10b981` (emerald-500) per MediZen palette
- Grid stroke: `#f0f0f0` → `#e2e8f0` (slate-200) across 7 chart files

**Smoke tests**:
- Build: ✓ PASS in 10.72s (0 errors, 1 pre-existing chunk-size warning)
- Unit tests: ✓ **547/547 PASS** (new 18 design-tokens tests included)
- TypeScript: ✓ **0 errors, 0 warnings**
- Linter: ✓ **0 ESLint errors, 0 warnings**

### ⏸️ Deferred (5 items)

| Item | ID | Reason | Recommendation |
|---|---|---|---|
| **Logo SVG replacement** | F.8 | Shield icon → MediZen logo SVG; asset management out of scope | TASK-040 (Phase D assets) or TASK-039b |
| **Favicon + Tauri icon** | F.9 | `src-tauri/tauri.conf.json` window icon/title; Tauri build config | TASK-039b or E2E follow-up |
| **Component restyle** | F.11 | Button variants, Input/Select field treatments, Card shadow/radius, Modal overlay, Toast colors, Badge chip radius — apply new tokens to component library | Propose as **TASK-039b** (separate Sprint) |
| **Playwright visual regression** | T.1 | Login, Dashboard, Sidebar collapsed/expanded, Topbar — screenshot compare vs Stitch exports | Defer to **E2E / VR test phase** (post-smoke) |
| **Dark mode parity test** | T.2 | Runtime dark-mode toggle validation for all 6 color scales + contrast verification | Defer to **E2E / VR test phase** |

---

## Bảng Token Mapping

### Màu sắc (Colors)

| Token | Hex | Tailwind Class | Use case | Spec |
|---|---|---|---|---|
| indigo-50 | #eef2ff | `bg-indigo-50` | Light bg | Primary scale |
| indigo-500 | #6366f1 | `bg-indigo-500` / `text-indigo-500` | Primary button, active state, text accent | **MediZen primary** |
| indigo-600 | #4f46e5 | `bg-indigo-600` / `hover:bg-indigo-600` | Button hover | Primary hover |
| indigo-700 | #4338ca | `active:bg-indigo-700` | Button active | Primary active |
| indigo-900 | #312e81 | `bg-indigo-900` | Sidebar dark bg option | Dark sidebar |
| — | — | — | — | — |
| slate-50 | #f8fafc | `bg-slate-50` | Page background | Surface bg |
| slate-200 | #e2e8f0 | `border-slate-200` / `stroke-slate-200` | Border, grid line | Border / neutral |
| slate-900 | #0f172a | `bg-slate-900` | Sidebar actual bg | Dark sidebar (chosen) |
| — | — | — | — | — |
| emerald-500 | #10b981 | `fill-emerald-500` | Recharts secondary bar | Secondary palette |
| amber-500 | #f59e0b | `bg-amber-500` | Warning / caution state | Alert |
| red-500 | #ef4444 | `bg-red-500` | Error / danger state | Error |
| sky-500 | #0ea5e9 | `text-sky-500` | Info state | Info |

### Border Radius

| Token | Value | Use case | Config |
|---|---|---|---|
| `rounded-card` | 12px | Card, modal, panel | `borderRadius.card: '12px'` |
| `rounded-input` | 8px | Input, select, textarea | `borderRadius.input: '8px'` |
| `rounded-chip` | 6px | Badge, pill, chip | `borderRadius.chip: '6px'` |

### Typography

| Token | Font Family | Weights | Use case |
|---|---|---|---|
| `font-display` | Plus Jakarta Sans | 600, 700 | Headings (h1–h4) |
| `font-sans` | Inter | 400, 500, 600, 700 | Body, labels, UI text |

### Spacing

| Token | Value | Use case |
|---|---|---|
| Baseline | 4px | `p-1`, `gap-1`, micro-spacing |
| Gutter | 24px | Container padding, section spacing |

---

## Files Modified — Summary

**Total**: 64 files

### Config & Root (2)
- `tailwind.config.js` — Full rewrite (brand color group removed, 6 scales added, border radius, fonts, spacing)
- `index.html` — Google Fonts preconnect + links, title + description rename

### New Files (2)
- `src/lib/tokens.ts` — MediZen token export module
- `src/tests/lib/design-tokens.test.ts` — 18 Vitest smoke tests

### CSS Variables (1)
- `src/styles.css` — MediZen palette, dark mode CSS vars (nit fix: unquoted hex)

### Brand Rename — UI Text (5)
- `src/pages/auth/LoginPage.tsx` — CURA → MediZen (3 lines)
- `src/components/shell/Sidebar.tsx` — Clinic CMS → MediZen, bg-gray-900 → bg-slate-900
- `src/components/shell/Topbar.tsx` — Clinic CMS → MediZen
- `src/pages/HomePage.tsx` — Clinic CMS → MediZen (dev-mode fallback)
- `src/router/index.tsx` — Comment: Clinic CMS → MediZen

### Brand Rename — Comments (1)
- `src/lib/i18n.ts` — JSDoc: "Clinic CMS" → "MediZen" (hygiene fix)

### Codemod Output (57)
- `src/components/ui/*.tsx` (button, input, dialog, checkbox, etc.) — 191 replacements total
- `src/pages/**/*.tsx` (LoginPage, PatientRegisterPage, PurchaseInPage, ConsultationPage, etc.) — brand- → indigo-
- `src/components/**/*.tsx` (ServicesTab, WalkInModal, etc.) — brand- → indigo-
- **Sample high-touch files**:
  - `PatientRegisterPage.tsx`: 18 replacements
  - `PurchaseInPage.tsx`: 12 replacements
  - Multiple 6–8 replacements

### Recharts Updates (6)
- `src/pages/reports/PrescriptionAnalyticsPage.tsx` — violet → emerald, grid stroke
- `src/pages/reports/RevenueReportPage.tsx` — secondary bar color + grid
- `src/pages/reports/DoctorPerformancePage.tsx` — secondary bar + grid
- `src/pages/reports/VisitVolumePage.tsx` — grid stroke
- `src/pages/dashboard/MainDashboardPage.tsx` — grid stroke
- `src/pages/doctor/DoctorDashboardPage.tsx` — grid stroke

---

## Codemod Statistics

| Metric | Value |
|---|---|
| **Files pre-codemod with `brand-` pattern** | 57 |
| **Replacements (first pass: bg/text/border/ring/from/to/via/fill/stroke)** | 186 |
| **Replacements (second pass: accent-brand-*)** | 5 |
| **Total replacements** | **191** |
| **Files post-codemod with `brand-` pattern** | **0** ✓ |

**Verification**: `grep -rEn "(bg|text|border|ring|from|to|accent|fill|stroke)-brand-" src/` → 0 hits

---

## Test Coverage

| Category | Result | Details |
|---|---|---|
| **Unit Tests** | **547/547 PASS** ✓ | 50 test files, 0 failures, 8.48s |
| **New Design Token Tests** | **18/18 PASS** ✓ | `src/tests/lib/design-tokens.test.ts` |
| **TypeScript** | **0 errors, 0 warnings** ✓ | `npx tsc --noEmit` |
| **ESLint** | **0 errors, 0 warnings** ✓ | `npm run lint --max-warnings 0` |
| **Build** | **PASS in 10.72s** ✓ | 0 errors, 1 pre-existing chunk-size warning |

### Smoke Tests Performed

1. ✓ `tailwind.config.js` contains all 6 color scales (indigo, slate, emerald, amber, red, sky)
2. ✓ No `brand-*` references remain (0 grep hits)
3. ✓ No "CURA" text in TS/TSX (0 hits in UI text)
4. ✓ Google Fonts preconnect + Plus Jakarta Sans 600/700 + Inter 400/500 present
5. ✓ `index.html` title: MediZen ✓
6. ✓ Recharts color palette: indigo primary, emerald secondary, slate-200 grid ✓
7. ✓ CSS variables fixed (dark mode unquoted) ✓
8. ✓ Post-review nit fixes applied (styles.css + i18n.ts) ✓

---

## Brand Mapping — Old → New

| Context | Old | New | Files | Count |
|---|---|---|---|---|
| **App name (UI)** | CURA | MediZen | LoginPage | 3 |
| **App name (UI)** | Clinic CMS | MediZen | Sidebar, Topbar, HomePage, router | 4 |
| **Page title** | Clinic CMS | MediZen | index.html | 1 |
| **Primary color** | `bg-brand-500` | `bg-indigo-500` | 57 files | 191 |
| **Color scale** | `text-brand-*` | `text-indigo-*` | 57 files | (subset of 191) |
| **Recharts secondary** | `#8b5cf6` (violet) | `#10b981` (emerald-500) | 3 chart files | 5 occurrences |
| **Recharts grid** | `#f0f0f0` | `#e2e8f0` (slate-200) | 7 chart files | 7 occurrences |
| **Sidebar bg** | `bg-gray-900` | `bg-slate-900` | Sidebar.tsx | 1 |

---

## Deferred Items — Roadmap

### F.8: Logo SVG Replacement (Shield → MediZen)

**Current state**: Shield icon (placeholder) retained  
**Deferred to**: TASK-040 (Phase D assets) or new sub-task TASK-039b  
**Action**:
- Obtain MediZen logo SVG file
- Replace `src/components/shell/Logo.tsx` (or icon import)
- Verify light/dark mode contrast
- Update favicon.ico + app icon in manifest

**Estimate**: 2–4 hours

### F.9: Favicon + Tauri Config

**Current state**: Not updated  
**Deferred to**: TASK-039b or E2E follow-up  
**Action**:
- Update `public/favicon.ico` (from MediZen logo)
- Update `src-tauri/tauri.conf.json` window title → "MediZen" (if still "Clinic CMS")
- Verify app window icon reflects new brand
- Test Tauri build: `npm run tauri build`

**Estimate**: 1–2 hours

### F.11: Component Restyle — Apply Token Defaults to Component Library

**Current state**: Token names updated (brand- → indigo-) but component library defaults NOT refreshed  
**Deferred to**: **TASK-039b (separate Sprint)** — full component audit  
**Action**:
- Audit all UI components: Button, Input, Select, Textarea, Card, Dialog, Toast, Badge, etc.
- Define MediZen-compliant default variants (sizes, shadows, border radius application)
- Update component props to use new tokens by default
- Ensure dark mode variants on all components
- Re-test all component compositions across screens

**Estimate**: 3–5 days

**Note**: Current codemod applied token class names to instances, but library *defaults* (e.g. `Button` component's `defaultClassName`) may still reference old tokens or need explicit refresh.

### T.1: Playwright Visual Regression Tests

**Current state**: Not in scope for TASK-039  
**Deferred to**: **E2E / VR test phase** (post-smoke, separate task)  
**Action**:
- Set up Playwright screenshot baseline for:
  - Login page (Plus Jakarta Sans heading, Indigo button)
  - MainDashboard (Indigo + Emerald Recharts, slate-200 grid)
  - Sidebar expanded/collapsed (bg-slate-900, indigo-400 icon, "MediZen" text)
  - Topbar (Indigo accents, "MediZen" clinic name)
- Compare actual vs Stitch design exports
- Validate responsive breakpoints (mobile / tablet / desktop)

**Estimate**: 2–3 days (infrastructure + baselines)

### T.2: Dark Mode Parity Test

**Current state**: CSS variables defined; runtime toggle not tested  
**Deferred to**: **E2E / VR test phase**  
**Action**:
- Manual: Toggle dark mode on Login + Dashboard + Sidebar
- Verify: All 6 color scales maintain contrast (WCAG AA)
- Verify: Dark mode CSS vars applied correctly (no broken fallbacks)
- Automated: Playwright dark-mode screenshot baseline (Chromium in dark-mode emulation)

**Estimate**: 1–2 days (manual + automation)

---

## Migration Notes

### Worktree Status

All changes applied to **`clinic-cms-merge/` worktree** on `main` branch:
- Directory: `E:\MyProject\clinic-cms-workspace\clinic-cms-merge`
- Branch: `main`
- Status: Uncommitted (64 files modified)
- Review: Code Review APPROVED; Test phase PASS; Documentation phase ACTIVE

### Next Steps

1. **Commit** (before merging):
   ```
   git add -A
   git commit -m "feat(design-system): port MediZen Modern tokens + brand rename

   - tailwind.config.js: indigo/slate/emerald/amber/red/sky scales
   - Plus Jakarta Sans (display) + Inter (sans) fonts
   - Brand rename: CURA → MediZen, Clinic CMS → MediZen
   - Codemod: 191 brand-* → indigo-* replacements
   - Recharts: violet → emerald secondary, slate-200 grid
   - CSS vars: unquoted dark mode hex
   - 18 new design-tokens tests (100% pass)
   - Build: PASS | Tests: 547/547 | TS: 0 errors | Lint: 0 errors
   "
   ```

2. **Test phase**: Already complete (547/547 tests pass)

3. **Merge to main** (after approval):
   ```
   git checkout main
   git merge clinic-cms-merge
   ```

4. **Downstream tasks** can now begin (TASK-034, TASK-035, TASK-036, TASK-040, TASK-042)

---

## References

1. **Design System Asset**: [Stitch MediZen Modern](https://stitch.withgoogle.com/projects/2542650746708884228) — `assets/3512187121078190969`

2. **Design System Spec**: [MEDIZEN_FRESH_PROJECT.md](../../../../../../design/medizen-modern/MEDIZEN_FRESH_PROJECT.md) — 45 canonical screens, token mapping, deferred items

3. **FE Audit Reports**:
   - [TASK-032 FE Audit — A.1](../../../../../TASK-032/handoff/fe-audit-report.md) — discovery of token debt
   - [TASK-032 FE Audit — Final](../../../../../TASK-032/deliveries/final-specs/audit-report.md) — full analysis + recommendations

4. **Implementation Handoff**: [impl-to-review.md](../../../handoff/impl-to-review.md)

5. **Code Review Report**: [review-to-test.md](../../../handoff/review-to-test.md)

6. **Test Report**: [test-to-documentation.md](../../../handoff/test-to-documentation.md)

---

## Completion Summary

| Gate | Status | Details |
|---|---|---|
| **Functional requirements** | ✅ DONE | Token rewrite, codemod, brand rename, font update, Recharts color palette |
| **Build gate** | ✅ PASS | 0 errors, 1 pre-existing chunk-size warning |
| **Test gate** | ✅ PASS | 547/547 unit + 0 TS + 0 lint + 18 new design-token tests |
| **Code review** | ✅ APPROVED | 2 minor nits fixed (CSS hex quote, JSDoc comment) |
| **Documentation gate** | ✅ ACTIVE | Functional design doc (this file), task.md updated, dashboard.md updated |

**Status**: TASK-039 DONE ✅ — Ready for Merge

**Unblocks**: TASK-034 (BHYT), TASK-035 (sidebar), TASK-036 (Cmd+K), TASK-040 (Phase D), TASK-042 (EMR)

