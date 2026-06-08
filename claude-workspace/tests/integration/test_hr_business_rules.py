"""TASK-014: Business Rule Integration Tests for the HR module.

Maps SRS/BA section 12 business rules (BR-XX) to integration test scenarios.
Focuses on invariants NOT already covered by the developer-written 35 tests.
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
async def br_client():
    limiter.reset()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def br_context(br_client):
    """Seed one clinic with an admin + a staff user (no HR permissions on staff by default)."""
    clinic_id = uuid4()
    admin_id = uuid4()
    staff_id = uuid4()
    suffix = clinic_id.hex[:6].upper()
    plain_pw = "BrRuleP@ssw0rd!"

    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        session.add_all([
            Clinic(
                id=clinic_id,
                code=f"BR{suffix}",
                name=f"BR Test Clinic {suffix}",
                specialty="general",
                is_active=True,
            ),
            User(
                id=admin_id,
                clinic_id=clinic_id,
                username=f"br_admin_{suffix.lower()}",
                full_name="BR Admin",
                password_hash=hash_password(plain_pw),
                is_active=True,
                is_locked=False,
                failed_login_count=0,
            ),
            User(
                id=staff_id,
                clinic_id=clinic_id,
                username=f"br_staff_{suffix.lower()}",
                full_name="BR Staff",
                password_hash=hash_password(plain_pw),
                is_active=True,
                is_locked=False,
                failed_login_count=0,
            ),
        ])
        await session.commit()

    async with factory() as session:
        row = (
            await session.execute(
                text("SELECT id FROM role WHERE code = 'admin' AND clinic_id IS NULL")
            )
        ).fetchone()
        admin_role_id = str(row[0])
        for uid in (admin_id, staff_id):
            await session.execute(
                text(
                    "INSERT INTO user_role (id, user_id, role_id)"
                    " VALUES (:id, :uid, :rid) ON CONFLICT DO NOTHING"
                ),
                {"id": str(uuid4()), "uid": str(uid), "rid": admin_role_id},
            )
        await session.commit()

    ctx = {
        "clinic_id": clinic_id,
        "clinic_code": f"BR{suffix}",
        "admin_id": admin_id,
        "staff_id": staff_id,
        "admin_username": f"br_admin_{suffix.lower()}",
        "staff_username": f"br_staff_{suffix.lower()}",
        "plain_pw": plain_pw,
        "client": br_client,
        "factory": factory,
    }
    yield ctx

    # Teardown
    async with factory() as session:
        for table in ("time_log", "leave_request", "shift", "recurring_schedule", "shift_template"):
            await session.execute(
                text(f"DELETE FROM {table} WHERE clinic_id = :cid"),
                {"cid": str(clinic_id)},
            )
        for uid in (admin_id, staff_id):
            await session.execute(
                text("DELETE FROM user_role WHERE user_id = :uid"), {"uid": str(uid)}
            )
        await session.execute(
            text('DELETE FROM "user" WHERE clinic_id = :cid'), {"cid": str(clinic_id)}
        )
        await session.execute(
            text("DELETE FROM clinic WHERE id = :cid"), {"cid": str(clinic_id)}
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
# BR-01: shift end_time > start_time (ShiftTemplate and Shift)
# ===========================================================================


class TestBR01ShiftTimeBoundary:
    """BR-01: shift end_time must be strictly after start_time."""

    async def test_br01_patch_shift_to_inverted_times_rejected(self, br_context):
        """PATCH /shifts/{id} with start_time > existing end_time → 400/422."""
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create valid shift (09:00 - 12:00)
        tmpl_r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "BR01 Tmpl", "start_time": "09:00:00", "end_time": "12:00:00"},
            headers=headers,
        )
        tmpl_id = tmpl_r.json()["id"]

        shift_r = await ctx["client"].post(
            "/api/v1/shifts",
            json={
                "user_id": str(ctx["staff_id"]),
                "shift_template_id": tmpl_id,
                "shift_date": "2026-06-15",
                "start_time": "09:00:00",
                "end_time": "12:00:00",
            },
            headers=headers,
        )
        assert shift_r.status_code == 201
        shift_id = shift_r.json()["id"]

        # Patch start_time to 13:00 → inverts (12:00 end < 13:00 start) → reject
        resp = await ctx["client"].patch(
            f"/api/v1/shifts/{shift_id}",
            json={"start_time": "13:00:00"},
            headers=headers,
        )
        assert resp.status_code in (400, 422), (
            f"Expected 400/422 for inverted shift, got {resp.status_code}: {resp.text}"
        )

        # Verify original shift NOT mutated
        shift_resp = await ctx["client"].get(
            "/api/v1/shifts",
            params={"from": "2026-06-15", "to": "2026-06-15", "user_id": str(ctx["staff_id"])},
            headers=headers,
        )
        shifts = shift_resp.json()["data"]
        matching = [s for s in shifts if s["id"] == shift_id]
        assert len(matching) == 1
        assert matching[0]["start_time"] == "09:00:00", "Start time should not have changed"

    async def test_br01_patch_shift_template_equal_times_rejected(self, br_context):
        """PATCH /shift-templates/{id} with start_time == end_time → 400."""
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        tmpl_r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "BR01 Equal Tmpl", "start_time": "08:00:00", "end_time": "12:00:00"},
            headers=headers,
        )
        tmpl_id = tmpl_r.json()["id"]

        # Patch end_time to equal start_time
        resp = await ctx["client"].patch(
            f"/api/v1/shift-templates/{tmpl_id}",
            json={"end_time": "08:00:00"},  # equal to start
            headers=headers,
        )
        assert resp.status_code in (400, 422)


# ===========================================================================
# BR-02: leave_request end_date >= start_date
# ===========================================================================


class TestBR02LeaveDateRange:
    """BR-02: leave end_date must be >= start_date."""

    async def test_br02_same_day_leave_is_valid(self, br_context):
        """A single-day leave (start == end) is valid."""
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        resp = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "sick",
                "start_date": "2026-07-15",
                "end_date": "2026-07-15",  # same day — OK
                "reason": "Sick for a day",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["start_date"] == "2026-07-15"

    async def test_br02_end_before_start_rejected_via_schema(self, br_context):
        """leave end_date < start_date → 422 from Pydantic."""
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        resp = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "sick",
                "start_date": "2026-07-20",
                "end_date": "2026-07-10",
                "reason": "Bad range",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


# ===========================================================================
# BR-03: Rejected leave does NOT cascade to shifts
# ===========================================================================


class TestBR03RejectedLeaveNoShiftCascade:
    """BR-03: When leave is rejected, shifts remain in 'scheduled' status."""

    async def test_br03_rejected_leave_leaves_shifts_scheduled(self, br_context):
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])
        admin_headers = {"Authorization": f"Bearer {token}"}
        staff_headers = {"Authorization": f"Bearer {staff_token}"}

        # Create template + shift for staff on 2026-07-01
        tmpl_r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "BR03 Tmpl", "start_time": "08:00:00", "end_time": "12:00:00"},
            headers=admin_headers,
        )
        tmpl_id = tmpl_r.json()["id"]

        shift_r = await ctx["client"].post(
            "/api/v1/shifts",
            json={
                "user_id": str(ctx["staff_id"]),
                "shift_template_id": tmpl_id,
                "shift_date": "2026-07-01",
                "start_time": "08:00:00",
                "end_time": "12:00:00",
            },
            headers=admin_headers,
        )
        assert shift_r.status_code == 201
        shift_id = shift_r.json()["id"]

        # Staff submits leave covering 2026-07-01
        lr_r = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "personal",
                "start_date": "2026-07-01",
                "end_date": "2026-07-01",
                "reason": "Personal",
            },
            headers=staff_headers,
        )
        assert lr_r.status_code == 201
        lr_id = lr_r.json()["id"]

        # Admin REJECTS the leave
        reject_r = await ctx["client"].post(
            f"/api/v1/leave-requests/{lr_id}/reject",
            json={"rejection_reason": "Staffing shortage"},
            headers=admin_headers,
        )
        assert reject_r.status_code == 200
        assert reject_r.json()["status"] == "rejected"

        # Verify the shift is still "scheduled" (not on_leave)
        async with ctx["factory"]() as session:
            result = await session.execute(
                text("SELECT status FROM shift WHERE id = :sid"),
                {"sid": shift_id},
            )
            row = result.fetchone()
        assert row is not None
        assert row[0] == "scheduled", (
            f"Rejected leave should not affect shift status, got: {row[0]}"
        )


# ===========================================================================
# BR-04: Check-out without check-in → 404 error
# ===========================================================================


class TestBR04CheckOutWithoutCheckIn:
    """BR-04: Check-out without an active check-in returns 404."""

    async def test_br04_checkout_without_checkin_returns_404(self, br_context):
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        # Staff has no active check-in; check-out should fail
        resp = await ctx["client"].post(
            "/api/v1/attendance/check-out",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"Expected 404 for checkout without checkin, got {resp.status_code}: {resp.text}"
        )


# ===========================================================================
# BR-05: TimeLog without shift_id (manual log) is allowed
# ===========================================================================


class TestBR05ManualLogNoShift:
    """BR-05: Check-in without shift_id is valid; late_minutes should be None."""

    async def test_br05_check_in_without_shift_id(self, br_context):
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        resp = await ctx["client"].post(
            "/api/v1/attendance/check-in",
            json={"check_in_method": "manual"},  # no shift_id
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["shift_id"] is None
        # No shift → late_minutes not computable → should be None
        assert body["late_minutes"] is None, (
            f"late_minutes should be None without shift_id, got: {body['late_minutes']}"
        )

        # Cleanup
        await ctx["client"].post(
            "/api/v1/attendance/check-out",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )


# ===========================================================================
# BR-06: UNIQUE (clinic_id, user_id, shift_date, start_time) constraint
# ===========================================================================


class TestBR06ShiftUniqueness:
    """BR-06: Cannot create duplicate shift for same user/date/start_time."""

    async def test_br06_duplicate_shift_rejected_with_conflict(self, br_context):
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        tmpl_r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "BR06 Tmpl", "start_time": "10:00:00", "end_time": "14:00:00"},
            headers=headers,
        )
        tmpl_id = tmpl_r.json()["id"]

        shift_payload = {
            "user_id": str(ctx["staff_id"]),
            "shift_template_id": tmpl_id,
            "shift_date": "2026-08-01",
            "start_time": "10:00:00",
            "end_time": "14:00:00",
        }

        # First insert succeeds
        r1 = await ctx["client"].post("/api/v1/shifts", json=shift_payload, headers=headers)
        assert r1.status_code == 201

        # Second insert with same (clinic, user, date, start_time) → conflict
        r2 = await ctx["client"].post("/api/v1/shifts", json=shift_payload, headers=headers)
        assert r2.status_code == 409, (
            f"Expected 409 for duplicate shift, got {r2.status_code}: {r2.text}"
        )


# ===========================================================================
# BR-07: Self-approval of leave request via API
# ===========================================================================


class TestBR07SelfApprovalLeave:
    """BR-07: A user cannot approve their own leave request (via API call)."""

    async def test_br07_self_approval_rejected_400(self, br_context):
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        # Admin submits their own leave request
        lr_r = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "vacation",
                "start_date": "2026-08-10",
                "end_date": "2026-08-12",
                "reason": "Vacation",
            },
            headers=headers,
        )
        assert lr_r.status_code == 201
        lr_id = lr_r.json()["id"]

        # Admin tries to approve their own leave
        resp = await ctx["client"].post(
            f"/api/v1/leave-requests/{lr_id}/approve",
            headers=headers,
        )
        assert resp.status_code in (400, 403), (
            f"Expected 400/403 for self-approval, got {resp.status_code}: {resp.text}"
        )

    async def test_br07_different_approver_succeeds(self, br_context):
        """BR-07 complement: manager approves staff's leave → should succeed."""
        ctx = br_context
        admin_token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        # Staff submits leave
        lr_r = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "sick",
                "start_date": "2026-08-20",
                "end_date": "2026-08-21",
                "reason": "Illness",
            },
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert lr_r.status_code == 201
        lr_id = lr_r.json()["id"]

        # Admin (different user) approves → should succeed
        resp = await ctx["client"].post(
            f"/api/v1/leave-requests/{lr_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"


# ===========================================================================
# BR-08: Cannot approve/reject a leave that is already approved/rejected
# ===========================================================================


class TestBR08DoubleApproval:
    """BR-08: Attempting to approve/reject a non-pending leave → 400."""

    async def test_br08_cannot_approve_already_approved_leave(self, br_context):
        ctx = br_context
        admin_token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        staff_headers = {"Authorization": f"Bearer {staff_token}"}

        # Staff submits leave, admin approves
        lr_r = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "vacation",
                "start_date": "2026-09-01",
                "end_date": "2026-09-03",
                "reason": "Vacation",
            },
            headers=staff_headers,
        )
        lr_id = lr_r.json()["id"]

        await ctx["client"].post(
            f"/api/v1/leave-requests/{lr_id}/approve",
            headers=admin_headers,
        )

        # Try to approve again
        resp = await ctx["client"].post(
            f"/api/v1/leave-requests/{lr_id}/approve",
            headers=admin_headers,
        )
        assert resp.status_code in (400, 409), (
            f"Expected 400/409 for double approval, got {resp.status_code}: {resp.text}"
        )

    async def test_br08_cannot_reject_already_rejected_leave(self, br_context):
        ctx = br_context
        admin_token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        lr_r = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "personal",
                "start_date": "2026-09-10",
                "end_date": "2026-09-10",
                "reason": "Day off",
            },
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        lr_id = lr_r.json()["id"]

        await ctx["client"].post(
            f"/api/v1/leave-requests/{lr_id}/reject",
            json={"rejection_reason": "Staffing"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Try to reject again
        resp = await ctx["client"].post(
            f"/api/v1/leave-requests/{lr_id}/reject",
            json={"rejection_reason": "Again"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code in (400, 409)


# ===========================================================================
# BR-09: Check-in with shift_id from same user but soft-deleted shift → 404
# ===========================================================================


class TestBR09SoftDeletedShiftCheckin:
    """BR-09: Attempting to check-in on a soft-deleted shift returns 404."""

    async def test_br09_checkin_with_deleted_shift_404(self, br_context):
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create and delete a shift
        tmpl_r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "BR09 Tmpl", "start_time": "08:00:00", "end_time": "12:00:00"},
            headers=headers,
        )
        tmpl_id = tmpl_r.json()["id"]

        shift_r = await ctx["client"].post(
            "/api/v1/shifts",
            json={
                "user_id": str(ctx["staff_id"]),
                "shift_template_id": tmpl_id,
                "shift_date": "2026-09-20",
                "start_time": "08:00:00",
                "end_time": "12:00:00",
            },
            headers=headers,
        )
        assert shift_r.status_code == 201
        shift_id = shift_r.json()["id"]

        # Soft-delete the shift
        del_r = await ctx["client"].delete(
            f"/api/v1/shifts/{shift_id}", headers=headers
        )
        assert del_r.status_code == 204

        # Staff tries to check in using deleted shift_id
        resp = await ctx["client"].post(
            "/api/v1/attendance/check-in",
            json={"shift_id": shift_id, "check_in_method": "manual"},
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 404, (
            f"Expected 404 for deleted shift, got {resp.status_code}: {resp.text}"
        )


# ===========================================================================
# BR-10: Cross-user check-in (user attempts another user's shift_id)
# ===========================================================================


class TestBR10CrossUserCheckIn:
    """BR-10: A user cannot check in to a shift that belongs to another user (same clinic)."""

    async def test_br10_staff_cannot_checkin_admins_shift(self, br_context):
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        # Create a shift assigned to ADMIN user
        tmpl_r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "BR10 Tmpl", "start_time": "09:00:00", "end_time": "13:00:00"},
            headers=headers,
        )
        tmpl_id = tmpl_r.json()["id"]

        shift_r = await ctx["client"].post(
            "/api/v1/shifts",
            json={
                "user_id": str(ctx["admin_id"]),  # Admin's shift
                "shift_template_id": tmpl_id,
                "shift_date": "2026-10-01",
                "start_time": "09:00:00",
                "end_time": "13:00:00",
            },
            headers=headers,
        )
        assert shift_r.status_code == 201
        admin_shift_id = shift_r.json()["id"]

        # Staff attempts to check in using admin's shift_id → 403
        resp = await ctx["client"].post(
            "/api/v1/attendance/check-in",
            json={"shift_id": admin_shift_id, "check_in_method": "manual"},
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code in (403, 404), (
            f"Expected 403/404 for cross-user shift check-in, got {resp.status_code}: {resp.text}"
        )


# ===========================================================================
# BR-11: Only authenticated users can submit leave (no permission check)
# ===========================================================================


class TestBR11LeaveSubmitAuthentication:
    """BR-11: POST /leave-requests is available to any authenticated user (no special perm)."""

    async def test_br11_any_authenticated_user_can_submit_leave(self, br_context):
        ctx = br_context
        # Use staff (non-admin) token
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        resp = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "vacation",
                "start_date": "2026-10-05",
                "end_date": "2026-10-07",
                "reason": "Holiday break",
            },
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"
        # user_id should be the staff user
        assert resp.json()["user_id"] == str(ctx["staff_id"])

    async def test_br11_unauthenticated_user_cannot_submit_leave(self, br_context):
        ctx = br_context
        resp = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "sick",
                "start_date": "2026-10-10",
                "end_date": "2026-10-10",
                "reason": "Sick",
            },
        )
        assert resp.status_code in (401, 403)


