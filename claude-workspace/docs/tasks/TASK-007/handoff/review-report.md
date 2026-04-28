# Code Review: TASK-007 — Visit Module (Entity + State Machine + Visit Number Generation)

**Reviewer:** Code Review Agent
**Date:** 2026-04-27
**Branch:** `feature/task-007-visits` (HEAD `963f02e`, branched from `main` `31b116a`)
**Iteration:** 1
**Status:** **CHANGES_REQUESTED**

---

## TL;DR

| Severity | Count | Examples |
|---|---|---|
| **CRITICAL** | **0** | — |
| **MAJOR** | **2** | `mark_paid` is gated on `visit.write` — every role with `visit.write` (admin, doctor, nurse, receptionist) can close the billing loop, despite `visit.cancel` and `payment.receive` already being seeded as separate permissions; the cancel endpoint similarly ignores the seeded `visit.cancel` permission. The "concurrent call-next" e2e test accepts `1 success + 1 404` as a valid outcome — that pattern is also the symptom of a serialization bottleneck rather than parallel execution, so the test does not actually prove the AC ("2 BS đồng thời không gây race condition") at the level of "both callers receive a different visit". |
| **MINOR** | **3** | `list_queue` docstring claims it reads from `v_active_queue` but the implementation is an ORM query against `visit`; `call_next` updates `visit.status` without going through `assert_can_transition` (defensive symmetry only — current code is correct because the `WHERE status = WAITING` filter already constrains the row); ORJSON deprecation warnings flooding test output (pre-existing, but visible everywhere visits routes are exercised). |

**Verdict:** **CHANGES_REQUESTED.** The implementation is solid — clean module structure, correct CASE-based priority ordering in `call_next`, real-DB integration tests with no mocks, RLS active on both tables, migration round-trips cleanly, lint is clean, coverage 87 %. The two MAJOR findings are about authorization granularity (`mark_paid` / cancel) and the strength of the concurrency test — both fixable with small changes and worth getting right before this state-machine becomes the linchpin for billing/queue behaviour. No CRITICAL findings; no migration regressions; no test-strategy violations.

---

## Review Summary

- **Files reviewed:** 18 changed (2,799 LOC additions). 1 migration, 1 main.py edit, 9 module files, 7 test files.
- **Test results actually observed:** **81 passed, 0 failed** in 30.84 s for `tests/{unit,integration}/visits`. Matches handoff (81/81).
- **Coverage actually observed:** **87 %** on `app/modules/visits/` (316 stmts, 40 missed). Matches handoff. `state_machine.py` 100 %, `models/visit.py` 100 %, `schemas/visit_schemas.py` 100 %, `api/routes.py` 87 %, `services/visit_service.py` 77 %.
- **Lint:** `ruff check app/modules/visits/ tests/unit/visits/ tests/integration/visits/` → **All checks passed!**
- **Migration round-trip:** clean. `0010 → 0009 → 0010 → 0009 → 0010` all apply cleanly. Tables `visit`, `visit_number_counter`, view `v_active_queue`, function `fn_next_visit_number(uuid, date)`, all 6 indexes, RLS (`relrowsecurity=t, relforcerowsecurity=t`), and `tenant_isolation` policies all present after upgrade and absent after downgrade.
- **Visit number format:** `SELECT fn_next_visit_number('329d655c-...', '2026-04-26')` twice → `20260426-001`, `20260426-002`. Format and monotonic increment confirmed live.
- **RLS isolation on `visit_number_counter`:** verified live with `SET ROLE cms_app; SET LOCAL app.current_clinic_id='aaaa...'; SELECT count(*) FROM visit_number_counter` → 0. Cross-clinic counter reads are denied.
- **Permission decorators:** all 10 routes have `Depends(require_permission(...))` (verified by grep — 10 `@router.{get,post,patch}` matches paired with 10 `require_permission` matches in `routes.py`).
- **Router registration:** `app.include_router(visits_router)` present at `app/main.py:54`.
- **Full-suite regression:** 586 passed, 2 failed. Both failures (`test_hr_service_logic`, `test_tenancy_middleware`) are pre-existing on `main` and unrelated to this task — handoff acknowledges them.

---

## CRITICAL Findings

**None.**

---

