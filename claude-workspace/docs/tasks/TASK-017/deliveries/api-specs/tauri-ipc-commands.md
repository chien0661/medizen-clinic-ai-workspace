# Tauri IPC Commands Consumed by FE — Reference

**Date:** 2026-04-27
**Task References:** TASK-016 (Tauri Foundation), TASK-017 (FE Auth + Shell)
**Status:** Phase A (implementation + mocking; Phase B runtime validation deferred)

---

## Overview

Frontend (TASK-017) consumes Tauri IPC commands provided by the Tauri backend (TASK-016). This is a **reference-only** document; the actual command definitions and implementations are TASK-016 deliverables.

FE calls are made via `lib/secureStore.ts` (token management) and other foundation hooks.

---

## Commands Summary

| Command | Source | Purpose | Response Type |
|---------|--------|---------|----------------|
| `secure_store_get` | TASK-016 | Retrieve stored secret (token/clinic-id/user JSON) from encrypted/secure backend | String or null |
| `secure_store_set` | TASK-016 | Store secret (token/clinic-id/user JSON) in encrypted/secure backend | void |
| `secure_store_delete` | TASK-016 | Delete stored secret from backend | void |
| `health_check` | TASK-016 | Verify Tauri runtime + Rust backend alive | `{status: "ok"}` |
| `get_app_config` | TASK-016 | Retrieve app-level config (version, API endpoints, feature flags) | `{apiUrl, appVersion, ...}` |
| `get_pending_changes_count` | TASK-016 | Check for unsaved/pending changes in sync queue | `{count: number}` |

---

## Detailed Commands

### 1. secure_store_get

**Signature:**
```typescript
invoke<string | null>("secure_store_get", { key: string }): Promise<string | null>
```

**Purpose:** Retrieve a stored value by key from Tauri secure store (TASK-016).

**Parameters:**
- `key` (string): Storage key — e.g., `"auth.access_token"`, `"auth.user"`, `"auth.clinic_id"`

**Returns:** 
- Value (string) if key exists
- `null` if key not found or never set

**FE Usage (src/lib/secureStore.ts):**
```typescript
const accessToken = await secureGet(TOKEN_KEYS.ACCESS_TOKEN);
// TOKEN_KEYS = { ACCESS_TOKEN: "auth.access_token", REFRESH_TOKEN: "auth.refresh_token", ... }
```

**Error Handling:**
- Network error (Tauri IPC failure) → throws Error
- Disk I/O failure → throws Error
- FE catches and treats as "key not found" → fallback to null or sessionStorage

---

### 2. secure_store_set

**Signature:**
```typescript
invoke<void>("secure_store_set", { key: string, value: string }): Promise<void>
```

**Purpose:** Store a secret value securely.

**Parameters:**
- `key` (string): Storage key
- `value` (string): Value to store (must be serialized to string; FE uses JSON.stringify for objects)

**Returns:** Void promise

**FE Usage:**
```typescript
await secureSet(TOKEN_KEYS.ACCESS_TOKEN, accessToken);
// Also used for user JSON:
await secureSet(TOKEN_KEYS.USER, JSON.stringify(user));
```

**Phase A Implementation Note:**
- TASK-016 currently uses plaintext JSON file (no encryption). Emits warning on first write.
- Phase B: must replace with `keyring` crate for production.
- FE has no visibility into whether plaintext or encrypted; treats as opaque storage.

---

### 3. secure_store_delete

**Signature:**
```typescript
invoke<void>("secure_store_delete", { key: string }): Promise<void>
```

**Purpose:** Remove a stored key from secure store.

**Parameters:**
- `key` (string): Key to delete

**Returns:** Void promise

**FE Usage:**
```typescript
await secureDelete(TOKEN_KEYS.USER);
// Called during logout to clean up user state
```

---

### 4. health_check

**Signature:**
```typescript
invoke<{status: "ok"}>("health_check", {}): Promise<{status: "ok"}>
```

**Purpose:** Verify Tauri runtime + Rust backend is responsive. Used for startup checks or connection verification.

**Parameters:** None

**Returns:**
```typescript
{ status: "ok" }
```

**FE Usage (planned TASK-018+):**
```typescript
const health = await invoke("health_check", {});
if (health.status === "ok") {
  // Backend is live; safe to proceed with app initialization
}
```

**Phase A Status:** Not currently called by FE. Mocked in tests. Phase B may wire at app startup to verify Tauri readiness before showing main UI.

---

### 5. get_app_config

**Signature:**
```typescript
invoke<AppConfig>("get_app_config", {}): Promise<AppConfig>
```

**AppConfig Response Shape:**
```typescript
interface AppConfig {
  apiUrl: string;              // Backend API base URL
  appVersion: string;          // Semantic version (e.g., "0.1.0")
  environment: "dev" | "staging" | "prod";
  features: {
    [featureKey: string]: boolean;  // Feature flags (e.g., sync_enabled, offline_mode)
  };
}
```

