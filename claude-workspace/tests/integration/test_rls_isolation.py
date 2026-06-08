"""Integration tests: RLS tenant isolation on audit_log.

Requires a live PostgreSQL with migrations applied (0001–0003).

RLS bypass note:
  The application DB user ``cms`` is a superuser (SUPERUSER + BYPASSRLS),
  so RLS is bypassed even with FORCE ROW LEVEL SECURITY.  To test policy
  enforcement we connect as a restricted role ``cms_app`` which is created
  (if absent) at fixture setup time.  This mirrors the intended production
  topology where the application connects as a non-superuser role.

Tests:
- Setting app.current_clinic_id restricts audit_log rows to that clinic
- Rows from another clinic are invisible under restricted role
- NULL clinic_id rows are visible to all clinics (system events)
"""

import re
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.conftest import TEST_DATABASE_URL

# Non-superuser role used for RLS testing
_RLS_TEST_ROLE = "cms_app"
# Build the restricted-role URL by replacing the user in the connection string
_RLS_URL = re.sub(r"//[^:]+:[^@]+@", f"//{_RLS_TEST_ROLE}:{_RLS_TEST_ROLE}@", TEST_DATABASE_URL)


async def _ensure_restricted_role(admin_engine) -> None:
    """Create cms_app role if it doesn't exist, grant table access."""
    async with admin_engine.connect() as conn:
        await conn.execute(text("COMMIT"))  # exit any implicit tx
        result = await conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :r"),
            {"r": _RLS_TEST_ROLE},
        )
        if not result.fetchone():
            # Create a non-superuser role with password = role name
            await conn.execute(
                text(f"CREATE ROLE {_RLS_TEST_ROLE} LOGIN PASSWORD '{_RLS_TEST_ROLE}'")
            )
        await conn.execute(
            text(f"GRANT CONNECT ON DATABASE cms TO {_RLS_TEST_ROLE}")
        )
        await conn.execute(
            text(f"GRANT SELECT, INSERT, DELETE ON audit_log TO {_RLS_TEST_ROLE}")
        )
        await conn.execute(text("COMMIT"))


@pytest_asyncio.fixture
async def rls_engine(async_engine):
    """Create engine connecting as restricted non-superuser role cms_app."""
    await _ensure_restricted_role(async_engine)
    engine = create_async_engine(_RLS_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def two_clinics_audit_rows(async_engine):
    """Insert two audit_log rows (different clinic_id) — committed via admin."""
    clinic_a = uuid4()
    clinic_b = uuid4()
    row_a_id = uuid4()
    row_b_id = uuid4()
    entity_id = uuid4()

    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO audit_log"
                " (id, clinic_id, action, entity_type, entity_id, created_at)"
                " VALUES"
                " (:id_a, :cid_a, 'INSERT', 'Patient', :eid, now()),"
                " (:id_b, :cid_b, 'INSERT', 'Patient', :eid, now())"
            ),
            {
                "id_a": row_a_id,
                "cid_a": clinic_a,
                "id_b": row_b_id,
                "cid_b": clinic_b,
                "eid": entity_id,
            },
        )
        await session.commit()

    return {
        "clinic_a": clinic_a,
        "clinic_b": clinic_b,
        "row_a_id": row_a_id,
        "row_b_id": row_b_id,
    }


class TestRLSIsolation:
    async def test_clinic_a_sees_only_own_rows(
        self, rls_engine, two_clinics_audit_rows
    ):
        data = two_clinics_audit_rows
        async with rls_engine.connect() as conn:
            await conn.execute(text("BEGIN"))
            # Safe: clinic_id is a validated uuid4() value
            await conn.execute(
                text(f"SET LOCAL app.current_clinic_id = '{data['clinic_a']}'")
            )
            rows = await conn.execute(
                text("SELECT id FROM audit_log WHERE id IN (:a, :b)"),
                {"a": data["row_a_id"], "b": data["row_b_id"]},
            )
            ids = [str(r[0]) for r in rows]
            await conn.execute(text("ROLLBACK"))

        assert str(data["row_a_id"]) in ids, "clinic_a row must be visible"
        assert str(data["row_b_id"]) not in ids, "clinic_b row must be hidden"

    async def test_clinic_b_sees_only_own_rows(
        self, rls_engine, two_clinics_audit_rows
    ):
        data = two_clinics_audit_rows
        async with rls_engine.connect() as conn:
            await conn.execute(text("BEGIN"))
            await conn.execute(
                text(f"SET LOCAL app.current_clinic_id = '{data['clinic_b']}'")
            )
            rows = await conn.execute(
                text("SELECT id FROM audit_log WHERE id IN (:a, :b)"),
                {"a": data["row_a_id"], "b": data["row_b_id"]},
            )
            ids = [str(r[0]) for r in rows]
            await conn.execute(text("ROLLBACK"))

        assert str(data["row_b_id"]) in ids, "clinic_b row must be visible"
        assert str(data["row_a_id"]) not in ids, "clinic_a row must be hidden"

    async def test_null_clinic_id_row_visible_to_all(
        self, rls_engine
    ):
        """System-level audit rows (clinic_id IS NULL) pass RLS for all clinics."""
        row_id = uuid4()
        any_clinic = uuid4()

        # Insert NULL-clinic row using rls_engine (NullPool, safe per-test)
        async with rls_engine.connect() as conn:
            await conn.execute(
                text(
                    "INSERT INTO audit_log"
                    " (id, clinic_id, action, entity_type, entity_id, created_at)"
                    " VALUES (:id, NULL, 'READ', 'System', :eid, now())"
                ),
                {"id": row_id, "eid": uuid4()},
            )
            await conn.commit()

        # Query via restricted user with an arbitrary clinic context
        async with rls_engine.connect() as conn:
            await conn.execute(text("BEGIN"))
            await conn.execute(
                text(f"SET LOCAL app.current_clinic_id = '{any_clinic}'")
            )
            result = await conn.execute(
                text("SELECT id FROM audit_log WHERE id = :id"),
                {"id": row_id},
            )
            row = result.fetchone()
            await conn.execute(text("ROLLBACK"))

        assert row is not None, "NULL clinic_id row should be visible under RLS"
