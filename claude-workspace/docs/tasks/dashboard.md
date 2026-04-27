# Task Tracking Dashboard

**Last Updated**: 2026-04-27 (TASK-016 → DOCUMENTING by test-agent, 73/73 tests PASS)

> **⚠️ Note**: This file is auto-generated. Do not edit manually.
> To update task status, use: `/task-status TASK-ID STATUS`
> To create new tasks, use: `/task-create TASK-ID "Title" Priority Type`

---

## Statistics

| Metric | Count |
|--------|-------|
| **Total Tasks** | 25 |
| TODO | 20 |
| IN_PROGRESS | 0 |
| IN_REVIEW | 2 |
| IN_TESTING | 1 |
| DOCUMENTING | 1 |
| DONE | 1 |

### By Priority

| Priority | Count |
|----------|-------|
| High | 16 |
| Medium | 9 |

### By Track

| Track | Tasks | Count |
|-------|-------|-------|
| Backend | TASK-001..015 | 15 |
| FE Foundation | TASK-016, 017 | 2 |
| FE Modules | TASK-018..024 | 7 |
| Integration & E2E | TASK-025 | 1 |

---

## Backend Roadmap (TASK-001 → TASK-015)

| Sprint | Task | Title | Priority | Status | Blockers |
|--------|------|-------|----------|--------|----------|
| 0-1 | [TASK-001](TASK-001/task.md) | Foundation — Project Skeleton, Docker Compose, Base Models, Alembic | High | DONE | — |
| 1 | [TASK-002](TASK-002/task.md) | Tenancy + RLS Policies + Audit Log Infrastructure | High | IN_REVIEW | — |
| 2 | [TASK-003](TASK-003/task.md) | Auth — JWT Login/Refresh + Password Reset + Account Lockout | High | IN_TESTING | — |
| 2 | [TASK-004](TASK-004/task.md) | Users + RBAC (Role + Permission + Multi-Role) | High | IN_REVIEW | — |
| 3 | [TASK-005](TASK-005/task.md) | Patient Management — CRUD + Guardian + Search + Merge | High | TODO | TASK-002, 004 |
| 3 | [TASK-006](TASK-006/task.md) | Clinic Settings + Tenant Onboarding Wizard | Medium | TODO | TASK-004, 005 |
| 4 | [TASK-007](TASK-007/task.md) | Visit — Entity + State Machine + Visit Number | High | TODO | TASK-005 |
| 5 | [TASK-008](TASK-008/task.md) | Appointment + Queue (Capacity + Smart Walk-in) | High | TODO | TASK-007, 014 |
| 5 | [TASK-009](TASK-009/task.md) | Vitals Dynamic Form (3 Tables + 5 Presets) | High | TODO | TASK-007 |
| 6 | [TASK-010](TASK-010/task.md) | Service Catalog + VisitService | Medium | TODO | TASK-007 |
| 7 | [TASK-011](TASK-011/task.md) | Medicine Catalog + Prescription (In-House/External) | High | TODO | TASK-007, 012 |
| 8-9 | [TASK-012](TASK-012/task.md) | Inventory + Batch + FEFO + Pharmacy Dispense | High | TODO | TASK-006 |
| 10-11 | [TASK-013](TASK-013/task.md) | Billing — Invoice + Multi-Payment + Discount + Void/Refund | High | TODO | TASK-010, 011 |
| 12-13 | [TASK-014](TASK-014/task.md) | HR — Shift + Recurring Schedule + Attendance + Leave | Medium | TODO | TASK-004 |
| 14 | [TASK-015](TASK-015/task.md) | Reporting + In-App Notifications + Background Jobs | Medium | TODO | TASK-013, 012, 008 |

## Frontend Roadmap (TASK-016 → TASK-024)

