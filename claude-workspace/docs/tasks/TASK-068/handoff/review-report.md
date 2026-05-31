# TASK-068 — Code Review Report

**Task**: Theme Selection & Customization System
**Branch**: `feature/TASK-068-theme-system` (clinic-cms-web)
**Reviewed commit**: `c9a09d7` — *feat(theme): add theme selection system with 6 presets + live preview (TASK-068)*
**Reviewer**: Code Review Agent
**Date**: 2026-05-31

## Decision: CHANGES_REQUESTED

The code is well-structured, fully typed, lint-clean, and all 32 unit tests pass. **However, the feature is non-functional in the running application** — the theme CSS never loads, so selecting any theme has zero visual effect. This is a blocking defect verified in both production build and the live dev server.

---

## Verification Summary

| Check | Result |
|-------|--------|
| New unit tests (32) | PASS — 32/32 |
| Full test suite regressions | None introduced (5 pre-existing billing/notifications/pharmacy failures unchanged) |
| `npm run type-check` | No NEW errors from TASK-068 files (6 errors are all pre-existing on `main`) |
| ESLint (6 new files) | PASS — clean |
| `vite build` | Builds successfully... |
| **Theme CSS in build output** | **FAIL — `themes.css` entirely absent from compiled CSS** |
| **Theme CSS in live dev app** | **FAIL — zero `[data-theme="..."]` rules loaded; `--theme-*` vars all undefined** |

---

## CRITICAL Issues (must fix)

### C1. Theme CSS is never loaded — feature has no visual effect

