# Handoff: TASK-118 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED (fix-round-2, commit `3c97a11`)

## Summary
FE-only UX cluster (M-13 service picker price, M-14 doctor dashboard 403/400 spam, M-16
appointment card patient name). Round-1 was CHANGES_REQUESTED because the M-14 `/shifts` sub-fix
was a no-op (`myShifts`/`listShifts` both hit the same `shift.manage`-gated `GET /api/v1/shifts`).
Round-2 (`3c97a11`) gates the shifts query behind `canViewShifts = isSuperuser ||
permissions.includes("shift.manage")` via `enabled`, so the call never fires for a doctor —
verified against the BE route and via 2 real unit assertions. All fixes now correct.

## Key Findings (for awareness)
- MINOR: `dashboardApi.getRangeStats` still calls `/reports/revenue` unconditionally on custom
  date ranges (out of scope, deferred; not on default load).
- BE constraint: there is **no** self-service shifts endpoint — `GET /shifts` requires
  `shift.manage`. A doctor legitimately sees "Không có ca hôm nay" (no shift data), by design.

## Focus Areas for Testing (FE-only scope; no BE changes)
1. **M-14 doctor dashboard (primary)** — log in as a doctor (no `shift.manage`, no
   `report.financial`, no linked HR profile) and confirm the network tab shows **no**
   `GET /reports/revenue`, **no** `GET /shifts`, and a single (non-retried) `GET /attendance/me`.
   Revenue KPI + weekly-revenue chart hidden; visits table full-width; AttendanceWidget shows the
   "not linked" notice; shift area shows "Không có ca hôm nay".
2. **M-14 financial/manager role** — a role with `report.financial` + `shift.manage` still sees
   the revenue KPI/chart and its own shift data (regression check).
3. **M-13** — doctor exam → "Thêm dịch vụ" picker shows real unit prices (e.g. 200.000), not 0đ.
4. **M-16** — appointment cards show patient name + code (not a truncated UUID); truncated-id
   fallback only when a patient can't be resolved.
5. Confirm no console errors / no forbidden (403/400) calls on default doctor dashboard load.

## Build status
- Handoff reports `tsc --noEmit` clean, lint clean on changed files; 5 pre-existing full-suite
  failures (QueuePage ×2, ForgotPasswordPage) unrelated to this task.
