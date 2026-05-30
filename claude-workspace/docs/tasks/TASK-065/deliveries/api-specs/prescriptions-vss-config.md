# API Specifications — TASK-065: GET /visits/{id}/prescriptions + VSS Config

**Task**: TASK-065 — Fix BUG-003 (GET /visits/{id}/prescriptions → 405) + BE VSS config endpoint  
**Date**: 2026-05-31  
**Status**: DOCUMENTING  
**Base Path**: `/api/v1`  

---

## Tổng quan

Task này fix 2 gap API:

1. **BUG-003 fix**: Thêm endpoint `GET /api/v1/visits/{visit_id}/prescriptions` — liệt kê các đơn thuốc của một visit (FE dùng để hiển thị tab Kê đơn trong EMR)
2. **VSS config endpoints**: Thêm `GET/PUT /api/v1/integrations/vss/config` — đọc/lưu cấu hình tích hợp VSS của clinic hiện tại

---

## Danh sách API

**Yêu cầu xác thực chung:**
```
Authorization: Bearer {token}
X-Clinic-Id: {clinic_uuid}  (header, bắt buộc cho các API)
```

| STT | Phương thức | Đường dẫn | Mô tả | Permission |
|-----|------------|-----------|-------|-----------|
| 1 | GET | `/visits/{visit_id}/prescriptions` | Liệt kê đơn thuốc của visit | `prescription.read` |
| 2 | GET | `/integrations/vss/config` | Đọc config VSS | `vss:read` |
| 3 | PUT | `/integrations/vss/config` | Cập nhật config VSS | `vss:sync` |

---

## 1. GET /api/v1/visits/{visit_id}/prescriptions (BUG-003 fix)

### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/visits/{visit_id}/prescriptions` |
| **Mô tả** | Liệt kê toàn bộ đơn thuốc không bị xoá của một visit. Được sắp xếp theo `prescribed_at` tăng dần. |
| **Xác thực** | Bắt buộc; permission `prescription.read` |
| **Feature flag** | `bhyt` (không bắt buộc; không khai báo trong route) |
| **Tenant isolation** | Clinic RLS: chỉ trả về prescriptions của clinic_id trong header |

### Tham số đầu vào

| Tham số | Loại | Vị trí | Bắt buộc | Mô tả | Ghi chú |
|--------|------|--------|---------|-------|--------|
| `visit_id` | UUID | Path | Có | ID của visit | Phải là UUID hợp lệ (v4 format); nếu không → 422 |
| `X-Clinic-Id` | UUID | Header | Có | ID clinic hiện tại | Được trích từ JWT token; nếu không có → 400 |

### Quy trình xử lý

| Bước | Mô tả | Lỗi có thể xảy ra |
|------|-------|------------------|
| 1 | Kiểm tra token xác thực | 401 UNAUTHORIZED (hết hạn hoặc không hợp lệ) |
| 2 | Kiểm tra permission `prescription.read` | 403 FORBIDDEN (user không có quyền) |
| 3 | Kiểm tra header `X-Clinic-Id` | 400 BAD_REQUEST (missing) |
| 4 | Validate UUID `visit_id` | 422 UNPROCESSABLE_ENTITY (invalid UUID) |
| 5 | Truy vấn prescriptions: `SELECT * FROM prescriptions WHERE visit_id = ? AND clinic_id = ? AND is_deleted = false ORDER BY prescribed_at ASC` | — |
| 6 | Ánh xạ mỗi row sang `PrescriptionResponse` | — |
| 7 | Trả kết quả dạng `PrescriptionListResponse` | — |

**Truy vấn SQL:**

```sql
SELECT p.*
FROM prescriptions p
WHERE p.visit_id = :visit_id
  AND p.clinic_id = :clinic_id
  AND p.is_deleted = false
ORDER BY p.prescribed_at ASC;
```

### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "visit_id": "550e8400-e29b-41d4-a716-446655440111",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440222",
      "patient_id": "550e8400-e29b-41d4-a716-446655440333",
      "doctor_id": "550e8400-e29b-41d4-a716-446655440444",
      "prescribed_at": "2026-05-31T10:30:00Z",
      "reason": "Cảm cúm",
      "total_cost": 250000,
      "vss_submitted": false,
      "vss_claim_id": null,
      "notes": "Dùng 3 lần mỗi ngày",
      "is_deleted": false,
      "created_at": "2026-05-31T10:30:00Z",
      "updated_at": "2026-05-31T10:30:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "visit_id": "550e8400-e29b-41d4-a716-446655440111",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440222",
      "patient_id": "550e8400-e29b-41d4-a716-446655440333",
      "doctor_id": "550e8400-e29b-41d4-a716-446655440444",
      "prescribed_at": "2026-05-31T11:15:00Z",
      "reason": "Đau đầu",
      "total_cost": 120000,
      "vss_submitted": false,
      "vss_claim_id": null,
      "notes": null,
      "is_deleted": false,
      "created_at": "2026-05-31T11:15:00Z",
      "updated_at": "2026-05-31T11:15:00Z"
    }
  ],
  "total": 2,
  "visit_id": "550e8400-e29b-41d4-a716-446655440111"
}
```

**Mô tả các trường:**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `items` | Array[PrescriptionResponse] | Danh sách đơn thuốc của visit |
| `total` | Integer | Tổng số đơn (bằng độ dài `items`) |
| `visit_id` | UUID | ID visit để xác nhận yêu cầu |

**PrescriptionResponse (fields chính):**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `id` | UUID | ID đơn thuốc |
| `visit_id` | UUID | ID visit |
| `clinic_id` | UUID | ID clinic |
| `prescribed_at` | DateTime (ISO 8601) | Thời gian kê đơn |
| `reason` | String | Lý do kê đơn |
| `total_cost` | Integer | Tổng chi phí (đơn vị: VND) |
| `vss_submitted` | Boolean | Đã submit lên VSS chưa |
| `vss_claim_id` | String \| null | ID claim trên VSS (nếu đã submit) |
| `notes` | String \| null | Ghi chú bác sĩ |
| `is_deleted` | Boolean | Đã xoá chưa (luôn false trong response) |
| `created_at` | DateTime | Ngày tạo |
| `updated_at` | DateTime | Ngày cập nhật cuối |

---

### Mã lỗi

| HTTP | Mã lỗi | Tình huống | Thông báo |
|------|--------|-----------|----------|
| 400 | BAD_REQUEST | Header `X-Clinic-Id` không được cung cấp | `"Missing clinic ID in request headers"` |
| 401 | UNAUTHORIZED | Token không hợp lệ hoặc hết hạn | `"Invalid or expired authentication token"` |
| 403 | FORBIDDEN | User không có permission `prescription.read` | `"Insufficient permissions: prescription.read required"` |
| 422 | UNPROCESSABLE_ENTITY | `visit_id` không phải UUID hợp lệ | `"Invalid UUID format for visit_id"` |
| 500 | INTERNAL_ERROR | Lỗi database hoặc hệ thống | `"Internal server error, please try again later"` |

**Định dạng phản hồi lỗi:**

```json
{
  "code": "BAD_REQUEST",
  "message": "Missing clinic ID in request headers"
}
```

---

## 2. GET /api/v1/integrations/vss/config

### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/integrations/vss/config` |
| **Mô tả** | Đọc cấu hình tích hợp VSS của clinic hiện tại. Config được lưu trong clinic_settings.settings['vss'] JSONB blob. Nếu chưa cấu hình, trả về mặc định (empty strings, enabled=false). |
| **Xác thực** | Bắt buộc; permission `vss:read` |
| **Feature flag** | `bhyt` (không bắt buộc) |
| **Tenant isolation** | Clinic RLS: chỉ trả về config của clinic_id trong header |

### Tham số đầu vào

| Tham số | Loại | Vị trí | Bắt buộc | Mô tả |
|--------|------|--------|---------|-------|
| `X-Clinic-Id` | UUID | Header | Có | ID clinic hiện tại |

### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra token xác thực |
| 2 | Kiểm tra permission `vss:read` |
| 3 | Kiểm tra header `X-Clinic-Id` |
| 4 | Truy vấn `clinic_settings` table: `SELECT settings FROM clinic_settings WHERE clinic_id = ?` |
| 5 | Trích key `vss` từ settings JSONB; merge với defaults |
| 6 | Trả `VssConfigResponse` |

**Truy vấn SQL:**

