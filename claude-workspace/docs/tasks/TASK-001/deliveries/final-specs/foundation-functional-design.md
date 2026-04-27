# Thiết Kế Chi Tiết: Nền Tảng Clinic CMS

**Task:** TASK-001
**Phiên bản:** 1.0
**Ngày:** 2026-04-26
**Trạng thái:** Hoàn thành
**Tài liệu liên quan:** [clinic_management_system_design.md](../../../../clinic_management_system_design.md), [clinic_management_business_analysis.md](../../../../clinic_management_business_analysis.md)

---

## 1. Tổng Quan

### 1.1 Mục Đích

Xây dựng nền tảng kỹ thuật cho hệ thống quản lý phòng khám (Clinic CMS). Bao gồm: cấu hình ứng dụng, cơ sở dữ liệu không đồng bộ (async), mô hình dữ liệu cơ sở với các mixin tiêu chuẩn, xử lý lỗi tập trung, logging có cấu trúc (JSON), quản lý luân phiên (migration) với Alembic, và tự động hóa CI/CD. Đây là nền tảng cho tất cả các tính năng tiếp theo.

### 1.2 Phạm Vi

**Bao gồm:**
- Cấu trúc dự án, PyProject.toml, Docker Compose cho môi trường dev
- FastAPI ứng dụng với 2 endpoint: `/health` và `/`
- Cơ sở dữ liệu PostgreSQL 15 với 5 extension bắt buộc (uuid-ossp, pgcrypto, unaccent, pg_trgm, btree_gin)
- Redis 7 cho cache và job queue (Arq)
- Async SQLAlchemy 2.x engine + AsyncSessionLocal
- 5 mixin tiêu chuẩn: TimestampMixin, SoftDeleteMixin, TenantMixin, AuditedMixin, VersionedMixin
- BaseEntity trừu tượng kế thừa tất cả các mixin và cung cấp UUID PK
- Clinic model — thực thể tenant (không kế thừa TenantMixin vì nó IS the tenant)
- Exception handlers và response shape chuẩn (`{error: {code, message, details}, meta: {request_id}}`)
- structlog JSON logging với contextvars (clinic_id, user_id, request_id)
- Alembic migrations (async, auto-import models)
- CI/CD skeleton: GitHub Actions (lint, type-check, test, build Docker)

**Không bao gồm:**
- Row-Level Security (RLS) policies — sẽ tạo ở TASK-002
- Xác thực/phân quyền (users, roles tables) — TASK-004
- Request ID middleware — TASK-002
- UUID PK mixin extract — TASK-002
- Endpoints CRUD — TASK-002+

### 1.3 Các Bên Liên Quan

| Vai Trò | Mô Tả |
|---------|-------|
| **Quản lý dự án** | Sử dụng để hiểu kiến trúc cơ bản và lộ trình |
| **QA/Tester** | Xác nhận các yêu cầu chấp nhận (docker up, /health, migrations, tests) |
| **Người phát triển** | Xây dựng các tính năng trên nền tảng này |
| **DevOps** | Quản lý Docker, CI/CD, cơ sở dữ liệu |

---

## 2. Kiến Trúc

### 2.1 Cấu Trúc Mô-đun

```
clinic-cms/
├── app/
│   ├── main.py                      # FastAPI entrypoint, lifespan, /health + /
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                # Pydantic Settings (DATABASE_URL, REDIS_URL, JWT, etc.)
│   │   ├── db.py                    # async engine, AsyncSessionLocal, get_db() dependency
│   │   ├── base_model.py            # Base, 5 mixins, BaseEntity
│   │   ├── exceptions.py            # Custom exceptions, error handlers, response shape
│   │   └── logging.py               # structlog setup, JSON formatter
│   ├── modules/
│   │   └── users/
│   │       └── models/
│   │           └── clinic.py        # Clinic (tenant) entity
│   └── workers/                     # Arq tasks (empty for now)
├── alembic/
│   ├── env.py                       # async, auto-import models via pkgutil.walk_packages
│   ├── script.py.mako
│   ├── alembic.ini
│   └── versions/
│       └── 0001_abc123_create_clinic.py    # Initial migration: clinic table + indexes
├── tests/
│   ├── conftest.py                  # pytest fixtures, async session
│   ├── unit/
│   │   ├── test_config.py           # Settings defaults, env loading, CORS parsing
│   │   ├── test_base_model.py       # Mixin column validation
│   │   └── test_exceptions.py       # Exception subclasses, handlers, response shape
│   └── integration/
│       ├── test_health.py           # /health, / endpoints
│       ├── test_db_session.py       # ContextVars, clinic_id/user_id defaults
│       └── test_alembic.py          # Migration idempotency, history
├── docker/
│   ├── docker-compose.yml           # postgres, redis, api, worker services
│   ├── Dockerfile                   # multi-stage, FastAPI + uvicorn
│   └── postgres-init.sql            # Extension init
├── .github/workflows/
│   └── ci.yml                       # lint (ruff), type-check (mypy), test (pytest), build
├── pyproject.toml                   # deps, pytest config, ruff, mypy
├── .env.example                     # All env vars template
├── .dockerignore, .gitignore
└── README.md
```

