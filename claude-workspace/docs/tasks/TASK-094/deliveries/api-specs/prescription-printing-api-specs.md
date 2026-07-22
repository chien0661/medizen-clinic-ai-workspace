# API Specification: Prescription Printing & Print Template Management (TASK-094)

**Date:** 2026-07-22  
**Version:** 1.0  
**Status:** Final (tested, approved)  
**Base URL:** `/api/v1`

---

## Changes Summary

This document describes the API endpoints changed or introduced by TASK-094:
1. **Print template read permission** changed from `settings.clinic` to `prescription.print`
2. **LayoutElement schema** now supports `hidden: bool | null` field (no migration — JSONB)
3. **Prescription item** now supports `usage_instruction: string | null` field
4. **DosageForm** now supports `unit: string | null` field

All endpoints use JWT Bearer token authentication (standard; unchanged).

---

## 1. Print Template Endpoints

### 1.1 List Print Templates

**Endpoint:** `GET /print-templates`

**Permission Required:** `prescription.print` *(doctor, nurse, pharmacist, admin)*  
**Changed from:** `settings.clinic` (admin-only)

**Purpose:** Fetch list of available print templates filtered by type and other criteria. This endpoint is called by print modals (doctor, billing, exam form) to find the clinic's configured default template.

**Query Parameters:**

| Name | Type | Required | Description | Example |
|------|------|----------|-------------|---------|
| `template_type` | string (enum) | No | Filter by template type: `prescription`, `exam_form`, `visit_summary` | `prescription` |
| `is_system` | boolean | No | Filter by system templates (true) vs. clinic-created (false) | `false` |
| `is_default` | boolean | No | Filter by default templates only | `true` |
| `page` | integer | No | Pagination (default: 1) | `1` |
| `page_size` | integer | No | Items per page (default: 50) | `20` |

**Request Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9999/api/v1/print-templates?template_type=prescription&is_default=true"
```

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": "tmpl-001-uuid",
      "clinic_id": "clinic-123",
      "name": "Đơn thuốc A4 (mẫu bệnh viện)",
      "template_type": "prescription",
      "is_system": false,
      "is_default": true,
      "paper_size": "A4",
      "orientation": "portrait",
      "layout": [
        {
          "id": "dg-19",
          "kind": "field",
          "field_key": "visit.diagnosis",
          "label": "Chẩn đoán:",
          "align": "left",
          "hidden": false
        },
        {
          "id": "pat-info",
          "kind": "block",
          "block_key": "patient_info",
          "hidden": null
        }
      ],
      "created_at": "2026-07-15T10:00:00Z",
      "updated_at": "2026-07-22T15:30:00Z",
      "created_by": "admin@clinic.com",
      "updated_by": "admin@clinic.com"
    }
  ],
  "pagination": {
    "total": 1,
    "page": 1,
    "page_size": 50,
    "total_pages": 1
  }
}
```

**Response: 403 Forbidden** (user lacks `prescription.print`)
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Permission 'prescription.print' is required for this action.",
    "details": {
      "required_permission": "prescription.print"
    }
  }
}
```

**Response: 401 Unauthorized** (no valid token)
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing authentication token."
  }
}
```

---

### 1.2 Get Print Template by ID

**Endpoint:** `GET /print-templates/{id}`

**Permission Required:** `prescription.print` *(doctor, nurse, pharmacist, admin)*  
**Changed from:** `settings.clinic` (admin-only)

**Purpose:** Fetch a single print template by ID. Called when rendering a print preview or actual print output via `TemplateRenderer`.

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string (UUID) | Yes | Template ID |

**Request Example:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9999/api/v1/print-templates/tmpl-001-uuid"
```

**Response: 200 OK**
```json
{
  "data": {
    "id": "tmpl-001-uuid",
    "clinic_id": "clinic-123",
    "name": "Đơn thuốc A4 (mẫu bệnh viện)",
    "template_type": "prescription",
    "is_system": false,
    "is_default": true,
    "paper_size": "A4",
    "orientation": "portrait",
    "layout": [
      {
        "id": "rx-list-1",
        "kind": "block",
        "block_key": "rx_list",
        "label": "Danh sách thuốc",
        "hidden": false
      },
      {
        "id": "dg-19",
        "kind": "field",
        "field_key": "visit.diagnosis",
        "label": "Chẩn đoán:",
        "align": "left",
        "hidden": false,
        "show_label": true
      }
    ],
    "config": {
      "show_diagnosis": true,
      "show_weight": false
    },
    "created_at": "2026-07-15T10:00:00Z",
    "updated_at": "2026-07-22T15:30:00Z"
  }
}
```

**Response: 404 Not Found**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Print template with ID 'tmpl-001-uuid' not found."
  }
}
```

