# Handoff: TASK-002 → Documentation Agent

**From**: Test Agent
**To**: Documentation Agent
**Status**: DOCUMENTING
**Date**: 2026-04-26

---

## Summary

All tests PASSED (148/148). TASK-002 Tenancy + RLS + Audit Log Infrastructure is fully validated and ready for documentation.

---

## Test Results

- **Total tests:** 148 (103 pre-existing + 45 new added this cycle)
- **Pass rate:** 100%
- **Overall coverage:** 81%
- **Commit:** `f90e915` on branch `feature/task-002-tenancy`

### Coverage by TASK-002 Module

| Module | Coverage |
|--------|---------|
| `app/core/tenancy.py` | 95% |
| `app/core/rls.py` | 100% |
| `app/core/db_security.py` | 100% |
| `app/modules/audit/models/audit_log.py` | 100% |
| `app/core/audit.py` | 69% |

Note on `audit.py` 69%: Lines 311-368 (the `_after_flush` event listener body) require a `__auditable__` model with a real DB table. No such model exists until TASK-005. Coverage will reach 90%+ when TASK-005 (User model) lands.

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| AC1 | Clinic A user sees only clinic A data via RLS | PASSED |
| AC2 | Superuser (cms) bypasses RLS | PASSED |
| AC3 | CREATE/UPDATE/DELETE writes audit_log with diff | PASSED |
| AC4 | UPDATE on audit_log rejected by trigger | PASSED |
| AC5 | Async audit p99 < 5% | DEFERRED (sync v1, documented) |

---

## Key Deliverables

- **Test report:** `docs/tasks/TASK-002/deliveries/test-reports/test-report.md`
- **Test catalog:** `docs/tasks/TASK-002/deliveries/test-cases/test-catalog.md`
- **Source code:** `clinic-cms/` on `feature/task-002-tenancy` (commit `f90e915`)

---

## Documentation Scope

The Documentation Agent should document:

1. **Multi-tenancy middleware** (`app/core/tenancy.py`)
   - Auth flow (dev headers → JWT → whitelist)
   - ContextVars: `current_clinic_id`, `current_user_id`, `current_request_id`
   - Security model (dev vs production environments)

2. **RLS infrastructure** (`app/core/rls.py` + migration 0003)
   - `apply_rls_with_tenant_isolation(op, table)` migration helper
   - How to add RLS to new business tables (TASK-005+)
   - Two-role topology (cms superuser + cms_app restricted)

3. **Audit log** (`app/core/audit.py` + `app/modules/audit/`)
   - `write_audit()` API for service-layer manual audit events
   - `audit_read()` for sensitive read logging
   - `__auditable__ = True` / `__audit_exclude__` pattern for models
   - PII redaction via `_ALWAYS_REDACT` + per-model exclude

4. **DB security** (`app/core/db_security.py`)
   - `check_db_role_security()` startup check
   - Production deployment requirement: `cms_app` role

5. **Deployment guide** (`docs/deployment/database-roles.md` — exists, may need update)

---

## Notes for Documentation Agent

- The `docs/deployment/database-roles.md` file was added in iter 2 — verify it's comprehensive
- The `.claude/agents/code-implementation.md` guide was updated with `__audit_exclude__` pattern
- AC5 deferral should be documented in the audit module docs as "Phase 2 — Arq queue"
- The `NULL clinic_id` policy allowance in RLS is intentional for `audit_log` system events (see review m1 in `handoff/review-report.md`)
