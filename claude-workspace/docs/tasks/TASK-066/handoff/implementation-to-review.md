# Handoff: TASK-066 → Code Review (Re-submission after CHANGES_REQUESTED)

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-05-31 (re-submitted after security fixes)

---

## Re-submission: Security Fixes Applied (2026-05-31)

All issues from `review-to-implementation.md` have been addressed:

### Fix 1 — BE: CSV formula injection guard
**File**: `clinic-cms-merge/app/modules/reports/services/ar_aging_service.py`

Added `_csv_safe()` helper and applied it to `p.patient_code` and `p.patient_name` in `build_ar_aging_csv()`:

```python
def _csv_safe(v: str) -> str:
    """Prevent CSV formula injection in Excel/Sheets (OWASP)."""
    return "'" + v if v and v[0] in ("=", "+", "-", "@", "\t", "\r") else v
```

### Fix 2 — FE: Client-side CSV formula injection guard
**File**: `clinic-cms-web/src/pages/reports/ARAgingReportPage.tsx`

Added `csvSafe()` inside `exportToCsv()` and applied to both string cells:

```ts
const csvSafe = (v: string): string =>
  /^[=+\-@\t\r]/.test(v) ? `'${v}` : v;
```

### Fix 3 — Integration test for injection neutralization
**File**: `clinic-cms-merge/tests/integration/reports/test_ar_aging_e2e.py`

Added `test_ar_aging_csv_export_neutralizes_formula_injection`:
- Seeds patient named `=SUM(A1:A10)` with an outstanding invoice
- Calls `GET /api/v1/reports/ar-aging/export`
- Asserts CSV contains `'=SUM(A1:A10)` (apostrophe-prefixed)
- Asserts no un-neutralized `,=SUM` cell exists

**Test results: 28 passed** (up from 27 — 1 new injection test added).

### Fix 4 — MINOR: Comment on `_COMPLETED_STATUSES`
**File**: `clinic-cms-merge/app/modules/reports/services/doctor_weekly_service.py`

Added explanatory comment:
> AWAITING_PAYMENT counts as completed work — the consultation is done and the
> visit is effectively finished; billing/payment is still pending but the doctor
> has already delivered the service.

### New commits
| Repo | Branch | Commit |
|------|--------|--------|
| clinic-cms-merge | `feature/TASK-066-ar-aging-report` | `476d61a` |
| clinic-cms-web | `feature/TASK-066-remove-mock-data` | `e6e956e` |

---

## Original Handoff (still valid)

## Summary

Implemented the AR Aging (`GET /api/v1/reports/ar-aging`) and Doctor Weekly
(`GET /api/v1/reports/doctor-weekly`) BE endpoints, removed the dangerous
`MOCK_DATA` const + silent catch fallback from `ARAgingReportPage.tsx`, and
wired the doctor weekly chart in `DoctorDashboardPage.tsx` to the real API.

## Files Changed

### BE — `clinic-cms-merge` branch `feature/TASK-066-ar-aging-report`

| File | Change |
|------|--------|
| `app/modules/reports/services/ar_aging_service.py` | NEW — two-phase logic: raw SQL aging buckets + ORM Patient load for encrypted full_name decryption; `build_ar_aging_csv()` helper |
| `app/modules/reports/services/doctor_weekly_service.py` | NEW — completed visits per ISO weekday; zero-fills all 7 days |
| `app/modules/reports/schemas/report_schemas.py` | Added `ARAgingPatientRow`, `ARAgingReport`, `DoctorWeeklyRow`, `DoctorWeeklyReport` schemas |
| `app/modules/reports/api/routes.py` | Added `GET /ar-aging`, `GET /ar-aging/export` (StreamingResponse CSV), `GET /doctor-weekly` |
| `tests/integration/reports/test_ar_aging_e2e.py` | NEW — 15 integration tests (real DB) |

### FE — `clinic-cms-web` branch `feature/TASK-066-remove-mock-data`

| File | Change |
|------|--------|
| `src/pages/reports/ARAgingReportPage.tsx` | Deleted 62-line `MOCK_DATA` const; removed silent `catch { return MOCK_DATA }` fallback; error state now shows clear Vietnamese message + retry button |
| `src/pages/doctor/DoctorDashboardPage.tsx` | Replaced hardcoded `weeklyData = [8,12,10,15,7,4,0]` with real `useQuery` → `GET /api/v1/reports/doctor-weekly`; chart hidden when API errors; loading + empty states handled |

## Test Results

- Integration tests: **27/27 passed** (15 new AR aging + doctor-weekly, 12 pre-existing)
- `ruff check app/modules/reports/`: **All checks passed**
- `mypy` on new files: **Success: no issues found in 3 source files**
- FE `tsc --noEmit` on changed files: **0 errors in ARAgingReportPage.tsx, DoctorDashboardPage.tsx** (pre-existing errors in unrelated files: Sidebar, admin/api, PatientDetailPage — not caused by this PR)

## Key Design Decisions

1. **Two-phase AR aging query**: `full_name` is BYTEA ciphertext (TASK-037 P2). Raw SQL cannot decrypt it. Strategy: SQL aggregation for bucket amounts → ORM `select(Patient)` to decrypt names in Python.

2. **Invoice status mapping**: BE uses `'issued'` (fully unpaid) and `'partially_paid'` — NOT `UNPAID`/`PARTIAL` as originally noted in the task description. Only `balance_due` is counted (not `grand_total`), so partially paid invoices correctly report the remaining amount.

3. **FE error state**: When the API fails, a red error card is shown with the error message and a Retry button. No fake numbers are ever displayed.

4. **Doctor weekly chart hides on error**: Per task spec — if API is unavailable, the chart is not rendered (rather than showing mock or empty data with no context).

5. **CSV export**: UTF-8 BOM prepended (`\xef\xbb\xbf`) for Excel compatibility; streamed via `StreamingResponse`.

## Areas for Review Focus

- SQL query in `ar_aging_service.py` — specifically the `JOIN visit v ON v.id = i.visit_id` clause: invoices without a linked visit_id are excluded. Confirm this is correct business logic (all billed invoices should come from visits).
- Tenant isolation: `clinic_id` filter is explicit in WHERE clause (belt-and-suspenders with RLS). The test `test_ar_aging_tenant_isolation` validates this.
- `_OUTSTANDING_STATUSES = ("issued", "partially_paid")` — confirm these match the exact status values used in the billing workflow.
- FE: `retry: 1` on the AR aging query (one auto-retry before showing error). Acceptable for a report page?
