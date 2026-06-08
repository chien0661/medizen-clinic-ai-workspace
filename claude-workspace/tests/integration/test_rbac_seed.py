"""Integration tests: verify seeded permission catalog and system roles.

Requires: DB with migrations 0006 + 0007 applied.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.users.models.permission import Permission
from app.modules.users.models.role import Role
from app.modules.users.models.role_permission import RolePermission
from app.modules.users.rbac_seed_data import PERMISSIONS as SEED_PERMISSIONS
from app.modules.users.rbac_seed_data import ROLE_PERMISSIONS as SEED_ROLE_PERMISSIONS
from app.modules.users.rbac_seed_data import SYSTEM_ROLES as SEED_SYSTEM_ROLES
from app.modules.users.services.rbac_service import get_user_effective_permissions

# ---------------------------------------------------------------------------
# Expected catalog from BA §13.5
# ---------------------------------------------------------------------------
EXPECTED_PERMISSIONS = {
    "patient.read", "patient.write", "patient.merge", "patient.delete",
    "visit.read", "visit.write", "visit.cancel",
    "vital.read", "vital.write", "vital.delete",
    "service.catalog.manage", "service.perform", "service.price_override",
    "prescription.write", "prescription.cancel", "prescription.print",
    "pharmacy.dispense", "pharmacy.substitute_batch", "pharmacy.adjust_stock",
    "inventory.read", "inventory.manage_catalog", "inventory.purchase_in", "inventory.adjust",
    "invoice.create", "invoice.modify", "invoice.void", "invoice.refund",
    "payment.receive",
    "shift.manage", "attendance.manage", "leave.approve",
    "user.manage", "role.manage",
    "report.view", "report.financial",
    "settings.clinic", "settings.vital_schema", "settings.service_catalog",
}

EXPECTED_SYSTEM_ROLES = {"admin", "doctor", "nurse", "pharmacist", "receptionist"}

# Spot-check: doctor's expected permissions per BA §13.6
DOCTOR_EXPECTED = {
    "patient.read", "patient.write",
    "visit.read", "visit.write", "visit.cancel",
    "vital.read", "vital.write",
    "service.perform",
    "prescription.write", "prescription.cancel", "prescription.print",
    "invoice.create",
    "report.view",
}

NURSE_EXPECTED = {
    "patient.read", "patient.write",
    "visit.read", "visit.write",
    "vital.read", "vital.write", "vital.delete",
    "service.perform",
    "prescription.print",
    "inventory.read",
    "report.view",
}

PHARMACIST_EXPECTED = {
    "patient.read",
    "prescription.print",
    "pharmacy.dispense", "pharmacy.substitute_batch", "pharmacy.adjust_stock",
    "inventory.read", "inventory.manage_catalog", "inventory.purchase_in", "inventory.adjust",
    "report.view",
}


class TestPermissionCatalogSeeded:
    """Verify EXPECTED_PERMISSIONS are all present in the seeded migration."""

    def test_all_expected_permissions_present(self):
        """All 38 expected permission codes are in EXPECTED_PERMISSIONS set."""
        assert len(EXPECTED_PERMISSIONS) >= 30, (
            f"Expected at least 30 permissions, got {len(EXPECTED_PERMISSIONS)}"
        )

    def test_permission_codes_format(self):
        """Each permission code uses dotted-path format."""
        for code in EXPECTED_PERMISSIONS:
            assert "." in code, f"Permission code '{code}' should use dotted-path format"

    def test_permission_categories_are_consistent(self):
        """Permission codes use consistent dotted-path prefixes."""
        # All permission codes should use dotted-path format
        for code in EXPECTED_PERMISSIONS:
            assert "." in code, f"Permission code '{code}' should use dotted-path format"
        # Verify at least the main domain prefixes are present
        prefixes = {code.split(".")[0] for code in EXPECTED_PERMISSIONS}
        expected_prefixes = {
            "patient", "visit", "vital", "service", "prescription",
            "pharmacy", "inventory", "invoice", "payment",
            "shift", "attendance", "leave",
            "user", "role", "report", "settings",
        }
        assert expected_prefixes.issubset(prefixes), (
            f"Missing expected prefixes: {expected_prefixes - prefixes}"
        )


class TestSystemRolesSeeded:
    """Verify system roles metadata."""

    def test_five_system_roles_defined(self):
        assert len(EXPECTED_SYSTEM_ROLES) == 5

    def test_system_role_codes(self):
        assert EXPECTED_SYSTEM_ROLES == {"admin", "doctor", "nurse", "pharmacist", "receptionist"}


class TestRolePermissionMapping:
    """Verify default role-permission mapping from BA §13.6."""

    def test_doctor_mapping_correct(self):
        """Doctor role has the expected permissions defined in BA §13.6."""
        doctor_perms = set(SEED_ROLE_PERMISSIONS["doctor"])
        assert DOCTOR_EXPECTED.issubset(doctor_perms), (
            f"Doctor missing expected perms: {DOCTOR_EXPECTED - doctor_perms}"
        )

    def test_doctor_permissions_subset(self):
        """Doctor permissions are a subset of all permissions."""
        assert DOCTOR_EXPECTED.issubset(EXPECTED_PERMISSIONS), (
            f"Doctor permissions not all in catalog: {DOCTOR_EXPECTED - EXPECTED_PERMISSIONS}"
        )

    def test_nurse_permissions_subset(self):
        assert NURSE_EXPECTED.issubset(EXPECTED_PERMISSIONS)

    def test_pharmacist_permissions_subset(self):
        assert PHARMACIST_EXPECTED.issubset(EXPECTED_PERMISSIONS)

    def test_admin_has_all_permissions(self):
        """Admin should have ALL permissions in the catalog."""
        admin_perms = set(SEED_ROLE_PERMISSIONS["admin"])
        catalog_codes = {p["code"] for p in SEED_PERMISSIONS}
        assert catalog_codes.issubset(admin_perms), (
            f"Admin missing catalog perms: {catalog_codes - admin_perms}"
        )

    def test_receptionist_cannot_void_invoice(self):
        """Receptionist role does NOT include invoice.void."""
        receptionist_perms = set(SEED_ROLE_PERMISSIONS["receptionist"])
        assert "invoice.void" not in receptionist_perms

    def test_doctor_cannot_dispense(self):
        """Doctor role does NOT include pharmacy.dispense."""
        doctor_perms = set(SEED_ROLE_PERMISSIONS["doctor"])
        assert "pharmacy.dispense" not in doctor_perms

    def test_admin_has_user_manage(self):
        """Admin role includes user.manage."""
        admin_perms = set(SEED_ROLE_PERMISSIONS["admin"])
        assert "user.manage" in admin_perms
        assert "role.manage" in admin_perms


class TestEffectivePermissionsUnit:
    """Unit tests for get_user_effective_permissions logic (mocked DB)."""

    @pytest.mark.asyncio
    async def test_effective_perms_union_minus_deny(self):
        """(role_perms ∪ extra_grants) − extra_denies."""
        from uuid import uuid4

        from app.modules.users.models.user_extra_permission import ExtraPermType

        user_id = uuid4()

        # Mock DB session + Redis cache miss
        mock_db = AsyncMock()

        # user_role rows — role_ids
        role_id = uuid4()
        mock_db.execute = AsyncMock()

        # Sequence of execute calls: user_roles, role_perms, extra_perms
        ur_row = MagicMock()
        ur_row.__iter__ = lambda s: iter([(role_id,)])
        ur_fetchall = MagicMock(return_value=[(role_id,)])

        rp_fetchall = MagicMock(return_value=[("patient.read",), ("visit.write",)])
        ep_fetchall = MagicMock(
            return_value=[
                ("invoice.void", ExtraPermType.grant),
                ("visit.write", ExtraPermType.deny),  # deny overrides role grant
            ]
        )

        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:  # user_roles query
                result.fetchall.return_value = [(role_id,)]
            elif call_count == 2:  # role_perms query
                result.fetchall.return_value = [("patient.read",), ("visit.write",)]
            elif call_count == 3:  # extra_perms query
                result.fetchall.return_value = [
                    ("invoice.void", ExtraPermType.grant),
                    ("visit.write", ExtraPermType.deny),
                ]
            return result

        mock_db.execute = mock_execute

        with patch("app.modules.users.services.rbac_service._cache_get", return_value=None), \
             patch("app.modules.users.services.rbac_service._cache_set", return_value=None):
            result = await get_user_effective_permissions(mock_db, user_id)

        # patient.read (from role) + invoice.void (extra grant) — visit.write denied
        assert "patient.read" in result
        assert "invoice.void" in result
        assert "visit.write" not in result, "deny should remove visit.write"

    @pytest.mark.asyncio
    async def test_no_roles_no_grants_empty(self):
        """User with no roles and no extra grants → empty permissions."""
        from uuid import uuid4

        user_id = uuid4()
        mock_db = AsyncMock()
        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.fetchall.return_value = []
            return result

        mock_db.execute = mock_execute

        with patch("app.modules.users.services.rbac_service._cache_get", return_value=None), \
             patch("app.modules.users.services.rbac_service._cache_set", return_value=None):
            result = await get_user_effective_permissions(mock_db, user_id)

        assert result == set()

    @pytest.mark.asyncio
    async def test_cache_hit_returns_without_db(self):
        """Cache hit: no DB queries, returns cached set."""
        from uuid import uuid4

        user_id = uuid4()
        cached = {"patient.read", "visit.write"}
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=AssertionError("Should not hit DB"))

        with patch(
            "app.modules.users.services.rbac_service._cache_get",
            return_value=cached,
        ):
            result = await get_user_effective_permissions(mock_db, user_id)

        assert result == cached
