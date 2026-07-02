# Thiết Kế Chi Tiết Tính Năng: Cấu hình giá thuốc + Báo cáo giá trị tồn kho

**Dự án:** Clinic CMS  
**Task:** TASK-083  
**Phiên bản:** 1.0  
**Ngày:** 2026-07-03  
**Người thực hiện:** Code Implementation + Review + Test Agents  
**Trạng thái:** Hoàn thành  
**Tài liệu liên quan:** TASK-011 (Medicine Catalog + Prescription), TASK-012 (Inventory + Batch + StockMovement + FEFO)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-07-03 | Phiên bản đầu tiên — hoàn thiện sau kiểm thử |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Nguồn dữ liệu đầu vào](#3-nguồn-dữ-liệu-đầu-vào)
- [4. Danh sách API](#4-danh-sách-api)
- [5. Chi tiết từng API](#5-chi-tiết-từng-api)
- [6. Cấu trúc cơ sở dữ liệu](#6-cấu-trúc-cơ-sở-dữ-liệu)
- [7. SQL tổng hợp và truy vấn dữ liệu](#7-sql-tổng-hợp-và-truy-vấn-dữ-liệu)
- [8. Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
- [9. Xử lý lỗi](#9-xử-lý-lỗi)
- [10. Ghi chú và lưu ý khi kiểm thử](#10-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Tính năng này cung cấp khả năng **quản lý giá thuốc** và **xem rõ số tiền đang nằm trong thuốc** (giá trị tồn kho quy ra tiền). Cụ thể:

1. **Cấu hình giá bán cho từng loại thuốc** — lưu giá bán (sale_price) trên từng thuốc, cho phép người quản lý theo dõi giá bán lẻ hiện tại.
2. **Báo cáo giá trị tồn kho** — hiển thị "Tổng tiền đang nằm trong thuốc" dựa trên **giá nhập (vốn)** thực tế của từng lô hàng còn tồn, thay vì ước tính trung bình.
3. **Tham khảo giá trị bán lẻ** — ngoài vốn tồn, cũng hiển thị giá trị bán lẻ (dùng sale_price) để tham khảo, giúp quản lý hiểu rõ tiềm năng doanh số từ tồn kho hiện tại.

**Ý nghĩa kế toán:** Vốn tồn (cost_value) phản ánh số tiền tối thiểu cần thiết để duy trì tồn kho hiện tại — đây là chỉ số quan trọng cho quản lý tài chính.

### 1.2 Phạm vi

**Bao gồm:**
- Cấu hình `sale_price` (giá bán) và tùy chọn `default_cost_price` (giá nhập mặc định) cho mỗi thuốc
- Báo cáo giá trị tồn kho: tính `cost_value = Σ(số lượng tồn × đơn giá nhập)` theo từng lô active/non-expired/non-recalled
- Hiển thị cảnh báo nếu lô thiếu giá nhập (`unit_cost`)
- Xuất Excel báo cáo giá trị tồn kho (chống formula-injection)
- Multi-tenancy/RLS per clinic

**Không bao gồm:**
- Lịch sử giá (price history) — chỉ giá hiện tại
- Tính toán giá nhập trung bình (weighted average) — dùng đơn giá thực tế từng lô
- Thay đổi luồng kê đơn (prescription) — sale_price không tự động điền vào unit_price

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Quản lý dược/quản lý kho** | Cấu hình giá bán thuốc, xem báo cáo tồn kho + giá trị vốn |
| **Kế toán/Quản lý tài chính** | Xem giá trị vốn tồn để lập báo cáo tài chính, quyết định mua thêm |
| **Hệ thống Inventory** | Cung cấp dữ liệu lô hàng (batch) với `unit_cost` (giá nhập thực tế) |
| **Hệ thống Medicine** | Cung cấp catalog thuốc + cấu hình giá |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
┌─────────────────────────────┐
│  Quản lý dược (UI)          │
│  - Cấu hình giá bán (sale_price)
│  - Cấu hình giá nhập mặc định (default_cost_price)
└────────────┬────────────────┘
             │ PUT/PATCH /medicines/:id
             ▼
┌─────────────────────────────┐
│  Medicine Service (BE)      │
│  - Lưu sale_price          │
│  - Lưu default_cost_price  │
└────────────┬────────────────┘
             │
             ▼
    ┌─────────────────────┐
    │  Database (medicine)│
    │  + sale_price       │
    │  + default_cost_price
    └─────────────────────┘


┌─────────────────────────────┐
│  Kế toán/Quản lý (UI)       │
│  Xem báo cáo giá trị tồn    │
└────────────┬────────────────┘
             │ GET /reports/inventory-valuation
             ▼
┌─────────────────────────────┐
│  Inventory Valuation Service│
│  - Lấy inventory_item       │
│  - Lấy batch (active)       │
│  - Tính cost_value per item │
│  - Tính retail_value (ref)  │
└────────────┬────────────────┘
             │
             ▼
    ┌──────────────────────────────┐
    │  Database (aggregation)       │
    │  SELECT SUM(qty × unit_cost)  │
    │         SUM(qty × sale_price) │
    │  FROM inventory_item + batch  │
    └──────────────────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  Response: Valuation Report │
│  - Per-medicine rows        │
│  - Total cost_value         │
│  - Total retail_value (opt.)│
│  - has_missing_cost flags   │
└────────────┬────────────────┘
             │
             ├─► Hiển thị trên UI (InventoryValuationReportPage)
             │
             └─► Export Excel (GET /export)
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | **Cấu hình giá bán thuốc** | Người quản lý truy cập MedicinesPage, chỉnh sửa/thêm mới thuốc, nhập giá bán (sale_price). Dữ liệu được lưu vào cột `medicine.sale_price` (Numeric 15,2, nullable). |
| 2 | **Cấu hình giá nhập mặc định (tùy chọn)** | Quản lý có thể đặt `default_cost_price` trên medicine (hiện chỉ via API, không có UI để chỉnh sửa). Dùng làm fallback nếu lô thiếu `batch.unit_cost`. |
| 3 | **Nhập lô hàng (từ TASK-012)** | Khi mua hàng, lô được tạo với `batch.unit_cost` (giá nhập thực tế). Nếu thiếu, sẽ dùng `default_cost_price` hoặc 0 (đánh dấu `has_missing_cost`). |
| 4 | **Xem báo cáo giá trị tồn** | Quản lý tài chính gọi `GET /reports/inventory-valuation`, nhận danh sách thuốc với: <br>- `available_qty` = tổng số lượng tồn (tính theo từng lô active/non-expired/non-recalled) <br>- `cost_value` = Σ(available_qty × effective_unit_cost) — vốn tồn <br>- `retail_value` = available_qty × sale_price (nếu có sale_price) <br>- `has_missing_cost` = cảnh báo nếu lô thiếu giá |
| 5 | **Tổng hợp vốn tồn** | Báo cáo trả về `total_cost_value` (tổng tiền nằm trong thuốc) và `total_retail_value` (tham khảo). Flag `has_any_missing_cost` nếu bất kỳ lô nào thiếu giá. |
| 6 | **Xuất Excel** | Người dùng nhấn "Xuất Excel", gọi `GET /reports/inventory-valuation/export`. Hệ thống trả file XLSX với các cột: Mã thuốc, Tên thuốc, Số lượng tồn, Giá trị vốn, Giá trị bán lẻ, Thiếu giá vốn. Tất cả cell được neutralize chống formula-injection. |

---

## 3. Nguồn dữ liệu đầu vào

Dữ liệu chỉ đến từ người dùng trực tiếp qua API (CRUD thuốc + xem báo cáo). Không có message queue hay file import.

---

## 4. Danh sách API

**Đường dẫn gốc:** `/api/v1`

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt |
|-----|------------|-----------|--------------|
| 1 | GET | `/reports/inventory-valuation` | Lấy báo cáo giá trị tồn kho (vốn + tham khảo bán lẻ) |
| 2 | GET | `/reports/inventory-valuation/export` | Xuất báo cáo giá trị tồn kho dưới dạng XLSX |
| 3 | PUT/PATCH | `/medicines/{id}` | Cập nhật thuốc (thêm/sửa `sale_price`, `default_cost_price`) — từ TASK-011 |

*(API #3 đã tồn tại từ TASK-011; TASK-083 chỉ thêm 2 trường mới)*

---

## 5. Chi tiết từng API

### 5.1 Lấy báo cáo giá trị tồn kho

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/reports/inventory-valuation` |
| **Mô tả** | Trả về danh sách thuốc có tồn kho kèm giá trị vốn (cost basis) và giá trị bán lẻ (reference). Dùng để xem "tiền đang nằm trong thuốc" theo từng thuốc và tổng cộng. |
| **Xác thực** | Bắt buộc (Bearer token) |
| **Quyền yêu cầu** | `report.financial` (tài chính) |

#### Tham số đầu vào

Không có tham số query hoặc body. API lấy `clinic_id` từ context request (header `X-Clinic-ID` hoặc JWT token).

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu từ ứng dụng client (POST man, browser, FE) |
| 2 | Kiểm tra token xác thực — từ chối nếu không hợp lệ (401 UNAUTHORIZED) |
| 3 | Kiểm tra quyền `report.financial` — từ chối nếu user không có quyền (403 FORBIDDEN) |
| 4 | Lấy `clinic_id` từ context |
| 5 | Truy vấn database: lấy từ `inventory_item`, `medicine`, `batch` theo điều kiện clinic + active/non-expired |
| 6 | Tính toán per medicine: available_qty, cost_value, retail_value, has_missing_cost |
| 7 | Tính tổng: total_cost_value, total_retail_value, has_any_missing_cost |
| 8 | Trả kết quả JSON |

**Truy vấn dữ liệu (tham khảo):**

```sql
SELECT
    m.id                                AS medicine_id,
    m.name                               AS medicine_name,
    m.sale_price                         AS sale_price,
    COALESCE(
        SUM(b.actual_quantity - b.reserved_quantity)
            FILTER (WHERE b.is_recalled = FALSE AND b.expiry_date >= :today),
        0
    )                                    AS available_qty,
    COALESCE(
        SUM(
            (b.actual_quantity - b.reserved_quantity)
            * COALESCE(b.unit_cost, m.default_cost_price, 0)
        ) FILTER (WHERE b.is_recalled = FALSE AND b.expiry_date >= :today),
        0
    )                                    AS cost_value,
    COALESCE(
        BOOL_OR(b.unit_cost IS NULL AND m.default_cost_price IS NULL)
            FILTER (
                WHERE b.is_recalled = FALSE
                  AND b.expiry_date >= :today
                  AND (b.actual_quantity - b.reserved_quantity) > 0
            ),
        FALSE
    )                                    AS has_missing_cost
FROM inventory_item ii
JOIN medicine m ON m.id = ii.medicine_id
LEFT JOIN batch b ON b.inventory_item_id = ii.id AND b.is_deleted = FALSE
WHERE ii.clinic_id = :clinic_id
  AND ii.is_deleted = FALSE
  AND m.is_deleted = FALSE
GROUP BY m.id, m.name, m.sale_price
HAVING COALESCE(
    SUM(b.actual_quantity - b.reserved_quantity)
        FILTER (WHERE b.is_recalled = FALSE AND b.expiry_date >= :today),
    0
) > 0
ORDER BY m.name ASC
```

**Giải thích SQL:**
- **FILTER (WHERE b.is_recalled = FALSE AND b.expiry_date >= :today):** Chỉ tính các lô active (không bị thu hồi, chưa hết hạn)
- **available_qty = SUM(actual_quantity - reserved_quantity):** Số lượng khả dụng = thực tế - đã dành cho đơn
- **cost_value = SUM((actual - reserved) × COALESCE(unit_cost, default_cost_price, 0)):** Vốn tồn dùng giá thực tế từng lô, fallback default_cost_price, cuối cùng là 0 nếu vẫn thiếu
- **has_missing_cost = BOOL_OR(unit_cost IS NULL AND default_cost_price IS NULL) ... COALESCE(..., FALSE):** Cảnh báo nếu bất kỳ lô nào (với qty > 0) thiếu cả hai nguồn giá
- **HAVING ... > 0:** Chỉ trả về thuốc có số lượng tồn > 0 (loại những thuốc hết)

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "clinic_id": "uuid-string",
  "total_cost_value": "1500000.50",
  "total_retail_value": "2250000.75",
  "has_any_missing_cost": false,
  "rows": [
    {
      "medicine_id": "uuid-string",
      "medicine_name": "Paracetamol 500mg",
      "available_qty": "500",
      "cost_value": "1000000.00",
      "retail_value": "1500000.00",
      "has_missing_cost": false
    },
    {
      "medicine_id": "uuid-string",
      "medicine_name": "Amoxicillin 250mg",
      "available_qty": "200",
      "cost_value": "500000.50",
      "retail_value": "750000.75",
      "has_missing_cost": false
    }
  ]
}
```

**Mô tả các trường kết quả:**

| Trường | Kiểu | Mô tả ý nghĩa nghiệp vụ |
|--------|------|------------------------|
| `clinic_id` | UUID | Mã phòng khám (từ context request) |
| `total_cost_value` | Decimal (string) | Tổng giá trị vốn tồn kho — số tiền tối thiểu cần để duy trì stock hiện tại |
| `total_retail_value` | Decimal (string) \| null | Tổng giá trị bán lẻ (reference only) — nếu tất cả thuốc đều có giá bán, đây là tổng doanh số tiềm năng từ tồn stock |
| `has_any_missing_cost` | Boolean | Cảnh báo: nếu true = có lô hàng nào thiếu giá, số liệu có thể chưa chính xác |
| `rows` | Array | Danh sách thuốc có tồn |
| `rows[].medicine_id` | UUID | Mã thuốc |
| `rows[].medicine_name` | String | Tên thuốc |
| `rows[].available_qty` | Decimal (string) | Số lượng tồn khả dụng (actual - reserved, active batch) |
| `rows[].cost_value` | Decimal (string) | Giá trị vốn của thuốc này = Σ(available_qty × unit_cost per batch) |
| `rows[].retail_value` | Decimal (string) \| null | Giá trị bán lẻ của thuốc này = available_qty × sale_price (nếu sale_price tồn tại) |
| `rows[].has_missing_cost` | Boolean | Cảnh báo: thuốc này có lô thiếu giá nhập không |

---

### 5.2 Xuất báo cáo giá trị tồn kho

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/reports/inventory-valuation/export` |
| **Mô tả** | Xuất báo cáo giá trị tồn kho dưới dạng file Excel (.xlsx). Dữ liệu giống API #5.1, nhưng format XLSX với các cột định nghĩa sẵn. Tất cả cell được neutralize chống formula-injection. |
| **Xác thực** | Bắt buộc (Bearer token) |
| **Quyền yêu cầu** | `report.financial` |

#### Tham số đầu vào

Không có tham số query hoặc body. API lấy `clinic_id` từ context request.

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu từ ứng dụng client |
| 2 | Kiểm tra token xác thực + quyền `report.financial` |
| 3 | Lấy dữ liệu báo cáo (gọi `get_inventory_valuation` như API #5.1) |
| 4 | Chuyển dữ liệu thành dòng XLSX: mỗi row tương ứng 1 thuốc, stringify Decimal → chuỗi |
| 5 | Neutralize tất cả cell (thêm leading apostrophe cho giá trị bắt đầu bằng `=`, `+`, `-`, `@`, tab, carriage return) — chống formula-injection |
| 6 | Trả file XLSX với `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

#### Cấu trúc file XLSX

**Sheet name:** `Giá trị tồn kho`

**Headers (1st row):**
| Mã thuốc | Tên thuốc | Số lượng tồn | Giá trị vốn | Giá trị bán lẻ | Thiếu giá vốn |

**Data rows (2nd onwards):**
| string (medicine_id) | string (medicine_name) | string (available_qty) | string (cost_value) | string (retail_value hoặc "") | string ("Có" / "Không") |

**Ví dụ:**
```
Mã thuốc                             | Tên thuốc           | Số lượng tồn | Giá trị vốn  | Giá trị bán lẻ | Thiếu giá vốn
uuid-1234                            | Paracetamol 500mg   | 500          | 1000000.00   | 1500000.00     | Không
uuid-5678                            | Amoxicillin 250mg   | 200          | 500000.50    |                | Không
```

**Filename:** `gia_tri_ton_kho.xlsx` (auto-generated)

---

## 6. Cấu trúc cơ sở dữ liệu

### 6.1 Tổng quan các bảng thay đổi

| Bảng | Thay đổi | Mục đích |
|------|---------|---------|
| `medicine` | Thêm 2 cột | Lưu giá bán (`sale_price`) và giá nhập mặc định (`default_cost_price`) |
| `batch` | Không thay đổi | Dùng cột `unit_cost` (từ TASK-012) để tính vốn tồn |
| `inventory_item` | Không thay đổi | Liên kết giữa `medicine` và `batch` |

### 6.2 Chi tiết bảng

#### Bảng: `medicine`

**Mô tả:** Bảng catalog thuốc (nền từ TASK-011). TASK-083 thêm 2 cột giá.

**Cột mới:**

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `sale_price` | NUMERIC(15,2) | Không | Giá bán lẻ của thuốc, per base_unit. Dùng cho báo cáo giá trị bán lẻ (tham khảo). Nếu không cấu hình → `null`. |
| `default_cost_price` | NUMERIC(15,2) | Không | Giá nhập mặc định, per base_unit. Dùng làm fallback nếu `batch.unit_cost IS NULL`. Nếu không cấu hình → `null`. |

**Migration SQL:**
```sql
ALTER TABLE medicine
ADD COLUMN sale_price NUMERIC(15, 2) NULL,
ADD COLUMN default_cost_price NUMERIC(15, 2) NULL;
```

**Notes:**
- Cả 2 cột nullable (không bắt buộc phải cấu hình)
- Kiểu Numeric(15,2) = tối đa 15 chữ số, 2 chữ thập phân (phù hợp tiền tệ VND)
- RLS từ TASK-011: `medicine` đã có RLS per clinic (via `inventory_item` → `clinic_id`)
- Không cần thêm permission mới: dùng `medicine.manage` để sửa, `report.financial` để xem báo cáo

#### Bảng: `batch` (không thay đổi, tham khảo)

Dùng cột `unit_cost` (NUMERIC, nullable) từ TASK-012 để lấy giá nhập thực tế của từng lô.

---

## 7. SQL tổng hợp và truy vấn dữ liệu

Tính năng này liên quan đến **thống kê/báo cáo** (inventory valuation), nên áp dụng phần này.

### 7.1 SQL tổng hợp / ghi dữ liệu

**Không áp dụng** — tính năng này không có logic ghi/tổng hợp dữ liệu vào bảng tổng hợp. Dữ liệu vốn tồn được tính toán **on-the-fly** từ batch + medicine khi API gọi, không lưu vào bảng riêng.

### 7.2 SQL truy vấn báo cáo / lấy dữ liệu

#### Truy vấn: Lấy giá trị tồn kho per medicine

**Mục đích:** Tính chi tiết từng thuốc: số lượng tồn khả dụng, giá trị vốn (cost_value), giá trị bán lẻ (retail_value), cảnh báo thiếu giá.

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `clinic_id` | `inventory_item.clinic_id` | Bắt buộc (từ context request) |
| `:today` | `batch.expiry_date >= :today` | Lô còn hết hạn (NOT expired) |
| `is_recalled` | `batch.is_recalled = FALSE` | Lô không bị thu hồi |
| `available_qty > 0` | `(actual_quantity - reserved_quantity) > 0` | Chỉ tính những thuốc có tồn |

```sql
SELECT
    m.id                                AS medicine_id,
    m.name                               AS medicine_name,
    m.sale_price                         AS sale_price,
    COALESCE(
        SUM(b.actual_quantity - b.reserved_quantity)
            FILTER (WHERE b.is_recalled = FALSE AND b.expiry_date >= :today),
        0
    )                                    AS available_qty,
    COALESCE(
        SUM(
            (b.actual_quantity - b.reserved_quantity)
            * COALESCE(b.unit_cost, m.default_cost_price, 0)
        ) FILTER (WHERE b.is_recalled = FALSE AND b.expiry_date >= :today),
        0
    )                                    AS cost_value,
    COALESCE(
        BOOL_OR(b.unit_cost IS NULL AND m.default_cost_price IS NULL)
            FILTER (
                WHERE b.is_recalled = FALSE
                  AND b.expiry_date >= :today
                  AND (b.actual_quantity - b.reserved_quantity) > 0
            ),
        FALSE
    )                                    AS has_missing_cost
FROM inventory_item ii
JOIN medicine m ON m.id = ii.medicine_id
LEFT JOIN batch b ON b.inventory_item_id = ii.id AND b.is_deleted = FALSE
WHERE ii.clinic_id = :clinic_id
  AND ii.is_deleted = FALSE
  AND m.is_deleted = FALSE
GROUP BY m.id, m.name, m.sale_price
HAVING COALESCE(
    SUM(b.actual_quantity - b.reserved_quantity)
        FILTER (WHERE b.is_recalled = FALSE AND b.expiry_date >= :today),
    0
) > 0
ORDER BY m.name ASC
```

**Giải thích chi tiết:**
- **Cột `available_qty`** — `SUM(actual_quantity - reserved_quantity)` cho tất cả batch active, dùng FILTER để chỉ lấy batch không hết hạn + không bị thu hồi
- **Cột `cost_value`** — tổng vốn = Σ(available_qty × effective_unit_cost), trong đó effective_unit_cost = COALESCE(batch.unit_cost, medicine.default_cost_price, 0)
  - Nếu batch có `unit_cost` → dùng `unit_cost`
  - Nếu batch không có `unit_cost` nhưng medicine có `default_cost_price` → dùng `default_cost_price`
  - Nếu cả hai thiếu → dùng 0 (và đánh dấu `has_missing_cost`)
- **Cột `has_missing_cost`** — `BOOL_OR(unit_cost IS NULL AND default_cost_price IS NULL)` với điều kiện FILTER (chỉ check batch có tồn, qty > 0). Nếu bất kỳ batch nào thiếu cả 2 → true
  - Dùng `COALESCE(..., FALSE)` để tránh NULL propagation khi không có batch nào match
- **HAVING** — chỉ trả về thuốc có tồn > 0 (loại thuốc hết hàng khỏi báo cáo)
- **Multi-tenancy** — `WHERE ii.clinic_id = :clinic_id` đảm bảo chỉ xem thuốc của clinic hiện tại

### 7.3 Logic tính toán tham số truy vấn

| Tham số | Lấy từ đâu | Ghi chú |
|---------|-----------|--------|
| `clinic_id` | Request context (JWT token hoặc header) | Bắt buộc — xác định phòng khám đang truy cập |
| `:today` | `date.today()` (Python) hoặc `CURDATE()` (SQL) | Ngày hiện tại — dùng để filter batch hết hạn (`expiry_date >= :today`) |

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi / Xử lý |
|----|--------------|-----------------|
| BR-001 | Giá bán (`sale_price`) phải ≥ 0 (nếu cấu hình) | Validate trên FE (Zod) và BE (Pydantic), từ chối giá trị âm với lỗi 422 |
| BR-002 | Giá nhập mặc định (`default_cost_price`) phải ≥ 0 (nếu cấu hình) | Validate trên FE + BE, từ chối giá âm |
| BR-003 | Vốn tồn (`cost_value`) = Σ(available_qty × unit_cost) **per batch**, fallback `default_cost_price`, cuối cùng fallback 0 | Không gộp giá nhập trung bình — dùng giá thực tế từng lô để chính xác kế toán |
| BR-004 | Nếu lô có `unit_cost` → dùng `unit_cost` (ưu tiên cao nhất) | Giá nhập thực tế của lô chính xác hơn giá mặc định của thuốc |
| BR-005 | Nếu lô không có `unit_cost` nhưng medicine có `default_cost_price` → dùng `default_cost_price` | Fallback để tránh tính 0 trong khi có thông tin giá |
| BR-006 | Nếu lô thiếu cả `unit_cost` và `default_cost_price` → tính 0, đánh dấu `has_missing_cost = true` | Cảnh báo người dùng dữ liệu chưa đủ, vốn tồn có thể bị đánh giá thấp |
| BR-007 | Giá trị bán lẻ (`retail_value`) = available_qty × `sale_price`, chỉ tính nếu `sale_price` có | Reference only — **KHÔNG** dùng để tính vốn tồn (`cost_value` độc lập) |
| BR-008 | Chỉ tính batch **active**: `is_recalled = FALSE`, `expiry_date >= today`, `is_deleted = FALSE` | Loại batch hết hạn, bị thu hồi, hoặc đã xóa khỏi báo cáo |
| BR-009 | Chỉ đưa thuốc vào báo cáo nếu có `available_qty > 0` | Không hiển thị thuốc hết tồn kho (tránh danh sách dài, gây khó đọc) |
| BR-010 | Quyền `report.financial` để xem báo cáo + xuất Excel | Dữ liệu vốn tồn là nhạy cảm tài chính — chỉ quản lý/kế toán được xem |
| BR-011 | Quyền `medicine.manage` để cấu hình giá bán/giá nhập mặc định | Chỉ quản lý dược / quản lý kho được sửa giá |
| BR-012 | Multi-tenancy: `cost_value` + `retail_value` **per clinic** — clinic B không thấy thuốc/giá của clinic A | RLS tại database level: `inventory_item.clinic_id` |

---

## 9. Xử lý lỗi

### 9.1 Các mã lỗi phổ biến

| Mã HTTP | Tình huống xảy ra | Thông báo trả về |
|---------|-------------------|-----------------|
| 200 | Thành công — trả dữ liệu báo cáo hoặc file Excel | Dữ liệu hoặc file Excel |
| 400 | Tham số query/body không hợp lệ (ví dụ: sale_price là chữ thay vì số) | `{"code": "INVALID_REQUEST", "message": "Tham số không hợp lệ: sale_price phải là số"}` |
| 401 | Token không hợp lệ hoặc đã hết hạn | `{"code": "UNAUTHORIZED", "message": "Yêu cầu xác thực để truy cập tài nguyên này"}` |
| 403 | User không có quyền `report.financial` hoặc `medicine.manage` | `{"code": "FORBIDDEN", "message": "Bạn không có quyền truy cập tài nguyên này"}` |
| 404 | Thuốc / báo cáo không tìm thấy (hiếm gặp — thường trả danh sách rỗng) | `{"code": "NOT_FOUND", "message": "Không tìm thấy tài nguyên"}` |
| 422 | Validation error — giá trị không nằm trong khoảng cho phép (ví dụ: sale_price < 0) | `{"code": "VALIDATION_ERROR", "message": "sale_price phải ≥ 0"}` |
| 500 | Lỗi hệ thống nội bộ (database, connection, v.v.) | `{"code": "INTERNAL_ERROR", "message": "Lỗi hệ thống, vui lòng thử lại sau"}` |

### 9.2 Kịch bản lỗi cụ thể

#### Kịch bản A: Cấu hình giá bán âm

**Yêu cầu:**
```json
PUT /api/v1/medicines/{id}
{
  "sale_price": "-1000"
}
```

**Phản hồi (422):**
```json
{
  "code": "VALIDATION_ERROR",
  "message": "sale_price phải ≥ 0"
}
```

#### Kịch bản B: Xem báo cáo mà thiếu quyền

**Yêu cầu:**
```
GET /api/v1/reports/inventory-valuation
(User không có quyền report.financial)
```

**Phản hồi (403):**
```json
{
  "code": "FORBIDDEN",
  "message": "Bạn không có quyền truy cập tài nguyên này"
}
```

#### Kịch bản C: Xuất Excel khi có lô thiếu giá

**Dữ liệu:** Paracetamol có 1 lô hết hạn (active), 1 lô không có `unit_cost` + `default_cost_price`

**Phản hồi (200):** File XLSX trả về bình thường, nhưng:
- Excel cell cho `has_missing_cost` = "Có" (cảnh báo)
- `cost_value` có thể không chính xác (một phần lô được tính 0)
- Header Excel không có cảnh báo, nhưng người dùng cần chú ý cột "Thiếu giá vốn"

---

## 10. Ghi chú và lưu ý khi kiểm thử

### 10.1 Điểm quan trọng cần nắm

1. **Vốn tồn = cost_value, KHÔNG = retail_value**  
   - `cost_value` = Σ(qty × unit_cost) — dùng giá nhập thực tế, phản ánh vốn kinh doanh
   - `retail_value` = Σ(qty × sale_price) — chỉ tham khảo, có thể null nếu sale_price chưa cấu hình
   - FE hiển thị 2 card riêng — "Tiền nằm trong thuốc" (cost) vs. "Giá trị bán lẻ" (reference)

2. **Fallback giá nhập: unit_cost → default_cost_price → 0 (+ cảnh báo)**  
   - Nếu batch có `unit_cost` (từ nhập hàng) → dùng nó
   - Nếu batch thiếu, nhưng medicine có `default_cost_price` (cấu hình) → dùng fallback
   - Nếu cả 2 thiếu → tính 0 và flag `has_missing_cost = true`

3. **default_cost_price chỉ có API, chưa có UI**  
   - Hiện tại MedicinesPage không có ô để chỉnh sửa `default_cost_price`
   - Nếu cần fallback, phải set qua API trực tiếp (PUT /medicines/{id})
   - Review note: "không clear được sale_price" — clearing bằng cách xóa dữ liệu trong ô, nhưng vì FE dùng `model_dump(exclude_unset=True)`, field rỗng sẽ bị skip (không reset về null)

4. **Excel export: công thức injection prevention (neutralize)**  
   - Tất cả cell giá trị có leading apostrophe nếu bắt đầu bằng `=`, `+`, `-`, `@`, tab, carriage return
   - Test: tạo thuốc tên `=SUM(A1:A10)`, export → check file Excel, xem apostrophe được thêm vào

5. **RLS / Multi-tenancy: per clinic**  
   - Mỗi clinic chỉ thấy thuốc + báo cáo của mình
   - Test: user clinic A không thấy thuốc/giá của clinic B

### 10.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Dữ liệu đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **Bình thường** | Thuốc A: sale_price=50000, 3 lô với qty=100,150,200, unit_cost=40000,42000,41000 | cost_value = (100×40000) + (150×42000) + (200×41000) = 14.6M; retail_value = 450×50000 = 22.5M |
| **Fallback default_cost_price** | Thuốc B: default_cost_price=30000; 1 lô qty=100, unit_cost=null | cost_value = 100×30000 = 3M; has_missing_cost = false (vì có fallback) |
| **Lô thiếu giá (cảnh báo)** | Thuốc C: 1 lô qty=50, unit_cost=null, default_cost_price=null (trên medicine cũng null) | cost_value += 50×0 = 0; has_missing_cost = true — cảnh báo dữ liệu chưa đủ |
| **Lô hết hạn (loại)** | Thuốc D: 2 lô, 1 active qty=100, 1 expired qty=50 | cost_value chỉ tính lô active, không tính lô expired |
| **Lô bị thu hồi (loại)** | Thuốc E: 1 lô active qty=100, 1 lô recalled qty=80 | cost_value chỉ tính active, loại recalled |
| **Hết tồn kho** | Thuốc F: qty=0 (hoặc actual = reserved) | Không xuất hiện trong báo cáo (HAVING qty > 0) |
| **Export Excel** | Bất kỳ báo cáo nào | File .xlsx, 6 cột, tất cả Decimal stringify, không formula injection |
| **Quyền thiếu** | User role=nurse (có report.view, không report.financial) | 403 FORBIDDEN |

### 10.3 Hạn chế hiện tại

1. **`default_cost_price` chưa có UI để chỉnh sửa trên MedicinesPage** — hiện chỉ có API, do scope giới hạn. Nếu cần, thêm ô trong modal MedicinesPage ở TASK tương lai.

2. **Không thể "unset" sale_price từ modal** — xóa nội dung ô, FE gửi `undefined`, BE skip nó (do `model_dump(exclude_unset=True)`). Hiện tại phải clear via API trực tiếp nếu muốn reset về null.

3. **available_qty không có thousands separator** — ví dụ: "1500000" thay vì "1,500,000" trên UI. Cosmetic issue, không ảnh hưởng logic. Cost/retail value có format currency (có separator).

4. **Không lịch sử giá (price history)** — chỉ lưu giá hiện tại. Nếu cần truy vết lịch thay đổi giá, là scope mới.

### 10.4 Hướng phát triển

- **Price override per clinic** — nếu cơ sở dữ liệu toàn cầu cần giá khác nhau ở từng clinic
- **Giá nhập trung bình (weighted average)** — thay vì giá từng lô
- **Prefill unit_price kê đơn từ sale_price** — tự động điền giá bán vào kê đơn (tránh nhập tay)
- **Báo cáo trend vốn tồn** — biểu đồ vốn tồn theo thời gian
- **Alert tồn kho cao / vốn nằm nhiều** — cảnh báo quản lý khi vốn tồn vượt mức

---

## Phê duyệt

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Implementation Agent | — | 2026-07-03 |
| Code Review Agent | — | 2026-07-03 ✅ APPROVED |
| Test Agent | — | 2026-07-03 ✅ PASSED (1198/1198 tests) |
| Documentation Agent | — | 2026-07-03 |
