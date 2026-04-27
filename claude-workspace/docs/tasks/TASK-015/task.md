---
id: TASK-015
type: feature
title: Reporting + In-App Notifications + Background Jobs (Arq)
status: TODO
priority: Medium
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [reporting, notifications, jobs, sprint-14]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#19-background-jobs"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#14-module-reporting"
    - "../../../../docs/clinic_management_business_analysis.md#154-notification-in-app-v1"
---

# TASK-015: Reporting + In-App Notifications + Background Jobs (Arq)

## Description

8 báo cáo cơ bản (doanh thu/lượt khám/top dịch vụ/top thuốc/tồn kho/cảnh báo kho/công nợ/chấm công) + export Excel/CSV. In-app notification table + WebSocket push (optional). Arq workers cho cron jobs (low_stock, near_expiry, appointment_reminder, no_show, daily_revenue).

## Requirements

- [ ] Migration `0013_create_notifications.py`
- [ ] Module `reporting/` với 8 query endpoints theo §14.1 BA + export `format=xlsx|csv`
- [ ] Module `notifications/` với endpoints `GET /api/v1/notifications/me`, `POST /api/v1/notifications/{id}/read`, `POST /api/v1/notifications/mark-all-read`
- [ ] Notification trigger service (gọi từ business event): `notify(user_ids, type, title, body, ref)`
- [ ] Arq worker tasks (`app/workers/tasks/`):
  - `auto_no_show_appointments` mỗi 5 min
  - `appointment_reminders` mỗi giờ (T-24h, T-2h)
  - `low_stock_alerts` 6:00 AM hàng ngày
  - `near_expiry_alerts` 7:00 AM hàng ngày (window theo `inventory.near_expiry_days`)
  - `daily_revenue_report` 23:00 hàng ngày (cache để morning hôm sau load nhanh)
  - `generate_recurring_shifts` 1:00 AM hàng ngày (TASK-014 dependency)
- [ ] Worker iterate per clinic, respect clinic settings
- [ ] Views SQL: `v_active_queue`, `v_inventory_status`, `v_daily_revenue`, `v_doctor_performance`, `v_outstanding_invoices` (theo DB Design)

## Acceptance Criteria

- [ ] Báo cáo doanh thu 1 tháng cho clinic 5000 visit < 2s (verify EXPLAIN)
- [ ] Export Excel doanh thu 1 năm download được file đúng format
- [ ] Tạo batch sắp hết hạn → cron run → tạo notification cho Pharmacist + Admin
- [ ] WebSocket push notification mới đến user online (hoặc fallback poll mỗi 30s)
- [ ] Dashboard count unread notification real-time

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/reporting/`, `app/modules/notifications/`, `app/workers/`

## Timestamps

- **Created**: 2026-04-26

## Notes

WebSocket optional — fallback polling vẫn OK cho v1. Reporting cache Redis 5 min cho hot reports.

## Blockers

- TASK-013 (revenue), TASK-012 (inventory alerts), TASK-008 (no_show)
