# Handoff: TASK-126 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW

## Summary

Implemented the Service Usage report (BE endpoint + FE page) per the implementation plan: usage count + revenue per service, joined to the TASK-125 `service_type` classification, over a clinic-local date range, with an optional `doctor_id` filter. Excel export added. No migration needed (reads `service_type_id` live via join — TASK-125 already merged to dev).

## Repos / Branches

- Backend: `F:/MyProject/clinic-cms-workspace/_feat126-be`, branch `feature/TASK-126`, pushed to `origin/feature/TASK-126`.
- Frontend: `F:/MyProject/clinic-cms-workspace/_feat126-web`, branch `feature/TASK-126`, pushed to `origin/feature/TASK-126`.
- **Not merged to dev** — manager coordinates merges. `main` and the w2e stack (ports 9999/5434/5436/6380/6382) were not touched.

## Files Changed

### Backend (`_feat126-be`)
- `app/modules/reports/services/service_usage_service.py` (new) — aggregation query (`get_service_usage`).
- `app/modules/reports/schemas/report_schemas.py` (modified) — `ServiceUsageRow` + `ServiceUsageReport`.
- `app/modules/reports/api/routes.py` (modified) — `GET /reports/service-usage` + `GET /reports/service-usage/export`, gated `report.financial`.
- `tests/unit/reports/test_report_schemas.py` (modified) — 3 new schema tests.
- `tests/integration/reports/test_service_usage_e2e.py` (new) — 7 e2e tests (real-DB style, see Test Results).

### Frontend (`_feat126-web`)
- `src/pages/reports/ServiceUsageReportPage.tsx` (new) — page (copy of `DoctorPerformancePage.tsx` pattern: `RequirePermission`, `DateRangeFilter`, chart, table, pagination, CSV + Excel export).
- `src/modules/reports/{api.ts,types.ts,helpers.ts}` (modified) — `getServiceUsage`, `ServiceUsageReport`/`ServiceUsageRow` types, `exportServiceUsageCsv`, `serviceUsageToChartData`.
- `src/pages/reports/ReportsHubPage.tsx` (modified) — new tab "Thống kê dịch vụ".
- `src/router/index.tsx` (modified) — lazy route `/reports/service-usage`.
- `src/locales/{vi,en}/reports.json` (modified) — `nav.serviceUsage` + `serviceUsage.*` keys.
- `src/tests/reports/ServiceUsageReportPage.test.tsx` (new) — 4 component tests.

### Docs
- `docs/tasks/TASK-126/deliveries/final-specs/service-usage-functional-design.md` (new)
- `docs/tasks/TASK-126/deliveries/api-specs/service-usage-api.md` (new)

## Aggregation SQL (core)

```sql
SELECT s.id AS service_id, s.name AS service_name,
       st.id AS service_type_id, st.name AS service_type_name,
       COUNT(*) AS usage_count,
       COALESCE(SUM(vs.quantity * vs.unit_price - COALESCE(vs.discount_amount, 0)), 0) AS revenue
FROM visit_service vs
JOIN service s ON s.id = vs.service_id
LEFT JOIN service_type st ON st.id = s.service_type_id
[JOIN visit v ON v.id = vs.visit_id]   -- only when doctor_id filter present
WHERE vs.clinic_id = :clinic_id
  AND vs.status != 'cancelled' AND vs.is_deleted = FALSE
  AND (vs.created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date BETWEEN :start_date AND :end_date
  [AND v.doctor_id = :doctor_id]
GROUP BY s.id, s.name, st.id, st.name
ORDER BY revenue DESC, usage_count DESC
```

## Key Decisions

1. **Revenue basis = list price** (`quantity * unit_price - discount_amount` on `visit_service`, same formula as `invoice_service.py::_pull_lines_from_visit`), NOT the invoice-collected amount. Matches the resolved "Open Decision" in the implementation plan (Key facts section of the task prompt already specified this SQL).
2. **`doctor_id` is a filter, not a grouping dimension** — response is always one row per service. A full per-doctor breakdown would require ORM name-resolution (like `doctor_performance_service.py`, since `full_name` is `EncryptedString`) and duplicates the existing `/reports/doctor-performance` report. FE v1 does not expose a doctor-picker UI for this filter (BE supports it; noted as a follow-up in the functional design, section 8.3).
3. **Timezone (M-10)**: date filter uses `(vs.created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date`, matching `visit_volume_service.py` — not naive UTC. Covered by a dedicated e2e test (`test_service_usage_timezone_boundary`).
4. **Unclassified services (`service_type_id IS NULL`) are included**, not filtered out — displayed as "Chưa phân loại" — so the report doesn't silently under-report revenue for pre-TASK-125 services.
5. **No migration** — `service_type_id` read live via `LEFT JOIN service_type` (column already on dev from TASK-125).

## Test Results

**Backend — NOT executed** (documented, same precedent as TASK-125's own e2e tests):
- No live Postgres/Redis available in this environment beyond the `w2e` stack, which the task explicitly forbids starting/touching.
- The local Python is 3.10; the project requires 3.11 (`datetime.UTC`, `enum.StrEnum` used in `app.main`'s import chain) — even the pure-schema unit tests can't be run through pytest (`tests/conftest.py` imports `app.main`, which fails at import on 3.10).
- Manually verified: `python -m py_compile` + `ast.parse` on all 3 changed/new BE files (no syntax errors); directly imported `report_schemas.py` (bypassing conftest) and constructed `ServiceUsageRow`/`ServiceUsageReport` instances successfully — schema logic is sound.
- 7 e2e tests written in `tests/integration/reports/test_service_usage_e2e.py` (empty period, count+revenue with discount, cancelled/deleted exclusion, timezone boundary, doctor filter, permission gate, tenant isolation) — ready to run once DB + Python 3.11 are available.
- 3 schema unit tests added to `tests/unit/reports/test_report_schemas.py`.

**Frontend — executed and passing** (Node 20, `npm install` run in the worktree):
- `npx vitest run src/tests/reports/` → **35/35 passed** (including the 4 new `ServiceUsageReportPage.test.tsx` tests).
- `npx vitest run` (full suite) → **1141/1144 passed**; the 3 failures are in `ForgotPasswordPage.test.tsx` / `QueuePage.test.tsx`, unrelated to this task and not touched by it (pre-existing on the branch).
- `npx tsc --noEmit` → clean, no errors.
- `npx eslint` on all new/modified files → clean, no errors/warnings.

## Areas for Review Focus

- Confirm the revenue-basis decision (list price vs. invoice-collected) matches what the manager/PO expects for this report — it's documented but was a plan-level "Open Decision" resolved by the task prompt's Key Facts, not re-confirmed with a human PO.
- BE integration tests are unverified (env constraints, not a code issue) — please run `tests/integration/reports/test_service_usage_e2e.py` against a real DB (Python 3.11 + migrated to head) before approving, per PROJECT.md's "Integration tests required: true (must be real-DB, not mocks)" gate.
- `doctor_id` filter has no FE UI — confirm this scoping is acceptable for this iteration.
