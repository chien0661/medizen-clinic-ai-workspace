# Handoff: TASK-117 -> Documentation Agent

**From**: Test Agent
**To**: Documentation Agent
**Status**: DOCUMENTING

## Summary
All tests PASSED — 95/95 (`tests/integration/appointments` +
`tests/integration/visits`) on isolated stack `x117`. Capacity/overlap is now
checked as a time-window intersection (can't be evaded with a small minute
offset), and `PATCH scheduled_at` actually reschedules, rechecks capacity,
and rejects past dates with 422 instead of silently dropping. Ready for
documentation.

## Test Results
- Backend: 95 scenarios, 95 passed (`tests/integration/appointments
  tests/integration/visits`), migration head confirmed at 0069.
- Key checks: overlap-by-offset -> 409; non-overlap after window ends ->
  201; exact-same-time -> 409 (regression); PATCH scheduled_at persists;
  reschedule into full slot rechecks capacity -> 409 (original untouched);
  past-date PATCH -> 422.
- Test report: `docs/tasks/TASK-117/deliveries/test-reports/test-report.md`
