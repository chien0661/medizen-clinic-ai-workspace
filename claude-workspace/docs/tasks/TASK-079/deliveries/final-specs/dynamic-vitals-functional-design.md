# Thiết Kế Chi Tiết Tính Năng: Sinh Hiệu Động

**Dự án:** Clinic CMS  
**Task:** TASK-079  
**Phiên bản:** 1.0  
**Ngày:** 2026-06-16  
**Người thực hiện:** Code Implementation Agent + Code Review Agent + Test Agent  
**Trạng thái:** Hoàn thành  
**Tài liệu liên quan:** implementation-plan.md, review-report.md, test-report.md

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-06-16 | Phiên bản đầu tiên — tổng hợp sau hoàn thành implementation, review (APPROVED), testing (ALL PASS) |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Mô hình dữ liệu](#3-mô-hình-dữ-liệu)
- [4. Danh sách API](#4-danh-sách-api)
- [5. Chi tiết từng API](#5-chi-tiết-từng-api)
- [6. Quy tắc đánh giá trạng thái](#6-quy-tắc-đánh-giá-trạng-thái)
- [7. Hành vi form nhập sinh hiệu](#7-hành-vi-form-nhập-sinh-hiệu)
- [8. Xử lý lỗi và Validation](#8-xử-lý-lỗi-và-validation)
- [9. Tương thích ngược](#9-tương-thích-ngược)
- [10. Ghi chú và lưu ý khi kiểm thử](#10-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Module **vitals** (sinh hiệu) của Clinic CMS đã sở hữu một nền tảng **cấu hình động** tại backend: admin có thể thêm/sửa/xoá các chỉ số sinh hiệu, đặt khoảng bình thường (warning band), reset theo chuyên khoa, v.v.

Tuy nhiên, **form nhập sinh hiệu của bác sĩ vẫn hardcode 6 chỉ số cố định** và không lưu trạng thái **bình thường/không bình thường** một cách có cấu trúc. Khi bác sĩ nhập, trạng thái bị nhét vào chuỗi text `notes`, khiến:
- Admin thêm chỉ số mới → bác sĩ vẫn chỉ nhìn thấy 6 chỉ số cũ
- Không thể lọc/thống kê/tô màu dữ liệu lịch sử theo trạng thái sinh hiệu
- Dữ liệu trạng thái không cấu trúc, dễ parse sai

**TASK-079 giải quyết:**
1. **(Backend)** Mở rộng bảng `visit_vitals` với 2 cột JSONB `field_status` và `field_notes` để lưu **trạng thái BT/không-BT và ghi chú từng chỉ số** dưới dạng có cấu trúc.
2. **(Frontend)** Viết lại form nhập và timeline để **render động theo `/api/v1/vitals/definitions`**, loại bỏ hardcode, và gửi payload có cấu trúc.

### 1.2 Phạm vi

**Bao gồm:**
- Extend schema `visit_vitals` (2 cột JSONB, migration, validator, service update)
- Viết lại `VitalsTab.tsx`: render động, đánh giá BT/không-BT theo definition, structured payload, timeline động
- i18n mới (6 key VI + EN)
- Unit & integration test (23+25 BE, 12 FE)

**Không bao gồm:**
- Trend chart API (`GET /visits/{id}/vitals/trend` — TASK-041, TODO)
- Snapshot schema history (dùng định nghĩa hiện hành, có thể upgrade sau)
- Stored procedure hoặc batch reporting

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Admin (quản lý cấu hình)** | Sử dụng `/admin/vitals` để thêm/sửa/xoá chỉ số, đặt ngưỡng cảnh báo, reset preset |
| **Bác sĩ (nhập liệu)** | Sử dụng `VitalsTab` để nhập sinh hiệu cho bệnh nhân, đánh giá BT/không-BT, ghi chú |
| **Backend (clinic-cms)** | Cấu hình động (`vital_field_definition`), validator (`validate_annotations`), service, migration |
| **Frontend (clinic-cms-web)** | Fetch definitions, render form, timeline, i18n |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
┌─────────────────────────────────────────────────────────────────────┐
│ ADMIN: Cấu hình chỉ số sinh hiệu                                    │
├─────────────────────────────────────────────────────────────────────┤
│  1. Truy cập /admin/vitals                                          │
│  2. Thêm/sửa/xoá vital_field_definition                              │
│     (key, label, unit, min/max, warning_min/max, group_name, ...)   │
│  3. Lưu lại → vital_schema_version tăng                              │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND: VitalsTab fetch definitions                               │
├─────────────────────────────────────────────────────────────────────┤
│  1. useQuery(getVitalDefinitions())                                  │
│  2. GET /api/v1/vitals/definitions → response definitions[]          │
│  3. Render input dynamically: data_type, unit, required, group_name │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ BÁC SĨ: Nhập sinh hiệu bệnh nhân                                     │
├─────────────────────────────────────────────────────────────────────┤
│  1. Nhập giá trị từng chỉ số (theo form động)                        │
│  2. FE tự đánh giá BT/không-BT dựa warning_min/max → min/max        │
│  3. Bác sĩ có thể toggle thủ công trạng thái hoặc ghi chú            │
│  4. Save → send POST /visits/{id}/vitals                            │
│     {values, field_status, field_notes, notes?}                      │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ BACKEND: Validate & Persist                                         │
├─────────────────────────────────────────────────────────────────────┤
│  1. Validate values (existing validator)                             │
│  2. Validate annotations: field_status status ∈ {normal,abnormal}    │
│     → field_notes key phải tồn tại trong definition                  │
│  3. Persist vào visit_vitals:                                        │
│     · values (existing)                                              │
│     · field_status = {key: "normal"|"abnormal"} (JSONB)             │
│     · field_notes = {key: note_text} (JSONB)                        │
│     · vital_schema_version (snapshot)                                │
│  4. Return 201 + VisitVitalsResponse (toàn bộ fields)               │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ FRONTEND: Timeline xem lại & lịch sử                                │
├─────────────────────────────────────────────────────────────────────┤
│  1. GET /visits/{id}/vitals → list records với field_status/notes    │
│  2. Render động:                                                     │
│     · Hiện tất cả key từ definition + orphan keys từ values         │
│     · Tô màu row theo field_status: abnormal=🔴, normal=🟢           │
│     · Hiện field_notes[key] dưới giá trị                             │
│  3. Nếu chưa cấu hình → show vitals.noSchemaError                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|----------|----------------|
| 1 | **Admin cấu hình** | Admin truy cập `/admin/vitals`, thêm/sửa/xoá `vital_field_definition` với các thông số như `key` (định danh duy nhất), `label` (tên hiển thị), `unit`, `min_value`/`max_value` (khoảng bình thường cứng), `warning_min`/`warning_max` (khoảng cảnh báo mềm), `is_required` (bắt buộc), `group_name` (nhóm), `sort_order` (thứ tự), `data_type` (kiểu input: number/integer/text/boolean/select). |
| 2 | **FE fetch & render** | Khi bác sĩ mở `VitalsTab`, frontend gọi `GET /api/v1/vitals/definitions`, nhận về danh sách definitions theo `schema_version` hiện tại. Render form động theo `data_type`, nhóm theo `group_name`, sort `sort_order`. |
| 3 | **Bác sĩ nhập & đánh giá** | Bác sĩ nhập giá trị cho từng chỉ số. FE **tự động đánh giá** trạng thái dựa vào ngưỡng (priority: `warning_min/max` → `min/max` → không đánh giá). Bác sĩ có thể toggle thủ công hoặc thêm ghi chú. |
| 4 | **Gửi payload có cấu trúc** | Khi save, FE gửi `{values, field_status, field_notes, notes?}` — không nối chuỗi text vào `notes`. Ví dụ: `{values: {heart_rate: 80, bp: "120/80"}, field_status: {heart_rate: "normal", bp: "abnormal"}, field_notes: {bp: "Huyết áp cao"}}` |
| 5 | **BE validate & persist** | Backend validate: (a) values (existing logic), (b) annotations (status ∈ {normal, abnormal}, key tồn tại). Persist cả 3 thành phần vào `visit_vitals`, lưu snapshot `vital_schema_version`. |
| 6 | **Timeline hiển thị động** | Khi xem lại, FE `GET /visits/{id}/vitals`, render timeline: ưu tiên definition keys + orphan keys từ `values`. Tô màu theo `field_status`, hiện `field_notes` per-field. |

---

## 3. Mô hình dữ liệu

### 3.1 Schema `visit_vitals` — Thêm 2 cột JSONB

**Bảng hiện trạng (trước TASK-079):**
```
id | visit_id | values | notes | created_at | ...
```

**Sau TASK-079 (migration 0041_add_vital_field_status):**
```
id | visit_id | values | notes | field_status | field_notes | vital_schema_version | created_at | ...
```

**Chi tiết 2 cột mới:**

| Cột | Kiểu | Nullable | Default | Mô tả |
|-----|------|----------|---------|-------|
| `field_status` | JSONB | Có | `'{}'::jsonb` | Map `{key: "normal" \| "abnormal"}` cho từng chỉ số. Ví dụ: `{"heart_rate": "normal", "bp": "abnormal"}` |
| `field_notes` | JSONB | Có | `'{}'::jsonb` | Map `{key: note_text}` cho từng chỉ số. Ví dụ: `{"bp": "Huyết áp cao do stress"}` |

**Lưu ý:**
- Cả hai cột **nullable** để **tương thích ngược** (dữ liệu cũ không có cột này → populate `server_default='{}'`)
- Dữ liệu cũ (trước migration): `field_status = {}`, `field_notes = {}` → FE xử lý bình thường
- `vital_schema_version` (cột hiện có) là snapshot của version định nghĩa tại lúc nhập → giúp xác định chính xác chỉ số nào được nhập (nếu admin sau đó xoá định nghĩa)

### 3.2 Ví dụ Payload Lưu & Đọc

**Request: POST /api/v1/visits/{id}/vitals**
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
    "bp": "Huyết áp cao, yêu cầu tái đo sau 5 phút"
  },
  "notes": "(optional) Ghi chú chung thêm"
}
```

**Response: GET /api/v1/visits/{id}/vitals (list)**
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
        "bp": "Huyết áp cao, yêu cầu tái đo sau 5 phút"
      },
      "vital_schema_version": 3,
      "notes": "(optional ghi chú chung)",
      "created_at": "2026-06-16T10:30:00Z",
      "is_primary": true
    }
  ]
}
```

---

## 4. Danh sách API

**Đường dẫn gốc:** `/api/v1`  
**Xác thực:** Bắt buộc (Bearer token)

| STT | Phương thức | Đường dẫn | Mô tả |
|-----|------------|-----------|-------|
| 1 | GET | `/vitals/definitions` | Lấy danh sách định nghĩa chỉ số sinh hiệu (schema hiện hành) |
| 2 | POST | `/visits/{id}/vitals` | Nhập sinh hiệu mới (với trạng thái + ghi chú có cấu trúc) |
| 3 | GET | `/visits/{id}/vitals` | Lấy lịch sử sinh hiệu của bệnh nhân |

---

## 5. Chi tiết từng API

### 5.1 Lấy danh sách định nghĩa chỉ số

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/vitals/definitions` |
| **Mô tả** | Trả về danh sách tất cả định nghĩa chỉ số sinh hiệu có sẵn theo schema version hiện hành. FE dùng để render form nhập động. |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

Không có tham số (hoặc có thể filter theo `clinic_id` nếu có preset per-specialty).

#### Kết quả trả về

**Thành công (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "key": "heart_rate",
      "label": "Nhịp tim",
      "unit": "lần/phút",
      "data_type": "number",
      "min_value": 60,
      "max_value": 100,
      "warning_min": 60,
      "warning_max": 100,
      "is_required": true,
      "group_name": "Tuyến tim mạch",
      "sort_order": 1,
      "options": null,
      "help_text": "Nhịp tim bình thường 60-100 lần/phút"
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
      "help_text": "Nhập dạng SBP/DBP (vd: 120/80)"
    },
    {
      "id": 3,
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
        {"value": "underweight", "label": "Thiếu cân"},
        {"value": "normal", "label": "Bình thường"},
        {"value": "overweight", "label": "Thừa cân"},
        {"value": "obese", "label": "Béo phì"}
      ],
      "help_text": "Chỉ số BMI được tính tự động nếu có height/weight"
    }
  ],
  "total": 8
}
```

**Mô tả các trường:**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `key` | String | Định danh duy nhất chỉ số (ví dụ: `heart_rate`, `bp`, `temperature`) |
| `label` | String | Tên hiển thị (VI) |
| `unit` | String | Đơn vị (ví dụ: "lần/phút", "°C", "mmHg") |
| `data_type` | String | Kiểu input: `number`, `integer`, `text`, `boolean`, `select` |
| `min_value` | Number \| null | Giá trị tối thiểu bình thường (cứng) |
| `max_value` | Number \| null | Giá trị tối đa bình thường (cứng) |
| `warning_min` | Number \| null | Giá trị tối thiểu cảnh báo (mềm) |
| `warning_max` | Number \| null | Giá trị tối đa cảnh báo (mềm) |
| `is_required` | Boolean | Có bắt buộc nhập không |
| `group_name` | String | Nhóm chỉ số (ví dụ: "Tuyến tim mạch", "Hô hấp") |
| `sort_order` | Integer | Thứ tự hiển thị trong nhóm |
| `options` | Array \| null | Danh sách tùy chọn cho `data_type=select` |
| `help_text` | String | Text hỗ trợ/placeholder |

### 5.2 Nhập sinh hiệu mới

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/visits/{id}/vitals` |
| **Mô tả** | Tạo bản ghi sinh hiệu mới cho bệnh nhân, lưu trạng thái bình thường/không bình thường và ghi chú từng chỉ số có cấu trúc. |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào (Request Body)

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `values` | Object | Có | Map `{key: giá_trị}` — giá trị sinh hiệu nhập vào (kiểu phụ thuộc `data_type`) |
| `field_status` | Object | Không | Map `{key: "normal" \| "abnormal"}` — trạng thái mỗi chỉ số (tự động hoặc bác sĩ toggle) |
| `field_notes` | Object | Không | Map `{key: ghi_chú}` — ghi chú riêng cho từng chỉ số |
| `notes` | String | Không | Ghi chú chung (nguyên bản cũ, tương thích) |

**Ví dụ request:**
```json
{
  "values": {
    "heart_rate": 88,
    "bp": "130/85",
    "temperature": 36.8
  },
  "field_status": {
    "heart_rate": "normal",
    "bp": "abnormal"
  },
  "field_notes": {
    "bp": "Huyết áp cao, tái đo lại"
  }
}
```

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận request từ FE, kiểm tra visit_id tồn tại + quyền write |
| 2 | Validate `values` (tương thích type, required check, range check) — nếu lỗi → 422 |
| 3 | Validate `field_status` (status ∈ {normal,abnormal}, key tồn tại trong definition) — nếu lỗi → 422 |
| 4 | Validate `field_notes` (key phải tồn tại trong definition) — nếu lỗi → 422 |
| 5 | Persist bản ghi mới vào `visit_vitals` với `field_status`, `field_notes`, snapshot `vital_schema_version` |
| 6 | Trả 201 Created + `VisitVitalsResponse` (toàn bộ fields) |

#### Kết quả trả về

**Thành công (201 Created):**
```json
{
  "id": 1001,
  "visit_id": 555,
  "values": {
    "heart_rate": 88,
    "bp": "130/85",
    "temperature": 36.8
  },
  "field_status": {
    "heart_rate": "normal",
    "bp": "abnormal"
  },
  "field_notes": {
    "bp": "Huyết áp cao, tái đo lại"
  },
  "vital_schema_version": 3,
  "notes": null,
  "is_primary": true,
  "created_at": "2026-06-16T10:30:00Z"
}
```

**Lỗi Validation (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "field": "field_status",
      "code": "INVALID_STATUS",
      "message": "Status phải là 'normal' hoặc 'abnormal', nhận được: 'abnormal_value'"
    },
    {
      "field": "field_notes",
      "code": "UNKNOWN_KEY",
      "message": "Khóa 'ghost_field' không tồn tại trong định nghĩa"
    }
  ]
}
```

### 5.3 Lấy lịch sử sinh hiệu

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/visits/{id}/vitals` |
| **Mô tả** | Lấy tất cả bản ghi sinh hiệu của một lần khám (có thể nhiều bản, tùy theo cấu hình `is_primary` hoặc quá trình khám). |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `id` | Path param | visit_id |
| `is_primary` | Query (optional) | Lọc `is_primary=true` nếu chỉ muốn bản ghi chính |

#### Kết quả trả về

**Thành công (200 OK):**
```json
{
  "data": [
    {
      "id": 1001,
      "visit_id": 555,
      "values": {
        "heart_rate": 88,
        "bp": "130/85",
        "temperature": 36.8
      },
      "field_status": {
        "heart_rate": "normal",
        "bp": "abnormal"
      },
      "field_notes": {
        "bp": "Huyết áp cao"
      },
      "vital_schema_version": 3,
      "created_at": "2026-06-16T10:30:00Z",
      "is_primary": true
    },
    {
      "id": 1002,
      "visit_id": 555,
      "values": {
        "heart_rate": 82
      },
      "field_status": {
        "heart_rate": "normal"
      },
      "field_notes": {},
      "vital_schema_version": 3,
      "created_at": "2026-06-16T10:45:00Z",
      "is_primary": false
    }
  ]
}
```

---

## 6. Quy tắc đánh giá trạng thái

### 6.1 Thuật toán auto-detect status

FE tự động đánh giá trạng thái **bình thường (normal)** hay **không bình thường (abnormal)** dựa vào giá trị nhập và ngưỡng từ definition:

**Ưu tiên (Priority):**

| Bước | Quy tắc | Kết quả |
|------|--------|--------|
| 1 | Nếu definition có `warning_min` + `warning_max` → dùng cặp này | Nếu giá trị nằm trong [warning_min, warning_max] → `normal`, ngoài → `abnormal` |
| 2 | Nếu không, mà có `min_value` + `max_value` → dùng cặp này | Nếu giá trị nằm trong [min_value, max_value] → `normal`, ngoài → `abnormal` |
| 3 | Nếu không có cặp nào → không auto-detect | FE sẽ không đánh giá tự động, yêu cầu bác sĩ toggle thủ công |

**Ví dụ:**

Định nghĩa chỉ số `heart_rate`:
```json
{
  "key": "heart_rate",
  "min_value": 50,
  "max_value": 120,
  "warning_min": 60,
  "warning_max": 100
}
```

| Giá trị nhập | Kết luận | Lý do |
|------------|---------|-------|
| 55 | normal | Nằm trong [60, 100] (warning band) |
| 65 | normal | Nằm trong [60, 100] (warning band) |
| 45 | abnormal | Ngoài [60, 100], kiểm tra [50, 120] → still ok nhưng < 60 warning → abnormal |
| 110 | abnormal | > 100 (warning_max) |
| 30 | abnormal | < 50 (min_value) |

### 6.2 Bác sĩ có thể override

Bác sĩ luôn có quyền **toggle thủ công** trạng thái từ auto-detected sang cái khác. Ví dụ:
- FE auto-detect: `heart_rate=55` → normal
- Bác sĩ toggle → abnormal (nếu có lý do riêng, ví dụ: nhân không đều, v.v.)

---

## 7. Hành vi form nhập sinh hiệu

### 7.1 Render động theo definition

1. FE gọi `GET /api/v1/vitals/definitions`, lưu vào state
2. **Nhóm** chỉ số theo `group_name`
3. **Sắp xếp** trong nhóm theo `sort_order`
4. Render **input khác nhau** theo `data_type`:
   - `number` / `integer` → `<input type="number" step="...">`
   - `text` → `<input type="text" placeholder="..." help_text="...">`
   - `boolean` → `<input type="checkbox">`
   - `select` → `<select><option>...` (options từ definition)

5. Hiển thị:
   - `label` (tên chỉ số)
   - `unit` (đơn vị)
   - `help_text` (ghi chú hỗ trợ)
   - **required marker** nếu `is_required=true`

### 7.2 Auto-evaluate status

Khi bác sĩ nhập giá trị → FE lập tức:
1. So sánh với `warning_min/max` hoặc `min_value/max_value`
2. Gán `field_status[key]` = `"normal"` hoặc `"abnormal"`
3. Hiển thị **visual indicator** (ví dụ: 🟢 normal, 🔴 abnormal)

### 7.3 Bác sĩ thêm ghi chú

Dưới hoặc bên cạnh mỗi input, có một text field cho ghi chú riêng:
- Placeholder: `"Ghi chú cho chỉ số này..."` (i18n: `vitals.noteFor`)
- Khi nhập → lưu vào `field_notes[key]`

### 7.4 Toggle thủ công

Khi nhấn vào status indicator → toggle giữa `normal` ↔ `abnormal`:
- FE cập nhật `field_status[key]` ngay
- **Không xóa** `field_notes[key]` (giữ ghi chú)

### 7.5 BMI tính dẫn xuất

Nếu definition có các key `height` và `weight`:
1. FE **tự tính** BMI = weight / (height/100)²
2. Hiển thị BMI như một chỉ số read-only
3. **Không** lưu cột BMI riêng → tính lại mỗi lần xem

### 7.6 Gửi payload

Khi bác sĩ nhấn Save:
```json
{
  "values": {
    "heart_rate": 80,
    "bp": "120/80",
    "temperature": 36.5,
    ...
  },
  "field_status": {
    "heart_rate": "normal",
    "bp": "normal",
    "temperature": "normal",
    ...
  },
  "field_notes": {
    "bp": "Tái đo lần 2"
  }
}
```

**Điểm chính:**
- **Không nối chuỗi** text vào `notes` (như cách cũ)
- `field_status` và `field_notes` là **structured objects**
- Gửi chỉ những key có dữ liệu (không gửi key rỗng)

---

## 8. Xử lý lỗi và Validation

### 8.1 Validation `values`

Vẫn tuân theo logic hiện có:
- Required check: nếu `is_required=true` mà không có giá trị → lỗi
- Type check: giá trị phải match `data_type` (number, text, boolean, v.v.)
- Range check: nếu có min/max → kiểm tra boundary

**HTTP code:** 422 Unprocessable Entity

### 8.2 Validation `field_status`

- **Status value phải ∈ {normal, abnormal}** → nếu giá trị khác (ví dụ: `"maybe"`, `"critical"`) → 422
- **Key phải tồn tại** trong definition hiện hành → nếu key lạ → 422
- **Empty values bỏ qua** → `field_status[key] = ""` → không lỗi, chỉ bỏ qua

**Lỗi ví dụ:**
```json
{
  "detail": [
    {
      "field": "field_status",
      "code": "INVALID_STATUS",
      "message": "Status phải là 'normal' hoặc 'abnormal', nhận được: 'critical'"
    }
  ]
}
```

### 8.3 Validation `field_notes`

- **Key phải tồn tại** trong definition → nếu key lạ → 422
- **Empty strings bỏ qua** → không lỗi

**Lỗi ví dụ:**
```json
{
  "detail": [
    {
      "field": "field_notes",
      "code": "UNKNOWN_KEY",
      "message": "Khóa 'ghost_field' không tồn tại trong định nghĩa"
    }
  ]
}
```

### 8.4 Xử lý No Schema

Nếu `GET /api/v1/vitals/definitions` trả về danh sách rỗng:
- FE hiển thị **error banner**: `vitals.noSchemaError` = "Chưa cấu hình chỉ số sinh hiệu. Vui lòng liên hệ quản trị viên."
- Disable form nhập

---

## 9. Tương thích ngước

### 9.1 Dữ liệu cũ (trước migration 0041)

**Trước:** Không có cột `field_status`, `field_notes`  
**Migration xử lý:**
- Thêm cột với `nullable=True`, `server_default='{}'::jsonb`
- Dữ liệu cũ tự động nhận `field_status = {}`, `field_notes = {}`

### 9.2 Reading old data

**FE:**
```javascript
const status = record.field_status ?? {};  // Fallback {}
const notes = record.field_notes ?? {};    // Fallback {}
```

**Timeline xem lại dữ liệu cũ:**
- Hiển thị bình thường, không lỗi
- Không có status indicator (vì `field_status = {}`)
- Không có ghi chú per-field (vì `field_notes = {}`)

### 9.3 Backward-compat request/response

**POST request không có field_status/field_notes:**
```json
{
  "values": {...},
  "notes": "Ghi chú chung"
}
```
→ Backend xử lý: `field_status` = {}, `field_notes` = {} (defaults)  
→ HTTP 201 OK

**GET response cho record cũ:**
```json
{
  "field_status": {},
  "field_notes": {}
}
```
→ FE hiển thị không có status (ok)

---

## 10. Ghi chú và lưu ý khi kiểm thử

### 10.1 Điểm quan trọng

- **Definition-driven**: Khi admin thêm chỉ số mới, bác sĩ **không cần reload code**, form tự hiển thị. Điều này là **yêu cầu chính** của TASK-079.
- **Structured status**: Không dùng parse chuỗi `notes` để xác định trạng thái — toàn bộ logic phụ thuộc `field_status` JSONB.
- **Snapshot schema version**: Mỗi record lưu snapshot `vital_schema_version` tại thời điểm nhập, giúp xác định exact nào là definition lúc đó.
- **BMI tính dẫn xuất**: Không có cột BMI riêng → tính lại mỗi lần.
- **Timeline động**: Hiển thị tất cả key từ definition + orphan key từ `values` (để không mất dữ liệu nếu admin xoá definition).

### 10.2 Gợi ý test scenario

| Kịch bản | Bước thực hiện | Kết quả kỳ vọng |
|---------|-------|--------|
| Admin thêm chỉ số mới | 1. Truy cập /admin/vitals 2. Thêm định nghĩa `SpO2` với warning_min=95, warning_max=100 3. Bác sĩ reload VitalsTab | VitalsTab tự hiển thị input `SpO2`, không sửa code FE |
| Nhập & auto-detect | 1. Nhập `heart_rate=50` (< warning_min=60) 2. Xem status indicator | FE auto-detect abnormal (🔴), có thể toggle manual |
| Toggle thủ công | 1. Status=abnormal (auto) 2. Nhấn status indicator → toggle normal | Field_status[key] đổi sang "normal", giữ field_notes |
| Ghi chú per-field | 1. Nhập `bp=140/90` 2. Ghi chú: "Tái đo lần 2" 3. Save | field_notes[bp]="Tái đo lần 2" được lưu, đọc lại đúng |
| Timeline lịch sử | 1. POST → 201 2. Xem timeline 3. Reload page | Lịch sử hiển thị, status indicator (🔴/🟢) đúng, ghi chú per-field hiện |
| Backward compat | 1. Xem dữ liệu cũ (pre-migration) 2. Reload | Không lỗi, timeline hiển thị bình thường (không có status indicator) |
| No schema | 1. Xoá tất cả definition 2. Bác sĩ mở VitalsTab | Error banner: "Chưa cấu hình chỉ số sinh hiệu" |
| Invalid status | 1. POST với `field_status[key]="critical"` | 422 INVALID_STATUS |
| Unknown key | 1. POST với `field_notes[ghost_key]="..."` | 422 UNKNOWN_KEY |
| Multi-error | 1. POST với status sai + key lạ | 422 với error list (2 items) |

### 10.3 Hạn chế hiện tại

- **Timeline snapshot**: Dùng definition hiện hành để render timeline, có thể sai nếu admin xoá definition sau khi nhập. Có thể upgrade sau để lưu snapshot full definition.
- **BMI label hardcoded VI**: Chưa i18n cho EN. Có thể cải tiến sau khi cần EN parity.

### 10.4 Hướng phát triển (không trong phạm vi TASK-079)

- **TASK-041**: Trend chart API — lấy dữ liệu timeline, tính tối ưu hóa query.
- **Snapshot definition**: Lưu full definition snapshot tại thời điểm nhập → render timeline chính xác ngay cả khi admin xoá definition.
- **Bulk operation**: Batch edit trạng thái nhiều record.
- **Dashboard vitals**: Báo cáo thống kê abnormal rate, v.v.

---

## Phê duyệt

| Vai trò | Họ tên | Ngày | Trạng thái |
|---------|--------|------|-----------|
| Code Review | Code Review Agent | 2026-06-16 | APPROVED ✓ |
| Testing | Test Agent | 2026-06-16 | ALL PASS (48 BE + 12 FE) ✓ |
| Documentation | Documentation Agent | 2026-06-16 | Hoàn thành ✓ |

---

**Tài liệu này tổng hợp sau khi TASK-079 hoàn thành tất cả phase (Implementation → Review → Testing → Documentation). Tất cả acceptance criteria đều PASS.**
