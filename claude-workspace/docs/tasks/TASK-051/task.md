---
id: TASK-051
type: feature
title: Cập nhật UI — tăng cỡ chữ, mặc định tiếng Việt, template in (phiếu khám/hóa đơn/đơn thuốc) FE
status: DONE
priority: Medium
assigned: ""
created: 2026-05-04
updated: 2026-05-04
completed: 2026-05-04
branch: "feature/TASK-051-ui-typography-i18n-print"
jira_key: ""
tags: [fe, ui, ux, i18n, print, accessibility]
affected-repos: [clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/tasks/TASK-047/task.md  # native print A4/A5 (PrintableInvoice + PrintablePrescription) — base để mở rộng"
    - "docs/tasks/TASK-039/task.md  # MediZen design system — Tailwind tokens + font"
    - "docs/tasks/TASK-017/task.md  # i18n (vi/en) baseline"
---

# TASK-051: Cập nhật UI — tăng cỡ chữ, mặc định tiếng Việt, template in (phiếu khám/hóa đơn/đơn thuốc) FE

## Locked Decisions (per /complete-task option C, 2026-05-04)

| Decision | Value | Rationale |
|---|---|---|
| Print strategy POS 80mm | `window.print()` + `@page { size: 80mm auto; }` CSS | Consistent với pattern TASK-047 (A4 hóa đơn + A5 đơn thuốc đều native browser print). Không dùng Tauri printer plugin / ESC-POS raw command. |
| ESC/POS raw | OUT OF SCOPE | Nếu cần follow-up sau, mở task riêng. |
| i18n default | `lng: "vi"` + `detection.order: ["localStorage"]` (drop navigator) | User báo: máy locale EN vẫn hiện EN dù `fallbackLng=vi`. Drop navigator detection — chỉ tôn trọng explicit user choice qua localStorage `app.language`. |
| Typography baseline | Tailwind default 16px body giữ nguyên; audit + nâng `text-xs`/`text-sm` ở các page chính lên 1 step (xs→sm, sm→base) | Không thay đổi root font-size để tránh vỡ layout dày đặc. Nâng theo từng usage là an toàn hơn. |
| Branch start point | `git stash --include-untracked` → `git checkout main` → `git pull` → `git checkout -b feature/TASK-051-ui-typography-i18n-print` | Currently dirty branch `feature/TASK-047-print-receipts` có 10 files modified KHÔNG liên quan TASK-051. Stash để user xử lý sau, KHÔNG `stash pop`. |
| Repo scope | `clinic-cms-web` ONLY | Không touch `clinic-cms`, `clinic-cms-merge`, `clinic-cms-landing`. Không touch BE source (precedent TASK-050 incident). |
| Phasing | Phase 1 (typography + i18n) + Phase 2 (4 print templates new) — implement cả 2 trong 1 PR | User chọn C = full scope. |

## Description

User feedback sau khi review FE:
1. **UI cần update lại** — cảm giác chữ nhỏ, khó đọc, đặc biệt với người dùng phòng khám (lễ tân, dược sĩ, bác sĩ thường nhìn màn hình cả ngày).
2. **Tăng cỡ chữ** — cần nâng baseline font-size (mặc định Tailwind `text-sm` 14px → `text-base` 16px, hoặc cấu hình root font-size).
3. **Mặc định tiếng Việt** — hiện đang detect browser language (i18next-browser-languagedetector), nhiều máy mặc định EN → user thấy tiếng Anh khi mở app. Cần force `vi` làm default.
4. **Template in chuyên dụng cho từng loại in (FE)** — TASK-047 đã làm `PrintableInvoice` (A4) + `PrintablePrescription` (A5). Cần mở rộng thêm các template còn thiếu:
   - **Phiếu khám** (visit slip / examination form) — A5
   - **Hóa đơn** (invoice / receipt) — đã có A4 từ TASK-047, kiểm tra lại có cần A5/POS thermal không
   - **Đơn thuốc** (prescription) — đã có A5 từ TASK-047
   - **Phiếu chỉ định cận lâm sàng** (lab order) — A5
   - **Phiếu thu** (payment receipt) — POS 80mm thermal hoặc A5
   - **Sổ khám bệnh / kết quả khám** (medical record summary) — A4

## Phạm vi

### 1. UI/Typography update (toàn FE)
- Nâng base font-size từ 14px → 16px hoặc dùng Tailwind `text-base` ở root
- Audit tất cả chỗ dùng `text-xs` (12px) → cân nhắc nâng lên `text-sm` (14px) cho readability
- Kiểm tra spacing/line-height phù hợp với font lớn hơn (tránh layout vỡ)
- Tăng button size? (`h-9` → `h-10` cho primary CTA?)
- Verify dark mode + MediZen Indigo brand vẫn nhất quán

### 2. Default language → Vietnamese
- Update `clinic-cms-web/src/i18n/index.ts` (hoặc tương đương) — set `fallbackLng: 'vi'` và bỏ/giảm priority `LanguageDetector`
- Hoặc detect lần đầu, nếu không phải `vi` thì set về `vi` (chỉ tôn trọng user override khi đã chuyển ngôn ngữ thủ công)
- Verify: mở app lần đầu trên máy EN → app hiện tiếng Việt
- Verify language switcher (vi/en) vẫn hoạt động + persist localStorage

### 3. Print templates — mở rộng từ TASK-047 base
TASK-047 đã thiết lập pattern: component `Printable<Type>` + class `print-only` + `@media print` CSS + `window.print()` trigger.

Cần thêm/audit:

| # | Loại in | Khổ giấy | Component | Trigger từ trang | Trạng thái |
|---|---|---|---|---|---|
| 1 | Phiếu khám (visit slip) | A5 | `PrintableVisitSlip` | VisitDetailPage / QueueBoard | TODO |
| 2 | Hóa đơn | A4 + (POS 80mm tùy chọn) | `PrintableInvoice` | InvoicePage | A4 đã có (TASK-047), POS TODO |
| 3 | Đơn thuốc | A5 | `PrintablePrescription` | PrescriptionPage / EMR | DONE (TASK-047) — chỉ verify |
| 4 | Phiếu chỉ định CLS | A5 | `PrintableLabOrder` | LabOrdersTab | TODO |
| 5 | Phiếu thu | POS 80mm | `PrintablePaymentReceipt` | PaymentModal | TODO |
| 6 | Sổ khám / tóm tắt | A4 | `PrintableMedicalSummary` | PatientDetailPage | TODO |

- Mỗi template tuân thủ pattern TASK-047 (xem `clinic-cms-web/src/features/print/`)
- Hỗ trợ logo phòng khám + thông tin clinic (lấy từ active clinic context)
- Support print preview modal trước khi `window.print()`
- I18n đầy đủ tiếng Việt (header, label, footer)

## Requirements

### Typography & UI
- [ ] Nâng base font-size root (14px → 16px) hoặc tăng Tailwind preset
- [ ] Audit `text-xs` usage → quyết định nâng/giữ
- [ ] Verify không vỡ layout: dashboard, EMR 8-tab, QueueBoard 5-col, ARAging, Pharmacy
- [ ] Verify accessibility (WCAG 2.1 AA contrast + min font 16px body)

### i18n default
- [ ] Set `fallbackLng: 'vi'` trong i18n config
- [ ] Logic: lần đầu mở app → vi; user đổi sang en → persist; refresh → giữ en
- [ ] Test trên máy locale EN → mở app thấy vi
- [ ] Verify Tauri build (i18n resource bundle)

### Print templates (FE)
- [ ] `PrintableVisitSlip` (A5) — phiếu khám có QR mã visit + thông tin BN + chuyên khoa + bác sĩ
- [ ] `PrintableLabOrder` (A5) — phiếu chỉ định cận lâm sàng (danh sách xét nghiệm + chuẩn bị)
- [ ] `PrintablePaymentReceipt` (POS 80mm thermal) — phiếu thu sau payment
- [ ] `PrintableMedicalSummary` (A4) — tóm tắt bệnh án (visit + diagnosis + prescription + lab results)
- [ ] (optional) `PrintableInvoice` thêm POS 80mm variant
- [ ] Mỗi template có Print Preview Modal + nút "In" gọi `window.print()`
- [ ] Header logo + tên + địa chỉ phòng khám (active clinic)
- [ ] I18n vi/en đầy đủ
- [ ] Unit tests cho mỗi component (vitest + Testing Library)

## Acceptance Criteria

- [ ] App mở lần đầu trên máy locale EN → hiện tiếng Việt
- [ ] Body font ≥16px ở mọi page chính (Dashboard, EMR, Queue, Pharmacy, Billing, Reports)
- [ ] 4 print templates mới (VisitSlip, LabOrder, PaymentReceipt, MedicalSummary) hoạt động:
  - Click nút "In" → mở Preview Modal → click "In" trong modal → `window.print()` hiển thị đúng layout
  - Khổ giấy đúng (A5/A4/POS 80mm) khi print thực tế
  - Logo + thông tin clinic xuất hiện
  - Vietnamese labels chuẩn (không lẫn EN)
- [ ] Không regression: 700+ tests FE hiện có vẫn pass
- [ ] Không vỡ layout (manual smoke test 7 màn chính)
- [ ] Lint + type-check pass

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-051/refs/`
- **Code**: `clinic-cms-web/src/` (FE feature branch)
  - i18n: `src/i18n/`
  - print templates: `src/features/print/` (xem TASK-047 pattern)
  - typography: `tailwind.config.ts` + `src/index.css`
- **Tests**: `docs/tasks/TASK-051/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-051/handoff/`
- **Test Report**: `docs/tasks/TASK-051/deliveries/test-reports/test-report.md`
- **Final Specs**: `docs/tasks/TASK-051/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-05-04

## Notes

- **Phụ thuộc**: TASK-047 (IN_REVIEW) thiết lập pattern print FE — nên đợi TASK-047 APPROVED trước khi nhân rộng template.
- **Risk**: nâng base font có thể gây vỡ layout dày đặc (EMR 8-tab, QueueBoard 5-col, ARAging table). Cần regression visual.
- **Decision pending**:
  - POS 80mm thermal có cần in browser native hay phải qua Tauri shell + `tauri-plugin-printer`? (TASK-047 dùng `window.print()` browser → có thể đủ với CSS `@page size`)
  - Có cần ESC/POS raw command cho máy in nhiệt không? (Out of scope, để follow-up nếu cần)
- **i18n default 'vi'**: cần check user preference key trong localStorage trước, nếu user đã chọn `en` thì tôn trọng.

## Blockers

None at task-create time. Suggest sequence:
1. Đợi TASK-047 APPROVED (pattern print stabilized)
2. Phase 1: typography + i18n default (impact rộng, cần regression toàn FE)
3. Phase 2: print templates (mở rộng theo pattern TASK-047)

## Timestamps

- **Implementation Completed**: 2026-05-04
- **Testing Completed**: 2026-05-04
