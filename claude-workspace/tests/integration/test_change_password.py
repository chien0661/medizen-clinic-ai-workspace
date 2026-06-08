"""Integration tests: POST /api/v1/auth/change-password.

Tests cover:
- No auth token → 401 (TenancyMiddleware blocks)
- Wrong old password → 401
- Correct old password → 204
- Missing required field → 422
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.db import get_db
from app.core.security import create_access_token
from app.main import app


async def _mock_db_session():
    """Yield a minimal mock DB session to bypass real DB in endpoint tests."""
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    yield mock


@pytest_asyncio.fixture
async def http_client_no_db():
    """HTTP client with get_db dependency overridden to skip real DB."""
    app.dependency_overrides[get_db] = _mock_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac


class TestChangePasswordEndpoint:
    async def test_no_auth_returns_401(self, http_client):
        """No Authorization header → TenancyMiddleware returns 401."""
        resp = await http_client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "old", "new_password": "newpassword123"},
        )
        assert resp.status_code == 401

    @patch("app.modules.auth.api.routes.auth_service.change_password")
    async def test_wrong_old_password_returns_401(self, mock_change, http_client_no_db):
        """Wrong old password → service raises ValueError → 401."""
        mock_change.side_effect = ValueError("invalid_credentials")

        user_id = uuid4()
        clinic_id = uuid4()
        token = create_access_token(user_id, clinic_id, [], [])

        resp = await http_client_no_db.post(
            "/api/v1/auth/change-password",
            json={"old_password": "WRONG_OLD", "new_password": "NewPassword123!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    @patch("app.modules.auth.api.routes.auth_service.change_password")
    async def test_correct_old_password_returns_204(self, mock_change, http_client_no_db):
        """Correct old password → 204."""
        mock_change.return_value = None  # success

        user_id = uuid4()
        clinic_id = uuid4()
        token = create_access_token(user_id, clinic_id, [], [])

        resp = await http_client_no_db.post(
            "/api/v1/auth/change-password",
            json={"old_password": "OldPassword123!", "new_password": "NewPassword456!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

    async def test_missing_new_password_returns_422(self, http_client):
        """Missing required new_password field → 422 (caught before auth)."""
        user_id = uuid4()
        clinic_id = uuid4()
        token = create_access_token(user_id, clinic_id, [], [])

        resp = await http_client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "OldPassword123!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
