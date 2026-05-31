# TASK-052 — Baseline Test Report (BE)

**Date**: 2026-05-29
**Target**: `../clinic-cms-merge` (branch `main`)
**Command**: `docker exec clinic_cms_w2e_api pytest -q` (full suite)
**Infra**: clinic_cms_w2e_{api,worker,postgres,redis} — all healthy

## Summary

| Result | Count |
|---|---|
| ✅ passed | 1119 |
| ❌ failed | 20 |
| 🔥 error (setup) | 385 |
| Duration | ~234s |

Total collected ≈ 1524 tests.

---

## Category A — 385 ERRORS: encryption ContextVar regression (1 root cause)

**Root cause**: `EncryptedString.process_bind_param` (`app/core/crypto/types.py:59`) raises
`RuntimeError: current_clinic_id ContextVar is not set` whenever a test fixture INSERTs a row
with encrypted PII columns (`User.email/phone/full_name/license_number/mfa_secret`,
`Patient.*`, `Clinic.*`) **directly via the DB session** — i.e. bypassing `TenancyMiddleware`,
which is the only thing that normally sets the ContextVar.

Introduced by **TASK-037 (column encryption)**. Test fixtures (including the shared helper
`tests/helpers/multi_clinic.py::create_test_user_with_clinic_role`) were never updated to set
the tenant context before flushing encrypted rows.

**Errors per area** (all same cause):
visits 58, patients 58, billing 33, prescriptions 20, vitals 19, admin 15, services 13,
appointments 13, reports 11, notifications 9, inventory 9, pharmacy 7, + hr_* (~70),
rbac_* (~20), sod 3, search 7, auth_lockout/refresh 2.

**Available fix primitive**: `app/core/tenancy.py:288` `with_tenant_context(clinic_id)`
(contextmanager that sets/resets `current_clinic_id`). Inserts of encrypted rows in fixtures
must be wrapped, e.g.:

```python
with with_tenant_context(clinic.id):
    session.add(user)
    await session.flush()
```

### Candidate fix strategies (need user decision)
- **A. Fix shared helpers + per-fixture wrapping** — update `multi_clinic.py` helpers and each
  fixture that raw-inserts users/patients/clinics to wrap in `with_tenant_context`. Correct &
  explicit, but touches many files. Cross-clinic tests (A vs B) need the right clinic_id per row.
- **B. Autouse conftest fixture** — seed a default `current_clinic_id` for the test session.
  Simplest, but breaks multi-clinic/RLS-isolation tests that legitimately use ≥2 clinics with
  different DEKs (write-under-A / read-under-B would fail).
- **C. Hybrid (recommended)** — fix the central helpers in `multi_clinic.py` to set context per
  created user's clinic, + add an explicit `with_tenant_context` to the remaining bespoke
  fixtures. Keeps multi-clinic semantics intact.

> ⚠️ Per CLAUDE.md **Database Error Handling Protocol**, not auto-applying a mass fix before
> user confirms direction (A/B/C) and scope.

---

## Category B — 20 FAILURES: behavior drift / possible regressions (need triage)

These are assertion failures, NOT the ContextVar error. Grouped:

| Area | Tests | Suspected cause |
|---|---|---|
| `unit/test_rls_helpers.py` | 2 (`test_executes_three_statements` ×2) | RLS helper now emits ≠3 SQL statements (ENABLE/FORCE/CREATE POLICY) — helper changed since test written. |
| `integration/test_rls_isolation.py` | 3 | RLS isolation behavior (clinic A/B own-rows, NULL clinic_id visibility). |
| `integration/test_rls_admin_bypass.py` | 2 | `cms_app_role` not superuser / restricted-role RLS block. |
| `integration/test_tenant_isolation_full.py` | 2 | audit-row tenant isolation (clinic A/B). |
| `integration/test_auth_mfa.py` | 3 | MFA challenge / mfa_token type (TASK-038). |
| `integration/test_auth_service_coverage.py` | 3 | login success/inactive-clinic/change-password. |
| `integration/test_jwt_includes_perms.py` | 2 | JWT RBAC claim shape / rbac service call. |
| `integration/admin/test_admin_e2e.py` | 3 | pediatric head_circumference, create-clinic-403, tenant-isolation settings. |

**Triage needed per group**: is each a *real regression* (fix the code) or a *stale test*
(behavior intentionally changed by TASK-035/037/038 → update the test)? Must not blindly
"fix" by loosening assertions.

---

## Recommended next steps

1. **User decides Category A strategy** (A / B / C-recommended) + scope sign-off.
2. Apply Category A fix → expect ~385 errors → 0; re-run to get the *true* failure set.
3. Triage Category B with full tracebacks; classify regression vs stale; fix accordingly
   (code fix vs test update), following Database Error Handling Protocol for any data/query change.
4. THEN proceed to the API-mapping deliverable + coverage-gap audit (the documentation half of TASK-052).
