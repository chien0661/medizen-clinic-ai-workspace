# Vitals Dynamic Form — Functional Design

**Task**: TASK-009  
**Status**: DONE  
**Date**: 2026-04-27  

---

## 1. Overview

The Vitals Dynamic Form module provides per-clinic configurable vital sign recording with schema versioning, runtime validation, and multi-specialty preset support.

## 2. Database Schema

### 2.1 `system_vital_preset`
Global read-only table; no RLS (no clinic_id). Populated at migration time.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| specialty_code | VARCHAR(50) UNIQUE | general/dental/pediatric/obstetric/dermatology |
| name | VARCHAR(100) | Display name |
| description | VARCHAR(500) | |
| fields | JSONB | Array of field definitions |
| created_at / updated_at | TIMESTAMPTZ | |

### 2.2 `vital_field_definition`
Per-clinic field catalog. Extends BaseEntity (RLS, soft-delete, audit, versioned).

| Column | Type | Notes |
|--------|------|-------|
| key | VARCHAR(100) | snake_case, immutable once set |
| label | VARCHAR(200) | Mutable (triggers version bump) |
| data_type | VARCHAR(20) | number/integer/text/boolean/select — immutable |
| unit | VARCHAR(20) | Mutable |
| min_value / max_value | NUMERIC(10,4) | Range enforcement (INVALID if violated) |
| warning_min / warning_max | NUMERIC(10,4) | Frontend visual only, not enforced by backend |
| decimal_places | INTEGER | |
| options | JSONB | Required for data_type='select' |
| is_required | BOOLEAN | Mutable (triggers version bump) |
| sort_order | INTEGER | |
| group_name | VARCHAR(100) | UI grouping |
| is_active | BOOLEAN | Soft-disable without deleting |
| is_system | BOOLEAN | Cloned from preset |

Indexes:
- `ix_vital_field_def_clinic_id` (clinic_id)
- `uq_vital_field_def_clinic_key` UNIQUE (clinic_id, key) WHERE NOT is_deleted

### 2.3 `vital_schema_version`
Immutable snapshot of all active field definitions per clinic. Created on every schema change.

| Column | Type | Notes |
|--------|------|-------|
| clinic_id | UUID FK | |
| version_number | INTEGER | Monotonically increasing per clinic |
| definitions_snapshot | JSONB | Full definition array at time of change |
| change_summary | VARCHAR(500) | Human-readable description |
| created_by | UUID | |

Constraints: UNIQUE (clinic_id, version_number)

### 2.4 `visit_vitals`
Actual vitals records. Extends BaseEntity. Multiple records per visit allowed; `is_primary` marks canonical record.

| Column | Type | Notes |
|--------|------|-------|
| visit_id | UUID FK → visit.id | |
| schema_version | INTEGER | Version number at time of recording |
| values | JSONB | Map of field key → cleaned value |
| notes | TEXT | Optional free text |
| is_primary | BOOLEAN | First record auto-set to true |
| recorded_by | UUID FK → user.id | |
| recorded_at | TIMESTAMPTZ | |

Indexes:
- `ix_visit_vitals_values_gin` GIN on values (enables fast JSONB containment queries)
- `ix_visit_vitals_is_primary` (visit_id, is_primary) WHERE is_primary=true
- `ix_visit_vitals_visit_recorded` (visit_id, recorded_at)

## 3. Schema Evolution Rules

| Change | Behavior |
|--------|----------|
| Rename `key` | 400 — "Cannot rename key, create new field instead" |
| Change `data_type` | 400 — "Cannot change data_type, create new field instead" |
| Modify `label`, `unit`, `is_required`, `is_active`, range values | Creates new schema_version snapshot, applies change |
| Soft-delete field | Creates new schema_version, sets is_deleted=True, is_active=False |

## 4. Runtime Validator

`VitalValidator.validate(payload, definitions)`:
1. **REQUIRED check**: For each required field in definitions, raise REQUIRED error if missing from payload
2. **UNKNOWN check**: For each key in payload, raise UNKNOWN error if not in active definitions
3. **Type coercion**: Coerce value to declared data_type; raise INVALID on failure
4. **Range check**: For number/integer, validate min_value ≤ value ≤ max_value
5. Collects ALL errors before raising `VitalValidationError` (422 response)

## 5. Permissions

| Permission | Description | Admin | Doctor | Nurse |
|-----------|-------------|-------|--------|-------|
| vital.read | View definitions & vitals | ✓ | ✓ | ✓ |
| vital.write | Record vitals for a visit | ✓ | ✓ | ✓ |
| vital.delete | Delete vital record | ✓ | | ✓ |
| vital.manage | CRUD definitions | ✓ | | |

## 6. System Presets (5 specialties per BA §7.4)

| Specialty | Fields |
|-----------|--------|
| general | systolic_bp, diastolic_bp, pulse, temperature, weight, height, spo2 (7) |
| dental | systolic_bp, diastolic_bp, pulse, temperature (4) |
| pediatric | weight, height, head_circumference, temperature, pulse (5) |
| obstetric | systolic_bp, diastolic_bp, weight, fundal_height, fetal_heart_rate, gestational_age (6) |
| dermatology | systolic_bp, weight (2) |

## 7. Business Rules

- A visit can have multiple `visit_vitals` records (re-measurement). First record is auto-set `is_primary=True`.
- Old vitals always readable via stored `schema_version` integer even after definition changes.
- `warning_min/max` are informational only — backend does not enforce them.
- Field `key` must be snake_case alphanumeric. Validated at creation.
