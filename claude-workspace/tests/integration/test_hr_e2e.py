"""TASK-014: End-to-end integration tests for the HR module.

Tests run against a real PostgreSQL database (alembic upgrade head must have
been run first) and a real Redis instance, exercising the full request stack
through app.main:app.

Acceptance Criteria covered:
  AC1 — Recurring (Mon/Wed/Fri, morning shift, from 2026-05-01) → shifts generated for May
  AC2 — LeaveRequest approved 2026-05-10→12 → shifts in range → status=on_leave
  AC3 — Check-in 7:45 for shift 7:30 → late_minutes = 15
  AC4 — Check-out 12:30 for shift end 12:00 → ot_hours = 0.5
  AC5 — Excel export 1 month × 10 employees < 5s  (timing assertion)
  AC6 — Duplicate active check-in for same user → 409
"""

from __future__ import annotations

import time as stdlib_time
from datetime import date, time
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
async def hr_e2e_client():
    limiter.reset()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def hr_context(hr_e2e_client):
    """Seed a clinic + admin user + staff users, wire admin role, yield context dict."""
    clinic_id = uuid4()
    admin_user_id = uuid4()
    staff_user_id = uuid4()
    suffix = clinic_id.hex[:6].upper()
    plain_pw = "HrTestPassw0rd!"

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    # Seed clinic + users
    async with factory() as session:
        clinic = Clinic(
            id=clinic_id,
            code=f"HR{suffix}",
            name=f"HR Test Clinic {suffix}",
            specialty="general",
            is_active=True,
        )
        admin_user = User(
            id=admin_user_id,
            clinic_id=clinic_id,
            username=f"hr_admin_{suffix.lower()}",
            full_name="HR Admin",
            password_hash=hash_password(plain_pw),
            is_active=True,
            is_locked=False,
            failed_login_count=0,
        )
        staff_user = User(
            id=staff_user_id,
            clinic_id=clinic_id,
            username=f"hr_staff_{suffix.lower()}",
            full_name="HR Staff",
            password_hash=hash_password(plain_pw),
            is_active=True,
            is_locked=False,
            failed_login_count=0,
        )
        session.add_all([clinic, admin_user, staff_user])
        await session.commit()

    # Assign admin role
    async with factory() as session:
        row = (
            await session.execute(
                text("SELECT id FROM role WHERE code = 'admin' AND clinic_id IS NULL")
            )
        ).fetchone()
        admin_role_id = str(row[0])

        await session.execute(
            text(
                "INSERT INTO user_role (id, user_id, role_id)"
                " VALUES (:id, :uid, :rid) ON CONFLICT DO NOTHING"
            ),
            {"id": str(uuid4()), "uid": str(admin_user_id), "rid": admin_role_id},
        )
        # Also give staff "attendance.manage" via extra permission
        await session.execute(
            text(
                "INSERT INTO user_role (id, user_id, role_id)"
                " VALUES (:id, :uid, :rid) ON CONFLICT DO NOTHING"
            ),
            {"id": str(uuid4()), "uid": str(staff_user_id), "rid": admin_role_id},
        )
        await session.commit()

    ctx = {
        "clinic_id": clinic_id,
        "clinic_code": f"HR{suffix}",
        "admin_user_id": admin_user_id,
        "staff_user_id": staff_user_id,
        "admin_username": f"hr_admin_{suffix.lower()}",
        "staff_username": f"hr_staff_{suffix.lower()}",
        "plain_pw": plain_pw,
        "client": hr_e2e_client,
        "factory": factory,
    }
    yield ctx

    # Teardown
    async with factory() as session:
        await session.execute(
            text("DELETE FROM time_log WHERE clinic_id = :cid"), {"cid": str(clinic_id)}
        )
        await session.execute(
            text("DELETE FROM leave_request WHERE clinic_id = :cid"), {"cid": str(clinic_id)}
        )
        await session.execute(
            text("DELETE FROM shift WHERE clinic_id = :cid"), {"cid": str(clinic_id)}
        )
        await session.execute(
            text("DELETE FROM recurring_schedule WHERE clinic_id = :cid"),
            {"cid": str(clinic_id)},
        )
        await session.execute(
            text("DELETE FROM shift_template WHERE clinic_id = :cid"), {"cid": str(clinic_id)}
        )
        await session.execute(
            text(
                "DELETE FROM user_role WHERE user_id IN (:a, :s)"
            ),
            {"a": str(admin_user_id), "s": str(staff_user_id)},
        )
        await session.execute(
            text("DELETE FROM \"user\" WHERE clinic_id = :cid"), {"cid": str(clinic_id)}
        )
        await session.execute(
            text("DELETE FROM clinic WHERE id = :cid"), {"cid": str(clinic_id)}
        )
        await session.commit()
    await engine.dispose()


