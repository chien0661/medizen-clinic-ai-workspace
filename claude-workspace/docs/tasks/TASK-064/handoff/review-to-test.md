# Handoff: TASK-064 → Test

**From**: Code Review Agent
**To**: Test Agent
**Decision**: APPROVED (Round 2 — fix verification)
**Date**: 2026-05-31
**Status**: IN_TESTING

## Round 2 Verdict

Both required fixes from the Round 1 CHANGES_REQUESTED review are verified correct. APPROVED for testing.

## Fix Verification

### Fix 1 — StocktakePage.tsx auth (CRITICAL) — VERIFIED

`clinic-cms-web/src/pages/pharmacy/StocktakePage.tsx`

- `import { api } from "../../lib/apiClient";` present (line 22).
- Submit mutation uses `await api.post("/api/v1/inventory/stocktake", { items: payload })` (line 133) — no raw `fetch()` anywhere in the file. The `api` client auto-attaches Authorization / X-Clinic-Id / X-Applied-Role headers and handles 401 refresh.
- `onError` extracts `.detail` from the thrown envelope (lines 139–145): checks for object with `detail` property, falls back to `err.message`, then to the i18n `submitError` string.

### Fix 2 — reserved_quantity dispose guard test (MAJOR) — VERIFIED

`clinic-cms-merge/tests/integration/inventory/test_stocktake_dispose.py`

`test_dispose_batch_with_reservation_returns_400` (lines 405–462):
- Seeds batch qty=40, then sets `reserved_quantity = 5` via raw SQL to simulate an active reservation.
- POSTs to `/api/v1/inventory/batches/dispose`, asserts HTTP **400** and `error.code == "BUSINESS_RULE_VIOLATION"`.
- Data integrity re-query: asserts `is_deleted == false` and `actual_quantity == 40` (batch NOT soft-deleted, qty unchanged) after the rejected dispose.

Confirmed against the service: `dispose_service.py:58` raises `BusinessRuleError` when `reserved_quantity > 0`; `exceptions.py:64-71` maps `BusinessRuleError` → HTTP 400 / code `BUSINESS_RULE_VIOLATION`.

## Test Results

- **BE**: `docker exec clinic_cms_w2e_api pytest -q tests/integration/inventory/test_stocktake_dispose.py` → **13 passed** in 19.90s (12 original + 1 new reservation guard).
- **FE**: `npm run type-check` → **no errors in StocktakePage.tsx or ExpiryProcessingPage.tsx**. Remaining errors are pre-existing and out of scope: `Sidebar.tsx` (unused `ShieldCheck`, `bhytEnabled`), `admin/api.ts` (duplicate `items` declarations), `LoginPage.tsx` (`must_rotate`), `i18n-default-language.test.ts` (unused `beforeEach`).

## Notes for Test Agent

- Container: `clinic_cms_w2e_api` (api), `clinic_cms_w2e_postgres` (db). FE dev server proxies to BE.
- Endpoints to exercise: `GET /api/v1/inventory/stocktake`, `POST /api/v1/inventory/stocktake`, `POST /api/v1/inventory/batches/dispose`.
- Permission gate: `inventory.adjust` (pharmacist has it, doctor does not).
- Suggested manual/E2E focus: full 3-step Stocktake wizard with a real login (auth headers now attached), and the dispose-with-reservation rejection surfacing a useful toast message.
- Pre-existing FE type errors above are NOT introduced by this task — do not file them against TASK-064.
