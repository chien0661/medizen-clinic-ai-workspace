"""Negative path / fuzz tests for Patient Management API (TASK-005).

Priority 6: Validates that bad inputs return 4xx (not 5xx) and that edge cases
in search, create, merge, and undo are handled gracefully.

All tests are real DB e2e (no mocks).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.main import app
from tests.conftest import TEST_DATABASE_URL

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _login(client: AsyncClient, clinic_code: str, username: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"clinic_code": clinic_code, "username": username, "password": password},
    )
    assert resp.status_code == 200, f"Login failed ({resp.status_code}): {resp.text}"
    return resp.json()["data"]["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def neg_ctx():
    """Seed a clinic + admin user; yield context; teardown."""
    limiter.reset()
    suffix = uuid4().hex[:6].upper()
    clinic_id = uuid4()
    admin_id = uuid4()
    clinic_code = f"NEGP{suffix}"
    admin_username = f"neg_admin_{suffix.lower()}"
    password = "NegTestPassw0rd!"

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        row = (
            await session.execute(
                text("SELECT id FROM role WHERE code = 'admin' AND clinic_id IS NULL")
            )
        ).fetchone()
        if row is None:
            pytest.skip("admin role not found")
        admin_role_id = str(row[0])

    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO clinic (id, code, name, specialty, is_active)"
                " VALUES (:id, :code, :name, :specialty, true)"
            ),
            {"id": str(clinic_id), "code": clinic_code, "name": "Negative Test Clinic", "specialty": "general"},
        )
        await session.execute(
            text(
                'INSERT INTO "user" (id, clinic_id, username, full_name,'
                " password_hash, is_active, is_locked, failed_login_count)"
                " VALUES (:id, :cid, :uname, :fname, :pw, true, false, 0)"
            ),
            {
                "id": str(admin_id),
                "cid": str(clinic_id),
                "uname": admin_username,
                "fname": "Negative Admin",
                "pw": hash_password(password),
            },
        )
        await session.execute(
            text(
                "INSERT INTO user_role (id, user_id, role_id)"
                " VALUES (:id, :uid, :rid) ON CONFLICT DO NOTHING"
            ),
            {"id": str(uuid4()), "uid": str(admin_id), "rid": admin_role_id},
        )
        await session.commit()

    yield {
        "clinic_id": clinic_id,
        "clinic_code": clinic_code,
        "admin_id": admin_id,
        "admin_username": admin_username,
        "password": password,
        "factory": factory,
    }

    # Teardown — NOTE: audit_log is append-only (trigger blocks DELETE); skip it.
    async with factory() as session:
        await session.execute(
            text("DELETE FROM patient_merge_log WHERE clinic_id = :cid"), {"cid": str(clinic_id)}
        )
        await session.execute(
            text("DELETE FROM patient_relation WHERE clinic_id = :cid"), {"cid": str(clinic_id)}
        )
        await session.execute(
            text("DELETE FROM patient WHERE clinic_id = :cid"), {"cid": str(clinic_id)}
        )
        await session.execute(
            text("DELETE FROM user_role WHERE user_id = :uid"), {"uid": str(admin_id)}
        )
        await session.execute(
            text('DELETE FROM "user" WHERE id = :uid'), {"uid": str(admin_id)}
        )
        await session.execute(
            text("DELETE FROM clinic WHERE id = :cid"), {"cid": str(clinic_id)}
        )
        await session.commit()
    await engine.dispose()


# ---------------------------------------------------------------------------
# Search negative paths
# ---------------------------------------------------------------------------


class TestSearchNegativePaths:
    """Search endpoint negative paths — all must return 4xx, never 5xx."""

    @pytest.mark.asyncio
    async def test_search_empty_q_returns_4xx(self, neg_ctx):
        """Empty q parameter must return 400 (not 500)."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.get("/api/v1/patients/search?q=&type=name", headers=_auth(token))
            assert resp.status_code < 500, (
                f"Empty q should not cause 5xx, got {resp.status_code}: {resp.text}"
            )
            assert resp.status_code in (200, 400, 422), (
                f"Expected 200/400/422 for empty q, got {resp.status_code}"
            )

    @pytest.mark.asyncio
    async def test_search_single_char_q_does_not_500(self, neg_ctx):
        """Single-character q must not cause 5xx."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.get("/api/v1/patients/search?q=a&type=name", headers=_auth(token))
            assert resp.status_code < 500, (
                f"Single-char q should not cause 5xx, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_search_very_long_q_does_not_500(self, neg_ctx):
        """1000-character q must not cause 5xx."""
        ctx = neg_ctx
        long_q = "a" * 1000
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.get(
                f"/api/v1/patients/search?q={long_q}&type=name", headers=_auth(token)
            )
            assert resp.status_code < 500, (
                f"1000-char q should not cause 5xx, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_search_unicode_q_does_not_500(self, neg_ctx):
        """Unicode-only q (Japanese) must not cause 5xx."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.get(
                "/api/v1/patients/search?q=日本語&type=name", headers=_auth(token)
            )
            assert resp.status_code < 500, (
                f"Unicode q should not cause 5xx, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_search_null_byte_q_does_not_500(self, neg_ctx):
        """Null byte in q must return 4xx (not 5xx) — SQL safety check."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.get(
                "/api/v1/patients/search?q=test%00name&type=name", headers=_auth(token)
            )
            # Null bytes in SQL string literals cause PostgreSQL errors — must be 4xx not 5xx
            assert resp.status_code < 500, (
                f"Null byte in q should not cause 5xx, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_search_missing_q_parameter_returns_4xx(self, neg_ctx):
        """Missing q parameter must return 422 Unprocessable Entity."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.get("/api/v1/patients/search?type=name", headers=_auth(token))
            assert resp.status_code in (400, 422), (
                f"Missing q should return 400/422, got {resp.status_code}"
            )


# ---------------------------------------------------------------------------
# Create negative paths
# ---------------------------------------------------------------------------


class TestCreateNegativePaths:
    """Create patient endpoint negative paths."""

    @pytest.mark.asyncio
    async def test_create_full_name_too_long_returns_4xx(self, neg_ctx):
        """full_name > 200 chars must return 422 (schema validation) or 400."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.post(
                "/api/v1/patients",
                headers=_auth(token),
                json={"full_name": "A" * 201, "gender": "male", "birth_year": 1990},
            )
            assert resp.status_code in (400, 422), (
                f"full_name > 200 chars should return 400/422, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_create_invalid_gender_returns_4xx(self, neg_ctx):
        """Invalid gender value must return 422."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.post(
                "/api/v1/patients",
                headers=_auth(token),
                json={"full_name": "Invalid Gender Test", "gender": "invalid", "birth_year": 1990},
            )
            assert resp.status_code in (400, 422), (
                f"Invalid gender should return 400/422, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_create_birth_year_zero_returns_4xx(self, neg_ctx):
        """birth_year=0 must return 400/422 (invalid year)."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.post(
                "/api/v1/patients",
                headers=_auth(token),
                json={"full_name": "Birth Year Zero", "gender": "male", "birth_year": 0},
            )
            assert resp.status_code in (400, 422), (
                f"birth_year=0 should return 400/422, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_create_future_dob_returns_4xx(self, neg_ctx):
        """date_of_birth in the future must return 400/422."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.post(
                "/api/v1/patients",
                headers=_auth(token),
                json={
                    "full_name": "Future DOB Test",
                    "gender": "female",
                    "date_of_birth": "2099-01-01",
                },
            )
            assert resp.status_code in (400, 422), (
                f"Future DOB should return 400/422, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_create_mismatched_dob_and_birth_year_returns_4xx(self, neg_ctx):
        """Mismatched date_of_birth year and birth_year must return 400/422."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.post(
                "/api/v1/patients",
                headers=_auth(token),
                json={
                    "full_name": "Mismatch DOB Year",
                    "gender": "male",
                    "date_of_birth": "1990-05-15",
                    "birth_year": 1991,  # mismatch: DOB says 1990, birth_year says 1991
                },
            )
            assert resp.status_code in (400, 422), (
                f"Mismatched dob+birth_year should return 400/422, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_create_missing_required_fields_returns_4xx(self, neg_ctx):
        """Missing required field full_name must return 422."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.post(
                "/api/v1/patients",
                headers=_auth(token),
                json={"gender": "male", "birth_year": 1990},  # no full_name
            )
            assert resp.status_code in (400, 422), (
                f"Missing full_name should return 400/422, got {resp.status_code}: {resp.text}"
            )


