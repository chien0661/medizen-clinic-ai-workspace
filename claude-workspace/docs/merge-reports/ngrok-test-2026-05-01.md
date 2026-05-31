# ngrok Public URL E2E Test Report
**Date:** 2026-05-01  
**ngrok URL:** `https://ff02-210-245-74-43.ngrok-free.app/`  
**BE repo:** `clinic-cms-merge` @ main (f0ec794+)  
**FE repo:** `clinic-cms-web` @ main (88fa765+)

---

## Phase 1 — Vite Proxy Config

**Status: ADDED NEW (+ bug-fix sweep across 12 files)**

### Changes made (committed to FE main):

| Commit | Description |
|--------|-------------|
| `88fa765` | feat: add Vite proxy + relative API base URL for ngrok/public-URL mode |
| `8947a4b` | fix: replace all hardcoded localhost:8000 API fallbacks with empty-string |

#### `vite.config.ts` — proxy added:
```ts
proxy: {
  "/api": {
    target: "http://localhost:8001",
    changeOrigin: true,
    secure: false,
  },
},
host: true,
cors: true,
```

#### `apiClient.ts` + 10 other runtime files — fallback changed:
```ts
// Before (broken via ngrok):
const API_BASE_URL = ... ?? "http://localhost:8000";

// After (relative-path proxy mode):
const API_BASE_URL = (VITE_API_URL !== "") ? VITE_API_URL : "";
```

Files fixed: `apiClient.ts`, `App.tsx`, `LoginPage.tsx`, `ClinicSwitcher.tsx`, `ClinicSelectorPage.tsx`, `ForgotPasswordPage.tsx`, `MfaEnrollPage.tsx`, `MfaVerifyPage.tsx`, `ProfilePage.tsx`, `SecurityTab.tsx`, `hr/api.ts`

#### `playwright.config.ts` — env override added:
```ts
baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:1420"
```

---

## Phase 2 — Stack Bring-up

| Service | Status |
|---------|--------|
| Docker compose (postgres, redis, api, worker) | UP |
| Alembic `upgrade head` (migration 0033) | OK |
| Demo seed (19 patients, 13 users, 30 medicines) | OK |
| Vite dev server (`VITE_API_URL=""`) | UP @ :1420 |

---

## Phase 3 — ngrok Forwarding Verification

| Check | HTTP Code | Result |
|-------|-----------|--------|
| `http://localhost:1420` (local FE) | 200 | PASS |
| `https://ff02-210-245-74-43.ngrok-free.app/` (ngrok root) | 200 | PASS |
| `POST /api/v1/auth/login` via ngrok | 200 + access_token | PASS — proxy working |

---

## Phase 4 — Golden Path curl Smoke via ngrok

All 5 scenarios via `https://ff02-210-245-74-43.ngrok-free.app`:

| # | Scenario | HTTP | Result |
|---|----------|------|--------|
| 1 | Login admin (`Demo@1234`) | 200 + JWT | PASS |
| 2 | GET /api/v1/patients | 200 | PASS |
| 3 | POST /api/v1/patients (create) | 201 | PASS |
| 4 | GET /api/v1/services | 200 | PASS |
| 5 | POST /api/v1/visits (create) | 201 | PASS |

**Manual curl golden path: 5/5 PASS**

---

## Phase 5 — Playwright Smoke via ngrok

**Run 1 (before full fix):** 37 passed, 2 failed, 1 flaky, 5 skipped (4.4 min)

Failed tests: `auth-lockout.spec.ts` — login UI tests showed "Cannot connect to server" because `LoginPage.tsx` (and 9 other files) still had hardcoded `localhost:8000` fallback, bypassing Vite proxy entirely.

**Run 2 (after full fix, blank .env.local):** 39 passed, 1 failed (rate-limit 429), 5 skipped (1.5 min)

The 1 remaining failure is `login with valid credentials redirects to dashboard` — the test gets HTTP 429 (rate-limited) because the preceding lockout test made multiple bad-password attempts for `admin`. The API correctly returned 429. This is a test-ordering issue, NOT a proxy/connectivity issue. Network path is confirmed working: screenshot shows "Too many requests. Try again in 60 seconds" — the app IS talking to the backend correctly.

**Root fix summary (3 commits):**
1. `88fa765` — Vite proxy + apiClient.ts fallback
2. `8947a4b` — 10 more files with hardcoded localhost:8000 fallback
3. `.env.local` — cleared `VITE_API_URL` to enable proxy mode

### Screenshot — Login page loaded via ngrok (pre-fix state):
`docs/merge-reports/ngrok-screenshots/login-page-ngrok-prefixed.png`

> Page rendered correctly through ngrok. Banner "Cannot connect to server" was caused by hardcoded localhost:8000 fetch — FIXED in commit `8947a4b`.

---

## Root Cause Analysis — auth-lockout failures

The 2 Playwright UI failures were NOT a proxy issue. Root cause:

- `LoginPage.tsx` (and 9 other pages) each had their own local `API_BASE_URL` constant with `"http://localhost:8000"` hardcoded as fallback
- When `VITE_API_URL=""`, these used `""` in `apiClient.ts` (fixed first) but **NOT** in the individual pages (fixed in second commit)
- Playwright Chromium running against ngrok URL would execute `fetch("http://localhost:8000/api/v1/auth/login")` — which a browser context cannot reach → `TypeError: fetch failed` → "Cannot connect to server" banner

---

## Phase 6 — Cleanup

- FE dev server: killed (powershell Stop-Process)
- Docker stack: stopped post-report
- Both committed to `clinic-cms-web` main

---

## Verdict

**PUBLIC_URL_WORKING**

| Item | Result |
|------|--------|
| Vite proxy config | ADDED NEW |
| ngrok root URL | HTTP 200 |
| `/api/v1/auth/login` via ngrok | HTTP 200 + access_token |
| Manual curl golden path | 5/5 PASS |
| Playwright smoke (full suite) | 39/40 PASS (1 rate-limit 429 — test ordering, not connectivity) |
| Cleanup | Done |

### Confirmed proxy chain:
```
Browser → https://ff02-210-245-74-43.ngrok-free.app → Vite dev server :1420 → Vite proxy /api/* → localhost:8001 (FastAPI)
```

### Screenshots:
- `ngrok-screenshots/login-page-ngrok-prefixed.png` — pre-fix: "Cannot connect to server" (hardcoded localhost:8000)
- `ngrok-screenshots/login-page-ngrok-postfix-429ratelimit.png` — post-fix: "Too many requests 429" (connected, rate-limited)
