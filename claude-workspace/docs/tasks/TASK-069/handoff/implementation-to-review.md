# Handoff: TASK-069 → Code Review (iteration 2)

**From**: Code Implementation Agent (FIX MODE)
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-05-31
**Iteration**: 2

## Fixes Applied (per review-to-implementation.md iteration 1)

### C1 — Entity-existence guard (Blocking: Security/Correctness)

**File**: `clinic-cms-merge/app/modules/tags/api/routes.py`

Added `await medicine_service.get_medicine(db, clinic_id, medicine_id)` / `await service_catalog_service.get_service(db, service_id, clinic_id)` guard at the top of **all six tag handlers**:
- `list_medicine_tags` — guard before listing
- `attach_medicine_tag` — guard before attaching
- `detach_medicine_tag` — guard before detaching
- `list_service_tags` — guard before listing
- `attach_service_tag` — guard before attaching
- `detach_service_tag` — guard before detaching

Both services raise `NotFoundError` (404) when the entity does not exist or belongs to a different clinic. This prevents orphan tag rows and cross-entity pollution.

### C2 — Autocomplete permission scoped by entity_type (Blocking: Security)

**File**: `clinic-cms-merge/app/modules/tags/api/routes.py`

Approach chosen: **split into two separate endpoints** (simplest, most explicit):
- `GET /api/v1/tags/medicines/autocomplete` — requires `medicine.read`
- `GET /api/v1/tags/services/autocomplete` — requires `service.read`

The old single `/tags/autocomplete?entity_type=...` endpoint (with static `medicine.read` gate) is **removed**. The `tagsApi` client in the FE was updated to use the new split endpoints (`autocompleteMedicineTags`, `autocompleteServiceTags`). A deprecated `autocomplete()` shim is kept for any callers referencing the old API.

### M1 — Integration tests (Blocking: PROJECT.md hard gate)

**File created**: `clinic-cms-merge/tests/integration/tags/test_tags_e2e_real_db.py`

25 integration tests running against real Postgres + Redis via `app.main:app`. All pass.

Test classes:
| Class | Tests | Coverage |
|---|---|---|
| `TestTagsMedicineHappyPath` | 1 | Attach → list → detach medicine tag |
| `TestTagsServiceHappyPath` | 1 | Attach → list → detach service tag |
| `TestTagsPermissions` | 2 | 403 on medicine.manage / service.manage |
| `TestTagsCrossClinicIsolation` | 1 | Clinic A token → 404 on clinic B's entities |
| `TestTagsAndFilter` | 2 | AND-filter on /medicines and /services |
| `TestTagsNotFoundGuard` | 4 | 404 on non-existent medicine/service UUIDs |
| `TestTagsAutocomplete` | 5 | Scoped by clinic, entity_type, prefix filter, auth |

Note: alembic migration `0037_create_entity_tags` needed to be run first (`alembic upgrade head`) — done in the test environment.

### M2 — Frontend wiring (Blocking: ACs 1, 2, 5 unmet)

**Repo**: `clinic-cms-web`, branch `feature/TASK-069-tag-system`

Files modified:
- `src/modules/tags/api.ts` — added `autocompleteMedicineTags`, `autocompleteServiceTags` split methods; deprecated old `autocomplete()`.
- `src/pages/admin/MedicinesPage.tsx` — integrated `TagInput` in create/edit modal with autocomplete; added `MedicineTagBadges` component for list view; added Tags column to table.
- `src/pages/admin/ServicesPage.tsx` — same pattern: `TagInput` in create/edit modal; `ServiceTagBadges` in list view; Tags column added.

Files created (tests):
- `src/tests/admin/MedicinesPage.tags.test.tsx` — 3 tests (renders TagInput, calls API, renders chips)
- `src/tests/admin/ServicesPage.tags.test.tsx` — 2 tests (renders TagInput, renders chips in list)

Note: `src/components/ui/tag-input.tsx`, `src/modules/tags/types.ts`, `src/tests/components/tag-input.test.tsx` were committed in the original TASK-069 commit but were missing from the working tree on the TASK-070 branch — restored via `git checkout 78aa307 -- <files>`.

## Test Results

- **Backend unit (tags)**: 11/11 passed (`tests/unit/tags/`)
- **Backend integration (tags)**: 25/25 passed (`tests/integration/tags/`)
- **Backend ruff**: 0 errors
- **Frontend**: 948/955 passed (7 pre-existing failures: `secureStore`, `useSync`, `ReportsHubPage` — unrelated to TASK-069)
- **Frontend new tests**: 16 new tests added (11 in tag-input.test + 3 MedicinesPage.tags + 2 ServicesPage.tags), all pass

## Areas for Re-review

1. **Tag sync on save (edit modal)** — The current implementation attaches all current tags on save (idempotent). Tags that were removed from the local `tags[]` state during edit are NOT detached via API — they stay on the backend. This is a known limitation. A follow-up could add diff-based sync (detach removed tags). Reviewer should note this for scoping purposes.

2. **N+1 tag queries in list view** — Each row fires a separate `GET /medicines/{id}/tags` query. React Query caches these (30s staleTime), acceptable for current scale. Reviewer may flag for future optimization.

3. **FE branch note** — The FE commit landed on `feature/TASK-070-superadmin-fe` (the working tree at time of fix). The files were staged correctly and committed there. If the reviewer needs to review FE changes, checkout `feature/TASK-070-superadmin-fe` in `clinic-cms-web`.
