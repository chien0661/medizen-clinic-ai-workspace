# Thiết kế chức năng: Admin Clinic + Settings + Onboarding Wizard

**Task**: TASK-006  
**Module**: `app/modules/admin/`  
**Ngày**: 2026-04-27  
**Trạng thái**: DONE

---

## 1. Tổng quan

Module Admin cung cấp:
1. **Quản lý Clinic**: Tạo/xem/cập nhật tenant clinic.
2. **Settings per-Clinic**: Cấu hình JSONB theo từng nhóm (operating_hours, appointment, queue, inventory, prescription, billing, specialty).
3. **Onboarding Wizard**: 6 bước hướng dẫn thiết lập clinic mới (specialty → info → users → shifts → inventory-csv → services → done).

---

## 2. Kiến trúc module

```
app/modules/admin/
├── api/
│   └── routes.py          — FastAPI router (12 endpoints)
├── models/
│   ├── clinic_settings.py — ClinicSettings SQLAlchemy model
│   └── clinic_onboarding_state.py — Onboarding state model
├── schemas/
│   ├── clinic_schemas.py  — ClinicCreate, ClinicUpdate, ClinicResponse
│   ├── settings_schemas.py — Per-group Pydantic settings models
│   └── onboarding_schemas.py — Wizard step schemas
└── services/
    ├── default_settings.py    — Nguồn giá trị mặc định
    ├── clinic_service.py      — CRUD clinic + auto-bootstrap
    ├── settings_service.py    — Get/update settings + Redis cache
    └── onboarding_service.py  — Wizard step handlers
```

---

## 3. Database Schema

### Bảng `clinic_settings`

| Column | Type | Mô tả |
|---|---|---|
| clinic_id | UUID (PK) | FK → clinic.id (CASCADE) |
| settings | JSONB | Blob chứa tất cả settings |
| updated_at | TIMESTAMPTZ | Lần cập nhật gần nhất |
| updated_by | UUID | User cập nhật |

**RLS**: `clinic_id::text = current_setting('app.current_clinic_id', true)`

### Bảng `clinic_onboarding_state`

| Column | Type | Mô tả |
|---|---|---|
| clinic_id | UUID (PK) | FK → clinic.id (CASCADE) |
| current_step | VARCHAR(50) | Bước hiện tại: info/users/shifts/inventory/services/done |
| completed_steps | TEXT[] | Các bước đã hoàn thành |
| started_at | TIMESTAMPTZ | Thời điểm bắt đầu |
| completed_at | TIMESTAMPTZ | Thời điểm hoàn thành (NULL nếu chưa xong) |
| started_by | UUID | User bắt đầu onboarding |

**RLS**: standard tenant_isolation policy.

---

## 4. Settings JSONB Structure

### Default values (tất cả specialty)

```json
{
  "operating_hours": {
    "mon":{"is_open":true,"open":"08:00","close":"17:00"},
    "tue":{"is_open":true,"open":"08:00","close":"17:00"},
    "wed":{"is_open":true,"open":"08:00","close":"17:00"},
    "thu":{"is_open":true,"open":"08:00","close":"17:00"},
    "fri":{"is_open":true,"open":"08:00","close":"17:00"},
    "sat":{"is_open":false,"open":"08:00","close":"12:00"},
    "sun":{"is_open":false,"open":"08:00","close":"12:00"}
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
    "vital_fields": ["bp_systolic","bp_diastolic","pulse","temperature","weight","height","spo2"]
  }
}
```

### Vital fields per specialty

| Specialty | Vital Fields | Count |
|---|---|---|
| general | bp_systolic, bp_diastolic, pulse, temperature, weight, height, spo2 | 7 |
| pediatric | general + head_circumference | 8 |
| ob_gyn | general + fundal_height, fetal_heart_rate | 9 |
| dermatology | bp_systolic, bp_diastolic, pulse, temperature, weight, height | 6 |
| dental | bp_systolic, bp_diastolic, pulse, temperature, weight | 5 |

---

## 5. Settings Service — Redis Cache

