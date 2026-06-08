"""Unit tests for onboarding wizard Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.admin.schemas.onboarding_schemas import (
    OnboardingInfoRequest,
    OnboardingServiceEntry,
    OnboardingShiftEntry,
    OnboardingStartRequest,
    OnboardingUserEntry,
)


class TestOnboardingStartRequest:
    def test_valid_specialty(self):
        r = OnboardingStartRequest(specialty="general")
        assert r.specialty == "general"

    def test_invalid_specialty(self):
        with pytest.raises(ValidationError):
            OnboardingStartRequest(specialty="surgery")

    @pytest.mark.parametrize(
        "specialty",
        ["general", "pediatric", "ob_gyn", "dermatology", "dental"],
    )
    def test_all_valid_specialties(self, specialty):
        r = OnboardingStartRequest(specialty=specialty)
        assert r.specialty == specialty


class TestOnboardingInfoRequest:
    def test_valid(self):
        r = OnboardingInfoRequest(name="Test Clinic", phone="0123456789")
        assert r.name == "Test Clinic"

    def test_name_too_short(self):
        with pytest.raises(ValidationError):
            OnboardingInfoRequest(name="A")


class TestOnboardingUserEntry:
    def test_valid_user(self):
        u = OnboardingUserEntry(
            username="drsmith",
            full_name="Dr Smith",
            password="securepass",
        )
        assert u.username == "drsmith"

    def test_short_password(self):
        with pytest.raises(ValidationError):
            OnboardingUserEntry(username="u", full_name="Name", password="short")

    def test_short_username(self):
        with pytest.raises(ValidationError):
            OnboardingUserEntry(username="ab", full_name="Name", password="validpass")


class TestOnboardingShiftEntry:
    def test_valid_shift(self):
        s = OnboardingShiftEntry(name="Morning", start_time="08:00", end_time="12:00")
        assert s.name == "Morning"

    def test_end_before_start_invalid(self):
        with pytest.raises(ValidationError):
            OnboardingShiftEntry(name="Bad", start_time="12:00", end_time="08:00")

    def test_equal_times_invalid(self):
        with pytest.raises(ValidationError):
            OnboardingShiftEntry(name="Bad", start_time="08:00", end_time="08:00")

    def test_invalid_time_format(self):
        with pytest.raises(ValidationError):
            OnboardingShiftEntry(name="Bad", start_time="8:00", end_time="17:00")


class TestOnboardingServiceEntry:
    def test_valid(self):
        s = OnboardingServiceEntry(name="Consultation", code="CONS", price=150_000)
        assert s.price == 150_000

    def test_negative_price(self):
        with pytest.raises(ValidationError):
            OnboardingServiceEntry(name="Svc", code="SVC", price=-100)
