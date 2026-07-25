# Handoff: TASK-118 → Code Implementation Agent

**From**: Code Review Agent
**To**: Code Implementation Agent
**Status**: IN_PROGRESS
**Decision**: CHANGES_REQUESTED

## Summary
M-13, M-16, and two of three M-14 sub-fixes (revenue skip, attendance/me notLinked) are correct
and approvable. But the M-14 `/shifts` 403 is not actually fixed: `hrApi.myShifts` and
`hrApi.listShifts` issue the identical `GET /api/v1/shifts` request, and the BE gates that single
route behind `require_permission("shift.manage")` — so a doctor still gets 403 on every dashboard
load. The rename is a no-op at the network layer; only `retry:false` reduced the spam.

## Required Changes

1. **Stop the `/shifts` 403 for roles without `shift.manage`.**
   - `src/components/hr/AttendanceWidget.tsx:~38` — gate the shifts query:
     `enabled: isSuperuser || (user?.permissions ?? []).includes("shift.manage")`
     (derive from the same auth/permission source `MainDashboardPage` uses for `canViewFinancial`).
   - When the query is disabled, `todayShift` stays null — the existing null-guards and
     "Không có ca hôm nay" branch already handle display, and self check-in via
     `POST /attendance/check-in` (no manage perm required) still works.
   - Verify against BE: `clinic-cms-merge/app/modules/hr/api/routes.py:397-401` — the only
     `GET /shifts` route requires `shift.manage`; there is no self-service shifts endpoint.

2. **Fix the misleading comment / root cause.**
   - `src/modules/hr/api.ts:214` — the `myShifts` comment "public — any authenticated user" is
     wrong (`GET /shifts` requires `shift.manage`). Correct or remove it. If `myShifts` is now
     identical to `listShifts` with no distinct purpose, reconsider keeping a separate wrapper.

3. **Make the test actually assert the fix.**
   - `src/tests/hr/AttendanceWidget.test.tsx` — add a case proving the shifts query does **not**
     fire when the user lacks `shift.manage` (e.g. assert `hrApi.myShifts` is not called for a
     doctor-role/no-perm render), so the regression is caught. The current suite mocks `hrApi`
     and would pass regardless of endpoint/permission.

## Not changing (already correct)
- M-13 (`default_price`), M-16 (`AppointmentPatientLabel`), M-14 revenue skip + gating,
  M-14 `/attendance/me` `retry:false` + `notLinked` notice.

## Out of scope (leave as-is / follow-up)
- `dashboardApi.getRangeStats` still calls `/reports/revenue` unconditionally on custom date
  ranges — acceptable to defer (not part of the default-load E2E finding).
