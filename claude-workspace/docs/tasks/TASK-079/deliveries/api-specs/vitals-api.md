# API Specification: Vitals — Dynamic Form & Structured Status

**Task:** TASK-079  
**Date:** 2026-06-16  
**Status:** APPROVED + ALL PASS (48 BE unit/integration tests, 12 FE tests)  
**Affected Endpoints:**
- `GET /api/v1/vitals/definitions` (existing, data source for dynamic form)
- `POST /api/v1/visits/{id}/vitals` (modified — new field_status + field_notes)
- `GET /api/v1/visits/{id}/vitals` (modified — returns field_status + field_notes)

---

## Glossary

| Term | Meaning |
|------|---------|
| **Vital Field Definition** | Configuration of one vital sign (key, label, unit, min/max, warning_min/max, data_type, options, group_name, sort_order, is_required) |
| **field_status** | JSONB map `{key: "normal" \| "abnormal"}` — structured status per vital field |
| **field_notes** | JSONB map `{key: note_text}` — per-field annotations |
| **vital_schema_version** | Snapshot of active schema version at time of entry — helps identify which definition was used |
| **Annotation** | Combination of field_status + field_notes (validation term) |

---

## 1. GET /api/v1/vitals/definitions

**Purpose:** Fetch all active vital field definitions. FE uses this to render the entry form dynamically.

### Request

```http
GET /api/v1/vitals/definitions
Authorization: Bearer {token}
```

**Query Parameters:** (optional)
- `clinic_id` (integer, optional) — filter by clinic (if presets per-specialty)
- `schema_version` (integer, optional) — get specific version (default: current)

### Response

**HTTP 200 OK**

```json
{
  "data": [
    {
      "id": 1,
      "key": "heart_rate",
      "label": "Nhịp tim",
      "unit": "lần/phút",
      "data_type": "number",
      "min_value": 50,
      "max_value": 120,
      "warning_min": 60,
      "warning_max": 100,
      "is_required": true,
      "group_name": "Tuyến tim mạch",
      "sort_order": 1,
      "options": null,
      "help_text": "Nhịp tim bình thường 60-100 lần/phút",
      "placeholder": "Nhập số lần trên phút"
    },
    {
      "id": 2,
      "key": "bp",
      "label": "Huyết áp",
      "unit": "mmHg",
      "data_type": "text",
      "min_value": null,
      "max_value": null,
      "warning_min": null,
      "warning_max": null,
      "is_required": true,
      "group_name": "Tuyến tim mạch",
      "sort_order": 2,
      "options": null,
      "help_text": "Nhập dạng SBP/DBP (ví dụ: 120/80)",
      "placeholder": "VD: 120/80"
    },
    {
      "id": 3,
      "key": "temperature",
      "label": "Nhiệt độ",
      "unit": "°C",
      "data_type": "number",
      "min_value": 36.0,
      "max_value": 37.5,
      "warning_min": 36.0,
      "warning_max": 37.5,
      "is_required": true,
      "group_name": "Chỉ số toàn thân",
      "sort_order": 3,
      "options": null,
      "help_text": "Nhiệt độ bình thường 36.0-37.5°C",
      "placeholder": "Nhập nhiệt độ"
    },
    {
      "id": 4,
      "key": "bmi_category",
      "label": "BMI",
      "unit": "",
      "data_type": "select",
      "min_value": null,
      "max_value": null,
      "warning_min": null,
      "warning_max": null,
      "is_required": false,
      "group_name": "Chỉ số cân nặng",
      "sort_order": 5,
      "options": [
        { "value": "underweight", "label": "Thiếu cân" },
        { "value": "normal", "label": "Bình thường" },
        { "value": "overweight", "label": "Thừa cân" },
        { "value": "obese", "label": "Béo phì" }
      ],
      "help_text": "BMI được tính tự động nếu có height + weight",
      "placeholder": null
    }
  ],
  "total": 8
}
```

