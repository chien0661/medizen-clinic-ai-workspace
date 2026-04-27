# Code Review: TASK-005 — Patient Management (CRUD + Guardian + Search + Merge)

**Reviewer:** Code Review Agent
**Date:** 2026-04-27
**Branch:** `feature/task-005-patients` (HEAD `a79981d`, branched from `feature/task-004-rbac`)
**Iteration:** 1
**Status:** **CHANGES_REQUESTED**

---

## TL;DR

| Severity | Count | Examples |
|---|---|---|
| **CRITICAL** | **2** | Migration 0008 fails (`unaccent` not IMMUTABLE in GIN index expression); "Integration" tests are mock-only — violates PROJECT.md §Project-Specific Overrides #4 (TASK-004 iter-1 precedent) |
| **MAJOR** | **6** | `audit_patient_read` background task uses already-closed session; phone search uses `ILIKE '%q%'` over btree (cannot meet AC < 100ms @ 100k); `to_tsquery` crashes on user-supplied apostrophes/special chars; undo over-reassigns rows that originally belonged to keep_patient (violates undo AC); unique-code collision risk between merge and undo via `fn_next_patient_code`; 11 ruff lint errors in test files (PROJECT.md `Lint must pass: true`) |
| **MINOR** | **3** | `fn_next_patient_code` lexical-MAX breaks at code-width transition (BN9999 → BN10000); `@pytest.mark.asyncio` on sync test method; unused-import / `B008` `# noqa` overuse in tests |

**Verdict:** **CHANGES_REQUESTED** — two CRITICALs reproduced at the database / test-strategy level; six MAJORs touch correctness of search, merge undo, and audit. The codebase is well-structured and the unit tests are thoughtful, but several core ACs (search performance, fuzzy match robustness, undo correctness, audit-on-read) are not actually delivered. Migration 0008 cannot be applied to a clean database.

---

## Review Summary

