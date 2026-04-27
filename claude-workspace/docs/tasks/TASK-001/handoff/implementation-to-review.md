# Handoff: TASK-001 Foundation → Code Review

**From:** Code Implementation Agent
**To:** Code Review Agent
**Date:** 2026-04-26
**Task:** TASK-001 — Foundation: Project Skeleton, Docker Compose, Base Models, Alembic
**Branch:** feature/task-001-foundation

## Summary

Implemented all TASK-001 deliverables on top of the existing scaffold: async SQLAlchemy engine with RLS context vars, full set of SQLAlchemy mixins, BaseEntity, custom exception hierarchy with FastAPI handlers, structlog JSON logging wired into app startup, async Alembic env.py with model auto-import, initial migration creating the `clinic` table, tests skeleton with 14 passing tests, and GitHub Actions CI workflow.

## Changes

**Files Added:**
- `app/core/db.py` — async engine, AsyncSessionLocal, `current_clinic_id`/`current_user_id` ContextVars, `get_db()` dependency
- `app/core/base_model.py` — `Base`, `TimestampMixin`, `SoftDeleteMixin`, `TenantMixin`, `AuditedMixin`, `VersionedMixin`, `BaseEntity`
- `app/core/exceptions.py` — `AppException` + 5 subclasses (`NotFoundError`, `ConflictError`, `ForbiddenError`, `BusinessRuleError`, `OptimisticLockError`), `register_exception_handlers()`
- `app/core/logging.py` — structlog JSON setup, `setup_logging()`, `get_logger()`
- `app/modules/__init__.py`, `app/modules/users/__init__.py`, `app/modules/users/models/__init__.py` — package init files
- `app/modules/users/models/clinic.py` — `Clinic` SQLAlchemy model (tenant entity)
- `alembic/versions/0001_abc123_create_clinic.py` — migration creating `clinic` table
- `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`
- `tests/conftest.py` — session-scoped event_loop, async_engine, async_session (transactional rollback), ASGI client fixture
- `tests/unit/test_config.py` — 3 tests verifying Settings load
- `tests/unit/test_base_model.py` — 8 tests verifying mixin columns
- `tests/integration/test_health.py` — 3 tests for /health and / endpoints
- `.github/workflows/ci.yml` — lint (ruff), type-check (mypy), test (pytest w/ postgres+redis services), build-image

**Files Modified:**
- `alembic/env.py` — replaced placeholder with full async setup; auto-imports all `*.models.*` modules under `app.modules`; reads DATABASE_URL from settings; supports offline + online (async) modes; `compare_type=True`
- `app/main.py` — wired in `setup_logging()` in lifespan, `register_exception_handlers()`
- `Dockerfile` — changed `pip install .` to `pip install ".[dev]"` so pytest/ruff/mypy available in image; added `COPY tests` and `COPY pyproject.toml`
- `docker/docker-compose.yml` — added volume mounts for `tests/` and `pyproject.toml` on api service so tests are accessible without image rebuild
- `README.md` — added Architecture, Local development, Running migrations, Running tests, Project layout sections

## Key Design Decision: clinic_settings merged into clinic

The task spec noted that `clinic_settings` JSONB might be merged into `clinic.settings` for v1 simplicity. **Decision: merged.** The `Clinic` model has a `settings: JSONB` column. A separate `clinic_settings` table can be split out later if the settings schema grows.

This is reflected in:
- The `Clinic` model docstring
- The migration column comment
- Task notes (see below)

## Tests

### Unit Tests
- **Total Tests:** 14 (11 unit + 3 integration)
- **Status:** 14 passing, 0 failing
- **Coverage:** Not measured (foundation pass; coverage thresholds apply from TASK-002 onward)
- **New Test Files:**
  - `tests/unit/test_config.py` (3 tests)
  - `tests/unit/test_base_model.py` (8 tests — one for each mixin + abstract + declarative base)
  - `tests/integration/test_health.py` (3 tests)

## Dependencies

No new dependencies added — all were already declared in `pyproject.toml` from the initial scaffold.

## Configuration Changes

No new environment variables. Existing: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `ENVIRONMENT`, `DEBUG`.

## Notes

- **ORJSONResponse deprecation warning**: FastAPI >=0.115 shows a deprecation warning for `ORJSONResponse` as a `default_response_class`. This warning appears in test output but does not cause failures. Removing it is a small cleanup the reviewer may want to flag for TASK-002+.
- **pytest in container**: The Dockerfile now installs dev deps (`.[dev]`). For the currently running container (built before this change), `pip install pytest pytest-asyncio httpx` was applied manually. A `docker compose build api` will bake pytest into future images.
- **RLS not enabled**: Context vars set `SET LOCAL app.current_clinic_id` on the session, but no RLS policies exist yet — those are deferred to migration `0014_setup_rls_policies.py` (TASK-002).
- **No user/role tables**: Intentionally not created — those belong to TASK-004.

