---
id: TASK-113
type: bug
title: "[Medium] 'Sắp hết' (low-stock) trong Tồn kho không hoạt động — stock-status thiếu field"
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-25
updated: 2026-07-25
branch: fix/TASK-113-low-stock-status
tags: [pharmacy, inventory, data-integrity, medium, e2e-finding]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (M-15)"
---

# TASK-113: [Medium] Low-stock "Sắp hết" không hoạt động (M-15)

**Nguồn:** E2E TASK-095, M-15.

- **Kỳ vọng:** Item avail 15/reorder_min 50 → hiện "Sắp hết"; khớp badge dashboard=1.
- **Thực tế:** List hiện "Bình thường", filter "Sắp hết" rỗng. `/inventory/stock-status` KHÔNG trả `reorder_min`/`is_low_stock` → FE không tính được, dù `/reports/inventory-status` trả low_stock_count=1.
- **File:** BE `app/modules/inventory/...` (endpoint stock-status), FE `clinic-cms-web` trang Tồn kho.

## Acceptance Criteria
- [x] `/inventory/stock-status` trả `reorder_min` + `is_low_stock` (hoặc FE dùng field tương đương) để list + filter "Sắp hết" hoạt động, khớp `/reports/inventory-status` low_stock_count.
- [x] FE hiển thị đúng trạng thái "Sắp hết" + filter.
- [x] Test: item dưới ngưỡng → is_low_stock=true, xuất hiện ở filter.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Documentation Completed
Documentation Completed: 2026-07-25 — Final specs in `docs/tasks/TASK-113/deliveries/final-specs/low-stock-status-fix.md`

## Testing — 2026-07-25 (PASSED -> DOCUMENTING)
Backend: 45/45 (`tests/integration/inventory`) in isolated stack `w113`,
migration reached single head 0069. Frontend: 66/66 vitest
(`src/tests/pharmacy`) + clean `type-check`. Low-stock set from
`/inventory/stock-status` confirmed to equal the set from
`/reports/inventory-status`. See `handoff/test-to-documentation.md` and
`deliveries/test-reports/test-report.md`.

## Blockers
Không.

## Implementation notes (2026-07-25)
See `handoff/implementation-to-review.md` for full detail. Summary: `reorder_min`
on stock-status is the *resolved* hierarchical low-stock threshold (TASK-093:
medicine -> dosage_form -> clinic settings), not the deprecated
`inventory_item.reorder_min` column — this is what keeps it consistent with
`/reports/inventory-status`.
