# API: Attendance (Time Log)

**Phiên bản:** 1.0  
**Ngày:** 2026-04-28  
**Task:** TASK-014

---

## Tổng quan

Attendance API quản lý check-in / check-out của nhân viên. Mỗi check-in tạo TimeLog entry. Hệ thống tự động tính toán total_hours, late_minutes, ot_hours.

---

## Danh sách Endpoints

| Phương thức | Đường dẫn | Mô tả |
|------------|-----------|-------|
| POST | `/api/v1/attendance/check-in` | Check-in (requires `attendance.manage`) |
| POST | `/api/v1/attendance/check-out` | Check-out (requires `attendance.manage`) |
| GET | `/api/v1/attendance/me` | Xem time log của bản thân (bất kỳ user) |
| GET | `/api/v1/attendance` | Xem time log of all users (requires `attendance.manage`) |
| GET | `/api/v1/attendance/export` | Export time log (xlsx) (requires `attendance.manage`) |

---

## Chi tiết từng API

### 1. POST /api/v1/attendance/check-in

**Mô tả:** Check-in một nhân viên. Tạo TimeLog entry mới.

**Xác thực:** Bearer token + `attendance.manage` permission

**Request Body:**

```json
{
  "shift_id": "550e8400-e29b-41d4-a716-446655440101",
  "check_in_method": "manual",
  "check_in_location": "192.168.1.10",
  "notes": "Check-in bình thường"
}
```

**Tham số:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Ràng buộc |
|---------|------|---------|-------|----------|
| `shift_id` | UUID | Không | ID shift (nếu null = check-in không liên kết shift) | Nếu có, phải tồn tại |
| `check_in_method` | String | Có | Phương thức check-in | manual / pin / qr / biometric |
| `check_in_location` | String | Không | Vị trí check-in (IP, device ID, v.v.) | Max 200 ký tự |
| `notes` | String | Không | Ghi chú | |

**Quy tắc nghiệp vụ:**
- Không thể có 2 TimeLog active (check-out=null) cùng lúc cho 1 user → 409 Conflict (BR-08)
- Nếu `shift_id` được cung cấp, shift phải tồn tại, không bị xóa, và thuộc user/clinic đó (BR-09, BR-10)

**Kết quả (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440400",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440010",
  "shift_id": "550e8400-e29b-41d4-a716-446655440101",
  "check_in_at": "2026-05-01T07:45:00+00:00",
  "check_out_at": null,
  "check_in_method": "manual",
  "check_in_location": "192.168.1.10",
  "notes": "Check-in bình thường",
  "late_minutes": 15,
  "total_hours": null,
  "ot_hours": null,
  "created_at": "2026-05-01T07:45:00+00:00",
  "updated_at": "2026-05-01T07:45:00+00:00"
}
```

**Computed Fields:**
- `late_minutes` = max(0, check_in_time - shift.start_time) nếu shift_id được cung cấp, nếu không = null (BR-12)

**Mã lỗi:**
- **400 Bad Request** — Quy tắc bị vi phạm
- **401 Unauthorized**
- **403 Forbidden** — Không có quyền, hoặc shift_id thuộc clinic khác/user khác
- **404 Not Found** — Shift không tồn tại hoặc đã bị xóa (BR-09)
- **409 Conflict** — Đã có TimeLog active (chưa check-out) (BR-08)
- **422 Unprocessable Entity** — Lỗi validation

---

### 2. POST /api/v1/attendance/check-out

**Mô tả:** Check-out cho nhân viên hiện tại. Cập nhật TimeLog entry gần nhất (chưa check-out).

**Xác thực:** Bearer token + `attendance.manage` permission

**Request Body:**

```json
{
  "notes": "Check-out bình thường"
}
```

**Tham số:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Ràng buộc |
|---------|------|---------|-------|----------|
| `notes` | String | Không | Ghi chú | |

**Quy tắc nghiệp vụ:**
- Phải có TimeLog active (check_out_at = null) → 404 nếu không (BR-11)

**Kết quả (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440400",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440010",
  "shift_id": "550e8400-e29b-41d4-a716-446655440101",
  "check_in_at": "2026-05-01T07:45:00+00:00",
  "check_out_at": "2026-05-01T12:30:00+00:00",
  "check_in_method": "manual",
  "check_in_location": "192.168.1.10",
  "notes": "Check-out bình thường",
  "late_minutes": 15,
  "total_hours": 4.75,
  "ot_hours": 0.5,
  "created_at": "2026-05-01T07:45:00+00:00",
  "updated_at": "2026-05-01T12:30:00+00:00"
}
```

**Computed Fields:**
- `total_hours` = (check_out_at - check_in_at) / 3600 (BR-14)
- `ot_hours` = max(0, check_out_at - shift.end_time) nếu shift_id được cung cấp, nếu không = null (BR-13)

**Mã lỗi:**
- **401 Unauthorized**
- **403 Forbidden** — Không có quyền
- **404 Not Found** — Không có TimeLog active (BR-11)
- **422 Unprocessable Entity** — Lỗi validation

---

### 3. GET /api/v1/attendance/me

**Mô tả:** Xem time log của bản thân (user hiện tại). Bất kỳ authenticated user nào cũng có thể xem.

**Xác thực:** Bearer token (không cần `attendance.manage`)

**Tham số Query:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Mặc định |
|---------|------|---------|-------|---------|
| `from` | Date | Không | Từ ngày (YYYY-MM-DD) | Không lọc |
| `to` | Date | Không | Đến ngày (YYYY-MM-DD) | Không lọc |
| `skip` | Integer | Không | Bỏ qua | 0 |
| `limit` | Integer | Không | Tối đa | 100 |

