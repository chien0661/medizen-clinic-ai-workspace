# API Specs — Inventory Stocktake & Batch Dispose (TASK-064)

**Task:** TASK-064  
**Module:** `app/modules/inventory/`  
**Date:** 2026-05-31  
**Status:** Completed — PASSED testing (13/13 BE integration tests)

---

## Overview

Three new endpoints for **stocktake** (physical inventory count) and **batch disposal** (write-off expired stock):

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/inventory/stocktake` | GET | Retrieve current system stock snapshot for physical comparison |
| `/api/v1/inventory/stocktake` | POST | Submit physical count results; create adjustment movements |
| `/api/v1/inventory/batches/dispose` | POST | Mark expired batches as disposed (zero qty, soft-delete) |

**Authentication:** All endpoints require `Authorization: Bearer {token}` + `inventory.adjust` permission  
**Tenant Isolation:** All endpoints enforce clinic-level RLS (`clinic_id` from JWT)  
**Audit Trail:** All operations logged via `StockMovement` records (`__auditable__ = True`)

---

## 1. GET /api/v1/inventory/stocktake

### Purpose

Returns a **snapshot** of expected inventory quantities per item for the current clinic.
Aggregates `actual_quantity` across all **active** (non-deleted, non-recalled) batches.
Pharmacist uses this to initialize their physical count form.

### Request

```http
GET /api/v1/inventory/stocktake
Authorization: Bearer {token}
```

**Query Parameters:** None

**Request Body:** None

### Response — Success (HTTP 200)

```json
{
  "items": [
    {
      "inventory_item_id": "550e8400-e29b-41d4-a716-446655440000",
      "medicine_name": "Natri Clorid",
      "medicine_code": "NaCl-0.9",
      "base_unit": "Lọ 100ml",
      "expected_quantity": 450.00
    },
    {
      "inventory_item_id": "550e8400-e29b-41d4-a716-446655440001",
      "medicine_name": "Clopidogrel",
      "medicine_code": "PLT-75",
      "base_unit": "Hộp 10 viên",
      "expected_quantity": 120.00
    }
  ],
  "generated_at": "2026-05-31T14:30:45.123456Z"
}
```

**Field Descriptions:**

| Field | Type | Meaning |
|---|---|---|
| `items[]` | Array | List of inventory items with expected quantities |
| `items[].inventory_item_id` | UUID | Unique ID of the inventory item |
| `items[].medicine_name` | String | Medicine name (e.g., "Natri Clorid") |
| `items[].medicine_code` | String | Internal medicine code |
| `items[].base_unit` | String | Unit of measurement (e.g., "Hộp 10 viên") |
| `items[].expected_quantity` | Decimal | SUM of `actual_quantity` across active batches for this item |
| `generated_at` | ISO 8601 timestamp | Moment snapshot was generated (UTC) |

### Response — Error Cases

| HTTP | Reason | Response |
|---|---|---|
| 401 | No bearer token or invalid token | `{ "detail": "Not authenticated" }` |
| 403 | Token valid but user lacks `inventory.adjust` permission | `{ "detail": "Insufficient permissions" }` |

---

## 2. POST /api/v1/inventory/stocktake

### Purpose

Submits the **physical count results** (actual quantities per item) after the pharmacist
has manually counted the medication in stock.

System processes:
1. **Compares** expected (from GET snapshot) vs. actual (submitted) quantities.
2. **Creates adjustment movements** on batches to reconcile the variance (FEFO ordering).
3. **Returns** per-item variance summary and list of created movement IDs.

**Variance Distribution Logic (FEFO — First-Expiry-First-Out):**
- **Shortage** (actual < expected): Deduct from **earliest expiry** batches first (minimize risk of expiring stock).
- **Surplus** (actual > expected): Add to **latest expiry** batch (least immediate risk).

### Request

```http
POST /api/v1/inventory/stocktake
Authorization: Bearer {token}
Content-Type: application/json

