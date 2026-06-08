"""TASK-004 — Extended RBAC e2e tests with real DB + Redis.

Covers gaps identified by Test Agent that are not exercised by the existing
test_rbac_e2e_real_db.py file:

AC2 — Role-permission mapping spot-check against real DB:
  - Doctor has vital.write in DB
  - Admin has ALL 38 permissions in DB
  - Nurse does NOT have prescription.write in DB
  - Pharmacist has pharmacy.dispense in DB

AC4 (end-to-end HTTP assertion) — extra_deny blocks the API call:
  - User with role that grants X, plus extra_deny X → actual HTTP 403

Negative paths (real router, real auth middleware):
  - Anonymous calls → 401
  - PATCH /roles/{system_role_id} → 403
  - POST /roles/{system_role_id}/permissions → 403
  - DELETE /roles/{system_role_id}/permissions/{code} → 403
  - GET /roles without role.manage → 403

Business-rule edge cases (real DB):
  - Multi-role union: doctor + pharmacist → union of both permission sets
  - extra_perm survives role revocation (independent of role membership)
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.main import app
from app.modules.users.models.clinic import Clinic
from app.modules.users.models.user import User
from tests.conftest import TEST_DATABASE_URL

_PERM_CACHE_PREFIX = "user:perms:"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_role_id_by_code(factory, code: str) -> str:
    async with factory() as session:
        row = (
            await session.execute(
                text("SELECT id FROM role WHERE code = :code AND clinic_id IS NULL"),
                {"code": code},
            )
        ).fetchone()
    if row is None:
        raise RuntimeError(f"System role '{code}' not found — run alembic upgrade head first")
    return str(row[0])


async def _login(client: AsyncClient, clinic_code: str, username: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"clinic_code": clinic_code, "username": username, "password": password},
    )
    assert resp.status_code == 200, f"Login failed ({resp.status_code}): {resp.text}"
    return resp.json()["data"]["access_token"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def ext_e2e_client():
    """Real HTTP client against app.main:app."""
    limiter.reset()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def ext_e2e_context(ext_e2e_client):
    """Create Clinic + three Users (admin, doctor, pharmacist) with initial roles.

    Yields a dict with all IDs and credentials.  Teardown cleans all created rows.
    """
    clinic_id = uuid4()
    admin_user_id = uuid4()
    doctor_user_id = uuid4()
    pharmacist_user_id = uuid4()
    suffix = clinic_id.hex[:6].upper()
    clinic_code = f"EXTRBAC{suffix}"
    admin_username = f"ext_admin_{suffix.lower()}"
    doctor_username = f"ext_doctor_{suffix.lower()}"
    pharmacist_username = f"ext_pharmacist_{suffix.lower()}"
    plain_password = "ExtRbacP@ss1!"

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    # Create clinic + users
    async with factory() as session:
        session.add(
            Clinic(
                id=clinic_id,
                code=clinic_code,
                name="Extended RBAC Test Clinic",
                specialty="general",
                is_active=True,
            )
        )
        session.add(
            User(
                id=admin_user_id,
                clinic_id=clinic_id,
                username=admin_username,
                full_name="Ext Admin",
                password_hash=hash_password(plain_password),
                is_active=True,
                is_locked=False,
                failed_login_count=0,
            )
        )
        session.add(
            User(
                id=doctor_user_id,
                clinic_id=clinic_id,
                username=doctor_username,
                full_name="Ext Doctor",
                password_hash=hash_password(plain_password),
                is_active=True,
                is_locked=False,
                failed_login_count=0,
            )
        )
        session.add(
            User(
                id=pharmacist_user_id,
                clinic_id=clinic_id,
                username=pharmacist_username,
                full_name="Ext Pharmacist",
                password_hash=hash_password(plain_password),
                is_active=True,
                is_locked=False,
                failed_login_count=0,
            )
        )
        await session.commit()

    # Resolve role IDs from DB
    admin_role_id = await _get_role_id_by_code(factory, "admin")
    doctor_role_id = await _get_role_id_by_code(factory, "doctor")
    pharmacist_role_id = await _get_role_id_by_code(factory, "pharmacist")

    # Assign initial roles
    async with factory() as session:
        for uid, rid in [
            (str(admin_user_id), admin_role_id),
            (str(doctor_user_id), doctor_role_id),
            (str(pharmacist_user_id), pharmacist_role_id),
        ]:
            await session.execute(
                text(
                    "INSERT INTO user_role (id, user_id, role_id)"
                    " VALUES (:id, :uid, :rid)"
                    " ON CONFLICT DO NOTHING"
                ),
                {"id": str(uuid4()), "uid": uid, "rid": rid},
            )
        await session.commit()

    yield {
        "client": ext_e2e_client,
        "factory": factory,
        "clinic_id": clinic_id,
        "clinic_code": clinic_code,
        "plain_password": plain_password,
        "admin_user_id": admin_user_id,
        "admin_username": admin_username,
        "admin_role_id": admin_role_id,
        "doctor_user_id": doctor_user_id,
        "doctor_username": doctor_username,
        "doctor_role_id": doctor_role_id,
        "pharmacist_user_id": pharmacist_user_id,
        "pharmacist_username": pharmacist_username,
        "pharmacist_role_id": pharmacist_role_id,
    }

    # Teardown
    for uid in (str(admin_user_id), str(doctor_user_id), str(pharmacist_user_id)):
        async with factory() as session:
            await session.execute(
                text("DELETE FROM user_extra_permission WHERE user_id = :uid"), {"uid": uid}
            )
            await session.execute(
                text("DELETE FROM user_role WHERE user_id = :uid"), {"uid": uid}
            )
            await session.execute(
                text('DELETE FROM "user" WHERE id = :uid'), {"uid": uid}
            )
            await session.commit()

    async with factory() as session:
        await session.execute(
            text("DELETE FROM clinic WHERE id = :cid"), {"cid": str(clinic_id)}
        )
        await session.commit()

    await engine.dispose()

    # Clear Redis cache
    async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
        for uid in (admin_user_id, doctor_user_id, pharmacist_user_id):
            await r.delete(f"{_PERM_CACHE_PREFIX}{uid}")


# ---------------------------------------------------------------------------
# AC2 — Role-permission mapping in real DB (spot-checks per BA §13.6)
# ---------------------------------------------------------------------------


class TestAc2RolePermissionMappingRealDb:
    """AC2: Default mapping matches BA §13.6 — verified against live DB."""

    @pytest.mark.asyncio
    async def test_admin_has_all_38_permissions(self, ext_e2e_context):
        """Admin role in DB must have all 38 permissions."""
        factory = ext_e2e_context["factory"]
        admin_role_id = ext_e2e_context["admin_role_id"]

        async with factory() as session:
            perm_count = (
                await session.execute(
                    text(
                        "SELECT COUNT(*) FROM role_permission WHERE role_id = :rid"
                    ),
                    {"rid": admin_role_id},
                )
            ).scalar_one()

        assert perm_count == 38, (
            f"Admin role should have 38 permissions in DB, got {perm_count}"
        )

    @pytest.mark.asyncio
    async def test_doctor_has_vital_write(self, ext_e2e_context):
        """Doctor role in DB must include vital.write (BA §13.6)."""
        factory = ext_e2e_context["factory"]
        doctor_role_id = ext_e2e_context["doctor_role_id"]

        async with factory() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT 1 FROM role_permission"
                        " WHERE role_id = :rid AND permission_code = 'vital.write'"
                    ),
                    {"rid": doctor_role_id},
                )
            ).fetchone()

        assert row is not None, "Doctor role must have vital.write per BA §13.6"

    @pytest.mark.asyncio
    async def test_pharmacist_has_pharmacy_dispense(self, ext_e2e_context):
        """Pharmacist role in DB must include pharmacy.dispense (BA §13.6)."""
        factory = ext_e2e_context["factory"]
        pharmacist_role_id = ext_e2e_context["pharmacist_role_id"]

        async with factory() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT 1 FROM role_permission"
                        " WHERE role_id = :rid AND permission_code = 'pharmacy.dispense'"
                    ),
                    {"rid": pharmacist_role_id},
                )
            ).fetchone()

        assert row is not None, "Pharmacist role must have pharmacy.dispense per BA §13.6"

    @pytest.mark.asyncio
    async def test_nurse_does_not_have_prescription_write(self, ext_e2e_context):
        """Nurse role in DB must NOT have prescription.write (BA §13.6)."""
        factory = ext_e2e_context["factory"]
        nurse_role_id = await _get_role_id_by_code(factory, "nurse")

        async with factory() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT 1 FROM role_permission"
                        " WHERE role_id = :rid AND permission_code = 'prescription.write'"
                    ),
                    {"rid": nurse_role_id},
                )
            ).fetchone()

        assert row is None, "Nurse role must NOT have prescription.write per BA §13.6"

    @pytest.mark.asyncio
    async def test_doctor_does_not_have_pharmacy_dispense(self, ext_e2e_context):
        """Doctor role must NOT have pharmacy.dispense — AC3 spirit (real DB)."""
        factory = ext_e2e_context["factory"]
        doctor_role_id = ext_e2e_context["doctor_role_id"]

        async with factory() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT 1 FROM role_permission"
                        " WHERE role_id = :rid AND permission_code = 'pharmacy.dispense'"
                    ),
                    {"rid": doctor_role_id},
                )
            ).fetchone()

        assert row is None, "Doctor must NOT have pharmacy.dispense — AC3 spirit"


# ---------------------------------------------------------------------------
# AC4 — extra_deny blocks HTTP 403 (end-to-end API assertion)
# ---------------------------------------------------------------------------


class TestAc4ExtraDenyBlocksApiCall:
    """AC4: User with role grant + extra_deny for same permission gets HTTP 403."""

    @pytest.mark.asyncio
    async def test_extra_deny_blocks_api_call_end_to_end(self, ext_e2e_context):
        """Doctor gets extra_grant for user.manage, then extra_deny — API returns 403.

        This is the AC4 end-to-end HTTP assertion that the reviewer requested:
        the existing test_rbac_e2e_real_db.test_extra_deny_blocks_even_with_role_grant
        only checks DB state; this test also asserts the HTTP 403 on the actual route.
        """
        ctx = ext_e2e_context
        client = ctx["client"]
        doctor_id = ctx["doctor_user_id"]

        admin_token = await _login(
            client, ctx["clinic_code"], ctx["admin_username"], ctx["plain_password"]
        )

        # Step 1: Give doctor an extra_grant for user.manage
        grant_resp = await client.post(
            f"/api/v1/users/{doctor_id}/extra-permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "permission_code": "user.manage",
                "type": "grant",
                "reason": "AC4 test: temporary grant",
            },
        )
        assert grant_resp.status_code == 201, f"Extra grant failed: {grant_resp.text}"

        # Step 2: Confirm doctor can now access user.manage route (fresh login)
        doctor_token_with_grant = await _login(
            client, ctx["clinic_code"], ctx["doctor_username"], ctx["plain_password"]
        )
        resp_granted = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {doctor_token_with_grant}"},
        )
        assert resp_granted.status_code == 200, (
            f"Doctor with extra_grant should get 200, got {resp_granted.status_code}"
        )

        # Step 3: Add extra_deny for user.manage — overrides the grant
        deny_resp = await client.post(
            f"/api/v1/users/{doctor_id}/extra-permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "permission_code": "user.manage",
                "type": "deny",
                "reason": "AC4 test: deny overrides grant",
            },
        )
        assert deny_resp.status_code == 201, f"Extra deny failed: {deny_resp.text}"

        # Step 4: Doctor re-login → deny wins → 403
        doctor_token_with_deny = await _login(
            client, ctx["clinic_code"], ctx["doctor_username"], ctx["plain_password"]
        )
        resp_denied = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {doctor_token_with_deny}"},
        )
        assert resp_denied.status_code == 403, (
            f"AC4: Doctor with extra_deny should get 403, got {resp_denied.status_code}: "
            f"{resp_denied.text}"
        )


# ---------------------------------------------------------------------------
# Negative paths — Anonymous + system-role immutability on real routes
# ---------------------------------------------------------------------------


class TestNegativePaths:
    """Negative path tests through the real router + real DB."""

    @pytest.mark.asyncio
    async def test_anonymous_list_users_returns_401(self, ext_e2e_context):
        """GET /users without any auth token → 401."""
        client = ext_e2e_context["client"]
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 401, f"Expected 401 for anonymous, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_anonymous_list_roles_returns_401(self, ext_e2e_context):
        """GET /roles without auth → 401."""
        client = ext_e2e_context["client"]
        resp = await client.get("/api/v1/roles")
        assert resp.status_code == 401, f"Expected 401 for anonymous, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_anonymous_assign_role_returns_401(self, ext_e2e_context):
        """POST /users/{id}/roles without auth → 401."""
        client = ext_e2e_context["client"]
        doctor_id = ext_e2e_context["doctor_user_id"]
        resp = await client.post(
            f"/api/v1/users/{doctor_id}/roles",
            json={"role_id": str(uuid4())},
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_doctor_cannot_list_roles(self, ext_e2e_context):
        """Doctor (no role.manage) → GET /roles returns 403."""
        ctx = ext_e2e_context
        client = ctx["client"]
        doctor_token = await _login(
            client, ctx["clinic_code"], ctx["doctor_username"], ctx["plain_password"]
        )
        resp = await client.get(
            "/api/v1/roles",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert resp.status_code == 403, (
            f"Doctor without role.manage should get 403 on GET /roles, got {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_patch_system_role_returns_403(self, ext_e2e_context):
        """PATCH /roles/{system_role_id} → 403 (system role is immutable)."""
        ctx = ext_e2e_context
        client = ctx["client"]
        admin_token = await _login(
            client, ctx["clinic_code"], ctx["admin_username"], ctx["plain_password"]
        )
        doctor_role_id = ctx["doctor_role_id"]

        resp = await client.patch(
            f"/api/v1/roles/{doctor_role_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Hacked Doctor Name"},
        )
        assert resp.status_code == 403, (
            f"PATCH on system role should return 403, got {resp.status_code}: {resp.text}"
        )

    @pytest.mark.asyncio
    async def test_post_system_role_permissions_returns_403(self, ext_e2e_context):
        """POST /roles/{system_role_id}/permissions → 403."""
        ctx = ext_e2e_context
        client = ctx["client"]
        admin_token = await _login(
            client, ctx["clinic_code"], ctx["admin_username"], ctx["plain_password"]
        )
        doctor_role_id = ctx["doctor_role_id"]

        resp = await client.post(
            f"/api/v1/roles/{doctor_role_id}/permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"permission_code": "invoice.void"},
        )
        assert resp.status_code == 403, (
            f"POST permission on system role should return 403, got {resp.status_code}: {resp.text}"
        )

    @pytest.mark.asyncio
    async def test_delete_system_role_permission_returns_403(self, ext_e2e_context):
        """DELETE /roles/{system_role_id}/permissions/{code} → 403."""
        ctx = ext_e2e_context
        client = ctx["client"]
        admin_token = await _login(
            client, ctx["clinic_code"], ctx["admin_username"], ctx["plain_password"]
        )
        doctor_role_id = ctx["doctor_role_id"]

        resp = await client.delete(
            f"/api/v1/roles/{doctor_role_id}/permissions/vital.write",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 403, (
            f"DELETE permission on system role should return 403, got {resp.status_code}: {resp.text}"
        )

    @pytest.mark.asyncio
    async def test_delete_system_role_returns_403(self, ext_e2e_context):
        """DELETE /roles/{system_role_id} → 403 (system role cannot be deleted)."""
        ctx = ext_e2e_context
        client = ctx["client"]
        admin_token = await _login(
            client, ctx["clinic_code"], ctx["admin_username"], ctx["plain_password"]
        )
        doctor_role_id = ctx["doctor_role_id"]

        resp = await client.delete(
            f"/api/v1/roles/{doctor_role_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 403, (
            f"DELETE on system role should return 403, got {resp.status_code}: {resp.text}"
        )


# ---------------------------------------------------------------------------
# Business-rule edge cases
# ---------------------------------------------------------------------------


class TestBusinessRuleEdgeCases:
    """Multi-role union, extra_perm survival, and other edge cases."""

    @pytest.mark.asyncio
    async def test_multi_role_union_grants_combined_permissions(self, ext_e2e_context):
        """Doctor + pharmacist roles → user.manage still denied, both sets unioned.

        Assigns pharmacist role to doctor_user; verifies that the doctor's
        effective permissions now include pharmacy.dispense (from pharmacist role)
        but still lacks user.manage (neither doctor nor pharmacist has it).
        """
        ctx = ext_e2e_context
        client = ctx["client"]
        doctor_id = ctx["doctor_user_id"]

        admin_token = await _login(
            client, ctx["clinic_code"], ctx["admin_username"], ctx["plain_password"]
        )

        # Assign pharmacist role to doctor_user (in addition to doctor role)
        assign_resp = await client.post(
            f"/api/v1/users/{doctor_id}/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role_id": ctx["pharmacist_role_id"]},
        )
        assert assign_resp.status_code == 201, (
            f"Failed to assign pharmacist role to doctor: {assign_resp.text}"
        )

        try:
            # doctor_user re-logins → gets union of doctor+pharmacist permissions
            doctor_token = await _login(
                client, ctx["clinic_code"], ctx["doctor_username"], ctx["plain_password"]
            )

            # Verify: still no user.manage (neither doctor nor pharmacist has it)
            resp_users = await client.get(
                "/api/v1/users",
                headers={"Authorization": f"Bearer {doctor_token}"},
            )
            assert resp_users.status_code == 403, (
                f"Multi-role user without user.manage should get 403, got {resp_users.status_code}"
            )

            # Verify: effective perms via DB include pharmacy.dispense (pharmacist role)
            factory = ctx["factory"]
            async with factory() as session:
                row = (
                    await session.execute(
                        text(
                            "SELECT COUNT(*) FROM user_role ur"
                            " JOIN role_permission rp ON rp.role_id = ur.role_id"
                            " WHERE ur.user_id = :uid AND rp.permission_code = 'pharmacy.dispense'"
                        ),
                        {"uid": str(doctor_id)},
                    )
                ).scalar_one()
            assert row >= 1, (
                "Multi-role user should have pharmacy.dispense via pharmacist role"
            )
        finally:
            # Cleanup: revoke pharmacist role from doctor_user
            await client.delete(
                f"/api/v1/users/{doctor_id}/roles/{ctx['pharmacist_role_id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

    @pytest.mark.asyncio
    async def test_extra_perm_survives_role_revocation(self, ext_e2e_context):
        """extra_grant survives role revocation — per-user overrides are independent.

        1. Give doctor an extra_grant for user.manage.
        2. Revoke doctor role from doctor_user.
        3. Verify the extra_permission row is still in DB (not deleted by role revocation).
        4. Re-assign doctor role (cleanup).
        """
        ctx = ext_e2e_context
        client = ctx["client"]
        doctor_id = ctx["doctor_user_id"]
        factory = ctx["factory"]

        admin_token = await _login(
            client, ctx["clinic_code"], ctx["admin_username"], ctx["plain_password"]
        )

        # Add extra_grant
        grant_resp = await client.post(
            f"/api/v1/users/{doctor_id}/extra-permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "permission_code": "report.financial",
                "type": "grant",
                "reason": "survival test",
            },
        )
        assert grant_resp.status_code == 201, f"Extra grant failed: {grant_resp.text}"

        # Revoke doctor role
        revoke_resp = await client.delete(
            f"/api/v1/users/{doctor_id}/roles/{ctx['doctor_role_id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert revoke_resp.status_code == 204, f"Role revocation failed: {revoke_resp.text}"

        try:
            # Verify extra_permission row still active in DB
            async with factory() as session:
                row = (
                    await session.execute(
                        text(
                            "SELECT COUNT(*) FROM user_extra_permission"
                            " WHERE user_id = :uid"
                            " AND permission_code = 'report.financial'"
                            " AND is_deleted = FALSE"
                        ),
                        {"uid": str(doctor_id)},
                    )
                ).scalar_one()
            assert row == 1, (
                f"Extra permission should survive role revocation, got {row} active rows"
            )
        finally:
            # Re-assign doctor role to restore fixture state
            await client.post(
                f"/api/v1/users/{doctor_id}/roles",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"role_id": ctx["doctor_role_id"]},
            )
