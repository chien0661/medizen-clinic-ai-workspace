# Implementation Plan: TASK-139

**Task:** Payroll — xuất bảng lương Excel + phiếu lương PDF từng nhân viên
**Date:** 2026-08-07
**Based on:** task.md + khảo sát hạ tầng export sẵn có + quyết định user 2026-08-07 (PDF = phiếu lương từng người, in qua trình duyệt)

---

## Approach

- **Excel**: thêm endpoint export vào payroll routes, gọi engine payroll hiện có để lấy payslips của kỳ rồi đổ ra .xlsx qua `app/core/excel.py` — cùng khuôn với `GET /staff/export` và `GET /attendance/export?format=xlsx`. Không thêm thư viện.
- **PDF**: thuần FE — component `PrintablePayslip` render phiếu lương từ dữ liệu payslip đã có trên PayrollPage, mở qua modal in (pattern `PrintVisitSlipModal`/`PrintPrescriptionModal`), người dùng Print → Save as PDF.

## Components

| Component | Action | Notes |
|-----------|--------|-------|
| BE `app/modules/hr/api/routes.py` | modify | `GET /api/v1/payroll/export?month=YYYY-MM` (+ filter đồng bộ màn payroll nếu có), RBAC `payroll.manage`, StreamingResponse xlsx |
| BE `app/modules/hr/services/payroll_service.py` | modify (nhỏ) | Hàm build rows export tái dùng compute kỳ hiện có — KHÔNG đổi engine |
| BE tests | create | Endpoint trả xlsx đúng số dòng/cột, kỳ rỗng, RBAC 403, số khớp payslip API |
| FE `src/pages/hr/PayrollPage.tsx` | modify | `ExportExcelButton` + `useExportDownload("/api/v1/payroll/export?...", "bang_luong_<kỳ>")`; nút in phiếu trên từng dòng |
| FE `src/components/hr/PrintablePayslip.tsx` + modal | create | Layout: header phòng khám, thông tin NV (staff_code, tên), kỳ, bảng breakdown (base/OT/phụ cấp/thưởng-phạt/commission + rate & nguồn/KPI/claw-back/điều chỉnh/gross/net), chữ ký; theo pattern PrintableInvoice |
| FE `src/modules/hr/api.ts` | modify | Nếu cần helper export URL |
| `src/locales/vi/hr.json` + `en/hr.json` | modify | Key mới cho export + payslip print |
| FE tests | create/extend | Export button gọi đúng URL; PrintablePayslip render đúng số liệu (override 15% vs chung) |

## Implementation Steps

1. Worktree: branch `feature/TASK-139-payroll-export` **từ `feature/TASK-138-payroll-session-shift`** ở cả 2 repo (`_feat139-be`, `_feat139-web`).
2. BE: hàm export rows + endpoint + tests (chạy trong Docker image clinic_e2e-api như TASK-138).
3. FE: ExportExcelButton + PrintablePayslip + modal + i18n vi/en + tests.
4. Regression: full BE unit suite + FE vitest (danh sách pre-existing failures như TASK-138).

## Dependencies

- TASK-138 branch (payslip fields). Không thư viện mới.

## Risks / Notes

- Excel số tiền: dùng number format, không string, để kế toán dùng được.
- Tên file có kỳ lương (`bang_luong_2026-08.xlsx`); encode UTF-8 header đúng chuẩn (`Content-Disposition` filename* nếu cần tiếng Việt).
- PrintablePayslip phải xử lý cả payslip kiểu monthly/hourly cũ (không có session/shift fields) — hide row thay vì hiện 0 sai lệch.
- Nhân sự không tài khoản: dữ liệu payslip đã key theo staff — không phụ thuộc user; không được join user để lấy tên.
