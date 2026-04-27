# API Specification — RBAC Module (TASK-004)

**Version:** 1.0  
**Date:** 2026-04-27  
**Base Path:** `/api/v1`  
**Authentication:** JWT Bearer token (required for all endpoints)

---

## Overview

This document specifies all 20 RBAC API endpoints in detail. All endpoints require `Authorization: Bearer {token}` header containing a valid JWT from the Auth module (TASK-003).

**Endpoint Categories:**
- Users (5 endpoints)
- User Roles (3 endpoints)
- User Extra Permissions (3 endpoints)
- Roles (5 endpoints)
- Role Permissions (3 endpoints)
- Permissions Catalog (1 endpoint)

---

## Users

### 1. List Users

```
GET /api/v1/users
```

**Permission:** `user.manage`  
**Authentication:** Required

**Query Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip (pagination offset) |
| `limit` | integer | No | 50 | Number of records to return (max 200) |

**Success Response (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "username": "dr_hung",
      "email": "hung@clinic.com",
      "full_name": "Dr. Hung Nguyen",
      "is_active": true,
      "created_at": "2026-04-27T10:30:00Z"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 50
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid JWT token
- **403 Forbidden:** User lacks `user.manage` permission

---

### 2. Create User

```
POST /api/v1/users
```

**Permission:** `user.manage`  
**Authentication:** Required

**Request Body:**

```json
{
  "username": "dr_minh",
  "email": "minh@clinic.com",
  "password": "SecurePass123!",
  "full_name": "Dr. Minh Tran",
  "is_active": true
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `username` | string | Yes | 3-50 chars, unique per clinic | Login username |
| `email` | string | Yes | Valid email, unique per clinic | Contact email |
| `password` | string | Yes | Min 8 chars, bcrypt-able | Will be hashed as bcrypt |
| `full_name` | string | No | Max 200 chars | Display name |
| `is_active` | boolean | No | Default: true | Account enabled/disabled |

**Success Response (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "username": "dr_minh",
  "email": "minh@clinic.com",
  "full_name": "Dr. Minh Tran",
  "is_active": true,
  "created_at": "2026-04-27T10:30:00Z"
}
```

**Error Responses:**

- **400 Bad Request:** Invalid input (e.g., password too short)
- **409 Conflict:** Username or email already exists in clinic
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `user.manage` permission

---

### 3. Get User

```
GET /api/v1/users/{id}
```

**Permission:** `user.manage`  
**Authentication:** Required

**Path Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `id` | UUID | User ID |

**Success Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "username": "dr_minh",
  "email": "minh@clinic.com",
  "full_name": "Dr. Minh Tran",
  "is_active": true,
  "created_at": "2026-04-27T10:30:00Z"
}
```

**Error Responses:**

- **404 Not Found:** User not found
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `user.manage` permission

---

### 4. Update User

```
PATCH /api/v1/users/{id}
```

**Permission:** `user.manage`  
**Authentication:** Required

**Request Body (all fields optional):**

```json
{
  "email": "minh.new@clinic.com",
  "full_name": "Dr. Minh Tran (Updated)",
  "is_active": false
}
```

**Success Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "username": "dr_minh",
  "email": "minh.new@clinic.com",
  "full_name": "Dr. Minh Tran (Updated)",
  "is_active": false,
  "updated_at": "2026-04-27T11:00:00Z"
}
```

**Error Responses:**

- **404 Not Found:** User not found
- **409 Conflict:** Email already in use
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `user.manage` permission

---

### 5. Soft-Delete User

```
DELETE /api/v1/users/{id}
```

**Permission:** `user.manage`  
**Authentication:** Required

**Success Response (204 No Content):** Empty body, status 204

**Error Responses:**

- **404 Not Found:** User not found
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `user.manage` permission

---

## User Roles

### 6. List User Roles

```
GET /api/v1/users/{id}/roles
```

**Permission:** `user.manage`  
**Authentication:** Required

**Path Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `id` | UUID | User ID |

