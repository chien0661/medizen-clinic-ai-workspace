# Handoff: Implementation → Code Review — TASK-124 (Phase 1 of 3)

**Date:** 2026-07-26
**From:** Code Implementation Agent
**To:** Code Review Agent
**Branch:** `feature/TASK-124-multi-unit` (based on `origin/dev` @ `1aeaf13`)
**Commit:** `05272e8` — `feat(inventory): unit_conversion table + Medicine.sell_unit/dosage_form_id + resolver, behavior-neutral backfill (TASK-124 phase 1)`
**Repo:** `clinic-cms` (backend)

---

## Scope of this delivery — Phase 1 of 3 ONLY

This is the **foundation** phase and is **behavior-neutral**: every existing flow
(purchase-in, prescribe, dispense, invoice, reports, alerts) is unchanged. All
conversion factors backfill to resolve **1× today** (sell_unit == base_unit,
factor 1), so no numbers move.

- **Phase 2 (NOT in this delivery):** prescribe / dispense / invoice conversion —
  search returns sell_unit + conversions; prescribe in sell-unit → resolver → base
  for reserve/dispense; invoice line qty/unit/price per sell-unit.
- **Phase 3 (NOT in this delivery):** frontend (MedicinesPage sell_unit + conversion
  table + dosage_form FK picker; PrescriptionTab sell-unit + shown conversion).

---

## What changed (5 files + 2 test files)

### Model
- **`app/modules/inventory/models/unit_conversion.py`** (new) — `UnitConversion(BaseEntity)`:
  `clinic_id` (NULLABLE, override), `medicine_id` FK (→ medicine, `ON DELETE CASCADE`),
  `from_unit`, `to_unit`, `factor Numeric(18,6)`.
  Unique `(medicine_id, from_unit, to_unit)`; CHECK `factor > 0`.
- **`app/modules/inventory/models/medicine.py`** (modified):
  - `sell_unit: str` — **NOT NULL**, defaults to `base_unit` at ORM-insert via an
    SQLAlchemy `default` callable (`_sell_unit_default` reads `base_unit` from the
    insert params) so existing create paths that don't pass it stay behavior-neutral.
  - `unit_conversions` relationship — `viewonly=True`, `lazy="selectin"` so the
    resolver can read conversions off a plain `Medicine` instance in async code.
  - **`dosage_form_id` was NOT added here** — it already exists on `origin/dev`
    (added + backfilled by migration **0061**). The task brief predates that merge.

### Migration
- **`alembic/versions/0070_unit_conversion_and_sell_unit.py`** (new) — single head, `0069 → 0070`.
  1. `medicine.sell_unit` added nullable → backfilled `= base_unit` → set NOT NULL.
  2. `unit_conversion` table + 2 indexes + GRANT.
  3. **Backfill (BEFORE RLS enable, so concrete-`clinic_id` INSERTs are not blocked
     by FORCE RLS):**
     - `base_unit → base_unit`, factor 1, for **every** medicine.
     - `purchase_unit → base_unit`, factor = `pack_size`, where `purchase_unit IS NOT NULL
       AND purchase_unit <> base_unit AND pack_size > 0` (the `<> base_unit` guard avoids
       a duplicate `base→base` row / unique+check conflict).
     - `clinic_id` on each conversion row copied from the medicine.
  4. RLS `apply_rls_with_tenant_isolation` (allows `clinic_id IS NULL`) applied last.
  - Downgrade drops table + column (additive/nullable-safe).

### Services
- **`app/modules/inventory/services/unit_service.py`** (new) — resolver:
  - `to_base(medicine, qty, unit) -> Decimal`, `from_base(medicine, base_qty, unit) -> Decimal`,
    `conversions_for(medicine) -> dict[(from,to), factor]`, `base_per_unit(medicine, unit)`.
  - `unit == base_unit` → factor 1 (no row required). Unknown unit → `UnitConversionError`
    (subclass of `BusinessRuleError`). Decimal throughout. Direct `unit→base` lookup
    (n-level chaining deferred to Phase 2 if needed — backfill only creates direct rows).