```sql
SELECT settings
FROM clinic_settings
WHERE clinic_id = :clinic_id;
-- Rồi lấy settings['vss'] (JSONB path)
-- Merge với defaults: { "api_url": "", "api_key": "", "facility_code": "", "enabled": false }
```

### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "api_url": "https://vss.gov.vn/api",
  "api_key": "sk_test_XXXXXXXXXXXXXX",
  "facility_code": "KCB123",
  "enabled": true
}
```

hoặc (chưa cấu hình):

```json
{
  "api_url": "",
  "api_key": "",
  "facility_code": "",
  "enabled": false
}
```

**Mô tả các trường:**

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `api_url` | String | Base URL của VSS API |
| `api_key` | String | API key để xác thực với VSS (có thể được mặt nạ/hash khi trả về; mặc định trả về plaintext nếu user có `vss:read`) |
| `facility_code` | String | Mã cơ sở KCB để xác định cơ sở y tế trong VSS |
| `enabled` | Boolean | Có bật tích hợp VSS không |

### Mã lỗi

| HTTP | Mã lỗi | Tình huống | Thông báo |
|------|--------|-----------|----------|
| 400 | BAD_REQUEST | Header `X-Clinic-Id` không có | `"Missing clinic ID in request headers"` |
| 401 | UNAUTHORIZED | Token không hợp lệ | `"Invalid or expired authentication token"` |
| 403 | FORBIDDEN | User không có permission `vss:read` | `"Insufficient permissions: vss:read required"` |
| 500 | INTERNAL_ERROR | Lỗi database | `"Internal server error, please try again later"` |

---

## 3. PUT /api/v1/integrations/vss/config

### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `PUT /api/v1/integrations/vss/config` |
| **Mô tả** | Cập nhật cấu hình VSS của clinic hiện tại. Hỗ trợ partial update (chỉ cần gửi các trường cần thay đổi). Config được lưu dưới key `vss` trong clinic_settings.settings JSONB blob. |
| **Xác thực** | Bắt buộc; permission `vss:sync` |
| **Feature flag** | `bhyt` (không bắt buộc) |
| **Tenant isolation** | Clinic RLS: chỉ cập nhật config của clinic_id trong header |

### Tham số đầu vào

**Request body (JSON):**

```json
{
  "api_url": "https://vss.gov.vn/api",
  "api_key": "sk_test_XXXXXXXXXXXXXX",
  "facility_code": "KCB123",
  "enabled": true
}
```

**Mô tả các trường:**

| Tham số | Kiểu | Bắt buộc | Mô tả | Ghi chú |
|--------|------|---------|-------|--------|
| `api_url` | String | Không | Base URL VSS API | Nếu không gửi → giữ giá trị cũ |
| `api_key` | String | Không | API key VSS | Nếu không gửi → giữ giá trị cũ |
| `facility_code` | String | Không | Mã cơ sở KCB | Nếu không gửi → giữ giá trị cũ |
| `enabled` | Boolean | Không | Bật/tắt VSS | Nếu không gửi → giữ giá trị cũ |

**Ví dụ partial update (chỉ thay đổi enabled):**

```json
{
  "enabled": false
}
```

### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra token xác thực |
| 2 | Kiểm tra permission `vss:sync` |
| 3 | Kiểm tra header `X-Clinic-Id` |
| 4 | Validate request body (nếu có lỗi format JSON → 400) |
| 5 | Truy vấn config hiện tại từ clinic_settings |
| 6 | Deep merge: `updated_config = {**current, **{k: v for k, v in patch if v is not None}}` |
| 7 | Cập nhật `clinic_settings.settings['vss'] = updated_config` |
| 8 | Ghi audit log (gọi `settings_service.update_settings(..., user_id=user_id)`) |
| 9 | Commit transaction; trả `VssConfigResponse` |

**Truy vấn SQL:**

```sql
-- Lấy config hiện tại
SELECT settings FROM clinic_settings
WHERE clinic_id = :clinic_id;

-- Sau khi merge locally, update:
UPDATE clinic_settings
SET settings = jsonb_set(settings, '{vss}', :updated_vss_json)
WHERE clinic_id = :clinic_id;
```

### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "api_url": "https://vss.gov.vn/api",
  "api_key": "sk_test_XXXXXXXXXXXXXX",
  "facility_code": "KCB123",
  "enabled": true
}
```

Trả về config **sau khi update** (full config, không phải chỉ fields được cập nhật).

