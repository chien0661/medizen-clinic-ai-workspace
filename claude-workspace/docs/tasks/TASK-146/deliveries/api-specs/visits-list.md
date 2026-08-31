# API Spec: GET /api/v1/visits

**Endpoint:** `GET /api/v1/visits`  
**Task:** TASK-146  
**Version:** 1.0  
**Date:** 2026-09-01

---

## Overview

Lấy danh sách lượt khám của bệnh nhân, hỗ trợ phân trang offset-based.

## Authentication

**Required:** Yes  
**Method:** Bearer Token (JWT)  
**Header:** `Authorization: Bearer <jwt_token>`

## Request

### Query Parameters

| Parameter | Type | Required | Default | Max | Description |
|-----------|------|----------|---------|-----|-------------|
| `patient_id` | UUID | Yes | — | — | ID bệnh nhân |
| `limit` | Integer | No | 50 | 500 | Số bản ghi mỗi trang |
| `skip` | Integer | No | 0 | — | Số bản ghi bỏ qua từ đầu |

### Example Request

```http
GET /api/v1/visits?patient_id=550e8400-e29b-41d4-a716-446655440000&limit=50&skip=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Response

### Success (HTTP 200)

```json
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "visit_number": "20260901-001",
      "visit_date": "2026-09-01",
      "status": "completed",
      "doctor_id": "f1f2f3f4-f5f6-f7f8-f9fa-fbfcfdfe0001",
      "assigned_doctor_id": "f1f2f3f4-f5f6-f7f8-f9fa-fbfcfdfe0002",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "patient_name": "Nguyễn Văn A",
      "patient_code": "BN001",
      "patient_date_of_birth": "1990-05-15",
      "patient_gender": "Male",
      "chief_complaint": "Đau đầu",
      "diagnosis": "Đau đầu căng thẳng",
      "notes": "Dùng thuốc hạ sốt",
      "created_at": "2026-09-01T08:00:00Z",
      "updated_at": "2026-09-01T08:30:00Z"
    },
    {
      "id": "b2c3d4e5-f6f7-8901-bcde-f12345678901",
      "visit_number": "20260901-002",
      "visit_date": "2026-09-01",
      "status": "completed",
      "doctor_id": null,
      "assigned_doctor_id": "f1f2f3f4-f5f6-f7f8-f9fa-fbfcfdfe0001",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "patient_name": "Nguyễn Văn A",
      "patient_code": "BN001",
      "patient_date_of_birth": "1990-05-15",
      "patient_gender": "Male",
      "chief_complaint": "Tái khám",
      "diagnosis": "Theo dõi",
      "notes": null,
      "created_at": "2026-09-01T09:30:00Z",
      "updated_at": "2026-09-01T10:00:00Z"
    }
  ],
  "total": 25,
  "limit": 50,
  "skip": 0
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | Array | Danh sách lượt khám |
| `items[].id` | UUID | Mã lượt khám |
| `items[].visit_number` | String | Số hiệu lượt khám (YYYYMMDD-NNN) |
| `items[].visit_date` | Date | Ngày khám (YYYY-MM-DD) |
| `items[].status` | String | Trạng thái lượt khám |
| `items[].doctor_id` | UUID \| null | ID bác sĩ khám (nếu có) |
| `items[].assigned_doctor_id` | UUID \| null | ID bác sĩ được giao |
| `items[].patient_id` | UUID | ID bệnh nhân |
| `items[].created_at` | DateTime | Thời điểm tạo |
| `items[].updated_at` | DateTime | Thời điểm cập nhật cuối |
| `total` | Integer | Tổng số lượt khám của bệnh nhân |
| `limit` | Integer | Kích thước trang được yêu cầu |
| `skip` | Integer | Số bản ghi bỏ qua |

## Error Responses

### 400 Bad Request

```json
{
  "error": {
    "code": "INVALID_PATIENT_ID",
    "message": "Patient ID không phải UUID hợp lệ",
    "details": { "patient_id": "invalid-uuid" }
  },
  "meta": { "request_id": "req-123" }
}
```

### 404 Not Found

```json
{
  "error": {
    "code": "PATIENT_NOT_FOUND",
    "message": "Bệnh nhân không tìm thấy",
    "details": { "patient_id": "550e8400-e29b-41d4-a716-446655440000" }
  },
  "meta": { "request_id": "req-124" }
}
```

### 403 Forbidden

```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Không có quyền truy cập hồ sơ bệnh nhân này",
    "details": {}
  },
  "meta": { "request_id": "req-125" }
}
```

### 500 Internal Server Error

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "Đã xảy ra lỗi không mong muốn",
    "details": {}
  },
  "meta": { "request_id": "req-126" }
}
```

## Pagination Logic

- **Page 1:** `skip=0, limit=50` → nhận items [0-49]
- **Page 2:** `skip=50, limit=50` → nhận items [50-99]
- **Termination:** Khi `skip + items.length >= total`, không có thêm dữ liệu
- **Next offset calculation:** `new_offset = sum(previous_pages_item_counts)`

## Notes

- Tất cả dữ liệu được lọc theo `clinic_id` từ JWT (multi-tenancy)
- Người dùng chỉ có thể xem bệnh nhân thuộc phòng khám của mình
- API không hỗ trợ lọc theo `status` cho endpoint này
