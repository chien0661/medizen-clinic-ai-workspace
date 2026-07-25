# Handoff: TASK-117 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW

## Summary

Fixed two bugs in `appointment_service` (repo `clinic-cms`, branch
`fix/TASK-117-appt-capacity-reschedule`, base `origin/dev` @ `85f70cc`, head
migration `0069`):

- **M-1**: capacity/overlap check now compares true time-window
  intersections instead of `existing.scheduled_at >= new.scheduled_at`, so
  appointments offset by a few minutes can no longer evade the capacity=2
  stub.
- **M-4**: `AppointmentUpdate` gained an optional `scheduled_at` field (was
  silently dropped before — PATCH returned 200 without changing anything,
  no validation at all); `update_appointment` now re-runs the same
  capacity/overlap check (excluding the appointment being moved) before
  applying the new time, and rejects a bad value with 422 via the schema's
  `must_be_future` validator (mirrors `AppointmentCreate`).

## Root cause (M-1)

`_check_slot_capacity` (`appointment_service.py:58-106` on `origin/dev`)
only counted existing rows where `scheduled_at >= new.scheduled_at AND
scheduled_at < new.slot_end`. An appointment that *started earlier* but was
still running when the new one begins (e.g. booked at 11:00, then 11:05,
then 11:10 — all 30-min default duration) was never counted, because its
`scheduled_at` is before the new appointment's start. So each request only
"saw" appointments starting at/after its own instant — offsetting by a few
minutes was enough to make 5 overlapping bookings all return 201.

## Fix approach

True interval overlap is `existing.start < new.end AND existing.end >
new.start`. Rewrote `_check_slot_capacity` to pull every *active* appointment
that could possibly overlap — bounded by a new `_MAX_APPOINTMENT_DURATION_MINUTES
= 480` constant matching the existing `Field(le=480)` bound on
`duration_minutes` in both schemas — then verify the exact overlap in Python
(each row's own `duration_minutes` varies, so it isn't safely expressible as
portable cross-dialect SQL arithmetic without DB-specific interval
functions). The candidate select still uses `.with_for_update()` to serialize
concurrent bookings, same as before. `func` import was dropped from
`appointment_service.py` (no longer used — the old two-query
lock-then-`func.count()` pattern collapsed into one).

`update_appointment` (M-4) now:
- Switches its appointment lookup from `_get_appointment_or_404` to the
  locking `_get_appointment_for_update` (consistent with every other
  mutating path in the file).
- If `scheduled_at` is provided: rejects tz-naive values (defense-in-depth,
  same pattern as `create_appointment`), computes the effective duration
  (new `duration_minutes` if also patched in the same call, else the
  existing one), reruns `_check_slot_capacity(..., exclude_id=a.id)`, then
  applies the new time.

## Files Changed

- `app/modules/appointments/services/appointment_service.py` — rewrote
  `_check_slot_capacity` overlap logic; `update_appointment` gained
  `scheduled_at` param + recheck; dropped now-unused `func` import.
- `app/modules/appointments/schemas/appointment_schemas.py` —
  `AppointmentUpdate.scheduled_at: datetime | None` + `must_be_future`
  validator (future + tz-aware, mirrors `AppointmentCreate`).
- `app/modules/appointments/api/routes.py` — PATCH route now passes
  `payload.scheduled_at` through to the service call.
- `tests/integration/appointments/test_appointments_e2e.py` — added
  `TestOverlapCapacityWindow` (3 tests) and `TestRescheduleScheduledAt`
  (3 tests).

## Test Results

Isolated Docker stack `fix117` (api 9956 / postgres 5456 / redis 6438),
built from this worktree, migrated to head (0069), torn down after (containers
+ volumes + image removed). Main `dev`/`w2e` stack (9999/5434/5436/6380/6382)
was left running and untouched throughout.

- Targeted: `tests/integration/appointments/test_appointments_e2e.py` —
  **23/23 passed** (17 pre-existing + 6 new: 3 overlap-window + 3 reschedule).
  Did not run the whole repo suite per instructions (targeted only).
  - New M-1 tests: overlapping bookings offset by 5/10 min hit capacity ->
    409; non-overlapping booking after earlier windows have ended -> 201;
    exact-same-time collision (pre-existing behavior) still -> 409.
  - New M-4 tests: PATCH `scheduled_at` actually persists the new time;
    rescheduling into an already-full slot rechecks capacity -> 409 and
    leaves the appointment untouched; PATCH with a past `scheduled_at` ->
    422 (not silently dropped).
- `ruff check app/modules/appointments tests/integration/appointments/test_appointments_e2e.py`
  (run inside the `fix117` API container): **0 issues**.
- `mypy app/modules/appointments` (same container): 1 error, at
  `routes.py:131` (`rows` variable reused across a `Patient` query then a
  `User` query — type-narrowing complaint). Confirmed pre-existing:
  identical code on `origin/dev` (`git show origin/dev:app/modules/appointments/api/routes.py`),
  unrelated to any line touched by this fix — **0 new mypy errors**.

## Areas for Review Focus

- `_MAX_APPOINTMENT_DURATION_MINUTES = 480` is a hardcoded mirror of the
  `Field(le=480)` bound in both `AppointmentCreate`/`AppointmentUpdate` — if
  that schema bound ever changes, this constant must be updated too (no
  single source of truth currently link them). Flagging for reviewer
  judgment on whether that's acceptable for a stub module already marked
  `TODO(TASK-014)`.
- `update_appointment` now locks the appointment row via
  `_get_appointment_for_update` instead of the non-locking
  `_get_appointment_or_404` used before — intentional (needed for a safe
  reschedule recheck) but is a behavior change worth a second look for lock
  contention on plain (non-reschedule) PATCHes (assigned_doctor_id /
  duration_minutes only).
- `slot_service._count_active_appointments_in_slot` (used by `GET
  /appointments/slots`) has the same start-instant-only overlap bug as the
  old `_check_slot_capacity`, but it's a separate function/endpoint not
  named in the task's file/line references — left untouched. Worth a
  follow-up task if the slot-listing display should also reflect true
  overlap.
