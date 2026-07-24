---
id: TASK-110
type: bug
title: "[Medium] Đánh số hóa đơn không serialize → phát hành đồng thời trùng số + 500"
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-24
updated: 2026-07-24
branch: "fix/TASK-110-invoice-number-serialize"
tags: [billing, invoice, concurrency, data-integrity, medium, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (M-20)"
---

# TASK-110: [Medium] Race đánh số hóa đơn (M-20)

**Nguồn:** E2E TASK-095, M-20.

- **Kỳ vọng:** 2 invoice phát hành đồng thời → số khác nhau, cả hai 200 (như đánh số visit dùng counter ON CONFLICT).
- **Thực tế:** `fn_next_invoice_number` dùng `SELECT MAX(seq)+1` không lock → race → cả hai tính `INV-...-008`; một 200, một **500** (đụng unique index). Invoice thua rollback về draft (số rỗng). Đa cashier là thường lệ.
- **File:** `app/modules/billing/services/invoice_service.py`, `alembic/versions/0053_invoice_number_max_seq.py`, `0019_create_invoices.py`; tham chiếu pattern counter ở `0010_create_visits.py`.

## Acceptance Criteria
- [x] Đánh số hóa đơn serialize an toàn dưới đồng thời (counter table + ON CONFLICT / SELECT FOR UPDATE / sequence) — 2 phát hành đồng thời → 2 số khác nhau, cả hai thành công.
- [x] Migration nếu cần (counter table), single head, additive.
- [x] Integration test đồng thời (2 phát hành song song không trùng, không 500).

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Blockers
Không.

## Implementation Summary (2026-07-24)
- Branch `fix/TASK-110-invoice-number-serialize`, base `origin/dev` (649bde4, alembic head 0067 → 0068).
- Mechanism: new `invoice_number_counter` table (clinic_id, invoice_date, last_seq), `fn_next_invoice_number` rewritten to `INSERT ... ON CONFLICT DO UPDATE SET last_seq = last_seq + 1 RETURNING last_seq` — mirrors `fn_next_visit_number` (0010). Row lock held for the caller's transaction (one txn/request, see `app/core/db.py::get_db`) serializes concurrent submits.
- Migration `0068_invoice_number_counter.py` — additive, single head (`alembic heads` → `0068 (head)`), seeds counter from max existing seq per clinic+date for backward compatibility, downgrade restores the pre-0068 MAX-scan function verbatim.
- Files: `alembic/versions/0068_invoice_number_counter.py` (new), `tests/integration/billing/test_billing_e2e.py` (+3 tests: 2-way concurrent submit, 5-way concurrent submit, sequential-monotonic sanity).
- Commit `699c7aa`, pushed `-u origin fix/TASK-110-invoice-number-serialize`.
- Tests: isolated Docker stack `fix110` (api 9970/pg 5470/redis 6452, no shared volumes), migrated to head, ran full suite — `tests/integration/billing/` (25/25 incl. new concurrency tests) + `tests/integration/visits/` + `tests/unit/` → 1080 passed, 5 pre-existing failures unrelated to this change (email templates, erasure last_accessed_at, feature_flags, 2x test_rls_helpers stale call-count assertions — none touch billing/invoice code, confirmed present on unmodified dev baseline). Stack torn down after.
- `ruff check app tests`: 452 pre-existing baseline errors, 0 new (new migration file clean after `--fix` on import order; test file's 4 pre-existing errors unchanged, unrelated to added code). `mypy app`: 50 pre-existing baseline errors in untouched files, 0 new (invoice_service.py not modified).
- Single alembic head confirmed: `0068 (head)`.
- Handoff: `docs/tasks/TASK-110/handoff/implementation-to-review.md`.

## Testing Completed: 2026-07-24

Independently re-verified in a fresh isolated stack `v110` (api 9967 / pg
5467 / redis 6449), migrated to head **0068** (single head confirmed) +
superadmin seed, worktree `_fix110-be` @ `699c7aa`. `pytest -q --tb=short
tests/integration/billing` → **40/40 passed**. Key assertions confirmed:
2-way and 5-way concurrent invoice submit → all distinct numbers, all 200,
no 500; sequential submits monotonic. Also verified `alembic downgrade -1`
→ `alembic upgrade head` cycles cleanly back to single head `0068`. No new
failures. Stack torn down after run. See
`deliveries/test-reports/test-report.md`.

## Documentation Completed: 2026-07-24

Final spec document: `deliveries/final-specs/invoice-numbering-serialization-fix.md`.
Technical overview of M-20 (invoice numbering race condition) fix using ON CONFLICT pattern, migration details (0068), and concurrency test results.
