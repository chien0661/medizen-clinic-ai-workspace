"""Integration tests: extra permission grant/deny logic.

Tests:
- extra_grant adds permission even when no role has it
- extra_deny removes permission even when a role grants it
- deny precedence over both role grants and extra grants
- add_extra_permission with unknown permission_code → ValueError
- remove_extra_permission soft-deletes and invalidates cache
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.users.models.user_extra_permission import ExtraPermType
from app.modules.users.services.rbac_service import (
    add_extra_permission,
    get_user_effective_permissions,
    remove_extra_permission,
)


class TestExtraGrant:
    @pytest.mark.asyncio
    async def test_extra_grant_adds_permission_without_role(self):
        """extra_grant gives permission even if no role provides it."""
        user_id = uuid4()
        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # user_roles query — no roles
                result.fetchall.return_value = []
            elif call_count == 2:
                # extra_perms query (role_perms query is skipped when role_ids=[])
                result.fetchall.return_value = [
                    ("invoice.void", ExtraPermType.grant),
                ]
            else:
                result.fetchall.return_value = []
            return result

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        with patch("app.modules.users.services.rbac_service._cache_get", return_value=None), \
             patch("app.modules.users.services.rbac_service._cache_set", return_value=None):
            perms = await get_user_effective_permissions(mock_db, user_id)

        assert "invoice.void" in perms

    @pytest.mark.asyncio
    async def test_extra_deny_removes_role_granted_permission(self):
        """extra_deny removes permission even when role grants it."""
        user_id = uuid4()
        role_id = uuid4()
        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.fetchall.return_value = [(role_id,)]
            elif call_count == 2:
                result.fetchall.return_value = [("invoice.void",), ("patient.read",)]
            elif call_count == 3:
                result.fetchall.return_value = [
                    ("invoice.void", ExtraPermType.deny),
                ]
            return result

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        with patch("app.modules.users.services.rbac_service._cache_get", return_value=None), \
             patch("app.modules.users.services.rbac_service._cache_set", return_value=None):
            perms = await get_user_effective_permissions(mock_db, user_id)

        assert "invoice.void" not in perms, "deny should remove role-granted permission"
        assert "patient.read" in perms, "other permissions should be unaffected"

    @pytest.mark.asyncio
    async def test_deny_overrides_extra_grant(self):
        """deny takes precedence over extra_grant for the same permission."""
        user_id = uuid4()
        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.fetchall.return_value = []  # no roles
            elif call_count == 2:
                # extra_perms: BOTH grant and deny for same code
                result.fetchall.return_value = [
                    ("invoice.void", ExtraPermType.grant),
                    ("invoice.void", ExtraPermType.deny),
                ]
            return result

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        with patch("app.modules.users.services.rbac_service._cache_get", return_value=None), \
             patch("app.modules.users.services.rbac_service._cache_set", return_value=None):
            perms = await get_user_effective_permissions(mock_db, user_id)

        assert "invoice.void" not in perms, "deny must override grant"


class TestAddExtraPermission:
    @pytest.mark.asyncio
    async def test_add_grant_success(self):
        """add_extra_permission creates a UserExtraPermission row."""
        user_id = uuid4()

        mock_db = AsyncMock()
        mock_perm = MagicMock()
        mock_db.get = AsyncMock(return_value=mock_perm)

        no_existing = MagicMock()
        no_existing.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=no_existing)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        with patch("app.modules.users.services.rbac_service.invalidate_user_cache") as inv:
            ep = await add_extra_permission(
                mock_db,
                user_id=user_id,
                permission_code="invoice.void",
                perm_type=ExtraPermType.grant,
                reason="Temporary override",
                granted_by=uuid4(),
            )

        mock_db.add.assert_called()
        inv.assert_awaited_once_with(user_id)
        assert ep.permission_code == "invoice.void"
        assert ep.type == ExtraPermType.grant

    @pytest.mark.asyncio
    async def test_add_permission_not_found(self):
        """Unknown permission_code → ValueError('permission_not_found')."""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="permission_not_found"):
            await add_extra_permission(
                mock_db,
                user_id=uuid4(),
                permission_code="nonexistent.perm",
                perm_type=ExtraPermType.grant,
                reason=None,
            )

    @pytest.mark.asyncio
    async def test_add_replaces_existing_override(self):
        """Existing active override is soft-deleted; new one created."""
        from datetime import UTC, datetime

        user_id = uuid4()

        mock_db = AsyncMock()
        mock_perm = MagicMock()
        mock_db.get = AsyncMock(return_value=mock_perm)

        existing_ep = MagicMock()
        existing_ep.is_deleted = False
        existing_result = MagicMock()
        existing_result.scalars.return_value.first.return_value = existing_ep
        mock_db.execute = AsyncMock(return_value=existing_result)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        with patch("app.modules.users.services.rbac_service.invalidate_user_cache"):
            await add_extra_permission(
                mock_db,
                user_id=user_id,
                permission_code="invoice.void",
                perm_type=ExtraPermType.deny,
                reason=None,
            )

        # Existing should be soft-deleted
        assert existing_ep.is_deleted is True


class TestRemoveExtraPermission:
    @pytest.mark.asyncio
    async def test_remove_success(self):
        """remove_extra_permission soft-deletes the row."""
        user_id = uuid4()
        ep_id = uuid4()

        mock_db = AsyncMock()
        mock_ep = MagicMock()
        mock_ep.id = ep_id
        mock_ep.user_id = user_id
        mock_ep.is_deleted = False
        mock_db.get = AsyncMock(return_value=mock_ep)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        with patch("app.modules.users.services.rbac_service.invalidate_user_cache") as inv:
            await remove_extra_permission(mock_db, user_id=user_id, ep_id=ep_id)

        assert mock_ep.is_deleted is True
        inv.assert_awaited_once_with(user_id)

    @pytest.mark.asyncio
    async def test_remove_not_found(self):
        """Missing ep → ValueError('extra_permission_not_found')."""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="extra_permission_not_found"):
            await remove_extra_permission(mock_db, user_id=uuid4(), ep_id=uuid4())

    @pytest.mark.asyncio
    async def test_remove_wrong_user(self):
        """ep belonging to different user → ValueError."""
        ep_id = uuid4()
        mock_db = AsyncMock()
        mock_ep = MagicMock()
        mock_ep.id = ep_id
        mock_ep.user_id = uuid4()  # different user
        mock_ep.is_deleted = False
        mock_db.get = AsyncMock(return_value=mock_ep)

        with pytest.raises(ValueError, match="extra_permission_not_found"):
            await remove_extra_permission(mock_db, user_id=uuid4(), ep_id=ep_id)
