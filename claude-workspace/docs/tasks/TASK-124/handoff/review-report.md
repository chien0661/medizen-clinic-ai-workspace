# Review Report — TASK-124 Phase 1 (BE core + backfill)

**Reviewer:** Code Review Agent
**Date:** 2026-07-26
**Branch:** `feature/TASK-124-multi-unit` @ `05272e8` (off `origin/dev` `1aeaf13`)
**Worktree:** `F:/MyProject/clinic-cms-workspace/_fix124-be`
**Scope:** Phase 1 of 3 — `unit_conversion` table + `Medicine.sell_unit` + resolver. Must be **behavior-neutral**.

## Decision: APPROVED → IN_TESTING

No CRITICAL or MAJOR issues. Behavior-neutrality, purchase-in regression safety, migration/backfill safety, and single-head all verified. Three MINOR notes below (none blocking).

---

## Scope verification

- 7 files, +648/-5. Diff limited to inventory model/service + migration + 2 test files. No prescribe/dispense/invoice/reports/FE changes — matches "Phase 1 only" claim.
- `dosage_form_id` correctly **NOT** re-added: already added + backfilled by migration `0061` (confirmed `0061_*.py:65`). Migration 0070 does not touch it. No duplicate column/migration.

## Migration 0070 — safety, idempotency, behavior-neutrality: PASS

- **Single head:** only `0070` revises `0069`; chain 0068→0069→0070 clean, no fork.
- **Ordering:** `sell_unit` add-nullable → backfill `= base_unit` → set NOT NULL (safe, no null-violation). Table create → backfill INSERTs → RLS applied **last**. Confirmed correct: `apply_rls_with_tenant_isolation` sets `FORCE ROW LEVEL SECURITY` with a `USING (clinic_id IS NULL OR clinic_id::text = current_setting('app.current_clinic_id'))` policy — concrete-`clinic_id` INSERTs during migration (no GUC set) would be blocked if RLS were enabled first, so inserting before enable is the correct choice. RLS `USING` allows `clinic_id IS NULL` (future global rows).
- **No duplicate/zero rows:** base→base factor 1 (>0) for every medicine; purchase→base only where `purchase_unit IS NOT NULL AND purchase_unit <> base_unit AND pack_size > 0` — the `<> base_unit` guard prevents colliding with the base→base row, and `pack_size > 0` guarantees factor > 0 (respects the `factor_positive` CHECK). One row max per (medicine, from, to).
- **Idempotent-safe:** both INSERTs use `ON CONFLICT (medicine_id, from_unit, to_unit) DO NOTHING` against the unique constraint — re-run cannot create duplicates.
- **No quantity/price/stock change:** migration only adds a column (defaulted to existing `base_unit`) and inserts conversion rows that all resolve to 1× today (sell==base). No UPDATE touches `Batch.actual_quantity`, prices, thresholds, or existing snapshots.
- **Downgrade clean:** revoke → remove RLS → drop indexes → drop table → drop column. Additive/nullable-safe, no data-dependent step.

## Purchase-in regression: SAFE

`_base_per_purchase(medicine)` returns `pack_size` when `purchase_unit` is unset or `== base_unit`; otherwise the resolver factor, falling back to `pack_size` on `UnitConversionError`. Backfill stores `purchase→base = pack_size`, so both quantity and per-unit-cost derive from one identical factor. For 5 packs × 100 @ 300/pack → qty 500, unit_cost 3.00 on both the resolver path and the fallback path (asserted by `test_purchase_in_identical_with_and_without_conversion_row`). `Numeric(18,6)` factor (e.g. `100.000000`) is numerically equal to the legacy `Decimal(pack_size)`; column coercion normalizes. Matches legacy exactly.

## Resolver (`unit_service.py`): SOUND

`to_base` / `from_base` / `conversions_for` / `base_per_unit`. Decimal throughout; `unit == base_unit` → factor 1 without a row; unknown unit → `UnitConversionError` (subclass of `BusinessRuleError`, coded). Non-positive rows defensively skipped. Direct `unit→base` only — sufficient for Phase 1 (backfill creates direct rows only); multi-hop deferred to Phase 2, acceptable.

## Tests: GENUINE (25)

Unit (9): factor-1 identity with/without row, conversion factor, inverse, unknown→raise, non-positive skip, Decimal precision (2.5 lo → 25.0 ml). Integration (3, real DB): `sell_unit` ORM default = base_unit, resolver reads real selectin-loaded rows, purchase-in identical with/without conversion row. Regression suite `test_inventory_e2e.py` (13) retained. Assertions are meaningful, not coverage-padding.

## Security

No secrets/tokens/TODO/print in new code. GRANT scoped to `cms_app`. RLS applied to the new table. Input is server-derived (migration copies `clinic_id` from medicine); resolver takes typed args. No injection surface.

## Quality checks

