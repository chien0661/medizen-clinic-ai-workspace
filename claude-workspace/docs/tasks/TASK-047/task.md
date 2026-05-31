---
id: TASK-047
type: feature
title: In phiếu khám + in hóa đơn (FE) — native browser print, A5/A4
status: IN_REVIEW
priority: High
assigned: code-review-agent
created: 2026-05-04
updated: 2026-05-03
branch: "feature/TASK-047-print-receipts"
jira_key: ""
tags: [fe, print]
affected-repos: [clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-047: In phiếu khám + in hóa đơn (FE) — native browser print, A5/A4

## Description

Hai luồng print core trên FE hiện **chưa hoạt động** (button có nhưng chưa wired up hoặc trả về placeholder):

1. **In phiếu khám** — phiếu khám bệnh / đơn thuốc / kết quả khám (khổ **A5**)
2. **In hóa đơn** — hóa đơn thanh toán cho bệnh nhân (khổ **A4**)

**Thứ tự thực hiện**: Hóa đơn trước → Phiếu khám sau (do hóa đơn được dùng nhiều hơn trong vận hành lễ tân + thu ngân).

**Beta features audit** đã được tách sang `TASK-048` — không nằm trong scope task này.

## Technical Decisions (locked)

- **Print strategy**: **Native browser print** (`window.print()` + CSS `@media print`). Không dùng PDF library client-side, không yêu cầu BE endpoint render PDF ở giai đoạn 1.
- **Khổ giấy**:
  - Phiếu khám: **A5** (148 × 210 mm)
  - Hóa đơn: **A4** (210 × 297 mm)
- **CSS approach**: dùng dedicated `@page` rules + print-only stylesheet để hide navigation / sidebar / buttons khi in. Tách `<PrintableInvoice>` / `<PrintablePrescription>` component riêng để tránh ảnh hưởng layout chính.
- **Trigger UX**:
  - Button "In hóa đơn" trên màn chi tiết hóa đơn → mở print preview (window.print)
  - Button "In phiếu khám" trên màn chi tiết bệnh nhân (tab visits / prescriptions) → mở print preview
- **Browser support**: Chrome + Edge (per project — Tauri 2 desktop dùng webview Chromium).

## Requirements

### Hóa đơn (làm trước)
- [ ] Identify nơi đang stub print hóa đơn trong FE (`InvoicesTab` ở `PatientDetailPage`, billing module)
- [ ] Tạo component `<PrintableInvoice>` với layout A4
- [ ] Template gồm: clinic name + logo + địa chỉ + tax ID, số hóa đơn + ngày in, patient info (tên, mã BN, SĐT), line items (tên dịch vụ/thuốc, đơn giá, số lượng, thành tiền), subtotal + VAT + total, payment method, ghi chú, signature line
- [ ] Wire button "In hóa đơn" → trigger `window.print()` với printable component
- [ ] CSS `@media print` + `@page { size: A4; margin: 12mm; }`

### Phiếu khám (sau)
- [ ] Identify nơi đang stub print phiếu khám trong FE
- [ ] Tạo component `<PrintablePrescription>` với layout A5
- [ ] Template gồm: clinic info, patient info, ngày khám, chẩn đoán, đơn thuốc (nếu có) hoặc chỉ định cận lâm sàng, lời dặn bác sĩ, signature line bác sĩ
- [ ] Wire button "In phiếu khám" → `window.print()`
- [ ] CSS `@media print` + `@page { size: A5; margin: 8mm; }`

### Common
- [ ] Hide top nav / sidebar / app chrome khi print
- [ ] Đảm bảo font readable khi in (12pt body, 14pt header)
- [ ] Print không bị cắt ở trang sau (page-break-inside: avoid trên line item rows)
- [ ] Test trên Chrome (Tauri webview) — kiểm tra Print Preview match design

## Acceptance Criteria

- [ ] Click "In hóa đơn" → browser print preview mở, hiển thị đúng template A4, không có nav/sidebar
- [ ] Click "In phiếu khám" → browser print preview mở, hiển thị đúng template A5, không có nav/sidebar
- [ ] Tất cả field bắt buộc render đúng từ data (clinic, patient, line items, totals)
- [ ] Print preview match Figma/design intent (nếu có) — fallback theo design system MediZen Modern
- [ ] Multi-page invoice (line items dài) page-break đúng, header lặp lại trên mỗi trang
- [ ] Không regression layout chính khi không print

## Progress Checklist

- [ ] Investigation: scan stub locations + existing button handlers
- [ ] Implementation Hóa đơn (component + wire + print CSS)
- [ ] Implementation Phiếu khám (component + wire + print CSS)
- [ ] Code Review
- [ ] Testing (manual + e2e nếu setup được)
- [ ] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-047/refs/`
- **Code**: `clinic-cms-web/src/pages/patients/PatientDetailPage.tsx` (InvoicesTab), `clinic-cms-web/src/modules/billing/`
- **Tests**: `docs/tasks/TASK-047/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-047/handoff/`
- **Test Report**: `docs/tasks/TASK-047/deliveries/test-reports/test-report.md`
- **Final Specs**: `docs/tasks/TASK-047/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-05-04
- **Implementation Completed**: 2026-05-03 01:37 UTC

## Notes

**Workspace state khi bắt đầu** (per user decision "không tách động gì"):
- `clinic-cms-web` đang ở branch `main`, có uncommitted changes:
  - `M src/modules/admin/api.ts`
  - `M src/pages/patients/PatientDetailPage.tsx` (vừa được fix duplicate TABS declaration trong session này)
  - `?? e2e/...` (untracked e2e specs)
- Code Implementation Agent sẽ tạo feature branch `feature/TASK-047-print-receipts` và include các thay đổi trên (per quyết định user).

**Investigation hints**:
- TASK-039 / TASK-040 port MediZen Modern design — có thể đã có printable component nào đó stubbed
- Search `window.print`, `onPrint`, `handlePrint`, "In hóa đơn", "In phiếu" trong `clinic-cms-web/src/`

## Blockers

None
