---
id: TASK-069
type: feature
title: Tag system for medicines and services
status: IN_REVIEW
priority: Medium
assigned: Unassigned
created: 2026-05-31
updated: 2026-05-31  # iteration 2 fixes applied → IN_REVIEW
branch: "feature/TASK-069-tag-system"
jira_key: ""
tags: [medicine, service, tagging, search]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-069: Tag system for medicines and services

## Description

Thêm tính năng **đánh tag** cho thuốc và dịch vụ khi khai báo trong hệ thống.
Tags giúp phân loại và tìm kiếm nhanh hơn theo nhóm, chỉ định, tác dụng, v.v.

## Requirements

- [ ] Thuốc (medicine): có thể gắn nhiều tag khi tạo mới / chỉnh sửa
- [ ] Dịch vụ (service): có thể gắn nhiều tag khi tạo mới / chỉnh sửa
- [ ] Tag có thể tạo mới inline hoặc chọn từ danh sách tag đã có
- [ ] API hỗ trợ filter/search thuốc và dịch vụ theo tag
- [ ] UI hiển thị tag trên danh sách và chi tiết

## Acceptance Criteria

- [ ] Có thể thêm/xóa tag trên form khai báo thuốc
- [ ] Có thể thêm/xóa tag trên form khai báo dịch vụ
- [ ] Tìm kiếm thuốc/dịch vụ theo tag trả về đúng kết quả
- [ ] Tag autocomplete gợi ý từ danh sách tag đã dùng trước đó
- [ ] Tag được lưu và hiển thị nhất quán ở list view và detail view

## Progress Checklist

- [x] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-069/refs/`
- **Code**: (feature branch)
- **Tests**: `docs/tasks/TASK-069/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-069/handoff/`
- **Test Report**: `docs/tasks/TASK-069/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-069/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-069/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-05-31

## Notes

- Cân nhắc dùng bảng `tags` chung (polymorphic) cho cả thuốc và dịch vụ, hoặc bảng tag riêng từng entity.
- Tag nên được normalize (lowercase, trim) trước khi lưu.

## Blockers

None
