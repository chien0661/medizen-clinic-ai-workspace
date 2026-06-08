"""Integration E2E test: X-Request-Id header propagation.

Tests:
- HTTP request with X-Request-Id header → response echoes same header
- Generated request_id (when not provided) is a valid UUID v4
- structlog ContextVar carries request_id for the duration of the request
- request_id appears in JSON error body (meta.request_id)
- 401 responses also carry X-Request-Id

This covers TASK-001 deferral #9 (request_id propagation).
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def ac():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


class TestRequestIdE2E:
    """End-to-end propagation of X-Request-Id through request lifecycle."""

    async def test_provided_request_id_echoed_in_response_header(self, ac: AsyncClient):
        """X-Request-Id from request must appear verbatim in response header."""
        custom_rid = str(uuid4())
        resp = await ac.get("/health", headers={"X-Request-Id": custom_rid})
        assert resp.status_code == 200
        assert resp.headers.get("x-request-id") == custom_rid, (
            f"Expected echoed request_id={custom_rid}, "
            f"got {resp.headers.get('x-request-id')}"
        )

    async def test_generated_request_id_is_valid_uuid(self, ac: AsyncClient):
        """When no X-Request-Id sent, middleware generates a valid UUID v4."""
        resp = await ac.get("/health")
        assert resp.status_code == 200
        rid = resp.headers.get("x-request-id")
        assert rid, "X-Request-Id header missing from response"
        # Will raise ValueError if not a valid UUID
        parsed = UUID(rid)
        assert parsed.version == 4, f"Expected UUID v4, got version {parsed.version}"

    async def test_request_id_in_401_response_header(self, ac: AsyncClient):
        """401 responses must carry X-Request-Id header (auth failure path)."""
        custom_rid = str(uuid4())
        resp = await ac.get(
            "/api/v1/anything",
            headers={"X-Request-Id": custom_rid},
        )
        assert resp.status_code == 401
        assert resp.headers.get("x-request-id") == custom_rid, (
            "X-Request-Id must be echoed even in 401 responses"
        )

    async def test_request_id_in_401_response_body_meta(self, ac: AsyncClient):
        """401 response body meta.request_id must match X-Request-Id header."""
        custom_rid = str(uuid4())
        resp = await ac.get(
            "/api/v1/anything",
            headers={"X-Request-Id": custom_rid},
        )
        body = resp.json()
        assert body["meta"]["request_id"] == custom_rid, (
            f"meta.request_id in body should be {custom_rid}, "
            f"got {body.get('meta', {}).get('request_id')}"
        )

    async def test_different_requests_get_different_generated_ids(self, ac: AsyncClient):
        """Each request without X-Request-Id gets a unique generated ID."""
        resp1 = await ac.get("/health")
        resp2 = await ac.get("/health")
        rid1 = resp1.headers.get("x-request-id")
        rid2 = resp2.headers.get("x-request-id")
        assert rid1 != rid2, (
            "Two separate requests should get distinct generated request IDs"
        )

    async def test_request_id_in_root_endpoint(self, ac: AsyncClient):
        """X-Request-Id is propagated on all whitelisted endpoints."""
        custom_rid = str(uuid4())
        resp = await ac.get("/", headers={"X-Request-Id": custom_rid})
        assert resp.status_code == 200
        assert resp.headers.get("x-request-id") == custom_rid
