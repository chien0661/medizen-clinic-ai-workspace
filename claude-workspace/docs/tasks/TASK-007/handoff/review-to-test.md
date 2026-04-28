# Handoff: TASK-007 Code Review → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Date**: 2026-04-27
**Branch**: `feature/task-007-visits` (HEAD `0a5f02a`)
**Iteration**: Test iteration 1 (post review-iter-2 APPROVAL)

---

## Iteration 2 Approval

Code Review approved iteration 2 of TASK-007. All iter-1 findings (2 MAJOR + 3 MINOR) resolved or justifiably deferred:

- **M1** — `cancel` route now requires `visit.cancel`, `mark-paid` requires `payment.receive` (matches seeded role intent). 2 new gating tests included.
- **M2** — Concurrent `call-next` test rewritten: 2 independent `AsyncClient` instances, asserts strict 200/200 with distinct IDs and DB-level `IN_PROGRESS` verification. Stability validated 5/5 runs.
- **m1** — `list_queue` docstring updated.
- **m2** — `assert_can_transition` added to `call_next` for state-machine symmetry.
- **m3** — ORJSON deprecation deferred (verified pre-existing since TASK-001).

Build state at handoff:
- 83/83 tests pass (`pytest tests/{unit,integration}/visits/`)
- Coverage 87% (317 stmts, 41 missed) on `app/modules/visits/`
- `ruff check` clean
- Migration 0010 round-trips clean (verified during iter-1)

See `review-report.md` § "Iteration 2 Review" for the full verification table.

---

## Test Focus Areas

The implementation has solid unit + integration coverage of individual transitions, but the test suite has gaps in **end-to-end workflow**, **AC #6 perf benchmark**, and **negative-path coverage**. Please prioritise:

### 1. Phase B integration — full state-machine lifecycle (E2E)

Test the full happy path **end-to-end through the HTTP API** as a single workflow:

```
POST /api/v1/visits                              → 201 (WAITING, visit_number=YYYYMMDD-001)
POST /api/v1/visits/{id}/start  (doctor)         → 200 (IN_PROGRESS, started_at set)
POST /api/v1/visits/{id}/complete (doctor)       → 200 (AWAITING_PAYMENT, completed_at set)
POST /api/v1/visits/{id}/mark-paid (admin/recpt) → 200 (COMPLETED, status final)
```

The implementation has `test_full_lifecycle_waiting_to_completed` which covers the state path but should be re-validated for:
- Each transition's timestamp side-effects (`started_at`, `completed_at` non-null, ordering correct)
- `audit_log` entries written for each transition (if audit hook fires for visit module)
- After `COMPLETED`, `start`/`cancel`/`complete` must all return 409 (re-verify)

### 2. AC #5 — concurrent call-next (already covered by M2 fix)

The new strict 200/200 + distinct-IDs assertion verified by review (5/5 stable runs). **Test agent should add scale tests if perf-critical for production**:
- 5 doctors, 5 WAITING visits, 5 concurrent `/call-next` → all 200, all distinct.
- 10 doctors, 5 WAITING → 5×200 + 5×404 (no duplicates).

Optional but valuable to defend `SELECT ... FOR UPDATE SKIP LOCKED` semantics under heavier load.

### 3. AC #6 — perf benchmark (queue 50 visits < 50ms)

**Currently NOT covered by any test.** This is the only AC without a verifying test. Suggested approach (mirrors TASK-005 perf-test pattern):

```python
@pytest.mark.asyncio
async def test_queue_50_visits_under_50ms(visits_e2e_ctx):
    # Seed 50 WAITING visits in the same clinic
    # Warm up: 1 GET /api/v1/visits/queue
    # Measure: 5 sequential GET /api/v1/visits/queue calls, take median
    # Assert: median < 50ms server-side
```

Use `time.perf_counter()` around the awaited HTTP call, or instrument server-side via response timing header. Document the measurement method (cold cache vs warm cache, isolated test DB, etc).

