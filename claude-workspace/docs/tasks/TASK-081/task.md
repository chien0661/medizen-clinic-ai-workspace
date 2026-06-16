---
id: TASK-081
type: feature
title: PHẦN KHÁM BỆNH — form khám lâm sàng động (BT/Bất thường + ghi chú) + seed 13 mục
status: IN_REVIEW
priority: High
assigned: Code Review Agent
created: 2026-06-16
updated: 2026-06-17
branch: "feature/TASK-081-examination-section"
jira_key: ""
tags: [frontend, backend, emr, examination, vitals, seed]
affected-repos: [clinic-cms-web, clinic-cms]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-081/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - docs/tasks/TASK-081/refs/examination-section-sample.png
---

# TASK-081: PHẦN KHÁM BỆNH — form khám lâm sàng động + seed 13 mục

## Description

Bổ sung khu vực **"PHẦN KHÁM BỆNH"** trong hồ sơ khám (EMR/consultation) theo mẫu `refs/examination-section-sample.png`: danh sách các mục khám, mỗi mục đánh dấu **Bình thường / Bất thường** kèm ô **ghi chú** (hiện khi Bất thường). Mục cuối (dấu hiệu màng não) dùng nhãn **Âm tính / Dương tính**.

Cấu trúc này trùng khít cơ chế `field_status` (normal/abnormal) + `field_notes` đã có ở **vitals động (TASK-079)**. Theo quyết định plan: **mở rộng module vitals** — thêm nhóm định nghĩa `kham_benh` (data_type dạng trạng thái, không nhập số) + **seed 13 mục mặc định**, tái dùng tối đa model/service/schema/field_status/field_notes sẵn có.

13 mục mặc định (theo ảnh mẫu):

| # | Mục | Kiểu trạng thái |
|---|-----|-----------------|
| 1 | Tri giác | Bình thường / Bất thường |
| 2 | Da niêm mạc | Bình thường / Bất thường |
| 3 | Hạch ngoại vi | Bình thường / Bất thường |
| 4 | Tim | Bình thường / Bất thường |
| 5 | Phổi | Bình thường / Bất thường |
| 6 | Bụng | Bình thường / Bất thường |
| 7 | Da | Bình thường / Bất thường |
| 8 | Thóp (nếu có) | Bình thường / Bất thường |
| 9 | Tai phải | Bình thường / Bất thường |
| 10 | Tai trái | Bình thường / Bất thường |
| 11 | Mũi | Bình thường / Bất thường |
| 12 | Họng | Bình thường / Bất thường |
| 13 | Dấu hiệu màng não | Âm tính / Dương tính |

## Requirements

### A. Backend (mở rộng vitals)
- [ ] Cho phép định nghĩa field dạng "khám" (trạng thái, không có giá trị số) — thêm `data_type` mới (vd `exam_status`) hoặc cờ tương đương, gom theo `group_name = "kham_benh"`.
- [ ] Hỗ trợ nhãn trạng thái tùy biến cho mục 13 (Âm tính/Dương tính) thay vì Bình thường/Bất thường mặc định.
- [ ] **Seed 13 mục mặc định** (system, clinic_id NULL, is_system=true) qua migration — theo pattern dosage_form (TASK-076), uuid5 deterministic, sort_order 1..13.
- [ ] Lưu kết quả khám vào `visit_vitals.field_status` + `field_notes` (cùng record với sinh hiệu) — không tạo bảng mới. Validate options.

### B. Frontend
- [ ] Render section "PHẦN KHÁM BỆNH" trong consultation/EMR (đọc definitions lọc theo `group_name='kham_benh'`), mỗi mục toggle BT/Bất thường (nhãn tùy biến cho mục 13) + ghi chú khi bất thường.
- [ ] Submit field_status/field_notes các mục khám cùng luồng lưu vitals; hiển thị lại khi xem record cũ (timeline).
- [ ] i18n vi/en.

