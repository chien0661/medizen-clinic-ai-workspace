# Handoff: TASK-067 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED
**Branch**: `feature/TASK-067-fe-routes-usesync` (clinic-cms-web), commit `73e1a6c`

## Summary

FE-only cleanup of 6 audit items: wired `/admin/security` + `/admin/bhyt` routes, built a `/reports` hub page (tab nav + Outlet over 7 nested sub-routes), replaced blank profile stubs with explicit read-only + coming-soon content, redirected `/settings` → `/admin/settings`, and added a Tauri browser guard to `useSync.ts`. Reviewed only commit `73e1a6c` (branch also carries unrelated TASK-064/066/068 commits). Passed: no new type errors, clean lint on touched files, 914/914 tests, and full Playwright visual verification on :1420.

## Key Findings (MINOR, for awareness)

- `SecuritySettingsPage.tsx` header docstring contradicts itself (says "admins only" but behavior is "any authenticated user"). Behavior is correct per codebase RBAC pattern; only the doc line is stale.
- `/admin/bhyt` route is reachable by any authenticated user via direct URL — no route-level or in-component permission gate (sidebar link IS gated by `bhyt:config`; BE enforces on PATCH). This matches the existing codebase convention (all routes are RequireAuth-only) and is not a TASK-067 regression.
- ReportsHubPage `/reports` index uses a `useEffect` redirect to `/reports/revenue` (works; brief hub flash before redirect).
- 6 pre-existing type-check errors remain in untouched files (field.tsx, modules/admin/api.ts, LoginPage.tsx, PatientDetailPage.tsx, a test file) — outside TASK-067 scope.

## Focus Areas for Testing

1. **useSync browser guard (highest priority)** — Run FE in browser, log in, stay logged in past 30s+. Confirm: NO `[useSync] Sync error` in console, NO ⚠️ indicator in Topbar (only "Online"). Code Review verified this over a 35s window with 0 errors. Re-confirm across multiple authenticated pages and a fresh page reload.
2. **`/reports` hub + 7 sub-routes** — Visit `/reports` (expect redirect to `/reports/revenue`). Click each tab (revenue, inventory, doctor-performance, visit-volume, prescriptions, ar-aging); confirm active highlight + correct sub-page render. With `bhyt` feature flag ON, confirm the BHYT tab appears and routes to `/reports/bhyt`.
3. **`/admin/security`** — Confirm SecurityTab renders (2FA panel + login history). Test as a non-admin authenticated user — should still be accessible (intentional).
4. **`/admin/bhyt`** — Confirm BhytConfigPage renders + toggle/save works. Test the save mutation actually hits BE and BE enforces `bhyt:config` (negative test with an unprivileged user if feasible).
5. **Profile tabs** — info / notifications / activity show explicit coming-soon content (not blank). security tab shows SecurityTab.
6. **`/settings` redirect** — Confirm `/settings` redirects to `/admin/settings` (no PlaceholderPage). Confirm sidebar "Cài đặt" points directly to `/admin/settings`.
7. **i18n** — Switch vi/en; confirm no raw i18n keys or blank labels on the new security/bhyt nav items and pages.

## Screenshots from review

`docs/tasks/TASK-067/deliveries/test-reports/screenshots/`: `admin-security.png`, `reports-hub.png`, `profile-info.png`.
