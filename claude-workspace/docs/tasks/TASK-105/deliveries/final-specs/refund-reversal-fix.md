# TASK-105: Refund đảo tiền đã thu, khôi phục sự nhất quán giữa payment-methods và revenue

**Mức độ:** High (H-3)  
**Ngày hoàn thành:** 2026-07-24  
**Trạng thái:** DONE (81/81 tests passed)

---

## Vấn đề

**Mâu thuẫn dữ liệu:** Khi refund hóa đơn đã thanh toán, tiền không được đảo ngược.

- `refund_invoice()` chỉ set `status='refunded'` + release stock; `paid_total` giữ nguyên, payment `is_voided=FALSE`.
- `payment_method_service.get_payment_method_breakdown()` cộng all payment không-void mà **không join** status hóa đơn → tiền hoàn vẫn "đã thu" mãi mãi.
- `revenue_service.get_revenue()` lọc `status IN ('paid','partially_paid')` → **loại** hóa đơn refunded → số tiền không được tính.
- **Kết quả:** Payment-methods report = 220,000 (gồm tiền hoàn); revenue report = 0 (loại tiền hoàn) → **không khớp**.
- **Tắc:** `void_payment()` **từ chối** chạy trên hóa đơn `refunded` (lỗi: `"Cannot void payment on a {status} invoice."`) → không có cách nào sửa lại sau khi đã hoàn.

**Bằng chứng:**
```
Invoice A refunded, paid_total=220,000
Payment A: is_voided=FALSE
payment-methods total: 220,000 ✗
revenue total: 0 ✓
→ Không khớp (220k - 0k)
```

---

## Giải pháp: Approach A — Void payments trong refund_invoice

**Chọn A vì:**

1. **Single point of change:** `payment_method_service` không cần sửa — filter `is_voided=FALSE` + khi refund void payments thì report tự đúng. Không cần join/subquery mới.
2. **Invoice consistent:** `paid_total`/`balance_due` trên hóa đơn refunded giờ = 0/grand_total (không còn số tiền stale). `void_payment`'s refusal trên refunded giờ make sense (không còn gì để void).
3. **Reuse tested logic:** Refund gọi `payment_service._recalculate_invoice_paid_total()` — **cùng helper** `void_payment` dùng → arithmetic derived identically.
4. **Partial refund:** Không áp dụng (refund chỉ accept status `'paid'`, không `'partially_paid'`).

**Reject B** vì để `paid_total` sai vĩnh viễn trên invoice + phải apply lại tất cả nơi sum payment rows.

---

## Thay đổi

**File:** `app/modules/billing/services/invoice_service.py`  
**Hàm:** `refund_invoice()`

```python
# 1. Load all active payments
payments = session.query(Payment).filter(
    Payment.invoice_id == invoice.id,
    Payment.is_voided == False,
    Payment.is_deleted == False
).all()

# 2. Void each payment (mirrors void_payment logic)
for payment in payments:
    payment.is_voided = True
    payment.voided_at = datetime.now()
    payment.void_reason = f"Refund: {reason}"
    payment.updated_by = refunded_by
    session.add(payment)

# 3. Set invoice refunded
invoice.status = 'refunded'
invoice.refunded_at = datetime.now()
invoice.refund_reason = reason
session.add(invoice)

# 4. Recalculate paid_total/balance_due
from app.modules.billing.services.payment_service import _recalculate_invoice_paid_total
_recalculate_invoice_paid_total(invoice, payments)

# 5. Commit
session.commit()
log.info("invoice_refunded", ..., payments_voided=len(payments))
```

**Kho thay đổi:**
- `invoice_service.py` (+49 lines, `refund_invoice` only)
- `test_billing_e2e.py` (+103 lines, 1 test mới)

---

## Kết quả

**Tests:**
- `test_refund_reverses_collected_money`: Refund → payment voided, paid_total=0, payment-methods tính đúng, == revenue ✓
- Billing + Reports suites: 81/81 passed (isolated stack `fix105`, ports 9978/5478/6460).
- Ruff/mypy: 0 new findings (2 fewer ruff issues than baseline).

**Xác minh nhất quán:**
```
Before fix:
  Invoice A (paid 220k, refunded) → payment.is_voided=FALSE
  payment-methods: 220,000 ✗
  revenue: 0 ✓
  → Mismatch

After fix:
  Invoice A (refunded) → payment.is_voided=TRUE
  payment-methods: 0 ✓
  revenue: 0 ✓
  → Match! Sự nhất quán khôi phục
```

---

## Ghi chú

- Không thay đổi `payment_method_service`, `revenue_service`, `payment_service`.
- `void_payment`'s refusal trên `refunded` invoice giờ **make sense** (không còn gì void).
- `double-void` (re-void refund-voided payment) đúng cách bị chặn → 400.

---

## Xác minh

| Tiêu chí | Kết quả |
|----------|---------|
| Unit + Integration tests | 81/81 passed ✓ |
| Refund voids payment | is_voided=TRUE ✓ |
| paid_total reset | 0 (not grand_total) ✓ |
| payment-methods == revenue | Cùng dữ liệu, cùng tổng ✓ |
| Double-void blocked | HTTP 400 ✓ |
| Static analysis | 0 new findings ✓ |
| Isolated stack | w105 (api 9978, postgres 5478, redis 6460) ✓ |
