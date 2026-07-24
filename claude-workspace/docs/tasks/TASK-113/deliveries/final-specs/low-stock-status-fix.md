# TASK-113: Low-Stock Status Fix

**Status:** DONE  
**Severity:** Medium (M-15, E2E finding TASK-095)  
**Affected Systems:** Inventory, Pharmacy (Backend), Pharmacy (Frontend)  
**Repos:** clinic-cms, clinic-cms-web  

---

## Bug Summary

The Inventory list on the Frontend always displayed "Bình thường" (normal status) even for items below the low-stock threshold. The "Sắp hết" (low-stock) filter was always empty, despite the backend `/reports/inventory-status` endpoint correctly identifying low-stock items.

**Repro:**
1. Configure item with available qty 15, low-stock threshold 50
2. Fetch `/inventory/stock-status` → no `reorder_min` or `is_low_stock` fields (null)
3. FE list shows "Bình thường"; filter "Sắp hết" is empty
4. Fetch `/reports/inventory-status` → correctly shows `low_stock_count=1` (inconsistent)

---

## Root Cause

**Backend:** Endpoint `/inventory/stock-status` did not return `reorder_min` and `is_low_stock` fields. The view `v_inventory_status` lacked the computed columns.

**Key finding:** The bug report assumed the fix was to expose `inventory_item.reorder_min` column, but that column is **deprecated** (TASK-093 migration 0061 explicitly removed it from alert logic). The real threshold is resolved hierarchically:
- First: `medicine.low_stock_min`
- Second: `dosage_form.default_low_stock_min`
- Third: `clinic_settings.settings->'inventory'->>'low_stock_default_min'`

---

## Fix Design

**Add resolved threshold and low-stock indicator to stock-status view.**

The fix mirrors the existing precedent in `reports.InventoryStatusRow.reorder_min` (report schemas), which keeps the field name `reorder_min` for API/FE backward compatibility, but its value is the **resolved hierarchical threshold**, not the raw column.

New fields exposed via `GET /inventory/stock-status`:
- `reorder_min: Decimal | None` — hierarchically resolved low-stock threshold
- `is_low_stock: boolean` — `available_qty <= reorder_min` (or `false` if threshold unresolved)

By construction, both endpoints now agree on what "low-stock" means.

---

## Changes

### Backend (clinic-cms)

**Branch:** `fix/TASK-113-low-stock-status` (base `origin/dev`, alembic head 0068)  
**Commit:** `94cd233`

#### New Files

- `alembic/versions/0069_stock_status_view_low_stock_fields.py`
  - Recreates `v_inventory_status` to add `reorder_min` and `is_low_stock` computed columns
  - `reorder_min`: `COALESCE(m.low_stock_min, df.default_low_stock_min, (cs.settings->'inventory'->>'low_stock_default_min')::numeric)`
  - `is_low_stock`: `available_qty <= reorder_min` (or `false` if no threshold resolves)
  - Adds JOIN to `dosage_form` table (view already joined `clinic_settings`)
  - Downgrade restores prior (0061) view definition

#### Modified Files

- `app/modules/inventory/schemas/inventory_schemas.py`
  - `InventoryStatusResponse` gains:
    - `reorder_min: Decimal | None = None`
    - `is_low_stock: bool = False`
  - No endpoint change needed: `GET /inventory/stock-status` already does `SELECT * FROM v_inventory_status`

#### Tests Added

- `tests/integration/inventory/test_alert_threshold_e2e.py::TestStockStatusLowStockFields`:
  1. `test_stock_status_exposes_reorder_min_and_is_low_stock` — avail 15, threshold 50 → `is_low_stock=true`, `reorder_min=50`; asserts stock-status low-stock set == report's low-stock set
  2. `test_stock_status_no_threshold_configured_is_not_low_stock` — no threshold → `is_low_stock=false`, `reorder_min=null`

### Frontend (clinic-cms-web)

