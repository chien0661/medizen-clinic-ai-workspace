# API Specification: Appointments (TASK-008)

**Base URL**: `/api/v1`  
**Authentication**: Bearer JWT (via `Authorization: Bearer <token>`)  
**Tenant**: via `X-Clinic-Code` header (set by TenancyMiddleware)  

---

## Endpoints

### GET /appointments/slots

Get available appointment slots for a date.

**Permission**: `appointment.read`

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| date | YYYY-MM-DD | Yes | Date to query slots |
| duration | integer (10-480) | No (default: 30) | Slot duration in minutes |

**Response 200**:
```json
[
  {
    "start_time": "2026-05-01T09:00:00+00:00",
    "capacity": 2,
    "booked": 1,
    "available": 1
  }
]
```

---

### GET /appointments

List appointments with optional filters.

**Permission**: `appointment.read`

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| status | string | Filter by status |
| patient_id | UUID | Filter by patient |
| assigned_doctor_id | UUID | Filter by doctor |
| skip | integer | Pagination offset |
| limit | integer (1-500) | Page size (default: 50) |

**Response 200**:
```json
{
  "items": [<AppointmentResponse>],
  "total": 42,
  "skip": 0,
  "limit": 50
}
```

---

### POST /appointments

Create a new appointment.

**Permission**: `appointment.write`

**Request Body**:
```json
{
  "patient_id": "uuid",
  "scheduled_at": "2026-05-01T09:00:00+00:00",
  "duration_minutes": 30,
  "assigned_doctor_id": "uuid|null"
}
```

**Validations**:
- `scheduled_at` must be timezone-aware and in the future
- `duration_minutes` must be 10-480
- Slot capacity must have `available > 0`

**Response 201**: `AppointmentResponse`

**Errors**:
- 409: Slot is fully booked

---

### GET /appointments/{appointment_id}

Get appointment detail.

**Permission**: `appointment.read`

**Response 200**: `AppointmentResponse`  
**Response 404**: Appointment not found (or wrong clinic — tenant isolation)

---

### PATCH /appointments/{appointment_id}

Update non-status fields.

**Permission**: `appointment.write`

**Request Body**:
```json
{
  "assigned_doctor_id": "uuid|null",
  "duration_minutes": 30
}
```

**Response 200**: `AppointmentResponse`

---

### POST /appointments/{appointment_id}/confirm

Confirm appointment: `scheduled → confirmed`.

**Permission**: `appointment.write`

**Response 200**: `AppointmentResponse`  
**Response 409**: Invalid status transition

---

### POST /appointments/{appointment_id}/check-in

Check in: `confirmed → checked_in`. Auto-creates a Visit.

**Permission**: `appointment.write`

**Response 200**:
```json
{
  "appointment": <AppointmentResponse>,
  "visit_id": "uuid"
}
```

**Errors**:
- 409: Cannot check-in from current status (must be `confirmed`)

**Side Effects**:
- Creates a new Visit with `status=WAITING`, `appointment_id` linked
- Sets `appointment.visit_id` and `appointment.checked_in_at`

---

### POST /appointments/{appointment_id}/cancel

Cancel appointment with mandatory reason.

**Permission**: `appointment.cancel`

**Request Body**:
```json
{
  "cancel_reason": "Patient cannot attend"
}
```

**Validations**:
- `cancel_reason` minimum 3 characters, not blank

**Response 200**: `AppointmentResponse`  
**Response 409**: Cannot cancel from terminal state (completed, no_show)

---

## Data Models

### AppointmentResponse
```json
{
  "id": "uuid",
  "clinic_id": "uuid",
  "patient_id": "uuid",
  "assigned_doctor_id": "uuid|null",
  "scheduled_at": "datetime",
  "duration_minutes": 30,
  "status": "scheduled|confirmed|checked_in|completed|cancelled|no_show",
  "cancel_reason": "string|null",
  "no_show_at": "datetime|null",
  "checked_in_at": "datetime|null",
  "visit_id": "uuid|null",
  "created_at": "datetime",
  "updated_at": "datetime",
  "created_by": "uuid|null",
  "updated_by": "uuid|null",
  "version": 1
}
```

---

## Error Codes

| HTTP | Code | Description |
|------|------|-------------|
| 400 | BAD_REQUEST | Missing clinic_id header |
| 401 | UNAUTHORIZED | Not authenticated |
| 403 | FORBIDDEN | Missing permission |
| 404 | NOT_FOUND | Appointment not found or wrong tenant |
| 409 | CONFLICT | State transition not allowed or slot full |
| 422 | UNPROCESSABLE_ENTITY | Schema validation failure |
