# Test Report: TASK-114 - visit-volume columns (M-17/M-18)

**Test Agent:** Automation Tester
**Date:** 2026-07-25
**Status:** ALL IN-SCOPE PASSED

## Environment

- Worktree `F:/MyProject/clinic-cms-workspace/_fix114-web`, branch
  `fix/TASK-114-visit-volume-columns` @ `c86fb4d`. `node_modules` already
  installed and newer than `package-lock.json` (no `npm ci` needed; skipped
  redundant install). FE-only, no Docker involved.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Vitest (`src/tests/reports`) | 31 | 31 | 0 | 100% |
| `type-check` (`tsc --noEmit`) | - | clean (exit 0) | - | - |

Commands:
- `npx vitest run src/tests/reports`
- `npm run type-check`

## Key Assertions Verified

- **Sigma(columns) == Total, including IN_PROGRESS + AWAITING_PAYMENT** —
  `describe("reportsApi.getVisitVolume") > it("maps every known status to a
  column and sums to total (M-17 + M-18 repro data)")`
  (`src/tests/reports/visitVolumeApi.test.ts:43`) — PASSED. Uses the exact
  E2E repro numbers (Total=21, Hoàn thành=3, Chờ khám=8, Đang khám=7, Đã
  hủy=1, Không đến=0, AWAITING_PAYMENT=2) and asserts
  `columnSum === point.total`.
- **Adapter covers all BE statuses (no status silently dropped from the
  column mapping)** —
  `it("every BE status has a mapped column so no row is counted in total
  without a column")` — iterates all 6 known statuses
  (`WAITING/IN_PROGRESS/AWAITING_PAYMENT/COMPLETED/CANCELLED/NO_SHOW`),
  asserts `columnSum === point.total` — PASSED.
- **Case-insensitive status mapping** —
  `it("handles lowercase status values from BE the same way")` — PASSED.
- **No new breakage**: all 7 report test files (31 tests total) passed;
  `tsc --noEmit` clean.

## Failures

None. 31/31 passed; type-check clean.

## Next Steps

All in-scope tests passed. Ready to proceed to Documentation phase.

**Task status -> DOCUMENTING**

---

**Total Scenarios:** 31 + type-check
**Environment:** FE-only, worktree `_fix114-web`, no Docker required.