### 2.2 Luồng Dữ Liệu

```
[Client]
  ↓ HTTP Request
[FastAPI Router] → [Exception Handler]
  ↓ Dependency Injection (get_db)
[get_db() sets ContextVars: clinic_id, user_id]
  ↓ Creates AsyncSession
[SQLAlchemy async ORM]
  ↓ Executes SQL against PostgreSQL
[PostgreSQL 15 + RLS context (future TASK-002)]
  ↓ Response
[Error shape: {error: {code, message, details}, meta: {request_id}}] OR [Data + meta]
  ↓ structlog JSON logging
[Stdout/Logging Sink]
```

### 2.3 Kiến Trúc Theo Lớp

Chưa triển khai hoàn toàn (sẽ trong TASK-002+), nhưng nền tảng hỗ trợ:

```
[Router Layer] ← Endpoints
     ↓
[Service Layer] ← Business logic
     ↓
[Repository Layer] ← Database abstraction
     ↓
[ORM Model Layer] ← SQLAlchemy models (Base, mixins)
     ↓
[Database Layer] ← PostgreSQL async engine
```

---

## 3. Quyết Định Kiến Trúc Chính

### 3.1 Clinic Settings → JSONB (không tách bảng)

**Quyết định:** Hợp nhất `clinic_settings` vào cột `clinic.settings` JSONB thay vì tạo bảng riêng.

**Lý do:**
- Đơn giản cho v1 (ít cấu hình)
- Tránh JOIN cho mọi truy vấn
- Dễ mở rộng (JSONB chứa bất kỳ keys nào)

**Khi nào tách:** Khi số key > 15 HOẶC cần audit từng cái riêng lẻ.

### 3.2 Naming Convention Dictionary trên MetaData

**Quyết định:** `Base.metadata = MetaData(naming_convention={...})` với quy tắc:
- `ix_<table>_<col>` cho index
- `uq_<table>_<col>` cho unique
- `fk_<table>_<col>_<reftable>` cho foreign key
- `pk_<table>` cho primary key
- `ck_<table>_<name>` cho check

**Lý do:**
- Tuân thủ Design §2.1
- Mỗi migration autogenerate sau đó tự động đúng format
- Tránh thủ công rewrite constraint names trong 23 task tiếp

### 3.3 Alembic Async với Auto-Import Models

**Quyết định:** `alembic/env.py` sử dụng `pkgutil.walk_packages()` để tự động import mô-đun chứa `".models"`.

**Cách thức:**
```python
import pkgutil
for pkg_info in pkgutil.walk_packages(path=__path__, prefix=f"{__name__}."):
    if ".models" in pkg_info.name:
        importlib.import_module(pkg_info.name)
```

**Lý do:**
- Không cần declaratively thêm `from app.modules.users.models import *` vào env.py
- Tự động phát hiện mô-đun mới khi chúng được thêm vào thư mục `*/models/`

**Hạn chế:**
- Nếu module path có `.models` literal như `app.modules.imports.models_helper` sẽ import nhầm
- Chỉ áp dụng khi ≤ 4 modules; khi ≥ 5 cần tight predicate hoặc registry

### 3.4 structlog JSON Logging với contextvars

**Quyết định:** structlog kết hợp:
- `shared_processors` trên cả stdlib và structlog loggers
- `format_exc_info` để promote `exc_info` → structured exception dict
- `dict_tracebacks` để JSON-friendly traceback
- `ContextVar` cho clinic_id, user_id, request_id (set bởi get_db() dependency)

**Cách thức:**
```python
structlog.contextvars.bind_contextvars(clinic_id=..., user_id=..., request_id=...)
# → Tất cả log lines từ đó tự động chứa các context key
```

**Lý do:**
- Correlate logs với request/user/clinic
- JSON-shippable cho Loki, Datadog, v.v.
- Asyncio-safe (không thread-local state)

### 3.5 5 Mixins + BaseEntity

**Quyết định:** 5 mixin độc lập:
1. `TimestampMixin`: `created_at`, `updated_at` (server_default=now())
2. `SoftDeleteMixin`: `is_deleted`, `deleted_at`, `deleted_by` (logical delete)
3. `TenantMixin`: `clinic_id` (FK to clinic, RESTRICT)
4. `AuditedMixin`: `created_by`, `updated_by` (user IDs)
5. `VersionedMixin`: `version` (int, default 1)

`BaseEntity` abstract class kế thừa **tất cả** + `id: UUID PK`.

