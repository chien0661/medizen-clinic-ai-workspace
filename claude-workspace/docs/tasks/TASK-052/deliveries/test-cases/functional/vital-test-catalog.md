# Test Case Catalog — VITAL · Sinh hiệu (Vitals)

**Nguồn:** function_list_data.py (group VITAL, mã VTL-001…VTL-014) + clinic_management_function_list.md (mục 7. VITAL — Sinh hiệu) + system_design/BA (visit state machine WAITING_VITAL → VITAL_DONE → IN_CONSULTATION, xem VIS-003).
**Phạm vi:** 14 functions (VTL-001 … VTL-014).  **Tổng test case:** 46.  **Ngày:** 2026-05-30.

> **Ghi chú nguồn & coverage:**
> - File dữ liệu chuẩn `function_list_data.py` liệt kê 14 mục VITAL. Trong đó **VTL-009 (Pediatric percentile chart)** và **VTL-010 (OBGYN tuần thai tracker)** ở trạng thái **IDEA / phase v2** (💡, task `—`); 12 mục còn lại ở trạng thái **TODO / phase v1** (gắn `TASK-009`).
> - Đối chiếu code thực tế trong `clinic-cms-merge`: **không tồn tại** file `*vital*`, không có tham chiếu `vital_schema` / `vital_data` / `WAITING_VITAL` / `VITAL_DONE`, không có module Python tương ứng → module VITAL **chưa được ship**.
> - Đối chiếu test thực tế (`clinic-cms-merge/tests`) và catalog cũ TASK-001..TASK-051: **không có** test/case nào phủ VITAL.
> - Kết luận: toàn bộ 14 function VITAL có Coverage = **MISSING**. Bộ catalog này là tập test case dự kiến (forward-looking) để khi TASK-009 implement sẽ dùng làm chuẩn nghiệm thu.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| VTL-001 | 5 specialty preset (General/Pediatric/Dental/OBGYN/TCM) | TODO (v1) | TC-VITAL-001, TC-VITAL-002, TC-VITAL-003 | MISSING |
| VTL-002 | Dynamic field schema (JSONB linh hoạt) | TODO (v1) | TC-VITAL-004, TC-VITAL-005, TC-VITAL-006 | MISSING |
| VTL-003 | Field types: number/text/select/bool | TODO (v1) | TC-VITAL-007, TC-VITAL-008, TC-VITAL-009 | MISSING |
| VTL-004 | Range bình thường (normal/warning) | TODO (v1) | TC-VITAL-010, TC-VITAL-011 | MISSING |
| VTL-005 | Auto-calc fields (BMI từ weight+height) | TODO (v1) | TC-VITAL-012, TC-VITAL-013, TC-VITAL-014 | MISSING |
| VTL-006 | Vital trends chart | TODO (v1) | TC-VITAL-015, TC-VITAL-016 | MISSING |
| VTL-007 | Schema editor (admin) | TODO (v1) | TC-VITAL-017, TC-VITAL-018, TC-VITAL-019, TC-VITAL-020 | MISSING |
| VTL-008 | Schema versioning (immutable, không phá visit cũ) | TODO (v1) | TC-VITAL-021, TC-VITAL-022, TC-VITAL-023 | MISSING |
| VTL-009 | Pediatric percentile chart (vs WHO) | IDEA (v2) | TC-VITAL-024, TC-VITAL-025 | MISSING |
| VTL-010 | OBGYN tuần thai tracker | IDEA (v2) | TC-VITAL-026, TC-VITAL-027 | MISSING |
| VTL-011 | TCM mạch/lưỡi (free text) | TODO (v1) | TC-VITAL-028, TC-VITAL-029 | MISSING |
| VTL-012 | Required field per preset | TODO (v1) | TC-VITAL-030, TC-VITAL-031, TC-VITAL-032 | MISSING |
| VTL-013 | Vital input by nurse (nurse fill, doctor verify) | TODO (v1) | TC-VITAL-033, TC-VITAL-034, TC-VITAL-035, TC-VITAL-036, TC-VITAL-037, TC-VITAL-038, TC-VITAL-039 | MISSING |
| VTL-014 | Vital alert thresholds (warning/critical) | TODO (v1) | TC-VITAL-040, TC-VITAL-041, TC-VITAL-042, TC-VITAL-043, TC-VITAL-044, TC-VITAL-045, TC-VITAL-046 | MISSING |

