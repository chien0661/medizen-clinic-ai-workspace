# Hệ thống Quản lý Phòng khám (CMS) — Phân tích Nghiệp vụ Chi tiết

> **Phiên bản:** 1.0 — Phân tích nghiệp vụ v1 (MVP)
> **Đối tượng:** Phòng khám tư nhân nhỏ, chuyên 1 mảng cụ thể
> **Mô hình kinh doanh:** SaaS multi-tenant, mỗi tenant = một phòng khám

---

## 1. Tổng quan dự án

### 1.1. Mục tiêu

Xây dựng nền tảng SaaS quản lý vận hành cho phòng khám tư nhân nhỏ tại Việt Nam, tập trung vào:

- Quản lý tiếp đón và lịch hẹn bệnh nhân
- Quản lý kho thuốc và vật tư y tế
- Quản lý kê đơn và cấp phát thuốc
- Quản lý hóa đơn và thanh toán
- Quản lý nhân sự, ca trực, chấm công
- Báo cáo vận hành cho chủ phòng khám

### 1.2. Đối tượng người dùng

- **Phòng khám tư nhân nhỏ** (1-5 bác sĩ).
- **Mỗi phòng khám chuyên về 1 mảng cụ thể** (răng, da liễu, nhi, sản, mắt, đa khoa, YHCT...).
- **Không tham gia BHYT** — toàn bộ thanh toán là dịch vụ trả phí trực tiếp.
- Có quầy thuốc nội bộ hoặc cho phép bệnh nhân mua thuốc bên ngoài.

### 1.3. Triết lý thiết kế

- **Đơn giản trong onboarding** — clinic mới setup nhanh.
- **Offline-capable** — desktop client (Tauri) hoạt động được khi mất mạng.
- **Multi-tenant** — kiến trúc SaaS từ đầu.
- **Modular** — tách module rõ ràng để dễ mở rộng.

### 1.4. Tech stack

| Lớp | Công nghệ |
|---|---|
| Backend | Python 3.11+ với FastAPI |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.x (async) |
| Migration | Alembic |
| Frontend/Desktop | React + Tauri |
| Authentication | JWT |
| Validation | Pydantic |

---

## 2. Phạm vi v1 (Scope)

### 2.1. Có trong v1

- Auth + RBAC + Tenancy + Audit log
- Patient (hồ sơ bệnh nhân + guardian relationship)
- Appointment + Walk-in + Queue
- Visit (entity trung tâm, không có EMR đầy đủ)
- **Vitals dynamic form** (cấu hình động theo từng phòng khám)
- Service catalog
- Prescription (in-house + external mixed)
- Inventory & Pharmacy (FEFO + reserve/dispense)
- Billing + Payment
- HR + Shift + Attendance (lương cứng)
- Reporting cơ bản
- Settings per clinic
- Offline support (Tauri client)

### 2.2. KHÔNG có trong v1 (để phase sau)

- **EMR (Electronic Medical Record) đầy đủ** — SOAP có cấu trúc, diagnosis ICD-10, lab results
- **BHYT** — không tích hợp BHXH, không xuất XML giám định
- **Commission cho bác sĩ** — chưa tính lương theo % doanh thu
- **Package/liệu trình** — không bán gói dịch vụ trả trước
- **Đa giá, giá theo bác sĩ** — đồng giá trong clinic
- **Tái khám discount** — không có logic giảm giá tái khám tự động
- **Patient tag/membership** — không có hệ thống VIP, khách quen
- **Multi-clinic per tenant** — 1 clinic = 1 tenant, chưa hỗ trợ chuỗi
- **Notification SMS/Zalo** — chỉ in-app notification
- **Patient self-portal** — bệnh nhân chưa tự đặt lịch online
- **Báo cáo BHYT, dịch tễ học** — không có
- **Module chuyên khoa đặc thù** — dental chart, prenatal tracking, etc.

---

## 3. Quyết định kiến trúc nền tảng

### 3.1. Multi-tenancy

**Mô hình:** Shared database + `clinic_id` ở mọi bảng + PostgreSQL Row-Level Security (RLS).

**Quy tắc bắt buộc:**

- Mọi bảng nghiệp vụ phải có cột `clinic_id` (UUID, NOT NULL).
- Mọi query phải filter theo `clinic_id` — đảm bảo qua middleware tự động set context.
- RLS policy bật cho tất cả bảng có `clinic_id`, dùng session variable `app.current_clinic_id`.
- Không có user xem chéo clinic — quan hệ user-clinic là 1-1.

**Cấu trúc 2 cấp:**

```
Tenant (= Clinic) ── User (Staff)
                ├── Patient
                ├── Visit, Appointment
                ├── Inventory, Prescription
                └── Invoice, Payment...
```

### 3.2. Soft delete & Audit log

- **Không có hard delete** ở bất kỳ bảng nghiệp vụ nào.
- Mọi bảng có cặp cột: `is_deleted` (boolean), `deleted_at` (timestamp), `deleted_by` (user_id).
- Audit log ghi mọi thao tác sensitive: create/update/delete + ai làm + khi nào + dữ liệu trước/sau.
- Audit log cho cả **đọc dữ liệu nhạy cảm** (xem hồ sơ bệnh nhân) — async, không block.

### 3.3. Module structure

```
/app
  /modules
    /auth              # Login, JWT, password
    /tenancy           # Clinic context, RLS context middleware
    /audit             # Decorator/middleware ghi audit log
    /users             # User, Role, Permission
    /patients          # Patient, guardian relationship
    /appointments      # Appointment, queue
    /visits            # Visit, VisitVitals, VisitService
    /vitals            # VitalFieldDefinition, VitalSchemaVersion
    /services          # Service catalog
    /prescriptions     # Prescription, PrescriptionItem
    /medicines         # Medicine catalog
    /inventory         # InventoryItem, Batch, StockMovement
    /pharmacy          # Dispense workflow
    /billing           # Invoice, InvoiceItem, Payment
    /hr                # Shift, ShiftTemplate, LeaveRequest, Attendance
    /reporting         # Query-heavy reports
    /admin             # Tenant onboarding, settings
    /notifications     # In-app notifications (phase 2: SMS)
  /core
    /db                # Session, RLS context, base model
    /security          # JWT, password hash, encryption
    /config            # Settings
    /exceptions        # Custom exception handlers
  /integrations        # POS printer, scanner (phase 2: BHYT, SMS)
  /utils
  /tests
```

### 3.4. Naming conventions

- **Bảng:** snake_case, số ít (`patient`, `visit`, không phải `patients`/`visits`). Hoặc số nhiều nhất quán — chọn 1.
- **Cột:** snake_case.
- **Foreign key:** `<table>_id` (vd: `patient_id`, `visit_id`).
- **Boolean:** `is_<adj>` hoặc `has_<noun>` (`is_active`, `is_deleted`, `has_insurance`).
- **Timestamp:** `<verb>_at` (`created_at`, `dispensed_at`).
- **Public ID** (hiển thị cho user): UUID hoặc mã ngắn dễ đọc — không dùng auto-increment integer.

---

## 4. Module Patient & Reception

### 4.1. Định danh bệnh nhân

**Cấu trúc ID:**

