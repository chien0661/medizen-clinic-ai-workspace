---
id: TASK-022
type: feature
title: FE — HR (Shift Calendar + Recurring Schedule + Leave Request + Attendance Check-in/out)
status: TODO
priority: Medium
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [frontend, hr, schedule, attendance, sprint-16]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#14-module-hr--schedule"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#12-module-hr-schedule--attendance"
---

# TASK-022: FE — HR Module (Schedule + Attendance + Leave)

## Description

UI cho admin: shift schedule calendar (week/month view), recurring schedule editor, leave request flow (submit + approve), attendance check-in/out widget với multi-method (manual/PIN/QR/biometric), personal time log, export Excel chấm công.

## Requirements

- [ ] **Shift calendar** (`/hr/schedule`)
  - View: week / month toggle
  - Cell: list shifts per day per user (color theo role)
  - Drag & drop to reschedule (admin perm `shift.manage`)
  - Click cell → detail/edit shift modal
  - Filter by user/role
- [ ] **Recurring schedule editor** (`/hr/recurring`)
  - List: user, shift_template, days_of_week, effective_from, effective_to
  - Form: chọn user, template, multi-select days (T2-CN), date range
  - "Generate shifts now" button → trigger background job (TASK-014)
- [ ] **Shift template manager** (`/hr/shift-templates`, admin)
  - CRUD: name (Ca sáng), start_time, end_time, is_active
- [ ] **Leave request flow**
  - User submit (`/hr/leave/new`): leave_type (sick/personal/vacation/other), start_date, end_date, reason
  - Manager approve list (`/hr/leave/approve`, perm `leave.approve`)
  - Approve/Reject với comment
  - On approve → shift trong khoảng đó hiển thị badge "On leave"
- [ ] **Attendance check-in/out widget** (gắn vào dashboard)
  - Show current shift (nếu có)
  - Big button "Check-in" / "Check-out"
  - Method: manual click | PIN input | QR scan (Tauri camera) | biometric (phase sau, hardware)
  - Hiển thị time: late_minutes (nếu có), ot_hours sau check-out
- [ ] **Personal time log** (`/hr/me/timelog`)
  - Calendar view tháng hiện tại
  - Cell: shift dự kiến vs check_in/out thực tế
  - Stats footer: total hours, late count, OT hours
- [ ] **Attendance export** (admin)
  - Form: date range, user(s) multi-select
  - Format: xlsx | csv
  - Output columns: user, date, shift, check_in, check_out, total_hours, late_min, ot_hours
- [ ] Permissions: `shift.manage`, `attendance.manage`, `leave.approve`

## Acceptance Criteria

- [ ] Drag shift từ T2 sang T3 → API call PATCH, calendar refresh
- [ ] Tạo recurring (T2/T4/T6, ca sáng, từ 5/2026) → click Generate → calendar tháng 5 có đủ shift
- [ ] Submit leave → status pending → admin thấy ở approve list
- [ ] Approve leave 5/10-5/12 → shift trong 3 ngày đó có badge "Nghỉ phép"
- [ ] Check-in lúc 7:45 cho shift 7:30 → widget hiện "Trễ 15 phút"
- [ ] Check-out lúc 12:30 (shift end 12:00) → "OT 0:30"
- [ ] Export Excel cả tháng cho 10 user → file download trong < 5s
- [ ] User check-in trùng shift đã có TimeLog active → toast error "Đã check-in"

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/desktop/src/modules/hr/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Calendar dùng FullCalendar React hoặc react-big-calendar. QR scan dùng Tauri camera plugin (phase sau nếu phức tạp, v1 để manual + PIN).

## Blockers

- TASK-017, TASK-014 (HR API)
