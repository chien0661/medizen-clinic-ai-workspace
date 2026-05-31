---
id: TASK-071
type: feature
title: Super Admin — Thống kê phòng khám theo thời gian
status: DOCUMENTING
priority: Medium
assigned: Unassigned
created: 2026-05-31
updated: 2026-05-31
review_round: 2
branch: "feature/TASK-071-superadmin-analytics"
jira_key: ""
tags: [super-admin, analytics, statistics, charts]
affected-repos: [clinic-cms-merge, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "Super admin module: clinic-cms-merge/app/modules/superadmin/"
    - "Super admin FE: clinic-cms-web/src/pages/superadmin/"
---

# TASK-071: Super Admin — Thống kê phòng khám theo thời gian

## Description

Bổ sung tính năng thống kê chi tiết cho Super Admin — xem chỉ số hoạt động của **từng phòng khám** hoặc **tổng hợp toàn hệ thống**, lọc theo khoảng thời gian tùy chọn (ngày/tuần/tháng/năm hoặc khoảng tùy ý). Chỉ Super Admin mới truy cập được.

Đây là phần mở rộng của TASK-070 (FE Super Admin), cần thêm API BE mới và trang FE mới trong section super admin.

## Requirements

### BE — API thống kê mới (`/api/v1/superadmin/analytics`)

- [ ] `GET /api/v1/superadmin/analytics/overview` — tổng hợp toàn hệ thống
  - Params: `period` (day|week|month|year), `date_from`, `date_to`, `clinic_id?`
  - Response: `{ visits, revenue, avg_revenue_per_visit, new_patients, returning_patients }`

- [ ] `GET /api/v1/superadmin/analytics/timeseries` — chuỗi thời gian để vẽ chart
  - Params: `metric` (visits|revenue|new_patients), `granularity` (day|week|month|year), `date_from`, `date_to`, `clinic_id?`
  - Response: `{ items: [{ period: "2026-05-01", value: 123 }] }`

- [ ] `GET /api/v1/superadmin/analytics/clinics` — bảng so sánh từng phòng khám
  - Params: `period`, `date_from`, `date_to`, `sort_by?`, `limit?`
  - Response: `{ items: [{ clinic_id, clinic_name, visits, revenue, avg_daily_visits, avg_weekly_visits, avg_monthly_revenue }] }`

### Chỉ số cần thống kê

| Chỉ số | Mô tả |
|--------|-------|
| `visits` | Số lượt khám |
| `revenue` | Doanh thu (từ hóa đơn paid) |
| `new_patients` | Bệnh nhân mới (lần đầu đến khám) |
| `returning_patients` | Bệnh nhân tái khám |
| `avg_revenue_per_visit` | Doanh thu trung bình/lượt khám |
| `avg_daily_visits` | Lượt khám TB/ngày |
| `avg_weekly_visits` | Lượt khám TB/tuần |
| `avg_monthly_visits` | Lượt khám TB/tháng |
| `avg_monthly_revenue` | Doanh thu TB/tháng |

### Bộ lọc thời gian

- [ ] Quick filters: Hôm nay / 7 ngày qua / 30 ngày qua / Tháng này / Quý này / Năm này
- [ ] Custom range: date picker từ–đến (tối đa 365 ngày)
- [ ] Granularity: Theo ngày / Theo tuần / Theo tháng / Theo năm

### FE — Trang mới trong Super Admin

**Trang: `/superadmin/analytics`**
- [ ] Filter bar trên cùng: chọn clinic (all hoặc từng clinic) + bộ lọc thời gian
- [ ] Stats cards hàng đầu: Tổng lượt khám, Tổng doanh thu, TB/ngày, TB/tháng
- [ ] Line chart: lượt khám hoặc doanh thu theo thời gian (chọn metric bằng toggle)
- [ ] Bảng so sánh phòng khám: sortable, show avg_daily/weekly/monthly
- [ ] Export CSV (optional, nice-to-have)

**Sidebar**: thêm link "Thống kê" vào section Super Admin (giữa Dashboard và Phòng khám)

### Scope guard
- Chỉ Super Admin (`is_superuser = true`) mới truy cập được
- Phòng khám thường (clinic admin) không thấy và không gọi được API này
- Dữ liệu trả về cross-tenant (bypass RLS dùng cơ chế đã có từ TASK-070)

## Acceptance Criteria

- [ ] Chọn "Hôm nay" → hiện lượt khám và doanh thu của ngày hôm nay, cập nhật realtime
- [ ] Chọn "Năm này" → line chart 12 điểm (tháng 1–12), granularity = month
- [ ] Custom range 90 ngày + granularity week → chart ~13 điểm (tuần)
- [ ] Filter theo 1 phòng khám cụ thể → chỉ hiện dữ liệu của clinic đó
- [ ] Bảng so sánh sortable theo doanh thu, lượt khám, avg
- [ ] Non-superuser navigate tới `/superadmin/analytics` → redirect về `/dashboard`

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **BE Super Admin module**: `clinic-cms-merge/app/modules/superadmin/`
- **FE Super Admin pages**: `clinic-cms-web/src/pages/superadmin/`
- **FE Super Admin API**: `clinic-cms-web/src/modules/superadmin/api.ts`
- **Input Specs**: `docs/tasks/TASK-071/refs/`
- **Tests**: `docs/tasks/TASK-071/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-071/handoff/`
- **Test Report**: `docs/tasks/TASK-071/deliveries/test-reports/test-report.md`

## Timestamps

- **Created**: 2026-05-31

## Notes

- BE query nguồn dữ liệu: `visit` table (status=completed) + `invoice` table (status=paid)
- Cần index trên `visit.completed_at` và `invoice.paid_at` để query nhanh theo khoảng thời gian
- `new_patients`: đếm patient_id có `first_visit_at` nằm trong khoảng filter
- Granularity mapping: `day` → GROUP BY DATE(col), `week` → GROUP BY DATE_TRUNC('week', col), v.v.
- Tham khảo queries hiện có trong reports module: `clinic-cms-merge/app/modules/reports/`
- Chart library: dùng `recharts` (đã có trong project) — LineChart + BarChart
- Bảng so sánh phòng khám: load lần đầu top-10 theo doanh thu, cho sort/filter thêm

## Blockers

- Phụ thuộc TASK-070 (FE Super Admin base) — cần merge trước
