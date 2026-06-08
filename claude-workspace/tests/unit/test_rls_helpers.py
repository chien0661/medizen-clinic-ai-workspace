"""Unit tests for app/core/rls.py — RLS migration helper functions.

These helpers are used exclusively in Alembic migrations (``upgrade``/
``downgrade``) and expect an ``alembic.operations.Operations`` (``op``)
object.  Tests use a mock to verify the correct SQL statements are issued
without requiring a live database or Alembic context.
"""

from __future__ import annotations

from unittest.mock import MagicMock, call

from app.core.rls import apply_rls_with_tenant_isolation, remove_rls


class TestApplyRLSWithTenantIsolation:
    def test_enables_rls_on_table(self):
        """apply_rls_with_tenant_isolation issues ALTER TABLE ENABLE ROW LEVEL SECURITY."""
        op = MagicMock()
        apply_rls_with_tenant_isolation(op, "patient")
        sql_calls = [str(c.args[0]).strip() for c in op.execute.call_args_list]
        assert any("ENABLE ROW LEVEL SECURITY" in s for s in sql_calls), (
            f"Expected ENABLE ROW LEVEL SECURITY, got: {sql_calls}"
        )

    def test_forces_rls_on_table(self):
        """apply_rls_with_tenant_isolation issues ALTER TABLE FORCE ROW LEVEL SECURITY."""
        op = MagicMock()
        apply_rls_with_tenant_isolation(op, "patient")
        sql_calls = [str(c.args[0]).strip() for c in op.execute.call_args_list]
        assert any("FORCE ROW LEVEL SECURITY" in s for s in sql_calls), (
            f"Expected FORCE ROW LEVEL SECURITY, got: {sql_calls}"
        )

    def test_creates_tenant_isolation_policy(self):
        """apply_rls_with_tenant_isolation creates the tenant_isolation policy."""
        op = MagicMock()
        apply_rls_with_tenant_isolation(op, "patient")
        sql_calls = " ".join(str(c.args[0]) for c in op.execute.call_args_list)
        assert "tenant_isolation" in sql_calls, (
            f"Expected 'tenant_isolation' policy, got: {sql_calls}"
        )
        assert "current_setting" in sql_calls, (
            "Policy must use current_setting for clinic context"
        )
        assert "app.current_clinic_id" in sql_calls, (
            "Policy must reference app.current_clinic_id"
        )

    def test_executes_three_statements(self):
        """apply_rls_with_tenant_isolation issues exactly 3 SQL statements."""
        op = MagicMock()
        apply_rls_with_tenant_isolation(op, "patient")
        assert op.execute.call_count == 3, (
            f"Expected 3 execute calls (ENABLE, FORCE, CREATE POLICY), "
            f"got {op.execute.call_count}"
        )

    def test_table_name_interpolated_correctly(self):
        """Table name appears in all SQL statements."""
        op = MagicMock()
        apply_rls_with_tenant_isolation(op, "visit")
        sql_calls = " ".join(str(c.args[0]) for c in op.execute.call_args_list)
        assert "visit" in sql_calls, (
            f"Expected table name 'visit' in SQL, got: {sql_calls}"
        )


class TestRemoveRLS:
    def test_drops_tenant_isolation_policy(self):
        """remove_rls drops the tenant_isolation policy."""
        op = MagicMock()
        remove_rls(op, "patient")
        sql_calls = " ".join(str(c.args[0]) for c in op.execute.call_args_list)
        assert "DROP POLICY IF EXISTS tenant_isolation" in sql_calls, (
            f"Expected DROP POLICY IF EXISTS, got: {sql_calls}"
        )

    def test_disables_force_rls(self):
        """remove_rls issues NO FORCE ROW LEVEL SECURITY."""
        op = MagicMock()
        remove_rls(op, "patient")
        sql_calls = " ".join(str(c.args[0]) for c in op.execute.call_args_list)
        assert "NO FORCE ROW LEVEL SECURITY" in sql_calls, (
            f"Expected NO FORCE ROW LEVEL SECURITY, got: {sql_calls}"
        )

    def test_disables_rls(self):
        """remove_rls issues DISABLE ROW LEVEL SECURITY."""
        op = MagicMock()
        remove_rls(op, "patient")
        sql_calls = " ".join(str(c.args[0]) for c in op.execute.call_args_list)
        assert "DISABLE ROW LEVEL SECURITY" in sql_calls, (
            f"Expected DISABLE ROW LEVEL SECURITY, got: {sql_calls}"
        )

    def test_executes_three_statements(self):
        """remove_rls issues exactly 3 SQL statements."""
        op = MagicMock()
        remove_rls(op, "patient")
        assert op.execute.call_count == 3, (
            f"Expected 3 execute calls (DROP POLICY, NO FORCE, DISABLE), "
            f"got {op.execute.call_count}"
        )

    def test_table_name_in_remove_sql(self):
        """Table name appears in all remove_rls SQL statements."""
        op = MagicMock()
        remove_rls(op, "prescription")
        sql_calls = " ".join(str(c.args[0]) for c in op.execute.call_args_list)
        assert "prescription" in sql_calls, (
            f"Expected table 'prescription' in remove SQL, got: {sql_calls}"
        )
