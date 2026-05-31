---
id: TASK-063
type: feature
title: Clinic config & platform-admin completeness — settings (holiday/lunch/prefixes/timezone/language) + platform role CRUD/clinic detail/system config/notes/activity feed
status: TODO
priority: Low
assigned: Unassigned
created: 2026-05-30
updated: 2026-05-30
branch: ""
jira_key: ""
tags: [backend, config, platform, gap-fix]
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

# TASK-063: Clinic config & platform-admin completeness — settings (holiday/lunch/prefixes/timezone/language) + platform role CRUD/clinic detail/system config/notes/activity feed

## Description

Hoàn thiện cấu hình phòng khám + platform admin còn lẻ: holiday list (auto-import VN), lunch break, patient/visit prefix, timezone & default language per-clinic (hiện chỉ system default), VN address API; phía platform: platform role CRUD (hiện read-only), clinic detail endpoint (hiện chỉ list), system config, internal notes, activity feed, feature-flag UI (hiện chỉ bhyt per-clinic, SuperClinicUpdate chưa expose).

> **Parent**: TASK-052 (API mapping). Task này hiện thực một cụm GAP/DRIFT đã được xác minh source (file:line) trong `api-mapping.md`. **Tuân thủ Database Error Handling Protocol** và Testing Strategy (integration real-DB Postgres+Redis) trong CLAUDE.md/PROJECT.md.

**Coordination / dependency**: Nhiều mục nhỏ, độ rủi ro thấp. CFG-011/012 hiện chỉ có system default, chưa cho cấu hình per-clinic.

## Scope — function codes

### GAP (chưa có API — build mới)

| GAP | Code | Chức năng |
|---|---|---|
| GAP | CFG-004 | Holiday list |
| GAP | CFG-005 | Lunch break |
| GAP | CFG-007 | Patient code prefix |
| GAP | CFG-008 | Visit number prefix |
| GAP | TENT-007 | Cấu hình prefix code |
| GAP | PLT-002 | Platform role CRUD |
| GAP | PLT-004 | Clinic detail panel |
| GAP | PLT-017 | System config |
| GAP | PLT-022 | Internal notes |
| GAP | PLT-023 | Activity feed platform-wide |
| GAP | INT-013 | VN address API |

### DRIFT (có nhưng lệch — hoàn thiện)

| DRIFT | Code | Chức năng |
|---|---|---|
| DRIFT | CFG-011 | Timezone |
| DRIFT | CFG-012 | Default language |
| DRIFT | PLT-018 | Feature flag UI |

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
- **Deliverables**: `docs/tasks/TASK-063/deliveries/`

## Timestamps

- **Created**: 2026-05-30

## Notes

Tách từ backlog GAP của TASK-052 (2026-05-30).

## Blockers

None
