# Test Case Catalog — DIAG · Chẩn đoán (ICD-10)

**Nguồn:** function_list_data.py (group DIAG) + clinic_management_function_list.md + system_design/BA.
**Phạm vi:** 9 functions (DIAG-001 … DIAG-009).  **Tổng test case:** 31.  **Ngày:** 2026-05-30.

> **CẢNH BÁO ĐỐI CHIẾU CODE (quan trọng):**
> - Đường dẫn `clinic-cms-merge/app` nêu trong brief **KHÔNG tồn tại**. Mã backend thực tế đang nằm tại `E:/MyProject/clinic-cms-workspace/claude-workspace/app`.
> - Backend hiện ship **chỉ** các module: `auth`, `users`, `clinics`, `roles`, RLS, health (xem `app/api/v1`, `app/models`, `app/core`). **KHÔNG có module icd10, visits, diagnosis nào được implement.**
> - Thư mục test thực tế `tests/` chỉ gồm: `test_auth.py`, `test_health.py`, `test_rls.py`, `test_clinics.py`, `test_users.py`, `test_smoke.py` — **không có test nào cho DIAG.**
> - Cột Status trong nguồn ghi DIAG-001..007 = DONE, nhưng **đối chiếu code cho thấy đây là DONE ở mức TASK design/spec (TASK-005/007), CHƯA có code ship.** Do đó toàn bộ Coverage thực tế = **MISSING**.
> - Các chi tiết endpoint / permission / shape dưới đây là **kỳ vọng theo thiết kế** (system_design + function_list), dùng làm spec cho test khi tính năng được implement; chưa phải hành vi đã verify trong code.

> **Đặc tả thiết kế DIAG (tổng hợp từ function_list + BA + system_design):**
> - `Visit.diagnosis` JSONB `{primary: "J02.9", secondary: ["R50.9"], notes: "..."}`; **primary bắt buộc khi visit COMPLETED**; secondary multi (ICD-10 autocomplete); notes free text. Hiển thị trên hóa đơn + đơn thuốc + báo cáo.
> - `Visit.clinical_notes` TEXT (rich text, tối đa ~5000 chars).
> - `Visit.instructions` TEXT (lời dặn, in trên đơn thuốc + summary).
> - `Visit.followup_date` DATE; nếu doctor xác nhận → tạo appointment SCHEDULED tự động.
> - Bảng `icd10_catalog` (code PK, name_vi, name_en, parent_code, chapter) — **GLOBAL, KHÔNG RLS**; full-text search; 22000+ entry dịch tiếng Việt.
> - DIAG-008 (templates) = IDEA v2; DIAG-009 (voice-to-text) = IDEA v3 → chưa implement.
> - Permission kỳ vọng cho nhập diagnosis/clinical/followup: thuộc quyền cập nhật visit của role Doctor (vd `visit:update`).

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| DIAG-001 | Chẩn đoán chính + phụ | DONE (spec) | TC-DIAG-001, TC-DIAG-002, TC-DIAG-003, TC-DIAG-004, TC-DIAG-005, TC-DIAG-006 | MISSING |
| DIAG-002 | Khám lâm sàng (free text) | DONE (spec) | TC-DIAG-007, TC-DIAG-008, TC-DIAG-009 | MISSING |
| DIAG-003 | ICD-10 autocomplete | DONE (spec) | TC-DIAG-010, TC-DIAG-011, TC-DIAG-012, TC-DIAG-013, TC-DIAG-014 | MISSING |
| DIAG-004 | ICD-10 catalog (Vietnamese) | DONE (spec) | TC-DIAG-015, TC-DIAG-016, TC-DIAG-017, TC-DIAG-018, TC-DIAG-019 | MISSING |
| DIAG-005 | Diagnosis history | DONE (spec) | TC-DIAG-020, TC-DIAG-021, TC-DIAG-022 | MISSING |
| DIAG-006 | Lời dặn cuối visit | DONE (spec) | TC-DIAG-023, TC-DIAG-024 | MISSING |
| DIAG-007 | Lịch tái khám | DONE (spec) | TC-DIAG-025, TC-DIAG-026, TC-DIAG-027, TC-DIAG-028, TC-DIAG-029 | MISSING |
| DIAG-008 | Diagnosis templates | IDEA (v2) | TC-DIAG-030 | MISSING |
| DIAG-009 | Voice-to-text input | IDEA (v3) | TC-DIAG-031 | MISSING |

