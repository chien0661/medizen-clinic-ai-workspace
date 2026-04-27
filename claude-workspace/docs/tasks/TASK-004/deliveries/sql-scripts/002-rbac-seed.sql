-- =====================================================================
-- RBAC Seed — INSERT Permissions, System Roles, and Role-Permission Mappings
-- =====================================================================
-- This file contains seed data extracted from alembic/versions/0007_seed_permissions_and_roles.py
-- for DBA reference. The canonical source is the alembic migration.
--
-- Inserts:
--   1. 38 permissions from BA §13.5 catalog
--   2. 5 system roles: admin, doctor, nurse, pharmacist, receptionist
--   3. Default role-permission mappings per BA §13.6
--
-- Role UUIDs: Deterministic uuid5(NAMESPACE_OID, role_code) for consistency across
-- alembic upgrade/downgrade/re-run cycles.
--
-- =====================================================================

-- =====================================================================
-- 1. INSERT PERMISSIONS — BA §13.5 Catalog
-- =====================================================================

INSERT INTO permission (code, description, category) VALUES
-- Patient module
('patient.read',        'View patient records',                              'patient'),
('patient.write',       'Create or update patient records',                  'patient'),
('patient.merge',       'Merge duplicate patient records',                   'patient'),
('patient.delete',      'Soft-delete a patient record',                      'patient'),

-- Visit / Encounter module
('visit.read',          'View visit / encounter records',                    'visit'),
('visit.write',         'Create or update visit records',                    'visit'),
('visit.cancel',        'Cancel a visit',                                    'visit'),

-- Vital Signs module
('vital.read',          'View vital sign measurements',                      'vital'),
('vital.write',         'Record vital sign measurements',                    'vital'),
('vital.delete',        'Delete a vital sign record',                        'vital'),

-- Service module
('service.catalog.manage', 'Manage service catalog items',                   'service'),
('service.perform',     'Perform / mark a service as done',                  'service'),
('service.price_override', 'Override service price on invoice',              'service'),

-- Prescription module
('prescription.write',  'Create or update prescriptions',                    'prescription'),
('prescription.cancel', 'Cancel a prescription',                             'prescription'),
('prescription.print',  'Print or export a prescription',                    'prescription'),

-- Pharmacy / Dispensing module
('pharmacy.dispense',   'Dispense medication to a patient',                  'pharmacy'),
('pharmacy.substitute_batch', 'Substitute batch during dispensing',          'pharmacy'),
('pharmacy.adjust_stock', 'Manual stock adjustment for pharmacy',            'pharmacy'),

-- Inventory module
('inventory.read',      'View inventory levels and catalog',                 'inventory'),
('inventory.manage_catalog', 'Manage inventory item catalog',                'inventory'),
('inventory.purchase_in', 'Record a purchase receipt',                       'inventory'),
('inventory.adjust',    'Manual inventory adjustment',                       'inventory'),

-- Invoicing module
('invoice.create',      'Create a new invoice',                              'invoice'),
('invoice.modify',      'Modify a draft invoice',                            'invoice'),
('invoice.void',        'Void an issued invoice',                            'invoice'),
('invoice.refund',      'Issue a refund against an invoice',                 'invoice'),

-- Payment module
('payment.receive',     'Receive and record a payment',                      'payment'),

-- HR / Attendance module
('shift.manage',        'Manage staff shift schedules',                      'hr'),
('attendance.manage',   'Manage attendance records',                         'hr'),
('leave.approve',       'Approve leave requests',                            'hr'),

-- Admin (User & Role management)
('user.manage',         'Create, update, deactivate users',                  'admin'),
('role.manage',         'Create and modify roles and permissions',           'admin'),

-- Reports module
('report.view',         'View operational reports',                          'report'),
('report.financial',    'View financial / revenue reports',                  'report'),

-- Settings module
('settings.clinic',     'Manage clinic-level settings',                      'settings'),
('settings.vital_schema', 'Manage vital sign schema configuration',          'settings'),
('settings.service_catalog', 'Manage service catalog settings',              'settings')
ON CONFLICT (code) DO NOTHING;

-- =====================================================================
-- 2. INSERT SYSTEM ROLES — BA §13.3
-- =====================================================================
-- UUIDs: uuid5(NAMESPACE_OID, role_code) for determinism
--   admin:       0c47bb77-fd45-5b42-87c0-e4beaea00040
--   doctor:      2f693b35-97a7-5d30-ad36-6a93ae5ad9d2
--   nurse:       8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d
--   pharmacist:  d5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1
--   receptionist: 1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d

