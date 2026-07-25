# Review Report: TASK-117 — appointment capacity/overlap + reschedule (M-1 + M-4)

**Reviewer**: Code Review Agent
**Date**: 2026-07-25
**Branch**: `fix/TASK-117-appt-capacity-reschedule` (off origin/dev `85f70cc`)
**Worktree**: `F:/MyProject/clinic-cms-workspace/_fix117-be`
**Decision**: **APPROVED** → IN_TESTING

## Scope reviewed
`git -C _fix117-be diff origin/dev...HEAD --unified=3` — 4 files:
`appointment_service.py`, `appointment_schemas.py`, `api/routes.py`, `test_appointments_e2e.py`.

## Overlap math verdict (M-1) — CORRECT

Enforced condition (SQL `scheduled_at < slot_end AND scheduled_at >= lower_bound`, then Python `existing.start + existing.duration > new.start`) is exactly the true interval intersection `existing.start < new.end AND existing.end > new.start`. Boundary cases verified:

- **Back-to-back touching at an instant** (`existing.end == new.start`): Python test `existing.end > new.start` is `==` → False → NOT counted. Correct, no false overlap.
- **Existing starts exactly at new end** (`existing.start == slot_end`): SQL `scheduled_at < slot_end` is `==` → False → excluded. Correct.
- **Exact same time**: `existing.end = start+dur > start` True AND `start < slot_end` True → counted → 3rd booking 409. Correct.
- **Non-overlapping after earlier windows ended**: correctly returns 201.
- **`lower_bound = scheduled_at − 480min`** safely captures all candidates: any overlapping row has `existing.start > scheduled_at − existing.duration ≥ scheduled_at − 480`, so the `>= lower_bound` filter never drops a real overlap (schema caps duration at 480). Sound optimization.

FOR UPDATE preserved on the candidate select (serializes concurrent bookings); two-query lock-then-count collapsed into one locking select counted in Python — cleaner, equivalent locking.

## Reschedule verdict (M-4) — CORRECT

- `scheduled_at` added to `AppointmentUpdate` with `must_be_future` validator (tz-aware + future), mirroring `AppointmentCreate` → past/naive value = 422 at parse time (not silently dropped).
- `update_appointment` rechecks capacity via `_check_slot_capacity(..., exclude_id=a.id)` **before** applying, so self is excluded (no self-conflict) and a full target slot yields 409 with the row left untouched. New time is persisted (`a.scheduled_at = scheduled_at`). Verified against the 3 new tests.
- Combined `scheduled_at` + `duration_minutes` PATCH: capacity check uses the new duration (`new_duration`). Correct.

## Findings by severity

**CRITICAL**: none.
**MAJOR**: none.

**MINOR**:
1. `_MAX_APPOINTMENT_DURATION_MINUTES = 480` duplicates the schema `Field(le=480)` bound with no shared source of truth — documented in-code; acceptable for a stub module (`TODO(TASK-014)`). If the schema bound rises without updating this constant, longer overlaps would be missed.
2. `update_appointment` now takes `FOR UPDATE` (via `_get_appointment_for_update`) even on non-reschedule PATCHes — a single-row lock on the row being mutated; prevents lost updates and matches every other mutating path. Perf impact negligible; acceptable.
3. `slot_service._count_active_appointments_in_slot` (GET /appointments/slots) still uses start-instant-only counting (`scheduled_at >= slot_start AND < slot_end`) — see out-of-scope note below. Follow-up task recommended.
4. PATCH that changes only `duration_minutes` (extending an appointment so it newly overlaps) does not recheck capacity — pre-existing behavior, out of scope for M-1/M-4. Note for a future task.

## Out-of-scope concern: does slot_service undermine the fix? — NO

`_count_active_appointments_in_slot` is called only by `get_slots` (GET /appointments/slots), a **display/availability** endpoint, not an enforcement path. Capacity enforcement lives entirely in `_check_slot_capacity`, used by both `create_appointment` and `update_appointment`, both now correct. So the overlap-evasion hole is closed for enforcement; the slots endpoint can at worst show slightly inaccurate availability for off-grid bookings (UX, not a capacity bypass). Legitimately out of scope — the task file/line refs point only to `appointment_service.py`. Follow-up task recommended.

## Checks run
- Manual line-by-line review of all changed hunks (overlap math, boundaries, reschedule flow, schema imports — `field_validator`/`UTC`/`datetime` all present).
- Host `ruff`: unavailable (wrong-platform binary, Exec format error — matches known-broken host tooling).
- Host `mypy`: env misconfigured (61 errors across 18 files); its 4 errors in this file are at lines 321/331/346/347 (`.value` in confirm/cancel), **outside the diff and pre-existing**; no error in changed lines 63-230.
- Relied on implementation's isolated `fix117` container results: 23/23 targeted tests pass (17 pre-existing + 6 new), ruff 0, mypy 0 new. To be independently re-run by Test Agent.

## Tests
6 new tests genuinely assert the fix: overlap-can't-be-evaded (offset 5/10 min → 409), non-overlap after windows end (201), exact-same-time regression (409), reschedule persists, reschedule into full slot → 409 + untouched, past scheduled_at → 422. AAA structure, meaningful assertions with diagnostic messages.

## Quality gate
No critical/major issues. APPROVED for testing.
