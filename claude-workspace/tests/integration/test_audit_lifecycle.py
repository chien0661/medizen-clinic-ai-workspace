"""Integration tests: Full CREATE + UPDATE + DELETE audit lifecycle.

Tests that write_audit() correctly captures all three action types with
old_data / new_data diff, and that changed_fields is populated on UPDATE.

Uses write_audit() directly (the public API) since no __auditable__ model
with a DB-backed table is available until TASK-005. This exercises the exact
same code path the SQLAlchemy event listener calls.

Acceptance criterion (TASK-002 spec):
  "CREATE/UPDATE/DELETE trên entity auditable → ghi audit_log đầy đủ với
  old_data/new_data diff"

NullPool note:
  All engines use NullPool (function-scoped) to avoid "attached to a different
  loop" errors from the session-scoped conftest engine pool.
"""

from __future__ import annotations

from uuid import uuid4

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.audit import write_audit
from app.core.db import current_clinic_id, current_user_id
from tests.conftest import TEST_DATABASE_URL


@pytest_asyncio.fixture
async def db_engine():
    """NullPool engine per function — avoids cross-loop pool contamination."""
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


class TestAuditLifecycle:
    """Full INSERT → UPDATE → DELETE audit lifecycle via write_audit()."""

    async def test_create_audit_row_written(self, db_engine):
        """INSERT action writes audit_log row with new_data and no old_data."""
        entity_id = uuid4()
        clinic = uuid4()
        factory = async_sessionmaker(db_engine, expire_on_commit=False)

        tok_c = current_clinic_id.set(clinic)
        tok_u = current_user_id.set(uuid4())
        try:
            async with factory() as session:
                await write_audit(
                    session,
                    action="INSERT",
                    entity_type="TestPatient",
                    entity_id=entity_id,
                    new_data={"name": "Alice", "code": "P001"},
                )
                await session.commit()
        finally:
            current_clinic_id.reset(tok_c)
            current_user_id.reset(tok_u)

        # Verify via raw query (superuser — bypasses RLS for assertion)
        async with factory() as session:
            row = await session.execute(
                text(
                    "SELECT action, old_data, new_data, clinic_id"
                    " FROM audit_log WHERE entity_id = :eid AND action = 'INSERT'"
                ),
                {"eid": entity_id},
            )
            result = row.fetchone()

        assert result is not None, "INSERT audit row not found"
        assert result[0] == "INSERT"
        assert result[1] is None, "old_data must be NULL for INSERT"
        assert result[2] is not None, "new_data must be set for INSERT"
        assert result[2].get("name") == "Alice"
        assert str(result[3]) == str(clinic), "clinic_id must come from ContextVar"

    async def test_update_audit_row_with_diff(self, db_engine):
        """UPDATE action writes audit_log row with old_data, new_data, and changed_fields."""
        entity_id = uuid4()
        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        tok_c = current_clinic_id.set(uuid4())
        tok_u = current_user_id.set(uuid4())
        try:
            async with factory() as session:
                await write_audit(
                    session,
                    action="UPDATE",
                    entity_type="TestPatient",
                    entity_id=entity_id,
                    old_data={"name": "Alice", "phone": "0901"},
                    new_data={"name": "Alice", "phone": "0999"},
                )
                await session.commit()
        finally:
            current_clinic_id.reset(tok_c)
            current_user_id.reset(tok_u)

        async with factory() as session:
            row = await session.execute(
                text(
                    "SELECT action, old_data, new_data, changed_fields"
                    " FROM audit_log WHERE entity_id = :eid AND action = 'UPDATE'"
                ),
                {"eid": entity_id},
            )
            result = row.fetchone()

        assert result is not None, "UPDATE audit row not found"
        assert result[0] == "UPDATE"
        assert result[1].get("phone") == "0901", "old_data.phone mismatch"
        assert result[2].get("phone") == "0999", "new_data.phone mismatch"
        assert result[3] is not None, "changed_fields must be populated"
        assert "phone" in result[3], f"changed_fields missing 'phone': {result[3]}"

    async def test_delete_audit_row_with_old_data(self, db_engine):
        """DELETE action writes audit_log row with old_data and no new_data."""
        entity_id = uuid4()
        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        tok_c = current_clinic_id.set(uuid4())
        tok_u = current_user_id.set(uuid4())
        try:
            async with factory() as session:
                await write_audit(
                    session,
                    action="DELETE",
                    entity_type="TestPatient",
                    entity_id=entity_id,
                    old_data={"name": "Alice", "code": "P001"},
                )
                await session.commit()
        finally:
            current_clinic_id.reset(tok_c)
            current_user_id.reset(tok_u)

        async with factory() as session:
            row = await session.execute(
                text(
                    "SELECT action, old_data, new_data"
                    " FROM audit_log WHERE entity_id = :eid AND action = 'DELETE'"
                ),
                {"eid": entity_id},
            )
            result = row.fetchone()

        assert result is not None, "DELETE audit row not found"
        assert result[0] == "DELETE"
        assert result[1] is not None, "old_data must be set for DELETE"
        assert result[1].get("name") == "Alice"
        assert result[2] is None, "new_data must be NULL for DELETE"

    async def test_update_changed_fields_accuracy(self, db_engine):
        """changed_fields lists only the fields that actually changed."""
        entity_id = uuid4()
        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        tok_c = current_clinic_id.set(uuid4())
        tok_u = current_user_id.set(uuid4())
        try:
            async with factory() as session:
                await write_audit(
                    session,
                    action="UPDATE",
                    entity_type="TestClinic",
                    entity_id=entity_id,
                    old_data={"name": "Old Name", "phone": "0901", "email": "a@b.com"},
                    new_data={"name": "New Name", "phone": "0901", "email": "a@b.com"},
                )
                await session.commit()
        finally:
            current_clinic_id.reset(tok_c)
            current_user_id.reset(tok_u)

        async with factory() as session:
            row = await session.execute(
                text(
                    "SELECT changed_fields FROM audit_log"
                    " WHERE entity_id = :eid AND action = 'UPDATE'"
                ),
                {"eid": entity_id},
            )
            result = row.fetchone()

        assert result is not None
        fields = result[0]
        assert fields == ["name"], (
            f"Only 'name' changed — changed_fields should be ['name'], got: {fields}"
        )

    async def test_pii_field_not_auto_redacted_by_write_audit(self, db_engine):
        """write_audit() passes data as-is: redaction is only in _write_audit_sync.

        This confirms that write_audit() is the caller-controlled path;
        automatic redaction happens only in the ORM event listener path.
        """
        entity_id = uuid4()
        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        tok_c = current_clinic_id.set(uuid4())
        tok_u = current_user_id.set(uuid4())
        try:
            async with factory() as session:
                await write_audit(
                    session,
                    action="INSERT",
                    entity_type="TestUser",
                    entity_id=entity_id,
                    new_data={"username": "alice", "password_hash": "bcrypt$xxx"},
                )
                await session.commit()
        finally:
            current_clinic_id.reset(tok_c)
            current_user_id.reset(tok_u)

        async with factory() as session:
            row = await session.execute(
                text(
                    "SELECT new_data FROM audit_log"
                    " WHERE entity_id = :eid AND action = 'INSERT'"
                ),
                {"eid": entity_id},
            )
            result = row.fetchone()

        assert result is not None
        # write_audit passes data as-is; the record is persisted as provided
        assert result[0].get("username") == "alice"
        # password_hash is stored as-is here because write_audit is the
        # direct/manual path — callers must manually exclude sensitive fields
        assert "password_hash" in result[0]
