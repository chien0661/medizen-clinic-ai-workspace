# API: Shifts

**Phiên bản:** 1.0  
**Ngày:** 2026-04-28  
**Task:** TASK-014

---

## Tổng quan

Shifts là các ca làm việc cụ thể theo ngày cho từng nhân viên. Có thể tạo từ Shift Template hoặc tạo tự do (custom shift). Chỉ admin (`shift.manage` permission) có thể quản lý.

---

## Danh sách Endpoints

| Phương thức | Đường dẫn | Mô tả |
|------------|-----------|-------|
| GET | `/api/v1/shifts` | Lấy danh sách shifts (lọc theo ngày, nhân viên) |
| POST | `/api/v1/shifts` | Tạo shift mới |
| PATCH | `/api/v1/shifts/{id}` | Cập nhật shift |
| DELETE | `/api/v1/shifts/{id}` | Xóa shift (soft delete) |

---

## Chi tiết từng API

### 1. GET /api/v1/shifts

**Mô tả:** Lấy danh sách shifts với hỗ trợ lọc theo khoảng thời gian và nhân viên.

**Xác thực:** Bearer token + `shift.manage` permission

**Tham số Query:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Mặc định |
|---------|------|---------|-------|---------|
| `from` | Date | Không | Ngày bắt đầu (YYYY-MM-DD) | Không lọc |
| `to` | Date | Không | Ngày kết thúc (YYYY-MM-DD) | Không lọc |
| `user_id` | UUID | Không | Lọc theo nhân viên cụ thể | Không lọc |
| `skip` | Integer | Không | Số bản ghi bỏ qua | 0 |
| `limit` | Integer | Không | Số bản ghi tối đa | 100 |

**Truy vấn dữ liệu:**

```python
# Lấy shifts với các điều kiện lọc
SELECT * FROM shift
WHERE clinic_id = :clinic_id
  AND NOT is_deleted
  AND (shift_date >= :from_date OR :from_date IS NULL)
  AND (shift_date <= :to_date OR :to_date IS NULL)
  AND (user_id = :user_id OR :user_id IS NULL)
ORDER BY shift_date ASC, start_time ASC
LIMIT :limit OFFSET :skip
```

**Kết quả (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440100",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "user_id": "550e8400-e29b-41d4-a716-446655440010",
      "shift_template_id": "550e8400-e29b-41d4-a716-446655440000",
      "shift_date": "2026-05-01",
      "start_time": "07:30:00",
      "end_time": "12:00:00",
      "role_in_shift": "Doctor",
      "status": "scheduled",
      "cancel_reason": null,
      "notes": null,
      "created_at": "2026-04-28T10:00:00+00:00",
      "updated_at": "2026-04-28T10:00:00+00:00"
    }
  ],
  "total": 1
}
```

**Mã lỗi:**
- **401 Unauthorized** — Chưa xác thực
- **403 Forbidden** — Không có quyền `shift.manage`

---

### 2. POST /api/v1/shifts

**Mô tả:** Tạo một shift cụ thể.

**Xác thực:** Bearer token + `shift.manage` permission

**Request Body:**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440010",
  "shift_template_id": "550e8400-e29b-41d4-a716-446655440000",
  "shift_date": "2026-05-02",
  "start_time": "07:30:00",
  "end_time": "12:00:00",
  "role_in_shift": "Doctor",
  "notes": "Khám ngoài"
}
```

**Tham số:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Ràng buộc |
|---------|------|---------|-------|----------|
| `user_id` | UUID | Có | ID nhân viên | Phải tồn tại |
| `shift_template_id` | UUID | Không | ID shift template (nếu null = custom) | |
| `shift_date` | Date | Có | Ngày làm việc | YYYY-MM-DD |
| `start_time` | Time | Có | Giờ bắt đầu | HH:MM:SS |
| `end_time` | Time | Có | Giờ kết thúc | HH:MM:SS, phải > start_time |
| `role_in_shift` | String | Không | Role trong shift | Max 50 ký tự |
| `notes` | String | Không | Ghi chú | |

**Quy tắc nghiệp vụ:**
- `end_time` phải > `start_time` (BR-01)
- UNIQUE (clinic_id, user_id, shift_date, start_time) — không thể tạo 2 shifts với cùng clinic/user/date/start_time (BR-06)

