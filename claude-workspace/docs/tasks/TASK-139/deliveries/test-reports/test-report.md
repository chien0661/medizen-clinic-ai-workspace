# Test Report: TASK-139 - Payroll: xuất bảng lương Excel + phiếu lương PDF từng nhân viên

**Test Agent:** Automation Tester
**Date:** 2026-08-08 (round 1), 2026-08-08 (round 2 — BUG-001 re-test)
**Status:** ✅ ALL PASSED (round 2) — round 1 found BUG-001 (footer column misalignment on PayrollPage), fixed in FE `d271e00`, verified below.

**Code under test:** BE `_feat139-be @ 37b258d` (unchanged since round 1), FE `_feat139-web @ d271e00` (round 1 was `d59942f`) — branch `feature/TASK-139-payroll-export`, based on `feature/TASK-138-payroll-session-shift`.

**Overall verdict: PASS.** Round 1's only failure (BUG-001) is fixed and verified; no new failures introduced. See "Re-test round 2" section near the end for the targeted re-test evidence.

## Environment

- **BE unit tests**: `docker run --rm -v _feat139-be:/work -w /work clinic_e2e-api python -m pytest tests/unit -q` (existing shared image, read-only mount, no DB).
- **BE integration/export-correctness tests**: a fully **disposable** stack, never touching the shared `clinic_e2e_*` containers:
  - `clinic_t139_pg` (postgres:15-alpine, isolated network `clinic_t139_net`)
  - `clinic_t139_redis` (redis:7-alpine)
  - `clinic_t139_api` — image built fresh from the `_feat139-be` worktree (`docker build -f Dockerfile .`) at commit `37b258d`, started with `alembic upgrade head` (reached **0077**, TASK-138's migration) then `uvicorn`.
  - All three containers, the image, and the network were removed at the end of the session (`docker rm -f` ×3, `docker network rm`, `docker rmi`). Verified the shared `clinic_e2e_*` containers were untouched throughout (`docker ps` before/after).
- **FE tests**: `npx vitest run` directly on the `_feat139-web` worktree (host Node 20.20.0/npm 10.8.2) — no DB/containers needed.
- **Playwright E2E**: not run — see Skips.

## Test Statistics

*(Round 1 numbers below; round 2 is a targeted re-test of just the FE regression/full-suite rows —
see "Re-test round 2" for its own numbers. Round 2 superseded the FE regression-verification row's
FAIL with a PASS.)*

| Test Type | Scenarios | Passed | Failed | Skipped |
|-----------|-----------|--------|--------|---------|
| BE unit (regression, full suite) | 1168 | 1156 | 12 (pre-existing baseline, 0 new) | 0 |
| BE unit — new TASK-139 files | 23 | 23 | 0 | 0 |
| BE integration (disposable stack) | 22 | 22 | 0 | 0 |
| FE unit/component (regression, full suite) — round 1 | 1285 | 1282 | 3 (pre-existing baseline, 0 new) | 0 |
| FE unit/component (regression, full suite) — round 2 | 1286 | 1283 | 3 (pre-existing baseline, 0 new) | 0 |
| FE unit — new TASK-139 files (round 1: 21; round 2: +1 regression test = 22) | 22 | 22 | 0 | 0 |
| FE regression-verification (source/manual) | 2 | 2 (round 2) | 0 (round 1 had 1 — BUG-001, now fixed) | 0 |
| Playwright E2E | 1 | 0 | 0 | 1 (scope decision) |
| **TOTAL (test-cases.md rows)** | **28** | **27** | **1** | **1 (E2E)** |

Full per-scenario detail: `docs/tasks/TASK-139/deliveries/test-cases/test-cases.md`.

## Commands run and raw results

```
# BE full unit regression
docker run --rm -v _feat139-be:/work -w /work clinic_e2e-api python -m pytest tests/unit -q
  -> 12 failed, 1156 passed, 33 warnings in 40.65s
  Failures (exact same 12 as documented baseline / prior review rounds):
    integrations/test_email.py::TestTemplates::test_all_templates_render_in_both_langs
    test_erasure_service.py::TestLastAccessedAtUpdateOnRead::test_last_accessed_at_updated_on_read
    test_feature_flags.py::test_get_flag_value_returns_false_for_unknown_flag
    test_medicine_stock_status.py::TestMedicineSearchResultSchema:: (×4)
    test_rls_helpers.py::TestApplyRLSWithTenantIsolation::test_executes_three_statements
    test_rls_helpers.py::TestRemoveRLS::test_executes_three_statements
    test_tenancy_middleware.py::TestDevHeaders:: (×2), TestJWTBearer::test_valid_jwt_passes

# New BE unit files
docker run ... pytest tests/unit/test_payroll_export.py tests/unit/test_payroll_export_route_validation.py -q
  -> 23 passed in 1.37s

# Disposable stack: migrations
docker run -d clinic_t139_api ... alembic upgrade head && uvicorn ...
  -> ... Running upgrade 0076 -> 0077, Payroll per-session/per-shift pay types + per-staff commission (TASK-138).
  -> Uvicorn running on http://0.0.0.0:8000

# Repo's own integration suite, against the disposable Postgres
docker run --rm --network clinic_t139_net -v _feat139-be:/work clinic_t139_api python -m pytest tests/integration/test_payroll_export_e2e.py -v
  -> 6 passed, 6 warnings in 7.90s   (no teardown ERROR in the summary line)

# Fixture-leak check (TASK-140 follow-up), disposable DB, after the run above
psql -U cms -d cms -c "select count(*) from clinic where code like 'PX%' ... union all select count(*) from clinic ..."
  -> clinic_PX=0, user_px=0, staff_profile_leftover=0, user_role_leftover=0, account_clinic_role_leftover=0,
     clinic_total=0, user_total=0

# Manual scenario script (mixed staff, cross-tenant, RBAC, malformed month) — see "Additional coverage" below
docker run --rm --network clinic_t139_net -v _feat139-be:/work -v <scratch>/zz_task139_manual.py:/work/tests/integration/zz_task139_manual.py clinic_t139_api python -m pytest tests/integration/zz_task139_manual.py -v
  -> 11 passed, 13 warnings in 10.35s

# FE full suite (×3 runs to check for flake)
npx vitest run --silent
  Run 1: 5 failed | 1280 passed  (2 EXTRA failures vs baseline — see "FE flake" below)
  Run 2: 3 failed | 1282 passed  (matches documented baseline exactly)
  Run 3: 3 failed | 1282 passed  (matches documented baseline exactly)
  Baseline failures (all 3 runs): ForgotPasswordPage > "handles 404 gracefully" , QueuePage > "shows empty state", QueuePage > "renders a visit card when visits exist"

# New FE files, isolated
npx vitest run --silent src/tests/hr/PrintablePayslip.test.tsx src/tests/hr/PrintPayslipModal.test.tsx src/tests/hr/PayrollPage.export.test.tsx
  -> 3 files, 21 passed
```

## Additional coverage built for this test round (beyond the shipped suite)

The reviewer's `review-to-test.md` asked for scenarios the shipped test suite doesn't cover: a genuinely
mixed staff set (monthly + `per_session` with a half-day + `per_shift` + commission-only + no-account +
formula-injection name) reconciled cell-by-cell against `GET /hr/payroll`, a **real** two-clinic
cross-tenant check (the shipped test only seeds one clinic), a forged `X-Clinic-Id` header probe, a
`doctor`-role RBAC check (shipped test only covers `receptionist`), and more `month` malformation
variants. These were written as a throwaway pytest file (`zz_task139_manual.py`, mirrors the shipped
`px_ctx` fixture pattern) bind-mounted into the disposable API container for a single run — **not** part
of the repo, does not modify source, and was not written to `_feat139-be`'s working tree at any point
(mounted at `/work/tests/integration/zz_task139_manual.py` inside the container only). Key results:

- **Cell-by-cell reconciliation** (monthly, `per_session` 1.5 worked days [1 present + 1 half day], `per_shift`
  2 completed + 1 cancelled shift, no-account staff, formula-injection name) — every checked cell matched
  the `GET /hr/payroll` response for the same staff/month, including the money-as-number and
  blank-vs-zero requirements.
- **Formula injection**: a staff named `=cmd|'/c calc'!A1` round-tripped through the real xlsx write+read
  as the literal string `"'=cmd|'/c calc'!A1"` with openpyxl `data_type == "s"` (never `"f"`) — the
  shared `build_xlsx_response` neutraliser holds for this new endpoint too.
- **Real two-clinic cross-tenant isolation**: clinic B's staff never appeared in clinic A's export for
  the same month (the shipped test only ever seeds one clinic, so this closes reviewer finding **m4**'s
  underlying concern for at least this test round — recommend the shipped integration test itself be
  strengthened per m4, still open as a follow-up since I did not modify source/tests).
- **Forged `X-Clinic-Id`**: clinic A's token + a `X-Clinic-Id` header pointing at clinic B returned clinic
  A's own data (200, B's staff absent) — the header is not honoured by the tenancy layer, consistent
  with the reviewer's read of `_clinic_id()`.
