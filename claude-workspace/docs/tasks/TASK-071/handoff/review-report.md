# TASK-071 Code Review Report — Round 1

**Reviewer**: Code Review Agent
**Date**: 2026-05-31
**Verdict**: **CHANGES_REQUESTED**
**Iteration**: 1 of 3
**SonarQube**: DISABLED (skipped)

---

## Scope Reviewed

- **BE** `clinic-cms-merge` @ `feature/TASK-071-superadmin-analytics`
  - `app/modules/superadmin/analytics.py` (325 lines, new)
  - `app/modules/superadmin/api/routes.py` (+3 analytics endpoints)
- **FE** `clinic-cms-web` @ `feature/TASK-071-superadmin-analytics` (base `feature/TASK-070-superadmin-fe`)
  - `src/pages/superadmin/SuperAdminAnalyticsPage.tsx` (new)
  - `src/modules/superadmin/{api.ts,types.ts}`, `src/router/index.tsx`, `src/components/shell/Sidebar.tsx`

---

## Test Results

| Suite | Result |
|-------|--------|
| BE unit `test_superadmin_analytics.py` + integration `test_superadmin_analytics_e2e.py` | **33 passed** (docker `clinic_cms_w2e_api`) |
| FE `SuperAdminAnalyticsPage.test.tsx` (vitest) | **17 passed** |
| FE `tsc --noEmit` | 0 new errors from TASK-071 (11 total, **all pre-existing on base branch**, confirmed) |

---

## Security Review — PASS

| Check | Result |
|-------|--------|
| All 3 analytics endpoints behind `require_superuser` | PASS — router-level `dependencies=[Depends(require_superuser)]` (routes.py:45). Integration tests confirm **403** for non-superuser on all 3. |
| SQL injection via `granularity` | SAFE — allowlist in `_date_trunc_expr` (`{day,week,month,year}`, else falls back to `day`). Only validated enum strings are interpolated into `text()`. Unit test `test_unknown_granularity_falls_back_to_day` covers it. |
| SQL injection via `metric` | SAFE — allowlist `{visits,revenue,new_patients}`, else `visits`. Test `test_unknown_metric_defaults_to_visits`. |
| SQL injection via `sort_by` | SAFE — allowlist `{visits,revenue}`, bound as `:order_col` parameter inside `ORDER BY CASE`. Test `test_unknown_sort_falls_back_to_revenue`. |
| `clinic_id` | SAFE — typed `UUID`, passed as bind param. |
| Cross-tenant correctness | OK — relies on RLS-bypass GUC set by TenancyMiddleware for superusers (same pattern as TASK-070). |
| FE route guard | OK — `<RequireSuperuser>` wraps `/superadmin/analytics`. |

No raw string interpolation of user input reaches SQL. Injection surface is clean.

---

## Findings

### 1. [MAJOR] Date-range max (365 days) not enforced; no `date_from <= date_to` validation

Task requires: *"Custom range: date picker từ–đến (tối đa 365 ngày)"*. Neither the route nor `analytics.py` caps the range or validates ordering.

- A superuser can request an arbitrary span (e.g. 10 years) → unbounded scans on `visit` / `invoice`. Blast radius is limited to superusers, but it is a stated acceptance requirement and a real performance concern.
- `date_from > date_to` silently returns empty results instead of HTTP 422.

**Required fix**: Enforce `date_from <= date_to` and `(date_to - date_from).days <= 365` in the route layer (raise 422 / ValidationError). Apply to all 3 analytics endpoints. Add a unit/integration test for the rejection path.

### 2. [MINOR] `limit` param unbounded on `/analytics/clinics`

`limit: int = Query(20)` has no upper bound. A superuser could pass `limit=10000000`.
**Fix**: add `Query(20, ge=1, le=200)` (or similar) on `limit`, and `ge=1` guard.

### 3. [MINOR] Revenue bucketed by `invoice.updated_at` (paid-proxy)

Disclosed in handoff (invoice has no `paid_at`). `updated_at` mutates on any later change (e.g. refund), so revenue can land in the wrong time bucket. `status='paid'` correctly excludes `partially_paid`/`refunded`. Acceptable as a **documented limitation** — leave a code comment / follow-up, no change required this round, but Test/Docs should record it.

### 4. [MINOR / observation] Duplicated average computation across BE & FE

FE stat cards "TB/ngày" / "TB/tháng" recompute from `overview.visits / daysInRange` client-side, while the clinic table uses BE-computed averages (both use the `30.44` month constant). Values should align; just two sources of truth. No change required.

### 5. [OBSERVATION — manager] Branch base / diff hygiene

`git diff main...feature/TASK-071-superadmin-analytics` includes **unrelated modules** (tags, `0037_create_entity_tags` migration, inventory, services). The branch was cut from a base ahead of `main`, not clean `main`. Not a TASK-071 code defect, but the eventual PR must target the correct base so it doesn't drag in unrelated work. Flagging to manager.

