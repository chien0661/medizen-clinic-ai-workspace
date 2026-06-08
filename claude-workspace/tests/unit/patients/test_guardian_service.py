"""Unit tests for guardian_service.py.

Covers:
- add_guardian: happy path, patient not found, guardian patient not found
- list_relations: returns list
- remove_relation: soft-deletes, not found
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.modules.patients.services import guardian_service

pytestmark = pytest.mark.asyncio


def _make_patient(is_deleted=False):
    p = MagicMock()
    p.id = uuid4()
    p.clinic_id = uuid4()
    p.is_deleted = is_deleted
    return p


def _make_relation(is_deleted=False):
    r = MagicMock()
    r.id = uuid4()
    r.is_deleted = is_deleted
    return r


def _make_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


class TestAddGuardian:
    async def test_happy_path_creates_relation(self):
        db = _make_db()
        patient = _make_patient()
        guardian = _make_patient()
        guardian.clinic_id = patient.clinic_id

        db.get = AsyncMock(side_effect=[patient, guardian])

        await guardian_service.add_guardian(
            db,
            patient_id=patient.id,
            guardian_patient_id=guardian.id,
            relation_type="parent",
            is_primary_contact=True,
            clinic_id=patient.clinic_id,
            created_by=uuid4(),
        )
        db.flush.assert_called_once()

    async def test_raises_not_found_for_patient(self):
        db = _make_db()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await guardian_service.add_guardian(
                db,
                patient_id=uuid4(),
                guardian_patient_id=uuid4(),
                relation_type="parent",
            )

    async def test_raises_not_found_for_guardian(self):
        db = _make_db()
        patient = _make_patient()
        # first call returns patient, second returns None for guardian
        db.get = AsyncMock(side_effect=[patient, None])

        with pytest.raises(NotFoundError):
            await guardian_service.add_guardian(
                db,
                patient_id=patient.id,
                guardian_patient_id=uuid4(),
                relation_type="parent",
            )

    async def test_raises_not_found_for_deleted_patient(self):
        db = _make_db()
        deleted_patient = _make_patient(is_deleted=True)
        db.get = AsyncMock(return_value=deleted_patient)

        with pytest.raises(NotFoundError):
            await guardian_service.add_guardian(
                db,
                patient_id=deleted_patient.id,
                guardian_patient_id=uuid4(),
                relation_type="parent",
            )


class TestListRelations:
    async def test_returns_relations(self):
        db = _make_db()
        rels = [_make_relation() for _ in range(2)]
        result = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=rels)))
        )
        db.execute = AsyncMock(return_value=result)

        found = await guardian_service.list_relations(db, uuid4())
        assert len(found) == 2

    async def test_returns_empty_list(self):
        db = _make_db()
        result = MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )
        db.execute = AsyncMock(return_value=result)

        found = await guardian_service.list_relations(db, uuid4())
        assert found == []


class TestRemoveRelation:
    async def test_soft_deletes_relation(self):
        db = _make_db()
        rel = _make_relation()
        db.get = AsyncMock(return_value=rel)

        await guardian_service.remove_relation(db, rel.id, deleted_by=uuid4())
        assert rel.is_deleted is True

    async def test_raises_not_found_when_none(self):
        db = _make_db()
        db.get = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await guardian_service.remove_relation(db, uuid4())

    async def test_raises_not_found_when_already_deleted(self):
        db = _make_db()
        rel = _make_relation(is_deleted=True)
        db.get = AsyncMock(return_value=rel)
        with pytest.raises(NotFoundError):
            await guardian_service.remove_relation(db, rel.id)