**Response Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `key` | string | Unique identifier for the vital (ví dụ: `heart_rate`, `bp`, `temperature`, `height`, `weight`) |
| `label` | string | Display name (Vietnamese) |
| `unit` | string | Unit of measurement (ví dụ: `lần/phút`, `mmHg`, `°C`, `cm`, `kg`) |
| `data_type` | string | Input type: `number`, `integer`, `text`, `boolean`, `select` |
| `min_value` | number \| null | Hard minimum (normal range) |
| `max_value` | number \| null | Hard maximum (normal range) |
| `warning_min` | number \| null | Soft warning minimum (preferred band) |
| `warning_max` | number \| null | Soft warning maximum (preferred band) |
| `is_required` | boolean | Required to fill in form |
| `group_name` | string | Grouping name for form rendering |
| `sort_order` | integer | Display order within group |
| `options` | array \| null | For `data_type=select`: array of `{value, label}` objects |
| `help_text` | string | Help/hint for user |
| `placeholder` | string | Input placeholder |

**Error Responses:**

| HTTP Status | Scenario |
|-------------|----------|
| 401 | Unauthorized (invalid/missing token) |
| 404 | No definitions configured |
| 500 | Server error |

---

## 2. POST /api/v1/visits/{id}/vitals

**Purpose:** Create a new vital entry with structured status (field_status) and per-field notes (field_notes).

### Request

```http
POST /api/v1/visits/{id}/vitals
Authorization: Bearer {token}
Content-Type: application/json
```

**URL Parameters:**
- `id` (integer, required) — visit_id

**Request Body:**

```json
{
  "values": {
    "heart_rate": 88,
    "bp": "130/85",
    "temperature": 36.8,
    "height": 170,
    "weight": 65
  },
  "field_status": {
    "heart_rate": "normal",
    "bp": "abnormal",
    "temperature": "normal"
  },
  "field_notes": {
    "bp": "Huyết áp cao, tái đo sau 5 phút"
  },
  "notes": "(optional) Ghi chú chung thêm"
}
```

**Request Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `values` | object | Yes | Map of `{key: value}` — vital measurements. Value type depends on `data_type` in definition. |
| `field_status` | object | No | Map of `{key: "normal" \| "abnormal"}` — per-field status (default: `{}`) |
| `field_notes` | object | No | Map of `{key: note_text}` — per-field annotations (default: `{}`) |
| `notes` | string | No | General/legacy notes field (backward compat) |

### Response

**HTTP 201 Created**

```json
{
  "id": 1001,
  "visit_id": 555,
  "values": {
    "heart_rate": 88,
    "bp": "130/85",
    "temperature": 36.8,
    "height": 170,
    "weight": 65
  },
  "field_status": {
    "heart_rate": "normal",
    "bp": "abnormal",
    "temperature": "normal"
  },
  "field_notes": {
    "bp": "Huyết áp cao, tái đo sau 5 phút"
  },
  "vital_schema_version": 3,
  "notes": null,
  "is_primary": true,
  "created_at": "2026-06-16T10:30:00Z",
  "created_by": "doctor_001"
}
```

**Response Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique vital entry ID |
| `visit_id` | integer | Associated visit_id |
| `values` | object | Echo of submitted values |
| `field_status` | object | Echo of submitted field_status |
| `field_notes` | object | Echo of submitted field_notes |
| `vital_schema_version` | integer | Snapshot of schema version at time of entry |
| `is_primary` | boolean | Whether this is the primary/latest entry for visit |
| `created_at` | string (ISO 8601) | Timestamp |
| `created_by` | string | User ID who created |

### Validation & Error Responses

#### 1. Invalid `values` (pre-existing validator)

**HTTP 422 Unprocessable Entity**