### C. Tích hợp
- [ ] Tận dụng quyền hiện có của vitals (không thêm permission mới nếu thuộc vitals).
- [ ] (Cân nhắc) Hiển thị/in phần khám bệnh trong các bản in liên quan nếu phù hợp.

### D. Cấu hình hiển thị + versioning (yêu cầu bổ sung 2026-06-16)
- [ ] **Chọn hiển thị**: Admin chọn được những mục khám (checklist) + chỉ số sinh hiệu nào hiển thị cho phần khám (mỗi phòng khám). Tận dụng CRUD `vital_field_definition` + cờ `is_active` + quyền `vital.manage` đã có; mở rộng "Vital Schema Editor" (TASK-023) để gồm nhóm `kham_benh`.
- [ ] **Áp dụng cho lượt khám mới**: thay đổi cấu hình tạo schema version mới (cơ chế `VitalSchemaVersion` + `_snapshot_current_definitions` đã có); lượt khám mới ghi `visit_vitals.schema_version = version hiện tại`.
- [ ] **Lượt khám cũ giữ nguyên**: xem lại lượt khám cũ phải render theo **snapshot của `schema_version` đã ghi trong record đó**, KHÔNG theo bộ definitions active hiện tại → bộ chỉ số/nhãn cũ vẫn hiệu lực. (Verify FE timeline hiện đang render theo snapshot hay theo active — vá nếu đang theo active.)

## Acceptance Criteria

- [ ] Form khám hiển thị đủ 13 mục đúng thứ tự + nhãn theo mẫu (mục 13 Âm/Dương tính).
- [ ] Đánh dấu Bất thường → hiện ô ghi chú; lưu + tải lại đúng trạng thái và ghi chú.
- [ ] Seed 13 mục có sẵn cho phòng khám mới (system definitions); phòng khám có thể tùy biến (thêm/ẩn/sửa) theo cơ chế definitions.
- [ ] Admin chọn được mục khám + chỉ số sinh hiệu nào hiển thị (toggle is_active) → tạo schema version mới.
- [ ] Lượt khám MỚI dùng cấu hình mới; lượt khám CŨ mở lại vẫn hiển thị đúng bộ chỉ số/nhãn tại thời điểm khám (theo `schema_version` đã ghi).
- [ ] Unit test BE (schema/seed/service/version snapshot có gồm field khám) + FE (component) ; không phá vỡ test vitals/TASK-079.
- [ ] E2E: mở consultation → khám → đánh dấu BT/Bất thường + ghi chú → lưu → tải lại đúng; đổi cấu hình → lượt mới đổi theo, lượt cũ giữ nguyên.

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-081/refs/` *(examination-section-sample.png, implementation-plan.md)*
- **Code**: (feature branch)
  - BE: `clinic-cms/app/modules/vitals/` (definitions model/schema/service + migration seed)
  - FE: `clinic-cms-web/src/components/doctor/` (section khám trong consultation; tham chiếu VitalsTab)
- **Tests**: `docs/tasks/TASK-081/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-081/handoff/`
- **Test Report**: `docs/tasks/TASK-081/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-081/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-081/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-06-16
- **Implementation Completed**: 2026-06-17
- **Review (1) — CHANGES_REQUESTED**: 2026-06-17 (1 MAJOR: FE old-visit snapshot rendering, criterion D)

## Notes

- **Mẫu tham chiếu**: `refs/examination-section-sample.png`.
- **Quyết định kiến trúc**: mở rộng vitals (nhóm `kham_benh`), KHÔNG tạo module riêng — tái dùng field_status/field_notes (TASK-079).
- **Seed**: theo pattern TASK-076 dosage_form (migration seed, system row clinic_id NULL).
- **Migration**: 0042 đã dùng (TASK-080 user.title) → migration mới dự kiến **0043** (verify head trước khi đặt số).
- **Base branch**: main hiện đã chứa TASK-079 + TASK-080.

## Blockers

None
