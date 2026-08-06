# Handoff: TASK-138 → Documentation Agent

**From**: Test Agent
**To**: Documentation Agent
**Status**: DOCUMENTING

## Summary

All tests PASSED (34/34 new-code scenarios; zero new failures in either full unit suite — BE 1133/1145, FE 1260/1264, all remaining failures independently confirmed pre-existing/unrelated to this branch). All four task.md Acceptance Criteria are verifiably met, including AC #3 (payslip commission rate/source traceability), which was an open gap (m4) at review handoff and has since been fixed in commit `cebf0bd` — this test phase provides the first concrete verification of that fix against real data.

## Test Results

- **BE unit (full suite):** 1133 passed, 12 failed (all pre-existing, verified by exact test-ID match against the documented baseline).
- **FE unit (full suite):** 1260 passed, 4 failed (all pre-existing, verified by exact test-name match — includes the documented date-flaky `AttendanceWidget` test).
- **DB integration (real disposable Postgres, migrated 0001→0077):** 15/15 scenarios pass — `per_session`/`per_shift` engine paths (full/half days, no-grid-data non-fallback, completed-only shifts, rate≤0 handling, allowance/bonus/penalty with OT forced to 0, monthly/hourly regression, period boundaries), per-staff commission override resolution with payslip rate/source traceability, claw-back symmetry at the override rate (incl. mixed-doctor batch, idempotency, unmapped doctor, unposted period), and a TASK-128 zero-override regression.
- **Migration 0077:** 5/5 scenarios pass — fresh upgrade, collision-data coexistence, downgrade with collision data (previously aborted pre-fix, now succeeds correctly discarding overrides while preserving the clinic-wide rate), re-upgrade. One informational note (not a bug): downgrading with `per_session`/`per_shift` staff data present still fails on the `pay_type` column-narrowing step — this is explicitly documented as accepted/expected behavior in the migration's own docstring.
- **API/RBAC (real app, real Postgres+Redis):** 9/9 scenarios pass — commission-rule CRUD with `staff_id` (valid/cross-clinic-404/nonexistent-404/clinic-wide-unaffected/nurse-without-account-valid), PATCH immutability, DELETE-reverts-to-fallback, GET filter + tenant isolation, RBAC 403 for non-`payroll.manage` roles.
- **Business rules:** staff without a login account (`user_id=NULL`) fully supported for `per_session`/`per_shift` pay and as a commission-override target; automatic commission attribution remains doctor-account-only (unchanged TASK-128 limit, confirmed not regressed).

Full detail: `docs/tasks/TASK-138/deliveries/test-cases/test-cases.md`, `docs/tasks/TASK-138/deliveries/test-reports/test-report.md`.

## Notable Items for Documentation

- **AC #3 payslip traceability (m4)** now has real fields to document: `Payslip.session_rate`/`shift_rate`/`completed_shifts` (fix round 1) plus `procedure_rate_percent`/`procedure_rate_source`/`medicine_rate_percent`/`medicine_rate_source` (fix round 2, `cebf0bd`) — the FE renders these as a badge ("15% · tỷ lệ riêng" / "5% · tỷ lệ chung") on `PayrollPage`. Worth calling out explicitly in user-facing docs since it directly answers "which commission rate was applied."
- **i18n debt (m3, carried forward, not a defect):** `CommissionKpiConfigPage`'s new per-staff section and `StaffFormPage`'s new pay-type labels are hardcoded Vietnamese (matching those pages' pre-existing convention). Flag as known debt if the documentation covers i18n status.
- **Operational note worth documenting for admins:** `per_session` pay is driven entirely by the `AttendanceDay` grid tick — if a staff member's attendance for the period was never ticked, they earn **0** "buổi" pay even if they have Shift/TimeLog data from other flows. This is a deliberate design decision, not a bug, but is easy for an admin to be surprised by.
- **Migration downgrade caveat** worth a line in ops/runbook docs: downgrading migration 0077 after the feature has been used in production discards per-staff commission overrides (clinic-wide rates survive) and will hard-fail if any staff has `pay_type` `per_session`/`per_shift` at downgrade time — both documented in the migration's own docstring.

## Coverage

- Total new-code scenarios executed: 34 (100% pass).
- Full regression baseline: 2409 pre-existing tests re-run across both suites with zero new failures.
- Skipped (with reasons, see test-report.md "Skipped"): Playwright UI E2E against a live browser stack (optional per task brief; would require rebuilding the shared e2e stack against this branch) — FE covered at unit + DB/API level instead. A literal fault-injection test of the claw-back `SAVEPOINT` rollback (idempotent double-call was used as a proxy instead).
