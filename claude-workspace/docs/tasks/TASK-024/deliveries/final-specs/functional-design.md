# TASK-024 Functional Design — Dashboard + Reports + Notifications

**Status**: DONE  
**Date**: 2026-04-27  
**Branch**: `feature/task-024-fe-dashboard` (worktree: `clinic-cms-web-task024`)

---

## 1. Architecture Overview

### Module Structure

```
src/modules/dashboard/
  types.ts          — DashboardSnapshot, WeeklyRevenuePoint, HourlyQueuePoint
  api.ts            — dashboardApi (STUB)
  helpers.ts        — percentageDelta, formatDelta, transformWeeklyRevenue, transformHourlyQueue, date range helpers

src/modules/reports/
  types.ts          — RevenuePeriod, InventoryStatusReport, DoctorPerformance, VisitVolumePoint, PrescriptionBreakdown
  api.ts            — reportsApi (STUB)
  helpers.ts        — formatPeriodLabel, CSV exporters, chart data transformers
  DateRangeFilter.tsx — shared filter component (React Hook Form + Zod)

src/modules/notifications/
  types.ts          — Notification, NotificationType, NotificationSeverity
  api.ts            — notificationsApi (STUB, in-memory store for mark-read/dismiss)
  helpers.ts        — timeAgoRaw, resolveNotificationPath, severityClass/BgClass
```

---

## 2. Pages

| Route | Component | Permission | Description |
|---|---|---|---|
| `/dashboard` | `MainDashboardPage` | authenticated | KPI cards + charts + quick actions + attendance widget |
| `/reports/revenue` | `RevenueReportPage` | `report.financial` | Bar chart + table + CSV export |
| `/reports/inventory` | `InventoryReportPage` | `report.view` | Summary cards + low stock table + near-expiry table |
| `/reports/doctor-performance` | `DoctorPerformancePage` | `report.financial` | Bar chart + table + CSV export |
| `/reports/visit-volume` | `VisitVolumePage` | `report.view` | Multi-line chart + table + CSV export |
| `/reports/prescriptions` | `PrescriptionAnalyticsPage` | `report.view` | Pie + bar + table |
| `/notifications` | `NotificationsPage` | authenticated | Full list with type/severity/read filters |

---

## 3. Components

### NotificationsPanel (Topbar)

- Bell icon with live unread badge (TanStack Query, `refetchInterval: 30s`)
- Dropdown: 10 latest notifications, mark read on click, dismiss button
- "Mark all read" button in header
- "View all" link to `/notifications`
- Click notification → auto mark read + navigate to reference entity (visit/invoice/pharmacy/appointment)

### DateRangeFilter (Shared)

- Quick presets: Today / Last 7 days / Last 30 days
- Date inputs (from/to)
- Optional granularity selector (daily/weekly/monthly)
- React Hook Form + Zod validation (start ≤ end)

---

## 4. KPI Dashboard Cards

| Card | Value Source | Poll | Click Action |
|---|---|---|---|
| Today Visits | `snapshot.today_visits` (+ delta vs yesterday) | 30s | — |
| Today Revenue | `snapshot.today_revenue` | 30s | — |
| Pending Dispense | `snapshot.pending_dispense` | 30s | → `/pharmacy/pending` |
| Stock Alerts | `low_stock_count + near_expiry_count` | 30s | → `/reports/inventory` |
| Unread Notifications | `snapshot.unread_notifications` | 30s | → `/notifications` |
| Pending Invoices | `snapshot.pending_invoices` | 30s | → `/billing/invoices` |

---

## 5. Stub Map (TASK-015 BE Endpoints)

| Function | STUB | Real Endpoint |
|---|---|---|
| `dashboardApi.getSnapshot()` | Deterministic mock | `GET /api/v1/reports/snapshots` |
| `dashboardApi.getWeeklyRevenue()` | Deterministic mock | `GET /api/v1/reports/revenue?granularity=daily&start=&end=` |
| `dashboardApi.getHourlyQueue()` | Deterministic mock | `GET /api/v1/reports/visit-volume?start=today&granularity=hourly` |
| `reportsApi.getRevenue(filter)` | Deterministic mock | `GET /api/v1/reports/revenue?start=&end=&granularity=` |
| `reportsApi.getInventoryStatus()` | Deterministic mock | `GET /api/v1/reports/inventory-status` |
| `reportsApi.getDoctorPerformance(filter)` | Deterministic mock | `GET /api/v1/reports/doctor-performance?start=&end=` |
| `reportsApi.getVisitVolume(filter)` | Deterministic mock | `GET /api/v1/reports/visit-volume?start=&end=&granularity=` |
| `reportsApi.getPrescriptionBreakdown(filter)` | Deterministic mock | `GET /api/v1/reports/prescription-breakdown?start=&end=` |
| `notificationsApi.getUnreadCount()` | In-memory store | `GET /api/v1/notifications/unread-count` |
| `notificationsApi.list(filters)` | In-memory store | `GET /api/v1/notifications?unread_only=&limit=&type=` |
| `notificationsApi.markRead(id)` | In-memory mutate | `POST /api/v1/notifications/{id}/read` |
| `notificationsApi.markDismissed(id)` | In-memory mutate | `POST /api/v1/notifications/{id}/dismiss` |
| `notificationsApi.markAllRead()` | In-memory mutate | `POST /api/v1/notifications/read-all` |

---

## 6. i18n

New namespaces added to `src/lib/i18n.ts`:
- `dashboard` (vi + en)
- `reports` (vi + en)
- `notifications` (vi + en)

Vietnamese diacritics verified: "Tổng quan", "Báo cáo", "Thông báo", "Lượt khám hôm nay", etc.

---

## 7. Routing Changes

- `/reports` → redirect to `/reports/revenue`
- 6 new lazy-loaded routes added to `AppRouter`
- Sidebar: "Báo cáo" group with 5 sub-items + "Thông báo" item
- Topbar: `NotificationsPanel` replaces static bell placeholder

---

## 8. Testing

| Suite | Tests | Notes |
|---|---|---|
| `tests/dashboard/helpers.test.ts` | 12 | percentageDelta, formatDelta, transformers, date ranges |
| `tests/dashboard/MainDashboardPage.test.tsx` | 5 | KPI renders, loading, error, quick actions, attendance widget |
| `tests/dashboard/i18n-parity.test.ts` | 6 | vi/en key parity + diacritics |
| `tests/reports/helpers.test.ts` | 7 | formatPeriodLabel, chart transformers |
| `tests/reports/RevenueReportPage.test.tsx` | 3 | render, CSV btn, error |
| `tests/reports/InventoryReportPage.test.tsx` | 2 | cards, permission |
| `tests/notifications/helpers.test.ts` | 14 | timeAgoRaw, resolveNotificationPath, severity classes |
| `tests/notifications/NotificationsPanel.test.tsx` | 5 | badge, open panel, empty, items, view all |

All 530 tests pass (including 482 pre-existing tests from TASK-017..023).

---

## 9. Deferred Items

| Item | Reason | Ticket |
|---|---|---|
| Real BE API calls | TASK-015 not merged to BE main (migration conflict) | TASK-015 |
| WebSocket push notifications | Requires TASK-015 BE + WS infrastructure | TASK-015 |
| Server-side Excel export | Requires TASK-015 BE endpoint | TASK-015 |
| Sound + Tauri notification API | Requires Tauri integration sprint | Future |
| Print report layout | Low priority, deferred | Future |
