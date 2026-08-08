---
id: TASK-139
type: feature
title: "Payroll: xuất bảng lương Excel + phiếu lương PDF từng nhân viên"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-08-07
updated: 2026-08-08
branch: "feature/TASK-139-payroll-export"
jira_key: ""
tags: [hr, payroll, export, excel, pdf, feature]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-139/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-139: Payroll — xuất bảng lương Excel + phiếu lương PDF từng nhân viên

**Nguồn:** Yêu cầu 2026-08-07. Phụ thuộc **TASK-138** (payslip breakdown buổi/ca + rate source) — code base là branch `feature/TASK-138-payroll-session-shift` (chưa merge dev).

## Description

Màn lương cuối tháng (PayrollPage) hiện chỉ có "Ghi vào chi phí", chưa xuất được file. Bổ sung:

1. **Xuất Excel bảng lương cả kỳ**: 1 file .xlsx chứa toàn bộ nhân viên trong kỳ với đầy đủ breakdown (kiểu lương, số công/buổi/ca, đơn giá, base, OT, phụ cấp, thưởng/phạt, commission thủ thuật/thuốc + tỷ lệ & nguồn (riêng/chung), KPI, claw-back, điều chỉnh, gross/net).
2. **Phiếu lương PDF từng nhân viên** (đã chốt với user 2026-08-07): mỗi nhân viên 1 phiếu lương chi tiết, in từ nút trên từng dòng bảng lương — theo pattern `Printable*` sẵn có của dự án (print qua trình duyệt → Save as PDF). KHÔNG sinh PDF phía BE.

## Requirements

- [ ] BE: endpoint `GET /api/v1/payroll/export` (kỳ tháng + filter như màn payroll) trả file .xlsx — tái dùng hạ tầng `app/core/excel.py` (như `/staff/export`, `/attendance/export`); RBAC `payroll.manage`; audit như các export khác.
- [ ] Cột Excel phủ toàn bộ trường payslip TASK-128 + TASK-138 (kể cả `procedure_rate_percent/source`, `medicine_rate_percent/source`, `session_rate`/`shift_rate`/`completed_shifts`); header tiếng Việt.
- [ ] FE: nút Xuất Excel trên PayrollPage — pattern `useExportDownload` + `ExportExcelButton` (như export DS bệnh nhân); tên file có kỳ lương.
- [ ] FE: component `PrintablePayslip` + modal in — nút in trên từng dòng nhân viên; layout phiếu lương: thông tin phòng khám, nhân viên (mã NV, tên — KHÔNG cần tài khoản), kỳ lương, bảng breakdown đầy đủ, chỗ ký nhận; theo pattern `PrintableInvoice`/`PrintablePrescription`.
- [ ] i18n: mọi label mới có ở cả `vi` và `en` (`hr.json`); không hardcode UI text.
- [ ] Nhân sự không có tài khoản (user_id NULL) xuất hiện đầy đủ trong Excel và in được phiếu lương.

## Acceptance Criteria

- [ ] Xuất Excel kỳ có dữ liệu → file mở được, đủ số dòng = số nhân viên có payslip, số liệu khớp màn hình (kể cả nhân viên lương buổi/ca và commission override).
- [ ] Kỳ không có dữ liệu → file rỗng có header (hoặc 4xx rõ ràng), không 500.
- [ ] Phiếu lương in từng người hiển thị đúng breakdown như API trả (đối chiếu ít nhất 1 nhân viên override 15% và 1 nhân viên rate chung).
- [ ] RBAC: role không có `payroll.manage` bị 403 với endpoint export; unit test BE + FE cho export và printable.
- [ ] Không regression PayrollPage hiện có.

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-139/refs/`
- **Code**: (feature branch)
- **Tests**: `docs/tasks/TASK-139/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-139/handoff/`
- **Test Report**: `docs/tasks/TASK-139/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-139/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-139/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-08-07
- **Review Completed**: 2026-08-07
- **Testing (round 1) Completed**: 2026-08-08 — 1 bug found (BUG-001), sent back to IN_PROGRESS
- **Testing (round 2) Completed**: 2026-08-08 — BUG-001 fix verified, all tests PASS

## Notes

- **Branch base = `feature/TASK-138-payroll-session-shift`** (BE `cebf0bd`, FE `4bf1b55`) vì cần các trường payslip mới; khi release phải merge TASK-138 trước rồi TASK-139.
- PDF qua browser-print là quyết định đã chốt (user 2026-08-07) — nhất quán với hoá đơn/đơn thuốc, không thêm thư viện PDF vào BE.
- Hạ tầng sẵn có: `app/core/excel.py`, `useExportDownload`/`exportBlob`, `ExportExcelButton`, pattern `Printable*` + print modal.

## Blockers

None

## Test Round 1 (2026-08-08) — sent back IN_PROGRESS

1 bug found: **BUG-001** — `PayrollPage.tsx` footer `colSpan` (13→14) misaligns the "Tổng thực nhận"
total under the new "In phiếu" column instead of "Thực nhận" (AC "Không regression PayrollPage hiện có"
not met). Everything else passed (BE full unit + new tests, BE integration on a disposable stack
including mixed pay types/cross-tenant/RBAC/malformed-month scenarios, FE full vitest + new tests, i18n
parity, printable payslip content). See:
- `docs/tasks/TASK-139/bugs/BUG-001.md`
- `docs/tasks/TASK-139/deliveries/test-reports/test-report.md`
- `docs/tasks/TASK-139/deliveries/test-cases/test-cases.md`
- `docs/tasks/TASK-139/handoff/test-to-implementation.md`

## Test Round 2 (2026-08-08) — PASS, → DOCUMENTING

Targeted re-test of BUG-001's fix (FE `d271e00`; BE unchanged at `37b258d`, not re-run). Verified the
`colSpan` revert (14→13) directly in the diff, confirmed the new `PayrollPage.export.test.tsx` regression
test genuinely ties the footer alignment to the "Thực nhận" header position (not a tautology), and ran
the full FE vitest suite once: 1283 passed / 3 pre-existing failures (QueuePage×2, ForgotPasswordPage×1),
zero new failures, AttendanceWidget M-14 did not trigger. All ACs now met. See:
- `docs/tasks/TASK-139/bugs/BUG-001.md` (Resolution section)
- `docs/tasks/TASK-139/deliveries/test-reports/test-report.md` ("Re-test round 2" section)
- `docs/tasks/TASK-139/deliveries/test-cases/test-cases.md` (F-09/F-11 rows)
- `docs/tasks/TASK-139/handoff/test-to-documentation.md`
