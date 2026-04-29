---
id: TASK-019
type: feature
title: FE — Doctor (My Queue + Consultation + Vitals Dynamic + Service + Prescription)
status: DONE
priority: High
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-27
branch: "feature/task-019-fe-doctor"
tags: [frontend, doctor, visit, vitals, prescription, sprint-15]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#8-module-visits"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#6-module-visit"
    - "../../../../docs/clinic_management_business_analysis.md#7-module-vitals-dynamic-form"
    - "../../../../docs/clinic_management_business_analysis.md#9-module-prescription"
---

# TASK-019: FE — Doctor Module (Consultation Workflow End-to-End)

## Description

UI cho bác sĩ: my queue với call-next, consultation page (patient summary + vitals timeline + chief complaint + notes), dynamic vitals form renderer (đọc VitalFieldDefinition từ API), service picker, prescription builder per-item dispense source (in_house/external mixed), in đơn thuốc.

## Requirements

- [ ] **My queue** (`/doctor/queue`)
  - Tab "Của tôi" (assigned_doctor_id = current user) | "Tất cả"
  - Card mỗi visit: visit_number, patient name + age + gender, chief_complaint preview, priority badge, wait time
  - Button "Gọi bệnh nhân tiếp theo" — gọi API `POST /visits/call-next`, redirect tới consultation
- [ ] **Consultation page** (`/doctor/visits/:id`)
  - Header: patient info (name, code, age, gender, phone), visit_number, status, timer
  - Left panel: patient history (last 5 visits, allergies, chronic diseases, current meds)
  - Center panel — sections:
    1. Chief complaint + notes (textarea, auto-save 5s debounce)
    2. **Vitals timeline + nhập mới** (xem TASK-019.vitals dưới)
    3. **Services performed** (xem dưới)
    4. **Prescription** (xem dưới)
  - Right panel: action buttons (Hoàn tất khám / Tạm dừng / Hủy visit)
  - Status transition: IN_PROGRESS → AWAITING_PAYMENT khi click Hoàn tất
- [ ] **Vitals dynamic form**
  - Fetch `GET /api/v1/vitals/definitions` (active fields cho clinic)
  - Render field theo data_type (number/integer/text/boolean/select)
  - Hiển thị unit, placeholder, help_text, group_name
  - Validation theo min/max, required
  - Visual warning nếu value ngoài warning_min/max (icon + tooltip)
  - Hỗ trợ nhiều lần đo per visit, mark "primary"
  - Trend chart: hiển thị vitals của 5 visit gần nhất (recharts)
- [ ] **Services performed**
  - Search service catalog với category filter
  - Multi-select, set quantity
  - Discount input (perm `service.price_override` mới enabled, kèm reason)
  - Preview total
- [ ] **Prescription builder**
  - Add item: search medicine với indicator "✓ Còn X viên" / "✗ Hết kho"
  - Auto-suggest dispense_source (in_house if stock available, else external) — toggle override
  - Free-text item (medicine_id null) cho thuốc ngoài catalog
  - Per-item: quantity, dosage_text, duration_days, instructions
  - Cảnh báo nếu in_house qty > available stock (cho phép override → external)
  - Preview prescription print
  - Save → call API tạo prescription + reserve inventory
- [ ] **Print prescription** qua Tauri printer (TASK-016 hardware)
  - Template từ `clinic_settings.prescription.print_mode` (all/external_only/ask)

## Acceptance Criteria

- [ ] Click "Gọi tiếp theo" với có visit assigned cho mình → ưu tiên đó trước; không có thì lấy unassigned
- [ ] Vitals form cho clinic pediatric hiển thị có `head_circumference`; cho clinic general thì không
- [ ] Nhập huyết áp 180/100 (warning_max systolic 140) → icon ⚠️ tooltip "Cao hơn ngưỡng"
- [ ] Search Paracetamol → kết quả: "Paracetamol 500mg ✓ 230 viên trong kho", "Paracetamol siro ✗ Hết kho"
- [ ] Kê 50 viên Paracetamol (còn 230) → in_house OK; kê 300 viên → cảnh báo + suggest external
- [ ] Mixed prescription: 2 in_house + 1 external → header dispense_type='mixed' lưu đúng
- [ ] Hoàn tất khám → status AWAITING_PAYMENT, navigate về my queue, visit không còn trong list của BS
- [ ] Auto-save notes hoạt động (test: gõ → reload page → notes vẫn còn)

## Progress Checklist

- [x] Implementation
- [x] Code Review (self-review, 2 iterations)
- [x] Testing (274 tests pass, tsc clean, lint clean)
- [x] Documentation

## Completion

- **Completed**: 2026-04-27
- **Branch**: `feature/task-019-fe-doctor`
- **Commits**: 6 commits (types/api/i18n, queue, consultation, dashboard, routing, tests)
- **Tests**: 274 pass (26 files), 0 tsc errors, 0 lint warnings

## Related Files

- **Code**: `clinic-cms/desktop/src/modules/doctor/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Vitals dynamic form là phần phức tạp nhất — implement renderer generic dựa vào `data_type`, không hardcode field. Trend chart dùng recharts. Print prescription cần test với printer thật trước khi merge.

## Blockers

- TASK-017, TASK-007 (Visit), TASK-009 (Vitals), TASK-010 (Service), TASK-011 (Prescription), TASK-012 (Inventory để check stock)
