# Super Admin API Reference — 10 Endpoints

**Project:** Clinic CMS  
**Task:** TASK-070  
**Date:** 2026-05-31  
**Version:** 1.0

---

## Overview

Super Admin FE consumes 10 API endpoints from Backend `/api/v1/superadmin/*` module.

**Authentication**: All endpoints require `Authorization: Bearer {token}` with JWT claim `is_superuser: true`.

**Base URL**: `/api/v1/superadmin`

---

## Endpoint Summary

| # | Method | Path | Description |
|---|--------|------|-------------|
| 1 | GET | `/stats` | System statistics: total clinics, users, active/locked counts |
| 2 | GET | `/clinics` | List all clinics (paginated) |
| 3 | POST | `/clinics` | Create new clinic |
| 4 | PATCH | `/clinics/{id}` | Update clinic (toggle active/inactive) |
| 5 | GET | `/accounts` | List all accounts cross-tenant (paginated, filterable) |
| 6 | POST | `/accounts` | Create new account |
| 7 | PATCH | `/accounts/{id}` | Update account (lock/unlock, activate/deactivate) |
| 8 | POST | `/accounts/{id}/reset-password` | Reset account password |
| 9 | GET | `/roles` | List all system roles |
| 10 | GET | `/audit-logs` | List audit logs cross-tenant (paginated, filterable) |

---

## Endpoint Details

### 1. GET /stats

**Purpose:** Fetch system-wide statistics.

**Request:**
```
GET /api/v1/superadmin/stats
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "total_clinics": 1283,
  "total_accounts": 1832,
  "active_accounts": 1832,
  "locked_accounts": 1,
  "inactive_clinics": 1
}
```

**Used by:** SuperAdminDashboardPage (stat cards)

---

### 2. GET /clinics

**Purpose:** Retrieve paginated list of all clinics.

**Request:**
```
GET /api/v1/superadmin/clinics?skip=0&limit=50&search=&active=all
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip` (int, default 0): Pagination offset
- `limit` (int, default 50): Page size
- `search` (string, optional): Filter by clinic name or code
- `active` (string, optional): Filter by status — `all`, `active`, `inactive`
- `order_by` (string, optional): Sort field — `name`, `code`, `created_at` (+ `_desc` suffix)

**Response (200 OK):**
```json
{
  "total": 1283,
  "skip": 0,
  "limit": 50,
  "data": [
    {
      "id": "uuid-1",
      "name": "Clinic A",
      "code": "CLI_A",
      "specialty": "Tổng hợp",
      "is_active": true,
      "user_count": 5,
      "created_at": "2026-05-01T10:00:00Z"
    },
    // ... 49 more
  ]
}
```

**Used by:** SuperAdminClinicsPage (table), SuperAdminDashboardPage (top-5)

---

### 3. POST /clinics

**Purpose:** Create a new clinic.

**Request:**
```
POST /api/v1/superadmin/clinics
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Clinic B",
  "code": "CLI_B",
  "specialty": "Tổng hợp"
}
```

**Request Body:**
- `name` (string, required): Clinic name, 1-100 chars
- `code` (string, required): Unique code, 3-20 chars, alphanumeric + underscore
- `specialty` (string, required): Specialty type

**Response (201 Created):**
```json
{
  "id": "uuid-new",
  "name": "Clinic B",
  "code": "CLI_B",
  "specialty": "Tổng hợp",
  "is_active": true,
  "user_count": 0,
  "created_at": "2026-05-31T14:00:00Z"
}
```

**Error (400 Bad Request):**
```json
{
  "code": "INVALID_REQUEST",
  "message": "Clinic code must be unique"
}
```

**Used by:** SuperAdminClinicsPage (create modal)

---

### 4. PATCH /clinics/{id}

**Purpose:** Update clinic (toggle active/inactive status).

**Request:**
```
PATCH /api/v1/superadmin/clinics/{clinic_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "is_active": false
}
```

**Request Body:**
- `is_active` (boolean, optional): Enable/disable clinic

**Response (200 OK):**
```json
{
  "id": "uuid-1",
  "name": "Clinic A",
  "code": "CLI_A",
  "specialty": "Tổng hợp",
  "is_active": false,
  "user_count": 5,
  "created_at": "2026-05-01T10:00:00Z"
}
```

**Used by:** SuperAdminClinicsPage (inline toggle)

---

### 5. GET /accounts

**Purpose:** List all accounts cross-tenant (all clinics).

