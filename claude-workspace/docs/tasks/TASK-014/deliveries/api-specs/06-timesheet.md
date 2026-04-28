# API: Timesheet Report

**Phiên bản:** 1.0  
**Ngày:** 2026-04-28  
**Task:** TASK-014

---

## Tổng quan

Timesheet API cung cấp báo cáo tổng hợp giờ làm của tất cả nhân viên trong một tháng. Dữ liệu được tính toán từ time logs (tổng giờ làm, số ngày làm việc, v.v.).

---

## Danh sách Endpoints

| Phương thức | Đường dẫn | Mô tả |
|------------|-----------|-------|
| GET | `/api/v1/hr/timesheet` | Lấy báo cáo timesheet theo tháng |

---

## Chi tiết API

### GET /api/v1/hr/timesheet

**Mô tả:** Lấy báo cáo timesheet (tổng giờ làm) cho tất cả nhân viên trong một tháng.

**Xác thực:** Bearer token + `attendance.manage` permission

**Tham số Query:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Format |
|---------|------|---------|-------|--------|
| `month` | String | Có | Tháng cần báo cáo | YYYY-MM |

**Truy vấn dữ liệu:**

```sql
-- Tổng hợp time log theo user và tháng
SELECT
  tl.user_id,
  u.full_name,
  COUNT(DISTINCT DATE(tl.check_in_at)) AS days_worked,
  ROUND(SUM(tl.total_hours)::NUMERIC, 2) AS total_hours,
  ROUND(SUM(COALESCE(tl.late_minutes, 0))::NUMERIC / 60, 2) AS total_late_hours,
  ROUND(SUM(COALESCE(tl.ot_hours, 0))::NUMERIC, 2) AS total_ot_hours,
  COUNT(tl.id) AS total_entries
FROM time_log tl
JOIN user u ON tl.user_id = u.id
WHERE tl.clinic_id = :clinic_id
  AND NOT tl.is_deleted
  AND EXTRACT(YEAR FROM tl.check_in_at) = :year
  AND EXTRACT(MONTH FROM tl.check_in_at) = :month
GROUP BY tl.user_id, u.full_name
ORDER BY u.full_name ASC
```

**Kết quả (200 OK):**

```json
{
  "month": "2026-05",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "employees": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440010",
      "full_name": "Nguyễn Văn A",
      "days_worked": 22,
      "total_hours": 176.5,
      "total_late_hours": 2.25,
      "total_ot_hours": 8.5
    },
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440011",
      "full_name": "Trần Thị B",
      "days_worked": 20,
      "total_hours": 160.0,
      "total_late_hours": 0.0,
      "total_ot_hours": 0.0
    }
  ],
  "summary": {
    "total_employees": 2,
    "total_hours_clinic": 336.5,
    "total_late_hours_clinic": 2.25,
    "total_ot_hours_clinic": 8.5
  }
}
```

**Mô tả các trường:**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `user_id` | UUID | ID nhân viên |
| `full_name` | String | Tên đầy đủ nhân viên |
| `days_worked` | Integer | Số ngày công (số ngày distinct có check-in) |
| `total_hours` | Decimal | Tổng giờ làm (decimal, ví dụ: 176.5 = 176 giờ 30 phút) |
| `total_late_hours` | Decimal | Tổng giờ đi muộn (tính từ late_minutes) |
| `total_ot_hours` | Decimal | Tổng giờ làm thêm (OT) |

**Summary:**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `total_employees` | Integer | Số nhân viên có time log trong tháng |
| `total_hours_clinic` | Decimal | Tổng giờ làm toàn clinic |
| `total_late_hours_clinic` | Decimal | Tổng late hours toàn clinic |
| `total_ot_hours_clinic` | Decimal | Tổng OT hours toàn clinic |

---

### Logic tính toán tham số

**Xác định năm và tháng từ `month` parameter:**

```python
# Input: month = "2026-05"
year, month = month.split('-')
year = int(year)
month = int(month)

if month < 1 or month > 12:
    raise ValueError("Month must be 1-12")
```

**Lọc dữ liệu:**
- `EXTRACT(YEAR FROM check_in_at) = :year`
- `EXTRACT(MONTH FROM check_in_at) = :month`

**Tính days_worked:**
- Count distinct dates (DATE(check_in_at)) — nếu nhân viên check-in nhiều lần trong 1 ngày, chỉ tính 1 ngày

**Tính total_late_hours:**
- `SUM(late_minutes) / 60` — chuyển đổi từ phút sang giờ

---

## Mã lỗi

| HTTP Code | Mô tả |
|-----------|-------|
| 200 | Thành công |
| 400 | Month format sai (không phải YYYY-MM) |
| 401 | Chưa xác thực |
| 403 | Không có quyền `attendance.manage` |
| 422 | Lỗi validation (month không hợp lệ, ví dụ: month > 12) |

**Ví dụ lỗi:**

```json
{
  "detail": "Invalid month format. Use YYYY-MM (e.g., 2026-05)"
}
```

---

## Ghi chú

- **Tháng truy cập:** API hỗ trợ bất kỳ tháng nào (quá khứ, hiện tại, hoặc tương lai nếu có dữ liệu)
- **Timezone:** Tất cả dates được tính dựa trên UTC (check_in_at là timestamp with timezone)
- **Employees without logs:** Nhân viên không có time log nào trong tháng sẽ không xuất hiện trong báo cáo
- **Performance:** Báo cáo 1 tháng × 50 nhân viên ~ 50-100ms
- **Use cases:**
  - Kế toán sử dụng để tính lương
  - HR kiểm tra kỷ luật đi muộn
  - Quản lý xem sức lao động (giờ làm thêm)
