# API Specification: Service Type (configurable service classification)

**Task:** TASK-125 — Phân loại danh mục dịch vụ (service_type)
**Date:** 2026-07-30
**Version:** 1.0
**Status:** Complete (implementation) — pending Code Review / Test

---

## Overview

This specification documents the new `/service-types` REST endpoints and the extensions made to the existing Service Catalog (`/services`) endpoints for TASK-125. `service_type` is a **per-clinic configuration table** (admin CRUD) — not a hard-coded enum — that classifies catalog services (e.g. Khám / Thủ thuật / Xét nghiệm / admin-added). It is the foundation for TASK-128 (Commission — % discount keyed on `service_type_id`) and TASK-126 (reporting grouped by type).

**Base URL:** `/api/v1`

**Authentication:** All endpoints require bearer token authentication:
```
Authorization: Bearer {jwt_token}
```

**Clinic Context:** All endpoints require the token to have an active `clinic_id` (tenant-scoped — `service_type` rows are never shared across clinics, unlike `dosage_form`).

**Permissions:** No new permission was introduced. `/service-types` reuses the existing `service.read` (list/get) and `service.manage` (create/update/delete) permissions from TASK-010 — the same boundary that already gates `/services`.

---

## Endpoints Summary

| # | Method | Path | Permission | Purpose |
|---|--------|------|-----------|---------|
| 1 | GET | `/service-types` | `service.read` | List service types for the current clinic |
| 2 | POST | `/service-types` | `service.manage` | Create a custom service type |
| 3 | GET | `/service-types/{id}` | `service.read` | Get a single service type |
| 4 | PATCH | `/service-types/{id}` | `service.manage` | Update a service type (403 if system row) |
| 5 | DELETE | `/service-types/{id}` | `service.manage` | Soft-delete a service type (403 if system row) |
| 6 | GET | `/services?service_type_id=` | `service.read` | *(extended)* Filter the catalog by service type |
| 7 | POST / PATCH | `/services` | `service.manage` | *(extended)* Set `service_type_id` on create/update |
| 8 | GET | `/services/export` | `service.read` | *(extended)* Excel export adds a "Loại dịch vụ" column |

---

## Endpoint Details

### 1. GET /service-types

**Description:**
List all service types belonging to the current clinic (there is no global/shared row — every row has a concrete `clinic_id`, unlike `dosage_form`). Ordered by `sort_order` then `name`.