- **ruff / mypy / pytest — could NOT run on host:** ruff binary fails `WinError 193`; host Python is 3.10 but the app requires 3.11 (`datetime.UTC`). This is the known-broken host tooling noted in the brief. Relied on the implementation's isolated-Docker verification (25/25 pass; ruff clean on new files; mypy 0 new — the one `# type: ignore[assignment]` on `unit_conversion.clinic_id` mirrors the pre-existing `dosage_form.py:27` pattern).
- **Spot-checks done on host:** `py_compile` clean on all 7 files; manual diff read; single-head grep; secret/TODO grep; RLS + 0061 confirmation.

## Findings (all MINOR — non-blocking)

1. **MINOR — selectin on every Medicine read** (`medicine.py`, `unit_conversions` relationship `lazy="selectin"`). Fires one extra (batched) SELECT on every `Medicine` load app-wide, including hot paths that don't need conversions. Functionally neutral and chosen so the resolver works off a plain `Medicine` in async (a `noload` relationship would raise on lazy access in async). Recommend Phase 2 revisit: `noload`/`raiseload` + explicit `selectinload` only at conversion-consuming callers, for consistency with the `dosage_form` relationship (`lazy="noload"`).
2. **MINOR — degenerate pack_size** (`purchase_in_service.py:_base_per_purchase`). For invalid data (`pack_size` NULL or 0) with `pack_quantity` given, the new fallback returns `Decimal(pack_size or 1) = 1`, whereas legacy would crash (`Decimal(None)`) or yield qty 0. Strictly safer, but technically not byte-identical for invalid data. Not a real regression (legacy behavior was itself broken); noted for awareness.
3. **MINOR — CHECK constraint name** (`factor_positive` in both migration and model `__table_args__`). Behavior-neutrality of autogenerate depends on Alembic applying the metadata naming convention so both resolve to `ck_unit_conversion_factor_positive`. Implementation verified this in Docker (no autogenerate drift); could not independently reproduce here (host tooling). Test Agent should confirm `alembic check`/autogenerate produces no drift in the test env.

## Quality gate

- [x] No critical/major issues
- [x] Behavior-neutral (purchase-in numbers identical; migration adds-only; factors resolve 1× today)
- [x] Single head 0070; downgrade clean; idempotent backfill
- [~] Tests pass — 25/25 per impl Docker run; not re-runnable on broken host (relied on handoff + manual review)
- [~] Lint/type — 0 new per impl Docker run; host tooling broken (spot-checked py_compile)
- [x] No security issues; follows CLAUDE.md standards

---
---

# Review Report — TASK-124 Phase 2 (wire sell↔base into prescribe / dispense / invoice)

**Reviewer:** Code Review Agent
**Date:** 2026-07-26
**Branch:** `feature/TASK-124-multi-unit` @ `123fef3` (Phase-1 `05272e8` already APPROVED)
**Worktree:** `F:/MyProject/clinic-cms-workspace/_fix124-be`
**Scope:** Phase 2 of 3 — prescribe in `sell_unit`; reserve/dispense stock math in `base_unit`; invoice per-sell; surface sell_unit + conversions in search.

## Decision: APPROVED → IN_TESTING

No CRITICAL or MAJOR issues. Backward-compat (sell==base byte-identical), conversion + stock-decrement-in-base correctness, and no-regression all verified. Two MINOR notes below (one is the flagged `sell_unit` server_default follow-up — a real but non-blocking gap).

---

## Scope verification

9 files, +552/-31. Diff limited to: `prescription_service.py` (conversion wiring), `medicine_search_service.py` + `prescription_schemas.py` (additive `sell_unit`/`conversions[]`), `medicine.py` (runtime import), `seed_categories.py` (raw-insert `sell_unit` fix), 2 regression test call-site fixes, 2 new test files. No dispense/reservation/invoice service code changed — matches the "reserve/dispense already base-unit primitives; invoice already snapshots per-sell" claim.

## Sell == base byte-identical: CONFIRMED

`_base_qty_for_reservation` short-circuits `if not unit or unit == base_unit: return q` **before any `to_base`/quantize call** — the factor-1 backfill path returns the prescribed Decimal with its exact value/scale (unit test asserts `out.as_tuple() == Decimal("7").as_tuple()`). The unknown-free-text-unit path (no conversion row → `UnitConversionError`) also returns raw `qty`, matching pre-124 behavior where free-text units were treated as base. e2e `test_backfilled_sell_equals_base_is_identical` proves stock (100→80), PIB, and invoice line (20 vien @ 2000 = 40000) all identical to today. Existing prescriptions/dispense/invoices unaffected: quantize only runs on the sell≠base-with-row branch.

## Conversion + stock-decrement-in-base: CORRECT

- `_add_item_to_prescription` loads the medicine once (selectin `unit_conversions`), converts sell→base via `_base_qty_for_reservation`, and passes **base_qty** to BOTH the availability check (`_resolve_dispense_source`) and `reserve_for_prescription`. `PrescriptionItem.quantity`/`unit`/`unit_price` store the **sell** values verbatim (unit_price = `med.sale_price`, which is per-sell). Correct separation.
- Stock chain is fully in base: `reservation_service` distributes `base_qty` via FEFO; `dispense_service` decrements `batch.actual_quantity -= pib.reserved_quantity` (base); reversal uses `dispensed_quantity or reserved_quantity` (base). Inventory stays consistent. e2e: ml→lọ 25 ml reserves/dispenses 2.5 lọ (stock 10→7.5); vỉ→viên 3 vỉ → 30 viên (stock 100→70).
- Invoice: no code change needed — `_pull_lines_from_visit` snapshots sell qty/unit/price verbatim. `line_total = sell_qty × price_per_sell` reconciles (125 000 = 25×5000; 90 000 = 3×30 000; 40 000 = 20×2000) — all asserted.
- `update_item`: re-reservation converts the new sell qty → base. Its `_resolve_dispense_source(..., "in_house")` passes an explicit source, which **short-circuits before `quantity` is used** — so the sell/base value there is inert, not an inconsistency (the reservation itself correctly uses base_qty).

