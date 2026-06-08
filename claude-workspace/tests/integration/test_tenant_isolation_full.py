"""Integration E2E test: Acceptance Criteria #1 — tenant isolation via RLS.

Scenario: User of clinic A queries audit_log → only sees clinic A data.

Setup:
  - 2 clinics (clinic_a, clinic_b) with committed audit_log rows
  - Written via write_audit() (business event path), not raw SQL inserts
  - Query performed as cms_app role (NOSUPERUSER NOBYPASSRLS) so RLS applies
  - ContextVar app.current_clinic_id drives the RLS policy

Acceptance criterion (TASK-002 spec):
  "User của clinic A query bảng audit_log → chỉ thấy data của clinic A"

NullPool note:
  All engines created in function-scoped tests use NullPool to avoid the
  "attached to a different loop" issue that arises when a session-scoped
  pool connection is reused across pytest-asyncio function-scoped event loops.
"""

from __future__ import annotations

import re
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.conftest import TEST_DATABASE_URL

_RLS_ROLE = "cms_app"
_RLS_URL = re.sub(r"//[^:]+:[^@]+@", f"//{_RLS_ROLE}:{_RLS_ROLE}@", TEST_DATABASE_URL)
_ADMIN_URL = TEST_DATABASE_URL


async def _ensure_cms_app_role(admin_url: str) -> None:
    """Ensure cms_app role exists with required privileges (idempotent)."""
    engine = create_async_engine(admin_url, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("COMMIT"))
            row = await conn.execute(
                text("SELECT 1 FROM pg_roles WHERE rolname = :r"),
                {"r": _RLS_ROLE},
            )
            if not row.fetchone():
                await conn.execute(
                    text(f"CREATE ROLE {_RLS_ROLE} LOGIN PASSWORD '{_RLS_ROLE}'")
                )
            await conn.execute(text(f"GRANT CONNECT ON DATABASE cms TO {_RLS_ROLE}"))
            await conn.execute(
                text(f"GRANT SELECT, INSERT ON audit_log TO {_RLS_ROLE}")
            )
            await conn.execute(text("COMMIT"))
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def admin_engine():
    """NullPool admin engine (connects as cms superuser) — function-scoped."""
    engine = create_async_engine(_ADMIN_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def rls_engine():
    """NullPool engine connecting as cms_app (NOSUPERUSER NOBYPASSRLS) — function-scoped."""
    await _ensure_cms_app_role(_ADMIN_URL)
    engine = create_async_engine(_RLS_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def two_clinic_audit_rows(admin_engine):
    """Write 2 audit_log rows via write_audit() for 2 different clinics.

    Uses write_audit() — the business event write path — so this exercises
    the real audit infrastructure, not a raw SQL bypass.
    """
    from app.core.audit import write_audit
    from app.core.db import current_clinic_id, current_user_id

    clinic_a = uuid4()
    clinic_b = uuid4()
    entity_id = uuid4()

    factory = async_sessionmaker(admin_engine, expire_on_commit=False)

    # Write audit row for clinic_a
    async with factory() as session:
        tok_c = current_clinic_id.set(clinic_a)
        tok_u = current_user_id.set(uuid4())
        try:
            await write_audit(
                session,
                action="INSERT",
                entity_type="Patient",
                entity_id=entity_id,
                new_data={"name": "Patient A"},
            )
            await session.commit()
        finally:
            current_clinic_id.reset(tok_c)
            current_user_id.reset(tok_u)

    # Write audit row for clinic_b
    async with factory() as session:
        tok_c = current_clinic_id.set(clinic_b)
        tok_u = current_user_id.set(uuid4())
        try:
            await write_audit(
                session,
                action="INSERT",
                entity_type="Patient",
                entity_id=entity_id,
                new_data={"name": "Patient B"},
            )
            await session.commit()
        finally:
            current_clinic_id.reset(tok_c)
            current_user_id.reset(tok_u)

    return {"clinic_a": clinic_a, "clinic_b": clinic_b, "entity_id": entity_id}


class TestTenantIsolationE2E:
    """End-to-end RLS isolation: clinic A user only sees clinic A audit rows."""

    async def test_clinic_a_sees_only_own_audit_rows(
        self, rls_engine, two_clinic_audit_rows
    ):
        """AC#1: clinic A user cannot see clinic B's audit rows via RLS.

        Connects as cms_app (NOSUPERUSER NOBYPASSRLS) — RLS is enforced.
        """
        data = two_clinic_audit_rows
        async with rls_engine.connect() as conn:
            await conn.execute(text("BEGIN"))
            await conn.execute(
                text(
                    f"SET LOCAL app.current_clinic_id = '{data['clinic_a']}'"
                )
            )
            rows = await conn.execute(
                text(
                    "SELECT clinic_id FROM audit_log"
                    " WHERE entity_type = 'Patient' AND entity_id = :eid"
                ),
                {"eid": data["entity_id"]},
            )
            clinic_ids = [str(r[0]) for r in rows.fetchall()]
            await conn.execute(text("ROLLBACK"))

        assert str(data["clinic_a"]) in clinic_ids, (
            "Clinic A row must be visible when app.current_clinic_id = clinic_a"
        )
        assert str(data["clinic_b"]) not in clinic_ids, (
            "Clinic B row must NOT be visible to clinic A user (RLS violation)"
        )

    async def test_clinic_b_sees_only_own_audit_rows(
        self, rls_engine, two_clinic_audit_rows
    ):
        """AC#1 (symmetric): clinic B user cannot see clinic A's audit rows."""
        data = two_clinic_audit_rows
        async with rls_engine.connect() as conn:
            await conn.execute(text("BEGIN"))
            await conn.execute(
                text(
                    f"SET LOCAL app.current_clinic_id = '{data['clinic_b']}'"
                )
            )
            rows = await conn.execute(
                text(
                    "SELECT clinic_id FROM audit_log"
                    " WHERE entity_type = 'Patient' AND entity_id = :eid"
                ),
                {"eid": data["entity_id"]},
            )
            clinic_ids = [str(r[0]) for r in rows.fetchall()]
            await conn.execute(text("ROLLBACK"))

        assert str(data["clinic_b"]) in clinic_ids, (
            "Clinic B row must be visible when app.current_clinic_id = clinic_b"
        )
        assert str(data["clinic_a"]) not in clinic_ids, (
            "Clinic A row must NOT be visible to clinic B user (RLS violation)"
        )

    async def test_write_audit_sets_clinic_id_from_contextvar(
        self, admin_engine, two_clinic_audit_rows
    ):
        """write_audit() correctly captures clinic_id from ContextVar."""
        data = two_clinic_audit_rows
        factory = async_sessionmaker(admin_engine, expire_on_commit=False)
        async with factory() as session:
            rows = await session.execute(
                text(
                    "SELECT DISTINCT clinic_id FROM audit_log"
                    " WHERE entity_type = 'Patient' AND entity_id = :eid"
                ),
                {"eid": data["entity_id"]},
            )
            found = {str(r[0]) for r in rows.fetchall()}

        assert str(data["clinic_a"]) in found, "clinic_a audit row missing"
        assert str(data["clinic_b"]) in found, "clinic_b audit row missing"
        assert len(found) == 2, f"Expected exactly 2 distinct clinic rows, got: {found}"
