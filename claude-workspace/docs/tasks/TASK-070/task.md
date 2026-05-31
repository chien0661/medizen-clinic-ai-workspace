---
id: TASK-070
type: feature
title: FE Super Admin — Quản lý toàn hệ thống (clinics + accounts)
status: DOCUMENTING
priority: High
assigned: Documentation Agent
created: 2026-05-31
updated: 2026-05-31
branch: "feature/TASK-070-superadmin-fe"
jira_key: ""
tags: [ui, super-admin, multi-tenant, clinic-management]
affected-repos: [clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "BE API: clinic-cms-merge/app/modules/superadmin/api/routes.py"
    - "BE migration: clinic-cms-merge/alembic/versions/0036_super_admin.py"
    - "Seed: clinic-cms-merge/scripts/seed_superadmin.py (superadmin / Super@12345)"
---

# TASK-070: FE Super Admin — Quản lý toàn hệ thống

## Description

Build giao diện Super Admin cho Clinic CMS. Super Admin là role cấp platform (trên tất cả phòng khám), có thể:
- Xem tổng quan toàn hệ thống (tất cả clinics, users, stats)
- Tạo / sửa / vô hiệu hóa phòng khám
- Tạo tài khoản admin cho từng phòng khám
- Reset mật khẩu, khóa/mở khóa tài khoản bất kỳ
- Xem audit logs cross-tenant

**BE đã hoàn chỉnh** — migration 0036, `/api/v1/superadmin/*`, seed script.
FE cần build từ đầu, không có page nào cho super admin hiện tại.

**Tài khoản test**: `superadmin` / `Super@12345`
(Chạy `alembic upgrade head` → `python scripts/seed_superadmin.py` trước)

## BE API Reference

Base URL: `/api/v1/superadmin/` — require `is_superuser: true` trong JWT

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/stats` | Stats: total clinics, users, active today |
| GET | `/clinics` | Danh sách tất cả phòng khám |
| POST | `/clinics` | Tạo phòng khám (name, code, specialty) |
| PATCH | `/clinics/{id}` | Cập nhật / toggle active |
| GET | `/accounts?clinic_id=&search=&skip=&limit=` | Accounts cross-tenant |
| POST | `/accounts` | Tạo account admin cho clinic |
| PATCH | `/accounts/{id}` | Khóa / mở khóa (is_active, is_locked) |
| POST | `/accounts/{id}/reset-password` | Reset mật khẩu |
| GET | `/roles` | Danh sách roles toàn hệ thống |
| GET | `/audit-logs?clinic_id=&action=&skip=&limit=` | Audit cross-tenant |

## Requirements

### Auth & Route Guard
- [ ] Đọc `is_superuser` từ JWT decoded payload vào `authStore`
- [ ] Guard `<RequireSuperuser>` — redirect `/dashboard` nếu thiếu quyền
- [ ] Ẩn hoàn toàn menu super admin với user thường (clinic admin, doctor, v.v.)
- [ ] API client `src/modules/superadmin/api.ts` — typed wrappers cho 10 endpoints trên

### Navigation
- [ ] Thêm section "Super Admin" trong Sidebar (chỉ render khi `is_superuser`)
- [ ] Menu items: Tổng quan · Phòng khám · Tài khoản · Audit logs

### Trang 1: Dashboard (`/superadmin`)
- [ ] Stats cards: Tổng phòng khám, Tổng tài khoản, Hoạt động hôm nay
- [ ] Bảng top 5 phòng khám mới nhất
- [ ] Cảnh báo: clinic inactive, account bị khóa

### Trang 2: Phòng khám (`/superadmin/clinics`)
- [ ] Bảng: tên, code, specialty, trạng thái, số accounts, ngày tạo
- [ ] Nút "Tạo phòng khám" → modal: name, code, specialty
- [ ] Toggle active/inactive inline
- [ ] Search/filter theo tên, code, trạng thái

### Trang 3: Tài khoản (`/superadmin/accounts`)
- [ ] Bảng cross-tenant: username, họ tên, email, clinic, roles, trạng thái
- [ ] Filter theo clinic (dropdown), search theo tên/username
- [ ] Nút "Tạo tài khoản" → form: chọn clinic, username, full_name, email, password, role_codes
- [ ] Action per row: Khóa/Mở khóa · Reset mật khẩu
- [ ] Badge: Active / Locked / Inactive

### Trang 4: Audit Logs (`/superadmin/audit-logs`)
- [ ] Bảng: timestamp, clinic, user, action, entity — cross-tenant
- [ ] Filter theo clinic + action
- [ ] Pagination (50/trang)

## Acceptance Criteria

- [ ] Login `superadmin` → thấy section Super Admin trong sidebar
- [ ] Login `admin` (clinic user) → KHÔNG thấy section Super Admin
- [ ] Tạo phòng khám mới → xuất hiện trong danh sách ngay
- [ ] Tạo tài khoản admin cho clinic → login được với tài khoản đó
- [ ] Khóa tài khoản → login thất bại với tài khoản đó
- [ ] Reset mật khẩu → login với mật khẩu mới thành công
- [ ] Audit logs load và filter đúng theo clinic

## Progress Checklist

- [x] Implementation
- [x] Code Review — APPROVED 2026-05-31 round 2 (commit 721433b, see handoff/review-to-test.md): all 3 round-1 blockers + nits 1/2/3 resolved (FE types aligned to real BE shapes, Sidebar clean, mocks fixed). 22/22 tests pass.
- [x] Testing — PASS 2026-05-31 (22/22 unit, TC-001/002/003/004 all PASS, see deliveries/test-reports/test-report.md)
- [ ] Documentation

## Related Files

- **BE API**: `clinic-cms-merge/app/modules/superadmin/api/routes.py`
- **BE Schemas**: `clinic-cms-merge/app/modules/superadmin/schemas.py`
- **BE Service**: `clinic-cms-merge/app/modules/superadmin/service.py`
- **FE pattern ref**: `clinic-cms-web/src/pages/admin/UserManagementPage.tsx`
- **Input Specs**: `docs/tasks/TASK-070/refs/`
- **Tests**: `docs/tasks/TASK-070/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-070/handoff/`
- **Test Report**: `docs/tasks/TASK-070/deliveries/test-reports/test-report.md`

## Timestamps

- **Created**: 2026-05-31

## Notes

- `authStore` cần thêm field `isSuperuser: boolean` từ JWT payload
- Super admin thuộc SYSTEM clinic (ID cố định `00000000-...00aa`) — FE không cần truyền clinic_id header cho superadmin APIs
- Dev server proxy `/api` → BE:8001 — kiểm tra superadmin routes đã được proxy chưa
- Tham khảo `UserManagementPage.tsx` làm base pattern cho bảng accounts
- Tạo nhánh `feature/TASK-070-superadmin-fe` từ `main` của `clinic-cms-web`

## Blockers

- Cần BE chạy migration 0036 + seed_superadmin.py trước khi test FE
