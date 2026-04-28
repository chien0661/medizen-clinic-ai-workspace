# API: Leave Requests

**Phiên bản:** 1.0  
**Ngày:** 2026-04-28  
**Task:** TASK-014

---

## Tổng quan

Leave Requests quản lý yêu cầu nghỉ phép của nhân viên. Bất kỳ nhân viên nào có thể nộp đơn xin nghỉ cho chính mình. Chỉ những người có quyền `leave.approve` (thường là manager/admin) mới có thể phê duyệt hoặc từ chối.

---

## Danh sách Endpoints

| Phương thức | Đường dẫn | Mô tả |
|------------|-----------|-------|
| GET | `/api/v1/leave-requests` | Lấy danh sách leave requests (requires `leave.approve`) |
| POST | `/api/v1/leave-requests` | Tạo leave request (bất kỳ authenticated user) |
| POST | `/api/v1/leave-requests/{id}/approve` | Phê duyệt leave (requires `leave.approve`) |
| POST | `/api/v1/leave-requests/{id}/reject` | Từ chối leave (requires `leave.approve`) |

---

## Chi tiết từng API

### 1. GET /api/v1/leave-requests

**Mô tả:** Lấy danh sách leave requests của clinic (chỉ manager/admin).

**Xác thực:** Bearer token + `leave.approve` permission

**Tham số Query:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Mặc định |
|---------|------|---------|-------|---------|
| `status` | String | Không | Lọc theo trạng thái | Không lọc |
| `user_id` | UUID | Không | Lọc theo nhân viên | Không lọc |
| `skip` | Integer | Không | Bỏ qua | 0 |
| `limit` | Integer | Không | Tối đa | 50 |

**Giá trị hợp lệ của `status`:**

| Giá trị | Mô tả |
|--------|-------|
| `pending` | Đang chờ phê duyệt |
| `approved` | Đã được phê duyệt |
| `rejected` | Bị từ chối |

**Truy vấn dữ liệu:**

```python
SELECT * FROM leave_request
WHERE clinic_id = :clinic_id
  AND NOT is_deleted
  AND (status = :status OR :status IS NULL)
  AND (user_id = :user_id OR :user_id IS NULL)
ORDER BY created_at DESC
LIMIT :limit OFFSET :skip
```

**Kết quả (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440300",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "user_id": "550e8400-e29b-41d4-a716-446655440010",
      "leave_type": "sick",
      "start_date": "2026-05-10",
      "end_date": "2026-05-12",
      "reason": "Bệnh sốt cao",
      "status": "pending",
      "approved_by": null,
      "approved_at": null,
      "rejection_reason": null,
      "created_at": "2026-04-28T09:00:00+00:00",
      "updated_at": "2026-04-28T09:00:00+00:00"
    }
  ],
  "total": 1
}
```

**Mã lỗi:**
- **401 Unauthorized**
- **403 Forbidden** — Không có quyền `leave.approve`

---

### 2. POST /api/v1/leave-requests

**Mô tả:** Tạo yêu cầu xin nghỉ phép. Nhân viên chỉ có thể xin nghỉ cho chính mình.

**Xác thực:** Bearer token (bất kỳ authenticated user nào có thể tạo)

**Request Body:**

```json
{
  "leave_type": "sick",
  "start_date": "2026-05-10",
  "end_date": "2026-05-12",
  "reason": "Bệnh sốt cao, cần điều trị"
}
```

**Tham số:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Ràng buộc |
|---------|------|---------|-------|----------|
| `leave_type` | String | Có | Loại nghỉ phép | sick / personal / vacation / other |
| `start_date` | Date | Có | Ngày bắt đầu | YYYY-MM-DD |
| `end_date` | Date | Có | Ngày kết thúc | YYYY-MM-DD, >= start_date |
| `reason` | String | Có | Lý do xin nghỉ | Min 1 ký tự (BR-14) |

**Quy tắc nghiệp vụ:**
- `end_date` phải >= `start_date` (BR-02)
- `reason` phải có ít nhất 1 ký tự (BR-14)

**Kết quả (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440300",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440010",
  "leave_type": "sick",
  "start_date": "2026-05-10",
  "end_date": "2026-05-12",
  "reason": "Bệnh sốt cao, cần điều trị",
  "status": "pending",
  "approved_by": null,
  "approved_at": null,
  "rejection_reason": null,
  "created_at": "2026-04-28T09:00:00+00:00",
  "updated_at": "2026-04-28T09:00:00+00:00"
}
```

