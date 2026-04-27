# Test Catalog: TASK-001 — Foundation

**Total tests:** 37 | **Pass rate:** 100%

---

## Unit — Config (`tests/unit/test_config.py`)

| # | Test Name | Description |
|---|---|---|
| 1 | `test_settings_defaults` | Settings has correct algorithm, token expiry defaults, and typed ENVIRONMENT/DEBUG |
| 2 | `test_settings_loads_from_env` | Settings reads DATABASE_URL, JWT_SECRET, ENVIRONMENT, ACCESS_TOKEN_EXPIRE_MINUTES from env vars via monkeypatch |
| 3 | `test_settings_cors_origins_json_parse` | CORS_ORIGINS JSON string in env var is parsed to list correctly |

---

## Unit — Base Model (`tests/unit/test_base_model.py`)

| # | Test Name | Description |
|---|---|---|
| 4 | `test_timestamp_mixin_columns` | BaseEntity has created_at and updated_at columns |
| 5 | `test_soft_delete_mixin_columns` | BaseEntity has is_deleted, deleted_at, deleted_by columns |
| 6 | `test_tenant_mixin_columns` | BaseEntity has clinic_id column |
| 7 | `test_audited_mixin_columns` | BaseEntity has created_by and updated_by columns |
| 8 | `test_versioned_mixin_columns` | BaseEntity has version column |
| 9 | `test_base_entity_has_uuid_pk` | BaseEntity has id as single UUID primary key |
| 10 | `test_base_entity_is_abstract` | BaseEntity.__abstract__ is True |
| 11 | `test_base_is_declarative` | Base is a subclass of DeclarativeBase |

---

## Unit — Exceptions (`tests/unit/test_exceptions.py`)

| # | Test Name | Description |
|---|---|---|
| 12 | `test_not_found_error_defaults` | NotFoundError has code=NOT_FOUND, http_status=404, default message |
| 13 | `test_not_found_error_custom_message` | NotFoundError accepts custom message and details dict |
| 14 | `test_conflict_error_defaults` | ConflictError has code=CONFLICT, http_status=409 |
| 15 | `test_forbidden_error_defaults` | ForbiddenError has code=FORBIDDEN, http_status=403 |
| 16 | `test_business_rule_error_defaults` | BusinessRuleError has code=BUSINESS_RULE_VIOLATION, http_status=400 |
| 17 | `test_optimistic_lock_error_defaults` | OptimisticLockError has code=OPTIMISTIC_LOCK_CONFLICT, http_status=409 |
| 18 | `test_app_exception_is_base` | All concrete exception classes are subclasses of AppException |
| 19 | `test_app_exception_empty_details_default` | details defaults to empty dict (not None) |
| 20 | `test_not_found_handler_status` | NotFoundError handler returns HTTP 404 |
| 21 | `test_not_found_handler_error_shape` | NotFoundError handler returns {error: {code, message, details}} JSON shape |
| 22 | `test_not_found_handler_meta_shape` | NotFoundError handler response includes meta.request_id |
| 23 | `test_conflict_handler_status` | ConflictError handler returns HTTP 409 |
| 24 | `test_unhandled_exception_handler_returns_500` | RuntimeError triggers unhandled_exception_handler returning HTTP 500 |
| 25 | `test_unhandled_exception_handler_error_shape` | 500 response has code=INTERNAL_SERVER_ERROR and meta.request_id |

---

## Integration — Health (`tests/integration/test_health.py`)

| # | Test Name | Description |
|---|---|---|
| 26 | `test_health_returns_200` | GET /health returns HTTP 200 |
| 27 | `test_health_returns_ok_status` | GET /health returns {status: ok, service: clinic-cms-api} |
| 28 | `test_root_returns_200` | GET / returns HTTP 200 with health link |

---

## Integration — DB Context-vars (`tests/integration/test_db_session.py`)

| # | Test Name | Description |
|---|---|---|
| 29 | `test_context_var_clinic_id_default_is_none` | current_clinic_id ContextVar default is None |
| 30 | `test_context_var_user_id_default_is_none` | current_user_id ContextVar default is None |
| 31 | `test_context_var_clinic_id_set_and_reset` | current_clinic_id set/get/reset round-trip works correctly |
| 32 | `test_context_var_user_id_set_and_reset` | current_user_id set/get/reset round-trip works correctly |
| 33 | `test_context_vars_are_independent` | clinic_id and user_id ContextVars are independent (no cross-contamination) |
| 34 | `test_health_endpoint_returns_ok` | Health endpoint reachable via ASGI client (validates app boot + wiring) |

---

## Integration — Alembic (`tests/integration/test_alembic.py`)

| # | Test Name | Description |
|---|---|---|
| 35 | `test_alembic_upgrade_head_is_idempotent` | alembic upgrade head runs twice without error (idempotent) |
| 36 | `test_alembic_current_shows_head` | alembic current reports being at head revision after upgrade |
| 37 | `test_alembic_history_shows_migration` | alembic history lists at least one migration (0001 present) |
