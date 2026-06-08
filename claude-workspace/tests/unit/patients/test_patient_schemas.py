"""Unit tests for patient Pydantic schemas.

Covers validation rules:
- PhoneValidator: valid VN phone, invalid format → 422
- DOB / birth_year check constraint replication in schema
- PatientCreate: happy path with only birth_year, only date_of_birth, both matching,
                 mismatch year → ValueError, neither provided → ValueError
- PatientUpdate: optional phone validation
- PatientSearchQuery: type enum validation
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.modules.patients.schemas.patient_schemas import (
    PatientCreate,
    PatientRelationCreate,
    PatientSearchQuery,
    PatientUpdate,
)


class TestPatientCreateValidation:
    def test_valid_birth_year_only(self):
        p = PatientCreate(full_name="Test", gender="male", birth_year=1990)
        assert p.birth_year == 1990
        assert p.date_of_birth is None

    def test_valid_dob_only(self):
        p = PatientCreate(full_name="Test", gender="female", date_of_birth=date(1990, 5, 20))
        assert p.date_of_birth == date(1990, 5, 20)

    def test_valid_both_matching(self):
        p = PatientCreate(
            full_name="Test",
            gender="male",
            date_of_birth=date(1990, 5, 20),
            birth_year=1990,
        )
        assert p.birth_year == 1990

    def test_mismatch_year_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            PatientCreate(
                full_name="Test",
                gender="male",
                date_of_birth=date(1990, 5, 20),
                birth_year=1991,
            )
        assert "birth_year" in str(exc_info.value) or "1990" in str(exc_info.value)

    def test_neither_dob_nor_birth_year_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            PatientCreate(full_name="Test", gender="male")
        assert "birth_year" in str(exc_info.value) or "date_of_birth" in str(exc_info.value)

    def test_valid_phone_10_digits(self):
        p = PatientCreate(full_name="Test", gender="male", birth_year=1990, phone="0912345678")
        assert p.phone == "0912345678"

    def test_invalid_phone_raises(self):
        with pytest.raises(ValidationError):
            PatientCreate(full_name="Test", gender="male", birth_year=1990, phone="912345678")

    def test_invalid_phone_11_digits_raises(self):
        with pytest.raises(ValidationError):
            PatientCreate(full_name="Test", gender="male", birth_year=1990, phone="09123456789")

    def test_invalid_gender_raises(self):
        with pytest.raises(ValidationError):
            PatientCreate(full_name="Test", gender="unknown", birth_year=1990)

    def test_null_phone_is_valid(self):
        p = PatientCreate(full_name="Test", gender="male", birth_year=1990, phone=None)
        assert p.phone is None


class TestPatientUpdateValidation:
    def test_valid_phone_update(self):
        u = PatientUpdate(phone="0987654321")
        assert u.phone == "0987654321"

    def test_invalid_phone_update_raises(self):
        with pytest.raises(ValidationError):
            PatientUpdate(phone="123")

    def test_all_fields_optional(self):
        u = PatientUpdate()
        assert u.full_name is None


class TestPatientSearchQuery:
    def test_valid_type_phone(self):
        q = PatientSearchQuery(q="0912", type="phone")
        assert q.type == "phone"

    def test_valid_type_name(self):
        q = PatientSearchQuery(q="nguyen", type="name")
        assert q.type == "name"

    def test_valid_type_code(self):
        q = PatientSearchQuery(q="BN0001", type="code")
        assert q.type == "code"

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            PatientSearchQuery(q="x", type="email")

    def test_empty_q_raises(self):
        with pytest.raises(ValidationError):
            PatientSearchQuery(q="")


class TestPatientRelationCreate:
    def test_valid_relation_type(self):
        from uuid import uuid4
        r = PatientRelationCreate(guardian_patient_id=uuid4(), relation_type="parent")
        assert r.relation_type == "parent"

    def test_invalid_relation_type_raises(self):
        from uuid import uuid4
        with pytest.raises(ValidationError):
            PatientRelationCreate(guardian_patient_id=uuid4(), relation_type="boss")
