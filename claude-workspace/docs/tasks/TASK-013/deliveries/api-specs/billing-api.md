# Billing API Specification — TASK-013

> **Version:** 1.0 | **Date:** 2026-04-27 | **Status:** DONE
> **Base URL:** `/api/v1`
> **Auth:** Bearer JWT — all endpoints require authentication.
> **Tenant context:** JWT payload includes `clinic_id`. RLS enforces isolation.

---

## Authentication & Tenant Context

All requests require:
```
Authorization: Bearer <access_token>
```

The JWT includes `clinic_id` which is automatically applied as RLS context. Users only see data for their own clinic.

---

## Invoice Endpoints

### POST `/visits/{visit_id}/invoices`

Auto-generate a draft invoice from a visit's completed services and in-house prescription items.

**Permission:** `invoice.create`

**Path params:** `visit_id` (UUID)

**Response 201:**
```json
{
  "id": "uuid",
  "clinic_id": "uuid",
  "visit_id": "uuid",
  "invoice_number": "",
  "status": "draft",
  "subtotal": "500000.00",
  "discount_total": "0.00",
  "tax_total": "0.00",
  "grand_total": "500000.00",
  "paid_total": "0.00",
  "balance_due": "500000.00",
  "issued_at": null,
  "voided_at": null,
  "void_reason": null,
  "refunded_at": null,
  "refund_reason": null,
  "created_at": "2026-04-27T10:00:00+00:00",
  "updated_at": "2026-04-27T10:00:00+00:00",
  "lines": [
    {
      "id": "uuid",
      "invoice_id": "uuid",
      "line_type": "service",
      "source_type": "visit_service",
      "source_id": "uuid",
      "name": "Khám tổng quát",
      "quantity": "1.000",
      "unit_price": "200000.00",
      "discount_amount": "0.00",
      "discount_reason": null,
      "line_total": "200000.00",
      "sort_order": 0,
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "payments": []
}
```

**Error 409:** Invoice already exists for this visit (active non-void invoice).

---

### GET `/invoices`

List invoices with optional filters.

**Permission:** `invoice.read`

**Query params:**
| Param | Type | Description |
|---|---|---|
| `status` | string | Filter by status (draft/issued/partially_paid/paid/void/refunded) |
| `visit_id` | UUID | Filter by visit |
| `limit` | int | Max results (default 50, max 200) |
| `offset` | int | Skip N results (default 0) |

**Response 200:** Array of `InvoiceSummaryResponse`
```json
[
  {
    "id": "uuid",
    "clinic_id": "uuid",
    "visit_id": "uuid",
    "invoice_number": "INV-20260427-001",
    "status": "issued",
    "grand_total": "500000.00",
    "paid_total": "0.00",
    "balance_due": "500000.00",
    "issued_at": "2026-04-27T10:05:00+00:00",
    "created_at": "2026-04-27T10:00:00+00:00"
  }
]
```

---

### GET `/invoices/{invoice_id}`

Get full invoice with lines and payments.

**Permission:** `invoice.read`

**Response 200:** Full `InvoiceResponse` (same as create response above)

**Error 404:** Invoice not found or belongs to different clinic.

---

### PATCH `/invoices/{invoice_id}`

Update invoice metadata (only allowed on draft invoices).

**Permission:** `invoice.modify`

**Request body:** `{}` (no mutable fields in Phase 1)

**Error 400:** Invoice is not in draft status.

---

### POST `/invoices/{invoice_id}/lines`

Add a manual adjustment or discount line to a **draft** invoice.

**Permission:** `invoice.modify`

**Request body:**
```json
{
  "line_type": "adjustment",
  "name": "Phụ phí giấy nhãn",
  "quantity": 1,
  "unit_price": "10000.00",
  "discount_amount": "0.00",
  "discount_reason": null,
  "sort_order": 10
}
```

**line_type values:**
- `adjustment` — positive surcharge
- `discount` — negative reduction (requires `discount_reason`)

**Validation rules:**
- `discount_amount > 0` requires `discount_reason`
- `line_type = "discount"` requires `discount_reason`
- `discount_amount` cannot exceed `unit_price * quantity`

**Response 201:** `InvoiceLineResponse`

**Error 400:** Invoice not in draft / discount_reason missing / discount exceeds max.
**Error 422:** Schema validation failure.

---

### DELETE `/invoice-lines/{line_id}`

Delete a line from a **draft** invoice.

**Permission:** `invoice.modify`

**Response 204:** No content.

**Error 400:** Invoice not in draft status.
**Error 404:** Line not found.

---

### POST `/invoices/{invoice_id}/submit`

Submit invoice: **draft → issued**. Assigns `invoice_number` (format `INV-YYYYMMDD-NNN`).

**Permission:** `invoice.create`

**No request body.**

**Response 200:** Full `InvoiceResponse` with `status: "issued"` and `invoice_number` set.

**Error 400:**
- Invoice not in draft status.
- Invoice has no lines.

---

### POST `/invoices/{invoice_id}/void`

Void an issued or partially-paid invoice.

**Permission:** `invoice.void`

**Request body:**
```json
{
  "reason": "Khách hàng huỷ lịch hẹn"
}
```

**Response 200:** Full `InvoiceResponse` with `status: "void"`, `voided_at` set, `void_reason` set.

