# Handoff: TASK-014 → Test Agent

**From**: Code Review Agent (Iteration 2)
**To**: Test Agent
**Status**: IN_TESTING
**Date**: 2026-04-28
**Branch**: `feature/task-014-hr-schedule` (worktree: `clinic-cms-task014`)
**Commits**: `2584e3e` (initial implementation) + `840acd0` (review fixes)

---

## Review Outcome

**APPROVED** — Iteration 2 verified all 8 findings from iteration 1 are fully fixed.

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0     | —      |
| Major    | 2     | 2 FIXED |
| Minor    | 6     | 6 FIXED |
| **Total**| **8** | **8 FIXED** |

See `review-report-iter2.md` for the per-finding verdict matrix.

---

## Test Suite Status (as observed by reviewer)

| Suite                  | Tests | Passed |
|------------------------|-------|--------|
| Unit (HR logic)        | 21    | 21     |
| Integration (HR e2e)   | 14    | 14     |
| **HR module total**    | **35**| **35** |

Plus 4 new tests added in iteration 2:
- `TestShiftUpdateRejectsInvertedTimes::test_shift_update_rejects_inverted_times`
- `TestShiftUpdateRejectsInvertedTimes::test_shift_template_update_rejects_inverted_times`
- `TestCheckInRejectsOtherUsersShiftId::test_check_in_rejects_other_users_shift_id`
- `TestApproveLeaveRejectsSelfApproval::test_approve_leave_rejects_self_approval`

Lint: ruff clean (0 warnings on `app/modules/hr/` + worker job).

Pre-existing failures: 2 in `tests/integration/test_alembic.py` (NOT a TASK-014 issue — caused by stale `0008_create_patients.py` in the master `clinic-cms` mount; alembic from a clean worktree succeeds). The implementation agent reported 324/324 against a clean checkout; this remains accurate.

---

## Acceptance Criteria — All 6 Verified Green

| AC | Test | Result |
|----|------|--------|
| AC1: Recurring Mon/Wed/Fri → shifts for May | `test_ac1_recurring_generates_may_shifts` | PASS |
| AC2: Approve leave 05-10→12 → shifts on_leave | `test_ac2_approve_leave_marks_shifts` | PASS |
| AC3: Check-in 7:45 / shift 7:30 → late=15 | `test_ac3_late_minutes` | PASS (UTC) |
| AC4: Check-out 12:30 / shift end 12:00 → ot=0.5 | `test_ac4_ot_hours` | PASS (UTC) |
| AC5: Excel export 1mo × 10 employees < 5s | `test_ac5_export_performance` | PASS |
| AC6: Duplicate active check-in → 409 | `test_ac6_duplicate_checkin_returns_409` | PASS |

---

## Focus Areas for Testing Phase

The following areas warrant attention beyond what existing automated tests cover.

### 1. Cross-tenant / cross-user negative paths (HIGH PRIORITY)

The new `check_in` ownership check (Issue 2 fix) is a security boundary. Add E2E tests beyond the unit test:

- **A**: Two users in same clinic. User A creates own shift. User B attempts `POST /attendance/check-in` with `shift_id=<A's shift>` → expect HTTP 403 with `error.code = "FORBIDDEN"` and message containing "does not belong to you".
- **B**: User attempts check-in with a `shift_id` from another clinic (cross-tenant) → expect HTTP 404 (RLS hides it) or HTTP 403, whichever the service returns first.
- **C**: `shift_id` referencing a soft-deleted shift → expect HTTP 404 "Shift not found".
- **D**: `shift_id` for a shift belonging to the user but in a different clinic context (theoretically impossible if RLS holds, but worth a defence-in-depth check).

### 2. Inverted-time updates via API (HIGH PRIORITY)

Issue 1 was fixed at service level. The schema still allows independent `start_time` / `end_time` patches. Add API-level negative tests:

- `PATCH /shifts/{id}` with `{"start_time": "13:00:00"}` against an existing (09:00, 12:00) shift → expect HTTP 400/422 with `BUSINESS_RULE_VIOLATION`.
- Same for `PATCH /shift-templates/{id}`.
- Equality boundary: `start_time == end_time` should also be rejected (the check is `<=`).
- Confirm the original shift is not mutated on rejection (DB roll-back).

