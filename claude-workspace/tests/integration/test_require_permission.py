"""Integration tests: require_permission FastAPI dependency.

Tests:
- Endpoint with require_permission returns 403 when permission missing
- Endpoint with require_permission returns 200 when permission present
- Unauthenticated request returns 401
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI, Request, status
from httpx import ASGITransport, AsyncClient

from app.core.db import current_user_id, get_db
from app.core.exceptions import register_exception_handlers
from app.core.permissions import require_permission

# ---------------------------------------------------------------------------
# Minimal test app with a protected endpoint + middleware to set ContextVar
# ---------------------------------------------------------------------------

_test_app = FastAPI()
register_exception_handlers(_test_app)


@_test_app.middleware("http")
async def inject_user_id(request: Request, call_next):
    """Middleware that reads X-Test-User-Id header and sets the ContextVar."""
    raw_uid = request.headers.get("X-Test-User-Id")
    if raw_uid:
        token = current_user_id.set(uuid4() if raw_uid == "auto" else
                                    __import__("uuid").UUID(raw_uid))
        try:
            return await call_next(request)
        finally:
            current_user_id.reset(token)
    return await call_next(request)


@_test_app.get(
    "/test-patient-write",
    dependencies=[Depends(require_permission("patient.write"))],
)
async def test_endpoint_patient_write():
    return {"ok": True}


@_test_app.get(
    "/test-invoice-void",
    dependencies=[Depends(require_permission("invoice.void"))],
)
async def test_endpoint_invoice_void():
    return {"ok": True}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


async def _mock_db():
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    yield mock


@pytest_asyncio.fixture
async def permission_client():
    _test_app.dependency_overrides[get_db] = _mock_db
    async with AsyncClient(
        transport=ASGITransport(app=_test_app), base_url="http://testserver"
    ) as ac:
        yield ac
    _test_app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRequirePermission:
    @pytest.mark.asyncio
    async def test_permission_present_returns_200(self, permission_client):
        """User with required permission → 200."""
        user_id = uuid4()

        with patch(
            "app.modules.users.services.rbac_service.get_user_effective_permissions",
            return_value={"patient.write", "visit.read"},
        ):
            resp = await permission_client.get(
                "/test-patient-write",
                headers={"X-Test-User-Id": str(user_id)},
            )

        assert resp.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_permission_missing_returns_403(self, permission_client):
        """User missing required permission → 403."""
        user_id = uuid4()

        with patch(
            "app.modules.users.services.rbac_service.get_user_effective_permissions",
            return_value={"patient.read"},  # has read but NOT write
        ):
            resp = await permission_client.get(
                "/test-patient-write",
                headers={"X-Test-User-Id": str(user_id)},
            )

        assert resp.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, permission_client):
        """No user_id in context → 401."""
        # No X-Test-User-Id header → ContextVar stays None
        resp = await permission_client.get("/test-patient-write")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_doctor_cannot_void_invoice(self, permission_client):
        """Doctor (no invoice.void) → 403 on invoice void endpoint."""
        user_id = uuid4()
        doctor_perms = {
            "patient.read", "patient.write",
            "visit.read", "visit.write", "visit.cancel",
            "vital.read", "vital.write",
            "service.perform",
            "prescription.write", "prescription.cancel", "prescription.print",
            "invoice.create",
            "report.view",
        }

        with patch(
            "app.modules.users.services.rbac_service.get_user_effective_permissions",
            return_value=doctor_perms,
        ):
            resp = await permission_client.get(
                "/test-invoice-void",
                headers={"X-Test-User-Id": str(user_id)},
            )

        assert resp.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_admin_can_void_invoice(self, permission_client):
        """Admin (has invoice.void) → 200 on invoice void endpoint."""
        user_id = uuid4()

        from app.modules.users.rbac_seed_data import PERMISSIONS as SEED_PERMISSIONS

        all_perms = {p["code"] for p in SEED_PERMISSIONS}

        with patch(
            "app.modules.users.services.rbac_service.get_user_effective_permissions",
            return_value=all_perms,
        ):
            resp = await permission_client.get(
                "/test-invoice-void",
                headers={"X-Test-User-Id": str(user_id)},
            )

        assert resp.status_code == status.HTTP_200_OK


class TestRequirePermissionImport:
    def test_require_permission_importable(self):
        """require_permission can be imported from app.core.permissions."""
        from app.core.permissions import require_permission

        dep = require_permission("patient.write")
        assert callable(dep)
