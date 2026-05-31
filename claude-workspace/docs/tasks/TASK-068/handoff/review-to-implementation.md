# TASK-068 — Review → Implementation Handoff

**Decision**: CHANGES_REQUESTED
**Status moved**: IN_REVIEW → IN_PROGRESS
**Date**: 2026-05-31
**Full report**: `docs/tasks/TASK-068/handoff/review-report.md`

---

## Summary for the Implementer

Good news: the architecture (store / hook / component split), TypeScript types, lint, and all 32 unit tests are solid. The bad news is the feature does not actually work in the running app — the theme CSS is never loaded, so picking a theme changes nothing on screen. This was verified in both the production build and the live dev server on `localhost:1420`.

Please fix the items below and re-submit (set status back to IN_REVIEW when ready).

---

## CRITICAL — must fix

### C1. `@import` placement drops the entire theme stylesheet

`src/styles.css` puts `@import "./styles/themes.css";` **after** the `@tailwind` directives. CSS requires `@import` to come first, so PostCSS silently drops it and none of `themes.css` reaches the output. No `[data-theme]` rules exist in the running app; `--theme-primary` / `--theme-sidebar-bg` etc. are all undefined.

**Fix (already verified working):**
```css
/* src/styles.css — move import to the very top */
@import "./styles/themes.css";
@tailwind base;
@tailwind components;
@tailwind utilities;
```
After fixing, run `vite build` and confirm `dist/assets/*.css` contains `emerald-health` and `--theme-sidebar-bg`.

---

## MAJOR — should fix before approval

- **M1.** No component consumes the `theme-*` tokens (grep found 0 usages outside ThemePicker's swatches). Even with C1 fixed, switching themes won't change anything visible. Migrate at least the primary action color and the sidebar to `theme-*` tokens / `--theme-*` vars so the feature is observably functional per the AC. If you intend a phased rollout, get manager sign-off and update the task AC — don't leave it implicit.
- **M2.** The 32 tests check JS state only, never that a CSS variable resolves — which is why they stayed green while the feature was broken. Add at least one assertion (Playwright/e2e) that `--theme-primary` resolves after a switch.
- **M3.** This commit also bundles unrelated rebrand changes (Sora font swap, full `brand` teal palette, borderRadius/spacing/boxShadow edits, `--color-*` changes). Not mentioned in the handoff and out of scope for a theme *picker*. Confirm with the manager whether they belong here; split out if not.

---

## MINOR — nice to fix

- **N2.** `customPrimaryColor` is not persisted/restored — lost on reload. Persist to localStorage + restore in the FOUC script, or descope explicitly.
- **N1.** `midnight-dark` is a palette only; it doesn't toggle the `.dark` background scheme, so the name may mislead. Consider a tooltip/rename. Re-verify dark+theme interop after C1.
- **N4.** Hover preview has no keyboard-focus equivalent — keyboard users get no live preview.

---

## Re-submission checklist

- [ ] C1 fixed; `dist/assets/*.css` contains the theme blocks after build
- [ ] M1: primary + sidebar visibly change when switching themes (or descope approved by manager)
- [ ] M2: at least one CSS-resolution assertion added
- [ ] M3: rebrand changes confirmed in-scope or split out
- [ ] N2: custom color persisted or descoped
- [ ] Re-run full suite (the 5 pre-existing billing/notifications/pharmacy failures are NOT yours — leave them)
- [ ] Set status back to IN_REVIEW and update the handoff
