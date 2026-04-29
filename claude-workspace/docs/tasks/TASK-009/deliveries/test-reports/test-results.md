# TASK-009 Test Results

**Date**: 2026-04-27  
**DB**: cms_task009 (postgresql+asyncpg://cms:cms@postgres:5432/cms_task009)  
**Branch**: feature/task-009-vitals  
**Commit**: 2ab0f0c  

---

## Summary

| Suite | Tests | Passed | Failed | Duration |
|-------|-------|--------|--------|----------|
| Unit (tests/unit/vitals/) | 12 | 12 | 0 | 0.26s |
| Integration (tests/integration/vitals/) | 20 | 20 | 0 | 35.52s |
| **Total** | **32** | **32** | **0** | **~36s** |

---

## Unit Tests (test_validator.py)

| Class | Test | Result |
|-------|------|--------|
| TestAC2GeneralVitals | test_general | PASSED |
| TestAC3UnknownField | test_unknown_error | PASSED |
| TestRequiredCheck | test_required_missing | PASSED |
| TestRequiredCheck | test_empty | PASSED |
| TestTypeMismatch | test_int_string | PASSED |
| TestTypeMismatch | test_bool_invalid | PASSED |
| TestTypeMismatch | test_select_bad | PASSED |
| TestRangeCheck | test_below_min | PASSED |
| TestRangeCheck | test_above_max | PASSED |
| TestRangeCheck | test_boundary | PASSED |
| TestMultiErrors | test_all | PASSED |
| TestMultiErrors | test_inactive_excluded | PASSED |

---

## Integration Tests (test_vitals_api.py)

| Class | Test | AC | Result |
|-------|------|-----|--------|
| TestAC1Pediatric | test_5_fields | AC1 | PASSED |
| TestAC1Pediatric | test_field_keys | AC1 | PASSED |
| TestAC1Pediatric | test_schema_version_created | AC1 | PASSED |
| TestAC2PostVitals | test_post_general | AC2 | PASSED |
| TestAC2PostVitals | test_nurse_post | AC2 | PASSED |
| TestAC3UnknownField | test_unknown | AC3 | PASSED |
| TestAC4SchemaEvolution | test_is_required_bumps_version | AC4 | PASSED |
| TestAC5Immutable | test_rename_rejected | AC5 | PASSED |
| TestAC5Immutable | test_data_type_rejected | AC5 | PASSED |
| TestAC6GIN | test_gin_exists | AC6 | PASSED |
| TestPermissions | test_nurse_no_manage | Perms | PASSED |
| TestPermissions | test_no_auth_401 | Perms | PASSED |
| TestMultiVitals | test_first_auto_primary | Multi | PASSED |
| TestMultiVitals | test_second_not_primary | Multi | PASSED |
| TestMultiVitals | test_get_all | Multi | PASSED |
| TestRLS | test_b_no_see_a | RLS | PASSED |
| TestRLS | test_b_no_modify_a | RLS | PASSED |
| TestCoverageBoost | test_list_definitions | Coverage | PASSED |
| TestCoverageBoost | test_delete_definition | Coverage | PASSED |
| TestCoverageBoost | test_get_visit_vitals_empty | Coverage | PASSED |

---

## Acceptance Criteria Verification

| AC | Description | Status |
|----|-------------|--------|
| AC1 | Onboard pediatric clinic → 5 fields (weight, height, head_circumference, temperature, pulse) | VERIFIED |
| AC2 | POST {systolic_bp: 120, diastolic_bp: 80} general → 201 | VERIFIED |
| AC3 | POST unknown key → 422 "Unknown field: xyz" | VERIFIED |
| AC4 | Modify is_required → new version, old data readable | VERIFIED |
| AC5 | Rename key → 400 "Cannot rename key, create new field instead" | VERIFIED |
| AC6 | GIN index ix_visit_vitals_values_gin exists on visit_vitals.values | VERIFIED |

---

## Notes

- DeprecationWarning on `HTTP_422_UNPROCESSABLE_ENTITY` constant (upstream FastAPI); does not affect functionality
- ORJSONResponse deprecation warnings are from the shared core module, not vitals-specific
