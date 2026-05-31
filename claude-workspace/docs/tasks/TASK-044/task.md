---
id: TASK-044
type: feature
title: Role-specific dashboards — Lễ tân + Điều dưỡng + Dược sĩ + Admin (4 màn FE)
status: DONE
priority: Medium
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
completed: 2026-05-01
branch: feature/task-044-role-dashboards
jira_key: ""
tags: [fe, dashboard, multi-role, ui, phase-d]
affected-repos: [clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/MENU_AND_SCREENS.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/2542650746708884228"
  confluence: ""
  jira_ticket: ""
  other:
    - "../TASK-043/deliveries/final-specs/conformance-audit-report.md"
    - "../TASK-035/task.md"
    - "../../design/medizen-modern/html-export/index.html"
---

# TASK-044: Role-specific dashboards (4 màn FE)

## Description

Build 4 role-specific dashboards based on Stitch refs identified by TASK-043 audit (gap: 4 dashboards missing in current FE).

## Requirements

### S.1 Receptionist Dashboard (`/dashboards/reception`)
- KPIs: BN chờ tiếp nhận, BN đã đăng ký hôm nay, BN walk-in vs appointment, lịch hẹn sắp tới (1h)
- Widget: Live queue board mini-view (top 5 BN chờ)
- Widget: Lịch hẹn hôm nay (table)
- Widget: Quick action — "Tiếp nhận BN mới" button

### S.2 Nurse Dashboard (`/dashboards/nurse`)
- KPIs: BN đang chờ ghi sinh hiệu, BN cần sàng lọc, đơn thuốc cần phát
- Widget: Bộ phận đang xử lý (Recharts bar)
- Widget: Lịch sử ghi sinh hiệu hôm nay (table)
- Widget: Cảnh báo dị ứng / sinh hiệu bất thường

### S.3 Pharmacist Dashboard (`/dashboards/pharmacy`)
- KPIs: Đơn chờ phát, Đơn đã phát, Lô hết hạn 30/60/90 ngày, Tồn kho thấp
- Widget: Inventory low-stock chart (Recharts)
- Widget: Đơn chờ phát top 10 (table)
- Widget: Quick action — "Kiểm kê" + "Xử lý hết hạn" links

### S.4 Admin Dashboard (`/dashboards/admin`)
- KPIs: Doanh thu hôm nay/tuần/tháng, BN mới, BN tái khám, Hoá đơn chờ thu
- Widget: Doanh thu 30 ngày (Recharts line)
- Widget: Phân bố BN theo khoa (Recharts pie)
- Widget: Hoạt động nhân viên (last 24h activity feed)
- Widget: Status feature flags (BHYT enabled? Multi-role?)

### Cross-cutting
- 4 routes added in `src/router/index.tsx`
- Coordinate with TASK-035 (Wave 3-B) — multi-role users land on `/dashboards/multi-role` with sections for each of their roles
- Use Recharts (existing dependency)
- Indigo MediZen tokens (TASK-039 inheritance)
- i18n vi/en for `dashboards.*` namespace
- Reuse existing API hooks where possible (visits, billing, prescriptions, inventory, reports)

### Tests
- 4 dashboard render tests (one per role)
- Empty state tests (no data scenarios)
- Multi-role navigation test

## Acceptance Criteria

- [x] 4 dashboards routable + rendered without console errors
- [x] KPIs display real data (or graceful empty/loading state)
- [x] Widget charts render với Indigo palette
- [x] FE tests pass; 0 TS errors; 0 lint warnings
- [x] Build PASS

## Dependencies

- Blocked by: TASK-039 ✅ (design tokens), TASK-035 (Wave 3-B in progress — for multi-role landing coord)
- Coordinates with: TASK-040 (DashboardPage existing routes — don't conflict)

## Effort

**Medium** (2-3d). 4 dashboards + reuse existing API/charts.

## Risk

LOW (FE only, no schema change, no BE migration).

## Completion Notes (2026-05-01)

- A11y Fix (F3): `kpi-low-stock` KpiCard converted to `<button type="button">` with `aria-label` when onClick present
- Permission rename (F1 follow-up): 4 strings renamed to 2-level convention (`reception.dashboard`, `nurse.dashboard`, `pharmacy.dashboard`, `admin.dashboard`); all 5 test files updated
- 572/572 tests pass, 0 TS errors, 0 lint warnings, build PASS
- Functional design: `docs/tasks/TASK-044/deliveries/final-specs/role-dashboards-functional-design.md`
- Merge-time TODOs: BE seed migration (4 new perms) + Sidebar nav entries (TASK-035)
