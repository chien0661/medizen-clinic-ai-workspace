"""Unit tests for settings_service deep-merge logic (no DB)."""

from __future__ import annotations

from app.modules.admin.services.settings_service import _deep_merge


class TestDeepMerge:
    def test_flat_override(self):
        base = {"a": 1, "b": 2}
        patch = {"b": 99}
        result = _deep_merge(base, patch)
        assert result == {"a": 1, "b": 99}

    def test_nested_merge(self):
        base = {"appointment": {"slot_duration_minutes": 30, "allow_walk_in": True}}
        patch = {"appointment": {"slot_duration_minutes": 20}}
        result = _deep_merge(base, patch)
        assert result["appointment"]["slot_duration_minutes"] == 20
        assert result["appointment"]["allow_walk_in"] is True  # preserved

    def test_new_key_added(self):
        base = {"a": 1}
        patch = {"b": 2}
        result = _deep_merge(base, patch)
        assert result == {"a": 1, "b": 2}

    def test_does_not_mutate_base(self):
        base = {"a": {"x": 1}}
        original_ref = base["a"]
        _deep_merge(base, {"a": {"x": 99}})
        # original base should be unchanged
        assert base["a"]["x"] == 1
        assert original_ref["x"] == 1

    def test_none_value_skipped(self):
        base = {"a": 1}
        patch = {"a": None}
        result = _deep_merge(base, patch)
        # None values should not overwrite existing values
        assert result["a"] == 1

    def test_deep_nested(self):
        base = {"a": {"b": {"c": 1, "d": 2}}}
        patch = {"a": {"b": {"c": 99}}}
        result = _deep_merge(base, patch)
        assert result["a"]["b"]["c"] == 99
        assert result["a"]["b"]["d"] == 2  # preserved
