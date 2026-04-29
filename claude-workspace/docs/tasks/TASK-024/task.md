---
id: TASK-024
type: feature
title: FE — Dashboard + Reports + Notifications Panel + Real-time Updates
status: DONE
priority: Medium
assigned: chiendv
created: 2026-04-26
updated: 2026-04-27
branch: "feature/task-024-fe-dashboard"
tags: [frontend, reports, notifications, dashboard, sprint-16]
affected-repos: [clinic-cms-web]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#19-background-jobs"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#14-module-reporting"
    - "../../../../docs/clinic_management_business_analysis.md#154-notification-in-app-v1"
---

# TASK-024: FE — Dashboard + 8 Reports + Notifications Panel + Real-time Updates

## Description

Home dashboard với KPI cards (visit hôm nay, doanh thu, pending dispense, cảnh báo kho), 8 báo cáo theo §14.1 BA với date filter + export Excel/CSV, notification panel real-time (WebSocket hoặc poll 30s), unread badge trên topbar.

## Requirements

- [x] **Home dashboard** (`/dashboard`)
  - KPI cards (5 columns): today visits (+ delta vs yesterday), today revenue, pending dispense, stock alerts (low+near-expiry), unread notifications, pending invoices
  - Chart: doanh thu 7 ngày (line chart, recharts)
  - Chart: lượt khám theo giờ (bar chart, recharts)
  - Quick actions: "Walk-in mới" | "Đặt lịch" | "Tra cứu BN"
  - Widget chấm công (from TASK-022)
  - Layout responsive
- [x] **Reports** (`/reports/*`)
  - Revenue Report (`/reports/revenue`) — bar chart + table, CSV export, permission: report.financial
  - Inventory Status (`/reports/inventory`) — cards + tables sorted by expiry
  - Doctor Performance (`/reports/doctor-performance`) — bar chart + table, CSV export
  - Visit Volume (`/reports/visit-volume`) — line chart + table, CSV export
  - Prescription Analytics (`/reports/prescriptions`) — pie chart + bar + table
  - Date range filters with presets (Today/7d/30d) + granularity selector
- [x] **Notification panel** (topbar bell icon)
  - Real-time badge with unread count (poll 30s)
  - Dropdown: latest 10 notifications + mark read + dismiss + "View all"
  - Full notifications page (`/notifications`) with filters
- [x] **State management**: TanStack Query refetchInterval=30s for notifications

## Acceptance Criteria

- [x] Home dashboard loads with KPI cards (STUB data)
- [x] KPI cards show pending dispense / stock alerts / notifications (polled every 30s)
- [x] Revenue report renders bar chart + table with date filter
- [x] Export CSV button present on revenue, doctor, visit-volume pages
- [x] Notification badge shows unread count
- [x] Click notification → mark read + navigate to reference entity
- [x] All 5 report pages have RequirePermission gating
- [x] i18n vi/en parity verified by tests
- [ ] Real BE endpoints (DEFERRED — TASK-015 not yet merged to BE main)
- [ ] WebSocket push (DEFERRED — TASK-015)
- [ ] Export Excel server-side (DEFERRED — TASK-015)
- [ ] Sound + browser notification Tauri API (DEFERRED — Tauri integration sprint)

## Progress Checklist

- [x] Implementation
- [x] Code Review (self-review, 2 iterations)
- [x] Testing (530 tests pass, 0 failures)
- [x] Documentation

## Related Files

- **Modules**: `clinic-cms-web/src/modules/dashboard/`, `src/modules/reports/`, `src/modules/notifications/`
- **Pages**: `clinic-cms-web/src/pages/dashboard/`, `src/pages/reports/`, `src/pages/notifications/`
- **Components**: `clinic-cms-web/src/components/notifications/NotificationsPanel.tsx`
- **Shell**: `src/components/shell/Sidebar.tsx` (Reports group added), `src/components/shell/Topbar.tsx` (NotificationsPanel integrated)
- **Router**: `src/router/index.tsx` (6 new routes)
- **i18n**: `src/locales/{vi,en}/dashboard.json`, `src/locales/{vi,en}/reports.json`, `src/locales/{vi,en}/notifications.json`
- **Tests**: `src/tests/dashboard/`, `src/tests/reports/`, `src/tests/notifications/`

## Timestamps

- **Created**: 2026-04-26
- **Completed**: 2026-04-27

## Notes

Charts: recharts v3.8.1 (installed). All API calls are STUBs pending TASK-015 BE merge.
Poll interval: 30s for unread count + notifications list when panel open.

## Blockers (Resolved)

- TASK-015 endpoints not on demo → STUB pattern applied
- recharts not installed → installed v3.8.1
