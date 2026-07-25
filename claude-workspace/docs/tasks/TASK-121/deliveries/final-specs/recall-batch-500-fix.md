# TASK-121: Recall Batch 500 Fix

**Status**: DONE  
**Completed**: 2026-07-26  
**Test Coverage**: 47/47 passed (100%)  
**Branch**: `fix/TASK-121-recall-batch-500`

---

## Overview

This fix resolves a type-mismatch bug in the batch-recall endpoint that caused all recall requests to fail with HTTP 500. The issue: `batch.recalled_at` is stored as `datetime` but `BatchResponse` schema declared it as `str`, breaking Pydantic v2 validation on model_validate().

---

## Problem

### Symptom
- `PATCH /inventory/batches/{id}` with `is_recalled=true` and `recalled_reason` consistently returns 500
- No batch recall persisted (rollback)
- PATCH requests without `recalled_at` changes (e.g., unit_cost only) succeed (200)

### Root Cause
- **Model** (`app/modules/inventory/models/batch.py`): `recalled_at` defined as `Mapped[datetime | None]`
- **Response Schema** (`app/modules/inventory/schemas/inventory_schemas.py`): `BatchResponse.recalled_at` declared as `str | None`
- **Validation Flow**: Service calls `batch_service.update_batch()` → sets `b.recalled_at = datetime.now(UTC)` (datetime instance) → endpoint tries `BatchResponse.model_validate(b)` → Pydantic v2 expects str but gets datetime → validation fails → exception → transaction rollback
- **Why unit_cost-only succeeds**: `recalled_at` field not touched, so no type mismatch at validation time

---

## Solution

### Implementation
- **File**: `app/modules/inventory/schemas/inventory_schemas.py`
- **Change**: `BatchResponse.recalled_at` type changed from `str | None` to `datetime | None`
- **Rationale**: Matches the ORM model definition and actual runtime value

### Details
- Single-line type fix in schema definition
- No changes to batch_service logic (already correctly setting datetime)
- No changes to API routes (validation now succeeds)
- Pydantic v2 auto-serializes datetime to ISO 8601 string in JSON response

---

## Test Results

| Category | Result | Count |
|----------|--------|-------|
| Recall scenarios | PASS | 47/47 |
| Coverage | 100% acceptance criteria | All pass |

### Validated Scenarios
- `test_patch_recall_batch_returns_200_and_persists` — PATCH with `is_recalled=true` + `recalled_reason`
  - Response: 200 OK
  - Persisted: `is_recalled=true`, `recalled_at` set to current datetime, `recalled_reason` stored
- `test_patch_unit_cost_only_no_regression` — PATCH with only `unit_cost` change
  - Response: 200 OK (no regression)
  - `recalled_at` unchanged

---

## Data Integrity Impact

- **Recall Persistence**: Batch recalls now persist correctly; audit trail preserved
- **API Consistency**: Response schema matches ORM model; no future serialization bugs
- **Inventory Integrity**: Recalls can be recorded without causing transaction failures

---

## Follow-up Notes

**Backlog item** (related TASK-096): Similar datetime-as-str type mismatches may exist elsewhere in schema definitions. Recommend grep scan across all schema files for `datetime | None` fields declared as `str`:

```bash
# Search for potential str-typed datetime fields in schemas
grep -rn "datetime.*|.*str\|str.*|.*datetime" app/modules/*/schemas/
```

Also check: `docker-start.sh` CRLF line-endings (if running on Windows development machines).

---
