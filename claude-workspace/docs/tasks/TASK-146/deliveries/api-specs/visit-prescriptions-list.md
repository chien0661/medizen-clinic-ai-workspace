# API Spec: GET /api/v1/visits/{visit_id}/prescriptions

**Endpoint:** `GET /api/v1/visits/{visit_id}/prescriptions`  
**Task:** TASK-146  
**Version:** 1.0  
**Date:** 2026-09-01

---

## Overview

Lấy **tất cả** đơn thuốc của một lượt khám, bao gồm cả những đơn đã hủy và đơn nháp. Dùng để hiển thị lịch sử đầy đủ.

**Lưu ý quan trọng:** Có một endpoint tương tự khác `GET /visits/{visit_id}/prescription` (singular, trả 1 đơn) được dùng bởi màn khám của bác sĩ để chỉnh sửa. Hai endpoint này **phục vụ mục đích khác nhau** và **KHÔNG ĐƯỢC NHẦM LẪN**.

| Endpoint | Mục đích | Trả về | Lọc |
|----------|---------|--------|-----|
| `GET .../prescriptions` (plural) | Lịch sử đơn thuốc | Tất cả đơn (gồm hủy) | Không lọc status |
| `GET .../prescription` (singular) | Màn khám bác sĩ | Đơn mới nhất còn hiệu lực | Lọc `status != 'cancelled'`, trả 1 |

## Authentication

**Required:** Yes  
**Method:** Bearer Token (JWT)  
**Header:** `Authorization: Bearer <jwt_token>`

## Request

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `visit_id` | UUID | Yes | ID lượt khám |

### Example Request

```http
GET /api/v1/visits/a1b2c3d4-e5f6-7890-abcd-ef1234567890/prescriptions
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Response

### Success (HTTP 200)

```json
{
  "items": [
    {
      "id": "rx-001",
      "visit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "cancelled",
      "prescribed_at": "2026-09-01T10:00:00Z",
      "cancelled_at": "2026-09-01T10:15:00Z",
      "cancel_reason": "Kê sai loại thuốc, thay đơn mới",
      "created_by": "dr-001",
      "updated_by": "dr-001",
      "line_items": [
        {
          "id": "rxl-001",
          "medicine_id": "med-001",
          "medicine_name": "Paracetamol 500mg",
          "quantity": 10,
          "dosage": "1 viên x 3 lần/ngày",
          "note": null
        }
      ]
    },
    {
      "id": "rx-002",
      "visit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "draft",
      "prescribed_at": "2026-09-01T10:20:00Z",
      "cancelled_at": null,
      "cancel_reason": null,
      "created_by": "dr-001",
      "updated_by": "dr-001",
      "line_items": [
        {
          "id": "rxl-002",
          "medicine_id": "med-002",
          "medicine_name": "Ibuprofen 200mg",
          "quantity": 20,
          "dosage": "1 viên x 2 lần/ngày",
          "note": "Sau ăn"
        }
      ]
    },
    {
      "id": "rx-003",
      "visit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "pending",
      "prescribed_at": "2026-09-01T10:25:00Z",
      "cancelled_at": null,
      "cancel_reason": null,
      "created_by": "dr-001",
      "updated_by": "dr-001",
      "line_items": [
        {
          "id": "rxl-003",
          "medicine_id": "med-003",
          "medicine_name": "Cephalexin 500mg",
          "quantity": 15,
          "dosage": "1 viên x 4 lần/ngày",
          "note": null
        }
      ]
    }
  ],
  "total": 3,
  "visit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `items` | Array | Danh sách đơn thuốc của lượt khám |
| `items[].id` | UUID | Mã đơn thuốc |
| `items[].visit_id` | UUID | ID lượt khám |
| `items[].status` | String | Trạng thái: `draft`, `pending`, `dispensed`, `cancelled` |
| `items[].prescribed_at` | DateTime | Thời điểm kê đơn |
| `items[].cancelled_at` | DateTime \| null | Thời điểm hủy (null nếu chưa hủy) |
| `items[].cancel_reason` | String \| null | Lý do hủy (null nếu chưa hủy) |
| `items[].created_by` | UUID | ID bác sĩ kê đơn |
| `items[].updated_by` | UUID | ID người cập nhật cuối (người hủy nếu cancelled) |
| `items[].line_items` | Array | Danh sách thuốc trong đơn |
| `items[].line_items[].id` | UUID | Mã thuốc trong đơn |
| `items[].line_items[].medicine_name` | String | Tên thuốc |
| `items[].line_items[].quantity` | Integer | Số lượng |
| `items[].line_items[].dosage` | String | Liều dùng |
| `total` | Integer | Tổng số đơn của lượt khám (không phân trang) |
| `visit_id` | UUID | ID lượt khám |

## Prescription Status

| Status | Ý nghĩa |
|--------|---------|
| `draft` | Đơn nháp, bác sĩ chưa gửi cho nhà thuốc |
| `pending` | Đơn chờ cấp phát tại nhà thuốc |
| `dispensed` | Nhà thuốc đã cấp phát |
| `cancelled` | Đơn bị hủy (nhà thuốc hoặc bác sĩ hủy trước khi cấp) |

## Frontend Filtering (D-1 Decision)

**Backend trả về tất cả status (draft, pending, dispensed, cancelled).**

**Frontend phải lọc bỏ `draft` khi hiển thị lịch sử:**

```typescript
// Pseudocode
const historyPrescriptions = items.filter(p => p.status !== 'draft');
```

**Lý do:**
- `draft` là đơn chưa bao giờ gửi cho bệnh nhân, chỉ là bản nháp
- Nó không phản ánh sự kiện lâm sàng thực sự xảy ra
- Hiển thị sẽ gây nhiễu cho bác sĩ khi truy vét lịch sử

## Error Responses

### 404 Not Found

```json
{
  "error": {
    "code": "VISIT_NOT_FOUND",
    "message": "Lượt khám không tìm thấy",
    "details": { "visit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890" }
  },
  "meta": { "request_id": "req-201" }
}
```

### 403 Forbidden

```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Không có quyền truy cập lượt khám này",
    "details": {}
  },
  "meta": { "request_id": "req-202" }
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
  "meta": { "request_id": "req-203" }
}
```

## Ordering

- Các đơn được sắp xếp theo `prescribed_at` (cũ → mới)
- Nếu cùng thời điểm, sắp xếp theo `created_at`

## Notes

- **Không hỗ trợ phân trang** — endpoint này trả về tất cả đơn của lượt khám
- **Ngôn ngữ thị giác:** Frontend hiển thị đơn `cancelled` với `line-through` + `opacity-50` trên các ô "Số đơn / Ngày kê / Số loại", nhưng **KHÔNG** áp dụng lên "Lý do hủy" để lý do vẫn đọc được rõ ràng
- **Âu actor:** `updated_by` là người hủy. Hiển thị tên người hủy cần thêm lookup `/users` (dành cho task follow-up)
- **Bác sĩ chỉnh sửa:** Màn khám của bác sĩ (PrescriptionTab.tsx) dùng endpoint khác `getVisitPrescription` (singular), **KHÔNG** dùng endpoint này
