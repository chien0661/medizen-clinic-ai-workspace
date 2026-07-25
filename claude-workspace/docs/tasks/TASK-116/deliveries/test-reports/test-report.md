# Test Report: TASK-116 - Print-template RBAC (M-11)

**Test Agent:** Automation Tester
**Date:** 2026-07-25
**Status:** ALL IN-SCOPE PASSED

## Environment

- Isolated Docker stack `x116` (project `-p x116`), built from worktree
  `F:/MyProject/clinic-cms-workspace/_fix116-be`, branch
  `fix/TASK-116-print-template-rbac` @ `5f66694`.
- Ports: api `9954`, postgres `5454`, redis `6436` (adjusted the worktree's
  scaffolded `docker/docker-compose.fix116.yml`, which had leftover values
  from an earlier local run, to these ports per the assigned stack — infra
  file only, no source touched). No collision with main/dev/w2e.
- Migrated `alembic upgrade head` -> reached **0069** (single head confirmed
  via `alembic heads`), clean run, no retry needed this time.
- Seeded superadmin + full demo dataset.
- Stack torn down (`docker compose -p x116 -f docker-compose.fix116.yml down -v`)
  after the run; `docker ps -a --filter name=x116` confirmed empty.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Integration (`tests/integration/admin`) | 23 | 23 | 0 | 100% |

Command: `pytest -q --tb=short tests/integration/admin`

## Key Assertions Verified (role x template_type matrix)

- **`test_print_template_read_gated_by_document_type`** — PASSED. Real
  `cashier` and `pharmacist` role users created via DB + real login (not
  admin-substituted):
  - cashier (`invoice.read`, no `prescription.print`) -> GET template
    `invoice` **200**; GET template `prescription` **403**; list endpoint
    filtered — `prescription` absent, `invoice` present in cashier's view.
  - pharmacist (`prescription.print` + `invoice.read`, no `visit.read`) -> GET
    `prescription` **200**, GET `invoice` **200**, GET `exam_form` **403**.
  - Write routes stay admin-only regardless of read access: cashier and
    pharmacist `PATCH /print-templates/{invoice_id}` -> **403** each
    (non-writer PATCH 403 confirmed for both roles).
- **`test_print_template_read_allowed_for_prescription_print_role`** —
  PASSED. Real `doctor` role user (DB-created + real login) -> GET/list
  `prescription` templates -> **200**; doctor `POST` (write) still blocked
  (write remains `settings.clinic`/admin-only).
- **`test_print_template_hidden_field_roundtrips`** — PASSED. Writer (admin)
  `POST` template -> **201** -> `PATCH` (adds `hidden:true`) -> **200**, PATCH
  response already reflects the field -> fresh `GET` by the same writer ->
  **200**, reads back own write correctly (writer read-back requirement).
- **No regression**: remaining 20 admin tests (settings groups, clinic
  onboarding, tenant isolation, CSV import, permission-403 baselines) all
  green.

## Failures

None. 23/23 passed. Full role x template_type matrix (cashier, pharmacist,
doctor, admin-writer) exercised with genuine per-role tokens, not admin
substitution — directly matches the assigned acceptance matrix.

## Next Steps

All in-scope tests passed. Ready to proceed to Documentation phase.

**Task status -> DOCUMENTING**

---

**Total Scenarios:** 23
**Environment:** isolated Docker stack `x116` (api 9954 / pg 5454 / redis 6436), torn down after run
