---
id: TASK-083
type: feature
title: Cấu hình giá thuốc + báo cáo tồn kho + xem giá trị tiền tồn kho
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-02
updated: 2026-07-03
branch: "feature/TASK-084-exam-templates"
jira_key: ""
tags: [pharmacy, inventory, pricing, reports]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-083/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-083: Cấu hình giá thuốc + báo cáo tồn kho + xem giá trị tiền tồn kho

## Description

Bổ sung khả năng **cấu hình giá cho từng loại thuốc**, cung cấp **báo cáo tồn kho**, và cho phép người dùng **nhìn thấy số tiền đang nằm trong thuốc** (giá trị tồn kho quy ra tiền). Dựa trên module medicine/inventory hiện có (TASK-011 Medicine Catalog + Prescription, TASK-012 Inventory + Batch + StockMovement + FEFO).

## Requirements

- [x] Cấu hình giá bán (và/hoặc giá nhập) cho từng loại thuốc trên UI, có phân quyền chỉnh sửa.
- [x] Báo cáo tồn kho: số lượng tồn theo thuốc/lô (batch), có lọc/tìm kiếm và xuất Excel (theo pattern export sẵn có — `app/core/excel.py`, TASK-075).
- [x] Báo cáo/khối hiển thị **giá trị tồn kho quy ra tiền** (tổng tiền đang nằm trong thuốc) — tính theo đơn giá cấu hình × số lượng tồn; làm rõ dùng giá nhập hay giá bán.
- [x] Tôn trọng multi-tenancy/RLS: giá và tồn kho theo `clinic_id`.
- [x] Migration Alembic cho mọi thay đổi schema (trường giá, v.v.), theo quy ước `NNNN_*.py`.

## Acceptance Criteria

- [x] Người dùng có quyền cấu hình được giá từng thuốc; thay đổi được lưu và phản ánh vào tính toán tồn kho.
- [x] Báo cáo tồn kho hiển thị đúng số lượng tồn theo thuốc (đối chiếu StockMovement/Batch).
- [x] Tổng giá trị tiền tồn kho tính đúng = Σ(đơn giá × số lượng tồn) và khớp khi thay đổi giá/nhập-xuất.
- [x] Xuất Excel báo cáo tồn kho hoạt động (không formula-injection — theo helper hiện có).
- [x] Test integration real-DB (Postgres + Redis) cho tính toán tồn kho + giá trị tiền; e2e cho luồng cấu hình giá.

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-083/refs/` *(DetailDesign, SRS, implementation-plan)*
- **Code**: (feature branch)
- **Tests**: `docs/tasks/TASK-083/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-083/handoff/`
- **Test Report**: `docs/tasks/TASK-083/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-083/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-083/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-07-02
- **Testing Completed**: 2026-07-03
- **Documentation Completed**: 2026-07-03

## Notes

- Module nền: TASK-011 (Medicine Catalog + Prescription), TASK-012 (Inventory + Batch + StockMovement + FEFO + Pharmacy Dispense). Xem thêm TASK-076 (dạng bào chế cấu hình động).
- Cần chốt ở `/task-plan`: giá trị tồn kho tính theo **giá nhập** (cost, phản ánh vốn) hay **giá bán** (retail) — mặc định đề xuất giá nhập cho "số tiền đang nằm trong thuốc". Có thể hiển thị cả hai.
- Cân nhắc lịch sử giá (price history) nếu cần truy vết — xác nhận scope.

## Blockers

None
