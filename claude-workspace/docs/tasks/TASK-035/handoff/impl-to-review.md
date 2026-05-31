# TASK-035 Implementation → Review Handoff

## Original Implementation Summary

Multi-role + applied_role + SoD framework implemented across BE and FE.
See `review-to-test.md` for full review findings.

---

## Fix-mode addendum

**Date**: 2026-05-01  
**Triggered by**: CHANGES_REQUESTED in `review-to-test.md`  
**Fix mode**: F.5/F.6/F.7 applied_role context + SoD negative tests + dead code removal

---

### Per-Finding Resolution

| Finding | Status | Resolution |
|---------|--------|------------|
| F.5 — appliedRole missing from authStore | FIXED | Added `appliedRole: string \| null` field + `setAppliedRole()` action with Tauri secureStore persistence (`APPLIED_ROLE` key). On login: defaults to `user.roles[0]`. On logout: clears. `loadFromStorage` restores value. |
| F.6 — apiClient missing X-Applied-Role | FIXED | Added header injection after `X-Clinic-Id` in `apiClient.ts`: `headers.set("X-Applied-Role", state.appliedRole)` when set. |
| F.7 — /dashboard/multi-role route missing | FIXED | Created `MultiRoleDashboardPage.tsx` stub + added route in `router/index.tsx` + updated `LoginPage.tsx` redirect: `if (user.roles.length > 1 && from === "/dashboard") → /dashboard/multi-role`. |
| Fix 3 — dead `require_no_self_approval` with `raise NotImplementedError` | FIXED | Deleted the function entirely from `app/core/sod.py`. Updated module docstring to reference `make_sod_dep` and `check_no_self_approval` as the actual API. No import cleanup needed (no callers found). |
| Nit — `'claims' in dir()` in tenancy.py:219 | FIXED | Initialized `claims: dict \| None = None` before the if/else branch; replaced `'claims' in dir()` with `claims is not None`. |
| Fix 2 — SoD negative integration tests missing | FIXED | Created `tests/integration/test_sod_violations.py` with 3 tests (see below). |

---

### F.5/F.6/F.7 Implementation Summary

**Files changed (FE):**
- `src/lib/secureStore.ts` — added `APPLIED_ROLE: "auth.applied_role"` key constant
- `src/stores/authStore.ts` — added `appliedRole` state field + `setAppliedRole()` action; `setTokens` sets default; `logout` clears; `loadFromStorage` restores
- `src/components/shell/Sidebar.tsx` — imports `ROLE_NAV_SECTIONS`; added `resolveRoleForSection()` helper; nav click calls `setAppliedRole(sectionRole)`; visual indicator `data-testid="applied-role-indicator-{key}"` dot on active role section headers
- `src/lib/apiClient.ts` — sends `X-Applied-Role: <role>` header when `appliedRole` is set
- `src/router/index.tsx` — added `/dashboard/multi-role` route
- `src/pages/dashboard/MultiRoleDashboardPage.tsx` — NEW stub page
- `src/pages/auth/LoginPage.tsx` — added multi-role redirect: `user.roles.length > 1 && from === "/dashboard"` → `/dashboard/multi-role`

**Files changed (BE):**
- `app/core/sod.py` — removed `require_no_self_approval()` dead function + updated docstring
- `app/core/tenancy.py` — fixed `'claims' in dir()` → `claims is not None`

---

### New Tests Added

**FE (src/tests/shell/):**
- `applied-role-context.test.tsx` — NEW (10 tests)
  - `authStore - setAppliedRole`: updates state + persists to secure store
  - `authStore - setAppliedRole(null)`: clears state + removes from store
  - `authStore - setTokens`: defaults appliedRole to first role
  - `authStore - logout`: clears appliedRole
  - `apiClient`: sends X-Applied-Role when set
  - `apiClient`: no header when null
  - Login redirect: multi-role → `/dashboard/multi-role`
  - Login redirect: single-role → `/dashboard`
  - Login redirect: deep-link preserves destination
  - Login redirect: zero-role → `/dashboard`
- `Sidebar-multi-role.test.tsx` — added 2 tests
  - Renders applied-role indicator dot for active role section
  - Does not render indicator for non-active role sections

**BE (tests/integration/):**
- `test_sod_violations.py` — NEW (3 tests)
  - `TestSoDInvoicePayment::test_invoice_creator_cannot_record_payment_returns_403_sod_violation`
  - `TestSoDInvoicePayment::test_different_user_can_record_payment` (negative control: user B succeeds)
  - `TestSoDPharmacyDispense::test_prescription_creator_cannot_dispense_returns_403`

**Tests removed:** 0

---

### Test Results Post-Fix

| Suite | Before | After | Delta |
|-------|--------|-------|-------|
| BE unit/test_sod.py | 8 pass | 8 pass | +0 |
| BE unit/test_audit_applied_role.py | 3 pass | 3 pass | +0 |
| BE integration/test_sod_violations.py | — | 3 pass | +3 NEW |
| **BE targeted total** | **11** | **14** | **+3** |
| FE total | 580 | 592 | +12 |

All 592 FE tests pass. All 14 targeted BE tests pass.
TypeScript: `npx tsc --noEmit` → 0 errors. ESLint: 0 warnings.
