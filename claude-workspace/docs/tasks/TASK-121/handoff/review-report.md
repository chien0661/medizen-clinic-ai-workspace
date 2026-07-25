# Review Report: TASK-121 — Recall batch PATCH always 500 (H-2)

**Reviewer**: Code Review Agent
**Date**: 2026-07-26
**Branch**: `fix/TASK-121-recall-batch-500` (off `origin/dev` `c24f5fe`)
**Commit**: `aa112fd`
**Worktree**: `F:/MyProject/clinic-cms-workspace/_fix121-be`

## Decision: APPROVED → IN_TESTING

## Summary

Single type fix: `BatchResponse.recalled_at` retyped `str | None` → `datetime | None`
to match `Batch.recalled_at: Mapped[datetime | None]` (model `batch.py:49`). This
removes the pydantic v2 datetime→str coercion crash that made
`PATCH /inventory/batches/{id}` with `is_recalled=true` raise inside the request and
roll back (`get_db`), leaving the batch `is_recalled=false`. Sibling of TASK-096.

Root cause verified: `batch_service.update_batch` (line 130) sets
`b.recalled_at = datetime.now(UTC)` only on the recall branch; the `elif unit_cost`
branch never touches it — which is exactly why unit_cost-only PATCH masked the bug.

## Type-consistency verdict: CONSISTENT

- Model column `recalled_at` is `Mapped[datetime | None]` (`batch.py:49`); schema now
  mirrors it (`datetime | None`). Correct.
- `recalled_at` is the only `datetime` field in `BatchResponse`. The other temporal
  fields (`manufacturing_date`, `expiry_date`, `received_date`) are typed `date`/
  `date | None`, mirroring their `Mapped[date]` columns — so the schema's established
  convention is to mirror the model's native temporal types, not use `str`. The fix
  brings `recalled_at` into line with that convention; the old `str` was the outlier.
- `datetime` import added correctly (`from datetime import date, datetime`).

## FE / consumer impact: NONE

- `clinic-cms-web` `Batch` interface (`src/modules/pharmacy/types.ts:91-105`) has no
  `recalled_at` field at all — nothing parses it. FE consumes only `is_recalled`
  (bool) and `recalled_reason` (string), both unchanged.
- Its other temporal fields (`expiry_date`, `created_at`, `earliest_expiry`) are typed
  `string` and receive ISO strings. datetime→ISO-string in JSON is the standard pydantic
  serialization, so even a future FE reader of `recalled_at` would get the same shape.
- No consumer expects a pre-formatted string differing from other datetimes.

## Tests

- `TestBatchRecallPatchRegression` (2 tests) added to `test_inventory_e2e.py`, genuine
  DB-backed e2e via `inv_client`:
  1. Recall PATCH → 200; asserts `is_recalled=true`, `recalled_at` not null,
     `recalled_reason` persisted; follow-up unit_cost PATCH keeps recall state + same
     `recalled_at` (persistence check).
  2. unit_cost-only PATCH → 200, `is_recalled=false`, `recalled_at=None` (no regression).
- Both directly exercise the acceptance criteria. Handoff reports 47/47 passed in the
  isolated `fix121` Docker stack (2 new + 45 pre-existing).

## Quality checks

- Diff reviewed `--unified=3`: 1 line of substance + 1 import + 2 tests. No secrets, no
  logging changes, no commented-out code, no DB query changes.
- ruff/mypy: host `ruff` binary is broken (`Exec format error` — wrong-arch install),
  confirming the handoff's "host tooling may be broken" note; could not re-run locally.
  Handoff reports 0 new ruff / 0 new mypy findings, verified there via `git stash` vs
  unmodified `origin/dev`. Change is a pure type annotation on one field — no plausible
  new lint/type error. Accepted.

## Findings

- No CRITICAL / MAJOR issues.
- MINOR (pre-existing, out of scope, not blocking): `update_batch` uses `if recall … elif
  unit_cost`, so a PATCH carrying both `is_recalled` and `unit_cost` applies only the
  recall branch. Pre-existing behavior, unrelated to this type fix.
- Noted for backlog (not this task): handoff flags CRLF in `docker/docker-start.sh`
  breaking `alembic upgrade head` on Windows hosts, and suggests a broader grep for other
  `datetime`-declared-as-`str` response fields (TASK-096 family). Both out of scope here.

## Gates

- [x] No critical/major issues
- [x] Tests meaningful, cover acceptance criteria + regression
- [x] Type consistency confirmed
- [x] No FE/consumer break
- [x] No security concerns
- [x] Report + handoff created, status updated
