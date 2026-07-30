# Handoff: TASK-131 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW

## Summary

Added per-medicine `usage_unit` (đơn vị dùng) + `default_dosage` (liều dùng
mặc định) config to the Medicine catalog (BE model/migration/schemas/service +
FE admin form), and wired them into the doctor prescribing screen: new-item
unit precedence now tries `usage_unit` before `sell_unit`/`dosage_form_unit`/
`base_unit`, and the dosage field prefills from `default_dosage` (still
editable). Purely additive/nullable — no behavior change for existing
medicines or existing prescribing/print/CSV-import flows.

## Files Changed

**Backend** (`F:/MyProject/clinic-cms-workspace/_feat131-be`, branch `feature/TASK-131`):
- `app/modules/inventory/models/medicine.py` — new nullable columns `usage_unit` (String(50)), `default_dosage` (String(200)).
- `alembic/versions/0074_medicine_usage_unit_default_dosage.py` — new migration, `down_revision="0073"`, additive `add_column` only.
- `app/modules/inventory/schemas/medicine_schemas.py` — added both fields to `MedicineCreate`/`MedicineUpdate`/`MedicineResponse`.
- `app/modules/inventory/services/medicine_service.py` — `create_medicine` threads the 2 new fields; `_to_response` returns them as-stored (no resolver logic, unlike TASK-093 alert thresholds). `update_medicine` needed no change (generic `exclude_unset` + `setattr`).
- `app/modules/prescriptions/schemas/prescription_schemas.py` — added `usage_unit`/`default_dosage` to `MedicineSearchResult`.
- `app/modules/prescriptions/services/medicine_search_service.py` — the one `MedicineSearchResult(...)` construction site now passes both fields from the `Medicine` row.
- Tests: `tests/unit/inventory/test_medicine_service_effective.py` (updated `_fake_medicine` defaults + 2 new test classes), `tests/unit/prescriptions/test_schemas.py` (1 new test class).

**Frontend** (`F:/MyProject/clinic-cms-workspace/_feat131-web`, branch `feature/TASK-131`):
- `src/modules/admin/types.ts` — `usage_unit`/`default_dosage` on `Medicine`, `MedicineCreate`, `MedicineUpdate`.
- `src/modules/doctor/types.ts` — same 2 fields on the doctor-side `Medicine` (medicine-search result) type.
- `src/pages/admin/MedicinesPage.tsx` — zod schema, `defaultValues`, create/update request bodies, and 2 new form fields ("Đơn vị dùng" dropdown reusing `SALE_UNITS`/`unitOptions()`; "Liều dùng mặc định" free-text input). No new table column (see decision note below).
- `src/components/doctor/PrescriptionTab.tsx` — `addMedicine()`: `unit: med.usage_unit || med.sell_unit || med.dosage_form_unit || med.base_unit` (was missing `usage_unit`); `dosage: med.default_dosage ?? ""` (was always `""`). Saved-prescription hydration path untouched (uses persisted `PrescriptionItem.dosage`/`.unit`, not `Medicine.*`).
- `src/locales/vi/admin.json`, `src/locales/en/admin.json` — new i18n keys (`usageUnit`, `usageUnitHint`, `defaultDosage`, `defaultDosagePlaceholder`, `defaultDosageHint`).
- New test files: `src/tests/admin/MedicinesPage.usageUnitDefaultDosage.test.tsx` (4 tests), `src/tests/doctor/PrescriptionTab-usage-unit-default-dosage.test.tsx` (7 tests).

## Decision Note

MedicinesPage table was **not** given new columns for `usage_unit`/
`default_dosage` — the table already has 12 columns, and `sell_unit` (its
closest analog, TASK-124) is also form-only, not shown in the table. Kept
consistent with that precedent.

## Test Results

**Backend** (run via `docker run --rm ... docker-api:latest python -m pytest`, host Python 3.10 is incompatible — see `PROJECT.md`/memory):
- Targeted new/updated tests: **35/35 passed**.
- Broader regression pass (`tests/unit/inventory`, `tests/unit/prescriptions`, medicine-related unit test files): **97 passed, 4 failed** — the 4 are **pre-existing**, in `test_medicine_stock_status.py`, unrelated to this task (that file constructs `MedicineSearchResult` without the already-required `sell_unit` field, a TASK-124 gap that predates TASK-131; `usage_unit`/`default_dosage` are optional with `None` defaults and did not cause any new failure).
- Full `tests/unit` suite: **1067 passed, 12 failed** — same 4 above plus 8 unrelated pre-existing failures (`test_email.py`, `test_erasure_service.py`, `test_feature_flags.py`, `test_rls_helpers.py`, `test_tenancy_middleware.py`). None touch Medicine/prescription code.
- **Not run**: DB-integration/e2e tests (e.g. `test_task124_sell_unit_conversion_e2e.py`) — per task instructions, no w2e-port DB stack was started. Migration is additive-only (`add_column`, nullable, no backfill); risk assessed as low but flagging for reviewer/tester with DB access to confirm `alembic upgrade head` applies cleanly.

**Frontend** (vitest):
- New tests: **11/11 passed**.
- Regression check (existing sell-unit/dosage-unit/usage-instruction/stock/price/tags/unitConversions test files): **28/28 passed**.
- Full suite: **1167 passed, 4 failed** — pre-existing, unrelated (`ForgotPasswordPage`, `QueuePage` ×2, `AttendanceWidget`).
- `npx tsc --noEmit`: **clean**.

## Migration

`0074_medicine_usage_unit_default_dosage.py`, `down_revision="0073"`.
Confirmed single head via `alembic heads` → `0073 (head)` before this
migration was authored; `0074` is the only new leaf. Purely additive
(`add_column`, both nullable, no backfill, no NOT NULL, no data migration).

## Scope Confirmation

- No changes to `main` branch or the w2e stack (ports 9999/5434/5436/6380/6382).
- Both worktrees (`_feat131-be`, `_feat131-web`) on `feature/TASK-131`,
  committed and pushed to `origin/feature/TASK-131`. **Not merged to dev** —
  per instructions, merge is manager-coordinated.

## Areas for Review Focus

- Confirm the unit-precedence change (`usage_unit` inserted ahead of
  `sell_unit`) reads correctly against the TASK-124 sell_unit/conversion
  design intent.
- Confirm the pre-existing `test_medicine_stock_status.py` failures (missing
  `sell_unit`) are indeed out of scope for this task (not introduced by it) —
  may be worth a follow-up ticket to fix that file's fixtures.
- DB-integration/e2e coverage for the new migration + medicine-search
  passthrough was not exercised against a live Postgres in this pass — flagged
  above for whoever has stack access.
