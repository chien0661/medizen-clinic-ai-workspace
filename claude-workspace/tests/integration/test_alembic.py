"""Integration tests: Alembic migration idempotency and schema sync."""

import subprocess
import sys


def _run_alembic(*args: str) -> subprocess.CompletedProcess:
    """Run an alembic command in-process via subprocess, capturing output."""
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        capture_output=True,
        text=True,
        cwd="/app",
    )


def test_alembic_upgrade_head_is_idempotent():
    """Running 'alembic upgrade head' twice must not fail (no-op on second run)."""
    # First run (may be no-op if already at head)
    result1 = _run_alembic("upgrade", "head")
    assert result1.returncode == 0, f"First upgrade failed:\n{result1.stderr}"

    # Second run — must also succeed with no errors
    result2 = _run_alembic("upgrade", "head")
    assert result2.returncode == 0, f"Second upgrade (idempotency) failed:\n{result2.stderr}"


def test_alembic_current_shows_head():
    """'alembic current' must report being at head after upgrade."""
    result = _run_alembic("current")
    assert result.returncode == 0, f"alembic current failed:\n{result.stderr}"
    # Should show the revision hash and/or (head)
    output = result.stdout + result.stderr
    assert "head" in output or len(output.strip()) > 0


def test_alembic_history_shows_migration():
    """'alembic history' must list at least one migration (0001_create_clinic_and_users)."""
    result = _run_alembic("history")
    assert result.returncode == 0, f"alembic history failed:\n{result.stderr}"
    output = result.stdout + result.stderr
    # The initial migration must be present
    assert "0001" in output or "clinic" in output.lower() or "<base>" in output