**Tổng kết coverage theo function:** COVERED = 0 · PARTIAL = 0 · MISSING = 14.

---

## 2. Chi tiết Test Cases

### TC-VITAL-001 — Seed & lấy danh sách 5 preset sinh hiệu chuẩn
- **Function:** VTL-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic onboarding đã seed 5 preset chuẩn (General, Pediatric, Dental, OBGYN, TCM). User role nurse/doctor có quyền đọc preset.
- **Bước thực hiện:** 1) GET `/vital-schemas` (hoặc `/vital-presets`). 2) Kiểm tra response.
- **Dữ liệu test:** clinic_id của tenant hiện hành.
- **Kết quả mong đợi:** HTTP 200; trả về 5 preset; preset General chứa field BP, HR, temp, SpO2, weight, height. Shape mảng JSON với `id, code, name, is_active`.
- **Coverage hiện tại:** MISSING (chưa có module/test VITAL trong clinic-cms-merge)

### TC-VITAL-002 — Lấy chi tiết một preset kèm danh sách field
- **Function:** VTL-001
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tồn tại preset Pediatric (có length, head circumference, percentile).
- **Bước thực hiện:** 1) GET `/vital-schemas/{id}`. 2) Đọc `fields[]`.
- **Dữ liệu test:** id = Pediatric.
- **Kết quả mong đợi:** HTTP 200; `fields[]` đầy đủ thuộc tính {code, name, type, unit, range, required, order}.
- **Coverage hiện tại:** MISSING

### TC-VITAL-003 — Cô lập preset theo clinic (RLS)
- **Function:** VTL-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và Clinic B mỗi clinic có vital_schema riêng.
- **Bước thực hiện:** 1) Đăng nhập user clinic A, GET `/vital-schemas`. 2) Đăng nhập user clinic B, GET `/vital-schemas/{schema_id_của_A}`.
- **Dữ liệu test:** schema_id của clinic A.
- **Kết quả mong đợi:** User A chỉ thấy schema clinic A; user B nhận 404/403 với schema của A (RLS theo clinic_id chặn).
- **Coverage hiện tại:** MISSING

### TC-VITAL-004 — Tạo vital_schema động (fields JSONB) cho clinic
- **Function:** VTL-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic Admin có quyền cấu hình schema.
- **Bước thực hiện:** 1) POST `/vital-schemas` với `fields` = mảng định nghĩa field. 2) GET lại schema.
- **Dữ liệu test:** fields gồm spo2 {type:number, unit:%, range:{min:95,max:100}}.
- **Kết quả mong đợi:** HTTP 201; schema lưu vào cột JSONB, không cần migration DDL; `is_active=true`.
- **Coverage hiện tại:** MISSING

### TC-VITAL-005 — Visit lưu vital_data JSONB theo schema active
- **Function:** VTL-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic có 1 schema active.
- **Bước thực hiện:** 1) POST vital cho visit. 2) Kiểm tra bản ghi lưu `vital_data` JSONB + tham chiếu schema_id active.
- **Dữ liệu test:** vital_data hợp lệ theo schema active.
- **Kết quả mong đợi:** HTTP 201; visit.vital_data lưu đúng cấu trúc; gắn schema_id của schema active hiện hành.
- **Coverage hiện tại:** MISSING

### TC-VITAL-006 — Từ chối field trùng code trong schema
- **Function:** VTL-002
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Schema đang có field code `temp`.
- **Bước thực hiện:** 1) POST/PUT schema thêm field code `temp` lần nữa.
- **Dữ liệu test:** code trùng `temp`.
- **Kết quả mong đợi:** HTTP 422/409; lỗi field code trùng; schema không đổi.
- **Coverage hiện tại:** MISSING

