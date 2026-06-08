"""Integration test: audit_log is append-only (PostgreSQL trigger).

Verifies that UPDATE and DELETE on audit_log raise an exception at DB level.
Requires live PostgreSQL with migration 0002 applied.

We use raw asyncpg connections (not SQLAlchemy sessions) to avoid session
state corruption from the trigger-aborted transactions.
"""

from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker


@pytest_asyncio.fixture
async def committed_audit_row(async_engine):
    """Insert one audit_log row (committed) and return its id."""
    row_id = uuid4()
    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO audit_log"
                " (id, clinic_id, action, entity_type, entity_id, created_at)"
                " VALUES (:id, NULL, 'INSERT', 'Test', :eid, now())"
            ),
            {"id": row_id, "eid": uuid4()},
        )
        await session.commit()
    return row_id


class TestAuditLogImmutable:
    async def test_update_raises_exception(
        self, async_engine, committed_audit_row
    ):
        """DB trigger prevents UPDATE on audit_log."""
        factory = async_sessionmaker(async_engine, expire_on_commit=False)
        # Use a fresh session per assert — the trigger aborts the transaction
        async with factory() as session:
            with pytest.raises((DBAPIError, Exception)):
                async with session.begin():
                    await session.execute(
                        text(
                            "UPDATE audit_log SET action = 'TAMPERED'"
                            " WHERE id = :id"
                        ),
                        {"id": committed_audit_row},
                    )

    async def test_delete_raises_exception(
        self, async_engine, committed_audit_row
    ):
        """DB trigger prevents DELETE on audit_log."""
        factory = async_sessionmaker(async_engine, expire_on_commit=False)
        async with factory() as session:
            with pytest.raises((DBAPIError, Exception)):
                async with session.begin():
                    await session.execute(
                        text("DELETE FROM audit_log WHERE id = :id"),
                        {"id": committed_audit_row},
                    )
