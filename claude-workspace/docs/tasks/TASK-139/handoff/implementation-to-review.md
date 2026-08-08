# Handoff: TASK-139 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW

## Summary

Added Excel export for the full payroll period (`GET /api/v1/payroll/export?month=YYYY-MM`)
and a per-staff printable payslip (browser print → Save as PDF, no BE PDF
generation). Both branches build on `feature/TASK-138-payroll-session-shift`
(not `dev`) per task.md, since the export needs TASK-138's session/shift
rate + commission-source payslip fields.

## Files Changed

### Backend (`_feat139-be`, branch `feature/TASK-139-payroll-export`, base `cebf0bd`)

- `app/modules/hr/services/payroll_service.py`: added `build_payroll_export_rows()`
  (pure — Payslip dicts → Excel row lists, Vietnamese `pay_type`/rate-source
  labels, money/percent as raw numbers, `None` → `""` blank cell for
  session/shift rate and commission rate when not applicable) and
  `export_payroll_xlsx()` (calls `compute_payroll` then `build_xlsx_response`).
  `PAYROLL_EXPORT_HEADERS` module constant (27 columns) documents the exact
  breakdown covered.
- `app/modules/hr/api/routes.py`: new `GET /payroll/export` route (RBAC
  `payroll.manage`, same permission as the other payroll endpoints), module
  docstring updated. Route path is literally `/payroll/export` (not nested
  under `/hr/payroll/...`) per task.md's explicit spec — flagged under
  Deviations below since it's the one inconsistency with the sibling
  `/hr/payroll` endpoints worth a second look.
- `tests/unit/test_payroll_export.py` (new, 13 tests): pure logic tests for
  `build_payroll_export_rows` — header/row alignment, pay-type labels,
  per_session/per_shift rate visibility, commission rate + source labels,
  blank-vs-zero handling, ordering.
- `tests/integration/test_payroll_export_e2e.py` (new, 6 tests, real DB):
  401/403 RBAC (receptionist role lacks `payroll.manage`), empty-period
  header-only workbook (not 500), data matches `GET /hr/payroll` for a
  monthly-pay staff member, staff with `user_id=NULL` appears in the export,
  cross-tenant isolation.

**Migration note**: the shared `clinic_e2e_postgres` container was one
migration behind this branch (`0076` vs code head `0077`,
`0077_payroll_session_shift_staff_commission.py` from TASK-138). Ran
`alembic upgrade head` against it to add the `session_rate`/`shift_rate`/
commission-override columns — required for the new e2e tests to even create
a `StaffProfile` row. No migration file was added by this task itself.

### Frontend (`_feat139-web`, branch `feature/TASK-139-payroll-export`, base `4bf1b55`)

- `src/pages/hr/PayrollPage.tsx`: added `ExportExcelButton` +
  `useExportDownload(() => exportBlob("/api/v1/payroll/export", { month }), "bang_luong_" + month)`
  next to "Ghi vào chi phí"; added an "In phiếu" column with a per-row print
  icon opening `PrintPayslipModal`. Table `tfoot` colSpan updated (13→14) for
  the new column.
- `src/components/hr/PrintablePayslip.tsx` (new): A4 payslip template,
  pattern-matched on `PrintableInvoice`/`PrintableVisitSlip` (own
  `.printable-payslip-wrapper` class + `@media print`/`@media screen` rules,
  visibility-toggle trick, `aria-hidden`). Renders a breakdown table built
  as a filtered row list — session/shift rate rows and the corresponding
  count only appear when non-null (hides rather than shows 0 for legacy
  monthly/hourly payslips); commission rows only appear when earned, with
  the applied rate % + source ("tỷ lệ riêng"/"tỷ lệ chung", reusing the
  TASK-138 i18n keys) appended to the label.
- `src/components/hr/PrintPayslipModal.tsx` (new): screen-only preview +
  print trigger wrapper, pattern-matched on `PrintVisitSlipModal` (fetches
  clinic settings for the header, `window.print()` on click).
- `src/locales/vi/hr.json` + `en/hr.json`: new `hr:payroll.payslip.*` keys
  (modal chrome + every breakdown row label) — verified by the existing
  `i18n-hr.test.ts` vi/en parity test (still green) and the new tests below.
- `src/tests/hr/PrintablePayslip.test.tsx` (new, 13 tests), `PrintPayslipModal.test.tsx`
  (new, 4 tests), `PayrollPage.export.test.tsx` (new, 4 tests: export button
  → correct URL/month/Authorization header; row print action opens/closes
  the modal for the right staff member).

## Test Results

