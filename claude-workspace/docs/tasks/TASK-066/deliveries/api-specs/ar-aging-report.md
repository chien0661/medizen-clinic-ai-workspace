# API Specification — AR Aging Report

**Task:** TASK-066  
**Module:** Reports (Công nợ phải thu)  
**Date:** 2026-05-31  
**Status:** DONE  

---

## Overview

The AR Aging report provides accounts-receivable aging analysis: outstanding invoices bucketed by days overdue (0-30 / 31-60 / 61-90 / >90 days) from the invoice issue date. This enables clinic managers to track and follow up on unpaid and partially paid invoices, assess cash flow risk, and prioritize collection efforts.

---

## API Endpoints

### 1. GET /api/v1/reports/ar-aging

**Purpose:**  
Retrieve AR aging report data aggregated by age bucket and patient. Only unpaid (`issued`) and partially paid (`partially_paid`) invoices are included. Age is calculated from `issued_at` relative to the as-of reference date.

#### Request

**URL & Method:**
```
GET /api/v1/reports/ar-aging
```

**Authentication:**
```
Authorization: Bearer {token}
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `as_of` | string (ISO 8601) | No | Today (UTC) | Reference date for age calculation. Format: `YYYY-MM-DD`. Example: `2026-05-31`. If not provided, uses current date (today). |

**Example Request:**
```
GET /api/v1/reports/ar-aging?as_of=2026-05-31
Authorization: Bearer eyJhbGc...
```

#### Permission

**Required Permission:** `report.financial`

Users without `report.financial` permission will receive **401 Unauthorized**.

#### Response

**Status:** 200 OK

**Content-Type:** application/json

**Response Schema:**

```json
{
  "as_of_date": "2026-05-31",
  "total_0_30": 5000000,
  "total_31_60": 3500000,
  "total_61_90": 2100000,
  "total_over_90": 800000,
  "grand_total": 11400000,
  "patients": [
    {
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "patient_code": "BN001",
      "patient_name": "Nguyễn Văn A",
      "bucket_0_30": 2000000,
      "bucket_31_60": 1500000,
      "bucket_61_90": 500000,
      "bucket_over_90": 0,
      "total_outstanding": 4000000
    },
    {
      "patient_id": "660e8400-e29b-41d4-a716-446655440001",
      "patient_code": "BN002",
      "patient_name": "Trần Thị B",
      "bucket_0_30": 3000000,
      "bucket_31_60": 2000000,
      "bucket_61_90": 1600000,
      "bucket_over_90": 800000,
      "total_outstanding": 7400000
    }
  ]
}
```

**Response Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `as_of_date` | string | ISO date string (YYYY-MM-DD) — the reference date used for age calculation |
| `total_0_30` | decimal | Sum of all outstanding amounts aged 0–30 days (in currency units, e.g., VND) |
| `total_31_60` | decimal | Sum of all outstanding amounts aged 31–60 days |
| `total_61_90` | decimal | Sum of all outstanding amounts aged 61–90 days |
| `total_over_90` | decimal | Sum of all outstanding amounts aged >90 days (most critical) |
| `grand_total` | decimal | Sum of all outstanding amounts (`total_0_30 + total_31_60 + total_61_90 + total_over_90`) |
| `patients` | array | List of per-patient AR aging rows (see below) |

**Patient Row Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `patient_id` | string (UUID) | Unique patient identifier |
| `patient_code` | string | Clinic-specific patient code (e.g., "BN001") |
| `patient_name` | string | Patient full name (decrypted from BYTEA cipher, per TASK-037 P2) |
| `bucket_0_30` | decimal | Patient's outstanding amount aged 0–30 days |
| `bucket_31_60` | decimal | Patient's outstanding amount aged 31–60 days |
| `bucket_61_90` | decimal | Patient's outstanding amount aged 61–90 days |
| `bucket_over_90` | decimal | Patient's outstanding amount aged >90 days |
| `total_outstanding` | decimal | Patient's total outstanding amount |

#### Error Responses

**400 Bad Request** — Invalid date format:
```json
{
  "code": "INVALID_REQUEST",
  "message": "Invalid date format. Expected YYYY-MM-DD, got: 31-05-2026"
}
```

**401 Unauthorized** — Missing or invalid token:
```json
{
  "code": "UNAUTHORIZED",
  "message": "Authentication required. Invalid or expired token."
}
```

**403 Forbidden** — Insufficient permission:
```json
{
  "code": "FORBIDDEN",
  "message": "User does not have permission: report.financial"
}
```

**500 Internal Server Error** — Database or processing error:
```json
{
  "code": "INTERNAL_ERROR",
  "message": "Error computing AR aging report. Please try again later."
}
```

---

### 2. GET /api/v1/reports/ar-aging/export

**Purpose:**  
Export AR aging report as CSV file (UTF-8 with BOM for Excel compatibility). The CSV includes per-patient rows and a summary totals row at the end.

#### Request

**URL & Method:**
```
GET /api/v1/reports/ar-aging/export
```

**Authentication:**
```
Authorization: Bearer {token}
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `as_of` | string (ISO 8601) | No | Today (UTC) | Reference date for age calculation. Format: `YYYY-MM-DD`. |

