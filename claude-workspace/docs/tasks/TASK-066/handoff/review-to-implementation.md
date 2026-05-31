# Handoff: TASK-066 → Code Implementation Agent

**From**: Code Review Agent
**To**: Code Implementation Agent
**Status**: IN_PROGRESS
**Decision**: CHANGES_REQUESTED

## Summary

The AR aging endpoint, doctor-weekly endpoint, and FE mock-data removal are all functionally correct and well-tested (15/15 integration tests pass, ruff clean, FE type-check clean). One MAJOR security issue must be fixed before testing: the CSV export does not neutralize spreadsheet formula injection on user-controlled patient names.

## Required Changes

### 1. (MAJOR) Neutralize CSV formula injection — BE
**File**: `clinic-cms-merge/app/modules/reports/services/ar_aging_service.py` → `build_ar_aging_csv()`

Patient names (and defensively patient_code) are written verbatim. A patient named `=...`, `+...`, `-...`, or `@...` becomes an executable formula in Excel/Sheets. Add a guard before writing each cell:

```python
def _csv_safe(v: str) -> str:
    return "'" + v if v and v[0] in ("=", "+", "-", "@", "\t", "\r") else v
```

Apply to `p.patient_name` and `p.patient_code` in both the data rows and (where applicable) any string cells.

### 2. (MAJOR) Same fix on the FE client-side fallback
**File**: `clinic-cms-web/src/pages/reports/ARAgingReportPage.tsx` → `exportToCsv()` (line 59)

The client-side fallback CSV path interpolates `p.patient_name` directly. Apply the same neutralization so both export paths are safe:

```ts
const csvSafe = (v: string) =>
  /^[=+\-@\t\r]/.test(v) ? `'${v}` : v;
```
(then quote as today). Keep the existing `"…"` quoting.

### 3. (MINOR — confirm, optional) doctor-weekly status set
**File**: `clinic-cms-merge/app/modules/reports/services/doctor_weekly_service.py`

`_COMPLETED_STATUSES = ("COMPLETED", "AWAITING_PAYMENT")` counts visits not yet completed under a "weekly completed" chart. Confirm this proxy is intended; if not, restrict to `("COMPLETED",)`. Not blocking — your call / product confirmation.

## Suggested test to add
Seed a patient named `=1+1` (or `@SUM(...)`), call `/reports/ar-aging/export`, and assert the corresponding cell starts with `'` (neutralized).

## Not in scope / no action
- Both branches carry unrelated work (BE inventory/vss/prescriptions, FE theme picker) — not part of this review.
- Everything else (SQL correctness, tenant isolation, encrypted-name decryption, permission gating, FE mock removal + error states) is approved as-is.
