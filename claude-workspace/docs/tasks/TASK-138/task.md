---
id: TASK-138
type: feature
title: "Payroll: thêm kiểu tính lương theo buổi / theo ca + chiết khấu cấu hình theo từng nhân sự"
status: DONE
priority: High
assigned: Unassigned
created: 2026-08-06
updated: 2026-08-07
branch: "feature/TASK-138-payroll-session-shift"
jira_key: ""
tags: [hr, payroll, commission, feature]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-138/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-138: Payroll — thêm kiểu tính lương theo buổi / theo ca + chiết khấu theo từng nhân sự

**Nguồn:** Yêu cầu 2026-08-06. Mở rộng nền payroll **TASK-128** (engine lương: base/công + KPI + commission) và **TASK-127** (ca làm việc / chấm công theo ngày).

## Description

Hai mở rộng cho phần tính lương:

1. **Kiểu tính lương theo buổi / theo ca**: hiện `staff_salary_config` chỉ hỗ trợ `monthly` (lương tháng) và `hourly` (theo giờ). Bổ sung 2 kiểu mới:
   - `per_session` (theo buổi — sáng/chiều/tối): đơn giá × số buổi làm thực tế trong kỳ.
   - `per_shift` (theo ca): đơn giá × số ca hoàn thành trong kỳ (nguồn từ dữ liệu ca/chấm công TASK-127).
2. **Chiết khấu (commission) cấu hình theo từng nhân sự**: hiện tỷ lệ chiết khấu thủ thuật/thuốc cấu hình chung (theo loại dịch vụ/thuốc — TASK-128). Bổ sung **override theo từng nhân sự**: mỗi nhân sự có thể có tỷ lệ riêng; nếu không cấu hình riêng thì fallback về tỷ lệ chung hiện tại.

## Requirements

- [ ] BE: mở rộng `staff_salary_config` — thêm `pay_type` mới (`per_session`, `per_shift`) + đơn giá tương ứng (migration mới, giữ tương thích dữ liệu cũ).
- [ ] BE: engine tính lương kỳ — nhánh tính base theo số buổi / số ca thực tế từ dữ liệu attendance/shift (TASK-127); định nghĩa rõ thế nào là "buổi/ca được tính" (hoàn thành vs. vắng/hủy).
- [ ] BE: bảng/cột cấu hình commission theo nhân sự (per-staff rate cho thủ thuật + thuốc) với logic resolve: per-staff → per-loại (hiện tại) → mặc định.
- [ ] FE: form cấu hình lương nhân sự (StaffFormPage / CommissionKpiConfigPage) — chọn kiểu lương mới + nhập đơn giá buổi/ca; UI cấu hình tỷ lệ chiết khấu riêng từng nhân sự.
- [ ] FE: màn lương cuối tháng (PayrollPage) — hiển thị đúng breakdown cho kiểu lương mới (số buổi/ca × đơn giá) và commission theo rate đã resolve.
- [ ] Phân quyền giữ nguyên `payroll.manage`; model mới/cột mới có audit (`__auditable__`).

## Acceptance Criteria

- [ ] Nhân sự cấu hình `per_session`/`per_shift` được tính lương kỳ = đơn giá × số buổi/ca thực tế, khớp dữ liệu chấm công; nhân sự `monthly`/`hourly` cũ không đổi kết quả.
- [ ] Nhân sự có tỷ lệ chiết khấu riêng được tính commission theo tỷ lệ riêng; nhân sự không có cấu hình riêng vẫn dùng tỷ lệ chung (regression TASK-128 pass).
- [ ] Payslip breakdown truy vết được: kiểu lương, số buổi/ca, đơn giá, tỷ lệ commission áp dụng (riêng hay chung).
- [ ] Unit test BE (engine + resolve rate) + FE (form config, PayrollPage breakdown); integration test với dữ liệu ca/chấm công thật.

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-138/refs/` *(DetailDesign, SRS, implementation-plan)*
- **Code**: (feature branch)
- **Tests**: `docs/tasks/TASK-138/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-138/handoff/`
- **Test Report**: `docs/tasks/TASK-138/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-138/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-138/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-08-06
- **Completed**: 2026-08-07

## Notes

- Nền sẵn có: `staff_salary_config` (migration 0058, mở rộng ở TASK-128), engine payroll + 3 model commission/KPI (TASK-128), dữ liệu ca/chấm công (TASK-127, migration 0072).
- FE hiện hardcode `PAY_TYPE_LABEL = { monthly: "Lương tháng", hourly: "Theo giờ" }` tại `PayrollPage.tsx` — khi thêm kiểu mới nên chuyển qua i18n (xem đợt rà soát i18n 2026-08-06).
- **Đã chốt với user (2026-08-06, xem implementation-plan.md):** "buổi" = ngày công admin tích trên lưới chấm công (`AttendanceDay`, nửa ngày = 0.5) — không xây UI chấm buổi riêng; lương theo ca chỉ tính ca `completed`; chiết khấu per-staff ở mức từng loại DV + rate thuốc riêng, fallback rate chung.
- **Ràng buộc vận hành (user, 2026-08-06):** điều dưỡng/y tá KHÔNG có tài khoản đăng nhập — admin nhập liệu toàn bộ. Mọi tính năng key theo `staff_id` (không phụ thuộc `user_id`); commission tự động vẫn chỉ áp dụng cho nhân sự có tài khoản bác sĩ (giới hạn TASK-128), nhân sự khác dùng `payroll_adjustment` thủ công.

## Blockers

None
