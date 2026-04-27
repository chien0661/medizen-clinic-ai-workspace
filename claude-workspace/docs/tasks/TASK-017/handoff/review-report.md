# Code Review Report — TASK-017 (FE Auth + App Shell + Design System + i18n)

**Reviewer**: Code Review Agent
**Date**: 2026-04-27
**Branch**: `feature/TASK-017-fe-shell` (commit `ca95d25`)
**Compared against**: `feature/TASK-016-tauri-foundation`
**Decision**: **CHANGES_REQUESTED**

---

## Summary

Implementation is broad in scope, well organized, and most of the surface area (capabilities, router, sidebar permission gate, lockout countdown, i18next wiring, ErrorBoundary, theme toggle, format helpers) is sound. Tests are green (136/136), `tsc --noEmit` is clean, and no hardcoded credentials or XSS vectors were found.

However, three issues block approval:

1. A **CRITICAL** security misrepresentation in the Rust secure store (docstring claims AES-GCM encryption; implementation writes plaintext JSON).
2. A **MAJOR** auth-state bug in `loadFromStorage` that leaves the user authenticated with a `null` user object on app restart, which collapses the entire permission-filtered sidebar.
3. A **MAJOR** i18n quality regression: Vietnamese strings ship as ASCII transliterations without diacritics, which violates AC "Đổi ngôn ngữ vi ↔ en: toàn bộ label translate" in spirit and would not be acceptable for clinic users.

A few additional MAJOR/MINOR issues are listed below.

Test pass: **136/136** (73 retained from TASK-016 + 63 new). No regressions.

---

## Quality Gate Results

| Check | Result |
|---|---|
| `tsc --noEmit` | PASS (0 errors) |
| `npm test -- --run` | PASS (136/136) |
| Test coverage (per handoff) | 83.85% lines / 77.04% functions / 77.57% branches — meets adjusted thresholds |
| ESLint | NOT RUN — no `.eslintrc*` / `eslint.config.*` in repo (MINOR) |
| SonarQube | SKIPPED (placeholder project key) |
| Visual inspection (Playwright) | SKIPPED (Tauri app, no browser) |
| `tauri build` / `tauri dev` | DEFERRED to CI (no Rust toolchain on host) |
| Hardcoded secrets grep | CLEAN |
| `dangerouslySetInnerHTML` / `eval` / `innerHTML=` grep | CLEAN |

---

## CRITICAL Issues

### C1 — Misleading "AES-GCM encryption" docstring; tokens stored as plaintext JSON
**File**: `src-tauri/src/secure_store.rs:1-15` and the entire module body
**Severity**: CRITICAL

The first line of the file states:

> Secure token storage using a simple AES-GCM encryption with a machine-derived key.

There is **no encryption**. `save_store` calls `serde_json::to_string(store)` and `std::fs::write(path, data)` — JWT access + refresh tokens land on disk in cleartext at `app_data_dir/secure_tokens.json`. Lines 12-13 then say:

> For now: tokens are stored in an encrypted JSON file in the OS app data directory. The encryption key is derived from the executable path (machine-specific).

Also untrue. There is no key derivation, no AES, no DPAPI call, no `keyring` crate — just `fs::write`.

This is a CRITICAL finding for two reasons:
- A future maintainer reading the docstring may believe the tokens are protected and therefore not prioritize the keyring migration.
- The handoff to the Test/Documentation agents also propagates this false claim (handoff section "Architectural Decisions §1" is honest about file-backed plaintext, but the source-of-truth comment in code disagrees with the handoff).

There is also no `chmod 600` (or Windows ACL equivalent) applied to the file, so any process running as the user can read the tokens.

**Required fix** — pick one path and make code + docstring agree:

- **Option A (preferred for v1):** rewrite the docstring to truthfully say "v1: PLAINTEXT JSON file in app_data_dir. NOT ENCRYPTED. TODO: replace with `keyring` crate before production." Add a `log::warn!("secure_store using plaintext fallback")` on first write. Restrict permissions on Unix (`std::os::unix::fs::PermissionsExt` → mode `0o600`).
- **Option B:** wire the `keyring` crate now (`keyring = "2"` in Cargo.toml; `keyring::Entry::new("clinic-cms", &key).set_password(&value)`). Remove the file path entirely.

Until one of these is done, the module is dishonest about its security posture.

---

## MAJOR Issues