- `id` (UUID): khóa chính nội bộ, không bao giờ hiển thị cho user.
- `patient_code` (string, unique trong clinic): mã ngắn dễ đọc, tự sinh (vd: `BN0001`, `BN0002`).
- `phone` (string, KHÔNG unique): field tìm kiếm chính.

**Lý do `phone` không unique:**

- Trẻ em chưa có SĐT, dùng SĐT của phụ huynh.
- Người già dùng chung SĐT con cháu.
- Một SĐT có thể có 3-4 bệnh nhân (mẹ và các con).
- Bệnh nhân có thể đổi số.

### 4.2. Thông tin bệnh nhân

**Bắt buộc:**
- Họ tên
- Ngày sinh (chỉ năm cũng được)
- Giới tính
- SĐT

**Tùy chọn:**
- CCCD/CMND
- Địa chỉ (phường/xã, quận/huyện, tỉnh/thành)
- Nhóm máu
- Dị ứng (text)
- Tiền sử bệnh mãn tính (text)
- Email
- Nghề nghiệp
- Nguồn khách (`referral_source`): Google, Facebook, người quen, walk-in...

### 4.3. Guardian Relationship

Hỗ trợ quan hệ giám hộ (cha/mẹ — con):

```
PatientRelation
  - id, clinic_id
  - patient_id (người được giám hộ)
  - guardian_patient_id (người giám hộ)
  - relation_type: "parent" | "spouse" | "child" | "other"
  - is_primary_contact: boolean
```

### 4.4. Merge hồ sơ trùng lặp

Khi lễ tân phát hiện bệnh nhân tạo trùng (đăng ký lại do quên mã cũ):

- Chức năng admin có quyền `patient.merge`.
- Chọn 2 hồ sơ → chọn record giữ lại → record kia bị soft-delete và merge:
  - Tất cả Visit, Prescription, Invoice của record cũ → reassign sang record mới.
  - Audit log đầy đủ.
- Có thể undo trong 7 ngày (backup mapping).

### 4.5. Workflow tiếp đón

```
Bệnh nhân đến phòng khám
        ↓
Lễ tân tra cứu (theo SĐT, tên, patient_code) hoặc tạo mới
        ↓
Tạo Visit (status: WAITING)
        ↓
[Tùy chọn] Lễ tân pre-assign doctor nếu bệnh nhân yêu cầu
        ↓
Bệnh nhân vào ghế chờ
        ↓
Y tá gọi vào phòng đo vitals → nhập VisitVitals
        ↓
Bệnh nhân quay lại ghế chờ
        ↓
Bác sĩ "Gọi bệnh nhân tiếp theo"
   ├─ Ưu tiên: visit có assigned_doctor_id = current user
   ├─ Sau: visit assigned_doctor_id = null
   └─ Sau: visit assigned cho người khác (chỉ khi không còn ai)
        ↓
Visit chuyển IN_PROGRESS, doctor_id = current user
        ↓
Bác sĩ chọn services đã thực hiện + kê đơn (nếu có)
        ↓
Bác sĩ "Hoàn tất khám" → status: AWAITING_PAYMENT
        ↓
Lễ tân lập Invoice (auto pull VisitService + Prescription in_house)
        ↓
Thu tiền (Payment) → cấp thuốc (Pharmacy dispense)
        ↓
Status: COMPLETED
```

### 4.6. Queue management

**Một queue duy nhất per clinic** — không tách theo bác sĩ.

**Sort order:**

```sql
ORDER BY
  priority DESC,           -- ưu tiên (cấp cứu, người già, mang thai, trẻ <6m)
  is_returning_patient DESC, -- bệnh nhân quay lại sau xét nghiệm/đo vitals
  created_at ASC           -- đến trước phục vụ trước
```

**Priority levels:**
- 0: thường
- 5: ưu tiên (người già >75, phụ nữ có thai, trẻ <6 tháng)
- 10: cấp cứu

Chỉ Admin/Doctor/Nurse có quyền thay đổi priority.

---

## 5. Module Appointment

### 5.1. Mô hình capacity

**Bệnh nhân không chọn bác sĩ khi đặt lịch.** Slot có capacity = tổng số bác sĩ on-shift tại slot đó.

**Tính capacity của slot:**

```python
def get_slot_capacity(clinic_id, slot_start, slot_end):
    doctors_on_shift = count(
        shifts where clinic_id = clinic_id
                 and start_time <= slot_start
                 and end_time >= slot_end
                 and not on leave
    )
    booked = count(
        appointments where clinic_id = clinic_id
                       and scheduled_at in [slot_start, slot_end)
                       and status in ['scheduled', 'confirmed']
    )
    return doctors_on_shift - booked
```

### 5.2. Slot duration

Cấu hình per clinic trong settings: `appointment_slot_minutes` (mặc định 30 phút).

### 5.3. Status machine

```
scheduled → confirmed → checked_in → completed
    ↓           ↓           ↓
cancelled   cancelled    cancelled
    ↓
no_show (auto sau X phút quá scheduled_at)
```

- `scheduled`: vừa tạo (lễ tân đặt qua điện thoại hoặc bệnh nhân tự đặt sau này).
- `confirmed`: bệnh nhân xác nhận (qua SMS hoặc lễ tân gọi confirm).
- `checked_in`: bệnh nhân đã đến → tự động tạo Visit link về appointment.
- `completed`: Visit đã COMPLETED.
- `no_show`: cron job đánh dấu sau `appointment_no_show_minutes` (mặc định 30 phút quá giờ).
- `cancelled`: bệnh nhân/lễ tân hủy.

### 5.4. Smart queue: appointment vs walk-in

**Vấn đề:** Bệnh nhân A có hẹn 9h, bệnh nhân B walk-in lúc 8h30, bác sĩ rảnh lúc 8h45.

**Quy tắc:** Walk-in B chỉ được ưu tiên vào nếu visit dự kiến của B kết thúc trước `appointment_time_of_A - buffer`.

```
appointment_buffer_minutes = 15 (config)

if (estimated_end_of_walkin < appointment_time - buffer):
    walk-in được khám trước
else:
    appointment được khám trước
```

### 5.5. Optional pre-assign doctor

Khi tạo appointment, lễ tân có thể optionally chọn bác sĩ (nếu bệnh nhân yêu cầu BS cũ). `Visit.assigned_doctor_id` được set.

Khi check-in tạo Visit, copy `assigned_doctor_id` từ appointment sang.

---

## 6. Module Visit

### 6.1. Vai trò

Visit là **entity trung tâm** kết nối:
- Patient
- Appointment (nếu có)
- Doctor (sau khi nhận ca)
- VisitVitals (1-N)
- VisitService (1-N)
- Prescription (0-N)
- Invoice (1-1)

### 6.2. Cấu trúc

```
Visit
  - id (UUID)
  - clinic_id (UUID)
  - patient_id (UUID)
  - appointment_id (UUID, nullable — null cho walk-in)
  - doctor_id (UUID, nullable — set khi bác sĩ nhận ca)
  - assigned_doctor_id (UUID, nullable — pre-assign)
  - visit_number (string, unique trong clinic-day, vd: "20260426-001")
  - chief_complaint (text — lý do đến khám, lễ tân hoặc bác sĩ nhập)
  - notes (text — bác sĩ ghi vắn tắt)
  - status (enum: WAITING/IN_PROGRESS/AWAITING_PAYMENT/COMPLETED/CANCELLED)
  - priority (int, default 0)
  - is_follow_up (boolean — tái khám hay không, chỉ là flag thông tin)
  - check_in_at (timestamp)
  - consultation_started_at (timestamp, nullable)
  - consultation_ended_at (timestamp, nullable)
  - completed_at (timestamp, nullable)
  - cancellation_reason (text, nullable)
  - created_by (user_id)
  - audit fields
```

