---
id: TASK-128
type: feature
title: "Payroll: tính lương (KPI + chiết khấu thủ thuật/thuốc) + màn hình lương cuối tháng"
status: IN_REVIEW
priority: High
assigned: Code Review Agent
created: 2026-07-30
updated: 2026-07-30
branch: "feature/TASK-128"
tags: [hr, payroll, kpi, commission, feature]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-128/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-128: Payroll — tính lương nhân sự (KPI + chiết khấu) + màn lương cuối tháng

**Nguồn:** Ý #1 + #7 batch 2026-07-30 (gộp: engine tính lương + màn hình). Phụ thuộc **TASK-125** (phân loại thủ thuật để chiết khấu) + **TASK-127** (ca/công). Đã có nền: migration `0058_staff_salary_config_and_payroll_perm` — cần rà soát tái dùng.

## Description
Xây dựng **tính lương nhân sự** gồm: lương cơ bản/theo công (từ attendance/ca — TASK-127), **KPI** (chỉ tiêu theo vai trò), **chiết khấu (commission)** theo **thủ thuật** (dịch vụ loại procedure — TASK-125) và theo **thuốc** (đơn thuốc/cấp phát). Kèm **màn hình tính lương cuối tháng** (bảng lương theo kỳ, chi tiết cấu phần, chốt/duyệt, xuất).

## Requirements
- [x] Rà soát `staff_salary_config` (0058) + quyền payroll đã có → tái dùng/mở rộng.
- [x] BE: cấu hình lương (base, hệ số KPI, tỷ lệ chiết khấu theo loại dịch vụ/thuốc), engine tính lương theo kỳ (tháng): base/công + KPI + commission thủ thuật + commission thuốc.
- [x] Nguồn commission: dịch vụ procedure (TASK-125) đã thực hiện + thuốc đã bán/cấp phát (đơn vị theo TASK-124) trong kỳ.
- [x] FE: **màn hình lương cuối tháng** — chọn kỳ, danh sách nhân sự + cấu phần lương, xem chi tiết, chốt/duyệt (đã có sẵn từ nền base payroll — mở rộng breakdown); xuất CSV/PDF không thuộc phạm vi build thêm ở TASK-128 (đã có "Ghi vào chi phí" từ nền cũ, chưa có export CSV/PDF riêng — xem hạn chế trong functional design).
- [x] Audit + phân quyền (chỉ HR/admin xem/chốt lương) — `payroll.manage` + `__auditable__` trên 3 model mới.

## Acceptance Criteria
- [x] Tính đúng lương kỳ = base/công + KPI + chiết khấu thủ thuật + chiết khấu thuốc, có chi tiết truy vết (4 trường breakdown trên payslip).
- [x] Màn lương cuối tháng: xem/chốt/xuất; số khớp dữ liệu dịch vụ/thuốc/công thực tế (xác minh bằng smoke test DB thật — xem handoff).
- [ ] Integration test engine + E2E màn hình; RBAC — unit tests đầy đủ (BE+FE) + smoke test DB thật cho commission/KPI; **DB-integration test suite đầy đủ + E2E UI chưa chạy trong phiên này** (để Test Agent xác nhận).

## Progress Checklist
- [x] Planning | [x] Implementation | [ ] Code Review | [ ] Testing | [x] Documentation

## Notes / Dependencies
- **SCOPE (chốt 2026-07-30):** CK thủ thuật = **% theo loại DV**, trả cho **bác sĩ khám (visit.doctor_id)** (không cần vá performed_by_user_id); CK thuốc = **% doanh thu thuốc** (bác sĩ kê đơn); **KPI theo doanh số**; **có claw-back** khi void/refund → trừ kỳ sau. Xem implementation-plan.
- **Phụ thuộc:** TASK-125 (service_type_id — rate khoá theo loại), TASK-127 (worked_days cho base), TASK-124 (đơn vị thuốc — DONE). Nền: 0058 + payroll_service + PayrollPage đã có.

## Blockers
Chờ TASK-125 + TASK-127 (dữ liệu đầu vào). Cần /task-plan chốt mô hình KPI/commission trước khi implement. — *Đã gỡ: TASK-125/127 đã merge vào dev, plan đã chốt (xem refs/implementation-plan.md).*

## Timestamps
- Implementation Completed: 2026-07-30

## Handoff
- `docs/tasks/TASK-128/handoff/implementation-to-review.md`
- Functional design: `docs/tasks/TASK-128/deliveries/final-specs/payroll-commission-kpi-functional-design.md`
- API spec: `docs/tasks/TASK-128/deliveries/api-specs/payroll-commission-kpi-api.md`