- **Files Reviewed:** 22 changed (3,180 LOC additions)
- **Test results actually observed:** 85 passed, 0 failed (59 unit + 26 integration). Confirmed reproducibility from the branch in the existing Docker stack.
- **Coverage actually observed:** 98% on `app/modules/patients/` (467 stmts, 9 missed). Matches handoff.
- **Lint:** App code clean; **test code has 11 ruff errors** (`F401`, `F841`).
- **Type check:** mypy not installed in container; static review only.
- **Migration round-trip:** **`alembic upgrade head` FAILS on a clean database** with `InvalidObjectDefinitionError: functions in index expression must be marked IMMUTABLE` (see CRITICAL #1). The test `tests/integration/test_alembic.py::test_alembic_upgrade_head_is_idempotent` (pre-existing) **regresses** on this branch.
- **Pre-existing failure unrelated to TASK-005:** `tests/unit/test_tenancy_middleware.py::TestDevHeaders::test_clinic_id_only_no_user_allowed` — present on `feature/task-004-rbac` already; not blocking this review.

---

## CRITICAL Findings

### C1. Migration 0008 fails on clean DB — `unaccent` is not IMMUTABLE
**File:** `clinic-cms/alembic/versions/0008_create_patients.py:125-132`
**Severity:** CRITICAL — blocks deployment, breaks pre-existing alembic round-trip test.

**What's wrong:**
```sql
CREATE INDEX gix_patient_name_search
  ON patient
  USING gin (to_tsvector('simple', unaccent(full_name)))
  WHERE NOT is_deleted
```
`unaccent(text)` is `STABLE`, not `IMMUTABLE`, in stock PostgreSQL. PG refuses to create a functional index on a non-IMMUTABLE function. Reproduced live:

```
sqlalchemy.exc.ProgrammingError: <class 'asyncpg.exceptions.InvalidObjectDefinitionError'>:
functions in index expression must be marked IMMUTABLE
[SQL: CREATE INDEX gix_patient_name_search ON patient USING gin (to_tsvector('simple', unaccent(full_name))) WHERE NOT is_deleted]
```

Confirmed via `docker exec clinic_cms_postgres psql -c "\df+ unaccent"` → `Volatility: stable`.

This breaks `tests/integration/test_alembic.py::test_alembic_upgrade_head_is_idempotent` which previously passed.

**Why it matters:** the migration cannot be applied to any clean environment (CI, staging, prod). Search by name is non-functional. AC "fuzzy theo tên (vd 'nguyen vn an') match được 'Nguyễn Văn An'" is undeliverable.

**Suggested fix:** wrap `unaccent` in a custom IMMUTABLE wrapper (canonical Postgres pattern):
```sql
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
  RETURNS text
  LANGUAGE sql
  IMMUTABLE
  STRICT
  PARALLEL SAFE
AS $$ SELECT unaccent('public.unaccent', $1) $$;

CREATE INDEX gix_patient_name_search
  ON patient
  USING gin (to_tsvector('simple', immutable_unaccent(full_name)))
  WHERE NOT is_deleted;
```
Then update the search query in `patient_service.py:253` to use `immutable_unaccent`. Add an alembic round-trip test that exercises 0008 in CI.

---

### C2. "Integration" tests are mock-only — violates PROJECT.md
**File:** `clinic-cms/tests/integration/patients/test_patients_api.py:42-78` (entire file)
**Severity:** CRITICAL — explicit project-level rule, with TASK-004 precedent.

**What's wrong:** the file builds a custom mini-`FastAPI()` app (line 42), overrides `get_db` with `_mock_db_session = AsyncMock()` (line 124), and patches every service call with `unittest.mock.patch`. No real Postgres, no RLS, no real `register_tenancy_middleware`, no real `register_permission`. PROJECT.md says verbatim:

> **Integration tests**: must hit real Postgres + Redis. Mock-only "integration" tests will be rejected at review (TASK-004 iteration 1 precedent).

The 26 "integration" tests that the handoff reports as passing are functionally **unit tests with HTTP wrapping**.

**Why it matters:** none of the actually-risky integration concerns are exercised — RLS isolation under merge, real `fn_next_patient_code` concurrency, the `gin_trgm_ops` similarity threshold, real BackgroundTask audit behaviour, real exception handler wiring through the production `app.main:app`. The 98 % coverage figure includes lines whose runtime behaviour is mocked.

**Suggested fix:** rewrite as DB-backed e2e tests against `app.main:app` using `httpx.AsyncClient` and the existing `clinic_cms_postgres` / `clinic_cms_redis` containers, following `tests/integration/test_rbac_e2e_real_db.py`. Cover at minimum: create + search + merge + undo + cross-tenant + duplicate-warning + RLS denial.

---

## MAJOR Findings

### M1. `audit_patient_read` BackgroundTask uses an already-closed AsyncSession
**File:** `clinic-cms/app/modules/patients/api/routes.py:172`
**Severity:** MAJOR — feature silently does not work; audit-on-read AC unmet.

**What's wrong:**
```python
@router.get("/patients/{patient_id}", ...)
async def get_patient(patient_id, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    patient = await patient_service.get_patient(db, patient_id)
    background_tasks.add_task(patient_service.audit_patient_read, db, patient)
    return PatientResponse.model_validate(patient)
```
`get_db()` (`app/core/db.py:27`) yields the session, then on return runs `await session.commit()` and exits the `async with` block — **closing** the session. FastAPI runs `BackgroundTasks` **after** the response is sent (i.e., after `get_db()` finalises). The background task therefore writes audit on a **closed** session. Inside `write_audit` (`app/core/audit.py:201`) the exception is swallowed. Net effect: every patient read silently skips the audit.

**Why it matters:** task brief explicitly requires "Audit log cho `patient.read` (async)". The unit test at `test_patient_service.py:333` calls `audit_patient_read` directly with a mock db, never exercising the real lifecycle. The "integration" test at `test_patients_api.py:563` mocks `audit_patient_read` itself — neither catches the bug.

**Suggested fix:** use a **fresh** session inside the BackgroundTask (open `AsyncSessionLocal()` inside `audit_patient_read`), or write the audit synchronously before returning. The "fresh session" pattern matches `app/core/audit.py` `write_audit` signature — pass `entity_id` instead of the patient ORM, open a new session, set the RLS context vars (which still live in ContextVar), write, commit, close.

---

### M2. Phone search cannot meet AC `< 100ms @ 100k patients`
**Files:** `clinic-cms/app/modules/patients/services/patient_service.py:237`; `clinic-cms/alembic/versions/0008_create_patients.py:118-122`
**Severity:** MAJOR — explicit AC failure.

**What's wrong:** the phone branch uses `Patient.phone.ilike(f"%{q}%")` (substring with leading wildcard). The only phone-related index is the partial **btree** `ix_patient_clinic_phone (clinic_id, phone) WHERE NOT is_deleted`. A btree index cannot serve `ILIKE '%foo%'` — Postgres falls back to a sequential scan. With 100k rows this will not return in < 100 ms.

The service's docstring at line 7 even claims "fast: ix_patient_clinic_phone" — incorrect.

**Why it matters:** AC1 of TASK-005 is "Search theo SĐT 10 chữ số trả < 100ms khi DB có 100k patient".

**Suggested fix (one of):**
1. Add a trigram index on phone: `CREATE INDEX gix_patient_phone_trgm ON patient USING gin (phone gin_trgm_ops)` and rewrite the query to use `phone % :q` similarity (or `LIKE`/`ILIKE`-on-trgm).
2. If the typical UX is "exact 10-digit" or "trailing N-digit" search, change to anchored matches (`phone = :q` or `phone LIKE :q || '%'`) which DO use the existing btree index.
3. Benchmark in the test plan with 100k seeded rows — currently no perf test exists.

---

### M3. `to_tsquery` crashes on user input containing apostrophes / special chars
**File:** `clinic-cms/app/modules/patients/services/patient_service.py:253-254`
**Severity:** MAJOR — DoS / 500-error vector on a public route.

**What's wrong:**
```python
func.to_tsquery("simple", func.unaccent(q.replace(" ", " & ")))
```
`to_tsquery` requires its input to be a valid tsquery string. User input containing `'`, `&` (multiple), `:`, `(`, `!`, etc. throws `syntax error in tsquery`. Example: searching for `O'Brien` produces `to_tsquery('simple', unaccent("O'Brien"))` → 500 error.

**Why it matters:** the endpoint is permissioned with `patient.read` — any clinic-staff user can trigger 500s by typing apostrophes in the search box, or worse, repeated invalid queries to spike error rates.

**Suggested fix:** use `plainto_tsquery` (or `websearch_to_tsquery`) which sanitises input; OR sanitise manually by stripping non-alphanumeric chars before `replace(" ", " & ")`. Ensure the trgm fallback still runs even if ts_query fails (current code raises before the trgm path). Add a unit test: `search_patients(q="O'Brien", search_type="name")` must not raise.

---

### M4. Undo over-reassigns rows that originally belonged to keep_patient
**File:** `clinic-cms/app/modules/patients/services/merge_service.py:255-266`
**Severity:** MAJOR — violates AC "Undo merge trong 7 ngày khôi phục đúng trạng thái cũ".

**What's wrong:** undo runs:
```sql
UPDATE {table} SET {fk} = :drop_id WHERE {fk} = :keep_id
```
This reassigns **all** rows currently pointing to `keep_id` back to `drop_id` — including rows that were originally on `keep_id` before the merge. The handoff itself acknowledges this ("This is an accepted limitation for v1 ... could reassign rows that naturally point to keep_patient"), but the AC says undo restores the previous state, which is now incorrect.

**Why it matters:** for a clinic with two patients merged where each had separate visit history, undoing the merge swaps the keep-patient's visits onto the drop-patient — silent data corruption that the user thinks is a recovery operation.

**Suggested fix:** snapshot the **list of reassigned row IDs per (table, fk)** at merge time into `patient_merge_log.source_patient_data` (or a sibling JSONB column `reassigned_refs: {table: [id, ...]}`). On undo, only revert rows whose IDs were captured. Add an explicit test where keep_patient has its own pre-existing relation row and verify it is **not** moved on undo.

---

### M5. Unique-code collision risk between soft-deleted drop_patient and new patients
**Files:** `clinic-cms/alembic/versions/0008_create_patients.py:294-321` (`fn_next_patient_code`); `0008_create_patients.py:144-150` (`uq_patient_clinic_code`)
**Severity:** MAJOR — undo can fail with unique-violation.

**What's wrong:** `fn_next_patient_code` selects `MAX(patient_code) WHERE NOT is_deleted` and increments it. The unique index `uq_patient_clinic_code` is `WHERE NOT is_deleted`. After a merge, drop_patient is soft-deleted and its code (say `BN0007`) becomes invisible to both the lookup and the partial unique index. A new patient created during the 7-day undo window can legitimately receive `BN0007` again. When `undo_merge` un-soft-deletes drop_patient (`is_deleted = False`), the partial unique index now sees two rows with `(clinic_id, BN0007)` → `IntegrityError`.

**Why it matters:** the undo path will fail intermittently in production, exactly when the user needs to recover from a wrong merge.

**Suggested fix (one of):**
1. Change `fn_next_patient_code` to consider **all** rows (incl. soft-deleted) for MAX — codes are never reused.
2. Or: at undo time, detect the conflict and append a suffix (`-RESTORED-1`) to drop_patient.patient_code, document this UX, and surface it in the response.
3. Add a unit/integration test: merge → create new patient → assert new code != drop_patient's code. Then undo → must succeed.

---

### M6. Eleven ruff lint errors in test files; PROJECT.md requires lint to pass
**Files:** `tests/integration/patients/test_patients_api.py` (2 errors); `tests/unit/patients/test_guardian_service.py` (1); `tests/unit/patients/test_merge_service.py` (3); `tests/unit/patients/test_patient_schemas.py` (1); `tests/unit/patients/test_patient_service.py` (4)
**Severity:** MAJOR — explicit quality gate.

**What's wrong:** `ruff check tests/unit/patients tests/integration/patients` reports 11 violations:
- `F401` unused imports: `typing.Any`, `ForbiddenError`, `PatientMergeRequest`, `datetime`, `timezone`, `unittest.mock.call`
- `F841` unused locals: `mock_search`, `rel`, `merge_log`, `result` (×2)

PROJECT.md §Quality Gates: `Lint must pass: true`. App-code itself is clean — only tests fail. Production code passes ruff.

**Suggested fix:** `ruff check --fix` handles 6/11 directly; the rest are unused-local assignments — drop the `result =` prefix or assert on it.

---

## MINOR Findings

### m1. `fn_next_patient_code` lexical-MAX breaks across width transitions
**File:** `0008_create_patients.py:304-310`
With LPAD(4) the code stays sortable up to BN9999. After BN9999 → BN10000, lexical comparison still works because longer-string > shorter-prefix. But once BN10000 exists, `MAX('BN10000', 'BN9999')` is `'BN9999'` lexically (because `'9' > '1'`). Increment becomes BN10000 → conflict. Latent bug; only triggers above 10k patients in one clinic. Switch to `MAX(CAST(SUBSTRING(patient_code FROM 3) AS INTEGER))` for numeric ordering.

### m2. Sync test method marked `@pytest.mark.asyncio`
**File:** `tests/unit/patients/test_merge_service.py:243`
`test_captures_all_columns` is sync but receives the asyncio mark via class-level pytestmark (warning observed at runtime). Move it out of the class or drop the mark.

### m3. Repeated `# noqa: B008` and unused-arg patterns in routes
**File:** `app/modules/patients/api/routes.py` (every route)
Every `db: AsyncSession = Depends(get_db)` has `# noqa: B008`. This is consistent with the existing codebase pattern, so not a blocker — just noting it. If a project-wide `Annotated[AsyncSession, Depends(get_db)]` alias exists or is desired, switching avoids the noqa.

---

## Build Verification — Actually Observed

| Check | Observed | Notes |
|---|---|---|
| `pytest -q tests/unit/patients tests/integration/patients` | **85 passed** | Matches handoff. |
| `pytest --cov=app/modules/patients tests/{unit,integration}/patients/` | **98 %** (467 stmts, 9 missed) | Matches handoff. |
| `pytest -q --tb=line` (full suite, excluding unrelated HR remnants) | **372 passed, 2 failed** | 1 failure = `test_alembic_upgrade_head_is_idempotent` (regression caused by C1); 1 failure = pre-existing tenancy middleware test on TASK-004 base. |
| `ruff check app/modules/patients` | **clean** | App code is clean. |
| `ruff check tests/{unit,integration}/patients` | **11 errors** | See M6. |
| `mypy app/modules/patients` | not run | mypy not in image; relied on static review. |
| `alembic upgrade head` (clean DB) | **FAIL** | C1 — `unaccent` not IMMUTABLE. Reproduced live. |
| `alembic downgrade -1` round-trip | **not exercised** | Upgrade fails before downgrade can be tested. |

---

## Permission Gating Audit

Every route in `app/modules/patients/api/routes.py` has a `Depends(require_permission(...))` dependency:

| Route | Method | Permission |
|---|---|---|
| `/api/v1/patients` | GET | `patient.read` |
| `/api/v1/patients` | POST | `patient.write` |
| `/api/v1/patients/search` | GET | `patient.read` |
| `/api/v1/patients/{id}` | GET | `patient.read` |
| `/api/v1/patients/{id}` | PATCH | `patient.write` |
| `/api/v1/patients/{id}` | DELETE | `patient.delete` |
| `/api/v1/patients/{id}/guardians` | POST | `patient.write` |
| `/api/v1/patients/{id}/guardians` | GET | `patient.read` |
| `/api/v1/patients/guardians/{rel_id}` | DELETE | `patient.write` |
| `/api/v1/patients/merge` | POST | `patient.merge` |
| `/api/v1/patients/merge/{merge_id}/undo` | POST | `patient.merge` |

All 11 routes are protected. Patient permissions confirmed seeded in `alembic/versions/0007_seed_permissions_and_roles.py` (lines 32-35). Router registered in `app/main.py:19,51` (verified via diff).

---

## Positive Observations

- Module structure follows the established `auth/`, `users/` layout precisely.
- `Patient.__audit_exclude__ = frozenset({"id_number"})` correctly excludes CCCD/CMND from audit log snapshots (verified at `app/modules/patients/models/patient.py:30`).
- Cross-tenant guard implemented in `merge_service.merge` (`CrossTenantError` raised when `keep.clinic_id != drop.clinic_id`) with a unit test covering it.
- Undo deadline / `MergeUndoExpiredError` returns HTTP 410 — correct status code for the AC.
- Duplicate-warning UX is implemented as a soft `warnings: []` field in the create response (HTTP 201) rather than a 409 — matches the spec ("warn but don't block").
- Merge log captures a JSONB snapshot of drop_patient before mutation — good basis for undo restoration of the row itself.
- All 11 routes correctly registered behind `require_permission`; `patient.read/write/merge/delete` already in the seed.
- `RELATED_PATIENT_TABLES` registry pattern is a clean extensibility hook — the comment-out hints (`# TASK-007: ('visit', 'patient_id')`) show forethought.

---

## Decision

**CHANGES_REQUESTED.**

The two CRITICAL items (broken migration, mock-only integration tests) must be fixed before this can move to testing — both are independently sufficient grounds for rejection per project rules. The MAJOR items collectively mean that several documented ACs (search performance, fuzzy match robustness, undo correctness, audit-on-read) are not actually delivered in iteration 1 even though tests pass.

The good news: the module structure, models, schemas, permissions, and routing are well done. The fixes are localised — most are within the migration, the search query, the merge/undo SQL, and the audit BackgroundTask wiring.

## Next Steps

1. Fix C1: wrap `unaccent` in an IMMUTABLE function inside the migration (and update the search query). Verify `alembic upgrade head` works on a clean DB.
2. Fix C2: convert `tests/integration/patients/test_patients_api.py` into real DB-backed e2e tests against `app.main:app`.
3. Fix M1: open a fresh session inside `audit_patient_read` and write/commit there.
4. Fix M2: add a trigram index on `phone` and rewrite the phone branch (or anchor the search).
5. Fix M3: switch to `plainto_tsquery` or sanitise input.
6. Fix M4: capture per-table reassigned IDs at merge time; only revert those on undo.
7. Fix M5: change `fn_next_patient_code` to look at all rows (or handle conflict on undo).
8. Fix M6: `ruff check --fix tests/{unit,integration}/patients` plus manual unused-local cleanup.
9. Re-run `pytest -q` and `alembic upgrade head` from a clean DB.
10. Resubmit for review with iteration 2.

**Review Time:** ~75 minutes (including live DB reproduction of C1).

---

## Iteration 2 Review

**Reviewer:** Code Review Agent
**Date:** 2026-04-27
**Branch:** `feature/task-005-patients` (HEAD `d9c0546`)
**Iter-1 baseline:** `a79981d`. Iter-2 commits: `adea8b6 → e2e06cb → 6aefd35 → b384e97 → d9c0546`.
**Verdict:** **APPROVED** → status `IN_TESTING`.

### Per-finding verification

| ID | Severity | Status | Commit | Verification |
|----|----------|--------|--------|--------------|
| **C1** | CRITICAL | **RESOLVED** | `adea8b6` | `immutable_unaccent(text)` SQL function (IMMUTABLE STRICT PARALLEL SAFE) added in `upgrade()`; `gix_patient_name_search` now uses it; `DROP FUNCTION` added to `downgrade()`. Live verified: `\df+ immutable_unaccent` → Volatility immutable. Migration round-trip clean (see below). |
| **C2** | CRITICAL | **RESOLVED** | `d9c0546` | `tests/integration/patients/test_patients_api.py` rewritten — 18 real e2e tests against `app.main:app` via `httpx.AsyncClient` + live PG/Redis. Zero `AsyncMock`/`unittest.mock.patch`/mini-FastAPI. Modelled on `test_rbac_e2e_real_db.py`. Confirmed by grep: no mock primitives in file. |
| **M1** | MAJOR | **RESOLVED** | `e2e06cb` | `audit_patient_read(patient_id, clinic_id, user_id)` opens fresh `AsyncSessionLocal()`, sets RLS via `SET LOCAL`, writes audit, commits, closes. Route passes plain UUIDs to BackgroundTask. Integration test `test_get_patient_writes_audit_read_row` verifies audit row landed. |
| **M2** | MAJOR | **RESOLVED** | `adea8b6` (migration) + `e2e06cb` (service) | Added `gix_patient_phone_trgm ON patient USING gin (phone gin_trgm_ops) WHERE NOT is_deleted`. Phone branch uses `Patient.phone.op("%")(q)` + `ORDER BY similarity(phone,q) DESC`. Index confirmed live in `\d+ patient`. Note: throughput at 100k still wants the test agent's perf-bench validation. |
| **M3** | MAJOR | **RESOLVED** | `e2e06cb` | `to_tsquery` → `plainto_tsquery("simple", func.immutable_unaccent(q))`. Sanitises arbitrary input. Integration test `test_search_by_name_apostrophe_does_not_500` exercises `O'Brien`. |
| **M4** | MAJOR | **RESOLVED** | `6aefd35` | `merge()` collects `SELECT id WHERE fk = drop_id` per (table,fk_col) before reassign, persists list as `source_patient_data["reassigned_refs"]`. `undo_merge()` reverts only those IDs via `UPDATE ... WHERE id = ANY(:ids)`. Legacy fallback for older logs retained (no manifest). Integration test `test_undo_does_not_reassign_keep_patient_own_relations` asserts keep-patient's pre-existing relation is untouched after undo. |
| **M5** | MAJOR | **RESOLVED** | `adea8b6` | `fn_next_patient_code` body: `SELECT MAX(CAST(SUBSTRING(patient_code FROM 3) AS INTEGER)) FROM patient WHERE clinic_id = p_clinic_id` — no `is_deleted` filter. Codes never reused. Verified live in `\df+ fn_next_patient_code`. Integration test `test_patient_code_not_reused_after_merge_and_undo_succeeds` asserts new code != drop_code AND undo succeeds without IntegrityError. |
| **M6** | MAJOR | **RESOLVED** | `b384e97` | All 11 ruff violations cleared. `ruff check app/modules/patients/ tests/unit/patients/ tests/integration/patients/` → "All checks passed!". |
| **m1** | MINOR | **RESOLVED** | `adea8b6` | Numeric-MAX fix (M5) also addresses lexical-ordering bug at BN9999→BN10000 boundary. |
| **m2** | MINOR | **RESOLVED** | `b384e97` | `test_captures_all_columns` converted to `async def`. |
| **m3** | MINOR | **DEFERRED** | — | Per iter-1 reviewer note ("consistent with codebase, leave for future global cleanup"). Not a blocker. |

### Per-commit summary

- `adea8b6` — C1 + M2 (migration index) + M5 + m1 (`fn_next_patient_code`). Migration only. Round-trip clean.
- `e2e06cb` — M1 (fresh session) + M2 (phone branch) + M3 (`plainto_tsquery`). Service + route changes only.
- `6aefd35` — M4 (manifest-based undo). Pure merge-service change with backward-compat legacy fallback.
- `b384e97` — M6 + m2. Tests-only, lint-only.
- `d9c0546` — C2 (real e2e suite). Tests-only.

### Build verification — actually observed

| Check | Observed | Iter-2 handoff claim | Match |
|-------|----------|---------------------|-------|
| `pytest -q tests/{unit,integration}/patients/` | **79 passed** in 21.31s | 79/79 | ✅ |
| `pytest --cov=app/modules/patients --cov-report=term ...` | **95 %** (493 stmts, 27 missed) | 95% | ✅ |
| `ruff check app/modules/patients/ tests/{unit,integration}/patients/` | **All checks passed** | exit 0 | ✅ |
| Full suite `pytest -q` (HR files moved aside) | **398 passed, 1 failed** | 396 + 3 pre-existing | ✅ better than claimed (alembic tests pass once HR conflict removed) |
| Pre-existing failure | `test_tenancy_middleware.py::TestDevHeaders::test_clinic_id_only_no_user_allowed` (TASK-004 base) | same | ✅ |

### Migration round-trip — actually observed (HR files moved aside per stash protocol)

```
docker exec clinic_cms_api alembic downgrade 0007  → OK (0008 → 0007)
docker exec clinic_cms_api alembic upgrade head    → OK (0007 → 0008, indexes/function created)
docker exec clinic_cms_api alembic downgrade -1    → OK (0008 → 0007)
docker exec clinic_cms_api alembic upgrade head    → OK (idempotent forward)

\df+ immutable_unaccent             → Volatility=immutable, Parallel=safe ✅
\d+ patient                         → gix_patient_name_search (uses immutable_unaccent),
                                       gix_patient_phone_trgm (gin_trgm_ops), all present
\df+ fn_next_patient_code           → numeric MAX over all rows, no NOT is_deleted filter ✅
```

The user's untracked `0008_create_hr_schedule.py` and `0009_create_patients.py` from TASK-014 WIP cause an alembic multi-head conflict if left in place. They were moved to `/tmp/task005-review-stash/` for round-trip verification and restored afterward. The user's working tree is unchanged — no git operations performed against those files.

### New findings introduced by iter-2 changes

**None.** No new CRITICAL or MAJOR. The 1 deprecation warning surfaced in tests (`ORJSONResponse is deprecated`) is pre-existing FastAPI noise unrelated to this task.

### Notes for the test agent

- Performance: AC1 ("phone search < 100ms @ 100k") is now plausible (trigram index in place) but **not benchmarked**. The test agent should seed ~100k patients and assert latency budget.
- Tenant isolation: `test_tenant_isolation_via_http` documents that `cms` DB role has `BYPASSRLS`. The test agent should verify behaviour with the production `cms_app` role (RLS-enforced) — this is the actual production risk surface for cross-tenant leakage.
- Audit timing: `test_get_patient_writes_audit_read_row` uses `await asyncio.sleep(0.5)` — could be flaky on slow CI. Consider polling instead.
- AC ↔ test mapping is complete: AC1 phone-search-<100ms (deferred to perf bench), AC2 fuzzy "nguyen vn an" → "Nguyễn Văn An" (covered), AC3 guardian primary-contact (covered), AC4 merge reassign visit/prescription/invoice (only `patient_relation` covered — visit/prescription/invoice tables don't exist yet; registry has commented-out hints), AC5 undo restores prior state (covered + M4 manifest-correctness covered), AC6 undo > 7d → 410 (covered).

### Decision

**APPROVED.** Iter-1 had 2 CRIT + 6 MAJ + 3 MIN. Iter-2 resolves all 2 CRIT, all 6 MAJ, and 2 of 3 MIN; the remaining MIN (m3 — `# noqa: B008`) was explicitly deferred at iter-1 review time and is consistent with the rest of the codebase. No regressions, no new findings. Proceed to testing.

**Review Time (iter 2):** ~50 minutes (per-commit verification + live DB round-trip + full test reproduction).

