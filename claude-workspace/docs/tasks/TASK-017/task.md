---
id: TASK-017
type: feature
title: FE — Auth + App Shell + Design System + i18n (vi/en)
status: IN_REVIEW
priority: High
assigned: Code Review Agent
created: 2026-04-26
updated: 2026-04-27
branch: "feature/TASK-017-fe-shell"
tags: [frontend, tauri, react, foundation, sprint-15]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#20-offline-sync"
  other:
    - "../../../../docs/clinic_cms_mockup.html"
---

# TASK-017: FE — Auth + App Shell + Design System + i18n (vi/en)

## Description

Lớp UI foundation cho Tauri client: routing, auth flow (login/lockout/change password/refresh), app shell (sidebar + topbar + user menu), design system (TailwindCSS + shadcn/ui), i18n vi (default) + en, permission-based menu visibility. Mọi screen module (TASK-018..024) build trên foundation này.

## Requirements

- [ ] Stack: Tauri 2.x + React 18 + Vite + TypeScript + TailwindCSS + shadcn/ui (Button, Input, Modal, Table, Toast, Form, Select, DatePicker, ...)
- [ ] State management: Zustand (auth/user/clinic context) + TanStack Query (server cache)
- [ ] Form: React Hook Form + Zod validation
- [ ] Routing: React Router v6 với nested routes + lazy loading
- [ ] Auth flow:
  - `/login` screen — username + password + remember me
  - `/change-password` (forced khi password expired hoặc lần đầu)
  - Token storage: Tauri secure store (KeychainManager / Windows DPAPI)
  - Auto refresh token khi access expired
  - Lockout countdown UI (sau 5 lần sai)
  - Logout flushes token + redirects
- [ ] App shell:
  - Sidebar nav (collapse/expand, dùng icon lucide-react)
  - Topbar: clinic name + notification bell + user menu (profile/logout)
  - Permission-based menu items (hide nếu không có permission)
  - Online/offline indicator (sẽ wired ở TASK-016)
- [ ] i18n (i18next + react-i18next):
  - Translations vi (default) + en
  - Number/date format theo locale (Intl)
  - Currency: VND default
- [ ] Theming: light + dark
- [ ] Error boundary global + toast notifications
- [ ] CI: lint (eslint), type check (tsc), test (vitest), build (tauri build)

## Acceptance Criteria

- [ ] `pnpm dev` start Tauri dev mode, hot reload working
- [ ] Login với credential đúng → redirect tới dashboard, JWT lưu secure store
- [ ] Login sai 5 lần → UI hiện lockout countdown, button disabled
- [ ] Refresh token rotate tự động (test: thay đổi access expiry = 5s, đợi 6s, click action → vẫn work)
- [ ] User Doctor không thấy menu Pharmacy/Admin (permission filter)
- [ ] Đổi ngôn ngữ vi ↔ en: toàn bộ label translate, ngày/tiền theo locale
- [ ] Build thành công cho Windows (`.msi`) và macOS (`.dmg`)
- [ ] Lighthouse-style audit: First Paint < 2s, Time to Interactive < 3s

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms-web/`
- **Reference UI**: `E:\MyProject\clinic-cms-workspace\docs\clinic_cms_mockup.html`

## Timestamps

- **Created**: 2026-04-26
- **Started**: 2026-04-27
- **Implementation Completed**: 2026-04-27

## Notes

Design system phải đủ component primitive trước khi TASK-018+ start. shadcn/ui kết hợp với theme custom (màu phòng khám). Mọi form dùng React Hook Form + Zod, không tự viết validate riêng.

## Blockers

- TASK-003 (Auth API), TASK-016 (Tauri foundation — secure store, IPC)