**Tổng kết coverage theo function:** COVERED = 0 · PARTIAL = 0 · MISSING = 9.
(Lý do: không tìm thấy bất kỳ code hay automated test nào cho group DIAG trong codebase hiện tại — module visits/icd10 chưa được implement.)

---

## 2. Chi tiết Test Cases

### TC-DIAG-001 — Lưu chẩn đoán chính + phụ + notes (happy path)
- **Function:** DIAG-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập role Doctor có quyền cập nhật visit; tồn tại visit IN_PROGRESS thuộc clinic hiện tại.
- **Bước thực hiện:** 1) Cập nhật clinical của visit với `diagnosis = {primary: "J02.9", secondary: ["R50.9","J06.9"], notes: "Viêm họng cấp kèm sốt"}`. 2) Đọc lại visit.
- **Dữ liệu test:** primary J02.9, secondary 2 mã hợp lệ, notes free text tiếng Việt.
- **Kết quả mong đợi:** HTTP 200; `Visit.diagnosis` JSONB lưu đúng `{primary, secondary[], notes}`; response trả về diagnosis vừa lưu; audit log ghi update.
- **Coverage hiện tại:** MISSING (module visits chưa implement).

### TC-DIAG-002 — Chẩn đoán chỉ có primary (secondary rỗng)
- **Function:** DIAG-001
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit IN_PROGRESS, doctor có quyền.
- **Bước thực hiện:** 1) Cập nhật `diagnosis = {primary: "I10", secondary: [], notes: null}`.
- **Dữ liệu test:** primary I10, secondary [].
- **Kết quả mong đợi:** HTTP 200; lưu `secondary: []`, `notes: null`; không lỗi.
- **Coverage hiện tại:** MISSING

### TC-DIAG-003 — Hoàn tất visit KHÔNG có primary → bị chặn (state machine)
- **Function:** DIAG-001
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit IN_PROGRESS chưa nhập diagnosis primary.
- **Bước thực hiện:** 1) Thực hiện transition COMPLETE visit khi `diagnosis.primary` rỗng/null.
- **Dữ liệu test:** diagnosis primary = null.
- **Kết quả mong đợi:** HTTP 400/422, message kiểu "Diagnosis (primary) is required to complete a visit"; visit GIỮ status IN_PROGRESS.
- **Coverage hiện tại:** MISSING

### TC-DIAG-004 — Cập nhật clinical sau khi visit đã COMPLETED → bị chặn
- **Function:** DIAG-001
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit đã COMPLETED.
- **Bước thực hiện:** 1) Cập nhật diagnosis của visit đã đóng.
- **Dữ liệu test:** diagnosis primary mới.
- **Kết quả mong đợi:** HTTP 400/409; diagnosis cũ không đổi (immutable sau khi đóng visit).
- **Coverage hiện tại:** MISSING

### TC-DIAG-005 — Cập nhật diagnosis chưa đăng nhập (401) / thiếu permission (403)
- **Function:** DIAG-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit tồn tại; (a) không header Authorization; (b) user role không có quyền cập nhật visit (vd Receptionist).
- **Bước thực hiện:** 1) Cập nhật diagnosis không token → kỳ vọng 401. 2) Bằng token role thiếu quyền → kỳ vọng 403.
- **Dữ liệu test:** token rỗng; token receptionist.
- **Kết quả mong đợi:** (a) HTTP 401; (b) HTTP 403; không ghi dữ liệu.
- **Coverage hiện tại:** MISSING

