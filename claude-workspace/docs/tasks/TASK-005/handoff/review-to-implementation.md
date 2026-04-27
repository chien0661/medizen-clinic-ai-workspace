# Handoff: TASK-005 → Code Implementation Agent

**From:** Code Review Agent
**To:** Code Implementation Agent
**Status:** IN_PROGRESS (iteration 2)
**Decision:** **CHANGES_REQUESTED**
**Date:** 2026-04-27

## Summary

Iteration 1 has solid module structure, correct permission gating, accurate audit-PII exclusion, and 85 passing tests at 98 % coverage. **However**, two CRITICAL issues block approval: the migration cannot be applied to a clean database (PG `unaccent` is not IMMUTABLE inside the GIN expression index), and the "integration" suite is mock-only — explicitly disallowed by `PROJECT.md` per the TASK-004 iter-1 precedent. Six MAJOR issues mean the documented ACs around search performance, fuzzy-match robustness, undo correctness, and audit-on-read are not actually delivered.

Full findings with rationale, code locations, and suggested fixes: `docs/tasks/TASK-005/handoff/review-report.md`.

---

## Required Changes — fix all CRITICAL + MAJOR before re-submission

### CRITICAL — must fix

#### C1. Make migration 0008 actually apply to a clean DB
**File:** `clinic-cms/alembic/versions/0008_create_patients.py:125-132`

Stock Postgres ships `unaccent(text)` as `STABLE`. PG refuses GIN expression indexes on non-IMMUTABLE functions:

```
asyncpg.exceptions.InvalidObjectDefinitionError: functions in index expression must be marked IMMUTABLE
[SQL: CREATE INDEX gix_patient_name_search ON patient USING gin (to_tsvector('simple', unaccent(full_name))) WHERE NOT is_deleted]
```

This is reproducible live (I ran `alembic upgrade head` against `clinic_cms_postgres` from 0007 and it failed).

**Fix:**
1. Inside `upgrade()`, after `CREATE EXTENSION`, add an IMMUTABLE wrapper:
   ```sql
   CREATE OR REPLACE FUNCTION immutable_unaccent(text)
     RETURNS text
     LANGUAGE sql
     IMMUTABLE
     STRICT
     PARALLEL SAFE
   AS $$ SELECT unaccent('public.unaccent', $1) $$;
   ```
2. Use it in the GIN index expression: `to_tsvector('simple', immutable_unaccent(full_name))`.
3. Also update the search query in `app/modules/patients/services/patient_service.py:253` to call `immutable_unaccent` (or add a helper in `core/db.py` that wraps it via `func.immutable_unaccent`).
4. Add `DROP FUNCTION IF EXISTS immutable_unaccent(text);` to `downgrade()`.
5. Verify locally: `alembic downgrade base && alembic upgrade head && alembic downgrade -1 && alembic upgrade head` — all must succeed. The pre-existing test `tests/integration/test_alembic.py::test_alembic_upgrade_head_is_idempotent` must pass.

#### C2. Replace mock-only "integration" suite with real DB-backed e2e tests
**File:** `clinic-cms/tests/integration/patients/test_patients_api.py` (whole file)

PROJECT.md §Project-Specific Overrides #4: "Integration tests must hit real Postgres + Redis. Mock-only 'integration' tests will be rejected at review (TASK-004 iteration 1 precedent)." The current file builds a mini `FastAPI()` app, overrides `get_db` with `AsyncMock`, and `unittest.mock.patch`-es every service.

**Fix:** rewrite as real e2e tests modelled on `tests/integration/test_rbac_e2e_real_db.py`:
- Import from `app.main:app` (the real app), use a real `httpx.AsyncClient`.
- Use the existing test fixtures that bootstrap a real clinic + user + JWT (see how `test_rbac_e2e_real_db.py` does it).
- Cover at minimum: create + duplicate-warning, search by all three types (with seeded data — and use the `nguyen vn an` → `Nguyễn Văn An` AC explicitly), guardian add/list/remove, merge happy path, merge cross-tenant 403, merge then undo within window, merge then undo expired (mutate `undo_deadline` to past), audit log row written for read, RLS isolation (clinic-A user cannot see clinic-B patients).
- Unit tests with `AsyncMock` are fine where they are now (`tests/unit/patients/`) — keep them. The replacement is for the *integration* directory only.

### MAJOR — must fix

#### M1. `audit_patient_read` BackgroundTask uses a closed AsyncSession
**File:** `app/modules/patients/api/routes.py:172`; `app/modules/patients/services/patient_service.py:287-301`

`get_db()` commits and closes the session before the BackgroundTask runs. The audit write fails silently (caught at `app/core/audit.py:201`).

**Fix:** change the signature so the background task does not depend on the request session.
```python
# patient_service.py
from app.core.db import AsyncSessionLocal

async def audit_patient_read(
    patient_id: UUID,
    clinic_id: UUID,
    user_id: UUID,
) -> None:
    async with AsyncSessionLocal() as session:
        # set RLS context
        await session.execute(text(f"SET LOCAL app.current_clinic_id = '{clinic_id}'"))
        if user_id:
            await session.execute(text(f"SET LOCAL app.current_user_id = '{user_id}'"))
        await write_audit(session, action="READ", entity_type="Patient", entity_id=patient_id)
        await session.commit()
```
And in routes:
```python
background_tasks.add_task(
    patient_service.audit_patient_read,
    patient.id, clinic_id, user_id,
)
```
Add an integration test that calls `GET /patients/{id}` and asserts a `READ` row landed in `audit_log`.

