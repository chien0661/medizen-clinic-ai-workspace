# TASK-015 SQL DDL — Reports & Notifications

**Date**: 2026-04-27
**Migrations**: `0020_create_notifications.py`, `0020a_add_report_permissions.py`, `0020b_create_visit_for_reports.py`

## Tables

### notification

```sql
CREATE TABLE notification (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
    user_id         UUID,                    -- NULL = broadcast
    type            TEXT NOT NULL CHECK (type IN (
                        'inventory.low_stock','inventory.near_expiry',
                        'appointment.reminder','appointment.no_show',
                        'visit.queue_alert','prescription.dispense_ready',
                        'invoice.overdue','system.alert')),
    severity        TEXT CHECK (severity IN ('info','warning','critical')),
    title           TEXT NOT NULL,
    body            TEXT,
    link            TEXT,
    entity_type     TEXT,
    entity_id       UUID,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    dismissed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ
);

CREATE INDEX ix_notification_clinic_user_read_created
    ON notification (clinic_id, user_id, is_read, created_at);
CREATE INDEX ix_notification_clinic_type_created
    ON notification (clinic_id, type, created_at);
CREATE INDEX ix_notification_dedup
    ON notification (clinic_id, type, entity_id);

ALTER TABLE notification ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification FORCE ROW LEVEL SECURITY;
CREATE POLICY notification_clinic_isolation ON notification
    USING (clinic_id = current_setting('app.current_clinic_id', true)::uuid);
```

### report_snapshot

```sql
CREATE TABLE report_snapshot (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id       UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
    report_type     TEXT NOT NULL CHECK (report_type IN (
                        'revenue_daily','inventory_status','doctor_performance',
                        'visit_volume','prescription_breakdown')),
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    data            JSONB NOT NULL DEFAULT '{}'::jsonb,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    generated_by    UUID
);

CREATE UNIQUE INDEX uq_report_snapshot_clinic_type_period
    ON report_snapshot (clinic_id, report_type, period_start);
CREATE INDEX ix_report_snapshot_clinic_type
    ON report_snapshot (clinic_id, report_type);

ALTER TABLE report_snapshot ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_snapshot FORCE ROW LEVEL SECURITY;
CREATE POLICY report_snapshot_clinic_isolation ON report_snapshot
    USING (clinic_id = current_setting('app.current_clinic_id', true)::uuid);
```

## Revenue Query (SQL Appendix)

```sql
SELECT
    date_trunc('day', issued_at)::date   AS period,
    SUM(subtotal)                         AS gross_revenue,
    SUM(discount_total)                   AS discount_total,
    SUM(subtotal - discount_total + tax_total) AS net_revenue,
    SUM(paid_total)                       AS paid_total,
    SUM(balance_due)                      AS balance_due_total,
    COUNT(*)                              AS invoice_count
FROM invoice
WHERE clinic_id = :clinic_id
  AND is_deleted = FALSE
  AND status IN ('paid', 'partially_paid')
  AND issued_at >= :start_dt
  AND issued_at < :end_dt
GROUP BY date_trunc('day', issued_at)
ORDER BY period ASC;
```

## Inventory Status Query

```sql
SELECT
    ii.id                               AS item_id,
    m.name                              AS medicine_name,
    COALESCE(
        SUM(b.actual_quantity - b.reserved_quantity)
            FILTER (WHERE b.is_recalled = FALSE AND b.expiry_date >= CURRENT_DATE),
        0
    )                                   AS available_qty,
    ii.reorder_min
FROM inventory_item ii
JOIN medicine m ON m.id = ii.medicine_id
LEFT JOIN batch b ON b.inventory_item_id = ii.id AND b.is_deleted = FALSE
WHERE ii.clinic_id = :clinic_id
  AND ii.is_deleted = FALSE
  AND m.is_deleted = FALSE
GROUP BY ii.id, m.name, ii.reorder_min;
```

## Doctor Performance Query

```sql
SELECT
    v.doctor_id,
    COALESCE(u.full_name, u.username, 'Unknown')    AS doctor_name,
    COUNT(v.id)                                       AS visits_count,
    COUNT(v.id) FILTER (WHERE v.status = 'COMPLETED') AS completed_count,
    AVG(EXTRACT(EPOCH FROM (v.completed_at - v.started_at)) / 60.0)
        FILTER (WHERE v.completed_at IS NOT NULL)     AS avg_consultation_minutes,
    COALESCE(SUM(i.grand_total) FILTER (
        WHERE i.status IN ('paid','partially_paid')
    ), 0)                                             AS gross_revenue,
    COUNT(DISTINCT p.id)                              AS prescription_count
FROM visit v
LEFT JOIN "user" u ON u.id = v.doctor_id
LEFT JOIN invoice i ON i.visit_id = v.id AND i.is_deleted = FALSE
LEFT JOIN prescription p ON p.visit_id = v.id AND p.is_deleted = FALSE
WHERE v.clinic_id = :clinic_id
  AND v.is_deleted = FALSE
  AND v.doctor_id IS NOT NULL
  AND v.visit_date >= :start_date
  AND v.visit_date <= :end_date
GROUP BY v.doctor_id, u.full_name, u.username
ORDER BY gross_revenue DESC;
```

## Permissions Seed

```sql
INSERT INTO permission (code, description, category) VALUES
    ('report.view',      'View general reports',    'reporting'),
    ('report.financial', 'View financial reports',  'reporting')
ON CONFLICT (code) DO NOTHING;
```
