# API: Recurring Schedules

**Phiên bản:** 1.0  
**Ngày:** 2026-04-28  
**Task:** TASK-014

---

## Tổng quan

Recurring Schedules định nghĩa lịch làm việc lặp lại hàng tuần (ví dụ: "Nhân viên A làm thứ 2, 4, 6 ca sáng"). Hệ thống có cron job để tự động sinh Shifts từ Recurring Schedules cho 30 ngày tới.

---

## Danh sách Endpoints

| Phương thức | Đường dẫn | Mô tả |
|------------|-----------|-------|
| GET | `/api/v1/recurring-schedules` | Lấy danh sách recurring schedules |
| POST | `/api/v1/recurring-schedules` | Tạo recurring schedule mới |
| PATCH | `/api/v1/recurring-schedules/{id}` | Cập nhật recurring schedule |
| DELETE | `/api/v1/recurring-schedules/{id}` | Xóa recurring schedule |
| POST | `/api/v1/recurring-schedules/{id}/generate-shifts` | Tạo shifts từ recurring schedule |

---

## Chi tiết từng API

### 1. GET /api/v1/recurring-schedules

**Mô tả:** Lấy danh sách recurring schedules của clinic.

**Xác thực:** Bearer token + `shift.manage` permission

**Tham số Query:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Mặc định |
|---------|------|---------|-------|---------|
| `skip` | Integer | Không | Số bản ghi bỏ qua | 0 |
| `limit` | Integer | Không | Số bản ghi tối đa | 50 |

**Kết quả (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440200",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "user_id": "550e8400-e29b-41d4-a716-446655440010",
      "shift_template_id": "550e8400-e29b-41d4-a716-446655440000",
      "days_of_week": [1, 3, 5],
      "effective_from": "2026-05-01",
      "effective_to": "2026-12-31",
      "is_active": true,
      "created_at": "2026-04-28T10:00:00+00:00",
      "updated_at": "2026-04-28T10:00:00+00:00"
    }
  ],
  "total": 1
}
```

**Mã lỗi:**
- **401 Unauthorized**
- **403 Forbidden**

---

### 2. POST /api/v1/recurring-schedules

**Mô tả:** Tạo một recurring schedule mới (lịch làm việc lặp lại hàng tuần).

**Xác thực:** Bearer token + `shift.manage` permission

**Request Body:**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440010",
  "shift_template_id": "550e8400-e29b-41d4-a716-446655440000",
  "days_of_week": [1, 3, 5],
  "effective_from": "2026-05-01",
  "effective_to": "2026-12-31"
}
```

**Tham số:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Ràng buộc |
|---------|------|---------|-------|----------|
| `user_id` | UUID | Có | ID nhân viên | Phải tồn tại |
| `shift_template_id` | UUID | Có | ID shift template để lặp | Phải tồn tại |
| `days_of_week` | Array[Int] | Có | Danh sách ngày trong tuần | 1-7 (ISO: 1=Mon, 7=Sun) |
| `effective_from` | Date | Có | Ngày bắt đầu có hiệu lực | YYYY-MM-DD |
| `effective_to` | Date | Không | Ngày kết thúc có hiệu lực | Nếu null = vô thời hạn |

**Quy tắc nghiệp vụ:**
- `days_of_week` phải chứa giá trị trong 1-7 (BR-04)
- Nếu `effective_to` được cung cấp, phải >= `effective_from` (BR-03)

