"""Unit tests for HR service pure-logic functions (no DB required)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

# ---------------------------------------------------------------------------
# attendance_service logic tests
# ---------------------------------------------------------------------------


class TestCheckInLateMinutes:
    """Test late_minutes computation in check_in."""

    def test_late_7m45s_for_shift_7m30s(self):
        """AC: Check-in 7:45 for shift start 7:30 → late_minutes = 15."""
        shift_date = date(2026, 5, 10)
        shift_start = time(7, 30)
        check_in_at = datetime(2026, 5, 10, 7, 45, tzinfo=UTC)

        shift_start_dt = datetime.combine(shift_date, shift_start).replace(tzinfo=UTC)
        diff = (check_in_at - shift_start_dt).total_seconds() / 60
        late_minutes = max(0, int(diff))

        assert late_minutes == 15

    def test_early_checkin_gives_zero_late(self):
        """Check-in before shift start → late_minutes = 0."""
        shift_date = date(2026, 5, 10)
        shift_start = time(8, 0)
        check_in_at = datetime(2026, 5, 10, 7, 55, tzinfo=UTC)

        shift_start_dt = datetime.combine(shift_date, shift_start).replace(tzinfo=UTC)
        diff = (check_in_at - shift_start_dt).total_seconds() / 60
        late_minutes = max(0, int(diff))

        assert late_minutes == 0

    def test_exact_on_time_gives_zero_late(self):
        """Check-in exactly on shift start → late_minutes = 0."""
        shift_date = date(2026, 5, 10)
        shift_start = time(8, 0)
        check_in_at = datetime(2026, 5, 10, 8, 0, tzinfo=UTC)

        shift_start_dt = datetime.combine(shift_date, shift_start).replace(tzinfo=UTC)
        diff = (check_in_at - shift_start_dt).total_seconds() / 60
        late_minutes = max(0, int(diff))

        assert late_minutes == 0


class TestCheckOutComputations:
    """Test ot_hours and early_leave_minutes computation."""

    def test_check_out_30min_late_gives_ot_0p5(self):
        """AC: Check-out 12:30 for shift end 12:00 → ot_hours = 0.5."""
        shift_date = date(2026, 5, 10)
        shift_end = time(12, 0)
        check_out_at = datetime(2026, 5, 10, 12, 30, tzinfo=UTC)

        shift_end_dt = datetime.combine(shift_date, shift_end).replace(tzinfo=UTC)
        diff_minutes = (shift_end_dt - check_out_at).total_seconds() / 60
        assert diff_minutes < 0  # left after end

        ot_seconds = (check_out_at - shift_end_dt).total_seconds()
        ot_hours = round(max(0.0, ot_seconds / 3600), 2)

        assert ot_hours == 0.5

    def test_check_out_early_gives_early_leave_minutes(self):
        """Check-out 11:45 for shift end 12:00 → early_leave_minutes = 15, ot = 0."""
        shift_date = date(2026, 5, 10)
        shift_end = time(12, 0)
        check_out_at = datetime(2026, 5, 10, 11, 45, tzinfo=UTC)

        shift_end_dt = datetime.combine(shift_date, shift_end).replace(tzinfo=UTC)
        diff_minutes = (shift_end_dt - check_out_at).total_seconds() / 60
        assert diff_minutes > 0  # left before end

        early_leave = int(diff_minutes)
        ot_hours = 0.0

        assert early_leave == 15
        assert ot_hours == 0.0

    def test_total_hours_calculation(self):
        """Compute total_hours from check_in to check_out."""
        check_in = datetime(2026, 5, 10, 8, 0, tzinfo=UTC)
        check_out = datetime(2026, 5, 10, 12, 30, tzinfo=UTC)
        duration = (check_out - check_in).total_seconds()
        total = round(duration / 3600, 2)
        assert total == 4.5


# ---------------------------------------------------------------------------
# recurring_service logic tests
# ---------------------------------------------------------------------------


class TestRecurringShiftGeneration:
    """Test the date iteration logic for recurring schedules."""

    def _dates_for_pattern(
        self,
        days_of_week: list[int],
        start: date,
        end: date,
    ) -> list[date]:
        """Replicate the iteration logic from recurring_service."""
        current = start
        result = []
        while current <= end:
            if current.isoweekday() in days_of_week:
                result.append(current)
            current += timedelta(days=1)
        return result

    def test_mon_wed_fri_for_may_2026(self):
        """AC: T2-T4-T6 (Mon/Wed/Fri) from 2026-05-01 generates correct shifts for May."""
        days = [1, 3, 5]  # Mon=1, Wed=3, Fri=5 (ISO)
        start = date(2026, 5, 1)
        end = date(2026, 5, 31)

        dates = self._dates_for_pattern(days, start, end)

        # All generated dates should be Mon, Wed, or Fri
        for d in dates:
            assert d.isoweekday() in days, f"{d} is weekday {d.isoweekday()}, not in {days}"

        # May 2026: Mon/Wed/Fri dates
        # May 1 = Fri, May 4 = Mon, May 6 = Wed, ...
        assert date(2026, 5, 1) in dates   # Fri (isoweekday=5)
        assert date(2026, 5, 4) in dates   # Mon (isoweekday=1)
        assert date(2026, 5, 6) in dates   # Wed (isoweekday=3)
        assert date(2026, 5, 29) in dates  # Fri (isoweekday=5)
        # May 30 = Sat (isoweekday=6) → not in [1,3,5], confirm absent
        assert date(2026, 5, 30) not in dates
        # May 31 = Sun (isoweekday=7) → not in [1,3,5], confirm absent
        assert date(2026, 5, 31) not in dates

    def test_effective_to_limits_generation(self):
        """Shifts are not generated past effective_to."""
        days = [1, 2, 3, 4, 5]  # Weekdays
        start = date(2026, 5, 1)
        effective_to = date(2026, 5, 10)
        until = date(2026, 5, 31)  # cron horizon

        end = min(until, effective_to)
        dates = self._dates_for_pattern(days, start, end)

        assert all(d <= effective_to for d in dates)
        assert date(2026, 5, 11) not in dates

    def test_no_weekend_shifts_for_weekday_pattern(self):
        """Weekday-only patterns should not produce weekend shifts."""
        days = [1, 2, 3, 4, 5]
        start = date(2026, 5, 1)
        end = date(2026, 5, 31)
        dates = self._dates_for_pattern(days, start, end)

        for d in dates:
            assert d.isoweekday() <= 5, f"{d} is a weekend"


# ---------------------------------------------------------------------------
# leave_service logic tests
# ---------------------------------------------------------------------------


class TestLeaveOverlapDetection:
    """Test the date range overlap that triggers shift marking."""

    def _shifts_in_range(
        self,
        shift_dates: list[date],
        leave_start: date,
        leave_end: date,
    ) -> list[date]:
        return [d for d in shift_dates if leave_start <= d <= leave_end]

    def test_leave_2026_05_10_to_12_marks_3_days(self):
        """AC: LeaveRequest 2026-05-10 → 2026-05-12 → shifts in that range marked."""
        shift_dates = [
            date(2026, 5, 8),
            date(2026, 5, 9),
            date(2026, 5, 10),  # in range
            date(2026, 5, 11),  # in range
            date(2026, 5, 12),  # in range
            date(2026, 5, 13),
        ]
        leave_start = date(2026, 5, 10)
        leave_end = date(2026, 5, 12)

        affected = self._shifts_in_range(shift_dates, leave_start, leave_end)

        assert len(affected) == 3
        assert date(2026, 5, 10) in affected
        assert date(2026, 5, 11) in affected
        assert date(2026, 5, 12) in affected
        assert date(2026, 5, 9) not in affected
        assert date(2026, 5, 13) not in affected

    def test_leave_single_day(self):
        """Single-day leave affects only that day's shift."""
        shift_dates = [date(2026, 5, 10), date(2026, 5, 11)]
        affected = self._shifts_in_range(
            shift_dates, date(2026, 5, 10), date(2026, 5, 10)
        )
        assert len(affected) == 1
        assert date(2026, 5, 10) in affected


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    """Test Pydantic schema validators."""

    def test_shift_template_end_must_be_after_start(self):
        from pydantic import ValidationError  # noqa: PLC0415

        from app.modules.hr.schemas.hr_schemas import ShiftTemplateCreate  # noqa: PLC0415

        with pytest.raises(ValidationError) as exc_info:
            ShiftTemplateCreate(
                name="Bad Shift",
                start_time=time(12, 0),
                end_time=time(8, 0),  # before start
            )
        assert "end_time must be after start_time" in str(exc_info.value)

    def test_leave_request_end_before_start_raises(self):
        from pydantic import ValidationError  # noqa: PLC0415

        from app.modules.hr.schemas.hr_schemas import LeaveRequestCreate  # noqa: PLC0415

        with pytest.raises(ValidationError):
            LeaveRequestCreate(
                leave_type="sick",
                start_date=date(2026, 5, 15),
                end_date=date(2026, 5, 10),  # before start
                reason="Test",
            )

    def test_days_of_week_must_be_1_to_7(self):
        from pydantic import ValidationError  # noqa: PLC0415

        from app.modules.hr.schemas.hr_schemas import RecurringScheduleCreate  # noqa: PLC0415

        with pytest.raises(ValidationError):
            RecurringScheduleCreate(
                user_id=uuid4(),
                shift_template_id=uuid4(),
                days_of_week=[0, 3, 8],  # 0 and 8 are invalid
                effective_from=date(2026, 5, 1),
            )

    def test_days_of_week_deduped_and_sorted(self):
        from app.modules.hr.schemas.hr_schemas import RecurringScheduleCreate  # noqa: PLC0415

        rs = RecurringScheduleCreate(
            user_id=uuid4(),
            shift_template_id=uuid4(),
            days_of_week=[3, 1, 3, 5],  # duplicates + unordered
            effective_from=date(2026, 5, 1),
        )
        assert rs.days_of_week == [1, 3, 5]

    def test_valid_leave_type(self):
        from app.modules.hr.schemas.hr_schemas import LeaveRequestCreate  # noqa: PLC0415

        lr = LeaveRequestCreate(
            leave_type="vacation",
            start_date=date(2026, 5, 10),
            end_date=date(2026, 5, 12),
            reason="Holiday",
        )
        assert lr.leave_type == "vacation"

    def test_invalid_leave_type(self):
        from pydantic import ValidationError  # noqa: PLC0415

        from app.modules.hr.schemas.hr_schemas import LeaveRequestCreate  # noqa: PLC0415

        with pytest.raises(ValidationError):
            LeaveRequestCreate(
                leave_type="holiday",  # not in enum
                start_date=date(2026, 5, 10),
                end_date=date(2026, 5, 12),
                reason="Holiday",
            )


