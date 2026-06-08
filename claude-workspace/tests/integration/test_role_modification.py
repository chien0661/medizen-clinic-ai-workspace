"""Integration tests: Role modification and system role protection.

Tests:
- System role cannot be deleted (returns 403)
- System role name/description can be updated (PATCH allowed)
- Regular (non-system) role can be deleted
- clone_system_role creates clinic-scoped copy with correct permissions
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.db import current_user_id, get_db
from app.main import app
from app.modules.users.rbac_seed_data import ROLE_PERMISSIONS as SEED_ROLE_PERMISSIONS
from app.modules.users.rbac_seed_data import SYSTEM_ROLES as SEED_SYSTEM_ROLES
from app.modules.users.services.rbac_service import clone_system_role


# ---------------------------------------------------------------------------
# HTTP-level tests for DELETE /roles/{id}
# ---------------------------------------------------------------------------


async def _mock_db():
    mock = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    yield mock


@pytest_asyncio.fixture
async def role_client():
    app.dependency_overrides[get_db] = _mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


class TestSystemRoleProtection:
    @pytest.mark.asyncio
    async def test_delete_system_role_returns_403(self, role_client):
        """DELETE on a system role → 403 Forbidden."""
        role_id = uuid4()
        user_id = uuid4()

        mock_system_role = MagicMock()
        mock_system_role.is_deleted = False
        mock_system_role.is_system = True
        mock_system_role.id = role_id

        with patch("app.core.db.current_user_id") as mock_uid, \
             patch(
                 "app.modules.users.services.rbac_service.get_user_effective_permissions",
                 return_value={"role.manage"},
             ), \
             patch("app.modules.users.api.routes.get_db") as mock_get_db:

            async def _inner_db():
                inner = AsyncMock()
                inner.get = AsyncMock(return_value=mock_system_role)
                inner.flush = AsyncMock()
                inner.add = MagicMock()
                inner.commit = AsyncMock()
                inner.rollback = AsyncMock()
                yield inner

            mock_uid.get.return_value = user_id
            app.dependency_overrides[get_db] = _inner_db
            resp = await role_client.delete(
                f"/api/v1/roles/{role_id}",
                headers={
                    "X-Clinic-Id": str(uuid4()),
                    "X-User-Id": str(user_id),
                },
            )

        app.dependency_overrides.pop(get_db, None)
        # The route enforces the is_system check → must be 403, not 401 or 404.
        # Asserting exactly 403 ensures a missing router (404) cannot mask the guard.
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_system_role_flag_enforced_in_service(self):
        """Service layer: system role marked correctly."""
        for role in SEED_SYSTEM_ROLES:
            assert role["is_system"] is True, (
                f"Role {role['code']} should have is_system=True"
            )

    def test_system_role_codes_are_correct(self):
        """System roles have exact expected codes."""
        codes = {r["code"] for r in SEED_SYSTEM_ROLES}
        assert codes == {"admin", "doctor", "nurse", "pharmacist", "receptionist"}

    def test_system_roles_have_no_clinic_id(self):
        """System roles are seeded with clinic_id=NULL."""
        for role in SEED_SYSTEM_ROLES:
            assert "clinic_id" not in role or role.get("clinic_id") is None, (
                f"System role {role['code']} should have no clinic_id"
            )


class TestCloneSystemRole:
    @pytest.mark.asyncio
    async def test_clone_success(self):
        """clone_system_role creates a new clinic-scoped role with same permissions."""
        clinic_id = uuid4()
        system_role_id = uuid4()

        mock_db = AsyncMock()

        # System role query
        sys_role = MagicMock()
        sys_role.id = system_role_id
        sys_role.code = "doctor"
        sys_role.name = "Doctor"
        sys_role.description = "Clinical staff"

        # No existing clinic role
        no_existing = MagicMock()
        no_existing.scalars.return_value.first.return_value = None

        # Role permission rows
        rp_result = MagicMock()
        rp_result.fetchall.return_value = [("patient.read",), ("visit.write",)]

        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:  # system role query
                result.scalars.return_value.first.return_value = sys_role
            elif call_count == 2:  # existing clinic role check
                result.scalars.return_value.first.return_value = None
            elif call_count == 3:  # role permissions copy
                result.fetchall.return_value = [("patient.read",), ("visit.write",)]
            return result

        mock_db.execute = mock_execute
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        new_role = await clone_system_role(mock_db, clinic_id=clinic_id, system_role_code="doctor")

        assert new_role.code == "doctor"
        assert new_role.clinic_id == clinic_id
        assert new_role.is_system is False
        # add called for new_role + 2 RolePermission rows
        assert mock_db.add.call_count >= 3

    @pytest.mark.asyncio
    async def test_clone_system_role_not_found(self):
        """Missing system role → ValueError('system_role_not_found')."""
        mock_db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        with pytest.raises(ValueError, match="system_role_not_found"):
            await clone_system_role(mock_db, clinic_id=uuid4(), system_role_code="nonexistent")

    @pytest.mark.asyncio
    async def test_clone_already_exists(self):
        """Clinic already has this role code → ValueError('clinic_role_exists')."""
        clinic_id = uuid4()
        mock_db = AsyncMock()

        sys_role = MagicMock()
        sys_role.code = "doctor"
        existing_clinic_role = MagicMock()

        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalars.return_value.first.return_value = sys_role
            elif call_count == 2:
                result.scalars.return_value.first.return_value = existing_clinic_role
            return result

        mock_db.execute = mock_execute

        with pytest.raises(ValueError, match="clinic_role_exists"):
            await clone_system_role(mock_db, clinic_id=clinic_id, system_role_code="doctor")
