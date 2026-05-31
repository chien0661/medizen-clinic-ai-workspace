---
id: TASK-059
type: feature
title: Appointments completeness + HR shift integration — reschedule, block schedule, HR conflict, smart queue, real slot capacity, no-show grace
status: TODO
priority: Medium
assigned: Unassigned
created: 2026-05-30
updated: 2026-05-30
branch: ""
jira_key: ""
tags: [backend, appointments, hr, gap-fix]
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

# TASK-059: Appointments completeness + HR shift integration — reschedule, block schedule, HR conflict, smart queue, real slot capacity, no-show grace

## Description

Hoàn thiện module lịch hẹn: APPT-006 reschedule (hiện PATCH không đổi được scheduled_at), APPT-009 smart queue priority (code dead, chưa nối route), APPT-016 block schedule cho bác sĩ, APPT-017 validate trùng ca/nghỉ HR, APPT-002 slot capacity thật theo HR shift (hiện hardcode = 2), APPT-008 chỉnh grace no-show 15→30 phút theo spec.

> **Parent**: TASK-052 (API mapping). Task này hiện thực một cụm GAP/DRIFT đã được xác minh source (file:line) trong `api-mapping.md`. **Tuân thủ Database Error Handling Protocol** và Testing Strategy (integration real-DB Postgres+Redis) trong CLAUDE.md/PROJECT.md.

**Coordination / dependency**: Gỡ stub HR shift (slot_service.py _STUB_DOCTORS_ON_SHIFT=2, TODO TASK-014). smart_queue.py đã có code, chỉ cần nối route.

## Scope — function codes

### GAP (chưa có API — build mới)

| GAP | Code | Chức năng |
|---|---|---|
| GAP | APPT-006 | Reschedule |
| GAP | APPT-009 | Smart queue priority |
| GAP | APPT-016 | Block schedule |
| GAP | APPT-017 | Conflict với HR shift |

### DRIFT (có nhưng lệch — hoàn thiện)

| DRIFT | Code | Chức năng |
|---|---|---|
| DRIFT | APPT-002 | Slot capacity per doctor |
| DRIFT | APPT-008 | NO_SHOW tracking |

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
- **Deliverables**: `docs/tasks/TASK-059/deliveries/`

## Timestamps

- **Created**: 2026-05-30

## Notes

Tách từ backlog GAP của TASK-052 (2026-05-30).

## Blockers

None
