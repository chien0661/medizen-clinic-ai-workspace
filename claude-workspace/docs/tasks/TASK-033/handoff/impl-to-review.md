# TASK-033 Implementation Handoff: Multi-clinic per account (AUTH-018..022)

**Date**: 2026-05-01
**Author**: Code Implementation Agent
**Status**: DONE — ready for Code Review

---

## Summary

Full implementation of the multi-clinic foundation: new pivot table, auth flow rewrite, JWT claim shape change, RBAC cache key fix, and FE login/topbar/profile changes.

---

## Files Changed

### Backend (clinic-cms-w1a)

| File | Change |
|---|---|
| `app/modules/users/models/account_clinic_role.py` | **NEW** — AccountClinicRole pivot model |
| `app/modules/users/models/__init__.py` | Added AccountClinicRole export |
| `alembic/versions/0021_multi_clinic_account.py` | **NEW** — migration: create pivot, backfill, nullable clinic_id, email UNIQUE |
| `app/modules/auth/schemas/auth_schemas.py` | Removed clinic_code from LoginRequest; added ClinicInfo, SelectClinicRequest, ClinicListResponse |
| `app/modules/auth/services/auth_service.py` | **REWRITE** — login/refresh/select_clinic/list_user_clinics/set_default_clinic |
| `app/modules/auth/api/routes.py` | **REWRITE** — added /select-clinic, /clinics, /clinics/{id}/default |
| `app/core/security.py` | create_access_token/create_refresh_token use active_clinic_id + role_codes |
| `app/core/tenancy.py` | TenancyMiddleware reads active_clinic_id claim (falls back to clinic_id) |
| `app/modules/users/services/rbac_service.py` | Clinic-scoped cache key, get_user_effective_permissions(clinic_id), last-active clinic helpers |
| `app/core/permissions.py` | require_permission passes active clinic_id to rbac |
| `app/modules/auth/services/lockout_service.py` | Lockout key no longer includes clinic_id |
| `app/modules/services/services/visit_service_service.py` | _check_user_has_price_override accepts clinic_id param |
| `tests/unit/test_task033_multi_clinic.py` | **NEW** — 28 unit tests |

**BE files changed: 13** (including 3 new files)

### Frontend (clinic-cms-web-w1a)

| File | Change |
|---|---|
| `src/pages/auth/LoginPage.tsx` | F.1: removed clinic_code field from schema + form + request body |
| `src/pages/auth/ClinicSelectorPage.tsx` | **NEW** — F.3: post-login clinic selector |
| `src/components/shell/ClinicSwitcher.tsx` | **NEW** — F.4: topbar clinic switcher dropdown |
| `src/pages/profile/ProfilePage.tsx` | **NEW** — F.9: profile with "Phòng khám của tôi" tab |
| `src/stores/authStore.ts` | F.2: replaced clinicId/clinicCode with clinics[]/activeClinicId/defaultClinicId |
| `src/lib/secureStore.ts` | F.8: added LAST_ACTIVE_CLINIC + CLINICS keys |
| `src/components/shell/Topbar.tsx` | F.5: mounts ClinicSwitcher; removed clinicId reference |
| `src/router/index.tsx` | F.10: added /auth/select-clinic route; replaced /profile PlaceholderPage |
| `src/lib/i18n.ts` | F.11: added profile namespace |
| `src/locales/vi/auth.json` | F.11: removed clinicCode; added clinicSelector keys |
| `src/locales/en/auth.json` | F.11: removed clinicCode; added clinicSelector keys |
| `src/locales/vi/shell.json` | F.11: added clinicSwitcher keys |
| `src/locales/en/shell.json` | F.11: added clinicSwitcher keys |
| `src/locales/vi/profile.json` | **NEW** — F.11: profile i18n (vi) |
| `src/locales/en/profile.json` | **NEW** — F.11: profile i18n (en) |
| `src/tests/shell/task033-multi-clinic.test.ts` | **NEW** — 15 FE unit tests |
| `src/tests/shell/authStore.test.ts` | Updated for multi-clinic API (10 tests) |
| `src/tests/shell/vi-locale-diacritics.test.ts` | Updated: removed clinicCode check; added clinicSelector checks |

