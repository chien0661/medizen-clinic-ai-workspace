# API Specification: Medicine usage_unit + default_dosage — TASK-131

**Project:** Clinic CMS
**Task:** TASK-131 — Đơn vị dùng + liều dùng mặc định trong Danh mục thuốc
**Date:** 2026-07-31
**Version:** 1.0
**Status:** Implemented (feature branch)

---

## Overview

Extends the existing Medicine catalog CRUD (`POST /medicines`,
`PATCH /medicines/{id}`) and the doctor medicine-search endpoint
(`GET /medicines/search`) with two new optional fields:

- `usage_unit` — string, ≤ 50 chars, nullable. Prescribing-unit hint.
- `default_dosage` — string, ≤ 200 chars, nullable. Suggested dosage text.

**Base Path:** `/api/v1`
**Authentication:** `Authorization: Bearer {token}` required on all endpoints.
**Scope:** Clinic-scoped (RLS on `medicine.clinic_id`), same as all existing
Medicine catalog operations.

No new permission was added. Existing gates apply unchanged:

- `medicine.manage` — create/update medicine (write).
- `medicine.read` — read medicine / medicine-search (read).

---

## 1. Create Medicine — `POST /medicines` (extended)

**Permission:** `medicine.manage`

### New fields in request body

```json
{
  "code": "ORS01",
  "name": "Oresol",
  "base_unit": "gói",
  "usage_unit": "gói",
  "default_dosage": "1 gói pha 200ml nước, uống sau tiêu chảy",
  "...": "existing fields (sell_unit, purchase_unit, pack_size, ...) unchanged"
}
```

