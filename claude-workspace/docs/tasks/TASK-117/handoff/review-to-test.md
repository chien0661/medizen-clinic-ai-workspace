# Handoff: TASK-117 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary
M-1 overlap now uses true interval intersection (`existing.start < new.end AND existing.end > new.start`) with FOR UPDATE candidates bounded by max duration 480 and verified in Python; M-4 adds `scheduled_at` to `AppointmentUpdate` (future/tz-aware validator) and rechecks capacity with `exclude_id` on reschedule. Overlap math and boundary handling verified correct; no critical/major issues.

## Key Findings (MINOR, awareness only)
- Hardcoded `_MAX_APPOINTMENT_DURATION_MINUTES = 480` mirrors schema `le=480` (no shared source of truth).
- `update_appointment` now locks the row on every PATCH (acceptable).
- `slot_service._count_active_appointments_in_slot` (GET /slots display) still uses start-instant counting — out of scope, follow-up task; does NOT bypass enforcement.
- Duration-only PATCH doesn't recheck capacity (pre-existing, out of scope).

## Focus Areas for Testing
- **Overlap boundaries**: back-to-back appointments touching at an instant (existing.end == new.start) must be 201 (no false overlap); exact-same-time 3rd booking must be 409.
- **Capacity via overlap**: bookings offset by a few minutes within one window must hit capacity=2 → 409 (the original evasion).
- **Reschedule**: PATCH `scheduled_at` persists the new time; reschedule into a full slot → 409 and leaves the row untouched; past/naive `scheduled_at` → 422.
- **Concurrency**: re-run the concurrent-booking test to confirm the single-query FOR UPDATE still serializes.
- Re-run the full targeted suite independently (host ruff/mypy are broken — use an isolated container like the implementation did; do NOT touch the main dev/w2e stack).
