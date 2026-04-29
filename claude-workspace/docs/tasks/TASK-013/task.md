---
id: TASK-013
type: feature
title: Billing — Invoice + Multi-Payment + Discount + Void/Refund
status: DONE
priority: High
assigned: chiendv
created: 2026-04-26
updated: 2026-04-27
branch: "feature/task-013-billing"
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

- [x] Migration `0019_create_invoices.py` (invoice + invoice_line + payment)
- [x] Migration `0019a_add_billing_permissions.py` (billing permissions seed)
- [x] Helper `fn_next_invoice_number(clinic_id, date)` format `INV-YYYYMMDD-NNN`
- [x] Endpoints:
  - `POST /api/v1/visits/{id}/invoices` (auto-generate từ visit; idempotent)
  - `GET /api/v1/invoices` (list with filters)
  - `GET /api/v1/invoices/{id}` (detail with lines + payments)
  - `PATCH /api/v1/invoices/{id}` (PATCH chỉ với draft)
  - `POST /api/v1/invoices/{id}/lines` (add adjustment/discount line)
  - `DELETE /api/v1/invoice-lines/{line_id}` (remove line from draft)
  - `POST /api/v1/invoices/{id}/submit` (draft → issued; assign invoice_number)
  - `POST /api/v1/invoices/{id}/void` (perm `invoice.void`, kèm reason)
  - `POST /api/v1/invoices/{id}/refund` (perm `invoice.refund`, kèm reason)
  - `GET /api/v1/invoices/{id}/print` (HTML POS template)
  - `POST /api/v1/invoices/{id}/payments` (add payment)
  - `GET /api/v1/invoices/{id}/payments` (list payments)
  - `POST /api/v1/payments/{id}/void` (void payment)
- [x] Auto recalc: invoice.paid_total = SUM(active payments), balance_due, status
- [x] Discount validation: discount_amount > 0 requires discount_reason
- [x] Edit rules: only draft allows line edits; issued+ rejects modification
- [x] Void: status → void + voided_at + void_reason (no stock release)
- [x] Refund: status → refunded + releases pharmacy reservations

## Acceptance Criteria

- [x] AC1: Auto-gen invoice from visit with services + in_house prescriptions → items snapshot
- [x] AC2: Invoice 500k, payment 200k → status partially_paid, balance 300k; payment 2 = 300k → paid
- [x] AC3: Discount amount > 0 without reason → 422 validation error
- [x] AC4: Void issued/partially_paid invoice → status void, no further payments allowed
- [x] AC5: Refund paid invoice → status refunded, pharmacy stock released

## Progress Checklist

- [x] Implementation
- [x] Code Review (self-review)
- [x] Testing (64 tests: 33 unit + 31 integration, all passing)
- [x] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/billing/`
- **Migrations**: `clinic-cms/alembic/versions/0019_create_invoices.py`, `0019a_add_billing_permissions.py`
- **API Spec**: `docs/tasks/TASK-013/deliveries/api-specs/billing-api.md`
- **Functional Design**: `docs/tasks/TASK-013/deliveries/final-specs/billing-functional-design.md`
- **DDL**: `docs/tasks/TASK-013/deliveries/sql-scripts/billing-ddl.md`

## Timestamps

- **Created**: 2026-04-26
- **Started**: 2026-04-27
- **Completed**: 2026-04-27

## Notes

V1: No tax/VAT. Phase 2: xuất hóa đơn điện tử.

Phase 1 implementation notes:
- Void does NOT release pharmacy reservations (only refund does)
- invoice_number assigned at submit time; empty string in draft
- Unique index on invoice_number excludes empty string to allow multiple drafts
- Savepoint pattern used for visit_service/prescription_item queries (graceful degradation)
- Fixed 0007 migration UUID cast issue for fresh databases (asyncpg CAST workaround)

## Blockers

- TASK-010 (VisitService) — worktree does not have visit_service table; handled via savepoint
- TASK-011 (Prescription) — available in this worktree; in_house items billed correctly
