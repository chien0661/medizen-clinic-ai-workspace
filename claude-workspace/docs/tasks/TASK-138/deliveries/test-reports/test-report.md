# Test Report: TASK-138 — Payroll per_session/per_shift + per-staff commission

**Test Agent:** Automation Tester
**Date:** 2026-08-07
**Status:** ✅ ALL PASSED
**Branch:** `feature/TASK-138-payroll-session-shift` — BE `_feat138-be` @ `cebf0bd`, FE `_feat138-web` @ `4bf1b55`

## Environment

- Host Python is 3.10 (app needs 3.11) → all BE execution ran inside Docker, image `clinic_e2e-api`.
- **Shared stack** (`clinic_e2e_api/postgres/redis/ui/worker`) was left running, untouched, throughout — never stopped/restarted/migrated.
- **DB-integration / migration / API tests** ran against **disposable** containers on a private Docker network (`test138net`), created and torn down by this test pass:
  - `test138_pg` — `postgres:15-alpine`, same extensions as `_dev-be/docker/postgres-init.sql`.
  - `test138_redis` — `redis:7-alpine` (needed for the API-layer test pass: login flow, rate limiter, feature-flag cache).
  - Both containers and the network were removed at the end of this run.
- FE tests ran on host: `cd _feat138-web && npx vitest run --silent`.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|---------------|
| BE Unit (full suite regression) | 1145 | 1133 | 12 (pre-existing) | 100%* |
| FE Unit (full suite regression) | 1264 | 1260 | 4 (pre-existing) | 100%* |
| DB Integration (payroll/commission/claw-back engine) | 15 | 15 | 0 | 100% |
| Migration 0077 (real-data upgrade/downgrade) | 5 | 5 | 0 | 100% |
| API Contract / RBAC / Tenancy | 9 | 9 | 0 | 100% |
| Business Rule (staff without account) | 3 | 3 | 0 | 100% |
| **TOTAL new-code scenarios** | **34** | **34** | **0** | **100%** |

\* Success rate against the *known pre-existing baseline* — the 12 BE / 4 FE failures are identical, by test ID, to the documented dev-clean failures; zero new failures introduced by this branch.

## Commands Run

```bash
# BE full unit suite
docker run --rm -v "F:/MyProject/clinic-cms-workspace/_feat138-be:/work" -w /work \
  clinic_e2e-api python -m pytest tests/unit -q

# FE full suite
cd _feat138-web && npx vitest run --silent

# Disposable stack for DB-integration / migration / API tests
docker network create test138net
docker run -d --name test138_pg --network test138net -e POSTGRES_DB=cms -e POSTGRES_USER=cms \
  -e POSTGRES_PASSWORD=cms -v ".../_dev-be/docker/postgres-init.sql:/docker-entrypoint-initdb.d/01-extensions.sql:ro" \
  postgres:15-alpine
docker run -d --name test138_redis --network test138net redis:7-alpine
docker run --rm --network test138net -e DATABASE_URL=postgresql+asyncpg://cms:cms@test138_pg:5432/cms \
  -v "F:/MyProject/clinic-cms-workspace/_feat138-be:/work" -w /work clinic_e2e-api alembic upgrade head

# Engine/commission/claw-back scenarios (standalone script, ORM + real service calls, NOT part of the repo)
docker run --rm --network test138net -e DATABASE_URL=... -e PYTHONPATH=/work \
  -v "_feat138-be:/work" -v "<scratchpad>:/scratch" -w /work clinic_e2e-api python /scratch/task138_integration.py

# Migration downgrade-with-collision-data (isolated seed, then CLI)
docker run --rm ... clinic_e2e-api python /scratch/task138_downgrade_seed.py
docker run --rm ... clinic_e2e-api alembic downgrade -1
docker run --rm ... clinic_e2e-api alembic upgrade head

# API/RBAC (temporary pytest file, added then REMOVED from the worktree after the run — see "Test Files" below)
docker run --rm --network test138net -e DATABASE_URL=... -e REDIS_URL=redis://test138_redis:6379/0 \
  -e JWT_SECRET=e2e-test-secret-not-for-prod-min32chars-ok -e ENVIRONMENT=development \
  -v "_feat138-be:/work" -w /work clinic_e2e-api python -m pytest tests/integration/test_task138_commission_rule_api_TEMP.py -q
```