### 3. Self-approval of leave (MEDIUM)

- User submits `POST /leave-requests`, then user (with `leave.approve` permission) calls `POST /leave-requests/{id}/approve` → expect HTTP 400 `BUSINESS_RULE_VIOLATION` "Cannot approve your own leave request".
- Manager A approves own leave → rejected (same path, different permission holder).
- Different approver (Manager B) approves Manager A's leave → success.

### 4. `/attendance/me` access (MEDIUM)

The fix for Issue 5 removed `attendance.manage`. Verify:

- An ordinary employee (no `attendance.manage`, only authenticated) can `GET /attendance/me` → 200 with only their own time logs.
- The endpoint never returns another user's logs even if a `user_id` query param were forged (it should ignore any user filtering and use `_user_id()` from JWT).
- A user with `attendance.manage` can still call `/attendance` (admin list) and see clinic-wide logs (this remains gated).

### 5. Recurring shift cron (MEDIUM)

Issue 3 fix changed `SET LOCAL` to `set_config()` bind-parameter. Verify:

- Run `python -m arq app.workers.scheduler.WorkerSettings` (or trigger via the test fixture) and confirm:
  - `app.current_clinic_id` GUC is set correctly per clinic.
  - RLS policies on `shift` / `recurring_schedule` resolve correctly under the new statement.
  - Idempotency is preserved across two runs in the same day.
- Optionally write a small Postgres-level test: connect, run the bind-parameter query, then `SELECT current_setting('app.current_clinic_id')` to confirm the GUC took effect within the transaction.

### 6. Timezone / wall-clock semantics (LOW — DOCUMENT, don't block)

Issues 4 & 7 are documented as deferred. For TASK-014's testing phase:

- Run all attendance / late / OT tests under UTC (current default — already passing).
- Document that non-UTC clinic deployments will produce skewed `late_minutes` / `ot_hours` and that the `func.date()` filter in `/attendance/export` and `/attendance` list rolls over at UTC midnight, not local. This should appear in the test report's "Known Limitations" section.

### 7. Excel export under load (LOW)

AC5 covers performance for 10 employees × 1 month. Optionally extend:

- 50 employees × 3 months → confirm response time ≤ ~30 s and memory profile stays bounded (no temp-file spillover).
- Confirm `Content-Disposition: attachment; filename=...xlsx` and content-type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.

### 8. Audit trail (LOW)

All 5 HR models have `__auditable__ = True`. Spot-check `audit_log` rows after:
- Creating a shift template
- Approving a leave (should record the new `status` and the marked-on_leave shifts)
- A successful check-in / check-out

This was implicitly covered by RLS + audit infra in TASK-002/003 but worth one direct verification.

---

## Test Environment Notes

- The running `clinic_cms_api` container is volume-mounted to the master `clinic-cms` repo, NOT to `clinic-cms-task014`. To test against TASK-014 code, either:
  1. Stop containers, switch master clinic-cms to `feature/task-014-hr-schedule` worktree, `docker compose up`, run pytest. **OR**
  2. Use `docker cp` to drop the worktree code into `/tmp/task014` inside the api container and run pytest with `-w /tmp/task014 -e PYTHONPATH=/tmp/task014` (this is what the reviewer did).
- The `/app/alembic/versions/` directory in the master mount currently contains stale leftover files including a duplicate `0008_create_patients.py`. This causes `tests/integration/test_alembic.py` to fail when run against the master mount. Test in the clean worktree to get accurate alembic results.

---

## What's Out of Scope for Test Phase

- Multi-timezone correctness (deferred — document only).
- Cross-tenant E2E performance / load testing (not part of AC).
- Worker autoscaling / failure recovery (cron job runs daily, single instance is acceptable per spec).

---

## Reference Files

- Implementation report (with Round 2 fixes): `handoff/implementation-to-review.md`
- Iteration 1 review: `handoff/review-report.md`
- Iteration 2 review (this one): `handoff/review-report-iter2.md`
- Code Review Agent contract: `.claude/agents/code-review.md`
- Code: `clinic-cms/app/modules/hr/`
- Tests: `clinic-cms/tests/unit/test_hr_service_logic.py`, `clinic-cms/tests/integration/test_hr_e2e.py`
