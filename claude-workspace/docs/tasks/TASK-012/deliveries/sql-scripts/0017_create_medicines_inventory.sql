-- TASK-012: Migration 0017 Summary
-- Full migration source: clinic-cms-task012/alembic/versions/0017_create_medicines_inventory.py

-- Tables created:
--   medicine        (catalog per clinic)
--   supplier        (per-clinic supplier catalog)
--   inventory_item  (one per clinic+medicine)
--   batch           (stock lot with FEFO expiry)
--   stock_movement  (append-only audit trail)
--   prescription_item_batch (reservation mapping)

-- Key constraints:
--   ck_batch_actual_qty_non_negative    batch.actual_quantity >= 0
--   ck_batch_reserved_qty_non_negative  batch.reserved_quantity >= 0
--   ck_batch_reserved_lte_actual        batch.reserved_quantity <= batch.actual_quantity
--   ck_stock_movement_movement_type     movement_type IN (7 types)
--   ck_prescription_item_batch_status   status IN ('reserved','dispensed','released')

-- Unique indexes:
--   uq_medicine_clinic_code          (clinic_id, code) WHERE NOT is_deleted
--   uq_supplier_clinic_code          (clinic_id, code) WHERE NOT is_deleted
--   uq_inventory_item_clinic_medicine (clinic_id, medicine_id) WHERE NOT is_deleted
--   uq_batch_clinic_item_code        (clinic_id, inventory_item_id, batch_code) WHERE NOT is_deleted

-- FEFO index:
--   ix_batch_inventory_item_expiry (inventory_item_id, expiry_date)
--   WHERE NOT is_deleted AND NOT is_recalled

-- Append-only trigger:
CREATE OR REPLACE FUNCTION fn_stock_movement_immutable()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'stock_movement is append-only: % on % is not allowed',
        TG_OP, TG_TABLE_NAME;
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_stock_movement_immutable
BEFORE UPDATE OR DELETE ON stock_movement
FOR EACH ROW EXECUTE FUNCTION fn_stock_movement_immutable();

-- View:
CREATE OR REPLACE VIEW v_inventory_status AS
SELECT
    ii.id AS inventory_item_id,
    ii.clinic_id,
    ii.medicine_id,
    m.name AS medicine_name,
    m.code AS medicine_code,
    m.base_unit,
    m.dosage_form,
    m.strength,
    COALESCE(SUM(b.actual_quantity), 0) AS total_qty,
    COALESCE(SUM(b.reserved_quantity), 0) AS total_reserved,
    COALESCE(SUM(b.actual_quantity - b.reserved_quantity), 0) AS available_qty,
    MIN(b.expiry_date) AS earliest_expiry,
    COUNT(*) FILTER (WHERE b.expiry_date < now() + INTERVAL '30 days') AS expiring_soon
FROM inventory_item ii
JOIN medicine m ON m.id = ii.medicine_id
LEFT JOIN batch b ON b.inventory_item_id = ii.id
    AND b.is_deleted = false
    AND b.is_recalled = false
    AND b.expiry_date >= CURRENT_DATE
WHERE ii.is_deleted = false
GROUP BY ii.id, ii.clinic_id, ii.medicine_id,
         m.name, m.code, m.base_unit, m.dosage_form, m.strength;
