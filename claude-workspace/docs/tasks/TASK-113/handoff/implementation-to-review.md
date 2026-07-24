# TASK-113 — Implementation → Review Handoff

**Bug (M-15, TASK-095 E2E):** `GET /inventory/stock-status` did not return `reorder_min`
/ `is_low_stock`, so the FE inventory list always showed "Bình thường" and the
"Sắp hết" (low-stock) filter was always empty — even though
`GET /reports/inventory-status` correctly computed `low_stock_count`.

## Root cause + key finding

The bug report assumed the fix was "expose `inventory_item.reorder_min`". That
column is **deprecated** — migration `0061_inventory_alert_thresholds.py`
(TASK-093) explicitly states it's "no longer read by any alert-generating code
path." The real threshold is resolved hierarchically by
`app/modules/inventory/services/alert_threshold_service.py`
(`medicine.low_stock_min -> dosage_form.default_low_stock_min ->
clinic_settings.settings->'inventory'->>'low_stock_default_min'`), and that's
exactly what `/reports/inventory-status` (`inventory_report_service.py`) uses
via its `LOW_STOCK_MIN_SQL` fragment.

Naming precedent already existed: `reports.InventoryStatusRow.reorder_min`
(`app/modules/reports/schemas/report_schemas.py:51`) keeps the field name
`reorder_min` for API/FE backward compatibility, but its *value* is the
resolved threshold, not the raw column. This fix mirrors that exactly so the
two endpoints agree by construction, not by coincidence.

## Backend changes (`clinic-cms`, branch `fix/TASK-113-low-stock-status`, commit `94cd233`)

1. **`alembic/versions/0069_stock_status_view_low_stock_fields.py`** (new) —
   recreates `v_inventory_status` to add:
   - `reorder_min` — `COALESCE(m.low_stock_min, df.default_low_stock_min, (cs.settings->'inventory'->>'low_stock_default_min')::numeric)`
   - `is_low_stock` — `available_qty <= reorder_min`, `false` when no tier resolves
   - Adds `LEFT JOIN dosage_form df ON df.id = m.dosage_form_id` (the view
     already joined `clinic_settings cs` for the near-expiry window).
   - `downgrade()` restores the prior (0061) view definition.
2. **`app/modules/inventory/schemas/inventory_schemas.py`** — `InventoryStatusResponse`
   gains `reorder_min: Decimal | None = None` and `is_low_stock: bool = False`.
   No route change needed — `GET /inventory/stock-status` already does
   `SELECT * FROM v_inventory_status` and unpacks into the schema.
3. **`tests/integration/inventory/test_alert_threshold_e2e.py`** — new
   `TestStockStatusLowStockFields` class:
   - `test_stock_status_exposes_reorder_min_and_is_low_stock` — avail 15 /
     `low_stock_min` 50 -> `is_low_stock=true`, `reorder_min=50`, and asserts
     the stock-status low-stock item set == the report's low-stock item set
     == `low_stock_count`.
   - `test_stock_status_no_threshold_configured_is_not_low_stock` — no
     threshold at any tier -> `is_low_stock=false`, `reorder_min=null`.

## Frontend changes (`clinic-cms-web`, branch `fix/TASK-113-low-stock-status`, commit `2bb6b48`)

1. **`src/modules/pharmacy/types.ts`** — `InventoryStatusItem` gains
   `reorder_min: number | null` and `is_low_stock: boolean`.
2. **`src/pages/pharmacy/InventoryPage.tsx`** — the two `getStockStatus(...)`
   call sites (status-filter predicate + row badge) now pass
   `reorderMin: item.reorder_min`. `getStockStatus` in
   `modules/pharmacy/helpers.ts` already implemented the correct `<=`
   semantics and precedence (expired > recalled > expiring_soon > low_stock >
   ok) — it just was never given the threshold. No helper changes needed.
3. **`src/tests/pharmacy/InventoryPage.test.tsx`** — added `reorder_min`/
   `is_low_stock` to existing mock fixtures, and a new AC test
   ("low_stock filter + badge use reorder_min/is_low_stock") with a
   avail=15/reorder_min=50 item verifying both the badge label and the
   "Sắp hết" filter narrow correctly.

## Test results

- **Backend** (isolated Docker stack `fix113`: api 9963 / postgres 5463 /
  redis 6445, migrated to head incl. 0069, torn down after):
  - Targeted: 7/7 passed (`TestStockStatusLowStockFields` x2 +
    `TestInventoryStatusReportResolvedThresholds` x5).
  - Full `tests/integration/inventory/`: **45/45 passed**.
  - `ruff check` on touched files: 31 pre-existing findings, confirmed
    identical against `origin/dev` baseline (diffed via `git show
    origin/dev:<path>` inside the container) — **0 new**.
  - `mypy` on touched files: 2 pre-existing errors (unrelated
    `format_currency_vn` typing issue at routes.py:268/689), confirmed
    identical against baseline — **0 new**.
- **Frontend**:
  - `npm ci` clean.
  - Targeted vitest (`InventoryPage.test.tsx` + `helpers.test.ts`): **35/35
    passed** (9 InventoryPage tests incl. the new AC test).
  - Full `vitest run`: 1098/1103 passed; 3 failing files
    (`ForgotPasswordPage.test.tsx`, `QueuePage.test.tsx`) are pre-existing
    failures unrelated to this change — reproduced on `origin/dev` before
    the fix was applied (confirmed via `git stash` + rerun).
  - `tsc --noEmit`: 0 errors.
  - `npm run lint`: 18 pre-existing problems, all in unrelated
    `admin/VitalsPage.tsx` / `admin/VssIntegrationConfigPage.tsx` /
    `admin/VssSyncLogPage.tsx` / `print/TemplateRenderer.tsx` — nothing under
    `pharmacy/` — **0 new**.

## For the reviewer

- Both worktrees left in place: `F:/MyProject/clinic-cms-workspace/_fix113-be`,
  `F:/MyProject/clinic-cms-workspace/_fix113-web`, both on
  `fix/TASK-113-low-stock-status`, both pushed.
- Please double-check the naming decision (`reorder_min` = resolved
  threshold, not raw column) against the AC wording — it's intentional and
  matches existing precedent in `reports/schemas/report_schemas.py`, but flag
  if you'd rather rename to `low_stock_min` for clarity (would be a
  FE+BE+migration rename, not just additive).
