"""MAJOR-1 Integration test: End-to-end account lockout with real DB + Redis.

Scenario:
  1. Create a real Clinic + User in the DB (committed).
  2. POST /api/v1/auth/login 5× with wrong password via real HTTP endpoint.
  3. Assert failed_login_count increments in DB.
  4. Assert Redis lockout key `lockout:{clinic_id}:{username}` increments.
  5. Assert 6th attempt returns 423 Locked.
  6. Assert User.is_locked = True in DB.
  7. Assert audit_log entry 'user.locked' was written.
  8. Cleanup: delete user, delete clinic, clear Redis key.

Coverage closes TASK-003 MAJOR review gap #1.

BUG-001 DISCOVERED: The is_locked=True DB update is rolled back because login()
  raises ValueError which triggers FastAPI get_db ROLLBACK.  The _lock_user()
  update (is_locked=True + audit write) runs inside the same transaction that
  gets rolled back when ValueError("invalid_credentials") is raised after the
  lockout is triggered.  This test correctly FAILS and exposes the bug.

Uses NullPool engine (not pool-backed session engine) to avoid asyncpg
connection-cancel errors when running with pytest-asyncio's session-scoped
event loop and function-scoped test loops.
"""

from __future__ import annotations

import uuid
from uuid import uuid4