### TC-DIAG-006 — Cô lập clinic (RLS) khi cập nhật diagnosis
- **Function:** DIAG-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit V1 thuộc clinic A; user thuộc clinic B (có quyền cập nhật visit).
- **Bước thực hiện:** 1) User clinic B cập nhật clinical của V1.
- **Dữ liệu test:** visit_id của clinic khác.
- **Kết quả mong đợi:** HTTP 404 (RLS che visit clinic khác); diagnosis V1 không đổi. (Pattern RLS đã được kiểm chứng ở `tests/test_rls.py` cho các module hiện có — áp dụng tương tự khi ship visits.)
- **Coverage hiện tại:** MISSING

### TC-DIAG-007 — Lưu khám lâm sàng (clinical_notes free text)
- **Function:** DIAG-002
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit IN_PROGRESS, doctor có quyền.
- **Bước thực hiện:** 1) Cập nhật `clinical_notes = "Họng đỏ, amidan sưng, không giả mạc..."`. 2) Đọc lại.
- **Dữ liệu test:** chuỗi rich-text (bold/list markup).
- **Kết quả mong đợi:** HTTP 200; `Visit.clinical_notes` lưu đúng nội dung; giữ tiếng Việt + markup.
- **Coverage hiện tại:** MISSING

### TC-DIAG-008 — clinical_notes vượt giới hạn ~5000 ký tự
- **Function:** DIAG-002
- **Loại:** Edge / Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit IN_PROGRESS.
- **Bước thực hiện:** 1) Cập nhật clinical_notes 6000 ký tự.
- **Dữ liệu test:** string len = 6000.
- **Kết quả mong đợi:** Nếu enforce max-length → HTTP 422; nếu chưa → ghi nhận gap cần thêm validation. Tài liệu hóa hành vi.
- **Coverage hiện tại:** MISSING

### TC-DIAG-009 — clinical_notes không gửi (partial update) giữ giá trị cũ
- **Function:** DIAG-002
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit IN_PROGRESS đã có clinical_notes.
- **Bước thực hiện:** 1) Cập nhật clinical với body không chứa field clinical_notes.
- **Dữ liệu test:** body không có clinical_notes.
- **Kết quả mong đợi:** HTTP 200; clinical_notes giữ nguyên giá trị cũ (partial update, không overwrite null).
- **Coverage hiện tại:** MISSING

### TC-DIAG-010 — Tìm ICD-10 theo code prefix (happy path)
- **Function:** DIAG-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập; catalog seed có J02.9.
- **Bước thực hiện:** 1) Gọi endpoint search ICD-10 với `q=J02`.
- **Dữ liệu test:** q = "J02".
- **Kết quả mong đợi:** HTTP 200; kết quả chứa các code bắt đầu J02; mỗi item có `code, name_vi`; sắp theo code; top-N (≤ 10 mặc định).
- **Coverage hiện tại:** MISSING

### TC-DIAG-011 — Tìm ICD-10 theo tên bệnh tiếng Việt
- **Function:** DIAG-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Catalog có "Viêm họng cấp".
- **Bước thực hiện:** 1) Search với `q=viêm họng`.
- **Dữ liệu test:** q = "viêm họng" (có dấu).
- **Kết quả mong đợi:** HTTP 200; match name_vi; trả về J02.9; case-insensitive; hỗ trợ tiếng Việt có dấu.
- **Coverage hiện tại:** MISSING

### TC-DIAG-012 — Giới hạn kết quả autocomplete (top-N / limit)
- **Function:** DIAG-003
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Query khớp nhiều entries.
- **Bước thực hiện:** 1) Search `q=a` không limit (default). 2) Search với limit vượt max cho phép.
- **Dữ liệu test:** default; limit lớn (vd 999).
- **Kết quả mong đợi:** Default trả ≤ 10 (top 10 theo spec); limit vượt giới hạn → 422 hoặc cap về max. Tài liệu hóa hành vi.
- **Coverage hiện tại:** MISSING

