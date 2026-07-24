# Test Report: TASK-108 - Visit-service guards (M-8 + M-9)

**Test Agent:** Automation Tester
**Date:** 2026-07-24
**Status:** ✅ ALL PASSED

## Environment

- Isolated Docker stack `v108` (project `-p v108`), built from worktree
  `F:/MyProject/clinic-cms-workspace/_fix108-be`, branch
  `fix/TASK-108-visit-service-guards` @ `54c31f1`.
- Ports: api `9969`, postgres `5469`, redis `6451` (no collision with
  main/dev/w2e stacks — those remained untouched throughout).
- Migrated `alembic upgrade head` → reached `0067` (matches expected head for
  this branch). Seeded superadmin (`scripts/seed_superadmin.py`).
- Stack torn down (`docker compose -p v108 -f docker-compose.fix108.yml down -v`)
  after the run.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Integration (`tests/integration/services`) | 17 | 17 | 0 | 100% |
| Integration (`tests/integration/visits`) | 72 | 72 | 0 | 100% |
| **TOTAL** | **89** | **89** | **0** | **100%** |

Command: `pytest -q --tb=short tests/integration/services tests/integration/visits`

## Key Assertions Verified

- ✅ **M-8**: `POST /visits/{unknown_id}/services` → `404` (not 500).
  Test: `test_add_service_to_unknown_visit_returns_404` — PASSED.
- ✅ **M-9**: adding a service to a visit with an active invoice
  (`issued`/`partially_paid`/`paid`) → `409`, invoice total left untouched;
  `recall` (issued→draft) then re-add → `201` with invoice auto-resync.
  Test: `test_add_service_to_visit_with_issued_invoice_blocked` — PASSED.
- ✅ Pre-invoice add (no invoice yet) → `201` (no regression) — covered by
  existing `test_services_e2e.py` happy-path cases — PASSED.
- ✅ Closed visit (CANCELLED) → `409` (no regression) —
  `test_invalid_state_transition_returns_409` — PASSED.
- Targeted re-run of the 3 M-8/M-9-relevant tests in isolation (`-k
  "unknown_visit or issued_invoice or closed"`) confirmed independently: all
  green.

## Coverage

- `tests/integration/services/test_services_e2e.py` (17 scenarios) — full
  file green, including both new tests added for this fix.
- `tests/integration/visits/*` (72 scenarios across lifecycle, negative,
  concurrency, RLS, edit-lock, history-filter, perf) — no regression from the
  `visit_service_service.add_to_visit` change.

## Failures

None. 0 new failures, 0 pre-existing flakes observed in this scope (the
known pre-existing DEK/RLS/merge/phone-search flakes documented for this
project live in `tests/integration/patients` / `tests/integration/billing`
merge paths, out of scope for this run).

## Next Steps

All tests passed successfully (89/89). Ready to proceed to Documentation
phase.

**Task status → DOCUMENTING**

---

**Test Execution Time:** ~2 minutes (118.84s pytest run)
**Total Scenarios:** 89
**Environment:** isolated Docker stack `v108` (api 9969 / pg 5469 / redis 6451), torn down after run
