# TASK-111 — Implementation → Review handoff

**Branch:** `fix/TASK-111-appt-cancel-visit-cascade` (base `origin/dev` @ 6d91053, alembic head 0068)
**Commit:** `90d4c2e` — pushed to `origin/fix/TASK-111-appt-cancel-visit-cascade`
**Worktree:** `F:/MyProject/clinic-cms-workspace/_fix111-be` (dedicated, left in place)

## Bug (M-2)

`cancel_appointment` (`app/modules/appointments/services/appointment_service.py`,
was lines 252-266) transitioned the appointment to `cancelled` but never
touched the Visit created at check-in. Result: cancel a checked-in
appointment → appointment shows `cancelled`, but its Visit stays `WAITING`
forever, orphaned in the queue (never served, never closed).

## Decision: cascade, not blanket block

Rule chosen: **cascade-cancel the linked visit** when it hasn't progressed
past a safe point; **block implicitly** (via the visit's own guard rails)
when it has.

Concretely, `cancel_appointment` now:
1. Runs the existing appointment state-machine check as before.
2. If `appointment.visit_id` is set, loads the Visit. If its status is not
   already `COMPLETED` or `CANCELLED`, calls
   `visit_service.transition_to_cancel(db, visit_id, clinic_id, reason=..., user_id=...)`.
3. Proceeds to set the appointment to `cancelled` only after that call
   succeeds (or was skipped because there was nothing to cascade).

`transition_to_cancel` is the pre-existing visit-cancel path
(`app/modules/visits/services/visit_service.py:493`) and already handles the
hard part: it's a documented "any non-COMPLETED state → CANCELLED" transition
(WAITING, IN_PROGRESS, AWAITING_PAYMENT all allowed per
`app/modules/visits/services/state_machine.py`), and it raises
`BusinessRuleError` (422) if money has been collected on an invoice or
medicines already dispensed — cascading prescription-cancel and invoice-void
for anything still open. So:

- Visit is `WAITING` or `IN_PROGRESS` with nothing collected/dispensed yet →
  cascaded cleanly to `CANCELLED`. No orphan.
- Visit already progressed to the point money/meds are committed → the visit
  cancel's own blocker fires, `BusinessRuleError` propagates out of
  `cancel_appointment`, and the appointment cancel is blocked too (409/422,
  same as today's error shape for that path).
- Visit already `COMPLETED` or `CANCELLED` → left untouched, appointment
  cancel proceeds normally (nothing to cascade).
- No linked visit (`appointment.visit_id is None`, e.g. cancel before
  check-in) → cascade block is skipped entirely; behavior unchanged from
  before this fix.

This was preferred over a hardcoded "block if IN_PROGRESS+" rule because the
visit module's own transition/blocker logic is the single source of truth for
"is it safe to cancel this visit" (it already accounts for billing and
pharmacy state, which a simple status check on the appointment side cannot
see).

## Files changed

- `app/modules/appointments/services/appointment_service.py` —
  `cancel_appointment`: cascades to `visit_service.transition_to_cancel` when
  a non-terminal linked visit exists; docstring documents the rule.
- `tests/integration/appointments/test_appointments_e2e.py` — new
  `TestCancelCascadesVisit` (3 tests, see below). No other files touched.

## Tests

Ran in isolated Docker stack `fix111` (compose file
`docker/docker-compose.fix111.yml`, **not committed** — untracked scratch
stack, same convention as prior fix branches, e.g.
`_fix110-be/docker/docker-compose.fix110.yml`). Ports: api 9965, postgres
5465, redis 6447 — distinct from shared dev stack (9999/5434/6380) and w2e
(5436/6382) per guardrails. Migrated to head (0068), ran tests, tore down
stack + volumes afterward (`docker compose -p fix111 down -v`).

New tests
(`tests/integration/appointments/test_appointments_e2e.py::TestCancelCascadesVisit`):

1. `test_cancel_checked_in_appointment_cascades_waiting_visit` — confirm →
   check-in (visit WAITING) → cancel appointment → appointment `cancelled`,
   visit re-fetched via `GET /api/v1/visits/{id}` is `CANCELLED`, not
   `WAITING`.
2. `test_cancel_checked_in_appointment_cascades_in_progress_visit` — same but
   visit started (`POST /visits/{id}/start` → `IN_PROGRESS`) before cancel;
   still cascades cleanly to `CANCELLED` (nothing billable/dispensed yet).
3. `test_cancel_appointment_without_visit_still_works` — regression: cancel
   an appointment that never checked in (`visit_id is None`) still returns
   200/`cancelled` — cascade is a no-op, existing behavior preserved.

Results:

- `tests/integration/appointments/test_appointments_e2e.py` — **17/17
  passed** (14 pre-existing + 3 new).
- `tests/integration/appointments/` + `tests/integration/visits/` (targeted
  sweep covering both sides of the cascade) — **89/89 passed**, no failures.
  (Full-repo sweep was intentionally not run for this task — targeted
  modules are sufficient signal and match the guardrail to keep isolated-stack
  runs scoped.)

## Static analysis

- `ruff check app/modules/appointments app/modules/visits` — clean, 0
  errors. `ruff check app tests` repo-wide reports 452 pre-existing baseline
  errors (same count noted in TASK-110's handoff off the same `origin/dev`
  base) — **0 new**, confirmed by scoping the check to the changed files
  only (also clean).
- `mypy app` — 50 pre-existing baseline errors (again, same count as
  TASK-110's baseline off `origin/dev`), none in
  `app/modules/appointments/services/appointment_service.py` or any file
  touched by this fix — **0 new**. `mypy app/modules/appointments` shows only
  the pre-existing, unrelated `routes.py:131` error (Patient/User Sequence
  mismatch, not touched by this change).

## Status

`docs/tasks/TASK-111/task.md` → `IN_REVIEW`, assigned Code Review Agent,
updated 2026-07-25.
