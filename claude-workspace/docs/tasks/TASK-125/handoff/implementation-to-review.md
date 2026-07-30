# Handoff: TASK-125 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW

## Summary

Implemented `service_type` — a **per-clinic configuration table** (admin CRUD, not a hard-coded enum) that classifies the service catalog. 3 defaults (consultation/procedure/test — Khám/Thủ thuật/Xét nghiệm) are seeded per clinic via migration `0071` (existing clinics) and via a new-clinic-creation hook (future clinics). `service.service_type_id` is a nullable FK — old rows stay `NULL` ("chưa phân loại") and the existing service→visit_service→billing flow is untouched. Foundation for TASK-128 (Commission, % discount keyed on `service_type_id`) and TASK-126 (reporting).

Both worktrees are on `feature/TASK-125`, committed, and pushed. **Not merged to dev/main** — per instructions, that's the manager's call.

## Files Changed

### Backend (`_feat125-be`, branch `feature/TASK-125`)

**New:**
- `app/modules/services/models/service_type.py` — `ServiceType(BaseEntity)` model. `clinic_id` stays NOT NULL (unlike `DosageForm`, which is global) — every row belongs to exactly one clinic.
- `app/modules/services/schemas/service_type_schemas.py` — `ServiceTypeCreate/Update/Response/ListResponse`.
- `app/modules/services/services/service_type_service.py` — CRUD + `seed_defaults_for_clinic()` (idempotent — checks existing codes first) + `DEFAULT_SERVICE_TYPES` constant (must stay in sync with the migration's `_DEFAULTS`, cross-referenced in both files' docstrings).
- `alembic/versions/0071_service_type.py` — **down_revision="0070"** (verified `alembic heads` resolves to single head `0071`). Creates `service_type` table + RLS + seeds 3 defaults per existing clinic (loop over `SELECT id FROM clinic`, deterministic `uuid5` ids so re-runs are idempotent) + adds `service.service_type_id` (nullable FK, `ON DELETE SET NULL`).
- `tests/unit/services/test_service_type_service.py` — 9 new mock-based unit tests.
- `tests/integration/services/test_task125_service_type_e2e.py` — 6 new integration tests (real DB, direct service-layer calls, mirrors `test_task124_unit_conversion_admin_crud.py` pattern). **Not executed** — see Test Results.

**Modified:**
- `app/modules/services/models/service.py` — added `service_type_id` (nullable FK → `service_type.id`, `ON DELETE SET NULL`).
- `app/modules/services/models/__init__.py` — export `ServiceType`.
- `app/modules/services/schemas/service_schemas.py` — `ServiceCreate/Update/Response` gain `service_type_id` (+ `service_type_name` on Response, populated by routes-layer enrichment, not an ORM column).
- `app/modules/services/services/service_catalog_service.py` — `create_service`/`update_service` accept `service_type_id`, validated against the caller's `clinic_id` via new `_check_service_type_belongs_to_clinic()` (404 if missing/cross-tenant — same treatment as an unknown `visit_id`). `list_services` gains a `service_type_id` filter (excludes NULL rows when set — intentional).
- `app/modules/services/api/routes.py` — new `/service-types` CRUD routes (reuse `service.read`/`service.manage`, **no new permission**); `_enrich_service`/`_enrich_service_list` helpers (mirrors existing `_enrich_vs`/`_enrich_vs_list` pattern) attach `service_type_name`; `list_services` route adds `service_type_id` query param **and includes it in the Redis cache `params_key`** (otherwise a filtered query could serve a stale/wrong cached variant); `export_services` adds a "Loại dịch vụ" column (batch-resolved, not N+1).
- `app/modules/admin/services/clinic_service.py` — `create_clinic` now calls `service_type_service.seed_defaults_for_clinic()` so clinics created after migration `0071` get the same 3 defaults.
- `tests/unit/services/test_service_catalog_service.py` — 3 new tests (valid/invalid cross-tenant `service_type_id` on create/update).
- `tests/unit/services/test_service_schemas.py` — new `TestServiceTypeCreate`/`TestServiceTypeUpdate` classes + `service_type_id` cases on `ServiceCreate`.

### Frontend (`_feat125-web`, branch `feature/TASK-125`)

**New:**
- `src/pages/admin/ServiceTypesPage.tsx` — `/admin/service-types` config screen, mirrors `DosageFormsPage.tsx` (TASK-076): system rows (is_system=true) hide edit/delete.
- `src/tests/admin/ServiceTypesPage.test.tsx` — 12 tests (i18n parity + render), mirrors `DosageFormsPage.test.tsx`.

