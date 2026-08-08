# Thiết Kế Chi Tiết Tính Năng: Xuất bảng lương Excel + phiếu lương PDF

**Dự án:** Clinic CMS  
**Task:** TASK-139  
**Phiên bản:** 1.0  
**Ngày:** 2026-08-08  
**Người thực hiện:** Implementation + Code Review + Test Agents  
**Trạng thái:** Đã duyệt  
**Tài liệu liên quan:** TASK-128 (commission/KPI/claw-back), TASK-138 (session/shift pay types)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-08-08 | Phiên bản đầu tiên — tính năng xuất Excel + phiếu lương in được triển khai đầy đủ và test xanh |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Danh sách API](#3-danh-sách-api)
- [4. Chi tiết API](#4-chi-tiết-api)
- [5. UI: Nút xuất Excel + In phiếu lương](#5-ui-nút-xuất-excel--in-phiếu-lương)
- [6. Cột Excel — định nghĩa và ngữ nghĩa](#6-cột-excel--định-nghĩa-và-ngữ-nghĩa)
- [7. Phiếu lương in (PrintablePayslip)](#7-phiếu-lương-in-printablepayslip)
- [8. Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
- [9. Xử lý lỗi](#9-xử-lý-lỗi)
- [10. An toàn dữ liệu](#10-an-toàn-dữ-liệu)
- [11. Ghi chú khi kiểm thử](#11-ghi-chú-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Tính năng cho phép xuất bảng lương toàn kỳ thành file Excel (.xlsx) từ màn lương, với đầy đủ breakdown các loại thu nhập (lương cơ bản, tăng ca, phụ cấp, thưởng chuyên cần, hoa hồng thủ thuật/thuốc, thưởng KPI, claw-back, v.v.). Đồng thời hỗ trợ in phiếu lương chi tiết từng nhân viên (PDF qua trình duyệt, không sinh PDF phía BE).

### 1.2 Phạm vi

**Bao gồm:**
- Endpoint `GET /api/v1/payroll/export?month=YYYY-MM` trả file .xlsx
- 27 cột Excel với header tiếng Việt, bao gồm thông tin nhân viên + full breakdown pay-type + session/shift rate + commission + KPI + claw-back
- Nút "Xuất Excel" trên màn PayrollPage
- Component `PrintablePayslip` + modal in phiếu lương từng nhân viên
- i18n đầy đủ (vi/en)
- RBAC: chỉ role có quyền `payroll.manage` mới export được
- Xử lý nhân sự không có tài khoản (user_id=NULL)

**Không bao gồm:**
- Sinh PDF phía BE — in qua trình duyệt (browser print → Save as PDF)
- Công cụ custom PDF rendering
- Thiết lập công cụ báo cáo ngoài (BI, analytics)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Người dùng cuối** | Quản lý lương: xuất bảng lương kỳ, in phiếu lương từng NV |
| **Hệ thống cung cấp dữ liệu** | Payroll engine (TASK-014 base + TASK-128 + TASK-138) |
| **Hệ thống tiêu thụ** | Excel (kế toán), trình duyệt in (PDF) |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
[PayrollPage — màn lương]
    │  Nhân viên chọn kỳ lương + click "Xuất Excel"
    ▼
[FE: useExportDownload → GET /api/v1/payroll/export?month=YYYY-MM]
    │  (RBAC check: `payroll.manage`, header Authorization)
    ▼
[BE: payroll_service.compute_payroll + build_payroll_export_rows]
    │  Tái dùng engine payroll hiện có (không tính toán lại)
    │  Lấy payslips → format Excel rows
    ▼
[BE: build_xlsx_response → StreamingResponse]
    │  filename: bang_luong_YYYY-MM.xlsx
    │  Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    ▼
[Client: browser download → .xlsx file]
    │  Người dùng mở Excel, xem dữ liệu


[PayrollPage — phiếu lương in]
    │  Nhân viên click nút "In phiếu" trên từng dòng
    ▼
[FE: PrintPayslipModal opens (screen-only modal)]
    │  Fetch clinic settings (header phòng khám)
    │  Render PrintablePayslip (dữ liệu payslip đã có)
    ▼
[User: window.print() → Save as PDF]
    │  Trình duyệt in → chọn "Save as PDF"
    ▼
[Client: phiếu lương.pdf]
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Người dùng truy cập màn lương | Nhân viên HR có quyền `payroll.manage` truy cập trang `PayrollPage` với kỳ lương (YYYY-MM) |
| 2 | Chọn kỳ lương + click "Xuất Excel" | FE tạo yêu cầu `GET /api/v1/payroll/export?month=YYYY-MM` qua `useExportDownload` |
| 3 | BE kiểm tra RBAC | Middleware xác thực token, `require_permission("payroll.manage")` từ chối 403 nếu thiếu quyền |
| 4 | BE validate tháng | `month` phải match pattern `^\d{4}-(0[1-9]\|1[0-2])$` (YYYY-MM), 422 nếu sai |
| 5 | BE compute payroll | Gọi `payroll_service.compute_payroll(db, clinic_id, month)` — lấy payslips từ engine hiện có |
| 6 | BE format Excel rows | Gọi `build_payroll_export_rows(payslips)` — mỗi payslip thành 1 dòng, 27 cột |
| 7 | BE trả file xlsx | `build_xlsx_response(headers=..., rows=..., filename="bang_luong_YYYY-MM")` → StreamingResponse (200) |
| 8 | Client download | Trình duyệt tải .xlsx, tự động save hoặc prompt người dùng |
| 9 | Xuất xong | File mở được bằng Excel, Google Sheets, v.v. |
| 10 | In phiếu: click "In phiếu" | Nhân viên click icon in trên từng dòng nhân viên |
| 11 | Modal in mở | `PrintPayslipModal` mở (screen-only), render `PrintablePayslip` + thông tin phòng khám |
| 12 | Người dùng print | Click "In" hoặc Ctrl+P → chọn "Save as PDF" |
| 13 | Phiếu lương PDF | File PDF lưu vào máy tính |

---

## 3. Danh sách API

Tất cả API yêu cầu xác thực:
```
Authorization: Bearer {token}
```

**Đường dẫn gốc (Base Path):** `/api/v1`

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt |
|-----|------------|-----------|--------------|
| 1 | GET | `/payroll/export` | Xuất bảng lương kỳ (YYYY-MM) thành .xlsx |

---

## 4. Chi tiết API

### 4.1 Xuất bảng lương Excel

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/payroll/export` |
| **Mô tả** | Xuất toàn bộ payslips của một kỳ lương (YYYY-MM) thành file Excel, bao gồm 27 cột breakdown đầy đủ. Tái dùng engine `compute_payroll` từ `GET /hr/payroll` — không tính toán lại, đảm bảo số liệu không drift. |
| **Xác thực** | Bắt buộc (Bearer token) |
| **Quyền** | `payroll.manage` (ngang với `/hr/payroll` + `/hr/payroll/post-to-expense`) |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `month` | String | Có | Kỳ lương cần xuất, định dạng YYYY-MM (e.g., `2026-08`). Phải match pattern `^\d{4}-(0[1-9]\|1[0-2])$` để tránh CRLF injection + invalid date. | — |

**Giá trị hợp lệ của `month`:**

| Giá trị | Ý nghĩa |
|---------|---------|
| `2026-08` | Tháng 8 năm 2026 |
| `2026-01` | Tháng 1 năm 2026 |
| `2025-12` | Tháng 12 năm 2025 |

**Giá trị không hợp lệ (sẽ trả 422):**

| Giá trị | Lý do |
|--------|-------|
| `2026-13` | Tháng 13 không tồn tại |
| `2026/08` | Dùng `/` thay vì `-` |
| `2026-8` | Tháng không pad `0` |
| `202608` | Thiếu dấu `-` |
| `2026-08\r\n` | CRLF injection — bị từ chối ở mức pattern |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu từ FE |
| 2 | Kiểm tra token xác thực — từ chối 401 nếu không hợp lệ |
| 3 | Kiểm tra quyền `payroll.manage` — từ chối 403 nếu thiếu |
| 4 | Kiểm tra tham số `month` — từ chối 422 nếu không match pattern YYYY-MM |
| 5 | Gọi `payroll_service.compute_payroll(db, clinic_id, month)` — lấy payslips (có thể rỗng) |
| 6 | Gọi `build_payroll_export_rows(payslips)` — format mỗi payslip thành 1 dòng Excel, 27 cột |
| 7 | Gọi `build_xlsx_response(headers=PAYROLL_EXPORT_HEADERS, rows=..., filename="bang_luong_YYYY-MM")` |
| 8 | Trả StreamingResponse (200, .xlsx binary) hoặc 400/422/500 nếu lỗi |

**Truy vấn dữ liệu:**

Endpoint gọi `compute_payroll`, một hàm pure (không có side-effects), kết hợp:
- Timesheet của tháng (từ bảng attendance_day + legacy Shift/TimeLog): worked_days, total_hours, ot_hours, absent_days, leave_days, late_count
- Commission tháng (TASK-128): procedure/medicine commission + rate source
- KPI bonus (TASK-128): từ KPI target + revenue
- Claw-back adjustment (TASK-128): từ PayrollAdjustment table
- Staff profile (pay_type, base/hourly/session/shift rate, allowance, v.v.)

```python
# Pseudo-code — BE implementation
async def export_payroll_xlsx(db, clinic_id: UUID, month: str) -> Response:
    # Validate month
    if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", month):
        raise HTTPException(422, "Invalid month format")
    
    # Compute payroll (tái dùng engine hiện có)
    payroll_dict = await payroll_service.compute_payroll(db, clinic_id, month)
    payslips = payroll_dict["payslips"]  # list, có thể rỗng
    
    # Format Excel rows
    rows = payroll_service.build_payroll_export_rows(payslips)
    
    # Build .xlsx
    return build_xlsx_response(
        sheet_title="Bảng lương",
        title=f"Bảng lương tháng {month}",
        headers=payroll_service.PAYROLL_EXPORT_HEADERS,  # 27 cột
        rows=rows,
        filename=f"bang_luong_{month}"  # e.g., bang_luong_2026-08.xlsx
    )
```

#### Kết quả trả về

**Thành công (200 OK):**

Trả file `.xlsx` binary với `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` và header:
```
Content-Disposition: attachment; filename="bang_luong_2026-08.xlsx"
```

**Cấu trúc Excel:**
- **Sheet:** "Bảng lương"
- **Dòng 1 (Title):** "Bảng lương tháng 2026-08"
- **Dòng 2:** Header 27 cột (xem mục 6 dưới)
- **Dòng 3+:** Data rows (mỗi nhân viên 1 dòng, sắp xếp theo staff_code)
- **Hàng cuối (nếu có):** Tổng cộng (tuỳ chọn)

**Trường hợp không có dữ liệu (kỳ rỗng):**
- Trả 200 OK, workbook vẫn có header (không 500 hoặc 204)
- Data rows rỗng, người dùng thấy sheet với header sẵn sàng để bổ sung dữ liệu

**Lỗi (4xx/5xx):**

| HTTP | Mã lỗi | Tình huống | Thông báo |
|------|--------|-----------|-----------|
| 401 | UNAUTHORIZED | Token không hợp lệ / hết hạn | "Yêu cầu xác thực để truy cập tài nguyên này" |
| 403 | FORBIDDEN | Role thiếu quyền `payroll.manage` | "Bạn không có quyền truy cập tài nguyên này" |
| 422 | VALIDATION_ERROR | `month` không match YYYY-MM | "Giá trị month không hợp lệ. Định dạng phải là YYYY-MM" |
| 400 | BAD_REQUEST | `month` hợp lệ nhưng tháng không tồn tại (hiếm) | "Tháng yêu cầu không hợp lệ" |
| 500 | INTERNAL_ERROR | Lỗi DB / compute engine | "Lỗi hệ thống, vui lòng thử lại sau" |

**Định dạng phản hồi lỗi:**
```json
{
  "detail": "Giá trị month không hợp lệ. Định dạng phải là YYYY-MM"
}
```

---

## 5. UI: Nút xuất Excel + In phiếu lương

### 5.1 Nút "Xuất Excel" trên PayrollPage

**Vị trí:** Bên cạnh nút "Ghi vào chi phí" trên màn lương (PayrollPage.tsx)

**Cấu tính:** 
- Component `ExportExcelButton` (pattern tái dùng từ /staff/export, /attendance/export)
- Hook `useExportDownload("/api/v1/payroll/export", { month }, "bang_luong_" + month)`
- Tự động pass Authorization header + clinic_id context

**Hành vi:**
- Click → ngay lập tức tải file `bang_luong_2026-08.xlsx`
- Không mở modal xác nhận (UX nhanh gọn)
- Tooltip hoặc label: "Xuất bảng lương Excel"

**i18n key:** `hr:payroll.export_button` (vi: "Xuất Excel", en: "Export Excel")

### 5.2 Nút "In phiếu" trên từng dòng nhân viên

**Vị trí:** Cột mới "In phiếu" bên phải bảng lương (table row action)

**Cấu tính:**
- Icon: print/document-text (Heroicons / Material Icons)
- Click → mở `PrintPayslipModal` với `staffId` + payslip data

**Hành vi:**
- Modal mở, hiển thị phiếu lương (PrintablePayslip component)
- Nút "In" hoặc tiêu đề modal có link "In"
- Click "In" → `window.print()` → trình duyệt mở print dialog
- Người dùng chọn "Save as PDF" → file PDF

**i18n key:** `hr:payroll.print_payslip` (vi: "In phiếu lương", en: "Print Payslip")

### 5.3 Cập nhật cột table

| Cột mới | Loại | Header | Nội dung |
|---------|------|--------|---------|
| In phiếu | Action | "In phiếu" | Icon print, click → `PrintPayslipModal` |

**Cập nhật colSpan footer:** Nếu table có footer tổng cộng, `colSpan` cần +1 để căn chỉnh với cột mới.

---

## 6. Cột Excel — định nghĩa và ngữ nghĩa

27 cột, order cố định (giữ nguyên giữa các lần export để accounting quen nhập liệu).

| STT | Tên cột Excel | Tên trường payslip | Kiểu | Mô tả chi tiết | Ghi chú |
|-----|---------------|-------------------|------|----------------|---------|
| 1 | Mã NV | staff_code | Text | Mã nhân viên duy nhất (không phụ thuộc user_id) | Ví dụ: "NV001" |
| 2 | Họ và tên | full_name | Text | Tên đầy đủ | Có khi không có tài khoản |
| 3 | Loại lương | pay_type | Text | monthly / hourly / per_session / per_shift | "Theo tháng" / "Theo giờ" / "Theo buổi" / "Theo ca" |
| 4 | Số công/buổi | worked_days | Number | Số ngày làm / buổi tính lương | Giờ 0.5 nếu buổi chiều |
| 5 | Tổng giờ làm | total_hours | Number | Tổng giờ làm trong tháng (nếu hourly) | 0 nếu monthly |
| 6 | Giờ tăng ca | ot_hours | Number | Giờ tăng ca (overtime) | monthly/hourly only |
| 7 | Số ngày vắng | absent_days | Number | Số ngày vắng không phép | Trừ từ base (monthly) |
| 8 | Số ngày nghỉ phép | leave_days | Number | Số ngày nghỉ phép được duyệt | Không trừ base |
| 9 | Số lần đi muộn | late_count | Number | Số lần check-in trễ (muộn) | Dùng tính late_penalty |
| 10 | Đơn giá buổi | session_rate | Number | Giá mỗi buổi (per_session pay type) | Blank nếu không per_session |
| 11 | Đơn giá ca | shift_rate | Number | Giá mỗi ca (per_shift pay type) | Blank nếu không per_shift |
| 12 | Số ca hoàn thành | completed_shifts | Number | Số ca có status='completed' | 0 nếu monthly/hourly |
| 13 | Lương cơ bản | base_earned | Currency | Lương cơ bản tính thực tế (monthly/hourly/per_session/per_shift) | Tính theo pay_type |
| 14 | Lương tăng ca | overtime_pay | Currency | Tiền tăng ca (monthly/hourly only) | 0 nếu per_session/per_shift |
| 15 | Phụ cấp | allowance | Currency | Phụ cấp (cấp cứu, điều hòa, v.v.) | Áp dụng tất cả pay types |
| 16 | Thưởng chuyên cần | attendance_bonus | Currency | Thưởng nếu 0 vắng + 0 muộn | Conditional |
| 17 | Phạt đi muộn | late_penalty_total | Currency | Tiền phạt muộn (late_count × late_penalty) | Âm hoặc 0 |
| 18 | Hoa hồng thủ thuật | procedure_commission | Currency | Commission từ procedure (TASK-128) | 0 nếu không có |
| 19 | Tỷ lệ HH thủ thuật (%) | procedure_rate_percent | Percent | Tỷ lệ commission thủ thuật được áp dụng | Blank nếu 0 commission; **ngữ nghĩa: bình quân gia quyền theo doanh thu** khi nhân viên hưởng nhiều loại DV |
| 20 | Nguồn tỷ lệ thủ thuật | procedure_rate_source | Text | Riêng (override) / Chung (clinic default) | Blank nếu không có commission; "Riêng" = ≥1 dòng dùng rate override |
| 21 | Hoa hồng thuốc | medicine_commission | Currency | Commission từ medicine (TASK-128) | 0 nếu không có |
| 22 | Tỷ lệ HH thuốc (%) | medicine_rate_percent | Percent | Tỷ lệ commission thuốc được áp dụng | Blank nếu 0 commission; **ngữ nghĩa: bình quân gia quyền theo doanh thu** |
| 23 | Nguồn tỷ lệ thuốc | medicine_rate_source | Text | Riêng / Chung | Blank nếu không có commission |
| 24 | Thưởng KPI | kpi_bonus | Currency | Thưởng KPI (TASK-128) | 0 nếu không đạt target |
| 25 | Điều chỉnh/hoàn ứng | clawback_adjustment | Currency | Điều chỉnh / hoàn ứng (TASK-128), thường âm | 0 nếu không có |
| 26 | Tổng thu nhập | gross_pay | Currency | Tổng lương trước khoảng trừ (gross) | = base + OT + allowance + bonus - penalty + commission + KPI + claw-back |
| 27 | Thực nhận | net_pay | Currency | Tổng lương thực tế người nhân viên lấy | = gross (v1 chưa có BHXH/thuế) |

### 6.1 Ngữ nghĩa cột "Tỷ lệ HH (%)" — Blended Rate

**Quy tắc quan trọng:** Các cột "Tỷ lệ HH thủ thuật (%)" (col 19) và "Tỷ lệ HH thuốc (%)" (col 22) **KHÔNG phải** là giá trị cấu hình sẵn trên staff profile. Đây là **tỷ lệ bình quân gia quyền theo doanh thu** tính toán từ:

```
Tỷ lệ áp dụng = (Commission / Doanh thu) × 100%
```

**Trường hợp thông thường (1 service type):**
- Nhân viên A làm procedure với rate override 15% → commission = doanh thu × 15%
- Excel show: "Tỷ lệ HH thủ thuật (%)" = 15.00, "Nguồn" = "Riêng"

**Trường hợp blended (nhiều service type, tỷ lệ khác nhau):**
- Nhân viên B làm 2 service types: procedure_1 (doanh thu 1M, rate 15%) + procedure_2 (doanh thu 2M, rate 20%)
- Commission = 1M×15% + 2M×20% = 550K
- Tỷ lệ áp dụng = (550K / 3M) × 100% ≈ 18.33%
- Excel show: "Tỷ lệ HH thủ thuật (%)" = 18.33, "Nguồn" = "Riêng" (vì ≥1 dòng dùng override)

**Quy tắc "Nguồn tỷ lệ":**
- "Riêng" = **có ít nhất 1 dòng dùng override** (staff-specific rate)
- "Chung" = **tất cả dòng dùng clinic default** rate
- Blank = không có commission (Commission = 0)

**Lý do quyết định giữ nguyên:** Để kế toán có thể dễ dàng kiểm tính commission (Commission = (Tỷ lệ / 100) × Doanh thu), nhưng cần hiểu rằng tỷ lệ hiển thị **không phải cấu hình cứng**, mà là **kết quả blended** từ các dòng transaction đa dịch vụ. Quyết định này đã chốt với user (2026-08-08).

---

## 7. Phiếu lương in (PrintablePayslip)

### 7.1 Yêu cầu layout

**Format:** A4, landscape hoặc portrait (tuỳ khách hàng), in được từ trình duyệt.

**Cấu trúc phiếu:**

1. **Header phòng khám** (từ clinic settings)
   - Logo / Tên phòng khám / Địa chỉ / Điện thoại

2. **Thông tin nhân viên**
   - Mã NV: [staff_code]
   - Tên: [full_name]
   - Kỳ lương: [month] (e.g., "Tháng 8/2026")

3. **Bảng breakdown chi tiết**
   - Lương cơ bản: [base_earned]
   - Lương tăng ca: [overtime_pay]
   - Phụ cấp: [allowance]
   - Thưởng chuyên cần: [attendance_bonus]
   - Phạt đi muộn: [late_penalty_total]
   - Hoa hồng thủ thuật: [procedure_commission] (nếu > 0, show badge "Tỷ lệ riêng" / "Tỷ lệ chung")
   - Hoa hồng thuốc: [medicine_commission] (nếu > 0, show badge "Tỷ lệ riêng" / "Tỷ lệ chung")
   - Thưởng KPI: [kpi_bonus] (nếu > 0)
   - Điều chỉnh/hoàn ứng: [clawback_adjustment] (nếu ≠ 0)
   - **Các dòng session/shift (nếu apply):** ẩn các dòng "Số công/buổi", "Tổng giờ làm", "Giờ tăng ca", "Số ca hoàn thành" nếu staff dùng pay_type khác → tránh nhầm lẫn (e.g., monthly staff không hiện 0 buổi)

4. **Tổng cộng**
   - Tổng lương: [gross_pay]
   - Thực nhận: [net_pay]

5. **Chỗ ký nhận**
   - Dòng ký nhận nhân viên (text: "Ký nhận")
   - Ngày [___]

### 7.2 Badge tỷ lệ riêng / chung

Khi hiện commission, thêm **badge nhỏ** bên cạnh số tiền:
- "Tỷ lệ riêng" (nếu procedure/medicine_rate_source = "staff_override")
- "Tỷ lệ chung" (nếu procedure/medicine_rate_source = "clinic_default")

Ví dụ:
```
Hoa hồng thủ thuật:         1,500,000đ  [Tỷ lệ riêng]
Hoa hồng thuốc:              800,000đ  [Tỷ lệ chung]
```

### 7.3 Ẩn dòng session/shift theo pay_type

Để tránh hiện các dòng không liên quan:

| Pay type | Ẩn các dòng |
|----------|-----------|
| monthly | "Số công/buổi", "Đơn giá buổi", "Đơn giá ca", "Số ca hoàn thành" |
| hourly | "Số công/buổi", "Đơn giá buổi", "Đơn giá ca", "Số ca hoàn thành" |
| per_session | "Tổng giờ làm", "Giờ tăng ca", "Lương tăng ca", "Đơn giá ca", "Số ca hoàn thành" |
| per_shift | "Tổng giờ làm", "Giờ tăng ca", "Lương tăng ca", "Đơn giá buổi", "Số công/buổi" |

### 7.4 Nhân sự không tài khoản

- Phiếu lương xuất hiện bình thường (dữ liệu payslip key theo staff_id, không user_id)
- Nếu chỗ ký nhận cần tên account, skip (không hiện username, chỉ in staff code + full_name)

### 7.5 Modal in (PrintPayslipModal)

**Cấu tính:**
- Button "In" / "Đóng" ở footer
- Click "In" → `window.print()` → trình duyệt dialog
- Print style: `@media print { ... }` ẩn chrome (modal header, buttons), chỉ in nội dung phiếu
- FE fetch clinic settings (clinic_name, address, phone) để render header

**i18n keys:**
- `hr:payroll.payslip.modal_title` (vi: "Phiếu lương", en: "Payslip")
- `hr:payroll.payslip.print_button` (vi: "In", en: "Print")
- `hr:payroll.payslip.close_button` (vi: "Đóng", en: "Close")

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-001 | Endpoint `/payroll/export` chỉ thực hiện với role có quyền `payroll.manage` (ngang role `/hr/payroll`). Các role khác (receptionist, doctor, v.v.) bị từ chối. | 403 Forbidden + thông báo "Bạn không có quyền truy cập tài nguyên này" |
| BR-002 | Tham số `month` phải match pattern `^\d{4}-(0[1-9]\|1[0-2])$` (YYYY-MM). CRLF, khoảng trắng, ký tự đặc biệt → reject. | 422 Unprocessable Entity + thông báo "Giá trị month không hợp lệ" |
| BR-003 | Dữ liệu Excel luôn match `GET /hr/payroll?month=...` (cùng engine compute, không tính lại). | Nếu detect drift → bug, cần investigate engine, không phải Excel export. |
| BR-004 | Kỳ lương rỗng (không có staff on payroll) → trả workbook với header, không 500 hoặc 204. | 200 OK, .xlsx có 1 sheet, header 27 cột, 0 data rows. |
| BR-005 | Nhân sự không có tài khoản (user_id=NULL) vẫn xuất hiện đầy đủ trong Excel và phiếu lương (key data theo staff_id). | Dữ liệu không bỏ sót, kế toán thấy tất cả NV. |
| BR-006 | File name: `bang_luong_YYYY-MM.xlsx` (e.g., `bang_luong_2026-08.xlsx`), UTF-8 encoded (tiếng Việt support). | Nếu client báo file name bị lỗi, check Content-Disposition header — BE đã handle đúng. |
| BR-007 | Tỷ lệ commission hiển thị = (commission / revenue) × 100%, **bình quân gia quyền** khi nhân viên nhiều service types. | Accounting cần hiểu ngữ nghĩa (xem mục 6.1). |
| BR-008 | Nguồn tỷ lệ ("Riêng"/"Chung") = "Riêng" nếu ≥1 dòng dùng override, ngược lại "Chung". | Giúp accounting tracking override policy. |

---

## 9. Xử lý lỗi

### 9.1 Validation lỗi tham số

**Case: `month` không match YYYY-MM**
```
GET /api/v1/payroll/export?month=2026-13

Response (422):
{
  "detail": "Giá trị month không hợp lệ. Định dạng phải là YYYY-MM"
}
```

**Case: `month` có CRLF hoặc ký tự đặc biệt**
```
GET /api/v1/payroll/export?month=2026-08%0D%0A

Response (422):
{
  "detail": "Giá trị month không hợp lệ. Định dạng phải là YYYY-MM"
}
```

### 9.2 RBAC lỗi

**Case: Role receptionist (không `payroll.manage`) export**
```
Response (403):
{
  "detail": "Bạn không có quyền truy cập tài nguyên này"
}
```

### 9.3 Lỗi hệ thống

**Case: Database timeout / compute engine crash**
```
Response (500):
{
  "detail": "Lỗi hệ thống, vui lòng thử lại sau"
}
```

---

## 10. An toàn dữ liệu

### 10.1 Chống formula injection

**Vấn đề:** Excel có thể thực thi formula (e.g., `=cmd|'/c calc'!A1`) nếu cell bắt đầu với `=`, `+`, `@`, `-`.

**Giải pháp:** `build_xlsx_response` (hạ tầng sẵn có) tự động:
- Escape các formula-prefix nếu detect
- Hoặc dùng cell format `@` (text) để cell được đọc như string

Các dòng test manual include staff có tên "=1+1" để verify neutralization.

### 10.2 Tenant isolation

- Endpoint kiểm tra clinic_id từ context (middleware), không cho phép cross-tenant access.
- Payroll export chỉ lấy payslips từ clinic_id hiện tại.

### 10.3 Audit trail

- Endpoint tái dùng `payroll_service.compute_payroll`, không có audit log riêng (giống `/hr/payroll`).
- Nếu cần audit export action, thêm log ở FE hoặc BE middleware (out of scope TASK-139).

---

## 11. Ghi chú khi kiểm thử

### 11.1 Điểm quan trọng

- **Số liệu khớp `GET /hr/payroll`:** Excel export dùng cùng engine, nên dữ liệu phải 100% match (staff_code, full_name, base_earned, commission, v.v.).
- **Blended rate semantics:** Cột "Tỷ lệ HH (%)" hiển thị blend, không phải configured rate → accounting cần hiểu (xem BR-007).
- **Empty period:** Kỳ không có staff → 200 OK, header-only .xlsx, không 500.
- **Session/shift rate:** Cột "Đơn giá buổi" / "Đơn giá ca" blank cho monthly/hourly staff.
- **Phiếu lương in:** Browser print → Save as PDF (client-side, không BE PDF generation).

### 11.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| Happy path: monthly staff | month=2026-08 | .xlsx, 1 dòng NV, base_earned > 0, commission/KPI/claw-back = 0 |
| Commission + blended rate | staff với procedure + medicine, nhiều service types | Excel col 19-20, 22-23 show blended rate + source badge |
| Empty period | month=2025-01 (kỳ không có staff) | 200 OK, .xlsx header-only |
| Invalid month | month=2026-13 | 422 + "Định dạng...YYYY-MM" |
| RBAC: no permission | role=receptionist | 403 + "không có quyền" |
| No account staff | staff.user_id=NULL | Excel + phiếu in vẫn xuất hiện (key theo staff_id) |
| Per_session staff | pay_type=per_session | Col 4 "Số công/buổi", col 10 "Đơn giá buổi" có giá trị; col 5-6 blank |
| Per_shift staff | pay_type=per_shift | Col 11 "Đơn giá ca", col 12 "Số ca" có giá trị; col 5-6 blank |
| Formula injection | staff_code hoặc full_name="=1+1" | .xlsx mở, cell hiện text "=1+1", không execute formula |

### 11.3 Hạn chế hiện tại

- **v1 không có statutory deductions (BHXH/thuế):** net_pay = gross_pay (tuỳ future release)
- **E2E Playwright scope:** Tester skip (FE vitest + BE integration + manual stack covers đủ)

### 11.4 Hướng phát triển

**TASK-140:** Cải thiện e2e DB fixture teardown (pre-existing pattern, không specific TASK-139).

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Code Review Agent | — | 2026-08-08 |
| Test Agent | — | 2026-08-08 |
| Implementation Agent | — | 2026-08-08 |
