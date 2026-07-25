# TASK-115 — Code Review Report

**Reviewer:** Code Review Agent
**Date:** 2026-07-25
**Branch:** `fix/TASK-115-exam-rbac` (base `origin/dev` @ `85f70cc`, commit `bfc27ff`)
**Scope:** exam write RBAC (M-6) — `POST /visits/{id}/exam` must require a clinical role.
**Decision:** **APPROVED → IN_TESTING**

## Summary

The fix adds `Depends(require_role(["doctor", "nurse", "admin"]))` alongside the
existing `Depends(require_permission("visit.write"))` on `POST /visits/{visit_id}/exam`
in `app/modules/exam_templates/api/routes.py`. FastAPI ANDs the two dependencies,
so a receptionist (has `visit.write`, no clinical role) now gets 403, while
doctor/nurse/admin (who hold both) are unaffected. `GET /visits/{id}/exam` remains
`visit.read` only. Diff is 2 files, 1 commit, no unrelated route changes.

## Gate-consistency verdict — CONSISTENT

- The chosen gate is **byte-identical** to the sibling visit-lifecycle endpoints
  `/visits/{id}/start` and `/visits/{id}/complete` (`app/modules/visits/api/routes.py`
  lines 361-368, 382-388): same `require_permission("visit.write")` +
  `require_role(["doctor","nurse","admin"])` pair.
- This is the correct analog. Recording an exam **auto-promotes WAITING → IN_PROGRESS**
  (the same lifecycle transition `/start` gates); role-based gating matching `/start`
  is more appropriate than a `vital.write`-style permission, and avoids a new
  migration + cross-env role_permission seed (higher blast radius for a Medium fix).
- Auto-promote side-effect is now reachable only by an authorized clinical actor —
  the new test asserts the visit stays `WAITING` after the blocked receptionist call.
- Not over-restrictive: the allowed-role list exactly mirrors the lifecycle endpoints,
  so any role that can `/start` a visit can also record its exam. No legitimate
  clinical role is newly excluded relative to the existing lifecycle gates.

## Findings by severity

### CRITICAL
- None.

### MAJOR
- None.

### MINOR
- **Positive-path automated coverage uses `admin`, not a literal `doctor`/`nurse`**
  (`test_exam_templates_api.py`): the `etx` fixture has admin/nurse/receptionist but
  no `doctor` user, so the new test's 200-path retry uses the admin token. Since
  `require_role` matches via `any(r in user_roles for r in allowed_roles)`, admin
  passing proves the mechanism and doctor/nurse would pass identically (both in the
  same allowed list); the handoff also records a manual E2E where real doctor/nurse
  returned 200. Acceptable — noted for Test Agent to exercise a real doctor/nurse token.

## Checks run

- `git diff origin/dev...HEAD --unified=3` — 2 files, +49/-10, 1 commit `bfc27ff`; no unrelated changes.
- Cross-referenced `require_role`/`require_permission` impl (`app/core/permissions.py`) — both 403 via `ForbiddenError`, role check is `any()`-match, permission-scoped to active clinic.
- Verified `/start` & `/complete` reference gates (`app/modules/visits/api/routes.py`) match the chosen pattern exactly.
- Verified vitals gate (`vital.write`, permission-based) as the alternative analog — role-based chosen deliberately and justified.
- New test `test_receptionist_cannot_write_exam` inspected: asserts recept→403, DB `status='WAITING'` (no auto-start), GET→200/`null`, clinical actor→200. Meaningful, not coverage-padding.
- Manual lint spot-check: `ruff` host binary broken (`Exec format error` — Windows binary under bash), as handoff predicted. By inspection touched files are clean (import used, no unused vars, no commented-out code, comment justifies the gate). Handoff reports ruff 0 findings / mypy 0 new on touched files, 209/209 regression + 13/13 module tests passing.

## Acceptance Criteria
- [x] `POST /visits/{id}/exam` requires a clinical role → receptionist 403.
- [x] doctor/nurse/admin still write (no regression).
- [x] Integration RBAC test present (recept→403; clinical→200) + side-effect assertion.
