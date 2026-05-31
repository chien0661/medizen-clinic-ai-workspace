# TASK-038 Q.1 — Implementation → Review handoff

**Phase**: Q.1 only (JWT_SECRET hardening)
**Scope**: standalone <1-day quick-win, isolated from rest of TASK-038 (MFA, anomaly cron, PII lifecycle, etc.)
**Implementer**: Manager (direct edit, scope too small to justify spawning Implementation agent)
**Date**: 2026-05-01

## Files modified

| File | Change |
|------|--------|
| `clinic-cms/app/core/config.py` | Added `_DEV_PLACEHOLDER_JWT_SECRET` (49 chars) constant + `_PLACEHOLDER_JWT_SECRETS` frozenset (3 entries); bumped `Field(min_length=8 → min_length=32)`; added `model_validator(mode="after")` that rejects placeholder secrets when `ENVIRONMENT != "development"` |
| `clinic-cms/tests/unit/test_config.py` | Replaced legacy 12/27-char secrets with `TEST_SECRET` (35 chars); added 5 new test groups (min_length, legacy short rejection, long placeholder allowed in dev, parametrized rejection in non-dev, default rejected in production) |
| `clinic-cms/.env.example` | Added 3-line comment block instructing how to generate a strong secret + warning |
| `clinic-cms/docker/docker-compose.yml` | Bumped `JWT_SECRET: dev-secret-change-me` (19 chars) → `dev-secret-change-me-must-be-32-or-more-chars` (45 chars) for both `api` + `worker` services |

## Behavior

| Env | JWT_SECRET | Result |
|-----|------------|--------|
| `development` | any ≥32-char string (incl. placeholders) | OK |
| `development` | <32-char string | `ValidationError: string_too_short` |
| `staging`/`production`/`test` | `change-me-in-production` (legacy) | `ValidationError: string_too_short` (fails on length first) |
| `staging`/`production`/`test` | any of the 3 known placeholders ≥32 chars | `ValidationError: JWT_SECRET is set to a placeholder value...` |
| `staging`/`production`/`test` | strong non-placeholder ≥32 chars | OK |

## Standalone verification

Ran 7-case manual validation script (since local Python is 3.10 — repo requires 3.11 for `datetime.UTC` in `app.modules.appointments.schemas`, blocking `pytest` import via `conftest.py → app.main`):

```
Test 1 pass: dev allows long placeholder
Test 2 pass: production rejects placeholder
Test 3 pass: short secret rejected (min_length=32)
Test 4 pass: strong secret accepted in production
Test 5 pass: _DEV_PLACEHOLDER_JWT_SECRET rejected in production
Test 6 pass: default works in dev (module load doesn't break)
Test 7 pass: default rejected in production

All 7 tests passed.
```

## Known limitation

`pytest tests/unit/test_config.py` cannot be run on this dev workstation due to Python 3.10 ↔ 3.11 mismatch (unrelated to this change — pre-existing in repo via `from datetime import UTC`). Docker Desktop is installed but daemon not running. Test execution will happen in:
- CI (Python 3.11 container)
- Docker Compose (`docker compose -f docker/docker-compose.yml up`)

Reviewer should re-run pytest in Docker if local 3.11 is unavailable.

## Review checklist

- [ ] Validator logic correct (placeholder set complete, env check correct)
- [ ] Error message includes both the actual secret value AND the environment name (helps ops debugging)
- [ ] No infinite loops or import cycles introduced
- [ ] Tests cover: dev-allow, non-dev-reject (parametrized 3 envs × 2 placeholders = 6 cases), min_length=32, default-rejected-in-prod
- [ ] `.env.example` comment is clear + actionable
- [ ] `docker-compose.yml` change doesn't break local dev startup (45 chars > 32, env="development" → OK)
- [ ] No regression on existing tests (security/auth/refresh tests use `settings.JWT_SECRET` — unchanged behavior at runtime since prod-strong secrets still pass)
- [ ] No unused imports, no dead code

## Decision points for reviewer

1. **Should the validator also reject `JWT_ALGORITHM != "HS256"`?** Spec NFR-028 says HS256 OK for v1, RS256 for v2. Current change does NOT touch algorithm validation. Recommend defer.
2. **Should we rotate `dev-secret-change-me-must-be-32-or-more-chars` to a randomly-generated value in `docker-compose.yml`?** Current value is itself a placeholder pattern (could be added to `_PLACEHOLDER_JWT_SECRETS`). Trade-off: developer ergonomics vs strict consistency. Recommend leave as-is + add comment that prod must override.
