---
id: TASK-026
type: debt
title: FE integration audit — replace remaining mocks with real BE + retest
status: DONE
priority: High
assigned: 
created: 2026-04-29
updated: 2026-04-29
branch: ""
jira_key: ""
tags: [frontend, integration, cleanup, post-v1]
affected-repos: [clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "../../../../clinic-cms-workspace/docs/tasks/TASK-015/deliveries/api-specs/reports-api.md"
    - "../../../../clinic-cms-workspace/docs/tasks/TASK-013/deliveries/api-specs/billing-api.md"
    - "../../../../clinic-cms-workspace/docs/tasks/TASK-011/deliveries/api-specs/prescriptions-api.md"
    - "../../../../clinic-cms-workspace/docs/tasks/TASK-012/deliveries/api-specs/inventory-pharmacy-api.md"
    - "../../../../clinic-cms-workspace/docs/tasks/TASK-009/deliveries/api-specs/vitals-api.md"
    - "../../../../clinic-cms-workspace/docs/tasks/TASK-006/deliveries/api-specs/admin-api.md"
---

# TASK-026: FE integration audit — replace remaining mocks with real BE + retest

## Description

TASK-016..024 (FE features) được code song song với BE đang dev. Nhiều FE module dùng stub data ở `apiClient` layer vì BE chưa deploy demo lúc đó. Sau khi BE main đã có toàn bộ TASK-006..015 merged, cần:

1. Rà soát từng FE module file `src/modules/*/api.ts`, identify chỗ nào vẫn dùng `STUB_*` constants, `IS_STUB` flags, hoặc inline mock data.
2. Replace stub bodies với real `api.get/post/patch/delete()` calls dùng `apiClient`.
3. Map BE response shape (Decimal → number, pivot rows, etc.) qua adapter layer nếu cần.
4. Remove "Beta" banners + i18n keys liên quan trên page UI.
5. Update test mocks để match real BE shape; chạy lại `npm test`, `npx tsc --noEmit`, `npm run lint`.
6. Manual smoke: login DEMO/admin/Demo@1234 → click qua tất cả page (Dashboard, Reception, Doctor, Pharmacy, Billing, Reports, Admin) → verify data thật từ BE.

## Requirements

- [ ] Rà soát `src/modules/{admin,billing,dashboard,doctor,notifications,pharmacy,reports}/api.ts`
- [ ] Flip `IS_STUB = true` → `false` (pharmacy/api.ts) hoặc remove inline stub data
- [ ] Replace stub function bodies với real `api.get/post/patch/delete()` calls
- [ ] Adapter layer cho Decimal-as-string (revenue/inventory) → number
- [ ] Pivot logic cho visit-volume rows (status × period)
- [ ] Remove "Beta" UI banners + tương ứng i18n keys
- [ ] Update component test mocks để match real BE shape
- [ ] Tests pass 100% (`npm test`, `tsc 0`, `lint 0`)
- [ ] Manual smoke test 7 module qua FE login DEMO/admin/Demo@1234
- [ ] Document graceful handling cho 3 known BE bugs (BUG-001/002/003 từ TASK-025)

## Acceptance Criteria

- [ ] `grep -rn "IS_STUB\|STUB_\|@stub\|\\[STUB" src/modules/ src/pages/` returns 0 results (hoặc chỉ comments giải thích, không có active code)
- [ ] `grep -rn "Beta\|betaBadge\|betaNote" src/pages/ src/components/` returns 0 results
- [ ] FE login + dashboard render với real BE data (port 8001, DB cms_demo)
- [ ] Reports/Inventory page hiện 17 low-stock items thật + 5 expired batches (đã verify)
- [ ] Doctor consultation page: vitals form load real definitions từ TASK-009 BE
- [ ] Admin/Medicines page: list real medicines, CSV/Excel import works
- [ ] Pharmacy pages: pending dispense + inventory load real từ TASK-012 BE
- [ ] Billing pages: invoice list + payment work real từ TASK-013 BE
- [ ] Notifications panel: real notifications từ TASK-015 BE (poll 30s)
- [ ] BUG-001 (services 500 Decimal): handled via try/catch + error toast
- [ ] BUG-002 (vitals 400 no defs): inline help "Chưa cấu hình schema vitals"
- [ ] BUG-003 (prescriptions GET 405): empty state hoặc dùng list endpoint thay thế
- [ ] All tests pass: `npm test` 530+/530+, `tsc` 0, `lint` 0

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Input Specs**: TASK-006/009/011/012/013/015 deliveries/api-specs/
- **Code**: `clinic-cms-web/src/modules/*/api.ts`, `src/pages/*/`, `src/components/`
- **Tests**: `clinic-cms-web/src/tests/`
- **Handoffs**: `docs/tasks/TASK-026/handoff/`
- **Test Report**: `docs/tasks/TASK-026/deliveries/test-reports/test-report.md`
- **Final Specs**: `docs/tasks/TASK-026/deliveries/final-specs/integration-audit-report.md`

## Timestamps

- **Created**: 2026-04-29
- **Completed**: 2026-04-29 — Wave 8 agent partial WIP recovered manually + 7 commits flipping all stubs. tsc clean, lint clean, no Beta banners or stub markers remain.

## Notes

Wave 8 đã được spawn ngày 2026-04-29 (agent `a8463cd5cdaf699e0`) với scope tương tự nhưng chạy lúc context khác. Reports module đã được flip thủ công (commit `469e4b7`). Các module còn lại (admin, billing, dashboard, doctor, notifications, pharmacy) đang được agent xử lý.

Khi task này done, dự án Clinic CMS hoàn toàn ngừng dùng mock data ở FE layer.

Known BE bugs để handle gracefully (không crash):
- BUG-001 (High): `POST /api/v1/services` 500 vì Decimal không JSON-serializable trong audit_log
- BUG-002 (Medium): `POST /api/v1/visits/{id}/vitals` 400 nếu clinic chưa setup vital_field_definition
- BUG-003 (Low): `GET /api/v1/visits/{id}/prescriptions` 405 (không có GET method)

## Blockers

- TASK-006..015 đã merge vào BE main ✓
- Demo BE container restart với code merged ✓
- Có thể start ngay
