---
task: TASK-039
handoff: implementation → review
date: 2026-05-01
author: code-implementation agent
status: ready-for-review
---

# TASK-039 Implementation Handoff — MediZen Design System Port

## Summary

All TASK-039 acceptance criteria met. Build passes. All 547 tests pass (new 18 design-tokens tests included).

---

## Files Modified (count: 64)

### Config / Root

| File | Change |
|---|---|
| `tailwind.config.js` | Full rewrite — removed `brand` color group, added Indigo/Slate/Emerald/Amber/Red/Sky scales + `surface` tokens, `borderRadius` card/input/chip, `fontFamily.display` (Plus Jakarta Sans) + `fontFamily.sans` (Inter), `spacing` baseline/gutter |
| `index.html` | Added Google Fonts preconnect + link (Plus Jakarta Sans 600/700 + Inter 400/500), renamed `<title>` to `MediZen`, updated description |

### New Files

| File | Change |
|---|---|
| `src/lib/tokens.ts` | New — exports full MediZen design tokens (colors, chartColors, borderRadius, spacing, fontFamily) for JS-side use |
| `src/tests/lib/design-tokens.test.ts` | New — 18 Vitest smoke tests for tokens.ts (all pass) |

### CSS Variables

| File | Change |
|---|---|
| `src/styles.css` | Updated CSS variables to MediZen palette (`--color-brand: #6366f1`, `--color-bg: #f8fafc` slate-50, `--color-border: #e2e8f0` slate-200, dark mode updated accordingly) |

### Brand Rename Files

| File | Change |
|---|---|
| `src/pages/auth/LoginPage.tsx` | "CURA" → "MediZen" at lines 236, 275, 452 (3 occurrences) |
| `src/components/shell/Sidebar.tsx` | "Clinic CMS" → "MediZen", `bg-gray-900` → `bg-slate-900`, `text-indigo-400` (was already fixed by codemod) |
| `src/components/shell/Topbar.tsx` | "Clinic CMS" → "MediZen" |
| `src/pages/HomePage.tsx` | "Clinic CMS" → "MediZen" (inline `<h1>` in dev-mode fallback page) |
| `src/router/index.tsx` | Comment-only: "Clinic CMS" → "MediZen" |

### Codemod — brand- → indigo- (57 files, 190 occurrences)

The sed-based codemod replaced all `bg-brand-*`, `text-brand-*`, `border-brand-*`, `ring-brand-*`, `from-brand-*`, `to-brand-*`, `via-brand-*`, `fill-brand-*`, `stroke-brand-*`, `accent-brand-*` → corresponding `indigo-*` variants across 57 files.

Post-codemod grep confirms: **0 remaining `brand-` references** in `src/`.

Key files touched by codemod (sample):

- `src/components/ui/button.tsx` — 3 occurrences
- `src/components/ui/input.tsx` — 1 occurrence
- `src/components/ui/dialog.tsx` — 1 occurrence
- `src/components/ui/checkbox.tsx` — 2 occurrences
- `src/pages/auth/LoginPage.tsx` — 6 occurrences
- `src/pages/patients/PatientRegisterPage.tsx` — 18 occurrences (highest single file)
- `src/pages/pharmacy/PurchaseInPage.tsx` — 12 occurrences
- `src/pages/doctor/ConsultationPage.tsx` — 6 occurrences
- `src/components/doctor/ServicesTab.tsx` — 8 occurrences
- `src/pages/reception/WalkInModal.tsx` — 8 occurrences
- (51 additional files with 1–7 occurrences each)

Also replaced 5 `accent-brand-*` occurrences (pattern not in initial sed command, caught in a second pass):
- `src/components/billing/AddLineModal.tsx`
- `src/components/billing/AddPaymentModal.tsx`
- `src/pages/admin/OnboardingPage.tsx` (2 occurrences)
- `src/pages/admin/ExtraPermissionsPage.tsx`

### Recharts Palette Updates

| File | Change |
|---|---|
| `src/pages/reports/PrescriptionAnalyticsPage.tsx` | `PIE_COLORS` updated: `#8b5cf6` (violet) → `#10b981` (emerald-500); grid stroke `#f0f0f0` → `#e2e8f0` |
| `src/pages/reports/RevenueReportPage.tsx` | Secondary bar `fill="#8b5cf6"` → `#10b981`; grid stroke updated |
| `src/pages/reports/DoctorPerformancePage.tsx` | Secondary bar fill + grid stroke updated |
| `src/pages/reports/VisitVolumePage.tsx` | Grid stroke updated |
| `src/pages/dashboard/MainDashboardPage.tsx` | Grid stroke updated |
| `src/pages/doctor/DoctorDashboardPage.tsx` | Grid stroke updated |