**Success Response (200 OK):**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "roles": [
    {
      "id": "1d156e88-38da-4ae8-bbec-d3ffff6eef6a",
      "clinic_id": null,
      "code": "doctor",
      "name": "Doctor",
      "is_system": true,
      "assigned_at": "2026-04-27T10:30:00Z"
    }
  ]
}
```

**Error Responses:**

- **404 Not Found:** User not found
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `user.manage` permission

---

### 7. Assign Role to User

```
POST /api/v1/users/{id}/roles
```

**Permission:** `role.manage`  
**Authentication:** Required

**Request Body:**

```json
{
  "role_id": "1d156e88-38da-4ae8-bbec-d3ffff6eef6a"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role_id` | UUID | Yes | ID of role to assign |

**Success Response (201 Created):**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "role_id": "1d156e88-38da-4ae8-bbec-d3ffff6eef6a",
  "role_code": "doctor",
  "role_name": "Doctor",
  "assigned_at": "2026-04-27T10:30:00Z"
}
```

**Processing Notes:**
- Redis cache for user permissions is invalidated immediately (`DEL user:perms:{user_id}`)
- Audit log entry created: "user_role_assigned"

**Error Responses:**

- **404 Not Found:** User or role not found
- **409 Conflict:** User already has this role
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `role.manage` permission

---

### 8. Revoke Role from User

```
DELETE /api/v1/users/{id}/roles/{role_id}
```

**Permission:** `role.manage`  
**Authentication:** Required

**Path Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `id` | UUID | User ID |
| `role_id` | UUID | Role ID to revoke |

**Success Response (204 No Content):** Empty body, status 204

**Processing Notes:**
- Redis cache for user permissions is invalidated immediately
- User's extra_permissions are NOT deleted (they survive role revocation)
- Audit log entry created: "user_role_revoked"

**Error Responses:**

- **404 Not Found:** User or role not found, or user doesn't have this role
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `role.manage` permission

---

## User Extra Permissions

### 9. List User Extra Permissions

```
GET /api/v1/users/{id}/extra-permissions
```

**Permission:** `user.manage`  
**Authentication:** Required

**Path Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `id` | UUID | User ID |

**Success Response (200 OK):**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "extra_permissions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "permission_code": "invoice.void",
      "type": "deny",
      "reason": "Revoked per manager request on 2026-04-27",
      "created_at": "2026-04-27T10:30:00Z",
      "created_by": "admin-user-id"
    }
  ]
}
```

**Error Responses:**

- **404 Not Found:** User not found
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `user.manage` permission

---

### 10. Add Extra Permission (Grant/Deny)

```
POST /api/v1/users/{id}/extra-permissions
```

**Permission:** `role.manage`  
**Authentication:** Required

**Request Body:**

```json
{
  "permission_code": "invoice.void",
  "type": "deny",
  "reason": "Revoked per audit findings"
}
```

| Field | Type | Required | Valid Values | Description |
|-------|------|----------|--------------|-------------|
| `permission_code` | string | Yes | Any permission code from catalog | Permission to grant/deny |
| `type` | enum | Yes | `"grant"`, `"deny"` | Grant=add, Deny=remove permission |
| `reason` | string | No | Max 500 chars | Audit reason |

**Success Response (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "permission_code": "invoice.void",
  "type": "deny",
  "reason": "Revoked per audit findings",
  "created_at": "2026-04-27T10:30:00Z"
}
```

**Processing Notes:**
- **Idempotent:** Calling twice with identical payload returns the same record (soft-deletes old, creates new with same ID)
- **Overwrite behavior:** If (user_id, permission_code) already exists with different type/reason, old row is soft-deleted and new row created
- Redis cache for user permissions is invalidated immediately
- Audit log entry created: "extra_permission_created"

**Error Responses:**

- **404 Not Found:** User or permission not found
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `role.manage` permission

---

### 11. Delete Extra Permission

```
DELETE /api/v1/users/{id}/extra-permissions/{ep_id}
```

**Permission:** `role.manage`  
**Authentication:** Required

**Path Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `id` | UUID | User ID |
| `ep_id` | UUID | Extra permission ID to delete |

**Success Response (204 No Content):** Empty body, status 204

**Processing Notes:**
- Soft-deletes the extra_permission row (is_deleted=TRUE)
- Redis cache for user permissions is invalidated immediately
- Audit log entry created: "extra_permission_deleted"

**Error Responses:**

- **404 Not Found:** User or extra permission not found
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `role.manage` permission

---

## Roles

### 12. List Roles

```
GET /api/v1/roles
```

**Permission:** `user.manage`  
**Authentication:** Required

**Query Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Pagination offset |
| `limit` | integer | No | 50 | Max records (max 200) |

**Success Response (200 OK):**

