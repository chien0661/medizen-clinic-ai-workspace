"""Integration tests: JWT payload includes real roles + permissions after login.

Tests:
- After login with RBAC, decoded JWT contains roles list and permissions list
- Roles and permissions come from DB (mocked for unit test layer)
- Empty roles → empty JWT claims
- auth_service now calls rbac_service instead of placeholder
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.security import create_access_token, decode_token
from app.modules.auth.services import auth_service


class TestJwtIncludesPermissions:
    def test_access_token_contains_roles_and_permissions(self):
        """create_access_token embeds roles + permissions in JWT payload."""
        user_id = uuid4()
        clinic_id = uuid4()
        roles = ["doctor", "nurse"]
        permissions = ["patient.read", "vital.write", "visit.read"]

        token = create_access_token(user_id, clinic_id, roles, permissions)
        claims = decode_token(token)

        assert claims["roles"] == roles
        assert claims["permissions"] == permissions
        assert claims["sub"] == str(user_id)
        assert claims["clinic_id"] == str(clinic_id)
        assert claims["type"] == "access"

    def test_empty_roles_and_permissions_in_jwt(self):
        """User with no roles → JWT has empty lists."""
        token = create_access_token(uuid4(), uuid4(), [], [])
        claims = decode_token(token)

        assert claims["roles"] == []
        assert claims["permissions"] == []

    @pytest.mark.asyncio
    async def test_login_calls_rbac_service(self):
        """auth_service.login() calls rbac_service for roles + permissions."""
        mock_db = AsyncMock()

        mock_clinic = MagicMock()
        mock_clinic.is_active = True
        mock_clinic.id = uuid4()

        mock_user = MagicMock()
        mock_user.is_locked = False
        mock_user.is_active = True
        mock_user.id = uuid4()
        mock_user.failed_login_count = 0
        mock_user.full_name = "Test Doctor"

        with patch(
            "app.modules.auth.services.auth_service._get_clinic_by_code",
            return_value=mock_clinic,
        ), patch(
            "app.modules.auth.services.auth_service._get_user",
            return_value=mock_user,
        ), patch(
            "app.modules.auth.services.auth_service.verify_password",
            return_value=True,
        ), patch(
            "app.modules.auth.services.auth_service.record_failed_attempt",
        ), patch(
            "app.modules.auth.services.auth_service.clear_failed_attempts",
        ), patch(
            "app.modules.auth.services.auth_service.write_audit",
        ), patch(
            "app.modules.users.services.rbac_service.get_user_role_codes",
            return_value=["doctor"],
        ) as mock_roles, patch(
            "app.modules.users.services.rbac_service.get_user_effective_permissions",
            return_value={"patient.read", "vital.write"},
        ) as mock_perms:
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()

            result = await auth_service.login(
                mock_db,
                username="doc1",
                password="secret",
                clinic_code="CLINIC01",
            )

        mock_roles.assert_awaited_once()
        mock_perms.assert_awaited_once()

        assert result["user"]["roles"] == ["doctor"]
        assert set(result["user"]["permissions"]) == {"patient.read", "vital.write"}

    @pytest.mark.asyncio
    async def test_login_jwt_contains_rbac_data(self):
        """Decoded access token from login contains role codes and permission codes."""
        mock_db = AsyncMock()
        user_id = uuid4()
        clinic_id = uuid4()

        mock_clinic = MagicMock()
        mock_clinic.is_active = True
        mock_clinic.id = clinic_id

        mock_user = MagicMock()
        mock_user.is_locked = False
        mock_user.is_active = True
        mock_user.id = user_id
        mock_user.failed_login_count = 0
        mock_user.full_name = "Admin User"

        with patch(
            "app.modules.auth.services.auth_service._get_clinic_by_code",
            return_value=mock_clinic,
        ), patch(
            "app.modules.auth.services.auth_service._get_user",
            return_value=mock_user,
        ), patch(
            "app.modules.auth.services.auth_service.verify_password",
            return_value=True,
        ), patch(
            "app.modules.auth.services.auth_service.record_failed_attempt",
        ), patch(
            "app.modules.auth.services.auth_service.clear_failed_attempts",
        ), patch(
            "app.modules.auth.services.auth_service.write_audit",
        ), patch(
            "app.modules.users.services.rbac_service.get_user_role_codes",
            return_value=["admin"],
        ), patch(
            "app.modules.users.services.rbac_service.get_user_effective_permissions",
            return_value={"user.manage", "role.manage", "patient.read"},
        ):
            mock_db.add = MagicMock()
            mock_db.flush = AsyncMock()

            result = await auth_service.login(
                mock_db,
                username="admin",
                password="admin_pass",
                clinic_code="CLINIC01",
            )

        access_token = result["access_token"]
        claims = decode_token(access_token)

        assert "admin" in claims["roles"]
        assert "user.manage" in claims["permissions"]
        assert "role.manage" in claims["permissions"]

    def test_jwt_uses_rbac_service_not_placeholder(self):
        """Ensure auth_service imports and uses rbac_service (not placeholder lists)."""
        import inspect

        from app.modules.auth.services import auth_service as svc

        source = inspect.getsource(svc)
        # Must import rbac_service
        assert "rbac_service" in source, (
            "auth_service should import rbac_service for TASK-004"
        )
        # Must call get_user_role_codes
        assert "get_user_role_codes" in source, (
            "auth_service.login should call rbac_service.get_user_role_codes"
        )
