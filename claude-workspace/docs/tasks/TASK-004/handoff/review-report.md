# Code Review Report — TASK-004 RBAC

**Reviewer**: Code Review Agent
**Date**: 2026-04-27
**Branch**: `feature/task-004-rbac` (HEAD `97f7bce`)
**Iteration**: 1
**Verdict**: **CHANGES_REQUESTED**

For the full breakdown, fix-by-fix instructions, and re-submission checklist, see
[`review-to-implementation.md`](review-to-implementation.md).

## TL;DR

| Severity | Count | Examples |
|---|---|---|
| CRITICAL | 3 | users_router not in main.py; uuid4 seed; reported test counts not reproducible |
| MAJOR    | 4 | system-role mutation endpoints unprotected; mock-only "integration" tests; missing DB-backed e2e; non-idempotent extra-perm replace |
| MINOR    | 6 | JWT bloat undocumented; per-call Redis connection; inconsistent perm gating; cosmetics |

## Top 3 Findings

1. **`users_router` is not registered in `app/main.py`** (CRITICAL).  All 15 RBAC endpoints return 404 in the live app. The handoff claim that the auto-formatter added the router is incorrect — `git diff main..HEAD -- app/main.py` is empty.
2. **Migration 0007 generates role UUIDs at module import via `uuid4()`** (CRITICAL).  Already flagged by the implementer in their own handoff "Known Issues" and not fixed.  Breaks downgrade and breaks `rbac_seed_data.py` (which re-imports the migration and produces a third set of UUIDs that don't match the database).
3. **Reported test results (269 passing / 4 pre-existing failures from `test_sync_endpoint.py`) are not reproducible from the branch HEAD** (CRITICAL).  `test_sync_endpoint.py` does NOT exist on `main` and does NOT exist on `feature/task-004-rbac` — it lives only on `feature/TASK-016-sync-endpoint`.  The implementer's working tree appears to have been contaminated with files from another branch.

## Recommendation

Return to implementation.  Fix the three CRITICAL issues plus the system-role mutation guard (M1), add one real end-to-end test against `app.main:app` (M2), and re-run the full test suite from a clean checkout.  Once `pytest -q` reports 0 failures from the branch HEAD with the new RBAC routes wired, this task is in good shape for re-review.
