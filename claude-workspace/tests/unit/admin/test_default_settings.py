"""Unit tests for default_settings module."""

from __future__ import annotations

import pytest

from app.modules.admin.services.default_settings import (
    SPECIALTY_VITAL_FIELDS,
    get_default_settings,
)


class TestGetDefaultSettings:
    def test_general_returns_all_groups(self):
        s = get_default_settings("general")
        required_groups = {
            "operating_hours",
            "appointment",
            "queue",
            "inventory",
            "prescription",
            "billing",
            "specialty",
        }
        assert required_groups <= s.keys()

    def test_general_vital_fields_count(self):
        s = get_default_settings("general")
        assert len(s["specialty"]["vital_fields"]) == 7

    def test_pediatric_has_head_circumference(self):
        s = get_default_settings("pediatric")
        assert "head_circumference" in s["specialty"]["vital_fields"]
        assert len(s["specialty"]["vital_fields"]) == 8

    def test_specialty_code_stored(self):
        s = get_default_settings("dental")
        assert s["specialty"]["code"] == "dental"

    def test_unknown_specialty_falls_back_to_general(self):
        s = get_default_settings("unknown")
        # Should use general vital fields as fallback
        assert s["specialty"]["vital_fields"] == SPECIALTY_VITAL_FIELDS["general"]

    def test_appointment_defaults(self):
        s = get_default_settings()
        assert s["appointment"]["slot_duration_minutes"] == 30
        assert s["appointment"]["allow_walk_in"] is True

    def test_operating_hours_weekdays_open(self):
        s = get_default_settings()
        for day in ("mon", "tue", "wed", "thu", "fri"):
            assert s["operating_hours"][day]["is_open"] is True

    def test_operating_hours_weekend_closed(self):
        s = get_default_settings()
        assert s["operating_hours"]["sat"]["is_open"] is False
        assert s["operating_hours"]["sun"]["is_open"] is False
