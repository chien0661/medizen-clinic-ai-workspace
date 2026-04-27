# API Specification: Foundation Endpoints

**Task:** TASK-001  
**Version:** 1.0  
**Date:** 2026-04-26  
**Status:** Approved

---

## Overview

TASK-001 delivers the foundational HTTP endpoints only: `/health` (diagnostic) and `/` (metadata). All other endpoints (CRUD, auth, etc.) will be delivered in TASK-002 onwards.

For interactive API documentation, see: **http://localhost:8000/docs** (Swagger UI)

---

## Endpoint Summary

| Method | Path | Purpose | Auth | Status |
|--------|------|---------|------|--------|
| GET | `/health` | Service health check | None | ✓ TASK-001 |
| GET | `/` | API metadata | None | ✓ TASK-001 |

---

## Detailed Endpoints

### 1. GET /health

**Purpose:** Diagnostic health check endpoint. Returns service status, version, and environment.

**Request:**

```http
GET /health HTTP/1.1
Host: localhost:8000
Accept: application/json
```

**Query Parameters:** None

**Request Body:** None

**Response (200 OK):**

```json
{
  "status": "ok",
  "service": "clinic-cms-api",
  "version": "0.1.0",
  "environment": "development"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Service status: `"ok"` if healthy |
| `service` | string | Service name identifier |
| `version` | string | API version (from pyproject.toml) |
| `environment` | string | Environment: `"development"`, `"staging"`, `"production"` |

**HTTP Status Codes:**

| Code | Condition | Example |
|------|-----------|---------|
| `200` | Service is healthy | See response above |

**Example cURL:**

```bash
curl http://localhost:8000/health
```

**Example Python:**

```python
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("http://localhost:8000/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

---

### 2. GET /

**Purpose:** Root endpoint. Returns API metadata including documentation links.

**Request:**

```http
GET / HTTP/1.1
Host: localhost:8000
Accept: application/json
```

**Query Parameters:** None

**Request Body:** None

**Response (200 OK):**

```json
{
  "name": "Clinic CMS",
  "docs": "/docs",
  "health": "/health"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | API name |
| `docs` | string | URL path to Swagger UI documentation |
| `health` | string | URL path to health check endpoint |

**HTTP Status Codes:**

| Code | Condition |
|------|-----------|
| `200` | Success |

**Example cURL:**

```bash
curl http://localhost:8000/
```

---

## Error Handling

All endpoints follow the standard error response shape defined in §2.4 of the functional design.

**Standard Error Response (any HTTP error code):**

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "optional_additional_context"
    }
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-04-26T12:00:00Z"
  }
}
```

**Note:** TASK-001 endpoints (`/health`, `/`) do not throw errors under normal operation. If an unhandled exception occurs:

- **HTTP 500 Internal Server Error** is returned with the above error shape
- The exception is logged via structlog with full traceback
- The `request_id` in the response can be used to correlate logs

---

## Future Endpoints

The following endpoints will be documented in their respective tasks:

| Task | Scope |
|------|-------|
| TASK-002 | RLS setup, request_id middleware, GET /clinics, GET /clinics/{id} |
| TASK-003 | POST /auth/login, POST /auth/refresh |
| TASK-004 | Users, roles, permissions (auth endpoints) |
| TASK-005+ | Domain-specific CRUD endpoints (appointments, patients, etc.) |

---

## Testing

All endpoints are tested in `tests/integration/test_health.py`:

```bash
docker exec clinic_cms_api pytest tests/integration/test_health.py -v
```

Test scenarios:
- ✓ `/health` returns 200 with correct JSON shape
- ✓ `/` returns 200 with correct JSON shape
- ✓ Response content-type is `application/json`

---

## Base URL

- **Development:** `http://localhost:8000`
- **Staging:** (TBD)
- **Production:** (TBD)

---

**Document Version:** 1.0 | **Date:** 2026-04-26 | **Status:** Approved