Primary color was already `#6366f1` (indigo-500) in all chart pages — no change needed.

---

## Codemod Stats

| Metric | Count |
|---|---|
| Files with `brand-` pattern (pre-codemod) | 57 |
| Total `(bg|text|…)-brand-*` occurrences replaced (first pass) | 186 |
| `accent-brand-*` occurrences replaced (second pass) | 5 |
| **Total replacements** | **191** |
| Files with `brand-` pattern (post-codemod) | **0** |

---

## Brand Text Replacements

| String | Occurrences Found | Replaced |
|---|---|---|
| `CURA` (UI text in LoginPage) | 3 | 3 — all replaced |
| `Clinic CMS` (UI text in Sidebar, Topbar, HomePage) | 3 | 3 — all replaced |
| `Clinic CMS` in `index.html` `<title>` | 1 | 1 — replaced with `MediZen` |
| `Clinic CMS` in `router/index.tsx` comment | 1 | 1 — replaced (comment hygiene) |
| `appName: "Clinic CMS"` in i18n JSON | 2 | **NOT replaced** — per task constraint "Do NOT touch i18n strings (separate task)" |
| `appName: "Clinic CMS"` in `src/tests/shell/i18n.test.ts` | 2 | **NOT replaced** — test for i18n key, not UI text |
| `Clinic CMS` in `apiClient.ts` comment | 1 | **NOT replaced** — comment-only, no functional impact |

---

## Spec Deviations & Decisions

1. **Tailwind full color scales defined explicitly**: Although Tailwind 3 ships default scales for indigo/slate/emerald/amber/red/sky, they were defined explicitly in `tailwind.config.js` under `theme.extend.colors` to make the MediZen palette canonical and self-documenting. This also ensures the explicit hex values match the spec exactly (e.g., indigo-500 = `#6366f1`).

2. **Secondary Recharts bar color**: Spec says use `emerald-500` for secondary series. Pre-existing code used violet (`#8b5cf6`). Changed to `#10b981` (emerald-500) per spec.

3. **Sidebar bg-indigo-900 vs bg-slate-900**: Task spec says "bg-indigo-900 or bg-slate-900 per spec (verify with Stitch screen)". Without Stitch screen access, chose `bg-slate-900` (`#0f172a`) — consistent with a dark neutral sidebar that lets Indigo accents (active item highlight `bg-indigo-500`) pop. Reviewer should confirm against Stitch design.

4. **accent-brand-500 pattern missed by first sed run**: The initial sed command only targeted `bg|text|border|ring|from|to|via|fill|stroke`. A follow-up pass caught `accent-brand-*` in 5 places. All replaced.

5. **F.8 / F.9 logo asset replacement**: Out of scope per task instructions — Shield icon retained, only text renamed.

6. **F.11 Component restyle audit**: Out of scope for TASK-039 per implementation brief — "Token rewrite + global brand rename". Full component restyle (Button variants, Input treatments, Card shadow/radius, Modal, Toast, Badge) deferred to a follow-up task.

7. **T.1 Visual regression (Playwright)**: Out of scope per implementation brief — brief specifies only Vitest smoke test + build check. Visual regression tests are separate scope.

---

## Build Output

```
✓ built in 21.46s
```

**Errors**: 0
**Warnings**: 1 pre-existing chunk size warning (`index-*.js` 1,108 kB) — unrelated to this task.

---

## Test Results

```
Test Files  50 passed (50)
     Tests 547 passed (547)
  Duration  19.11s
```

New tests: `src/tests/lib/design-tokens.test.ts` — 18 tests, all passing.

---

## Files NOT Touched (suspected future attention)

| File | Reason |
|---|---|
| `src/locales/vi/common.json`, `src/locales/en/common.json` | `appName: "Clinic CMS"` — i18n strings, separate task |
| `src/tests/shell/i18n.test.ts` | Asserts `common:appName === "Clinic CMS"` — needs update when i18n strings are renamed |
| `src/lib/apiClient.ts` | Comment references "Clinic CMS" — cosmetic |
| `src/components/ui/button.tsx` | Only token codemod done — full MediZen variant restyle (sizes, shadows) for TASK-039 F.11 |
| `src/components/ui/input.tsx` | Same — border-radius `rounded-input` not yet applied |
| `src/components/ui/dialog.tsx` | Same — card radius not yet applied |
| `src-tauri/tauri.conf.json` | App window title may still say "Clinic CMS" — F.9 Tauri config update deferred |
| Playwright e2e tests in `e2e/` | Visual regressions (T.1) not run — separate scope |
