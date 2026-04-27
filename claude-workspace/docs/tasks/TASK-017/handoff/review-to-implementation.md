# Handoff: TASK-017 → Code Implementation Agent

**From**: Code Review Agent
**To**: Code Implementation Agent
**Status**: IN_PROGRESS
**Decision**: CHANGES_REQUESTED
**Date**: 2026-04-27

---

## Summary

Solid breadth-first implementation — 136/136 tests pass, tsc clean, capabilities wired, permission gate correct. Blocked on one CRITICAL security misrepresentation in the Rust secure store, plus four MAJOR issues (auth-state hydration bug, ASCII-transliterated Vietnamese locale, redundant token writes in the refresh path, and missing tests/race in the refresh-failure path). Fix the Critical + the four Majors and resubmit.

Full review at `docs/tasks/TASK-017/handoff/review-report.md`.

---

## Required Changes

### CRITICAL

#### C1. Fix secure_store.rs — code/docstring mismatch on encryption
**File**: `clinic-cms-web/src-tauri/src/secure_store.rs`

The first 14 lines claim AES-GCM encryption with a machine-derived key. The actual implementation writes plaintext JSON via `serde_json::to_string` + `fs::write`. Pick ONE:

- **Option A (faster)**: Make the docstring honest. Replace the opening doc-comment with something like:

  ```rust
  /// **PLAINTEXT** token storage — v1 MVP only.
  ///
  /// SECURITY: Tokens (access + refresh JWT) are written to a JSON file in
  /// `app_data_dir/secure_tokens.json` with **NO encryption**. Any process
  /// running as the user can read them. This is acceptable only for v1 on
  /// managed clinic workstations. PRODUCTION TODO: replace with the
  /// `keyring` crate (Windows Credential Manager / macOS Keychain).
  ```

  Add `log::warn!("[secure_store] using plaintext fallback — replace with keyring before production")` in `save_store` (gated to fire once, e.g., via `std::sync::Once`).

  On Unix, set file mode `0o600` after `fs::write`:
  ```rust
  #[cfg(unix)]
  {
      use std::os::unix::fs::PermissionsExt;
      let perms = std::fs::Permissions::from_mode(0o600);
      std::fs::set_permissions(&path, perms)?;
  }
  ```

- **Option B (proper fix)**: Add `keyring = "2"` to `src-tauri/Cargo.toml` and rewrite the three commands to call `keyring::Entry::new("clinic-cms", &key).set_password(&value)` / `get_password` / `delete_password`. Remove `get_store_path`, `load_store`, `save_store`, `STORE_FILE`, `TokenStore`. Update the docstring to describe the real backend.

Either way: the docstring and the code must agree, and there must be no code path that silently writes plaintext while documentation says otherwise.

---

### MAJOR

#### M1. authStore.loadFromStorage must restore (or invalidate) `user`
**File**: `clinic-cms-web/src/stores/authStore.ts:80-96`

Currently `loadFromStorage` sets `isAuthenticated: true` while leaving `user: null`. After app restart, `RequirePermission` then hides every permission-gated nav item (including ones the user is entitled to). Choose one:

- **Persist user**: in `setTokens`, also `secureSet(TOKEN_KEYS.USER, JSON.stringify(user))`; in `loadFromStorage`, parse it and `set({ user: parsed, ... })`. Add `USER: "auth.user"` to `TOKEN_KEYS` in `secureStore.ts`. Combine with C1.
- **Re-fetch user**: keep `isAuthenticated: false` initially; in `App.tsx`, after `loadFromStorage`, call `GET /api/v1/auth/me` (or whatever endpoint exposes the current user/permissions) and only set `isAuthenticated: true` after `user` is populated. Show a splash screen while hydrating. On 401, call `logout()` + redirect to `/login`.

Add a test in `authStore.test.ts` verifying that after `loadFromStorage` either (a) `user` is non-null, or (b) `isAuthenticated` is false until `user` is hydrated. The current test `"loadFromStorage sets isAuthenticated when tokens exist"` allows the broken state — update or replace it.

