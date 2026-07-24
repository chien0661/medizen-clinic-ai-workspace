---
id: TASK-107
type: bug
title: "[High] Bất biến phiên/RBAC: vô hiệu hóa tài khoản, đổi mật khẩu, thu hồi role đều KHÔNG chấm dứt quyền"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-24
updated: 2026-07-24
completed: 2026-07-24
branch: "fix/TASK-107-auth-session-invariants"
tags: [auth, security, rbac, session, high, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (H-5, H-6, H-7)"
---

# TASK-107: [High] Cụm bất biến phiên & thực thi RBAC (H-5/H-6/H-7)

**Nguồn:** E2E TASK-095, gộp H-5/H-6/H-7 (cùng vùng auth/middleware/rbac — nên fix chung).

## H-5 — Vô hiệu hóa tài khoản (is_active=false) không thu hồi access token đang sống
- `TenancyMiddleware` chỉ verify chữ ký/expiry JWT, không kiểm `is_active`/blacklist → token cũ vẫn 200 (trả PII) tới khi hết hạn (~15').
- File: `app/core/tenancy.py`, `token_blacklist.py`, `auth_service.py`.

## H-6 — Đổi mật khẩu không thu hồi phiên trước
- `change_password` chỉ update hash; không blacklist/không bump version/không revoke refresh; refresh flow không so `iat` với `password_changed_at` → token trước-đổi dùng được tới 7 ngày.
- File: `app/modules/auth/services/auth_service.py`.

## H-7 — Thu hồi role không gỡ quyền hiệu lực
- `get_user_effective_permissions` hợp nhất `user_role` VÀ `account_clinic_role.role_codes` (pivot); `revoke_role` chỉ xóa `user_role`, không đụng pivot → thu hồi là no-op về enforcement (dù API 204, GET roles `[]`). Cả token cũ lẫn login MỚI vẫn đủ quyền.
- File: `app/modules/users/services/rbac_service.py`, `user_service.py`, `api/routes.py`.

## Hướng fix đề xuất (impl xác nhận, review chốt — có yếu tố bảo mật)
- Middleware kiểm `is_active` (và/hoặc token version/blacklist) mỗi request.
- Thêm `password_changed_at`/token-version; reject access+refresh có `iat < password_changed_at`; revoke refresh khi đổi mật khẩu / vô hiệu hóa.
- `revoke_role` phải đồng bộ cả `account_clinic_role.role_codes` (pivot) + invalidate cache; hoặc effective-perms không merge pivot đã thu hồi.

## Acceptance Criteria
- [ ] Vô hiệu hóa tài khoản → token cũ 401 ngay.
- [ ] Đổi mật khẩu → mọi access/refresh trước-đổi vô hiệu.
- [ ] Thu hồi role → mất quyền ngay (token cũ + login mới đều 403); pivot đồng bộ.
- [ ] Integration/E2E real-DB cho cả 3 (không mock).

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Blockers
Yếu tố bảo mật — cân nhắc cơ chế thu hồi (blacklist Redis vs token-version). Impl đề xuất, review/bạn chốt nếu cần.

## Testing Completed: 2026-07-24
3/3 acceptance tests PASS (H-5 401, H-6 401+401, H-7 403+fresh-login-403) on isolated stack `v107`
(api 9974/pg 5474/redis 6456), migrated to head 0067. Regression sweep: 13 pre-existing failures,
verified identical on a fresh `origin/dev` baseline stack (`v107base`) — zero new regressions.
See `docs/tasks/TASK-107/deliveries/test-reports/test-report.md`.

## Documentation Completed: 2026-07-24
Final specification document created: `docs/tasks/TASK-107/deliveries/final-specs/auth-session-invariants-fix.md` (VI)
Covers: vấn đề (H-5/H-6/H-7), cơ chế fix (version-check via tokens_valid_after + Redis fast-path),
chi tiết từng khắc phục, acceptance criteria xác thực, danh sách file thay đổi, ghi chú thiết kế (fail-open,
race condition <1s, system-role scope), ghi chú bảo mật (mật khẩu mặc định cms_app), hướng dẫn triển khai.
