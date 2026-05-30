# Code Review Report — TASK-065

**Reviewer**: Code Review Agent
**Date**: 2026-05-31
**Decision**: **APPROVED** → IN_TESTING
**SonarQube**: DISABLED (skipped per agent guide)

## Scope Reviewed

- BE branch `feature/TASK-065-prescriptions-vss-config`, commit `c917fe4` (TASK-065 only; commits `826f5ce`/`40e613e` belong to TASK-064 and were excluded from review).
- FE branch `feature/TASK-065-prescriptions-vss-fix`, commit `4bf16f1` (TASK-065 only; `c9a09d7`/`905c3c0`/`9df90f7` belong to TASK-064/068 and were excluded).

> Note: the BUG-003 BE endpoint, VSS config endpoints, FE workaround removal, and VSS save wiring were all verified against the committed TASK-065 changes (not the working tree, which was checked out on `feature/TASK-068-theme-system`).

## Focus-Area Findings

### 1. BUG-003 cross-tenant isolation — PASS
`prescription_service.get_by_visit()` queries the `prescriptions` table directly with
`Prescription.visit_id == visit_id AND Prescription.clinic_id == clinic_id AND is_deleted == False`.
There is no separate visit lookup, and none is needed: even if a clinic-A user supplies a clinic-B
`visit_id`, the `clinic_id` filter guarantees only clinic-A rows are returned (empty otherwise). RLS
via tenancy middleware is also active (double protection). A foreign `visit_id` returns `200` with an
empty list rather than `404` — acceptable and matches the test design.

### 2. api_key in audit logs — PASS (not at risk)
VSS config is stored under the `vss` key inside `clinic_settings.settings` JSONB.
- `ClinicSettings` does **not** declare `__auditable__`, so the auto `after_flush` audit listener never
  snapshots it.
- `settings_service.update_settings()` does **not** call `write_audit()`; its `log.info("settings_updated")`
  logs only `clinic_id` + `user_id`, never the settings blob.

Therefore the `api_key` never reaches an audit log or app log. The `__audit_exclude__` redaction only
operates on top-level column names anyway (it would not redact nested JSONB keys), but that path is not
exercised here.

### 3. VSS permission codes (`vss:read`, `vss:sync`) — PASS
Both are seeded in `alembic/versions/0029_bhyt_toggle.py` (lines 33–34). Not newly invented.
GET uses `vss:read`, PUT uses `vss:sync` — consistent with existing sync-log / submit-claim usage.

### 4. Feature-flag gate on config endpoints — ACCEPTABLE (MINOR observation)
Both config endpoints are gated behind `require_feature("bhyt")`. The review brief questioned whether
config should be reachable before bhyt is enabled. In practice this is consistent and not a blocker:
the FE `VssIntegrationConfigPage` itself short-circuits to `NotEnabledFallback` when `bhytEnabled` is
false, so it never calls the endpoints when bhyt is off. The `bhyt` flag is toggled via a separate
clinic-level setting (migration 0029 `bhyt_enabled`), not through this VSS config — so there is no
chicken-and-egg lockout. Leaving as a MINOR design note for the test agent to confirm the enable flow.

### 5. FE silent `catch(() => {})` — PASS (fixed)
`VssIntegrationConfigPage.handleSave` now calls `api.put("/api/v1/integrations/vss/config", config)`
with no inner `.catch`. `apiClient.put` throws on non-2xx (apiClient.ts:126/133), so failures propagate
to the outer `catch` which sets `saveResult = { ok: false, msg: t("config.saveError") }`. Real error
handling confirmed.

### 6. FE `doctor/api.ts` workaround — PASS (fully removed)
The ~18-line BUG-003 fallback (`/prescriptions?visit_id=` + array/wrapper handling + `catch { return null }`)
is gone. Replaced with a clean call to `GET /visits/{id}/prescriptions` typed as `PrescriptionListResponse`,
returning `result.items[0] ?? null`. The KNOWN-BUG header comment was updated to "fixed (TASK-065)".

## Quality Gates

| Gate | Result |
|------|--------|
| BE integration tests (prescription + vss) | **31/31 passed** (`test_prescription_get_visit.py` 7, `test_vss_config_endpoints.py` 9, `test_vss_endpoints.py` 15) |
| FE type-check (TASK-065 files) | **No errors** in api.ts / types.ts / VssIntegrationConfigPage.tsx (9 pre-existing TS errors in unrelated files) |
| BE ruff (new code) | Clean. 7 ruff findings exist but all on **pre-existing** lines outside the TASK-065 diff (I001 import order, UP037/F821 on `to_response` line 699, B904 on eligibility-check line 104) |
| BE mypy | 1 error on `prescription_service.py:699` (`to_response` forward-ref) — **pre-existing**, outside diff |

## Issues

### MAJOR — none

### MINOR
1. **api_key returned in plaintext** (`vss_schemas.py:VssConfigResponse.api_key`, `vss_service.get_vss_config`).
   The GET response returns the stored key verbatim to any `vss:read` user. Endpoint is permission-gated
   and HTTPS, so not a CRITICAL leak, but consider masking (e.g. `***` for non-empty keys) on GET, accepting
   the full value only on PUT. Implementer explicitly flagged this for review — recommend follow-up, not a
   release blocker.
2. **FE `VssConfig` interface lacks `enabled`** (`VssIntegrationConfigPage.tsx:47-51`). BE schema supports
   `enabled` but the form cannot toggle it; save omits it (safe via `exclude_none`). Pre-existing FE gap, not
   introduced by this task.
3. **Pre-existing ruff/mypy debt** in prescriptions module (I001 import ordering, UP037/F821 forward-ref on
   `to_response`). Not introduced here; recommend a separate cleanup task. AC says "ruff + mypy pass" — the
   new TASK-065 code is clean, but the module still carries pre-existing findings.

## Decision Rationale

All six focus areas pass (or are acceptable-with-note). All new tests pass, the new code is lint/type clean,
cross-tenant isolation is sound, and no secret is logged. The only security item (plaintext api_key in GET)
is a hardening improvement, not a leak given the permission gate. **APPROVED for testing.**
