# Thiết Kế Chi Tiết Tính Năng: Thống Kê Sử Dụng Dịch Vụ (Service Usage Report)

**Dự án:** Clinic CMS
**Task:** TASK-126
**Phiên bản:** 1.0
**Ngày:** 2026-07-30
**Người thực hiện:** Code Implementation Agent
**Trạng thái:** Đã triển khai (BE + FE) — chờ Code Review / Test
**Tài liệu liên quan:** TASK-125 (Service Type), TASK-015/TASK-024 (Reports module), implementation-plan.md, task.md

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-07-30 | Phiên bản đầu tiên — hoàn tất Implementation, sẵn sàng Review |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Danh sách API](#3-danh-sách-api)
- [4. Truy vấn tổng hợp (SQL)](#4-truy-vấn-tổng-hợp-sql)
- [5. Quy tắc nghiệp vụ](#5-quy-tắc-nghiệp-vụ)
- [6. Xử lý lỗi](#6-xử-lý-lỗi)
- [7. Giao diện người dùng](#7-giao-diện-người-dùng)
- [8. Ghi chú và lưu ý khi kiểm thử](#8-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Module Reports hiện có các báo cáo doanh thu, hiệu suất bác sĩ, lượng khám, đơn thuốc... nhưng chưa có báo cáo trả lời câu hỏi "dịch vụ nào được sử dụng nhiều nhất, mang lại doanh thu bao nhiêu, thuộc loại gì (Khám/Thủ thuật/Xét nghiệm — TASK-125)". TASK-126 bổ sung báo cáo **Thống kê sử dụng dịch vụ**, tổng hợp trực tiếp từ `visit_service` (nguồn dữ liệu gốc, không qua `invoice`), giúp phòng khám thấy được cơ cấu dịch vụ theo thời gian, có thể lọc theo bác sĩ thực hiện.

### 1.2 Phạm vi

**Bao gồm:**
- BE: endpoint `GET /reports/service-usage` — số lượt sử dụng + doanh thu theo dịch vụ, nhóm kèm loại dịch vụ (TASK-125), lọc theo khoảng thời gian và (tùy chọn) bác sĩ.
- BE: endpoint `GET /reports/service-usage/export` — xuất Excel cùng dữ liệu.
- FE: trang `/reports/service-usage` (bảng + biểu đồ top 10 + filter khoảng thời gian + xuất CSV/Excel), thêm tab vào Reports Hub.
- Test: integration test đối soát (số lượt/doanh thu, loại trừ cancelled/deleted, biên timezone, lọc theo bác sĩ, cách ly tenant) + unit test schema + component test FE.

**Không bao gồm:**
- Bộ lọc bác sĩ trên giao diện FE (BE đã hỗ trợ `doctor_id` query param, nhưng FE v1 chưa có ô chọn bác sĩ trên UI — xem mục 8.3 "Hạn chế hiện tại"). Người dùng muốn xem theo bác sĩ hiện dùng báo cáo `/reports/doctor-performance` sẵn có.
- Migration DB mới — cột `service_type_id` đã được TASK-125 thêm vào bảng `service` và đã có trên `dev`.
- Đối soát tự động với số liệu hoá đơn thực thu (invoice `paid`) — báo cáo này dùng **giá niêm yết** ghi nhận trên `visit_service` (xem mục 5, BR-001), không phải tiền thực thu.

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Quản lý phòng khám / Kế toán** | Có quyền `report.financial` — xem báo cáo để đánh giá cơ cấu dịch vụ, doanh thu theo loại. |
| **TASK-125 (Service Type)** | Nguồn phân loại — báo cáo group theo `service_type_id`/`name` qua join, không sửa đổi bảng `service_type`. |
| **TASK-128 (Commission — tương lai)** | Có thể tham chiếu cùng cách tính doanh thu theo `service_type_id` khi tính hoa hồng. |

---

## 2. Luồng xử lý tổng thể

```
[visit_service] ──JOIN── [service] ──LEFT JOIN── [service_type]
      │ (status != cancelled, is_deleted = false)
      │ (created_at trong khoảng [start, end] theo giờ VN)
      ▼
[GROUP BY service_id, service_type_id]
      │ COUNT(*)                                   → usage_count
      │ SUM(quantity*unit_price - discount_amount) → revenue
      ▼
[ServiceUsageReport] ──► FE: bảng + biểu đồ top 10 + xuất Excel/CSV
```

Khi có `doctor_id` filter: thêm `JOIN visit v ON v.id = vs.visit_id` và `WHERE v.doctor_id = :doctor_id` — không đổi hình dạng kết quả (vẫn 1 dòng/dịch vụ), chỉ thu hẹp tập dữ liệu đầu vào.

---

## 3. Danh sách API

Xem chi tiết đầy đủ (request/response/lỗi) tại `docs/tasks/TASK-126/deliveries/api-specs/service-usage-api.md`.

| STT | Phương thức | Đường dẫn | Quyền yêu cầu | Mô tả tóm tắt |
|-----|------------|-----------|---------------|--------------|
| 1 | GET | `/api/v1/reports/service-usage` | `report.financial` | Số lượt + doanh thu theo dịch vụ, trong khoảng thời gian |
| 2 | GET | `/api/v1/reports/service-usage/export` | `report.financial` | Xuất Excel cùng dữ liệu |

> **Không có quyền mới** — dùng lại `report.financial` (báo cáo có doanh thu), cùng quyền với `revenue`, `doctor-performance`, `inventory-valuation`.

---

## 4. Truy vấn tổng hợp (SQL)

```sql
SELECT
    s.id AS service_id, s.name AS service_name,
    st.id AS service_type_id, st.name AS service_type_name,
    COUNT(*) AS usage_count,
    COALESCE(SUM(vs.quantity * vs.unit_price - COALESCE(vs.discount_amount, 0)), 0) AS revenue
FROM visit_service vs
JOIN service s ON s.id = vs.service_id
LEFT JOIN service_type st ON st.id = s.service_type_id
[JOIN visit v ON v.id = vs.visit_id]  -- chỉ khi có doctor_id filter
WHERE vs.clinic_id = :clinic_id
  AND vs.status != 'cancelled'
  AND vs.is_deleted = FALSE
  AND (vs.created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date BETWEEN :start_date AND :end_date
  [AND v.doctor_id = :doctor_id]
GROUP BY s.id, s.name, st.id, st.name
ORDER BY revenue DESC, usage_count DESC
```

Cài đặt tại `app/modules/reports/services/service_usage_service.py`, theo đúng khuôn `doctor_performance_service.py` (raw `sqlalchemy.text()`, không CTE, `result.mappings()`).

**Ghi chú kỹ thuật:**
- Không cần resolve tên qua ORM (khác `doctor_performance_service.py` — `full_name` bác sĩ là `EncryptedString`) vì `service.name`/`service_type.name` là cột text thường, group/COALESCE trực tiếp trong SQL được.
- `visit_service` có sẵn cột `clinic_id` (kế thừa `TenantMixin`) nên lọc tenant trực tiếp trên `vs.clinic_id`, không bắt buộc phải join `visit` (chỉ join khi cần `doctor_id`).

---

## 5. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Lý do / Hành vi |
|----|--------------|-----------------|
| BR-001 | `revenue` tính theo **giá niêm yết đã ghi nhận trên lượt khám** (`quantity * unit_price - discount_amount`, giống công thức `invoice_service.py::_pull_lines_from_visit`), **không phải** tiền thực thu trên hoá đơn (có thể lệch do hoá đơn bị void/hoàn tiền/thanh toán một phần). | Trả lời đúng câu hỏi "dịch vụ nào được thực hiện, trị giá bao nhiêu" độc lập với trạng thái thanh toán; không cần join `invoice`/`payment`. |
| BR-002 | Loại trừ `vs.status = 'cancelled'` và `vs.is_deleted = true` khỏi mọi phép đếm/tổng. | Dịch vụ đã huỷ/xoá mềm không phải là "đã sử dụng". |
| BR-003 | Bộ lọc khoảng thời gian và việc quy định "ngày" đều tính theo giờ địa phương phòng khám (`Asia/Ho_Chi_Minh`), không dùng UTC thô (M-10 — lỗi đã gặp ở các báo cáo khác trước đây). | Một `visit_service` tạo lúc 23h UTC có thể đã sang ngày hôm sau theo giờ VN — nếu dùng UTC thô sẽ gán nhầm ngày. |
| BR-004 | Dịch vụ chưa được phân loại (`service_type_id IS NULL` — dữ liệu trước TASK-125 hoặc chưa được admin gán loại) vẫn xuất hiện trong báo cáo, với `service_type_id`/`service_type_name = null`. | Ẩn dịch vụ chưa phân loại sẽ làm báo cáo thiếu doanh thu — vi phạm AC "khớp dữ liệu thực". FE hiển thị nhãn "Chưa phân loại". |
| BR-005 | `doctor_id` là **bộ lọc**, không phải chiều nhóm (group-by) — báo cáo luôn trả về 1 dòng/dịch vụ, dù có hay không lọc theo bác sĩ. | Giữ hình dạng response đơn giản; muốn xem breakdown đầy đủ theo bác sĩ, dùng `/reports/doctor-performance` sẵn có (đã resolve `doctor_name` qua ORM). |
| BR-006 | Không có migration mới — đọc `service_type_id` qua `LEFT JOIN service_type` trực tiếp (cột đã có từ TASK-125 trên `dev`). | Tránh trùng lặp migration, tận dụng hạ tầng TASK-125 đã merge. |

---

## 6. Xử lý lỗi

| Mã HTTP | Tình huống xảy ra |
|---------|-------------------|
| 401/403 | Thiếu token hoặc thiếu quyền `report.financial` |
| 422 | Thiếu/sai định dạng `start`/`end` (không phải `YYYY-MM-DD`) |

Không có lỗi nghiệp vụ riêng (404/409) — báo cáo chỉ đọc dữ liệu, không có thao tác ghi.

---

## 7. Giao diện người dùng

| Màn hình | Mô tả |
|----------|-------|
| **`/reports/service-usage`** (mới) | Trang báo cáo — copy khuôn `DoctorPerformancePage.tsx`: `RequirePermission` (`report.financial`), `DateRangeFilter` (chỉ khoảng ngày, không granularity), 3 thẻ tổng hợp (tổng lượt, tổng doanh thu, số dịch vụ), biểu đồ cột top 10 dịch vụ (lượt + doanh thu, 2 trục Y), bảng chi tiết có phân trang, nút xuất CSV (client-side) và xuất Excel (`ExportExcelButton` + `useExportDownload` gọi `/export`). |
| **Reports Hub** (mở rộng) | Thêm tab "Thống kê dịch vụ" vào `TABS` trong `ReportsHubPage.tsx`, đặt ngay sau tab "Hiệu suất bác sĩ". |

Sidebar/router: route `/reports/service-usage` lazy-loaded, bọc `RequirePermission` bên trong component (giống mọi trang report khác — router không tự bọc permission).

---

## 8. Ghi chú và lưu ý khi kiểm thử

### 8.1 Điểm quan trọng cần nắm

- Doanh thu ở đây **không** phải số tiền đã thu thực tế trên hoá đơn — xem BR-001. Khi đối soát với kế toán, cần làm rõ đây là "giá trị dịch vụ đã ghi nhận" chứ không phải "tiền đã thu".
- Dịch vụ "chưa phân loại" (`service_type_id = null`) là hợp lệ, không phải lỗi — xem BR-004.
- `doctor_id` chỉ là filter — không có breakdown "theo bác sĩ" đầy đủ trong response (xem BR-005 và mục 1.2 "Không bao gồm").

### 8.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| 1 dịch vụ, 2 lượt sử dụng (có discount) | qty=1@200.000 + qty=2@50.000 (discount 10.000) | `usage_count=2`, `revenue=290.000` |
| Có lượt cancelled + soft-deleted | 1 lượt hợp lệ + 1 cancelled + 1 is_deleted | Chỉ đếm 1 lượt hợp lệ |
| Biên timezone (M-10) | `created_at` = 17:30 UTC ngày X (= 00:30 giờ VN ngày X+1) | Xuất hiện khi query ngày X+1 (giờ VN), KHÔNG xuất hiện khi query ngày X (UTC thô) |
| Lọc theo bác sĩ | 2 visit khác bác sĩ, cùng 1 dịch vụ | `doctor_id=A` → chỉ đếm lượt của bác sĩ A |
| Cách ly tenant | Dịch vụ giá trị lớn ở clinic khác | Không xuất hiện trong báo cáo của clinic hiện tại |

### 8.3 Hạn chế hiện tại

- FE v1 chưa có ô lọc theo bác sĩ trên giao diện (BE đã hỗ trợ qua query param `doctor_id`) — có thể bổ sung sau nếu có nhu cầu thực tế.
- Chưa kiểm thử tích hợp với DB thật trong phiên làm việc này — môi trường không có Postgres/Redis chạy sẵn ngoài stack `w2e` (theo chỉ đạo không được khởi động/đụng vào stack đó), và Python cài sẵn trên máy là 3.10 trong khi dự án yêu cầu 3.11 (`datetime.UTC`, `enum.StrEnum` — không import được `app.main` để chạy pytest, kể cả unit test schema thuần). Đã xác nhận thủ công logic schema Pydantic (`ServiceUsageRow`/`ServiceUsageReport`) hoạt động đúng bằng cách import trực tiếp module schema (bỏ qua `conftest.py`/`app.main`). Test tích hợp đã viết sẵn (`tests/integration/reports/test_service_usage_e2e.py`) theo đúng khuôn `test_reports_e2e.py` + `test_task125_service_type_e2e.py`, sẵn sàng chạy khi có DB + Python 3.11.
- FE: test suite, type-check, và ESLint **đã chạy thành công** trong worktree này (Node 20, `npm install` cục bộ) — 35/35 test pass trong `src/tests/reports/`, toàn bộ 1141/1144 test pass ở mức full suite (3 test lỗi thuộc `ForgotPasswordPage`/`QueuePage`, không liên quan TASK-126, đã xác nhận là lỗi có sẵn trước khi bắt đầu task này).

### 8.4 Hướng phát triển

- Bổ sung ô lọc bác sĩ trên UI nếu có nhu cầu xem nhanh theo bác sĩ mà không rời trang.
- Cân nhắc thêm chế độ "theo loại dịch vụ" (group-by service_type thay vì service) nếu người dùng cần view tổng hợp cấp cao hơn.

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Trưởng nhóm kỹ thuật | | |
| Tester phụ trách | | |
| Khách hàng / PO | | |
