# API Specification: Unit (configurable dispensing/stock unit catalog)

**Task:** TASK-132 — Danh mục đơn vị (unit) quản lý được + dropdown creatable
**Date:** 2026-07-31
**Version:** 1.0
**Status:** Complete (implementation) — pending Code Review / Test

---

## Overview

This specification documents the new `/units` REST endpoints for TASK-132. `unit` is a **per-clinic configuration table** (admin CRUD) — not a hard-coded enum — that supplies suggestion/quick-create options for the medicine catalog's unit fields (`base_unit`, `sell_unit`, `purchase_unit`, `usage_unit`). It mirrors TASK-125's `service_type` pattern exactly.

**Important:** `unit` is a *suggestion catalog*, not a foreign-key constraint. `medicine.base_unit` / `sell_unit` / `purchase_unit` / `usage_unit` remain free-text `String` columns (unchanged by this task) — there is no DB-level FK from `medicine` to `unit`. This keeps all historical medicine/prescription/invoice data completely unaffected.

**Base URL:** `/api/v1`

**Authentication:** All endpoints require bearer token authentication:
```
Authorization: Bearer {jwt_token}
```

**Clinic Context:** All endpoints require the token to have an active `clinic_id` (tenant-scoped — `unit` rows are never shared across clinics, unlike `dosage_form`).

**Permissions:** No new permission was introduced. `/units` reuses the existing `inventory.read` (list/get) and `inventory.manage_catalog` (create/update/delete/quick-create) permissions — seeded in migration `0017a`, granted to `admin` + `pharmacist` — the same boundary that already gates `/medicines` and the other inventory catalog endpoints.

---

## Endpoints Summary

| # | Method | Path | Permission | Purpose |
|---|--------|------|-----------|---------|
| 1 | GET | `/units` | `inventory.read` | List units for the current clinic |
| 2 | POST | `/units` | `inventory.manage_catalog` | Create a custom unit (admin CRUD page) |
| 3 | POST | `/units/quick-create` | `inventory.manage_catalog` | Get-or-create a unit by display name (creatable combobox flow) |
| 4 | GET | `/units/{id}` | `inventory.read` | Get a single unit |
| 5 | PATCH | `/units/{id}` | `inventory.manage_catalog` | Update a unit (403 if system row) |
| 6 | DELETE | `/units/{id}` | `inventory.manage_catalog` | Soft-delete a unit (403 if system row) |

---

## Endpoint Details

### 1. GET /units

**Description:**
List all units belonging to the current clinic (there is no global/shared row — every row has a concrete `clinic_id`, unlike `dosage_form`). Ordered by `sort_order` then `name`.

**Request:**
```
GET /api/v1/units?is_active=true
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
      "code": "vien",
      "name": "viên",
      "description": null,
      "is_active": true,
      "sort_order": 1,
      "is_system": true,
      "is_deleted": false,
      "created_at": "2026-07-31T00:00:00Z",
      "updated_at": "2026-07-31T00:00:00Z",
      "created_by": null,
      "updated_by": null,
      "version": 1
    }
  ],
  "total": 11
}
```

---

### 2. POST /units

**Description:**
Create a custom (non-system) unit — used by the `/admin/units` CRUD page. `is_system` is always `false` for created rows.

**Request:**
```json
POST /api/v1/units
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "hop",
  "name": "Hộp",
  "description": null,
  "sort_order": 12,
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

**Response (201 Created):** Full `UnitResponse` object (same shape as list items).

**Errors:**
- `409 Conflict` — `code` already exists (case-insensitive) for this clinic.
- `422 Unprocessable Entity` — schema validation failure (e.g. uppercase code).

---

### 3. POST /units/quick-create

**Description:**
Get-or-create a unit by **display name only** — the code is derived server-side (diacritics stripped, lowercased, spaces → `-`, de-duplicated with a numeric suffix on collision). This is the endpoint the medicine-form creatable combobox calls when the user types a value not already in the catalog and confirms "Tạo '<x>'".

**Idempotent:** calling this twice with the same name (any case, leading/trailing whitespace) returns the **same row** — no duplicate is created, no `409` is raised. This mirrors `tag_service.attach_tag`'s get-or-create pattern.

**Request:**
```json
POST /api/v1/units/quick-create
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Ống hút"
}
```

**Body fields:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | 1-200 chars |

**Response (200 OK):** Full `UnitResponse` — either the pre-existing matching row, or the newly created one (`is_system: false`).

```json
{
  "id": "6f9619ff-8b86-d011-b42d-00c04fc964ff",
  "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "code": "ong-hut",
  "name": "Ống hút",
  "description": null,
  "is_active": true,
  "sort_order": 0,
  "is_system": false,
  "is_deleted": false,
  "created_at": "2026-07-31T00:00:00Z",
  "updated_at": "2026-07-31T00:00:00Z",
  "created_by": "...",
  "updated_by": "...",
  "version": 1
}
```

**Errors:** `422 Unprocessable Entity` — empty name.

---

### 4. GET /units/{id}

**Response (200 OK):** Single `UnitResponse` object.

**Errors:** `404 Not Found` — id doesn't exist or belongs to another clinic.

---

### 5. PATCH /units/{id}

**Description:**
Update `name` / `description` / `sort_order` / `is_active`. `code` and `is_system` are immutable — not accepted in the body.

**Request:**
```json
PATCH /api/v1/units/{id}
{
  "name": "Hộp giấy",
  "is_active": false
}
```

**Response (200 OK):** Updated `UnitResponse`.

**Errors:**
- `403 Forbidden` — target row has `is_system=true` ("Không thể sửa/xóa đơn vị hệ thống").
- `404 Not Found` — id doesn't exist / wrong clinic.

---

### 6. DELETE /units/{id}

**Description:** Soft-delete (sets `is_deleted=true`). Medicine rows with a `base_unit`/`sell_unit`/`purchase_unit`/`usage_unit` string matching the deleted unit's name/code are **not** affected — there is no FK, so nothing cascades or breaks.

**Response (200 OK):** The deleted `UnitResponse` (`is_deleted: true`).

**Errors:** Same `403`/`404` as PATCH.

---

## Data Model Reference

### UnitResponse

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | |
| `clinic_id` | UUID | Always set — no global/shared rows |
| `code` | string | Immutable after creation |
| `name` | string | |
| `description` | string \| null | |
| `is_active` | boolean | |
| `sort_order` | integer | |
| `is_system` | boolean | `true` for the 11 seeded defaults — read-only |
| `is_deleted` | boolean | |
| `created_at` / `updated_at` | datetime | |
| `created_by` / `updated_by` | UUID \| null | |
| `version` | integer | Optimistic lock |

### Default seeded units (per clinic)

| `code` | `name` | `sort_order` |
|--------|--------|--------------|
| `vien` | viên | 1 |
| `vi` | vỉ | 2 |
| `goi` | gói | 3 |
| `ong` | ống | 4 |
| `chai` | chai | 5 |
| `lo` | lọ | 6 |
| `tuyp` | tuýp | 7 |
| `ml` | ml | 8 |
| `gam` | gam | 9 |
| `mieng` | miếng | 10 |
| `cai` | cái | 11 |

Seeded by migration `0075` (existing clinics) and `clinic_service.create_clinic` → `unit_catalog_service.seed_defaults_for_clinic` (new clinics) — both idempotent and using the same code/name/order tuple.

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-31 | Initial version — `/units` CRUD + `/units/quick-create` |
