# TASK-108: Visit-Service Guards — M-8 & M-9 Fix

**Date:** 2026-07-24  
**Status:** DONE  
**Test Coverage:** 89/89 passed (integration suite)

---

## Problem Summary

### M-8: Missing Visit Validation (500 → 404)
- **Issue:** `POST /visits/{unknown}/services` returned 500 Internal Server Error instead of 404 Not Found
- **Root Cause:** `add_to_visit()` called `raise_if_visit_closed()` (which is a no-op if the visit doesn't exist) and proceeded directly to insert VisitService; the `visit_id` NOT NULL foreign key constraint caused an IntegrityError leak 500
- **Impact:** Unclear error response; clients cannot distinguish "visit doesn't exist" from "server error"

### M-9: Under-billing on Issued Invoice (409 Protection Missing)
- **Issue:** Adding a billable service to a visit with an issued/paid invoice did not block the operation, resulting in silent under-billing (invoice total remained unchanged)
- **Root Cause:** `raise_if_visit_closed()` only checked for `COMPLETED` or `CANCELLED` statuses, not accounting for invoices in `issued`, `partially_paid`, or `paid` states
- **Impact:** Financial inconsistency; invoice line items did not reflect added services, creating audit and reconciliation issues

---

## Solution Design

### M-8: Pre-insert Validation
- **Change:** In `app/modules/services/services/visit_service_service.py`, `add_to_visit()` now calls `visit_service.get_visit(visit_id, clinic_id)` before checking closed status and inserting the VisitService row
- **Behavior:** If the visit doesn't exist, `get_visit()` raises a 404 HTTPException immediately; no IntegrityError leak
- **Scope:** Only `add_to_visit()` modified; the shared `raise_if_visit_closed()` contract (used by prescriptions, vitals) left untouched to avoid regression

### M-9: Invoice Status Block (409 Conflict)
- **Change:** After the visit-existence check, `add_to_visit()` now validates that the visit does not have an active invoice (`status IN (issued, partially_paid, paid)`)
- **Behavior:** If an active invoice exists, return **409 Conflict** with a message pointing the operator to the escape hatch: `POST /invoices/{id}/recall` (un-issues the invoice, auto-resyncs line items on the next submit)
- **Affected Statuses:** `issued`, `partially_paid`, `paid` (excludes `void`, `refunded`, `draft`)
- **Scope:** Draft invoices and pre-invoice service additions remain unaffected; only blocks concurrent changes to finalized billing

---

## Implementation Details

**File:** `app/modules/services/services/visit_service_service.py`

```python
# Pseudocode: add_to_visit() flow
1. get_visit(visit_id, clinic_id)  # → 404 if not found
2. raise_if_visit_closed(visit)   # → 409 if COMPLETED/CANCELLED
3. check_invoice_status(visit)    # → 409 if issued/partially_paid/paid
4. insert VisitService            # → 201 on success
```

**Reused Components:**
- `visit_service.get_visit()` — existing scoped lookup (clinic_id filter)
- `visit_service.raise_if_visit_closed()` — unchanged behavior for existing callers
- No changes to `invoice_service.py` or `visit_service.py`; the recall flow was already in place

---

## Testing

**Test Environment:** Isolated Docker stack `v108` (api 9969 / pg 5469 / redis 6451), migrated to alembic head 0067

**Test Cases:**
1. `test_add_service_to_unknown_visit_returns_404` — POST unknown visit → 404
2. `test_add_service_to_visit_with_issued_invoice_blocked` — POST issued/partially_paid/paid → 409; confirm recall → re-add succeeds with resync; invoice total unchanged while blocked
3. Pre-existing integration suite (visits, services, billing) — no regression

**Results:** **89/89 passed** ✓
- Unknown visit add → 404 ✓
- Issued/partially_paid/paid invoice add → 409, recall escape hatch works ✓
- Pre-invoice add → 201 (no regression) ✓
- Closed visit → 409 (no regression) ✓

**Code Quality:**
- `ruff check` on modified files → 0 errors
- `mypy` on modified files → 0 errors

---

## Deployment Notes

- **Migration:** None required (no schema changes)
- **Backward Compatibility:** Full — existing callers of `raise_if_visit_closed()` unaffected
- **Configuration:** None
- **Rollout:** Safe to deploy in any environment; no data cleanup needed

---

## References

- **Branch:** `fix/TASK-108-visit-service-guards` (commit `54c31f1`)
- **Test Report:** `docs/tasks/TASK-108/deliveries/test-reports/test-report.md`
- **Source E2E Finding:** TASK-095 (M-8, M-9)
