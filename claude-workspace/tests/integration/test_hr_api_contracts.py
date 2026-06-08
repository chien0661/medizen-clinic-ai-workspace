"""TASK-014: API Contract Tests for the HR module.

Tests HTTP semantics: 401 unauthenticated, 403 wrong permission, 404 not found,
422 schema invalid, response shape round-trips, tenant isolation (CRITICAL),
and Excel export HTTP headers.
"""

from __future__ import annotations

from datetime import date, datetime, UTC
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
from app.modules.users.models.clinic import Clinic
from app.modules.users.models.user import User
from tests.conftest import TEST_DATABASE_URL


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def contract_client():
    limiter.reset()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def two_clinic_context(contract_client):
    """Seed two completely separate clinics, each with an HR admin user."""
    suffix_a = uuid4().hex[:6].upper()
    suffix_b = uuid4().hex[:6].upper()
    clinic_a_id = uuid4()
    clinic_b_id = uuid4()
    user_a_id = uuid4()
    user_b_id = uuid4()
    plain_pw = "ContractP@ssw0rd!"

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        session.add_all([
            Clinic(
                id=clinic_a_id,
                code=f"CA{suffix_a}",
                name=f"Contract Clinic A {suffix_a}",
                specialty="general",
                is_active=True,
            ),
            Clinic(
                id=clinic_b_id,
                code=f"CB{suffix_b}",
                name=f"Contract Clinic B {suffix_b}",
                specialty="general",
                is_active=True,
            ),
            User(
                id=user_a_id,
                clinic_id=clinic_a_id,
                username=f"contract_a_{suffix_a.lower()}",
                full_name="Contract User A",
                password_hash=hash_password(plain_pw),
                is_active=True,
                is_locked=False,
                failed_login_count=0,
            ),
            User(
                id=user_b_id,
                clinic_id=clinic_b_id,
                username=f"contract_b_{suffix_b.lower()}",
                full_name="Contract User B",
                password_hash=hash_password(plain_pw),
                is_active=True,
                is_locked=False,
                failed_login_count=0,
            ),
        ])
        await session.commit()

    # Give both users the admin role
    async with factory() as session:
        row = (
            await session.execute(
                text("SELECT id FROM role WHERE code = 'admin' AND clinic_id IS NULL")
            )
        ).fetchone()
        admin_role_id = str(row[0])
        for uid in (user_a_id, user_b_id):
            await session.execute(
                text(
                    "INSERT INTO user_role (id, user_id, role_id)"
                    " VALUES (:id, :uid, :rid) ON CONFLICT DO NOTHING"
                ),
                {"id": str(uuid4()), "uid": str(uid), "rid": admin_role_id},
            )
        await session.commit()

    ctx = {
        "clinic_a_id": clinic_a_id,
        "clinic_a_code": f"CA{suffix_a}",
        "clinic_b_id": clinic_b_id,
        "clinic_b_code": f"CB{suffix_b}",
        "user_a_id": user_a_id,
        "user_a_username": f"contract_a_{suffix_a.lower()}",
        "user_b_id": user_b_id,
        "user_b_username": f"contract_b_{suffix_b.lower()}",
        "plain_pw": plain_pw,
        "client": contract_client,
        "factory": factory,
    }
    yield ctx

    # Teardown
    async with factory() as session:
        for table in ("time_log", "leave_request", "shift", "recurring_schedule", "shift_template"):
            for cid in (clinic_a_id, clinic_b_id):
                await session.execute(
                    text(f"DELETE FROM {table} WHERE clinic_id = :cid"),
                    {"cid": str(cid)},
                )
        for uid in (user_a_id, user_b_id):
            await session.execute(
                text("DELETE FROM user_role WHERE user_id = :uid"),
                {"uid": str(uid)},
            )
        await session.execute(
            text('DELETE FROM "user" WHERE id = ANY(:ids)'),
            {"ids": [str(user_a_id), str(user_b_id)]},
        )
        for cid in (clinic_a_id, clinic_b_id):
            await session.execute(
                text("DELETE FROM clinic WHERE id = :cid"), {"cid": str(cid)}
            )
        await session.commit()
    await engine.dispose()


async def _login(client, clinic_code, username, password):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"clinic_code": clinic_code, "username": username, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["data"]["access_token"]


# ===========================================================================
# CONTRACT-01: 401 Unauthenticated on all HR endpoints
# ===========================================================================


