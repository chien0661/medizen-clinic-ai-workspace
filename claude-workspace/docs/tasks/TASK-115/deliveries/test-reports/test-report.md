# Test Report: TASK-115 - Exam RBAC (M-6)

**Test Agent:** Automation Tester
**Date:** 2026-07-25
**Status:** ALL IN-SCOPE PASSED

## Environment

- Isolated Docker stack `x115` (project `-p x115`), built from worktree
  `F:/MyProject/clinic-cms-workspace/_fix115-be`, branch
  `fix/TASK-115-exam-rbac` @ `bfc27ff`.
- Ports: api `9955`, postgres `5455`, redis `6437` (new
  `docker/docker-compose.fix115.yml` scaffolded for this run — infra file
  only, no source touched). No collision with main/dev/w2e.
- Migrated `alembic upgrade head` -> reached **0069** (single head confirmed
  via `alembic heads`). First attempt hit the known
  "Cannot run encryption migration while N other connections are active"
  transient (pre-existing DEK migration flake) — retry succeeded cleanly.
- Seeded superadmin (`scripts/seed_superadmin.py`) + full demo dataset
  (`scripts/seed_demo_data.py`, 13 staff accounts incl. `dr_nguyen` (doctor),
  `nurse_lan` (nurse), `recept_anh` (receptionist)).
- Stack torn down (`docker compose -p x115 -f docker-compose.fix115.yml down -v`)
  after the run; `docker ps -a --filter name=x115` confirmed empty.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Integration (`tests/integration/exam_templates` + `tests/integration/visits`) | 85 | 85 | 0 | 100% |

Command: `pytest -q --tb=short tests/integration/exam_templates tests/integration/visits`

## Key Assertions Verified

- **`test_receptionist_cannot_write_exam`**
  (`tests/integration/exam_templates/test_exam_templates_api.py:352`) — PASSED.
  Receptionist (`visit.write` only) `POST /visits/{id}/exam` -> 403; visit_exam
  read returns `None`; visit `status` remains `WAITING` in DB. Note: this
  fixture-based test's own "clinical role can write" follow-up call reuses the
  fixture's admin token (`at`), not a dedicated doctor/nurse token — flagged
  per the reviewer's instruction not to rely on admin for the 200 path.
- **Independent live-API verification with real per-role demo accounts**
  (reviewer flag addressed directly): ran a standalone script against the
  running `x115` API using `recept_anh`/`Recept@1234`,
  `dr_nguyen`/`Doctor@1234`, `nurse_lan`/`Nurse@1234` (real seeded users, not
  admin):
  - Receptionist creates a walk-in visit (`visit.write`) -> `WAITING`;
    `POST /visits/{id}/exam` -> **403** `{"code":"FORBIDDEN","message":"One of
    roles ['doctor','nurse','admin'] is required..."}`; visit re-checked via
    `GET /visits/{id}` -> still `WAITING` (no auto-start side effect from the
    blocked call).
  - Doctor (`dr_nguyen`) creates a walk-in visit -> `WAITING`;
    `POST /visits/{id}/exam` -> **200**; visit re-checked -> **`IN_PROGRESS`**
    (auto-start confirmed).
  - Nurse (`nurse_lan`) creates a walk-in visit -> `WAITING`;
    `POST /visits/{id}/exam` -> **200**; visit re-checked ->
    **`IN_PROGRESS`** (auto-start confirmed).
  - All three scenarios ran against the live app (not admin-substituted),
    directly satisfying the "real receptionist AND real doctor/nurse token"
    requirement.
- **No regression on template CRUD / versioning / RLS / SOAP migration** —
  remaining 82 tests in `exam_templates` + `visits` all green (nurse-cannot-
  manage-templates, single-default enforcement, snapshot versioning, system
  template RLS 403s, visit lifecycle/concurrency/RLS/edit-lock suites).

## Failures

None. 85/85 pytest passed; independent 3-scenario live verification (recept
403 + no-auto-start, doctor 200 + auto-start, nurse 200 + auto-start) all
matched expected behavior.

## Next Steps

All in-scope tests passed. Ready to proceed to Documentation phase.

**Task status -> DOCUMENTING**

---

**Total Scenarios:** 85 (pytest) + 3 (independent live RBAC verification)
**Environment:** isolated Docker stack `x115` (api 9955 / pg 5455 / redis 6437), torn down after run
