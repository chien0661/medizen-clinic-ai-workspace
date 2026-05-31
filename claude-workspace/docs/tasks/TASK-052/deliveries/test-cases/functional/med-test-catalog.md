# Test Case Catalog — MED · Danh mục Thuốc & Tồn kho

**Nguồn:** function_list_data.py (group MED) + clinic_management_function_list.md + system_design/BA.
**Phạm vi:** 18 functions (MED-001 … MED-018).  **Tổng test case:** 64.  **Ngày:** 2026-05-30.

> **Ghi chú coverage (đối chiếu nguồn + code thực tế):** Cột Status trong nguồn cho thấy toàn bộ chức năng MED v1 đang ở trạng thái ⬜ (chưa triển khai — task TASK-011/012/015 chưa ship) và các chức năng v2 ở trạng thái 💡 (ý tưởng, chưa lập task). Đối chiếu repo `clinic-cms-merge/app` và `clinic-cms-merge/tests` không tìm thấy module medicine/inventory đã ship cũng như test tự động cho MED, và các catalog cũ TASK-001..TASK-051 không bao phủ nhóm MED. Vì vậy toàn bộ test case dưới đây được gán **Coverage hiện tại: MISSING** (chưa có test/code) — đây là bộ catalog định nghĩa kỳ vọng để triển khai & kiểm thử khi các task MED được thực hiện.
>
> Các quy ước HTTP & nghiệp vụ áp dụng chung:
> - Multi-tenant: mọi bảng domain đều có `clinic_id` + PostgreSQL RLS. Mọi truy vấn chỉ trả về dữ liệu của clinic trong JWT context (`app.current_clinic_id`). Test cô lập clinic = bắt buộc cho mọi function đụng dữ liệu domain.
> - Auth: thiếu token → `401 Unauthorized`; có token nhưng thiếu permission/role → `403 Forbidden`.
> - Audit: thao tác ghi (create/update/delete/approve/import/adjust) phải sinh bản ghi audit (actor, clinic_id, entity, before/after, timestamp).
> - Số lượng & tiền: kiểm tra số âm, tràn số, làm tròn, đơn vị quy đổi.

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| MED-001 | Medicine catalog CRUD | ⬜ TODO (v1, TASK-011) | TC-MED-001, TC-MED-002, TC-MED-003, TC-MED-004, TC-MED-005, TC-MED-006 | MISSING |
| MED-002 | Phân loại thuốc (Kê đơn/OTC/kiểm soát) | ⬜ TODO (v1, TASK-011) | TC-MED-007, TC-MED-008, TC-MED-009 | MISSING |
| MED-003 | Multi-unit conversion | ⬜ TODO (v1, TASK-011) | TC-MED-010, TC-MED-011, TC-MED-012 | MISSING |
| MED-004 | Min/max stock alert | ⬜ TODO (v1, TASK-012) | TC-MED-013, TC-MED-014, TC-MED-015 | MISSING |
| MED-005 | Lot/batch tracking | ⬜ TODO (v1, TASK-012) | TC-MED-016, TC-MED-017, TC-MED-018 | MISSING |
| MED-006 | Stock movement audit | ⬜ TODO (v1, TASK-012) | TC-MED-019, TC-MED-020, TC-MED-021 | MISSING |
| MED-007 | Expiry tracking (30/60/90 ngày) | ⬜ TODO (v1, TASK-012) | TC-MED-022, TC-MED-023, TC-MED-024 | MISSING |
| MED-008 | FEFO suggestion | ⬜ TODO (v1, TASK-012) | TC-MED-025, TC-MED-026, TC-MED-027 | MISSING |
| MED-009 | Stock import (PO) | ⬜ TODO (v1, TASK-012) | TC-MED-028, TC-MED-029, TC-MED-030, TC-MED-031 | MISSING |
| MED-010 | Stock adjustment | ⬜ TODO (v1, TASK-012) | TC-MED-032, TC-MED-033, TC-MED-034, TC-MED-035 | MISSING |
| MED-011 | Adjustment approval | ⬜ TODO (v1, TASK-012) | TC-MED-036, TC-MED-037, TC-MED-038, TC-MED-039 | MISSING |
| MED-012 | Reorder suggestion | 💡 Idea (v2) | TC-MED-040, TC-MED-041 | MISSING |
| MED-013 | Substitute medicine | 💡 Idea (v2) | TC-MED-042, TC-MED-043 | MISSING |
| MED-014 | Supplier catalog | ⬜ TODO (v1, TASK-012) | TC-MED-044, TC-MED-045, TC-MED-046, TC-MED-047 | MISSING |
| MED-015 | Cost tracking (giá vốn + WAC) | ⬜ TODO (v1, TASK-012) | TC-MED-048, TC-MED-049, TC-MED-050, TC-MED-051 | MISSING |
| MED-016 | Margin report | ⬜ TODO (v1, TASK-015) | TC-MED-052, TC-MED-053, TC-MED-054 | MISSING |
| MED-017 | Barcode scan | 💡 Idea (v2) | TC-MED-055, TC-MED-056 | MISSING |
| MED-018 | Bulk import CSV catalog | 💡 Idea (v2) | TC-MED-057, TC-MED-058, TC-MED-059, TC-MED-060 | MISSING |

