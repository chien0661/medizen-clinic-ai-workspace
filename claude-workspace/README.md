# Clinic CMS

Multi-tenant SaaS clinic management system. See workspace docs at `../docs/` for full design (business analysis, system design, database design).

## Stack

- Python 3.11 + FastAPI (async)
- PostgreSQL 15 with Row-Level Security (RLS enabled in TASK-002)
- Redis 7 (cache, session, Arq job queue)
- Alembic migrations (async, autogenerate)
- Tauri + React desktop client (TASK-016)

## Architecture

- **Design docs**: `../docs/clinic_management_system_design.md`
- **Database design**: `../docs/clinic_management_database_design.md`
- **Business analysis**: `../docs/clinic_management_business_analysis.md`
- **Layered**: Router → Service → Repository → Model (SQLAlchemy)
- **Multi-tenancy**: `clinic_id` on all entities; RLS context via `app.current_clinic_id` session local

## Local Development

Prerequisites: Docker Desktop running.

```bash
cd docker
docker compose up -d
```

Services:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Postgres: localhost:5432 (db=cms, user=cms, pass=cms)
- Redis: localhost:6379

Stop: `docker compose down` (add `-v` to drop the data volume).

## Running Migrations

```bash
# Inside the api container (code is volume-mounted)
docker exec clinic_cms_api alembic upgrade head

# Or from host (if postgres is exposed on localhost:5432)
DATABASE_URL=postgresql+asyncpg://cms:cms@localhost:5432/cms alembic upgrade head
```

## Running Tests

```bash
# Run all tests inside the api container
docker exec clinic_cms_api pytest -q

# With coverage
docker exec clinic_cms_api pytest -q --cov=app --cov-report=term-missing
```

## Project Layout

```
clinic-cms/
├── app/
│   ├── main.py
│   ├── core/           # config, db, base_model, exceptions, logging
│   ├── modules/
│   │   └── users/
│   │       └── models/
│   │           └── clinic.py    # Clinic (tenant) model
│   └── workers/        # Arq scheduler + tasks
├── alembic/
│   ├── env.py          # async autogenerate
│   └── versions/
│       └── 0001_*_create_clinic.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── docker/
│   ├── docker-compose.yml
│   └── postgres-init.sql
├── .github/workflows/ci.yml
├── pyproject.toml
└── alembic.ini
```

## Production Deployment Requirements

### Database Role

**CRITICAL**: The app must connect as the `cms_app` role (not `cms`) in production.
The `cms` user is a PostgreSQL superuser — it silently bypasses RLS, leaking cross-tenant data.

```bash
# Run migrations (creates cms_app role via migration 0004)
alembic upgrade head

# Set production DATABASE_URL
DATABASE_URL=postgresql+asyncpg://cms_app:<password>@<host>:5432/cms
```

See [`docs/deployment/database-roles.md`](docs/deployment/database-roles.md) for full details.

### JWT Authentication

In `ENVIRONMENT=production` or `ENVIRONMENT=staging`:
- Dev override headers (`X-Clinic-Id` / `X-User-Id`) are **rejected with 401**
- JWT Bearer tokens **must** have a valid HS256 signature (verified against `JWT_SECRET`)
- Invalid signature → 401

In `ENVIRONMENT=development`:
- Dev headers and unsigned JWTs are accepted for convenience

## Implementation Roadmap

See `../claude-workspace/docs/tasks/dashboard.md` for the 16-task roadmap (TASK-001..TASK-016).
