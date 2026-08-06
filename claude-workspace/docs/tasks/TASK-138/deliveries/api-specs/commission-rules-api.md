# API Specification: Commission Rules (TASK-138 Extensions)

**Version:** 1.0
**Date:** 2026-08-07
**Status:** Implemented & Tested

---

## Overview

This document specifies the commission rule endpoints, extended in TASK-138 to support per-staff commission overrides (`staff_id` parameter). The base commission-rule endpoints were introduced in TASK-128; this spec documents the new capability and changed behavior.

**Base Path:** `POST /api/v1/hr`

**Authentication:** All endpoints require Bearer token; permission `payroll.manage` required.

---

## Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hr/commission-rules` | List all rules (clinic-wide + per-staff), optionally filtered by `staff_id` |
| POST | `/hr/commission-rules` | Create a new rule (clinic-wide if `staff_id=NULL`, per-staff override if `staff_id` set) |
| PATCH | `/hr/commission-rules/{id}` | Update rule rate / is_active; `staff_id` immutable |
| DELETE | `/hr/commission-rules/{id}` | Delete (soft-delete: set `is_deleted=true`) |

---

## GET /api/v1/hr/commission-rules

**Purpose:** Retrieve commission rules (clinic-wide + per-staff overrides), optionally filtered by staff member.

### Request

#### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `staff_id` | UUID | No | If supplied, return clinic-wide rule + per-staff rules for this staff member. If omitted, return all rules (clinic-wide + all per-staff overrides) | `a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6` |

**Example:**
```
GET /api/v1/hr/commission-rules?staff_id=a1b2c3d4-...
```

### Response

#### Success (200 OK)

