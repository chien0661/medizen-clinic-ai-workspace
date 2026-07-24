# Handoff: TASK-108 → Code Review

**From**: Code Implementation Agent (FIX MODE)
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-07-24
**Branch**: `fix/TASK-108-visit-service-guards` (base `origin/dev` @ `649bde4`, alembic head 0067)
**Commit**: `54c31f1`

## Summary

Two edge-case bugs in the add-service-to-visit path (`add_to_visit`), both
found in TASK-095 E2E (M-8, M-9).

## M-8 — `POST /visits/{unknown}/services` 500 → 404

`add_to_visit` called `visit_service.raise_if_visit_closed()` (a documented
no-op when the visit is missing — shared contract with prescriptions/vitals,
see its docstring) and then inserted `VisitService` directly. `visit_id` is a
NOT NULL FK, so a nonexistent visit surfaced as an unhandled `IntegrityError`
→ 500 at flush time.

**Fix**: added `await visit_service.get_visit(db, visit_id, clinic_id)` (404
if missing) as a new, separate first step in `add_to_visit`, ahead of the
existing `raise_if_visit_closed` closed-visit check. `raise_if_visit_closed`
itself is untouched — its no-op-on-missing contract is relied on by
prescriptions/vitals and must not change.

## M-9 — billable service added after invoice ISSUED → silent under-billing

`raise_if_visit_closed`'s `CLOSED_STATUSES` is `{COMPLETED, CANCELLED}` only
(by design — `AWAITING_PAYMENT` stays editable "until money is collected").
But invoices snapshot `visit_service` lines only at generation
(`create_from_visit`) or explicit resync (`refresh_from_visit`) — a service
added to the visit *after* the invoice is issued never reaches it. Evidence
from E2E: invoice ISSUED grand_total=219000, added a 150000 service, invoice
stayed at 219000 with no warning anywhere.

### Decision (flagged for review): block (409), not a stale-flag/warning

Considered per the task: block outright vs. mark the invoice
stale/needs-refresh and surface a warning. Chose **block**:

- No schema support for a stale flag today (`Invoice` has no
  `stale`/`needs_refresh` column) — adding one is a migration, out of
  proportion for this fix, and a flag is easy to silently ignore anyway.
- The codebase already treats an issued invoice as line-immutable elsewhere
  — `add_adjustment_line`, `delete_line`, and `submit` all reject edits to a
  non-draft invoice with a `BusinessRuleError`/409. Blocking the
  visit-service side mirrors the same rule instead of introducing a second,
  weaker convention.
- There's already a first-class escape hatch that does exactly the right
  thing: `POST /invoices/{id}/recall` (issued + unpaid → back to `draft`,
  which auto-resyncs its lines on the next `refresh_from_visit`/generation
  path), or void/refund for a paid one. The 409 message points the operator
  at this directly instead of inventing new machinery.

**Implementation**: `add_to_visit` now queries for an active invoice
(`Invoice.status in {"issued", "partially_paid", "paid"}`, excluding
`void`/`refunded` — same "active invoice" definition already used by
`create_from_visit`'s idempotency check) for the visit. If found, raises
`ConflictError` (409) before any insert. Draft invoices (or no invoice yet)
are unaffected — the common pre-invoice add path is untouched.

## Files Changed

- `app/modules/services/services/visit_service_service.py` — both fixes,
  inside `add_to_visit`. No changes to `visit_service.py` (reused existing
  `get_visit`/`raise_if_visit_closed`) or `invoice_service.py` (reused
  existing `recall`) — task listed them as candidate files but neither
  needed edits once M-8/M-9 were localized to the call site.
- `tests/integration/services/test_services_e2e.py` — 2 new tests:
  - `test_add_service_to_unknown_visit_returns_404` (M-8).
  - `test_add_service_to_visit_with_issued_invoice_blocked` (M-9): pre-invoice
    add → 201; generate + submit invoice; second add → 409; invoice total
    confirmed unchanged (219000-style regression proof); recall → draft;
    add again → 201 (escape hatch works).
  - Also patched the shared `svc_ctx` teardown fixture: it was missing
    `payment`/`invoice_line`/`invoice` deletes before the `visit`/`clinic`
    deletes, which FK-violated once a test in this file actually generated
    an invoice (none had before). Pre-existing gap, not a new regression —
    just never exercised until now.
- `tests/unit/services/test_visit_service_service.py` — fixed 1 test broken
  by the new code path:
  `test_check_price_override_receives_clinic_id_in_add_to_visit` mocked
  `db.execute` with one fixed return value for every call. `add_to_visit`
  now issues 2 more queries (visit-exists, active-invoice) before reaching
  the price-override permission check under test, so the single mock value
  got consumed by the wrong query and the M-9 guard fired first (409) before
  the permission-check spy ever ran. Rewrote the mock as a `side_effect`
  list matching the real call order (visit exists/not-closed → no active
  invoice → service lookup) so the test again reaches and exercises the
  permission-check spy it's actually testing.

## Test Results

Isolated Docker stack `fix108` (postgres 5472, redis 6454, api 9972 —
built from the repo's own `Dockerfile`), migrated to alembic head `0067`,
stack torn down after the run (`docker compose -p fix108 down -v`); no
w2e/main/dev containers touched.

**Targeted suite — 177/177 passed**:
`tests/integration/services/` + `tests/integration/visits/` +
`tests/integration/billing/` + `tests/unit/services/`.

Includes the 2 new M-8/M-9 tests, the regression check on the normal
pre-invoice add path, the existing closed-visit 409 test
(`test_add_service_blocked_on_cancelled`, visit forced CANCELLED —
unaffected since that visit still exists), and the full existing
billing/invoice-lifecycle suite (recall, refund, void, payment) to confirm
the new active-invoice query doesn't regress any of that.

A full-repo `pytest -q` run was also started for extra confidence but the
isolated stack was torn down before it finished — several pre-existing
failures unrelated to this change appeared early in the run (this repo has
known DEK/RLS-setup flakiness per project memory); the targeted, complete
177/177 run above is the authoritative result for this change.

## Static Analysis

- `ruff check` on all 3 touched files → **0 errors** (repo-wide baseline:
  452 pre-existing errors elsewhere, unrelated).
- `mypy` on all 3 touched files → **0 errors** (repo-wide baseline: 56
  pre-existing errors elsewhere — `format_currency_vn`/Decimal typing,
  `app/main.py` return types, etc. — none in touched files).

## Review Focus Suggested

1. M-9 decision (block vs. stale-flag) — is 409 the right call, or should a
   product-level warning path be preferred instead? (Documented rationale in
   `task.md` "Implementation Notes" and above.)
2. Whether the "active invoice" status set (`issued`, `partially_paid`,
   `paid`) is the right boundary — confirm `void`/`refunded` should *not*
   block a fresh add (mirrors `create_from_visit`'s own idempotency check).
3. The two added `db.execute` calls in `add_to_visit` (visit-exists,
   active-invoice) are extra round-trips on every add — acceptable given
   this isn't a hot/bulk path, but flagging for awareness.
