# Test Cases: TASK-139 — Payroll Excel export + printable payslip

**Test Agent** | **Date:** 2026-08-08
**Env:** disposable stack (`clinic_t139_pg`/`clinic_t139_redis`/`clinic_t139_api`, built from `_feat139-be@37b258d`), FE vitest run directly on `_feat139-web@d59942f` worktree (no DB needed). Shared `clinic_e2e_*` containers were never touched.

Legend: PASS / FAIL / SKIP (with reason).

## 1. BE unit regression + new tests

| ID | Description | Steps | Expected | Actual | Result |
|----|---|---|---|---|---|
| U-01 | Full BE unit suite regression | `pytest tests/unit -q` in `clinic_e2e-api` image mounting `_feat139-be` | Same 12 pre-existing failures as documented baseline (email templates, erasure, feature_flags, medicine_stock×4, rls_helpers×2, tenancy_middleware×3), zero new failures | 1156 passed, 12 failed — exact same 12 test names as baseline | PASS |
| U-02 | New `test_payroll_export.py` (13 tests) | `pytest tests/unit/test_payroll_export.py -q` | 13/13 pass | 13/13 pass (bundled into U-03 run) | PASS |
| U-03 | New `test_payroll_export_route_validation.py` (10 tests) | `pytest tests/unit/test_payroll_export.py tests/unit/test_payroll_export_route_validation.py -q` | 23/23 pass | 23/23 pass | PASS |

## 2. BE integration — disposable stack

