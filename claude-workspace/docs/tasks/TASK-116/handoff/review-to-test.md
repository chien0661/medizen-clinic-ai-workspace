# Handoff: TASK-116 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary

Print-template READ RBAC rebalanced to a per-`template_type` gate (invoice→invoice.read, prescription→prescription.print, exam_form→visit.read) plus a `settings.clinic` writer-bypass; WRITE unchanged (settings.clinic). Reviewed the diff, permission catalog, and auth flow — no critical/major issues, no privilege leak, writer-bypass is read-only, and TASK-094's prescription flow is preserved.

## Key Findings (for awareness)

- MINOR: matrix test omits a positive `exam_form` read by a `visit.read` holder and pharmacist's unfiltered-list; recommend closing in testing.
- MINOR: pre-existing F401 (unused `Clinic` import) in the test file — not introduced by this task.
- Info: GET-by-id returns 403 (not 404) for existing-but-unreadable templates (negligible, non-PHI layouts).
- Host ruff/mypy broken (exec-format error); implementer's containerized run reported 0 new. Please re-run lint/type in the isolated stack.

## Focus Areas for Testing

- Role × template_type read matrix, ideally including **receptionist** (visit.read+invoice.read, no prescription.print) and a **positive exam_form** read by a visit.read holder.
- Writer read-back for **superadmin** specifically (the original 201-then-403 reporter), not just admin.
- Confirm WRITE (POST/PATCH/duplicate/DELETE) stays 403 for all non-`settings.clinic` roles.
- Unfiltered `GET /print-templates` returns the correctly filtered subset per role (not 403, not over-broad).
- Fail-closed behavior is by construction (TemplateType is a closed Literal), but worth a sanity check if any new template_type is added.
