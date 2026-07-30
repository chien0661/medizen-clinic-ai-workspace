---
id: TASK-131
type: feature
title: "Danh mục thuốc: cấu hình đơn vị dùng + liều dùng mặc định / mỗi thuốc"
status: IN_REVIEW
priority: Medium
assigned: Code Review Agent
created: 2026-07-31
updated: 2026-07-31
branch: "feature/TASK-131"
tags: [inventory, medicines, prescriptions, dosage, feature]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-131/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-131: Đơn vị dùng + liều dùng mặc định trong Danh mục thuốc

**Nguồn:** Yêu cầu 2026-07-31 (mở rộng TASK-124/129). Bổ sung cấu hình kê-đơn cho từng thuốc trong Danh mục thuốc.

## Description
Thêm 2 trường cấu hình cho mỗi thuốc trong **Danh mục thuốc** (MedicinesPage):
- **Đơn vị dùng** (`usage_unit`, nullable) — đơn vị dùng khi **kê đơn** (vd "gói", "ml", "viên"), tách biệt với `sell_unit` (đơn vị bán) và `purchase_unit` (đơn vị nhập). Khi kê đơn, ưu tiên gợi ý theo `usage_unit` nếu có.
- **Liều dùng mặc định** (`default_dosage`, nullable text) — chuỗi liều dùng gợi ý sẵn (vd "1 viên x 2 lần/ngày"), **auto-fill** ô "Liều dùng" khi bác sĩ chọn thuốc (vẫn sửa được).

## Requirements
- [x] BE: thêm cột `usage_unit` (str, nullable) + `default_dosage` (str, nullable) vào model `Medicine` + migration **0074** (down_revision head hiện tại 0073; additive). Schemas Create/Update/Response + medicine_search response.
- [x] BE: API create/update medicine nhận 2 trường; medicine-search trả `usage_unit` + `default_dosage` để FE kê đơn dùng.
- [x] FE MedicinesPage: form thêm/sửa có ô "Đơn vị dùng" + "Liều dùng mặc định"; hiển thị ở list nếu hợp lý. (Quyết định: không thêm cột bảng — bảng đã có 12 cột, `sell_unit` cũng chỉ ở form, không ở bảng, giữ nhất quán.)
- [x] FE PrescriptionTab `addMedicine`: `unit` ưu tiên `usage_unit || sell_unit || dosage_form_unit || base_unit`; prefill `dosage` = `default_dosage ?? ""` (vẫn cho sửa).
- [x] Không hồi quy luồng kê đơn/in (TASK-124/129) + import CSV medicines.

## Acceptance Criteria
- [x] Cấu hình được đơn vị dùng + liều dùng mặc định cho từng thuốc (BE+FE), lưu + hiển thị lại đúng.
- [x] Kê đơn: chọn thuốc → đơn vị gợi ý theo `usage_unit`, ô liều dùng prefill `default_dosage`; sửa tay vẫn được.
- [x] Unit test (BE) + FE test; migration additive an toàn. DB-integration/e2e test KHÔNG chạy (không dựng stack DB theo chỉ định task) — xem chi tiết trong api-spec §7.

## Progress Checklist
- [x] Planning | [x] Implementation | [ ] Code Review | [ ] Testing | [ ] Documentation

## Notes / Dependencies
- Xây trên TASK-124 (sell_unit/unit_conversion) + TASK-129 (prescribing/print). `PrescriptionTab.tsx addMedicine` (~dòng 667-733): điểm tích hợp unit + dosage prefill.
- Migration mới = **0074** (head dev hiện tại 0073).

## Blockers
Không.
