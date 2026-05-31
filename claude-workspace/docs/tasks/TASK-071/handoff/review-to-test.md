# Handoff: Code Review → Test — TASK-071

**From**: Code Review Agent
**To**: Test Agent
**Date**: 2026-05-31
**Verdict**: APPROVED (round 2 of 3)
**Status transition**: IN_REVIEW → IN_TESTING

---

## Summary

TASK-071 (Super Admin Analytics) passed review on round 2. Both round-1 blockers are fixed:

1. **[MAJOR] Date-range validation** — `_validate_date_range()` now enforces `date_from <= date_to` and `(date_to - date_from).days <= 365`, raising HTTP 422. Wired into all 3 analytics endpoints.
2. **[MINOR] Bounded limit** — `/analytics/clinics` `limit` is now `Query(20, ge=1, le=200)`.

All 38 BE tests pass (23 unit + 15 integration). All 29 TASK-071 FE tests pass.

---

## Branches

- **BE**: `feature/TASK-071-superadmin-analytics` @ `clinic-cms-merge` (fix commit `1f82ca7`)
- **FE**: `feature/TASK-071-superadmin-analytics` @ `clinic-cms-web` (commit `dc41068`, unchanged since round 1)

## Endpoints to test

- `GET /api/v1/superadmin/analytics/overview`
- `GET /api/v1/superadmin/analytics/timeseries`
- `GET /api/v1/superadmin/analytics/clinics`

All behind `require_superuser`.

---

## Test focus areas

### Functional (acceptance criteria from task.md)
- Quick filters: Hôm nay / 7 ngày / 30 ngày / Tháng này / Quý này / Năm này
- "Năm này" → 12-point line chart (granularity=month)
- Custom range 90 days + granularity=week → ~13 points
- Filter by single clinic → only that clinic's data
- Clinic comparison table sortable by revenue / visits / avg
- Non-superuser → `/superadmin/analytics` redirects to `/dashboard` (and API returns 403)

### Validation (newly added — regression-verify)
- `date_from > date_to` → **422**
- range > 365 days → **422**
- exactly 365 days → **OK**
- same-day range → **OK**
- `limit` out of `[1, 200]` → **422** (FastAPI param validation)

### Known limitations to record in test report (carried from review)
1. **Revenue bucketing** (round-1 finding #3): revenue is bucketed by `invoice.updated_at` as a paid-proxy (no `paid_at` column). A later mutation (e.g. refund) can shift revenue into the wrong time bucket. `status='paid'` correctly excludes `partially_paid`/`refunded`. Document as a known limitation, not a bug.
2. **Average duplication** (finding #4): FE stat cards "TB/ngày"/"TB/tháng" recompute client-side from `overview.visits / daysInRange`, while the clinic table uses BE-computed averages (both use the 30.44 month constant). Verify the two align.

---

## Action items / follow-ups (do NOT block TASK-071)

### Pre-existing FE test failure — `RequireSuperuser.test.tsx`
- **3 of 4 tests fail** (render empty `<div />`).
- **Root cause**: commit `8ed9af3` (`fix(auth): add isHydrated flag`) added `if (!isHydrated) return null;` to `RequireSuperuser.tsx`. The test's `useAuthStore.setState(...)` fixtures never set `isHydrated: true`, so the guard short-circuits.
- **Not a TASK-071 regression**: this file belongs to TASK-070 (route guard), unmodified on the TASK-071 branch.
- **Fix** (small, for Test or a follow-up): add `isHydrated: true` to the 3 authenticated `setState` blocks (lines ~62, ~86, the "regular admin" block) — and the unauthenticated test needs `isHydrated: true` too so it renders the redirect.
- Please confirm this in the test report; it should not gate TASK-071 sign-off, but it is a real (separate) broken test that should be tracked.

### Branch base hygiene (manager — round-1 finding #5)
- `git diff main...feature/TASK-071-superadmin-analytics` drags in unrelated modules (tags / migration `0037` / inventory / services) because the branch was cut from a base ahead of `main`. The eventual PR must target the correct base. Manager to resolve before merge.

---

## Review artifacts

- Full report (round 1 + round 2): `docs/tasks/TASK-071/handoff/review-report.md`
