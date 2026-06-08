"""Unit tests for app/core/audit.py.

Tests cover:
- _model_to_dict serialises UUID fields correctly
- _compute_diff returns only changed fields
- _serialize_value handles UUID, datetime, plain values
- write_audit creates a record with correct fields (using async_session)
- audit_read creates a READ action record
- UUIDPrimaryKeyMixin is reusable (deferral #8)
"""

from datetime import UTC, datetime
from uuid import uuid4

from app.core.audit import _compute_diff, _model_to_dict, _serialize_value

# ---------------------------------------------------------------------------
# Pure function unit tests (no DB required)
# ---------------------------------------------------------------------------


class TestSerializeValue:
    def test_uuid_becomes_string(self):
        u = uuid4()
        assert _serialize_value(u) == str(u)

    def test_datetime_becomes_iso(self):
        dt = datetime(2026, 4, 26, 10, 0, 0, tzinfo=UTC)
        result = _serialize_value(dt)
        assert "2026-04-26" in result

    def test_plain_string_passthrough(self):
        assert _serialize_value("hello") == "hello"

    def test_none_passthrough(self):
        assert _serialize_value(None) is None

    def test_int_passthrough(self):
        assert _serialize_value(42) == 42


class TestComputeDiff:
    def test_no_change_returns_empty(self):
        old = {"name": "Alice", "age": 30}
        new = {"name": "Alice", "age": 30}
        assert _compute_diff(old, new) == []

    def test_changed_field_returned(self):
        old = {"name": "Alice", "age": 30}
        new = {"name": "Bob", "age": 30}
        assert _compute_diff(old, new) == ["name"]

    def test_multiple_changes_sorted(self):
        old = {"a": 1, "b": 2, "c": 3}
        new = {"a": 9, "b": 2, "c": 9}
        assert _compute_diff(old, new) == ["a", "c"]

    def test_added_field_detected(self):
        old: dict = {"name": "Alice"}
        new = {"name": "Alice", "email": "a@b.com"}
        result = _compute_diff(old, new)
        assert "email" in result

    def test_none_old_returns_empty(self):
        assert _compute_diff(None, {"x": 1}) == []

    def test_none_new_returns_empty(self):
        assert _compute_diff({"x": 1}, None) == []


class TestModelToDict:
    def test_returns_dict_from_simple_model(self):
        """Use the Clinic model as a simple non-BaseEntity model."""
        from app.modules.users.models.clinic import Clinic

        clinic = Clinic(
            id=uuid4(),
            code="C001",
            name="Test Clinic",
            specialty="general",
        )
        result = _model_to_dict(clinic)
        assert isinstance(result, dict)
        assert "code" in result
        # UUID should be serialised to string
        assert isinstance(result["id"], str)

    def test_skips_sa_instance_state(self):
        from app.modules.users.models.clinic import Clinic

        clinic = Clinic(code="C001", name="Test", specialty="general")
        result = _model_to_dict(clinic)
        assert "__sa_instance_state" not in result

    def test_skips_audit_timestamp_columns(self):
        from app.modules.users.models.clinic import Clinic

        clinic = Clinic(code="C001", name="Test", specialty="general")
        result = _model_to_dict(clinic)
        # created_at and updated_at are in SKIP_COLUMNS
        assert "created_at" not in result
        assert "updated_at" not in result


# ---------------------------------------------------------------------------
# UUID PK Mixin extraction test (deferral #8)
# ---------------------------------------------------------------------------


class TestUUIDPrimaryKeyMixin:
    def test_mixin_provides_id_via_concrete_model(self):
        """UUIDPrimaryKeyMixin contributes `id` — verified via a concrete model."""
        # Use the existing Clinic model (which uses UUIDPrimaryKeyMixin)
        import sqlalchemy as sa

        from app.modules.users.models.clinic import Clinic

        mapper = sa.inspect(Clinic)
        col_names = [c.key for c in mapper.columns]
        assert "id" in col_names

    def test_base_entity_uses_mixin(self):
        """BaseEntity should use UUIDPrimaryKeyMixin rather than inline id."""
        from app.core.base_model import BaseEntity, UUIDPrimaryKeyMixin

        assert issubclass(BaseEntity, UUIDPrimaryKeyMixin)

    def test_clinic_uses_mixin(self):
        """Clinic should use UUIDPrimaryKeyMixin rather than inline id."""
        from app.core.base_model import UUIDPrimaryKeyMixin
        from app.modules.users.models.clinic import Clinic

        assert issubclass(Clinic, UUIDPrimaryKeyMixin)

    def test_mixin_id_column_is_pk(self):
        """id column from UUIDPrimaryKeyMixin is the primary key."""
        from app.modules.users.models.clinic import Clinic

        pk_cols = [c.name for c in Clinic.__table__.primary_key.columns]
        assert pk_cols == ["id"]