**Tổng kết coverage theo function:** COVERED = 0 · PARTIAL = 0 · MISSING = 18.

---

## 2. Chi tiết Test Cases

### TC-MED-001 — Tạo thuốc mới đầy đủ thông tin (happy path)
- **Function:** MED-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập với role Clinic Admin của clinic A; có permission `medicine:create`.
- **Bước thực hiện:** 1) POST `/medicines` với body hợp lệ. 2) Đọc lại bằng GET `/medicines/{id}`.
- **Dữ liệu test:** `{ name: "Paracetamol 500mg", active_ingredient: "Paracetamol", strength: "500mg", dosage_form: "Viên nén", base_unit: "viên", category: "OTC" }`.
- **Kết quả mong đợi:** `201 Created`; bản ghi gắn `clinic_id` của A; audit create được tạo; GET trả về đúng các trường đã nhập.
- **Coverage hiện tại:** MISSING

### TC-MED-002 — Validate trường bắt buộc khi tạo thuốc
- **Function:** MED-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập Clinic Admin.
- **Bước thực hiện:** 1) POST `/medicines` thiếu `name`/`base_unit`. 2) POST với `strength` rỗng.
- **Dữ liệu test:** `{ active_ingredient: "Paracetamol" }` (thiếu name, base_unit).
- **Kết quả mong đợi:** `422 Unprocessable Entity`; thông báo lỗi rõ trường thiếu; không tạo bản ghi.
- **Coverage hiện tại:** MISSING

### TC-MED-003 — Cập nhật & xóa mềm thuốc; chống trùng tên trong cùng clinic
- **Function:** MED-001
- **Loại:** Negative / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có thuốc "Paracetamol 500mg" trong clinic A.
- **Bước thực hiện:** 1) PUT cập nhật `min_stock`. 2) POST tạo thuốc trùng tên+hàm lượng → kỳ vọng lỗi unique. 3) DELETE (soft) thuốc.
- **Dữ liệu test:** Trùng `name="Paracetamol 500mg"` + `strength="500mg"`.
- **Kết quả mong đợi:** PUT `200`; POST trùng `409 Conflict`; DELETE đặt `is_active=false` / `deleted_at`, không xóa cứng (giữ liên kết kho/đơn).
- **Coverage hiện tại:** MISSING

### TC-MED-004 — Liệt kê & tìm kiếm thuốc có phân trang/lọc còn hàng
- **Function:** MED-001
- **Loại:** Happy path / Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Clinic A có >25 thuốc; có thuốc hết hàng và còn hàng.
- **Bước thực hiện:** 1) GET `/medicines?q=para&page=1&size=20`. 2) GET với `in_stock_only=true`.
- **Dữ liệu test:** từ khóa "para", filter chip "Chỉ hiện thuốc còn hàng".
- **Kết quả mong đợi:** `200`; phân trang đúng; filter loại bỏ thuốc `available_qty=0`; thuốc loại External không bị filter theo stock.
- **Coverage hiện tại:** MISSING

### TC-MED-005 — Bảo mật: 401 chưa auth & 403 thiếu quyền (MED-001)
- **Function:** MED-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User role Receptionist (không có `medicine:create`).
- **Bước thực hiện:** 1) POST `/medicines` không token. 2) POST `/medicines` với token Receptionist.
- **Dữ liệu test:** Body thuốc hợp lệ.
- **Kết quả mong đợi:** Bước 1 → `401`; Bước 2 → `403`; không tạo bản ghi.
- **Coverage hiện tại:** MISSING

### TC-MED-006 — RLS: cô lập danh mục thuốc giữa các clinic (MED-001)
- **Function:** MED-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và clinic B đều có thuốc; user thuộc clinic A.
- **Bước thực hiện:** 1) GET `/medicines` (context A). 2) GET `/medicines/{id_của_B}`.
- **Dữ liệu test:** id thuốc thuộc clinic B.
- **Kết quả mong đợi:** Bước 1 chỉ trả thuốc của A; Bước 2 → `404 Not Found` (RLS ẩn dữ liệu B, không lộ tồn tại).
- **Coverage hiện tại:** MISSING

