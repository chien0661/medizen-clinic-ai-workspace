# API Specification: Permission Presets

**Task:** TASK-082 — Cấu hình phân quyền đơn giản hóa (phòng khám nhỏ)  
**Date:** 2026-07-03  
**Version:** 1.0  
**Status:** Complete

---

## Overview

This specification documents the 6 new REST API endpoints introduced in TASK-082 to support **Permission Preset** functionality. Permission presets allow clinic admins to grant a user all operational permissions in one click, without manually selecting 30+ individual permissions.

**Base URL:** `/api/v1`

**Authentication:** All endpoints require bearer token authentication:
```
Authorization: Bearer {jwt_token}
```

**Clinic Context:** All mutation endpoints (POST, PATCH, DELETE) require the token to have an active `clinic_id`.

---

## Endpoints Summary

| # | Method | Path | Permission | Purpose |
|---|--------|------|-----------|---------|
| 1 | GET | `/permission-presets` | Authenticated | List system + clinic-owned presets |
| 2 | POST | `/permission-presets` | `role.manage` | Create a custom preset |
| 3 | PATCH | `/permission-presets/{preset_id}` | `role.manage` | Update a custom preset |
| 4 | DELETE | `/permission-presets/{preset_id}` | `role.manage` | Delete a custom preset |
| 5 | POST | `/roles/from-preset` | `role.manage` | Create a role from a preset + assign user |
| 6 | POST | `/roles/{role_id}/apply-preset` | `role.manage` | Apply a preset to an existing role |

---

## Endpoint Details

### 1. GET /permission-presets

**Description:**  
List all permission presets visible to the current clinic: system presets (clinic_id=NULL) and clinic-owned presets (clinic_id=current_clinic_id).

**Authentication:** Bearer token required (any authenticated user)

**Request:**
```
GET /api/v1/permission-presets
Authorization: Bearer <token>
```

**Query Parameters:** None

**Request Body:** None

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "clinic_id": null,
      "code": "small_clinic_doctor",
      "name": "Bác sĩ toàn quyền (phòng khám nhỏ)",
      "description": "Quyền vận hành đầy đủ: tiếp nhận, khám, kê đơn, dược, thanh toán, báo cáo",
      "permission_codes": ["exam.create", "exam.read", "exam.update", "exam.delete", "prescription.create", ...],
      "is_system": true
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "code": "custom_specialist",
      "name": "Bác sĩ chuyên khoa tùy chỉnh",
      "description": "Khám + kê đơn, không thanh toán",
      "permission_codes": ["exam.create", "exam.read", "exam.update", "prescription.create", "prescription.read"],
      "is_system": false
    }
  ],
  "total": 2
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `data` | Array | List of presets |
| `data[].id` | UUID | Preset ID |
| `data[].clinic_id` | UUID \| null | Clinic owner (null = system preset) |
| `data[].code` | String | Preset code (e.g., "small_clinic_doctor") |
| `data[].name` | String | Display name in Vietnamese |
| `data[].description` | String \| null | Optional description |
| `data[].permission_codes` | Array<String> | List of permission codes in preset |
| `data[].is_system` | Boolean | true = system preset (immutable) |
| `total` | Integer | Total count |

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 401 | UNAUTHORIZED | Invalid or expired token |

**Notes:**
- RLS automatically filters to system + clinic-owned presets only
- No permission gating for read (any authenticated user can list presets)

---

### 2. POST /permission-presets

**Description:**  
Create a new custom preset for the current clinic. Server automatically strips platform permission codes (system.manage, clinic.create/read/update/delete/list) even if client sends them.

**Authentication:** Bearer token + `role.manage` permission required

**Request:**
```
POST /api/v1/permission-presets
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "custom_specialist",
  "name": "Bác sĩ chuyên khoa",
  "description": "Khám + kê đơn, không thanh toán",
  "permission_codes": ["exam.create", "exam.read", "exam.update", "prescription.create", "prescription.read"]
}
```