- **`app/modules/inventory/services/purchase_in_service.py`** (modified) — quantity AND
  per-unit cost now derived from one factor `_base_per_purchase(medicine)`:
  resolver when `purchase_unit` is a distinct unit with a conversion row, else legacy
  `pack_size` fallback. **Numbers are identical** to before in every branch.

---

## Verification (isolated Docker stack `fix124`: api / pg 5439 / redis 6421 — real Postgres 15 + Redis 7; torn down after)

- **Migration:** `alembic upgrade head` reaches **single head `0070`**; clean
  downgrade `0070→0069` + re-upgrade verified. CHECK constraint name resolves to
  `ck_unit_conversion_factor_positive` (matches model metadata — no autogenerate drift).
- **Backfill (seeded 3 medicines, ran the real migration on them):**
  - M1 (base=vien, purchase=hop, pack=100) → `vien→vien=1` + `hop→vien=100`. ✅
  - M2 (base=ml, no purchase) → only `ml→ml=1`. ✅
  - M3 (base=vien, purchase=vien==base, pack=10) → only `vien→vien=1` (dedup). ✅
  - `sell_unit == base_unit` for all. ✅
- **Purchase-in regression:** with-conversion-row path and pack_size-fallback path both
  produce `actual_quantity = 500` and `unit_cost = 3.00` for 5 packs × 100 @ 300/pack —
  identical to legacy. Existing `test_inventory_e2e.py` (incl. AC6 multi-unit) still green.
- **Tests:** **25 passed / 25** — `tests/unit/test_unit_service.py` (9),
  `tests/integration/inventory/test_unit_conversion_e2e.py` (3, real-DB),
  `tests/integration/inventory/test_inventory_e2e.py` (13, regression).
- **ruff / mypy — 0 NEW:**
  - ruff: all new files clean. The one remaining `I001` in `purchase_in_service.py`
    (a local-import block) is pre-existing — baseline had 2 such, my edit reduced it to 1.
  - mypy: only new error would have been the `clinic_id` NULLABLE-override on
    `unit_conversion.py` (identical to the pre-existing, un-suppressed one on
    `dosage_form.py:27`); suppressed with `# type: ignore[assignment]`. The
    `purchase_in_service.py` `scalar_one_or_none` `[assignment]` error is pre-existing
    (baseline line 49), confirmed via stash.

---

## Review focus / notes

- Confirm the **behavior-neutral** claim: purchase-in numbers unchanged; `sell_unit`
  default callable path; selectin relationship adds a query per Medicine read (functional
  results unchanged) — flag if the extra query is a concern for any hot path.
- Confirm the backfill ordering (INSERT before RLS FORCE) and the `<> base_unit` dedup guard.
- `unit_conversion.clinic_id` set from `medicine.clinic_id` in backfill; model allows NULL
  (global) for future use. RLS `tenant_isolation` allows both.
- Resolver is direct `unit→base` only (sufficient for Phase 1); multi-hop is a Phase-2 concern.

---

# Phase 2 — wire sell↔base conversion into prescribe / dispense / invoice (BACKEND)

**Date:** 2026-07-26 · **Branch:** `feature/TASK-124-multi-unit` · **Status → IN_REVIEW**

## What changed (behavior)
Doctors now prescribe in the medicine's **sell_unit**; all pharmacy **stock math
runs in `base_unit`**, converted via the Phase-1 `unit_service` resolver. For every
backfilled medicine (`sell_unit == base_unit`, factor 1) the numbers are **identical
to before** — the change only manifests when a medicine has `sell_unit != base_unit`
with a `unit_conversion` row.

