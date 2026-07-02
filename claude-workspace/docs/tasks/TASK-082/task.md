---
id: TASK-082
type: feature
title: Cấu hình phân quyền đơn giản hóa — cho phép 1 bác sĩ có đủ quyền (phòng khám nhỏ)
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-02
updated: 2026-07-03
branch: "feature/TASK-084-exam-templates"
jira_key: ""
tags: [rbac, permissions, config, small-clinic]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-082/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-082: Cấu hình phân quyền đơn giản hóa — cho phép 1 bác sĩ có đủ quyền (phòng khám nhỏ)

## Description

Hệ thống RBAC hiện tại (TASK-004: 5 system role, 38 permission, multi-role + per-user grant/deny override) khá đầy đủ nhưng nặng nề với các phòng khám nhỏ. Yêu cầu: **đơn giản hóa việc cấu hình quyền** để một phòng khám nhỏ (chỉ có 1 bác sĩ) có thể cấu hình để bác sĩ đó nắm **đủ quyền** vận hành toàn bộ hệ thống, và việc cấu hình này thực hiện **ngay trên hệ thống** (UI), không cần can thiệp kỹ thuật.

Mục tiêu: người quản trị phòng khám tự bật/tắt, gom quyền theo mô hình vận hành (phòng khám nhỏ vs. phòng khám nhiều nhân sự) mà không phải hiểu chi tiết 38 permission.

## Requirements

- [ ] Cơ chế cấu hình quyền ở cấp phòng khám (clinic-level) cho phép chọn "chế độ" vận hành: ví dụ **Phòng khám nhỏ (1 BS toàn quyền)** vs **Phòng khám đầy đủ vai trò**.
- [ ] Ở chế độ phòng khám nhỏ: 1 tài khoản bác sĩ được gán preset "đủ quyền" (all-in-one) bao trùm tiếp nhận, khám, kê đơn, dược, thu ngân, báo cáo — nhưng KHÔNG vượt ra ngoài ranh giới tenant (không chạm superadmin / cross-clinic).
- [ ] Màn hình cấu hình quyền trên UI (admin) dễ hiểu: gom permission theo nhóm chức năng, mô tả bằng ngôn ngữ nghiệp vụ (không phải mã `perm.code`).
- [ ] Giữ nguyên tính đúng đắn của RLS/tenancy và cache permission (JWT 15 phút + Redis `user:perms:{user_id}` 5 phút TTL) — đổi preset phải invalidate cache.
- [ ] Không phá vỡ mô hình multi-role + grant/deny override hiện có; preset là lớp tiện lợi phía trên.
- [ ] Migration Alembic cho mọi thay đổi schema (preset/config), theo quy ước `NNNN_*.py`.

## Acceptance Criteria

- [ ] Admin phòng khám bật chế độ "Phòng khám nhỏ" → tài khoản bác sĩ được cấp preset đủ quyền và truy cập được tất cả module nghiệp vụ trong tenant.
- [ ] Chuyển đổi chế độ có hiệu lực ngay sau khi cache permission được invalidate (kiểm chứng bằng e2e: 403 → 200 sau khi đổi).
- [ ] Preset "đủ quyền" KHÔNG bao gồm quyền superadmin/cross-clinic (kiểm chứng: bác sĩ không thấy dữ liệu clinic khác).
- [ ] Màn cấu hình quyền hiển thị quyền theo nhóm nghiệp vụ, có mô tả tiếng Việt.
- [ ] E2E test cho toàn bộ luồng cấu hình quyền (bắt buộc cho permission gate mới — theo Quality Gates).

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-082/refs/` *(DetailDesign, SRS, implementation-plan)*
- **Code**: (feature branch)
- **Tests**: `docs/tasks/TASK-082/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-082/handoff/`
- **Test Report**: `docs/tasks/TASK-082/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-082/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-082/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-07-02
- **Implementation Completed**: 2026-07-03
- **Testing Completed**: 2026-07-03
- **Documentation Completed**: 2026-07-03

## Notes

- Nền tảng RBAC tham chiếu: TASK-004 (5 role, 38 permission, multi-role, grant/deny override) và `PROJECT.md` mục Authorization (`app/core/permissions.py`, `require_permission`).
- Cân nhắc: preset là "role tổng hợp cấp tenant" hay là cờ cấu hình clinic sinh quyền động — cần chốt ở `/task-plan`.
- Ranh giới bảo mật: không được cho phép leo thang lên superadmin/cross-tenant.

## Blockers

None
