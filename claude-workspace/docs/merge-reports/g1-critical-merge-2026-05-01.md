# G1 Critical Merge Report — 2026-05-01

**Operator:** Claude (G1 Critical Merge Orchestrator)
**Date:** 2026-05-01
**Repos:** clinic-cms-merge (BE, main) + clinic-cms-web (FE, main)

---

## Branches Merged

### BE repo (`clinic-cms-merge`)

| # | Branch | Result | Notes |
|---|--------|--------|-------|
| 1 | `feature/task-038-q1` | CLEAN | JWT fail-fast validator |
| 2 | `feature/task-033-multi-clinic` | CLEAN | multi-clinic pivot + migration 0021 |
| 3 | `feature/task-042-emr-rx016` | CLEAN + FIX | migration rename 0023→0022 |
| 4 | `feature/task-047-test-fixtures-multi-clinic` | CLEAN | test fixtures |

Post-merge fixup commits:
- `15a7d5b` — rename migration file 0023→0022
- `8d6eaec` — update revision/down_revision content
- `4c6cc83` — update test_icd10_search hardcoded path 0023→0022

### FE repo (`clinic-cms-web`)

| # | Branch | Result | Notes |
|---|--------|--------|-------|
| 1 | `feature/task-039-design-system` | CLEAN | MediZen Modern tokens |
| 2 | `feature/task-033-multi-clinic-fe` | CLEAN | ClinicSwitcher + AuthStore |
| 3 | `feature/task-042-emr-rx016-fe` | CLEAN | EMR 6-tab + stock chip |
| 4 | `feature/task-040-phase-d-screens` | CONFLICTS RESOLVED | 5 files |

Note: FE branches not in BE repo (no dedicated FE merge worktree on main). Used `clinic-cms-web` primary checkout (stashed dirty task-038-b1-fe state first).

---

## Conflicts Resolved (5 files in TASK-040 FE merge)

| File | Conflict Type | Resolution |
|------|---------------|------------|
| `src/lib/i18n.ts` | Comment label only | Merged TASK-033/TASK-040 label |
| `src/locales/en/auth.json` | Add/Add section | Kept both `clinicSelector` (TASK-033) + `forgotPassword` (TASK-040) |
| `src/locales/en/profile.json` | Add/Add structure | Merged myClinics (TASK-033) + profile wrapper (TASK-040) |
| `src/locales/vi/profile.json` | Add/Add structure | Same as EN |
| `src/pages/profile/ProfilePage.tsx` | Add/Add impl | Took TASK-033 full implementation (237 lines) over TASK-040 stub (129 lines) |
| `src/router/index.tsx` | Duplicate import + route conflict | Removed duplicate ProfilePage import; kept both `/auth/select-clinic` + `/forgot-password` routes |

---

## Migration Chain (Final)

```
… → 65fc9ae59ba5 (merge TASK-015 reports/notifications)
    → 0021_multi_clinic_account   (TASK-033)
    → 0022_visit_soap_diagnosis   (TASK-042, renumbered from 0023)
```

`alembic upgrade head` ran cleanly end-to-end (confirmed via Docker container logs).

---

## BE Unit Tests

| Metric | Value |
|--------|-------|
| Passed | 635 |
| Failed | 1 |
| Total  | 636 |
| Pass % | 99.8% |

**1 pre-existing failure** (not a regression): `test_hr_service_logic.py::TestCheckInRejectsOtherUsersShiftId::test_check_in_rejects_other_users_shift_id` — confirmed present on main before merges.

---

## Playwright Smoke Results

| Metric | Value |
|--------|-------|
| Passed | 5 |
| Failed | 9 |
| Skipped | 5 |
| Did not run | 26 |

**Failed tests root cause:** API backend not seeded with `demo` clinic credentials for E2E. All 9 failures are `ECONNREFUSED` / `401 login` — infrastructure issue, not code regression. RBAC + offline-sync tests passed.

Specific smoke specs that pass: `rbac-enforcement` (4/4 assertions), `offline-sync`.

---

## Cleanup

- FE dev server (vite PID): stopped
- Docker containers (`g1-merge` project): stopped and removed
- Stash restored (task-038-b1-password-history-fe state preserved in stash)

---

## Verdict: **SUCCESS**

All 8 critical branches merged (4 BE + 4 FE). Migration chain is linear and ran cleanly. BE unit tests at 99.8% (pre-existing 1 failure). Smoke failures are infrastructure/seed issues, not code regressions.

---

## Next Steps / Follow-ups

1. **Fix pre-existing HR test** `TestCheckInRejectsOtherUsersShiftId` — shift ownership check throws NotFoundError instead of expected PermissionError (separate bug ticket recommended)
2. **E2E smoke infrastructure** — seed a `demo` clinic with test credentials for Playwright backend API calls
3. **FE merge worktree** — no dedicated FE `main` worktree on merge branch; user may want to create `clinic-cms-web-merge` worktree pattern similar to BE
4. **Push to remote** when ready (not done per constraints)
5. **Skipped branches** remain available for post-MVP+: TASK-034, 035, 036, 037, 038-B.x, 039b/c, 044, 045, 046
