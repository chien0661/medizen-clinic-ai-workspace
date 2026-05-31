# TASK-038 Q.1 — Review → Test handoff

**Phase**: Q.1 only (JWT_SECRET hardening)
**Reviewer**: Code Review agent
**Date**: 2026-05-01
**Decision**: **APPROVED** (with minor non-blocking notes for future polish)

---

## Files reviewed

1. `clinic-cms/app/core/config.py`
2. `clinic-cms/tests/unit/test_config.py`
3. `clinic-cms/.env.example`
4. `clinic-cms/docker/docker-compose.yml`
5. Cross-checked: `tests/integration/test_jwt_signature.py`, `test_auth_*.py`, `test_security.py`, `app/core/tenancy.py`, `app/core/security.py`

---

## A. Security correctness

| # | Item | Status | Note |
|---|---|---|---|
| A.1 | Placeholder set complete for the *known* repo-shipped values (3 entries) | ✅ | Covers `change-me-in-production`, `please-change-me-…`, and the new long default. |
| A.2 | `model_validator(mode="after")` runs AFTER field validation | ✅ | Verified by Pydantic v2 docs + impl handoff "Test 3" — short secret fails on `min_length=32` first. |
| A.3 | Echoing `self.JWT_SECRET!r` in error message safe | ✅ | Validator only fires when value ∈ public placeholder set → no real-secret leakage possible. |
| A.4 | `ENVIRONMENT == "development"` is the only "safe" comparison | ⚠️ | `"dev"`, `"DEV"`, `"local"`, `"Development"` (case-sensitive `case_sensitive=True`) are treated as production → correct strict default, but worth documenting. **Recommend** adding a sentence to `.env.example`: *"ENVIRONMENT must be exactly `development` (lowercase) to allow placeholder secrets — `dev`/`local` will be treated as production."* Non-blocking. |
| A.5 | Other commonly-leaked dev secrets (`secret`, `password`, `test`, `xxx…`) | ⚠️ | Not in the rejected set. Trade-off: those are <32 chars or rarely used as JWT secrets specifically. `min_length=32` already blocks the obvious ones. **Non-blocking**, but track as future hardening (consider entropy check via Shannon ≥3.5 in a v2 follow-up). |
| A.6 | Fail-fast at app startup (per AC) | ✅ | `settings = get_settings()` at module bottom (line 62) → raises `ValidationError` before FastAPI binds. |

---

## B. Test coverage

| # | Item | Status | Note |
|---|---|---|---|
| B.1 | All 6 new test cases meaningful + non-redundant | ✅ | min_length, legacy short reject, dev allows long placeholder, parametrized non-dev reject, strong-prod accepted, default-rejected-in-prod. |
| B.2 | Parametrized matrix 3 envs × 2 long placeholders = 6 cases | ✅ | `_LONG_PLACEHOLDERS` × `["staging","production","test"]`. Note: `_DEV_PLACEHOLDER_JWT_SECRET` is in `_LONG_PLACEHOLDERS`, so it IS covered by parametrization. |
| B.3 | Verify `dev-secret-change-me-must-be-32-or-more-chars` (docker-compose value) NOT in `_PLACEHOLDER_JWT_SECRETS` | ⚠️ | **Missing.** Recommend adding 1-line assertion in test_config.py to lock in the contract. Non-blocking but cheap. Suggested: `def test_docker_compose_dev_secret_not_in_placeholder_set(): assert "dev-secret-change-me-must-be-32-or-more-chars" not in _PLACEHOLDER_JWT_SECRETS`. |
| B.4 | Smoke test that bare `Settings()` instantiates with default + ENVIRONMENT=development at module import | ⚠️ | Implicitly covered by `from app.core.config import Settings` succeeding at top of `test_config.py` (which means `settings = get_settings()` at module load did NOT raise). **Recommend** an explicit one-liner: `def test_module_load_in_dev_with_defaults(monkeypatch): monkeypatch.setenv("ENVIRONMENT","development"); assert Settings(...).JWT_SECRET == _DEV_PLACEHOLDER_JWT_SECRET`. Non-blocking. |
| B.5 | Test names + docstrings clear | ✅ | All 6 tests follow consistent naming convention. |

---

## C. Backwards compatibility / regression

