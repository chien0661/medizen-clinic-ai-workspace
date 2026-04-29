# Thiết Kế Chức Năng — Module Billing
## TASK-013: Hóa Đơn + Đa Thanh Toán + Chiết Khấu + Hủy/Hoàn Tiền

> **Phiên bản:** 1.0 | **Ngày:** 2026-04-27 | **Trạng thái:** DONE
> **Thay thế:** Tài liệu thiết kế §13 trong clinic_management_system_design.md

---

## 1. Tổng Quan

Module Billing quản lý toàn bộ quy trình thanh toán trong phòng khám:
- **Tự động tạo hóa đơn** từ lượt khám (visit_service + prescription_item in_house)
- **Đa thanh toán** (nhiều lần thanh toán cho 1 hóa đơn, nhiều phương thức)
- **Chiết khấu** theo dòng với yêu cầu lý do
- **Hủy hóa đơn** (void) cho trường hợp chưa hoàn tất hoặc sai
- **Hoàn tiền** (refund) cho hóa đơn đã thanh toán + giải phóng dự trữ kho thuốc

---

## 2. Quy Trình Nghiệp Vụ

### 2.1. Tạo Hóa Đơn Tự Động

```
Lượt khám (Visit)
       │
       ▼
Gọi POST /visits/{visit_id}/invoices
       │
       ▼
invoice_service.create_from_visit()
  ├── Kiểm tra hóa đơn đã tồn tại → 409 nếu trùng
  ├── Tạo invoice header (status = draft)
  ├── Đọc visit_service (completed services) → thêm lines loại "service"
  ├── Đọc prescription_item (in_house, not cancelled) → thêm lines loại "medicine"
  └── Tính tổng subtotal + grand_total
```

**Snapshot giá:** Giá lúc xuất hóa đơn được lấy từ `unit_price` của `visit_service` và `prescription_item`. Thay đổi catalog sau này không ảnh hưởng hóa đơn đã tạo.

### 2.2. Nộp Hóa Đơn

```
draft ──[submit]──► issued
```

- Kiểm tra có ít nhất 1 dòng
- Gọi `fn_next_invoice_number()` để cấp số hóa đơn (`INV-YYYYMMDD-NNN`)
- Đặt `issued_at = now()`
- Sau khi submitted, **không thể sửa dòng hóa đơn** nữa

### 2.3. Thanh Toán Nhiều Lần

```
issued ──[payment]──► partially_paid ──[payment = balance]──► paid
   └────────────────────────────────────────────────────────────┘
```

- Mỗi lần thanh toán cộng vào `paid_total`
- Tính `balance_due = grand_total - paid_total`
- Quá ngưỡng `grand_total` → từ chối (không cho phép trả thừa)

### 2.4. Hủy Hóa Đơn (Void)

```
issued / partially_paid ──[void]──► void
```

- Yêu cầu: `void_reason`
- Đặt `voided_at = now()`
- **Không** giải phóng dự trữ kho thuốc (khác với refund)
- Sau khi void: không thể thêm thanh toán, không thể hoàn tiền

### 2.5. Hoàn Tiền (Refund)

```
paid ──[refund]──► refunded
```

- Yêu cầu: `refund_reason`
- Đặt `refunded_at = now()`
- **Giải phóng** tất cả dự trữ kho thuốc cho in_house items qua `pharmacy.release_reservation`
- Sau khi refunded: trạng thái terminal

### 2.6. Hủy Thanh Toán (Payment Void)

```
payment(active) ──[void_payment]──► payment(voided)
     └── tự động tính lại invoice.paid_total và status
```

- Đặt `payment.is_voided = true`
- Tính lại `invoice.paid_total` = tổng các payment active (chưa void)
- Status invoice có thể đổi: `paid` → `partially_paid` → `issued`

---

## 3. Cơ Máy Trạng Thái (State Machine)

### 3.1. Invoice Status

| Từ | Sự kiện | Đến | Điều kiện |
|---|---|---|---|
| `draft` | submit | `issued` | Có ≥1 dòng |
| `issued` | payment (amount < balance) | `partially_paid` | Invoice không bị void/refund |
| `issued` | payment (amount = balance) | `paid` | Invoice không bị void/refund |
| `partially_paid` | payment | `paid` hoặc `partially_paid` | |
| `issued` | void | `void` | Cần reason |
| `partially_paid` | void | `void` | Cần reason |
| `paid` | refund | `refunded` | Cần reason |

### 3.2. Trạng thái terminal
- `void`: không thể thêm payment, không thể refund
- `refunded`: trạng thái cuối, không thể thay đổi

---

## 4. Quy Tắc Chiết Khấu