### M1 — `loadFromStorage` does not restore `user`; permission-gated UI collapses after app restart
**File**: `src/stores/authStore.ts:80-96`
**Severity**: MAJOR

```ts
loadFromStorage: async () => {
  const [accessToken, refreshToken, clinicId, clinicCode] = await Promise.all([...]);
  if (accessToken && refreshToken) {
    set({
      accessToken,
      refreshToken,
      clinicId: clinicId ?? null,
      clinicCode: clinicCode ?? null,
      isAuthenticated: true,   // ← user remains null
    });
  }
},
```

After a restart with valid tokens on disk:
- `RequireAuth` lets the user into `/dashboard` (`isAuthenticated === true`).
- `RequirePermission` short-circuits on `if (!user) return fallback` (RequirePermission.tsx:38-40).
- Result: every permission-gated nav item in `Sidebar.tsx` is hidden, including items the user is entitled to. Only Dashboard + Settings (which use `permission: null`) remain.

This silently breaks AC "User Doctor không thấy menu Pharmacy/Admin (permission filter)" for the persistent-session path — a Doctor whose tokens are restored from disk would not see the Doctor menu either.

**Required fix**: choose one strategy and wire it end-to-end:
1. Persist a small subset of `user` (id, full_name, roles, permissions) in the secure store and restore it in `loadFromStorage`. (Tokens in plaintext already, so this is no worse — but combine with C1 fix.)
2. After `loadFromStorage` populates tokens, fire a one-shot `GET /api/v1/auth/me` (or whatever the BE exposes) to hydrate `user`. Show a splash/loading screen until it resolves; on 401 → logout + redirect to /login.

Either way, until `user` is non-null `isAuthenticated` should be `false` (or there should be a separate `isHydrating` flag).

### M2 — Vietnamese locale ships as ASCII transliteration (no diacritics)
**Files**: `src/locales/vi/{auth,common,shell,validation}.json`
**Severity**: MAJOR

Examples from `src/locales/vi/auth.json`:
- `"title": "Dang nhap he thong"` (should be `Đăng nhập hệ thống`)
- `"errors.accountLocked": "Tai khoan bi khoa do nhap sai qua nhieu lan..."` (should contain `Tài khoản bị khóa do nhập sai quá nhiều lần…`)
- `"changePassword.title": "Doi mat khau"` (should be `Đổi mật khẩu`)

The handoff (Areas for Review Focus §7) flags this and asks the reviewer to decide. The decision is: **not acceptable**. Vietnamese clinic staff will read these as broken/typo-ridden text. The AC explicitly says "toàn bộ label translate, ngày/tiền theo locale" — translation in spirit means proper Vietnamese, not transliterated Latin.

JSON files are UTF-8 and i18next handles UTF-8 fine; there is no encoding blocker. The only thing the implementation agent needed was to type the diacritics. This must be fixed before the task is acceptable for clinic deployment.

**Required fix**: replace all four `vi/*.json` files with proper UTF-8 Vietnamese text including diacritics. Verify by opening one of the rendered pages in a browser-only Vite dev mode and confirming the strings render correctly.

### M3 — `apiClient.refreshTokenOnce` redundantly writes tokens twice and stomps `user`
**File**: `src/lib/apiClient.ts:51-57`
**Severity**: MAJOR

```ts
const data: RefreshResponse = await response.json();
const { access_token, refresh_token, user } = data.data;
const store = useAuthStore.getState();
await store.updateAccessToken(access_token);     // writes to secure store (1)
await store.updateRefreshToken(refresh_token);   // writes to secure store (2)
store.setTokens(access_token, refresh_token, user); // writes again (3,4) AND not awaited
```

Three independent issues here:

1. `setTokens` is `async` in the store but the call is **not awaited**. The race is mostly benign (the in-memory `set({...})` runs synchronously) but the secure store IPC writes overlap in time with the previous `updateAccessToken`/`updateRefreshToken` writes — under Tauri the underlying `fs::write` is not guaranteed to serialize.
2. Three back-to-back IPC roundtrips per refresh (vs. a single combined "rotateTokens" call) is wasteful and slows the auth-recovery path on slow disks.
3. If the BE `/auth/refresh` response shape doesn't include `user` (the TASK-003 spec is ambiguous — handoff Areas §5 acknowledges this), `user` becomes `undefined` and `setTokens` overwrites the existing user object with `undefined`, causing the same sidebar-collapse problem as M1 even in mid-session.

