# Hệ thống Quản lý Phòng khám — Thiết kế Hệ thống Chi tiết

> **Phiên bản:** 1.0
> **Tài liệu kèm theo:** [clinic_management_business_analysis.md](./clinic_management_business_analysis.md)
> **Mục đích:** Hướng dẫn chi tiết cho team phát triển — schema, API, workflow, infrastructure

---

## Mục lục

1. [Tổng quan thiết kế](#1-tổng-quan-thiết-kế)
2. [Conventions & Standards](#2-conventions--standards)
3. [Database Foundation](#3-database-foundation)
4. [Module Auth & Users](#4-module-auth--users)
5. [Module Tenancy & Audit](#5-module-tenancy--audit)
6. [Module Patients](#6-module-patients)
7. [Module Appointments & Queue](#7-module-appointments--queue)
8. [Module Visits](#8-module-visits)
9. [Module Vitals (Dynamic Form)](#9-module-vitals-dynamic-form)
10. [Module Services](#10-module-services)
11. [Module Medicines & Inventory](#11-module-medicines--inventory)
12. [Module Prescriptions & Pharmacy](#12-module-prescriptions--pharmacy)
13. [Module Billing](#13-module-billing)
14. [Module HR & Schedule](#14-module-hr--schedule)
15. [RBAC Implementation](#15-rbac-implementation)
16. [Cross-cutting Concerns](#16-cross-cutting-concerns)
17. [API Design Patterns](#17-api-design-patterns)
18. [Critical Workflows](#18-critical-workflows)
19. [Background Jobs](#19-background-jobs)
20. [Offline Sync](#20-offline-sync)
21. [Migration Strategy](#21-migration-strategy)
22. [Testing Strategy](#22-testing-strategy)
23. [Deployment Architecture](#23-deployment-architecture)
24. [Security Checklist](#24-security-checklist)

---

## 1. Tổng quan thiết kế

### 1.1. Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────┐
│                      Tauri Desktop Client                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  React UI  ←→  Local SQLite Cache  ←→  Sync Engine    │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS (REST + JWT)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Reverse Proxy (Nginx)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
┌──────────────────┐              ┌──────────────────┐
│  FastAPI App     │              │  Background      │
│  (Uvicorn x N)   │              │  Workers (Arq)   │
│                  │              │                  │
│  - Routers       │              │  - Notifications │
│  - Services      │              │  - Cron jobs     │
│  - Repositories  │              │  - Sync tasks    │
└────────┬─────────┘              └────────┬─────────┘
         │                                 │
         └────────────┬────────────────────┘
                      ▼
        ┌─────────────────────────────┐
        │  PostgreSQL 15+             │
        │  - RLS bật                  │
        │  - Audit log                │
        │  - Connection pool          │
        └─────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │  Redis                      │
        │  - Session, cache           │
        │  - Job queue                │
        │  - Rate limit               │
        └─────────────────────────────┘
```

### 1.2. Layered architecture (per module)

```
┌─────────────────────────────────────────┐
│  Router (FastAPI)                       │  ← HTTP, validation, auth
│  app/modules/<mod>/api/routes.py        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Service (business logic)               │  ← orchestration, transaction
│  app/modules/<mod>/services/*.py        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Repository (data access)               │  ← queries, no business logic
│  app/modules/<mod>/repositories/*.py    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Model (SQLAlchemy)                     │  ← schema definition
│  app/modules/<mod>/models/*.py          │
└─────────────────────────────────────────┘
```

**Quy tắc:**
- Router KHÔNG truy cập DB trực tiếp, luôn qua Service.
- Service nhận DTO (Pydantic) làm input, trả entity hoặc DTO.
- Repository chỉ chứa query, không có business logic.
- Service có thể gọi Service khác (cross-module), Repository không gọi cross-module.

### 1.3. Cấu trúc thư mục đầy đủ

```
clinic-cms/
├── app/
│   ├── main.py                      # FastAPI app entry
│   ├── core/
│   │   ├── config.py                # Settings, env vars
│   │   ├── db.py                    # Session, engine
│   │   ├── security.py              # JWT, password
│   │   ├── exceptions.py            # Custom exceptions + handlers
│   │   ├── tenancy.py               # Clinic context middleware
│   │   ├── audit.py                 # Audit log mechanism
│   │   ├── permissions.py           # RBAC dependencies
│   │   └── base_model.py            # Base SQLAlchemy class
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── api/
│   │   │   │   └── routes.py
│   │   │   ├── services/
│   │   │   │   └── auth_service.py
│   │   │   ├── repositories/
│   │   │   ├── models/
│   │   │   └── schemas/             # Pydantic
│   │   ├── users/
│   │   ├── patients/
│   │   ├── appointments/
│   │   ├── visits/
│   │   ├── vitals/
│   │   ├── services/                # service catalog
│   │   ├── medicines/
│   │   ├── inventory/
│   │   ├── prescriptions/
│   │   ├── pharmacy/
│   │   ├── billing/
│   │   ├── hr/
│   │   ├── reporting/
│   │   ├── notifications/
│   │   └── admin/
│   ├── integrations/
│   │   └── printer/
│   ├── workers/
│   │   ├── tasks/
│   │   └── scheduler.py
│   └── utils/
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── scripts/
│   └── seed_data.py
├── docker/
├── pyproject.toml
├── alembic.ini
└── README.md
```

---

## 2. Conventions & Standards

### 2.1. Naming

| Loại | Convention | Ví dụ |
|---|---|---|
| Bảng DB | snake_case, số ít | `patient`, `visit`, `prescription_item` |
| Cột | snake_case | `created_at`, `is_active` |
| Foreign key | `<table>_id` | `patient_id`, `clinic_id` |
| Boolean | `is_*` / `has_*` | `is_active`, `has_insurance` |
| Timestamp | `*_at` | `created_at`, `paid_at` |
| Enum | UPPER_SNAKE_CASE values | `WAITING`, `IN_PROGRESS` |
| Index | `ix_<table>_<columns>` | `ix_visit_clinic_id_status` |
| Unique | `uq_<table>_<columns>` | `uq_user_clinic_username` |
| FK constraint | `fk_<table>_<col>_<reftable>` | `fk_visit_patient_id_patient` |
| Class Python | PascalCase | `Patient`, `VisitService` |
| Function/var | snake_case | `get_patient_by_id` |
| Pydantic schema | `<Entity><Action>` | `PatientCreate`, `PatientUpdate`, `PatientResponse` |
| Service class | `<Entity>Service` | `PatientService`, `VisitService` |
| Repository class | `<Entity>Repository` | `PatientRepository` |

### 2.2. URL conventions

```
GET    /api/v1/patients                  # list
POST   /api/v1/patients                  # create
GET    /api/v1/patients/{id}             # get one
PATCH  /api/v1/patients/{id}             # partial update
DELETE /api/v1/patients/{id}             # soft delete

# Sub-resources
GET    /api/v1/patients/{id}/visits      # nested list
POST   /api/v1/visits/{id}/vitals        # create vitals for visit

# Actions (verb)
POST   /api/v1/visits/{id}/start         # bác sĩ nhận ca
POST   /api/v1/visits/{id}/complete      # hoàn tất visit
POST   /api/v1/invoices/{id}/void        # hủy invoice
POST   /api/v1/prescriptions/{id}/dispense  # cấp phát
```

### 2.3. HTTP status codes

| Code | Khi nào |
|---|---|
| 200 OK | GET, PATCH thành công |
| 201 Created | POST tạo mới thành công |
| 204 No Content | DELETE thành công |
| 400 Bad Request | Validation error, business rule violation |
| 401 Unauthorized | Chưa login hoặc token invalid |
| 403 Forbidden | Đã login nhưng không có quyền |
| 404 Not Found | Resource không tồn tại (hoặc thuộc clinic khác) |
| 409 Conflict | Optimistic lock conflict, unique violation |
| 422 Unprocessable Entity | Pydantic validation fail |
| 500 Internal Server Error | Bug, lỗi không lường trước |

### 2.4. Response format

Success:
```json
{
  "data": { ... },
  "meta": { "request_id": "...", "version": "v1" }
}
```

List với pagination:
```json
{
  "data": [ ... ],
  "meta": {
    "total": 245,
    "page": 1,
    "page_size": 20,
    "total_pages": 13
  }
}
```

Error:
```json
{
  "error": {
    "code": "PATIENT_NOT_FOUND",
    "message": "Bệnh nhân không tồn tại",
    "details": { ... }
  },
  "meta": { "request_id": "..." }
}
```

### 2.5. Pagination

Mọi list endpoint hỗ trợ:
```
?page=1&page_size=20&sort=-created_at&filter[status]=WAITING
```

- `page` (default 1, min 1)
- `page_size` (default 20, max 100)
- `sort`: cột, `-` cho desc (vd: `-created_at`, `name`)
- `filter[<field>]`: filter cụ thể

---

## 3. Database Foundation

### 3.1. Base Model

```python
# app/core/base_model.py

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base cho mọi model."""
    pass


class TimestampMixin:
    """Created/updated timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    """Soft delete fields."""
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)


class TenantMixin:
    """Clinic isolation."""
    clinic_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clinic.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )


class AuditedMixin:
    """Track who created/modified."""
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)


class VersionedMixin:
    """Optimistic lock."""
    version: Mapped[int] = mapped_column(default=1, nullable=False)


class BaseEntity(Base, TimestampMixin, SoftDeleteMixin, TenantMixin, AuditedMixin, VersionedMixin):
    """Base cho mọi entity nghiệp vụ — có clinic_id, soft delete, audit, version."""
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
```

### 3.2. RLS Helper

```python
# app/core/db.py

from contextvars import ContextVar
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Context vars cho tenancy
current_clinic_id: ContextVar[UUID | None] = ContextVar("current_clinic_id", default=None)
current_user_id: ContextVar[UUID | None] = ContextVar("current_user_id", default=None)


async def get_db() -> AsyncSession:
    """Dependency cho FastAPI — yield session với RLS context set."""
    async with AsyncSessionLocal() as session:
        clinic_id = current_clinic_id.get()
        user_id = current_user_id.get()

        if clinic_id:
            await session.execute(
                text("SET LOCAL app.current_clinic_id = :cid"),
                {"cid": str(clinic_id)},
            )
        if user_id:
            await session.execute(
                text("SET LOCAL app.current_user_id = :uid"),
                {"uid": str(user_id)},
            )

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### 3.3. RLS Policy template

```sql
-- Cho mỗi bảng có clinic_id
ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON <table_name>
  FOR ALL
  USING (clinic_id::text = current_setting('app.current_clinic_id', true));

-- Lưu ý: dùng `true` ở current_setting để không lỗi khi không set (cho admin queries)
-- Admin role có thể bypass bằng cách BYPASSRLS
```

### 3.4. Migration strategy với Alembic

```
alembic/
├── env.py                    # auto-import models
├── script.py.mako            # template
└── versions/
    ├── 0001_initial.py       # schema gốc
    ├── 0002_add_audit_log.py
    └── ...
```

**Quy tắc:**
- Migration phải **forward-only** ở production (không downgrade).
- Migration phá hoại (drop column, rename) phải multi-step:
  1. Add new column → deploy → backfill
  2. Switch code dùng new column → deploy
  3. Drop old column → deploy
- Test migration trên staging trước khi production.

---

## 4. Module Auth & Users

### 4.1. Schema

```python
# app/modules/users/models/clinic.py

from sqlalchemy import String, Boolean, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, TimestampMixin, SoftDeleteMixin, AuditedMixin
from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class Clinic(Base, TimestampMixin, SoftDeleteMixin, AuditedMixin):
    """Tenant — một phòng khám."""
    __tablename__ = "clinic"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    specialty: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tax_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
```

```python
# app/modules/users/models/user.py

from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseEntity


class User(BaseEntity):
    """User của clinic — bác sĩ, y tá, lễ tân, dược sĩ, admin."""
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Doctor-specific (nullable cho non-doctor)
    license_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    specialty_subfield: Mapped[str | None] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        # username unique trong clinic (chưa bị soft delete)
        # Postgres partial index
        # CREATE UNIQUE INDEX uq_user_clinic_username ON user (clinic_id, username) WHERE NOT is_deleted
    )
```

### 4.2. Roles & Permissions

```python
# app/modules/users/models/role.py

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import UUID

from app.core.base_model import BaseEntity, Base, TimestampMixin


class Role(BaseEntity):
    """Vai trò — admin, doctor, nurse, pharmacist, receptionist."""
    __tablename__ = "role"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Permission(Base, TimestampMixin):
    """Catalog permission — system-wide, không thuộc clinic."""
    __tablename__ = "permission"

    code: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)


class RolePermission(Base, TimestampMixin):
    """Mapping role -> permissions."""
    __tablename__ = "role_permission"

    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("role.id"), primary_key=True
    )
    permission_code: Mapped[str] = mapped_column(
        String(100), ForeignKey("permission.code"), primary_key=True
    )


class UserRole(Base, TimestampMixin):
    """User có role nào."""
    __tablename__ = "user_role"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True
    )
    role_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("role.id"), primary_key=True
    )
    assigned_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)


class UserExtraPermission(Base, TimestampMixin):
    """Permission grant/deny per user (override role)."""
    __tablename__ = "user_extra_permission"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True
    )
    permission_code: Mapped[str] = mapped_column(
        String(100), ForeignKey("permission.code"), primary_key=True
    )
    grant_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'grant' | 'deny'
```

### 4.3. Authentication flow

```python
# app/core/security.py

from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from uuid import UUID

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: UUID, clinic_id: UUID, roles: list[str]) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "clinic_id": str(clinic_id),
        "roles": roles,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def create_refresh_token(user_id: UUID) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except JWTError as e:
        raise InvalidTokenError(str(e))
```

### 4.4. Login endpoint

```python
# app/modules/auth/api/routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.auth.services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.login(
        clinic_code=payload.clinic_code,
        username=payload.username,
        password=payload.password,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.refresh(refresh_token)


@router.post("/logout", status_code=204)
async def logout(token: str = Depends(get_current_token)):
    # Revoke refresh token (Redis blacklist hoặc DB)
    ...
```

### 4.5. Login service logic

```python
class AuthService:
    async def login(self, clinic_code: str, username: str, password: str) -> TokenResponse:
        # 1. Tìm clinic
        clinic = await self.clinic_repo.get_by_code(clinic_code)
        if not clinic or not clinic.is_active:
            raise InvalidCredentialsError()

        # 2. Tìm user trong clinic
        user = await self.user_repo.get_by_username(clinic.id, username)
        if not user or not user.is_active:
            raise InvalidCredentialsError()

        # 3. Check lockout
        if user.is_locked:
            raise AccountLockedError()

        # 4. Verify password
        if not verify_password(password, user.password_hash):
            user.failed_login_count += 1
            if user.failed_login_count >= 5:
                user.is_locked = True
                # TODO: gửi email reset password
            await self.db.commit()
            raise InvalidCredentialsError()

        # 5. Reset failed count, update last login
        user.failed_login_count = 0
        user.last_login_at = datetime.utcnow()
        await self.db.commit()

        # 6. Load roles & permissions
        roles = await self.user_repo.get_role_codes(user.id)

        # 7. Generate tokens
        access = create_access_token(user.id, clinic.id, roles)
        refresh = create_refresh_token(user.id)

        # 8. Audit log
        await self.audit_service.log("login", "user", user.id, user_id=user.id, clinic_id=clinic.id)

        return TokenResponse(access_token=access, refresh_token=refresh, token_type="bearer")
```

---

## 5. Module Tenancy & Audit

### 5.1. Tenancy middleware

```python
# app/core/tenancy.py

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_token
from app.core.db import current_clinic_id, current_user_id


class TenancyMiddleware(BaseHTTPMiddleware):
    """Parse JWT, set context vars cho clinic_id và user_id."""

    PUBLIC_PATHS = {"/api/v1/auth/login", "/api/v1/auth/refresh", "/health", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        # Skip cho public paths
        if any(request.url.path.startswith(p) for p in self.PUBLIC_PATHS):
            return await call_next(request)

        # Parse Authorization header
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing token")

        token = auth[7:]
        try:
            payload = decode_token(token)
        except Exception:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

        if payload.get("type") != "access":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong token type")

        # Set context vars
        clinic_token = current_clinic_id.set(UUID(payload["clinic_id"]))
        user_token = current_user_id.set(UUID(payload["sub"]))

        try:
            response = await call_next(request)
            return response
        finally:
            current_clinic_id.reset(clinic_token)
            current_user_id.reset(user_token)
```

### 5.2. Audit log model

```python
# app/modules/audit/models.py

from datetime import datetime
from uuid import UUID
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.base_model import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    clinic_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("clinic.id"), nullable=True, index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # create/update/delete/view
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    old_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    changed_fields: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
```

**Lưu ý:** Audit log là append-only, không soft delete, không update. Có thể partition theo tháng nếu volume lớn.

### 5.3. Audit log mechanism

**Cách 1: SQLAlchemy event hooks** (tự động cho mọi entity inherit `BaseEntity`):

```python
# app/core/audit.py

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.base_model import BaseEntity
from app.core.db import current_user_id, current_clinic_id


def setup_audit_hooks():
    @event.listens_for(Session, "before_flush")
    def before_flush(session, flush_context, instances):
        for obj in session.new:
            if isinstance(obj, BaseEntity):
                _log_audit(session, obj, "create", new_data=_serialize(obj))
        
        for obj in session.dirty:
            if isinstance(obj, BaseEntity):
                old, new, changed = _diff(obj, session)
                if changed:
                    _log_audit(session, obj, "update", old_data=old, new_data=new, changed_fields=changed)
        
        for obj in session.deleted:
            if isinstance(obj, BaseEntity):
                _log_audit(session, obj, "delete", old_data=_serialize(obj))


def _log_audit(session, obj, action, old_data=None, new_data=None, changed_fields=None):
    from app.modules.audit.models import AuditLog
    log = AuditLog(
        id=uuid4(),
        clinic_id=current_clinic_id.get(),
        user_id=current_user_id.get(),
        action=action,
        entity_type=obj.__tablename__,
        entity_id=obj.id,
        old_data=old_data,
        new_data=new_data,
        changed_fields=changed_fields,
    )
    session.add(log)
```

**Cách 2: Decorator explicit** cho service methods (cho action không phải CRUD):

```python
def audited(action: str, entity_type: str):
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            result = await func(self, *args, **kwargs)
            await self.audit_service.log(
                action=action,
                entity_type=entity_type,
                entity_id=result.id if hasattr(result, "id") else None,
            )
            return result
        return wrapper
    return decorator
```

**Khuyến nghị:** Cách 1 cho CRUD chuẩn, Cách 2 cho action tùy chỉnh (login, void invoice, dispense, ...).

### 5.4. Đọc dữ liệu nhạy cảm

Mỗi khi gọi GET một entity nhạy cảm (Patient, Visit detail, Prescription), log async:

```python
async def get_patient(self, patient_id: UUID):
    patient = await self.repo.get_by_id(patient_id)
    if not patient:
        raise NotFoundError()
    
    # Async log, không block
    asyncio.create_task(
        self.audit_service.log("view", "patient", patient_id)
    )
    
    return patient
```

---

## 6. Module Patients

### 6.1. Schema

```python
# app/modules/patients/models/patient.py

from datetime import date
from sqlalchemy import String, Date, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseEntity


class Patient(BaseEntity):
    __tablename__ = "patient"

    patient_code: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    birth_year: Mapped[int | None] = mapped_column(nullable=True)  # khi không nhớ ngày
    gender: Mapped[str] = mapped_column(String(10), nullable=False)  # 'male'/'female'/'other'
    
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    id_number: Mapped[str | None] = mapped_column(String(20), nullable=True)  # CCCD/CMND
    
    address_line: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ward: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    blood_type: Mapped[str | None] = mapped_column(String(5), nullable=True)
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)
    chronic_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    occupation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    referral_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class PatientRelation(BaseEntity):
    """Quan hệ giữa các bệnh nhân (cha/mẹ-con, vợ-chồng)."""
    __tablename__ = "patient_relation"

    patient_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("patient.id"), nullable=False, index=True
    )
    guardian_patient_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("patient.id"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(String(20), nullable=False)  # parent/spouse/child/other
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

### 6.2. Indexes

```sql
-- Tìm kiếm theo phone (rất phổ biến)
CREATE INDEX ix_patient_clinic_phone ON patient (clinic_id, phone) WHERE NOT is_deleted;

-- Tìm theo tên (full text search)
CREATE INDEX ix_patient_clinic_name_gin ON patient
  USING gin (to_tsvector('simple', unaccent(full_name)))
  WHERE NOT is_deleted;

-- Patient code unique trong clinic
CREATE UNIQUE INDEX uq_patient_clinic_code ON patient (clinic_id, patient_code) WHERE NOT is_deleted;

-- Patient code generator: dùng sequence per clinic hoặc lock + count
```

### 6.3. Patient code generation

```python
async def generate_patient_code(self, clinic_id: UUID) -> str:
    """Generate next patient code: BN0001, BN0002, ..."""
    # Dùng SELECT ... FOR UPDATE để tránh race condition
    last_patient = await self.db.execute(
        select(Patient.patient_code)
        .where(Patient.clinic_id == clinic_id)
        .order_by(Patient.patient_code.desc())
        .limit(1)
        .with_for_update()
    )
    last = last_patient.scalar_one_or_none()
    
    if not last:
        return "BN0001"
    
    num = int(last[2:]) + 1
    return f"BN{num:04d}"

# Alternative: dùng PostgreSQL sequence per clinic
# CREATE SEQUENCE patient_code_seq_<clinic_id> START 1;
```

### 6.4. API endpoints

```
GET    /api/v1/patients                       # list, filter, search
POST   /api/v1/patients                       # create
GET    /api/v1/patients/{id}                  # detail
PATCH  /api/v1/patients/{id}                  # update
DELETE /api/v1/patients/{id}                  # soft delete
POST   /api/v1/patients/search                # advanced search (name, phone, dob)

GET    /api/v1/patients/{id}/visits           # visits của bệnh nhân
GET    /api/v1/patients/{id}/prescriptions    # đơn thuốc
GET    /api/v1/patients/{id}/vitals-history   # vitals trend

GET    /api/v1/patients/{id}/relations        # guardian relationships
POST   /api/v1/patients/{id}/relations        # add relation
DELETE /api/v1/patients/relations/{rel_id}    # remove relation

POST   /api/v1/patients/merge                 # merge 2 patients (admin only)
  body: { source_id, target_id, reason }
```

### 6.5. Search optimization

```python
async def search_patients(self, query: str, clinic_id: UUID, limit: int = 20):
    """Search bệnh nhân theo tên hoặc phone."""
    if query.isdigit():
        # Tìm theo phone
        return await self.db.execute(
            select(Patient).where(
                Patient.clinic_id == clinic_id,
                Patient.phone.ilike(f"%{query}%"),
                Patient.is_deleted == False,
            ).limit(limit)
        )
    else:
        # Full text search theo tên
        return await self.db.execute(
            select(Patient).where(
                Patient.clinic_id == clinic_id,
                func.to_tsvector("simple", func.unaccent(Patient.full_name))
                  .match(func.unaccent(query)),
                Patient.is_deleted == False,
            ).limit(limit)
        )
```

### 6.6. Patient merge logic

```python
async def merge_patients(self, source_id: UUID, target_id: UUID, reason: str, admin_user_id: UUID):
    """Merge source patient INTO target patient."""
    
    async with self.db.begin():
        source = await self.repo.get_by_id(source_id)
        target = await self.repo.get_by_id(target_id)
        
        if not source or not target:
            raise NotFoundError()
        if source.clinic_id != target.clinic_id:
            raise CrossTenantError()
        
        # 1. Reassign tất cả related records
        await self.db.execute(
            update(Visit).where(Visit.patient_id == source_id).values(patient_id=target_id)
        )
        await self.db.execute(
            update(Appointment).where(Appointment.patient_id == source_id).values(patient_id=target_id)
        )
        await self.db.execute(
            update(Invoice).where(Invoice.patient_id == source_id).values(patient_id=target_id)
        )
        # ... các bảng khác
        
        # 2. Backup source data trước khi soft delete (cho undo)
        backup = PatientMergeBackup(
            id=uuid4(),
            clinic_id=source.clinic_id,
            source_patient_data=serialize(source),
            target_patient_id=target_id,
            merged_by=admin_user_id,
            reason=reason,
        )
        self.db.add(backup)
        
        # 3. Soft delete source
        source.is_deleted = True
        source.deleted_at = datetime.utcnow()
        source.deleted_by = admin_user_id
        
        # 4. Audit log
        await self.audit_service.log(
            "merge", "patient", target_id,
            old_data={"source_id": str(source_id)},
            new_data={"reason": reason},
        )
```

---

## 7. Module Appointments & Queue

### 7.1. Schema

```python
class Appointment(BaseEntity):
    __tablename__ = "appointment"

    patient_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("patient.id"), nullable=False, index=True
    )
    assigned_doctor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=True, index=True
    )
    
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_minutes: Mapped[int] = mapped_column(default=30, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled", index=True)
    # scheduled / confirmed / checked_in / completed / cancelled / no_show
    
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

### 7.2. Indexes

```sql
-- Lookup theo time slot (capacity check)
CREATE INDEX ix_appointment_clinic_time ON appointment (clinic_id, scheduled_at)
  WHERE NOT is_deleted AND status IN ('scheduled', 'confirmed', 'checked_in');

-- Lookup appointments của bệnh nhân
CREATE INDEX ix_appointment_patient ON appointment (patient_id, scheduled_at DESC)
  WHERE NOT is_deleted;

-- Cron auto-no-show
CREATE INDEX ix_appointment_no_show_check ON appointment (scheduled_at, status)
  WHERE status IN ('scheduled', 'confirmed') AND NOT is_deleted;
```

### 7.3. Capacity check service

```python
class AppointmentService:
    async def check_slot_capacity(
        self,
        clinic_id: UUID,
        slot_start: datetime,
        slot_duration_minutes: int,
    ) -> dict:
        slot_end = slot_start + timedelta(minutes=slot_duration_minutes)
        
        # Count doctors on shift
        doctors_query = (
            select(func.count(distinct(Shift.user_id)))
            .where(
                Shift.clinic_id == clinic_id,
                Shift.shift_date == slot_start.date(),
                Shift.start_time <= slot_start.time(),
                Shift.end_time >= slot_end.time(),
                Shift.status == "scheduled",
                Shift.is_deleted == False,
            )
        )
        # Filter only users with role 'doctor'
        # ... (join with user_role)
        
        doctors_count = (await self.db.execute(doctors_query)).scalar() or 0
        
        # Count overlapping appointments
        appts_query = (
            select(func.count(Appointment.id))
            .where(
                Appointment.clinic_id == clinic_id,
                Appointment.scheduled_at < slot_end,
                Appointment.scheduled_at + 
                  cast(Appointment.duration_minutes, INTERVAL) * text("INTERVAL '1 minute'") > slot_start,
                Appointment.status.in_(["scheduled", "confirmed", "checked_in"]),
                Appointment.is_deleted == False,
            )
        )
        booked = (await self.db.execute(appts_query)).scalar() or 0
        
        return {
            "doctors_on_shift": doctors_count,
            "booked": booked,
            "available": max(0, doctors_count - booked),
            "slot_start": slot_start,
            "slot_end": slot_end,
        }
    
    async def create_appointment(self, payload: AppointmentCreate, clinic_id: UUID):
        # 1. Validate scheduled_at trong giờ làm việc
        await self._validate_within_operating_hours(clinic_id, payload.scheduled_at)
        
        # 2. Check capacity
        capacity = await self.check_slot_capacity(
            clinic_id, payload.scheduled_at, payload.duration_minutes
        )
        if capacity["available"] <= 0:
            raise NoCapacityError()
        
        # 3. Validate patient exists
        await self.patient_repo.get_or_404(payload.patient_id)
        
        # 4. Create
        appt = Appointment(
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            assigned_doctor_id=payload.assigned_doctor_id,
            scheduled_at=payload.scheduled_at,
            duration_minutes=payload.duration_minutes,
            chief_complaint=payload.chief_complaint,
            status="scheduled",
        )
        self.db.add(appt)
        await self.db.flush()
        
        return appt
```

### 7.4. API endpoints

```
GET    /api/v1/appointments?date=2026-04-26&status=scheduled
POST   /api/v1/appointments
GET    /api/v1/appointments/{id}
PATCH  /api/v1/appointments/{id}
DELETE /api/v1/appointments/{id}                  # cancel (soft)

POST   /api/v1/appointments/{id}/confirm          # confirm
POST   /api/v1/appointments/{id}/check-in         # check-in → tạo Visit
POST   /api/v1/appointments/{id}/cancel
  body: { reason }

GET    /api/v1/appointments/calendar?from=...&to=...   # calendar view
GET    /api/v1/appointments/slots?date=2026-04-26      # available slots cho 1 ngày
```

### 7.5. Queue logic

Queue không có entity riêng — là **dynamic view** của Visit:

```python
class QueueService:
    async def get_queue(self, clinic_id: UUID, doctor_id: UUID | None = None) -> list[Visit]:
        """Lấy queue hiện tại."""
        query = (
            select(Visit)
            .options(selectinload(Visit.patient), selectinload(Visit.vitals))
            .where(
                Visit.clinic_id == clinic_id,
                Visit.status == "WAITING",
                Visit.is_deleted == False,
            )
            .order_by(
                Visit.priority.desc(),
                Visit.is_returning.desc(),
                Visit.check_in_at.asc(),
            )
        )
        return (await self.db.execute(query)).scalars().all()
    
    async def call_next(self, clinic_id: UUID, doctor_id: UUID) -> Visit | None:
        """Bác sĩ gọi bệnh nhân tiếp theo."""
        async with self.db.begin():
            # Logic ưu tiên: assigned_doctor_id = current → null → others
            query = (
                select(Visit)
                .where(
                    Visit.clinic_id == clinic_id,
                    Visit.status == "WAITING",
                    Visit.is_deleted == False,
                )
                .order_by(
                    # Priority: assigned cho mình > null > others
                    case(
                        (Visit.assigned_doctor_id == doctor_id, 0),
                        (Visit.assigned_doctor_id.is_(None), 1),
                        else_=2,
                    ),
                    Visit.priority.desc(),
                    Visit.check_in_at.asc(),
                )
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            visit = (await self.db.execute(query)).scalar_one_or_none()
            
            if not visit:
                return None
            
            # Optionally: check require_vitals_before_consultation
            settings = await self.settings_service.get(clinic_id)
            if settings.queue.require_vitals_before_consultation:
                has_vitals = await self.vital_repo.exists(visit.id)
                if not has_vitals:
                    raise VitalsRequiredError()
            
            # Update status
            visit.status = "IN_PROGRESS"
            visit.doctor_id = doctor_id
            visit.consultation_started_at = datetime.utcnow()
            
            return visit
```

---

## 8. Module Visits

### 8.1. Schema

```python
class Visit(BaseEntity):
    __tablename__ = "visit"

    patient_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("patient.id"), nullable=False, index=True
    )
    appointment_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("appointment.id"), nullable=True, unique=True
    )
    assigned_doctor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=True
    )
    doctor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=True, index=True
    )
    
    visit_number: Mapped[str] = mapped_column(String(30), nullable=False)  # "20260426-001"
    
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # bác sĩ ghi
    
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="WAITING", index=True
    )
    # WAITING / IN_PROGRESS / AWAITING_PAYMENT / COMPLETED / CANCELLED
    
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    is_follow_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_returning: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    check_in_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    consultation_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consultation_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


# Constraints:
# UNIQUE (clinic_id, visit_number) WHERE NOT is_deleted
# CHECK status IN (WAITING, IN_PROGRESS, AWAITING_PAYMENT, COMPLETED, CANCELLED)
```

### 8.2. Visit number generator

```python
async def generate_visit_number(self, clinic_id: UUID) -> str:
    """Format: YYYYMMDD-NNN, reset daily per clinic."""
    today = date.today()
    prefix = today.strftime("%Y%m%d")
    
    # Lock + count cho race-safe
    last_query = (
        select(Visit.visit_number)
        .where(
            Visit.clinic_id == clinic_id,
            Visit.visit_number.like(f"{prefix}-%"),
        )
        .order_by(Visit.visit_number.desc())
        .limit(1)
        .with_for_update()
    )
    last = (await self.db.execute(last_query)).scalar_one_or_none()
    
    if not last:
        return f"{prefix}-001"
    
    num = int(last.split("-")[1]) + 1
    return f"{prefix}-{num:03d}"
```

### 8.3. State machine

```python
VALID_TRANSITIONS = {
    "WAITING": ["IN_PROGRESS", "CANCELLED"],
    "IN_PROGRESS": ["AWAITING_PAYMENT", "CANCELLED"],
    "AWAITING_PAYMENT": ["COMPLETED", "CANCELLED"],
    "COMPLETED": [],
    "CANCELLED": [],
}


class VisitService:
    async def transition(self, visit_id: UUID, new_status: str, **kwargs):
        async with self.db.begin():
            visit = await self.repo.get_by_id_for_update(visit_id)
            
            if new_status not in VALID_TRANSITIONS[visit.status]:
                raise InvalidTransitionError(
                    f"Cannot transition from {visit.status} to {new_status}"
                )
            
            old_status = visit.status
            visit.status = new_status
            
            # Side effects per transition
            if new_status == "IN_PROGRESS":
                visit.consultation_started_at = datetime.utcnow()
                visit.doctor_id = kwargs.get("doctor_id")
            elif new_status == "AWAITING_PAYMENT":
                visit.consultation_ended_at = datetime.utcnow()
                # Trigger create invoice
                await self.invoice_service.create_from_visit(visit)
            elif new_status == "COMPLETED":
                visit.completed_at = datetime.utcnow()
            elif new_status == "CANCELLED":
                visit.cancelled_at = datetime.utcnow()
                visit.cancellation_reason = kwargs.get("reason")
                # Release inventory reservations
                await self.prescription_service.cancel_all_for_visit(visit_id)
            
            await self.audit_service.log(
                "transition", "visit", visit_id,
                old_data={"status": old_status},
                new_data={"status": new_status},
            )
            
            return visit
```

### 8.4. API endpoints

```
GET    /api/v1/visits                    # list, filter (status, doctor, date)
POST   /api/v1/visits                    # create (walk-in)
GET    /api/v1/visits/{id}               # detail
PATCH  /api/v1/visits/{id}               # update notes, chief_complaint

POST   /api/v1/visits/{id}/start         # IN_PROGRESS (bác sĩ nhận)
POST   /api/v1/visits/{id}/complete      # → AWAITING_PAYMENT
POST   /api/v1/visits/{id}/finish        # → COMPLETED (sau khi paid)
POST   /api/v1/visits/{id}/cancel
  body: { reason }

GET    /api/v1/visits/{id}/timeline      # full timeline: vitals, services, prescriptions, invoice

# Queue
GET    /api/v1/queue                     # current queue
POST   /api/v1/queue/call-next           # bác sĩ gọi tiếp theo
```

---

## 9. Module Vitals (Dynamic Form)

### 9.1. Schema

```python
class VitalFieldDefinition(BaseEntity):
    __tablename__ = "vital_field_definition"

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # 'number' | 'integer' | 'text' | 'boolean' | 'select'
    
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    min_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    max_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    warning_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    warning_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    decimal_places: Mapped[int | None] = mapped_column(Integer, nullable=True)
    options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    group_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    placeholder: Mapped[str | None] = mapped_column(String(200), nullable=True)
    help_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class VitalSchemaVersion(Base, TimestampMixin):
    __tablename__ = "vital_schema_version"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    clinic_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    field_snapshot: Mapped[list] = mapped_column(JSONB, nullable=False)
    changed_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)


class VisitVitals(BaseEntity):
    __tablename__ = "visit_vitals"

    visit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("visit.id"), nullable=False, index=True
    )
    recorded_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    values: Mapped[dict] = mapped_column(JSONB, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# System preset (master data)
class SystemVitalPreset(Base, TimestampMixin):
    __tablename__ = "system_vital_preset"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    specialty_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fields: Mapped[list] = mapped_column(JSONB, nullable=False)
```

### 9.2. Indexes

```sql
CREATE UNIQUE INDEX uq_vital_def_clinic_key ON vital_field_definition (clinic_id, key)
  WHERE NOT is_deleted;

CREATE INDEX ix_vital_schema_version ON vital_schema_version (clinic_id, version DESC);

-- Cho query trend
CREATE INDEX ix_visit_vitals_visit ON visit_vitals (visit_id, recorded_at DESC);

-- GIN cho query trên values JSONB (vd: lấy huyết áp 6 tháng qua)
CREATE INDEX ix_visit_vitals_values_gin ON visit_vitals USING gin (values);
```

### 9.3. Validation runtime

```python
class VitalValidator:
    def __init__(self, definitions: list[VitalFieldDefinition]):
        self.defs = {d.key: d for d in definitions if d.is_active}

    def validate(self, payload: dict) -> dict:
        errors = []
        cleaned = {}

        # Check required fields
        for key, defn in self.defs.items():
            if defn.is_required and key not in payload:
                errors.append({"field": key, "code": "REQUIRED", "message": f"{defn.label} là bắt buộc"})

        # Validate each field
        for key, value in payload.items():
            if key not in self.defs:
                errors.append({"field": key, "code": "UNKNOWN", "message": f"Field {key} không tồn tại"})
                continue
            
            defn = self.defs[key]
            
            try:
                cleaned_value = self._coerce_type(value, defn)
                self._validate_range(cleaned_value, defn)
                cleaned[key] = cleaned_value
            except ValueError as e:
                errors.append({"field": key, "code": "INVALID", "message": str(e)})

        if errors:
            raise ValidationError(errors)
        
        return cleaned

    def _coerce_type(self, value, defn):
        if defn.data_type == "number":
            return Decimal(str(value))
        elif defn.data_type == "integer":
            return int(value)
        elif defn.data_type == "boolean":
            return bool(value)
        elif defn.data_type == "select":
            options = defn.options or []
            if value not in options:
                raise ValueError(f"Giá trị phải là một trong: {options}")
            return value
        else:  # text
            return str(value)

    def _validate_range(self, value, defn):
        if defn.data_type in ("number", "integer"):
            if defn.min_value is not None and value < defn.min_value:
                raise ValueError(f"Tối thiểu {defn.min_value}")
            if defn.max_value is not None and value > defn.max_value:
                raise ValueError(f"Tối đa {defn.max_value}")


class VitalsService:
    async def create_vitals(self, visit_id: UUID, payload: dict, user_id: UUID, clinic_id: UUID):
        # 1. Get current definitions
        defs = await self.def_repo.get_active(clinic_id)
        validator = VitalValidator(defs)
        
        # 2. Validate payload
        cleaned = validator.validate(payload)
        
        # 3. Get current schema version
        current_version = await self.version_repo.get_current_version(clinic_id)
        
        # 4. Create
        vitals = VisitVitals(
            clinic_id=clinic_id,
            visit_id=visit_id,
            recorded_by=user_id,
            schema_version=current_version,
            values=cleaned,
        )
        self.db.add(vitals)
        await self.db.flush()
        
        return vitals
```

### 9.4. Schema evolution

```python
class VitalDefinitionService:
    async def update_definition(self, def_id: UUID, payload: VitalDefUpdate, user_id: UUID, clinic_id: UUID):
        async with self.db.begin():
            defn = await self.def_repo.get_by_id(def_id)
            
            # Không cho sửa key và data_type
            if payload.key is not None and payload.key != defn.key:
                raise ImmutableFieldError("Cannot change key")
            if payload.data_type is not None and payload.data_type != defn.data_type:
                raise ImmutableFieldError("Cannot change data_type")
            
            # Apply changes
            for field, value in payload.dict(exclude_unset=True).items():
                setattr(defn, field, value)
            defn.updated_by = user_id
            
            # Create new schema version
            await self._create_schema_version(clinic_id, user_id, f"Updated field {defn.key}")

    async def _create_schema_version(self, clinic_id: UUID, user_id: UUID, summary: str):
        # Snapshot tất cả active definitions
        defs = await self.def_repo.get_active(clinic_id)
        snapshot = [
            {
                "key": d.key, "label": d.label, "data_type": d.data_type,
                "unit": d.unit, "min_value": str(d.min_value) if d.min_value else None,
                "max_value": str(d.max_value) if d.max_value else None,
                "warning_min": str(d.warning_min) if d.warning_min else None,
                "warning_max": str(d.warning_max) if d.warning_max else None,
                "options": d.options, "is_required": d.is_required,
                "sort_order": d.sort_order, "group_name": d.group_name,
            }
            for d in defs
        ]
        
        last_version = await self.version_repo.get_current_version(clinic_id) or 0
        version = VitalSchemaVersion(
            id=uuid4(),
            clinic_id=clinic_id,
            version=last_version + 1,
            field_snapshot=snapshot,
            changed_by=user_id,
            change_summary=summary,
        )
        self.db.add(version)
```

### 9.5. API endpoints

```
# Definitions (admin)
GET    /api/v1/vital-fields              # list current definitions
POST   /api/v1/vital-fields              # add new field
PATCH  /api/v1/vital-fields/{id}         # update field
DELETE /api/v1/vital-fields/{id}         # disable/soft delete
POST   /api/v1/vital-fields/reorder      # reorder

GET    /api/v1/vital-schema/versions     # version history
GET    /api/v1/vital-schema/versions/{n} # specific version

# Vitals (nurse, doctor)
POST   /api/v1/visits/{id}/vitals        # add vitals to visit
GET    /api/v1/visits/{id}/vitals        # list vitals của visit
PATCH  /api/v1/vitals/{id}               # update (trong cùng ngày)
DELETE /api/v1/vitals/{id}               # soft delete

GET    /api/v1/patients/{id}/vitals/trend?field=systolic_bp&from=...&to=...
                                          # historical trend
```

---

## 10. Module Services

### 10.1. Schema

```python
class Service(BaseEntity):
    __tablename__ = "service"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    default_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class VisitService(BaseEntity):
    """Service đã được cung cấp cho 1 visit."""
    __tablename__ = "visit_service"

    visit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("visit.id"), nullable=False, index=True
    )
    service_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("service.id"), nullable=False
    )
    performed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=True
    )
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    discount_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ordered", nullable=False)
    # ordered / in_progress / completed / cancelled
    
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# Constraints
# UNIQUE (clinic_id, code) WHERE NOT is_deleted (cho service)
```

### 10.2. API endpoints

```
# Service catalog (admin)
GET    /api/v1/services                  # list
POST   /api/v1/services                  # create
GET    /api/v1/services/{id}
PATCH  /api/v1/services/{id}
DELETE /api/v1/services/{id}

# Visit services
POST   /api/v1/visits/{id}/services      # add service to visit
PATCH  /api/v1/visit-services/{id}       # update (price override, qty)
DELETE /api/v1/visit-services/{id}

POST   /api/v1/visit-services/{id}/start    # in_progress
POST   /api/v1/visit-services/{id}/complete # completed
```

---

## 11. Module Medicines & Inventory

### 11.1. Medicine catalog

```python
class Medicine(BaseEntity):
    __tablename__ = "medicine"

    # Medicine có thể là system-level (clinic_id = null) hoặc clinic-level
    # Để đơn giản, v1 luôn clinic-level — clinic_id NOT NULL
    
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    generic_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    strength: Mapped[str | None] = mapped_column(String(100), nullable=True)
    form: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # tablet/capsule/syrup/injection/cream/drops/...
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    atc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    base_unit: Mapped[str] = mapped_column(String(20), nullable=False)  # "viên", "ml"
    pack_size: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=1, nullable=False)
    pack_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "hộp"
    
    is_prescription_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_controlled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    storage_condition: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
```

### 11.2. Inventory & Batch

```python
class InventoryItem(BaseEntity):
    """Một medicine cụ thể trong kho của clinic."""
    __tablename__ = "inventory_item"

    medicine_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("medicine.id"), nullable=False
    )
    
    default_purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    default_sale_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    reorder_point: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    reorder_quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Batch(BaseEntity):
    """Lô của một inventory item."""
    __tablename__ = "batch"

    inventory_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("inventory_item.id"), nullable=False, index=True
    )
    supplier_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("supplier.id"), nullable=True
    )
    
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    manufacturing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    
    initial_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    actual_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0, nullable=False)
    
    is_recalled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    @hybrid_property
    def available_quantity(self):
        return self.actual_quantity - self.reserved_quantity
    
    @hybrid_property
    def is_expired(self):
        return self.expiry_date < date.today()


class StockMovement(Base, TimestampMixin):
    """Append-only log mọi thay đổi tồn kho."""
    __tablename__ = "stock_movement"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    clinic_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("batch.id"), nullable=False, index=True
    )
    
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    # purchase_in / prescription_out / adjustment_increase / adjustment_decrease
    # transfer_out / transfer_in / expiry_writeoff / damage_writeoff / recall_writeoff / return_in
    
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    quantity_before: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    performed_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Supplier(BaseEntity):
    __tablename__ = "supplier"
    
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
```

### 11.3. Indexes

```sql
-- Medicine search
CREATE INDEX ix_medicine_clinic_name_gin ON medicine
  USING gin (clinic_id, to_tsvector('simple', unaccent(name)))
  WHERE NOT is_deleted;

CREATE UNIQUE INDEX uq_medicine_clinic_code ON medicine (clinic_id, code) WHERE NOT is_deleted;

-- Inventory item lookup
CREATE UNIQUE INDEX uq_inventory_clinic_medicine ON inventory_item (clinic_id, medicine_id)
  WHERE NOT is_deleted;

-- Batch FEFO
CREATE INDEX ix_batch_fefo ON batch (clinic_id, inventory_item_id, expiry_date, received_date)
  WHERE NOT is_deleted AND NOT is_recalled AND actual_quantity > reserved_quantity;

-- Expiry alerts
CREATE INDEX ix_batch_expiry ON batch (clinic_id, expiry_date)
  WHERE NOT is_deleted;

-- Stock movement
CREATE INDEX ix_stock_movement_batch_time ON stock_movement (batch_id, performed_at DESC);
CREATE INDEX ix_stock_movement_clinic_time ON stock_movement (clinic_id, performed_at DESC);
```

### 11.4. Inventory operations

```python
class InventoryService:
    async def receive_stock(
        self,
        inventory_item_id: UUID,
        batch_data: BatchCreate,
        performed_by: UUID,
        clinic_id: UUID,
    ):
        """Nhập kho — tạo batch mới."""
        async with self.db.begin():
            # 1. Tạo batch
            batch = Batch(
                clinic_id=clinic_id,
                inventory_item_id=inventory_item_id,
                batch_number=batch_data.batch_number,
                expiry_date=batch_data.expiry_date,
                received_date=batch_data.received_date or date.today(),
                purchase_price=batch_data.purchase_price,
                initial_quantity=batch_data.quantity,
                actual_quantity=batch_data.quantity,
                reserved_quantity=0,
                supplier_id=batch_data.supplier_id,
            )
            self.db.add(batch)
            await self.db.flush()
            
            # 2. Stock movement
            movement = StockMovement(
                id=uuid4(),
                clinic_id=clinic_id,
                batch_id=batch.id,
                movement_type="purchase_in",
                quantity_delta=batch_data.quantity,
                quantity_before=0,
                quantity_after=batch_data.quantity,
                reference_type="batch_received",
                reference_id=batch.id,
                reason=f"Nhập kho lô {batch_data.batch_number}",
                performed_by=performed_by,
            )
            self.db.add(movement)
            
            return batch
    
    async def adjust_stock(
        self,
        batch_id: UUID,
        delta: Decimal,
        reason: str,
        performed_by: UUID,
        clinic_id: UUID,
    ):
        """Điều chỉnh tồn kho (kiểm kê)."""
        if not reason:
            raise ValueError("Reason required for stock adjustment")
        
        async with self.db.begin():
            batch = await self.repo.get_batch_for_update(batch_id)
            
            new_qty = batch.actual_quantity + delta
            if new_qty < batch.reserved_quantity:
                raise InsufficientStockError(
                    f"Không thể giảm xuống {new_qty} vì có {batch.reserved_quantity} đã reserve"
                )
            
            quantity_before = batch.actual_quantity
            batch.actual_quantity = new_qty
            
            movement = StockMovement(
                id=uuid4(),
                clinic_id=clinic_id,
                batch_id=batch.id,
                movement_type="adjustment_increase" if delta > 0 else "adjustment_decrease",
                quantity_delta=delta,
                quantity_before=quantity_before,
                quantity_after=new_qty,
                reason=reason,
                performed_by=performed_by,
            )
            self.db.add(movement)
            
            return batch
```

---

## 12. Module Prescriptions & Pharmacy

### 12.1. Schema

```python
class Prescription(BaseEntity):
    __tablename__ = "prescription"

    visit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("visit.id"), nullable=False, index=True
    )
    prescribed_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    prescribed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    dispense_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # in_house / external / mixed
    
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    # pending / partially_dispensed / dispensed / cancelled
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    printed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PrescriptionItem(BaseEntity):
    __tablename__ = "prescription_item"

    prescription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("prescription.id"), nullable=False, index=True
    )
    medicine_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("medicine.id"), nullable=True
    )
    medicine_name_text: Mapped[str | None] = mapped_column(String(300), nullable=True)
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    dosage_text: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    dispense_source: Mapped[str] = mapped_column(String(20), nullable=False)
    # in_house / external
    
    in_house_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # pending / reserved / dispensed / cancelled (chỉ khi dispense_source=in_house)
    
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PrescriptionItemBatch(BaseEntity):
    """Mapping prescription item -> batches đã reserve/dispense."""
    __tablename__ = "prescription_item_batch"

    prescription_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("prescription_item.id"), nullable=False, index=True
    )
    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("batch.id"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    # reserved / dispensed / cancelled / substituted
    
    dispensed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispensed_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
```

### 12.2. Reserve logic (FEFO)

```python
class PrescriptionService:
    async def create_prescription(
        self,
        visit_id: UUID,
        items_data: list[PrescriptionItemCreate],
        prescribed_by: UUID,
        clinic_id: UUID,
    ):
        async with self.db.begin():
            # 1. Determine dispense_type
            sources = {item.dispense_source for item in items_data}
            if sources == {"in_house"}:
                dispense_type = "in_house"
            elif sources == {"external"}:
                dispense_type = "external"
            else:
                dispense_type = "mixed"
            
            # 2. Create prescription
            rx = Prescription(
                clinic_id=clinic_id,
                visit_id=visit_id,
                prescribed_by=prescribed_by,
                dispense_type=dispense_type,
                status="pending",
            )
            self.db.add(rx)
            await self.db.flush()
            
            # 3. Create items + reserve in_house
            for idx, item_data in enumerate(items_data):
                item = PrescriptionItem(
                    clinic_id=clinic_id,
                    prescription_id=rx.id,
                    medicine_id=item_data.medicine_id,
                    medicine_name_text=item_data.medicine_name_text,
                    quantity=item_data.quantity,
                    dosage_text=item_data.dosage_text,
                    duration_days=item_data.duration_days,
                    instructions=item_data.instructions,
                    dispense_source=item_data.dispense_source,
                    sort_order=idx,
                )
                
                if item_data.dispense_source == "in_house":
                    item.in_house_status = "pending"
                    
                    # Lookup inventory item
                    inv = await self.inventory_repo.get_by_medicine(
                        clinic_id, item_data.medicine_id
                    )
                    if not inv:
                        raise NoInventoryError(item_data.medicine_id)
                    
                    item.unit_price = inv.default_sale_price
                    item.total_amount = inv.default_sale_price * item_data.quantity
                    
                    self.db.add(item)
                    await self.db.flush()
                    
                    # Reserve from batches (FEFO)
                    await self._reserve_for_item(item, inv.id, clinic_id)
                else:
                    self.db.add(item)
            
            return rx
    
    async def _reserve_for_item(
        self,
        item: PrescriptionItem,
        inventory_item_id: UUID,
        clinic_id: UUID,
    ):
        """FEFO reservation."""
        needed = item.quantity
        
        # Lock batches for FEFO
        batches_query = (
            select(Batch)
            .where(
                Batch.clinic_id == clinic_id,
                Batch.inventory_item_id == inventory_item_id,
                Batch.actual_quantity > Batch.reserved_quantity,
                Batch.is_recalled == False,
                Batch.expiry_date > date.today(),
                Batch.is_deleted == False,
            )
            .order_by(Batch.expiry_date.asc(), Batch.received_date.asc())
            .with_for_update(skip_locked=True)
        )
        batches = (await self.db.execute(batches_query)).scalars().all()
        
        remaining = needed
        for batch in batches:
            available = batch.actual_quantity - batch.reserved_quantity
            take = min(available, remaining)
            
            if take > 0:
                batch.reserved_quantity += take
                
                pib = PrescriptionItemBatch(
                    clinic_id=clinic_id,
                    prescription_item_id=item.id,
                    batch_id=batch.id,
                    quantity=take,
                    status="reserved",
                )
                self.db.add(pib)
                
                remaining -= take
                if remaining == 0:
                    break
        
        if remaining > 0:
            raise InsufficientStockError(
                f"Cần {needed}, chỉ available {needed - remaining}"
            )
        
        item.in_house_status = "reserved"
```

### 12.3. Dispense logic

```python
class PharmacyService:
    async def dispense_item(
        self,
        item_id: UUID,
        pharmacist_id: UUID,
        clinic_id: UUID,
    ):
        """Cấp phát thuốc — deduct stock thật."""
        async with self.db.begin():
            item = await self.repo.get_item_for_update(item_id)
            
            if item.in_house_status != "reserved":
                raise InvalidStateError(f"Item must be 'reserved', got {item.in_house_status}")
            
            # Get all reserved batches for this item
            reservations = await self.repo.get_reservations(item_id)
            
            for res in reservations:
                if res.status != "reserved":
                    continue
                
                batch = await self.repo.get_batch_for_update(res.batch_id)
                
                # Deduct actual + release reserved
                quantity_before = batch.actual_quantity
                batch.actual_quantity -= res.quantity
                batch.reserved_quantity -= res.quantity
                
                # Update reservation status
                res.status = "dispensed"
                res.dispensed_at = datetime.utcnow()
                res.dispensed_by = pharmacist_id
                
                # Stock movement
                movement = StockMovement(
                    id=uuid4(),
                    clinic_id=clinic_id,
                    batch_id=batch.id,
                    movement_type="prescription_out",
                    quantity_delta=-res.quantity,
                    quantity_before=quantity_before,
                    quantity_after=batch.actual_quantity,
                    reference_type="prescription_item",
                    reference_id=item.id,
                    performed_by=pharmacist_id,
                )
                self.db.add(movement)
            
            item.in_house_status = "dispensed"
            
            # Update prescription status
            await self._update_prescription_status(item.prescription_id)
    
    async def cancel_reservation(self, item_id: UUID, reason: str, user_id: UUID, clinic_id: UUID):
        """Release reserve (visit cancelled, prescription cancelled)."""
        async with self.db.begin():
            item = await self.repo.get_item_for_update(item_id)
            
            if item.in_house_status not in ("pending", "reserved"):
                return  # Already dispensed or cancelled
            
            reservations = await self.repo.get_reservations(item_id)
            for res in reservations:
                if res.status != "reserved":
                    continue
                
                batch = await self.repo.get_batch_for_update(res.batch_id)
                batch.reserved_quantity -= res.quantity
                res.status = "cancelled"
            
            item.in_house_status = "cancelled"
    
    async def substitute_batch(
        self,
        item_id: UUID,
        old_batch_id: UUID,
        new_batch_id: UUID,
        quantity: Decimal,
        reason: str,
        pharmacist_id: UUID,
        clinic_id: UUID,
    ):
        """Đổi batch khi cấp phát (batch reserve bị hỏng/thiếu)."""
        async with self.db.begin():
            # Release old reservation
            old_res = await self.repo.get_reservation(item_id, old_batch_id)
            old_batch = await self.repo.get_batch_for_update(old_batch_id)
            old_batch.reserved_quantity -= quantity
            old_res.status = "substituted"
            
            # Reserve new
            new_batch = await self.repo.get_batch_for_update(new_batch_id)
            if new_batch.actual_quantity - new_batch.reserved_quantity < quantity:
                raise InsufficientStockError()
            
            new_batch.reserved_quantity += quantity
            new_res = PrescriptionItemBatch(
                clinic_id=clinic_id,
                prescription_item_id=item_id,
                batch_id=new_batch_id,
                quantity=quantity,
                status="reserved",
            )
            self.db.add(new_res)
            
            # Audit
            await self.audit_service.log(
                "substitute_batch", "prescription_item", item_id,
                old_data={"batch_id": str(old_batch_id)},
                new_data={"batch_id": str(new_batch_id), "reason": reason},
            )
```

### 12.4. API endpoints

```
# Prescription
POST   /api/v1/visits/{id}/prescriptions    # bác sĩ kê đơn
GET    /api/v1/prescriptions/{id}
PATCH  /api/v1/prescriptions/{id}            # update notes (chưa dispensed)
POST   /api/v1/prescriptions/{id}/cancel
POST   /api/v1/prescriptions/{id}/print      # in đơn

# Pharmacy
GET    /api/v1/pharmacy/queue                # prescriptions có in_house items pending
POST   /api/v1/prescription-items/{id}/dispense
POST   /api/v1/prescription-items/{id}/substitute
  body: { old_batch_id, new_batch_id, quantity, reason }
POST   /api/v1/prescriptions/{id}/dispense-all   # dispense tất cả items in_house
```

---

## 13. Module Billing

### 13.1. Schema

```python
class Invoice(BaseEntity):
    __tablename__ = "invoice"

    visit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("visit.id"), nullable=False, index=True
    )
    patient_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("patient.id"), nullable=False, index=True
    )
    
    invoice_number: Mapped[str] = mapped_column(String(30), nullable=False)
    
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    total_discount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    discount_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_tax: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    # draft / pending / partially_paid / paid / cancelled / refunded
    
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    @hybrid_property
    def balance(self):
        return self.total_amount - self.paid_amount


class InvoiceItem(BaseEntity):
    __tablename__ = "invoice_item"

    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("invoice.id"), nullable=False, index=True
    )
    
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # service / medicine / other
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    discount_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Payment(BaseEntity):
    __tablename__ = "payment"

    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("invoice.id"), nullable=False, index=True
    )
    
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    # cash / card / bank_transfer / ewallet
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False
    )
    
    is_refund: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

### 13.2. Logic tạo invoice

```python
class InvoiceService:
    async def create_from_visit(self, visit: Visit) -> Invoice:
        async with self.db.begin():
            # 1. Generate invoice number
            invoice_number = await self._generate_invoice_number(visit.clinic_id)
            
            # 2. Create invoice
            invoice = Invoice(
                clinic_id=visit.clinic_id,
                visit_id=visit.id,
                patient_id=visit.patient_id,
                invoice_number=invoice_number,
                status="pending",
                issued_at=datetime.utcnow(),
            )
            self.db.add(invoice)
            await self.db.flush()
            
            items = []
            
            # 3. Pull VisitServices completed/ordered
            visit_services = await self.visit_service_repo.get_billable(visit.id)
            for vs in visit_services:
                items.append(InvoiceItem(
                    clinic_id=visit.clinic_id,
                    invoice_id=invoice.id,
                    item_type="service",
                    reference_type="visit_service",
                    reference_id=vs.id,
                    description=vs.service.name,
                    quantity=vs.quantity,
                    unit_price=vs.unit_price,
                    discount_amount=vs.discount_amount,
                    total=vs.total_amount,
                ))
            
            # 4. Pull in_house prescription items
            rx_items = await self.prescription_repo.get_in_house_items_for_visit(visit.id)
            for ri in rx_items:
                items.append(InvoiceItem(
                    clinic_id=visit.clinic_id,
                    invoice_id=invoice.id,
                    item_type="medicine",
                    reference_type="prescription_item",
                    reference_id=ri.id,
                    description=f"{ri.medicine.name} ({ri.medicine.strength})",
                    quantity=ri.quantity,
                    unit_price=ri.unit_price,
                    total=ri.total_amount,
                ))
            
            for item in items:
                self.db.add(item)
            
            # 5. Calculate totals
            await self.db.flush()
            invoice.subtotal = sum(item.total for item in items)
            invoice.total_amount = invoice.subtotal - invoice.total_discount + invoice.total_tax
            
            return invoice
    
    async def add_payment(
        self,
        invoice_id: UUID,
        payment_data: PaymentCreate,
        received_by: UUID,
        clinic_id: UUID,
    ):
        async with self.db.begin():
            invoice = await self.repo.get_for_update(invoice_id)
            
            if invoice.status in ("cancelled", "refunded"):
                raise InvalidStateError("Cannot add payment to cancelled invoice")
            
            if payment_data.amount > invoice.balance:
                raise OverpaymentError()
            
            payment = Payment(
                clinic_id=clinic_id,
                invoice_id=invoice_id,
                payment_method=payment_data.payment_method,
                amount=payment_data.amount,
                reference_number=payment_data.reference_number,
                notes=payment_data.notes,
                received_by=received_by,
            )
            self.db.add(payment)
            
            # Update invoice
            invoice.paid_amount += payment_data.amount
            
            if invoice.paid_amount >= invoice.total_amount:
                invoice.status = "paid"
                invoice.paid_at = datetime.utcnow()
                
                # Trigger visit complete?
                # Hoặc để user manually trigger → /visits/{id}/finish
            elif invoice.paid_amount > 0:
                invoice.status = "partially_paid"
            
            return payment
    
    async def void_invoice(self, invoice_id: UUID, reason: str, user_id: UUID, clinic_id: UUID):
        """Void invoice — chỉ paid hoặc partially_paid."""
        async with self.db.begin():
            invoice = await self.repo.get_for_update(invoice_id)
            
            if invoice.status not in ("paid", "partially_paid", "pending"):
                raise InvalidStateError()
            
            old_status = invoice.status
            invoice.status = "cancelled"
            invoice.cancelled_at = datetime.utcnow()
            invoice.cancellation_reason = reason
            
            # Release inventory cho prescription items
            visit = await self.visit_repo.get_by_id(invoice.visit_id)
            await self.prescription_service.cancel_all_for_visit(visit.id)
            
            # Audit
            await self.audit_service.log(
                "void", "invoice", invoice_id,
                old_data={"status": old_status},
                new_data={"reason": reason},
            )
```

### 13.3. API endpoints

```
GET    /api/v1/invoices                   # list, filter
GET    /api/v1/invoices/{id}              # detail with items + payments
PATCH  /api/v1/invoices/{id}              # update (chỉ draft/pending, no payment)

POST   /api/v1/invoices/{id}/items        # add item (manual)
DELETE /api/v1/invoices/{id}/items/{iid}  # remove item
PATCH  /api/v1/invoices/{id}/items/{iid}  # update item (price override)

POST   /api/v1/invoices/{id}/payments     # add payment
DELETE /api/v1/invoices/payments/{pid}    # void payment

POST   /api/v1/invoices/{id}/discount     # apply per-invoice discount
POST   /api/v1/invoices/{id}/void
POST   /api/v1/invoices/{id}/refund
POST   /api/v1/invoices/{id}/print
```

---

## 14. Module HR & Schedule

### 14.1. Schema

```python
class ShiftTemplate(BaseEntity):
    __tablename__ = "shift_template"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Shift(BaseEntity):
    __tablename__ = "shift"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    shift_template_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("shift_template.id"), nullable=True
    )
    shift_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    role_in_shift: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="scheduled", nullable=False)
    # scheduled / cancelled / on_leave / completed
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class RecurringSchedule(BaseEntity):
    __tablename__ = "recurring_schedule"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    shift_template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("shift_template.id"), nullable=False
    )
    days_of_week: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    # [1, 3, 5] = thứ 2, 4, 6 (ISO: 1=Mon, 7=Sun)
    
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class LeaveRequest(BaseEntity):
    __tablename__ = "leave_request"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    leave_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # sick / personal / vacation / other
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    # pending / approved / rejected
    
    approved_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class TimeLog(BaseEntity):
    __tablename__ = "time_log"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    shift_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("shift.id"), nullable=True
    )
    
    check_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    check_in_method: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    # manual / pin / qr / biometric
    check_in_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
```

### 14.2. Indexes

```sql
-- Shift lookup cho capacity check
CREATE INDEX ix_shift_clinic_date_user ON shift (clinic_id, shift_date, user_id)
  WHERE NOT is_deleted AND status = 'scheduled';

CREATE INDEX ix_shift_user_date ON shift (user_id, shift_date) WHERE NOT is_deleted;

-- Time log
CREATE INDEX ix_timelog_user_check_in ON time_log (user_id, check_in_at DESC);

-- Leave overlap check
CREATE INDEX ix_leave_user_dates ON leave_request (user_id, start_date, end_date)
  WHERE status = 'approved' AND NOT is_deleted;
```

### 14.3. API endpoints

```
# Shift templates (admin)
GET    /api/v1/shift-templates
POST   /api/v1/shift-templates
PATCH  /api/v1/shift-templates/{id}
DELETE /api/v1/shift-templates/{id}

# Shifts
GET    /api/v1/shifts?from=...&to=...&user_id=...
POST   /api/v1/shifts                    # tạo shift cụ thể
PATCH  /api/v1/shifts/{id}
DELETE /api/v1/shifts/{id}

# Recurring
GET    /api/v1/recurring-schedules
POST   /api/v1/recurring-schedules
POST   /api/v1/recurring-schedules/{id}/generate-shifts?until=2026-12-31

# Leave
GET    /api/v1/leave-requests?status=pending
POST   /api/v1/leave-requests           # user tự xin
POST   /api/v1/leave-requests/{id}/approve
POST   /api/v1/leave-requests/{id}/reject

# Attendance
POST   /api/v1/attendance/check-in
POST   /api/v1/attendance/check-out
GET    /api/v1/attendance/me?from=...&to=...
GET    /api/v1/attendance?user_id=...&from=...&to=...   # admin view
GET    /api/v1/attendance/export?from=...&to=...        # CSV/Excel

# Reports
GET    /api/v1/hr/timesheet?month=2026-04   # tổng giờ làm theo nhân viên
```

---

## 15. RBAC Implementation

### 15.1. Permission decorator

```python
# app/core/permissions.py

from fastapi import Depends, HTTPException, status
from app.core.db import current_user_id, current_clinic_id


async def get_current_user_permissions(db: AsyncSession = Depends(get_db)) -> set[str]:
    user_id = current_user_id.get()
    if not user_id:
        raise HTTPException(401)
    
    # Cache trong Redis cho mỗi user
    cache_key = f"user_perms:{user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return set(json.loads(cached))
    
    # Compute: roles permissions + extra grants - extra denies
    role_perms = await db.execute(
        select(RolePermission.permission_code)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user_id)
    )
    perms = {r[0] for r in role_perms}
    
    extras = await db.execute(
        select(UserExtraPermission.permission_code, UserExtraPermission.grant_type)
        .where(UserExtraPermission.user_id == user_id)
    )
    for code, grant_type in extras:
        if grant_type == "grant":
            perms.add(code)
        else:
            perms.discard(code)
    
    await redis.setex(cache_key, 300, json.dumps(list(perms)))  # 5 min cache
    return perms


def require_permission(*required: str):
    """Dependency: require user have at least one of the permissions."""
    async def checker(perms: set[str] = Depends(get_current_user_permissions)):
        if not any(p in perms for p in required):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Required permission: {' or '.join(required)}",
            )
    return checker


# Usage
@router.post("/patients", dependencies=[Depends(require_permission("patient.write"))])
async def create_patient(...):
    ...
```

### 15.2. Permission seed data

```python
# scripts/seed_permissions.py

PERMISSIONS = [
    # Patients
    ("patient.read", "Xem bệnh nhân"),
    ("patient.write", "Tạo/sửa bệnh nhân"),
    ("patient.merge", "Merge hồ sơ"),
    ("patient.delete", "Xóa bệnh nhân"),
    
    # Visits
    ("visit.read", "Xem lượt khám"),
    ("visit.write", "Tạo lượt khám"),
    ("visit.cancel", "Hủy lượt khám"),
    
    # Vitals
    ("vital.read", "Xem vitals"),
    ("vital.write", "Nhập vitals"),
    ("vital.delete", "Xóa vitals"),
    ("vital.schema_manage", "Quản lý vital schema"),
    
    # Services
    ("service.catalog_manage", "Quản lý service catalog"),
    ("service.perform", "Thực hiện service"),
    
    # Prescriptions
    ("prescription.write", "Kê đơn thuốc"),
    ("prescription.cancel", "Hủy đơn thuốc"),
    
    # Pharmacy
    ("pharmacy.dispense", "Cấp phát thuốc"),
    ("pharmacy.substitute_batch", "Thay batch khi cấp phát"),
    ("pharmacy.adjust_stock", "Điều chỉnh tồn kho"),
    
    # Inventory
    ("inventory.read", "Xem kho"),
    ("inventory.manage_catalog", "Quản lý catalog thuốc"),
    ("inventory.purchase_in", "Nhập kho"),
    
    # Billing
    ("invoice.create", "Tạo hóa đơn"),
    ("invoice.modify", "Sửa hóa đơn"),
    ("invoice.void", "Hủy hóa đơn"),
    ("invoice.refund", "Hoàn tiền"),
    ("payment.receive", "Nhận thanh toán"),
    
    # HR
    ("shift.manage", "Quản lý ca trực"),
    ("attendance.manage", "Quản lý chấm công"),
    ("leave.approve", "Duyệt nghỉ phép"),
    
    # Users
    ("user.manage", "Quản lý nhân viên"),
    ("role.manage", "Quản lý roles"),
    
    # Reports
    ("report.view", "Xem báo cáo"),
    ("report.financial", "Xem báo cáo tài chính"),
    
    # Settings
    ("settings.clinic", "Cấu hình clinic"),
    ("settings.vital_schema", "Cấu hình vital schema"),
]


ROLE_PERMISSIONS = {
    "admin": "*",  # all permissions
    "doctor": [
        "patient.read", "patient.write",
        "visit.read", "visit.write",
        "vital.read", "vital.write",
        "service.perform",
        "prescription.write", "prescription.cancel",
        "inventory.read",
        "report.view",
    ],
    "nurse": [
        "patient.read", "patient.write",
        "visit.read", "visit.write",
        "vital.read", "vital.write",
        "service.perform",
    ],
    "pharmacist": [
        "patient.read",
        "visit.read",
        "inventory.read", "inventory.manage_catalog", "inventory.purchase_in",
        "pharmacy.dispense", "pharmacy.substitute_batch", "pharmacy.adjust_stock",
    ],
    "receptionist": [
        "patient.read", "patient.write",
        "visit.read", "visit.write", "visit.cancel",
        "invoice.create", "invoice.modify",
        "payment.receive",
    ],
}
```

---

## 16. Cross-cutting Concerns

### 16.1. Notification

```python
class Notification(BaseEntity):
    __tablename__ = "notification"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

API:
```
GET    /api/v1/notifications?unread_only=true
POST   /api/v1/notifications/{id}/read
POST   /api/v1/notifications/mark-all-read
```

### 16.2. Settings

```python
class ClinicSettings(Base, TimestampMixin):
    __tablename__ = "clinic_settings"

    clinic_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("clinic.id"), primary_key=True
    )
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    updated_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
```

Service helper:
```python
class SettingsService:
    async def get(self, clinic_id: UUID) -> ClinicSettingsDTO:
        cache_key = f"clinic_settings:{clinic_id}"
        cached = await redis.get(cache_key)
        if cached:
            return ClinicSettingsDTO.parse_raw(cached)
        
        row = await self.repo.get_by_clinic_id(clinic_id)
        if not row:
            return ClinicSettingsDTO.default()
        
        dto = ClinicSettingsDTO(**row.settings)
        await redis.setex(cache_key, 300, dto.json())
        return dto
    
    async def update(self, clinic_id: UUID, patch: dict, user_id: UUID):
        async with self.db.begin():
            row = await self.repo.get_for_update(clinic_id)
            if not row:
                row = ClinicSettings(clinic_id=clinic_id, settings={})
                self.db.add(row)
            
            # Deep merge
            row.settings = deep_merge(row.settings, patch)
            row.updated_by = user_id
            
            await redis.delete(f"clinic_settings:{clinic_id}")
```

### 16.3. Default settings template

```python
DEFAULT_SETTINGS = {
    "general": {
        "name": "",
        "address": "",
        "phone": "",
        "email": "",
        "tax_code": "",
        "logo_url": None,
    },
    "operating_hours": {
        "monday": {"open": "07:30", "close": "17:30"},
        "tuesday": {"open": "07:30", "close": "17:30"},
        "wednesday": {"open": "07:30", "close": "17:30"},
        "thursday": {"open": "07:30", "close": "17:30"},
        "friday": {"open": "07:30", "close": "17:30"},
        "saturday": {"open": "07:30", "close": "12:00"},
        "sunday": None,  # closed
    },
    "appointment": {
        "slot_duration_minutes": 30,
        "buffer_minutes": 15,
        "no_show_minutes": 30,
        "advance_booking_days": 30,
        "auto_confirm": False,
    },
    "queue": {
        "require_vitals_before_consultation": False,
        "auto_priority_for_elderly": True,
        "elderly_age_threshold": 75,
    },
    "inventory": {
        "near_expiry_days": 90,
        "low_stock_alert": True,
    },
    "prescription": {
        "print_mode": "all",
        "show_external_warning": True,
    },
    "billing": {
        "discount_threshold_percent": 10,
        "require_discount_reason": True,
        "invoice_template": "default",
    },
    "specialty": "general",
}
```

---

## 17. API Design Patterns

### 17.1. FastAPI app setup

```python
# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.tenancy import TenancyMiddleware
from app.core.exceptions import setup_exception_handlers
from app.modules import (
    auth, users, patients, appointments, visits,
    vitals, services, medicines, inventory, prescriptions,
    pharmacy, billing, hr, reporting, notifications, admin,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.connect()
    yield
    # Shutdown
    await redis_client.disconnect()


app = FastAPI(
    title="Clinic Management System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TenancyMiddleware)

setup_exception_handlers(app)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(patients.router, prefix="/api/v1")
# ...
```

### 17.2. Custom exceptions

```python
# app/core/exceptions.py

from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "Internal server error"
    
    def __init__(self, message: str = None, **details):
        self.message = message or self.message
        self.details = details


class NotFoundError(AppException):
    status_code = 404
    code = "NOT_FOUND"
    message = "Resource not found"


class ValidationError(AppException):
    status_code = 422
    code = "VALIDATION_ERROR"
    message = "Validation failed"


class PermissionDeniedError(AppException):
    status_code = 403
    code = "PERMISSION_DENIED"
    message = "Permission denied"


class InvalidStateError(AppException):
    status_code = 400
    code = "INVALID_STATE"


class InsufficientStockError(AppException):
    status_code = 400
    code = "INSUFFICIENT_STOCK"


class ConflictError(AppException):
    status_code = 409
    code = "CONFLICT"


class OptimisticLockError(ConflictError):
    code = "OPTIMISTIC_LOCK_CONFLICT"
    message = "Resource has been modified by another user"


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
                "meta": {"request_id": request.state.request_id},
            },
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        # Log full error
        logger.exception("Database error")
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "DATABASE_ERROR", "message": "Database error"}},
        )
```

### 17.3. Request ID middleware

```python
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

### 17.4. Pydantic schemas pattern

```python
# app/modules/patients/schemas.py

from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from uuid import UUID


class PatientBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    gender: Literal["male", "female", "other"]
    date_of_birth: date | None = None
    birth_year: int | None = None
    phone: str | None = Field(None, max_length=20)
    email: str | None = None
    # ... other fields


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    """All fields optional cho PATCH."""
    full_name: str | None = Field(None, min_length=1, max_length=200)
    phone: str | None = None
    # ... other fields


class PatientResponse(PatientBase):
    id: UUID
    patient_code: str
    clinic_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PatientListResponse(BaseModel):
    data: list[PatientResponse]
    meta: PaginationMeta
```

---

## 18. Critical Workflows

### 18.1. Visit lifecycle (sequence)

```
[Receptionist]                    [Backend]                  [Doctor/Nurse]
      │                              │                              │
      │ POST /visits                 │                              │
      │─────────────────────────────→│                              │
      │   {patient_id, ...}          │                              │
      │                              │ generate visit_number        │
      │                              │ create Visit (WAITING)       │
      │                              │ audit_log("create")          │
      │ ←─────────────────────────── │                              │
      │   Visit                      │                              │
      │                              │                              │
      │                              │ ←── GET /queue ──────────────│
      │                              │                              │ [Nurse]
      │                              │ ─── 200 OK ─────────────────→│
      │                              │                              │
      │                              │ ←── POST /visits/{id}/vitals │
      │                              │ validate (dynamic schema)    │
      │                              │ snapshot schema_version      │
      │                              │ create VisitVitals           │
      │                              │ ─── 201 ────────────────────→│
      │                              │                              │
      │                              │ ←── POST /queue/call-next ───│
      │                              │                              │ [Doctor]
      │                              │ FOR UPDATE SKIP LOCKED       │
      │                              │ visit.status = IN_PROGRESS   │
      │                              │ visit.doctor_id = current    │
      │                              │ ─── 200 (Visit) ────────────→│
      │                              │                              │
      │                              │ ←── POST /visits/{id}/services
      │                              │ ←── POST /visits/{id}/prescriptions
      │                              │     (FEFO reserve in_house)  │
      │                              │ ─── 201 ────────────────────→│
      │                              │                              │
      │                              │ ←── POST /visits/{id}/complete
      │                              │ visit.status=AWAITING_PAYMENT│
      │                              │ create Invoice from visit    │
      │                              │ ─── 200 ───────────────────→│
      │                              │                              │
      │ POST /invoices/{id}/payments │                              │
      │─────────────────────────────→│                              │
      │   {method, amount}           │                              │
      │                              │ create Payment               │
      │                              │ update invoice.paid_amount   │
      │                              │ if balance==0: status=paid   │
      │ ←─────────────────────────── │                              │
      │                              │                              │
      │                              │ ←── POST /pi/{id}/dispense ──│
      │                              │                              │ [Pharmacist]
      │                              │ deduct batch actual_qty      │
      │                              │ release reserved             │
      │                              │ stock_movement log           │
      │                              │ ─── 200 ────────────────────→│
      │                              │                              │
      │ POST /visits/{id}/finish     │                              │
      │─────────────────────────────→│                              │
      │                              │ visit.status = COMPLETED     │
      │ ←─────────────────────────── │                              │
```

### 18.2. Reserve & dispense

```
[Doctor]                  [Backend]                          [Database]
   │                          │                                  │
   │ POST /prescriptions      │                                  │
   │─────────────────────────→│                                  │
   │   {items: [...]}         │                                  │
   │                          │ BEGIN TRANSACTION                │
   │                          │ ─────────────────────────────────→│
   │                          │                                  │
   │                          │ For each in_house item:          │
   │                          │   SELECT batch FOR UPDATE        │
   │                          │   ORDER BY expiry, received      │
   │                          │ ─────────────────────────────────→│
   │                          │                                  │
   │                          │   ←── batches (locked) ──────────│
   │                          │                                  │
   │                          │   greedy reserve:                │
   │                          │     batch.reserved += take       │
   │                          │     create PIB(reserved)         │
   │                          │                                  │
   │                          │ COMMIT                           │
   │                          │ ─────────────────────────────────→│
   │ ←──── Prescription ──────│                                  │
   │                          │                                  │

[Pharmacist]              [Backend]                          [Database]
   │                          │                                  │
   │ POST /pi/{id}/dispense   │                                  │
   │─────────────────────────→│                                  │
   │                          │ BEGIN TRANSACTION                │
   │                          │                                  │
   │                          │ Get reservations + batches       │
   │                          │ FOR UPDATE                       │
   │                          │                                  │
   │                          │ For each reservation:            │
   │                          │   batch.actual -= qty            │
   │                          │   batch.reserved -= qty          │
   │                          │   reservation.status = dispensed │
   │                          │   INSERT stock_movement          │
   │                          │                                  │
   │                          │ item.in_house_status = dispensed │
   │                          │                                  │
   │                          │ Update prescription status       │
   │                          │ COMMIT                           │
   │ ←──── 200 OK ────────────│                                  │
```

### 18.3. Cancel visit → release reservations

```python
async def cancel_visit(self, visit_id: UUID, reason: str, user_id: UUID, clinic_id: UUID):
    async with self.db.begin():
        visit = await self.repo.get_for_update(visit_id)
        
        if visit.status == "COMPLETED":
            raise InvalidStateError("Cannot cancel completed visit")
        
        # 1. Cancel visit
        visit.status = "CANCELLED"
        visit.cancelled_at = datetime.utcnow()
        visit.cancellation_reason = reason
        
        # 2. Release prescription reservations
        prescriptions = await self.prescription_repo.get_by_visit(visit_id)
        for rx in prescriptions:
            if rx.status not in ("dispensed", "cancelled"):
                for item in rx.items:
                    if item.dispense_source == "in_house" and item.in_house_status == "reserved":
                        await self.pharmacy_service.cancel_reservation(item.id, reason, user_id, clinic_id)
                rx.status = "cancelled"
        
        # 3. Cancel invoice if exists
        invoice = await self.invoice_repo.get_by_visit(visit_id)
        if invoice and invoice.status not in ("paid", "cancelled"):
            invoice.status = "cancelled"
            invoice.cancelled_at = datetime.utcnow()
            invoice.cancellation_reason = reason
        
        await self.audit_service.log("cancel", "visit", visit_id, new_data={"reason": reason})
```

---

## 19. Background Jobs

### 19.1. Setup with Arq

```python
# app/workers/scheduler.py

from arq import cron

from app.workers.tasks import (
    auto_no_show_appointments,
    expire_low_stock_alerts,
    near_expiry_alerts,
    appointment_reminders,
    daily_revenue_report,
)


class WorkerSettings:
    redis_settings = ...
    
    cron_jobs = [
        # Mỗi 5 phút: check appointment quá giờ → no_show
        cron(auto_no_show_appointments, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
        
        # Mỗi giờ: appointment reminder (T-24h, T-2h)
        cron(appointment_reminders, minute=0),
        
        # Mỗi sáng 6h: alert tồn kho thấp
        cron(expire_low_stock_alerts, hour=6, minute=0),
        
        # Mỗi sáng 7h: alert sắp hết hạn
        cron(near_expiry_alerts, hour=7, minute=0),
        
        # Cuối ngày 23h: tổng kết doanh thu
        cron(daily_revenue_report, hour=23, minute=0),
    ]
    
    functions = [
        send_notification,
        generate_recurring_shifts,
        export_attendance,
    ]
```

### 19.2. No-show job

```python
async def auto_no_show_appointments(ctx):
    """Mark appointments quá giờ là no_show."""
    async with AsyncSessionLocal() as db:
        # Lấy tất cả clinics
        clinics = (await db.execute(select(Clinic).where(Clinic.is_active))).scalars()
        
        for clinic in clinics:
            settings = await settings_service.get(clinic.id)
            no_show_min = settings.appointment.no_show_minutes
            
            cutoff = datetime.utcnow() - timedelta(minutes=no_show_min)
            
            stmt = (
                update(Appointment)
                .where(
                    Appointment.clinic_id == clinic.id,
                    Appointment.scheduled_at < cutoff,
                    Appointment.status.in_(["scheduled", "confirmed"]),
                )
                .values(status="no_show")
            )
            result = await db.execute(stmt)
            await db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Marked {result.rowcount} no-show in clinic {clinic.id}")
```

### 19.3. Notification job

```python
async def near_expiry_alerts(ctx):
    """Alert sắp hết hạn cho từng clinic."""
    async with AsyncSessionLocal() as db:
        clinics = (await db.execute(select(Clinic).where(Clinic.is_active))).scalars().all()
        
        for clinic in clinics:
            settings = await settings_service.get(clinic.id)
            days = settings.inventory.near_expiry_days
            
            cutoff = date.today() + timedelta(days=days)
            
            batches = await db.execute(
                select(Batch, Medicine.name)
                .join(InventoryItem, Batch.inventory_item_id == InventoryItem.id)
                .join(Medicine, InventoryItem.medicine_id == Medicine.id)
                .where(
                    Batch.clinic_id == clinic.id,
                    Batch.expiry_date <= cutoff,
                    Batch.expiry_date >= date.today(),
                    Batch.actual_quantity > 0,
                    Batch.is_deleted == False,
                )
            )
            
            # Tạo notification cho pharmacist & admin
            recipients = await get_users_with_perm(clinic.id, "pharmacy.dispense")
            
            for user_id in recipients:
                if batches:
                    notif = Notification(
                        clinic_id=clinic.id,
                        user_id=user_id,
                        type="near_expiry",
                        title=f"{len(batches.all())} lô thuốc sắp hết hạn",
                        body="...",
                    )
                    db.add(notif)
            
            await db.commit()
```

---

## 20. Offline Sync

### 20.1. Local SQLite schema (Tauri)

Mirror các bảng chính từ server, thêm field sync:

```sql
CREATE TABLE patient (
    id UUID PRIMARY KEY,
    -- ... tất cả field như server ...
    
    -- Sync metadata
    sync_status TEXT NOT NULL DEFAULT 'synced',
    -- 'synced' | 'pending_create' | 'pending_update' | 'pending_delete'
    sync_attempted_at TIMESTAMP,
    sync_error TEXT,
    server_version INTEGER  -- last known server version
);
```

### 20.2. Sync engine architecture

```typescript
// src-tauri/sync/engine.ts

class SyncEngine {
  async syncAll() {
    if (!await isOnline()) return;
    
    try {
      // 1. Push local changes
      await this.pushChanges();
      
      // 2. Pull server changes
      await this.pullChanges();
    } catch (e) {
      console.error("Sync failed", e);
    }
  }
  
  async pushChanges() {
    const pending = await db.query(
      "SELECT * FROM patient WHERE sync_status != 'synced' LIMIT 50"
    );
    
    for (const record of pending) {
      try {
        if (record.sync_status === 'pending_create') {
          await api.post('/patients', record);
        } else if (record.sync_status === 'pending_update') {
          await api.patch(`/patients/${record.id}`, record);
        } else if (record.sync_status === 'pending_delete') {
          await api.delete(`/patients/${record.id}`);
        }
        
        await db.execute(
          "UPDATE patient SET sync_status='synced' WHERE id=?",
          [record.id]
        );
      } catch (e) {
        if (e.status === 409) {
          // Conflict — show resolution UI
          await this.handleConflict(record, e.response);
        } else {
          await db.execute(
            "UPDATE patient SET sync_attempted_at=?, sync_error=? WHERE id=?",
            [new Date(), e.message, record.id]
          );
        }
      }
    }
  }
  
  async pullChanges() {
    const lastSync = await getLastSyncTime();
    const response = await api.get('/sync/changes', {
      params: { since: lastSync.toISOString() }
    });
    
    for (const change of response.data) {
      // Apply change to local DB
      await this.applyChange(change);
    }
    
    await setLastSyncTime(new Date());
  }
}
```

### 20.3. Server sync endpoint

```python
@router.get("/sync/changes")
async def get_changes(
    since: datetime,
    db: AsyncSession = Depends(get_db),
):
    """Trả về changes từ thời điểm `since`."""
    clinic_id = current_clinic_id.get()
    
    # Lấy tất cả entity được modified sau `since`
    changes = []
    
    for Model in [Patient, Visit, Appointment, ...]:  # các bảng cần sync
        records = await db.execute(
            select(Model).where(
                Model.clinic_id == clinic_id,
                Model.updated_at > since,
            )
        )
        for r in records.scalars():
            changes.append({
                "entity_type": Model.__tablename__,
                "operation": "delete" if r.is_deleted else "upsert",
                "data": serialize(r),
                "version": r.version,
            })
    
    return {"changes": changes, "server_time": datetime.utcnow()}
```

### 20.4. Conflict resolution

```typescript
async handleConflict(localRecord, serverError) {
  const serverData = serverError.response.data.server_record;
  
  // Strategy 1: Last-write-wins (auto)
  if (localRecord.updated_at > serverData.updated_at) {
    // Force push
    await api.put(`/patients/${localRecord.id}?force=true`, localRecord);
  }
  
  // Strategy 2: Show conflict UI cho user resolve
  await showConflictDialog({
    local: localRecord,
    server: serverData,
    onResolve: async (resolved) => {
      await api.patch(`/patients/${localRecord.id}`, resolved);
    }
  });
}
```

---

## 21. Migration Strategy

### 21.1. Alembic setup

```python
# alembic/env.py

from app.core.base_model import Base
from app.modules import (
    auth, users, patients, ...
)  # import all models for autogenerate

target_metadata = Base.metadata


def run_migrations_online():
    connectable = create_engine(settings.DATABASE_URL)
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            compare_type=True,
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

### 21.2. Initial migration structure

```
versions/
├── 0001_create_clinic_and_users.py      # core tables
├── 0002_setup_rbac.py                    # roles, permissions, mappings
├── 0003_create_patients.py
├── 0004_create_appointments.py
├── 0005_create_visits.py
├── 0006_create_vitals_dynamic.py
├── 0007_create_services.py
├── 0008_create_medicines_inventory.py
├── 0009_create_prescriptions.py
├── 0010_create_billing.py
├── 0011_create_hr_schedule.py
├── 0012_create_audit_log.py
├── 0013_create_notifications.py
├── 0014_setup_rls_policies.py            # RLS cuối cùng
└── 0015_seed_permissions_and_presets.py
```

### 21.3. RLS migration template

```python
# 0014_setup_rls_policies.py

def upgrade():
    tables_with_clinic_id = [
        "user", "role", "patient", "patient_relation", "appointment", "visit",
        "visit_vitals", "vital_field_definition", "service", "visit_service",
        "medicine", "inventory_item", "batch", "supplier",
        "prescription", "prescription_item", "prescription_item_batch",
        "invoice", "invoice_item", "payment",
        "shift_template", "shift", "recurring_schedule", "leave_request", "time_log",
        "notification",
    ]
    
    for table in tables_with_clinic_id:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            FOR ALL
            USING (clinic_id::text = current_setting('app.current_clinic_id', true));
        """)
        # Bypass cho admin role (DB-level)
        op.execute(f"""
            CREATE POLICY admin_bypass ON {table}
            FOR ALL TO postgres
            USING (true);
        """)
```

### 21.4. Forward-only deployment

Quy tắc:
1. Tạo migration lên branch dev → test trên local + CI.
2. Apply trên staging database → smoke test.
3. Apply trên production → monitor.
4. **Không dùng `alembic downgrade`** trên production. Có lỗi → tạo migration mới fix.

---

## 22. Testing Strategy

### 22.1. Test pyramid

```
       ┌────────────┐
       │   E2E      │  (~5%)  Tauri client + backend
       └────────────┘
     ┌────────────────┐
     │  Integration   │  (~25%) API + DB real
     └────────────────┘
   ┌────────────────────┐
   │      Unit          │  (~70%)  Pure functions, services with mocks
   └────────────────────┘
```

### 22.2. Test setup

```python
# tests/conftest.py

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.core.db import get_db


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/cms_test")
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine):
    """Session per test, rollback at end."""
    async with test_engine.connect() as conn:
        async with conn.begin():
            session = AsyncSession(bind=conn)
            yield session
            await session.rollback()


@pytest.fixture
async def test_clinic(test_db):
    clinic = Clinic(code="TEST001", name="Test Clinic", specialty="general")
    test_db.add(clinic)
    await test_db.flush()
    return clinic


@pytest.fixture
async def test_admin_user(test_db, test_clinic):
    user = User(
        clinic_id=test_clinic.id,
        username="admin",
        password_hash=hash_password("admin123"),
        full_name="Admin",
    )
    # ... assign admin role
    test_db.add(user)
    await test_db.flush()
    return user


@pytest.fixture
async def authenticated_client(test_admin_user, test_clinic):
    """HTTP client with auth token."""
    token = create_access_token(test_admin_user.id, test_clinic.id, ["admin"])
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        client.headers["Authorization"] = f"Bearer {token}"
        yield client
```

### 22.3. Test categories

```python
# tests/unit/test_fefo.py — pure logic
async def test_fefo_picks_oldest_expiry_first():
    batches = [
        Batch(id="b1", expiry_date=date(2026, 12, 31), available=100),
        Batch(id="b2", expiry_date=date(2026, 6, 30), available=50),
        Batch(id="b3", expiry_date=date(2027, 1, 31), available=200),
    ]
    
    result = fefo_pick(batches, needed=120)
    
    assert result == [
        ("b2", 50),   # oldest first, take all 50
        ("b1", 70),   # next oldest, take 70
    ]


# tests/integration/test_prescription_flow.py — full DB
async def test_prescription_reserve_and_dispense(test_db, test_clinic, test_doctor, test_pharmacist):
    # Setup: medicine + inventory + batches
    # Action: create prescription → check batches reserved
    # Action: dispense → check batches deducted, stock_movement created
    ...


# tests/integration/test_api_visits.py — HTTP layer
async def test_create_visit(authenticated_client, test_patient):
    response = await authenticated_client.post("/api/v1/visits", json={
        "patient_id": str(test_patient.id),
        "chief_complaint": "Sốt cao",
    })
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "WAITING"
```

### 22.4. Coverage targets

- Unit: > 90% cho services
- Integration: cover happy path + error path cho mọi endpoint critical
- E2E: 5-10 scenarios cốt lõi (login, full visit lifecycle, prescription dispense)

---

## 23. Deployment Architecture

### 23.1. Production stack

```
                   ┌──────────────┐
                   │  Cloudflare  │  (CDN + DDoS)
                   └──────┬───────┘
                          │
                   ┌──────▼───────┐
                   │   Nginx      │  (SSL termination, rate limit)
                   └──────┬───────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
     ┌──────────┐  ┌──────────┐  ┌──────────┐
     │ FastAPI  │  │ FastAPI  │  │ FastAPI  │  (3+ Uvicorn workers)
     └────┬─────┘  └────┬─────┘  └────┬─────┘
          │             │             │
          └─────────────┼─────────────┘
                        ▼
              ┌──────────────────┐
              │  PgBouncer       │  (connection pool)
              └────────┬─────────┘
                       ▼
              ┌──────────────────┐
              │  PostgreSQL 15   │  (primary + replica)
              │  - Streaming rep │
              │  - Daily backup  │
              └──────────────────┘
                       
              ┌──────────────────┐
              │  Redis           │  (session, cache, queue)
              └──────────────────┘
              
              ┌──────────────────┐
              │  Arq Workers     │  (background jobs)
              └──────────────────┘
              
              ┌──────────────────┐
              │  S3-compatible   │  (file uploads, backup)
              └──────────────────┘
```

### 23.2. Docker compose dev

```yaml
# docker/docker-compose.yml

version: "3.9"

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: cms
      POSTGRES_USER: cms
      POSTGRES_PASSWORD: cms
    ports: ["5432:5432"]
    volumes:
      - pgdata:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  
  api:
    build: ..
    command: uvicorn app.main:app --host 0.0.0.0 --reload
    environment:
      DATABASE_URL: postgresql+asyncpg://cms:cms@postgres:5432/cms
      REDIS_URL: redis://redis:6379/0
    ports: ["8000:8000"]
    volumes:
      - ../app:/app/app
    depends_on:
      - postgres
      - redis
  
  worker:
    build: ..
    command: arq app.workers.scheduler.WorkerSettings
    environment:
      DATABASE_URL: postgresql+asyncpg://cms:cms@postgres:5432/cms
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

volumes:
  pgdata:
```

### 23.3. Backup strategy

- **PostgreSQL:** Daily `pg_basebackup` + WAL archiving cho PITR (Point-In-Time Recovery).
- **RPO target:** < 1 giờ.
- **RTO target:** < 4 giờ.
- **Retention:** 30 ngày daily, 12 tháng monthly.
- **Test restore:** monthly automated test restore từ backup.
- **Encryption:** backup encrypted với GPG/age trước khi upload S3.

### 23.4. Monitoring

- **Logs:** structured JSON → Loki/Grafana hoặc CloudWatch.
- **Metrics:** Prometheus + Grafana — request rate, latency p95/p99, error rate, DB pool.
- **Tracing:** OpenTelemetry — trace có `clinic_id` tag.
- **Alerts:**
  - Error rate > 1% (5 min window)
  - Latency p95 > 1s
  - DB connections > 80%
  - Disk > 80%
  - Backup failure
  - Redis down

---

## 24. Security Checklist

### 24.1. Authentication & Session

- [x] Bcrypt cho password (cost ≥ 12)
- [x] JWT với HS256 hoặc RS256, secret rotation kế hoạch
- [x] Access token ngắn (15 phút), refresh token dài hơn (7-30 ngày)
- [x] Refresh token có thể revoke (Redis blacklist hoặc DB)
- [x] Account lockout sau N lần sai
- [x] Rate limit login endpoint (Redis)
- [x] Force password change khi admin reset
- [x] Password policy: min 8 chars, mix

### 24.2. Authorization

- [x] RBAC với role + permission + extras
- [x] Permission check ở mọi endpoint qua `Depends(require_permission)`
- [x] RLS bật ở DB layer (defense in depth)
- [x] Session variable set per request (clinic_id, user_id)
- [x] Cross-tenant access = 404 (không phải 403, để tránh leak existence)

### 24.3. Input validation

- [x] Pydantic validation cho mọi input
- [x] SQL injection: dùng SQLAlchemy parameterized, không string interpolation
- [x] XSS: escape output, dùng React (auto-escape)
- [x] Path traversal: validate file path
- [x] File upload: check MIME type, size limit, scan malware (phase 2)

### 24.4. Data protection

- [x] TLS 1.2+ bắt buộc
- [x] Database at-rest encryption (TDE hoặc filesystem)
- [x] Backup encrypted
- [x] PII không log raw vào application log
- [x] Mask sensitive fields trong UI cho role thấp

### 24.5. Audit & monitoring

- [x] Audit log mọi CUD trên entity nghiệp vụ
- [x] Audit log read sensitive data
- [x] Login/logout/failed login logged
- [x] Permission denied events logged
- [x] Detect anomaly: bulk export, unusual access pattern

### 24.6. Operational

- [x] Secret management: env vars, không commit .env
- [x] Dependency scanning: Dependabot/Snyk
- [x] OWASP Top 10 review periodic
- [x] Penetration test trước launch + annual
- [x] Disaster recovery plan + tested restore
- [x] Privacy policy + ToS publish
- [x] DPA (Data Processing Agreement) với clinic

---

## Phụ lục: Quick Reference Tables

### A. Tables list

| # | Table | Module | Note |
|---|---|---|---|
| 1 | `clinic` | core | Tenant |
| 2 | `clinic_settings` | admin | JSONB |
| 3 | `user` | users | |
| 4 | `role` | users | |
| 5 | `permission` | users | system catalog |
| 6 | `role_permission` | users | M2M |
| 7 | `user_role` | users | M2M |
| 8 | `user_extra_permission` | users | grant/deny |
| 9 | `patient` | patients | |
| 10 | `patient_relation` | patients | guardian |
| 11 | `appointment` | appointments | |
| 12 | `visit` | visits | central entity |
| 13 | `vital_field_definition` | vitals | dynamic schema |
| 14 | `vital_schema_version` | vitals | snapshot history |
| 15 | `visit_vitals` | vitals | JSONB values |
| 16 | `system_vital_preset` | vitals | master data |
| 17 | `service` | services | catalog |
| 18 | `visit_service` | services | rendered |
| 19 | `medicine` | medicines | catalog |
| 20 | `supplier` | inventory | |
| 21 | `inventory_item` | inventory | per clinic |
| 22 | `batch` | inventory | lô |
| 23 | `stock_movement` | inventory | append-only |
| 24 | `prescription` | prescriptions | |
| 25 | `prescription_item` | prescriptions | |
| 26 | `prescription_item_batch` | prescriptions | reservation |
| 27 | `invoice` | billing | |
| 28 | `invoice_item` | billing | |
| 29 | `payment` | billing | multi-payment |
| 30 | `shift_template` | hr | |
| 31 | `shift` | hr | concrete |
| 32 | `recurring_schedule` | hr | |
| 33 | `leave_request` | hr | |
| 34 | `time_log` | hr | attendance |
| 35 | `notification` | notifications | |
| 36 | `audit_log` | audit | append-only |

### B. Common queries cheat sheet

```sql
-- Queue hiện tại
SELECT v.*, p.full_name, p.patient_code
FROM visit v
JOIN patient p ON p.id = v.patient_id
WHERE v.clinic_id = :cid
  AND v.status = 'WAITING'
  AND NOT v.is_deleted
ORDER BY v.priority DESC, v.is_returning DESC, v.check_in_at ASC;

-- Tồn kho hiện tại của 1 medicine
SELECT 
  m.name,
  SUM(b.actual_quantity) AS total_actual,
  SUM(b.reserved_quantity) AS total_reserved,
  SUM(b.actual_quantity - b.reserved_quantity) AS available
FROM medicine m
JOIN inventory_item ii ON ii.medicine_id = m.id
JOIN batch b ON b.inventory_item_id = ii.id
WHERE m.clinic_id = :cid
  AND m.id = :mid
  AND NOT b.is_deleted
  AND b.expiry_date >= CURRENT_DATE
  AND NOT b.is_recalled;

-- Doanh thu theo ngày
SELECT 
  DATE(i.paid_at) AS day,
  SUM(i.total_amount) AS revenue,
  COUNT(*) AS invoice_count
FROM invoice i
WHERE i.clinic_id = :cid
  AND i.status = 'paid'
  AND i.paid_at BETWEEN :from AND :to
GROUP BY DATE(i.paid_at)
ORDER BY day;

-- Vitals trend (huyết áp 6 tháng)
SELECT 
  v.recorded_at,
  (v.values->>'systolic_bp')::int AS systolic,
  (v.values->>'diastolic_bp')::int AS diastolic
FROM visit_vitals v
JOIN visit vi ON vi.id = v.visit_id
WHERE vi.patient_id = :pid
  AND v.clinic_id = :cid
  AND v.recorded_at > NOW() - INTERVAL '6 months'
  AND v.values ? 'systolic_bp'
ORDER BY v.recorded_at;
```

---

## Bước tiếp theo

Tài liệu thiết kế đã đầy đủ cho việc bắt đầu implementation. Các bước tiếp theo cụ thể:

1. **Setup project skeleton** — pyproject.toml, Alembic, Docker, CI
2. **Implement core foundation** — base model, tenancy, audit, RLS
3. **Sprint 1: Auth + RBAC + Tenant onboarding**
4. **Sprint 2-N: từng module theo roadmap MVP**

Khi bắt đầu code, tham chiếu file này như single source of truth. Mọi thay đổi thiết kế cần update file + version bump.

---

*Tài liệu này là output kỹ thuật của giai đoạn thiết kế. Cần được review bởi senior backend, DBA, security engineer trước khi implement. Quy ước, schema, và workflow trong tài liệu cần được điều chỉnh dựa trên feedback thực tế khi triển khai.*
