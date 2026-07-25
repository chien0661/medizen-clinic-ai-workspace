# Test Report: TASK-119 — Complete billing reversal (H-5 refund→stock/COGS, H-6 void→payment)

**Date**: 2026-07-26
**Tester**: Test Agent
**Branch**: `fix/TASK-119-billing-reversal` @ `f6bbe89` (base `origin/dev` @ `c24f5fe`, migrations to `0069`)
**Worktree**: `_fix119-be` (isolated stack `y119`: api :9948, postgres :5448, redis :6430)

## Summary

| Metric | Value |
|---|---|
| Total collected (billing + reports + pharmacy) | 109 |
| Passed | 108 |
| Failed | 1 |
| New failures (regressions from this fix) | 0 |

Command: `pytest -q --tb=short tests/integration/billing tests/integration/reports tests/integration/pharmacy`

## Result

```
FAILED tests/integration/reports/test_reports_e2e.py::test_visit_volume_report
1 failed, 108 passed, 117 warnings in 94.09s
```

`test_visit_volume_report` fails with `assert 0 >= 1 / where 0 = len([])` (no completed-visit rows returned for the report window). This is the pre-existing `visit_volume` flake called out as acceptable in the test scope (unrelated to billing/pharmacy reversal code touched by this branch — no billing/pharmacy/reports-reversal test failed). Treated as a known, out-of-scope flake, not a regression.

## Acceptance Criteria Validation

| # | Criterion | Test(s) | Result |
|---|---|---|---|
| 1 | Void invoice w/ payment → payment voided, paid_total→0, payment-methods==revenue (3-way reconcile), reservation released, visit reopened | `test_billing_e2e.py::TestVoidInvoice::test_void_reverses_collected_money`, `test_void_issued_invoice`, `test_payment_reversal_unlocks_visit.py::TestVoidPaymentUnlocksCompletedVisit::test_void_payment_round_trip` | PASS |
| 2 | Refund/void after dispense → `batch.actual_quantity` restored + COGS/profit reversed + prescription no longer stuck 'dispensed' | `test_billing_reversal_stock.py::TestRefundAfterDispenseRestoresStock::test_refund_after_dispense_restores_stock_and_cogs`, `TestVoidAfterDispenseRestoresStock::test_void_after_dispense_restores_stock` | PASS |
| 3 | No TASK-105 refund-path regression | `test_billing_e2e.py::TestRefundInvoice::test_refund_paid_invoice`, `test_refund_reverses_collected_money`, `test_refund_unpaid_invoice_rejected`; `test_invoice_service.py::TestCreateFromVisitAfterRefund::test_refunded_invoice_allows_new_invoice_for_visit` | PASS |
| 4 | Double-void → 400 | `test_billing_e2e.py::TestVoidInvoice::test_void_draft_invoice_rejected`; `test_invoice_service.py::TestPaymentEndpoints::test_void_payment_already_voided_rejected` | PASS |

## Coverage

- `tests/integration/billing/` — all files (test_billing_e2e, test_billing_generate_from_visit, test_billing_reversal_stock, test_invoice_service, test_payment_reversal_unlocks_visit): PASS
- `tests/integration/reports/` — test_ar_aging_e2e, test_inventory_valuation_e2e: PASS; test_reports_e2e: 1 pre-existing flake (test_visit_volume_report), unrelated to this fix
- `tests/integration/pharmacy/` — test_pending_dispense_enrichment, test_pharmacy_e2e: PASS

## Environment

- Isolated Docker Compose stack `y119` (project name), built from `_fix119-be` worktree, `Dockerfile` context.
- Postgres 15-alpine, Redis 7-alpine, api container (`tail -f /dev/null`, tests run via `docker compose exec`).
- Migrated `alembic upgrade head` → `0069_stock_status_view_low_stock_fields`. Superadmin seeded via `scripts/seed_superadmin.py`.
- Stack torn down (`docker compose down -v`) after test run. No shared/main/dev/w2e stacks touched.

## Conclusion

All in-scope billing/pharmacy/reversal-report assertions PASS. The single failure (`test_visit_volume_report`) is a known pre-existing flake explicitly out of scope for this task. **Task TASK-119 → DOCUMENTING.**