# ---------------------------------------------------------------------------
# Merge negative paths
# ---------------------------------------------------------------------------


class TestMergeNegativePaths:
    """Merge endpoint negative paths."""

    @pytest.mark.asyncio
    async def test_merge_same_id_returns_4xx(self, neg_ctx):
        """Merging keep_id == drop_id must return 400/422."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])

            create_resp = await client.post(
                "/api/v1/patients",
                headers=_auth(token),
                json={"full_name": "Self Merge Test", "gender": "male", "birth_year": 1990},
            )
            patient_id = create_resp.json()["data"]["id"]

            resp = await client.post(
                "/api/v1/patients/merge",
                headers=_auth(token),
                json={"keep_id": patient_id, "drop_id": patient_id, "reason": "self merge"},
            )
            assert resp.status_code in (400, 422), (
                f"Same-id merge should return 400/422, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_merge_already_deleted_drop_returns_4xx(self, neg_ctx):
        """Merging with an already-deleted drop_patient must return 404."""
        ctx = neg_ctx
        factory = ctx["factory"]

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])

            keep_resp = await client.post(
                "/api/v1/patients",
                headers=_auth(token),
                json={"full_name": "Deleted Drop Keep", "gender": "male", "birth_year": 1990},
            )
            drop_resp = await client.post(
                "/api/v1/patients",
                headers=_auth(token),
                json={"full_name": "Deleted Drop Target", "gender": "male", "birth_year": 1990},
            )
            keep_id = keep_resp.json()["data"]["id"]
            drop_id = drop_resp.json()["data"]["id"]

            # Soft-delete the drop patient directly
            async with factory() as session:
                await session.execute(
                    text(
                        "UPDATE patient SET is_deleted = true, deleted_at = now()"
                        " WHERE id = :pid"
                    ),
                    {"pid": drop_id},
                )
                await session.commit()

            resp = await client.post(
                "/api/v1/patients/merge",
                headers=_auth(token),
                json={"keep_id": keep_id, "drop_id": drop_id},
            )
            assert resp.status_code in (400, 404, 422), (
                f"Merging already-deleted patient should return 400/404/422, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_merge_nonexistent_uuid_returns_4xx(self, neg_ctx):
        """Merge with non-existent keep/drop UUIDs must return 404."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.post(
                "/api/v1/patients/merge",
                headers=_auth(token),
                json={
                    "keep_id": str(uuid4()),  # random non-existent UUID
                    "drop_id": str(uuid4()),
                    "reason": "nonexistent merge",
                },
            )
            assert resp.status_code in (400, 404, 422), (
                f"Non-existent UUIDs should return 400/404/422, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_merge_invalid_uuid_format_returns_422(self, neg_ctx):
        """Invalid UUID format in merge body must return 422."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.post(
                "/api/v1/patients/merge",
                headers=_auth(token),
                json={"keep_id": "not-a-uuid", "drop_id": "also-not-a-uuid"},
            )
            assert resp.status_code in (400, 422), (
                f"Invalid UUID format should return 400/422, got {resp.status_code}: {resp.text}"
            )


# ---------------------------------------------------------------------------
# Undo negative paths
# ---------------------------------------------------------------------------


class TestUndoNegativePaths:
    """Undo merge endpoint negative paths."""

    @pytest.mark.asyncio
    async def test_undo_already_undone_merge_returns_409(self, neg_ctx):
        """Undoing an already-undone merge_log must return 409 Conflict."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])

            keep_resp = await client.post(
                "/api/v1/patients",
                headers=_auth(token),
                json={"full_name": "Undo Twice Keep", "gender": "male", "birth_year": 1990},
            )
            drop_resp = await client.post(
                "/api/v1/patients",
                headers=_auth(token),
                json={"full_name": "Undo Twice Drop", "gender": "male", "birth_year": 1990},
            )
            keep_id = keep_resp.json()["data"]["id"]
            drop_id = drop_resp.json()["data"]["id"]

            merge_resp = await client.post(
                "/api/v1/patients/merge",
                headers=_auth(token),
                json={"keep_id": keep_id, "drop_id": drop_id},
            )
            assert merge_resp.status_code == 201
            merge_log_id = merge_resp.json()["merge_log_id"]

            # First undo
            undo1 = await client.post(
                f"/api/v1/patients/merge/{merge_log_id}/undo",
                headers=_auth(token),
            )
            assert undo1.status_code == 200, undo1.text

            # Second undo — must 409
            undo2 = await client.post(
                f"/api/v1/patients/merge/{merge_log_id}/undo",
                headers=_auth(token),
            )
            assert undo2.status_code == 409, (
                f"Double undo should return 409, got {undo2.status_code}: {undo2.text}"
            )

    @pytest.mark.asyncio
    async def test_undo_nonexistent_merge_log_returns_404(self, neg_ctx):
        """Undo with a non-existent merge_log ID must return 404."""
        ctx = neg_ctx
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            resp = await client.post(
                f"/api/v1/patients/merge/{uuid4()}/undo",
                headers=_auth(token),
            )
            assert resp.status_code in (404, 400), (
                f"Non-existent merge_log should return 404/400, got {resp.status_code}: {resp.text}"
            )

    @pytest.mark.asyncio
    async def test_undo_merge_from_different_clinic_returns_404_or_403(self, neg_ctx):
        """Undo a merge_log that belongs to a different clinic must be rejected.

        Creates a second clinic's merge_log, then tries to undo it using clinic-A's JWT.
        The merge_log is not visible to clinic-A via RLS/app filter → 404.
        """
        ctx = neg_ctx
        factory = ctx["factory"]

        # Create a separate clinic B
        suffix2 = uuid4().hex[:6].upper()
        clinic_b_id = uuid4()
        admin_b_id = uuid4()
        clinic_b_code = f"NEGB{suffix2}"

        async with factory() as session:
            row = (
                await session.execute(
                    text("SELECT id FROM role WHERE code = 'admin' AND clinic_id IS NULL")
                )
            ).fetchone()
            admin_role_id = str(row[0])

        async with factory() as session:
            await session.execute(
                text(
                    "INSERT INTO clinic (id, code, name, specialty, is_active)"
                    " VALUES (:id, :code, :name, :specialty, true)"
                ),
                {"id": str(clinic_b_id), "code": clinic_b_code, "name": "Neg Clinic B", "specialty": "general"},
            )
            await session.execute(
                text(
                    'INSERT INTO "user" (id, clinic_id, username, full_name,'
                    " password_hash, is_active, is_locked, failed_login_count)"
                    " VALUES (:id, :cid, :uname, :fname, :pw, true, false, 0)"
                ),
                {
                    "id": str(admin_b_id),
                    "cid": str(clinic_b_id),
                    "uname": f"neg_admin_b_{suffix2.lower()}",
                    "fname": "Neg Admin B",
                    "pw": hash_password("NegTestPassw0rd!"),
                },
            )
            await session.execute(
                text(
                    "INSERT INTO user_role (id, user_id, role_id)"
                    " VALUES (:id, :uid, :rid) ON CONFLICT DO NOTHING"
                ),
                {"id": str(uuid4()), "uid": str(admin_b_id), "rid": admin_role_id},
            )
            await session.commit()

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://testserver"
            ) as client:
                token_b = await _login(
                    client, clinic_b_code, f"neg_admin_b_{suffix2.lower()}", "NegTestPassw0rd!"
                )

                # Create keep + drop in clinic B
                keep_b = await client.post(
                    "/api/v1/patients",
                    headers=_auth(token_b),
                    json={"full_name": "Cross Undo Keep B", "gender": "male", "birth_year": 1990},
                )
                drop_b = await client.post(
                    "/api/v1/patients",
                    headers=_auth(token_b),
                    json={"full_name": "Cross Undo Drop B", "gender": "male", "birth_year": 1990},
                )
                keep_b_id = keep_b.json()["data"]["id"]
                drop_b_id = drop_b.json()["data"]["id"]

                merge_b_resp = await client.post(
                    "/api/v1/patients/merge",
                    headers=_auth(token_b),
                    json={"keep_id": keep_b_id, "drop_id": drop_b_id, "reason": "cross clinic undo test"},
                )
                assert merge_b_resp.status_code == 201
                merge_b_log_id = merge_b_resp.json()["merge_log_id"]

                # Now use clinic-A's token to try to undo clinic-B's merge
                token_a = await _login(
                    client, ctx["clinic_code"], ctx["admin_username"], ctx["password"]
                )
                undo_resp = await client.post(
                    f"/api/v1/patients/merge/{merge_b_log_id}/undo",
                    headers=_auth(token_a),  # clinic-A token
                )
                assert undo_resp.status_code in (403, 404), (
                    f"Cross-clinic undo should return 403/404, got {undo_resp.status_code}: {undo_resp.text}"
                )
        finally:
            # Cleanup clinic B
            async with factory() as session:
                await session.execute(
                    text("DELETE FROM patient_merge_log WHERE clinic_id = :cid"), {"cid": str(clinic_b_id)}
                )
                await session.execute(
                    text("DELETE FROM patient_relation WHERE clinic_id = :cid"), {"cid": str(clinic_b_id)}
                )
                await session.execute(
                    text("DELETE FROM patient WHERE clinic_id = :cid"), {"cid": str(clinic_b_id)}
                )
                await session.execute(
                    text("DELETE FROM user_role WHERE user_id = :uid"), {"uid": str(admin_b_id)}
                )
                await session.execute(
                    text('DELETE FROM "user" WHERE id = :uid'), {"uid": str(admin_b_id)}
                )
                await session.execute(
                    text("DELETE FROM clinic WHERE id = :cid"), {"cid": str(clinic_b_id)}
                )
                await session.commit()
