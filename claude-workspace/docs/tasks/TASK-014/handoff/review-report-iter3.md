# Code Review Report — TASK-014 Iteration 3 (Bug-Fix Re-Review)

**Reviewer**: Code Review Agent
**Date**: 2026-04-28
**Branch**: `feature/task-014-hr-schedule` (worktree: `clinic-cms-task014`)
**Commit reviewed**: `cc5c539` — `fix(hr): address 4 bugs from test round (TASK-014)`
**Decision**: **APPROVED**

---

## Scope

Focused re-review of the 4 surgical bug fixes prescribed in `docs/tasks/TASK-014/handoff/test-to-implementation.md` (Round 2 fix recipes). Per protocol, no broad re-review of unrelated areas.

Files touched in commit `cc5c539` (5 total, all in `app/modules/hr/`):

```
app/modules/hr/api/routes.py                  | 25 +++++++++++++++++--------
app/modules/hr/services/attendance_service.py | 11 ++++++++---
app/modules/hr/services/leave_service.py      | 14 ++++++++++----
app/modules/hr/services/recurring_service.py  | 12 +++++++++---
app/modules/hr/services/shift_service.py      | 24 ++++++++++++++++++------
```

No test files were modified. No code outside `app/modules/hr/` was touched.

---

## Per-Bug Verdict

### BUG-001 (CRITICAL — cross-clinic mutation via BYPASSRLS) — **FIXED**

- `get_shift_template`, `get_shift` in `shift_service.py` accept optional `clinic_id: UUID | None = None`; raise `NotFoundError` (NOT `ForbiddenError`) when `str(obj.clinic_id) != str(clinic_id)`. Existence is not leaked.
- `get_leave_request` in `leave_service.py` — same pattern.
- `get_recurring_schedule` in `recurring_service.py` — same pattern.
- All mutating service entrypoints (`update_*`, `delete_*`, `approve_*`, `reject_*`) now accept `clinic_id` and forward it to their guarded `get_*` helper.
- Routes `routes.py` correctly pass `clinic_id=_clinic_id()` from the request context (`current_clinic_id` ContextVar), validated for all 8 mutating handlers:
  - `update_shift_template` (L154), `delete_shift_template` (L169)
  - `update_shift` (L243), `delete_shift` (L258)
  - `update_recurring_schedule` (L321), `delete_recurring_schedule` (L336)
  - `approve_leave_request` (L419), `reject_leave_request` (L436)
- `clinic_id` parameter defaults to `None` → fully backwards-compatible signature; no existing test or caller breaks.
- `db.get(...)` calls remaining in HR services audit:
  - `attendance_service.py:133` (`check_out`): reads `Shift` for already-validated user time_log — safe.
  - `recurring_service.py:121`: reads `ShiftTemplate` for an `rs` already validated by `get_recurring_schedule(...)` — safe.
  - All other `db.get` are inside the four guarded helpers.

### BUG-002 (MAJOR — PATCH inverted times accepted) — **FIXED**

- `BusinessRuleError` in `app/core/exceptions.py:64-72` correctly maps to `http_status=400`, dispatched by `_error_response` exception handler.
- `update_shift` (`shift_service.py:206-207`) checks `if shift.end_time <= shift.start_time: raise BusinessRuleError(...)` AFTER applying patched fields and BEFORE `db.flush(...)`. Correct.
- `update_shift_template` (`shift_service.py:85-86`) applies the same pattern.
- The implementation report's claim is verified: code was correct since Round 2; the failure was a Docker mount issue (test container running `feature/task-005-patients` not `feature/task-014-hr-schedule`). No code change needed beyond the existing Round 2 logic; tests now pass with task014 deployed.

### BUG-003 (MAJOR — leave self-approval not rejected) — **FIXED**

- `leave_service.py:95-96`: `if str(lr.user_id) == str(approved_by): raise BusinessRuleError("Cannot approve your own leave request")`.
- Placed BEFORE the status check (line 98 `if lr.status != "pending": ...`), so self-approval is rejected even on stale/pending requests where status would otherwise pass.
- UUID type-mismatch is resolved via `str()` coercion on both sides.

### BUG-004 (CRITICAL — check-in on soft-deleted + cross-user shift) — **FIXED**

- `attendance_service.py:55-60`: `db.get(Shift, shift_id)` replaced with explicit `select(Shift).where(Shift.id == shift_id, Shift.is_deleted.is_(False))` → bypasses ORM identity-map cache and enforces soft-delete filter at SQL level. Returns `NotFoundError` if missing or deleted.
- `attendance_service.py:64-65`: `if str(shift.user_id) != str(user_id) or str(shift.clinic_id) != str(clinic_id): raise ForbiddenError(...)` — `str()` coercion fixes UUID type mismatch.
- Error type is `ForbiddenError` (HTTP 403), matching the test expectation in `test_br10_staff_cannot_checkin_admins_shift`. The cross-clinic case is also caught here (BUG-001/004 overlap).

---

## Test Re-Run Summary

Ran via `docker exec clinic_cms_api`:

```
tests/unit/test_hr_service_logic.py
tests/integration/test_hr_e2e.py
tests/integration/test_hr_api_contracts.py
tests/integration/test_hr_business_rules.py
tests/integration/test_hr_workflows.py
```

**Result**: `95 passed, 89 warnings in 76.06s` — **95/95 pass**, exactly as the implementation agent reported.

Pre-existing unrelated failure verified unchanged:
- `tests/unit/test_tenancy_middleware.py::TestDevHeaders::test_clinic_id_only_no_user_allowed` — still fails (1 failed, 17 passed). Documented since Round 2; not introduced by TASK-014. **Not blocking.**

---

## Backwards Compatibility / Side-Effect Audit

- All four `get_*()` and all `update_*` / `delete_*` / `approve_*` / `reject_*` service signatures gain `clinic_id: UUID | None = None` (default `None`). Internal callers in services pass `clinic_id` through; external callers without the kwarg behave exactly as before.
- No public schema, route signature, or DTO changed.
- No DB migration changes.
- No test code changed.
- Lint not re-run, but no new imports added beyond the existing `select` (already present in `attendance_service.py`).

---

## Anything New Spotted (Non-blocking)

1. **Defense in depth — RLS at DB layer**: The fix is service-level only; the underlying `BYPASSRLS=True` on the `cms` DB user remains. This is acceptable for V1 per the test handoff ("optional for V1 if service-layer fix provides adequate protection"), but the residual risk is documented and should be tracked as infra follow-up. No action required for this task.
2. **`get_shift` is also called from non-mutating contexts** (e.g. detail GET endpoints if any): if any GET handler exists that does not pass `clinic_id`, RLS still acts as a soft barrier (when not BYPASSRLS) but cross-clinic existence may technically be probable. Spot-check of `routes.py` shows no such handler in the diff, so not an issue today. Worth noting for future GET-by-id endpoints.
3. **`f"clinic_id required"` in `_clinic_id()` raises HTTP 400** rather than 412/422 — matches existing convention in this codebase. Not a finding.

None of the above is blocking.

---

## Decision

**APPROVED.** All 4 bug fixes are correct, surgical, backward-compatible, and verified by 95/95 passing tests. Returning to Test Agent for the final test pass (Round 2 of testing).

Next agent: **Test Agent**. Status: `IN_TESTING`. Handoff: `handoff/review-to-test-iter2.md`.
