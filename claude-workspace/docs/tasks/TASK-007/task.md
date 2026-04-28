---
id: TASK-007
type: feature
title: Visit — Entity + State Machine + Visit Number Generation
status: DONE
priority: High
assigned: 
created: 2026-04-26
updated: 2026-04-28
branch: "feature/task-007-visits"
iteration: 2
tags: [visit, sprint-4]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#8-module-visits"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#6-module-visit"
---

# TASK-007: Visit — Entity + State Machine + Visit Number Generation

## Description

Visit là entity trung tâm kết nối Patient-Appointment-Doctor-Vitals-Service-Prescription-Invoice. State machine: WAITING → IN_PROGRESS → AWAITING_PAYMENT → COMPLETED (+ CANCELLED ở mọi state trừ COMPLETED). Sinh visit_number `YYYYMMDD-NNN` reset hàng ngày per clinic.

## Requirements

- [ ] Migration `0005_create_visits.py` (visit table)
- [ ] Helper `fn_next_visit_number(clinic_id, date)` dùng PostgreSQL sequence per (clinic, date)
- [ ] Endpoints: CRUD + actions
  - `POST /api/v1/visits` (tạo walk-in)
  - `POST /api/v1/visits/{id}/start` (BS nhận ca: WAITING → IN_PROGRESS, set doctor_id = current user)
  - `POST /api/v1/visits/{id}/complete` (BS hoàn tất: IN_PROGRESS → AWAITING_PAYMENT)
  - `POST /api/v1/visits/{id}/cancel` (kèm reason)
  - `POST /api/v1/visits/call-next` (BS gọi visit tiếp theo theo priority logic)
- [ ] State machine enforcement: chỉ allow transition hợp lệ, return 409 nếu invalid
- [ ] Call-next logic: ưu tiên visit có `assigned_doctor_id = current_user`, sau đó null, sau cùng assigned người khác
- [ ] Indexes: `ix_visit_clinic_status_priority` cho queue query
- [ ] View `v_active_queue` SQL theo §14 BA

## Acceptance Criteria

- [ ] Visit number unique trong (clinic, date), format `20260426-001`
- [ ] State transition: WAITING → COMPLETED trực tiếp bị reject (409)
- [ ] COMPLETED không revert được
- [ ] CANCELLED ở COMPLETED bị reject
- [ ] Call-next với 2 BS đồng thời không gây race condition (test với SELECT FOR UPDATE)
- [ ] Performance: query queue 50 visit < 50ms

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation (Completed: 2026-04-28)

## Related Files

- **Code**: `clinic-cms/app/modules/visits/`

## Timestamps

- **Created**: 2026-04-26
- **Started**: 2026-04-27
- **Implementation Completed**: 2026-04-27
- **Review (1st pass)**: 2026-04-27 — CHANGES_REQUESTED. 0 CRIT, 2 MAJ (mark-paid/cancel use overly-broad visit.write instead of seeded visit.cancel/payment.receive; concurrent call-next test accepts 1×200+1×404 which doesn't prove the AC), 3 MIN. Migration round-trip clean, coverage 87 %, lint clean, 81/81 tests pass — see `handoff/review-report.md` and `handoff/review-to-implementation.md` for the targeted fix list.
- **Fix iteration 2**: 2026-04-27 — All 2 MAJ + 2 of 3 MIN fixed. m3 (ORJSON deprecation) deferred as pre-existing in codebase. 83/83 tests pass, coverage 87%, lint clean. Re-submitted for review.
- **Review (2nd pass)**: 2026-04-27 — APPROVED. All 4 in-scope fixes RESOLVED (M1 narrower permissions + 2 new gating tests; M2 strict 200/200 distinct-IDs assertion + DB-level IN_PROGRESS verification; m1 docstring; m2 assert_can_transition symmetry). m3 ORJSON deferral verified pre-existing (introduced in TASK-001 commit `6bf2c53`). Build numbers match handoff: 83/83 pass, 87% coverage (317/41), ruff clean. M2 stability 5/5 runs. Handed off to Test Agent — see `handoff/review-to-test.md`.
- **Testing Completed**: 2026-04-28 — PASSED. 33 new tests added (perf/RLS/lifecycle/concurrent/negative). Total 117 tests pass (116 non-perf + 1 perf). AC #6 p95=13.6ms < 50ms. RLS verified via cms_app role. 5-way concurrent call-next SKIP LOCKED verified. Coverage 87%. 1 bug documented: BUG-001 (ghost patient_id → FK IntegrityError not mapped to 404). Handed off to Documentation Agent.
- **Documentation Completed**: 2026-04-28 — 3 deliverables delivered: visits-functional-design.md (Vietnamese, 700+ lines covering all sections), visits-api.md (10 endpoints with curl examples), visits-ddl.md (complete DDL, RLS, indexes, forward/downgrade scripts). All files commit-ready.

## Notes

Sửa sai sau COMPLETED phải void invoice + tạo entry điều chỉnh, không revert visit state.

## Blockers

- TASK-005
