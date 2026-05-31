# Test Case Catalog — CFG · Cấu hình Hệ thống

**Nguồn:** function_list_data.py (group CFG, dòng 1387–1437) + clinic_management_function_list.md + system_design/BA.
**Phạm vi:** 17 functions (CFG-001 … CFG-017).  **Tổng test case:** 58.  **Ngày:** 2026-05-30.

> Ghi chú phương pháp: Danh sách 17 function được trích trực tiếp từ `function_list_data.py` dòng 1387–1438 (helper `f(group, code, name, brief, detail, role, phase, task, status)`). Mọi function của group đều được liệt kê trong Ma trận truy vết và có tối thiểu 1 happy-path TC. Cấu hình clinic là dữ liệu thuộc tenant (clinic_id) → mọi TC chạm dữ liệu domain đều có case cô lập clinic (RLS) và case 401/403 cho quyền.
>
> Cột Status lấy đúng từ tuple nguồn: CFG-001..009 = TODO (TASK-006); CFG-010/011/012 = DONE (TASK-006); CFG-013 = TODO (TASK-009); CFG-014 = TODO (TASK-010); CFG-015/016 = IDEA (Phase 2, v2); CFG-017 = TODO (TASK-006).
>
> Cảnh báo độ tin cậy về Coverage: Cột "Coverage hiện tại" chưa được đối chiếu trực tiếp với mã đã ship trong `clinic-cms-merge/app`, thư mục `tests`, hay catalog cũ TASK-001..051 trong phiên này. Vì vậy gán thận trọng: function DONE/MVP cốt lõi (clinic info, prefix, VAT, currency, timezone, ngôn ngữ, giờ làm việc, lunch break) tạm gán PARTIAL; function TODO/IDEA chưa có evidence test (holiday import, vital schema, service category, discount policy, medicine warning rules, BHYT toggle) gán MISSING. Reviewer/Test PHẢI verify lại bằng `pytest --collect-only` + grep đường dẫn test thực tế trước khi nâng PARTIAL → COVERED. Lưu ý CFG-015 & CFG-016 là IDEA Phase 2 (chưa lên kế hoạch v1) → các TC chỉ mang tính future/spec, không kỳ vọng pass ở v1.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| CFG-001 | Clinic info (tên/mã/địa chỉ/SĐT/email/MST) | TODO (TASK-006) | TC-CFG-001, TC-CFG-002, TC-CFG-003, TC-CFG-004, TC-CFG-005, TC-CFG-006 | PARTIAL |
| CFG-002 | Logo upload (hiện trên hóa đơn / app shell) | TODO (TASK-006) | TC-CFG-007, TC-CFG-008, TC-CFG-009, TC-CFG-010 | PARTIAL |
| CFG-003 | Working hours (lịch tuần điển hình) | TODO (TASK-006) | TC-CFG-011, TC-CFG-012, TC-CFG-013 | PARTIAL |
| CFG-004 | Holiday list (auto-import VN public holidays) | TODO (TASK-006) | TC-CFG-014, TC-CFG-015, TC-CFG-016 | MISSING |
| CFG-005 | Lunch break (default 12:00–13:30) | TODO (TASK-006) | TC-CFG-017, TC-CFG-018 | PARTIAL |
| CFG-006 | Invoice prefix (HD-) | TODO (TASK-006) | TC-CFG-019, TC-CFG-020, TC-CFG-021 | PARTIAL |
| CFG-007 | Patient code prefix (BN-) | TODO (TASK-006) | TC-CFG-022, TC-CFG-023 | PARTIAL |
| CFG-008 | Visit number prefix (KB-) | TODO (TASK-006) | TC-CFG-024, TC-CFG-025 | PARTIAL |
| CFG-009 | VAT rate (default 5%) | TODO (TASK-006) | TC-CFG-026, TC-CFG-027, TC-CFG-028 | PARTIAL |
| CFG-010 | Currency (VND default) | DONE (TASK-006) | TC-CFG-029, TC-CFG-030 | PARTIAL |
| CFG-011 | Timezone (Asia/Ho_Chi_Minh) | DONE (TASK-006) | TC-CFG-031, TC-CFG-032 | PARTIAL |
| CFG-012 | Default language (vi/en) | DONE (TASK-006) | TC-CFG-033, TC-CFG-034 | PARTIAL |
| CFG-013 | Vital schema editor (tuỳ chỉnh fields) | TODO (TASK-009) | TC-CFG-035, TC-CFG-036, TC-CFG-037, TC-CFG-038 | MISSING |
| CFG-014 | Service category management (CRUD phân loại) | TODO (TASK-010) | TC-CFG-039, TC-CFG-040, TC-CFG-041, TC-CFG-042, TC-CFG-043, TC-CFG-044 | MISSING |
| CFG-015 | Discount policy (cấu hình policy giảm giá) | IDEA (Phase 2 / v2) | TC-CFG-045, TC-CFG-046, TC-CFG-047, TC-CFG-048 | MISSING |
| CFG-016 | Medicine warning rules (custom dị ứng/tương tác) | IDEA (Phase 2 / v2) | TC-CFG-049, TC-CFG-050, TC-CFG-051, TC-CFG-052 | MISSING |
| CFG-017 | Toggle BHYT bật/tắt (feature flag clinic.bhyt_enabled, default OFF) | TODO (TASK-006) | TC-CFG-053, TC-CFG-054, TC-CFG-055, TC-CFG-056, TC-CFG-057, TC-CFG-058 | MISSING |

