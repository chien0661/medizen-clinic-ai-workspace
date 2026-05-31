# Handoff: TASK-067 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW
**Branch**: `feature/TASK-067-fe-routes-usesync` (in `clinic-cms-web`)
**Commit**: `73e1a6c`

---

## Summary

Implemented all 6 FE-only cleanup items from TASK-053 audit: wired missing `/admin/security` and `/admin/bhyt` routes, created a `/reports` hub page with tab navigation, replaced blank profile stubs with explicit placeholders, redirected `/settings` to `/admin/settings`, and added a Tauri browser guard to `useSync.ts` that silences errors in web/browser mode.

---

## Files Changed

### New files
- `clinic-cms-web/src/pages/admin/SecuritySettingsPage.tsx` — wraps `SecurityTab` for the `/admin/security` route (MFA + login fingerprints)
- `clinic-cms-web/src/pages/reports/ReportsHubPage.tsx` — hub page at `/reports` with tab nav linking to all 7 sub-routes via NavLink + Outlet; redirects index → `/reports/revenue`

### Modified files
- `clinic-cms-web/src/router/index.tsx`
  - Added lazy imports: `SecuritySettingsPage`, `BhytConfigPage`, `ReportsHubPage`
  - Removed unused `PlaceholderPage` import
  - Added `/admin/security` → `SecuritySettingsPage`
  - Added `/admin/bhyt` → `BhytConfigPage`
  - Converted `/reports` flat routes → nested under `ReportsHubPage` parent (Outlet pattern)
  - Changed `/settings` from `PlaceholderPage` → `<Navigate to="/admin/settings" replace />`
- `clinic-cms-web/src/components/shell/Sidebar.tsx`
  - Added `admin-security` and `admin-bhyt` sub-items under admin group
  - Updated `settings` top-level path `/settings` → `/admin/settings` (avoids redirect hop)
  - Removed orphaned `bhytEnabled` variable and `useFeatureFlag` import
- `clinic-cms-web/src/pages/profile/ProfilePage.tsx`
  - Replaced `StubTab` (generic blank) with `InfoTab` (read-only user fields + coming-soon banner), `NotificationsTab` (channel outline + coming-soon banner)
  - `StubTab` now accepts `title` + optional `description` props instead of i18n key
  - Removed dependency on missing `common:comingSoon` i18n key
- `clinic-cms-web/src/hooks/useSync.ts`
  - Added `isTauriApp()` helper checking `window.__TAURI__`
  - `syncEnabled = enabled && tauriActive` — all three `useEffect` hooks now guard on `syncEnabled`
  - In browser mode: no intervals started, no sync errors thrown, no `⚠️` in Topbar
- `clinic-cms-web/src/locales/vi/admin.json` — added `nav.security`, `nav.bhytConfig`, `security.title`, `security.description`
- `clinic-cms-web/src/locales/en/admin.json` — same keys in English

---

## Test Results

- **Type-check**: No new errors introduced. Pre-existing errors (6) in `field.tsx`, `admin/api.ts`, `LoginPage.tsx`, `PatientDetailPage.tsx`, test file — all pre-TASK-067.
- **Lint**: No errors in modified files. Pre-existing lint errors (15) in `VssIntegrationConfigPage.tsx`, `VssSyncLogPage.tsx`, test file.
- **Unit tests**: 914/914 passed (88 test files) — no regressions.

---

## Areas for Review Focus

1. **`useSync.ts` guard** — verify `isTauriApp()` approach is correct vs. `@tauri-apps/api/core:isTauri()`. Both check `window.__TAURI__`; the chosen approach avoids an async dynamic import at hook init time.

2. **`/reports` nested route structure** — `ReportsHubPage` uses `<Outlet />`. Confirm the sidebar `NavLink` active state works: sub-items use full paths (`/reports/revenue`) so `isActive` fires correctly. The parent group button is not a NavLink so no conflict.

3. **`/admin/bhyt` vs. BHYT tab in `/admin/settings`** — route `/admin/bhyt` is a standalone page (no permission wrapper beyond RequireAuth). BhytConfigPage self-gates via `bhyt:config` inside its own form. The BHYT tab in SettingsPage still exists (gated by feature flag) — both paths are accessible; this is intentional.

4. **`SecuritySettingsPage`** — uses no extra permission gate (accessible to any authenticated user) since it shows personal MFA/login history. Task says "admin only" but the security panels are personal. If reviewers want `settings.clinic` or `admin.access` gate, easy to add.

5. **Profile stubs** — `InfoTab` shows read-only data only (no PUT call). Task noted `PUT /api/v1/users/{id}` but also accepted "coming soon" placeholder. Chosen: read-only display + coming-soon banner, which avoids coupling to an untested endpoint.

---

## Acceptance Criteria Verification

- [x] `/admin/security` route exists and renders SecurityTab (MFA + login history)
- [x] `/admin/bhyt` route exists and renders BhytConfigPage
- [x] `/reports` renders hub with tab nav; sidebar NavLinks active on sub-routes
- [x] Profile tab "info" has explicit content (not blank stub)
- [x] Profile tab "notifications" has explicit content (not blank stub)
- [x] `/settings` does not render PlaceholderPage — redirects to `/admin/settings`
- [x] `useSync.ts` guard: browser mode skips all sync init; no console errors; no ⚠️
- [x] `npm run type-check` — no new errors
- [x] `npm run lint` — no new errors
- [x] `npm test` — 914/914 passed
