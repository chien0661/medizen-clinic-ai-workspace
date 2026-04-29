# TASK-021: FE Billing — Functional Design

> **Status**: DONE | **Date**: 2026-04-27 | **Branch**: feature/task-021-fe-billing

---

## Overview

Frontend billing module for Clinic CMS. Handles invoice lifecycle management from auto-generation through multi-payment collection, discount management, void/refund operations, and POS thermal printing.

## Scope

Backend: TASK-013 (Billing API). FE consumes API stubs while TASK-013 is not deployed on demo (port 8001).

---

## Pages

### 1. Invoice List — `/billing/invoices`

**Permission**: `invoice.read`

**Features**:
- Beta banner (BE TASK-013 not yet on demo)
- Filter: status dropdown (all/draft/issued/partially_paid/paid/void/refunded)
- Patient/invoice search input (client-side filter)
- Table: invoice_number, visit_id (truncated), status badge, grand_total, balance_due (red/green), issued_at
- Row click navigates to detail
- "New Invoice" button → `/billing/invoice/new` (requires `invoice.create`)

**Component**: `src/pages/billing/InvoiceListPage.tsx`

### 2. Invoice Detail — `/billing/invoices/:id`

**Permission**: `invoice.read`

**Features**:
- Header: invoice_number or "(Nháp)", status badge with color coding, visit_id
- Lines table: name, qty, unit_price, discount, line_total; delete button on draft (requires `invoice.modify`)
- Summary: subtotal, discount_total, tax_total, grand_total, paid_total, balance_due (highlighted)
- Payments table: method, amount, reference, received_at; void payment button (requires `invoice.void`)
- Action bar (permission-gated):
  - Add Line (draft, `invoice.modify`)
  - Issue Invoice (draft → issued, `invoice.create`)
  - Receive Payment (issued/partially_paid, `payment.receive`)
  - Void Invoice (issued/partially_paid, `invoice.void`)
  - Refund (paid, `invoice.refund`)
  - Print (always visible)
- Paid banner when status=paid
- Void/refund reason display

**Component**: `src/pages/billing/InvoiceDetailPage.tsx`

### 3. Generate Invoice — `/billing/invoice/new/:visit_id`

**Permission**: `invoice.create`

**Features**:
- Shows visit_id, description of auto-generation logic
- "Tạo hóa đơn" calls `POST /visits/{visit_id}/invoices`
- Redirects to detail on success
- Shows 409 conflict message if invoice already exists

**Component**: `src/pages/billing/GenerateInvoicePage.tsx`

---

## Modals

### Add Payment Modal

**Permission**: `payment.receive` (enforced at parent)

- Payment method radio: Tiền mặt / Thẻ / Chuyển khoản / MoMo / VNPay / Khác
- Amount field (default = balance_due, max = balance_due)
- Reference field (optional)
- Calls `POST /invoices/{id}/payments`
- Invalidates invoice query on success

### Add Adjustment Line Modal

**Permission**: `invoice.modify` (enforced at parent)

- Line type: adjustment (phụ phí) or discount (giảm giá)
- Name, quantity, unit_price inputs
- Discount amount input
- Discount reason textarea (required when line_type=discount OR discount_amount > 0)
- Zod validation prevents save without reason (AC3)

### Void Modal

**Permission**: `invoice.void`

- Warning banner (non-reversible)
- Reason textarea (min 3 chars required — Zod)
- Calls `POST /invoices/{id}/void`

### Refund Modal

**Permission**: `invoice.refund`

- Warning: "Sẽ hoàn lại stock cho thuốc nội viện" (AC5)
- Reason textarea (min 3 chars)
- Calls `POST /invoices/{id}/refund`

### Print Modal

- Tries `GET /invoices/{id}/print` for server HTML; falls back to local template
- Local template: 80mm thermal receipt layout (font-family: monospace, max-width: 80mm)
- `window.print()` with `@media print` CSS for thermal + A4
- Shows: clinic name, invoice_number, date, visit_id, line items, totals, payment method, "Cảm ơn quý khách!"

---

## Status Machine (per TASK-013)

```
draft → issued → partially_paid → paid → refunded
issued/partially_paid → void
```

## Permission Matrix

| Action | Permission |
|--------|-----------|
| View invoices/payments | invoice.read |
| Create + submit invoice | invoice.create |
| Add/delete lines (draft) | invoice.modify |
| Receive payment | payment.receive |
| Void invoice/payment | invoice.void |
| Refund | invoice.refund |

---

## i18n

Namespaces: `billing` (vi + en) — 11 top-level keys, 100+ translation strings.

Vietnamese diacritics verified: "Hóa đơn", "Thanh toán", "Đã hủy", "Hoàn tiền", "Tiền mặt".

---

## State Management

- TanStack Query v5 for server state (invoices, invoice detail)
- Query keys: `["invoices"]`, `["invoice", id]`, `["invoice-print", id]`
- React Hook Form + Zod for all modal forms
- Toast notifications via Sonner

---

## Acceptance Criteria Status

| AC | Description | Status |
|----|-------------|--------|
| AC1 | Invoice auto-gen from visit | PASS (GenerateInvoicePage → POST /visits/{id}/invoices) |
| AC2 | Multi-payment partial → final | PASS (AddPaymentModal, balance_due recalculates) |
| AC3 | Discount line requires reason | PASS (Zod schema in AddLineModal) |
| AC4 | Void disables further payments | PASS (canAcceptPayment("void")=false, actions hidden) |
| AC5 | Refund triggers stock release notice | PASS (RefundModal warning text) |
| AC6 | Print preview renders thermal layout | PASS (PrintModal, 80mm CSS) |
| AC7 | Pay full → status auto-changes to paid | DEFERRED-BE (BE side-effect, UI reflects via query invalidation) |

**AC7 note**: The paid status transition when balance=0 is a BE-side effect (TASK-013). UI correctly shows paid badge once BE updates the status, verified by query invalidation on payment success.
