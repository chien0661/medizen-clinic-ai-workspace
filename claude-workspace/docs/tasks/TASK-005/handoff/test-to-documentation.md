# Handoff: TASK-005 → Documentation Agent

**From:** Test Agent (final regression validation)
**To:** Documentation Agent
**Status:** DOCUMENTING
**Date:** 2026-04-27
**Branch:** `feature/task-005-patients` (HEAD `6e98751`)

---

## Summary

All tests PASS after the iter-3 bug fixes. **117/117 non-perf tests** + **2/2 perf tests** green. Coverage **94%** on `app/modules/patients/`. Migration round-trip clean. Lint clean.

The full review/test/fix cycle history:

| Iter | Phase | Outcome |
|---|---|---|
| 1 | Implementation | 85 tests, 98% coverage (mocks-heavy) |
| 1 | Review | CHANGES_REQUESTED — 2 CRIT + 6 MAJ + 3 MIN. Top hits: migration `unaccent` non-IMMUTABLE, mock-only integration tests, audit BackgroundTask session leak |
| 2 | Implementation (FIX MODE) | 79 tests (rewritten DB-backed e2e), 95% coverage, all CRIT+MAJ resolved |
| 2 | Review | APPROVED |
| 2 | Test | FAILED — 4 bugs filed: BUG-001 null-byte 500, BUG-002 future DOB, BUG-003 self-merge, BUG-004 CRITICAL cross-clinic undo bypass |
| 3 | Implementation (FIX MODE) | 117 tests, 94% coverage, all 4 bugs RESOLVED |
| 3 | Review | APPROVED — narrow verification of 4 fixes |
| 3 | Test (regression) | **117/117 PASS** — handoff to Documentation |

---

## What Documentation needs to cover

Per `.claude/skills/complete-task/` Phase 4:

1. **Functional design document (PRIMARY)** — `claude-workspace/docs/tasks/TASK-005/deliveries/final-specs/patients-functional-design.md`
   - Use template `docs/templates/specs/functional-design-template.md` (Vietnamese, natural language).
   - This task is API-heavy + has data aggregation logic (search, merge), so MOST template sections apply (unlike TASK-017 which was FE-only).
   - Cover: CRUD, search (phone/name/code), guardian relationships, merge + undo with 7-day window, audit log on read, RLS.
   - Section 7 (SQL aggregation) IS applicable — document `fn_next_patient_code`, the GIN+trigram indexes, the search query patterns, and the merge reassignment SQL.

2. **API specs delivery** — `claude-workspace/docs/tasks/TASK-005/deliveries/api-specs/`
   - Document each of the 11 endpoints (CRUD × 5, search × 1, guardian × 3, merge × 2). Path, method, permission, request/response schema, error codes.
   - Permission matrix per endpoint (`patient.read` / `patient.write` / `patient.delete` / `patient.merge`).

3. **SQL scripts delivery** — `claude-workspace/docs/tasks/TASK-005/deliveries/sql-scripts/`
   - Migration `0008_create_patients.py` — copy the SQL/DDL with comments.
   - The `fn_next_patient_code` function body.
   - The `immutable_unaccent` wrapper function.
   - The 4 indexes (phone trgm, name GIN unaccent, name trgm, unique patient_code).
   - RLS policies for `patient`, `patient_relation`, `patient_merge_log`.

