"""Unit tests for lockout_service.py — coverage for autonomous-tx paths.

Covers:
  - _lock_user: user not found (early return)
  - _lock_user: user already locked (early return)
  - _lock_user: success path (sets is_locked, writes audit, commits)
  - get_attempt_count: key present
  - get_attempt_count: key absent → 0
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.auth.services.lockout_service import _lock_user, get_attempt_count

pytestmark = pytest.mark.asyncio


class TestLockUserAutonomousTx:
    async def test_lock_user_not_found_returns_early(self):
        """_lock_user returns without update if user not in DB."""
        uid = uuid4()
        cid = uuid4()

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=None)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        # AsyncSessionLocal is imported locally inside _lock_user — patch at source
        with patch("app.core.db.AsyncSessionLocal", return_value=mock_session):
            await _lock_user(uid, cid, "testuser")

        mock_session.flush.assert_not_called()
        mock_session.commit.assert_not_called()

    async def test_lock_user_already_locked_returns_early(self):
        """_lock_user returns without update if user.is_locked is already True."""
        uid = uuid4()
        cid = uuid4()

        user = MagicMock()
        user.is_locked = True

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=user)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("app.core.db.AsyncSessionLocal", return_value=mock_session):
            await _lock_user(uid, cid, "testuser")

        mock_session.flush.assert_not_called()
        mock_session.commit.assert_not_called()

    async def test_lock_user_success_sets_locked_and_commits(self):
        """_lock_user: sets is_locked=True, flushes, writes audit, commits."""
        uid = uuid4()
        cid = uuid4()

        user = MagicMock()
        user.is_locked = False

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=user)
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.core.db.AsyncSessionLocal", return_value=mock_session),
            patch(
                "app.modules.auth.services.lockout_service.write_audit",
                new_callable=AsyncMock,
            ) as mock_audit,
        ):
            await _lock_user(uid, cid, "testuser")

        assert user.is_locked is True
        mock_session.add.assert_called_once_with(user)
        mock_session.flush.assert_awaited_once()
        mock_audit.assert_awaited_once()
        mock_session.commit.assert_awaited_once()


class TestGetAttemptCount:
    async def test_returns_count_when_key_exists(self):
        """get_attempt_count returns integer when Redis key is present."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="3")
        mock_redis.__aenter__ = AsyncMock(return_value=mock_redis)
        mock_redis.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.modules.auth.services.lockout_service._redis",
            return_value=mock_redis,
        ):
            count = await get_attempt_count(uuid4(), "user1")

        assert count == 3

    async def test_returns_zero_when_key_absent(self):
        """get_attempt_count returns 0 when Redis key is absent (None)."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.__aenter__ = AsyncMock(return_value=mock_redis)
        mock_redis.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.modules.auth.services.lockout_service._redis",
            return_value=mock_redis,
        ):
            count = await get_attempt_count(uuid4(), "user1")

        assert count == 0