**Request:**
```
GET /api/v1/service-types?is_active=true
Authorization: Bearer <token>
```

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `is_active` | boolean | No | Filter by active status |

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "code": "consultation",
      "name": "Khám",
      "description": null,
      "is_active": true,
      "sort_order": 1,
      "is_system": true,
      "is_deleted": false,
      "created_at": "2026-07-30T00:00:00Z",
      "updated_at": "2026-07-30T00:00:00Z",
      "created_by": null,
      "updated_by": null,
      "version": 1
    },
    { "code": "procedure", "name": "Thủ thuật", "sort_order": 2, "is_system": true, "...": "..." },
    { "code": "test", "name": "Xét nghiệm", "sort_order": 3, "is_system": true, "...": "..." }
  ],
  "total": 3
}
```

---

### 2. POST /service-types

**Description:**
Create a custom (non-system) service type. `is_system` is always `false` for created rows — the flag cannot be set by the client.

**Request:**
```json
POST /api/v1/service-types
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "physio",
  "name": "Vật lý trị liệu",
  "description": "Điều trị phục hồi chức năng",
  "sort_order": 4,
  "is_active": true
}
```

**Body fields:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `code` | string | Yes | `^[a-z0-9_-]{1,50}$`, unique per clinic (active rows only) |
| `name` | string | Yes | 1-200 chars |
| `description` | string | No | ≤500 chars |
| `sort_order` | integer | No | ≥0, default `0` |
| `is_active` | boolean | No | default `true` |

**Response (201 Created):** Full `ServiceTypeResponse` object (same shape as list items).

**Errors:**
- `409 Conflict` — `code` already exists (case-insensitive) for this clinic.
- `422 Unprocessable Entity` — schema validation failure (e.g. uppercase code).

---

### 3. GET /service-types/{id}

**Response (200 OK):** Single `ServiceTypeResponse` object.

**Errors:** `404 Not Found` — id doesn't exist or belongs to another clinic.

---

### 4. PATCH /service-types/{id}

**Description:**
Update `name` / `description` / `sort_order` / `is_active`. `code` and `is_system` are immutable — not accepted in the body.

**Request:**
```json
PATCH /api/v1/service-types/{id}
{
  "name": "Vật lý trị liệu (PT)",
  "is_active": false
}
```

**Response (200 OK):** Updated `ServiceTypeResponse`.

**Errors:**
- `403 Forbidden` — target row has `is_system=true` ("Không thể sửa/xóa loại dịch vụ hệ thống"). This protects the 3 seeded default ids so TASK-128 Commission can key discount rates on them without risk of drift.
- `404 Not Found` — id doesn't exist / wrong clinic.

---

### 5. DELETE /service-types/{id}

**Description:** Soft-delete (sets `is_deleted=true`). Services still referencing the deleted type keep their `service_type_id` unchanged (no cascade).

**Response (200 OK):** The deleted `ServiceTypeResponse` (`is_deleted: true`).

**Errors:** Same `403`/`404` as PATCH.

---

### 6. GET /services?service_type_id={id} (extended)

**Description:**
Existing `/services` list endpoint gains a `service_type_id` query filter. When set, only services with an **exact match** on `service_type_id` are returned — services with `service_type_id IS NULL` ("chưa phân loại") are excluded from a type-scoped filter (intentional — not a bug).

Response items now include two additional fields:

```json
{
  "items": [
    {
      "...": "existing ServiceResponse fields...",
      "service_type_id": "550e8400-e29b-41d4-a716-446655440000",
      "service_type_name": "Khám"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

`service_type_name` is denormalized server-side for display convenience (batch-resolved, not an N+1 query). Both fields are `null` for unclassified services.

**Cache note:** `service_type_id` is now part of the Redis list-cache `params_key` (`services:list:{clinic}:v{ver}:{category}|{is_active}|{q}|{tags}|{service_type_id}|{skip}|{limit}`) — without this, a filtered query could be served a stale/wrong cached variant.

---

### 7. POST / PATCH /services (extended)

**Description:**
`ServiceCreate` / `ServiceUpdate` bodies accept an optional `service_type_id` (UUID). The referenced type must belong to the same clinic as the service.

**Request (create):**
```json
POST /api/v1/services
{
  "code": "KHTQ",
  "name": "Khám tổng quát",
  "default_price": "150000.00",
  "service_type_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errors:**
- `404 Not Found` — `service_type_id` doesn't exist or belongs to another clinic (same tenant-isolation treatment as an unknown `visit_id`).

**Known limitation:** matching the pre-existing behavior of the `category` field, PATCH only *sets* `service_type_id` when a non-null value is supplied — there is currently no way to clear a previously-set `service_type_id` back to `NULL` through this endpoint.

---

### 8. GET /services/export (extended)

**Description:** Excel export gains a "Loại dịch vụ" column (service type name, resolved via a single batch query — not per-row).

Column order: Mã DV, Tên dịch vụ, Danh mục, **Loại dịch vụ**, Đơn giá, Trạng thái.

---

## Data Model Reference

### ServiceTypeResponse

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | |
| `clinic_id` | UUID | Always set — no global/shared rows |
| `code` | string | Immutable after creation |
| `name` | string | |
| `description` | string \| null | |
| `is_active` | boolean | |
| `sort_order` | integer | |
| `is_system` | boolean | `true` for the 3 seeded defaults — read-only |
| `is_deleted` | boolean | |
| `created_at` / `updated_at` | datetime | |
| `created_by` / `updated_by` | UUID \| null | |
| `version` | integer | Optimistic lock |

### Default seeded types (per clinic)

| `code` | `name` | `sort_order` |
|--------|--------|--------------|
| `consultation` | Khám | 1 |
| `procedure` | Thủ thuật | 2 |
| `test` | Xét nghiệm | 3 |

Seeded by migration `0071` (existing clinics) and `clinic_service.create_clinic` → `service_type_service.seed_defaults_for_clinic` (new clinics) — both idempotent and using the same code/name/order tuple.

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-30 | Initial version — `/service-types` CRUD + `/services` extensions |
