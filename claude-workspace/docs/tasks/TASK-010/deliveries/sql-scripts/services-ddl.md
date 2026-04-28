# TASK-010: Services DDL

Migration: `alembic/versions/0013_create_services.py`
Branch: `feature/task-010-services`
DB: `cms_task010` (isolated test DB)

## Tables

### `service` — Service Catalog

```sql
CREATE TABLE service (
    id UUID PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    default_price NUMERIC(15,2) NOT NULL,
    default_duration_minutes INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT true,
    -- BaseEntity
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_by UUID,
    version INTEGER NOT NULL DEFAULT 1
);

-- Partial unique: code unique per clinic among active records
CREATE UNIQUE INDEX uq_service_clinic_code_active
    ON service (clinic_id, code)
    WHERE is_deleted = false;

-- Index for catalog browsing queries
CREATE INDEX ix_service_clinic_active
    ON service (clinic_id, category, is_active)
    WHERE is_deleted = false;

CREATE INDEX ix_service_clinic_id ON service (clinic_id);
```

### `visit_service` — Performed Services Per Visit

```sql
CREATE TABLE visit_service (
    id UUID PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
    visit_id UUID NOT NULL REFERENCES visit(id) ON DELETE RESTRICT,
    service_id UUID NOT NULL REFERENCES service(id) ON DELETE RESTRICT,
    unit_price NUMERIC(15,2) NOT NULL,  -- snapshotted at creation (AC #1)
    quantity INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'ordered'
        CHECK (status IN ('ordered','in_progress','completed','cancelled')),
    discount_amount NUMERIC(15,2),
    discount_reason TEXT,
    notes TEXT,
    performed_by_user_id UUID,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    -- BaseEntity
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_by UUID,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX ix_visit_service_visit_id ON visit_service (visit_id);
CREATE INDEX ix_visit_service_clinic_status ON visit_service (clinic_id, status);
CREATE INDEX ix_visit_service_clinic_id ON visit_service (clinic_id);
```

## RLS Policies

Applied to both tables:

```sql
ALTER TABLE service ENABLE ROW LEVEL SECURITY;
ALTER TABLE service FORCE ROW LEVEL SECURITY;

CREATE POLICY service_superuser ON service
    USING (current_setting('app.current_user_role', true) = 'superuser');

CREATE POLICY service_tenant ON service
    USING (clinic_id::text = current_setting('app.current_clinic_id', true));

-- Same pattern for visit_service
```

## Permission Seeding

New permissions added in migration 0013:

| Code | Description |
|------|-------------|
| `service.read` | View service catalog and visit services |
| `service.write` | Add/update performed services on a visit |
| `service.manage` | Create, update, soft-delete service catalog items |

Role assignments:
- **admin**: service.read, service.write, service.manage
- **doctor**: service.read, service.write
- **nurse**: service.read, service.write
- **receptionist**: service.read, service.write

(`service.price_override` was already seeded in 0007)