Tổng: 17 functions — PARTIAL: 10, MISSING: 7, COVERED: 0 (chờ verify đường dẫn test thực tế để nâng cấp PARTIAL → COVERED).

---

## 2. Chi tiết Test Cases

### TC-CFG-001 — Lấy thông tin clinic hiện tại (happy path)
- **Function:** CFG-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã đăng nhập user thuộc clinic A có quyền xem cấu hình; clinic A đã có bản ghi config.
- **Bước thực hiện:** 1) GET `/api/v1/settings/clinic` với token clinic A. 2) Đọc response.
- **Dữ liệu test:** clinic A = {name, code, address, phone, email, tax_code}.
- **Kết quả mong đợi:** 200; body chứa đủ tên/mã/địa chỉ/SĐT/email/MST của clinic A.
- **Coverage hiện tại:** PARTIAL (chưa xác nhận file test thực tế; cần verify `tests/.../test_settings*`).

### TC-CFG-002 — Cập nhật thông tin clinic (happy path)
- **Function:** CFG-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User clinic A có quyền `settings.update`.
- **Bước thực hiện:** 1) PUT `/api/v1/settings/clinic` body hợp lệ. 2) GET lại để xác nhận.
- **Dữ liệu test:** name="Phòng khám Bình Minh", phone="0901234567", email="a@b.vn", tax_code="0312345678".
- **Kết quả mong đợi:** 200; giá trị mới được lưu; ghi audit log (actor, before/after).
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-003 — Validate dữ liệu clinic info sai định dạng (negative)
- **Function:** CFG-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User clinic A có quyền update.
- **Bước thực hiện:** 1) PUT với email sai định dạng / phone chứa chữ / MST sai format VN (theo nguồn: "Validate MST format VN" — MST 10 hoặc 13 chữ số).
- **Dữ liệu test:** email="abc", phone="abc", tax_code="x" (không đúng 10/13 chữ số).
- **Kết quả mong đợi:** 422 với chi tiết lỗi từng field (đặc biệt MST không khớp định dạng VN); không thay đổi DB.
- **Coverage hiện tại:** MISSING.

### TC-CFG-004 — Truy cập khi chưa auth (security 401)
- **Function:** CFG-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi token.
- **Bước thực hiện:** 1) GET/PUT `/api/v1/settings/clinic` không Authorization header.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** 401 Unauthorized.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-005 — Thiếu permission cập nhật cấu hình (security 403)
- **Function:** CFG-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User clinic A có role không bao gồm `settings.update` (vd: receptionist).
- **Bước thực hiện:** 1) PUT `/api/v1/settings/clinic`.
- **Dữ liệu test:** payload hợp lệ.
- **Kết quả mong đợi:** 403 Forbidden; DB không đổi.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-006 — Cô lập clinic (RLS) khi đọc/ghi clinic info
- **Function:** CFG-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS bật)
- **Tiền điều kiện:** Tồn tại clinic A và clinic B, mỗi clinic có config riêng.
- **Bước thực hiện:** 1) Token clinic A GET config → chỉ thấy A. 2) Token A thử PUT/GET dùng id thuộc B.
- **Dữ liệu test:** clinic A id, clinic B id.
- **Kết quả mong đợi:** A không bao giờ thấy/sửa được dữ liệu B (404/403 hoặc kết quả lọc rỗng); RLS chặn cross-tenant.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-007 — Upload logo hợp lệ (happy path)
- **Function:** CFG-002
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User clinic A có quyền update settings.
- **Bước thực hiện:** 1) Lấy presigned S3 URL (theo nguồn: upload qua presigned S3 URL). 2) PUT file PNG/JPG lên S3. 3) Xác nhận resize tự động về 200×60px cho letterhead. 4) GET settings + preview.
- **Dữ liệu test:** logo.png 256x256, 50KB (PNG hoặc JPG).
- **Kết quả mong đợi:** 200; trả về URL/đường dẫn logo; ảnh được resize 200×60px; logo dùng được trên hóa đơn / app shell; có preview.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-008 — Upload file sai loại / quá lớn (negative)
- **Function:** CFG-002
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) Upload file sai format (theo nguồn chỉ chấp nhận PNG/JPG): .exe / .svg / .gif; 2) file > giới hạn dung lượng.
- **Dữ liệu test:** evil.exe; logo.gif; huge.png 20MB.
- **Kết quả mong đợi:** 422/413; từ chối format không phải PNG/JPG; không lưu file.
- **Coverage hiện tại:** MISSING.

