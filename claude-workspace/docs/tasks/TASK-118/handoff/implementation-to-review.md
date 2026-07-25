# TASK-118 — Implementation → Review handoff

**Repo:** clinic-cms-web (`chien0661/medizen-clinic-web`)
**Branch:** `fix/TASK-118-fe-ux-cluster` (base `origin/dev` @ `f9825c9`)
**Worktree:** `F:/MyProject/clinic-cms-workspace/_fix118-web` (left in place, not merged/deleted)
**Commit:** `1c8d5a0` — pushed to `origin/fix/TASK-118-fe-ux-cluster`

## M-13 — Service picker showed 0đ

**Root cause:** `Service` (in `src/modules/doctor/types.ts`) declared a `price: string`
field that does not exist on the BE catalog response — the BE serializes the
service price as `default_price` (confirmed against the admin catalog's own
`Service` type in `src/modules/admin/types.ts`). `ServicesTab.tsx` read
`svc.price`, always `undefined` → `formatCurrency` parsed `NaN` → rendered "0 đ".
The row only showed the right price after adding, because `VisitService.unit_price`
is a different, correctly-named field computed server-side at add time.

**Fix:**
- `src/modules/doctor/types.ts` — renamed `Service.price` → `Service.default_price: number | string`.
- `src/components/doctor/ServicesTab.tsx` — picker row now reads `svc.default_price`.

**Test:** `src/components/doctor/ServicesTab.test.tsx` (new) — opens the picker,
asserts "200.000" renders and no row shows "0 đ"/"0 ₫".

## M-14 — Doctor dashboard 403/400 spam

**Root causes (3 distinct bugs on `/dashboard`, which is `MainDashboardPage`,
shared by all roles — not the separate `/doctor/dashboard` page):**
1. `dashboardApi.getSnapshot()` and the weekly-revenue query always called
   `GET /reports/revenue`, which requires `report.financial` — 403 for
   doctor, on every load (`refetchInterval: 30_000`).
2. `AttendanceWidget` called `hrApi.listShifts` (the admin/manage listing
   endpoint) instead of `hrApi.myShifts` (the existing self-service wrapper
   already used correctly by `AttendanceSelfPage`) — 403 for any role
   without shift-management permission.
3. `GET /attendance/me` 400s when the account has no linked HR staff
   profile (a data-state fact, not a permission the FE can pre-check) — and
   React Query's global default retries non-auth errors twice, multiplying
   every one of the above into 3 requests per failed call per load.

**Fix:**
- `src/modules/dashboard/api.ts` — `getSnapshot(canViewFinancial = true)`
  skips the `/reports/revenue` sub-request entirely when `false` (revenue/
  pending-invoices default to 0, same as the old failure path, just without
  the wasted/noisy call).
- `src/pages/dashboard/MainDashboardPage.tsx` — passes the existing
  `canViewFinancial` (`report.financial` perm or superuser) into
  `getSnapshot`; `weeklyRevenueQuery` gets `enabled: canViewFinancial`; the
  "Doanh thu" KPI card and the weekly-revenue chart panel are now hidden
  (not just empty) when the role lacks the permission; the visits table
  expands to full width when the chart is hidden.
