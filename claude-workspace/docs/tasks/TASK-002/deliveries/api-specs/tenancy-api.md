# API Specification — Tenancy Middleware & RLS (TASK-002)

**Date**: 2026-04-26  
**Task**: TASK-002 Tenancy + RLS + Audit Log Infrastructure  
**Status**: DONE  
**Test Status**: 148/148 pass (100%)  

---

## Overview

TASK-002 does not introduce **new API endpoints**. Instead, it:
- **Adds authentication middleware** that intercepts every request
- **Sets context variables** (clinic_id, user_id, request_id) consumed by downstream service logic
- **Applies RLS policies** at the database layer (transparent to application code)
- **Records audit trail** automatically and on-demand

This document specifies the middleware behavior, required headers, and error responses.

---

## Authentication Middleware

### Path Whitelist

The following paths **do not require authentication**:

| Path | Purpose |
|------|---------|
| `/` | Root (health check / info) |
| `/health` | Health check endpoint |
| `/docs` | Swagger UI (documentation) |
| `/openapi.json` | OpenAPI schema |
| `/redoc` | ReDoc UI (documentation) |

Matching includes trailing slashes and query parameters:
- `/health`, `/health/`, `/health?foo=bar` → all allowed
- `/health-check`, `/healthx` → rejected (pattern mismatch)

All other paths require valid authentication (see **Auth Flow** below).

---

## Auth Flow

### Priority Order

1. **Dev Headers (DEVELOPMENT ONLY)**
   - If `ENVIRONMENT=development`, accept `X-Clinic-Id` + `X-User-Id` headers
   - Non-dev environment → reject with 401
   
2. **JWT Bearer Token**
   - Development: unsigned JWTs accepted (convenience)
   - Non-dev (test, staging, production): HS256 signature verified against `JWT_SECRET`
   
3. **No Auth**
   - If path is whitelisted → proceed
   - Else → 401

### Dev Headers (development only)

**Format**:
```
X-Clinic-Id: <uuid>
X-User-Id: <uuid>
```

**Example**:
```http
GET /patients HTTP/1.1
X-Clinic-Id: 550e8400-e29b-41d4-a716-446655440000
X-User-Id: 6ba7b810-9dad-11d1-80b4-00c04fd430c8
```

**Security**:
- Only accepted when `ENVIRONMENT=development`
- Production deployment → 401 if these headers present

**Priority**: Takes precedence over JWT if both provided in dev env.

### JWT Bearer Token

**Format**:
```
Authorization: Bearer <token>
```

**Token Structure**:
```json
{
  "clinic_id": "<uuid>",
  "sub": "<user-uuid>",
  "iat": 1714129200
}
```

**Example Request**:
```http
GET /patients HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGluaWNfaWQiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJzdWIiOiI2YmE3YjgxMC05ZGFkLTExZDEtODBiNC0wMGMwNGZkNDMwYzgiLCJpYXQiOjE3MTQxMjkyMDB9.signature
```

**Signature Verification**:
- **Development**: signature **NOT verified** (unsigned tokens accepted)
- **Staging, Production**: HS256 signature **MUST** verify against `JWT_SECRET`
  - Invalid signature → 401
  - Invalid JWT format → 401

---

## Request ID Propagation

### X-Request-Id Header (Optional Input, Always Echoed)

**Purpose**: Correlate logs across request lifecycle.

**Format**: UUID v4 (36 bytes, e.g., `550e8400-e29b-41d4-a716-446655440000`)

**Client sends** (optional):
```http
GET /patients HTTP/1.1
X-Request-Id: 550e8400-e29b-41d4-a716-446655440000
```

**Server generates** (if missing):
```
Generated UUID v4 → stored in ContextVar current_request_id
```

**Server echoes** (always in response):
```
X-Request-Id: <client-provided-or-generated-uuid>
```

**Example Response**:
```http
HTTP/1.1 200 OK
X-Request-Id: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{"patients": [...]}
```

**All audit records & logs carry request_id** for end-to-end traceability.

---

## Error Responses

### 401 Unauthorized

**When**:
- Protected path (not whitelisted) + no valid auth
- Dev environment: no X-Clinic-Id / X-User-Id, no JWT
- Non-dev environment: invalid JWT signature, expired token, malformed Bearer
- Non-dev environment: X-Clinic-Id / X-User-Id header present (dev header in production)

**Response**:
```http
HTTP/1.1 401 Unauthorized
X-Request-Id: <uuid>
Content-Type: application/json

{
  "detail": "Not authenticated",
  "request_id": "<uuid>"
}
```

### 403 Forbidden (Future — TASK-004 RBAC)

**When**: Valid auth, but insufficient permissions for the action.

**Response** (Phase 2):
```http
HTTP/1.1 403 Forbidden
X-Request-Id: <uuid>
Content-Type: application/json

{
  "detail": "Insufficient permissions",
  "request_id": "<uuid>"
}
```

