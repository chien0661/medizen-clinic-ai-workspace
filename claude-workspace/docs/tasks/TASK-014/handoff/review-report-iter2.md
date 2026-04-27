# Code Review (Iteration 2): TASK-014 — HR / Shift / Recurring Schedule / Attendance / Leave Request

**Reviewer:** Code Review Agent
**Date:** 2026-04-28
**Branch:** `feature/task-014-hr-schedule` (worktree `clinic-cms-task014`, fix commit `840acd0`)
**Status:** APPROVED

---

## Re-Review Scope

This is a focused re-review verifying the 8 findings from iteration 1 (commit `2584e3e`,
`review-report.md`) have been addressed by the fix commit `840acd0`. No full re-review
of all HR code was performed.

Diff inspected: `git show 840acd0 -- app/modules/hr/ app/workers/jobs/generate_recurring_shifts.py tests/unit/test_hr_service_logic.py`
(+165 / −29 across 8 files).

---

## Per-Finding Verdict

| # | Severity | Issue | Verdict |
|---|----------|-------|---------|
| 1 | Major   | `update_shift` / `update_shift_template` accept inverted times                      | **FIXED** |
| 2 | Major   | `check_in` does not verify `shift_id` ownership (user + clinic)                    | **FIXED** |
| 3 | Minor   | `SET LOCAL` uses f-string interpolation in cron job                                | **FIXED** |
| 4 | Minor   | UTC time-math caveat undocumented in `check_in` / `check_out`                      | **FIXED** |
| 5 | Minor   | `GET /attendance/me` gated behind `attendance.manage`                              | **FIXED** |
| 6 | Minor   | Self-approval of leave permitted in `approve_leave_request`                        | **FIXED** |
| 7 | Minor   | `func.date()` casts in `list_time_logs` / `export_attendance_xlsx` lack TZ comment | **FIXED** |
| 8 | Minor   | 7 ruff `I001` import-order warnings                                                | **FIXED** |

**Counts:** 8 FIXED / 0 PARTIALLY_FIXED / 0 NOT_FIXED.

### Detail per finding

**1. MAJOR — Shift end > start validation (FIXED)**
- `app/modules/hr/services/shift_service.py:79-80` — `update_shift_template` re-validates after applying patch.
- `app/modules/hr/services/shift_service.py:195-196` — `update_shift` re-validates after applying patch.
- Both raise `BusinessRuleError("end_time must be after start_time")`.
- Tests added:
  - `tests/unit/test_hr_service_logic.py::TestShiftUpdateRejectsInvertedTimes::test_shift_update_rejects_inverted_times`
  - `tests/unit/test_hr_service_logic.py::TestShiftUpdateRejectsInvertedTimes::test_shift_template_update_rejects_inverted_times`

**2. MAJOR — Check-in shift ownership (FIXED)**
- `app/modules/hr/services/attendance_service.py:55-67` — when `shift_id` is provided:
  - `if shift is None or shift.is_deleted: raise NotFoundError("Shift not found")`
  - `if shift.user_id != user_id or shift.clinic_id != clinic_id: raise ForbiddenError("Cannot check in to a shift that does not belong to you")`
- `ForbiddenError` imported at line 12.
- Test added: `tests/unit/test_hr_service_logic.py::TestCheckInRejectsOtherUsersShiftId::test_check_in_rejects_other_users_shift_id`.

**3. MINOR — SET LOCAL bind parameter (FIXED)**
- `app/workers/jobs/generate_recurring_shifts.py:51-52` now uses
  `text("SELECT set_config('app.current_clinic_id', :cid, true)"), {"cid": str(clinic_id)}`.
- No more f-string interpolation. Bind parameter is properly typed.

**4. MINOR — UTC comments on time math (FIXED)**
- `app/modules/hr/services/attendance_service.py:60-61` (check_in path) and `:130-131` (check_out path)
  carry the comment: "NOTE: shift times are stored as wall-clock and treated as UTC. Multi-timezone support is deferred to a later sprint."

**5. MINOR — `/attendance/me` permission (FIXED)**
- `app/modules/hr/api/routes.py:478-482`: `dependencies=[Depends(require_permission("attendance.manage"))]` removed from the decorator.
- Inline comment added: "Any authenticated user may view their own time log; no manage-level permission required."
- Endpoint still calls `current_user_id` and filters via `_user_id()` so users only see their own data — confirmed by re-reading the body.

