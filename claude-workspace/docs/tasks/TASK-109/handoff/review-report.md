# Review Report: TASK-109 — get_patient clinic_id scoping (M-19)

**Reviewer**: Code Review Agent
**Date**: 2026-07-24
**Branch**: `fix/TASK-109-patient-get-tenant-filter` (base `origin/dev` @ 649bde4)
**Worktree**: `F:/MyProject/clinic-cms-workspace/_fix109-be`
**Decision**: **APPROVED** → IN_TESTING

---

## Scope Reviewed

Diff `git diff origin/dev...HEAD --unified=3`: 2 source files, 3 test files.

- `app/modules/patients/services/patient_service.py` — `get_patient` now scoped
  by `clinic_id`; `update_patient` / `soft_delete_patient` gained required
  `clinic_id` param.
- `app/modules/patients/api/routes.py` — `GET/PATCH/DELETE /patients/{id}`
  resolve `clinic_id = _require_clinic_id()` and pass it through.
- Tests updated (unit + 2 integration suites), cross-tenant assertion tightened
  to strict `== 404`.

---

## Findings by Severity

### CRITICAL
None.

### MAJOR
None.

### MINOR
1. **Sibling unscoped `db.get(Patient, ...)` remain out of scope**
   (`guardian_service.py`, `merge_service.py`) — same class of IDOR bug, correctly
   left untouched per M-19 scope. `merge_service` already has its own service-layer
   cross-tenant 403 check. **Recommend a follow-up ticket** (already flagged by
   implementer). Not blocking.
2. **3 pre-existing integration failures** (`test_merge_cross_tenant_forbidden`,
   `test_rls_search_by_phone_cross_clinic_returns_zero`,
   `test_rls_merge_cross_tenant_blocked_at_service_layer`) — implementer verified
   identical on unmodified `origin/dev` baseline. Unrelated to this fix. Test Agent
   should re-confirm baseline.

---

## Correctness Review

- **Fix is correct and minimal.** `get_patient` replaces unscoped `db.get(Patient,
  patient_id)` with `select(Patient).where(id == patient_id, clinic_id == clinic_id,
  is_deleted.is_(False))` + `scalar_one_or_none()`. A foreign-clinic row is excluded
  by the WHERE clause and **never loaded** — no `EncryptedString` decrypt attempt, no
  `InvalidTag`, no 500 oracle, no latent PII exposure. Foreign → 404, own → 200,
  soft-deleted → 404. Meets all 3 acceptance criteria.
- **Mirrors the established pattern** exactly: `visit_service._get_visit_or_404`
  (visit_service.py:62) uses the identical select/where/scalar_one_or_none shape.
  Consistent with the codebase.
- **`clinic_id` source is correct**: `_require_clinic_id()` reads the request-scoped
  `current_clinic_id` contextvar (set by auth/tenancy middleware from the caller's
  JWT), 400 if absent. Same source every other patients route already uses. Not
  attacker-controllable.
- **Cascade is in scope and correct.** `update_patient` / `soft_delete_patient` call
  `get_patient` internally to fetch-before-mutate and had the identical (worse:
  write/delete) flaw. Changing `get_patient`'s signature required touching them
  anyway. Both routes now pass `_require_clinic_id()`. Approved as in-scope.
- **No build break.** All callers of the three changed functions are in patients
  `routes.py` (verified repo-wide); all updated. The only cross-module import from
  `patient_service` is `_normalize_vi` (search_service) — unrelated helper. No other
  module imports the changed functions.
- **db.refresh interplay (TASK-096)**: `soft_delete_patient` change is limited to
  adding the `clinic_id` fetch scope; the existing `db.refresh` behavior is
  untouched. Guard test `test_soft_delete_patient_service_can_be_serialized_after_delete`
  updated for the new signature, no behavioral regression.

## Superuser / Legitimate Cross-Clinic Verdict

**No legitimate flow broken.** There is no cross-clinic single-patient read path
through `get_patient`. The superadmin module (`superadmin/analytics.py`,
`superadmin/api/routes.py`) reads patient data only via aggregate raw-SQL analytics
queries (COUNT/JOIN with optional `clinic_id` filter) — it never fetches an
individual decrypted patient record via `get_patient`. Scoping `get_patient` to the
caller's clinic is therefore safe and does not affect superadmin. No superadmin
bypass parameter is needed.

## Tests

- New assertion strictness is genuine: both cross-tenant HTTP tests changed from
  `in (200, 404)` to strict `== 404`
  (`test_tenant_isolation_via_http`,
  `test_rls_via_http_get_patient_cross_tenant_returns_404`), and the misleading
  "documents current behavior / may return 200" comments were removed. This is a real
  regression guard, not coverage padding.
- New unit test `test_raises_not_found_when_foreign_clinic` asserts the foreign-clinic
  → NotFoundError path. Mock shape (`db.execute` AsyncMock → MagicMock with sync
  `scalar_one_or_none`) matches the real call pattern.
- Own-clinic 200 preserved (`test_returns_patient_when_found`, update/delete happy
  paths).

## Checks Run

- **Manual diff review** — full `--unified=3` diff read; logic verified against
  `visit_service` pattern and `_require_clinic_id` helper.
- **Caller analysis** — repo-wide grep confirms all callers updated, no build break.
- **Superuser path analysis** — confirmed superadmin uses separate aggregate path.
- **`/auto-build test` / lint NOT run on host** — host Python is 3.10; codebase
  requires 3.11 (`from datetime import UTC` fails to import → conftest import error).
  Host test/lint/mypy tooling is genuinely broken, consistent with the implementer's
  "20 pre-existing mypy datetime.UTC 3.10-vs-3.11" note. Relied on the implementer's
  isolated Docker stack results (unit 62/62, integration patients 60/63 with the 2
  target tests passing, 3 pre-existing failures baseline-confirmed) + diff logic
  spot-check. SonarQube not configured. No FE changes (Playwright n/a).

---

## Quality Gate Summary

| Gate | Result |
|------|--------|
| No critical/major issues | PASS |
| Unit tests (isolated docker) | 62/62 PASS |
| Integration (isolated docker) | 60/63 (3 pre-existing baseline failures) |
| Security (tenant isolation) | PASS — foreign → 404, no PII leak |
| Follows CLAUDE.md / codebase conventions | PASS (mirrors visit_service) |
| Host tooling | broken (py3.10) — noted, relied on docker results |

**Decision: APPROVED.** Proceed to IN_TESTING.
