---
id: TASK-067
type: feature
title: FE UI routes cleanup — Security route, BHYT config route, Reports hub, Profile stubs, useSync browser UX
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-05-31
updated: 2026-05-31
branch: ""
jira_key: ""
tags: [frontend, ui, ux, routes, i18n]
affected-repos: [clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/tasks/TASK-053/deliveries/final-specs/ui-ux-audit.md  # §3 G1,G2,G5,G8,G9"
    - "docs/tasks/TASK-053/deliveries/test-reports/runtime-verification.md  # §3 useSync"
    - "docs/design/medizen-modern/TAB_MATRIX.md  # spec chuẩn"
    - "clinic-cms-web/src/router/index.tsx  # route definitions"
    - "clinic-cms-web/src/hooks/useSync.ts  # sync hook"
    - "PROJECT.md"
---

# TASK-067: FE UI routes cleanup — Security, BHYT config, Reports hub, Profile stubs, useSync UX

## Description

TASK-053 ui-ux-audit phát hiện các điểm THIẾU/LỆCH trong FE (sau khi đã implement đủ route core). Đây là bước hoàn thiện FE mà không cần thêm BE endpoint:

1. **[G1] Bảo mật & Mã hoá** — `BhytConfigPage` component tồn tại nhưng chưa expose route. Kiểm tra TASK-046 đã làm 4 security panels (MFA/Encryption/LoginHistory/Password) → có thể chỉ cần thêm route `/admin/security` hoặc `/admin/settings?tab=security`.

2. **[G2] BHYT config** — `BhytConfigPage` cần route tường minh (`/admin/bhyt` hoặc tab trong `/admin/settings`).

3. **[G5] Reports tab hub** — Spec = 1 trang "Báo cáo" với 6 tab; impl = 7 route rời. Cần chốt: (a) tạo `/reports` hub page với tab navigation link sang các sub-route, hoặc (b) cập nhật spec là OK với route rời. Không cần merge code, chỉ cần hub page + sidebar active state đúng.

4. **[G8/G9] Profile stubs + Settings root** — Profile tab "info" (form sửa thông tin cá nhân) + tab "notifications" (toggle email/SMS/in-app) còn stub. `/settings` route render `PlaceholderPage`.

5. **[UX] useSync error ẩn khi browser** — `useSync.ts` throw lỗi Tauri SQL mỗi 30s khi chạy ngoài Tauri, hiện icon ⚠️ trên Topbar. Cần: detect `isTauri()` hoặc kiểm tra plugin available trước khi init hook → ẩn lỗi ở web/browser mode.

## Requirements

- [ ] Wire route `/admin/security` (hoặc tab trong `/admin/settings`) → SecuritySettingsPage (TASK-046 panels)
- [ ] Wire route `/admin/bhyt` (hoặc conditional tab `/admin/settings?tab=bhyt`) → BhytConfigPage
- [ ] Tạo `/reports` hub page (hoặc redirect page) với tab nav linking sang các sub-route; sidebar "Báo cáo" active state đúng khi ở bất kỳ `/reports/*`
- [ ] Profile tab "info": form cơ bản (tên, email, SĐT, ảnh đại diện) với `PUT /api/v1/users/{id}` hoặc tương đương
- [ ] Profile tab "notifications": toggle email/push per event type với `/api/v1/users/{id}/notification-prefs` (nếu BE có) hoặc mark stub rõ hơn
- [ ] `/settings` root: redirect sang `/admin/settings` hoặc `/profile` thay vì `PlaceholderPage`
- [ ] `useSync.ts` + `useSync.ts:22`: bao lỗi trong `isTauri` guard → không throw/log khi chạy browser; Topbar không hiện ⚠️ sync error ở web mode

## Acceptance Criteria

- [ ] `/admin/security` route tồn tại và render Security settings (MFA/Encryption/LoginHistory/Password panels)
- [ ] `/admin/bhyt` route tồn tại và render BhytConfigPage (gated bởi `bhyt_enabled` feature flag)
- [ ] `/reports` render hub hoặc redirect đúng; sidebar highlight đúng khi ở sub-route
- [ ] Profile tab "info" có form cơ bản submit được (hoặc rõ ràng "coming soon" thay vì blank stub)
- [ ] `/settings` không render PlaceholderPage trống
- [ ] Chạy FE trong browser: Topbar KHÔNG hiện ⚠️ sync error; console KHÔNG log useSync errors
- [ ] `npm run type-check` + `npm run lint` + `npm test --silent` pass

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Router**: `clinic-cms-web/src/router/index.tsx`
- **Sync**: `clinic-cms-web/src/hooks/useSync.ts` · `src/sync/engine.ts`
- **Pages**: `admin/SettingsPage.tsx` · `admin/BhytConfigPage.tsx` · `profile/ProfilePage.tsx` · `pages/PlaceholderPage.tsx`
- **Shell**: `components/shell/Topbar.tsx` (status indicator)

## Timestamps

- **Created**: 2026-05-31
- **Review Completed**: 2026-05-31 — APPROVED (see handoff/review-report.md)
- **Testing Completed**: 2026-05-31 — PASSED 930/930 unit tests + 8/8 E2E (see deliveries/test-reports/test-report.md)

## Notes

- G5 (Reports hub): trước khi code, chốt với user về chiến lược (6-tab 1 trang vs 7-route rời). Nếu giữ 7-route, chỉ cần hub redirect + active state.
- Profile "notifications": verify BE có endpoint notification-prefs chưa (`/api/v1/notifications/prefs`?). Nếu chưa → placeholder rõ ràng ("Tính năng đang phát triển") vẫn tốt hơn blank.
- useSync guard: dùng `window.__TAURI__` hoặc `@tauri-apps/api/core:isTauri()` — không import dynamic nếu gây tree-shake issue.

## Blockers

None
