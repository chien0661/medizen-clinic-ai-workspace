# Handoff: TASK-114 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary
Visit-volume report fix (M-17 + M-18) adds IN_PROGRESS + AWAITING_PAYMENT columns to the
table and CSV and covers all 6 BE statuses in the adapter switch, so Σcolumns == Total.
All quality gates pass (31 vitest tests, clean type-check, no new lint).

## Key Findings (MINOR, for awareness)
- `total += r.count` in `getVisitVolume` still runs unconditionally — an unknown/new BE
  status would inflate total without a column. All known statuses covered; out of scope.
- CSV column order differs from UI table order (cosmetic; values map correctly).

## Focus Areas for Testing
- **FE-only — no backend/Docker needed.** Test phase = vitest + optionally a quick UI check.
- Run `npx vitest run src/tests/reports` (worktree `F:/MyProject/clinic-cms-workspace/_fix114-web`).
- Confirm `visitVolumeApi.test.ts` asserts Σcolumns == Total with E2E numbers
  (21 = 3+8+7+1+0+2) and that every known status maps to a column.
- Optional UI check: VisitVolumePage table shows "Đang khám" + "Chờ thanh toán" columns
  and per-row Total == sum of status columns; CSV export contains both new columns and
  reconciles to Total. Verify vi + en locale labels render.