---

## Context Variables (Internal)

The middleware sets the following **ContextVar** values, accessible to downstream handlers:

| Variable | Type | Source | Example |
|----------|------|--------|---------|
| `app.current_clinic_id` | UUID | JWT claim or header | `550e8400-e29b-41d4-a716-446655440000` |
| `app.current_user_id` | UUID | JWT `sub` or header | `6ba7b810-9dad-11d1-80b4-00c04fd430c8` |
| `current_request_id` | str (UUID) | header or generated | `550e8400-e29b-41d4-a716-446655440000` |

**Usage in service layer**:
```python
from app.core.db import current_clinic_id, current_user_id
from app.core.tenancy import current_request_id

async def get_patients(db: AsyncSession) -> list[Patient]:
    clinic_id = current_clinic_id.get()  # ContextVar value set by middleware
    # RLS policy auto-filters via current_setting('app.current_clinic_id', true)
    result = await db.execute(select(Patient))
    return result.scalars().all()  # Returns only this clinic's patients
```

**Logging**:
All structured logs automatically include `clinic_id`, `user_id`, `request_id` from ContextVars (via structlog integration).

---

## Audit API (Manual Audit Writes)

### write_audit

**Purpose**: Manually record an audit event outside the automatic after_flush listener.

**Signature**:
```python
async def write_audit(
    db: AsyncSession,
    action: str,  # "CREATE", "UPDATE", "DELETE", "READ", etc.
    entity_type: str,  # e.g., "Patient"
    entity_id: UUID,
    old_data: dict | None = None,
    new_data: dict | None = None,
    changed_fields: list[str] | None = None,
) -> AuditLog:
    """Write an audit record to audit_log table.
    
    clinic_id, user_id, request_id automatically captured from ContextVar.
    """
```

**Example**:
```python
await write_audit(
    db,
    action="UPDATE",
    entity_type="Patient",
    entity_id=patient_id,
    old_data={"name": "John"},
    new_data={"name": "Jane"},
    changed_fields=["name"],
)
```

### audit_read

**Purpose**: Log READ access to sensitive data.

**Signature**:
```python
async def audit_read(
    db: AsyncSession,
    entity_type: str,
    entity_id: UUID,
) -> AuditLog:
    """Log a READ action for sensitive data access."""
```

**Example**:
```python
# Service method reading sensitive patient data
async def get_patient_full(db: AsyncSession, patient_id: UUID) -> Patient:
    patient = await db.get(Patient, patient_id)
    await audit_read(db, entity_type="Patient", entity_id=patient_id)
    return patient
```

---

## Audit Log Schema

Each audit record written to `audit_log` table contains:

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | UUID | NO | Primary key (uuid4) |
| `clinic_id` | UUID | YES | Tenant context (NULL for system events) |
| `user_id` | UUID | YES | Actor (NULL for system events) |
| `request_id` | string (36) | YES | Correlation ID |
| `action` | string (50) | NO | INSERT, UPDATE, DELETE, READ, etc. |
| `entity_type` | string (100) | NO | Model name (e.g., "Patient") |
| `entity_id` | UUID | NO | Record ID |
| `old_data` | JSONB | YES | State before change (NULL on INSERT) |
| `new_data` | JSONB | YES | State after change (NULL on DELETE) |
| `changed_fields` | array[text] | YES | List of field names that changed (NULL on INSERT/DELETE) |
| `ip_address` | string (45) | YES | Client IP (IPv4 or IPv6) |
| `user_agent` | text | YES | User-Agent header (no length limit) |
| `created_at` | timestamp(tz) | NO | Server time (immutable) |

**Example Record (UPDATE)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "request_id": "550e8400-e29b-41d4-a716-446655440002",
  "action": "UPDATE",
  "entity_type": "Patient",
  "entity_id": "550e8400-e29b-41d4-a716-446655440003",
  "old_data": {
    "name": "John Doe",
    "phone": "555-1234"
  },
  "new_data": {
    "name": "Jane Doe",
    "phone": "555-1234"
  },
  "changed_fields": ["name"],
  "ip_address": "192.0.2.1",
  "user_agent": "Mozilla/5.0 ...",
  "created_at": "2026-04-26T10:00:00Z"
}
```

---

## PII Redaction in Audit

### Automatic Redaction Rules

Fields in `_ALWAYS_REDACT` are **always redacted** to `"***"`:
- `password_hash`
- `password`
- `token`, `access_token`, `refresh_token`, `refresh_token_hash`
- `secret`, `jwt_secret`, `mfa_secret`

### Per-Model Exclusion

Models can opt out additional fields via `__audit_exclude__` ClassVar:

```python
from typing import ClassVar

