# Handoff: TASK-069 → Test Agent

**From**: Code Review Agent (iteration 3 — APPROVED)
**To**: Test Agent
**Status**: IN_TESTING

## Context

Tag system for medicines and services. Polymorphic `entity_tag` table (clinic-scoped, RLS), BE attach/detach/list/autocomplete + AND-filter endpoints, FE `TagInput` wired into medicine/service create/edit modals and list-view chips.

- **BE branch**: `feature/TASK-069-tag-system` (`clinic-cms-merge`)
- **FE branch**: `feature/TASK-069-tag-system` (`clinic-cms-web`)
- Review report: `docs/tasks/TASK-069/handoff/review-report.md`

## Already covered by automated tests — DO NOT re-run manually

### Backend integration (real DB) — `tests/integration/tags/test_tags_e2e_real_db.py` (25 tests, all pass)
- Happy path attach → list → detach (medicine + service): `test_attach_list_detach_medicine_tag`, `test_attach_list_detach_service_tag`
- 403 when `medicine.manage` / `service.manage` missing (doctor token): `test_403_medicine_manage_required_for_attach`, `test_403_service_manage_required_for_attach`
- **Cross-clinic isolation → 404**: `test_cross_clinic_isolation`
- AND-filter on `?tags=`: `test_medicine_and_filter`, `test_service_and_filter`
- 404 on attach/list for non-existent entity: `test_404_attach_nonexistent_*`, `test_404_list_tags_for_nonexistent_*`
- Autocomplete scoped by clinic + entity_type + prefix + auth (401/403): `test_medicine_autocomplete_scoped_to_clinic`, `test_*_autocomplete_requires_*_read`, `test_autocomplete_prefix_filter`, `test_unauthenticated_autocomplete_returns_401`

### Frontend unit/component (Vitest) — 7 tests, all pass
- `src/tests/admin/MedicinesPage.tags.test.tsx`: renders TagInput, attach on create, **detach on edit-remove (B1)**, list chips
- `src/tests/admin/ServicesPage.tags.test.tsx`: renders TagInput, **detach on edit-remove (B1)**, list chips

**Action for Test Agent**: run the BE integration suite and the FE Vitest suite once to confirm green in the test environment, then focus effort on the E2E/manual scenarios below. Do not author duplicate API-level tests for the cases already listed.

## What needs E2E / manual testing

### FE E2E (Playwright) — login as admin (`admin / Demo@1234`), FE dev `:1420` → BE `:8001`

**E2E-1 — Add tag on medicine (AC1, AC4)**
1. `/admin/medicines` → open Create (or Edit an existing medicine).
2. In Tags field, type a prefix → assert autocomplete suggestions appear from previously-used tags.
3. Add a brand-new tag name + add an existing suggested tag. Save.
4. Reopen the medicine → both tags persist. Tag chips show in the list-view Tags column.

**E2E-2 — Remove tag on medicine (AC1 — the B1 fix, primary E2E focus)**
1. Edit a medicine that has ≥2 tags.
2. Click the X (`aria-label="Remove tag {name}"`) on one chip → chip disappears from form.
3. Save. Verify a `DELETE /api/v1/medicines/{id}/tags/{tagId}` fires (network tab).
4. **Reopen the edit modal → the removed tag must NOT reappear.** Remaining tag still present. List-view chips updated.

**E2E-3 — Add + remove tag on service (AC2)**
Repeat E2E-1 and E2E-2 for `/admin/services` (`DELETE /api/v1/services/{id}/tags/{tagId}`).

**E2E-4 — Search/filter by tag (AC3)**
1. Tag two medicines with a shared tag, one medicine without it.
2. Apply the tag filter (or call `GET /api/v1/medicines?tags=<tag>`) → only the two tagged medicines return. Repeat for services.
3. If multi-tag filter UI exists: two tags → AND semantics (only entities having BOTH).

**E2E-5 — Consistency list vs detail (AC5)**
Confirm the same tag set shows in list-view chips and in the edit modal for the same entity after add/remove operations.

### Manual / exploratory edge cases
- Add a tag, remove it again before saving (net no-op) → no attach and no detach call on save.
- Re-add a tag with the same name as one just removed in the same session → ends as a net no-op (name in both original and current).
- Duplicate tag name on the same entity → BE unique constraint `(clinic_id, entity_type, entity_id, name)`; UI should not create a duplicate chip. Verify graceful handling (no error toast for idempotent attach).
- Tag normalization (lowercase/trim per task notes) — confirm `"  Cardio "` and `"cardio"` collapse consistently.
- Cross-clinic via UI: a second clinic's admin must not see clinic A's tags in autocomplete (BE test covers API; spot-check UI if multi-clinic login is available).

## Known non-blocking items (do NOT file as new bugs — already triaged in review)
- m1: autocomplete `like` prefix not escaping `%`/`_` (low risk, clinic-scoped read-only).
- m3: TagInput keyboard nav minimal (no ArrowUp roving focus / Enter-to-select-highlighted).
- m4: `bulk_delete_entity_tags` not wired into entity-delete paths → orphan rows on entity deletion (follow-up).
- m5: N+1 per-row tag fetch in list view (React Query cached 30s).

If E2E-2/E2E-3 (tag removal persistence) pass and AC3 filter returns correct results, the task meets all acceptance criteria.
