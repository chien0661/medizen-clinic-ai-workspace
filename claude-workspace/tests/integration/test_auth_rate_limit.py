"""Integration tests: rate limiting on POST /api/v1/auth/login.

Tests cover:
- 10 requests in rapid succession: first 10 pass (may 401 for wrong creds, not 429)
- 11th request → 429 Too Many Requests
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.db import get_db
from app.core.rate_limit import limiter
from app.main import app


async def _mock_db_session():
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    yield mock


@pytest_asyncio.fixture
async def http_client():
    # Reset the limiter storage before the test so prior login requests don't pollute it
    limiter.reset()
    app.dependency_overrides[get_db] = _mock_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


class TestRateLimit:
    @patch("app.modules.auth.api.routes.auth_service.login")
    async def test_eleventh_request_returns_429(self, mock_login, http_client):
        """11th login request in < 1 minute from the same IP → 429."""
        # Service always returns 401 for non-existent clinic (doesn't matter for rate limit test)
        mock_login.side_effect = ValueError("invalid_credentials")

        body = {"clinic_code": "NOPE", "username": "u", "password": "p"}
        status_codes = []
        for _ in range(11):
            resp = await http_client.post("/api/v1/auth/login", json=body)
            status_codes.append(resp.status_code)

        # The 11th should be 429
        assert status_codes[-1] == 429, (
            f"Expected last request to return 429, got {status_codes[-1]}. "
            f"All codes: {status_codes}"
        )
        # First 10 must NOT be 429
        for code in status_codes[:10]:
            assert code != 429, f"Expected first 10 not to be 429, got {code}"
