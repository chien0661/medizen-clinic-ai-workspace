# TASK-038 B.1-B.4 — Review Report (Code Review → Test)

**Date**: 2026-05-01
**Reviewer**: Code Review Agent
**Scope**: NFR-027 Password Policy — history (B.1) + change_password enforcement (B.2) + rotation cron (B.3) + FE banner (B.4)
**Branches reviewed**:
- BE: `clinic-cms-w1b` @ `feature/task-038-b1-password-history`
- FE: `clinic-cms-web` @ `feature/task-038-b1-password-history-fe`

---

## Decision

**CHANGES_REQUESTED** — One blocking integration bug (login → banner field mismatch) plus minor concerns. BE quality is solid; FE banner will not render in real flow.

---

## A. Migration Safety (B.1, B.3)

| Item | Status | Notes |
|------|--------|-------|
| `0021` revision id, down-revision `65fc9ae59ba5` matches HEAD | ✅ | Confirmed via grep over `alembic/versions/`. |
| `password_history` schema (composite PK + user_id index + FK CASCADE) | ✅ | Matches handoff spec. |
| `user.must_rotate BOOLEAN NOT NULL DEFAULT false` added | ✅ | Server-default `false` backfills existing rows safely. |
| `user.password_changed_at` already exists (migration `0005`) | ✅ | Not re-added. Pre-existing column reused — no schema conflict. |
| Backfill of NULL `password_changed_at` for legacy rows | ⚠️ | Deferred per handoff. Cron correctly skips NULL because SQL `NULL < timestamp` is `UNKNOWN` (not TRUE). Verified in `password_rotation.py` — the `<` comparator naturally drops NULLs. ✅ Safe but means legacy users **never** get flagged until they change once. Documenting follow-up backfill is fine. |
| Downgrade path | ✅ | `drop_column` → `drop_index` → `drop_table` order is correct (column first, then index/table). |
| Idempotency / model parity | ✅ | ORM `User.must_rotate` matches column; `PasswordHistory` ORM matches table (PK, FK CASCADE, server_default). |

**Concern**: ⚠️ Migration uses `sa.UUID(as_uuid=True)` — most other migrations in this repo use `postgresql.UUID(as_uuid=True)` for the user FK. Functionally equivalent on Postgres but slightly inconsistent. Non-blocking.

---

## B. History Rejection (B.2)

| Item | Status | Notes |
|------|--------|-------|
| Compares against last 5 hashes via `bcrypt.verify` (no plaintext compare) | ✅ | `verify_password()` from `app.core.security`, called per entry. |
| Inserts old hash BEFORE storing new hash | ✅ | Order in `change_password()` is correct: history insert (line 408), then `password_hash = new_hash` (line 411). |
| History trim keeps only last 5 | ✅ | `_insert_password_history` issues a `DELETE WHERE changed_at NOT IN (top-5)` after add+flush. |
| Also rejects re-use of current hash | ✅ | Extra explicit check at line 401-405. Effectively prevents re-use of 6 most recent passwords. Acceptable per NFR-027 spirit. |
| Error code 400 + meaningful message | ✅ | `HTTPException(400, "Password matches one of your last 5 passwords")`. FE matches via `detail.includes("last 5")`. |
| Race condition on concurrent change_password | ⚠️ | The select-then-insert is not atomic; a concurrent change for the same user could allow trim to drop one extra entry. Real-world risk LOW (single user rarely has parallel password changes), but flag for future work — could use `SELECT ... FOR UPDATE` on the user row. **Out of scope for this task.** |
| Vietnamese error text | ⚠️ | Server returns English `"Password matches one of your last 5 passwords"`. FE re-translates via i18n key `auth:changePassword.errors.passwordInHistory`, so user sees Vietnamese. ✅ acceptable. |

---

## C. Rotation Cron (B.3)

