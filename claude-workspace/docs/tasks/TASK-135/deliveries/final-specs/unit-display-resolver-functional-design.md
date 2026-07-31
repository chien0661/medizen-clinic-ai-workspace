# Thiết Kế Chi Tiết Tính Năng: Resolver hiển thị đơn vị theo NAME (code→name)

**Dự án:** Clinic CMS
**Task:** TASK-135
**Phiên bản:** 1.0
**Ngày:** 2026-07-31
**Người thực hiện:** Code Implementation Agent
**Trạng thái:** Đã triển khai (FE only) — chờ Code Review / Test
**Tài liệu liên quan:** TASK-132 (Unit — danh mục đơn vị + creatable combobox), TASK-124 (unit_conversion), TASK-131 (usage_unit), task.md

---

## 1. Bối cảnh & vấn đề

`medicine.base_unit` / `sell_unit` / `purchase_unit` / `usage_unit` và `prescription_item.unit` là các cột **chuỗi tự do** (không FK tới bảng `unit`). Dữ liệu seed cũ lưu **`code`** không dấu của danh mục (`vien`, `lo`, `ong`, …), trong khi danh mục `unit` (TASK-132) có `name` có dấu tương ứng (`viên`, `lọ`, `ống`). Dữ liệu tạo mới qua `CreatableCombobox` (từ TASK-132 trở đi) lưu thẳng `name` — nên hai kiểu giá trị (code cũ / name mới) cùng tồn tại trong cùng một cột.

**Yêu cầu (phương án A — đã chọn):** không sửa dữ liệu đã lưu (phương án B, migration hàng loạt, bị loại). Thay vào đó, **ở mọi nơi hiển thị đơn vị cho người dùng**: nếu giá trị khớp một `code` trong danh mục `unit` (không phân biệt hoa/thường) → hiển thị `name`; nếu không khớp (đơn vị tự do/lạ) → giữ nguyên chuỗi, không được mất dữ liệu.

## 2. Giải pháp

### 2.1 Resolver dùng chung — `src/lib/units.ts`

```ts
buildUnitNameMap(units: {code, name}[]): Map<string, string>   // code (lowercase) -> name
resolveUnitLabel(value, nameByCode): string                     // "" khi value rỗng; passthrough khi không khớp
useUnitLabel(): { resolveUnitLabel(value) => string, isLoading, nameByCode }
```