### 6.3. State machine

```
       ┌─→ CANCELLED (bất kỳ trạng thái nào trừ COMPLETED)
       │
WAITING ─── (BS nhận ca) ──→ IN_PROGRESS
                                    │
                                    └── (BS hoàn tất khám) ──→ AWAITING_PAYMENT
                                                                       │
                                                                       └── (đã thanh toán + cấp thuốc) ──→ COMPLETED
```

**Quy tắc:**
- Chỉ tạo VisitService/Prescription khi status `IN_PROGRESS` hoặc `AWAITING_PAYMENT`.
- Chỉ tạo Invoice khi status `AWAITING_PAYMENT` hoặc cao hơn.
- COMPLETED là trạng thái cuối, không quay lại được. Có sai sót thì phải void invoice + tạo entry điều chỉnh.

### 6.4. Visit number

Format đề xuất: `YYYYMMDD-NNN` (vd: `20260426-001`).

Reset counter mỗi ngày, scope per clinic. Dùng PostgreSQL sequence riêng hoặc lock + count trong transaction.

---

## 7. Module Vitals (Dynamic Form)

### 7.1. Vấn đề & cách tiếp cận

Mỗi specialty đo các chỉ số khác nhau:
- Phòng khám đa khoa: BP, mạch, nhiệt độ, cân, cao
- Nhi khoa: thêm vòng đầu
- Sản khoa: thêm fundal height, fetal heart rate
- Mắt: thị lực, nhãn áp
- YHCT: chất lưỡi, đặc điểm mạch

**Pattern thiết kế:** Pure JSONB + schema versioning.

### 7.2. Ba bảng chính

#### VitalFieldDefinition

Định nghĩa các field hiện hành của clinic.

```
VitalFieldDefinition
  - id (UUID)
  - clinic_id (UUID)
  - key (string, snake_case — vd: "systolic_bp", "vong_dau")
  - label (string — vd: "Huyết áp tâm thu", "Vòng đầu")
  - data_type (enum: "number", "integer", "text", "boolean", "select")
  - unit (string, nullable — "mmHg", "kg", "cm", "°C")
  - min_value (decimal, nullable)
  - max_value (decimal, nullable)
  - warning_min (decimal, nullable — ngưỡng cảnh báo dưới)
  - warning_max (decimal, nullable — ngưỡng cảnh báo trên)
  - decimal_places (int, nullable)
  - options (JSONB, nullable — cho data_type = "select")
  - is_required (boolean)
  - sort_order (int)
  - group_name (string, nullable — vd: "Sinh hiệu", "Nhân trắc")
  - placeholder (string, nullable)
  - help_text (string, nullable)
  - is_active (boolean — soft disable)
  - is_system (boolean — từ preset, không cho xóa cứng)
  - audit fields
  
UNIQUE (clinic_id, key) WHERE is_deleted = false
```

#### VitalSchemaVersion

Snapshot toàn bộ definition mỗi khi có thay đổi.

```
VitalSchemaVersion
  - id (UUID)
  - clinic_id (UUID)
  - version (int — auto-increment per clinic)
  - field_snapshot (JSONB — array of definitions)
  - changed_by (user_id)
  - changed_at (timestamp)
  - change_summary (text — vd: "Thêm field vong_dau")
```

#### VisitVitals

Bản ghi đo vitals của một lần đo.

```
VisitVitals
  - id (UUID)
  - clinic_id (UUID)
  - visit_id (UUID, FK)
  - recorded_by (user_id — thường là nurse)
  - recorded_at (timestamp)
  - schema_version (int — snapshot khi đo)
  - values (JSONB — vd: {"systolic_bp": 120, "diastolic_bp": 80, "pulse": 75})
  - notes (text, nullable)
  - audit fields

INDEX GIN ON values
INDEX (clinic_id, visit_id)
```

### 7.3. Schema evolution

**Quy tắc khi admin thay đổi field:**

| Hành động | Cho phép? | Hệ quả |
|---|---|---|
| Thêm field mới | ✓ | Tạo VitalSchemaVersion mới |
| Sửa label | ✓ | Tạo version mới, dữ liệu cũ giữ label cũ trong snapshot |
| Sửa unit, range, sort_order | ✓ | Tạo version mới |
| Sửa key | ✗ | Không cho — phải tạo field mới + ẩn field cũ |
| Sửa data_type | ✗ | Không cho — phải tạo field mới + ẩn field cũ |
| Disable field (`is_active = false`) | ✓ | Field không hiện trong form mới, dữ liệu cũ vẫn xem được |
| Xóa field | ✓ (soft) | Tương tự disable, không mất dữ liệu cũ |

### 7.4. Preset theo specialty

V1 cung cấp 5 preset:

1. **General** (đa khoa): BP, pulse, temp, weight, height, SpO2
2. **Dental** (RHM): BP, pulse, temp (đo trước thủ thuật)
3. **Pediatric** (nhi): weight, height, head_circumference, temperature, pulse
4. **Obstetric** (sản): BP, weight, fundal_height, fetal_heart_rate, gestational_age
5. **Dermatology** (da liễu): BP, weight (cho prescribe theo cân)

```
SystemVitalPreset
  - id, specialty_code, name
  - fields (JSONB — array of definitions)
  - is_default
```

Khi onboard clinic mới → chọn specialty → clone preset thành VitalFieldDefinition của clinic.

### 7.5. Validation runtime

Pydantic không thể declare static schema. Phải build validator runtime:

```python
def validate_vitals_payload(payload: dict, clinic_id: UUID) -> dict:
    definitions = get_active_definitions(clinic_id)
    errors = []
    
    for key in payload:
        if key not in {d.key for d in definitions}:
            errors.append(f"Unknown field: {key}")
    
    for d in definitions:
        if d.is_required and d.key not in payload:
            errors.append(f"Required field missing: {d.key}")
        
        if d.key in payload:
            value = payload[d.key]
            # type check, range check theo d.data_type, d.min_value, d.max_value
            ...
    
    if errors:
        raise ValidationError(errors)
    
    return payload
```

### 7.6. Cảnh báo bất thường

Sau khi nhập, frontend so giá trị với `warning_min`/`warning_max` của definition → hiển thị icon cảnh báo. Không block lưu, chỉ visual warning.

### 7.7. Một visit nhiều lần đo

`Visit 1 — N VisitVitals` — cho phép đo lại trong cùng visit (vd: huyết áp cao bất thường → cho nghỉ → đo lại).

Bác sĩ thấy tất cả lần đo, có thể đánh dấu lần đo nào là "primary".

### 7.8. Vai trò người dùng

| Role | Xem | Nhập | Sửa | Xóa |
|---|---|---|---|---|
| Doctor | ✓ | ✓ | ✓ | ✗ |
| Nurse | ✓ | ✓ | ✓ (trong ngày) | ✗ |
| Receptionist | ✗ | ✗ | ✗ | ✗ |
| Pharmacist | ✗ | ✗ | ✗ | ✗ |
| Admin | ✓ | ✓ | ✓ | ✓ (soft) |