| Item | Status | Notes |
|------|--------|-------|
| Cron schedule daily 02:00 UTC | ✅ | `cron(password_rotation_check, hour=2, minute=0)` registered in `WorkerSettings.cron_jobs`. Worker function also added to `functions` list. |
| Async session usage | ✅ | Creates engine, session factory, `async with` session, commit, dispose engine in `finally`. Pattern matches other workers (e.g. `check_low_stock`). |
| Idempotent SQL — only flips `false→true` | ✅ | `WHERE must_rotate = false` clause prevents redundant updates. |
| Skips `is_deleted = true` | ✅ | Filter present. |
| Skips NULL `password_changed_at` | ✅ | `< now() - interval` naturally excludes NULL (SQL three-valued logic). |
| Audit log on flip | ❌ | **No audit entry written when `must_rotate` flips false→true.** This is a security-sensitive state change and should be auditable per the rest of the codebase (e.g. `user.password_changed` writes audit). Recommend adding a per-user audit insert OR a single summary audit row (`password_rotation_check.users_flagged: N`). **Non-blocking but log to test phase as a coverage gap.** |
| Engine disposal in `finally` | ✅ | Test `test_engine_always_disposed` verifies. |
| Error handling | ✅ | Exceptions caught + logged + returned in summary; cron does not crash worker. |

---

## D. Login Response (B.4 prerequisite)

| Item | Status | Notes |
|------|--------|-------|
| `password_expired` field returned in login response | ✅ | Service `auth_service.login()` line 181, route `routes.py` line 81, schema `UserInfo.password_expired: bool = False`. |
| Field name choice (`password_expired` vs `must_rotate`) | ⚠️ | BE uses `password_expired` in API to match LoginPage's existing `user.password_expired` redirect logic. **Defensible** — see Section E for the FE consequence. |
| Schema backward compatibility | ✅ | `password_expired: bool = False` default — old FE code that ignores the field still parses. |

---

## E. FE Banner (B.4) — **BLOCKING ISSUE**

| Item | Status | Notes |
|------|--------|-------|
| Banner renders when `user.must_rotate=true` | ❌ | **Bug:** BE login response sends `password_expired`, but FE `UserInfo` interface in `authStore.ts` defines only `must_rotate?`. `LoginPage.onSubmit` calls `setTokens(access_token, refresh_token, user)` where `user` carries `password_expired` (not `must_rotate`). `ChangePasswordPage` reads `Boolean(user?.must_rotate)` → always `false` in real flow. **Banner will never appear.** Tests pass because they inject `must_rotate=true` directly into mocked store, bypassing the real login mapping. |
| Vietnamese banner text correct | ✅ | "Mật khẩu đã hết hạn — vui lòng đổi mật khẩu" — natural Vietnamese. |
| Accessibility | ✅ | `role="alert"`, `aria-hidden` on icon, `data-testid` for tests. |
| Tailwind classes use OLD `brand-*`/`amber-*` (pre-TASK-039) | ✅ | Expected — FE branched from `main` not `feature/task-039-design-system`. **Documented**: when this merges with TASK-039 main, banner classes need migration to `indigo-*` per Stream B coordination. Flag for documentation phase. |
| Auto-redirect to ChangePasswordPage on dashboard with must_rotate | ⚠️ | LoginPage already redirects to `/change-password` when `password_expired=true` (line 173). However, if user lands on `/dashboard` via stored session and `must_rotate` becomes true mid-session, no auto-redirect exists. **Out of scope for this PR** (cron only flags daily; user re-logins eventually). Flag for future enhancement. |

### Required fix for E

One of the following two options must land before testing:

1. **Map BE → FE in LoginPage**: change `await setTokens(..., user)` to `await setTokens(..., { ...user, must_rotate: user.password_expired })`. Update `UserInfo` interface to keep both fields or drop `password_expired`.
2. **Rename FE field to match BE**: rename `must_rotate?` → `password_expired?` in `authStore.ts` AND `ChangePasswordPage.tsx` (`mustRotate = Boolean(user?.password_expired)`), AND update test fixtures.

Option 1 is preferred because it preserves the existing LoginPage semantics and keeps the internal FE concept tied to BE column name (`must_rotate` → DB) at the boundary mapping layer.

---

## F. Test Coverage

