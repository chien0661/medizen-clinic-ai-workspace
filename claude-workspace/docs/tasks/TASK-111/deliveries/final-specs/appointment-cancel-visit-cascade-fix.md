# TASK-111: Appointment Cancel Visit Cascade Fix

**Status:** DONE  
**Severity:** Medium (M-2, E2E finding TASK-095)  
**Affected Systems:** Appointments, Visits  
**Repos:** clinic-cms  

---

## Bug Summary

When cancelling an appointment that had been checked in (resulting in a linked Visit), the appointment transitioned to `cancelled`, but the Visit remained orphaned in `WAITING` state forever. The appointment cancel operation did not cascade to the related Visit.

**Repro:**
1. Create appointment → confirm → check-in (Visit created in WAITING state)
2. Cancel the appointment → returns HTTP 200, appointment → cancelled
3. Fetch the Visit → still WAITING (orphaned, never served)

---

## Root Cause

`cancel_appointment` (`app/modules/appointments/services/appointment_service.py`, lines 252-266) transitioned the appointment state but never invoked any logic to handle the linked Visit record.

---

## Fix Design

**Strategy: Cascade, not blanket block.**

When cancelling an appointment with a linked Visit in a non-terminal state (`WAITING`, `IN_PROGRESS`, `AWAITING_PAYMENT`):

1. Call the existing `visit_service.transition_to_cancel(db, visit_id, clinic_id, reason, user_id)` — same path as a direct visit cancel.
2. That helper enforces its own guard rails:
   - If money has been collected on an invoice → `BusinessRuleError` (HTTP 400)
   - If medicines have been dispensed → `BusinessRuleError` (HTTP 400)
   - Otherwise → successfully transitions Visit to CANCELLED
3. The appointment cancel proceeds only if the visit cascade succeeds (or is skipped for COMPLETED/CANCELLED visits or missing `visit_id`).

**Rationale:** The Visit module's own transition logic is the single source of truth for "is it safe to cancel?" — it already audits billing and pharmacy state, preventing unsafe cascades without a separate hardcoded rule.

---

## Changes

### Backend (clinic-cms)

**Branch:** `fix/TASK-111-appt-cancel-visit-cascade` (base `origin/dev` @ 6d91053, alembic head 0068)  
**Commit:** `90d4c2e`

#### Modified Files

- `app/modules/appointments/services/appointment_service.py`
  - `cancel_appointment()`: Added cascade logic to call `visit_service.transition_to_cancel()` when `appointment.visit_id` is set and Visit status is non-terminal.
  - Docstring clarifies the cascade rule and guard-rail behavior.

#### Tests Added

- `tests/integration/appointments/test_appointments_e2e.py::TestCancelCascadesVisit` (3 tests):
  1. `test_cancel_checked_in_appointment_cascades_waiting_visit` — confirm → check-in (WAITING) → cancel → visit CANCELLED
  2. `test_cancel_checked_in_appointment_cascades_in_progress_visit` — same but with visit started (IN_PROGRESS)
  3. `test_cancel_appointment_without_visit_still_works` — regression: appointment without visit cancels normally

---

## Testing

**Environment:** Isolated Docker stack `fix111` (api 9965, postgres 5465, redis 6447)  
**Migration head:** 0068  
**Test results:** ✅ 89/89 passed

- `tests/integration/appointments/test_appointments_e2e.py` — 17/17 (14 pre-existing + 3 new)
- `tests/integration/appointments/` + `tests/integration/visits/` — 89/89 passed

**Code quality:**
- `ruff check` on changed files → clean, no new errors (baseline: 452 pre-existing, unchanged)
- `mypy app` → no new errors (baseline: 50 pre-existing, unchanged)

---

## API Behavior

### POST /api/v1/appointments/{appointment_id}/cancel

**Success (new behavior):**
- If appointment has linked Visit in non-terminal state:
  - Visit transitions to CANCELLED
  - Appointment transitions to cancelled
  - HTTP 200 (no change to status code)

**Blocked (new behavior, via Visit guard rails):**
- If Visit has money collected or medicines dispensed:
  - HTTP 400, `BusinessRuleError` (existing error code, reused)
  - Appointment remains in current state
  - Visit remains COMPLETED/IN_PROGRESS

**Unchanged:**
- No linked Visit (checked in before Visit existed): appointment cancels normally
- Visit already COMPLETED/CANCELLED: appointment cancels normally

---

## Acceptance Criteria Met

- [x] Hủy lịch đã check-in → Visit liên quan được hủy (cascade) hoặc chặn nếu not safe (quyết định: cascade)
- [x] Không còn visit mồ côi trong hàng đợi sau khi hủy lịch
- [x] Integration test: check-in→cancel → visit không còn WAITING

---

## Data Integrity Guarantees

- **No orphaned Visits:** Cascade ensures Visit is moved to a terminal state when possible.
- **No unsafe cancels:** Visit's own guard rails (billing + pharmacy state) prevent cascade when not safe.
- **No state-machine extension:** Reuses existing Visit cancel logic; no new transitions added.

---

## Deployment Notes

- No database migration required (no schema changes).
- No breaking API changes (HTTP status codes unchanged).
- Safe to deploy alongside other fixes — isolated to appointment cancel path.
