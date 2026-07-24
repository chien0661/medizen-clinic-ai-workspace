# TASK-112: Reopen Visit on Payment Reversal Fix

**Status:** DONE  
**Severity:** Medium (M-5, E2E finding TASK-095)  
**Affected Systems:** Visits, Billing (Payment, Invoice)  
**Repos:** clinic-cms  

---

## Bug Summary

Voiding/recalling/refunding a payment on a COMPLETED visit left the visit in COMPLETED state (locked), even though the invoice was no longer fully paid. This broke the "cancel invoice → edit" workflow: users could not re-edit visit content (PATCH exam/vitals returned 409) until payment was restored.

**Repro:**
1. Complete visit → visit COMPLETED, invoice PAID
2. Void the payment → invoice unpaid, but visit still COMPLETED
3. PATCH exam/vitals → HTTP 409 (COMPLETED is locked per `visit_service.CLOSED_STATUSES`)
4. Stuck: cannot re-edit until payment restored manually

---

## Root Cause

The Visit state machine had no path from COMPLETED back to an editable state (AWAITING_PAYMENT). Payment reversal operations (void, recall, refund) did not communicate the financial change to the Visit module.

---

## Fix Design

**Add a targeted reopen helper that bridges billing and visit state.**

New function: `visit_completion_service.reopen_after_payment_reversal(db, clinic_id, visit_id, updated_by: str)`

- Fetches the Visit `FOR UPDATE` (row lock)
- No-ops if Visit is not currently COMPLETED or not found
- If COMPLETED → sets to AWAITING_PAYMENT, flushes
- Returns `True` if actual reopen occurred, `False` otherwise

**Critical design choice:** Does NOT go through the shared `state_machine.ALLOWED_TRANSITIONS` table (which keeps `COMPLETED` terminal for doctor operations). Instead, checks the COMPLETED precondition directly inside the reopen helper. This prevents accidentally loosening the `transition_to_complete` path (the doctor's normal "finish exam" operation).

**Wiring (which payment ops trigger reopen):**

| Operation | Trigger Condition | File |
|-----------|-------------------|------|
| `void_payment` | `invoice.visit_id is not None && invoice.status != "paid"` (after recalc) | `billing/services/payment_service.py` |
| `recall_invoice` | `invoice.visit_id is not None` (always, recall is a full reversal) | `billing/services/invoice_service.py` |
| `refund_invoice` | `invoice.visit_id is not None` (always, refund is a full reversal) | `billing/services/invoice_service.py` |

**Round-trip:**
1. COMPLETED → (void payment) → AWAITING_PAYMENT
2. AWAITING_PAYMENT → (edit content) → still AWAITING_PAYMENT
3. AWAITING_PAYMENT → (re-pay in full) → auto-complete → COMPLETED again

---

## Changes

### Backend (clinic-cms)

**Branch:** `fix/TASK-112-unlock-visit-on-reversal` (base `origin/dev` @ 6d91053, alembic head 0068)  
**Commit:** `c27b860`

#### New Files

- `app/modules/visits/services/visit_completion_service.py`
  - New function: `reopen_after_payment_reversal(db, clinic_id, visit_id, updated_by)`

#### Modified Files

- `app/modules/billing/services/payment_service.py`
  - `void_payment()`: Added call to `reopen_after_payment_reversal()` after recalculation if invoice is no longer fully paid
  
- `app/modules/billing/services/invoice_service.py`
  - `recall()`: Added call to `reopen_after_payment_reversal()`
  - `refund_invoice()`: Added call to `reopen_after_payment_reversal()`

- `app/modules/visits/services/state_machine.py`
  - Docstring/comment clarification: explains why `COMPLETED` remains terminal in shared transition table, where COMPLETED→AWAITING_PAYMENT unlock actually lives

- `tests/unit/visits/test_state_machine.py`
  - Comment update in `test_completed_is_terminal` explaining the design choice

#### Tests Added

- `tests/integration/billing/test_payment_reversal_unlocks_visit.py` (4 tests):
  1. `test_void_payment_round_trip` — COMPLETED → void → AWAITING_PAYMENT → edit → re-pay → COMPLETED
  2. `test_void_payment_no_op_when_still_fully_paid` — edge case: multiple payments, voiding one still leaves covered
  3. `test_recall_zero_total_invoice_unlocks_visit` — edge case: zero-total invoice can coexist with COMPLETED
  4. `test_refund_invoice_unlocks_visit` — refund paid invoice on COMPLETED → AWAITING_PAYMENT

**No migration needed:** VisitStatus.AWAITING_PAYMENT enum value already exists.

---

## Testing

**Environment:** Isolated Docker stack `fix112` (api 9964, postgres 5464, redis 6446)  
**Migration head:** 0068  
**Test results:** ✅ 178/178 passed

- New tests: 4/4 passed (`test_payment_reversal_unlocks_visit.py`)
- Regression sweep: 195 total passed (178 + 17 pharmacy) across `billing/`, `visits/`, `unit/visits/`, `pharmacy/`
  - Critical regression: `test_visits_lifecycle.py::test_completed_visit_cannot_revert` still passes (COMPLETED→complete is still blocked)

**Code quality:**
- `ruff check` on changed files → clean, no new errors (baseline: 452 pre-existing, unchanged)
- `mypy app` → no new errors (baseline: 50 pre-existing, unchanged)

---

## API Behavior

### POST /api/v1/payments/{payment_id}/void

**New side effect:**
- If the voided payment makes the linked invoice no longer fully paid:
  - Linked Visit (if COMPLETED) → reopens to AWAITING_PAYMENT
  - No change to HTTP status (still 200 on success)

### POST /api/v1/invoices/{invoice_id}/recall

**New side effect:**
- If invoice has a linked Visit in COMPLETED state:
  - Visit → reopens to AWAITING_PAYMENT
  - No change to HTTP status (still 200 on success)

### POST /api/v1/invoices/{invoice_id}/refund

**New side effect:**
- If invoice has a linked Visit in COMPLETED state:
  - Visit → reopens to AWAITING_PAYMENT
  - No change to HTTP status (still 200 on success)

---

## Acceptance Criteria Met

- [x] Void/recall/refund on COMPLETED visit → visit AWAITING_PAYMENT (reopened)
- [x] Reopened visit content is editable (PATCH/exam 200)
- [x] Round-trip: complete → void → editable → re-pay → complete works cleanly
- [x] Regression guard: COMPLETED still terminal for doctor's "finish exam" operation (transition_to_complete)

---

## Data Integrity Guarantees

- **State machine integrity:** COMPLETED remains terminal for normal doctor operations; reopen is only triggered by payment reversal, not by visit-module operations.
- **No orphaned lockouts:** Visit automatically unlocks when financial state changes.
- **Idempotent:** Calling reopen when Visit is not COMPLETED is a no-op (safe to wire unconditionally).

---

## Workflow Alignment

Aligns the "cancel invoice → edit" user journey with the actual billing state:
1. User cancels invoice (payment reversed, invoice unpaid)
2. User edits visit content (visit unlocked)
3. User re-bills (payment re-collected, visit auto-completes)

No manual state-fix workaround needed.

---

## Deployment Notes

- No database migration required.
- No breaking API changes (HTTP status codes unchanged).
- Safe to deploy with TASK-111 (independent cascade logic).