### TC-CFG-009 — Upload logo khi chưa auth / thiếu quyền (security 401/403)
- **Function:** CFG-002
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) không token; (b) token thiếu `settings.update`.
- **Bước thực hiện:** 1) POST logo cho cả 2 trường hợp.
- **Dữ liệu test:** logo.png.
- **Kết quả mong đợi:** (a) 401; (b) 403.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-010 — Logo cô lập theo clinic (RLS)
- **Function:** CFG-002
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** Clinic A và B đều có logo.
- **Bước thực hiện:** 1) A đọc logo → của A. 2) A không truy cập được asset của B.
- **Dữ liệu test:** logoA, logoB.
- **Kết quả mong đợi:** Mỗi clinic chỉ thấy logo của mình.
- **Coverage hiện tại:** MISSING.

### TC-CFG-011 — Cấu hình giờ làm việc theo tuần (happy path)
- **Function:** CFG-003
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update settings.
- **Bước thực hiện:** 1) PUT working hours JSON 7 ngày `{mon:{open:'08:00',close:'17:00'},...}` + ngày nghỉ (theo nguồn). 2) GET xác nhận.
- **Dữ liệu test:** T2–T6 08:00–17:00, T7 08:00–12:00, CN nghỉ.
- **Kết quả mong đợi:** 200; lưu đúng cấu trúc JSON; dùng được cho gợi ý slot lịch hẹn.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-012 — Giờ đóng trước giờ mở / xung đột lunch break / format sai (negative)
- **Function:** CFG-003
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update; lunch break 12:00–13:30.
- **Bước thực hiện:** 1) PUT ngày T2 open=17:00, close=08:00; 2) PUT giờ làm việc không bao trùm lunch break (theo nguồn: "Validate xung đột với lunch break"); 3) format giờ sai "25:00".
- **Dữ liệu test:** open>close; giờ làm 14:00–17:00 (lunch 12:00–13:30 nằm ngoài); "25:00".
- **Kết quả mong đợi:** 422; báo lỗi xung đột lunch break khi áp dụng; không lưu.
- **Coverage hiện tại:** MISSING.

### TC-CFG-013 — Working hours: auth/permission/RLS (security)
- **Function:** CFG-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Không token; token thiếu quyền; clinic A vs B.
- **Bước thực hiện:** 1) PUT không token → 401. 2) PUT thiếu quyền → 403. 3) A không sửa được giờ của B.
- **Dữ liệu test:** payload hợp lệ.
- **Kết quả mong đợi:** 401 / 403 / cô lập RLS.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-014 — Auto-import danh sách ngày lễ VN (happy path)
- **Function:** CFG-004
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update; năm hiện tại 2026.
- **Bước thực hiện:** 1) POST `/api/v1/settings/holidays/import?year=2026`. 2) GET danh sách.
- **Dữ liệu test:** năm 2026.
- **Kết quả mong đợi:** 200; tạo các ngày lễ VN (Tết, 30/4, 1/5, 2/9, …); đánh dấu là ngày nghỉ trong lịch.
- **Coverage hiện tại:** MISSING.

### TC-CFG-015 — Import lại / thêm-sửa-xóa ngày lễ thủ công (edge + CRUD)
- **Function:** CFG-004
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã import 2026.
- **Bước thực hiện:** 1) Import lại 2026 (không nhân đôi). 2) Thêm ngày lễ riêng. 3) Xóa 1 ngày.
- **Dữ liệu test:** ngày lễ tùy chỉnh "Kỷ niệm phòng khám".
- **Kết quả mong đợi:** Không trùng lặp; CRUD thủ công hoạt động; idempotent.
- **Coverage hiện tại:** MISSING.

