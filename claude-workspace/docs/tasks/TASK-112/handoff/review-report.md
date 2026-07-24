# Code Review Report — TASK-112

**Task:** [Medium→cao] Đảo tiền (void/refund/recall) trên visit COMPLETED không mở khóa visit (M-5)
**Branch:** `fix/TASK-112-unlock-visit-on-reversal` (base `origin/dev` @ `6d91053`), commit `c27b860`
**Worktree:** `F:/MyProject/clinic-cms-workspace/_fix112-be`
**Reviewer:** Code Review Agent · **Date:** 2026-07-25
**Diff:** `git -C .../_fix112-be diff origin/dev...HEAD --unified=3` — 6 files, +571/-2

## Decision: APPROVED → IN_TESTING

No critical or major issues. Two minor test-quality notes below; neither blocks.

---

## Key-risk verdict — shared state-machine table unchanged (CONFIRMED SAFE)

`app/modules/visits/services/state_machine.py`: the `ALLOWED_TRANSITIONS`
dict is **behaviorally identical to origin/dev**. The diff touches only the
module docstring and one trailing comment; `"COMPLETED": set()` (terminal)
and every other entry are unchanged. `assert_can_transition` is untouched.
Therefore `visit_service.transition_to_complete` / the doctor "finish exam"
action and `/visits/{id}/complete` are NOT loosened — an already-COMPLETED
visit still cannot re-complete. The reopen path is fully separate and guarded:
`reopen_after_payment_reversal` fetches the visit `FOR UPDATE` and returns
`False` unless `status == COMPLETED`, then sets `AWAITING_PAYMENT`. This is
the correct design; the impl's rejection of the shared-table approach (which
the existing `test_completed_visit_cannot_revert` regression would have
broken) is sound.

## Trigger-correctness (void / recall / refund + no-op guard)

- **void_payment** (`payment_service.py`): guard `invoice.visit_id is not None and invoice.status != "paid"` is evaluated *after* `_recalculate_invoice_paid_total` + `db.refresh(invoice)`, so `status` reflects the post-void state. Correct — no-op when another active payment still fully covers the invoice (status stays `paid`). `updated_by=voided_by`. ✅
- **recall** (`invoice_service.py`): called unconditionally when `visit_id is not None` after status → `draft`; safe because the helper self-guards on COMPLETED. Recall already rejects invoices with active payments, so this only fires for the zero-balance-invoice case. `updated_by`. ✅
- **refund_invoice** (`invoice_service.py`): called unconditionally when `visit_id is not None` after status → `refunded` and payments voided. Helper self-guards. `updated_by=refunded_by`. ✅
- **No-op guard:** two layers — void skips the call when `status == "paid"`; the helper returns `False` for missing/non-COMPLETED visits. Both correct. Round-trip re-completion relies on the existing `try_auto_complete` (from `add_payment`), unchanged. ✅

Consistent with TASK-094 lock rule: `CLOSED_STATUSES = {COMPLETED, CANCELLED}`; `AWAITING_PAYMENT` stays editable — so the reopen genuinely unlocks PATCH/exam/vitals (409→200).

## Findings by severity

### CRITICAL — none
### MAJOR — none
### MINOR
1. **`test_void_payment_no_op_when_still_fully_paid` is misnamed / doesn't cover its stated case** (`tests/integration/billing/test_payment_reversal_unlocks_visit.py:337`). The docstring claims to assert the no-op-when-still-paid guard, but overpayment is rejected so a "still fully paid after voiding one payment" state is unreachable; the test actually voids down to `partially_paid` and asserts the *unlock* path (duplicating the round-trip's void step). The genuine `status == "paid"` no-op branch of the void guard is verified only by code reasoning, not end-to-end. Honest inline comment acknowledges this. Not a blocker — flag for Test Agent.
2. **Stream-of-consciousness inline comment** in that same test (~lines 363-375, "…wait invoice still short. Instead void…") reads as thinking-out-loud left in a committed test. Cosmetic; tidy up when convenient.

## Checks run
- Manual diff review of all 6 files (--unified=3) + surrounding context (recalc helper, CLOSED_STATUSES, recall/refund/void bodies, imports). ✅
- State-machine table origin/dev equivalence confirmed. ✅
- Tests read: round-trip asserts 409→void→AWAITING_PAYMENT→PATCH 200→re-pay→COMPLETED; recall/refund unlock asserted with invoice end-states (`draft`/`refunded`); regression `test_visits_lifecycle.py::test_completed_visit_cannot_revert` confirmed present, asserts COMPLETED→complete = 409. ✅
- `py_compile` on all 6 changed files → COMPILE_OK. ✅
- **ruff / mypy: NOT run on host** — host binaries broken (WinError 193 / "Exec format error"), matching the known-unstable-tooling memory note. Relied on impl handoff's Docker-stack evidence (195 passed, 0 failed; ruff/mypy 0 new vs TASK-110 baseline) + byte-compile + manual read. Test Agent should re-run in the Docker stack.

## Quality gates
- [x] No critical/major issues
- [x] Round-trip + regression genuinely asserted
- [x] Follows CLAUDE.md standards; no secrets/sensitive logs (log fields are ids only)
- [~] Lint/type-check not host-verified (tooling broken) — deferred to testing in Docker
- [x] Review report created
