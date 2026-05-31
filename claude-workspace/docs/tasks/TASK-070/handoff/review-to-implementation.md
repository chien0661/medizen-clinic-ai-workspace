---
from: review
to: implementation
task: TASK-070
date: 2026-05-31
branch: feature/TASK-070-superadmin-fe
decision: CHANGES_REQUESTED
status: IN_PROGRESS
---

# TASK-070 — Review → Implementation Handoff (CHANGES_REQUESTED)

Full details: `handoff/review-report.md`. Summary of required fixes below.

## ✅ Security passed — no auth changes needed
The `isSuperuser` model is correct and server-authoritative (BE `require_superuser`
verifies the JWT claim on every `/superadmin/*` call). Route guards are wired
correctly. Do not change the auth/guard logic.

## ❌ Must fix (blockers)

### 1. Merge-conflict markers in `Sidebar.tsx` (lines 656–661) — BUILD BROKEN
Delete the `<<<<<<< Updated upstream` / `=======` / `>>>>>>> Stashed changes`
markers. The two `<nav>` variants differ only in CSS class order — keep one.
Run `npx tsc --noEmit` and confirm `Sidebar.tsx` reports 0 errors.

### 2. Dashboard stats field mismatch (`types.ts` + `SuperAdminDashboardPage.tsx`)
BE `GET /superadmin/stats` returns:
`total_clinics, active_clinics, total_users, active_users, locked_users`.
FE expects `total_accounts, active_today, locked_accounts, inactive_clinics` → 3 of 4
cards show 0 and warnings never fire.
- Align FE to BE names. Suggested mapping:
  - "Tổng tài khoản" → `total_users`
  - "Hoạt động hôm nay" → no BE equivalent; use `active_users` (rename label) or remove
  - "Tài khoản bị khóa" → `locked_users`
  - warnings: derive inactive clinics from `total_clinics - active_clinics`, locked from `locked_users`

### 3. Accounts table — roles + full name (`SuperAdminAccountsPage.tsx` + `types.ts`)
- BE returns `role_codes` (not `roles`). Rename and render `role_codes`.
- BE never returns `full_name_encrypted` / `email_encrypted` (cross-tenant projection
  is plaintext-only, no PII). The `⚠ <bytes>` branch is dead. Decide with product/BE:
  drop the "Họ tên" column, or show username only, or request a BE per-account decrypt
  endpoint. Update `SuperAdminAccount` type accordingly (add `role_codes`, `clinic_code`;
  remove `*_encrypted`).

## ⚠️ Should fix (non-blocking)
4. Clinics "Số tài khoản": read `user_count` not `account_count`.
5. Update unit-test mocks (`superadminApi.test.ts`, `SuperAdminDashboardPage.test.tsx`)
   to mirror the real BE response shapes — current mocks hide the contract bugs.
6. `SuperAdminAccountCreate.email` → optional (`email?: string`) to match BE.
7. AuditLogs "Áp dụng" button is cosmetic (query already refetches per keystroke) —
   debounce or gate the fetch.
8. Remove/adjust the misleading "do NOT send X-Clinic-Id" comment in `api.ts`
   (apiClient sends it anyway; harmless because BE bypasses RLS).

## Recommended verification before re-submit
- `npx tsc --noEmit` clean (no Sidebar errors).
- Run against a live BE (`alembic upgrade head` + `seed_superadmin.py`, login
  `superadmin` / `Super@12345`) and confirm dashboard stats, account roles, and
  clinic account-counts render real values.
- `npx vitest run src/tests/superadmin` still green with corrected mocks.

Set status back to IN_REVIEW when done.