## Review Focus Areas

1. **`app/core/exceptions.py`** — exception handler registration order; verify `AppException` handler takes priority over generic `Exception` handler.
2. **`alembic/env.py`** — `pkgutil.walk_packages` auto-import pattern; ensure it correctly discovers future model packages as modules are added.
3. **`tests/conftest.py`** — session-scoped `event_loop` fixture compatibility with pytest-asyncio 1.3.0 (tested: passes without warning).
4. **`app/modules/users/models/clinic.py`** — verify `Clinic` does NOT inherit `TenantMixin`/`BaseEntity` (correct: clinic is the tenant root, not a child entity).
5. **Migration `0001`** — indexes: `ix_clinic_code` (unique), `ix_clinic_is_active`. Review if additional indexes are needed for common query patterns.

## Related Documentation

- Detail Design: `E:/MyProject/clinic-cms-workspace/docs/clinic_management_system_design.md` — §2 (Conventions), §3 (Database Foundation), §4.1 (Clinic model)
- Task: `E:/MyProject/clinic-cms-workspace/claude-workspace/docs/tasks/TASK-001/task.md`

---

## Iteration 2 — Fixes (2026-04-26)

**From:** Code Implementation Agent (fix mode)
**Responding to:** `handoff/review-report.md` — CHANGES_REQUESTED (11 issues)
**Commit:** `fix(foundation): address review issues from iteration 1 (TASK-001)`

### Issues Fixed

| # | Severity | File | Fix Applied |
|---|---|---|---|
| 1 | CRITICAL | `tests/conftest.py` | `TEST_DATABASE_URL` now reads `os.environ.get("DATABASE_URL", "...localhost...")` — works in Docker, CI, and host |
| 2 | CRITICAL | `.dockerignore` | Removed `tests/` line — Dockerfile `COPY tests /app/tests` now succeeds |
| 3 | MAJOR | `app/core/exceptions.py` | Added `log.exception("unhandled_exception", path=..., method=..., exc_type=...)` before returning 500 response |
| 4 | MAJOR | `app/core/base_model.py` | Added `NAMING_CONVENTION` dict + `metadata = MetaData(naming_convention=NAMING_CONVENTION)` to `Base`; imports `MetaData` |
| 5 | MAJOR | `app/core/logging.py` | Added `format_exc_info` to `shared_processors`; added `format_exc_info` + `dict_tracebacks` before `renderer` in `ProcessorFormatter` chain |
| 6 | MAJOR | `tests/conftest.py` + `pyproject.toml` | Deleted session-scoped `event_loop` fixture; added `asyncio_default_fixture_loop_scope = "session"` to `[tool.pytest.ini_options]`; removed redundant `@pytest.mark.asyncio` decorators from `test_health.py` |
| 7 | MAJOR | `tests/unit/test_config.py` | Rewrote with: (a) defaults test asserting static fields + isinstance for env-variable ones, (b) `monkeypatch.setenv` env-loading test, (c) `CORS_ORIGINS` JSON parse test |
| 10 | MINOR | `tests/unit/test_config.py`, `tests/unit/test_base_model.py` | Removed unused `import pytest`; also removed `import inspect` and unused mixin imports (F401) that ruff now catches |

### Deferred (per review-to-implementation.md guidance)

- **Issue 8** (`Clinic.id` UUIDPrimaryKeyMixin): Deferred to TASK-002 — DRY refactor, no functional impact now.
- **Issue 9** (`request_id` middleware): Deferred to TASK-002 — real fix requires request-id middleware; noted in `exceptions.py` inline comment.
- **Issue 11** (`pkgutil.walk_packages` predicate): Deferred — tighten to `.endswith(".models")` when ≥5 modules exist.

### Additional Pre-existing Ruff Fixes (discovered during verification)

- `UP035` in `app/core/db.py` and `tests/conftest.py`: `typing.AsyncGenerator` → `collections.abc.AsyncGenerator`
- `SIM108` in `app/core/logging.py`: `if/else` → ternary for `renderer`
- `SIM117` in `tests/conftest.py`: nested `async with` → single `async with session_factory() as session, session.begin()`
- `I001` in `app/modules/users/models/clinic.py`: split JSONB import to fix import sort order
- `N818` on `AppException`: added `# noqa: N818` (intentional naming — renames would break all subclasses)

### Verification Results

- `pytest -q` inside container: **14 passed, 0 failed**
- `ruff check app tests`: **All checks passed**
- `alembic upgrade head`: **no-op (already at head)**
- `docker compose build api`: **Build succeeded**
- No deprecation warnings from pytest-asyncio (event_loop fixture removed)
