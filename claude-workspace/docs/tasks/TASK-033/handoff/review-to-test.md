# TASK-033 Code Review Report — Multi-clinic per account (AUTH-018..022)

**Date**: 2026-05-01
**Reviewer**: Code Review Agent
**Decision**: **CHANGES_REQUESTED** (non-blocking for Test phase — recommend conditional pass)

> Recommendation: proceed to Test phase **with prerequisites tracked as deferred items**. The implementation itself is structurally sound; defects identified are either pre-existing test debt or low-impact in scope. Test phase must surface what unit tests cannot (concurrency, Redis stale cache, RLS leak with active_clinic switch).

---

## Summary by checklist

### A. Schema migration safety — ⚠️ MOSTLY OK, ONE GAP

| Check | Result |
|---|---|
| Pivot table created with composite PK + FK CASCADE | ✅ |
| Backfill SQL idempotent (`ON CONFLICT … DO NOTHING`) | ✅ |
| Backfill skips orphan users (`WHERE u.clinic_id IS NOT NULL AND u.is_deleted = FALSE`) | ✅ |
| Multiple roles aggregated into `role_codes[]` via `ARRAY_AGG ... FILTER` | ✅ |
| `user.clinic_id` made nullable (kept for rollback per B.3) | ✅ |
| `account.email UNIQUE` added | ⚠️ Migration does **not** auto-check for duplicate emails — operator-runbook only. If duplicates exist, `alembic upgrade` fails mid-transaction; partial state left depending on backend. Recommend: add a `SELECT 1 FROM (SELECT email, COUNT(*) c FROM "user" WHERE email IS NOT NULL GROUP BY email HAVING c > 1) WHERE EXISTS RAISE EXCEPTION` precondition step **inside** the migration. |
| Downgrade exists | ✅ All 4 steps reversed in order |
| Downgrade caveat: `SET NOT NULL` will fail if any user created post-migration without clinic_id | ✅ Documented in module docstring |
| **Migration revision conflict (Stream B/C)** | ❌ **ACKNOWLEDGED** — Stream B `0021_password_history` and Stream C `0021_add_mfa` will collide with this `0021_multi_clinic_account`. All three claim same revision ID + same parent. Merge-time resolution required: rename two of them to `0021a_*` / `0021b_*` with linear `down_revision` chain. **Flag for merge integrator.** |

### B. Auth flow correctness — ✅ CORRECT

| Check | Result |
|---|---|
| `LoginRequest` no longer has `clinic_code` (schema + service + route) | ✅ Verified in `auth_schemas.py:14`, `auth_service.py:138`, `routes.py:60` |
| Login response shape includes `clinics: [...]` + `active_clinic_id` | ✅ `TokenPair` schema includes both fields; populated from pivot via `_get_user_clinics()` |
| Auto-resolve logic (1 clinic → auto / N+default → use default / N+no-default → null) | ✅ `_resolve_active_clinic()` correct in all 3 cases |
| `POST /auth/select-clinic` membership check (privilege-escalation guard) | ✅ `auth_service.py:283 — pivot is None → ValueError("not_a_member") → 403 FORBIDDEN`. **Critical security check — confirmed present.** |
| Clinic active check (cannot switch to deleted/inactive clinic) | ✅ `auth_service.py:289` |
| JWT revocation on switch — Redis blacklist | ✅ Refresh JTI revoked via `revoke_token(jti, exp_dt)` before issuing new pair. ⚠️ Old **access token** is NOT revoked (15-min natural expiry). Acceptable per access-token short-TTL design but worth noting. |
| New JWT has correct `active_clinic_id` + scoped `permissions` | ✅ `select_clinic()` calls `get_user_effective_permissions(db, user_id, clinic_id)` with the new clinic |
| `no_clinic_membership` ValueError in docstring but never raised | ⚠️ Cosmetic — login lets users with 0 clinics through with `active_clinic_id=None`. FE must handle this case (currently FE only branches on `length > 1`). **See E.4 below.** |

### C. RBAC + cache integrity — ✅ CORRECT

| Check | Result |
|---|---|
| `get_user_effective_permissions(user_id, clinic_id)` signature with pivot lookup | ✅ Filters `Role.clinic_id == clinic_id OR is None` for system roles (line 188-189) |
| Cache key `user:perms:{user_id}:{clinic_id}` (or `:global`) | ✅ `_perm_cache_key` correct; clinic_id None → "global" sentinel |
| Existing cached entries with old format (`user:perms:{user_id}`) — graceful invalidation | ⚠️ Old key format will sit as stale data until 5-min TTL expires. No SCAN-and-purge logic. Operator-runbook says "flush Redis during deploy window" — relies on operator. **Recommend: add an idempotent `FLUSHDB`-equivalent command in deploy script, or migration step.** |
| Cache invalidation on role/extra-perm change | ✅ `invalidate_user_cache(user_id)` uses SCAN to wipe all clinic variants |