---

### 1.3 Create Print Template

**Endpoint:** `POST /print-templates`

**Permission Required:** `settings.clinic` *(admin only)*  
**Status:** Unchanged

**Purpose:** Create a new print template (admin interface).

**Request Body:**
```json
{
  "name": "Đơn thuốc A5",
  "template_type": "prescription",
  "paper_size": "A5",
  "orientation": "portrait",
  "is_default": false,
  "layout": [
    {
      "id": "rx-list-1",
      "kind": "block",
      "block_key": "rx_list",
      "hidden": false
    },
    {
      "id": "dg-20",
      "kind": "field",
      "field_key": "visit.diagnosis",
      "label": "Chẩn đoán:",
      "align": "left",
      "hidden": false,
      "show_label": true
    }
  ]
}
```

**Response: 201 Created**
```json
{
  "data": {
    "id": "tmpl-002-uuid",
    "clinic_id": "clinic-123",
    "name": "Đơn thuốc A5",
    "template_type": "prescription",
    "is_system": false,
    "is_default": false,
    "created_at": "2026-07-22T16:00:00Z"
  }
}
```

---

### 1.4 Update Print Template (including hidden field)

**Endpoint:** `PATCH /print-templates/{id}`

**Permission Required:** `settings.clinic` *(admin only)*  
**Status:** Unchanged (but now accepts `hidden` in layout elements)

**Purpose:** Update an existing print template. This is where admins can toggle the `hidden` flag on layout elements to show/hide individual fields.

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string (UUID) | Yes | Template ID to update |

**Request Body:**
```json
{
  "name": "Đơn thuốc A4 v2",
  "is_default": true,
  "layout": [
    {
      "id": "dg-19",
      "kind": "field",
      "field_key": "visit.diagnosis",
      "label": "Chẩn đoán:",
      "align": "left",
      "hidden": true,
      "show_label": true
    },
    {
      "id": "rx-list-1",
      "kind": "block",
      "block_key": "rx_list",
      "hidden": false
    }
  ]
}
```

**Key changes for this task:**
- **New field in LayoutElement:** `hidden: bool | null` (optional, defaults to `null`/`false`)
- **Semantics:** When `hidden === true`, the renderer skips this element entirely (does not render)
- **Storage:** JSONB in PostgreSQL — no migration needed. Existing elements implicitly have `hidden: null` (treated as visible)

**Response: 200 OK**
```json
{
  "data": {
    "id": "tmpl-001-uuid",
    "clinic_id": "clinic-123",
    "name": "Đơn thuốc A4 v2",
    "template_type": "prescription",
    "is_default": true,
    "layout": [
      {
        "id": "dg-19",
        "kind": "field",
        "field_key": "visit.diagnosis",
        "label": "Chẩn đoán:",
        "align": "left",
        "hidden": true,
        "show_label": true
      },
      {
        "id": "rx-list-1",
        "kind": "block",
        "block_key": "rx_list",
        "hidden": false
      }
    ],
    "updated_at": "2026-07-22T16:05:00Z"
  }
}
```

