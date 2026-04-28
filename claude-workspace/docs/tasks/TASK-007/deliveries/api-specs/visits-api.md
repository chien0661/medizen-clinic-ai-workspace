# Visit API Specifications

**Task:** TASK-007  
**Module:** Visit Management  
**Base Path:** `/api/v1/visits`  
**Version:** 1.0  
**Status:** APPROVED & TESTED (117/117 tests pass)

---

## Authentication

All endpoints require a valid JWT token in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

Missing or invalid token → **401 Unauthorized**

---

## Endpoints Overview

| # | Method | Path | Summary | Permission |
|---|--------|------|---------|-----------|
| 1 | GET | `/visits` | List visits with optional filters | `visit.read` |
| 2 | POST | `/visits` | Create new walk-in visit | `visit.write` |
| 3 | GET | `/visits/queue` | Get active queue (WAITING + IN_PROGRESS) | `visit.read` |
| 4 | POST | `/visits/call-next` | Atomically pick next WAITING visit | `visit.write` |
| 5 | GET | `/visits/{visit_id}` | Get visit detail by ID | `visit.read` |
| 6 | PATCH | `/visits/{visit_id}` | Update non-status fields | `visit.write` |
| 7 | POST | `/visits/{visit_id}/start` | Start visit (WAITING → IN_PROGRESS) | `visit.write` |
| 8 | POST | `/visits/{visit_id}/complete` | Complete visit (IN_PROGRESS → AWAITING_PAYMENT) | `visit.write` |
| 9 | POST | `/visits/{visit_id}/cancel` | Cancel visit with reason | `visit.cancel` |
| 10 | POST | `/visits/{visit_id}/mark-paid` | Mark as paid (AWAITING_PAYMENT → COMPLETED) | `payment.receive` |

---

## Common Response Schema

### Success Response (200/201)

**VisitResponse:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "patient_id": "550e8400-e29b-41d4-a716-446655440002",
  "doctor_id": "550e8400-e29b-41d4-a716-446655440003",
  "assigned_doctor_id": "550e8400-e29b-41d4-a716-446655440004",
  "appointment_id": null,
  "visit_number": "20260428-001",
  "visit_date": "2026-04-28",
  "status": "IN_PROGRESS",
  "priority": 5,
  "chief_complaint": "Đau đầu",
  "notes": "Bệnh nhân có tiền sử cao huyết áp",
  "is_follow_up": false,
  "is_returning": true,
  "cancel_reason": null,
  "started_at": "2026-04-28T09:15:00+07:00",
  "completed_at": null,
  "cancelled_at": null,
  "created_at": "2026-04-28T09:10:00+07:00",
  "updated_at": "2026-04-28T09:15:00+07:00",
  "created_by": "550e8400-e29b-41d4-a716-446655440003",
  "updated_by": null,
  "version": 2
}
```

### Error Response (4xx/5xx)

```json
{
  "detail": "Error message describing the issue"
}
```

or for validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "priority"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## Endpoint Details

### 1. GET /visits — List Visits

#### Request

```http
GET /api/v1/visits?status=WAITING&doctor_id=<uuid>&skip=0&limit=50
Authorization: Bearer <token>
```

**Query Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `status` | string | No | null | Filter by status (WAITING, IN_PROGRESS, AWAITING_PAYMENT, COMPLETED, CANCELLED) |
| `doctor_id` | UUID | No | null | Filter by assigned/actual doctor |
| `visit_date` | date (YYYY-MM-DD) | No | null | Filter by visit date |
| `skip` | integer ≥ 0 | No | 0 | Pagination offset |
| `limit` | integer 1-500 | No | 50 | Page size |

#### Response

**200 OK:**

```json
{
  "items": [
    { /* VisitResponse */ }
  ],
  "total": 15,
  "skip": 0,
  "limit": 50
}
```

**Error Responses:**

- `401 Unauthorized` — Missing/invalid token
- `403 Forbidden` — Missing `visit.read` permission
- `400 Bad Request` — Invalid clinic_id in context

#### curl Example

```bash
curl -X GET \
  "http://localhost:8000/api/v1/visits?status=WAITING&limit=10" \
  -H "Authorization: Bearer <token>"
