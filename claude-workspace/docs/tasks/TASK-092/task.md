---
id: TASK-092
type: feature
title: Nâng cấp màn hình Super Admin — tập trung quản lý hệ thống, tài khoản,
  người dùng & cấu hình hệ thống
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-16
updated: 2026-07-22
completed: 2026-07-22
branch: "feature/TASK-092-superadmin-system-config"
jira_key: ""
tags:
  - super-admin
  - ui-ux
  - system-management
  - accounts
  - users
  - system-config
affected-repos:
  - clinic-cms-web
  - clinic-cms
refs:
  detail_design: ""
  implementation_plan: docs/tasks/TASK-092/refs/implementation-plan.md
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - docs/tasks/TASK-070/deliveries/final-specs/superadmin-functional-design.md
    - docs/tasks/TASK-071/deliveries/final-specs/analytics-functional-design.md
---

# TASK-092: Nâng cấp màn hình Super Admin — tập trung quản lý hệ thống, tài khoản, người dùng & cấu hình hệ thống

## Description

Nâng cấp và tái định hướng (refocus) giao diện **Super Admin** để chỉ tập trung vào các
nghiệp vụ quản trị **cấp hệ thống**, không lẫn với nghiệp vụ vận hành phòng khám. Phạm vi
Super Admin sau khi nâng cấp gồm 4 nhóm chức năng chính:

1. **Quản lý hệ thống** — quản trị toàn bộ phòng khám (clinics/tenants), trạng thái tenant,
   thông tin toàn hệ thống.
2. **Quản lý tài khoản** — tài khoản đăng nhập cấp hệ thống (accounts), khóa/mở, gán phòng khám.
3. **Quản lý người dùng** — người dùng trong hệ thống (users), vai trò/quyền cấp nền tảng.
4. **Cấu hình hệ thống** — các cấu hình dùng chung toàn hệ thống (system configuration).

Công việc kế thừa và mở rộng từ TASK-070 (FE Super Admin — quản lý toàn hệ thống: Dashboard +
Clinics + Accounts + AuditLogs) và TASK-071 (Super Admin Analytics). Trọng tâm là **gom, làm gọn
và chuẩn hóa** trải nghiệm Super Admin quanh 4 nhóm trên; loại bỏ / ẩn các mục không thuộc phạm vi
quản trị hệ thống khỏi khu vực Super Admin.

> ⚠️ Cần **chốt phạm vi chi tiết với người dùng** ở bước `/task-plan` trước khi implement:
> chính xác những màn/mục nào giữ lại, gộp hay loại bỏ; có phát sinh endpoint BE mới không
> (users/system-config cấp nền tảng); ràng buộc `RequireSuperuser` route guard.

## Requirements

- [x] Rà soát giao diện Super Admin hiện tại (TASK-070/071) và liệt kê mục đang có
- [x] Định nghĩa lại cấu trúc điều hướng Super Admin quanh 3 nhóm điều hướng thực tế (xem Notes: "Tài khoản" và "Người dùng" gộp làm 1 màn theo quyết định planning) + 1 màn Cấu hình hệ thống
- [x] Nâng cấp/gom màn quản lý phòng khám (clinics) cấp hệ thống — server-side pagination/search (audit fix)
- [x] Nâng cấp/gom màn quản lý tài khoản (accounts) cấp hệ thống — đã là màn gộp đầy đủ từ TASK-070, giữ nguyên + sửa dropdown phòng khám
- [x] Bổ sung/nâng cấp màn quản lý người dùng (users) cấp hệ thống — quyết định planning: KHÔNG tách riêng, gộp vào màn Tài khoản
- [x] Bổ sung/nâng cấp màn cấu hình hệ thống (system configuration) — `SuperAdminSystemConfigPage` mới, 4 tab
- [x] Loại bỏ / ẩn các mục ngoài phạm vi quản trị hệ thống khỏi khu vực Super Admin (không thay đổi — vốn đã đúng phạm vi từ TASK-070)
- [x] Đảm bảo `RequireSuperuser` route guard trên toàn bộ route Super Admin (route mới `/superadmin/system-config` cũng bọc `RequireSuperuser`)
- [x] Bổ sung/điều chỉnh endpoint BE cho system-config cấp nền tảng (`GET`/`PUT /superadmin/system-config[/{section}]`, migration `0061_superadmin_system_config`)
- [ ] i18n vi/en cho toàn bộ nhãn mới — KHÔNG áp dụng: các màn Super Admin hiện có (TASK-070/071) đều dùng chuỗi tiếng Việt cứng (không qua i18next); màn mới giữ nhất quán cùng convention, xem Notes

## Acceptance Criteria

- [x] Super Admin chỉ thấy và thao tác được các nhóm chức năng: quản lý hệ thống (dashboard/clinics/analytics/audit), tài khoản & người dùng, cấu hình hệ thống
- [x] Điều hướng Super Admin gọn gàng, phân nhóm rõ ràng, không lẫn nghiệp vụ vận hành phòng khám
- [x] Người dùng không phải superuser bị chặn (403 / redirect) trên mọi route Super Admin
- [x] Các thao tác CRUD trong các nhóm hoạt động end-to-end với BE thật (không mock) — integration tests real-DB (`tests/integration/test_superadmin_system_config_e2e.py`, 13/13 pass)
- [x] Test FE + BE integration/E2E PASS; lint + type-check sạch

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-092/refs/` *(DetailDesign, SRS, implementation-plan)*
- **Code**: `clinic-cms` and `clinic-cms-web`, branch `feature/TASK-092-superadmin-system-config` in both repos
- **Tests**: `docs/tasks/TASK-092/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-092/handoff/`
- **Test Report**: `docs/tasks/TASK-092/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-092/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-092/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-07-16
- **Started**: 2026-07-20 05:15:39
- **Review Started**: 2026-07-20 05:16:10
- **Review Completed**: 2026-07-22
- **Testing Completed**: 2026-07-22

