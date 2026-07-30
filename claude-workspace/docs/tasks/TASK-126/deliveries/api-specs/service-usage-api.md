# API Specification: Service Usage Report

**Task:** TASK-126 — Thống kê sử dụng dịch vụ (service-usage report)
**Date:** 2026-07-30
**Version:** 1.0
**Status:** Complete (implementation) — pending Code Review / Test

---

## Overview

This specification documents the new `/reports/service-usage` and `/reports/service-usage/export` endpoints added to the Reports module. The report aggregates **usage count** and **revenue** per service, joined to the TASK-125 `service_type` classification (Khám / Thủ thuật / Xét nghiệm / admin-added), for a clinic-local date range, optionally restricted to a single performing doctor.

**Base URL:** `/api/v1`

**Authentication:** All endpoints require bearer token authentication:
```
Authorization: Bearer {jwt_token}
```

**Clinic Context:** Scoped to the token's active `clinic_id` (tenant-isolated, same as every other `/reports/*` endpoint).

**Permission:** `report.financial` — no new permission was introduced. Revenue is present in the response, so this report is gated the same as `revenue`, `doctor-performance`, `inventory-valuation`, etc.

---

## Endpoints Summary

| # | Method | Path | Permission | Purpose |
|---|--------|------|-----------|---------|
| 1 | GET | `/reports/service-usage` | `report.financial` | Usage count + revenue per service, for a date range |
| 2 | GET | `/reports/service-usage/export` | `report.financial` | Excel export of the same report (one row per service) |

---

## Endpoint Details

### 1. GET /reports/service-usage

**Description:**
Aggregates `visit_service` rows into one row per service (with its `service_type` attached), for the given clinic-local date range. Excludes cancelled (`vs.status = 'cancelled'`) and soft-deleted rows.

**Request:**
```
GET /api/v1/reports/service-usage?start=2026-07-01&end=2026-07-31
Authorization: Bearer <token>
```

**Query Parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `start` | date (YYYY-MM-DD) | Yes | Start of range (inclusive), clinic-local day |
| `end` | date (YYYY-MM-DD) | Yes | End of range (inclusive), clinic-local day |
| `doctor_id` | UUID | No | Restrict to services performed on visits belonging to this doctor |

**Response (200 OK):**
```json
{
  "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "start": "2026-07-01",
  "end": "2026-07-31",
  "doctor_id": null,
  "rows": [
    {
      "service_id": "550e8400-e29b-41d4-a716-446655440000",
      "service_name": "Khám tổng quát",
      "service_type_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "service_type_name": "Khám",
      "usage_count": 42,
      "revenue": "8400000.00"
    },
    {
      "service_id": "...",
      "service_name": "Dịch vụ cũ (chưa phân loại)",
      "service_type_id": null,
      "service_type_name": null,
      "usage_count": 3,
      "revenue": "450000.00"
    }
  ],
  "summary": {
    "total_usage_count": 45,
    "total_revenue": "8850000.00",
    "service_count": 2
  }
}
```

**Errors:**
- `401/403` — missing/invalid token or missing `report.financial` permission.
- `422` — missing/invalid `start`/`end`.

---

### 2. GET /reports/service-usage/export

**Description:** Same aggregation as endpoint #1, returned as a styled `.xlsx` download via the shared `build_xlsx_response` helper (title row + optional date-range line + STT column, matching every other report export).

**Request:**
```
GET /api/v1/reports/service-usage/export?start=2026-07-01&end=2026-07-31
Authorization: Bearer <token>
```

**Query Parameters:** same as endpoint #1 (`start`, `end`, `doctor_id`).

**Response (200 OK):** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` binary, filename `thong_ke_dich_vu_{start}_{end}.xlsx`.

**Columns:** Mã dịch vụ, Tên dịch vụ, Loại dịch vụ (`"Chưa phân loại"` when NULL), Số lượt, Doanh thu.

---

## Data Model Reference

### ServiceUsageRow

| Field | Type | Notes |
|-------|------|-------|
| `service_id` | UUID | |
| `service_name` | string | |
| `service_type_id` | UUID \| null | TASK-125 classification; `null` = chưa phân loại |
| `service_type_name` | string \| null | Denormalized (LEFT JOIN), `null` when unclassified |
| `usage_count` | integer | `COUNT(*)` of non-cancelled, non-deleted `visit_service` rows |
| `revenue` | Decimal | `SUM(quantity * unit_price - COALESCE(discount_amount, 0))` |

### ServiceUsageReport

| Field | Type | Notes |
|-------|------|-------|
| `clinic_id` | UUID | |
| `start` / `end` | date | Echo of the request range |
| `doctor_id` | UUID \| null | Echo of the `doctor_id` filter, `null` when not supplied |
| `rows` | ServiceUsageRow[] | One row per service, ordered by `revenue DESC, usage_count DESC` |
| `summary` | object | `total_usage_count`, `total_revenue`, `service_count` |

---

## Design Decisions

1. **Revenue basis = list price, not invoice-collected amount.** `revenue = SUM(vs.quantity * vs.unit_price - COALESCE(vs.discount_amount, 0))` — the value snapshotted on `visit_service` at time of service, same formula used by `invoice_service.py::_pull_lines_from_visit` when generating invoice lines. This is **not** the amount actually collected (which can differ from the list price due to void/refund/partial payment on the invoice) — consistent with how `doctor_performance_service.gross_revenue` is a distinct, invoice-derived figure. Chosen because it directly answers "which services were performed and what are they worth", independent of billing/collection status, and requires no additional joins to `invoice`/`payment`.
2. **Doctor is a filter, not a grouping dimension.** The report returns one row per service (optionally restricted to a doctor via `doctor_id`), rather than one row per (service × doctor) pair. A full per-doctor breakdown would require resolving `doctor_name` per row via the ORM (like `doctor_performance_service.py`, because `full_name` is `EncryptedString` and cannot be grouped in raw SQL) and duplicates functionality already covered by the existing `/reports/doctor-performance` endpoint. This keeps the query and response shape simple while still satisfying "theo bác sĩ" via the filter.
3. **Timezone (M-10).** The date-range filter uses `(vs.created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date`, matching `visit_volume_service.py` / `payment_method_service.py` — NOT naive UTC. A `visit_service` created late UTC evening that falls on the next clinic-local day is correctly attributed to that next day.
4. **Unclassified services included, not filtered out.** Unlike `GET /services?service_type_id=` (TASK-125, which excludes NULL rows from a type-scoped filter by design), this report has no `service_type_id` query filter — it always returns every service used in the range, with `service_type_id`/`service_type_name` as `null` for pre-TASK-125 (unclassified) services. This matches the AC "khớp dữ liệu thực" (must reconcile with actual visit_service/billing data) — hiding unclassified usage would silently under-report revenue.
5. **No new migration.** `service_type_id` is read live via `LEFT JOIN service_type st ON st.id = s.service_type_id` — TASK-125 already added the column and table on `dev`.

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-30 | Initial version — `/reports/service-usage` + export |