| Field | Type | Required | Validation | Notes |
|---|---|---|---|---|
| `usage_unit` | string | No | ≤ 50 chars | Omit → `null` (no default derived from `base_unit`/`sell_unit`, unlike `sell_unit`'s TASK-124 default-to-`base_unit` behavior — `usage_unit` has no fallback at the DB layer, only at FE display time). |
| `default_dosage` | string | No | ≤ 200 chars | Omit → `null`. |

### Response — 201 Created (excerpt)

```json
{
  "id": "c1b2...",
  "code": "ORS01",
  "name": "Oresol",
  "base_unit": "gói",
  "sell_unit": "gói",
  "usage_unit": "gói",
  "default_dosage": "1 gói pha 200ml nước, uống sau tiêu chảy",
  "...": "..."
}
```

---

## 2. Update Medicine — `PATCH /medicines/{id}` (extended)

**Permission:** `medicine.manage`

### New fields in request body (partial update — only supplied fields change)

```json
{ "usage_unit": "viên" }
```

```json
{ "default_dosage": "1 viên x 2 lần/ngày" }
```

| Field | Type | Required | Validation | Notes |
|---|---|---|---|---|
| `usage_unit` | string | No | ≤ 50 chars if provided | Partial update — omitted fields are untouched (standard `exclude_unset` semantics, same as every other `MedicineUpdate` field). |
| `default_dosage` | string | No | ≤ 200 chars if provided | Same partial-update semantics. |

### Response — 200 OK

Full `MedicineResponse` (see §4) with the updated field(s) reflected.

---

## 3. Medicine Search (doctor prescribing) — `GET /medicines/search` (extended)

**Permission:** `medicine.read`

**Description:** The `MedicineSearchResult` items now carry `usage_unit` and
`default_dosage` alongside the existing `sell_unit`/`dosage_form_unit`, so the
doctor's prescribing screen can resolve the suggested unit/dosage without an
extra round-trip.

### Response — 200 OK (excerpt, one item)

```json
{
  "items": [
    {
      "id": "c1b2...",
      "code": "ORS01",
      "name": "Oresol",
      "base_unit": "gói",
      "sell_unit": "gói",
      "dosage_form_unit": null,
      "usage_unit": "gói",
      "default_dosage": "1 gói pha 200ml nước, uống sau tiêu chảy",
      "conversions": [],
      "is_in_house": true,
      "is_active": true,
      "in_stock": true,
      "available": "50",
      "stock_status": "ok"
    }
  ],
  "total": 1,
  "query": "oresol",
  "with_stock": true
}
```

| Field | Type | Description |
|---|---|---|
| `usage_unit` | string \| null | Prescribing-unit hint. `null` when not configured for this medicine. |
| `default_dosage` | string \| null | Suggested dosage string. `null` when not configured for this medicine. |

### FE consumption rule (PrescriptionTab.tsx `addMedicine`)

```
unit    = usage_unit || sell_unit || dosage_form_unit || base_unit
dosage  = default_dosage ?? ""   // still editable
```

---

## 4. `MedicineResponse` — full field reference (new fields highlighted)

| Field | Type | Notes |
|---|---|---|
| `usage_unit` | string \| null | **New (TASK-131).** As-stored value — no resolver/precedence logic (unlike `effective_low_stock_min`/`effective_near_expiry_days`, which layer medicine → dosage_form → clinic). |
| `default_dosage` | string \| null | **New (TASK-131).** As-stored value. |
| *(all other fields unchanged from TASK-124/TASK-093 — see prior API specs)* | | |

---

## 5. Error Handling

No new error codes. Standard validation errors apply:

| HTTP | Code | Reason |
|---|---|---|
| 400 | INVALID_REQUEST | `usage_unit` > 50 chars or `default_dosage` > 200 chars. |
| 401 | UNAUTHORIZED | Missing/invalid token. |
| 403 | FORBIDDEN | Token lacks `medicine.manage` (write) / `medicine.read` (read). |
| 404 | NOT_FOUND | Medicine does not exist or belongs to another clinic. |

---

## 6. Backward Compatibility

- Both columns are nullable, no default, no backfill — every pre-existing
  medicine has `usage_unit = NULL`, `default_dosage = NULL` after the
  migration, which resolves to the exact same FE behavior as before TASK-131
  (`sell_unit || dosage_form_unit || base_unit` and `dosage: ""`).
- Migration `0074_medicine_usage_unit_default_dosage.py`:
  `down_revision = "0073"`, single head confirmed via `alembic heads` → `0073
  (head)` before this migration was added, `0074 (head)` after. Purely
  additive `add_column`; `downgrade()` drops both columns cleanly.

---

## 7. Testing Notes

### 7.1 Backend (pytest via `docker-api:latest`, `docker run --rm`)

Command:

```bash
docker run --rm -v "<repo>:/app" -w /app docker-api:latest \
  python -m pytest tests/unit/inventory/test_medicine_service_effective.py \
                    tests/unit/prescriptions/test_schemas.py -q
```

Result: **35 passed** (includes 2 new test classes:
`TestToResponseUsageUnitDefaultDosage`, `TestMedicineCreateUpdateSchemas` in
`test_medicine_service_effective.py`, and
`TestMedicineSearchResultUsageUnitDefaultDosage` in `test_schemas.py`).

Broader regression check — `tests/unit/inventory`, `tests/unit/prescriptions`,
`tests/unit/test_medicine_stock_status.py`, `tests/unit/test_medicine_substitutes.py`,
`tests/unit/test_medicine_lots_endpoint.py`: **97 passed, 4 failed** — the 4
failures are **pre-existing** (in `test_medicine_stock_status.py`,
`MedicineSearchResult(...)` constructed without the already-required
`sell_unit` field — a TASK-124 gap unrelated to and not introduced by
TASK-131; confirmed by reproducing the same failure on `sell_unit` alone,
independent of the new `usage_unit`/`default_dosage` fields, both of which
are optional with a `None` default).

Full `tests/unit` suite: **1067 passed, 12 failed** — the 12 failures span
`test_email.py`, `test_erasure_service.py`, `test_feature_flags.py`, the 4
`test_medicine_stock_status.py` failures above, `test_rls_helpers.py`, and
`test_tenancy_middleware.py` — none touch the Medicine/prescription code
changed by this task.

**Not run:** DB-integration / e2e tests (e.g.
`tests/integration/prescriptions/test_task124_sell_unit_conversion_e2e.py`)
— these require a live Postgres instance. Per task instructions, no w2e-port
DB stack was started for TASK-131; these are marked **unverified** (reason:
no local DB stack permitted for this task). The migration is additive-only
(`add_column`, nullable, no backfill) so the risk of an untested DB-integration
regression is assessed as low, but a reviewer with DB access should confirm
`alembic upgrade head` applies cleanly on top of `0073`.

### 7.2 Frontend (vitest)

Command:

```bash
npx vitest run src/tests/admin/MedicinesPage.usageUnitDefaultDosage.test.tsx \
                src/tests/doctor/PrescriptionTab-usage-unit-default-dosage.test.tsx
```

Result: **11 passed** (4 in `MedicinesPage.usageUnitDefaultDosage.test.tsx`:
edit-form prefill, create payload with both fields, create payload omitting
both fields, update payload; 7 in
`PrescriptionTab-usage-unit-default-dosage.test.tsx`: unit precedence
usage_unit > sell_unit > dosage_form_unit > base_unit at each fallback level,
dosage prefill from `default_dosage`, dosage remains editable after prefill,
dosage stays blank when `default_dosage` is absent).

Regression check — existing `PrescriptionTab-sell-unit`, `-dosage-unit`,
`-usage-instruction`, `-stock`, and `MedicinesPage.price`, `.tags`,
`.unitConversions` test files: **28 passed, 0 failed**.

Full suite: **1167 passed, 4 failed** — pre-existing failures in
`ForgotPasswordPage.test.tsx`, `QueuePage.test.tsx` (×2), and
`AttendanceWidget.test.tsx` — none in the Medicine/prescription/doctor
prescribing modules touched by this task.

`npx tsc --noEmit`: **clean, no errors**.

---

**Version 1.0 — 2026-07-31**
**Status: Implemented — feature branch `feature/TASK-131`, pushed, not merged to dev**
