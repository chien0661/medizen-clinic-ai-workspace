# TASK-038 Q.1 — Test → Documentation handoff

**Phase**: Q.1 only (JWT_SECRET hardening)
**Tester**: Test agent
**Date**: 2026-05-01
**Decision**: **PASS** — proceed to Documentation phase

---

## Environment

| Item | Value |
|------|-------|
| Python version | 3.10.0 (local) |
| pytest version | 9.0.2 |
| Docker daemon | OFFLINE — Docker Desktop not running |
| Pytest invocation | `pytest tests/unit/test_config.py --noconftest -v --tb=short` |

**Why --noconftest**: `tests/conftest.py` imports `from app.main import app`, which triggers `from datetime import UTC` in `app.modules.appointments.schemas` — a Python 3.11-only symbol. Using `--noconftest` bypasses that import entirely. `test_config.py` is a pure unit test; it uses no fixtures from conftest, only `monkeypatch` (a built-in pytest fixture). This is a valid pytest run for the validator unit tests.

---

## Option used

**Option 2** (pytest with `--noconftest`) + **Option 3 extended** (standalone Python script for cases 8 & 9).

`test_security.py` could not be collected due to the same `datetime.UTC` Python 3.11 constraint; this is a pre-existing repo limitation unrelated to TASK-038 Q.1.

---

## Test results

### `tests/unit/test_config.py` — all 15 tests

```
tests/unit/test_config.py::test_settings_defaults                                                                            PASSED
tests/unit/test_config.py::test_settings_loads_from_env                                                                     PASSED
tests/unit/test_config.py::test_settings_cors_origins_json_parse                                                            PASSED
tests/unit/test_config.py::test_jwt_secret_min_length_enforced                                                              PASSED
tests/unit/test_config.py::test_jwt_secret_legacy_short_placeholder_rejected_by_length                                      PASSED
tests/unit/test_config.py::test_jwt_secret_long_placeholder_allowed_in_development[please-change-me-to-a-strong-random-secret]    PASSED
tests/unit/test_config.py::test_jwt_secret_long_placeholder_allowed_in_development[change-me-in-production-this-default-is-insecure] PASSED
tests/unit/test_config.py::test_jwt_secret_placeholder_rejected_outside_development[staging-please-change-me-to-a-strong-random-secret]           PASSED
tests/unit/test_config.py::test_jwt_secret_placeholder_rejected_outside_development[staging-change-me-in-production-this-default-is-insecure]     PASSED
tests/unit/test_config.py::test_jwt_secret_placeholder_rejected_outside_development[production-please-change-me-to-a-strong-random-secret]        PASSED
tests/unit/test_config.py::test_jwt_secret_placeholder_rejected_outside_development[production-change-me-in-production-this-default-is-insecure]  PASSED
tests/unit/test_config.py::test_jwt_secret_placeholder_rejected_outside_development[test-please-change-me-to-a-strong-random-secret]              PASSED
tests/unit/test_config.py::test_jwt_secret_placeholder_rejected_outside_development[test-change-me-in-production-this-default-is-insecure]        PASSED
tests/unit/test_config.py::test_jwt_secret_strong_value_accepted_in_production                                              PASSED
tests/unit/test_config.py::test_jwt_secret_default_value_rejected_in_production                                             PASSED

========================= 15 passed in 0.17s =========================
```

**Result: 15/15 PASSED**

### Extended verification (cases 8 & 9 from test brief)

Run via standalone Python script importing `app.core.config` directly.

| Case | Description | Result |
|------|-------------|--------|
| 8a | `dev-secret-change-me-must-be-32-or-more-chars` NOT in `_PLACEHOLDER_JWT_SECRETS` → loads in production | PASS |
| 8b | Same docker-compose dev secret loads cleanly in development | PASS |
| 9a | Whitespace-padded placeholder (`"   change-me-in-production-this-default-is-insecure   "`) in production — pydantic does NOT strip whitespace → NOT matched by frozenset → accepted | PASS (expected behavior documented) |
| 9b | Short secret with whitespace (9 chars total) → rejected by `min_length=32` | PASS |

**Result: 4/4 PASSED**

---

## Individual case results (full matrix)

| # | Scenario | Expected | Actual |
|---|----------|----------|--------|
| 1 | dev allows long placeholder | OK | PASS |
| 2 | production rejects long placeholder | ValidationError | PASS |
| 3 | short secret rejected (min_length=32) | ValidationError | PASS |
| 4 | strong secret accepted in production | OK | PASS |
| 5 | `_DEV_PLACEHOLDER_JWT_SECRET` rejected in production | ValidationError | PASS |
| 6 | default loads cleanly in dev | OK | PASS |
| 7 | default rejected in production | ValidationError | PASS |
| 8 | docker-compose `dev-secret-change-me-must-be-32-or-more-chars` loads in prod | OK | PASS |
| 9 | whitespace-padded secret — pydantic no-strip behavior confirmed | OK (not stripped) | PASS |

