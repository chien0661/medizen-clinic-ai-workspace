# Handoff: TASK-124 → Test Agent (Phase 2)

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED
**Branch**: `feature/TASK-124-multi-unit` @ `123fef3` (Phase-1 `05272e8` already tested/approved)
**Worktree**: `F:/MyProject/clinic-cms-workspace/_fix124-be`

## Summary
Phase 2 wires the Phase-1 unit resolver into prescribe/dispense/invoice: doctors prescribe in `sell_unit`, all pharmacy stock math (availability check, reserve, dispense, reversal) runs in `base_unit` via `unit_service.to_base` (quantize ROUND_HALF_UP 6dp), while `PrescriptionItem` and invoice lines keep sell qty/unit/price verbatim. Backfilled `sell == base` (factor 1) is byte-identical to today. No dispense/reservation/invoice service code changed; single head stays 0070 (no new migration).

## Key Findings (MINOR — for awareness)
- **Real gap (follow-up):** `Medicine.sell_unit` is NOT NULL with only an ORM `default` — no DB `server_default`/trigger. Raw-SQL inserts must set it explicitly (2 tests + `seed_categories.py` were patched). A future raw insert / bulk load will still hit `NotNullViolationError`. Deferred to a follow-up migration (would move head off 0070). Watch for this if you add fixtures/seeds via raw SQL.
- Medicine is now loaded once per add-item (with selectin `unit_conversions`) even when snapshots are supplied — functionally neutral, minor extra query.

## Focus Areas for Testing
1. **Backward-compat (sell == base):** existing prescribe→dispense→invoice flows must produce identical stock/PIB/invoice numbers as before (factor-1 path, no rounding). This is the core guarantee.
2. **sell ≠ base conversion end-to-end:**
   - Fractional: `ml` sell → `lọ` base (e.g. 25 ml, factor 0.1 → reserve/dispense 2.5 lọ; stock decrements in base; invoice shows 25 ml @ price/ml).
   - Discrete: `vỉ`/`hộp` sell → `viên` base (integer factor → whole base qty).
   - Confirm invoice `line_total = sell_qty × price_per_sell` reconciles.
3. **Stock integrity:** verify `batch.actual_quantity` decrements in BASE and never goes negative; reserved qty == dispensed qty (no reserve/dispense drift); `reserved_quantity <= actual_quantity` CHECK holds under fractional conversions.
4. **update_item re-reservation** with a sell≠base medicine (change qty) → reservation re-derived in base.
5. **No regression** to TASK-108/112/119/120/123 (invoice sync, TASK-119 reversal, pending/visit-close guards). Re-run the billing/pharmacy/prescriptions/visits/services integration suites.
6. **Search API** surfaces `sell_unit` + `conversions[]` correctly (additive; defaults to base_unit/factor-1 for backfilled medicines).
7. **Note:** host ruff/mypy/pytest are broken (WinError 193 / Python 3.10 vs required 3.11) — run in the isolated Docker stack. The `invoice_number_counter` teardown-only FK error is pre-existing (TASK-068), not a Phase-2 failure.
