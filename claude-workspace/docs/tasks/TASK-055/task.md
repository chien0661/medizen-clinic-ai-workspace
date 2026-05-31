---
id: TASK-055
type: feature
title: Subscription & clinic lifecycle (provider billing) — model + state machine + guard + admin actions + jobs
status: TODO
priority: High
assigned: Unassigned
created: 2026-05-30
updated: 2026-05-30
branch: ""
jira_key: ""
tags: [backend, subscription, platform, gap-fix, epic]
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

# TASK-055: Subscription & clinic lifecycle (provider billing) — model + state machine + guard + admin actions + jobs

## Description

Xây dựng toàn bộ module subscription (provider-side) — hiện KHÔNG tồn tại model/table/middleware nào. Bao gồm: trial/grace/state machine, SubscriptionGuard gate API, suspend/reactivate/archive đúng nghĩa (thay vì chỉ toggle is_active), renewal/convert/upgrade, subscription event audit, các cron lifecycle (expiration/grace/expired/reminder/hard-delete), và metrics MRR/ARR/churn cho dashboard super admin.

> **Parent**: TASK-052 (API mapping). Task này hiện thực một cụm GAP/DRIFT đã được xác minh source (file:line) trong `api-mapping.md`. **Tuân thủ Database Error Handling Protocol** và Testing Strategy (integration real-DB Postgres+Redis) trong CLAUDE.md/PROJECT.md.

**Coordination / dependency**: Task lớn (epic) — nên chia phase nội bộ: (1) model+state machine, (2) SubscriptionGuard middleware + read-only mode, (3) admin actions (suspend/reactivate/archive/renew/convert/upgrade) thay cho is_active toggle hiện tại, (4) Arq jobs + reminders, (5) metrics MRR/ARR/churn.

## Scope — function codes

### GAP (chưa có API — build mới)

| GAP | Code | Chức năng |
|---|---|---|
| GAP | SUB-001 | Subscription type |
| GAP | SUB-002 | Billing cycle |
| GAP | SUB-003 | Trial 14 ngày default |
| GAP | SUB-004 | Grace period |
| GAP | SUB-005 | Subscription state machine |
| GAP | SUB-006 | SubscriptionGuard middleware |
| GAP | SUB-007 | Behavior matrix per status |
| GAP | SUB-008 | Read-only mode khi expired |
| GAP | SUB-009 | Banner cảnh báo trial/grace |
| GAP | SUB-010 | Subscription event audit |
| GAP | SUB-011 | Renewal manual (super admin) |
| GAP | SUB-012 | Convert trial → paid |
| GAP | SUB-013 | Upgrade plan |
| GAP | SUB-016 | Archive clinic |
| GAP | SUB-017 | Auto export trước hard delete |
| GAP | SUB-018 | Hard delete sau 90d |
| GAP | SUB-019 | Reminder D-14/-7/-3/-1/0 |
| GAP | SUB-020 | Daily reminder trong grace |
| GAP | PLT-006 | Convert trial → paid |
| GAP | PLT-007 | Renew subscription |
| GAP | PLT-010 | Archive clinic |
| GAP | PLT-015 | Subscription expiring view |
| GAP | JOB-001 | Subscription expiration check |
| GAP | JOB-002 | Grace transition |
| GAP | JOB-003 | Expired transition |
| GAP | JOB-004 | Reminder dispatch |
| GAP | JOB-005 | Hard delete archived |

### DRIFT (có nhưng lệch — hoàn thiện)

| DRIFT | Code | Chức năng |
|---|---|---|
| DRIFT | SUB-014 | Suspend clinic |
| DRIFT | SUB-015 | Reactivate clinic |
| DRIFT | SUB-021 | Subscription metrics dashboard |
| DRIFT | PLT-008 | Suspend clinic |
| DRIFT | PLT-009 | Reactivate clinic |
| DRIFT | PLT-014 | Platform metrics dashboard |

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
- **Deliverables**: `docs/tasks/TASK-055/deliveries/`

## Timestamps

- **Created**: 2026-05-30

## Notes

Tách từ backlog GAP của TASK-052 (2026-05-30).

## Blockers

None