---

## 8. Module Service Catalog

### 8.1. Cấu trúc

```
Service
  - id (UUID)
  - clinic_id (UUID)
  - code (string, unique trong clinic — vd: "KHAM001", "TIEM001")
  - name (string)
  - description (text, nullable)
  - category (string, nullable — "Khám", "Thủ thuật", "Xét nghiệm", ...)
  - default_price (decimal)
  - duration_minutes (int, nullable — thời gian thực hiện ước tính)
  - is_active (boolean)
  - sort_order (int)
  - audit fields
```

### 8.2. VisitService

Ghi nhận dịch vụ đã được cung cấp trong một visit.

```
VisitService
  - id (UUID)
  - clinic_id (UUID)
  - visit_id (UUID)
  - service_id (UUID)
  - performed_by (user_id — bác sĩ chỉ định, y tá thực hiện)
  - quantity (int, default 1)
  - unit_price (decimal — snapshot từ Service.default_price tại thời điểm tạo)
  - discount_amount (decimal, default 0)
  - discount_reason (text, nullable)
  - total_amount (decimal — computed: quantity * unit_price - discount)
  - notes (text, nullable)
  - status (enum: ordered/in_progress/completed/cancelled)
  - performed_at (timestamp, nullable)
  - audit fields
```

### 8.3. Workflow

1. Bác sĩ trong consultation chọn service từ catalog → tạo VisitService với status `ordered`.
2. Y tá thực hiện (nếu là thủ thuật) → đánh dấu `in_progress` → `completed`.
3. Khi tạo invoice, pull các VisitService có status `completed` (hoặc `ordered` cho service tự động hoàn thành như "Khám").

### 8.4. Override giá

Lễ tân có quyền `service.price_override` → có thể sửa `unit_price` khi tạo invoice (giảm giá đặc biệt). Bắt buộc nhập `discount_reason`. Audit log.

---

## 9. Module Prescription

### 9.1. Cấu trúc cốt lõi

```
Prescription
  - id (UUID)
  - clinic_id (UUID)
  - visit_id (UUID)
  - prescribed_by (user_id — doctor)
  - prescribed_at (timestamp)
  - dispense_type (enum: in_house/external/mixed)
  - status (enum: pending/dispensed/partially_dispensed/cancelled)
  - notes (text, nullable)
  - printed_at (timestamp, nullable)
  - audit fields
  
PrescriptionItem
  - id (UUID)
  - clinic_id (UUID)
  - prescription_id (UUID)
  - medicine_id (UUID, nullable — null nếu kê thuốc ngoài catalog)
  - medicine_name_text (string, nullable — dùng khi medicine_id null)
  - quantity (decimal — theo base_unit)
  - dosage_text (string — vd: "1 viên × 3 lần/ngày, sau ăn")
  - duration_days (int, nullable)
  - instructions (text, nullable — "Uống nhiều nước", "Không uống rượu bia")
  
  - dispense_source (enum: in_house/external)
  - in_house_status (enum, nullable: pending/reserved/dispensed/cancelled)
  - unit_price (decimal, nullable — chỉ khi in_house)
  - total_amount (decimal, nullable)
  
  - audit fields
```

### 9.2. Per-item dispense source

Một prescription có thể có cả thuốc in_house và external (mixed). Logic:

- Khi bác sĩ chọn medicine từ catalog có inventory → mặc định `in_house`.
- Khi medicine không có trong inventory hoặc kê text → mặc định `external`.
- Bác sĩ có thể override (bệnh nhân muốn ra ngoài mua dù phòng khám có).

### 9.3. Reserve/Dispense lifecycle (cho in_house items)

```
Bác sĩ kê đơn (in_house item)
        ↓
Reserve quantity từ inventory (FEFO)
in_house_status = 'reserved'
        ↓
        ├─→ Bệnh nhân thanh toán + dược sĩ cấp phát
        │       ↓
        │   Deduct thật từ batch
        │   in_house_status = 'dispensed'
        │
        └─→ Bệnh nhân hủy hoặc không lấy
                ↓
            Release reserve
            in_house_status = 'cancelled'
```

### 9.4. Logic kê thuốc

Khi bác sĩ kê thuốc từ catalog:

1. Search medicine trong catalog → hiện kết quả với indicator (có/không có trong kho).
2. Chọn medicine → app suggest dispense_source dựa trên inventory.
3. Bác sĩ nhập quantity → app check available quantity (= actual - reserved).
4. Nếu in_house và không đủ kho → cảnh báo "Kho chỉ còn X, có chuyển sang external không?"
5. Bác sĩ có thể bypass cảnh báo và để in_house (sẽ bị reject khi commit nếu không đủ).

### 9.5. In đơn thuốc

Cấu hình clinic settings:
- `prescription_print_mode`: "all" | "external_only" | "ask"
- `prescription_template`: layout đơn thuốc (header, font, kích thước)

In ra:
- Header: tên phòng khám, địa chỉ, SĐT, mã số thuế (nếu có)
- Bác sĩ kê: họ tên, chuyên môn
- Bệnh nhân: tên, tuổi, giới tính, mã BN
- Ngày kê
- Danh sách thuốc với liều dùng
- Chữ ký bác sĩ (text hoặc digital)

---

## 10. Module Inventory & Pharmacy

### 10.1. Ba cấp dữ liệu

```
Medicine (catalog dùng chung — master data hệ thống)
    │
    │  1-N
    ▼
InventoryItem (medicine cụ thể trong kho của một clinic)
    │
    │  1-N
    ▼
Batch (lô cụ thể của inventory item)
```

### 10.2. Medicine catalog

Master data, có thể không thuộc clinic nào cụ thể (system-level), hoặc clinic có thể tự thêm medicine không có trong master.

```
Medicine
  - id (UUID)
  - clinic_id (UUID, nullable — null = system-level)
  - code (string)
  - name (string — tên thương mại)
  - generic_name (string, nullable — tên hoạt chất)
  - strength (string — vd: "500mg")
  - form (enum: tablet/capsule/syrup/injection/cream/drops/...)
  - manufacturer (string, nullable)
  - atc_code (string, nullable)
  - registration_number (string, nullable)
  - base_unit (string — "viên", "ml", "ống", "tube")
  - pack_size (decimal — vd: 100 nếu 1 hộp = 100 viên)
  - pack_unit (string — vd: "hộp", "vỉ")
  - is_prescription_only (boolean)
  - is_controlled (boolean — thuốc kiểm soát đặc biệt)
  - storage_condition (text, nullable — "Bảo quản 2-8°C")
  - notes (text, nullable)
  - is_active (boolean)
  - audit fields
```

### 10.3. InventoryItem

Một medicine cụ thể trong kho của một clinic. Có giá nhập/giá bán riêng.

```
InventoryItem
  - id (UUID)
  - clinic_id (UUID)
  - medicine_id (UUID)
  - default_purchase_price (decimal)  -- giá nhập tham khảo
  - default_sale_price (decimal)       -- giá bán
  - reorder_point (decimal, nullable)  -- ngưỡng cảnh báo tồn thấp
  - reorder_quantity (decimal, nullable) -- số lượng đặt hàng đề xuất
  - location (string, nullable — vị trí kệ)
  - is_active (boolean)
  - audit fields
  
UNIQUE (clinic_id, medicine_id) WHERE is_deleted = false
```

