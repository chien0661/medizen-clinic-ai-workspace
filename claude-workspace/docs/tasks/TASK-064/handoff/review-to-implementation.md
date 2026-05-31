# Handoff: TASK-064 → Code Implementation Agent

**From**: Code Review Agent
**To**: Code Implementation Agent
**Status**: IN_PROGRESS
**Decision**: CHANGES_REQUESTED

## Summary

BE is approval-ready (12/12 integration tests pass, permission/RLS/audit all correct). Blocked by one CRITICAL FE bug (stocktake submit bypasses the authenticated API client → will 401 in production) and one MAJOR test gap (the reserved-quantity dispose guard is untested).

## Required Changes

### CRITICAL — must fix
1. **`clinic-cms-web/src/pages/pharmacy/StocktakePage.tsx`** (mutationFn, ~lines 129-147): the submit uses raw `fetch("/api/v1/inventory/stocktake", { headers: { "Content-Type": ... } })` with NO auth headers. The BE endpoint requires `inventory.adjust` + clinic RLS context, so this 401s in prod and the feature is non-functional.
   - Replace with: `import { api } from "../../lib/apiClient";` then `await api.post("/api/v1/inventory/stocktake", { items: payload });`
   - `api` auto-attaches `Authorization: Bearer`, `X-Clinic-Id`, `X-Applied-Role` and handles 401 refresh.
   - Update `onError` to extract `.detail` from the thrown envelope (the `api` client throws the raw parsed `{ detail }` object, NOT an `Error`) — mirror the pattern already used in `ExpiryProcessingPage.tsx` onError (~lines 241-247).

### MAJOR — must fix
2. **`clinic-cms-merge/tests/integration/inventory/test_stocktake_dispose.py`**: add a test for the `reserved_quantity > 0` dispose-rejection guard in `dispose_service.py:58-61`. Create a batch with `reserved_quantity > 0`, attempt dispose, assert it is rejected (BusinessRuleError → expect the mapped HTTP status, likely 409/400) and that the batch is NOT soft-deleted.

## Optional (MINOR — your call, not blocking)
- The FE diff carries an out-of-scope Tailwind palette refactor (gray→slate, indigo→brand, red→rose). If not part of a sanctioned project-wide migration, consider splitting it out. Low risk, can stay.
- `ExpiryProcessingPage` GET batches still falls back to `generateMockBatches()` on error — track as a follow-up (out of scope here).
- `submit_stocktake` silently drops surplus when an item has zero active batches (variance>0, no batch to add to). Consider documenting or surfacing this.

## Re-submit
After fixes: re-run `pytest tests/integration/inventory/test_stocktake_dispose.py -q` (should now include the reserved-qty test) and FE `tsc --noEmit` (confirm no new errors), then set status back to IN_REVIEW.
