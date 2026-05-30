---
id: TASK-064
type: feature
title: BE inventory completeness — stocktake submit + batches/dispose endpoints + gỡ mock-success FE
status: IN_REVIEW
priority: High
assigned: Code Implementation Agent
created: 2026-05-31
updated: 2026-05-31
branch: ""
jira_key: ""
tags: [backend, frontend, inventory, pharmacy, bugfix]
affected-repos: [clinic-cms-merge, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/tasks/TASK-053/deliveries/final-specs/functional-audit.md  # §3.3, §3.4 — GAP source"
    - "docs/tasks/TASK-053/deliveries/test-reports/runtime-verification.md  # §1 mock-fallback"
    - "clinic-cms-web/src/pages/pharmacy/StocktakePage.tsx:134,140  # FE call + mock-success"
    - "clinic-cms-web/src/pages/pharmacy/ExpiryProcessingPage.tsx:192,234  # FE call + mock-success"
    - "clinic-cms-merge/app/modules/inventory/  # BE module nguồn"
    - "PROJECT.md"
---

# TASK-064: BE inventory completeness — stocktake submit + batches/dispose + gỡ mock FE

## Description

TASK-053 phát hiện 2 gap BE + 2 mock-success FE trong module inventory/pharmacy:

1. **`GET/POST /api/v1/inventory/stocktake`** — BE chưa có endpoint. FE `StocktakePage.tsx` đã implement UI wizard 3 bước (Chuẩn bị → Đếm → Đối chiếu); bước Chuẩn bị đọc `/inventory/items` (OK), nhưng **Submit giả success** khi `/inventory/stocktake` 404 (comment: "Mock success if BE not available").

2. **`POST /api/v1/inventory/batches/dispose`** — BE chưa có endpoint. FE `ExpiryProcessingPage.tsx` đọc `/inventory/batches` (OK) nhưng **dispose giả success** khi endpoint không có (comment: "Mock success — BE not yet live").

Nhiệm vụ: (a) implement 2 endpoint BE, (b) gỡ mock-success FE để lỗi thật nổi lên khi BE không có.

## Requirements

### BE (`clinic-cms-merge`)
- [ ] `GET /api/v1/inventory/stocktake` — lấy snapshot kiểm kê hiện tại (items + expected quantity)
- [ ] `POST /api/v1/inventory/stocktake` — submit kết quả kiểm kê (actual qty per item → tạo adjustment records)
- [ ] `POST /api/v1/inventory/batches/dispose` — đánh dấu lô hàng hết hạn là "đã huỷ/tiêu huỷ", trừ stock
- [ ] Cả 3 endpoint phải có: permission gate (`inventory.adjust`), RLS theo `clinic_id`, audit trail (`__auditable__ = True`), integration test real-DB
- [ ] Migration nếu cần thêm table/column (ví dụ: `stocktake_sessions`, `stocktake_items`)

### FE (`clinic-cms-web`)
- [ ] `StocktakePage.tsx:140` — bỏ `// Mock success if BE not available`, để `catch` hiện lỗi thật (toast error)
- [ ] `ExpiryProcessingPage.tsx:236` — bỏ `// Mock success — BE not yet live`, để `catch` hiện lỗi thật
- [ ] Verify UI vẫn hoạt động đúng sau khi gỡ mock (kết nối với BE real endpoint)

## Acceptance Criteria

- [ ] `POST /inventory/stocktake` nhận submit kiểm kê → tạo adjustment → pass integration test
- [ ] `POST /inventory/batches/dispose` huỷ lô → trừ stock → pass integration test
- [ ] FE StocktakePage: bấm submit gọi BE thật; nếu lỗi → toast error rõ (không giả thành công)
- [ ] FE ExpiryProcessingPage: bấm dispose gọi BE thật; nếu lỗi → toast error rõ
- [ ] Permission gate `inventory.adjust` chặn đúng unauthorized user
- [ ] `ruff check` + `mypy` + `pytest -q` pass

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **FE**: `clinic-cms-web/src/pages/pharmacy/StocktakePage.tsx` · `ExpiryProcessingPage.tsx`
- **BE**: `clinic-cms-merge/app/modules/inventory/` (routes, services, models, schemas)
- **Tests**: `clinic-cms-merge/tests/integration/`

## Timestamps

- **Created**: 2026-05-31
- **Review Completed (CHANGES_REQUESTED)**: 2026-05-31 — returned to IN_PROGRESS

## Notes

- Source gap: TASK-053 runtime audit. Trùng nhóm TASK-041 (branch consolidation) — verify xem BE inventory module trên nhánh `feature/task-010..015` đã có stub không trước khi build mới.
- Scope guard: chỉ 2 endpoint này + gỡ mock FE. KHÔNG refactor toàn bộ inventory.

## Blockers

None
