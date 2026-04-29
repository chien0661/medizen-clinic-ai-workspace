# TASK-011 Prescription & Medicine Search — API Contract

> **Stability:** Production-ready. TASK-019 (FE Doctor) and TASK-020 (FE Pharmacy) may stub against this contract before merge.
>
> **Base URL:** `/api/v1`
> **Auth:** JWT Bearer in `Authorization` header
> **Tenant:** `X-Clinic-Code` header (set by TenancyMiddleware, resolved to `clinic_id`)

---

## Authentication

All endpoints require a valid JWT token. Token is obtained via:

```
POST /api/v1/auth/login
{ "clinic_code": "CLINIC001", "username": "doctor1", "password": "..." }
→ { "data": { "access_token": "<jwt>", "refresh_token": "<jwt>" } }
```

---

## Medicine Search

### GET /api/v1/medicines/search

Search medicine catalog with optional real-time stock indicator.

**Permission required:** `medicine.read`

**Query Parameters:**

| Param | Type | Required | Description |
|---|---|---|---|
| `q` | string | YES | Search term (min 1 char). Matched against name, generic_name, brand_name, code (ILIKE) |
| `with_stock` | boolean | NO (default: true) | If true, annotate results with stock info from inventory |
| `limit` | integer | NO (default: 20, max: 100) | Max results |

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "clinic_id": "uuid",
      "code": "PAR500",
      "name": "Paracetamol 500mg",
      "generic_name": "Acetaminophen",
      "brand_name": "Tylenol",
      "dosage_form": "tablet",
      "strength": "500mg",
      "base_unit": "viên",
      "is_in_house": true,
      "is_active": true,
      "in_stock": true,
      "available": "120",
      "batches_count": 2
    }
  ],
  "total": 5,
  "query": "paracetamol",
  "with_stock": true
}
```

**Notes for FE:**
- `in_stock: true` → show "In Stock" badge; `false` → "Out of Stock"
- `available` is a decimal string (Postgres Numeric) — parse as float
- When `with_stock=false`, `available=0` and `in_stock=false` regardless of actual stock
- After selecting a medicine, call `POST /prescriptions/{id}/items` with the `medicine_id` — service auto-suggests `dispense_source` based on real-time stock

---

## Prescriptions

### POST /api/v1/visits/{visit_id}/prescriptions

Create a new prescription for a visit. Items can be included inline or added later.

**Permission required:** `prescription.write`

**Path Params:**
- `visit_id` (UUID): The visit to prescribe for

**Request Body:**
```json
{
  "doctor_id": "uuid",
  "notes": "Patient complains of fever",
  "items": [
    {
      "medicine_id": "uuid-or-null",
      "medicine_name": "Paracetamol 500mg",
      "dosage": "1 viên × 3 lần / ngày",
      "quantity": 30,
      "unit": "viên",
      "dispense_source": "in_house",
      "unit_price": null,
      "sort_order": 0
    }
  ]
}
```

**Item fields:**
- `medicine_id`: UUID from catalog, or `null` for external free-text items
- `medicine_name`: Required always. For in_house items with `medicine_id`, this is auto-filled from catalog if blank
- `dispense_source`: `"in_house"` | `"external"` | `null` (null = auto-suggest from stock)
- When `dispense_source` is omitted/null, service auto-suggests:
  - `"in_house"` if available stock ≥ quantity
  - `"external"` if available < quantity (with warning)

**Response 201:**
```json
{
  "id": "uuid",
  "clinic_id": "uuid",
  "visit_id": "uuid",
  "doctor_id": "uuid",
  "dispense_type": "mixed",
  "status": "draft",
  "notes": "Patient complains of fever",
  "prescribed_at": "2026-04-27T10:30:00+07:00",
  "cancelled_at": null,
  "cancel_reason": null,
  "items": [
    {
      "id": "uuid",
      "clinic_id": "uuid",
      "prescription_id": "uuid",
      "medicine_id": "uuid",
      "medicine_name": "Paracetamol 500mg",
      "dosage": "1 viên × 3 lần / ngày",
      "quantity": "30",
      "unit": "viên",
      "dispense_source": "in_house",
      "in_house_status": "reserved",
      "unit_price": null,
      "sort_order": 0,
      "is_deleted": false,
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "is_deleted": false,
  "created_at": "...",
  "updated_at": "..."
}
```

**dispense_type derivation:**
- All items `in_house` → `"in_house"`
- All items `external` → `"external"`
- Mix → `"mixed"`

---

### GET /api/v1/prescriptions/{prescription_id}

Get prescription detail with all active items.

**Permission required:** `prescription.read`

**Response 200:** Same structure as Create response above.

**Error 404:** Prescription not found or belongs to different clinic.

---

### PATCH /api/v1/prescriptions/{prescription_id}

Update prescription header fields (notes, dispense_type override).

**Permission required:** `prescription.write`

**Request Body (all fields optional):**
```json
{
  "notes": "Updated clinical notes",
  "dispense_type": "mixed"
}
```

**Restrictions:**
- Cannot update if status is `"dispensed"` or `"cancelled"` → 400

**Response 200:** Updated prescription.

---

### POST /api/v1/prescriptions/{prescription_id}/items

Add a medicine item to an existing prescription.

**Permission required:** `prescription.write`

**Request Body:**
```json
{
  "medicine_id": "uuid-or-null",
  "medicine_name": "Vitamin C",
  "dosage": "1 viên / ngày",
  "quantity": 30,
  "unit": "viên",
  "dispense_source": null,
  "unit_price": null,
  "sort_order": 1
}
```

**Behavior:**
1. If `dispense_source` is null and `medicine_id` is provided → auto-suggest from stock
2. If suggested source is `"external"` due to low stock → service still creates the item; caller is informed via response (check `in_house_status`)
3. If `medicine_id` is null → always `"external"` regardless of dispense_source
4. If `dispense_source = "in_house"` and `medicine_id` is provided → reserve stock immediately (FEFO)

**Response 201:**
```json
{
  "id": "uuid",
  "clinic_id": "uuid",
  "prescription_id": "uuid",
  "medicine_id": "uuid",
  "medicine_name": "Paracetamol 500mg",
  "dosage": "1 viên × 3 lần / ngày",
  "quantity": "30",
  "unit": "viên",
  "dispense_source": "in_house",
  "in_house_status": "reserved",
  "unit_price": null,
  "sort_order": 1,
  "is_deleted": false,
  "created_at": "...",
  "updated_at": "..."
}
```

**Error 409 (InsufficientStockError):** When trying to reserve more than available. Body:
```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Insufficient stock for medicine ...: needed=30, available=5",
    "details": {
      "medicine_id": "uuid",
      "needed": "30",
      "available": "5"
    }
  }
}
```

---

### PATCH /api/v1/prescription-items/{item_id}

Update a single prescription item. Smart re-reservation if quantity or source changes.

**Permission required:** `prescription.write`

**Request Body (all optional):**
```json
{
  "medicine_name": "Updated name",
  "dosage": "2 viên × 3 lần / ngày",
  "quantity": 20,
  "unit": "viên",
  "dispense_source": "external",
  "unit_price": 5000,
  "sort_order": 2
}
```

**Behavior on source/quantity change:**
- If item was `in_house` and source or qty changes → old reservation released first
- If new source is `in_house` → new reservation created
- If switching from `in_house` → `external` → reservation released, `in_house_status` → null

**Response 200:** Updated `PrescriptionItemResponse`.

---

### DELETE /api/v1/prescription-items/{item_id}

Soft-delete a prescription item. Releases any in_house reservation.

**Permission required:** `prescription.write`

**Response 204:** No content.

**Errors:**
- 400 if prescription status is `dispensed` or `cancelled`

---

### POST /api/v1/prescriptions/{prescription_id}/submit

Submit prescription: `draft` → `pending`.

**Permission required:** `prescription.write`

**Validates:**
- At least one active item
- All `in_house` items have `in_house_status = "reserved"`

**Response 200:** Updated prescription with `status: "pending"`.

**Errors:**
- 400 if status is not `draft`
- 400 if no items
- 400 if any in_house item not reserved

---

### POST /api/v1/prescriptions/{prescription_id}/cancel

Cancel prescription. Releases all in_house reservations.

**Permission required:** `prescription.cancel`

**Request Body:**
```json
{
  "reason": "Patient cancelled appointment"
}
```

**Response 200:** Updated prescription with `status: "cancelled"`, `cancelled_at`, `cancel_reason`.

**Errors:**
- 409 if status is `"dispensed"` — cannot cancel dispensed prescription
- 400 if already `"cancelled"`

---

### GET /api/v1/prescriptions/{prescription_id}/print

Generate prescription HTML for printing.

**Permission required:** `prescription.print`

**Query Params:**

| Param | Default | Description |
|---|---|---|
| `mode` | `"all"` | `"all"` = all items; `"external_only"` = only mua ngoài; `"ask"` = return choice prompt |

**Response 200:**

For `mode="all"` or `mode="external_only"`:
```json
{
  "prescription_id": "uuid",
  "mode": "all",
  "content_type": "text/html",
  "html": "<!DOCTYPE html>...<h3>ĐƠN THUỐC</h3>...",
  "choice_required": false,
  "options": []
}
```

For `mode="ask"`:
```json
{
  "prescription_id": "uuid",
  "mode": "ask",
  "content_type": "text/html",
  "html": null,
  "choice_required": true,
  "options": ["all", "external_only"]
}
```

**FE guidance:** When `choice_required=true`, show a dialog asking which print mode. Then re-call with explicit mode.

---

## Status Flows

```
PRESCRIPTION STATUS
  draft ──submit──► pending ──(pharmacy)──► dispensed
  draft ──cancel──► cancelled
  pending ──cancel──► cancelled  (releases reservations)
  dispensed → cannot cancel (409)