**Kết quả (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440200",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440010",
  "shift_template_id": "550e8400-e29b-41d4-a716-446655440000",
  "days_of_week": [1, 3, 5],
  "effective_from": "2026-05-01",
  "effective_to": "2026-12-31",
  "is_active": true,
  "created_at": "2026-04-28T10:00:00+00:00",
  "updated_at": "2026-04-28T10:00:00+00:00"
}
```

**Mã lỗi:**
- **400 Bad Request** — Quy tắc bị vi phạm
- **401 Unauthorized**
- **403 Forbidden**
- **404 Not Found** — User hoặc shift_template không tồn tại
- **422 Unprocessable Entity** — Lỗi validation (ví dụ: days_of_week chứa giá trị > 7)

---

### 3. PATCH /api/v1/recurring-schedules/{id}

**Mô tả:** Cập nhật một recurring schedule.

**Xác thực:** Bearer token + `shift.manage` permission

**Tham số Path:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `id` | UUID | ID của recurring schedule |

**Request Body (optional):**

```json
{
  "days_of_week": [1, 2, 3, 4, 5],
  "effective_to": "2026-11-30",
  "is_active": false
}
```

**Tham số:**

| Tham số | Kiểu | Mô tả | Ràng buộc |
|---------|------|-------|----------|
| `days_of_week` | Array[Int] | Ngày mới | 1-7 nếu có |
| `effective_from` | Date | Ngày bắt đầu mới | |
| `effective_to` | Date | Ngày kết thúc mới | >= effective_from nếu có |
| `is_active` | Boolean | Kích hoạt/vô hiệu hóa | |

**Kết quả (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440200",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440010",
  "shift_template_id": "550e8400-e29b-41d4-a716-446655440000",
  "days_of_week": [1, 2, 3, 4, 5],
  "effective_from": "2026-05-01",
  "effective_to": "2026-11-30",
  "is_active": false,
  "created_at": "2026-04-28T10:00:00+00:00",
  "updated_at": "2026-04-28T11:00:00+00:00"
}
```

**Mã lỗi:**
- **400 Bad Request** — Quy tắc bị vi phạm
- **401 Unauthorized**
- **403 Forbidden**
- **404 Not Found** — Recurring schedule không tồn tại
- **422 Unprocessable Entity** — Lỗi validation

---

### 4. DELETE /api/v1/recurring-schedules/{id}

**Mô tả:** Xóa mềm một recurring schedule.

**Xác thực:** Bearer token + `shift.manage` permission

**Tham số Path:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `id` | UUID | ID của recurring schedule |

**Kết quả (204 No Content):**

Không trả về body.

**Mã lỗi:**
- **401 Unauthorized**
- **403 Forbidden**
- **404 Not Found**

---

### 5. POST /api/v1/recurring-schedules/{id}/generate-shifts

**Mô tả:** Tạo Shifts từ recurring schedule cho đến ngày được chỉ định. API này là idempotent — chạy nhiều lần không tạo duplicates.

**Xác thực:** Bearer token + `shift.manage` permission

**Tham số Path:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `id` | UUID | ID của recurring schedule |

**Tham số Query:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Mặc định |
|---------|------|---------|-------|---------|
| `until` | Date | Có | Sinh shifts đến ngày này | — |

**Quy tắc xử lý:**

```
Duyệt từng ngày từ max(today, effective_from) đến until:
  Nếu ngày đó là một trong days_of_week:
    Nếu effective_to không null và ngày > effective_to:
      Bỏ qua (quá hạn hiệu lực)
    Nếu shift với (clinic_id, user_id, shift_date, start_time) chưa tồn tại:
      Tạo shift mới từ shift_template
    Nếu đã tồn tại:
      Bỏ qua (idempotency)
```

**Kết quả (200 OK):**

```json
{
  "created": 12
}
```

Trả về số shifts được tạo (không tính những shifts đã tồn tại).

**Mã lỗi:**
- **400 Bad Request** — `until` date sai format
- **401 Unauthorized**
- **403 Forbidden**
- **404 Not Found** — Recurring schedule không tồn tại
- **422 Unprocessable Entity** — Lỗi validation

---

## Background Cron Job

Ngoài API on-demand, hệ thống chạy cron job hàng ngày để tự động sinh shifts cho các recurring schedules:

```
Ngày hôm nay:
  Duyệt tất cả recurring schedules (is_active = true):
    Gọi generate_shifts_for_schedule(until=today + 30 days)
```

---

## Ghi chú

- **days_of_week format:** ISO 8601 — 1=Monday, 2=Tuesday, ..., 7=Sunday
- **Idempotency:** UNIQUE (clinic_id, user_id, shift_date, start_time) đảm bảo mỗi shift chỉ tồn tại một lần
- **Effective_to:** Nếu null, recurring schedule tồn tại vô thời hạn
- **is_active = false:** Recurring schedule vô hiệu hóa sẽ không sinh shifts mới (cron job kiểm tra)
