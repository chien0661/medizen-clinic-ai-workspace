# Functional Design: Đơn vị dùng + Liều dùng mặc định — TASK-131

**Project:** Clinic CMS
**Task:** TASK-131 — Danh mục thuốc: cấu hình đơn vị dùng + liều dùng mặc định / mỗi thuốc
**Date:** 2026-07-31
**Version:** 1.0
**Status:** Implemented (feature branch, awaiting review/merge)

---

## 1. Overview

TASK-131 extends the Medicine catalog (built on TASK-124's multi-unit foundation)
with two purely optional, per-medicine prescribing-convenience fields:

- **`usage_unit`** (Đơn vị dùng) — a unit hint used specifically when
  prescribing, distinct from `sell_unit` (đơn vị bán, TASK-124) and
  `purchase_unit` (đơn vị nhập). Example: a medicine sold in "hộp" (box) but
  prescribed/counted in "gói" (sachet) per dose.
- **`default_dosage`** (Liều dùng mặc định) — a free-text suggested dosage
  string (e.g. "1 viên x 2 lần/ngày") used to auto-fill the "Liều dùng" field
  on the doctor's prescribing screen when the medicine is selected. The field
  remains editable — it is a convenience prefill, not a constraint.

Both fields are nullable with no default and no backfill: existing medicines
and existing prescribing/dispensing/invoicing/print flows (TASK-124, TASK-129)
are unaffected until a clinic explicitly configures either field.

## 2. Data Model

### 2.1 `medicine` table (additive columns)

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `usage_unit` | `VARCHAR(50)` | Yes | `NULL` | Prescribing-unit hint. |
| `default_dosage` | `VARCHAR(200)` | Yes | `NULL` | Suggested dosage string. |

Migration: `alembic/versions/0074_medicine_usage_unit_default_dosage.py`
(`down_revision = "0073"`, confirmed single head at the time of writing).
Purely additive `add_column` — no backfill, no `NOT NULL`, no data migration.
`downgrade()` drops both columns.

### 2.2 Precedence rule (prescribing unit)

When the doctor adds a medicine to a prescription, the suggested `unit` is
resolved with the following precedence (first non-empty wins):

```
usage_unit  >  sell_unit  >  dosage_form_unit  >  base_unit
```

- `usage_unit` (TASK-131, this task) — new, highest priority when configured.
- `sell_unit` (TASK-124) — the configured sale/dispense unit.
- `dosage_form_unit` (TASK-094 E) — resolved default unit for the medicine's
  linked `DosageForm` catalog entry.
- `base_unit` — the stock/threshold unit, always present as the final
  fallback.

### 2.3 Dosage prefill rule

When the doctor adds a medicine to a **new** prescription line, the `dosage`
field is prefilled with `medicine.default_dosage ?? ""` — still fully
editable. This only applies to `addMedicine` (adding a fresh line). It does
**not** apply when hydrating an existing/saved prescription on (re)mount —
that path always uses the persisted `PrescriptionItem.dosage` snapshot, never
`Medicine.default_dosage`, so editing a previously-saved prescription is
unaffected.

## 3. Backend Changes

| File | Change |
|---|---|
| `app/modules/inventory/models/medicine.py` | Added `usage_unit: str \| None` (String(50)) and `default_dosage: str \| None` (String(200)) columns. |
| `alembic/versions/0074_medicine_usage_unit_default_dosage.py` | New migration, additive, `down_revision="0073"`. |
| `app/modules/inventory/schemas/medicine_schemas.py` | Added `usage_unit`/`default_dosage` to `MedicineCreate`, `MedicineUpdate`, `MedicineResponse`. |
| `app/modules/inventory/services/medicine_service.py` | `create_medicine` now threads `usage_unit`/`default_dosage` from `MedicineCreate` into the new `Medicine` row. `_to_response` now includes both fields (as-stored, no resolver logic — unlike the TASK-093 alert-threshold fields). `update_medicine` needed no change: it already applies `MedicineUpdate.model_dump(exclude_unset=True)` generically via `setattr`. |
| `app/modules/prescriptions/schemas/prescription_schemas.py` | Added `usage_unit: str \| None = None` and `default_dosage: str \| None = None` to `MedicineSearchResult`. |
| `app/modules/prescriptions/services/medicine_search_service.py` | The single `MedicineSearchResult(...)` construction site now passes `usage_unit=m.usage_unit, default_dosage=m.default_dosage`. |

No new permission was introduced — both fields are gated by the existing
`medicine.manage` (write) / `medicine.read` (read, via medicine-search) checks
already in place for the Medicine catalog and doctor medicine-search.

## 4. Frontend Changes

| File | Change |
|---|---|
| `src/modules/admin/types.ts` | Added `usage_unit?: string \| null` / `default_dosage?: string \| null` to `Medicine`, `MedicineCreate`, `MedicineUpdate`. |
| `src/modules/doctor/types.ts` | Added the same two optional fields to the doctor-side `Medicine` type (medicine-search result shape). |
| `src/pages/admin/MedicinesPage.tsx` | Added `usage_unit` (dropdown, reusing the `SALE_UNITS` list + `unitOptions()` helper, same pattern as `sell_unit`) and `default_dosage` (free-text input) to the create/edit form's zod schema, `defaultValues`, and both create/update request bodies. Not added as a table column — the table is already dense (12 columns); the form is the primary configuration surface, consistent with how `sell_unit` itself is also form-only. |
| `src/components/doctor/PrescriptionTab.tsx` | `addMedicine()` now sets `unit: med.usage_unit \|\| med.sell_unit \|\| med.dosage_form_unit \|\| med.base_unit` (was `sell_unit \|\| dosage_form_unit \|\| base_unit`) and `dosage: med.default_dosage ?? ""` (was always `""`). The saved-prescription hydration `useEffect` is untouched — it maps from `it.dosage`/`it.unit` on the persisted `PrescriptionItemResponse`, never from `Medicine`. |
| `src/locales/vi/admin.json`, `src/locales/en/admin.json` | Added `medicines.form.usageUnit`, `usageUnitHint`, `defaultDosage`, `defaultDosagePlaceholder`, `defaultDosageHint` keys in both locales. |

## 5. Non-Regression

- **TASK-124 (sell_unit / unit conversions):** untouched precedence chain —
  `usage_unit` is inserted strictly *before* `sell_unit` in the fallback
  chain; when `usage_unit` is unset (the default for every pre-existing
  medicine), behavior is byte-for-byte identical to pre-TASK-131.
- **TASK-129 (Rx print / cách dùng inline):** print templates read
  `PrescriptionItem.dosage`/`.unit` (persisted snapshots), not
  `Medicine.usage_unit`/`.default_dosage` — no code path there was touched.
- **CSV import (`MedicineCsvImportModal`):** its `rowsToMedicines()` mapper
  was not changed; imported rows simply omit `usage_unit`/`default_dosage`
  (both optional on `MedicineCreate`), so import behavior is unchanged.
- **Medicine catalog CRUD:** `update_medicine`'s generic
  `model_dump(exclude_unset=True)` + `setattr` loop means partial updates
  (e.g. edit only `sale_price`) never accidentally clear `usage_unit`/
  `default_dosage` — they're simply absent from the diff.

## 6. Testing Summary

See `docs/tasks/TASK-131/deliveries/api-specs/medicine-usage-unit-api.md` §7
for the full test command + pass/fail breakdown. Highlights:

- BE: 35 new/updated unit tests (schema pass-through, `_to_response` mapping,
  `MedicineSearchResult` construction) — all pass under `docker-api:latest`.
  Full `tests/unit` suite: 1067 passed / 12 pre-existing failures, none in the
  medicine/prescription modules and none related to this change.
- FE: 11 new vitest tests (MedicinesPage form + PrescriptionTab
  `addMedicine`) — all pass. Full suite: 1167 passed / 4 pre-existing
  failures (auth, doctor queue timing, HR attendance) — unrelated to this
  change. `npx tsc --noEmit` clean.
- DB-integration (real migration apply + end-to-end prescribe flow against a
  live Postgres): **not run** — per task instructions, no w2e-port DB stack
  was started for this task. The migration itself is a plain additive
  `add_column` (no data movement, no constraint change), matching the pattern
  of prior additive migrations (e.g. 0070's `sell_unit` add before backfill).