```

---

### 2. POST /visits — Create Visit

#### Request

```http
POST /api/v1/visits
Authorization: Bearer <token>
Content-Type: application/json
```

**Body (VisitCreate):**

```json
{
  "patient_id": "550e8400-e29b-41d4-a716-446655440002",
  "chief_complaint": "Đau đầu, chóng mặt",
  "priority": 5,
  "appointment_id": null,
  "assigned_doctor_id": null,
  "is_follow_up": false,
  "is_returning": true,
  "notes": "Bệnh nhân có tiền sử cao huyết áp"
}
```

**Fields:**

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| `patient_id` | UUID | Yes | — | Must exist, belong to clinic |
| `chief_complaint` | string | No | null | — |
| `priority` | integer | No | 0 | 0-100 |
| `appointment_id` | UUID | No | null | — |
| `assigned_doctor_id` | UUID | No | null | — |
| `is_follow_up` | boolean | No | false | — |
| `is_returning` | boolean | No | false | — |
| `notes` | string | No | null | — |

#### Response

**201 Created:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "patient_id": "550e8400-e29b-41d4-a716-446655440002",
  "doctor_id": null,
  "assigned_doctor_id": null,
  "visit_number": "20260428-001",
  "visit_date": "2026-04-28",
  "status": "WAITING",
  "priority": 5,
  "chief_complaint": "Đau đầu, chóng mặt",
  "notes": "Bệnh nhân có tiền sử cao huyết áp",
  "is_follow_up": false,
  "is_returning": true,
  "cancel_reason": null,
  "started_at": null,
  "completed_at": null,
  "cancelled_at": null,
  "created_at": "2026-04-28T09:10:00+07:00",
  "updated_at": "2026-04-28T09:10:00+07:00",
  "created_by": "550e8400-e29b-41d4-a716-446655440003",
  "updated_by": null,
  "version": 1
}
```

**Error Responses:**

- `400 Bad Request` — clinic_id missing
- `401 Unauthorized` — Invalid token
- `403 Forbidden` — Missing `visit.write` permission
- `404 Not Found` — Patient doesn't exist (NOTE: currently returns 500 with FK error — BUG-001)
- `422 Unprocessable Entity` — Invalid field (e.g., priority > 100)

#### curl Example

```bash
curl -X POST \
  http://localhost:8000/api/v1/visits \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "550e8400-e29b-41d4-a716-446655440002",
    "chief_complaint": "Đau đầu",
    "priority": 5,
    "is_returning": true
  }'
```

---

### 3. GET /visits/queue — Active Queue

#### Request

```http
GET /api/v1/visits/queue?skip=0&limit=100
Authorization: Bearer <token>
```

**Query Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `skip` | integer ≥ 0 | No | 0 | Pagination offset |
| `limit` | integer 1-500 | No | 100 | Page size |

#### Response

**200 OK:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
    "patient_id": "550e8400-e29b-41d4-a716-446655440002",
    "doctor_id": "550e8400-e29b-41d4-a716-446655440003",
    "assigned_doctor_id": "550e8400-e29b-41d4-a716-446655440004",
    "visit_number": "20260428-001",
    "visit_date": "2026-04-28",
    "status": "IN_PROGRESS",
    "priority": 10,
    "chief_complaint": "Đau đầu",
    "notes": null,
    "is_follow_up": false,
    "is_returning": true,
    "cancel_reason": null,
    "started_at": "2026-04-28T09:15:00+07:00",
    "completed_at": null,
    "cancelled_at": null,
    "created_at": "2026-04-28T09:10:00+07:00",
    "updated_at": "2026-04-28T09:15:00+07:00",
    "created_by": "550e8400-e29b-41d4-a716-446655440003",
    "updated_by": null,
    "version": 2
  }
]
```

Returns array of VisitResponse, ordered by priority DESC, created_at ASC.

**Performance:** p95 = 13.6 ms for 50 visits (AC threshold 50 ms).

#### curl Example

```bash
curl -X GET \
  "http://localhost:8000/api/v1/visits/queue?limit=20" \
  -H "Authorization: Bearer <token>"
