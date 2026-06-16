---
id: TASK-080
type: feature
title: Cập nhật & cấu hình template in đơn thuốc theo mẫu phòng khám
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-06-16
updated: 2026-06-16
completed: 2026-06-16
branch: "feature/TASK-080-prescription-template"
jira_key: ""
tags: [frontend, print, prescription, clinic-settings, template]
affected-repos: [clinic-cms-web, clinic-cms]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-080/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - docs/tasks/TASK-080/refs/prescription-template-sample.png
---

# TASK-080: Cập nhật & cấu hình template in đơn thuốc theo mẫu phòng khám

## Description

Khi in đơn thuốc, bản in hiện tại (`PrintablePrescription.tsx`, TASK-047 — bố cục "Phiếu Khám Bệnh" A5 dạng bảng) **không khớp** với mẫu đơn thuốc thực tế phòng khám yêu cầu.

Mẫu yêu cầu (xem ảnh `refs/prescription-template-sample.png`) là **"ĐƠN THUỐC"** với bố cục:

- **Header (trái):** Tên phòng khám + Địa chỉ (vd: "Phòng khám chuyên khoa Nhi Dr Trường Medi" / "Địa chỉ: R21-Eurowindow River Park").
- **Tiêu đề (giữa):** **ĐƠN THUỐC**.
- **Thông tin bệnh nhân:**
  - Họ tên
  - Ngày sinh — **Cân nặng (kg)** — Giới tính (Nam/Nữ) *(trên cùng một dòng)*
  - Địa chỉ
  - **Chẩn đoán**
  - **Thuốc điều trị:**
- **Danh sách thuốc:** đánh số **1 → 6** dạng dòng kẻ chấm (free-form, KHÔNG phải bảng có cột SL/Đơn vị như hiện tại).
- **Lời dặn (chân trang, có dấu `*`):**
  - `*Lời dặn: Uống thuốc đúng liều, đúng giờ theo đơn; theo dõi sốt, ăn uống và các dấu hiệu bất thường (sốt cao không hạ, khó thở, lì bì, nôn nhiều).`
  - `*Tái khám sau 03 ngày hoặc đưa trẻ đi khám ngay nếu có triệu chứng nặng hơn.`
- **Chữ ký (phải):** ngày giờ + thứ + ngày in (vd "00:14 Thứ Năm, 05 Tháng Ba 2026") + "Bác sỹ/Y sỹ khám bệnh" + tên bác sĩ có học hàm/chức danh (vd "Ths.Bs Lê Mạnh Trường").
- **Chân trang cuối:**
  - `- Khám bệnh lại xin mang theo đơn này.`
  - `- Số điện thoại liên hệ: 0353334009`

Phần 2 của yêu cầu: **cho phép cấu hình template đơn thuốc** — các nội dung cố định (header phòng khám, lời dặn, ghi chú chân trang, chức danh bác sĩ, SĐT liên hệ, có/không hiển thị cân nặng…) phải lấy từ cấu hình phòng khám/template thay vì hard-code, để mỗi phòng khám tự chỉnh được.

## Requirements

### A. Cập nhật bản in theo mẫu
- [ ] Đổi bố cục bản in đơn thuốc theo mẫu "ĐƠN THUỐC" trong `refs/prescription-template-sample.png` (header trái, tiêu đề ĐƠN THUỐC, danh sách thuốc đánh số dạng dòng kẻ chấm).
- [ ] Bổ sung field **Cân nặng (kg)** và **Chẩn đoán** vào bản in (lấy từ sinh hiệu/visit nếu có — xem TASK-079 dynamic vitals cho cân nặng).
- [ ] Hiển thị ngày sinh — cân nặng — giới tính trên cùng một dòng; địa chỉ bệnh nhân.
- [ ] Block lời dặn (`*Lời dặn…`, `*Tái khám…`) + ghi chú chân trang (mang theo đơn, SĐT liên hệ).
- [ ] Block chữ ký: ngày giờ + thứ tiếng Việt + chức danh bác sĩ + tên.

