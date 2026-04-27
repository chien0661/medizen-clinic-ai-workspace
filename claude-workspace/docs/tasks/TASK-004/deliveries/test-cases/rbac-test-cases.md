# TASK-004 RBAC — Test Cases

**Date**: 2026-04-27
**Agent**: Test Agent
**Branch**: `feature/task-004-rbac` (HEAD `afb922a`)
**Total Scenarios**: 40 (273 pre-existing + 16 new = 289 total; 40 RBAC-specific)

---

## AC → Test Scenario Mapping

| AC | Scenario | Test File | Test Function | Status |
|----|----------|-----------|---------------|--------|
| AC1 | DB has exactly 38 permissions from migration 0007 | `tests/integration/test_rbac_e2e_real_db.py` | `TestRbacE2eRealDb::test_seed_integrity` | PASS |
| AC1 | DB has exactly 5 system roles (clinic_id IS NULL, is_system=TRUE) | `tests/integration/test_rbac_e2e_real_db.py` | `TestRbacE2eRealDb::test_seed_integrity` | PASS |
| AC1 | 5 system role codes: admin, doctor, nurse, pharmacist, receptionist | `tests/integration/test_role_modification.py` | `TestSystemRoleProtection::test_system_role_codes_are_correct` | PASS |
| AC1 | All expected permission codes present in seed data (38 items) | `tests/integration/test_rbac_seed.py` | `TestPermissionCatalogSeeded::test_all_expected_permissions_present` | PASS |
| AC2 | Admin has all 38 permissions in DB (real DB) | `tests/integration/test_rbac_e2e_extended.py` | `TestAc2RolePermissionMappingRealDb::test_admin_has_all_38_permissions` | PASS |
| AC2 | Doctor has vital.write in DB (BA §13.6) | `tests/integration/test_rbac_e2e_extended.py` | `TestAc2RolePermissionMappingRealDb::test_doctor_has_vital_write` | PASS |
| AC2 | Pharmacist has pharmacy.dispense in DB | `tests/integration/test_rbac_e2e_extended.py` | `TestAc2RolePermissionMappingRealDb::test_pharmacist_has_pharmacy_dispense` | PASS |
| AC2 | Nurse does NOT have prescription.write | `tests/integration/test_rbac_e2e_extended.py` | `TestAc2RolePermissionMappingRealDb::test_nurse_does_not_have_prescription_write` | PASS |
| AC2 | Doctor does NOT have pharmacy.dispense | `tests/integration/test_rbac_e2e_extended.py` | `TestAc2RolePermissionMappingRealDb::test_doctor_does_not_have_pharmacy_dispense` | PASS |
| AC2 | Doctor role mapping correct per BA §13.6 (seed data unit) | `tests/integration/test_rbac_seed.py` | `TestRolePermissionMapping::test_doctor_mapping_correct` | PASS |
| AC2 | Admin has user.manage and role.manage | `tests/integration/test_rbac_seed.py` | `TestRolePermissionMapping::test_admin_has_user_manage` | PASS |
| AC2 | Receptionist cannot void invoice | `tests/integration/test_rbac_seed.py` | `TestRolePermissionMapping::test_receptionist_cannot_void_invoice` | PASS |
| AC3 | Doctor role lacks pharmacy.dispense (BA §13.6 spirit) | `tests/integration/test_rbac_e2e_extended.py` | `TestAc2RolePermissionMappingRealDb::test_doctor_does_not_have_pharmacy_dispense` | DEFERRED (pharmacy module not built) |
| AC4 | extra_deny overrides role grant — DB state verified | `tests/integration/test_rbac_e2e_real_db.py` | `TestRbacE2eRealDb::test_extra_deny_blocks_even_with_role_grant` | PASS |
| AC4 | extra_deny blocks actual HTTP call → 403 (end-to-end API) | `tests/integration/test_rbac_e2e_extended.py` | `TestAc4ExtraDenyBlocksApiCall::test_extra_deny_blocks_api_call_end_to_end` | PASS |
| AC4 | deny precedence over extra_grant (unit) | `tests/integration/test_rbac_extra_perm.py` | `TestExtraGrant::test_deny_overrides_extra_grant` | PASS |
| AC4 | (role_perms ∪ extra_grants) − extra_denies logic | `tests/integration/test_rbac_seed.py` | `TestEffectivePermissionsUnit::test_effective_perms_union_minus_deny` | PASS |
| AC5 | Role assignment grants access; revocation blocks (full HTTP cycle) | `tests/integration/test_rbac_e2e_real_db.py` | `TestRbacE2eRealDb::test_role_assignment_grants_access_then_revocation_blocks` | PASS |
| AC5 | Redis cache populated after first authenticated request | `tests/integration/test_rbac_e2e_real_db.py` | `TestRbacE2eRealDb::test_role_assignment_grants_access_then_revocation_blocks` (step 4) | PASS |
| AC5 | Redis cache invalidated after role revocation | `tests/integration/test_rbac_e2e_real_db.py` | `TestRbacE2eRealDb::test_role_assignment_grants_access_then_revocation_blocks` (step 5) | PASS |

