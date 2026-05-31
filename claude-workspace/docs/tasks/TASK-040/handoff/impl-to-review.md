# TASK-040 — Implementation → Review Handoff

**Date:** 2026-05-01
**Branch:** `feature/task-040-phase-d-screens` (worktree: `clinic-cms-web-w2c`)
**Delivered by:** Code Implementation Agent
**Finalized by:** Rescue/Finalize Agent

---

## Screen Coverage (7 delivered / 1 deferred)

| ID  | Screen                       | Status    | Notes                                                          |
|-----|------------------------------|-----------|----------------------------------------------------------------|
| S.1 | ForgotPasswordPage           | DONE      | `/forgot-password` route, centered card 400px, success state  |
| S.2 | PatientDetailPage 8-tab      | DONE      | 3-col layout, 8 tabs incl. BHYT gated (TASK-034 dep.)         |
| S.3 | QueueBoardPage 5-col Kanban  | DONE      | Extended from 3 → 5 columns (Đăng ký + Hoàn tất added)        |
| S.4 | ProfilePage 5-tab stub       | PARTIAL   | 5 tabs rendered; "Phòng khám của tôi" tab DEFERRED (TASK-033) |
| S.5 | ARAgingReportPage            | DONE      | `/reports/ar-aging`, 0-30/31-60/61-90/>90 buckets + export    |
| S.6 | NotificationsPage enhanced   | DONE      | Bulk mark-read (all + selected), pagination, date range filter |
| S.7 | StocktakePage 3-step wizard  | DONE      | `/pharmacy/stocktake`, Chuẩn bị → Đếm → Đối chiếu wizard     |
| S.8 | ExpiryProcessingPage         | DONE      | `/pharmacy/expiry`, 30/60/90 day filter + disposal flow        |

**Deferred:** ProfilePage "Phòng khám của tôi" tab — blocked on TASK-033 multi-clinic integration. Tab renders a "Coming soon" stub with a clear TASK-033 TODO comment.

---

## Files Changed

### Modified files (tracked via `git diff --stat HEAD`)

| File                                              | Change           |
|---------------------------------------------------|------------------|
| `src/components/shell/Sidebar.tsx`                | +27 lines — added Pharmacy: Stocktake + Expiry sub-items |
| `src/lib/i18n.ts`                                 | +10 — registered `profile` namespace                     |
| `src/locales/en/auth.json`                        | +17 — `forgotPassword.*` keys                            |
| `src/locales/vi/auth.json`                        | +17 — same                                               |
| `src/locales/en/pharmacy.json`                    | +78 — `stocktake.*`, `expiry.*` keys                     |
| `src/locales/vi/pharmacy.json`                    | +78 — same                                               |
| `src/locales/en/reception.json`                   | +29 — `queue.kanban.*` keys                              |
| `src/locales/vi/reception.json`                   | +31 — same                                               |
| `src/locales/en/reports.json`                     | +26 — `reports.arAging.*` keys                           |
| `src/locales/vi/reports.json`                     | +26 — same                                               |
| `src/locales/en/notifications.json`               | +9 — `notifications.bulk.*` keys                         |
| `src/locales/vi/notifications.json`               | +9 — same                                               |
| `src/pages/auth/LoginPage.tsx`                    | +1 — link to `/forgot-password`                          |
| `src/pages/notifications/NotificationsPage.tsx`   | +229 net — bulk actions, pagination, date filter          |
| `src/pages/patients/PatientDetailPage.tsx`        | +313 net — 3-col layout, 8 tabs, AI sidebar               |
| `src/pages/queue/QueueBoardPage.tsx`              | +79 — 5-col Kanban                                       |
| `src/router/index.tsx`                            | +54 — 5 new routes                                       |
| `src/tests/reception/QueueBoardPage.test.tsx`     | +13 — 5-col test coverage                                |

**Total tracked diff:** 18 files, 1109 insertions, 205 deletions

### New (untracked) files

| File                                               | Description                              |
|----------------------------------------------------|------------------------------------------|
| `src/pages/auth/ForgotPasswordPage.tsx`            | S.1 — new screen                         |
| `src/pages/pharmacy/StocktakePage.tsx`             | S.7 — new screen                         |
| `src/pages/pharmacy/ExpiryProcessingPage.tsx`      | S.8 — new screen                         |
| `src/pages/profile/ProfilePage.tsx`                | S.4 — new screen (5-tab stub)            |
| `src/pages/reports/ARAgingReportPage.tsx`          | S.5 — new screen                         |
| `src/locales/vi/profile.json`                      | 26 lines, profile.* namespace            |
| `src/locales/en/profile.json`                      | 26 lines, profile.* namespace            |
| `src/tests/auth/ForgotPasswordPage.test.tsx`       | T.1+T.2 — smoke + golden path tests      |
| `src/tests/pharmacy/StocktakePage.test.tsx`        | T.3 — wizard step navigation tests       |
| `src/tests/pharmacy/ExpiryProcessingPage.test.tsx` | T.1 — smoke + 30/60/90 filter tests      |
| `src/tests/reports/ARAgingReportPage.test.tsx`     | T.4 — fetch + render with mock data      |

---

## New Routes Added

| Path                    | Component              | Guard      |
|-------------------------|------------------------|------------|
| `/forgot-password`      | ForgotPasswordPage     | public     |
| `/profile`              | ProfilePage            | authGuard  |
| `/pharmacy/stocktake`   | StocktakePage          | authGuard  |
| `/pharmacy/expiry`      | ExpiryProcessingPage   | authGuard  |
| `/reports/ar-aging`     | ARAgingReportPage      | authGuard  |

---

## i18n Keys Added