**Truy vấn dữ liệu:**

```python
SELECT * FROM time_log
WHERE user_id = :current_user_id
  AND clinic_id = :current_clinic_id
  AND NOT is_deleted
  AND (CAST(check_in_at AS DATE) >= :from_date OR :from_date IS NULL)
  AND (CAST(check_in_at AS DATE) <= :to_date OR :to_date IS NULL)
ORDER BY check_in_at DESC
LIMIT :limit OFFSET :skip
```

**Kết quả (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440400",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "user_id": "550e8400-e29b-41d4-a716-446655440010",
      "shift_id": "550e8400-e29b-41d4-a716-446655440101",
      "check_in_at": "2026-05-01T07:45:00+00:00",
      "check_out_at": "2026-05-01T12:30:00+00:00",
      "check_in_method": "manual",
      "check_in_location": "192.168.1.10",
      "notes": "Check-out bình thường",
      "late_minutes": 15,
      "total_hours": 4.75,
      "ot_hours": 0.5,
      "created_at": "2026-05-01T07:45:00+00:00",
      "updated_at": "2026-05-01T12:30:00+00:00"
    }
  ],
  "total": 1
}
```

**Mã lỗi:**
- **401 Unauthorized** — Chưa xác thực

---

### 4. GET /api/v1/attendance

**Mô tả:** Lấy time log của tất cả nhân viên (admin view).

**Xác thực:** Bearer token + `attendance.manage` permission

**Tham số Query:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Mặc định |
|---------|------|---------|-------|---------|
| `user_id` | UUID | Không | Lọc theo nhân viên | Không lọc |
| `from` | Date | Không | Từ ngày | Không lọc |
| `to` | Date | Không | Đến ngày | Không lọc |
| `skip` | Integer | Không | Bỏ qua | 0 |
| `limit` | Integer | Không | Tối đa | 100 |

**Truy vấn dữ liệu:** Tương tự GET /attendance/me, nhưng không filter theo `current_user_id` (filter theo `user_id` param nếu có).

**Kết quả (200 OK):** Tương tự GET /attendance/me.

**Mã lỗi:**
- **401 Unauthorized**
- **403 Forbidden** — Không có quyền `attendance.manage`

---

### 5. GET /api/v1/attendance/export

**Mô tả:** Export time log thành file Excel (xlsx) cho khoảng thời gian chỉ định.

**Xác thực:** Bearer token + `attendance.manage` permission

**Tham số Query:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Mặc định |
|---------|------|---------|-------|---------|
| `from` | Date | Có | Từ ngày (YYYY-MM-DD) | — |
| `to` | Date | Có | Đến ngày (YYYY-MM-DD) | — |
| `format` | String | Không | Định dạng export | xlsx |

**Giá trị hợp lệ của `format`:**

| Giá trị | Mô tả |
|--------|-------|
| `xlsx` | Microsoft Excel 2007+ | Excel (hiện chỉ hỗ trợ) |

**Kết quả (200 OK):**

```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename=attendance_2026-05-01_2026-05-31.xlsx

[Binary XLSX data]
```

**Cấu trúc Excel:**

Sheet "Attendance":
- Column A: User ID
- Column B: User Name (nếu có)
- Column C: Check-in Date
- Column D: Check-in Time
- Column E: Check-out Time
- Column F: Total Hours
- Column G: Late Minutes
- Column H: OT Hours
- Column I: Method
- Column J: Notes

**Truy vấn dữ liệu (pseudocode):**

```python
SELECT
  tl.user_id,
  u.full_name,
  DATE(tl.check_in_at),
  tl.check_in_at,
  tl.check_out_at,
  tl.total_hours,
  tl.late_minutes,
  tl.ot_hours,
  tl.check_in_method,
  tl.notes
FROM time_log tl
JOIN user u ON tl.user_id = u.id
WHERE tl.clinic_id = :clinic_id
  AND NOT tl.is_deleted
  AND CAST(tl.check_in_at AS DATE) >= :from_date
  AND CAST(tl.check_in_at AS DATE) <= :to_date
ORDER BY tl.user_id, tl.check_in_at
```

**Performance:**
- Excel export cho 1 tháng × 10 nhân viên < 1s (AC5 requirement)
- Excel export cho 3 tháng × 50 nhân viên ~ 2.28s (tested)

**Mã lỗi:**
- **400 Bad Request** — Format không hỗ trợ (không phải `xlsx`)
- **401 Unauthorized**
- **403 Forbidden** — Không có quyền `attendance.manage`
- **422 Unprocessable Entity** — Date format sai (ví dụ: không phải YYYY-MM-DD)

---

## Định dạng lỗi chung

```json
{
  "detail": "Mô tả lỗi chi tiết"
}
```

---

## Ghi chú

- **Check-in Method:** manual (nhập tay), pin (mã PIN), qr (mã QR), biometric (vân tay/mặt — Tauri client)
- **Computed Fields:**
  - `late_minutes` = max(0, check_in_time - shift.start_time) nếu shift_id có, nếu không = null
  - `ot_hours` = max(0, check_out_time - shift.end_time) nếu shift_id có, nếu không = null
  - `total_hours` = (check_out_time - check_in_time) / 3600 (giờ thập phân)
- **Tenant Isolation (BR-15):** Tất cả time logs phải belonged to same clinic
- **Self check-in only:** Admin không thể check-in cho người khác — check-in luôn áp dụng cho user_id từ JWT
