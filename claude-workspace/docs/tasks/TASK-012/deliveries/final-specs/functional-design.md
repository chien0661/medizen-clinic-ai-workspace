# TASK-012: Inventory + Batch + StockMovement + FEFO + Pharmacy Dispense
## Functional Design

**Status**: DONE  
**Branch**: feature/task-012-inventory  
**Date**: 2026-04-27

---

## 1. Domain Model

### Three-Level Inventory Hierarchy

```
Medicine (catalog per clinic)
  └── InventoryItem (one per clinic per medicine)
        └── Batch (specific lot/lô hàng, with expiry date)
              └── StockMovement (append-only audit trail)
              └── PrescriptionItemBatch (reservation mapping)
```

### Tables

| Table | Description |
|-------|-------------|
| `medicine` | Catalog of medicines per clinic. `code` unique per clinic. `pack_size` = base_units per package. `is_in_house` = dispensed in-clinic vs external only. |
| `supplier` | Supplier catalog per clinic. |
| `inventory_item` | Links medicine to clinic's physical stock. One per (clinic, medicine). Has reorder_min/reorder_max. |
| `batch` | Specific stock lot with expiry date, quantities, and supplier. Enforces `reserved_quantity <= actual_quantity` via CHECK constraint. |
| `stock_movement` | Append-only audit trail. UPDATE/DELETE blocked by DB trigger `trg_stock_movement_immutable`. |
| `prescription_item_batch` | FEFO reservation mapping: links prescription_item → batch. Status: reserved → dispensed/released. |

### View

`v_inventory_status`: Aggregated per inventory_item showing total_qty, reserved, available, earliest_expiry, expiring_soon (within 30 days).

---

## 2. FEFO Algorithm

**First Expired, First Out**: batches selected in ORDER BY expiry_date ASC, received_date ASC (tiebreaker).

### Reservation Flow

1. Find `InventoryItem` for (clinic, medicine).
2. `SELECT batch FOR UPDATE NOWAIT` — fail immediately if concurrent lock.
3. Filter: `is_deleted=false, is_recalled=false, expiry_date > today`.
4. Distribute quantity across batches from earliest expiry.
5. Create `PrescriptionItemBatch` rows for each allocation.
6. Raise `InsufficientStockError` (HTTP 409) if stock insufficient.

### Concurrent Safety

- `FOR UPDATE NOWAIT`: second concurrent transaction fails immediately → caller gets 409 Conflict.
- `CHECK constraint ck_batch_reserved_lte_actual`: database-level guard.
- No over-reservation possible even under race conditions.

---

## 3. Dispense Flow

```
reserve_for_prescription()     → creates PrescriptionItemBatch (status=reserved)
dispense(prescription_id)      → deducts batch.actual_quantity + reserved_quantity
                                 → creates StockMovement (type=prescription_out)
                                 → marks PrescriptionItemBatch status=dispensed
```

**Stub**: `prescription_item.in_house_status` update deferred to TASK-011 (prescription_item table not yet implemented).

---

## 4. Permissions

| Permission | Description |
|------------|-------------|
| `medicine.read` | View medicine catalog |
| `medicine.manage` | Create/update/delete medicine catalog |
| `inventory.read` | View inventory items and stock |
| `inventory.manage_catalog` | Manage items, suppliers, batches |
| `inventory.purchase_in` | Receive purchase orders |
| `inventory.adjust` | Manual stock adjustments |
| `pharmacy.dispense` | Reserve and dispense medications |
| `pharmacy.substitute_batch` | Swap batch for a reservation |

### Role Assignments

| Role | Permissions |
|------|-------------|
| admin | All above |
| doctor | medicine.read, inventory.read |
| pharmacist | All above |
| nurse | medicine.read, inventory.read |
| receptionist | medicine.read |

---

## 5. Business Rules

- `medicine.code` must be unique per clinic (partial unique index on `is_deleted=false`).
- One `inventory_item` per (clinic, medicine) pair.
- `batch.reserved_quantity <= batch.actual_quantity` (DB CHECK constraint).
- Stock movements are immutable: `fn_stock_movement_immutable` trigger blocks UPDATE and DELETE.
- Expired batches (expiry_date < today) are excluded from FEFO allocation.
- Recalled batches (`is_recalled=true`) are excluded from FEFO allocation.
- Manual adjustments must include a reason string (min_length=1).
- Purchase-in with `pack_quantity` computes: `actual_quantity = pack_quantity × medicine.pack_size`.
- Tenant isolation enforced via RLS on all 6 tables.
