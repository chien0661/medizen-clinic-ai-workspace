"""Integration tests: request_id middleware behaviour (TASK-001 deferral #9).

Tests:
- /health returns X-Request-Id header always
- X-Request-Id from request is echoed back in response
- A generated request_id is a valid UUID v4
- Protected endpoints also return X-Request-Id even on 401
"""

from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c


class TestRequestIdHeader:
    async def test_health_always_has_request_id(self, ac: AsyncClient):
        resp = await ac.get("/health")
        assert resp.status_code == 200
        assert "x-request-id" in resp.headers

    async def test_generated_request_id_is_uuid(self, ac: AsyncClient):
        resp = await ac.get("/health")
        rid = resp.headers["x-request-id"]
        UUID(rid)  # raises ValueError if not a valid UUID

    async def test_custom_request_id_preserved(self, ac: AsyncClient):
        custom = str(uuid4())
        resp = await ac.get("/health", headers={"X-Request-Id": custom})
        assert resp.headers["x-request-id"] == custom

    async def test_401_response_has_request_id_header(self, ac: AsyncClient):
        """Even 401 responses must carry X-Request-Id."""
        resp = await ac.get("/api/v1/anything")
        assert resp.status_code == 401
        assert "x-request-id" in resp.headers

    async def test_401_body_meta_request_id_matches_header(self, ac: AsyncClient):
        """Body meta.request_id should match X-Request-Id header."""
        resp = await ac.get("/api/v1/anything")
        body = resp.json()
        header_rid = resp.headers["x-request-id"]
        body_rid = body["meta"]["request_id"]
        assert header_rid == body_rid

    async def test_custom_rid_propagated_to_401_body(self, ac: AsyncClient):
        custom = str(uuid4())
        resp = await ac.get(
            "/api/v1/anything", headers={"X-Request-Id": custom}
        )
        body = resp.json()
        assert body["meta"]["request_id"] == custom
