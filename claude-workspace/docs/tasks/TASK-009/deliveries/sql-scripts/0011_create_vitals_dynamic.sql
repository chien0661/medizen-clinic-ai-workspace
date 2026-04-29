-- TASK-009: Vitals Dynamic Form — DDL Reference
-- This is the DDL equivalent of migration 0011_create_vitals_dynamic.py
-- Applied to: cms_task009
-- Date: 2026-04-27

-- 1. system_vital_preset (global, no RLS)
CREATE TABLE system_vital_preset (
    id UUID PRIMARY KEY,
    specialty_code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    fields JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_system_vital_preset_specialty_code UNIQUE (specialty_code)
);
GRANT SELECT ON system_vital_preset TO cms_app;

-- 2. vital_field_definition (BaseEntity + RLS)
CREATE TABLE vital_field_definition (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
    key VARCHAR(100) NOT NULL,
    label VARCHAR(200) NOT NULL,
    data_type VARCHAR(20) NOT NULL,
    unit VARCHAR(20),
    min_value NUMERIC(10,4),
    max_value NUMERIC(10,4),
    warning_min NUMERIC(10,4),
    warning_max NUMERIC(10,4),
    decimal_places INTEGER,
    options JSONB,
    is_required BOOLEAN NOT NULL DEFAULT false,
    sort_order INTEGER NOT NULL DEFAULT 0,
    group_name VARCHAR(100),
    placeholder VARCHAR(200),
    help_text VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_system BOOLEAN NOT NULL DEFAULT false,
    -- BaseEntity
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,
    created_by UUID,
    updated_by UUID,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX ix_vital_field_def_clinic_id ON vital_field_definition (clinic_id);
CREATE UNIQUE INDEX uq_vital_field_def_clinic_key ON vital_field_definition (clinic_id, key)
    WHERE NOT is_deleted;

ALTER TABLE vital_field_definition ENABLE ROW LEVEL SECURITY;
ALTER TABLE vital_field_definition FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON vital_field_definition
    FOR ALL
    USING (
        clinic_id IS NULL
        OR clinic_id::text = current_setting('app.current_clinic_id', true)
    );
GRANT SELECT, INSERT, UPDATE, DELETE ON vital_field_definition TO cms_app;

-- 3. vital_schema_version (immutable snapshots + RLS)
CREATE TABLE vital_schema_version (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
    version_number INTEGER NOT NULL,
    definitions_snapshot JSONB NOT NULL,
    change_summary VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    CONSTRAINT uq_vital_schema_version_clinic_ver UNIQUE (clinic_id, version_number)
);

CREATE INDEX ix_vital_schema_version_clinic_ver ON vital_schema_version (clinic_id, version_number);

ALTER TABLE vital_schema_version ENABLE ROW LEVEL SECURITY;
ALTER TABLE vital_schema_version FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON vital_schema_version
    FOR ALL
    USING (
        clinic_id IS NULL
        OR clinic_id::text = current_setting('app.current_clinic_id', true)
    );
GRANT SELECT, INSERT ON vital_schema_version TO cms_app;

-- 4. visit_vitals (BaseEntity + RLS + GIN index)
CREATE TABLE visit_vitals (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
    visit_id UUID NOT NULL REFERENCES visit(id) ON DELETE RESTRICT,
    schema_version INTEGER NOT NULL,
    values JSONB NOT NULL,
    notes TEXT,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    recorded_by UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- BaseEntity
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,
    created_by UUID,
    updated_by UUID,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX ix_visit_vitals_values_gin ON visit_vitals USING GIN (values);
CREATE INDEX ix_visit_vitals_clinic_id ON visit_vitals (clinic_id);
CREATE INDEX ix_visit_vitals_visit_recorded ON visit_vitals (visit_id, recorded_at);
CREATE INDEX ix_visit_vitals_is_primary ON visit_vitals (visit_id, is_primary)
    WHERE is_primary = true;

ALTER TABLE visit_vitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE visit_vitals FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON visit_vitals
    FOR ALL
    USING (
        clinic_id IS NULL
        OR clinic_id::text = current_setting('app.current_clinic_id', true)
    );
GRANT SELECT, INSERT, UPDATE, DELETE ON visit_vitals TO cms_app;

-- 5. Permissions
INSERT INTO permission (code, description, category)
VALUES ('vital.manage', 'Manage vital field definitions (admin)', 'vital')
ON CONFLICT (code) DO NOTHING;

-- Assign to admin role
INSERT INTO role_permission (role_id, permission_code, granted_at)
SELECT r.id, unnest(ARRAY['vital.read','vital.write','vital.delete','vital.manage']), now()
FROM role r WHERE r.code = 'admin' AND r.clinic_id IS NULL
ON CONFLICT DO NOTHING;

-- doctor
INSERT INTO role_permission (role_id, permission_code, granted_at)
SELECT r.id, unnest(ARRAY['vital.read','vital.write']), now()
FROM role r WHERE r.code = 'doctor' AND r.clinic_id IS NULL
ON CONFLICT DO NOTHING;

-- nurse
INSERT INTO role_permission (role_id, permission_code, granted_at)
SELECT r.id, unnest(ARRAY['vital.read','vital.write','vital.delete']), now()
FROM role r WHERE r.code = 'nurse' AND r.clinic_id IS NULL
ON CONFLICT DO NOTHING;
