# Thiết Kế Chi Tiết Tính Năng: Super Admin Analytics — Thống kê phòng khám theo thời gian

**Dự án:** Clinic CMS
**Task:** TASK-071
**Phiên bản:** 1.0
**Ngày:** 2026-06-01
**Người thực hiện:** Documentation Agent
**Trạng thái:** Đã duyệt
**Tài liệu liên quan:** Test Report (test-to-documentation.md)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-06-01 | Phiên bản đầu tiên — hoàn thành implementation & testing |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Danh sách API](#3-danh-sách-api)
- [4. Danh sách chỉ số thống kê](#4-danh-sách-chỉ-số-thống-kê)
- [5. Chi tiết từng API](#5-chi-tiết-từng-api)
- [6. Cấu trúc cơ sở dữ liệu](#6-cấu-trúc-cơ-sở-dữ-liệu)
- [7. SQL tổng hợp và truy vấn dữ liệu](#7-sql-tổng-hợp-và-truy-vấn-dữ-liệu)
- [8. Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
- [9. Xử lý lỗi](#9-xử-lý-lỗi)
- [10. Ghi chú và lưu ý khi kiểm thử](#10-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Cung cấp bộ công cụ thống kê chi tiết cho Super Admin — xem chỉ số hoạt động (**lượt khám, doanh thu, bệnh nhân mới/tái khám**) của **từng phòng khám** hoặc **toàn hệ thống**, trong một khoảng thời gian tùy chọn (ngày/tuần/tháng/năm hoặc tùy ý). Giúp Super Admin theo dõi hiệu suất hoạt động của các phòng khám, phát hiện các phòng khám có hiệu suất cao/thấp, và đưa ra quyết định kinh doanh dựa trên dữ liệu.

### 1.2 Phạm vi

**Bao gồm:**
- Trang `/superadmin/analytics` với filter bar, stats cards, line chart, và bảng so sánh phòng khám
- 3 API endpoint mới cho thống kê (overview, timeseries, clinics comparison)
- Sidebar link "Thống kê" trong section Super Admin
- Quyền kiểm soát: chỉ Super Admin (`is_superuser=true`) mới truy cập được
- 7 chỉ số chính: lượt khám, doanh thu, doanh thu TB/lượt, bệnh nhân mới, bệnh nhân tái khám, và các chỉ số trung bình theo ngày/tuần/tháng

**Không bao gồm:**
- Tính năng export CSV (ngoài scope hiện tại)
- Dữ liệu các phòng khám đã xóa
- Thống kê dưới mức phòng khám (ví dụ: per-service, per-doctor)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Super Admin (End User)** | Người dùng với quyền `is_superuser=true`, truy cập `/superadmin/analytics` để xem báo cáo thống kê |
| **Clinic Admin** | Không thể truy cập tính năng này; nếu cố gắng navigate sẽ bị redirect về `/dashboard` |
| **Backend Service** | Cung cấp 3 API endpoints với dữ liệu cross-tenant (bypass RLS) |
| **Frontend App** | Hiển thị UI, gọi API, render charts & tables |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
[Super Admin User]
        │
        │ 1. Chọn filters (clinic + date range + granularity)
        ▼
[FE: SuperAdminAnalyticsPage]
        │
        │ 2. Gọi 3 API song song
        ├─► GET /api/v1/superadmin/analytics/overview
        ├─► GET /api/v1/superadmin/analytics/timeseries
        └─► GET /api/v1/superadmin/analytics/clinics
        │
        ▼
[Backend: analytics.py — Cross-tenant service]
        │
        │ 3. Query visit + invoice + patient tables
        │    (với RLS bypass qua GUC app.is_superuser)
        │
        ▼
[Database: PostgreSQL]
        │ Trả về aggregated metrics
        ▼
[FE: Render results]
        │
        ├─► Stats cards (7 chỉ số)
        ├─► Line chart (lượt khám / doanh thu over time)
        └─► Clinic comparison table (sortable)
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Super Admin chọn filter | User chọn clinic (all hoặc từng clinic), preset thời gian (Hôm nay / 7d / 30d / Tháng này / Năm này) hoặc custom range (date_from → date_to), và granularity (ngày/tuần/tháng/năm) |
| 2 | FE validate & gọi API | FE kiểm tra date_from ≤ date_to và range ≤ 365 ngày; nếu ok thì gọi 3 API song song với parameters |
| 3 | BE kiểm tra xác thực | BE kiểm tra token — nếu không hợp lệ hoặc user không phải superuser, trả về 403 Forbidden |
| 4 | BE query dữ liệu | BE thực thi 3 truy vấn SQL (overview, timeseries, clinics) trên `visit`, `invoice`, `patient` tables với RLS bypass; kết quả bao gồm cả dữ liệu từ nhiều clinics (cross-tenant) |
| 5 | BE trả kết quả | API trả về JSON chứa các chỉ số aggregated |
| 6 | FE render UI | FE render stats cards, line chart, clinic comparison table từ dữ liệu nhận được |
| 7 | User xem & phân tích | Super Admin có thể toggle metrics, sort bảng, filter theo clinic, thay đổi date range một cách real-time |

---

## 3. Danh sách API

Tất cả API đều yêu cầu xác thực qua header:
```
Authorization: Bearer {token}
```

**Đường dẫn gốc (Base Path):** `/api/v1/superadmin/analytics`

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt |
|-----|------------|-----------|--------------|
| 1 | GET | `/api/v1/superadmin/analytics/overview` | Lấy tổng hợp chỉ số: lượt khám, doanh thu, trung bình, bệnh nhân mới/tái khám |
| 2 | GET | `/api/v1/superadmin/analytics/timeseries` | Lấy chuỗi thời gian cho metric cụ thể (lượt khám / doanh thu / bệnh nhân mới) để vẽ chart |
| 3 | GET | `/api/v1/superadmin/analytics/clinics` | Lấy bảng so sánh per-clinic với các chỉ số trung bình |

---

## 4. Danh sách chỉ số thống kê

| Chỉ số | Mô tả | Đơn vị | Ghi chú |
|--------|-------|--------|---------|
| `visits` | Số lượt khám | Lượt | Status = COMPLETED trong khoảng thời gian filter |
| `revenue` | Tổng doanh thu | VND | Sum(invoice.grand_total) với status = paid |
| `avg_revenue_per_visit` | Doanh thu TB trên 1 lượt khám | VND | = revenue / visits (làm tròn 2 chữ số) |
| `new_patients` | Bệnh nhân mới | Bệnh nhân | Patient được tạo trong khoảng filter |
| `returning_patients` | Bệnh nhân tái khám | Bệnh nhân | Patient tạo TRƯỚC range nhưng visit trong range |
| `avg_daily_visits` | TB lượt khám/ngày | Lượt | = visits / (số ngày trong range) |
| `avg_weekly_visits` | TB lượt khám/tuần | Lượt | = visits / (số tuần trong range) |
| `avg_monthly_revenue` | TB doanh thu/tháng | VND | = revenue / (số tháng trong range) |

---

## 5. Chi tiết từng API

### 5.1 GET /api/v1/superadmin/analytics/overview

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `GET /api/v1/superadmin/analytics/overview` |
| **Mô tả** | Trả về tổng hợp chỉ số (visits, revenue, avg_revenue_per_visit, new_patients, returning_patients) trong khoảng thời gian đã chọn, có thể lọc theo clinic cụ thể hoặc tất cả clinics |
| **Xác thực** | Bắt buộc; chỉ superuser mới được phép |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `date_from` | Date (yyyy-MM-dd) | Có | Ngày bắt đầu khoảng thời gian (inclusive) | — |
| `date_to` | Date (yyyy-MM-dd) | Có | Ngày kết thúc khoảng thời gian (inclusive) | — |
| `clinic_id` | UUID | Không | ID của phòng khám cụ thể; nếu không truyền → lấy tất cả clinics | null (all clinics) |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu từ FE; kiểm tra token xác thực |
| 2 | Kiểm tra user là superuser → trả 403 nếu không |
| 3 | Kiểm tra date_from ≤ date_to → trả 422 nếu không |
| 4 | Kiểm tra (date_to - date_from).days ≤ 365 → trả 422 nếu vượt |
| 5 | Thực thi 4 subquery SQL (visits, revenue, new_patients, returning_patients) với RLS bypass |
| 6 | Tính avg_revenue_per_visit = revenue / visits (làm tròn 2 chữ số) |
| 7 | Trả JSON chứa 5 chỉ số |

**Truy vấn dữ liệu:**

```sql
SELECT
  -- Lượt khám hoàn thành trong range
  (
    SELECT COUNT(*)
    FROM visit v
    JOIN clinic c ON c.id = v.clinic_id
    WHERE v.status = 'COMPLETED'
      AND v.completed_at::date BETWEEN :date_from AND :date_to
      AND c.code <> 'SYSTEM'
      AND c.is_deleted IS FALSE
      [AND v.clinic_id = :clinic_id]
  ) AS visits,

  -- Doanh thu từ hóa đơn paid (dùng invoice.updated_at làm paid date proxy)
  (
    SELECT COALESCE(SUM(i.grand_total), 0)
    FROM invoice i
    JOIN clinic c ON c.id = i.clinic_id
    WHERE i.status = 'paid'
      AND i.updated_at::date BETWEEN :date_from AND :date_to
      AND c.code <> 'SYSTEM'
      AND c.is_deleted IS FALSE
      [AND i.clinic_id = :clinic_id]
  ) AS revenue,

  -- Bệnh nhân mới (created trong range)
  (
    SELECT COUNT(*)
    FROM patient p
    JOIN clinic c ON c.id = p.clinic_id
    WHERE p.is_deleted IS FALSE
      AND p.created_at::date BETWEEN :date_from AND :date_to
      AND c.code <> 'SYSTEM'
      AND c.is_deleted IS FALSE
      [AND p.clinic_id = :clinic_id]
  ) AS new_patients,

  -- Bệnh nhân tái khám (visit trong range nhưng created TRƯỚC range)
  (
    SELECT COUNT(DISTINCT v.patient_id)
    FROM visit v
    JOIN clinic c ON c.id = v.clinic_id
    JOIN patient p ON p.id = v.patient_id
    WHERE v.status = 'COMPLETED'
      AND v.completed_at::date BETWEEN :date_from AND :date_to
      AND c.code <> 'SYSTEM'
      AND c.is_deleted IS FALSE
      AND p.created_at::date < :date_from
      [AND v.clinic_id = :clinic_id]
  ) AS returning_patients
```

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "data": {
    "visits": 250,
    "revenue": 25000000,
    "avg_revenue_per_visit": 100000.0,
    "new_patients": 45,
    "returning_patients": 205
  }
}
```

**Mô tả các trường kết quả:**

| Trường | Kiểu | Mô tả ý nghĩa nghiệp vụ |
|--------|------|------------------------|
| `visits` | Số nguyên | Tổng số lượt khám hoàn thành trong khoảng thời gian |
| `revenue` | Số thực | Tổng doanh thu từ các hóa đơn có status = paid, được cập nhật trong khoảng thời gian |
| `avg_revenue_per_visit` | Số thực | Doanh thu trung bình trên mỗi lượt khám (làm tròn 2 chữ số) — giúp đánh giá hiệu quả kinh tế |
| `new_patients` | Số nguyên | Số bệnh nhân mới lần đầu đến khám trong khoảng thời gian |
| `returning_patients` | Số nguyên | Số bệnh nhân tái khám (đã đến khám trước khoảng thời gian) trong khoảng thời gian |

---

### 5.2 GET /api/v1/superadmin/analytics/timeseries

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `GET /api/v1/superadmin/analytics/timeseries` |
| **Mô tả** | Trả về chuỗi thời gian cho một metric cụ thể (lượt khám / doanh thu / bệnh nhân mới) theo granularity đã chọn (ngày/tuần/tháng/năm); dùng để vẽ line chart |
| **Xác thực** | Bắt buộc; chỉ superuser mới được phép |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `metric` | String | Có | Chỉ số cần lấy: `visits` (lượt khám), `revenue` (doanh thu), `new_patients` (bệnh nhân mới) | — |
| `granularity` | String | Có | Độ hạt: `day` (ngày), `week` (tuần), `month` (tháng), `year` (năm) | — |
| `date_from` | Date (yyyy-MM-dd) | Có | Ngày bắt đầu (inclusive) | — |
| `date_to` | Date (yyyy-MM-dd) | Có | Ngày kết thúc (inclusive) | — |
| `clinic_id` | UUID | Không | Lọc theo clinic cụ thể; nếu không → tất cả clinics | null (all clinics) |

**Giá trị hợp lệ của `metric`:**

| Giá trị | Ý nghĩa |
|---------|---------|
| `visits` | Tổng số lượt khám hoàn thành trong mỗi period |
| `revenue` | Tổng doanh thu từ hóa đơn paid trong mỗi period |
| `new_patients` | Số bệnh nhân mới được tạo trong mỗi period |

**Giá trị hợp lệ của `granularity`:**

| Giá trị | Ý nghĩa |
|---------|---------|
| `day` | GROUP BY ngày (DATE) |
| `week` | GROUP BY tuần (DATE_TRUNC('week', ...)) |
| `month` | GROUP BY tháng (DATE_TRUNC('month', ...)) |
| `year` | GROUP BY năm (DATE_TRUNC('year', ...)) |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu, kiểm tra token xác thực |
| 2 | Kiểm tra user là superuser → 403 nếu không |
| 3 | Kiểm tra date_from ≤ date_to, range ≤ 365 ngày → 422 nếu vi phạm |
| 4 | Validate metric & granularity; nếu không hợp lệ → dùng giá trị mặc định (metric=visits, granularity=day) |
| 5 | Thực thi truy vấn SQL phù hợp với metric + granularity |
| 6 | Trả array của {period, value} objects, sắp xếp theo period tăng dần |

**Truy vấn dữ liệu (ví dụ metric=visits, granularity=week):**

```sql
SELECT
  DATE_TRUNC('week', v.completed_at) AS period,
  COUNT(*) AS value
FROM visit v
JOIN clinic c ON c.id = v.clinic_id
WHERE v.status = 'COMPLETED'
  AND v.completed_at::date BETWEEN :date_from AND :date_to
  AND c.code <> 'SYSTEM'
  AND c.is_deleted IS FALSE
  [AND v.clinic_id = :clinic_id]
GROUP BY 1
ORDER BY 1
```

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "data": [
    { "period": "2026-05-01", "value": 100 },
    { "period": "2026-05-02", "value": 150 },
    { "period": "2026-05-03", "value": 120 },
    { "period": "2026-05-04", "value": 180 }
  ]
}
```

**Mô tả các trường kết quả:**

| Trường | Kiểu | Mô tả ý nghĩa nghiệp vụ |
|--------|------|------------------------|
| `period` | Chuỗi (ISO 8601) | Khoảng thời gian (ngày / tuần / tháng / năm) phục vụ cho việc render trục X của chart |
| `value` | Số thực | Giá trị của metric (lượt khám / doanh thu / bệnh nhân mới) trong period đó |

---

### 5.3 GET /api/v1/superadmin/analytics/clinics

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `GET /api/v1/superadmin/analytics/clinics` |
| **Mô tả** | Trả về bảng so sánh per-clinic với các chỉ số aggregated (visits, revenue, avg_daily_visits, avg_weekly_visits, avg_monthly_revenue); kết quả được sort và limit |
| **Xác thực** | Bắt buộc; chỉ superuser mới được phép |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `date_from` | Date (yyyy-MM-dd) | Có | Ngày bắt đầu (inclusive) | — |
| `date_to` | Date (yyyy-MM-dd) | Có | Ngày kết thúc (inclusive) | — |
| `sort_by` | String | Không | Sắp xếp theo: `visits` hoặc `revenue` | `revenue` (doanh thu) |
| `limit` | Số nguyên | Không | Giới hạn số clinics trả về (1–200) | 20 |

**Giá trị hợp lệ của `sort_by`:**

| Giá trị | Ý nghĩa |
|---------|---------|
| `revenue` | Sắp xếp giảm dần theo doanh thu |
| `visits` | Sắp xếp giảm dần theo lượt khám |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu, kiểm tra token xác thực |
| 2 | Kiểm tra user là superuser → 403 nếu không |
| 3 | Kiểm tra date_from ≤ date_to, range ≤ 365 ngày → 422 nếu vi phạm |
| 4 | Validate limit: phải ≥1 và ≤200; nếu không → dùng 20 |
| 5 | Tính số ngày/tuần/tháng trong range (dùng cho công thức tính avg_*) |
| 6 | Thực thi CTE query để join visit_stats + revenue_stats + clinic info |
| 7 | Tính toán avg_daily_visits, avg_weekly_visits, avg_monthly_revenue |
| 8 | Trả sorted & limited results |

**Truy vấn dữ liệu:**

```sql
WITH visit_stats AS (
  SELECT v.clinic_id, COUNT(*) AS visits, COUNT(DISTINCT v.patient_id) AS unique_patients
  FROM visit v
  JOIN clinic c ON c.id = v.clinic_id
  WHERE v.status = 'COMPLETED'
    AND v.completed_at::date BETWEEN :date_from AND :date_to
    AND c.code <> 'SYSTEM'
    AND c.is_deleted IS FALSE
  GROUP BY v.clinic_id
),
revenue_stats AS (
  SELECT i.clinic_id, COALESCE(SUM(i.grand_total), 0) AS revenue
  FROM invoice i
  JOIN clinic c ON c.id = i.clinic_id
  WHERE i.status = 'paid'
    AND i.updated_at::date BETWEEN :date_from AND :date_to
    AND c.code <> 'SYSTEM'
    AND c.is_deleted IS FALSE
  GROUP BY i.clinic_id
)
SELECT
  c.id AS clinic_id,
  c.name AS clinic_name,
  COALESCE(vs.visits, 0) AS visits,
  COALESCE(rs.revenue, 0) AS revenue
FROM clinic c
LEFT JOIN visit_stats vs ON vs.clinic_id = c.id
LEFT JOIN revenue_stats rs ON rs.clinic_id = c.id
WHERE c.is_deleted IS FALSE AND c.code <> 'SYSTEM'
ORDER BY
  CASE WHEN :sort_by = 'revenue' THEN COALESCE(rs.revenue, 0) END DESC NULLS LAST,
  CASE WHEN :sort_by = 'visits' THEN COALESCE(vs.visits, 0) END DESC NULLS LAST
LIMIT :limit
```

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "data": [
    {
      "clinic_id": "550e8400-e29b-41d4-a716-446655440000",
      "clinic_name": "Phòng khám Trung tâm",
      "visits": 500,
      "revenue": 50000000,
      "avg_daily_visits": 16.67,
      "avg_weekly_visits": 100.0,
      "avg_monthly_revenue": 5000000.0
    },
    {
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "clinic_name": "Phòng khám Tây Hà Nội",
      "visits": 350,
      "revenue": 35000000,
      "avg_daily_visits": 11.67,
      "avg_weekly_visits": 70.0,
      "avg_monthly_revenue": 3500000.0
    }
  ]
}
```

**Mô tả các trường kết quả:**

| Trường | Kiểu | Mô tả ý nghĩa nghiệp vụ |
|--------|------|------------------------|
| `clinic_id` | UUID (chuỗi) | ID duy nhất của phòng khám |
| `clinic_name` | Chuỗi | Tên phòng khám |
| `visits` | Số nguyên | Tổng lượt khám hoàn thành trong khoảng thời gian |
| `revenue` | Số thực | Tổng doanh thu từ hóa đơn paid trong khoảng thời gian |
| `avg_daily_visits` | Số thực | Trung bình lượt khám/ngày = visits / (số ngày trong range) |
| `avg_weekly_visits` | Số thực | Trung bình lượt khám/tuần = visits / (số tuần trong range) |
| `avg_monthly_revenue` | Số thực | Trung bình doanh thu/tháng = revenue / (số tháng trong range) |

---

## 6. Cấu trúc cơ sở dữ liệu

### 6.1 Tổng quan các bảng

| Bảng | Mục đích |
|------|---------|
| `visit` | Lưu thông tin lượt khám; có status (COMPLETED, PENDING, CANCELLED), completed_at (timestamp), clinic_id, patient_id |
| `invoice` | Lưu thông tin hóa đơn; có status (draft, pending, paid, refunded), grand_total (tiền), updated_at (timestamp), clinic_id |
| `patient` | Lưu thông tin bệnh nhân; có created_at (timestamp tạo bệnh nhân), clinic_id, is_deleted flag |
| `clinic` | Lưu thông tin phòng khám; có code (SYSTEM cho hệ thống), name, is_deleted flag |

### 6.2 Chi tiết các trường cần thiết

#### Bảng: `visit`

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Tham chiếu đến clinic — dùng để filter per-clinic |
| `patient_id` | UUID | Có | Tham chiếu đến patient — dùng để đếm bệnh nhân tái khám |
| `status` | ENUM | Có | Trạng thái: COMPLETED, PENDING, CANCELLED — chỉ lấy COMPLETED |
| `completed_at` | TIMESTAMPTZ | Không | Thời điểm hoàn thành khám; dùng làm cơ sở cho date range filter |
| `created_at` | TIMESTAMPTZ | Có | Thời điểm tạo bản ghi |

#### Bảng: `invoice`

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Tham chiếu đến clinic |
| `status` | ENUM | Có | Trạng thái: draft, pending, paid, refunded — chỉ lấy paid |
| `grand_total` | NUMERIC(15,2) | Có | Tổng tiền (VND) — dùng để tính revenue |
| `updated_at` | TIMESTAMPTZ | Có | Thời điểm cập nhật (dùng làm proxy cho paid date) |

#### Bảng: `patient`

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Tham chiếu đến clinic |
| `created_at` | TIMESTAMPTZ | Có | Thời điểm tạo bệnh nhân — dùng để xác định bệnh nhân mới |
| `is_deleted` | BOOLEAN | Có | Flag xóa mềm; nếu TRUE → bỏ qua |

#### Bảng: `clinic`

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `code` | VARCHAR | Có | Code phòng khám; "SYSTEM" → bỏ qua trong thống kê |
| `name` | VARCHAR | Có | Tên phòng khám — hiển thị trong bảng clinics |
| `is_deleted` | BOOLEAN | Có | Flag xóa mềm; nếu TRUE → bỏ qua |

### 6.3 Index được sử dụng

Để tối ưu hiệu suất truy vấn, các index sau **nên tồn tại hoặc được tạo thêm**:

```sql
-- Tối ưu truy vấn visit theo completed_at range
CREATE INDEX idx_visit_completed_at_clinic ON visit(clinic_id, completed_at);

-- Tối ưu truy vấn invoice theo updated_at range
CREATE INDEX idx_invoice_updated_at_clinic ON invoice(clinic_id, updated_at);

-- Tối ưu truy vấn patient theo created_at
CREATE INDEX idx_patient_created_at_clinic ON patient(clinic_id, created_at);
```

---

## 7. SQL tổng hợp và truy vấn dữ liệu

### 7.1 SQL tổng hợp / ghi dữ liệu

**Ghi chú**: Tính năng analytics này **không lưu trữ dữ liệu aggregated vào database**. Tất cả dữ liệu được **tính toán real-time** từ các bảng nguồn (visit, invoice, patient) khi user gọi API. Do đó phần này không áp dụng.

---

### 7.2 SQL truy vấn báo cáo / lấy dữ liệu

#### Truy vấn 1: Overview — Tổng hợp chỉ số trong khoảng thời gian

**Mục đích**: Lấy 5 chỉ số aggregated (visits, revenue, avg_revenue_per_visit, new_patients, returning_patients) trong khoảng thời gian đã chọn.

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `date_from` | visit.completed_at, invoice.updated_at, patient.created_at | Ngày bắt đầu (inclusive) |
| `date_to` | visit.completed_at, invoice.updated_at, patient.created_at | Ngày kết thúc (inclusive) |
| `clinic_id` | visit.clinic_id, invoice.clinic_id, patient.clinic_id | Nếu null → lấy tất cả clinics |

```sql
SELECT
  -- Lượt khám hoàn thành
  (
    SELECT COUNT(*)
    FROM visit v
    JOIN clinic c ON c.id = v.clinic_id
    WHERE v.status = 'COMPLETED'
      AND v.completed_at::date BETWEEN :date_from AND :date_to
      AND c.code <> 'SYSTEM'
      AND c.is_deleted IS FALSE
      AND (:clinic_id IS NULL OR v.clinic_id = :clinic_id)
  ) AS visits,

  -- Doanh thu từ hóa đơn paid
  (
    SELECT COALESCE(SUM(i.grand_total), 0)
    FROM invoice i
    JOIN clinic c ON c.id = i.clinic_id
    WHERE i.status = 'paid'
      AND i.updated_at::date BETWEEN :date_from AND :date_to
      AND c.code <> 'SYSTEM'
      AND c.is_deleted IS FALSE
      AND (:clinic_id IS NULL OR i.clinic_id = :clinic_id)
  ) AS revenue,

  -- Bệnh nhân mới
  (
    SELECT COUNT(*)
    FROM patient p
    JOIN clinic c ON c.id = p.clinic_id
    WHERE p.is_deleted IS FALSE
      AND p.created_at::date BETWEEN :date_from AND :date_to
      AND c.code <> 'SYSTEM'
      AND c.is_deleted IS FALSE
      AND (:clinic_id IS NULL OR p.clinic_id = :clinic_id)
  ) AS new_patients,

  -- Bệnh nhân tái khám
  (
    SELECT COUNT(DISTINCT v.patient_id)
    FROM visit v
    JOIN clinic c ON c.id = v.clinic_id
    JOIN patient p ON p.id = v.patient_id
    WHERE v.status = 'COMPLETED'
      AND v.completed_at::date BETWEEN :date_from AND :date_to
      AND c.code <> 'SYSTEM'
      AND c.is_deleted IS FALSE
      AND p.created_at::date < :date_from
      AND (:clinic_id IS NULL OR v.clinic_id = :clinic_id)
  ) AS returning_patients
```

**Giải thích:**
- Sử dụng 4 subquery độc lập để đếm visits, revenue, new_patients, returning_patients
- Mỗi subquery có JOIN với clinic table để filter SYSTEM clinic và deleted clinics
- Điều kiện clinic_id dùng `(:clinic_id IS NULL OR ...)` để hỗ trợ cả 2 trường hợp: lấy tất cả hoặc lọc 1 clinic

---

#### Truy vấn 2: Timeseries — Chuỗi thời gian (ví dụ: visits theo tuần)

**Mục đích**: Lấy chuỗi thời gian cho metric visits, granularity week.

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `date_from`, `date_to` | visit.completed_at | Date range |
| `granularity` | DATE_TRUNC(...) | week → DATE_TRUNC('week', v.completed_at) |
| `clinic_id` | visit.clinic_id | Nếu null → all clinics |

```sql
-- Metric: visits, Granularity: week
SELECT
  DATE_TRUNC('week', v.completed_at)::date AS period,
  COUNT(*) AS value
FROM visit v
JOIN clinic c ON c.id = v.clinic_id
WHERE v.status = 'COMPLETED'
  AND v.completed_at::date BETWEEN :date_from AND :date_to
  AND c.code <> 'SYSTEM'
  AND c.is_deleted IS FALSE
  AND (:clinic_id IS NULL OR v.clinic_id = :clinic_id)
GROUP BY 1
ORDER BY 1 ASC
```

**Biến thể cho các granularities:**

- `day` → `DATE(v.completed_at)` hoặc `DATE_TRUNC('day', v.completed_at)`
- `month` → `DATE_TRUNC('month', v.completed_at)`
- `year` → `DATE_TRUNC('year', v.completed_at)`

**Biến thể cho các metrics:**

- `revenue` → SUM(i.grand_total) FROM invoice, filter by i.status = 'paid', i.updated_at
- `new_patients` → COUNT(*) FROM patient, filter by p.created_at, p.is_deleted = FALSE

---

#### Truy vấn 3: Per-clinic Comparison — Bảng so sánh phòng khám

**Mục đích**: Lấy bảng so sánh per-clinic với visits, revenue, và các chỉ số trung bình.

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `date_from`, `date_to` | visit.completed_at, invoice.updated_at | Date range |
| `sort_by` | CASE WHEN ... THEN revenue/visits END DESC | revenue hoặc visits |
| `limit` | LIMIT | Max 200 |

```sql
WITH visit_stats AS (
  SELECT v.clinic_id,
         COUNT(*) AS visits,
         COUNT(DISTINCT v.patient_id) AS unique_patients
  FROM visit v
  JOIN clinic c ON c.id = v.clinic_id
  WHERE v.status = 'COMPLETED'
    AND v.completed_at::date BETWEEN :date_from AND :date_to
    AND c.code <> 'SYSTEM'
    AND c.is_deleted IS FALSE
  GROUP BY v.clinic_id
),
revenue_stats AS (
  SELECT i.clinic_id,
         COALESCE(SUM(i.grand_total), 0) AS revenue
  FROM invoice i
  JOIN clinic c ON c.id = i.clinic_id
  WHERE i.status = 'paid'
    AND i.updated_at::date BETWEEN :date_from AND :date_to
    AND c.code <> 'SYSTEM'
    AND c.is_deleted IS FALSE
  GROUP BY i.clinic_id
)
SELECT c.id AS clinic_id,
       c.name AS clinic_name,
       COALESCE(vs.visits, 0) AS visits,
       COALESCE(rs.revenue, 0) AS revenue
FROM clinic c
LEFT JOIN visit_stats vs ON vs.clinic_id = c.id
LEFT JOIN revenue_stats rs ON rs.clinic_id = c.id
WHERE c.is_deleted IS FALSE AND c.code <> 'SYSTEM'
ORDER BY
  CASE WHEN :sort_by = 'revenue' THEN COALESCE(rs.revenue, 0) END DESC NULLS LAST,
  CASE WHEN :sort_by = 'visits' THEN COALESCE(vs.visits, 0) END DESC NULLS LAST
LIMIT :limit
```

**Giải thích:**
- Sử dụng CTE (visit_stats, revenue_stats) để tính toán visits và revenue per-clinic
- Sau đó LEFT JOIN với clinic table để lấy danh sách tất cả clinics (kể cả những clinic không có visits/revenue trong period)
- ORDER BY CASE để thực hiện dynamic sorting dựa trên :sort_by parameter

---

### 7.3 Logic tính toán tham số truy vấn

#### Logic A: Tính khoảng ngày từ quick filter presets

| Preset | Công thức | Ví dụ (hôm nay = 2026-05-31) |
|--------|-----------|------|
| `today` | date_from = today(), date_to = today() | 2026-05-31 → 2026-05-31 |
| `7d` | date_from = today() - 6 days, date_to = today() | 2026-05-25 → 2026-05-31 |
| `30d` | date_from = today() - 29 days, date_to = today() | 2026-05-02 → 2026-05-31 |
| `this_month` | date_from = first day of current month, date_to = today() | 2026-05-01 → 2026-05-31 |
| `this_year` | date_from = 2026-01-01, date_to = today() | 2026-01-01 → 2026-05-31 |

#### Logic B: Tính số ngày/tuần/tháng trong range (dùng cho avg_*)

```
days_in_range = (date_to - date_from).days + 1          // ≥ 1
weeks_in_range = days_in_range / 7.0                    // ≥ 1
months_in_range = days_in_range / 30.44                 // ≥ 1

avg_daily_visits = visits / days_in_range
avg_weekly_visits = visits / weeks_in_range
avg_monthly_revenue = revenue / months_in_range
```

#### Logic C: Xác định granularity từ date range (optional, cho FE suggest)

| Date range | Suggested granularity |
|------------|----------------------|
| ≤ 7 ngày | day |
| 8–30 ngày | week |
| 31–90 ngày | week hoặc month |
| 91–365 ngày | month |
| 365+ ngày | year (nhưng bị reject ở validation) |

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-001 | Chỉ Super Admin (`is_superuser = true`) mới được phép truy cập API `/api/v1/superadmin/analytics/*` | Trả 403 Forbidden |
| BR-002 | `date_from` phải ≤ `date_to` | Trả 422 Unprocessable Entity với message: "date_from must be ≤ date_to" |
| BR-003 | Khoảng thời gian `(date_to - date_from).days` không được vượt quá 365 ngày | Trả 422 Unprocessable Entity với message: "Date range cannot exceed 365 days" |
| BR-004 | Tham số `limit` trong `/clinics` endpoint phải nằm trong khoảng 1–200 | Nếu < 1 hoặc > 200, normalize: < 1 → 1; > 200 → 200 |
| BR-005 | Doanh thu (`revenue`) được tính từ `SUM(invoice.grand_total)` của các hóa đơn có `status = 'paid'`, với thời gian tính dựa trên `invoice.updated_at` | Revenue có thể misbucket nếu hóa đơn bị refund sau khoảng thời gian filter — xem ghi chú về limitation |
| BR-006 | Lượt khám (`visits`) được đếm từ số `visit` records có `status = 'COMPLETED'` trong khoảng `visit.completed_at` | Chỉ tính COMPLETED visits; PENDING, CANCELLED bị loại |
| BR-007 | Bệnh nhân mới được xác định là patient có `created_at` nằm trong khoảng filter | Sử dụng patient.created_at làm proxy cho first visit (không có cột first_visit_at) |
| BR-008 | Bệnh nhân tái khám được xác định là patient có `created_at` TRƯỚC khoảng filter nhưng có visit TRONG khoảng filter | Dùng để phân biệt khách hàng mới vs. khách hàng cũ |
| BR-009 | Dữ liệu cross-tenant được phép; bypass RLS qua GUC `app.is_superuser` đã set bởi TenancyMiddleware | Super Admin có thể xem dữ liệu của tất cả clinics |
| BR-010 | Clinic với `code = 'SYSTEM'` được loại ra khỏi tất cả thống kê (là clinic hệ thống, không phải clinic thực) | Filter WHERE `clinic.code <> 'SYSTEM'` |
| BR-011 | Clinic bị đánh dấu deleted (`is_deleted = true`) được loại ra khỏi thống kê | Filter WHERE `clinic.is_deleted IS FALSE` |
| BR-012 | Patient bị đánh dấu deleted (`is_deleted = true`) không được tính vào bệnh nhân mới | Filter WHERE `patient.is_deleted IS FALSE` |

---

## 9. Xử lý lỗi

### 9.1 Các mã lỗi phổ biến

| Mã HTTP | Mã lỗi nội bộ | Tình huống xảy ra | Thông báo trả về |
|---------|--------|-------------------|-----------------|
| 200 | — | Yêu cầu thành công | `{ "data": {...} }` |
| 400 | INVALID_REQUEST | Tham số không hợp lệ (ví dụ: granularity không phải day/week/month/year, metric không phải visits/revenue/new_patients) | "Invalid parameter: {param_name}. Accepted values: [...]" |
| 401 | UNAUTHORIZED | Token không được cung cấp hoặc không hợp lệ | "Unauthorized: Invalid or missing token" |
| 403 | FORBIDDEN | User không phải superuser (`is_superuser = false`) | "Forbidden: Only superusers can access this endpoint" |
| 422 | VALIDATION_ERROR | Date validation fail (date_from > date_to hoặc range > 365 days); limit out of range | "Invalid date range: {chi tiết lỗi}." hoặc "Limit must be between 1 and 200" |
| 500 | INTERNAL_ERROR | Lỗi database, timeout, v.v. | "Internal server error. Please try again later." |

### 9.2 Định dạng phản hồi lỗi

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Invalid date range: date_from (2026-06-01) must be <= date_to (2026-05-31)",
  "details": null
}
```

---

## 10. Ghi chú và lưu ý khi kiểm thử

### 10.1 Điểm quan trọng cần nắm

- **Revenue proxy**: Doanh thu sử dụng `invoice.updated_at` làm proxy cho ngày thanh toán (paid date). Nếu hóa đơn được tạo trong khoảng nhưng thanh toán sau khoảng, nó sẽ bị bỏ qua. Ngược lại, nếu thanh toán được cập nhật trong khoảng, nó được tính cả khi hóa đơn tạo trước khoảng.

- **New patients**: Bệnh nhân mới được xác định dựa trên `patient.created_at`. Không có cột `first_visit_at` riêng biệt, nên ta dùng ngày tạo patient làm proxy.

- **Returning patients**: Tính từ distinct patient_ids có visit trong range nhưng created_at < date_from. Điều này có thể bao gồm cả những patient không có visit trong range trước đó.

- **Cross-tenant visibility**: Super Admin thấy dữ liệu từ tất cả clinics nhờ bypass RLS. Một số clinic có thể hiển thị tên "Other Clinic" nếu tên không khả dụng trong cross-tenant context.

- **Index optimization**: Truy vấn có thể chậm nếu thiếu index trên `visit.completed_at`, `invoice.updated_at`, `patient.created_at` — cần đảm bảo index tồn tại trên production.

### 10.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| Lấy dữ liệu hôm nay | date_from=2026-05-31, date_to=2026-05-31, clinic_id=null | Trả về các chỉ số của ngày 31/5, tất cả clinics |
| Lấy dữ liệu 30 ngày qua | date_from=2026-05-02, date_to=2026-05-31, granularity=week | Trả về ~4-5 datapoints (tuần), mỗi tuần có visits + revenue |
| Lọc 1 clinic cụ thể | date_from=2026-05-01, date_to=2026-05-31, clinic_id={uuid} | Chỉ hiện dữ liệu của clinic đó |
| Range vượt 365 ngày | date_from=2025-05-31, date_to=2026-05-31 | 422 Validation error: range > 365 days |
| date_from > date_to | date_from=2026-06-01, date_to=2026-05-31 | 422 Validation error: date_from > date_to |
| Non-superuser access | User với is_superuser=false gọi API | 403 Forbidden |
| Clinic không có dữ liệu | clinic_id tương ứng với clinic mới chưa có visits | Trả về 0 visits, 0 revenue, null averages |
| Table sort by visits | sort_by=visits, limit=20 | Bảng clinics sắp xếp giảm dần theo visits |

### 10.3 Hạn chế hiện tại

- **Revenue bucketing mismatch**: `invoice.updated_at` dùng làm proxy paid date; nếu hóa đơn được refund sau khoảng filter, nó vẫn được tính vào revenue của khoảng đó.

- **Date range limit 365 days**: Không thể xem dữ liệu trên 1 năm trong 1 lần query. Cần nhiều query hoặc yêu cầu hỗ trợ range dài hơn từ team BE.

- **Granularity cố định**: Mỗi lần gọi `/timeseries` phải chỉ định 1 granularity (day/week/month/year); không thể lấy dữ liệu multi-granularity trong 1 lần.

- **Clinic data incompleteness**: Một số clinic có thể hiển thị là "Other Clinic" hoặc có dữ liệu incomplete nếu RLS filter chặn quyền truy cập — nhưng điều này không xảy ra với superuser (RLS bypassed).

### 10.4 Hướng phát triển

- **Export CSV/Excel**: Thêm endpoint `/export` hoặc button "Download" trên UI để xuất báo cáo
- **Scheduled reports**: Gửi email báo cáo hàng tuần/tháng cho Super Admin
- **Advanced filtering**: Thêm filter theo service type, doctor, bác sĩ chuyên khoa, v.v.
- **Predictive analytics**: Dự đoán xu hướng visits/revenue dựa trên dữ liệu lịch sử

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Trưởng nhóm kỹ thuật | — | — |
| Tester phụ trách | — | — |
| Khách hàng / PO | — | — |