{
  "items": [
    {
      "inventory_item_id": "550e8400-e29b-41d4-a716-446655440000",
      "actual_quantity": 450.00
    },
    {
      "inventory_item_id": "550e8400-e29b-41d4-a716-446655440001",
      "actual_quantity": 125.00
    }
  ],
  "notes": "Optional notes about the count session"
}
```

**Field Descriptions:**

| Field | Type | Required | Constraints | Meaning |
|---|---|---|---|---|
| `items` | Array | Yes | min 1 item | List of counted items |
| `items[].inventory_item_id` | UUID | Yes | Must exist in DB | The inventory item being counted |
| `items[].actual_quantity` | Decimal | Yes | >= 0 | Physical count result |
| `notes` | String | No | Max 500 chars | Free-text notes (e.g., reason for large variance) |

### Response — Success (HTTP 200)

```json
{
  "adjusted_count": 1,
  "results": [
    {
      "inventory_item_id": "550e8400-e29b-41d4-a716-446655440000",
      "expected_quantity": 450.00,
      "actual_quantity": 450.00,
      "variance": 0.00,
      "movement_ids": []
    },
    {
      "inventory_item_id": "550e8400-e29b-41d4-a716-446655440001",
      "expected_quantity": 120.00,
      "actual_quantity": 125.00,
      "variance": 5.00,
      "movement_ids": ["760e8400-e29b-41d4-a716-446655440002"]
    }
  ]
}
```

**Field Descriptions:**

| Field | Type | Meaning |
|---|---|---|
| `adjusted_count` | Integer | Number of items with non-zero variance (had movements created) |
| `results[]` | Array | Per-item reconciliation summary |
| `results[].inventory_item_id` | UUID | The item that was counted |
| `results[].expected_quantity` | Decimal | System expected qty at time of submission |
| `results[].actual_quantity` | Decimal | Pharmacist's physical count result |
| `results[].variance` | Decimal | `actual - expected` (positive = surplus, negative = shortage) |
| `results[].movement_ids[]` | Array of UUID | IDs of `StockMovement` records created to reconcile variance |

### Response — Error Cases

| HTTP | Reason | Response |
|---|---|---|
| 400 | Request body invalid (e.g., empty `items` array, negative qty) | `{ "detail": "Validation error: [specific issue]" }` |
| 401 | No bearer token or invalid token | `{ "detail": "Not authenticated" }` |
| 403 | User lacks `inventory.adjust` permission | `{ "detail": "Insufficient permissions" }` |

---

## 3. POST /api/v1/inventory/batches/dispose

### Purpose

Marks one or more **expired/damaged batches as disposed** (write-off).

System processes:
1. **Validates** each batch exists + belongs to this clinic.
2. **Checks** `reserved_quantity == 0` (cannot dispose if units are reserved for prescriptions).
3. **Creates** expiry write-off `StockMovement` record (quantity_delta = negative of actual qty).
4. **Zeroes** batch `actual_quantity` and **soft-deletes** the batch.

### Request

```http
POST /api/v1/inventory/batches/dispose
Authorization: Bearer {token}
Content-Type: application/json

