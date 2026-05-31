---
id: TASK-058
type: feature
title: Clinical safety & inventory integrity — allergy warning, partial/reverse dispense, adjustment approval, vital trends, service-doctor map
status: TODO
priority: High
assigned: Unassigned
created: 2026-05-30
updated: 2026-05-30
branch: ""
jira_key: ""
tags: [backend, prescriptions, pharmacy, inventory, patient-safety, gap-fix]
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

# TASK-058: Clinical safety & inventory integrity — allergy warning, partial/reverse dispense, adjustment approval, vital trends, service-doctor map

## Description

Đóng các lỗ hổng an toàn lâm sàng & toàn vẹn kho: **RX-006 cảnh báo dị ứng** (hiện KHÔNG check patient.allergies khi kê đơn — rủi ro an toàn cao), PHRM-005 cấp phát một phần (hiện all-or-nothing), PHRM-012 reverse/hoàn kho khi hủy cấp phát (hiện không có), MED-011 duyệt phiếu điều chỉnh kho (hiện apply ngay không qua duyệt), VTL-006 biểu đồ xu hướng sinh hiệu (cần endpoint tổng hợp cross-visit), SVC-004 ánh xạ service↔bác sĩ được phép thực hiện.

> **Parent**: TASK-052 (API mapping). Task này hiện thực một cụm GAP/DRIFT đã được xác minh source (file:line) trong `api-mapping.md`. **Tuân thủ Database Error Handling Protocol** và Testing Strategy (integration real-DB Postgres+Redis) trong CLAUDE.md/PROJECT.md.

**Coordination / dependency**: Coordinate với TASK-054 BILL-016 (void→reverse stock dùng chung reverse-dispense path).

## Scope — function codes

### GAP (chưa có API — build mới)

| GAP | Code | Chức năng |
|---|---|---|
| GAP | RX-006 | Cảnh báo dị ứng |
| GAP | PHRM-005 | Partial dispense |
| GAP | PHRM-012 | Reverse dispense |
| GAP | MED-011 | Adjustment approval |
| GAP | VTL-006 | Vital trends chart |

### DRIFT (có nhưng lệch — hoàn thiện)

| DRIFT | Code | Chức năng |
|---|---|---|
| DRIFT | SVC-004 | Service-doctor mapping |

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
- **Deliverables**: `docs/tasks/TASK-058/deliveries/`

## Timestamps

- **Created**: 2026-05-30

## Notes

Tách từ backlog GAP của TASK-052 (2026-05-30).

## Blockers

None
