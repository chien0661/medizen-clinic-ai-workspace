---
id: TASK-013
type: feature
title: Billing — Invoice + Multi-Payment + Discount + Void/Refund
status: TODO
priority: High
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [billing, payment, sprint-10]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#13-module-billing"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#11-module-billing--payment"
---

# TASK-013: Billing — Invoice + Multi-Payment + Discount + Void/Refund

## Description

Auto-generate invoice từ Visit khi chuyển AWAITING_PAYMENT (pull VisitService completed + Prescription items in_house). Multi-payment, discount per-item & per-invoice (kèm reason nếu vượt threshold). Void = invoice negative entry. Refund = payment negative. Print POS template.

## Requirements

- [ ] Migration `0010_create_billing.py` (invoice + invoice_item + payment)
- [ ] Helper `fn_next_invoice_number(clinic_id, date)` format `INV-YYYYMMDD-NNN`
- [ ] Endpoints:
  - `POST /api/v1/visits/{id}/invoice` (auto-generate từ visit; idempotent)
  - `GET/PATCH /api/v1/invoices/{id}` (PATCH chỉ với draft/pending)
  - `POST /api/v1/invoices/{id}/payments` (thêm payment)
  - `POST /api/v1/invoices/{id}/void` (perm `invoice.void`, kèm reason)
  - `POST /api/v1/invoices/{id}/refund` (full hoặc partial)
  - `GET /api/v1/invoices/{id}/print` (HTML POS template)
- [ ] Auto recalc: invoice.paid_amount = SUM(payments.amount), invoice.balance, status (pending/partially_paid/paid)
- [ ] Trigger PostgreSQL: update invoice status khi insert/update payment
- [ ] Discount validation: nếu > threshold (clinic_settings.billing.discount_threshold_require_reason) bắt buộc reason
- [ ] Edit rules theo §11.5 BA (draft/pending: edit thoải mái; partially_paid: chỉ thêm payment; paid: chỉ void/refund)
- [ ] Void: tạo Invoice mới với amount âm + link 2 chiều `voided_by_invoice_id`
- [ ] Khi visit COMPLETED → invoice phải paid + prescription dispensed (validate)

## Acceptance Criteria

- [ ] Visit complete với 2 service + 1 in_house prescription → invoice có 3 items, total đúng
- [ ] Invoice 500k, payment 200k → status partially_paid, balance 300k
- [ ] Payment thứ 2 = 300k → status paid, paid_at set
- [ ] Void invoice paid → tạo invoice negative, original status = voided
- [ ] Refund 100k vào invoice paid → tạo payment amount=-100k, balance=100k, status partially_paid
- [ ] Discount 15% trên invoice 1tr (threshold 10%) không có reason → 400

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/billing/`

## Timestamps

- **Created**: 2026-04-26

## Notes

V1 không có tax, không VAT. invoice_item.tax_amount default 0. Phase sau cần xuất hoá đơn điện tử thì revisit.

## Blockers

- TASK-010 (VisitService), TASK-011 (Prescription)
