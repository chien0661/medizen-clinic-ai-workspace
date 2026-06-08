"""Unit tests for clinic settings Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.admin.schemas.settings_schemas import (
    AppointmentSettings,
    BillingSettings,
    DayHours,
    InventorySettings,
    OperatingHoursSettings,
    PrescriptionSettings,
    QueueSettings,
    SpecialtySettings,
)


class TestDayHours:
    def test_valid_hours(self):
        d = DayHours(is_open=True, open="08:00", close="17:00")
        assert d.is_open is True

    def test_close_must_be_after_open(self):
        with pytest.raises(ValidationError, match="close time"):
            DayHours(is_open=True, open="17:00", close="08:00")

    def test_equal_times_invalid(self):
        with pytest.raises(ValidationError):
            DayHours(is_open=True, open="08:00", close="08:00")

    def test_closed_day_ignores_time_constraint(self):
        # When is_open=False the times are stored but not validated for order
        d = DayHours(is_open=False, open="08:00", close="12:00")
        assert d.is_open is False

    def test_invalid_time_format(self):
        with pytest.raises(ValidationError):
            DayHours(is_open=True, open="8:00", close="17:00")  # no leading zero


class TestOperatingHoursSettings:
    def test_defaults(self):
        h = OperatingHoursSettings()
        assert h.mon.is_open is True
        assert h.sat.is_open is False
        assert h.sun.is_open is False


class TestAppointmentSettings:
    def test_defaults(self):
        a = AppointmentSettings()
        assert a.slot_duration_minutes == 30

    def test_custom_duration(self):
        a = AppointmentSettings(slot_duration_minutes=20)
        assert a.slot_duration_minutes == 20

    def test_duration_below_min(self):
        with pytest.raises(ValidationError):
            AppointmentSettings(slot_duration_minutes=1)

    def test_duration_above_max(self):
        with pytest.raises(ValidationError):
            AppointmentSettings(slot_duration_minutes=500)

    def test_negative_deposit(self):
        with pytest.raises(ValidationError):
            AppointmentSettings(deposit_amount=-1)


class TestQueueSettings:
    def test_defaults(self):
        q = QueueSettings()
        assert q.algorithm == "fifo"

    def test_invalid_algorithm(self):
        with pytest.raises(ValidationError):
            QueueSettings(algorithm="random")


class TestInventorySettings:
    def test_threshold_out_of_range(self):
        with pytest.raises(ValidationError):
            InventorySettings(low_stock_threshold_percent=110)


class TestPrescriptionSettings:
    def test_defaults(self):
        p = PrescriptionSettings()
        assert p.max_days_supply == 30


class TestBillingSettings:
    def test_defaults(self):
        b = BillingSettings()
        assert b.currency == "VND"
        assert b.tax_rate_percent == 0.0

    def test_negative_tax_rate(self):
        with pytest.raises(ValidationError):
            BillingSettings(tax_rate_percent=-1.0)


class TestSpecialtySettings:
    def test_general_vital_fields_populated(self):
        s = SpecialtySettings(code="general")
        assert "bp_systolic" in s.vital_fields
        assert len(s.vital_fields) == 7

    def test_pediatric_has_head_circumference(self):
        s = SpecialtySettings(code="pediatric")
        assert "head_circumference" in s.vital_fields
        assert len(s.vital_fields) == 8

    def test_invalid_specialty(self):
        with pytest.raises(ValidationError):
            SpecialtySettings(code="unknown")

    def test_custom_vital_fields_preserved(self):
        s = SpecialtySettings(code="general", vital_fields=["pulse"])
        assert s.vital_fields == ["pulse"]
