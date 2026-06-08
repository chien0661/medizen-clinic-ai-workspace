"""Integration tests: JWT signature verification in non-development environments.

Verifies that:
- In non-development environments, an unsigned (alg=none) JWT is rejected with 401
- In non-development environments, a JWT with a wrong secret is rejected with 401
- In non-development environments, a properly signed JWT with correct secret passes

These tests patch ``settings.ENVIRONMENT`` and ``_IS_DEVELOPMENT`` in the tenancy
module so we can exercise production-mode behaviour without spinning up a separate
process.
"""

from __future__ import annotations

import base64
import json
from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt

from app.core.config import settings
from app.main import app


def _make_unsigned_jwt(clinic_id: str, sub: str) -> str:
    """Build a minimal unsigned (alg=none) JWT."""
    header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
    payload = (
        base64.urlsafe_b64encode(
            json.dumps({"clinic_id": clinic_id, "sub": sub}).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    return f"{header}.{payload}."


def _make_signed_jwt(clinic_id: str, sub: str, secret: str = settings.JWT_SECRET) -> str:
    """Build an HS256-signed JWT."""
    return jose_jwt.encode(
        {"clinic_id": clinic_id, "sub": sub},
        secret,
        algorithm="HS256",
    )


@pytest.fixture
def prod_client():
    """HTTP client with environment patched to production."""
    with (
        patch("app.core.tenancy.settings") as mock_settings,
        patch("app.core.tenancy._IS_DEVELOPMENT", False),
    ):
        mock_settings.JWT_SECRET = settings.JWT_SECRET
        mock_settings.JWT_ALGORITHM = settings.JWT_ALGORITHM
        mock_settings.ENVIRONMENT = "production"
        client = AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
        yield client


class TestJWTSignatureVerification:
    async def test_unsigned_jwt_rejected_in_production(self, prod_client):
        """Unsigned (alg=none) JWT must be rejected with 401 outside development."""
        token = _make_unsigned_jwt(str(uuid4()), str(uuid4()))
        async with prod_client as ac:
            resp = await ac.get(
                "/api/v1/patients",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 401, (
            f"Expected 401 for unsigned JWT in production, got {resp.status_code}"
        )

    async def test_wrong_secret_jwt_rejected_in_production(self, prod_client):
        """JWT signed with wrong secret must be rejected with 401."""
        token = _make_signed_jwt(str(uuid4()), str(uuid4()), secret="wrong-secret")
        async with prod_client as ac:
            resp = await ac.get(
                "/api/v1/patients",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 401, (
            f"Expected 401 for wrong-secret JWT in production, got {resp.status_code}"
        )

    async def test_valid_signed_jwt_passes_in_production(self, prod_client):
        """JWT signed with correct secret must pass auth (not 401)."""
        token = _make_signed_jwt(str(uuid4()), str(uuid4()))
        async with prod_client as ac:
            resp = await ac.get(
                "/api/v1/patients",
                headers={"Authorization": f"Bearer {token}"},
            )
        # Path doesn't exist → 404; the important thing is NOT 401
        assert resp.status_code != 401, (
            f"Valid signed JWT should not return 401, got {resp.status_code}"
        )
