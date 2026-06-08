"""Integration test: Acceptance Criteria #2 — superuser bypasses RLS.

Acceptance criterion (TASK-002 spec):
  "Bypass: chạy query với role postgres không bị chặn bởi RLS"

Verifies that the cms superuser (BYPASSRLS) can read all audit_log rows
regardless of the app.current_clinic_id setting, while the restricted
cms_app role (NOSUPERUSER NOBYPASSRLS) is correctly blocked by the policy.

This validates the two-role topology:
  - cms (superuser) → RLS bypassed → sees all rows
  - cms_app (restricted) → RLS enforced → sees only own-clinic rows

NullPool note:
  All engines use NullPool (function-scoped) to avoid "attached to a different
  loop" errors from the session-scoped conftest engine pool.
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
    """NullPool admin (superuser) engine — function-scoped."""
    engine = create_async_engine(_ADMIN_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def rls_engine():
    """NullPool engine connecting as cms_app restricted role — function-scoped."""
    await _ensure_cms_app_role(_ADMIN_URL)
    engine = create_async_engine(_RLS_URL, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def two_clinic_rows(admin_engine):
    """Insert 2 audit_log rows with different clinic_ids — committed via superuser."""
    clinic_a = uuid4()
    clinic_b = uuid4()
    row_a = uuid4()
    row_b = uuid4()
    entity_id = uuid4()

    factory = async_sessionmaker(admin_engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(
            text(
                "INSERT INTO audit_log"
                " (id, clinic_id, action, entity_type, entity_id, created_at)"
                " VALUES"
                " (:ra, :ca, 'INSERT', 'RLSBypassTest', :eid, now()),"
                " (:rb, :cb, 'INSERT', 'RLSBypassTest', :eid, now())"
            ),
            {"ra": row_a, "ca": clinic_a, "rb": row_b, "cb": clinic_b, "eid": entity_id},
        )
        await session.commit()

    return {
        "clinic_a": clinic_a,
        "clinic_b": clinic_b,
        "row_a": row_a,
        "row_b": row_b,
        "entity_id": entity_id,
    }


class TestRLSAdminBypass:
    """AC#2: Superuser bypasses RLS; restricted role is blocked."""

    async def test_superuser_sees_all_rows_regardless_of_clinic_context(
        self, admin_engine, two_clinic_rows
    ):
        """CMS superuser can see both clinic rows even with clinic_a context set.

        This validates BYPASSRLS attribute of cms role — superuser is never
        blocked by row-level security policies.
        """
        data = two_clinic_rows
        factory = async_sessionmaker(admin_engine, expire_on_commit=False)
        async with factory() as session:
            # Set clinic_a context on the superuser session
            await session.execute(
                text(f"SET LOCAL app.current_clinic_id = '{data['clinic_a']}'")
            )
            result = await session.execute(
                text(
                    "SELECT id FROM audit_log"
                    " WHERE entity_type = 'RLSBypassTest' AND entity_id = :eid"
                ),
                {"eid": data["entity_id"]},
            )
            ids = {str(r[0]) for r in result.fetchall()}

        # Superuser sees BOTH rows despite clinic_a context
        assert str(data["row_a"]) in ids, "Superuser must see clinic_a row"
        assert str(data["row_b"]) in ids, (
            "Superuser must see clinic_b row (RLS bypass — not restricted by policy)"
        )

    async def test_restricted_role_blocked_by_rls(
        self, rls_engine, two_clinic_rows
    ):
        """CMS_APP restricted role is blocked by RLS — sees only own-clinic rows."""
        data = two_clinic_rows
        async with rls_engine.connect() as conn:
            await conn.execute(text("BEGIN"))
            await conn.execute(
                text(f"SET LOCAL app.current_clinic_id = '{data['clinic_a']}'")
            )
            result = await conn.execute(
                text(
                    "SELECT id FROM audit_log"
                    " WHERE entity_type = 'RLSBypassTest' AND entity_id = :eid"
                ),
                {"eid": data["entity_id"]},
            )
            ids = {str(r[0]) for r in result.fetchall()}
            await conn.execute(text("ROLLBACK"))

        assert str(data["row_a"]) in ids, "Restricted role must see clinic_a row"
        assert str(data["row_b"]) not in ids, (
            "Restricted role must NOT see clinic_b row (RLS enforcement)"
        )

    async def test_cms_role_is_superuser(self, admin_engine):
        """Verify cms database role has rolsuper=true (by-design topology)."""
        factory = async_sessionmaker(admin_engine, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
            )
            row = result.fetchone()

        assert row is not None, "Could not query pg_roles"
        # cms connects as superuser in test/dev — this is the expected topology
        assert row[0] is True, (
            "cms role must be SUPERUSER (confirmed topology for bypass test)"
        )

    async def test_cms_app_role_is_not_superuser(self, rls_engine):
        """Verify cms_app database role has rolsuper=false (correct restricted topology)."""
        async with rls_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
            )
            row = result.fetchone()

        assert row is not None, "Could not query pg_roles as cms_app"
        assert row[0] is False, (
            "cms_app must NOT be a superuser — it must be subject to RLS"
        )
