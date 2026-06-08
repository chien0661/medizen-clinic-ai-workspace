# PROJECT.md — Clinic CMS Workspace

Project-specific context for Claude Code. Read alongside `CLAUDE.md` (workflow rules + git conventions) and `docs/guide/workflow/MULTI_AGENT_ORCHESTRATION.md` (agent contracts).

This file is **agent-consumable**: every section is read by Implementation, Review, Test, or Documentation agents at runtime. Keep it terse and accurate.

---

## Workspace Configuration

```yaml
workspace-type: microservice    # This repo is a workspace; source code lives in sibling repos.

repos:
  clinic-cms:
    path: ../clinic-cms
    description: FastAPI backend (Python 3.11, PostgreSQL 15, Redis 7, Alembic, Arq). NOTE - this directory is often left checked out on a stale per-task feature branch. Audits/integration work should target ../clinic-cms-merge instead, which is the main worktree.
  clinic-cms-merge:
    path: ../clinic-cms-merge
    description: Backend MAIN-branch worktree (same git repo as clinic-cms, different worktree). Use this for read audits, integration testing, and any "what's actually shipped on main" question. Contains all merged modules (admin, appointments, audit, auth, billing, hr, inventory, notifications, patients, pharmacy, prescriptions, reports, services, users, visits, vitals).
  clinic-cms-web:
    path: ../clinic-cms-web
    description: Tauri 2 desktop client (React 18 + Vite + TypeScript + TanStack Query + zustand). Currently checked out on main.
  clinic-cms-landing:
    path: ../clinic-cms-landing
    description: Next.js 15 marketing landing site (Vercel SSR). SEO-optimized, separate from desktop app. Branch feature/TASK-030-landing-page.
```

`/commit-push-pr TASK-ID` commits and creates PRs in each repo listed under `affected-repos` in the task's frontmatter.

Workspace docs (specs, ADRs, business analysis): `../docs/` (sibling of this workspace) and this workspace's own `docs/`.

---

## Project Identity

- **Project**: Clinic CMS — multi-tenant SaaS clinic management system
- **Backend**: `clinic-cms` (Python 3.11, FastAPI 0.115+, async)
- **Frontend**: `clinic-cms-web` (Tauri 2 desktop app; React 18.3 + Vite 5 + TypeScript 5.4)
- **Default API port**: 8000 (Docker Compose)
- **Default web dev port**: 1420 (Vite/Tauri dev)

---

## Architecture Pattern

**Backend** follows **Layered Architecture** (Router → Service → Repository → Model):

```
clinic-cms/app/
├── core/                  # cross-cutting: db, redis, audit, permissions, tenancy middleware
├── modules/<feature>/
│   ├── api/routes.py      # FastAPI routers, request/response shape
│   ├── services/          # business logic, orchestration, cache invalidation
│   ├── models/            # SQLAlchemy 2.0 async models (BaseEntity, mixins)
│   ├── schemas/           # Pydantic v2 request/response schemas
│   └── repositories/      # data access (where present)
├── workers/               # Arq background jobs
└── main.py                # app factory + router registration
```

Existing modules (as of TASK-017): `auth`, `audit`, `users`, `patients`. Each new feature module follows the same structure.

**Frontend** is a Tauri-wrapped React SPA — feature-folder layout under `clinic-cms-web/src/`, `@tauri-apps/plugin-sql` for offline-first SQLite mirror, `@tanstack/react-query` for server state, `zustand` for client state.

### Multi-tenancy

- Every domain entity carries `clinic_id` (UUID).
- Postgres **Row-Level Security** is enforced via the session-local `app.current_clinic_id`.
- `app/core/tenancy.py` middleware sets the session var per request from the JWT.
- Helpers and migration patterns established in TASK-001 (RLS) and TASK-002 (audit).

### Authorization

- RBAC via `app/modules/users/`: 5 system roles, 38 permissions, multi-role per user, plus per-user grant/deny overrides (TASK-004).
- Route gating: `Depends(require_permission("<perm.code>"))` from `app/core/permissions.py`.
- Effective permissions cached in JWT (15 min) and Redis (`user:perms:{user_id}`, 5 min TTL); invalidated on role/extra-perm change.

### Audit

- Models opt in via `__auditable__ = True`; secret columns must declare `__audit_exclude__: ClassVar[frozenset[str]]` (see `code-implementation.md` "Audit PII Exclusion Pattern"). Global redaction list in `app/core/audit.py` catches common names.

---

## Technology Stack

