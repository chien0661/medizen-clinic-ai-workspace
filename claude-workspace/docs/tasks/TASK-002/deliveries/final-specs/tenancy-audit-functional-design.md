# Thiết kế chi tiết — Hạ tầng Tenancy + RLS + Audit Log (TASK-002)

**Ngày**: 2026-04-26  
**Trạng thái**: DONE  
**Phạm vi**: TASK-002 v1  
**Kiểm thử**: 148/148 pass (100%), coverage 95% tenancy.py, 100% rls.py/db_security.py/audit_log.py  

---

## 1. Mục đích

Thiết lập hạ tầng bảo mật nền tảng cho Clinic CMS:
- **Multi-tenancy**: mỗi người dùng chỉ có quyền truy cập dữ liệu của phòng khám họ
- **Row-Level Security (RLS)**: PostgreSQL policy tự động lọc dữ liệu theo `clinic_id` trong context
- **Audit log**: ghi lại mọi thay đổi dữ liệu (CREATE/UPDATE/DELETE) vào bảng append-only `audit_log`, bao gồm old_data, new_data, thông tin người thực hiện, IP, user-agent
- **Request tracking**: propagate `request_id` qua mọi yêu cầu để traceability

Mục tiêu: bảo vệ dữ liệu bệnh nhân giữa các phòng khám, đáp ứng yêu cầu phối hợp (§31 BA) và audit (§15.1 BA).

---

## 2. Phạm vi v1

### 2.1 Những gì được triển khai

**Middleware tenancy** (`app/core/tenancy.py`)
- Middleware FastAPI `TenancyMiddleware` intercept mọi request
- Parse authorization từ nguồn (ưu tiên):
  1. Dev headers (`X-Clinic-Id`, `X-User-Id`) — chỉ accept khi `ENVIRONMENT=development`
  2. JWT Bearer token — signature HS256 verified ngoài dev environment
- Set ContextVars: `app.current_clinic_id`, `app.current_user_id`, `current_request_id` (UUID)
- Generate hoặc echo lại `X-Request-Id` header (UUID v4)
- Bind clinic_id, user_id, request_id vào log context (structlog)
- Reject 401 trên protected paths nếu không có valid auth
- Whitelist paths: `/`, `/health`, `/docs`, `/openapi.json`, `/redoc`

**RLS infrastructure** (`app/core/rls.py` + migration 0003)
- PostgreSQL Row-Level Security policy `tenant_isolation`:  
  `clinic_id::text = current_setting('app.current_clinic_id', true) OR clinic_id IS NULL`  
  (Cho phép NULL cho system-level events trong `audit_log`)
- Migration helper `apply_rls_with_tenant_isolation(op, table)` — áp dụng RLS mới cho bảng business
- Helper `remove_rls()` để rollback
- Policy chỉ có hiệu lực với role non-superuser; `cms` (superuser) bypass RLS ở local dev
- Production phải dùng `cms_app` (NOSUPERUSER NOBYPASSRLS) để RLS có hiệu lực

**Audit log** (`app/core/audit.py` + migration 0002 + `app/modules/audit/models/audit_log.py`)
- Bảng `audit_log` (append-only, không soft-delete, không version)
- PostgreSQL trigger: chặn UPDATE / DELETE trên `audit_log`
- SQLAlchemy event listener `after_flush`: tự động ghi INSERT/UPDATE/DELETE của `__auditable__=True` model
- Sync write v1: audit record thêm vào session, flush cùng business transaction (atomicity)
- Async Arq queue là Phase 2
- Record schema:
  - `id` (UUID, PK)
  - `clinic_id` (UUID, nullable — system events)
  - `user_id` (UUID, nullable — system events)
  - `request_id` (string, correlation)
  - `action` (INSERT, UPDATE, DELETE, READ)
  - `entity_type` (tên model)
  - `entity_id` (UUID)
  - `old_data` (JSONB, null khi INSERT)
  - `new_data` (JSONB, null khi DELETE)
  - `changed_fields` (array[text], field name nào thay đổi khi UPDATE)
  - `ip_address`, `user_agent`
  - `created_at` (timestamp)

