# API Specification: Inventory Valuation Report

**Task:** TASK-083 - Cấu hình giá thuốc + báo cáo tồn kho + xem giá trị tiền tồn kho  
**Date:** 2026-07-03  
**Base URL:** `/api/v1`

---

## Overview

This specification documents the two new inventory valuation endpoints introduced in TASK-083. These endpoints provide the cost-basis inventory valuation ("tiền đang nằm trong thuốc") — the monetary value of stock on hand, calculated using actual purchase prices (batch.unit_cost) per lot, with fallback to medicine-level default cost and retail price reference.

---

## Endpoints Summary

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| GET | `/reports/inventory-valuation` | Fetch inventory valuation report as JSON | `report.financial` |
| GET | `/reports/inventory-valuation/export` | Export inventory valuation report as XLSX | `report.financial` |

---

## 1. GET /reports/inventory-valuation

### 1.1 Request

**Method:** `GET`  
**Path:** `/api/v1/reports/inventory-valuation`  
**Authentication:** Required (Bearer token in Authorization header)  
**Permission:** `report.financial`

**Query Parameters:** None

**Headers:**
```
Authorization: Bearer {token}
```

**Body:** None (GET request)

### 1.2 Processing

1. Validate authorization (401 if missing token)
2. Check permission `report.financial` (403 if lacking)
3. Extract `clinic_id` from request context (JWT claim or header)
4. Query database:
   - Join `inventory_item`, `medicine`, `batch` tables
   - Filter: clinic_id, active batches (not recalled, not expired, not deleted)
   - Aggregate per medicine: available_qty, cost_value, retail_value, has_missing_cost
   - Include only medicines with available_qty > 0 (HAVING clause)
5. Calculate report totals: total_cost_value, total_retail_value, has_any_missing_cost
6. Return JSON response (200 OK)

### 1.3 Response

**Status Code:** 200 OK

**Content-Type:** `application/json`

**Body:**
```json
{
  "clinic_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_cost_value": "1500000.50",
  "total_retail_value": "2250000.75",
  "has_any_missing_cost": false,
  "rows": [
    {
      "medicine_id": "550e8400-e29b-41d4-a716-446655440001",
      "medicine_name": "Paracetamol 500mg",
      "available_qty": "500",
      "cost_value": "1000000.00",
      "retail_value": "1500000.00",
      "has_missing_cost": false
    },
    {
      "medicine_id": "550e8400-e29b-41d4-a716-446655440002",
      "medicine_name": "Amoxicillin 250mg",
      "available_qty": "200",
      "cost_value": "500000.50",
      "retail_value": "750000.75",
      "has_missing_cost": false
    }
  ]
}
```

**Response Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `clinic_id` | UUID (string) | Clinic identifier (from request context) |
| `total_cost_value` | Decimal (string) | Total cost basis of all stock on hand (vốn tồn tổng). This is the "tiền đang nằm trong thuốc" primary figure. Calculated as SUM of cost_value across all rows. |
| `total_retail_value` | Decimal (string) \| null | Total retail reference value (tổng giá trị bán lẻ) if all medicines have sale_price configured. `null` if any medicine lacks sale_price. Reference only — never included in cost_value total. |
| `has_any_missing_cost` | Boolean | Flag: true if any medicine row has has_missing_cost=true. Warns user that some batches are missing cost data, so total_cost_value may understate true capital tied up in stock. |
| `rows` | Array[InventoryValuationRow] | Per-medicine valuation details (see below). Empty array if clinic has no stock on hand. |

**InventoryValuationRow:**

| Field | Type | Description |
|-------|------|-------------|
| `medicine_id` | UUID (string) | Medicine identifier |
| `medicine_name` | String | Medicine name (from medicine catalog) |
| `available_qty` | Decimal (string) | Total available quantity = SUM(batch.actual_quantity - batch.reserved_quantity) across active, non-expired, non-recalled batches. |
| `cost_value` | Decimal (string) | Cost basis of this medicine's stock = SUM(available_qty_per_batch × effective_unit_cost). Effective unit cost = COALESCE(batch.unit_cost, medicine.default_cost_price, 0). |
| `retail_value` | Decimal (string) \| null | Retail reference value = available_qty × medicine.sale_price. `null` if medicine.sale_price is not configured. Reference only. |
| `has_missing_cost` | Boolean | Flag: true if any batch on hand (qty > 0) is missing both batch.unit_cost AND medicine.default_cost_price. Indicates that portion of cost_value may be inaccurate (valued at 0). |

