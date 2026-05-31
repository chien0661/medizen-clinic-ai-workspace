# TASK-044 — Handoff: Implementation → Review

**Date**: 2026-05-01
**Agent**: Code Implementation
**Target**: Code Review

---

## Files Added (12 new files)

### Dashboard Pages (4)
- `src/pages/dashboards/ReceptionDashboardPage.tsx`
- `src/pages/dashboards/NurseDashboardPage.tsx`
- `src/pages/dashboards/PharmacyDashboardPage.tsx`
- `src/pages/dashboards/AdminDashboardPage.tsx`

### i18n (2)
- `src/locales/vi/dashboards.json` — 80+ keys across 4 roles
- `src/locales/en/dashboards.json` — 80+ keys across 4 roles

### Tests (5)
- `src/tests/dashboards/ReceptionDashboardPage.test.tsx` — 5 tests
- `src/tests/dashboards/NurseDashboardPage.test.tsx` — 5 tests
- `src/tests/dashboards/PharmacyDashboardPage.test.tsx` — 5 tests
- `src/tests/dashboards/AdminDashboardPage.test.tsx` — 6 tests
- `src/tests/dashboards/route-guard.test.tsx` — 4 tests

### Modified Files (2)
- `src/lib/i18n.ts` — registered `dashboards` namespace (vi + en)
- `src/router/index.tsx` — added 4 lazy routes under `/dashboards/*`

---

## Routes Added (4)

| Route | Component | Permission |
|-------|-----------|------------|
| `/dashboards/reception` | `ReceptionDashboardPage` | `reception.dashboard.view` |
| `/dashboards/nurse` | `NurseDashboardPage` | `nurse.dashboard.view` |
| `/dashboards/pharmacy` | `PharmacyDashboardPage` | `pharmacy.dashboard.view` |
| `/dashboards/admin` | `AdminDashboardPage` | `admin.dashboard.view` |

---

## i18n Keys Added

Namespace `dashboards.*` with 4 sub-namespaces:
- `dashboards.reception.*` — 20 keys (title, 4 KPIs, queue table, appointments table, actions, statuses)
- `dashboards.nurse.*` — 18 keys (title, 3 KPIs, alerts, chart, vitals history)
- `dashboards.pharmacy.*` — 20 keys (title, 4 KPIs, chart, pending table, priorities, actions)
- `dashboards.admin.*` — 22 keys (title, 6 KPIs, charts, activity, feature flags)

---

## Test Counts

| File | Tests |
|------|-------|
| ReceptionDashboardPage.test.tsx | 5 |
| NurseDashboardPage.test.tsx | 5 |
| PharmacyDashboardPage.test.tsx | 5 |
| AdminDashboardPage.test.tsx | 6 |
| route-guard.test.tsx | 4 |
| **Total new** | **25** |
| Pre-existing | 547 |
| **Grand total** | **572** |

---

## Build & Quality Status

| Check | Status |
|-------|--------|
| `npm run type-check` | PASS (0 errors) |
| `npm run lint` | PASS (0 warnings) |
| `npm test -- --run` | PASS (572/572) |
| `npm run build` | PASS (chunk size warning pre-existing) |

---

## Decisions Deferred

1. **Real BE hooks not wired for ReceptionDashboard**: `visitApi.queue()` and `appointmentApi.list()` return real `Visit`/`Appointment` types which don't have display fields like `patient_name`, `wait_minutes`, `time`. Dashboard uses internal `QueueItem`/`AppointmentItem` types with `queryFn: async () => MOCK_DATA`. Switching to live BE requires a view-model adapter layer (deferred to BE integration task).

2. **NurseDashboard**: All 3 queries use `async () => MOCK_*` (no real nurse vitals endpoint exists yet in FE modules). Deferred until TASK-nurse-vitals BE endpoint lands.

3. **PharmacyDashboard**: KPI "Dispensed today" and "Near-expiry 30/60/90" use hardcoded placeholders (24 and "3/8/15") — real data needs `/pharmacy/dispense-history?date=today` endpoint not yet in spec.

4. **AdminDashboard**: Revenue 30d uses generated random mock; `pendingInvoices` / `newPatients` derived from snapshot (real). Feature flags use hardcoded `MOCK_FEATURE_FLAGS` — actual flag endpoint not available in FE modules.

5. **`/dashboards/multi-role`** route not added — per task scope, Wave 3-B stub handles that route separately.

6. **Walk-in redirect** `/reception/walk-in` — route doesn't exist yet (placeholder for future Reception module screen). The "Tiếp nhận BN mới" button navigates there per spec.

---

## Architecture Notes

- KpiCard components are defined locally per page (not extracted to shared component) — consistent with MainDashboardPage pattern
- All pages use `RequirePermission` with `fallback` showing `common:forbidden`
- Mock data uses realistic Vietnamese names (Nguyễn Thị Hương, Trần Văn Minh, etc.) and realistic medication names
- Indigo/Emerald/Amber/Red palette only — no `brand-*` legacy colors used
- All charts use `#6366f1` (indigo-500) or `#f59e0b` (amber-500) per spec
