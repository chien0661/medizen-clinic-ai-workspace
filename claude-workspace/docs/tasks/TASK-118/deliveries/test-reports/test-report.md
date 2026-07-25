# Test Report: TASK-118 - FE UX cluster (M-13/M-14/M-16)

**Test Agent:** Automation Tester
**Date:** 2026-07-25
**Status:** ALL IN-SCOPE PASSED

## Environment

- Worktree `F:/MyProject/clinic-cms-workspace/_fix118-web`, branch
  `fix/TASK-118-fe-ux-cluster` @ `3c97a11`.
- `node_modules` already installed and newer than `package-lock.json` — no
  `npm ci` needed (skipped redundant install), Node v20.20.0 / npm 10.8.2.
- No Docker involved — pure vitest + tsc run directly in the worktree.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Frontend vitest (4 changed test files) | 21 | 21 | 0 | 100% |
| Frontend `type-check` (`tsc --noEmit`) | - | clean (exit 0) | - | - |

Commands:
- `npx vitest run src/components/doctor/ServicesTab.test.tsx src/tests/hr/AttendanceWidget.test.tsx src/tests/dashboard/MainDashboardPage.test.tsx src/tests/appointments/AppointmentPage.test.tsx`
- `npm run type-check`

Note: the assignment referenced `src/pages/dashboard/*.test.tsx`; the actual
test file for `MainDashboardPage` lives at
`src/tests/dashboard/MainDashboardPage.test.tsx` (confirmed via
`git diff --stat` against the two fix commits, which touched exactly this
file plus the other three run above — no other test files were touched).

## Key Assertions Verified

- **M-13 (service price)** —
  `ServicesTab — M-13 picker price > shows the real unit price in the search
  dropdown (not 0đ)` (`src/components/doctor/ServicesTab.test.tsx`) —
  PASSED.
- **M-14 (shifts query gated by `shift.manage`)** —
  `AttendanceWidget > M-14: does NOT call hrApi.myShifts (GET /shifts) for a
  role without shift.manage` and `M-14: DOES call hrApi.myShifts (GET
  /shifts) for a role with shift.manage`
  (`src/tests/hr/AttendanceWidget.test.tsx`) — both PASSED.
- **M-14 (revenue card hidden for non-financial)** —
  `MainDashboardPage > M-14: hides revenue KPI + weekly-revenue chart without
  report.financial` and `M-14: shows revenue KPI + weekly-revenue chart for a
  user with report.financial`
  (`src/tests/dashboard/MainDashboardPage.test.tsx`) — both PASSED.
- **M-16 (appointment card shows patient name)** —
  `AppointmentPage — M-16 patient name on cards > shows the patient's name +
  code instead of the truncated UUID` and `falls back to the truncated id if
  the patient can't be resolved`
  (`src/tests/appointments/AppointmentPage.test.tsx`) — both PASSED.
- **No regression**: remaining AttendanceWidget (check-in/out, late/OT
  calculation, duplicate check-in 409 toast, no-shift-today, not-linked
  notice) and MainDashboardPage (loading/error states, quick actions,
  attendance widget render) tests all green; `tsc --noEmit` clean.

## Failures

None. 21/21 vitest passed; type-check clean.

## Next Steps

All in-scope tests passed. Ready to proceed to Documentation phase.

**Task status -> DOCUMENTING**

---

**Total Scenarios:** 21 + type-check
**Environment:** worktree `_fix118-web`, no Docker
