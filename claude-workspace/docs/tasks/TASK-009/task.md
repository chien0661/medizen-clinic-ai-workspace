---
id: TASK-009
type: feature
title: Vitals Dynamic Form (3 Tables + 5 Specialty Presets + Runtime Validation)
status: TODO
priority: High
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [vitals, dynamic-form, sprint-5]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#9-module-vitals-dynamic-form"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#7-module-vitals-dynamic-form"
---

# TASK-009: Vitals Dynamic Form (3 Tables + 5 Specialty Presets + Runtime Validation)

## Description

Vitals form động per clinic: 3 bảng `vital_field_definition` (defs hiện hành), `vital_schema_version` (snapshot mỗi version), `visit_vitals` (record với schema_version + JSONB values). Runtime validator dựa vào definitions. 5 preset (general/dental/pediatric/obstetric/dermatology). Schema evolution rules theo §7.3 BA.

## Requirements

- [ ] Migration `0006_create_vitals_dynamic.py` (4 bảng kể cả `system_vital_preset`)
- [ ] Seed `system_vital_preset` cho 5 specialty với fields đúng §7.4 BA
- [ ] Endpoints:
  - `GET/POST/PATCH/DELETE /api/v1/vitals/definitions` (admin only)
  - `GET /api/v1/vitals/definitions/version/{n}`
  - `POST /api/v1/visits/{id}/vitals` (nurse/doctor)
  - `GET /api/v1/visits/{id}/vitals`
- [ ] Runtime validator `validate_vitals_payload(payload, clinic_id)` — type check + range check + required check
- [ ] Schema evolution rule enforcement:
  - Sửa key/data_type → reject 400
  - Sửa label/unit/range → tạo version mới
  - Disable/delete field → tạo version mới + soft-delete
- [ ] GIN index trên `visit_vitals.values` JSONB
- [ ] UNIQUE (clinic_id, key) WHERE NOT is_deleted cho `vital_field_definition`
- [ ] Visit có thể có nhiều `visit_vitals` (đo lại); flag `is_primary` cho 1 record

## Acceptance Criteria

- [ ] Onboard clinic specialty=pediatric → vital_field_definition có 5 fields chuẩn (weight, height, head_circumference, temperature, pulse)
- [ ] POST vitals payload `{"systolic_bp": 120, "diastolic_bp": 80}` cho clinic general → 201
- [ ] POST với key không tồn tại trong definition → 400 với detail "Unknown field: xyz"
- [ ] Sửa `is_required` của field tồn tại → tạo version mới, dữ liệu cũ vẫn xem được
- [ ] Sửa `key` của field → 400 với detail "Cannot rename key, create new field instead"
- [ ] Query vitals trend `WHERE values->>'systolic_bp' > '140'` dùng GIN index (verify EXPLAIN)

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/vitals/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Frontend cảnh báo bất thường (warning_min/max) — không block lưu, chỉ visual. Backend không kiểm tra cảnh báo.

## Blockers

- TASK-007
