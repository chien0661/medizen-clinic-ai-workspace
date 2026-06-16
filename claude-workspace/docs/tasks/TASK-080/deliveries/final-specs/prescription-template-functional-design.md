# Thiết Kế Chi Tiết: Cập nhật & cấu hình template in đơn thuốc

**Task:** TASK-080
**Phiên bản:** 1.0
**Ngày:** 2026-06-16
**Trạng thái:** Đã duyệt
**Tài liệu liên quan:** TASK-079 (dynamic vitals), TASK-047 (print foundation)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-06-16 | Phiên bản đầu tiên |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Nguồn dữ liệu đầu vào](#3-nguồn-dữ-liệu-đầu-vào)
- [4. Danh sách API](#4-danh-sách-api)
- [5. Chi tiết từng API](#5-chi-tiết-từng-api)
- [6. Cấu trúc cơ sở dữ liệu](#6-cấu-trúc-cơ-sở-dữ-liệu)
- [7. SQL tổng hợp và truy vấn dữ liệu](#7-sql-tổng-hợp-và-truy-vấn-dữ-liệu)
- [8. Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
- [9. Xử lý lỗi](#9-xử-lý-lỗi)
- [10. Ghi chú và lưu ý khi kiểm thử](#10-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Khi in đơn thuốc, bản in hiện tại (TASK-047 — bố cục "Phiếu Khám Bệnh" dạng bảng) không khớp với mẫu đơn thuốc thực tế mà phòng khám yêu cầu. Tính năng này **thay thế bố cục bản in** với mẫu "**ĐƠN THUỐC**" theo chuẩn phòng khám, và cho phép **cấu hình các nội dung cố định** (tên phòng khám, địa chỉ, lời dặn, chữ ký, v.v.) thông qua giao diện quản trị, thay vì hard-code.

### 1.2 Phạm vi

**Bao gồm:**
- Đổi bố cục bản in từ "Phiếu Khám Bệnh" (bảng) sang "ĐƠN THUỐC" (dòng kẻ chấm)
- Bổ sung trường **Cân nặng (kg)** và **Chẩn đoán** vào bản in
- Cấu hình template: header phòng khám, địa chỉ, số dòng thuốc tối thiểu, lời dặn, lời tái khám, footer, chữ ký, khổ giấy (A5/A4)
- Màn hình cấu hình template trong Admin → Cài đặt phòng khám
- Trường chức danh/học hàm (title) của bác sĩ ký

**Không bao gồm:**
- Thay đổi luồng khám bệnh, tạo đơn thuốc
- Thay đổi khác với các component in khác (chứng chỉ, biên lai, v.v.)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Bác sĩ/Y sĩ** | Sử dụng nút in để in đơn thuốc từ màn hình khám bệnh hoặc billing |
| **Quản trị phòng khám** | Cấu hình template in thông qua Admin → Cài đặt phòng khám |
| **Hệ thống Backend** | Cung cấp API cấu hình (GET/PATCH `/clinics/me/settings`), lưu cấu hình dưới dạng JSONB |
| **Frontend** | Render bản in theo cấu hình, hiển thị giao diện cấu hình |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
[1. Quản trị phòng khám]
      │  Truy cập Admin → Cài đặt → Mẫu in đơn thuốc
      ▼
[Giao diện cấu hình (SettingsPage)]
      │  Chỉnh sửa: tên phòng khám, lời dặn, footer, chữ ký, v.v.
      ├─► PATCH /api/v1/clinics/me/settings
      │    (nhóm prescription_template)
      ▼
[Backend Settings API]
      │  Lưu cấu hình dưới JSONB vào clinic_settings
      ▼
[Database: clinic_settings.settings]
      │  {prescription_template: {...}}
      │
      ├─────────────────────────────────────────┐
      │                                         │
      ▼                                         ▼
[2. Bác sĩ kê đơn]                  [FE: Load cấu hình]
      │  PrescriptionTab:                │  GET /clinics/me/settings
      │  - Kê đơn                        ▼
      │  - Nút "In đơn thuốc"     [settingsStore: {prescription_template}]
      │    ↓                              │
      │  PrintPrescriptionModal    [Render: PrintablePrescription.tsx]
      │  (draft hoặc full data)           │
      │  - draft: chỉ có thuốc            │  Truyền:
      │  - full: có BN, chẩn đoán,        │  - config (tên phòng, lời dặn, ...)
      │    cân nặng (từ vitals)           │  - patient, visit, prescription
      │                                   │  - doctor name + title
      ▼                                   ▼
[3. In đơn]                      [In "ĐƠN THUỐC"]
      │  window.print()                   │  HTML → CSS @page → PDF/In
      │  (browser native print dialog)    │  Theo khổ giấy (A5/A4)
      ▼                                   ▼
[4. Kết quả in trên giấy]
      │  Bố cục:
      │  - Header (trái): tên phòng khám, địa chỉ
      │  - Tiêu đề (giữa): ĐƠN THUỐC
      │  - Thông tin BN: họ tên / ngày sinh – cân nặng – giới tính / địa chỉ / chẩn đoán
      │  - Danh sách thuốc: 1..N dòng kẻ chấm (đệm tới min_rows)
      │  - Lời dặn: *Lời dặn: [...], *Tái khám: [...]
      │  - Chữ ký (phải): Ngày giờ – thứ – Chức danh + Tên BS
      │  - Footer: "Mang theo đơn này", "Số ĐT liên hệ"
      ▼
[Bản in giấy]
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Quản trị cấu hình template | Quản trị viên phòng khám truy cập Admin → Cài đặt phòng khám → tab "Mẫu in đơn thuốc". Hiển thị biểu mẫu với 11 trường cấu hình: tên phòng khám, địa chỉ, khổ giấy (A5/A4), số dòng thuốc tối thiểu, 3 checkbox (hiển thị cân nặng, chẩn đoán, giới tính), lời dặn, lời tái khám, dòng footer, nhãn chữ ký, tên BS mặc định. Nút "Lưu" gửi PATCH request đến BE. |
| 2 | Lưu cấu hình vào database | Backend nhận PATCH /clinics/me/settings với nhóm prescription_template. Validate dữ liệu theo Pydantic schema. Ghi vào clinic_settings.settings (JSONB). Trả lại response với toàn bộ settings group, kể cả prescription_template. |
| 3 | FE tải cấu hình vào store | Khi ứng dụng khởi động hoặc sau khi PATCH, FE gọi GET /clinics/me/settings, lưu prescription_template vào settingsStore. |
| 4 | Bác sĩ kê đơn và in | Bác sĩ/Y sĩ kê đơn từ PrescriptionTab hoặc xem đơn từ billing. Nhấn nút "In đơn thuốc" → mở PrintPrescriptionModal. Modal render PrintablePrescription.tsx với props: (config từ store, patient/visit data, prescription items, doctor info). |
| 5 | Render bản in | PrintablePrescription.tsx render HTML bố cục "ĐƠN THUỐC": header (tên phòng, địa chỉ từ config), tiêu đề, thông tin BN (họ tên, ngày sinh, cân nặng từ vitals, giới tính, địa chỉ, chẩn đoán từ visit). Danh sách thuốc từ prescription.items, loại bỏ deleted items. Đệm dòng trống kẻ chấm tới min_rows. Lời dặn/tái khám/footer từ config. Chữ ký: ngày/giờ + thứ tiếng Việt + tên + chức danh BS (từ user.title hoặc fallback config). |
| 6 | In | FE gọi window.print() → mở dialog in trình duyệt → người dùng chọn máy in hoặc lưu PDF. CSS @page xác định khổ giấy (A5 hay A4). |

---

## 3. Nguồn dữ liệu đầu vào

Phần này không áp dụng — dữ liệu cấu hình lấy từ người dùng (quản trị viên) qua API, không từ nguồn bên ngoài (Message Queue, File Import, v.v.).

---

## 4. Danh sách API

Tất cả API đều yêu cầu xác thực qua header:
```
Authorization: Bearer {token}
```

**Đường dẫn gốc (Base Path):** `/api/v1`

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt |
|-----|------------|-----------|--------------|
| 1 | GET | `/api/v1/clinics/me/settings` | Lấy toàn bộ cài đặt phòng khám (kể cả prescription_template) |
| 2 | PATCH | `/api/v1/clinics/me/settings` | Cập nhật cài đặt phòng khám (bao gồm nhóm prescription_template) |

---

## 5. Chi tiết từng API

### 5.1 Lấy cài đặt phòng khám

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `GET /api/v1/clinics/me/settings` |
| **Mô tả** | Trả về toàn bộ cài đặt phòng khám của clinic hiện tại, bao gồm nhóm prescription_template |
| **Xác thực** | Bắt buộc (Bearer token) |
| **Quyền yêu cầu** | Không yêu cầu (đọc cài đặt của clinic mình) |

#### Tham số đầu vào

Không có tham số đầu vào.

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu từ FE |
| 2 | Kiểm tra token xác thực — từ chối nếu không hợp lệ |
| 3 | Lấy clinic_id từ context của user (clinic hiện tại) |
| 4 | Truy vấn bảng clinic_settings, lấy cột settings (JSONB) |
| 5 | Thực hiện deep-merge: default settings + cài đặt trong DB, đảm bảo clinic cũ không có key prescription_template sẽ nhận giá trị mặc định |
| 6 | Validate từng group (appointment, queue, prescription_template, v.v.) qua Pydantic schema |
| 7 | Trả kết quả về dạng ClinicSettingsResponse (JSON) |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "operating_hours": {...},
  "appointment": {...},
  "queue": {...},
  "inventory": {...},
  "prescription": {...},
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
    "signature_default": "Dr. Nguyễn Văn A",
    "paper_size": "A5"
  },
  "billing": {...},
  "specialty": {...}
}
```

**Mô tả các trường prescription_template:**

| Trường | Kiểu | Mô tả ý nghĩa |
|--------|------|--------------|
| `header_clinic_name` | Chuỗi | Tên phòng khám hiển thị ở header trái bản in (mặc định: "Phòng khám") |
| `header_address` | Chuỗi | Địa chỉ phòng khám hiển thị ở header trái (mặc định: "") |
| `show_weight` | Boolean | Hiển thị cân nặng trên bản in khi có dữ liệu (mặc định: true) |
| `show_diagnosis` | Boolean | Hiển thị chẩn đoán trên bản in khi có dữ liệu (mặc định: true) |
| `show_gender` | Boolean | Hiển thị giới tính trên bản in khi có dữ liệu (mặc định: true) |
| `min_medicine_rows` | Số nguyên | Số dòng thuốc tối thiểu hiển thị (đệm dòng trống kẻ chấm nếu cần). Giới hạn: 1–20 (mặc định: 6) |
| `advice_text` | Chuỗi | Lời dặn về cách dùng thuốc (dòng 1, có dấu `*Lời dặn:`) |
| `followup_text` | Chuỗi | Lời dặn tái khám (dòng 2, có dấu `*Tái khám:`) |
| `footer_lines` | Mảng chuỗi | Danh sách ghi chú chân trang (ví dụ: ["Mang theo đơn này", "SĐT: 0353334009"]) |
| `signature_label` | Chuỗi | Nhãn chữ ký (ví dụ: "Bác sỹ/Y sỹ khám bệnh") |
| `signature_default` | Chuỗi | Fallback tên/chức danh BS khi user profile không có dữ liệu (mặc định: "") |
| `paper_size` | Chuỗi | Khổ giấy: "A5" hoặc "A4" (mặc định: "A5") |

---

### 5.2 Cập nhật cài đặt phòng khám

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `PATCH /api/v1/clinics/me/settings` |
| **Mô tả** | Cập nhật cài đặt phòng khám (có thể cập nhật từng nhóm settings riêng lẻ). Request body chứa các nhóm cần thay đổi. Hệ thống thực hiện merge (chỉ cập nhật field được gửi, các field khác giữ nguyên). |
| **Xác thực** | Bắt buộc (Bearer token) |
| **Quyền yêu cầu** | `clinic.settings.update` |

#### Tham số đầu vào

Request body (`ClinicSettingsPatchRequest`):

```json
{
  "prescription_template": {
    "header_clinic_name": "Phòng khám Nhi Xanh",
    "header_address": "Tòa nhà A, Quận 1",
    "show_weight": true,
    "min_medicine_rows": 8,
    "paper_size": "A4"
  }
}
```

| Trường | Kiểu | Bắt buộc | Mô tả |
|--------|------|---------|-------|
| `prescription_template` | Object hoặc null | Không | Nhóm cài đặt template in. Nếu gửi, chỉ cần gửi các field muốn thay đổi. Hệ thống tự động merge với giá trị cũ. |

**Lưu ý:** Chỉ các nhóm settings trong body được cập nhật. Các nhóm khác (appointment, queue, v.v.) giữ nguyên nếu không có trong request.

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu PATCH từ FE |
| 2 | Kiểm tra token xác thực — từ chối nếu không hợp lệ |
| 3 | Kiểm tra quyền `clinic.settings.update` — từ chối nếu không đủ quyền |
| 4 | Validate request body: các trường prescription_template phải hợp lệ (ví dụ: min_medicine_rows phải từ 1–20, paper_size phải là "A5" hoặc "A4") |
| 5 | Lấy clinic_id từ context |
| 6 | Truy vấn cài đặt hiện tại từ clinic_settings |
| 7 | Thực hiện merge: `settings_current[prescription_template].update(request_body[prescription_template])` |
| 8 | Ghi cài đặt mới vào DB (JSONB) |
| 9 | Validate lại toàn bộ settings (đảm bảo consistency) |
| 10 | Trả lại ClinicSettingsResponse với dữ liệu đã cập nhật |

#### Kết quả trả về

**Thành công (200 OK):**

Trả về toàn bộ ClinicSettingsResponse (giống GET), phản ánh các thay đổi vừa được lưu.

```json
{
  "prescription_template": {
    "header_clinic_name": "Phòng khám Nhi Xanh",
    "header_address": "Tòa nhà A, Quận 1",
    "show_weight": true,
    "show_diagnosis": true,
    "show_gender": true,
    "min_medicine_rows": 8,
    "advice_text": "Uống thuốc đúng liều...",
    "followup_text": "Tái khám sau 03 ngày...",
    "footer_lines": ["Mang theo đơn này", "SĐT: 0353334009"],
    "signature_label": "Bác sỹ/Y sỹ khám bệnh",
    "signature_default": "",
    "paper_size": "A4"
  },
  ...
}
```

---

## 6. Cấu trúc cơ sở dữ liệu

### 6.1 Tổng quan các bảng

| Bảng | Mục đích |
|------|---------|
| `clinic_settings` | Lưu JSONB cài đặt cho từng phòng khám, bao gồm nhóm prescription_template |
| `user` | Lưu thông tin bác sĩ, thêm cột `title` (chức danh/học hàm) |

### 6.2 Chi tiết bảng

#### Bảng: `clinic_settings`

**Mô tả:** Bảng lưu toàn bộ cài đặt của phòng khám dưới dạng JSONB. Bao gồm các nhóm: operating_hours, appointment, queue, inventory, prescription, **prescription_template**, billing, specialty.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `clinic_id` | UUID | Có | Khóa ngoài → clinic.id |
| `settings` | JSONB | Có | Dữ liệu cài đặt, bao gồm key `prescription_template` |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo |
| `updated_at` | TIMESTAMP | Có | Thời điểm cập nhật cuối |

**Cấu trúc JSONB — nhóm `prescription_template`:**

```json
{
  "header_clinic_name": "Phòng khám",
  "header_address": "",
  "show_weight": true,
  "show_diagnosis": true,
  "show_gender": true,
  "min_medicine_rows": 6,
  "advice_text": "Uống thuốc đúng liều...",
  "followup_text": "Tái khám sau 03 ngày...",
  "footer_lines": ["Mang theo đơn này", "SĐT: "],
  "signature_label": "Bác sỹ/Y sỹ khám bệnh",
  "signature_default": "",
  "paper_size": "A5"
}
```

#### Bảng: `user`

**Mô tả:** Thêm cột `title` để lưu chức danh/học hàm của bác sĩ (ví dụ: "Ths.Bs", "Dr.", "BS.", v.v.). Dùng để hiển thị trên bản in đơn thuốc khi in chữ ký BS.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `title` | VARCHAR(100) | Không | Chức danh/học hàm (ví dụ: "Ths.Bs", "Dr.", nullable) |
| ... | ... | ... | Các cột khác giữ nguyên |

**Migration:** `0042_add_user_title.py`

```sql
ALTER TABLE "user" ADD COLUMN title character varying(100);
```

---

## 7. SQL tổng hợp và truy vấn dữ liệu

Không áp dụng — tính năng này không có logic tổng hợp dữ liệu. Cấu hình lưu trong JSONB của clinic_settings, được quản lý thông qua Pydantic schema (không cần SQL tùy chỉnh).

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-001 | Khi cấu hình `show_weight=true`, nếu visit không có dữ liệu cân nặng (weight từ vitals), bảng in vẫn hiển thị nhãn "Cân nặng (kg)" nhưng giá trị để trống. | Hiển thị trống gọn gàng (không hiển thị "N/A" hoặc dấu gạch ngang), hoặc ẩn hẳn nếu config cho phép. |
| BR-002 | Khi cấu hình `show_diagnosis=true`, nếu visit không có diagnosis, sử dụng fallback `chief_complaint` từ visit. Nếu chief_complaint cũng trống, để trống field diagnosis. | Không hiển thị cảnh báo hoặc lỗi, chỉ để trống. |
| BR-003 | Danh sách thuốc được đệm tới `min_medicine_rows` dòng trống kẻ chấm. Ví dụ: nếu min_medicine_rows=6 nhưng chỉ có 3 thuốc, thêm 3 dòng trống kẻ chấm. Nếu thuốc > min_rows, in hết, không cắt. | Để nguyên số dòng in được (không cắt hoặc pad lại). |
| BR-004 | Chữ ký: lấy `user.full_name + user.title` từ profile bác sĩ khám (visit.doctor). Nếu user.title trống, dùng `signature_default` từ config. Nếu cả hai đều trống, hiển thị chỉ ngày/giờ + nhãn (không tên). | Không báo lỗi, chỉ để trống phần tên bác sĩ. |
| BR-005 | Khổ giấy: cấu hình `paper_size` được áp dụng bằng CSS `@page size: A5` hoặc `@page size: A4`. In dùng khổ giấy này. | Nếu in trên giấy khác, phần mềm in sẽ scale hoặc cắt tự động (không lỗi ứng dụng). |
| BR-006 | Khi in từ PrescriptionTab (draft flow), modal nhận chỉ dữ liệu prescription (không có patient/visit context). Các trường như họ tên BN, DOB, địa chỉ, chẩn đoán sẽ để trống. | Đây là hành vi được chấp nhận (draft print chỉ hiển thị thuốc và template). Là enhancement tương lai để tải thêm context từ API. |
| BR-007 | Footer (dòng 3+ của bản in): mỗi item trong `footer_lines` hiển thị trên một dòng riêng. | Không giới hạn số dòng (có thể mở rộng nếu config ghi nhiều dòng). |

---

## 9. Xử lý lỗi

### 9.1 Các mã lỗi phổ biến

| Mã HTTP | Mã lỗi | Tình huống xảy ra | Thông báo trả về |
|---------|--------|-------------------|-----------------|
| 200 | — | GET / PATCH thành công | Trả về đầy đủ ClinicSettingsResponse |
| 400 | INVALID_REQUEST | Request body không đúng format JSON | "Invalid request body" |
| 400 | VALIDATION_ERROR | `min_medicine_rows` ngoài phạm vi 1–20, hoặc `paper_size` không phải "A5"/"A4" | "Invalid value for min_medicine_rows (1-20)" hoặc "paper_size must be A5 or A4" |
| 401 | UNAUTHORIZED | Token không hợp lệ hoặc hết hạn | "Unauthorized" |
| 403 | FORBIDDEN | PATCH request nhưng user không có quyền `clinic.settings.update` | "Insufficient permissions" |
| 500 | INTERNAL_ERROR | Lỗi hệ thống (database crash, v.v.). *Trước BUG-080-001 fix: prescription_template field missing → 500 ValidationError* | "Internal server error" |

### 9.2 Định dạng phản hồi lỗi

```json
{
  "error": "Mã lỗi nội bộ",
  "message": "Mô tả lỗi chi tiết"
}
```

---

## 10. Ghi chú và lưu ý khi kiểm thử

### 10.1 Điểm quan trọng cần nắm

- **Cấu hình JSONB linh hoạt**: Clinic cũ trong DB có thể không có key `prescription_template`. Hệ thống tự động fill default values qua Pydantic schema khi GET settings, không cần migration JSONB.
- **Draft print limitation**: Khi in từ `PrescriptionTab` (draft flow), component chỉ nhận prescription object, không có patient/visit context. Các trường như họ tên, ngày sinh, địa chỉ, chẩn đoán sẽ để trống. Đây là hành vi dự kiến. Để in đầy đủ dữ liệu, in từ billing hoặc visit đã hoàn thành.
- **User.title field**: Thêm cột `user.title` (nullable VARCHAR(100)). Giá trị không được mã hoá (không phải PII nhạy cảm), chỉ chức danh. Nếu user không có title, fallback `signature_default` từ config.
- **Print dialog**: `window.print()` mở dialog in trình duyệt — không thể capture bằng Playwright. Kiểm thử thủ công hoặc bằng headless browser có in PDF tích hợp.

### 10.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| Cấu hình lần đầu | Admin chưa cấu hình, GET settings → prescription_template mặc định | Trả về default (tên="Phòng khám", min_rows=6, paper="A5", v.v.) |
| Cập nhật header | PATCH `header_clinic_name="Phòng khám Xanh"` | Bản in cập nhật header trong lần in tiếp theo |
| Thay đổi khổ giấy | PATCH `paper_size="A4"` | CSS @page size: A4 áp dụng, in trên A4 |
| In draft (PrescriptionTab) | Bác sĩ kê đơn 3 thuốc, nhấn in từ PrescriptionTab | HTML in: 3 dòng thuốc + 3 dòng trống (tới min_rows=6), BN tên/DOB/địa chỉ để trống |
| In full (billing) | In đơn từ invoice (visit hoàn thành, có BN + vitals) | HTML in: đầy đủ BN, cân nặng, chẩn đoán, chữ ký BS với title, footer |
| Ẩn cân nặng | Cấu hình `show_weight=false` | Bản in không hiển thị dòng "Cân nặng (kg)" |
| Ẩn chẩn đoán | Cấu hình `show_diagnosis=false` | Bản in không hiển thị dòng "Chẩn đoán" |
| Validation error | PATCH `min_medicine_rows=25` (ngoài 1–20) | Response 400: "min_medicine_rows must be between 1 and 20" |

### 10.3 Hạn chế hiện tại

- **PrescriptionTab draft print** không truyền patient/visit context → các trường họ tên, ngày sinh, địa chỉ, chẩn đoán để trống trên bản in. Đây là hành vi dự kiến, không phải defect (draft print chỉ hiển thị danh sách thuốc và cấu hình template).
- **Print dialog native** (`window.open()` + `win.print()`) không thể được Playwright/Selenium capture. Kiểm thử thủ công hoặc dùng headless browser có hỗ trợ PDF in tích hợp.
- **Khổ giấy runtime** CSS `@page size` không đổi động dễ dàng — giải pháp: render style `<style>@page { size: ... }</style>` theo config tại thời điểm in (đã áp dụng).

### 10.4 Hướng phát triển

- **Enhancement**: Thêm preview nút "Xem trước" trong SettingsPage để quản trị viên xem bản in mẫu trước khi lưu.
- **Enhancement**: PrescriptionTab draft print — thêm API call để lấy patient/visit context từ visitId, populate đầy đủ trường.
- **Enhancement**: Thêm tính năng mẫu in dạng template HTML tùy chỉnh (cho phép upload HTML template).

---

## Ảnh minh hoạ mẫu

![Mẫu đơn thuốc](../../refs/prescription-template-sample.png)

---

## Ảnh chụp test

### Admin Settings Panel

![Tab "Mẫu in đơn thuốc" đã tải](../test-reports/screenshots/PASS-settings-tab-loaded.png)

![Sau khi lưu cấu hình](../test-reports/screenshots/PASS-settings-saved.png)

![Xác nhận cấu hình được lưu](../test-reports/screenshots/PASS-settings-persistence-verified.png)

### In modal

![Modal in đơn từ billing](../test-reports/screenshots/PASS-print-modal-loaded.png)

---

**Tài liệu này mô tả chức năng trong tình trạng đã hoàn thành và kiểm thử (2026-06-16).**