**Error 400:** Invoice not in `issued` or `partially_paid` status.

**Important:** Void does **not** release pharmacy reservations. Only refund releases stock.

---

### POST `/invoices/{invoice_id}/refund`

Refund a **paid** invoice. Releases pharmacy stock reservations for in-house prescription items.

**Permission:** `invoice.refund`

**Request body:**
```json
{
  "reason": "Hoàn tiền theo yêu cầu khách hàng"
}
```

**Response 200:** Full `InvoiceResponse` with `status: "refunded"`, `refunded_at` set.

**Error 400:** Invoice not in `paid` status.

---

### GET `/invoices/{invoice_id}/print`

Get print-ready HTML invoice.

**Permission:** `invoice.read`

**Response 200:**
```json
{
  "invoice": { ... },
  "html": "<!DOCTYPE html>...<html>...<body>...</body></html>"
}
```

---

## Payment Endpoints

### POST `/invoices/{invoice_id}/payments`

Record a payment against an invoice.

**Permission:** `payment.receive`

**Request body:**
```json
{
  "payment_method": "cash",
  "amount": "200000.00",
  "reference": "TXN-20260427-001"
}
```

**payment_method values:** `cash`, `card`, `transfer`, `momo`, `vnpay`, `other`

**Validation:**
- `amount` must be positive and ≤ `invoice.balance_due`
- Invoice must be in `issued` or `partially_paid` status

**Response 201:** `PaymentResponse`
```json
{
  "id": "uuid",
  "invoice_id": "uuid",
  "payment_method": "cash",
  "amount": "200000.00",
  "reference": null,
  "received_by_user_id": "uuid",
  "received_at": "2026-04-27T10:10:00+00:00",
  "is_voided": false,
  "voided_at": null,
  "void_reason": null,
  "created_at": "..."
}
```

**Invoice status side effects:**
- `amount < balance_due` → invoice status becomes `partially_paid`
- `amount == balance_due` → invoice status becomes `paid`

**Error 400:**
- Overpayment (amount > balance_due)
- Invoice in void/refunded/draft status

---

### GET `/invoices/{invoice_id}/payments`

List all payments for an invoice.

**Permission:** `invoice.read`

**Response 200:** Array of `PaymentResponse`

---

### POST `/payments/{payment_id}/void`

Void a payment. Recalculates invoice `paid_total` and status.

**Permission:** `invoice.void`

**Request body:**
```json
{
  "reason": "Sai phương thức thanh toán"
}
```

**Response 200:** Updated `PaymentResponse` with `is_voided: true`.

**Side effects:**
- Invoice `paid_total` recalculated from remaining active payments
- Invoice `status` may revert (e.g., `paid` → `partially_paid` → `issued`)

**Error 400:**
- Payment already voided
- Invoice in void/refunded status

---

## Status Machine Summary

### Invoice Status

```
draft ──[submit]──► issued
                      │
            [payment < balance]
                      ▼
              partially_paid
                      │
            [payment = balance]
                      ▼
                    paid
                      │
                  [refund]
                      ▼
                  refunded

issued / partially_paid ──[void]──► void
```

### Payment Lifecycle

```
active ──[void_payment]──► voided
```

---

## Permission Reference

| Permission | Description | Default Roles |
|---|---|---|
| `invoice.read` | View invoices and payments | admin, doctor, nurse, receptionist, pharmacist |
| `invoice.create` | Create and submit invoices | admin, receptionist |
| `invoice.modify` | Edit draft invoices | admin, receptionist |
| `invoice.void` | Void invoices and payments | admin |
| `invoice.refund` | Refund paid invoices | admin |
| `payment.receive` | Record payments | admin, receptionist |

---

## Error Response Format

```json
{
  "error": {
    "code": "BUSINESS_RULE_VIOLATION",
    "message": "Cannot modify invoice in status 'issued'. Only draft invoices allow line edits.",
    "details": {}
  },
  "meta": {
    "request_id": "uuid"
  }
}
```

**Error codes:**
- `NOT_FOUND` (404) — resource not found or wrong clinic
- `CONFLICT` (409) — duplicate invoice for visit
- `BUSINESS_RULE_VIOLATION` (400) — state machine violation, overpayment, etc.
- `FORBIDDEN` (403) — insufficient permissions
- `INTERNAL_SERVER_ERROR` (500) — unexpected error

---

## Data Types

All monetary amounts are returned as strings (Decimal precision) to avoid floating-point issues:
```json
"grand_total": "500000.00"
"amount": "200000.00"
```

All IDs are UUIDs in string format.

All timestamps are ISO 8601 with timezone offset (UTC): `"2026-04-27T10:00:00+00:00"`

---

## Notes for TASK-021 (FE Billing)

1. **Draft invoices** can have lines added/deleted. Submit to lock for payment.
2. **Invoice number** is only assigned at submit time (empty string in draft).
3. **Multi-payment:** Multiple payment calls are allowed. Each must ≤ balance_due.
4. **Void vs Refund:** Void = cancel unpaid/partial. Refund = undo completed payment.
5. **Print:** Returns HTML string suitable for embedding in iframe or direct print.
6. **Pagination:** Use `limit` + `offset` for list views. Default 50 per page.
