# Handoff: TASK-002 → Code Implementation Agent

**From**: Code Review Agent
**To**: Code Implementation Agent
**Status**: IN_PROGRESS
**Decision**: CHANGES_REQUESTED
**Iteration**: 1 → 2
**Date**: 2026-04-26

## Summary

Tenancy + RLS + audit shape is correct, all 84 tests pass and ruff is clean. However, two CRITICAL security gaps (unsigned JWT accepted in any environment; superuser DB role with FORCE RLS that doesn't actually force) and one MAJOR audit-listener correctness bug (fire-and-forget `create_task` from sync `after_flush`) must be fixed before this can become the multi-tenant foundation for TASK-003+.

Full report: `docs/tasks/TASK-002/handoff/review-report.md`.

## Required Changes (in priority order)

### CRITICAL — must fix
1. **C1 — Gate unsigned JWT and dev headers to development env only**
   - File: `app/core/tenancy.py:44-152`
   - Reject (or 501) JWT path when `settings.ENVIRONMENT != "development"` until TASK-003 lands real verification.
   - Same gate for `X-Clinic-Id` / `X-User-Id` dev headers.
   - Add a unit test that `ENVIRONMENT=production` + unsigned JWT → 401/501.

2. **C2 — Enforce non-superuser app role + document production deploy**
   - Add startup check in `app/main.lifespan` (or `app/core/db_security.py`): `SELECT usesuper FROM pg_user WHERE usename = current_user`. Fail fast if `usesuper = true` AND env != development.
   - Add migration `0004_create_app_role.py` (idempotent) that creates `cms_app NOSUPERUSER NOBYPASSRLS LOGIN` and grants minimal table privileges, OR a documented bootstrap script in `docs/deployment/database-roles.md`.
   - Update `tests/integration/test_rls_isolation.py` to rely on the migration-created role, not the in-fixture create.

### MAJOR — must fix this iteration
3. **M1 — Drop `asyncio.create_task` in audit listener**
   - File: `app/core/audit.py:193-261`, `:280-329`
   - Make `_schedule_audit` synchronous: build the `AuditLog` object and call `session.add(record)` directly inside the sync `after_flush` listener. SQLAlchemy will include it in the next flush of the same session/transaction.
   - Remove `_get_auditable_session` (dead code) and the `asyncio.get_event_loop()` block.
   - Add an integration test that creates an `__auditable__` model, commits, and verifies the audit row is visible in the same transaction's reads.

4. **M2 — PII exclusion mechanism**
   - Add `__audit_exclude__: ClassVar[frozenset[str]] = frozenset()` support in `_model_to_dict()` and the update-diff loop in `_after_flush`.
   - Document the pattern in `audit.py` module docstring AND add a note in `.claude/agents/code-implementation.md` so TASK-005 (User) excludes `password_hash`, `mfa_secret`, `refresh_token_hash`.
   - Test: a sample model with an excluded field is audited without that field.

5. **M3 — Diff calc handles JSONB / Mutable**
   - Document limitation in `audit.py` docstring (in-place dict/list mutation requires `MutableDict.as_mutable`).
   - Add unit test for `None → value` and `value → None` transitions to confirm they are captured.

6. **M4 — Migration 0002 idempotent triggers**
   - `DROP TRIGGER IF EXISTS … ON audit_log;` before each `CREATE TRIGGER`.
   - Re-run safety: verify `alembic downgrade -1 && alembic upgrade head` is clean.

7. **M5 — CI runs `alembic upgrade head` before pytest**
   - Add the step to `.github/workflows/ci.yml` (create the file if missing).
   - Add a step to bootstrap `cms_app` role idempotently (psql -c).

### MINOR — fix or open follow-up tickets
- m1: rename helper to clarify NULL allowance is audit-log-only, OR add strict variant. (Recommend strict variant for TASK-005+ business tables.)
- m2: change `audit_log.user_agent` to `sa.Text` (no length cap).
- m4: flag `/` whitelist for revisit when SPA mounts.
- m5: remove `_get_auditable_session` dead code (rolled into M1).

### NIT — at your discretion
- Empty `if TYPE_CHECKING: pass` in `audit.py`.
- Remove unused `enable_rls_sql` / `disable_rls_sql` legacy helpers in `rls.py`.

## What's already good (do not change)
- TASK-001 deferral closure (`UUIDPrimaryKeyMixin`, `walk_packages` predicate, `request_id` middleware) — all clean.
- Append-only triggers + integration test pattern (fresh session per assert).
- Whitelist regex resists path-traversal bypass.
- Middleware wiring order in `main.py`.
- Ruff clean, naming conventions applied.

## Re-review checklist (for iteration 2)

- [ ] `ENVIRONMENT` gate active on JWT + dev headers; unit test proves prod rejects
- [ ] Startup superuser check; manual test by connecting as `cms` (superuser) in non-dev env should fail boot
- [ ] `cms_app` role migration or bootstrap doc exists
- [ ] Audit listener no longer uses `create_task`; new test proves audit row in same tx
- [ ] `__audit_exclude__` mechanism documented + tested
- [ ] Migration 0002 re-runnable
- [ ] CI yml runs migrations before tests
- [ ] All 84 tests still pass + new tests for the above

When done, update `task.md` status to `IN_REVIEW` and write `handoff/implementation-to-review-iter2.md` summarising what changed per this list.
