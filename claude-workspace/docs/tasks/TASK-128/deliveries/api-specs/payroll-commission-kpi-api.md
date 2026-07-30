# API Specification: Payroll — Commission + KPI + Claw-back

**Task:** TASK-128 — Payroll: base + commission + KPI + claw-back + month-end screen
**Date:** 2026-07-30
**Version:** 1.0
**Status:** Complete (implementation) — pending Code Review / Test

---

## Overview

This spec documents the TASK-128 extensions: the new `/hr/commission-rules` and `/hr/kpi-targets` CRUD endpoints, and the extended payslip shape returned by the existing `/hr/payroll` endpoints (unchanged paths, additive response fields only).

**Base URL:** `/api/v1`

**Authentication:** All endpoints require bearer token authentication:
```
Authorization: Bearer {jwt_token}
```

**Clinic Context:** Tenant-scoped — all rows belong to the caller's active clinic (RLS-enforced).

**Permissions:** No new permission introduced. Everything below is gated by the existing `payroll.manage` permission (same boundary as `/hr/payroll`).

---

## Endpoints Summary

| # | Method | Path | Purpose |
|---|--------|------|---------|
| 1 | GET | `/hr/payroll?month=` | *(extended)* Payslips now include commission/KPI/claw-back breakdown |
| 2 | POST | `/hr/payroll/post-to-expense?month=` | *(extended)* Also marks the period's `payroll_adjustment` rows `applied=true` |
| 3 | GET | `/hr/commission-rules` | List commission rate config (per service_type + medicine) |
| 4 | POST | `/hr/commission-rules` | Create a commission rate |
| 5 | PATCH | `/hr/commission-rules/{id}` | Update rate_percent / is_active |
| 6 | DELETE | `/hr/commission-rules/{id}` | Soft-delete |
| 7 | GET | `/hr/kpi-targets?period=` | List KPI targets for a period |
| 8 | POST | `/hr/kpi-targets` | Create a KPI target for a staff member/period |
| 9 | PATCH | `/hr/kpi-targets/{id}` | Update revenue_target / bonus_amount |
| 10 | DELETE | `/hr/kpi-targets/{id}` | Soft-delete |

---

## Endpoint Details

### 1. GET /hr/payroll?month=YYYY-MM *(extended)*

**Description:** Unchanged path/params. Each payslip object now includes 4 additional fields, already folded into `gross_pay`/`net_pay`.

**Response (200 OK):**
```json
{
  "month": "2026-07",
  "payslips": [
    {
      "staff_id": "uuid",
      "staff_code": "NV0001",
      "full_name": "Bác sĩ A",
      "pay_type": "monthly",
      "worked_days": 26,
      "total_hours": 0,
      "ot_hours": 0,
      "absent_days": 0,
      "leave_days": 0,
      "late_count": 0,
      "base_earned": 20000000,
      "overtime_pay": 0,
      "allowance": 0,
      "attendance_bonus": 0,
      "late_penalty_total": 0,
      "procedure_commission": 1000000,
      "medicine_commission": 250000,
      "kpi_bonus": 500000,
      "clawback_adjustment": -400000,
      "gross_pay": 21350000,
      "net_pay": 21350000
    }
  ],
  "total_net": 21350000,
  "total_gross": 21350000,
  "staff_count": 1
}
```