```json
{
  "data": [
    {
      "id": "1d156e88-38da-4ae8-bbec-d3ffff6eef6a",
      "clinic_id": null,
      "code": "admin",
      "name": "Administrator",
      "description": "Full system access",
      "is_system": true,
      "created_at": "2026-04-26T00:00:00Z"
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 50
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `user.manage` permission

---

### 13. Create Role

```
POST /api/v1/roles
```

**Permission:** `role.manage`  
**Authentication:** Required

**Request Body:**

```json
{
  "code": "custom_doctor",
  "name": "Doctor (Extended)",
  "description": "Doctor with extra invoice permissions"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `code` | string | Yes | 3-50 chars, unique per clinic | Role identifier |
| `name` | string | Yes | Max 200 chars | Display name |
| `description` | string | No | Max 1000 chars | Role purpose |

**Success Response (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "code": "custom_doctor",
  "name": "Doctor (Extended)",
  "description": "Doctor with extra invoice permissions",
  "is_system": false,
  "created_at": "2026-04-27T10:30:00Z"
}
```

**Error Responses:**

- **409 Conflict:** Role code already exists in clinic
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `role.manage` permission

---

### 14. Get Role

```
GET /api/v1/roles/{id}
```

**Permission:** `user.manage`  
**Authentication:** Required

**Path Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `id` | UUID | Role ID |

**Success Response (200 OK):**

```json
{
  "id": "1d156e88-38da-4ae8-bbec-d3ffff6eef6a",
  "clinic_id": null,
  "code": "doctor",
  "name": "Doctor",
  "description": "Clinic doctor role",
  "is_system": true,
  "created_at": "2026-04-26T00:00:00Z"
}
```

**Error Responses:**

- **404 Not Found:** Role not found
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `user.manage` permission

---

### 15. Update Role

```
PATCH /api/v1/roles/{id}
```

**Permission:** `role.manage`  
**Authentication:** Required

**Request Body (all optional):**

```json
{
  "name": "Doctor (v2)",
  "description": "Updated description"
}
```

**Success Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440004",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "code": "custom_doctor",
  "name": "Doctor (v2)",
  "description": "Updated description",
  "is_system": false,
  "updated_at": "2026-04-27T11:00:00Z"
}
```

**Error Responses:**

- **403 Forbidden:** Role is system role (`is_system=true`) — cannot modify
- **404 Not Found:** Role not found
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `role.manage` permission

---

### 16. Delete Role

```
DELETE /api/v1/roles/{id}
```

**Permission:** `role.manage`  
**Authentication:** Required

**Success Response (204 No Content):** Empty body, status 204

**Error Responses:**

- **403 Forbidden:** Role is system role (`is_system=true`) — cannot delete
- **404 Not Found:** Role not found
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `role.manage` permission

---

## Role Permissions

### 17. List Role Permissions

```
GET /api/v1/roles/{id}/permissions
```

**Permission:** `user.manage`  
**Authentication:** Required

**Path Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `id` | UUID | Role ID |

**Success Response (200 OK):**

```json
{
  "role_id": "1d156e88-38da-4ae8-bbec-d3ffff6eef6a",
  "permissions": [
    {
      "code": "patient.read",
      "description": "View patient records",
      "category": "patient",
      "granted_at": "2026-04-26T00:00:00Z"
    }
  ]
}
```

**Error Responses:**

- **404 Not Found:** Role not found
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `user.manage` permission

---

### 18. Add Permission to Role

```
POST /api/v1/roles/{id}/permissions
```

**Permission:** `role.manage`  
**Authentication:** Required

**Request Body:**

```json
{
  "permission_code": "invoice.void"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `permission_code` | string | Yes | Permission code from catalog |

**Success Response (201 Created):**

```json
{
  "role_id": "550e8400-e29b-41d4-a716-446655440004",
  "permission_code": "invoice.void",
  "granted_at": "2026-04-27T10:30:00Z"
}
```

**Error Responses:**

- **403 Forbidden:** Role is system role (`is_system=true`) — cannot modify permissions
- **404 Not Found:** Role or permission not found
- **409 Conflict:** Permission already assigned to role
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `role.manage` permission

---

### 19. Remove Permission from Role

```
DELETE /api/v1/roles/{id}/permissions/{code}
```

**Permission:** `role.manage`  
**Authentication:** Required

**Path Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `id` | UUID | Role ID |
| `code` | string | Permission code (e.g., `invoice.void`) |

**Success Response (204 No Content):** Empty body, status 204

**Error Responses:**

- **403 Forbidden:** Role is system role (`is_system=true`) — cannot modify permissions
- **404 Not Found:** Role or permission mapping not found
- **401 Unauthorized:** Missing or invalid JWT
- **403 Forbidden:** Lacks `role.manage` permission

---

## Permissions Catalog

### 20. List All Permissions (Catalog)

```
GET /api/v1/permissions
```

**Permission:** None (any authenticated user)  
**Authentication:** Required

**Query Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `category` | string | No | Filter by category (e.g., `"patient"`, `"invoice"`) |
| `skip` | integer | No | Pagination offset |
| `limit` | integer | No | Max records (max 200) |

**Success Response (200 OK):**

```json
{
  "data": [
    {
      "code": "patient.read",
      "description": "View patient records",
      "category": "patient",
      "created_at": "2026-04-26T00:00:00Z"
    },
    {
      "code": "patient.write",
      "description": "Create or update patient records",
      "category": "patient",
      "created_at": "2026-04-26T00:00:00Z"
    }
  ],
  "total": 38,
  "skip": 0,
  "limit": 50
}
```

**Error Responses:**

- **401 Unauthorized:** Missing or invalid JWT

---

## Error Response Format

All error responses follow this format:

```json
{
  "code": "[ERROR_CODE]",
  "message": "[Human-readable message]"
}
```

**Common Error Codes:**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid JWT token |
| `FORBIDDEN` | 403 | User lacks required permission or system role guard triggered |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Duplicate unique constraint (e.g., username exists) |
| `INVALID_REQUEST` | 400 | Invalid input parameters |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Example Request/Response Flow

### Scenario: Doctor with Extra Deny

1. **Setup:** Doctor user has `invoice.void` permission from role
2. **Manager grants extra-deny:** POST `/users/{id}/extra-permissions` with type=`"deny"`
3. **User's effective perms:** `(doctor_perms ∪ extra_grants) − extra_denies`
4. **Result:** `invoice.void` removed from effective permissions
5. **Next API call:** Any endpoint requiring `invoice.void` → 403 Forbidden

---

**End of API Specification**
