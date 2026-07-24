---
id: TASK-109
type: bug
title: "[Medium] GET /patients/{id} không lọc clinic_id → 500 oracle + IDOR liên tenant tiềm ẩn"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-24
updated: 2026-07-24
branch: "fix/TASK-109-patient-get-tenant-filter"
tags: [patients, security, idor, multi-tenant, medium, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (M-19)"
---

# TASK-109: [Medium→cao] GET /patients/{id} thiếu lọc clinic_id (M-19)

**Nguồn:** E2E TASK-095, M-19. Độc lập với quyết định RLS (fix ở tầng app), nhưng cùng chủ đề cách ly tenant (xem C-5/C-7 = TASK-100/102).

- **Kỳ vọng:** patient của clinic khác → 404 (như visits/prescriptions đã làm).
- **Thực tế:** `get_patient` (`patient_service.py:177` `db.get(Patient, patient_id)`) KHÔNG lọc `clinic_id`, chỉ dựa RLS (đã bị bypass — C-7). Row liên tenant bị load; `full_name` (EncryptedString) giải mã bằng DEK caller → `InvalidTag` → **500**. Tạo oracle 404-vs-500 + IDOR full-PII tiềm ẩn (cột plaintext như patient_code/dob/gender là bề mặt lộ; hiện chỉ bị che vì decrypt full_name ném trước — không phải do authz).
- **File:** `app/modules/patients/services/patient_service.py`, `api/routes.py`

## Acceptance Criteria
- [x] `get_patient` lọc `clinic_id` ở tầng app → patient clinic khác trả 404 (không 500, không lộ PII).
- [x] Không hồi quy GET own-clinic (200).
- [x] Integration test cross-tenant (foreign → 404, own → 200).

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Blockers
Không. (Fix tầng app độc lập; RLS tổng thể vẫn theo TASK-102.)

## Implementation (2026-07-24)

Branch `fix/TASK-109-patient-get-tenant-filter` (base `origin/dev` @ 649bde4), pushed.
Commit `a8b0f5f` — `fix(patients): scope get_patient by clinic_id so foreign patients
return 404 (TASK-109)`.

`get_patient` now filters `Patient.id == patient_id AND Patient.clinic_id == clinic_id
AND is_deleted.is_(False)` via `select()` instead of unscoped `db.get()`, mirroring
`visit_service._get_visit_or_404`. `clinic_id` sourced from `_require_clinic_id()`
(request-scoped, same as every other patients route). Cascaded to `update_patient` /
`soft_delete_patient`, which call `get_patient` internally and had the identical flaw.

Tests: unit 62/62 pass, integration patients 60/63 pass (3 pre-existing failures in
`merge_service`/phone-search, verified identical on unmodified `origin/dev` baseline —
unrelated to this fix, out of scope). ruff/mypy: 0 new. Full detail in
`handoff/implementation-to-review.md`.

## Testing Completed: 2026-07-24

Independently re-verified in a fresh isolated stack `v109` (api 9968 / pg
5468 / redis 6450), migrated to head `0067` + superadmin seed, worktree
`_fix109-be` @ `a8b0f5f`. `pytest -q --tb=short tests/integration/patients
tests/unit/patients` → **122/125 passed** (3 known-baseline DEK/RLS
merge/phone-search flakes, same 3 named in `handoff/review-to-test.md`, not
caused by this fix). Key assertions confirmed: cross-tenant GET → 404 (no
PII, no 500); own-clinic GET → 200; soft-deleted → 404; cross-tenant
PATCH/DELETE → 404 (cascade). See
`deliveries/test-reports/test-report.md`.

## Documentation Completed: 2026-07-24

Final spec document: `deliveries/final-specs/patient-get-tenant-scoping-fix.md`.
Technical overview of M-19 (clinic_id scoping on patient GET) fix, including security impact analysis and follow-up recommendations (guardian_service, merge_service still unscoped).