**Branch:** `fix/TASK-113-low-stock-status` (base `origin/dev`)  
**Commit:** `2bb6b48`

#### Modified Files

- `src/modules/pharmacy/types.ts`
  - `InventoryStatusItem` gains:
    - `reorder_min: number | null`
    - `is_low_stock: boolean`

- `src/pages/pharmacy/InventoryPage.tsx`
  - Updated both `getStockStatus()` call sites (status-filter predicate + row badge) to pass `reorderMin: item.reorder_min`
  - Helper already implemented correct `<=` semantics and precedence (expired > recalled > expiring_soon > low_stock > ok)

- `src/modules/reports/helpers.ts`
  - No change needed (already uses correct logic)

- `src/locales/{vi,en}/reports.json`
  - Added `visitVolume.awaitingPayment` and `inventory.lowStock` keys
  - Key `inventory.inProgress` already existed but was unused

#### Tests Added

- `src/tests/pharmacy/InventoryPage.test.tsx`
  - Updated mock fixtures with new `reorder_min`/`is_low_stock` fields
  - New AC test: "low_stock filter + badge use reorder_min/is_low_stock" with avail=15/reorder_min=50 item

---

## Testing

### Backend

**Environment:** Isolated Docker stack `fix113` (api 9963, postgres 5463, redis 6445)  
**Migration head:** 0069  
**Test results:** ✅ 45/45 passed

- Targeted tests: 7/7 (`TestStockStatusLowStockFields` x2 + `TestInventoryStatusReportResolvedThresholds` x5)
- Full `tests/integration/inventory/` — 45/45 passed
- `ruff check` on touched files → clean, no new errors (baseline: 31 pre-existing, confirmed unchanged)
- `mypy` on touched files → no new errors (baseline: 2 pre-existing `format_currency_vn` unrelated)

### Frontend

**Test results:** ✅ 66/66 passed (35 targeted + 66 full suite clean)

- `npx vitest run src/tests/pharmacy` — 35/35 passed (9 InventoryPage + 26 other pharmacy tests)
- `npx vitest run` (full frontend suite) — 1098/1103 passed; 5 pre-existing failures in unrelated files (confirmed on `origin/dev`)
- `tsc --noEmit` — clean, no errors
- `npm run lint` → 18 pre-existing problems in unrelated files (`VitalsPage`, `VssIntegration*`, `TemplateRenderer`); nothing in `pharmacy/` — no new breakage

---

## API Behavior

### GET /inventory/stock-status

**Response schema (new fields):**

```json
{
  "id": "...",
  "available_qty": 15,
  "reorder_min": 50,
  "is_low_stock": true,
  ...
}
```

For items with no threshold configured anywhere:
```json
{
  "id": "...",
  "available_qty": 100,
  "reorder_min": null,
  "is_low_stock": false,
  ...
}
```

---

## Acceptance Criteria Met

- [x] `/inventory/stock-status` returns `reorder_min` + `is_low_stock` fields
- [x] FE inventory list shows correct "Sắp hết" status based on these fields
- [x] "Sắp hết" filter works; matches report's low-stock set
- [x] Test: item below threshold → `is_low_stock=true`, appears in filter

---

## Data Consistency Guarantees

- **Endpoint alignment:** Both `/inventory/stock-status` and `/reports/inventory-status` use the same hierarchical resolution logic for low-stock thresholds (by construction — both read from the same view/helper functions).
- **Backward-compatible naming:** Field is called `reorder_min` (matches existing report schema) despite holding a resolved threshold, not a raw column.
- **Null safety:** Items with no threshold configured return `reorder_min=null`, `is_low_stock=false`.

---

## Deployment Notes

- Requires database migration `0069_stock_status_view_low_stock_fields.py`
- No breaking API changes (new fields are additive).
- Backend and frontend can be deployed independently (frontend gracefully handles missing fields via default values).
