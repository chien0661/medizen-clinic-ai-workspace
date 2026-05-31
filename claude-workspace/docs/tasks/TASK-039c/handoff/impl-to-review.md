---
task: TASK-039c
from: implementation
to: review
date: 2026-05-01
status: READY_FOR_REVIEW
---

# TASK-039c Implementation Handoff — Impl → Review

## SVG Design Specifics

**File:** `clinic-cms-web-w7/src/assets/medizen-logo.svg`

Design concept — Vietnamese health software branding:
- **Shape:** 64x64 viewBox, rounded circle background
- **Background:** Indigo `#6366F1` circle (r=30, full fill)
- **Subtle ring:** Semi-transparent white inner ring (rgba 12%) for depth
- **Medical cross:** White cross composed of two rounded rectangles (rx=2) — vertical 8x30, horizontal 30x8, centered
- **Emerald accent:** `#10B981` circle (r=6) at bottom-right (cx=44, cy=44) symbolizing health/wellness
- **Checkmark inside dot:** White polyline checkmark (1.8px stroke, round caps) inside the emerald dot — implies "healthy/approved"
- Scales cleanly from 16x16 to 512x512 (pure vector)

**Favicon:** `clinic-cms-web-w7/public/favicon.svg` — simplified version of logo (same design, no inner ring for cleaner small rendering)

## React Component

**File:** `clinic-cms-web-w7/src/components/branding/MedizenLogo.tsx`

Props: `size?: number | string` (default 32), `className?: string`, `alt?: string`
Usage: `<MedizenLogo size={32} className="shrink-0" />`

## Favicon Strategy

| Asset | Status | Notes |
|---|---|---|
| `public/favicon.svg` | COMMITTED | SVG-based favicon — works in all modern browsers (Chrome 80+, Firefox 78+, Edge 80+) |
| `public/favicon-32x32.png` | OFFLINE NEEDED | Generate from `favicon.svg` offline (see command below) |
| `public/apple-touch-icon.png` | OFFLINE NEEDED | 180x180 PNG for iOS home screen |
| `public/favicon.ico` | OFFLINE NEEDED | Legacy multi-res ICO for IE/older systems |

**Offline generation commands (run once by developer):**
```bash
# Install sharp-cli or use ImageMagick
# Option A — using Inkscape (recommended)
inkscape public/favicon.svg --export-filename=public/favicon-32x32.png --export-width=32 --export-height=32
inkscape public/favicon.svg --export-filename=public/apple-touch-icon.png --export-width=180 --export-height=180

# Option B — using sharp-cli
npx sharp-cli -i public/favicon.svg -o public/favicon-32x32.png resize 32

# Generate ICO from PNGs (ImageMagick)
convert public/favicon-32x32.png -define icon:auto-resize=16,32,48 public/favicon.ico
```

`index.html` already references all three links (SVG primary, PNG 32x32, apple-touch-icon). The SVG link is sufficient for modern browser tabs; PNG/ICO needed only for legacy support and iOS.

## Tauri Icon Strategy

**Existing icons in `src-tauri/icons/`:** `32x32.png`, `128x128.png`, `128x128@2x.png`, `icon.icns`, `icon.ico` — these are the Tauri default placeholder icons.

**`tauri.conf.json` icon paths** — already correct (paths unchanged, defaults preserved).

**To regenerate icons with MediZen branding (run once offline):**
```bash
# Using Tauri CLI (preferred)
npm install -g @tauri-apps/cli
tauri icon ./src/assets/medizen-logo.svg
# This auto-generates all required sizes + formats in src-tauri/icons/

# Alternative: manual conversion via Inkscape + ImageMagick
inkscape src/assets/medizen-logo.svg --export-filename=src-tauri/icons/32x32.png --export-width=32 --export-height=32
inkscape src/assets/medizen-logo.svg --export-filename=src-tauri/icons/128x128.png --export-width=128 --export-height=128
inkscape src/assets/medizen-logo.svg --export-filename=src-tauri/icons/128x128@2x.png --export-width=256 --export-height=256
```

Note: `icon.icns` (macOS) and `icon.ico` (Windows) require platform-specific tooling. `tauri icon` CLI handles both automatically.

Also updated: `tauri.conf.json` productName and window title changed from `"Clinic CMS"` to `"MediZen"`.

## Shield → Logo Replacement

| File | Location | Change |
|---|---|---|
| `src/components/shell/Sidebar.tsx` | Logo area top (line ~401) | `<Shield className="h-6 w-6 text-indigo-400 shrink-0" />` → `<MedizenLogo size={24} className="shrink-0" />` |
| `src/pages/auth/LoginPage.tsx` | Brand mark top-left of panel (line ~234) | `<Shield className="h-6 w-6" />` → `<MedizenLogo size={24} />` |
| `src/pages/auth/LoginPage.tsx` | Mobile-only logo (line ~272) | `<Shield className="h-5 w-5" />` → `<MedizenLogo size={20} />` |

**Note:** Shield icon retained for:
- `src/components/shell/Sidebar.tsx` nav item `admin` (icon: Shield) — semantically correct (admin/security section icon)
- `src/pages/auth/LoginPage.tsx` feature pill "RBAC + audit" — semantically correct
- `src/pages/admin/RolesPage.tsx` — roles/permissions context (out of scope for this task)
- `src/pages/admin/UsersPage.tsx` — user roles badge (out of scope for this task)

## Test Results

```
Test Files: 51 passed (51)
Tests:      556 passed (556)
New tests:  src/tests/branding/MedizenLogo.test.tsx — 9 tests
```

Test coverage for MedizenLogo:
- Renders img element with correct alt text
- Default size 32
- Numeric size prop
- String size prop (CSS units)
- className forwarding
- Custom alt text
- 16x16 (favicon size)
- 512x512 (full icon size)
- draggable=false

## Verification Summary

| Check | Result |
|---|---|
| `tsc --noEmit` | PASS — 0 errors |
| ESLint | PASS — 0 warnings |
| `npm test -- --run` | PASS — 556/556 |
| `npm run build` | PASS — built in ~22s |

Chunk size warning (~1.1MB index bundle) is a pre-existing Rollup warning from TASK-039 baseline, not introduced by this task.

## Files Changed

- `clinic-cms-web-w7/src/assets/medizen-logo.svg` — NEW
- `clinic-cms-web-w7/public/favicon.svg` — NEW
- `clinic-cms-web-w7/src/components/branding/MedizenLogo.tsx` — NEW
- `clinic-cms-web-w7/src/tests/branding/MedizenLogo.test.tsx` — NEW
- `clinic-cms-web-w7/src/components/shell/Sidebar.tsx` — logo swap + import
- `clinic-cms-web-w7/src/pages/auth/LoginPage.tsx` — 2x logo swap + import
- `clinic-cms-web-w7/index.html` — favicon links + title update
- `clinic-cms-web-w7/src-tauri/tauri.conf.json` — productName + window title
