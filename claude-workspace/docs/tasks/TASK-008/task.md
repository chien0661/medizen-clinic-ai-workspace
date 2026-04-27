---
id: TASK-008
type: feature
title: Appointment + Queue (Slot Capacity + Smart Walk-in vs Appointment)
status: TODO
priority: High
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [appointment, queue, sprint-5]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#7-module-appointments--queue"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#5-module-appointment"
---

# TASK-008: Appointment + Queue (Slot Capacity + Smart Walk-in vs Appointment)

## Description

Appointment với capacity-based slots (capacity = số bác sĩ on-shift), bệnh nhân không chọn bác sĩ, optional pre-assign. State machine: scheduled → confirmed → checked_in → completed + cancelled/no_show. Smart queue: walk-in chỉ chèn trước appointment nếu (estimated_end_walkin < appointment_time - buffer).

## Requirements

- [ ] Migration `0004_create_appointments.py`
- [ ] Endpoints:
  - `GET /api/v1/appointments/slots?date=YYYY-MM-DD&duration=30` (trả slots với capacity và availability)
  - `POST /api/v1/appointments` (tạo)
  - `POST /api/v1/appointments/{id}/confirm`
  - `POST /api/v1/appointments/{id}/check-in` (auto tạo Visit, copy assigned_doctor_id)
  - `POST /api/v1/appointments/{id}/cancel`
- [ ] Slot capacity logic theo §5.1 BA: count doctors on-shift - count appointments active
- [ ] Smart queue function: cho walk-in vào trước appointment nếu thoả điều kiện buffer
- [ ] Background job `auto_no_show_appointments` (Arq cron mỗi 5 min) đánh dấu no_show sau `appointment_no_show_minutes`
- [ ] Appointment buffer config từ clinic settings (`appointment.buffer_minutes`, default 15)
- [ ] Indexes: `ix_appointment_clinic_time` (status IN scheduled/confirmed/checked_in)

## Acceptance Criteria

- [ ] 2 BS on-shift 9-12h, slot 30min → mỗi slot 9:00, 9:30, 10:00... có capacity 2
- [ ] Tạo 2 appointment slot 9:00 → slot 9:00 capacity = 0, tạo cái thứ 3 trả 409
- [ ] Walk-in lúc 8:30, appointment 9:00, BS rảnh 8:45, visit walk-in dự kiến 25min → walk-in được vào (8:45 + 25 = 9:10 > 9:00 - 15 = 8:45 ❌). Fix logic: 9:10 > 8:45 → appointment ưu tiên ✓
- [ ] No-show job đánh dấu đúng sau N phút quá scheduled_at
- [ ] Check-in tạo Visit với appointment_id link

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/appointments/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Capacity check phải account cho leave (LeaveRequest approved → BS off shift). Có thể cần JOIN với shift + leave.

## Blockers

- TASK-007, TASK-014 (cần shift/leave để tính capacity — có thể stub trước)
