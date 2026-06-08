"""Integration tests: role assignment and revocation.

Tests:
- assign_role → effective permissions include role's permissions
- revoke_role → effective permissions no longer include role's permissions
- duplicate assignment → ValueError
- assign non-existent role → ValueError
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.users.services.rbac_service import (
    assign_role,
    get_user_effective_permissions,
    revoke_role,
)


class TestAssignRole:
    @pytest.mark.asyncio
    async def test_assign_role_success(self):
        """assign_role stores UserRole row and invalidates cache."""
        user_id = uuid4()
        role_id = uuid4()

        mock_db = AsyncMock()

        # Mock db.get for Role — return active role
        mock_role = MagicMock()
        mock_role.is_deleted = False
        mock_db.get = AsyncMock(return_value=mock_role)

        # Mock check duplicate — no existing assignment
        no_result = MagicMock()
        no_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=no_result)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        with patch("app.modules.users.services.rbac_service.invalidate_user_cache") as inv:
            ur = await assign_role(mock_db, user_id=user_id, role_id=role_id)

        mock_db.add.assert_called_once()
        inv.assert_awaited_once_with(user_id)
        assert ur.user_id == user_id
        assert ur.role_id == role_id

    @pytest.mark.asyncio
    async def test_assign_role_not_found(self):
        """Role not found → ValueError('role_not_found')."""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="role_not_found"):
            await assign_role(mock_db, user_id=uuid4(), role_id=uuid4())

    @pytest.mark.asyncio
    async def test_assign_role_deleted_role(self):
        """Soft-deleted role → ValueError('role_not_found')."""
        mock_db = AsyncMock()
        mock_role = MagicMock()
        mock_role.is_deleted = True
        mock_db.get = AsyncMock(return_value=mock_role)

        with pytest.raises(ValueError, match="role_not_found"):
            await assign_role(mock_db, user_id=uuid4(), role_id=uuid4())

    @pytest.mark.asyncio
    async def test_assign_role_duplicate(self):
        """Duplicate assignment → ValueError('role_already_assigned')."""
        mock_db = AsyncMock()
        mock_role = MagicMock()
        mock_role.is_deleted = False
        mock_db.get = AsyncMock(return_value=mock_role)

        existing_ur = MagicMock()
        dup_result = MagicMock()
        dup_result.scalars.return_value.first.return_value = existing_ur
        mock_db.execute = AsyncMock(return_value=dup_result)

        with pytest.raises(ValueError, match="role_already_assigned"):
            await assign_role(mock_db, user_id=uuid4(), role_id=uuid4())


class TestRevokeRole:
    @pytest.mark.asyncio
    async def test_revoke_role_success(self):
        """revoke_role deletes UserRole and invalidates cache."""
        user_id = uuid4()
        role_id = uuid4()

        mock_db = AsyncMock()
        existing_ur = MagicMock()
        result = MagicMock()
        result.scalars.return_value.first.return_value = existing_ur
        mock_db.execute = AsyncMock(return_value=result)
        mock_db.delete = AsyncMock()
        mock_db.flush = AsyncMock()

        with patch("app.modules.users.services.rbac_service.invalidate_user_cache") as inv:
            await revoke_role(mock_db, user_id=user_id, role_id=role_id)

        mock_db.delete.assert_awaited_once_with(existing_ur)
        inv.assert_awaited_once_with(user_id)

    @pytest.mark.asyncio
    async def test_revoke_role_not_found(self):
        """Assignment not found → ValueError('assignment_not_found')."""
        mock_db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        with pytest.raises(ValueError, match="assignment_not_found"):
            await revoke_role(mock_db, user_id=uuid4(), role_id=uuid4())


class TestEffectivePermissionsAfterAssign:
    @pytest.mark.asyncio
    async def test_effective_includes_role_perms(self):
        """After assigning a role, effective perms include role's permissions."""
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
                result.fetchall.return_value = [
                    ("patient.read",), ("visit.write",), ("vital.write",)
                ]
            elif call_count == 3:
                result.fetchall.return_value = []
            return result

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        with patch("app.modules.users.services.rbac_service._cache_get", return_value=None), \
             patch("app.modules.users.services.rbac_service._cache_set", return_value=None):
            perms = await get_user_effective_permissions(mock_db, user_id)

        assert "patient.read" in perms
        assert "visit.write" in perms
        assert "vital.write" in perms

    @pytest.mark.asyncio
    async def test_effective_empty_after_revoke(self):
        """After revoking all roles, effective perms are empty (no extras)."""
        user_id = uuid4()
        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.fetchall.return_value = []
            return result

        mock_db = AsyncMock()
        mock_db.execute = mock_execute

        with patch("app.modules.users.services.rbac_service._cache_get", return_value=None), \
             patch("app.modules.users.services.rbac_service._cache_set", return_value=None):
            perms = await get_user_effective_permissions(mock_db, user_id)

        assert perms == set()
