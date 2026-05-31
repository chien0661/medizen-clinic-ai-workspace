---
id: TASK-062
type: feature
title: Email infra & event-driven notifications — email provider + transactional/templates + visit-complete/stock-low/sub-expiring notify
status: IN_PROGRESS
priority: Medium
assigned: chiendv
created: 2026-05-30
updated: 2026-05-30
branch: "fix/TASK-052-test-encryption-fixtures"
jira_key: ""
tags: [backend, integration, notifications, email, gap-fix]
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

# TASK-062: Email infra & event-driven notifications — email provider + transactional/templates + visit-complete/stock-low/sub-expiring notify

## Description

Wire email provider (SES/SendGrid — INT-001) + email transactional/templates vi-en (NOTI-008/009), và bổ sung notification event-driven còn thiếu: NOTI-005 thông báo khi visit hoàn tất (hiện KHÔNG tạo notification dù enum VISIT_QUEUE_ALERT đã định nghĩa), NOTI-006 stock-low theo sự kiện ngưỡng + target đúng dược sĩ (hiện chỉ cron broadcast mỗi giờ), NOTI-007 subscription expiring, PLT-024 email team super admin.

> **Parent**: TASK-052 (API mapping). Task này hiện thực một cụm GAP/DRIFT đã được xác minh source (file:line) trong `api-mapping.md`. **Tuân thủ Database Error Handling Protocol** và Testing Strategy (integration real-DB Postgres+Redis) trong CLAUDE.md/PROJECT.md.

**Coordination / dependency**: Nền tảng cho TASK-057 (signup verify), TASK-061 (forgot pw), TASK-055 (subscription reminders). Làm sớm.

## Scope — function codes

### GAP (chưa có API — build mới)

| GAP | Code | Chức năng |
|---|---|---|
| GAP | INT-001 | Email provider |
| GAP | NOTI-005 | Visit completion notify |
| GAP | NOTI-007 | Subscription expiring |
| GAP | NOTI-008 | Email transactional |
| GAP | NOTI-009 | Email templates |
| GAP | PLT-024 | Email super admin team |

### DRIFT (có nhưng lệch — hoàn thiện)

| DRIFT | Code | Chức năng |
|---|---|---|
| DRIFT | NOTI-006 | Stock low alert |

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
  - [x] **Increment 1 (2026-05-30)** — Email infra (INT-001) + templates vi/en (NOTI-009) + transactional send (NOTI-008) + visit-completion notify (NOTI-005). 18 new unit tests pass.
  - [x] **Increment 2 (2026-05-31)** — NOTI-006 stock-low event-driven (DRIFT→MAPPED): `stock_alert_service` wired into dispense + adjustment. 5 unit tests + 23 real-DB pharmacy/inventory integration tests pass, ruff clean.
  - [ ] PLT-024 recipient resolution (mechanism done; wire platform-admin emails when superadmin lands)
  - [ ] NOTI-007 subscription-expiring trigger — BLOCKED by TASK-055 (subscription module)
  - **5/7 MAPPED**; PLT-024 partial; NOTI-007 blocked. Core (email infra + event-driven notify) complete + tested.
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Parent mapping**: `docs/tasks/TASK-052/deliveries/api-specs/api-mapping.md`
- **Code (target)**: `../clinic-cms-merge/app/modules/`
- **Tests**: `../clinic-cms-merge/tests/{unit,integration}/`
- **Deliverables**: `docs/tasks/TASK-062/deliveries/`

## Timestamps

- **Created**: 2026-05-30

## Notes

Tách từ backlog GAP của TASK-052 (2026-05-30).

## Blockers

None
