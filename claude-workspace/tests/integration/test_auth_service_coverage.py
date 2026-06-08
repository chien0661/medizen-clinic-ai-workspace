"""Service-layer unit tests for auth_service.py — coverage for AC-6.

These tests exercise auth_service functions directly (not via HTTP) to cover
the paths left uncovered when HTTP-layer tests mock the entire service.

Uncovered lines targeted (from pytest --cov-report=term-missing):
  58, 69             — _get_clinic_by_code / _get_user helpers
  97-124             — login error paths (inactive clinic, no user, locked, inactive)
  133-141            — login success (reset counters, last_login_at)
  156-158            — login success return value
  204                — refresh: missing claims → invalid_token
  214-215            — refresh: bad UUID → invalid_token
  220-232            — refresh: user not found / locked / inactive
  247                — refresh success return dict
  286                — logout: missing jti / exp → early return
  302-303            — logout: audit exception swallowed
  325-345            — change_password success path

All tests use AsyncMock for the DB session — no real DB required.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from jose import jwt as jose_jwt

from app.core.config import settings
from app.modules.auth.services import auth_service

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db() -> AsyncMock:
    """Minimal async DB session mock."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    return db


def _make_clinic(is_active: bool = True) -> MagicMock:
    c = MagicMock()
    c.id = uuid4()
    c.is_active = is_active
    return c


def _make_user(
    *,
    is_active: bool = True,
    is_locked: bool = False,
    failed_login_count: int = 0,
) -> MagicMock:
    u = MagicMock()
    u.id = uuid4()
    u.clinic_id = uuid4()
    u.full_name = "Test User"
    u.is_active = is_active
    u.is_locked = is_locked
    u.failed_login_count = failed_login_count
    u.last_login_at = None
    u.password_hash = "$2b$12$placeholder"  # real hash not needed for mock
    u.password_changed_at = None
    return u


def _scalars_first(value: Any) -> AsyncMock:
    """Return an execute() mock whose .scalars().first() returns ``value``."""
    result = MagicMock()
    result.scalars.return_value.first.return_value = value
    execute_mock = AsyncMock(return_value=result)
    return execute_mock


def _make_refresh_token(
    user_id: UUID,
    clinic_id: UUID,
    *,
    token_type: str = "refresh",
    include_jti: bool = True,
    include_sub: bool = True,
    include_clinic: bool = True,
    include_exp: bool = True,
) -> str:
    """Build a real signed JWT with controlled claims for refresh tests."""
    now = datetime.now(UTC)
    payload: dict = {
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(days=1),
    }
    if include_sub:
        payload["sub"] = str(user_id)
    if include_clinic:
        payload["clinic_id"] = str(clinic_id)
    if include_jti:
        payload["jti"] = str(uuid4())
    return jose_jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Login — error paths
# ---------------------------------------------------------------------------