#### M2. Replace transliterated Vietnamese with proper UTF-8 (with diacritics)
**Files**: `clinic-cms-web/src/locales/vi/{auth,common,shell,validation}.json`

Examples that need fixing:
- `"Dang nhap he thong"` → `"Đăng nhập hệ thống"`
- `"Mat khau"` → `"Mật khẩu"`
- `"Ma phong kham"` → `"Mã phòng khám"`
- `"Doi mat khau"` → `"Đổi mật khẩu"`
- `"Tai khoan bi khoa do nhap sai qua nhieu lan. Vui long lien he quan tri vien."` → `"Tài khoản bị khóa do nhập sai quá nhiều lần. Vui lòng liên hệ quản trị viên."`
- `"Truong nay la bat buoc"` → `"Trường này là bắt buộc"`
- `"Tong quan"` → `"Tổng quan"`
- `"Tiep tan"` → `"Tiếp tân"`
- `"Bac si"` → `"Bác sĩ"`
- `"Nha thuoc"` → `"Nhà thuốc"`
- `"Truc tuyen"` → `"Trực tuyến"`
- `"Ngoai tuyen"` → `"Ngoại tuyến"`

(Translate ALL keys in all four `vi/*.json` files — the items above are illustrative.)

Verify the i18n test still passes (it doesn't assert specific Vietnamese characters). If you want defense-in-depth, add one assertion in `i18n.test.ts` that a known Vietnamese key contains a diacritic character (e.g., `expect(t).toMatch(/[ăâđêôơư]/i)`).

#### M3. Refactor token-rotation path in apiClient — single store call, await it, don't stomp `user`
**File**: `clinic-cms-web/src/lib/apiClient.ts:51-57`

Replace:
```ts
const { access_token, refresh_token, user } = data.data;
const store = useAuthStore.getState();
await store.updateAccessToken(access_token);
await store.updateRefreshToken(refresh_token);
store.setTokens(access_token, refresh_token, user);  // not awaited; overwrites user
```

with a single-purpose method on the store:

```ts
// In authStore.ts
rotateTokens: async (accessToken, refreshToken) => {
  await Promise.all([
    secureSet(TOKEN_KEYS.ACCESS_TOKEN, accessToken),
    secureSet(TOKEN_KEYS.REFRESH_TOKEN, refreshToken),
  ]);
  set({ accessToken, refreshToken });  // do NOT touch user
},
```

```ts
// In apiClient.ts
const { access_token, refresh_token } = data.data;
await useAuthStore.getState().rotateTokens(access_token, refresh_token);
```

This (a) writes the secure store once with parallel IPC, (b) preserves the existing `user` (since the BE refresh response may not include a fresh user object), and (c) is awaited.

Drop the now-unused `updateAccessToken`/`updateRefreshToken` if no other caller uses them, OR keep them for explicit single-token updates and only switch the refresh path. Update tests in `authStore.test.ts` accordingly.

#### M4. Refresh-failure path: prefer router navigate; add happy-path + recursion-prevention tests
**File**: `clinic-cms-web/src/lib/apiClient.ts:99-117`, `src/tests/shell/apiClient.test.ts`

Two parts:

1. **Add tests** (these are the gating ones):

   ```ts
   // happy path
   it("retries original request after successful refresh", async () => {
     mockFetch
       .mockResolvedValueOnce({ ok: false, status: 401, json: ...({ error: "AUTH_TOKEN_EXPIRED" }) })  // original
       .mockResolvedValueOnce({ ok: true, status: 200, json: ...({ data: { access_token: "new-a", refresh_token: "new-r" }}) })  // refresh
       .mockResolvedValueOnce({ ok: true, status: 200, json: ...({ result: "after-refresh" }) });    // retry
     const result = await api.get<{ result: string }>("/api/v1/test");
     expect(result.result).toBe("after-refresh");
     expect(mockFetch).toHaveBeenCalledTimes(3);
   });

   // recursion guard
   it("does not infinite-loop when refresh endpoint itself returns 401", async () => {
     mockFetch
       .mockResolvedValueOnce({ ok: false, status: 401, json: ...({ error: "AUTH_TOKEN_EXPIRED" }) })
       .mockResolvedValueOnce({ ok: false, status: 401, json: ...({ error: "AUTH_REFRESH_REVOKED" }) });  // refresh fails
     await expect(api.get("/api/v1/test")).rejects.toThrow("AUTH_SESSION_EXPIRED");
     // exactly 2 fetches: 1 original + 1 refresh attempt; NOT 3+
     expect(mockFetch).toHaveBeenCalledTimes(2);
   });

   // concurrent dedup
   it("dedupes concurrent 401s onto a single refresh call", async () => {
     mockFetch
       .mockResolvedValueOnce({ ok: false, status: 401, json: ...({ error: "AUTH_TOKEN_EXPIRED" }) })
       .mockResolvedValueOnce({ ok: false, status: 401, json: ...({ error: "AUTH_TOKEN_EXPIRED" }) })
       .mockResolvedValueOnce({ ok: true, status: 200, json: ...({ data: { access_token: "x", refresh_token: "y" }}) })  // single refresh
       .mockResolvedValueOnce({ ok: true, status: 200, json: ...({ result: "a" }) })
       .mockResolvedValueOnce({ ok: true, status: 200, json: ...({ result: "b" }) });
     const [a, b] = await Promise.all([api.get("/api/v1/a"), api.get("/api/v1/b")]);
     // exactly ONE refresh in the call sequence
     const refreshCalls = mockFetch.mock.calls.filter(c => c[0].includes("/auth/refresh"));
     expect(refreshCalls).toHaveLength(1);
   });
   ```

2. **Optional refactor**: replace `window.location.hash = "#/login"` with router-aware navigation. Acceptable workaround: keep the hash assignment but stop the `throw` from racing with `Navigate` — wrap the `logout()` + redirect in a microtask so the route guard sees the new state first.

---

## MINOR (please address but not blocking)

- **m1**: add `.eslintrc.cjs` with `@typescript-eslint/recommended` + `plugin:react/recommended` + `plugin:react-hooks/recommended` so `npm run lint` works. Update PROJECT.md if needed.
- **m3**: remove the dead `get(); // no-op — triggers any watchers` line in `authStore.ts:106`.
- **m5**: change "Forgot password?" `<a href="#">` in `LoginPage.tsx:280-285` to `<button type="button">` to avoid hash-route side effects.
- **m8**: translate the hardcoded English aria-labels in `Topbar.tsx:124, 138` (`"Switch to dark mode"`, `"User menu"`) — add keys to both `vi/shell.json` and `en/shell.json`.

(See review-report.md for m2, m4, m6, m7 — those are informational only; no action needed this round.)

---

## Acceptance Checklist for Re-Review

- [ ] C1 fixed: secure_store.rs code and docstring agree; either keyring crate or honest plaintext-with-warn + chmod 600 + clear TODO
- [ ] M1 fixed: `loadFromStorage` either restores `user` from secure store or defers `isAuthenticated: true` until `/auth/me` returns
- [ ] M2 fixed: all four `vi/*.json` use proper UTF-8 Vietnamese with diacritics
- [ ] M3 fixed: token rotation in apiClient uses a single awaited `rotateTokens` call that doesn't touch `user`
- [ ] M4 fixed: 3 new apiClient tests added (happy-path retry, recursion-guard, concurrent dedup) and pass
- [ ] All Minors above addressed (or explicitly deferred with rationale in handoff)
- [ ] `npm test -- --run` passes (≥ 136 + new tests)
- [ ] `npx tsc --noEmit` clean
- [ ] New handoff `implementation-to-review.md` describes the fixes

---

## Notes

The implementation is genuinely close. None of the issues above require architectural rework — they're targeted fixes. Estimate 2-3 hours for an experienced FE/Rust engineer to land all five blocking changes plus the four minors.

Do NOT regenerate the whole locale files via tool — type the diacritics directly. Watch for any place where the build pipeline might transcode UTF-8 (Vite handles this fine by default, but if you see mojibake in the rendered page, check `tsconfig.json` for unusual `target`/`module` settings or the editor's BOM mode).
