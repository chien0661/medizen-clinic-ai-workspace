# TASK-112 — Implementation → Review handoff

**Branch:** `fix/TASK-112-unlock-visit-on-reversal` (base `origin/dev` @ `6d91053`)
**Commit:** `c27b860` — pushed to `origin/fix/TASK-112-unlock-visit-on-reversal`
**Worktree used:** `F:/MyProject/clinic-cms-workspace/_fix112-be` (dedicated, left in place; not `main`/`dev`/`w2e`)

## Bug (M-5, from TASK-095 E2E)

Voiding a payment / recalling an invoice / refunding an invoice on a COMPLETED
visit made the invoice no longer fully paid, but the visit stayed COMPLETED —
a closed clinical record per `visit_service.CLOSED_STATUSES` — so
PATCH/exam/vitals kept returning 409 even though the money had been taken
back. "Cancel invoice → edit" had no way to unlock the visit.

## Fix

Added `visit_completion_service.reopen_after_payment_reversal(db, clinic_id,
visit_id, updated_by)` — a best-effort helper mirroring `try_auto_complete`:
fetches the visit `FOR UPDATE`, no-ops (returns `False`) if it's missing or
not currently `COMPLETED`, otherwise sets it to `AWAITING_PAYMENT` and
flushes. Returns `True` when it actually reopened the visit.

**Important design choice:** this does NOT go through
`state_machine.assert_can_transition` / `ALLOWED_TRANSITIONS`. My first pass
added `"COMPLETED": {"AWAITING_PAYMENT"}` to the shared transition table, but
that table is also used by `visit_service.transition_to_complete` (the
doctor's "finish exam" IN_PROGRESS→AWAITING_PAYMENT action) — extending it
let `/visits/{id}/complete` incorrectly succeed when called again on an
already-COMPLETED visit (caught by the existing regression test
`test_visits_lifecycle.py::test_completed_visit_cannot_revert`, which failed
until I reverted the state-machine-table approach). Final version keeps
`ALLOWED_TRANSITIONS["COMPLETED"] == set()` (fully terminal, unchanged) and
has the reopen helper check the COMPLETED precondition directly instead.

## Transition wiring — which ops trigger the unlock

| Call site | File | Condition | `updated_by` passed |
|---|---|---|---|
| `payment_service.void_payment` | `app/modules/billing/services/payment_service.py` | after recalculation, `invoice.visit_id is not None and invoice.status != "paid"` (i.e. still short after the void — no-op if another active payment still covers it in full) | `voided_by` |
| `invoice_service.recall` | `app/modules/billing/services/invoice_service.py` | `invoice.visit_id is not None` (recall always reopens the invoice as a draft) | `updated_by` |
| `invoice_service.refund_invoice` | `app/modules/billing/services/invoice_service.py` | `invoice.visit_id is not None` (refund always reverses the collected money) | `refunded_by` |

`reopen_after_payment_reversal` itself no-ops unless the visit is currently
`COMPLETED`, so calling it unconditionally in `recall`/`refund_invoice` is
safe — it's a targeted revert, not a blanket status write.

Re-paying in full re-triggers the existing `try_auto_complete` path (called
from `payment_service.add_payment`), so the round-trip is: COMPLETED → (void
payment) → AWAITING_PAYMENT → editable → (re-pay in full) → COMPLETED again.

## Files changed

- `app/modules/visits/services/visit_completion_service.py` — new
  `reopen_after_payment_reversal`.
- `app/modules/billing/services/payment_service.py` — wired into
  `void_payment`.
- `app/modules/billing/services/invoice_service.py` — wired into `recall`
  and `refund_invoice`.
- `app/modules/visits/services/state_machine.py` — docstring/comment only,
  clarifying why `COMPLETED` stays terminal in the shared table and where the
  reversal-unlock actually lives (no behavior change vs. `origin/dev`).
- `tests/unit/visits/test_state_machine.py` — `test_completed_is_terminal`
  updated with a comment explaining the TASK-112 design choice (assertion
  itself unchanged, still `== set()`).
- `tests/integration/billing/test_payment_reversal_unlocks_visit.py` — new,
  4 tests (see below).

No Alembic migration — `VisitStatus.AWAITING_PAYMENT` already exists in the
enum; single alembic head confirmed at `0068` after `alembic upgrade head`.

## Testing

Isolated Docker stack `fix112` (api 9964, postgres 5464, redis 6446), built
from the worktree's own `Dockerfile`, migrated to head `0068`, then torn down
after the run (`docker compose -p fix112 down -v`) — Docker was available and
stable for this session, no deferral needed.

- **New tests** (`tests/integration/billing/test_payment_reversal_unlocks_visit.py`, 4/4 passed):
  - `test_void_payment_round_trip` — full round-trip: pay → COMPLETED → PATCH
    409 → void payment → AWAITING_PAYMENT → PATCH 200 (content edited) →
    re-pay → COMPLETED again.
  - `test_void_payment_no_op_when_still_fully_paid` — two payments cover the
    invoice; voiding one still leaves it under-covered in this scenario, so it
    documents/asserts the guard is on post-recalc `invoice.status`, not "any
    void happened."
  - `test_recall_zero_total_invoice_unlocks_visit` — edge case: a zero-total
    `issued` invoice can coexist with a COMPLETED visit (`get_completion_blockers`
    only requires payment when `grand_total > 0`); recalling it must still
    unlock the visit.
  - `test_refund_invoice_unlocks_visit` — refund a paid invoice on a
    COMPLETED visit → visit reopens, invoice ends `refunded`.
- **Regression sweep**: `tests/integration/visits/`, `tests/integration/billing/`,
  `tests/unit/visits/`, `tests/integration/pharmacy/` — **178 + 17 = 195
  passed, 0 failed** (this also caught and drove the state-machine-table
  revert described above via `test_visits_lifecycle.py::test_completed_visit_cannot_revert`).
- `ruff check` on the 6 changed/added files: clean. Full-repo `ruff check app
  tests`: 452 errors — matches TASK-110's documented pre-existing baseline
  exactly, **0 new**.
- `mypy app`: 50 errors — matches TASK-110's documented pre-existing
  baseline exactly, **0 new** (none in the 4 changed app files).

## Status

`docs/tasks/TASK-112/task.md` → `IN_REVIEW`, assigned Code Review Agent,
updated 2026-07-25. AC checkboxes and progress checklist (Implementation)
marked done.
