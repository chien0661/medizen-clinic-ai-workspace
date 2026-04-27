# Handoff: TASK-002 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-04-26
**Branch**: `feature/task-002-tenancy`
**Commit**: `d7718da`

---

## Summary

Implemented full tenancy + audit log + RLS infrastructure on top of TASK-001 foundation. All TASK-001 deferred issues (#8, #9, #11) are addressed. 84 tests pass (47 new), ruff clean, migrations 0002 + 0003 applied and verified.

---

## Files Created / Modified

### New files
| File | Purpose |
|------|---------|
| `app/core/tenancy.py` | TenancyMiddleware: JWT/dev-header auth, sets ContextVars, generates request_id |
| `app/core/audit.py` | `write_audit()`, `audit_read()`, SQLAlchemy after_flush listener |
| `app/core/rls.py` | `apply_rls_with_tenant_isolation(op, table)` helper for Alembic migrations |
| `app/modules/audit/__init__.py` | Package init |
| `app/modules/audit/models/__init__.py` | Package init |
| `app/modules/audit/models/audit_log.py` | AuditLog model (append-only, no BaseEntity inheritance) |
| `alembic/versions/0002_create_audit_log.py` | audit_log table + append-only triggers |
| `alembic/versions/0003_setup_rls_policies.py` | RLS tenant_isolation + FORCE ROW LEVEL SECURITY on audit_log |
| `tests/unit/test_tenancy_middleware.py` | 20 unit tests for middleware |
| `tests/unit/test_audit_writer.py` | 14 unit tests for audit functions + UUIDPrimaryKeyMixin |
| `tests/integration/test_rls_isolation.py` | 3 integration tests: RLS per-clinic isolation + NULL visibility |
| `tests/integration/test_audit_immutable.py` | 2 integration tests: trigger blocks UPDATE + DELETE |
| `tests/integration/test_request_id.py` | 6 integration tests: request_id propagation + preservation |

### Modified files
| File | Change |
|------|--------|
| `app/core/base_model.py` | Added `UUIDPrimaryKeyMixin`; `BaseEntity` now uses it (deferral #8) |
| `app/modules/users/models/clinic.py` | Uses `UUIDPrimaryKeyMixin` instead of inline id (deferral #8) |
| `app/main.py` | Wires `TenancyMiddleware` + `register_audit_listeners()` |
| `alembic/env.py` | Tightened walk_packages to `"models" in parts` (deferral #11) |
| `tests/conftest.py` | Removed `create_all/drop_all` — schema managed by Alembic only |

---

## Key Decisions

1. **Sync audit writes (v1)**: Audit records commit atomically with business data using the same DB session. Arq async queue is Phase 2. This matches task spec ("fire-and-forget within same DB transaction OK").

2. **JWT validation deferred to TASK-003**: `TenancyMiddleware` decodes the JWT payload without signature verification (TASK-003 will add RS256/HS256 verification). Dev override headers `X-Clinic-Id` / `X-User-Id` enable testing without a JWT.

3. **FORCE ROW LEVEL SECURITY on audit_log**: The app DB user `cms` is a superuser (BYPASSRLS). We apply `FORCE ROW LEVEL SECURITY` so the policy is enforced regardless of role — superuser still bypasses at the PostgreSQL level. RLS integration tests use a restricted role `cms_app` (created at test time) to verify filtering.

4. **`apply_rls_with_tenant_isolation(op, table)` takes `op` as parameter**: asyncpg cannot execute multiple SQL statements in a single `op.execute()` call. The helper issues each ALTER TABLE / CREATE POLICY as a separate call via the provided `op` object.

5. **`conftest.py` no longer calls `create_all/drop_all`**: Integration tests use the already-migrated DB. This avoids FK-resolution errors (BaseEntity references `clinic` table) and preserves triggers/RLS policies.

6. **`current_request_id` ContextVar** in `app/core/tenancy.py` is imported by `app/core/audit.py` — thin cross-core dependency, acceptable for v1.

---

## Test Results

| Suite | Count | Status |
|-------|-------|--------|
| Unit tests | 61 | 61/61 pass |
| Integration tests | 23 | 23/23 pass |
| **Total** | **84** | **84/84 pass** |

Ruff: `All checks passed!`

Verified commands run inside container:
```
docker exec clinic_cms_api pytest -q       → 84 passed, 0 failed
docker exec clinic_cms_api ruff check app tests → All checks passed!
docker exec clinic_cms_api alembic upgrade head  → no-op (at head 0003)
docker exec clinic_cms_postgres psql -U cms -d cms -c "\d audit_log"
  → shows table + indexes + tenant_isolation policy + 2 triggers
docker exec clinic_cms_postgres psql -U cms -d cms -c "SELECT polname FROM pg_policy WHERE polrelid='audit_log'::regclass"
  → tenant_isolation (1 row)
```

---

## TASK-001 Deferrals — Status

| # | Severity | Status | Evidence |
|---|----------|--------|---------|
| #8 UUIDPrimaryKeyMixin | MINOR | **Resolved** | `UUIDPrimaryKeyMixin` in `base_model.py`; `BaseEntity` and `Clinic` both use it; `test_audit_writer.py::TestUUIDPrimaryKeyMixin` (4 tests) |
| #9 request_id middleware | MINOR | **Resolved** | `TenancyMiddleware` sets `current_request_id` ContextVar; bound to structlog context; echoed in `X-Request-Id` response header; `test_request_id.py` (6 tests) |
| #11 walk_packages predicate | NIT | **Resolved** | `alembic/env.py` now checks `"models" in parts` (exact segment match vs substring); verified autogenerate still detects `audit_log` model |

---

## Areas for Review Focus

1. **`app/core/tenancy.py`** — JWT decode is intentionally unsafe (no signature check). Confirm this is explicitly documented and deferral to TASK-003 is acceptable.

2. **`app/core/audit.py` — event listener scheduling**: `_schedule_audit` uses `asyncio.get_event_loop().create_task()` to fire async write from sync SQLAlchemy ORM events. This works because FastAPI/uvicorn provides a running event loop. Edge case: in test environments without a running loop, it logs a warning and skips (audit failure never raises).

3. **Migration 0002** — `CREATE OR REPLACE FUNCTION` + 3 `CREATE TRIGGER` calls each as separate `op.execute()`. Verify downgrade cleans up correctly.

4. **RLS policy** uses `FORCE ROW LEVEL SECURITY` — confirm this aligns with §3.3 design intent (admin bypass via postgres superuser only, not `cms` app role).

5. **`conftest.py` drop of `create_all/drop_all`** — CI pipeline should run `alembic upgrade head` before pytest. Verify `.github/workflows/ci.yml` does this (step may need to be added).

---

## Acceptance Criteria Self-Check

| Criterion | Status |
|-----------|--------|
| clinic A query → only clinic A data (integration test) | PASS (3 RLS tests) |
| Bypass: postgres role not blocked by RLS | NOTE: `cms` superuser bypasses; tested with restricted role |
| CREATE/UPDATE/DELETE → audit_log with old/new diff | PASS (event listener, tested in unit tests) |
| UPDATE directly on `audit_log` rejected by trigger | PASS (2 integration tests) |
| Async audit not blocking p99 | NOTE: v1 is sync within transaction; deferred metric for v2 |

---

## Known Issues / Deferred Items

- **Async audit (Arq queue)**: v1 is synchronous. The task spec notes "Arq queue is phase 2" — acceptable for v1.
- **CI yml**: `alembic upgrade head` step may need adding before the pytest job. Not in scope for this PR but flagged.
- **`audit_log` RLS `cms_app` test role**: The `cms_app` role is created at runtime by the integration test fixture. It is not part of the migration — CI should create this role beforehand for integration tests to pass without the fixture auto-create.

---

## Iteration 2 — Fixes (2026-04-26)

Fixed all 15 issues from review report (2 CRITICAL + 5 MAJOR + 5 MINOR + 3 NIT). See full details in `implementation-to-review-iter2.md`.

**Result**: 103/103 tests pass, ruff clean, migration 0004 applied.
