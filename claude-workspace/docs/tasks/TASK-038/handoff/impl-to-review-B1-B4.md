# TASK-038 B.1–B.4 — Handoff: Implementation → Review

**Date**: 2026-05-01
**Agent**: Code Implementation
**Scope**: NFR-027 Password Policy — history (B.1), change_password enforcement (B.2), rotation cron (B.3), FE banner (B.4)

---

## 1. BE Files Changed (`clinic-cms-w1b` on `feature/task-038-b1-password-history`)

| File | Change |
|------|--------|
| `alembic/versions/0021_password_history_and_rotation.py` | NEW — creates `password_history` table + adds `user.must_rotate BOOLEAN DEFAULT false` |
| `app/modules/users/models/user.py` | Added `must_rotate: Mapped[bool]` column |
| `app/modules/users/models/password_history.py` | NEW — ORM model for `password_history` table |
| `app/modules/auth/services/auth_service.py` | Updated imports, added `_PASSWORD_HISTORY_DEPTH=5`, `_get_password_history()`, `_insert_password_history()`, updated `change_password()` (history check + archive + trim + must_rotate clear), updated login response to include `password_expired` |
| `app/modules/auth/schemas/auth_schemas.py` | Added `password_expired: bool = False` to `UserInfo` |
| `app/modules/auth/api/routes.py` | Pass `password_expired` through in login response |
| `app/workers/jobs/password_rotation.py` | NEW — daily cron job marking stale passwords with `must_rotate=true` |
| `app/workers/scheduler.py` | Registered `password_rotation_check` in `functions` + `cron_jobs` (daily 02:00 UTC) |
| `tests/unit/test_password_history.py` | NEW — 9 unit tests for history helpers + `change_password` |
| `tests/unit/test_password_rotation.py` | NEW — 6 unit tests for cron job |
| `tests/integration/test_change_password.py` | Added `test_password_matches_history_returns_400` (1 new test) |

---

## 2. FE Files Changed (`clinic-cms-web` on `feature/task-038-b1-password-history-fe`)

| File | Change |
|------|--------|
| `src/stores/authStore.ts` | Added `must_rotate?: boolean` to `UserInfo` interface |
| `src/pages/auth/ChangePasswordPage.tsx` | Added `must_rotate` banner with `AlertTriangle` icon; imported `useAuthStore`; handles `detail.includes("last 5")` server error |
| `src/tests/shell/ChangePasswordPage.test.tsx` | NEW — 6 unit tests for banner visibility + accessibility |

---

## 3. Migration Details

| Key | Value |
|-----|-------|
| Migration file | `0021_password_history_and_rotation.py` |
| Revision ID | `0021` |
| Down-revision | `65fc9ae59ba5` (current HEAD before this task) |
| New table | `password_history(user_id PK, changed_at PK, password_hash)` with FK→user(id) CASCADE + index on user_id |
| New column | `user.must_rotate BOOLEAN NOT NULL DEFAULT false` |
| Type | ADDITIVE — no existing data destructed; backfill by default |

---

## 4. Test Results

### BE unit tests
```
tests/unit/test_password_history.py  — 9 PASSED
tests/unit/test_password_rotation.py — 6 PASSED
Total new unit tests: 15 PASSED
```

### BE integration tests (new test only)
```
tests/integration/test_change_password.py::test_password_matches_history_returns_400 — PASSED
tests/integration/test_change_password.py (total pre-existing, excluding 1 DB-only): 4 PASSED
```

Note: `test_missing_new_password_returns_422` requires live Postgres — pre-existing env limitation in isolated Docker (not caused by this change).

### FE unit tests
```
src/tests/shell/ChangePasswordPage.test.tsx — 6 PASSED
Full suite: 535 PASSED across 50 test files (0 failures)
```

---

## 5. Key Design Decisions

1. **Login response field name**: Used `password_expired` (not `must_rotate`) in the login API response to match the existing `LoginPage.tsx` logic that already reads `user.password_expired`. Internally the DB column is `must_rotate`.

2. **`must_rotate` cleared on successful password change**: When `change_password` succeeds, `user.must_rotate = False` is set so subsequent logins don't re-trigger the forced redirect.

3. **History check includes current hash**: The "last 5" reuse check verifies both the archived history table entries AND the current `password_hash` (since it hasn't been archived yet), effectively preventing reuse of 6 passwords total (current + last 5). This matches the spirit of NFR-027.

4. **Trim strategy**: After insert, a DELETE keeps only the newest `_PASSWORD_HISTORY_DEPTH` rows, ensuring the table stays bounded.

5. **FE banner placement**: The `must_rotate` banner appears above the form card (not inside it), making it visually distinct from the server-error div.

---

## 6. Deferred / Out of Scope

- **Backfill of `password_changed_at`** for legacy users where it is NULL: the column already existed from migration `0005` but rows pre-dating its introduction may have NULL. The cron query uses `password_changed_at < now() - 90 days`, so NULL rows are not flagged (IS NULL is not `<`). A follow-up backfill UPDATE (`SET password_changed_at = created_at WHERE password_changed_at IS NULL`) can be added in a separate migration when needed.
- **Pepper** for bcrypt: Not implemented (marked as optional in NFR-027).
- **B.5–B.17** (anomaly detection, MFA, PII lifecycle): separate sub-tasks.
