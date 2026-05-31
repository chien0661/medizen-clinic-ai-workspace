---
task: TASK-070
phase: review
reviewer: Code Review Agent
date: 2026-05-31
branch: feature/TASK-070-superadmin-fe
decision: CHANGES_REQUESTED
---

# TASK-070 — Code Review Report

**Feature**: FE Super Admin — Quản lý toàn hệ thống
**Branch**: `feature/TASK-070-superadmin-fe` (clinic-cms-web)
**Decision**: ❌ **CHANGES_REQUESTED**

---

## Summary

The implementation is well-structured and the **security model is correct** (see below).
However, review found **one build-breaking blocker** (committed Git merge-conflict
markers) and **a set of BE↔FE contract mismatches** that make 4 of the feature's
data fields render empty/zero at runtime. The 22 unit tests pass, but they pass
against *mocked* response shapes that do not match the real backend, so they give
false confidence and did not catch the mismatches.

Must be fixed and re-submitted.

---

## ✅ What is correct

### Security model — PASS (this was the critical concern)
- **`isSuperuser` is server-authoritative, not client-spoofable for real access.**
  - BE sets `is_superuser` both in the signed JWT claim *and* in the login-response
    `user` object (`auth_schemas.py:70`, `auth_service.py:346`).
  - Every `/api/v1/superadmin/*` route is guarded server-side by
    `Depends(require_superuser)` which verifies the JWT claim
    (`app/modules/superadmin/api/routes.py:41`).
  - The FE `isSuperuser` flag (derived in `authStore.setTokens` / `restoreSession`
    from `user.is_superuser === true`) only gates *cosmetic* visibility (sidebar +
    route guard). A user who tampered with localStorage to flip the flag would see
    the menu/routes but every API call would still return **403** from the BE.
    This is the correct defense-in-depth posture. ✔
- **Route protection** — all 4 `/superadmin/*` routes are wrapped in
  `<RequireSuperuser>` *and* nested inside the `RequireAuth` + `AppShell` parent
  route. `RequireSuperuser` redirects unauthenticated → `/login` and
  authenticated-non-superuser → `/dashboard`. Direct URL navigation to
  `/superadmin/clinics` by a non-superuser is blocked. ✔
- **Auth headers** — `apiClient` attaches `Authorization: Bearer` automatically;
  401 triggers refresh-then-retry, hard logout on failure. ✔
- **No hardcoded credentials/secrets** in the diff. (The seed password
  `Super@12345` only appears in task docs, not in shipped code.) ✔
- `logout()` and `restoreSession()` both reset `isSuperuser`. ✔

### Other good points
- Clean module layering (`types.ts` / `api.ts` / pages), typed API wrappers.
- Query-param builders correctly omit empty params.
- Sidebar section gated by `isSuperuser`, amber theme, `data-testid`s present.
- AuditLogs page uses null-safe fallbacks and consumes BE fields correctly.

---

## ❌ Blockers (must fix before re-submit)

### BLOCKER 1 — Committed merge-conflict markers in `Sidebar.tsx` (build broken)
`src/components/shell/Sidebar.tsx` lines **656–661** contain a live, unresolved Git
conflict:

```
{/* Navigation */}
<<<<<<< Updated upstream
      <nav className="flex-1 overflow-y-auto py-2 no-scrollbar" ...>
=======
      <nav className="flex-1 overflow-y-auto no-scrollbar py-2" ...>
>>>>>>> Stashed changes
```

- `npx tsc --noEmit` fails with `TS1185: Merge conflict marker encountered` plus a
  cascade of JSX parse errors (11 errors in this file). A production `vite build`
  will fail.
- The two sides differ **only** in CSS class ordering — pick either and delete the
  markers (`<<<<<<<`, `=======`, `>>>>>>>`).
- Note: `vitest` passed despite this because the test suite does not exercise the
  real Sidebar render path the same way; do **not** rely on the green test run as
  proof the build is healthy.

### BLOCKER 2 — Dashboard stats fields do not match the BE contract
`SuperAdminDashboardPage.tsx` + `types.ts` `SuperAdminStats` expect:
`total_accounts`, `active_today`, `locked_accounts`, `inactive_clinics`.

BE `service.get_stats()` actually returns (`superadmin/service.py:343`):
`total_clinics`, `active_clinics`, `total_users`, `active_users`, `locked_users`.

Result at runtime: only **"Tổng phòng khám"** shows a real number. The other 3 stat
cards always show **0** (masked by `?? 0`), and the warnings section
(`inactive_clinics` / `locked_accounts`) **never** triggers. Acceptance criteria for
the dashboard are not met.

**Fix**: align FE to the real BE field names (recommended), or coordinate a BE change.
There is also no `active_today` concept in the BE at all — decide what that card
should show (e.g. `active_users`) or remove it.

