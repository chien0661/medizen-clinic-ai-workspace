"""Unit tests for TenancyMiddleware.

Tests cover:
- Whitelist paths are allowed without auth
- Protected paths require auth
- Dev headers (X-Clinic-Id / X-User-Id) set context correctly
- JWT Bearer sets context correctly
- Invalid JWT returns 401
- Missing auth on protected path returns 401
- X-Request-Id header is preserved (or generated)
- request_id appears in response headers
"""

import base64
import json
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def _make_jwt(clinic_id: str | None = None, sub: str | None = None) -> str:
    """Build a minimal unsigned JWT for testing purposes."""
    header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
    payload_data: dict = {}
    if clinic_id is not None:
        payload_data["clinic_id"] = clinic_id
    if sub is not None:
        payload_data["sub"] = sub
    payload = (
        base64.urlsafe_b64encode(json.dumps(payload_data).encode())
        .rstrip(b"=")
        .decode()
    )
    return f"{header}.{payload}."


@pytest.fixture
async def ac():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c


# ---------------------------------------------------------------------------
# Whitelist tests
# ---------------------------------------------------------------------------


class TestWhitelistPaths:
    async def test_health_no_auth(self, ac: AsyncClient):
        resp = await ac.get("/health")
        assert resp.status_code == 200

    async def test_root_no_auth(self, ac: AsyncClient):
        resp = await ac.get("/")
        assert resp.status_code == 200

    async def test_docs_no_auth(self, ac: AsyncClient):
        resp = await ac.get("/docs")
        # FastAPI may return 200 or redirect — not 401
        assert resp.status_code != 401

    async def test_openapi_json_no_auth(self, ac: AsyncClient):
        resp = await ac.get("/openapi.json")
        assert resp.status_code == 200

    async def test_redoc_no_auth(self, ac: AsyncClient):
        resp = await ac.get("/redoc")
        assert resp.status_code != 401


# ---------------------------------------------------------------------------
# 401 on protected paths without auth
# ---------------------------------------------------------------------------


class TestProtectedPaths:
    async def test_unknown_path_no_auth_returns_401(self, ac: AsyncClient):
        resp = await ac.get("/api/v1/patients")
        assert resp.status_code == 401

    async def test_401_body_shape(self, ac: AsyncClient):
        resp = await ac.get("/api/v1/patients")
        body = resp.json()
        assert body["error"]["code"] == "UNAUTHORIZED"
        assert "request_id" in body["meta"]

    async def test_401_has_request_id_header(self, ac: AsyncClient):
        resp = await ac.get("/api/v1/patients")
        assert "x-request-id" in resp.headers


# ---------------------------------------------------------------------------
# Dev headers
# ---------------------------------------------------------------------------


class TestDevHeaders:
    async def test_dev_headers_bypass_jwt(self, ac: AsyncClient):
        clinic = str(uuid4())
        user = str(uuid4())
        resp = await ac.get(
            "/api/v1/patients",
            headers={"X-Clinic-Id": clinic, "X-User-Id": user},
        )
        # Path doesn't exist yet → 404 or 422, not 401
        assert resp.status_code != 401

    async def test_invalid_clinic_id_returns_401(self, ac: AsyncClient):
        resp = await ac.get(
            "/api/v1/patients",
            headers={"X-Clinic-Id": "not-a-uuid"},
        )
        assert resp.status_code == 401

    async def test_invalid_user_id_returns_401(self, ac: AsyncClient):
        resp = await ac.get(
            "/api/v1/patients",
            headers={"X-Clinic-Id": str(uuid4()), "X-User-Id": "bad-uuid"},
        )
        assert resp.status_code == 401

    async def test_clinic_id_only_no_user_allowed(self, ac: AsyncClient):
        """X-User-Id is optional when using dev headers."""
        clinic = str(uuid4())
        resp = await ac.get(
            "/api/v1/patients",
            headers={"X-Clinic-Id": clinic},
        )
        assert resp.status_code != 401


# ---------------------------------------------------------------------------
# JWT Bearer
# ---------------------------------------------------------------------------


class TestJWTBearer:
    async def test_valid_jwt_passes(self, ac: AsyncClient):
        token = _make_jwt(clinic_id=str(uuid4()), sub=str(uuid4()))
        resp = await ac.get(
            "/api/v1/patients",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code != 401

    async def test_jwt_missing_clinic_id_returns_401(self, ac: AsyncClient):
        token = _make_jwt(sub=str(uuid4()))  # no clinic_id
        resp = await ac.get(
            "/api/v1/patients",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
        assert "clinic_id" in resp.json()["error"]["message"]

    async def test_malformed_bearer_returns_401(self, ac: AsyncClient):
        resp = await ac.get(
            "/api/v1/patients",
            headers={"Authorization": "Bearer not.a.jwt"},
        )
        # "not.a.jwt" decodes but payload might be empty — expect 401
        assert resp.status_code == 401

    async def test_wrong_auth_scheme_returns_401(self, ac: AsyncClient):
        resp = await ac.get(
            "/api/v1/patients",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Request ID
# ---------------------------------------------------------------------------


class TestRequestId:
    async def test_request_id_generated_if_missing(self, ac: AsyncClient):
        resp = await ac.get("/health")
        assert "x-request-id" in resp.headers
        rid = resp.headers["x-request-id"]
        # Should be a valid UUID
        UUID(rid)  # raises ValueError if not valid

    async def test_request_id_preserved_from_header(self, ac: AsyncClient):
        custom_rid = str(uuid4())
        resp = await ac.get("/health", headers={"X-Request-Id": custom_rid})
        assert resp.headers["x-request-id"] == custom_rid
