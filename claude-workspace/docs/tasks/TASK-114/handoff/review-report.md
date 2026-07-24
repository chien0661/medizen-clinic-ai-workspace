# Review Report — TASK-114 (M-17 + M-18)

**Reviewer**: Code Review Agent
**Date**: 2026-07-25
**Branch**: `fix/TASK-114-visit-volume-columns` (base `origin/dev` @ `0dfb3eb`)
**Commit**: `c86fb4d`
**Scope**: FE-only — visit-volume report table columns + Total reconciliation.
**Decision**: **APPROVED** → IN_TESTING

## Summary

Fix adds the two missing statuses (`IN_PROGRESS` "Đang khám", `AWAITING_PAYMENT`
"Chờ thanh toán") as columns in both the on-screen table (`VisitVolumePage.tsx`) and the
CSV export (`helpers.ts`), and adds `case "AWAITING_PAYMENT"` to the adapter switch in
`getVisitVolume` (`api.ts`) plus the `awaiting_payment` field on `VisitVolumePoint`
(`types.ts`). All 6 BE statuses now have a switch case, so Σcolumns == Total by
construction. Locale keys (vi/en) added.

## Σcolumns == Total — VERIFIED

- **Adapter** (`api.ts:281-288`): all 6 known BE statuses (WAITING, IN_PROGRESS,
  AWAITING_PAYMENT, COMPLETED, CANCELLED, NO_SHOW) each have a `case` that assigns to a
  distinct column field. `point.total += r.count` accumulates every row. Since every
  known status also lands in a column, Σ(6 columns) == total.
- **On-screen table** (`VisitVolumePage.tsx:168-201`): 8 headers = 8 body cells, order
  period/total/completed/waiting/in_progress/awaiting_payment/cancelled/no_show. Both
  IN_PROGRESS and AWAITING_PAYMENT now rendered. ✔
- **CSV** (`helpers.ts` `exportVisitVolumeCsv`): header + data rows both include
  "Đang khám" and "Chờ thanh toán". ✔
- **Test evidence**: `visitVolumeApi.test.ts` test 1 asserts exact E2E numbers
  (21 = 3+8+7+1+0+2) and `columnSum === point.total`; test 2 feeds one row per known
  status and asserts columnSum === total; test 3 confirms case-insensitive mapping. All
  genuinely assert the reconciliation. ✔

## Findings

### CRITICAL
- None.

### MAJOR
- None.

### MINOR
1. **Residual `total += r.count` on unknown status** (`api.ts:280`) — total still
   accumulates unconditionally, so if BE ever emits a *new/unknown* status outside the 6
   cases, it would inflate total without a column (the same failure class as M-18). All
   currently-known statuses are covered per AC, so not blocking; a defensive `default`
   case or deriving total from columns would be more robust. Out of current scope.
2. **CSV vs UI column ordering differs** — UI shows completed before waiting/in_progress;
   CSV lists waiting/in_progress/awaiting_payment before completed. Pre-existing ordering
   style; each header maps to the correct value in both, so no correctness impact.
3. Chart (Recharts) left unchanged — correctly out of scope per bug report.

## Quality Gates

- **Tests**: `npx vitest run src/tests/reports` → 7 files, **31 passed** (3 new, 28
  pre-existing, none broken). ✔
- **Type-check**: `npm run type-check` (tsc --noEmit) → **clean, no errors**. ✔
- **Lint**: `npm run lint` → **18 pre-existing problems (17 errors, 1 warning)**, all in
  untouched files (VitalsPage, VssIntegrationConfigPage, VssSyncLogPage,
  TemplateRenderer). Confirmed none of the 8 changed files appear in lint output — **no
  new lint breakage**. ✔
- **Security**: FE-only display/CSV change, no secrets, no injection surface. ✔

## Conclusion

All quality gates pass; no critical/major issues. Both UI and CSV now show IN_PROGRESS +
AWAITING_PAYMENT and reconcile with Total. **APPROVED → IN_TESTING.**