| Item | Status | Notes |
|------|--------|-------|
| 9 unit tests (history) — current/history match, accept valid, user_not_found, invalid_credentials | ✅ | Comprehensive. |
| 6 unit tests (rotation cron) — happy/no-users/db-error/disposal/days/keys | ✅ | Good coverage. |
| 1 integration test for 400 history-match on endpoint | ✅ | New test passes. |
| Negative test: nth+1 password (boundary) — re-use of 6th-oldest after trim should succeed | ❌ | **Missing.** `_insert_password_history` trims to 5; after a 6th change, the original (1st) password should be re-usable. No explicit test verifies this trim → re-use boundary. **Recommend adding in test phase.** |
| Concurrency test | ⚠️ | Out of scope per handoff. Acceptable. |
| Cron edge cases — all NULL `password_changed_at` (legacy clinic) | ⚠️ | Implicitly covered by `test_no_users_due` (rowcount=0). Good. |
| Audit log assertion for `user.password_changed` event | ⚠️ | `test_accepts_valid_new_password` patches `write_audit` but does NOT assert it was called. Flag minor coverage gap. |
| Audit assertion for cron flip | ❌ | No audit written by cron (see Section C). |
| FE banner integration test (real LoginPage → ChangePasswordPage) | ❌ | All 6 FE tests are unit-level; none catch the `password_expired` → `must_rotate` mismatch. **Add E2E or integration test in test phase.** |

---

## G. Implementation Hygiene

| Item | Status | Notes |
|------|--------|-------|
| Imports clean | ✅ | `delete`, `select` from `sqlalchemy`; `HTTPException` from `fastapi`; `PasswordHistory` from new model. |
| No hardcoded secrets / debug prints | ✅ | None spotted. `structlog` used consistently. |
| Type hints complete | ✅ | All new functions typed; `_get_password_history` returns `list[PasswordHistory]`, cron returns `dict`. |
| Cron uses `text()` parameterized SQL | ✅ | `:days` parameter properly bound — not vulnerable to injection (constant anyway). |
| `_PASSWORD_HISTORY_DEPTH` and `_ROTATION_DAYS` named constants | ✅ | Both exported as module-level for reuse / testability. |
| Random spot-check `password_history.py` model | ✅ | Clean ORM definition; FK CASCADE matches migration. |
| Random spot-check `password_rotation.py` worker | ✅ | Engine creation per-invocation is consistent with other workers; could use shared engine for perf, but matches local convention. |

---

## Summary of Blockers / Action Items for Test Phase

### Must fix before APPROVED → Test

1. **E: Login → Banner field mismatch.** BE returns `password_expired`, FE banner reads `must_rotate`. **Banner will never appear in real flow.** Implementation must either map at LoginPage or rename FE field. This is a B.4 functional regression.

### Recommended (non-blocking)

2. **C/F: Cron audit log gap.** Add a single audit row per cron run (`action="user.password_rotation_check"`, count in metadata) OR per-user audits when must_rotate flips.
3. **F: Add boundary test for trim-then-reuse** (6th password change → 1st password should be re-usable since it was trimmed out of the last-5 window).
4. **F: Assert `write_audit` was called in `test_accepts_valid_new_password`.**
5. **A: Migration UUID type style nit** — `sa.UUID(as_uuid=True)` vs `postgresql.UUID(as_uuid=True)` for consistency with other migrations.
6. **E (TASK-039 coordination)**: Banner uses `brand-*`/`amber-*` classes from `main`; document follow-up to migrate to `indigo-*` after TASK-039 merge — already noted in handoff.
7. **E (UX)**: No auto-redirect when must_rotate becomes true mid-session. Flag as future enhancement.

---

**Overall**: Backend implementation quality is strong (clean migrations, idempotent cron, solid history logic, good test coverage). The single integration bug at the login → banner boundary is the only blocker. Once mapped/renamed, this is ready for test phase.

**Next step**: Implementation agent re-spins FE branch with the field mapping fix (15-min change), re-runs FE tests, then re-submit for review or proceed directly to test phase if reviewer confidence is high.
