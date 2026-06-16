# Handoff: TASK-081 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-06-17

---

## Summary

Implemented PHẦN KHÁM BỆNH (Clinical Examination Section) by extending the existing vitals module. Added `exam_status` as a new `data_type`, seeded 13 examination items via migration 0043 into `system_vital_preset.fields`, and built a new `ExaminationSection` React component in the FE with toggle-button UI and read-only timeline display.

---

## Commits

| Repo | Branch | Commit SHA | Description |
|------|--------|-----------|-------------|
| `clinic-cms` | `feature/TASK-081-examination-section` | `6e0eade` | feat(vitals): add exam_status data_type + PHẦN KHÁM BỆNH seed |
| `clinic-cms-web` | `feature/TASK-081-examination-section` | `f5e7325` | feat(doctor): add ExaminationSection component for PHẦN KHÁM BỆNH |

---

## Files Changed

### Backend (`clinic-cms`)

| File | Change |
|------|--------|
| `app/modules/vitals/models/vital_field_definition.py` | Added `"exam_status"` to `VALID_DATA_TYPES` |
| `app/modules/vitals/schemas/vitals_schemas.py` | Added `"exam_status"` to `VALID_DATA_TYPES` in schema layer |
| `app/modules/vitals/services/validator_service.py` | `exam_status` fields: skip required-check + reject numeric values + allow field_status/field_notes |
| `app/modules/vitals/services/definition_service.py` | `_snapshot_current_definitions()` now includes `options`, `group_name`, `placeholder`, `help_text`, `decimal_places` |
| `app/modules/vitals/services/preset_service.py` | `clone_preset_to_clinic()` snapshot now includes same extended fields |
| `alembic/versions/0043_seed_examination_fields.py` | Migration: appends 13 exam fields to ALL `system_vital_preset.fields` rows |
| `tests/unit/vitals/test_exam_status.py` | 13 unit tests: schema validation, validator status-only behavior |
| `tests/integration/vitals/test_exam_status_integration.py` | 11 integration tests: preset seed, API create, vitals POST/GET, snapshot metadata |
| `tests/integration/vitals/test_vitals_api.py` | Updated `TestAC1Pediatric`: count 5→18 (5 vitals + 13 exam), key set updated |

### Frontend (`clinic-cms-web`)

| File | Change |
|------|--------|
| `src/modules/doctor/types.ts` | Added `"exam_status"` to `VitalDataType` union |
| `src/components/doctor/ExaminationSection.tsx` | New component: renders exam_status fields as toggle-button pairs with note textarea + readOnly timeline mode |
| `src/components/doctor/VitalsTab.tsx` | Split definitions → vitalsDefinitions + examDefinitions; ExaminationSection integrated into form + timeline; exam status/notes merged in save payload |
| `src/locales/vi/doctor.json` | Added `exam.*` i18n keys (vi) |
| `src/locales/en/doctor.json` | Added `exam.*` i18n keys (en) |
| `src/components/doctor/ExaminationSection.test.tsx` | 10 unit tests: render, labels, toggle, note show/hide, deselect, readOnly, empty list, group filter |

---

## Test Results

### Backend

| Suite | Tests | Result |
|-------|-------|--------|
| Unit: `tests/unit/vitals/test_exam_status.py` | 13/13 | PASS |
| Integration: `tests/integration/vitals/test_exam_status_integration.py` | 11/11 | PASS |
| Integration: `tests/integration/vitals/test_vitals_api.py` | 59/59 | PASS |
| **Total vitals suite** | **72/72** | **PASS** |

### Frontend

| Suite | Tests | Result |
|-------|-------|--------|
| `ExaminationSection.test.tsx` | 10/10 | PASS |
| `VitalsTab.test.tsx` | 12/12 | PASS (existing, unbroken) |
| TypeScript check (`tsc --noEmit`) | — | PASS |
| ESLint on new/modified files | 0 errors | PASS |

---

## Architecture Discovery / Deviation from Plan

**Critical deviation**: The implementation plan stated seed rows should use `clinic_id=NULL` (`is_system=true` global rows). However, the actual DB schema has `clinic_id NOT NULL` on `vital_field_definition`. Inspection revealed:
- System presets are distributed via `system_vital_preset.fields` (JSONB array)
- When a clinic onboards, `clone_preset_to_clinic()` creates rows with the clinic's own UUID
- There are NO global `clinic_id=NULL` rows in `vital_field_definition`