```json
{
  "detail": [
    {
      "field": "values",
      "code": "REQUIRED",
      "message": "Chỉ số 'heart_rate' là bắt buộc"
    },
    {
      "field": "values",
      "code": "TYPE_MISMATCH",
      "message": "Chỉ số 'heart_rate' phải là kiểu number, nhận được: string"
    },
    {
      "field": "values",
      "code": "OUT_OF_RANGE",
      "message": "Chỉ số 'heart_rate'=200 vượt quá max=120"
    }
  ]
}
```

#### 2. Invalid `field_status` (NEW in TASK-079)

**HTTP 422 Unprocessable Entity**

```json
{
  "detail": [
    {
      "field": "field_status",
      "code": "INVALID_STATUS",
      "message": "Status phải là 'normal' hoặc 'abnormal', nhận được: 'critical'"
    },
    {
      "field": "field_status",
      "code": "UNKNOWN_KEY",
      "message": "Khóa 'ghost_field' không tồn tại trong định nghĩa"
    }
  ]
}
```

**Validation Rules for `field_status`:**
- Status value **must be** `"normal"` or `"abnormal"` (case-sensitive)
- Key **must exist** in active vital_field_definition
- Empty values (empty string) are **ignored** (no error)

#### 3. Invalid `field_notes` (NEW in TASK-079)

**HTTP 422 Unprocessable Entity**

```json
{
  "detail": [
    {
      "field": "field_notes",
      "code": "UNKNOWN_KEY",
      "message": "Khóa 'unknown_vital' không tồn tại trong định nghĩa"
    }
  ]
}
```

**Validation Rules for `field_notes`:**
- Key **must exist** in active vital_field_definition
- Empty strings are **ignored** (no error)
- Note text (value) can be arbitrary string

#### 4. Other Errors

| HTTP Status | Scenario |
|-------------|----------|
| 400 | Invalid request format |
| 401 | Unauthorized |
| 403 | Forbidden (no write permission on visit) |
| 404 | Visit not found |
| 500 | Server error |

### Processing Steps

1. Validate `visit_id` exists + user has `vital.write` permission
2. Validate `values` using existing validator (type, required, range)
3. **NEW:** Validate `field_status`:
   - Each status value ∈ {normal, abnormal}
   - Each key exists in active definitions
   - Empty values ignored
4. **NEW:** Validate `field_notes`:
   - Each key exists in active definitions
   - Empty values ignored
5. If validation passes → persist to `visit_vitals` table with all fields
6. Snapshot `vital_schema_version` at time of entry
7. Return 201 with full `VisitVitalsResponse`

---

## 3. GET /api/v1/visits/{id}/vitals

**Purpose:** Fetch all vital entries for a visit (including history timeline with structured status).

### Request

```http
GET /api/v1/visits/{id}/vitals
Authorization: Bearer {token}
```

**URL Parameters:**
- `id` (integer, required) — visit_id

**Query Parameters:** (optional)
- `is_primary` (boolean, optional) — filter for primary entry only (`true` / `false`)
- `limit` (integer, optional) — max records (default: 100)
- `offset` (integer, optional) — pagination offset

### Response

**HTTP 200 OK**

```json
{
  "data": [
    {
      "id": 1001,
      "visit_id": 555,
      "values": {
        "heart_rate": 88,
        "bp": "130/85",
        "temperature": 36.8,
        "height": 170,
        "weight": 65
      },
      "field_status": {
        "heart_rate": "normal",
        "bp": "abnormal",
        "temperature": "normal"
      },
      "field_notes": {
        "bp": "Huyết áp cao, tái đo sau 5 phút"
      },
      "vital_schema_version": 3,
      "notes": null,
      "is_primary": true,
      "created_at": "2026-06-16T10:30:00Z",
      "created_by": "doctor_001"
    },
    {
      "id": 1002,
      "visit_id": 555,
      "values": {
        "heart_rate": 82,
        "bp": "125/82"
      },
      "field_status": {
        "heart_rate": "normal",
        "bp": "normal"
      },
      "field_notes": {},
      "vital_schema_version": 3,
      "notes": "Tái đo — kết quả bình thường",
      "is_primary": false,
      "created_at": "2026-06-16T10:45:00Z",
      "created_by": "doctor_001"
    }
  ],
  "total": 2
}
```