## MAJOR Findings

### M1. `mark_paid` (and `/cancel`) bypass already-seeded narrower permissions

**Files:**
- `clinic-cms/app/modules/visits/api/routes.py:278` (`mark-paid` → `visit.write`)
- `clinic-cms/app/modules/visits/api/routes.py:259` (`cancel` → `visit.write`)
- `clinic-cms/alembic/versions/0007_seed_permissions_and_roles.py:39,142` (`visit.cancel` permission seeded; doctor role granted; receptionist NOT granted)

**Severity:** MAJOR — authorization gap that will become a silent privilege escalation once Billing (TASK-013) ships.

**What's wrong:**

The seed migration `0007_seed_permissions_and_roles.py` already defines two narrower permissions:
- `visit.cancel` — only granted to `admin` and `doctor` (line 142).
- `payment.receive` — only granted to `admin` and `receptionist` (line 170 area; via the receptionist mapping).

The new routes ignore both:
```python
# routes.py:259
@router.post("/visits/{visit_id}/cancel",
    dependencies=[Depends(require_permission("visit.write"))],  # any visit.write — too broad

# routes.py:278
@router.post("/visits/{visit_id}/mark-paid",
    dependencies=[Depends(require_permission("visit.write"))],  # any visit.write — too broad
```

`visit.write` is held by **admin, doctor, nurse, receptionist** (per `ROLE_PERMISSIONS` at `0007:140-172`). That means:

1. **Any nurse can cancel a visit**, even though only doctors/admin were intended (per the seed mapping, only those two have `visit.cancel`).
2. **Any nurse or doctor can move `AWAITING_PAYMENT → COMPLETED`** by hitting `/mark-paid`, bypassing the receptionist-only `payment.receive` permission. Because this state transition is the gating action that closes a visit's billing lifecycle, the cleaner production design is to require `payment.receive` here. The implementation handoff's "Known Limitations" §2 acknowledges this is a stub for TASK-013 — but iteration-1 should at minimum gate the action behind the right permission so it ships safe.

**Why it matters:**

- The seed already encodes the business intent (cancel = doctor-or-admin; payment = receptionist-or-admin). Deviating from it in iteration 1 means the rollout to production starts in a less-restrictive state than the seed mapping implies, and tightening it later is a breaking change.
- TASK-007 task brief AC says "kèm reason" for cancel — gating doesn't matter for the API shape, but for production correctness it does.
- TASK-013 will create the invoice on AWAITING_PAYMENT. If `mark_paid` then voids the invoice flag without `payment.receive`, billing reconciliation will silently lose audit fidelity.

**Suggested fix (small, no design change):**

```python
# routes.py:256-272
@router.post("/visits/{visit_id}/cancel",
    dependencies=[Depends(require_permission("visit.cancel"))],   # use the narrower seeded permission
    ...

# routes.py:275-289
@router.post("/visits/{visit_id}/mark-paid",
    dependencies=[Depends(require_permission("payment.receive"))],  # match the seeded role intent
    ...
```

If the implementer prefers to keep the broader gate temporarily, please at least:
1. Add a short note in the handoff stating the deliberate deviation from the seed.
2. Add a TODO+test_xfail tracker for the TASK-013 hook so this doesn't slip past Billing.
3. Update `tests/integration/visits/test_visits_api.py::test_missing_visit_write_returns_403` to assert the right permission for each action.

---

### M2. The concurrent-call-next test accepts the failure mode it's meant to prevent

**File:** `clinic-cms/tests/integration/visits/test_visits_api.py:772-826`
**Severity:** MAJOR — AC #5 ("Call-next với 2 BS đồng thời không gây race condition") is asserted but the test cannot distinguish "real concurrency, both succeed" from "fully serialised, second call sees nothing".

**What's wrong:**

```python
# test_visits_api.py:813-818
if r.status_code == 200:
    assigned_ids.append(r.json()["visit"]["id"])
else:
    assert r.status_code == 404, ...
# ...
# At least one must have been assigned
assert len(assigned_ids) >= 1
```

With 2 WAITING visits seeded, the only outcomes that should be acceptable are:
- 200/200 → both callers got a different visit (the AC).

