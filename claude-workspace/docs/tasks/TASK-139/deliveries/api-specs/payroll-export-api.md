# API Specification: Payroll Export (TASK-139)

**Endpoint:** `GET /api/v1/payroll/export`  
**Version:** 1.0  
**Date:** 2026-08-08  
**Status:** Approved & Implemented

---

## Overview

Exports the full payroll period (all staff with payslips) for a given month (YYYY-MM) as a single Excel file (.xlsx). The export reuses the same `compute_payroll` engine as `GET /hr/payroll` — no separate computation path, ensuring data always stays in sync.

**Key Design Decision:**  
The endpoint path is **`/api/v1/payroll/export`** (not nested under `/hr/payroll/...`), intentionally matching the sibling export-endpoint convention (`/staff/export`, `/attendance/export`, etc.). This is by design and confirmed in code review.

---

## Endpoint Details

### Request

**Method:** `GET`  
**URL:** `/api/v1/payroll/export`  
**Authentication:** Required (Bearer token)  
**Permission:** `payroll.manage` (same as `GET /hr/payroll`)

#### Query Parameters

| Parameter | Type | Required | Format | Description | Example |
|-----------|------|----------|--------|-------------|---------|
| `month` | String | Yes | `YYYY-MM` | Payroll period to export. Must match pattern `^\d{4}-(0[1-9]\|1[0-2])$` to prevent CRLF injection. | `2026-08` |

#### Request Headers

```
Authorization: Bearer {jwt_token}
X-Clinic-Id: {clinic_uuid}  [passed via middleware context]
```

#### Validation Rules

| Field | Rule | On Failure |
|-------|------|-----------|
| `month` | Match `^\d{4}-(0[1-9]\|1[0-2])$` (strict YYYY-MM) | 422 Unprocessable Entity |
| `Authorization` | Valid JWT token | 401 Unauthorized |
| `payroll.manage` permission | User role has permission | 403 Forbidden |
| Clinic isolation | Access only current clinic's data | 403 (implicit via middleware) |

#### Invalid Month Examples (all return 422)

```
2026-13        → month 13 doesn't exist
2026/08        → uses "/" instead of "-"
2026-8         → month not zero-padded
202608         → missing separator
2026-08\r\n    → embedded CRLF (injection attempt)
2026-08 08     → extra spaces
```

---

### Response

#### Success Response (200 OK)

**Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

**Headers:**
```
Content-Disposition: attachment; filename="bang_luong_2026-08.xlsx"
Content-Length: {file_size}
```

**Body:** Binary .xlsx file

**Excel Structure:**

| Row | Content |
|-----|---------|
| 1 | **Title:** "Bảng lương tháng 2026-08" |
| 2 | **Headers:** 27 column names (Vietnamese) |
| 3+ | **Data rows:** One per staff member with payslip, sorted by `staff_code` |
| (Optional) | **Total row:** Sum of numeric columns (implementation detail) |

**Data Format per Row:**

Each data row contains exactly **27 columns**:

```
[staff_code, full_name, pay_type, worked_days, total_hours, ot_hours, 
 absent_days, leave_days, late_count, session_rate, shift_rate, completed_shifts,
 base_earned, overtime_pay, allowance, attendance_bonus, late_penalty_total,
 procedure_commission, procedure_rate_percent, procedure_rate_source,
 medicine_commission, medicine_rate_percent, medicine_rate_source,
 kpi_bonus, clawback_adjustment, gross_pay, net_pay]
```

**Data Types in Excel:**

| Columns | Type | Notes |
|---------|------|-------|
| staff_code, full_name, pay_type | Text | |
| worked_days, total_hours, ot_hours, ... | Number | Real numeric format, not text |
| All money columns (base_earned, commission, etc.) | Currency (Number) | No string formatting, enables sum/filter |
| All percent columns (*_rate_percent) | Number (decimal) | E.g., 15.00 for 15% |
| Blank cells for null values | (blank) | E.g., session_rate blank for monthly staff |

#### Empty Period Response (200 OK)

If the month has **no staff on payroll**:
- File is still returned (200, not 204 or 404)
- Excel sheet contains headers on row 2
- Zero data rows
- Accounting can immediately add staff to the template if needed

#### Error Responses

**401 Unauthorized**
```json
{
  "detail": "Not authenticated"
}
```
Cause: Missing or invalid Bearer token.

**403 Forbidden**
```json
{
  "detail": "You do not have permission to perform this action"
}
```
Cause: User's role lacks `payroll.manage` permission.

**422 Unprocessable Entity**
```json
{
  "detail": "Giá trị month không hợp lệ. Định dạng phải là YYYY-MM"
}
```
Cause: `month` parameter does not match `^\d{4}-(0[1-9]|1[0-2])$`.

