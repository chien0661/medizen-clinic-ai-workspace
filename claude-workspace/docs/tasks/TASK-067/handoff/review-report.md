# Code Review Report — TASK-067

**From**: Code Review Agent
**Task**: FE UI routes cleanup — Security route, BHYT config route, Reports hub, Profile stubs, useSync browser UX
**Branch**: `feature/TASK-067-fe-routes-usesync` (clinic-cms-web)
**Commit reviewed**: `73e1a6c` (only the TASK-067 commit; branch also carries TASK-064/066/068 commits which were excluded from scope)
**Decision**: **APPROVED** → IN_TESTING
**Date**: 2026-05-31

---

## Scope Note

The branch's full `main...branch` diff (25 files) mixes in TASK-064/066/068 work (theme system, pharmacy fetch fixes, AR aging). The review was correctly scoped to the **8 files in commit `73e1a6c`**:

- `src/hooks/useSync.ts`
- `src/pages/admin/SecuritySettingsPage.tsx` (new)
- `src/pages/reports/ReportsHubPage.tsx` (new)
- `src/router/index.tsx`
- `src/components/shell/Sidebar.tsx`
- `src/pages/profile/ProfilePage.tsx`
- `src/locales/vi/admin.json`, `src/locales/en/admin.json`

---

## Quality Gates

| Gate | Result |
|------|--------|
| Type-check (`npm run type-check`) | 6 errors — **all pre-existing**, in files NOT touched by TASK-067 (`field.tsx`, `modules/admin/api.ts`, `LoginPage.tsx`, `PatientDetailPage.tsx`, `i18n-default-language.test.ts`). Verified present at merge-base `e3a5679`. No new errors. |
| Lint (eslint on the 6 TASK-067 source files) | **0 errors / 0 warnings** |
| Unit tests (`npm test`) | **914/914 passed** (88 files), no regressions |
| SonarQube | DISABLED — skipped per agent guide |
| Visual inspection (Playwright, app on :1420) | **PASS** — see below |

---

## Focus-Area Findings

### 1. `useSync.ts` browser guard — CORRECT
- `isTauriApp()` checks `typeof window !== "undefined" && "__TAURI__" in window`. This is equivalent to `@tauri-apps/api/core:isTauri()` (which also checks `window.__TAURI_INTERNALS__`/`__TAURI__`) but avoids an async dynamic import at hook init — a sound choice.
- The guard is applied to **all 3** `useEffect` hooks: online polling, periodic sync (30s), pending-count (10s) — all switched from `enabled` → `syncEnabled = enabled && tauriActive`. Verified in diff.
- **Runtime verified**: logged in as admin, sat on the dashboard for 35s (past the 30s sync interval). Console errors since dashboard load = **0**. Topbar status shows only "Online" — **no ⚠️ sync-error indicator**.
- Stale `[useSync] Sync error: Failed to load Tauri SQL plugin` lines exist in the session-history console buffer, but their stack traces point to old line numbers (`useSync.ts:22`/`:37`) that do not match the current code — confirming they are from a pre-TASK-067 session, not the current build.

### 2. `/admin/security` permission — ACCEPTABLE
- Implementation uses no permission gate beyond `RequireAuth`; sidebar nav item is `permission: null`. Rationale: SecurityTab shows personal MFA/backup-codes/login-fingerprints, not admin-wide data.
- This matches the **established codebase RBAC pattern**: router applies only `RequireAuth`; no route in `router/index.tsx` uses `RequirePermission`. Permission scoping is done via sidebar visibility + BE enforcement. So "any authenticated user" is consistent and correct.
- **MINOR (doc only)**: `SecuritySettingsPage.tsx` has a contradictory header docstring — line ~8 says *"Gated by: admin.access permission (admins only)"* while the function comment and actual behavior say "any authenticated user". The code behavior is fine; the stale docstring line should be removed for clarity. Non-blocking.

