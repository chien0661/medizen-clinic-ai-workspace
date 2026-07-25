---
id: TASK-117
type: bug
title: "[Medium] Lịch hẹn: capacity/overlap bị né (M-1) + không đổi được giờ,
  PATCH scheduled_at bị drop (M-4)"
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-25
updated: 2026-07-25
branch: fix/TASK-117-appt-capacity-reschedule
tags:
  - appointments
  - business-logic
  - medium
  - e2e-finding
affected-repos:
  - clinic-cms
refs:
  other:
    - docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md
      (M-1, M-4)
---

# TASK-117: [Medium] Appointment capacity/overlap + reschedule (M-1 + M-4)

**Nguồn:** E2E TASK-095, M-1 + M-4 (cùng `appointment_service` → gộp).

## M-1 — Capacity/overlap bị né bằng lệch giờ vài giây
- Với stub capacity=2, 5 lịch chồng thời gian (lệch 5') đều 201. Chỉ đếm row có `scheduled_at >= new.scheduled_at` → lệch giờ đủ né. Cùng giờ chính xác thì 409 đúng.
- Fix: kiểm overlap theo **khoảng thời gian** (scheduled_at + duration) thay vì mốc bằng nhau.
- File: `app/modules/appointments/services/appointment_service.py:58-106`.

## M-4 — PATCH scheduled_at bị drop âm thầm (không đổi được giờ)
- PATCH `scheduled_at` mới → 200 nhưng giá trị không đổi; field không có trong `AppointmentUpdate` → drop im lặng (không 422).
- Fix: thêm `scheduled_at` vào `AppointmentUpdate`; reschedule recheck capacity/overlap.
- File: `app/modules/appointments/schemas/appointment_schemas.py:28-30`, `appointment_service.py:176-194`.

## Acceptance Criteria
- [x] Overlap/capacity kiểm theo khoảng thời gian → lịch chồng vượt capacity bị 409 (không né được bằng lệch vài giây).
- [x] PATCH scheduled_at đổi được giờ (recheck capacity) hoặc trả 422 nếu không hợp lệ (không drop im lặng).
- [x] Integration test cả M-1 (chồng giờ) + M-4 (reschedule).

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

Documentation Completed: 2026-07-25
- Final spec: `docs/tasks/TASK-117/deliveries/final-specs/appointment-capacity-reschedule-fix.md`

## Testing Completed (2026-07-25)
95/95 passed (`tests/integration/appointments` + `tests/integration/visits`)
on isolated stack `x117` (api 9953 / pg 5453 / redis 6435), migrated to head
0069, torn down after run. Confirmed: overlapping appts offset by minutes
within capacity=2 -> 3rd is 409 (can't evade via few-minute offset);
non-overlapping booking after window ends -> 201; exact-same-time -> 409;
PATCH scheduled_at actually persists the new time; reschedule into an
already-full slot rechecks capacity -> 409 (original untouched); PATCH
scheduled_at to a past date -> 422 (not silently dropped). See
`docs/tasks/TASK-117/deliveries/test-reports/test-report.md`.

## Blockers
Không. (M-3 capacity theo ca trực HR tách riêng — cần tích hợp HR/TASK-014.)