**Response: 403 Forbidden** (insufficient permissions)
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Permission 'settings.clinic' is required for this action."
  }
}
```

---

### 1.5 Delete Print Template

**Endpoint:** `DELETE /print-templates/{id}`

**Permission Required:** `settings.clinic` *(admin only)*  
**Status:** Unchanged

---

### 1.6 Duplicate Print Template

**Endpoint:** `POST /print-templates/{id}/duplicate`

**Permission Required:** `settings.clinic` *(admin only)*  
**Status:** Unchanged

---

## 2. Prescription Endpoints

### 2.1 Create Prescription

**Endpoint:** `POST /prescriptions`

**Permission Required:** `prescription.create`  
**Status:** Updated to support `usage_instruction` field

**Purpose:** Create a new prescription with items (used when doctor prescribes medications).

**Request Body:**
```json
{
  "visit_id": "visit-456-uuid",
  "notes": "Take with food",
  "items": [
    {
      "medicine_id": "med-789-uuid",
      "quantity": 1,
      "unit": "ống",
      "usage_instruction": "Uống sau ăn",
      "note": "Dùng hết liều"
    },
    {
      "medicine_id": "med-790-uuid",
      "quantity": 10,
      "unit": "ml",
      "usage_instruction": "Uống 3 lần/ngày trước ăn",
      "note": ""
    }
  ]
}
```

**New field in PrescriptionItemCreate:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `usage_instruction` | string | No | Structured usage timing (e.g., "Uống trước ăn", "Uống sau ăn", "Trước khi ngủ"). Max 200 chars. Accepts free-text with dropdown suggestions. |

**Response: 201 Created**
```json
{
  "data": {
    "id": "rx-001-uuid",
    "visit_id": "visit-456-uuid",
    "notes": "Take with food",
    "items": [
      {
        "id": "rx-item-1-uuid",
        "medicine_id": "med-789-uuid",
        "medicine_name": "Dexamethasone 4mg inj",
        "quantity": 1,
        "unit": "ống",
        "usage_instruction": "Uống sau ăn",
        "note": "Dùng hết liều",
        "created_at": "2026-07-22T16:00:00Z"
      }
    ],
    "created_at": "2026-07-22T16:00:00Z"
  }
}
```

---

### 2.2 Update Prescription Item

**Endpoint:** `PATCH /prescriptions/{id}/items/{item_id}`

**Permission Required:** `prescription.update`  
**Status:** Updated to support `usage_instruction` field

**Purpose:** Update an existing prescription item (e.g., change quantity, usage, or unit).

**Path Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string (UUID) | Yes | Prescription ID |
| `item_id` | string (UUID) | Yes | Prescription item ID to update |

**Request Body:**
```json
{
  "quantity": 2,
  "unit": "ống",
  "usage_instruction": "Uống trước ăn",
  "note": "Tăng liều"
}
```

**New field in PrescriptionItemUpdate:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `usage_instruction` | string | No | Updated usage instruction. Can be empty to clear. |

**Response: 200 OK**
```json
{
  "data": {
    "id": "rx-item-1-uuid",
    "medicine_id": "med-789-uuid",
    "medicine_name": "Dexamethasone 4mg inj",
    "quantity": 2,
    "unit": "ống",
    "usage_instruction": "Uống trước ăn",
    "note": "Tăng liều",
    "updated_at": "2026-07-22T16:05:00Z"
  }
}
```

---

### 2.3 Get Prescription by ID (with print data)

**Endpoint:** `GET /prescriptions/{id}`

**Permission Required:** `prescription.read`  
**Status:** Unchanged (but now includes `usage_instruction` in item responses)

**Response includes:**
```json
{
  "data": {
    "id": "rx-001-uuid",
    "items": [
      {
        "id": "rx-item-1-uuid",
        "medicine_id": "med-789-uuid",
        "medicine_name": "Dexamethasone 4mg inj",
        "quantity": 1,
        "unit": "ống",
        "usage_instruction": "Uống sau ăn",
        "dosage_form": "injection",
        "dosage_form_unit": "ống"
      }
    ]
  }
}
```

---

## 3. DosageForm Endpoints

### 3.1 List Dosage Forms

**Endpoint:** `GET /dosage-forms`

**Permission Required:** None (public read)  
**Status:** Updated to include `unit` field

**Purpose:** Fetch list of dosage forms (viên, ml, ống, etc.). Used in admin interface and medicine search.

**Query Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `is_system` | boolean | No | Filter by system (true) or clinic-created (false) | `true` |
| `page` | integer | No | Pagination | `1` |

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": "df-001-uuid",
      "name": "Viên",
      "code": "tablet",
      "unit": "viên",
      "is_system": true,
      "clinic_id": null,
      "created_at": "2026-01-01T00:00:00Z"
    },
    {
      "id": "df-002-uuid",
      "name": "Tiêm",
      "code": "injection",
      "unit": "ống",
      "is_system": true,
      "clinic_id": null
    },
    {
      "id": "df-003-uuid",
      "name": "Siro",
      "code": "syrup",
      "unit": "ml",
      "is_system": true
    }
  ],
  "pagination": {
    "total": 7,
    "page": 1
  }
}
```

**New field in DosageForm response:**

| Field | Type | Description |
|-------|------|-------------|
| `unit` | string \| null | Display unit for this dosage form (e.g., "viên", "ml", "ống"). Nullable. Used when resolving the unit for a prescription item. |

---

### 3.2 Get Dosage Form by ID

**Endpoint:** `GET /dosage-forms/{id}`

**Permission Required:** None  
**Status:** Updated to include `unit` field