**400 Bad Request** (rare)
```json
{
  "detail": "Invalid clinic context or other parameter error"
}
```
Cause: Missing clinic_id in middleware context or other validation failure.

**500 Internal Server Error**
```json
{
  "detail": "Lỗi hệ thống, vui lòng thử lại sau"
}
```
Cause: Database timeout, compute engine crash, or I/O error during .xlsx generation.

---

## Column Specifications

### 27 Columns in Excel Export

| # | Column Header (Vietnamese) | Source Field | Data Type | Description |
|---|---------------------------|--------------|-----------|-------------|
| 1 | Mã NV | staff_code | Text | Staff ID code (unique per clinic) |
| 2 | Họ và tên | full_name | Text | Full name |
| 3 | Loại lương | pay_type | Text | "Theo tháng" / "Theo giờ" / "Theo buổi" / "Theo ca" |
| 4 | Số công/buổi | worked_days | Number | Days worked (or sessions attended on grid) |
| 5 | Tổng giờ làm | total_hours | Number | Total hours worked (for hourly pay type) |
| 6 | Giờ tăng ca | ot_hours | Number | Overtime hours (monthly/hourly only) |
| 7 | Số ngày vắng | absent_days | Number | Unpaid absent days |
| 8 | Số ngày nghỉ phép | leave_days | Number | Approved leave days |
| 9 | Số lần đi muộn | late_count | Number | Late check-in count |
| 10 | Đơn giá buổi | session_rate | Number | Rate per session (blank if not per_session pay type) |
| 11 | Đơn giá ca | shift_rate | Number | Rate per shift (blank if not per_shift pay type) |
| 12 | Số ca hoàn thành | completed_shifts | Number | Completed shifts count |
| 13 | Lương cơ bản | base_earned | Currency | Base pay earned (calculated per pay_type) |
| 14 | Lương tăng ca | overtime_pay | Currency | Overtime pay (0 for per_session/per_shift) |
| 15 | Phụ cấp | allowance | Currency | Fixed allowance |
| 16 | Thưởng chuyên cần | attendance_bonus | Currency | Bonus if 0 absent & 0 late |
| 17 | Phạt đi muộn | late_penalty_total | Currency | Late penalty (late_count × penalty_rate) |
| 18 | Hoa hồng thủ thuật | procedure_commission | Currency | Procedure (surgery) commission |
| 19 | Tỷ lệ HH thủ thuật (%) | procedure_rate_percent | Number | **Blended rate:** (procedure_commission / procedure_revenue) × 100 |
| 20 | Nguồn tỷ lệ thủ thuật | procedure_rate_source | Text | "Riêng" (override) / "Chung" (clinic default) / blank |
| 21 | Hoa hồng thuốc | medicine_commission | Currency | Medicine commission |
| 22 | Tỷ lệ HH thuốc (%) | medicine_rate_percent | Number | **Blended rate:** (medicine_commission / medicine_revenue) × 100 |
| 23 | Nguồn tỷ lệ thuốc | medicine_rate_source | Text | "Riêng" / "Chung" / blank |
| 24 | Thưởng KPI | kpi_bonus | Currency | KPI bonus (if revenue target met) |
| 25 | Điều chỉnh/hoàn ứng | clawback_adjustment | Currency | Claw-back or other payroll adjustment (often negative) |
| 26 | Tổng thu nhập | gross_pay | Currency | **Total earnings** (before deductions) |
| 27 | Thực nhận | net_pay | Currency | **Net pay** (received by staff; v1 = gross, no BHXH/tax yet) |

### Rate Semantics (Columns 19, 22)

**Important Note for Accounting:**

Columns "Tỷ lệ HH thủ thuật (%)" and "Tỷ lệ HH thuốc (%)" are **NOT** the configured rate on staff profile. They are **derived** from the period's actual transactions:

```
Applied Rate % = (Commission Amount / Service Revenue) × 100
```

When a staff member earns commission across **multiple service types** at **different rates**, the displayed rate is a **revenue-weighted blend**, not the literal configured rate.

**Example:**
- Procedure A: Revenue 1M, Rate 15% → Commission 150K
- Procedure B: Revenue 2M, Rate 20% → Commission 400K
- Total: Revenue 3M, Commission 550K
- **Displayed Rate:** (550K / 3M) × 100 = **18.33%** (blend)

**Column 20 / 23 — "Nguồn tỷ lệ" (Rate Source):**
- **"Riêng"** = at least one contributing line used a staff-specific override rate
- **"Chung"** = all contributing lines used clinic-wide default rates
- **(blank)** = no commission earned (Commission = 0)

