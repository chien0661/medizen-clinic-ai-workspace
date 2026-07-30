---
id: TASK-125
type: feature
title: "Phân loại danh mục dịch vụ: khám / thủ thuật / test (service type)"
status: IN_REVIEW
priority: High
assigned: Code Review Agent
created: 2026-07-30
updated: 2026-07-30
branch: "feature/TASK-125"
tags: [services, catalog, classification, feature]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-125/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-125: Phân loại danh mục dịch vụ (khám / thủ thuật / test)

**Nguồn:** Ý #2 trong batch yêu cầu 2026-07-30. **Nền móng** cho TASK-128 (chiết khấu theo thủ thuật/thuốc) và TASK-126 (thống kê theo loại dịch vụ).

## Description
Danh mục dịch vụ hiện chưa phân biệt loại. Cần thêm **service_type** (enum: `consultation` khám / `procedure` thủ thuật / `test` xét nghiệm — chốt danh sách khi /task-plan) để phân loại, lọc, báo cáo, và làm cơ sở tính chiết khấu (thủ thuật) ở Payroll.

## Requirements
- [x] BE: thêm bảng cấu hình `service_type` (per-clinic, admin CRUD — không phải enum cứng) + FK `service.service_type_id` + migration 0071 (seed 3 mặc định/clinic).
- [x] BE: schema + API create/update/list/filter theo `service_type_id`; CRUD `/service-types`.
- [x] FE: ServiceTypesPage (cấu hình loại) + ServicesPage (chọn/hiển thị loại, CSV theo mã loại) + ServicesTab (badge).
- [x] Không hồi quy luồng service→visit→billing hiện có (service_type_id nullable, không đụng visit_service/billing).

## Acceptance Criteria
- [x] Mỗi dịch vụ có 0 hoặc 1 service_type; tạo/sửa/lọc theo loại hoạt động (BE+FE).
- [x] Dữ liệu cũ được backfill hợp lý (NULL = chưa phân loại), không vỡ visit-service/billing.
- [x] Unit test BE (73 passed, mock-based) + FE test (20 passed) written and run. Integration test (real DB) written but **unverified** — no DB stack available in this environment (see handoff).

## Progress Checklist
- [x] Planning | [x] Implementation | [ ] Code Review | [ ] Testing | [ ] Documentation

## Notes / Dependencies
- **SCOPE (chốt 2026-07-30):** service_type là **bảng cấu hình admin quản lý được** (không phải enum cứng); `service.service_type_id` FK. Xem implementation-plan.
- Blocker cho TASK-128 (chiết khấu **% theo loại**) và TASK-126 (thống kê theo loại).
- Liên quan module `services`. Head alembic thực tế = 0070 → migration mới 0071 (`0071_service_type.py`).
- Implementation hoàn tất trên `feature/TASK-125` (BE + FE worktrees), đã push, CHƯA merge vào `dev` — chờ Code Review Agent.

## Blockers
Không.

## Implementation Notes (2026-07-30)
Xem chi tiết đầy đủ tại `docs/tasks/TASK-125/handoff/implementation-to-review.md`.
