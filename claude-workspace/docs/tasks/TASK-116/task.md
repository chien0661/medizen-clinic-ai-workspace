---
id: TASK-116
type: bug
title: "[Medium] Bất đối xứng RBAC print-template: READ gate prescription.print, WRITE gate settings.clinic"
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-25
updated: 2026-07-25
branch: "fix/TASK-116-print-template-rbac"
tags: [admin, print-templates, rbac, medium, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (M-11)"
    - "docs/tasks/TASK-094 (BUG-094-001 — read gate đã đổi sang prescription.print)"
---

# TASK-116: [Medium] Print-template RBAC bất đối xứng (M-11)

**Nguồn:** E2E TASK-095, M-11. Liên quan TASK-094/BUG-094-001 (read gate đổi sang `prescription.print`).

- **Kỳ vọng:** Role in tài liệu đọc được template tương ứng; role có quyền write đọc lại được cái vừa viết.
- **Thực tế:** GET yêu cầu `prescription.print` → recept/cashier→403 (không lấy được layout **invoice** để in hóa đơn); superadmin→403. WRITE yêu cầu `settings.clinic` → superadmin POST 201 nhưng GET chính id đó→403.
- **File:** `app/modules/admin/api/routes.py`, `services/print_template_service.py`

## Hướng fix (đề xuất — impl chốt + ghi rõ)
Cân bằng lại: READ template nên mở cho role in loại tài liệu tương ứng (vd cashier/recept đọc được template **invoice**; doctor/nurse đọc **prescription**) hoặc gate READ theo một quyền rộng hợp lý; role có WRITE (settings.clinic, gồm superadmin) PHẢI đọc lại được. Giữ WRITE = admin. Nhất quán với quyết định TASK-094 (read = prescription.print cho luồng bác sĩ) — mở rộng cho invoice/cashier.

## Acceptance Criteria
- [x] Role in hóa đơn (cashier/recept) đọc được template invoice; role in đơn (doctor/nurse) đọc được prescription.
- [x] Role có quyền WRITE (gồm superadmin) đọc lại được template vừa tạo (GET không 403).
- [x] Integration test ma trận role × template_type cho READ + WRITE.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

Documentation Completed: 2026-07-25
- Final spec: `docs/tasks/TASK-116/deliveries/final-specs/print-template-rbac-fix.md`

## Testing Completed (2026-07-25)
23/23 passed (`tests/integration/admin`) on isolated stack `x116` (api 9954 /
pg 5454 / redis 6436), migrated to head 0069, torn down after run. Role ×
template_type matrix confirmed with real per-role users (doctor, cashier,
pharmacist created via DB + real login, not admin-substituted): cashier ->
invoice 200 / prescription 403; pharmacist -> prescription+invoice 200 /
exam_form 403; doctor -> prescription 200; admin (writer) POST -> PATCH ->
GET all 200 (reads back own write); cashier/pharmacist PATCH -> 403. See
`docs/tasks/TASK-116/deliveries/test-reports/test-report.md`.

## Review Completed (2026-07-25)
APPROVED by Code Review Agent → IN_TESTING. Per-type READ gate + writer-bypass
verified: no privilege leak, writer-bypass read-only (write still settings.clinic),
auth preserved (401 before per-type 403), TASK-094 prescription flow intact,
exam_form→visit.read judged acceptable (non-PHI layout, real permission split).
See `handoff/review-report.md`.

## Implementation summary (2026-07-25)
RBAC scheme chosen (per-document-type READ + writer bypass) — see
`docs/tasks/TASK-116/handoff/implementation-to-review.md` for full detail and
the RBAC-design note flagged for the reviewer.

- Branch `fix/TASK-116-print-template-rbac` (base `origin/dev` @ `85f70cc`),
  worktree `F:/MyProject/clinic-cms-workspace/_fix116-be`, pushed.
- Commit `5f66694` — `fix(admin): rebalance print-template read/write RBAC so
  printing roles can read + writers can read back (TASK-116)`.
- Tests: 3/3 new + targeted (`tests/integration/admin/test_admin_e2e.py -k
  print_template`), 23/23 full `tests/integration/admin/` — isolated stack
  `fix116` (api 9957 / pg 5457 / redis 6439, migrated to head 0069, torn down).
- `ruff check` / `mypy` on touched files: 0 new (1 pre-existing F401 in the
  test file, confirmed identical on `origin/dev`).

## Blockers
Không (nếu phát sinh quyết định RBAC lớn, impl flag để review/user chốt).
