# API Spec: GET /api/v1/invoices

**Endpoint:** `GET /api/v1/invoices`  
**Task:** TASK-146  
**Version:** 1.0  
**Date:** 2026-09-01

---

## Overview

Lấy danh sách hóa đơn của bệnh nhân, bao gồm cả những hóa đơn đã hủy/hoàn tiền. Hỗ trợ phân trang offset-based.

**FIX-2 (TASK-146):** Từ trước, tham số `patient_id` bị bỏ qua → tab hiển thị hóa đơn của **toàn clinic**. Đã sửa để lọc đúng theo bệnh nhân.

## Authentication

**Required:** Yes  
**Method:** Bearer Token (JWT)  
**Header:** `Authorization: Bearer <jwt_token>`

## Request

### Query Parameters

| Parameter | Type | Required | Default | Max | Description |
|-----------|------|----------|---------|-----|-------------|
| `patient_id` | UUID | Yes | — | — | ID bệnh nhân (FIX-2: giờ được áp dụng) |
| `limit` | Integer | No | 50 | 200 | Số bản ghi mỗi trang |
| `offset` | Integer | No | 0 | — | Số bản ghi bỏ qua từ đầu |

### Example Request

```http
GET /api/v1/invoices?patient_id=550e8400-e29b-41d4-a716-446655440000&limit=50&offset=0
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Response

### Success (HTTP 200)

```json
{
  "items": [
    {
      "id": "inv-001",
      "invoice_number": "INV-20260901-001",
      "visit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "grand_total": 500000,
      "paid_total": 500000,
      "status": "paid",
      "voided_at": null,
      "void_reason": null,
      "refunded_at": null,
      "refund_reason": null,
      "created_at": "2026-09-01T10:00:00Z",
      "updated_at": "2026-09-01T10:05:00Z"
    },
    {
      "id": "inv-002",
      "invoice_number": "INV-20260901-002",
      "visit_id": "b2c3d4e5-f6f7-8901-bcde-f12345678901",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "grand_total": 750000,
      "paid_total": 0,
      "status": "voided",
      "voided_at": "2026-09-01T11:00:00Z",
      "void_reason": "Phát hành nhầm — sẽ phát hành lại",
      "refunded_at": null,
      "refund_reason": null,
      "created_at": "2026-09-01T10:30:00Z",
      "updated_at": "2026-09-01T11:00:00Z"
    },
    {
      "id": "inv-003",
      "invoice_number": "INV-20260901-003",
      "visit_id": "b2c3d4e5-f6f7-8901-bcde-f12345678901",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "grand_total": 750000,
      "paid_total": 750000,
      "status": "refunded",
      "voided_at": null,
      "void_reason": null,
      "refunded_at": "2026-09-01T12:00:00Z",
      "refund_reason": "Khách yêu cầu trả lại",
      "created_at": "2026-09-01T10:45:00Z",
      "updated_at": "2026-09-01T12:00:00Z"
    },
    {
      "id": "inv-004",
      "invoice_number": "INV-20260901-004",
      "visit_id": "c3d4e5f6-f7f8-9012-cdef-123456789012",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "grand_total": 300000,
      "paid_total": 0,
      "status": "issued",
      "voided_at": null,
      "void_reason": null,
      "refunded_at": null,
      "refund_reason": null,
      "created_at": "2026-09-01T14:00:00Z",
      "updated_at": "2026-09-01T14:00:00Z"
    }
  ],
  "total": 4,
  "limit": 50,
  "offset": 0
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | Array | Danh sách hóa đơn |
| `items[].id` | UUID | Mã hóa đơn |
| `items[].invoice_number` | String | Số hiệu hóa đơn (INV-YYYYMMDD-NNN) |
| `items[].visit_id` | UUID | ID lượt khám liên quan |
| `items[].patient_id` | UUID | ID bệnh nhân |
| `items[].grand_total` | Integer | Tổng tiền hóa đơn (VND) |
| `items[].paid_total` | Integer | Tiền đã thanh toán (VND) |
| `items[].status` | String | Trạng thái hóa đơn |
| `items[].voided_at` | DateTime \| null | **NEW:** Thời điểm hủy hóa đơn |
| `items[].void_reason` | String \| null | **NEW:** Lý do hủy |
| `items[].refunded_at` | DateTime \| null | **NEW:** Thời điểm hoàn tiền |
| `items[].refund_reason` | String \| null | **NEW:** Lý do hoàn tiền |
| `items[].created_at` | DateTime | Thời điểm tạo |
| `items[].updated_at` | DateTime | Thời điểm cập nhật cuối |
| `total` | Integer | Tổng số hóa đơn của bệnh nhân (không phân trang) |
| `limit` | Integer | Kích thước trang được yêu cầu |
| `offset` | Integer | Số bản ghi bỏ qua |

## Invoice Status

| Status | Ý nghĩa |
|--------|---------|
| `draft` | Nháp, chưa phát hành |
| `issued` | Đã phát hành, chờ thanh toán |
| `paid` | Đã thanh toán đầy đủ |
| `voided` | Đã hủy (hóa đơn không hợp lệ) |
| `refunded` | Đã hoàn tiền (khách đổi ý hoặc trả lại) |

## New Fields (FIX-F2)

**Từ trước:** `InvoiceSummaryResponse` thiếu thông tin về lý do hủy/hoàn tiền

**Từ nay:** Bổ sung 4 trường:
- `voided_at` — thời điểm hủy
- `void_reason` — lý do hủy
- `refunded_at` — thời điểm hoàn tiền
- `refund_reason` — lý do hoàn tiền

## Pagination Logic

- **Page 1:** `offset=0, limit=50` → nhận items [0-49]
- **Page 2:** `offset=50, limit=50` → nhận items [50-99]
- **Termination:** Khi `offset + items.length >= total`, không có thêm dữ liệu
- **Next offset calculation:** `new_offset = previous_offset + items.length`

## Error Responses

### 400 Bad Request

```json
{
  "error": {
    "code": "INVALID_PATIENT_ID",
    "message": "Patient ID không phải UUID hợp lệ",
    "details": { "patient_id": "invalid-uuid" }
  },
  "meta": { "request_id": "req-301" }
}
```

### 422 Unprocessable Entity

```json
{
  "error": {
    "code": "INVALID_UUID",
    "message": "patient_id không hợp lệ",
    "details": {}
  },
  "meta": { "request_id": "req-302" }
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
  "meta": { "request_id": "req-303" }
}
```

### 403 Forbidden

```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Không có quyền truy cập hóa đơn của bệnh nhân này",
    "details": {}
  },
  "meta": { "request_id": "req-304" }
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
  "meta": { "request_id": "req-305" }
}
```

## Changes from Previous Version

| Item | Trước | Sau | Ghi chú |
|------|--------|-----|---------|
| `patient_id` filter | Bị bỏ qua (FIX-2) | Áp dụng (lọc đúng bệnh nhân) | Tab Hóa đơn giờ chỉ hiển thị hóa đơn của bệnh nhân này, không phải toàn clinic |
| `voided_at` field | Không có | Có (NEW) | FIX-F2 |
| `void_reason` field | Không có | Có (NEW) | FIX-F2 |
| `refunded_at` field | Không có | Có (NEW) | FIX-F2 |
| `refund_reason` field | Không có | Có (NEW) | FIX-F2 |

## Notes

- **Multi-tenancy:** Tất cả dữ liệu được lọc theo `clinic_id` từ JWT
- **Permission checking:** Người dùng chỉ có thể xem hóa đơn của bệnh nhân thuộc phòng khám của mình
- **Ordering:** Hóa đơn được sắp xếp theo `created_at` (mới → cũ)
- **Ngôn ngữ thị giác:** Frontend hiển thị hóa đơn `voided`/`refunded` với `line-through` + `opacity-50` trên các ô "Số hoá đơn / Ngày / Tổng tiền", nhưng **KHÔNG** áp dụng lên "Lý do hủy/hoàn tiền" để lý do vẫn đọc được rõ ràng
