# Review Report — TASK-110 (M-20: invoice numbering race)

**Reviewer:** Code Review Agent
**Date:** 2026-07-24
**Branch:** `fix/TASK-110-invoice-number-serialize` (base `origin/dev` @ 649bde4)
**Commit under review:** `699c7aa`
**Decision:** **APPROVED → IN_TESTING**

## Scope reviewed
Diff `git diff origin/dev...HEAD` — 2 files, +280 lines, no deletions, no app code changed:
- `alembic/versions/0068_invoice_number_counter.py` (new, 152 lines)
- `tests/integration/billing/test_billing_e2e.py` (+128 lines, `TestConcurrentInvoiceNumbering`)

## Findings by severity
- **CRITICAL:** none.
- **MAJOR:** none.
- **MINOR (1):** `SEED_COUNTER` carries an `ON CONFLICT ... DO UPDATE SET last_seq = GREATEST(...)` clause that cannot fire — the `GROUP BY clinic_id, date` guarantees unique keys into a freshly-created empty table. Harmless/defensive; no change required.

## Serialization correctness — VERDICT: CORRECT
- `fn_next_invoice_number` rewritten to `INSERT ... ON CONFLICT (clinic_id, invoice_date) DO UPDATE SET last_seq = last_seq + 1 RETURNING last_seq` — byte-for-byte the same mechanism as `fn_next_visit_number` (0010), which is the proven race-safe pattern in this codebase.
- The `ON CONFLICT DO UPDATE` acquires a row-level lock on the `(clinic_id, invoice_date)` counter row. PostgreSQL `INSERT ... ON CONFLICT` is atomic against concurrent inserts of a not-yet-existing key (one inserts, the other blocks then takes the UPDATE path), so both the "first number of the day" and the "existing counter" cases serialize with no gap.
- One-txn-per-request confirmed in `app/core/db.py::get_db` (lines 121-129): the session is opened, yielded, and `commit()` runs exactly once at request end. The counter-row lock is therefore held from number assignment until the invoice row is committed — no window where a second txn can read the same `last_seq`.
- Call site `invoice_service.py::submit` (lines 540-548) executes `SELECT fn_next_invoice_number(...)` on the same `db` session as the invoice `flush()` (line 554) — inside the one request transaction. No app change was needed and none was made. The recall/re-issue path (line 540-541) reuses the already-allocated number and never calls the function, so it introduces no second allocation.
- Each call returns a strictly increasing distinct integer; the `uq_invoice_clinic_number` partial unique index remains as a backstop. No residual collision path identified.

## Backfill correctness — VERDICT: CORRECT (no off-by-one)
- Old (0053, current live) function returns `MAX(existing seq) + 1`. Seed sets `last_seq = MAX(existing seq)`; the new function's first post-seed call returns `last_seq + 1 = MAX + 1`. Identical successor — no reissue of an existing number, no gap, no reset.
- Date with no prior invoices: no counter row seeded → first `INSERT` returns `1` → `INV-YYYYMMDD-001`. Matches old behaviour (`MAX(∅)=0 → 1`).
- Seed regex `^INV-(\d{8})-(\d+)$` matches the exact `INV-YYYYMMDD-NNN` format; date key derived from the parsed number equals the `p_date` embedded when the number was minted, so counter keys line up with historical numbers.
- Filter parity: seed uses `is_deleted = false` + `LIKE 'INV-%'`, matching the old MAX-scan filter. It therefore includes recalled-draft numbers and void numbers (both retain their number and occupy the partial unique index), so newly issued numbers cannot collide with them. Behaviour consistent with the pre-fix function — no regression.

## Migration hygiene — CORRECT
- Additive: `create_table` + RLS + seed + function replace; no destructive op on existing data.
- Single head confirmed by grep: only `0068` declares `down_revision = "0067"`, and nothing declares `down_revision = "0068"`. (`alembic heads` per host was unavailable; verified structurally.)
- RLS: `apply_rls_with_tenant_isolation` + `GRANT ... TO cms_app`, same shape as `visit_number_counter`.
- Downgrade restores the pre-0068 MAX-scan function verbatim (matches 0053's installed body), then `remove_rls` + `drop_table` in a safe order (restored function no longer references the counter).

## Tests
- `TestConcurrentInvoiceNumbering` genuinely asserts the acceptance criteria: 2-way and 5-way `asyncio.gather` submits on independent `AsyncClient`s assert **all 200** (no duplicate-number 500), **N distinct `INV-` numbers** via `len(set(...)) == N`, and the 5-way test DB-verifies all rows persisted `status='issued'`. Sequential test asserts strict monotonicity (happy-path regression guard).
- Reported results: billing suite 25/25 (22 + 3 new); full sweep 1080 passed, 5 pre-existing failures in untouched non-billing modules (email templates, erasure `last_accessed_at`, feature flags, 2× stale `test_rls_helpers` call-count) — plausible and unrelated to this change.

## Checks run
- Full diff review (`--unified=3`).
- Cross-referenced reference pattern `0010_create_visits.py::fn_next_visit_number`.
- Verified one-txn-per-request in `app/core/db.py::get_db`.
- Verified call site `invoice_service.py::submit`.
- Verified `uq_invoice_clinic_number` is a partial unique index (`0019_create_invoices.py`).
- Verified single alembic head structurally (grep on `down_revision`).
- Confirmed downgrade function matches the current live (0053) MAX-scan body.
- **ruff/mypy:** host `ruff` binary broken (`Exec format error`) — could not re-run; static-analysis claims (0 new) accepted on the basis that only `alembic/versions/` + `tests/` changed and the new file matches established style. Test Agent runs inside the Docker stack where tooling works.

## Quality gate summary
No critical/major issues; mechanism proven-correct and mirrors an existing safe pattern; backfill is collision-free; concurrency tests meaningful. Approved for testing.
