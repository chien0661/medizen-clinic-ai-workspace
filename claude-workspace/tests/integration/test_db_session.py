"""Integration tests: DB context-vars and session-layer behaviour.

The global `AsyncSessionLocal` (from app.core.db) binds to the module-level
engine, which is shared across all tests but scoped to the import-time event
loop.  Mixing it with pytest-asyncio function-scoped test loops produces
"attached to a different loop" errors.

Strategy:
- Context-var tests: pure Python, synchronous — no DB/loop dependency.
- DB-live tests: only via the `client` fixture (ASGI transport, fresh per test).

The `async_session` fixture is session-scoped and intended for use by future
tests that are also session-scoped (e.g., TASK-002 RLS policy tests).
"""

from uuid import uuid4

from app.core.db import current_clinic_id, current_user_id

# ---------------------------------------------------------------------------
# Context-var tests — pure Python, synchronous, no event loop required
# ---------------------------------------------------------------------------


def test_context_var_clinic_id_default_is_none():
    """current_clinic_id ContextVar defaults to None (no tenant context)."""
    assert current_clinic_id.get() is None


def test_context_var_user_id_default_is_none():
    """current_user_id ContextVar defaults to None (no user context)."""
    assert current_user_id.get() is None


def test_context_var_clinic_id_set_and_reset():
    """current_clinic_id ContextVar round-trips: set → get → reset."""
    test_id = uuid4()
    token = current_clinic_id.set(test_id)
    try:
        assert current_clinic_id.get() == test_id
    finally:
        current_clinic_id.reset(token)
    assert current_clinic_id.get() is None


def test_context_var_user_id_set_and_reset():
    """current_user_id ContextVar round-trips: set → get → reset."""
    test_id = uuid4()
    token = current_user_id.set(test_id)
    try:
        assert current_user_id.get() == test_id
    finally:
        current_user_id.reset(token)
    assert current_user_id.get() is None


def test_context_vars_are_independent():
    """clinic_id and user_id are separate ContextVars — no cross-contamination."""
    cid = uuid4()
    uid = uuid4()
    ct = current_clinic_id.set(cid)
    ut = current_user_id.set(uid)
    try:
        assert current_clinic_id.get() == cid
        assert current_user_id.get() == uid
        assert current_clinic_id.get() != current_user_id.get()
    finally:
        current_clinic_id.reset(ct)
        current_user_id.reset(ut)


# ---------------------------------------------------------------------------
# DB-live tests — use the `client` fixture (function-scoped ASGI transport)
# ---------------------------------------------------------------------------


async def test_health_endpoint_returns_ok(client):
    """Health endpoint reachable via ASGI client (validates app boot + wiring)."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