**Notes:**
- `procedure_commission`, `medicine_commission`, `kpi_bonus` are always `>= 0`.
- `clawback_adjustment` is `<= 0` (0 when no claw-back applies to this period).
- A staff member with no `base_salary`/`hourly_rate` configured but with non-zero commission/KPI/claw-back this period **now appears on the payslip list** (previously they'd be silently excluded) — `base_earned`/`overtime_pay`/`allowance`/etc. are `0` in that case.

### 2. POST /hr/payroll/post-to-expense?month=YYYY-MM *(extended)*

**Description:** Unchanged request/response shape. Side effect added: marks every `payroll_adjustment` row with `apply_period = month` and `applied = false` as `applied = true` — this is the "period locked" bookkeeping claw-back checks against.

**Response (200 OK):** unchanged —
```json
{ "expense_id": "uuid", "amount": 21350000, "month": "2026-07" }
```

---

### 3. GET /hr/commission-rules

**Description:** List all commission rate rows for the current clinic (both `service_type` and `medicine` rule types, active and inactive).

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "uuid",
      "rule_type": "service_type",
      "service_type_id": "uuid-of-procedure-type",
      "rate_percent": 10.00,
      "is_active": true,
      "created_at": "2026-07-30T00:00:00Z",
      "updated_at": "2026-07-30T00:00:00Z"
    },
    {
      "id": "uuid",
      "rule_type": "medicine",
      "service_type_id": null,
      "rate_percent": 5.00,
      "is_active": true,
      "created_at": "2026-07-30T00:00:00Z",
      "updated_at": "2026-07-30T00:00:00Z"
    }
  ]
}
```

### 4. POST /hr/commission-rules

**Request Body:**
```json
{
  "rule_type": "service_type",
  "service_type_id": "uuid-of-procedure-type",
  "rate_percent": 10.0,
  "is_active": true
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `rule_type` | `"service_type"` \| `"medicine"` | Yes | |
| `service_type_id` | UUID | Required iff `rule_type='service_type'`; must be omitted/null iff `rule_type='medicine'` (422 otherwise) | |
| `rate_percent` | number | Yes | 0–100 |
| `is_active` | boolean | No | default `true` |

**Errors:**
- `409 Conflict` — a rule already exists for this `(clinic, service_type_id)` (service_type rules) or the clinic already has a medicine rule.
- `422 Unprocessable Entity` — `service_type_id` present/absent inconsistent with `rule_type`.

### 5. PATCH /hr/commission-rules/{id}

**Request Body:** `{ "rate_percent"?: number, "is_active"?: boolean }` — `service_type_id`/`rule_type` cannot be changed (delete + recreate instead).

**Errors:** `404 Not Found` if the rule doesn't exist or belongs to another clinic.

### 6. DELETE /hr/commission-rules/{id}

Soft-delete. `204 No Content` on success. `404 Not Found` if missing.

---

### 7. GET /hr/kpi-targets?period=YYYY-MM

**Description:** List KPI targets. `period` is optional — omit to list all periods.

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "uuid",
      "staff_id": "uuid",
      "period": "2026-07",
      "revenue_target": 100000000,
      "bonus_amount": 5000000,
      "created_at": "2026-07-30T00:00:00Z",
      "updated_at": "2026-07-30T00:00:00Z"
    }
  ]
}
```

### 8. POST /hr/kpi-targets

**Request Body:**
```json
{
  "staff_id": "uuid",
  "period": "2026-07",
  "revenue_target": 100000000,
  "bonus_amount": 5000000
}
```

`period` must match `^\d{4}-(0[1-9]|1[0-2])$`.

**Errors:** `409 Conflict` if a target already exists for `(staff_id, period)`.

### 9. PATCH /hr/kpi-targets/{id}

**Request Body:** `{ "revenue_target"?: number, "bonus_amount"?: number }` — `staff_id`/`period` cannot be changed.

**Errors:** `404 Not Found`.

### 10. DELETE /hr/kpi-targets/{id}

Soft-delete. `204 No Content`. `404 Not Found` if missing.

---

## Bonus Formula (KPI)

```
achievement_ratio = min(1, actual_revenue / revenue_target)   # 0 if revenue_target <= 0 or actual_revenue <= 0
bonus = bonus_amount * achievement_ratio
```

`actual_revenue` = the staff member's total attributed procedure + medicine revenue for the period (the same revenue commission was computed on) — see functional design §8.1 for why this is scoped to commission-eligible revenue rather than all revenue.

## Claw-back (no dedicated endpoint — automatic side effect)

Triggered internally from `billing` void/refund (`POST /invoices/{id}/void`, `POST /invoices/{id}/refund` — unchanged request/response shapes, no new fields). When the invoice's source period is already locked (posted to expense), a negative `payroll_adjustment` is written for the next period, attributed per affected doctor. This is entirely server-side bookkeeping; it surfaces to the FE only via the `clawback_adjustment` field on a later `GET /hr/payroll?month=<next period>` call.
