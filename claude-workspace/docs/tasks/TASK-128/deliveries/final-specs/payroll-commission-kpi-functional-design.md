# Thiết Kế Chi Tiết Tính Năng: Payroll — Chiết khấu (Commission) + KPI + Claw-back

**Dự án:** Clinic CMS
**Task:** TASK-128
**Phiên bản:** 1.0
**Ngày:** 2026-07-30
**Người thực hiện:** Code Implementation Agent
**Trạng thái:** Đã triển khai (BE + FE) — chờ Code Review / Test
**Tài liệu liên quan:** TASK-125 (service_type), TASK-127 (attendance/worked_days), migration 0058 (staff_salary_config + payroll.manage), implementation-plan.md, task.md

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-07-30 | Phiên bản đầu tiên — hoàn tất Implementation, sẵn sàng Review |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Danh sách API](#3-danh-sách-api)
- [4. Cấu trúc cơ sở dữ liệu](#4-cấu-trúc-cơ-sở-dữ-liệu)
- [5. Quy tắc nghiệp vụ](#5-quy-tắc-nghiệp-vụ)
- [6. Xử lý lỗi](#6-xử-lý-lỗi)
- [7. Giao diện người dùng](#7-giao-diện-người-dùng)
- [8. Ghi chú và lưu ý khi kiểm thử](#8-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Payroll hiện có (migration 0058 + `payroll_service.compute_payroll`) chỉ tính lương cơ bản/công + OT + phụ cấp/thưởng/phạt chuyên cần. TASK-128 bổ sung 3 cấu phần còn thiếu theo yêu cầu nghiệp vụ (chốt 2026-07-30):

- **Chiết khấu thủ thuật** — % theo **loại dịch vụ** (`service_type`, TASK-125), trả cho **bác sĩ khám** (`visit.doctor_id`).
- **Chiết khấu thuốc** — % trên **doanh thu thuốc**, trả cho **bác sĩ kê đơn** (`prescription.doctor_id`).
- **KPI** — chỉ tiêu doanh số/nhân sự/kỳ → thưởng theo **mức đạt** (tỷ lệ đạt/chỉ tiêu, không phải ngưỡng đạt/không).
- **Claw-back** — khi một hóa đơn thuộc kỳ **đã chốt lương** (đã "Ghi vào chi phí") bị hủy/hoàn tiền, hệ thống tự động tạo một điều chỉnh âm, trừ vào lương **kỳ kế tiếp** của (các) bác sĩ liên quan.

### 1.2 Phạm vi

**Bao gồm:**
- Model + migration `0073`: `commission_rule`, `kpi_target`, `payroll_adjustment`.
- `commission_service` — tổng hợp doanh thu thủ thuật (theo `service_type`) + doanh thu thuốc theo kỳ, nhân với rate cấu hình, quy đổi bác sĩ (`user.id`) → nhân sự (`staff_profile.id`) qua `staff_profile.user_id`.
- `kpi_service` — tính thưởng KPI theo tỷ lệ đạt.
- Hook claw-back trong `billing/services/invoice_service.py` (`void_invoice`, `refund_invoice`).
- Tích hợp vào `payroll_service.compute_payroll`/`_compute_one` — payslip có thêm 4 trường: `procedure_commission`, `medicine_commission`, `kpi_bonus`, `clawback_adjustment`.
- API CRUD `/hr/commission-rules`, `/hr/kpi-targets` (quyền `payroll.manage` — không thêm quyền mới).
- FE: `PayrollPage.tsx` hiển thị breakdown 4 cột mới; trang mới `CommissionKpiConfigPage.tsx` (`/hr/commission-kpi`) để cấu hình rate + chỉ tiêu KPI.

**Không bao gồm:**
- Vá `visit_service.performed_by_user_id` (NULL-prone) — **chốt quyết định KHÔNG dùng trường này**, dùng `visit.doctor_id` thay thế.
- Thuế/BHXH trừ lương (đã ngoài phạm vi từ engine payroll gốc — v1).
- Bậc thang KPI nhiều mức (multi-tier) — v1 dùng công thức tuyến tính theo tỷ lệ đạt, xem mục 5.

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **HR/Admin (`payroll.manage`)** | Cấu hình rate chiết khấu, chỉ tiêu KPI; xem/chốt bảng lương. |
| **Bác sĩ (nhận chiết khấu/KPI)** | Không tương tác trực tiếp — chỉ nhận kết quả qua payslip; yêu cầu có `staff_profile.user_id` liên kết để nhận tự động. |
| **Billing (TASK-105/112/119 — void/refund)** | Nguồn kích hoạt claw-back — không cần thay đổi UI/luồng nghiệp vụ billing, chỉ có thêm side-effect ghi `payroll_adjustment`. |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
[Admin cấu hình] ──► commission_rule (rate% theo service_type_id + rate% thuốc)
                 ──► kpi_target (staff_id, period, revenue_target, bonus_amount)
                        │
                        ▼
[GET /hr/payroll?month=] ──► payroll_service.compute_payroll
   │                              │
   │                              ├─► commission_service.compute_commission
   │                              │      (visit_service × service_type rate + prescription_item × medicine rate,
   │                              │       group by doctor → map user.id→staff_profile.id)
   │                              ├─► kpi_service.compute_kpi_bonuses
   │                              │      (doanh thu bác sĩ đã tính ở trên vs kpi_target → bonus theo tỷ lệ đạt)
   │                              └─► payroll_adjustment (SUM theo apply_period) — claw-back kỳ trước dồn vào kỳ này
   ▼
payslip = base+OT+phụ cấp... (đã có) + procedure_commission + medicine_commission + kpi_bonus + clawback_adjustment

[POST /hr/payroll/post-to-expense] ──► ghi Expense(category='salary') ── đây là tín hiệu "khóa kỳ"
                                        (đồng thời đánh dấu payroll_adjustment.applied=true cho kỳ đó)

[Billing: void/refund invoice] ──► invoice_service.void_invoice/refund_invoice
        │
        ▼
   payroll_service.record_invoice_clawback
        │  1. Lấy visit.doctor_id + visit_date (kỳ nguồn)
        │  2. Nếu kỳ đó CHƯA "khóa" (chưa post-to-expense) → không làm gì (sửa bình thường)
        │  3. Nếu ĐÃ khóa → tính lại chiết khấu mà các dòng hóa đơn này đã tạo ra
        │     (join invoice_line → visit_service/prescription_item → rate hiện tại)
        │  4. Ghi payroll_adjustment ÂM, apply_period = kỳ_nguồn + 1 tháng
        │     (idempotent theo (clinic_id, staff_id, source_ref=invoice_id))
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Cấu hình rate | Admin vào `/hr/commission-kpi`: chọn loại dịch vụ → nhập rate% (per service_type); nhập rate% thuốc (1 rate chung); thêm chỉ tiêu KPI cho từng nhân sự/kỳ. |
| 2 | Tính lương kỳ | `GET /hr/payroll?month=` gọi `compute_payroll`: với mỗi nhân sự, cộng thêm commission + KPI bonus + claw-back (nếu có) vào gross/net đã tính từ base+OT+phụ cấp. |
| 3 | Nhân sự chỉ nhận chiết khấu (không có lương cơ bản) | Nếu `_compute_one` trả về `None` (chưa cấu hình `base_salary`/`hourly_rate`) nhưng có commission/KPI/claw-back ≠ 0, hệ thống vẫn tạo payslip "rỗng" (`_empty_slip`) để không mất khoản chiết khấu. |
| 4 | Chốt lương | `POST /hr/payroll/post-to-expense` ghi 1 dòng Expense (idempotent theo tháng) — đây là tín hiệu duy nhất để hệ thống biết kỳ đã "khóa" (không có bảng `payroll_period` riêng). |
| 5 | Hủy/hoàn hóa đơn sau khi đã khóa kỳ | `void_invoice`/`refund_invoice` gọi `record_invoice_clawback`: nếu kỳ nguồn (theo `visit.visit_date`) đã khóa, tính lại đúng số tiền chiết khấu mà các dòng hóa đơn (dịch vụ + thuốc) đã đóng góp, ghi âm vào `payroll_adjustment` cho kỳ **kế tiếp**. Best-effort — không bao giờ chặn luồng void/refund. |
| 6 | Nhân sự không có tài khoản liên kết | Nếu bác sĩ (`visit.doctor_id`/`prescription.doctor_id`) không có `staff_profile.user_id` tương ứng, khoản chiết khấu bị **bỏ qua** (không tính vào payroll của ai) và được ghi log cảnh báo (`commission.unmapped_doctors`) — không có API riêng hiển thị danh sách "chưa gắn" trong v1 (xem Hạn chế). |

---

## 3. Danh sách API

**Đường dẫn gốc (Base Path):** `/api/v1`. Tất cả yêu cầu `Authorization: Bearer {token}` + quyền `payroll.manage`.

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt |
|-----|------------|-----------|--------------|
| 1 | GET | `/api/v1/hr/payroll?month=YYYY-MM` | *(đã có, mở rộng)* Payslip có thêm 4 trường chiết khấu/KPI/claw-back |
| 2 | POST | `/api/v1/hr/payroll/post-to-expense?month=YYYY-MM` | *(đã có, mở rộng)* Đồng thời đánh dấu `payroll_adjustment.applied=true` cho kỳ |
| 3 | GET | `/api/v1/hr/commission-rules` | Danh sách cấu hình chiết khấu (theo loại DV + thuốc) |
| 4 | POST | `/api/v1/hr/commission-rules` | Tạo cấu hình chiết khấu mới |
| 5 | PATCH | `/api/v1/hr/commission-rules/{id}` | Sửa rate/trạng thái |
| 6 | DELETE | `/api/v1/hr/commission-rules/{id}` | Xóa mềm |
| 7 | GET | `/api/v1/hr/kpi-targets?period=YYYY-MM` | Danh sách chỉ tiêu KPI theo kỳ |
| 8 | POST | `/api/v1/hr/kpi-targets` | Thêm chỉ tiêu cho 1 nhân sự/kỳ |
| 9 | PATCH | `/api/v1/hr/kpi-targets/{id}` | Sửa chỉ tiêu/thưởng |
| 10 | DELETE | `/api/v1/hr/kpi-targets/{id}` | Xóa mềm |

Chi tiết request/response: xem `deliveries/api-specs/payroll-commission-kpi-api.md`.

---

## 4. Cấu trúc cơ sở dữ liệu

### 4.1 Tổng quan các bảng (migration `0073`, `down_revision="0072"`, head duy nhất đã xác nhận)

| Bảng | Mục đích |
|------|---------|
| `commission_rule` | Rate % chiết khấu — 1 dòng/loại dịch vụ (`rule_type='service_type'`) hoặc 1 dòng cho thuốc (`rule_type='medicine'`, `service_type_id=NULL`). Per-clinic. |
| `kpi_target` | Chỉ tiêu doanh số + mức thưởng — 1 dòng/(staff_id, period). |
| `payroll_adjustment` | Điều chỉnh lương (claw-back tự động hoặc điều chỉnh thủ công tương lai) — 1 dòng/(staff_id, source_ref) áp dụng cho `apply_period`. |

### 4.2 Chi tiết bảng

#### `commission_rule`

| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `rule_type` | VARCHAR(20) | `'service_type'` \| `'medicine'` — CHECK constraint |
| `service_type_id` | UUID, nullable | FK → `service_type.id` (CASCADE) — **bắt buộc** khi `rule_type='service_type'`, **phải NULL** khi `rule_type='medicine'` (CHECK constraint ràng buộc 2 chiều) |
| `rate_percent` | NUMERIC(5,2) | 0–100 (CHECK) |
| `is_active` | Boolean | Mặc định `true` |

**Ràng buộc duy nhất:** `(clinic_id, service_type_id) WHERE rule_type='service_type' AND NOT is_deleted`; `(clinic_id) WHERE rule_type='medicine' AND NOT is_deleted` — mỗi clinic chỉ có **1** rate thuốc đang hoạt động tại một thời điểm.

#### `kpi_target`

| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `staff_id` | UUID | FK → `staff_profile.id` (CASCADE) |
| `period` | VARCHAR(7) | `"YYYY-MM"` |
| `revenue_target` | NUMERIC(15,2) | ≥ 0 |
| `bonus_amount` | NUMERIC(15,2) | ≥ 0 — mức thưởng tối đa khi đạt 100% chỉ tiêu |

**Ràng buộc duy nhất:** `(clinic_id, staff_id, period) WHERE NOT is_deleted`.

#### `payroll_adjustment`

| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| `staff_id` | UUID | FK → `staff_profile.id` (CASCADE) |
| `apply_period` | VARCHAR(7) | Kỳ áp dụng điều chỉnh (kỳ **sau** kỳ phát sinh claw-back) |
| `amount` | NUMERIC(15,2) | Âm với claw-back |
| `reason` | TEXT | Mô tả (vd "Huỷ hoá đơn HD000123: lý do...") |
| `source_type` | VARCHAR(30), nullable | `"invoice"` cho claw-back tự động |
| `source_ref` | VARCHAR(100), nullable | `invoice.id` (string) — khóa idempotent |
| `applied` | Boolean | Đánh dấu khi kỳ `apply_period` đã được "Ghi vào chi phí" (bookkeeping — KHÔNG dùng để lọc khi tính `compute_payroll`, tổng luôn tính theo `apply_period` bất kể `applied`) |

**Ràng buộc duy nhất:** `(clinic_id, staff_id, source_ref) WHERE NOT is_deleted AND source_ref IS NOT NULL`.

Cả 3 bảng đều bật RLS tenant isolation (`apply_rls_with_tenant_isolation`) + grant `cms_app`, theo đúng khuôn mẫu `service_type`/`attendance_day` (0071/0072).

### 4.3 Payslip — 4 trường mới (không đổi cấu trúc cũ)

`procedure_commission`, `medicine_commission`, `kpi_bonus`, `clawback_adjustment` (float, mặc định `0.0`) — đã được cộng/trừ sẵn vào `gross_pay`/`net_pay`, hiển thị riêng để truy vết.

---

## 5. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi |
|----|--------------|---------|
| BR-001 | Chiết khấu thủ thuật tính trên **doanh thu** `visit_service` (`quantity × unit_price − discount_amount`) của các dòng `status != 'cancelled'`, nhóm theo `service_type_id` của `service`, nhân rate cấu hình. `service_type_id = NULL` (dịch vụ chưa phân loại) → **không** có chiết khấu. | — |
| BR-002 | Người nhận chiết khấu thủ thuật = `visit.doctor_id` (bác sĩ khám) — **không** dùng `visit_service.performed_by_user_id`. | — |
| BR-003 | Chiết khấu thuốc tính trên doanh thu `prescription_item` (`quantity × unit_price`, chỉ dòng có `unit_price` khác NULL) của đơn thuốc `status != 'cancelled'`, nhân **1 rate chung**; người nhận = `prescription.doctor_id` (bác sĩ kê đơn — có thể khác `visit.doctor_id`). | — |
| BR-004 | Ánh xạ bác sĩ (`user.id`) → nhân sự (`staff_profile.id`) qua `staff_profile.user_id`. Bác sĩ không có `staff_profile` liên kết → chiết khấu bị **bỏ qua**, ghi log cảnh báo, **không lỗi** hệ thống. | Log `commission.unmapped_doctors` |
| BR-005 | KPI: thưởng = `bonus_amount × min(1, doanh_thu_thực_tế / revenue_target)` — tuyến tính theo tỷ lệ đạt, giới hạn tối đa 100% `bonus_amount` (vượt chỉ tiêu không thưởng thêm). `revenue_target ≤ 0` hoặc doanh thu ≤ 0 → thưởng = 0 (không chia cho 0). Doanh thu KPI = tổng doanh thu thủ thuật + thuốc mà nhân sự đó đã được tính chiết khấu trong kỳ (không tính riêng doanh thu chưa gắn `service_type`/không cấu hình rate). | — |
| BR-006 | Nhân sự **không có** `base_salary`/`hourly_rate` cấu hình nhưng có commission/KPI/claw-back ≠ 0 trong kỳ vẫn xuất hiện trên payslip (payslip "rỗng" — chỉ có phần chiết khấu). | — |
| BR-007 | Claw-back chỉ phát sinh khi kỳ nguồn (tháng theo `visit.visit_date` của hóa đơn bị hủy/hoàn) đã được "Ghi vào chi phí" (`POST /hr/payroll/post-to-expense`) — đây là tín hiệu "khóa kỳ" duy nhất (không có bảng `payroll_period` riêng). Nếu chưa khóa, sửa hóa đơn diễn ra bình thường, kỳ lương sẽ tự phản ánh đúng khi tính lại. | — |
| BR-008 | Claw-back áp dụng vào **kỳ kế tiếp** kỳ nguồn (`apply_period = kỳ_nguồn + 1 tháng`), không sửa lại kỳ đã chốt. | — |
| BR-009 | Claw-back là **idempotent** theo `(clinic_id, staff_id, source_ref=invoice_id)` — gọi lại nhiều lần trên cùng hóa đơn không tạo trùng điều chỉnh (ràng buộc DB + kiểm tra ứng dụng). | — |
| BR-010 | Claw-back tính lại theo **rate hiện tại** (không snapshot rate tại thời điểm chốt lương gốc) — nếu admin đổi rate giữa lúc chốt lương và lúc hủy hóa đơn, số tiền claw-back có thể khác số đã trả ban đầu. Đây là giới hạn đã biết (xem mục 8.3). | — |
| BR-011 | Best-effort: mọi lỗi trong `record_invoice_clawback` được bắt (`try/except`) và ghi log — **không bao giờ** chặn thao tác void/refund hóa đơn, giống khuôn mẫu `_release_pharmacy_reservations`/`_undispense_dispensed_items` đã có trong `invoice_service.py`. | Log `payroll.clawback_failed` |
| BR-012 | Chỉ `payroll.manage` mới xem/cấu hình chiết khấu, KPI, xem payslip breakdown — không có quyền mới, tái dùng quyền payroll hiện có. | 401/403 |

---

## 6. Xử lý lỗi

| Mã HTTP | Tình huống | Thông báo |
|---------|-----------|-----------|
| 409 | Tạo `commission_rule` trùng (`service_type_id` đã có rate, hoặc đã có rate thuốc) | "Đã có cấu hình chiết khấu cho loại dịch vụ này." / "Đã có cấu hình chiết khấu thuốc — sửa cấu hình hiện có thay vì tạo mới." |
| 409 | Tạo `kpi_target` trùng (staff_id, period) | "Nhân sự này đã có chỉ tiêu KPI cho kỳ này." |
| 404 | Sửa/xóa `commission_rule`/`kpi_target` không tồn tại (hoặc khác clinic) | "Không tìm thấy cấu hình chiết khấu." / "Không tìm thấy chỉ tiêu KPI." |
| 422 | `rule_type='service_type'` thiếu `service_type_id` (hoặc ngược lại có `service_type_id` khi `rule_type='medicine'`) | Pydantic validation error |
| 401/403 | Thiếu/sai quyền `payroll.manage` | Chuẩn RBAC hiện có |

Claw-back (`record_invoice_clawback`) **không trả lỗi HTTP** — mọi lỗi được nuốt nội bộ (best-effort), chỉ ảnh hưởng số liệu payroll kỳ sau, không ảnh hưởng response của API void/refund.

---

## 7. Giao diện người dùng

| Màn hình | Mô tả |
|----------|-------|
| **`/hr/payroll`** (mở rộng) | Thêm 4 cột: CK thủ thuật, CK thuốc, KPI, Điều chỉnh (claw-back, hiển thị âm màu đỏ nếu có). Nút liên kết nhanh sang trang cấu hình. |
| **`/hr/commission-kpi`** (mới) | 3 khối: (1) bảng rate% theo từng loại dịch vụ (load từ `/service-types`), (2) thẻ rate% thuốc (1 giá trị chung), (3) bảng chỉ tiêu KPI theo kỳ (chọn tháng, thêm/sửa/xóa — dùng `StaffPicker` có sẵn). Quyền: `payroll.manage`. |

Sidebar: mục điều hướng mới `hr:nav.commissionKpi` (icon `Percent`), quyền `payroll.manage`, đặt ngay dưới mục "Bảng lương".

---

## 8. Ghi chú và lưu ý khi kiểm thử

### 8.1 Điểm quan trọng cần nắm

- "Khóa kỳ" **không phải** một bảng/cờ riêng — nó là sự tồn tại của dòng `Expense(category='salary', description=...)` mà `post_payroll_to_expense` đã ghi (idempotent theo mô tả chứa tháng/năm). `is_period_posted()` chỉ kiểm tra dòng này có tồn tại hay không.
- `payroll_adjustment.applied` là **bookkeeping thuần túy** — không ảnh hưởng phép tính `compute_payroll` (luôn `SUM` theo `apply_period`), chỉ được set `true` khi kỳ đó được "Ghi vào chi phí" để biết điều chỉnh đã được đưa vào một kỳ lương đã chốt.
- KPI doanh số = doanh thu thủ thuật + thuốc **đã được tính chiết khấu** trong kỳ (tức là chỉ tính phần doanh thu có `service_type` được cấu hình rate hoặc thuộc rate thuốc đang active) — **không phải** tổng doanh thu bác sĩ trong toàn bộ hệ thống báo cáo (`doctor_performance_service` dùng công thức khác — join `invoice` theo trạng thái thanh toán). Đây là quyết định thiết kế để tránh 1 query riêng — xem Hạn chế bên dưới.

### 8.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| Chiết khấu thủ thuật cơ bản | rate 10% loại "Thủ thuật", visit_service 1,000,000đ | commission = 100,000đ, gán cho `visit.doctor_id` |
| Dịch vụ chưa phân loại | `service_type_id = NULL` | Không tính chiết khấu cho dòng đó |
| Chiết khấu thuốc | rate 5% chung, doanh thu thuốc 2,000,000đ trong kỳ | commission = 100,000đ, gán cho `prescription.doctor_id` |
| Bác sĩ chưa gắn tài khoản | `visit.doctor_id` không có `staff_profile.user_id` tương ứng | Bỏ qua, không tính vào payroll ai, log cảnh báo — không lỗi 500 |
| KPI đạt 100% | doanh thu = chỉ tiêu | thưởng = `bonus_amount` đầy đủ |
| KPI đạt 50% | doanh thu = 50% chỉ tiêu | thưởng = 50% `bonus_amount` |
| KPI vượt chỉ tiêu | doanh thu = 200% chỉ tiêu | thưởng vẫn = 100% `bonus_amount` (không thưởng thêm) |
| Claw-back sau khi chốt | Chốt lương tháng 7 → hủy hóa đơn tháng 7 sau đó | `payroll_adjustment` âm ghi vào kỳ tháng 8, không sửa lại số đã chốt tháng 7 |
| Claw-back trước khi chốt | Hủy hóa đơn tháng 7 khi tháng 7 **chưa** "Ghi vào chi phí" | Không tạo `payroll_adjustment` — kỳ 7 tự phản ánh đúng khi tính `compute_payroll` |
| Claw-back gọi lại 2 lần | Gọi `record_invoice_clawback` 2 lần cho cùng invoice | Chỉ tạo **1** dòng `payroll_adjustment`/nhân sự (idempotent) |

### 8.3 Hạn chế hiện tại

- Claw-back tính lại theo **rate hiện tại**, không snapshot rate tại thời điểm hóa đơn được tính lương lần đầu — nếu rate thay đổi giữa 2 mốc, số tiền claw-back có thể lệch với số đã trả gốc. Chấp nhận được cho v1 (rate hiếm khi đổi), nhưng cần lưu ý khi kiểm thử số liệu chính xác tuyệt đối.
- KPI chỉ tính trên doanh thu **đã được tính chiết khấu** (có rate cấu hình) — nếu admin chưa cấu hình rate cho một `service_type`, doanh thu loại đó **không** được tính vào doanh số KPI của bác sĩ dù dịch vụ có thực hiện. Đây là đơn giản hóa v1 (tránh phải viết thêm 1 query doanh thu riêng biệt cho KPI) — cân nhắc tách riêng nếu nghiệp vụ yêu cầu KPI độc lập với cấu hình chiết khấu.
- Không có API liệt kê "danh sách bác sĩ chưa gắn `staff_profile`, đang bị bỏ lỡ chiết khấu" — chỉ có log server-side (`commission.unmapped_doctors`, `payroll.clawback_unmapped_doctor`). Nếu cần cảnh báo trên UI, cần bổ sung endpoint riêng.
- Chưa kiểm thử tích hợp với DB thật của môi trường CI chính thức trong phiên làm việc này (không được khởi động lại stack `w2e`) — đã dùng ephemeral Postgres container (mạng Docker riêng, không publish port) để: (a) chạy toàn bộ chain `alembic upgrade head` từ đầu tới `0073` (thành công, idempotent, downgrade/upgrade lại cũng thành công), (b) seed dữ liệu tối thiểu và gọi trực tiếp `commission_service.compute_commission` + `kpi_service.compute_kpi_bonuses` — xác nhận SQL JOIN thực thi đúng và kết quả khớp kỳ vọng. Container đã được dọn dẹp sau khi xác minh. Luồng claw-back qua `void_invoice`/`refund_invoice` đầy đủ (bao gồm dữ liệu invoice/invoice_line thật) **chưa** được kiểm thử end-to-end với DB thật trong phiên này — được bao phủ bởi unit test cho phần tổng hợp thuần túy (`aggregate_clawback`) và rà soát thủ công logic join với invoice_service.py.

### 8.4 Hướng phát triển

- Bậc thang KPI nhiều mức (ví dụ: đạt 80% → thưởng X, đạt 100% → thưởng Y, đạt 120% → thưởng Z) nếu nghiệp vụ cần sau này — hiện tại là tuyến tính đơn giản.
- Rate thuốc theo nhóm thuốc (thay vì 1 rate chung) nếu cần chi tiết hơn.
- Snapshot rate tại thời điểm tính lương (để claw-back chính xác tuyệt đối, không phụ thuộc rate hiện tại).

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Trưởng nhóm kỹ thuật | | |
| Tester phụ trách | | |
| Khách hàng / PO | | |
