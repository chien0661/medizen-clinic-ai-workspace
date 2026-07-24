# Handoff: TASK-111 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary
`cancel_appointment` now cascade-cancels a checked-in appointment's linked visit
via `visit_service.transition_to_cancel`, closing the M-2 orphan-WAITING-visit
bug. Cascade logic, atomicity (single session + single commit, rollback on
raise), and the guard coupling are all correct; no critical/major issues.

## Key Findings (MINOR, for awareness)
- Block-path 422 message says "Chưa thể hủy lượt khám…" (visit-framed) when the
  user cancelled an appointment — acceptable but slightly surprising wording.
- No integration test covers the block path (money collected / meds dispensed →
  appointment cancel 422); it's covered indirectly by visits-module tests.

## Focus Areas for Testing
1. **Core regression:** check-in → cancel appointment → confirm visit is
   `CANCELLED` (not orphan `WAITING`) and appointment is `cancelled`.
2. **IN_PROGRESS cascade:** start visit, then cancel appointment → visit `CANCELLED`.
3. **Block path (the untested gap):** visit with a paid invoice OR dispensed
   medicines → cancel appointment should return **422** (`BusinessRuleError`),
   appointment must stay **uncancelled**, visit untouched — verify no partial
   state (atomic rollback).
4. **Terminal-state skip:** COMPLETED / already-CANCELLED visit → appointment
   cancel proceeds, visit unchanged.
5. **No-visit regression:** appointment never checked in → cancel still 200.
6. Static tooling on the host is broken; if the isolated stack allows, re-run
   ruff/mypy on the two changed files to confirm 0 new findings.