- **BE unit** (`tests/unit`, Docker `clinic_e2e-api`): 1146 passed, 12
  pre-existing failures (email templates, erasure, feature_flags,
  medicine_stock ×4, rls_helpers ×2, tenancy_middleware ×3) — unchanged from
  baseline, zero new failures. New `test_payroll_export.py`: 13/13 passed.
- **BE integration** (`test_payroll_export_e2e.py`, real Postgres/Redis):
  6/6 passed.
- **BE lint/type-check**: `ruff check` clean on all changed files; `mypy`
  clean on `payroll_service.py` (fixed a pre-existing-pattern
  `str | None` → dict-key arg-type error by coalescing `or ""` before the
  `_RATE_SOURCE_LABEL.get()` lookup).
- **FE full suite** (`npx vitest run`): 1282 passed, 3 pre-existing failures
  (QueuePage ×2, ForgotPasswordPage ×1) — unchanged from baseline, zero new
  failures. New TASK-139 test files: 21/21 passed
  (`PrintablePayslip.test.tsx` 13, `PrintPayslipModal.test.tsx` 4,
  `PayrollPage.export.test.tsx` 4).
- **FE type-check**: clean. **FE lint** (scoped to touched files): clean —
  the full `npm run lint` run has 17 pre-existing errors in untouched files
  (`VssIntegrationConfigPage.tsx`, `VssSyncLogPage.tsx`, `VitalsPage.tsx`,
  `units.ts`, `TemplateRenderer.tsx`), confirmed via `git status` to predate
  this task.

## Areas for Review Focus

1. **Route path**: `GET /api/v1/payroll/export` (not `/hr/payroll/export`)
   was implemented literally per task.md/the implementation plan, even though
   every sibling payroll endpoint lives under `/hr/payroll/...`. Worth
   confirming this was an intentional API design choice and not a
   typo/oversight in the original spec before it ships.