**Fix**: Migration 0043 was rewritten to **append 13 exam fields into `system_vital_preset.fields`** for all specialty presets, matching the correct architecture. Clinics receive exam fields on next onboarding clone. Existing clinic definitions are not retroactively updated (correct behavior — clinic controls their active definitions).

This also means `TestAC1Pediatric` in the existing test suite had to be updated (5→18 fields, added 13 exam keys to expected set).

---

## Review Focus (4 Verdicts Requested)

### (a) exam_status status-only validation

- `validator_service.py` correctly rejects any key with `data_type='exam_status'` appearing in `values` payload (raises INVALID error)
- `exam_status` fields are skipped from the `is_required` check in `validate()`
- `validate_annotations()` accepts `field_status ∈ {normal, abnormal}` and free-text `field_notes` for exam keys
- No threshold auto-status computation runs on exam fields
- **Verdict needed**: Confirm the double-guard pattern (skip in required-check loop + skip in value-coerce loop) is clean and doesn't have edge cases

### (b) Snapshot now carries full metadata?

Before TASK-081: `_snapshot_current_definitions()` stored only: `key, label, data_type, unit, min/max/warning ranges, is_required, sort_order, is_active, is_deleted`.

After TASK-081: Added `decimal_places, options, group_name, placeholder, help_text`.

`options` and `group_name` are essential for reconstructing exam field labels (custom Âm tính/Dương tính) and grouping from old visit snapshots.
- **Verdict needed**: Confirm the snapshot now contains sufficient metadata to fully reconstruct an old visit's exam form (labels, group, options, sort order)

### (c) FE renders old visits from snapshot?

The current FE (`VitalsTab.tsx`) renders the **timeline** from:
1. `vitalsDefinitions` (current active definitions) for determining labels
2. `rec.values` for numeric values
3. `rec.field_status` + `rec.field_notes` for status/notes

**Gap identified**: The timeline currently reads labels from `definitions` (current active), not from the visit record's `schema_version` snapshot. This means if a clinic renames a field or changes `group_name`, old visit timelines would show the current label, not the original.

**For exam fields specifically**: The FE correctly reads `rec.field_status[key]` to display exam status in the timeline via `ExaminationSection readOnly`. However, the label lookup (`defn.label`, `defn.options`) still comes from current `examDefinitions`, not the version snapshot.

**Full snapshot-based rendering** would require: `GET /vitals/definitions/version/{rec.schema_version}` per record in the timeline. This is a known pre-existing gap (not introduced by TASK-081) — confirmed the existing `VitalsTab.test.tsx` doesn't test snapshot-based rendering either.

- **Verdict needed**: Is the current behavior (current-definitions label lookup for timeline) acceptable for now, or should TASK-081 require full snapshot-based rendering? If yes, this needs a new API call per timeline record.

### (d) Config editor changes

The existing `VitalsPage.tsx` (`/admin/vitals`) already shows ALL `vital_field_definition` rows including those with `data_type='exam_status'`. Admins can already:
- Toggle `is_active` to show/hide exam items
- Update labels via the edit modal
- Reorder via sort buttons

No code changes were made to `VitalsPage.tsx` because the requirement "extend Vital Schema Editor to include `kham_benh` group" is already satisfied by the existing UI showing all definition rows. The `DATA_TYPES` dropdown in `AddFieldModal` uses a hardcoded list `["number", "string", "boolean", "enum"]` (admin types) — `exam_status` is intentionally excluded from admin-create since it should only come from the system preset.

- **Verdict needed**: Confirm that the existing VitalsPage adequately covers the config requirement (D), or if a dedicated group-filter view is needed.

---

## Known Gaps / Deferred

1. **FE timeline snapshot rendering**: Old visit labels use current-definitions, not version snapshot (pre-existing gap, not regressed by TASK-081)
2. **Print integration**: Exam section not shown in prescription print (out of scope per plan — "chỉ làm nếu được xác nhận")
3. **Admin `exam_status` in add-field dropdown**: Deliberately excluded — exam fields come from preset clone, not manual admin creation
