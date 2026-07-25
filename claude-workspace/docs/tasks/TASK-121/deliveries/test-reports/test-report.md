# Test Report: TASK-121 — Recall batch 500 (H-2)

**Date**: 2026-07-26
**Tester**: Test Agent
**Branch**: `fix/TASK-121-recall-batch-500` @ `aa112fd` (base `origin/dev` @ `c24f5fe`, migrations to `0069`)
**Worktree**: `_fix121-be` (isolated stack `y121`: api :9946, postgres :5446, redis :6428)

## Summary

| Metric | Value |
|---|---|
| Total collected (inventory) | 47 |
| Passed | 47 |
| Failed | 0 |
| New failures (regressions from this fix) | 0 |

Command: `pytest -q --tb=short tests/integration/inventory`

## Result

```
47 passed, 58 warnings in 50.81s
```

## Acceptance Criteria Validation

| # | Criterion | Test(s) | Result |
|---|---|---|---|
| 1 | `PATCH` batch `is_recalled=true` + reason → 200, `is_recalled`+`recalled_at` persisted | `test_inventory_e2e.py::TestBatchRecallPatchRegression::test_patch_recall_batch_returns_200_and_persists` | PASS |
| 2 | `unit_cost`-only PATCH → 200 (no regression) | `test_inventory_e2e.py::TestBatchRecallPatchRegression::test_patch_unit_cost_only_no_regression` | PASS |

Root cause fix confirmed: `BatchResponse.recalled_at` now typed `datetime | None` (matching the ORM model), so `BatchResponse.model_validate(b)` no longer raises on Pydantic v2 str-coercion, and the recall PATCH no longer 500s/rolls back.

## Environment

- Isolated Docker Compose stack `y121` (project name), built from `_fix121-be` worktree, `Dockerfile` context.
- Postgres 15-alpine, Redis 7-alpine, api container (`tail -f /dev/null`, tests run via `docker compose exec`).
- Migrated `alembic upgrade head` → `0069_stock_status_view_low_stock_fields`. Superadmin seeded via `scripts/seed_superadmin.py`.
- Stack torn down (`docker compose down -v`) after test run. No shared/main/dev/w2e stacks touched.

## Conclusion

All in-scope inventory/batch-recall assertions PASS (47/47). **Task TASK-121 → DOCUMENTING.**
