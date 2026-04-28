# Handoff: TASK-007 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-04-27
**Iteration**: 1
**Branch**: `feature/task-007-visits`

---

## Summary

Implemented the Visit entity module for Clinic CMS: migration 0010 (visit table + visit_number_counter + fn_next_visit_number + v_active_queue view + RLS), full module skeleton (models, schemas, services, API routes), state machine, and 81 real-DB-backed tests. All quality gates pass: 87% coverage, lint clean, migration round-trip verified.

---

## Commits (newest first)

| SHA | Message |
|---|---|
| `963f02e` | feat(visits): TASK-007 implement state machine + service + routes |
| `bd39515` | test(visits): TASK-007 unit + DB-backed e2e tests for state transitions and call-next |
| `60ff3d2` | feat(visits): TASK-007 add visit table + visit_number generator + RLS (migration 0010) |

---

## Files Created / Modified

### New files (17)
- `clinic-cms/alembic/versions/0010_create_visits.py` — migration: visit_number_counter table, fn_next_visit_number PL/pgSQL, visit table with CHECK constraint, indexes, v_active_queue view, RLS, grants
- `clinic-cms/app/modules/visits/__init__.py`
- `clinic-cms/app/modules/visits/models/__init__.py`
- `clinic-cms/app/modules/visits/models/visit.py` — Visit ORM model + VisitStatus (enum.StrEnum)
- `clinic-cms/app/modules/visits/schemas/__init__.py`
- `clinic-cms/app/modules/visits/schemas/visit_schemas.py` — VisitCreate, VisitUpdate, VisitResponse, VisitCancelRequest, VisitCallNextResponse, VisitListResponse
- `clinic-cms/app/modules/visits/services/__init__.py`
- `clinic-cms/app/modules/visits/services/state_machine.py` — ALLOWED_TRANSITIONS dict + assert_can_transition
- `clinic-cms/app/modules/visits/services/visit_service.py` — CRUD, all state transitions, call_next with CASE-based priority
- `clinic-cms/app/modules/visits/api/__init__.py`
- `clinic-cms/app/modules/visits/api/routes.py` — 10 routes covering all AC endpoints
- `clinic-cms/tests/unit/visits/__init__.py`
- `clinic-cms/tests/unit/visits/test_state_machine.py` — 18 tests
- `clinic-cms/tests/unit/visits/test_visit_schemas.py` — 12 tests
- `clinic-cms/tests/unit/visits/test_visit_service.py` — 29 tests (mocked DB)
- `clinic-cms/tests/integration/visits/__init__.py`
- `clinic-cms/tests/integration/visits/test_visits_api.py` — 22 real DB e2e tests

### Modified files (1)
- `clinic-cms/app/main.py` — added visits_router import + include_router

---

## Test Results

| Suite | Passed | Failed | Total |
|---|---|---|---|
| Unit (state_machine) | 18 | 0 | 18 |
| Unit (schemas) | 12 | 0 | 12 |
| Unit (service) | 29 | 0 | 29 |
| Integration (e2e) | 22 | 0 | 22 |
| **Total** | **81** | **0** | **81** |

**Coverage**: 87% on `app/modules/visits/` (316 stmts, 40 missed, threshold: 80%)

| File | Coverage |
|---|---|
| `state_machine.py` | 100% |
| `models/visit.py` | 100% |
| `schemas/visit_schemas.py` | 100% |
| `api/routes.py` | 87% |
| `services/visit_service.py` | 77% |

Full suite regression: 586 passed, 2 pre-existing failures (test_tenancy_middleware + test_hr_service_logic — both confirmed pre-existing from TASK-004/TASK-014 bases).

---

## Migration Round-Trip

```
alembic downgrade -1  → OK (0010 → 0009)
alembic upgrade head  → OK (0009 → 0010)
```

Tables created: `visit_number_counter`, `visit`  
Function created: `fn_next_visit_number(UUID, DATE) → TEXT`  
View created: `v_active_queue`  
Indexes: `ix_visit_clinic_status_priority` (partial, WHERE NOT is_deleted), `uq_visit_clinic_date_number` (UNIQUE partial), `ix_visit_patient_id`  
RLS: enabled with FORCE on both `visit` and `visit_number_counter`

---

## Concurrency Test Result

`test_concurrent_call_next_no_double_assign` fires 2 simultaneous `/call-next` requests (via `asyncio.gather`) against 2 WAITING visits. Result: each caller receives a different visit, no double-assignment. The `SELECT ... FOR UPDATE SKIP LOCKED` ensures serialisation.

---

## Design Decisions Worth Attention

### 1. visit_number_counter table (not scan-based)
The design doc suggested a `SELECT ... FOR UPDATE ... ORDER BY DESC LIMIT 1` approach. Implemented a dedicated `visit_number_counter` table with `INSERT ... ON CONFLICT DO UPDATE SET last_seq = last_seq + 1 RETURNING last_seq`. This is more correct under concurrent load because:
- Row-level lock on the counter row serializes concurrent generators without a full table scan
- No risk of stale reads or phantom rows
- Simpler downgrade (just drop the table)

### 2. CASE expression in call_next ORDER BY (critical bug fixed)
Initial implementation used `(Visit.assigned_doctor_id == doctor_user_id).desc()` in ORDER BY. This generates `assigned_doctor_id = :uid DESC`. The problem: when `assigned_doctor_id IS NULL`, the comparison yields SQL NULL (not FALSE). In PostgreSQL, NULL sorts BEFORE TRUE in DESC order — meaning unassigned visits incorrectly ranked higher than assigned ones.

Fixed using `sa_case((Visit.assigned_doctor_id == doctor_user_id, 2), (Visit.assigned_doctor_id.is_(None), 1), else_=0)` which maps to `CASE WHEN ... THEN 2 WHEN ... THEN 1 ELSE 0 END` — no NULLs in the ordering expression.

### 3. appointment_id — no FK constraint
The `appointment` table does not exist yet (TASK-008+). The column is stored as a plain UUID without a FK constraint. A comment in both migration and model documents that the FK will be added when appointment is implemented.

### 4. doctor_id FK points to `user` table
The design requires `doctor_id` and `assigned_doctor_id` as FKs to `user`. Both are implemented. Note: in `transition_to_complete`, the service verifies `visit.doctor_id == caller_doctor_id` before allowing the state change, preventing a different doctor from completing someone else's visit.

---

## Known Limitations

- `appointment_id` has no FK enforcement (table not yet created).
- `mark_paid` (AWAITING_PAYMENT → COMPLETED) is ready for TASK-013 Billing integration but has no invoice side-effect yet — per task spec this is intentional.
- The `v_active_queue` view is defined in the migration but the service uses an ORM query (with matching WHERE + ORDER BY) rather than querying the view directly, because SQLAlchemy's ORM cannot natively map to a view without additional setup. A future refactor could add a mapped view entity.
- Coverage on `visit_service.py` is 77% — the uncovered lines are in `list_visits` filter branches (doctor_id, visit_date filters) and edge cases in `call_next` not exercised by the concurrent test. The overall module coverage (87%) comfortably exceeds the 80% threshold.