| # | Item | Status | Note |
|---|---|---|---|
| C.1 | Existing `tests/integration/test_auth_*.py` use `settings.JWT_SECRET` for HMAC sign/verify | ✅ | They run in container (ENVIRONMENT=development from docker-compose), so JWT_SECRET=`dev-secret-change-me-must-be-32-or-more-chars` (45 chars, NOT in placeholder set) → all pass. Verified usages at: `test_auth_logout.py:92`, `test_auth_refresh_rotation_real_redis.py:49,219`, `test_auth_service_coverage.py:109,364,503,528`, `test_auth_refresh.py:96`. |
| C.2 | `tests/integration/test_jwt_signature.py` uses `patch("app.core.tenancy.settings")` to flip ENVIRONMENT="production" | ✅ | The patch only changes `settings.ENVIRONMENT` at the consumer side; the original `settings` singleton was already validated at module-import time in dev → no startup re-trigger. Mock substitutes `JWT_SECRET=settings.JWT_SECRET` (same value). No regression. |
| C.3 | `tests/unit/test_security.py:161` — uses `settings.JWT_SECRET` | ✅ | Inherits dev secret from container env, unaffected. |
| C.4 | `Settings(JWT_SECRET="too-short-secret", ENVIRONMENT="development")` test now expects `ValidationError` (vs previous `min_length=8` would have allowed) | ✅ | New test `test_jwt_secret_min_length_enforced` covers this. |
| C.5 | Older test secrets (12/27-char) replaced with 35-char `TEST_SECRET` | ✅ | Consistent across the file. |

---

## D. Implementation quality

| # | Item | Status | Note |
|---|---|---|---|
| D.1 | Constant name `_DEV_PLACEHOLDER_JWT_SECRET` clear | ✅ | Acceptable. Alternative `_DEFAULT_JWT_SECRET_PLACEHOLDER` is also valid; current choice emphasises *intent* (dev-only) over *role* (default). Either works, no change needed. |
| D.2 | `_PLACEHOLDER_JWT_SECRETS` placement (module-level vs class-level) | ✅ | Module-level frozenset is fine — no monkey-patching needed in tests, immutable, no instance cost. Class-level would be slightly tidier but not material. |
| D.3 | `dev-secret-change-me-must-be-32-or-more-chars` in docker-compose itself a placeholder pattern | ⚠️ | **Intentional trade-off**: leaving it OUT of `_PLACEHOLDER_JWT_SECRETS` so `docker-compose up` still works in dev. Acceptable; documented in handoff "Decision points #2". Recommend a 1-line comment in `docker-compose.yml`: `# dev-only — production deployments MUST override JWT_SECRET via secrets manager`. |
| D.4 | No unused imports / no dead code | ✅ | Clean. |
| D.5 | No import cycles | ✅ | `_PLACEHOLDER_JWT_SECRETS` is module-local; not exported. |
| D.6 | `lru_cache` on `get_settings()` preserved | ✅ | Validator runs once at first call, cached afterwards. |

---

## E. Documentation

| # | Item | Status | Note |
|---|---|---|---|
| E.1 | `.env.example` instructs `python -c "import secrets; print(secrets.token_urlsafe(48))"` | ✅ | Correct: `token_urlsafe(48)` returns ~64-char URL-safe string, comfortably ≥32. |
| E.2 | `.env.example` ships `JWT_SECRET=please-change-me-to-a-strong-random-secret` | ✅ | A long-form placeholder that loads in dev but blows up in prod — exactly the desired UX. |
| E.3 | CHANGELOG / migration note for ops | ⚠️ | **Recommend** ops gets a heads-up: any staging/production deployment shipping the old `change-me-in-production` will now refuse to start. Trivial to fix at deploy time, but should be flagged in release notes. **Non-blocking** — Documentation agent can pick this up post-Test phase. |

---

## Decision

**APPROVED** — proceed to Test phase.

### Non-blocking polish items (pick up at Documentation phase, NOT before Test):

1. Add 1-line assertion that `dev-secret-change-me-must-be-32-or-more-chars` is NOT in `_PLACEHOLDER_JWT_SECRETS` (B.3).
2. Add explicit smoke test for dev-default module load (B.4).
3. Add comment in `.env.example` clarifying ENVIRONMENT must be exactly lowercase `development` (A.4).
4. Add comment in `docker-compose.yml` that dev secret MUST be overridden in prod (D.3).
5. Add CHANGELOG/migration note for ops team (E.3).

### Blocking items: **none.**

---

## Test phase notes

**Cannot run pytest locally** (Python 3.10/3.11 mismatch — pre-existing). Test agent should:

1. Run `docker compose -f docker/docker-compose.yml up -d postgres redis` then `docker compose exec api pytest tests/unit/test_config.py -v` (Python 3.11 in container).
2. Run full integration suite: `docker compose exec api pytest tests/ -v --tb=short` to confirm no regression in auth/JWT/refresh tests.
3. Manual smoke: `docker compose exec api python -c "from app.core.config import Settings; Settings(JWT_SECRET='change-me-in-production-this-default-is-insecure', ENVIRONMENT='production')"` — expect `ValidationError` with "placeholder" message.
4. Verify `docker compose up` still starts cleanly with new 45-char dev secret.

Pass criteria: all 13 tests in `test_config.py` PASS, no regressions in `test_auth_*` / `test_jwt_*` / `test_security.py`.
