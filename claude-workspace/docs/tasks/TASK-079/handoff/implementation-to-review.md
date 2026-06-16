# Handoff: TASK-079 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-06-16

---

## Summary

Implemented dynamic vitals form that drives the doctor entry form and timeline from `GET /api/v1/vitals/definitions` instead of hardcoded fields, and extended the `visit_vitals` table with two JSONB columns (`field_status`, `field_notes`) to store per-field normal/abnormal status and notes in a structured way instead of concatenating into a text `notes` string.

---

## Files Changed

### Backend — `clinic-cms` (branch: `feature/TASK-079-dynamic-vitals`)

| File | Change |
|------|--------|
| `alembic/versions/0041_add_vital_field_status.py` | **NEW** — Alembic migration adding `field_status JSONB` and `field_notes JSONB` columns (nullable, `server_default '{}'::jsonb`) to `visit_vitals`. `down_revision = 0040_create_advice_template`. Downgrade drops both columns. No RLS changes needed. |
| `app/modules/vitals/models/visit_vitals.py` | Added `field_status: Mapped[dict]` and `field_notes: Mapped[dict]` JSONB columns with `server_default='{}'::jsonb`, `nullable=True`, `default=dict`. |
| `app/modules/vitals/schemas/vitals_schemas.py` | `VisitVitalsCreate`: added `field_status: dict[str,str] = {}` and `field_notes: dict[str,str] = {}`. `VisitVitalsResponse`: added same fields. |
| `app/modules/vitals/services/validator_service.py` | Added `VALID_STATUSES = frozenset({"normal","abnormal"})` and `validate_annotations(field_status, field_notes)` method — validates status values are in `{normal, abnormal}`, validates all keys exist in active definitions, ignores empty values, collects errors in `{field, code, message}` format without breaking existing `validate()` flow. |
| `app/modules/vitals/services/vitals_service.py` | Calls `validate_annotations()` after `validate()`, raises HTTP 422 if annotation errors exist, persists `field_status`/`field_notes` on the new `VisitVitals` record. |
| `tests/unit/vitals/test_validator.py` | Added `TestAnnotations` class with 12 unit test cases: valid normal/abnormal, invalid status value, unknown key in field_status, unknown key in field_notes, empty payload, empty strings ignored, notes with known key, multiple errors collected, both valid status+notes. |
| `tests/integration/vitals/test_vitals_api.py` | Added `TestFieldStatusAnnotations` class with 5 real-DB integration tests: POST round-trip (POST → assert response), GET returns field_status/field_notes, backward compat (POST without new fields → 201), invalid status value → 422, unknown annotation key → 422. |

### Frontend — `clinic-cms-web` (branch: `feature/TASK-079-dynamic-vitals`)

| File | Change |
|------|--------|
| `src/modules/doctor/types.ts` | `VisitVitals`: added `field_status?: Record<string,'normal'\|'abnormal'>` and `field_notes?: Record<string,string>`. `VitalsCreate`: same optional fields added. |
| `src/components/doctor/VitalsTab.tsx` | **REWRITE** — Removed `VITAL_FIELDS` (hardcoded 6 fields) and `NORMAL_RANGES` (hardcoded ranges). Now fetches `getVitalDefinitions()` via `useQuery`. Renders inputs by `data_type` (number/integer/text/boolean/select+options), shows `unit`, uses `placeholder`/`help_text`, groups by `group_name`, sorts by `sort_order`, marks `is_required`. Auto-evaluates status using `warning_min/warning_max` → fallback `min_value/max_value`. Manual toggle still works. Sends `{values, field_status, field_notes, notes?}` — no longer builds text notes string for status. Timeline renders dynamically: shows all definition keys plus any extra keys in `values`; colors rows by `field_status`; shows `field_notes` per field. BMI kept as derived value when height+weight keys exist in definitions. Shows `vitals.noSchemaError` when no active definitions loaded. |
| `src/components/doctor/VitalsTab.test.tsx` | **NEW** — 12 vitest tests: loading state, no-schema error, dynamic field render (label+unit), required marker, auto abnormal detection, auto normal detection, structured payload build with field_status+field_notes, normal value sends correct field_status, timeline color display with field_notes, backward compat (records without new fields), select input for data_type=select, group header render. |
| `src/locales/vi/doctor.json` | Added: `statusNormal`, `statusAbnormal`, `toggleStatus`, `noteFor`, `extraNotes`, `extraNotesPlaceholder`. |
| `src/locales/en/doctor.json` | Added: same 6 keys in English. |

---

## Test Results

### Backend (run in Docker — Python 3.11)

| Suite | Result |
|-------|--------|
| `tests/unit/vitals/test_validator.py` | **23/23 passed** (11 pre-existing + 12 new `TestAnnotations`) |
| `tests/integration/vitals/test_vitals_api.py` | **25/25 passed** (20 pre-existing + 5 new `TestFieldStatusAnnotations`) |
| Migration `alembic upgrade head` | Applied cleanly (`0041_add_vital_field_status` is HEAD) |
| `ruff check app/modules/vitals` | No new errors introduced (pre-existing I001/B004/B008 in unchanged files) |
| `mypy app/modules/vitals` | `Success: no issues found in 15 source files` |

### Frontend

| Check | Result |
|-------|--------|
| `VitalsTab.test.tsx` | **12/12 passed** |
| `npm run type-check` (tsc --noEmit) | **Clean — 0 errors** |
| `npm run lint` | No errors in modified files (pre-existing errors in VssIntegrationConfigPage.tsx, VssSyncLogPage.tsx) |

---

## Areas for Review Focus

### 1. Migration (`0041_add_vital_field_status.py`)
- Verify `nullable=True` + `server_default='{}'::jsonb` is correct pattern for backward compat
- Check that `downgrade()` correctly drops both columns in reverse order
- Pattern matches existing migration 0040 style (same ruff lint profile pre-exists)

### 2. `validate_annotations()` in validator_service.py
- Confirm error collection logic: errors accumulate across both `field_status` and `field_notes` in one pass
- Confirm empty strings are correctly skipped (not flagged as unknown)
- Confirm the method does NOT raise — it returns error list for the caller to decide

### 3. VitalsTab.tsx — Dynamic Render Rewrite
- Review `autoDetectStatus()`: priority `warning_min/warning_max` → fallback `min_value/max_value` → no auto-flag if neither
- Review `coerceValue()`: handles number/integer/boolean/select/text correctly
- Review `groupDefinitions()`: confirms sort by `sort_order` then group by `group_name`
- Review BMI detection: uses `.find(d => d.key === 'height' || d.key.includes('height'))` — may need stricter matching if keys diverge
- Review timeline rendering: shows all definition keys first, then any orphan keys from `values` dict (ensures old data with removed definitions is still visible)

### 4. Backward Compatibility
- Old `visit_vitals` rows: `field_status` and `field_notes` will be `{}` (from server_default) — FE handles with `?? {}` fallback
- FE `VisitVitals` type: both fields are `optional` — FE codebase handles `undefined` gracefully
- `VisitVitalsCreate.field_status`/`field_notes` default to `{}` — existing callers sending only `{values, notes}` continue to work

### 5. i18n
- 6 new keys added to both `vi/doctor.json` and `en/doctor.json` — confirm translations are acceptable

---

## Branches

- `clinic-cms`: `feature/TASK-079-dynamic-vitals` (commit `fb87dd1`)
- `clinic-cms-web`: `feature/TASK-079-dynamic-vitals` (commit `3161829`)
