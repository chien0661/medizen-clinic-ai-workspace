# Handoff: TASK-109 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary

`get_patient` is now scoped by `clinic_id` at the query level (select/where instead
of unscoped `db.get`), mirroring `visit_service._get_visit_or_404`; the cascade to
`update_patient`/`soft_delete_patient` and their routes is correct and complete. Fix
is minimal, meets all acceptance criteria, and breaks no legitimate flow (superadmin
uses a separate aggregate path, not `get_patient`).

## Key Findings (for awareness)

- MINOR: `guardian_service.py` / `merge_service.py` still have unscoped
  `db.get(Patient, ...)` — same bug class, out of scope for M-19, recommend a
  follow-up ticket.
- Host test tooling is broken (Python 3.10 vs required 3.11 — `datetime.UTC` import
  fails). Run tests in an isolated Docker stack (as the implementer did:
  `fix109`, alembic head 0067).

## Focus Areas for Testing

1. **Cross-tenant GET → strict 404** (foreign patient, real DB): confirm no 500, no
   PII in body. This is the core M-19 fix.
2. **Own-clinic GET → 200** (no regression).
3. **Soft-deleted patient → 404**.
4. **Cross-tenant PATCH and DELETE → 404** (the cascade; foreign-clinic write/delete
   must not succeed).
5. **Own-clinic PATCH/DELETE → success** (no regression; check the TASK-096
   db.refresh interplay on soft-delete serialization).
6. **Re-confirm the 3 pre-existing failures** (`test_merge_cross_tenant_forbidden`,
   `test_rls_search_by_phone_cross_clinic_returns_zero`,
   `test_rls_merge_cross_tenant_blocked_at_service_layer`) reproduce on unmodified
   `origin/dev` — they are baseline, not caused by this fix.
