# Handoff: TASK-113 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary
`/inventory/stock-status` now returns `reorder_min` + `is_low_stock` computed by the
exact resolver `/reports/inventory-status` uses (via migration `0069` recreating
`v_inventory_status`), so the FE "Sắp hết" badge + filter work and the two endpoints
agree by construction. BE + FE reviewed; no critical/major issues.

## Key Findings (MINOR, for awareness)
- View doesn't filter `m.is_deleted` (report does) — possible divergence only when a medicine is soft-deleted with an active item. Pre-existing.
- `helpers.ts:72` docstring priority order is stale vs the code (harmless).

## Focus Areas for Testing
- **AC / M-15 reproduction**: item avail 15 / low_stock_min 50 → list shows "Sắp hết", "Sắp hết" filter returns it, and matches `/reports/inventory-status` `low_stock_count`.
- **Threshold tiers**: verify resolution when only `dosage_form.default_low_stock_min` set, and when only `clinic_settings` default set (both endpoints must agree).
- **No-threshold**: no tier configured → `is_low_stock=false`, `reorder_min=null`, even at avail 0.
- **Cross-endpoint set equality** on realistic multi-item data.
- **Edge case to probe**: soft-deleted medicine with an active inventory_item (MINOR-1) — does stock-status show it while the report hides it?
- Migration up/down: apply `0069` then downgrade; confirm view returns to prior shape.
