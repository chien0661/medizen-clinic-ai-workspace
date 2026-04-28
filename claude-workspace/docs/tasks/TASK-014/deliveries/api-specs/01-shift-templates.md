# API: Shift Templates

**Phiên bản:** 1.0  
**Ngày:** 2026-04-28  
**Task:** TASK-014

---

## Tổng quan

Shift Templates là các mẫu ca làm việc (ví dụ: "Ca sáng 07:30-12:00", "Ca chiều 13:00-17:30") được định nghĩa ở mức clinic. Chỉ admin (`shift.manage` permission) có thể quản lý.

---

## Danh sách Endpoints

| Phương thức | Đường dẫn | Mô tả |
|------------|-----------|-------|
| GET | `/api/v1/shift-templates` | Lấy danh sách shift templates (có phân trang) |
| POST | `/api/v1/shift-templates` | Tạo shift template mới |
| PATCH | `/api/v1/shift-templates/{id}` | Cập nhật shift template |
| DELETE | `/api/v1/shift-templates/{id}` | Xóa shift template (soft delete) |

---

## Chi tiết từng API

### 1. GET /api/v1/shift-templates

**Mô tả:** Lấy danh sách shift templates của clinic hiện tại, hỗ trợ phân trang.

**Xác thực:** Bearer token + `shift.manage` permission

**Tham số Query:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Mặc định |
|---------|------|---------|-------|---------|
| `skip` | Integer | Không | Số bản ghi bỏ qua | 0 |
| `limit` | Integer | Không | Số bản ghi tối đa trả về | 50 |

**Truy vấn dữ liệu:**

```python
# Lấy tất cả shift templates không bị xóa của clinic, sắp xếp theo tên
SELECT * FROM shift_template
WHERE clinic_id = :clinic_id
  AND NOT is_deleted
ORDER BY name ASC
LIMIT :limit OFFSET :skip
```

**Kết quả (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Ca sáng",
      "start_time": "07:30:00",
      "end_time": "12:00:00",
      "is_active": true,
      "created_at": "2026-04-28T10:00:00+00:00",
      "updated_at": "2026-04-28T10:00:00+00:00"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Ca chiều",
      "start_time": "13:00:00",
      "end_time": "17:30:00",
      "is_active": true,
      "created_at": "2026-04-28T10:00:00+00:00",
      "updated_at": "2026-04-28T10:00:00+00:00"
    }
  ],
  "total": 2
}
```

**Mã lỗi:**
- **401 Unauthorized** — Chưa xác thực hoặc token hết hạn
- **403 Forbidden** — Không có quyền `shift.manage`

---

### 2. POST /api/v1/shift-templates

**Mô tả:** Tạo một shift template mới.

**Xác thực:** Bearer token + `shift.manage` permission

**Request Body:**

```json
{
  "name": "Ca tối",
  "start_time": "18:00:00",
  "end_time": "22:00:00"
}
```

**Tham số:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Ràng buộc |
|---------|------|---------|-------|----------|
| `name` | String | Có | Tên ca làm việc | 1-100 ký tự |
| `start_time` | Time | Có | Giờ bắt đầu ca | HH:MM:SS |
| `end_time` | Time | Có | Giờ kết thúc ca | HH:MM:SS, phải > start_time |

**Quy tắc nghiệp vụ:**
- `end_time` phải lớn hơn `start_time` (BR-01)

**Kết quả (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Ca tối",
  "start_time": "18:00:00",
  "end_time": "22:00:00",
  "is_active": true,
  "created_at": "2026-04-28T10:15:00+00:00",
  "updated_at": "2026-04-28T10:15:00+00:00"
}
```

**Mã lỗi:**
- **400 Bad Request** — Tham số không hợp lệ (ví dụ: `end_time <= start_time`)
- **401 Unauthorized** — Chưa xác thực
- **403 Forbidden** — Không có quyền `shift.manage`
- **422 Unprocessable Entity** — Lỗi validation (ví dụ: `name` rỗng, format thời gian sai)

---

### 3. PATCH /api/v1/shift-templates/{id}

**Mô tả:** Cập nhật một shift template (các trường có thể cập nhật: name, start_time, end_time, is_active).

**Xác thực:** Bearer token + `shift.manage` permission

**Tham số Path:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `id` | UUID | ID của shift template cần cập nhật |

**Request Body (tất cả trường optional):**

```json
{
  "name": "Ca sáng cập nhật",
  "start_time": "07:00:00",
  "end_time": "12:30:00",
  "is_active": false
}
```

**Tham số:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Ràng buộc |
|---------|------|---------|-------|----------|
| `name` | String | Không | Tên mới | 1-100 ký tự nếu có |
| `start_time` | Time | Không | Giờ bắt đầu mới | Nếu có, phải < end_time |
| `end_time` | Time | Không | Giờ kết thúc mới | Nếu có, phải > start_time |
| `is_active` | Boolean | Không | Kích hoạt/vô hiệu hóa | |

**Quy tắc nghiệp vụ:**
- Nếu cả `start_time` và `end_time` được cung cấp, `end_time` phải > `start_time` (BR-01b)
- Nếu chỉ có một trong hai được cung cấp, check vẫn được thực hiện với giá trị cũ

**Kết quả (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Ca sáng cập nhật",
  "start_time": "07:00:00",
  "end_time": "12:30:00",
  "is_active": false,
  "created_at": "2026-04-28T10:00:00+00:00",
  "updated_at": "2026-04-28T10:20:00+00:00"
}
```

**Mã lỗi:**
- **400 Bad Request** — Quy tắc nghiệp vụ bị vi phạm (ví dụ: `end_time <= start_time`)
- **401 Unauthorized** — Chưa xác thực
- **403 Forbidden** — Không có quyền `shift.manage`, hoặc thuộc clinic khác
- **404 Not Found** — Shift template không tồn tại
- **422 Unprocessable Entity** — Lỗi validation

---

### 4. DELETE /api/v1/shift-templates/{id}

**Mô tả:** Xóa mềm (soft delete) một shift template. Hệ thống sẽ đánh dấu `is_deleted = true` thay vì xóa thực sự.

**Xác thực:** Bearer token + `shift.manage` permission

**Tham số Path:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `id` | UUID | ID của shift template cần xóa |

**Kết quả (204 No Content):**

Không trả về body, chỉ status code 204.

**Mã lỗi:**
- **401 Unauthorized** — Chưa xác thực
- **403 Forbidden** — Không có quyền `shift.manage`, hoặc thuộc clinic khác
- **404 Not Found** — Shift template không tồn tại hoặc đã bị xóa

---

## Định dạng lỗi chung

Khi có lỗi, API trả về:

```json
{
  "detail": "Mô tả lỗi chi tiết"
}
```

**Ví dụ:**

```json
{
  "detail": "end_time must be after start_time"
}
```

---

## Ghi chú

- Tất cả endpoint đều yêu cầu header `Authorization: Bearer <token>`.
- Clinic ID được lấy từ JWT token (context), không cần truyền trong request.
- Soft delete: các shift templates bị xóa sẽ không xuất hiện trong danh sách GET, nhưng vẫn tồn tại trong database để lấy lịch sử.