```json
{
  "code": "00",
  "message": "Success",
  "data": [
    {
      "id": "rule-001-uuid",
      "rule_type": "service_type",
      "service_type_id": "service-type-001-uuid",
      "staff_id": null,
      "rate_percent": 10.0,
      "is_active": true,
      "created_at": "2026-08-01T10:00:00Z",
      "updated_at": "2026-08-01T10:00:00Z"
    },
    {
      "id": "rule-002-uuid",
      "rule_type": "service_type",
      "service_type_id": "service-type-001-uuid",
      "staff_id": "staff-dr-001-uuid",
      "rate_percent": 15.0,
      "is_active": true,
      "created_at": "2026-08-06T14:30:00Z",
      "updated_at": "2026-08-06T14:30:00Z"
    },
    {
      "id": "rule-003-uuid",
      "rule_type": "medicine",
      "service_type_id": null,
      "staff_id": null,
      "rate_percent": 5.0,
      "is_active": true,
      "created_at": "2026-07-15T09:00:00Z",
      "updated_at": "2026-07-15T09:00:00Z"
    }
  ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Rule ID (unique within clinic) |
| `rule_type` | String | `"service_type"` (procedure commission) or `"medicine"` (medicine commission) |
| `service_type_id` | UUID \| null | Service type ID (required for `rule_type='service_type'`); NULL for medicine rules |
| `staff_id` | UUID \| null | **[TASK-138]** Staff ID for per-staff override (NULL = clinic-wide rule) |
| `rate_percent` | Decimal | Commission rate as percentage (0.00–100.00) |
| `is_active` | Boolean | Whether this rule is currently active |
| `created_at` | DateTime | UTC timestamp when rule was created |
| `updated_at` | DateTime | UTC timestamp when rule was last updated |

#### Error Responses

| HTTP | Code | Message | Description |
|------|------|---------|-------------|
| 400 | INVALID_REQUEST | "Invalid staff_id parameter" | Malformed UUID or invalid parameter |
| 401 | UNAUTHORIZED | "Not authenticated" | Missing or invalid token |
| 403 | FORBIDDEN | "Insufficient permissions" | User lacks `payroll.manage` permission |
| 500 | INTERNAL_ERROR | "Database error" | Server-side error |

---

## POST /api/v1/hr/commission-rules

**Purpose:** Create a new commission rule (clinic-wide or per-staff override).

### Request

#### Request Body

```json
{
  "rule_type": "service_type",
  "service_type_id": "service-type-uuid",
  "staff_id": "staff-dr-001-uuid",
  "rate_percent": 15.0,
  "is_active": true
}
```

#### Body Parameters

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| `rule_type` | String | Yes | `"service_type"` or `"medicine"` | Enum: `service_type` \| `medicine` |
| `service_type_id` | UUID | Conditional | Service type ID. **Required** if `rule_type='service_type'`; **must be NULL/omitted** if `rule_type='medicine'` | Must exist in `service_type` table (same clinic) |
| `staff_id` | UUID \| null | No | **[TASK-138]** Staff member ID for per-staff override; NULL = clinic-wide rule (default). When set, must exist in `staff_profile` table (same clinic) | If not NULL: must exist in `staff_profile` + same clinic_id |
| `rate_percent` | Decimal | Yes | Commission rate percentage | 0 ≤ rate_percent ≤ 100 (e.g., `15.0` = 15%) |
| `is_active` | Boolean | No | Active status (default: `true`) | — |

#### Validation Rules

1. **Conditional service_type_id:**
   - If `rule_type = "service_type"` and `service_type_id` is NULL → 400 error: "service_type_id required for service_type rules"
   - If `rule_type = "medicine"` and `service_type_id` is not NULL → 400 error: "service_type_id must be NULL for medicine rules"

2. **staff_id clinic scope (NEW in TASK-138):**
   - If `staff_id` is provided (not NULL), API must verify that this `staff_id` exists and belongs to the same clinic as the authenticated user
   - If staff not found in the clinic → 404 NOT_FOUND: "Staff member not found"
   - This prevents cross-clinic data leakage

3. **Uniqueness:**
   - For `service_type` rules: `(clinic_id, service_type_id, COALESCE(staff_id, zero-uuid))` must be unique
   - For `medicine` rules: `(clinic_id, COALESCE(staff_id, zero-uuid))` must be unique
   - Duplicate attempt → 422 VALIDATION_ERROR: "A rule for this staff member / service type already exists"

### Response

#### Success (201 Created)

```json
{
  "code": "00",
  "message": "Created",
  "data": {
    "id": "newly-created-rule-uuid",
    "rule_type": "service_type",
    "service_type_id": "service-type-uuid",
    "staff_id": "staff-dr-001-uuid",
    "rate_percent": 15.0,
    "is_active": true,
    "created_at": "2026-08-07T10:30:00Z",
    "updated_at": "2026-08-07T10:30:00Z"
  }
}
```

#### Error Responses

| HTTP | Code | Message | Description |
|------|------|---------|-------------|
| 400 | INVALID_REQUEST | "Validation failed: service_type_id required when rule_type='service_type'" | Missing required field based on rule_type |
| 400 | INVALID_REQUEST | "rate_percent must be between 0 and 100" | Out-of-range value |
| 401 | UNAUTHORIZED | "Not authenticated" | Missing/invalid token |
| 403 | FORBIDDEN | "Insufficient permissions" | User lacks `payroll.manage` permission |
| 404 | NOT_FOUND | "Staff member not found" | Provided `staff_id` doesn't exist in this clinic |
| 404 | NOT_FOUND | "Service type not found" | Provided `service_type_id` doesn't exist |
| 422 | VALIDATION_ERROR | "A rule for this service type and staff member already exists" | Duplicate rule (violates uniqueness) |
| 500 | INTERNAL_ERROR | "Database error" | Server-side error |

---

## PATCH /api/v1/hr/commission-rules/{id}

**Purpose:** Update an existing rule's rate and/or active status. **Note: `staff_id` is immutable after creation.**

### Request

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | UUID | Yes | Rule ID to update |

#### Request Body

```json
{
  "rate_percent": 18.0,
  "is_active": true
}
```

| Parameter | Type | Required | Description | Notes |
|-----------|------|----------|-------------|-------|
| `rate_percent` | Decimal | No | New commission rate (0–100); omit to keep current | If provided, must be in valid range |
| `is_active` | Boolean | No | New active status; omit to keep current | — |

**Important:** The `staff_id` field cannot be changed. If the request body includes `staff_id`, it is **silently ignored** (no error, but the field is not updated).

### Response

#### Success (200 OK)

```json
{
  "code": "00",
  "message": "Updated",
  "data": {
    "id": "rule-uuid",
    "rule_type": "service_type",
    "service_type_id": "service-type-uuid",
    "staff_id": "staff-dr-001-uuid",
    "rate_percent": 18.0,
    "is_active": true,
    "created_at": "2026-08-07T10:30:00Z",
    "updated_at": "2026-08-07T11:00:00Z"
  }
}
```

#### Error Responses

| HTTP | Code | Message | Description |
|------|------|---------|-------------|
| 400 | INVALID_REQUEST | "rate_percent must be between 0 and 100" | Out-of-range value |
| 401 | UNAUTHORIZED | "Not authenticated" | Missing/invalid token |
| 403 | FORBIDDEN | "Insufficient permissions" | User lacks `payroll.manage` permission |
| 404 | NOT_FOUND | "Rule not found" | Rule ID doesn't exist |
| 500 | INTERNAL_ERROR | "Database error" | Server-side error |

---

## DELETE /api/v1/hr/commission-rules/{id}

**Purpose:** Delete (soft-delete) a commission rule. The staff member reverts to the clinic-wide rate (or 0% if no clinic-wide rule exists).

### Request

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | UUID | Yes | Rule ID to delete |

### Response

#### Success (204 No Content)

No response body (standard REST convention for DELETE).

#### Error Responses

| HTTP | Code | Message | Description |
|------|------|---------|-------------|
| 401 | UNAUTHORIZED | "Not authenticated" | Missing/invalid token |
| 403 | FORBIDDEN | "Insufficient permissions" | User lacks `payroll.manage` permission |
| 404 | NOT_FOUND | "Rule not found" | Rule ID doesn't exist |
| 500 | INTERNAL_ERROR | "Database error" | Server-side error |

---

## Payroll Response (Extended)

**Endpoint:** `GET /api/v1/hr/payroll?month=YYYY-MM`

This existing endpoint (from TASK-128) is extended with new fields to support traceability of commission rates.

### New Payslip Fields (TASK-138)

Added to the `Payslip` object in the response:

```json
{
  ...existing payslip fields...,
  
  "session_rate": 200.0,
  "shift_rate": null,
  "completed_shifts": 0,
  
  "procedure_rate_percent": 15.0,
  "procedure_rate_source": "staff_override",
  "medicine_rate_percent": 5.0,
  "medicine_rate_source": "clinic_default"
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `session_rate` | float \| null | Unit rate (VND/day) for `pay_type='per_session'`; NULL for other pay types |
| `shift_rate` | float \| null | Unit rate (VND/shift) for `pay_type='per_shift'`; NULL for other pay types |
| `completed_shifts` | int | Number of shifts with status='completed' in the period (only meaningful for `pay_type='per_shift'`) |
| `procedure_rate_percent` | float \| null | Commission percentage actually applied to procedure revenue; NULL if no commission earned |
| `procedure_rate_source` | "staff_override" \| "clinic_default" \| null | Source of the procedure rate: per-staff override or clinic-wide; NULL if `procedure_rate_percent` is NULL |
| `medicine_rate_percent` | float \| null | Commission percentage applied to medicine revenue; NULL if no commission earned |
| `medicine_rate_source` | "staff_override" \| "clinic_default" \| null | Source of medicine rate; NULL if `medicine_rate_percent` is NULL |

#### Example Full Payslip Response

```json
{
  "code": "00",
  "message": "Success",
  "data": {
    "month": "2026-08",
    "payslips": [
      {
        "staff_id": "staff-001-uuid",
        "staff_code": "NV001",
        "full_name": "Nguyễn Văn A",
        "pay_type": "per_session",
        "worked_days": 20.5,
        "total_hours": 160.0,
        "ot_hours": 0.0,
        "absent_days": 2,
        "leave_days": 0,
        "late_count": 0,
        "base_earned": 4100.0,
        "overtime_pay": 0.0,
        "allowance": 500.0,
        "attendance_bonus": 200.0,
        "late_penalty_total": 0.0,
        "gross_pay": 5200.0,
        "net_pay": 4680.0,
        "procedure_commission": 150.0,
        "medicine_commission": 45.0,
        "kpi_bonus": 100.0,
        "clawback_adjustment": 0.0,
        
        "session_rate": 200.0,
        "shift_rate": null,
        "completed_shifts": 0,
        
        "procedure_rate_percent": 12.0,
        "procedure_rate_source": "staff_override",
        "medicine_rate_percent": 6.0,
        "medicine_rate_source": "clinic_default"
      }
    ],
    "total_net": 4680.0,
    "total_gross": 5200.0,
    "staff_count": 1
  }
}
```

---

## Business Rules & Rate Resolution

### Commission Rate Resolution

The system resolves the commission rate using this priority:

1. **Per-staff override**: If a rule exists with (`service_type_id`, `staff_id = this_staff`), use its rate
2. **Clinic-wide rule**: If no per-staff override, use the rule with (`service_type_id`, `staff_id = NULL`)
3. **No rule**: If neither exists, no commission (0% or null)

**Example (service_type procedure):**
```
Clinic-wide rule: 10% for service_type_001
Dr. A: override rule: 15% for service_type_001

When Dr. A performs service_type_001:
  commission % = 15% (uses override, not clinic-wide 10%)
  rate_source = "staff_override"

When Dr. B performs service_type_001:
  commission % = 10% (no override, uses clinic-wide)
  rate_source = "clinic_default"
```

### Claw-back Symmetry

When an invoice is reversed (claw-back):
- The system applies the **same rate resolution** as the original earning
- If Dr. A earned 1000 × 15% (override) = 150, the claw-back is also -150 (not -100 at clinic 10%)
- This ensures rate symmetry: what you earn with, you repay with

### Staff Without Login Account

Per TASK-138 design:
- A staff member with `user_id=NULL` (nurse, technician, etc.) can be configured with a per-staff commission override
- However, automatic commission attribution requires a linked doctor account (unchanged from TASK-128)
- Such staff members can still receive commission via manual `payroll_adjustment` (out of scope for auto commission)

---

## Testing Checklist

- [ ] **Create clinic-wide rule** (staff_id=NULL) — success, appears in list
- [ ] **Create per-staff override** for same service_type as clinic-wide — both coexist, different rates
- [ ] **Create override with non-existent staff_id** → 404 NOT_FOUND
- [ ] **Create override with cross-clinic staff_id** → 404 NOT_FOUND
- [ ] **Create duplicate rule** (same staff_id + service_type) → 422 VALIDATION_ERROR
- [ ] **Update rule rate** (rate_percent) — changes reflected in payslip
- [ ] **Update rule with staff_id in body** — staff_id ignored (immutable), other fields updated
- [ ] **Delete rule** — soft-delete, staff reverts to clinic-wide rate on next payroll
- [ ] **List all rules** (no filter) — returns clinic-wide + all per-staff
- [ ] **List rules filtered by staff_id** — returns clinic-wide + per-staff for that staff member only
- [ ] **Payslip shows correct rate_percent / rate_source** for both procedure and medicine commission
- [ ] **Claw-back applies override rate** (not clinic-wide) when reversing procedure/medicine revenue
- [ ] **Staff without account (user_id=NULL)** can be created as override target; no auto commission, manual only

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-07 | Initial spec: per-staff commission override (TASK-138) + payslip rate traceability |

