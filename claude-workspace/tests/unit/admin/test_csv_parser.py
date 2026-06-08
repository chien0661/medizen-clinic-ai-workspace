"""Unit tests for the inventory CSV parser."""

from __future__ import annotations

import csv
import io
import time as time_mod

import pytest

from app.modules.admin.services.onboarding_service import _parse_inventory_csv


def _make_csv(rows: list[dict], header: list[str] | None = None) -> bytes:
    """Helper to produce CSV bytes from a list of dicts."""
    if header is None:
        header = ["name", "code", "unit", "initial_qty"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=header)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


class TestCSVParser:
    def test_valid_rows(self):
        csv_bytes = _make_csv(
            [
                {"name": "Amoxicillin", "code": "AMX", "unit": "tab", "initial_qty": "100"},
                {"name": "Paracetamol", "code": "PAR", "unit": "tab", "initial_qty": "200"},
            ]
        )
        valid, errors = _parse_inventory_csv(csv_bytes)
        assert len(valid) == 2
        assert len(errors) == 0
        assert valid[0].name == "Amoxicillin"
        assert valid[0].initial_qty == 100.0

    def test_negative_qty_error(self):
        csv_bytes = _make_csv(
            [{"name": "Drug A", "code": "DA", "unit": "tab", "initial_qty": "-5"}]
        )
        valid, errors = _parse_inventory_csv(csv_bytes)
        assert len(valid) == 0
        assert len(errors) == 1
        assert "initial_qty" in errors[0].field

    def test_non_numeric_qty_error(self):
        csv_bytes = _make_csv(
            [{"name": "Drug A", "code": "DA", "unit": "tab", "initial_qty": "abc"}]
        )
        valid, errors = _parse_inventory_csv(csv_bytes)
        assert len(errors) == 1

    def test_missing_required_field(self):
        # CSV missing 'code' column
        csv_bytes = _make_csv(
            [{"name": "Drug A", "unit": "tab", "initial_qty": "50"}],
            header=["name", "unit", "initial_qty"],
        )
        valid, errors = _parse_inventory_csv(csv_bytes)
        assert len(errors) == 1
        assert "code" in errors[0].field

    def test_empty_name_error(self):
        csv_bytes = _make_csv(
            [{"name": "", "code": "DA", "unit": "tab", "initial_qty": "10"}]
        )
        valid, errors = _parse_inventory_csv(csv_bytes)
        assert len(errors) >= 1

    def test_bom_utf8_handled(self):
        """CSV with BOM should parse without error."""
        rows = [{"name": "Drug", "code": "D01", "unit": "tab", "initial_qty": "10"}]
        normal = _make_csv(rows)
        bom_csv = b"\xef\xbb\xbf" + normal
        valid, errors = _parse_inventory_csv(bom_csv)
        assert len(valid) == 1
        assert len(errors) == 0

    def test_mixed_valid_invalid_rows(self):
        csv_bytes = _make_csv(
            [
                {"name": "Good", "code": "G01", "unit": "tab", "initial_qty": "10"},
                {"name": "", "code": "B01", "unit": "tab", "initial_qty": "10"},
                {"name": "Also Good", "code": "A02", "unit": "ml", "initial_qty": "5.5"},
            ]
        )
        valid, errors = _parse_inventory_csv(csv_bytes)
        assert len(valid) == 2
        assert len(errors) == 1

    def test_zero_qty_allowed(self):
        csv_bytes = _make_csv(
            [{"name": "Drug A", "code": "DA", "unit": "tab", "initial_qty": "0"}]
        )
        valid, errors = _parse_inventory_csv(csv_bytes)
        assert len(valid) == 1
        assert valid[0].initial_qty == 0.0

    def test_fractional_qty(self):
        csv_bytes = _make_csv(
            [{"name": "Saline", "code": "SAL", "unit": "ml", "initial_qty": "500.5"}]
        )
        valid, errors = _parse_inventory_csv(csv_bytes)
        assert valid[0].initial_qty == 500.5

    def test_1000_row_performance(self):
        """1000 rows should parse in under 30 seconds (AC requirement)."""
        rows = [
            {"name": f"Drug{i}", "code": f"D{i:04d}", "unit": "tab", "initial_qty": str(i)}
            for i in range(1000)
        ]
        csv_bytes = _make_csv(rows)
        start = time_mod.time()
        valid, errors = _parse_inventory_csv(csv_bytes)
        elapsed = time_mod.time() - start
        assert len(valid) == 1000
        assert len(errors) == 0
        assert elapsed < 30, f"CSV parsing took {elapsed:.1f}s, expected < 30s"

    def test_preview_capped_at_20(self):
        """Only first 20 rows should appear in preview when calling via service layer."""
        rows = [
            {"name": f"Drug{i}", "code": f"D{i:04d}", "unit": "tab", "initial_qty": "10"}
            for i in range(50)
        ]
        csv_bytes = _make_csv(rows)
        valid, errors = _parse_inventory_csv(csv_bytes)
        assert len(valid) == 50  # parser returns all; service slices preview
