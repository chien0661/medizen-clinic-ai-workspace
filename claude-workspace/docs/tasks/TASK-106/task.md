---
id: TASK-106
type: bug
title: "[High] Report doctor-performance nhân bản Cartesian (over-count visits/revenue)"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-24
updated: 2026-07-24
branch: "fix/TASK-106-doctor-perf-cartesian"
tags: [reports, data-integrity, sql, high, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (H-4)"
---

# TASK-106: [High] doctor-performance nhân bản Cartesian

## Documentation (2026-07-24)
- **Status:** DONE
- **Document:** `docs/tasks/TASK-106/deliveries/final-specs/doctor-performance-cartesian-fix.md`
- **Summary:** Documented CTE-based pre-aggregation fix, Cartesian product elimination, test results (51/51), no regression.

---

**Nguồn:** E2E TASK-095, H-4.

- **Kỳ vọng:** `visits_count` = số visit distinct; revenue cộng mỗi invoice một lần.
- **Thực tế:** SQL `LEFT JOIN invoice` + `LEFT JOIN prescription` trong 1 query → `COUNT(v.id)` và `SUM(i.grand_total)` bị nhân khi visit có invoice AND ≥2 đơn (chỉ `COUNT(DISTINCT p.id)` được bảo vệ). Thí nghiệm: thêm đơn thứ 2 (không tạo visit mới) → visits_count 7→8.
- **File:** `app/modules/reports/services/doctor_performance_service.py`

## Acceptance Criteria
- [x] visits_count/revenue/avg tính đúng distinct (tách aggregate hoặc COUNT/SUM DISTINCT / subquery); khớp ground-truth `/visits?doctor_id=`.
- [x] Integration test: visit có nhiều đơn/nhiều invoice không làm over-count.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Blockers
Không.

## Implementation
See `docs/tasks/TASK-106/handoff/implementation-to-review.md`.

## Testing Notes (2026-07-24)
- Testing Completed: 2026-07-24
- Isolated stack `w106` (api 9977/pg 5477/redis 6459), migrate head + seed. `pytest -q --tb=short tests/integration/reports tests/unit/reports` → **51 passed, 0 failed**.
- H-4 confirmed fixed: `test_doctor_performance_no_cartesian_overcount` — visit with 1 invoice + 3 prescriptions no longer inflates `visits_count`/`gross_revenue`; visits_count == 2 (distinct), revenue == 150000 (not 350000). No regressions on other doctor-performance or sibling report tests.
- Test report: `docs/tasks/TASK-106/deliveries/test-reports/test-report.md`. Stack torn down (`down -v`); worktree left untouched.