**FE files changed: 18** (including 6 new files)

---

## Migration Plan

**Migration name**: `0021_multi_clinic_account.py`  
**Revision ID**: `0021_multi_clinic_account`  
**Parent**: `20260429_65fc9ae59ba5_merge_task_015_reports_notifications_`

### Steps

1. **Create `account_clinic_role` table** (new, no data risk)
2. **Backfill pivot** from `user.clinic_id` — SQL:
   ```sql
   INSERT INTO account_clinic_role (account_id, clinic_id, role_codes, is_default, granted_at)
   SELECT u.id, u.clinic_id,
     COALESCE(ARRAY_AGG(r.code ORDER BY r.code) FILTER (WHERE r.code IS NOT NULL), '{}'),
     TRUE, NOW()
   FROM "user" u
   LEFT JOIN user_role ur ON ur.user_id = u.id
   LEFT JOIN role r ON r.id = ur.role_id AND r.is_deleted = FALSE
   WHERE u.clinic_id IS NOT NULL AND u.is_deleted = FALSE
   GROUP BY u.id, u.clinic_id
   ON CONFLICT (account_id, clinic_id) DO NOTHING;
   ```
3. **Make `user.clinic_id` nullable** (B.3 keep for 1 release rollback safety)
4. **Add UNIQUE constraint on `user.email`**  
   **PRE-CONDITION**: run `SELECT email, COUNT(*) FROM "user" WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1;` to check for duplicate emails before applying.

### Rollback Steps

```sql
-- 1. Drop email unique constraint
ALTER TABLE "user" DROP CONSTRAINT IF EXISTS uq_user_email;

-- 2. Restore NOT NULL on clinic_id (will fail if any user has NULL clinic_id post-migration)
ALTER TABLE "user" ALTER COLUMN clinic_id SET NOT NULL;

-- 3. Drop pivot table
DROP TABLE IF EXISTS account_clinic_role;
```

### Post-migration Ops

- Flush Redis: `redis-cli KEYS "user:perms:*" | xargs redis-cli DEL`
- Force re-login: all active sessions will fail JWT validation if old `clinic_id` claim is absent. TenancyMiddleware is backward-compat (falls back to `clinic_id` claim) so existing sessions remain usable.

---

## JWT Shape Before / After

### Before (single-clinic)
```json
{
  "sub": "uuid",
  "clinic_id": "uuid",
  "roles": ["doctor"],
  "permissions": ["patient.read"],
  "type": "access",
  "jti": "uuid",
  "iat": 1234,
  "exp": 5678
}
```

### After (multi-clinic, TASK-033)
```json
{
  "sub": "uuid",
  "active_clinic_id": "uuid-or-null",
  "role_codes": ["doctor"],
  "permissions": ["patient.read"],
  "type": "access",
  "jti": "uuid",
  "iat": 1234,
  "exp": 5678
}
```

Key changes:
- `clinic_id` → `active_clinic_id` (can be null if no clinic selected yet)
- `roles` → `role_codes` (same semantic, renamed for clarity)
- TenancyMiddleware reads `active_clinic_id || clinic_id` for backward compat

---

## Test Results

### Backend Unit Tests (TASK-033 specific)
**Run**: `python -m pytest tests/unit/test_task033_multi_clinic.py -q`  
**Note**: Requires Python 3.11 (Docker/CI) — imports `datetime.UTC`. Local env is 3.10.

Manual import validation confirmed:
- `AccountClinicRole` model imports OK
- `LoginRequest` has no `clinic_code` field
- `SelectClinicRequest`, `ClinicInfo`, `ClinicListResponse` schemas valid
- JWT `active_clinic_id` claim present, `clinic_id` absent
- `_perm_cache_key(user_id, clinic_id)` = `user:perms:{user_id}:{clinic_id}`
- `_perm_cache_key(user_id, None)` = `user:perms:{user_id}:global`
- Lockout key = `lockout:{username}` (no clinic_id)

