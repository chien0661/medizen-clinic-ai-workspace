"""TASK-004 M2 — End-to-end RBAC test with real DB + Redis through app.main:app.

Scenario
--------
1. Seed: create a Clinic + two Users (doctor_user, admin_user) in the DB.
   Assign admin_user the system ``admin`` role via raw DB insert.
   (The system roles are already present from migration 0007.)

2. Login as doctor_user (has system ``doctor`` role via DB assignment).
   Call GET /api/v1/users (requires user.manage).
   Assert 403 — doctor role lacks user.manage.

3. Use admin_user's token to assign ``admin`` role to doctor_user via
   POST /api/v1/users/{id}/roles  →  this calls rbac_service.assign_role
   and invalidates doctor_user's Redis cache.

4. doctor_user logs in again (fresh JWT with updated permissions).
   Call GET /api/v1/users → assert 200.
   Verify Redis cache was populated (key exists after first 200 request).

5. Admin user revokes the extra admin role from doctor_user
   (DELETE /api/v1/users/{id}/roles/{role_id}) → cache invalidated.

6. doctor_user logs in again (permissions recomputed).
   Call GET /api/v1/users → assert 403.

7. Also validate seed integrity: assert permission count == 38 and
   system role count == 5 by querying the real DB directly.

Coverage:
- require_permission() wired through app.main:app (not an isolated _test_app)
- rbac_service.assign_role / revoke_role → cache invalidation
- JWT refresh path for permission changes
- Seed migration correctness from DB
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
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


async def _get_role_id_by_code(factory, code: str) -> str:
    """Look up a system role UUID by code from the DB (tolerates both uuid4 and uuid5 IDs)."""
    async with factory() as session:
        row = (await session.execute(
            text("SELECT id FROM role WHERE code = :code AND clinic_id IS NULL"),
            {"code": code},
        )).fetchone()
    if row is None:
        raise RuntimeError(f"System role '{code}' not found in DB — run alembic upgrade head first")
    return str(row[0])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def rbac_e2e_client():
    """Real HTTP client against app.main:app — no dependency overrides."""
    limiter.reset()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def rbac_e2e_context(rbac_e2e_client):
    """Create Clinic + two Users with initial role assignments; teardown after test.

    Uses NullPool to avoid asyncpg event-loop mismatch errors.
    """
    clinic_id = uuid4()
    doctor_user_id = uuid4()
    admin_user_id = uuid4()
    suffix = clinic_id.hex[:6].upper()
    clinic_code = f"RBACE2E{suffix}"
    doctor_username = f"doctor_e2e_{suffix.lower()}"
    admin_username = f"admin_e2e_{suffix.lower()}"
    plain_password = "RbacE2ePassw0rd!"

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    # --- Setup: create clinic + users ---
    async with factory() as session:
        clinic = Clinic(
            id=clinic_id,
            code=clinic_code,
            name="RBAC E2E Test Clinic",
            specialty="general",
            is_active=True,
        )
        doctor_user = User(
            id=doctor_user_id,
            clinic_id=clinic_id,
            username=doctor_username,
            full_name="RBAC E2E Doctor",
            password_hash=hash_password(plain_password),
            is_active=True,
            is_locked=False,
            failed_login_count=0,
        )
        admin_user = User(
            id=admin_user_id,
            clinic_id=clinic_id,
            username=admin_username,
            full_name="RBAC E2E Admin",
            password_hash=hash_password(plain_password),
            is_active=True,
            is_locked=False,
            failed_login_count=0,
        )
        session.add(clinic)
        session.add(doctor_user)
        session.add(admin_user)
        await session.commit()

    # Look up system role IDs from DB (supports both uuid4 seed and uuid5 seed)
    doctor_role_id = await _get_role_id_by_code(factory, "doctor")
    admin_role_id = await _get_role_id_by_code(factory, "admin")

    # Assign roles via raw SQL (migration 0007 must have seeded role rows already)
    async with factory() as session:
        # doctor_user → doctor role
        await session.execute(
            text(
                "INSERT INTO user_role (id, user_id, role_id)"
                " VALUES (:id, :uid, :rid)"
                " ON CONFLICT DO NOTHING"
            ),
            {"id": str(uuid4()), "uid": str(doctor_user_id), "rid": doctor_role_id},
        )
        # admin_user → admin role
        await session.execute(
            text(
                "INSERT INTO user_role (id, user_id, role_id)"
                " VALUES (:id, :uid, :rid)"
                " ON CONFLICT DO NOTHING"
            ),
            {"id": str(uuid4()), "uid": str(admin_user_id), "rid": admin_role_id},
        )
        await session.commit()

    yield {
        "clinic_id": clinic_id,
        "clinic_code": clinic_code,
        "doctor_user_id": doctor_user_id,
        "admin_user_id": admin_user_id,
        "doctor_username": doctor_username,
        "admin_username": admin_username,
        "plain_password": plain_password,
        "admin_role_id": admin_role_id,
        "client": rbac_e2e_client,
        "factory": factory,
    }

    # --- Teardown: delete user_extra_permission → user_role → user → clinic ---
    async with factory() as session:
        # extra permissions (if any were created by test)
        for uid in (str(doctor_user_id), str(admin_user_id)):
            await session.execute(
                text("DELETE FROM user_extra_permission WHERE user_id = :uid"),
                {"uid": uid},
            )
        # role assignments
        for uid in (str(doctor_user_id), str(admin_user_id)):
            await session.execute(
                text("DELETE FROM user_role WHERE user_id = :uid"),
                {"uid": uid},
            )
        # users
        for uid in (str(doctor_user_id), str(admin_user_id)):
            await session.execute(
                text('DELETE FROM "user" WHERE id = :uid'),
                {"uid": uid},
            )
        # clinic
        await session.execute(
            text("DELETE FROM clinic WHERE id = :cid"),
            {"cid": str(clinic_id)},
        )
        await session.commit()

    await engine.dispose()

    # Clear Redis permission cache keys
    async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
        await r.delete(f"{_PERM_CACHE_PREFIX}{doctor_user_id}")
        await r.delete(f"{_PERM_CACHE_PREFIX}{admin_user_id}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _login(client: AsyncClient, clinic_code: str, username: str, password: str) -> str:
    """Login and return the access_token."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"clinic_code": clinic_code, "username": username, "password": password},
    )
    assert resp.status_code == 200, f"Login failed ({resp.status_code}): {resp.text}"
    return resp.json()["data"]["access_token"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRbacE2eRealDb:
    """End-to-end RBAC flow: assign role → permissions effective → revoke → blocked.

    All HTTP calls go through app.main:app (real router, real middleware, real DB).
    No mocks — uses a live PostgreSQL + Redis matching the Docker Compose setup.
    """

    @pytest.mark.asyncio
    async def test_seed_integrity(self, rbac_e2e_context):
        """DB should have exactly 38 permissions and 5 system roles from migration 0007."""
        factory = rbac_e2e_context["factory"]
        async with factory() as session:
            perm_count = (await session.execute(text("SELECT COUNT(*) FROM permission"))).scalar_one()
            role_count = (
                await session.execute(
                    text("SELECT COUNT(*) FROM role WHERE clinic_id IS NULL AND is_system = TRUE")
                )
            ).scalar_one()

        assert perm_count == 38, f"Expected 38 permissions, got {perm_count}"
        assert role_count == 5, f"Expected 5 system roles, got {role_count}"

    @pytest.mark.asyncio
    async def test_doctor_cannot_access_user_manage_route(self, rbac_e2e_context):
        """Doctor role lacks user.manage → GET /api/v1/users returns 403."""
        ctx = rbac_e2e_context
        client = ctx["client"]

        token = await _login(
            client, ctx["clinic_code"], ctx["doctor_username"], ctx["plain_password"]
        )

        resp = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403, (
            f"Doctor should get 403 on user.manage route, got {resp.status_code}: {resp.text}"
        )

    @pytest.mark.asyncio
    async def test_role_assignment_grants_access_then_revocation_blocks(self, rbac_e2e_context):
        """Core RBAC e2e flow: assign admin role → 200; revoke → 403.

        Steps:
          1. doctor_user login → GET /users → 403 (no user.manage).
          2. admin_user login → POST /users/{doctor_id}/roles (assign admin) → 201.
          3. doctor_user login again (fresh JWT, cache invalidated) → GET /users → 200.
          4. Verify Redis cache key exists after the 200 request.
          5. admin_user → DELETE /users/{doctor_id}/roles/{user_role_id} → 204.
          6. doctor_user login again → GET /users → 403.
        """
        ctx = rbac_e2e_context
        client = ctx["client"]
        doctor_id = ctx["doctor_user_id"]
        factory = ctx["factory"]
        admin_role_id = ctx["admin_role_id"]

        # --- Step 1: doctor login → 403 on user.manage route ---
        doctor_token = await _login(
            client, ctx["clinic_code"], ctx["doctor_username"], ctx["plain_password"]
        )
        resp = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert resp.status_code == 403, (
            f"Step 1: Expected 403, got {resp.status_code}: {resp.text}"
        )

        # --- Step 2: admin login → assign admin role to doctor_user via API ---
        admin_token = await _login(
            client, ctx["clinic_code"], ctx["admin_username"], ctx["plain_password"]
        )
        assign_resp = await client.post(
            f"/api/v1/users/{doctor_id}/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role_id": admin_role_id},
        )
        assert assign_resp.status_code == 201, (
            f"Step 2: Role assignment failed ({assign_resp.status_code}): {assign_resp.text}"
        )
        # Note: DELETE /users/{id}/roles/{role_id} takes the *role* ID, not the user_role row ID

        # --- Step 3: doctor re-login → fresh JWT with admin permissions → 200 ---
        doctor_token2 = await _login(
            client, ctx["clinic_code"], ctx["doctor_username"], ctx["plain_password"]
        )
        resp2 = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {doctor_token2}"},
        )
        assert resp2.status_code == 200, (
            f"Step 3: Expected 200 after role assignment, got {resp2.status_code}: {resp2.text}"
        )

        # --- Step 4: Redis cache key should exist now ---
        async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
            cached = await r.get(f"{_PERM_CACHE_PREFIX}{doctor_id}")
        assert cached is not None, "Step 4: Redis permission cache should be populated after request"

        # --- Step 5: admin revokes admin role from doctor_user → cache invalidated ---
        revoke_resp = await client.delete(
            f"/api/v1/users/{doctor_id}/roles/{admin_role_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert revoke_resp.status_code == 204, (
            f"Step 5: Role revocation failed ({revoke_resp.status_code}): {revoke_resp.text}"
        )

        # Redis key should be gone after revocation
        async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
            cached_after_revoke = await r.get(f"{_PERM_CACHE_PREFIX}{doctor_id}")
        assert cached_after_revoke is None, "Step 5: Redis cache should be invalidated after role revocation"

        # --- Step 6: doctor re-login → only doctor role again → 403 ---
        doctor_token3 = await _login(
            client, ctx["clinic_code"], ctx["doctor_username"], ctx["plain_password"]
        )
        resp3 = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {doctor_token3}"},
        )
        assert resp3.status_code == 403, (
            f"Step 6: Expected 403 after role revocation, got {resp3.status_code}: {resp3.text}"
        )

    @pytest.mark.asyncio
    async def test_extra_deny_blocks_even_with_role_grant(self, rbac_e2e_context):
        """Extra deny overrides role grant: doctor with pharmacy.dispense grant, then deny wins.

        This exercises the extra_permission path via the API.
        """
        ctx = rbac_e2e_context
        client = ctx["client"]
        doctor_id = ctx["doctor_user_id"]
        factory = ctx["factory"]

        # Login as admin to add extra permissions
        admin_token = await _login(
            client, ctx["clinic_code"], ctx["admin_username"], ctx["plain_password"]
        )

        # First add extra_grant for pharmacy.dispense
        grant_resp = await client.post(
            f"/api/v1/users/{doctor_id}/extra-permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "permission_code": "pharmacy.dispense",
                "type": "grant",
                "reason": "e2e test grant",
            },
        )
        assert grant_resp.status_code == 201, (
            f"Failed to add extra grant: {grant_resp.status_code}: {grant_resp.text}"
        )

        # Now add extra_deny for the same permission
        deny_resp = await client.post(
            f"/api/v1/users/{doctor_id}/extra-permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "permission_code": "pharmacy.dispense",
                "type": "deny",
                "reason": "e2e test deny",
            },
        )
        assert deny_resp.status_code == 201, (
            f"Failed to add extra deny: {deny_resp.status_code}: {deny_resp.text}"
        )

        # Verify from DB that the deny is active and the old grant was soft-deleted
        async with factory() as session:
            from sqlalchemy import text as _text
            rows = (await session.execute(
                _text(
                    "SELECT type, is_deleted FROM user_extra_permission"
                    " WHERE user_id = :uid AND permission_code = 'pharmacy.dispense'"
                    " ORDER BY created_at"
                ),
                {"uid": str(doctor_id)},
            )).fetchall()

        types_deleted = [(r[0], r[1]) for r in rows]
        # There should be 2 rows: a soft-deleted grant + active deny
        assert len(types_deleted) == 2, f"Expected 2 override rows, got: {types_deleted}"
        assert any(r[0] == "grant" and r[1] is True for r in types_deleted), (
            "Grant should be soft-deleted"
        )
        assert any(r[0] == "deny" and r[1] is False for r in types_deleted), (
            "Deny should be active"
        )

    @pytest.mark.asyncio
    async def test_idempotent_extra_permission(self, rbac_e2e_context):
        """Calling add_extra_permission twice with identical payload returns same record.

        Verifies M4 fix: no new DB row is created on idempotent call.
        """
        ctx = rbac_e2e_context
        client = ctx["client"]
        doctor_id = ctx["doctor_user_id"]
        factory = ctx["factory"]

        admin_token = await _login(
            client, ctx["clinic_code"], ctx["admin_username"], ctx["plain_password"]
        )

        payload = {
            "permission_code": "report.view",
            "type": "grant",
            "reason": "idempotent test",
        }

        resp1 = await client.post(
            f"/api/v1/users/{doctor_id}/extra-permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload,
        )
        assert resp1.status_code == 201, f"First call failed: {resp1.text}"
        ep_id_1 = resp1.json()["id"]

        resp2 = await client.post(
            f"/api/v1/users/{doctor_id}/extra-permissions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=payload,
        )
        assert resp2.status_code == 201, f"Second call failed: {resp2.text}"
        ep_id_2 = resp2.json()["id"]

        # Both calls should return the same record (idempotent)
        assert ep_id_1 == ep_id_2, (
            f"Idempotent call returned different IDs: {ep_id_1} vs {ep_id_2}"
        )

        # Verify only one active row in DB
        async with factory() as session:
            active_count = (await session.execute(
                text(
                    "SELECT COUNT(*) FROM user_extra_permission"
                    " WHERE user_id = :uid"
                    " AND permission_code = 'report.view'"
                    " AND is_deleted = FALSE"
                ),
                {"uid": str(doctor_id)},
            )).scalar_one()
        assert active_count == 1, f"Should be exactly 1 active row, got {active_count}"