### Files
- `app/modules/prescriptions/services/prescription_service.py`
  - New helper `_base_qty_for_reservation(medicine, qty, unit)` — sell→base for stock.
  - New helper `_load_medicine(...)` — loads Medicine (+ selectin `unit_conversions`).
  - `_add_item_to_prescription`: loads the medicine once, converts the prescribed
    sell qty → base, uses **base qty** for the stock-availability suggestion AND the
    reservation. `PrescriptionItem.quantity`/`unit`/`unit_price` still store the
    **sell** values verbatim (snapshot semantics unchanged; price is per sell_unit).
  - `update_item`: re-reservation now converts the new sell qty → base too.
- `app/modules/prescriptions/services/medicine_search_service.py` + `schemas`
  - `MedicineSearchResult` now surfaces `sell_unit` + `conversions[]` (new
    `UnitConversionInfo{from_unit,to_unit,factor}`) for the FE (Phase 3). Additive.
- `app/modules/inventory/models/medicine.py`
  - Added a **runtime import** of `UnitConversion` (was `TYPE_CHECKING`-only) so the
    string-based `unit_conversions` relationship always resolves in the mapper — see
    "Phase-1 defects fixed" below.

### Reservation base-qty derivation & rounding rule
`_base_qty_for_reservation`:
1. `unit` unset or `== base_unit` → return `qty` **unchanged** (factor-1 backfill —
   byte-for-byte identical, no quantize).
2. `unit != base_unit` but **no conversion row** → return raw `qty` (legacy free-text
   units were already treated as base by the pre-124 reservation call — unchanged).
3. `unit != base_unit` **with** a conversion row → `unit_service.to_base()` then
   **quantize ROUND_HALF_UP at 6 dp** (matches `unit_conversion.factor` `Numeric(18,6)`).
   Base stock is a plain `Numeric`, so fractional base qty is allowed and **not**
   forced to an integer: a divisible form (sell `ml` → base `lọ`) legitimately reserves
   a fractional base amount; a discrete form (sell `vỉ`/`hộp` → base `viên`, integer
   factor) always yields a whole number.

Reservation persists the base qty in `prescription_item_batch.reserved_quantity`
(and dispense decrements `batch.actual_quantity` in base), so **no new column** was
needed on `prescription_item` — head stays at **0070**.

### Invoice wiring (per sell_unit)
`invoice_service._pull_lines_from_visit` already snapshots `quantity` / `unit` /
`unit_price` **verbatim** from `prescription_item` (which holds the sell values +
per-sell price). Therefore **no invoice code change** was required: medicine lines
carry sell qty + sell unit + price/sell, and `line_total = sell_qty × price_per_sell`.
Verified reconciling in the e2e (25 ml × 5000/ml = 125 000). TASK-119 reversal /
TASK-108/123 sync paths untouched.

### Regression safety
- **Backfilled `sell == base` → regression-safe: YES.** Factor-1 path returns the
  exact prescribed qty with no quantize; e2e asserts stock/PIB/invoice all identical.
- **No TASK-108/112/119/120/123 regression: YES.** Full service-level suites green
  (see below). Reservation FEFO / dispense movement / pending-issued guards /
  visit-close guards preserved (I only changed the *quantity value* passed to
  `reserve_for_prescription`, which remains a pure base-unit primitive; the manual
  `POST /pharmacy/reserve` route is left as a base-unit primitive by design).

### Phase-1 defects found & fixed (surfaced by the Phase-2 regression gate)
These broke the regression suite on the branch and were **not** caused by Phase 2;
fixed minimally without a schema change (head stays 0070):
1. **`sell_unit` NOT NULL without a DB server_default** — raw-SQL `INSERT INTO
   medicine` (2 test files + `scripts/seed_categories.py`) omitted `sell_unit` →
   `NotNullViolationError`. Fixed by adding `sell_unit = base_unit` to those raw
   inserts. **Recommend a durable follow-up** (BEFORE-INSERT trigger defaulting
   `sell_unit := base_unit`, or a static server_default) so any future raw insert is
   safe — deferred because it needs a new migration (would move head off 0070).
