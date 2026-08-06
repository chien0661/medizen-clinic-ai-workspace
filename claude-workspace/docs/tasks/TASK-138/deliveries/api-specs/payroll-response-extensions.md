# API Specification: Payroll Response Extensions (TASK-138)

**Version:** 1.0
**Date:** 2026-08-07
**Status:** Implemented & Tested

---

## Overview

The `GET /api/v1/hr/payroll?month=YYYY-MM` endpoint (introduced in TASK-128) is extended in TASK-138 to include:

1. **New pay type fields** for per_session and per_shift: `session_rate`, `shift_rate`, `completed_shifts`
2. **Commission rate traceability fields**: `procedure_rate_percent`, `procedure_rate_source`, `medicine_rate_percent`, `medicine_rate_source`

This document specifies the new fields and their semantics.

---

## Endpoint

```
GET /api/v1/hr/payroll?month=YYYY-MM
```

**Authentication:** Bearer token required; permission `payroll.view` required.

**Response:** 200 OK with extended `Payslip` schema (see below).

---

## Extended Payslip Schema

### Full Example Response

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
      },
      {
        "staff_id": "staff-002-uuid",
        "staff_code": "NV002",
        "full_name": "Trần Thị B",
        "pay_type": "per_shift",
        "worked_days": 18.0,
        "total_hours": 144.0,
        "ot_hours": 0.0,
        "absent_days": 2,
        "leave_days": 0,
        "late_count": 0,
        "base_earned": 4500.0,
        "overtime_pay": 0.0,
        "allowance": 300.0,
        "attendance_bonus": 0.0,
        "late_penalty_total": 0.0,
        "gross_pay": 4800.0,
        "net_pay": 4320.0,
        "procedure_commission": 0.0,
        "medicine_commission": 0.0,
        "kpi_bonus": 0.0,
        "clawback_adjustment": 0.0,
        
        "session_rate": null,
        "shift_rate": 250.0,
        "completed_shifts": 18,
        
        "procedure_rate_percent": null,
        "procedure_rate_source": null,
        "medicine_rate_percent": null,
        "medicine_rate_source": null
      },
      {
        "staff_id": "staff-003-uuid",
        "staff_code": "DR001",
        "full_name": "Phạm Văn C (Doctor)",
        "pay_type": "monthly",
        "worked_days": 22.0,
        "total_hours": 176.0,
        "ot_hours": 0.0,
        "absent_days": 0,
        "leave_days": 0,
        "late_count": 0,
        "base_earned": 5000.0,
        "overtime_pay": 0.0,
        "allowance": 500.0,
        "attendance_bonus": 300.0,
        "late_penalty_total": 0.0,
        "gross_pay": 6800.0,
        "net_pay": 6120.0,
        "procedure_commission": 500.0,
        "medicine_commission": 80.0,
        "kpi_bonus": 200.0,
        "clawback_adjustment": 0.0,
        
        "session_rate": null,
        "shift_rate": null,
        "completed_shifts": 0,
        
        "procedure_rate_percent": 10.0,
        "procedure_rate_source": "clinic_default",
        "medicine_rate_percent": 5.0,
        "medicine_rate_source": "clinic_default"
      }
    ],
    "total_net": 16440.0,
    "total_gross": 16800.0,
    "staff_count": 3
  }
}
```

---

## New Field Specifications

### Pay Type Fields

#### `session_rate` (float | null)

**Description:** The configured unit rate (VND/day) for per_session pay type.

**Semantics:**
- When `pay_type = "per_session"`: populated with the configured `staff_profile.session_rate`
- When `pay_type ≠ "per_session"`: always `null`

**Example:** `200.0` means VND 200,000 per day (buổi)

**Calculation Reference:** `base_earned = session_rate × worked_days`

#### `shift_rate` (float | null)

**Description:** The configured unit rate (VND/shift) for per_shift pay type.

**Semantics:**
- When `pay_type = "per_shift"`: populated with the configured `staff_profile.shift_rate`
- When `pay_type ≠ "per_shift"`: always `null`

**Example:** `250.0` means VND 250,000 per shift

**Calculation Reference:** `base_earned = shift_rate × completed_shifts`

#### `completed_shifts` (integer)

**Description:** Count of shifts with `status='completed'` in the pay period.

**Semantics:**
- Relevant for `pay_type = "per_shift"`: shows how many completed shifts this staff member worked
- For other pay types: always `0` (shifts are not the pay basis)

**Example:** `18` shifts completed in the month

**Data Source:** Count of `Shift` rows where `status = 'completed'` and `staff_id = this_staff` and `shift_date` falls in the month.

---

### Commission Rate Traceability Fields

#### `procedure_rate_percent` (float | null)

**Description:** The commission percentage (0–100) actually applied to **procedure (service) revenue** this period.

**Semantics:**
- When procedure commission was earned (`procedure_commission > 0`): shows the exact % rate used
- When no procedure commission earned (`procedure_commission = 0` or `null`): `null`
- Reflects per-staff override if configured, or clinic-wide rate if no override, or `null` if no rate exists

**Example:**
- `12.0` means 12% commission was applied to procedure revenue
- `null` means the staff earned no procedure commission this period

**Resolution Order (how the rate was chosen):**
1. If a per-staff commission override exists (`commission_rule` with `staff_id = this_staff`), use that rate
2. Else if a clinic-wide rule exists (`commission_rule` with `staff_id = NULL`), use that rate
3. Else `null` (no commission)

#### `procedure_rate_source` (enum | null)

**Description:** Indicates the **source** of the `procedure_rate_percent`: whether it came from a per-staff override or the clinic-wide default.

**Allowed values:**
- `"staff_override"`: Per-staff commission override was used (higher priority)
- `"clinic_default"`: Clinic-wide rule was used (fallback)
- `null`: No procedure commission earned this period

**Semantics:**
- When `procedure_rate_percent = null`, `procedure_rate_source = null` (always paired)
- When `procedure_rate_percent ≠ null`, `procedure_rate_source` is one of the above

**Example:**
- `"staff_override"` + `12.0%`: This doctor has a custom 12% rate
- `"clinic_default"` + `10.0%`: This doctor uses the clinic's standard 10% rate
- `null` + `null`: No procedure commission

#### `medicine_rate_percent` (float | null)

**Description:** The commission percentage (0–100) actually applied to **medicine revenue** this period.

**Semantics:**
- Same as `procedure_rate_percent`, but for medicine/pharmaceutical revenue
- When medicine commission earned: shows the exact rate; else `null`

**Example:** `6.0` means 6% of medicine revenue was paid as commission

#### `medicine_rate_source` (enum | null)

**Description:** Source of `medicine_rate_percent`: per-staff override or clinic-wide.

**Allowed values:** Same as `procedure_rate_source`:
- `"staff_override"`
- `"clinic_default"`
- `null`

---

## Backward Compatibility

**For payslips from before this change (or from staff with no commission):**

The four new rate/source fields will have `null` values if:
1. The payslip was generated before TASK-138 (pre-migration)
2. The staff member earned no commission this period
3. No commission rule is configured for the staff

**Frontend handling:**
```javascript
// Safe to check without crashing on older payslips
if (payslip.procedure_rate_percent !== null) {
  // Display rate badge: "12% · tỷ lệ riêng" or "10% · tỷ lệ chung"
  renderRateBadge(payslip.procedure_rate_percent, payslip.procedure_rate_source);
}
```

---

## Frontend Display Examples

### Example 1: Per-Session Staff with Commission (Override)

```
Staff: Nguyễn Văn A (NV001)
Pay Type: Per Session (Theo buổi)
Worked Days: 20.5 buổi × VND 200,000 = VND 4,100,000 (base_earned)

