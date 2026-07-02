# Test Report: TASK-083 - Cấu hình giá thuốc + báo cáo tồn kho + xem giá trị tiền tồn kho

**Test Agent:** Automation Tester
**Date:** 2026-07-03
**Branch:** `feature/TASK-084-exam-templates` (shared by TASK-082/083/084)
**Commits tested:** BE `clinic-cms@6c17fb8` + 3 new tests added this pass, FE `clinic-cms-web@a6cfb06` (no FE changes needed)
**Status:** ✅ ALL PASSED

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| BE integration/e2e (`-k "medicine or inventory or valuation or report"`) | 147 | 147 | 0 | 100% |
| — of which: new valuation e2e (`test_inventory_valuation_e2e.py`) | 16 | 16 | 0 | 100% |
| FE unit/component (`npm test`, full suite) | 1051 | 1051 | 0 | 100% |
| **TOTAL** | **1198** | **1198** | **0** | **100%** |

Additional gates: `ruff check` (touched test file) clean; FE `npm run type-check` clean; `alembic heads` → single head `0047_add_medicine_price`.

## Gap analysis vs. Implementation/Review hand-off

The Implementation and Review agents reported 13 BE valuation e2e tests covering cost-basis math,
missing-cost fallback, exclusions, export, tenant isolation, and unauthenticated-401. Re-reading the
task's acceptance criteria and the Review agent's "Focus Areas for Testing" note against that test file
found 3 uncovered scenarios, closed in this pass (all real-DB, no mocks):

1. **`test_valuation_forbidden_without_financial_permission`** — AC6 says the `report.financial` gate
   must 403 a user who lacks it. The existing test only checked *unauthenticated* (401/403). Added a
   `nurse` role user (has `report.view`, confirmed **not** `report.financial` via DB query) and asserted
   403 on both `GET /reports/inventory-valuation` and `/export`.
2. **`test_valuation_decreases_after_stock_adjustment`** — AC3 requires the total to "update correctly
   after price change / purchase-in / **dispense**". Purchase-in-increase was tested; the dispense/decrease
   direction was not. Added a test that purchase-in's 20 units then calls the real
   `POST /inventory/adjustments` endpoint (creates an actual `StockMovement`, same mechanism dispense uses
   to reduce `batch.actual_quantity`) down to 12, and asserts `available_qty`/`cost_value` both drop
   proportionally (20000 → 12000).
3. **`test_valuation_export_neutralizes_formula_injection`** — AC4 explicitly requires "no
   formula-injection". The existing export test only checked the response content-type, not that a
   malicious medicine name is actually neutralized. Added a medicine named `=SUM(A1:A10)`, exported the
   XLSX, loaded it with `openpyxl`, and asserted the cell value is `'=SUM(A1:A10)` (leading apostrophe)
   and the raw un-neutralized string is never present — proves `app/core/excel.py::_neutralize` is
   actually wired into this endpoint, not just present in the shared helper.

All 3 new tests pass against the current implementation with no code changes required — the
implementation was already correct; these tests close verification gaps, not code bugs.

## Acceptance Criteria Coverage

| # | Acceptance Criterion | Verification | Result |
|---|---|---|---|
| 1 | User with `medicine.manage` configures per-medicine price (sale_price); persists and reflected in inventory calc | `test_medicine_create_and_update_sale_price`, `test_medicine_sale_price_optional`, `test_valuation_sale_price_change_reflected_immediately` | ✅ PASS |
| 2 | Inventory report shows correct on-hand qty per medicine, reconciled vs batch/StockMovement | `test_valuation_cost_basis_matches_purchase_in`, `test_valuation_increases_after_additional_purchase_in`, `test_valuation_decreases_after_stock_adjustment` (new) | ✅ PASS |
| 3 | Total money value = Σ(unit_cost × qty), correct & updates after price change / purchase-in / dispense; retail NOT counted in cost total | `test_valuation_cost_basis_matches_purchase_in`, `test_valuation_increases_after_additional_purchase_in`, `test_valuation_decreases_after_stock_adjustment` (new), `test_valuation_sale_price_change_reflected_immediately` (proves `cost_value` unaffected by `sale_price` change) | ✅ PASS |
| 4 | Excel export works, no formula-injection | `test_valuation_export_returns_xlsx`, `test_valuation_export_neutralizes_formula_injection` (new, actually decodes the XLSX and checks neutralization) | ✅ PASS |
| 5 | Missing `unit_cost` lots → fallback to `default_cost_price`, else flagged `has_missing_cost` | `test_valuation_missing_unit_cost_flagged`, `test_valuation_default_cost_price_fallback` | ✅ PASS |
| 6 | RLS: valuation + price per-clinic; `report.financial` gate 403 without it | `test_valuation_tenant_isolation`, `test_valuation_requires_authentication`, `test_valuation_forbidden_without_financial_permission` (new — authenticated `nurse` role, has `report.view` but not `report.financial`, gets 403 on report + export) | ✅ PASS |
| — | Recalled/expired batch exclusion (Review focus area) | `test_valuation_recalled_batch_excluded`, `test_valuation_expired_batch_excluded` | ✅ PASS |
| — | Migration additive/single-head | `docker exec clinic_cms_w2e_api alembic heads` → `0047_add_medicine_price (head)` | ✅ PASS |
| — | FE: price field integers, blank not coerced to 0, total card = cost not retail, i18n vi/en | `MedicinesPage.price.test.tsx` (4), `InventoryValuationReportPage.test.tsx` (4), `ReportsHubPage.test.tsx` (7th tab) — all in `npm test` full run | ✅ PASS |