### TC-DIAG-013 — Query rỗng / thiếu q → 422
- **Function:** DIAG-003
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập.
- **Bước thực hiện:** 1) Search `q=` (rỗng). 2) Search thiếu param q.
- **Dữ liệu test:** q = "" / không truyền.
- **Kết quả mong đợi:** HTTP 422 (q required, min_length ≥ 1).
- **Coverage hiện tại:** MISSING

### TC-DIAG-014 — Autocomplete chưa đăng nhập → 401
- **Function:** DIAG-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) Gọi search ICD-10 không Authorization header.
- **Dữ liệu test:** request không token.
- **Kết quả mong đợi:** HTTP 401 (endpoint yêu cầu xác thực).
- **Coverage hiện tại:** MISSING

### TC-DIAG-015 — Lấy 1 entry ICD-10 theo code (happy path)
- **Function:** DIAG-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Catalog có J02.9.
- **Bước thực hiện:** 1) Get entry theo code "J02.9".
- **Dữ liệu test:** code = "J02.9".
- **Kết quả mong đợi:** HTTP 200; trả `code, name_vi, name_en, parent_code, chapter`.
- **Coverage hiện tại:** MISSING

### TC-DIAG-016 — Code không tồn tại → 404
- **Function:** DIAG-004
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập.
- **Bước thực hiện:** 1) Get entry code "ZZZ.999".
- **Dữ liệu test:** code không có trong catalog.
- **Kết quả mong đợi:** HTTP 404.
- **Coverage hiện tại:** MISSING

### TC-DIAG-017 — Catalog là GLOBAL, không bị RLS theo clinic
- **Function:** DIAG-004
- **Loại:** Edge / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 user thuộc clinic A và clinic B.
- **Bước thực hiện:** 1) User clinic A get J02.9. 2) User clinic B get J02.9.
- **Dữ liệu test:** cùng code, 2 clinic khác nhau.
- **Kết quả mong đợi:** Cả hai HTTP 200 cùng kết quả (bảng `icd10_catalog` không có clinic_id, không RLS) — xác nhận đúng thiết kế global master data.
- **Coverage hiện tại:** MISSING

### TC-DIAG-018 — Seed data ICD-10 đầy đủ & có name_vi
- **Function:** DIAG-004
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã chạy seed catalog.
- **Bước thực hiện:** 1) Đếm số dòng `icd10_catalog`. 2) Kiểm tra sample (A00, J02.9, I10) có name_vi không rỗng.
- **Dữ liệu test:** sample mã các chương.
- **Kết quả mong đợi:** Bảng có dữ liệu lớn (spec ~22000 entry); name_vi không null cho sample; code PK unique.
- **Coverage hiện tại:** MISSING

### TC-DIAG-019 — Get entry chưa đăng nhập → 401
- **Function:** DIAG-004
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) Get ICD-10 entry không Authorization.
- **Dữ liệu test:** request không token.
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING

### TC-DIAG-020 — Xem lịch sử chẩn đoán theo bệnh nhân (happy path)
- **Function:** DIAG-005
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN có ≥ 2 visit COMPLETED, mỗi visit có diagnosis.
- **Bước thực hiện:** 1) Lấy danh sách visit của patient (tab Visits) kèm diagnosis primary+secondary. 2) Kiểm tra view top diagnosis frequent.
- **Dữ liệu test:** patient_id có nhiều visit.
- **Kết quả mong đợi:** HTTP 200; danh sách visit theo thời gian; mỗi item có diagnosis; aggregated top diagnosis hiển thị bệnh tái phát.
- **Coverage hiện tại:** MISSING