INSERT INTO role (id, clinic_id, code, name, description, is_system, is_deleted, version, created_at, updated_at)
VALUES
(
    '0c47bb77-fd45-5b42-87c0-e4beaea00040'::UUID,
    NULL,
    'admin',
    'Administrator',
    'Full system access — clinic administrator',
    TRUE,
    FALSE,
    1,
    now(),
    now()
),
(
    '2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID,
    NULL,
    'doctor',
    'Doctor',
    'Clinical staff with prescribing authority',
    TRUE,
    FALSE,
    1,
    now(),
    now()
),
(
    '8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID,
    NULL,
    'nurse',
    'Nurse',
    'Nursing staff — vitals, assist in visits',
    TRUE,
    FALSE,
    1,
    now(),
    now()
),
(
    'd5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID,
    NULL,
    'pharmacist',
    'Pharmacist',
    'Pharmacy dispensing and stock management',
    TRUE,
    FALSE,
    1,
    now(),
    now()
),
(
    '1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d'::UUID,
    NULL,
    'receptionist',
    'Receptionist',
    'Front desk — scheduling, invoicing, payment',
    TRUE,
    FALSE,
    1,
    now(),
    now()
)
ON CONFLICT DO NOTHING;

-- =====================================================================
-- 3. INSERT ROLE-PERMISSION MAPPINGS — BA §13.6
-- =====================================================================
-- Each row assigns a permission to a role via role_permission M2M table

-- ADMIN: All 38 permissions
INSERT INTO role_permission (role_id, permission_code, granted_at)
SELECT '0c47bb77-fd45-5b42-87c0-e4beaea00040'::UUID, code, now()
FROM permission
ON CONFLICT DO NOTHING;

-- DOCTOR: 18 permissions (clinical + some admin)
INSERT INTO role_permission (role_id, permission_code, granted_at) VALUES
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'patient.read', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'patient.write', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'visit.read', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'visit.write', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'visit.cancel', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'vital.read', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'vital.write', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'service.perform', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'service.price_override', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'prescription.write', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'prescription.cancel', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'prescription.print', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'invoice.create', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'invoice.modify', now()),
('2f693b35-97a7-5d30-ad36-6a93ae5ad9d2'::UUID, 'report.view', now())
ON CONFLICT DO NOTHING;

-- NURSE: 11 permissions (vital signs, support visit, limited services)
INSERT INTO role_permission (role_id, permission_code, granted_at) VALUES
('8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID, 'patient.read', now()),
('8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID, 'patient.write', now()),
('8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID, 'visit.read', now()),
('8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID, 'visit.write', now()),
('8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID, 'vital.read', now()),
('8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID, 'vital.write', now()),
('8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID, 'vital.delete', now()),
('8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID, 'service.perform', now()),
('8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID, 'prescription.print', now()),
('8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID, 'inventory.read', now()),
('8ddb2fda-9f78-5e6e-9d15-0e3e0b9c1c3d'::UUID, 'report.view', now())
ON CONFLICT DO NOTHING;

-- PHARMACIST: 9 permissions (pharmacy, inventory)
INSERT INTO role_permission (role_id, permission_code, granted_at) VALUES
('d5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID, 'patient.read', now()),
('d5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID, 'prescription.print', now()),
('d5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID, 'pharmacy.dispense', now()),
('d5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID, 'pharmacy.substitute_batch', now()),
('d5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID, 'pharmacy.adjust_stock', now()),
('d5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID, 'inventory.read', now()),
('d5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID, 'inventory.manage_catalog', now()),
('d5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID, 'inventory.purchase_in', now()),
('d5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID, 'inventory.adjust', now()),
('d5f1c8e2-f4b1-5c2a-92d8-97e3c7f8d6e1'::UUID, 'report.view', now())
ON CONFLICT DO NOTHING;

-- RECEPTIONIST: 11 permissions (front-desk, scheduling, invoicing, payment)
INSERT INTO role_permission (role_id, permission_code, granted_at) VALUES
('1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d'::UUID, 'patient.read', now()),
('1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d'::UUID, 'patient.write', now()),
('1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d'::UUID, 'visit.read', now()),
('1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d'::UUID, 'visit.write', now()),
('1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d'::UUID, 'service.perform', now()),
('1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d'::UUID, 'invoice.create', now()),
('1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d'::UUID, 'invoice.modify', now()),
('1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d'::UUID, 'payment.receive', now()),
('1a2b3c4d-5e6f-5a7b-8c9d-0e1f2a3b4c5d'::UUID, 'report.view', now())
ON CONFLICT DO NOTHING;

-- =====================================================================
-- END OF SEED DATA
-- =====================================================================
