# Handoff: TASK-069 → Code Review (iteration 3 — FINAL)

**From**: Code Implementation Agent (FIX MODE)
**To**: Code Review Agent
**Status**: IN_REVIEW
**Iteration**: 3 of 3

## Fix Applied

### B1 — Tag removal on save

**Files changed:**
- `src/pages/admin/MedicinesPage.tsx`
- `src/pages/admin/ServicesPage.tsx`

**What changed:**

Previously, tag state was `string[]` and save only called `attachMedicineTag`/`attachServiceTag` for all current tags (idempotent attach, no detach). Tags removed by the user would reappear on refetch.

Now:

1. Tag state is split into two:
   - `originalTags: Array<{id: string; name: string}>` — loaded from BE when opening edit modal (full objects with IDs)
   - `currentTags: Array<{id?: string; name: string}>` — tracks live UI state; existing tags keep their IDs, newly added tags have no ID yet

2. On save, a diff is computed:
   - `toAdd` = tags in `currentTags` whose name is NOT in `originalTags` → `attachMedicineTag`/`attachServiceTag`
   - `toRemove` = tags in `originalTags` whose name is NOT in `currentTags` → `detachMedicineTag`/`detachServiceTag` (uses stored `id`)

3. `onSuccess` invalidates `["medicine-tags", savedId]` / `["service-tags", savedId]` (specific entity cache, not the whole tag namespace).

4. `TagInput` props updated: `tags={currentTags.map(t => t.name)}`, `onAddTag` adds `{name}`, `onRemoveTag` filters by name.

**API signatures used:**
- `tagsApi.detachMedicineTag(medicineId: string, tagId: string)` → `DELETE /api/v1/medicines/{id}/tags/{tagId}`
- `tagsApi.detachServiceTag(serviceId: string, tagId: string)` → `DELETE /api/v1/services/{id}/tags/{tagId}`

### P1 — Branch fix

**Problem**: The previous iteration's FE wiring commit (`feat(tags): wire TagInput into medicine/service forms + list views`) was accidentally committed on `feature/TASK-070-superadmin-fe` instead of `feature/TASK-069-tag-system`.

**Fix applied**:
1. Cherry-picked commit `f94f019` from TASK-070 onto `feature/TASK-069-tag-system` (resolved one conflict in `src/modules/tags/api.ts` — kept the split autocomplete endpoints from the incoming side)
2. Applied B1 fix directly on `feature/TASK-069-tag-system`
3. Committed as `8e2bbcc fix(tags): wire tag removal on save in medicine/service edit modals (TASK-069)`

**Final branch state (`feature/TASK-069-tag-system`):**
```
8e2bbcc fix(tags): wire tag removal on save in medicine/service edit modals (TASK-069)
dd7b33d feat(tags): wire TagInput into medicine/service forms + list views (TASK-069)
78aa307 feat(tags): add TagInput component + tag API client (TASK-069)
```

## Test Results

- **Frontend (TASK-069 specific)**: 7/7 pass
  - MedicinesPage: 4 tests (renders TagInput, attach on create, detach on edit remove — NEW, list chips)
  - ServicesPage: 3 tests (renders TagInput, detach on edit remove — NEW, list chips)
- **Frontend (full suite)**: 947 pass, 10 pre-existing failures (all unrelated to TASK-069):
  - `secureStore.test.ts` — 5 failures (sessionStorage vs localStorage mismatch from TASK-065 auth fix)
  - `useSync.test.ts` — 2 failures (TASK-067 browser guard tests)
  - `ReportsHubPage.test.tsx` — 1 file (TASK-066 AR aging report)
  - `RequireSuperuser.test.tsx` — 3 failures (TASK-070 superadmin tests, wrong branch)
- **Backend**: unchanged from iteration 2 (25 integration + unit tests all pass)

## Verification

To manually verify B1 fix:
1. Start dev server (`npm run dev` in clinic-cms-web)
2. Login as admin, navigate to `/admin/medicines`
3. Open the edit modal for a medicine that already has tags
4. Click X on one of the tag chips to remove it — chip disappears from form
5. Click Save
6. Reopen the edit modal — the removed tag should be GONE (not reappear from server)
7. Repeat for `/admin/services`

Expected: removed tag is detached via `DELETE /api/v1/medicines/{id}/tags/{tagId}` on save, and does not reappear on refetch.