**Required fix**: collapse to a single store method (e.g., `rotateTokens(access, refresh)` that does NOT touch `user`) and `await` it:

```ts
await store.rotateTokens(access_token, refresh_token);
// Do NOT call setTokens here — keep the existing user; if the BE rotates user info,
// add a separate updateUser path triggered by a /me endpoint.
```

### M4 — Refresh-failure path can race the route guard; throw vs. navigate ordering
**File**: `src/lib/apiClient.ts:109-115`
**Severity**: MAJOR

```ts
if (refreshed) { ... }
else {
  const store = useAuthStore.getState();
  await store.logout();
  window.location.hash = "#/login";
  throw new Error("AUTH_SESSION_EXPIRED");
}
```

`store.logout()` flips `isAuthenticated` to false, which causes any currently-mounted `RequireAuth` components to render `<Navigate to="/login" />`. Then `window.location.hash = "#/login"` runs. Then the thrown error bubbles into a TanStack Query handler. Two concurrent navigations into `/login` is benign in React Router, but the `throw` after `window.location.hash =` can show a brief unhandled-promise toast from Sonner if a query is in flight. More importantly, if the refresh endpoint itself returns 401 (revoked refresh token), the code path is fine — but if it returns 401 AND there's a race with another 401 retry already waiting on `refreshPromise`, the second caller sees `refreshed === false`, calls `logout()` again, and `setHash` again. Idempotent but noisy.

Also: there is no test for the "refresh succeeds, original request retried" happy path. The single test that touches refresh (`apiClient.test.ts:126-145`) only verifies the failure case.

**Required fix**:
- Use React Router's `navigate()` instead of `window.location.hash` (this requires hoisting the auth-redirect logic into a hook or a router-aware effect; alternative: keep `hash =` but document it as the no-router fallback).
- Add a happy-path test: mock first response 401, refresh response 200, retry response 200 → assert that the final result is the retried response and that `refreshPromise` is reset to null.
- Add a test verifying the refresh endpoint itself returning 401 doesn't infinite-loop (the `_isRetry` guard should prevent it; codify that with a test).

---

## MINOR Issues

### m1 — ESLint not configured
No `.eslintrc*` or `eslint.config.*` exists. The acceptance criteria says "CI: lint (eslint), type check (tsc), test (vitest), build (tauri build)". `tsc` and `vitest` work; `eslint` fails because there is no config. Add a minimal `.eslintrc.cjs` (recommended-react + typescript-eslint) in this task or follow-up.

### m2 — Validation messages built inside component body each render
**File**: `src/pages/auth/LoginPage.tsx:76-81`, `ChangePasswordPage.tsx:32-45`

The Zod schema is rebuilt on every render because it captures `t()`. Functionally correct; performance-wise harmless for these small forms. If kept, fine. Alternatively use a Zod custom error map fed by i18n once at startup (handoff §"i18n pitfalls" asks about this).

### m3 — `updateRefreshToken` ends with a no-op `get()` call
**File**: `src/stores/authStore.ts:106` — `get(); // no-op — triggers any watchers`

`get()` does not trigger watchers in Zustand; only `set()` does. The line is dead. Remove it or replace with a real subscription if there is intent.

### m4 — `Topbar` clinic-name placeholder is hardcoded "Clinic CMS"
**File**: `src/components/shell/Topbar.tsx:74-78`

The comment says it will be resolved in TASK-018. Acceptable as a placeholder, but it is not pulled from i18n and not from any clinic-context value. Confirm TASK-018 picks this up.

### m5 — `forgotPassword` link is `href="#"`
**File**: `src/pages/auth/LoginPage.tsx:280-285`

Clicking it changes the hash and triggers HashRouter navigation to an unintended location. Either make it `<button type="button" onClick={...}>` or `<a href="#/login">` so it is idempotent. Currently low-impact because the click navigates back to itself, but it's untidy.

### m6 — Dialog `dangerouslySetInnerHTML`-equivalents
None. (Verified clean — listing for completeness.)

### m7 — `secure_store.rs` is excluded from Rust unit tests
The empty `#[cfg(test)] mod tests` documents that integration tests need a real `AppHandle`. Acceptable, but the file currently has zero compile-time test coverage. Once the keyring migration happens, add at least round-trip tests via a mock `AppHandle`.

---

## Strengths Worth Calling Out

