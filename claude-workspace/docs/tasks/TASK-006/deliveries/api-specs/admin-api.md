# Admin API Specification — TASK-006

## Overview

Module admin cung cấp các API để quản lý clinic, settings, và wizard onboarding.
Base URL: `/api/v1`

---

## 1. Clinic Admin Endpoints

### POST /admin/clinics
Tạo mới một clinic tenant.

**Permission**: `clinic.create`

**Request Body**:
```json
{
  "name": "string (2-200)",
  "code": "string (2-50, alphanumeric + dash/underscore)",
  "specialty": "general|pediatric|ob_gyn|dermatology|dental",
  "address": "string (optional)",
  "phone": "string (optional)",
  "email": "string (optional)",
  "tax_code": "string (optional)"
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "code": "string",
  "name": "string",
  "specialty": "string",
  "address": null,
  "phone": null,
  "email": null,
  "tax_code": null,
  "is_active": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Errors**: 409 — duplicate clinic code; 403 — missing permission.

**Side effects**: Creates default `clinic_settings` row and `clinic_onboarding_state` row.

---

### GET /admin/clinics/{clinic_id}
Xem thông tin chi tiết clinic.

**Permission**: `clinic.read`

**Response 200**: same as POST response.

---

### PATCH /admin/clinics/{clinic_id}
Cập nhật thông tin clinic.

**Permission**: `clinic.update`

**Request Body** (partial):
```json
{
  "name": "string (optional)",
  "specialty": "general|...|dental (optional)",
  "address": "string (optional)",
  "phone": "string (optional)",
  "email": "string (optional)",
  "tax_code": "string (optional)"
}
```

**Response 200**: same as POST response.

---

## 2. Settings Endpoints

### GET /clinics/me/settings
Đọc settings của clinic hiện tại (lấy từ JWT).

**Permission**: Authenticated user only (no specific permission).

**Response 200**:
```json
{
  "clinic_id": "uuid",
  "operating_hours": {
    "mon": {"is_open": true, "open": "08:00", "close": "17:00"},
    "tue": {...}, "wed": {...}, "thu": {...}, "fri": {...},
    "sat": {"is_open": false, "open": "08:00", "close": "12:00"},
    "sun": {"is_open": false, "open": "08:00", "close": "12:00"}
  },
  "appointment": {
    "slot_duration_minutes": 30,
    "booking_advance_days": 30,
    "allow_walk_in": true,
    "require_deposit": false,
    "deposit_amount": 0.0
  },
  "queue": {
    "algorithm": "fifo",
    "max_wait_minutes": 120,
    "sms_reminder": false
  },
  "inventory": {
    "low_stock_threshold_percent": 20.0,
    "auto_reorder": false
  },
  "prescription": {
    "max_days_supply": 30,
    "require_generic": false
  },
  "billing": {
    "currency": "VND",
    "tax_rate_percent": 0.0,
    "invoice_prefix": "INV"
  },
  "specialty": {
    "code": "general",
    "vital_fields": ["bp_systolic", "bp_diastolic", "pulse", "temperature", "weight", "height", "spo2"]
  }
}
```

**Caching**: Redis 5 phút (key `clinic:settings:{clinic_id}`). Fallback to DB nếu Redis không available.

---

### PATCH /clinics/me/settings
Cập nhật settings của clinic hiện tại (deep merge).

**Permission**: `clinic.settings.update`

**Request Body** (partial — chỉ cần gửi nhóm cần update):
```json
{
  "appointment": {
    "slot_duration_minutes": 20
  }
}
```

**Response 200**: Full settings response sau khi update.

**Cache invalidation**: Xóa Redis cache sau khi update thành công.

---

## 3. Onboarding Wizard Endpoints

### POST /onboarding/start
Khởi tạo hoặc reset wizard onboarding.

**Permission**: `clinic.onboard`

**Request Body**:
```json
{"specialty": "general|pediatric|ob_gyn|dermatology|dental"}
```

**Response 200**:
```json
{
  "clinic_id": "uuid",
  "completed_step": "start",
  "next_step": "info",
  "message": "Onboarding started. Next step: info"
}
```

**Side effects**: Sets specialty settings, resets onboarding state to step "info".

---

### GET /onboarding/state
Xem trạng thái wizard hiện tại (hỗ trợ resume).

**Permission**: `clinic.onboard`

**Response 200**:
```json
{
  "clinic_id": "uuid",
  "current_step": "info",
  "completed_steps": ["start"],
  "started_at": "datetime",
  "completed_at": null
}
```

---

### POST /onboarding/info
Step 1: Cập nhật thông tin cơ bản clinic.

**Permission**: `clinic.onboard`

**Request Body**:
```json
{
  "name": "string",
  "address": "string (optional)",
  "phone": "string (optional)",
  "email": "string (optional)",
  "tax_code": "string (optional)"
}
```

---

### POST /onboarding/users
Step 2: Tạo tài khoản nhân viên.

**Permission**: `clinic.onboard`

**Request Body**:
```json
{
  "users": [
    {
      "username": "string (3-100)",
      "full_name": "string",
      "password": "string (min 8)",
      "email": "string (optional)",
      "phone": "string (optional)",
      "license_number": "string (optional)",
      "specialty_subfield": "string (optional)"
    }
  ]
}
```

---

### POST /onboarding/shifts
Step 3: Tạo ca làm việc templates.

**Permission**: `clinic.onboard`

**Request Body**:
```json
{
  "shifts": [
    {
      "name": "string",
      "start_time": "HH:MM",
      "end_time": "HH:MM"
    }
  ]
}
```

**Note**: Sử dụng TASK-014 shift_service nếu available, graceful stub nếu chưa có.

---

### POST /onboarding/inventory-csv
Step 4: Import danh mục thuốc/vật tư từ CSV (multipart form).

**Permission**: `clinic.onboard`

**Form Fields**:
- `dry_run: bool` (default `true`) — preview only, không commit
- `file: file` — CSV file

**CSV Format** (header row required):
```
name,code,unit,initial_qty
Amoxicillin 500mg,AMX500,tab,1000
Paracetamol 500mg,PAR500,tab,5000
```

**Limits**: max 5MB, max 10,000 rows.

**Response 200**:
```json
{
  "ok": true,
  "total_rows": 2,
  "valid_rows": 2,
  "error_count": 0,
  "errors": [],
  "preview": [{"row_number": 2, "name": "...", "code": "...", "unit": "...", "initial_qty": 1000.0}],
  "committed": false
}
```

**Performance**: 1000 rows < 30s (tested: ~0.2s).

---

### POST /onboarding/services
Step 5: Tạo danh mục dịch vụ.

**Permission**: `clinic.onboard`

**Note**: Stub pending TASK-010 service catalog module.

---

### POST /onboarding/complete
Hoàn tất wizard onboarding.

**Permission**: `clinic.onboard`

**Response 200**: `{"completed_step": "done", "next_step": null, "message": "Onboarding complete!"}`

---

## 4. Error Codes

| HTTP Status | Code | Description |
|---|---|---|
| 401 | Not authenticated | No or invalid JWT |
| 403 | FORBIDDEN | Missing required permission |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Duplicate code/username |
| 422 | VALIDATION_ERROR | Pydantic schema validation failed |
