"""Integration tests: dev header gating to development environment only.

Verifies that:
- X-Clinic-Id / X-User-Id headers are accepted in development
- X-Clinic-Id / X-User-Id headers return 401 in non-development environments
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def dev_client():
    """HTTP client with environment patched to development (baseline)."""
    with patch("app.core.tenancy._IS_DEVELOPMENT", True):
        yield AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


@pytest.fixture
def prod_client():
    """HTTP client with environment patched to production."""
    with patch("app.core.tenancy._IS_DEVELOPMENT", False):
        yield AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


class TestDevHeaderGating:
    async def test_dev_headers_accepted_in_development(self, dev_client):
        """X-Clinic-Id / X-User-Id are accepted in development environment."""
        async with dev_client as ac:
            resp = await ac.get(
                "/api/v1/patients",
                headers={"X-Clinic-Id": str(uuid4()), "X-User-Id": str(uuid4())},
            )
        # 404 is fine — the route doesn't exist. 401 would mean auth failed.
        assert resp.status_code != 401, (
            f"Dev headers should be accepted in development, got {resp.status_code}: {resp.text}"
        )

    async def test_dev_headers_rejected_in_production(self, prod_client):
        """X-Clinic-Id / X-User-Id must return 401 in production environment."""
        async with prod_client as ac:
            resp = await ac.get(
                "/api/v1/patients",
                headers={"X-Clinic-Id": str(uuid4()), "X-User-Id": str(uuid4())},
            )
        assert resp.status_code == 401, (
            f"Dev headers must be rejected in production, got {resp.status_code}"
        )
        assert "not accepted outside development" in resp.json()["error"]["message"].lower() or \
               "development" in resp.json()["error"]["message"].lower(), (
            "401 response should mention dev-env restriction"
        )

    async def test_clinic_id_only_rejected_in_production(self, prod_client):
        """X-Clinic-Id alone also rejected in production."""
        async with prod_client as ac:
            resp = await ac.get(
                "/api/v1/patients",
                headers={"X-Clinic-Id": str(uuid4())},
            )
        assert resp.status_code == 401