PRESCRIPTION ITEM IN_HOUSE_STATUS
  reserved (after add_item with in_house)
  dispensed (after pharmacy dispenses)
  released (after cancel or switch to external)
```

---

## dispense_type Values

| Value | Meaning |
|---|---|
| `in_house` | All items dispensed from clinic inventory |
| `external` | All items prescribed for external purchase |
| `mixed` | Mix of in_house and external items |

---

## Common Error Codes

| HTTP Status | Error Code | Description |
|---|---|---|
| 400 | `BUSINESS_RULE_VIOLATION` | Status transition not allowed |
| 401 | — | Not authenticated |
| 403 | `FORBIDDEN` | Missing required permission |
| 404 | `NOT_FOUND` | Prescription or item not found / wrong tenant |
| 409 | `CONFLICT` | Dispensed prescription cannot cancel; insufficient stock |
| 422 | — | Request body validation error (Pydantic) |

---

## Pharmacy Integration (TASK-020)

For TASK-020 (Pharmacy FE), the flow after prescription `pending`:

1. Pharmacist reads `GET /prescriptions/{id}` to see `items` with `dispense_source` and `in_house_status`
2. For `in_house` items with `in_house_status="reserved"`, call pharmacy dispense endpoint (TASK-012):
   - `POST /api/v1/pharmacy/dispense` — marks reservation as dispensed + decrements batch.actual_quantity
3. For `external` items — no inventory action needed
4. After all in_house items dispensed, prescription status becomes `dispensed` (via pharmacy service)

---

## FE Stub Checklist (TASK-019 / TASK-020)

TASK-019 (Doctor FE) can stub on:
- `GET /medicines/search` — for medicine picker autocomplete
- `POST /visits/{id}/prescriptions` — create prescription
- `POST /prescriptions/{id}/items` — add items
- `POST /prescriptions/{id}/submit` — submit
- `GET /prescriptions/{id}/print` — print

TASK-020 (Pharmacy FE) can stub on:
- `GET /prescriptions/{id}` — view prescription items
- `POST /api/v1/pharmacy/dispense` (TASK-012 endpoint)
- `POST /prescriptions/{id}/cancel` — cancel flow

---

_Generated by TASK-011 Implementation Agent. Last updated: 2026-04-27._
