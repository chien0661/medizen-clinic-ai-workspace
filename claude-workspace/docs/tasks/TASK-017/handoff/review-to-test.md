# Handoff: TASK-017 → Test Agent

**From**: Code Review Agent (iter 2)
**To**: Test Agent
**Status**: IN_TESTING
**Date**: 2026-04-27
**Branch**: `feature/TASK-017-fe-shell` (HEAD `c545481`)
**Iter 1 verdict**: CHANGES_REQUESTED (1 CRIT, 4 MAJ, 8 MIN)
**Iter 2 verdict**: **APPROVED** — all blocking issues resolved.

---

## Quality gate snapshot at handoff time

| Check | Result |
|---|---|
| `npm test -- --run --reporter=basic` | **142/142 PASS** (16 test files) |
| `npx tsc --noEmit` | CLEAN (0 errors) |
| `npm run lint` (`eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0`) | CLEAN |

---

## What was fixed in iter 2 (relevant for testing)

### Behavioral changes you need to verify

1. **Auth persistence across restart (M1)** — On Tauri-app restart with valid tokens on disk, the user object is now restored from secure store. `loadFromStorage` reads `auth.user` JSON, parses with try/catch, gracefully falls back to `user: null` on corruption. Permission-gated sidebar items should now appear correctly for a returning Doctor/Admin/Pharmacist after closing and reopening the app.
   - **Test scenario**: Login as Doctor → close app → reopen → verify Doctor sidebar items still visible (Reception, Doctor; NOT Pharmacy/Admin).
   - **Negative scenario**: Manually corrupt `auth.user` in `secure_tokens.json` → reopen app → app should not crash; permission-gated items hidden until user re-authenticates.

2. **Token refresh path (M3, M4)** — `apiClient.ts` 401-refresh now uses `rotateTokens(access, refresh)` (single IPC roundtrip pair, never overwrites user). New behavior:
   - Concurrent 401s deduped onto a single `/auth/refresh` call.
   - Refresh endpoint itself returning 401 triggers `logout()` exactly once, no infinite loop.
   - On refresh failure: `logout()` runs first (synchronous Zustand `set`), then a microtask awaited via `await Promise.resolve()`, then `window.location.hash = "#/login"`. RequireAuth's React render fires before the hash assignment.
   - **Test scenario**: Set BE access-token TTL to 5s, wait, fire an action → verify rotation succeeds and original action retries (covered by AC "Refresh token rotate tự động").
   - **Test scenario**: Revoke BE refresh token, fire an action → verify single redirect to `/login` (no double-nav, no toast spam).

3. **Vietnamese locale (M2)** — All 4 `vi/*.json` files now contain proper UTF-8 with diacritics. Strings to spot-check at runtime:
   - LoginPage: "Đăng nhập hệ thống", "Mật khẩu", "Mã phòng khám", "Quên mật khẩu?"
   - Sidebar nav: "Tổng quan", "Bác sĩ", "Nhà thuốc", "Quản trị"
   - Topbar: "Thông báo", "Ngôn ngữ", "Đăng xuất"
   - Validation: "Trường này là bắt buộc", "Phải có ít nhất 8 ký tự"
   - **Test scenario**: Toggle vi ↔ en in topbar → verify all visible labels translate. AC "Đổi ngôn ngữ vi ↔ en: toàn bộ label translate".

4. **secure_store.rs (C1)** — Now plaintext-but-honest. On first call to `secure_store_set` (per process), an `eprintln!` warning fires:
   `[secure_store] WARNING: using plaintext file-backed storage. Tokens are NOT encrypted. Replace with the keyring crate before production.`
   On Unix the file is chmod 0o600. On Windows, file remains in `%APPDATA%/clinic-cms/` (already user-ACL-restricted).
   - **Test scenario** (Tauri dev mode): Login → confirm `secure_tokens.json` exists in `app_data_dir`, contains tokens, and the warning appears in stderr exactly once.
   - **Manual**: Verify the file is readable JSON (no encryption claim) and contains keys: `auth.access_token`, `auth.refresh_token`, `auth.user`, optionally `auth.clinic_id`, `auth.clinic_code`.

5. **UX nits (m5, m8)** —
   - LoginPage forgot-password is now a `<button type="button">` (no longer navigates).
   - Topbar theme-toggle and user-menu aria-labels are now translated.
   - **Test scenario**: With screen reader / accessibility inspector, verify aria-labels are in the active locale.

