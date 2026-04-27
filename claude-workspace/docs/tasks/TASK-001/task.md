---
id: TASK-001
type: feature
title: Foundation — Project Skeleton, Docker Compose, Base Models, Alembic
status: DONE
priority: High
assigned: ""
created: 2026-04-26
updated: 2026-04-26
branch: "feature/task-001-foundation"
jira_key: ""
tags: [foundation, infrastructure, sprint-0]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#3-database-foundation"
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "../../../../docs/clinic_management_business_analysis.md#312-roadmap-sprint-0-1-foundation"
---

# TASK-001: Foundation — Project Skeleton, Docker Compose, Base Models, Alembic

## Description

Khởi tạo project `clinic-cms` (Python 3.11 + FastAPI + SQLAlchemy 2.x async + Alembic + PostgreSQL 15 + Redis + Arq). Setup docker-compose dev stack, base SQLAlchemy mixins (Timestamp/SoftDelete/Tenant/Audited/Versioned), exception handlers, config loader, structured logging, CI skeleton. Đây là nền tảng cho mọi task sau.

## Requirements

- [ ] `pyproject.toml` với deps: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings, python-jose, passlib[bcrypt], arq, redis, httpx, structlog, pytest, pytest-asyncio
- [ ] `docker/docker-compose.yml` với services: postgres:15-alpine, redis:7-alpine, api (FastAPI + uvicorn --reload), worker (Arq) — verbatim theo §23 System Design
- [ ] `Dockerfile` multi-stage (builder + runtime) cho api & worker
- [ ] `app/main.py` FastAPI entrypoint với `/health` endpoint trả `{"status": "ok"}`
- [ ] `app/core/config.py` Pydantic Settings (DATABASE_URL, REDIS_URL, JWT_SECRET, ACCESS/REFRESH expiry)
- [ ] `app/core/db.py` async engine + `AsyncSessionLocal` + ContextVars `current_clinic_id` / `current_user_id` + `get_db()` dependency set RLS context
- [ ] `app/core/base_model.py` `Base`, `TimestampMixin`, `SoftDeleteMixin`, `TenantMixin`, `AuditedMixin`, `VersionedMixin`, `BaseEntity`
- [ ] `app/core/exceptions.py` custom exceptions + global handlers (response shape `{error: {code, message, details}, meta}`)
- [ ] `alembic.ini` + `alembic/env.py` async + auto-import models
- [ ] Migration `0001_create_clinic_and_users.py` (clinic + clinic_settings tables — minimal để các task sau migrate được)
- [ ] PostgreSQL extensions seeded: `uuid-ossp`, `pgcrypto`, `unaccent`, `pg_trgm`, `btree_gin`
- [ ] `.env.example` với mọi env var
- [ ] `.dockerignore`, `.gitignore`
- [ ] README.md cơ bản: setup, run, test
- [ ] GitHub Actions CI: lint (ruff), type check (mypy), test (pytest), build docker

## Acceptance Criteria

- [ ] `docker compose up -d` boots postgres + redis + api + worker không lỗi
- [ ] `curl http://localhost:8000/health` trả 200 + `{"status":"ok"}`
- [ ] `docker compose exec api alembic upgrade head` chạy thành công
- [ ] `docker compose exec api pytest` chạy được (kể cả 0 test)
- [ ] PostgreSQL có các extension `uuid-ossp`, `pgcrypto`, `unaccent`, `pg_trgm`, `btree_gin` enabled
- [ ] CI green trên PR

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-001/refs/`
- **Code**: `clinic-cms/` (foundation files)
- **Tests**: `docs/tasks/TASK-001/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-001/handoff/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Blocker for TẤT CẢ task khác. Phải merge trước. RLS chưa bật ở task này — chỉ tạo helper context. RLS policies sẽ tạo ở migration `0014_setup_rls_policies.py` (TASK-002).

**2026-04-26 — Code Review verdict: CHANGES_REQUESTED.** 11 issues (2 CRITICAL, 5 MAJOR, 3 MINOR, 1 NIT). Foundation is structurally sound but blocked by: (1) hardcoded test DB hostname (CI will fail); (2) `.dockerignore` vs `Dockerfile` contradiction (build will fail); (3) no logging in unhandled exception handler; (4) missing `MetaData(naming_convention=...)` (downstream §2.1 violations); (5) structlog ProcessorFormatter chain incomplete; (6) deprecated session-scoped event_loop fixture. See `handoff/review-report.md` (full) and `handoff/review-to-implementation.md` (action list).

**2026-04-26 — Code Review iter 2 verdict: APPROVED.** All 8 fixes verified (issues 1-7, 10); 3 deferrals (issues 8, 9, 11) sensible — folded into TASK-002 follow-up. Verifications: `pytest -q` 14/14, `ruff check app tests` clean, `alembic upgrade head` no-op, naming convention applied to clinic table (`pk_clinic`, `ix_clinic_code`, `ix_clinic_is_active`) and inherited by all future autogen constraints. Minor non-blocking drift: `ix_clinic_is_active` exists in DB but not declared on model — fold into TASK-002. Moving to IN_TESTING. See `handoff/review-report.md` § Iteration 2.

## Blockers

None

**2026-04-26 — Testing Completed.** 37/37 tests pass (100%). 23 new tests added (exceptions, context-vars, alembic idempotency). Coverage: app/core/exceptions 100%, app/core/base_model 100%, app/core/config 100%, overall 67%. All acceptance criteria verified. Moving to DOCUMENTING.

**DONE 2026-04-26** — 37/37 tests, coverage 67% overall (100% on base_model/config/exceptions). Foundation merged on feature/task-001-foundation. Deliverables: foundation-functional-design.md (Vietnamese, 400 lines), foundation-api.md (2 endpoints), SQL migration with postgres-init.sql. Deferrals to TASK-002: request_id middleware, UUID PK mixin extraction, walk_packages predicate tightening.
