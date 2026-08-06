# Implementation Plan: TASK-138

**Task:** Payroll — thêm kiểu tính lương theo buổi / theo ca + chiết khấu cấu hình theo từng nhân sự
**Date:** 2026-08-06
**Based on:** khảo sát code `_dev-be` (payroll TASK-128, attendance/shift TASK-127) + phiên hỏi-đáp chốt yêu cầu với user 2026-08-06

---

## Locked decisions (user, 2026-08-06)

1. **"Buổi" = ngày công do admin tích** trên lưới chấm công ngày (`AttendanceDay`, TASK-127): cả ngày = 1.0, nửa ngày = 0.5. KHÔNG xây UI chấm buổi sáng/chiều/tối riêng. → `per_session` thực chất là **lương theo ngày công**: `đơn giá × attendance_worked_days`.
2. **Lương theo ca chỉ tính ca `completed`** — ca cancelled/scheduled-chưa-hoàn-thành không tính.
3. **Chiết khấu per-staff ở mức chi tiết**: mỗi nhân sự override được rate theo **từng loại thủ thuật** (service_type) + **rate thuốc riêng**; không cấu hình thì fallback rate chung (CommissionRule hiện tại, staff_id NULL).
4. **Priority: High.**
5. **Nhân sự KHÔNG có tài khoản đăng nhập** (điều dưỡng, y tá… — `staff_profile.user_id` NULL): admin quản lý và nhập liệu toàn bộ (chấm công, cấu hình lương, chốt lương). Mọi tính năng của task này phải hoạt động đầy đủ cho nhân sự không tài khoản:
   - Lương theo buổi/ca chỉ cần `staff_profile` + `AttendanceDay`/`Shift` (đều key theo `staff_id`, không cần `user_id`) → OK by design.
   - Cấu hình chiết khấu per-staff key theo `staff_id` (không phải user) → cấu hình được cho mọi nhân sự.
   - **Giới hạn kế thừa từ TASK-128**: việc *quy nguồn doanh thu* commission (thủ thuật/thuốc) resolve qua `visit.doctor_id`/`prescription.doctor_id` → chỉ nhân sự CÓ tài khoản (bác sĩ) mới được tính commission tự động. Nhân sự không tài khoản nếu cần chia chiết khấu → dùng `payroll_adjustment` thủ công (đã có từ TASK-128), KHÔNG mở rộng cơ chế quy nguồn trong task này.

## Approach

Mở rộng theo đúng kiến trúc TASK-128, không tạo bảng cấu hình lương mới:

- **Kiểu lương mới** thêm vào `staff_profile` (nơi đã giữ `pay_type`/`base_salary`/`hourly_rate`): 2 giá trị `pay_type` mới + 2 cột đơn giá. Engine `payroll_service._compute_one` thêm 2 nhánh tính `base_earned`.
- **Chiết khấu per-staff** thêm chiều `staff_id` (nullable) vào bảng `commission_rule` sẵn có — row `staff_id NULL` giữ nguyên nghĩa "rate chung toàn phòng khám". Resolve khi tính: rule (staff, service_type) → rule (service_type) → không có; thuốc: rule (staff, medicine) → rule medicine chung.

## Components

