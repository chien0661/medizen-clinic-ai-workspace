---
id: TASK-057
type: feature
title: Self-signup & lead funnel — public signup form, email verify, lead management, convert lead→clinic, atomic clinic+admin
status: TODO
priority: High
assigned: Unassigned
created: 2026-05-30
updated: 2026-05-30
branch: ""
jira_key: ""
tags: [backend, tenant, signup, gap-fix]
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

# TASK-057: Self-signup & lead funnel — public signup form, email verify, lead management, convert lead→clinic, atomic clinic+admin

## Description

Xây luồng đăng ký phòng khám tự phục vụ (public) + lead funnel: form self-signup, email verification (token TTL 24h, single-use, resend), tạo clinic+admin ATOMIC (hiện chưa atomic — admin user tạo ở bước onboarding riêng), clone roles cho clinic mới (clone_system_role hiện là dead code), prefix config khi provisioning, lead management + convert lead→clinic cho super admin, reCAPTCHA + ToS/Privacy versioning. Sửa TENT-006: thêm preset TCM (hiện chỉ có general/pediatric/ob_gyn/dermatology/dental).

> **Parent**: TASK-052 (API mapping). Task này hiện thực một cụm GAP/DRIFT đã được xác minh source (file:line) trong `api-mapping.md`. **Tuân thủ Database Error Handling Protocol** và Testing Strategy (integration real-DB Postgres+Redis) trong CLAUDE.md/PROJECT.md.

**Coordination / dependency**: Phụ thuộc TASK-062 (email infra) cho email verification + invite resend. ToS versioning (AUDIT-011) gắn với bước đồng ý khi signup.

## Scope — function codes

### GAP (chưa có API — build mới)

| GAP | Code | Chức năng |
|---|---|---|
| GAP | TENT-001 | Self-signup form |
| GAP | TENT-002 | Email verification |
| GAP | TENT-008 | Lead form (Liên hệ tư vấn) |
| GAP | TENT-010 | Convert lead → clinic |
| GAP | TENT-011 | Email verify token TTL 24h |
| GAP | TENT-012 | Invite resend |
| GAP | TENT-014 | reCAPTCHA on signup |
| GAP | PLT-012 | Lead management |
| GAP | PLT-013 | Convert lead → clinic |
| GAP | AUDIT-011 | ToS + Privacy versioning |

### DRIFT (có nhưng lệch — hoàn thiện)

| DRIFT | Code | Chức năng |
|---|---|---|
| DRIFT | TENT-003 | Tạo clinic + admin user |
| DRIFT | TENT-004 | Clone system roles cho clinic mới |
| DRIFT | TENT-006 | Chọn vital preset |

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
- **Deliverables**: `docs/tasks/TASK-057/deliveries/`

## Timestamps

- **Created**: 2026-05-30

## Notes

Tách từ backlog GAP của TASK-052 (2026-05-30).

## Blockers

None
