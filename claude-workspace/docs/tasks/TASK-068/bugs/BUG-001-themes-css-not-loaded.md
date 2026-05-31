# BUG-001: themes.css Not Loaded — @import After @tailwind Directives

**Task**: TASK-068 Theme Selection & Customization System
**Severity**: CRITICAL (blocks all visual theme switching)
**Found by**: Test Agent (E2E CSS variable verification)
**Date**: 2026-05-31
**Status**: OPEN

---

## Summary

`@import "./styles/themes.css"` is placed on line 6 of `src/styles.css`, **after** the three `@tailwind` directives on lines 1–3. CSS spec and PostCSS both require `@import` rules to appear before all other rules. When `@import` follows `@tailwind base/components/utilities`, PostCSS silently drops the import. As a result, the entire `themes.css` file (containing all `[data-theme="..."]` CSS variable blocks) is never injected into the browser in either dev mode or the compiled bundle.

## Root Cause

`src/styles.css` lines 1–6:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* TASK-068: Theme preset CSS variables (must come before :root overrides) */
@import "./styles/themes.css";    ← WRONG POSITION
```

The `@import` must be the very first statement, before any `@tailwind` directives.

## Evidence

- `getComputedStyle(document.documentElement).getPropertyValue('--theme-primary')` returns `""` (empty) for all themes tested.
- `getComputedStyle(document.documentElement).getPropertyValue('--theme-sidebar-bg')` returns `""` (empty).
- CSS stylesheet inspection in browser shows 0 rules containing `--theme-primary`, `--theme-sidebar-bg`, `emerald-health`, or `medical-blue` CSS variable definitions.
- `npx vite build` produces `dist/assets/index-*.css` with **0 occurrences** of `theme-primary`, `theme-sidebar-bg`, `emerald-health`, or `medical-blue` (grep count = 0).
- Only 2 inline `<style>` sheets in dev mode — neither contains any `[data-theme]` variable rules from themes.css.

## Impact

- **All 6 theme presets have zero visual effect** — sidebar, buttons, and other themed elements do not change color when a theme is selected.
- `data-theme` attribute is correctly set on `<html>` (selector logic works), but the CSS rules that match `[data-theme="..."]` are never present in the stylesheet.
- TC-003, TC-004, TC-005 (visual), TC-006 CSS verification all FAIL as a result.

## Fix Required

Move `@import "./styles/themes.css"` to the **very top** of `src/styles.css`, before all `@tailwind` directives:

```css
@import "./styles/themes.css";   ← MUST BE FIRST

@tailwind base;
@tailwind components;
@tailwind utilities;
```

## Review Discrepancy

The round-2 review report (handoff `review-to-test.md`) stated:
> "C1 FIXED: `@import "./styles/themes.css"` now sits at the very top of `src/styles.css`, above the `@tailwind` directives."

This claim is **incorrect**. The actual file has `@import` on line 6 after the `@tailwind` directives on lines 1–3. The fix was not applied.