- **`doctor` role** (not just `receptionist`) correctly gets 403.
- **9 malformed `month` variants** (including `%0d%0a` URL-style CRLF and an empty string, beyond the 8
  already covered by the shipped unit test) all correctly 422.
- **Teardown**: my own script's fixtures fully cleaned up — `clinic_total=0`/`user_total=0` in the
  disposable DB afterward, no leaks from this script either.

## FE flake (not a regression)

The first of three `vitest run` passes showed 5 failures (3 baseline + `CommissionKpiConfigPage.test.tsx`
×2, an unrelated pre-existing test file never touched by this task) while the total pass/fail count summed
to the same 1285 tests. Re-running twice more reproduced the documented baseline exactly (3 failed / 1282
passed) both times. This reads as environment/timing flake in an unrelated `waitFor` (`getByRole("heading")`)
in `CommissionKpiConfigPage`, not something TASK-139 touches or introduces — recorded here for visibility,
not filed as a TASK-139 bug.

## Fixture-leak / teardown observation for TASK-140 (as instructed)

Contrary to the reviewer's finding against the **shared** `clinic_e2e_postgres` (5 leaked `PX%` clinics +
10 leaked `px_*` users after a run), re-running the exact same `tests/integration/test_payroll_export_e2e.py`
against a **fresh, single-tenant, disposable** Postgres left **zero** leftover rows (`clinic_total=0`,
`user_total=0` after the run) and the pytest summary line showed no teardown ERROR (`6 passed, 6 warnings`).