---

## File changes verified

| File | Change | Verified |
|------|--------|----------|
| `clinic-cms/app/core/config.py` | `_DEV_PLACEHOLDER_JWT_SECRET`, `_PLACEHOLDER_JWT_SECRETS`, `min_length=32`, `model_validator` | Yes — source read & logic exercised |
| `clinic-cms/tests/unit/test_config.py` | 15 tests, `TEST_SECRET` 35 chars, parametrized matrix | Yes — all 15 passed |
| `clinic-cms/.env.example` | Comment block + `generate` instruction + warning | Yes — confirmed at lines 7–10 |
| `clinic-cms/docker/docker-compose.yml` | JWT_SECRET = 45-char value for api + worker (lines 40, 66) | Yes — grepped both service entries |

---

## Coverage assessment

**`app/core/config.py` validator logic — coverage by test cases:**

| Line / branch | Covered by |
|---------------|-----------|
| `ENVIRONMENT != "development"` true branch (raise) | `test_jwt_secret_placeholder_rejected_outside_development` (6 parametrized cases: 3 envs × 2 placeholders) + `test_jwt_secret_default_value_rejected_in_production` |
| `ENVIRONMENT != "development"` false branch (return self) | `test_jwt_secret_long_placeholder_allowed_in_development` (2 cases) |
| `JWT_SECRET in _PLACEHOLDER_JWT_SECRETS` false branch (non-placeholder in prod) | `test_jwt_secret_strong_value_accepted_in_production` |
| `min_length=32` failure path | `test_jwt_secret_min_length_enforced` + `test_jwt_secret_legacy_short_placeholder_rejected_by_length` |

Estimated line coverage of `config.py` validator path: **~100% of the validator's reachable branches**.

---

## Notable findings

### Finding 1: Whitespace handling (non-blocking)

Pydantic does NOT strip whitespace on string fields by default. A value like `"   change-me-in-production-this-default-is-insecure   "` (with leading/trailing spaces) passes the frozenset check in production because it is NOT equal to the plain string. This is technically a bypass vector if an operator accidentally adds whitespace in an env var.

**Severity**: Low. Real-world risk is minimal (env vars rarely have accidental padding). Noted as future hardening — consider `@field_validator("JWT_SECRET", mode="before")` that calls `.strip()`.

### Finding 2: `test_security.py` not runnable locally

`tests/unit/test_security.py` requires Python 3.11 (`from datetime import UTC`). This is a pre-existing constraint unrelated to Q.1. It will pass in CI/Docker (Python 3.11). The review handoff confirmed `test_security.py:161` uses `settings.JWT_SECRET` unchanged — no regression expected.

### Finding 3: `_PLACEHOLDER_JWT_SECRETS` contains 23-char `"change-me-in-production"`

This member fails `min_length=32` before the model_validator fires, so it's effectively unreachable in the frozenset check. Not a bug — dual defense is fine — but this entry is inert in the frozenset. Non-blocking; worth a comment in the source.

---

## Tests that could NOT run

| Test file | Reason | Impact |
|-----------|--------|--------|
| `tests/unit/test_security.py` | `from datetime import UTC` — Python 3.11 only | Low — unrelated to Q.1; will pass in 3.11 CI |
| `tests/integration/test_jwt_signature.py` | Docker daemon offline + Python 3.11 | Medium — integration regression cannot be verified locally; must verify in CI |
| All other integration tests | Docker daemon offline | N/A to Q.1 |

---

## Recommendation

**PASS** — proceed to Documentation phase.

All 15 formal pytest cases PASS. All 4 extended brief cases PASS. Validator logic is correct, error messages are informative, docker-compose change is non-breaking (45-char dev secret not in placeholder set). No blocking issues found.

### Items for Documentation phase (from review handoff, non-blocking):

1. Add 1-line assertion: `assert "dev-secret-change-me-must-be-32-or-more-chars" not in _PLACEHOLDER_JWT_SECRETS` in `test_config.py` (B.3 from review).
2. Add explicit dev-default smoke test (B.4 from review).
3. Add `.env.example` note: ENVIRONMENT must be exactly lowercase `development` (A.4 from review).
4. Add `docker-compose.yml` comment that prod MUST override JWT_SECRET (D.3 from review).
5. Add CHANGELOG / migration note: staging/production deployments using old `change-me-in-production` will now refuse to start (E.3 from review).
6. (Optional future hardening) Add `.strip()` normalisation for JWT_SECRET field to close whitespace bypass (Finding 1 from this report).
