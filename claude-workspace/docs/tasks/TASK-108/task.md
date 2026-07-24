---
id: TASK-108
type: bug
title: "[Medium] Thêm dịch vụ vào visit: 500 khi visit không tồn tại (M-8) + under-billing khi invoice đã ISSUED (M-9)"
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-24
updated: 2026-07-24
branch: "fix/TASK-108-visit-service-guards"
tags: [services, visits, billing, data-integrity, crash, medium, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (M-8, M-9)"
---

# TASK-108: [Medium] Visit-service edge cases (M-8 + M-9)

**Nguồn:** E2E TASK-095, M-8 + M-9 (cùng vùng `visit_service_service`/`visit_service` → gộp).

## M-8 — `POST /visits/{unknown}/services` trả 500 thay vì 404/409
- `add_to_visit` gọi `raise_if_visit_closed()` (no-op khi visit thiếu) rồi insert VisitService; `visit_id` NOT NULL FK → IntegrityError leak 500.
- Fix: validate visit tồn tại (404) trước khi insert; visit đã đóng → 409 (đã đúng).

## M-9 — Thêm dịch vụ billable vào visit đã có invoice ISSUED → under-billing âm thầm
- `raise_if_visit_closed` CLOSED_STATUSES chỉ {COMPLETED,CANCELLED}; visit AWAITING_PAYMENT + invoice ISSUED vẫn nhận service mới → invoice giữ nguyên total, không cảnh báo.
- Fix: chặn/đánh dấu stale/cảnh báo khi visit có invoice đã phát hành (issued/paid) — quyết định cách xử lý, ghi rõ.
- **File:** `app/modules/services/services/visit_service_service.py`, `app/modules/visits/services/visit_service.py`, `billing/services/invoice_service.py`

## Acceptance Criteria
- [x] POST service vào visit không tồn tại → 404 (không 500).
- [x] Thêm service vào visit có invoice ISSUED → bị chặn hoặc invoice được đánh dấu cần refresh/cảnh báo rõ (không under-bill âm thầm).
- [x] Integration test cả 2 case + case hợp lệ không hồi quy.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Blockers
Không.

## Implementation Notes (2026-07-24)

Branch `fix/TASK-108-visit-service-guards` (base `origin/dev` @ `649bde4`), commit `54c31f1`, pushed.

- **M-8:** `add_to_visit` now calls `visit_service.get_visit(...)` (404 if the
  visit doesn't exist) before `raise_if_visit_closed` and the insert.
  `raise_if_visit_closed`'s "no-op on missing visit" contract (shared with
  prescriptions/vitals) is left untouched — the existence check was added as
  a separate step in `visit_service_service.add_to_visit` only.
- **M-9 (decision — chặn, không đánh dấu stale):** chose **block (409)**
  over a stale-flag/warning. There is no `stale`/`needs_refresh` column on
  `Invoice` (would need a migration), and the codebase already treats an
  issued invoice as immutable line-wise (`add_adjustment_line`, `delete_line`,
  `submit` all reject non-draft edits). `add_to_visit` now 409s when the
  visit has an active invoice (`status in {issued, partially_paid, paid}`,
  excluding void/refunded) and points the operator at the existing escape
  hatch: `POST /invoices/{id}/recall` (issued, unpaid → back to draft, which
  auto-resyncs lines) or void/refund. Draft invoices and the normal
  pre-invoice add are unaffected.
- Files: `app/modules/services/services/visit_service_service.py` (both
  fixes); no changes needed in `visit_service.py` (reused existing
  `get_visit`/`raise_if_visit_closed`) or `invoice_service.py` (reused
  existing `recall`).
- Tests: 2 new integration tests in
  `tests/integration/services/test_services_e2e.py`
  (`test_add_service_to_unknown_visit_returns_404`,
  `test_add_service_to_visit_with_issued_invoice_blocked` — also covers the
  recall-then-add-succeeds path and confirms the invoice total stays
  untouched while blocked); fixed 1 pre-existing mock-based unit test in
  `tests/unit/services/test_visit_service_service.py` whose fixed
  single-return-value `db.execute` mock broke once `add_to_visit` gained two
  more queries ahead of the price-override check. Also patched the shared
  `svc_ctx` teardown fixture (missing `payment`/`invoice_line`/`invoice`
  deletes before clinic teardown — exposed by the new M-9 test, which is the
  first in this file to generate a real invoice).
- Test run (isolated Docker stack `fix108`: pg 5472 / redis 6454 / api 9972,
  migrated to head 0067): targeted suite
  `tests/integration/services + tests/integration/visits +
  tests/integration/billing + tests/unit/services` → **177/177 passed**.
  Stack torn down after the run (`docker compose -p fix108 down -v`); no
  w2e/main/dev containers touched.
- Static: `ruff check` on all 3 touched files → 0 errors. `mypy` on all 3
  touched files → 0 errors (repo baseline has 56 pre-existing mypy errors
  elsewhere, none in touched files; `ruff check app tests` baseline has 452
  pre-existing errors elsewhere, unrelated).

## Testing Completed: 2026-07-24

Independently re-verified in a fresh isolated stack `v108` (api 9969 / pg
5469 / redis 6451), migrated to head `0067` + superadmin seed, worktree
`_fix108-be` @ `54c31f1`. `pytest -q --tb=short tests/integration/services
tests/integration/visits` → **89/89 passed**. Key assertions confirmed:
unknown-visit add → 404; issued/partially_paid/paid-invoice add → 409
(recall→re-add → 201, resync); pre-invoice add → 201; closed visit → 409.
No new failures. Stack torn down after run. See
`deliveries/test-reports/test-report.md`.

## Documentation Completed: 2026-07-24

Final spec document: `deliveries/final-specs/visit-service-guards-fix.md`.
Comprehensive technical overview of M-8 (404 on unknown visit) and M-9 (409 on issued invoice) fixes, including solution design, implementation details, and test coverage.