## Notes

- Kế thừa: TASK-070 (Super Admin — Dashboard + Clinics + Accounts + AuditLogs), TASK-071 (Super Admin Analytics).
- FE là trọng tâm (`clinic-cms-web`); BE (`clinic-cms`) chỉ đụng nếu thiếu endpoint users/system-config cấp nền tảng.
- Priority đặt tạm **Medium** (yêu cầu gốc không nêu) — điều chỉnh bằng cách sửa frontmatter hoặc khi `/task-plan`.
- Yêu cầu gốc (nguyên văn, có lỗi chính tả): "nâng cấp màn hình cho supper admin, supper admin chỉ tạp trung vào quản lý hệ thống, tai koản, nguuoiwf dùng, cáccaasuhifnh hệ thống".

### Implementation summary (2026-07-20)

- **BE** (`clinic-cms`, branch `feature/TASK-092-superadmin-system-config`, commit `5dd753e`): new `system_config` table
  (migration `0061_superadmin_system_config.py`, 4 sections: `feature_defaults`/`security_policy`/`email`/`system_info`),
  `GET`/`PUT /superadmin/system-config[/{section}]`, `feature_defaults` wired as tier-3 fallback in the feature-flag
  precedence chain (`app/core/features.py::_platform_default`), plus an audit-driven fix to `GET /superadmin/clinics`
  (previously returned the whole table with no pagination at all — now `search`/`skip`/`limit` + `{items,total,skip,limit}`).
  13/13 new integration tests pass; full suite re-run shows only the same ~30 pre-existing unrelated failures
  (RLS/auth/lockout/MFA infra tests — verified via `git stash` baseline diff, none touch `superadmin` or `system_config`).
- **FE** (`clinic-cms-web`, same branch, commits `9a73442`, `c6cbc21`): new `SuperAdminSystemConfigPage.tsx` (4 tabs,
  react-hook-form + zod per tab, independent save per section); Sidebar regrouped into 3 headed sections per the
  locked-in plan (Quản lý hệ thống: Tổng quan/Phòng khám/Thống kê/Audit Logs — Tài khoản & Người dùng: Tài khoản —
  Cấu hình hệ thống: Cấu hình hệ thống); `SuperAdminClinicsPage` converted to real server-side pagination/search;
  `SuperAdminAuditLogsPage` pagination now uses the API's real `total` instead of a page-size heuristic (both were
  pre-existing bugs found during the "rà soát" audit, not net-new regressions). Clinic-picker dropdowns elsewhere
  (dashboard/analytics/accounts/audit filters) request `limit: 500` so they aren't silently truncated by the BE's
  new default page size of 50.
- **Scope note**: per the locked-in implementation plan (`refs/implementation-plan.md`), "Tài khoản" and "Người dùng"
  were deliberately merged into ONE screen (`SuperAdminAccountsPage`, already existed from TASK-070) rather than
  building a separate platform-level "users" screen — this is why the requirement checklist item for "quản lý
  người dùng" is marked done via the existing combined screen, not a new one.
- **i18n**: none of the existing Super Admin screens (TASK-070/071) go through i18next — they use hardcoded
  Vietnamese strings throughout. The new System Config page follows the same convention for consistency rather
  than introducing a new i18n pattern mid-module.
- **Not yet done**: pushing branches to origin / opening PRs (blocked earlier in this session by no `gh` CLI —
  unresolved, awaiting user decision on `gh auth login` vs manual PR links, see prior handoffs in this session).

### Testing summary (2026-07-22)

- **Decision**: ALL PASS → DOCUMENTING. Full report: `deliveries/test-reports/test-report.md`.
- **BE**: migrations applied (`0061` head, isolated w2e stack), `test_superadmin_system_config_e2e.py` 13/13 pass,
  full regression 1743/1772 (29 pre-existing/unrelated RLS-auth-lockout-MFA failures — analyzed, confirmed not
  regressions), ruff/mypy 0 new findings in 092-touched files.
- **FE**: type-check clean, lint 0 new findings in 092-touched files, unit tests 1075/1078 (3 pre-existing/unrelated)
  + 6/6 scoped `SuperAdminSystemConfigPage.test.tsx`.
- **E2E (Playwright, real backend)**: all 4 mandated scenarios PASS — nav 3-group structure, System Config 4-tab
  save/reload persistence + smtp_password write-only masking, non-superuser guard (403/redirect), Clinics+Accounts
  CRUD end-to-end. Screenshots in `deliveries/test-reports/screenshots/`.
- **Environment note**: the FE dev server found running at session start was serving a stale pre-branch bundle
  (Sidebar nav rendered as the old flat 5-item list despite the source already having the 3-group structure);
  restarting `npm run dev` fixed it — not a product bug, just a stale dev-server artifact from the prior session.

## Blockers

None