1. Khi thêm dòng `discount` hoặc khi `discount_amount > 0`: **bắt buộc** có `discount_reason`
2. `discount_amount` không được vượt quá `unit_price * quantity`
3. Dòng `discount` có `line_total` âm → giảm `grand_total`
4. Phase 1: không có ngưỡng % chiết khấu bắt buộc reason (theo task gốc) — validation thuần Pydantic

---

## 5. Số Hóa Đơn

**Format:** `INV-YYYYMMDD-NNN`

- `YYYYMMDD`: ngày xuất hóa đơn theo UTC
- `NNN`: số thứ tự 3 chữ số, bắt đầu từ 001, reset mỗi ngày mỗi phòng khám
- Số được cấp qua SQL function `fn_next_invoice_number(clinic_id, date)`
- Chỉ cấp số khi submit (status draft có invoice_number = '')
- Duy nhất theo (clinic_id, invoice_number) khi is_deleted=false và invoice_number != ''

---

## 6. Tích Hợp Module Khác

### 6.1. TASK-010 — Visit Services
- Đọc `visit_service` table để lấy các dịch vụ đã thực hiện
- Snapshot: `service_name`, `quantity`, `unit_price`, `discount_amount`

### 6.2. TASK-011 — Prescriptions
- Đọc `prescription_item` với `dispense_source = 'in_house'` và prescription không bị cancelled
- Snapshot: `medicine_name`, `quantity`, `unit_price`

### 6.3. TASK-012 — Pharmacy/Inventory
- Khi refund: gọi `pharmacy.release_reservation(db, clinic_id, prescription_item_id)` cho tất cả items có `in_house_status = 'reserved'`
- **Void không gọi release** — chỉ refund mới release stock

---

## 7. Cấu Trúc Module

```
app/modules/billing/
├── __init__.py
├── api/
│   ├── __init__.py
│   └── routes.py          # 13 endpoints, permission-gated
├── models/
│   ├── __init__.py
│   ├── invoice.py         # Invoice model (BaseEntity)
│   ├── invoice_line.py    # InvoiceLine model (BaseEntity)
│   └── payment.py         # Payment model (BaseEntity)
├── schemas/
│   ├── __init__.py
│   └── invoice_schemas.py # Pydantic schemas + validators
└── services/
    ├── __init__.py
    ├── invoice_service.py # Invoice lifecycle + line management
    └── payment_service.py # Multi-payment + void logic
```

---

## 8. Bảo Mật & Cô Lập Tenant

- **RLS** trên cả 3 bảng (`invoice`, `invoice_line`, `payment`)
- Policy: `clinic_id::text = current_setting('app.current_clinic_id', true)`
- Người dùng một phòng khám không thể truy cập dữ liệu phòng khám khác
- `cms_app` role có `SELECT, INSERT, UPDATE, DELETE` trên cả 3 bảng

---

## 9. Giới Hạn Phase 1

- **Không có VAT/thuế** (`tax_total` luôn = 0)
- **Không có hóa đơn điện tử** (xuất hóa đơn điện tử → Phase 2)
- **In hóa đơn** chỉ là HTML template đơn giản (không phải PDF)
- **Void chỉ thay đổi status** (không tạo hóa đơn âm như BA gốc mô tả)
- **Partial refund không hỗ trợ** — refund là refund toàn bộ

---

## 10. Kiểm Thử (Test Coverage)

### Unit Tests (33 tests)
- Schema validation (9 tests): discount rules, payment method, void/refund schemas
- Totals calculation (7 tests): single/multi lines, discount lines, deleted lines, tax zero
- State machine (7 tests): payment totals, void status not changed, terminal statuses

### Integration Tests (31 tests)
- AC1: Tạo hóa đơn từ visit (2 tests — no visit_service table → empty invoice)
- AC2: Đa thanh toán partial → full (3 tests + concurrent payment test)
- AC3: Discount cần reason (2 tests)
- AC4: Void invoice (3 tests)
- AC5: Refund invoice (2 tests)
- Thêm: số hóa đơn sequential, tenant isolation, permission gating, print, list/filter

**Coverage:** 63% trên `app/modules/billing/` (services coverage giới hạn do thiếu visit_service table trong worktree)

---

## 11. Các Vấn Đề Đã Xử Lý

1. **MissingGreenlet (SQLAlchemy async)**: Thêm `await db.refresh(entity)` sau mỗi UPDATE flush để tránh sync load trên `updated_at` (server_default với `onupdate`).
2. **Unique index + draft invoice**: Index `uq_invoice_clinic_number` exclude `invoice_number = ''` để nhiều draft cùng clinic không conflict.
3. **Transaction abort khi query bảng chưa tồn tại**: Dùng savepoint (`await db.begin_nested()`) cho query `visit_service` và `prescription_item` trong `create_from_visit`.
4. **UUID cast asyncpg**: Migration 0007 cần `CAST(:id AS UUID)` cho fresh database.