### Backend (`clinic-cms`)
- **Framework**: FastAPI 0.115+ on Uvicorn (`uvicorn[standard]`)
- **Language**: Python 3.11 (`requires-python = ">=3.11"`)
- **DB**: PostgreSQL 15 (`postgres:15-alpine`)
- **DB driver**: `asyncpg` 0.30 via `sqlalchemy[asyncio]` 2.0.36
- **Migrations**: Alembic 1.14, async, autogenerate. Migrations live at `clinic-cms/alembic/versions/NNNN_*.py`. Numbering is sequential (e.g. `0006_setup_rbac.py`, `0007_seed_permissions_and_roles.py`).
- **Cache + queue**: Redis 7 (`redis:7-alpine`); `redis>=5.2` client; `arq>=0.26` for background jobs (worker entrypoint: `app.workers.scheduler.WorkerSettings`).
- **Auth**: JWT via `python-jose[cryptography]`; passwords with `passlib[bcrypt]`.
- **Validation/config**: Pydantic 2.10+ / pydantic-settings 2.6+.
- **Logging**: `structlog` 24.4+, `orjson` for serialization.
- **Rate limiting**: `slowapi` 0.1.9.
- **Lint/format**: `ruff` 0.8 (line-length 100, rules `E F I N W B UP SIM`, ignore `E501`).
- **Type check**: `mypy` 1.13.
- **Test**: `pytest` 8.3 + `pytest-asyncio` 0.24 (asyncio_mode = auto, session-scoped loop) + `pytest-cov` 6.0. Tests in `clinic-cms/tests/{unit,integration}/`.

### Frontend (`clinic-cms-web`)
- **Shell**: Tauri 2 (`@tauri-apps/api` 2.x, `@tauri-apps/plugin-sql`, `@tauri-apps/plugin-shell`)
- **UI**: React 18.3, Vite 5.3, TypeScript 5.4, Tailwind 3.4, Radix UI primitives + `lucide-react`
- **State**: `@tanstack/react-query` 5.x (server), `zustand` 5 (client)
- **Forms**: `react-hook-form` 7.74 + `zod` 3.25 + `@hookform/resolvers`
- **i18n**: `i18next` 23 + `react-i18next` 14 + browser language detector
- **Routing**: `react-router-dom` 6.30
- **Toasts**: `sonner` (preferred) + Radix Toast primitives
- **Test**: `vitest` 2.0 + `@testing-library/react` + `happy-dom`
- **Lint**: ESLint 8.57 + `@typescript-eslint`

### Custom/internal libraries
None. All dependencies are upstream OSS.

---

## Configuration Management

### Backend
- **Settings loader**: `pydantic-settings`. Env vars are the source of truth.
- **Local dev source**: `clinic-cms/docker/docker-compose.yml` (the `api` service env block).
- **Required env vars**:
  - `DATABASE_URL` — e.g. `postgresql+asyncpg://cms:cms@postgres:5432/cms`
  - `REDIS_URL` — e.g. `redis://redis:6379/0`
  - `JWT_SECRET` — HS256 signing key (rotate per environment; never commit a real value)
  - `ENVIRONMENT` — `development` | `staging` | `production`
  - `DEBUG` — `"true"` / `"false"`

### Frontend
- Vite env vars in `.env.local` (gitignored). Tauri config in `clinic-cms-web/src-tauri/tauri.conf.json`.

---

## Build & Test Commands

> All commands run from inside the source repo (`clinic-cms` or `clinic-cms-web`), **not** this workspace.

### Backend (`clinic-cms`)

```bash
# Bring up Postgres + Redis + API + Arq worker
cd docker && docker compose up -d

# Run a migration
docker exec clinic_cms_api alembic upgrade head

# Test suite (canonical — Postgres + Redis are required, mocks are not acceptable for integration)
docker exec clinic_cms_api pytest -q --tb=short

# Targeted test
docker exec clinic_cms_api pytest -q tests/integration/test_rbac_e2e_real_db.py

# Coverage
docker exec clinic_cms_api pytest -q --cov=app --cov-report=term-missing

# Lint / type-check
docker exec clinic_cms_api ruff check app tests
docker exec clinic_cms_api mypy app
```

`/auto-build test` and `/auto-build check` auto-detect this stack — prefer those over raw commands inside agents.

### Frontend (`clinic-cms-web`)

```bash
npm install --silent
npm run dev                  # Vite dev server (browser only, no Tauri shell)
npm run tauri:dev            # Tauri desktop app (dev mode)
npm test --silent            # vitest run
npm run test:coverage        # vitest with v8 coverage
npm run lint
npm run type-check
npm run build                # tsc + vite build
npm run tauri:build          # Tauri production bundle
```

### Token-optimization rules (per CLAUDE.md)
- Never `cat`/`tail -f` log files. Filter first: `grep ERROR app.log | tail -20`.
- Use `--quiet`/`--silent`/`-q` flags on builds and installs.
- `docker logs --tail 50 --since 5m clinic_cms_api`.

---

## Database Schema Management

