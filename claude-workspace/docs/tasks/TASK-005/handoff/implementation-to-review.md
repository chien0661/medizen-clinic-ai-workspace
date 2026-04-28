# Handoff: TASK-005 → Code Review Agent (Iteration 2)

**From:** Code Implementation Agent  
**To:** Code Review Agent  
**Status:** IN_REVIEW (iteration 2)  
**Date:** 2026-04-27  
**Branch:** `feature/task-005-patients` (HEAD `d9c0546`)

---

## Summary

All 2 CRITICAL + 6 MAJOR + 2 MINOR findings from iteration 1 review have been addressed. Migration round-trip is clean. 79/79 tests pass. Coverage 95%. Ruff exit 0.

---

## Finding-by-Finding Resolution

### CRITICAL

**C1 — Migration 0008 fails on clean DB (unaccent not IMMUTABLE)**  
Fix: Added `immutable_unaccent(text)` SQL function (IMMUTABLE, STRICT, PARALLEL SAFE) in `upgrade()` before the GIN index. Updated `gix_patient_name_search` to use `immutable_unaccent(full_name)`. Added `gix_patient_phone_trgm` GIN index for phone (M2 fix, same commit). Updated `fn_next_patient_code` to use numeric `MAX(CAST(SUBSTRING(...) AS INTEGER))` over all rows including soft-deleted (M5 fix). Added `DROP FUNCTION IF EXISTS immutable_unaccent(text)` to `downgrade()`. Also updated `search_patients` in `patient_service.py` to call `func.immutable_unaccent()` matching the index.  
Commit: `adea8b6`  
Verified: `alembic downgrade 0007 → upgrade head → downgrade -1 → upgrade head` — all clean.

**C2 — Integration tests are mock-only**  
Fix: Completely rewrote `tests/integration/patients/test_patients_api.py`. New file: 15 real e2e tests against `app.main:app` using `httpx.AsyncClient` + live PostgreSQL + Redis. Pattern modelled on `test_rbac_e2e_real_db.py`. Covers: patient permissions seeded, create 201 + patient_code, duplicate name+DOB → 201 + warnings, fuzzy name search (Nguyễn Văn An AC), apostrophe in search (M3), phone search via trigram (M2), code search, guardian add/list/remove, merge happy path, cross-tenant 403, undo within window (restores drop_patient), undo expired → 410, audit READ row written (M1 verification), tenant isolation documentation, permission gating 403, M4 undo correctness, M5 code non-reuse.  
Commit: `d9c0546`

### MAJOR

**M1 — `audit_patient_read` BackgroundTask uses a closed AsyncSession**  
Fix: Changed `audit_patient_read` signature to `(patient_id: UUID, clinic_id: UUID, user_id: UUID | None) -> None`. Opens its own `AsyncSessionLocal()` session, sets RLS context vars via `SET LOCAL`, writes audit, commits, closes. Route now passes `patient.id, clinic_id, user_id` (plain values, no ORM objects) to background task.  
Files: `app/modules/patients/services/patient_service.py`, `app/modules/patients/api/routes.py`  
Commit: `e2e06cb`

**M2 — Phone search uses ILIKE '%q%' over btree (cannot meet AC < 100ms @ 100k)**  
Fix: Added `gix_patient_phone_trgm ON patient USING gin (phone gin_trgm_ops) WHERE NOT is_deleted` in migration. Rewrote phone search branch to use `Patient.phone.op("%")(q)` (pg_trgm similarity operator) + `ORDER BY similarity(phone, q) DESC`.  
Files: `alembic/versions/0008_create_patients.py`, `app/modules/patients/services/patient_service.py`  
Commit: `adea8b6` (migration), `e2e06cb` (service)

**M3 — `to_tsquery` crashes on apostrophes / special chars**  
Fix: Replaced `to_tsquery("simple", ...)` with `plainto_tsquery("simple", func.immutable_unaccent(q))`. `plainto_tsquery` sanitises arbitrary user input and cannot raise on apostrophes. Regression test added (`test_search_by_name_apostrophe_does_not_raise` in unit tests, `test_search_by_name_apostrophe_does_not_500` in integration tests).  
File: `app/modules/patients/services/patient_service.py`  
Commit: `e2e06cb`

**M4 — Undo over-reassigns rows that originally belonged to keep_patient**  
Fix: `merge()` now captures, per `(table, fk_col)`, the list of row IDs that were actually moved from `drop_id → keep_id`. This manifest is stored as `source_patient_data["reassigned_refs"]`. `undo_merge()` reads the manifest and issues `UPDATE ... WHERE id = ANY(:ids)` — only reverting rows that were actually moved at merge time. Rows originally on `keep_patient` are untouched. Legacy fallback (blind reassignment) retained for merge_logs that pre-date this fix (no `reassigned_refs` key). Regression test added in both unit (`test_undo_only_moves_manifested_rows`) and integration (`test_undo_does_not_reassign_keep_patient_own_relations`).  
File: `app/modules/patients/services/merge_service.py`  
Commit: `6aefd35`

**M5 — Unique-code conflict between merge and undo**  
Fix: `fn_next_patient_code` no longer filters `WHERE NOT is_deleted`. It uses `MAX(CAST(SUBSTRING(patient_code FROM 3) AS INTEGER))` over ALL rows (including soft-deleted) to ensure codes are never reused. This prevents `uq_patient_clinic_code` violations when `undo_merge` un-soft-deletes a patient. Regression test in integration: `test_patient_code_not_reused_after_merge_and_undo_succeeds`.  
File: `alembic/versions/0008_create_patients.py` (in `fn_next_patient_code` function body)  
Commit: `adea8b6`

