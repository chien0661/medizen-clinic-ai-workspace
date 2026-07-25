# Review Report — TASK-119 (billing reversal: H-6 void + H-5 refund→stock)

**Reviewer:** Code Review Agent
**Date:** 2026-07-26
**Branch:** `fix/TASK-119-billing-reversal` @ `f6bbe89` (base `origin/dev` `c24f5fe`)
**Worktree:** `F:/MyProject/clinic-cms-workspace/_fix119-be`
**Decision:** **APPROVED → IN_TESTING**

## Scope reviewed

Diff `git diff origin/dev...HEAD` — 3 files, +765/-6:
- `app/modules/billing/services/invoice_service.py` (`void_invoice` rewrite, new `_undispense_dispensed_items`, `refund_invoice` undispense call, docstrings)
- `tests/integration/billing/test_billing_e2e.py` (+`test_void_reverses_collected_money`)
- `tests/integration/billing/test_billing_reversal_stock.py` (new, 2 service-layer tests)

No changes to `payment_method_service.py` / `revenue_service.py` — correct: the fix corrects source data (payments + status + stock), not report queries.

## Correctness verdict

### H-6 — void reverses collected money ✅
Old `void_invoice` on `origin/dev` only set `status='void'` (verified via `git show`). Rewrite now mirrors `refund_invoice`/TASK-105 exactly:
1. undispense + release reservations (if `visit_id`),
2. void every active `Payment` (`is_voided=True`, `voided_at`, `void_reason`),
3. set `status='void'` (terminal) **then** call `_recalculate_invoice_paid_total` → paid_total 0 / balance_due back up,
4. `reopen_after_payment_reversal` (TASK-112, no-op unless COMPLETED).

`_recalculate_invoice_paid_total` early-returns on `void`/`refunded` (payment_service.py:60-61), so the recalc cannot flip a terminal status back open — status-flip risk is closed. `allowed_statuses` unchanged (`{issued, partially_paid}`); `paid` still routes only through refund.

### H-5 — undispense restores stock + COGS ✅
New `_undispense_dispensed_items` selects distinct `prescription_id`s with `in_house_status='dispensed'` and calls `dispense_service.undispense` per prescription. Verified against `undispense` (dispense_service.py:172-281): it restores `batch.actual_quantity += qty` **and** `reserved_quantity += qty`, records a `'return'` stock_movement, flips pib + `in_house_status` back to `'reserved'`. The subsequent `_release_pharmacy_reservations` then matches those now-`reserved` rows and fully frees them (`status='released'`, `reserved_quantity` decremented). Net batch state = fully restored, `reserved_quantity` back to 0 — asserted and passing in both new tests. COGS reverses automatically (profit_service filters `pib.status='dispensed'`, which undispense clears); no profit_service change needed and none made.

### No TASK-105 regression ✅
`git show origin/dev` confirms refund's payment-void + recalc block (lines 701-733) pre-dates this diff. The diff only *inserts* the `_undispense_dispensed_items` call before `_release_pharmacy_reservations` — payment reversal is neither duplicated nor altered.

## Double-reversal / idempotency ✅
- Refund requires `status=='paid'`; after refund → `refunded` → second call raises `BusinessRuleError`.
- Void requires `status ∈ {issued, partially_paid}`; after void → `void` → second call raises.
- Terminal guards therefore prevent any second undispense/payment-void → no double-restore, no negative stock.
- Reserved-but-not-dispensed items: undispense finds 0 rows, release handles them → no missed items, no double-restore.
- Mixed dispensed+reserved: undispense flips dispensed→reserved, release frees all reserved → clean.
- Void of unpaid `issued` invoice: empty payment loop, recalc keeps paid_total 0 → works.
- API double-void guard: test asserts `/payments/{id}/void` returns 400 after invoice void (payment already voided).

## 3-way reconcile ✅
`test_void_reverses_collected_money` asserts payment-methods `total == revenue total_paid == 150000` after voiding invoice A (its 120000 excluded from both). Reconcile holds.

## Findings

- **MINOR (observation, not blocking):** `_undispense_dispensed_items` swallows all exceptions (best-effort, returns 0 + logs `pharmacy_undispense_failed`). If undispense throws mid-loop, money still reverses but stock may be left partially unrestored, silently. This intentionally mirrors the pre-existing `_release_pharmacy_reservations` error-handling contract and the task's "reuse TASK-105 pattern" instruction, so it is not a regression and not a blocker — flagged for Test Agent to probe the failure path.
- **MINOR:** Redundant (harmless) visit reopen — `undispense` itself reverts a COMPLETED visit to AWAITING_PAYMENT, and void/refund then call `reopen_after_payment_reversal`; both target the same state.

No CRITICAL or MAJOR issues.

## Checks run
- Full diff reviewed `--unified=3`; precedent functions (`refund_invoice`, `undispense`, `_recalculate_invoice_paid_total`, `_release_pharmacy_reservations`) read and cross-checked.
- `git show origin/dev` on `void_invoice` and `refund_invoice` to confirm rewrite vs. pre-existing payment logic.
- Python AST syntax check (UTF-8) on all 3 changed files → **SYNTAX_OK**.
- `ruff` on host = broken (`Exec format error` — cannot execute binary), consistent with handoff note; mypy likewise host-broken. Handoff reports **0 new** ruff/mypy scoped to changed files (diffed vs origin/dev); accepted with spot-check caveat — Test Agent to re-run in the isolated stack.
- Test suite: handoff reports 108 passed / 1 failed; the 1 failure (`test_visit_volume_report`) confirmed pre-existing on clean `origin/dev` via git stash. Accepted as unrelated flake.

## Quality gate
No critical/major issues; tests meaningful and assert money+stock+COGS+reconcile; no TASK-105 regression. **APPROVED.**
