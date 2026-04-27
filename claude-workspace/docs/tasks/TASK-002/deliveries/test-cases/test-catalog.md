# Test Catalog: TASK-002 — Tenancy + RLS + Audit

**Total tests:** 148 (103 pre-existing + 45 new)  
**All passing:** 2026-04-26  
**Branch:** `feature/task-002-tenancy`

---

## New Tests (this cycle — 45 tests)

### `tests/integration/test_tenant_isolation_full.py` (3)

| # | Test | Description |
|---|------|-------------|
| 1 | `TestTenantIsolationE2E::test_clinic_a_sees_only_own_audit_rows` | AC1: cms_app role with clinic_a context cannot see clinic_b audit rows |
| 2 | `TestTenantIsolationE2E::test_clinic_b_sees_only_own_audit_rows` | AC1 symmetric: cms_app role with clinic_b context cannot see clinic_a audit rows |
| 3 | `TestTenantIsolationE2E::test_write_audit_sets_clinic_id_from_contextvar` | write_audit() captures clinic_id from ContextVar into audit_log row |

### `tests/integration/test_audit_lifecycle.py` (5)

| # | Test | Description |
|---|------|-------------|
| 4 | `TestAuditLifecycle::test_create_audit_row_written` | INSERT action: new_data set, old_data NULL, clinic_id from ContextVar |
| 5 | `TestAuditLifecycle::test_update_audit_row_with_diff` | UPDATE action: old_data, new_data, changed_fields populated |
| 6 | `TestAuditLifecycle::test_delete_audit_row_with_old_data` | DELETE action: old_data set, new_data NULL |
| 7 | `TestAuditLifecycle::test_update_changed_fields_accuracy` | changed_fields lists only fields that changed (not all fields) |
| 8 | `TestAuditLifecycle::test_pii_field_not_auto_redacted_by_write_audit` | write_audit() passes data as-is; redaction is in event listener path |

### `tests/integration/test_rls_admin_bypass.py` (4)

| # | Test | Description |
|---|------|-------------|
| 9 | `TestRLSAdminBypass::test_superuser_sees_all_rows_regardless_of_clinic_context` | AC2: cms superuser bypasses RLS — sees rows from all clinics |
| 10 | `TestRLSAdminBypass::test_restricted_role_blocked_by_rls` | cms_app restricted role is blocked by RLS |
| 11 | `TestRLSAdminBypass::test_cms_role_is_superuser` | Confirms cms role has rolsuper=true (by-design topology) |
| 12 | `TestRLSAdminBypass::test_cms_app_role_is_not_superuser` | Confirms cms_app role has rolsuper=false (restricted topology) |

### `tests/integration/test_request_id_e2e.py` (6)

| # | Test | Description |
|---|------|-------------|
| 13 | `TestRequestIdE2E::test_provided_request_id_echoed_in_response_header` | Custom X-Request-Id echoed verbatim in response |
| 14 | `TestRequestIdE2E::test_generated_request_id_is_valid_uuid` | Auto-generated request_id is valid UUID v4 |
| 15 | `TestRequestIdE2E::test_request_id_in_401_response_header` | 401 responses carry X-Request-Id |
| 16 | `TestRequestIdE2E::test_request_id_in_401_response_body_meta` | 401 body meta.request_id matches X-Request-Id header |
| 17 | `TestRequestIdE2E::test_different_requests_get_different_generated_ids` | Each request gets unique generated ID |
| 18 | `TestRequestIdE2E::test_request_id_in_root_endpoint` | X-Request-Id propagated on root endpoint |

### `tests/integration/test_startup_superuser_warning.py` (5)

| # | Test | Description |
|---|------|-------------|
| 19 | `TestStartupSuperuserWarning::test_superuser_in_production_emits_critical_log` | CRITICAL log emitted when connecting as superuser in production |
| 20 | `TestStartupSuperuserWarning::test_superuser_in_staging_emits_critical_log` | CRITICAL log emitted in any non-development env (staging) |
| 21 | `TestStartupSuperuserWarning::test_development_env_skips_check_entirely` | check_db_role_security is no-op in development (no DB query) |
| 22 | `TestStartupSuperuserWarning::test_non_superuser_in_production_emits_info_log` | Non-superuser in production logs info, no CRITICAL |
| 23 | `TestStartupSuperuserWarning::test_critical_log_event_name` | CRITICAL log event name is `db_role_security_violation` |

### `tests/unit/test_audit_coverage.py` (12)

