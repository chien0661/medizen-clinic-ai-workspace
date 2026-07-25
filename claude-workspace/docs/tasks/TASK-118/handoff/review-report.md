# Review Report — TASK-118 (FIX iteration)

**Reviewer**: Code Review Agent
**Date**: 2026-07-25
**Branch**: `fix/TASK-118-fe-ux-cluster` (worktree `F:/MyProject/clinic-cms-workspace/_fix118-web`), base `origin/dev` @ `f9825c9`
**Diff**: `git -C .../_fix118-web diff origin/dev...HEAD`
**Scope**: FE-only. Read-only review, no code changes.

## Decision (round 2, commit `3c97a11`): APPROVED → IN_TESTING

**Round 1 was CHANGES_REQUESTED** (MAJOR: M-14 `/shifts` 403 not fixed — see below).
**Round 2 (`3c97a11`) resolves both MAJOR findings and is APPROVED:**
- `AttendanceWidget.tsx` now gates the shifts query with
  `enabled: canViewShifts` where `canViewShifts = isSuperuser || (user?.permissions ?? []).includes("shift.manage")`,
  read from `useAuthStore` — the identical source/pattern MainDashboardPage uses for
  `canViewFinancial` (verified `authStore` exposes `isSuperuser` + `user.permissions: string[]`).
  With `enabled:false` React Query never invokes the queryFn, so `GET /shifts` **does not fire**
  for a doctor; the widget falls to the existing "Không có ca hôm nay" branch. Self check-in via
  `POST /attendance/check-in` (no manage perm) is unaffected.
- `myShifts` comment corrected (no longer claims "public"; documents the `shift.manage` gate).
- Test adds 2 real assertions gating on permission (`hrApi.myShifts` NOT called without
  `shift.manage`; IS called with it), driven by overriding the `useAuthStore` mock per case — a
  genuine assertion of the `enabled` gate, not hidden by the wholesale `hrApi` mock. `beforeEach`
  restores a `shift.manage`-holding default so pre-existing shift-display tests still exercise the
  shift UI (no regression).

Original round-1 findings retained below for history.

---

## Round 1 — CHANGES_REQUESTED (superseded by round 2 above)

Two of the three M-14 sub-fixes and both M-13 and M-16 were correct. But one of the three
explicitly-listed M-14 defects — the `/shifts` 403 on doctor dashboard load — was **not
actually fixed** in round 1. The change gave a false impression of a fix; the forbidden call still fired.

---

## Findings by severity

### MAJOR

1. **M-14 shifts 403 still fires — `myShifts` is the same endpoint as `listShifts`**
   (`src/components/hr/AttendanceWidget.tsx:41`, `src/modules/hr/api.ts:215`)
   - `hrApi.myShifts` and `hrApi.listShifts` both issue `GET ${BASE}/shifts?from&to` — an
     **identical HTTP request** when no `staff_id` is passed (the widget passes none).
   - BE (`clinic-cms-merge/app/modules/hr/api/routes.py:397-401`) has exactly **one** `/shifts`
     GET route, gated by `Depends(require_permission("shift.manage"))`. There is **no**
     self-service shifts endpoint. A doctor without `shift.manage` still gets **403 on every
     dashboard load**; the rename changes nothing at the network layer.
   - The only real mitigation applied is `retry: false` (3 calls → 1). The E2E defect
     (`/shifts` → 403) and the AC "no forbidden calls / no 403 spam" are **not met** — a
     forbidden call still fires once per load.
   - The `myShifts` wrapper comment ("My shifts (public — any authenticated user)") and the
     handoff root-cause #2 ("myShifts ... doesn't require shift-management permission") are
     **factually incorrect**.
   - Suggested fix: gate the shifts query so it does not fire for roles that will 403 —
     `enabled: isSuperuser || (user?.permissions ?? []).includes("shift.manage")`. With no
     shift data the existing null-guards / "Không có ca hôm nay" branch already handle display,
     and self check-in via `POST /attendance/check-in` (no manage perm) is unaffected. Also
     correct the misleading `myShifts` comment.

2. **M-14 AttendanceWidget test does not assert the shifts fix**
   (`src/tests/hr/AttendanceWidget.test.tsx`)
   - The test mocks `hrApi` wholesale, so it passes identically whether the code calls
     `listShifts` or `myShifts` and regardless of the real endpoint's permission — it provides
     **no assurance** that the 403 was eliminated. (The new `notLinked` case is fine.)

### MINOR

3. **`getRangeStats` still calls `/reports/revenue` unconditionally** (flagged by implementer,
   out of scope). Reasonable to defer — only fires when a non-financial role uses the custom
   date-range picker, not on default load. Worth a follow-up task.

---

## Per-fix correctness

- **M-13 (service picker 0đ) — CORRECT.** `Service.price` → `Service.default_price: number | string`,
  matching BE serialization (cross-checked `src/modules/admin/types.ts:302` — `default_price`).
  `formatCurrency` (`modules/doctor/helpers.ts:125`) accepts `string | number`. No other consumer
  of the old `.price` field remains (grep clean). Picker row reads `svc.default_price`.
- **M-14 revenue — CORRECT.** `getSnapshot(canViewFinancial=true)` skips `/reports/revenue` when
  false, defaulting revenue/pending to 0 (guarded by `revTodayRaw.value`); `weeklyRevenueQuery`
  gets `enabled: canViewFinancial`; KPI card + weekly chart gated behind `canViewFinancial`; visits
  table expands to `lg:col-span-5` when chart hidden. `canViewFinancial` correctly derived from
  `report.financial` perm or superuser. Financial roles still see revenue.
- **M-14 attendance/me — CORRECT.** BE `GET /attendance/me` (routes.py:710) needs no permission;
  400 = no linked HR profile (data-state). `retry:false` + `notLinked` notice (added to
  `locales/{vi,en}/hr.json`) is the right handling; check-in flow hidden when it errors.
- **M-14 shifts — INCORRECT.** See MAJOR #1.
- **M-16 (UUID → patient name) — CORRECT.** `AppointmentPatientLabel` resolves `patient_id` via
  `patientApi.get` (`["patient", id]` query key → dedupe/cache, no N+1 explosion), renders
  `full_name (patient_code)` (both fields exist on `Patient`), loading state + truncated-id fallback
  on failure. Same pattern as ClinicalWorkspacePage/InvoiceDetailPage.

## Type-check / Lint

- Not independently re-run; the defect is a runtime/logic issue, not a compile error (the code
  type-checks — `myShifts` exists and types align). Handoff claims `tsc --noEmit` clean and lint
  clean on changed files, with pre-existing errors unchanged — plausible and consistent with the diff.

## Notes

- 5 pre-existing full-suite failures (QueuePage ×2, ForgotPasswordPage) acknowledged as
  unrelated / present on `origin/dev`.
- M-13 and M-16 are approvable as-is; only the M-14 shifts sub-fix (+ its test) needs rework.