**Request:**
```
GET /api/v1/superadmin/accounts?skip=0&limit=50&clinic_id=&search=&status=all
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip` (int, default 0): Pagination offset
- `limit` (int, default 50): Page size
- `clinic_id` (string, optional): Filter by clinic UUID
- `search` (string, optional): Filter by username or email
- `status` (string, optional): Filter — `all`, `active`, `locked`, `inactive`
- `order_by` (string, optional): Sort field — `username`, `last_login`, `created_at`

**Response (200 OK):**
```json
{
  "total": 1832,
  "skip": 0,
  "limit": 50,
  "data": [
    {
      "id": "account-uuid-1",
      "username": "admin_clinic1",
      "email": "admin@clinic1.com",
      "clinic_id": "clinic-uuid-1",
      "clinic_name": "Clinic A",
      "role_codes": ["admin"],
      "is_active": true,
      "is_locked": false,
      "last_login_at": "2026-05-31T10:30:00Z",
      "created_at": "2026-05-01T09:00:00Z"
    },
    // ... 49 more
  ]
}
```

**Note:** `full_name` is NOT returned (cross-tenant PII encryption limitation).

**Used by:** SuperAdminAccountsPage (table)

---

### 6. POST /accounts

**Purpose:** Create a new account.

**Request:**
```
POST /api/v1/superadmin/accounts
Authorization: Bearer {token}
Content-Type: application/json

{
  "clinic_id": "clinic-uuid-1",
  "username": "new_admin",
  "email": "new_admin@clinic.com",
  "password": "SecurePass123!",
  "role_codes": ["admin"]
}
```

**Request Body:**
- `clinic_id` (string, required): Target clinic UUID
- `username` (string, required): Unique username, 4-20 chars
- `email` (string, required): Valid email
- `password` (string, required): 8+ chars, must contain uppercase, lowercase, digit, special char
- `role_codes` (array[string], required): At least 1 role — `admin`, `doctor`, `nurse`, etc.

**Response (201 Created):**
```json
{
  "id": "account-uuid-new",
  "username": "new_admin",
  "email": "new_admin@clinic.com",
  "clinic_id": "clinic-uuid-1",
  "clinic_name": "Clinic A",
  "role_codes": ["admin"],
  "is_active": true,
  "is_locked": false,
  "created_at": "2026-05-31T14:00:00Z"
}
```

**Error (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must contain uppercase, lowercase, digit, special char",
      "type": "value_error"
    }
  ]
}
```

**Used by:** SuperAdminAccountsPage (create modal)

---

### 7. PATCH /accounts/{id}

**Purpose:** Update account (lock/unlock, activate/deactivate).

**Request:**
```
PATCH /api/v1/superadmin/accounts/{account_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "is_locked": true,
  "is_active": false
}
```

**Request Body:**
- `is_locked` (boolean, optional): Lock/unlock account
- `is_active` (boolean, optional): Activate/deactivate account

**Response (200 OK):**
```json
{
  "id": "account-uuid-1",
  "username": "admin_clinic1",
  "email": "admin@clinic1.com",
  "clinic_id": "clinic-uuid-1",
  "clinic_name": "Clinic A",
  "role_codes": ["admin"],
  "is_active": false,
  "is_locked": true,
  "last_login_at": "2026-05-31T10:30:00Z",
  "created_at": "2026-05-01T09:00:00Z"
}
```

**Used by:** SuperAdminAccountsPage (lock/unlock button)

---

### 8. POST /accounts/{id}/reset-password

**Purpose:** Reset account password.

**Request:**
```
POST /api/v1/superadmin/accounts/{account_id}/reset-password
Authorization: Bearer {token}
Content-Type: application/json