**DB security** (`app/core/db_security.py`)
- Startup check: nếu connected role là superuser ở non-dev environment → emit CRITICAL log event `db_role_security_violation`
- Kiểm tra qua `SELECT current_user, usesuper FROM pg_user WHERE usename = current_user`

**Migration v1** (0002, 0003, 0004)
- 0002: create table `audit_log`, function & trigger immutable
- 0003: enable RLS + apply policy trên mọi business table có `clinic_id`
- 0004: create role `cms_app` NOSUPERUSER NOBYPASSRLS, grant privileges

---

## 3. Quyết định thiết kế chính

### 3.1 Audit ghi đồng bộ (sync) trong cùng transaction (v1)

**Quyết định**: SQLAlchemy event listener `after_flush` ghi audit record **đồng bộ** bằng `session.add(record)`.

**Lý do**:
- Audit row được ghi **cùng transaction** với business data → atomicity: nếu transaction rollback, audit rollback
- Không sử dụng `asyncio.create_task()` (không reliable từ sync callback, race condition, silent drop on test teardown)
- `session.add()` tự re-enter flush queue → audit record đi vào next flush, vẫn trong same DB transaction

**Hạn chế**: không đo được p99 latency overhead. AC5 (async p99 < 5%) deferred.

**Phase 2**: Arq async queue — audit queue độc lập, persistent, không block response. Dành cho TASK-025.

---

### 3.2 PII redaction qua `_ALWAYS_REDACT` + `__audit_exclude__`

**Quyết định**: Mô hình kép:
1. **Built-in safety net**: `_ALWAYS_REDACT` frozenset gồm tên field phổ biến (password_hash, mfa_secret, refresh_token, v.v.)
2. **Per-model opt-out**: `__audit_exclude__: ClassVar[frozenset[str]]` trên model (e.g., User)

**Cách dùng**:
```python
class User(BaseEntity):
    __auditable__ = True
    __audit_exclude__: ClassVar[frozenset[str]] = frozenset({
        "password_hash", "mfa_secret", "refresh_token_hash",
    })
```

Excluded field → ghi `"***"` vào `old_data`/`new_data`. Tất cả `_ALWAYS_REDACT` field luôn redacted dù không trong `__audit_exclude__`.

**TASK-005 (User model) PHẢI set `__audit_exclude__`** cho mọi secret field.

---

### 3.3 Production user phải dùng role `cms_app`

**Quyết định**: 
- Dev: accept superuser `cms` (convenience)
- Production / staging: **ENFORCE** role `cms_app` (NOSUPERUSER NOBYPASSRLS)
- Startup check log CRITICAL nếu superuser + non-dev

**Lý do**: PostgreSQL BYPASSRLS privilege — ngay cả khi `FORCE ROW LEVEL SECURITY` enable trên table, superuser vẫn bypass. Để RLS hoạt động, app phải non-superuser.

**Deployment**: `DATABASE_URL` phải `postgresql+asyncpg://cms_app:...`  
Migration 0004 tạo role idempotent + grant privileges.

---

### 3.4 JWT signature verification — gated to non-dev env

**Quyết định**:
- `ENVIRONMENT=development`: unsigned JWT accept (dev convenience), dev headers accept
- Mọi env khác (test, staging, prod): JWT PHẢI HS256 signature verify → 401 on fail
- Dev headers → reject 401 ở non-dev env

**Security model**:
- **Development**: unsigned JWT `{"clinic_id": "...", "sub": "..."}` + dev header override → fast iteration
- **Production**: Bearer token → HS256 verify vs `JWT_SECRET` env var. TASK-003 sẽ chuyển RS256 + JWKS

**Non-superuser validation**: JWT `sub` (user_id) phải UUID format; log warning nếu non-UUID, continue với `user_id=None` (v1).

---

### 3.5 Request ID tracking (TASK-001 deferral #9)