**Example Request:**
```
GET /api/v1/reports/ar-aging/export?as_of=2026-05-31
Authorization: Bearer eyJhbGc...
```

#### Permission

**Required Permission:** `report.financial`

#### Response

**Status:** 200 OK

**Content-Type:** text/csv; charset=utf-8

**Headers:**
```
Content-Disposition: attachment; filename="ar-aging-2026-05-31.csv"
```

**CSV Format:**

```
Mã BN,Tên bệnh nhân,0-30 ngày,31-60 ngày,61-90 ngày,>90 ngày,Tổng công nợ
BN001,Nguyễn Văn A,2000000,1500000,500000,0,4000000
BN002,Trần Thị B,3000000,2000000,1600000,800000,7400000
TỔNG CỘNG,,5000000,3500000,2100000,800000,11400000
```

**CSV Columns:**

| Column | Description |
|--------|-------------|
| Mã BN | Patient code (formula injection guarded with leading apostrophe if needed) |
| Tên bệnh nhân | Patient full name (formula injection guarded) |
| 0-30 ngày | Outstanding amount aged 0–30 days |
| 31-60 ngày | Outstanding amount aged 31–60 days |
| 61-90 ngày | Outstanding amount aged 61–90 days |
| >90 ngày | Outstanding amount aged >90 days |
| Tổng công nợ | Total outstanding amount |

**Security Note — Formula Injection Prevention:**  
Any cell starting with `=`, `+`, `-`, `@`, TAB, or CR is prefixed with a single quote (`'`) to prevent formula injection attacks when the CSV is opened in Excel/Google Sheets. Example: if patient code is `=IMPORTXML(...)`, the CSV will contain `'=IMPORTXML(...)`.

#### Error Responses

**401 Unauthorized, 403 Forbidden, 500 Internal Error** — Same as `/ar-aging` endpoint above.

---

### 3. GET /api/v1/reports/doctor-weekly

**Purpose:**  
Retrieve weekly visit volume per day-of-week for the specified doctor (or all doctors). Returns 7 rows representing Monday–Sunday of the ISO week containing the reference date. Used for the DoctorDashboard weekly trend chart.

#### Request

**URL & Method:**
```
GET /api/v1/reports/doctor-weekly
```

**Authentication:**
```
Authorization: Bearer {token}
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `doctor_id` | string (UUID) | No | All doctors | Filter to a specific doctor. If omitted, aggregates visits from all doctors. |
| `ref_date` | string (ISO 8601) | No | Today (UTC) | Any date in the desired ISO week. Format: `YYYY-MM-DD`. The API returns data for the full week (Mon–Sun) containing this date. |

**Example Requests:**
```
# All doctors, current week
GET /api/v1/reports/doctor-weekly
Authorization: Bearer eyJhbGc...

