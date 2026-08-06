# Thiết Kế Chi Tiết Tính Năng: Lương theo buổi/ca + Chiết khấu theo nhân sự

**Dự án:** Clinic CMS
**Task:** TASK-138
**Phiên bản:** 1.0
**Ngày:** 2026-08-07
**Người thực hiện:** Implementation/Review/Test Agents
**Trạng thái:** Đã hoàn thành
**Tài liệu liên quan:** TASK-128 (payroll engine), TASK-127 (chấm công ca/ngày), implementation-plan.md

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-08-07 | Phiên bản đầu tiên sau triển khai và kiểm thử hoàn tất |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Danh sách API](#3-danh-sách-api)
- [4. Chi tiết từng API](#4-chi-tiết-từng-api)
- [5. Cấu trúc cơ sở dữ liệu](#5-cấu-trúc-cơ-sở-dữ-liệu)
- [6. Quy tắc nghiệp vụ](#6-quy-tắc-nghiệp-vụ)
- [7. Xử lý lỗi](#7-xử-lỗi)
- [8. Ghi chú và lưu ý khi kiểm thử](#8-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

TASK-138 mở rộng nền payroll hiện tại (TASK-128) với hai khả năng mới:

1. **Hai kiểu tính lương mới:**
   - `per_session` (theo buổi/ngày công): lương = đơn giá buổi × số buổi làm thực tế từ lưới chấm công
   - `per_shift` (theo ca): lương = đơn giá ca × số ca hoàn thành trong kỳ

2. **Chiết khấu (commission) cấu hình theo từng nhân sự:**
   - Mỗi nhân sự có thể có tỷ lệ chiết khấu riêng cho mỗi loại thủ thuật (service_type) và riêng cho thuốc
   - Nếu không cấu hình tỷ lệ riêng, tự động fallback về tỷ lệ chung của phòng khám
   - Payslip truy vết rõ tỷ lệ nào được áp dụng (riêng hay chung) và tại sao

Điều này cho phép quản lý lương linh hoạt hơn, đặc biệt là cho các đội y tá, điều dưỡng, và có thể chia chiết khấu khác nhau cho các bác sĩ.

### 1.2 Phạm vi

**Bao gồm:**
- Kiểu lương `per_session`: tính từ lưới `AttendanceDay` (nửa ngày = 0.5, toàn ngày = 1.0), không fallback sang dữ liệu cũ nếu không có lưới
- Kiểu lương `per_shift`: tính từ số `Shift` có status='completed' trong kỳ, không tính OT
- Cấu hình chiết khấu per-staff qua API: tạo/sửa/xóa rule riêng cho mỗi nhân sự, từng loại DV + rate thuốc
- Payslip truy vết: hiển thị đơn giá buổi/ca, số buổi/ca, tỷ lệ commission áp dụng (riêng hay chung), nguồn rate
- Claw-back (hoàn chiết khấu): tự động áp dụng tỷ lệ override của nhân sự nếu có, fallback tỷ lệ chung

**Không bao gồm:**
- UI chấm công buổi riêng (sáng/chiều/tối) — "buổi" là ngày công admin tick trên lưới chấm công (TASK-127)
- OT cho kiểu lương mới (OT chỉ áp dụng monthly/hourly)
- Tự động commission cho nhân sự KHÔNG có tài khoản bác sĩ (ràng buộc từ TASK-128): nếu cần chia tiền phải dùng `payroll_adjustment` thủ công

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Admin phòng khám** | Quản lý cấu hình kiểu lương và chiết khấu per-staff, chốt lương cuối tháng |
| **Bác sĩ / Điều dưỡng / Y tá** | Xem payslip riêng, thấy chi tiết lương và chiết khấu áp dụng |
| **Hệ thống chấm công** | Cung cấp dữ liệu `AttendanceDay` (TASK-127) + `Shift` cho engine tính lương |
| **Engine payroll (BE)** | Tính lương kỳ dựa kiểu lương + dữ liệu chấm công, resolve tỷ lệ commission |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
┌─ Admin cấu hình lương nhân sự ─┐
│  • Chọn kiểu lương: per_session | per_shift
│  • Nhập đơn giá buổi/ca
│  • Cấu hình chiết khấu riêng (service_type + thuốc)
└──────────────┬─────────────────┘
               ▼
        [StaffProfile] ← pay_type, session_rate, shift_rate
        [CommissionRule] ← staff_id IS NOT NULL (override)

Admin chốt lương tháng (tháng YYYY-MM):
               │
               ▼
    [Engine payroll._compute_one()]
    ├─ Nhánh per_session:
    │  └─ session_rate × attendance_worked_days (từ AttendanceDay grid)
    ├─ Nhánh per_shift:
    │  └─ shift_rate × count(Shift.status='completed')
    ├─ monthly/hourly (cũ — không đổi)
    └─ Cộng: allowance, attendance_bonus, late_penalty (áp dụng mọi kiểu)
               │
               ▼
    [Engine commission.aggregate_commission()]
    ├─ Resolve tỷ lệ per-staff (staff_id override)
    ├─ Fallback tỷ lệ chung (staff_id NULL)
    └─ Tính commission thủ thuật + thuốc, theo tỷ lệ đã resolve
               │
               ▼
    [Payslip] ghi nhận:
    ├─ base_earned (lương cơ bản từ kiểu lương)
    ├─ procedure_commission / medicine_commission
    ├─ procedure_rate_percent / procedure_rate_source (riêng/chung)
    ├─ medicine_rate_percent / medicine_rate_source (riêng/chung)
    ├─ session_rate / shift_rate / completed_shifts (truy vết)
    └─ Hiển thị UI: [rate] · [nguồn]
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Admin cấu hình kiểu lương | Chọn `per_session`, `per_shift`, `monthly`, hoặc `hourly` cho mỗi nhân sự; nhập đơn giá tương ứng (session_rate hoặc shift_rate) |
| 2 | Admin cấu hình chiết khấu per-staff (tùy chọn) | Tạo rule (staff_id ≠ NULL, loại DV, tỷ lệ) override tỷ lệ chung; không cấu hình = áp dụng tỷ lệ chung |
| 3 | Quá trình chấm công tháng | Admin/hệ thống tích vào lưới `AttendanceDay` mỗi ngày (present=1, half=0.5); hoặc tạo/hoàn thành `Shift` từ lịch làm |
| 4 | Admin chốt lương tháng | Gọi API `/api/v1/hr/payroll?month=YYYY-MM` → engine tính lương |
| 5 | Engine tính base_earned | Theo kiểu lương: `per_session` dùng attendance_worked_days, `per_shift` dùng completed_shifts, `monthly`/`hourly` dùng cách cũ |
| 6 | Engine resolve tỷ lệ commission | Tìm rule (staff_id = this_staff) với (service_type_id) → không có thì tìm rule (staff_id = NULL, service_type_id) → không có thì 0% |
| 7 | Engine tính commission | Với mỗi doanh thu (visit_service / prescription_item), apply tỷ lệ đã resolve; tính tổng procedure + medicine |
| 8 | Payslip ghi nhận rate/source | Mỗi component (procedure, medicine) ghi lại tỷ lệ % và nguồn ("staff_override" hay "clinic_default") |
| 9 | FE hiển thị payslip | Hiển thị chi tiết lương + badge tỷ lệ commission ("15% · tỷ lệ riêng" hay "5% · tỷ lệ chung") |

---

## 3. Danh sách API

Tất cả API đều yêu cầu xác thực qua header:
```
Authorization: Bearer {token}
```

Quyền cần có: `payroll.manage` (cho tất cả thao tác cấu hình)

**Đường dẫn gốc (Base Path):** `/api/v1/hr`

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt |
|-----|------------|-----------|--------------|
| 1 | GET | `/hr/commission-rules?staff_id=...` | Lấy danh sách commission rule (clinic-wide + per-staff), tùy chọn lọc theo staff_id |
| 2 | POST | `/hr/commission-rules` | Tạo rule chiết khấu mới (clinic-wide nếu staff_id=NULL, per-staff nếu có staff_id) |
| 3 | PATCH | `/hr/commission-rules/{id}` | Sửa tỷ lệ hoặc trạng thái is_active; staff_id không thay đổi được |
| 4 | DELETE | `/hr/commission-rules/{id}` | Xóa rule (nhân sự revert về tỷ lệ chung hoặc 0%) |
| 5 | GET | `/hr/payroll?month=YYYY-MM` | Lấy danh sách payslip tháng (bao gồm các trường rate/source mới) |

---

## 4. Chi tiết từng API

### 4.1 Lấy danh sách commission rules

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/hr/commission-rules` |
| **Mô tả** | Lấy toàn bộ commission rule trong phòng khám (clinic-wide + per-staff), tùy chọn lọc theo staff_id |
| **Xác thực** | Bắt buộc; quyền `payroll.manage` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `staff_id` | UUID | Không | Nếu truyền, chỉ trả rule riêng (staff_id ≠ NULL) và rule chung (staff_id = NULL) cho nhân sự đó. Nếu bỏ trống, trả tất cả rule (clinic-wide + tất cả per-staff) | — |

**Ví dụ:**
- `GET /api/v1/hr/commission-rules` → trả cả rule chung và tất cả per-staff
- `GET /api/v1/hr/commission-rules?staff_id=a1b2c3d4-...` → trả rule chung + per-staff của nhân sự đó

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "code": "00",
  "message": "Success",
  "data": [
    {
      "id": "rule-001-uuid",
      "rule_type": "service_type",
      "service_type_id": "service-type-001-uuid",
      "staff_id": null,
      "rate_percent": 10.0,
      "is_active": true,
      "created_at": "2026-08-01T10:00:00Z",
      "updated_at": "2026-08-01T10:00:00Z"
    },
    {
      "id": "rule-002-uuid",
      "rule_type": "service_type",
      "service_type_id": "service-type-001-uuid",
      "staff_id": "staff-dr-001-uuid",
      "rate_percent": 15.0,
      "is_active": true,
      "created_at": "2026-08-06T14:30:00Z",
      "updated_at": "2026-08-06T14:30:00Z"
    },
    {
      "id": "rule-003-uuid",
      "rule_type": "medicine",
      "service_type_id": null,
      "staff_id": null,
      "rate_percent": 5.0,
      "is_active": true,
      "created_at": "2026-07-15T09:00:00Z",
      "updated_at": "2026-07-15T09:00:00Z"
    }
  ]
}
```

**Mô tả các trường kết quả:**

| Trường | Kiểu | Mô tả ý nghĩa nghiệp vụ |
|--------|------|------------------------|
| `id` | UUID | ID duy nhất của rule |
| `rule_type` | String | `service_type` (chiết khấu theo loại DV) hoặc `medicine` (chiết khấu thuốc) |
| `service_type_id` | UUID \| null | ID loại thủ thuật (chỉ khi rule_type='service_type'); NULL khi medicine |
| `staff_id` | UUID \| null | ID nhân sự override (NULL = tỷ lệ chung phòng khám) |
| `rate_percent` | Decimal | Tỷ lệ chiết khấu (0–100%) |
| `is_active` | Boolean | Quy tắc có đang hoạt động hay không |
| `created_at` / `updated_at` | DateTime | Dấu thời gian tạo/cập nhật |

**Các mã lỗi có thể:**

| Mã HTTP | Mô tả |
|---------|-------|
| 400 | Tham số `staff_id` không hợp lệ (không phải UUID) |
| 401 | Không có token xác thực |
| 403 | Người dùng không có quyền `payroll.manage` |
| 500 | Lỗi hệ thống (database, etc.) |

---

### 4.2 Tạo commission rule mới

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/hr/commission-rules` |
| **Mô tả** | Tạo rule chiết khấu mới — có thể là clinic-wide (staff_id=NULL) hoặc per-staff override (staff_id≠NULL). Nếu tạo rule per-staff với staff_id không tồn tại hoặc không cùng phòng khám → 404 NOT_FOUND |
| **Xác thực** | Bắt buộc; quyền `payroll.manage` |

#### Tham số đầu vào (Request Body)

```json
{
  "rule_type": "service_type",
  "service_type_id": "uuid-of-service-type",
  "staff_id": "uuid-of-staff (hoặc null cho tỷ lệ chung)",
  "rate_percent": 15.0,
  "is_active": true
}
```

| Tham số | Kiểu | Bắt buộc | Mô tả | Ràng buộc |
|---------|------|---------|-------|-----------|
| `rule_type` | String | Có | `"service_type"` hoặc `"medicine"` | — |
| `service_type_id` | UUID | Phụ thuộc | Bắt buộc khi `rule_type="service_type"` (ID loại DV); NULL/omit khi `rule_type="medicine"` | Phải tồn tại trong bảng `service_type` |
| `staff_id` | UUID \| null | Không | ID nhân sự override; NULL = tỷ lệ clinic-wide. Khi cung cấp, phải tồn tại trong cùng phòng khám | Phải tồn tại, cùng clinic_id; nếu không → 404 |
| `rate_percent` | Decimal | Có | Tỷ lệ chiết khấu từ 0 đến 100 | 0 ≤ rate_percent ≤ 100 |
| `is_active` | Boolean | Không | Quy tắc có hoạt động hay không (mặc định true) | — |

**Quy tắc duy nhất (Uniqueness):**
- `(clinic_id, service_type_id, COALESCE(staff_id, zero-uuid))` phải duy nhất cho `rule_type='service_type'`
- `(clinic_id, COALESCE(staff_id, zero-uuid))` phải duy nhất cho `rule_type='medicine'`
- Nếu tạo rule trùng lặp → 422 VALIDATION_ERROR

#### Kết quả trả về

**Thành công (201 Created):**

```json
{
  "code": "00",
  "message": "Created",
  "data": {
    "id": "newly-created-rule-uuid",
    "rule_type": "service_type",
    "service_type_id": "service-type-001-uuid",
    "staff_id": "staff-dr-001-uuid",
    "rate_percent": 15.0,
    "is_active": true,
    "created_at": "2026-08-07T10:30:00Z",
    "updated_at": "2026-08-07T10:30:00Z"
  }
}
```

**Các mã lỗi có thể:**

| Mã HTTP | Mã lỗi | Tình huống | Thông báo ví dụ |
|---------|--------|-----------|-----------------|
| 400 | INVALID_REQUEST | Tham số thiếu hoặc format sai (ví dụ: rate_percent > 100) | "rate_percent phải từ 0 đến 100" |
| 401 | UNAUTHORIZED | Token không hợp lệ | "Yêu cầu xác thực" |
| 403 | FORBIDDEN | Không có quyền `payroll.manage` | "Không có quyền cấu hình commission" |
| 404 | NOT_FOUND | staff_id không tồn tại hoặc không cùng phòng khám | "Nhân sự không tồn tại" |
| 422 | VALIDATION_ERROR | Tạo rule trùng lặp, hoặc `service_type_id` missing khi `rule_type='service_type'` | "Rule này đã tồn tại cho nhân sự / loại DV này" |
| 500 | INTERNAL_ERROR | Lỗi database | "Lỗi hệ thống" |

---

### 4.3 Sửa commission rule (PATCH)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `PATCH /api/v1/hr/commission-rules/{id}` |
| **Mô tả** | Sửa tỷ lệ hoặc trạng thái của rule (sửa từng trường). Chú ý: `staff_id` **không thay đổi được** — nếu muốn thay đổi staff_id, phải xóa rule cũ và tạo rule mới |
| **Xác thực** | Bắt buộc; quyền `payroll.manage` |

#### Tham số đầu vào (Request Body)

```json
{
  "rate_percent": 18.0,
  "is_active": true
}
```

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `rate_percent` | Decimal | Không | Tỷ lệ mới (0–100); nếu omit thì giữ nguyên |
| `is_active` | Boolean | Không | Trạng thái hoạt động mới; nếu omit thì giữ nguyên |

**Lưu ý:** `staff_id` không được phép sửa. Nếu request body chứa `staff_id`, nó sẽ bị bỏ qua (không lỗi, nhưng không áp dụng).

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "code": "00",
  "message": "Updated",
  "data": {
    "id": "rule-uuid",
    "rule_type": "service_type",
    "service_type_id": "service-type-001-uuid",
    "staff_id": "staff-dr-001-uuid",
    "rate_percent": 18.0,
    "is_active": true,
    "created_at": "2026-08-07T10:30:00Z",
    "updated_at": "2026-08-07T11:00:00Z"
  }
}
```

**Các mã lỗi:**

| Mã HTTP | Mô tả |
|---------|-------|
| 404 | Rule ID không tồn tại |
| 422 | rate_percent ngoài khoảng [0, 100] |
| 403 | Không có quyền `payroll.manage` |

---

### 4.4 Xóa commission rule (DELETE)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `DELETE /api/v1/hr/commission-rules/{id}` |
| **Mô tả** | Xóa rule chiết khấu. Nhân sự sẽ revert về tỷ lệ chung (nếu có) hoặc 0% commission. Soft-delete (đánh dấu `is_deleted=true`), không xóa vật lý |
| **Xác thực** | Bắt buộc; quyền `payroll.manage` |

#### Kết quả trả về

**Thành công (204 No Content):** Không có response body

**Các mã lỗi:**

| Mã HTTP | Mô tả |
|---------|-------|
| 404 | Rule ID không tồn tại |
| 403 | Không có quyền `payroll.manage` |

---

### 4.5 Lấy payslip tháng (các trường mới)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/hr/payroll?month=YYYY-MM` |
| **Mô tả** | Lấy danh sách payslip của tháng (bao gồm các trường rate/source mới cho TASK-138) |
| **Xác thực** | Bắt buộc; quyền `payroll.view` |
| **Ghi chú** | Endpoint này cũ từ TASK-128, mở rộng response với các trường mới |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `month` | String | Có | Tháng cần lấy (định dạng YYYY-MM) |

#### Kết quả trả về (Có các trường mới)

**Thành công (200 OK):**

```json
{
  "code": "00",
  "message": "Success",
  "data": {
    "month": "2026-08",
    "payslips": [
      {
        "staff_id": "staff-001-uuid",
        "staff_code": "NV001",
        "full_name": "Nguyễn Văn A",
        "pay_type": "per_session",
        "worked_days": 20.5,
        "total_hours": 160.0,
        "ot_hours": 0.0,
        "absent_days": 2,
        "leave_days": 0,
        "late_count": 0,
        "base_earned": 4100.0,
        "overtime_pay": 0.0,
        "allowance": 500.0,
        "attendance_bonus": 200.0,
        "late_penalty_total": 0.0,
        "gross_pay": 5200.0,
        "net_pay": 4680.0,
        "procedure_commission": 150.0,
        "medicine_commission": 45.0,
        "kpi_bonus": 100.0,
        "clawback_adjustment": 0.0,
        "procedure_rate_percent": 12.0,
        "procedure_rate_source": "staff_override",
        "medicine_rate_percent": 6.0,
        "medicine_rate_source": "clinic_default",
        "session_rate": 200.0,
        "shift_rate": null,
        "completed_shifts": 0
      }
    ],
    "total_net": 4680.0,
    "total_gross": 5200.0,
    "staff_count": 1
  }
}
```

**Mô tả các trường mới (TASK-138):**

| Trường | Kiểu | Mô tả ý nghĩa |
|--------|------|--------|
| `session_rate` | float \| null | Đơn giá buổi (VNĐ) nếu `pay_type='per_session'`, null nếu kiểu lương khác |
| `shift_rate` | float \| null | Đơn giá ca (VNĐ) nếu `pay_type='per_shift'`, null nếu kiểu lương khác |
| `completed_shifts` | int | Số ca hoàn thành trong tháng (chỉ dùng cho `per_shift`, là 0 khi kiểu lương khác) |
| `procedure_rate_percent` | float \| null | Tỷ lệ % chiết khấu thủ thuật được áp dụng; null nếu không earn commission |
| `procedure_rate_source` | "staff_override" \| "clinic_default" \| null | Nguồn tỷ lệ procedure (riêng nhân sự hay chung phòng khám); null nếu `procedure_rate_percent` là null |
| `medicine_rate_percent` | float \| null | Tỷ lệ % chiết khấu thuốc được áp dụng; null nếu không earn commission |
| `medicine_rate_source` | "staff_override" \| "clinic_default" \| null | Nguồn tỷ lệ medicine; null nếu `medicine_rate_percent` là null |

**Ví dụ hiển thị UI (FE):**
- Nếu `procedure_rate_percent=12.0` và `procedure_rate_source="staff_override"` → hiển thị badge "**12% · tỷ lệ riêng**" (amber)
- Nếu `medicine_rate_percent=5.0` và `medicine_rate_source="clinic_default"` → hiển thị badge "**5% · tỷ lệ chung**" (gray)
- Nếu `procedure_rate_percent=null` → không hiển thị badge (commission bằng 0)

---

## 5. Cấu trúc cơ sở dữ liệu

### 5.1 Tổng quan các bảng mở rộng

| Bảng | Cột mới/thay đổi | Mục đích |
|------|------------------|---------|
| `staff_profile` | `pay_type` (widen), `session_rate`, `shift_rate` | Lưu kiểu lương mới và đơn giá tương ứng |
| `commission_rule` | `staff_id` (FK) | Per-staff commission override dimension |

### 5.2 Chi tiết thay đổi bảng

#### Bảng: `staff_profile`

**Thay đổi:**

| Cột | Kiểu cũ | Kiểu mới | Bắt buộc | Mô tả |
|-----|---------|---------|---------|-------|
| `pay_type` | VARCHAR(10) | VARCHAR(20) | Có | Widen để chứa "per_session" (11 ký tự). Giá trị: `monthly` \| `hourly` \| `per_session` \| `per_shift` |
| `session_rate` | — | NUMERIC(15,2) | Không | Đơn giá buổi (VNĐ); NULL khi pay_type ≠ 'per_session' |
| `shift_rate` | — | NUMERIC(15,2) | Không | Đơn giá ca (VNĐ); NULL khi pay_type ≠ 'per_shift' |

**Ví dụ dữ liệu:**

```
staff_id: "staff-001-uuid"
pay_type: "per_session"
session_rate: 200.00        ← VNĐ/buổi
shift_rate: NULL

staff_id: "staff-002-uuid"
pay_type: "per_shift"
session_rate: NULL
shift_rate: 250.00          ← VNĐ/ca
```

---

#### Bảng: `commission_rule`

**Mô tả:** Bảng này được mở rộng từ TASK-128. Cột `staff_id` cho phép override per-staff.

| Cột | Kiểu | Bắt buộc | Mô tả | Ghi chú |
|-----|------|---------|-------|--------|
| `id` | UUID | Có | Khóa chính |  |
| `clinic_id` | UUID | Có | FK → clinic |  |
| `rule_type` | VARCHAR(20) | Có | `'service_type'` hoặc `'medicine'` |  |
| `service_type_id` | UUID | Phụ thuộc | FK → service_type; NULL khi `rule_type='medicine'` | |
| `staff_id` | UUID | Không | **[TASK-138 mới]** FK → staff_profile; NULL = tỷ lệ chung | Soft-delete CASCADE: nếu xóa nhân sự, xóa override của họ |
| `rate_percent` | NUMERIC(5,2) | Có | Tỷ lệ chiết khấu (0–100%) |  |
| `is_active` | BOOLEAN | Có | Quy tắc có hoạt động | Default true |
| `is_deleted` | BOOLEAN | Có | Soft-delete flag |  |
| `created_at` | TIMESTAMP | Có | Thời gian tạo |  |
| `updated_at` | TIMESTAMP | Có | Thời gian cập nhật |  |

**Tính duy nhất (Partial Unique Indexes — migration 0077):**

```sql
-- service_type rules: clinic + service_type + (staff override or NULL)
CREATE UNIQUE INDEX uq_commission_rule_clinic_service_type_staff
  ON commission_rule (clinic_id, service_type_id, COALESCE(staff_id, '00000000-0000-0000-0000-000000000000'::uuid))
  WHERE rule_type = 'service_type' AND is_deleted = false;

-- medicine rule: clinic + (staff override or NULL)
CREATE UNIQUE INDEX uq_commission_rule_clinic_medicine_staff
  ON commission_rule (clinic_id, COALESCE(staff_id, '00000000-0000-0000-0000-000000000000'::uuid))
  WHERE rule_type = 'medicine' AND is_deleted = false;
```

Cơ chế COALESCE với zero-UUID sentinel cho phép NULL-safe uniqueness — một phòng khám có thể có:
- 1 rule chung (staff_id = NULL) + N override (staff_id ≠ NULL) cho cùng service_type
- Mà không vi phạm uniqueness constraint

**Ví dụ dữ liệu:**

```
Clinic A — thủ thuật loại 001:
├─ rule (staff_id=NULL) → 10% (chung)
├─ rule (staff_id=dr-001) → 15% (override cho bác sĩ 1)
└─ rule (staff_id=dr-002) → 12% (override cho bác sĩ 2)

Clinic A — thuốc:
├─ rule (staff_id=NULL) → 5% (chung)
└─ rule (staff_id=nurse-001) → 3% (override cho y tá 1)
```

---

## 6. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-001 | **Kiểu lương mới không tính OT**: `per_session` và `per_shift` không accumulate ot_hours — OT chỉ áp dụng monthly/hourly | Hệ thống bỏ qua, ghi OT=0 cho 2 kiểu này |
| BR-002 | **per_session KHÔNG fallback sang legacy TimeLog**: nếu nhân sự không có `AttendanceDay` records cho tháng, `worked_days` = 0.0 (không tính từ Shift/TimeLog cũ) | Lương = 0 nếu không tick lưới chấm công; admin phải tick lại |
| BR-003 | **per_shift chỉ tính ca `completed`**: Shift với status ≠ 'completed' (scheduled, cancelled, on_leave, etc.) không được tính | Shift đó không tính vào lương ca |
| BR-004 | **Resolve tỷ lệ commission**: ưu tiên rule với (staff_id = this_staff, service_type_id), → fallback rule (staff_id = NULL, service_type_id), → không rule = 0% commission | Nhân sự không config override tự động dùng tỷ lệ chung |
| BR-005 | **Chiết khấu claw-back**: hoàn chiết khấu cùng tỷ lệ đã áp dụng khi earn (per-staff override nếu có, fallback chung), không phải tỷ lệ cũ | Claw-back reversible symmetry: nếu earn 15%, claw-back cũng -15% (không lẫn lộn với 10% chung) |
| BR-006 | **Nhân sự không tài khoản (`user_id=NULL`)**: vẫn có thể cấu hình `per_session`/`per_shift` lương và commission override | Admin có thể quản lý y tá/điều dưỡng mà họ không cần đăng nhập |
| BR-007 | **Automatic commission chỉ cho doctor**: chỉ nhân sự CÓ tài khoản bác sĩ mới được tính commission tự động (resolve từ visit.doctor_id → staff.user_id). Nhân sự khác nếu cần chia chiết khấu → `payroll_adjustment` thủ công | Giới hạn kế thừa từ TASK-128, không mở rộng |
| BR-008 | **staff_id không thay đổi sau tạo**: muốn thay đổi nhân sự của rule → xóa rule cũ, tạo rule mới | PATCH /commission-rules/{id} bỏ qua staff_id (immutable) |
| BR-009 | **Allowance/bonus/penalty áp dụng mọi kiểu lương**: không phải chỉ monthly/hourly mà cả per_session/per_shift | Nhân sự per_session vẫn nhận thêm allowance, bonus, late penalty |

---

## 7. Xử lý lỗi

### 7.1 Các mã lỗi phổ biến

| Mã HTTP | Mã lỗi | Tình huống xảy ra | Thông báo trả về |
|---------|--------|-------------------|-----------------|
| 400 | INVALID_REQUEST | Tham số không hợp lệ (ví dụ: month format sai, rate_percent > 100) | "Tham số không hợp lệ: [chi tiết]" |
| 401 | UNAUTHORIZED | Token xác thực không hợp lệ hoặc đã hết hạn | "Yêu cầu xác thực để truy cập tài nguyên này" |
| 403 | FORBIDDEN | Không có quyền yêu cầu (ví dụ: không có `payroll.manage`) | "Không có quyền truy cập" |
| 404 | NOT_FOUND | Không tìm thấy rule, staff, hoặc month | "Không tìm thấy [tài nguyên]" |
| 422 | VALIDATION_ERROR | Dữ liệu trùng lặp (duplicate rule cho staff+service_type), hoặc logic không hợp lệ | "Rule này đã tồn tại cho nhân sự và loại DV này" |
| 500 | INTERNAL_ERROR | Lỗi database, transaction, v.v. | "Lỗi hệ thống, vui lòng thử lại sau" |

### 7.2 Định dạng phản hồi lỗi

```json
{
  "code": "[Mã lỗi nội bộ hoặc HTTP status]",
  "message": "[Mô tả lỗi chi tiết]"
}
```

**Ví dụ:**

```json
{
  "code": "404",
  "message": "Staff ID không tồn tại hoặc không cùng phòng khám"
}
```

---

## 8. Ghi chú và lưu ý khi kiểm thử

### 8.1 Điểm quan trọng cần nắm

- **Lưới chấm công bắt buộc cho per_session**: nhân sự `per_session` không bao giờ fallback sang legacy TimeLog — nếu admin không tick lưới `AttendanceDay`, lương tháng = 0 buổi × đơn giá = 0. Đây là thiết kế có ý để bắt buộc admin quy trình chấm công chính thức.

- **per_shift chỉ tính completed**: Shift với status `cancelled`, `on_leave`, hoặc `scheduled` (chưa hoàn thành) không tính. Admin phải thay đổi status → `completed` để tính lương.

- **Claw-back dùng tỷ lệ override nếu có**: ví dụ, nếu bác sĩ có override 15% và earn commission, sau đó admin tạo invoice hoàn → hoàn cùng 15%, không phải tỷ lệ chung 10%. Điều này đảm bảo symmetry: earn/claw-back ở cùng tỷ lệ.

- **Nhân sự không tài khoản vẫn có commission config**: y tá/điều dưỡng `user_id=NULL` có thể config tỷ lệ riêng, nhưng commission tự động chỉ apply cho doctor (`user_id≠NULL`). Để chia chiết khấu cho y tá → dùng `payroll_adjustment` thủ công.

- **Soft-delete trên commission_rule**: xóa rule = set `is_deleted=true`, không xóa vật lý. Lý do: đảm bảo audit trail + tính toán lại lương cũ có dữ liệu.

- **i18n chưa hoàn tất (known debt m3)**: label "Theo buổi (ngày công)" / "Theo ca" trên StaffFormPage và CommissionKpiConfigPage còn hardcode tiếng Việt, chưa dùng i18n key.

### 8.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Dữ liệu đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **per_session lương thường** | Staff A: pay_type='per_session', session_rate=200; AttendanceDay: 20 ngày full + 1 nửa ngày = 20.5 buổi | base_earned = 200 × 20.5 = 4100 |
| **per_session không có attendance grid** | Staff B: pay_type='per_session'; tháng đó không tick lưới chấm công | worked_days=0, base_earned=0 (không fallback) |
| **per_shift lương thường** | Staff C: pay_type='per_shift', shift_rate=250; Shift count status='completed' = 18 | base_earned = 250 × 18 = 4500 |
| **per_shift + cancelled shift** | Staff D: per_shift, 18 completed + 2 cancelled | Chỉ tính 18, không tính 2 cancelled → base_earned=4500 |
| **Commission override per-staff** | Service type DV001: clinic-wide rule 10%; Dr. E: override rule 15% cho DV001; revenue từ DV001 = 1000 | Commission = 1000 × 15% = 150 (dùng override, không 10%) |
| **Commission fallback chung** | Service type DV002: clinic-wide rule 10%; Dr. F: không config override; revenue = 1000 | Commission = 1000 × 10% = 100 (dùng chung) |
| **Medicine commission** | Clinic-wide medicine rate 5%; Dr. G: override 7%; prescription revenue = 2000 | Commission = 2000 × 7% = 140 (dùng override) |
| **Claw-back invoice hoàn** | Dr. H earned 1000 × 15% (override) = 150; invoice hoàn → claw-back | adjustment = -150 (cùng tỷ lệ 15%, không 10% chung) |
| **API duplicate rule** | Tạo rule (clinic, service_type='DV001', staff_id=NULL, 10%) rồi tạo lại với cùng params | 422 VALIDATION_ERROR: "Rule này đã tồn tại" |
| **API cross-clinic staff_id** | Clinic A tạo rule với staff_id từ Clinic B | 404 NOT_FOUND: "Staff không tồn tại" (clinic scope check) |

### 8.3 Hạn chế hiện tại

- **per_session chỉ từ AttendanceDay (TASK-127)**: không có UI chấm buổi sáng/chiều/tối riêng — toàn bộ dựa vào lưới ngày công theo tick admin. Nếu cần chấm chi tiết hơn (tính công sáng riêng từ chiều) → ngoài scope TASK-138.

- **OT không áp dụng per_session/per_shift**: hiện tại OT logic (multiplier, tính giờ qua 48/tuần, etc.) chỉ cho monthly/hourly. Per_session/per_shift không OT.

- **Nhân sự không tài khoản không được commission tự động**: điều dưỡng/y tá (`user_id=NULL`) có thể config tỷ lệ riêng nhưng commission tự động không tính (design từ TASK-128). Phải thủ công bằng `payroll_adjustment`.

### 8.4 Hướng phát triển

- **Tính OT cho per_session/per_shift** (nếu user request): cần phân tích logic — per_shift OT là gì? "Quá 20 ca/tháng"?
- **Chấm công sáng/chiều/tối riêng** (nếu user request): thêm UI chấm buổi, tính per_session từ buổi thay vì ngày.
- **Hoàn tất i18n cho trang cấu hình lương** (known debt m3): đưa label về i18n key.
- **Commission tự động cho non-doctor** (out of scope TASK-128): cần quy tắc quy nguồn cho y tá/điều dưỡng (hiện resolve qua visit.doctor_id/prescription.doctor_id, không cho nhân sự khác).

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày | Ghi chú |
|---------|--------|------|--------|
| Implementation Agent | — | 2026-08-06 | Hoàn tất implementation + fix rounds |
| Code Review Agent | — | 2026-08-06 | Approved (fixed critical issues) |
| Test Agent | — | 2026-08-07 | All 34 new-code scenarios passed |
| Documentation Agent | — | 2026-08-07 | Tài liệu này |

---

**Tài liệu liên quan:**
- `docs/tasks/TASK-128/deliveries/final-specs/` — Payroll engine base (commission/KPI/claw-back)
- `docs/tasks/TASK-127/deliveries/final-specs/` — Attendance grid & Shift management
- `docs/tasks/TASK-138/refs/implementation-plan.md` — Technical decisions
- `docs/tasks/TASK-138/deliveries/test-reports/test-report.md` — Test results