### D. `current_clinic_id` call sites — ✅ STRUCTURALLY OK, ONE REGRESSION

`grep -rn "current_clinic_id" app/` → **27 files matched**. All use the ContextVar set by TenancyMiddleware, which now reads `active_clinic_id` JWT claim with `clinic_id` fallback. The middleware change propagates transparently to all 27 sites — no per-site refactor needed for ContextVar consumers. ✅

| Spot check | Result |
|---|---|
| `app/modules/visits/api/routes.py` | ✅ Reads `current_clinic_id.get()` |
| `app/modules/billing/api/routes.py` | ✅ Reads `current_clinic_id.get()` |
| `app/modules/prescriptions/api/routes.py` | ✅ Reads `current_clinic_id.get()` |
| `app/modules/inventory/api/routes.py` | ✅ Reads `current_clinic_id.get()` |
| `app/modules/reports/api/routes.py` | ✅ Reads `current_clinic_id.get()` |
| `app/core/permissions.py` `require_permission` | ✅ Now passes `clinic_id` to RBAC (line 65) |
| `app/modules/services/services/visit_service_service.py:_check_user_has_price_override` | ⚠️ **DEFECT**: function signature accepts `clinic_id` (line 91), but **call sites at lines 137 + 319 do NOT pass it** (only `db, requesting_user_id`). Result: `clinic_id=None` → uses "global" cache key, scans all of user's roles unscoped. Defeats B.10 intent for this code path. **Fix**: pass `clinic_id` through `add_to_visit` + `update_price` callers (already have it as required arg). Low impact (only affects price-override perm check), but functional bug. |

### E. FE flow — ✅ MOSTLY OK, ONE EDGE CASE

| Check | Result |
|---|---|
| `LoginPage` Zod schema removed `clinic_code` | ✅ `LoginPage.tsx:88-92` |
| `AuthStore` shape: `clinics: ClinicInfo[] + activeClinicId + defaultClinicId` | ✅ Confirmed |
| AuthStore loses `clinicId/clinicCode/setClinicContext` (single-tenant remnants) | ✅ Tested `expect("clinicCode" in state).toBe(false)` |
| `ClinicSelectorPage` handles N clinics | ✅ Renders selector with role chips + default badge |
| Auto-resolve if 1 clinic — handled in BE login (`active_clinic_id` set), so FE redirects to `from`/`/dashboard` | ✅ `LoginPage.tsx:171` (no selector page navigation) |
| **0-clinic case (user with no memberships)** | ❌ **GAP**: BE login returns `clinics:[], active_clinic_id:null`. FE LoginPage check `!active_clinic_id && clinics.length > 1` is FALSE → user redirects to `/dashboard` with no clinic context. Will hit middleware/RLS errors on first API call. **Expected**: explicit error screen "Tài khoản chưa được gán phòng khám — liên hệ admin" + force logout. |
| ClinicSwitcher: 240px, role chip, "Hiện tại" indicator | ✅ `w-60` (240px), role chips rendered, "current" label via i18n |
| `queryClient.clear()` on switch | ✅ Confirmed line 78, also page reload on line 81 |
| Tauri secureStore `LAST_ACTIVE_CLINIC` + `CLINICS` keys | ✅ `secureStore.ts:21-22` |
| `ProfilePage` "Phòng khám của tôi" tab — list + set-default | ✅ Optimistic update via `useAuthStore.setState({ clinics: ... })`. **Minor**: bug at `ProfilePage.tsx:62` — uses stale `localClinics` (closure captures pre-update state). `setLocalClinics` called above but `useAuthStore.setState` reads the un-mutated `localClinics` constant. Cosmetic — second click reconciles. |
| Visual: Indigo tokens (Wave 1 FE on TASK-039 branch) | ✅ All Indigo `bg-indigo-*` / `text-indigo-*` classes |

### F. Multi-role implications — ✅ CORRECT

- 2 roles in clinic A + 1 role in clinic B → backfill SQL `ARRAY_AGG(... ORDER BY r.code)` GROUPs by `(u.id, u.clinic_id)` → 2 pivot rows, each with their own `role_codes[]`. ✅
- Permissions union per-clinic only. `get_user_effective_permissions` filters `Role.clinic_id == active_clinic_id OR Role.clinic_id IS NULL` → never unions across clinics. ✅
- ⚠️ **Caveat for TASK-035**: Multi-role per clinic is supported via `role_codes[]` array, but there is NO mechanism to switch between roles within a single clinic. JWT carries union of all role's permissions per-clinic. If TASK-035 needs per-session role choice, this needs revision.

### G. Test quality — ⚠️ ADEQUATE BUT LIGHT