```

---

### 4. POST /visits/call-next — Call Next Visit

#### Request

```http
POST /api/v1/visits/call-next
Authorization: Bearer <token>
Content-Type: application/json
```

No request body.

#### Response

**200 OK:**

```json
{
  "visit": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
    "patient_id": "550e8400-e29b-41d4-a716-446655440002",
    "doctor_id": "550e8400-e29b-41d4-a716-446655440003",
    "assigned_doctor_id": "550e8400-e29b-41d4-a716-446655440003",
    "visit_number": "20260428-001",
    "visit_date": "2026-04-28",
    "status": "IN_PROGRESS",
    "priority": 5,
    "chief_complaint": "Đau đầu",
    "notes": null,
    "is_follow_up": false,
    "is_returning": true,
    "cancel_reason": null,
    "started_at": "2026-04-28T09:15:00+07:00",
    "completed_at": null,
    "cancelled_at": null,
    "created_at": "2026-04-28T09:10:00+07:00",
    "updated_at": "2026-04-28T09:15:00+07:00",
    "created_by": "550e8400-e29b-41d4-a716-446655440003",
    "updated_by": "550e8400-e29b-41d4-a716-446655440003",
    "version": 2
  },
  "reason": "assigned_doctor_match"
}
```

**Fields:**

- `visit` — VisitResponse with status updated to IN_PROGRESS
- `reason` — string, one of:
  - `"assigned_doctor_match"` — visit.assigned_doctor_id = calling_doctor
  - `"unassigned"` — visit.assigned_doctor_id IS NULL
  - `"other"` — visit.assigned_doctor_id ≠ calling_doctor

**Error Responses:**

- `401 Unauthorized` — Invalid token
- `403 Forbidden` — Missing `visit.write` permission
- `404 Not Found` — No WAITING visits in queue

**Concurrency:** Uses `SELECT ... FOR UPDATE SKIP LOCKED` to prevent race conditions. Each concurrent caller gets a different visit. Verified with 5-way concurrent test (AC #5).

#### curl Example

```bash
curl -X POST \
  http://localhost:8000/api/v1/visits/call-next \
  -H "Authorization: Bearer <token>"
```

---

### 5. GET /visits/{visit_id} — Get Visit Detail

#### Request

```http
GET /api/v1/visits/{visit_id}
Authorization: Bearer <token>
```

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `visit_id` | UUID | Yes | Visit ID |

#### Response

**200 OK:** VisitResponse

**Error Responses:**

- `401 Unauthorized` — Invalid token
- `403 Forbidden` — Missing `visit.read` permission
- `404 Not Found` — Visit doesn't exist or doesn't belong to clinic

#### curl Example

```bash
curl -X GET \
  http://localhost:8000/api/v1/visits/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"
```

---

### 6. PATCH /visits/{visit_id} — Update Visit

#### Request

```http
PATCH /api/v1/visits/{visit_id}
Authorization: Bearer <token>
Content-Type: application/json
```

**Body (VisitUpdate, all fields optional):**

```json
{
  "chief_complaint": "Updated complaint",
  "notes": "Updated notes",
  "priority": 10,
  "assigned_doctor_id": "550e8400-e29b-41d4-a716-446655440004",
  "is_follow_up": true,
  "is_returning": true
}
```

**Fields:**

| Field | Type | Constraints |
|-------|------|-------------|
| `chief_complaint` | string | — |
| `notes` | string | — |
| `priority` | integer | 0-100 |
| `assigned_doctor_id` | UUID | — |
| `is_follow_up` | boolean | — |
| `is_returning` | boolean | — |

#### Response

**200 OK:** VisitResponse (updated)

**Error Responses:**

- `401 Unauthorized` — Invalid token
- `403 Forbidden` — Missing `visit.write` permission
- `404 Not Found` — Visit doesn't exist
- `422 Unprocessable Entity` — Invalid field value

#### curl Example

```bash
curl -X PATCH \
  http://localhost:8000/api/v1/visits/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"priority": 10, "notes": "Updated"}'
```

---

### 7. POST /visits/{visit_id}/start — Start Visit

#### Request

```http
POST /api/v1/visits/{visit_id}/start
Authorization: Bearer <token>
Content-Type: application/json
```

No request body (or empty JSON `{}`).

#### Response

**200 OK:** VisitResponse with:
- `status` = "IN_PROGRESS"
- `doctor_id` = current user ID
- `started_at` = current timestamp

**Error Responses:**

- `401 Unauthorized` — Invalid token
- `403 Forbidden` — Missing `visit.write` permission
- `404 Not Found` — Visit doesn't exist
- `409 Conflict` — Invalid state transition (status must be WAITING)

#### curl Example

```bash
curl -X POST \
  http://localhost:8000/api/v1/visits/550e8400-e29b-41d4-a716-446655440000/start \
  -H "Authorization: Bearer <token>"