| ID | Description | Steps | Expected | Actual | Result |
|----|---|---|---|---|---|
| I-01 | Repo integration suite `test_payroll_export_e2e.py` (6 tests) against disposable Postgres | `alembic upgrade head` (→0077) then `pytest tests/integration/test_payroll_export_e2e.py -v` | 6/6 pass, no teardown ERROR | 6 passed, 6 warnings, **no ERROR** in summary line | PASS |
| I-02 | Fixture-leak check (TASK-140 follow-up) | `psql` count of `PX%` clinics / `px_*` users / staff_profile/user_role/account_clinic_role for those, and grand totals, in the **disposable** DB after I-01 | Report actual counts, no cleanup performed | `clinic_total=0, user_total=0` — **zero leaked rows**, full clean teardown in this isolated single run (contrasts with the reviewer's shared-DB finding of 5 leaked clinics/10 users — see test-report for discussion) | PASS (finding recorded, see report) |
| I-03 | Mixed staff set export vs `GET /hr/payroll` reconciliation: monthly, `per_session` (1.5 worked days incl. one half-day), `per_shift` (2 completed / 1 cancelled shift), no-account staff, formula-injection staff name | Seed via direct model inserts (`with_tenant_context`), call both endpoints for the same month, diff every relevant cell | Row count = 5, per-cell match, blank (not 0) for inapplicable session/shift columns, injection name neutralised as literal text | All assertions passed; injection cell `data_type == "s"`, value `"'=cmd|'/c calc'!A1"` (leading `'` neutraliser) | PASS |
| I-04 | Money/percent cells are real numbers | Same export as I-03 — `isinstance(cell, (int, float))` on "Lương cơ bản" | numeric, not string | `isinstance(..., (int, float))` True | PASS |
| I-05 | Blank-vs-zero for session/shift rate columns | Same export — monthly/per_session/per_shift rows | "Đơn giá buổi"/"Đơn giá ca" blank (`None` after openpyxl round-trip) when not applicable, not `0` | Confirmed `in (None, "")` for the inapplicable column on each pay type | PASS |
| I-06 | Empty period → header-only workbook | `GET /payroll/export?month=2020-01` (no staff) via repo's own `test_export_empty_period_returns_header_only_xlsx` | 200, header row present, 0 data rows | 200, `"Mã NV"` in header row 3, 0 data rows | PASS |
| I-07 | Malformed `month` → 422 (9 variants) | `garbage`, `2026-13`, `2026-00`, `2026-08\r\nX-Injected: 1`, `2026-08ABC`, `2026/08`, `26-08`, `%0d%0aX-Injected:1`, `""` | 422 for all (Fix round 1 `pattern=` validation) | 422 for all 9 variants | PASS |
| I-08 | Valid `month` boundaries | `2026-08`, `2026-01`, `2026-12` (covered by BE unit route-validation tests) | 200/expected path taken | 200 (per U-03) | PASS |
| I-09 | RBAC: no `payroll.manage` → 403 (receptionist, repo test) | `GET /payroll/export` with receptionist token | 403 | 403 | PASS |
| I-10 | RBAC: no `payroll.manage` → 403 (doctor role, additional) | Seed a `doctor`-role user, call export | 403 | 403 | PASS |
| I-11 | Unauthenticated → 401/403 | No `Authorization` header | 401 or 403 | 401/403 (repo test asserts `in (401,403)`) | PASS |
| I-12 | Cross-tenant isolation — real two-clinic scenario | Clinic A (5 mixed staff) + Clinic B (1 staff), same month, export as clinic A admin | Clinic B's staff absent from A's export | `"MXBNV01"` / `"Clinic B Nhân Viên"` absent from A's export; A's own 5 rows all present | PASS |
| I-13 | Forged `X-Clinic-Id` header targeting another tenant | Clinic A admin token + `X-Clinic-Id: <clinic B id>` header on export request | Forged header ignored or rejected — clinic B's data never returned | 200 returned, but clinic B's staff name absent — clinic A's own data returned (header ignored, tenancy resolved server-side) | PASS |
| I-14 | Staff with no user account appears with correct code/name | Repo test + I-03's `MXNV04`/`Không Tài Khoản Manual` | Full name/code present in export | Present in both | PASS |
| I-15 | `Content-Disposition` filename includes the period | Export response header for `2026-05` | `bang_luong_2026-05` present | Present | PASS |
| I-16 | Open workbook with a real reader (openpyxl load_workbook end-to-end via HTTP response bytes) | All of the above already round-trip through `openpyxl.load_workbook(io.BytesIO(resp.content))` | Opens without error | Opened cleanly in every scenario above | PASS |

## 3. FE unit/component tests

| ID | Description | Steps | Expected | Actual | Result |
|----|---|---|---|---|---|
| F-01 | Full FE vitest suite regression | `npx vitest run --silent` (×3 runs round 1, watching for flake; ×1 run round 2 on `d271e00`) | Same 3 pre-existing failures (QueuePage×2, ForgotPasswordPage×1), zero new failures | Round 1 run 1: 5 failed (2 extra, non-deterministic — CommissionKpiConfigPage timing). Round 1 runs 2 & 3: exactly 3 failed / 1282 passed, matching baseline. Round 2 (`d271e00`, 1 run): 3 failed / 1283 passed (1286 total — +1 test from the new BUG-001 regression test), same 3 pre-existing names, AttendanceWidget M-14 did not trigger | PASS (flake noted, not a regression — see report) |
| F-02 | New `PrintablePayslip.test.tsx` (13), `PrintPayslipModal.test.tsx` (4), `PayrollPage.export.test.tsx` (4) | Run the 3 files directly | 21/21 pass | 21/21 pass | PASS |
| F-03 | i18n vi/en parity for `payroll.payslip.*`, `payroll.rateSource.*`, `payroll.payType.*` keys | Programmatic flattened-key diff | No missing/orphan keys either direction | 45 keys in `vi`, all present in `en`; 0 missing, 0 orphan | PASS |
| F-04 | PrintablePayslip hides session/shift rows for monthly/hourly | Source read + `PrintablePayslip.test.tsx` cases | Rows absent (not `0`) when `session_rate`/`shift_rate` are `null` | Confirmed in component logic (`!= null` gates) and covered by 4 dedicated tests | PASS |
| F-05 | PrintablePayslip shows "tỷ lệ riêng"/"tỷ lệ chung" correctly | `PrintablePayslip.test.tsx`: staff_override → "tỷ lệ riêng", clinic_default → "tỷ lệ chung" | Correct label per source | Both cases pass | PASS |
| F-06 | PrintablePayslip: no-account staff renders fully | Payslip type has no `user_id` field at all — nothing account-related in the component | Renders code/name from payslip only | Confirmed by design + test suite (10th test in file) | PASS |
| F-07 | Export button → correct URL/month/Authorization header | `PayrollPage.export.test.tsx` | `GET /api/v1/payroll/export?month=...` with bearer token | Covered, passing | PASS |
| F-08 | Row print action opens/closes modal for the right staff member | `PayrollPage.export.test.tsx` | Modal opens with correct `payslip` prop, closes | Covered, passing | PASS |
| F-09 | PayrollPage footer "Tổng thực nhận" aligns under the "Thực nhận" column after the new "In phiếu" column | **Round 1** (`d59942f`): source inspection — header `<th>` count (15) vs `tfoot` `colSpan` (14) + 1 unspanned `<td>`. **Round 2** (`d271e00`): re-ran `PayrollPage.export.test.tsx`'s new regression test (`labelColSpan === thucNhanIndex`, 0-based) + re-inspected the diff | Total value lands under "Thực nhận" (col 14) | **Round 1**: landed under **"In phiếu"** (col 15) — misaligned, filed as BUG-001. **Round 2**: `colSpan` reverted 14→13; value now lands on "Thực nhận" (index 13, 0-based) — new test asserts this exact invariant and passes | **FAIL (round 1) → PASS (round 2, BUG-001 fixed in `d271e00`)** |
| F-11 | New regression test genuinely exercises the alignment invariant (not a tautology) | Inspect `PayrollPage.export.test.tsx`'s new `describe("... footer alignment regression (BUG-001)")` block: asserts `headers.length === thucNhanIndex + 2` (print column exists after "Thực nhận"), `footerCells.length === 2`, `labelColSpan === thucNhanIndex` (not `headers.length - 1`, which is the exact off-by-one BUG-001 regressed to), and the value cell's text | Test correctly ties `colSpan` to the "Thực nhận" header position rather than total header count | Confirmed by reading the test source — it fails against the pre-fix `colSpan={14}` per the implementer's own verification note in BUG-001.md ("Confirmed the new test fails against the pre-fix `colSpan={14}` (`expected 14 to be 13`)") and passes against `d271e00` | PASS |
| F-10 | "Ghi vào chi phí" button still works (no regression) | Source/test inspection — button untouched by this diff | Still present and functional | Present in `PayrollPage.tsx`, no diff to its handler; not otherwise re-tested at UI level (no behavioral change in scope) | PASS |

## 4. Playwright E2E

| ID | Description | Result |
|----|---|---|
| E-01 | Full browser E2E walkthrough (export button, print modal, print preview) | **SKIPPED** — would require standing up a full FE+BE dev stack (login, navigate, seed payroll data via UI) beyond the disposable-container scope used for API-level testing; the reviewer's OPTIONAL clause allows skipping when it needs extra stack build-out. The functional core (export correctness, RBAC, tenancy, printable content/i18n) is already covered end-to-end at the API/component level above (I-01…I-16, F-01…F-10). Recommend a follow-up manual/Playwright pass once BUG-001 is fixed. |

## 5. Out-of-scope / not re-verified (by design)

| Item | Reason |
|---|---|
| Blended commission rate (m2/m3) full multi-service-type reconciliation via real invoices | User decision on record: **KEEP AS-IS** (implementation-to-review.md "Fix round 1"). The mapping logic itself (rate%/source columns) is exhaustively unit-tested (`test_procedure_commission_staff_override_source_label`, `test_medicine_commission_clinic_default_source_label`, etc.); constructing a full real-invoice multi-rate scenario was judged not to change the pass/fail verdict for a documented, accepted behavior, and was descoped to keep this test round proportionate. |
| m5 (unknown `rate_source` blanks instead of falling back) | Explicitly called out by reviewer as "not blocking", cosmetic, follow-up only — not re-tested. |