This does not contradict the reviewer's M1 finding — it's a different environment:
- The shared DB has months of accumulated state (1,731 clinics / 2,410 users per the review) and many
  concurrent/sequential test files hitting it; a single isolated run here can't reproduce whatever
  interaction (connection pooling, concurrent sessions, GUC/tenant-context bleed between tests) causes
  the final two `DELETE` statements to silently no-op there.
- It does confirm the teardown SQL *itself* is correct in isolation — the bug (if any) is likely
  concurrency- or session-state-dependent, not a logic error in the DELETE statements' order/content.

**Per the instructions**: reporting this observation only, no cleanup attempted on any shared container,
no code changes made. Recommend the TASK-140 follow-up investigate under concurrent load / repeated runs
against a long-lived DB rather than a single fresh run, since that's where the discrepancy would surface.

## Acceptance Criteria verdict (task.md)

| AC | Verdict | Evidence |
|---|---|---|
| Xuất Excel kỳ có dữ liệu → đủ dòng, đúng nhân viên (kể cả buổi/ca và commission override) | ✅ PASS | I-03, I-04, I-05 (test-cases.md); commission override mapping covered by BE unit tests (`test_procedure_commission_staff_override_source_label`) |
| Kỳ không có dữ liệu → header-only hoặc 4xx rõ ràng, không 500 | ✅ PASS | I-06 |
| Phiếu lương in đúng breakdown, đối chiếu override 15% vs rate chung | ✅ PASS | F-04, F-05 |
| RBAC 403 không có `payroll.manage`; unit test BE+FE | ✅ PASS | I-09, I-10, I-11, F-02 |
| Không regression PayrollPage hiện có | ✅ **PASS** (round 2) | Round 1: ❌ FAIL (F-09 / BUG-001 — footer total rendered under "In phiếu" instead of "Thực nhận"). Round 2: fixed in FE `d271e00` (`colSpan` reverted 14→13) — verified via re-inspection + the new regression test in `PayrollPage.export.test.tsx`, both passing. See "Re-test round 2" section below. |

## Skips

- **Playwright browser E2E** — skipped per the task's explicit "OPTIONAL — skip if it needs rebuilding
  shared stack" allowance. A full click-through (export button → download, print button → modal →
  browser print preview) would require standing up FE+BE dev servers with seeded UI-visible data, beyond
  what the disposable API-container approach supports without extra build-out. The functional surface
  (export correctness, RBAC, tenancy, printable content mapping, i18n) is otherwise fully covered above.
  Recommend a manual/Playwright pass after BUG-001 is fixed, since the footer bug is itself a
  visually-observable defect.

## Bug found (round 1) — fixed and verified in round 2

- **BUG-001** (Medium) — `src/pages/hr/PayrollPage.tsx` footer `colSpan` bumped 13→14 alongside the new
  "In phiếu" header column, which shifted the "Tổng thực nhận" total value cell to render under "In
  phiếu" instead of "Thực nhận". Full detail, line references, root cause, and the fix:
  `docs/tasks/TASK-139/bugs/BUG-001.md` (Resolution section filled in by Implementation Agent).
  **Status: RESOLVED**, see round 2 below.

---

## Re-test round 2 (2026-08-08) — targeted, BUG-001 fix verification

**Trigger**: coordinator reported BUG-001 fixed in FE commit `d271e00` — "`PayrollPage` tfoot label
`colSpan` reverted 14→13 (total now aligns under 'Thực nhận'), plus a new regression test block in
`src/tests/hr/PayrollPage.export.test.tsx` asserting footer alignment." **BE is unchanged since round 1
(`37b258d`) — no BE re-run performed, per the coordinator's explicit instruction and confirmed via
`git log -1` on `_feat139-be` showing the same commit.**

