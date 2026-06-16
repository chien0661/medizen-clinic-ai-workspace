# API Spec: Clinic Settings — Prescription Template

**Task:** TASK-080
**Date:** 2026-06-16
**Endpoint:** `/api/v1/clinics/me/settings` (GET / PATCH)
**Status:** Đã hoàn thành & kiểm thử

---

## Tổng quan

Các endpoint này cho phép:
1. **GET** toàn bộ cài đặt phòng khám, bao gồm nhóm `prescription_template` (cấu hình mẫu in đơn thuốc)
2. **PATCH** cập nhật nhóm `prescription_template` hoặc các nhóm khác

---

## 1. GET /api/v1/clinics/me/settings

### Mô tả

Trả về toàn bộ cài đặt phòng khám của clinic hiện tại, bao gồm các nhóm: `operating_hours`, `appointment`, `queue`, `inventory`, `prescription`, `prescription_template`, `billing`, `specialty`.

Hệ thống tự động thực hiện deep-merge: default settings + settings trong DB. Clinic cũ không có key `prescription_template` sẽ nhận giá trị mặc định.

### Request

```
GET /api/v1/clinics/me/settings
Authorization: Bearer {token}
```

**Tham số:** Không có

### Response

#### 200 OK

```json
{
  "operating_hours": {
    "mon": { "is_open": true, "open": "08:00", "close": "17:00" },
    "tue": { "is_open": true, "open": "08:00", "close": "17:00" },
    "wed": { "is_open": true, "open": "08:00", "close": "17:00" },
    "thu": { "is_open": true, "open": "08:00", "close": "17:00" },
    "fri": { "is_open": true, "open": "08:00", "close": "17:00" },
    "sat": { "is_open": false, "open": "08:00", "close": "12:00" },
    "sun": { "is_open": false, "open": "08:00", "close": "12:00" }
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
  "prescription_template": {
    "header_clinic_name": "Phòng khám",
    "header_address": "",
    "show_weight": true,
    "show_diagnosis": true,
    "show_gender": true,
    "min_medicine_rows": 6,
    "advice_text": "Uống thuốc đúng liều, đúng giờ theo đơn; theo dõi sốt, ăn uống và các dấu hiệu bất thường (sốt cao không hạ, khó thở, lì bì, nôn nhiều).",
    "followup_text": "Tái khám sau 03 ngày hoặc đưa trẻ đi khám ngay nếu có triệu chứng nặng hơn.",
    "footer_lines": [
      "Khám bệnh lại xin mang theo đơn này.",
      "Số điện thoại liên hệ: "
    ],
    "signature_label": "Bác sỹ/Y sỹ khám bệnh",
    "signature_default": "",
    "paper_size": "A5"
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

#### Mô tả trường `prescription_template`

| Trường | Kiểu | Mô tả | Mặc định |
|--------|------|-------|---------|
| `header_clinic_name` | string | Tên phòng khám hiển thị ở header | "Phòng khám" |
| `header_address` | string | Địa chỉ phòng khám hiển thị ở header | "" |
| `show_weight` | boolean | Hiển thị cân nặng trên bản in | true |
| `show_diagnosis` | boolean | Hiển thị chẩn đoán trên bản in | true |
| `show_gender` | boolean | Hiển thị giới tính trên bản in | true |
| `min_medicine_rows` | integer | Số dòng thuốc tối thiểu (1–20) | 6 |
| `advice_text` | string | Lời dặn về cách dùng thuốc | "Uống thuốc đúng liều..." |
| `followup_text` | string | Lời dặn tái khám | "Tái khám sau 03 ngày..." |
| `footer_lines` | array[string] | Danh sách ghi chú chân trang | ["Khám bệnh lại...", "SĐT: "] |
| `signature_label` | string | Nhãn chữ ký (ví dụ: "Bác sỹ/Y sỹ khám bệnh") | "Bác sỹ/Y sỹ khám bệnh" |
| `signature_default` | string | Fallback tên BS khi user profile trống | "" |
| `paper_size` | string | Khổ giấy: "A5" hoặc "A4" | "A5" |

#### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "message": "Token không hợp lệ hoặc hết hạn"
}
```

#### 500 Internal Server Error

```json
{
  "error": "INTERNAL_ERROR",
  "message": "Lỗi hệ thống"
}
```

---

