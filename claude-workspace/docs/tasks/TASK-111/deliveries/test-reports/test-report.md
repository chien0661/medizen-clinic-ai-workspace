# Test Report: TASK-111 - appointment cancel cascades to visit (M-2)

**Test Agent:** Automation Tester
**Date:** 2026-07-25
**Status:** ALL IN-SCOPE PASSED

## Environment

- Isolated Docker stack `w111` (project `-p w111`), built from worktree
  `F:/MyProject/clinic-cms-workspace/_fix111-be`, branch
  `fix/TASK-111-appt-cancel-visit-cascade` @ `90d4c2e`.
- Ports: api `9962`, postgres `5462`, redis `6444` (adjusted the worktree's
  scaffolded `docker/docker-compose.fix111.yml` to these values — infra file
  only, no source touched). No collision with main/dev/w2e (9999/5434/5436/
  6380/6382), which remained untouched throughout.
- Migrated `alembic upgrade head` -> reached `0068`. Seeded superadmin
  (`scripts/seed_superadmin.py`).
- Stack torn down (`docker compose -p w111 -f docker-compose.fix111.yml down -v`)
  after the run.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Integration (`tests/integration/appointments` + `tests/integration/visits`) | 89 | 89 | 0 | 100% |

Command: `pytest -q --tb=short tests/integration/appointments tests/integration/visits`

## Key Assertions Verified

- **Check-in -> cancel appt -> visit CANCELLED (not orphan WAITING)** —
  `TestCancelCascadesVisit::test_cancel_checked_in_appointment_cascades_waiting_visit`
  — PASSED. Visit confirmed WAITING before cancel, CANCELLED after.
- **IN_PROGRESS visit also cascaded** —
  `TestCancelCascadesVisit::test_cancel_checked_in_appointment_cascades_in_progress_visit`
  — PASSED.
- **No-visit appointment cancel still works (regression, no-op cascade)** —
  `TestCancelCascadesVisit::test_cancel_appointment_without_visit_still_works`
  — PASSED.
- **Visit with collected money / dispensed medicine blocks the cascade
  (and therefore the appointment cancel)** — no existing integration test
  exercises this exact HTTP path (pre-existing gap, not introduced by this
  fix), so verified by code inspection instead:
  `visit_service.transition_to_cancel` (visit_service.py:493-555) raises
  `BusinessRuleError` when `any(invoice.paid_total > 0 ...)` or
  `any(rx.status == "dispensed" ...)`; `appointment_service.cancel_appointment`
  (appointment_service.py:249-292) calls `transition_to_cancel` with no
  try/except, so the exception propagates unmodified through the
  `/appointments/{id}/cancel` route. Confirmed via `app/core/exceptions.py`
  that `BusinessRuleError` maps to **HTTP 400**, not 422 (its `http_status`
  defaults to 400 for `BUSINESS_RULE_VIOLATION`; no route-level override
  exists for the cancel endpoint). **Note:** the task brief expected 422;
  actual is 400. This is the same pre-existing app-wide convention for every
  other `BusinessRuleError` use in the codebase (confirmed by grep across
  `app/core/exceptions.py` and existing call sites) — not a regression
  introduced by TASK-111, since `transition_to_cancel`'s guard logic itself
  predates this task and TASK-111 only added the cascade call into it. Net
  effect (blocked cancel with a 4xx client error) is correct; only the exact
  status code differs from the brief's assumption.

## Failures

None. 89/89 passed, no baseline flakes encountered in this subset.

## Next Steps

All in-scope tests passed (89/89). Ready to proceed to Documentation phase.

**Task status -> DOCUMENTING**

---

**Total Scenarios:** 89
**Environment:** isolated Docker stack `w111` (api 9962 / pg 5462 / redis 6444), torn down after run
