# Implementation Plan: TASK-124

**Task:** Quản lý đa đơn vị đo + quy đổi (nhập / tồn-cảnh báo / bán-cấp phát)
**Date:** 2026-07-26
**Based on:** task.md + rà soát code hiện trạng (Explore) + 4 quyết định thiết kế chốt với người dùng 2026-07-26.

---

## Quyết định thiết kế (đã chốt)
1. **Mô hình factor:** bảng `unit_conversion` tổng quát (n cấp).
2. **Giá:** theo **đơn vị bán (sell_unit)** — migrate `sale_price`/đơn giá HĐ.
3. **dosage_form:** thêm **FK `Medicine.dosage_form_id`** (giữ cột free-text `dosage_form` để backfill/compat).
4. **Cảnh báo tồn:** giữ theo **base_unit** (3 cấp TASK-093/113), không thêm đơn vị thứ 3.

## Nguyên tắc lõi
- `base_unit` vẫn là **đơn vị gốc của tồn kho** (Batch.actual_quantity, ngưỡng cảnh báo) — KHÔNG đổi, đảm bảo backward-compat.
- Mọi đơn vị khác quy về base qua `unit_conversion`. Factor lưu chuẩn: **1 `from_unit` = `factor` × `to_unit`**; resolver luôn quy về base.
- Backfill: mọi thuốc có row `base→base factor=1` + (nếu có) `purchase_unit→base = pack_size` + `sell_unit=base_unit factor=1` → **hành vi hiện hữu không đổi** (factor 1), đơn/HĐ cũ giữ nguyên.

## Approach
Giữ nguyên trục tồn kho theo base_unit; thêm **lớp quy đổi đơn vị** (bảng + resolver) và **đơn vị bán** cho medicine. Prescribe/bill nhập theo sell_unit → resolver quy sang base để reserve/dispense/trừ kho; giá & HĐ theo sell_unit. Purchase→base đã có (pack_size) được backfill vào bảng để thống nhất nguồn.

## Components

| Component | Action | Notes |
|-----------|--------|-------|
| `inventory/models/unit_conversion.py` | create | `unit_conversion(id, clinic_id nullable, medicine_id FK, from_unit str, to_unit str, factor Numeric)`; unique (medicine_id, from_unit, to_unit) |
| `inventory/models/medicine.py` | modify | + `dosage_form_id` FK (nullable) → DosageForm; + `sell_unit` (default = base_unit). Giữ `dosage_form`(free-text), `purchase_unit`, `pack_size`, `base_unit`, `sale_price` |
| `alembic/versions/00NN_unit_conversion_and_sell_unit.py` | create | tạo bảng + cột; **backfill**: base→base(1), purchase→base(pack_size), sell_unit=base_unit; backfill `dosage_form_id` bằng match name/code; giữ `sale_price` (per base = per sell vì sell=base factor 1) |
| `inventory/services/unit_service.py` (mới) | create | resolver: `to_base(medicine, qty, unit)`, `from_base(...)`, `conversions_for(medicine)`; validate factor>0, đơn vị tồn tại |
| `inventory/services/purchase_in_service.py` | modify | dùng resolver (fallback pack_size) — không đổi hành vi |
| `inventory/services/medicine_service.py` + schemas | modify | CRUD sell_unit + conversions + dosage_form_id |
| `prescriptions/services/prescription_service.py` + `medicine_search_service.py` | modify | search trả sell_unit + conversions; kê đơn nhập sell-unit, resolver → base để reserve; `PrescriptionItem` giữ `quantity`(sell) + `unit`(sell), thêm base cho pharmacy |
| `pharmacy/services/reservation_service.py`, `dispense_service.py` | modify | reserve/dispense theo **base** (quy đổi từ sell) — trừ kho đúng |
| `billing/services/invoice_service.py` | modify | line quantity+unit=sell, `unit_price` per sell; tổng khớp |
| `reports/services/*` | verify | valuation/COGS theo base×unit_cost (giữ); revenue theo giá sell — kiểm nhất quán |
| clinic-cms-web: MedicinesPage, PrescriptionTab, DosageFormsPage, InventoryPage | modify | form định nghĩa sell_unit + bảng conversion + chọn dosage_form (FK); kê đơn chọn sell-unit + hiện quy đổi; hiển thị đơn vị đúng |

## Implementation Steps
1. **BE model + migration** (bảng unit_conversion, Medicine.sell_unit + dosage_form_id) + **backfill an toàn** (factor 1, sell=base) → chạy được, hành vi cũ không đổi.
2. `unit_service` resolver + test đơn vị (to_base/from_base, làm tròn).
3. Purchase-in dùng resolver (giữ tương thích pack_size).
4. Medicine CRUD (BE+FE): quản lý sell_unit + conversions + dosage_form_id.
5. Prescribe: search trả conversions; kê theo sell-unit; reserve theo base.
6. Dispense + invoice: trừ kho base, HĐ + giá theo sell-unit; đối soát tổng.
7. Reports nhất quán; cảnh báo tồn giữ base.
8. E2E: nhập thùng→tồn hộp→bán viên/ml; case sell≠base (lọ→ml); backward-compat factor=1 (đơn/HĐ cũ).

## Dependencies
- Không thư viện mới. Dùng Alembic, SQLAlchemy, Decimal (làm tròn), infra sẵn có.
- Liên quan TASK-076 (dosage form category), TASK-093/113 (ngưỡng cảnh báo), TASK-094 (DosageForm.unit gợi ý — sẽ được thay bằng resolver thật).

## Risks / Notes
- **Làm tròn:** sell≠base (lọ→ml) cần Decimal + quy tắc làm tròn rõ; viên = số nguyên. Xác định policy khi reserve/dispense lẻ.
- **Giá migrate:** đổi `sale_price` sang per-sell — với backfill sell=base factor 1 nên giá cũ giữ nguyên; chỉ thuốc set sell≠base mới cần nhập lại giá.
- **Backward-compat:** đơn/HĐ cũ có `unit` snapshot + quantity — KHÔNG đổi; resolver chỉ áp cho bản ghi mới.
- **dosage_form_id backfill:** match free-text có thể sót (viết sai/không có DosageForm tương ứng) → để null, fallback free-text; log các case không match.
- Phạm vi lớn, cross-cutting → nên chia phase (BE core + backfill trước, FE + prescribe/bill sau) và test kỹ regression billing/pharmacy (đừng vỡ TASK-108/112/119/120/123).