**Request Body Fields:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `code` | String | Yes | 1-50 chars, alphanumeric + underscore | Unique per clinic |
| `name` | String | Yes | 1-200 chars | Display name in Vietnamese |
| `description` | String | No | max 5000 chars | Optional description |
| `permission_codes` | Array<String> | Yes | default [] | Permission codes to include; platform codes auto-stripped |

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "code": "custom_specialist",
  "name": "Bác sĩ chuyên khoa",
  "description": "Khám + kê đơn, không thanh toán",
  "permission_codes": ["exam.create", "exam.read", "exam.update", "prescription.create", "prescription.read"],
  "is_system": false
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | BAD_REQUEST | Missing clinic context or validation error |
| 401 | UNAUTHORIZED | Invalid token or not authenticated |
| 403 | FORBIDDEN | User lacks `role.manage` permission |
| 409 | CONFLICT | Preset code already exists for this clinic |

**Notes:**
- Platform permission codes are silently stripped (e.g., if client sends `["exam.create", "system.manage"]`, only `["exam.create"]` is saved)
- Clinic context (`clinic_id`) is required in token
- Partial unique constraint: `(clinic_id, code) WHERE is_deleted=false`

---

### 3. PATCH /permission-presets/{preset_id}

**Description:**  
Update a custom preset (name, description, permission_codes). System presets cannot be updated.

**Authentication:** Bearer token + `role.manage` permission required

**Request:**
```
PATCH /api/v1/permission-presets/550e8400-e29b-41d4-a716-446655440001
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Bác sĩ chuyên khoa (updated)",
  "permission_codes": ["exam.create", "exam.read", "exam.update", "prescription.create", "prescription.read", "prescription.update"]
}
```

**URL Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `preset_id` | UUID | Yes | ID of preset to update |

**Request Body Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | No | New display name |
| `description` | String | No | New description |
| `permission_codes` | Array<String> | No | New list of codes; platform codes auto-stripped |

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "code": "custom_specialist",
  "name": "Bác sĩ chuyên khoa (updated)",
  "description": null,
  "permission_codes": ["exam.create", "exam.read", "exam.update", "prescription.create", "prescription.read", "prescription.update"],
  "is_system": false
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | BAD_REQUEST | Missing clinic context or validation error |
| 401 | UNAUTHORIZED | Invalid token |
| 403 | FORBIDDEN | System preset immutable or insufficient permission |
| 404 | NOT_FOUND | Preset not found (cross-clinic isolation via RLS) |

**Notes:**
- Cannot update system presets (is_system=true) → 403 Forbidden
- RLS ensures clinic can only update own presets
- Platform codes are stripped even if provided

---

### 4. DELETE /permission-presets/{preset_id}

**Description:**  
Delete a custom preset (soft-delete). System presets cannot be deleted.

**Authentication:** Bearer token + `role.manage` permission required

**Request:**
```
DELETE /api/v1/permission-presets/550e8400-e29b-41d4-a716-446655440001
Authorization: Bearer <token>
```

**URL Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `preset_id` | UUID | Yes | ID of preset to delete |

**Request Body:** None

**Response (204 No Content):**
```
[empty body]
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | BAD_REQUEST | Missing clinic context |
| 401 | UNAUTHORIZED | Invalid token |
| 403 | FORBIDDEN | System preset immutable or insufficient permission |
| 404 | NOT_FOUND | Preset not found |

**Notes:**
- Soft-delete: `is_deleted=true`, `deleted_at=now()`, `deleted_by=current_user()`
- System presets cannot be deleted (is_system=true) → 403 Forbidden

---

### 5. POST /roles/from-preset

**Description:**  
Create a new clinic-scoped role from a permission preset, optionally assigning it to a user. This is the core of the "Cấp bác sĩ toàn quyền" 1-click flow.

**Authentication:** Bearer token + `role.manage` permission required

**Request:**
```
POST /api/v1/roles/from-preset
Authorization: Bearer <token>
Content-Type: application/json