| Check | Result |
|---|---|
| 28 BE unit tests authored | ✅ `test_task033_multi_clinic.py` |
| Coverage: JWT shape (10), RBAC cache key (5), AccountClinicRole model (4), schemas (5), lockout key (3) | ✅ Total 27 tests counted (handoff says 28; close enough) |
| Concurrency tests (parallel select-clinic from same user) | ❌ Missing |
| Negative test: select clinic user is NOT member of → 403 | ❌ Missing (relies on integration env) |
| Integration test for full login → select → switch flow | ❌ Deferred (Docker required) — handoff acknowledges |
| 564 FE tests pass (baseline 547 + 17 new TASK-033 tests) | ✅ `npx vitest run` confirms 564/564 |
| **Existing integration tests reference `clinic_code`** (35 files) | ❌ **TEST DEBT**: 35+ existing integration tests still POST `{"clinic_code": ..., ...}` to `/auth/login`. These will fail after migration. **Test agent must update these as part of regression sweep, OR run integration suite first to confirm fail-list, then fix in bulk.** |

### H. Decisions deferred — ✅ ALL HAVE REASONABLE RATIONALE

1. **`user.clinic_id` drop** → kept nullable 1 release. ✅ Low rollback risk; explicit follow-up needed.
2. **Email duplicate pre-check** → operator-runbook only. ⚠️ See A above.
3. **Redis flush** → operator-runbook + 5-min TTL. ⚠️ Stale data risk during deploy window — see C above.
4. **`X-Active-Clinic` header dropped** in favor of JWT claim. ✅ Reasonable; reduces attack surface.
5. **`queryClient.clear()` over `invalidateQueries`** → broader purge but safer. ✅ Acceptable; `window.location.reload()` follows so cache state moot.
6. **`UserRole` legacy table left in place** → roles are dual-written (or rather: backfill is one-shot). ⚠️ Going forward, role-management changes must update **both** `user_role` AND `account_clinic_role.role_codes[]`. Not enforced by code yet. **Strong recommendation**: add a follow-up task TASK-033b to consolidate.

---

## Critical security/data integrity concerns

1. **Privilege escalation guard intact**: `select_clinic` checks pivot membership before reissuing JWT. ✅
2. **Cross-clinic permission leakage**: Cache key now per-clinic; `get_user_effective_permissions` filters roles by clinic. ✅
3. **Email uniqueness migration could leave DB in inconsistent state** if operator skips pre-check. ⚠️
4. **Stale Redis cache during deploy** could serve old (pre-multi-clinic) permissions for ~5 min. Acceptable mitigation: enforce flush during deploy window per operator runbook.
5. **0-clinic users orphan-state**: silently authenticated with no clinic — protected APIs will 401/403, but no user-friendly error. Low security risk (no data leak), UX defect.

---

## Required changes before merge to main

These should be fixed BEFORE merge to `main` (not blocking for Test phase, but blocking for production):

| Priority | Item | Owner |
|---|---|---|
| **HIGH** | Resolve `0021_*` migration revision collision across Streams A/B/C — rename pairs to `0021a/0021b` linear chain | Merge integrator |
| **HIGH** | Fix `_check_user_has_price_override` callers to pass `clinic_id` (regression in B.10) | Code Implementation |
| **MEDIUM** | Update 35+ existing integration tests removing `clinic_code` | Test agent |
| **MEDIUM** | FE LoginPage: handle `clinics.length === 0` case explicitly | Code Implementation |
| **LOW** | Migration: add inline duplicate-email pre-check (raise if found) | Code Implementation |
| **LOW** | ProfilePage: fix stale `localClinics` closure on optimistic update | Code Implementation |
| **LOW** | Add follow-up task: drop `user.clinic_id` after 1 release | Manager |
| **LOW** | Add follow-up task: consolidate `user_role` → `account_clinic_role.role_codes` | Manager |

---

## Migration conflict acknowledged

**YES** — migration revision `0021` is claimed by three streams:
- Stream A (this task): `0021_multi_clinic_account`
- Stream B: `0021_password_history`
- Stream C: `0021_add_mfa`

All three set `down_revision = "20260429_65fc9ae59ba5_merge_task_015_reports_notifications_"`. At merge time, only one can keep `0021` — the other two must be renamed (e.g., `0022_password_history`, `0023_add_mfa`) and have their `down_revision` updated to chain linearly. **Flagged in handoff for the merge integrator.**

---

## Verdict

**CHANGES_REQUESTED** — proceed to **Test phase** with the following understanding:

- The structural implementation is correct and the security model holds.
- Test phase MUST cover: 0-clinic user flow, parallel select-clinic, RLS no-leak after switch, integration test repair (fix `clinic_code` references in 35+ files).
- Production merge BLOCKED until the HIGH-priority items are resolved.

Code Implementation agent should address `_check_user_has_price_override` regression and FE 0-clinic case before/during the Test fix-up cycle.