### TC-VITAL-007 — Lưu value đúng theo từng field type (number/text/select/bool/date)
- **Function:** VTL-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Schema có đủ các field type.
- **Bước thực hiện:** 1) POST vital_data với value cho từng type. 2) GET lại.
- **Dữ liệu test:** number=37.5, text="ho khan", select="cao", bool=true, date="2026-05-30".
- **Kết quả mong đợi:** HTTP 201; value lưu đúng kiểu (number là số, bool là boolean, date hợp lệ).
- **Coverage hiện tại:** MISSING

### TC-VITAL-008 — Từ chối value sai kiểu (number nhận chữ)
- **Function:** VTL-003
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Field `temp` type number có min/max.
- **Bước thực hiện:** 1) POST vital_data với `temp="abc"`. 2) POST `temp` ngoài min/max.
- **Dữ liệu test:** temp="abc"; temp=999.
- **Kết quả mong đợi:** HTTP 422; lỗi validation theo type & min/max; không lưu.
- **Coverage hiện tại:** MISSING

### TC-VITAL-009 — Field select chỉ chấp nhận value trong options
- **Function:** VTL-003
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Field select có options [thấp, bình thường, cao].
- **Bước thực hiện:** 1) POST value `"rất cao"` (ngoài options).
- **Dữ liệu test:** value="rất cao".
- **Kết quả mong đợi:** HTTP 422; từ chối giá trị ngoài tập options.
- **Coverage hiện tại:** MISSING

### TC-VITAL-010 — Phân loại giá trị theo range normal/warning
- **Function:** VTL-004
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Field BP tâm thu range_normal 90-140, range_warning 80-160.
- **Bước thực hiện:** 1) POST BP=150 (ngoài normal, trong warning). 2) POST BP=170 (ngoài warning). 3) POST BP=120 (normal).
- **Dữ liệu test:** 150 / 170 / 120.
- **Kết quả mong đợi:** Phân loại trả về: 120→normal(xanh), 150→warning(vàng), 170→ngoài warning(đỏ). Lưu thành công, kèm flag mức độ.
- **Coverage hiện tại:** MISSING

### TC-VITAL-011 — Giá trị ở biên range (inclusive)
- **Function:** VTL-004
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** range_normal 90-140.
- **Bước thực hiện:** 1) Đánh giá BP=90 (biên dưới). 2) BP=140 (biên trên).
- **Dữ liệu test:** 90 và 140.
- **Kết quả mong đợi:** Cả hai biên đều được xếp là normal (inclusive theo thiết kế).
- **Coverage hiện tại:** MISSING

### TC-VITAL-012 — Auto-calc BMI từ weight và height
- **Function:** VTL-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Schema có field computed `bmi` công thức weight/(height/100)².
- **Bước thực hiện:** 1) POST weight=70, height=170 (không gửi bmi). 2) Đọc bmi.
- **Dữ liệu test:** weight=70kg, height=170cm.
- **Kết quả mong đợi:** HTTP 201; bmi tự tính ≈ 24.2; field read-only do server tính.
- **Coverage hiện tại:** MISSING

### TC-VITAL-013 — Auto-calc khi thiếu field nguồn
- **Function:** VTL-005
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Field computed bmi phụ thuộc weight+height.
- **Bước thực hiện:** 1) POST chỉ weight, thiếu height.
- **Dữ liệu test:** weight=70, height=null.
- **Kết quả mong đợi:** bmi = null/bỏ qua, không lỗi 500; lưu phần còn lại bình thường.
- **Coverage hiện tại:** MISSING

### TC-VITAL-014 — Client không ghi đè được field computed
- **Function:** VTL-005
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** bmi là field computed.
- **Bước thực hiện:** 1) POST weight=70, height=170, bmi=10 (giả).
- **Dữ liệu test:** bmi=10 do client gửi.
- **Kết quả mong đợi:** Server bỏ qua bmi client gửi, tính lại ≈24.2 (server-authoritative).
- **Coverage hiện tại:** MISSING

### TC-VITAL-015 — Lấy dữ liệu trend chart theo metric & thời gian
- **Function:** VTL-006
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Bệnh nhân có ≥3 visit có vital (BP/weight).
- **Bước thực hiện:** 1) GET `/patients/{id}/vital-trends?metric=bp`.
- **Dữ liệu test:** patient với 3 bản ghi BP.
- **Kết quả mong đợi:** HTTP 200; mảng `{date, value, visit_id}` sắp xếp tăng dần theo thời gian; đánh dấu datapoint bất thường.
- **Coverage hiện tại:** MISSING

