---
id: TASK-115
type: bug
title: "[Medium] Receptionist (chỉ visit.write) ghi/ghi đè exam lâm sàng + auto-start visit"
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-25
updated: 2026-07-25
branch: "fix/TASK-115-exam-rbac"
tags: [exam, rbac, security, medium, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (M-6)"
---

# TASK-115: [Medium] Exam RBAC — receptionist ghi exam lâm sàng (M-6)

**Nguồn:** E2E TASK-095, M-6.

- **Kỳ vọng:** Ghi nội dung khám lâm sàng cần capability/role lâm sàng (như vitals qua `vital.write`, /start & /complete qua require_role).
- **Thực tế:** `POST /visits/{id}/exam` chỉ gate `visit.write`, không kiểm exam/role lâm sàng → receptionist (chỉ visit.write) ghi/ghi đè exam VÀ auto-promote WAITING→IN_PROGRESS (vượt role gate của /start). recept có visit.write nhưng /exam-templates→403, vitals→403.
- **File:** `app/modules/exam_templates/api/routes.py`, `services/visit_exam_service.py`, tham chiếu gate của vitals/start.

## Acceptance Criteria
- [x] `POST /visits/{id}/exam` yêu cầu quyền/role lâm sàng phù hợp (nhất quán với vitals `vital.write` và /start require_role) → receptionist bị 403.
- [x] Role lâm sàng (doctor/nurse) vẫn ghi được (không hồi quy).
- [x] Integration test RBAC: recept→403, doctor→200.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

Documentation Completed: 2026-07-25
- Final spec: `docs/tasks/TASK-115/deliveries/final-specs/exam-rbac-fix.md`

## Blockers
Không.

## Implementation
Branch `fix/TASK-115-exam-rbac` (base `origin/dev` @ `85f70cc`), commit `bfc27ff`, pushed.
See `docs/tasks/TASK-115/handoff/implementation-to-review.md`.

## Testing
85/85 passed (`tests/integration/exam_templates` + `tests/integration/visits`)
on isolated stack `x115`, plus independent live-API verification with real
`recept_anh`/`dr_nguyen`/`nurse_lan` demo accounts confirming 403 (no
auto-start) / 200 (auto-start IN_PROGRESS) / 200 (auto-start IN_PROGRESS).
See `docs/tasks/TASK-115/deliveries/test-reports/test-report.md`.