### New tests added in iter 2 (already passing locally)

- `authStore.test.ts` (+3 tests): persisted-user roundtrip, corrupted-user-JSON fallback to null, `rotateTokens` does not touch user.
- `apiClient.test.ts` (+3 tests): happy-path retry after refresh, recursion guard (refresh-401 → no loop), concurrent 401 dedup (single refresh call).

---

## Recommended test phases

### Phase A — Static / unit (can run on host without Rust toolchain)

```bash
cd ../clinic-cms-web
npm test -- --run         # Expect 142/142
npx tsc --noEmit          # Expect 0 errors
npm run lint              # Expect clean
```

### Phase B — Integration (requires Rust toolchain + Tauri dev mode in CI)

Use the AC checklist as the test plan:

1. **Login happy path** — correct creds → JWT in secure store → redirect to `/dashboard`.
2. **Login lockout** — 5 wrong attempts → countdown UI; verify both local 5-attempt counter and BE 423/429 paths.
3. **Token refresh rotation** — set access TTL = 5s, wait 6s, fire action → verify rotation, no user-flicker, no double-write.
4. **Persistent session** — login → close app → reopen → land on `/dashboard` with full sidebar (M1 verification).
5. **Permission filter** — login as Doctor → verify Pharmacy/Admin not in sidebar; login as Admin → verify all items visible.
6. **i18n toggle** — switch vi ↔ en in topbar → all labels (sidebar, topbar, login form, validation) translate; date/currency reformat (VND constant, separator changes).
7. **Theme toggle** — light ↔ dark, persisted via localStorage.
8. **Refresh failure** — revoke BE refresh token → next action triggers logout + redirect to `/login`.

### Phase C — Build / perf (CI only)

- `npm run tauri:build` → `.msi` (Windows) and `.dmg` (macOS).
- Lighthouse-style audit on production build: First Paint < 2s, TTI < 3s.

These are deferred items in the AC and do not block test approval; flag any failures as bugs.

---

## Known deferrals (NOT regressions)

These were explicitly accepted as out-of-scope for TASK-017 in iter 1 and remain unchanged:

- m2: Zod schema is rebuilt per render in LoginPage/ChangePasswordPage — informational, no action.
- m4: Topbar clinic-name hardcoded "Clinic CMS" — TASK-018 will wire from clinic context.
- m7: `secure_store.rs` has no Rust unit tests — deferred until keyring migration.
- AC "pnpm dev" / `.msi` / `.dmg` build / Lighthouse — deferred to CI per handoff.

---

## API contract gap to flag (for HE/PM)

`password_expired` field on the login response `user` object: TASK-003 spec is ambiguous. If BE doesn't return it, the forced redirect to `/change-password?forced=true` simply never fires (graceful degradation). Test agent should validate against the actual BE response and raise a bug if the BE+FE contract diverges.

---

## Files relevant to test scope

**Frontend logic / UI:**
- `src/lib/apiClient.ts` (refresh path)
- `src/lib/secureStore.ts` (Tauri IPC wrapper + browser fallback)
- `src/lib/i18n.ts` (i18next init)
- `src/lib/format.ts` (date/currency)
- `src/stores/authStore.ts` (persistence + rotation)
- `src/stores/settingsStore.ts` (theme + language)
- `src/components/auth/RequireAuth.tsx`
- `src/components/auth/RequirePermission.tsx`
- `src/components/error/ErrorBoundary.tsx`
- `src/components/shell/{AppShell,Sidebar,Topbar}.tsx`
- `src/pages/auth/{LoginPage,ChangePasswordPage}.tsx`
- `src/router/index.tsx`
- `src/locales/{vi,en}/*.json`

**Backend (Tauri):**
- `src-tauri/src/secure_store.rs`
- `src-tauri/src/lib.rs` (invoke_handler registration)
- `src-tauri/capabilities/default.json` (IPC permissions)

---

## Estimated test runtime

45-60 min if Tauri dev mode is available in CI. Without Tauri dev mode, ~20 min for static + unit phase only (Phase B blocked).

---

## Bug reporting protocol

Per CLAUDE.md: file bug reports to `docs/tasks/TASK-017/bugs/`. If a regression in 142/142 or in the iter 2 fixes is found, escalate immediately to Implementation Agent (status IN_TESTING → IN_PROGRESS).
