---
id: TASK-011
type: feature
title: Medicine Catalog + Prescription (In-House / External Mixed)
status: TODO
priority: High
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
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

- [ ] Migration `0009_create_prescriptions.py` (prescription + prescription_item + prescription_item_batch)
- [ ] Bảng `medicine` (system-level + clinic-level), endpoints `/api/v1/medicines`
- [ ] Endpoints prescription:
  - `POST /api/v1/visits/{id}/prescriptions` (tạo đơn)
  - `GET /api/v1/medicines/search?q=...&with_stock=true` (search + indicator còn hàng)
  - `POST /api/v1/prescriptions/{id}/items` (thêm item, suggest dispense_source)
  - `POST /api/v1/prescriptions/{id}/cancel`
  - `GET /api/v1/prescriptions/{id}/print` (HTML template)
- [ ] Auto-suggest dispense_source: nếu `inventory.available > 0` → in_house, else → external; BS có thể override
- [ ] Print template config qua `clinic_settings.prescription.print_mode` (all/external_only/ask)
- [ ] PrescriptionItem.medicine_id nullable (cho phép kê thuốc text khi external)

## Acceptance Criteria

- [ ] Tạo prescription mixed: 2 in_house + 1 external → header `dispense_type='mixed'`
- [ ] Search medicine với inventory→ kết quả có flag `in_stock: true/false`
- [ ] BS chọn medicine trong stock + qty > available → cảnh báo (nhưng cho phép override để chuyển external)
- [ ] Cancel prescription đã dispense → 409 (chỉ pending/reserved mới hủy được)
- [ ] Print template render đúng header clinic + danh sách thuốc + dosage

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/medicines/`, `app/modules/prescriptions/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Reserve inventory khi tạo prescription in_house — chi tiết logic nằm ở TASK-012 (Inventory). Task này tạo skeleton API, gọi `inventory_service.reserve()`.

## Blockers

- TASK-007, TASK-012 (Inventory phải có trước để reserve hoạt động)
