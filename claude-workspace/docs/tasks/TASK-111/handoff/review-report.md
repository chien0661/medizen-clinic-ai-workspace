# TASK-111 — Code Review Report

**Reviewer:** Code Review Agent
**Date:** 2026-07-25
**Branch:** `fix/TASK-111-appt-cancel-visit-cascade` (base `origin/dev` @ `6d91053`)
**Diff:** `git -C F:/MyProject/clinic-cms-workspace/_fix111-be diff origin/dev...HEAD`
**Decision: APPROVED → IN_TESTING**

## Scope

Cancelling a checked-in appointment left an orphan `WAITING` visit in the queue
(M-2). Fix: `cancel_appointment` now cascade-cancels the linked visit via the
existing `visit_service.transition_to_cancel` for any non-COMPLETED/CANCELLED
visit. Two files: `app/modules/appointments/services/appointment_service.py`
(logic + docstring), `tests/integration/appointments/test_appointments_e2e.py`
(3 new tests). No other files touched.

## Verification

### Cascade behavior — CORRECT
- `appointment_service.py:276-277` — appointment transition guard
  (`assert_can_transition`) runs **first**, so a visit is never cascade-cancelled
  for an appointment that itself can't be cancelled. Good ordering.
- `:279-293` — cascade only when `visit_id is not None` and visit status is not
  in `(COMPLETED, CANCELLED)`. Matches AC: WAITING/IN_PROGRESS → cancelled (no
  orphan); COMPLETED/CANCELLED left untouched; no-visit → no-op.
- `VisitStatus` is properly imported (`appointment_service.py:17`). Inline import
  of `visit_service` avoids a circular dependency — consistent with the pattern
  already used in `transition_to_cancel` itself.
- Visit state machine (`visits/services/state_machine.py`) confirms WAITING,
  IN_PROGRESS, AWAITING_PAYMENT all allow → CANCELLED, so the cascade never
  hits an illegal-transition 409 for an in-flight visit.

### Cascade + guard coupling — CORRECT, acceptable UX
- Reusing `transition_to_cancel`'s guard rails is the right call: that function
  is the single source of truth for "is it safe to cancel this visit," and it
  alone sees billing (paid invoices) and pharmacy (dispensed meds) state that a
  status check on the appointment side cannot. Money collected / meds dispensed
  → `BusinessRuleError` (422), which propagates cleanly out of
  `cancel_appointment` (no try/except swallows it) and blocks the appointment
  cancel. This is the desired "block when unsafe" behavior — no silent orphan,
  no partial cancel.
- The reason is threaded through as `f"Hủy theo lịch hẹn: {cancel_reason}"` —
  the visit's cancel_reason records that it was cancelled via the appointment.

### Atomicity — CORRECT
- Single session per request (`get_db`, `app/core/db.py:112-129`): the service
  uses `db.flush()` only (both the cascade and the appointment update); the
  route dependency commits once at the end and rolls back on any exception.
  If `transition_to_cancel` raises, the whole transaction rolls back — appointment
  stays uncancelled, visit untouched. Both-or-neither guaranteed.

### Tests — genuine
- `TestCancelCascadesVisit` (3 tests): (1) WAITING visit — asserts visit
  re-fetched via `GET /visits/{id}` is `CANCELLED` not `WAITING` (the core
  regression, with explanatory message); (2) IN_PROGRESS visit cascades to
  CANCELLED; (3) no-visit appointment still cancels (regression). Assertions are
  real, not coverage padding.
- Scope: only one caller of `cancel_appointment` exists app-wide (the route); no
  scheduler/background job invokes it, so the cascade is well-contained.

### Static analysis
- Host tooling is broken (`ruff` → "cannot execute binary file: Exec format
  error"), as the task anticipated — could not independently re-run. Handoff
  reports 0 new ruff/mypy findings on changed files (452/50 pre-existing baseline,
  same as TASK-110 off the same base). Diff is visually clean: no lint smells,
  reasonable line lengths, docstring documents the decision. Accepting the
  handoff's claim with this note.

## Findings

**CRITICAL:** none.
**MAJOR:** none.

**MINOR:**
1. UX wording — when the block fires, the 422 message is "Chưa thể hủy lượt khám:
   Đã thu tiền…" (mentions *lượt khám*/visit) even though the user cancelled an
   *appointment*. Informative and points to the correct remediation, but the
   noun mismatch is slightly surprising. Acceptable; flag for the frontend/UX to
   consider surfacing an appointment-framed message if it matters.
2. Test coverage gap — no integration test exercises the block path (visit with
   money collected / meds dispensed → appointment cancel 422). That path is
   covered by the visits module's own `transition_to_cancel` tests, so the
   coupling's blocking behavior is tested at the unit it lives in; a
   cross-module assertion via the appointment endpoint would be nice-to-have.
   Not blocking.

## Quality Gates
- [x] No critical or major issues
- [x] Cascade logic correct (guard-first ordering, terminal-state skip, no-op on no visit)
- [x] Atomic (single session, flush + single commit, rollback on raise)
- [x] Tests meaningful and assert the regression
- [ ] Lint/type re-run — host tooling broken; relying on handoff (0 new) + manual read
- [x] No security concerns (no secrets, no injection; permission dep `appointment.cancel` unchanged)
- SonarQube: not configured — skipped. Playwright: no frontend changes — skipped.