```

---

### 8. POST /visits/{visit_id}/complete — Complete Visit

#### Request

```http
POST /api/v1/visits/{visit_id}/complete
Authorization: Bearer <token>
Content-Type: application/json
```

No request body.

#### Response

**200 OK:** VisitResponse with:
- `status` = "AWAITING_PAYMENT"
- `completed_at` = current timestamp

**Error Responses:**

- `401 Unauthorized` — Invalid token
- `403 Forbidden` — Missing `visit.write` permission
- `404 Not Found` — Visit doesn't exist
- `409 Conflict` — Invalid state transition (status must be IN_PROGRESS, or doctor_id mismatch)

#### curl Example

```bash
curl -X POST \
  http://localhost:8000/api/v1/visits/550e8400-e29b-41d4-a716-446655440000/complete \
  -H "Authorization: Bearer <token>"
```

---

### 9. POST /visits/{visit_id}/cancel — Cancel Visit

#### Request

```http
POST /api/v1/visits/{visit_id}/cancel
Authorization: Bearer <token>
Content-Type: application/json
```

**Body (VisitCancelRequest):**

```json
{
  "cancel_reason": "Bệnh nhân yêu cầu dời lịch"
}
```

**Fields:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `cancel_reason` | string | Yes | Min length 3, not blank (whitespace only rejected) |

#### Response

**200 OK:** VisitResponse with:
- `status` = "CANCELLED"
- `cancel_reason` = provided reason
- `cancelled_at` = current timestamp

**Error Responses:**

- `401 Unauthorized` — Invalid token
- `403 Forbidden` — Missing `visit.cancel` permission (only admin/doctor)
- `404 Not Found` — Visit doesn't exist
- `409 Conflict` — Invalid state transition (status = COMPLETED cannot be cancelled)
- `422 Unprocessable Entity` — cancel_reason < 3 chars or whitespace only

#### curl Example

```bash
curl -X POST \
  http://localhost:8000/api/v1/visits/550e8400-e29b-41d4-a716-446655440000/cancel \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"cancel_reason": "Bệnh nhân yêu cầu hoãn"}'
```

---

### 10. POST /visits/{visit_id}/mark-paid — Mark as Paid

#### Request

```http
POST /api/v1/visits/{visit_id}/mark-paid
Authorization: Bearer <token>
Content-Type: application/json
```

No request body.

#### Response

**200 OK:** VisitResponse with:
- `status` = "COMPLETED"

**Error Responses:**

- `401 Unauthorized` — Invalid token
- `403 Forbidden` — Missing `payment.receive` permission (only admin/receptionist)
- `404 Not Found` — Visit doesn't exist
- `409 Conflict` — Invalid state transition (status must be AWAITING_PAYMENT)

**Note:** This is a terminal state. No further transitions allowed.

#### curl Example

```bash
curl -X POST \
  http://localhost:8000/api/v1/visits/550e8400-e29b-41d4-a716-446655440000/mark-paid \
  -H "Authorization: Bearer <token>"
```

---

## Error Code Reference

| HTTP Code | Meaning | Common Causes |
|-----------|---------|---------------|
| 200 | OK | Request succeeded |
| 201 | Created | Visit successfully created |
| 400 | Bad Request | Missing clinic_id context |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Missing required permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Invalid state transition |
| 422 | Unprocessable Entity | Validation error (bad data) |
| 500 | Internal Server Error | Unexpected server error |

---

## Tenant Isolation (RLS)

All endpoints enforce Row-Level Security (RLS) via `clinic_id = current_clinic_id`. Users can only see and manipulate visits belonging to their clinic. Cross-clinic access is denied at the database level (not a 403 HTTP response, but a 404 because the row is invisible).

---

## Versioning

All responses include an optimistic lock `version` field. This is used internally for concurrency control but is not relevant to API consumers.

---

**API Version: 1.0**  
**Last Updated: 2026-04-28**  
**Status: Tested & Approved**
