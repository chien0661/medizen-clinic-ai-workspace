# Thiết Kế Chức Năng — Đơn Thuốc & Danh Mục Thuốc

**Task:** TASK-011 — Medicine Catalog + Prescription (In-House / External Mixed)  
**Ngày cập nhật:** 2026-04-27  
**Trạng thái:** DONE  
**Branch:** `feature/task-011-prescriptions`

---

## 1. Tổng Quan

Module quản lý đơn thuốc cho phép bác sĩ kê đơn thuốc từ kho nội bộ phòng khám (in-house) hoặc kê thuốc mua ngoài (external). Một đơn có thể chứa cả hai loại (mixed).

### Luồng chính

```
Bác sĩ tìm kiếm thuốc
        ↓
Kiểm tra tồn kho tự động (auto-suggest source)
        ↓
Tạo đơn thuốc (draft) + thêm item
        ↓
Nộp đơn (pending) → Dược sĩ nhận
        ↓
Cấp phát (dispensed) ← TASK-012 pharmacy
```

---

## 2. Danh Mục Thuốc (Medicine Catalog)

### 2.1 Nguồn dữ liệu

- Dữ liệu thuốc lưu tại bảng `medicine` (TASK-012)
- Mỗi phòng khám tự quản lý danh mục thuốc của mình (multi-tenant)
- Trường `is_in_house = true` → thuốc có thể cấp phát từ kho nội bộ

### 2.2 Tìm kiếm thuốc

**Endpoint:** `GET /api/v1/medicines/search?q=paracetamol&with_stock=true`

- Tìm kiếm full-text (ILIKE) theo: `name`, `generic_name`, `brand_name`, `code`
- Kết quả kèm chỉ số tồn kho: `in_stock`, `available`, `batches_count`
- Thông tin tồn kho lấy từ view `v_inventory_status` (TASK-012)

---

## 3. Đơn Thuốc (Prescription)

### 3.1 Cấu trúc đơn thuốc

Một đơn thuốc (`prescription`) chứa nhiều dòng thuốc (`prescription_item`).

**Các trạng thái đơn:**
- `draft` — Đơn đang soạn (mặc định khi tạo)
- `pending` — Đã nộp, chờ dược sĩ cấp phát
- `dispensed` — Đã cấp phát
- `cancelled` — Đã hủy

### 3.2 Loại dispense_type

Được tự động tính từ tổng hợp các item:

| Điều kiện | dispense_type |
|---|---|
| Tất cả item là in_house | `in_house` |
| Tất cả item là external | `external` |
| Có cả hai | `mixed` |

### 3.3 Quy tắc nghiệp vụ

1. **Tạo đơn:** Trạng thái khởi đầu luôn là `draft`
2. **Thêm item:** Có thể thêm vào đơn `draft` hoặc `pending` (không thêm vào `dispensed`/`cancelled`)
3. **Nộp đơn:** Yêu cầu ít nhất 1 item; tất cả item `in_house` phải có trạng thái `reserved`
4. **Hủy đơn:**
   - Chỉ hủy được đơn `draft` hoặc `pending`
   - Đơn `dispensed` → lỗi 409
   - Hủy tự động giải phóng tất cả reservation in_house

---

## 4. Cấp Phát Thuốc (Dispense Source)

### 4.1 Auto-suggest logic

Khi bác sĩ thêm thuốc vào đơn mà không chỉ định `dispense_source`:

```
Nếu medicine_id = NULL → external (bắt buộc)
Nếu medicine_id có giá trị:
  → Truy vấn v_inventory_status
  → available_qty >= quantity → suggest "in_house"
  → available_qty > 0 nhưng < quantity → suggest "external" + cảnh báo
  → available_qty = 0 → suggest "external"
```

Bác sĩ có thể override suggest bằng cách truyền `dispense_source` trong request.

### 4.2 Reservation In-house

Khi item được thêm với `dispense_source = "in_house"`:

1. Gọi `reservation_service.reserve_for_prescription()` (TASK-012)
2. Phân bổ theo FEFO (First Expired First Out)
3. Tạo bản ghi `prescription_item_batch` liên kết item → batch
4. Cập nhật `batch.reserved_quantity`
5. Item có `in_house_status = "reserved"`

### 4.3 Giải phóng reservation

Khi:
- Hủy đơn (cancel)
- Xóa item in_house
- Chuyển item từ in_house → external

→ Gọi `reservation_service.release_reservation()` (TASK-012)
→ Giảm `batch.reserved_quantity`
→ Item có `in_house_status = "released"`

---

## 5. In Đơn Thuốc

### 5.1 Các chế độ in

| mode | Mô tả |
|---|---|
| `all` | In tất cả thuốc (cả nội và ngoại) |
| `external_only` | Chỉ in thuốc mua ngoài (bệnh nhân ra hiệu thuốc) |
| `ask` | Trả về câu hỏi cho FE chọn chế độ |

### 5.2 Nội dung đơn thuốc

Template HTML bao gồm:
- Header: Tên phòng khám, địa chỉ, SĐT
- Thông tin bác sĩ, ngày kê đơn, mã đơn
- Bảng thuốc: tên, liều dùng, số lượng, đơn vị, nguồn (in_house/external)
- Chữ ký bác sĩ

---

## 6. Quyền Truy Cập

| Endpoint | Permission |
|---|---|
| GET /medicines/search | `medicine.read` |
| POST /visits/{id}/prescriptions | `prescription.write` |
| GET /prescriptions/{id} | `prescription.read` |
| PATCH /prescriptions/{id} | `prescription.write` |
| POST /prescriptions/{id}/items | `prescription.write` |
| PATCH /prescription-items/{id} | `prescription.write` |
| DELETE /prescription-items/{id} | `prescription.write` |
| POST /prescriptions/{id}/submit | `prescription.write` |
| POST /prescriptions/{id}/cancel | `prescription.cancel` |
| GET /prescriptions/{id}/print | `prescription.print` |

---

## 7. Bảo Mật Multi-tenant

- RLS (Row Level Security) bật trên tất cả bảng: `prescription`, `prescription_item`
- Policy: `clinic_id::text = current_setting('app.current_clinic_id', true)`
- Không thể truy cập dữ liệu của phòng khám khác ngay cả khi biết ID

---

## 8. Tích Hợp Module Khác

| Module | Tương tác |
|---|---|
| **TASK-012 Inventory** | Đọc `v_inventory_status` cho auto-suggest |
| **TASK-012 Pharmacy** | Gọi `reservation_service.reserve_for_prescription()` và `release_reservation()` |
| **TASK-013 Billing** | Đọc prescription.items để tạo invoice line items (unit_price) |
| **TASK-019 FE Doctor** | Stub API để kê đơn |
| **TASK-020 FE Pharmacy** | Stub API để xem và cấp phát đơn |

---

## 9. Acceptance Criteria — Xác Nhận

| AC | Kết quả |
|---|---|
| AC1: Mixed prescription (2 in_house + 1 external) → `dispense_type='mixed'` | ✅ PASS |
| AC2: Search medicine với inventory flag `in_stock` | ✅ PASS |
| AC3: qty > available → cảnh báo + suggest external | ✅ PASS |
| AC4: Cancel dispensed → 409; cancel pending → 200 + release reservation | ✅ PASS |
| AC5: Print 3 modes (all/external_only/ask) | ✅ PASS |
| Tenant isolation | ✅ PASS |
| Permission gating | ✅ PASS |
| Concurrent reservation | ✅ PASS |

---

_Tài liệu này được tạo bởi TASK-011 Implementation Agent._
