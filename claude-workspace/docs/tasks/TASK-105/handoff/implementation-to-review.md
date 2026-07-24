# TASK-105 — Implementation → Code Review Handoff

**Date:** 2026-07-24
**Repo:** clinic-cms backend
**Worktree (for reviewer):** `F:/MyProject/clinic-cms-workspace/_fix105-be` (left in place, branch checked out)
**Branch:** `fix/TASK-105-refund-reversal` (based on `origin/dev` @ `f305496`), pushed to origin
**Commit:** `bc9df21`

## Bug (H-3)
`refund_invoice()` in `app/modules/billing/services/invoice_service.py` only flipped
`invoice.status` to `'refunded'` and released pharmacy stock. `paid_total` was left
unchanged and the invoice's payment rows stayed `is_voided = FALSE`.
`payment_method_service.get_payment_method_breakdown()` sums non-voided `payment` rows
without joining invoice status, so refunded money kept counting as "collected" forever.
`revenue_service.get_revenue()` already filters `status IN ('paid','partially_paid')`,
so it correctly excludes refunded invoices. Result: the two reports permanently
disagreed about the same money, and `payment_service.void_payment()` explicitly refuses
to run on a `refunded` invoice (`"Cannot void payment on a {status} invoice."`), so
there was no way to correct the skew after the fact.

## Approach chosen: A — void the payments inside `refund_invoice`

Two approaches were viable (task.md left the choice to implementation):
- **(A)** On `refund_invoice`, void the invoice's active payments so `paid_total` drops.
- **(B)** Have `payment_method_service` join invoice status and exclude payments
  belonging to refunded invoices.

**Chose (A)** because:
1. **Single point of change.** `payment_method_service` needs zero changes — it already
   filters `is_voided = FALSE`; once refund voids the payments, that filter alone makes
   the report correct. No new join/subquery, no risk of missing some other report that
   also sums `payment` rows the same naive way.
