---
task: TASK-070
from: Code Review Agent
to: Test Agent
date: 2026-05-31
round: 2
decision: APPROVED
branch: feature/TASK-070-superadmin-fe
commit_reviewed: 721433b
---

# TASK-070 — Review → Test Handoff (Round 2 APPROVED)

**Feature**: FE Super Admin — Quản lý toàn hệ thống (clinics + accounts)
**Branch**: `feature/TASK-070-superadmin-fe` (clinic-cms-web)
**Decision**: ✅ **APPROVED** → IN_TESTING

---

## Round-2 verification summary

All 3 round-1 blockers and nits 1/2/3 are resolved in commit **721433b**.

| Round-1 item | Status | Evidence |
|--------------|--------|----------|
| BLOCKER 1 — Sidebar.tsx merge-conflict markers | ✅ Fixed | `git diff main...branch -- Sidebar.tsx` → **0** conflict markers |
| BLOCKER 2 — Dashboard stats field mismatch | ✅ Fixed | `SuperAdminStats` now `total_clinics / active_clinics / total_users / active_users / locked_users`; cards updated; `inactiveClinics` derived as `total_clinics - active_clinics` |
| BLOCKER 3 — Accounts `roles` / `full_name_encrypted` | ✅ Fixed | `roles` → `role_codes`; `*_encrypted` fields removed; "Họ tên" column dropped (option a — BE cannot return decrypted PII cross-tenant); dead `⚠ <bytes>` branch removed |
| Nit 1 — Clinics `account_count` | ✅ Fixed | → `user_count` in type + page |
| Nit 2 — `email` required on create | ✅ Fixed | `email?: string`; form schema `.email().optional().or(z.literal(""))` |
| Nit 3 — Test mocks wrong contract | ✅ Fixed | `superadminApi.test.ts` + `SuperAdminDashboardPage.test.tsx` mocks now mirror real BE shapes |

### Checks performed (round 2)
- `npx tsc --noEmit` — **0 errors in superadmin files**. (Two TS6133 unused-var warnings remain in `Sidebar.tsx` — `ShieldCheck` line 63, `bhytEnabled` — but both **pre-exist on `main`** and are NOT introduced by this branch; not a TASK-070 blocker.)
- `npx vitest run src/tests/superadmin` — **22/22 PASS** (3 files: RequireSuperuser 4, SuperAdminDashboardPage 6, superadminApi 12).
- Field-name scan (`total_accounts|active_today|locked_accounts|account_count|*_encrypted|.roles`) across `modules/superadmin/`, `pages/superadmin/`, `tests/superadmin/` — **no matches**.
- Security model (verified round 1, unchanged): `is_superuser` is server-authoritative (JWT claim + `require_superuser`); FE flag gates cosmetic visibility only.

---

## What to test (functional, against a live BE)

**Prereq**: BE must run migration 0036 + `python scripts/seed_superadmin.py`. Login `superadmin` / `Super@12345`. FE dev :1420 proxies `/api` → BE :8001.

Acceptance criteria from task.md:
1. Login `superadmin` → Super Admin section visible in sidebar.
2. Login `admin` (clinic user) → Super Admin section NOT visible; direct nav to `/superadmin/*` redirects to `/dashboard`.
3. Dashboard stats render real numbers (all 4 cards) — verify `total_clinics`, `total_users`, `active_users`, `locked_users` are non-zero/correct against DB.
4. Create clinic → appears in list immediately; `user_count` column shows a value.
5. Create admin account for a clinic → can log in with it. Verify role badges render (`role_codes`).
6. Lock account → login fails; reset password → login with new password succeeds.
7. Audit logs load + filter by clinic/action.

### Carry-over notes / known limitations to confirm during testing
- **Nit 4** (deferred): AuditLogs "Áp dụng" button is cosmetic — query re-fetches on every keystroke since `filterAction` is in the query key. Confirm UX is acceptable or log as follow-up.
- **Nit 5** (deferred): `X-Clinic-Id` header is still sent on superadmin calls; BE bypasses RLS so harmless, but confirm no 4xx caused by it.
- **Nit 6 / Blocker note**: confirm the superadmin (SYSTEM clinic, 0 owned clinics) does NOT get stuck at a 0-clinic login redirect and can actually reach `/superadmin`.
- "Họ tên" column was intentionally removed from the accounts table (BE cross-tenant projection returns plaintext-only columns, no decrypted PII). Verify product accepts username/clinic/roles columns only.

---

## Files in scope

- `clinic-cms-web/src/modules/superadmin/types.ts`
- `clinic-cms-web/src/modules/superadmin/api.ts`
- `clinic-cms-web/src/pages/superadmin/SuperAdminDashboardPage.tsx`
- `clinic-cms-web/src/pages/superadmin/SuperAdminClinicsPage.tsx`
- `clinic-cms-web/src/pages/superadmin/SuperAdminAccountsPage.tsx`
- `clinic-cms-web/src/pages/superadmin/SuperAdminAuditLogsPage.tsx`
- `clinic-cms-web/src/components/shell/Sidebar.tsx`
- `clinic-cms-web/src/tests/superadmin/*`