#### M2. Phone search cannot meet AC `< 100ms @ 100k`
**Files:** `app/modules/patients/services/patient_service.py:237`; `alembic/versions/0008_create_patients.py:118-122`

`Patient.phone.ilike(f"%{q}%")` cannot use the btree partial index — sequential scan. Pick **one** of:
1. Add a trigram index in 0008 (`CREATE INDEX gix_patient_phone_trgm ON patient USING gin (phone gin_trgm_ops)`) and rewrite the phone branch to use `phone % :q` similarity.
2. Switch to anchored matches (`phone = :q OR phone LIKE :q || '%'`) — both DO use `ix_patient_clinic_phone`. Document the UX implication (no infix search) in the route docstring.
3. Add a perf test to the test plan — load 100k rows in a fixture and assert `< 100 ms`.

#### M3. `to_tsquery` crashes on apostrophes / special chars
**File:** `app/modules/patients/services/patient_service.py:253-254`

`to_tsquery` is not a sanitiser. User-supplied `O'Brien` → 500.

**Fix:** use `plainto_tsquery` (or `websearch_to_tsquery`) which sanitises and ANDs terms automatically:
```python
func.to_tsvector("simple", func.immutable_unaccent(Patient.full_name)).op("@@")(
    func.plainto_tsquery("simple", func.immutable_unaccent(q))
)
```
Add a unit test: `search_patients(q="O'Brien", search_type="name")` must not raise.

#### M4. Undo over-reassigns rows that originally belonged to keep_patient
**File:** `app/modules/patients/services/merge_service.py:151-158, 255-266`

The current undo blindly moves all rows currently on `keep_id` to `drop_id`. Rows that originally belonged to `keep_patient` get moved as collateral damage.

**Fix:** at merge time, capture the IDs of every row reassigned, per (table, fk_col), into `patient_merge_log.source_patient_data` (or a new sibling JSONB column `reassigned_refs`). On undo, iterate that map and only `UPDATE table SET fk = drop_id WHERE id = ANY(:ids)`. Add a test where keep_patient has its own pre-existing relation; after merge → undo, that relation must still belong to keep_patient.

#### M5. Unique-code conflict on undo (drop_patient code may collide with new patients)
**Files:** `alembic/versions/0008_create_patients.py:144-150, 294-321`

`fn_next_patient_code` filters `WHERE NOT is_deleted`. After merge, drop_patient's code is invisible — a new patient created during the 7-day window can take it. Undo will violate `uq_patient_clinic_code`.

**Fix (preferred):** change `fn_next_patient_code` to consider **all** rows (drop the `NOT is_deleted` filter for the MAX lookup) — codes are never reused, even after soft-delete.

Alternative: detect the collision at undo time and append a suffix to `drop_patient.patient_code` (e.g. `BN0007-RESTORED`), surface this in the response.

Add a test: merge → create a new patient → assert new code != drop_patient's code. Then undo — must succeed without `IntegrityError`.

#### M6. 11 ruff lint errors in test files
Run `ruff check --fix` then manually clean unused locals:
- `tests/integration/patients/test_patients_api.py`: drop `from typing import Any` (line 19), drop `as mock_search` (line 398).
- `tests/unit/patients/test_guardian_service.py`: drop `rel = ` prefix (line 53).
- `tests/unit/patients/test_merge_service.py`: drop `ForbiddenError` import (line 19), drop `merge_log = ` (line 104), drop `result = ` (line 193).
- `tests/unit/patients/test_patient_schemas.py`: drop `PatientMergeRequest` import (line 21).
- `tests/unit/patients/test_patient_service.py`: drop `datetime`, `timezone`, `call` imports (lines 16-17), drop `result = ` (line 193).

Final state: `docker exec clinic_cms_api ruff check app tests` → exit 0.

---

## MINOR (nice-to-have, not blocking but flag for next iteration)

- **m1.** `fn_next_patient_code` lexical MAX breaks when crossing 4-digit→5-digit width. Consider switching to `MAX(CAST(SUBSTRING(patient_code FROM 3) AS INTEGER))`.
- **m2.** `tests/unit/patients/test_merge_service.py:243` — `test_captures_all_columns` is sync but receives `pytest.mark.asyncio` from class-level mark. Move out of the class or drop the mark.
- **m3.** Repeated `# noqa: B008` on every `Depends(get_db)` — consistent with the existing codebase, so leave for a future global cleanup.

---

## Verification before resubmitting

Please run **all** of these on a clean container (no leftover state) and report results in the next handoff:

```bash
# 1. Migration round-trip
docker exec clinic_cms_postgres psql -U cms cms -c "TRUNCATE alembic_version;"  # or fresh DB
docker exec clinic_cms_api alembic upgrade head
docker exec clinic_cms_api alembic downgrade -1
docker exec clinic_cms_api alembic upgrade head

# 2. Full test suite, no exclusions
docker exec clinic_cms_api pytest -q --tb=short

# 3. Lint
docker exec clinic_cms_api ruff check app tests

# 4. Patient-module coverage
docker exec clinic_cms_api pytest --cov=app/modules/patients --cov-report=term tests/{unit,integration}/patients/
```

Expected: all pass; coverage stays ≥ 80 % on new files; alembic round-trips cleanly; ruff exit 0.

---

## Out of scope / accepted

- Pre-existing test failure `tests/unit/test_tenancy_middleware.py::TestDevHeaders::test_clinic_id_only_no_user_allowed` — confirmed present on `feature/task-004-rbac` base. Not your concern in this iteration.
- mypy not in the container image — relied on static review for type-correctness. No findings.