**Quyết định**: Middleware propagate `X-Request-Id` header.

**Cách dùng**:
- Client gửi: `X-Request-Id: <uuid>`  
  → Server lưu + trả lại trong response header
- Nếu client không gửi → Server generate UUID v4, lưu vào ContextVar `current_request_id`
- Mọi event log (structlog) tự carry request_id

**Traceability**: Mọi log, audit record, error response đều mang request_id → trace request end-to-end.

---

## 4. Luồng xử lý tổng thể

```
Client request
    ↓
TenancyMiddleware
    ├─ Check whitelist → skip auth
    ├─ Parse dev header (X-Clinic-Id, X-User-Id) → ONLY if dev env
    ├─ Parse Bearer token → decode (unsigned if dev, verified HS256 if not)
    ├─ Set ContextVar: current_clinic_id, current_user_id, current_request_id
    ├─ Bind to structlog context
    └─ Generate/echo X-Request-Id header
    ↓
Route handler
    ↓
SQLAlchemy session (via get_db())
    ├─ current_clinic_id ContextVar → auto bind RLS policy
    ├─ Model INSERT/UPDATE/DELETE
    └─ SQLAlchemy after_flush listener
        ├─ Check if model.__auditable__ = True
        ├─ Compute old_data/new_data diff
        ├─ Redact sensitive fields (_ALWAYS_REDACT + __audit_exclude__)
        ├─ Create AuditLog record (clinic_id, user_id, action, entity_type, entity_id, old_data, new_data, changed_fields, ip_address, user_agent, created_at)
        └─ session.add(audit_record)  [sync, re-enters flush queue]
    ↓
Transaction commit
    └─ AuditLog row + business data committed atomically
    ↓
Response + X-Request-Id header + audit trail written ✓
```

---

## 5. Multi-tenancy isolation (§3.1)

### 5.1 RLS Policy

PostgreSQL policy trên mọi business table:

```sql
CREATE POLICY tenant_isolation ON <table_name>
  FOR ALL
  USING (clinic_id::text = current_setting('app.current_clinic_id', true) 
         OR clinic_id IS NULL)
```

- User clinic A: ContextVar `current_clinic_id = <clinic-a-uuid>`  
  → RLS policy lọc: chỉ hiển thị row `clinic_id = <clinic-a-uuid>` hoặc `clinic_id IS NULL`
- User clinic B: khác clinic → query cùng table → 0 row từ clinic A ✓
- Superuser `cms` → BYPASS RLS (dev-only safe)
- Non-superuser `cms_app` → RLS enforced ✓

### 5.2 Audit isolation

`audit_log` có `clinic_id` (nullable).  
Khi audit_read (sensitive reads) được gọi, record được tag `clinic_id = current_clinic_id` (non-NULL).  
System events (migrations, schema updates): `clinic_id = NULL`, accessible by BYPASSRLS roles.

---

## 6. Audit log lifecycle

### 6.1 Automatic (after_flush event)

Model định nghĩa `__auditable__ = True`:

```python
class Patient(BaseEntity):
    __auditable__ = True
    name: Mapped[str]
    clinic_id: Mapped[UUID]
    ...
```

CREATE Patient → audit record:
```json
{
  "action": "INSERT",
  "entity_type": "Patient",
  "entity_id": "<patient-uuid>",
  "old_data": null,
  "new_data": {"name": "John", "clinic_id": "...", ...},
  "changed_fields": null,
  "clinic_id": "<from-ContextVar>",
  "user_id": "<from-ContextVar>",
  "request_id": "<from-ContextVar>",
  "created_at": "2026-04-26T10:00:00Z"
}
```

UPDATE Patient → audit record:
```json
{
  "action": "UPDATE",
  "entity_type": "Patient",
  "entity_id": "<same>",
  "old_data": {"name": "John", ...},
  "new_data": {"name": "Jane", ...},
  "changed_fields": ["name"],  [only changed fields]
  "clinic_id": "<from-ContextVar>",
  ...
}
```

