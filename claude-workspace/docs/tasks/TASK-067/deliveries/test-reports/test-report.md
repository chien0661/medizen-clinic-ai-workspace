---
task: TASK-067
title: FE UI routes cleanup — Security route, BHYT config route, Reports hub, Profile stubs, useSync browser UX
tested_by: Test Agent
date: 2026-05-31
branch: feature/TASK-067-fe-routes-usesync
commit: 73e1a6c
result: PASSED
---

# Test Report — TASK-067

## Summary

| Category | Count |
|---|---|
| Unit test files (new) | 3 |
| Unit tests (new) | 16 |
| Total unit tests (suite) | 930 |
| Unit tests passed | 930 |
| Unit tests failed | 0 |
| E2E scenarios | 8 |
| E2E passed | 8 |
| E2E failed | 0 |
| **Overall result** | **PASSED** |

---

## Unit Tests

### Pre-existing suite
- **914 tests passing** before any new tests were added (baseline from review handoff).

### New tests written for TASK-067

#### 1. `src/tests/hooks/useSync.test.ts` — useSync browser guard (5 tests)

| # | Test name | Result |
|---|---|---|
| T1 | Does NOT call syncAll when `window.__TAURI__` is undefined (browser mode) | PASS |
| T2 | Does NOT set any sync errors when `window.__TAURI__` is undefined | PASS |
| T3 | Does NOT start online-check interval when `window.__TAURI__` is undefined | PASS |
| T4 | Starts sync intervals when `window.__TAURI__` IS defined (Tauri mode) | PASS |
| T5 | Returns empty conflicts array in browser mode (no errors thrown) | PASS |

#### 2. `src/tests/reports/ReportsHubPage.test.tsx` — ReportsHubPage component (8 tests)

| # | Test name | Result |
|---|---|---|
| T1 | Renders the page heading "Báo cáo" | PASS |
| T2 | Renders the tab navigation landmark | PASS |
| T3 | Renders all 6 base tabs (revenue, inventory, doctor-performance, visit-volume, prescriptions, ar-aging) | PASS |
| T4 | Does NOT render BHYT tab when bhyt feature flag is OFF | PASS |
| T5 | Renders BHYT tab when bhyt feature flag is ON | PASS |
| T6 | Renders an `<Outlet />` — child route content area | PASS |
| T7 | Revenue tab is active (indigo border) when on /reports/revenue | PASS |
| T8 | All tab links point to the correct paths | PASS |

#### 3. `src/tests/router/settingsRedirect.test.tsx` — /settings redirect and /admin/security route (3 tests)

| # | Test name | Result |
|---|---|---|
| T1 | Navigating to /settings renders /admin/settings (not PlaceholderPage) | PASS |
| T2 | Navigating to /settings does NOT render a PlaceholderPage | PASS |
| T3 | Navigating to /admin/security renders the security page (not 404) | PASS |

### Full suite run
```
Test Files  91 passed (91)
      Tests 930 passed (930)
   Duration  17.68s
```

---

## E2E Tests (Playwright — app on :1420)

### Test environment
- App URL: `http://localhost:1420` (Vite dev server, browser/web mode)
- Auth: admin / Demo@1234
- Topbar sync indicator monitored throughout

### E2E scenarios

| # | Scenario | URL | Result | Notes |
|---|---|---|---|---|
| E1 | `/admin/security` renders Security panels | `#/admin/security` | PASS | Heading "Bảo mật & Mã hoá", MFA panel (Xác thực hai yếu tố), login history visible. Topbar: "Online" (no ⚠️). |
| E2 | `/admin/bhyt` renders BHYT config page | `#/admin/bhyt` | PASS | BhytConfigPage rendered with description text. Breadcrumb shows Admin > Bhyt. |
| E3 | `/reports` redirects to `/reports/revenue` | `#/reports` → `#/reports/revenue` | PASS | URL changed to `/reports/revenue`. Hub heading "Báo cáo" visible. All 6 base tabs rendered with correct hrefs. Revenue sub-page renders inside Outlet. |
| E4 | Sidebar "Báo cáo" active on any `/reports/*` sub-route | `#/reports/inventory` | PASS | Sidebar button labelled `"Báo cáo active role"` confirmed active on `/reports/inventory`. |
| E5 | Profile "info" tab shows "Tính năng đang phát triển" | `#/profile` → info tab | PASS | InfoTab renders read-only fields + badge "Chỉnh sửa thông tin — Tính năng đang phát triển". Not a blank stub. |
| E6 | Profile "notifications" tab shows "Tính năng đang phát triển" | `#/profile` → notifications tab | PASS | NotificationsTab renders channel rows (Email/SMS/In-app) + badge "Tính năng đang phát triển". |
| E7 | `/settings` redirects to `/admin/settings` | `#/settings` → `#/admin/settings` | PASS | URL changed to `/admin/settings`. Page heading "Cài đặt phòng khám" rendered. No PlaceholderPage. |
| E8 | No useSync errors in browser mode (35s soak) | `#/dashboard` (35s wait) | PASS | `browser_console_messages(all=false, level=error)` returned 0 errors after 35 seconds. Topbar shows "Online" (no ⚠️). Historical errors in session log are from pre-fix browser session. |

---

## Business Rules Validation

| Acceptance Criterion | Result |
|---|---|
| `/admin/security` route exists and renders Security settings (MFA/LoginHistory panels) | PASS |
| `/admin/bhyt` route exists and renders BhytConfigPage | PASS |
| `/reports` renders hub with redirect + sidebar highlight on sub-routes | PASS |
| Profile tab "info" has explicit coming-soon badge (not blank stub) | PASS |
| Profile tab "notifications" has explicit coming-soon badge (not blank stub) | PASS |
| `/settings` does NOT render PlaceholderPage — redirects to `/admin/settings` | PASS |
| Browser mode: Topbar NO ⚠️ sync error; console NO `[useSync] Sync error` (35s soak) | PASS |
| `npm test --silent` passes (all 930 tests) | PASS |

---

## Screenshots

All screenshots saved to `docs/tasks/TASK-067/deliveries/test-reports/screenshots/`:

| File | Description |
|---|---|
| `e2e-admin-security.png` | `/admin/security` — full page, Security panels visible |
| `e2e-admin-bhyt.png` | `/admin/bhyt` — BHYT config page rendered |
| `e2e-reports-hub.png` | `/reports/revenue` — hub with tab nav + revenue sub-page |
| `e2e-profile-notifications.png` | Profile notifications tab — "Tính năng đang phát triển" badge |
| `e2e-settings-redirect.png` | `/settings` → `/admin/settings` redirect confirmed |
| `e2e-usesync-guard-clean.png` | Dashboard after 35s soak — Topbar "Online", no ⚠️ |

---

## Notes

- The `browser_console_messages(all=true)` showed historical `[useSync] Sync error` entries from a prior browser session (before TASK-067 code was loaded in the dev server). With `all=false` (errors since last navigation), **0 errors** were found on each page — confirming the guard is working.
- 6 pre-existing type-check errors in untouched files remain (noted in review handoff); outside TASK-067 scope.
- BHYT tab in ReportsHubPage is conditional on `bhyt` feature flag — confirmed absent when flag OFF, present when ON.