### TC-VITAL-016 — Trend chart rỗng khi chưa có dữ liệu
- **Function:** VTL-006
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Bệnh nhân mới, chưa có vital.
- **Bước thực hiện:** 1) GET vital-trends cho patient mới.
- **Dữ liệu test:** patient không có vital.
- **Kết quả mong đợi:** HTTP 200; mảng rỗng `[]`; không lỗi.
- **Coverage hiện tại:** MISSING

### TC-VITAL-017 — Clinic Admin tạo/sửa schema qua editor → version mới
- **Function:** VTL-007
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic Admin có quyền; schema đang active version v1.
- **Bước thực hiện:** 1) PUT `/admin/vital-schema` thêm field + reorder. 2) GET schema active.
- **Dữ liệu test:** thêm field `glucose`, đổi order.
- **Kết quả mong đợi:** HTTP 200/201; tạo version mới immutable, set active; audit ghi thay đổi schema.
- **Coverage hiện tại:** MISSING

### TC-VITAL-018 — Chặn truy cập schema editor khi chưa đăng nhập (401)
- **Function:** VTL-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi token.
- **Bước thực hiện:** 1) PUT `/admin/vital-schema` không kèm Authorization.
- **Dữ liệu test:** request không token.
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING

### TC-VITAL-019 — Nurse không có quyền sửa schema (403)
- **Function:** VTL-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User role nurse (không phải Clinic Admin).
- **Bước thực hiện:** 1) PUT `/admin/vital-schema`.
- **Dữ liệu test:** token nurse.
- **Kết quả mong đợi:** HTTP 403; schema không đổi.
- **Coverage hiện tại:** MISSING

### TC-VITAL-020 — Cô lập schema editor theo clinic (RLS)
- **Function:** VTL-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin clinic A, schema của clinic B.
- **Bước thực hiện:** 1) Admin A PUT/sửa schema thuộc clinic B.
- **Dữ liệu test:** schema_id của B.
- **Kết quả mong đợi:** HTTP 404/403; không sửa được schema clinic khác.
- **Coverage hiện tại:** MISSING

### TC-VITAL-021 — Đổi schema tạo version+1, version cũ is_active=false
- **Function:** VTL-008
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Schema đang ở version v1 is_active=true.
- **Bước thực hiện:** 1) Sửa schema. 2) Truy vấn bảng vital_schema.
- **Dữ liệu test:** thay đổi 1 field.
- **Kết quả mong đợi:** INSERT row version=2 is_active=true; row version=1 set is_active=false (không xóa, immutable).
- **Coverage hiện tại:** MISSING

### TC-VITAL-022 — Visit cũ vẫn hiển thị theo schema_id của nó sau khi đổi schema
- **Function:** VTL-008
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit đo theo schema v1; sau đó nâng schema → v2.
- **Bước thực hiện:** 1) Đo vital (v1). 2) Đổi schema → v2. 3) GET lại visit cũ.
- **Dữ liệu test:** 1 visit cũ.
- **Kết quả mong đợi:** Visit cũ render theo schema v1 (field cũ không mất); visit mới dùng v2 active.
- **Coverage hiện tại:** MISSING

### TC-VITAL-023 — Truy vấn lịch sử version schema (migration history)
- **Function:** VTL-008
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Schema có ≥2 version.
- **Bước thực hiện:** 1) GET `/vital-schemas/versions`.
- **Dữ liệu test:** schema có v1, v2.
- **Kết quả mong đợi:** HTTP 200; danh sách version kèm created_at/created_by, đánh dấu version active.
- **Coverage hiện tại:** MISSING

### TC-VITAL-024 — (v2/IDEA) Tính percentile nhi theo tuổi/giới vs WHO
- **Function:** VTL-009
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Có bảng WHO standard curves (P3, P50, P97). Tính năng phase v2 (IDEA).
- **Bước thực hiện:** 1) Gọi hàm tính percentile với weight/height, age_months, sex.
- **Dữ liệu test:** bé trai 12 tháng, 10kg.
- **Kết quả mong đợi:** Trả về percentile hợp lý (~P50); highlight nếu <P3 hoặc >P97.
- **Coverage hiện tại:** MISSING (chức năng v2 chưa lên kế hoạch implement)

