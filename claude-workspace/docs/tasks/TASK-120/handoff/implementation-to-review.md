# TASK-120 — Implementation → Review handoff

**Date:** 2026-07-25
**Branch:** `fix/TASK-120-prescription-guards` (base `origin/dev` @ `c24f5fe`), pushed to origin.
**Commit:** `7b67cf4` — `fix(prescriptions): block mutation of pending prescriptions + item edit after invoice issued (TASK-120)`
**Worktree used:** `F:/MyProject/clinic-cms-workspace/_fix120-be` (left in place per contract; not cleaned up).

## Root causes recap

- **H-1:** `prescription_service.update()` / `add_item()` / `update_item()` only blocked mutation when `rx.status in ("dispensed", "cancelled")`. A `pending` prescription (already sent to pharmacy) was fully editable — PATCH notes, PATCH item quantity (which re-reserves stock via `reservation_service`), and POST a new item all succeeded with 200/201. This was asymmetric with `create_with_items`' re-save guard, which already 409s ("đã gửi nhà thuốc") instead of silently replacing a pending prescription.
- **H-4:** `update_item()` / `add_item()` had no invoice-issued guard. Invoices only snapshot prescription lines at generation time (`create_from_visit`) or on explicit resync (`refresh_from_visit`); changing an item's quantity, or adding a new item, after the invoice reached `issued`/`partially_paid`/`paid` never reached the invoice line — silent under/over-billing. TASK-108/M-9 added this exact guard to `visit_service_service.add_to_visit` (the *service* mutation path) but not to the prescription-item path.

## Fix

File: `app/modules/prescriptions/services/prescription_service.py` (+72 lines only, no deletions — existing `dispensed`/`cancelled` checks untouched).

Two new helpers, both placed just above `_resolve_dispense_source`:

- `_raise_if_pending(rx, action_vi)` — raises `ConflictError` (409) when `rx.status == "pending"`. Called (after the existing dispensed/cancelled check) from:
  - `update()` — header PATCH
  - `add_item()` — POST item
  - `update_item()` — PATCH item
  - `delete_item()` — DELETE item (**not explicitly named in the H-1 report, but added for consistency**: leaving delete callable on a pending prescription while every other mutation is blocked would just relocate the same asymmetry — flagging this extension explicitly for review in case it's considered scope creep).

- `_raise_if_invoice_issued(db, visit_id, clinic_id, action_vi)` (async) — mirrors `visit_service_service.add_to_visit`'s M-9 block byte-for-byte in approach: queries `Invoice.status in ("issued", "partially_paid", "paid")` for the visit, raises `ConflictError` (409) if found. Called from:
  - `add_item()`
  - `update_item()`

  **Not** added to `delete_item()` — deleting an item after invoice issuance has the same latent billing-drift risk (invoice keeps a line for a since-removed item) but wasn't part of the reported H-4 finding; flagging as a suggested follow-up rather than silently expanding this fix's blast radius further.

### H-4 approach: block vs resync

Chose **block (409)**, matching the TASK-108/M-9 precedent exactly, over auto-resync. Rationale: auto-resyncing an already-*issued* invoice's total behind the operator's back is itself a silent billing change (the customer may have already been shown/handed the printed invoice) — the existing pattern in this codebase is that only *draft* invoices auto-resync (via `create_with_items`'s best-effort draft-invoice sync block, untouched by this fix); anything past `draft` requires an explicit recall-to-draft or void/refund before the underlying visit data can change. Blocking keeps that invariant consistent instead of introducing a second, inconsistent resync behavior for prescriptions only.

## Tests

New file: `tests/integration/prescriptions/test_prescription_mutation_guards.py` (self-contained, mirrors fixture patterns in `test_prescription_service_coverage.py` / `test_billing_e2e.py`'s `_create_manual_invoice`). 8 tests, all passing:

- `TestH1PendingMutationGuard`: PATCH header / PATCH item qty / POST item / DELETE item on a `pending` prescription → all 409.
- `TestH4InvoiceIssuedGuard`: PATCH item qty after issued invoice → 409; POST item after issued invoice → 409; PATCH item qty with a **draft** invoice present → 200 (no-regression check — drafts still auto-resync).
- `TestDraftStillEditable`: draft prescription, no invoice at all — header PATCH, item PATCH, item POST all still succeed (200/201) — confirms no regression on the primary happy path.

### Test run (isolated stack `fix120`, api 9950 / pg 5450 / redis 6432, migrated to head 0069, then torn down)

```
tests/integration/prescriptions + tests/integration/billing (pre-existing, 71 tests): 71 passed
tests/integration/prescriptions/test_prescription_mutation_guards.py (new, 8 tests):    8 passed
Combined re-run: 79 passed, 0 failed
```

Docker was stable for this run — no recovery needed.

## Lint / type-check

- `ruff check app tests` — repo baseline has 453 pre-existing errors (unrelated legacy files, e.g. `tests/unit/vitals/test_validator.py`). Checked the two touched/created files in isolation:
  - `prescription_service.py`: 4 findings, all confirmed pre-existing on `origin/dev` (unrelated to this diff — an unsorted local-import block inside `create_with_items` at the old line ~253, and a `UP037`/`F821` forward-ref quirk in `to_response`'s return annotation, both outside the lines this fix touched). **0 new.**
  - `test_prescription_mutation_guards.py`: 1 import-order finding, auto-fixed with `ruff check --fix` (cosmetic only — removed a blank line before a comment block). Clean after fix.
- `mypy app` — 50 pre-existing errors baseline; the 1 hit in `prescription_service.py` is the same pre-existing `PrescriptionResponse` forward-ref issue noted above (confirmed present in `origin/dev` before this change). **0 new.**

## Not committed

`docker/docker-compose.fix120.yml` (isolated test-stack compose file, ports 9950/5450/6432) was created for the integration-test run but deliberately left **uncommitted**, matching the convention observed in prior fix worktrees (`_fix108-be`, `_fix117-be` never committed their `docker-compose.fixNNN.yml`). File remains on disk in the worktree if the reviewer wants to reuse the same stack.

## For the reviewer

1. Confirm the `delete_item` pending-guard extension (not in the literal H-1/H-4 report text) is acceptable, or ask for it to be reverted/split out.
2. Confirm block-over-resync for H-4 is the desired direction (see rationale above) — no other files needed changes (`api/routes.py` and `billing/services/invoice_service.py` were read but did not require edits; both already delegate the actual guard logic to the service layer / the guard reads `Invoice.status` directly rather than needing new invoice-service surface).
3. Optional follow-up (not in scope here): same invoice-issued guard on `delete_item`.