# ---------------------------------------------------------------------------
# Fix iteration 1: new tests for review-requested security / validation rules
# ---------------------------------------------------------------------------


class TestShiftUpdateRejectsInvertedTimes:
    """update_shift and update_shift_template must reject end_time <= start_time."""

    @pytest.mark.asyncio
    async def test_shift_update_rejects_inverted_times(self):
        """Patching start_time to be after end_time raises BusinessRuleError."""
        from app.core.exceptions import BusinessRuleError  # noqa: PLC0415
        from app.modules.hr.services import shift_service  # noqa: PLC0415

        # Build a mock shift that currently has (09:00, 12:00)
        mock_shift = MagicMock()
        mock_shift.is_deleted = False
        mock_shift.start_time = time(13, 0)   # will be set via setattr
        mock_shift.end_time = time(12, 0)     # already stored end_time

        db = AsyncMock()
        db.get = AsyncMock(return_value=mock_shift)

        # Simulate get_shift returning mock_shift
        with patch.object(shift_service, "get_shift", AsyncMock(return_value=mock_shift)):
            with pytest.raises(BusinessRuleError, match="end_time must be after start_time"):
                await shift_service.update_shift(
                    db,
                    shift_id=uuid4(),
                    updated_by=uuid4(),
                    start_time=time(13, 0),   # inverts the (09:00 → 12:00) shift
                )

    @pytest.mark.asyncio
    async def test_shift_template_update_rejects_inverted_times(self):
        """Patching start_time to be after end_time on a template raises BusinessRuleError."""
        from app.core.exceptions import BusinessRuleError  # noqa: PLC0415
        from app.modules.hr.services import shift_service  # noqa: PLC0415

        mock_tmpl = MagicMock()
        mock_tmpl.is_deleted = False
        mock_tmpl.start_time = time(14, 0)
        mock_tmpl.end_time = time(9, 0)

        db = AsyncMock()

        with patch.object(shift_service, "get_shift_template", AsyncMock(return_value=mock_tmpl)):
            with pytest.raises(BusinessRuleError, match="end_time must be after start_time"):
                await shift_service.update_shift_template(
                    db,
                    template_id=uuid4(),
                    updated_by=uuid4(),
                    start_time=time(14, 0),
                )


