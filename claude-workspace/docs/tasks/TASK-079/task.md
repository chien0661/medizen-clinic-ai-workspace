---
id: TASK-079
type: feature
title: "Sinh hiệu động — form nhập theo cấu hình + lưu trạng thái bình thường/không bình thường có cấu trúc"
status: IN_REVIEW
priority: High
assigned: Code Review Agent
created: 2026-06-16
updated: 2026-06-16
branch: "feature/TASK-079-dynamic-vitals"
jira_key: ""
tags: [vitals, frontend, backend, migration]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-079/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-079: Sinh hiệu động — form nhập theo cấu hình + lưu trạng thái BT/không BT có cấu trúc

## Description

Module **vitals** đã có sẵn nền tảng cấu hình động ở backend và màn admin:

- `vital_field_definition` (key, label, unit, `min_value`/`max_value`, `warning_min`/`warning_max`, `is_required`, `sort_order`, `group_name`, `data_type`), có schema versioning (`vital_schema_version`) và preset theo chuyên khoa (`system_vital_preset`).
- Màn admin `/admin/vitals` (`clinic-cms-web/src/pages/admin/VitalsPage.tsx`) cho phép thêm/sửa/xoá/sắp xếp chỉ số, đặt khoảng bình thường, xem lịch sử phiên bản, reset theo chuyên khoa.

**Vấn đề (gap):** Form nhập sinh hiệu của bác sĩ chưa dùng cấu hình động và chưa lưu trạng thái có cấu trúc:

1. `clinic-cms-web/src/components/doctor/VitalsTab.tsx` **HARDCODE 6 chỉ số** (`VITAL_FIELDS`, dòng 24-31) và khoảng bình thường (`NORMAL_RANGES`, dòng 18-22) — **không** đọc từ `GET /api/v1/vitals/definitions`. Admin cấu hình thêm/sửa chỉ số nhưng form nhập + timeline vẫn chỉ hiển thị 6 chỉ số cố định (timeline cũng lặp `VITAL_FIELDS`, dòng 177).
2. Trạng thái **bình thường / không bình thường** chỉ được nhét vào chuỗi text `notes` khi lưu (`buildNotes()`, dòng 98-111). `POST /visits/{id}/vitals` chỉ nhận `{ values, notes }`. BE (`visit_vitals`) **không có trường có cấu trúc** cho cờ normal/abnormal hay ghi chú riêng từng chỉ số → không lọc/thống kê/tô màu lại khi xem history được.

**Mục tiêu:** Nối form nhập (và timeline) vào cấu hình động, và lưu trạng thái BT/không-BT + ghi chú từng chỉ số **có cấu trúc** xuống BE.

## Requirements

### Backend (`clinic-cms`)
- [ ] Bổ sung lưu trạng thái có cấu trúc per-field trên `visit_vitals`. **Đề xuất**: 2 cột JSONB `field_status` (`{ "<key>": "normal" | "abnormal" }`) và `field_notes` (`{ "<key>": "<note>" }`) — hoặc gộp thành `annotations` (`{ "<key>": { "status", "note" } }`). Chốt cách tiếp cận ở bước `/task-plan`.
- [ ] Alembic migration mới (head hiện tại = `0040_create_advice_template` → migration kế tiếp `0041_*`), tuân thủ pattern RLS của module. Nullable / default rỗng để **tương thích ngược** dữ liệu cũ.
- [ ] Cập nhật `VisitVitalsCreate` / `VisitVitalsResponse` (`schemas/vitals_schemas.py`) thêm field_status / field_notes (optional).
- [ ] Validator (`validator_service.py`): status chỉ nhận `{normal, abnormal}`; key trong field_status/field_notes phải tồn tại trong định nghĩa active; không phá luồng validate hiện tại.
- [ ] Service (`vitals_service.py`) persist + trả về các trường mới.

