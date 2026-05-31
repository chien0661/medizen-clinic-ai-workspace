# Code Review Report — TASK-064

**Reviewer**: Code Review Agent
**Date**: 2026-05-31
**Status**: IN_REVIEW → **CHANGES_REQUESTED**
**Decision**: CHANGES_REQUESTED

- **BE**: `clinic-cms-merge` @ `feature/TASK-064-inventory-stocktake-dispose` (826f5ce)
- **FE**: `clinic-cms-web` @ `feature/TASK-064-remove-inventory-mock` (9df90f7)
- SonarQube: DISABLED (no project key) — skipped per agent guide.

## Summary

BE implementation is high quality: 3 endpoints with correct `inventory.adjust` permission gates, clinic_id RLS (session GUC + explicit filters), append-only `stock_movement` audit records, FEFO variance distribution, and 12 passing real-DB integration tests. The FE `ExpiryProcessingPage` change is correct.

However, **`StocktakePage.tsx` submit uses a raw `fetch()` with no auth headers**, which will fail in production (401) — making the stocktake submit feature non-functional. This is the CRITICAL issue blocking approval, plus one MAJOR test gap.

## Checks Run

| Check | Result |
|-------|--------|
| BE integration tests (`pytest tests/integration/inventory/test_stocktake_dispose.py`) | **12/12 PASS** (17.9s, real DB in `clinic_cms_w2e_api`) |
| `ruff check` (per handoff) | PASS |
| FE `tsc --noEmit` | No new errors in TASK files; only pre-existing errors (Sidebar.tsx, admin/api.ts, LoginPage.tsx, i18n test) |

---

## CRITICAL Issues

### 1. StocktakePage submit bypasses the authenticated API client — feature non-functional in prod
**File**: `clinic-cms-web/src/pages/pharmacy/StocktakePage.tsx` (mutationFn, ~lines 129-147)

Found:
```ts
const res = await fetch("/api/v1/inventory/stocktake", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ items: payload }),
});
```

The BE endpoint `POST /inventory/stocktake` is gated by `require_permission("inventory.adjust")` and depends on RLS clinic context. The raw `fetch` does **not** attach any of the headers the project's `api` client adds automatically (`src/lib/apiClient.ts:84-95`):
- `Authorization: Bearer <access_token>` → **request will be 401 Unauthorized**
- `X-Clinic-Id` → RLS tenant context missing
- `X-Applied-Role` → audit role context missing
- It also skips the 401 auto-refresh/retry logic.

Net effect: in production the submit always fails. Worse, because the mock fallback was (correctly) removed, the new error toast will now surface `HTTP 401` to the pharmacist — i.e. the feature is broken, not silently faking success.

The sibling page (`ExpiryProcessingPage.tsx:233`) already does this correctly with `await api.post("/api/v1/inventory/batches/dispose", { ... })`.

**Fix**:
```ts
import { api } from "../../lib/apiClient";
// ...
await api.post("/api/v1/inventory/stocktake", { items: payload });
```
Then align `onError` to extract `.detail` from the thrown envelope the same way ExpiryProcessingPage does (the `api` client throws the raw parsed `{ detail }` object on non-OK, not an `Error`):
```ts
onError: (err: unknown) => {
  const detail =
    typeof err === "object" && err !== null && "detail" in err
      ? String((err as { detail: unknown }).detail)
      : (err instanceof Error ? err.message : null);
  toast.error(detail || t("pharmacy:stocktake.submitError"));
},
```
This was explicitly flagged by the implementation agent in the handoff ("Areas for Review Focus") but left unfixed.

---

## MAJOR Issues

### 2. No test for the `reserved_quantity > 0` dispose guard
**File**: `clinic-cms-merge/app/modules/inventory/services/dispose_service.py:58-61`

The dispose service refuses to dispose a batch with active reservations (`BusinessRuleError`). This is a data-loss prevention guard (zeroing reserved stock would corrupt prescription reservations), but there is **no integration test** covering it. The test file covers happy path, 404 (deleted/nonexistent/cross-clinic), and 403 permission, but not the reserved-quantity rejection.

**Fix**: Add a test that creates a batch with `reserved_quantity > 0`, attempts dispose, and asserts the request is rejected (expected 409/400 per `BusinessRuleError` mapping) and that the batch is NOT soft-deleted.

---

## MINOR Issues

### 3. Out-of-scope Tailwind color refactor mixed into the FE diff
**Files**: `StocktakePage.tsx`, `ExpiryProcessingPage.tsx`

The diff includes a large cosmetic palette migration (`gray→slate`, `indigo→brand`, `red→rose`) unrelated to the task ("Scope guard: chỉ 2 endpoint này + gỡ mock FE. KHÔNG refactor"). Low risk (purely className strings) but it inflates the diff and mixes concerns. Acceptable to keep if it matches a project-wide palette migration already in flight; otherwise it should have been a separate task.

### 4. ExpiryProcessingPage GET batches still has mock fallback
Per handoff, the `GET /inventory/batches` query in ExpiryProcessingPage still falls back to `generateMockBatches()` on error. This was out of scope for TASK-064 but should be tracked as a follow-up so the expiry list does not silently show fake data.

### 5. `submit_stocktake` silently no-ops when an item has zero batches
**File**: `stocktake_service.py:131` — `if variance != 0 and batches:`

If a submitted item has a positive actual count but **no active batches** (expected=0, variance>0), no movement is created and the surplus is silently dropped (it's reported in the result `variance` but never recorded). This may be intentional (can't add stock to a non-existent batch), but consider documenting or surfacing it so the surplus isn't lost without a trace.

---

## Positive Notes

- Permission gates (`inventory.adjust`) present on all 3 routes; `_user_id() is None` → 401 guard on both write endpoints.
- RLS double-enforced: session GUC (`SET LOCAL app.current_clinic_id`) + explicit `clinic_id ==` filters in every query.
- `StockMovement` is the append-only audit log (DB trigger-immutable); write-off movement created *before* zeroing quantity so `quantity_before` is accurate.
- FEFO logic correct: shortage deducted from earliest-expiry batches (bounded by `max_deductible`, can't go negative), surplus added to furthest-expiry batch.
- Dispose transaction-atomic: if any batch in the list fails, the whole request rolls back (consistent, no partial dispose).
- Tenant isolation verified by test (cross-clinic batch → 404, not 403 — correct, avoids existence leak).
- No new DB tables / migration needed — `inventory.adjust` permission pre-seeded.

## Verdict

**CHANGES_REQUESTED** — blocked on Issue #1 (CRITICAL, broken feature) and #2 (MAJOR, untested data-loss guard). BE endpoint code itself is approval-ready; the blockers are an FE auth bug and a missing test.