{
  "batch_ids": [
    "660e8400-e29b-41d4-a716-446655440003",
    "660e8400-e29b-41d4-a716-446655440004"
  ],
  "reason": "expired"
}
```

**Field Descriptions:**

| Field | Type | Required | Constraints | Meaning |
|---|---|---|---|---|
| `batch_ids` | Array of UUID | Yes | min 1 ID | Batch IDs to dispose |
| `reason` | String | No | min 1 char, default: `"expired"` | Reason for disposal (e.g., "expired", "damaged", "recall") |

### Response — Success (HTTP 200)

```json
{
  "disposed_count": 2,
  "results": [
    {
      "batch_id": "660e8400-e29b-41d4-a716-446655440003",
      "quantity_written_off": 50.00,
      "movement_id": "770e8400-e29b-41d4-a716-446655440005"
    },
    {
      "batch_id": "660e8400-e29b-41d4-a716-446655440004",
      "quantity_written_off": 30.00,
      "movement_id": "770e8400-e29b-41d4-a716-446655440006"
    }
  ]
}
```

**Field Descriptions:**

| Field | Type | Meaning |
|---|---|---|
| `disposed_count` | Integer | Number of batches successfully disposed |
| `results[]` | Array | Per-batch disposal summary |
| `results[].batch_id` | UUID | The batch that was disposed |
| `results[].quantity_written_off` | Decimal | Quantity zeroed (original `actual_quantity`) |
| `results[].movement_id` | UUID | ID of `StockMovement` record created for the write-off |

### Response — Error Cases

| HTTP | Code | Reason | Response |
|---|---|---|---|
| 400 | `BUSINESS_RULE_VIOLATION` | Batch has `reserved_quantity > 0` (units reserved for prescriptions) | `{ "detail": "Cannot dispose batch [ID]: X units still reserved" }` |
| 400 | `INVALID_REQUEST` | Empty `batch_ids` array or invalid reason | `{ "detail": "Validation error: [specific issue]" }` |
| 401 | — | No bearer token or invalid token | `{ "detail": "Not authenticated" }` |
| 403 | — | User lacks `inventory.adjust` permission | `{ "detail": "Insufficient permissions" }` |
| 404 | `NOT_FOUND` | Batch does not exist, already deleted, or belongs to different clinic | `{ "detail": "Batch [ID] not found or already deleted" }` |

---

## Permission Requirements

All three endpoints require the user to hold the **`inventory.adjust`** permission.

**Permission Check Flow:**
1. Backend validates JWT token is present and valid (401 if not).
2. Backend checks permission gate via `require_permission("inventory.adjust")` (403 if missing).
3. Backend extracts `clinic_id` from JWT claims → enforces clinic-level RLS.

**Who has this permission?**
- Pharmacy Manager (`role = "pharmacy_manager"`)
- System Administrator (`role = "admin"`)

---

## Audit Trail

All stock adjustments are recorded in the **`stock_movement`** table:

| Field | Value |
|---|---|
| `movement_type` | `"adjustment"` (stocktake) or `"expiry_writeoff"` (dispose) |
| `quantity_delta` | Signed change in batch stock |
| `reference_type` | `"stocktake"` or `"batch_dispose"` |
| `reason` | User-provided notes or disposal reason |
| `performed_by` | UUID of user who performed the action |
| `created_at` | Server timestamp (UTC) |

These records are immutable and serve as the **audit trail** for compliance.

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Pharmacist clicks "Bắt đầu kiểm kê" (Start Stocktake)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  GET /inventory/stocktake    │
        │  (Chuẩn bị — Step 1)         │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────────────────────────────┐
        │ Pharmacist reviews items + expected qty             │
        │ Enters actual counts for each item (Đếm — Step 2)   │
        └──────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────▼───────────────────────────────────────┐
        │ Review variance (Đối chiếu — Step 3)                 │
        │ Click "Xác nhận & Lưu kiểm kê" (Confirm & Save)      │
        └──────────────┬───────────────────────────────────────┘
                       │
        ┌──────────────▼──────────────────────────────────────┐
        │ POST /inventory/stocktake                            │
        │   { items: [{id, actual_qty}, ...], notes? }        │
        │ ✓ Creates StockMovement records for variances       │
        │ ✓ Adjusts batch actual_quantity via FEFO logic      │
        │ ✓ Returns { adjusted_count, results[] }             │
        └──────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────▼──────────────────────────────────────┐
        │ Success: Toast "Lưu kiểm kê thành công"             │
        │ Failure: Toast error detail + retry option          │
        └──────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────┐
│ Pharmacist clicks "Xử lý hết hạn" (Expiry Processing)    │
└─────────────────────┬────────────────────────────────────┘
                      │
        ┌─────────────▼──────────────┐
        │ GET /inventory/batches     │
        │ (with near_expiry=true)    │
        │ Lists batches expiring     │
        │ within 90 days             │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────────────────────────────┐
        │ Pharmacist selects batches to dispose               │
        │ (marked as expired, damaged, or recalled)           │
        └─────────────┬──────────────────────────────────────┘
                      │
        ┌─────────────▼──────────────────────────────────────┐
        │ POST /inventory/batches/dispose                     │
        │   { batch_ids: [id1, id2, ...], reason: "expired" } │
        │ ✓ Validates reserved_qty == 0 (BR violation → 400) │
        │ ✓ Creates expiry_writeoff StockMovement             │
        │ ✓ Zeroes actual_qty, soft-deletes batch             │
        │ ✓ Returns { disposed_count, results[] }             │
        └─────────────┬──────────────────────────────────────┘
                      │
        ┌─────────────▼──────────────────────────────────────┐
        │ Success: Toast "Xử lý lô hàng thành công"           │
        │ Failure: Toast error detail + retry option          │
        └──────────────────────────────────────────────────────┘
```

---

## Related Documentation

- **Functional Design:** `docs/tasks/TASK-064/deliveries/final-specs/inventory-stocktake-functional-design.md`
- **Test Report:** `docs/tasks/TASK-064/deliveries/test-reports/test-report.md`
- **Integration Tests:** `tests/integration/inventory/test_stocktake_dispose.py`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-31 | Initial API specs (TASK-064 delivery) |

