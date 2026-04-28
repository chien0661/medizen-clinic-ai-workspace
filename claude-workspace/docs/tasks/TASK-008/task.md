---
id: TASK-008
type: feature
title: Appointment + Queue (Slot Capacity + Smart Walk-in vs Appointment)
status: DONE
priority: High
assigned: chiendv
created: 2026-04-26
updated: 2026-04-29
branch: "feature/task-008-appointments"
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

- [x] Migration `t008_create_appointments.py` (revision t008, down_revision 0010)
- [x] Endpoints:
  - `GET /api/v1/appointments/slots?date=YYYY-MM-DD&duration=30` (trả slots với capacity và availability)
  - `POST /api/v1/appointments` (tạo)
  - `GET /api/v1/appointments` (list)
  - `GET /api/v1/appointments/{id}` (detail)
  - `PATCH /api/v1/appointments/{id}` (update non-status)
  - `POST /api/v1/appointments/{id}/confirm`
  - `POST /api/v1/appointments/{id}/check-in` (auto tạo Visit, copy assigned_doctor_id)
  - `POST /api/v1/appointments/{id}/cancel`
- [x] Slot capacity logic theo §5.1 BA: stub 2 doctors/slot, TODO(TASK-014) replace with real shift query
- [x] Smart queue function: pure functions `should_walk_in_jump_appointment` và `walk_in_wait_minutes`
- [x] Background job `auto_no_show_appointments` (Arq cron mỗi 5 min) đánh dấu no_show sau 15 phút
- [x] Appointment buffer config default 15 phút (configurable qua `APPOINTMENT_NO_SHOW_MINUTES`)
- [x] Indexes: `ix_appointment_clinic_time`, `ix_appointment_patient_id`, `ix_appointment_assigned_doctor`
- [x] RLS policies on appointment table
- [x] Permissions: appointment.read, appointment.write, appointment.cancel (migration t008a)

## Acceptance Criteria

- [x] AC1: 2 BS on-shift 9-12h, slot 30min → mỗi slot 9:00, 9:30, 10:00... có capacity 2 ✓
- [x] AC2: Tạo 2 appointment slot 9:00 → slot 9:00 capacity = 0, tạo cái thứ 3 trả 409 ✓
- [x] AC3: Walk-in 8:45, appointment 9:00, 25min visit → 8:45+25=9:10 > 9:00-15=8:45 → appointment ưu tiên ✓
- [x] AC4: No-show job đánh dấu đúng sau N phút quá scheduled_at ✓
- [x] AC5: Check-in tạo Visit với appointment_id link, patient_id, assigned_doctor_id, status=WAITING ✓

## Progress Checklist

- [x] Implementation
- [x] Code Review (self-review)
- [x] Testing (53 tests pass)
- [x] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/appointments/`
- **Migrations**: `clinic-cms/alembic/versions/t008_create_appointments.py`, `t008a_add_appointment_permissions.py`
- **Tests**: `clinic-cms/tests/unit/appointments/`, `clinic-cms/tests/integration/appointments/`
- **Worker**: `clinic-cms/app/workers/jobs/auto_no_show_appointments.py`

## Timestamps

- **Created**: 2026-04-26
- **Implementation Started**: 2026-04-28
- **Testing Completed**: 2026-04-29
- **Documentation Completed**: 2026-04-29
- **Done**: 2026-04-29

## Notes

- Migration revision ID is `t008` (not `0011`) to avoid conflict with parallel branches (TASK-006, TASK-009, TASK-010)
- Slot capacity uses stub of 2 doctors; TODO(TASK-014): replace with real HR shift query
- Concurrent booking test uses sequential requests due to single event-loop constraint in test env
- `appointment.visit_id` and `visit.appointment_id` form a circular FK; teardown must NULL out appointment.visit_id before deleting

## Deferrals

- **TASK-014 HR integration**: Slot capacity currently stubs 2 doctors. When TASK-014 is merged, `slot_service._get_doctors_on_shift` should query shift/leave tables.
- **Concurrent booking true test**: asyncio.gather in single event loop does not produce true concurrent DB transactions. Production multi-worker deployment enforces this via SELECT FOR UPDATE.
