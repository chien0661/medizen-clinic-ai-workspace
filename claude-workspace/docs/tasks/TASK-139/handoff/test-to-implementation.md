# Handoff: TASK-139 → Code Implementation Agent

**From**: Test Agent
**To**: Code Implementation Agent
**Status**: IN_PROGRESS

## Summary

Tests FAILED (1 new bug; everything else PASSED — see full breakdown below). BE (37 unit + 22
integration scenarios, all on a disposable stack — shared `clinic_e2e_*` containers were never touched)
and FE (1282/1282 baseline-matching regression + 21/21 new tests) are otherwise clean. One AC is not met:
**"Không regression PayrollPage hiện có."**

## Failures

- **BUG-001** (Medium): `src/pages/hr/PayrollPage.tsx:256` — the `tfoot` `colSpan` was bumped from `13`
  to `14` when the new "In phiếu" (print) column was added, but that's the wrong fix. It shifts the
  "Tổng thực nhận" total value cell to render under the **"In phiếu"** header instead of **"Thực nhận"**.
  `colSpan` should have stayed at `13` (the label cell still ends at "Điều chỉnh"; the value cell then
  naturally lands on "Thực nhận" as column 14, leaving "In phiếu" — an action column — with no footer
  cell, which is fine). Full evidence (header/row/footer column counts, before/after diff) in the bug
  report.
  - Bug report: `docs/tasks/TASK-139/bugs/BUG-001.md`
  - Suggested fix: one-line revert of `colSpan={14}` → `colSpan={13}`.

## Everything else — PASSED, no action needed

- BE full unit regression: 1156 passed, 12 pre-existing failures (unchanged baseline), 0 new. New
  `test_payroll_export.py` + `test_payroll_export_route_validation.py`: 23/23 pass.
- BE integration (disposable stack, migrated to 0077): shipped `test_payroll_export_e2e.py` 6/6 pass, no
  teardown ERROR; disposable-DB fixture-leak check found **zero** leftover rows (contrast noted for
  TASK-140 in the test report — not a TASK-139 issue).
- Additional scenarios built for this round (mixed pay types incl. per_session half-day + per_shift,
  formula-injection name, real two-clinic cross-tenant, forged `X-Clinic-Id`, `doctor`-role RBAC, 9
  malformed-`month` variants): all passed, reconciling exactly against `GET /hr/payroll`.
- FE full vitest regression: 1282 passed / 3 pre-existing failures (unchanged baseline) across 2 of 3
  runs (1 run had 2 extra flaky failures in an unrelated file, `CommissionKpiConfigPage.test.tsx` —
  reproduced-away on re-run, not a TASK-139 regression). New `PrintablePayslip`/`PrintPayslipModal`/
  `PayrollPage.export` tests: 21/21 pass.
- i18n vi/en parity for all `payroll.payslip.*`/`payroll.rateSource.*`/`payroll.payType.*` keys: 0
  missing, 0 orphan.
- PrintablePayslip: session/shift row hide/show, "tỷ lệ riêng"/"tỷ lệ chung" labeling, no-account staff
  rendering — all verified correct.

Full detail: `docs/tasks/TASK-139/deliveries/test-reports/test-report.md` and
`docs/tasks/TASK-139/deliveries/test-cases/test-cases.md`.

## Next steps for Implementation Agent

1. Fix BUG-001 (`colSpan={14}` → `colSpan={13}` in `PayrollPage.tsx`'s `tfoot`).
2. Optionally add a regression test so a future column addition doesn't silently break footer alignment
   again (suggested in the bug report).
3. Re-submit for testing (`/task-status TASK-139 IN_TESTING`) — given the fix is a 1-line, isolated
   revert with no other findings, a full re-run of BE+FE regression is still recommended but should be
   fast; the disposable-stack integration scenarios and FE component tests do not need to change.