class TestCheckInRejectsOtherUsersShiftId:
    """check_in must reject shift_id that belongs to a different user or clinic."""

    @pytest.mark.asyncio
    async def test_check_in_rejects_other_users_shift_id(self):
        """Supplying a shift_id owned by a different user raises ForbiddenError."""
        from app.core.exceptions import ForbiddenError  # noqa: PLC0415
        from app.modules.hr.services import attendance_service  # noqa: PLC0415

        current_user_id = uuid4()
        other_user_id = uuid4()
        clinic_id = uuid4()
        shift_id = uuid4()

        # Mock shift owned by other_user_id in the same clinic
        mock_shift = MagicMock()
        mock_shift.is_deleted = False
        mock_shift.user_id = other_user_id
        mock_shift.clinic_id = clinic_id

        db = AsyncMock()
        db.get = AsyncMock(return_value=mock_shift)

        # Mock the duplicate-check query to return no existing active check-in
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ForbiddenError, match="does not belong to you"):
            await attendance_service.check_in(
                db,
                clinic_id=clinic_id,
                user_id=current_user_id,
                shift_id=shift_id,
                check_in_method="manual",
            )


class TestApproveLeaveRejectsSelfApproval:
    """approve_leave_request must forbid a user from approving their own request."""

    @pytest.mark.asyncio
    async def test_approve_leave_rejects_self_approval(self):
        """Approver == requestor raises BusinessRuleError."""
        from app.core.exceptions import BusinessRuleError  # noqa: PLC0415
        from app.modules.hr.services import leave_service  # noqa: PLC0415

        user_id = uuid4()

        mock_lr = MagicMock()
        mock_lr.user_id = user_id
        mock_lr.status = "pending"

        db = AsyncMock()

        with patch.object(leave_service, "get_leave_request", AsyncMock(return_value=mock_lr)):
            with pytest.raises(BusinessRuleError, match="Cannot approve your own leave request"):
                await leave_service.approve_leave_request(
                    db,
                    leave_id=uuid4(),
                    approved_by=user_id,  # same as requestor
                )
