# Handoff: TASK-121 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW

## Summary

Fixed bug H-2 in repo `clinic-cms` (backend), branch
`fix/TASK-121-recall-batch-500`, base `origin/dev` @ `c24f5fe` (head migration
`0069`).

`PATCH /inventory/batches/{id}` with `is_recalled=true` always returned 500.

## Root cause

`batch_service.update_batch` sets `b.recalled_at = datetime.now(UTC)` (a
`datetime`) when recalling a batch. `BatchResponse.recalled_at` was typed
`str | None`. `BatchResponse.model_validate(b)` (called from
`routes.update_batch`) failed pydantic v2's strict datetime->str coercion,
raising inside the request; `get_db` rolled back the transaction, so the
batch stayed `is_recalled=false`. PATCH requests touching only `unit_cost`
(never assigning `recalled_at`) never hit the code path that failed, so they
returned 200 — masking the bug.

## Fix

`app/modules/inventory/schemas/inventory_schemas.py`:
- `BatchResponse.recalled_at` changed from `str | None` to `datetime | None`,
  matching `Batch.recalled_at: Mapped[datetime | None]` in
  `app/modules/inventory/models/batch.py:49`.
- Added `datetime` to the `from datetime import date` import.

One-line-of-substance change; no other field touched.

## Files Changed

- `app/modules/inventory/schemas/inventory_schemas.py` — `BatchResponse.recalled_at` type fix.
- `tests/integration/inventory/test_inventory_e2e.py` — added `TestBatchRecallPatchRegression`
  (2 tests): recall PATCH returns 200 + persists `recalled_at`/`recalled_reason`/`is_recalled`;
  a follow-up `unit_cost`-only PATCH keeps `is_recalled`/`recalled_at` intact and still returns 200.

## Test Results

Isolated Docker stack `fix121` (api 9949 / postgres 5449 / redis 6431), built from
this worktree, migrated to head (0069) + demo-seeded via the standard
`docker-start.sh` entrypoint, torn down after (containers + volumes + image
removed). No other stack (`dev`/`w2e` 9999/5434/5436/6380/6382, or the
unrelated `fix120` stack already running on the host) was touched.

- Targeted: `pytest -q tests/integration/inventory` — **47/47 passed**
  (45 pre-existing + 2 new). New tests isolated via `-k Recall` — both pass
  standalone.
- `ruff check app/modules/inventory/schemas/inventory_schemas.py
  tests/integration/inventory/test_inventory_e2e.py`: 2 pre-existing findings
  (UP037 in `PurchaseInRequest.require_item_or_medicine`, I001 import-sort in
  the test file) — confirmed identical via `git stash` against unmodified
  `origin/dev` content. **0 new ruff errors.**
- `mypy app/modules/inventory`: 5 pre-existing errors (dosage_form.py,
  stocktake_service.py, purchase_in_service.py, routes.py x2), none in
  `inventory_schemas.py` — confirmed identical via `git stash` against
  unmodified `origin/dev`. **0 new mypy errors.**

## Note (infra, not committed)

The repo's `docker/docker-start.sh` has CRLF line endings as checked out on
this Windows host, which breaks `alembic upgrade head` (arg becomes literal
`"head\r"`) and the seed/demo steps when bind-mounted into the Linux
container. Converted to LF locally only to run the isolated stack for this
task; reverted before committing (not part of this fix, pre-existing on
`origin/dev`, out of scope for TASK-121). Flagging in case it blocks other
agents' Docker-based test runs — may warrant its own task (`.gitattributes`
entry or `dos2unix` step) if it recurs.

## Areas for Review Focus

- Confirm no other schema in the codebase has the same
  datetime-declared-as-`str`-in-response-schema pattern (sibling to
  TASK-096's `updated_at` bug and now this one) — worth a broader grep if
  reviewer has time, though out of scope for this targeted fix.