The `ix_visit_clinic_status_priority` partial index should make this trivial — but the test will catch any regression where the index gets dropped or the query stops using it.

### 4. Negative paths — invalid transitions and access control

Verify these failure modes via API (some are covered, some are not — check coverage):

- **Invalid state transitions** (must return 409 with `from_status`/`to_status`/`allowed`):
  - `WAITING → COMPLETED` (skip)
  - `COMPLETED → IN_PROGRESS` (revert)
  - `CANCELLED → IN_PROGRESS` (revert)
  - `AWAITING_PAYMENT → IN_PROGRESS` (revert)
- **Doctor identity guard** on `transition_to_complete`: doctor B cannot complete doctor A's visit (should be 403 or 409 per current implementation).
- **Cross-clinic access** (RLS):
  - User from clinic A cannot read clinic B's visit (404 expected via RLS, NOT 403 — a 403 leaks existence).
  - `test_clinic_a_cannot_access_clinic_b_visit` already exists; verify it asserts 404 not 403.
  - Verify the `visit_number_counter` isolation (cross-clinic counter reads denied — already verified live during review, but a test is missing).
- **Validation edge cases** for any date-bearing fields:
  - The visit module has `created_at`, `started_at`, `completed_at`, `cancelled_at` — all server-set, so no client-input date validation to test here. But check `VisitCreate` / `VisitUpdate` schemas for any client-supplied date fields and add boundary tests if found.
- **Cancel-reason validation**: empty string, whitespace-only, very long string (>500 chars or wherever the limit is). Existing `test_cancel_reason_validation` covers some of this — verify breadth.

### 5. Visit number generation under load

Currently tested via `test_visit_number_format` and `test_visit_number_increments`. Add (optional but recommended):
- Concurrent visit creation: 10 simultaneous `POST /api/v1/visits` in same clinic-day → 10 distinct visit_numbers, monotonically `001..010`.
- Cross-clinic same day: clinic A's `001` and clinic B's `001` co-exist (independent counters).
- Date rollover: a visit created at `23:59:59` and one at `00:00:01` next day get `YYYYMMDD-001` for both (counter resets per date).

---

## Test Cases Deliverable

Please populate `docs/tasks/TASK-007/deliveries/test-cases/` with the test scenarios you cover (one md file per scenario family is fine), and put test reports + screenshots (if relevant) into `docs/tasks/TASK-007/deliveries/test-reports/`.

---

## Bug Reporting

If issues are found during testing, file them under `docs/tasks/TASK-007/bugs/` (one .md per bug, severity: BLOCKER / CRITICAL / MAJOR / MINOR). Status flow: IN_TESTING → IN_PROGRESS (rejection) → IN_REVIEW → IN_TESTING.

---

## Workspace + Branch

- **Source repo**: `E:\MyProject\clinic-cms-workspace\clinic-cms` on `feature/task-007-visits`
- **HEAD**: `0a5f02a` (iter-2 commits: `0a5f02a` test M2, `021b321` fix M1+m1+m2)
- **Workspace**: `E:\MyProject\clinic-cms-workspace\claude-workspace`

## Test commands (Docker-based)

```bash
cd E:/MyProject/clinic-cms-workspace/clinic-cms
# Visits suite only
docker compose -f docker/docker-compose.yml exec -T api pytest tests/unit/visits/ tests/integration/visits/ -q

# With coverage
docker compose -f docker/docker-compose.yml exec -T api pytest --cov=app/modules/visits --cov-report=term tests/unit/visits/ tests/integration/visits/

# Lint
docker compose -f docker/docker-compose.yml exec -T api ruff check app/modules/visits/ tests/{unit,integration}/visits/

# Full suite regression (586 + 2 pre-existing failures expected)
docker compose -f docker/docker-compose.yml exec -T api pytest -q
```
