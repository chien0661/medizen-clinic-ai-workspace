# ADR: Silent Parameter Drops in Query Filters — Discovery & Prevention Pattern

**Date:** 2026-09-01  
**Status:** Documented (from TASK-146 audit)  
**Related:** TASK-146, invoice_service.py `GET /api/v1/invoices` fix  
**Audience:** Backend architects, API designers, code reviewers

---

## Problem

In TASK-146's audit phase, a critical bug was discovered in `GET /api/v1/invoices`:

```python
# Route declaration
@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    status_filter: Optional[str] = Query(None),
    visit_id: Optional[UUID] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    clinic_id: UUID = Depends(get_current_clinic_id),
):
    # ... implementation calls invoice_service.list_invoices(...)
```

The **frontend was sending** `patient_id` in the query string:

```javascript
GET /api/v1/invoices?patient_id=<uuid>&limit=50&offset=0
```

But the **backend route never declared** a `patient_id` parameter. FastAPI silently ignores unknown query parameters, so:

1. The filter was never applied
2. The endpoint returned invoices from the **entire clinic**, not just the requested patient
3. The UI appeared to work (it showed invoice data, just the wrong patient's data)
4. The bug was invisible for months because invoice counts looked normal on single-patient clinic scenarios

**Result:** A receptionist opening a multi-patient clinic's patient chart would see that patient's **plus invoices from all other patients** in the same clinic. **Data leak + wrong patient data shown on screen.**

---

## Why This Pattern Is Dangerous

### 1. **Silent Failure, Not Loud**

```python
# LOUD (easy to catch):
GET /api/v1/invoices?unknown_param=123
# → Response: 400 Bad Request "Unknown parameter"

# SILENT (hard to catch):
GET /api/v1/invoices?patient_id=<uuid>  # not declared in route
# → Response: 200 OK (with wrong data)
```

FastAPI's default behavior is to silently drop unknown query parameters. The request "succeeds", so tests pass, users don't see error messages, and logs stay quiet. The bug only surfaces when:
- Someone manually audits the returned data for correctness
- A test specifically verifies row counts per patient
- Code review catches the declaration-vs-usage mismatch

### 2. **Frontend Filter Assumption**

When frontend code sends a filter parameter, developers assume "the backend will filter for me". The frontend passes `patient_id`, gets data back, and never questions whether the backend actually applied the filter. This creates a false sense of security.

### 3. **Works in Single-Patient Scenarios**

If test data only ever involves one patient per clinic, the bug is invisible. All invoices returned happen to belong to that one patient, so the test passes. The bug only surfaces under realistic multi-patient load.

---

## Solution: Declaration-Driven Validation

**Rule:** Every query parameter the frontend intends to filter on **must** be explicitly declared in the route signature.

### Pattern A: Explicit Route Declaration (Recommended)

```python
# BEFORE (BUG):
@router.get("")
async def list_invoices(
    status_filter: Optional[str] = Query(None),
    visit_id: Optional[UUID] = Query(None),
    # ↑ patient_id is missing!
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    # visit_id filter applied, patient_id ignored → silent data leak

# AFTER (FIXED):
@router.get("")
async def list_invoices(
    patient_id: Optional[UUID] = Query(None),  # ← now declared
    status_filter: Optional[str] = Query(None),
    visit_id: Optional[UUID] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    # All three filters applied → data returned matches intent
    return await invoice_service.list_invoices(
        patient_id=patient_id,
        status_filter=status_filter,
        visit_id=visit_id,
        limit=limit,
        offset=offset,
        clinic_id=clinic_id,
    )
```

### Pattern B: Validation Layer (For Extra Safety)

If manual query building is used, add explicit validation:

```python
# Validate that frontend-intended filters are handled
required_filters = {"patient_id", "status"}
provided_filters = set(query_params.keys())

unexpected = provided_filters - {"patient_id", "status", "limit", "offset"}
if unexpected:
    raise ValueError(f"Unknown filters provided: {unexpected}")

unhandled = required_filters & (provided_filters - handled_filters)
if unhandled:
    raise ValueError(f"Filters provided but not handled: {unhandled}")
```

---

## Detection: Code Review Checklist

When reviewing API route changes, ask:

1. **Does every query parameter in the route signature get used?**
   - If not declared: ❌ will be ignored silently
   - If declared but not used: ❌ dead code or a bug

2. **Does the service method handle all declared params?**
   - Check: route → service function call
   - Every param passed to the service?
   - Every param in the where clause?

3. **Do the integration tests verify the filter?**
   - Test data setup: Two patients in the same clinic, each with different data
   - Assertion: Requesting patient A's data returns A's records only, never B's
   - Common mistake: Only testing single-patient scenarios

4. **Does the frontend match the backend's parameters?**
   - Check frontend API client
   - For each filter the FE sends, verify the route declares it
   - Integration test: call the real API (not mocks) with valid and invalid param names

---

## Application to TASK-146

**The fix (FIX-2):**

```python
# Added to route:
patient_id: Optional[UUID] = Query(None),

# Passed to service:
return await invoice_service.list_invoices(
    patient_id=patient_id,  # ← new filter
    ...
)

# Service applies filter:
if patient_id:
    query = query.join(Visit).where(Visit.patient_id == patient_id)
```

**Test coverage added:**

```python
# Two patients, same clinic
invoices_for_patient_a = ...
invoices_for_patient_b = ...

# Request patient A's list
response_a = client.get(f"/invoices?patient_id={patient_a_id}")
assert response_a.items.count == len(invoices_for_patient_a)
assert all(inv.patient_id == patient_a_id for inv in response_a.items)

# Request patient B's list
response_b = client.get(f"/invoices?patient_id={patient_b_id}")
assert response_b.items.count == len(invoices_for_patient_b)
assert all(inv.patient_id == patient_b_id for inv in response_b.items)

# Verify no cross-contamination
assert set(response_a.item_ids) & set(response_b.item_ids) == set()
```

---

## Prevention Going Forward

### For Developers

When adding a query filter:

1. **Declare it** in the route signature with `Query(...)`
2. **Pass it** to the service layer
3. **Use it** in the SQL where clause
4. **Test it** with multiple rows of data where the filter makes a difference

Checklist template:
```python
# ✓ Declared in route
status: Optional[str] = Query(None)

# ✓ Passed to service
await service.list(..., status=status)

# ✓ Used in where clause
if status:
    query = query.where(Model.status == status)

# ✓ Tested
def test_status_filter_returns_only_matching_rows():
    assert ...
```

### For Code Reviewers

- [ ] Every `Query(...)` in the route signature is passed to the service? 
- [ ] Every passed parameter is used in the service's SQL? 
- [ ] Integration test verifies the filter with multi-row data? 
- [ ] Frontend sends the parameter with the expected name? 

### For Architects

- Establish linting rule: unused `Query` parameters (parameters declared but not referenced in the function body) trigger a warning
- Add a test template to `docs/` for multi-patient filtering tests
- Document this pattern in API design guidelines

---

## Related Issues

- **BUG-146-04:** No UI action to submit prescriptions → similar root cause (missing wiring), but caught at design time (backend has the endpoint, frontend just never calls it)
- **TASK-145:** Audit logs ensure we can forensically detect silent data leaks after the fact — but preventing them at design time is better

---

## References

- TASK-146 audit report: `docs/tasks/TASK-146/handoff/audit-report.md` (section "NEW — InvoicesTab patient_id filter")
- Fixed code: `clinic-cms/app/modules/billing/api/routes.py` (route), `app/modules/billing/services/invoice_service.py` (service filter logic)
- Test case: `clinic-cms-web/src/tests/patients/InvoicesTab.test.tsx` (AC2 patient filter verification)

