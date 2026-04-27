-- =====================================================================
-- RBAC Schema — DDL for TASK-004
-- =====================================================================
-- This file contains the DDL extracted from alembic/versions/0006_setup_rbac.py
-- for DBA reference. The canonical source is the alembic migration.
--
-- Tables:
--   - permission (system-wide catalog, no RLS)
--   - role (system + clinic-scoped roles, RLS on clinic_id)
--   - role_permission (M2M: role ↔ permission)
--   - user_role (M2M: user ↔ role, RLS via user.clinic_id)
--   - user_extra_permission (per-user grant/deny overrides, RLS via user.clinic_id)
--
-- RLS Policies:
--   - role: allows system roles (clinic_id IS NULL) + clinic-scoped access
--   - user_role: isolation via user.clinic_id
--   - user_extra_permission: isolation via user.clinic_id
--
-- Indexes:
--   - ix_permission_category
--   - ix_role_clinic_id
--   - uq_role_clinic_code (partial: clinic-scoped roles)
--   - uq_role_system_code (partial: system roles)
--   - ix_role_permission_role_id
--   - ix_user_role_user_id, ix_user_role_role_id
--   - uq_user_role_user_role (partial unique)
--   - ix_user_extra_perm_user_id
--   - uq_user_extra_perm_user_code (partial: active overrides only)
--
-- =====================================================================

-- =====================================================================
-- 1. ENUM TYPE: extra_perm_type
-- =====================================================================
CREATE TYPE extra_perm_type AS ENUM ('grant', 'deny');

-- =====================================================================
-- 2. TABLE: permission
-- =====================================================================
-- System-wide permission catalog (no RLS, all users can read)
-- Natural PK: code (e.g., 'patient.read', 'invoice.void')

CREATE TABLE permission (
    code VARCHAR(100) PRIMARY KEY NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX ix_permission_category ON permission (category);

-- Grants (no RLS on this table)
GRANT SELECT, INSERT, UPDATE, DELETE ON permission TO cms_app;

-- =====================================================================
-- 3. TABLE: role
-- =====================================================================
-- Roles: system roles (clinic_id IS NULL, is_system=TRUE) +
--        clinic-scoped custom roles (clinic_id NOT NULL, is_system=FALSE)
-- RLS: allows all system roles + clinic-scoped rows matching current clinic

CREATE TABLE role (
    id UUID PRIMARY KEY NOT NULL,
    clinic_id UUID,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    created_by UUID,
    updated_by UUID,
    version INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_role_clinic_id_clinic
        FOREIGN KEY (clinic_id) REFERENCES clinic (id) ON DELETE RESTRICT
);

CREATE INDEX ix_role_clinic_id ON role (clinic_id);

-- Partial unique indexes for role code uniqueness
-- Clinic-scoped: (clinic_id, code) unique when clinic_id NOT NULL and not deleted
CREATE UNIQUE INDEX uq_role_clinic_code
    ON role (clinic_id, code)
    WHERE NOT is_deleted AND clinic_id IS NOT NULL;

-- System roles: code unique when clinic_id IS NULL and not deleted
CREATE UNIQUE INDEX uq_role_system_code
    ON role (code)
    WHERE NOT is_deleted AND clinic_id IS NULL;

-- RLS: allow all system roles (clinic_id IS NULL) + matching clinic
ALTER TABLE role ENABLE ROW LEVEL SECURITY;
ALTER TABLE role FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON role
    FOR ALL
    USING (
        clinic_id IS NULL
        OR clinic_id::text = current_setting('app.current_clinic_id', true)
    );

GRANT SELECT, INSERT, UPDATE, DELETE ON role TO cms_app;

-- =====================================================================
-- 4. TABLE: role_permission
-- =====================================================================
-- M2M: maps roles to permissions (composite PK)

CREATE TABLE role_permission (
    role_id UUID NOT NULL,
    permission_code VARCHAR(100) NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    granted_by UUID,
    PRIMARY KEY (role_id, permission_code),
    CONSTRAINT fk_role_permission_role_id_role
        FOREIGN KEY (role_id) REFERENCES role (id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permission_permission_code_permission
        FOREIGN KEY (permission_code) REFERENCES permission (code) ON DELETE CASCADE
);

CREATE INDEX ix_role_permission_role_id ON role_permission (role_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON role_permission TO cms_app;

-- =====================================================================
-- 5. TABLE: user_role
-- =====================================================================
-- M2M: maps users to roles (multi-role support)
-- RLS: isolation via user.clinic_id

CREATE TABLE user_role (
    id UUID PRIMARY KEY NOT NULL,
    user_id UUID NOT NULL,
    role_id UUID NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    assigned_by UUID,
    CONSTRAINT fk_user_role_user_id_user
        FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_role_role_id_role
        FOREIGN KEY (role_id) REFERENCES role (id) ON DELETE CASCADE
);

CREATE INDEX ix_user_role_user_id ON user_role (user_id);
CREATE INDEX ix_user_role_role_id ON user_role (role_id);

-- Unique: one row per (user, role) — no duplicate assignments
CREATE UNIQUE INDEX uq_user_role_user_role ON user_role (user_id, role_id);

-- RLS: user_role is isolated by joining to user.clinic_id
ALTER TABLE user_role ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_role FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON user_role
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM "user" u
            WHERE u.id = user_role.user_id
            AND (
                u.clinic_id::text = current_setting('app.current_clinic_id', true)
                OR current_setting('app.current_clinic_id', true) IS NULL
            )
        )
    );

GRANT SELECT, INSERT, UPDATE, DELETE ON user_role TO cms_app;

-- =====================================================================
-- 6. TABLE: user_extra_permission
-- =====================================================================
-- Per-user grant/deny overrides (independent of role membership)
-- Soft-delete support for audit trail
-- Partial unique index: only one active override per (user, permission)

CREATE TABLE user_extra_permission (
    id UUID PRIMARY KEY NOT NULL,
    user_id UUID NOT NULL,
    permission_code VARCHAR(100) NOT NULL,
    type extra_perm_type NOT NULL,
    reason TEXT,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    created_by UUID,
    updated_by UUID,
    CONSTRAINT fk_user_extra_permission_user_id_user
        FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_extra_permission_permission_code_permission
        FOREIGN KEY (permission_code) REFERENCES permission (code) ON DELETE CASCADE
);

CREATE INDEX ix_user_extra_perm_user_id ON user_extra_permission (user_id);

-- Partial unique: one active override per (user, permission)
CREATE UNIQUE INDEX uq_user_extra_perm_user_code
    ON user_extra_permission (user_id, permission_code)
    WHERE NOT is_deleted;

-- RLS: isolated by joining to user.clinic_id
ALTER TABLE user_extra_permission ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_extra_permission FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON user_extra_permission
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM "user" u
            WHERE u.id = user_extra_permission.user_id
            AND (
                u.clinic_id::text = current_setting('app.current_clinic_id', true)
                OR current_setting('app.current_clinic_id', true) IS NULL
            )
        )
    );

GRANT SELECT, INSERT, UPDATE, DELETE ON user_extra_permission TO cms_app;

-- =====================================================================
-- END OF SCHEMA DDL
-- =====================================================================
