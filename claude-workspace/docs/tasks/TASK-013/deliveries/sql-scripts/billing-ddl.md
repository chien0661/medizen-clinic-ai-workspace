# Billing DDL — TASK-013

> **Migration files:** `0019_create_invoices.py`, `0019a_add_billing_permissions.py`
> **Revision chain:** `0018a → 0019 → 0019a`

---

## Tables

### `invoice`

Invoice header per visit. One active (non-void) invoice per visit enforced via partial unique index.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK, gen_random_uuid() | |
| clinic_id | UUID | FK clinic.id, NOT NULL, INDEX | Tenant isolation |
| visit_id | UUID | NULL, INDEX | Soft ref to visit (no FK — visit module separate) |
| invoice_number | TEXT | NOT NULL, default '' | Empty for drafts; INV-YYYYMMDD-NNN after submit |
| status | TEXT | NOT NULL, CHECK in statuses | draft/issued/partially_paid/paid/void/refunded |
| subtotal | NUMERIC(15,2) | NOT NULL, default 0, ≥0 | Sum of line totals before discount |
| discount_total | NUMERIC(15,2) | NOT NULL, default 0, ≥0 | Total discounts applied |
| tax_total | NUMERIC(15,2) | NOT NULL, default 0, ≥0 | Phase 1: always 0 |
| grand_total | NUMERIC(15,2) | NOT NULL, default 0, ≥0 | subtotal - discount + tax |
| paid_total | NUMERIC(15,2) | NOT NULL, default 0, ≥0 | Sum of active payments |
| balance_due | NUMERIC(15,2) | NOT NULL, default 0, ≥0 | grand_total - paid_total |
| issued_at | TIMESTAMPTZ | NULL | Set on submit |
| voided_at | TIMESTAMPTZ | NULL | Set on void |
| void_reason | TEXT | NULL | |
| refunded_at | TIMESTAMPTZ | NULL | Set on refund |
| refund_reason | TEXT | NULL | |
| is_deleted | BOOLEAN | NOT NULL, default false | Soft delete |
| deleted_at | TIMESTAMPTZ | NULL | |
| deleted_by | UUID | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, default now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, default now() | |
| created_by | UUID | NULL | |
| updated_by | UUID | NULL | |
| version | INTEGER | NOT NULL, default 1 | Optimistic lock |

**Check constraints:**
- `ck_invoice_status`: status IN ('draft','issued','partially_paid','paid','void','refunded')
- `ck_invoice_subtotal_non_negative`: subtotal >= 0
- `ck_invoice_discount_total_non_negative`: discount_total >= 0
- `ck_invoice_grand_total_non_negative`: grand_total >= 0
- `ck_invoice_paid_total_non_negative`: paid_total >= 0

**Indexes:**
```sql
ix_invoice_clinic_id              ON invoice(clinic_id)
ix_invoice_clinic_status          ON invoice(clinic_id, status)
ix_invoice_clinic_visit           ON invoice(clinic_id, visit_id)
uq_invoice_clinic_visit_active    ON invoice(clinic_id, visit_id) WHERE is_deleted=false AND status != 'void'
uq_invoice_clinic_number          ON invoice(clinic_id, invoice_number) WHERE is_deleted=false AND invoice_number != ''
ix_invoice_clinic_issued_at       ON invoice(clinic_id, issued_at DESC) WHERE is_deleted=false
```

**RLS:** `clinic_id::text = current_setting('app.current_clinic_id', true)`

---

### `invoice_line`