**FE Usage (planned TASK-018+):**
```typescript
const config = await invoke("get_app_config", {});
// Override Vite env vars with Tauri config
if (config.apiUrl) {
  API_BASE_URL = config.apiUrl;
}
```

**Phase A Status:** Not currently called. Vite env vars used instead. Phase B may wire if BE config needs to be dynamically changeable post-build.

---

### 6. get_pending_changes_count

**Signature:**
```typescript
invoke<{count: number}>("get_pending_changes_count", {}): Promise<{count: number}>
```

**Purpose:** Check how many changes are pending sync to BE (TASK-016 sync engine). Used to warn user before logout if unsaved changes exist.

**Parameters:** None

**Returns:**
```typescript
{ count: 0 }  // No pending changes
{ count: 5 }  // 5 pending changes waiting to sync
```

**FE Usage (planned TASK-018+):**
```typescript
const pending = await invoke("get_pending_changes_count", {});
if (pending.count > 0) {
  // Show warning: "You have {count} unsaved changes. Sync before exiting?"
}
```

**Phase A Status:** Not currently called. Network store integration exists for online/offline status, but pending-count warning deferred to TASK-018+.

---

## Capabilities & Permissions

All commands above are listed in Tauri `src-tauri/capabilities/default.json` (TASK-016 scope). FE includes are validated at compile time (capabilities checked against `invoke()` calls).

```json
{
  "permissions": [
    "core:invoke",
    "secure_store:allow-get",
    "secure_store:allow-set",
    "secure_store:allow-delete",
    "health_check:allow",
    "get_app_config:allow",
    "get_pending_changes_count:allow"
  ]
}
```

---

## Phase A Mocking

All commands are mocked via `src/tests/setup.ts` using `vitest.mock()`. During Phase A unit/component testing, actual Tauri runtime is not running.

**Mock implementation (example):**
```typescript
// Mock secure store as in-memory map
const mockSecureStore = new Map<string, string>();

vi.mocked(window.ipc).invoke = vi.fn(async (cmd, args) => {
  if (cmd === "secure_store_get") {
    return mockSecureStore.get(args.key) ?? null;
  }
  if (cmd === "secure_store_set") {
    mockSecureStore.set(args.key, args.value);
    return undefined;
  }
  // ... etc
});
```

During Phase B (Tauri runtime integration), real IPC calls will fire. Test harness will verify actual command registration + response handling.

---

## Phase B Expectations

1. **Startup sequence:** App.tsx calls `loadFromStorage()` → triggers `secure_store_get` for tokens + user JSON
2. **Token refresh:** `refreshTokenOnce()` → stores new tokens via `secure_store_set`
3. **Logout:** `authStore.logout()` → calls `secure_store_delete` for tokens + user
4. **Health verification:** (optional) App startup may call `health_check()` to verify backend before rendering main UI
5. **Config initialization:** (optional) May call `get_app_config()` to override Vite env with Tauri-provided URLs/flags
6. **Sync awareness:** (optional) Screens in TASK-018+ may call `get_pending_changes_count()` for UX warnings

---

## Known Issues & TODOs

1. **Plaintext secure store (TASK-016 issue):** Currently no encryption. Phase B must migrate to `keyring` crate. FE has no control; assume opacity.
2. **No command retry logic on IPC failure:** FE calls are synchronous await; no automatic retry. If Tauri IPC fails, exception bubbles to ErrorBoundary. Phase B may add retry hook for production robustness.
3. **No request timeout:** IPC calls have no explicit timeout. Long-running operations (e.g., large file sync) may hang. Phase B to spec timeout behavior.
4. **Config hot-reload not supported:** Once `get_app_config` is called, changes in Tauri backend require app restart to take effect.

---

## Summary Table

| Command | Impl. Status | Phase A Test | Phase B Real | TASK-017 Usage | Notes |
|---------|--------------|--------------|--------------|-----------------|-------|
| secure_store_get | ✅ TASK-016 | Mocked | Real IPC | Login restore, token read | Core to auth |
| secure_store_set | ✅ TASK-016 | Mocked | Real IPC | Login store, token update | Core to auth |
| secure_store_delete | ✅ TASK-016 | Mocked | Real IPC | Logout clean | Core to auth |
| health_check | ✅ TASK-016 | Mocked | Real IPC | Planned TASK-018 | Startup verification |
| get_app_config | ✅ TASK-016 | Mocked | Real IPC | Planned TASK-018 | Config override |
| get_pending_changes_count | ✅ TASK-016 | Mocked | Real IPC | Planned TASK-018 | Sync awareness |

---

**End of Tauri IPC Commands Reference**