**Mã lỗi:**
- **400 Bad Request** — Quy tắc bị vi phạm
- **401 Unauthorized** — Chưa xác thực
- **422 Unprocessable Entity** — Lỗi validation

---

### 3. POST /api/v1/leave-requests/{id}/approve

**Mô tả:** Phê duyệt yêu cầu xin nghỉ phép. Khi approved, tất cả shifts trong khoảng thời gian sẽ được đánh dấu `on_leave`.

**Xác thực:** Bearer token + `leave.approve` permission

**Tham số Path:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `id` | UUID | ID của leave request |

**Request Body:** Không có body

**Quy tắc nghiệp vụ:**
- Người phê duyệt không được là chính người xin nghỉ (BR-07)
- Leave request phải ở trạng thái `pending` (BR-08)
- Khi phê duyệt, hệ thống sẽ tự động mark các shifts trong khoảng `start_date` đến `end_date` với status = `on_leave` (BR-06)

**Kết quả (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440300",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440010",
  "leave_type": "sick",
  "start_date": "2026-05-10",
  "end_date": "2026-05-12",
  "reason": "Bệnh sốt cao, cần điều trị",
  "status": "approved",
  "approved_by": "550e8400-e29b-41d4-a716-446655440020",
  "approved_at": "2026-04-28T10:00:00+00:00",
  "rejection_reason": null,
  "created_at": "2026-04-28T09:00:00+00:00",
  "updated_at": "2026-04-28T10:00:00+00:00"
}
```

**Mã lỗi:**
- **400 Bad Request** — Quy tắc bị vi phạm (ví dụ: self-approval, already finalized)
- **401 Unauthorized**
- **403 Forbidden** — Không có quyền `leave.approve` hoặc thuộc clinic khác
- **404 Not Found** — Leave request không tồn tại
- **422 Unprocessable Entity** — Lỗi validation

---

### 4. POST /api/v1/leave-requests/{id}/reject

**Mô tả:** Từ chối yêu cầu xin nghỉ phép.

**Xác thực:** Bearer token + `leave.approve` permission

**Tham số Path:**

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `id` | UUID | ID của leave request |

**Request Body:**

```json
{
  "rejection_reason": "Quá nhiều nhân viên nghỉ cùng thời gian"
}
```

**Tham số:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Ràng buộc |
|---------|------|---------|-------|----------|
| `rejection_reason` | String | Không | Lý do từ chối | |

**Quy tắc nghiệp vụ:**
- Leave request phải ở trạng thái `pending` (BR-08)
- Khi reject, shifts **không** bị thay đổi (BR-05) — chỉ status leave request → rejected

**Kết quả (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440300",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440010",
  "leave_type": "sick",
  "start_date": "2026-05-10",
  "end_date": "2026-05-12",
  "reason": "Bệnh sốt cao, cần điều trị",
  "status": "rejected",
  "approved_by": "550e8400-e29b-41d4-a716-446655440020",
  "approved_at": "2026-04-28T10:05:00+00:00",
  "rejection_reason": "Quá nhiều nhân viên nghỉ cùng thời gian",
  "created_at": "2026-04-28T09:00:00+00:00",
  "updated_at": "2026-04-28T10:05:00+00:00"
}
```

**Mã lỗi:**
- **400 Bad Request** — Quy tắc bị vi phạm (already finalized)
- **401 Unauthorized**
- **403 Forbidden** — Không có quyền hoặc thuộc clinic khác
- **404 Not Found** — Leave request không tồn tại
- **422 Unprocessable Entity** — Lỗi validation

---

## Định dạng lỗi chung

```json
{
  "detail": "Mô tả lỗi chi tiết"
}
```

---

## Ghi chú

- **Leave Types:** sick (bệnh), personal (cá nhân), vacation (kỳ nghỉ), other (khác)
- **Status Flow:** pending → (approved hoặc rejected)
- **Shift Cascade:** Khi approve, tất cả shifts trong khoảng `start_date` đến `end_date` được mark `on_leave`. Khi reject, shifts không thay đổi.
- **Tenant Isolation:** Người phê duyệt phải thuộc cùng clinic với leave request.
