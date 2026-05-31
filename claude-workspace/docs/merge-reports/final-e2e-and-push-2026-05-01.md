# Final E2E + Fix + Push Report — 2026-05-01

**Executed by:** Claude Code (automated)
**Date:** 2026-05-01

---

## Migration Head

Alembic reached `0033_bhyt_fac_code_enc` (post all merges) as expected.
Note: Migration 0031 requires API+worker services stopped (maintenance window) — handled in this run.

---

## BE Unit Tests

**Result: 846 passed, 0 failed, 20 warnings**

### Bugs Fixed (Unit Tests)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 1 | `tests/unit/patients/test_patient_service.py` | `test_search_by_phone` expected `len==0` but `feat: f57bfde` re-enabled phone search via decrypt-then-filter | Updated assertion to `len==1` |
| 2 | `tests/unit/patients/test_patient_service.py` | `test_search_by_name_*` used old two-query `side_effect` pattern but service now uses single-query + Python filter | Rewrote 3 tests for `.scalars().all()` single-query pattern |
| 3 | `tests/unit/test_hr_service_logic.py` | `test_check_in_rejects_other_users_shift_id` mocked `db.get` but service uses `db.execute(select(...))` after FIX-4a (55da9c1) | Updated to `side_effect=[no_checkin, shift_result]` on `db.execute` |
| 4 | `tests/unit/test_search_service.py` | Multiple tests used old multi-query `side_effect` and `.all()` mock but `_search_patients` now calls `.scalars().all()` | Updated `_make_patient_row` (add missing fields) + all patient mocks |

---

## BE Integration Tests

**Targeted tests (post-merge features): 108+ passed**

### Bugs Fixed (Integration Tests + Service)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 5 | `app/modules/integrations/vss/api/routes.py` | POST-TASK-034 TODO never completed: `require_feature_stub("bhyt")` always allowed access, making `test_vss_integration_status_returns_404_when_flag_off` fail | Replaced all 4 usages with real `require_feature("bhyt")` |
| 6 | `tests/integration/test_vss_endpoints.py` | After fix #5, tests that expect 200 now needed bhyt flag=True | Added `patch("app.core.feature_flags._get_flag_value", return_value=True)` to fixture and cross-tenant test |

### Pre-existing failures (NOT fixed — documented)

- Integration tests using raw SQL INSERT into BYTEA encrypted columns (full_name, email, phone) — requires ORM TypeDecorator but tests bypass it. Affects: admin e2e, appointments, search endpoint, and many others. Root cause: TASK-037 P2 encryption preceded the integration test fixtures.
- JWT perms tests: MFA challenge triggered during test login (TASK-038 B.8 MFA merge). Not new.

---

## Playwright Smoke Tests

**38 passed, 7 skipped, 0 failed**

### Bug Fixed (FE)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 7 | `src/router/index.tsx` | `ProfilePage` declared twice (lines 67 and 219) — Babel threw "Identifier already declared" causing Vite 500 on `/src/router/index.tsx`, blank white page | Removed duplicate declaration at line 219 (introduced by TASK-038 B.14 merge) |

Also fixed: `vite.config.ts` server port aligned to 1420; `playwright.config.ts` baseURL aligned to 1420.

---

## Playwright Regression Tests

**85 passed, 4 skipped, 0 failed**

---

## Golden Path Smoke (5 scenarios — curl/httpx via BE)

| # | Scenario | Result |
|---|----------|--------|
| 1 | Health check `GET /health` | PASS (200 `ok`) |
| 2 | Patient search decrypt-then-filter `GET /patients/search?q=ngu&type=name` | PASS (200, 1 result) |
| 3 | BHYT settings `GET /settings/bhyt` | PASS (200, bhyt_enabled=False) |
| 4 | CmdK global search `GET /search?q=ngu&mode=bn` | PASS (200, 1 result) |
| 5 | Patient list `GET /patients?limit=5` | PASS (200, 5 patients) |

Note: VSS status endpoint returns 404 as expected (demo clinic bhyt_enabled=False).

---

## Bugs Fixed Summary

**7 total** (4 BE unit test stale mocks, 1 BE service TODO stub, 1 BE integration test mock, 1 FE router duplicate)

| Commit | Repo | Description |
|--------|------|-------------|
| `f0ec794` | BE | fix(post-merge): require_feature_stub → real bhyt gate + stale unit tests |
| `12c3ac5` | FE | fix(router): remove duplicate ProfilePage + vite port alignment |

---

## Push Results

| Repo | Remote | Result | Final SHA |
|------|--------|--------|-----------|
| BE (clinic-cms-merge) | `git@gitlab.com:clinic-cms/clinic-cms-be.git` | SUCCESS | `f0ec794e2d0b4f06fc568200ff3dbd1bb5d810d9` |
| FE (clinic-cms-web) | `git@gitlab.com:clinic-cms/clinic-cms-web.git` | SUCCESS | `12c3ac569157821d05f838531b60dab2f08a9666` |

---

## Verdict: SHIPPED