## 2. PATCH /api/v1/clinics/me/settings

### Mô tả

Cập nhật cài đặt phòng khám. Request body chứa các nhóm (hoặc field trong nhóm) cần thay đổi. Hệ thống thực hiện merge (chỉ cập nhật field được gửi, các field khác giữ nguyên).

**Quyền yêu cầu:** `clinic.settings.update`

### Request

```
PATCH /api/v1/clinics/me/settings
Authorization: Bearer {token}
Content-Type: application/json
```

#### Request Body

```json
{
  "prescription_template": {
    "header_clinic_name": "Phòng khám chuyên khoa Nhi Dr Trường Medi",
    "header_address": "R21-Eurowindow River Park",
    "show_weight": true,
    "show_diagnosis": true,
    "show_gender": true,
    "min_medicine_rows": 6,
    "advice_text": "Uống thuốc đúng liều, đúng giờ theo đơn; theo dõi sốt, ăn uống và các dấu hiệu bất thường (sốt cao không hạ, khó thở, lì bì, nôn nhiều).",
    "followup_text": "Tái khám sau 03 ngày hoặc đưa trẻ đi khám ngay nếu có triệu chứng nặng hơn.",
    "footer_lines": [
      "Khám bệnh lại xin mang theo đơn này.",
      "Số điện thoại liên hệ: 0353334009"
    ],
    "signature_label": "Bác sỹ/Y sỹ khám bệnh",
    "signature_default": "",
    "paper_size": "A5"
  }
}
```

**Lưu ý:** Chỉ cần gửi các field muốn cập nhật. Hệ thống sẽ merge với giá trị cũ.

**Ví dụ: cập nhật chỉ tên phòng khám**

```json
{
  "prescription_template": {
    "header_clinic_name": "Phòng khám Xanh"
  }
}
```

#### Validation

| Trường | Quy tắc | Thông báo lỗi |
|--------|--------|--------------|
| `min_medicine_rows` | 1 ≤ value ≤ 20 | "min_medicine_rows must be between 1 and 20" |
| `paper_size` | "A5" hoặc "A4" | "paper_size must be 'A5' or 'A4'" |
| `header_clinic_name` | Chuỗi, tối đa 200 ký tự | "header_clinic_name must be a string (max 200 chars)" |
| `advice_text` | Chuỗi, tối đa 500 ký tự | "advice_text must be a string (max 500 chars)" |
| `footer_lines` | Mảng chuỗi | "footer_lines must be an array of strings" |

### Response

#### 200 OK

Trả về toàn bộ `ClinicSettingsResponse` (giống GET), phản ánh các thay đổi vừa được lưu.

```json
{
  "operating_hours": { ... },
  "appointment": { ... },
  "queue": { ... },
  "inventory": { ... },
  "prescription": { ... },
  "prescription_template": {
    "header_clinic_name": "Phòng khám chuyên khoa Nhi Dr Trường Medi",
    "header_address": "R21-Eurowindow River Park",
    "show_weight": true,
    "show_diagnosis": true,
    "show_gender": true,
    "min_medicine_rows": 6,
    "advice_text": "Uống thuốc đúng liều...",
    "followup_text": "Tái khám sau 03 ngày...",
    "footer_lines": [
      "Khám bệnh lại xin mang theo đơn này.",
      "Số điện thoại liên hệ: 0353334009"
    ],
    "signature_label": "Bác sỹ/Y sỹ khám bệnh",
    "signature_default": "",
    "paper_size": "A5"
  },
  "billing": { ... },
  "specialty": { ... }
}
```

#### 400 Bad Request

```json
{
  "error": "VALIDATION_ERROR",
  "message": "min_medicine_rows must be between 1 and 20"
}
```

#### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "message": "Token không hợp lệ hoặc hết hạn"
}
```

#### 403 Forbidden

```json
{
  "error": "FORBIDDEN",
  "message": "Bạn không có quyền cập nhật cài đặt phòng khám"
}
```

#### 500 Internal Server Error

```json
{
  "error": "INTERNAL_ERROR",
  "message": "Lỗi hệ thống"
}
```

---

## 3. User — Trường `title` (Chức danh/Học hàm)

### Mô tả

Bác sĩ/Y sĩ có thể cấu hình chức danh/học hàm (ví dụ: "Ths.Bs", "Dr.", "BS.", v.v.) trong hồ sơ của mình. Trường này được sử dụng khi in đơn thuốc để hiển thị tên + chức danh trên chữ ký.

### Database Migration

```sql
ALTER TABLE "user" ADD COLUMN title character varying(100);
```

### API

#### Endpoint cải tiến

- **GET** `/api/v1/users/{id}` — Trả về user object kèm trường `title`
- **POST** `/api/v1/users` — Tạo user mới, có thể gửi `title` (optional)
- **PATCH** `/api/v1/users/{id}` — Cập nhật hồ sơ user, kể cả `title`

#### Schema Example

```json
{
  "id": "uuid",
  "full_name": "Nguyễn Văn A",
  "title": "Ths.Bs",
  "email": "nguyenva@clinic.vn",
  "role": "doctor",
  ...
}
```

#### Validation

| Trường | Quy tắc | Thông báo lỗi |
|--------|--------|--------------|
| `title` | Chuỗi, tối đa 100 ký tự, optional | "title must be a string (max 100 chars)" |

---

## 4. Luồng Integrate

### Khởi động ứng dụng (FE)

1. FE gọi `GET /api/v1/clinics/me/settings`
2. Lưu toàn bộ response vào `settingsStore` (Pinia/Vuex)
3. Component `PrintablePrescription` đọc `settingsStore.prescription_template`

### Cập nhật cấu hình (Admin panel)

1. Admin vào Settings → "Mẫu in đơn thuốc"
2. Chỉnh sửa các field
3. Nhấn "Lưu" → FE gửi `PATCH /api/v1/clinics/me/settings` với `prescription_template` object
4. BE xác nhận, trả về response 200
5. FE cập nhật `settingsStore`
6. Component in cập nhật tự động (react to store change)

### In đơn thuốc

1. Bác sĩ kê đơn → nhấn "In"
2. FE mở `PrintPrescriptionModal`
3. Component `PrintablePrescription` render HTML bao gồm:
   - Header từ `prescription_template.header_clinic_name` + `header_address`
   - Thông tin BN từ props: `patient`, `visit`, `weight` (từ vitals)
   - Danh sách thuốc từ `prescription.items`
   - Lời dặn từ `prescription_template.advice_text` + `followup_text`
   - Footer từ `prescription_template.footer_lines`
   - Chữ ký: lấy `doctor.full_name + doctor.title`, fallback `prescription_template.signature_default`
4. Nhấn "In" → `window.print()` → dialog in trình duyệt → in/lưu PDF

---

## 5. Test Cases

| Kịch bản | Yêu cầu | Kết quả kỳ vọng |
|---------|---------|----------------|
| **TS-001** GET settings clinic mới | Clinic không có cấu hình | 200 OK, trả về default prescription_template (header="Phòng khám", min_rows=6, paper="A5") |
| **TS-002** PATCH header_clinic_name | Gửi `{"prescription_template": {"header_clinic_name": "Clinic XYZ"}}` | 200 OK, prescription_template.header_clinic_name = "Clinic XYZ", các field khác không thay đổi |
| **TS-003** PATCH min_medicine_rows=25 | Gửi value ngoài 1–20 | 400 Bad Request, "min_medicine_rows must be between 1 and 20" |
| **TS-004** PATCH paper_size="Letter" | Gửi value không hợp lệ | 400 Bad Request, "paper_size must be 'A5' or 'A4'" |
| **TS-005** PATCH chỉ 1 field | Gửi chỉ `{"prescription_template": {"header_address": "..."}}` | 200 OK, merge partial, các field khác giữ nguyên |
| **TS-006** GET settings + round-trip | PATCH → GET → so sánh giá trị | 200 OK, giá trị GET khớp với PATCH |
| **TS-007** In bản in đơn | Render PrintablePrescription với config | HTML in có header, lời dặn, footer, chữ ký đúng theo config |
| **TS-008** Ẩn/hiện cân nặng | Config show_weight=false, có weight data | Bản in không hiển thị dòng cân nặng |
| **TS-009** PATCH không có quyền | User không có quyền clinic.settings.update | 403 Forbidden |
| **TS-010** Token hết hạn | GET/PATCH với token không hợp lệ | 401 Unauthorized |

---

**Tài liệu này mô tả API spec cho TASK-080 (2026-06-16).**

