# TASK-068 — Test → Implementation Handoff

**Task**: Theme Selection & Customization System
**Branch**: `feature/TASK-068-theme-system` (clinic-cms-web)
**Test verdict**: FAIL
**Test Agent date**: 2026-05-31
**Returning to**: Implementation Agent

---

## Decision: FAIL → Return to IN_PROGRESS

Testing found 3 bugs — 2 CRITICAL and 1 MAJOR. The core acceptance criteria (visible theme switching) are completely non-functional. All three bugs correspond to fixes that were claimed as done in round-2 code review but were NOT actually applied to the source files.

**Full test report**: `docs/tasks/TASK-068/deliveries/test-reports/test-report.md`

---

## Bugs to Fix (in priority order)

### BUG-001 — CRITICAL: @import placed after @tailwind directives

**File**: `src/styles.css`

**Problem**:
```css
@tailwind base;          ← line 1
@tailwind components;    ← line 2
@tailwind utilities;     ← line 3

@import "./styles/themes.css";   ← line 6 — WRONG, must be FIRST
```

**Fix**: Move the `@import` to line 1, before all `@tailwind` directives:
```css
@import "./styles/themes.css";   ← FIRST

@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Verification**: After fix, run `npx vite build` and check `dist/assets/index-*.css` contains `--theme-primary`, `--theme-sidebar-bg`, `emerald-health`, `medical-blue` (grep count > 0 each). Also verify in dev mode: `getComputedStyle(document.documentElement).getPropertyValue('--theme-primary')` returns a non-empty RGB triplet when `data-theme="emerald-health"` is set.

---

### BUG-002 — CRITICAL: Sidebar and Button use hardcoded colors

**Files**: `src/components/shell/Sidebar.tsx`, `src/components/ui/button.tsx`

**Problem in Sidebar.tsx**:
```tsx
// Line 637 — wrapper still uses bg-slate-900
"flex flex-col bg-slate-900 text-gray-100 sidebar-transition shrink-0"

// Lines 617, 589 — active item still uses bg-indigo-500
"bg-indigo-500 text-white"

// Lines 552, 619–620 — hover still uses hover:bg-gray-700
"hover:bg-gray-700 hover:text-white"
```

**Required Sidebar.tsx changes**:
- Wrapper: `bg-slate-900` → `bg-theme-sidebar`, `text-gray-100` → `text-theme-sidebar-text`
- Active nav item: `bg-indigo-500` → `bg-theme-primary`, keep `text-white` or → `text-theme-primary-text`
- Hover: `hover:bg-gray-700` → `hover:bg-theme-sidebar-hover`
- Any `bg-indigo-*` color in sidebar context → equivalent theme token

**Problem in button.tsx**:
```tsx
// Line 12 — default variant hardcoded
default: "bg-indigo-500 text-white hover:bg-indigo-600 active:bg-indigo-700"
```

**Required button.tsx changes**:
```tsx
default: "bg-theme-primary text-theme-primary-text hover:bg-theme-primary-hover active:bg-theme-primary-hover focus-visible:ring-theme-primary"
```

Note: `bg-theme-primary`, `bg-theme-sidebar`, etc. are already defined in `tailwind.config.js` (lines 120–126). No config changes needed.

**Verification**: After fix, with Emerald Health selected, the sidebar background should visually show `rgb(6, 78, 59)` (emerald-900) and primary buttons should show `rgb(5, 150, 105)` (emerald-600).

---

### BUG-003 — MAJOR: Custom primary color not persisted to localStorage

**File**: `src/stores/themeStore.ts`

**Problem**: `setCustomPrimaryColor` never calls `localStorage.setItem("theme-custom-primary", ...)`.

**Fix — `setCustomPrimaryColor` action** (around line 156):
```ts
setCustomPrimaryColor: (color) => {
  set({ customPrimaryColor: color });
  // Persist to localStorage
  try {
    if (color) {
      localStorage.setItem("theme-custom-primary", color);
    } else {
      localStorage.removeItem("theme-custom-primary");
    }
  } catch { /* ignore quota errors */ }
  // Apply inline CSS override
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

**Fix — `resetToDefault` action** (around line 172): add `localStorage.removeItem("theme-custom-primary")`:
```ts
resetToDefault: () => {
  persistTheme(DEFAULT_THEME);
  applyDataTheme(DEFAULT_THEME);
  try { localStorage.removeItem("theme-custom-primary"); } catch { }
  if (typeof document !== "undefined") {
    document.documentElement.style.removeProperty("--theme-primary");
  }
  set({ activeTheme: DEFAULT_THEME, customPrimaryColor: null, previewTheme: null });
},
```

**Fix — store init** (around line 131): restore custom color on module load:
```ts
const initialTheme = readPersistedTheme();
applyDataTheme(initialTheme);

// Restore custom primary color if saved
const savedCustomColor = (() => {
  try { return localStorage.getItem("theme-custom-primary"); } catch { return null; }
})();
if (savedCustomColor && /^#[0-9a-fA-F]{6}$/.test(savedCustomColor)) {
  const rgb = hexToRgbTriplet(savedCustomColor);
  if (rgb && typeof document !== "undefined") {
    document.documentElement.style.setProperty("--theme-primary", rgb);
  }
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  activeTheme: initialTheme,
  customPrimaryColor: savedCustomColor,   // ← initialize from storage
  // ...
```

**Verification**: Set custom color → reload → `localStorage["theme-custom-primary"]` should persist and the color should restore without flash.

---

## What Was Verified as Working (do not break)

- ThemePicker component structure and UI: 6 presets, custom color input, reset button — all render correctly (TC-001, TC-002 PASS)
- `data-theme` attribute logic: correctly set/cleared on selection and hover (store/DOM logic is correct)
- `localStorage["theme-preference"]` persistence: correctly written and restored (TC-006 PASS)
- `resetToDefault()` clears `localStorage["theme-custom-primary"]` correctly (TC-007 PASS)
- Hover preview mechanism: correctly sets/restores `data-theme` on hover/mouseleave
- Unit tests: 914/914 PASS — do not break these

---

## Re-test Checklist

After implementing fixes, re-run full test cycle:

1. `npm test` — must still show 914/914
2. `npx vite build` → `grep "theme-primary" dist/assets/index-*.css` — must return matches
3. Browser CSS var check: with `data-theme="emerald-health"`, `getComputedStyle(document.documentElement).getPropertyValue('--theme-primary')` must return `"5 150 105"` (or equivalent non-empty RGB triplet)
4. Visual check: sidebar background turns green (emerald-900) with Emerald Health, indigo with Medical Blue
5. Primary button color changes with each theme
6. Custom color persists after reload
7. `resetToDefault` clears custom color from localStorage

---

## Notes for Implementation Agent

- The review claimed all three of these were fixed in round 2, but they are not present in the actual source files. Please apply all three fixes carefully.
- BUG-001 fix is a one-line change in `src/styles.css` — just move `@import` to line 1.
- BUG-002 may affect other components using `bg-indigo-*` in the sidebar — review thoroughly.
- After applying BUG-001, run `npx vite build` and grep the compiled CSS immediately to confirm the fix took effect before proceeding to other bugs.