### 10.4. Batch (Lô)

Stock thực tế tính ở cấp batch.

```
Batch
  - id (UUID)
  - clinic_id (UUID)
  - inventory_item_id (UUID)
  - batch_number (string)
  - manufacturing_date (date, nullable)
  - expiry_date (date)
  - received_date (date)
  - purchase_price (decimal)  -- giá nhập của lô này
  - initial_quantity (decimal)
  - actual_quantity (decimal)   -- số lượng thực tế còn lại
  - reserved_quantity (decimal) -- số đã reserve (chưa cấp thật)
  - is_recalled (boolean)        -- bị thu hồi
  - is_expired (boolean — generated từ expiry_date)
  - notes (text, nullable)
  - supplier_id (UUID, nullable)
  - audit fields

available_quantity = actual_quantity - reserved_quantity
```

### 10.5. FEFO logic

Khi cần lấy `N` đơn vị medicine M cho prescription:

```python
def reserve_for_prescription(item_id, needed_qty):
    batches = db.query(Batch).filter(
        Batch.inventory_item_id == item_id,
        Batch.actual_quantity - Batch.reserved_quantity > 0,
        Batch.is_recalled == False,
        Batch.expiry_date > today,
    ).order_by(
        Batch.expiry_date.asc(),    # FEFO
        Batch.received_date.asc(),  # tiebreaker
    ).with_for_update().all()
    
    reservations = []
    remaining = needed_qty
    
    for batch in batches:
        available = batch.actual_quantity - batch.reserved_quantity
        take = min(available, remaining)
        if take > 0:
            batch.reserved_quantity += take
            reservations.append((batch.id, take))
            remaining -= take
        if remaining == 0:
            break
    
    if remaining > 0:
        raise InsufficientStockError(...)
    
    return reservations  # [(batch_id, qty), ...]
```

Lưu reservations vào bảng `PrescriptionItemBatch` để khi dispense có thể trừ đúng batch.

### 10.6. StockMovement

Audit log cho mọi thay đổi tồn kho.

```
StockMovement
  - id (UUID)
  - clinic_id (UUID)
  - batch_id (UUID)
  - movement_type (enum)
  - quantity_delta (decimal — âm cho xuất, dương cho nhập)
  - quantity_before (decimal)
  - quantity_after (decimal)
  - reference_type (string, nullable — "purchase_order", "prescription", "adjustment")
  - reference_id (UUID, nullable)
  - reason (text, nullable)
  - performed_by (user_id)
  - performed_at (timestamp)
```

**Movement types:**
- `purchase_in`: nhập kho từ nhà cung cấp
- `prescription_out`: xuất theo đơn thuốc (in_house dispensed)
- `adjustment_increase`: điều chỉnh tăng (kiểm kê)
- `adjustment_decrease`: điều chỉnh giảm (kiểm kê)
- `transfer_out`/`transfer_in`: chuyển kho (phase sau)
- `expiry_writeoff`: hủy do hết hạn
- `damage_writeoff`: hủy do hỏng
- `recall_writeoff`: hủy do thu hồi
- `return_in`: trả lại từ bệnh nhân (nếu cho phép)

### 10.7. Cảnh báo

Background job định kỳ (hoặc trigger):

| Cảnh báo | Logic | Đối tượng nhận |
|---|---|---|
| Tồn thấp | `total_actual < reorder_point` | Pharmacist, Admin |
| Sắp hết hạn | `expiry_date - today < 90 days` (config) | Pharmacist, Admin |
| Hết hạn | `expiry_date < today` | Pharmacist, Admin |
| Lô bị thu hồi | `is_recalled = true` (manual flag) | Pharmacist, Admin |

### 10.8. Multi-unit handling

Một medicine có 2 đơn vị: `base_unit` (viên) và `pack_unit` (hộp), với `pack_size` (100).

- **Tồn kho luôn tính theo `base_unit`** (viên).
- **Giá có thể theo cả 2** — UI hiển thị "150,000đ/hộp ≈ 1,500đ/viên".
- **Nhập kho theo pack** → app convert: 5 hộp × 100 viên = 500 viên.
- **Xuất theo prescription thường theo viên**.
- **Báo cáo có thể quy đổi cả 2** tùy nhu cầu.

### 10.9. Pharmacy dispense workflow

1. Pharmacist mở "Pending dispense" → list các Prescription có in_house items chưa dispense.
2. Click vào prescription → thấy chi tiết:
   - Item, qty cần
   - Batch đã reserve (theo FEFO)
   - Tổng tiền
3. Pharmacist kiểm tra thực tế kho.
4. Nếu đúng → click "Dispense" → batch bị deduct thật, status = `dispensed`, ghi StockMovement.
5. Nếu cần substitute batch (batch reserve bị hỏng) → click "Substitute" → chọn batch khác → release reserve cũ + reserve batch mới.
6. In nhãn thuốc (label) cho từng item nếu cần.

### 10.10. Stock take (kiểm kê) — phase sau

Tính năng kiểm kê kho định kỳ. V1 có thể bỏ qua, dùng `adjustment` thủ công.

---

## 11. Module Billing & Payment

### 11.1. Cấu trúc Invoice

```
Invoice
  - id (UUID)
  - clinic_id (UUID)
  - visit_id (UUID, FK)
  - invoice_number (string, unique trong clinic — "INV-20260426-001")
  - patient_id (UUID — denormalized từ visit để query nhanh)
  - subtotal (decimal — tổng các item trước discount/tax)
  - total_discount (decimal)
  - total_tax (decimal — phase sau, v1 = 0)
  - total_amount (decimal — sau discount, sau tax)
  - paid_amount (decimal — tổng đã thanh toán)
  - balance (decimal — total - paid)
  - status (enum: draft/pending/partially_paid/paid/cancelled/refunded)
  - issued_at (timestamp)
  - paid_at (timestamp, nullable)
  - cancelled_at, cancelled_by, cancellation_reason
  - notes (text, nullable)
  - audit fields

InvoiceItem
  - id (UUID)
  - clinic_id (UUID)
  - invoice_id (UUID)
  - item_type (enum: service/medicine/other)
  - reference_type (string, nullable — "visit_service", "prescription_item")
  - reference_id (UUID, nullable)
  - description (string)
  - quantity (decimal)
  - unit_price (decimal)
  - discount_amount (decimal)
  - tax_amount (decimal — phase sau)
  - total (decimal)
  - audit fields

Payment
  - id (UUID)
  - clinic_id (UUID)
  - invoice_id (UUID)
  - payment_method (enum: cash/card/bank_transfer/ewallet)
  - amount (decimal)
  - paid_at (timestamp)
  - reference_number (string, nullable — số giao dịch nếu là chuyển khoản/thẻ)
  - notes (text, nullable)
  - received_by (user_id)
  - audit fields
```

### 11.2. Logic tạo invoice

Khi visit chuyển sang `AWAITING_PAYMENT`:

```python
def create_invoice_from_visit(visit_id):
    visit = get_visit(visit_id)
    items = []
    
    # 1. Pull VisitService completed
    for vs in visit.services where status in ['completed', 'ordered']:
        items.append(InvoiceItem(
            item_type='service',
            reference_type='visit_service',
            reference_id=vs.id,
            description=vs.service.name,
            quantity=vs.quantity,
            unit_price=vs.unit_price,  # snapshot
            discount_amount=vs.discount_amount,
            total=vs.total_amount,
        ))
    
    # 2. Pull Prescription items in_house đã reserve hoặc dispensed
    for pi in visit.prescription.items where dispense_source = 'in_house':
        items.append(InvoiceItem(
            item_type='medicine',
            reference_type='prescription_item',
            reference_id=pi.id,
            description=pi.medicine.name,
            quantity=pi.quantity,
            unit_price=pi.unit_price,
            total=pi.total_amount,
        ))
    
    invoice = Invoice(items=items, status='pending', ...)
    return invoice
```

### 11.3. Multi-payment

Một invoice có thể có nhiều `Payment` (trả nhiều lần, nhiều phương thức).

```
Invoice.paid_amount = SUM(payments.amount WHERE not deleted)
Invoice.balance = total_amount - paid_amount

if balance == 0: status = 'paid'
elif paid_amount > 0: status = 'partially_paid'
else: status = 'pending'
```

### 11.4. Discount

**Per-item discount:** ở `InvoiceItem.discount_amount` + `discount_reason`.

**Per-invoice discount:** ở `Invoice.total_discount` (giảm trực tiếp, không phân bổ về item).

Cả hai đều cần `reason` nếu vượt ngưỡng config (vd: > 10% giá trị).

### 11.5. Sửa & hủy invoice

| Status | Action cho phép |
|---|---|
| `draft` | Sửa thoải mái, log từng thay đổi |
| `pending` | Sửa thoải mái nếu chưa có payment, log |
| `partially_paid` | Không sửa item. Có thể thêm Payment, void |
| `paid` | **Không sửa.** Chỉ void/refund |
| `cancelled` | Read-only |
| `refunded` | Read-only |

**Void invoice:** tạo entry điều chỉnh — sinh `Invoice` mới với amount âm, hoặc field `voided_by_invoice_id` link 2 chiều. Audit log.

**Refund:** tạo `Payment` với amount âm + lý do, có thể partial.

### 11.6. Invoice number

Format: `INV-YYYYMMDD-NNN` (vd: `INV-20260426-001`).

Reset counter mỗi ngày, scope per clinic.

---

## 12. Module HR, Schedule & Attendance

### 12.1. Tách rõ 2 khái niệm

- **Schedule (kế hoạch):** ai làm ca nào → input để xếp lịch hẹn.
- **Attendance (thực tế):** ai đã có mặt → input để tính lương.

### 12.2. Shift Templates

```
ShiftTemplate
  - id (UUID)
  - clinic_id (UUID)
  - name (string — "Ca sáng", "Ca chiều", "Ca tối")
  - start_time (time — 07:30)
  - end_time (time — 12:00)
  - is_active (boolean)
  - audit fields
```

### 12.3. Shift cụ thể

```
Shift
  - id (UUID)
  - clinic_id (UUID)
  - user_id (UUID)
  - shift_template_id (UUID, nullable — null nếu shift custom)
  - shift_date (date)
  - start_time (time)
  - end_time (time)
  - role_in_shift (string — "Doctor", "Nurse" — nếu user có nhiều role)
  - status (enum: scheduled/cancelled/completed)
  - notes (text, nullable)
  - audit fields
  
UNIQUE (clinic_id, user_id, shift_date, start_time)
```

### 12.4. Recurring Schedule

```
RecurringSchedule
  - id (UUID)
  - clinic_id (UUID)
  - user_id (UUID)
  - shift_template_id (UUID)
  - days_of_week (int[] — [1,3,5] = thứ 2,4,6)
  - effective_from (date)
  - effective_to (date, nullable)
  - is_active (boolean)
  - audit fields
```

Background job sinh Shift cụ thể từ recurring schedule (cron hoặc on-demand).

### 12.5. Leave Request

```
LeaveRequest
  - id (UUID)
  - clinic_id (UUID)
  - user_id (UUID)
  - leave_type (enum: sick/personal/vacation/other)
  - start_date (date)
  - end_date (date)
  - reason (text)
  - status (enum: pending/approved/rejected)
  - approved_by (user_id, nullable)
  - approved_at (timestamp, nullable)
  - audit fields
```

Khi approved → Shift trong khoảng đó tự động `cancelled` (hoặc `on_leave` để phân biệt).

### 12.6. Attendance / Time Log

```
TimeLog
  - id (UUID)
  - clinic_id (UUID)
  - user_id (UUID)
  - shift_id (UUID, nullable — link với shift kế hoạch)
  - check_in_at (timestamp)
  - check_out_at (timestamp, nullable)
  - check_in_method (enum: manual/pin/qr/biometric)
  - check_in_location (string, nullable — IP, device ID)
  - notes (text, nullable)
  - audit fields
```

**Tính toán:**
- Tổng giờ làm = check_out - check_in
- Đi muộn = max(0, check_in - shift.start_time)
- Về sớm = max(0, shift.end_time - check_out)
- OT = max(0, check_out - shift.end_time)

### 12.7. Lương

V1 không tính lương trong app. Cung cấp **export** sang Excel/CSV để kế toán xử lý:
- TimeLog của tất cả nhân viên trong khoảng thời gian
- Tổng giờ làm, đi muộn, OT
- (Phase sau): commission cho bác sĩ

---

## 13. Module Auth & RBAC

### 13.1. Authentication

- JWT (access + refresh).
- Access token: 15 phút.
- Refresh token: 7-30 ngày, có thể revoke.
- Password: bcrypt với cost 12+.
- Lockout sau N lần sai (config, vd 5 lần / 15 phút).

### 13.2. User

```
User
  - id (UUID)
  - clinic_id (UUID)
  - username (string, unique trong clinic)
  - email (string, nullable, unique trong clinic nếu có)
  - phone (string, nullable)
  - password_hash (string)
  - full_name (string)
  - is_active (boolean)
  - is_locked (boolean)
  - last_login_at (timestamp, nullable)
  - failed_login_count (int)
  - password_changed_at (timestamp)
  - audit fields
```

### 13.3. Role

```
Role
  - id (UUID)
  - clinic_id (UUID, nullable — null = system role)
  - code (string — "admin", "doctor", "nurse", "pharmacist", "receptionist")
  - name (string)
  - is_system (boolean — không cho xóa)
  - audit fields

UserRole
  - user_id, role_id, assigned_at, assigned_by
```

User có thể có **nhiều role** (multi-role). Vd: phòng khám nhỏ, một người vừa là Receptionist vừa là Pharmacist.

### 13.4. Permission

```
Permission
  - code (string — "patient.read", "patient.write", "invoice.void", ...)
  - description

RolePermission
  - role_id, permission_code

UserExtraPermission
  - user_id, permission_code, type (grant/deny)
```

User permission cuối cùng = (Σ permissions của các roles) + extra grants - extra denies.

### 13.5. Permission catalog (đề xuất v1)

