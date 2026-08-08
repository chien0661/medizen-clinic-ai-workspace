---
id: TASK-140
type: debt
title: "Test infra: fix integration-test fixture teardown bị RLS chặn — rò rỉ clinic/user vào DB e2e"
status: TODO
priority: Medium
assigned: Unassigned
created: 2026-08-08
updated: 2026-08-08
branch: ""
jira_key: ""
tags: [test-infra, rls, fixtures, debt]
affected-repos: [clinic-cms]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-140: Fix teardown fixture integration test bị RLS chặn (rò rỉ data vào DB e2e)

**Nguồn:** Phát hiện trong review TASK-139 (2026-08-08). Đã dọn hậu quả (1.729 clinic + ~100K patient + 2.395 user rác, tích tụ từ 2026-07-30) — task này fix gốc rễ để không tái diễn.

## Description

Fixture integration test (pattern dùng chung nhiều file test, ví dụ `px_ctx` trong `tests/integration/test_payroll_export_e2e.py` và các file cùng khuôn) **seed data bên trong `with_tenant_context`** nhưng **teardown DELETE chạy bên ngoài tenant context**. Các bảng `FORCE ROW LEVEL SECURITY` (`"user"`, `clinic`, …) lặng lẽ match 0 dòng khi DELETE không có tenant context → mỗi lần chạy test rò rỉ 1 clinic + N user vào DB. Teardown "thành công" giả (không lỗi, chỉ không xoá được gì), pytest không báo gì.

## Requirements

- [ ] Audit toàn bộ fixture integration test có seed clinic/user — xác định pattern teardown chung.
- [ ] Fix teardown: chạy DELETE trong đúng tenant context (hoặc dùng connection role bypass RLS dành riêng cho test teardown), đảm bảo xoá thật sự — assert rowcount > 0 hoặc verify count sau xoá.
- [ ] Thêm guard: fixture cuối session kiểm tra số clinic trước/sau test run — chênh lệch → fail rõ ràng (chống tái diễn âm thầm).
- [ ] Chạy lại toàn bộ integration suite trên DB sạch để xác nhận không còn rò rỉ (count clinic/user không đổi trước–sau).

## Acceptance Criteria

- [ ] Chạy full integration suite 2 lần liên tiếp → số dòng `clinic`/`"user"` trong DB e2e không tăng.
- [ ] Teardown thất bại (RLS chặn / FK) phải nổi ERROR trong pytest, không im lặng.

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-140/refs/`
- **Handoffs**: `docs/tasks/TASK-140/handoff/`
- **Test Report**: `docs/tasks/TASK-140/deliveries/test-reports/test-report.md`

## Timestamps

- **Created**: 2026-08-08

## Notes

- Chẩn đoán chi tiết + bằng chứng: `docs/tasks/TASK-139/handoff/review-report.md` (finding Major #1).
- DB e2e đã được dọn sạch 2026-08-08 (backup trước khi dọn: scratchpad `cms_backup_pre_cleanup.dump`, 16.8MB); còn DEMO + SYSTEM + 15 user thật, app verify OK sau dọn.
- Bảng append-only (`stock_movement`, `audit_log`, …) có trigger chặn DELETE — teardown/cleanup phải tính đến (xem script dọn 2026-08-08 đã phải DISABLE TRIGGER USER tạm thời).

## Blockers

None
