# Handoff: TASK-005 → Test Agent

**From:** Code Review Agent
**To:** Test Agent
**Status:** IN_TESTING
**Decision (review iter 2):** **APPROVED**
**Date:** 2026-04-27
**Branch:** `feature/task-005-patients` (HEAD `d9c0546`)

---

## Summary

Iteration 2 resolved all 2 CRITICAL + 6 MAJOR + 2 MINOR findings from iter-1. The remaining MIN finding (m3 — `# noqa: B008` repetition) was deferred at iter-1 as "consistent with existing codebase". No new CRIT/MAJ introduced. Migration round-trip clean. 79/79 patient tests pass. 95% coverage on `app/modules/patients/`. Ruff exit 0.

Implementation details: see `docs/tasks/TASK-005/handoff/implementation-to-review.md` and the iteration 2 section of `docs/tasks/TASK-005/handoff/review-report.md`.

---

## Test Plan — Focus Areas for the Test Agent

The integration suite at `tests/integration/patients/test_patients_api.py` already covers the AC happy paths in real e2e form. Your job is the high-risk validation that integration tests cannot reasonably assert.

### Priority 1 — Performance benchmark (AC1 not yet validated)

**AC1:** "Search theo SĐT 10 chữ số trả < 100ms khi DB có 100k patient"

The trigram phone index `gix_patient_phone_trgm` is now in place (M2 fix), but the iter-2 test suite does not benchmark at scale. Build:

- Seed fixture that inserts ~100k synthetic patients across 1–3 clinics.
- Measure p95 latency for `GET /api/v1/patients/search?q=<10-digit>&type=phone`.
- Same for `type=name` with fuzzy queries (e.g., `nguyen vn an`, accent variants).
- Assert p95 < 100 ms on the local Docker stack.
- If exceeded, file a performance bug back to the implementation agent (do NOT silently relax the AC).

### Priority 2 — RLS isolation under production role

The integration test `test_tenant_isolation_via_http` documents that the `cms` DB role has `BYPASSRLS` so DB-level RLS is not enforced in tests. Production uses `cms_app` (no BYPASSRLS).

- Run merge / search / get-patient scenarios against the `cms_app` role to confirm cross-tenant access is denied at the DB level.
- Specifically: clinic-A user calling `GET /api/v1/patients/{clinic_b_patient_id}` must return 404 (not 200), and the underlying `SELECT` must return zero rows due to RLS.

### Priority 3 — Merge / undo behaviour matrix

Iter-2 has unit + integration coverage for the M4 manifest fix. Expand:

- **Concurrent merges**: two admins call `/merge` on overlapping (keep, drop) pairs simultaneously — does the locking on `fn_next_patient_code` plus row-level lock on `patient` prevent corruption?
- **Long manifest**: when drop_patient has many `patient_relation` rows (e.g., 100+ guardians), verify undo reverts exactly those IDs (use the test_undo_does_not_reassign_keep_patient_own_relations pattern but at scale).
- **Merge → undo → merge again**: after a successful undo, can the same drop_patient be merged again into a different keep_patient?
- **Undo at the deadline boundary**: undo at exactly `now() = undo_deadline` (within 1 ms) — currently the code does `now > undo_deadline` so equality is allowed; confirm the off-by-one is acceptable for the AC.

### Priority 4 — Audit log invariants

M1 fix opens a fresh session inside the BackgroundTask. Confirm:

- Every `GET /api/v1/patients/{id}` produces exactly 1 `audit_log` row with `action='READ', entity_type='Patient', entity_id=<patient.id>`.
- The `audit_log.user_id` and `audit_log.clinic_id` are correctly populated (RLS context vars set inside the BackgroundTask).
- `Patient.__audit_exclude__ = frozenset({"id_number"})` — verify CCCD/CMND values are absent from audit snapshots in CREATE/UPDATE rows.
- The integration test currently uses `await asyncio.sleep(0.5)` to wait for the BackgroundTask. Replace with a polling loop with a 5-second cap to make CI more robust.

### Priority 5 — Full AC traceability

Map each AC line in `task.md` to one or more test cases and verify each is asserted:

| AC | Test |
|----|------|
| Search SĐT 10 chữ số < 100ms @ 100k | (NEW) `test_perf_phone_search_under_100ms_at_100k` |
| Fuzzy `nguyen vn an` → `Nguyễn Văn An` | `test_search_by_name_fuzzy_matches_accented` ✅ exists |
| Guardian parent→child + `is_primary_contact=true` | `test_guardian_add_list_remove` (verify `is_primary_contact` field) |
| Merge: all Visit của drop_id có patient_id mới | covered for `patient_relation` only — `visit/prescription/invoice` tables don't exist yet; document deferral to TASK-007/011/013 |
| Undo merge trong 7 ngày khôi phục đúng | `test_merge_then_undo_within_window` ✅ + `test_undo_does_not_reassign_keep_patient_own_relations` ✅ |
| Sau 7 ngày → 410 Gone | `test_merge_undo_after_expired_deadline_returns_410` ✅ |

### Priority 6 — Negative paths / fuzz

- Search: empty `q`, `q` of 1 char, very long `q` (1000 chars), unicode-only `q` (`日本語`), null bytes — all must 4xx not 500.
- Create: very long `full_name` (>200 chars), invalid `gender`, `birth_year=0`, future DOB, both `dob` and `birth_year` mismatched.
- Merge: same-id merge (`keep_id == drop_id`), already-deleted patient, non-existent UUID.
- Undo: already-undone merge_log, merge_log from a different clinic.

---

## Test Environment

- Docker stack already running (`clinic_cms_postgres`, `clinic_cms_redis`, `clinic_cms_api`).
- Seed: existing test fixtures bootstrap a clinic + admin user; reuse the patterns from `tests/integration/patients/test_patients_api.py`.
- For perf seeding, use raw SQL `COPY` or `INSERT ... SELECT` against the patient table directly — avoid going through the API for 100k inserts.

## Out of Scope for Testing

- The user's untracked TASK-014 HR files in `alembic/versions/` (`0008_create_hr_schedule.py`, `0009_create_patients.py`) cause an alembic multi-head conflict. The pre-existing tests `test_alembic_upgrade_head_is_idempotent` and `test_alembic_history_shows_migration` will fail unless those files are temporarily moved aside. This is the user's WIP for a different task — do NOT modify or delete them. Document the limitation; do not file a bug.
- The pre-existing `test_tenancy_middleware.py::TestDevHeaders::test_clinic_id_only_no_user_allowed` failure is on the TASK-004 base, not TASK-005's responsibility.
- m3 (`# noqa: B008` repetition) is deferred per reviewer guidance — do not file a bug.

## Reporting

On completion, deposit:

- `docs/tasks/TASK-005/deliveries/test-cases/` — your test scenarios in markdown.
- `docs/tasks/TASK-005/deliveries/test-reports/` — a final PASS/FAIL report with perf numbers, RLS verification result, screenshots if applicable.
- `docs/tasks/TASK-005/bugs/` — any bug reports filed (intermediate, during testing).
- `docs/tasks/TASK-005/handoff/test-to-documentation.md` once all tests pass.

If any test fails the AC or reveals a defect, status moves to `IN_PROGRESS` (iter 3 — last automatic attempt before user escalation per `complete-task` skill loop-prevention rule).
