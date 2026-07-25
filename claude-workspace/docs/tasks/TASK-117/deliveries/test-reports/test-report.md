# Test Report: TASK-117 - Appointment capacity/overlap + reschedule (M-1/M-4)

**Test Agent:** Automation Tester
**Date:** 2026-07-25
**Status:** ALL IN-SCOPE PASSED

## Environment

- Isolated Docker stack `x117` (project `-p x117`), built from worktree
  `F:/MyProject/clinic-cms-workspace/_fix117-be`, branch
  `fix/TASK-117-appt-capacity-reschedule` @ `1e58607`.
- Ports: api `9953`, postgres `5453`, redis `6435` (new
  `docker/docker-compose.fix117.yml` scaffolded for this run — infra file
  only, no source touched). No collision with main/dev/w2e.
- Migrated `alembic upgrade head` -> reached **0069** (single head confirmed
  via `alembic heads`), clean run.
- Seeded superadmin + full demo dataset.
- Stack torn down (`docker compose -p x117 -f docker-compose.fix117.yml down -v`)
  after the run; `docker ps -a --filter name=x117` confirmed empty.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Integration (`tests/integration/appointments` + `tests/integration/visits`) | 95 | 95 | 0 | 100% |

Command: `pytest -q --tb=short tests/integration/appointments tests/integration/visits`

## Key Assertions Verified

- **`TestOverlapCapacityWindow::test_overlapping_appointments_offset_by_minutes_hit_capacity`**
  — PASSED. Capacity=2: two bookings offset by 5 min (windows intersect via
  default 30-min duration) succeed (201, 201); a 3rd offset by 10 min (still
  overlapping) -> **409**. Directly proves capacity/overlap is checked as a
  time-window intersection, not exact-instant equality — cannot be evaded
  with a small time offset.
- **`test_non_overlapping_booking_after_capacity_reached_still_201`** —
  PASSED. Once earlier windows have fully ended, a new non-overlapping
  booking is still accepted (201) — confirms the fix isn't over-broad.
- **`test_exact_same_time_still_409`** — PASSED. Regression: exact-same-
  instant collision (capacity=2, 3rd request) still 409 after the overlap
  rewrite.
- **`TestRescheduleScheduledAt::test_patch_scheduled_at_actually_moves_the_appointment`**
  — PASSED. `PATCH .../{id}` with a new `scheduled_at` returns 200 with the
  changed value, and a follow-up `GET` confirms it persisted (was previously
  silently dropped).
- **`test_reschedule_into_full_slot_rechecks_capacity_409`** — PASSED. Fill a
  slot to capacity=2, then `PATCH` an unrelated appointment's `scheduled_at`
  into that full slot -> **409**; follow-up `GET` confirms the appointment
  stayed untouched at its original time (reschedule recheck confirmed, not
  a rollback bug).
- **`test_patch_scheduled_at_in_the_past_is_422_not_silently_dropped`** —
  PASSED. `PATCH scheduled_at` to a past date -> **422** (not silently
  ignored/200'd).
- **No regression**: `TestSlotCapacity` (`test_ac1_slots_capacity_2`,
  `test_ac2_third_booking_409`), `test_sequential_capacity_enforcement`,
  double-confirm/checkin-without-confirm 409 baselines, and the full
  `tests/integration/visits` suite (lifecycle/concurrency/RLS/edit-lock) all
  green.

## Failures

None. 95/95 passed.

## Next Steps

All in-scope tests passed. Ready to proceed to Documentation phase.

**Task status -> DOCUMENTING**

---

**Total Scenarios:** 95
**Environment:** isolated Docker stack `x117` (api 9953 / pg 5453 / redis 6435), torn down after run
