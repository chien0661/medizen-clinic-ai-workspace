# TASK-012 Test Report

**Date**: 2026-04-27  
**Branch**: feature/task-012-inventory  
**DB**: cms_task012  

---

## Results Summary

| Suite | Tests | Passed | Failed |
|-------|-------|--------|--------|
| Unit – Inventory | 10 | 10 | 0 |
| Unit – Pharmacy | 5 | 5 | 0 |
| Integration – Inventory | 9 | 9 | 0 |
| Integration – Pharmacy | 10 | 10 | 0 |
| **TOTAL** | **34** | **34** | **0** |

---

## Acceptance Criteria Coverage

| AC | Description | Test | Result |
|----|-------------|------|--------|
| AC1 | Reserve 100 from 3 batches (A:50/90d, B:80/120d, C:100/240d) → A=50 + B=50 FEFO | `TestFEFOReservation::test_fefo_ac1` | PASS |
| AC2 | Concurrent reserve 100+100 from 150 → 1 success + 1 InsufficientStockError | `TestConcurrentReservation::test_concurrent_reserve_no_over_reservation` | PASS |
| AC3 | Cancel/release → batch.reserved_quantity decremented exactly | `TestReleaseReservation::test_release_decrements_reserved` | PASS |
| AC4 | Dispense → stock_movement quantity_delta negative, batch decremented | `TestDispense::test_dispense_creates_movement` | PASS |
| AC5 | UPDATE stock_movement rejected by trigger | `TestStockMovementImmutable::test_update_stock_movement_raises` | PASS |
| AC5b | DELETE stock_movement rejected by trigger | `TestStockMovementImmutable::test_delete_stock_movement_raises` | PASS |
| AC6 | 5 packs × 100 tablets → batch.actual_quantity = 500 | `TestPurchaseIn::test_multi_unit_pack_quantity` | PASS |

---

## FEFO Concurrent Stability (5 Runs)

| Run | Result |
|-----|--------|
| 1 | PASS |
| 2 | PASS |
| 3 | PASS |
| 4 | PASS |
| 5 | PASS |

---

## Migration Round-Trip

- `alembic downgrade 0016` → clean (all 6 tables dropped, view dropped, trigger dropped)
- `alembic upgrade head` → clean (all 6 tables created, view created, trigger created, permissions seeded)

---

## Notes

- `slowapi` not in container image requirements — installed at test runtime. Tracked as deferred dep issue.
- `appointments`/`visits` modules not in this worktree — removed from main.py imports (those modules exist only in merged branches).
- FEFO concurrent test uses `SET LOCAL app.current_clinic_id = '...'` (f-string) because PostgreSQL SET does not support parameterized values.
