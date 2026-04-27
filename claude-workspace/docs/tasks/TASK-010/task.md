---
id: TASK-010
type: feature
title: Service Catalog + VisitService (Performed Services Tracking)
status: TODO
priority: Medium
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [service, sprint-6]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#10-module-services"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#8-module-service-catalog"
---

# TASK-010: Service Catalog + VisitService (Performed Services Tracking)

## Description

Catalog dịch vụ phòng khám (Khám, Thủ thuật, Xét nghiệm...) đồng giá per clinic. `VisitService` ghi nhận dịch vụ thực hiện trong visit, snapshot price từ catalog tại thời điểm tạo. Override giá cần permission + reason.

## Requirements

- [ ] Migration `0007_create_services.py` (service + visit_service)
- [ ] Endpoints:
  - CRUD `/api/v1/services` (admin)
  - `POST /api/v1/visits/{id}/services` (BS chọn dịch vụ)
  - `PATCH /api/v1/visit-services/{id}` (status: ordered → in_progress → completed)
  - `POST /api/v1/visit-services/{id}/cancel`
- [ ] Service categories: free text per clinic (hiển thị grouped trong UI)
- [ ] VisitService.unit_price = snapshot từ Service.default_price khi tạo
- [ ] Override price cần permission `service.price_override` + bắt buộc `discount_reason`
- [ ] Indexes: `ix_visit_service_visit_id`, `ix_service_clinic_active`

## Acceptance Criteria

- [ ] Tạo service "Khám tổng quát" giá 150k → BS chọn vào visit → VisitService có unit_price 150k
- [ ] Sau khi service catalog đổi giá thành 200k, visit_service cũ vẫn giữ 150k
- [ ] User không có perm `service.price_override` PATCH unit_price → 403
- [ ] Cancel visit_service status='completed' → 409 (chỉ ordered/in_progress mới hủy được)

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/services/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Phase sau có package/liệu trình — design schema để dễ mở rộng (thêm `package_id` nullable sau).

## Blockers

- TASK-007