---

## Correctness Verification (passed)

- Model columns confirmed against source: `Visit.status` StrEnum `COMPLETED`, `Visit.completed_at`, soft-delete `is_deleted` via BaseEntity; `Invoice.status` includes `paid`, `Invoice.grand_total`/`updated_at`; `Patient.created_at`/`is_deleted`/`clinic_id`; `Clinic.code`/`name`/`is_deleted`. All SQL references valid.
- `SYSTEM` clinic excluded via `c.code <> :sys` in every query. Correct.
- `avg_revenue_per_visit` div-by-zero guarded (`visits > 0`). `days_in_range` min-1 guard prevents div/0. Tests confirm.
- `_date_trunc_expr` emits valid PostgreSQL (`DATE(col)` for day, `DATE_TRUNC('week'|...)` otherwise).

---

## Decision

**CHANGES_REQUESTED** — Finding #1 (365-day cap + date ordering validation) is an unimplemented stated acceptance requirement and a performance concern. Finding #2 (bound `limit`) should be fixed in the same pass. Findings #3–#5 are minor/observational and do not block on their own.

Hand back to Implementation. See `review-to-implementation.md`.

---

# TASK-071 Code Review Report — Round 2

**Reviewer**: Code Review Agent
**Date**: 2026-05-31
**Verdict**: **APPROVED**
**Iteration**: 2 of 3
**SonarQube**: DISABLED (skipped)

## Scope Reviewed (round 2 — delta only)

Fix commit `1f82ca7` on `feature/TASK-071-superadmin-analytics` (BE only):
- `app/modules/superadmin/api/routes.py` (+17 lines)
- `tests/unit/test_superadmin_analytics.py` (+42 lines, 5 new tests)

FE branch unchanged since round 1 (last FE commit `dc41068`).

## Round-1 Blockers — Verification

| # | Round-1 finding | Status | Evidence |
|---|-----------------|--------|----------|
| 1 [MAJOR] | 365-day cap + `date_from <= date_to` not enforced | **FIXED** | New `_validate_date_range()` helper raises `HTTPException(422)` for `date_from > date_to` and for `(date_to - date_from).days > 365`. Called in all 3 endpoints (`analytics_overview`, `analytics_timeseries`, `analytics_clinics`). Confirmed in diff. |
| 2 [MINOR] | `limit` unbounded on `/analytics/clinics` | **FIXED** | `limit: int = Query(20, ge=1, le=200)` — lower + upper bound applied. |

Findings #3–#5 (round 1) were minor/observational and do not block; #3 (revenue bucketed by `invoice.updated_at`) and #5 (branch base hygiene) carried forward to Test/Docs and Manager respectively.

## Quick Scan — remaining Query params

Remaining unbounded Query params are string enums already protected by service-layer allowlists (verified round 1): `metric`, `granularity`, `sort_by`. No new unbounded numeric/range params. No new concerns.

## Test Results

| Suite | Result |
|-------|--------|
| BE unit `test_superadmin_analytics.py` + integration `test_superadmin_analytics_e2e.py` | **38 passed, 0 failed** (docker `clinic_cms_w2e_api`) — was 33, +5 new validation tests |
| FE `SuperAdminAnalyticsPage.test.tsx` + `superadminApi.test.ts` (TASK-071 deliverable) | **29 passed, 0 failed** |
| FE `SuperAdminDashboardPage.test.tsx` | passing |

New validation tests cover: `date_from > date_to` → 422, range > 365d → 422, valid range, same-day boundary, exactly-365-day boundary.

## Pre-existing FE test failure (NOT a blocker for TASK-071)

`src/tests/superadmin/RequireSuperuser.test.tsx` — 3 of 4 tests FAIL (render empty `<div />`).

- **Root cause**: commit `8ed9af3` (`fix(auth): add isHydrated flag`) added `if (!isHydrated) return null;` to `RequireSuperuser.tsx`, but this test's `useAuthStore.setState(...)` fixtures never set `isHydrated: true`, so the guard short-circuits to `null`.
- **Not caused by TASK-071**: this test file belongs to TASK-070 (route guard), was last modified by TASK-070 commit `a260390`, and is **not** touched on the TASK-071 branch. TASK-071's FE change is the analytics page (`dc41068`) only.
- **Not masking a real bug**: the guard component change is correct; only the test fixture is stale.
- **Action**: logged as a follow-up (test-fixture fix: add `isHydrated: true` to the 3 authenticated setState blocks). Recommend the Test agent flag it; it should not block TASK-071.

## Decision

**APPROVED** — both round-1 blockers (#1 date-range validation, #2 bounded `limit`) are resolved, all 38 BE tests pass, all 29 TASK-071 FE tests pass. Advancing to **IN_TESTING**. See `review-to-test.md`.
