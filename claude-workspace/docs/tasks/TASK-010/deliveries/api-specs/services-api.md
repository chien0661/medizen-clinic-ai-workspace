# TASK-010: Services API Specification

Base URL: `/api/v1`
Auth: Bearer JWT (set by TenancyMiddleware)

## Service Catalog

### GET /services
List catalog items for the current clinic.

**Permission**: `service.read`

**Query params**:
- `category` (optional): filter by category string
- `is_active` (optional): filter by active/inactive
- `skip` (default 0): pagination offset
- `limit` (default 50, max 500): page size

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "clinic_id": "uuid",
      "code": "XRAY01",
      "name": "X-Ray Chest",
      "category": "radiology",
      "description": null,
      "default_price": "150.00",
      "default_duration_minutes": 30,
      "is_active": true,
      "is_deleted": false,
      "created_at": "2026-04-27T10:00:00Z",
      "updated_at": "2026-04-27T10:00:00Z",
      "created_by": "uuid",
      "updated_by": null,
      "version": 1
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

---

### POST /services
Create a new service catalog item.

**Permission**: `service.manage`

**Body**:
```json
{
  "code": "XRAY01",          // letters+digits, 2-20 chars, uppercased
  "name": "X-Ray Chest",
  "default_price": "150.00",
  "category": "radiology",   // optional
  "description": "...",      // optional
  "default_duration_minutes": 30,  // optional, >= 1
  "is_active": true          // default: true
}
```

**Response 201**: ServiceResponse

**Errors**:
- `409 Conflict`: duplicate code for this clinic (active records only)
- `422 Unprocessable`: invalid code format

---

### GET /services/{service_id}
Get a single service catalog item.

**Permission**: `service.read`

**Response 200**: ServiceResponse  
**Errors**: `404 Not Found`

---

### PATCH /services/{service_id}
Update service catalog fields.

**Permission**: `service.manage`

**Body** (all fields optional):
```json
{
  "name": "Updated Name",
  "default_price": "175.00",
  "is_active": false
}
```

**Response 200**: ServiceResponse

---

### DELETE /services/{service_id}
Soft-delete a service catalog item.

**Permission**: `service.manage`

**Response 200**: ServiceResponse (with `is_deleted: true`)

---

## Visit Services (Performed Services)

### POST /visits/{visit_id}/services
Add a service to a visit. Snapshots `unit_price` from catalog's `default_price`.

**Permission**: `service.write`

**Body**:
```json
{
  "service_id": "uuid",
  "quantity": 1,
  "unit_price_override": null,    // optional; requires service.price_override perm
  "discount_amount": null,        // optional; if > 0, discount_reason required
  "discount_reason": null,        // required if discount_amount > 0
  "notes": null,
  "performed_by_user_id": null
}
```

**Response 201**: VisitServiceResponse

**Errors**:
- `403 Forbidden`: `unit_price_override` set but no `service.price_override` perm
- `422`: discount_amount > 0 but discount_reason missing

---

### GET /visits/{visit_id}/services
List services for a visit.

**Permission**: `service.read`

**Response 200**: VisitServiceListResponse

---

### PATCH /visit-services/{vs_id}
Update visit service status or notes.

**Permission**: `service.write`

**Body**:
```json
{
  "status": "in_progress",           // optional; triggers state machine
  "notes": "Updated notes",          // optional
  "performed_by_user_id": "uuid"    // optional
}
```

**State machine**: `ordered → in_progress → completed`; `ordered/in_progress → cancelled`

**Response 200**: VisitServiceResponse  
**Errors**: `409 Conflict` on invalid transition

---

### POST /visit-services/{vs_id}/cancel
Cancel a visit service.

**Permission**: `service.write`

**Body**:
```json
{
  "reason": "Patient no longer needs this"  // optional
}
```

**Response 200**: VisitServiceResponse  
**Errors**: `409 Conflict` if status is `completed` (AC #4)

---

### PATCH /visit-services/{vs_id}/price
Override unit price. Audit-logged.

**Permission**: `service.price_override`

**Body**:
```json
{
  "unit_price": "75.00",
  "reason": "Insurance negotiated rate"  // required, min 3 chars
}
```

**Response 200**: VisitServiceResponse

---

## Status Machine

```
ordered → in_progress → completed (terminal)
ordered → cancelled (terminal)
in_progress → cancelled (terminal)
completed → (terminal, cannot cancel)
```
