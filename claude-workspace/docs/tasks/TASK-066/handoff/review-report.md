# Code Review Report: TASK-066

**Reviewer**: Code Review Agent
**Date**: 2026-05-31
**Decision**: CHANGES_REQUESTED
**BE branch**: `feature/TASK-066-ar-aging-report` (clinic-cms-merge)
**FE branch**: `feature/TASK-066-remove-mock-data` (clinic-cms-web)
**SonarQube**: DISABLED (skipped per guide)

---

## Scope Reviewed

TASK-066-specific files only (both branches also contain unrelated work — BE: inventory/vss/prescriptions; FE: theme picker — NOT reviewed here):

- BE: `app/modules/reports/services/ar_aging_service.py`, `doctor_weekly_service.py`, `api/routes.py`, `schemas/report_schemas.py`, `tests/integration/reports/test_ar_aging_e2e.py`
- FE: `src/pages/reports/ARAgingReportPage.tsx`, `src/pages/doctor/DoctorDashboardPage.tsx`

---

## Quality Gates

| Gate | Result |
|------|--------|
| AR aging integration tests | 15/15 PASS |
| `ruff check` (3 new/changed BE files) | All checks passed |
| FE `tsc --noEmit` (changed files) | 0 errors in TASK-066 files |
| Manual review | 1 MAJOR, 1 MINOR |

---

## Focus-Area Verification (all PASS except CSV injection)

1. **AR aging SQL correctness** — PASS. Only `status = ANY(('issued','partially_paid'))`, uses `i.balance_due` (not `grand_total`), ages from `DATE(i.issued_at AT TIME ZONE 'UTC')` relative to `as_of`. `balance_due > 0` guard present. Invoice model (`invoice.py:15,56,60`) confirms these are the real column/status names. Verified by `test_ar_aging_partially_paid_invoice` (asserts 400k not 1M) and `test_ar_aging_paid_invoices_excluded`.
2. **Cross-tenant isolation** — PASS. Explicit `clinic_id = :clinic_id` on invoice, visit, AND patient joins (belt + suspenders with RLS). `test_ar_aging_tenant_isolation` seeds a 999,999,999 invoice in another clinic and asserts it's excluded.
3. **EncryptedString decryption** — PASS. `full_name` is `EncryptedString` (BYTEA). Two-phase approach: raw SQL for amounts (plaintext `patient_code` only) → ORM `select(Patient)` to decrypt names via the `current_clinic_id` ContextVar. No ciphertext leaks into the response. `test_ar_aging_bucket_0_30` asserts `patient_name != "" and != "(unknown)"`, proving decryption succeeded.
4. **CSV export security** — PARTIAL. Content-Disposition + `text/csv; charset=utf-8` + UTF-8 BOM all correct (`test_ar_aging_export_csv`). **However, no CSV-formula-injection guard** — see MAJOR-1.
5. **FE ARAgingReportPage** — PASS. 62-line `MOCK_DATA` const deleted; silent `catch { return MOCK_DATA }` removed. Error state shows a clear Vietnamese message + error detail + Retry button (`data-testid="ar-aging-error"`). No 30.1M fake data remains.
6. **FE DoctorDashboardPage** — PASS. Hardcoded `[8,12,10,15,7,4,0]` replaced with real `useQuery → GET /reports/doctor-weekly`. Chart is wrapped in `{!weeklyQuery.isError && (...)}` so it is hidden on error (no stale/fake data); loading and empty states handled.
7. **Permission `report.financial`** — PASS. Seeded in `alembic/versions/0020a_add_report_permissions.py` (admin-only). AR aging endpoints gate on `report.financial`; doctor-weekly on `report.view` (appropriate — non-financial).

---

## MAJOR Issues

### MAJOR-1: CSV formula injection in AR aging export
**Files**: `app/modules/reports/services/ar_aging_service.py` (`build_ar_aging_csv`, ~line 200) AND `clinic-cms-web/src/pages/reports/ARAgingReportPage.tsx` (`exportToCsv`, line 59)

- Patient `full_name` is user-controlled and written verbatim into CSV cells via `csv.writer` (BE) / string interpolation (FE).
- A patient named `=cmd|'/c calc'!A1`, `+...`, `-...`, or `@...` will be interpreted as a **formula** when the CSV is opened in Excel/LibreOffice/Google Sheets — a known data-exfiltration / RCE vector, especially serious for a financial report distributed to finance staff.
- **Fix (BE)**: prefix any cell value beginning with `=`, `+`, `-`, `@`, tab, or CR with a single quote `'` (or wrap), before writing. Apply to `patient_name` (and `patient_code` defensively).
  ```python
  def _csv_safe(v: str) -> str:
      return "'" + v if v and v[0] in ("=", "+", "-", "@", "\t", "\r") else v
  ```
- **Fix (FE)**: apply the same neutralization in `exportToCsv` so the client-side fallback path is also safe.
- A unit/integration test seeding a patient named `=1+1` and asserting the exported cell is neutralized would lock this in.

---

## MINOR Issues

### MINOR-1: doctor-weekly counts AWAITING_PAYMENT as "completed"
**File**: `app/modules/reports/services/doctor_weekly_service.py:_COMPLETED_STATUSES`

`_COMPLETED_STATUSES = ("COMPLETED", "AWAITING_PAYMENT")`. Per `VisitStatus`, `AWAITING_PAYMENT` precedes `COMPLETED` in the lifecycle, so a "weekly completed visits" chart will include not-yet-completed visits. Acceptable as a "consultation done" proxy if intended, but the chart label says "completed". Confirm with product or restrict to `COMPLETED` only. Documented for awareness; not blocking on its own.

---

## Positive Notes

- Parameterized queries throughout — no SQL injection surface.
- Structured logging (`structlog`) logs only aggregate counts/totals, no PII (patient names are not logged). Good.
- Decimal arithmetic preserved end-to-end (no float drift in money).
- Test suite is genuinely meaningful (AAA pattern, edge cases: empty, each bucket, partial, paid-excluded, tenant isolation, permission gates, CSV headers).

---

## Decision

**CHANGES_REQUESTED** — the AR aging report is functionally correct and well-tested, but the CSV export (BE + FE) lacks formula-injection neutralization. For a financial export consumed in spreadsheet software, this is a security issue that should be fixed before testing. The fix is small and localized.