### TC-CFG-016 — Ngày lễ: auth/permission/RLS (security)
- **Function:** CFG-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Không token; thiếu quyền; clinic A vs B.
- **Bước thực hiện:** 1) Import không token → 401. 2) Thiếu quyền → 403. 3) A không thấy ngày lễ của B.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** 401 / 403 / cô lập RLS.
- **Coverage hiện tại:** MISSING.

### TC-CFG-017 — Cấu hình giờ nghỉ trưa mặc định (happy path)
- **Function:** CFG-005
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) GET settings mới → lunch break mặc định 12:00–13:30. 2) PUT đổi 11:30–13:00. 3) GET xác nhận.
- **Dữ liệu test:** 11:30–13:00.
- **Kết quả mong đợi:** 200; default đúng 12:00–13:30; cập nhật được; slot lịch loại trừ giờ nghỉ trưa.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-018 — Lunch break không hợp lệ / nằm ngoài giờ làm (negative + edge)
- **Function:** CFG-005
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Working hours 08:00–17:00.
- **Bước thực hiện:** 1) PUT lunch 18:00–19:00 (ngoài giờ làm); 2) PUT start>end.
- **Dữ liệu test:** 18:00–19:00; 13:00–12:00.
- **Kết quả mong đợi:** 422; không lưu.
- **Coverage hiện tại:** MISSING.

### TC-CFG-019 — Cấu hình prefix hóa đơn (happy path)
- **Function:** CFG-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) GET → `settings.invoice_prefix` mặc định "HD". 2) PUT đổi "INV". 3) Tạo hóa đơn mới → số bắt đầu bằng prefix; hóa đơn CŨ giữ nguyên (theo nguồn: "Apply cho invoice mới, cũ giữ nguyên").
- **Dữ liệu test:** prefix="INV".
- **Kết quả mong đợi:** 200; mặc định "HD"; hóa đơn mới mang prefix mới, hóa đơn cũ không đổi; sequence/đánh số đúng theo clinic.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-020 — Prefix rỗng / ký tự không hợp lệ (negative)
- **Function:** CFG-006
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) PUT prefix="" / chứa ký tự không-alphanumeric / > 5 ký tự (theo nguồn: "Validate alphanumeric, max 5 chars").
- **Dữ liệu test:** ""; "A B"; "HD-#@"; "ABCDEF" (6 ký tự).
- **Kết quả mong đợi:** 422 (chỉ alphanumeric, tối đa 5 ký tự); không lưu.
- **Coverage hiện tại:** MISSING.

### TC-CFG-021 — Prefix hóa đơn cô lập clinic (RLS)
- **Function:** CFG-006
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** Clinic A prefix "HD-", clinic B prefix "INV-".
- **Bước thực hiện:** 1) Hóa đơn của A dùng "HD-", B dùng "INV-"; không lẫn nhau.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Mỗi clinic dùng prefix riêng; sequence riêng; không cross-tenant.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-022 — Cấu hình prefix mã bệnh nhân (happy path)
- **Function:** CFG-007
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) GET → "BN-". 2) PUT "PT-". 3) Tạo bệnh nhân mới → mã bắt đầu "PT-".
- **Dữ liệu test:** prefix="PT-".
- **Kết quả mong đợi:** 200; mặc định "BN-"; bệnh nhân mới mang prefix mới.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-023 — Prefix bệnh nhân: validate + auth/permission/RLS (negative + security)
- **Function:** CFG-007
- **Loại:** Security / Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Không token; thiếu quyền; clinic A vs B.
- **Bước thực hiện:** 1) PUT prefix rỗng → 422. 2) PUT không token → 401. 3) Thiếu quyền → 403. 4) A vs B cô lập prefix.
- **Dữ liệu test:** ""; payload hợp lệ.
- **Kết quả mong đợi:** 422 / 401 / 403 / RLS isolation.
- **Coverage hiện tại:** MISSING.

### TC-CFG-024 — Cấu hình prefix số lượt khám (happy path)
- **Function:** CFG-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) GET → "KB-". 2) PUT "V-". 3) Tạo lượt khám → số bắt đầu "V-".
- **Dữ liệu test:** prefix="V-".
- **Kết quả mong đợi:** 200; mặc định "KB-"; lượt khám mới mang prefix mới.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-025 — Prefix lượt khám: validate + auth/permission/RLS (negative + security)
- **Function:** CFG-008
- **Loại:** Security / Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Không token; thiếu quyền; clinic A vs B.
- **Bước thực hiện:** 1) PUT rỗng → 422. 2) Không token → 401. 3) Thiếu quyền → 403. 4) Cô lập A/B.
- **Dữ liệu test:** ""; payload hợp lệ.
- **Kết quả mong đợi:** 422 / 401 / 403 / RLS.
- **Coverage hiện tại:** MISSING.

