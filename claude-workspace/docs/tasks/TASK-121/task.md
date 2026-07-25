---
id: TASK-121
type: bug
title: "[High] Recall batch (PATCH /inventory/batches/{id} is_recalled) luôn 500"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-25
updated: 2026-07-26
branch: "fix/TASK-121-recall-batch-500"
tags: [inventory, batch, crash, high, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (H-2)"
---

# TASK-121: [High] Recall batch luôn 500 (H-2)

**Nguồn:** E2E re-run TASK-095, H-2. Cùng họ bug type-mismatch với TASK-096.

- **Kỳ vọng:** `PATCH /inventory/batches/{id}` với `is_recalled=true` + `recalled_reason` → đánh dấu recalled, 200.
- **Thực tế:** 500 + rollback (lô vẫn is_recalled=false). Gốc: `update_batch` gán `b.recalled_at = datetime.now(UTC)` (datetime) nhưng `BatchResponse.recalled_at` khai `str | None`; `BatchResponse.model_validate(b)` fail pydantic v2 str-coercion của datetime → raise → get_db rollback. PATCH chỉ `unit_cost` (không đụng recalled_at) → 200.
- **File:** `app/modules/inventory/schemas/inventory_schemas.py` (BatchResponse.recalled_at), `.../services/batch_service.py`, `.../api/routes.py`. Model `batch.py:49` recalled_at là `Mapped[datetime|None]`.

## Acceptance Criteria
- [x] `BatchResponse.recalled_at` kiểu datetime|None (khớp model) → recall trả 200, lô is_recalled=true persisted.
- [x] Không hồi quy PATCH unit_cost / các field khác.
- [x] Integration test recall batch (200 + persisted) + case chỉ unit_cost.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Documentation Completed
2026-07-26 — Final spec: `deliveries/final-specs/recall-batch-500-fix.md`

## Blockers
Không.

## Testing Completed (2026-07-26)
47/47 passed (isolated stack `y121`, base `origin/dev`@`c24f5fe`, migrated 0069). Recall PATCH → 200 with is_recalled+recalled_at persisted; unit_cost-only PATCH → 200 (no regression). See `deliveries/test-reports/test-report.md`.
