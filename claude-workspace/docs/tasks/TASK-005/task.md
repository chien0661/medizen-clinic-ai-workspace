---
id: TASK-005
type: feature
title: Patient Management — CRUD + Guardian + Search + Merge Duplicates
status: IN_PROGRESS
priority: High
assigned: code-implementation-agent
created: 2026-04-26
updated: 2026-04-27
branch: "feature/task-005-patients"
iteration: 3
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
- **Review (1st pass)**: 2026-04-27 — CHANGES_REQUESTED (2 CRITICAL, 6 MAJOR, 3 MINOR). See `handoff/review-report.md` and `handoff/review-to-implementation.md`.
- **Fix iteration 2**: 2026-04-27 — All 2 CRIT + 6 MAJ + 2 MIN fixed. (C1) Added `immutable_unaccent()` SQL function + updated GIN index expression and search queries; (C2) Rewrote integration tests as real DB e2e against `app.main:app` (15 scenarios); (M1) Fresh `AsyncSessionLocal()` in `audit_patient_read`; (M2) Trigram GIN index on phone + similarity operator; (M3) Switched to `plainto_tsquery`; (M4) Per-row reassignment manifest in `source_patient_data['reassigned_refs']`; (M5) `fn_next_patient_code` uses numeric MAX over ALL rows (incl. soft-deleted); (M6) All 11 ruff violations fixed. Minor: (m1) `fn_next_patient_code` now uses integer MAX (no more lexical ordering bug); (m2) `test_captures_all_columns` converted to `async`. Migration round-trip clean. 79/79 tests pass (61 unit + 18 integration). Coverage 95% on patients module. Ruff exit 0.
- **Review (2nd pass)**: 2026-04-27 — APPROVED. All 2 CRIT + 6 MAJ + 2 MIN verified RESOLVED per-commit (`adea8b6` C1/M2-mig/M5/m1; `e2e06cb` M1/M2-svc/M3; `6aefd35` M4; `b384e97` M6/m2; `d9c0546` C2). m3 deferred per iter-1 guidance. Migration round-trip clean. 79/79 patient tests pass, 95% coverage, ruff clean. No new findings. Handoff: `handoff/review-to-test.md`. Status → IN_TESTING.
- **Testing (Phase 3)**: 2026-04-27 — FAILED. 4 bugs found during fuzz/negative testing: (BUG-001) null byte in search q → 500; (BUG-002) future DOB accepted → 201; (BUG-003) self-merge allowed → 201; (BUG-004) cross-clinic undo merge → 200 (Critical). 113/117 non-perf tests pass. Performance: phone p95=46.9ms (AC1 PASS). RLS verified. Coverage 95%. See `deliveries/test-reports/test-report.md`. Status → IN_PROGRESS (iter 3).

## Notes

DOB cho phép chỉ năm (`birth_year` int). Check constraint: phải có dob hoặc birth_year, nếu có cả 2 thì year phải khớp.

## Blockers

- TASK-002, TASK-004