# ---------------------------------------------------------------------------
# Helper: login
# ---------------------------------------------------------------------------


async def _login(client: AsyncClient, clinic_code: str, username: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"clinic_code": clinic_code, "username": username, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["data"]["access_token"]


# ---------------------------------------------------------------------------
# Shift Template CRUD
# ---------------------------------------------------------------------------


class TestShiftTemplateCRUD:
    async def test_create_and_list(self, hr_context):
        ctx = hr_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create
        resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "Morning", "start_time": "07:30:00", "end_time": "12:00:00"},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        tmpl = resp.json()
        assert tmpl["name"] == "Morning"
        assert tmpl["is_active"] is True

        # List
        resp2 = await ctx["client"].get("/api/v1/shift-templates", headers=headers)
        assert resp2.status_code == 200
        assert resp2.json()["total"] >= 1

    async def test_unauthorized_without_token(self, hr_context):
        ctx = hr_context
        resp = await ctx["client"].get("/api/v1/shift-templates")
        assert resp.status_code in (401, 403)

    async def test_patch_and_delete(self, hr_context):
        ctx = hr_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create
        resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "Afternoon", "start_time": "13:00:00", "end_time": "17:00:00"},
            headers=headers,
        )
        assert resp.status_code == 201
        tmpl_id = resp.json()["id"]

        # Patch
        resp2 = await ctx["client"].patch(
            f"/api/v1/shift-templates/{tmpl_id}",
            json={"name": "Afternoon v2"},
            headers=headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["name"] == "Afternoon v2"

        # Delete
        resp3 = await ctx["client"].delete(
            f"/api/v1/shift-templates/{tmpl_id}", headers=headers
        )
        assert resp3.status_code == 204


# ---------------------------------------------------------------------------
# AC1: Recurring schedule → generate shifts for May
# ---------------------------------------------------------------------------


class TestRecurringScheduleAndGeneration:
    async def test_ac1_recurring_generates_may_shifts(self, hr_context):
        """AC1: Mon/Wed/Fri morning shift from 2026-05-01 → cron generates May shifts."""
        ctx = hr_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create morning template
        tmpl_resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "AC1 Morning", "start_time": "07:30:00", "end_time": "12:00:00"},
            headers=headers,
        )
        assert tmpl_resp.status_code == 201
        template_id = tmpl_resp.json()["id"]

        # Create recurring schedule Mon/Wed/Fri from 2026-05-01
        rs_resp = await ctx["client"].post(
            "/api/v1/recurring-schedules",
            json={
                "user_id": str(ctx["staff_user_id"]),
                "shift_template_id": template_id,
                "days_of_week": [1, 3, 5],  # Mon=1, Wed=3, Fri=5
                "effective_from": "2026-05-01",
            },
            headers=headers,
        )
        assert rs_resp.status_code == 201
        schedule_id = rs_resp.json()["id"]

        # Generate shifts manually (simulates cron)
        gen_resp = await ctx["client"].post(
            f"/api/v1/recurring-schedules/{schedule_id}/generate-shifts?until=2026-05-31",
            headers=headers,
        )
        assert gen_resp.status_code == 200
        created = gen_resp.json()["created"]
        assert created > 0, "Should have created at least one shift"

        # Verify shifts exist for May
        shifts_resp = await ctx["client"].get(
            "/api/v1/shifts",
            params={
                "from": "2026-05-01",
                "to": "2026-05-31",
                "user_id": str(ctx["staff_user_id"]),
            },
            headers=headers,
        )
        assert shifts_resp.status_code == 200
        shifts = shifts_resp.json()["data"]

        # All shifts should be Mon/Wed/Fri
        for s in shifts:
            shift_date = date.fromisoformat(s["shift_date"])
            assert shift_date.isoweekday() in [1, 3, 5], (
                f"Shift on {shift_date} is weekday {shift_date.isoweekday()}, expected Mon/Wed/Fri"
            )

        # Second call should be idempotent (0 new shifts)
        gen_resp2 = await ctx["client"].post(
            f"/api/v1/recurring-schedules/{schedule_id}/generate-shifts?until=2026-05-31",
            headers=headers,
        )
        assert gen_resp2.status_code == 200
        assert gen_resp2.json()["created"] == 0

    async def test_recurring_crud(self, hr_context):
        """Create, list, update, delete recurring schedule."""
        ctx = hr_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        tmpl_resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "RS CRUD Tmpl", "start_time": "08:00:00", "end_time": "16:00:00"},
            headers=headers,
        )
        template_id = tmpl_resp.json()["id"]

        # Create
        resp = await ctx["client"].post(
            "/api/v1/recurring-schedules",
            json={
                "user_id": str(ctx["staff_user_id"]),
                "shift_template_id": template_id,
                "days_of_week": [1, 2],
                "effective_from": "2026-06-01",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        rs_id = resp.json()["id"]

        # List
        list_resp = await ctx["client"].get("/api/v1/recurring-schedules", headers=headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        # Update
        patch_resp = await ctx["client"].patch(
            f"/api/v1/recurring-schedules/{rs_id}",
            json={"is_active": False},
            headers=headers,
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["is_active"] is False

        # Delete
        del_resp = await ctx["client"].delete(
            f"/api/v1/recurring-schedules/{rs_id}", headers=headers
        )
        assert del_resp.status_code == 204


# ---------------------------------------------------------------------------
# AC2: Leave approval marks shifts on_leave
# ---------------------------------------------------------------------------


class TestLeaveRequest:
    async def test_ac2_approve_leave_marks_shifts(self, hr_context):
        """AC2: Leave 2026-05-10 → 12 approved → shifts in range become on_leave."""
        ctx = hr_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create template + shifts manually for May 10, 11, 12
        tmpl_resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "AC2 Morning", "start_time": "07:30:00", "end_time": "12:00:00"},
            headers=headers,
        )
        template_id = tmpl_resp.json()["id"]

        created_shift_ids = []
        for d in ["2026-05-10", "2026-05-11", "2026-05-12"]:
            sr = await ctx["client"].post(
                "/api/v1/shifts",
                json={
                    "user_id": str(ctx["staff_user_id"]),
                    "shift_template_id": template_id,
                    "shift_date": d,
                    "start_time": "07:30:00",
                    "end_time": "12:00:00",
                },
                headers=headers,
            )
            assert sr.status_code == 201
            created_shift_ids.append(sr.json()["id"])

        # Staff submits leave request
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])
        staff_headers = {"Authorization": f"Bearer {staff_token}"}

        lr_resp = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "sick",
                "start_date": "2026-05-10",
                "end_date": "2026-05-12",
                "reason": "Not feeling well",
            },
            headers=staff_headers,
        )
        assert lr_resp.status_code == 201
        lr_id = lr_resp.json()["id"]

        # Admin approves
        approve_resp = await ctx["client"].post(
            f"/api/v1/leave-requests/{lr_id}/approve",
            headers=headers,
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "approved"

        # Verify shifts are marked on_leave
        for shift_id in created_shift_ids:
            shift_resp = await ctx["client"].get(
                "/api/v1/shifts",
                params={"user_id": str(ctx["staff_user_id"]), "from": "2026-05-10", "to": "2026-05-12"},
                headers=headers,
            )
            assert shift_resp.status_code == 200

        # Direct DB check
        async with ctx["factory"]() as session:
            result = await session.execute(
                text(
                    "SELECT status FROM shift WHERE id = ANY(:ids) AND is_deleted = FALSE"
                ),
                {"ids": created_shift_ids},
            )
            statuses = [row[0] for row in result.all()]
        assert all(s == "on_leave" for s in statuses), f"Some shifts not on_leave: {statuses}"

    async def test_reject_leave(self, hr_context):
        ctx = hr_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        lr_resp = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "personal",
                "start_date": "2026-06-01",
                "end_date": "2026-06-02",
                "reason": "Personal day",
            },
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert lr_resp.status_code == 201
        lr_id = lr_resp.json()["id"]

        reject_resp = await ctx["client"].post(
            f"/api/v1/leave-requests/{lr_id}/reject",
            json={"rejection_reason": "Staffing shortage"},
            headers=headers,
        )
        assert reject_resp.status_code == 200
        assert reject_resp.json()["status"] == "rejected"