Snapshot line items. Created at invoice generation time; prices captured from catalog.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | |
| clinic_id | UUID | FK clinic.id, NOT NULL | Tenant isolation |
| invoice_id | UUID | FK invoice.id CASCADE, NOT NULL | Parent invoice |
| line_type | TEXT | NOT NULL, CHECK | service/medicine/adjustment/discount |
| source_type | TEXT | NULL | 'visit_service' or 'prescription_item' |
| source_id | UUID | NULL | Soft ref — no FK constraint |
| name | TEXT | NOT NULL | Snapshot of service/medicine name |
| quantity | NUMERIC(10,3) | NOT NULL, default 1, >0 | |
| unit_price | NUMERIC(15,2) | NOT NULL, ≥0 | Snapshot price at billing time |
| discount_amount | NUMERIC(15,2) | NOT NULL, default 0, ≥0 | Per-line discount |
| discount_reason | TEXT | NULL | Required when discount_amount > 0 |
| line_total | NUMERIC(15,2) | NOT NULL | qty * unit_price - discount_amount (negative for discount lines) |
| sort_order | INTEGER | NULL, default 0 | Display order |
| (+ BaseEntity columns) | | | |

**Check constraints:**
- `ck_invoice_line_type`: line_type IN ('service','medicine','adjustment','discount')
- `ck_invoice_line_quantity_positive`: quantity > 0
- `ck_invoice_line_unit_price_non_negative`: unit_price >= 0
- `ck_invoice_line_discount_amount_non_negative`: discount_amount >= 0

**Indexes:**
```sql
ix_invoice_line_clinic_id         ON invoice_line(clinic_id)
ix_invoice_line_invoice_id        ON invoice_line(invoice_id)
ix_invoice_line_clinic_invoice    ON invoice_line(clinic_id, invoice_id)
```

---

### `payment`

Individual payment records. Multiple payments per invoice allowed.

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | |
| clinic_id | UUID | FK clinic.id, NOT NULL | Tenant isolation |
| invoice_id | UUID | FK invoice.id RESTRICT, NOT NULL | Parent invoice |
| payment_method | TEXT | NOT NULL, CHECK | cash/card/transfer/momo/vnpay/other |
| amount | NUMERIC(15,2) | NOT NULL, >0 | Must be positive |
| reference | TEXT | NULL | Transaction ID / receipt number |
| received_by_user_id | UUID | NOT NULL | User who recorded payment |
| received_at | TIMESTAMPTZ | NOT NULL, default now() | |
| is_voided | BOOLEAN | NOT NULL, default false | |
| voided_at | TIMESTAMPTZ | NULL | |
| void_reason | TEXT | NULL | |
| (+ BaseEntity columns) | | | |

**Check constraints:**
- `ck_payment_method`: payment_method IN ('cash','card','transfer','momo','vnpay','other')
- `ck_payment_amount_positive`: amount > 0

**Indexes:**
```sql
ix_payment_clinic_id          ON payment(clinic_id)
ix_payment_invoice_id         ON payment(invoice_id)
ix_payment_clinic_invoice     ON payment(clinic_id, invoice_id)
```

---

## SQL Function

### `fn_next_invoice_number(p_clinic_id UUID, p_date DATE)`

Generates sequential invoice numbers per clinic per day.

**Format:** `INV-YYYYMMDD-NNN` (3-digit zero-padded sequence)

**Examples:**
- `INV-20260427-001` (first invoice on 2026-04-27)
- `INV-20260427-002` (second invoice on same day)

**Algorithm:**
```sql
v_seq = COUNT(*) + 1
FROM invoice
WHERE clinic_id = p_clinic_id
  AND is_deleted = false
  AND DATE(issued_at AT TIME ZONE 'UTC') = p_date
  AND invoice_number LIKE 'INV-' || TO_CHAR(p_date, 'YYYYMMDD') || '-%'
```

**Security:** `SECURITY DEFINER`, granted to `cms_app`.

---

## Permissions Seeded (0019a)

```
invoice.read       — View invoices and payments
invoice.create     — Create and auto-generate invoices
invoice.modify     — Modify draft invoices and add adjustment lines
invoice.void       — Void issued or partially paid invoices
invoice.refund     — Refund paid invoices
payment.receive    — Record payments against invoices
```

**Role assignments:**

| Role | Permissions |
|---|---|
| admin | all 6 |
| receptionist | invoice.read, invoice.create, invoice.modify, payment.receive |
| doctor | invoice.read |
| nurse | invoice.read |
| pharmacist | invoice.read |
