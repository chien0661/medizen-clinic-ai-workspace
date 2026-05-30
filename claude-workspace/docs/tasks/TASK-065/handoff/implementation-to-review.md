# Handoff: TASK-065 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-05-31

## Summary

Fixed BUG-003 (GET /visits/{id}/prescriptions returning 405) by adding the missing GET endpoint to the BE prescriptions module. Added GET/PUT /api/v1/integrations/vss/config endpoints using clinic_settings JSONB storage. Updated FE to remove the BUG-003 workaround and wire the real endpoints.

## Files Changed

### BE — clinic-cms-merge (branch: feature/TASK-065-prescriptions-vss-config)

- `app/modules/prescriptions/api/routes.py`: Added `GET /visits/{visit_id}/prescriptions` → `PrescriptionListResponse`. Declared BEFORE the POST to avoid FastAPI routing conflicts. Permission: `prescription.read`.
- `app/modules/prescriptions/schemas/prescription_schemas.py`: Added `PrescriptionListResponse` schema (`items: list[PrescriptionResponse]`, `total: int`, `visit_id: UUID`).
- `app/modules/prescriptions/services/prescription_service.py`: Added `get_by_visit(db, visit_id, clinic_id)` — queries by `visit_id + clinic_id + is_deleted=False`, ordered by `prescribed_at ASC`.
- `app/modules/integrations/vss/api/routes.py`: Added `GET /config` (vss:read) + `PUT /config` (vss:sync), both behind `require_feature("bhyt")`.
- `app/modules/integrations/vss/schemas/vss_schemas.py`: Added `VssConfigResponse` + `VssConfigUpdate` schemas.
- `app/modules/integrations/vss/services/vss_service.py`: Added `get_vss_config()` + `update_vss_config()` — stores config under `vss` key in `clinic_settings.settings` JSONB (no new migration required).
- `tests/integration/test_prescription_get_visit.py`: 7 new integration tests (200 shape, prescriptions returned, permission gate 403, invalid UUID 422, cross-tenant isolation).
- `tests/integration/test_vss_config_endpoints.py`: 9 new integration tests (GET/PUT 200 shapes, partial update, permission gates, tenant isolation).

### FE — clinic-cms-web (branch: feature/TASK-065-prescriptions-vss-fix)

- `src/modules/doctor/api.ts`: Replaced 18-line BUG-003 workaround in `getVisitPrescription` with a clean 4-line call to `GET /visits/{id}/prescriptions`. Added `PrescriptionListResponse` import.
- `src/modules/doctor/types.ts`: Added `PrescriptionListResponse` interface.
- `src/pages/admin/VssIntegrationConfigPage.tsx`: Replaced placeholder `api.patch("/api/v1/admin/integrations/vss/config", ...)` (with silent error swallow) with `api.put("/api/v1/integrations/vss/config", config)`.

## Test Results

- New integration tests: **16/16 passed** (test_prescription_get_visit.py × 7, test_vss_config_endpoints.py × 9)
- Existing VSS tests: **15/15 passed** (test_vss_endpoints.py)
- Combined: **31/31 passed**
- `mypy` (3 modified BE files): **no issues found**
- FE `tsc --noEmit`: no new errors in modified files (pre-existing errors in unrelated files)

### BUG-001 Fix (2026-05-31 — test fix only)

The test file `VssIntegrationConfigPage.test.tsx` was stale — it mocked `api.patch` but the component now calls `api.put`. Three changes applied (test file only, no production code touched):

1. Added `put: vi.fn()` to the `vi.mock("../../lib/apiClient")` mock object.
2. Added `(api.put as ReturnType<typeof vi.fn>).mockResolvedValue({ ok: true })` in `beforeEach`.
3. Renamed test `"calls api.put on save form submit"` and updated assertion to `expect(api.put).toHaveBeenCalledWith("/api/v1/integrations/vss/config", expect.objectContaining({ api_url: expect.any(String) }))`.

**Result after fix**: FE test suite **909/909 passed** (88 test files). Commit: `fix(TASK-065): update VssIntegrationConfigPage test mock api.patch→api.put`.

## Design Decisions

1. **GET /visits/{visit_id}/prescriptions** — Option A chosen (visit-scoped path) because it's the canonical REST path. The `clinic_id` filter in `get_by_visit()` ensures cross-clinic isolation at the query level, not relying on RLS alone.

2. **VSS config storage** — Reusing `clinic_settings.settings` JSONB under key `"vss"` avoids a new migration. The `settings_service.update_settings()` deep-merge handles partial updates correctly. Config includes: `api_url`, `api_key`, `facility_code`, `enabled`.

3. **VSS config permissions** — Used `vss:read` for GET (consistent with sync-log), `vss:sync` for PUT (consistent with submit-claim). Admin-level config write needs the "sync" permission, which prevents read-only users from accidentally misconfiguring.

## Areas for Review Focus

1. **`get_by_visit()` query** — Verify the `clinic_id` filter is sufficient for cross-tenant isolation (RLS is also active via tenancy middleware, so it's double-protected).
2. **`PrescriptionListResponse` — visit_id field** — Confirm the `visit_id` is useful for the FE (the FE already knows it, but it confirms the BE understood the request).
3. **VSS config `api_key` field** — Currently returned in plaintext. The review agent should assess whether masking is needed (e.g., returning `***` for non-empty keys in GET responses).
4. **Import ordering** — Pre-existing I001 ruff issues in prescriptions module (not introduced by this task).
