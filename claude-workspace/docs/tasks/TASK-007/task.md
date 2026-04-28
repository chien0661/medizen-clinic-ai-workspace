---
id: TASK-007
type: feature
title: Visit — Entity + State Machine + Visit Number Generation
status: IN_REVIEW
priority: High
assigned: code-review-agent
created: 2026-04-26
updated: 2026-04-27
branch: "feature/task-007-visits"
iteration: 1
tags: [visit, sprint-4]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#8-module-visits"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#6-module-visit"
---

# TASK-007: Visit — Entity + State Machine + Visit Number Generation

## Description

Visit là entity trung tâm kết nối Patient-Appointment-Doctor-Vitals-Service-Prescription-Invoice. State machine: WAITING → IN_PROGRESS → AWAITING_PAYMENT → COMPLETED (+ CANCELLED ở mọi state trừ COMPLETED). Sinh visit_number `YYYYMMDD-NNN` reset hàng ngày per clinic.

## Requirements

- [ ] Migration `0005_create_visits.py` (visit table)
- [ ] Helper `fn_next_visit_number(clinic_id, date)` dùng PostgreSQL sequence per (clinic, date)
- [ ] Endpoints: CRUD + actions
  - `POST /api/v1/visits` (tạo walk-in)
  - `POST /api/v1/visits/{id}/start` (BS nhận ca: WAITING → IN_PROGRESS, set doctor_id = current user)
  - `POST /api/v1/visits/{id}/complete` (BS hoàn tất: IN_PROGRESS → AWAITING_PAYMENT)
  - `POST /api/v1/visits/{id}/cancel` (kèm reason)
  - `POST /api/v1/visits/call-next` (BS gọi visit tiếp theo theo priority logic)
- [ ] State machine enforcement: chỉ allow transition hợp lệ, return 409 nếu invalid
- [ ] Call-next logic: ưu tiên visit có `assigned_doctor_id = current_user`, sau đó null, sau cùng assigned người khác
- [ ] Indexes: `ix_visit_clinic_status_priority` cho queue query
- [ ] View `v_active_queue` SQL theo §14 BA

## Acceptance Criteria

- [ ] Visit number unique trong (clinic, date), format `20260426-001`
- [ ] State transition: WAITING → COMPLETED trực tiếp bị reject (409)
- [ ] COMPLETED không revert được
- [ ] CANCELLED ở COMPLETED bị reject
- [ ] Call-next với 2 BS đồng thời không gây race condition (test với SELECT FOR UPDATE)
- [ ] Performance: query queue 50 visit < 50ms

## Progress Checklist

- [x] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/visits/`

## Timestamps

- **Created**: 2026-04-26
- **Started**: 2026-04-27
- **Implementation Completed**: 2026-04-27

## Notes

Sửa sai sau COMPLETED phải void invoice + tạo entry điều chỉnh, không revert visit state.

## Blockers

- TASK-005