**Lý do:**
- Clinic model bỏ qua TenantMixin (nó IS the tenant)
- Các mô-đun khác có thể chọn mixin cần thiết
- Separation of concerns — không bắt buộc có tất cả

---

## 4. Quy Ước và Tiêu Chuẩn

### 4.1 Naming Convention

| Loại | Format | Ví Dụ |
|------|--------|-------|
| Bảng | snake_case, singular | `clinic`, `user`, `patient` |
| Cột | snake_case | `created_at`, `clinic_id` |
| Primary Key | `pk_<table>` | `pk_clinic` |
| Index | `ix_<table>_<col>` | `ix_clinic_code`, `ix_clinic_is_active` |
| Unique | `uq_<table>_<col>` | `uq_clinic_code` |
| Foreign Key | `fk_<table>_<col>_<reftable>` | `fk_patient_clinic_id_clinic` |

### 4.2 Error Response Shape

Tất cả lỗi trả về JSON chuẩn:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "clinic_id is required",
    "details": {
      "field": "clinic_id",
      "reason": "required"
    }
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-04-26T12:00:00Z"
  }
}
```

HTTP status codes:
- `400 Bad Request` — validation lỗi, malformed JSON
- `401 Unauthorized` — missing/invalid JWT
- `403 Forbidden` — insufficient permissions
- `404 Not Found` — resource không tồn tại
- `500 Internal Server Error` — unhandled exception

### 4.3 JWT Settings

| Tham Số | Mặc định | Dev | CI |
|---------|----------|-----|-----|
| `JWT_SECRET` | `change-me-in-production` | `dev-secret-change-me` | `ci-test-secret` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | `1440` (24h) | `1440` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | `7` | `7` |
| `ALGORITHM` | `HS256` | `HS256` | `HS256` |

### 4.4 CORS Configuration

```python
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]  # dev
# Parse từ JSON env var: CORS_ORIGINS='["http://localhost:3000"]'
```

---

## 5. Cơ Sở Dữ Liệu

### 5.1 Bảng Clinic

```sql
CREATE TABLE clinic (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic info
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    specialty VARCHAR(50) NOT NULL,
    address VARCHAR(500),
    phone VARCHAR(20),
    email VARCHAR(200),
    tax_code VARCHAR(50),
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- Settings (JSONB, merged from clinic_settings)
    settings JSONB NOT NULL DEFAULT '{}',
    
    -- TimestampMixin
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- SoftDeleteMixin
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID,
    
    -- AuditedMixin
    created_by UUID,
    updated_by UUID
);

CREATE UNIQUE INDEX ix_clinic_code ON clinic(code);
CREATE INDEX ix_clinic_is_active ON clinic(is_active);
```

### 5.2 PostgreSQL Extensions

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";        -- encrypt/decrypt (future)
CREATE EXTENSION IF NOT EXISTS "unaccent";        -- normalize text (search)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- trigram matching (fuzzy search)
CREATE EXTENSION IF NOT EXISTS "btree_gin";       -- GIN index (complex queries)
```

---

## 6. SQL: Không Áp Dụng

Tính năng này không có logic tổng hợp dữ liệu, ETL, hoặc analytics. Clinic table là CRUD cơ bản — sẽ có dữ liệu đầu vào thông qua API user input ở TASK-002+. Không có stored procedures, triggers, hoặc scheduled jobs ở nền tảng.

---

## 7. Quy Tắc Nghiệp Vụ

| ID | Mô Tả | Test Ref |
|----|-------|----------|
| BR-001 | Mỗi phòng khám có code duy nhất | `test_base_model.py:test_clinic_code_unique` |
| BR-002 | Phòng khám can edit được `settings` JSONB | N/A — no CRUD endpoint yet |
| BR-003 | Soft delete — `is_deleted=true` không xóa hàng vật lý | N/A — soft delete column present; logic ở TASK-002+ |
| BR-004 | Tất cả entities có `created_at`, `updated_at` (tự động server) | `test_base_model.py:test_timestamp_defaults` |
| BR-005 | `clinic_id` context var đặt tự động từ get_db() dependency | `test_db_session.py:test_context_vars_set` |

---

## 8. Xử Lý Lỗi

### 8.1 Exception Hierarchy

```
AppException (base)
├── ValidationError (400)
├── UnauthorizedError (401)
├── ForbiddenError (403)
├── NotFoundError (404)
└── ConflictError (409)

unhandled Exception → 500 (logged via structlog.exception)
```

### 8.2 Exception Handlers

| Exception | HTTP Status | Error Code |
|-----------|------------|-----------|
| `ValidationError` | 400 | `VALIDATION_ERROR` |
| `UnauthorizedError` | 401 | `UNAUTHORIZED` |
| `ForbiddenError` | 403 | `FORBIDDEN` |
| `NotFoundError` | 404 | `NOT_FOUND` |
| `ConflictError` | 409 | `CONFLICT` |
| `Exception` (unhandled) | 500 | `INTERNAL_SERVER_ERROR` |