```
# Patient
patient.read
patient.write
patient.merge
patient.delete

# Visit
visit.read
visit.write
visit.cancel

# Vitals
vital.read
vital.write
vital.delete

# Service
service.catalog.manage
service.perform

# Prescription
prescription.write
prescription.cancel

# Pharmacy
pharmacy.dispense
pharmacy.substitute_batch
pharmacy.adjust_stock

# Inventory
inventory.read
inventory.manage_catalog
inventory.purchase_in
inventory.adjust

# Billing
invoice.create
invoice.modify
invoice.void
invoice.refund
payment.receive

# HR
shift.manage
attendance.manage
leave.approve

# RBAC
user.manage
role.manage

# Reports
report.view
report.financial

# Settings
settings.clinic
settings.vital_schema
settings.service_catalog
```

### 13.6. Default role-permission mapping

| Permission | Admin | Doctor | Nurse | Pharmacist | Receptionist |
|---|---|---|---|---|---|
| patient.read | ✓ | ✓ | ✓ | ✓ | ✓ |
| patient.write | ✓ | ✓ | ✓ | | ✓ |
| visit.write | ✓ | ✓ | ✓ | | ✓ |
| vital.write | ✓ | ✓ | ✓ | | |
| service.perform | ✓ | ✓ | ✓ | | |
| prescription.write | ✓ | ✓ | | | |
| pharmacy.dispense | ✓ | | | ✓ | |
| inventory.manage_catalog | ✓ | | | ✓ | |
| invoice.create | ✓ | | | | ✓ |
| invoice.void | ✓ | | | | |
| user.manage | ✓ | | | | |
| settings.clinic | ✓ | | | | |
| report.financial | ✓ | | | | |

### 13.7. RLS (Row-Level Security)

PostgreSQL RLS bật cho mọi bảng có `clinic_id`:

```sql
ALTER TABLE patient ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON patient
  FOR ALL
  USING (clinic_id = current_setting('app.current_clinic_id')::uuid);
```

Application middleware set:
```sql
SET LOCAL app.current_clinic_id = '...';
SET LOCAL app.current_user_id = '...';
```

ở đầu mỗi request, sau khi parse JWT.

---

## 14. Module Reporting

### 14.1. Báo cáo v1

| Báo cáo | Mô tả | Filter |
|---|---|---|
| Doanh thu theo ngày | Tổng invoice paid theo ngày | khoảng thời gian |
| Doanh thu theo bác sĩ | Tổng invoice paid breakdown theo doctor_id | khoảng thời gian |
| Lượt khám | Số visit theo ngày, theo bác sĩ | khoảng thời gian |
| Top dịch vụ | Top N service được cung cấp nhiều nhất | khoảng thời gian, theo qty hoặc revenue |
| Top thuốc | Top N medicine bán chạy | khoảng thời gian |
| Tồn kho hiện tại | Tồn kho từng item, breakdown theo batch | snapshot |
| Cảnh báo kho | Items low stock, near expiry, expired | snapshot |
| Công nợ | Invoices có balance > 0 | snapshot |
| Chấm công | TimeLog của nhân viên | tháng, theo user |

### 14.2. Implementation

- Module riêng `reporting` để tách query phức tạp.
- Có thể cache report frequently-accessed (Redis) — phase sau.
- Export Excel/CSV cho mọi báo cáo.
- V1 không có dashboard real-time, các báo cáo là pull-based on-demand.

---

## 15. Cross-cutting Concerns

### 15.1. Audit Log

```
AuditLog
  - id (UUID)
  - clinic_id (UUID, nullable — null cho action system-level)
  - user_id (UUID, nullable — null cho action system)
  - action (string — "create", "update", "delete", "view")
  - entity_type (string — "patient", "invoice", ...)
  - entity_id (UUID)
  - old_data (JSONB, nullable)
  - new_data (JSONB, nullable)
  - changed_fields (string[], nullable)
  - ip_address (string)
  - user_agent (string)
  - created_at (timestamp)
```

**Implementation:** decorator hoặc SQLAlchemy event hook tự động ghi audit log khi insert/update/delete entity được mark `auditable`.

**Query log đọc dữ liệu nhạy cảm:** cho `Patient.read`, `Visit.read` (full), `Prescription.read` — async ghi log không block response.

### 15.2. Settings per Clinic

Bảng `ClinicSettings` key-value JSON:

```
ClinicSettings
  - clinic_id (UUID, PK)
  - settings (JSONB)
  - updated_by (user_id)
  - updated_at (timestamp)
```

Các keys (ví dụ):

```json
{
  "general": {
    "name": "Phòng khám ABC",
    "address": "...",
    "phone": "...",
    "email": "...",
    "tax_code": "..."
  },
  "operating_hours": {
    "monday": { "open": "07:30", "close": "20:00" },
    ...
  },
  "appointment": {
    "slot_duration_minutes": 30,
    "buffer_minutes": 15,
    "no_show_minutes": 30,
    "advance_booking_days": 30
  },
  "queue": {
    "require_vitals_before_consultation": false
  },
  "inventory": {
    "near_expiry_days": 90,
    "low_stock_alert": true
  },
  "prescription": {
    "print_mode": "all"
  },
  "billing": {
    "discount_threshold_require_reason": 10,
    "invoice_template": "default"
  },
  "specialty": "general"
}
```

### 15.3. Tenant Onboarding Flow

```
1. Đăng ký clinic mới (qua landing page hoặc admin nội bộ tạo)
        ↓
2. Tạo Clinic record + tài khoản Admin đầu tiên
        ↓
3. Wizard onboarding:
   a. Chọn specialty → load preset (vital schema, service template)
   b. Nhập thông tin clinic (tên, địa chỉ, giờ làm)
   c. Tạo các user: bác sĩ, y tá, lễ tân, dược sĩ
   d. Setup shift template
   e. Import inventory ban đầu (CSV upload optional)
   f. Setup service catalog (từ template hoặc tự nhập)
        ↓
4. Clinic sẵn sàng vận hành
```

### 15.4. Notification (in-app v1)

```
Notification
  - id (UUID)
  - clinic_id (UUID)
  - user_id (UUID — người nhận)
  - type (string — "low_stock", "near_expiry", "appointment_reminder", ...)
  - title (string)
  - body (text)
  - reference_type, reference_id (link tới entity)
  - is_read (boolean)
  - read_at (timestamp, nullable)
  - created_at (timestamp)
```

**Triggers:**
- Low stock: cron hằng ngày
- Near expiry: cron hằng tuần
- Appointment reminder: cron hằng giờ (T-24h và T-2h)
- Invoice unpaid: cron hằng ngày sau N ngày

Phase 2: gửi qua SMS/Zalo/Email.

### 15.5. Data Security & Privacy

**Tuân thủ Nghị định 13/2023/NĐ-CP:**

- Mã hóa at-rest cho database (TDE hoặc filesystem encryption).
- TLS bắt buộc cho mọi connection.
- Audit log đầy đủ.
- Quyền truy cập theo nguyên tắc least-privilege.
- Backup mã hóa.
- Xóa dữ liệu khi tenant hủy hợp đồng (sau thời gian giữ theo luật).

**PII/PHI handling:**

- Không log raw PII trong application log.
- Mask SĐT/CCCD trong UI cho role không đủ quyền.
- Khi export data, có audit log + tùy chọn mã hóa file.

---

## 16. Offline Strategy (Tauri Client)

### 16.1. Mức độ offline

**Read offline (full):** mọi dữ liệu cache local SQLite, xem được khi mất mạng.

**Write offline (queued):** một số thao tác cho phép tạo offline, queue lại push khi online:

