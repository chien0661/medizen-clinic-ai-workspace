---
id: TASK-054
type: feature
title: Billing correctness — VAT, BHYT split, change-due, VietQR, void→reverse stock, POS/A4 print, manual invoice
status: TODO
priority: High
assigned: Unassigned
created: 2026-05-30
updated: 2026-05-30
branch: ""
jira_key: ""
tags: [backend, billing, gap-fix]
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

# TASK-054: Billing correctness — VAT, BHYT split, change-due, VietQR, void→reverse stock, POS/A4 print, manual invoice

## Description

Hoàn thiện độ chính xác thanh toán/hóa đơn — nhóm rủi ro tiền & tồn kho cao nhất. Hiện trạng đã verify: VAT hardcode = 0, không split BHYT trên hóa đơn, không tính tiền thừa (overpay bị reject), không sinh mã VietQR, **void KHÔNG hoàn kho** (chỉ refund mới hoàn), print 1 payload chung không phân biệt POS 58/80mm vs A4, và không có đường tạo hóa đơn lẻ (manual, không gắn visit).

> **Parent**: TASK-052 (API mapping). Task này hiện thực một cụm GAP/DRIFT đã được xác minh source (file:line) trong `api-mapping.md`. **Tuân thủ Database Error Handling Protocol** và Testing Strategy (integration real-DB Postgres+Redis) trong CLAUDE.md/PROJECT.md.

**Coordination / dependency**: Coordinate BILL-016 (void→reverse stock) với TASK-058 (pharmacy reversal). VietQR (INT-003) là tiền đề BILL-008.

## Scope — function codes

### GAP (chưa có API — build mới)

| GAP | Code | Chức năng |
|---|---|---|
| GAP | BILL-006 | Cash payment |
| GAP | BILL-008 | QR payment |
| GAP | BILL-010 | BHYT |
| GAP | BILL-012 | VAT |
| GAP | INT-003 | VietQR generator |

### DRIFT (có nhưng lệch — hoàn thiện)

| DRIFT | Code | Chức năng |
|---|---|---|
| DRIFT | BILL-003 | Manual invoice |
| DRIFT | BILL-016 | Void → reverse stock |
| DRIFT | BILL-018 | In hóa đơn POS |
| DRIFT | BILL-019 | In hóa đơn A4 |

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
- **Deliverables**: `docs/tasks/TASK-054/deliveries/`

## Timestamps

- **Created**: 2026-05-30

## Notes

Tách từ backlog GAP của TASK-052 (2026-05-30).

## Blockers

None