### TC-VITAL-025 — (v2/IDEA) Percentile chỉ áp dụng preset Pediatric
- **Function:** VTL-009
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit dùng preset General (người lớn).
- **Bước thực hiện:** 1) Yêu cầu percentile chart cho visit người lớn.
- **Dữ liệu test:** patient người lớn.
- **Kết quả mong đợi:** Không tính/không hiển thị percentile nhi; trả về rỗng hoặc 422 hợp lý.
- **Coverage hiện tại:** MISSING

### TC-VITAL-026 — (v2/IDEA) Tracker tuần thai theo nhiều visit
- **Function:** VTL-010
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Preset OBGYN; bệnh nhân có nhiều visit theo tuần thai. Tính năng phase v2 (IDEA).
- **Bước thực hiện:** 1) GET tracker theo dõi BP/cân nặng/đo bụng/tim thai theo tuần thai.
- **Dữ liệu test:** 3 visit ở tuần 12, 20, 28.
- **Kết quả mong đợi:** Chart theo tuần thai so với chuẩn; sắp xếp đúng theo tuần.
- **Coverage hiện tại:** MISSING

### TC-VITAL-027 — (v2/IDEA) Cảnh báo lệch chuẩn (vd cân nặng tăng nhanh)
- **Function:** VTL-010
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Có ngưỡng cảnh báo pre-eclampsia risk.
- **Bước thực hiện:** 1) Nhập chuỗi cân nặng tăng đột biến.
- **Dữ liệu test:** cân nặng +5kg/2 tuần.
- **Kết quả mong đợi:** Phát cảnh báo lệch chuẩn; không crash.
- **Coverage hiện tại:** MISSING

### TC-VITAL-028 — Nhập mạch chẩn/thiệt chẩn TCM (free text)
- **Function:** VTL-011
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Preset TCM có field text 'Mạch chẩn', 'Thiệt chẩn' (no strict validation).
- **Bước thực hiện:** 1) POST vital_data mạch="Phù hư", lưỡi="Đỏ, ít rêu".
- **Dữ liệu test:** mạch="Phù hư", lưỡi="Đỏ, ít rêu".
- **Kết quả mong đợi:** HTTP 201; lưu nguyên văn free text; hiển thị trong hồ sơ.
- **Coverage hiện tại:** MISSING

### TC-VITAL-029 — Field TCM chỉ xuất hiện ở preset TCM
- **Function:** VTL-011
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Visit dùng preset General.
- **Bước thực hiện:** 1) Mở form vital preset General.
- **Dữ liệu test:** preset General.
- **Kết quả mong đợi:** Không render field Mạch chẩn/Thiệt chẩn TCM.
- **Coverage hiện tại:** MISSING

### TC-VITAL-030 — Lưu thành công khi điền đủ field bắt buộc
- **Function:** VTL-012
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Preset General required BP+HR+weight+height.
- **Bước thực hiện:** 1) POST vital đầy đủ field required.
- **Dữ liệu test:** BP, HR, weight, height đều có.
- **Kết quả mong đợi:** HTTP 201; lưu thành công.
- **Coverage hiện tại:** MISSING

### TC-VITAL-031 — Từ chối lưu khi thiếu field bắt buộc
- **Function:** VTL-012
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Preset General required BP.
- **Bước thực hiện:** 1) POST vital thiếu BP.
- **Dữ liệu test:** payload không có BP.
- **Kết quả mong đợi:** HTTP 422; lỗi liệt kê field thiếu; không lưu.
- **Coverage hiện tại:** MISSING

### TC-VITAL-032 — Required set khác nhau theo preset
- **Function:** VTL-012
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Pediatric required head_circumference; General không.
- **Bước thực hiện:** 1) POST vital Pediatric thiếu head_circumference → lỗi. 2) POST vital General thiếu head_circumference → OK.
- **Dữ liệu test:** hai preset khác required set.
- **Kết quả mong đợi:** Pediatric 422; General 201 (validation tôn trọng required theo preset).
- **Coverage hiện tại:** MISSING