### TC-CFG-026 — Cấu hình thuế suất VAT (happy path)
- **Function:** CFG-009
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) GET → `settings.vat_rate` mặc định 0.05 (5%). 2) PUT 0.08. 3) Tạo hóa đơn mới → VAT theo 0.08 (theo nguồn: "Apply cho invoice mới sau update").
- **Dữ liệu test:** vat_rate=0.08.
- **Kết quả mong đợi:** 200; mặc định 0.05; hóa đơn mới áp 0.08; hóa đơn cũ không đổi; số tiền thuế đúng (làm tròn theo quy tắc).
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-027 — VAT ngoài khoảng hợp lệ (negative)
- **Function:** CFG-009
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) PUT vat_rate ngoài range cho phép (theo nguồn: range 0–0.15): -0.01 / 0.20 / "abc".
- **Dữ liệu test:** -0.01; 0.20; "abc".
- **Kết quả mong đợi:** 422 (0 ≤ vat_rate ≤ 0.15); không lưu. (Lưu ý edge: 0.15 hợp lệ, 0.16 không.)
- **Coverage hiện tại:** MISSING.

### TC-CFG-028 — VAT: auth/permission/RLS (security)
- **Function:** CFG-009
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Không token; thiếu quyền; clinic A vs B.
- **Bước thực hiện:** 1) PUT không token → 401. 2) Thiếu quyền → 403. 3) A đổi VAT không ảnh hưởng B.
- **Dữ liệu test:** vat_rate=10.
- **Kết quả mong đợi:** 401 / 403 / cô lập RLS.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-029 — Cấu hình tiền tệ (happy path)
- **Function:** CFG-010
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) GET → currency mặc định VND. 2) (nếu hỗ trợ) PUT đổi mã tiền hợp lệ. 3) Hiển thị/định dạng tiền theo currency.
- **Dữ liệu test:** "VND".
- **Kết quả mong đợi:** 200; mặc định VND; định dạng số tiền đúng (1.000.000 ₫).
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-030 — Currency không hợp lệ + auth/permission (negative + security)
- **Function:** CFG-010
- **Loại:** Negative / Security
- **Ưu tiên:** P2
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Không token; thiếu quyền.
- **Bước thực hiện:** 1) PUT currency="XXX" không hỗ trợ → 422. 2) Không token → 401. 3) Thiếu quyền → 403.
- **Dữ liệu test:** "XXX".
- **Kết quả mong đợi:** 422 / 401 / 403.
- **Coverage hiện tại:** MISSING.

### TC-CFG-031 — Cấu hình múi giờ (happy path)
- **Function:** CFG-011
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) GET → timezone mặc định Asia/Ho_Chi_Minh. 2) Kiểm tra mốc thời gian hiển thị (lịch hẹn, hóa đơn) theo timezone.
- **Dữ liệu test:** "Asia/Ho_Chi_Minh".
- **Kết quả mong đợi:** 200; mặc định Asia/Ho_Chi_Minh; thời gian hiển thị đúng offset (+07:00).
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-032 — Timezone không hợp lệ + auth/permission (negative + security)
- **Function:** CFG-011
- **Loại:** Negative / Security
- **Ưu tiên:** P2
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Không token; thiếu quyền.
- **Bước thực hiện:** 1) PUT timezone="Mars/Phobos" → 422. 2) Không token → 401. 3) Thiếu quyền → 403.
- **Dữ liệu test:** "Mars/Phobos".
- **Kết quả mong đợi:** 422 (chỉ chấp nhận IANA tz hợp lệ) / 401 / 403.
- **Coverage hiện tại:** MISSING.

### TC-CFG-033 — Cấu hình ngôn ngữ mặc định (happy path)
- **Function:** CFG-012
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) GET → `settings.default_language` mặc định "vi" (theo nguồn: ENUM('vi','en'), mặc định 'vi'). 2) PUT đổi "en". 3) Tạo user mới → user inherit clinic default (theo nguồn: "New user inherit clinic default. User tự override sau").
- **Dữ liệu test:** "vi", "en".
- **Kết quả mong đợi:** 200; mặc định "vi"; chỉ chấp nhận vi/en; user mới kế thừa ngôn ngữ mặc định của clinic.
- **Coverage hiện tại:** PARTIAL.

