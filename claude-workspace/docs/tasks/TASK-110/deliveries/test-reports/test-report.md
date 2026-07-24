# Test Report: TASK-110 - Invoice numbering serialization (M-20)

**Test Agent:** Automation Tester
**Date:** 2026-07-24
**Status:** ✅ ALL PASSED

## Environment

- Isolated Docker stack `v110` (project `-p v110`), built from worktree
  `F:/MyProject/clinic-cms-workspace/_fix110-be`, branch
  `fix/TASK-110-invoice-number-serialize` @ `699c7aa`.
- Ports: api `9967`, postgres `5467`, redis `6449` (no collision with
  main/dev/w2e — those remained untouched throughout).
- Migrated `alembic upgrade head` → reached **`0068`** (single head,
  confirmed via `alembic heads`). Seeded superadmin
  (`scripts/seed_superadmin.py`).
- Stack torn down (`docker compose -p v110 -f docker-compose.fix110.yml down -v`)
  after the run.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Integration (`tests/integration/billing`) | 40 | 40 | 0 | 100% |
| **TOTAL** | **40** | **40** | **0** | **100%** |

Command: `pytest -q --tb=short tests/integration/billing`

## Key Assertions Verified

- ✅ **2-way concurrent submit → distinct numbers, both 200**:
  `TestConcurrentInvoiceNumbering::test_two_concurrent_submits_get_distinct_numbers`
  — PASSED.
- ✅ **5-way concurrent submit → all distinct, all 200, no 500**:
  `TestConcurrentInvoiceNumbering::test_five_concurrent_submits_all_distinct_and_successful`
  — PASSED.
- ✅ **Sequential submits → monotonic numbering**:
  `TestConcurrentInvoiceNumbering::test_sequential_submits_still_monotonic`
  — PASSED.
- ✅ **Concurrent payments total correctness** (adjacent regression check):
  `TestConcurrentPayments::test_concurrent_payments_total_correct` — PASSED.
- ✅ **Single alembic head at 0068**: `alembic heads` → `0068 (head)`.
- ✅ **Migration reversibility**: `alembic downgrade -1` (0068→0067) then
  `alembic upgrade head` (0067→0068) completed cleanly, restoring the
  MAX-scan function and re-applying the counter-table migration with no
  errors; final state confirmed back at single head `0068 (head)`.

## Coverage

- `tests/integration/billing/test_billing_e2e.py` (27 scenarios incl. the 3
  concurrency tests + concurrent-payments test) — full file green.
- `tests/integration/billing/test_billing_generate_from_visit.py` and
  `test_invoice_service.py` — no regression in invoice generation/service
  logic from the numbering-function swap.

## Failures

None. 0 new failures in the billing scope for this run.

## Next Steps

All tests passed successfully (40/40). Migration confirmed single-head at
0068 and cleanly reversible. Ready to proceed to Documentation phase.

**Task status → DOCUMENTING**

---

**Test Execution Time:** ~36 seconds (35.97s pytest run)
**Total Scenarios:** 40
**Environment:** isolated Docker stack `v110` (api 9967 / pg 5467 / redis 6449), torn down after run
