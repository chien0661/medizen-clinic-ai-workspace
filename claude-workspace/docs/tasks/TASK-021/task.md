---
id: TASK-021
type: feature
title: FE — Billing (Invoice Auto-Gen + Multi-Payment + Discount + Void/Refund + POS Print)
status: DONE
priority: High
assigned: ""
created: 2026-04-26
updated: 2026-04-27
branch: "feature/task-021-fe-billing"
tags: [frontend, billing, payment, sprint-15]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#13-module-billing"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#11-module-billing--payment"
---

# TASK-021: FE — Billing Module (Invoice + Payment + POS Receipt)

## Description

UI cho lễ tân/cashier thu tiền: invoice tự động generate khi visit AWAITING_PAYMENT, edit invoice items khi draft/pending, multi-payment (cash/card/transfer/ewallet), discount với reason, void/refund với audit, in hóa đơn POS receipt.

## Requirements

- [ ] **Invoice list** (`/billing`)
  - Tabs: Today | Pending | Partially paid | Paid | Voided
  - Filter: date range, patient, doctor, amount range, status
  - Columns: invoice_number, patient, total, paid, balance, status, issued_at
  - Quick action: "Thu tiền" → payment modal
- [ ] **Invoice detail** (`/billing/invoices/:id`)
  - Header: invoice_number, status badge, visit_number link, patient
  - Items table:
    - Service items: name, qty, unit_price, discount, total
    - Medicine items: name, qty, unit_price, total
    - Other items (custom)
  - Edit mode (chỉ với draft/pending): add/remove/edit item, override price
  - Discount section: per-invoice total_discount + reason (nếu > threshold)
  - Subtotal / Total Discount / Total / Paid / **Balance** (highlight)
  - Action buttons: Add Payment | Edit | Print | Void (perm) | Refund (perm)
- [ ] **Payment modal**
  - Amount (default = balance)
  - Method: cash | card | bank_transfer | ewallet (radio)
  - Reference number (cho non-cash)
  - Notes
  - "Thu tiền + In hoá đơn" button (combined action)
  - Sau thu xong: balance = 0 → status='paid', show big "Đã thanh toán" + receipt preview
- [ ] **Discount UI**
  - Input %, hoặc số tiền tuyệt đối (toggle)
  - Reason textarea (required nếu > clinic_settings.billing.discount_threshold_require_reason)
  - Block save nếu reason missing
- [ ] **Void invoice modal** (perm `invoice.void`)
  - Reason required
  - Warning: "Không thể undo. Sẽ tạo invoice negative."
  - Confirm → original status='voided', voided_by_invoice_id link 2 chiều
- [ ] **Refund modal**
  - Choose full / partial
  - Refund amount input
  - Reason
  - Method (về cash/về thẻ/về ewallet)
  - Tạo Payment với amount âm
- [ ] **POS receipt print**
  - Tauri printer ESC/POS
  - Template: header clinic (tên, địa chỉ, SĐT, MST), invoice_number, date, patient, items, total, payment method, "Cảm ơn quý khách!"
  - Reprint history button (audit log)
- [ ] **Daily cashier closing report**
  - End-of-day summary: tổng thu theo method, count payment, refund
  - Export PDF/Excel

## Acceptance Criteria

- [ ] Visit AWAITING_PAYMENT → click "Tạo invoice" → auto-pull VisitService completed + Prescription items in_house thành line items
- [ ] Edit item draft invoice → save → version increment, audit ghi diff
- [ ] Invoice paid → button Edit disabled, chỉ còn Print/Void/Refund
- [ ] Discount 15% trên 1tr không reason (threshold 10%) → button Save disabled, hint hiện rõ
- [ ] Multi-payment: thu 200k + 300k cho invoice 500k → balance = 0, status='paid', paid_at set
- [ ] Void → tạo invoice negative, original có badge "Đã hủy"
- [ ] Refund 100k vào invoice paid 500k → balance = 100k, status='partially_paid', payment có amount=-100k
- [ ] POS receipt in được trên printer thật (test thực địa)

## Progress Checklist

- [x] Implementation
- [x] Code Review (self-review, 1 cycle)
- [x] Testing
- [x] Documentation

## Related Files

- **Code**: `clinic-cms/desktop/src/modules/billing/`

## Timestamps

- **Created**: 2026-04-26
- **Started**: 2026-04-27 15:45:00
- **Documentation Completed**: 2026-04-27 16:00:00

## Notes

Receipt template đa năng — cho phép admin custom layout (logo, footer text) ở settings (TASK-023). V1 hardcode template, phase sau template editor.

## Blockers

- TASK-017, TASK-013 (Billing API)
