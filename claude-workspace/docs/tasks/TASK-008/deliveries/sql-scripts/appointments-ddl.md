# SQL Scripts: Appointments (TASK-008)

## Migration Chain

- **t008**: Create appointment table (down_revision: 0010)
- **t008a**: Add appointment permissions (down_revision: t008)

---

## Migration t008: Create Appointment Table

```sql
-- Table: appointment
CREATE TABLE appointment (
    id              UUID NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_deleted      BOOLEAN NOT NULL DEFAULT false,
    deleted_at      TIMESTAMPTZ,
    deleted_by      UUID,
    clinic_id       UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
    created_by      UUID,
    updated_by      UUID,
    version         INTEGER NOT NULL DEFAULT 1,
    patient_id      UUID NOT NULL REFERENCES patient(id) ON DELETE RESTRICT,
    assigned_doctor_id UUID REFERENCES "user"(id) ON DELETE RESTRICT,
    scheduled_at    TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 30,
    status          VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    cancel_reason   TEXT,
    no_show_at      TIMESTAMPTZ,
    checked_in_at   TIMESTAMPTZ,
    visit_id        UUID REFERENCES visit(id) ON DELETE RESTRICT,
    CONSTRAINT pk_appointment PRIMARY KEY (id),
    CONSTRAINT ck_appointment_status CHECK (
        status IN ('scheduled','confirmed','checked_in','completed','cancelled','no_show')
    )
);

-- Indexes
CREATE INDEX ix_appointment_clinic_time
  ON appointment (clinic_id, scheduled_at)
  WHERE is_deleted = false
    AND status IN ('scheduled', 'confirmed', 'checked_in');

CREATE INDEX ix_appointment_patient_id ON appointment (patient_id);

CREATE INDEX ix_appointment_assigned_doctor
  ON appointment (clinic_id, assigned_doctor_id)
  WHERE assigned_doctor_id IS NOT NULL;

-- RLS
ALTER TABLE appointment ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointment FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON appointment
  FOR ALL
  USING (
    clinic_id IS NULL
    OR clinic_id::text = current_setting('app.current_clinic_id', true)
  );

GRANT SELECT, INSERT, UPDATE, DELETE ON appointment TO cms_app;

-- FK from visit (was placeholder without FK in migration 0010)
ALTER TABLE visit
  ADD CONSTRAINT fk_visit_appointment_id_appointment
  FOREIGN KEY (appointment_id) REFERENCES appointment(id) ON DELETE RESTRICT;
```

---

## Migration t008a: Add Appointment Permissions

```sql
-- Insert permissions
INSERT INTO permission (code, description, category)
VALUES
  ('appointment.read', 'View appointments and slots', 'appointment'),
  ('appointment.write', 'Create and update appointments', 'appointment'),
  ('appointment.cancel', 'Cancel appointments', 'appointment')
ON CONFLICT (code) DO NOTHING;

-- Grant to admin and receptionist
INSERT INTO role_permission (role_id, permission_code, granted_at)
SELECT r.id, p.code, now()
FROM role r
CROSS JOIN (
  SELECT unnest(ARRAY['appointment.read','appointment.write','appointment.cancel']) AS code
) p
WHERE r.code IN ('admin', 'receptionist')
ON CONFLICT DO NOTHING;

-- Grant read+write to doctor
INSERT INTO role_permission (role_id, permission_code, granted_at)
SELECT r.id, p.code, now()
FROM role r
CROSS JOIN (
  SELECT unnest(ARRAY['appointment.read','appointment.write']) AS code
) p
WHERE r.code = 'doctor'
ON CONFLICT DO NOTHING;
```

---

## Downgrade

```sql
-- t008a downgrade
DELETE FROM role_permission WHERE permission_code IN ('appointment.read', 'appointment.write', 'appointment.cancel');
DELETE FROM permission WHERE code IN ('appointment.read', 'appointment.write', 'appointment.cancel');

-- t008 downgrade
ALTER TABLE visit DROP CONSTRAINT IF EXISTS fk_visit_appointment_id_appointment;
DROP INDEX IF EXISTS ix_appointment_assigned_doctor;
DROP INDEX IF EXISTS ix_appointment_patient_id;
DROP INDEX IF EXISTS ix_appointment_clinic_time;
DROP POLICY IF EXISTS tenant_isolation ON appointment;
ALTER TABLE appointment NO FORCE ROW LEVEL SECURITY;
ALTER TABLE appointment DISABLE ROW LEVEL SECURITY;
DROP TABLE appointment;
```
