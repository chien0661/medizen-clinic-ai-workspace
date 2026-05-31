# API Reference — Super Admin Analytics (TASK-071)

**Version**: 1.0  
**Date**: 2026-06-01  
**Base URL**: `/api/v1/superadmin`  
**Authentication**: Required (Bearer token)  

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [1. GET /analytics/overview](#1-get-analyticsoverview)
- [2. GET /analytics/timeseries](#2-get-analyticstimeseries)
- [3. GET /analytics/clinics](#3-get-analyticsclinics)
- [Error Handling](#error-handling)
- [Examples](#examples)

---

## Overview

The Super Admin Analytics API provides three endpoints for retrieving clinic statistics:

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `/analytics/overview` | Aggregate metrics (visits, revenue, avg_revenue_per_visit, new_patients, returning_patients) | Single object |
| `/analytics/timeseries` | Time-series data for charting (visits/revenue/new_patients over time) | Array of {period, value} |
| `/analytics/clinics` | Per-clinic comparison table | Array of clinic objects |

All endpoints support optional clinic filtering and require superuser access.

---

## Authentication

All requests must include an `Authorization` header with a valid Bearer token:

```
Authorization: Bearer {access_token}
```

If the token is missing or invalid, the API returns **401 Unauthorized**.  
If the user is not a superuser, the API returns **403 Forbidden**.

---

## 1. GET /analytics/overview

### Description

Returns aggregate statistics (total visits, revenue, averages, new/returning patients) for a given date range. Optionally filtered by clinic.

### Request

#### URL

```
GET /api/v1/superadmin/analytics/overview
```

#### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `date_from` | Date (yyyy-MM-dd) | Yes | Start date (inclusive) | `2026-05-01` |
| `date_to` | Date (yyyy-MM-dd) | Yes | End date (inclusive) | `2026-05-31` |
| `clinic_id` | UUID | No | Filter by specific clinic; if omitted, returns all clinics | `550e8400-e29b-41d4-a716-446655440000` |

#### Example Requests

**All clinics, May 2026:**
```
GET /api/v1/superadmin/analytics/overview?date_from=2026-05-01&date_to=2026-05-31
```

**Specific clinic, May 2026:**
```
GET /api/v1/superadmin/analytics/overview?date_from=2026-05-01&date_to=2026-05-31&clinic_id=550e8400-e29b-41d4-a716-446655440000
```

### Response

#### Success (200 OK)

```json
{
  "data": {
    "visits": 250,
    "revenue": 25000000,
    "avg_revenue_per_visit": 100000.0,
    "new_patients": 45,
    "returning_patients": 205
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `visits` | Integer | Total completed visits in the date range |
| `revenue` | Decimal | Total revenue from paid invoices (in VND) |
| `avg_revenue_per_visit` | Decimal | Average revenue per visit (rounded to 2 decimal places) |
| `new_patients` | Integer | Count of patients created within the date range |
| `returning_patients` | Integer | Count of distinct patients who visited in the range but were created before it |

#### Error (422 Unprocessable Entity)

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Date range cannot exceed 365 days"
}
```

---

## 2. GET /analytics/timeseries

### Description

Returns time-series data for a specific metric (visits, revenue, or new_patients) at a chosen granularity (day, week, month, year). Used for rendering line charts.

### Request

#### URL

```
GET /api/v1/superadmin/analytics/timeseries
```

#### Query Parameters

| Parameter | Type | Required | Description | Valid Values |
|-----------|------|----------|-------------|--------------|
| `metric` | String | Yes | Which metric to return | `visits`, `revenue`, `new_patients` |
| `granularity` | String | Yes | Time bucketing | `day`, `week`, `month`, `year` |
| `date_from` | Date (yyyy-MM-dd) | Yes | Start date (inclusive) | `2026-05-01` |
| `date_to` | Date (yyyy-MM-dd) | Yes | End date (inclusive) | `2026-05-31` |
| `clinic_id` | UUID | No | Filter by specific clinic | `550e8400-e29b-41d4-a716-446655440000` |

#### Example Requests

**Daily visits for May 2026:**
```
GET /api/v1/superadmin/analytics/timeseries?metric=visits&granularity=day&date_from=2026-05-01&date_to=2026-05-31
```

**Weekly revenue for a specific clinic:**
```
GET /api/v1/superadmin/analytics/timeseries?metric=revenue&granularity=week&date_from=2026-05-01&date_to=2026-05-31&clinic_id=550e8400-e29b-41d4-a716-446655440000
```

**Monthly new patients for 2026:**
```
GET /api/v1/superadmin/analytics/timeseries?metric=new_patients&granularity=month&date_from=2026-01-01&date_to=2026-12-31
```

### Response

#### Success (200 OK)

```json
{
  "data": [
    { "period": "2026-05-01", "value": 45 },
    { "period": "2026-05-02", "value": 52 },
    { "period": "2026-05-03", "value": 38 },
    { "period": "2026-05-04", "value": 61 },
    { "period": "2026-05-05", "value": 54 }
  ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `period` | String (ISO 8601) | Time bucket (date or date range depending on granularity) |
| `value` | Decimal | Value of the metric for that period |

**Note on `period` format:**
- `granularity=day`: `YYYY-MM-DD` (e.g., `2026-05-01`)
- `granularity=week`: Start date of the week, `YYYY-MM-DD` (e.g., `2026-04-27`)
- `granularity=month`: First day of the month, `YYYY-MM-DD` (e.g., `2026-05-01`)
- `granularity=year`: January 1st, `YYYY-MM-DD` (e.g., `2026-01-01`)

#### Error (422 Unprocessable Entity)

```json
{
  "code": "VALIDATION_ERROR",
  "message": "date_from must be <= date_to"
}
```

---

## 3. GET /analytics/clinics

### Description

Returns a table of per-clinic statistics, sorted by a chosen metric (revenue or visits) and limited to a specified number of rows. Each clinic row includes aggregated visits, revenue, and calculated averages.

### Request

#### URL

```
GET /api/v1/superadmin/analytics/clinics
```

#### Query Parameters

| Parameter | Type | Required | Description | Default | Range |
|-----------|------|----------|-------------|---------|-------|
| `date_from` | Date (yyyy-MM-dd) | Yes | Start date (inclusive) | — | — |
| `date_to` | Date (yyyy-MM-dd) | Yes | End date (inclusive) | — | — |
| `sort_by` | String | No | Sort column | `revenue` | `revenue`, `visits` |
| `limit` | Integer | No | Max number of clinics to return | `20` | 1–200 |

#### Example Requests

**Top 20 clinics by revenue:**
```
GET /api/v1/superadmin/analytics/clinics?date_from=2026-05-01&date_to=2026-05-31&sort_by=revenue&limit=20
```

**Top 50 clinics by visits:**
```
GET /api/v1/superadmin/analytics/clinics?date_from=2026-05-01&date_to=2026-05-31&sort_by=visits&limit=50
```

### Response

#### Success (200 OK)

```json
{
  "data": [
    {
      "clinic_id": "550e8400-e29b-41d4-a716-446655440000",
      "clinic_name": "Phòng khám Trung tâm",
      "visits": 500,
      "revenue": 50000000,
      "avg_daily_visits": 16.67,
      "avg_weekly_visits": 100.0,
      "avg_monthly_revenue": 5000000.0
    },
    {
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "clinic_name": "Phòng khám Tây Hà Nội",
      "visits": 350,
      "revenue": 35000000,
      "avg_daily_visits": 11.67,
      "avg_weekly_visits": 70.0,
      "avg_monthly_revenue": 3500000.0
    },
    {
      "clinic_id": "550e8400-e29b-41d4-a716-446655440002",
      "clinic_name": "Phòng khám Đông Hà Nội",
      "visits": 200,
      "revenue": 20000000,
      "avg_daily_visits": 6.67,
      "avg_weekly_visits": 40.0,
      "avg_monthly_revenue": 2000000.0
    }
  ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `clinic_id` | UUID (String) | Unique clinic identifier |
| `clinic_name` | String | Clinic name |
| `visits` | Integer | Total completed visits in the date range |
| `revenue` | Decimal | Total revenue from paid invoices (in VND) |
| `avg_daily_visits` | Decimal | Average visits per day = visits / (days in range) |
| `avg_weekly_visits` | Decimal | Average visits per week = visits / (weeks in range) |
| `avg_monthly_revenue` | Decimal | Average revenue per month = revenue / (months in range) |

#### Error (422 Unprocessable Entity)

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Limit must be between 1 and 200"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Common Reason |
|------|---------|--------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameter format (e.g., date not in yyyy-MM-dd format) |
| 401 | Unauthorized | Missing or invalid Bearer token |
| 403 | Forbidden | User is not a superuser |
| 422 | Unprocessable Entity | Validation error (e.g., date_from > date_to, range > 365 days) |
| 500 | Internal Server Error | Database query error or unexpected server error |

### Error Response Format

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable error description"
}
```

### Common Error Scenarios

#### 401 Unauthorized — Missing Token
```
GET /api/v1/superadmin/analytics/overview?date_from=2026-05-01&date_to=2026-05-31

Response:
{
  "code": "UNAUTHORIZED",
  "message": "Unauthorized: Invalid or missing token"
}
```

#### 403 Forbidden — Not Superuser
```
GET /api/v1/superadmin/analytics/overview?date_from=2026-05-01&date_to=2026-05-31
Authorization: Bearer {clinic-admin-token}

Response:
{
  "code": "FORBIDDEN",
  "message": "Forbidden: Only superusers can access this endpoint"
}
```

#### 422 Validation Error — Range Exceeds 365 Days
```
GET /api/v1/superadmin/analytics/overview?date_from=2025-05-31&date_to=2026-05-31

Response:
{
  "code": "VALIDATION_ERROR",
  "message": "Date range cannot exceed 365 days"
}
```

#### 422 Validation Error — Invalid Date Order
```
GET /api/v1/superadmin/analytics/overview?date_from=2026-06-01&date_to=2026-05-31

Response:
{
  "code": "VALIDATION_ERROR",
  "message": "date_from must be <= date_to"
}
```

#### 422 Validation Error — Invalid Limit
```
GET /api/v1/superadmin/analytics/clinics?date_from=2026-05-01&date_to=2026-05-31&limit=500

Response:
{
  "code": "VALIDATION_ERROR",
  "message": "Limit must be between 1 and 200"
}
```

---

## Examples

### Example 1: Get Daily Stats for Today

**Request:**
```
GET /api/v1/superadmin/analytics/overview?date_from=2026-05-31&date_to=2026-05-31
Authorization: Bearer {superuser_token}
```

**Response:**
```json
{
  "data": {
    "visits": 45,
    "revenue": 4500000,
    "avg_revenue_per_visit": 100000.0,
    "new_patients": 5,
    "returning_patients": 40
  }
}
```

### Example 2: Get Weekly Visits Chart for Last Month

**Request:**
```
GET /api/v1/superadmin/analytics/timeseries?metric=visits&granularity=week&date_from=2026-05-01&date_to=2026-05-31
Authorization: Bearer {superuser_token}
```

**Response:**
```json
{
  "data": [
    { "period": "2026-04-29", "value": 120 },
    { "period": "2026-05-06", "value": 145 },
    { "period": "2026-05-13", "value": 132 },
    { "period": "2026-05-20", "value": 155 },
    { "period": "2026-05-27", "value": 98 }
  ]
}
```

### Example 3: Get Top 10 Clinics by Revenue for May

**Request:**
```
GET /api/v1/superadmin/analytics/clinics?date_from=2026-05-01&date_to=2026-05-31&sort_by=revenue&limit=10
Authorization: Bearer {superuser_token}
```

**Response:**
```json
{
  "data": [
    {
      "clinic_id": "550e8400-e29b-41d4-a716-446655440000",
      "clinic_name": "Phòng khám Trung tâm",
      "visits": 500,
      "revenue": 50000000,
      "avg_daily_visits": 16.67,
      "avg_weekly_visits": 100.0,
      "avg_monthly_revenue": 5000000.0
    },
    {
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "clinic_name": "Phòng khám Tây Hà Nội",
      "visits": 350,
      "revenue": 35000000,
      "avg_daily_visits": 11.67,
      "avg_weekly_visits": 70.0,
      "avg_monthly_revenue": 3500000.0
    }
  ]
}
```

### Example 4: Get Monthly Revenue Chart for Specific Clinic

**Request:**
```
GET /api/v1/superadmin/analytics/timeseries?metric=revenue&granularity=month&date_from=2026-01-01&date_to=2026-05-31&clinic_id=550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {superuser_token}
```

**Response:**
```json
{
  "data": [
    { "period": "2026-01-01", "value": 4500000 },
    { "period": "2026-02-01", "value": 5200000 },
    { "period": "2026-03-01", "value": 4800000 },
    { "period": "2026-04-01", "value": 5500000 },
    { "period": "2026-05-01", "value": 5000000 }
  ]
}
```

### Example 5: Get New Patients Count (Weekly) for Last Quarter

**Request:**
```
GET /api/v1/superadmin/analytics/timeseries?metric=new_patients&granularity=week&date_from=2026-03-01&date_to=2026-05-31
Authorization: Bearer {superuser_token}
```

**Response:**
```json
{
  "data": [
    { "period": "2026-03-02", "value": 12 },
    { "period": "2026-03-09", "value": 15 },
    { "period": "2026-03-16", "value": 18 },
    { "period": "2026-03-23", "value": 20 },
    { "period": "2026-03-30", "value": 14 },
    { "period": "2026-04-06", "value": 16 },
    { "period": "2026-04-13", "value": 19 },
    { "period": "2026-04-20", "value": 21 },
    { "period": "2026-04-27", "value": 17 },
    { "period": "2026-05-04", "value": 13 },
    { "period": "2026-05-11", "value": 18 },
    { "period": "2026-05-18", "value": 22 },
    { "period": "2026-05-25", "value": 15 }
  ]
}
```

---

## Rate Limiting

No specific rate limiting is documented for these endpoints. However, complex queries (e.g., 365-day range with daily granularity) may take longer to execute. Consider caching results or breaking large date ranges into smaller chunks if needed.

---

## Notes

- All timestamps in request/response are in **yyyy-MM-dd** format (date only, no time component)
- Revenue values are in **VND** (Vietnamese Dong)
- All decimal values are rounded to 2 decimal places where applicable
- The API uses **cross-tenant data visibility** for superusers — they can see all clinics regardless of RLS policies