### Frontend (`clinic-cms-web`)
- [ ] `VitalsTab.tsx`: thay `VITAL_FIELDS` hardcode bằng dữ liệu từ `doctorApi.getVitalDefinitions()`. Render input theo `data_type` (number/integer/text/boolean/select + options), hiển thị `unit`, `placeholder`/`help_text`, nhóm theo `group_name`, sắp xếp theo `sort_order`, đánh dấu `is_required`.
- [ ] Tự đánh giá BT/không-BT theo `min_value`/`max_value` + `warning_min`/`warning_max` của **định nghĩa** (bỏ `NORMAL_RANGES` hardcode); vẫn cho phép bác sĩ toggle thủ công.
- [ ] Khi lưu: gửi `values` + `field_status` + `field_notes` **có cấu trúc** (không nối chuỗi vào `notes`).
- [ ] Timeline xem lại: render động theo định nghĩa (ưu tiên snapshot theo `schema_version` của record để hiển thị đúng chỉ số đã đo), tô màu BT/không-BT + hiện ghi chú từng chỉ số.
- [ ] Xử lý trường hợp chưa cấu hình schema (đã có key i18n `vitals.noSchemaError`).
- [ ] BMI: giữ tính dẫn xuất khi có height/weight (nếu định nghĩa có các key tương ứng).

### Tài liệu / i18n
- [ ] Bổ sung i18n key mới (nếu có) cho EN + VI.
- [ ] Cập nhật final-spec mô tả mô hình lưu trạng thái + hành vi form động.

## Acceptance Criteria

- [ ] Admin thêm 1 chỉ số mới ở `/admin/vitals` → form nhập của bác sĩ và timeline **tự hiển thị** chỉ số đó, không sửa code FE.
- [ ] Trạng thái BT/không-BT và ghi chú từng chỉ số được **lưu có cấu trúc** và đọc lại đúng sau reload (không phụ thuộc parse chuỗi `notes`).
- [ ] Đánh giá BT/không-BT lấy ngưỡng từ định nghĩa cấu hình, không còn range hardcode trong FE.
- [ ] Dữ liệu vitals cũ (trước migration) vẫn đọc/hiển thị bình thường (không lỗi do thiếu field mới).
- [ ] BE: unit test validator (status hợp lệ/không hợp lệ, key lạ) + integration test real-DB (POST/GET round-trip field_status/field_notes) PASS.
- [ ] FE: vitest cho `VitalsTab` (render động theo definitions, build payload có cấu trúc, hiển thị trạng thái) PASS.
- [ ] `ruff check` + `mypy` (BE) và `lint` + `type-check` (FE) PASS.

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-079/refs/` *(DetailDesign, SRS, implementation-plan)*
- **Code (BE)**: `clinic-cms/app/modules/vitals/` (`models/visit_vitals.py`, `schemas/vitals_schemas.py`, `services/vitals_service.py`, `services/validator_service.py`, `api/routes.py`), `clinic-cms/alembic/versions/0041_*.py`
- **Code (FE)**: `clinic-cms-web/src/components/doctor/VitalsTab.tsx`, `clinic-cms-web/src/components/doctor/VitalsTrendChart.tsx`, `clinic-cms-web/src/modules/doctor/api.ts`
- **Tests**: `docs/tasks/TASK-079/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-079/handoff/`
- **Test Report**: `docs/tasks/TASK-079/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-079/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-079/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-06-16
- **Implementation Completed**: 2026-06-16

## Notes

- Liên quan/tiền đề: TASK-009 (Vital Schema editor admin), TASK-041 (BE endpoint trend chart — đang TODO).
- Nền tảng động đã tồn tại; task này chủ yếu **nối FE vào cấu hình động** + **mở rộng lưu trạng thái có cấu trúc** ở BE, không xây mới module.
- Quyết định cần chốt ở `/task-plan`: cột tách (`field_status` + `field_notes`) vs gộp (`annotations`). Khuyến nghị: 2 cột JSONB tách để query/filter `field_status` bằng GIN dễ hơn.
- Migration kế tiếp dự kiến `0041_*` (head hiện tại `0040_create_advice_template`).

## Blockers

None