### TC-MED-007 — Gán phân loại thuốc (Kê đơn / OTC / Kiểm soát đặc biệt)
- **Function:** MED-002
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có thuốc; role Clinic Admin.
- **Bước thực hiện:** 1) PUT `/medicines/{id}` đặt `category=PRESCRIPTION`. 2) Đặt `category=CONTROLLED`.
- **Dữ liệu test:** enum {OTC, PRESCRIPTION, CONTROLLED}.
- **Kết quả mong đợi:** `200`; lưu đúng enum; audit ghi thay đổi phân loại.
- **Coverage hiện tại:** MISSING

### TC-MED-008 — Từ chối phân loại không hợp lệ
- **Function:** MED-002
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có thuốc.
- **Bước thực hiện:** PUT đặt `category="ABC"` (ngoài enum).
- **Dữ liệu test:** giá trị enum sai.
- **Kết quả mong đợi:** `422`; không cập nhật.
- **Coverage hiện tại:** MISSING

### TC-MED-009 — Thuốc kiểm soát đặc biệt yêu cầu ràng buộc khi kê/xuất
- **Function:** MED-002
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc category=CONTROLLED.
- **Bước thực hiện:** 1) Truy vấn danh sách thuốc CONTROLLED. 2) Kiểm tra cờ yêu cầu kê đơn/ghi nhận đặc biệt được trả về.
- **Dữ liệu test:** thuốc kiểm soát.
- **Kết quả mong đợi:** API trả `requires_prescription=true`, đánh dấu để UI cảnh báo; thuốc OTC trả `requires_prescription=false`.
- **Coverage hiện tại:** MISSING

### TC-MED-010 — Khai báo quy đổi đa đơn vị (1 hộp = 10 vỉ × 10 viên)
- **Function:** MED-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc tồn tại; base_unit="viên".
- **Bước thực hiện:** 1) POST `/medicines/{id}/units` định nghĩa vỉ=10 viên, hộp=10 vỉ. 2) GET đọc lại cấu trúc unit.
- **Dữ liệu test:** `[{unit:"vỉ", factor:10}, {unit:"hộp", factor:100}]`.
- **Kết quả mong đợi:** `201`; hệ số quy đổi về base_unit chính xác (hộp=100 viên).
- **Coverage hiện tại:** MISSING

### TC-MED-011 — Quy đổi số lượng nhập/xuất theo đơn vị
- **Function:** MED-003
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Đã cấu hình unit ở TC-MED-010.
- **Bước thực hiện:** Nhập 2 hộp → kiểm tra tồn quy đổi sang viên.
- **Dữ liệu test:** 2 hộp.
- **Kết quả mong đợi:** Tồn tăng đúng 200 viên (base_unit); hiển thị lại theo đơn vị lớn khi đủ.
- **Coverage hiện tại:** MISSING

### TC-MED-012 — Chặn hệ số quy đổi không hợp lệ
- **Function:** MED-003
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc tồn tại.
- **Bước thực hiện:** POST unit với `factor<=0` hoặc trùng tên đơn vị.
- **Dữ liệu test:** `factor=0`, `factor=-5`.
- **Kết quả mong đợi:** `422`; từ chối hệ số ≤ 0 và đơn vị trùng.
- **Coverage hiện tại:** MISSING

### TC-MED-013 — Cảnh báo dưới min stock
- **Function:** MED-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc có `min_stock=20`; tồn hiện 12.
- **Bước thực hiện:** GET `/inventory/alerts` hoặc cờ trên `/medicines`.
- **Dữ liệu test:** available=12, min=20.
- **Kết quả mong đợi:** `200`; thuốc xuất hiện trong alert `BELOW_MIN`; chip amber ở UI.
- **Coverage hiện tại:** MISSING

### TC-MED-014 — Cảnh báo vượt max stock
- **Function:** MED-004
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc có `max_stock=500`; tồn 520.
- **Bước thực hiện:** GET alerts.
- **Dữ liệu test:** available=520, max=500.
- **Kết quả mong đợi:** Alert `ABOVE_MAX` xuất hiện.
- **Coverage hiện tại:** MISSING