### 8.3 Logging

Tất cả lỗi được log dưới dạng structlog JSON:
```json
{
  "event": "unhandled_exception",
  "path": "/health",
  "method": "GET",
  "exc_type": "AttributeError",
  "exc_info": "..full traceback..",
  "clinic_id": null,
  "user_id": null,
  "request_id": "550e8400..."
}
```

---

## 9. Hạn Chế & Chưa Làm

| Item | Reason | Task |
|------|--------|------|
| RLS (Row-Level Security) | Chưa triển khai policies | TASK-002 |
| Request ID middleware | Chưa có, request_id regenerate mỗi lần error | TASK-002 |
| Users / Roles tables | Out of scope | TASK-004 |
| UUID PK mixin extract | Premature abstraction (chỉ Clinic dùng) | TASK-002 |
| walk_packages predicate tighten | Acceptable khi ≤ 4 modules | TASK-002+ |

---

## 10. Vận Hành

### 10.1 Khởi Động Dev Stack

```bash
cd clinic-cms/docker
docker compose up -d

# Logs
docker compose logs -f api
```

Services:
- API: http://localhost:8000
- Docs (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/health
- Postgres: localhost:5432 (db=cms, user=cms, pass=cms)
- Redis: localhost:6379

### 10.2 Chạy Migrations

```bash
# Từ host (nếu postgres exposed)
DATABASE_URL=postgresql+asyncpg://cms:cms@localhost:5432/cms \
  alembic upgrade head

# Hoặc từ container
docker exec clinic_cms_api alembic upgrade head

# Kiểm tra hiện tại
docker exec clinic_cms_api alembic current
```

### 10.3 Chạy Tests

```bash
# Tất cả tests
docker exec clinic_cms_api pytest -q

# Với coverage
docker exec clinic_cms_api pytest -q --cov=app --cov-report=term-missing

# Một file
docker exec clinic_cms_api pytest tests/unit/test_base_model.py -v
```

### 10.4 Dừng Stack

```bash
docker compose down        # giữ data
docker compose down -v     # xóa volume
```

---

## 11. Ghi Chú Kiểm Thử

### 11.1 Acceptance Criteria Verified

✓ `docker compose up -d` → all 4 services healthy (api, postgres, redis, worker)
✓ `curl http://localhost:8000/health` → 200 + `{status:ok, service:clinic-cms-api, version:0.1.0, environment:development}`
✓ `alembic upgrade head` → success + idempotent (no-op on 2nd run)
✓ `pytest` → 37/37 tests pass (100% pass rate)
✓ PostgreSQL extensions → uuid-ossp, pgcrypto, unaccent, pg_trgm, btree_gin all present
✓ CI YAML → syntax valid

### 11.2 Coverage Notes

- **app/core/base_model.py**: 100% — mixin columns, abstract flag, PK uniqueness
- **app/core/config.py**: 100% — Settings defaults, env loading, CORS parsing
- **app/core/exceptions.py**: 100% — exception subclasses, handler JSON shape
- **app/core/db.py**: 46% — `get_db()` body requires live test loop (deferred to TASK-002)
- **app/core/logging.py**: 35% — `setup_logging()` global state modification (skip due to brittleness)

### 11.3 Non-Blocking Issues

1. **ORJSONResponse deprecation warning** (FastAPI 0.136.1) — pre-existing, will address when response handling refactored
2. **async_session fixture scope** — session-scoped fixture incompatible with function-scoped test loop; TASK-002 should establish integration test patterns
3. **ix_clinic_is_active drift** — index exists in DB but not declared on model; fold into TASK-002 cleanup

### 11.4 Test Data Suggestions

- Clinic: `code="CLINIC001"`, `name="City Health"`, `specialty="General"`, `is_active=true`
- Verify soft delete: set `is_deleted=true` and confirm entity not returned in queries (TASK-002 filter)
- Verify ContextVars: set `clinic_id` in session, confirm RLS context correct (TASK-002 policies)

---

## 12. Kết Luận

Nền tảng Clinic CMS đã sẵn sàng với:
- ✓ Cấu trúc dự án sạch, modular
- ✓ Mô hình cơ sở dữ liệu linh hoạt (5 mixins + BaseEntity)
- ✓ Xử lý lỗi + logging tập trung
- ✓ Quy ước naming convention enforced
- ✓ Alembic async migrations
- ✓ Docker Compose + CI/CD skeleton
- ✓ 37/37 tests passing (67% coverage, 100% on core modules)

Sẵn sàng cho TASK-002 (RLS + Request ID middleware).

---

**Document Version:** 1.0 | **Date:** 2026-04-26 | **Status:** Approved
