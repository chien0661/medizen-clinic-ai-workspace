# Thiết Kế Chi Tiết Tính Năng: Quản lý Đa Đơn vị Đo + Quy Đổi

**Dự án:** Clinic CMS  
**Task:** TASK-124  
**Phiên bản:** 1.0  
**Ngày:** 2026-07-27  
**Người thực hiện:** Development Team (Phase 1–3)  
**Trạng thái:** Đã duyệt & Hoàn thành  
**Tài liệu liên quan:** 
- Implementation Plan: `docs/tasks/TASK-124/refs/implementation-plan.md`
- Test Report: `docs/tasks/TASK-124/deliveries/test-reports/test-report.md`
- API Spec: `docs/tasks/TASK-124/deliveries/api-specs/unit-conversion-api.md`

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-07-27 | Phiên bản đầu tiên — toàn bộ 3 phase (BE core + prescribe/dispense/invoice + FE admin CRUD) hoàn thành và APPROVED |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Mô hình dữ liệu](#3-mô-hình-dữ-liệu)
- [4. Resolver (Dịch vụ quy đổi đơn vị)](#4-resolver-dịch-vụ-quy-đổi-đơn-vị)
- [5. Danh sách API](#5-danh-sách-api)
- [6. Cấu trúc cơ sở dữ liệu](#6-cấu-trúc-cơ-sở-dữ-liệu)
- [7. Chi tiết luồng nghiệp vụ](#7-chi-tiết-luồng-nghiệp-vụ)
- [8. Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
- [9. Xử lý lỗi](#9-xử-lý-lỗi)
- [10. Ghi chú kiểm thử & Backward Compatibility](#10-ghi-chú-kiểm-thử--backward-compatibility)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Cung cấp khả năng quản lý **ba vai trò đơn vị riêng biệt** cho mỗi loại thuốc:

1. **Đơn vị nhập (purchase_unit):** Đơn vị mua từ nhà cung cấp (thùng, hộp lớn, etc.). Quy đổi sang base_unit qua `pack_size`.
2. **Đơn vị tồn & cảnh báo (base_unit):** Đơn vị tiêu chuẩn của kho hàng. Tất cả tồn kho, ngưỡng cảnh báo, FIFO/FEFO tính toán dựa trên base_unit.
3. **Đơn vị bán & cấp phát (sell_unit):** Đơn vị mà bác sĩ kê đơn và dược sĩ cấp phát (viên, ml, vỉ, etc.). Khi kê đơn, hệ thống tự động quy đổi sang base_unit để kiểm tra tồn và trừ kho chính xác.

**Lợi ích:**
- Xử lý nhất quán các loại thuốc có nhiều quy cách (vd: nhập thùng 100 viên, tồn theo hộp 10 viên, bán lẻ theo viên).
- Tránh sai sót tính toán số lượng khi bán không trùng khít với tồn.
- Hóa đơn và báo cáo luôn chuẩn xác theo đơn vị bán thực tế.

### 1.2 Phạm vi

**Bao gồm:**
- Định nghĩa mối quan hệ quy đổi giữa các đơn vị thông qua bảng `unit_conversion` tổng quát (n cấp).
- Quản lý `sell_unit` và `dosage_form_id` trên mỗi loại thuốc.
- Dịch vụ resolver tự động quy đổi số lượng khi kê đơn (sell → base).
- API admin để CRUD quy đổi đơn vị.
- Giao diện admin để quản lý bảng quy đổi trên MedicinesPage.
- Giao diện kê đơn tự động đặt mặc định đơn vị bán + hiển thị gợi ý quy đổi.
- Trữ cảnh báo tồn giữ theo base_unit (KHÔNG thay đổi so với trước).
- Giá theo đơn vị bán (`sale_price` = giá/sell_unit).

**Không bao gồm:**
- Thay đổi logic cảnh báo tồn (vẫn tính theo base_unit như hiện tại).
- Hỗ trợ quy đổi đa bước (chaining) tự động — hiện tại mối quan hệ chỉ là trực tiếp từ unit A → unit B.
- Thay đổi cơ chế FIFO/FEFO (vẫn tính theo base_unit).

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Quản lý phòng khám (Admin)** | Sử dụng MedicinesPage để định nghĩa bảng quy đổi cho từng loại thuốc, chọn sell_unit, liên kết dosage_form. |
| **Bác sĩ / Kê đơn** | Kê đơn theo sell_unit (ví dụ: "10 viên aspirin"), hệ thống tự quy đổi sang base_unit để kiểm tra kho và cấp phát. |
| **Dược sĩ / Nhân viên kho** | Cấp phát theo sell_unit như được hiển thị trên đơn; kho trừ theo base_unit (nội bộ). |
| **Hóa đơn & Báo cáo** | Dữ liệu theo sell_unit + giá/sell_unit; doanh thu, tồn kho theo base_unit. |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. NHẬP KHO                                                      │
│    Nhân viên nhập (ví dụ: 5 thùng aspirin, 100 viên/thùng)      │
├─────────────────────────────────────────────────────────────────┤
│ Hệ thống tính: qty_base = 5 thùng × 100 viên/thùng = 500 viên   │
│ Lưu Batch: actual_quantity = 500 (base_unit)                     │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. KỀ ĐƠN                                                        │
│    Bác sĩ kê: "10 viên aspirin" (sell_unit = viên)              │
├─────────────────────────────────────────────────────────────────┤
│ Hệ thống: qty_base = 10 viên × 1 (factor viên→viên) = 10 viên   │
│ PrescriptionItem: quantity=10, unit="viên" (gọi là sell)        │
│ Reservation: dành riêng 10 viên từ Batch (base_unit)            │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. CẤPPHÁT (DISPENSE)                                           │
│    Dược sĩ cấp: 10 viên (hiển thị theo sell_unit)               │
├─────────────────────────────────────────────────────────────────┤
│ Hệ thống trừ kho: Batch.actual_quantity -= 10 (base_unit)       │
│ → Batch.actual_quantity = 500 - 10 = 490 viên                   │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. HÓA ĐƠN                                                       │
│    InvoiceLine: quantity=10, unit="viên", unit_price=5000/viên  │
├─────────────────────────────────────────────────────────────────┤
│ Dòng tiền: 10 viên × 5000 = 50.000 VND                          │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. CẢNH BÁO TỒN                                                  │
│    Ngưỡng cảnh báo: 50 viên (tính theo base_unit)               │
├─────────────────────────────────────────────────────────────────┤
│ Nếu actual_quantity < 50 → cảnh báo "Tồn thấp"                  │
│ (so sánh luôn theo base_unit, KHÔNG quy đổi)                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | **Quản lý thuốc & định nghĩa quy đổi (Admin)** | Admin tạo/chỉnh sửa Medicine: chọn base_unit (vd: viên), chọn sell_unit (vd: viên), tạo bảng quy đổi (vd: "1 thùng = 100 viên"). Dữ liệu lưu vào `Medicine`, `unit_conversion`. |
| 2 | **Nhập kho** | Nhân viên nhập kho với purchase_unit (thùng). Hệ thống dùng `unit_conversion` (thùng→viên) + `pack_size` để tính qty_base, lưu vào Batch.actual_quantity theo base_unit. |
| 3 | **Kê đơn** | Bác sĩ nhập số lượng theo sell_unit (ví dụ: "10 viên"). Hệ thống dùng resolver quy đổi sang base_unit, kiểm tra tồn, tạo reservation. PrescriptionItem lưu sell_unit + qty. |
| 4 | **Cấp phát (Dispense)** | Dược sĩ xác nhận cấp. Hệ thống trừ kho: `Batch.actual_quantity -= reserved_qty_in_base`. Hiển thị cấp theo sell_unit. |
| 5 | **Hóa đơn** | InvoiceLine lấy snapshot: qty + unit + unit_price từ PrescriptionItem (gọi là sell values). Tính doanh thu: qty × unit_price. |
| 6 | **Cảnh báo tồn** | Hệ thống so sánh `Batch.actual_quantity` (base_unit) với ngưỡng → phát cảnh báo nếu cần. Ngưỡng LUÔN tính theo base_unit. |

---

## 3. Mô hình dữ liệu

### 3.1 Bảng `unit_conversion` (mới)

**Mục đích:** Lưu trữ hệ số quy đổi giữa hai đơn vị của một thuốc.

**Cấu trúc:**

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | BIGINT | Có | Khóa chính, tự tăng |
| `clinic_id` | BIGINT | Không | FK → clinic (NULLABLE, cho phép global rows). Nếu NULL = global; nếu có = chỉ clinic đó dùng. |
| `medicine_id` | BIGINT | Có | FK → medicine `ON DELETE CASCADE`. Mỗi thuốc có nhiều quy đổi. |
| `from_unit` | VARCHAR(50) | Có | Đơn vị nguồn (ví dụ: "thùng", "hộp", "viên"). |
| `to_unit` | VARCHAR(50) | Có | Đơn vị đích (ví dụ: "viên", "ml"). |
| `factor` | NUMERIC(18, 6) | Có | Hệ số: `1 from_unit = factor × to_unit`. Ví dụ: `1 thùng = 100 viên` → factor = 100. ALWAYS > 0. |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo. |
| `updated_at` | TIMESTAMP | Có | Thời điểm cập nhật. |

**Ràng buộc:**
- **PRIMARY KEY:** `(id)`
- **UNIQUE:** `(medicine_id, from_unit, to_unit)` — mỗi cặp (thuốc, từ_unit, tới_unit) chỉ có một hệ số.
- **CHECK:** `factor > 0` — hệ số luôn dương.
- **FK:** `medicine_id` → `medicine.id` ON DELETE CASCADE.

**Backfill (Migration 0070):**
- Mỗi thuốc có ít nhất một hàng: `base_unit → base_unit`, factor = 1.
- Nếu thuốc có `purchase_unit` khác `base_unit` và `pack_size > 0`: thêm hàng `purchase_unit → base_unit`, factor = `pack_size`.
- `clinic_id` = lấy từ `medicine.clinic_id`.

### 3.2 Cột mới trên `Medicine`

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|-------------|---------|-------|-----------------|
| `sell_unit` | VARCHAR(50) | Có | Đơn vị bán (ví dụ: "viên", "ml", "vỉ"). Sử dụng khi kê đơn, cấp phát, hóa đơn. | = `base_unit` (ORM INSERT-time default) |
| `dosage_form_id` | BIGINT | Không | FK → dosage_form.id (nếu null = dùng free-text `dosage_form` cũ). Giúp gợi ý sell_unit mặc định. | NULL |

**Thay đổi:**
- `dosage_form_id` **đã tồn tại** trên `origin/dev` (thêm bởi migration 0061) — KHÔNG cần thêm lại.
- `sell_unit` thêm mới, có server-level ORM default = `base_unit` để backward-compat.

---

## 4. Resolver (Dịch vụ quy đổi đơn vị)

### 4.1 Dịch vụ `unit_service.py`

**Mục đích:** Cung cấp các hàm quy đổi định lượng giữa các đơn vị.

#### Hàm chính

**`to_base(medicine: Medicine, qty: Decimal, unit: str) -> Decimal`**

Quy đổi số lượng từ một đơn vị bất kỳ sang base_unit.

```python
# Ví dụ:
med = get_medicine(id=1)  # base_unit = "viên", sell_unit = "viên"
qty_base = to_base(med, Decimal("5"), "vỉ")
# Nếu có conversion "vỉ → viên" factor=10 → qty_base = 50
```

**Logic:**
1. Nếu `unit == base_unit` hoặc `unit` rỗng → trả `qty` nguyên (không quantize).
2. Nếu `unit == base_unit` (byte-for-byte) → trả `qty` (factor = 1, không cần convert).
3. Tìm conversion row: `(medicine_id, from_unit=unit, to_unit=base_unit)`.
4. Nếu tìm được → `result = qty × factor`, quantize ROUND_HALF_UP tại 6 decimal places.
5. Nếu không tìm thấy → raise `UnitConversionError`.

**`from_base(medicine: Medicine, base_qty: Decimal, unit: str) -> Decimal`**

Quy đổi từ base_unit sang một đơn vị khác (inverse của `to_base`).

```python
# Ví dụ:
med = get_medicine(id=1)
qty_vials = from_base(med, Decimal("50"), "vỉ")
# Nếu "vỉ → viên" factor=10 → qty_vials = 5
```

**Logic:** Tìm conversion row `(medicine_id, from_unit=unit, to_unit=base_unit)`, chia base_qty cho factor, quantize ROUND_HALF_UP 6dp.

**`conversions_for(medicine: Medicine) -> dict[(from_unit, to_unit), factor]`**

Lấy tất cả quy đổi của một thuốc dưới dạng dict.

**`base_per_unit(medicine: Medicine, unit: str) -> Decimal`**

Trả về hệ số base_unit trên 1 unit. Ví dụ: nếu "vỉ → viên" factor=10 → `base_per_unit(..., "vỉ") = 10`.

### 4.2 Quy tắc làm tròn

- **Khi convert sang base_unit:** `ROUND_HALF_UP` at 6 decimal places (ví dụ: 5 × 0.333333 = 1.666665 → 1.666665, không làm tròn).
- **Khi sử dụng để reserve/dispense:** Dùng giá trị đã quantize từ bước trên (ví dụ: base_qty = 1.666665 được dùng để reserve).
- **Khi cấp phát (dispense):** Không re-convert, dùng luôn reserved_quantity đã lưu.
- **Khi tính tiền:** Không làm tròn (dùng Decimal chính xác), chỉ hiển thị tròn khi cần (2 decimal cho VND).

### 4.3 Backward Compatibility (Backfill)

Mọi Medicine có `sell_unit == base_unit` và `factor = 1` đều:
- Không qua quantize (short-circuit trước).
- Trả về qty **nguyên bản không đổi**.
- Số lượng reserve/dispense = số lượng kê = số lượng trừ kho (byte-for-byte như trước).

---

## 5. Danh sách API

**Đường dẫn gốc:** `/api/v1`  
**Xác thực:** Bắt buộc (Bearer token)  
**Phạm vi phòng khám:** Tất cả API được scoped theo `clinic_id` từ token.

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt | Quyền |
|-----|------------|-----------|--------------|-------|
| 1 | POST | `/medicines` | Tạo thuốc (bao gồm sell_unit) | medicine.manage |
| 2 | PATCH | `/medicines/{id}` | Chỉnh sửa thuốc (bao gồm sell_unit) | medicine.manage |
| 3 | GET | `/medicines/{id}/unit-conversions` | Liệt kê quy đổi của thuốc | medicine.read |
| 4 | POST | `/medicines/{id}/unit-conversions` | Tạo hàng quy đổi | medicine.manage |
| 5 | PATCH | `/medicines/{id}/unit-conversions/{conversion_id}` | Cập nhật hàng quy đổi | medicine.manage |
| 6 | DELETE | `/medicines/{id}/unit-conversions/{conversion_id}` | Xóa hàng quy đổi | medicine.manage |
| 7 | GET | `/medicines/search` | Tìm kiếm thuốc (trả sell_unit + conversions[]) | medicine.read |

Chi tiết xem mục [5. Chi tiết từng API](#5-chi-tiết-từng-api) trong `unit-conversion-api.md`.

---

## 6. Cấu trúc cơ sở dữ liệu

### 6.1 Tổng quan bảng

| Bảng | Mục đích | Phạm vi | Ghi chú |
|------|---------|---------|--------|
| `medicine` | Định nghĩa loại thuốc | clinic_id | Thêm cột: `sell_unit`, `dosage_form_id` |
| `unit_conversion` | Hệ số quy đổi giữa các đơn vị | clinic_id (nullable) | Mới, unique (medicine_id, from_unit, to_unit) |
| `batch` | Lô thuốc tồn kho | clinic_id | Không thay đổi, `actual_quantity` vẫn tính theo base_unit |
| `prescription_item` | Dòng kê đơn | clinic_id | Không thay đổi, `unit` vẫn là sell_unit snapshot |
| `invoice_line` | Dòng hóa đơn | clinic_id | Không thay đổi, `unit` + `quantity` + `unit_price` = sell values |

### 6.2 Chi tiết bảng `unit_conversion`

**Script tạo bảng (Migration 0070):**

```sql
CREATE TABLE unit_conversion (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    clinic_id BIGINT NULLABLE,
    medicine_id BIGINT NOT NULL,
    from_unit VARCHAR(50) NOT NULL,
    to_unit VARCHAR(50) NOT NULL,
    factor NUMERIC(18, 6) NOT NULL CHECK (factor > 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_unit_conversion (medicine_id, from_unit, to_unit),
    FOREIGN KEY fk_unit_conversion_medicine (medicine_id) 
        REFERENCES medicine(id) ON DELETE CASCADE,
    FOREIGN KEY fk_unit_conversion_clinic (clinic_id) 
        REFERENCES clinic(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- RLS Policy:
-- SELECT: clinic_id IS NULL OR clinic_id = current_clinic_id
-- INSERT/UPDATE/DELETE: clinic_id = current_clinic_id
```

---

## 7. Chi tiết luồng nghiệp vụ

### 7.1 Luồng nhập kho (Purchase In)

**Tham gia:** `purchase_in_service.py`

1. **Nhập dữ liệu:** Nhân viên nhập `pack_quantity` (ví dụ: 5) với `purchase_unit` (thùng).
2. **Tính base_qty:**
   - Nếu có conversion row `(purchase_unit → base_unit)`: dùng resolver `to_base(..., purchase_unit, pack_quantity)`.
   - Nếu không → fallback `pack_size` (legacy logic).
   - Kết quả: `actual_qty_base = 500 viên`.
3. **Lưu Batch:** `batch.actual_quantity = 500` (base_unit), `batch.unit = base_unit`.

### 7.2 Luồng kê đơn (Prescribe)

**Tham gia:** `prescription_service.py`, `medicine_search_service.py`

1. **Tìm kiếm thuốc:** API trả về `medicine` với thêm field:
   - `sell_unit = "viên"`
   - `conversions[] = [{from_unit: "vỉ", to_unit: "viên", factor: 10}, ...]`
2. **Bác sĩ kê:** Nhập `quantity = 10` với `unit = "viên"` (mặc định = sell_unit).
3. **Hệ thống xử lý:**
   - Gọi resolver: `to_base(medicine, 10, "viên") = 10 viên` (factor = 1).
   - Kiểm tra tồn: có >= 10 viên trong Batch không?
   - Tạo reservation: dành riêng 10 viên từ Batch (gọi là `reserved_quantity_in_base`).
4. **Lưu PrescriptionItem:**
   - `quantity = 10` (sell)
   - `unit = "viên"` (sell)
   - `unit_price = med.sale_price = 5000` (per viên = per sell_unit)

### 7.3 Luồng cấp phát (Dispense)

**Tham gia:** `dispense_service.py`, `pharmacy_service.py`

1. **Xác nhận cấp:** Dược sĩ nhấn cấp trên đơn (hiển thị "10 viên").
2. **Hệ thống trừ kho:**
   - Tìm hàng reserve trong `prescription_item_batch`: `reserved_qty_in_base = 10 viên`.
   - Giảm batch: `batch.actual_quantity -= 10` → từ 500 → 490 viên.
3. **Ghi nhận cấp:** `dispense_record` lưu `dispensed_quantity = 10` (sell), `unit = "viên"`.

### 7.4 Luồng hóa đơn (Billing)

**Tham gia:** `invoice_service.py`

1. **Kéo dữ liệu từ visit:** API lấy tất cả `prescription_item` của visit.
2. **Với mỗi item:**
   - `invoice_line.quantity = 10` (lấy từ prescription_item, đơn vị sell)
   - `invoice_line.unit = "viên"` (lấy từ prescription_item, sell_unit)
   - `invoice_line.unit_price = 5000` (per viên = per sell_unit)
   - `line_total = 10 × 5000 = 50.000 VND`
3. **Tổng hóa đơn:** Sum của tất cả `line_total`.

**Ghi chú:** Không cần thay đổi logic invoice — đã lưu snapshot giá trị sell từ lúc kê.

### 7.5 Luồng cảnh báo tồn (Low Stock Alert)

**Tham gia:** `alert_service.py` (không thay đổi logic, chỉ thêm ghi chú)

1. **Kiểm tra:** So sánh `batch.actual_quantity` (base_unit) với ngưỡng `medicine.low_stock_threshold` (base_unit).
2. **Phát cảnh báo:** Nếu actual_quantity < threshold → cảnh báo **"Tồn thấp"**.
3. **Quy tắc:** Ngưỡng LUÔN tính theo base_unit, **KHÔNG quy đổi** sang sell_unit.
   - Ví dụ: base_unit=viên, threshold=50 viên. Nếu sell_unit=vỉ (10 viên/vỉ), ngưỡng vẫn là 50 viên, không phải 5 vỉ.

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-001 | Mỗi thuốc có ít nhất một quy đổi `base_unit → base_unit` với factor = 1 (backfill mặc định). | Migration đảm bảo; API không cho phép xóa hàng này. |
| BR-002 | Mỗi cặp `(medicine_id, from_unit, to_unit)` chỉ có một hàng quy đổi (unique constraint). | API trả 409 Conflict nếu cố tạo duplicate. |
| BR-003 | Factor phải luôn > 0 (không cho factor ≤ 0). | API schema validate + DB CHECK constraint. Trả 400 Bad Request nếu vi phạm. |
| BR-004 | Bác sĩ kê đơn bằng `sell_unit` (mặc định); hệ thống tự quy đổi sang `base_unit` để kiểm tra tồn. | Nếu không có conversion row → UnitConversionError, hiển thị lỗi cho người dùng. |
| BR-005 | Khi `sell_unit == base_unit` (backfill), quy đổi trả về qty nguyên bản, KHÔNG quantize. | Đảm bảo backward-compat: số lượng kê/cấp/HĐ = số lượng trừ kho. |
| BR-006 | Ngưỡng cảnh báo tồn luôn tính theo `base_unit`, không bao giờ quy đổi sang `sell_unit`. | Giao diện admin hiển thị cảnh báo dưới label "Đơn vị tồn" (base_unit), không confuse với sell_unit. |
| BR-007 | Giá `sale_price` trên Medicine = giá/sell_unit (không phải giá/base_unit). Nếu sell_unit thay đổi, admin phải cập nhật sale_price. | Nếu thay sell_unit nhưng không cập sale_price → giá sẽ sai trên hóa đơn. Ghi chú cho admin. |
| BR-008 | Nếu kê đơn với free-text unit (bác sĩ override) không khớp với sell_unit → hệ thống cố gắng tìm conversion. Nếu không tìm → xử lý như legacy (coi là base_unit). | Không lỗi, chỉ log cảnh báo. Ensure backward-compat với đơn cũ. |

---

## 9. Xử lý lỗi

### 9.1 Các mã lỗi phổ biến

| Mã HTTP | Mã lỗi | Tình huống xảy ra | Thông báo trả về |
|---------|--------|-------------------|-----------------|
| 400 | INVALID_REQUEST | Tham số không hợp lệ (ví dụ: factor ≤ 0, unit rỗng). | "Yêu cầu không hợp lệ: factor phải > 0." |
| 404 | NOT_FOUND | Không tìm thấy thuốc hoặc quy đổi theo ID. | "Không tìm thấy thuốc hoặc quy đổi." |
| 409 | CONFLICT | Cố tạo quy đổi trùng (medicine_id, from_unit, to_unit đã tồn tại). | "Quy đổi này đã tồn tại. Vui lòng cập nhật hoặc xóa bản hiện tại." |
| 422 | VALIDATION_ERROR | Dữ liệu không hợp lệ theo schema (ví dụ: from_unit = to_unit). | "Đơn vị gốc và đơn vị đích phải khác nhau." |
| 500 | UNIT_CONVERSION_ERROR | Không tìm thấy conversion để quy đổi khi kê đơn. | "Không có quy đổi từ [unit] sang [base_unit]. Vui lòng kiểm tra lại." |

### 9.2 Định dạng phản hồi lỗi

```json
{
  "code": "UNIT_CONVERSION_ERROR",
  "message": "Không có quy đổi từ 'vỉ' sang 'viên' cho thuốc này."
}
```

---

## 10. Ghi chú kiểm thử & Backward Compatibility

### 10.1 Điểm quan trọng cần nắm

- **Backward Compatibility (BCP):** Mọi thuốc có `sell_unit == base_unit` (factor = 1) đều ứng xử y hệt như trước, byte-for-byte. Không có số lượng nào thay đổi trong kê/cấp/HĐ.
- **Thay đổi hành vi:** Chỉ khi `sell_unit != base_unit` với conversion row. Lúc đó, hệ thống mới quy đổi trong nội bộ (reserve/dispense base_unit), nhưng giao diện + HĐ vẫn hiển thị sell_unit.
- **dosage_form_id:** Đã tồn tại từ TASK-093, chỉ là dùng để gợi ý sell_unit mặc định — không bắt buộc.
- **Ngưỡng cảnh báo:** Vẫn tính theo base_unit, không quay trở lại nữa. Phạm vi cảnh báo không nằm trong TASK-124.
- **Giá:** Nếu admin thay sell_unit của 1 thuốc, **phải cập nhật `sale_price` tương ứng.** Giao diện admin phải cảnh báo điều này.

### 10.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **Backward-compat (sell==base)** | Thuốc A: base="viên", sell="viên", factor=1. Kê 10 viên. | Reserve 10, cấp 10, HĐ 10 viên, trừ kho 10 viên. Byte-for-byte như cũ. |
| **Divisible (ml→lọ)** | Thuốc B: base="ml", sell="lọ", 1 lọ=20ml (factor=20). Kê 2.5 lọ. | Reserve 50 ml, cấp 2.5 lọ, HĐ 2.5 lọ × 5000/lọ=12.500, trừ kho 50 ml. |
| **Discrete (vỉ→viên)** | Thuốc C: base="viên", sell="vỉ", 1 vỉ=10 viên (factor=10). Kê 3 vỉ. | Reserve 30 viên, cấp 3 vỉ, HĐ 3 vỉ × 30.000/vỉ=90.000, trừ kho 30 viên. |
| **Rounding (ROUND_HALF_UP)** | Thuốc D: base="ml", sell="ống", factor=0.333333 (3 ống=1ml). Kê 5 ống. | base_qty = 5 × 0.333333 = 1.666665 ml (quantized), reserve 1.666665 ml. |
| **Admin CRUD** | POST `/medicines/1/unit-conversions` với factor=0 (hoặc -5). | 400 Bad Request: "factor phải > 0". |
| **Duplicate prevent** | POST `/medicines/1/unit-conversions` với cùng (from="vỉ", to="viên") 2 lần. | Lần 1 OK; lần 2: 409 Conflict. |
| **Cross-clinic isolation** | Admin clinic B cố GET `/medicines/1/unit-conversions` (medicine thuộc clinic A). | 404 Not Found (không leak sang clinic khác). |
| **Cảnh báo tồn** | Thuốc E: base="hộp", threshold=5 hộp, sell="viên" (1 hộp=100 viên). Tồn còn 3 hộp. | Cảnh báo "Tồn thấp" (so sánh 3 < 5 theo hộp, không đổi sang viên). |

### 10.3 Hạn chế hiện tại

- **Quy đổi không chained tự động:** Nếu A→B và B→C, hệ thống không tự quy đổi A→C. Phải khai báo explicit A→C row.
- **dosage_form_id backfill sót:** Backfill bằng match tên; nếu DosageForm hoặc tên sai → null, dùng fallback free-text.
- **Server default của sell_unit:** ORM default =base_unit, nhưng raw-SQL INSERT cần thêm `sell_unit` tường minh (không có DB server_default). Dự định fix bằng trigger/server_default sau.
- **Precision trong report COGS:** Nếu hệ số lẻ (như ml→lọ), COGS tính bằng base×unit_cost có thể khác 1 phần triệu so với nếu tính bằng sell×price_per_sell. Chấp nhận được do độ chính xác Decimal(18,6).

### 10.4 Hướng phát triển (Follow-up)

- **Server default của sell_unit:** Migration thêm BEFORE-INSERT trigger hoặc ALTER TABLE ... DEFAULT.
- **Quy đổi chained:** Implement resolver multipath search (DFS/BFS) để tìm chuỗi quy đổi từ unit A → base.
- **Audit trail:** Ghi lại ai, khi nào thay đổi conversion row (cho compliance).
- **Bulk import/export:** Template Excel để admin nhập batch quy đổi.

---

**Phê duyệt & Trạng thái**

| Vai trò | Họ tên | Ngày | Trạng thái |
|---------|--------|------|-----------|
| **Người triển khai** | Development Team | 2026-07-27 | ✅ Hoàn thành |
| **Code Review** | Code Review Agent | 2026-07-27 | ✅ APPROVED (Phase 1/2/3) |
| **Testing** | Test Agent | 2026-07-27 | ✅ PASSED (302/312 BE, FE 8/8 FE + full suite 1118/1122) |
| **Documentation** | Documentation Agent | 2026-07-27 | ✅ Functional Design + API Spec |

---

**Version 1.0 — 2026-07-27**

Hoàn thành. TASK-124 từ Planning → Implementation → Review → Testing → Documentation. Tất cả phase (1–3) APPROVED và TESTED.
