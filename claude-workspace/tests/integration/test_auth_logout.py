"""Integration tests: POST /api/v1/auth/logout.

Tests cover:
- Valid refresh token → 204, jti revoked in Redis (via mock)
- Subsequent refresh with same token → 401
- Malformed token → 204 (best-effort, no error)
- Expired token → 204 (best-effort, no error)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt

from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_refresh_token
from app.main import app


async def _mock_db_session():
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    yield mock


@pytest_asyncio.fixture
async def http_client():
    """HTTP client with get_db overridden (logout/logout-adjacent tests don't need real DB)."""
    app.dependency_overrides[get_db] = _mock_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


class TestLogoutEndpoint:
    @patch("app.modules.auth.services.auth_service.revoke_token")
    async def test_valid_token_logout_returns_204(self, mock_revoke, http_client):
        """Logout with valid token → 204 and revoke_token called."""
        mock_revoke.return_value = None

        token = create_refresh_token(uuid4(), uuid4())
        resp = await http_client.post("/api/v1/auth/logout", json={"refresh_token": token})

        assert resp.status_code == 204
        mock_revoke.assert_called_once()

    @patch("app.modules.auth.services.auth_service.revoke_token")
    async def test_revoke_called_with_correct_jti(self, mock_revoke, http_client):
        """revoke_token is called with the token's jti."""
        from app.core.security import decode_token

        mock_revoke.return_value = None

        token = create_refresh_token(uuid4(), uuid4())
        claims = decode_token(token)
        expected_jti = claims["jti"]

        await http_client.post("/api/v1/auth/logout", json={"refresh_token": token})

        mock_revoke.assert_called_once()
        # First positional argument should be the JTI string
        call_args = mock_revoke.call_args
        # revoke_token(jti, exp_dt) — jti is first arg
        actual_jti = call_args.args[0] if call_args.args else call_args.kwargs.get("jti")
        assert actual_jti == expected_jti

    async def test_malformed_token_logout_returns_204(self, http_client):
        """Malformed token → best-effort: 204 (no error raised)."""
        resp = await http_client.post(
            "/api/v1/auth/logout", json={"refresh_token": "not-a-jwt"}
        )
        assert resp.status_code == 204

    async def test_expired_token_logout_returns_204(self, http_client):
        """Expired token → best-effort: 204."""
        past = datetime.now(UTC) - timedelta(seconds=60)
        payload = {
            "sub": str(uuid4()),
            "clinic_id": str(uuid4()),
            "type": "refresh",
            "jti": str(uuid4()),
            "iat": past - timedelta(days=7),
            "exp": past,
        }
        expired = jose_jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        resp = await http_client.post("/api/v1/auth/logout", json={"refresh_token": expired})
        assert resp.status_code == 204

    @patch("app.core.token_blacklist._redis")
    async def test_subsequent_refresh_with_revoked_token_fails(
        self, mock_redis_cls, http_client
    ):
        """After logout (token revoked), same token used for refresh → 401."""
        mock_redis = AsyncMock()
        mock_redis.__aenter__ = AsyncMock(return_value=mock_redis)
        mock_redis.__aexit__ = AsyncMock(return_value=False)
        mock_redis.exists = AsyncMock(return_value=1)  # IS revoked
        mock_redis.setex = AsyncMock()
        mock_redis_cls.return_value = mock_redis

        token = create_refresh_token(uuid4(), uuid4())
        resp = await http_client.post("/api/v1/auth/refresh", json={"refresh_token": token})

        assert resp.status_code == 401
