---
id: TASK-061
type: feature
title: Auth & RBAC gaps — clinic-admin password reset, forgot-password, clone-role via API, full SoD coverage
status: TODO
priority: High
assigned: Unassigned
created: 2026-05-30
updated: 2026-05-30
branch: ""
jira_key: ""
tags: [backend, auth, rbac, security, gap-fix]
affected-repos: [clinic-cms-merge]
parent: TASK-052
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/tasks/TASK-052/deliveries/api-specs/api-mapping.md  # nguồn GAP/DRIFT đã verify (file:line)"
    - "scripts/function_list_data.py  # function list 461 fn"
    - "PROJECT.md  # build/test, module map (target ../clinic-cms-merge)"
---

# TASK-061: Auth & RBAC gaps — clinic-admin password reset, forgot-password, clone-role via API, full SoD coverage

## Description

Đóng lỗ hổng auth/RBAC: AUTH-008/HR-004 cho clinic admin reset/generate mật khẩu nhân viên (hiện chỉ super admin platform có), AUTH-009 forgot-password self-service qua email, RBAC-008 expose clone system role qua API (POST /roles hiện tạo role rỗng; clone_system_role là dead code), RBAC-016 mở rộng SoD coverage (hiện chỉ gate 2 action: dispense + payment; make_sod_dep factory chưa nối route nào; Rx self-approve & price self-approve chưa chặn).

> **Parent**: TASK-052 (API mapping). Task này hiện thực một cụm GAP/DRIFT đã được xác minh source (file:line) trong `api-mapping.md`. **Tuân thủ Database Error Handling Protocol** và Testing Strategy (integration real-DB Postgres+Redis) trong CLAUDE.md/PROJECT.md.

**Coordination / dependency**: AUTH-009 forgot-password phụ thuộc TASK-062 (email infra). RBAC-008 clone: hàm clone_system_role đã có, cần expose qua route.

## Scope — function codes

### GAP (chưa có API — build mới)

| GAP | Code | Chức năng |
|---|---|---|
| GAP | AUTH-008 | Reset password (admin gen) |
| GAP | AUTH-009 | Forgot password (self-service) |
| GAP | HR-004 | Reset password (admin) |

### DRIFT (có nhưng lệch — hoàn thiện)

| DRIFT | Code | Chức năng |
|---|---|---|
| DRIFT | RBAC-008 | Clone system role |
| DRIFT | RBAC-016 | Separation of Duties (SoD) |

## Requirements

- [ ] Đọc chi tiết từng function trong `scripts/function_list_data.py` + ghi chú verified trong `api-mapping.md`
- [ ] Thiết kế endpoint/model/migration (Alembic) cho từng GAP; hoàn thiện phần lệch cho từng DRIFT
- [ ] Viết integration test real-DB (Postgres+Redis) cho mỗi endpoint; e2e cho permission gate mới
- [ ] Cập nhật `api-mapping.md`: chuyển trạng thái GAP/DRIFT → MAPPED khi xong
- [ ] Quality gates: test pass 100%, coverage new ≥80%, `ruff check` + `mypy` pass

## Acceptance Criteria

- [ ] Tất cả function code trong Scope đạt MAPPED (có endpoint + test)
- [ ] Không phá vỡ test hiện có trên `clinic-cms-merge`
- [ ] Migration chạy `alembic upgrade head` sạch; RLS giữ nguyên cô lập tenant

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Parent mapping**: `docs/tasks/TASK-052/deliveries/api-specs/api-mapping.md`
- **Code (target)**: `../clinic-cms-merge/app/modules/`
- **Tests**: `../clinic-cms-merge/tests/{unit,integration}/`
- **Deliverables**: `docs/tasks/TASK-061/deliveries/`

## Timestamps

- **Created**: 2026-05-30

## Notes

Tách từ backlog GAP của TASK-052 (2026-05-30).

## Blockers

None
