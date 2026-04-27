---
id: TASK-020
type: feature
title: FE — Pharmacy (Pending Dispense + Substitute Batch + Inventory + Stock Adjustment)
status: TODO
priority: High
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [frontend, pharmacy, inventory, sprint-15]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#11-module-medicines--inventory"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#10-module-inventory--pharmacy"
---

# TASK-020: FE — Pharmacy Module (Dispense + Inventory Management)

## Description

UI cho dược sĩ: list pending dispense, dispense workflow (verify batch FEFO + confirm), substitute batch khi lô bị hỏng, inventory list với cảnh báo (tồn thấp/sắp hết hạn/hết hạn/thu hồi), stock adjustment (kiểm kê), purchase-in form.

## Requirements

- [ ] **Pending dispense list** (`/pharmacy/pending`)
  - Group: trong ngày | overdue
  - Card: prescription_id, patient, visit_number, doctor, items count, total amount
  - Click → dispense detail
- [ ] **Dispense detail** (`/pharmacy/dispense/:id`)
  - Items list: medicine name, qty, batch breakdown (theo FEFO reservation đã reserve sẵn)
  - Per item: button "Substitute batch" (chọn batch khác nếu lô reserved bị hỏng)
  - Verify checkbox cho mỗi item (dược sĩ confirm thấy đủ thực tế)
  - "Print label" button per item (in nhãn thuốc qua POS printer)
  - "Dispense all" → call API → status='dispensed', deduct stock
  - Khi dispense xong → suggest về billing để collect payment
- [ ] **Substitute batch modal**
  - List batch còn available (sort FEFO, hiển thị expiry, qty available)
  - Reason input
  - Confirm → release reserve cũ + reserve mới
- [ ] **Inventory list** (`/inventory`)
  - Table: medicine, total stock, reserved, available, reorder_point flag, near_expiry flag
  - Filter: low stock | near expiry | expired | recalled
  - Search by name/code/atc
  - Click → inventory item detail
- [ ] **Inventory item detail** (`/inventory/:id`)
  - Tabs: Batches | Movement history | Settings
  - Batches: batch_number, expiry, qty, status (active/recalled/expired)
  - Movement: stock_movement timeline (purchase_in/dispense/adjustment/...)
  - Settings: reorder_point, default_purchase_price, default_sale_price, location
- [ ] **Stock adjustment form**
  - Multi-row: select batch, qty delta, reason (required)
  - Preview total impact + confirm
  - Audit: record current user + timestamp
- [ ] **Purchase-in form** (`/inventory/purchase-in`)
  - Supplier select + new
  - Multi-row: medicine, batch_number, expiry, qty (theo pack hoặc base_unit), unit price
  - Preview total + confirm → tạo batch + stock_movement(purchase_in)
- [ ] **Cảnh báo dashboard widget** (gắn vào home dashboard TASK-024)
  - Count: low stock, near expiry, expired, recalled
  - Click → filter inventory list

## Acceptance Criteria

- [ ] Pending dispense list refresh khi có prescription mới (poll hoặc WebSocket)
- [ ] Substitute batch: release đúng lô cũ + reserve lô mới, total qty không đổi
- [ ] Dispense → stock_movement có quantity_delta âm = qty dispense
- [ ] Inventory filter "near_expiry" với threshold 90 days đúng records
- [ ] Stock adjustment ghi reason; user không có perm `inventory.adjust` → button disabled
- [ ] Purchase-in 5 hộp × 100 viên → batch.actual_quantity = 500 (multi-unit conversion đúng)
- [ ] Print medicine label qua POS printer (template tên thuốc + dosage + bệnh nhân)

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/desktop/src/modules/pharmacy/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Dispense action là CRITICAL: phải online (không cho offline vì sẽ oversell). UI phải hiển thị error rõ nếu offline.

## Blockers

- TASK-017, TASK-011 (Prescription), TASK-012 (Inventory + Pharmacy API)