### BLOCKER 3 — Accounts table: roles + full name never render
`SuperAdminAccountsPage.tsx`:
- **Roles column** reads `account.roles`, but BE `list_accounts` returns
  `role_codes` (`service.py:163,178`). Roles badges are **always empty**.
- **Họ tên column** reads `account.full_name_encrypted`, but the BE cross-tenant
  projection **never returns** `full_name_encrypted` / `email_encrypted` at all
  (it intentionally projects plaintext-only columns and skips encrypted PII —
  see `service.py` module docstring + the `list_accounts` SELECT). So the column is
  **always "—"** and the `⚠ <bytes>` branch is dead code.

**Fix**:
- Rename FE field `roles` → `role_codes` (or map it in the API layer).
- Decide product behavior for full name: BE deliberately cannot return decrypted PII
  in a cross-tenant scan. Either (a) drop the "Họ tên" column, (b) show username
  only, or (c) add a BE endpoint that decrypts per-account on demand. This needs a
  product/BE decision — flag it, don't silently keep dead code.
- Also update `types.ts` `SuperAdminAccount` to reflect reality (`role_codes`,
  `clinic_code`, no `*_encrypted` fields).

---

## ⚠️ Non-blocking issues / nits

1. **Clinics "Số tài khoản" column** reads `clinic.account_count` but BE returns
   `user_count` (`service.py:50`). Always shows "-". Cosmetic but should be fixed
   (rename to `user_count`). Trang 2 requirement "số accounts" is unmet.
2. **`SuperAdminAccountCreate.email` typed as required** (`string`) and the create
   form uses `z.string().email()` (required), but BE `SuperAccountCreate.email` is
   **optional** (`str | None`). Task spec lists email in the create form, so this is
   acceptable, but the type should be `email?: string` to match BE and avoid blocking
   accounts that legitimately have no email.
3. **Unit tests validate the wrong contract.** `superadminApi.test.ts` and
   `SuperAdminDashboardPage.test.tsx` mock responses with the FE-assumed field names
   (`total_accounts`, `active_today`, `locked_accounts`, `inactive_clinics`) and the
   dashboard test asserts on them. After fixing the contract, **update these mocks to
   mirror the real BE shape** so the tests actually protect against regressions.
   (Side note: `superadminApi.test.ts:133` already mocks `role_codes` — inconsistent
   with the page that reads `roles`.)
4. **AuditLogs "Áp dụng" button is misleading** — the query key includes
   `filterAction`, so the list re-fetches on every keystroke regardless of the button.
   Either debounce + drop the button, or gate the fetch on an applied value. Minor UX.
5. **`X-Clinic-Id` is still sent on superadmin calls.** `api.ts` comments "do NOT send
   X-Clinic-Id", but `apiClient` always attaches it when `activeClinicId` is set. BE
   superadmin routes bypass RLS so this is harmless today, but the code comment is
   misleading — either remove the comment or add a real skip mechanism.
6. **Superadmin/SYSTEM-clinic login flow** — handoff "Known Limitations" notes the
   superadmin may hit a 0-clinic redirect at login. Not in scope to fix here, but
   testing should confirm the superadmin can actually reach `/superadmin` after login.

---

## Verification performed

| Check | Result |
|-------|--------|
| Handoff + task.md read | ✔ |
| Branch diff reviewed (13 files, +2210) | ✔ |
| Security model traced FE→BE (JWT claim + `require_superuser`) | ✔ PASS |
| Route guard nesting verified | ✔ PASS |
| BE schemas/routes/service cross-checked vs FE types | ❌ mismatches found |
| `npx vitest run src/tests/superadmin` | 22/22 PASS (but wrong contract) |
| `npx tsc --noEmit` (superadmin files) | 0 errors in superadmin files |
| `npx tsc --noEmit` (Sidebar.tsx) | ❌ 11 errors — merge-conflict markers |
| Hardcoded secrets scan | ✔ none |
| App reachable at :1420 | 200 (not used for runtime verify due to broken build) |

SonarQube: disabled per instructions.
Pre-existing TS/lint errors (9 TS / 17 lint in unrelated files): not penalized.
`InvoiceListPage.tsx` TS errors are pre-existing/unrelated.

---

## Required actions for re-submit

1. Remove the merge-conflict markers in `Sidebar.tsx` (BLOCKER 1) — verify `tsc` is clean.
2. Fix `SuperAdminStats` field names to match BE (BLOCKER 2).
3. Fix accounts `roles`→`role_codes` and resolve the full-name column (BLOCKER 3).
4. Fix clinics `account_count`→`user_count` (nit 1).
5. Update unit-test mocks to the real BE response shapes (nit 3).
6. Address nits 2/4/5 or explicitly defer with a note.

Re-submit to review once `tsc` is clean and the data renders against a live BE.
