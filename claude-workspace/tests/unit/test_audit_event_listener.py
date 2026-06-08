"""Unit tests: audit event listener uses synchronous session.add (not asyncio.create_task).

Tests verify:
1. _write_audit_sync calls session.add synchronously (not via event loop)
2. The audit record is added to the session in the same call (no async dispatch)
3. PII fields are redacted before session.add is called
4. None → value transitions (new column set for first time) are captured
5. No asyncio.create_task is used in the actual code paths (only in docstring references)
"""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock
from uuid import uuid4

from app.core.audit import (
    _ALWAYS_REDACT,
    _REDACTED,
    _compute_diff,
    _model_to_dict,
    _write_audit_sync,
    register_audit_listeners,
)


class TestWriteAuditSyncIsSynchronous:
    def test_no_asyncio_create_task_in_write_audit_sync_code(self):
        """_write_audit_sync must not call asyncio.create_task in executable code."""
        source = inspect.getsource(_write_audit_sync)
        # Strip docstring lines (lines between the triple-quote markers)
        lines = source.splitlines()
        in_docstring = False
        code_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
                continue
            if not in_docstring:
                code_lines.append(line)
        code_only = "\n".join(code_lines)
        assert "create_task" not in code_only, (
            "_write_audit_sync must not call asyncio.create_task in its code body"
        )

    def test_no_asyncio_create_task_in_after_flush_code(self):
        """The after_flush listener must not call asyncio.create_task in code."""
        source = inspect.getsource(register_audit_listeners)
        lines = source.splitlines()
        in_docstring = False
        code_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
                continue
            if not in_docstring:
                code_lines.append(line)
        code_only = "\n".join(code_lines)
        assert "create_task(" not in code_only, (
            "after_flush listener must not call asyncio.create_task()"
        )

    def test_write_audit_sync_calls_session_add(self):
        """_write_audit_sync must call session.add with an AuditLog record."""
        mock_session = MagicMock()
        mock_instance = MagicMock()
        mock_instance.id = uuid4()
        type(mock_instance).__name__ = "TestEntity"
        type(mock_instance).__audit_exclude__ = frozenset()

        new_data = {"name": "Alice", "code": "C001"}

        # AuditLog is imported locally inside _write_audit_sync, so patch the module
        import app.modules.audit.models.audit_log as audit_log_module

        original_cls = audit_log_module.AuditLog
        try:
            fake_record = MagicMock()
            fake_cls = MagicMock(return_value=fake_record)
            audit_log_module.AuditLog = fake_cls

            _write_audit_sync(
                session=mock_session,
                action="INSERT",
                instance=mock_instance,
                old_data=None,
                new_data=new_data,
            )

            mock_session.add.assert_called_once_with(fake_record)
        finally:
            audit_log_module.AuditLog = original_cls

    def test_write_audit_sync_redacts_pii_before_add(self):
        """PII fields must be replaced with *** before session.add is called."""
        mock_session = MagicMock()
        mock_instance = MagicMock()
        mock_instance.id = uuid4()
        type(mock_instance).__name__ = "User"
        type(mock_instance).__audit_exclude__ = frozenset({"password_hash"})

        new_data_with_secret = {
            "username": "alice",
            "password_hash": "bcrypt$very_secret_hash",
        }

        import app.modules.audit.models.audit_log as audit_log_module

        original_cls = audit_log_module.AuditLog
        try:
            captured_kwargs: dict = {}

            def capture_init(**kwargs):  # noqa: ANN001
                captured_kwargs.update(kwargs)
                return MagicMock()

            audit_log_module.AuditLog = capture_init  # type: ignore[assignment]

            _write_audit_sync(
                session=mock_session,
                action="INSERT",
                instance=mock_instance,
                old_data=None,
                new_data=new_data_with_secret,
            )

            assert captured_kwargs["new_data"]["password_hash"] == _REDACTED, (
                f"password_hash should be {_REDACTED!r} in new_data, "
                f"got: {captured_kwargs['new_data'].get('password_hash')}"
            )
            assert captured_kwargs["new_data"]["username"] == "alice", (
                "username should not be redacted"
            )
        finally:
            audit_log_module.AuditLog = original_cls


class TestNoneToValueTransition:
    def test_compute_diff_detects_new_field(self):
        """_compute_diff detects when a field is added (None → value)."""
        old = {"name": "Alice"}
        new = {"name": "Alice", "email": "alice@example.com"}
        result = _compute_diff(old, new)
        assert "email" in result

    def test_compute_diff_detects_value_to_none(self):
        """_compute_diff detects when a field is cleared (value → None)."""
        old = {"name": "Alice", "email": "alice@example.com"}
        new = {"name": "Alice", "email": None}
        result = _compute_diff(old, new)
        assert "email" in result

    def test_compute_diff_detects_none_to_value(self):
        """_compute_diff detects when a None field gets a value."""
        old = {"name": "Alice", "email": None}
        new = {"name": "Alice", "email": "new@example.com"}
        result = _compute_diff(old, new)
        assert "email" in result


class TestAuditExcludeMechanism:
    def test_always_redact_fields_covered(self):
        """_ALWAYS_REDACT must include standard secret field names."""
        required = {"password_hash", "password", "token", "secret", "refresh_token"}
        missing = required - _ALWAYS_REDACT
        assert not missing, f"_ALWAYS_REDACT missing: {missing}"

    def test_model_without_exclude_has_no_redactions(self):
        """A model with no secret fields should have no *** in _model_to_dict output."""
        from app.modules.users.models.clinic import Clinic

        clinic = Clinic(id=uuid4(), code="C001", name="Test", specialty="general")
        result = _model_to_dict(clinic)
        redacted = [k for k, v in result.items() if v == _REDACTED]
        assert not redacted, f"Unexpected redactions in Clinic model: {redacted}"