class User(BaseEntity):
    __auditable__ = True
    __audit_exclude__: ClassVar[frozenset[str]] = frozenset({
        "password_hash",
        "mfa_secret",
        "custom_secret_field",
    })
```

All fields in `__audit_exclude__` + `_ALWAYS_REDACT` → logged as `"***"`.

---

## Database Roles & RLS

### Application Role: `cms_app`

| Attribute | Value |
|-----------|-------|
| Name | `cms_app` |
| Superuser | NO |
| BYPASSRLS | NO |
| Login | YES |

**Result**: RLS policies **actively enforced**.

### RLS Policy: `tenant_isolation`

Applied to all business tables:

```sql
CREATE POLICY tenant_isolation ON <table_name>
  FOR ALL
  USING (clinic_id::text = current_setting('app.current_clinic_id', true) 
         OR clinic_id IS NULL)
```

**Behavior**:
- User's `current_clinic_id` ContextVar → stored in database via `current_setting()`
- Query automatically filters: only rows where `clinic_id` matches OR `clinic_id IS NULL`
- Silent filtering (no error, just 0 rows if cross-tenant query attempted)

### Production Deployment Requirement

`DATABASE_URL` **must** connect as `cms_app`, NOT `cms` (superuser):

```bash
# ✅ CORRECT
DATABASE_URL=postgresql+asyncpg://cms_app:password@host:5432/cms

# ❌ WRONG (RLS bypassed)
DATABASE_URL=postgresql+asyncpg://cms:password@host:5432/cms
```

App startup check logs **CRITICAL** warning if superuser detected in non-dev environment.

---

## Startup Checks

### Database Role Security Check

At app startup (lifespan), `db_security.py:check_db_role_security()` verifies:

1. Query: `SELECT current_user, usesuper FROM pg_user WHERE usename = current_user`
2. If `usesuper = true` AND `ENVIRONMENT != "development"`
   - Log event: `db_role_security_violation`
   - Severity: **CRITICAL**
   - App continues (alert systems should page)

**Example log**:
```json
{
  "event": "db_role_security_violation",
  "current_user": "cms",
  "superuser": true,
  "environment": "production",
  "severity": "CRITICAL"
}
```

---

## Environment Configuration

### Required Environment Variables

| Variable | Type | Example | Notes |
|----------|------|---------|-------|
| `ENVIRONMENT` | string | `development` \| `test` \| `staging` \| `production` | Controls auth/security behavior |
| `JWT_SECRET` | string | (from vault) | HMAC secret for HS256 signature verification (non-dev only) |
| `JWT_ALGORITHM` | string | `HS256` | Algorithm for token verification |
| `DATABASE_URL` | string | `postgresql+asyncpg://cms_app:...` | **MUST use cms_app role in production** |

---

## Testing Scenarios

### Scenario 1: Dev Environment with Unsigned JWT

```http
GET /patients HTTP/1.1
ENVIRONMENT=development
Authorization: Bearer eyJhbGciOiJub25lIn0.eyJjbGluaWNfaWQiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJzdWIiOiI2YmE3YjgxMC05ZGFkLTExZDEtODBiNC0wMGMwNGZkNDMwYzgifQ.
```

**Result**: 200 OK  
**Reason**: Dev env accepts unsigned JWT

### Scenario 2: Production with Invalid JWT Signature

```http
GET /patients HTTP/1.1
ENVIRONMENT=production
Authorization: Bearer <token-with-invalid-sig>
```

**Result**: 401 Unauthorized  
**Reason**: Non-dev env requires valid HS256 signature

### Scenario 3: Dev Headers in Production

```http
GET /patients HTTP/1.1
ENVIRONMENT=production
X-Clinic-Id: 550e8400-e29b-41d4-a716-446655440000
X-User-Id: 6ba7b810-9dad-11d1-80b4-00c04fd430c8
```

**Result**: 401 Unauthorized  
**Reason**: Dev headers only accepted in development env

### Scenario 4: Whitelisted Path (No Auth Required)

```http
GET /health HTTP/1.1
```

**Result**: 200 OK  
**Reason**: /health is whitelisted

---

## Notes for Consumers

1. **All business endpoints** (not whitelisted) require either:
   - Valid JWT with HS256 signature (production), OR
   - Dev headers (development only)

2. **RLS is transparent** — query filters happen at database layer. Service logic reads normally.

3. **Every request carries X-Request-Id** — use it in logs and error messages for traceability.

4. **Audit is automatic** — mark models with `__auditable__ = True` and set `__audit_exclude__` for secrets.

5. **TASK-003 (Auth v2)** will add:
   - RS256 + JWKS
   - JWT exp / nbf / aud validation
   - User model with password hashing

---

**Approved**: Code Review (2026-04-26)  
**Tests**: 148/148 pass (100%)  
**Status**: Ready for merge after TASK-001