2. **The invoice's own numbers become internally consistent**, not just the report:
   `paid_total`/`balance_due` on a refunded invoice now correctly show 0/grand_total
   instead of a stale "paid" amount that no money actually backs anymore. This also
   makes `void_payment`'s existing refusal on refunded invoices *make sense*
   semantically (there's nothing left to void — refund already did it) instead of being
   an unexplained dead end for the caller.
3. **Reuses existing, tested logic.** `refund_invoice` now calls
   `payment_service._recalculate_invoice_paid_total()` — the exact same helper
   `void_payment` uses — so paid_total/balance_due are derived identically in both
   code paths (no duplicated arithmetic to keep in sync).
4. **Partial refunds:** not a real scenario in the current model — `refund_invoice`
   only accepts invoices in status `'paid'` (never `'partially_paid'`), and there is no
   separate "refund this one payment" endpoint. So "partial refund" reduces to: an
   already-`paid` invoice has exactly the payments that sum to `grand_total`; refund
   voids all of them at once. No special-casing needed.

Approach B was rejected because it would leave the invoice's own `paid_total`
permanently wrong (misleading on the print view / invoice detail) while only fixing
the aggregate report, and it would need to be re-applied to every other place that
might later sum `payment` rows.

## Change
File: `app/modules/billing/services/invoice_service.py`, `refund_invoice()`:
- After releasing pharmacy reservations, loads all active (`is_voided=false`,
  `is_deleted=false`) payments for the invoice and voids each one
  (`is_voided=True`, `voided_at=now`, `void_reason=f"Refund: {reason}"`,
  `updated_by=refunded_by`) — mirrors exactly what `payment_service.void_payment` does
  per-payment.
- Sets `invoice.status='refunded'`, `refunded_at`, `refund_reason` as before.
- Calls `payment_service._recalculate_invoice_paid_total(invoice, all_payments)` (local
  import to avoid a module-load cycle) so `paid_total`/`balance_due` reflect the
  now-voided payments. This helper returns early on terminal statuses without touching
  `invoice.status`, so it only updates the two totals here — same behavior as
  `void_payment`.
- `log.info("invoice_refunded", ...)` now also logs `payments_voided` count.

No changes to `payment_method_service.py`, `revenue_service.py`, or `payment_service.py`.

## Tests added
`tests/integration/billing/test_billing_e2e.py`, `TestRefundInvoice` class, new test
`test_refund_reverses_collected_money`:
- Pays invoice A (220,000) and invoice B (150,000), both cash.
- Refunds invoice A. Asserts: `paid_total == 0`, `balance_due == grand_total` on the
  refunded invoice; its single payment is `is_voided == True`; a subsequent
  `void_payment` call on that payment returns 400 (already reversed, no double-void).
- Invoice B (untouched) still shows `status == 'paid'`, `paid_total == 150000` —
  guards against the fix over-reaching into unrelated invoices.
- Hits `/api/v1/reports/payment-methods` and `/api/v1/reports/revenue` for a
  3-day window centered on "now" (timezone-safe against the `Asia/Ho_Chi_Minh`
  conversion both reports apply): payment-methods `cash`/`total` == 150,000 only
  (A's 220,000 no longer counted); revenue's `summary.total_paid` == 150,000 too —
  i.e. **payment-methods total == revenue total_paid** for the same data, which is
  the acceptance criterion.

## Verification (real Postgres + Redis, isolated Docker stack — NOT the w2e/9999 stack)
- Isolated stack: project name `fix105`, ports api 9978 / postgres 5478 / redis 6460,
  built from the repo's own `Dockerfile`, compose file
  `docker/docker-compose.fix105.yml` (temporary, not committed — deleted after use).
- `alembic upgrade head` — migrated cleanly through `0066` (no errors).
- `pytest tests/integration/billing/ tests/integration/reports/
  tests/integration/test_sod_violations.py tests/integration/test_rbac_seed.py -q`
  → **100 passed** (81 pre-existing + this task's new test; also reran
  `tests/integration/billing/test_billing_e2e.py -k Refund` in isolation — 3 passed).
- Stack torn down (`docker compose -p fix105 ... down -v`) and the temporary compose
  file deleted; confirmed via `docker ps` before/after that the `w2e` stack
  (`clinic_cms_w2e_api/postgres/redis/worker`, ports 9999/5434/5436/6380/6382) was
  running throughout and untouched.

## Static analysis
- `ruff check app tests`: 452 errors after the change vs. 454 on `origin/dev` baseline
  (2 *fewer* — the new test starts using the `timedelta` import that was previously
  imported-but-unused in that file). **0 new findings.** Both changed files individually
  scanned clean (`invoice_service.py`: 0 findings; `test_billing_e2e.py`: 4 pre-existing
  findings, same category as baseline, none introduced by the new test).
- `mypy app`: 185 errors in 79 files, identical before and after the change (confirmed
  via `git stash`/`git stash pop` A/B comparison). **0 new errors.**
  `invoice_service.py`'s only mypy findings (`datetime.UTC` attr / Decimal assignment,
  lines 23/83/84/86) are pre-existing and unrelated to the new code (added at
  line ~646+).

## Files changed
- `app/modules/billing/services/invoice_service.py` (+49 lines, `refund_invoice` only)
- `tests/integration/billing/test_billing_e2e.py` (+103 lines, one new test)

## For the reviewer
- Worktree left at `F:/MyProject/clinic-cms-workspace/_fix105-be` on branch
  `fix/TASK-105-refund-reversal`, already pushed to `origin`.
- `payment_method_service.py` and `revenue_service.py` are untouched — worth
  double-checking that's acceptable given the task description offered both (A) and
  (B) as options; the rationale for picking (A) over (B) is above.
- `void_payment`'s existing refusal on `void`/`refunded` invoices was NOT changed —
  it now simply never gets a chance to matter for refunded invoices since refund
  already voided everything.
