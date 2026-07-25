# Review Report — TASK-116

**Reviewer**: Code Review Agent
**Date**: 2026-07-25
**Branch**: `fix/TASK-116-print-template-rbac` (base `origin/dev` @ `85f70cc`), worktree `F:/MyProject/clinic-cms-workspace/_fix116-be`
**Decision**: **APPROVED** → IN_TESTING

## Scope

Print-template READ/WRITE RBAC rebalance (M-11, from TASK-095 E2E). READ moved from a single blanket `prescription.print` gate to a per-`template_type` gate plus a `settings.clinic` writer-bypass; WRITE unchanged. Security-relevant (RBAC). Read-only review — no code changed.

Diff: `app/modules/admin/api/routes.py`, `app/modules/admin/services/print_template_service.py`, `tests/integration/admin/test_admin_e2e.py`.

## Verification performed

- Confirmed `READ_PERMISSION_BY_TYPE` = `{invoice→invoice.read, prescription→prescription.print, exam_form→visit.read}` and that `TemplateType = Literal["invoice","prescription","exam_form"]` — map is total over the enum, so no template_type falls through; an unknown type fails **closed** (`required is None` → `ForbiddenError`).
- Confirmed WRITE routes (POST/PATCH create, update, duplicate, delete — routes.py:423/442/464/484) still carry `dependencies=[Depends(require_permission("settings.clinic"))]`. The writer-bypass lives only in `assert_can_read`, which is called only from the two GET routes → **cannot grant write**.
- Confirmed authentication is preserved after the GET routes dropped their permission dependency: `_get_user_id()` (routes.py:74) raises **401** from `current_user_id` ContextVar before `assert_can_read` runs. Flow is 401-if-unauth → 403-if-unpermitted.
- Verified `rbac_service.get_user_effective_permissions(db, user_id, clinic_id) -> set[str]` signature matches call sites; `readable_types(set[str])` used correctly for the unfiltered-list filter.
- **Permission catalog cross-check** (0007, 0018a, 0019a, 0034, 0036 migrations):
  - `invoice.read`: admin, doctor, nurse, receptionist, pharmacist, cashier — held by **all** system roles (billing visibility granted broadly by design in 0019a). Broad but still a real check (a custom role lacking it → 403).
  - `prescription.print`: admin, doctor, nurse, pharmacist — **not** receptionist/cashier.
  - `visit.read`: admin, doctor, nurse, receptionist, cashier — **not** pharmacist.
  - `settings.clinic`: admin (all perms) + super_admin (0036) only → writer-bypass = admin+superadmin, which is exactly the "write 201 then read 403" case being fixed.
- Syntax spot-check (`ast.parse`) on all 3 files: OK.

## Findings

### CRITICAL
None.

### MAJOR
None.

### MINOR
1. **Test matrix coverage gaps (non-blocking)**: the matrix asserts the negative `exam_form` path (pharmacist 403) but not a positive `exam_form` read by a `visit.read` holder, and only cashier's unfiltered list is asserted (not pharmacist's). The writer reads back all three, so the exam_form layout is exercised indirectly. Suggest Test Agent close these in the testing phase.
2. **Pre-existing `F401`** (unused `Clinic` import) in `test_admin_e2e.py` — confirmed by implementer as identical on `origin/dev`; not introduced here.
3. **(Info) Existence disclosure**: GET-by-id returns 403 (not 404) for an existing-but-unreadable template, letting a caller distinguish "exists" from "not found" for a layout id. Negligible — templates are non-PHI layout definitions.

## Focus-area verdicts (per review brief)

- **No leak**: invoice templates → all staff roles (by design; hypothetical reduced role still 403). prescription templates → only prescription.print holders (doctor/nurse/pharmacist); receptionist/cashier correctly denied. exam_form → visit.read holders; pharmacist correctly denied. No role gains access it shouldn't.
- **`exam_form` → `visit.read` breadth**: **acceptable.** `visit.read` is held by doctor/nurse/receptionist/cashier (matches `PrintExamFormModal.tsx` callers) and denies pharmacist, so it remains a real split rather than an open gate. The resource is a blank exam-form *layout*, not patient data, so the broader holder set carries no PHI-disclosure risk. No dedicated `exam_form.print` permission exists; introducing one is a reasonable future improvement but not required.
- **Writer-bypass correct**: yes — read-only, admin+superadmin, fixes the 201-then-403 asymmetry; write remains independently gated.
- **TASK-094 / BUG-094-001 consistency**: preserved — prescription templates still gated on `prescription.print`, so the doctor read flow is unchanged.

## Quality gates

- [x] No critical/major issues.
- [x] New tests exist and cover read-per-type + writer-readback + write-still-403 + unfiltered-list filtering.
- [x] Auth/authorization correct; no leak; fail-closed on unknown type.
- [x] CLAUDE.md standards (no secrets, no sensitive logging, focused helpers).
- [~] ruff/mypy: **host tooling broken** (`ruff` → "Exec format error", WSL/Windows binary mismatch; `mypy` not runnable on host). Relied on implementer's containerized run (`fix116` stack, 0 new ruff/mypy, 1 pre-existing F401) + my `ast` syntax spot-check. Tests run in isolated Docker (23/23 admin, 3/3 print_template) per handoff.
