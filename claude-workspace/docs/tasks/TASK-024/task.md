---
id: TASK-024
type: feature
title: FE — Dashboard + Reports + Notifications Panel + Real-time Updates
status: TODO
priority: Medium
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [frontend, reports, notifications, dashboard, sprint-16]
affected-repos: [clinic-cms]
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

- [ ] **Home dashboard** (`/`)
  - KPI cards (4 columns):
    - Lượt khám hôm nay (count, % vs hôm qua)
    - Doanh thu hôm nay (sum, target progress nếu có)
    - Pending dispense (count, link tới TASK-020)
    - Cảnh báo kho (low/expiry/recall counts, link)
  - Chart: doanh thu 7 ngày (line chart, recharts)
  - Chart: top 5 dịch vụ tuần này (bar chart)
  - Quick actions: "Walk-in mới" | "Đặt lịch" | "Tra cứu BN"
  - Widget chấm công (check-in/out, từ TASK-022)
  - Layout responsive, role-based (Doctor thấy queue widget; Pharmacist thấy pending dispense widget; ...)
- [ ] **Reports list** (`/reports`)
  - 8 báo cáo:
    1. Doanh thu theo ngày
    2. Doanh thu theo bác sĩ
    3. Lượt khám
    4. Top dịch vụ
    5. Top thuốc
    6. Tồn kho hiện tại
    7. Cảnh báo kho (low/near-expiry/expired/recalled)
    8. Công nợ (invoices unpaid)
  - Mỗi report: date filter (today/week/month/custom), filter phụ (theo BS, theo specialty), table + chart
  - Export Excel/CSV button (call API generate)
  - Print preview button
- [ ] **Notification panel** (slide-in từ topbar bell icon)
  - List: title + body + time ago + reference link
  - Group: Unread | Read
  - Click → mark read + navigate ref
  - "Mark all read" button
  - Filter by type (low_stock/near_expiry/appointment_reminder/invoice_unpaid)
  - Real-time: WebSocket subscribe `/ws/notifications`, fallback poll 30s
  - Unread badge trên bell icon (count)
- [ ] **Sound + browser notification** (Tauri notification API)
  - Optional toggle ở user settings
  - Trigger với type="appointment_reminder" hoặc "low_stock" critical

## Acceptance Criteria

- [ ] Home dashboard load < 1s với data 1000 visit/tháng
- [ ] KPI cards refresh sau khi tạo visit mới (WebSocket hoặc poll)
- [ ] Báo cáo doanh thu 1 tháng cho clinic 5000 visit < 2s render (chart + table)
- [ ] Export Excel doanh thu năm → file download ~ 50KB
- [ ] Tạo notification (vd cron near_expiry) → user online thấy ngay (≤ 30s)
- [ ] Click notification → mark read + navigate đúng entity
- [ ] Doctor login: dashboard hiện queue widget; Pharmacist: pending dispense widget
- [ ] Print report: layout đẹp A4, không cắt cột

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/desktop/src/modules/dashboard/`, `src/modules/reports/`, `src/modules/notifications/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Charts: recharts (đơn giản, performant) hoặc Apache ECharts (nhiều type hơn, nặng hơn). V1 chọn recharts. WebSocket nên dùng socket.io hoặc native WS với reconnect logic.

## Blockers

- TASK-017, TASK-015 (Reports + Notifications API + Background jobs)
