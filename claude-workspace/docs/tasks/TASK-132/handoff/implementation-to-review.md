# Handoff: TASK-132 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW

## Summary

Implemented a **per-clinic configuration table `unit`** (admin CRUD, not a hard-coded enum) that replaces the previously hard-coded medicine-unit dropdown list, plus a reusable **creatable combobox** (`CreatableCombobox`) wired into all 4 unit fields of the medicine form. 11 defaults (viên/vỉ/gói/ống/chai/lọ/tuýp/ml/gam/miếng/cái) are seeded per clinic via migration `0075` (existing clinics) and a new-clinic-creation hook (future clinics). Mirrors the TASK-125 `service_type` pattern exactly.

**Important design note:** `medicine.base_unit`/`sell_unit`/`purchase_unit`/`usage_unit` remain free-text `String` columns — **no FK** was added from `medicine` to `unit`. The catalog is a suggestion/quick-create source for the combobox and the admin page only; it does not constrain what a medicine's unit fields can contain. This was a deliberate choice to guarantee zero regression risk to historical medicine/prescription/invoice data (see functional design §1.1/§3/BR-006).

Both worktrees are on `feature/TASK-132`, committed, and pushed. **Not merged to dev/main** — per instructions, that's the manager's call.

## Existing-concept check (required by task brief)

Searched the BE for any existing unit-catalog concept before building (TASK-050 seed mentions "units"):
- `app/modules/inventory/services/unit_service.py` — a **resolver**, not a catalog: converts quantities between a medicine's units using `Medicine.unit_conversions`. No table of valid unit codes.
- `app/modules/inventory/models/unit_conversion.py` (`UnitConversion`) — per-medicine `(from_unit, to_unit, factor)` rows; `from_unit`/`to_unit` are free-text strings, not FK'd to anything.
- `DosageForm.unit` — a single string column (default unit hint per dosage form), not a catalog.
- `medicine.base_unit/sell_unit/purchase_unit/usage_unit` — free-text strings, previously backed only by a hard-coded FE dropdown list.

**Conclusion:** no unit-catalog table existed. Built new (`unit` table), did not touch/extend `unit_conversion` (different purpose entirely — conversion factors, not a code catalog).

## Files Changed

### Backend (`_feat132-be`, branch `feature/TASK-132`)