### TC-MED-015 — Ngưỡng biên: tồn = min, tồn = max (không cảnh báo sai)
- **Function:** MED-004
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** min=20, max=500.
- **Bước thực hiện:** Đặt tồn lần lượt =20 và =500.
- **Dữ liệu test:** available∈{20,500}.
- **Kết quả mong đợi:** Tồn = min/max không tạo cảnh báo (chỉ < min hoặc > max mới cảnh báo).
- **Coverage hiện tại:** MISSING

### TC-MED-016 — Tạo lô với số lô + HSD khi nhập
- **Function:** MED-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc tồn tại; role Pharmacist.
- **Bước thực hiện:** Tạo lô qua phiếu nhập với `lot_no`, `expiry_date`, `qty`.
- **Dữ liệu test:** `{lot_no:"240425", expiry_date:"2027-04-30", qty:200}`.
- **Kết quả mong đợi:** `201`; lô lưu gắn `clinic_id`; tồn theo lô = 200.
- **Coverage hiện tại:** MISSING

### TC-MED-017 — Chặn HSD ở quá khứ & số lô trùng
- **Function:** MED-005
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có lô "240425".
- **Bước thực hiện:** 1) Tạo lô với `expiry_date` < hôm nay. 2) Tạo lô trùng `lot_no` cùng thuốc.
- **Dữ liệu test:** expiry=2020-01-01; lot_no="240425".
- **Kết quả mong đợi:** Bước 1 `422` (HSD quá khứ); Bước 2 `409` hoặc gộp vào lô hiện có theo quy tắc thiết kế.
- **Coverage hiện tại:** MISSING

### TC-MED-018 — RLS lô thuốc & tồn theo clinic
- **Function:** MED-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B đều có lô.
- **Bước thực hiện:** GET `/medicines/{id}/lots` ở context A cho id thuộc B.
- **Dữ liệu test:** id thuốc/lô của B.
- **Kết quả mong đợi:** `404`; không lộ lô của clinic khác.
- **Coverage hiện tại:** MISSING

### TC-MED-019 — Ghi nhận stock movement IN/OUT kèm lý do
- **Function:** MED-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc có lô tồn.
- **Bước thực hiện:** 1) Tạo movement OUT (xuất kê đơn). 2) GET `/inventory/movements?medicine_id=...`.
- **Dữ liệu test:** `{type:"OUT", qty:5, reason:"PRESCRIPTION", ref_id:<rx>}`.
- **Kết quả mong đợi:** `201`; tồn giảm 5; movement có actor, reason, ref, timestamp, before/after qty.
- **Coverage hiện tại:** MISSING

### TC-MED-020 — Audit trail không thể sửa/xóa
- **Function:** MED-006
- **Loại:** Negative / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có movement.
- **Bước thực hiện:** PUT/DELETE lên movement đã ghi.
- **Dữ liệu test:** movement id.
- **Kết quả mong đợi:** `405`/`403` — bản ghi movement là append-only; điều chỉnh phải qua phiếu adjustment (MED-010), không sửa trực tiếp.
- **Coverage hiện tại:** MISSING

### TC-MED-021 — Chặn xuất vượt tồn (movement OUT > available)
- **Function:** MED-006
- **Loại:** Negative / Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tồn khả dụng = 12.
- **Bước thực hiện:** Tạo movement OUT qty=20.
- **Dữ liệu test:** qty=20 > available=12.
- **Kết quả mong đợi:** `409`/`422` "Vượt tồn kho — chỉ xuất được 12"; tồn không đổi; không tạo movement.
- **Coverage hiện tại:** MISSING

### TC-MED-022 — Cảnh báo HSD theo ngưỡng 30/60/90 ngày
- **Function:** MED-007
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có lô HSD trong 25, 50, 85 ngày tới.
- **Bước thực hiện:** GET `/inventory/expiry-alerts`.
- **Dữ liệu test:** 3 lô với khoảng HSD khác nhau.
- **Kết quả mong đợi:** Phân nhóm đúng vào bucket ≤30 (đỏ), ≤60 (cam), ≤90 (vàng).
- **Coverage hiện tại:** MISSING

### TC-MED-023 — Lô đã hết hạn được đánh dấu & loại khỏi tồn khả dụng
- **Function:** MED-007
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lô có `expiry_date` < hôm nay.
- **Bước thực hiện:** GET tồn khả dụng & danh sách lô hết hạn.
- **Dữ liệu test:** lô expired qty=30.
- **Kết quả mong đợi:** Lô expired không tính vào `available_qty`; xuất hiện trong danh sách EXPIRED chờ hủy.
- **Coverage hiện tại:** MISSING

