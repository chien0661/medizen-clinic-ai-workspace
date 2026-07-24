# Test Report: TASK-112 - reopen COMPLETED visit on payment reversal (M-5)

**Test Agent:** Automation Tester
**Date:** 2026-07-25
**Status:** ALL IN-SCOPE PASSED

## Environment

- Isolated Docker stack `w112` (project `-p w112`), built from worktree
  `F:/MyProject/clinic-cms-workspace/_fix112-be`, branch
  `fix/TASK-112-unlock-visit-on-reversal` @ `c27b860`.
- Ports: api `9961`, postgres `5461`, redis `6443` (adjusted the worktree's
  scaffolded `docker/docker-compose.fix112.yml` to these values — infra file
  only, no source touched). No collision with main/dev/w2e.
- Migrated `alembic upgrade head` -> reached `0068`. Seeded superadmin.
- Stack torn down (`docker compose -p w112 -f docker-compose.fix112.yml down -v`)
  after the run.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Integration (`tests/integration/billing` + `tests/integration/visits`) + Unit (`tests/unit/visits`) | 178 | 178 | 0 | 100% |

Command: `pytest -q --tb=short tests/integration/billing tests/integration/visits tests/unit/visits`

## Key Assertions Verified

- **Round-trip: complete (paid) -> void payment -> AWAITING_PAYMENT + PATCH 200
  -> re-pay -> COMPLETED** —
  `TestVoidPaymentUnlocksCompletedVisit::test_void_payment_round_trip`
  (`tests/integration/billing/test_payment_reversal_unlocks_visit.py:263`) —
  PASSED. Verified: paid visit locked (PATCH 409) -> `void_payment` reverts
  visit to `AWAITING_PAYMENT` -> PATCH now 200 and persists -> re-adding
  payment auto-completes the visit again.
- **No-op when still fully paid** —
  `test_void_payment_no_op_when_still_fully_paid` — PASSED.
- **Recall variant reopens visit** —
  `TestRecallUnlocksCompletedVisit::test_recall_zero_total_invoice_unlocks_visit`
  — PASSED.
- **Refund variant reopens visit** —
  `TestRefundUnlocksCompletedVisit::test_refund_invoice_unlocks_visit` —
  PASSED.
- **Regression: `/visits/{id}/complete` on already-COMPLETED still 409**
  (shared `ALLOWED_TRANSITIONS` table not loosened) —
  `test_completed_visit_cannot_revert`
  (`tests/integration/visits/test_visits_lifecycle.py:416-457`) — PASSED.
  Explicitly asserts COMPLETED->start, COMPLETED->complete, COMPLETED->cancel
  all still return 409 for a visit that reached COMPLETED via the normal
  (non-reopened) path. Confirms the new COMPLETED->AWAITING_PAYMENT reopen
  transition is a separate, self-guarded path (only triggered by payment
  reversal service logic, not exposed as a generic transition) and does not
  loosen the general state machine.

## Failures

None. 178/178 passed, no baseline flakes encountered in this subset.

## Next Steps

All in-scope tests passed (178/178). Ready to proceed to Documentation phase.

**Task status -> DOCUMENTING**

---

**Total Scenarios:** 178
**Environment:** isolated Docker stack `w112` (api 9961 / pg 5461 / redis 6443), torn down after run
