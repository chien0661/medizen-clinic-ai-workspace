# Fix Handoff: TASK-081 — Iteration 1 (post-review fix)

**From**: Code Implementation Agent
**To**: Code Review Agent
**Date**: 2026-06-17
**Based on**: CHANGES_REQUESTED review report (`review-report.md`)

## Summary

Two review findings addressed:
1. **MAJOR (blocker)**: FE timeline now renders old visits from their `schema_version` snapshot, not current active definitions.
2. **MINOR (B017 lint)**: `pytest.raises(Exception)` narrowed to `pytest.raises(ValidationError)`.

Issues 3 & 4 explicitly out of scope per instructions — not touched.

---

## Fix 1 — FE snapshot rendering (MAJOR, criterion D)

### Approach

Instead of filtering current active `examDefinitions` for timeline records, the component now:

1. **Fetches the version snapshot** via `GET /api/v1/vitals/definitions/version/{n}` for each unique `schema_version` seen in the loaded records.
2. **Caches by version number** in a `Map<number, VitalFieldDefinition[]>` (React state). A `useRef<Set<number>>` prevents duplicate concurrent fetches for the same version. Fetch fires once per unique version per component mount.
3. **Renders from the snapshot** — both exam (exam_status) and numeric/vitals field definitions for that record come from `snapshotCache.get(rec.schema_version)`, falling back to current active definitions if the snapshot hasn't loaded yet.
4. **Graceful degradation**: fetch failures are caught silently; the fallback is the current active definitions (no crash).

### Files changed

| File | Change |
|------|--------|
| `clinic-cms-web/src/modules/doctor/types.ts` | Added `VitalSchemaVersion` interface (version_number, definitions_snapshot, created_at) |
| `clinic-cms-web/src/modules/doctor/api.ts` | Added `getSchemaVersion(version: number): Promise<VitalSchemaVersion>` → `GET /api/v1/vitals/definitions/version/{n}` |
| `clinic-cms-web/src/components/doctor/VitalsTab.tsx` | Added `snapshotCache` state + `fetchingVersions` ref; `useEffect` to fetch missing versions from records; timeline now uses `snapDefs` from cache for `recVitalsDefs` and `recExamDefsFromSnap`; vitals field label lookup uses `recVitalsDefs.find()` (snapshot) instead of `vitalsDefinitions.find()` |

### Key lines in VitalsTab.tsx

- **State** (added after form state ~line 179): `snapshotCache: Map<number, VitalFieldDefinition[]>`, `fetchingVersions: useRef<Set<number>>`
- **Effect** (after `vitalsQuery` and `definitions` split): `useEffect(() => { /* fetch unique versions, cache, no-duplicate guard */ }, [vitalsQuery.data])`
- **Timeline render** (`records.map`): `snapDefs = snapshotCache.get(rec.schema_version)` → `recVitalsDefs` and `recExamDefsFromSnap` — used for `allKeys` construction, exam section `definitions` prop, and vitals label lookup

---

## Fix 2 — BE lint B017 (MINOR)

**File**: `clinic-cms/tests/unit/vitals/test_exam_status.py:69`

Changed:
```python
# Before
with pytest.raises(Exception):

# After
with pytest.raises(ValidationError):
```

Added `from pydantic import ValidationError` import. Pydantic v2 wraps `ValueError` raised by `@field_validator` in a `ValidationError`. Ruff B017 is now clean.

---

## Regression Test Added

**File**: `clinic-cms-web/src/components/doctor/VitalsTab.test.tsx`

**Test name**: `"renders deactivated exam item from schema_version snapshot (criterion D regression)"`

**What it proves**:
- Current active `getVitalDefinitions()` does NOT include `lung_exam` ("Phổi") — simulates admin deactivating the item.
- Old visit record at `schema_version=1` has `field_status: { lung_exam: "abnormal" }` and `field_notes: { lung_exam: "Ran nổ đáy phổi" }`.
- `getSchemaVersion(1)` returns a snapshot that DOES include `lung_exam` (is_active: false in snapshot too).
- After the snapshot loads, the timeline must show "Phổi" (original label) and "Ran nổ đáy phổi" (original note).
- Without the fix, "Phổi" would not appear at all (data in DB but not rendered).

Also: updated `doctorApi` mock object to include `getSchemaVersion`, and added a `beforeEach` default mock (returns empty snapshot) so all 10 pre-existing VitalsTab tests continue to pass unchanged.

---

## Commit SHAs

| Repo | Branch | SHA | Message |
|------|--------|-----|---------|
| `clinic-cms` | `feature/TASK-081-examination-section` | `a3ec28a` | `fix(vitals): narrow pytest.raises(Exception) to ValidationError in test_exam_status (B017)` |
| `clinic-cms-web` | `feature/TASK-081-examination-section` | `b1294c0` | `fix(vitals): render timeline old visits from schema_version snapshot (criterion D)` |

---

## Test & Lint Results

### FE (vitest)
- `VitalsTab.test.tsx`: **13/13 PASS** (10 pre-existing + 1 new snapshot regression + 2 others in file = 13 total)
- `ExaminationSection.test.tsx`: **10/10 PASS** (unchanged)
- **Total**: 23/23 PASS
- `tsc --noEmit`: 0 errors
- `eslint` on changed files: 0 errors

### BE (pytest in docker py3.11)
- `tests/unit/vitals/test_exam_status.py`: **13/13 PASS**
- `ruff check tests/unit/vitals/test_exam_status.py`: All checks passed (B017 gone)

---

## Out of Scope (not touched)

- **Issue 3** (`clone_preset_to_clinic` not wired into production onboarding): pre-existing; flagged for Test/Docs awareness.
- **Issue 4** (kham_benh group filter in admin editor): optional, deferred.
- Pre-existing B904 in `validator_service._coerce_type`: pre-existing on origin/main, not touched.