### 1. Verified the fix directly

`git diff d59942f d271e00 -- src/pages/hr/PayrollPage.tsx`:
```diff
-                  <td colSpan={14} ...>
+                  <td colSpan={13} ...>
                     Tổng thực nhận
                   </td>
```
Matches the bug report's suggested fix exactly (revert to 13, do not bump for trailing action columns).

### 2. Verified the new regression test is genuine, not a tautology

`git diff d59942f d271e00 -- src/tests/hr/PayrollPage.export.test.tsx` adds a new
`describe("PayrollPage — TASK-139 footer alignment regression (BUG-001)")` block that:
- Reads the actual rendered `<th>` headers, finds the 0-based index of "Thực nhận" (`thucNhanIndex`).
- Asserts `headers.length === thucNhanIndex + 2` — i.e. explicitly confirms the "In phiếu" trailing
  action column exists **after** "Thực nhận", so the test can't pass vacuously if that column were ever
  removed.
- Reads the actual `tfoot` row's two `<td>` cells, and asserts `labelColSpan === thucNhanIndex` (not
  `headers.length - 1`, which is exactly the off-by-one BUG-001 regressed to) — this ties the invariant
  to "wherever 'Thực nhận' actually is," not to "total column count minus one," so a future column
  addition anywhere in the table would correctly fail this test if the same mistake were repeated.
- Also asserts the value cell's rendered text (`"20.000.000"`) to confirm it's still the correct total.

This is a correct, meaningful regression guard — confirmed independently by reading the test logic, not
just trusting the implementer's description. The implementer's own verification note in
`BUG-001.md`'s Resolution ("confirmed the new test fails against the pre-fix `colSpan={14}`
(`expected 14 to be 13`) and passes with the fix restored") is consistent with what the test's logic
would actually produce given the pre-fix code — plausible and not re-verified against the old commit
directly (not necessary: the diff and current-state run below are conclusive).

### 3. Ran the new test + related payroll FE files

```
npx vitest run --silent src/tests/hr/PayrollPage.export.test.tsx src/tests/hr/PayrollPage.test.tsx \
  src/tests/hr/PrintablePayslip.test.tsx src/tests/hr/PrintPayslipModal.test.tsx
  -> 4 files, 32 passed (was 31 in round 1 — +1 for the new regression test)
  -> PayrollPage.export.test.tsx: 5 passed (was 4 in round 1)
```

### 4. Full FE vitest suite (1 run — targeted re-test, not repeated ×3 since round 1 already
   established the flake source is unrelated to this task)

```
npx vitest run --silent
  -> Test Files  2 failed | 136 passed (138)
  -> Tests       3 failed | 1283 passed (1286)
  Failures (identical names/count to round 1's stable baseline):
    ForgotPasswordPage > "handles 404 gracefully (BE not yet live) — shows success"
    QueuePage > "shows empty state when no visits"
    QueuePage > "renders a visit card when visits exist"
```
Zero new failures. Total test count is 1286 (was 1285 in round 1) — the +1 is the new BUG-001 regression
test, accounted for. AttendanceWidget M-14 (flagged by the coordinator as possibly flaky) did **not**
trigger in this run. The `CommissionKpiConfigPage` flake seen in round 1's first run also did not
recur — consistent with round 1's conclusion that it's unrelated, timing-based flake.

### 5. Worktree cleanliness

`git status --short` on `_feat139-web`: clean (no stray files). `_feat139-be` confirmed unchanged at
`37b258d`, also clean.

### Round 2 verdict: **PASS**

BUG-001 is fixed, verified via source diff + a genuine (non-tautological) regression test that itself
passes, and the full FE suite shows zero new failures against the established baseline. Combined with
round 1's otherwise-clean BE (unchanged, still valid) and FE results, **all TASK-139 acceptance criteria
are now met.**

## Next Steps

**All tests passed.** Round 1's only failure (BUG-001) is fixed and verified in round 2. Ready to
proceed to Documentation phase.

**task.md status → DOCUMENTING**, "Testing" ticked in the Progress Checklist. Handoff:
`docs/tasks/TASK-139/handoff/test-to-documentation.md`.

---

**Test Execution Time:** Round 1 ~35 minutes; Round 2 (targeted) ~10 minutes.
**Total Scenarios:** 29 (test-cases.md, +1 for the BUG-001 regression-test verification row)
**Environment:** disposable Docker stack (BE, round 1 only) + host Node (FE, both rounds) — see
"Environment" above. Round 2 required no Docker/disposable-stack work since BE was unchanged.