This semantics was **intentionally retained** (user decision, 2026-08-08) to allow accounting to reverse-check: `Commission ≈ (Rate / 100) × Revenue`. Understanding the blend is essential for correct reconciliation.

---

## Business Rules

| Rule ID | Description | Enforcement |
|---------|-------------|------------|
| BR-001 | Only `payroll.manage` role can export | 403 if role mismatch |
| BR-002 | Month must be valid YYYY-MM | 422 on pattern mismatch |
| BR-003 | Empty period returns 200 OK with header, not error | No exception thrown |
| BR-004 | Numbers (money, percent) stored as Excel numbers, not text | ORM/openpyxl handles automatically |
| BR-005 | Staff without account (user_id=NULL) included in export | Data never dropped, keyed by staff_id |
| BR-006 | File name UTF-8 encoded, supports Vietnamese characters | Content-Disposition header set correctly |
| BR-007 | Filename format: `bang_luong_YYYY-MM.xlsx` | Consistent, descriptive |

---

## Formula Injection Prevention

**Threat:** Excel cells starting with `=`, `+`, `@`, `-` can execute formulas (e.g., `=cmd|'/c calc'!A1`).

**Mitigation:** The underlying `build_xlsx_response` utility automatically:
- Detects formula-prefix characters
- Either escapes them or applies cell format `@` (text-only)
- Tested with staff names like `"=1+1"`, `"+2+2"` — cell displays literal text, not formula

No manual escaping needed in export code.

---

## Implementation Notes

### Code Paths

**Backend (FastAPI):**
```python
@router.get("/payroll/export", dependencies=[Depends(require_permission("payroll.manage"))])
async def export_payroll(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        return await payroll_service.export_payroll_xlsx(db, clinic_id=_clinic_id(), month=month)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
```

**Service Layer:**
```python
async def export_payroll_xlsx(db, clinic_id, month) -> Response:
    # Reuse compute_payroll (same engine as GET /hr/payroll)
    payroll = await compute_payroll(db, clinic_id, month)
    payslips = payroll["payslips"]
    
    # Convert payslips to Excel rows (pure function, no DB)
    rows = build_payroll_export_rows(payslips)
    
    # Build .xlsx via openpyxl/xlsxwriter
    return build_xlsx_response(
        sheet_title="Bảng lương",
        title=f"Bảng lương tháng {month}",
        headers=PAYROLL_EXPORT_HEADERS,  # 27 columns
        rows=rows,
        filename=f"bang_luong_{month}"
    )
```

**Frontend (React):**
```typescript
// ExportExcelButton on PayrollPage
useExportDownload(
  "/api/v1/payroll/export",
  { month },
  `bang_luong_${month}`
);
```

### Reuse Strategy

- **Engine:** `payroll_service.compute_payroll(...)` used verbatim
- **No duplicate computation:** Export always reflects what `GET /hr/payroll` returns
- **Formula injection safety:** `build_xlsx_response` handles escaping automatically
- **Clinic isolation:** Enforced by middleware (`current_clinic_id` context)

---

## Test Coverage

| Test Type | Scenarios | Status |
|-----------|-----------|--------|
| BE unit (payroll_export.py) | 13 tests: header/row alignment, pay-type labels, rate visibility, blank handling | ✅ Pass |
| BE integration (test_payroll_export_e2e.py) | 6 tests: RBAC (401/403), empty period (200), data match `/hr/payroll`, staff without account, cross-tenant | ✅ Pass |
| BE additional (disposable stack) | 11 scenarios: mixed staff types, real two-clinic isolation, formula injection, 9 malformed-month variants | ✅ Pass |
| FE (PayrollPage.export.test.tsx) | Export button URL/month/header, modal open/close | ✅ Pass (4 tests) |
| **Total** | 28 scenarios | ✅ **All Pass** |

See `docs/tasks/TASK-139/deliveries/test-reports/test-report.md` for full details.

---

## Deprecations / Compatibility

**None.** This is a new endpoint, no legacy code affected.

---

## Related Endpoints

- `GET /api/v1/hr/payroll?month=YYYY-MM` — Fetch payroll data (JSON response)
- `GET /api/v1/staff/export` — Export staff directory (similar pattern)
- `GET /api/v1/attendance/export?from=...&to=...` — Export attendance (similar pattern)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-08 | Initial spec: `GET /api/v1/payroll/export` with 27-column Excel export and formula injection prevention |

---

**Approval Signatures**

| Role | Approval | Date |
|------|----------|------|
| Code Review | ✅ Approved | 2026-08-08 |
| Test / QA | ✅ Passed | 2026-08-08 |
| Implementation | ✅ Complete | 2026-08-08 |