- `src/components/hr/AttendanceWidget.tsx` — switched `hrApi.listShifts` →
  `hrApi.myShifts`; added `retry: false` to both shift/attendance queries
  (permission/data-state errors won't succeed on retry); when
  `/attendance/me` errors (e.g. 400 "not linked"), the widget now shows a
  quiet notice (`hr:attendance.notLinked`, added to `locales/{vi,en}/hr.json`)
  instead of an interactive check-in flow that could never succeed.

**Out of scope (flagged, not fixed):** `dashboardApi.getRangeStats` (used
only when the user picks a non-"today" date range) still calls
`/reports/revenue` unconditionally — not part of the E2E finding (default
load), left alone to keep the fix minimal; worth a follow-up if a
non-financial role uses the date picker.

**Tests:** `src/tests/dashboard/MainDashboardPage.test.tsx` — 2 new cases
(hides revenue KPI/chart + `getSnapshot(false)` + `getWeeklyRevenue` never
called, without `report.financial`; shows them + `getSnapshot(true)` with
it). `src/tests/hr/AttendanceWidget.test.tsx` — updated for the `myShifts`
rename, + 1 new case for the "not linked" 400 notice.

## M-16 — Appointment cards showed truncated UUID

**Root cause:** `Appointment` (BE, `src/modules/reception/types.ts`) only
carries `patient_id` — unlike `Visit`, which the BE enriches with
`patient_name`/`patient_code` for the queue board (TASK-088). The card
rendered `appt.id.slice(0, 8)…` (the appointment id, not even the patient
id) as a stand-in.

**Fix:** `src/pages/appointments/AppointmentPage.tsx` — new
`AppointmentPatientLabel` subcomponent resolves `patient_id → Patient` via
`patientApi.get` (same pattern as `ClinicalWorkspacePage`/
`InvoiceDetailPage`), rendering `full_name (patient_code)`; falls back to
the old truncated-id display only if the patient can't be resolved. React
Query dedupes by `["patient", patientId]`, so repeat patients across rows
cost one request.

**Test:** `src/tests/appointments/AppointmentPage.test.tsx` (new) — asserts
name+code render and no UUID fragment is shown; a second case covers the
not-found fallback.

## Verification
- Vitest (targeted): 4 files, **19/19 passed**.
- Vitest (full suite): 1107/1112 passed; the 5 failures (QueuePage ×2,
  ForgotPasswordPage ×1 file / see below) are **pre-existing on
  `origin/dev`** — reproduced identically after `git stash` of this branch's
  changes. Not touched by this task.
- `tsc --noEmit`: clean.
- `npm run lint`: clean on all changed files; the 17 pre-existing errors
  elsewhere (VssIntegrationConfigPage, VssSyncLogPage, VitalsPage,
  TemplateRenderer) are unchanged from `origin/dev`.

## Files touched
- `src/modules/doctor/types.ts`, `src/components/doctor/ServicesTab.tsx` (+ new test)
- `src/modules/dashboard/api.ts`, `src/pages/dashboard/MainDashboardPage.tsx`,
  `src/components/hr/AttendanceWidget.tsx`, `src/locales/{vi,en}/hr.json`
  (+ updated/new tests)
- `src/pages/appointments/AppointmentPage.tsx` (+ new test)

---

## Fix-round-2 (2026-07-25) — M-14 shifts, per review CHANGES_REQUESTED

**Reviewer's finding (`review-to-implementation.md`, `review-report.md`):**
`hrApi.myShifts` and `hrApi.listShifts` issue the *identical* `GET /api/v1/shifts`
request. The BE has exactly one `/shifts` GET route, gated by
`require_permission("shift.manage")` (`clinic-cms-merge/app/modules/hr/api/routes.py:397-401`)
— there is no self-service shifts endpoint. So round-1's rename to `myShifts`
was a no-op at the network layer: a doctor still got 403 on every dashboard
load. The `myShifts` wrapper comment ("public — any authenticated user") and
my round-1 root-cause write-up were factually wrong, as flagged.

**Fix applied:**
- `src/components/hr/AttendanceWidget.tsx` — reads `user`/`isSuperuser` from
  `useAuthStore` (same source `MainDashboardPage` uses for
  `canViewFinancial`) and computes
  `canViewShifts = isSuperuser || (user?.permissions ?? []).includes("shift.manage")`.
  The shifts query now gets `enabled: canViewShifts` — it does not fire at
  all for a role without `shift.manage`. `todayShift` stays `null` in that
  case, which the existing null-guard already renders as
  "Không có ca hôm nay"; self check-in (`POST /attendance/check-in`, no
  manage perm required) is unaffected.
- `src/modules/hr/api.ts` — corrected the `myShifts` comment: it is the same
  `shift.manage`-gated `/shifts` route as `listShifts`, not a public
  self-service endpoint; callers must gate on the permission themselves.
- `src/tests/hr/AttendanceWidget.test.tsx` — default mocked user now carries
  `shift.manage` (so the pre-existing shift-display tests, e.g. AC5/AC6,
  keep exercising real shift data) plus `isSuperuser: false`; `beforeEach`
  re-asserts this default (via `mockImplementation`) since `clearAllMocks()`
  doesn't reset an override from a prior test. Two new cases assert the
  actual gate rather than mocking around it:
  - `"M-14: does NOT call hrApi.myShifts (GET /shifts) for a role without shift.manage"`
    — user with `["visit.read","visit.write"]` (no `shift.manage`, not
    superuser) renders "Không có ca hôm nay" and asserts
    `hrApi.myShifts` was never called.
  - `"M-14: DOES call hrApi.myShifts (GET /shifts) for a role with shift.manage"`
    — default (has `shift.manage`) asserts `hrApi.myShifts` was called with
    `{ from: todayStr, to: todayStr }`.

**Verification:**
- `npx vitest run` (4 affected files): 21/21 passed.
- `npx vitest run` (full suite): 1111/1114 passed; same 3 pre-existing
  failures as round-1 (QueuePage ×2, ForgotPasswordPage ×1) — unrelated,
  reproducible on a clean `origin/dev` stash.
- `tsc --noEmit`: clean.
- `npm run lint` on changed files (`AttendanceWidget.tsx`, `hr/api.ts`,
  `AttendanceWidget.test.tsx`): clean, `--max-warnings 0`.

**Commit:** `3c97a11` "fix(ui): gate shifts query behind shift.manage so
non-manager roles don't 403 (TASK-118)" — pushed to
`origin/fix/TASK-118-fe-ux-cluster`.

**Files touched (round-2):** `src/components/hr/AttendanceWidget.tsx`,
`src/modules/hr/api.ts`, `src/tests/hr/AttendanceWidget.test.tsx`.
