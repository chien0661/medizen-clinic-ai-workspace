# TASK-110 — Implementation → Review handoff

**Branch:** `fix/TASK-110-invoice-number-serialize` (base `origin/dev` @ 649bde4, alembic head 0067 → 0068)
**Commit:** `699c7aa` — pushed to `origin/fix/TASK-110-invoice-number-serialize`
**Worktree:** `F:/MyProject/clinic-cms-workspace/_fix110-be` (dedicated, left in place)

## Bug (M-20)

`fn_next_invoice_number` (0053) computed the next sequence with `SELECT MAX(seq)+1`
and no locking. Two concurrent invoice submits for the same clinic+date could read
the same MAX and compute the same number. One `INSERT`/`UPDATE` succeeded; the other
hit `uq_invoice_clinic_number` and surfaced as a 500, with the losing invoice rolled
back to draft (empty `invoice_number`). Multi-cashier issuing makes this routine, not
an edge case.

## Fix

Mirrors the existing visit-numbering pattern (`0010_create_visits.py` /
`fn_next_visit_number`):

- New table `invoice_number_counter (clinic_id, invoice_date, last_seq)`,
  PK `(clinic_id, invoice_date)`, FK → `clinic.id` `ON DELETE RESTRICT`, RLS via
  `apply_rls_with_tenant_isolation` (same policy shape as `visit_number_counter`).
- `fn_next_invoice_number` rewritten to:
  ```sql
  INSERT INTO invoice_number_counter (clinic_id, invoice_date, last_seq)
  VALUES (p_clinic_id, p_date, 1)
  ON CONFLICT (clinic_id, invoice_date)
  DO UPDATE SET last_seq = invoice_number_counter.last_seq + 1
  RETURNING last_seq INTO v_seq;
  ```
  The `ON CONFLICT` upsert takes an implicit row lock on the `(clinic_id, date)`
  counter row, held for the lifetime of the caller's transaction. Since each
  request runs in exactly one transaction (`app/core/db.py::get_db` commits once
  at the end), concurrent submits for the same clinic+date serialize on that one
  row and each returns a distinct, strictly increasing `last_seq` — no scan, no
  race window.
- **Backward compatibility:** migration seeds the counter from
  `MAX(seq)` already in use per `(clinic_id, date)`, parsed out of existing
  `invoice_number` values, so newly issued numbers never collide with numbers
  assigned by the old MAX-scan function.
- **Downgrade:** restores the pre-0068 MAX-scan function verbatim and drops the
  counter table + its RLS policies.

`invoice_service.py` (submit flow) was **not modified** — it already calls
`fn_next_invoice_number` via `SELECT fn_next_invoice_number(:clinic_id, :date)`
inside the same DB session/transaction as the invoice row update, which is exactly
what the new locking mechanism requires. No app-layer change was needed.

## Files changed

- `alembic/versions/0068_invoice_number_counter.py` (new) — revises `0067`, single
  head confirmed (`alembic heads` → `0068 (head)`).
- `tests/integration/billing/test_billing_e2e.py` — added `TestConcurrentInvoiceNumbering`
  with 3 tests (below). No other files touched.

## Tests

Ran in isolated Docker stack `fix110` (compose file `docker/docker-compose.fix110.yml`,
**not committed** — untracked scratch stack, same convention as prior fix branches
e.g. `_fix108-be/docker/docker-compose.fix108.yml`). Ports: api 9970, postgres 5470,
redis 6452 — distinct from shared dev stack (9999/5434/6380) and w2e (5436/6382) per
guardrails. Migrated to head, ran tests, tore down stack + volumes afterward.

New tests (`tests/integration/billing/test_billing_e2e.py::TestConcurrentInvoiceNumbering`):

1. `test_two_concurrent_submits_get_distinct_numbers` — 2 draft invoices submitted via
   `asyncio.gather` on 2 independent `AsyncClient`s → both 200, 2 distinct `INV-` numbers.
2. `test_five_concurrent_submits_all_distinct_and_successful` — 5-way version, higher
   contention → all 200, 5 distinct numbers, DB-verified all 5 rows `status='issued'`.
3. `test_sequential_submits_still_monotonic` — sanity check that non-concurrent
   submits remain strictly increasing (no regression on the happy path).

Results:

- `tests/integration/billing/test_billing_e2e.py` — **25/25 passed** (22 pre-existing +
  3 new concurrency tests).
- Full sweep — `tests/integration/billing/` + `tests/integration/visits/` + `tests/unit/`
  → **1080 passed**, 5 pre-existing failures unrelated to this change and unrelated to
  billing/invoice code (`test_email.py` template rendering, `test_erasure_service.py`
  `last_accessed_at`, `test_feature_flags.py` unknown-flag case, 2x `test_rls_helpers.py`
  stale call-count assertions expecting 3 `execute` calls vs the current 4 — these
  helpers weren't touched by this fix and the assertions are already stale against
  `app/core/rls.py` as it exists on `dev`).

## Static analysis

- `ruff check app tests`: 452 pre-existing baseline errors repo-wide; **0 new**. The
  new migration file is ruff-clean (`--fix` applied once, for import ordering only,
  no logic change). The modified test file's 4 pre-existing errors (unsorted imports,
  2 unused imports, 1 unused local at an unrelated test) are unchanged — confirmed
  present in the file at `origin/dev` HEAD before this change.
- `mypy app`: 50 pre-existing baseline errors; **0 new** — `app/` was not modified by
  this fix (only `alembic/versions/` and `tests/` changed), so the count is identical
  to the `origin/dev` baseline.

## Status

`docs/tasks/TASK-110/task.md` → `IN_REVIEW`, assigned Code Review Agent.
