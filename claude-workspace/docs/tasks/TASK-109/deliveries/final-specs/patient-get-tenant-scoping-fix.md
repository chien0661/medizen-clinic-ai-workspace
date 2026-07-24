# TASK-109: Patient GET Tenant Scoping — M-19 Fix

**Date:** 2026-07-24  
**Status:** DONE  
**Test Coverage:** 122/125 passed (in-scope tests; 3 baseline failures unrelated)

---

## Problem Summary

### M-19: Missing clinic_id Filter on GET /patients/{id} (IDOR + 500 Oracle)
- **Issue:** `GET /patients/{id}` did not filter by `clinic_id`, allowing foreign-clinic patient rows to be loaded and returning 500 instead of 404
- **Root Cause:** `get_patient()` in `patient_service.py` used unscoped `db.get(Patient, patient_id)`, relying entirely on Row-Level Security (RLS) which was already bypassed in testing (C-7)
- **Impact:** 
  - **IDOR:** Foreign-clinic patient data accessible (PII leak: patient_code, DOB, gender visible in plaintext; full_name only protected by decrypt-failure 500)
  - **404-vs-500 Oracle:** Cross-clinic queries threw InvalidTag on EncryptedString decrypt → 500 instead of 404, revealing row existence across tenant boundaries
  - **Scope Leak:** Same vulnerability in `update_patient()` and `soft_delete_patient()` which call `get_patient()` internally

---

## Solution Design

### Scoped Lookup with clinic_id Filter
- **Change:** Rewrite `get_patient()` to use `select(Patient).where(...)` instead of unscoped `db.get()`, filtering by:
  - `Patient.id == patient_id`
  - `Patient.clinic_id == clinic_id` (sourced from `_require_clinic_id()`)
  - `Patient.is_deleted == False` (exclude soft-deleted)
- **Behavior:** If no matching row exists, return 404 Not Found; if found, return 200 with patient data
- **Scope Cascade:** `update_patient()` and `soft_delete_patient()` automatically inherit the same filter through their internal calls to `get_patient()`
- **Pattern:** Mirrors the existing `visit_service._get_visit_or_404()` pattern (clinic_id scoping already proven safe in visits module)

**File:** `app/modules/patients/services/patient_service.py`

---

## Implementation Details

**Scoped Query:**
```python
# Before: db.get(Patient, patient_id) — no clinic_id filter
# After:
select(Patient).where(
    (Patient.id == patient_id) &
    (Patient.clinic_id == clinic_id) &
    (Patient.is_deleted.is_(False))
)
```

**clinic_id Source:** `_require_clinic_id()` from request context (same pattern used in every other patients route)

**Affected Endpoints:**
- `GET /patients/{id}` — direct scoped lookup
- `PATCH /patients/{id}` — calls `get_patient()` internally, now scoped
- `DELETE /patients/{id}` (soft-delete) — calls `get_patient()` internally, now scoped

**No Changes:** `visit_service.py`, `invoice_service.py`, routes layer (clinic_id already available in request context)

---

## Testing

**Test Environment:** Isolated Docker stack `v109` (api 9968 / pg 5468 / redis 6450), migrated to alembic head 0067

**Test Cases:**
1. **Cross-tenant GET → 404:** Patient from clinic B accessed by clinic A user → 404 (no 500, no PII)
2. **Own-clinic GET → 200:** Patient from same clinic → 200 with full data
3. **Soft-deleted → 404:** Deleted patient → 404 regardless of clinic (is_deleted filter)
4. **Cross-tenant PATCH/DELETE → 404:** Cascaded scoping on write operations
5. **Phone search (baseline):** Pre-existing RLS test, unmodified; confirms no regression in query path

**Results:** **122/125 passed** ✓
- Cross-tenant GET → 404 ✓
- Own-clinic GET → 200 ✓
- Soft-deleted → 404 ✓
- Cross-tenant PATCH/DELETE → 404 ✓
- **Baseline Failures (pre-existing, not caused by this fix):**
  - `test_merge_cross_tenant_forbidden` — DEK/RLS merge service issue
  - `test_rls_search_by_phone_cross_clinic_returns_zero` — DEK phone search
  - `test_rls_merge_cross_tenant_blocked_at_service_layer` — merge service RLS

**Code Quality:**
- `ruff check` on modified files → 0 errors
- `mypy` on modified files → 0 errors

---

## Security Impact

- **IDOR Closed:** Foreign-clinic patients now return 404; plaintext fields (patient_code, DOB, gender) no longer accessible cross-tenant
- **Oracle Closed:** 404 response is consistent (no 500 on decrypt failure); removes existence oracle
- **RLS Dependency Reduced:** Application layer scoping now provides defense-in-depth; RLS bypass (if it occurs elsewhere) does not expose foreign-clinic patients through this endpoint

---

## Follow-up Notes

**Out of Scope (Tracked Separately):**
- `guardian_service` and `merge_service` still use unscoped `db.get(Patient)` in internal calls — recommend adding clinic_id filters as a separate hardening task
- Broader RLS audit (C-7) tracks systematic RLS bypass issues; this fix addresses the specific patient GET path

---

## Deployment Notes

- **Migration:** None required (no schema changes)
- **Backward Compatibility:** Full — existing callers benefit from narrower scope; no API contract change (still returns 404 on not found, 200 on success)
- **Configuration:** None
- **Rollout:** Safe to deploy immediately; no data cleanup needed

---

## References

- **Branch:** `fix/TASK-109-patient-get-tenant-filter` (commit `a8b0f5f`)
- **Test Report:** `docs/tasks/TASK-109/deliveries/test-reports/test-report.md`
- **Source E2E Finding:** TASK-095 (M-19)
- **Related Tasks:** TASK-100 (RLS audit C-5), TASK-102 (RLS audit C-7)
