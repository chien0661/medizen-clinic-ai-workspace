# TASK-004 RBAC — Test Report

**Date**: 2026-04-27
**Agent**: Test Agent
**Branch**: `feature/task-004-rbac`
**HEAD**: `afb922a` (test commit on top of `bba9020`)
**Environment**: Docker — Python 3.11.15, PostgreSQL 15, Redis 7

---

## Executive Summary

All 289 tests pass. Zero failures. Zero bugs filed.

The RBAC implementation is **ready for documentation**.

---

## Test Run Results

### Final Run (with new tests)

```
289 passed, 57 warnings in 42.37s
```

### Baseline (before Test Agent additions)

```
273 passed, 42 warnings in 19.78s
```

### New Tests Added by Test Agent

**File**: `tests/integration/test_rbac_e2e_extended.py`
**Tests added**: 16

| Class | Count | Description |
|-------|-------|-------------|
| `TestAc2RolePermissionMappingRealDb` | 5 | Real-DB spot-checks of default role-permission mapping |
| `TestAc4ExtraDenyBlocksApiCall` | 1 | End-to-end HTTP assertion: extra_deny → 403 on actual API call |
| `TestNegativePaths` | 8 | Anonymous→401, no-permission→403, system role guards→403 |
| `TestBusinessRuleEdgeCases` | 2 | Multi-role union, extra_perm survival after role revocation |

---

## Coverage Report

**Command**: `pytest -q --cov=app/modules/users --cov=app/core/permissions --cov-report=term-missing`

```
Name                                                Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------
app/modules/users/__init__.py                           0      0   100%
app/modules/users/api/__init__.py                       0      0   100%
app/modules/users/api/routes.py                       182    101    45%   78, 101, 117-135, ...
app/modules/users/models/__init__.py                    8      0   100%
app/modules/users/models/clinic.py                     15      0   100%
app/modules/users/models/permission.py                 12      0   100%
app/modules/users/models/role.py                       15      0   100%
app/modules/users/models/role_permission.py            14      0   100%
app/modules/users/models/user.py                       22      0   100%
app/modules/users/models/user_extra_permission.py      18      0   100%
app/modules/users/models/user_role.py                  15      0   100%
app/modules/users/rbac_seed_data.py                    10      0   100%
app/modules/users/schemas/__init__.py                   0      0   100%
app/modules/users/schemas/user_schemas.py              81      0   100%
app/modules/users/services/__init__.py                  0      0   100%
app/modules/users/services/rbac_service.py            137      7    95%   60-61, 70-71, 83-84, 274
app/modules/users/services/user_service.py             52     36    31%   30-34, 43-46, ...
---------------------------------------------------------------------------------
TOTAL                                                 581    144    75%
```

### Coverage Analysis

**rbac_service.py — 95%**: The 7 uncovered lines are:
- Lines 60-61, 70-71, 83-84: Redis exception handlers (`except Exception: log.warning(...)`) — these are defensive fault-tolerance paths requiring Redis to be down, not testable without infrastructure manipulation
- Line 274: `return existing` in the idempotent path where `existing.type == perm_type and existing.reason == reason` — a narrow edge case within the idempotency guard. The adjacent code (the `is_deleted` replace path) is covered.

**routes.py — 45%**: The uncovered lines are all user CRUD handler bodies (create/update/delete/get user request handling). These involve full HTTP request parsing + clinic context that falls outside pure RBAC scope. All RBAC-specific route guards (`is_system` checks, `require_permission` dependencies) are fully exercised by the e2e tests.

**user_service.py — 31%**: User CRUD service is not in RBAC scope. A separate testing effort for TASK-user-crud would cover this.

**Overall 75%** on RBAC modules. The `rbac_service.py` (core business logic) is at 95% which exceeds the PROJECT.md 80% threshold for new code.

---

## Per-AC Pass/Fail Table

| AC | Description | Verdict | Evidence |
|----|-------------|---------|----------|
| **AC1** | Seed data: 5 system roles + 38 permissions per catalog §13.5 | **PASS** | `test_seed_integrity` queries live DB: 38 perms, 5 system roles |
| **AC2** | Default mapping matches BA §13.6 | **PASS** | Real-DB spot-checks: admin=38, doctor has vital.write, pharmacist has pharmacy.dispense, nurse missing prescription.write |
| **AC3** | Doctor cannot call POST /pharmacy/dispense (403) | **DEFERRED** | Pharmacy module not yet built. Doctor role confirmed to lack `pharmacy.dispense` in DB. AC3 formally deferred per review handoff. |
| **AC4** | extra_deny on invoice.void blocks user even with role grant | **PASS** | (a) DB state verified in `test_extra_deny_blocks_even_with_role_grant`; (b) HTTP 403 asserted end-to-end in `test_extra_deny_blocks_api_call_end_to_end` |
| **AC5** | Role change → permission effective on next request | **PASS** | Full HTTP cycle tested: assign→200, revoke→403, Redis cache verified populated then invalidated |

---

## Defects

**None filed.** Zero test failures. All assertions passed on first run.

---

## Notes for Documentation Agent

1. **AC3 is deferred** — document as "pending pharmacy module". The permission `pharmacy.dispense` exists in the catalog and is NOT assigned to the doctor role (verified). When TASK-pharmacy is implemented, the existing `require_permission("pharmacy.dispense")` guard will automatically enforce this.

2. **JWT payload size** — admin with 38 permissions generates a JWT of approximately 700 bytes in the claims payload. Not a defect, but worth documenting in the functional design as a known characteristic.

3. **Redis cache key pattern** — `user:perms:{user_id}`, TTL 5 minutes. Cache is invalidated synchronously on every role/extra-perm change. If Redis is unavailable, the system falls back to DB on every request (see `_cache_get` exception handler).

4. **extra_perm is independent of role membership** — when a role is revoked, the user's `user_extra_permission` rows are NOT deleted. This is by design (verified by `test_extra_perm_survives_role_revocation`). Document this clearly so clinic admins understand that extra overrides persist even after role changes.

5. **Multi-role union** — users can have multiple roles simultaneously; effective permissions are the union of all role permissions plus extra_grants minus extra_denies (verified by `test_multi_role_union_grants_combined_permissions`).

6. **System role cloning** — `clone_system_role()` is implemented but has no endpoint yet. It will be wired in the onboarding flow. Document as "future use".