- `capabilities/default.json` correctly enumerates the three new IPC commands. Production Tauri build will not silently block `secure_store_*`.
- `RequirePermission` uses `Array.includes` for **exact** match, not substring, and treats empty/null permission arrays as "no access" by default. The component is concise and well tested (6 tests, including the AC-specific "Doctor cannot see Admin" case).
- Refresh deduplication via `refreshPromise` singleton in `apiClient.ts:21,63-70` is the right pattern (modulo M3/M4 fixes).
- `format.ts` correctly always uses VND and only varies the locale for separator style. Documented and tested.
- `ErrorBoundary.tsx` is a textbook implementation; logs errors via `console.error` (no sensitive data exposure) and supports custom fallback.
- HashRouter for Tauri is the right call; documented in the handoff.
- `i18next` is initialized **before** `AppRouter` mounts (App.tsx:23 imports `./lib/i18n` at module load) so there is no flash of untranslated content.
- Test isolation in `RequirePermission.test.tsx` resets the auth store via `beforeEach` — no test pollution.
- No console.log left behind in production code paths (only `console.error` in ErrorBoundary).

---

## Concerns Specifically Raised in the Brief

1. **Tauri capabilities updated** → CONFIRMED. All 3 commands are listed.
2. **Secure store v1** → see C1. File path is correct (`app_data_dir`), but file is plaintext, no chmod 600, and the docstring lies about AES-GCM. CRITICAL.
3. **apiClient 401 auto-refresh** → see M3, M4. Dedup pattern correct, retry correct, but redundant writes and missing happy-path test.
4. **Permission gate** → CONFIRMED correct (exact match, null-safe, returns null fallback). No issues.
5. **i18n pitfalls** → see M2. Also note: Zod schema messages route through `t("validation:...")` inside component (correct pattern); no hardcoded English/Vietnamese in `*.tsx` validators. Aria-labels in Topbar at line 124 ("Switch to dark mode") and 138 ("User menu") are NOT translated — minor, raise as m8.
6. **No TASK-016 regressions** → CONFIRMED 136/136 pass.
7. **Hardcoded secrets** → CONFIRMED clean.

### m8 (added from §5 above) — Hardcoded English aria-labels in Topbar
**File**: `src/components/shell/Topbar.tsx:124, 138`
- `aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}`
- `aria-label="User menu"`

Should use `t("shell:topbar.themeToggle.toLight"/"toDark")` and `t("shell:topbar.userMenu.label")`. Add the keys to both vi/en `shell.json`. MINOR.

---

## Decision: CHANGES_REQUESTED

| Severity | Count |
|---|---|
| CRITICAL | 1 |
| MAJOR | 4 |
| MINOR | 8 |

Status transition: **IN_REVIEW → IN_PROGRESS**.

The Critical (C1) and Majors (M1, M2, M3, M4) must be resolved before re-review. Minors are nice-to-haves and can be deferred to a follow-up cleanup commit if the implementation agent prefers, but should at least be acknowledged.

After fixes, re-run `npm test -- --run` (must remain 136/136 or higher with new tests covering M3/M4) and `npx tsc --noEmit` (must remain clean), then re-submit for review.

---

## Next Steps for Implementation Agent

See `review-to-implementation.md` in this folder for the prioritized action list.

---

## Iteration 2 Review

**Reviewer**: Code Review Agent
**Date**: 2026-04-27
**Branch**: `feature/TASK-017-fe-shell` (HEAD `c545481`, 6 fix commits on top of `ca95d25`)
**Decision**: **APPROVED**

### Quality Gates (re-run)

| Check | Result |
|---|---|
| `npm test -- --run --reporter=basic` | **PASS — 142/142** (16 test files, +6 vs iter 1) |
| `npx tsc --noEmit` | PASS (0 errors, 0 output) |
| `npm run lint` (new) | PASS (0 warnings, 0 errors with `--max-warnings 0`) |
| `git diff ca95d25..HEAD --stat` | 14 files, +422 / -126 |

### Iter 2 commit verification

