# TASK-115 — Implementation → Review Handoff

**Bug (M-6, TASK-095 E2E):** `POST /visits/{id}/exam` only gated on
`visit.write`, so a receptionist (has `visit.write`, no clinical role/perm)
could write/overwrite the clinical exam AND auto-promote
WAITING -> IN_PROGRESS (bypassing the `/start` role gate). Receptionist
already got 403 on `/exam-templates` and vitals — exam recording was the
inconsistent gap.

## Root cause

`alembic/versions/0044_create_exam_templates.py` explicitly documents the
original design decision: "Recording a visit exam reuses the existing
`visit.write` / `visit.read` permissions (no new permission needed for that
part)." That decision is what let receptionist through — `visit.write` is
granted to receptionist in the base RBAC seed (`0007_seed_permissions_and_roles.py`).

## Fix

`app/modules/exam_templates/api/routes.py` — `POST /visits/{visit_id}/exam`:
added `Depends(require_role(["doctor", "nurse", "admin"]))` alongside the
existing `Depends(require_permission("visit.write"))`. This is the exact
same two-dependency pattern already used by `/visits/{id}/start` and
`/visits/{id}/complete` in `app/modules/visits/api/routes.py` (lines
361-368, 382-388) — no new permission/migration needed, no new blast
radius. `GET /visits/{id}/exam` is untouched (still `visit.read` only —
receptionist can still read).

Gate chosen: **role-based** (`require_role`), matching the `/start`/`/complete`
sibling visit-lifecycle endpoints, rather than inventing a new `exam.write`
permission (which would have required a new migration + role_permission
seed rows across environments — out of scope / higher blast radius for a
Medium bug fix).

## Files changed

- `app/modules/exam_templates/api/routes.py` — added `require_role(["doctor","nurse","admin"])` dependency + import.
- `tests/integration/exam_templates/test_exam_templates_api.py` — added a `receptionist` user to the shared `etx` fixture (role `receptionist`, clinic-scoped) and a new test `TestVisitExam::test_receptionist_cannot_write_exam`:
  - receptionist POST exam -> 403
  - visit `status` stays `WAITING` in the DB (no auto-start side-effect from the blocked call)
  - `GET /visits/{id}/exam` still 200 (receptionist read unaffected) and returns `null` (nothing was recorded)
  - admin (clinical role) retry on the same visit -> 200

## Test results

Isolated Docker stack `fix115` (api 9958 / postgres 5458 / redis 6440,
migrated to head `0069` + demo seed, torn down after — `clinic_cms_w2e_*`
stack on 9999/5434/5436/6380/6382 left untouched throughout):

- Manual E2E script (login as `admin`/`recept_anh`/`dr_nguyen`/`nurse_lan`
  against seeded demo data): receptionist POST exam -> 403, visit stayed
  `WAITING`; doctor POST exam -> 200, visit auto-started to `IN_PROGRESS`;
  nurse POST exam -> 200; receptionist GET exam -> 200 (read unaffected).
  All assertions passed.
- `tests/integration/exam_templates/test_exam_templates_api.py`: **13/13
  passed** (incl. new `test_receptionist_cannot_write_exam`).
- Broader regression — `tests/integration/visits`, `tests/integration/exam_templates`,
  `tests/integration/vitals`, `tests/unit/test_exam_template_validation.py`,
  `tests/unit/visits`, `tests/unit/test_visit_complete_endpoint.py`,
  `tests/unit/test_visit_complete_audit.py`: **209/209 passed**.
- `ruff check` on the two touched files: **0 findings** (whole-repo `ruff
  check app tests` has pre-existing findings elsewhere, none in touched
  files).
- `mypy app`: **50 pre-existing errors in 27 files, 0 in
  `app/modules/exam_templates/api/routes.py`** (confirmed via grep — 0 new).

## Status

`bfc27ff` on `fix/TASK-115-exam-rbac` (base `origin/dev` @ `85f70cc`),
pushed. Worktree `F:/MyProject/clinic-cms-workspace/_fix115-be` left in
place for the reviewer.