{
  "send_email": true
}
```

**Request Body:**
- `send_email` (boolean, optional): If true, send new password to account's email

**Response (200 OK):**
```json
{
  "id": "account-uuid-1",
  "username": "admin_clinic1",
  "temporary_password": "TempPass123456",
  "expires_in_hours": 24,
  "email_sent": true
}
```

**Used by:** SuperAdminAccountsPage (reset password action)

---

### 9. GET /roles

**Purpose:** Retrieve all system roles.

**Request:**
```
GET /api/v1/superadmin/roles
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "code": "admin",
      "name": "Quản trị viên",
      "description": "Quản trị viên phòng khám"
    },
    {
      "code": "doctor",
      "name": "Bác sĩ",
      "description": "Bác sĩ phòng khám"
    },
    {
      "code": "nurse",
      "name": "Y tá",
      "description": "Y tá phòng khám"
    },
    {
      "code": "receptionist",
      "name": "Tiếp tân",
      "description": "Tiếp tân phòng khám"
    }
  ]
}
```

**Used by:** SuperAdminAccountsPage (create account form — role multi-checkbox)

---

### 10. GET /audit-logs

**Purpose:** Retrieve audit logs cross-tenant with filtering.

**Request:**
```
GET /api/v1/superadmin/audit-logs?skip=0&limit=50&clinic_id=&action=&date_from=&date_to=
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip` (int, default 0): Pagination offset
- `limit` (int, default 50): Page size
- `clinic_id` (string, optional): Filter by clinic UUID
- `action` (string, optional): Filter by action type — `CREATE`, `UPDATE`, `DELETE`, `LOGIN`, `LOGOUT`, `LOCK_ACCOUNT`, `RESET_PASSWORD`, etc.
- `date_from` (string, optional): ISO 8601 date — filter logs from this date
- `date_to` (string, optional): ISO 8601 date — filter logs until this date
- `order_by` (string, optional): Sort — `created_at_desc` (default), `created_at_asc`, `action`

**Response (200 OK):**
```json
{
  "total": 5432,
  "skip": 0,
  "limit": 50,
  "data": [
    {
      "id": "log-uuid-1",
      "timestamp": "2026-05-31T14:30:00Z",
      "clinic_id": "clinic-uuid-1",
      "clinic_name": "Clinic A",
      "user_id": "account-uuid-5",
      "username": "admin_clinic1",
      "action": "CREATE",
      "entity_type": "ACCOUNT",
      "entity_id": "account-uuid-new",
      "description": "Created account: new_admin",
      "details": {
        "username": "new_admin",
        "clinic_id": "clinic-uuid-1"
      }
    },
    {
      "id": "log-uuid-2",
      "timestamp": "2026-05-31T14:00:00Z",
      "clinic_id": "clinic-uuid-2",
      "clinic_name": "Clinic B",
      "user_id": "account-uuid-10",
      "username": "doctor_clinic2",
      "action": "LOGIN",
      "entity_type": "ACCOUNT",
      "entity_id": "account-uuid-10",
      "description": "User logged in",
      "details": {
        "ip_address": "192.168.1.100"
      }
    },
    // ... 48 more
  ]
}
```

**Used by:** SuperAdminAuditLogsPage (read-only table)

---

## Error Responses (Common)

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```
**Action:** FE logout + redirect `/login`

### 403 Forbidden
```json
{
  "detail": "Not authorized to perform this action"
}
```
**Action:** Toast "Không có quyền truy cập"

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```
**Action:** Toast "Không tìm thấy dữ liệu"

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```
**Action:** Toast "Lỗi hệ thống, vui lòng thử lại sau"

---

## Type Definitions (TypeScript)

See `src/modules/superadmin/types.ts` in clinic-cms-web for TypeScript interfaces:

```typescript
export interface Stats {
  total_clinics: number;
  total_accounts: number;
  active_accounts: number;
  locked_accounts: number;
  inactive_clinics: number;
}

export interface Clinic {
  id: string;
  name: string;
  code: string;
  specialty: string;
  is_active: boolean;
  user_count: number;
  created_at: string;
}

export interface Account {
  id: string;
  username: string;
  email: string;
  clinic_id: string;
  clinic_name: string;
  role_codes: string[];
  is_active: boolean;
  is_locked: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface Role {
  code: string;
  name: string;
  description: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  clinic_id: string;
  clinic_name: string;
  user_id: string;
  username: string;
  action: string;
  entity_type: string;
  entity_id: string;
  description: string;
  details: Record<string, any>;
}

export interface PaginatedResponse<T> {
  total: number;
  skip: number;
  limit: number;
  data: T[];
}
```

---

## API Client Usage (FE)

All endpoints are wrapped in `src/modules/superadmin/api.ts`:

```typescript
import { superadminApi } from '@/modules/superadmin/api';

// Get stats
const stats = await superadminApi.getStats();

// Get clinics
const clinics = await superadminApi.getClinics({ skip: 0, limit: 50 });

// Create clinic
const newClinic = await superadminApi.createClinic({ name, code, specialty });

// Update clinic
await superadminApi.updateClinic(clinicId, { is_active: false });

// Get accounts
const accounts = await superadminApi.getAccounts({ clinic_id, skip: 0, limit: 50 });

// Create account
const newAccount = await superadminApi.createAccount({ clinic_id, username, email, password, role_codes });

// Update account
await superadminApi.updateAccount(accountId, { is_locked: true });

// Reset password
const result = await superadminApi.resetPassword(accountId, { send_email: true });

// Get roles
const roles = await superadminApi.getRoles();

// Get audit logs
const logs = await superadminApi.getAuditLogs({ clinic_id, action, skip: 0, limit: 50 });
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-31