### TC-DIAG-021 — Lịch sử cô lập theo clinic (RLS)
- **Function:** DIAG-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Patient P1 + visit thuộc clinic A; user clinic B.
- **Bước thực hiện:** 1) User clinic B truy vấn lịch sử visit của P1.
- **Dữ liệu test:** patient_id của clinic khác.
- **Kết quả mong đợi:** HTTP 404 / danh sách rỗng (RLS chặn).
- **Coverage hiện tại:** MISSING

### TC-DIAG-022 — BN chưa từng khám → lịch sử rỗng
- **Function:** DIAG-005
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Patient mới, chưa có visit.
- **Bước thực hiện:** 1) Lấy lịch sử chẩn đoán của patient.
- **Dữ liệu test:** patient không visit.
- **Kết quả mong đợi:** HTTP 200; danh sách rỗng; không lỗi.
- **Coverage hiện tại:** MISSING

### TC-DIAG-023 — Lưu lời dặn cuối visit (instructions)
- **Function:** DIAG-006
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit IN_PROGRESS, doctor có quyền.
- **Bước thực hiện:** 1) Cập nhật `instructions = "Uống nhiều nước, nghỉ ngơi, kiêng đồ lạnh"`. 2) Đọc lại.
- **Dữ liệu test:** chuỗi lời dặn tiếng Việt.
- **Kết quả mong đợi:** HTTP 200; `Visit.instructions` lưu đúng; sẵn sàng in trên đơn thuốc + summary.
- **Coverage hiện tại:** MISSING

### TC-DIAG-024 — Instructions chưa auth (401) / thiếu permission (403)
- **Function:** DIAG-006
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit tồn tại; (a) không token; (b) role thiếu quyền cập nhật visit.
- **Bước thực hiện:** 1) Cập nhật instructions không token → 401. 2) Bằng role thiếu quyền → 403.
- **Dữ liệu test:** token rỗng; token thiếu quyền.
- **Kết quả mong đợi:** (a) 401; (b) 403.
- **Coverage hiện tại:** MISSING

### TC-DIAG-025 — Đặt ngày tái khám + auto-tạo appointment (happy path)
- **Function:** DIAG-007
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit IN_PROGRESS, doctor có quyền.
- **Bước thực hiện:** 1) Cập nhật `followup_date = today+7` kèm xác nhận tạo appointment. 2) Kiểm tra appointment.
- **Dữ liệu test:** followup_date hợp lệ tương lai.
- **Kết quả mong đợi:** HTTP 200; `Visit.followup_date` lưu; tạo 1 appointment SCHEDULED đúng ngày, đúng patient, đúng clinic.
- **Coverage hiện tại:** MISSING

### TC-DIAG-026 — Đặt followup_date nhưng KHÔNG xác nhận tạo appointment
- **Function:** DIAG-007
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit IN_PROGRESS.
- **Bước thực hiện:** 1) Cập nhật followup_date mà không bật cờ tạo appointment.
- **Dữ liệu test:** flag tạo appointment = false.
- **Kết quả mong đợi:** HTTP 200; followup_date lưu; KHÔNG tạo appointment.
- **Coverage hiện tại:** MISSING

### TC-DIAG-027 — followup_date trong quá khứ → validate
- **Function:** DIAG-007
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit IN_PROGRESS.
- **Bước thực hiện:** 1) Cập nhật `followup_date = today-1` kèm xác nhận tạo appointment.
- **Dữ liệu test:** ngày quá khứ.
- **Kết quả mong đợi:** Nếu có validation → HTTP 422 và không tạo appointment; nếu chưa → ghi nhận gap. Tài liệu hóa hành vi.
- **Coverage hiện tại:** MISSING

