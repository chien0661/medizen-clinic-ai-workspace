---
id: TASK-119
type: bug
title: "[High] Hoàn thiện đảo chiều billing: void không đảo payment (H-6) + refund không hoàn kho/COGS (H-5)"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-25
updated: 2026-07-26
branch: "fix/TASK-119-billing-reversal"
tags: [billing, pharmacy, reports, data-integrity, financial, high, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (H-5, H-6)"
    - "docs/tasks/TASK-105 (refund payment reversal — precedent)"
    - "docs/tasks/TASK-112 (reopen_after_payment_reversal — reuse)"
---

# TASK-119: [High] Đảo chiều billing chưa hoàn thiện (H-6 void + H-5 refund→kho)

**Nguồn:** E2E re-run TASK-095, H-5 + H-6 (cùng `invoice_service` reversal → gộp 1 branch để tránh conflict).

## H-6 — `void_invoice` không đảo payment đã thu → tiền mồ côi, 3 báo cáo lệch
- `void_invoice` chỉ set `status='void'`, KHÔNG đụng payments/reservations. paid_total giữ nguyên, payment `is_voided=false`. payment_method_service (sum is_voided=false) TÍNH khoản đó, revenue_service (status paid/partially_paid) LOẠI → lệch đúng số tiền đã thu; đối soát 3 chiều mâu thuẫn.
- **Fix (mirror `refund_invoice`/TASK-105):** void đảo/void các payment active → paid_total→0, balance→0; giải phóng reservation in_house; gọi `reopen_after_payment_reversal` (COMPLETED→AWAITING_PAYMENT). Kết quả: payment-methods == revenue; không tiền mồ côi.
- File: `app/modules/billing/services/invoice_service.py` (`void_invoice` ~620), `reports/services/payment_method_service.py`, `revenue_service.py`.

## H-5 — refund sau khi đã cấp phát KHÔNG hoàn thuốc về kho + lệch COGS
- `refund_invoice` gọi `_release_pharmacy_reservations` chỉ lọc `pi.in_house_status='reserved'` / `pib.status='reserved'`; sau dispense cả hai = 'dispensed' → 0 dòng khớp → tồn không đụng. `dispense_service.undispense` tồn tại nhưng refund không gọi. profit COGS lọc `pib.status='dispensed'` → vẫn đếm khoản đã refund.
- **Fix:** `refund_invoice` (và void nếu đã dispense) phải gọi `undispense` cho item đã cấp → khôi phục `batch.actual_quantity` (+qty, movement 'return', pib.status→released) → COGS/profit đảo đúng.
- File: `invoice_service.py`, `pharmacy/services/reservation_service.py`, `dispense_service.py`, `reports/services/profit_service.py`.

## Acceptance Criteria
- [x] void HĐ đã thu tiền → payment voided, paid_total→0; payment-methods == revenue (đối soát 3 chiều nhất quán); reservation giải phóng; visit reopen.
- [x] refund/void HĐ đã dispense → tồn kho phục hồi (actual_quantity), COGS/profit đảo tương ứng; đơn không còn kẹt 'dispensed'.
- [x] Integration test: void-đã-thu, refund-đã-dispense, đối soát report; không hồi quy refund path (TASK-105).

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Documentation Completed
2026-07-26 — Final spec: `deliveries/final-specs/billing-reversal-completeness-fix.md`

## Testing Completed (2026-07-26)
108/109 passed (isolated stack `y119`, base `origin/dev`@`c24f5fe`, migrated 0069). All in-scope billing/pharmacy reversal assertions PASS: void→payment reversal+3-way reconcile, refund/void-after-dispense stock/COGS restore, no TASK-105 regression, double-void 400. 1 failure = pre-existing `test_visit_volume_report` flake (out of scope, unrelated to this fix). See `deliveries/test-reports/test-report.md`.

## Blockers
Không. Tài chính — làm cẩn thận, tái dùng helper TASK-105/TASK-112.
