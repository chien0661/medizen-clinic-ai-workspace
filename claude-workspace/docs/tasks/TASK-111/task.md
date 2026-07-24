---
id: TASK-111
type: bug
title: "[Medium] Hủy lịch đã check-in để lại Visit mồ côi ở trạng thái WAITING"
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-25
updated: 2026-07-25
branch: "fix/TASK-111-appt-cancel-visit-cascade"
tags: [appointments, visits, data-integrity, cross-module, medium, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (M-2)"
---

# TASK-111: [Medium] Hủy lịch checked-in → Visit mồ côi WAITING (M-2)

**Nguồn:** E2E TASK-095, M-2.

- **Kỳ vọng:** Hủy lịch đã check-in nên hủy/void Visit đã tạo, hoặc chặn transition.
- **Thực tế:** Lịch → cancelled nhưng Visit vẫn WAITING, mồ côi trong hàng đợi. `cancel_appointment` không đụng Visit.
- **Repro:** appt confirm→check-in tạo visit (WAITING); cancel appt → 200 cancelled; visit vẫn WAITING.
- **File:** `app/modules/appointments/services/appointment_service.py:252-266`, `state_machine.py:16-23`

## Acceptance Criteria
- [x] Hủy lịch đã check-in → Visit liên quan được hủy (hoặc chặn hủy lịch nếu visit đã bắt đầu khám) — quyết định + ghi rõ.
- [x] Không còn visit mồ côi trong hàng đợi sau khi hủy lịch.
- [x] Integration test: check-in→cancel → visit không còn WAITING.

## Decision (implementation)
**Cascade, not blanket block.** `cancel_appointment` now cascade-cancels the
linked Visit (any non-COMPLETED/CANCELLED state, including IN_PROGRESS) via
the existing `visit_service.transition_to_cancel`. That function already
enforces its own guard rails — it raises `BusinessRuleError` (422) if money
has been collected or medicines already dispensed — so the appointment
cancel is naturally blocked in exactly the cases where cascading would be
unsafe, without a separate hardcoded IN_PROGRESS block. See docstring on
`cancel_appointment` in
`app/modules/appointments/services/appointment_service.py`.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Documentation Completed
Documentation Completed: 2026-07-25 — Final specs in `docs/tasks/TASK-111/deliveries/final-specs/appointment-cancel-visit-cascade-fix.md`

## Testing — 2026-07-25 (PASSED -> DOCUMENTING)
89/89 integration tests passed (`tests/integration/appointments` +
`tests/integration/visits`) in isolated stack `w111`. Cascade verified for
WAITING and IN_PROGRESS visits; no-visit cancel regression OK. Money/dispensed
guard verified by code inspection (blocks correctly; HTTP 400 not 422 — see
test report). See `handoff/test-to-documentation.md` and
`deliveries/test-reports/test-report.md`.

## Blockers
Không.
