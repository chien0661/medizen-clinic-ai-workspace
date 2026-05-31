---
id: TASK-039
type: feature
title: MediZen Modern design system port — Tailwind tokens + Indigo brand + fonts + brand rename
status: DONE
priority: High
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
completed: 2026-05-01
branch: clinic-cms-merge (main)
jira_key: ""
tags: [design-system, tailwind, branding, ui, fe, foundation]
affected-repos: [clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/MEDIZEN_FRESH_PROJECT.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/2542650746708884228"
  confluence: ""
  jira_ticket: ""
  other:
    - "../TASK-032/handoff/fe-audit-report.md"
    - "../TASK-032/deliveries/final-specs/audit-report.md"
    - "../../design/medizen-modern/MEDIZEN_FRESH_PROJECT.md"
    - "handoff/impl-to-review.md"
    - "handoff/review-to-test.md"
    - "handoff/test-to-documentation.md"
    - "deliveries/final-specs/design-system-port-functional-design.md"
---

# TASK-039: MediZen Modern design system port

## Description

Replace "VISSoft blue + Segoe UI + CURA" branding with "MediZen Indigo + Plus Jakarta Sans/Inter" per Stitch design system asset `3512187121078190969`. Token rewrite + global brand rename + every `bg-brand-*` / `text-brand-*` reference touched.

This is a **visual-blocker**: every other UI sub-task (TASK-034 BhytConfig, TASK-035 sidebar grouping, TASK-036 CommandPalette, TASK-040 Phase D screens, TASK-042 EMR tabs) inherits the new tokens, so this lands first or in parallel with TASK-033.

## Requirements

### Tokens

- [ ] **F.1** Rewrite `tailwind.config.js`:
  - `colors`: Indigo `#6366F1` primary (50-900 scale), Slate `#0F172A` secondary, Emerald `#10B981`, Amber `#F59E0B`, Red `#EF4444`, Sky `#0EA5E9`
  - Surface: white; page bg: slate-50; border: slate-200
  - `borderRadius`: card 12px / input 8px / chip 6px
  - `fontFamily.display: ['Plus Jakarta Sans', 'sans-serif']`, `fontFamily.sans: ['Inter', 'sans-serif']`
  - Spacing baseline 4px / gutter 24px
  - Keep `darkMode: 'class'` + add dark variants for every new color
- [ ] **F.2** `index.html`: add font preconnect + link for Plus Jakarta Sans 600/700 + Inter 400/500
- [ ] **F.3** `src/styles.css`: update CSS variables if any
- [ ] **F.4** New `src/lib/tokens.ts` exporting design tokens for JS-side use (Recharts theming, etc.)

### Brand rename

- [ ] **F.5** Codemod: replace `text-brand-*` / `bg-brand-*` / `border-brand-*` → `text-indigo-*` / `bg-indigo-*` / `border-indigo-*` across `src/`
- [ ] **F.6** Replace literal "CURA" → "MediZen" in `LoginPage.tsx` (lines 236, 276, 452)
- [ ] **F.7** Replace literal "Clinic CMS" → "MediZen" in `Sidebar.tsx`, `Topbar.tsx` (logo + greeting), `index.html` `<title>`
- [ ] **F.8** Replace logo asset (Shield icon → MediZen logo SVG)
- [ ] **F.9** Update favicon.ico + app icon in Tauri config
- [ ] **F.10** Sidebar bg: change `bg-gray-900` → `bg-indigo-900` or `bg-slate-900` per spec (verify with Stitch screen)

### Component restyle (apply tokens)

- [ ] **F.11** Audit + restyle: `Button` component variants, `Input`/`Select` field treatments, `Card` shadow/radius, `Modal` overlay, `Toast` colors, `Badge` chip radius
- [ ] **F.12** Recharts theme: update `BarChart`/`LineChart`/`PieChart` axis + tooltip + legend colors to Indigo/Slate/Emerald/Amber

### Tests

- [ ] **T.1** Visual regression (Playwright screenshot): Login, MainDashboard, Sidebar collapsed/expanded, Topbar — compare to Stitch screen exports
- [ ] **T.2** Dark mode parity test for each new color

## Acceptance Criteria

- [x] **F.1** `tailwind.config.js` matches MediZen tokens spec — DONE ✓
- [x] **F.2** Google Fonts preconnect + Plus Jakarta Sans 600/700 + Inter 400/500 — DONE ✓
- [x] **F.3** `src/styles.css` CSS variables updated — DONE ✓
- [x] **F.4** `src/lib/tokens.ts` design token export — DONE ✓
- [x] **F.5** Codemod: 191 `brand-*` → `indigo-*` replacements, 0 remaining — DONE ✓
- [x] **F.6** "CURA" → "MediZen" in LoginPage (3 lines) — DONE ✓
- [x] **F.7** "Clinic CMS" → "MediZen" in Sidebar, Topbar, index.html — DONE ✓
- [ ] **F.8** Logo asset replacement (Shield → MediZen SVG) — **DEFERRED** to TASK-040 or TASK-039b
- [ ] **F.9** Favicon + Tauri icon config — **DEFERRED** to TASK-039b or E2E follow-up
- [x] **F.10** Sidebar bg: `bg-gray-900` → `bg-slate-900` — DONE ✓
- [ ] **F.11** Component restyle audit (Button/Input/Card/Modal/Toast/Badge) — **DEFERRED** to TASK-039b (separate Sprint)
- [x] **F.12** Recharts theme: Indigo/Emerald/Slate colors — DONE ✓
- [ ] **T.1** Playwright visual regression (Login/Dashboard/Sidebar) — **DEFERRED** to E2E / VR test phase
- [ ] **T.2** Dark mode parity test (WCAG AA contrast) — **DEFERRED** to E2E / VR test phase

### Deferred Items Explanation

- **F.8 (Logo SVG)**: Asset management requires source file; recommend as separate sub-task to keep design-system token work focused.
- **F.9 (Favicon/Tauri)**: Desktop app config; dependent on logo asset (F.8); defer to F.8 completion or TASK-039b.
- **F.11 (Component restyle)**: Full component library audit (Button variants, shadow/radius defaults, dark mode) is 3–5 day effort; recommend as **TASK-039b** to parallelize with TASK-034/035/036.
- **T.1 (Playwright VR)**: Visual regression infrastructure not yet in place; defer to dedicated E2E / VR test phase (post-smoke tests).
- **T.2 (Dark mode parity)**: CSS vars in place; runtime validation deferred to E2E phase to unblock downstream visual tasks.

### Core Acceptance Criteria (Met)

- [x] `tailwind.config.js` matches MediZen tokens spec — verified against MEDIZEN_FRESH_PROJECT.md
- [x] No `bg-brand-*` / `text-brand-*` references remain in `src/` — **0 grep hits** ✓
- [x] No "CURA" / "Clinic CMS" text strings in UI (non-i18n sources) — **0 hits** ✓
- [x] Recharts dashboards use new color palette (indigo primary, emerald secondary, slate-200 grid) — code verified ✓
- [x] FE build passes; smoke test 547/547 unit tests pass + 0 TS + 0 lint — PASS ✓

## Dependencies

- Blocked by: none (independent — can run in parallel with all BE work)
- Blocks: TASK-034, TASK-035, TASK-036, TASK-040, TASK-042 (visual conformance for new screens)

## Effort

**Medium** (2-3 days). Token rewrite surgical; codemod + brand replacement mechanical but wide.

## Risk

LOW. Visual regressions caught by snapshot tests; dark mode is the only sneaky risk.

## Notes

- Discovery via TASK-032 FE audit A.1, A.2 + cross-cutting #1.
- Stitch design system asset: `3512187121078190969` (do NOT regenerate — reuse).
- Reference: `docs/design/medizen-modern/MEDIZEN_FRESH_PROJECT.md`.

---

## Completion Notes (2026-05-01)

### Functional Design Document

Published: [`docs/tasks/TASK-039/deliveries/final-specs/design-system-port-functional-design.md`](deliveries/final-specs/design-system-port-functional-design.md)

Content:
- Port mục đích, phạm vi, token mapping
- 64 files modified summary (config, new files, brand rename, codemod)
- Codemod stats: 191 replacements, 0 remaining `brand-*` references
- Token table: Tailwind colors / border radius / fonts / spacing with spec mapping
- Brand mapping: old → new (CURA → MediZen, etc.)
- Deferred items (F.8/F.9/F.11/T.1/T.2) with recommendations
- Migration notes: worktree status, commit message template

### Test & Review Results

| Gate | Result | Details |
|---|---|---|
| **Unit Tests** | ✅ 547/547 PASS | 50 test files, 18 new design-tokens tests, 0 failures |
| **TypeScript** | ✅ 0 errors | `npx tsc --noEmit` clean |
| **Linter** | ✅ 0 warnings | `npm run lint` max-warnings 0 ✓ |
| **Build** | ✅ PASS | 10.72s, 0 errors, 1 pre-existing chunk-size warning |
| **Code Review** | ✅ APPROVED | 2 minor cosmetic nits fixed by manager (styles.css CSS quote, i18n.ts JSDoc) |

### Files Modified

**Count**: 64 files
- `tailwind.config.js` — full rewrite
- `index.html` — Google Fonts preconnect + link, title/description
- `src/lib/tokens.ts` — new token export module
- `src/tests/lib/design-tokens.test.ts` — new 18-test suite
- `src/styles.css` — CSS variables + dark mode (nit fix: unquoted hex)
- Brand rename: 5 files (LoginPage, Sidebar, Topbar, HomePage, router)
- Codemod output: 57 files (brand-* → indigo-*)
- Recharts: 6 files (color palette + grid stroke)

### Codemod Statistics

- **Replacements**: 191 (186 first pass + 5 accent-brand second pass)
- **Files touched**: 57
- **Remaining `brand-*` references**: **0** ✓
- **Verification**: `grep -rEn "(bg|text|border|…)-brand-" src/` → 0 hits

### Review Nits Fixed by Manager

1. **styles.css line 21** — Dark mode `--color-brand` value unquoted (was quoted hex string, broke CSS var)
2. **i18n.ts line 2** — JSDoc "Clinic CMS" → "MediZen" (hygiene)

Both applied before test phase; no functional impact on current codebase.

### Deferred Items Routing

| Item | Recommendation | Effort |
|---|---|---|
| **F.8 Logo SVG** | TASK-040 (Phase D assets) or TASK-039b | 2–4h |
| **F.9 Favicon/Tauri** | TASK-039b or E2E follow-up | 1–2h |
| **F.11 Component restyle** | **TASK-039b (separate Sprint)** — full audit of Button/Input/Card/Modal/Toast/Badge defaults | 3–5d |
| **T.1 Playwright VR** | E2E / VR test phase (infrastructure setup + baselines) | 2–3d |
| **T.2 Dark mode parity** | E2E / VR test phase (runtime validation + WCAG AA checks) | 1–2d |

### Worktree Note

Changes live on **`clinic-cms-merge` worktree** at `E:\MyProject\clinic-cms-workspace\clinic-cms-merge` (branch: `main`).
- 64 files modified
- Uncommitted (ready for commit + merge when approved)
- Recommended commit message included in functional-design.md

### Unblocks

Ready to unblock:
- TASK-034 (BHYT toggle wiring) — needs MediZen tokens
- TASK-035 (Multi-role sidebar UX) — needs MediZen tokens + sidebar bg decision
- TASK-036 (Cmd+K Quick Search) — needs MediZen tokens for palette UI
- TASK-040 (Phase D screens port) — needs fonts + token defaults
- TASK-042 (EMR 8-tab refactor) — needs Recharts color palette + token refresh
