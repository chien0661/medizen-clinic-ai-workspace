---
from: implementation
to: review
task: TASK-070
date: 2026-05-31
branch: feature/TASK-070-superadmin-fe
status: IN_REVIEW
round: 2
---

# TASK-070 — Implementation to Review Handoff (Round 2 — Bug Fixes)

## Summary

Round-2 fixes applied to align FE types to real BE response shapes.
Latest commit: `721433b`

## Round-2 Fixes Applied

### FIX 1 — Sidebar.tsx merge conflict
No actual conflict markers were present on the feature branch. Pre-existing TS6133 unused-variable warnings (`ShieldCheck`, `bhytEnabled`) existed before TASK-070 and remain unchanged.

### FIX 2 — Stats field mismatch
- `SuperAdminStats` interface updated: `total_clinics`, `active_clinics`, `total_users`, `active_users`, `locked_users`
- `SuperAdminDashboardPage.tsx`: stat cards use real field names; `inactive_clinics` computed as `total_clinics - active_clinics`; label "Hoạt động hôm nay" renamed to "Đang hoạt động"

### FIX 3 — Accounts field mismatch
- `SuperAdminAccount`: removed `full_name_encrypted`, `email_encrypted`, `roles`; added `role_codes: string[]` and optional `clinic_code`
- `SuperAdminAccountCreate`: `email` made optional
- `SuperAdminAccountsPage.tsx`: removed "Họ tên" column + encrypted dead-code; `account.roles` → `account.role_codes`; email in create form optional

### FIX 4 — Clinic account_count → user_count
- `SuperAdminClinic.account_count` renamed to `user_count?: number`
- `SuperAdminClinicsPage.tsx` updated to `clinic.user_count`

### FIX 5 — Test mocks updated
- Stats mock now uses real field names in both test files
- `MOCK_CLINICS` uses `user_count` instead of `account_count`
- Label assertion updated to "Đang hoạt động"

## Test Results (round 2)

```
Test Files  3 passed (3)
Tests       22 passed (22)
```

No new TS errors in superadmin files.

---

## Original Implementation Summary (Round 1)

FE Super Admin module is fully implemented on branch `feature/TASK-070-superadmin-fe`.
Original commit: `a260390`

## Files Changed

### New files (13 files, +2210 lines)

**Auth & Guard**
- `src/components/auth/RequireSuperuser.tsx` — route guard that redirects non-superusers to /dashboard

**Module**
- `src/modules/superadmin/types.ts` — TypeScript interfaces for all 10 BE endpoints
- `src/modules/superadmin/api.ts` — typed API wrappers (stats, clinics, accounts, roles, audit-logs)

**Pages (4)**
- `src/pages/superadmin/SuperAdminDashboardPage.tsx` — stats cards (4), top-5 clinics table, warnings section
- `src/pages/superadmin/SuperAdminClinicsPage.tsx` — table + create modal + toggle active/inactive
- `src/pages/superadmin/SuperAdminAccountsPage.tsx` — cross-tenant table + create modal + lock/reset-password
- `src/pages/superadmin/SuperAdminAuditLogsPage.tsx` — read-only audit log + pagination

**Tests (3 files, 22 tests)**
- `src/tests/superadmin/superadminApi.test.ts` — 14 tests for all API functions
- `src/tests/superadmin/RequireSuperuser.test.tsx` — 4 tests for guard (renders/redirects)
- `src/tests/superadmin/SuperAdminDashboardPage.test.tsx` — 6 tests for dashboard page

### Modified files

- `src/stores/authStore.ts` — added `isSuperuser: boolean` to AuthState + UserInfo, `useIsSuperuser()` hook
- `src/components/shell/Sidebar.tsx` — added Super Admin nav section (amber) gated by `isSuperuser`
- `src/router/index.tsx` — added `/superadmin/*` routes wrapped in `<RequireSuperuser>`

## Quality Gate Results

| Check | Result |
|-------|--------|
| TypeScript (new files) | PASS — 0 new errors |
| ESLint (new files) | PASS — 0 new errors |
| Unit tests | PASS — 22/22 |
| Pre-existing TS errors | 9 (unchanged) |
| Pre-existing lint errors | 17 (unchanged) |

## Key Design Decisions

1. **`is_superuser` in `UserInfo`**: Added as optional field. BE returns it in login response user object. On `setTokens()`, `isSuperuser` is derived from `user.is_superuser === true`.

2. **No JWT decoding on FE**: The existing pattern passes user object directly from login response — no need to decode JWT on FE. `is_superuser` comes from BE user object.

3. **Encrypted fields**: `full_name_encrypted` / `email_encrypted` display raw value with `⚠` prefix. No FE decryption implemented (per task notes).

4. **Super Admin clinic header**: SuperAdmin APIs bypass RLS — the `apiClient` sends `X-Clinic-Id` from `activeClinicId`. For superadmin user, this will be the SYSTEM clinic ID (`00000000-...00aa`). No special handling needed.

5. **Sidebar amber theme**: Super admin nav items use amber color to visually distinguish from regular nav (indigo). Section label "SUPER ADMIN" in amber.

## Testing Notes for Reviewer

1. Run `alembic upgrade head` + `python scripts/seed_superadmin.py` to create the superadmin account
2. Login with `superadmin` / `Super@12345` — sidebar should show Super Admin section in amber
3. Login with any clinic user — Super Admin section should NOT appear
4. `/superadmin` route should redirect to `/dashboard` for non-superusers
5. Stats cards, clinics table, accounts table, audit logs all load from BE

## Known Limitations

- Encrypted `full_name` / `email` fields display raw encrypted bytes with `⚠` warning
- Clinic selector page for superadmin is not handled (superadmin's SYSTEM clinic may cause 0-clinic redirect) — needs BE investigation
- No inline edit for clinics (only toggle active/inactive + create)

## Related Files (BE reference)

- `clinic-cms-merge/app/modules/superadmin/api/routes.py`
- `clinic-cms-merge/app/modules/superadmin/schemas.py`
- `clinic-cms-merge/alembic/versions/0036_super_admin.py`
