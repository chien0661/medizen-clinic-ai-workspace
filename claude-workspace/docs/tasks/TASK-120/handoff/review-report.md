# TASK-120 — Review Report

**Reviewer:** Code Review Agent
**Date:** 2026-07-26
**Branch:** `fix/TASK-120-prescription-guards` @ `7b67cf4` (base `origin/dev` @ `c24f5fe`)
**Worktree:** `F:/MyProject/clinic-cms-workspace/_fix120-be`
**Diff scope:** `prescription_service.py` (+72), `test_prescription_mutation_guards.py` (+432). No other files touched.

## Decision: APPROVED → IN_TESTING

No CRITICAL or MAJOR issues. Two guards implemented correctly and consistently with existing precedent; tests are genuine.

---

## Verification

### H-1 — pending mutation guard (coverage of all entry points)
`_raise_if_pending(rx, action_vi)` raises `ConflictError` (409) when `rx.status == "pending"`, called after the existing `dispensed`/`cancelled` `BusinessRuleError` check in:

| Entry point | Guarded | In H-1 report? |
|---|---|---|
| `update()` (PATCH prescription header) | ✅ | yes |
| `add_item()` (POST item) | ✅ | yes |
| `update_item()` (PATCH prescription-item) | ✅ | yes |
| `delete_item()` (DELETE item) | ✅ | no — documented cohesion extension |

All three reported mutation entry points covered. The `delete_item` extension is a sound cohesion decision (leaving delete callable on a pending Rx would relocate the same asymmetry); implementer flagged it explicitly. `draft` passes the guard unchanged. Behavior now matches `create_with_items`' existing re-save 409 ("đã gửi nhà thuốc"). **Confirmed.**

### H-4 — invoice-issued guard (status set)
`_raise_if_invoice_issued(db, visit_id, clinic_id, action_vi)` queries `Invoice.status` for the visit, blocking `("issued", "partially_paid", "paid")`, called in `add_item()` and `update_item()`. Verified **byte-for-byte equivalent** to the TASK-108/M-9 precedent in `app/modules/services/services/visit_service_service.py::add_to_visit` (same status tuple, same `is_deleted == False`, same `scalar_one_or_none`, same `ConflictError`).

- Blocked: issued / partially_paid / paid ✅
- Allowed (not in set): draft (auto-resyncs elsewhere), void, refunded ✅
- `visit_id is None` → early return (no over-block of visit-less prescriptions) ✅

Status-set verdict: **correct and consistent with TASK-108.** Block-over-resync direction is the right call — matches the codebase invariant that only draft invoices auto-resync; issued+ requires explicit recall/void. **Confirmed.**

### Guard composition
In `update_item`/`add_item` the order is: `dispensed/cancelled` → `_raise_if_pending` → `raise_if_visit_closed` → `_raise_if_invoice_issued`. A **pending** prescription on an **issued-invoice** visit short-circuits at `_raise_if_pending` → 409 with the pending message. Still blocked, clear error. The H-4 tests deliberately use a *draft* (unsubmitted) prescription so the invoice guard is exercised independently. **Confirmed.**

### Tests (8, `test_prescription_mutation_guards.py`)
- `TestH1PendingMutationGuard`: PATCH header / PATCH item qty / POST item / DELETE item on pending → all assert 409 (4).
- `TestH4InvoiceIssuedGuard`: PATCH item qty after issued → 409; POST item after issued → 409; PATCH item qty with **draft** invoice → 200 (no-regression) (3).
- `TestDraftStillEditable`: draft Rx, no invoice — PATCH header / PATCH item / POST item → 200/201 (1).

Assertions are real (status-code + `.text` on failure), fixtures self-contained. Both guards and the draft-allowed happy path are genuinely exercised. **Confirmed.**

### Checks run
- `git diff origin/dev...HEAD --unified=3` — reviewed full diff.
- Cross-referenced M-9 precedent guard — byte-for-byte match confirmed.
- Verified all identifiers used by new helpers are imported at module top (`ConflictError`, `select`, `AsyncSession`, `Prescription`, `UUID`); `Invoice` imported locally with `noqa: PLC0415`.
- `ruff` / `mypy` **could not run on host** (`ruff` binary: "Exec format error"; host tooling broken as warned). Spot-check: both changed files pass `ast.parse` (UTF-8) cleanly. Handoff claims 0 new ruff/mypy findings — plausible and consistent with the diff (no unusual constructs). Rely on documented isolated-stack run (79 passed) + Test Agent re-run.

---

## Findings

### MINOR
1. **No dedicated compose test** (pending Rx + issued invoice). Outcome is guaranteed by guard ordering (pending 409 fires first), but an explicit test would document the intent. Suggest Test Agent add one.
2. **`delete_item` has no invoice-issued guard** (implementer-flagged follow-up). Deleting a prescription-item after invoice issuance leaves the invoice line orphaned — same latent billing-drift class as H-4, but outside the reported H-4 scope. Track as a separate follow-up task, not a blocker here.

No CRITICAL/MAJOR issues.

---

## Quality Gates
- [x] No critical/major issues
- [x] Guards cover all reported entry points + consistent with precedent
- [x] Tests genuine, cover both guards + no-regression paths
- [~] Lint/type-check: host tooling broken — static spot-check clean; 0-new claim relied upon + deferred to Test Agent
- [ ] Full suite re-run: deferred to Test Agent (Docker-dependent; documented run = 79 passed)
