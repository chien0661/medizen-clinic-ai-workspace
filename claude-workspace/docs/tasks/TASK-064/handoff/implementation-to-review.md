# Handoff: TASK-064 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-05-31
**Round**: 2 (fixes from CHANGES_REQUESTED)

## Summary

Fixed 2 issues flagged by review (1 CRITICAL, 1 MAJOR). All 13 integration tests now pass. No new type errors introduced in FE.

## Fix Round Summary

### Fix 1 — CRITICAL: StocktakePage.tsx raw fetch → api.post (FE)

Replaced the raw `fetch("/api/v1/inventory/stocktake", { headers: { "Content-Type" } })` call with `await api.post(...)` from `../../lib/apiClient`. The `api` client auto-attaches `Authorization: Bearer`, `X-Clinic-Id`, `X-Applied-Role` and handles 401 refresh. Updated `onError` to extract `.detail` from the thrown envelope (same pattern as `ExpiryProcessingPage.tsx` lines 241-247).

Commit: `905c3c0` on `feature/TASK-064-remove-inventory-mock`

### Fix 2 — MAJOR: Add integration test for reserved_quantity dispose guard (BE)

Added `test_dispose_batch_with_reservation_returns_400` to `TestBatchDispose` in `test_stocktake_dispose.py`. The test:
1. Seeds a batch with qty=40 via `_seed_inventory`
2. Directly sets `reserved_quantity = 5` via raw SQL to simulate an active reservation
3. POSTs to `/api/v1/inventory/batches/dispose` and asserts HTTP 400 + `BUSINESS_RULE_VIOLATION` error code
4. Queries the DB to confirm `is_deleted = false` and `actual_quantity = 40` (data integrity intact)

`BusinessRuleError` maps to HTTP 400 (confirmed in `app/core/exceptions.py:72`).

Commit: `40e613e` on `feature/TASK-064-inventory-stocktake-dispose`

## Repos and Branches

- **BE**: `clinic-cms-merge` branch `feature/TASK-064-inventory-stocktake-dispose` (commit `40e613e`)
- **FE**: `clinic-cms-web` branch `feature/TASK-064-remove-inventory-mock` (commit `905c3c0`)

## Files Changed

### BE (`clinic-cms-merge`)

- `app/modules/inventory/schemas/inventory_schemas.py`: Added 7 new Pydantic schemas (StocktakeItemResult, StocktakeSubmitRequest, StocktakeItemSnapshot, StocktakeSnapshotResponse, StocktakeAdjustmentResult, StocktakeSubmitResponse, BatchDisposeRequest, BatchDisposeResult, BatchDisposeResponse)
- `app/modules/inventory/services/stocktake_service.py` (NEW): `get_stocktake_snapshot()` + `submit_stocktake()` — aggregates expected qty from active batches, applies variance adjustments using FEFO order
- `app/modules/inventory/services/dispose_service.py` (NEW): `dispose_batches()` — zeroes qty, soft-deletes batch, creates expiry_writeoff movement; validates reserved_qty == 0
- `app/modules/inventory/api/routes.py`: Added 3 route handlers + added `near_expiry` query param to existing GET /inventory/batches
- `app/modules/inventory/services/batch_service.py`: Extended `list_batches()` to support `near_expiry=True` (return batches expiring within 90 days)
- `tests/integration/inventory/test_stocktake_dispose.py` (NEW): 12 integration tests (real DB, real app)

### FE (`clinic-cms-web`)

- `src/pages/pharmacy/StocktakePage.tsx`: Removed try/catch mock-success. Mutation now throws on non-OK response, extracts `detail` from FastAPI error envelope for the toast message
- `src/pages/pharmacy/ExpiryProcessingPage.tsx`: Removed try/catch mock-success. `onError` handler extracts `.detail` from API error object (apiClient throws raw parsed JSON, not Error instance)

## Test Results

- Integration tests: **13/13 passed** (12 original + 1 new reserved_quantity guard test)
- `ruff check` on new files: **All checks passed**
- FE type-check (`tsc --noEmit`): no errors in `StocktakePage.tsx`; pre-existing errors in Sidebar.tsx, admin/api.ts, LoginPage.tsx — not introduced by this task

## Design Decisions

1. **No new DB tables**: Stocktake is stateless (snapshot from existing batch data). Adjustments are stored as `stock_movement` records with `reference_type="stocktake"`. If auditable stocktake sessions are needed later, a separate `stocktake_session` table can be added in a future task.

2. **FEFO deduction for negative variance**: Shortage is deducted from earliest-expiry batches first. Surplus is added to the last (furthest-expiry) batch. This is the safest distribution that minimises waste risk.

3. **Dispose = soft-delete + expiry_writeoff movement**: Batch is soft-deleted (is_deleted=True) and actual_quantity zeroed. The stock_movement record is created before zeroing so `quantity_before` is the true write-off amount.

4. **`inventory.adjust` permission already seeded**: Confirmed in migration 0007 and 0017a — no new migration needed.

5. **FE error extraction**: `api.post` throws the raw parsed JSON `{ detail: "..." }` from FastAPI, not an Error instance. The `onError` handler checks for `.detail` property before falling back to `.message`.

## Areas for Review Focus

- FEFO variance distribution logic in `stocktake_service.py` (~lines 90-140) — especially edge cases with multiple batches and mixed variances
- The `dispose_batches()` loop: if one batch fails mid-list (e.g. has reservations), the transaction rolls back entirely (consistent). Confirm this is the desired behaviour vs partial success
- FE `StocktakePage.tsx`: now uses `api.post()` (fixed in Round 2) — auth headers attached correctly.
- `ExpiryProcessingPage.tsx` batches query still has mock fallback on GET (returns `generateMockBatches()` on error) — tracked as a follow-up, out of scope per review notes.

## Blockers / Notes

- No blockers
- No Alembic migration needed (no new tables)
- `inventory.adjust` permission exists in DB (verified in migration files)
