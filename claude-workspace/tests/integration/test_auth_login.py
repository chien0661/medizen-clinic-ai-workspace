"""Integration tests: POST /api/v1/auth/login.

Tests cover:
- Wrong clinic code → 401
- Wrong password → 401
- Inactive user → 401
- Locked user → 423
- Missing required fields → 422

Note: Full DB integration tests (e.g., testing last_login_at, audit log) are
covered in test_auth_service_db.py using the service layer directly.
HTTP-layer tests here use mocked services to avoid cross-loop issues.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.db import get_db
from app.main import app


async def _mock_db_session():
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    yield mock


@pytest_asyncio.fixture
async def http_client():
    """HTTP client with mocked DB session — service layer is mocked too."""
    app.dependency_overrides[get_db] = _mock_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


class TestLoginEndpoint:
    @patch("app.modules.auth.api.routes.auth_service.login")
    async def test_successful_login_returns_200(self, mock_login, http_client):
        """Successful login → 200 with access_token, refresh_token, user."""
        from uuid import uuid4

        uid = uuid4()
        mock_login.return_value = {
            "access_token": "access.token.here",
            "refresh_token": "refresh.token.here",
            "user": {"id": uid, "full_name": "Test User", "roles": [], "permissions": []},
        }

        resp = await http_client.post(
            "/api/v1/auth/login",
            json={"clinic_code": "TEST", "username": "user", "password": "pass"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert body["data"]["access_token"] == "access.token.here"
        assert body["data"]["refresh_token"] == "refresh.token.here"
        assert "user" in body["data"]

    @patch("app.modules.auth.api.routes.auth_service.login")
    async def test_wrong_credentials_returns_401(self, mock_login, http_client):
        """Invalid credentials → service raises ValueError → 401."""
        mock_login.side_effect = ValueError("invalid_credentials")

        resp = await http_client.post(
            "/api/v1/auth/login",
            json={"clinic_code": "TEST", "username": "user", "password": "wrong"},
        )
        assert resp.status_code == 401

    @patch("app.modules.auth.api.routes.auth_service.login")
    async def test_inactive_user_returns_401(self, mock_login, http_client):
        """Inactive user → service raises ValueError → 401."""
        mock_login.side_effect = ValueError("inactive_user")

        resp = await http_client.post(
            "/api/v1/auth/login",
            json={"clinic_code": "TEST", "username": "user", "password": "pass"},
        )
        assert resp.status_code == 401

    @patch("app.modules.auth.api.routes.auth_service.login")
    async def test_locked_user_returns_423(self, mock_login, http_client):
        """Locked user → service raises ValueError → 423."""
        mock_login.side_effect = ValueError("locked_user")

        resp = await http_client.post(
            "/api/v1/auth/login",
            json={"clinic_code": "TEST", "username": "user", "password": "pass"},
        )
        assert resp.status_code == 423

    async def test_missing_fields_returns_422(self, http_client):
        """Missing required fields → FastAPI validation → 422."""
        resp = await http_client.post(
            "/api/v1/auth/login",
            json={"username": "user"},  # missing clinic_code and password
        )
        assert resp.status_code == 422
