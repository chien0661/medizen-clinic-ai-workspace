# Production Database Roles

## Overview

The Clinic CMS uses PostgreSQL Row-Level Security (RLS) to enforce multi-tenant
data isolation. For RLS to be **actively enforced**, the application must connect
as a **non-superuser** role.

> **CRITICAL**: PostgreSQL superusers (BYPASSRLS) bypass RLS silently, even when
> `FORCE ROW LEVEL SECURITY` is set. If the app connects as `cms` (the default
> superuser in local dev), RLS is not enforced in production.

---

## Required Production Role: `cms_app`

| Attribute    | Value                                  |
|--------------|----------------------------------------|
| Role name    | `cms_app`                              |
| LOGIN        | YES                                    |
| SUPERUSER    | NO                                     |
| BYPASSRLS    | NO                                     |
| Password     | Set via vault / secret manager         |

### Automated Setup (Alembic migration 0004)

Migration `0004_create_app_role` creates `cms_app` idempotently and grants the
required privileges. It runs automatically with:

```bash
alembic upgrade head
```

### Manual Bootstrap (alternative)

```sql
-- Run as postgres superuser
CREATE ROLE cms_app LOGIN PASSWORD '<secure-password>'
  NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

GRANT CONNECT ON DATABASE cms TO cms_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cms_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cms_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO cms_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE ON SEQUENCES TO cms_app;
```

---

## Environment Variable

In **production / staging**, the `DATABASE_URL` must use `cms_app`:

```
DATABASE_URL=postgresql+asyncpg://cms_app:<password>@<host>:5432/cms
```

**Never use the `cms` superuser role in production.**

---

## Startup Check

The application checks the connected role at startup (`app/core/db_security.py`).
If it detects a superuser connection outside `ENVIRONMENT=development`, it logs
a **CRITICAL** warning. While the app will start, cross-tenant data leakage is
possible until the role is corrected.

---

## Role Matrix

| Role       | Purpose                | Superuser | BYPASSRLS | RLS enforced |
|------------|------------------------|-----------|-----------|--------------|
| `postgres` | DB admin               | YES       | YES       | NO           |
| `cms`      | Dev / migration owner  | YES       | YES       | NO           |
| `cms_app`  | Application (prod)     | NO        | NO        | YES          |

---

## Local Development

In development (`ENVIRONMENT=development`), connecting as `cms` (superuser) is
acceptable — the startup check skips the warning, and RLS is tested via the
`cms_app` role in integration tests (`tests/integration/test_rls_isolation.py`).