**Response Field Descriptions:** Same as POST response (all vital entry fields).

**Special Notes:**
- **field_status & field_notes always present** in response (empty `{}` if not set)
- Records ordered **descending by created_at** (newest first)
- **Backward compat:** Old records (pre-migration 0041) have `field_status={}`, `field_notes={}` (populated by server_default)

### Error Responses

| HTTP Status | Scenario |
|-------------|----------|
| 400 | Invalid query parameters |
| 401 | Unauthorized |
| 403 | Forbidden (no read permission on visit) |
| 404 | Visit not found |
| 500 | Server error |

---

## 4. Migration: 0041_add_vital_field_status

**Location:** `clinic-cms/alembic/versions/0041_add_vital_field_status.py`

### Summary

Adds two JSONB columns to `visit_vitals` table:
- `field_status`: Structured per-field normal/abnormal status
- `field_notes`: Structured per-field annotations

### Changes

```python
def upgrade():
    # Add field_status column
    op.add_column('visit_vitals',
        sa.Column('field_status', sa.JSON(), 
                  nullable=True, 
                  server_default=text("'{}'::jsonb"))
    )
    
    # Add field_notes column
    op.add_column('visit_vitals',
        sa.Column('field_notes', sa.JSON(), 
                  nullable=True, 
                  server_default=text("'{}'::jsonb"))
    )

def downgrade():
    op.drop_column('visit_vitals', 'field_notes')
    op.drop_column('visit_vitals', 'field_status')
```

### Details

| Aspect | Value |
|--------|-------|
| **down_revision** | `0040_create_advice_template` |
| **revision** | HEAD after merge |
| **Columns added** | 2 (field_status, field_notes) |
| **Data backfill** | Automatic via `server_default='{}'::jsonb` |
| **RLS changes** | None (add-column only, no policy updates) |
| **Backward compat** | ✓ Full — existing rows get empty `{}` values |

---

## 5. Pydantic Schemas (Backend)

### VisitVitalsCreate

```python
class VisitVitalsCreate(BaseModel):
    values: dict[str, Any]                              # Vital measurements
    field_status: dict[str, str] = {}                   # {key: "normal"|"abnormal"}
    field_notes: dict[str, str] = {}                    # {key: note_text}
    notes: Optional[str] = None                         # Legacy field
```

### VisitVitalsResponse

```python
class VisitVitalsResponse(BaseModel):
    id: int
    visit_id: int
    values: dict[str, Any]
    field_status: dict[str, str]                        # Always present (empty {} if not set)
    field_notes: dict[str, str]                         # Always present (empty {} if not set)
    vital_schema_version: int
    notes: Optional[str]
    is_primary: bool
    created_at: datetime
    created_by: str
    
    model_config = ConfigDict(from_attributes=True)
```

---

## 6. Validator: validate_annotations

**Location:** `clinic-cms/app/modules/vitals/services/validator_service.py`

### Signature

```python
def validate_annotations(
    field_status: dict[str, str],
    field_notes: dict[str, str],
    active_definitions: list[VitalFieldDefinition]
) -> list[ValidationError]:
```

### Rules

| Check | Error Code | Message | Ignore Empty? |
|-------|-----------|---------|---------------|
| Status value ∉ {normal, abnormal} | `INVALID_STATUS` | "Status phải là 'normal' hoặc 'abnormal', nhận được: X" | Yes (empty strings ignored) |
| Key not in active definitions (field_status) | `UNKNOWN_KEY` | "Khóa '{key}' không tồn tại trong định nghĩa" | Yes |
| Key not in active definitions (field_notes) | `UNKNOWN_KEY` | "Khóa '{key}' không tồn tại trong định nghĩa" | Yes |

