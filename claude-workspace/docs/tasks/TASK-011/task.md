---
id: TASK-011
type: feature
title: Medicine Catalog + Prescription (In-House / External Mixed)
status: DONE
priority: High
assigned: chiendv
created: 2026-04-26
updated: 2026-04-27
branch: "feature/task-011-prescriptions"
tags: [medicine, prescription, sprint-7]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#12-module-prescriptions--pharmacy"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#9-module-prescription"
---

# TASK-011: Medicine Catalog + Prescription (In-House / External Mixed)

## Description

Master data Medicine (system-level + clinic-level), Prescription per visit. Per-item dispense_source: in_house (lấy từ inventory phòng khám) hoặc external (kê text, BN ra ngoài mua). Một đơn có thể mixed. Logic suggest source dựa trên inventory available. In đơn theo template.

## Requirements

- [x] Migration `0018_create_prescriptions.py` (prescription + prescription_item) + FK to prescription_item_batch
- [x] Bảng `medicine` (TASK-012), endpoints `/api/v1/medicines/search`
- [x] Endpoints prescription:
  - `POST /api/v1/visits/{id}/prescriptions` (tạo đơn)
  - `GET /api/v1/medicines/search?q=...&with_stock=true` (search + indicator còn hàng)
  - `POST /api/v1/prescriptions/{id}/items` (thêm item, suggest dispense_source)
  - `POST /api/v1/prescriptions/{id}/cancel`
  - `GET /api/v1/prescriptions/{id}/print` (HTML template)
  - `PATCH /api/v1/prescriptions/{id}` (update header)
  - `PATCH /api/v1/prescription-items/{id}` (update item)
  - `DELETE /api/v1/prescription-items/{id}` (delete item)
  - `POST /api/v1/prescriptions/{id}/submit` (draft → pending)
- [x] Auto-suggest dispense_source: nếu `inventory.available >= quantity` → in_house, else → external; BS có thể override
- [x] Print template với 3 modes: all/external_only/ask
- [x] PrescriptionItem.medicine_id nullable (cho phép kê thuốc text khi external)

## Acceptance Criteria

- [x] Tạo prescription mixed: 2 in_house + 1 external → header `dispense_type='mixed'`
- [x] Search medicine với inventory → kết quả có flag `in_stock: true/false`
- [x] BS chọn medicine trong stock + qty > available → cảnh báo (nhưng cho phép override để chuyển external)
- [x] Cancel prescription đã dispense → 409 (chỉ pending/draft mới hủy được)
- [x] Print template render đúng header clinic + danh sách thuốc + dosage

## Progress Checklist

- [x] Implementation
- [x] Code Review (Self-Review)
- [x] Testing
- [x] Documentation

## Related Files

- **Code**: `clinic-cms-task011/app/modules/prescriptions/`
- **Migrations**: `clinic-cms-task011/alembic/versions/0018_create_prescriptions.py`, `0018a_add_prescription_permissions.py`
- **Tests**: `clinic-cms-task011/tests/integration/prescriptions/`, `tests/unit/prescriptions/`
- **API Spec**: `docs/tasks/TASK-011/deliveries/api-specs/prescriptions-api.md`
- **DDL**: `docs/tasks/TASK-011/deliveries/sql-scripts/prescriptions-ddl.md`
- **Functional Design**: `docs/tasks/TASK-011/deliveries/final-specs/prescriptions-functional-design.md`

## Timestamps

- **Created**: 2026-04-26
- **Implementation Started**: 2026-04-27
- **Tests Passed**: 2026-04-27 (38 tests, all PASS)
- **Review Approved**: 2026-04-27 (Self-Review)
- **Completed**: 2026-04-27

## Notes

- Calls TASK-012's `reservation_service.reserve_for_prescription()` and `release_reservation()` directly
- Migration 0018 adds FK from `prescription_item_batch.prescription_item_id → prescription_item.id` (stub from TASK-012 now enforced)
- `medicine_search_router` must be registered BEFORE `inventory_router` in `main.py` to prevent route collision
- Coverage 65% due to pytest-asyncio + coverage async instrumentation limitation; all functional paths verified via passing tests

## Blockers (Resolved)

- TASK-012 (Inventory) ✅ — provides medicine catalog, inventory, reservation_service
