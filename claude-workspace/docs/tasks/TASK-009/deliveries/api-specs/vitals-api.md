# Vitals API Specification

**Task**: TASK-009  
**Base URL**: `/api/v1`  
**Auth**: Bearer JWT required on all endpoints  

---

## Endpoints

### 1. GET /vitals/definitions
List all vital field definitions for the current clinic (including inactive, excluding soft-deleted).

**Permission**: `vital.read`

**Response 200**:
```json
[
  {
    "id": "uuid",
    "clinic_id": "uuid",
    "key": "systolic_bp",
    "label": "Systolic BP",
    "data_type": "integer",
    "unit": "mmHg",
    "min_value": 60,
    "max_value": 250,
    "warning_min": 90,
    "warning_max": 140,
    "decimal_places": null,
    "options": null,
    "is_required": true,
    "sort_order": 1,
    "group_name": "Sinh hiệu",
    "placeholder": null,
    "help_text": null,
    "is_active": true,
    "is_system": false,
    "created_at": "2026-04-27T00:00:00Z",
    "updated_at": "2026-04-27T00:00:00Z"
  }
]
```

---

### 2. POST /vitals/definitions
Create a new vital field definition for the clinic. Triggers a new schema version.

**Permission**: `vital.manage` (admin only)

**Request**:
```json
{
  "key": "systolic_bp",
  "label": "Systolic BP",
  "data_type": "integer",
  "unit": "mmHg",
  "min_value": 60,
  "max_value": 250,
  "warning_min": 90,
  "warning_max": 140,
  "is_required": true,
  "sort_order": 1,
  "group_name": "Sinh hiệu"
}
```

**Response 201**: VitalFieldDefinitionResponse

**Error 422**: Invalid data_type or missing options for select type

---

### 3. PATCH /vitals/definitions/{definition_id}
Update a vital field definition. Mutable changes trigger new schema version.

**Permission**: `vital.manage`

**Request** (all fields optional):
```json
{
  "label": "New Label",
  "is_required": true,
  "unit": "kg"
}
```

**Response 200**: VitalFieldDefinitionResponse

**Error 400**:
- `"Cannot rename key, create new field instead"` — if key is changed
- `"Cannot change data_type, create new field instead"` — if data_type is changed

---

### 4. DELETE /vitals/definitions/{definition_id}
Soft-delete a vital field definition. Triggers new schema version.

**Permission**: `vital.manage`

**Response 204**: No Content

---

### 5. GET /vitals/definitions/version/{version_number}
Get a historical schema version snapshot.

**Permission**: `vital.read`

**Response 200**:
```json
{
  "id": "uuid",
  "clinic_id": "uuid",
  "version_number": 3,
  "definitions_snapshot": [...],
  "change_summary": "Updated field 'pulse'",
  "created_at": "2026-04-27T00:00:00Z",
  "created_by": "uuid"
}
```

**Error 404**: Version not found

---

### 6. POST /visits/{visit_id}/vitals
Record vital measurements for a visit. Runtime validates against current active definitions.

**Permission**: `vital.write` (nurse, doctor, admin)

**Request**:
```json
{
  "values": {
    "systolic_bp": 120,
    "diastolic_bp": 80
  },
  "notes": "Taken before consultation",
  "is_primary": false
}
```

**Response 201**: VisitVitalsResponse

**Errors**:
- `400`: No active definitions for clinic
- `422`: Validation errors — list of `{field, code, message}` objects
  - `REQUIRED` — required field missing
  - `UNKNOWN` — key not in active definitions
  - `INVALID` — type mismatch or out of range

---

### 7. GET /visits/{visit_id}/vitals
Get all vitals records for a visit, ordered by recorded_at.

**Permission**: `vital.read`

**Response 200**:
```json
[
  {
    "id": "uuid",
    "clinic_id": "uuid",
    "visit_id": "uuid",
    "schema_version": 3,
    "values": {"systolic_bp": 120, "diastolic_bp": 80},
    "notes": null,
    "is_primary": true,
    "recorded_by": "uuid",
    "recorded_at": "2026-04-27T10:00:00Z",
    "created_at": "2026-04-27T10:00:00Z",
    "updated_at": "2026-04-27T10:00:00Z"
  }
]
```

---

## Data Types for Field Definitions

| data_type | Description | Validation |
|-----------|-------------|------------|
| `integer` | Whole number | int conversion, min/max range |
| `number` | Decimal number | Decimal conversion, min/max range |
| `text` | Free string | str conversion |
| `boolean` | True/False | bool/0/1/"true"/"false" accepted |
| `select` | Enum from options list | Must be in options list |