**Response: 200 OK**
```json
{
  "data": {
    "id": "df-002-uuid",
    "name": "Tiêm",
    "code": "injection",
    "unit": "ống",
    "is_system": true,
    "clinic_id": null,
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

---

### 3.3 Create Dosage Form

**Endpoint:** `POST /dosage-forms`

**Permission Required:** `inventory.manage` *(admin)*  
**Status:** Updated to support `unit` field

**Purpose:** Create a new custom dosage form for the clinic.

**Request Body:**
```json
{
  "name": "Viên nang",
  "code": "capsule",
  "unit": "viên",
  "is_system": false
}
```

**New field in DosageFormCreate:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `unit` | string | No | Display unit (e.g., "viên", "ml"). Max 50 chars. |

**Response: 201 Created**
```json
{
  "data": {
    "id": "df-008-uuid",
    "name": "Viên nang",
    "code": "capsule",
    "unit": "viên",
    "is_system": false,
    "clinic_id": "clinic-123",
    "created_at": "2026-07-22T16:10:00Z"
  }
}
```

---

### 3.4 Update Dosage Form

**Endpoint:** `PATCH /dosage-forms/{id}`

**Permission Required:** `inventory.manage` *(admin)*  
**Status:** Updated to support `unit` field

**Purpose:** Update an existing dosage form.

**Request Body:**
```json
{
  "unit": "ml"
}
```

**Response: 200 OK**
```json
{
  "data": {
    "id": "df-001-uuid",
    "name": "Siro",
    "code": "syrup",
    "unit": "ml",
    "updated_at": "2026-07-22T16:15:00Z"
  }
}
```

---

## 4. Medicine Search Endpoint (for prescribing)

### 4.1 Search Medicines

**Endpoint:** `GET /medicines/search`

**Permission Required:** `prescription.create`  
**Status:** Updated to include `dosage_form_unit` in response

**Purpose:** Search medicines by name/code for the prescribing UI dropdown. This endpoint now includes resolved dosage-form unit for pre-filling the unit field when a medicine is selected.

**Query Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `q` | string | Yes | Search term (medicine name or code) | `dexamethasone` |
| `limit` | integer | No | Max results (default: 10) | `20` |

**Response: 200 OK**
```json
{
  "data": [
    {
      "id": "med-789-uuid",
      "name": "Dexamethasone 4mg Inj",
      "code": "DEX4MG",
      "base_unit": "ống",
      "dosage_form": "injection",
      "dosage_form_id": "df-002-uuid",
      "dosage_form_unit": "ống",
      "strength": "4mg",
      "route": "IV",
      "created_at": "2026-06-01T00:00:00Z"
    },
    {
      "id": "med-790-uuid",
      "name": "Cough Syrup 5mg/5ml",
      "code": "COUGH5",
      "base_unit": "ml",
      "dosage_form": "syrup",
      "dosage_form_id": "df-003-uuid",
      "dosage_form_unit": "ml",
      "strength": "5mg/5ml",
      "route": "PO",
      "created_at": "2026-06-02T00:00:00Z"
    }
  ]
}
```

**New/Changed field in Medicine response:**

| Field | Type | Description |
|-------|------|-------------|
| `dosage_form_unit` | string \| null | **NEW** — resolved unit from the medicine's dosage form. Calculated as: <br/>1. If `dosage_form_id` exists (FK from TASK-093), resolve via `DosageForm.unit` <br/>2. Else match `dosage_form` (free-text) against system DosageForm catalog by name/code <br/>3. Fallback: `base_unit` <br/>4. Final fallback: `null` <br/>Frontend uses this to pre-fill the unit field when prescribing. |

---

## 5. Backward Compatibility

### Old API consumers (no changes needed)

- **Prescription item without `usage_instruction`:** Still works. Field is optional; omit it or pass `null`.
- **Print templates with existing `hidden: null` / absent:** Still work. Implicit `hidden: null` is treated as visible (no behavior change for existing templates).
- **DosageForm without `unit`:** Still works. If `unit` is `null`, fallback to `medicine.base_unit`.
- **Existing code calling `GET /print-templates` with `settings.clinic` permission:** **Will fail (403)** — this is an intentional breaking change to fix the permission model. Callers must use `prescription.print` instead.
  - **Mitigation:** Apply the new RBAC permission to relevant roles (already done in the implementation).

---

## 6. Error Handling

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful GET, PATCH, DELETE |
| 201 | Created | Successful POST (resource created) |
| 400 | Bad Request | Invalid JSON, missing required fields, validation failed |
| 401 | Unauthorized | No/invalid JWT token |
| 403 | Forbidden | Insufficient permissions for the role |
| 404 | Not Found | Resource ID doesn't exist |
| 409 | Conflict | Duplicate key, business logic violation |
| 500 | Internal Server Error | Unexpected server error |

### Error Response Format (all endpoints)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "field_errors": [
        {
          "field": "items[0].usage_instruction",
          "message": "Must be <= 200 characters"
        }
      ]
    }
  }
}
```