### Mã lỗi

| HTTP | Mã lỗi | Tình huống | Thông báo |
|------|--------|-----------|----------|
| 400 | BAD_REQUEST | Header `X-Clinic-Id` không có; hoặc request body JSON không hợp lệ | `"Missing clinic ID in request headers"` or `"Invalid JSON format"` |
| 401 | UNAUTHORIZED | Token không hợp lệ | `"Invalid or expired authentication token"` |
| 403 | FORBIDDEN | User không có permission `vss:sync` | `"Insufficient permissions: vss:sync required"` |
| 500 | INTERNAL_ERROR | Lỗi database | `"Internal server error, please try again later"` |

---

## Ghi chú khi kiểm thử

### Điểm quan trọng

1. **Clinic isolation**: Clinic A và Clinic B phải có config VSS hoàn toàn riêng biệt. Nếu Clinic A update config, Clinic B không bị ảnh hưởng.

2. **Prescription ordering**: GET `/visits/{visit_id}/prescriptions` trả kết quả sắp xếp theo `prescribed_at ASC` (đơn cũ nhất trước). FE hiển thị `items[0]` = đơn cũ nhất.

3. **Permission gates**:
   - `GET /visits/{visit_id}/prescriptions` → require `prescription.read` (để đọc đơn)
   - `GET /integrations/vss/config` → require `vss:read` (để đọc cấu hình)
   - `PUT /integrations/vss/config` → require `vss:sync` (để cập nhật cấu hình)

4. **VSS config defaults**: Nếu clinic chưa cấu hình VSS, GET trả về defaults:
   ```json
   {
     "api_url": "",
     "api_key": "",
     "facility_code": "",
     "enabled": false
   }
   ```

5. **Partial PUT**: `PUT /integrations/vss/config` với body `{"enabled": true}` chỉ cập nhật field `enabled`, giữ nguyên các trường khác.

6. **Empty PUT**: `PUT /integrations/vss/config` với body `{}` được chấp nhận (no-op merge, trả về config hiện tại).

7. **Missing X-Clinic-Id**: Tất cả 3 API đều yêu cầu header `X-Clinic-Id`. Nếu không có → 400 BAD_REQUEST.

### Gợi ý dữ liệu kiểm thử

| Kịch bản | Input | Kết quả kỳ vọng |
|---------|-------|-----------------|
| GET prescriptions của visit có 2 đơn | `visit_id=UUID, X-Clinic-Id=CLINIC_A` | 200 + array 2 items, sắp xếp `prescribed_at ASC` |
| GET prescriptions của visit không có đơn | `visit_id=UUID, X-Clinic-Id=CLINIC_A` | 200 + `items=[], total=0` |
| GET prescriptions — missing X-Clinic-Id | (không gửi header) | 400 BAD_REQUEST |
| GET prescriptions — invalid visit_id UUID | `visit_id="invalid"` | 422 UNPROCESSABLE_ENTITY |
| GET prescriptions — missing `prescription.read` | User không có permission | 403 FORBIDDEN |
| GET VSS config — chưa cấu hình | (request to fresh clinic) | 200 + defaults (empty strings, enabled=false) |
| GET VSS config — đã cấu hình | (request to clinic with config) | 200 + config đã lưu |
| PUT VSS config — partial update | `{"enabled": true}` | 200 + full config (other fields unchanged) |
| PUT VSS config — empty body | `{}` | 200 + config không thay đổi |
| PUT VSS config — invalid permission | User không có `vss:sync` | 403 FORBIDDEN |
| Clinic isolation — GET config | Clinic A request → Clinic B's config | Không thể access; chỉ thấy Clinic A's config |

---

## Tóm tắt thay đổi schema

**prescriptions table** (không thay đổi):
- Đã tồn tại, không thêm cột mới

**clinic_settings table** (JSONB storage):
- Đã tồn tại cột `settings` (JSONB)
- Thêm key `vss` trong settings JSONB (không cần migration)
- Structure:
  ```json
  {
    "vss": {
      "api_url": "string",
      "api_key": "string",
      "facility_code": "string",
      "enabled": boolean
    },
    "..." : "other settings"
  }
  ```

---

**Phiên bản**: 1.0  
**Ngày**: 2026-05-31  
**Người thực hiện**: Implementation + Test Agent  
