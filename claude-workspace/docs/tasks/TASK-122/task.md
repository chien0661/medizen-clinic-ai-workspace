---
id: TASK-122
type: bug
title: "[Critical] JWT không verify chữ ký ở ENVIRONMENT=development → giả token chiếm quyền admin/superadmin"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-26
updated: 2026-07-26
branch: "fix/TASK-122-jwt-verify-always"
tags: [auth, security, jwt, critical, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (C-1 run3)"
    - "docs/tasks/TASK-122/handoff/implementation-to-review.md"
---

# TASK-122: [Critical] JWT dev-bypass — không verify chữ ký (C-1)

**Nguồn:** E2E re-run lần 3 TASK-095, C-1.

- **Kỳ vọng:** Mọi Bearer token verify HMAC theo `JWT_SECRET`; token sửa/giả → 401. Không có đường nào chấp nhận claims chưa verify để ra quyết định xác thực.
- **Thực tế:** Khi `ENVIRONMENT=development`, `TenancyMiddleware` gọi `_decode_jwt_payload_unsafe()` — base64-decode claims **không verify chữ ký**. Token tự chế `sub=<admin id>`, `is_superuser=true` được cấp toàn quyền (bật GUC bypass RLS). `.env.example` mặc định `ENVIRONMENT=development` → deploy quên override là mở toang.
- **Bằng chứng:** token giả chữ ký `GET /users` → 200 dữ liệu thật; cắt cụt chữ ký token doctor vẫn xác thực.
- **File:** `app/core/tenancy.py:74,95,178`

## Hướng fix (fail-safe)
Đọc code trước để hiểu vì sao có `_decode_jwt_payload_unsafe` (có thể dùng cho mục đích non-auth như log token hết hạn). Yêu cầu: **đường xác thực LUÔN verify chữ ký** ở mọi ENVIRONMENT. Nếu unsafe-decode cần cho mục đích khác thì cô lập, KHÔNG bao giờ dùng cho authz. Cân nhắc: hard-fail khi `ENVIRONMENT=development` mà không phải local (tùy chọn), nhưng cốt lõi là bỏ dev-bypass trong middleware auth.

## Acceptance Criteria
- [x] Token chữ ký sai/giả → 401 ở mọi ENVIRONMENT (kể cả development).
- [x] Token hợp lệ vẫn hoạt động; không hồi quy luồng auth.
- [x] Integration test: token giả chữ ký → 401; token thật → 200.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Blockers
Không.

## Implementation Completed (2026-07-26)
Branch `fix/TASK-122-jwt-verify-always` (base `origin/dev`@`45c5b32`, head migration 0069), pushed. `_decode_jwt_payload_unsafe()` removed entirely from `app/core/tenancy.py` — the JWT auth path now always calls the HMAC-verified decode (`_decode_jwt_payload_verified`) in every ENVIRONMENT. See `handoff/implementation-to-review.md` for full details.

## Testing Completed (2026-07-26)
In-scope tests 13/13 passed (`test_jwt_signature.py` + `test_dev_header_gating.py`); broader auth/tenancy sweep 63/72 passed (9 pre-existing failures, unrelated to this diff). See `deliveries/test-reports/test-report.md` and `handoff/test-to-documentation.md`.

## Documentation Completed (2026-07-26)
Final specification document: `docs/tasks/TASK-122/deliveries/final-specs/jwt-verify-always-fix.md`. Comprehensive coverage of vulnerability, fix, test results, and follow-up hardening task for X-Clinic-Id header.
