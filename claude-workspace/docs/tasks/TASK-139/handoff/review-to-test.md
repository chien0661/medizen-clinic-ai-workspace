# Handoff: TASK-139 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED
**Branch**: `feature/TASK-139-payroll-export` (based on `feature/TASK-138-payroll-session-shift`, **not** `dev`)
**Commits**: BE `fd020da` (`_feat139-be`) · FE `d59942f` (`_feat139-web`)
**Full report**: `docs/tasks/TASK-139/handoff/review-report.md`

## Summary

Excel export of the whole payroll period (`GET /api/v1/payroll/export?month=`, 27 columns) plus a
per-staff printable payslip (browser print → Save as PDF). Purely additive: +638 BE lines across 4
files, 3 new FE components/pages touched. The export reuses `compute_payroll` verbatim — the same
engine the payroll screen uses — so there is no second computation path to drift, and the printable
payslip renders from the already-fetched row object rather than re-fetching. Approved with 1 Major
(a pre-existing, repo-wide test-fixture issue, not a product defect) and 5 Minors.

## State at approval

- BE unit: **1146 passed, 12 failed** — the known pre-existing dev set, zero new failures.
- FE: **1282 passed, 3 failed** — the known pre-existing set, zero new failures.
- `ruff` clean on all TASK-139 files. i18n vi/en parity verified programmatically (no orphan keys
  either direction; 39 `payroll.payslip.*` keys in both).
- BE integration (`test_payroll_export_e2e.py`, 6 tests) reported passing by the implementer — but see
  the teardown caveat below before trusting the count.

## Focus areas for testing

### 1. Excel export fidelity vs the screen (the core AC)

- Export a period with a **mixed** staff set — monthly, hourly, `per_session` (incl. a half-day 0.5
  total), `per_shift`, a commission-only staff on an `_empty_slip`, and a staff with **no user
  account** — and reconcile **every** cell against `GET /hr/payroll` for the same month.
- Confirm money/count cells are stored as **numbers**, not text: `SUM()` over "Thực nhận" in Excel
  must work without re-typing the column. Same for the `%` columns.
- Confirm blank-vs-zero: "Đơn giá buổi"/"Đơn giá ca" must be **empty** for monthly/hourly, not `0`.
- Row count must equal the payslip count; verify ordering is stable.
- Open the file in real Excel (and ideally LibreOffice/Google Sheets) — the unit tests only check the
  openpyxl object model, not that the workbook actually opens cleanly.
- Formula-injection: create a staff named `=cmd|'/c calc'!A1` and confirm the cell renders as literal
  text (the shared helper neutralises it — verify it survives this path).

### 2. Empty and malformed periods

- Period with no staff on payroll → **200 header-only workbook**, not 500 (explicit AC).
- ⚠️ **Malformed `month`** — the param has no format validation (review finding m1). Try
  `month=2026-08ABC` (expect: silently accepted, file mis-named/mis-titled) and
  `month=2026-13`, `month=abcd`, and a value containing `%0d%0a`. The CRLF case is expected to produce
  a **500** (h11 rejects the malformed `Content-Disposition` header). Please document the actual
  observed behaviour — it feeds the decision on whether to add `pattern=` validation now.

### 3. RBAC and tenancy

- A role **without** `payroll.manage` → 403 on the export endpoint (receptionist, doctor, nurse).
  Unauthenticated → 401.
- **Cross-tenant**: seed two clinics that *both* have staff on payroll in the same month, then export
  as clinic A and assert clinic B's staff are absent. The existing integration test only seeds one
  clinic, so it cannot actually catch a tenancy regression (finding m4) — this needs a real two-tenant
  test.
- Confirm the export cannot be steered by a client-supplied clinic id (it comes from the tenancy
  middleware, but verify a forged `X-Clinic-Id` for another tenant is rejected, not honoured).

### 4. Printable payslip

- Print for at least one staff on **each** pay type. Verify session/shift rows are **absent** (not
  zero) for monthly/hourly, and that `worked_days` / `total_hours` / `completed_shifts` each appear
  only where meaningful.
- Per the AC, compare **one staff with a 15% per-staff override** against **one on the clinic-wide
  rate**: the slip must show the applied `%` and the correct "tỷ lệ riêng" / "tỷ lệ chung" source.
- Staff with **no login account** must print with correct code/name.
- Actual browser print → Save as PDF: check A4 pagination, that the modal chrome and page nav are
  excluded from the printed output, and the signature block placement.
- Switch language to `en` and confirm every payslip label resolves (no raw `hr:payroll.payslip.*` keys
  leaking through).
- Edge (finding n1): a `per_shift` commission-only staff (`shift_rate` null) currently renders **no**
  count row at all — confirm this reads acceptably or file it.

### 5. PayrollPage regression

- The new "In phiếu" column shifted the footer colSpan (13→14) — verify the "Tổng thực nhận" footer
  still aligns under the right column at several viewport widths.
- Export button loading/disabled states; existing "Ghi vào chi phí" still works.

## Known open items — do NOT re-file as bugs

- **M1 — shared e2e DB pollution (confirmed, but pre-existing and repo-wide).** I verified live against
  `clinic_e2e_postgres`: this test file left **5 `PX%` clinics + 10 `px_*` users** behind
  (`staff_profile`, `user_role`, `account_clinic_role` *were* cleaned). The DB already holds **1,731
  clinics / 2,410 users** from months of runs across many test files using the same fixture shape, so
  TASK-139 inherited the pattern rather than introducing it. Two asks for this phase:
  1. When you re-run the integration tests, **read the full pytest summary line** — confirm whether
     teardown ERRORs accompany the "6 passed". The implementer's "6/6 passed" may have omitted them.
  2. Report the observed behaviour into the follow-up task; do not attempt a DB cleanup as part of
     testing (CLAUDE.md DB protocol — the user decides on data changes).
- **m2/m3 — blended commission rate in the export.** The `Tỷ lệ HH (%)` columns are *derived*
  (`commission / revenue × 100`), so a staff earning across several service types at different rates
  shows a revenue-weighted blend matching no configured rule; and `Nguồn tỷ lệ` shows "Riêng" if
  **any** row used an override, not all. Directionally right, not literally reconcilable. Please
  **construct this exact scenario** (one staff, two service types, override on only one) and record the
  output — the user needs it to decide between a footnote, an extra column, or accepting as-is.
- **m5** — an unrecognised `rate_source` renders as a blank cell instead of falling back to the raw
  value. Cosmetic, noted for follow-up.
- **Route path `/api/v1/payroll/export`** (not `/hr/payroll/export`) is **intentional and closed** —
  all five existing export endpoints in this router are un-prefixed. Do not file as an inconsistency.

## Note on the branch base

TASK-138 gained commit `cebf0bd` (payslip commission rate + source) *after* I approved that branch;
it is TASK-139's base and supplies the `procedure_rate_percent`/`_source` fields this export depends
on. It has not itself been through a review gate — findings m2 and m3 originate there, not in
TASK-139. When TASK-138's own testing phase covers the rate/source fields, that closes the gap.
Release order remains: merge TASK-138 first, then TASK-139.
