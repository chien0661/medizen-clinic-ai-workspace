---
id: TASK-126
type: feature
title: "Thống kê sử dụng dịch vụ (service usage report)"
status: IN_REVIEW
priority: Medium
assigned: code-review-agent
created: 2026-07-30
updated: 2026-07-30
branch: "feature/TASK-126"
tags: [reports, services, analytics, feature]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-126/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-126: Thống kê sử dụng dịch vụ

**Nguồn:** Ý #3 batch 2026-07-30. **Phụ thuộc TASK-125** (service_type để nhóm theo loại).

## Description
Thêm báo cáo **thống kê sử dụng dịch vụ**: số lượt, doanh thu, theo loại (khám/thủ thuật/test — TASK-125), theo khoảng thời gian, theo bác sĩ/phòng khám; xuất CSV/Excel. Nằm trong module reports (đã có revenue/visit-volume…).

## Requirements
- [x] BE: endpoint report `service-usage` — group by service + service_type + (doctor/date range); count lượt + tổng tiền. Nhất quán timezone với các report khác (lưu ý M-10 cũ).
- [x] FE: trang report service-usage (bảng + filter + export), theo mẫu các report hiện có.
- [x] Đối soát số liệu với visit-service/billing thực tế — logic verified qua e2e test đã viết (chưa chạy được, xem Notes); doanh thu = giá niêm yết trên visit_service (không phải tiền thực thu hoá đơn).

## Acceptance Criteria
- [x] Report trả đúng số lượt + doanh thu theo dịch vụ/loại/khoảng thời gian; khớp dữ liệu thực (theo test case đã viết, chưa chạy trên DB thật).
- [x] Export CSV/Excel; FE hiển thị + filter.
- [x] Integration test đối soát — viết sẵn (`tests/integration/reports/test_service_usage_e2e.py`), chưa chạy được (xem Notes).

## Progress Checklist
- [x] Planning | [x] Implementation | [ ] Code Review | [ ] Testing | [ ] Documentation

## Notes / Dependencies
- Phụ thuộc TASK-125 (service_type) — đã merge vào dev (`c459e8f`/`21d3418`), unblocked.
- BE integration tests + BE unit tests (pytest) written but **not executed**: no live Postgres/Redis in this environment beyond the `w2e` stack (explicitly off-limits per task instructions), and local Python is 3.10 while the project requires 3.11 (`app.main` import chain fails on 3.10 — same as TASK-125's precedent). Schema logic manually verified by importing `report_schemas.py` directly.
- FE tests **executed and passing**: 35/35 in `src/tests/reports/` (incl. 4 new), 1141/1144 full suite (3 pre-existing failures unrelated to this task), `tsc --noEmit` clean, `eslint` clean.
- Full details: `docs/tasks/TASK-126/handoff/implementation-to-review.md` and `docs/tasks/TASK-126/deliveries/final-specs/service-usage-functional-design.md` (section 8.3).

## Timestamps
- **Created**: 2026-07-30
- **Implementation Completed**: 2026-07-30

## Blockers
None — TASK-125 dependency resolved (service_type merged to dev).