{
  "preset_code": "small_clinic_doctor",
  "role_name": "Bác sĩ Nguyễn Văn A",
  "role_code": "doctor_nguyen_van_a",
  "assign_user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

**Request Body Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `preset_code` | String | Yes | Code of preset to use (e.g., "small_clinic_doctor") |
| `role_name` | String | Yes | Display name for new role (1-200 chars) |
| `role_code` | String | No | Code for new role; auto-slugified from role_name if omitted |
| `assign_user_id` | UUID | No | If provided, immediately assign the new role to this user |

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "code": "doctor_nguyen_van_a",
  "name": "Bác sĩ Nguyễn Văn A",
  "description": null,
  "is_system": false,
  "permission_count": 64
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Role ID |
| `clinic_id` | UUID | Clinic owner |
| `code` | String | Role code |
| `name` | String | Role display name |
| `description` | String \| null | Role description |
| `is_system` | Boolean | false for clinic roles |
| `permission_count` | Integer | Number of permissions assigned to role |

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | BAD_REQUEST | Missing clinic context or validation error |
| 401 | UNAUTHORIZED | Invalid token |
| 403 | FORBIDDEN | Insufficient permission (need `role.manage`) |
| 404 | NOT_FOUND | Preset or user not found |
| 409 | CONFLICT | Role code already exists in clinic |

**Behavioral Details:**
1. Fetches preset from database (prefers clinic-scoped, falls back to system)
2. Computes operational permission set (all permissions − platform blacklist)
3. Intersects preset codes with operational set → `safe_codes`
4. Creates new clinic-scoped role with permissions from `safe_codes`
5. If `assign_user_id` provided: assigns role to user + invalidates user's permission cache
6. Returns role with permission count

**Notes:**
- Platform permission codes are never granted, even if in preset
- If `role_code` omitted, auto-generated by slugifying `role_name`
- If `assign_user_id` omitted, role is created but not assigned to anyone
- Role creation + optional assignment is atomic (transaction)
- Cache invalidation (Redis key deletion) happens immediately if user assigned

---

### 6. POST /roles/{role_id}/apply-preset

**Description:**  
Apply a permission preset to an existing role, replacing all role permissions with preset codes. Invalidates cache for all users holding that role.

**Authentication:** Bearer token + `role.manage` permission required

**Request:**
```
POST /api/v1/roles/550e8400-e29b-41d4-a716-446655440010/apply-preset
Authorization: Bearer <token>
Content-Type: application/json

{
  "preset_code": "small_clinic_doctor"
}
```

**URL Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role_id` | UUID | Yes | ID of role to update |

**Request Body Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `preset_code` | String | Yes | Code of preset to apply |

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "code": "doctor_nguyen_van_a",
  "name": "Bác sĩ Nguyễn Văn A",
  "description": null,
  "is_system": false,
  "permission_count": 64
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | BAD_REQUEST | Missing clinic context or validation error |
| 401 | UNAUTHORIZED | Invalid token |
| 403 | FORBIDDEN | Cannot apply preset to system role or insufficient permission |
| 404 | NOT_FOUND | Role or preset not found |

**Behavioral Details:**
1. Fetches role (ensures clinic_id matches current context)
2. Rejects if role is system role (is_system=true) → 403
3. Fetches preset (prefers clinic-scoped, falls back to system)
4. Computes operational permission set
5. Intersects preset codes with operational set → `safe_codes`
6. **Atomically** deletes all existing `role_permission` rows for this role
7. Creates new `role_permission` rows for all codes in `safe_codes`
8. Finds all users with this role via `user_role` table
9. For each user: invalidates permission cache by deleting Redis key `user:perms:{user_id}`
10. Returns updated role

**Notes:**
- This is a **full replacement** (not an additive merge) — all old permissions removed
- Next user request will immediately get new permission set
- Platform codes are never applied, even if in preset
- System roles cannot be modified → 403 Forbidden

---

## Error Handling

### Standard Error Response Format

```json
{
  "code": "[error_code]",
  "message": "[descriptive message in Vietnamese]"
}
```

### Common HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Request succeeded, returning data |
| 201 | Resource created successfully |
| 204 | Request succeeded, no content returned |
| 400 | Invalid request (validation, missing clinic context) |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden (insufficient permission, immutable resource) |
| 404 | Resource not found (cross-clinic isolation, soft-delete) |
| 409 | Conflict (duplicate code/id) |
| 500 | Internal server error |

### Platform Permission Blacklist

The following permissions can **NEVER** be granted through preset endpoints, even if client sends them. Server strips them unconditionally:

```
system.manage
clinic.create
clinic.read
clinic.update
clinic.delete
clinic.list
```

If a client attempts to include these in `permission_codes`, they are silently removed (not an error; no 400).

---

## Security Notes

1. **Platform Escalation Guard**: All mutation endpoints strip the platform blacklist server-side. Clinic users cannot escalate to `system.manage` or `clinic.*` permissions through preset APIs.

2. **RLS (Row-Level Security)**: 
   - System presets (clinic_id=NULL) visible to all clinics
   - Clinic presets (clinic_id!=NULL) only visible to clinic owner
   - API routes automatically filtered by RLS policy

3. **Permission Gating**: Only users with `role.manage` permission can mutate presets/roles. Read-only endpoints (GET) require authentication but not specific permission.

4. **Clinic Context**: All mutation endpoints require `clinic_id` in JWT token. API returns 400 if missing.

5. **Cache Invalidation**: When role permissions change, all users holding that role have their permission cache invalidated (Redis key deletion). Next request recalculates permissions.

---

## Example Workflows

### Workflow 1: "Cấp bác sĩ toàn quyền" (1-click Doctor Setup)

1. Admin opens Roles page
2. Admin clicks "Cấp bác sĩ toàn quyền" button
3. Admin selects a doctor account from a modal
4. FE calls: `POST /roles/from-preset`
   ```json
   {
     "preset_code": "small_clinic_doctor",
     "role_name": "Bác sĩ Nguyễn Văn A",
     "assign_user_id": "f47ac10b-..."
   }
   ```
5. Backend creates role + assigns to doctor + invalidates cache
6. Doctor logs out and back in, now has all operational permissions

### Workflow 2: Create Custom Preset

1. Admin opens Presets page
2. Admin clicks "Create Preset"
3. Admin fills: code="custom_specialist", name="Bác sĩ chuyên khoa", permissions=[exam.*, prescription.*]
4. FE calls: `POST /permission-presets` with body
5. Backend strips platform codes (if any) and saves
6. Preset appears in list

### Workflow 3: Apply Preset to Existing Role

1. Admin opens Roles page
2. Admin selects a role
3. Admin clicks "Áp preset" and selects "small_clinic_doctor"
4. FE calls: `POST /roles/{role_id}/apply-preset`
5. Backend replaces all role permissions + invalidates cache for all users in role
6. All users in role immediately get new permissions on next request

---

## Rate Limiting & Performance

- No explicit rate limiting documented; standard API rate limits apply
- Cache invalidation for 1000+ users in a role may take 2-5 seconds (SCAN operation)
- Recommend monitoring for large clinics

---

## Versioning

Current API version: **v1** (path prefix: `/api/v1`)

Future breaking changes will increment version (e.g., `/api/v2`)

---

## Implementation References

- **Backend**: `clinic-cms` @ commit `832c7da`, branch `feature/TASK-084-exam-templates`
  - Model: `app/modules/users/models/permission_preset.py`
  - Service: `app/modules/users/services/rbac_service.py`
  - Routes: `app/modules/users/api/routes.py`
  - Migration: `alembic/versions/0046_create_permission_preset.py`

- **Frontend**: `clinic-cms-web` @ commit `aa831e0`
  - Components: `src/pages/admin/RolesPage.tsx`
  - API client: `src/modules/admin/api.ts`
  - Types: `src/modules/admin/types.ts`
  - Translations: `src/locales/{vi,en}/admin.json`

---

**Last Updated:** 2026-07-03  
**Status:** Complete and Tested
