---
id: TASK-014
type: feature
title: HR — Shift + Recurring Schedule + Attendance + Leave Request
status: DONE
priority: Medium
assigned: ""
created: 2026-04-26
updated: 2026-04-28
completed: 2026-04-28
branch: feature/task-014-hr-schedule
tags: [hr, schedule, attendance, sprint-12]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#14-module-hr--schedule"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#12-module-hr-schedule--attendance"
---

# TASK-014: HR — Shift + Recurring Schedule + Attendance + Leave Request

## Description

Tách 2 khái niệm: Schedule (kế hoạch — input cho appointment capacity) và Attendance (thực tế — input cho lương). Shift template, recurring schedule auto-generate Shift, Leave request approve flow, TimeLog với multi-method (manual/pin/qr/biometric). Lương export Excel.

## Requirements

- [ ] Migration `0011_create_hr_schedule.py` (shift_template + shift + recurring_schedule + leave_request + time_log)
- [ ] Endpoints:
  - CRUD `/api/v1/shift-templates`
  - CRUD `/api/v1/shifts`
  - CRUD `/api/v1/recurring-schedules`
  - `POST /api/v1/leave-requests`, `POST /api/v1/leave-requests/{id}/approve|reject`
  - `POST /api/v1/attendance/check-in`, `POST /api/v1/attendance/check-out`
  - `GET /api/v1/attendance/me` (xem time log của bản thân)
  - `GET /api/v1/attendance/export?from=...&to=...&format=xlsx`
- [ ] Background job `generate_recurring_shifts` (cron daily) sinh Shift từ recurring_schedule cho 30 ngày tới
- [ ] Khi LeaveRequest approved → cancel/mark on_leave các Shift trong khoảng đó
- [ ] Compute fields: total_hours, late_minutes, early_leave, ot_hours
- [ ] Indexes: `ix_shift_clinic_date_user`, `ix_leave_user_dates` (status approved)
- [ ] UNIQUE (clinic_id, user_id, shift_date, start_time) cho shift

## Acceptance Criteria

- [ ] Recurring schedule (BS X, T2-T4-T6, ca sáng, từ 2026-05-01) → cron sinh đủ shift cho tháng 5
- [ ] LeaveRequest approved 2026-05-10 → 2026-05-12 → shift trong khoảng đó status=`on_leave`
- [ ] Check-in lúc 7:45 cho shift 7:30 → late_minutes = 15
- [ ] Check-out lúc 12:30 cho shift end 12:00 → ot_hours = 0.5
- [ ] Export Excel cả tháng cho 10 nhân viên < 5s
- [ ] User check-in trùng shift đã có TimeLog active → 409

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/hr/`

## Timestamps

- **Created**: 2026-04-26
- **Started**: 2026-04-28
- **Implementation Completed**: 2026-04-28
- **Review Round 1 Completed**: 2026-04-28 (CHANGES_REQUESTED — 0 Critical, 2 Major, 6 Minor)
- **Fix Iteration 1 Completed**: 2026-04-28
- **Review Round 2 Completed**: 2026-04-28 (APPROVED — 8/8 findings FIXED, 35/35 HR tests pass)
- **Testing Round 1**: 2026-04-27 (FAIL — 9 failures in 64 new tests, 4 bugs: BUG-001 through BUG-004)
- **Fix Iteration 2 Completed**: 2026-04-28
- **Testing Completed**: 2026-04-28 (PASS — 95/95, all 4 bugs resolved in commit cc5c539)
- **Documentation Completed**: 2026-04-28

## Notes

V1 không tính lương trong app — chỉ export. Commission BS phase sau. Biometric/QR check-in cần hardware → Tauri client TASK-016.

## Blockers

- TASK-004 (User)
