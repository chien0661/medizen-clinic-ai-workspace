# Handoff: TASK-112 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary
Payment-reversal unlock (void / recall / refund → visit COMPLETED → AWAITING_PAYMENT) is implemented via a separate, self-guarded `reopen_after_payment_reversal` helper without touching the shared `ALLOWED_TRANSITIONS` table (key risk — verified unchanged, so `/visits/{id}/complete` is not loosened). Triggers and no-op guards are correct; round-trip and the "already-completed can't re-complete" regression are genuinely asserted.

## Key Findings (MINOR, awareness only)
- `test_void_payment_no_op_when_still_fully_paid` is misnamed — it cannot construct a "still fully paid after void" state (overpayment rejected) and actually asserts the unlock path. The genuine `invoice.status == "paid"` no-op branch of the void guard is unverified end-to-end.
- Stream-of-consciousness inline comment left in that test (~lines 363-375). Cosmetic.

## Focus Areas for Testing
1. **Re-run in the Docker stack** — host ruff/mypy are broken (WinError 193), so lint/type-check were not host-verified. Re-run the new suite + regression sweep (`tests/integration/visits`, `.../billing`, `tests/unit/visits`, `.../pharmacy`) and confirm ruff/mypy `0 new` vs TASK-110 baseline.
2. **Round-trip** complete → void → AWAITING_PAYMENT (PATCH/exam/vitals 200) → re-pay in full → COMPLETED again.
3. **No-op coverage gap** — the `status == "paid"` guard branch of `void_payment` (visit must STAY COMPLETED). If a genuine still-fully-paid-after-void scenario can be built (or via a partial-payment invoice whose remaining active payments still cover it), assert the visit does NOT reopen.
4. **recall** on a zero-total issued invoice, and **refund** on a paid invoice — visit reopens; invoice ends `draft` / `refunded`.
5. **Never-completed / partial visits** — confirm reversal does not touch a visit that was never COMPLETED (helper returns False).
6. Regression: `/visits/{id}/complete` and `/start` on an already-COMPLETED visit still return 409.