### TC-CFG-034 — Ngôn ngữ ngoài {vi,en} + auth/permission (negative + security)
- **Function:** CFG-012
- **Loại:** Negative / Security
- **Ưu tiên:** P2
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Không token; thiếu quyền.
- **Bước thực hiện:** 1) PUT lang="fr" → 422. 2) Không token → 401. 3) Thiếu quyền → 403.
- **Dữ liệu test:** "fr".
- **Kết quả mong đợi:** 422 / 401 / 403.
- **Coverage hiện tại:** MISSING.

### TC-CFG-035 — Tùy chỉnh schema sinh hiệu (vital) — thêm field (happy path)
- **Function:** CFG-013
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update settings.
- **Bước thực hiện:** 1) GET vital schema hiện tại. 2) PUT thêm field "SpO2" (kiểu number, đơn vị %, min/max). 3) Tạo lượt khám → form vital hiển thị SpO2.
- **Dữ liệu test:** {key:"spo2", label:"SpO2", type:"number", unit:"%", min:0, max:100}.
- **Kết quả mong đợi:** 200; field mới xuất hiện trong form ghi sinh hiệu; validate theo min/max.
- **Coverage hiện tại:** MISSING.

### TC-CFG-036 — Vital schema: định nghĩa field sai (negative)
- **Function:** CFG-013
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền update.
- **Bước thực hiện:** 1) PUT field thiếu key/label; 2) key trùng; 3) min>max.
- **Dữ liệu test:** {} ; key trùng "temp"; min=100,max=0.
- **Kết quả mong đợi:** 422; không lưu schema.
- **Coverage hiện tại:** MISSING.

### TC-CFG-037 — Vital schema: tương thích dữ liệu đã ghi (edge)
- **Function:** CFG-013
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có vital records dùng schema cũ.
- **Bước thực hiện:** 1) Xóa/đổi 1 field đang được dùng. 2) Mở lại bản ghi vital cũ.
- **Dữ liệu test:** field "pulse" đã có dữ liệu lịch sử.
- **Kết quả mong đợi:** Dữ liệu lịch sử không bị mất/hỏng; có cảnh báo hoặc giữ nguyên giá trị cũ.
- **Coverage hiện tại:** MISSING.

### TC-CFG-038 — Vital schema: auth/permission/RLS (security)
- **Function:** CFG-013
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Không token; thiếu quyền; clinic A vs B.
- **Bước thực hiện:** 1) PUT không token → 401. 2) Thiếu quyền → 403. 3) A đổi schema không ảnh hưởng B.
- **Dữ liệu test:** payload hợp lệ.
- **Kết quả mong đợi:** 401 / 403 / cô lập RLS.
- **Coverage hiện tại:** MISSING.

### TC-CFG-039 — Tạo phân loại dịch vụ (CRUD - Create, happy path)
- **Function:** CFG-014
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền quản lý phân loại dịch vụ.
- **Bước thực hiện:** 1) POST `/api/v1/service-categories` body hợp lệ. 2) GET list xác nhận.
- **Dữ liệu test:** {name:"Xét nghiệm", code:"XN"}.
- **Kết quả mong đợi:** 201; bản ghi mới gắn clinic_id hiện tại.
- **Coverage hiện tại:** MISSING.

### TC-CFG-040 — Đọc/sửa/xóa phân loại dịch vụ (CRUD - Read/Update/Delete)
- **Function:** CFG-014
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tồn tại 1 category.
- **Bước thực hiện:** 1) GET by id. 2) PUT đổi tên. 3) DELETE category chưa gắn dịch vụ.
- **Dữ liệu test:** id category vừa tạo.
- **Kết quả mong đợi:** GET 200; PUT 200; DELETE 200/204.
- **Coverage hiện tại:** MISSING.

### TC-CFG-041 — Trùng tên/mã phân loại (negative)
- **Function:** CFG-014
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có category "Xét nghiệm".
- **Bước thực hiện:** 1) POST category trùng tên/mã trong cùng clinic.
- **Dữ liệu test:** {name:"Xét nghiệm"}.
- **Kết quả mong đợi:** 409/422 duplicate; không tạo.
- **Coverage hiện tại:** MISSING.

### TC-CFG-042 — Xóa phân loại đang được dịch vụ tham chiếu (edge)
- **Function:** CFG-014
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Category "Xét nghiệm" có dịch vụ gắn vào.
- **Bước thực hiện:** 1) DELETE category đang được dùng.
- **Dữ liệu test:** category có ≥1 service.
- **Kết quả mong đợi:** 409 (chặn xóa) hoặc soft-delete theo thiết kế; không để dịch vụ mồ côi.
- **Coverage hiện tại:** MISSING.