import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.main import app
from app.modules.audit.models.audit_log import AuditLog
from app.modules.users.models.clinic import Clinic
from app.modules.users.models.user import User
from tests.conftest import TEST_DATABASE_URL

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lockout_key(clinic_id: uuid.UUID, username: str) -> str:
    return f"lockout:{clinic_id}:{username.lower()}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def lockout_http_client():
    """Real HTTP client — no dependency overrides; uses real DB + Redis.

    Resets the in-process rate limiter before use so prior test runs that
    exhausted the login rate limit (10/min) don't block this test's login calls.
    The lockout test sends 5 wrong-password attempts + 1 correct attempt = 6 total.
    """
    limiter.reset()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def lockout_test_context(lockout_http_client):
    """Create a Clinic + User in the DB; clean up after test.

    Uses a private NullPool engine to avoid asyncpg connection-cancel errors
    from pool connections crossing event loop boundaries in pytest-asyncio.
    """
    clinic_id = uuid4()
    user_id = uuid4()
    clinic_code = f"LOCK{clinic_id.hex[:6].upper()}"
    username = f"locktest_{clinic_id.hex[:8]}"
    plain_password = "CorrectPassw0rd!"
    password_hash = hash_password(plain_password)

    # NullPool: no connection reuse → no event-loop mismatch on teardown
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    # --- Setup ---
    async with factory() as session:
        clinic = Clinic(
            id=clinic_id,
            code=clinic_code,
            name="Lockout Test Clinic",
            specialty="general",
            is_active=True,
        )
        user = User(
            id=user_id,
            clinic_id=clinic_id,
            username=username,
            full_name="Lockout Test User",
            password_hash=password_hash,
            is_active=True,
            is_locked=False,
            failed_login_count=0,
        )
        session.add(clinic)
        session.add(user)
        await session.commit()

    yield {
        "clinic_id": clinic_id,
        "clinic_code": clinic_code,
        "user_id": user_id,
        "username": username,
        "plain_password": plain_password,
        "factory": factory,
        "client": lockout_http_client,
    }

    # --- Teardown: remove user + clinic; skip audit_log (append-only DB trigger) ---
    async with factory() as session:
        await session.execute(
            text('DELETE FROM "user" WHERE id = :uid'),
            {"uid": user_id},
        )
        await session.execute(
            text("DELETE FROM clinic WHERE id = :cid"),
            {"cid": clinic_id},
        )
        await session.commit()

    await engine.dispose()

    # Clear Redis lockout key
    redis_key = _lockout_key(clinic_id, username)
    async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
        await r.delete(redis_key)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLockoutFlowRealDB:
    """End-to-end lockout: 5 wrong passwords → is_locked=True → 6th returns 423.

    BUG-001 DETECTED: The DB write for is_locked=True (inside _lock_user) is
    inside the same SQLAlchemy transaction as the failed login attempt.  When
    login() raises ValueError, FastAPI's get_db dependency catches the exception
    and issues a ROLLBACK, undoing both the failed_login_count update AND the
    is_locked=True update.  The Redis counter persists, but the DB state does not.

    Expected (correct) behaviour after fix:
      - After 5 failed attempts, User.is_locked=True in DB.
      - 6th attempt with any password → 423 Locked.
      - audit_log has a 'user.locked' entry committed.

    This test will FAIL until BUG-001 is fixed.  See bugs/BUG-001.md.
    """

    async def test_lockout_end_to_end(self, lockout_test_context):
        """Full lockout flow: 5 wrong attempts then 423 on 6th.

        Validates:
          - Each of 5 wrong attempts returns 401 (not 423 yet).
          - Redis lockout key exists and has positive TTL after failures.
          - Redis counter >= LOCKOUT_MAX_ATTEMPTS.
          - User.is_locked is True in DB after lockout threshold (BUG-001: currently FAILS).
          - 6th attempt returns 423 Locked (BUG-001: currently returns 401).
          - audit_log has a 'user.locked' entry (BUG-001: rolled back with tx).
        """
        ctx = lockout_test_context
        cid = ctx["clinic_id"]
        uid = ctx["user_id"]
        code = ctx["clinic_code"]
        username = ctx["username"]
        factory = ctx["factory"]
        client = ctx["client"]
        redis_key = _lockout_key(cid, username)

        max_attempts = settings.LOCKOUT_MAX_ATTEMPTS  # 5

        # --- 5 wrong-password attempts ---
        for attempt in range(1, max_attempts + 1):
            resp = await client.post(
                "/api/v1/auth/login",
                json={
                    "clinic_code": code,
                    "username": username,
                    "password": "WRONG_PASSWORD",
                },
            )
            assert resp.status_code == 401, (
                f"Attempt {attempt}: expected 401, got {resp.status_code}"
            )

        # --- Assert Redis: lockout key exists with positive TTL and correct count ---
        async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
            count_val = await r.get(redis_key)
            ttl = await r.ttl(redis_key)

        assert count_val is not None, (
            f"Redis lockout key '{redis_key}' should exist after {max_attempts} failures"
        )
        assert int(count_val) >= max_attempts, (
            f"Redis counter should be >= {max_attempts}, got {count_val}"
        )
        assert ttl > 0, f"Redis lockout key should have positive TTL, got {ttl}"
        assert ttl <= settings.LOCKOUT_WINDOW_MINUTES * 60, (
            f"Redis TTL should be <= {settings.LOCKOUT_WINDOW_MINUTES * 60}s, got {ttl}"
        )

        # --- Assert DB: is_locked=True --- BUG-001: this FAILS because is_locked update
        # is rolled back when ValueError is raised in the same transaction ---
        async with factory() as session:
            user = await session.get(User, uid)
            assert user is not None
            assert user.is_locked is True, (
                "BUG-001: Expected is_locked=True after lockout threshold reached. "
                "_lock_user() DB update is rolled back with the failed-login transaction. "
                "Fix: commit the lock update in a separate autonomous transaction. "
                "See bugs/BUG-001.md."
            )

        # --- 6th attempt: even correct password must return 423 ---
        # BUG-001: returns 401 (not 423) because is_locked=False in DB
        resp6 = await client.post(
            "/api/v1/auth/login",
            json={
                "clinic_code": code,
                "username": username,
                "password": ctx["plain_password"],
            },
        )
        assert resp6.status_code == 423, (
            f"6th attempt must return 423 Locked, got {resp6.status_code}. "
            "(BUG-001: is_locked=False in DB so login proceeds normally)"
        )

        # --- Assert audit_log: 'user.locked' entry written ---
        # BUG-001: audit row also rolled back with transaction
        async with factory() as session:
            result = await session.execute(
                select(AuditLog).where(
                    AuditLog.entity_id == uid,
                    AuditLog.action == "user.locked",
                )
            )
            audit_row = result.scalars().first()
            assert audit_row is not None, (
                "Expected an audit_log row with action='user.locked'. "
                "(BUG-001: audit row rolled back with the failed-login transaction)"
            )