### TC-VITAL-033 — Nurse nhập vital → visit WAITING_VITAL chuyển VITAL_DONE
- **Function:** VTL-013
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit status=WAITING_VITAL; user role nurse có quyền nhập vital.
- **Bước thực hiện:** 1) Nurse POST `/visits/{id}/vitals`. 2) GET visit.
- **Dữ liệu test:** visit WAITING_VITAL, payload vital hợp lệ.
- **Kết quả mong đợi:** HTTP 201; visit.status=VITAL_DONE; audit event `nurse_input` (actor=nurse).
- **Coverage hiện tại:** MISSING

### TC-VITAL-034 — Doctor thấy vital điền sẵn và có thể edit
- **Function:** VTL-013
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit VITAL_DONE, nurse đã nhập vital; doctor có quyền edit.
- **Bước thực hiện:** 1) Doctor GET visit thấy vital. 2) Doctor PUT sửa 1 field. 3) GET lại.
- **Dữ liệu test:** sửa temp 37.0 → 37.8.
- **Kết quả mong đợi:** HTTP 200; field cập nhật; audit event `doctor_verified`/`vital_edited` (actor=doctor).
- **Coverage hiện tại:** MISSING

### TC-VITAL-035 — Chưa đăng nhập không nhập được vital (401)
- **Function:** VTL-013
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi token.
- **Bước thực hiện:** 1) POST `/visits/{id}/vitals` không Authorization.
- **Dữ liệu test:** request không token.
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING

### TC-VITAL-036 — Role không có quyền nhập vital bị chặn (403)
- **Function:** VTL-013
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User role receptionist (không có quyền nhập vital).
- **Bước thực hiện:** 1) POST vital cho visit.
- **Dữ liệu test:** token receptionist.
- **Kết quả mong đợi:** HTTP 403; visit không đổi state.
- **Coverage hiện tại:** MISSING

### TC-VITAL-037 — Cô lập vital theo clinic (RLS)
- **Function:** VTL-013
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit thuộc clinic A; nurse thuộc clinic B.
- **Bước thực hiện:** 1) Nurse B POST vital cho visit của clinic A.
- **Dữ liệu test:** visit_id của clinic A.
- **Kết quả mong đợi:** HTTP 404/403; RLS không cho ghi vital chéo clinic.
- **Coverage hiện tại:** MISSING

### TC-VITAL-038 — Không nhập vital khi visit ở state không hợp lệ
- **Function:** VTL-013
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit status=COMPLETED (hoặc CANCELLED).
- **Bước thực hiện:** 1) Nurse POST vital cho visit COMPLETED.
- **Dữ liệu test:** visit COMPLETED.
- **Kết quả mong đợi:** HTTP 409/422; không cho nhập vital ngoài WAITING_VITAL/VITAL_DONE; state không đổi.
- **Coverage hiện tại:** MISSING

### TC-VITAL-039 — Audit ghi đủ sự kiện nurse_input và doctor_verified
- **Function:** VTL-013
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quy trình đầy đủ nurse nhập → doctor verify.
- **Bước thực hiện:** 1) Nurse nhập vital. 2) Doctor verify. 3) Truy vấn audit log.
- **Dữ liệu test:** 1 visit qua trọn quy trình.
- **Kết quả mong đợi:** Audit có 2 event riêng `nurse_input` (actor nurse) và `doctor_verified` (actor doctor) kèm timestamp + actor_id chính xác.
- **Coverage hiện tại:** MISSING

### TC-VITAL-040 — Cấu hình thresholds (warning/critical) cho field
- **Function:** VTL-014
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic Admin có quyền cấu hình ngưỡng.
- **Bước thực hiện:** 1) PUT thresholds cho BP tâm thu {warning_high:140, critical_high:180}. 2) GET lại.
- **Dữ liệu test:** warning_high=140, critical_high=180.
- **Kết quả mong đợi:** HTTP 200; thresholds lưu trong schema field; audit ghi thay đổi.
- **Coverage hiện tại:** MISSING