| Namespace         | New keys (vi = en) | Key prefixes                                      |
|-------------------|--------------------|---------------------------------------------------|
| `auth`            | ~16 keys           | `forgotPassword.*` (title, fields, errors, states)|
| `pharmacy`        | ~60 keys           | `stocktake.*`, `expiry.*`                         |
| `reception`       | ~20 keys           | `queue.kanban.*`, `queue.column.*`                |
| `reports`         | ~20 keys           | `reports.arAging.*` (buckets, table, export)      |
| `notifications`   | ~8 keys            | `notifications.bulk.*` (markAll, markSelected, dateFilter) |
| `profile` (new)   | 26 lines/file      | `profile.tabs.*`, `profile.fields.*`, `profile.stubs.*` |

---

## Test Gate Results

| Check    | Result            |
|----------|-------------------|
| `tsc --noEmit` | **0 errors** (fixed: `global.fetch` → `vi.stubGlobal` in ForgotPasswordPage.test.tsx) |
| `npm run lint` | **0 warnings, 0 errors** |
| `npm test -- --run` | **566/566 passed** (54 test files) — up from 547 baseline (+19 tests) |
| `npm run build` | **PASS** in 12s (chunk size warning is pre-existing, not a blocker) |

---

## Fix Applied During Finalization

`src/tests/auth/ForgotPasswordPage.test.tsx` lines 56 and 90:
- `global.fetch = vi.fn()...` → `vi.stubGlobal("fetch", vi.fn()...)`
- Reason: `global` is not in scope under the project's strict TS config (no `@types/node`). `vi.stubGlobal` is the Vitest-idiomatic equivalent and is fully type-safe.

---

## Deferred Decisions / Open Blockers

1. **ProfilePage "Phòng khám của tôi" tab** — deferred, awaiting TASK-033 multi-clinic API. Tab is present with a yellow "Coming soon" banner; no `PlaceholderPage` used.
2. **PatientDetailPage "Lịch sử BHYT" tab** — gated via `DevPlaceholder` component. Awaiting TASK-034 feature flag integration.
3. **AR Aging + Stocktake + Expiry BE endpoints** — UI uses mock data. Awaiting TASK-041 billing/inventory backend.
4. **QueueBoardPage drag-drop** — 5-column layout is complete; card drag-drop state transitions not implemented (future scope, no API yet).

---

## Review Focus Areas

- PatientDetailPage 3-col layout responsiveness on < 1280px viewport
- QueueBoardPage "Đăng ký" vs "Chờ khám" column split logic (5-min timestamp heuristic — confirm with PM)
- ARAgingReportPage export format (currently CSV via xlsx mock — confirm with billing team)
- StocktakePage wizard step 3 "Đối chiếu" diff table (mocked data — confirm field names with BE)

---

## Fix-mode addendum (TASK-040 review → CHANGES_REQUESTED fix pass)

**Date:** 2026-05-01
**Agent:** Code Implementation (fix-mode)
**Files patched:** 5

### 1. PatientDetailPage — 4 tabs wired

`src/pages/patients/PatientDetailPage.tsx`

All 4 stub tabs replaced with real implementations:

| Tab | Wired | Endpoint used | Fallback |
|-----|-------|---------------|----------|
| Visits | ✅ wired | `doctorApi.getPatientVisits(patientId)` → `GET /api/v1/visits?patient_id=` | `PendingBEState` empty state with explanatory message |
| Prescriptions | ✅ wired | `GET /api/v1/prescriptions?patient_id=` (direct `api.get`) | `PendingBEState` empty state |
| Invoices | ✅ wired | `GET /api/v1/invoices?patient_id=` (direct `api.get`) | `PendingBEState` empty state |
| Vitals | ✅ wired (partial) | `doctorApi.getPatientVisits` for timeline; per-visit vitals batching deferred to TASK-041 | Recharts `LineChart` with visit timeline axis; explanatory note in chart |

- BHYT tab: kept as `DevPlaceholder` (TASK-034 dependency — not in scope)
- Prescriptions/Invoices use direct `api.get` since typed module APIs only accept `visit_id`; if BE returns 404/error, `PendingBEState` message displays
- Vitals chart rendered with `recharts LineChart`; weight/BP/temperature lines wired to fields but will be empty until TASK-041 per-patient vitals endpoint is live

### 2. ExpiryProcessingPage — a11y fixes

`src/pages/pharmacy/ExpiryProcessingPage.tsx`

- Select-all checkbox: added `aria-label="Chọn tất cả lô sắp hết hạn"`
- Each row checkbox: added `aria-label="Chọn lô {medicine_name} - {batch_code}"`
- `ConfirmModal`:
  - Added `role="dialog"` + `aria-modal="true"` + `aria-labelledby={CONFIRM_MODAL_TITLE_ID}`
  - Focus trap: `useEffect` focuses Cancel button on open
  - Esc-to-close: `useEffect` with `keydown` listener, respects `loading` state

### 3. ForgotPassword — scope descope documented

`src/pages/auth/ForgotPasswordPage.tsx`

- Added scope decision comment at top of file:
  > SCOPE DECISION (TASK-040 review): keeping 2-state pattern. 3-step OTP flow per Stitch refs quen-mat-khau-1/2/3 deferred to follow-up task — depends on SMS OTP backend service.

`src/locales/vi/auth.json` + `src/locales/en/auth.json`

- Fixed `forgotPassword.errors.networkFallback` copy: removed internal "BE/mock" terminology; now user-facing ("Tạm thời không kết nối được. Vui lòng thử lại sau.")

### Verification

| Check | Result |
|-------|--------|
| `tsc --noEmit` | 0 errors |
| `npm run lint` | 0 warnings, 0 errors |
| `npm test -- --run` | 566/566 passed (54 files) — no regressions |