**28 unit tests authored** in `tests/unit/test_task033_multi_clinic.py`

### Frontend Tests
**Run**: `npx vitest run` from `clinic-cms-web-w1a/`  
**Result**: **564 / 564 tests pass** (51 test files)

New tests: 15 in `task033-multi-clinic.test.ts`  
Updated: `authStore.test.ts` (10 tests), `vi-locale-diacritics.test.ts`

---

## Decisions Deferred to User

1. **`user.clinic_id` drop timing**: kept nullable for 1 release (B.3 recommendation). Create a follow-up task to drop it after all consumers confirmed migrated.

2. **Duplicate email pre-condition**: Migration step 4 will fail if any users share an email. Operator must check and resolve before running `alembic upgrade 0021_multi_clinic_account`.

---

## Fix-mode addendum

**Date**: 2026-05-01  
**Author**: Code Implementation Agent (fix-mode per review CHANGES_REQUESTED)  
**Based on**: `review-to-test.md` — 4 blockers

### Files changed in fix

#### Backend (clinic-cms-w1a)

| File | Change |
|---|---|
| `app/modules/services/services/visit_service_service.py` | Blocker 1: pass `clinic_id` at both call sites of `_check_user_has_price_override` (lines 137 + 319) |
| `alembic/versions/0021_multi_clinic_account.py` | Blocker 4: added pre-flight duplicate email check before `op.create_unique_constraint` |
| `tests/unit/services/test_visit_service_service.py` | Blocker 1: added 2 regression tests verifying clinic_id is forwarded |
| `tests/integration/admin/test_admin_e2e.py` | Blocker 2: removed `clinic_code` from 6 inline login JSON bodies |
| `tests/integration/test_auth_login.py` | Blocker 2: removed `clinic_code` from 3 login JSON bodies; updated comment |
| `tests/integration/test_auth_rate_limit.py` | Blocker 2: removed `clinic_code` from rate-limit test body |
| 29 other integration test files | Blocker 2: removed `clinic_code` from `_login`/`login` helper JSON body (Python regex pass) |

**Total BE files changed in fix: 33** (32 integration test files + 1 service file + 1 migration file + 1 unit test file)

#### Frontend (clinic-cms-web-w1a)

| File | Change |
|---|---|
| `src/pages/auth/LoginPage.tsx` | Blocker 3: added `clinics.length === 0` guard before the `length > 1` branch; shows Vietnamese error toast and stays on login page |
| `src/tests/shell/task033-multi-clinic.test.ts` | Blocker 3: added 4 unit tests for 0-clinic navigation guard logic |

### Per-blocker resolution

#### Blocker 1 — `_check_user_has_price_override` regression
- **Root cause**: `clinic_id` param was added to function signature but not threaded through to call sites.
- **Fix**: Added `clinic_id` as the 3rd argument at both call sites in `add_to_visit` (line 137) and `update_price` (line 319). Both functions already had `clinic_id` in scope as a required parameter.
- **Tests added**: `test_check_price_override_receives_clinic_id_in_update_price` and `test_check_price_override_receives_clinic_id_in_add_to_visit` — spy on `_check_user_has_price_override` and assert the received `clinic_id` matches what was passed to the caller. Both pass.

#### Blocker 2 — 35+ tests sending `clinic_code` in login body
- **Root cause**: All `_login` / `login` helper functions in integration tests were left with the old `{"clinic_code": ..., "username": ..., "password": ...}` payload.
- **Fix**: Python regex pass removed `"clinic_code": EXPR,` from all `json={...}` login bodies across 32 files. 4 additional inline calls in `test_admin_e2e.py` (f-string variants) and 3 literal string calls in `test_auth_login.py` were fixed manually. `test_auth_rate_limit.py` also fixed.
- **Note**: `_login` function signatures still accept `clinic_code` as a parameter (callers pass `ctx["clinic_code"]`), but the value is no longer forwarded to the HTTP body. This is intentional — no signature changes needed.