| # | Test | Description |
|---|------|-------------|
| 24 | `TestIsAuditable::test_true_when_auditable_set` | _is_auditable returns True for __auditable__ = True |
| 25 | `TestIsAuditable::test_false_when_no_auditable_attr` | _is_auditable returns False for plain model |
| 26 | `TestIsAuditable::test_false_when_auditable_false` | _is_auditable returns False for __auditable__ = False |
| 27 | `TestIsAuditable::test_false_for_audit_log_itself` | AuditLog itself is not auditable (prevents infinite loop) |
| 28 | `TestWriteAuditSyncNoneEntityId::test_returns_early_when_entity_id_is_none` | _write_audit_sync exits without session.add if instance.id is None |
| 29 | `TestWriteAuditSyncExceptionPath::test_logs_exception_when_session_add_fails` | session.add() exception swallowed (doesn't break business tx) |
| 30 | `TestWriteAuditExceptionPath::test_swallows_exception_when_flush_fails` | write_audit() catches flush errors, never re-raises |
| 31 | `TestAuditRead::test_audit_read_calls_write_audit_with_read_action` | audit_read() delegates to write_audit with action='READ' |
| 32 | `TestAuditRead::test_audit_read_no_old_new_data` | audit_read() passes no old_data/new_data |
| 33 | `TestAfterFlushListener::test_register_audit_listeners_registers_after_flush` | register_audit_listeners wires after_flush (source inspection) |
| 34 | `TestAfterFlushListener::test_write_audit_sync_insert_path` | _write_audit_sync INSERT: correct AuditLog args built |
| 35 | `TestAfterFlushListener::test_write_audit_sync_delete_path` | _write_audit_sync DELETE: old_data set, new_data None |

### `tests/unit/test_rls_helpers.py` (10)

| # | Test | Description |
|---|------|-------------|
| 36 | `TestApplyRLSWithTenantIsolation::test_enables_rls_on_table` | ENABLE ROW LEVEL SECURITY issued |
| 37 | `TestApplyRLSWithTenantIsolation::test_forces_rls_on_table` | FORCE ROW LEVEL SECURITY issued |
| 38 | `TestApplyRLSWithTenantIsolation::test_creates_tenant_isolation_policy` | CREATE POLICY tenant_isolation with app.current_clinic_id |
| 39 | `TestApplyRLSWithTenantIsolation::test_executes_three_statements` | Exactly 3 SQL statements for apply |
| 40 | `TestApplyRLSWithTenantIsolation::test_table_name_interpolated_correctly` | Table name appears in all statements |
| 41 | `TestRemoveRLS::test_drops_tenant_isolation_policy` | DROP POLICY IF EXISTS tenant_isolation |
| 42 | `TestRemoveRLS::test_disables_force_rls` | NO FORCE ROW LEVEL SECURITY issued |
| 43 | `TestRemoveRLS::test_disables_rls` | DISABLE ROW LEVEL SECURITY issued |
| 44 | `TestRemoveRLS::test_executes_three_statements` | Exactly 3 SQL statements for remove |
| 45 | `TestRemoveRLS::test_table_name_in_remove_sql` | Table name in remove SQL statements |

---

## Pre-existing TASK-002 Tests (from iter 1+2 — 19 tests)

### `tests/unit/test_tenancy_middleware.py`

| Test | Description |
|------|-------------|
| `TestTenancyMiddleware::test_sets_clinic_id_contextvar` | Dev header sets current_clinic_id ContextVar |
| `TestTenancyMiddleware::test_sets_user_id_contextvar` | Dev header sets current_user_id ContextVar |
| `TestTenancyMiddleware::test_whitelist_paths_skip_auth` | Whitelisted paths bypass auth |
| `TestTenancyMiddleware::test_whitelist_regex_rejects_path_traversal` | Regex rejects path traversal attempts |

### `tests/unit/test_audit_writer.py` + `test_audit_event_listener.py`

Various pure-unit tests for _serialize_value, _compute_diff, _model_to_dict, _write_audit_sync, PII redaction, None→value transitions.

### `tests/integration/test_rls_isolation.py`

2-clinic isolation on audit_log table via cms_app role.

### `tests/integration/test_audit_immutable.py`

UPDATE/DELETE on audit_log rejected by PostgreSQL trigger.

### `tests/integration/test_jwt_signature.py`

3 tests: unsigned JWT → 401, wrong-secret JWT → 401, valid signed JWT passes.

### `tests/integration/test_dev_header_gating.py`

3 tests: dev headers blocked in non-dev, allowed in dev.

### `tests/integration/test_audit_pii_redaction.py`

4 tests: password_hash and other PII fields redacted in audit records.

### `tests/integration/test_request_id.py`

6 tests: X-Request-Id propagation (pre-existing).

---

## Pre-existing TASK-001 Tests (84 tests)

Not catalogued here — see TASK-001 test deliverables.
