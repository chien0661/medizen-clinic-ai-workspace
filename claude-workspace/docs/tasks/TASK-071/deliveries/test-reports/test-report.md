# Test Report — TASK-071: Super Admin Analytics

**Date**: 2026-06-01
**Branch BE**: feature/TASK-071-superadmin-analytics (clinic-cms-merge)
**Branch FE**: feature/TASK-071-superadmin-analytics (clinic-cms-web)
**Overall verdict**: PASS

---

## Unit Tests

### BE (pytest)
- **23 unit tests** — `tests/unit/test_superadmin_analytics.py` — ALL PASS
- **15 integration tests** — `tests/integration/test_superadmin_analytics_e2e.py` — ALL PASS
- **Total**: 38/38 PASS

### FE (vitest)
- **TASK-071 superadmin tests**: 39/39 PASS
  - `src/tests/superadmin/SuperAdminAnalyticsPage.test.tsx` — 17 tests PASS
  - `src/tests/superadmin/RequireSuperuser.test.tsx` — 4 tests PASS
  - `src/tests/superadmin/SuperAdminDashboardPage.test.tsx` — 6 tests PASS
  - Additional superadmin suite — 12 tests PASS
- **Full suite**: 967/974 tests PASS (7 failures are pre-existing, unrelated to TASK-071)
  - `src/tests/hooks/useSync.test.ts` — 2 pre-existing failures (TASK-067 browser guard)
  - `src/tests/shell/secureStore.test.ts` — 5 pre-existing failures (browser fallback)
  - `src/tests/reports/ReportsHubPage.test.tsx` — 1 file-level error (missing page import — pre-existing)
- **Note**: RequireSuperuser test fixtures updated (`isHydrated:true`) in commit f1fe7d4

---

## E2E Tests

| TC | Description | Result | Notes |
|----|-------------|--------|-------|
| TC-001 | Analytics sidebar link visible (Super Admin section) | PASS | "Thống kê" between Tổng quan and Phòng khám |
| TC-002 | Default state (30d) — stats cards loaded | PASS | 4 stats cards + 3 secondary cards visible |
| TC-003 | Year filter + line chart renders | PASS | Chart switches to monthly granularity |
| TC-004 | Clinic filter — filters by selected clinic | PASS | Dropdown filters table and chart |
| TC-005 | Clinic comparison table sortable | PASS | Click "Lượt khám" header moves sort arrow from Doanh thu → Lượt khám |
| TC-006 | Route guard blocks non-superuser | PASS | admin/Demo@1234 redirected to /dashboard immediately |

**All 6 E2E test cases PASS.**

---

## Screenshots

| File | TC |
|------|----|
| `screenshots/TC-001-analytics-sidebar.png` | TC-001 |
| `screenshots/TC-002-analytics-default.png` | TC-002 |
| `screenshots/TC-003-analytics-year.png` | TC-003 |
| `screenshots/TC-004-analytics-clinic-filter.png` | TC-004 |
| `screenshots/TC-005-analytics-clinics-table.png` | TC-005 |
| `screenshots/TC-006-analytics-guard.png` | TC-006 |

---

## Known Limitations

- Revenue bucketed by `invoice.updated_at` (paid proxy) — can misbucket refunded invoices
- Date range max 365 days enforced (422 on violation)
- Clinic comparison table shows clinics named "Other Clinic" for tenant-isolated data not visible in cross-tenant context (expected behavior)
- Pre-existing FE test failures (7 tests in 3 files) are unrelated to TASK-071 and existed before this branch