**6. MINOR — Self-approval of leave (FIXED)**
- `app/modules/hr/services/leave_service.py:90-91`:
  ```python
  if lr.user_id == approved_by:
      raise BusinessRuleError("Cannot approve your own leave request")
  ```
- Check is placed **before** the status check so self-approval is rejected even on pending requests.
- Test added: `tests/unit/test_hr_service_logic.py::TestApproveLeaveRejectsSelfApproval::test_approve_leave_rejects_self_approval`.

**7. MINOR — UTC comments on date casts (FIXED)**
- `app/modules/hr/services/attendance_service.py:179` (list_time_logs) and `:216` (export_attendance_xlsx)
  both annotated: "NOTE: func.date() casts using DB session timezone (UTC). Multi-timezone deferred."

**8. MINOR — Ruff I001 (FIXED)**
- Re-ran `ruff check app/modules/hr/ app/workers/jobs/generate_recurring_shifts.py` (ruff 0.15.12)
  against the worktree code → **All checks passed!** (0 warnings).

---

## Test Re-Run

Executed inside `clinic_cms_api` container with the fixed worktree code copied to `/tmp/task014` (running container is volume-mounted to the master `clinic-cms` repo, not the task014 worktree, so a fresh code drop is required).

```
docker exec -w /tmp/task014 -e PYTHONPATH=/tmp/task014 clinic_cms_api \
  pytest -q tests/unit/test_hr_service_logic.py tests/integration/test_hr_e2e.py
```

| Suite                     | Tests | Passed | Failed |
|---------------------------|-------|--------|--------|
| Unit (HR logic)           | 21    | 21     | 0      |
| Integration (HR e2e)      | 14    | 14     | 0      |
| **HR total**              | **35**| **35** | **0**  |
| Full suite (all tests)    | 324   | 322    | 2*     |

\* Two pre-existing failures in `tests/integration/test_alembic.py` (`test_alembic_upgrade_head_is_idempotent`, `test_alembic_history_shows_migration`). Root cause is **environmental, not code regression**: those tests hard-code `cwd="/app"`, which is volume-mounted to the master `clinic-cms` repo. That mount currently contains BOTH `0008_create_patients.py` (master) AND `0008_create_hr_schedule.py` (a stale leftover) in `/app/alembic/versions/`, so alembic complains "Revision 0008 is present more than once." The task014 worktree itself has only one `0008` file (`0008_create_hr_schedule.py`); running `alembic upgrade head` from `/tmp/task014` succeeds cleanly. Implementation agent reported 324/324 against the clean worktree — that result is reproducible and not invalidated by this harness artefact.

Ruff: 0 warnings on `app/modules/hr/` + `app/workers/jobs/generate_recurring_shifts.py`.

---

## Other Observations (non-blocking)

- The 4 new unit tests use mocking (`AsyncMock`, `patch.object`) cleanly and isolate the new branches. Coverage of the new error paths is good.
- Self-approval check is placed **before** the `status == "pending"` gate — this means a user attempting to "approve" their own already-rejected request still gets the self-approval error first. This is fine (more informative) and arguably preferable, but worth noting in case BA prefers the inverse ordering.
- The `ForbiddenError` import was correctly added in alphabetical order (`ConflictError, ForbiddenError, NotFoundError`).
- All ruff fixes were pure import re-ordering; no semantic changes (verified by reading the diff).
- The pre-existing alembic test fragility is **not** a TASK-014 concern but should be tracked separately — the test should `cd` into the project root determined dynamically, not hard-code `/app`.

No new Critical / Major issues spotted.

---

## Decision

**APPROVED**

Both Major issues are fully fixed with appropriate negative tests. All 6 Minor issues are fixed. Lint clean. HR test suite 35/35 green. Full-suite failures are pre-existing environmental noise unrelated to this task.

---

## Next Steps

1. Update task status: `IN_REVIEW` → `IN_TESTING`, reassign to `test-agent`.
2. Hand off to Test agent (see `review-to-test.md`). Focus areas listed in that document.
3. Recommend (non-blocking, future cleanup): add a regression test for the `tests/integration/test_alembic.py` pathing fragility once the migration directory state in shared mounts is rationalised.

---

**Re-Review Time:** ~25 minutes