The current test also accepts:
- 200/404 (one caller got a visit, the other got "no WAITING visits") — this would happen if the second call ran *after* the first call's transaction had already committed, **and** the queue lookup raced. But it would also happen if `SKIP LOCKED` were not in effect and the second call simply blocked-then-saw-nothing. The test cannot tell those apart, so it cannot prove the AC.

In the test environment (single asyncio loop, ASGITransport in-process, single async DB engine), the two coroutines are interleaved by the event loop, not truly parallel — `asyncio.gather` here likely serialises the SQL round-trips at the connection-pool layer. The test as written passes regardless of `SKIP LOCKED` correctness.

**Why it matters:**

The whole point of the `SELECT … FOR UPDATE SKIP LOCKED` design is to prove the concurrent-pick safety. Without a stricter assertion, a regression (e.g., dropping `skip_locked=True` from the query, or running both callers in a single shared transaction) wouldn't fail this test.

**Suggested fix — at least one of:**

1. Assert the strict outcome: with 2 WAITING visits, both calls **must** return 200 with distinct IDs:
   ```python
   assert all(r.status_code == 200 for r in results)
   assert len(set(assigned_ids)) == 2
   ```
2. Move the concurrency proof to a **DB-level** test that opens two real `psycopg`/`asyncpg` connections, manually `BEGIN; SELECT ... FOR UPDATE SKIP LOCKED LIMIT 1;` on both, and asserts each gets a different row before either commits. This is the only way to defeat the connection-pool serialization on a single-loop client.
3. (Alternative) seed N>2 visits, fire N callers, assert no duplicate IDs across all 200s. Add a sanity check that at least 2 callers got 200s (probabilistic, but with N≥4 it becomes hard to dodge).

---

## MINOR Findings

### m1. `list_queue` docstring claims to read from `v_active_queue`, but uses an ORM query

**File:** `clinic-cms/app/modules/visits/services/visit_service.py:189-210`

```python
async def list_queue(...):
    """Return active queue (WAITING + IN_PROGRESS) from v_active_queue view.
    ...
    """
    result = await db.execute(
        select(Visit).where(...)            # ← ORM query against `visit`, not the view
        .order_by(Visit.priority.desc(), Visit.created_at.asc())
        ...
    )
```

The handoff "Known Limitations" §3 acknowledges this — SQLAlchemy ORM cannot map onto a view without extra setup. Acceptable. Just update the docstring to read "Return active queue (WAITING + IN_PROGRESS); ordering matches the `v_active_queue` view definition" so the next reader doesn't go hunting for view-based code.

---

### m2. `call_next` updates `visit.status` without `assert_can_transition`

**File:** `clinic-cms/app/modules/visits/services/visit_service.py:432`

```python
# call_next at line 411-425 selects WHERE Visit.status == WAITING.value
# At line 432:
visit.status = VisitStatus.IN_PROGRESS.value   # ← no assert_can_transition() call here
```

This is currently safe because the row was selected by a `WHERE Visit.status == 'WAITING'` filter, so it's guaranteed to be in WAITING when assigned. But the rest of the service treats `assert_can_transition` as the single point of state-machine enforcement. Adding it here for symmetry is cheap insurance against a future refactor that, e.g., loosens the filter:

```python
assert_can_transition(visit.status, VisitStatus.IN_PROGRESS.value)
visit.status = VisitStatus.IN_PROGRESS.value
```

Severity = MINOR because the current code is correct. Worth a 2-line patch.

---

### m3. ORJSON deprecation noise flooding visit test runs

**File:** `clinic-cms/app/main.py:6,41`; `clinic-cms/app/core/exceptions.py:118,128`

`tests/integration/visits/test_visits_api.py` triggers ~27 `FastAPIDeprecationWarning: ORJSONResponse is deprecated` per run. Pre-existing — not a TASK-007 regression — but the visits test suite is the highest-volume offender so far. Future task should switch `default_response_class=ORJSONResponse` away or set Pydantic native serialization. Not blocking.

---

## State-Machine Audit

