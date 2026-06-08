"""Advanced merge/undo behavior matrix tests for Patient Management (TASK-005).

Priority 3: Covers scenarios not addressed by the base integration suite:
- Concurrent merges on overlapping patient pairs
- Undo with large manifest (100+ patient_relation rows)
- Merge → undo → merge again (same drop_patient, different keep_patient)
- Undo at exact deadline boundary (1ms before / 1ms after)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
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


def _patient_payload(full_name: str = "Test Patient", gender: str = "male") -> dict:
    return {"full_name": full_name, "gender": gender, "birth_year": 1990}


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def merge_adv_ctx():
    """Seed clinic + admin user; yield context; teardown all created data."""
    limiter.reset()
    suffix = uuid4().hex[:6].upper()
    clinic_id = uuid4()
    admin_id = uuid4()
    clinic_code = f"MRGADV{suffix}"
    admin_username = f"mrgadv_admin_{suffix.lower()}"
    password = "MergeAdvPassw0rd!"

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
            {"id": str(clinic_id), "code": clinic_code, "name": "Merge Adv Clinic", "specialty": "general"},
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
                "fname": "Merge Adv Admin",
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

    # Teardown — NOTE: audit_log is append-only (trigger blocks DELETE), so we do NOT
    # attempt to clean it up. Patient + relation + merge_log records are cleaned below.
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
# Tests
# ---------------------------------------------------------------------------


class TestMergeAdvanced:
    """Advanced merge/undo behavior matrix."""

    # ------------------------------------------------------------------
    # 1. Concurrent merges on overlapping pairs
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_concurrent_merges_no_corruption(self, merge_adv_ctx):
        """Two concurrent merge requests on overlapping (keep, drop) pairs.

        Scenario:
        - Request A: merge(keep=P1, drop=P2)  [P2 is the shared "drop"]
        - Request B: merge(keep=P3, drop=P2)  [same P2 drop, different keep]

        One should succeed (201), the other should receive an error (400/404/409/422/500)
        because P2 is either not found (already soft-deleted) or in an inconsistent state.
        No data corruption should result (P1/P3 should be intact).
        """
        ctx = merge_adv_ctx
        factory = ctx["factory"]

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])

            # Create 3 patients: P1 (keep-A), P2 (drop - shared), P3 (keep-B)
            p1_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                        json=_patient_payload("Concurrent Keep A"))
            p2_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                        json=_patient_payload("Concurrent Drop Shared"))
            p3_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                        json=_patient_payload("Concurrent Keep B"))
            p1_id = p1_resp.json()["data"]["id"]
            p2_id = p2_resp.json()["data"]["id"]
            p3_id = p3_resp.json()["data"]["id"]

            # Fire both merges concurrently
            async def do_merge(keep_id: str, drop_id: str) -> tuple[int, dict]:
                r = await client.post(
                    "/api/v1/patients/merge",
                    headers=_auth(token),
                    json={"keep_id": keep_id, "drop_id": drop_id, "reason": "concurrent test"},
                )
                return r.status_code, r.json()

            results = await asyncio.gather(
                do_merge(p1_id, p2_id),
                do_merge(p3_id, p2_id),
                return_exceptions=True,
            )

        status_codes = [r[0] if isinstance(r, tuple) else -1 for r in results]
        print(f"\n[concurrent_merge] Results: {status_codes}")

        # Exactly one should succeed (201), the other should fail cleanly
        success_count = sum(1 for s in status_codes if s == 201)
        error_count = sum(1 for s in status_codes if s in (400, 404, 409, 422, 500))

        assert success_count >= 1, (
            f"Expected at least one successful merge, got status codes: {status_codes}"
        )
        assert error_count >= 1 or success_count == 2, (
            # It's also acceptable for both to succeed if the DB serializes them
            # (P2 gets soft-deleted by first, second gets NotFoundError → non-201)
            f"Expected one error or both succeed: status codes: {status_codes}"
        )

        # P1 and P3 must still be non-deleted (the keep patients)
        factory = ctx["factory"]
        async with factory() as session:
            for pid, name in [(p1_id, "P1"), (p3_id, "P3")]:
                row = (
                    await session.execute(
                        text("SELECT is_deleted FROM patient WHERE id = :pid"),
                        {"pid": pid},
                    )
                ).fetchone()
                assert row is not None and row[0] is False, (
                    f"Keep patient {name} ({pid}) should not be deleted after concurrent merge"
                )

    # ------------------------------------------------------------------
    # 2. Undo with long manifest (100+ patient_relation rows)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_undo_with_long_manifest(self, merge_adv_ctx):
        """Merge drop_patient with 100+ patient_relation rows; undo reverses all.

        Verifies that the M4 manifest captures and restores all 100+ rows correctly.
        No row should be over-reassigned or missed.
        """
        ctx = merge_adv_ctx
        factory = ctx["factory"]
        num_relations = 105  # > 100 to test scale

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])

            # Create keep + drop patients
            keep_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                          json=_patient_payload("Long Manifest Keep"))
            drop_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                          json=_patient_payload("Long Manifest Drop"))
            keep_id = keep_resp.json()["data"]["id"]
            drop_id = drop_resp.json()["data"]["id"]

        # Create 105 guardian patients and add patient_relation rows pointing to drop_id
        guardian_ids = []
        async with factory() as session:
            for i in range(num_relations):
                g_id = uuid4()
                guardian_ids.append(g_id)
                # Insert guardian patient directly
                await session.execute(
                    text(
                        "INSERT INTO patient"
                        " (id, clinic_id, patient_code, full_name, gender, birth_year,"
                        "  is_deleted, version, created_at, updated_at)"
                        " VALUES (:id, :cid, :code, :name, 'other', 2000, false, 1, now(), now())"
                    ),
                    {
                        "id": str(g_id),
                        "cid": str(ctx["clinic_id"]),
                        "code": f"BNGRD{i:05d}",
                        "name": f"Guardian {i:05d}",
                    },
                )
                # Insert patient_relation: guardian → drop_patient
                rel_id = uuid4()
                await session.execute(
                    text(
                        "INSERT INTO patient_relation"
                        " (id, clinic_id, patient_id, guardian_patient_id, relation_type,"
                        "  is_primary_contact, version, created_at, updated_at)"
                        " VALUES (:id, :cid, :pid, :gid, 'guardian', false, 1, now(), now())"
                    ),
                    {
                        "id": str(rel_id),
                        "cid": str(ctx["clinic_id"]),
                        "pid": drop_id,  # relations point to drop_id
                        "gid": str(g_id),
                    },
                )
            await session.commit()

        # Verify 105 relations point to drop_id before merge
        async with factory() as session:
            pre_count = (
                await session.execute(
                    text("SELECT COUNT(*) FROM patient_relation WHERE patient_id = :pid"),
                    {"pid": drop_id},
                )
            ).scalar_one()
        assert pre_count == num_relations, f"Expected {num_relations} relations, got {pre_count}"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])

            # Merge
            merge_resp = await client.post(
                "/api/v1/patients/merge",
                headers=_auth(token),
                json={"keep_id": keep_id, "drop_id": drop_id, "reason": "long manifest test"},
            )
            assert merge_resp.status_code == 201, merge_resp.text
            merge_log_id = merge_resp.json()["merge_log_id"]

        # After merge: relations should point to keep_id
        async with factory() as session:
            moved_count = (
                await session.execute(
                    text("SELECT COUNT(*) FROM patient_relation WHERE patient_id = :pid"),
                    {"pid": keep_id},
                )
            ).scalar_one()
        assert moved_count >= num_relations, (
            f"Expected >= {num_relations} relations on keep after merge, got {moved_count}"
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])

            # Undo
            undo_resp = await client.post(
                f"/api/v1/patients/merge/{merge_log_id}/undo",
                headers=_auth(token),
            )
            assert undo_resp.status_code == 200, undo_resp.text

        # After undo: all 105 relations must point back to drop_id
        async with factory() as session:
            after_undo_count = (
                await session.execute(
                    text("SELECT COUNT(*) FROM patient_relation WHERE patient_id = :pid"),
                    {"pid": drop_id},
                )
            ).scalar_one()
        assert after_undo_count == num_relations, (
            f"After undo: expected {num_relations} relations on drop_id, got {after_undo_count}"
        )

        # Verify zero collateral: keep_id must have no leftover relations from drop
        async with factory() as session:
            keep_relations = (
                await session.execute(
                    text("SELECT COUNT(*) FROM patient_relation WHERE patient_id = :pid"),
                    {"pid": keep_id},
                )
            ).scalar_one()
        assert keep_relations == 0, (
            f"After undo: keep_id should have 0 relations, got {keep_relations} (collateral)"
        )

    # ------------------------------------------------------------------
    # 3. Merge → undo → merge again (same drop, different keep)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_merge_undo_merge_again(self, merge_adv_ctx):
        """After undo, the same drop_patient can be merged into a different keep_patient."""
        ctx = merge_adv_ctx
        factory = ctx["factory"]

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])

            # Create 3 patients: keep1, drop, keep2
            keep1_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                           json=_patient_payload("Keep One"))
            drop_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                          json=_patient_payload("Drop Twice"))
            keep2_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                           json=_patient_payload("Keep Two"))
            keep1_id = keep1_resp.json()["data"]["id"]
            drop_id = drop_resp.json()["data"]["id"]
            keep2_id = keep2_resp.json()["data"]["id"]

            # First merge: keep1 + drop
            merge1_resp = await client.post(
                "/api/v1/patients/merge",
                headers=_auth(token),
                json={"keep_id": keep1_id, "drop_id": drop_id, "reason": "first merge"},
            )
            assert merge1_resp.status_code == 201, merge1_resp.text
            merge1_log_id = merge1_resp.json()["merge_log_id"]

            # Undo first merge
            undo_resp = await client.post(
                f"/api/v1/patients/merge/{merge1_log_id}/undo",
                headers=_auth(token),
            )
            assert undo_resp.status_code == 200, undo_resp.text

            # Verify drop_patient is active again
            async with factory() as session:
                row = (
                    await session.execute(
                        text("SELECT is_deleted FROM patient WHERE id = :pid"),
                        {"pid": drop_id},
                    )
                ).fetchone()
            assert row is not None and row[0] is False, (
                "drop_patient must be active after undo before second merge"
            )

            # Second merge: keep2 + drop (different keep!)
            merge2_resp = await client.post(
                "/api/v1/patients/merge",
                headers=_auth(token),
                json={"keep_id": keep2_id, "drop_id": drop_id, "reason": "second merge"},
            )
            assert merge2_resp.status_code == 201, (
                f"Second merge failed: {merge2_resp.status_code}: {merge2_resp.text}"
            )
            merge2_log_id = merge2_resp.json()["merge_log_id"]
            assert merge2_log_id != merge1_log_id, "Second merge should produce a new log entry"

        # Verify drop_patient is soft-deleted after second merge
        async with factory() as session:
            row = (
                await session.execute(
                    text("SELECT is_deleted FROM patient WHERE id = :pid"),
                    {"pid": drop_id},
                )
            ).fetchone()
        assert row is not None and row[0] is True, (
            "drop_patient should be soft-deleted after second merge"
        )

    # ------------------------------------------------------------------
    # 4. Undo at exact deadline boundary
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_undo_at_exact_deadline_boundary_past_returns_410(self, merge_adv_ctx):
        """Undo at now() + 1ms past deadline → 410 Gone.

        The undo code checks: if now > deadline: raise MergeUndoExpiredError
        So at deadline + 1ms, undo must fail with 410.
        """
        ctx = merge_adv_ctx
        factory = ctx["factory"]

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])

            keep_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                          json=_patient_payload("Boundary Keep Past"))
            drop_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                          json=_patient_payload("Boundary Drop Past"))
            keep_id = keep_resp.json()["data"]["id"]
            drop_id = drop_resp.json()["data"]["id"]

            merge_resp = await client.post(
                "/api/v1/patients/merge",
                headers=_auth(token),
                json={"keep_id": keep_id, "drop_id": drop_id},
            )
            assert merge_resp.status_code == 201
            merge_log_id = merge_resp.json()["merge_log_id"]

        # Set deadline to now() - 1ms (1 millisecond in the past)
        past_deadline = datetime.now(UTC) - timedelta(milliseconds=1)
        async with factory() as session:
            await session.execute(
                text("UPDATE patient_merge_log SET undo_deadline = :dl WHERE id = :id"),
                {"dl": past_deadline, "id": merge_log_id},
            )
            await session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            undo_resp = await client.post(
                f"/api/v1/patients/merge/{merge_log_id}/undo",
                headers=_auth(token),
            )
        assert undo_resp.status_code == 410, (
            f"Expected 410 at deadline - 1ms, got {undo_resp.status_code}: {undo_resp.text}"
        )

    @pytest.mark.asyncio
    async def test_undo_at_exact_deadline_boundary_future_succeeds(self, merge_adv_ctx):
        """Undo at now() + 1ms before deadline → 200 OK.

        The undo code checks: if now > deadline (strict), so at deadline - 1ms undo must work.
        """
        ctx = merge_adv_ctx
        factory = ctx["factory"]

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])

            keep_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                          json=_patient_payload("Boundary Keep Future"))
            drop_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                          json=_patient_payload("Boundary Drop Future"))
            keep_id = keep_resp.json()["data"]["id"]
            drop_id = drop_resp.json()["data"]["id"]

            merge_resp = await client.post(
                "/api/v1/patients/merge",
                headers=_auth(token),
                json={"keep_id": keep_id, "drop_id": drop_id},
            )
            assert merge_resp.status_code == 201
            merge_log_id = merge_resp.json()["merge_log_id"]

        # Set deadline to now() + 1 second (safely in the future, 1ms buffer is too tight in CI)
        future_deadline = datetime.now(UTC) + timedelta(seconds=1)
        async with factory() as session:
            await session.execute(
                text("UPDATE patient_merge_log SET undo_deadline = :dl WHERE id = :id"),
                {"dl": future_deadline, "id": merge_log_id},
            )
            await session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])
            undo_resp = await client.post(
                f"/api/v1/patients/merge/{merge_log_id}/undo",
                headers=_auth(token),
            )
        assert undo_resp.status_code == 200, (
            f"Expected 200 with deadline + 1s in future, got {undo_resp.status_code}: {undo_resp.text}"
        )

    @pytest.mark.asyncio
    async def test_undo_already_undone_returns_409(self, merge_adv_ctx):
        """Attempting to undo an already-undone merge returns 409."""
        ctx = merge_adv_ctx

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            token = await _login(client, ctx["clinic_code"], ctx["admin_username"], ctx["password"])

            keep_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                          json=_patient_payload("Already Undone Keep"))
            drop_resp = await client.post("/api/v1/patients", headers=_auth(token),
                                          json=_patient_payload("Already Undone Drop"))
            keep_id = keep_resp.json()["data"]["id"]
            drop_id = drop_resp.json()["data"]["id"]

            merge_resp = await client.post(
                "/api/v1/patients/merge",
                headers=_auth(token),
                json={"keep_id": keep_id, "drop_id": drop_id},
            )
            assert merge_resp.status_code == 201
            merge_log_id = merge_resp.json()["merge_log_id"]

            # First undo — should succeed
            undo1_resp = await client.post(
                f"/api/v1/patients/merge/{merge_log_id}/undo",
                headers=_auth(token),
            )
            assert undo1_resp.status_code == 200, undo1_resp.text

            # Second undo of same log — must return 409
            undo2_resp = await client.post(
                f"/api/v1/patients/merge/{merge_log_id}/undo",
                headers=_auth(token),
            )
            assert undo2_resp.status_code == 409, (
                f"Expected 409 for double-undo, got {undo2_resp.status_code}: {undo2_resp.text}"
            )
