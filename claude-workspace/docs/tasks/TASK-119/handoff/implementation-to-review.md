# TASK-119 — Implementation → Review handoff

**Branch:** `fix/TASK-119-billing-reversal` (base `origin/dev` @ `c24f5fe`, alembic head `0069`), pushed to origin.
**Worktree:** `F:/MyProject/clinic-cms-workspace/_fix119-be` (left in place for review).

## Summary

Both H-6 (void doesn't reverse collected money) and H-5 (refund/void after
dispense doesn't restore stock/COGS) are fixed in
`app/modules/billing/services/invoice_service.py`, reusing the TASK-105
(payment reversal) and TASK-112 (`reopen_after_payment_reversal`) precedents
exactly as instructed — no double-reversal, no changes to reports code.

## H-6 — `void_invoice` now reverses collected money

Previously `void_invoice` only set `status='void'`; any active payment on a
`partially_paid` invoice stayed `is_voided=false`, so
`payment_method_service` (sums non-voided payments) kept counting it as
collected while `revenue_service` (status filter) excluded the invoice —
permanent 3-way mismatch.

`void_invoice` now mirrors `refund_invoice`/TASK-105 in order:
1. If `invoice.visit_id` is set: undispense any dispensed in_house items,
   then release remaining in_house reservations (H-5, see below).
2. Void every active `Payment` (`is_voided=True`, `voided_at`, `void_reason`).
3. Set `invoice.status='void'` (terminal) **before** recalculating, so
   `payment_service._recalculate_invoice_paid_total` (reused, not
   duplicated) sees the terminal status and only updates
   `paid_total`/`balance_due`, leaving status alone — same pattern
   `refund_invoice` already used.
4. Call `visit_completion_service.reopen_after_payment_reversal` (TASK-112,
   no-op if the visit isn't COMPLETED) so a COMPLETED visit reopens to
   AWAITING_PAYMENT.

`allowed_statuses` for void is unchanged (`{issued, partially_paid}`) —
`paid` invoices still only go through `refund_invoice`, per the existing
status-flow contract in the module docstring (updated to reflect the new
void/refund parity).

## H-5 — refund/void after dispense now restores stock + COGS

`_release_pharmacy_reservations` only ever matched
`in_house_status='reserved'`; once the pharmacy actually dispensed a
prescription the items are `'dispensed'`, so refund/void released 0 rows —
`batch.actual_quantity` never came back, and `profit_service`'s COGS query
(`pib.status='dispensed'` within the period) kept counting the reversed
cost forever.

New helper `_undispense_dispensed_items(db, clinic_id, visit_id,
performed_by)` (placed right before `_release_pharmacy_reservations`):
finds distinct `prescription_id`s on the visit with `in_house_status
='dispensed'`, and calls `dispense_service.undispense` on each — which
restores `batch.actual_quantity`/`reserved_quantity`, records a `'return'`
stock_movement, and flips the item/PIB back to **`'reserved'`** (not
`'released'` — that's `dispense_service.undispense`'s existing contract,
verified against its docstring/code; I did not change it). The subsequent
`_release_pharmacy_reservations` call then picks up those now-`'reserved'`
rows and fully frees them (`status='released'`,
`batch.reserved_quantity` decremented) — same end state as an item that was
only ever reserved and never dispensed. Net effect on the batch:
`actual_quantity` fully restored, `reserved_quantity` back to its
pre-reservation value.

Both `refund_invoice` and `void_invoice` call
`_undispense_dispensed_items` **before** `_release_pharmacy_reservations`
(order matters — see above). Best-effort / try-except, mirroring
`_release_pharmacy_reservations`'s existing error handling, so a
pharmacy-side failure never blocks the billing reversal itself.

COGS reversal is automatic and required no `profit_service` change:
its query filters `pib.status='dispensed' AND dispensed_at BETWEEN
:start AND :end`; `undispense` clears both, so the cost drops out of the
period naturally.

## Files changed

- `app/modules/billing/services/invoice_service.py` — `void_invoice`
  rewritten to mirror `refund_invoice`; new `_undispense_dispensed_items`
  helper; `refund_invoice` now calls it before releasing reservations;
  module docstring updated.
- `tests/integration/billing/test_billing_e2e.py` — new
  `test_void_reverses_collected_money` (mirrors TASK-105's
  `test_refund_reverses_collected_money`, but for void): partially_paid
  invoice + payment → void → payment voided, paid_total 0, double-void
  rejected, payment-methods/revenue 3-way reconciliation both exclude the
  voided invoice.
- `tests/integration/billing/test_billing_reversal_stock.py` — new,
  service-layer tests (direct `invoice_service`/`dispense_service`/
  `payment_service` calls, following the TASK-112 test pattern since HTTP
  route setup for a full dispense scenario is out of scope):
  - `test_refund_after_dispense_restores_stock_and_cogs` — dispense → pay
    in full (visit auto-completes) → refund: batch.actual_quantity
    restored, reserved_quantity back to 0, PIB `released`, invoice
    `refunded`/paid_total 0, visit back to AWAITING_PAYMENT,
    `profit_service.get_profit_summary` COGS goes from 20000 → 0.
  - `test_void_after_dispense_restores_stock` — dispense → partial payment
    (`partially_paid`) → void: same stock/PIB restoration, payment voided,
    invoice `void`, visit asserted still AWAITING_PAYMENT (was never
    COMPLETED — guards the reopen call is a safe no-op here).

No Alembic migration needed (no schema change).

## Testing

Isolated Docker stack `fix119` (api 9951, postgres 5451, redis 6433), built
from the worktree's own `Dockerfile` (bypassed `docker-start.sh` — its CRLF
line endings break under Git Bash on this checkout, unrelated to this fix;
ran `alembic upgrade head` and `uvicorn` directly instead), migrated to head
`0069`, torn down after the run (`down -v`, image removed). Ports/volumes
kept fully separate from `main`/`dev`/`w2e` stacks — confirmed no leakage
onto 9999/5434/5436/6380/6382 after fixing an initial compose-override
merge mistake (caught before any container bound the wrong port).

```
pytest -q --tb=short tests/integration/billing tests/integration/reports tests/integration/pharmacy
→ 108 passed, 1 failed (tests/integration/reports/test_reports_e2e.py::test_visit_volume_report)
```

The one failure is **pre-existing on unmodified `origin/dev`** — verified by
`git stash` + re-running that single test on the clean checkout, same
`assert 0 >= 1` failure (looks like a date/timezone-boundary flake in an
unrelated visit-volume report test). Not a regression from this change.

All new/changed tests pass:
- `test_void_reverses_collected_money` — pass
- `test_refund_after_dispense_restores_stock_and_cogs` — pass
- `test_void_after_dispense_restores_stock` — pass
- Full existing `tests/integration/billing/*` suite (TASK-105/TASK-112
  regression coverage included) — pass, no double-reversal.

`ruff check app tests` / `mypy app`: both re-run scoped to changed files and
diffed against `origin/dev` (via `git stash`) to isolate new issues —
**0 new** in either tool. (Repo-wide `ruff`/`mypy` both have large pre-existing
baselines — 455 ruff errors mostly in unrelated `tests/unit/vitals/`, 50 mypy
errors scattered across the codebase — none touched by this change; the 3
mypy errors mypy reports inside `invoice_service.py` are in
`_recalculate_totals`, lines away from anything this fix touched, and were
already present before this diff at the same relative lines.)

## Review focus suggestions

- Confirm the void/refund ordering (`_undispense_dispensed_items` →
  `_release_pharmacy_reservations` → void payments → recalc → reopen visit)
  matches intent and there's no path where `_recalculate_invoice_paid_total`
  could flip a terminal `void`/`refunded` status back open (it explicitly
  early-returns on those two statuses — unchanged, reused as-is).
- `_undispense_dispensed_items` swallows exceptions (best-effort, matching
  `_release_pharmacy_reservations`'s existing style) — confirm that's the
  right failure mode for a financial-integrity fix vs. surfacing the error.
- No changes were made to `payment_method_service.py` / `revenue_service.py`
  — the fix corrects the source data (payments/status) rather than the
  report queries, per the task's own analysis.