| Sprint | Task | Title | Priority | Status | Blockers |
|--------|------|-------|----------|--------|----------|
| 15 | [TASK-016](TASK-016/task.md) | Tauri Foundation — Shell + Offline Sync Engine + Hardware | High | DOCUMENTING | TASK-001 |
| 15 | [TASK-017](TASK-017/task.md) | FE — Auth + App Shell + Design System + i18n (vi/en) | High | TODO | TASK-003, 016 |
| 15 | [TASK-018](TASK-018/task.md) | FE — Reception (Patient + Walk-in + Appointment + Queue) | High | TODO | TASK-017, 005, 007, 008 |
| 15 | [TASK-019](TASK-019/task.md) | FE — Doctor (Visit + Vitals + Service + Prescription) | High | TODO | TASK-017, 007, 009, 010, 011, 012 |
| 15 | [TASK-020](TASK-020/task.md) | FE — Pharmacy (Dispense + Inventory + Stock Adjustment) | High | TODO | TASK-017, 011, 012 |
| 15 | [TASK-021](TASK-021/task.md) | FE — Billing (Invoice + Payment + POS Print) | High | TODO | TASK-017, 013 |
| 16 | [TASK-022](TASK-022/task.md) | FE — HR (Shift Calendar + Attendance + Leave) | Medium | TODO | TASK-017, 014 |
| 16 | [TASK-023](TASK-023/task.md) | FE — Admin (Users + Roles + Settings + Onboarding Wizard) | Medium | TODO | TASK-017, 004, 006, 009 |
| 16 | [TASK-024](TASK-024/task.md) | FE — Dashboard + Reports + Notifications + Real-time | Medium | TODO | TASK-017, 015 |

## Final — Integration & Acceptance

| Sprint | Task | Title | Priority | Status | Blockers |
|--------|------|-------|----------|--------|----------|
| 16+ | [TASK-025](TASK-025/task.md) | System Integration + E2E Test Suite (Playwright + Smoke + Regression + Perf) | High | TODO | ALL TASK-001..024 |

---

## Critical Path

```
TASK-001 (BE Foundation)
    ├──→ TASK-002 (RLS/Audit)
    │       └→ TASK-003 (Auth)
    │           └→ TASK-004 (RBAC)
    │               ├→ TASK-005 (Patient)
    │               │   └→ TASK-007 (Visit) ──┬→ TASK-009 (Vitals)
    │               │                          ├→ TASK-010 (Services)
    │               │                          └→ TASK-008 (Appointment)
    │               ├→ TASK-006 (Settings)
    │               │   └→ TASK-012 (Inventory)
    │               │       └→ TASK-011 (Prescription)
    │               │           └→ TASK-013 (Billing)
    │               └→ TASK-014 (HR)
    │
    └──→ TASK-016 (Tauri Foundation)
            └→ TASK-017 (FE Auth + Shell)
                ├→ TASK-018 (FE Reception)
                ├→ TASK-019 (FE Doctor)
                ├→ TASK-020 (FE Pharmacy)
                ├→ TASK-021 (FE Billing)
                ├→ TASK-022 (FE HR)
                ├→ TASK-023 (FE Admin)
                └→ TASK-024 (FE Dashboard/Reports)
                                    │
                                    ▼
                            TASK-015 (Reports/Notif/Jobs BE)
                                    │
                                    ▼
                            TASK-025 (Integration + E2E)
```

---

## Phase Grouping

| Phase | Tasks | Theme | Sprint |
|-------|-------|-------|--------|
| **Phase 0 — BE Foundation** | 001, 002 | Multi-tenant skeleton, RLS, audit | 0-1 |
| **Phase 1 — Identity** | 003, 004 | Auth + RBAC | 2 |
| **Phase 2 — Patient & Onboarding** | 005, 006 | Patient mgmt + clinic setup | 3 |
| **Phase 3 — Clinical Workflow BE** | 007, 008, 009, 010 | Visit + Appointment + Vitals + Services | 4-6 |
| **Phase 4 — Inventory & Prescription BE** | 011, 012 | Medicine + FEFO + Pharmacy | 7-9 |
| **Phase 5 — Billing & Operations BE** | 013, 014, 015 | Invoice + HR + Reports/Jobs | 10-14 |
| **Phase 6 — FE Foundation** | 016, 017 | Tauri shell + sync + design system | 15 |
| **Phase 7 — FE Modules** | 018, 019, 020, 021, 022, 023, 024 | UI per module (parallel after 017) | 15-16 |
| **Phase 8 — Integration** | 025 | E2E + smoke + regression + perf + pilot | 16+ |

---

## Parallelization Strategy

After **TASK-017** (FE foundation) merges, **TASK-018..024** can run in parallel by 2-3 FE devs. Each FE module task only blocks on its corresponding BE task being IN_REVIEW or later (with API contract stable).

**Suggested team allocation (3 BE + 2 FE devs):**
- BE Track A: 001 → 002 → 003 → 004 → 005 → 007 → 009
- BE Track B: 006 → 012 → 011 → 013
- BE Track C: 008 → 010 → 014 → 015
- FE Track 1: 016 → 017 → 018 → 019 → 024
- FE Track 2: 020 → 021 → 022 → 023

**Estimated**: 16-20 weeks (4-5 months) with 5 devs in parallel; 32 weeks with 1 dev sequential.

---

**💡 Tip**: Click on any task ID to view full details.
