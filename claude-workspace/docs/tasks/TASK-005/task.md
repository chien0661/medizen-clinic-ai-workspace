---
id: TASK-005
type: feature
title: Patient Management — CRUD + Guardian + Search + Merge Duplicates
status: IN_REVIEW
priority: High
assigned: code-review-agent
created: 2026-04-26
updated: 2026-04-28
branch: "feature/task-005-patients"
iteration: 1
tags: [patient, sprint-3]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#6-module-patients"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#4-module-patient--reception"
---

# TASK-005: Patient Management — CRUD + Guardian + Search + Merge Duplicates

## Description

Quản lý bệnh nhân: CRUD, search nhanh theo phone/name/patient_code (full-text + trigram), guardian relationship, merge 2 hồ sơ trùng (admin perm), undo merge trong 7 ngày, audit log mọi thao tác đọc.

## Requirements

- [ ] Migration `0003_create_patients.py` (patient + patient_relation)
- [ ] Helper `fn_next_patient_code(clinic_id)` sinh `BN0001`, `BN0002`...
- [ ] Indexes: `ix_patient_clinic_phone`, `gix_patient_name_search` (GIN unaccent), `gix_patient_name_trgm`, `uq_patient_clinic_code` (partial WHERE NOT is_deleted)
- [ ] Endpoints: CRUD + `GET /api/v1/patients/search?q=...&type=phone|name|code`
- [ ] `POST /api/v1/patients/{id}/guardians` — thêm guardian (patient_relation)
- [ ] `POST /api/v1/patients/merge` — body `{keep_id, drop_id}`, perm `patient.merge`
- [ ] Merge logic: reassign Visit/Prescription/Invoice của drop_id → keep_id, soft-delete drop_id, lưu mapping vào bảng `patient_merge_log`
- [ ] `POST /api/v1/patients/merge/{merge_id}/undo` — chỉ trong 7 ngày
- [ ] Phone NOT unique, name + DOB cũng không unique (cảnh báo nếu trùng nhưng không block)
- [ ] Audit log cho `patient.read` (async)

## Acceptance Criteria

- [ ] Search theo SĐT 10 chữ số trả < 100ms khi DB có 100k patient
- [ ] Search fuzzy theo tên (vd "nguyen vn an") match được "Nguyễn Văn An" nhờ unaccent + trgm
- [ ] Tạo guardian: parent (patient A) → child (patient B), `is_primary_contact=true`
- [ ] Merge: tất cả Visit của drop_id phải có patient_id mới sau merge (verify count + spot-check)
- [ ] Undo merge trong 7 ngày khôi phục đúng trạng thái cũ
- [ ] Sau 7 ngày, undo trả 410 Gone

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/patients/`

## Timestamps

- **Created**: 2026-04-26
- **Started**: 2026-04-28
- **Implementation Completed**: 2026-04-28

## Notes

DOB cho phép chỉ năm (`birth_year` int). Check constraint: phải có dob hoặc birth_year, nếu có cả 2 thì year phải khớp.

## Blockers

- TASK-002, TASK-004
