# TASK-020: Test Report

**Date**: 2026-04-27  
**Branch**: `feature/task-020-fe-pharmacy`  
**Test Runner**: Vitest 2.1.9  

---

## Summary

| Metric | Result |
|--------|--------|
| Total test files | 28 (5 new for pharmacy) |
| Total tests | 282 (55 new for pharmacy) |
| Passed | 282 |
| Failed | 0 |
| TypeScript check | CLEAN (0 errors) |
| ESLint | CLEAN (0 warnings/errors) |

---

## Pharmacy Test Files

### `src/tests/pharmacy/helpers.test.ts` — 27 tests PASS

Unit tests for pure helpers:
- `isExpiringSoon`: 6 tests (including 90-day threshold AC)
- `isExpired`: 3 tests
- `formatQty`: 5 tests
- `formatDate`: 2 tests
- `getStockStatus`: 6 tests (recalled > expired > expiring_soon > low_stock > ok priority)
- `stockStatusBadgeClass`: 5 tests

### `src/tests/pharmacy/PendingDispensePage.test.tsx` — 7 tests PASS

- Renders page title and beta banner
- Shows empty state when no pending items
- Renders pending items with patient name and prescription number
- Shows "Cấp phát" button for user with `pharmacy.dispense` permission
- Opens dispense modal when button is clicked
- Calls `dispensePrescription` on confirm
- Data-testid present

### `src/tests/pharmacy/InventoryPage.test.tsx` — 7 tests PASS

- Renders page title and data-testid
- Shows empty state when no items
- Renders stock items with medicine name and code
- Filters by search term (client-side)
- AC: expiring_soon filter shows item with 30-day expiry (uses 90-day threshold)
- Opens batch drawer when row is clicked
- Renders all 5 filter buttons

### `src/tests/pharmacy/AdjustmentsPage.test.tsx` — 4 tests PASS

- Renders page title and form with data-testid
- AC: user without `inventory.adjust` sees "no permission" message and no submit button
- Renders adjustment form fields for user with permission
- Shows adjustment history section

### `src/tests/pharmacy/i18n-pharmacy.test.ts` — 7 tests PASS

- vi and en have the same number of keys (52 leaf keys each)
- vi and en have identical key paths
- All vi values are non-empty strings
- All en values are non-empty strings
- nav section has all 5 pharmacy routes
- dispenseModal.source has in_house and external
- inventory.status has all 5 status values

---

## Regression — All Pre-Existing Tests Still Pass

All 227 pre-existing tests continue to pass. No regressions.
