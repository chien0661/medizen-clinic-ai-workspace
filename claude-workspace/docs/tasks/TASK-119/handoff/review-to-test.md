# Handoff: TASK-119 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary
`void_invoice` rewrite (H-6) correctly mirrors `refund_invoice`/TASK-105 — voids active payments, recalcs paid_total→0/balance_due, releases reservations, reopens COMPLETED visit — and the new `_undispense_dispensed_items` helper (H-5), called before reservation release in both refund and void, restores `batch.actual_quantity`/`reserved_quantity` and reverses COGS for already-dispensed items. Terminal-status guards prevent double-reversal; no TASK-105 regression; 3-way reconcile holds.

## Key Findings (MINOR, for awareness)
- `_undispense_dispensed_items` swallows exceptions (best-effort, mirrors existing `_release_pharmacy_reservations`) — money reverses even if stock restore fails; verify this failure mode is acceptable.
- Visit reopen happens both inside `undispense` and via `reopen_after_payment_reversal` — redundant but harmless (same target state).

## Focus Areas for Testing
- Void of a **partially_paid, already-dispensed** invoice: money reversed (paid_total 0, payment voided) AND stock restored (actual_quantity + reserved_quantity) AND COGS drops out.
- Refund after full-pay + dispense: stock/COGS reversal + visit → AWAITING_PAYMENT + no TASK-105 payment-reversal regression.
- 3-way reconcile (payment-methods total == revenue total_paid == SUM paid_total) after void and after refund.
- Idempotency: double-void / double-refund rejected; mixed dispensed+reserved items on one visit; no negative stock.
- Re-run `ruff check`/`mypy` in the isolated stack (host tooling is binary-broken) to confirm 0 new issues.
- Confirm `test_visit_volume_report` failure is pre-existing (not caused by this change) in your run.
