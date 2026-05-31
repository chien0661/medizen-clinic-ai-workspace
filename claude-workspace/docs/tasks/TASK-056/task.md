---
id: TASK-056
type: feature
title: Reports dimensions + exports — payment-method/specialty/least-used/cost/no-show/demographic/duration/wait + CSV/PDF + data export (PDPA)
status: TODO
priority: Medium
assigned: Unassigned
created: 2026-05-30
updated: 2026-05-30
branch: ""
jira_key: ""
tags: [backend, reports, export, gap-fix]
affected-repos: [clinic-cms-merge]
parent: TASK-052
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/tasks/TASK-052/deliveries/api-specs/api-mapping.md  # nguồn GAP/DRIFT đã verify (file:line)"
    - "scripts/function_list_data.py  # function list 461 fn"
    - "PROJECT.md  # build/test, module map (target ../clinic-cms-merge)"
---

# TASK-056: Reports dimensions + exports — payment-method/specialty/least-used/cost/no-show/demographic/duration/wait + CSV/PDF + data export (PDPA)

## Description

Bổ sung các chiều group-by còn thiếu trong report (theo phương thức thanh toán, theo chuyên khoa, thuốc ít dùng, tồn kho theo giá vốn, margin, no-show rate, demographic, visit duration, wait time), thêm export CSV/PDF (hiện report chỉ trả JSON), và xây pipeline export dữ liệu (patient/visit/invoice/full-clinic + PDPA data portability).

> **Parent**: TASK-052 (API mapping). Task này hiện thực một cụm GAP/DRIFT đã được xác minh source (file:line) trong `api-mapping.md`. **Tuân thủ Database Error Handling Protocol** và Testing Strategy (integration real-DB Postgres+Redis) trong CLAUDE.md/PROJECT.md.

**Coordination / dependency**: batch.unit_cost đã có sẵn (chưa surface). Data export (DATA-004..007) + AUDIT-010 PDPA + PLT-021 dùng chung pipeline export.

## Scope — function codes

### GAP (chưa có API — build mới)

| GAP | Code | Chức năng |
|---|---|---|
| GAP | RPT-003 | Doanh thu theo phương thức |
| GAP | RPT-006 | Thuốc ít dùng |
| GAP | RPT-007 | Tồn kho theo giá vốn |
| GAP | RPT-009 | No-show rate |
| GAP | RPT-010 | Demographic BN |
| GAP | RPT-011 | Visit duration |
| GAP | RPT-012 | Wait time |
| GAP | RPT-014 | Export CSV |
| GAP | RPT-015 | Export PDF |
| GAP | SVC-008 | Service revenue report |
| GAP | MED-016 | Margin report |
| GAP | DATA-004 | Patient export |
| GAP | DATA-005 | Visit export |
| GAP | DATA-006 | Invoice export |
| GAP | DATA-007 | Full clinic export |
| GAP | AUDIT-010 | Data export (PDPA) |
| GAP | PLT-021 | Data export per clinic |

### DRIFT (có nhưng lệch — hoàn thiện)

| DRIFT | Code | Chức năng |
|---|---|---|
| DRIFT | RPT-004 | Số visit theo specialty |

## Requirements

- [ ] Đọc chi tiết từng function trong `scripts/function_list_data.py` + ghi chú verified trong `api-mapping.md`
- [ ] Thiết kế endpoint/model/migration (Alembic) cho từng GAP; hoàn thiện phần lệch cho từng DRIFT
- [ ] Viết integration test real-DB (Postgres+Redis) cho mỗi endpoint; e2e cho permission gate mới
- [ ] Cập nhật `api-mapping.md`: chuyển trạng thái GAP/DRIFT → MAPPED khi xong
- [ ] Quality gates: test pass 100%, coverage new ≥80%, `ruff check` + `mypy` pass

## Acceptance Criteria

- [ ] Tất cả function code trong Scope đạt MAPPED (có endpoint + test)
- [ ] Không phá vỡ test hiện có trên `clinic-cms-merge`
- [ ] Migration chạy `alembic upgrade head` sạch; RLS giữ nguyên cô lập tenant

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Parent mapping**: `docs/tasks/TASK-052/deliveries/api-specs/api-mapping.md`
- **Code (target)**: `../clinic-cms-merge/app/modules/`
- **Tests**: `../clinic-cms-merge/tests/{unit,integration}/`
- **Deliverables**: `docs/tasks/TASK-056/deliveries/`

## Timestamps

- **Created**: 2026-05-30

## Notes

Tách từ backlog GAP của TASK-052 (2026-05-30).

## Blockers

None