class TestLoginErrorPaths:
    async def test_login_clinic_not_found_raises(self):
        """Clinic code not found (None) → invalid_credentials."""
        db = _make_db()
        db.execute = _scalars_first(None)

        with pytest.raises(ValueError, match="invalid_credentials"):
            await auth_service.login(db, "user", "pass", "BADCLINIC")

    async def test_login_inactive_clinic_raises(self):
        """Inactive clinic → invalid_credentials."""
        db = _make_db()
        clinic = _make_clinic(is_active=False)
        db.execute = _scalars_first(clinic)

        with pytest.raises(ValueError, match="invalid_credentials"):
            await auth_service.login(db, "user", "pass", "CLINIC1")

    async def test_login_user_not_found_raises(self):
        """User not found → record_failed_attempt (no user_id) → invalid_credentials."""
        db = _make_db()
        clinic = _make_clinic(is_active=True)

        call_count = 0

        async def _execute_side(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            # 1st call → clinic, 2nd call → None (user not found)
            result.scalars.return_value.first.return_value = (
                clinic if call_count == 1 else None
            )
            return result

        db.execute = AsyncMock(side_effect=_execute_side)

        with patch(
            "app.modules.auth.services.auth_service.record_failed_attempt",
            new_callable=AsyncMock,
        ) as mock_rfa, pytest.raises(ValueError, match="invalid_credentials"):
            await auth_service.login(db, "user", "pass", "CLINIC1")

        mock_rfa.assert_awaited_once()
        # Called without user_id
        _call_kwargs = mock_rfa.call_args
        assert _call_kwargs.kwargs.get("user_id") is None

    async def test_login_locked_user_raises(self):
        """Locked user → locked_user before password check."""
        db = _make_db()
        clinic = _make_clinic()
        user = _make_user(is_locked=True)

        call_count = 0

        async def _execute_side(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.scalars.return_value.first.return_value = (
                clinic if call_count == 1 else user
            )
            return result

        db.execute = AsyncMock(side_effect=_execute_side)

        with pytest.raises(ValueError, match="locked_user"):
            await auth_service.login(db, "user", "pass", "CLINIC1")

    async def test_login_inactive_user_raises(self):
        """Inactive user → inactive_user."""
        db = _make_db()
        clinic = _make_clinic()
        user = _make_user(is_active=False)

        call_count = 0

        async def _execute_side(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.scalars.return_value.first.return_value = (
                clinic if call_count == 1 else user
            )
            return result

        db.execute = AsyncMock(side_effect=_execute_side)

        with pytest.raises(ValueError, match="inactive_user"):
            await auth_service.login(db, "user", "pass", "CLINIC1")

    async def test_login_wrong_password_increments_count(self):
        """Wrong password → flush failed_login_count, record_failed_attempt, audit, raise."""
        db = _make_db()
        clinic = _make_clinic()
        user = _make_user(failed_login_count=0)

        call_count = 0

        async def _execute_side(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.scalars.return_value.first.return_value = (
                clinic if call_count == 1 else user
            )
            return result

        db.execute = AsyncMock(side_effect=_execute_side)

        with (
            patch(
                "app.modules.auth.services.auth_service.verify_password",
                return_value=False,
            ),
            patch(
                "app.modules.auth.services.auth_service.record_failed_attempt",
                new_callable=AsyncMock,
            ) as mock_rfa,
            patch(
                "app.modules.auth.services.auth_service.write_audit",
                new_callable=AsyncMock,
            ),pytest.raises(ValueError, match="invalid_credentials")
        ):
            await auth_service.login(db, "user", "WRONG", "CLINIC1")

        mock_rfa.assert_awaited_once()
        assert user.failed_login_count == 1


# ---------------------------------------------------------------------------
# Login — success path
# ---------------------------------------------------------------------------


class TestLoginSuccess:
    async def test_login_success_resets_count_and_returns_tokens(self):
        """Correct password → reset counters, issue tokens, audit login."""
        db = _make_db()
        clinic = _make_clinic()
        user = _make_user(failed_login_count=3)

        call_count = 0

        async def _execute_side(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.scalars.return_value.first.return_value = (
                clinic if call_count == 1 else user
            )
            return result

        db.execute = AsyncMock(side_effect=_execute_side)

        with (
            patch(
                "app.modules.auth.services.auth_service.verify_password",
                return_value=True,
            ),
            patch(
                "app.modules.auth.services.auth_service.clear_failed_attempts",
                new_callable=AsyncMock,
            ) as mock_clear,
            patch(
                "app.modules.auth.services.auth_service.write_audit",
                new_callable=AsyncMock,
            ),
            patch(
                "app.modules.auth.services.auth_service.create_access_token",
                return_value="access.token",
            ),
            patch(
                "app.modules.auth.services.auth_service.create_refresh_token",
                return_value="refresh.token",
            ),
        ):
            result = await auth_service.login(db, "user", "correct", "CLINIC1")

        assert result["access_token"] == "access.token"
        assert result["refresh_token"] == "refresh.token"
        assert "user" in result
        assert user.failed_login_count == 0
        mock_clear.assert_awaited_once()


# ---------------------------------------------------------------------------
# Refresh — error paths
# ---------------------------------------------------------------------------


class TestRefreshErrorPaths:
    async def test_refresh_malformed_token_raises(self):
        """Completely invalid JWT → invalid_token."""
        db = _make_db()
        with pytest.raises(ValueError, match="invalid_token"):
            await auth_service.refresh(db, "not.a.jwt")

    async def test_refresh_access_token_used_raises(self):
        """Access token passed as refresh → invalid_token (wrong type)."""
        db = _make_db()
        uid = uuid4()
        cid = uuid4()
        access_tok = _make_refresh_token(uid, cid, token_type="access")

        with pytest.raises(ValueError, match="invalid_token"):
            await auth_service.refresh(db, access_tok)

    async def test_refresh_missing_claims_raises(self):
        """Token missing jti/sub/clinic_id/exp → invalid_token."""
        db = _make_db()
        uid = uuid4()
        cid = uuid4()
        # Missing jti
        token = _make_refresh_token(uid, cid, include_jti=False)

        with pytest.raises(ValueError, match="invalid_token"):
            await auth_service.refresh(db, token)

    async def test_refresh_revoked_token_raises(self):
        """Blacklisted jti → revoked_token."""
        db = _make_db()
        uid = uuid4()
        cid = uuid4()
        token = _make_refresh_token(uid, cid)

        with patch(
            "app.modules.auth.services.auth_service.is_revoked",
            new_callable=AsyncMock,
            return_value=True,
        ), pytest.raises(ValueError, match="revoked_token"):
            await auth_service.refresh(db, token)

    async def test_refresh_bad_uuid_in_sub_raises(self):
        """Sub/clinic_id not valid UUIDs → invalid_token."""
        db = _make_db()
        # Craft token with bad sub
        now = datetime.now(UTC)
        payload = {
            "type": "refresh",
            "sub": "not-a-uuid",
            "clinic_id": "not-a-uuid",
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(days=1),
        }
        token = jose_jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        with patch(
            "app.modules.auth.services.auth_service.is_revoked",
            new_callable=AsyncMock,
            return_value=False,
        ), pytest.raises(ValueError, match="invalid_token"):
            await auth_service.refresh(db, token)

    async def test_refresh_user_not_found_raises(self):
        """User not in DB → invalid_token."""
        db = _make_db()
        uid = uuid4()
        cid = uuid4()
        token = _make_refresh_token(uid, cid)

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        with patch(
            "app.modules.auth.services.auth_service.is_revoked",
            new_callable=AsyncMock,
            return_value=False,
        ), pytest.raises(ValueError, match="invalid_token"):
            await auth_service.refresh(db, token)

    async def test_refresh_locked_user_raises(self):
        """Locked user → locked_user during refresh."""
        db = _make_db()
        uid = uuid4()
        cid = uuid4()
        token = _make_refresh_token(uid, cid)
        user = _make_user(is_locked=True)

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        with patch(
            "app.modules.auth.services.auth_service.is_revoked",
            new_callable=AsyncMock,
            return_value=False,
        ), pytest.raises(ValueError, match="locked_user"):
            await auth_service.refresh(db, token)

    async def test_refresh_inactive_user_raises(self):
        """Inactive user → inactive_user during refresh."""
        db = _make_db()
        uid = uuid4()
        cid = uuid4()
        token = _make_refresh_token(uid, cid)
        user = _make_user(is_active=False)

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        with patch(
            "app.modules.auth.services.auth_service.is_revoked",
            new_callable=AsyncMock,
            return_value=False,
        ), pytest.raises(ValueError, match="inactive_user"):
            await auth_service.refresh(db, token)


# ---------------------------------------------------------------------------
# Refresh — success path
# ---------------------------------------------------------------------------


class TestRefreshSuccess:
    async def test_refresh_success_returns_new_tokens(self):
        """Valid refresh token → revoke old jti, issue new pair, audit."""
        db = _make_db()
        uid = uuid4()
        cid = uuid4()
        token = _make_refresh_token(uid, cid)
        user = _make_user()

        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        with (
            patch(
                "app.modules.auth.services.auth_service.is_revoked",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch(
                "app.modules.auth.services.auth_service.revoke_token",
                new_callable=AsyncMock,
            ) as mock_revoke,
            patch(
                "app.modules.auth.services.auth_service.create_access_token",
                return_value="new.access",
            ),
            patch(
                "app.modules.auth.services.auth_service.create_refresh_token",
                return_value="new.refresh",
            ),
            patch(
                "app.modules.auth.services.auth_service.write_audit",
                new_callable=AsyncMock,
            ),
        ):
            result = await auth_service.refresh(db, token)

        assert result["access_token"] == "new.access"
        assert result["refresh_token"] == "new.refresh"
        assert "user" in result
        mock_revoke.assert_awaited_once()


# ---------------------------------------------------------------------------
# Logout — edge paths
# ---------------------------------------------------------------------------


class TestLogoutEdgePaths:
    async def test_logout_malformed_token_silent(self):
        """Malformed/expired token → silently returns (nothing to revoke)."""
        db = _make_db()
        # Should not raise
        await auth_service.logout(db, "totally.invalid.token")

    async def test_logout_missing_jti_returns_early(self):
        """Token missing jti/exp → early return without revocation."""
        db = _make_db()
        # Craft token without jti
        now = datetime.now(UTC)
        payload = {
            "sub": str(uuid4()),
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=1),
            # no jti
        }
        token = jose_jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        with patch(
            "app.modules.auth.services.auth_service.revoke_token",
            new_callable=AsyncMock,
        ) as mock_revoke:
            await auth_service.logout(db, token)

        mock_revoke.assert_not_awaited()

    async def test_logout_audit_exception_swallowed(self):
        """Audit write failure during logout does not raise."""
        db = _make_db()
        uid = uuid4()
        cid = uuid4()
        # Build a token with sub so the audit path is exercised
        now = datetime.now(UTC)
        payload = {
            "sub": str(uid),
            "clinic_id": str(cid),
            "type": "refresh",
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(days=1),
        }
        token = jose_jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        with (
            patch(
                "app.modules.auth.services.auth_service.revoke_token",
                new_callable=AsyncMock,
            ),
            patch(
                "app.modules.auth.services.auth_service.write_audit",
                new_callable=AsyncMock,
                side_effect=Exception("audit down"),
            ),
        ):
            # Must not raise
            await auth_service.logout(db, token)


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------


class TestChangePassword:
    async def test_change_password_user_not_found_raises(self):
        """user_id not in DB → user_not_found."""
        db = _make_db()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="user_not_found"):
            await auth_service.change_password(db, uuid4(), "old", "new")

    async def test_change_password_wrong_old_password_raises(self):
        """Wrong old password → invalid_credentials."""
        db = _make_db()
        user = _make_user()
        db.get = AsyncMock(return_value=user)

        with patch(
            "app.modules.auth.services.auth_service.verify_password",
            return_value=False,
        ), pytest.raises(ValueError, match="invalid_credentials"):
            await auth_service.change_password(db, uuid4(), "wrong_old", "new")

    async def test_change_password_success(self):
        """Correct old password → hash updated, audit written, no exception."""
        db = _make_db()
        user = _make_user()
        db.get = AsyncMock(return_value=user)

        with (
            patch(
                "app.modules.auth.services.auth_service.verify_password",
                return_value=True,
            ),
            patch(
                "app.modules.auth.services.auth_service.hash_password",
                return_value="new_hash",
            ),
            patch(
                "app.modules.auth.services.auth_service.write_audit",
                new_callable=AsyncMock,
            ) as mock_audit,
        ):
            await auth_service.change_password(db, uuid4(), "old_pass", "new_pass")

        assert user.password_hash == "new_hash"
        assert user.password_changed_at is not None
        mock_audit.assert_awaited_once()
