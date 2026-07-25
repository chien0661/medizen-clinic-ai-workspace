---
id: TASK-120
type: bug
title: "[High] Guard sửa đơn thuốc: đơn pending vẫn sửa (H-1) + đổi số lượng sau HĐ issued (H-4)"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-25
updated: 2026-07-26
branch: "fix/TASK-120-prescription-guards"
tags: [prescriptions, pharmacy, billing, data-integrity, high, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (H-1, H-4)"
    - "docs/tasks/TASK-108 (guard đường service — precedent cho H-4)"
---

# TASK-120: [High] Guard mutation đơn thuốc (H-1 pending + H-4 invoice-issued)

**Nguồn:** E2E re-run TASK-095, H-1 + H-4 (cùng `prescription_service` mutation guard → gộp).

## H-1 — Đơn `pending` (đã gửi nhà thuốc) vẫn sửa tự do
- Guard trong service chỉ chặn `('dispensed','cancelled')`, bỏ sót `'pending'`. Trên đơn pending: PATCH notes→200, PATCH item quantity 10→20→200 (re-reserve tồn), POST item mới→201. Đường re-save cả-đơn thì đã 409 "đã gửi nhà thuốc" (bất đối xứng).
- **Fix:** chặn 409 mọi mutation (PATCH prescription / prescription-item / add-item) khi status `pending` (nhất quán với đường re-save).

## H-4 — Sửa số lượng thuốc sau khi HĐ issued → billing lệch âm thầm
- `PATCH /prescription-items/{id}` qty 10→50 trên visit đã có HĐ `issued` → 200, nhưng dòng HĐ vẫn qty 10 → under/over-billing. `update_item()`/`add_item()` không có guard invoice-issued (TASK-108 chỉ guard đường *service*, không đường prescription-item).
- **Fix:** chặn (409) hoặc resync khi visit có HĐ issued/paid — nhất quán với TASK-108/M-9.

- **File:** `app/modules/prescriptions/services/prescription_service.py`, `.../api/routes.py`, `billing/services/invoice_service.py`.

## Acceptance Criteria
- [x] Mutation đơn `pending` → 409 (PATCH đơn/item + add item).
- [x] Đổi số lượng prescription-item khi HĐ issued → 409 (hoặc resync HĐ); không under/over-bill âm thầm.
- [x] Cho phép sửa khi đơn còn `draft` + chưa có HĐ issued (không hồi quy).
- [x] Integration test cả 2 case.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Documentation Completed
2026-07-26 — Final spec: `deliveries/final-specs/prescription-mutation-guards-fix.md`

## Blockers
Không.

## Testing Completed (2026-07-26)
79/79 passed (isolated stack `y120`, base `origin/dev`@`c24f5fe`, migrated 0069). All in-scope guard assertions PASS: pending mutation → 409 (header/item/add/delete), qty edit after invoice issued → 409, draft still editable → 200. No billing regression. See `deliveries/test-reports/test-report.md`.

## Implementation Summary (2026-07-25)
- Branch: `fix/TASK-120-prescription-guards` (base `origin/dev` @ `c24f5fe`), pushed.
- Commit: `7b67cf4` — `fix(prescriptions): block mutation of pending prescriptions + item edit after invoice issued (TASK-120)`.
- File: `app/modules/prescriptions/services/prescription_service.py` (+72 lines, no deletions).
- Test file (new): `tests/integration/prescriptions/test_prescription_mutation_guards.py` (8 tests).
- Details in `handoff/implementation-to-review.md`.
