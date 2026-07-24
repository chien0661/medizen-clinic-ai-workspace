# Review Report: TASK-108 — visit-service guards (M-8 + M-9)

**Reviewer**: Code Review Agent
**Date**: 2026-07-24
**Branch**: `fix/TASK-108-visit-service-guards` (base `origin/dev` @ `649bde4`, commit `54c31f1`)
**Diff**: `git -C F:/MyProject/clinic-cms-workspace/_fix108-be diff origin/dev...HEAD`
**Decision**: **APPROVED → IN_TESTING**

## Scope Reviewed

3 files, +219/-2:
- `app/modules/services/services/visit_service_service.py` (both fixes, inside `add_to_visit`)
- `tests/integration/services/test_services_e2e.py` (+2 tests, teardown fixture patch)
- `tests/unit/services/test_visit_service_service.py` (1 pre-existing mock repaired)

## M-8 — missing visit → 404 (not 500)

**Correct.** `add_to_visit` now calls `visit_service.get_visit(db, visit_id, clinic_id)`
as the first step (raises `NotFoundError` → 404 when absent), ahead of
`raise_if_visit_closed` and the insert. `visit_id` is a NOT NULL FK, so this
pre-empts the IntegrityError→500 at flush time.

`raise_if_visit_closed`'s "no-op on missing visit" contract is **untouched**
(confirmed at `visit_service.py:124-149` — docstring and body unchanged in the
diff; the existence check was added only at the `add_to_visit` call site).
Shared contract with prescriptions/vitals is preserved. ✅

## M-9 — block 409 when visit has an active (billed) invoice

**Decision (block 409, not stale-flag) — endorsed.** Rationale is sound:
no `stale`/`needs_refresh` column exists (a flag would need a migration and is
easy to ignore), and the codebase already treats an issued invoice as
line-immutable (`add_adjustment_line`/`delete_line`/`submit` reject non-draft
edits). Blocking mirrors that existing rule and points the operator at the
first-class escape hatch (`recall` → draft auto-resync, or void/refund).

### Status-set correctness — VERIFIED CORRECT

Full enum: `INVOICE_STATUSES = ("draft", "issued", "partially_paid", "paid", "void", "refunded")`
(`app/modules/billing/models/invoice.py:15`). The guard blocks exactly
`{issued, partially_paid, paid}`:

- `draft` — **not blocked** ✅ (editable; auto-resyncs at generation/refresh; pre-invoice add path untouched)
- `void`, `refunded` — **not blocked** ✅ (terminal/inactive; allows a fresh billing cycle post-void)
- `issued`, `partially_paid`, `paid` — **blocked** ✅ (money-relevant, line-locked states)

All 6 statuses accounted for; no over-block of legitimate flows.

**Minor note (not a defect):** the handoff says this "mirrors `create_from_visit`'s
idempotency check". That check uses `notin_(("void","refunded"))`
(`invoice_service.py:280`), which *includes* `draft`. The M-9 set deliberately
also excludes `draft`. Behaviorally M-9 is more precise and correct here (draft
must not block); only the prose comparison is slightly loose.

Query is tenant-scoped (`clinic_id`) and `is_deleted == False` filtered —
isolation preserved.

## Tests

- **M-8 test** (`test_add_service_to_unknown_visit_returns_404`): asserts 404 on `uuid4()` visit. ✅
- **M-9 test** (`test_add_service_to_visit_with_issued_invoice_blocked`): pre-invoice add → 201;
  generate+submit → issued (grand_total 150000); second add → **409**; invoice total
  re-fetched and **confirmed still 150000** (under-bill regression proof); recall → draft;
  add again → **201** (escape hatch). Genuinely asserts all required conditions. ✅
- **Unit mock repair**: `side_effect` list `[visit_exists, visit_status, no_active_invoice, svc]`
  matches the real call order in `add_to_visit`; guards pass as no-ops so the test again
  reaches the price-override spy it targets. Test-only, sound. ✅
- **Teardown fixture patch**: adds `payment`→`invoice_line`→`invoice` deletes before
  `visit`/`clinic` teardown. FK order correct (payment/invoice_line → invoice → visit/clinic).
  Pre-existing gap first exercised by the M-9 test (first to create a real invoice). Test-only, sound. ✅

Reported result: targeted suite **177/177 passed** (services + visits + billing + unit/services)
on isolated Docker stack `fix108`, torn down after run. No shared containers touched.

## Static Analysis

Host `ruff`/`mypy` could not run (`WinError 193` — documented broken host tooling).
Spot-checked the diff manually: clean, `# noqa: E712` correctly applied to the
`Invoice.is_deleted == False` comparison, imports (`select`, `ConflictError`)
already present at module top. Reported 0 new ruff/mypy errors on touched files
is consistent with inspection.

## Findings

| Severity | Finding |
|----------|---------|
| MINOR | `Invoice.is_deleted == False` (noqa'd) vs. `.is_(False)` used elsewhere in the codebase — style inconsistency only. |
| MINOR | Handoff prose overstates equivalence with `create_from_visit`'s idempotency set (that one includes `draft`); actual M-9 behavior is correct. |
| INFO | Two extra `db.execute` round-trips per add (visit-exists, active-invoice) — acceptable, not a hot path. |

No CRITICAL or MAJOR issues.

## Quality Gates

- [x] No critical/major issues
- [x] Fixes correct and well-scoped (M-8 + M-9)
- [x] M-9 status set verified complete and correct
- [x] Tests genuinely assert both cases + no-regression
- [x] Test-only changes (mock + teardown) confirmed sound
- [~] Lint/type: host tooling broken; verified by inspection (see above)

**APPROVED.**
