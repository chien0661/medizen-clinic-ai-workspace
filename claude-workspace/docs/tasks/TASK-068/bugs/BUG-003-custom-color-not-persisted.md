# BUG-003: Custom Primary Color Not Persisted to localStorage

**Task**: TASK-068 Theme Selection & Customization System
**Severity**: MAJOR (customization lost on page reload)
**Found by**: Test Agent (TC-008 + store code review)
**Date**: 2026-05-31
**Status**: OPEN

---

## Summary

`setCustomPrimaryColor()` in `src/stores/themeStore.ts` applies the custom color as an inline CSS variable on `<html>` and updates Zustand state, but **never writes to localStorage**. The FOUC script in `index.html` checks `localStorage["theme-custom-primary"]` to restore the color on page load, but since it is never written, the custom color is always lost after reload.

## Evidence

**TC-008 test**: Setting the color input to `#ff0000` via `onChange`:
```js
{ lsCustom: null, inlineStyle: "255 0 0" }
```
- `document.documentElement.style.getPropertyValue('--theme-primary')` = `"255 0 0"` ✓ (applied inline)
- `localStorage.getItem('theme-custom-primary')` = `null` ✗ (not persisted)

**Store code** (`src/stores/themeStore.ts` lines 156–170):
```ts
setCustomPrimaryColor: (color) => {
  set({ customPrimaryColor: color });
  if (typeof document !== "undefined") {
    if (color) {
      const rgb = hexToRgbTriplet(color);
      if (rgb) {
        document.documentElement.style.setProperty("--theme-primary", rgb);
      }
    } else {
      document.documentElement.style.removeProperty("--theme-primary");
    }
  }
},
```
No `localStorage.setItem("theme-custom-primary", color)` call is present.

The `resetToDefault` action also does not call `localStorage.removeItem("theme-custom-primary")`.

## Impact

- User sets a custom primary color → it works for the current session.
- User reloads the page → custom color is gone, falls back to theme default.
- The FOUC script in `index.html` lines 26–35 (which reads `localStorage["theme-custom-primary"]`) never fires meaningfully because the key is never written.

## Fix Required

In `setCustomPrimaryColor`, add localStorage persistence:
```ts
setCustomPrimaryColor: (color) => {
  set({ customPrimaryColor: color });
  try {
    if (color) {
      localStorage.setItem("theme-custom-primary", color);
    } else {
      localStorage.removeItem("theme-custom-primary");
    }
  } catch { /* ignore quota errors */ }
  // ... rest of inline style application
},
```

Also fix `resetToDefault` to remove the localStorage key:
```ts
resetToDefault: () => {
  try { localStorage.removeItem("theme-custom-primary"); } catch { }
  // ... rest of reset logic
},
```

Also update `themeStore` init to restore `customPrimaryColor` from localStorage on module load (currently only restores the preset, not the custom color).

## Review Discrepancy

The round-2 review report stated N2 was FIXED:
> "`setCustomPrimaryColor` persists to `localStorage["theme-custom-primary"]`; `resetToDefault` removes it; store init restores it."

The actual store code does **not** contain any `localStorage.setItem("theme-custom-primary", ...)` calls. The fix was not applied.