| # | Hash | Issue | Verdict | Evidence |
|---|------|-------|---------|----------|
| C1 | `ee1070e` | secure-store false AES-GCM claim | **VERIFIED** | Docstring rewritten as `**PLAINTEXT** token storage — v1 MVP only`. `TODO(security)` block at top points to keyring crate. `std::sync::Once` guards single `eprintln!` warning on first save. `#[cfg(unix)]` `PermissionsExt::from_mode(0o600)` applied after every save. Code matches docs. |
| M1 | `e1b5993` | `loadFromStorage` left `user: null` | **VERIFIED** | `TOKEN_KEYS.USER = "auth.user"` added. `setTokens` JSON-encodes user via `JSON.stringify(user)` in `Promise.all`. `loadFromStorage` reads `userJson`, parses with `try/catch` — corrupted JSON gracefully sets `user = null`. `logout` also deletes USER key. |
| M3 | `34d2113` (+ `e1b5993`) | apiClient triple-write + user stomp | **VERIFIED** | `rotateTokens(access, refresh)` added to authStore — single `Promise.all` IPC + `set({accessToken, refreshToken})`, no user touch. `apiClient.doRefresh` calls `await rotateTokens(...)` in single line. `RefreshResponse.user` field deleted from interface. |
| M4 | `34d2113` | redirect race + missing tests | **VERIFIED** | `await Promise.resolve()` defers `window.location.hash` after `logout()` so RequireAuth re-renders first. 3 new tests pass: happy-retry (`rotateTokens` called with new tokens), recursion guard (refresh-401 → exactly 2 fetches, no loop, logout once), concurrent dedup (2 parallel 401s → exactly 1 refresh fetch, `rotateTokens` called once). |
| M2 | `9e05b9e` | vi locales as ASCII transliteration | **VERIFIED** | All 4 vi files now contain proper UTF-8 diacritics. Spot-checks: `Đăng nhập hệ thống`, `Mật khẩu`, `Mã phòng khám`, `Tên đăng nhập`, `Đổi mật khẩu` (auth.json); `Tổng quan`, `Bác sĩ`, `Nhà thuốc`, `Tiếp tân`, `Quản trị` (shell/nav); `Đang tải...`, `Hủy`, `Xác nhận`, `Trực tuyến`, `Ngoại tuyến` (common); `Trường này là bắt buộc`, `Phải có ít nhất {{min}} ký tự`, `Định dạng không hợp lệ` (validation). NO ASCII transliteration remains. Bonus: `themeToggle.{toDark,toLight}` and `userMenu.label` keys added to both vi and en `shell.json`. |
| m5 | `9f22d68` | `<a href="#">` forgot-password | **VERIFIED** | Replaced with `<button type="button">` with matching styles. No more hash-route side effect. |
| m8 | `9f22d68` | hardcoded English aria-labels | **VERIFIED** | Topbar.tsx now uses `t("shell:topbar.themeToggle.toDark"/"toLight")` and `t("shell:topbar.userMenu.label")`. Both vi and en bundles populated. |
| m1 | `9f22d68` + `c545481` | no ESLint config | **VERIFIED** | `.eslintrc.cjs` added: `eslint:recommended` + `plugin:@typescript-eslint/recommended` + `plugin:react-hooks/recommended` + `react-refresh/only-export-components` (warn). Sane unused-vars rule with `_`-prefix exception. Override correctly **scoped** to `src/components/ui/**` to disable react-refresh rule for shadcn co-export pattern (NOT a blanket disable). `npm run lint` passes with `--max-warnings 0`. |
| m3 | `e1b5993` | dead `get()` no-op | **VERIFIED** | Removed from `updateRefreshToken`. |

### Deferred minors (acknowledged, not blocking)

- m2 (Zod schema rebuilt per render) — noted as informational in iter 1
- m4 (Topbar clinic-name hardcoded) — original review note allows deferral to TASK-018
- m6 (no `dangerouslySetInnerHTML`) — already clean, no action needed
- m7 (secure_store.rs empty test block) — deferred until keyring migration

These do not block approval per iter 1 decision rules.

### Regressions

- None. Test count grew 136 → 142 (+6 net new). All prior tests retained. tsc still clean. New ESLint gate clean.

### Final tally

- **CRITICAL**: 1/1 fixed
- **MAJOR**: 4/4 fixed
- **MINOR**: 4/8 fixed (4 deferred per agreement)

### Decision: APPROVED

Status transition: **IN_REVIEW → IN_TESTING**.

Implementation faithfully addresses every blocking issue from iter 1. The secure-store module is now honest about its threat model and includes a single-fire warning + Unix permission hardening; auth state correctly survives restart with graceful corruption handling; the refresh path is concurrent-safe with three new tests pinning the contract; the Vietnamese locale renders properly for clinic users; ESLint is wired and clean; the small UX nits (forgot-pwd hash, aria-labels) are resolved.

See `review-to-test.md` for the Test Agent handoff.