# ---------------------------------------------------------------------------
# AC3 + AC4 + AC6: Attendance
# ---------------------------------------------------------------------------


class TestAttendance:
    async def _setup_shift(self, client, headers, user_id, shift_date, start, end, tmpl_id):
        resp = await client.post(
            "/api/v1/shifts",
            json={
                "user_id": str(user_id),
                "shift_template_id": tmpl_id,
                "shift_date": shift_date,
                "start_time": start,
                "end_time": end,
            },
            headers=headers,
        )
        assert resp.status_code == 201
        return resp.json()

    async def test_ac3_late_minutes(self, hr_context):
        """AC3: Check-in 7:45 for shift 7:30 → late_minutes = 15."""
        ctx = hr_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        tmpl_resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "AC3 Morning", "start_time": "07:30:00", "end_time": "12:00:00"},
            headers=headers,
        )
        template_id = tmpl_resp.json()["id"]

        shift = await self._setup_shift(
            ctx["client"], headers,
            ctx["staff_user_id"], "2026-05-20", "07:30:00", "12:00:00", template_id
        )
        shift_id = shift["id"]

        # Staff checks in at 07:45 UTC
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        # Mock the current time via DB insert (direct insert to avoid real-time dependency)
        # Instead, we patch at the service layer for the check_in time
        from unittest.mock import patch  # noqa: PLC0415
        from datetime import datetime, UTC  # noqa: PLC0415

        mock_now = datetime(2026, 5, 20, 7, 45, tzinfo=UTC)
        with patch(
            "app.modules.hr.services.attendance_service.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = mock_now
            mock_dt.combine = datetime.combine

            resp = await ctx["client"].post(
                "/api/v1/attendance/check-in",
                json={"shift_id": shift_id, "check_in_method": "manual"},
                headers={"Authorization": f"Bearer {staff_token}"},
            )

        assert resp.status_code == 201, resp.text
        tl = resp.json()
        assert tl["late_minutes"] == 15, f"Expected 15 late minutes, got {tl['late_minutes']}"

        # Clean up: check out so future tests don't hit duplicate
        with patch(
            "app.modules.hr.services.attendance_service.datetime"
        ) as mock_dt2:
            mock_dt2.now.return_value = datetime(2026, 5, 20, 12, 0, tzinfo=UTC)
            mock_dt2.combine = datetime.combine
            await ctx["client"].post(
                "/api/v1/attendance/check-out",
                json={},
                headers={"Authorization": f"Bearer {staff_token}"},
            )

    async def test_ac4_ot_hours(self, hr_context):
        """AC4: Check-out 12:30 for shift end 12:00 → ot_hours = 0.5."""
        ctx = hr_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        tmpl_resp = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "AC4 Morning", "start_time": "08:00:00", "end_time": "12:00:00"},
            headers=headers,
        )
        template_id = tmpl_resp.json()["id"]

        shift = await self._setup_shift(
            ctx["client"], headers,
            ctx["staff_user_id"], "2026-05-21", "08:00:00", "12:00:00", template_id
        )
        shift_id = shift["id"]

        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        from unittest.mock import patch  # noqa: PLC0415
        from datetime import datetime, UTC  # noqa: PLC0415

        # Check in on time at 08:00
        with patch("app.modules.hr.services.attendance_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 5, 21, 8, 0, tzinfo=UTC)
            mock_dt.combine = datetime.combine
            ci_resp = await ctx["client"].post(
                "/api/v1/attendance/check-in",
                json={"shift_id": shift_id, "check_in_method": "manual"},
                headers={"Authorization": f"Bearer {staff_token}"},
            )
        assert ci_resp.status_code == 201

        # Check out at 12:30 (30 min OT)
        with patch("app.modules.hr.services.attendance_service.datetime") as mock_dt2:
            mock_dt2.now.return_value = datetime(2026, 5, 21, 12, 30, tzinfo=UTC)
            mock_dt2.combine = datetime.combine
            co_resp = await ctx["client"].post(
                "/api/v1/attendance/check-out",
                json={},
                headers={"Authorization": f"Bearer {staff_token}"},
            )
        assert co_resp.status_code == 200, co_resp.text
        tl = co_resp.json()
        assert float(tl["ot_hours"]) == 0.5, f"Expected ot_hours=0.5, got {tl['ot_hours']}"

    async def test_ac6_duplicate_checkin_returns_409(self, hr_context):
        """AC6: Duplicate active check-in for same user → 409."""
        ctx = hr_context
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])
        staff_headers = {"Authorization": f"Bearer {staff_token}"}

        from unittest.mock import patch  # noqa: PLC0415
        from datetime import datetime, UTC  # noqa: PLC0415

        # First check-in
        with patch("app.modules.hr.services.attendance_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 5, 22, 8, 0, tzinfo=UTC)
            mock_dt.combine = datetime.combine
            resp1 = await ctx["client"].post(
                "/api/v1/attendance/check-in",
                json={"check_in_method": "manual"},
                headers=staff_headers,
            )
        assert resp1.status_code == 201

        # Second check-in (duplicate) — must return 409
        with patch("app.modules.hr.services.attendance_service.datetime") as mock_dt2:
            mock_dt2.now.return_value = datetime(2026, 5, 22, 8, 5, tzinfo=UTC)
            mock_dt2.combine = datetime.combine
            resp2 = await ctx["client"].post(
                "/api/v1/attendance/check-in",
                json={"check_in_method": "manual"},
                headers=staff_headers,
            )
        assert resp2.status_code == 409, f"Expected 409, got {resp2.status_code}: {resp2.text}"

        # Clean up
        with patch("app.modules.hr.services.attendance_service.datetime") as mock_dt3:
            mock_dt3.now.return_value = datetime(2026, 5, 22, 12, 0, tzinfo=UTC)
            mock_dt3.combine = datetime.combine
            await ctx["client"].post(
                "/api/v1/attendance/check-out",
                json={},
                headers=staff_headers,
            )

    async def test_my_attendance_list(self, hr_context):
        """GET /attendance/me returns logged-in user's time logs."""
        ctx = hr_context
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])
        resp = await ctx["client"].get(
            "/api/v1/attendance/me",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 200
        assert "data" in resp.json()


# ---------------------------------------------------------------------------
# AC5: Excel export performance
# ---------------------------------------------------------------------------


class TestExcelExport:
    async def test_ac5_export_performance(self, hr_context):
        """AC5: Export 1 month of attendance data < 5 seconds."""
        ctx = hr_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        # Seed 10 employees and check-in/out records for a month
        from datetime import datetime, UTC, timedelta  # noqa: PLC0415

        async with ctx["factory"]() as session:
            user_ids = []
            for i in range(10):
                uid = uuid4()
                user_ids.append(uid)
                await session.execute(
                    text(
                        'INSERT INTO "user"'
                        " (id, clinic_id, username, full_name, password_hash,"
                        "  is_active, is_locked, failed_login_count, is_deleted, version,"
                        "  created_at, updated_at)"
                        " VALUES (:id, :cid, :u, :fn, 'x', TRUE, FALSE, 0, FALSE, 1,"
                        "  now(), now())"
                    ),
                    {
                        "id": str(uid),
                        "cid": str(ctx["clinic_id"]),
                        "u": f"export_user_{i}_{ctx['clinic_id'].hex[:4]}",
                        "fn": f"Export User {i}",
                    },
                )
            # Insert time logs: each user has one log per working day of April
            for uid in user_ids:
                for day in range(1, 23):  # ~22 working days
                    check_in = datetime(2026, 4, day if day <= 30 else 30, 8, 0, tzinfo=UTC)
                    check_out = datetime(2026, 4, day if day <= 30 else 30, 17, 0, tzinfo=UTC)
                    await session.execute(
                        text(
                            "INSERT INTO time_log"
                            " (id, clinic_id, user_id, check_in_at, check_out_at,"
                            "  check_in_method, total_hours, late_minutes,"
                            "  early_leave_minutes, ot_hours,"
                            "  is_deleted, version, created_at, updated_at)"
                            " VALUES (:id, :cid, :uid, :ci, :co,"
                            "  'manual', 9.0, 0, 0, 0,"
                            "  FALSE, 1, now(), now())"
                        ),
                        {
                            "id": str(uuid4()),
                            "cid": str(ctx["clinic_id"]),
                            "uid": str(uid),
                            "ci": check_in,
                            "co": check_out,
                        },
                    )
            await session.commit()

        start_time = stdlib_time.monotonic()
        resp = await ctx["client"].get(
            "/api/v1/attendance/export",
            params={"from": "2026-04-01", "to": "2026-04-30", "format": "xlsx"},
            headers=headers,
        )
        elapsed = stdlib_time.monotonic() - start_time

        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert len(resp.content) > 0
        assert elapsed < 5.0, f"Export took {elapsed:.2f}s (> 5s limit)"

        # Clean up extra users
        async with ctx["factory"]() as session:
            for uid in user_ids:
                await session.execute(
                    text("DELETE FROM time_log WHERE user_id = :uid"), {"uid": str(uid)}
                )
                await session.execute(
                    text('DELETE FROM "user" WHERE id = :uid'), {"uid": str(uid)}
                )
            await session.commit()


# ---------------------------------------------------------------------------
# Timesheet
# ---------------------------------------------------------------------------


class TestTimesheet:
    async def test_timesheet_returns_month_summary(self, hr_context):
        ctx = hr_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        resp = await ctx["client"].get(
            "/api/v1/hr/timesheet",
            params={"month": "2026-04"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["month"] == "2026-04"
        assert "entries" in body

    async def test_timesheet_invalid_month(self, hr_context):
        ctx = hr_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        resp = await ctx["client"].get(
            "/api/v1/hr/timesheet",
            params={"month": "invalid"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (400, 422, 500)
