---
id: BUG-006
title: FE refresh loop sau login — nhiều endpoint trả 401 dù token hợp lệ trong sessionStorage
severity: Medium
status: OPEN
discovered_in: TASK-049 Phase 1 — admin login (post BUG-005 fix)
url: http://localhost:1420/#/dashboard
---

# BUG-006: FE refresh loop sau login — `apiRequest` chưa attach Authorization khi store chưa hydrate

## Symptom
Sau login admin (`admin` / `Demo@1234`), URL chuyển sang `/#/dashboard` và dashboard render OK với data, NHƯNG console liên tục báo errors:
- ~5–7 endpoints (`/api/v1/reports/*`, `/shifts`, `/attendance/me`) trả **401 Unauthorized "Missing or malformed Authorization header"**
- Sau mỗi 401, FE auto trigger POST `/api/v1/auth/refresh` (200 OK)
- Retry với `_isRetry: true` vẫn 401 → vòng lặp lặp lại liên tục → console errors > 100 trong vài giây
- `/notifications/unread-count` trả 403 Forbidden (separate — admin role missing notification permission?)

UX-impact: Dashboard vẫn render và data hiển thị OK (TanStack Query cache hit từ 1 query may mắn) nhưng background traffic noisy + tăng tải BE + có thể gây flicker.

## Verified facts (không phải BUG-005 hay JWT issue)
1. `sessionStorage` đầy đủ:
   - `auth.access_token` = JWT hợp lệ với `sub`, `active_clinic_id`, `role_codes: ["admin"]`, 50+ permissions, `type: "access"`, `exp` future
   - `auth.refresh_token`, `auth.user`, `auth.clinics`, `auth.applied_role: "admin"`
2. Direct `fetch('/api/v1/reports/inventory-status', { headers: { Authorization: 'Bearer ' + token }})` từ chính tab → **200 OK + dữ liệu thật** (Acid Folic 5mg, 6 expired items)
3. Direct `fetch` không Bearer → 401 "Missing or malformed Authorization header" — ĐÚNG message FE đang gặp
4. Code `clinic-cms-web/src/lib/apiClient.ts:84-95` có set Authorization header `if (state.accessToken)`, nhưng có vẻ tại runtime `state.accessToken` là null/empty cho 1 số request đầu

## Hypothesis (chưa verify root cause cuối)
Race condition giữa `useAuthStore.loadPersistedTokens()` (async, đọc Tauri secureStore / sessionStorage) và TanStack Query auto-fetch khi component mount. Dashboard mount nhiều `useQuery` (revenue, inventory, visit-volume, snapshots) → fire ngay khi `useAuthStore.getState().accessToken` còn null → 401 → interceptor refresh → 200 → BUT retry vẫn dùng store snapshot cũ → loop.

Or: zustand store có separate "auth state" + "token state" và một trong hai không sync. Cần debug stepwise.

## Repro
1. `cd clinic-cms-merge/docker && docker compose up -d` (BE port 8001)
2. `cd clinic-cms-web && npm run dev` (FE port 1420)
3. Mở `http://localhost:1420/`, login `admin` / `Demo@1234`
4. F12 → Network tab → quan sát hàng loạt 401 trên `/reports/*` xen kẽ với 200 trên `/auth/refresh`
5. F12 → Console → > 100 errors trong < 10s

## Files involved
- `clinic-cms-web/src/lib/apiClient.ts:74-110` (apiRequest header injection + 401 retry)
- `clinic-cms-web/src/stores/authStore.ts` (loadPersistedTokens — async hydration order)
- `clinic-cms-web/src/App.tsx` (auth bootstrap — chỗ gọi loadPersistedTokens)
- Dashboard hooks bắn queries trước khi auth hydrate

## Suggested fix (need design)
- **Option A**: Block render queries trong `RequireAuth` cho đến khi `loadPersistedTokens` resolved AND `accessToken` non-null. Hiện có thể đang render con quá sớm.
- **Option B**: Trong `apiRequest`, nếu `!state.accessToken && !skipAuth` → throw early hoặc await store hydration promise (e.g. expose `useAuthStore.getState().hydrationPromise`).
- **Option C**: TanStack Query v5: dùng `enabled: !!accessToken` cho mọi query; BoardingHook đọc state để gate.

## Impact / blocking
- **NOT BLOCKING** TASK-049 E2E test — dashboard render OK + data hiển thị đúng. Refresh loop chỉ noisy.
- Should be fixed before prod: tải BE tăng + browser DevTools rất khó đọc do 100+ errors/page-load.

## Related
- BUG-005 (vừa fix): khác bug, đã unblock luồng login. BUG-006 là regression hiện diện cả trước BUG-005.
- TASK-035 F.5/F.6 (applied_role): liên quan vì authStore hỗ trợ thêm hydration paths.