---

## Business Rule Tests

| Rule | Scenario | Test File | Test Function | Status |
|------|----------|-----------|---------------|--------|
| BR-RBAC-01 | User with no roles → 403 on protected route | `tests/integration/test_rbac_e2e_real_db.py` | `TestRbacE2eRealDb::test_doctor_cannot_access_user_manage_route` | PASS |
| BR-RBAC-02 | Multi-role union: doctor+pharmacist have combined perms | `tests/integration/test_rbac_e2e_extended.py` | `TestBusinessRuleEdgeCases::test_multi_role_union_grants_combined_permissions` | PASS |
| BR-RBAC-03 | extra_perm survives role revocation (independent of role membership) | `tests/integration/test_rbac_e2e_extended.py` | `TestBusinessRuleEdgeCases::test_extra_perm_survives_role_revocation` | PASS |
| BR-RBAC-04 | Idempotent extra_permission: same call twice → same record | `tests/integration/test_rbac_e2e_real_db.py` | `TestRbacE2eRealDb::test_idempotent_extra_permission` | PASS |
| BR-RBAC-05 | System role immutable: cannot delete | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_delete_system_role_returns_403` | PASS |
| BR-RBAC-06 | System role immutable: cannot PATCH name | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_patch_system_role_returns_403` | PASS |
| BR-RBAC-07 | System role immutable: cannot add permission | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_post_system_role_permissions_returns_403` | PASS |
| BR-RBAC-08 | System role immutable: cannot remove permission | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_delete_system_role_permission_returns_403` | PASS |
| BR-RBAC-09 | Cache invalidation on role assignment | `tests/integration/test_rbac_e2e_real_db.py` | (step 3-4 of role cycle test) | PASS |
| BR-RBAC-10 | Cache invalidation on role revocation | `tests/integration/test_rbac_e2e_real_db.py` | (step 5 of role cycle test) | PASS |

---

## API Contract Tests (Negative Paths)

| Endpoint | Scenario | Test File | Test Function | Status |
|----------|----------|-----------|---------------|--------|
| GET /users | Anonymous → 401 | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_anonymous_list_users_returns_401` | PASS |
| GET /roles | Anonymous → 401 | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_anonymous_list_roles_returns_401` | PASS |
| POST /users/{id}/roles | Anonymous → 401 | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_anonymous_assign_role_returns_401` | PASS |
| GET /roles | Doctor (no role.manage) → 403 | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_doctor_cannot_list_roles` | PASS |
| GET /users | Doctor (no user.manage) → 403 | `tests/integration/test_rbac_e2e_real_db.py` | `TestRbacE2eRealDb::test_doctor_cannot_access_user_manage_route` | PASS |
| PATCH /roles/{id} | System role → 403 | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_patch_system_role_returns_403` | PASS |
| POST /roles/{id}/permissions | System role → 403 | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_post_system_role_permissions_returns_403` | PASS |
| DELETE /roles/{id}/permissions/{code} | System role → 403 | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_delete_system_role_permission_returns_403` | PASS |
| DELETE /roles/{id} | System role → 403 | `tests/integration/test_rbac_e2e_extended.py` | `TestNegativePaths::test_delete_system_role_returns_403` | PASS |
| DELETE /roles/{id} | System role (mock DB) → 403 | `tests/integration/test_role_modification.py` | `TestSystemRoleProtection::test_delete_system_role_returns_403` | PASS |

---

## Deferred / Out of Scope

| AC | Reason |
|----|--------|
| **AC3** (Doctor cannot POST /pharmacy/dispense → 403) | Pharmacy module not yet built. The permission catalog correctly excludes `pharmacy.dispense` from the doctor role (verified by `test_doctor_does_not_have_pharmacy_dispense`). AC3 will be formally closed when TASK-pharmacy ships. |

---

## Coverage Notes

| Module | Coverage | Notes |
|--------|----------|-------|
| `app/modules/users/services/rbac_service.py` | 95% | 7 lines: Redis exception handlers (60-61, 70-71, 83-84) + idempotent same-params return (274). These are defensive error handlers, not logic paths. |
| `app/modules/users/api/routes.py` | 45% | Uncovered lines are user CRUD handlers (create/update/delete/get user body logic). These require full request+response cycle and are RBAC-adjacent, not RBAC core. Route guards (is_system checks) are fully covered. |
| `app/modules/users/services/user_service.py` | 31% | User CRUD service not in RBAC scope — separate testing task needed. |
| All RBAC models + schemas | 100% | Complete coverage. |
| `app/core/permissions.py` | (included in rbac_service coverage run) | require_permission decorator exercised by multiple e2e tests. |
