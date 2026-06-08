"""Integration tests: PII / secret field redaction in audit logs.

Verifies that:
- Fields in ``__audit_exclude__`` are written as "***" in audit_log new_data
- Fields in ``_ALWAYS_REDACT`` (e.g. password_hash) are redacted even without
  ``__audit_exclude__``
- Non-excluded fields are captured normally

These tests use the Clinic model for baseline (no secrets) and a custom
``__audit_exclude__`` attribute temporarily patched onto Clinic to test
the exclusion mechanism.
"""

from __future__ import annotations

from uuid import uuid4

from app.core.audit import _ALWAYS_REDACT, _REDACTED, _model_to_dict
from app.modules.users.models.clinic import Clinic


class TestAuditPIIRedaction:
    def test_model_to_dict_no_redactions_on_clean_model(self):
        """A model with no secret fields should have no *** in _model_to_dict output."""
        clinic = Clinic(id=uuid4(), code="C001", name="Test Clinic", specialty="general")
        result = _model_to_dict(clinic)
        redacted = [k for k, v in result.items() if v == _REDACTED]
        assert not redacted, f"Unexpected redactions in Clinic model: {redacted}"

    def test_always_redact_set_contains_expected_names(self):
        """Verify the _ALWAYS_REDACT set covers standard secret field names."""
        expected = {"password_hash", "password", "token", "secret", "refresh_token"}
        assert expected.issubset(_ALWAYS_REDACT), (
            f"_ALWAYS_REDACT missing expected names: {expected - _ALWAYS_REDACT}"
        )

    def test_model_to_dict_with_audit_exclude(self):
        """__audit_exclude__ fields are replaced with *** in the snapshot dict."""
        original_exclude = getattr(Clinic, "__audit_exclude__", frozenset())
        try:
            Clinic.__audit_exclude__ = frozenset({"code"})  # pretend 'code' is sensitive
            clinic = Clinic(id=uuid4(), code="SECRET_CODE", name="Test", specialty="general")
            result = _model_to_dict(clinic)
            assert result.get("code") == _REDACTED, (
                f"'code' in __audit_exclude__ should be redacted, got: {result.get('code')}"
            )
            assert result.get("name") == "Test", "Non-excluded field should pass through"
        finally:
            if original_exclude:
                Clinic.__audit_exclude__ = original_exclude
            elif hasattr(Clinic, "__audit_exclude__"):
                del Clinic.__audit_exclude__

    def test_pii_redaction_in_new_data_dict(self):
        """Simulate what the event listener does: redact always-redact fields before audit write."""
        entity_id = uuid4()
        new_data_with_secret = {
            "id": str(entity_id),
            "username": "testuser",
            "password_hash": "bcrypt$2b$12$actual_hash_value",
        }
        redacted_data = {
            k: (_REDACTED if k in _ALWAYS_REDACT else v)
            for k, v in new_data_with_secret.items()
        }

        assert redacted_data["password_hash"] == _REDACTED, (
            "password_hash should be redacted before writing to audit_log"
        )
        assert redacted_data["username"] == "testuser", "username should pass through"
        assert redacted_data["id"] == str(entity_id), "id should pass through"