### Return Value

List of `ValidationError` objects with `{field, code, message}`.  
**Does NOT raise** — caller decides whether to raise 422.

### Example

```python
errors = validate_annotations(
    field_status={"heart_rate": "invalid_value", "ghost": "normal"},
    field_notes={"bp": "..."},
    active_definitions=[...])

# errors = [
#   ValidationError(field="field_status", code="INVALID_STATUS", 
#                   message="Status phải là 'normal' hoặc 'abnormal', nhận được: 'invalid_value'"),
#   ValidationError(field="field_status", code="UNKNOWN_KEY",
#                   message="Khóa 'ghost' không tồn tại trong định nghĩa")
# ]
```

---

## 7. Frontend Type Definitions

### VisitVitals Type

```typescript
interface VisitVitals {
  id: number;
  visit_id: number;
  values: Record<string, any>;
  field_status?: Record<string, 'normal' | 'abnormal'>;
  field_notes?: Record<string, string>;
  vital_schema_version: number;
  notes?: string;
  is_primary: boolean;
  created_at: string;
  created_by: string;
}
```

### VitalsCreate Type

```typescript
interface VitalsCreate {
  values: Record<string, any>;
  field_status?: Record<string, 'normal' | 'abnormal'>;
  field_notes?: Record<string, string>;
  notes?: string;
}
```

### VitalFieldDefinition Type

```typescript
interface VitalFieldDefinition {
  id: number;
  key: string;
  label: string;
  unit: string;
  data_type: 'number' | 'integer' | 'text' | 'boolean' | 'select';
  min_value?: number | null;
  max_value?: number | null;
  warning_min?: number | null;
  warning_max?: number | null;
  is_required: boolean;
  group_name: string;
  sort_order: number;
  options?: Array<{ value: string; label: string }> | null;
  help_text: string;
  placeholder?: string;
}
```

---

## 8. i18n Keys (NEW in TASK-079)

### Vietnamese (vi/doctor.json)

```json
{
  "statusNormal": "Bình thường",
  "statusAbnormal": "Không bình thường",
  "toggleStatus": "Thay đổi trạng thái",
  "noteFor": "Ghi chú cho {field}",
  "extraNotes": "Ghi chú thêm",
  "extraNotesPlaceholder": "Nhập ghi chú..."
}
```

### English (en/doctor.json)

```json
{
  "statusNormal": "Normal",
  "statusAbnormal": "Abnormal",
  "toggleStatus": "Toggle Status",
  "noteFor": "Note for {field}",
  "extraNotes": "Additional Notes",
  "extraNotesPlaceholder": "Enter notes..."
}
```

---

## 9. Testing Coverage

### Backend Unit Tests

| Test Class | Count | Coverage |
|-----------|-------|----------|
| TestAnnotations (NEW) | 12 | field_status validation (valid/invalid), field_notes validation, error collection |

**Test Cases:**
- `test_valid_status_normal` — status="normal" ✓
- `test_valid_status_abnormal` — status="abnormal" ✓
- `test_invalid_status_value` — status="critical" → INVALID_STATUS ✗
- `test_unknown_key_in_field_status` — key not in definition → UNKNOWN_KEY ✗
- `test_unknown_key_in_field_notes` — key not in definition → UNKNOWN_KEY ✗
- `test_empty_payload_no_errors` — empty {} → no errors ✓
- `test_empty_status_value_ignored` — status="" → ignored (no error) ✓
- `test_empty_note_ignored` — note="" → ignored (no error) ✓
- `test_valid_notes_with_known_key` — valid note for known key ✓
- `test_multiple_errors_collected` — 2+ errors in one payload ✓
- `test_both_valid_status_and_notes` — both correct ✓
- (1 additional combined status+notes test) ✓