**New:**
- `app/modules/inventory/models/unit.py` — `Unit(BaseEntity)` model. `clinic_id` stays NOT NULL (per-clinic, like `ServiceType`; unlike the global `DosageForm`).
- `app/modules/inventory/schemas/unit_catalog_schemas.py` — `UnitCreate/Update/Response/ListResponse/QuickCreate`. Named `unit_catalog_schemas` (not `unit_schemas`) to avoid clashing with the existing `unit_conversion_schemas.py`.
- `app/modules/inventory/services/unit_catalog_service.py` — CRUD + `seed_defaults_for_clinic()` (idempotent, `DEFAULT_UNITS` constant — must stay in sync with the migration's `_DEFAULTS`) + `get_or_create_unit_by_name()` (idempotent get-or-create by display name, derives a code via NFKD-normalize + slugify + de-dup suffix, mirrors `tag_service.attach_tag`'s idempotency pattern). Named `unit_catalog_service` to avoid clashing with the existing `unit_service.py` (conversion resolver).
- `alembic/versions/0075_unit_catalog.py` — **down_revision="0074"** (verified `alembic heads` resolves to single head `0075`, run inside `docker-api:latest`). Creates `unit` table + seeds 11 defaults per existing clinic (loop over `SELECT id FROM clinic`, deterministic `uuid5` ids) **before** enabling RLS (mirrors migration `0070`'s ordering, safe as non-superuser) + RLS (`apply_rls_with_tenant_isolation`) + grant.
- `tests/unit/services/test_unit_catalog_service.py` — 10 new mock-based unit tests (CRUD, is_system 403, seed idempotency, get-or-create).
- `tests/integration/inventory/test_task132_unit_catalog_e2e.py` — 6 new integration tests (real DB, direct service-layer calls, mirrors `test_task125_service_type_e2e.py`). **Not executed** — see Test Results.

**Modified:**
- `app/modules/inventory/api/routes.py` — new `/units` CRUD routes + `/units/quick-create` (reuse `inventory.read`/`inventory.manage_catalog`, **no new permission**).
- `app/modules/admin/services/clinic_service.py` — `create_clinic` now also calls `unit_catalog_service.seed_defaults_for_clinic()` (alongside the existing `service_type_service` seed call) so clinics created after migration `0075` get the same 11 defaults.

### Frontend (`_feat132-web`, branch `feature/TASK-132`)

**New:**
- `src/components/ui/creatable-combobox.tsx` — `CreatableCombobox`, a reusable single-select combobox (not unit-specific). Options list + free-text input; typing a value not in the list shows "Tạo '&lt;x&gt;'" which calls `onCreate` then selects the result. Every keystroke still fires `onChange` directly (so unconfirmed free text is preserved exactly like the `<select>` it replaces — no regression to existing saves). Uses a `useRef` guard (not just React state) against a rapid double-confirm firing `onCreate` twice in the same tick.
- `src/pages/admin/UnitsPage.tsx` — `/admin/units` config screen, mirrors `ServiceTypesPage.tsx` (TASK-125): system rows (11 seeded defaults) hide edit/delete.
- `src/tests/admin/UnitsPage.test.tsx` — 12 tests (i18n parity + render), mirrors `ServiceTypesPage.test.tsx`.
- `src/tests/components/CreatableCombobox.test.tsx` — 8 tests (option filtering, select, create-new flow, exact-match suppression, free-text passthrough, double-confirm guard).

**Modified:**
- `src/modules/admin/types.ts` — `Unit`/`UnitCreate`/`UnitUpdate`/`UnitQuickCreate`.
- `src/modules/admin/api.ts` — `adminUnitsApi` (list/create/update/delete/quickCreate; defensively unwraps both `{items}` and bare-array responses, same convention as `adminServiceTypesApi`).
- `src/pages/admin/MedicinesPage.tsx` — `base_unit`, `purchase_unit`, `sell_unit`, `usage_unit` fields switched from `<select>` to `CreatableCombobox` via react-hook-form `Controller` (added `control` to the `useForm` destructure). Removed the now-unused `SALE_UNITS`/`PURCHASE_UNITS` hard-coded arrays and the `unitOptions()` helper. A shared `["admin","units"]` query feeds options to all 4 fields; creating a unit in any one field invalidates the cache so the others see it immediately.
- `src/router/index.tsx`, `src/components/shell/Sidebar.tsx` — new route `/admin/units` + nav entry (`Tags` icon, `inventory.manage_catalog` permission).
- `src/locales/{vi,en}/admin.json` — `nav.units`, `units.*` block (mirrors `serviceTypes.*` exactly).
- `src/tests/admin/MedicinesPage.usageUnitDefaultDosage.test.tsx`, `src/tests/admin/MedicinesPage.price.test.tsx` — updated DOM queries from `select[name="..."]` to `input[name="..."]` (the combobox renders a plain `<input>`, not a `<select>`; `name` is forwarded from `field.name` for exactly this kind of test compatibility).

## Test Results

**Backend** (run inside the project's own `docker-api:latest` image via `docker run --rm -v ... `, no ports exposed):
- `alembic heads` → single head `0075`.
- `python -m pytest tests/unit/services/test_unit_catalog_service.py -q` → **10 passed**.
- `python -m pytest tests/unit -q` (full suite) → **1077 passed, 12 failed** — all 12 failures are **pre-existing and unrelated** (email templates, erasure_service, feature_flags, medicine_stock_status, `test_rls_helpers.py` expecting 3 `execute()` calls but the current `apply_rls_with_tenant_isolation` issues 4 — a stale assertion predating this task, tenancy_middleware). Verified none of the failing test files were touched by this change.
- `ruff check` on every new/changed file → clean (routes.py shows pre-existing B008 warnings at unrelated lines far from this task's additions, not introduced here).
- `python -c "from app.modules.inventory.api import routes; ..."` → imports clean.
- Integration test (`tests/integration/inventory/test_task132_unit_catalog_e2e.py`) → written, **not executed** — no non-w2e DB stack was available and the w2e stack (ports 9999/5434/5436/6380/6382) must not be started per instructions.

**Frontend** (ran via a Windows junction `node_modules -> ../clinic-cms-web/node_modules`, confirmed identical `package-lock.json` at the branch point — no new deps added):
- `npx tsc --noEmit` → clean.
- `npx vitest run` on `CreatableCombobox.test.tsx` (8), `UnitsPage.test.tsx` (12), `admin.test.tsx` (42, i18n parity) → all pass.
- Updated `MedicinesPage.usageUnitDefaultDosage.test.tsx` (4) + `MedicinesPage.price.test.tsx` (5) + `MedicinesPage.unitConversions.test.tsx` (4) → all pass **when run with `--no-file-parallelism`**; running all 3 files with default parallelism intermittently failed on `waitFor` timeouts in this resource-constrained sandbox (confirmed as a parallel-worker contention flake, not a real regression, by re-running each file alone — all pass — and sequentially — all 13 pass).
- Full `src/tests/admin src/tests/components src/tests/doctor` suite (`--no-file-parallelism`) → **287 passed, 2 failed**, both in `src/tests/doctor/QueuePage.test.tsx` (a date-fixture mismatch, confirmed pre-existing/unrelated — file not touched by this task, reproduces in isolation too).

## Design Decisions Worth Reviewer Attention

1. **No FK from `medicine.*_unit` to `unit`** — intentional (see Summary). `unit` is purely a suggestion/quick-create source, so this task carries zero risk to historical data. Flagged explicitly in the functional design (BR-006) in case a reviewer expected a hard constraint.
2. **Permission choice**: `/units` reuses `inventory.read`/`inventory.manage_catalog` (not `dosage_form.read/manage`, which is admin-only) — chosen because `inventory.manage_catalog` is granted to both `admin` and `pharmacist`, matching who actually edits the medicine catalog and would need to create units on the fly. `dosage_form.manage` is admin-only and would have blocked pharmacists from the creatable-combobox flow.
3. **`/units/quick-create` is a separate endpoint from `POST /units`** — the combobox only has a display name (no code field in that UX), so quick-create derives + de-duplicates the code server-side and is idempotent by name (get-or-create, no 409 on a repeat call) — mirrors `tag_service.attach_tag`'s existing idempotent-create pattern in this codebase.
4. **System rows (`is_system=true`) are fully locked** — cannot be edited or deleted (403) — same as `ServiceType`/`DosageForm` convention.
5. **CreatableCombobox fires `onChange` on every keystroke**, not only on explicit create/select — this was a deliberate choice to guarantee the old `<select>`'s effective behavior (arbitrary free text always savable) is preserved even if the user never clicks "Tạo".
6. **Applied the combobox to all 4 unit fields** (base/purchase/sell/usage), not just `usage_unit` as the task's "at minimum" — assessed as low-risk since all 4 were structurally identical `<select>` elements bound to plain string fields.

## Areas for Review Focus

- `app/modules/inventory/services/unit_catalog_service.py::get_or_create_unit_by_name` — the code-derivation/slugify/de-dup logic; please double-check the NFKD-normalize approach handles the full range of Vietnamese diacritics you'd expect in real unit names.
- `alembic/versions/0075_unit_catalog.py` — per-clinic seed loop + `uuid5` determinism + seed-before-RLS ordering (mirrors `0070`); please confirm idempotency reasoning holds.
- `tests/integration/inventory/test_task132_unit_catalog_e2e.py` — written but unverified (no DB stack). Please run once a DB is available.
- `src/components/ui/creatable-combobox.tsx` — the `creatingRef` synchronous guard against double-create; and the deliberate choice to fire `onChange` on every keystroke (point 5 above) — confirm this matches the intended creatable-combobox UX rather than requiring an explicit confirm-to-persist-any-change model.
- The FE test flakiness note (parallel workers) — if CI has more headroom than this sandbox, the 3 MedicinesPage suites should be reliably green without `--no-file-parallelism`; worth a sanity check on a real CI runner.

## Confirmations

- No `main`/`dev` branch touched — worktrees are on `feature/TASK-132` off the latest `dev` (includes TASK-131), not merged.
- No Docker stack started on ports 9999/5434/5436/6380/6382 (w2e) — only ephemeral `docker run --rm docker-api:latest ...` calls were used (no port bindings, no compose).
- Both worktrees committed and pushed to `origin/feature/TASK-132`.