### B. Cấu hình template
- [ ] Các text cố định lấy từ cấu hình (clinic settings / prescription template config), không hard-code: header phòng khám, mặc định lời dặn, mặc định tái khám, ghi chú chân trang, SĐT liên hệ, chức danh + tên bác sĩ ký.
- [ ] Màn hình/khu vực cấu hình template đơn thuốc (Admin → Cấu hình) để chỉnh các nội dung trên + preview.
- [ ] (Quyết định khi plan) Lưu cấu hình ở đâu: clinic settings hiện có (BE `clinic-cms`) hay bảng/JSON template riêng. Có thể cần endpoint BE + migration.
- [ ] Số dòng thuốc tối thiểu hiển thị (mẫu có sẵn 1–6 dòng trống) — cấu hình được hoặc auto theo số thuốc thực tế.

### C. Tích hợp
- [ ] Thay/điều hướng từ `PrintPrescriptionModal` + nút in trong `PrescriptionTab` sang template mới.
- [ ] Liên quan BUG-077-004 (chưa có route in đơn thuốc sau khi hoàn tất khám) — đảm bảo có lối in đơn thuốc từ luồng kết thúc khám.

## Acceptance Criteria

- [x] Bản in đơn thuốc trên giấy khớp bố cục mẫu `prescription-template-sample.png` (kiểm tra print preview A5/A4).
- [x] Sửa header/lời dặn/SĐT/chức danh bác sĩ trong cấu hình → bản in cập nhật theo, không cần đổi code.
- [x] Cân nặng + chẩn đoán hiển thị đúng khi visit có dữ liệu; ẩn/để trống gọn gàng khi không có.
- [x] Unit test FE cho component bản in mới + cấu hình; không phá vỡ test hiện có (PrintablePrescription.test.tsx cập nhật theo).
- [x] E2E: kê đơn → in → kiểm tra nội dung theo template + theo cấu hình.

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [x] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-080/refs/` *(prescription-template-sample.png)*
- **Code**: (feature branch)
  - FE: `clinic-cms-web/src/components/doctor/PrintablePrescription.tsx` *(cập nhật)*
  - FE: `clinic-cms-web/src/components/doctor/PrintPrescriptionModal.tsx`, `PrescriptionTab.tsx`
  - FE: `clinic-cms-web/src/components/billing/PrintPrescriptionModal.tsx` *(bản billing — kiểm tra trùng lặp)*
  - FE: màn cấu hình template (Admin)
  - BE (nếu cần): `clinic-cms/app/modules/<clinic settings>` + migration template config
- **Tests**: `docs/tasks/TASK-080/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-080/handoff/`
- **Test Report**: `docs/tasks/TASK-080/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-080/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-080/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-06-16
- **Implementation Completed**: 2026-06-16
- **Review Completed**: 2026-06-16
- **Testing Failed**: 2026-06-16
- **Bug Fixed**: 2026-06-16 -- BUG-080-001 resolved (commit 0b29fbc); back to IN_TESTING — BUG-080-001 (Critical): `_build_settings_response` missing `prescription_template` field → HTTP 500 on all settings endpoints
- **Testing Completed**: 2026-06-16 -- All 97 tests PASS; BUG-080-001 RESOLVED; E2E verified (Settings tab + PrintPrescriptionModal); status → DOCUMENTING

## Notes

- **Mẫu tham chiếu**: `refs/prescription-template-sample.png` — là nguồn chân lý cho bố cục.
- **Hiện trạng**: `PrintablePrescription.tsx` đang là layout "Phiếu Khám Bệnh" dạng bảng (TASK-047, IN_REVIEW). Mẫu mới là "ĐƠN THUỐC" dạng dòng kẻ chấm → đây là thay đổi bố cục đáng kể, không chỉ chỉnh chữ.
- **Cân nặng**: lấy từ sinh hiệu động (TASK-079) — phối hợp lấy field weight.
- **Liên quan**: TASK-047 (print foundation, A5/A4 native print), TASK-051 (4 print template FE), BUG-077-004 (thiếu route in đơn thuốc sau khám).
- **Cần làm rõ khi plan**: nơi lưu cấu hình template (clinic settings vs bảng riêng), phạm vi BE.

## Blockers

None
