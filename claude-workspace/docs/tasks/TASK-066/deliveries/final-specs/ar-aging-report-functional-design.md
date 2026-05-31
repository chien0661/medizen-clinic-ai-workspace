# Thiết Kế Chi Tiết Tính Năng: Báo Cáo Công Nợ Phải Thu (AR Aging)

**Dự án:** Clinic CMS  
**Task:** TASK-066  
**Phiên bản:** 1.0  
**Ngày:** 2026-05-31  
**Trạng thái:** Hoàn thành  
**Tài liệu liên quan:** 
- TASK-053 Functional Audit (phát hiện vấn đề MOCK_DATA)
- TASK-037 P2 — Encryption (EncryptedString for patient.full_name)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-05-31 | Bản hoàn chỉnh — gỡ MOCK_DATA, 3 endpoint mới, CSV export, doctor-weekly chart |

---

## Mục lục

1. [Tổng quan tính năng](#1-tổng-quan-tính-năng)
2. [Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
3. [Danh sách API](#3-danh-sách-api)
4. [Chi tiết từng API](#4-chi-tiết-từng-api)
5. [Cấu trúc cơ sở dữ liệu](#5-cấu-trúc-cơ-sở-dữ-liệu)
6. [SQL tổng hợp và truy vấn dữ liệu](#6-sql-tổng-hợp-và-truy-vấn-dữ-liệu)
7. [Quy tắc nghiệp vụ](#7-quy-tắc-nghiệp-vụ)
8. [Xử lý lỗi](#8-xử-lý-lỗi)
9. [Ghi chú khi kiểm thử](#9-ghi-chú-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Cung cấp báo cáo Công nợ Phải Thu (Accounts Receivable Aging — AR Aging) cho quản lý phòng khám, giúp:
- Theo dõi các hoá đơn chưa thanh toán theo độ tuổi (0-30 / 31-60 / 61-90 / >90 ngày)
- Xác định rủi ro dòng tiền (cash flow risk)
- Ưu tiên theo dõi thu nợ cho các khoản công nợ quá hạn
- Xuất báo cáo dạng CSV cho phân tích ngoài hệ thống

**Bối cảnh:** TASK-053 phát hiện lỗi nghiêm trọng — trang `ARAgingReportPage` hiển thị dữ liệu giả (30.1M VND) khi endpoint BE chưa sẵn sàng. TASK-066 triển khai 3 endpoint thực để thay thế dữ liệu giả hoàn toàn.

### 1.2 Phạm vi

**Bao gồm:**
- `GET /api/v1/reports/ar-aging` — lấy dữ liệu công nợ theo bucket
- `GET /api/v1/reports/ar-aging/export` — xuất CSV
- `GET /api/v1/reports/doctor-weekly` — dữ liệu tuần cho DoctorDashboard chart
- Gỡ MOCK_DATA từ `ARAgingReportPage.tsx` + `DoctorDashboardPage.tsx`

**Không bao gồm:**
- Chức năng ghi chú / follow-up công nợ (future task)
- Tích hợp SMS/Email thông báo (future task)
- Phân tích xu hướng dài hạn (TASK-056)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Người dùng cuối** | Quản lý tài chính, quản lý phòng khám — theo dõi công nợ và lên kế hoạch thu nợ |
| **Hệ thống cung cấp dữ liệu** | Bảng `invoice` (hoá đơn), `visit` (lượt khám), `patient` (bệnh nhân) — dữ liệu từ các module billing / clinic |
| **Hệ thống tiêu thụ** | `ARAgingReportPage` (FE), `DoctorDashboardPage` (weekly chart), CSV export tools |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
┌─────────────────────────────────────────────────────────────────┐
│ Người dùng FE (DashBoard / Reports)                              │
│ - ARAgingReportPage.tsx                                          │
│ - DoctorDashboardPage.tsx (weekly chart)                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ GET /api/v1/reports/ar-aging?as_of=YYYY-MM-DD
                       │ GET /api/v1/reports/ar-aging/export
                       │ GET /api/v1/reports/doctor-weekly?doctor_id=&ref_date=
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ BE FastAPI Routes (app/modules/reports/api/routes.py)           │
│ - require_permission("report.financial") — AR aging endpoints   │
│ - require_permission("report.view") — doctor-weekly endpoint    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│ get_ar_aging │ │build_ar_aging│ │get_doctor_weekly │
│   (service)  │ │    _csv      │ │    (service)     │
│              │ │  (CSV export)│ │                  │
└──────┬───────┘ └──────┬───────┘ └────────┬─────────┘
       │                │                  │
       ▼                ▼                  ▼
┌────────────────────────────────────────────────────┐
│ SQL Queries (Raw text() for aggregation)           │
│ - Join invoice → visit → patient                   │
│ - Age bucket calculation (CASE WHEN)               │
│ - RLS context (clinic_id isolation)                │
└────────────────────┬───────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────┐
│ Database (PostgreSQL)                              │
│ - invoice, visit, patient tables                   │
│ - EncryptedString column for patient.full_name     │
│ - RLS policies for clinic_id isolation             │
└────────────────────────────────────────────────────┘
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Người dùng yêu cầu dữ liệu | Client gọi `/reports/ar-aging` hoặc `/reports/doctor-weekly` với date range / doctor filter |
| 2 | Kiểm tra xác thực | FastAPI kiểm tra JWT token — từ chối nếu không hợp lệ |
| 3 | Kiểm tra quyền | Kiểm tra permission: `report.financial` cho AR aging, `report.view` cho doctor-weekly — từ chối nếu thiếu |
| 4 | Lấy clinic_id từ context | TenancyMiddleware thiết lập current_clinic_id ContextVar từ token claims |
| 5 | Truy vấn DB — Raw SQL | Thực thi SQL aggregate kèm RLS context — tính bucket, tổng hợp theo patient |
| 6 | Giải mã full_name | ORM load Patient objects — EncryptedString TypeDecorator tự động giải mã full_name từ BYTEA |
| 7 | Xây dựng response | Merge dữ liệu bucket + decrypted full_name → ARAgingReport / DoctorWeeklyReport |
| 8 | CSV export (nếu /export) | Render report → CSV bytes với UTF-8 BOM + formula injection guard |
| 9 | Trả dữ liệu | Gửi JSON response hoặc StreamingResponse (CSV bytes) cho client |
| 10 | FE render | ARAgingReportPage / DoctorDashboardPage hiển thị dữ liệu thực hoặc error state |

---

## 3. Danh sách API

**Base Path:** `/api/v1/reports`

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt | Permission |
|-----|------------|-----------|--------------|-----------|
| 1 | GET | `/ar-aging` | Lấy báo cáo công nợ phải thu theo bucket tuổi | `report.financial` |
| 2 | GET | `/ar-aging/export` | Xuất CSV công nợ phải thu | `report.financial` |
| 3 | GET | `/doctor-weekly` | Lấy số lượt khám hoàn thành theo ngày trong tuần | `report.view` |

---

## 4. Chi tiết từng API

### 4.1 GET /api/v1/reports/ar-aging

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `GET /api/v1/reports/ar-aging` |
| **Mô tả** | Lấy báo cáo Công nợ Phải Thu (AR Aging): tổng hợp các hoá đơn chưa thanh toán / thanh toán một phần theo độ tuổi (0-30 / 31-60 / 61-90 / >90 ngày từ ngày phát hành). Trả về tổng cộng theo từng bucket và chi tiết từng bệnh nhân. |
| **Xác thực** | Bắt buộc (JWT token) |
| **Permission** | `report.financial` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `as_of` | string (ISO 8601) | Không | Ngày tham chiếu để tính tuổi hoá đơn. Format: `YYYY-MM-DD` | Hôm nay (UTC) |

**Ví dụ:**
```
GET /api/v1/reports/ar-aging?as_of=2026-05-31
Authorization: Bearer {token}
```

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra token xác thực — từ chối nếu không hợp lệ |
| 2 | Kiểm tra permission `report.financial` — từ chối nếu thiếu |
| 3 | Parse `as_of` parameter — mặc định là hôm nay nếu không truyền |
| 4 | Lấy `clinic_id` từ JWT claims (TenancyMiddleware) |
| 5 | Thực thi SQL aggregate (xem §6.2) — tính bucket, tổng hợp invoice/visit/patient |
| 6 | ORM load Patient objects để giải mã `full_name` (BYTEA EncryptedString) |
| 7 | Merge dữ liệu bucket + full_name → ARAgingPatientRow list |
| 8 | Tính toán grand totals (tổng cộng các bucket) |
| 9 | Trả ARAgingReport JSON |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "as_of_date": "2026-05-31",
  "total_0_30": 5000000.00,
  "total_31_60": 3500000.00,
  "total_61_90": 2100000.00,
  "total_over_90": 800000.00,
  "grand_total": 11400000.00,
  "patients": [
    {
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "patient_code": "BN001",
      "patient_name": "Nguyễn Văn A",
      "bucket_0_30": 2000000.00,
      "bucket_31_60": 1500000.00,
      "bucket_61_90": 500000.00,
      "bucket_over_90": 0.00,
      "total_outstanding": 4000000.00
    }
  ]
}
```

**Mô tả các trường kết quả:**

| Trường | Kiểu | Mô tả ý nghĩa nghiệp vụ |
|--------|------|------------------------|
| `as_of_date` | string | Ngày tham chiếu (YYYY-MM-DD) |
| `total_0_30` | decimal | Tổng công nợ tuổi 0-30 ngày |
| `total_31_60` | decimal | Tổng công nợ tuổi 31-60 ngày |
| `total_61_90` | decimal | Tổng công nợ tuổi 61-90 ngày |
| `total_over_90` | decimal | Tổng công nợ tuổi >90 ngày (nguy hiểm nhất) |
| `grand_total` | decimal | Tổng cộng tất cả công nợ |
| `patients` | array | Danh sách chi tiết công nợ từng bệnh nhân |

---

### 4.2 GET /api/v1/reports/ar-aging/export

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `GET /api/v1/reports/ar-aging/export` |
| **Mô tả** | Xuất báo cáo Công nợ Phải Thu dạng CSV (UTF-8 với BOM để Excel đọc đúng encoding). Bao gồm các hàng chi tiết per patient và hàng tổng cộng cuối cùng. |
| **Xác thực** | Bắt buộc |
| **Permission** | `report.financial` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `as_of` | string (ISO 8601) | Không | Ngày tham chiếu | Hôm nay |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra token + permission (giống `/ar-aging`) |
| 2 | Gọi `get_ar_aging()` để lấy dữ liệu |
| 3 | Gọi `build_ar_aging_csv(report)` — render CSV từ report object |
| 4 | Thêm UTF-8 BOM (byte sequence `EF BB BF`) để Excel đọc đúng |
| 5 | Trả StreamingResponse với `Content-Type: text/csv` + `Content-Disposition: attachment` |

#### Kết quả trả về

**Thành công (200 OK):**

```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="ar-aging-2026-05-31.csv"

Mã BN,Tên bệnh nhân,0-30 ngày,31-60 ngày,61-90 ngày,>90 ngày,Tổng công nợ
BN001,Nguyễn Văn A,2000000.00,1500000.00,500000.00,0.00,4000000.00
BN002,Trần Thị B,3000000.00,2000000.00,1600000.00,800000.00,7400000.00
TỔNG CỘNG,,5000000.00,3500000.00,2100000.00,800000.00,11400000.00
```

**Bảo vệ Công thức Injection (Formula Injection Guard):**  
Bất kỳ giá trị cell nào bắt đầu bằng `=`, `+`, `-`, `@`, TAB hoặc CR đều được thêm dấu ngoặc đơn (`'`) ở đầu để tránh bị Excel hiểu nhầm là công thức. Ví dụ: nếu mã BN là `=IMPORTXML(...)`, file CSV sẽ chứa `'=IMPORTXML(...)`.

---

### 4.3 GET /api/v1/reports/doctor-weekly

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `GET /api/v1/reports/doctor-weekly` |
| **Mô tả** | Lấy số lượt khám hoàn thành theo từng ngày trong tuần (T2–CN / Mon–Sun) cho một bác sĩ cụ thể hoặc tất cả. Dùng để vẽ biểu đồ trend tuần trên DoctorDashboard. |
| **Xác thực** | Bắt buộc |
| **Permission** | `report.view` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `doctor_id` | string (UUID) | Không | Lọc theo bác sĩ cụ thể | Tất cả bác sĩ (null) |
| `ref_date` | string (ISO 8601) | Không | Ngày bất kỳ trong tuần ISO muốn truy vấn | Hôm nay |

**Ví dụ:**
```
# Tất cả bác sĩ, tuần hiện tại
GET /api/v1/reports/doctor-weekly
Authorization: Bearer {token}

# Bác sĩ cụ thể, tuần cụ thể
GET /api/v1/reports/doctor-weekly?doctor_id=550e8400-e29b-41d4-a716-446655440000&ref_date=2026-05-29
Authorization: Bearer {token}
```

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra token xác thực + permission `report.view` |
| 2 | Parse `ref_date` (mặc định hôm nay) |
| 3 | Tính toán tuần ISO: Monday → Sunday chứa `ref_date` |
| 4 | Thực thi SQL (xem §6.3) — đếm lượt khám hoàn thành (status IN COMPLETED, AWAITING_PAYMENT) theo ngày tuần |
| 5 | Xây dựng 7 hàng (T2–CN) — zero-fill các ngày không có lượt khám |
| 6 | Trả DoctorWeeklyReport JSON |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "clinic_id": "770e8400-e29b-41d4-a716-446655440002",
  "doctor_id": "550e8400-e29b-41d4-a716-446655440000",
  "week_start": "2026-05-25",
  "week_end": "2026-05-31",
  "rows": [
    { "day_of_week": 0, "day_label": "T2", "count": 5 },
    { "day_of_week": 1, "day_label": "T3", "count": 7 },
    { "day_of_week": 2, "day_label": "T4", "count": 6 },
    { "day_of_week": 3, "day_label": "T5", "count": 4 },
    { "day_of_week": 4, "day_label": "T6", "count": 8 },
    { "day_of_week": 5, "day_label": "T7", "count": 3 },
    { "day_of_week": 6, "day_label": "CN", "count": 1 }
  ]
}
```

**Mô tả các trường:**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `clinic_id` | UUID | Phòng khám (tenant scope) |
| `doctor_id` | UUID / null | Bác sĩ (null = tất cả) |
| `week_start` | date | Thứ Hai của tuần ISO (YYYY-MM-DD) |
| `week_end` | date | Chủ nhật của tuần ISO (YYYY-MM-DD) |
| `rows[].day_of_week` | int | 0=T2, 1=T3, ..., 6=CN |
| `rows[].day_label` | string | Nhãn tiếng Việt ("T2", "T3", ..., "CN") |
| `rows[].count` | int | Số lượt khám hoàn thành hôm đó |

---

## 5. Cấu trúc cơ sở dữ liệu

### 5.1 Tổng quan các bảng

| Bảng | Mục đích |
|------|---------|
| `invoice` | Các hoá đơn khám chữa bệnh — chứa `issued_at`, `balance_due`, `status` (issued / partially_paid / paid) |
| `visit` | Các lượt khám — FK `patient_id`, `doctor_id`, `visit_date`, `status` (COMPLETED / AWAITING_PAYMENT / CANCELLED) |
| `patient` | Danh sách bệnh nhân — chứa `patient_code` (plaintext), `full_name` (BYTEA EncryptedString) |

### 5.2 Chi tiết bảng liên quan

#### Bảng: `invoice`

**Mô tả:** Lưu các hoá đơn khám chữa bệnh — được sinh ra từ lượt khám (visit). AR aging truy vấn bảng này để tìm các hoá đơn chưa thanh toán / thanh toán một phần.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Tenant scope (RLS filter) |
| `visit_id` | UUID (FK) | Có | Liên kết đến visit |
| `issued_at` | TIMESTAMP | Có | Ngày phát hành hoá đơn — dùng để tính tuổi công nợ |
| `total_amount` | DECIMAL(15,2) | Có | Tổng tiền hoá đơn |
| `balance_due` | DECIMAL(15,2) | Có | Số tiền còn phải trả (0 nếu đã thanh toán hết) |
| `status` | VARCHAR | Có | 'issued' (chưa thanh toán) / 'partially_paid' (thanh toán một phần) / 'paid' (đã thanh toán) |
| `is_deleted` | BOOLEAN | Có | Soft delete flag |

#### Bảng: `visit`

**Mô tả:** Lưu các lượt khám. AR aging join bảng này qua `visit_id` để lấy `patient_id` (FK → patient).

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Tenant scope |
| `patient_id` | UUID (FK) | Có | Liên kết đến patient |
| `doctor_id` | UUID (FK) | Có | Liên kết đến doctor |
| `visit_date` | DATE | Có | Ngày khám (không có giờ) |
| `status` | VARCHAR | Có | 'COMPLETED' / 'AWAITING_PAYMENT' / 'CANCELLED' / v.v. |
| `is_deleted` | BOOLEAN | Có | Soft delete flag |

#### Bảng: `patient`

**Mô tả:** Danh sách bệnh nhân. AR aging load Patient ORM objects để giải mã `full_name` (BYTEA ciphertext).

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Tenant scope |
| `patient_code` | VARCHAR(50) | Có | Mã BN (plaintext) — hiển thị trong báo cáo |
| `full_name` | BYTEA | Có | Họ tên (EncryptedString — BYTEA ciphertext, giải mã qua ORM) — từ TASK-037 P2 |
| `is_deleted` | BOOLEAN | Có | Soft delete flag |

---

## 6. SQL tổng hợp và truy vấn dữ liệu

### 6.1 Truy vấn AR Aging — Tổng hợp theo Bucket

**Mục đích:**  
Lấy dữ liệu tổng hợp công nợ theo độ tuổi hoá đơn từ ngày phát hành (`issued_at`) đến ngày tham chiếu (`as_of`). Tính toán 4 bucket (0-30 / 31-60 / 61-90 / >90 ngày) cho từng bệnh nhân. Chỉ bao gồm hoá đơn có status = 'issued' (chưa thanh toán) hoặc 'partially_paid' (thanh toán một phần).

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `clinic_id` | `invoice.clinic_id`, `visit.clinic_id`, `patient.clinic_id` | Tenant isolation — RLS + explicit WHERE |
| `as_of` | Tính toán tuổi: `(as_of - DATE(issued_at))` | Mặc định = hôm nay (UTC) |
| `statuses` | `invoice.status` | IN ('issued', 'partially_paid') |

**SQL Truy vấn (PostgreSQL — có RLS context):**

```sql
SELECT
    p.id                                   AS patient_id,
    p.patient_code                         AS patient_code,
    SUM(
        CASE WHEN (:as_of - DATE(i.issued_at AT TIME ZONE 'UTC')) BETWEEN 0 AND 30
             THEN i.balance_due ELSE 0 END
    )::numeric(15,2)                       AS bucket_0_30,
    SUM(
        CASE WHEN (:as_of - DATE(i.issued_at AT TIME ZONE 'UTC')) BETWEEN 31 AND 60
             THEN i.balance_due ELSE 0 END
    )::numeric(15,2)                       AS bucket_31_60,
    SUM(
        CASE WHEN (:as_of - DATE(i.issued_at AT TIME ZONE 'UTC')) BETWEEN 61 AND 90
             THEN i.balance_due ELSE 0 END
    )::numeric(15,2)                       AS bucket_61_90,
    SUM(
        CASE WHEN (:as_of - DATE(i.issued_at AT TIME ZONE 'UTC')) > 90
             THEN i.balance_due ELSE 0 END
    )::numeric(15,2)                       AS bucket_over_90,
    SUM(i.balance_due)::numeric(15,2)      AS total_outstanding
FROM invoice i
JOIN visit v   ON v.id = i.visit_id
               AND v.clinic_id = :clinic_id
               AND v.is_deleted = FALSE
JOIN patient p ON p.id = v.patient_id
               AND p.clinic_id = :clinic_id
               AND p.is_deleted = FALSE
WHERE i.clinic_id = :clinic_id
  AND i.is_deleted = FALSE
  AND i.status = ANY(:statuses)
  AND i.issued_at IS NOT NULL
  AND i.balance_due > 0
GROUP BY p.id, p.patient_code
ORDER BY total_outstanding DESC
```

**Giải thích:**
- **CASE WHEN:** Tính tuổi dưới dạng số ngày, so sánh với các boundary (30, 60, 90)
- **SUM(...) / GROUP BY:** Tổng hợp `balance_due` theo từng bệnh nhân
- **JOIN:** Kết nối invoice → visit → patient để lấy thông tin bệnh nhân
- **WHERE:** Chỉ lấy hoá đơn status = issued/partially_paid, balance_due > 0, is_deleted = FALSE
- **ORDER BY:** Sắp xếp theo công nợ lớn nhất trước

---

### 6.2 Truy vấn Doctor Weekly — Đếm Lượt Khám Hoàn Thành

**Mục đích:**  
Đếm số lượt khám hoàn thành theo từng ngày trong tuần ISO (T2–CN) để vẽ biểu đồ trend tuần trên DoctorDashboard. Chỉ tính các lượt khám có status = 'COMPLETED' hoặc 'AWAITING_PAYMENT'.

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `clinic_id` | `visit.clinic_id` | Tenant isolation |
| `week_start` / `week_end` | `visit_date` | Tuần ISO (T2–CN) |
| `doctor_id` | `visit.doctor_id` | Nếu null → tất cả bác sĩ |
| `statuses` | `visit.status` | IN ('COMPLETED', 'AWAITING_PAYMENT') |

**SQL Truy vấn (PostgreSQL):**

```sql
SELECT
    EXTRACT(ISODOW FROM visit_date)::int - 1  AS dow,   -- 0=Mon, 6=Sun
    COUNT(*)                                   AS cnt
FROM visit
WHERE clinic_id = :clinic_id
  AND is_deleted = FALSE
  AND status = ANY(:statuses)
  AND visit_date >= :week_start
  AND visit_date <= :week_end
  [AND doctor_id = :doctor_id]  -- optional filter
GROUP BY EXTRACT(ISODOW FROM visit_date)
ORDER BY dow ASC
```

**Giải thích:**
- **EXTRACT(ISODOW FROM visit_date) - 1:** Trích xuất ngày trong tuần ISO (1=T2 … 7=CN), trừ 1 để được 0=T2 … 6=CN
- **COUNT(*):** Đếm số lượt khám
- **GROUP BY dow:** Nhóm theo ngày
- **Optional filter doctor_id:** Nếu truyền doctor_id, chỉ tính lượt khám của bác sĩ đó

---

### 6.3 Logic Tính Toán Tham Số Truy Vấn

#### 6.3.1 Tuổi Hoá Đơn (Age Bucket)

| Tuổi (ngày) | Bucket | Biểu thức SQL |
|-------------|--------|--------------|
| 0–30 | Bucket 0-30 | `BETWEEN 0 AND 30` |
| 31–60 | Bucket 31-60 | `BETWEEN 31 AND 60` |
| 61–90 | Bucket 61-90 | `BETWEEN 61 AND 90` |
| >90 | Bucket >90 | `> 90` |

**Công thức tính tuổi:**
```
age = as_of_date - DATE(invoice.issued_at)
```

Ví dụ:
- Nếu `as_of = 2026-05-31` và `issued_at = 2026-05-01 10:30:00`:
  - Age = 2026-05-31 - 2026-05-01 = 30 ngày → Bucket 0-30
- Nếu `issued_at = 2026-04-01`:
  - Age = 2026-05-31 - 2026-04-01 = 60 ngày → Bucket 31-60

#### 6.3.2 Tuần ISO (ISO Week)

| Tham số | Biểu thức | Ví dụ |
|---------|-----------|-------|
| Input: `ref_date` | Bất kỳ ngày nào trong tuần mong muốn | 2026-05-29 (thứ 4) |
| Monday (week_start) | `ref_date - WEEKDAY(ref_date)` | 2026-05-25 |
| Sunday (week_end) | `Monday + 6 days` | 2026-05-31 |

**Công thức (PostgreSQL ISO Week):**
```sql
-- Lấy thứ Hai
week_start = ref_date - (EXTRACT(ISODOW FROM ref_date)::int - 1) * INTERVAL '1 day'
-- Lấy chủ nhật
week_end = week_start + 6 * INTERVAL '1 day'
```

Ví dụ:
- `ref_date = 2026-05-29` (Wednesday, ISODOW=3)
- `week_start = 2026-05-29 - 2 days = 2026-05-27` ❌ Sai!
- Chính xác: `week_start = 2026-05-25` (thứ Hai trước)

---

## 7. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm | Enforce |
|----|--------------|---------------------|---------|
| BR-001 | Chỉ các hoá đơn có status = 'issued' (chưa thanh toán) hoặc 'partially_paid' (thanh toán một phần) mới được tính vào AR aging. Các hoá đơn 'paid' (đã thanh toán) bị loại bỏ. | Hoá đơn đã thanh toán sẽ không hiển thị trong báo cáo | SQL WHERE: `status = ANY(:statuses)` |
| BR-002 | Phân loại bucket dựa trên tuổi hoá đơn (ngày): tuổi = as_of_date - DATE(issued_at). Ranh giới: 0-30 (current) / 31-60 (past due 1-2 tháng) / 61-90 (past due 2-3 tháng) / >90 (severely past due). | Hoá đơn được phân bucket sai sẽ dẫn báo cáo không chính xác | SQL CASE WHEN với logic ngày chính xác |
| BR-003 | Chỉ lấy hoá đơn có `balance_due > 0` (vẫn còn nợ). Nếu `balance_due = 0` (tất cả đã trả), không tính. | Hoá đơn không có nợ sẽ được loại bỏ | SQL WHERE: `balance_due > 0` |
| BR-004 | Isolation — chỉ trả về dữ liệu của clinic mà user đó có quyền xem. RLS database + explicit WHERE clause. | Cross-clinic data leak — người dùng phòng khám A thấy dữ liệu phòng khám B | RLS policies + WHERE `clinic_id = :clinic_id` |
| BR-005 | Hoá đơn thanh toán một phần (status = 'partially_paid'): dùng `balance_due` (số tiền còn lại) thay vì `total_amount` để tính nợ. | Báo cáo sẽ ghi nhận quá cao nợ của bệnh nhân | SQL: `SUM(i.balance_due)` |
| BR-006 | CSV export phải bảo vệ chống công thức injection (formula injection): bất kỳ cell nào bắt đầu bằng `=`, `+`, `-`, `@`, TAB, hoặc CR đều được thêm dấu ngoặc đơn ở đầu để Excel không hiểu nhầm là công thức. | Nếu mã BN là `=IMPORTXML(...)`, Excel sẽ chạy macro mà không hỏi → bảo mật lỏng | Hàm `_csv_safe()` kiểm tra ký tự đầu + thêm `'` |
| BR-007 | Doctor-weekly chỉ tính lượt khám có status = 'COMPLETED' hoặc 'AWAITING_PAYMENT'. Các trạng thái khác (CANCELLED, PENDING) không tính. | Báo cáo không chính xác về năng suất bác sĩ | SQL WHERE: `status = ANY(:statuses)` |
| BR-008 | FE không được hiển thị MOCK_DATA — khi API fail phải hiển thị error state rõ ràng (không ghi dữ liệu giả). | Người quản lý tưởng hệ thống có đủ chức năng nhưng thực chất là mock → lỗi trên go-live | FE code: gỡ MOCK_DATA const, catch error → show AlertCircle |
| BR-009 | Tất cả số tiền (`balance_due`, `total_amount`) phải lưu dạng DECIMAL(15,2) để đảm bảo độ chính xác tiền tệ (không floating-point). API response dùng Decimal type (không float). | Sai số làm tròn → ghi chép tài chính không chính xác | SQL CAST + Pydantic Decimal |

---

## 8. Xử lý lỗi

### 8.1 Các mã lỗi phổ biến

| Mã HTTP | Mã lỗi | Tình huống xảy ra | Thông báo trả về |
|---------|--------|-------------------|-----------------|
| 400 | INVALID_REQUEST | Tham số `as_of` định dạng sai (ví dụ: `31-05-2026` thay vì `2026-05-31`) hoặc `doctor_id` không phải UUID hợp lệ | "Invalid date format. Expected YYYY-MM-DD, got: ..." |
| 401 | UNAUTHORIZED | Token JWT không hợp lệ, hết hạn, hoặc thiếu | "Authentication required. Invalid or expired token." |
| 403 | FORBIDDEN | User có token hợp lệ nhưng thiếu permission cần thiết (`report.financial` cho AR aging, `report.view` cho doctor-weekly) | "User does not have permission: report.financial" |
| 404 | NOT_FOUND | Doctor ID không tồn tại trong hệ thống (khi filter doctor-weekly) | "Doctor not found" |
| 500 | INTERNAL_ERROR | Database connection fail, query timeout, hoặc lỗi trong xử lý (ví dụ: exception khi giải mã `full_name`) | "Error computing report. Please try again later." |

### 8.2 Định dạng phản hồi lỗi

**Format JSON:**

```json
{
  "code": "INVALID_REQUEST",
  "message": "Invalid date format. Expected YYYY-MM-DD, got: 31-05-2026"
}
```

**Format CSV Export Error (trả về JSON thay vì CSV):**

```json
{
  "code": "FORBIDDEN",
  "message": "User does not have permission: report.financial"
}
```

---

## 9. Ghi chú khi kiểm thử

### 9.1 Điểm quan trọng cần nắm

- **MOCK_DATA gỡ bỏ hoàn toàn:** Các trang `ARAgingReportPage` và `DoctorDashboardPage` không còn MOCK_DATA const. Khi API fail → hiển thị error state (AlertCircle + Retry button), KHÔNG hiển thị dữ liệu bịa.
- **Patient `full_name` giải mã qua ORM:** SQL aggregate chỉ lấy được `patient_code` (plaintext). Để lấy `full_name`, phải ORM load Patient objects → EncryptedString TypeDecorator tự động giải mã trong context của clinic_id hiện tại.
- **RLS Context:** Database RLS policy + explicit WHERE `clinic_id = :clinic_id` (belt-and-suspenders). Kiểm thử cần phải verify cross-clinic data KHÔNG bị leak.
- **Tuổi hoá đơn tính từ `issued_at` không phải `created_at`:** Hãy chắc chắn các hoá đơn test có `issued_at` được đặt đúng.
- **Doctor-weekly status:** Chỉ `COMPLETED` + `AWAITING_PAYMENT`. Không tính `CANCELLED` hay `PENDING`.

### 9.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| AR aging — empty data | Clinic không có hoá đơn unpaid/partial | `grand_total: 0, patients: []` |
| AR aging — bucket 0-30 | Hoá đơn issued_at = hôm nay | Xuất hiện trong `bucket_0_30` |
| AR aging — bucket >90 | Hoá đơn issued_at > 90 ngày trước | Xuất hiện trong `bucket_over_90` |
| AR aging — partial payment | Hoá đơn status='partially_paid', balance_due=500k | AR aging hiển thị balance_due=500k (không phải total_amount) |
| AR aging — permission denied | User không có permission `report.financial` | 403 FORBIDDEN |
| AR aging — export CSV | As-of=2026-05-31 | File CSV được download, tên: `ar-aging-2026-05-31.csv` |
| CSV formula injection | Patient code = `=IMPORTXML(...)` | CSV cell chứa `'=IMPORTXML(...)` (có dấu ngoặc đơn ở đầu) |
| Doctor-weekly — empty | Tuần không có lượt khám | Tất cả 7 hàng count=0 |
| Doctor-weekly — specific doctor | doctor_id=<uuid>, có 3 lượt khám thứ 2 | rows[0].count=3, day_label="T2" |
| Doctor-weekly — ISO week boundary | ref_date = 2026-05-29 (thứ 4) | week_start=2026-05-25 (T2), week_end=2026-05-31 (CN) |

### 9.3 Hạn chế hiện tại

- **Không hỗ trợ phân trang (pagination):** Nếu một phòng khám có >1000 hoá đơn unpaid, response sẽ chứa tất cả (có thể chậm). Future task có thể thêm `limit` / `offset`.
- **CSV export phía client:** Nếu BE `/export` endpoint fail, FE có fallback là tự render CSV từ dữ liệu JSON (không phải ideal cho large dataset).
- **Doctor-weekly chỉ trả per-doctor hoặc all:** Không support nhóm bác sĩ (department-level aggregation) — future task.

### 9.4 Hướng phát triển

- **Thêm drill-down:** AR aging → click vào patient → xem chi tiết hoá đơn từng cái
- **Alert / Threshold:** Cảnh báo nếu công nợ >90 ngày vượt ngưỡng
- **TASK-056:** Phân tích xu hướng dài hạn, so sánh tháng trước
- **Tích hợp SMS/Email:** Thông báo tự động cho bệnh nhân công nợ

---

## Kết luận

TASK-066 cung cấp giải pháp hoàn chỉnh cho báo cáo Công nợ Phải Thu:
- **3 endpoint REST** để lấy dữ liệu và xuất báo cáo
- **Gỡ bỏ hoàn toàn dữ liệu mock** từ frontend
- **Bảo vệ bảo mật:** RLS, permission gating, formula injection guard
- **Hỗ trợ chart tuần** cho DoctorDashboard

Các yêu cầu acceptance đã hoàn tất:
- ✅ GET /reports/ar-aging trả real data từ DB
- ✅ ARAgingReportPage gỡ MOCK_DATA; error state hiển thị rõ
- ✅ CSV export hoạt động
- ✅ DoctorDashboard weekly chart dùng real data
- ✅ Tất cả test pass (29 BE integration + 914 FE unit + 4 E2E)