DELETE Patient → audit record:
```json
{
  "action": "DELETE",
  "entity_type": "Patient",
  "entity_id": "<same>",
  "old_data": {"name": "Jane", ...},
  "new_data": null,
  "changed_fields": null,
  "clinic_id": "<from-ContextVar>",
  ...
}
```

### 6.2 Manual (write_audit + audit_read)

**write_audit**: ghi audit record ngoài event listener (e.g., PATCH, UPSERT complex logic)

```python
await write_audit(
    db,
    action="CREATE",
    entity_type="Patient",
    entity_id=patient_uuid,
    new_data={"name": "John"},
)
```

**audit_read**: ghi READ action cho sensitive data access

```python
await audit_read(
    db,
    entity_type="Patient",
    entity_id=patient_uuid,
)
```

---

## 7. Immutability trigger

PostgreSQL trigger trên `audit_log` chặn UPDATE / DELETE:

```sql
CREATE TRIGGER audit_log_immutable
  BEFORE UPDATE OR DELETE ON audit_log
  FOR EACH ROW
  EXECUTE FUNCTION raise_audit_immutable();

CREATE FUNCTION raise_audit_immutable() RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'audit_log table is immutable';
END;
$$ LANGUAGE plpgsql;
```

Nếu application hoặc admin cố UPDATE / DELETE audit row → PostgreSQL error, transaction rollback.

---

## 8. Security validation

### 8.1 JWT signature + environment gating

| Scenario | Behavior | Status |
|----------|----------|--------|
| Dev env, unsigned JWT | Accept, extract clinic_id/user_id | ✓ |
| Dev env, wrong JWT signature | Accept (unsigned), extract | ✓ |
| Non-dev env, no Authorization header | 401 (whitelist exempt) | ✓ |
| Non-dev env, unsigned JWT | 401 | ✓ |
| Non-dev env, wrong JWT signature | 401 | ✓ |
| Non-dev env, valid JWT (HS256) | Accept, extract, proceed | ✓ |
| Non-dev env, dev header (X-Clinic-Id) | 401 | ✓ |

### 8.2 Superuser production warning

```python
# app/core/db_security.py
async def check_db_role_security(engine: AsyncEngine) -> None:
    """Warn if connected as superuser outside dev environment."""
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT current_user, usesuper FROM pg_user WHERE usename = current_user")
        )
        row = result.first()
        if row and row.usesuper and settings.ENVIRONMENT != "development":
            log.critical(
                "db_role_security_violation",
                current_user=row[0],
                superuser=True,
                environment=settings.ENVIRONMENT,
            )
```

Output: CRITICAL log event `db_role_security_violation` (structured logs).  
App continues, but alerts / monitors should catch this.

---

## 9. Hạn chế v1

### 9.1 JSONB in-place mutation không detect

**Vấn đề**: Nếu model có JSONB column, in-place mutation không được SQLAlchemy detect nếu column không dùng `MutableDict.as_mutable(JSONB)`.

```python
# NOT detected by audit:
record.meta["key"] = "new value"  # in-place

# Detected:
record.meta = {**record.meta, "key": "new value"}  # replacement
```

**Giải pháp v1**: Downstream model phải dùng `MutableDict` cho JSONB.

```python
from sqlalchemy.types import TypeDecorator
from sqlalchemy.ext.mutable import MutableDict

class Patient(BaseEntity):
    meta: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB))
```

---

### 9.2 Audit p99 latency benchmark deferred

AC5 (async audit p99 < 5%) không test v1.  
v1 ghi sync → no latency regression (write in-transaction).  
Phase 2 Arq queue sẽ benchmark.

---

## 10. Quy tắc kiểm thử

### AC1: Isolation giữa clinic

- Clinic A user query `patient` table → chỉ thấy patient clinic A ✓
- Clinic B user query cùng table → 0 row ✓
- Update patient clinic A khi login clinic B → query fail silently, 0 row update ✓

### AC2: Superuser bypass

