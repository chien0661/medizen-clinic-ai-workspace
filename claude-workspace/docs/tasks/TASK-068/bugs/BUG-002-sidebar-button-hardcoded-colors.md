# BUG-002: Sidebar and Button Use Hardcoded Colors — Theme Tokens Not Applied

**Task**: TASK-068 Theme Selection & Customization System
**Severity**: CRITICAL (sidebar and primary buttons never change with theme)
**Found by**: Test Agent (source code inspection + E2E)
**Date**: 2026-05-31
**Status**: OPEN

---

## Summary

`src/components/shell/Sidebar.tsx` and `src/components/ui/button.tsx` use hardcoded Tailwind color classes instead of the theme token classes (`bg-theme-sidebar`, `bg-theme-primary`, etc.). Even if BUG-001 is fixed and the CSS variables load correctly, the Sidebar and primary buttons will still not reflect theme changes.

## Evidence

**Sidebar.tsx** (line 637):
```tsx
"flex flex-col bg-slate-900 text-gray-100 sidebar-transition shrink-0"
```
Active nav item (line 617):
```tsx
"bg-indigo-500 text-white"
```
Hover states (lines 552–553, 619–620):
```tsx
"hover:bg-gray-700 hover:text-white"
```

**button.tsx** (line 12):
```tsx
default: "bg-indigo-500 text-white hover:bg-indigo-600 active:bg-indigo-700"
```

None of these use `bg-theme-sidebar`, `text-theme-sidebar-text`, `bg-theme-primary`, `text-theme-primary-text`, `hover:bg-theme-primary-hover`, `hover:bg-theme-sidebar-hover`, or `ring-theme-primary`.

The Tailwind config **does** define the tokens (lines 120–126 of `tailwind.config.js`):
```js
"theme-primary": "rgb(var(--theme-primary) / <alpha-value>)",
"theme-sidebar": "rgb(var(--theme-sidebar-bg) / <alpha-value>)",
// etc.
```

## Impact

- Sidebar background never changes from `bg-slate-900` (dark navy) regardless of theme selection.
- Primary buttons never change from `bg-indigo-500` regardless of theme selection.
- The main visual proof points of the theme system (sidebar color change, primary action button color change) are non-functional.

## Fix Required

**Sidebar.tsx**: Replace hardcoded classes with theme tokens on the wrapper and nav items:
```tsx
// Wrapper: bg-slate-900 → bg-theme-sidebar
// Active item: bg-indigo-500 → bg-theme-primary
// Hover: hover:bg-gray-700 → hover:bg-theme-sidebar-hover
// Text: text-gray-100 → text-theme-sidebar-text
```

**button.tsx** default variant:
```tsx
// bg-indigo-500 text-white hover:bg-indigo-600 active:bg-indigo-700
// →
// bg-theme-primary text-theme-primary-text hover:bg-theme-primary-hover active:bg-theme-primary-hover
```

## Review Discrepancy

The round-2 review report stated M1 was FIXED:
> "Sidebar.tsx now uses `bg-theme-sidebar`, `text-theme-sidebar-text`, `bg-theme-primary`, `hover:bg-theme-sidebar-hover`. button.tsx default variant → `bg-theme-primary text-theme-primary-text hover:bg-theme-primary-hover`..."

The actual files do **not** contain these classes. The fix was not applied.