---

## 7. Field Validation

### LayoutElement.hidden

- **Type:** `boolean | null`
- **Default:** `null` (treated as visible)
- **Rules:** None (nullable, no validation)

### PrescriptionItem.usage_instruction

- **Type:** `string | null`
- **Max length:** 200 characters
- **Required:** No
- **Validation:** Server rejects if `len(usage_instruction) > 200`
- **Frontend validation:** Input `maxLength="200"`

### DosageForm.unit

- **Type:** `string | null`
- **Max length:** 50 characters
- **Required:** No
- **Rules:** Text label (e.g., "viên", "ml", "ống")

---

## 8. Example: Complete Flow (Doctor Prescribes with New Features)

### Step 1: Doctor searches for a medicine
```bash
GET /api/v1/medicines/search?q=dexamethasone&limit=10
→ Returns medicine with dosage_form_unit="ống" (resolved from DosageForm.unit)
```

### Step 2: Doctor selects medicine and sets usage
- Frontend pre-fills unit: `"ống"` (from `dosage_form_unit`)
- Doctor selects/types usage: `"Uống sau ăn"`
- Doctor sets quantity: `1`

### Step 3: Doctor saves prescription
```bash
POST /api/v1/prescriptions
{
  "visit_id": "visit-456",
  "items": [
    {
      "medicine_id": "med-789",
      "quantity": 1,
      "unit": "ống",
      "usage_instruction": "Uống sau ăn"
    }
  ]
}
→ 201 Created with full prescription object
```

### Step 4: Doctor clicks "In đơn thuốc" (Print)
```bash
GET /api/v1/print-templates?template_type=prescription
→ Returns list with is_default=true custom template

GET /api/v1/print-templates/{id}
→ Returns template layout with hidden fields filtered out

Frontend renders via TemplateRenderer:
- Diagnosis field from visit.diagnosis (not notes)
- Usage field: "Uống sau ăn" (from usage_instruction)
- Unit: "ống" (resolved)
```

### Step 5: Print output
- Custom template A4 format
- Diagnosis: "Viêm phế quản"
- Medicine: "Dexamethasone 4mg inj · 1 ống · Uống sau ăn"
- Hidden fields omitted from layout

---

## 9. Database Schema Changes (reference for devops)

### Migration 0061: Add usage_instruction to prescription_item
```sql
ALTER TABLE prescription_item 
ADD COLUMN usage_instruction VARCHAR(200) NULL;
```

### Migration 0062: Add unit to dosage_form + seed
```sql
ALTER TABLE dosage_form 
ADD COLUMN unit VARCHAR(50) NULL;

UPDATE dosage_form SET unit = 'viên' 
WHERE is_system = true AND code IN ('tablet', 'capsule');
UPDATE dosage_form SET unit = 'ml' 
WHERE is_system = true AND code = 'syrup';
UPDATE dosage_form SET unit = 'ống' 
WHERE is_system = true AND code = 'injection';
UPDATE dosage_form SET unit = 'tuýp' 
WHERE is_system = true AND code = 'cream';
UPDATE dosage_form SET unit = 'lọ' 
WHERE is_system = true AND code = 'drops';
UPDATE dosage_form SET unit = 'bình' 
WHERE is_system = true AND code = 'inhaler';
```

---

## 10. Testing Checklist

- [x] `GET /print-templates` returns 200 for `doctor` role (was 403)
- [x] `GET /print-templates/{id}` returns layout with `hidden` field persisted (PATCH→GET round-trip)
- [x] `POST /prescriptions` with `usage_instruction` saves correctly
- [x] `PATCH /prescriptions/{id}/items/{item_id}` with `usage_instruction` persists
- [x] `GET /medicines/search` includes `dosage_form_unit` in response (e.g., injection → "ống")
- [x] `GET /dosage-forms` includes `unit` field
- [x] `PATCH /dosage-forms/{id}` with `unit` updates correctly
- [x] Permission enforcement: doctor can read templates, admin can write templates
- [x] Backward compat: old code without new fields still works

All verified in live E2E testing (test report, Iteration 2, 2026-07-22).

---

**Document Status:** ✅ Final & Tested (2026-07-22)

