# TASK-015 API Specification — Reports & Notifications

**Version**: 1.0
**Base URL**: `/api/v1`
**Auth**: Bearer JWT (all endpoints require authentication)
**Date**: 2026-04-27

---

## Reports Endpoints

### 1. Revenue Report

```
GET /api/v1/reports/revenue
```

**Permission**: `report.financial`

**Query Parameters**:
| Parameter | Type | Required | Description |
|---|---|---|---|
| `start` | date | Yes | Start date inclusive (YYYY-MM-DD) |
| `end` | date | Yes | End date inclusive (YYYY-MM-DD) |
| `granularity` | string | No | `daily` | `weekly` | `monthly` (default: `daily`) |

**Response** `200 OK`:
```json
{
  "clinic_id": "uuid",
  "start": "2026-01-01",
  "end": "2026-01-31",
  "granularity": "monthly",
  "rows": [
    {
      "period": "2026-01-01",
      "gross_revenue": "5000000.00",
      "discount_total": "250000.00",
      "net_revenue": "4750000.00",
      "paid_total": "4500000.00",
      "balance_due_total": "250000.00",
      "invoice_count": 42
    }
  ],
  "summary": {
    "total_gross_revenue": "5000000.00",
    "total_net_revenue": "4750000.00",
    "total_paid": "4500000.00",
    "total_balance_due": "250000.00",
    "total_invoice_count": 42,
    "period_count": 1
  }
}
```

---

### 2. Inventory Status Report

```
GET /api/v1/reports/inventory-status
```

**Permission**: `report.view`

**Response** `200 OK`:
```json
{
  "clinic_id": "uuid",
  "low_stock_count": 3,
  "near_expiry_count": 5,
  "expired_count": 1,
  "items": [
    {
      "item_id": "uuid",
      "medicine_name": "Paracetamol 500mg",
      "available_qty": "150.00",
      "reorder_min": "200.00",
      "is_low_stock": true
    }
  ]
}
```

---

### 3. Doctor Performance Report

```
GET /api/v1/reports/doctor-performance
```

**Permission**: `report.financial`

**Query**: `start` (date, required), `end` (date, required)

**Response** `200 OK`:
```json
{
  "clinic_id": "uuid",
  "start": "2026-01-01",
  "end": "2026-01-31",
  "rows": [
    {
      "doctor_id": "uuid",
      "doctor_name": "BS. Nguyen Van A",
      "visits_count": 120,
      "completed_count": 115,
      "avg_consultation_minutes": 12.5,
      "gross_revenue": "6000000.00",
      "prescription_count": 98
    }
  ]
}
```

---

### 4. Visit Volume Report

```
GET /api/v1/reports/visit-volume
```

**Permission**: `report.view`

**Query**: `start`, `end`, `granularity` (daily/weekly/monthly)

**Response** `200 OK`:
```json
{
  "clinic_id": "uuid",
  "start": "2026-01-01",
  "end": "2026-01-07",
  "granularity": "daily",
  "rows": [
    {"period": "2026-01-01", "status": "COMPLETED", "count": 25},
    {"period": "2026-01-01", "status": "CANCELLED", "count": 2}
  ]
}
```

---

### 5. Prescription Breakdown

```
GET /api/v1/reports/prescription-breakdown
```

**Permission**: `report.view`

**Query**: `start`, `end`

**Response** `200 OK`:
```json
{
  "clinic_id": "uuid",
  "start": "2026-01-01",
  "end": "2026-01-31",
  "total_prescriptions": 250,
  "in_house_count": 200,
  "external_count": 50,
  "cancelled_count": 15,
  "cancel_rate": 0.06,
  "top_medicines": [
    {"medicine_id": "uuid", "medicine_name": "Amoxicillin 500mg", "prescribed_count": 45}
  ]
}
```

---

### 6. Report Snapshots

```
GET /api/v1/reports/snapshots
```

**Permission**: `report.view`

**Query**: `type` (optional), `start` (date, optional), `end` (date, optional)

**Response** `200 OK`: Array of snapshot objects:
```json
[
  {
    "id": "uuid",
    "clinic_id": "uuid",
    "report_type": "revenue_daily",
    "period_start": "2026-01-27",
    "period_end": "2026-01-27",
    "data": {"summary": {}, "rows": []},
    "generated_at": "2026-01-27T23:50:00Z",
    "generated_by": null
  }
]
```

---

## Notifications Endpoints

### 7. List Notifications

```
GET /api/v1/notifications
```

**Permission**: Any authenticated user

**Query**: `unread_only` (bool, default false), `limit` (1-200, default 50), `offset` (int, default 0)

**Response** `200 OK`:
```json
{
  "data": [
    {
      "id": "uuid",
      "clinic_id": "uuid",
      "user_id": null,
      "type": "inventory.low_stock",
      "severity": "warning",
      "title": "Low Stock: Paracetamol 500mg",
      "body": "Available: 15, Reorder min: 200",
      "link": "/inventory/item-uuid",
      "entity_type": "inventory_item",
      "entity_id": "uuid",
      "is_read": false,
      "read_at": null,
      "dismissed_at": null,
      "created_at": "2026-01-27T08:00:00Z",
      "expires_at": null
    }
  ],
  "total": 5,
  "unread_count": 3
}
```

---

### 8. Unread Count (Dashboard Badge)

```
GET /api/v1/notifications/unread-count
```

**Permission**: Any authenticated user

**Response** `200 OK`:
```json
{"unread_count": 3}
```

---

### 9. Mark Read

```
POST /api/v1/notifications/{notification_id}/read
```

**Response** `200 OK`: Full `NotificationOut` with `is_read: true`

---

### 10. Mark All Read

```
POST /api/v1/notifications/mark-all-read
```

**Response** `200 OK`:
```json
{"marked_read": 5}
```

---

### 11. Dismiss Notification

```
POST /api/v1/notifications/{notification_id}/dismiss
```

**Response** `200 OK`: Full `NotificationOut` with `dismissed_at` set

---

## Background Jobs (Cron Schedule)

| Job | Schedule | Description |
|---|---|---|
| `generate_daily_revenue_snapshot` | 23:50 UTC daily | Cache revenue per clinic |
| `check_low_stock` | Every hour | Low stock notifications (24h dedup) |
| `check_near_expiry` | 08:00 UTC daily | Near expiry notifications (24h dedup) |
| `check_overdue_invoices` | 09:00 UTC daily | Overdue invoice notifications (24h dedup) |
| `appointment_reminder` | Every 30min | Upcoming appointment reminders (24h dedup) |

---

## Permissions Reference

| Permission Code | Category | Default Roles |
|---|---|---|
| `report.view` | reporting | admin, doctor, receptionist, pharmacist |
| `report.financial` | reporting | admin, doctor |
