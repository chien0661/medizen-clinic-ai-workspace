---
id: BUG-001
title: useSync hook spam errors khi chạy FE trong browser (non-Tauri context)
severity: Medium
status: OPEN
discovered_in: TASK-049 Phase 1 — admin login
url: https://ff02-210-245-74-43.ngrok-free.app/#/dashboard
---

# BUG-001: useSync hook spam errors khi chạy FE trong browser (non-Tauri context)

## Symptom
Console log spam liên tục error:
```
[useSync] Sync error: Error: Failed to load Tauri SQL plugin. Ensure app is running in Tauri context.
    at getDb (src/sync/database.ts:96:11)
    at async getPendingRecords (src/sync/database.ts:102:14)
    at async pushChanges (src/sync/engine.ts:125:21)
    at async syncAll (src/sync/engine.ts:195:18)
    at async ... src/hooks/useSync.ts:22:22
```

Mỗi sync interval (vài giây) lại retry và lỗi lại — pollute console + waste resources.

Status bar góc trên hiển thị icon (!) cảnh báo "Sync error: Failed to load Tauri SQL plugin..." cho user thấy.

## Reproduction
1. Mở app trong browser thường (không phải Tauri desktop) — VD via ngrok URL
2. Login bất kỳ
3. Chờ vài giây → console liên tục log error này

## Root cause (suspected)
`useSync` hook không detect non-Tauri context trước khi gọi sync. Hook nên:
- Check `window.__TAURI__` (hoặc tương tự) — nếu không có → skip toàn bộ sync logic, không poll
- Hoặc làm lazy import plugin và gracefully no-op nếu fail

## Expected behavior
- Browser context: sync feature tự disable, không log error, status bar không hiện cảnh báo
- Tauri context: sync hoạt động bình thường

## Impact
- UX: status bar luôn warning → user lo lắng dù không có vấn đề
- Performance: spam network/log mỗi vài giây
- Dev: che lấp các error thực sự trong console

## Files involved
- `clinic-cms-web/src/sync/database.ts` (line 96)
- `clinic-cms-web/src/sync/engine.ts` (line 125, 195)
- `clinic-cms-web/src/hooks/useSync.ts` (line 22-37)

## Suggested fix
Thêm guard ở đầu `useSync` hoặc `database.ts`:
```ts
const isTauri = typeof window !== 'undefined' && '__TAURI__' in window;
if (!isTauri) return; // skip sync entirely in browser
```
