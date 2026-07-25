# Handoff: TASK-115 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary

`POST /visits/{id}/exam` now gates on `require_permission("visit.write")` AND
`require_role(["doctor","nurse","admin"])` — identical to the `/start` & `/complete`
lifecycle endpoints. Receptionist (visit.write, no clinical role) → 403; the
WAITING→IN_PROGRESS auto-promote side-effect is now behind the role gate.

## Key Findings

- MINOR: automated positive-path (200) uses the `admin` token; no literal `doctor`/`nurse`
  user exists in the `etx` fixture. Mechanism is proven, but see focus areas.

## Focus Areas for Testing

- Verify a real **doctor** and **nurse** token → 200 on `POST /visits/{id}/exam`
  (AC literally names doctor→200; only admin is asserted in the automated test).
- Confirm receptionist → 403 AND visit remains `WAITING` (no auto-start leak).
- Confirm receptionist GET `/visits/{id}/exam` still → 200 (read unaffected).
- Regression: exam create/update by a clinical actor still auto-promotes WAITING→IN_PROGRESS.
- Negative: any other non-clinical role holding `visit.write` is also blocked.
