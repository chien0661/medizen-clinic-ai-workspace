# TASK-012: Inventory + Pharmacy API Specification

**Base**: `/api/v1`  
**Auth**: Bearer JWT required for all endpoints  
**Tenant**: `X-Clinic-Code` header or JWT claim sets RLS context  

---

## Inventory Module

### Medicine Catalog

#### `GET /medicines`
- Permission: `medicine.read`
- Query: `?is_active=true|false`
- Response: `list[MedicineResponse]`

#### `POST /medicines`
- Permission: `medicine.manage`
- Body: `MedicineCreate`
- Response: `MedicineResponse` (201)
- Errors: 409 if code already exists

#### `GET /medicines/{medicine_id}`
- Permission: `medicine.read`
- Response: `MedicineResponse`
- Errors: 404 if not found

#### `PATCH /medicines/{medicine_id}`
- Permission: `medicine.manage`
- Body: `MedicineUpdate` (partial)
- Response: `MedicineResponse`

#### `DELETE /medicines/{medicine_id}`
- Permission: `medicine.manage`
- Response: 204 No Content (soft delete)

---

### Suppliers

#### `GET /inventory/suppliers`
- Permission: `inventory.read`
- Response: `list[SupplierResponse]`

#### `POST /inventory/suppliers`
- Permission: `inventory.manage_catalog`
- Body: `SupplierCreate`
- Response: `SupplierResponse` (201)

#### `PATCH /inventory/suppliers/{supplier_id}`
- Permission: `inventory.manage_catalog`
- Body: `SupplierUpdate`
- Response: `SupplierResponse`

#### `DELETE /inventory/suppliers/{supplier_id}`
- Permission: `inventory.manage_catalog`
- Response: 204 No Content

---

### Inventory Items

#### `GET /inventory/items`
- Permission: `inventory.read`
- Response: `list[InventoryItemResponse]`

#### `POST /inventory/items`
- Permission: `inventory.manage_catalog`
- Body: `InventoryItemCreate`
- Response: `InventoryItemResponse` (201)
- Errors: 409 if duplicate (clinic, medicine)

#### `PATCH /inventory/items/{item_id}`
- Permission: `inventory.manage_catalog`
- Body: `InventoryItemUpdate` (location, reorder_min, reorder_max)
- Response: `InventoryItemResponse`

#### `DELETE /inventory/items/{item_id}`
- Permission: `inventory.manage_catalog`
- Response: 204 No Content

---

### Batches

#### `GET /inventory/batches`
- Permission: `inventory.read`
- Query: `?inventory_item_id=<uuid>&include_recalled=false&include_expired=false`
- Response: `list[BatchResponse]`

#### `POST /inventory/batches`
- Permission: `inventory.manage_catalog`
- Body: `BatchCreate`
- Response: `BatchResponse` (201)

#### `PATCH /inventory/batches/{batch_id}`
- Permission: `inventory.manage_catalog`
- Body: `BatchUpdate` (unit_cost, is_recalled, recalled_reason)
- Response: `BatchResponse`

#### `DELETE /inventory/batches/{batch_id}`
- Permission: `inventory.manage_catalog`
- Response: 204 No Content

---

### Purchase-In

#### `POST /inventory/purchase-in`
- Permission: `inventory.purchase_in`
- Body:
  ```json
  {
    "inventory_item_id": "uuid",
    "supplier_id": "uuid|null",
    "batches": [
      {
        "batch_code": "string",
        "expiry_date": "YYYY-MM-DD",
        "quantity": 500,
        "pack_quantity": 5,
        "unit_cost": 12.50
      }
    ],
    "reason": "string|null"
  }
  ```
  Note: `pack_quantity` × `medicine.pack_size` = `actual_quantity` (multi-unit support)
- Response: `PurchaseInResponse` (201)
  ```json
  {
    "created_batches": [BatchResponse],
    "movement_ids": ["uuid"]
  }
  ```

---

### Stock Adjustments

#### `POST /inventory/adjustments`
- Permission: `inventory.adjust`
- Body:
  ```json
  {
    "batch_id": "uuid",
    "new_actual_quantity": 450,
    "reason": "Inventory count 2026-04-27"
  }
  ```
- Response: `StockAdjustmentResponse`
  ```json
  {
    "batch_id": "uuid",
    "quantity_before": 500,
    "quantity_after": 450,
    "movement_id": "uuid"
  }
  ```
- Errors: 400 if `new_actual_quantity < reserved_quantity`

---

### Stock Status

#### `GET /inventory/stock-status`
- Permission: `inventory.read`
- Response: `list[InventoryStatusResponse]` (from `v_inventory_status` view)
  ```json
  [
    {
      "inventory_item_id": "uuid",
      "medicine_name": "Paracetamol 500mg",
      "medicine_code": "PARA001",
      "base_unit": "tablet",
      "total_qty": 230,
      "total_reserved": 50,
      "available_qty": 180,
      "earliest_expiry": "2026-06-15",
      "expiring_soon": 1
    }
  ]
  ```

---

## Pharmacy Module

### Reserve Stock

#### `POST /pharmacy/reserve`
- Permission: `pharmacy.dispense`
- Body:
  ```json
  {
    "medicine_id": "uuid",
    "prescription_item_id": "uuid",
    "quantity": 100
  }
  ```
- Response (201):
  ```json
  {
    "prescription_item_id": "uuid",
    "reservations": [
      {
        "id": "uuid",
        "batch_id": "uuid",
        "reserved_quantity": "50",
        "status": "reserved"
      }
    ]
  }
  ```
- Errors: 409 InsufficientStockError if not enough stock

---

### Release Reservation

#### `POST /pharmacy/release/{prescription_item_id}`
- Permission: `pharmacy.dispense`
- Response (200):
  ```json
  {"released": 2}
  ```

---

### Dispense Prescription

#### `POST /pharmacy/dispense/{prescription_id}`
- Permission: `pharmacy.dispense`
- Response (200):
  ```json
  {
    "prescription_id": "uuid",
    "movements": [
      {
        "movement_id": "uuid",
        "batch_id": "uuid",
        "quantity_delta": "-40",
        "quantity_before": "100",
        "quantity_after": "60"
      }
    ]
  }
  ```

---

### Substitute Batch

#### `POST /pharmacy/substitute-batch`
- Permission: `pharmacy.substitute_batch`
- Body:
  ```json
  {
    "prescription_item_batch_id": "uuid",
    "new_batch_id": "uuid"
  }
  ```
- Response (200):
  ```json
  {
    "prescription_item_batch_id": "uuid",
    "new_batch_id": "uuid",
    "status": "reserved"
  }
  ```
- Errors: 409 if new batch has insufficient stock

---

### Pending Dispense

#### `GET /pharmacy/pending-dispense`
- Permission: `pharmacy.dispense`
- Response (200): `list[dict]`
  ```json
  [
    {
      "prescription_item_id": "uuid",
      "reserved_at": "2026-04-27T10:00:00+00:00",
      "batch_ids": ["uuid1", "uuid2"],
      "total_reserved": 100.0
    }
  ]
  ```