**Result:** 12/12 PASS

### Backend Integration Tests

| Test Class | Count | Coverage |
|-----------|-------|----------|
| TestFieldStatusAnnotations (NEW) | 5 | API round-trip, backward compat, 422 validation |

**Test Cases:**
- `test_post_with_field_status_and_notes` — POST → 201, response includes field_status/field_notes ✓
- `test_get_returns_field_status` — GET list includes field_status/field_notes ✓
- `test_backward_compat_no_annotation_fields` — POST without new fields → 201, defaults {} ✓
- `test_invalid_status_value_rejected` — POST bad status → 422 ✗
- `test_unknown_key_in_annotation_rejected` — POST ghost key → 422 ✗

**Result:** 5/5 PASS

### Frontend Tests

| Test Suite | Count | Coverage |
|-----------|-------|----------|
| VitalsTab.test.tsx (NEW) | 12 | Dynamic render, status evaluation, structured payload, timeline, backward compat |

**Test Cases:**
- `shows loading spinner while fetching definitions` ✓
- `renders no-schema error when definitions list is empty` ✓
- `renders form fields dynamically from definition (label + unit)` ✓
- `renders required marker for is_required fields` ✓
- `auto-evaluates abnormal when value exceeds warning_max` ✓
- `auto-evaluates normal when value is within warning range` ✓
- `sends structured payload with field_status and field_notes on save` ✓
- `sends empty field_status when value is normal` ✓ (note: name slightly misleading; correctly sends "normal" status)
- `displays field_status from timeline record with color coding` ✓
- `backward compat: records without field_status/field_notes render without error` ✓
- `renders select input for data_type=select definition` ✓
- `renders group header when group_name is set` ✓

**Result:** 12/12 PASS

---

## 10. Performance & Scaling Notes

### JSONB Indexing

For optimal query performance on `field_status` filtering (e.g., "find all abnormal BP readings"):

```sql
-- Optional GIN index for field_status JSONB column (if needed for filtering)
CREATE INDEX idx_visit_vitals_field_status_gin 
ON visit_vitals USING GIN (field_status);
```

Not created by migration (can add as separate task if needed).

### Response Size

- `field_status` + `field_notes` typically < 100 bytes per record
- Minimal impact on API response payload size
- No query plan changes needed

---

## 11. Backward Compatibility Checklist

| Aspect | Status | Notes |
|--------|--------|-------|
| Old data reads correctly | ✓ | Migration backfills `{}` via server_default; FE uses `?? {}` fallback |
| New fields optional in request | ✓ | `field_status` + `field_notes` default to `{}` in schema |
| Old clients still work | ✓ | POST without new fields → 201 OK (defaults applied server-side) |
| Response always includes new fields | ✓ | Even old records return `field_status={}`, `field_notes={}` |
| No breaking changes to existing fields | ✓ | `values`, `notes`, `is_primary`, etc. unchanged |
| Timeline rendering handles old records | ✓ | FE checks for empty `field_status`/`field_notes`, renders without error |

---

## 12. Summary of Changes

| Component | Type | Change |
|-----------|------|--------|
| Schema | DB | ADD COLUMN field_status JSONB, ADD COLUMN field_notes JSONB |
| Migration | DB | 0041_add_vital_field_status.py |
| Validator | BE | NEW method validate_annotations() |
| Service | BE | Call validator, persist new fields, return in response |
| Types | FE | Add field_status, field_notes to VisitVitals, VitalsCreate |
| Form | FE | Render dynamically from definitions, send structured payload |
| Timeline | FE | Display field_status with colors, show field_notes per-field |
| i18n | FE | 6 new keys (VI + EN) |
| Tests | BE/FE | 12 unit + 5 integration (BE), 12 vitest (FE) |

---

**All endpoints tested and verified to work correctly with the new schema. API is backward compatible with legacy clients.**