## Coverage

### API Endpoints
- ✅ `POST/PATCH /api/v1/medicines` (`sale_price`/`default_cost_price`) — 2 scenarios
- ✅ `GET /api/v1/reports/inventory-valuation` — 12 scenarios (math, exclusions, permission, tenancy)
- ✅ `GET /api/v1/reports/inventory-valuation/export` — 2 scenarios (content-type, formula-injection)

**Coverage:** 100% of new/changed endpoints.

### Database Operations
- ✅ Migration `0047_add_medicine_price` applied cleanly, single head, chains off `0046`.
- ✅ Cost-basis SQL aggregate reconciled against `batch`/`StockMovement`-driven quantity changes (purchase-in increase, adjustment/dispense decrease).
- ✅ RLS/tenant isolation confirmed (clinic B never sees clinic A's medicine/stock/totals).

## Test Files Modified

### Integration/E2E (Backend, real Postgres + Redis)
- `clinic-cms/tests/integration/reports/test_inventory_valuation_e2e.py` — 13 pre-existing + **3 new**:
  - `test_valuation_decreases_after_stock_adjustment`
  - `test_valuation_export_neutralizes_formula_injection`
  - `test_valuation_forbidden_without_financial_permission`

No FE test changes were needed — the 8 new FE tests from the implementation pass already cover the
price-field and report-page UI behavior called out in the plan.

## Pre-existing / Out-of-scope Debt (not gated, verified pre-existing)

- 30 `ruff B008` (Depends-in-default) findings in `app/modules/inventory/api/routes.py` — pre-existing pattern used throughout the module (all inventory routes use this FastAPI idiom), not introduced by TASK-083, not touched by this task's diff.
- 17 FE lint errors in unrelated files (`VitalsPage.tsx`, `VssIntegrationConfigPage.tsx`, `VssSyncLogPage.tsx`, `ExpensesPage.tsx`) — not in TASK-083's diff.
- 7 teardown FK errors (`notification → clinic`) reported on the shared branch DB by a concurrent test run — not observed in this pass's isolated `-k` run; unrelated to inventory/reports tables (disjoint from TASK-082 RBAC test agent running concurrently on the same containers).

## UI E2E — Deferred

Per instructions, interactive Playwright UI E2E was **not** run standalone for this task. A consolidated
UI E2E pass covering TASK-082/083/084 (all sharing branch `feature/TASK-084-exam-templates`) runs
separately at the end of that combined effort. This report's criteria coverage is via real-DB BE
integration/e2e tests + FE component/unit tests, per the assignment's explicit instruction.

## Next Steps

All tests passed successfully (1198/1198, 100%). Acceptance criteria fully covered including the 3 gaps
closed in this pass. Ready to proceed to Documentation phase.

**docs/tasks/dashboard.md status → DOCUMENTING**

---

**Test Execution Time:** ~4 minutes (BE ~2 min incl. new tests, FE ~35s, type-check/lint/migration checks ~1 min)
**Total Scenarios:** 1198 (147 BE + 1051 FE)
**New Scenarios Added This Pass:** 3 (BE)
**Environment:** Docker (`clinic_cms_w2e_api` / `clinic_cms_w2e_postgres` / `clinic_cms_w2e_redis`), DB at migration head `0047`