### 1.4 Error Responses

| Status | Code | Message | Cause |
|--------|------|---------|-------|
| 400 | `INVALID_REQUEST` | "Invalid request" | Malformed query parameters (rare for this endpoint) |
| 401 | `UNAUTHORIZED` | "Authentication required" | Missing or invalid Bearer token |
| 403 | `FORBIDDEN` | "Insufficient permissions" | User lacks `report.financial` permission |
| 500 | `INTERNAL_ERROR` | "Internal server error" | Database or system error |

**Example Error Response (403):**
```json
{
  "code": "FORBIDDEN",
  "message": "You do not have permission to access this resource"
}
```

### 1.5 Example Scenarios

#### Scenario A: Normal case with all cost data
```
Request: GET /api/v1/reports/inventory-valuation
Response (200):
{
  "clinic_id": "clinic-uuid",
  "total_cost_value": "5000000.00",
  "total_retail_value": "8000000.00",
  "has_any_missing_cost": false,
  "rows": [
    {
      "medicine_id": "med-1",
      "medicine_name": "Medicine A",
      "available_qty": "500",
      "cost_value": "2500000.00",
      "retail_value": "4000000.00",
      "has_missing_cost": false
    },
    {
      "medicine_id": "med-2",
      "medicine_name": "Medicine B",
      "available_qty": "300",
      "cost_value": "2500000.00",
      "retail_value": "4000000.00",
      "has_missing_cost": false
    }
  ]
}
```

#### Scenario B: Medicine missing cost (fallback to default_cost_price)
```
Medicine "C" has 1 batch with qty=100, unit_cost=NULL, medicine.default_cost_price=30000
Result row:
{
  "medicine_id": "med-3",
  "medicine_name": "Medicine C",
  "available_qty": "100",
  "cost_value": "3000000.00",
  "retail_value": null,
  "has_missing_cost": false
}
```

#### Scenario C: Missing all cost data (cảnh báo)
```
Medicine "D" has 1 batch with qty=100, unit_cost=NULL, medicine.default_cost_price=NULL
Result row:
{
  "medicine_id": "med-4",
  "medicine_name": "Medicine D",
  "available_qty": "100",
  "cost_value": "0.00",
  "retail_value": null,
  "has_missing_cost": true
}

Response header: has_any_missing_cost = true (warns user)
```

---

## 2. GET /reports/inventory-valuation/export

### 2.1 Request

**Method:** `GET`  
**Path:** `/api/v1/reports/inventory-valuation/export`  
**Authentication:** Required (Bearer token)  
**Permission:** `report.financial`

**Query Parameters:** None

**Headers:**
```
Authorization: Bearer {token}
```

**Body:** None

### 2.2 Processing

1. Validate authorization and permission (same as endpoint 1)
2. Call `get_inventory_valuation()` to fetch report data
3. Transform rows to XLSX format:
   - Each row = [medicine_id, medicine_name, available_qty, cost_value, retail_value or "", has_missing_cost label]
   - Stringify all Decimal values
   - Neutralize all cells against formula-injection (prepend apostrophe to `=`, `+`, `-`, `@`, tab, carriage return)
4. Build XLSX file using `build_xlsx_response()` helper:
   - Sheet name: "Giá trị tồn kho"
   - Headers: ["Mã thuốc", "Tên thuốc", "Số lượng tồn", "Giá trị vốn", "Giá trị bán lẻ", "Thiếu giá vốn"]
   - Filename: "gia_tri_ton_kho.xlsx"
5. Return file as streaming response (200 OK)

### 2.3 Response

**Status Code:** 200 OK

**Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

**Headers:**
```
Content-Disposition: attachment; filename="gia_tri_ton_kho.xlsx"
```

**Body:** Binary XLSX file (streaming)

**XLSX Structure:**

| Sheet Name | Giá trị tồn kho |
|------------|-----------------|