Procedure Commission: VND 150,000
  → Badge: "12% · tỷ lệ riêng" (amber, indicating override)
  
Medicine Commission: VND 45,000
  → Badge: "6% · tỷ lệ chung" (gray, indicating clinic default)
```

### Example 2: Per-Shift Staff (No Commission)

```
Staff: Trần Thị B (NV002)
Pay Type: Per Shift (Theo ca)
Completed Shifts: 18 × VND 250,000 = VND 4,500,000 (base_earned)

Procedure Commission: VND 0
  → No badge (null rate)
  
Medicine Commission: VND 0
  → No badge (null rate)
```

### Example 3: Monthly Doctor (With Both Override and Default)

```
Staff: Phạm Văn C (DR001)
Pay Type: Monthly
Base: VND 5,000,000

Procedure Commission: VND 500,000
  → Badge: "10% · tỷ lệ chung" (gray, using clinic-wide rule)
  
Medicine Commission: VND 80,000
  → Badge: "5% · tỷ lệ chung" (gray, using clinic-wide rule)
```

---

## Calculation Examples

### Per-Session Pay Calculation

```
Staff Configuration:
  pay_type = 'per_session'
  session_rate = 200.00

Attendance Grid (August 2026):
  - 20 full days (present = 1.0 each)
  - 1 half day (half = 0.5)
  - 2 absent days (not marked)
  - No leave days
  Total: 20.5 working days

