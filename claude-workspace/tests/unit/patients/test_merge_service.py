"""Unit tests for merge_service.py.

Covers:
- merge: happy path, cross-tenant rejection, drop_id not found, keep_id not found,
         drop_id already soft-deleted, audit log created
- undo_merge: happy path within 7 days, expired deadline → 410, already undone → 409,
              merge_log not found
- _snapshot_patient: captures all columns, UUIDs as strings
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.modules.patients.services.merge_service import (
    CrossTenantError,
    MergeAlreadyUndoneError,
    MergeUndoExpiredError,
    _snapshot_patient,
    merge,
    undo_merge,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_patient(
    patient_id=None,
    clinic_id=None,
    is_deleted=False,
    patient_code="BN0001",
):
    p = MagicMock()
    p.id = patient_id or uuid4()
    p.clinic_id = clinic_id or uuid4()
    p.is_deleted = is_deleted
    p.patient_code = patient_code
    p.full_name = "Test Patient"
    p.date_of_birth = None
    p.birth_year = 1990
    p.gender = "male"
    p.phone = None
    return p


def _make_merge_log(
    merge_id=None,
    keep_id=None,
    drop_id=None,
    clinic_id=None,
    undone=False,
    undo_deadline=None,
    is_deleted=False,
):
    m = MagicMock()
    m.id = merge_id or uuid4()
    m.keep_patient_id = keep_id or uuid4()
    m.drop_patient_id = drop_id or uuid4()
    m.clinic_id = clinic_id or uuid4()
    m.undone = undone
    m.undo_deadline = undo_deadline or (datetime.now(UTC) + timedelta(days=7))
    m.is_deleted = is_deleted
    # source_patient_data: use a real dict so .get() works in undo_merge (M4 fix)
    m.source_patient_data = {"full_name": "Test", "reassigned_refs": {}}
    return m


def _make_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# merge()
# ---------------------------------------------------------------------------


def _make_execute_with_fetchall(rows=None):
    """Return an AsyncMock for db.execute that supports .fetchall()."""
    result = MagicMock()
    result.fetchall.return_value = rows or []
    return AsyncMock(return_value=result)


class TestMerge:
    @patch("app.modules.patients.services.merge_service._snapshot_patient")
    @patch("app.modules.patients.services.merge_service.write_audit")
    async def test_happy_path(self, mock_audit, mock_snapshot):
        mock_audit.return_value = None
        mock_snapshot.return_value = {"full_name": "Test", "id": str(uuid4())}

        clinic_id = uuid4()
        keep = _make_patient(clinic_id=clinic_id)
        drop = _make_patient(clinic_id=clinic_id)

        db = _make_db()
        # get(Patient, keep_id) → keep, get(Patient, drop_id) → drop
        db.get = AsyncMock(side_effect=[keep, drop])
        # merge now does SELECT id ... fetchall() then UPDATE for each table
        db.execute = _make_execute_with_fetchall()

        await merge(
            db,
            keep_id=keep.id,
            drop_id=drop.id,
            reason="Test merge",
            merged_by=uuid4(),
        )

        assert drop.is_deleted is True
        mock_audit.assert_called_once()
        db.flush.assert_called()

    @patch("app.modules.patients.services.merge_service.write_audit")
    async def test_cross_tenant_raises(self, mock_audit):
        keep = _make_patient(clinic_id=uuid4())
        drop = _make_patient(clinic_id=uuid4())  # different clinic

        db = _make_db()
        db.get = AsyncMock(side_effect=[keep, drop])

        with pytest.raises(CrossTenantError):
            await merge(db, keep_id=keep.id, drop_id=drop.id, reason=None, merged_by=uuid4())

    async def test_keep_not_found_raises(self):
        db = _make_db()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await merge(db, keep_id=uuid4(), drop_id=uuid4(), reason=None, merged_by=uuid4())

    async def test_drop_not_found_raises(self):
        db = _make_db()
        keep = _make_patient()
        db.get = AsyncMock(side_effect=[keep, None])

        with pytest.raises(NotFoundError):
            await merge(db, keep_id=keep.id, drop_id=uuid4(), reason=None, merged_by=uuid4())

    async def test_drop_already_deleted_raises(self):
        db = _make_db()
        clinic_id = uuid4()
        keep = _make_patient(clinic_id=clinic_id)
        drop = _make_patient(clinic_id=clinic_id, is_deleted=True)
        db.get = AsyncMock(side_effect=[keep, drop])

        with pytest.raises(NotFoundError):
            await merge(db, keep_id=keep.id, drop_id=drop.id, reason=None, merged_by=uuid4())

    @patch("app.modules.patients.services.merge_service._snapshot_patient")
    @patch("app.modules.patients.services.merge_service.write_audit")
    async def test_audit_log_is_written(self, mock_audit, mock_snapshot):
        mock_audit.return_value = None
        mock_snapshot.return_value = {"full_name": "Test", "id": str(uuid4())}
        clinic_id = uuid4()
        keep = _make_patient(clinic_id=clinic_id)
        drop = _make_patient(clinic_id=clinic_id)

        db = _make_db()
        db.get = AsyncMock(side_effect=[keep, drop])
        db.execute = _make_execute_with_fetchall()

        await merge(db, keep_id=keep.id, drop_id=drop.id, reason="audit test", merged_by=uuid4())

        mock_audit.assert_called_once()
        kwargs = mock_audit.call_args.kwargs
        assert kwargs["action"] == "MERGE"
        assert kwargs["entity_type"] == "Patient"
        assert kwargs["entity_id"] == keep.id


# ---------------------------------------------------------------------------
# undo_merge()
# ---------------------------------------------------------------------------


class TestUndoMerge:
    @patch("app.modules.patients.services.merge_service.write_audit")
    async def test_happy_path_within_deadline(self, mock_audit):
        mock_audit.return_value = None

        merge_log = _make_merge_log(undo_deadline=datetime.now(UTC) + timedelta(days=3))
        drop = _make_patient(is_deleted=True)
        drop.id = merge_log.drop_patient_id

        db = _make_db()
        # get(PatientMergeLog, merge_id) → merge_log, get(Patient, drop_id) → drop
        db.get = AsyncMock(side_effect=[merge_log, drop])
        db.execute = AsyncMock(return_value=MagicMock())

        await undo_merge(db, merge_id=merge_log.id, undone_by=uuid4())

        assert drop.is_deleted is False
        assert merge_log.undone is True
        mock_audit.assert_called_once()

    async def test_expired_deadline_raises_410(self):
        merge_log = _make_merge_log(undo_deadline=datetime.now(UTC) - timedelta(days=1))

        db = _make_db()
        db.get = AsyncMock(return_value=merge_log)

        with pytest.raises(MergeUndoExpiredError) as exc_info:
            await undo_merge(db, merge_id=merge_log.id, undone_by=uuid4())
        assert exc_info.value.http_status == 410

    async def test_already_undone_raises_409(self):
        merge_log = _make_merge_log(undone=True)

        db = _make_db()
        db.get = AsyncMock(return_value=merge_log)

        with pytest.raises(MergeAlreadyUndoneError) as exc_info:
            await undo_merge(db, merge_id=merge_log.id, undone_by=uuid4())
        assert exc_info.value.http_status == 409

    async def test_merge_log_not_found_raises(self):
        db = _make_db()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await undo_merge(db, merge_id=uuid4(), undone_by=uuid4())

    async def test_drop_patient_missing_raises(self):
        merge_log = _make_merge_log(undo_deadline=datetime.now(UTC) + timedelta(days=3))

        db = _make_db()
        # merge_log found, but drop patient not found
        db.get = AsyncMock(side_effect=[merge_log, None])

        with pytest.raises(NotFoundError):
            await undo_merge(db, merge_id=merge_log.id, undone_by=uuid4())

    @patch("app.modules.patients.services.merge_service.write_audit")
    async def test_undo_only_moves_manifested_rows(self, mock_audit):
        """Undo must only revert rows listed in reassigned_refs manifest (M4 fix).

        keep_patient may have rows of its own that must not be moved back.
        """
        mock_audit.return_value = None

        reassigned_row_id = str(uuid4())
        merge_log = _make_merge_log(undo_deadline=datetime.now(UTC) + timedelta(days=3))
        # Provide a manifest with exactly one row ID
        merge_log.source_patient_data = {
            "reassigned_refs": {
                "patient_relation.patient_id": [reassigned_row_id],
            }
        }
        drop = _make_patient(is_deleted=True)
        drop.id = merge_log.drop_patient_id

        executed_sqls: list[str] = []

        async def capture_execute(stmt, params=None):
            sql = str(stmt)
            executed_sqls.append(sql)
            return MagicMock()

        db = _make_db()
        db.get = AsyncMock(side_effect=[merge_log, drop])
        db.execute = capture_execute

        await undo_merge(db, merge_id=merge_log.id, undone_by=uuid4())

        # Verify the UPDATE used ANY(:ids) — not a blind WHERE fk = keep_id
        update_sqls = [s for s in executed_sqls if "UPDATE" in s.upper()]
        assert any("ANY" in s for s in update_sqls), (
            "Expected id-based UPDATE using ANY(:ids), got: " + str(update_sqls)
        )


# ---------------------------------------------------------------------------
# _snapshot_patient
# ---------------------------------------------------------------------------


class TestSnapshotPatient:
    async def test_captures_all_columns(self):
        """_snapshot_patient should return a non-empty dict with all mapped columns."""
        from app.modules.patients.models.patient import Patient

        p = Patient(
            full_name="Test",
            gender="male",
            birth_year=1990,
        )
        # Set required attrs manually (no DB)
        p.id = uuid4()
        p.clinic_id = uuid4()

        snap = _snapshot_patient(p)
        # Should contain patient-specific fields
        assert "full_name" in snap
        assert snap["full_name"] == "Test"
        # UUIDs should be strings
        assert isinstance(snap["id"], str)
        assert isinstance(snap["clinic_id"], str)