### 3. `/reports` nested route + Outlet — CORRECT
- `ReportsHubPage` renders heading + NavLink tab bar + `<Outlet />`. All 7 sub-routes (revenue, inventory, doctor-performance, visit-volume, prescriptions, ar-aging, bhyt) are nested children in the router. BHYT tab is conditionally shown via `useFeatureFlag("bhyt")`.
- Index redirect: visiting `/reports` triggers a `useEffect` redirect to `/reports/revenue`. **Runtime verified**: `#/reports` → auto-redirected to `#/reports/revenue`, hub chrome + revenue content rendered, no blank page.
- NavLink active state uses full paths (`/reports/revenue` etc.) so `isActive` fires per sub-route. Clicking the "Hiệu suất bác sĩ" tab navigated to `#/reports/doctor-performance` with hub chrome preserved. All i18n labels resolve (verified `reports:nav.*`, `reports:arAging.nav`, `reports:title` exist in vi+en).

### 4. Profile "info" tab — ACCEPTABLE (coming-soon allowed)
- `InfoTab` shows read-only Họ và tên / Email / Vai trò + an explicit "Chỉnh sửa thông tin — Tính năng đang phát triển" banner. **Runtime verified** with real user data (Demo Admin / admin@demo.clinic / admin).
- No PUT call — task explicitly allows *"rõ ràng 'coming soon' thay vì blank stub"*. Criterion met. `NotificationsTab` and `activity` `StubTab` similarly show explicit coming-soon content instead of blank.
- The `common:comingSoon` i18n key (which was missing) is no longer referenced anywhere — verified via grep. `StubTab` now takes literal `title`/`description` props.

### 5. Sidebar changes — NO BREAKAGE
- Added `admin-security` (`/admin/security`, `permission: null`) and `admin-bhyt` (`/admin/bhyt`, `permission: "bhyt:config"`) under the admin group.
- Top-level "Cài đặt" path updated `/settings` → `/admin/settings` (avoids a redirect hop). **Runtime verified**: sidebar "Cài đặt" link points to `#/admin/settings`.
- Orphaned `bhytEnabled` var + `useFeatureFlag` import removed from Sidebar (the BHYT nav item now uses `permission` gating instead of feature flag — acceptable). Note: `useFeatureFlag` is still used by 6 other pages and remains imported there.
- No existing nav links broken; dashboard/reports/notifications/billing links all intact in the live snapshot.

### 6. i18n keys — COMPLETE (vi + en)
- New keys added to **both** locale files: `admin:nav.security`, `admin:nav.bhytConfig`, `admin:security.title`, `admin:security.description`. Verified in diff for both `vi/admin.json` and `en/admin.json`.
- `SecuritySettingsPage` also passes `defaultValue` fallbacks, so no blank labels even if a key were missing. No missing-key warnings observed in console.

---

## Additional Observations (Non-blocking)

- **MINOR — `/admin/bhyt` route is reachable by any authenticated user via direct URL.** The route has no route-level gate, and `BhytConfigPage` does not self-gate in-component (the "Permission: bhyt:config" line is only a docstring; there is no `RequirePermission`/`useHasPermission` check). The sidebar link IS gated by `bhyt:config`, and the BE PATCH endpoint is the real authority. This matches the existing codebase convention (route-level = `RequireAuth` only) and is **not a TASK-067 regression** — flagging for awareness only. **Runtime verified** the page renders correctly.
- **MINOR — ReportsHubPage index redirect** uses a `useEffect`+`navigate` instead of a React-Router `index` route with `<Navigate>`. The effect approach works (verified) but causes a brief render of the hub before redirect. An `<Route index element={<Navigate to="revenue" replace />} />` would be marginally cleaner. Non-blocking.

---

## Visual Evidence

Screenshots saved to `docs/tasks/TASK-067/deliveries/test-reports/screenshots/`:
- `admin-security.png` — SecuritySettingsPage (2FA + login history)
- `reports-hub.png` — ReportsHubPage tab bar + revenue Outlet
- `profile-info.png` — Profile InfoTab read-only + coming-soon banner

---

## Conclusion

All 7 acceptance criteria are met and runtime-verified. No critical or major issues. Quality gates pass (no new type errors, clean lint on touched files, 914/914 tests). Two MINOR doc/style notes do not block. **APPROVED.**
