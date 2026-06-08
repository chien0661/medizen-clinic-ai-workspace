"""Unit tests for patient_service.py.

Covers:
- generate_patient_code: first patient → BN0001, nth patient increments
- create_patient: happy path, duplicate name+DOB warning, no warning when different DOB
- get_patient: found, not found, deleted
- update_patient: field updates, not found
- soft_delete_patient: sets is_deleted, not found
- list_patients: returns paginated results
- search_patients: phone, name (ts_query + trigram), code
- audit_patient_read: calls write_audit
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.modules.patients.services import patient_service

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_patient(
    *,
    patient_id=None,
    clinic_id=None,
    full_name="Nguyen Van An",
    date_of_birth=None,
    birth_year=1990,
    gender="male",
    phone="0912345678",
    patient_code="BN0001",
    is_deleted=False,
):
    p = MagicMock()
    p.id = patient_id or uuid4()
    p.clinic_id = clinic_id or uuid4()
    p.full_name = full_name
    p.date_of_birth = date_of_birth
    p.birth_year = birth_year
    p.gender = gender
    p.phone = phone
    p.patient_code = patient_code
    p.is_deleted = is_deleted
    return p


def _make_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# generate_patient_code
# ---------------------------------------------------------------------------


class TestGeneratePatientCode:
    async def test_first_patient_returns_bn0001(self):
        db = _make_db()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one=MagicMock(return_value="BN0001")))
        code = await patient_service.generate_patient_code(db, uuid4())
        assert code == "BN0001"

    async def test_nth_patient_increments(self):
        db = _make_db()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one=MagicMock(return_value="BN0042")))
        code = await patient_service.generate_patient_code(db, uuid4())
        assert code == "BN0042"


# ---------------------------------------------------------------------------
# create_patient
# ---------------------------------------------------------------------------


class TestCreatePatient:
    async def test_happy_path_no_warnings(self):
        clinic_id = uuid4()
        db = _make_db()

        # No duplicate found
        no_dup = MagicMock()
        no_dup.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))

        # fn_next_patient_code returns BN0001
        code_result = MagicMock(scalar_one=MagicMock(return_value="BN0001"))

        db.execute = AsyncMock(side_effect=[no_dup, code_result])

        patient, warnings = await patient_service.create_patient(
            db,
            clinic_id=clinic_id,
            full_name="Test Patient",
            gender="male",
            birth_year=1990,
        )
        assert warnings == []
        db.flush.assert_called_once()

    async def test_duplicate_name_dob_raises_warning(self):
        clinic_id = uuid4()
        db = _make_db()

        existing = MagicMock()
        existing_result = MagicMock()
        existing_result.scalars = MagicMock(
            return_value=MagicMock(first=MagicMock(return_value=existing))
        )

        code_result = MagicMock(scalar_one=MagicMock(return_value="BN0002"))
        db.execute = AsyncMock(side_effect=[existing_result, code_result])

        patient, warnings = await patient_service.create_patient(
            db,
            clinic_id=clinic_id,
            full_name="Duplicate Name",
            gender="female",
            date_of_birth=date(1990, 1, 1),
            birth_year=1990,
        )
        assert len(warnings) == 1
        assert "duplicate" in warnings[0].lower()

    async def test_no_dob_no_warning(self):
        """Without date_of_birth, no duplicate check runs → no warnings."""
        clinic_id = uuid4()
        db = _make_db()
        code_result = MagicMock(scalar_one=MagicMock(return_value="BN0003"))
        db.execute = AsyncMock(return_value=code_result)

        patient, warnings = await patient_service.create_patient(
            db,
            clinic_id=clinic_id,
            full_name="No DOB Patient",
            gender="other",
            birth_year=2000,
        )
        assert warnings == []


# ---------------------------------------------------------------------------
# get_patient
# ---------------------------------------------------------------------------


class TestGetPatient:
    async def test_returns_patient_when_found(self):
        db = _make_db()
        p = _make_patient()
        db.get = AsyncMock(return_value=p)
        result = await patient_service.get_patient(db, p.id)
        assert result is p

    async def test_raises_not_found_when_none(self):
        db = _make_db()
        db.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await patient_service.get_patient(db, uuid4())

    async def test_raises_not_found_when_deleted(self):
        db = _make_db()
        p = _make_patient(is_deleted=True)
        db.get = AsyncMock(return_value=p)
        with pytest.raises(NotFoundError):
            await patient_service.get_patient(db, p.id)


# ---------------------------------------------------------------------------
# update_patient
# ---------------------------------------------------------------------------


class TestUpdatePatient:
    async def test_updates_full_name(self):
        db = _make_db()
        p = _make_patient()
        db.get = AsyncMock(return_value=p)
        user_id = uuid4()

        await patient_service.update_patient(
            db, p.id, updated_by=user_id, full_name="Updated Name"
        )
        assert p.full_name == "Updated Name"
        assert p.updated_by == user_id
        db.flush.assert_called_once()

    async def test_raises_not_found(self):
        db = _make_db()
        db.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await patient_service.update_patient(db, uuid4(), full_name="x")


# ---------------------------------------------------------------------------
# soft_delete_patient
# ---------------------------------------------------------------------------


class TestSoftDeletePatient:
    async def test_sets_is_deleted(self):
        db = _make_db()
        p = _make_patient()
        db.get = AsyncMock(return_value=p)
        user_id = uuid4()

        await patient_service.soft_delete_patient(db, p.id, deleted_by=user_id)
        assert p.is_deleted is True
        assert p.deleted_by == user_id

    async def test_raises_not_found(self):
        db = _make_db()
        db.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await patient_service.soft_delete_patient(db, uuid4())


# ---------------------------------------------------------------------------
# list_patients
# ---------------------------------------------------------------------------


class TestListPatients:
    async def test_returns_list_and_total(self):
        db = _make_db()
        clinic_id = uuid4()
        patients = [_make_patient(clinic_id=clinic_id) for _ in range(3)]

        count_result = MagicMock(scalar_one=MagicMock(return_value=3))
        list_result = MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=patients))))

        db.execute = AsyncMock(side_effect=[count_result, list_result])

        result_patients, total = await patient_service.list_patients(db, clinic_id)
        assert total == 3
        assert len(result_patients) == 3


# ---------------------------------------------------------------------------
# search_patients
# ---------------------------------------------------------------------------


class TestSearchPatients:
    async def test_search_by_phone(self):
        db = _make_db()
        clinic_id = uuid4()
        patients = [_make_patient()]
        result = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=patients)))
        )
        db.execute = AsyncMock(return_value=result)

        found = await patient_service.search_patients(db, clinic_id, q="0912345678", search_type="phone")
        assert len(found) == 1

    async def test_search_by_code(self):
        db = _make_db()
        clinic_id = uuid4()
        patients = [_make_patient(patient_code="BN0042")]
        result = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=patients)))
        )
        db.execute = AsyncMock(return_value=result)

        found = await patient_service.search_patients(db, clinic_id, q="BN0042", search_type="code")
        assert len(found) == 1

    async def test_search_by_name_combines_ts_and_trgm(self):
        db = _make_db()
        clinic_id = uuid4()

        p1 = _make_patient(patient_id=uuid4())
        p2 = _make_patient(patient_id=uuid4())  # different id

        ts_result = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[p1])))
        )
        trgm_result = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[p1, p2])))
        )
        db.execute = AsyncMock(side_effect=[ts_result, trgm_result])

        found = await patient_service.search_patients(
            db, clinic_id, q="nguyen van an", search_type="name"
        )
        # p1 from ts, p2 added from trgm — no duplicates
        assert len(found) == 2

    async def test_search_by_name_deduplicates(self):
        db = _make_db()
        clinic_id = uuid4()
        p1 = _make_patient(patient_id=uuid4())

        ts_result = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[p1])))
        )
        trgm_result = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[p1])))
        )
        db.execute = AsyncMock(side_effect=[ts_result, trgm_result])

        found = await patient_service.search_patients(
            db, clinic_id, q="an", search_type="name"
        )
        assert len(found) == 1  # deduplicated

    async def test_search_by_name_apostrophe_does_not_raise(self):
        """Regression: plainto_tsquery is safe on apostrophes (M3 fix).

        Previously used to_tsquery which raised on O'Brien.
        Now uses plainto_tsquery which handles arbitrary user input.
        """
        db = _make_db()
        clinic_id = uuid4()

        ts_result = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )
        trgm_result = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )
        db.execute = AsyncMock(side_effect=[ts_result, trgm_result])

        # Must not raise even with apostrophes, special chars
        found = await patient_service.search_patients(
            db, clinic_id, q="O'Brien", search_type="name"
        )
        assert found == []


# ---------------------------------------------------------------------------
# audit_patient_read
# ---------------------------------------------------------------------------


class TestAuditPatientRead:
    async def test_calls_write_audit(self):
        patient_id = uuid4()
        clinic_id = uuid4()
        user_id = uuid4()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        with (
            patch(
                "app.modules.patients.services.patient_service.AsyncSessionLocal",
                return_value=mock_session,
            ),
            patch("app.modules.patients.services.patient_service.write_audit") as mock_audit,
        ):
            mock_audit.return_value = None
            await patient_service.audit_patient_read(patient_id, clinic_id, user_id)
            mock_audit.assert_called_once()
            call_kwargs = mock_audit.call_args
            assert call_kwargs.kwargs["action"] == "READ"
            assert call_kwargs.kwargs["entity_type"] == "Patient"
            assert call_kwargs.kwargs["entity_id"] == patient_id