Result:
  worked_days = 20.5
  base_earned = 200.00 × 20.5 = 4100.00
  session_rate = 200.00
  shift_rate = null
  completed_shifts = 0
```

### Per-Shift Pay Calculation

```
Staff Configuration:
  pay_type = 'per_shift'
  shift_rate = 250.00

Shifts in August 2026:
  - 18 Shift rows with status='completed'
  - 2 Shift rows with status='cancelled' (not counted)

Result:
  worked_days = 18 (conceptually, representing completed shifts)
  base_earned = 250.00 × 18 = 4500.00
  session_rate = null
  shift_rate = 250.00
  completed_shifts = 18
```

### Commission Rate Resolution

```
Clinic A - Service Type DV001:
  Clinic-wide rule: 10%
  Dr. A override rule: 15%
  Dr. B (no override): —

August Revenue:
  Dr. A procedure revenue: VND 1000
  Dr. B procedure revenue: VND 1000

Results:
  Dr. A:
    procedure_commission = 1000 × 15% = 150
    procedure_rate_percent = 15.0
    procedure_rate_source = "staff_override"
  
  Dr. B:
    procedure_commission = 1000 × 10% = 100
    procedure_rate_percent = 10.0
    procedure_rate_source = "clinic_default"
```

---

## Error Handling

The `/hr/payroll` endpoint maintains existing error handling:

| HTTP | Code | Message | Cause |
|------|------|---------|-------|
| 400 | INVALID_REQUEST | "Invalid month format (expected YYYY-MM)" | Malformed month parameter |
| 401 | UNAUTHORIZED | "Not authenticated" | Missing/invalid token |
| 403 | FORBIDDEN | "Insufficient permissions" | Lacks `payroll.view` permission |
| 500 | INTERNAL_ERROR | "Failed to compute payroll" | Server error during calculation |

The new fields do not introduce new error conditions (they are additive).

---

## Testing Checklist

- [ ] **Per-session staff**: verify `session_rate` populated, `worked_days` from attendance grid, `shift_rate` is null
- [ ] **Per-shift staff**: verify `shift_rate` populated, `completed_shifts` count, `session_rate` is null
- [ ] **Monthly staff**: verify both `session_rate` and `shift_rate` are null
- [ ] **Commission override**: verify `rate_percent` and `rate_source="staff_override"` when override exists
- [ ] **Commission fallback**: verify `rate_percent` and `rate_source="clinic_default"` when using clinic-wide rule
- [ ] **No commission**: verify `rate_percent=null` and `rate_source=null` when no rule or no revenue
- [ ] **Payslip UI badge display**: renders correctly for override / default / null cases
- [ ] **Backward compat**: older payslips (pre-TASK-138) don't crash when parsed; fields are null

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-07 | Initial spec: per-session/per-shift rate fields + commission rate/source traceability (TASK-138) |