# Specific doctor, specific week
GET /api/v1/reports/doctor-weekly?doctor_id=550e8400-e29b-41d4-a716-446655440000&ref_date=2026-05-29
Authorization: Bearer eyJhbGc...
```

#### Permission

**Required Permission:** `report.view`

Users without `report.view` permission will receive **403 Forbidden**.

#### Response

**Status:** 200 OK

**Content-Type:** application/json

**Response Schema:**

```json
{
  "clinic_id": "770e8400-e29b-41d4-a716-446655440002",
  "doctor_id": "550e8400-e29b-41d4-a716-446655440000",
  "week_start": "2026-05-25",
  "week_end": "2026-05-31",
  "rows": [
    {
      "day_of_week": 0,
      "day_label": "T2",
      "count": 5
    },
    {
      "day_of_week": 1,
      "day_label": "T3",
      "count": 7
    },
    {
      "day_of_week": 2,
      "day_label": "T4",
      "count": 6
    },
    {
      "day_of_week": 3,
      "day_label": "T5",
      "count": 4
    },
    {
      "day_of_week": 4,
      "day_label": "T6",
      "count": 8
    },
    {
      "day_of_week": 5,
      "day_label": "T7",
      "count": 3
    },
    {
      "day_of_week": 6,
      "day_label": "CN",
      "count": 1
    }
  ]
}
```

**Response Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `clinic_id` | string (UUID) | Clinic identifier (tenant scope) |
| `doctor_id` | string (UUID) \| null | Doctor filter used (null = all doctors) |
| `week_start` | string (ISO 8601) | Monday of the queried ISO week (YYYY-MM-DD) |
| `week_end` | string (ISO 8601) | Sunday of the queried ISO week (YYYY-MM-DD) |
| `rows` | array | 7 rows, one for each day of the week (Mon–Sun) |

**Day Row Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `day_of_week` | integer | Day index: 0 = Monday, 1 = Tuesday, ..., 6 = Sunday |
| `day_label` | string | Vietnamese day label: "T2", "T3", ..., "CN" (Chủ nhật) |
| `count` | integer | Number of completed visits on that day (includes `COMPLETED` and `AWAITING_PAYMENT` statuses) |

#### Empty Week Example

If there are no visits during the queried week:
```json
{
  "clinic_id": "770e8400-e29b-41d4-a716-446655440002",
  "doctor_id": "550e8400-e29b-41d4-a716-446655440000",
  "week_start": "2026-05-25",
  "week_end": "2026-05-31",
  "rows": [
    { "day_of_week": 0, "day_label": "T2", "count": 0 },
    { "day_of_week": 1, "day_label": "T3", "count": 0 },
    { "day_of_week": 2, "day_label": "T4", "count": 0 },
    { "day_of_week": 3, "day_label": "T5", "count": 0 },
    { "day_of_week": 4, "day_label": "T6", "count": 0 },
    { "day_of_week": 5, "day_label": "T7", "count": 0 },
    { "day_of_week": 6, "day_label": "CN", "count": 0 }
  ]
}
```

#### Error Responses

**400 Bad Request** — Invalid date format or doctor_id:
```json
{
  "code": "INVALID_REQUEST",
  "message": "Invalid doctor_id format or date format. Expected UUID and YYYY-MM-DD."
}
```

**401 Unauthorized, 403 Forbidden, 500 Internal Error** — Same as AR aging endpoints above.

---

## Data Processing Logic

### Age Bucket Classification

For each invoice with `status` = `issued` or `partially_paid`:

- **Age (days) = as_of_date − DATE(issued_at)**
- **Bucket 0–30:** Age BETWEEN 0 AND 30
- **Bucket 31–60:** Age BETWEEN 31 AND 60
- **Bucket 61–90:** Age BETWEEN 61 AND 90
- **Bucket >90:** Age > 90

**Outstanding Amount:**
- For `issued` invoices: `total_amount` (fully unpaid)
- For `partially_paid` invoices: `balance_due` (remaining balance after partial payment)

### Doctor Weekly Data

Visits are included if:
- `status` IN (`COMPLETED`, `AWAITING_PAYMENT`)
  - `COMPLETED`: consultation finished, payment complete
  - `AWAITING_PAYMENT`: consultation finished, billing/payment pending
- `visit_date` is within the specified ISO week (Monday–Sunday)
- `doctor_id` matches (if specified)
- `is_deleted` = FALSE
- `clinic_id` matches (tenant isolation via RLS)

Week calculation:
- Input: `ref_date` (any date in the desired week)
- Output: ISO week Monday and Sunday
- Example: If `ref_date = 2026-05-29` (Wednesday), returns week 2026-05-25 to 2026-05-31

---

## Business Rules & Validation

| Rule ID | Description | Enforcement |
|---------|-------------|-------------|
| BR-001 | Only `issued` (unpaid) and `partially_paid` invoices are included in AR aging | Query WHERE clause filters by status |
| BR-002 | Age buckets are based on `issued_at` relative to `as_of` date (defaults to today) | CASE WHEN logic in SQL aggregate |
| BR-003 | Patient's `balance_due` must be > 0 to be included | Query WHERE clause: `balance_due > 0` |
| BR-004 | Patients are cross-clinic filtered (RLS + explicit WHERE clause) | Tenant isolation at database level + query filter |
| BR-005 | Doctor weekly includes only `COMPLETED` and `AWAITING_PAYMENT` visits | Query WHERE status filter |
| BR-006 | CSV export cells are guarded against formula injection (=, +, −, @, TAB, CR) | `_csv_safe()` function applies leading apostrophe |
| BR-007 | API responses use `Decimal` (numeric precision for financial data) | Python Pydantic schemas define Decimal types |
| BR-008 | FE must not display mock/hardcoded data — show error state on API failure | FE error state guard (no fallback to MOCK_DATA) |

---

## Tenant Isolation & Security

### Row-Level Security (RLS)

All database queries are executed within the RLS context set by the TenancyMiddleware and `get_db` dependency. This ensures:
- User's `clinic_id` is enforced at the query level
- Cross-clinic data leakage is prevented by database-level RLS policies

### Explicit clinic_id Filtering

In addition to RLS, queries include explicit `WHERE clinic_id = :clinic_id` clauses (belt-and-suspenders pattern) to ensure safety if RLS policies are inadvertently bypassed.

### Permission Gating

- AR aging endpoints require `report.financial` permission
- Doctor weekly endpoint requires `report.view` permission

Users without the appropriate permission receive **403 Forbidden**.

---

## Summary

These three endpoints provide:
1. **AR Aging Report** — financial health snapshot of outstanding invoices by age and patient
2. **AR Aging Export** — CSV download for external analysis or printing
3. **Doctor Weekly** — visit volume trend data for dashboard charts

All endpoints enforce tenant isolation, permission gating, and data integrity (Decimal types, formula injection guards, date validation).