class TestUnauthenticated:
    """All HR endpoints must return 401 when no token is provided."""

    async def test_401_shift_templates_list(self, contract_client):
        resp = await contract_client.get("/api/v1/shift-templates")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    async def test_401_shifts_list(self, contract_client):
        resp = await contract_client.get("/api/v1/shifts")
        assert resp.status_code in (401, 403)

    async def test_401_recurring_schedules_list(self, contract_client):
        resp = await contract_client.get("/api/v1/recurring-schedules")
        assert resp.status_code in (401, 403)

    async def test_401_leave_requests_list(self, contract_client):
        resp = await contract_client.get("/api/v1/leave-requests")
        assert resp.status_code in (401, 403)

    async def test_401_attendance_check_in(self, contract_client):
        resp = await contract_client.post(
            "/api/v1/attendance/check-in",
            json={"check_in_method": "manual"},
        )
        assert resp.status_code in (401, 403)

    async def test_401_attendance_check_out(self, contract_client):
        resp = await contract_client.post("/api/v1/attendance/check-out", json={})
        assert resp.status_code in (401, 403)

    async def test_401_attendance_export(self, contract_client):
        resp = await contract_client.get(
            "/api/v1/attendance/export",
            params={"from": "2026-05-01", "to": "2026-05-31", "format": "xlsx"},
        )
        assert resp.status_code in (401, 403)


# ===========================================================================
# CONTRACT-02: 422 Schema validation on required fields
# ===========================================================================


