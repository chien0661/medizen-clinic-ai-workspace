# TASK-068 — Review → Test Handoff

**Task**: Theme Selection & Customization System
**Branch**: `feature/TASK-068-theme-system` (clinic-cms-web)
**Reviewed commit**: `e0f0d34` — *fix(theme): move @import, wire sidebar+button tokens, persist custom color (TASK-068)*
**Reviewer**: Code Review Agent (round 2)
**Date**: 2026-05-31

## Decision: APPROVED → proceed to Testing

Round-1 CHANGES_REQUESTED blockers are all resolved and verified. The feature is now functional: theme CSS loads in the compiled bundle, the sidebar + primary buttons consume theme tokens, and the custom primary color persists across reload.

---

## Round-1 issues — verification status

| ID | Severity | Status | Evidence |
|----|----------|--------|----------|
| **C1** Theme CSS never loaded | CRITICAL | **FIXED** | `@import "./styles/themes.css"` now sits at the very top of `src/styles.css`, above the `@tailwind` directives. `npx vite build` → compiled `dist/assets/index-*.css` contains all 6 presets (`medical-blue`, `emerald-health`, `soft-lavender`, `warm-coral`, `midnight-dark`, `slate-professional`), plus `data-theme`, `--theme-sidebar-bg`, `--theme-primary` (grep count ≥1 each). |
| **M1** No component consumes tokens | MAJOR | **FIXED** | `src/components/shell/Sidebar.tsx` now uses `bg-theme-sidebar`, `text-theme-sidebar-text`, `bg-theme-primary`, `hover:bg-theme-sidebar-hover`. `src/components/ui/button.tsx` default variant → `bg-theme-primary text-theme-primary-text hover:bg-theme-primary-hover active:bg-theme-primary-hover`, focus ring → `ring-theme-primary`. All tokens are defined in both `tailwind.config.js` (lines 120-126) and `src/styles/themes.css`; `theme-sidebar-bg)` utility is emitted in the compiled CSS. |
| **M2** Tests don't assert CSS application | MAJOR | **FIXED (within vitest limits)** | `src/tests/shell/themeStore.test.ts` adds an `applyDataTheme` block asserting `setAttribute('data-theme', preset)` for all 6 presets. jsdom/happy-dom can't resolve `@import`, so true `getComputedStyle` resolution is correctly deferred to the e2e/Playwright layer (see Test Focus below). |
| **N2** customPrimaryColor not persisted | MINOR | **FIXED** | `src/stores/themeStore.ts`: `setCustomPrimaryColor` persists to `localStorage["theme-custom-primary"]`; `resetToDefault` removes it; store init restores it and re-applies `--theme-primary`. `index.html` FOUC script reads `theme-custom-primary`, validates `/^#[0-9a-fA-F]{6}$/`, and applies the RGB triplet before React renders. 3 new persistence tests added. |

## Build / test / quality gate results (round 2)

- **Unit tests**: 914/914 PASS, 88 files, 0 failures (`npm test`). Note: the previously-flagged VssIntegrationConfigPage failure is now also green — suite is fully clean.
- **`npx vite build`**: succeeds; CSS verification passes (see C1 above). NOTE: `npm run build` (which runs `tsc` first) fails on **pre-existing** type errors unrelated to TASK-068 — see "Pre-existing issues" below. The CSS bundle is correctly produced by vite.
- **`npm run type-check`**: 9 errors, **all pre-existing** and in files NOT touched by TASK-068 (admin/api.ts, LoginPage, PatientDetailPage, field.tsx, i18n test, and Sidebar's `ShieldCheck`/`bhytEnabled` unused-vars which originate from the TASK-045 merge, NOT this branch — verified the feature commit `c9a09d7` never touched Sidebar.tsx and the fix commit only changed Tailwind class strings).
- **`npm run lint`**: 17 errors, **all pre-existing** (VssSyncLogPage conditional-hooks, i18n-default-language.test unused import). None in TASK-068-touched files.
- **No new security issues**: no secrets, no `console.log`, storage access wrapped in try/catch.

## Pre-existing issues (NOT introduced by TASK-068 — do not block this task)

- Type errors in `src/modules/admin/api.ts`, `src/pages/auth/LoginPage.tsx`, `src/pages/patients/PatientDetailPage.tsx`, `src/components/ui/field.tsx`, `src/tests/lib/i18n-default-language.test.ts`, and Sidebar unused-var warnings (from TASK-045 merge).
- Lint errors in `src/pages/admin/VssSyncLogPage.tsx` (rules-of-hooks) and the i18n test.
- These predate the feature branch; flag to manager for a separate cleanup task if desired.

---

## Test Focus (for Test Agent)

The unit layer is green but, by design, cannot prove CSS variables resolve. Prioritize these e2e/manual checks in a real browser (dev server `localhost:1420`):

1. **CSS resolution per preset** — for each of the 6 presets, set `data-theme` (via the picker) and assert
   `getComputedStyle(document.documentElement).getPropertyValue('--theme-primary')` is non-empty and matches the expected RGB triplet in `src/styles/themes.css`.
2. **Visible theme switch** — selecting a theme visibly changes the **sidebar background** (`--theme-sidebar-bg`) and **primary button** color. Default action buttons and the active sidebar item should recolor.
3. **Live preview** — hover-preview in the picker applies/reverts without flicker; AC "live preview mượt".
4. **Persistence + FOUC** — pick a non-default theme + a custom primary color, reload: theme and custom color restore with no flash (FOUC script in `index.html`). Confirm `localStorage["theme-preference"]` and `localStorage["theme-custom-primary"]` are written.
5. **Reset** — `resetToDefault` returns to medical-blue AND clears the custom color from localStorage + removes the inline `--theme-primary`.
6. **Dark mode interop (N1)** — verify `.dark` class behavior layers correctly with `data-theme`. Note `midnight-dark` is a palette, not a dark-mode toggle (potential UX tooltip — non-blocking).
7. **Responsive + a11y** — picker on mobile/tablet; WCAG AA contrast per preset; keyboard navigation of the listbox (N4: hover-preview has no keyboard-focus equivalent — accessibility nicety, non-blocking).

## Remaining minor notes (non-blocking, carry to Test/Docs)

- **N1** — `midnight-dark` preset name may mislead (palette, not dark-mode switch). Consider tooltip/rename.
- **N3** — `applyDataTheme`/custom-color restore run at module import AND in the inline `index.html` script (double-apply). Harmless, just noted.
- **N4** — Picker live preview is hover/mouse driven; no keyboard-focus preview equivalent.
- **M3 (round 1)** — the bundled MediZen Pro rebrand (Sora font, teal palette, radius changes) remains in the branch. Confirm with manager whether it belongs in TASK-068 scope or should be split; not a code-correctness blocker.