### TC-MED-024 — Biên ngày: HSD đúng ngày hôm nay
- **Function:** MED-007
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Lô `expiry_date` = hôm nay.
- **Bước thực hiện:** Đánh giá phân loại HSD.
- **Dữ liệu test:** expiry = 2026-05-30.
- **Kết quả mong đợi:** Theo quy tắc thiết kế (thường: còn dùng hết ngày hôm nay → bucket ≤30 đỏ), nhất quán không lẫn EXPIRED.
- **Coverage hiện tại:** MISSING

### TC-MED-025 — Gợi ý lô theo FEFO khi xuất
- **Function:** MED-008
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc có 2 lô: 240310 (HSD 03/2027) và 240425 (HSD 04/2027).
- **Bước thực hiện:** GET `/medicines/{id}/fefo-suggestion?qty=...`.
- **Dữ liệu test:** xuất 150 viên.
- **Kết quả mong đợi:** Gợi ý lấy lô HSD sớm nhất (240310) trước; trả breakdown đúng thứ tự FEFO.
- **Coverage hiện tại:** MISSING

### TC-MED-026 — FEFO bắc cầu nhiều lô khi 1 lô không đủ
- **Function:** MED-008
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Lô A=120, lô B=200 (A sớm hạn hơn).
- **Bước thực hiện:** Xuất 150.
- **Dữ liệu test:** qty=150.
- **Kết quả mong đợi:** Lấy 120 từ A + 30 từ B; tổng = 150; không đụng lô hết hạn.
- **Coverage hiện tại:** MISSING

### TC-MED-027 — FEFO khi tổng tồn không đủ
- **Function:** MED-008
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tổng tồn = 100.
- **Bước thực hiện:** Yêu cầu FEFO cho qty=150.
- **Dữ liệu test:** qty=150 > tồn 100.
- **Kết quả mong đợi:** Trả lỗi/cảnh báo "chỉ đáp ứng 100"; không tạo xuất.
- **Coverage hiện tại:** MISSING

### TC-MED-028 — Tạo phiếu nhập (PO) từ nhà cung cấp
- **Function:** MED-009
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Role Pharmacist; supplier tồn tại.
- **Bước thực hiện:** POST `/stock-imports` với nhiều dòng (thuốc, lô, HSD, qty, đơn giá).
- **Dữ liệu test:** 2 dòng thuốc, supplier_id hợp lệ.
- **Kết quả mong đợi:** `201`; tồn theo lô tăng; movement IN sinh cho từng dòng; giá vốn cập nhật (liên kết MED-015).
- **Coverage hiện tại:** MISSING

### TC-MED-029 — Phiếu nhập tham chiếu supplier không hợp lệ
- **Function:** MED-009
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Pharmacist.
- **Bước thực hiện:** POST phiếu nhập với `supplier_id` không tồn tại / thuộc clinic khác.
- **Dữ liệu test:** supplier_id của clinic B.
- **Kết quả mong đợi:** `422`/`404`; không tạo phiếu; không cộng tồn.
- **Coverage hiện tại:** MISSING

### TC-MED-030 — Bảo mật phiếu nhập: 401 & 403
- **Function:** MED-009
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User Receptionist không có `stock:import`.
- **Bước thực hiện:** 1) POST không token. 2) POST với token Receptionist.
- **Dữ liệu test:** phiếu nhập hợp lệ.
- **Kết quả mong đợi:** `401` rồi `403`; không tạo phiếu.
- **Coverage hiện tại:** MISSING

### TC-MED-031 — RLS phiếu nhập theo clinic
- **Function:** MED-009
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A & B có phiếu nhập.
- **Bước thực hiện:** GET `/stock-imports` context A; GET phiếu id của B.
- **Dữ liệu test:** import id của B.
- **Kết quả mong đợi:** Danh sách chỉ của A; chi tiết phiếu B → `404`.
- **Coverage hiện tại:** MISSING

### TC-MED-032 — Tạo phiếu điều chỉnh tồn khi kiểm kê
- **Function:** MED-010
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Role Pharmacist; tồn hệ thống = 100, thực kiểm = 95.
- **Bước thực hiện:** POST `/stock-adjustments` chênh lệch -5, kèm lý do.
- **Dữ liệu test:** `{medicine_id, lot_id, delta:-5, reason:"Kiểm kê hao hụt"}`.
- **Kết quả mong đợi:** `201`; phiếu ở trạng thái `PENDING` (chờ duyệt MED-011); tồn CHƯA đổi cho tới khi duyệt.
- **Coverage hiện tại:** MISSING

### TC-MED-033 — Điều chỉnh yêu cầu lý do bắt buộc
- **Function:** MED-010
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Pharmacist.
- **Bước thực hiện:** POST adjustment thiếu `reason`.
- **Dữ liệu test:** reason rỗng.
- **Kết quả mong đợi:** `422`; không tạo phiếu.
- **Coverage hiện tại:** MISSING