**Column Headers (Row 1):**
| Mã thuốc | Tên thuốc | Số lượng tồn | Giá trị vốn | Giá trị bán lẻ | Thiếu giá vốn |

**Data Rows (2+):**
| String (medicine_id) | String (name) | String (qty) | String (cost_value) | String (retail_value or blank) | String ("Có" or "Không") |

**Example XLSX Content:**
```
Mã thuốc          | Tên thuốc           | Số lượng tồn | Giá trị vốn  | Giá trị bán lẻ | Thiếu giá vốn
uuid-1            | Paracetamol 500mg   | 500          | 1000000.00   | 1500000.00     | Không
uuid-2            | Amoxicillin 250mg   | 200          | 500000.50    | 750000.75      | Không
```

### 2.4 Formula-Injection Prevention

All cell values are sanitized before writing to Excel:
- If a cell value starts with `=`, `+`, `-`, `@`, or control characters (tab, carriage return), a leading apostrophe (`'`) is prepended
- Example: Medicine name `=SUM(A1:A10)` becomes `'=SUM(A1:A10)` in the cell
- This renders the cell as plain text, preventing formula execution

**Implementation:** Uses the `app/core/excel.py::_neutralize()` helper function, which is already used by other export endpoints (e.g., revenue report).

### 2.5 Error Responses

Same as endpoint 1:

| Status | Code | Message | Cause |
|--------|------|---------|-------|
| 400 | `INVALID_REQUEST` | "Invalid request" | Malformed query parameters |
| 401 | `UNAUTHORIZED` | "Authentication required" | Missing or invalid token |
| 403 | `FORBIDDEN` | "Insufficient permissions" | User lacks `report.financial` permission |
| 500 | `INTERNAL_ERROR` | "Internal server error" | Database or system error (e.g., cannot generate XLSX) |

**Example (403):**
```
Status: 403 Forbidden
Content-Type: application/json

{
  "code": "FORBIDDEN",
  "message": "You do not have permission to access this resource"
}
```

### 2.6 Example Scenarios

#### Scenario A: Successful export
```
Request: GET /api/v1/reports/inventory-valuation/export
Response:
  Status: 200 OK
  Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  Content-Disposition: attachment; filename="gia_tri_ton_kho.xlsx"
  Body: [binary XLSX data]
```

#### Scenario B: Export with injection-safe data
```
Clinic has medicine named: =CONCAT("Hack","attempt")
XLSX cell value written: '=CONCAT("Hack","attempt")
  (apostrophe prevents formula eval, displays as plain text in Excel)
```

#### Scenario C: Insufficient permission
```
Request: GET /api/v1/reports/inventory-valuation/export
  (User has role="nurse", which has report.view but NOT report.financial)
Response (403):
{
  "code": "FORBIDDEN",
  "message": "You do not have permission to access this resource"
}
```

---

## 3. Related Endpoints (Reference)

### 3.1 Update Medicine Price

**Method:** `PUT` / `PATCH`  
**Path:** `/api/v1/medicines/{id}`  
**New Fields:** `sale_price`, `default_cost_price` (added by TASK-083)  
**Permission:** `medicine.manage`

**Request Body Example:**
```json
{
  "sale_price": "50000.00",
  "default_cost_price": "35000.00"
}
```

**Notes:**
- Both fields are optional (can be `null`)
- Must be ≥ 0 if provided
- `sale_price` is the clinic-configured retail price; used for "retail value" reference in valuation report
- `default_cost_price` is optional fallback for batches missing `unit_cost`
- This endpoint already existed (TASK-011); TASK-083 only adds the 2 new fields

---

## 4. Data Types & Constraints

### 4.1 Numeric Fields (Currency)

All monetary values use SQL type `Numeric(15,2)`:
- Maximum 15 digits total, 2 decimal places
- Example: `1234567890123.45` (valid), `12345678901234.56` (invalid — too many digits)
- JSON representation: string (to preserve precision, avoid float drift)

### 4.2 Quantity Fields

Quantities are `Numeric` (no explicit scale limitation in typical cases):
- Example: `500`, `1000.5` (if using sub-unit quantities)
- JSON representation: string (to preserve precision)