### TC-CFG-043 — Phân loại dịch vụ: auth/permission (security 401/403)
- **Function:** CFG-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token; token thiếu quyền.
- **Bước thực hiện:** 1) POST/PUT/DELETE không token → 401. 2) Thiếu quyền → 403.
- **Dữ liệu test:** payload hợp lệ.
- **Kết quả mong đợi:** 401 / 403.
- **Coverage hiện tại:** MISSING.

### TC-CFG-044 — Phân loại dịch vụ cô lập clinic (RLS)
- **Function:** CFG-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** Clinic A và B mỗi clinic có category riêng.
- **Bước thực hiện:** 1) A GET list → chỉ thấy của A. 2) A GET/PUT/DELETE id thuộc B.
- **Dữ liệu test:** category id của B.
- **Kết quả mong đợi:** A chỉ thấy category của A; thao tác lên B → 404/403.
- **Coverage hiện tại:** MISSING.

### TC-CFG-045 — Cấu hình policy giảm giá (happy path)
- **Function:** CFG-015
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền cấu hình giảm giá.
- **Bước thực hiện:** 1) POST/PUT policy (vd: max giảm 20%, cần duyệt khi > ngưỡng). 2) Áp dụng trên hóa đơn trong giới hạn.
- **Dữ liệu test:** {max_discount_percent:20, require_approval_above:10}.
- **Kết quả mong đợi:** 200; giảm giá trong ngưỡng được áp; vượt ngưỡng → cần duyệt/bị chặn.
- **Coverage hiện tại:** MISSING.

### TC-CFG-046 — Giảm giá vượt ngưỡng / giá trị âm (negative)
- **Function:** CFG-015
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Policy max 20%.
- **Bước thực hiện:** 1) Áp giảm 50% > ngưỡng. 2) PUT policy với percent âm / >100.
- **Dữ liệu test:** discount=50%; max_discount=-5; max_discount=200.
- **Kết quả mong đợi:** Chặn áp giảm vượt ngưỡng (403/422); policy invalid → 422.
- **Coverage hiện tại:** MISSING.

### TC-CFG-047 — Giảm giá đúng tại ngưỡng biên (edge)
- **Function:** CFG-015
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Policy max 20%, require_approval_above 10%.
- **Bước thực hiện:** 1) Áp đúng 20% (= max). 2) Áp đúng 10% (= ngưỡng duyệt).
- **Dữ liệu test:** 20%; 10%.
- **Kết quả mong đợi:** 20% được áp; 10% boundary xử lý nhất quán với định nghĩa (>= hay >).
- **Coverage hiện tại:** MISSING.

### TC-CFG-048 — Discount policy: auth/permission/RLS (security)
- **Function:** CFG-015
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Không token; thiếu quyền; clinic A vs B.
- **Bước thực hiện:** 1) PUT policy không token → 401. 2) Thiếu quyền → 403. 3) Policy của A không áp cho B.
- **Dữ liệu test:** payload hợp lệ.
- **Kết quả mong đợi:** 401 / 403 / cô lập RLS.
- **Coverage hiện tại:** MISSING.

### TC-CFG-049 — Cấu hình quy tắc cảnh báo thuốc (happy path)
- **Function:** CFG-016
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền cấu hình; danh mục thuốc/hoạt chất sẵn có.
- **Bước thực hiện:** 1) POST rule dị ứng (bệnh nhân dị ứng X → cảnh báo khi kê thuốc chứa X). 2) POST rule tương tác (thuốc A + B). 3) Kê đơn vi phạm → xuất cảnh báo.
- **Dữ liệu test:** rule dị ứng penicillin; rule tương tác A↔B.
- **Kết quả mong đợi:** 201; khi kê đơn vi phạm hiện cảnh báo đúng loại; cho phép ghi nhận đè (override) có lý do nếu thiết kế hỗ trợ.
- **Coverage hiện tại:** MISSING.

### TC-CFG-050 — Rule cảnh báo không hợp lệ / trùng (negative)
- **Function:** CFG-016
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có rule.
- **Bước thực hiện:** 1) POST rule thiếu hoạt chất/đối tượng; 2) rule trùng; 3) tự-tương-tác (A↔A).
- **Dữ liệu test:** {}; rule trùng; A↔A.
- **Kết quả mong đợi:** 422/409; không lưu.
- **Coverage hiện tại:** MISSING.