### TC-MED-034 — Điều chỉnh âm vượt tồn hiện có
- **Function:** MED-010
- **Loại:** Edge / Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tồn lô = 5.
- **Bước thực hiện:** POST adjustment delta=-10.
- **Dữ liệu test:** delta=-10 > tồn 5.
- **Kết quả mong đợi:** `422` (không cho tồn âm) hoặc theo quy tắc cho phép nhưng chặn duyệt; tài liệu hóa rõ.
- **Coverage hiện tại:** MISSING

### TC-MED-035 — RLS điều chỉnh theo clinic
- **Function:** MED-010
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** A & B có phiếu adjustment.
- **Bước thực hiện:** GET phiếu adjustment id của B ở context A.
- **Dữ liệu test:** adjustment id của B.
- **Kết quả mong đợi:** `404`.
- **Coverage hiện tại:** MISSING

### TC-MED-036 — Admin duyệt phiếu điều chỉnh (state PENDING → APPROVED)
- **Function:** MED-011
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có phiếu adjustment PENDING (delta -5); role Admin.
- **Bước thực hiện:** POST `/stock-adjustments/{id}/approve`.
- **Dữ liệu test:** phiếu PENDING.
- **Kết quả mong đợi:** `200`; state=APPROVED; tồn áp dụng (-5); sinh movement audit với approver; timestamp duyệt.
- **Coverage hiện tại:** MISSING

### TC-MED-037 — Từ chối phiếu điều chỉnh (PENDING → REJECTED)
- **Function:** MED-011
- **Loại:** Happy path / State machine
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Phiếu PENDING.
- **Bước thực hiện:** POST `/reject` kèm lý do.
- **Dữ liệu test:** reason="Số liệu chưa đúng".
- **Kết quả mong đợi:** `200`; state=REJECTED; tồn KHÔNG đổi; audit ghi.
- **Coverage hiện tại:** MISSING

### TC-MED-038 — Chống tự duyệt & duyệt 2 lần
- **Function:** MED-011
- **Loại:** Negative / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Phiếu PENDING do user X tạo.
- **Bước thực hiện:** 1) User X (Pharmacist, không phải Admin) approve. 2) Approve phiếu đã APPROVED lần nữa.
- **Dữ liệu test:** cùng phiếu.
- **Kết quả mong đợi:** Bước 1 `403` (cần Admin / không tự duyệt); Bước 2 `409` (state không hợp lệ — không từ APPROVED sang APPROVED).
- **Coverage hiện tại:** MISSING

### TC-MED-039 — Bảo mật duyệt: 401 chưa auth
- **Function:** MED-011
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Phiếu PENDING.
- **Bước thực hiện:** POST `/approve` không token.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** `401`.
- **Coverage hiện tại:** MISSING

### TC-MED-040 — Gợi ý nhập lại theo tốc độ tiêu thụ (v2)
- **Function:** MED-012
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có lịch sử xuất 30 ngày; thuốc gần min_stock.
- **Bước thực hiện:** GET `/inventory/reorder-suggestions`.
- **Dữ liệu test:** thuốc có velocity ~10 viên/ngày, tồn 30.
- **Kết quả mong đợi:** Trả gợi ý số lượng & thời điểm nhập; tính theo lead-time + tốc độ tiêu thụ.
- **Coverage hiện tại:** MISSING (v2 idea — chưa lập task)

### TC-MED-041 — Reorder không gợi ý khi tồn dư dả
- **Function:** MED-012
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Tồn >> max consumption.
- **Bước thực hiện:** GET reorder-suggestions.
- **Dữ liệu test:** tồn 1000, velocity 1/ngày.
- **Kết quả mong đợi:** Không có gợi ý cho thuốc này.
- **Coverage hiện tại:** MISSING (v2 idea)

### TC-MED-042 — Gợi ý thuốc tương đương khi hết hàng (v2)
- **Function:** MED-013
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc A hết hàng; có thuốc B cùng hoạt chất/hàm lượng còn hàng (đã khai báo tương đương).
- **Bước thực hiện:** GET `/medicines/{A}/substitutes`.
- **Dữ liệu test:** A=Paracetamol 500mg hết hàng.
- **Kết quả mong đợi:** Trả danh sách thuốc tương đương còn hàng (B); dùng trong banner "Đề xuất thuốc tương đương" ở form kê đơn.
- **Coverage hiện tại:** MISSING (v2 idea)