2. **`PAYROLL_EXPORT_HEADERS` column set (27 columns)** — confirm the
   Vietnamese labels and column order read well for accounting's actual
   workflow; this is a judgment call with no existing precedent to copy from
   (unlike `/staff/export`'s much shorter column set).
3. **happy-dom test gotcha** (FE): `useExportDownload`'s throwaway
   `<a>.click()` causes happy-dom (unlike real browsers) to actually
   navigate `window.location` to the `blob:` URL, corrupting later tests in
   the same file. `PayrollPage.export.test.tsx` stubs
   `URL.createObjectURL`/`revokeObjectURL` and
   `HTMLAnchorElement.prototype.click` to avoid this — flagging in case this
   pattern needs to be extracted into a shared test helper for future export
   button tests (I did not create one, to keep this task's diff scoped).
4. **Migration side-effect**: I ran `alembic upgrade head` against the
   shared `clinic_e2e_postgres` container (see BE note above) since it was
   behind TASK-138's migration. This is a one-time DB-state fix, not a code
   change — confirm this doesn't need to be called out anywhere else (e.g.
   deploy notes) since `clinic-cms-deploy-gotchas` memory already flags that
   `deploy.sh` doesn't auto-run migrations.

## Deviations from task.md

- None in scope/behavior. The only judgment call was the exact Excel column
  set/order and label wording (see focus area 2 above) — task.md specifies
  the fields to cover but not literal header text.

---

## Fix round 1 (post-APPROVED, review-report.md)

**Scope**: finding **m1** only (`month` query param unvalidated → CRLF/garbage
reaches the `Content-Disposition` filename and 500s at the h11 layer instead
of a clean 422). Verdict was APPROVED and task.md stayed `IN_TESTING`
throughout — this is a targeted fix, not a re-review cycle.

### Change

`app/modules/hr/api/routes.py` — `export_payroll`'s `month` parameter is now:

```python
month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="YYYY-MM")
```

matching the reviewer's suggested pattern and the existing `pattern=` idiom
used in `app/modules/patients/api/routes.py`. A malformed `month` (wrong
shape, out-of-range month like `2026-13`, or a CRLF-injection attempt) is now
rejected by FastAPI/Pydantic with **422** before the endpoint body — and
therefore `payroll_service.export_payroll_xlsx` and the
`Content-Disposition` filename interpolation — ever runs.

### Tests added

`tests/unit/test_payroll_export_route_validation.py` (10 tests, **true unit
tests — no DB, no shared e2e Postgres touched**): mounts only the `hr`
router in a bare `FastAPI()` app with RBAC/DB dependencies overridden and
`_clinic_id`/`export_payroll_xlsx` monkeypatched, so it exercises exactly
the `Query()` validation layer in isolation.
- Valid `"2026-08"`, plus the `"2026-01"`/`"2026-12"` month boundaries → 200.
- 8 malformed inputs (`"2026-13"`, `"2026-00"`, `"garbage"`, the reviewer's
  CRLF PoC `"2026-08\r\nX-Injected: 1"`, a path-traversal-shaped string,
  non-zero-padded month, 2-digit year, empty string) → 422, and asserts
  `export_payroll_xlsx` was never called for any of them.

Per the orchestrator's instruction, `tests/integration/test_payroll_export_e2e.py`
was **not** touched or re-run — the shared `clinic_e2e_postgres` DB-pollution
follow-up (review M1) is being handled separately.

### Test results

- New file: 10/10 passed.
- Full `tests/unit` suite (Docker `clinic_e2e-api`): **1156 passed, 12
  pre-existing failures** (same set as every prior round: email templates,
  erasure, feature_flags, medicine_stock ×4, rls_helpers ×2,
  tenancy_middleware ×3) — zero new failures.
- `ruff check` on the changed files: clean. `mypy` on `routes.py`: no new
  errors.

### Commit

`37b258d` — `fix(hr): validate month on GET /payroll/export to prevent CRLF-triggered 500 (TASK-139)`
(`_feat139-be`, branch `feature/TASK-139-payroll-export`).

### User decision on record — blended commission-rate columns (m2/m3): KEEP AS-IS

No code change. For the Documentation Agent: the Excel export's
`Tỷ lệ HH thủ thuật (%)` / `Tỷ lệ HH thuốc (%)` columns (and the matching
rate shown on `PrintablePayslip`) are **derived**, not a literal configured
rate — `commission / revenue * 100` — so for a staff member who earned
commission across multiple service types at different rates in the same
period, the exported percentage is a **revenue-weighted blend**, not a
number that matches any single `commission_rule` row. Likewise, the
`Nguồn tỷ lệ` ("Riêng"/"Chung") column reflects whether **at least one**
contributing line used a per-staff override — a staff row can show "Riêng"
even when only one of several service types actually had an override, with
the rest resolved at the clinic-wide rate. This is intentional
(TASK-138 `_commission_rate_and_source`, kept as-is per user decision on
this review round) but should be documented explicitly wherever the export
columns are described, since accounting could otherwise misread the
percentage as "the configured rate."

---

## Fix round 2 (BUG-001)

**Scope**: BUG-001 only (Test Agent finding, Medium severity) — the payroll
table's `tfoot` "Tổng thực nhận" total rendered under the wrong column.

### Root cause

Adding the "In phiếu" (print) action column to `<thead>`/`<tbody>` in the
original implementation also bumped the `tfoot` label cell's `colSpan` from
`13` to `14`, on the (incorrect) assumption that colSpan should track
"header count − 1". Since the value `<td>` right after the label cell is
un-spanned, it lands on whatever column immediately follows the label span —
bumping the span to 14 pushed the value from column 14 ("Thực nhận") to
column 15 ("In phiếu"). The label cell must stay at `colSpan={13}`
(spanning through "Điều chỉnh") regardless of trailing action columns added
after "Thực nhận"; "In phiếu" simply has no cell in the footer row, which is
correct for an action column.

### Change

`src/pages/hr/PayrollPage.tsx` — reverted the `tfoot` label cell back to
`colSpan={13}`, with an inline comment explaining why it must NOT track the
header count, to prevent a future column addition from reintroducing the
same off-by-one.

### Test added

`src/tests/hr/PayrollPage.export.test.tsx` — new describe block
`"PayrollPage — TASK-139 footer alignment regression (BUG-001)"`: asserts
the footer label cell's `colSpan` equals the 0-based index of the "Thực
nhận" column header (not `headers.length - 2`), and that the value cell
renders the total directly after it. Verified the test fails against the
pre-fix `colSpan={14}` (`expected 14 to be 13`) and passes with the fix,
before finalizing.

### Test results

- `PayrollPage.export.test.tsx` + `PayrollPage.test.tsx`: 15/15 passed.
- Full `npx vitest run`: 1283 passed (was 1282; +1 new test), same 3
  pre-existing failures (QueuePage ×2, ForgotPasswordPage ×1) — zero new
  failures.
- `eslint` on both changed files: clean.

### Commit

`d271e00` — `fix(hr): correct payroll footer colSpan so total aligns under Thực nhận (TASK-139)`
(`_feat139-web`, branch `feature/TASK-139-payroll-export`).

Status set back to `IN_TESTING` in `task.md` — ready for re-test.