### 4.3 UUID Fields

Standard UUID v4 format as string:
- Example: `550e8400-e29b-41d4-a716-446655440000`

### 4.4 Date Handling

Expiry date and filtering use `DATE` type:
- Format: ISO 8601 (YYYY-MM-DD)
- Filtering: `batch.expiry_date >= today` (non-expired) — as of 00:00:00 same day
- Current date determined by `date.today()` in Python or `CURDATE()` in SQL

---

## 5. Permission Matrix

| Endpoint | Permission | Role Example | Access |
|----------|-----------|--------------|--------|
| GET `/reports/inventory-valuation` | `report.financial` | Manager, Accountant | ✅ |
| GET `/reports/inventory-valuation/export` | `report.financial` | Manager, Accountant | ✅ |
| GET `/reports/inventory-valuation` | `report.view` | Nurse, Pharmacist | ❌ (403) |
| GET `/reports/inventory-status` | `report.view` | Nurse, Pharmacist | ✅ |
| PUT `/medicines/{id}` (price fields) | `medicine.manage` | Pharmacy Manager | ✅ |

---

## 6. Multi-Tenancy / RLS

All endpoints filter by `clinic_id`:
- Extracted from request context (JWT claim `clinic_id` or header)
- Applied in SQL WHERE clause: `inventory_item.clinic_id = :clinic_id`
- Result: Clinic A never sees Clinic B's medicines, stock, or valuations

**Example:**
- Clinic A GETs `/reports/inventory-valuation` → sees only Clinic A's stock
- Clinic B GETs same endpoint → sees only Clinic B's stock

---

## 7. Backward Compatibility

- No breaking changes to existing endpoints
- `GET /reports/inventory-status` (existing) uses `report.view` permission — unchanged
- Medicine CRUD (`POST/PUT/PATCH /medicines`) adds 2 optional fields — backward compatible
- Clients that don't populate `sale_price`/`default_cost_price` continue working; new fields default to `null`

---

## 8. Rate Limiting & Caching

- No explicit rate limiting defined for this endpoint
- No caching strategy (data fetched fresh on each request)
- Consider caching at client level if valuation is fetched frequently and data changes infrequently

---

## 9. Testing Notes

### 9.1 Unit & Integration Tests

Backend tests in `tests/integration/reports/test_inventory_valuation_e2e.py`:
- ✅ Cost-basis math validation (qty × unit_cost)
- ✅ Missing cost fallback (unit_cost → default_cost_price → 0)
- ✅ Batch filtering (active/non-expired/non-recalled)
- ✅ Retail value calculation (qty × sale_price, separate from cost)
- ✅ Excel export + formula-injection neutralization
- ✅ Permission gate (403 without report.financial)
- ✅ Tenant isolation (clinic A ≠ clinic B)

All tests passed: **16/16** (incl. 3 additional closure tests for permission, dispense decrease, formula-injection verification)

### 9.2 Test Data Setup

```python
# 1. Create clinic
clinic = Clinic(name="Test Clinic", ...)

# 2. Create user with report.financial permission
user = User(email="test@example.com", permissions=["report.financial"], clinic_id=clinic.id)

# 3. Create medicine
medicine = Medicine(name="Paracetamol 500mg", sale_price=50000, default_cost_price=35000)

# 4. Create inventory item
item = InventoryItem(medicine_id=medicine.id, clinic_id=clinic.id)

# 5. Create batch
batch = Batch(inventory_item_id=item.id, unit_cost=40000, actual_quantity=100, reserved_quantity=0, expiry_date=date.today()+timedelta(days=30), is_recalled=False)

# 6. Request report
GET /api/v1/reports/inventory-valuation
  (as user)
Expected: cost_value = 100 * 40000 = 4000000
```

### 9.3 Edge Cases to Test

- Empty stock (no batches on hand) → report with empty `rows` array
- All medicines lack sale_price → `total_retail_value` = `null`
- Batch missing both unit_cost and default_cost_price → cost_value includes 0, has_missing_cost = true
- Export with medicine names containing `=`, `+`, `-`, `@` → apostrophe prepended in XLSX

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-03 | Initial specification — inventory valuation endpoints (TASK-083) |
