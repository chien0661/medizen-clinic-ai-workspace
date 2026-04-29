# TASK-015 Functional Design
Version: 1.0 | Date: 2026-04-27 | Status: DONE

## Modules

- reports: 5 report types (revenue, inventory, doctor_performance, visit_volume, prescription_breakdown)
- notifications: in-app notification table + CRUD API
- workers: 5 Arq cron jobs with 24h dedup

## API Routes

Reports (Permission: report.financial / report.view):
  GET /api/v1/reports/revenue?start=&end=&granularity=
  GET /api/v1/reports/inventory-status
  GET /api/v1/reports/doctor-performance?start=&end=
  GET /api/v1/reports/visit-volume?start=&end=&granularity=
  GET /api/v1/reports/prescription-breakdown?start=&end=
  GET /api/v1/reports/snapshots?type=&start=&end=

Notifications (any authenticated user):
  GET /api/v1/notifications?unread_only=&limit=&offset=
  GET /api/v1/notifications/unread-count
  POST /api/v1/notifications/{id}/read
  POST /api/v1/notifications/mark-all-read
  POST /api/v1/notifications/{id}/dismiss

## Data Models

notification: id, clinic_id (RLS), user_id (NULL=broadcast), type, severity, title, body, link, entity_type, entity_id, is_read, read_at, dismissed_at, created_at, expires_at

report_snapshot: id, clinic_id, report_type, period_start, period_end, data JSONB, generated_at, generated_by
  Unique: (clinic_id, report_type, period_start)

## Background Jobs

Job                          | Schedule     | Dedup
generate_daily_revenue_snapshot| 23:50 UTC   | N/A
check_low_stock              | Hourly       | 24h
check_near_expiry            | 08:00 UTC    | 24h
check_overdue_invoices       | 09:00 UTC    | 24h
appointment_reminder         | Every 30min  | 24h

## Permissions

report.view: admin, doctor, receptionist, pharmacist
report.financial: admin, doctor

## SQL Appendix

### Revenue Query
SELECT date_trunc(trunc_unit, issued_at) AS period,
       SUM(subtotal) AS gross_revenue,
       SUM(discount_total) AS discount_total,
       SUM(subtotal - discount_total + tax_total) AS net_revenue,
       SUM(paid_total) AS paid_total,
       SUM(balance_due) AS balance_due_total,
       COUNT(*) AS invoice_count
FROM invoice
WHERE clinic_id = :clinic_id AND is_deleted = FALSE
  AND status IN ('paid', 'partially_paid')
  AND issued_at >= :start_dt AND issued_at < :end_dt
GROUP BY date_trunc(trunc_unit, issued_at)
ORDER BY period ASC;

### Doctor Performance
SELECT v.doctor_id, u.full_name AS doctor_name,
       COUNT(v.id) AS visits_count,
       COUNT(v.id) FILTER (WHERE v.status = 'COMPLETED') AS completed_count,
       AVG(EXTRACT(EPOCH FROM (v.completed_at - v.started_at))/60)
           FILTER (WHERE v.completed_at IS NOT NULL) AS avg_minutes,
       COALESCE(SUM(i.grand_total) FILTER (WHERE i.status IN ('paid','partially_paid')),0) AS gross_revenue,
       COUNT(DISTINCT p.id) AS prescription_count
FROM visit v
LEFT JOIN user u ON u.id = v.doctor_id
LEFT JOIN invoice i ON i.visit_id = v.id AND i.is_deleted = FALSE
LEFT JOIN prescription p ON p.visit_id = v.id AND p.is_deleted = FALSE
WHERE v.clinic_id = :clinic_id AND v.is_deleted = FALSE
  AND v.visit_date BETWEEN :start AND :end
GROUP BY v.doctor_id, u.full_name
ORDER BY gross_revenue DESC;

## Test Results

Unit tests: 13 PASS
Integration notifications: 10 PASS
Integration reports: 12 PASS
Worker dedup: 6 PASS
Total: 41/41 PASS | Coverage: 85%

## Migrations

0020_create_notifications (down: 0019a): notification + report_snapshot + RLS
0020a_add_report_permissions (down: 0020): report.view, report.financial
0020b_create_visit_for_reports (down: 0020a): visit + appointment tables