# ===========================================================================
# BR-12: /attendance/me only returns current user's logs (no admin bypass)
# ===========================================================================


class TestBR12AttendanceMeIsolation:
    """BR-12: GET /attendance/me always returns only the requesting user's logs."""

    async def test_br12_attendance_me_scoped_to_self(self, br_context):
        ctx = br_context
        admin_token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        # Admin checks in
        ci_r = await ctx["client"].post(
            "/api/v1/attendance/check-in",
            json={"check_in_method": "manual"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert ci_r.status_code == 201
        admin_log_id = ci_r.json()["id"]

        # Staff calls /attendance/me — must NOT see admin's log
        resp = await ctx["client"].get(
            "/api/v1/attendance/me",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 200
        ids = [tl["id"] for tl in resp.json()["data"]]
        assert admin_log_id not in ids, (
            "Staff's /attendance/me must not include admin's time logs"
        )

        # Cleanup
        await ctx["client"].post(
            "/api/v1/attendance/check-out",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    async def test_br12_attendance_list_admin_sees_all(self, br_context):
        """GET /attendance (admin endpoint) with attendance.manage perm returns clinic-wide logs."""
        ctx = br_context
        admin_token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        # Both users check in
        ci_admin = await ctx["client"].post(
            "/api/v1/attendance/check-in",
            json={"check_in_method": "manual"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert ci_admin.status_code == 201
        admin_log_id = ci_admin.json()["id"]

        ci_staff = await ctx["client"].post(
            "/api/v1/attendance/check-in",
            json={"check_in_method": "manual"},
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert ci_staff.status_code == 201
        staff_log_id = ci_staff.json()["id"]

        # Admin calls /attendance (clinic-wide) — should see both
        resp = await ctx["client"].get(
            "/api/v1/attendance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        all_ids = [tl["id"] for tl in resp.json()["data"]]
        assert admin_log_id in all_ids, "Admin's /attendance must include own log"
        assert staff_log_id in all_ids, "Admin's /attendance must include staff log"

        # Cleanup
        for t in (admin_token, staff_token):
            await ctx["client"].post(
                "/api/v1/attendance/check-out", json={}, headers={"Authorization": f"Bearer {t}"}
            )

    async def test_br12_staff_cannot_access_attendance_admin_list(self, br_context):
        """GET /attendance (admin) is forbidden for users without attendance.manage."""
        ctx = br_context
        # Create a user WITHOUT admin role for this test
        clinic_id = ctx["clinic_id"]
        no_perm_id = uuid4()
        suffix = no_perm_id.hex[:4]
        engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
        factory = async_sessionmaker(engine, expire_on_commit=False)

        async with factory() as session:
            session.add(User(
                id=no_perm_id,
                clinic_id=clinic_id,
                username=f"noperm_{suffix}",
                full_name="No Perm User",
                password_hash=hash_password(ctx["plain_pw"]),
                is_active=True,
                is_locked=False,
                failed_login_count=0,
            ))
            await session.commit()

        try:
            # Login without any role
            login_resp = await ctx["client"].post(
                "/api/v1/auth/login",
                json={
                    "clinic_code": ctx["clinic_code"],
                    "username": f"noperm_{suffix}",
                    "password": ctx["plain_pw"],
                },
            )
            assert login_resp.status_code == 200
            no_perm_token = login_resp.json()["data"]["access_token"]

            resp = await ctx["client"].get(
                "/api/v1/attendance",
                headers={"Authorization": f"Bearer {no_perm_token}"},
            )
            assert resp.status_code in (401, 403), (
                f"Expected 403 for user without attendance.manage, got {resp.status_code}"
            )
        finally:
            async with factory() as session:
                await session.execute(
                    text('DELETE FROM "user" WHERE id = :uid'), {"uid": str(no_perm_id)}
                )
                await session.commit()
            await engine.dispose()


# ===========================================================================
# BR-13: recurring_schedule effective_to >= effective_from
# ===========================================================================


class TestBR13RecurringScheduleEffectiveRange:
    """BR-13: recurring_schedule effective_to must not precede effective_from."""

    async def test_br13_generate_shifts_respects_effective_to(self, br_context):
        """Shifts are NOT generated beyond effective_to."""
        ctx = br_context
        token = await _login(ctx["client"], ctx["clinic_code"], ctx["admin_username"], ctx["plain_pw"])
        headers = {"Authorization": f"Bearer {token}"}

        tmpl_r = await ctx["client"].post(
            "/api/v1/shift-templates",
            json={"name": "BR13 Tmpl", "start_time": "08:00:00", "end_time": "12:00:00"},
            headers=headers,
        )
        tmpl_id = tmpl_r.json()["id"]

        # Recurring schedule effective only for 2026-07-01 to 2026-07-05
        rs_r = await ctx["client"].post(
            "/api/v1/recurring-schedules",
            json={
                "user_id": str(ctx["staff_id"]),
                "shift_template_id": tmpl_id,
                "days_of_week": [1, 2, 3, 4, 5],  # Weekdays
                "effective_from": "2026-07-01",
                "effective_to": "2026-07-05",  # ends July 5
            },
            headers=headers,
        )
        assert rs_r.status_code == 201
        schedule_id = rs_r.json()["id"]

        # Generate up to July 31 — but effective_to = July 5 limits generation
        gen_r = await ctx["client"].post(
            f"/api/v1/recurring-schedules/{schedule_id}/generate-shifts?until=2026-07-31",
            headers=headers,
        )
        assert gen_r.status_code == 200

        # Fetch resulting shifts for user
        shifts_r = await ctx["client"].get(
            "/api/v1/shifts",
            params={
                "user_id": str(ctx["staff_id"]),
                "from": "2026-07-01",
                "to": "2026-07-31",
            },
            headers=headers,
        )
        assert shifts_r.status_code == 200
        shifts = shifts_r.json()["data"]

        # All generated shifts must be on or before July 5
        for s in shifts:
            shift_date = date.fromisoformat(s["shift_date"])
            assert shift_date <= date(2026, 7, 5), (
                f"Shift on {shift_date} exceeds effective_to 2026-07-05"
            )


# ===========================================================================
# BR-14: Leave-request missing required "reason" field → 422
# ===========================================================================


class TestBR14LeaveReasonRequired:
    """BR-14: reason is a required field on leave request creation."""

    async def test_br14_leave_request_without_reason_422(self, br_context):
        ctx = br_context
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        resp = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "sick",
                "start_date": "2026-11-01",
                "end_date": "2026-11-02",
                # reason omitted
            },
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 422

    async def test_br14_leave_request_empty_reason_422(self, br_context):
        ctx = br_context
        staff_token = await _login(ctx["client"], ctx["clinic_code"], ctx["staff_username"], ctx["plain_pw"])

        resp = await ctx["client"].post(
            "/api/v1/leave-requests",
            json={
                "leave_type": "sick",
                "start_date": "2026-11-01",
                "end_date": "2026-11-02",
                "reason": "",  # empty string (min_length=1)
            },
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 422
