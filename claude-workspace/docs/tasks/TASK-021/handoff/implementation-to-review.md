# TASK-021 — Implementation Handoff

> **Date**: 2026-04-27 | **From**: Code Implementation Agent | **To**: Code Review

---

## Branch

`feature/task-021-fe-billing` in `clinic-cms-web-task021` worktree

## Commits

1. `3678db1` — feat(billing): TASK-021 invoice list + filter
2. `b5906c2` — feat(billing): TASK-021 routing + sidebar + i18n vi/en
3. `e5c96e0` — test(billing): TASK-021 unit + component tests

## Files Created

**Modules:**
- `src/modules/billing/types.ts` — TypeScript types (Invoice, Payment, InvoiceLine, etc.)
- `src/modules/billing/api.ts` — billingApi object wrapping all TASK-013 endpoints
- `src/modules/billing/helpers.ts` — status color, action guards, money parsing

**Pages:**
- `src/pages/billing/InvoiceListPage.tsx` — `/billing/invoices`
- `src/pages/billing/InvoiceDetailPage.tsx` — `/billing/invoices/:id`
- `src/pages/billing/GenerateInvoicePage.tsx` — `/billing/invoice/new/:visit_id`

**Modals:**
- `src/components/billing/AddPaymentModal.tsx`
- `src/components/billing/AddLineModal.tsx`
- `src/components/billing/VoidModal.tsx`
- `src/components/billing/RefundModal.tsx`
- `src/components/billing/PrintModal.tsx`

**i18n:**
- `src/locales/vi/billing.json` — 100+ vi strings with full diacritics
- `src/locales/en/billing.json` — en parity

**Tests:**
- `src/tests/billing/helpers.test.ts` — 30 unit tests, AC2/3/4/5/6/7 coverage
- `src/tests/billing/i18n-billing.test.ts` — 15 i18n parity tests
- `src/tests/billing/InvoiceListPage.test.tsx` — 5 component tests
- `src/tests/billing/modals.test.tsx` — 11 component tests

**Modified:**
- `src/lib/i18n.ts` — added billing namespace
- `src/router/index.tsx` — billing routes replacing placeholder
- `src/components/shell/Sidebar.tsx` — billing sub-items with invoice.read guard

## Test Results

```
Test Files: 27 passed
Tests: 293 passed
TSC: clean
Lint: clean
```

## Stub Map

All billing API calls stub to real TASK-013 paths. The UI shows a beta banner when navigating to billing pages. When BE returns 4xx/5xx (expected on demo), TanStack Query surfaces the error state.

| Stub | Endpoint | When BE available |
|------|----------|-------------------|
| listInvoices | GET /api/v1/invoices | Remove retry:false |
| getInvoice | GET /api/v1/invoices/:id | No change needed |
| generateInvoice | POST /visits/:id/invoices | No change needed |
| addPayment | POST /invoices/:id/payments | No change needed |
| voidInvoice | POST /invoices/:id/void | No change needed |
| refundInvoice | POST /invoices/:id/refund | No change needed |

## Known Items

- `window.prompt()` used for void payment reason (inline, not a full modal) — can be upgraded to a proper modal in a follow-up
- Print uses local template fallback until TASK-013 `/print` endpoint is live
- Daily cashier closing report (task.md requirement) deferred — not in Phase 1 scope per instructions
