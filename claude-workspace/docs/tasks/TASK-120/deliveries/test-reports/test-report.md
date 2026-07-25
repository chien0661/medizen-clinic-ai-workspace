# Test Report: TASK-120 — Prescription mutation guards (H-1 pending, H-4 invoice-issued)

**Date**: 2026-07-26
**Tester**: Test Agent
**Branch**: `fix/TASK-120-prescription-guards` @ `7b67cf4` (base `origin/dev` @ `c24f5fe`, migrations to `0069`)
**Worktree**: `_fix120-be` (isolated stack `y120`: api :9947, postgres :5447, redis :6429)

## Summary

| Metric | Value |
|---|---|
| Total collected (prescriptions + billing) | 79 |
| Passed | 79 |
| Failed | 0 |
| New failures (regressions from this fix) | 0 |

Command: `pytest -q --tb=short tests/integration/prescriptions tests/integration/billing`

## Result

```
79 passed, 105 warnings in 65.93s
```

## Acceptance Criteria Validation

| # | Criterion | Test(s) | Result |
|---|---|---|---|
| 1 | Mutate `pending` prescription (PATCH header/item, add item) → 409 | `test_prescription_mutation_guards.py::TestH1PendingMutationGuard::test_patch_prescription_header_on_pending_409`, `test_patch_prescription_item_on_pending_409`, `test_add_item_on_pending_409`, `test_delete_item_on_pending_409` | PASS |
| 2 | Edit prescription-item qty when invoice issued → 409 (no silent under/over-bill) | `TestH4InvoiceIssuedGuard::test_update_item_qty_after_invoice_issued_409`, `test_add_item_after_invoice_issued_409` | PASS |
| 3 | Draft (no issued invoice) still editable → 200 | `TestH4InvoiceIssuedGuard::test_update_item_qty_with_draft_invoice_still_200`, `TestDraftStillEditable::test_draft_prescription_fully_editable` | PASS |

No regressions in the full `tests/integration/billing` suite (invoice issuance, void/refund, payment reversal — all pass alongside the new guards).

## Environment

- Isolated Docker Compose stack `y120` (project name), built from `_fix120-be` worktree, `Dockerfile` context.
- Postgres 15-alpine, Redis 7-alpine, api container (`tail -f /dev/null`, tests run via `docker compose exec`).
- Migrated `alembic upgrade head` → `0069_stock_status_view_low_stock_fields`. Superadmin seeded via `scripts/seed_superadmin.py`.
- Stack torn down (`docker compose down -v`) after test run. No shared/main/dev/w2e stacks touched.

## Conclusion

All in-scope prescription-guard and billing-regression assertions PASS (79/79). **Task TASK-120 → DOCUMENTING.**