### TC-MED-043 — Substitute không trả thuốc khác hoạt chất / hết hàng
- **Function:** MED-013
- **Loại:** Edge / Negative
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** B cùng hoạt chất nhưng cũng hết hàng; C khác hoạt chất.
- **Bước thực hiện:** GET substitutes của A.
- **Dữ liệu test:** B hết hàng, C khác hoạt chất.
- **Kết quả mong đợi:** Loại B (hết hàng) và C (khác hoạt chất) khỏi gợi ý; trả rỗng nếu không có tương đương còn hàng.
- **Coverage hiện tại:** MISSING (v2 idea)

### TC-MED-044 — CRUD nhà cung cấp
- **Function:** MED-014
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Role Clinic Admin.
- **Bước thực hiện:** POST/GET/PUT/DELETE `/suppliers`.
- **Dữ liệu test:** `{name:"Cty Dược ABC", tax_code, phone, address}`.
- **Kết quả mong đợi:** CRUD đúng; gắn `clinic_id`; audit ghi.
- **Coverage hiện tại:** MISSING

### TC-MED-045 — Validate & chống trùng mã số thuế supplier
- **Function:** MED-014
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có supplier với tax_code X.
- **Bước thực hiện:** Tạo supplier trùng tax_code; tạo supplier thiếu name.
- **Dữ liệu test:** tax_code trùng; name rỗng.
- **Kết quả mong đợi:** `409`/`422` tương ứng.
- **Coverage hiện tại:** MISSING

### TC-MED-046 — Bảo mật supplier: 401 & 403
- **Function:** MED-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User thiếu quyền supplier.
- **Bước thực hiện:** POST `/suppliers` không token; rồi với token thiếu quyền.
- **Dữ liệu test:** body supplier.
- **Kết quả mong đợi:** `401` rồi `403`.
- **Coverage hiện tại:** MISSING

### TC-MED-047 — RLS supplier theo clinic
- **Function:** MED-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** A & B có supplier.
- **Bước thực hiện:** GET supplier id của B ở context A.
- **Dữ liệu test:** supplier id của B.
- **Kết quả mong đợi:** `404`; danh sách chỉ của A.
- **Coverage hiện tại:** MISSING

### TC-MED-048 — Cập nhật giá vốn theo phiếu nhập (WAC bình quân gia quyền)
- **Function:** MED-015
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit
- **Tiền điều kiện:** Tồn 100 @ giá vốn 1.000đ; nhập thêm 100 @ 1.200đ.
- **Bước thực hiện:** Nhập lô mới → tính lại WAC.
- **Dữ liệu test:** (100×1000 + 100×1200)/200.
- **Kết quả mong đợi:** WAC = 1.100đ; lưu lịch sử giá vốn.
- **Coverage hiện tại:** MISSING

### TC-MED-049 — Lịch sử giá vốn được lưu theo thời điểm
- **Function:** MED-015
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có >=2 lần nhập giá khác nhau.
- **Bước thực hiện:** GET `/medicines/{id}/cost-history`.
- **Dữ liệu test:** 2 mốc giá.
- **Kết quả mong đợi:** Trả lịch sử có timestamp + giá; WAC hiện hành đúng.
- **Coverage hiện tại:** MISSING

### TC-MED-050 — Làm tròn & tiền tệ trong tính giá vốn
- **Function:** MED-015
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Giá lẻ gây số thập phân.
- **Bước thực hiện:** Nhập số lượng/giá lẻ → kiểm tra làm tròn VND.
- **Dữ liệu test:** 3 đơn vị @ 1.001đ.
- **Kết quả mong đợi:** Làm tròn nhất quán theo quy tắc tiền tệ VND; không sai lệch tích lũy.
- **Coverage hiện tại:** MISSING

### TC-MED-051 — RLS giá vốn theo clinic
- **Function:** MED-015
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** A & B có giá vốn.
- **Bước thực hiện:** GET cost-history thuốc của B ở context A.
- **Dữ liệu test:** id thuốc B.
- **Kết quả mong đợi:** `404`; không lộ giá vốn clinic khác.
- **Coverage hiện tại:** MISSING

### TC-MED-052 — Báo cáo lợi nhuận thuốc (margin = giá bán − giá vốn)
- **Function:** MED-016
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có dữ liệu bán & giá vốn; role Admin.
- **Bước thực hiện:** GET `/reports/medicine-margin?from=&to=`.
- **Dữ liệu test:** kỳ báo cáo 1 tháng.
- **Kết quả mong đợi:** `200`; margin/sản phẩm + tổng; dùng WAC tại thời điểm bán.
- **Coverage hiện tại:** MISSING

