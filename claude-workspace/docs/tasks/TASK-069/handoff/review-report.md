# Code Review Report: TASK-069 (Iteration 3 — FINAL)

**Reviewer**: Code Review Agent
**Date**: 2026-05-31
**Iteration**: 3 of 3 (final)
**Status**: APPROVED

## Summary

The sole blocking issue from iteration 2 (B1 — tag removal on save being non-functional) is now **fully and correctly fixed** on both the medicine and service pages, and the process issue (P1 — FE wiring landed on the wrong branch) is resolved: all TASK-069 frontend commits are now on `feature/TASK-069-tag-system`. All five acceptance criteria are satisfied. Verdict: **APPROVED → IN_TESTING.**

## B1 — Tag removal on save (FIXED, verified)

Verified in both `src/pages/admin/MedicinesPage.tsx` and `src/pages/admin/ServicesPage.tsx`:

- **Separate state tracked** — `originalTags: Array<{id; name}>` loaded from BE when opening edit modal (full objects incl. ids), and `currentTags: Array<{id?; name}>` for live UI state. (Medicines lines 84–86; Services lines 83–85.)
- **Diff computed on save** — `toAdd = currentTags not in originalTags(by name)`, `toRemove = originalTags not in currentTags(by name)`. (Medicines 167–170; Services 155–158.)
- **Both attach and detach called** — `Promise.all([...toAdd.map(attach...), ...toRemove.map(t => detach...Tag(savedId, t.id))])`. Removal correctly uses the stored tag `id`. (Medicines 171–174; Services 159–162.)
- **Query keys invalidated** — `["admin", "medicines"|"services"]` and `["medicine-tags"|"service-tags", savedId]` on success. (Medicines 178–179; Services 166–167.)
- **TagInput wiring** — `tags={currentTags.map(t => t.name)}`, `onAddTag` pushes `{name}`, `onRemoveTag` filters by name. The chip X button (`tag-input.tsx` line 144/228–233, `aria-label="Remove tag {name}"`) calls `onRemove → onRemoveTag(tag)`, so clicking X mutates `currentTags`, and the save diff then emits the DELETE. Full chain confirmed end-to-end.
- **Tests added** — `src/tests/admin/MedicinesPage.tags.test.tsx` (`calls detachMedicineTag when a tag is removed in edit mode and saved (B1 fix)`, asserts detach called with the tag id) and the equivalent `ServicesPage.tags.test.tsx` test.

The `detach*Tag` client methods that were dead code in iteration 2 are now actually called.

## P1 — Branch verification (FIXED, verified)

`git log --oneline feature/TASK-069-tag-system`:
```
8e2bbcc fix(tags): wire tag removal on save in medicine/service edit modals (TASK-069)
dd7b33d feat(tags): wire TagInput into medicine/service forms + list views (TASK-069)
78aa307 feat(tags): add TagInput component + tag API client (TASK-069)
```
All three TASK-069 FE commits are on the correct branch. The feature is no longer entangled with TASK-070 and can be merged independently. The conflict in `src/modules/tags/api.ts` during cherry-pick was resolved keeping the split autocomplete endpoints (verified: `autocompleteMedicineTags` / `autocompleteServiceTags` present, deprecated shim retained).

## Acceptance criteria

| AC | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| AC1 | Thêm/xóa tag trên form thuốc | PASS | TagInput in medicine modal; add via `onAddTag`, remove via diff+detach (B1) |
| AC2 | Thêm/xóa tag trên form dịch vụ | PASS | Same pattern in ServicesPage |
| AC3 | Tìm kiếm thuốc/dịch vụ theo tag | PASS | BE AND-filter on `GET /medicines?tags=` / `/services?tags=`; integration tests `test_medicine_and_filter`, `test_service_and_filter` |
| AC4 | Tag autocomplete từ tag đã dùng | PASS | Split endpoints `GET /tags/medicines/autocomplete` + `/tags/services/autocomplete`; TagInput consumes via `autocomplete*Tags` + `onQueryChange`; tests `test_autocomplete_prefix_filter`, scoped/auth tests |
| AC5 | Tag hiển thị nhất quán list + detail | PASS | `MedicineTagBadges`/`ServiceTagBadges` render `TagChip` in list views (MedicinesPage line 552); edit modal loads + shows tags |

## Security (final confirmation)

- **clinic_id isolation / RLS**: `alembic/versions/0037_create_entity_tags.py` adds `entity_tag` with non-null `clinic_id` FK, a `(clinic_id, entity_type, entity_id, name)` unique constraint, and applies `apply_rls_with_tenant_isolation(op, "entity_tag")`. RLS tenant isolation confirmed.
- **Cross-clinic test**: `tests/integration/tags/test_tags_e2e_real_db.py::test_cross_clinic_isolation` seeds two clinics and asserts **404** when clinic B lists/attaches against clinic A's medicine. Entity-existence guards (C1, iteration 1) plus RLS produce correct 404 isolation.

## Minor issues (non-blocking, deferred — unchanged from iteration 2)

- **m1** — autocomplete uses `like(f"{q}%")` without escaping `%`/`_` (clinic-scoped read-only, low risk). Recommend `ilike` + escape later.
- **m3** — TagInput keyboard nav minimal (`aria-selected={false}` hard-coded, no ArrowUp roving focus). Acceptable first cut.
- **m4** — `bulk_delete_entity_tags` not wired into entity-delete paths → orphan tag rows accumulate on entity deletion. Recommend wiring into delete handlers in a follow-up.
- **m5** — N+1 in list view (per-row `GET /{id}/tags`, React Query cached 30s). Acceptable at current scale.

None block this task. Recommend filing m4 as a follow-up so orphan rows don't accumulate.

## Verdict

**APPROVED** (iteration 3 of 3)

B1 is fixed correctly on both pages with tests; P1 branch reconciliation is complete; all five acceptance criteria pass; RLS isolation and the cross-clinic test are in place. Promoting to IN_TESTING.