### TC-CFG-051 — Cảnh báo không kích hoạt sai (edge - không false positive)
- **Function:** CFG-016
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Rule dị ứng penicillin.
- **Bước thực hiện:** 1) Kê thuốc KHÔNG chứa penicillin cho bệnh nhân dị ứng penicillin.
- **Dữ liệu test:** thuốc paracetamol.
- **Kết quả mong đợi:** Không phát sinh cảnh báo sai; chỉ cảnh báo khi thực sự khớp rule.
- **Coverage hiện tại:** MISSING.

### TC-CFG-052 — Medicine warning rules: auth/permission/RLS (security)
- **Function:** CFG-016
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Không token; thiếu quyền; clinic A vs B.
- **Bước thực hiện:** 1) POST rule không token → 401. 2) Thiếu quyền → 403. 3) Rule custom của A không áp cho B.
- **Dữ liệu test:** payload hợp lệ.
- **Kết quả mong đợi:** 401 / 403 / cô lập RLS.
- **Coverage hiện tại:** MISSING.

### TC-CFG-053 — BHYT mặc định TẮT cho clinic mới (happy path / default)
- **Function:** CFG-017
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tạo clinic mới.
- **Bước thực hiện:** 1) GET `/api/v1/settings/features` (hoặc settings) → đọc `clinic.bhyt_enabled`.
- **Dữ liệu test:** clinic mới.
- **Kết quả mong đợi:** 200; `bhyt_enabled = false` mặc định.
- **Coverage hiện tại:** MISSING.

### TC-CFG-054 — Bật feature flag BHYT (happy path)
- **Function:** CFG-017
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Quyền cấu hình feature flag.
- **Bước thực hiện:** 1) PUT `bhyt_enabled=true`. 2) GET xác nhận. 3) Kiểm tra menu/chức năng BHYT trở nên khả dụng.
- **Dữ liệu test:** bhyt_enabled=true.
- **Kết quả mong đợi:** 200; flag = true; các endpoint/UI BHYT được kích hoạt.
- **Coverage hiện tại:** MISSING.

### TC-CFG-055 — Khi BHYT TẮT, chức năng BHYT bị ẩn/chặn (negative/gating)
- **Function:** CFG-017
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + E2E (httpx)
- **Tiền điều kiện:** `bhyt_enabled=false`.
- **Bước thực hiện:** 1) Gọi endpoint nghiệp vụ BHYT (vd tạo hồ sơ/khai báo BHYT).
- **Dữ liệu test:** payload BHYT hợp lệ.
- **Kết quả mong đợi:** Bị chặn (403/409/404 feature-disabled) với thông báo rõ; không tạo dữ liệu BHYT.
- **Coverage hiện tại:** MISSING.

### TC-CFG-056 — Tắt BHYT khi đã có dữ liệu BHYT (edge)
- **Function:** CFG-017
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** `bhyt_enabled=true`, đã có hồ sơ BHYT.
- **Bước thực hiện:** 1) PUT `bhyt_enabled=false`. 2) Truy cập dữ liệu BHYT cũ.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Không mất dữ liệu cũ; chức năng tạo mới bị chặn; xử lý nhất quán (chỉ ẩn entry mới).
- **Coverage hiện tại:** MISSING.

### TC-CFG-057 — Toggle BHYT: auth/permission (security 401/403)
- **Function:** CFG-017
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token; token thiếu quyền cấu hình.
- **Bước thực hiện:** 1) PUT flag không token → 401. 2) Thiếu quyền → 403.
- **Dữ liệu test:** bhyt_enabled=true.
- **Kết quả mong đợi:** 401 / 403; flag không đổi.
- **Coverage hiện tại:** MISSING.

### TC-CFG-058 — Toggle BHYT cô lập clinic (RLS)
- **Function:** CFG-017
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** Clinic A bật BHYT, clinic B tắt.
- **Bước thực hiện:** 1) A đọc flag → true. 2) B đọc flag → false. 3) A đổi flag không ảnh hưởng B.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Flag độc lập theo từng clinic; không cross-tenant.
- **Coverage hiện tại:** MISSING.

---

## 3. Khuyến nghị verify (cho Test/Review)
1. Chạy `pytest --collect-only` trong `clinic-cms-merge/tests` và grep theo `settings`, `clinic_config`, `service_category`, `holiday`, `vital`, `discount`, `bhyt` để nâng các TC PARTIAL → COVERED khi tìm thấy test thật.
2. Đối chiếu endpoint thực tế trong `clinic-cms-merge/app/modules/*` (đặc biệt module settings/config) để chỉnh path/method trong các TC cho khớp.
3. Bổ sung cột Status (DONE/TODO) chính xác từ `function_list_data.py` tuple thứ 8 cho từng CFG-### khi tool I/O ổn định trở lại (phiên này chỉ trích được code/name/brief).