### TC-VITAL-041 — Vital vượt ngưỡng critical sinh cảnh báo
- **Function:** VTL-014
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** critical_high BP=180.
- **Bước thực hiện:** 1) POST BP=190. 2) Đọc response.
- **Dữ liệu test:** BP=190.
- **Kết quả mong đợi:** Lưu thành công; trả về `alert_level=critical` (background đỏ + icon ⚠️ trên UI).
- **Coverage hiện tại:** MISSING

### TC-VITAL-042 — Vital bình thường không cảnh báo
- **Function:** VTL-014
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** thresholds đã set.
- **Bước thực hiện:** 1) POST BP trong khoảng bình thường.
- **Dữ liệu test:** BP=120.
- **Kết quả mong đợi:** `alert_level=none`; không cảnh báo.
- **Coverage hiện tại:** MISSING

### TC-VITAL-043 — Phân tầng warning vs critical
- **Function:** VTL-014
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** warning_high=140, critical_high=180.
- **Bước thực hiện:** 1) Tính alert cho 150. 2) Tính alert cho 190.
- **Dữ liệu test:** 150 và 190.
- **Kết quả mong đợi:** 150 → warning (vàng); 190 → critical (đỏ). Phân tầng đúng.
- **Coverage hiện tại:** MISSING

### TC-VITAL-044 — Chưa đăng nhập không cấu hình được thresholds (401)
- **Function:** VTL-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi token.
- **Bước thực hiện:** 1) PUT thresholds không Authorization.
- **Dữ liệu test:** request không token.
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING

### TC-VITAL-045 — Thiếu quyền không cấu hình thresholds (403)
- **Function:** VTL-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User role nurse (không phải Clinic Admin).
- **Bước thực hiện:** 1) PUT thresholds.
- **Dữ liệu test:** token nurse.
- **Kết quả mong đợi:** HTTP 403; thresholds không đổi.
- **Coverage hiện tại:** MISSING

### TC-VITAL-046 — Cô lập cấu hình thresholds theo clinic (RLS)
- **Function:** VTL-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B có thresholds riêng.
- **Bước thực hiện:** 1) Admin A đọc/sửa thresholds của clinic B.
- **Dữ liệu test:** cấu hình của clinic B.
- **Kết quả mong đợi:** HTTP 404/403; mỗi clinic chỉ thấy/sửa thresholds của mình.
- **Coverage hiện tại:** MISSING

---

## 3. Ghi chú coverage & rủi ro

- **Trạng thái triển khai:** Module VITAL chưa được implement (không có file/code/test trong `clinic-cms-merge`). Toàn bộ 14 function ở trạng thái chưa làm (12 TODO/v1 gắn TASK-009; VTL-009, VTL-010 là IDEA/v2). Coverage = MISSING 100%.
- **Phụ thuộc state machine Visit (VIS-003):** VTL-013 gắn chặt transition `WAITING_VITAL → VITAL_DONE`. Khi VISIT module đổi rule transition cần re-test TC-VITAL-033/038. Lưu ý visit có 8 state; chỉ doctor mới set IN_CONSULTATION → COMPLETED.
- **Khu vực rủi ro cao (ưu tiên P0 khi implement):**
  1. Dynamic schema JSONB + versioning immutable (VTL-002/008) — sai version làm hỏng hiển thị bản ghi lịch sử.
  2. Auto-calc computed server-authoritative (VTL-005) — client không được ghi đè BMI.
  3. Nurse nhập vital + chuyển state + RLS + audit kép (VTL-013).
  4. Cấu hình + đánh giá thresholds lâm sàng (VTL-014, VTL-004).
- **Khuyến nghị khi TASK-009 chạy:** Ưu tiên xác lập COVERED cho nhóm P0 (TC-VITAL-001, 004, 007, 012, 017, 021, 030, 033, 041) bằng integration test trên real DB + RLS context; nhóm security (401/403/RLS) bắt buộc xanh trước khi DONE.
- **Các TC v2/IDEA (TC-VITAL-024..027):** đánh dấu P2, chỉ thực thi khi VTL-009/VTL-010 được đưa vào phase v2; hiện giữ làm placeholder để bảo đảm bao phủ 100% function list.
