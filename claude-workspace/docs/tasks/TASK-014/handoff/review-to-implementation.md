# Handoff: TASK-014 → Code Implementation Agent

**From:** Code Review Agent
**To:** Code Implementation Agent
**Status:** IN_PROGRESS
**Decision:** CHANGES_REQUESTED
**Date:** 2026-04-28
**Branch:** `feature/task-014-hr-schedule` (worktree `clinic-cms-task014`)

## Summary

HR module functionality is solid — all 31 tests pass (re-run by reviewer in container against worktree code), all 6 AC verified. Two Major issues need fixing before testing can proceed: `ShiftUpdate` allows partial updates that silently violate `end_time > start_time`, and `attendance/check-in` does not verify the supplied `shift_id` belongs to the current user (allowing intra-clinic late-minute spoofing).

See `review-report.md` for the full breakdown (0 Critical / 2 Major / 6 Minor).

## Required Changes (Major — must fix)

1. **`app/modules/hr/services/shift_service.py:182-197`** — `update_shift` blindly applies fields. After applying, re-validate `shift.end_time > shift.start_time`. Same for `update_shift_template`. Raise `BusinessRuleError` on violation. Add a unit test (`test_shift_update_rejects_inverted_times`).

2. **`app/modules/hr/services/attendance_service.py:55-63`** — when `shift_id` is provided to `check_in`, verify `shift.user_id == user_id` and `shift.clinic_id == clinic_id`. Raise `ForbiddenError` (or `NotFoundError`) on mismatch. Add a unit test (`test_check_in_rejects_other_users_shift_id`).

## Recommended (Minor — fix at your discretion)

3. **`app/workers/jobs/generate_recurring_shifts.py:51`** — replace f-string `SET LOCAL` with bind-parameterised `SELECT set_config('app.current_clinic_id', :cid, true)`.
4. **`app/modules/hr/services/attendance_service.py:59, 126`** — at minimum, add a comment that shift times are treated as UTC. (Multi-timezone deferred.)
5. **`app/modules/hr/api/routes.py:478-481`** — `/attendance/me` should not require `attendance.manage` (a normal employee should view their own log).
6. **`app/modules/hr/services/leave_service.py:82-129`** — optional: forbid self-approval (`if lr.user_id == approved_by: raise BusinessRuleError(...)`).
7. **`app/modules/hr/services/attendance_service.py:173, 209`** — document the `func.date()` UTC-cast caveat for export & list_time_logs.
8. **Lint** — `ruff check --fix app/modules/hr/ app/workers/jobs/generate_recurring_shifts.py` (7 fixable I001 import-order warnings).

## Verification After Fix

```bash
cd E:/MyProject/clinic-cms-workspace/clinic-cms-task014
# Run in docker container with worktree mounted (network = docker_default):
MSYS_NO_PATHCONV=1 docker run --rm --network docker_default \
  -v "E:\MyProject\clinic-cms-workspace\clinic-cms-task014:/app" -w //app \
  -e DATABASE_URL=postgresql+asyncpg://cms:cms@postgres:5432/cms \
  -e TEST_DATABASE_URL=postgresql+asyncpg://cms:cms@postgres:5432/cms \
  -e REDIS_URL=redis://redis:6379/0 docker-api:latest \
  sh -c "pip install -q -e .[dev] && python -m pytest -q tests/unit/test_hr_service_logic.py tests/integration/test_hr_e2e.py"
```

Expected: all 31 + the new 2 unit tests pass.

After fixes:
- Update `docs/tasks/TASK-014/task.md` frontmatter: `status: IN_REVIEW`, `assigned: code-review-agent`.
- Append to handoff `implementation-to-review.md` (new section "Round 2 — Review feedback fixes") describing each change with file:line.