**File**: `src/styles.css` (lines 1–6)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* TASK-068: Theme preset CSS variables (must come before :root overrides) */
@import "./styles/themes.css";   /* ← INVALID PLACEMENT */
```

Per the CSS spec, `@import` **must precede all other statements** (except `@charset`). Because this `@import` sits *after* the `@tailwind` directives, PostCSS / `postcss-import` treats it as invalid and silently drops it. The entire contents of `themes.css` (all six `[data-theme="..."]` blocks and every `--theme-*` variable) never make it into the output.

**Evidence:**
- Production build: `grep` for `emerald-health`, `--theme-sidebar-bg`, `data-theme`, `--theme-primary` in `dist/assets/*.css` → **0 matches**.
- Live dev server (`localhost:1420`): enumerated `document.styleSheets` — the only `data-theme` rules present belong to the Sonner toast library. After setting `data-theme="medical-blue"` AND `data-theme="emerald-health"` on `<html>`, `getComputedStyle(document.documentElement).getPropertyValue('--theme-primary')` returns **empty** for both.

**Net effect:** The Zustand store, the FOUC inline script, and the picker all correctly set `data-theme` on `<html>`, but there are no CSS rules to match it. Picking a theme (even the default) changes nothing on screen. This fails Acceptance Criteria "Người dùng có thể chọn theme... toàn bộ UI cập nhật ngay" and "Live preview hoạt động mượt".

**Fix (verified):** Move the `@import` to the very top of `src/styles.css`, before the `@tailwind` directives:

```css
@import "./styles/themes.css";
@tailwind base;
@tailwind components;
@tailwind utilities;
```

I temporarily applied this and rebuilt: the compiled CSS then contained `emerald-health` and `--theme-sidebar-bg` (count 1). I reverted the change so the branch is left exactly as submitted. **Note:** the inline comment "must come before :root overrides" shows the intent was correct — only the physical placement is wrong.

---

## MAJOR Issues (should fix before approval)

### M1. No component consumes the theme tokens — themes change nothing even once CSS loads

Even after fixing C1, selecting a theme would still produce no visible change, because **no component in the app uses the `theme-*` Tailwind tokens or `--theme-*` variables**.

- `grep` for `theme-primary | theme-sidebar | theme-accent` across `src/**/*.tsx` (excluding tests + ThemePicker's own swatches) → **0 matches**.
- Sidebar, Topbar, buttons, tables, cards, badges, charts all still use hard-coded `brand-*` / `indigo-*` / `slate-*` classes.
- The custom-primary-color override sets `--theme-primary` inline on `<html>`, but nothing reads that variable, so the color picker also has no effect.

The task's Acceptance Criteria explicitly require the theme to apply to "sidebar, header, tables, buttons, cards, badges, charts." As implemented, the picker is a fully wired control panel attached to nothing. The implementer flagged the sidebar gap as a possible "follow-up," but given the AC, this is **MAJOR**, not minor — at minimum the primary action color and sidebar should be migrated to theme tokens so the feature is observably functional. If a phased rollout is intended, that must be agreed with the manager and the AC/scope adjusted; it cannot silently pass review as-is.

### M2. Unit tests validate JS state but not CSS application — gave false confidence

The 32 tests assert that the store updates `activeTheme`, that `data-theme` is set on `document.documentElement`, and that the hook delegates correctly. None assert that any CSS variable actually resolves to a value. That is why a 100%-green suite coexists with a completely non-functional feature. A test that reads `getComputedStyle(...).getPropertyValue('--theme-primary')` after switching themes would have caught C1. Recommend adding at least one such integration-style assertion (jsdom won't resolve `@import`, so this likely belongs in the Playwright/e2e layer the Test agent will build).

### M3. Out-of-scope design-system changes bundled into the theme commit

Commit `c9a09d7` also rewrites unrelated design tokens not mentioned in the handoff:
- `index.html`: swaps the display font from **Plus Jakarta Sans → Sora**.
- `tailwind.config.js`: adds a full **`brand` teal palette**, changes `borderRadius` (`card` 12→16, `input` 8→10, adds `btn`), adds `spacing.section`, adds `boxShadow.card`.
- `src/styles.css`: changes `--color-bg`, `--color-text`, `--color-brand` (indigo→teal), bumps base body font size to 15px.

These "MediZen Pro" rebrand changes are a separate concern from theme *selection* and affect the global look of the whole app. They should either be split into their own task/commit or be explicitly documented and approved as part of this scope. Bundling them makes the diff hard to reason about and couples an unrelated rebrand to the theme-picker review.

---

## MINOR Issues / Notes

- **N1 — Dark-mode + theme interop:** Could not be visually verified because the theme CSS doesn't load (C1). The architecture (independent `.dark` class + `data-theme`) is sound in principle; re-verify after C1 is fixed. Note that the `midnight-dark` preset only sets sidebar/primary vars — it does not flip the app into the `.dark` background scheme, so its name may mislead users (it is a palette, not a dark-mode toggle). Worth a tooltip or rename.
- **N2 — `customPrimaryColor` not persisted:** `setTheme`/`resetToDefault` persist to `localStorage`, but `setCustomPrimaryColor` only sets store state + inline style; the custom hex is lost on reload (and the FOUC script doesn't restore it). The task asks for "Tùy chỉnh được lưu vào... localStorage." Minor only because the feature is blocked upstream by C1/M1.
- **N3 — `applyDataTheme`/`readPersistedTheme` run at module import time** (side effect on load). Works, but duplicates the inline `index.html` script. Acceptable; just noting the double-apply.
- **N4 — Picker is keyboard/hover driven:** hover preview (`onMouseEnter`/`onMouseLeave`) has no keyboard-focus equivalent, so keyboard users get no live preview. Accessibility nicety, not blocking.

---

## What's Good

- Clean separation: store / hook / component, each with focused tests.
- TypeScript types are precise (`ThemePresetId` union, `THEME_PRESETS as const`).
- `hexToRgbTriplet` is correct and tested; storage access is wrapped in try/catch for private-browsing safety.
- FOUC inline script validates against an allow-list before applying — good defensive coding.
- No secrets, no `console.log`, no TODO/FIXME in the new files.
- ThemePicker has solid a11y scaffolding (`role="listbox"`/`option`, `aria-selected`, `aria-label`s, `data-testid`s).
- Lint-clean and zero new type errors.

---

## Required Actions for Re-submission

1. **(C1)** Move `@import "./styles/themes.css";` to the top of `src/styles.css`, above the `@tailwind` directives. Verify with a production build that `dist/assets/*.css` contains the `[data-theme="..."]` blocks.
2. **(M1)** Migrate at least the primary action color and the sidebar to the `theme-*` tokens so theme switching is observably functional per the AC (or get explicit manager sign-off on a reduced/phased scope and update the task AC accordingly).
3. **(M2)** Add at least one assertion that a `--theme-*` variable actually resolves after a theme switch (e2e/Playwright layer is fine).
4. **(M3)** Confirm with the manager whether the bundled font/brand/radius rebrand belongs in TASK-068; split out if not.
5. **(N2)** Persist + restore `customPrimaryColor` (localStorage + FOUC script), or descope it explicitly.

Re-run after fixes: `vite build` + grep the compiled CSS for `emerald-health`, then visually confirm a theme switch changes the primary/sidebar colors in the running app.