- cms role (superuser) query → thấy ALL row, RLS bypass ✓
- cms_app role (non-superuser) query → RLS enforced ✓

### AC3: Audit CREATE/UPDATE/DELETE

- CREATE → old_data null, new_data present, changed_fields null ✓
- UPDATE → old_data vs new_data khác, changed_fields có tên field thay đổi ✓
- DELETE → old_data present, new_data null ✓

### AC4: Immutability

- UPDATE audit_log row → PostgreSQL error ✓
- DELETE audit_log row → PostgreSQL error ✓

---

## 11. Vận hành production

### 11.1 Deployment checklist

1. **Migrate database** (phải before app start):
   ```bash
   alembic upgrade head
   ```
   → Creates cms_app role, audit_log table, RLS policies

2. **Set environment variables**:
   ```
   ENVIRONMENT=production
   DATABASE_URL=postgresql+asyncpg://cms_app:<password>@<host>:5432/cms
   JWT_SECRET=<secure-value-from-vault>
   JWT_ALGORITHM=HS256
   ```

3. **Start app** (lifespan startup check):
   - `db_security.py` query current role
   - If superuser + non-dev → CRITICAL log
   - Proceed anyway (alert/monitor should catch)

4. **Monitor**:
   - `db_role_security_violation` event → page oncall
   - Audit lag (not v1, Phase 2)
   - RLS policy violations (PostgreSQL error logs)

### 11.2 JWT_SECRET rotation (production)

1. Deploy new SECRET → `JWT_SECRET` env var (app restarts)
2. Old tokens still validate (no expiry check v1, TASK-003 adds exp)
3. New tokens use new secret
4. No downtime

---

## 12. Ghi chú kiểm thử & phát triển

### 12.1 Dev headers (X-Clinic-Id / X-User-Id)

Chỉ accept khi `ENVIRONMENT=development`.  
Production: 401 nếu có header này.  
Useful for local testing without JWT.

### 12.2 DB schema migration order

0002: audit_log + trigger  
0003: RLS enable + policy on all tables  
0004: cms_app role creation  

Phải theo thứ tự. Rollback auto via Alembic.

### 12.3 Test role bootstrap

Tests tạo `cms_app` role tại test time (fixture).  
Production: migration 0004 tạo + GRANT idempotent.

### 12.4 ContextVar cleanup

FastAPI lifespan / request context cleanup automatic.  
No manual ContextVar teardown needed.

---

## 13. Kết nối với TASK khác

- **TASK-001**: deferral #9 request_id tracking → đã implement
- **TASK-003** (Auth v2): RS256 + JWKS, JWT exp/nbf, User model + password
- **TASK-005** (User model): PHẢI set `__audit_exclude__` cho sensitive field
- **TASK-004** (RBAC): thêm permission check trong middleware / route decorator
- **TASK-025** (Async audit): Arq queue, independent persistence, p99 benchmark

---

## 14. Danh sách file & migration

| File | Dòng | Mô tả |
|------|------|-------|
| `app/core/tenancy.py` | 200+ | Middleware + JWT decode + ContextVar |
| `app/core/audit.py` | 370+ | Event listener + write_audit + audit_read |
| `app/core/rls.py` | 85 | RLS helper, migration-time |
| `app/core/db_security.py` | 40 | Startup superuser check |
| `app/modules/audit/models/audit_log.py` | 90 | AuditLog model |
| `alembic/versions/0002_*.py` | 100+ | audit_log table + trigger |
| `alembic/versions/0003_*.py` | 50+ | RLS enable + policy |
| `alembic/versions/0004_*.py` | 60+ | cms_app role creation |

---

**Phê duyệt**: Code Review APPROVED (2026-04-26 iter 2)  
**Test status**: 148/148 pass (100%)  
**Coverage**: 95% tenancy, 100% rls, 100% db_security, 100% audit_log, 69% audit (event listener coverage deferred TASK-005)  
**Branch**: `feature/task-002-tenancy` (commit f90e915)  
**Merge ready**: Yes, onto TASK-001 after TASK-001 merges.