**Modified:**
- `src/modules/admin/types.ts` — `ServiceType`/`ServiceTypeCreate`/`ServiceTypeUpdate`; `Service`/`ServiceCreate`/`ServiceUpdate` gain `service_type_id`(+`service_type_name` on `Service`).
- `src/modules/admin/api.ts` — `adminServiceTypesApi` (defensively unwraps both `{items}` and bare-array responses); `adminServicesApi` threads `service_type_id` through list/create/update.
- `src/pages/admin/ServicesPage.tsx` — service-type `<select>` in the create/edit modal (loads `/service-types`); badge column in the list table; CSV/Excel import gains a `service_type_code` column, resolved to `service_type_id` at import time (unknown code → left unclassified, does not block the import).
- `src/modules/doctor/types.ts`, `src/components/doctor/ServicesTab.tsx` — `Service` type + a small badge next to the service name in the visit-service picker.
- `src/router/index.tsx`, `src/components/shell/Sidebar.tsx` — new route `/admin/service-types` + nav entry (`Tags` icon, `service.manage` permission).
- `src/locales/{vi,en}/admin.json` — `nav.serviceTypes`, `serviceTypes.*` block, `services.columns/form.serviceType(*)`, updated CSV import instructions.

## Test Results

**Backend** (run inside the project's own `docker-api:latest` image, `-v` bind-mount, **no ports exposed** — the local Python is 3.10 but the project requires ≥3.11):
- `pytest tests/unit/services -q` → **73 passed** (51 pre-existing + 22 new), 0 failed.
- `ruff check` on every new/modified file → clean.
- `alembic heads` → single head `0071`.
- `python -c "import app.main"` → imports clean, 35 routes registered (no route-name collisions).
- Integration tests (`tests/integration/services/test_task125_service_type_e2e.py`, 17 pre-existing `test_services_e2e.py` cases) → **collect cleanly**, ruff clean, but **NOT executed** — no non-w2e DB stack was available, and per instructions the w2e stack (ports 9999/5434/5436/6380/6382) must not be started. Written and ready for CI / whoever has DB access.

**Frontend** (ran via a `node_modules` junction to the sibling `_dev-web` worktree — `package.json` confirmed identical at the branch point, no new deps added):
- `npx tsc --noEmit` → clean.
- `npx eslint` on every new/modified file → clean.
- `npx vitest run` on `ServiceTypesPage.test.tsx`, `ServicesPage.test.tsx`, `ServicesPage.tags.test.tsx`, `ServicesTab.test.tsx`, `Sidebar-multi-role.test.tsx`, `router/settingsRedirect.test.tsx` → **20 + 11 = all passed**, 0 failed.

## Design Decisions Worth Reviewer Attention

1. **`service_type` is per-clinic (clinic_id NOT NULL)**, unlike `dosage_form` (TASK-076), which has global `clinic_id IS NULL` shared rows. This matches the plan/task explicitly ("seed 3 mặc định cho mỗi clinic hiện có" — per-clinic, not shared) and means a brand-new clinic needs its own seed (handled via the `create_clinic` hook).
2. **System rows (`is_system=true`) are fully locked** — cannot be edited *or* deleted (403), not just deletion-blocked. This is stricter than the plan's open wording ("admin có thể... sửa") but mirrors the existing `DosageForm` convention exactly and keeps `service_type_id` maximally stable for TASK-128 Commission. Flagged as a documented, reversible decision in the functional design (§10.3) if a reviewer wants edit-name-only allowed later.
3. **No new permission** — `/service-types` reuses `service.read`/`service.manage`, resolving the plan's open decision per the orchestration prompt's explicit instruction.
4. **Filter semantics**: `GET /services?service_type_id=X` excludes `NULL` rows (does not implicitly include "unclassified" in a type-scoped filter). Documented as intentional in both the functional design and API spec.
5. **Cache key**: `service_type_id` was added to the existing Redis list-cache `params_key` — required, otherwise filtered/unfiltered queries could cross-contaminate.
6. **PATCH cannot clear `service_type_id` back to NULL** — same pre-existing limitation as `category`; not something introduced by this task, called out explicitly so it isn't mistaken for a new bug.

## Areas for Review Focus

- `app/modules/services/services/service_type_service.py::_ensure_editable` (403 on system rows) and `service_catalog_service.py::_check_service_type_belongs_to_clinic` (404 cross-tenant) — the two guardrails protecting TASK-128's future stability.
- `alembic/versions/0071_service_type.py` — the per-clinic loop + `uuid5` determinism; please double check idempotency reasoning (re-running `upgrade()` against a DB that already has some rows should insert nothing new, via `ON CONFLICT DO NOTHING` + the partial unique index).
- `tests/integration/services/test_task125_service_type_e2e.py` — written but unverified (no DB stack). Please run once a DB is available, before/instead of trusting the unit-test coverage alone for the cross-tenant and NULL-filter behaviors.
- FE CSV import (`ServicesPage.tsx` `CsvImportModal`) — `service_type_code` resolution silently defaults to "unclassified" on an unrecognized code; confirm this fail-open behavior (vs. a hard validation error) matches expectations.

## Confirmations

- No `main`/`dev` branch touched — worktrees are on `feature/TASK-125` off `dev`, not merged.
- No Docker stack started on ports 9999/5434/5436/6380/6382 (w2e) — confirmed via `docker ps -a` before/after; those containers remain `Exited`.
- Both worktrees committed and pushed to `origin/feature/TASK-125`.
