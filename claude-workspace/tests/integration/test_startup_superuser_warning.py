"""Integration test: Startup superuser CRITICAL warning (Acceptance Criteria #2 guard).

Verifies that check_db_role_security() emits a CRITICAL log when the
application connects as a superuser in a non-development environment.

This is the security guardrail from review issue C2: if someone accidentally
deploys with DATABASE_URL pointing to the cms superuser in production,
the CRITICAL warning is impossible to miss in production logs.

Also verifies that non-superuser (cms_app) in non-dev logs info (no warning).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.db_security import check_db_role_security


class TestStartupSuperuserWarning:
    """check_db_role_security() behaviour in various environments."""

    async def test_superuser_in_production_emits_critical_log(self):
        """CRITICAL log emitted when connecting as superuser in production env."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (True,)  # rolsuper = True
        mock_db.execute.return_value = mock_result

        captured_calls = []

        with (
            patch("app.core.db_security.settings") as mock_settings,
            patch("app.core.db_security.log") as mock_log,
        ):
            mock_settings.ENVIRONMENT = "production"
            mock_log.critical = MagicMock(side_effect=lambda *a, **kw: captured_calls.append(("critical", kw)))
            mock_log.info = MagicMock()

            await check_db_role_security(mock_db)

        # Verify CRITICAL was emitted
        critical_calls = [c for c in captured_calls if c[0] == "critical"]
        assert critical_calls, (
            "CRITICAL log must be emitted when app connects as superuser in production"
        )
        # Verify the event name and key message fields
        _, kwargs = critical_calls[0]
        assert kwargs.get("environment") == "production"
        assert "message" in kwargs
        assert "SUPERUSER" in kwargs["message"] or "superuser" in kwargs["message"].lower()

    async def test_superuser_in_staging_emits_critical_log(self):
        """CRITICAL log emitted in any non-development environment (staging)."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (True,)
        mock_db.execute.return_value = mock_result

        captured_calls = []

        with (
            patch("app.core.db_security.settings") as mock_settings,
            patch("app.core.db_security.log") as mock_log,
        ):
            mock_settings.ENVIRONMENT = "staging"
            mock_log.critical = MagicMock(
                side_effect=lambda *a, **kw: captured_calls.append(("critical", kw))
            )
            mock_log.info = MagicMock()

            await check_db_role_security(mock_db)

        critical_calls = [c for c in captured_calls if c[0] == "critical"]
        assert critical_calls, (
            "CRITICAL log must be emitted for superuser in staging environment"
        )

    async def test_development_env_skips_check_entirely(self):
        """check_db_role_security is a no-op in development env (no DB query)."""
        mock_db = AsyncMock()

        with patch("app.core.db_security.settings") as mock_settings:
            mock_settings.ENVIRONMENT = "development"
            await check_db_role_security(mock_db)

        # In development, no DB query should be issued
        mock_db.execute.assert_not_called()

    async def test_non_superuser_in_production_emits_info_log(self):
        """Non-superuser role in production emits info (no CRITICAL)."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (False,)  # rolsuper = False
        mock_db.execute.return_value = mock_result

        info_calls = []
        critical_calls = []

        with (
            patch("app.core.db_security.settings") as mock_settings,
            patch("app.core.db_security.log") as mock_log,
        ):
            mock_settings.ENVIRONMENT = "production"
            mock_log.info = MagicMock(side_effect=lambda *a, **kw: info_calls.append(kw))
            mock_log.critical = MagicMock(side_effect=lambda *a, **kw: critical_calls.append(kw))

            await check_db_role_security(mock_db)

        assert not critical_calls, (
            f"No CRITICAL log expected for non-superuser in production, got: {critical_calls}"
        )
        assert info_calls, "Info log expected when role is non-superuser in production"

    async def test_critical_log_event_name(self):
        """CRITICAL log event name is 'db_role_security_violation'."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (True,)
        mock_db.execute.return_value = mock_result

        captured_event = []

        with (
            patch("app.core.db_security.settings") as mock_settings,
            patch("app.core.db_security.log") as mock_log,
        ):
            mock_settings.ENVIRONMENT = "production"
            mock_log.critical = MagicMock(
                side_effect=lambda event, **kw: captured_event.append(event)
            )
            mock_log.info = MagicMock()

            await check_db_role_security(mock_db)

        assert captured_event, "CRITICAL log must be emitted"
        assert captured_event[0] == "db_role_security_violation", (
            f"Expected event name 'db_role_security_violation', got '{captured_event[0]}'"
        )