Chiến lược cache:
- **Key**: `clinic:settings:{clinic_id}`
- **TTL**: 5 phút
- **Hit**: Trả về từ Redis (không query DB)
- **Miss**: Query DB, deep-merge với defaults, set cache
- **Invalidation**: `update_settings()` xóa cache ngay sau khi ghi DB
- **Fallback**: Nếu Redis không available, đọc thẳng từ DB (không raise exception)

Deep merge logic:
```python
_deep_merge(base, patch) → new_dict  # không mutate base
```

---

## 6. Onboarding Wizard Flow

```
POST /onboarding/start (specialty)
  ↓ tạo/reset clinic_onboarding_state, set specialty settings
POST /onboarding/info (name, address, phone, email, tax_code)
  ↓ cập nhật clinic, completed_steps += ["info"]
POST /onboarding/users (list of users)
  ↓ tạo user qua user_service, completed_steps += ["users"]
POST /onboarding/shifts (list of shift templates)
  ↓ tạo shift qua hr.shift_service (stub nếu TASK-014 không có), completed_steps += ["shifts"]
POST /onboarding/inventory-csv (CSV file, dry_run=True/False)
  ↓ parse + validate CSV, nếu dry_run=False thì commit (stub cho inventory table - TASK-010)
POST /onboarding/services (list of services)
  ↓ tạo service qua service_catalog (stub nếu TASK-010 không có), completed_steps += ["services"]
POST /onboarding/complete
  ↓ set current_step="done", completed_at=now()
```

### Skip step:
Không gọi step đó → `current_step` advance mà không add vào `completed_steps`.

### Resume:
GET /onboarding/state → xem `current_step` và `completed_steps` → tiếp tục từ đúng bước.

---

## 7. CSV Import Inventory

### Format
```
name,code,unit,initial_qty
Amoxicillin 500mg,AMX500,tab,1000
Paracetamol 500mg,PAR500,tab,5000
```

### Validation per row
- `name`: required, non-empty
- `code`: required, non-empty  
- `unit`: required, non-empty
- `initial_qty`: non-negative float

### Limits
- File size: max 5 MB
- Rows: max 10,000

### Performance
- 1,000 rows: < 30s (tested: ~0.2s)

### Dry-run
Khi `dry_run=True`: chỉ parse + validate, không commit. Response trả về `committed=false`.

---

## 8. Permission Matrix

| Permission | Admin | Receptionist | Doctor | Nurse |
|---|---|---|---|---|
| clinic.create | ✓ | | | |
| clinic.read | ✓ | | | |
| clinic.update | ✓ | | | |
| clinic.settings.update | ✓ | | | |
| clinic.onboard | ✓ | | | |

---

## 9. Test Coverage

| Test Type | Count | Coverage |
|---|---|---|
| Unit tests (schemas, services) | 64 | 100% schemas, 100% models |
| Integration tests (API e2e) | 18 | Key happy paths + 403 + RLS |
| **Total** | **82** | **70% overall** |

### Tests verified:
- Tạo clinic → default settings auto-applied (general: 7 vital fields)
- Pediatric clinic → head_circumference present (8 vital fields)
- PATCH appointment.slot_duration_minutes=20 → reread returns 20
- CSV 1000 rows dry-run < 30s ✓
- Onboarding start → info → resume from state
- Permission gating: 403 without required permission
- Tenant isolation: JWT clinic_id enforced via RLS + middleware

---

## 10. Lưu ý triển khai

1. **Redis**: Nếu Redis không available, settings vẫn hoạt động (đọc từ DB). Không có lỗi cho user.
2. **TASK-009 (Vitals)**: Vital fields được store trong `clinic_settings.specialty.vital_fields`, không dùng bảng `vital_field_definition` (TASK-009 scope). Khi TASK-009 hoàn thành, có thể sync từ settings sang bảng đó.
3. **TASK-010 (Services)**: Inventory commit và service catalog creation trong onboarding là stubs. Log warning khi TASK-010 module không tìm thấy.
4. **TASK-014 (HR Shifts)**: Shift creation trong onboarding sử dụng `app.modules.hr.services.shift_service`. Nếu module không có, stub gracefully.