| Service method | from-state guard | sets `started_at`? | sets `completed_at`? | sets `cancelled_at`? | calls `assert_can_transition` | OK? |
|---|---|---|---|---|---|---|
| `transition_to_started` | WAITING (via assert) | yes | — | — | yes | yes |
| `transition_to_complete` | IN_PROGRESS + same doctor | — | yes | — | yes | yes |
| `transition_to_cancel` | non-COMPLETED (via assert) | — | — | yes | yes | yes |
| `mark_paid` | AWAITING_PAYMENT (via assert) | — | — | — | yes | yes (no extra timestamp needed; `completed_at` was set on the prior transition) |
| `call_next` | WAITING (via WHERE) | yes | — | — | **NO** (see m2) | safe by construction |

Audit-trail symmetry: `started_at` set on `transition_to_started` AND on `call_next` ✓. `completed_at` set on `transition_to_complete` ✓ but `mark_paid` does NOT set a `paid_at` timestamp — there's no such column. Acceptable given the brief says billing detail will live elsewhere; flag for TASK-013 in case Billing wants a `paid_at` column on visit. Not a blocker.

---

## Tenant Isolation — Verified Live

```sql
-- as cms_app role with bogus current_clinic_id:
SET ROLE cms_app;
SET LOCAL app.current_clinic_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
SELECT count(*) FROM visit_number_counter; -- 0
SELECT count(*) FROM visit;                -- 0
```

Both tables have `relrowsecurity=t, relforcerowsecurity=t` and a `tenant_isolation` ALL-policy. Cross-tenant reads of the counter are denied — good, since otherwise an attacker could read another clinic's `last_seq` and infer their daily visit volume.

---

## Migration Round-Trip — Verified Live

```
docker compose -f docker/docker-compose.yml exec -T api alembic downgrade 0009  → OK
docker compose -f docker/docker-compose.yml exec -T api alembic upgrade head    → OK
docker compose -f docker/docker-compose.yml exec -T api alembic downgrade -1    → OK
docker compose -f docker/docker-compose.yml exec -T api alembic upgrade head    → OK
```

Post-upgrade DB state confirmed:
- 2 tables present: `visit`, `visit_number_counter`
- 6 indexes: `pk_visit`, `pk_visit_number_counter`, `ix_visit_clinic_id`, `ix_visit_clinic_status_priority` (partial WHERE NOT is_deleted), `uq_visit_clinic_date_number` (UNIQUE partial WHERE NOT is_deleted), `ix_visit_patient_id`
- View `v_active_queue` defined
- Function `fn_next_visit_number(uuid, date)` defined (PL/pgSQL)
- RLS ENABLE+FORCE on both tables; `tenant_isolation` ALL-policy on both
- `cms_app` role granted SELECT, INSERT, UPDATE, DELETE on both

Post-downgrade DB state: all six artefacts above are removed.

The `appointment` table has no FK from `visit.appointment_id` — handoff acknowledges this; appointment table doesn't exist yet (TASK-008+). Acceptable.

---

## Permission Gating Audit

All 10 routes have a `Depends(require_permission(...))` dependency:

| Route | Method | Permission | Comment |
|---|---|---|---|
| `/api/v1/visits/queue` | GET | `visit.read` | OK |
| `/api/v1/visits/call-next` | POST | `visit.write` | OK |
| `/api/v1/visits` | GET | `visit.read` | OK |
| `/api/v1/visits` | POST | `visit.write` | OK |
| `/api/v1/visits/{id}` | GET | `visit.read` | OK |
| `/api/v1/visits/{id}` | PATCH | `visit.write` | OK |
| `/api/v1/visits/{id}/start` | POST | `visit.write` | OK |
| `/api/v1/visits/{id}/complete` | POST | `visit.write` | OK |
| `/api/v1/visits/{id}/cancel` | POST | `visit.write` | **see M1** — should be `visit.cancel` |
| `/api/v1/visits/{id}/mark-paid` | POST | `visit.write` | **see M1** — should be `payment.receive` |

---

## Build Verification — Actually Observed

