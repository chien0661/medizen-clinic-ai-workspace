"""MAJOR-2 Integration test: Refresh rotation blacklist verification with real Redis.

Scenario:
  1. Login → get refresh_token A (jti_A).
  2. Call /auth/refresh with A → get tokens B (jti_B).
  3. Assert Redis key `revoked:{jti_A}` exists with positive TTL.
  4. Assert jti_B != jti_A.
  5. Call /auth/refresh with A again → should return 401 (token reused/revoked).
  6. Call /auth/refresh with B → should succeed (C issued) and revoke B.

Uses real Redis (no mocks) to verify the blacklist wiring end-to-end.
Uses real DB for user lookup during refresh service call.
Coverage closes TASK-003 MAJOR review gap #2.

Uses NullPool engine (not the pool-backed session engine) to avoid asyncpg
connection-cancel errors when running with pytest-asyncio's session-scoped
event loop and function-scoped test loops.
"""

from __future__ import annotations

import uuid
from uuid import uuid4

import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.main import app
from app.modules.users.models.clinic import Clinic
from app.modules.users.models.user import User
from tests.conftest import TEST_DATABASE_URL

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decode_jti(token: str) -> str:
    """Decode a JWT locally and return the jti claim."""
    claims = jose_jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return claims["jti"]


def _revoked_key(jti: str) -> str:
    return f"revoked:{jti}"


def _lockout_key(clinic_id: uuid.UUID, username: str) -> str:
    return f"lockout:{clinic_id}:{username.lower()}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def rotation_http_client():
    """Real HTTP client — no dependency overrides.

    Resets the in-process rate limiter before use so prior test runs that
    exhausted the login rate limit (10/min) don't block this test's login calls.
    """
    limiter.reset()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def rotation_test_context(rotation_http_client):
    """Create Clinic + User and yield context; clean up via raw SQL after test.

    Uses a private NullPool engine scoped to this fixture to avoid asyncpg
    connection-cancel errors from pool connections crossing event loop boundaries.
    """
    clinic_id = uuid4()
    user_id = uuid4()
    clinic_code = f"ROT{clinic_id.hex[:6].upper()}"
    username = f"rottest_{clinic_id.hex[:8]}"
    plain_password = "RotationPassw0rd!"
    password_hash = hash_password(plain_password)

    # NullPool: no connection reuse → no event-loop mismatch on teardown
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    # --- Setup ---
    async with factory() as session:
        clinic = Clinic(
            id=clinic_id,
            code=clinic_code,
            name="Rotation Test Clinic",
            specialty="general",
            is_active=True,
        )
        user = User(
            id=user_id,
            clinic_id=clinic_id,
            username=username,
            full_name="Rotation Test User",
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
        "client": rotation_http_client,
    }

    # --- Teardown ---
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

class TestRefreshRotationBlacklist:
    """Verify that old jti is blacklisted in Redis after a successful token refresh."""

    async def test_refresh_rotation_blacklists_old_jti(self, rotation_test_context):
        """Full rotation flow: old jti in Redis blacklist, new jti different, reuse blocked.

        Steps:
          1. Login → get refresh_token_A (jti_A).
          2. /auth/refresh with A → get refresh_token_B (jti_B).
          3. Assert revoked:{jti_A} exists in Redis with positive TTL.
          4. Assert jti_B != jti_A and token_B type is 'refresh'.
          5. /auth/refresh with A again → 401 (reused/revoked token).
          6. /auth/refresh with B → 200 (B valid, issues C, revokes B).
          7. Assert revoked:{jti_B} exists in Redis after step 6.
          8. /auth/refresh with B again → 401 (B is now revoked).
        """
        ctx = rotation_test_context
        client = ctx["client"]
        code = ctx["clinic_code"]
        username = ctx["username"]
        plain_password = ctx["plain_password"]

        # --- Step 1: Login to get refresh_token_A ---
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "clinic_code": code,
                "username": username,
                "password": plain_password,
            },
        )
        assert login_resp.status_code == 200, (
            f"Login failed: {login_resp.status_code} {login_resp.text}"
        )
        refresh_token_a = login_resp.json()["data"]["refresh_token"]
        jti_a = _decode_jti(refresh_token_a)

        # --- Step 2: Call /auth/refresh with token_A → get token_B ---
        refresh_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token_a},
        )
        assert refresh_resp.status_code == 200, (
            f"First refresh failed: {refresh_resp.status_code} {refresh_resp.text}"
        )
        refresh_token_b = refresh_resp.json()["data"]["refresh_token"]
        jti_b = _decode_jti(refresh_token_b)

        # --- Step 3: Assert revoked:{jti_A} exists in Redis with positive TTL ---
        async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
            key_a_exists = await r.exists(_revoked_key(jti_a))
            ttl_a = await r.ttl(_revoked_key(jti_a))

        assert key_a_exists == 1, (
            f"Redis key '{_revoked_key(jti_a)}' must exist after successful refresh"
        )
        assert ttl_a > 0, (
            f"Redis blacklist key for jti_A must have positive TTL, got {ttl_a}"
        )

        # --- Step 4: Assert jti_B != jti_A, type = 'refresh' ---
        assert jti_b != jti_a, (
            "New refresh token (B) must have a different jti than old token (A)"
        )
        claims_b = jose_jwt.decode(
            refresh_token_b,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert claims_b.get("type") == "refresh", (
            f"Token B should be of type 'refresh', got '{claims_b.get('type')}'"
        )

        # --- Step 5: Reuse token_A → must return 401 ---
        reuse_a_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token_a},
        )
        assert reuse_a_resp.status_code == 401, (
            f"Reusing revoked token_A must return 401, got {reuse_a_resp.status_code}"
        )

        # --- Step 6: Use token_B → must succeed (C issued) ---
        refresh_b_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token_b},
        )
        assert refresh_b_resp.status_code == 200, (
            f"Token B should still be valid, got {refresh_b_resp.status_code}"
        )
        refresh_token_c = refresh_b_resp.json()["data"]["refresh_token"]
        jti_c = _decode_jti(refresh_token_c)
        assert jti_c != jti_b, "Token C must have a different jti than token B"

        # --- Step 7: Assert token_B is now revoked in Redis ---
        async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
            key_b_exists = await r.exists(_revoked_key(jti_b))
            ttl_b = await r.ttl(_revoked_key(jti_b))

        assert key_b_exists == 1, (
            f"Redis key '{_revoked_key(jti_b)}' must exist after token B is rotated"
        )
        assert ttl_b > 0, (
            f"Redis blacklist key for jti_B must have positive TTL, got {ttl_b}"
        )

        # --- Step 8: Reuse token_B → must return 401 ---
        reuse_b_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token_b},
        )
        assert reuse_b_resp.status_code == 401, (
            f"Reusing revoked token_B must return 401, got {reuse_b_resp.status_code}"
        )