| Thao tác | Offline? |
|---|---|
| Đăng ký bệnh nhân mới | ✓ |
| Tạo Visit (walk-in) | ✓ |
| Nhập VisitVitals | ✓ |
| Tạo Appointment | ✓ |
| Bác sĩ chọn VisitService | ✓ |
| Bác sĩ kê Prescription (cả in_house và external) | ✓ |
| Nhập TimeLog (chấm công) | ✓ |
| Hoàn tất visit (status COMPLETED) | ✓ |
| **Reserve inventory cho prescription in_house** | ✗ phải online |
| **Dispense thuốc (deduct stock thật)** | ✗ phải online |
| **Tạo Invoice + Payment** | ✗ phải online (vì liên quan stock) |

### 16.2. Conflict resolution

- **UUID client-side:** Tauri tạo UUID v7 khi tạo entity offline → không conflict ID.
- **Optimistic lock:** mỗi entity có cột `version` (int). Khi sync, server check version → reject nếu conflict.
- **Last-write-wins ở field level** cho các entity ít quan trọng.
- **Reject + báo lỗi** cho entity quan trọng (Prescription, Invoice) → user phải resolve manually.

### 16.3. Sync mechanism

```
┌─────────────┐         ┌──────────────┐
│ Tauri App   │ ──────→ │ Local SQLite │
│             │         │              │
│             │ ←────── │              │
└─────────────┘         └──────────────┘
       │
       │  background sync khi có mạng
       ▼
┌─────────────┐
│ Sync Engine │
│  - Push     │
│  - Pull     │
│  - Resolve  │
└─────────────┘
       │
       ▼
┌─────────────┐
│  Backend    │
│   FastAPI   │
└─────────────┘
```

- Push: gửi local changes lên server.
- Pull: nhận server changes mới hơn `last_sync_at`.
- Resolve: xử lý conflict.

### 16.4. Hardware integration

Tauri cho phép native access:
- POS printer (ESC/POS protocol) — in hóa đơn, đơn thuốc, label thuốc.
- Barcode scanner — scan mã thuốc, mã bệnh nhân.
- (Phase sau) Đầu đọc CCCD, máy đo huyết áp Bluetooth, cân điện tử.

---

## 17. Tổng kết các quyết định nghiệp vụ

| Quyết định | Lựa chọn |
|---|---|
| Multi-tenancy | Shared DB + clinic_id + RLS |
| Tenant model | 1 clinic = 1 tenant (chưa hỗ trợ chuỗi) |
| BHYT | Bỏ qua v1 |
| EMR đầy đủ | Bỏ qua v1 (chỉ vitals + notes) |
| Specialty per clinic | 1 clinic chuyên 1 mảng |
| Vitals form | Dynamic, JSONB + schema versioning |
| Vital presets | 5 specialty: general, dental, pediatric, obstetric, dermatology |
| Patient ID | UUID + patient_code dễ đọc, phone không unique |
| Guardian relationship | Có |
| Visit vs Appointment | 2 entity tách biệt, link 1-1 optional |
| Walk-in + Appointment | Cùng tồn tại, smart queue |
| Doctor selection khi đặt lịch | KHÔNG (bệnh nhân không chọn bác sĩ) |
| Pre-assign doctor | Optional khi bệnh nhân yêu cầu |
| Multi-doctor | Có |
| Vitals nhập bởi | Y tá (chính), bác sĩ (cũng được) |
| Service catalog | Đồng giá per clinic |
| Đa giá theo bác sĩ | Không |
| Tái khám discount | Không tự động |
| Patient tag/membership | Không v1 |
| Package/liệu trình | Không v1 |
| Prescription dispense source | Per-item (in_house/external mixed) |
| FIFO vs FEFO | FEFO cho thuốc |
| Inventory deduction timing | Reserve khi kê đơn, deduct khi dispense |
| Multi-unit | base_unit + pack_size |
| Invoice editing | Draft sửa, paid chỉ void/refund |
| Multi-payment | Có |
| Discount với reason | Có (per-item và per-invoice) |
| Roles | Admin, Doctor, Nurse, Pharmacist, Receptionist |
| Multi-role per user | Có |
| RBAC | Role + Permission + extra/denied |
| Schedule vs Attendance | Tách 2 module |
| Lương trong app | Không (chỉ export) |
| Commission cho bác sĩ | Phase sau |
| Audit log | Đầy đủ, ghi cả read sensitive |
| Soft delete | Bắt buộc, không hard delete |
| Notification | In-app v1, SMS phase 2 |
| Offline read | Có |
| Offline write | Có (trừ inventory deduction) |
| UUID client-side | Có (UUIDv7) |
| Optimistic lock | Có (version column) |

---

## 18. Roadmap đề xuất

### Phase 1 (MVP — 4-6 tháng)

**Sprint 0-1: Foundation**
- Setup project structure
- Auth + JWT
- Tenancy + RLS
- Audit log + Soft delete base classes
- Migration với Alembic
- Test infrastructure

**Sprint 2-3: Core entities**
- User + Role + Permission
- Patient + Guardian
- Clinic settings
- Tenant onboarding

**Sprint 4-5: Visit workflow**
- Visit + state machine
- Appointment + Queue
- Vitals dynamic form (3 bảng + preset)

**Sprint 6-7: Service & Prescription**
- Service catalog
- VisitService
- Medicine catalog (master data)
- Prescription + per-item dispense

**Sprint 8-9: Inventory**
- InventoryItem + Batch
- StockMovement
- FEFO logic + Reserve/Dispense
- Cảnh báo

**Sprint 10-11: Billing**
- Invoice + Multi-payment
- Discount + Void/Refund
- Print invoice (POS)

**Sprint 12-13: HR**
- Shift + ShiftTemplate + RecurringSchedule
- Attendance + TimeLog
- Leave Request

**Sprint 14: Reporting + Polish**
- 8 báo cáo cơ bản
- Export Excel/CSV
- UI polish, bug fixing

**Sprint 15-16: Tauri client + Offline**
- Tauri app shell
- Local SQLite cache
- Sync engine
- Hardware integration (printer, scanner)

### Phase 2 (sau MVP)

- EMR đầy đủ (theo specialty)
- Commission cho bác sĩ
- BHYT integration (nếu cần)
- SMS/Zalo notification
- Patient self-portal
- Multi-clinic per tenant (chuỗi)
- Stock take (kiểm kê)
- Báo cáo dashboard real-time
- Mobile app cho bác sĩ
- Tích hợp thêm hardware (đo huyết áp Bluetooth, đầu đọc CCCD)

---

## 19. Bước tiếp theo

Sau khi business analysis được duyệt, các bước tiếp theo:

1. **Database schema chi tiết** — toàn bộ entity, relationships, indexes, RLS policies
2. **API contract** — danh sách endpoints, request/response schemas
3. **UI/UX wireframe** — flow từng màn hình
4. **Infrastructure plan** — deployment, CI/CD, monitoring, backup

---

*Tài liệu này là kết quả phân tích nghiệp vụ giai đoạn đầu, dùng làm tham chiếu chính cho thiết kế kỹ thuật và phát triển. Mọi quyết định trong tài liệu cần được xác nhận lại với stakeholders thực tế (chủ phòng khám, bác sĩ, y tá) trước khi triển khai.*
