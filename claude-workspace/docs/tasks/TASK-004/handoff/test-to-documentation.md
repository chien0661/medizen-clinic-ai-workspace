# Handoff: TASK-004 → Documentation Agent

**From**: Test Agent
**To**: Documentation Agent
**Status**: DOCUMENTING
**Date**: 2026-04-27
**Branch**: `feature/task-004-rbac`
**HEAD**: `afb922a`

---

## Summary

All 289 tests PASSED (289/289, 0 failures). RBAC implementation is fully validated and ready for documentation.

The Test Agent added 16 new end-to-end tests in `tests/integration/test_rbac_e2e_extended.py` covering gaps identified in the review handoff. These tests operate against the real PostgreSQL + Redis stack with no mocks.

---

## Test Results

| Metric | Value |
|--------|-------|
| Total tests | 289 |
| Passed | 289 |
| Failed | 0 |
| New tests added | 16 |
| Test duration | ~42s |
| Environment | Docker: Python 3.11.15, PostgreSQL 15, Redis 7 |

**Test report**: `docs/tasks/TASK-004/deliveries/test-reports/rbac-test-report.md`
**Test cases**: `docs/tasks/TASK-004/deliveries/test-cases/rbac-test-cases.md`

---

## Per-AC Verdict

| AC | Description | Verdict |
|----|-------------|---------|
| AC1 | 5 system roles + 38 permissions from seed migration | **PASS** |
| AC2 | Default role-permission mapping per BA §13.6 | **PASS** |
| AC3 | Doctor cannot POST /pharmacy/dispense (403) | **DEFERRED** — pharmacy module not yet built |
| AC4 | extra_deny blocks API call even with role grant | **PASS** |
| AC5 | Role change → permission effective on next request | **PASS** |

---

## Coverage Summary

- `app/modules/users/services/rbac_service.py`: **95%** (core business logic — exceeds 80% threshold)
- `app/modules/users/api/routes.py`: **45%** (RBAC guards fully covered; user CRUD handler bodies not in RBAC scope)
- All RBAC models + schemas: **100%**
- Overall RBAC module coverage: **75%**

---

## Key Behaviors Discovered / Confirmed During Testing

The Documentation Agent should ensure these behaviors are clearly documented in the functional design:

### 1. AC3 is Deferred
The pharmacy module (`POST /pharmacy/dispense`) does not exist yet. Doctor role correctly lacks `pharmacy.dispense` in the DB (verified). AC3 will close automatically when the pharmacy module ships. Document this as "pending pharmacy module implementation".

### 2. JWT Payload Size
Admin users carry all 38 permission codes in their JWT payload (~700 bytes in the claims). This is a known, accepted trade-off (see review handoff item m1). Document in the functional design as a design decision.

### 3. Redis Cache Pattern
- Key: `user:perms:{user_id}`, TTL: 5 minutes
- Cache is invalidated **synchronously** on every role/extra-perm change
- On Redis failure: falls back to DB on each request (graceful degradation)
- Document this in the API spec / operational guide

### 4. extra_perm Independence
`user_extra_permission` rows are **not deleted** when a user's roles change. Per-user overrides persist independently of role membership. This is by design (confirmed by `test_extra_perm_survives_role_revocation`). This behavior should be explicitly documented for clinic admins.

### 5. Multi-Role Union
A user can hold multiple roles simultaneously. Effective permissions = union of all role permissions + extra_grants - extra_denies. This is demonstrated by `test_multi_role_union_grants_combined_permissions`.

### 6. System Role Immutability
All five system roles (`admin`, `doctor`, `nurse`, `pharmacist`, `receptionist`) cannot be:
- Deleted (403)
- Modified via PATCH (403)
- Have permissions added (403)
- Have permissions removed (403)

To customize, use `clone_system_role()` (scaffolded, awaiting onboarding endpoint).

### 7. Idempotent Extra Permissions
Calling `POST /users/{id}/extra-permissions` with identical payload twice returns the same record. Calling with a different `type` or `reason` for the same `permission_code` soft-deletes the old record and creates a new one (tested in `test_idempotent_extra_permission`).

---

## Bugs Filed

None.

---

## Files Created by Test Agent

| File | Description |
|------|-------------|
| `clinic-cms/tests/integration/test_rbac_e2e_extended.py` | 16 new real-DB e2e tests |
| `docs/tasks/TASK-004/deliveries/test-cases/rbac-test-cases.md` | AC → test mapping table |
| `docs/tasks/TASK-004/deliveries/test-reports/rbac-test-report.md` | Full test report with coverage |
| `docs/tasks/TASK-004/handoff/test-to-documentation.md` | This file |
