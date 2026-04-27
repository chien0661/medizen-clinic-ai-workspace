---
id: TASK-004
type: feature
title: Users + RBAC (Role + Permission + Multi-Role)
status: IN_PROGRESS
priority: High
assigned: code-implementation-agent
created: 2026-04-26
updated: 2026-04-27
branch: "feature/task-004-rbac"
tags: [rbac, users, sprint-2]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#15-rbac-implementation"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#13-module-auth--rbac"
---

# TASK-004: Users + RBAC (Role + Permission + Multi-Role + Extra Grants/Denies)

## Description

CRUD User trong clinic, RBAC với `Role`, `Permission`, `UserRole` (M2M), `UserExtraPermission` (per-user grant/deny). Decorator `@require_permission("patient.write")` cho route. Permission catalog seed sẵn (theo §13.5 BA), default role-permission mapping (Admin/Doctor/Nurse/Pharmacist/Receptionist).

## Requirements

- [ ] Migrations: `0002_setup_rbac.py` (role, permission, role_permission, user_role, user_extra_permission)
- [ ] Migration `0015_seed_permissions_and_presets.py` (seed permissions + system roles + default mapping)
- [ ] Endpoints CRUD: `/api/v1/users`, `/api/v1/users/{id}/roles`, `/api/v1/roles`, `/api/v1/roles/{id}/permissions`, `/api/v1/users/{id}/extra-permissions`
- [ ] `app/core/permissions.py` — `require_permission(code)` FastAPI dependency
- [ ] User effective permission = (Σ permission của roles) + extra_grants - extra_denies
- [ ] Cache effective permissions trong JWT payload (signed) hoặc Redis (5 min TTL)
- [ ] User có thể có nhiều role (multi-role)
- [ ] Khi đổi role/permission → invalidate cache
- [ ] System role không cho xóa (`is_system = true`)

## Acceptance Criteria

- [ ] Seed data: 5 system roles + ~30 permissions theo catalog §13.5
- [ ] Default mapping đúng theo bảng §13.6 (Admin có hết, Doctor có vital.write, etc.)
- [ ] Test: user có role Doctor không gọi được `POST /pharmacy/dispense` (403)
- [ ] Test: user có extra_deny `invoice.void` dù role có permission đó vẫn bị block
- [ ] Test: thay đổi role → permission có hiệu lực ở request tiếp theo

## Progress Checklist

- [x] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-004/refs/`
- **Code**: `clinic-cms/app/modules/users/`
- **SQL Scripts**: `docs/tasks/TASK-004/deliveries/sql-scripts/`

## Timestamps

- **Created**: 2026-04-26

## Notes

User-Clinic relationship là 1-1 (xác nhận trong §31 BA). Multi-clinic per user là phase sau.

## Blockers

- TASK-003
