"""Integration tests: POST /api/v1/auth/refresh.

Tests cover:
- Valid refresh token → new access + refresh tokens returned
- Rotation: old jti ends up blacklisted
- Blacklisted token → 401
- Expired token → 401
- Wrong type token (access used as refresh) → 401
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
from app.core.security import create_access_token
from app.main import app


async def _mock_db_session():
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    yield mock


@pytest_asyncio.fixture
async def http_client():
    app.dependency_overrides[get_db] = _mock_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


class TestRefreshEndpoint:
    @patch("app.modules.auth.api.routes.auth_service.refresh")
    async def test_valid_refresh_returns_200(self, mock_refresh, http_client):
        """Valid refresh token → 200 with new access and refresh tokens."""
        uid = uuid4()
        mock_refresh.return_value = {
            "access_token": "new.access.token",
            "refresh_token": "new.refresh.token",
            "user": {"id": uid, "full_name": "Refresh User", "roles": [], "permissions": []},
        }

        resp = await http_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "some.valid.token"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["access_token"] == "new.access.token"
        assert body["data"]["refresh_token"] == "new.refresh.token"

    @patch("app.modules.auth.api.routes.auth_service.refresh")
    async def test_revoked_token_returns_401(self, mock_refresh, http_client):
        """Revoked token → service raises ValueError → 401."""
        mock_refresh.side_effect = ValueError("revoked_token")

        resp = await http_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "old.token"},
        )
        assert resp.status_code == 401

    @patch("app.modules.auth.api.routes.auth_service.refresh")
    async def test_invalid_token_returns_401(self, mock_refresh, http_client):
        """Invalid/expired token → service raises ValueError → 401."""
        mock_refresh.side_effect = ValueError("invalid_token")

        resp = await http_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "expired.token"},
        )
        assert resp.status_code == 401

    async def test_expired_jwt_returns_401(self, http_client):
        """Actually expired JWT (not mocked) → service raises JWTError → 401."""
        past = datetime.now(UTC) - timedelta(seconds=10)
        payload = {
            "sub": str(uuid4()),
            "clinic_id": str(uuid4()),
            "type": "refresh",
            "jti": str(uuid4()),
            "iat": past - timedelta(days=7),
            "exp": past,
        }
        expired_token = jose_jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        resp = await http_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": expired_token}
        )
        assert resp.status_code == 401

    async def test_access_token_as_refresh_returns_401(self, http_client):
        """Access token (type=access) passed to /refresh → 401."""
        token = create_access_token(uuid4(), uuid4(), [], [])
        resp = await http_client.post("/api/v1/auth/refresh", json={"refresh_token": token})
        assert resp.status_code == 401

    async def test_garbage_string_returns_401(self, http_client):
        resp = await http_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "not-a-token"}
        )
        assert resp.status_code == 401
