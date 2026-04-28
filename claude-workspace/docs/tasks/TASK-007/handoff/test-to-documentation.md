# Handoff: TASK-007 → Documentation Agent

**From**: Test Agent
**To**: Documentation Agent
**Status**: DOCUMENTING
**Date**: 2026-04-28
**Branch**: `feature/task-007-visits` (HEAD `e4e2ada`)

---

## Summary

All tests PASSED (117/117). API validated, AC coverage complete. One bug filed (BUG-001 — MAJOR, non-blocking for documentation). Ready for documentation.

---

## Test Results

- **Non-perf suite**: 116 passed, 0 failed (1 deselected = perf mark excluded)
- **Perf suite**: 1 passed — `test_perf_queue_under_50ms_for_50_visits`
- **Coverage**: 87% (317 stmts, 41 missed — above 80% threshold)
- **Lint**: `ruff check` — All checks passed!
- **Full suite regression**: 619 passed, 2 failed (pre-existing, unrelated)
- **Test report**: `docs/tasks/TASK-007/deliveries/test-reports/test-report.md`

---

## AC Verification (All 6 ACs PASS)

| AC | Description | Result |
|----|-------------|--------|
| AC #1 | Visit number `YYYYMMDD-NNN`, unique per clinic+date | PASS |
| AC #2 | WAITING→COMPLETED direct transition rejected (409) | PASS |
| AC #3 | COMPLETED cannot revert to any status | PASS (4 attempts all 409) |
| AC #4 | Cancel from COMPLETED rejected (409) | PASS |
| AC #5 | Concurrent call-next no race condition (SKIP LOCKED) | PASS (2-way + 5-way concurrent) |
| AC #6 | Queue 50 visits < 50ms (p95) | PASS — **p95 = 13.6 ms** |

---

## New Test Files (Source Repo)

| File | Tests | Category |
|------|-------|----------|
| `tests/integration/visits/test_visits_perf.py` | 1 | Performance (AC #6) |
| `tests/integration/visits/test_visits_lifecycle.py` | 10 | Full lifecycle E2E + visit number scale |
| `tests/integration/visits/test_visits_rls.py` | 8 | RLS isolation (cms_app role) |
| `tests/integration/visits/test_visits_concurrent.py` | 2 | 5-way concurrent call-next |
| `tests/integration/visits/test_visits_negative.py` | 12 | Negative paths / fuzz |

---

## Bug Filed

| Bug | Severity | Summary |
|-----|----------|---------|
| `bugs/BUG-001.md` | MAJOR | `create_visit` with non-existent `patient_id` raises unhandled FK IntegrityError instead of HTTP 404. Fix: add patient existence check before `db.flush()`. Non-blocking for documentation — no data corruption risk. |

---

## Key Findings for Documentation

1. **Performance**: Queue query p95 = 13.6ms against 50 WAITING visits (73% headroom under 50ms AC). The `ix_visit_clinic_status_priority` partial index is highly effective.
2. **RLS**: `visit` and `visit_number_counter` both enforce tenant isolation under `cms_app` (BYPASSRLS=false). Cross-clinic reads correctly denied.
3. **Visit number**: Counter is per `(clinic_id, visit_date)`. Resets at midnight per clinic independently.
4. **State machine**: All terminal states (COMPLETED, CANCELLED) correctly reject further transitions.
5. **Cancel reason**: `min_length=3`, not-blank validated. No max_length — long strings accepted (documented).
6. **Concurrency**: `SELECT FOR UPDATE SKIP LOCKED` proven effective at 5-way concurrency with distinct assignment verified at DB level.
7. **BUG-001**: Document that `patient_id` validation is incomplete — ghost patient IDs cause a DB-level FK error rather than API 404.