| Check | Observed | Handoff claim | Match |
|---|---|---|---|
| `pytest -q tests/unit/visits/ tests/integration/visits/` | **81 passed** in 30.84s | 81/81 | yes |
| `pytest --cov=app/modules/visits …` | **87 %** (316 stmts, 40 missed) | 87 % | yes |
| `ruff check app/modules/visits/ tests/{unit,integration}/visits/` | **All checks passed!** | exit 0 | yes |
| Full-suite `pytest -q` | **586 passed, 2 failed** | 586 + 2 pre-existing | yes |
| Pre-existing failures | `test_hr_service_logic.py::TestCheckInRejectsOtherUsersShiftId`, `test_tenancy_middleware.py::TestDevHeaders::test_clinic_id_only_no_user_allowed` | matches | yes |
| Migration round-trip on clean DB | clean (4 cycles) | clean | yes |
| `fn_next_visit_number` format | `20260426-001` then `20260426-002` | implied by tests | yes |
| RLS on `visit_number_counter` | enforced live | implied | yes |

---

## Positive Observations

- **CASE-based priority ordering in `call_next`** (`visit_service.py:405-409`) — the handoff's "Design Decision §2" correctly identifies and avoids the NULL-comparison footgun. The CASE expression maps assigned-to-me/unassigned/other to 2/1/0, which is the right pattern for SQL `ORDER BY` over a nullable equality predicate. This is the sort of subtle bug that's easy to miss; calling it out and fixing it in iteration 1 is excellent.
- **Counter-table approach for visit_number** (rather than scan-MAX) — race-safe under concurrent registration, downgrade-clean, and survives soft-deletes. Better than the design-doc sketch.
- **Real-DB integration tests** with no mocks — TASK-005 iter-1 lesson genuinely applied. The whole `tests/integration/visits/test_visits_api.py` runs against `app.main:app` via `httpx.AsyncClient`, real PG, real Redis, real RLS, real permissions.
- **Tenant isolation extends to the counter table** — RLS policy applied via the canonical `apply_rls_with_tenant_isolation` helper. Cross-clinic counter reads denied. Verified live.
- **State-machine `assert_can_transition` discipline** — every state-mutating service method (except `call_next`, which is filter-constrained) goes through the same enforcement function. The error messages include `from_status`, `to_status`, and `allowed` next states — debuggable.
- **Static routes declared before parameterised `/{id}` routes** (`routes.py:67` comment) — avoids the FastAPI ordering footgun.
- **`transition_to_complete` doctor-identity check** (`visit_service.py:298-302`) — prevents a different doctor from completing someone else's visit. Not in the AC but a sensible defensive check.
- **Migration downgrade is correct** — RLS removed before `DROP TABLE`, view dropped first, function dropped after table to avoid dependency errors.
- **Full lifecycle e2e test** (`test_full_lifecycle_waiting_to_completed`) exercises WAITING → IN_PROGRESS → AWAITING_PAYMENT → COMPLETED through the HTTP API, verifying timestamp side-effects.
- **Cancel reason validation** (`schemas/visit_schemas.py:83-88`) rejects whitespace-only reasons via a custom `field_validator`.

---

## Decision

**CHANGES_REQUESTED.**

No CRITICAL findings. The implementation is clean, the migration round-trips, the integration tests are real, lint is green, and coverage is comfortably above 80 %. The two MAJOR findings are about getting authorization granularity right (`mark_paid` / cancel) and turning the concurrency test into something that actually proves the AC — both are localised, sub-1-day fixes. The MINORs are all cosmetic / docstring / defensive symmetry items.

## Next Steps

1. Fix M1: change `cancel` to `require_permission("visit.cancel")` and `mark-paid` to `require_permission("payment.receive")` (2 line changes in `routes.py`). Update the existing integration test `test_missing_visit_write_returns_403` to also exercise `test_cancel_requires_visit_cancel_permission` and `test_mark_paid_requires_payment_receive_permission`.
2. Fix M2: tighten the assertion in `test_concurrent_call_next_no_double_assign` to require both calls to return 200 with distinct IDs given 2 WAITING visits (or move to a true two-connection DB test). Document the chosen approach in the test docstring.
3. Fix m1: update `list_queue` docstring to "ordering matches `v_active_queue`" (no implementation change).
4. Fix m2: add `assert_can_transition` to `call_next` for symmetry (2 lines).
5. Re-run `pytest tests/unit/visits/ tests/integration/visits/` and `ruff check ...` from a clean Docker state.
6. Resubmit for review with iteration 2.

---

**Review Time:** ~55 minutes (full diff read + live migration round-trip + real-DB lint/cov/test reproduction + RLS sanity check + visit-number format check).
