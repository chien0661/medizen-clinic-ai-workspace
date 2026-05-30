# Thiết Kế Chi Tiết: Kiểm Kê Kho Dược & Huỷ Lô Hàng Hết Hạn

**Dự án:** Clinic CMS — Quản Lý Phòng Khám  
**Task:** TASK-064  
**Phiên bản:** 1.0  
**Ngày:** 2026-05-31  
**Trạng thái:** Hoàn tất (27/27 kiểm thử đã qua)  
**Tài liệu liên quan:** TASK-053 (GAP audit), TASK-041 (branch consolidation)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-05-31 | Thiết kế ban đầu — hoàn tất tính năng kiểm kê và huỷ lô hàng |

---

## Mục lục

1. [Tổng quan tính năng](#1-tổng-quan-tính-năng)
2. [Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
3. [Nguồn dữ liệu đầu vào](#3-nguồn-dữ-liệu-đầu-vào)
4. [Danh sách API](#4-danh-sách-api)
5. [Chi tiết từng API](#5-chi-tiết-từng-api)
6. [Cấu trúc cơ sở dữ liệu](#6-cấu-trúc-cơ-sở-dữ-liệu)
7. [SQL tổng hợp và truy vấn dữ liệu](#7-sql-tổng-hợp-và-truy-vấn-dữ-liệu)
8. [Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
9. [Xử lý lỗi](#9-xử-lý-lỗi)
10. [Ghi chú và lưu ý khi kiểm thử](#10-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Tính năng này cung cấp hai quy trình quan trọng cho quản lý dược:

1. **Kiểm kê kho dược (Stocktake):** Cho phép dược sĩ tiến hành kiểm kê vật lý (đếm tay) toàn bộ dược phẩm trong kho so với hệ thống. Hệ thống tự động điều chỉnh số lượng dây chuyền nếu có chênh lệch (do mất mát, sai sót, vv.).

2. **Huỷ lô hàng hết hạn (Batch Dispose):** Cho phép dược sĩ ghi nhận việc huỷ/tiêu huỷ các lô dược hết hạn hoặc hư hỏng, tự động trừ khỏi tổng số dây chuyền và tạo chứng từ kiểm toán.

**Khoảng cách được bao phủ:**
- TASK-053 đã phát hiện 2 endpoint BE còn thiếu + 2 mock-success FE.
- TASK-064 hoàn tất việc (a) implement 2 endpoint BE, (b) gỡ mock-success FE để lỗi thật nổi lên.

### 1.2 Phạm vi

**Bao gồm:**
- `GET /api/v1/inventory/stocktake` — lấy snapshot kỳ vọng
- `POST /api/v1/inventory/stocktake` — submit kết quả kiểm kê + tạo adjustment movements
- `POST /api/v1/inventory/batches/dispose` — huỷ lô hàng + tạo write-off movements
- Gỡ bỏ mock-success fallback từ FE (StocktakePage, ExpiryProcessingPage)
- Kiểm toán (audit trail) via `StockMovement` records
- Cách ly theo phòng khám (tenant RLS)

**Không bao gồm:**
- Refactor toàn bộ module inventory
- Thay đổi cấu trúc batch/movement hiện tại
- Tính năng lập kế hoạch/dự báo dược

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Dược sĩ / Quản lý dược** | Người tiến hành kiểm kê + huỷ lô, quyền `inventory.adjust` |
| **Phòng khám (Clinic)** | Phạm vi dữ liệu — mỗi phòng khám độc lập |
| **Hệ thống CMS** | Backend FastAPI + DB PostgreSQL, FE React/Tauri |
| **Audit / Compliance** | Yêu cầu ghi chép đầy đủ lý do + ai tiến hành |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
╔═══════════════════════════════════════════════════════════════════╗
║                        KIỂM KÊ KHO DƯỢC                           ║
╚═════════════════════════════════════╤═════════════════════════════╝
                                      │
              ┌───────────────────────┴───────────────────────┐
              │                                               │
      ┌───────▼─────────┐                         ┌──────────▼────────┐
      │ Dược sĩ nhấn    │                         │ Hệ thống tạo      │
      │ "Bắt đầu kiểm"  │                         │ snapshot hiện tại │
      └───────┬─────────┘                         └──────────┬────────┘
              │                                              │
              │ GET /inventory/stocktake ◄──────────────────┘
              │                                              
              ▼                                              
      ┌──────────────────────────────────────────────────────┐
      │ Bước 1: Chuẩn bị                                     │
      │ - Xem danh sách dược (77+ mặt hàng)                  │
      │ - Xem số lượng lý thuyết hệ thống (expected_qty)     │
      │ - Bắt đầu đếm từng mặt hàng                          │
      └──────────────┬───────────────────────────────────────┘
                     │
      ┌──────────────▼───────────────────────────────────────┐
      │ Bước 2: Đếm                                          │
      │ - Dược sĩ nhập số lượng thực tế (actual_qty)         │
      │ - Hệ thống lưu từng mục nhập                         │
      └──────────────┬───────────────────────────────────────┘
                     │
      ┌──────────────▼───────────────────────────────────────┐
      │ Bước 3: Đối chiếu                                    │
      │ - Xem bảng so sánh: Lý thuyết vs Thực tế             │
      │ - Tính chênh lệch (variance) cho từng mục            │
      │ - Nhấn "Xác nhận & Lưu"                              │
      └──────────────┬───────────────────────────────────────┘
                     │
      ┌──────────────▼───────────────────────────────────────┐
      │ POST /inventory/stocktake                            │
      │ { items: [{id, actual}, ...], notes? }               │
      └──────────────┬───────────────────────────────────────┘
                     │
      ┌──────────────▼───────────────────────────────────────┐
      │ Backend xử lý từng mục:                              │
      │ 1. Tính variance = actual - expected                 │
      │ 2. Tạo StockMovement records (movement_type=adjust)  │
      │    theo thứ tự FEFO (First-Expiry-First-Out):        │
      │    - Thiếu → trừ từ lô sớm hết hạn nhất trước       │
      │    - Thừa → cộng vào lô muộn hết hạn nhất           │
      │ 3. Cập nhật batch.actual_quantity                    │
      │ 4. Ghi audit trail (user, ngày giờ, lý do)          │
      └──────────────┬───────────────────────────────────────┘
                     │
      ┌──────────────▼───────────────────────────────────────┐
      │ Phản hồi: { adjusted_count, results[] }              │
      │ - Số mục có chênh lệch                               │
      │ - Chi tiết từng mục + movement IDs                   │
      └──────────────┬───────────────────────────────────────┘
                     │
      ┌──────────────▼───────────────────────────────────────┐
      │ FE: Toast thành công / lỗi                           │
      └──────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════╗
║                      HUỶ LÔ HÀNG HẾT HẠN                          ║
╚═════════════════════════════════════╤═════════════════════════════╝
                                      │
              ┌───────────────────────┴───────────────────────┐
              │                                               │
      ┌───────▼──────────┐                     ┌──────────────▼────────┐
      │ Dược sĩ nhấn     │                     │ Hệ thống lọc & hiển   │
      │ "Xử lý hết hạn"  │                     │ thị lô hàng hết hạn   │
      └───────┬──────────┘                     │ (trong 90 ngày)       │
              │                                 └──────────┬────────────┘
              │                                           │
              │ GET /inventory/batches (near_expiry=true)◄┘
              │                                           
              ▼                                           
      ┌──────────────────────────────────────────────────────┐
      │ Xem danh sách lô:                                    │
      │ - Lô 1 | Dược A | Exp 2026-06-01 | Qty: 50          │
      │ - Lô 2 | Dược B | Exp 2026-06-15 | Qty: 30          │
      │ - ... (chọn một hoặc nhiều lô để huỷ)               │
      └──────────────┬───────────────────────────────────────┘
                     │
      ┌──────────────▼───────────────────────────────────────┐
      │ Dược sĩ nhấn "Huỷ lô" (Dispose)                     │
      │ Hệ thống hiển thị cảnh báo:                          │
      │ "Bạn sắp huỷ X lô, số lượng sẽ bị trừ khỏi kho"     │
      └──────────────┬───────────────────────────────────────┘
                     │
      ┌──────────────▼───────────────────────────────────────┐
      │ POST /inventory/batches/dispose                      │
      │ { batch_ids: [id1, id2, ...], reason: "expired" }   │
      └──────────────┬───────────────────────────────────────┘
                     │
      ┌──────────────▼───────────────────────────────────────┐
      │ Backend xử lý từng lô:                               │
      │ 1. Kiểm tra: Lô có tồn tại + thuộc phòng khám này?  │
      │    (404 nếu không tìm thấy hoặc xóa rồi)            │
      │ 2. Kiểm tra: reserved_qty == 0?                      │
      │    (400 BUSINESS_RULE_VIOLATION nếu > 0)            │
      │    → Không thể huỷ lô đang bị giữ cho đơn             │
      │ 3. Tạo StockMovement:                                │
      │    - movement_type = "expiry_writeoff"               │
      │    - quantity_delta = -(actual_qty)                  │
      │ 4. Cập nhật lô:                                      │
      │    - actual_quantity = 0                             │
      │    - is_deleted = true (soft delete)                 │
      │    - deleted_by, deleted_at                          │
      │ 5. Ghi audit trail                                   │
      └──────────────┬───────────────────────────────────────┘
                     │
      ┌──────────────▼───────────────────────────────────────┐
      │ Phản hồi: { disposed_count, results[] }              │
      │ - Số lô đã huỷ thành công                            │
      │ - Chi tiết từng lô + qty huỷ + movement ID           │
      └──────────────┬───────────────────────────────────────┘
                     │
      ┌──────────────▼───────────────────────────────────────┐
      │ FE: Toast thành công / lỗi                           │
      │    Nếu lỗi (reserved_qty > 0):                       │
      │    "Không thể huỷ — lô này có đơn giữ hàng"          │
      └──────────────────────────────────────────────────────┘
```

### 2.2 Mô tả các bước chính

#### Kiểm Kê Kho Dược

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | **Lấy snapshot** | FE gọi `GET /inventory/stocktake` → Backend trả về danh sách dược + số lượng lý thuyết (expected_qty) từ tổng tất cả lô dây chuyền hiện tại |
| 2 | **Nhập dữ liệu** | Dược sĩ xem từng loại dược, nhập số lượng thực tế đã đếm được (actual_qty) |
| 3 | **Đối chiếu & xác nhận** | Xem bảng so sánh lý thuyết vs thực tế, xem chênh lệch (variance) cho từng mục, nhấn lưu |
| 4 | **Gửi yêu cầu điều chỉnh** | FE gửi `POST /inventory/stocktake` với danh sách dược + actual_qty + notes tùy chọn |
| 5 | **Backend xử lý variance** | Cho mỗi mục có chênh lệch: tạo `StockMovement` records, cập nhật `batch.actual_quantity` theo FEFO logic |
| 6 | **Phản hồi kết quả** | Backend trả về `adjusted_count` (mục có chênh lệch) + chi tiết từng mục |
| 7 | **Ghi chép kiểm toán** | Tất cả movements được lưu với `performed_by`, `reason`, `created_at` |

#### Huỷ Lô Hàng Hết Hạn

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | **Xem danh sách lô hết hạn** | FE gọi `GET /inventory/batches?near_expiry=true` → lấy các lô sắp hết hạn trong 90 ngày tới |
| 2 | **Chọn lô để huỷ** | Dược sĩ chọn một hoặc nhiều lô (VD: hết hạn, hư hỏng, bị thu hồi) |
| 3 | **Xác nhận huỷ** | Hệ thống hiển thị cảnh báo danh sách lô + số lượng sắp bị trừ |
| 4 | **Gửi yêu cầu** | FE gửi `POST /inventory/batches/dispose` với batch_ids + reason |
| 5 | **Backend xác thực** | Kiểm tra từng lô: tồn tại? thuộc phòng khám? reserved_qty = 0? |
| 6 | **Tạo movements & soft delete** | Tạo `StockMovement` (type=expiry_writeoff), set `actual_quantity=0`, đánh dấu `is_deleted=true` |
| 7 | **Phản hồi kết quả** | Trả về số lô huỷ thành công + chi tiết từng lô |
| 8 | **Audit trail** | Ghi nhận user, thời gian, lý do trong `StockMovement` |

---

## 3. Nguồn dữ liệu đầu vào

**Không áp dụng** — Tính năng này **không** nhận dữ liệu từ message queue hay file import.
Dữ liệu đầu vào đến từ **người dùng trực tiếp qua FE** (kiểm kê thủ công, chọn lô để huỷ).

---

## 4. Danh sách API

**Đường dẫn gốc:** `/api/v1/`  
**Xác thực:** Tất cả yêu cầu phải có header `Authorization: Bearer {token}` + quyền `inventory.adjust`  
**Cách ly:** Tất cả dữ liệu bị lọc theo `clinic_id` từ JWT

| # | Phương thức | Đường dẫn | Mô tả tóm tắt |
|---|-----------|----------|--------------|
| 1 | GET | `/inventory/stocktake` | Lấy snapshot số lượng lý thuyết cho kiểm kê |
| 2 | POST | `/inventory/stocktake` | Submit kết quả kiểm kê; tạo adjustment movements |
| 3 | POST | `/inventory/batches/dispose` | Huỷ lô hàng hết hạn; tạo write-off movements |

---

## 5. Chi tiết từng API

### 5.1 GET /inventory/stocktake — Lấy Snapshot Kiểm Kê

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/inventory/stocktake` |
| **Mô tả** | Lấy snapshot hiện tại: danh sách dược + số lượng lý thuyết (tổng từ tất cả lô dây chuyền hoạt động). Dược sĩ dùng để khởi tạo form kiểm kê. |
| **Xác thực** | Bắt buộc + quyền `inventory.adjust` |
| **Cách ly** | Chỉ trả dữ liệu của phòng khám hiện tại |

#### Tham số đầu vào

Không có query parameters.

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu từ FE |
| 2 | Xác thực token (401 nếu không có) |
| 3 | Kiểm tra quyền `inventory.adjust` (403 nếu không có) |
| 4 | Lấy `clinic_id` từ JWT claims |
| 5 | Truy vấn tất cả `InventoryItem` của phòng khám (chưa xóa) |
| 6 | Cho mỗi item, tính `expected_qty = SUM(batch.actual_qty)` (chỉ lô hoạt động: không xóa, không bị recall) |
| 7 | Sắp xếp theo tên dược |
| 8 | Trả về danh sách + timestamp |

**Truy vấn cơ sở dữ liệu:**

```sql
SELECT
    ii.id AS inventory_item_id,
    m.name AS medicine_name,
    m.code AS medicine_code,
    m.base_unit,
    COALESCE(SUM(b.actual_quantity), 0) AS expected_quantity
FROM inventory_item ii
JOIN medicine m ON ii.medicine_id = m.id
LEFT JOIN batch b ON (
    b.inventory_item_id = ii.id
    AND b.clinic_id = :clinic_id
    AND b.is_deleted = FALSE
    AND b.is_recalled = FALSE
)
WHERE
    ii.clinic_id = :clinic_id
    AND ii.is_deleted = FALSE
GROUP BY
    ii.id,
    m.name,
    m.code,
    m.base_unit
ORDER BY m.name ASC;
```

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "items": [
    {
      "inventory_item_id": "550e8400-e29b-41d4-a716-446655440000",
      "medicine_name": "Natri Clorid",
      "medicine_code": "NaCl-0.9",
      "base_unit": "Lọ 100ml",
      "expected_quantity": 450.00
    }
  ],
  "generated_at": "2026-05-31T14:30:45.123456Z"
}
```

---

### 5.2 POST /inventory/stocktake — Submit Kiểm Kê

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/inventory/stocktake` |
| **Mô tả** | Submit kết quả kiểm kê (actual_qty cho từng dược). Backend tính variance, tạo adjustment movements, cập nhật batch quantities theo FEFO logic. |
| **Xác thực** | Bắt buộc + quyền `inventory.adjust` |
| **Cách ly** | Chỉ tác động dữ liệu của phòng khám hiện tại |

#### Tham số đầu vào

```json
{
  "items": [
    {
      "inventory_item_id": "550e8400-e29b-41d4-a716-446655440000",
      "actual_quantity": 450.00
    }
  ],
  "notes": "Đếm lại 3 lần, số lượng khớp"
}
```

| Tham số | Kiểu | Bắt buộc | Ràng buộc | Mô tả |
|---------|------|---------|-----------|-------|
| `items` | Array | Có | min 1 | Danh sách dược đã đếm |
| `items[].inventory_item_id` | UUID | Có | Phải tồn tại | ID dược trong hệ thống |
| `items[].actual_quantity` | Decimal | Có | >= 0 | Số lượng thực tế đã đếm |
| `notes` | String | Không | <= 500 ký tự | Ghi chú kiểm kê (VD: lý do chênh lệch) |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Xác thực token + quyền |
| 2 | Kiểm tra request body (400 nếu thiếu items hoặc qty < 0) |
| 3 | Cho mỗi item trong danh sách: |
| 4 | - Tính `expected_qty = SUM(batch.actual_qty)` (lô hoạt động) |
| 5 | - Tính `variance = actual_qty - expected_qty` |
| 6 | - Nếu variance ≠ 0: tạo StockMovement records để hấp thụ chênh lệch |
| 7 | **Logic FEFO:** |
| 8 | - **Nếu variance < 0 (thiếu):** Trừ dần từ lô soonest-expiry trước (earliest expiry first) |
| 9 | - **Nếu variance > 0 (thừa):** Cộng vào lô latest-expiry (last batch in order) |
| 10 | 11 | - Cập nhật `batch.actual_quantity` |
| 11 | - Tạo `StockMovement` record (movement_type="adjustment") |
| 12 | Lưu commit database |
| 13 | Trả về { adjusted_count, results[] } |

**Ví dụ xử lý variance (FEFO):**

Giả sử:
- Item A, expected_qty = 100 (3 lô)
  - Lô 1: Exp 2026-06-01, qty=30
  - Lô 2: Exp 2026-07-01, qty=40
  - Lô 3: Exp 2026-08-01, qty=30
- Actual_qty nhập = 85 (thiếu 15)

**Cách xử lý:**
1. Lô 1 (soonest): trừ 15 → Lô 1 qty = 30 - 15 = 15 ✓

Giả sử actual_qty = 110 (thừa 10):
1. Lô 3 (latest): cộng 10 → Lô 3 qty = 30 + 10 = 40 ✓

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "adjusted_count": 1,
  "results": [
    {
      "inventory_item_id": "550e8400-e29b-41d4-a716-446655440000",
      "expected_quantity": 100.00,
      "actual_quantity": 85.00,
      "variance": -15.00,
      "movement_ids": ["770e8400-e29b-41d4-a716-446655440005"]
    }
  ]
}
```

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `adjusted_count` | Integer | Số mục có chênh lệch (movements được tạo) |
| `results[].inventory_item_id` | UUID | ID dược |
| `results[].expected_quantity` | Decimal | Số lượng lý thuyết tại thời điểm submit |
| `results[].actual_quantity` | Decimal | Số lượng thực tế nhập |
| `results[].variance` | Decimal | Chênh lệch (thực - lý thuyết); âm = thiếu, dương = thừa |
| `results[].movement_ids[]` | Array UUID | Danh sách movement IDs tạo ra (để audit) |

---

### 5.3 POST /inventory/batches/dispose — Huỷ Lô Hàng

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/inventory/batches/dispose` |
| **Mô tả** | Huỷ/tiêu huỷ lô dược hết hạn hoặc hư hỏng. Backend kiểm tra điều kiện (reserved_qty == 0), tạo write-off movement, soft-delete lô. |
| **Xác thực** | Bắt buộc + quyền `inventory.adjust` |
| **Cách ly** | Chỉ tác động lô của phòng khám hiện tại |

#### Tham số đầu vào

```json
{
  "batch_ids": [
    "660e8400-e29b-41d4-a716-446655440003",
    "660e8400-e29b-41d4-a716-446655440004"
  ],
  "reason": "expired"
}
```

| Tham số | Kiểu | Bắt buộc | Ràng buộc | Mô tả |
|---------|------|---------|-----------|-------|
| `batch_ids` | Array UUID | Có | min 1 | Danh sách lô để huỷ |
| `reason` | String | Không | default="expired" | Lý do huỷ (VD: expired, damaged, recalled) |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Xác thực token + quyền |
| 2 | Kiểm tra request body (400 nếu batch_ids rỗng) |
| 3 | Cho mỗi batch_id: |
| 4 | - **Tìm lô:** `WHERE batch.id = batch_id AND batch.clinic_id = :clinic_id AND batch.is_deleted = FALSE` |
| 5 | - Nếu không tìm → 404 NOT_FOUND |
| 6 | - **Kiểm tra reserved_qty:** |
| 7 | - - Nếu `batch.reserved_quantity > 0` → 400 BUSINESS_RULE_VIOLATION (không thể huỷ lô bị giữ) |
| 8 | - **Tạo write-off movement:** |
| 9 | - - `StockMovement(movement_type="expiry_writeoff", quantity_delta=-(batch.actual_qty))` |
| 10 | - **Cập nhật lô:** |
| 11 | - - `actual_quantity = 0` |
| 12 | - - `is_deleted = TRUE` |
| 13 | - - `deleted_at = NOW()` |
| 14 | - - `deleted_by = user_id` |
| 15 | - Ghi log + audit trail |
| 16 | Lưu commit database |
| 17 | Trả về { disposed_count, results[] } |

**Kiểm tra Cách Ly (RLS):**

Nếu batch tồn tại nhưng thuộc phòng khám khác → 404 NOT_FOUND (không lộ thông tin)

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "disposed_count": 2,
  "results": [
    {
      "batch_id": "660e8400-e29b-41d4-a716-446655440003",
      "quantity_written_off": 50.00,
      "movement_id": "770e8400-e29b-41d4-a716-446655440005"
    },
    {
      "batch_id": "660e8400-e29b-41d4-a716-446655440004",
      "quantity_written_off": 30.00,
      "movement_id": "770e8400-e29b-41d4-a716-446655440006"
    }
  ]
}
```

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `disposed_count` | Integer | Số lô huỷ thành công |
| `results[].batch_id` | UUID | ID lô |
| `results[].quantity_written_off` | Decimal | Số lượng đã huỷ (= batch.actual_qty trước khi zeroing) |
| `results[].movement_id` | UUID | Movement ID tạo ra (dùng audit) |

**Lỗi (400 BUSINESS_RULE_VIOLATION):**

```json
{
  "detail": "Cannot dispose batch 660e8400-...: 5 units still reserved"
}
```

**Lỗi (404 NOT_FOUND):**

```json
{
  "detail": "Batch 660e8400-... not found or already deleted"
}
```

---

## 6. Cấu trúc cơ sở dữ liệu

### 6.1 Tổng quan các bảng

| Bảng | Mục đích |
|------|---------|
| `batch` | Lưu lô dược (actual_qty, expiry_date, vv.). Cột `is_deleted` và `deleted_by`, `deleted_at` để soft-delete |
| `stock_movement` | Audit trail: mỗi thay đổi qty được ghi nhận với movement_type, quantity_delta, reason, performed_by |
| `inventory_item` | Liên kết dược với phòng khám |
| `medicine` | Thông tin dược (name, code, base_unit) |

### 6.2 Chi tiết bảng liên quan

#### Bảng: `batch`

**Mô tả:** Lưu thông tin lô dược. Cột `actual_quantity` thay đổi khi kiểm kê hoặc huỷ. Cột `reserved_quantity` để kiểm tra xem lô có bị giữ cho đơn không.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Phòng khám sở hữu lô |
| `inventory_item_id` | UUID | Có | Tham chiếu đến inventory_item |
| `batch_number` | VARCHAR(50) | Có | Số lô từ nhà cung cấp |
| `expiry_date` | DATE | Có | Ngày hết hạn |
| `received_date` | DATE | Có | Ngày nhập kho |
| `actual_quantity` | DECIMAL(15,4) | Có | Số lượng hiện tại (thay đổi bởi kiểm kê, huỷ) |
| `reserved_quantity` | DECIMAL(15,4) | Có | Số lượng bị giữ cho đơn (không thể huỷ nếu > 0) |
| `is_recalled` | BOOLEAN | Có | Lô bị thu hồi? |
| `is_deleted` | BOOLEAN | Có | Soft delete flag (huỷ lô) |
| `deleted_at` | TIMESTAMP | Không | Thời điểm soft delete |
| `deleted_by` | UUID | Không | User ID người thực hiện soft delete |
| `updated_by` | UUID | Không | User ID lần cập nhật cuối |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo |

#### Bảng: `stock_movement`

**Mô tả:** Audit trail của tất cả thay đổi qty. Mỗi adjustment (kiểm kê) hoặc write-off (huỷ) tạo một dòng.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Phòng khám |
| `batch_id` | UUID | Có | Tham chiếu batch |
| `movement_type` | VARCHAR(50) | Có | "adjustment" (kiểm kê) hoặc "expiry_writeoff" (huỷ) |
| `quantity_delta` | DECIMAL(15,4) | Có | Thay đổi qty (âm = trừ, dương = cộng) |
| `quantity_before` | DECIMAL(15,4) | Có | Qty trước thay đổi |
| `quantity_after` | DECIMAL(15,4) | Có | Qty sau thay đổi |
| `reference_type` | VARCHAR(50) | Có | "stocktake" hoặc "batch_dispose" |
| `reason` | VARCHAR(500) | Không | Lý do chi tiết (kiểm kê notes hoặc reason) |
| `performed_by` | UUID | Có | User ID thực hiện |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo movement |

---

## 7. SQL tổng hợp và truy vấn dữ liệu

### Khái quát

Tính năng này **KHÔNG có logic tổng hợp (ETL)** — không aggregation, không batch job, không Kafka consumer.

Tuy nhiên, nó **CÓ logic truy vấn phức tạp** (multi-table join, GROUP BY, conditional WHERE) để:
1. Lấy snapshot expected_qty (GROUP BY inventory_item, SUM batches)
2. Liệt kê lô hết hạn (date range filter)
3. Tính toán FEFO ordering (ORDER BY expiry_date, received_date)

Vì vậy, phần này bao gồm **SQL truy vấn báo cáo** (7.2).

### 7.1 SQL tổng hợp / ghi dữ liệu

**Không áp dụng** — Tính năng này không có logic tổng hợp hay ETL. Tất cả dữ liệu đến từ người dùng trực tiếp.

### 7.2 SQL truy vấn báo cáo / lấy dữ liệu

#### 7.2.1 Truy vấn Snapshot Kiểm Kê (GET /inventory/stocktake)

**Mục đích:** Lấy danh sách dược + expected_qty (tổng từ lô hoạt động) cho form kiểm kê.

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `clinic_id` | `ii.clinic_id`, `b.clinic_id` | Bắt buộc, từ JWT |
| `include_deleted` | `ii.is_deleted`, `b.is_deleted` | Lọc: chỉ dược + lô chưa xóa |
| `include_recalled` | `b.is_recalled` | Lọc: loại lô bị recall |

```sql
SELECT
    ii.id AS inventory_item_id,
    m.name AS medicine_name,
    m.code AS medicine_code,
    m.base_unit,
    COALESCE(SUM(b.actual_quantity), 0) AS expected_quantity
FROM inventory_item ii
JOIN medicine m ON ii.medicine_id = m.id
LEFT JOIN batch b ON (
    b.inventory_item_id = ii.id
    AND b.clinic_id = :clinic_id
    AND b.is_deleted = FALSE          -- [Loại bỏ lô đã xóa]
    AND b.is_recalled = FALSE         -- [Loại bỏ lô bị recall]
)
WHERE
    ii.clinic_id = :clinic_id
    AND ii.is_deleted = FALSE         -- [Loại bỏ dược đã xóa]
GROUP BY
    ii.id,
    m.name,
    m.code,
    m.base_unit
ORDER BY m.name ASC;
```

**Giải thích:**
- **LEFT JOIN batch:** Mỗi dược có thể không có lô hoạt động (sẽ có qty = 0)
- **GROUP BY inventory_item_id:** Tập hợp tất cả qty lô theo dược
- **COALESCE(..., 0):** Nếu không có lô, qty = 0

#### 7.2.2 Truy vấn Lô Hết Hạn (GET /inventory/batches?near_expiry=true)

**Mục đích:** Liệt kê các lô sắp hết hạn trong 90 ngày (để huỷ/tiêu huỷ).

```sql
SELECT
    b.id,
    b.batch_number,
    ii.id AS inventory_item_id,
    m.name AS medicine_name,
    b.expiry_date,
    b.actual_quantity,
    b.reserved_quantity,
    ii.clinic_id
FROM batch b
JOIN inventory_item ii ON b.inventory_item_id = ii.id
JOIN medicine m ON ii.medicine_id = m.id
WHERE
    b.clinic_id = :clinic_id
    AND b.is_deleted = FALSE          -- [Loại bỏ lô đã soft-delete]
    AND b.is_recalled = FALSE         -- [Loại bỏ lô bị recall]
    AND b.expiry_date <= (CURRENT_DATE + INTERVAL '90 days')  -- [Sắp hết hạn trong 90 ngày]
ORDER BY b.expiry_date ASC, b.received_date ASC;  -- [FEFO: soonest first]
```

**Giải thích:**
- **expiry_date <= NOW + 90 days:** Bao gồm lô đã hết hạn + sắp hết
- **ORDER BY:** FEFO order (phục vụ dispose logic nếu cần xử lý multiple batches)

#### 7.2.3 Truy vấn Lô Hoạt Động Theo Item (cho FEFO adjustment)

**Mục đích:** Khi xử lý kiểm kê, lấy các lô hoạt động của một dược **theo FEFO order** để tính variance + tạo movements.

```sql
SELECT
    b.id,
    b.actual_quantity,
    b.inventory_item_id,
    b.expiry_date,
    b.received_date
FROM batch b
WHERE
    b.inventory_item_id = :inventory_item_id
    AND b.clinic_id = :clinic_id
    AND b.is_deleted = FALSE
    AND b.is_recalled = FALSE
    AND b.expiry_date >= CURRENT_DATE   -- [Loại lô đã hết hạn]
ORDER BY
    b.expiry_date ASC,                  -- [FEFO: soonest first]
    b.received_date ASC;                -- [Tiebreaker: older first]
```

**Giải thích:**
- **expiry_date >= CURDATE():** Chỉ lô còn hạn dùng
- **ORDER BY expiry_date, received_date:** FEFO logic — khi trừ, bắt đầu từ lô soonest-expiry

### 7.3 Logic tính toán tham số truy vấn

**Không áp dụng** — Tính năng này không có logic tính toán tham số phức tạp (như date range logic).
Các tham số đơn giản:
- `clinic_id` — từ JWT
- `batch_ids` — user chọn từ UI
- `near_expiry` — boolean cố định (90 ngày)

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm | Kiểm thử |
|----|--------------|---------------------|---------|
| **BR-1** | GET /stocktake trả về expected_qty = SUM(batch.actual_qty) từ lô hoạt động (không xóa, không recall, không hết hạn) | Qty sai → kiểm kê không chính xác | test_returns_snapshot ✓ |
| **BR-2** | POST /stocktake: nếu actual_qty = expected_qty (no variance) → không tạo movement | Movement thừa dẫn đến audit confusing | test_submit_no_variance ✓ |
| **BR-3** | POST /stocktake: nếu actual_qty < expected_qty (shortage) → tạo negative movements trên các lô soonest-expiry trước | Có thể xóa sai lô, hỏng FEFO logic | test_submit_shortage ✓ |
| **BR-4** | POST /stocktake: nếu actual_qty > expected_qty (surplus) → tạo positive movement trên lô latest-expiry | Có thể overload 1 lô, mất cơ hội rotate stock | test_submit_surplus ✓ |
| **BR-5** | GET /stocktake yêu cầu quyền `inventory.adjust` | User không phép truy cập được dữ liệu | test_requires_inventory_adjust_permission ✓ |
| **BR-6** | POST /stocktake yêu cầu quyền `inventory.adjust` | User không phép submit được | test_requires_inventory_adjust_permission ✓ |
| **BR-7** | Tất cả endpoint yêu cầu auth token hợp lệ (401 if none/invalid) | Request không được xử lý | test_unauthenticated_returns_401 ✓ |
| **BR-8** | POST /batches/dispose: tạo expiry_writeoff movement, zeroes actual_qty, soft-delete batch (is_deleted=true) | Batch vẫn tính vào stock, số liệu sai | test_dispose_batch ✓ |
| **BR-9** | POST /batches/dispose: nếu batch đã soft-delete → 404 NOT_FOUND | Có thể double-dispose → data integrity issue | test_dispose_already_deleted_batch_returns_404 ✓ |
| **BR-10** | POST /batches/dispose: nếu batch không tồn tại → 404 NOT_FOUND | Lỗi handling không clear | test_dispose_nonexistent_batch_returns_404 ✓ |
| **BR-11** | POST /batches/dispose yêu cầu quyền `inventory.adjust` | User không phép huỷ | test_requires_inventory_adjust_permission ✓ |
| **BR-12** | POST /batches/dispose: nếu batch.reserved_quantity > 0 → 400 BUSINESS_RULE_VIOLATION (không thể huỷ) | Huỷ lô bị giữ → đơn mất hàng, customer dissatisfied | test_dispose_batch_with_reservation_returns_400 ✓ |
| **BR-13** | POST /batches/dispose: batch thuộc phòng khám khác (tenant isolation) → 404 NOT_FOUND | Data breach: user A huỷ batch của user B | test_tenant_isolation_cross_clinic_batch_returns_404 ✓ |

---

## 9. Xử lý lỗi

### 9.1 Các mã lỗi phổ biến

| Mã HTTP | Mã lỗi | Tình huống | Thông báo | Hành động FE |
|---------|--------|-----------|-----------|--------------|
| 400 | `INVALID_REQUEST` | Body thiếu field bắt buộc / qty âm / items rỗng | "Yêu cầu không hợp lệ: [chi tiết]" | Hiển thị toast lỗi, gợi ý nhập lại |
| 400 | `BUSINESS_RULE_VIOLATION` | Huỷ lô có reserved_qty > 0 | "Không thể huỷ lô: X đơn vị đang được giữ" | Toast error, không gọi lại |
| 401 | `UNAUTHORIZED` | Token không có / hết hạn | "Yêu cầu xác thực" | Redirect login |
| 403 | `FORBIDDEN` | User không có quyền `inventory.adjust` | "Không đủ quyền" | Toast "Bạn không đủ quyền", disable button |
| 404 | `NOT_FOUND` | Batch/Item không tồn tại hoặc đã xóa | "Không tìm thấy dữ liệu" | Toast "Dữ liệu không còn tồn tại, tải lại danh sách" |
| 422 | `VALIDATION_ERROR` | Tham số giá trị sai (VD: qty > MAX_DECIMAL) | "Giá trị tham số không hợp lệ" | Toast, request validation |
| 500 | `INTERNAL_ERROR` | Lỗi database / server | "Lỗi hệ thống, vui lòng thử lại" | Toast, retry button |

### 9.2 Định dạng phản hồi lỗi

**Lỗi 400 (Validation):**

```json
{
  "detail": "Validation error: items must have at least 1 item"
}
```

**Lỗi 400 (Business Rule):**

```json
{
  "detail": "Cannot dispose batch 660e8400-...: 5 units still reserved"
}
```

**Lỗi 401:**

```json
{
  "detail": "Not authenticated"
}
```

**Lỗi 403:**

```json
{
  "detail": "Insufficient permissions"
}
```

**Lỗi 404:**

```json
{
  "detail": "Batch 660e8400-... not found or already deleted"
}
```

---

## 10. Ghi chú và lưu ý khi kiểm thử

### 10.1 Điểm quan trọng cần nắm

- **FEFO logic phức tạp:** Kiểm kê tạo movements để phân phối variance. Kiểm thử cần verify batches được cập nhật theo FEFO (soonest-expiry trước khi trừ, latest khi cộng).

- **Soft delete + RLS:** Các lô đã huỷ (`is_deleted=true`) không được trả về trong snapshot. Kiểm thử cần confirm: sau khi dispose, lô không còn trong `GET /inventory/batches`, `GET /inventory/stocktake`.

- **Reserved quantity guard:** Không thể huỷ lô nếu `reserved_qty > 0`. Kiểm thử cần tạo reserve trên batch (link to prescription/voucher), sau đó test dispose → 400 BUSINESS_RULE_VIOLATION.

- **Audit trail:** Tất cả movements phải có `performed_by`, `reason`, `created_at`. Dùng để compliance + debugging.

- **Tenant isolation:** Mỗi phòng khám thấy/thao tác chỉ dữ liệu của mình. Kiểm thử cross-clinic dispose → 404.

### 10.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **Kiểm kê bình thường** | actual_qty = expected_qty (từ snapshot) | adjusted_count=0, movement_ids=[] |
| **Kiểm kê thiếu** | actual_qty < expected_qty (50% of expected) | adjusted_count=1, negative movements trên soonest-expiry batch |
| **Kiểm kê thừa** | actual_qty > expected_qty (150% of expected) | adjusted_count=1, positive movement trên latest-expiry batch |
| **Huỷ lô bình thường** | Lô exp 2026-06-01, qty=50, reserved=0 | disposed_count=1, qty_written_off=50 |
| **Huỷ lô bị giữ** | Batch có reserved_qty=10 > 0 | HTTP 400 BUSINESS_RULE_VIOLATION |
| **Huỷ lô đã xóa** | batch.is_deleted=TRUE | HTTP 404 NOT_FOUND |
| **Huỷ từ phòng khám khác** | batch.clinic_id ≠ user.clinic_id | HTTP 404 NOT_FOUND (RLS) |
| **Không quyền** | User role="customer" (no `inventory.adjust`) | HTTP 403 FORBIDDEN |
| **Không auth** | Token missing / invalid | HTTP 401 UNAUTHORIZED |

### 10.3 Hạn chế hiện tại

- **Snapshot tĩnh:** Snapshot không real-time (tính lúc gọi API). Nếu dược sĩ kiểm kê lâu, có thể có lô mới nhập trong khi dạo. *(Chấp nhận được vì là snapshot khởi động form)*

- **Batch-level adjustment:** Variance được phân phối trên batch, không trên lô NHẤT ĐỊNH. *(Thiết kế FEFO đã tối ưu)*

- **Không rollback kiểm kê:** Sau khi submit, không có undo. *(Nên ghi audit trail rõ ràng)*

### 10.4 Hướng phát triển

- **Stocktake session tracking:** Ghi nhận session ID, thời gian bắt đầu/kết thúc, user → better audit.
- **Batch-level notes:** Cho phép ghi chú riêng lẻ cho từng lô huỷ (VD: nguyên nhân hư hỏng).
- **Approval workflow:** Kiểm kê / huỷ cần duyệt trước khi committed (chưa support).
- **Scheduled stocktake:** Thêm tính năng đặt lịch kiểm kê định kỳ + reminder.

---

## Kết luận

TASK-064 hoàn tất hai tính năng quan trọng:
1. **Kiểm kê kho dược** — process đếm tay, so sánh hệ thống, điều chỉnh tự động (FEFO logic)
2. **Huỷ lô hàng** — process ghi nhận huỷ/tiêu huỷ, với guard để không huỷ lô đang được sử dụng

Toàn bộ đã được kiểm thử (27/27 pass), audit trail hoàn chỉnh, RLS + permission gate được enforce.

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Test Agent | — | 2026-05-31 ✓ |
| Documentation Agent | — | 2026-05-31 |

