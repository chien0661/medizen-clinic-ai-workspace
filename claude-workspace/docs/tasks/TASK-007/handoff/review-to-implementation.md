# Handoff: TASK-007 → Code Implementation Agent (Iteration 2)

**From**: Code Review Agent
**To**: Code Implementation Agent
**Status**: IN_PROGRESS
**Date**: 2026-04-27
**Iteration**: 1 → fix → 2
**Decision**: CHANGES_REQUESTED
**Branch**: `feature/task-007-visits` (HEAD `963f02e`)

---

## Summary

Iteration 1 is well-built — clean migration with proper RLS on both `visit` and `visit_number_counter`, race-safe `fn_next_visit_number` via counter table, real-DB integration tests, 87 % coverage, lint clean. **No CRITICAL findings.** Two MAJOR items remain: the `cancel` and `mark-paid` endpoints are gated on the broad `visit.write` permission instead of the already-seeded narrower `visit.cancel` / `payment.receive` permissions, and the "concurrent call-next" test accepts `1×200 + 1×404` as success — that's the symptom of full serialisation, not parallel safety, so it doesn't actually prove AC #5. Plus 2 MINOR docstring/symmetry items.

Full report: `docs/tasks/TASK-007/handoff/review-report.md`.

---

## Required Changes

### MAJOR — must fix before re-review

#### M1. Use the seeded narrower permissions for `cancel` and `mark-paid`

The seed migration `0007_seed_permissions_and_roles.py` already defines `visit.cancel` (granted only to admin + doctor) and `payment.receive` (granted only to admin + receptionist). The new routes ignore both and use `visit.write`, which is held by admin + doctor + nurse + receptionist — too broad.

**File:** `clinic-cms/app/modules/visits/api/routes.py`

```python
# Line 256-272 — change cancel to use visit.cancel
@router.post(
    "/visits/{visit_id}/cancel",
    response_model=VisitResponse,
    dependencies=[Depends(require_permission("visit.cancel"))],   # was: visit.write
    summary="Cancel a visit with a mandatory reason",
)
...

# Line 275-289 — change mark-paid to use payment.receive
@router.post(
    "/visits/{visit_id}/mark-paid",
    response_model=VisitResponse,
    dependencies=[Depends(require_permission("payment.receive"))],   # was: visit.write
    summary="Mark visit as paid — AWAITING_PAYMENT → COMPLETED (for TASK-013 Billing)",
)
```

Also update the integration test:

**File:** `clinic-cms/tests/integration/visits/test_visits_api.py`

Add (or extend `test_missing_visit_write_returns_403`) two new tests:
- `test_cancel_requires_visit_cancel_permission`: a user with only `visit.write` (no `visit.cancel`) must get 403 when calling `/cancel`.
- `test_mark_paid_requires_payment_receive_permission`: a user with only `visit.write` (no `payment.receive`) must get 403 when calling `/mark-paid`.

Re-run `pytest tests/integration/visits/` and confirm green.

#### M2. Strengthen the concurrent-call-next test

**File:** `clinic-cms/tests/integration/visits/test_visits_api.py:772-826`

Currently the test accepts `200 + 404` as success. With 2 WAITING visits seeded, that outcome is also what you'd see if the two calls were fully serialised — defeating the AC. Pick one of:

**Option A (preferred, smallest change):**

```python
# Replace lines 802-826 with:
results = await asyncio.gather(
    client.post("/api/v1/visits/call-next", headers=_auth(doc_token)),
    client.post("/api/v1/visits/call-next", headers=_auth(admin_token)),
)

# Both must succeed with 200 (we seeded 2 WAITING visits)
assert all(r.status_code == 200 for r in results), [
    (r.status_code, r.text) for r in results
]
assigned_ids = [r.json()["visit"]["id"] for r in results]
# Both got a visit
assert len(assigned_ids) == 2
# No double-assign
assert len(set(assigned_ids)) == 2, f"Double-assign detected! Got: {assigned_ids}"
# Both must be drawn from the seeded set
assert set(assigned_ids) <= set(v_ids), (
    f"Returned visit IDs not from seeded set: {assigned_ids} vs {v_ids}"
)
```

**Option B (stronger, more setup):**

Open two real `asyncpg` connections, manually `BEGIN; SELECT id FROM visit WHERE clinic_id=$1 AND status='WAITING' LIMIT 1 FOR UPDATE SKIP LOCKED;` on both connections **before** committing, and assert each gets a different row. This is the only way to defeat the asyncio/connection-pool serialisation in a single-loop test client.

If you take Option A and it flakes (because the two coroutines genuinely hit the same connection pool), document the limitation and add a Postgres-direct test as `test_skip_locked_correctness_db_level` using the existing `factory` fixture — open two `factory()` sessions, run two `SELECT ... FOR UPDATE SKIP LOCKED LIMIT 1` against the same clinic, assert different IDs returned.

### MINOR — fix at your discretion (no re-review required if M1+M2 are clean)

#### m1. `list_queue` docstring

**File:** `clinic-cms/app/modules/visits/services/visit_service.py:195-198`

Replace:
```python
    """Return active queue (WAITING + IN_PROGRESS) from v_active_queue view.

    The view is ordered by priority DESC, created_at ASC server-side.
    """
```
with:
```python
    """Return active queue (WAITING + IN_PROGRESS), tenant-scoped.

    Ordering matches the v_active_queue view definition (priority DESC,
    created_at ASC). Implemented as an ORM query for typing convenience —
    SQLAlchemy ORM does not natively map onto views.
    """
```

#### m2. Defensive `assert_can_transition` in `call_next`

**File:** `clinic-cms/app/modules/visits/services/visit_service.py:430-432`

```python
    reason = _call_next_priority_reason(visit, doctor_user_id)

    assert_can_transition(visit.status, VisitStatus.IN_PROGRESS.value)   # ← add this
    visit.status = VisitStatus.IN_PROGRESS.value
```

Currently safe because of the `WHERE status = WAITING` filter, but adding the assertion keeps every state-machine transition uniform.

---

## What's Already Good (Don't Change)

- Migration 0010 round-trips cleanly (verified live).
- `fn_next_visit_number` via counter table — race-safe and produces exactly `YYYYMMDD-NNN` format.
- RLS on both `visit` and `visit_number_counter` — verified live (cross-clinic counter reads denied).
- CASE-based priority ordering in `call_next` (the NULL-comparison fix in your handoff §2 is correct and important).
- Real-DB integration tests, no mocks — TASK-005 lesson successfully applied.
- All 10 routes have `Depends(require_permission(...))`.
- Router registered in `app/main.py`.
- State-machine assertion discipline in service methods (only `call_next` skips it — see m2).
- Lint clean, coverage 87 %, full-suite regression matches handoff (586 passed, 2 pre-existing failures).

---

## Re-Review Scope

When you push iteration 2, the reviewer will:
1. Verify M1 — confirm decorator changes + new permission tests pass.
2. Verify M2 — re-run `test_concurrent_call_next_no_double_assign` 5×; confirm strict assertions in place.
3. Spot-check m1, m2 if applied.
4. Re-run `pytest tests/{unit,integration}/visits/ -q` + `ruff check ...` + migration round-trip.

Expect ~20 minutes review turnaround if M1 + M2 land cleanly.
