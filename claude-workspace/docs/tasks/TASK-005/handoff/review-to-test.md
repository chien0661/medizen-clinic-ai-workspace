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

---

## Iteration 3 Handoff (2026-04-27) — Bug-Fix Regression Validation

**Decision (review iter 3):** **APPROVED**
**Branch HEAD:** `feature/task-005-patients` @ `6e98751`
**Scope:** Quick regression verification of the 4 bug fixes from iter-2 testing. NOT a full re-test cycle.

### Context

Iter-2 testing surfaced 4 bugs (`BUG-001`/`002`/`003`/`004`). Implementation Agent fixed all 4 (commits `ae4d8f8`, `0625af8`, `2da9db0`, `d020648`+`61208ae`, plus style polish `6e98751`). Code Review Agent (iter 3) verified each fix at the root cause and APPROVED.

### Verification asks (minimal — please be quick)

1. **Confirm the 4 previously-failing tests now PASS:**
   - `tests/integration/patients/test_patients_negative.py::TestSearchNegativePaths::test_search_null_byte_q_does_not_500` (BUG-001)
   - `tests/integration/patients/test_patients_negative.py::TestCreateNegativePaths::test_create_future_dob_returns_4xx` (BUG-002)
   - `tests/integration/patients/test_patients_negative.py::TestMergeNegativePaths::test_merge_same_id_returns_4xx` (BUG-003)
   - `tests/integration/patients/test_patients_negative.py::TestUndoNegativePaths::test_undo_merge_from_different_clinic_returns_404_or_403` (BUG-004 — check response is 404 specifically, not 403, to avoid enumeration leak)

2. **Sanity full pass:** `pytest tests/{unit,integration}/patients/ -m 'not perf' --tb=short`. Expect 117/117 pass, ~94% coverage.

3. **Mark each bug report as RESOLVED** in `docs/tasks/TASK-005/bugs/BUG-00{1..4}.md` with the verifying test name + commit SHA.

4. **Do NOT re-run the full perf / RLS / advanced merge matrix** — those passed in iter-2 testing and are unchanged. Only the 4 negative-path scenarios are in scope.

### After verification

- If all 4 PASS and full suite holds 117/117: write `docs/tasks/TASK-005/handoff/test-to-documentation.md` and update task status to `DOCUMENTING` with `assigned: documentation-agent`.
- If anything fails: file a new bug, set status to `IN_PROGRESS` (iter 4), and notify the user — iter 4 is past the loop-prevention threshold and requires human escalation.

### Out of scope (do not file as bugs — already cleared)

- `m3` (`# noqa: B008` repetition) — deferred at iter-1 reviewer guidance.
- BUG-004 service signature `clinic_id: UUID | None = None` — confirmed safe by iter-3 review (route always supplies a real auth-context clinic_id; `None` path is unit-test-only).
- Pre-existing `test_tenancy_middleware.py::TestDevHeaders::test_clinic_id_only_no_user_allowed` failure (TASK-004 base).
- Alembic multi-head conflict from user's untracked TASK-014 HR files.

### Per-bug fix references

| Bug | Severity | Fix Commit(s) | Layer |
|-----|----------|---------------|-------|
| BUG-001 | High | `ae4d8f8` | route guard (rejects `\x00` in `q` with 400) |
| BUG-002 | Medium | `0625af8` | schema field_validator on `PatientCreate` + `PatientUpdate` |
| BUG-003 | High | `2da9db0`, style `6e98751` | schema model_validator on `PatientMergeRequest` |
| BUG-004 | Critical | `d020648`, `61208ae` | route forwards `clinic_id`; service raises `NotFoundError` (HTTP 404) on tenant mismatch |