2. **`UnitConversion` mapper not registered** — `Medicine.unit_conversions =
   relationship("UnitConversion")` referenced the class only under `TYPE_CHECKING`,
   so `Medicine` ORM use in a process that never imported `UnitConversion` failed
   mapper configuration (`InvalidRequestError: failed to locate a name
   'UnitConversion'`). Fixed with a runtime import at the bottom of `medicine.py`
   (no import cycle — `unit_conversion.py` doesn't import `medicine`).

### Tests (isolated stack `fix124b`: pg 5438 / redis 6420, `alembic upgrade head`→0070)
- **New Phase-2 tests — all pass:**
  - `tests/unit/prescriptions/test_task124_base_qty_conversion.py` (6) — rounding rule
    + behaviour-neutral fallbacks.
  - `tests/integration/prescriptions/test_task124_sell_unit_conversion_e2e.py` (3,
    real-DB) — (a) `sell == base` regression identical; (b) `ml`→`lọ` fractional
    (25 ml → reserve/dispense 2.5 lọ, stock 10→7.5, invoice 25 ml @ 5000/ml =
    125 000); (c) `vỉ`→`viên` discrete (3 vỉ → 30 viên base, invoice 3 vỉ @ 30 000).
- **Regression sweep: 205 passed, 0 functional failures** across
  `tests/integration/{billing,pharmacy,prescriptions,visits,services}` +
  `test_task123_invariant_enforcement.py` + the new unit file. The **1 remaining
  "error"** is a **teardown-only** FK (`invoice_number_counter` pins the clinic on the
  test's `DELETE clinic` cleanup — a pre-existing TASK-068 test-teardown gap; the test
  **body passed**), unrelated to this change.
- **Docker note:** the shared `w2e` stack (9999/5434/5436/6380/6382) was left
  untouched; an isolated per-run stack `fix124b` was used and torn down.

### ruff / mypy — 0 NEW
Verified against the committed baseline (`git show HEAD:...`): the changed app files
report the **identical** pre-existing ruff findings (import-block `I001`, forward-ref
`UP037`, `F401` — all from the stricter ruff 0.15.22, on lines this change did not
touch) and the same 2 pre-existing mypy errors. New files (`medicine.py` edit + both
new test files + seed edit) add **zero** new ruff/mypy errors; `mypy medicine.py`
clean. (The 2 `seed_categories.py` `B007` warnings pre-date this change.)

---

# Phase 3 — FE (MedicinesPage + PrescriptionTab) + BE admin CRUD gap-fill

**Date:** 2026-07-27 · **Status -> IN_REVIEW**

## Scope of this delivery — Phase 3 of 3

Frontend surface for the Phase 1/2 backend, plus closing an admin-CRUD gap
found on the backend (Phase 1/2 never exposed sell_unit or unit_conversion
writes through the medicine admin API — only the migration/backfill and the
resolver's read path existed).

### A. BE — admin CRUD gap-fill (clinic-cms, worktree _fix124-be)

**Commit:** 8da3a71 — feat(inventory): admin CRUD for unit_conversion + sell_unit/dosage_form_id (TASK-124 phase 3 BE)
**Branch:** feature/TASK-124-multi-unit (pushed, 123fef3..8da3a71)

Checked first (per brief): dosage_form_id was already on
MedicineCreate/Update/Response since Phase 1 — no change needed. sell_unit
and unit_conversion writes were missing — added:

- app/modules/inventory/schemas/medicine_schemas.py — sell_unit: str | None
  added to MedicineCreate/Update, sell_unit: str added to MedicineResponse.
- app/modules/inventory/services/medicine_service.py — create_medicine sets
  medicine.sell_unit only when the caller supplies a value (otherwise the
  model's INSERT-time default sell_unit := base_unit applies unchanged, same
  behavior-neutral guarantee as Phase 1); update_medicine's existing generic
  model_dump(exclude_unset=True) loop already covers sell_unit with no code
  change; _to_response now includes sell_unit.
- app/modules/inventory/schemas/unit_conversion_schemas.py (new) —
  UnitConversionCreate/Update/Response; factor gt=0 + non-blank units
  validated on the schema (reuses the same factor>0 invariant as
  unit_service / the DB factor_positive CHECK).
- app/modules/inventory/services/unit_conversion_service.py (new) —
  list_conversions / get_conversion / create_conversion / update_conversion /
  delete_conversion, all scoped to the medicine's own clinic_id (reuses
  medicine_service.get_medicine for the ownership check -> NotFoundError for
  cross-clinic/unknown medicine_id). Duplicate (medicine_id, from_unit,
  to_unit) -> ConflictError (checked pre-flush + IntegrityError fallback,
  same pattern as hr/services/shift_service.py).
- app/modules/inventory/api/routes.py — new endpoints, gated like the rest
  of the medicine catalog:
  - GET    /medicines/{id}/unit-conversions (medicine.read)
  - POST   /medicines/{id}/unit-conversions (medicine.manage)
  - PATCH  /medicines/{id}/unit-conversions/{conversion_id} (medicine.manage)
  - DELETE /medicines/{id}/unit-conversions/{conversion_id} (medicine.manage)

No new migration (head stays 0070) — only schema/service/route additions on
top of the existing table + column.

**Tests (new, isolated stack fix124c — pg 5437/redis 6419/api 9937, alembic
upgrade head -> 0070, torn down after):**
tests/integration/inventory/test_task124_unit_conversion_admin_crud.py — 9
tests: create medicine with explicit sell_unit, create without (defaults to
base_unit), update sell_unit, create/list/update/delete a conversion row,
duplicate-conversion -> ConflictError, unknown medicine_id -> NotFoundError,
cross-clinic medicine -> NotFoundError (no leak). 9/9 pass.
Regression: tests/unit/test_unit_service.py + tests/integration/inventory/ +
Phase-2 test_task124_* (77/77), plus the wider
billing/pharmacy/prescriptions/visits/services integration sweep (191
passed, 1 pre-existing teardown-only error on invoice_number_counter /
TASK-068, same as noted in the Phase 2 handoff — test body passed, unrelated
to this change). ruff clean on both new files (unit_conversion_service.py,
unit_conversion_schemas.py); the 4 new B008 (Depends in default arg) hits in
routes.py are the same pre-existing project-wide style already present on
every other route in that file (30->34, purely additional instances, no new
class of issue). w2e (main dev stack, 9999/5434/5436/6380/6382) was never
touched.

### B. FE (clinic-cms-web, worktree _fix124-web, branch off origin/dev)

**Commit:** 72c429e — feat(ui): manage sell_unit/conversions/dosage_form on medicines + sell-unit prescribing (TASK-124 phase 3)
**Branch:** feature/TASK-124-multi-unit (new, pushed)

- src/pages/admin/MedicinesPage.tsx — new sell_unit select (blank = defer to
  the BE default/base_unit), base_unit relabeled as the stock/threshold unit
  for clarity now that it's no longer synonymous with "sell unit", and a new
  UnitConversionsEditor component: lists a medicine's conversion rows
  (from_unit / factor-editable-inline / to_unit / delete), plus an add-row
  form. Only rendered when editing an existing medicine (needs a
  medicine_id to attach rows to) — a brand-new medicine shows a "save first"
  hint instead. Defensive Array.isArray guard on the conversions list query
  result (same pattern as the existing dosageForms guard in this file) —
  caught a real crash (rows.map is not a function) against the pre-existing
  MedicinesPage.tags.test.tsx mock, which stubs every api.get call with a
  single {data:[...], total:N} shape. dosage_form_id (FK select) was already
  wired since TASK-093 — untouched.
- src/components/doctor/PrescriptionTab.tsx — addMedicine now defaults the
  new draft item's unit to med.sell_unit || med.dosage_form_unit ||
  med.base_unit (was dosage_form_unit || base_unit); a new
  unitConversionHint() helper shows a small "1 lo = 20 ml"-style hint under
  the unit input, derived from medicine.conversions[] for the
  currently-entered unit — only when it differs from base_unit with a known
  non-1 factor (no hint for the backfilled sell_unit == base_unit case).
  Quantity is still entered/sent in the sell unit exactly as before; the
  free-text unit input is unchanged (doctors can still override).
- Types — modules/admin/types.ts: sell_unit?: string added to
  Medicine/MedicineCreate/MedicineUpdate (optional — defensive against stale
  cached responses, matching the existing TASK-093 field style); new
  UnitConversion/UnitConversionCreate/UnitConversionUpdate.
  modules/doctor/types.ts: Medicine gains optional sell_unit +
  conversions?: UnitConversionInfo[] (new UnitConversionInfo type), matching
  the Phase 2 MedicineSearchResult additive fields exactly.
  modules/admin/api.ts: adminMedicinesApi.{list,create,update,delete}
  UnitConversion wired to the new BE routes.
- i18n — locales/{vi,en}/admin.json: new medicines.form.{sellUnit,
  sellUnitHint,unitConversions,unitConversionsHint,unitConversionsSaveFirst,
  unitConversionsEmpty,addConversion,fromUnit,toUnit,factor,
  confirmDeleteConversion,conversion{Create,Update,Delete}Success} +
  medicines.columns.sellUnit.
- DosageFormsPage / InventoryPage — reviewed, no change: InventoryPage
  already displays all stock quantities in base_unit consistently (correct —
  stock is tracked in base_unit by design); DosageFormsPage's unit field is
  display-only free text, unaffected by this task.

**Tests (new):**
- src/tests/admin/MedicinesPage.unitConversions.test.tsx (4) — edit modal
  loads/renders existing conversion rows; add-form POSTs the entered
  from_unit/to_unit/factor; delete (after window.confirm) calls DELETE with
  the row id; create-mode shows the "save first" hint and issues no
  /unit-conversions GET for an unsaved medicine.
- src/tests/doctor/PrescriptionTab-sell-unit.test.tsx (4) — unit defaults to
  sell_unit when present; falls back to dosage_form_unit then base_unit when
  absent (preserves the pre-existing TASK-094 test's exact expectations);
  quy-doi hint shown for a sell_unit != base_unit conversion row; no hint for
  the backfilled sell_unit == base_unit case.

**Full-suite check:** npm run type-check and npm run lint clean on all
changed files (0 new errors/warnings). Targeted suite (9 files touching
Medicines/DosageForms/PrescriptionTab/Inventory): 48/48 pass. Full vitest
run: 117/119 files, 1119/1122 tests pass — the 2 failing files
(ForgotPasswordPage.test.tsx, QueuePage.test.tsx, 3 tests) reproduce
identically on a clean git stash back to origin/dev HEAD, confirmed
pre-existing and unrelated to this change.

## Review focus / notes for Phase 3

- BE: confirm the unit_conversion_service ownership check (via
  medicine_service.get_medicine) can't leak rows across clinics — see the
  test_conversion_scoped_to_other_clinic_not_visible test.
- BE: sell_unit optional-then-conditional-set in create_medicine — this is
  deliberately conditional (only assigned when truthy) so an unset field
  lets the DB/ORM-level default apply, rather than overriding it with an
  explicit falsy value — flagged for extra scrutiny since it differs from
  the unconditional-assign style used for sibling MedicineCreate fields.
- FE: UnitConversionsEditor is a self-contained widget (its own
  query/mutations) mounted inside the react-hook-form <form> — confirm no
  double-submit / stale-closure issues since it doesn't go through the
  medicine save mutation.
- FE: confirm the relabeling of base_unit ("Don vi ban" -> "Don vi ton kho")
  reads as a terminology clarification, not a functional change — the
  base_unit select's name/behavior is unchanged; only the i18n label + a raw
  string label changed.
