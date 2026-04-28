---
id: TASK-010
type: feature
title: Service Catalog + VisitService (Performed Services Tracking)
status: DONE
priority: Medium
assigned: chiendv
created: 2026-04-26
updated: 2026-04-28
branch: "feature/task-010-services"
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

- [x] Migration `0013_create_services.py` (service + visit_service + permission seeding)
- [x] Endpoints:
  - CRUD `/api/v1/services` (admin)
  - `POST /api/v1/visits/{id}/services` (BS chọn dịch vụ)
  - `PATCH /api/v1/visit-services/{id}` (status: ordered → in_progress → completed)
  - `POST /api/v1/visit-services/{id}/cancel`
  - `PATCH /api/v1/visit-services/{id}/price` (price override)
- [x] Service categories: free text per clinic
- [x] VisitService.unit_price = snapshot từ Service.default_price khi tạo
- [x] Override price cần permission `service.price_override` + bắt buộc reason
- [x] Indexes: `ix_visit_service_visit_id`, `ix_service_clinic_active`, `ix_visit_service_clinic_status`

## Acceptance Criteria

- [x] AC #1: Tạo service "Khám tổng quát" giá 150k → BS chọn vào visit → VisitService có unit_price 150k
- [x] AC #2: Sau khi service catalog đổi giá thành 200k, visit_service cũ vẫn giữ 150k
- [x] AC #3: User không có perm `service.price_override` PATCH unit_price → 403
- [x] AC #4: Cancel visit_service status='completed' → 409

## Progress Checklist

- [x] Implementation — commit 6143dd6, dc1f096
- [x] Code Review — self-reviewed, all checks pass
- [x] Testing — 62 tests passing, 86% coverage
- [x] Documentation — final-specs, api-specs, sql-scripts

## Related Files

- **Code**: `clinic-cms/app/modules/services/`

## Timestamps

- **Created**: 2026-04-26
- **Implementation Started**: 2026-04-28
- **Implementation Done**: 2026-04-28
- **Review Done**: 2026-04-28
- **Testing Done**: 2026-04-28
- **Documentation Done**: 2026-04-28
- **Completed**: 2026-04-28

## Notes

Phase sau có package/liệu trình — design schema để dễ mở rộng (thêm `package_id` nullable sau).

## Blockers

- TASK-007