| Component | Action | Notes |
|-----------|--------|-------|
| `alembic/versions/0077_*.py` (BE) | create | Xem chi tiết migration bên dưới |
| `app/modules/hr/models/staff_profile.py` | modify | `pay_type` String(10)→String(20) (⚠️ `per_session` dài 11 ký tự); thêm `session_rate`, `shift_rate` Numeric(15,2) nullable |
| `app/modules/hr/models/commission_rule.py` | modify | Thêm `staff_id` UUID nullable FK `staff_profile.id` ondelete CASCADE; sửa docstring LOCKED DECISIONS |
| `app/modules/hr/schemas/staff_schemas.py` | modify | `PayType` literal + `session_rate`/`shift_rate` trong create/update/response |
| `app/modules/hr/services/payroll_service.py` | modify | 2 nhánh mới trong `_compute_one`; `per_session`: `session_rate × attendance_worked_days` (bắt buộc dùng attendance grid; không có dữ liệu grid → 0 công); `per_shift`: `shift_rate × completed_shifts`; OT = 0 cho 2 kiểu này (không áp dụng); allowance/attendance_bonus/late_penalty giữ nguyên logic |
| `app/modules/hr/services/timesheet_service.py` | modify | Bổ sung `completed_shifts` (đếm Shift status='completed' trong kỳ) vào dict timesheet |
| `app/modules/hr/services/commission_service.py` | modify | Resolve rate: ưu tiên rule có `staff_id` khớp, fallback rule `staff_id IS NULL` |
| `app/modules/hr/services/commission_config_service.py` + API routes | modify | CRUD rule nhận `staff_id` optional; list trả cả rule chung + rule riêng |
| Partial unique indexes (trong migration 0077) | modify | Thay 2 index cũ: `(clinic_id, service_type_id, COALESCE(staff_id,zero-uuid))` WHERE rule_type='service_type' AND NOT is_deleted; `(clinic_id, COALESCE(staff_id,zero-uuid))` WHERE rule_type='medicine' AND NOT is_deleted |
| FE `src/pages/hr/StaffFormPage.tsx` | modify | Select kiểu lương thêm "Theo buổi (ngày công)" / "Theo ca" + input đơn giá tương ứng |
| FE `src/pages/hr/PayrollPage.tsx` | modify | `PAY_TYPE_LABEL` thêm 2 kiểu (chuyển sang i18n key trong `hr.json` — xem nợ i18n 2026-08-06); breakdown hiển thị `số công/ca × đơn giá` |
| FE `src/pages/hr/CommissionKpiConfigPage.tsx` | modify | Section "Chiết khấu theo nhân sự": chọn nhân sự → bảng rate per service_type + rate thuốc; hiển thị rõ giá trị fallback (rate chung) khi chưa override |
| FE `src/modules/hr/api.ts` + types | modify | Types/params mới |
| `src/locales/vi/hr.json` + `en/hr.json` | modify | Key mới cho 2 kiểu lương, labels config per-staff |

## Implementation Steps

1. **Migration 0077** (branch từ `dev`, head hiện tại 0076): widen `staff_profile.pay_type` → String(20); add `session_rate`, `shift_rate`; add `commission_rule.staff_id` + FK + rebuild 2 partial unique indexes (drop cũ, tạo mới có chiều staff). Downgrade đầy đủ.
2. **BE models + schemas**: cập nhật `StaffProfile`, `CommissionRule`, `PayType` literal, staff schemas.
3. **BE engine**: `timesheet_service` thêm `completed_shifts`; `payroll_service._compute_one` thêm 2 nhánh (guard: đơn giá ≤ 0 → coi như chưa cấu hình lương, trả None như monthly/hourly hiện tại); payslip dict thêm `session_rate`/`shift_rate`/`completed_shifts` để FE hiển thị truy vết.
4. **BE commission resolve**: `commission_service` load rules per kỳ thành map `{(service_type_id, staff_id): rate}` + `{staff_id: medicine_rate}`; lookup ưu tiên staff-specific. `commission_config_service` + routes CRUD với `staff_id`.
5. **BE tests**: unit cho 2 nhánh lương mới (kể cả half-day 0.5, không có attendance data, đơn giá 0), resolve rate per-staff/fallback, regression monthly/hourly + commission chung không đổi.
6. **FE**: StaffFormPage (select + đơn giá), PayrollPage (label i18n + breakdown), CommissionKpiConfigPage (per-staff section), api/types, locales vi+en.
7. **FE tests**: form save 2 kiểu mới, PayrollPage render breakdown, config page override + fallback display.
8. Smoke test DB thật (docker e2e) như quy trình TASK-128.

## Dependencies

- Không thêm thư viện mới. Phụ thuộc dữ liệu: attendance grid (TASK-127) phải được chấm thì `per_session` mới ra công — ghi rõ trong tài liệu người dùng.

## Risks / Notes

- ⚠️ `pay_type` đang là `String(10)` — `per_session` (11 ký tự) sẽ tràn nếu quên widen cột (bước 1).
- Nhân sự `per_session`/`per_shift` **không có OT** trong scope này (OT gắn với giờ/tháng); nếu cần sau này tách task riêng.
- Đổi partial unique index trên `commission_rule` phải giữ được rows hiện có (staff_id NULL) — dùng COALESCE với zero-uuid để NULL không thoát uniqueness.
- Claw-back (TASK-128) không đổi — chỉ điểm resolve rate thay đổi.
- FE config per-staff: danh sách chọn nhân sự phải lấy từ `staff_profile` (toàn bộ nhân sự active, kể cả không có tài khoản) — KHÔNG lấy từ danh sách user. Với nhân sự không tài khoản, UI nên hiển thị ghi chú "commission tự động chỉ áp dụng khi có tài khoản bác sĩ gắn với hồ sơ".
- Alembic: đánh số 0077 sau khi rebase lên `dev` mới nhất — tránh đụng số như sự cố 092/093/094 trước đây.
