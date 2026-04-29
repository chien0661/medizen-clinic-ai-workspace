---
id: TASK-012
type: feature
title: Inventory + Batch + StockMovement + FEFO + Pharmacy Dispense
status: DONE
priority: High
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-27
branch: "feature/task-012-inventory"
tags: [inventory, pharmacy, fefo, sprint-8]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#11-module-medicines--inventory"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#10-module-inventory--pharmacy"
---

# TASK-012: Inventory + Batch + StockMovement + FEFO + Pharmacy Dispense

## Description

Inventory 3 cấp: Medicine (catalog) → InventoryItem (per clinic) → Batch (lô cụ thể). FEFO logic khi reserve. StockMovement audit mọi thay đổi tồn. Pharmacy dispense workflow: pending → reserved → dispensed. Multi-unit (base_unit + pack_size).

## Requirements

- [ ] Migration `0008_create_medicines_inventory.py` (medicine, supplier, inventory_item, batch, stock_movement)
- [ ] FEFO function `reserve_for_prescription(item_id, qty)`:
  - Query batch ORDER BY expiry_date, received_date
  - WHERE actual - reserved > 0, NOT recalled, NOT expired
  - SELECT FOR UPDATE để tránh race
  - Ghi `prescription_item_batch` mapping
- [ ] Dispense function `dispense(prescription_id)`:
  - Deduct actual_quantity, decrement reserved_quantity
  - Insert stock_movement với type=`prescription_out`
  - Update prescription_item.in_house_status='dispensed'
- [ ] Substitute batch function (release reserve cũ + reserve batch mới)
- [ ] Endpoints:
  - CRUD inventory items, batches
  - `POST /api/v1/inventory/purchase-in` (nhập kho từ supplier)
  - `POST /api/v1/inventory/adjustments` (kiểm kê thủ công, kèm reason)
  - `POST /api/v1/pharmacy/dispense/{prescription_id}`
  - `POST /api/v1/pharmacy/substitute-batch`
  - `GET /api/v1/pharmacy/pending-dispense`
- [ ] StockMovement append-only (PostgreSQL trigger chặn UPDATE/DELETE)
- [ ] Trigger validate `batch.reserved_quantity <= actual_quantity`
- [ ] View `v_inventory_status` aggregation per item

## Acceptance Criteria

- [ ] Reserve 100 viên Paracetamol có 3 batch (A:50 expire 2026-06, B:80 expire 2026-08, C:100 expire 2027-01) → reserve A=50 + B=50, FEFO order
- [ ] Concurrent reserve 100 + 100 từ tổng 150 → 1 thành công, 1 nhận InsufficientStockError (test với 2 connection async)
- [ ] Cancel prescription reserved → release reserve, batch reserved_quantity giảm đúng
- [ ] Dispense → stock_movement có quantity_delta âm = qty dispense, quantity_before/after đúng
- [ ] Update trực tiếp stock_movement bị reject (trigger)
- [ ] Multi-unit: nhập 5 hộp × 100 viên → batch.actual_quantity = 500

## Progress Checklist

- [x] Implementation
- [x] Code Review (self-review, 2 iterations)
- [x] Testing (34/34 pass)
- [x] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/inventory/`, `app/modules/pharmacy/`

## Timestamps

- **Created**: 2026-04-26

## Notes

CRITICAL: lock ordering FEFO phải nhất quán để tránh deadlock. Luôn ORDER BY expiry_date ASC + SELECT FOR UPDATE NOWAIT (hoặc SKIP LOCKED tuỳ tradeoff). Cảnh báo near-expiry/low-stock chuyển TASK-015.

## Blockers

- TASK-006 (cần inventory CSV import từ onboarding)
