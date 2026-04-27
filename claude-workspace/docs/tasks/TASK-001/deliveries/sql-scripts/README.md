# SQL Scripts Delivery: TASK-001 Foundation

**Task:** TASK-001  
**Date:** 2026-04-26  
**Version:** 1.0

---

## Overview

This directory contains the SQL initialization and migration scripts for TASK-001 Foundation. These scripts set up the PostgreSQL database schema and required extensions.

---

## Files

### 1. postgres-init.sql (Extension Initialization)

**Location:** `clinic-cms/docker/postgres-init.sql`

**Purpose:** Initialize required PostgreSQL extensions on first container startup.

**Extensions Installed:**

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- gen_random_uuid() function
CREATE EXTENSION IF NOT EXISTS "pgcrypto";        -- Cryptographic functions (future use)
CREATE EXTENSION IF NOT EXISTS "unaccent";        -- Text normalization for search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- Trigram matching for fuzzy search
CREATE EXTENSION IF NOT EXISTS "btree_gin";       -- GIN indexes for complex queries
```

**When it runs:** Automatically executed when the PostgreSQL container starts for the first time (mounted in docker-compose as init script).

**How to verify:**

```bash
docker exec clinic_cms_postgres psql -U cms -d cms -c "\dx"
```

Expected output:

```
                                     List of installed extensions
     Name     | Version |   Schema   |                         Description
--------------+---------+------------+----------------------------------------------
 btree_gin    | 1.3     | public     | support for indexing common datatypes in GiST
 pgcrypto     | 1.3     | public     | cryptographic functions
 pg_trgm      | 1.6     | public     | text search support for trigram matching
 plpgsql      | 1.0     | public     | PL/pgSQL procedural language
 unaccent     | 1.1     | public     | text search support for unaccented search
 uuid-ossp    | 1.1     | public     | generate universally unique identifiers (UUIDs)
(6 rows)
```

---

### 2. 0001_abc123_create_clinic.py (Migration: Initial Schema)

**Location:** `clinic-cms/alembic/versions/0001_abc123_create_clinic.py`

**Purpose:** Create the initial `clinic` table with all foundational columns (TimestampMixin, SoftDeleteMixin, AuditedMixin, settings JSONB).

**What it creates:**

```sql
CREATE TABLE clinic (
    -- Primary key (UUID)
    id UUID PRIMARY KEY,
    
    -- Basic clinic info
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    specialty VARCHAR(50) NOT NULL,
    address VARCHAR(500),
    phone VARCHAR(20),
    email VARCHAR(200),
    tax_code VARCHAR(50),
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- Settings (merged from clinic_settings table for v1 simplicity)
    settings JSONB NOT NULL DEFAULT '{}',
    
    -- TimestampMixin columns
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- SoftDeleteMixin columns
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID,
    
    -- AuditedMixin columns
    created_by UUID,
    updated_by UUID
);

-- Named indexes (following §2.1 naming convention)
CREATE UNIQUE INDEX ix_clinic_code ON clinic(code);
CREATE INDEX ix_clinic_is_active ON clinic(is_active);
```

**How to apply:**

```bash
# From host (if postgres is exposed on localhost:5432)
DATABASE_URL=postgresql+asyncpg://cms:cms@localhost:5432/cms \
  alembic upgrade head

# Or from API container (recommended)
docker exec clinic_cms_api alembic upgrade head
```

**How to verify:**

```bash
# Check current migration
docker exec clinic_cms_api alembic current
# Expected: abc123 (create clinic table)

# Inspect table structure
docker exec clinic_cms_postgres psql -U cms -d cms -c "\d clinic"
```

**Rollback (if needed):**

```bash
docker exec clinic_cms_api alembic downgrade base
```

---

## Migration Strategy

### Idempotency

All migrations are designed to be idempotent — running `alembic upgrade head` twice should produce no changes on the second run.

**Verify idempotency:**

```bash
docker exec clinic_cms_api alembic upgrade head
docker exec clinic_cms_api alembic current
# Should show abc123 both times
```

### Async Support

Alembic is configured for async PostgreSQL using `asyncpg` driver.

**Configuration:** See `clinic-cms/alembic/env.py` — uses `create_async_engine()` and `async_configure_engine()`.

### Auto-Model-Discovery

`env.py` automatically imports models from `app/*/models/` directories via `pkgutil.walk_packages()`. No need to manually register models in `env.py` for Alembic to detect them during `--autogenerate`.

---

## Database Setup Checklist

- [ ] `docker compose up -d` — all services healthy
- [ ] `docker exec clinic_cms_postgres psql -U cms -d cms -c "\dx"` — 6 extensions present
- [ ] `docker exec clinic_cms_api alembic upgrade head` — no errors
- [ ] `docker exec clinic_cms_api alembic current` — shows `abc123`
- [ ] `docker exec clinic_cms_postgres psql -U cms -d cms -c "\d clinic"` — clinic table exists with all columns
- [ ] `docker exec clinic_cms_api pytest -q` — 37/37 tests pass

---

## Connection Strings

### Default (Docker Compose)

```
postgresql+asyncpg://cms:cms@postgres:5432/cms
```

(Used by FastAPI inside container)

### From Host (local development)

```
postgresql+asyncpg://cms:cms@localhost:5432/cms
```

(Used for CLI tools like Alembic on the host)

### Environment Variable

Set `DATABASE_URL` to override:

```bash
export DATABASE_URL=postgresql+asyncpg://cms:cms@localhost:5432/cms
alembic upgrade head
```

---

## Future Migrations

Starting with TASK-002, new migrations will be created by Alembic's `--autogenerate` feature:

```bash
docker exec clinic_cms_api alembic revision --autogenerate -m "add patient table"
```

Each migration file will follow the naming: `NNNN_<hash>_<description>.py`

---

## Troubleshooting

### "could not connect to server"

Ensure PostgreSQL container is running:

```bash
docker ps | grep postgres
# Should show clinic_cms_postgres running
```

### "Extension does not exist"

The extensions are created in `postgres-init.sql` at first startup. If they're missing:

```bash
docker compose down -v
docker compose up -d
```

This resets the database and reruns the init script.

### "Alembic command not found"

Run commands inside the API container:

```bash
docker exec clinic_cms_api alembic upgrade head
```

Not from the host (unless you've installed alembic and set DATABASE_URL).

---

**Document Version:** 1.0 | **Date:** 2026-04-26 | **Status:** Approved