4. **Business rules** — embed in functional design Section 8:
   - BR-PAT-001: patient_code format `BN0001` etc., monotonic per clinic, includes soft-deleted in MAX (M5 fix)
   - BR-PAT-002: phone NOT unique, name+DOB NOT unique (warning surfaced in `warnings: []` field, not 409)
   - BR-PAT-003: dob OR birth_year required; if both, year(dob) == birth_year
   - BR-PAT-004: future DOB rejected (BUG-002 fix)
   - BR-PAT-005: id_number (CCCD/CMND) excluded from audit logs (`__audit_exclude__`)
   - BR-PAT-006: search `q` rejects null bytes (BUG-001 fix)
   - BR-MERGE-001: keep_id ≠ drop_id (BUG-003 fix)
   - BR-MERGE-002: same-clinic only (cross-tenant raises NotFoundError)
   - BR-MERGE-003: per-row reassignment manifest stored in `patient_merge_log.source_patient_data.reassigned_refs`
   - BR-MERGE-004: undo within 7 days; after expiry → 410 Gone
   - BR-MERGE-005: undo restricted to same clinic as the merge log (BUG-004 fix)
   - BR-MERGE-006: registry `RELATED_PATIENT_TABLES` extensible by future tasks (TASK-007 visit, TASK-008 appointment, TASK-011 prescription, TASK-013 invoice)

5. **Performance contract** (Section 11 — testing notes):
   - Phone search p95 = **46.9 ms** at 100k patients (AC1 PASS, threshold 100ms)
   - Fuzzy name search p95 = **180.5 ms** (no AC threshold — informational)
   - Migration apply: ~ 200 ms on clean DB

6. **Known deferrals / future work**:
   - Visit/Prescription/Invoice/Appointment tables don't exist yet — merge reassignment registry has placeholders for TASK-007/008/011/013 to extend. Document this clearly.
   - `cms` DB role has `BYPASSRLS` in test DB; production uses `cms_app` (no BYPASSRLS) — RLS verified at DB level under `cms_app`.

---

## Files relevant to documentation scope

**Source (TASK-005 deliverables):**
- `clinic-cms/alembic/versions/0008_create_patients.py`
- `clinic-cms/app/modules/patients/models/{patient,patient_relation,patient_merge_log}.py`
- `clinic-cms/app/modules/patients/schemas/patient_schemas.py`
- `clinic-cms/app/modules/patients/services/{patient_service,guardian_service,merge_service}.py`
- `clinic-cms/app/modules/patients/api/routes.py`
- `clinic-cms/app/main.py` — patients router registration line

**Tests** (for traceability — do NOT document these as deliverables):
- `clinic-cms/tests/unit/patients/`
- `clinic-cms/tests/integration/patients/test_patients_api.py`
- `clinic-cms/tests/integration/patients/test_patients_perf.py`
- `clinic-cms/tests/integration/patients/test_patients_negative.py`
- `clinic-cms/tests/integration/patients/test_patients_merge_advanced.py`
- `clinic-cms/tests/integration/patients/test_patients_audit.py`
- `clinic-cms/tests/integration/patients/test_rls_isolation_cms_app_role.py`

**Existing handoff history:**
- `claude-workspace/docs/tasks/TASK-005/handoff/implementation-to-review.md`
- `claude-workspace/docs/tasks/TASK-005/handoff/review-report.md` (3 iterations of review)
- `claude-workspace/docs/tasks/TASK-005/bugs/BUG-001..004.md`

---

## What is OUT OF SCOPE for Documentation

- The user's HR module work (TASK-014) in untracked working-tree files. Don't touch.
- README updates (the project README hasn't materially changed; let it be).
- Source code changes — Documentation Agent is doc-only.

---

## Quality gate confirmation

| Gate (PROJECT.md) | Threshold | Actual | ✓/✗ |
|---|---|---|---|
| Required Test Pass Rate | 100% | 117/117 (excl. perf) + 2/2 perf | ✓ |
| Unit Tests Required | true | 61 unit + 18 e2e + 38 spec/perf/RLS/audit/merge/neg | ✓ |
| Integration Tests Required | true | DB-backed e2e against `app.main:app` | ✓ |
| Coverage (new code) | ≥ 80% | 94% on `app/modules/patients/` | ✓ |
| Build / Lint Must Pass | true | ruff: 0 errors | ✓ |
| AC1 (perf < 100ms @ 100k) | < 100ms p95 | 46.9 ms p95 | ✓ |

All gates green. Proceed with Phase 4 documentation.
