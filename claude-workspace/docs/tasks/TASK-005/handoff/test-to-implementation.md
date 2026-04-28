# Handoff: TASK-005 → Code Implementation Agent

**From:** Test Agent
**To:** Code Implementation Agent
**Status:** IN_PROGRESS (iteration 3)
**Date:** 2026-04-27

## Summary

Tests FAILED (4/117 non-perf tests). Bug reports created.

117 non-perf tests run. 113 passed. 4 failed in negative/fuzz scenarios.
Performance AC1 validated (phone search p95 = 46.9ms < 100ms). RLS confirmed. Audit log verified.

## Failures

| Bug | Severity | Test | Failure |
|-----|----------|------|---------|
| [BUG-001](../bugs/BUG-001.md) | High | `test_search_null_byte_q_does_not_500` | Null byte `%00` in search `q` causes 500 (asyncpg UTF8 error) — must sanitize to 400 |
| [BUG-002](../bugs/BUG-002.md) | Medium | `test_create_future_dob_returns_4xx` | Future `date_of_birth` (e.g., 2099-01-01) accepted as 201 — must reject as 400/422 |
| [BUG-003](../bugs/BUG-003.md) | High | `test_merge_same_id_returns_4xx` | Self-merge (`keep_id == drop_id`) succeeds as 201 — must reject as 400/422 |
| [BUG-004](../bugs/BUG-004.md) | Critical | `test_undo_merge_from_different_clinic_returns_404_or_403` | Cross-clinic undo returns 200 — `undo_merge()` has no clinic ownership check |

## Fix Priority

1. **BUG-004 (Critical)**: Add `clinic_id` ownership check in `merge_service.undo_merge()`. After fetching `PatientMergeLog`, verify `merge_log.clinic_id == calling_clinic_id`. Pass `clinic_id` from the JWT into the service call via the API route.
2. **BUG-003 (High)**: Add self-merge guard in `merge_service.merge()` or `MergeRequest` Pydantic schema: raise 400 if `keep_id == drop_id`.
3. **BUG-001 (High)**: Sanitize null bytes in search `q` parameter — reject with 400 in the route or service.
4. **BUG-002 (Medium)**: Add Pydantic `field_validator` in `PatientCreateRequest.date_of_birth` to reject future dates.

## What Passed (Do Not Regress)

- All 79 pre-existing tests (61 unit + 18 integration) still pass.
- 8 RLS isolation tests (cms_app role): all pass.
- 5 audit invariant tests: all pass.
- 6 merge/undo advanced matrix tests: all pass.
- 15/19 negative path tests: pass.
- 2 performance tests: phone search p95 = 46.9ms (AC1 ✅), fuzzy name p95 = 180.5ms.

## Relevant Files

- `clinic-cms/app/modules/patients/services/merge_service.py` — BUG-003, BUG-004
- `clinic-cms/app/modules/patients/schemas/patient_schemas.py` — BUG-002, BUG-003 (alternative)
- `clinic-cms/app/modules/patients/api/routes.py` — BUG-001, BUG-004 (pass clinic_id)
- Test files (do not modify source): `tests/integration/patients/test_patients_negative.py`

## After Fix

Re-run: `pytest tests/unit/patients/ tests/integration/patients/ -m 'not perf' -q --tb=short`

Expected: 0 failures, 117 passed.

Then resubmit to review agent with updated handoff.