## Rounding-drift risk: LOW / SOUND

- ROUND_HALF_UP quantize at 6 dp matches `unit_conversion.factor` `Numeric(18,6)`; base stock is plain `Numeric` so fractional base is allowed (not forced integer). Discrete forms (integer factor) yield whole numbers unaffected by quantize.
- **No reserve≠dispense drift:** reservation persists the quantized base qty in `prescription_item_batch.reserved_quantity`; dispense reads that same persisted value (does **not** re-convert). Reserve base == dispense base exactly.
- **No stock-negative / over-reserve risk:** the availability check uses the *same* quantized base_qty as the reservation, so any half-up rounding (≤ 5e-7) is consistent on both sides; the `reserved_quantity <= actual_quantity` DB CHECK still guards. Money path carries zero conversion rounding (invoice = user-entered sell qty × price), so totals are exact.

## No regression to TASK-108/112/119/120/123: CONFIRMED

Only the *quantity value* passed to `reserve_for_prescription` changed (still a pure base-unit primitive); FEFO / dispense movement / pending-issued guards / visit-close guards / TASK-119 reversal / TASK-108/123 invoice-sync paths are untouched. Impl regression sweep: 205 passed. The single remaining "error" is a **teardown-only** FK on `invoice_number_counter` (pre-existing TASK-068 test-teardown gap; test body passed) — unrelated to Phase 2.

## Phase-1 defects fixed here: SOUND, test/model-only

1. Raw `INSERT INTO medicine` missing `sell_unit` → fixed by adding `sell_unit = base_unit` to 2 regression tests + `seed_categories.py`. Test/seed-only, no app-logic change.
2. `UnitConversion` mapper not registered → runtime import at bottom of `medicine.py` (`noqa: E402,F401`). No import cycle (`unit_conversion.py` doesn't import `medicine`). Model-only, correct.

## Tests: GENUINE (6 unit + 3 integration)

Unit file pins: factor-1 identity (value+scale), None-unit passthrough, unknown-unit fallback, discrete vỉ→viên (30), fractional ml→lọ (2.5), ROUND_HALF_UP 6dp (5×0.333333=1.666665). e2e asserts real base-unit stock decrement + sell-unit invoice reconciliation across all three cases. Not coverage-padding.

## Quality checks

- **ruff / mypy / pytest — could NOT run on host** (confirmed: ruff binary fails `WinError 193`; host Python 3.10 vs app-required 3.11). Relied on impl isolated-Docker run (all new tests pass; 205-regression green; 0 new ruff/mypy).
- **Host spot-checks:** single head `0070` confirmed (0068→0069→0070, no fork; no new migration); both new test files present; manual diff read of all 9 files; `_resolve_dispense_source` short-circuit verified; dispense/reservation base-unit chain verified by source read.

## Findings (all MINOR — non-blocking)

1. **MINOR (real gap) — `sell_unit` NOT NULL has no DB server_default.** The ORM `default` callable is bypassed by raw-SQL INSERTs; this already broke 2 tests + the seed and was patched at those call-sites, but any *future* raw insert / bulk COPY / external script will still hit `NotNullViolationError`. A durable fix (static `server_default` or BEFORE-INSERT trigger defaulting `sell_unit := base_unit`) is correctly deferred (needs a new migration, would move head off 0070). Track as a Phase-3 / follow-up migration. Not blocking Phase 2 (behavior is correct and covered).
2. **MINOR — extra Medicine load on `_add_item_to_prescription`.** The medicine is now loaded unconditionally (when `medicine_id` present) even if all snapshot fields were supplied, plus the selectin `unit_conversions` query — needed for conversion. Functionally neutral (sell==base ⇒ base_qty==qty); minor extra query on a non-hot path. Acceptable.

## Quality gate

- [x] No critical/major issues
- [x] sell==base byte-identical (short-circuit before quantize; unit + e2e asserted)
- [x] Conversion correct; stock decremented in BASE; invoice reconciles sell qty×price
- [x] No reserve≠dispense drift; no stock-negative/over-reserve risk
- [x] No TASK-108/112/119/120/123 regression (205 green per impl Docker run)
- [x] Single head 0070; no new migration
- [~] Tests pass — 6+3 new + 205 regression per impl Docker run; not re-runnable on broken host (relied on handoff + manual review)
- [~] Lint/type — 0 new per impl Docker run; host tooling broken (spot-checked single-head + diff)
- [x] No security issues; follows CLAUDE.md standards