- **Tool**: Alembic (async).
- **Location**: `clinic-cms/alembic/versions/`
- **Naming**: `NNNN_<short_description>.py` — sequential integer prefix, e.g. `0006_setup_rbac.py`.
- **Audit trail**: `app/core/audit.py` listens to ORM events on models with `__auditable__ = True`. Excluded fields appear redacted as `"***"`.
- **RLS pattern**: see TASK-002 migrations for the canonical RLS-enable + policy block.
- **Seed UUIDs**: use `uuid.uuid5(uuid.NAMESPACE_OID, <stable-key>)` for deterministic IDs in seed data — **never** `uuid4()` at module load (TASK-004 review C2).

---

## Testing Strategy

| Layer | Location | Framework | Notes |
|---|---|---|---|
| Unit | `clinic-cms/tests/unit/` | pytest + mocks | OK to mock; pure logic only. |
| Integration (DB-backed) | `clinic-cms/tests/integration/` | pytest + real Postgres + Redis | **Do NOT mock DB or Redis here.** Run against the live `clinic_cms_postgres` / `clinic_cms_redis` containers. The reviewer rejects mock-only "integration" tests. |
| E2E | `clinic-cms/tests/integration/test_*_e2e_*.py` | `httpx.AsyncClient` against `app.main:app` | Exercise real router registration + middleware + DB + cache. Required for any new permission gate. |
| Frontend unit | `clinic-cms-web/src/**/*.test.{ts,tsx}` | vitest + Testing Library + happy-dom | |

Pattern reference: `clinic-cms/tests/integration/test_rbac_e2e_real_db.py` (TASK-004) is the canonical DB-backed e2e example.

---

## SonarQube

**Disabled.** No project key configured. Code quality is enforced by `ruff` + `mypy` + the Code Review Agent + test pass rate. Re-enable per the original template instructions if/when a project key is provisioned.

---

## Agent Model Configuration

```yaml
agent-models:
  code-implementation: sonnet    # default
  code-review: opus              # default — needs deep reasoning for security/RLS/RBAC review
  test: sonnet                   # default
  documentation: haiku           # default
  manager: opus                  # default
```

No project-specific overrides today. Override here if a particular agent should run on a different model for this project.

---

## Quality Gates

Read by every agent at runtime.

### Code coverage
- **New code**: ≥ 80%
- **Overall**: ≥ 70%

### Code review
- **Max iterations**: 3 (task flagged as stuck after this — manager intervenes)
- **Auto-approve minor-only**: false

### Testing
- **Required pass rate**: 100% (zero failures before DOCUMENTING)
- **Unit tests required**: true
- **Integration tests required**: true (must be real-DB, not mocks)
- **E2E tests required**: true for any new permission gate or cross-module flow

### Build
- **Build must pass**: true (`/auto-build check`)
- **Lint must pass**: true (`ruff check app tests`)

### SonarQube
- Disabled (no project key).

---

## Project-Specific Overrides (deviations from defaults)

1. **DB driver**: `asyncpg` only (not psycopg2). All SQLAlchemy sessions are `AsyncSession`. Sync DB code is not allowed.
2. **Migrations as truth**: SQL DDL is generated by Alembic. Hand-written DDL in deliveries (`docs/tasks/TASK-XXX/deliveries/sql-scripts/`) is for ops/DBA reference only — Alembic is canonical.
3. **Seed UUIDs**: deterministic (`uuid5`) only — see TASK-004 C2.
4. **Integration tests**: must hit real Postgres + Redis. Mock-only "integration" tests will be rejected at review (TASK-004 iteration 1 precedent).
5. **Audit exclude**: any `__auditable__ = True` model with secret columns must declare `__audit_exclude__: ClassVar[frozenset[str]]`. See `code-implementation.md`.
6. **Git commits**: NO `Co-Authored-By` tags (CLAUDE.md). Conventional commits only (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
7. **Frontend storage**: SQLite via `@tauri-apps/plugin-sql` for offline mirror; Postgres remains the system of record. Sync layer is TASK-016/017 territory.

---

## Common Patterns

**Permission gate on a route:**
```python
from fastapi import APIRouter, Depends
from app.core.permissions import require_permission

router = APIRouter(prefix="/api/v1/patients")

@router.post("", dependencies=[Depends(require_permission("patient.write"))])
async def create_patient(...): ...
```

**Auditable model with secret column:**
```python
from typing import ClassVar
class User(BaseEntity):
    __auditable__ = True
    __audit_exclude__: ClassVar[frozenset[str]] = frozenset({"password_hash", "mfa_secret"})
```

**DB-backed e2e test skeleton:**
```python
async def test_role_gates_route(async_client, db_session):
    # log in as user without permission → 403
    # assign role with permission → 200 on next request
    # verify Redis cache invalidation
```

Reference: `clinic-cms/tests/integration/test_rbac_e2e_real_db.py`.

---

## Document Maintenance

**Last updated**: 2026-04-27 (post TASK-004 RBAC delivery).
**Update triggers**: new module added, new env var, stack version bump, agent-model change, quality-gate change. Do **not** update for routine task completion.
