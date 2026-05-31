# Handoff: TASK-069 Code Review → Implementation (CHANGES_REQUESTED)

**From**: Code Review Agent
**To**: Code Implementation Agent
**Status**: IN_PROGRESS (returned for fixes)
**Date**: 2026-05-31
**Iteration**: 2 of 3 (one iteration remaining)

Full report: `docs/tasks/TASK-069/handoff/review-report.md`

## Verdict: CHANGES_REQUESTED

Great progress — C1 (entity guard), C2 (split autocomplete permissions), and M1 (real-DB integration tests) are all verified fixed and correct. The frontend add + display path also works. **One blocking issue remains.**

## Required fix (blocking)

### B1 — Wire tag REMOVAL on save in the edit modals (AC violation)
Repo: `clinic-cms-web`. Files: `src/pages/admin/MedicinesPage.tsx`, `src/pages/admin/ServicesPage.tsx`.

Today the save mutation only attaches the current local tags:
```js
await Promise.all(tags.map((name) => tagsApi.attachMedicineTag(savedId, { name })));
```
Tags the user removes via the chip X are dropped from local state but never detached on the backend, so they silently reappear. The AC requires add **and** remove ("Có thể thêm/xóa tag trên form khai báo thuốc / dịch vụ").

Do this:
1. When loading existing tags in edit mode, keep the full `{id, name}` objects (the list endpoint returns ids), not just names.
2. On save, compute the diff against the originally-loaded tags:
   - Attach the newly-added names (current behavior).
   - For each removed tag, call `tagsApi.detachMedicineTag(savedId, tagId)` / `tagsApi.detachServiceTag(savedId, tagId)` using its `tag_id`.
3. Invalidate the `["medicine-tags", id]` / `["service-tags", id]` queries after save (already partially done).
4. Add a test (both pages) asserting that removing a previously-attached tag triggers the DELETE call and the tag disappears from the list after save.

The DELETE routes and the `detachMedicineTag`/`detachServiceTag` client methods already exist — this is a small, contained change.

## Also do before closing (process, not a code gate)

### P1 — Move the FE commits onto the TASK-069 branch
The frontend wiring is committed on `feature/TASK-070-superadmin-fe` (`f94f019`), not on `feature/TASK-069-tag-system`. Cherry-pick / move the TASK-069 FE commit(s) onto `feature/TASK-069-tag-system` so the feature can be merged independently of TASK-070. Confirm the working tree is on the TASK-069 branch when making the B1 fix and commit there.

## Recommended (non-blocking, may defer)
- m1: `ilike` + escape `%`/`_` in the autocomplete prefix.
- m4: wire `bulk_delete_entity_tags` into medicine/service delete paths (or formally defer) to avoid orphan tag rows on entity deletion.
- m3: TagInput keyboard nav (ArrowUp/roving focus/Enter-to-select); `aria-selected` is hard-coded false.

## Re-submission
After fixing B1 (and P1), update status to IN_REVIEW and overwrite `handoff/implementation-to-review.md` (iteration 3). This is the final review iteration — please ensure B1 is fully working (manual check: edit a medicine, remove a tag, save, reopen — tag should be gone).