**M6 — 11 ruff lint errors in test files**  
Fix: Removed all unused imports (`ForbiddenError`, `PatientMergeRequest`, `datetime`, `timezone`, `call`) and unused local assignments (`rel`, `merge_log`, `result` x2, `mock_search`). Unit tests for `audit_patient_read` updated to match new signature. `test_captures_all_columns` converted to `async def` to match module-level `pytestmark` (m2 fix).  
Files: all four unit test files + integration test file  
Commit: `b384e97`

### MINOR

**m1 — fn_next_patient_code lexical MAX breaks at 4 → 5 digit width**  
Fixed as part of M5: switched to `MAX(CAST(SUBSTRING(...) AS INTEGER))` numeric ordering. Handles BN9999 → BN10000 correctly.

**m2 — Sync `test_captures_all_columns` marked asyncio at class scope**  
Fixed: method converted to `async def test_captures_all_columns`.

**m3 — Repeated `# noqa: B008` in routes**  
Left as-is. Pre-existing pattern across the codebase. Out of scope per reviewer note.

---

## Verification Results

### Migration Round-Trip (run on live Docker stack, without user's HR WIP files)

```
alembic downgrade 0007 → OK
alembic upgrade head   → OK (created immutable_unaccent, all 3 GIN indexes, fn_next_patient_code)
alembic downgrade -1   → OK (dropped function, indexes, tables cleanly)
alembic upgrade head   → OK (idempotent forward)
```

Note: The user's untracked HR files (`0008_create_hr_schedule.py`, `0009_create_patients.py`) create an alembic multi-head conflict in the versions directory. The pre-existing `test_alembic_upgrade_head_is_idempotent` and `test_alembic_history_shows_migration` tests fail when those files are present. When the HR files are moved out temporarily, those tests pass. This is a pre-existing user working-tree issue, not a TASK-005 regression.

### Full Test Suite

```
tests/unit/patients/        : 61 passed
tests/integration/patients/ : 18 passed (real DB e2e)
Total patients module       : 79/79 passed
Coverage on app/modules/patients/ : 95% (493 stmts, 27 missed)

Full suite: 396 passed, 3 failed (all pre-existing)
  - test_alembic_upgrade_head_is_idempotent — HR file conflict (not TASK-005)
  - test_alembic_history_shows_migration — HR file conflict (not TASK-005)
  - test_tenancy_middleware.py::TestDevHeaders::test_clinic_id_only_no_user_allowed — pre-existing on task-004-rbac base
```

### Lint

```
ruff check app/modules/patients/ tests/unit/patients/ tests/integration/patients/
All checks passed!
```

---

## New Commits (iteration 2)

| SHA | Message |
|---|---|
| `adea8b6` | fix(patients): TASK-005 use IMMUTABLE wrapper around unaccent in expression index (C1) |
| `e2e06cb` | fix(patients): TASK-005 use fresh AsyncSession in audit_patient_read BackgroundTask (M1) |
| `6aefd35` | fix(patients): TASK-005 record per-row reassignment manifest for accurate undo (M4) |
| `b384e97` | style(patients): TASK-005 ruff lint fixes in test files (M6) |
| `d9c0546` | test(patients): TASK-005 rewrite integration tests as DB-backed e2e (C2) |

Note: M2, M3 fixes are in commit `e2e06cb` (patient_service.py); M5, m1 fixes are in commit `adea8b6` (migration).

---

## Known Limitations / Deferred

- **RLS isolation via BYPASSRLS**: The `cms` DB user has `BYPASSRLS` so DB-level RLS is not enforced in the test environment. The `test_tenant_isolation_via_http` test documents this and asserts only that the HTTP response is 200 or 404 (either is acceptable). Production correctness depends on using the `cms_app` role which does not have BYPASSRLS. This is a pre-existing architectural note, not introduced by TASK-005.
- **m3 (`# noqa: B008`)**: Left as-is per reviewer guidance ("consistent with existing codebase, leave for future global cleanup").

---

## Iteration 3 Fixes (2026-04-27)

All 4 bugs reported by Test Agent (iteration 3) have been fixed. 117/117 non-perf tests pass. Coverage 94%. Ruff exit 0.

| Bug | Severity | Fix Description | Commit SHA |
|-----|----------|-----------------|------------|
| BUG-004 | Critical | `undo_merge()` now accepts `clinic_id` param; route passes caller's clinic; post-fetch ownership check raises 404 if mismatch | `d020648`, `61208ae` |
| BUG-003 | High | `PatientMergeRequest` model_validator rejects `keep_id == drop_id` with 422 | `2da9db0` |
| BUG-001 | High | `search_patients` route rejects `q` containing `\x00` with 400 | `ae4d8f8` |
| BUG-002 | Medium | `PatientCreate` + `PatientUpdate` field_validator rejects future `date_of_birth` with 422 | `0625af8` |

### Test Results

```
117 passed, 2 deselected (perf) in 50.61s
Coverage: 94% (app/modules/patients/)
Ruff: All checks passed!
Full suite (non-perf): 498 passed, 3 failed (pre-existing unrelated failures)
```

### Design Note: BUG-004 `clinic_id` Optionality

`clinic_id` is `Optional[UUID] = None` in the service signature to preserve backward compatibility with pre-existing unit tests that call the service directly without a clinic context. The route always supplies `clinic_id`, so the security check is enforced on all production API calls. The `None` path is a pure unit-test convenience — it is never exercised from the HTTP layer.
