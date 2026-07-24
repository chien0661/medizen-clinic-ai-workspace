# Test Report: TASK-113 - low-stock stock-status (M-15)

**Test Agent:** Automation Tester
**Date:** 2026-07-25
**Status:** ALL IN-SCOPE PASSED (backend + frontend)

## Environment — Backend

- Isolated Docker stack `w113` (project `-p w113`), built from worktree
  `F:/MyProject/clinic-cms-workspace/_fix113-be`, branch
  `fix/TASK-113-low-stock-status` @ `94cd233`.
- Ports: api `9960`, postgres `5460`, redis `6442` (adjusted the worktree's
  scaffolded `docker/docker-compose.fix113.yml` to these values — infra file
  only, no source touched). No collision with main/dev/w2e.
- Migrated `alembic upgrade head` -> reached **0069** (single head confirmed
  via `alembic heads`). Seeded superadmin.
- Stack torn down (`docker compose -p w113 -f docker-compose.fix113.yml down -v`)
  after the run.

## Environment — Frontend

- Worktree `F:/MyProject/clinic-cms-workspace/_fix113-web`, branch
  `fix/TASK-113-low-stock-status` @ `2bb6b48`. `node_modules` already
  installed and newer than `package-lock.json` (no `npm ci` needed; skipped
  redundant install). No Docker involved for this half.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Backend integration (`tests/integration/inventory`) | 45 | 45 | 0 | 100% |
| Frontend vitest (`src/tests/pharmacy`) | 66 | 66 | 0 | 100% |
| Frontend `type-check` (`tsc --noEmit`) | - | clean (exit 0) | - | - |

Commands:
- `pytest -q --tb=short tests/integration/inventory`
- `npx vitest run src/tests/pharmacy`
- `npm run type-check`

## Key Assertions Verified

- **Single migration head at 0069** — confirmed via `alembic heads` ->
  `0069 (head)` only.
- **Item below resolved threshold -> `is_low_stock=true` + `reorder_min` set,
  matches `/reports/inventory-status` low_stock_count (the M-15 point)** —
  `TestStockStatusLowStockFields::test_stock_status_exposes_reorder_min_and_is_low_stock`
  (`tests/integration/inventory/test_alert_threshold_e2e.py:595`) — PASSED.
  Item seeded with `low_stock_min=50`, batch qty 15 (avail 15 <= 50) ->
  `/inventory/stock-status` row has `is_low_stock=True`, `reorder_min=50`,
  `available_qty=15`; cross-checked against `/reports/inventory-status` row
  for the same item (`is_low_stock`/`reorder_min` match); additionally
  asserts the **full set** of low-stock item IDs from `/stock-status` equals
  the set from `/reports/inventory-status` — exactly the M-15 consistency
  requirement, not just a single-item spot check.
- **No-threshold-configured item is not flagged low-stock** —
  `test_stock_status_no_threshold_configured_is_not_low_stock` — PASSED.
- **FE inventory badge/filter** —
  `it("AC (TASK-113/M-15): low_stock filter + badge use reorder_min/is_low_stock")`
  in `src/tests/pharmacy/InventoryPage.test.tsx:233` — PASSED, part of the 8
  passing `InventoryPage.test.tsx` cases.
- **No new FE breakage**: all 7 pharmacy test files (66 tests total) passed;
  `tsc --noEmit` clean.

## Failures

None. 45/45 backend + 66/66 frontend passed; type-check clean.

## Next Steps

All in-scope tests passed. Ready to proceed to Documentation phase.

**Task status -> DOCUMENTING**

---

**Total Scenarios:** 111 (45 backend + 66 frontend) + type-check
**Environment:** isolated Docker stack `w113` (api 9960 / pg 5460 / redis 6442) for backend, torn down after run; FE run directly in worktree, no Docker.
