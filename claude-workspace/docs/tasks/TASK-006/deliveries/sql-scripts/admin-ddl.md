# Admin DDL — TASK-006

## Migration 0015: Clinic Permissions

File: `alembic/versions/0015_add_clinic_permissions.py`

Thêm permissions mới cho quản lý clinic:

```sql
INSERT INTO permission (code, description, category) VALUES
  ('clinic.create', 'Create a new clinic tenant', 'admin'),
  ('clinic.read', 'View clinic details', 'admin'),
  ('clinic.update', 'Update clinic record', 'admin'),
  ('clinic.settings.update', 'Update clinic settings', 'settings'),
  ('clinic.onboard', 'Run the clinic onboarding wizard', 'admin')
ON CONFLICT (code) DO NOTHING;

-- Grant all to admin system role (queries role by code, tolerates any UUID)
INSERT INTO role_permission (role_id, permission_code, granted_at)
SELECT r.id, p.code, now()
FROM role r, permission p
WHERE r.code = 'admin' AND r.clinic_id IS NULL
  AND p.code IN ('clinic.create', 'clinic.read', 'clinic.update',
                 'clinic.settings.update', 'clinic.onboard')
ON CONFLICT DO NOTHING;
```

---

## Migration 0016: Clinic Settings + Onboarding State

File: `alembic/versions/0016_create_clinic_settings.py`

### Table: `clinic_settings`

```sql
CREATE TABLE clinic_settings (
    clinic_id    UUID        NOT NULL,
    settings     JSONB       NOT NULL DEFAULT '{}',
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by   UUID,
    CONSTRAINT pk_clinic_settings PRIMARY KEY (clinic_id),
    CONSTRAINT fk_clinic_settings_clinic_id_clinic
        FOREIGN KEY (clinic_id) REFERENCES clinic(id) ON DELETE CASCADE
);

-- RLS: tenant isolation
ALTER TABLE clinic_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinic_settings FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON clinic_settings
    FOR ALL
    USING (
        clinic_id IS NULL
        OR clinic_id::text = current_setting('app.current_clinic_id', true)
    );

GRANT SELECT, INSERT, UPDATE, DELETE ON clinic_settings TO cms_app;
```

#### Settings JSONB Structure

```json
{
  "operating_hours": {
    "mon": {"is_open": bool, "open": "HH:MM", "close": "HH:MM"},
    ...
    "sun": {"is_open": bool, "open": "HH:MM", "close": "HH:MM"}
  },
  "appointment": {
    "slot_duration_minutes": int,
    "booking_advance_days": int,
    "allow_walk_in": bool,
    "require_deposit": bool,
    "deposit_amount": float
  },
  "queue": {
    "algorithm": "fifo|priority",
    "max_wait_minutes": int,
    "sms_reminder": bool
  },
  "inventory": {
    "low_stock_threshold_percent": float,
    "auto_reorder": bool
  },
  "prescription": {
    "max_days_supply": int,
    "require_generic": bool
  },
  "billing": {
    "currency": string,
    "tax_rate_percent": float,
    "invoice_prefix": string
  },
  "specialty": {
    "code": "general|pediatric|ob_gyn|dermatology|dental",
    "vital_fields": [string]
  }
}
```

### Table: `clinic_onboarding_state`

```sql
CREATE TABLE clinic_onboarding_state (
    clinic_id       UUID        NOT NULL,
    current_step    VARCHAR(50) NOT NULL DEFAULT 'info',
    completed_steps TEXT[]      NOT NULL DEFAULT ARRAY[]::text[],
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    started_by      UUID,
    CONSTRAINT pk_clinic_onboarding_state PRIMARY KEY (clinic_id),
    CONSTRAINT fk_clinic_onboarding_state_clinic_id_clinic
        FOREIGN KEY (clinic_id) REFERENCES clinic(id) ON DELETE CASCADE
);

-- RLS: standard tenant isolation
ALTER TABLE clinic_onboarding_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinic_onboarding_state FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON clinic_onboarding_state
    FOR ALL
    USING (
        clinic_id IS NULL
        OR clinic_id::text = current_setting('app.current_clinic_id', true)
    );

GRANT SELECT, INSERT, UPDATE, DELETE ON clinic_onboarding_state TO cms_app;
```

---

## Downgrade

```sql
-- 0016 downgrade
REVOKE SELECT, INSERT, UPDATE, DELETE ON clinic_onboarding_state FROM cms_app;
DROP POLICY IF EXISTS tenant_isolation ON clinic_onboarding_state;
ALTER TABLE clinic_onboarding_state NO FORCE ROW LEVEL SECURITY;
ALTER TABLE clinic_onboarding_state DISABLE ROW LEVEL SECURITY;
DROP TABLE clinic_onboarding_state;

REVOKE SELECT, INSERT, UPDATE, DELETE ON clinic_settings FROM cms_app;
DROP POLICY IF EXISTS tenant_isolation ON clinic_settings;
ALTER TABLE clinic_settings NO FORCE ROW LEVEL SECURITY;
ALTER TABLE clinic_settings DISABLE ROW LEVEL SECURITY;
DROP TABLE clinic_settings;

-- 0015 downgrade
DELETE FROM role_permission
WHERE role_id = (SELECT id FROM role WHERE code = 'admin' AND clinic_id IS NULL)
  AND permission_code IN ('clinic.create', 'clinic.read', 'clinic.update',
                           'clinic.settings.update', 'clinic.onboard');

DELETE FROM permission WHERE code IN (
    'clinic.create', 'clinic.read', 'clinic.update',
    'clinic.settings.update', 'clinic.onboard'
);
```