## Results by Scope Area

### 1. BE full unit suite regression
`1133 passed, 12 failed`. Diffed the failing test IDs against the documented pre-existing set — **exact match**: `test_email.py::test_all_templates_render_in_both_langs`, `test_erasure_service.py::...test_last_accessed_at_updated_on_read`, `test_feature_flags.py::test_get_flag_value_returns_false_for_unknown_flag`, `test_medicine_stock_status.py` ×4, `test_rls_helpers.py` ×2, `test_tenancy_middleware.py` ×3. **Zero new failures.** All 40+ TASK-138 unit tests (payroll branches, resolve-rate precedence, clinic-scope validation, claw-back symmetry, m4 rate/source) pass.

### 2. FE full unit suite regression
`1260 passed, 4 failed`. Failing tests, confirmed identical to the documented list: `ForgotPasswordPage > handles 404 gracefully`, `QueuePage > shows empty state when no visits`, `QueuePage > renders a visit card when visits exist`, `AttendanceWidget > M-14: DOES call hrApi.myShifts` (the documented date-flaky test). **Zero new failures.**

### 3. DB Integration — Payroll Engine
See test-cases.md §C (INT-01..INT-15). All 15 scenarios pass, covering: `per_session` full+half days, no-attendance-grid-data (confirmed **no** fallback to legacy TimeLog count even with a non-zero legacy count present — this was the reviewer's top concern and is verified end-to-end against real `AttendanceDay`/`TimeLog` rows), `per_shift` completed-only counting, rate≤0 drop-off vs. `_empty_slip` commission-only path, allowance/bonus/penalty applying to the new pay types with OT forced to 0, monthly/hourly regression with populated-but-unused new rate fields, period boundaries, per-staff commission override vs. clinic-wide fallback with payslip `rate_percent`/`rate_source` traceability (this is the concrete verification of the m4 fix in `cebf0bd`), claw-back symmetry at the override rate (not clinic-wide) including a mixed two-doctor batch, claw-back idempotency, claw-back on an unposted period, claw-back for an unmapped doctor, and the TASK-128 zero-override regression.

All scenarios ran against a real disposable Postgres migrated 0001→0077, using actual `AttendanceDay`/`Shift`/`TimeLog`/`Visit`/`VisitService`/`Prescription`/`PrescriptionItem`/`Invoice`/`InvoiceLine`/`CommissionRule` rows — not mocked data. The claw-back path exercised the real `record_invoice_clawback` → `_compute_and_record_clawback` DB-orchestration wiring (candidate-doctor gathering, `load_rate_maps`, the raw-SQL invoice-line joins), which the reviewer flagged as the code unit tests cannot reach.

### 4. Migration 0077 on real data
See test-cases.md §D (MIG-01..MIG-05). Fresh upgrade 0001→0077 verified column-by-column and index-by-index. The exact collision scenario the reviewer called out (clinic-wide rule + per-staff override coexisting on the same `service_type_id`, plus the same for `medicine`) was seeded, and `alembic downgrade -1` — which aborted before the implementer's fix-round-1 m2 fix — now **succeeds**: override rows are discarded, the clinic-wide rate survives, old 0073 indexes are restored, and a subsequent `alembic upgrade head` succeeds cleanly.

One additional, **informational** finding (MIG-05): downgrading a DB that has `staff_profile` rows with `pay_type='per_session'` fails on the `pay_type` VARCHAR(20)→VARCHAR(10) narrowing step. This is **not a new bug** — it is explicitly documented in the migration's own module docstring as accepted, expected behavior ("will fail if any row holds 'per_session'/'per_shift' at downgrade time — expected, since those values have nowhere to fit in the old schema"), and is a separate, pre-acknowledged data-loss caveat from the commission_rule one the m2 fix addressed. Confirmed behavior matches the documentation; not filed as a bug.

### 5. API Surface / RBAC / Tenancy
See test-cases.md §E (API-01..API-09). Ran against the real app (`httpx.AsyncClient` + `ASGITransport`) with real login, real JWT, real Postgres + Redis — not mocked. Covers: valid same-clinic `staff_id` create; cross-clinic `staff_id` → 404 not 500, no row written; non-existent `staff_id` → 404 not 500; clinic-wide (`staff_id=None`) path unaffected; a staff member **without a login account** (nurse, `user_id=NULL`) is a valid override target; `staff_id` is immutable via PATCH (schema has no such field — attempting to pass it is silently ignored, confirmed via response); DELETE of an override reverts the filtered list to empty (staff reverts to the clinic-wide fallback on the next payroll run, per the DB-level verification in INT-14/§3); `GET ?staff_id=` filtering plus tenant isolation (clinic B never sees clinic A's rules, filtered vs. unfiltered counts correct); RBAC — a `receptionist` role (no `payroll.manage`) gets 403 on all four commission-rule endpoints.

### 6. Business Rules — Staff Without Login Account
See test-cases.md §F. Nurses/other `user_id IS NULL` staff can be configured for `per_session`/`per_shift` pay and produce a correct payslip end-to-end (BR-01, DB level), and can be selected as a per-staff commission-override target in the API (BR-02). The pre-existing TASK-128 limitation — automatic commission attribution still requires a linked doctor account (`staff_profile.user_id`) — is unchanged by this task (BR-03, confirmed by code inspection: no change to the recipient-resolution code path in `commission_service`, only to which *rate* applies once a recipient is already resolved).

### 7. FE
Covered entirely by the FE full-suite regression (§2/scope area 2) — the 21 new/modified TASK-138 FE tests (`StaffFormPage.test.tsx` — pay-type selects, hidden OT field, stale-field-not-sent-on-switch; `PayrollPage.test.tsx` — buổi/ca breakdown rendering, i18n labels, override/default rate badges; `CommissionKpiConfigPage.test.tsx` — per-staff section, general-table filtering, fallback display; `i18n-hr.test.ts` — key parity) all pass within that run. No separate FE-only script was needed.

## Acceptance Criteria Verdict (task.md)

| # | AC | Verdict | Evidence |
|---|----|---------|----------|
| 1 | `per_session`/`per_shift` staff paid = đơn giá × số buổi/ca thực tế, khớp chấm công; `monthly`/`hourly` không đổi | ✅ MET | INT-01, INT-02, INT-03, INT-07, INT-08 |
| 2 | Staff có tỷ lệ chiết khấu riêng dùng tỷ lệ riêng; không cấu hình riêng dùng tỷ lệ chung (regression TASK-128) | ✅ MET | INT-09, INT-10, INT-14, API-01..API-08 |
| 3 | Payslip breakdown truy vết được: kiểu lương, số buổi/ca, đơn giá, **tỷ lệ commission áp dụng (riêng hay chung)** | ✅ MET — **previously an open gap (m4), now closed in `cebf0bd`.** INT-09 directly asserts `procedure_rate_percent`/`procedure_rate_source` on the payslip for both the override (`staff_override`, 15.0) and clinic-wide (`clinic_default`, 10.0) cases. FE `PayrollPage.test.tsx` (in the FE full-suite run) confirms the corresponding UI badge. |
| 4 | Unit test BE (engine + resolve rate) + FE (form config, PayrollPage breakdown); integration test với dữ liệu ca/chấm công thật | ✅ MET | Unit: §1/§2 (pre-existing, unchanged from review handoff). Integration: this test phase closes the gap explicitly flagged by the reviewer (`review-to-test.md` — "no integration or E2E coverage for any TASK-138 path exists") — see §3/§4/§5 above, all against real Postgres data. |

**All four acceptance criteria are verifiably met.**

## Coverage of the Reviewer's Testing Focus List (`review-to-test.md`)

| Focus area | Covered by | Status |
|---|---|---|
| 1. Payroll engine against live Postgres — full/half days, no-grid-data, per_shift completed-only, rate≤0, allowance/bonus/penalty + OT=0, monthly/hourly regression, period boundaries | INT-01..INT-08, INT-15 | ✅ Fully covered |
| 2. Claw-back symmetry E2E — override rate, mixed batch, TASK-128 regression, unmapped doctor, period-not-posted, savepoint isolation | INT-09..INT-14 | ✅ Covered — savepoint isolation verified via idempotent double-call + successful outer commit (INT-11); a *forced internal exception* inside the claw-back body (to prove the savepoint rollback itself, not just idempotency) was **not** separately injected — see Skipped below |
| 3. Migration 0077 on real data — widening + rebuilt indexes on existing rows, collision coexistence, downgrade with collision data | MIG-01..MIG-04 | ✅ Fully covered |
| 4. API surface / RBAC / tenancy — cross-clinic 404, non-existent 404, `staff_id=None` unaffected, PATCH immutability, RBAC 403, GET filter + tenant isolation, delete-reverts-to-fallback | API-01..API-09 | ✅ Fully covered |
| 5. Frontend flows — StaffFormPage, PayrollPage, CommissionKpiConfigPage, staff-without-account end-to-end | FE full-suite (§2/§7) for unit-level; DB/API level for the staff-without-account flow (INT-15, API-05) | ✅ Covered at unit + DB/API level; UI-driven (Playwright) walkthrough not run — see Skipped |

## Known Open Item Carried Forward (not a defect — per reviewer's handoff)

- **m3 (i18n debt)** — the new "Chiết khấu riêng theo nhân sự" section and StaffFormPage labels remain hardcoded Vietnamese, matching those two pages' pre-existing (zero `useTranslation`) convention. Not re-tested as a defect; carried forward as documented technical debt per the reviewer's own conclusion.
- **m4 was the one open acceptance-criteria gap** flagged by the reviewer as needing a decision before close — it has since been **fixed** (commit `cebf0bd`) and is now verified as MET above (AC #3). Surfaced here per the reviewer's explicit request ("Please surface this in the test report so it doesn't close silently") — it should now be considered **resolved**, not open.

## Skipped (with reasons)

1. **UI E2E via Playwright against a live browser stack** — explicitly marked optional in the task brief. Skipped because it would require rebuilding the shared `clinic_e2e` stack's `api`/`ui` images against this feature branch (the running shared stack is on `dev`, not `feature/TASK-138-payroll-session-shift`), which the task brief says to avoid disturbing. FE behavior for all three touched pages (StaffFormPage, PayrollPage, CommissionKpiConfigPage) is covered at the unit level (§2/§7) plus the underlying data flow at DB/API level (INT-15, API-05); this is considered adequate given the explicit "optional" framing.
2. **A forced internal exception inside `_compute_and_record_clawback`'s body**, to directly observe the `SAVEPOINT` rollback (as opposed to observing its *effect* via idempotent re-calling, which was tested in INT-11) — would require either a source-code fault injection (out of scope: Test Agent does not modify source) or a contrived DB state expected to raise partway through the function (e.g., a manufactured constraint violation), which risks being unrepresentative of any real failure mode. INT-11's idempotent double-call plus successful outer `commit()` is treated as sufficient evidence that the savepoint boundary does not leak into the caller's transaction.

No test files were left behind: the temporary API/RBAC pytest file (`tests/integration/test_task138_commission_rule_api_TEMP.py`) was removed from the `_feat138-be` worktree after this run (`git status` confirmed clean). The standalone DB-integration verification script and its downgrade-seed companion live only in this session's scratchpad, outside both repos.

## Next Steps

All tests passed successfully (34/34 new-code scenarios; zero new regressions in either full unit suite). All four acceptance criteria verifiably met, including the previously-open m4 gap (now closed and verified). Ready to proceed to the Documentation phase.

**`docs/tasks/TASK-138/task.md` status → `DOCUMENTING`; "Testing" ticked in Progress Checklist.**

---

**Test Execution Time:** ~2.5 hours (including disposable-environment setup/teardown)
**Total Scenarios:** 34 new-code scenarios (+ 2 full-suite regression runs covering 2409 pre-existing tests)
**Environment:** Docker (`clinic_e2e-api` image) + disposable Postgres/Redis (`test138net`, torn down after the run) + host vitest