### TC-DIAG-028 — Auto-appointment cô lập đúng clinic (RLS)
- **Function:** DIAG-007
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit thuộc clinic A.
- **Bước thực hiện:** 1) Tạo followup từ visit clinic A. 2) Xác nhận appointment mới có clinic_id = A và user clinic B không thấy.
- **Dữ liệu test:** visit clinic A.
- **Kết quả mong đợi:** appointment.clinic_id = A; RLS chặn user clinic B.
- **Coverage hiện tại:** MISSING

### TC-DIAG-029 — Lịch tái khám chưa auth (401) / thiếu quyền (403)
- **Function:** DIAG-007
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit tồn tại; (a) không token; (b) role thiếu quyền.
- **Bước thực hiện:** 1) Cập nhật followup_date không token → 401. 2) Bằng role thiếu quyền → 403.
- **Dữ liệu test:** token rỗng; token thiếu quyền.
- **Kết quả mong đợi:** (a) 401; (b) 403; không tạo appointment.
- **Coverage hiện tại:** MISSING

### TC-DIAG-030 — Diagnosis templates (placeholder — chưa ship, v2)
- **Function:** DIAG-008
- **Loại:** Happy path (đặc tả tương lai)
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest) — khi implement
- **Tiền điều kiện:** Tính năng v2 chưa có; hiện chỉ verify KHÔNG tồn tại endpoint/UI template.
- **Bước thực hiện:** 1) Khi ship: doctor lưu template (name + diagnosis codes + clinical_notes + instructions). 2) Áp dụng 1 click vào visit. 3) Verify chia sẻ trong clinic (RLS theo clinic).
- **Dữ liệu test:** template "Viêm họng cấp standard".
- **Kết quả mong đợi:** (hiện tại) không có route templates → 404. (khi ship) template áp dụng đúng các field, cô lập theo clinic, cần quyền cập nhật visit.
- **Coverage hiện tại:** MISSING (IDEA v2 — chưa implement)

### TC-DIAG-031 — Voice-to-text input (placeholder — chưa ship, v3)
- **Function:** DIAG-009
- **Loại:** Happy path (đặc tả tương lai)
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest) — khi implement
- **Tiền điều kiện:** Tính năng v3 chưa có.
- **Bước thực hiện:** 1) Khi ship: doctor đọc → transcribe vào clinical_notes (Whisper/Web Speech). 2) Verify privacy: audio KHÔNG lưu, chỉ transcribe. 3) Xử lý tiếng Việt + thuật ngữ y khoa.
- **Dữ liệu test:** đoạn audio tiếng Việt mẫu.
- **Kết quả mong đợi:** (hiện tại) không có tính năng. (khi ship) text transcribe điền vào clinical_notes; không lưu file audio trên server.
- **Coverage hiện tại:** MISSING (IDEA v3 — chưa implement)

---

## 3. Ghi chú & rủi ro coverage
- **Gap nghiêm trọng nhất:** Cả group DIAG (kể cả DIAG-001..007 đang ghi DONE trong nguồn) **chưa hề được implement trong codebase hiện tại** — backend mới có auth/users/clinics/roles/RLS. Status "DONE" trong function_list nhiều khả năng phản ánh TASK design/spec, không phải code ship. Cần làm rõ với PM/manager trước khi coi DIAG là hoàn thành.
- **Không có automated test** nào cho DIAG (tests/ chỉ có auth/health/rls/clinics/users/smoke).
- **Ưu tiên P0 khi implement:** rule "primary required on COMPLETE" (TC-DIAG-003), "immutable sau COMPLETED" (TC-DIAG-004), auto-tạo follow-up appointment (TC-DIAG-025), và RLS cô lập diagnosis/visit (TC-DIAG-006, 021, 028) — mô hình RLS đã có sẵn `tests/test_rls.py` để tái sử dụng.
- **Validation cần làm rõ:** max-length clinical_notes (~5000, TC-DIAG-008) và followup_date quá khứ (TC-DIAG-027).
- **Lưu ý đường dẫn brief:** `clinic-cms-merge/app` không tồn tại; mã thực tế ở `claude-workspace/app`.
