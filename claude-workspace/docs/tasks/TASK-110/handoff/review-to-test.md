# Handoff: TASK-110 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary
Invoice numbering race (M-20) fixed by replacing the `MAX(seq)+1` scan in `fn_next_invoice_number` with an atomic `invoice_number_counter` table (`INSERT ... ON CONFLICT DO UPDATE ... RETURNING`), mirroring the proven `fn_next_visit_number` (0010) pattern. Serialization and backfill both verified correct; single additive migration 0068, no app-code change.

## Key Findings
- MINOR: `SEED_COUNTER`'s `ON CONFLICT` clause is dead/defensive (GROUP BY yields unique keys into an empty table) — harmless, no change requested.
- Static analysis not re-run: host `ruff` binary is broken (`Exec format error`); please confirm ruff/mypy = 0 new inside the Docker stack.

## Focus Areas for Testing
- Run the migration end-to-end on a DB that already has issued invoices (and ideally recalled-draft and void invoices) for the same clinic+date, then issue a new invoice — confirm the new number is `MAX+1` with no collision against existing/void/recalled numbers.
- Re-run `TestConcurrentInvoiceNumbering` (2-way + 5-way) under the isolated stack; confirm all 200, all-distinct, no 500, and DB rows `status='issued'`.
- Confirm sequential monotonicity is preserved on the happy path.
- Verify `alembic upgrade head` reaches `0068` as single head and `alembic downgrade -1` restores the MAX-scan function and drops the counter table cleanly.
- Confirm full suite green aside from the 5 known pre-existing non-billing failures.