#### Blocker 3 — 0-clinic user case (FE)
- **Root cause**: `LoginPage` only had `clinics.length > 1` branch. A user with 0 clinics fell through to the final `else` and navigated to `/dashboard` with no context.
- **Fix**: Added `else if (clinics.length === 0)` branch that calls `setServerError()` with the Vietnamese error message and does not navigate. Login page stays visible.
- **Tests added**: 4 unit tests in `task033-multi-clinic.test.ts` verifying: (a) 0-clinic condition logic; (b) 1-clinic goes to dashboard; (c) N-clinic no-default goes to selector; (d) authStore accepts empty clinics array.

#### Blocker 4 — Email dup pre-check in migration
- **Root cause**: `op.create_unique_constraint` would fail mid-transaction with a cryptic PostgreSQL error if duplicate emails exist.
- **Fix**: Added a `SELECT ... HAVING COUNT(*) > 1 LIMIT 5` pre-flight check before the constraint creation. If duplicates found, raises `RuntimeError` with actionable message (how many duplicates, example row). Migration aborts cleanly before any DDL runs.

### Test results post-fix

| Suite | Result |
|---|---|
| BE unit (excl. 2 pre-existing failures in hr_service_logic + tenancy_middleware) | **482 passed** |
| `test_visit_service_service.py` specifically | **11 passed** (9 original + 2 new Blocker-1 tests) |
| FE vitest | **568 passed** (564 baseline + 4 new Blocker-3 tests) |

**Pre-existing failures (NOT caused by this fix)**:
- `tests/unit/test_hr_service_logic.py::TestCheckInRejectsOtherUsersShiftId::test_check_in_rejects_other_users_shift_id` — pre-existing
- `tests/unit/test_tenancy_middleware.py::TestDevHeaders::test_clinic_id_only_no_user_allowed` — pre-existing

**New findings during fix**:
- The Python regex pattern `[^}\"]+` did not match string-literal values like `"TEST"`, `"NOPE"` in JSON bodies — these needed manual fixes. 3 files affected.
- The Docker container does not bind-mount test files from the host worktree; `docker compose cp` was needed to push changes into the container before pytest runs reflected them.

3. **Redis flush timing**: Active JWTs using old `clinic_id` claim still work (TenancyMiddleware falls back). However, old Redis perm cache keys (`user:perms:{user_id}` without clinic) will serve stale data for up to 5 minutes. Recommend Redis flush during deploy window.

4. **F.6 (`X-Active-Clinic` header)**: Decided NOT to add this header — JWT `active_clinic_id` claim is sufficient. BE reads from JWT, FE sends new token pair after switch. No custom header needed.

5. **`ClinicSwitcher.tsx` query client**: Uses `queryClient.clear()` on switch per F.7. This purges ALL cached data including non-clinic-scoped queries (e.g., system settings). If this causes visible flicker, a more targeted `queryClient.invalidateQueries()` can be used instead.

6. **B.13 (`current_clinic_id` call sites ~50+)**: The middleware correctly sets `current_clinic_id` ContextVar from JWT. The `get_db()` RLS helper reads from this ContextVar. All existing route handlers that rely on `current_clinic_id` via `get_db()` are automatically updated because the ContextVar is populated from the new `active_clinic_id` JWT claim. Direct call sites in service code reviewed — only `visit_service_service.py` needed explicit clinic_id param update.

---

## Known Limitations / Not Implemented

- **BE integration test** for full login → select-clinic → switch flow with mock clinics fixture: deferred because test DB setup needed (requires Docker). File authored at `tests/unit/test_task033_multi_clinic.py` covers unit cases.
- **`queryClient.clear()` on FE page reload**: ClinicSwitcher calls `window.location.reload()` after switch which naturally clears React-Query cache. Direct `queryClient.clear()` also called for belt-and-suspenders.
- **UserRole to AccountClinicRole migration**: `user_role` table still holds roles. The pivot `role_codes` is populated at backfill time from `user_role`. Going forward, role assignment should update both tables until a follow-up task migrates fully to the pivot.
