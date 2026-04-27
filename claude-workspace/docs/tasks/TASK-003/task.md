---
id: TASK-003
type: feature
title: Auth — JWT Login/Refresh + Password Reset + Account Lockout
status: TODO
priority: High
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [auth, security, sprint-2]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#4-module-auth--users"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#131-authentication"
---

# TASK-003: Auth — JWT Login/Refresh + Password Reset + Account Lockout

## Description

Auth module: login với username + password, JWT access (15 min) + refresh (7-30 days, revocable), bcrypt cost 12+, lockout sau N lần sai (config), refresh token revocation lưu Redis blacklist, password change/reset.

## Requirements

- [ ] Endpoints: `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`, `POST /api/v1/auth/change-password`
- [ ] `app/core/security.py` — `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`, `decode_token`
- [ ] JWT payload: `sub` (user_id), `clinic_id`, `roles`, `permissions`, `exp`, `jti`
- [ ] Refresh token rotation: mỗi lần refresh, invalidate token cũ + cấp mới
- [ ] Redis blacklist cho revoked `jti`
- [ ] Lockout: sau 5 lần sai trong 15 phút → `is_locked = true`, audit log
- [ ] Pydantic schemas: `LoginRequest`, `LoginResponse`, `RefreshRequest`, `ChangePasswordRequest`
- [ ] Rate limit endpoint login: 10 req/phút/IP (slowapi)

## Acceptance Criteria

- [ ] Login đúng → trả access + refresh, ghi `last_login_at`, reset `failed_login_count`
- [ ] Login sai 5 lần → account locked, return 423 Locked
- [ ] Refresh token hợp lệ → trả access mới + refresh mới, token cũ vào blacklist
- [ ] Logout → refresh token vào blacklist
- [ ] Tất cả endpoint có audit log
- [ ] Coverage > 90% cho `auth_service.py`

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-003/refs/`
- **Code**: `clinic-cms/app/modules/auth/`
- **API Specs**: `docs/tasks/TASK-003/deliveries/api-specs/`

## Timestamps

- **Created**: 2026-04-26

## Notes

JWT_SECRET phải rotate được. Lockout duration config per clinic (default 30 phút).

## Blockers

- TASK-001, TASK-002
