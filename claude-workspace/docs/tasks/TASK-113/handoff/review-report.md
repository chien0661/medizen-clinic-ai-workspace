# TASK-113 — Code Review Report

**From**: Code Review Agent
**Date**: 2026-07-25
**Branches**: `fix/TASK-113-low-stock-status` (BE `_fix113-be`, FE `_fix113-web`)
**Diff base**: `origin/dev` → HEAD (`git diff origin/dev...HEAD --unified=3`)

## Decision: APPROVED → IN_TESTING

The fix correctly resolves M-15: `GET /inventory/stock-status` now exposes
`reorder_min` (resolved threshold) + `is_low_stock`, computed by the **exact same
resolver** that `/reports/inventory-status` uses, so the two endpoints agree by
construction — which is the whole point of the task.

---

## Resolver-matches-reports verdict: MATCH (by construction)

- **Threshold**: the view's inline COALESCE in migration `0069` is character-for-character
  the same tier hierarchy as `alert_threshold_service.LOW_STOCK_MIN_SQL`
  (used verbatim by `inventory_report_service.py:57`):
  `COALESCE(m.low_stock_min, df.default_low_stock_min, (cs.settings->'inventory'->>'low_stock_default_min')::numeric)`.
  Requires `LEFT JOIN dosage_form df` — correctly added (clinic_settings was already joined).
- **`is_low_stock` semantics**: view = `COALESCE(available_qty <= <threshold>, false)`;
  report service = `low_stock_min is not None and available_qty <= low_stock_min`.
  Both yield `false` when no tier resolves, and `available_qty <= threshold` otherwise. Equivalent.
- **`available_qty`**: view filters recalled/expired/deleted batches in the JOIN;
  report filters them in the SUM `FILTER`. Net result identical (non-deleted,
  non-recalled, non-expired `actual - reserved`).
- **Test** genuinely asserts the equality, not just per-row values:
  `low_stock_ids_from_status == low_stock_ids_from_report` **and**
  `report["low_stock_count"] == len(low_stock_ids)`.

## Migration 0069 head: OK
- Single head: only `0069` sets `down_revision = "0068"`; `0068 → 0067`. Linear, single head.
- `upgrade()` DROP + CREATE view (additive columns); `downgrade()` restores the exact prior
  (0061) view definition. View recreation is safe — no data migration, `GRANT SELECT ON ... TO cms_app` preserved.
- Python syntax compiles (`py_compile` OK).

## Schema / route / FE
- `InventoryStatusResponse` gains `reorder_min: Decimal | None = None`, `is_low_stock: bool = False` — additive, backward-compatible.
- Route unchanged: `SELECT * FROM v_inventory_status WHERE clinic_id = :clinic_id`, unpacked into schema; clinic-scoped. Correct.
- FE: `reorder_min`/`is_low_stock` added to `InventoryStatusItem`; `InventoryPage.tsx` passes `reorderMin` at **both** `getStockStatus` sites (filter predicate + row badge). Helper already had correct `<=` semantics + null-threshold guard — no helper change, correct.

## Checks run
- **FE `tsc --noEmit`: 0 errors** (verified by reviewer).
- FE lint / vitest 35/35 and BE 45/45: per implementation handoff (in-container).
- **BE host ruff/mypy broken** (`WinError 193` — ruff shim not a valid Win32 binary), confirming the handoff note; the implementer ran them inside the Docker `fix113` stack (reported 0 new vs baseline). BE migration + schema Python syntax verified OK by reviewer.

## Findings by severity
- **CRITICAL**: none.
- **MAJOR**: none.
- **MINOR (all pre-existing, not introduced by this diff; noted for awareness)**:
  1. View `JOIN medicine m` does not filter `m.is_deleted`, whereas the report's WHERE has
     `m.is_deleted = FALSE`. A soft-deleted medicine with a still-active `inventory_item` could
     make the two endpoints disagree on the low-stock set. Pre-existing view behavior; out of scope. Flag to Test Agent as an edge case worth probing.
  2. `helpers.ts:72` docstring lists a stale priority order that doesn't match the code
     (code = recalled > expired > expiring_soon > low_stock > ok). Pre-existing; not in this diff.
  3. View uses `CURRENT_DATE` (DB) while report uses `date.today()` (app param). Effectively equal; cosmetic.
- **Naming (confirmed intentional)**: `reorder_min` = *resolved* threshold, mirroring
  `reports.InventoryStatusRow.reorder_min` — deliberately consistent, not the deprecated
  `inventory_item.reorder_min` column (see 0061). Correct call; no rename needed.
