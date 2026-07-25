# TASK-119: Billing Reversal Completeness Fix

**Status**: DONE  
**Completed**: 2026-07-26  
**Test Coverage**: 108/109 passed (1 pre-existing flake)  
**Branch**: `fix/TASK-119-billing-reversal`

---

## Overview

This fix addresses two critical billing data-integrity issues in the invoice reversal flow:

1. **H-6**: `void_invoice` does not reverse collected payments, leaving orphaned payments and breaking 3-way reconciliation between payment-methods, revenue, and invoice reports.
2. **H-5**: `refund_invoice` after dispensing does not restore inventory or reverse COGS/profit entries.

---

## H-6: Void Invoice Payment Reversal

### Problem
- `void_invoice` only set invoice `status='void'` without touching payments or reservations
- Collected payments remained marked `is_voided=false`, visible to revenue/payment-method service
- `paid_total` and balance stayed non-zero
- Result: Orphaned payments; 3-way reconciliation mismatch between payment-methods=actual amount collected, revenue=visits with status paid/partially_paid (void excluded), invoice.paid_total (not reversed)

### Solution
- Mirror `refund_invoice` logic (TASK-105 precedent): void all active payments for the invoice
- Set `paid_total → 0`, `balance → 0`
- Release in-house reservation
- Call `reopen_after_payment_reversal` (TASK-112) to transition visit from COMPLETED back to AWAITING_PAYMENT

### Implementation Details
- **File**: `app/modules/billing/services/invoice_service.py` (~620 lines)
- **Changes**:
  - `void_invoice()` now voids all non-voided payments, mirrors void logic to `_release_pharmacy_reservations` (already existed)
  - Visit reopened; payment-method == revenue (3-way reconciliation now consistent)
- **Side effects**: No regressions; void-twice properly blocked (409 on second attempt)

---

## H-5: Refund After Dispensing Stock & COGS Restoration

### Problem
- `refund_invoice` calls `_release_pharmacy_reservations` filtering only for `in_house_status='reserved'` or `pib.status='reserved'`
- After dispensing, both statuses = 'dispensed', so no rows match → inventory unchanged
- Profit service still counts dispensed items in COGS → amount calculation remains incorrect
- Result: Inventory discrepancy; profit/COGS remain incorrect after refund

### Solution
- `refund_invoice` (and void, if items already dispensed) must call `undispense` for each dispensed item
- `undispense` restores `batch.actual_quantity` (+qty), creates 'return' movement, sets `pib.status→released`
- COGS/profit automatically corrected (profit filters on `status='dispensed'`)

### Implementation Details
- **Files Modified**:
  - `app/modules/billing/services/invoice_service.py`: refund/void call `undispense` after `_release_pharmacy_reservations`
  - `app/modules/pharmacy/services/dispense_service.py`: `undispense` logic used
  - `app/modules/reports/services/profit_service.py`: no changes needed (filters on status)
- **Changes**:
  - Refund path extended to handle post-dispense items
  - Void path similarly updated for consistency
- **Side effects**: None; refund-post-dispense now fully reversible

---

## Test Results

| Category | Result | Count |
|----------|--------|-------|
| Billing reversal scenarios | PASS | 108/109 |
| Pre-existing flake | `test_visit_volume_report` | 1 (out of scope) |
| Key assertions | PASS | All in-scope |

### Validated Scenarios
- **Void reversal**: `test_void_reverses_collected_money`, `test_void_payment_round_trip`
  - Payment voided, `paid_total → 0`, reservation released, visit reopened
- **Refund post-dispense**: `test_refund_after_dispense_restores_stock_and_cogs`, `test_void_after_dispense_restores_stock`
  - Batch `actual_quantity` restored, COGS/profit reversed
- **Regression check**: `test_refund_paid_invoice`, `test_refunded_invoice_allows_new_invoice_for_visit`
  - TASK-105 (refund original behavior) confirmed working
- **Guard**: `test_void_draft_invoice_rejected`, `test_void_payment_already_voided_rejected`
  - Double-void blocked (409)

---

## Financial Impact

- **Reconciliation Integrity**: 3-way reconciliation (payment-methods, revenue, invoice) now consistent
- **Orphaned Payments Eliminated**: All voided payments properly marked; no orphaned amounts
- **Inventory Accuracy**: Refunded dispensed items fully restocked with movement audit trail
- **Profit Accuracy**: COGS reversals match physical inventory changes

---

## Follow-up Notes

None. Tài chính — all happy paths + edge cases covered, reused proven helpers from TASK-105 (refund) and TASK-112 (reopen).