- `useUnitLabel()` gọi `useQuery({ queryKey: ["admin","units"], queryFn: () => adminUnitsApi.list({is_active:true}) })` — **đúng key** mà `MedicinesPage` đã dùng, nên react-query cache dùng chung, không tạo thêm request trùng khi nhiều component cùng gọi hook trên cùng một trang.
- Trong lúc danh mục đang tải (`nameByCode` rỗng), `resolveUnitLabel` trả nguyên văn giá trị gốc — không chặn render, không "loading spinner" thêm.
- Hàm thuần `resolveUnitLabel(value, map)` và `buildUnitNameMap` được export riêng để unit-test không cần mock react-query, và để tái sử dụng map đã có sẵn (vd. `MedicinesPage`'s `MedicineModal` đã load `units` cho combobox — dùng lại map đó thay vì gọi hook lần 2).

### 2.2 Nguyên tắc áp dụng

1. **Chỉ hiển thị (display), không đổi dữ liệu đã lưu.** Trường form/draft item vẫn giữ giá trị gốc (code hoặc name) trừ 2 ngoại lệ có chủ đích bên dưới.
2. **Ngoại lệ có chủ đích — nơi giá trị "chốt" mới nên là name ngay từ đầu:**
   - `MedicinesPage` — `MedicineModal`'s `defaultValues` cho 4 ô combobox (`base_unit/sell_unit/purchase_unit/usage_unit`): resolve code→name khi mở form sửa, để combobox hiện đúng name. Nếu bác sĩ/admin lưu lại mà không đổi ô này, giá trị lưu sẽ tự nhiên "chuyển" từ code sang name — đây là hệ quả chấp nhận được của việc hiển thị đúng, không phải một migration chủ động.
   - `PrescriptionTab.addMedicine` — auto-fill đơn vị khi chọn thuốc: resolve **trước khi** đưa vào `item.unit`, nên đơn mới tạo lưu thẳng name (đúng AC "Kê đơn mới: đơn vị auto-fill là name; in ra đúng name").
3. **Mọi nơi còn lại:** chỉ bọc resolver quanh giá trị hiển thị (JSX), không sửa state/props gốc.

## 3. Danh sách nơi áp dụng (đã grep exhaustive toàn bộ `src/`)

| Khu vực | File | Vị trí |
|---|---|---|
| Danh mục thuốc | `src/pages/admin/MedicinesPage.tsx` | Cột `effective_low_stock_min` (list); `defaultValues` 4 ô combobox khi sửa |
| Danh mục dạng bào chế | `src/pages/admin/DosageFormsPage.tsx` | Cột "Đơn vị" trong bảng danh sách |
| Kê đơn (bác sĩ) | `src/components/doctor/PrescriptionTab.tsx` | `addMedicine` (auto-fill); ô "Đơn vị" (`DraftItemRow`); gợi ý quy đổi `unitConversionHint` |
| Tóm tắt khám | `src/components/doctor/SummaryTab.tsx` | Dòng đơn thuốc trong tóm tắt |
| Cockpit khám (settlement) | `src/pages/doctor/ClinicalWorkspacePage.tsx` | Danh sách rx trong `SettlementPanel` |
| Chi tiết lượt khám | `src/pages/visits/VisitDetailPage.tsx` | Bảng đơn thuốc |
| In đơn thuốc (bác sĩ) | `src/components/doctor/PrintPrescriptionModal.tsx`, `src/components/doctor/PrintablePrescription.tsx` | Preview + block in tuỳ biến (`TemplateRenderer` `rx.qty`) |
| In đơn thuốc (từ hóa đơn) | `src/components/billing/PrintPrescriptionModal.tsx` | Preview + block in tuỳ biến |
| Hóa đơn | `src/pages/billing/InvoiceDetailPage.tsx`, `src/components/billing/PrintableInvoice.tsx`, `src/components/billing/PrintModal.tsx` | Cột "Đơn vị" của dòng hóa đơn (bao gồm dòng thuốc `line_type=medicine`) |
| Tồn kho | `src/pages/pharmacy/InventoryPage.tsx` | Batch drawer + bảng tồn kho (`formatQty(qty, resolveUnitLabel(unit))`) |
| Nhập hàng | `src/pages/pharmacy/PurchaseInPage.tsx` | Giá bán, đơn vị nhập, số lượng, đơn giá, giá vốn quy đổi |
| Kiểm kê | `src/pages/pharmacy/StocktakePage.tsx` | Bảng bước 2 (đếm) + bước 3 (đối chiếu) |
| Điều chỉnh tồn kho | `src/pages/pharmacy/AdjustmentsPage.tsx` | Tồn hiện tại, số lượng mới, chênh lệch |
| Chờ cấp phát | `src/pages/pharmacy/PendingDispensePage.tsx` | Bảng thuốc trong modal cấp phát |
| Báo cáo tồn kho | `src/pages/reports/InventoryReportPage.tsx` | Cột đơn vị (bảng sắp hết hàng) |

**Test resolver:** `src/tests/lib/units.test.ts` (thuần function). **Test component:** `src/tests/admin/MedicinesPage.unitLabel.test.tsx` (code→name ở list + combobox sửa).

## 4. Nơi cố ý KHÔNG áp dụng

- **`UnitConversionsEditor`** (trong `MedicinesPage.tsx`) — các ô `from_unit`/`to_unit` của bảng quy đổi (TASK-124) là input tự do do admin gõ trực tiếp để định nghĩa **hệ số quy đổi** giữa 2 chuỗi chính xác như đã lưu; resolver ở đây có thể gây lệch giữa giá trị hiển thị và giá trị dùng để so khớp `from_unit`/`to_unit` khi tính hint. Ngoài phạm vi checklist TASK-135.
- **`components/print/TemplateRenderer.tsx`** — không cần sửa trực tiếp: khối `rx` chỉ nhận chuỗi `qty` đã ghép sẵn (`"{quantity} {unit}"`) từ nơi gọi (đã resolve ở `PrintPrescriptionModal`/`PrintablePrescription`); khối `lines` (hóa đơn) nhận `unit` đã resolve từ `PrintModal.tsx`/`PrintableInvoice.tsx` trước khi truyền vào block data.
- **`ExpiryProcessingPage.tsx`** (`t("pharmacy:common.unit")`) — đây là **nhãn tĩnh** "đơn vị" (chuỗi i18n cố định), không phải giá trị đơn vị của một thuốc cụ thể — không có gì để resolve.
- **Vitals** (`VitalsPage`, `VitalsTab`, `VitalsTrendChart`, `DiagnosisTab`, `modules/doctor/helpers.ts#formatVitalValue`) — trường `unit` ở đây là đơn vị của **chỉ số sinh hiệu** (mmHg, °C, kg…), thuộc catalog `vital_field_definition` hoàn toàn khác, không liên quan danh mục `unit` thuốc/kê đơn của TASK-132/135.

## 5. Rủi ro & lưu ý khi test

- Vì `useUnitLabel()` dùng `useQuery`, mọi test component render trực tiếp cây bị ảnh hưởng (`PrintablePrescription`, `PrintableInvoice`) cần bọc `QueryClientProvider` — đã cập nhật 2 file test hiện có (`PrintablePrescription.test.tsx`, `PrintableInvoice.test.tsx`) để mock `api.get` trả `[]` và bọc provider, tránh gọi mạng thật trong test.
- Danh mục rỗng/đang tải → resolver trả nguyên văn, không có "flash of code" gây khó chịu vì giá trị ban đầu vốn đã là chuỗi hợp lệ (chỉ là code thay vì name).
