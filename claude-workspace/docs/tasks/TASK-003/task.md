---
id: TASK-003
type: feature
title: Auth — JWT Login/Refresh + Password Reset + Account Lockout
status: DONE
priority: High
assigned: ""
created: 2026-04-26
updated: 2026-04-27
branch: "feature/task-003-auth"
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

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-003/refs/`
- **Code**: `clinic-cms/app/modules/auth/`
- **API Specs**: `docs/tasks/TASK-003/deliveries/api-specs/`

## Timestamps

- **Created**: 2026-04-26
- **Implementation Completed**: 2026-04-27 05:30:00

## Notes

JWT_SECRET phải rotate được. Lockout duration config per clinic (default 30 phút).

- 2026-04-27 Code Review: **APPROVED** (0 critical, 2 major, 5 minor). Both MAJOR are test gaps (end-to-end lockout + refresh-rotation blacklist), routed to Test Agent. SET LOCAL f-string verified safe (UUID-only writers). Report: `handoff/review-report.md`.

## Blockers

- TASK-001, TASK-002

---
- **Testing Started**: 2026-04-27
- **Testing Result (Iteration 1)**: FAILED — 1 critical bug found (BUG-001). Status reverted to IN_PROGRESS. See `handoff/test-to-implementation.md` and `bugs/BUG-001.md`.
- **BUG-001 Fixed**: 2026-04-26 — autonomous transaction fix in `lockout_service.py`. Coverage tests added (22 new tests, auth_service.py 53% → 100%).
- **Re-Testing Started**: 2026-04-26
- **Re-Testing Result (Iteration 2)**: **PASSED** — 215/215 tests pass, BUG-001 fixed, auth_service.py 100% coverage, lockout-rotation verified.
- **Documentation**: 2026-04-27 — Functional design (Vietnamese, 300+ lines), API spec (4 endpoints), SQL delivery (migration reference + setup guide). Branch `feature/task-003-auth` ready for merge.

**DONE 2026-04-27** — 215/215 tests pass, 100% coverage on auth_service.py + lockout_service.py. BUG-001 fixed via autonomous transaction (lockout persists across failed-login rollback). Followups: Redis-backed slowapi (production multi-worker), 2FA + password reset email (phase 2), passlib compatibility when bcrypt 5.x support lands.