**Kết quả (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440101",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440010",
  "shift_template_id": "550e8400-e29b-41d4-a716-446655440000",
  "shift_date": "2026-05-02",
  "start_time": "07:30:00",
  "end_time": "12:00:00",
  "role_in_shift": "Doctor",
  "status": "scheduled",
  "cancel_reason": null,
  "notes": "Khám ngoài",
  "created_at": "2026-04-28T10:30:00+00:00",
  "updated_at": "2026-04-28T10:30:00+00:00"
}
```

**Mã lỗi:**
- **400 Bad Request** — Quy tắc bị vi phạm (ví dụ: `end_time <= start_time`, hoặc trùng lặp shift)
- **401 Unauthorized** — Chưa xác thực
- **403 Forbidden** — Không có quyền `shift.manage`
- **404 Not Found** — User hoặc shift_template không tồn tại
- **409 Conflict** — UNIQUE constraint violation (shift trùng lặp)
- **422 Unprocessable Entity** — Lỗi validation

---

### 3. PATCH /api/v1/shifts/{id}

**Mô tả:** Cập nhật một shift.

**Xác thực:** Bearer token + `shift.manage` permission

**Tham số Path:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `id` | UUID | ID của shift cần cập nhật |

**Request Body (tất cả trường optional):**

```json
{
  "shift_date": "2026-05-03",
  "start_time": "08:00:00",
  "end_time": "13:00:00",
  "role_in_shift": "Nurse",
  "status": "cancelled",
  "cancel_reason": "Nhân viên bị ốm",
  "notes": "Cập nhật ghi chú"
}
```

**Tham số:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Ràng buộc |
|---------|------|---------|-------|----------|
| `shift_date` | Date | Không | Ngày mới | |
| `start_time` | Time | Không | Giờ bắt đầu mới | Nếu có, phải < end_time |
| `end_time` | Time | Không | Giờ kết thúc mới | Nếu có, phải > start_time |
| `role_in_shift` | String | Không | Role mới | Max 50 ký tự |
| `status` | String | Không | Trạng thái mới | scheduled / cancelled / on_leave / completed |
| `cancel_reason` | String | Không | Lý do hủy | Nếu status = cancelled |
| `notes` | String | Không | Ghi chú mới | |

**Quy tắc nghiệp vụ:**
- Nếu cập nhật time, `end_time` phải > `start_time` (BR-01b)

**Kết quả (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440101",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440010",
  "shift_template_id": "550e8400-e29b-41d4-a716-446655440000",
  "shift_date": "2026-05-03",
  "start_time": "08:00:00",
  "end_time": "13:00:00",
  "role_in_shift": "Nurse",
  "status": "cancelled",
  "cancel_reason": "Nhân viên bị ốm",
  "notes": "Cập nhật ghi chú",
  "created_at": "2026-04-28T10:30:00+00:00",
  "updated_at": "2026-04-28T10:45:00+00:00"
}
```

**Mã lỗi:**
- **400 Bad Request** — Quy tắc bị vi phạm
- **401 Unauthorized** — Chưa xác thực
- **403 Forbidden** — Không có quyền hoặc thuộc clinic khác
- **404 Not Found** — Shift không tồn tại
- **422 Unprocessable Entity** — Lỗi validation

---

### 4. DELETE /api/v1/shifts/{id}

**Mô tả:** Xóa mềm (soft delete) một shift.

**Xác thực:** Bearer token + `shift.manage` permission

**Tham số Path:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `id` | UUID | ID của shift cần xóa |

**Kết quả (204 No Content):**

Không trả về body.

**Mã lỗi:**
- **401 Unauthorized** — Chưa xác thực
- **403 Forbidden** — Không có quyền hoặc thuộc clinic khác
- **404 Not Found** — Shift không tồn tại

---

## Định dạng lỗi chung

```json
{
  "detail": "Mô tả lỗi chi tiết"
}
```

---

## Ghi chú

- Status shift: `scheduled` (mặc định), `cancelled`, `on_leave` (khi leave được approve), `completed`
- Khi tạo shift từ recurring schedule, `shift_template_id` được lưu để theo dõi gốc
- Custom shifts (không từ template) sẽ có `shift_template_id = null`
- Soft delete: shifts bị xóa không xuất hiện trong GET nhưng vẫn được tham chiếu từ TimeLog