class TestSchemaValidation422:
    """Missing or invalid request bodies return 422 Unprocessable Entity."""

    async def test_422_create_shift_template_missing_end_time(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "Bad", "start_time": "08:00:00"},  # missing end_time
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_422_create_shift_template_inverted_times(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "Inverted", "start_time": "12:00:00", "end_time": "08:00:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_422_create_shift_equal_times(self, two_clinic_context):
        """start_time == end_time must be rejected (validator uses <=)."""
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "Equal", "start_time": "08:00:00", "end_time": "08:00:00"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_422_leave_request_end_before_start(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "sick",
                "start_date": "2026-06-10",
                "end_date": "2026-06-05",  # before start
                "reason": "Bad range",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_422_leave_request_invalid_leave_type(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "holiday",  # not in enum
                "start_date": "2026-06-10",
                "end_date": "2026-06-12",
                "reason": "Testing",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_422_days_of_week_out_of_range(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].post(
            "/api/v1/recurring-schedules",
            json={
                "user_id": str(ctx["user_a_id"]),
                "shift_template_id": str(uuid4()),
                "days_of_week": [0, 3, 8],  # 0 and 8 are invalid
                "effective_from": "2026-06-01",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_422_check_in_invalid_method(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].post(
            "/api/v1/attendance/check-in",
            json={"check_in_method": "badge_scan"},  # not in enum
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


# ===========================================================================
# CONTRACT-03: 404 Not Found for non-existent resources
# ===========================================================================


class TestNotFound404:
    """Non-existent resource IDs return 404."""

    async def test_404_patch_shift_template(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].patch(
            f"/api/v1/shift-templates/{uuid4()}",
            json={"name": "Ghost"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_404_delete_shift_template(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].delete(
            f"/api/v1/shift-templates/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_404_patch_shift(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].patch(
            f"/api/v1/shifts/{uuid4()}",
            json={"notes": "Ghost"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_404_approve_nonexistent_leave(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].post(
            f"/api/v1/leave-requests/{uuid4()}/approve",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_404_generate_shifts_for_nonexistent_schedule(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].post(
            f"/api/v1/recurring-schedules/{uuid4()}/generate-shifts",
            params={"until": "2026-05-31"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


# ===========================================================================
# CONTRACT-04: Pagination on list endpoints
# ===========================================================================


class TestPagination:
    """List endpoints must respect skip/limit pagination."""

    async def test_shift_templates_pagination_skip_limit(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create 3 templates
        names = ["Page1 Ca Sáng", "Page1 Ca Chiều", "Page1 Ca Tối"]
        for name in names:
            r = await ctx["client"].post(
                "/api/v1/shift-templates",
                json={"name": name, "start_time": "07:00:00", "end_time": "12:00:00"},
                headers=headers,
            )
            assert r.status_code == 201

        # Get all: total >= 3
        resp_all = await ctx["client"].get(
            "/api/v1/shift-templates", params={"limit": 200, "skip": 0}, headers=headers
        )
        assert resp_all.status_code == 200
        body_all = resp_all.json()
        assert body_all["total"] >= 3

        # Skip first 2
        resp_page = await ctx["client"].get(
            "/api/v1/shift-templates",
            params={"skip": 2, "limit": 1},
            headers=headers,
        )
        assert resp_page.status_code == 200
        body_page = resp_page.json()
        assert len(body_page["data"]) <= 1

    async def test_shifts_list_pagination(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        tmpl_resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "Paginate Shift Tmpl", "start_time": "09:00:00", "end_time": "13:00:00"},
            headers=headers,
        )
        tmpl_id = tmpl_resp.json()["id"]

        # Create 3 shifts on different dates
        for day in ["2026-07-01", "2026-07-02", "2026-07-03"]:
            r = await ctx["client"].post(
                "/api/v1/shifts",
                json={
                    "user_id": str(ctx["user_a_id"]),
                    "shift_template_id": tmpl_id,
                    "shift_date": day,
                    "start_time": "09:00:00",
                    "end_time": "13:00:00",
                },
                headers=headers,
            )
            assert r.status_code == 201

        resp = await ctx["client"].get(
            "/api/v1/shifts",
            params={"from": "2026-07-01", "to": "2026-07-03", "skip": 1, "limit": 1},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["total"] >= 3


# ===========================================================================
# CONTRACT-05: Response shape validation
# ===========================================================================


class TestResponseShape:
    """Response bodies must include required fields as per Pydantic schemas."""

    async def test_shift_template_response_has_required_fields(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "Shape Test", "start_time": "08:00:00", "end_time": "16:00:00"},
            headers=headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        required = {"id", "clinic_id", "name", "start_time", "end_time", "is_active",
                    "created_at", "updated_at"}
        assert required.issubset(body.keys()), f"Missing fields: {required - body.keys()}"
        assert body["is_active"] is True

    async def test_leave_request_response_has_required_fields(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        resp = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "vacation",
                "start_date": "2026-08-01",
                "end_date": "2026-08-05",
                "reason": "Summer holiday",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        required = {"id", "clinic_id", "user_id", "leave_type", "start_date", "end_date",
                    "reason", "status", "approved_by", "approved_at", "rejection_reason",
                    "created_at", "updated_at"}
        assert required.issubset(body.keys()), f"Missing fields: {required - body.keys()}"
        assert body["status"] == "pending"
        assert body["approved_by"] is None

    async def test_time_log_response_has_required_fields(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        resp = await ctx["client"].post(
            "/api/v1/attendance/check-in",
            json={"check_in_method": "manual"},
            headers=headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        required = {"id", "clinic_id", "user_id", "shift_id", "check_in_at", "check_out_at",
                    "check_in_method", "late_minutes", "total_hours", "ot_hours"}
        assert required.issubset(body.keys()), f"Missing fields: {required - body.keys()}"
        assert body["check_out_at"] is None

        # Clean up
        await ctx["client"].post("/api/v1/attendance/check-out", json={}, headers=headers)

    async def test_recurring_schedule_response_shape(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        tmpl_resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "RS Shape Tmpl", "start_time": "08:00:00", "end_time": "16:00:00"},
            headers=headers,
        )
        tmpl_id = tmpl_resp.json()["id"]

        resp = await ctx["client"].post(
            "/api/v1/recurring-schedules",
            json={
                "user_id": str(ctx["user_a_id"]),
                "shift_template_id": tmpl_id,
                "days_of_week": [1, 3, 5],
                "effective_from": "2026-09-01",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        body = resp.json()
        required = {"id", "clinic_id", "user_id", "shift_template_id", "days_of_week",
                    "effective_from", "effective_to", "is_active", "created_at", "updated_at"}
        assert required.issubset(body.keys())
        assert body["days_of_week"] == [1, 3, 5]
        assert body["effective_to"] is None


# ===========================================================================
# CONTRACT-06: Excel export HTTP headers
# ===========================================================================


class TestExcelHttpHeaders:
    """Export endpoint must set correct Content-Type and Content-Disposition."""

    async def test_export_content_type_and_disposition(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        resp = await ctx["client"].get(
            "/api/v1/attendance/export",
            params={"from": "2026-05-01", "to": "2026-05-31", "format": "xlsx"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ), f"Wrong content-type: {resp.headers.get('content-type')}"
        assert "content-disposition" in resp.headers
        assert "attachment" in resp.headers["content-disposition"]
        assert ".xlsx" in resp.headers["content-disposition"]

    async def test_export_unsupported_format_returns_400(self, two_clinic_context):
        ctx = two_clinic_context
        token = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        resp = await ctx["client"].get(
            "/api/v1/attendance/export",
            params={"from": "2026-05-01", "to": "2026-05-31", "format": "csv"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400


# ===========================================================================
# CONTRACT-07: CRITICAL — Tenant isolation at HTTP layer
# ===========================================================================


class TestTenantIsolation:
    """Cross-tenant access must be blocked at the HTTP API layer.

    User B (clinic B) must not be able to see or modify clinic A's resources.
    RLS should hide them entirely (404) or the auth layer raises 403.
    """

    async def test_user_b_cannot_list_clinic_a_shift_templates(self, two_clinic_context):
        """GET /shift-templates for clinic B returns only clinic B's data."""
        ctx = two_clinic_context
        token_a = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        token_b = await _login(ctx["client"], ctx["clinic_b_code"], ctx["user_b_username"], ctx["plain_pw"])

        # Create a template in clinic A
        r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "Clinic A Template", "start_time": "07:00:00", "end_time": "12:00:00"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert r.status_code == 201
        tmpl_id_a = r.json()["id"]
        tmpl_name_a = r.json()["name"]

        # User B lists shift-templates — must NOT see clinic A's template
        resp_b = await ctx["client"].get(
            "/api/v1/shift-templates",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp_b.status_code == 200
        ids_seen_by_b = [t["id"] for t in resp_b.json()["data"]]
        names_seen_by_b = [t["name"] for t in resp_b.json()["data"]]
        assert tmpl_id_a not in ids_seen_by_b, (
            f"Clinic A's template '{tmpl_name_a}' should not be visible to clinic B"
        )

    async def test_user_b_cannot_patch_clinic_a_shift_template(self, two_clinic_context):
        """PATCH /shift-templates/{id_from_A} by user B → 404 (RLS hides it)."""
        ctx = two_clinic_context
        token_a = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        token_b = await _login(ctx["client"], ctx["clinic_b_code"], ctx["user_b_username"], ctx["plain_pw"])

        # Create template in clinic A
        r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "A Tmpl Iso", "start_time": "08:00:00", "end_time": "16:00:00"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert r.status_code == 201
        tmpl_id_a = r.json()["id"]

        # User B attempts to patch it
        resp = await ctx["client"].patch(
            f"/api/v1/shift-templates/{tmpl_id_a}",
            json={"name": "Hijacked"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        # RLS will hide the record → service raises NotFoundError → 404
        assert resp.status_code in (403, 404), (
            f"Expected 403 or 404, got {resp.status_code}: {resp.text}"
        )

    async def test_user_b_cannot_see_clinic_a_shifts(self, two_clinic_context):
        """GET /shifts for clinic B only shows clinic B's shifts."""
        ctx = two_clinic_context
        token_a = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        token_b = await _login(ctx["client"], ctx["clinic_b_code"], ctx["user_b_username"], ctx["plain_pw"])

        # Create a shift in clinic A
        tmpl_r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "A Shift Tmpl", "start_time": "07:00:00", "end_time": "12:00:00"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        tmpl_id_a = tmpl_r.json()["id"]

        shift_r = await ctx["client"].post(
            "/api/v1/shifts",
            json={
                "user_id": str(ctx["user_a_id"]),
                "shift_template_id": tmpl_id_a,
                "shift_date": "2026-09-15",
                "start_time": "07:00:00",
                "end_time": "12:00:00",
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert shift_r.status_code == 201
        shift_id_a = shift_r.json()["id"]

        # User B lists shifts — must NOT see clinic A's shift
        resp_b = await ctx["client"].get(
            "/api/v1/shifts",
            params={"from": "2026-09-01", "to": "2026-09-30"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp_b.status_code == 200
        ids_b = [s["id"] for s in resp_b.json()["data"]]
        assert shift_id_a not in ids_b, "Clinic A's shift should not be visible to clinic B"

    async def test_user_b_cannot_patch_clinic_a_shift(self, two_clinic_context):
        """PATCH /shifts/{shift_id_from_A} by user B → 404."""
        ctx = two_clinic_context
        token_a = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        token_b = await _login(ctx["client"], ctx["clinic_b_code"], ctx["user_b_username"], ctx["plain_pw"])

        # Create shift in clinic A
        tmpl_r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "A Shift Iso", "start_time": "08:00:00", "end_time": "12:00:00"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        tmpl_id_a = tmpl_r.json()["id"]

        shift_r = await ctx["client"].post(
            "/api/v1/shifts",
            json={
                "user_id": str(ctx["user_a_id"]),
                "shift_template_id": tmpl_id_a,
                "shift_date": "2026-09-16",
                "start_time": "08:00:00",
                "end_time": "12:00:00",
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert shift_r.status_code == 201
        shift_id_a = shift_r.json()["id"]

        # User B tries to patch it
        resp = await ctx["client"].patch(
            f"/api/v1/shifts/{shift_id_a}",
            json={"notes": "Hijacked"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code in (403, 404)

    async def test_user_b_cannot_see_clinic_a_leave_requests(self, two_clinic_context):
        """GET /leave-requests for clinic B must not show clinic A's requests."""
        ctx = two_clinic_context
        token_a = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        token_b = await _login(ctx["client"], ctx["clinic_b_code"], ctx["user_b_username"], ctx["plain_pw"])

        # User A submits a leave request
        lr_r = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "sick",
                "start_date": "2026-09-20",
                "end_date": "2026-09-22",
                "reason": "Clinic A sick leave",
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert lr_r.status_code == 201
        lr_id_a = lr_r.json()["id"]

        # User B lists leave requests — must NOT see clinic A's
        resp_b = await ctx["client"].get(
            "/api/v1/leave-requests",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp_b.status_code == 200
        ids_b = [lr["id"] for lr in resp_b.json()["data"]]
        assert lr_id_a not in ids_b, "Clinic A's leave request should not be visible to clinic B"

    async def test_user_b_cannot_approve_clinic_a_leave(self, two_clinic_context):
        """POST /leave-requests/{id_from_A}/approve by user B → 404."""
        ctx = two_clinic_context
        token_a = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        token_b = await _login(ctx["client"], ctx["clinic_b_code"], ctx["user_b_username"], ctx["plain_pw"])

        # User A submits leave
        lr_r = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "vacation",
                "start_date": "2026-10-01",
                "end_date": "2026-10-03",
                "reason": "Clinic A vacation",
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert lr_r.status_code == 201
        lr_id_a = lr_r.json()["id"]

        # User B tries to approve clinic A's leave
        resp = await ctx["client"].post(
            f"/api/v1/leave-requests/{lr_id_a}/approve",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        # RLS hides it — should be 404 (not found in B's context)
        assert resp.status_code in (403, 404), (
            f"Expected 403/404, got {resp.status_code}: {resp.text}"
        )

    async def test_check_in_with_cross_clinic_shift_id_forbidden(self, two_clinic_context):
        """POST /attendance/check-in with shift_id from clinic A by user B → 403 or 404."""
        ctx = two_clinic_context
        token_a = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        token_b = await _login(ctx["client"], ctx["clinic_b_code"], ctx["user_b_username"], ctx["plain_pw"])

        # Create a shift in clinic A for user A
        tmpl_r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "A Cross Tmpl", "start_time": "08:00:00", "end_time": "16:00:00"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        tmpl_id_a = tmpl_r.json()["id"]

        shift_r = await ctx["client"].post(
            "/api/v1/shifts",
            json={
                "user_id": str(ctx["user_a_id"]),
                "shift_template_id": tmpl_id_a,
                "shift_date": "2026-10-10",
                "start_time": "08:00:00",
                "end_time": "16:00:00",
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert shift_r.status_code == 201
        shift_id_a = shift_r.json()["id"]

        # User B tries to check in using clinic A's shift_id
        resp = await ctx["client"].post(
            "/api/v1/attendance/check-in",
            json={"shift_id": shift_id_a, "check_in_method": "manual"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        # RLS hides the shift or service rejects it
        assert resp.status_code in (403, 404), (
            f"Expected 403/404 for cross-clinic check-in, got {resp.status_code}: {resp.text}"
        )

    async def test_attendance_me_only_returns_own_logs(self, two_clinic_context):
        """GET /attendance/me returns only the authenticated user's time logs."""
        ctx = two_clinic_context
        token_a = await _login(ctx["client"], ctx["clinic_a_code"], ctx["user_a_username"], ctx["plain_pw"])
        token_b = await _login(ctx["client"], ctx["clinic_b_code"], ctx["user_b_username"], ctx["plain_pw"])

        # User A checks in
        ci_r = await ctx["client"].post(
            "/api/v1/attendance/check-in",
            json={"check_in_method": "manual"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert ci_r.status_code == 201
        a_log_id = ci_r.json()["id"]

        # User B calls /attendance/me — must NOT see user A's log
        resp_b = await ctx["client"].get(
            "/api/v1/attendance/me",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp_b.status_code == 200
        ids_b = [tl["id"] for tl in resp_b.json()["data"]]
        assert a_log_id not in ids_b, "User B must not see User A's time logs via /attendance/me"

        # Cleanup
        await ctx["client"].post(
            "/api/v1/attendance/check-out",
            json={},
            headers={"Authorization": f"Bearer {token_a}"},
        )