### TC-MED-053 — Margin report rỗng & biên kỳ
- **Function:** MED-016
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Kỳ không có giao dịch.
- **Bước thực hiện:** GET với kỳ rỗng; kỳ `from>to`.
- **Dữ liệu test:** from>to.
- **Kết quả mong đợi:** Kỳ rỗng → tổng 0; `from>to` → `422`.
- **Coverage hiện tại:** MISSING

### TC-MED-054 — Bảo mật margin report: 401 & 403 (chỉ Admin)
- **Function:** MED-016
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User Pharmacist (không có quyền report margin).
- **Bước thực hiện:** GET report không token; rồi với token Pharmacist.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** `401` rồi `403`.
- **Coverage hiện tại:** MISSING

### TC-MED-055 — Quét barcode tra cứu thuốc khi xuất/nhập (v2)
- **Function:** MED-017
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc có `barcode` khai báo.
- **Bước thực hiện:** GET `/medicines/lookup?barcode=...`.
- **Dữ liệu test:** barcode hợp lệ.
- **Kết quả mong đợi:** Trả đúng thuốc tương ứng barcode (trong clinic).
- **Coverage hiện tại:** MISSING (v2 idea)

### TC-MED-056 — Barcode không tồn tại / trùng
- **Function:** MED-017
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** —
- **Bước thực hiện:** Lookup barcode không có; tạo 2 thuốc cùng barcode.
- **Dữ liệu test:** barcode lạ; barcode trùng.
- **Kết quả mong đợi:** Lookup → `404`; tạo trùng barcode → `409`.
- **Coverage hiện tại:** MISSING (v2 idea)

### TC-MED-057 — Import CSV danh mục thuốc hợp lệ (v2)
- **Function:** MED-018
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Role Clinic Admin; file CSV đúng schema.
- **Bước thực hiện:** POST `/medicines/import` (multipart CSV).
- **Dữ liệu test:** CSV 50 dòng hợp lệ.
- **Kết quả mong đợi:** `200`; tạo/cập nhật đúng số dòng; báo cáo kết quả import; tất cả gắn clinic hiện tại.
- **Coverage hiện tại:** MISSING (v2 idea)

### TC-MED-058 — Import CSV có dòng lỗi (partial / báo lỗi từng dòng)
- **Function:** MED-018
- **Loại:** Negative / Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** CSV có dòng thiếu cột bắt buộc, dòng trùng tên.
- **Bước thực hiện:** POST import.
- **Dữ liệu test:** CSV 10 dòng, 3 lỗi.
- **Kết quả mong đợi:** Báo cáo chi tiết dòng lỗi + dòng thành công; quy tắc all-or-nothing vs partial được tài liệu hóa & nhất quán.
- **Coverage hiện tại:** MISSING (v2 idea)

### TC-MED-059 — Import CSV sai định dạng / quá lớn
- **Function:** MED-018
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** File không phải CSV / vượt giới hạn kích thước.
- **Bước thực hiện:** POST file .xlsx nhị phân hoặc file > giới hạn.
- **Dữ liệu test:** file sai định dạng.
- **Kết quả mong đợi:** `422`/`413`; không import.
- **Coverage hiện tại:** MISSING (v2 idea)

### TC-MED-060 — Bảo mật import: 401 & 403
- **Function:** MED-018
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User thiếu quyền import.
- **Bước thực hiện:** POST import không token; rồi với token thiếu quyền.
- **Dữ liệu test:** CSV hợp lệ.
- **Kết quả mong đợi:** `401` rồi `403`; không import.
- **Coverage hiện tại:** MISSING (v2 idea)

---

## 3. Tổng kết & khuyến nghị

- **Bao phủ function:** 18/18 (100%). Mỗi function có ≥1 happy-path; các function CRUD / state machine / tiền-kho-quyền (MED-001, 005, 006, 009, 010, 011, 014, 015) có thêm Negative/Edge/Security.
- **Coverage thực tế:** 0 COVERED · 0 PARTIAL · 18 MISSING. Toàn bộ MED chưa có code/test đã ship (Status nguồn ⬜/💡; không tìm thấy module medicine/inventory & test trong `clinic-cms-merge`).
- **Rủi ro lớn nhất cần ưu tiên kiểm thử khi triển khai:** (1) Tính nhất quán tồn kho qua state machine adjustment PENDING→APPROVED và tính append-only của stock movement; (2) Logic FEFO + chặn xuất vượt tồn; (3) RLS cô lập clinic trên mọi bảng kho/giá vốn/supplier.
