---
id: TASK-041
type: refactor
title: BE branch consolidation — verified already done on main (no merge work performed)
status: DONE
completed: 2026-05-01
priority: High
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
branch: ""
jira_key: ""
tags: [be, modules, missing, scope-clarification, foundation]
affected-repos: [clinic-cms]
refs:
  detail_design: "docs/design/medizen-modern/MENU_AND_SCREENS.md"
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "../TASK-032/handoff/be-audit-report.md"
    - "../TASK-032/deliveries/final-specs/audit-report.md"
    - "../../../docs/clinic_management_function_list.md"
---

# TASK-041: BE branch consolidation

## Description

**Correction (2026-05-01)**: Initial TASK-032 BE audit ran against branch `feature/task-006-settings` and reported 6 modules "missing". Investigation confirmed the modules **DO exist** on later feature branches:

```
feature/task-010-services
feature/task-011-prescriptions
feature/task-012-inventory
feature/task-013-billing
feature/task-014-hr-schedule
feature/task-015-reports  ← has: billing, inventory, notifications, prescriptions, pharmacy, reports (verified via git ls-tree)
```

This task is **branch consolidation + integration testing**, not fresh build. Goal: produce a unified main branch with all TASK-001..015 modules merged, before TASK-033 multi-clinic refactor runs on top.

## Requirements

### Pre-flight

- [x] **P.1** Verify modules exist on feature branches — CONFIRMED via `git ls-tree feature/task-015-reports app/modules/`
- [ ] **P.2** Decide merge strategy with user: (a) merge feature branches sequentially to a new `main` baseline first, then TASK-033 refactor; (b) refactor each feature branch for multi-clinic individually then merge; (c) cherry-pick by module
- [ ] **P.3** Identify merge conflicts ahead of time (run dry-merge per branch into target)

### Original 6-module fresh-build requirements — DESCOPED
The detailed module-by-module schema/endpoint requirements below are kept for reference (in case any module needs partial refactor during merge), but the bulk of the work is now merge + integration test, NOT fresh build.

### Modules (kept as reference during merge — verify each merged module aligns with v1.3 fn list)

#### Module 1 — `services` (Dịch vụ KCB)

- [ ] Schema: `service(id, clinic_id, code, name, category, price, bhyt_price, is_active)`, `service_group`
- [ ] CRUD endpoints `/api/v1/services`
- [ ] Permission: `service:read`, `service:write`

#### Module 2 — `medicines` (Thuốc)

- [ ] Schema: `medicine(id, clinic_id, code, name, active_ingredient, unit, form, route, manufacturer, has_bhyt, bhyt_price, retail_price, min_stock_level, ...)`
- [ ] CRUD endpoints `/api/v1/medicines`
- [ ] `GET /medicines/{id}/stock-summary` for RX-016 (TASK-042)
- [ ] Permissions

#### Module 3 — `inventory` (Kho thuốc)

- [ ] Schema: `inventory_lot(id, medicine_id, lot_number, expiry_date, quantity, cost_price)`, `stock_movement(id, lot_id, type, quantity, reason, ref_id, created_by)`, `purchase_order`, `stocktake_session`, `inventory_disposal`
- [ ] FEFO (First Expire First Out) query helper
- [ ] Endpoints: `POST /inventory/po`, `POST /inventory/stocktake` (3-step state machine), `GET /inventory/expired?days=30|60|90`, `POST /inventory/expired/disposal`
- [ ] Permissions

#### Module 4 — `prescriptions` (Đơn thuốc)

- [ ] Schema: `prescription(id, visit_id, doctor_id, ...)`, `prescription_item(id, prescription_id, medicine_id, quantity, dosage, instructions)`, `dispense(id, prescription_id, dispensed_by, dispensed_at)`
- [ ] Endpoints: CRUD + dispense flow + substitute suggestion
- [ ] Stock decrement on dispense via `stock_movement`
- [ ] Permissions

#### Module 5 — `billing` (Hoá đơn + thanh toán)

- [ ] Schema: `invoice(id, clinic_id, patient_id, visit_id, total, paid, status, ...)`, `invoice_line(id, invoice_id, type, ref_id, qty, price, bhyt_amount, patient_amount)`, `payment(id, invoice_id, method, amount, paid_at)`, `account_receivable` (denormalized for AR aging)
- [ ] Endpoints: `POST /invoices`, `GET /invoices`, `POST /invoices/{id}/payments`
- [ ] Permissions + SoD (TASK-035 — payment approval)

#### Module 6 — `notifications`

- [ ] Schema: `notification(id, user_id, type, severity, title, body, link, read_at, created_at)`, `notification_subscription` (per-user channel prefs)
- [ ] Endpoints: `GET /notifications?type=&date=&unread=&page=`, `POST /notifications/mark-read` (bulk), `POST /notifications/mark-all-read`
- [ ] Arq jobs: visit-completion notify, low-stock alert, subscription-expiring alert
- [ ] Permissions

#### Module 7 — `reports`

- [ ] Endpoints: `GET /reports/ar-aging?clinic_id=&as_of=` (buckets + per-patient), `GET /reports/revenue`, `GET /reports/inventory`, `GET /reports/doctor-performance`, `GET /reports/visit-volume`, `GET /reports/prescriptions`, `GET /reports/bhyt/*` (gated by TASK-034)
- [ ] Read-only — query layer over existing tables
- [ ] Permissions

### Tests

- [ ] **T.1** Per-module CRUD test
- [ ] **T.2** AR Aging buckets calculation test (fixture: invoices with mixed ages)
- [ ] **T.3** FEFO query test (lots with mixed expiry dates)
- [ ] **T.4** Stocktake 3-step state machine test
- [ ] **T.5** Notification fan-out (low-stock alert) test

## Acceptance Criteria

- [ ] All 7 modules listed exist under `app/modules/`
- [ ] Migrations clean apply
- [ ] All endpoints documented in OpenAPI
- [ ] Permissions seeded
- [ ] BE tests 100% pass
- [ ] No regressions on existing modules

## Dependencies

- Blocked by: TASK-033 (multi-clinic foundation — every new module needs to respect tenant identity)
- Blocks: TASK-040 (AR Aging, Notifications, Pharmacy screens), TASK-042 (RX-016 needs medicines + inventory), TASK-036 (Cmd+K /thuoc /inv modes), TASK-034 (BHYT consumers)

## Effort

**Medium** (2-5 days for branch consolidation + integration testing). Originally estimated as Very Large under fresh-build assumption — descoped after verification.

## Risk

MEDIUM (merge conflicts, schema migration order, alembic version conflicts between feature branches). LOW for individual module functionality (already implemented + tested per their original tasks).

**Stop-and-ask before**:
- Picking merge strategy (sequential into main vs refactor-then-merge vs cherry-pick)
- Resolving any non-trivial merge conflict — bring to user
- Squashing alembic migrations or renaming version files

## Notes

- Discovery via TASK-032 BE audit B.3, B.7, B.8, B.9 + cross-cutting #1.
- This is the largest single sub-task — consider splitting per-module if PM confirms fresh build.
- Reference function list v1.3: MED-001..016, INV-001..010, BILL-001..014, NOTI-001..007, REP-001..010.
