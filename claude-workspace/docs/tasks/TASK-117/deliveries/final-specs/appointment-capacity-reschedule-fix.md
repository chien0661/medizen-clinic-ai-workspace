# TASK-117: Appointment Capacity/Overlap + Reschedule Fix

## Issue M-1: Capacity/Overlap Could Be Evaded by Small Time Offsets
With capacity=2, 5 overlapping appointments (offset 5 minutes apart) all received 201 OK instead of the 3rd+ being rejected with 409.

**Root cause**: Overlap check only compared exact `scheduled_at` timestamps (binary: equal or not), missing true time-window collisions.

## Issue M-4: PATCH scheduled_at Silently Dropped
Rescheduling with `PATCH /appointments/{id}` and `scheduled_at` field would return 200 but the time never changed.

**Root cause**: 
- `scheduled_at` not in `AppointmentUpdate` schema → silently ignored
- No capacity/overlap recheck on reschedule

## Fixes Applied

### M-1: Time-Window Overlap Check
Changed overlap detection from point-comparison to interval overlap:
- Check: `appointment.scheduled_at` + `duration` intersects with new booking window
- Example: 09:00–09:30 and 09:25–09:55 now correctly detected as overlapping (violates capacity)

### M-4: Reschedule with Capacity Recheck
- Added `scheduled_at` to `AppointmentUpdate` schema
- On reschedule: recheck capacity/overlap for the new time slot
- Invalid dates (past) rejected with 422, not silently dropped

### Files Changed
- `app/modules/appointments/services/appointment_service.py` (lines 58–106, 176–194)
- `app/modules/appointments/schemas/appointment_schemas.py` (lines 28–30)

## Verification
- **Integration Tests**: 95/95 passed on isolated stack `x117`
- **Key scenarios confirmed**:
  - Overlapping bookings within capacity=2 → 3rd is 409 ✓
  - Non-overlapping booking after window ends → 201 ✓
  - Exact same time → 409 (regression prevented) ✓
  - `PATCH scheduled_at` persists new time ✓
  - Reschedule into full slot rechecks capacity → 409 (original untouched) ✓
  - Past-date PATCH → 422 (not silently dropped) ✓

## Result
Appointments can no longer evade capacity checks via small time offsets. Rescheduling fully works with capacity validation.

## Follow-up Items
- **M-3** (HR capacity per shift): Requires HR/TASK-014 integration — separate task
- **Slot service display**: Consider exposing available time slots per service/resource (future UX enhancement)
