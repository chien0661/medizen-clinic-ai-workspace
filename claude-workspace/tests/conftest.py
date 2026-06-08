"""Shared pytest fixtures for the clinic-cms test suite."""

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app

# ---------------------------------------------------------------------------
# Test database URL — env var first, sensible local default (works in Docker,
# CI, and on the host without modification).
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://cms:cms@localhost:5432/cms",
)


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Create an async engine connected to the already-migrated test database.

    Schema is managed exclusively by Alembic migrations (run before the test
    suite in CI and Docker).  We do NOT call ``create_all`` / ``drop_all`` here
    to avoid conflicts with FK constraints between tables (e.g. BaseEntity
    models referencing ``clinic``) and to preserve RLS policies / triggers that
    are set up by migrations and not reflected in ORM metadata.
    """
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Transactional test session — rolls back after each test."""
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_factory() as session, session.begin():
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client pointed at the FastAPI app (no real network)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
