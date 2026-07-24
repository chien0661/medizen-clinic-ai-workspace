# Handoff: TASK-109 → Code Review

**From**: Code Implementation Agent (FIX MODE)
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-07-24
**Branch**: `fix/TASK-109-patient-get-tenant-filter` (base `origin/dev` @ 649bde4, alembic head 0067)

## Summary

`GET /patients/{id}` (bug M-19) had no `clinic_id` filter — `get_patient()` used
`db.get(Patient, patient_id)` and relied solely on RLS for tenant isolation. With RLS
bypassed (app DB role), a foreign-clinic patient row would load, then its
`EncryptedString` columns (e.g. `full_name`) would fail to decrypt with the caller's
DEK → `cryptography.exceptions.InvalidTag` → uncaught 500. That created a
404-vs-500 enumeration oracle (foreign patient → 500, non-existent → 404) and a
latent full-PII IDOR (plaintext columns like `patient_code`/`dob`/`gender` were the
exposure surface, only accidentally hidden because the name-decrypt raised first).

## Fix

`patient_service.get_patient` now takes a `clinic_id` param and filters at the query
level, mirroring `visit_service._get_visit_or_404`:

```python
result = await db.execute(
    select(Patient).where(
        Patient.id == patient_id,
        Patient.clinic_id == clinic_id,
        Patient.is_deleted.is_(False),
    )
)
patient = result.scalar_one_or_none()
if patient is None:
    raise NotFoundError("Patient not found")
```

A foreign-clinic row is now excluded by the `WHERE` clause and never loaded — no
decrypt attempt, no `InvalidTag`, clean 404 in all cases.

`clinic_id` is sourced the same way every other patients route already gets it:
`current_clinic_id` (request-scoped contextvar set by the auth/tenancy middleware
from the caller's JWT), via the existing `_require_clinic_id()` helper in
`api/routes.py`.

**Cascade to sibling callers**: `update_patient` and `soft_delete_patient` both call
`get_patient` internally to fetch-before-mutate, so they had the identical flaw (and
a worse one — write/delete of a foreign-clinic patient, not just a read). Both now
also take a required `clinic_id` param and pass it through; their routes
(`PATCH /patients/{id}`, `DELETE /patients/{id}`) now call `_require_clinic_id()` and
pass it in. These were not separately reported but are the same function/same file/
same root cause, and changing `get_patient`'s signature required touching them
anyway to not break the build.

**Explicitly out of scope** (different files/modules, not touched): `guardian_service.py`
and `merge_service.py` also contain unscoped `db.get(Patient, ...)` calls, but they are
separate call sites with their own logic (merge already has its own cross-tenant 403
check at the service layer) — left alone per "do not change unrelated code."

## Files Changed

- `app/modules/patients/services/patient_service.py` — `get_patient(db, patient_id,
  clinic_id)` now filters by clinic_id (select+where instead of `db.get`);
  `update_patient` / `soft_delete_patient` gained a required `clinic_id` param, passed
  through to `get_patient`.
- `app/modules/patients/api/routes.py` — `GET/PATCH/DELETE /patients/{id}` now resolve
  `clinic_id = _require_clinic_id()` and pass it to the service calls.
- `tests/unit/patients/test_patient_service.py` — updated `TestGetPatient` /
  `TestUpdatePatient` / `TestSoftDeletePatient` mocks from `db.get` to `db.execute` +
  `scalar_one_or_none`; added `test_raises_not_found_when_foreign_clinic`.
- `tests/integration/patients/test_patients_api.py` — `test_tenant_isolation_via_http`:
  tightened the cross-tenant GET assertion from `in (200, 404)` to strict `== 404`;
  fixed the `soft_delete_patient` call in `test_...` to pass the new `clinic_id` arg.
- `tests/integration/patients/test_rls_isolation_cms_app_role.py` —
  `test_rls_via_http_get_patient_cross_tenant_returns_404`: tightened from
  `in (200, 404)` to strict `== 404` (no longer depends on RLS/BYPASSRLS — the app
  layer now enforces it unconditionally).

## Test Results (isolated Docker stack `fix109`: api 9971 / pg 5471 / redis 6453, alembic head 0067)

- **Unit — `tests/unit/patients/`: 62/62 pass** (full module, includes the updated
  get/update/soft-delete-patient suites).
- **Integration — `tests/integration/patients/`: 60/63 pass.** The 2 tests targeting
  this exact bug (`test_rls_via_http_get_patient_cross_tenant_returns_404`,
  `test_tenant_isolation_via_http`) pass with the now-strict `== 404` assertion.
- **3 pre-existing failures, NOT caused by this change** — verified identical on
  baseline `origin/dev` (stashed my diff, same migrated DB, same 3 tests fail):
  `test_merge_cross_tenant_forbidden`,
  `test_rls_search_by_phone_cross_clinic_returns_zero`,
  `test_rls_merge_cross_tenant_blocked_at_service_layer`. First and third are the
  separate `merge_service.py` unscoped `db.get(Patient, ...)` IDOR (out of scope here,
  same class of bug but different file/function — worth its own ticket); the phone
  search failure predates this change too. All 3 reproduce unchanged on unmodified
  `origin/dev`.

## Static analysis

- `ruff check app tests`: **0 new** (repo has 452 pre-existing errors, entirely in
  unrelated files/lines — e.g. `tests/unit/vitals/test_validator.py`; the one hit in
  `patient_service.py` — `SIM102` in `search_patients` — is pre-existing, confirmed
  identical line count on `origin/dev` before my diff, and outside the functions I
  touched).
- `mypy app`: **0 new** (20 pre-existing errors, same 20 on `origin/dev` baseline —
  mostly `datetime.UTC` py3.10-vs-3.11 stub mismatches unrelated to this change; none
  on the lines I edited).

## Areas for Review Focus

1. Confirm `update_patient`/`soft_delete_patient` picking up `clinic_id` is in scope —
   it fixes the same class of bug (foreign-clinic write/delete) but wasn't in the
   original M-19 report; flag if you'd rather split it into its own ticket.
2. The two pre-existing `merge_service.py` cross-tenant failures
   (`test_merge_cross_tenant_forbidden`, `test_rls_merge_cross_tenant_blocked_at_service_layer`)
   look like the same root-cause pattern (unscoped `db.get(Patient, ...)`) — recommend
   a follow-up ticket; not fixed here to keep this diff scoped to M-19.
3. `test_rls_search_by_phone_cross_clinic_returns_zero` pre-existing failure is
   unrelated to patient-by-id lookup; also worth a separate look.

## Not run

Docker was available this session (no instability encountered); isolated stack
`fix109` was created, migrated (0067), tested, and torn down (`docker compose -p
fix109 down -v`). No FE/UI changes (backend-only fix).
