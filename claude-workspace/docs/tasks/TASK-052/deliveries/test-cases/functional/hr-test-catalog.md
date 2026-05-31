# Test Case Catalog — HR · Nhân sự & Chấm công

**Nguồn:** function_list_data.py (group HR, dòng 1155–1220) + clinic_management_function_list.md (mục 15) + system_design/SaaS.
**Phạm vi:** 22 functions (HR-001 … HR-022).  **Tổng test case:** 52.  **Ngày:** 2026-05-30.

> **Ghi chú truy cập nguồn / phương pháp gán Coverage:**
> - Repo mã nguồn `E:/MyProject/clinic-cms-merge` (app + tests) **không truy cập được** từ môi trường subagent này (Glob/Read báo "Directory does not exist"). Vì vậy **Coverage được suy ra từ cột `status` của function_list_data.py**:
>   - `✅ DONE` → **COVERED** (kỳ vọng có test, *cần xác minh test file* khi truy cập được repo).
>   - `⬜ TODO` → **MISSING** (chưa hiện thực hoặc chưa có test).
>   - `💡 IDEA` → **MISSING** (mới ở mức ý tưởng, phase v2/v3).
> - HR là module nghiệp vụ multi-tenant: mọi bảng (`user`, `shift`, `recurring_schedule`, `attendance`, `leave_request`) đều có `clinic_id` + RLS (session var `app.current_clinic_id`). Permission liên quan trong system_design: `attendance.manage` (Quản lý chấm công), `leave.approve` (Duyệt nghỉ phép).
> - Khi truy cập được repo: map endpoint/path thực tế + test file thực tế và cập nhật cột Coverage thành `COVERED (path::test)`.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| HR-001 | User CRUD (clinic) | ⬜ TODO | TC-HR-001, TC-HR-002, TC-HR-003 | MISSING |
| HR-002 | Temp password gen (12-char, hiện 1 lần) | ⬜ TODO | TC-HR-004, TC-HR-005 | MISSING |
| HR-003 | Magic link invite (Phase 2) | ⬜ TODO | TC-HR-006 | MISSING |
| HR-004 | Reset password (admin) | ⬜ TODO | TC-HR-007, TC-HR-008 | MISSING |
| HR-005 | Disable/enable user (toggle is_active) | ⬜ TODO | TC-HR-009, TC-HR-010 | MISSING |
| HR-006 | License number (chứng chỉ hành nghề) | ⬜ TODO | TC-HR-011, TC-HR-012 | MISSING |
| HR-007 | Specialty per doctor (chuyên khoa phụ) | ⬜ TODO | TC-HR-013 | MISSING |
| HR-008 | Shift CRUD | ✅ DONE | TC-HR-014, TC-HR-015, TC-HR-016 | COVERED |
| HR-009 | Recurring schedule (template tuần) | ✅ DONE | TC-HR-017, TC-HR-018 | COVERED |
| HR-010 | Apply recurring → shifts (cron generate) | ✅ DONE | TC-HR-019, TC-HR-020 | COVERED |
| HR-011 | Calendar view (week grid) | ⬜ TODO | TC-HR-021 | MISSING |
| HR-012 | Drag to reschedule (Phase 2) | 💡 IDEA | TC-HR-022 | MISSING |
| HR-013 | Attendance check-in | ✅ DONE | TC-HR-023, TC-HR-024, TC-HR-025 | COVERED |
| HR-014 | Attendance check-out | ✅ DONE | TC-HR-026, TC-HR-027 | COVERED |
| HR-015 | OT calculation (tính giờ OT) | ✅ DONE | TC-HR-028, TC-HR-029 | COVERED |
| HR-016 | Late/early tracking | ✅ DONE | TC-HR-030, TC-HR-031 | COVERED |
| HR-017 | Leave request (đơn nghỉ phép) | ✅ DONE | TC-HR-032, TC-HR-033, TC-HR-034 | COVERED |
| HR-018 | Leave approval (manager duyệt) | ✅ DONE | TC-HR-035, TC-HR-036, TC-HR-037 | COVERED |
| HR-019 | Leave balance (số ngày phép còn) | ✅ DONE | TC-HR-038, TC-HR-039 | COVERED |
| HR-020 | Attendance report (bảng chấm công tháng) | ⬜ TODO | TC-HR-040, TC-HR-041 | MISSING |
| HR-021 | Payroll integration (export lương, Phase 3) | 💡 IDEA | TC-HR-042 | MISSING |
| HR-022 | Multi-role user (1 NV kiêm 2 role) | ✅ DONE | TC-HR-043, TC-HR-044, TC-HR-045 | COVERED |
| — (xuyên suốt) | Cô lập đa phòng khám (RLS) toàn module HR | — | TC-HR-046, TC-HR-047 | PARTIAL |
| — (xuyên suốt) | Ma trận xác thực & phân quyền HR | — | TC-HR-048, TC-HR-049 | PARTIAL |
| — (xuyên suốt) | Audit log các hành động nhạy cảm HR | — | TC-HR-050 | PARTIAL |
| — (xuyên suốt) | Offline-first (Tauri) chấm công | — | TC-HR-051, TC-HR-052 | PARTIAL |

**Tổng kết coverage:**
- **COVERED:** 25 TC (10 function DONE: HR-008, 009, 010, 013, 014, 015, 016, 017, 018, 019, 022).
- **MISSING:** 20 TC (12 function TODO/IDEA: HR-001..007, 011, 012, 020, 021).
- **PARTIAL:** 7 TC (xuyên suốt: RLS, phân quyền/auth, audit, offline — dựa cơ chế core dùng chung, cần xác minh phủ riêng cho bảng/endpoint HR).

---

## 2. Chi tiết Test Cases

### TC-HR-001 — Tạo/sửa/xóa nhân viên (CRUD happy path)
- **Function:** HR-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập Clinic Admin clinic A.
- **Bước thực hiện:** 1) POST tạo nhân viên (tên, username, email, SĐT, role(s), license_number, specialty). 2) PATCH sửa SĐT/role. 3) DELETE (soft-delete).
- **Dữ liệu test:** Bác sĩ có license_number + specialty=general.
- **Kết quả mong đợi:** 201 khi tạo, `clinic_id`=clinic A; 200 khi sửa; soft-delete giữ history visit/Rx (record vẫn còn nhưng is_deleted=true, không xuất hiện ở list active).
- **Coverage hiện tại:** MISSING (status TODO — TASK-006, chưa hiện thực; cần viết test sau khi build).

### TC-HR-002 — Validate dữ liệu nhân viên & trùng email/username (negative)
- **Function:** HR-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Unit / Integration
- **Tiền điều kiện:** Đã có 1 nhân viên với email X.
- **Bước thực hiện:** 1) Tạo NV thiếu tên/email. 2) Email sai định dạng. 3) Tạo NV trùng email X (global unique). 4) Role doctor thiếu license_number.
- **Dữ liệu test:** Payload thiếu trường; email `abc@`; email trùng.
- **Kết quả mong đợi:** 422 lỗi validate; 409 trùng email; doctor thiếu license → 422 (theo regulation VN).
- **Coverage hiện tại:** MISSING (status TODO).

### TC-HR-003 — Chỉ admin được CRUD nhân viên (security)
- **Function:** HR-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token role thường (không phải admin) + request không token.
- **Bước thực hiện:** 1) POST/DELETE nhân viên không token → 401. 2) Bằng token non-admin → 403.
- **Dữ liệu test:** Token rỗng; token staff thường.
- **Kết quả mong đợi:** 401 khi không token; 403 khi thiếu quyền; không tạo/sửa/xóa bản ghi.
- **Coverage hiện tại:** MISSING (status TODO).

### TC-HR-004 — Sinh temp password 12-char khi tạo nhân viên (happy path)
- **Function:** HR-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin tạo nhân viên mới.
- **Bước thực hiện:** 1) POST tạo nhân viên. 2) Đọc plain password trong response 1 lần.
- **Dữ liệu test:** Nhân viên mới.
- **Kết quả mong đợi:** Password 12 ký tự (mixed case + số + symbol), được hash bcrypt trong DB (không lưu plain), trả plain 1 lần qua API, `must_change_password=true`.
- **Coverage hiện tại:** MISSING (status TODO — TASK-006).

### TC-HR-005 — Temp password không lặp lại lần 2 & độ phức tạp (edge/security)
- **Function:** HR-002
- **Loại:** Edge / Security
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Đã tạo nhân viên (đã đọc password 1 lần).
- **Bước thực hiện:** 1) GET lại nhân viên — kiểm tra không trả lại plain password. 2) Sinh nhiều password — kiểm tra entropy/độ phức tạp.
- **Dữ liệu test:** Nhiều lần generate.
- **Kết quả mong đợi:** Plain password chỉ hiện 1 lần lúc tạo; các lần đọc sau không lộ; mọi password đạt complexity rule.
- **Coverage hiện tại:** MISSING (status TODO).

### TC-HR-006 — Magic link invite đặt password (happy path, Phase 2)
- **Function:** HR-003
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có email infra; admin gửi invite.
- **Bước thực hiện:** 1) Admin gửi magic link cho email NV. 2) NV click link trong TTL 72h → đặt password tự chọn.
- **Dữ liệu test:** Link hợp lệ; link hết hạn (>72h).
- **Kết quả mong đợi:** Link hợp lệ → đặt password thành công; link hết hạn → từ chối; token dùng 1 lần.
- **Coverage hiện tại:** MISSING (status TODO — Phase 2, TASK-027, cần email infra).

### TC-HR-007 — Admin reset password nhân viên (happy path)
- **Function:** HR-004
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập Clinic Admin; nhân viên tồn tại.
- **Bước thực hiện:** 1) POST reset password cho nhân viên. 2) Đọc temp password mới (hiện 1 lần).
- **Dữ liệu test:** Nhân viên hiện hữu.
- **Kết quả mong đợi:** Sinh temp password mới, `must_change_password=true`; password cũ vô hiệu; (kỳ vọng) audit event.
- **Coverage hiện tại:** MISSING (status TODO — TASK-006).

### TC-HR-008 — Reset password không đủ quyền (security)
- **Function:** HR-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token non-admin.
- **Bước thực hiện:** 1) POST reset bằng non-admin → 403. 2) Reset cho nhân viên clinic khác (RLS) → 404/403.
- **Dữ liệu test:** Nhân viên clinic B.
- **Kết quả mong đợi:** 403 thiếu quyền; không reset được nhân viên clinic khác (RLS).
- **Coverage hiện tại:** MISSING (status TODO).

### TC-HR-009 — Disable/enable user toggle is_active (happy path)
- **Function:** HR-005
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập Clinic Admin; nhân viên đang active.
- **Bước thực hiện:** 1) Toggle is_active=false. 2) Nhân viên thử login. 3) Toggle lại active.
- **Dữ liệu test:** Nhân viên đang làm việc.
- **Kết quả mong đợi:** Inactive → login bị từ chối; enable lại → login được; thao tác được audit.
- **Coverage hiện tại:** MISSING (status TODO — TASK-006).

### TC-HR-010 — User inactive bị chặn truy cập (security)
- **Function:** HR-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Nhân viên đang có token hợp lệ rồi bị disable.
- **Bước thực hiện:** 1) Disable nhân viên. 2) Nhân viên dùng access token còn hạn gọi API.
- **Dữ liệu test:** Token cũ của user vừa bị disable.
- **Kết quả mong đợi:** Truy cập bị chặn (401/403) sau khi disable; không login mới được.
- **Coverage hiện tại:** MISSING (status TODO).

### TC-HR-011 — License number bắt buộc cho doctor/pharmacist (happy path + negative)
- **Function:** HR-006
- **Loại:** Happy path / Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin tạo/sửa nhân viên.
- **Bước thực hiện:** 1) Tạo doctor có license_number hợp lệ. 2) Tạo doctor không có license_number. 3) Tạo lễ tân (không bắt buộc license).
- **Dữ liệu test:** License đúng format Bộ Y tế; rỗng.
- **Kết quả mong đợi:** Doctor/pharmacist không có license → 422; lễ tân không cần; license in được trên đơn thuốc.
- **Coverage hiện tại:** MISSING (status TODO — TASK-006).

### TC-HR-012 — Validate format license number (negative)
- **Function:** HR-006
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Có rule validate format theo Bộ Y tế.
- **Bước thực hiện:** 1) Nhập license sai format.
- **Dữ liệu test:** Chuỗi không đúng pattern.
- **Kết quả mong đợi:** 422 với thông báo format không hợp lệ.
- **Coverage hiện tại:** MISSING (status TODO).

### TC-HR-013 — Specialty subfield cho bác sĩ (happy path)
- **Function:** HR-007
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Bác sĩ specialty=general.
- **Bước thực hiện:** 1) Set specialty_subfield='Nội tim mạch'. 2) UI service-doctor mapping filter theo subfield.
- **Dữ liệu test:** Subfield cụ thể.
- **Kết quả mong đợi:** Lưu đúng subfield; filter mapping service-doctor theo subfield hoạt động.
- **Coverage hiện tại:** MISSING (status TODO — TASK-006).

### TC-HR-014 — Tạo/sửa/xóa ca làm việc (Shift CRUD happy path)
- **Function:** HR-008
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập Clinic Admin/Manager; có nhân viên.
- **Bước thực hiện:** 1) POST shift (user_id, start_time, end_time, break_minutes, role_in_shift, notes). 2) PATCH đổi giờ. 3) DELETE.
- **Dữ liệu test:** Ca sáng 08:00–12:00, break 0p, role_in_shift=doctor.
- **Kết quả mong đợi:** 201/200/204 tương ứng; ca lưu đúng, gắn `clinic_id`=clinic hiện tại.
- **Coverage hiện tại:** COVERED (cần xác minh test file — status DONE, TASK-014).

### TC-HR-015 — Validate ca làm việc (negative)
- **Function:** HR-008
- **Loại:** Negative / Edge
- **Ưu tiên:** P1
- **Layer:** Unit / Integration
- **Tiền điều kiện:** Có nhân viên.
- **Bước thực hiện:** 1) end_time < start_time. 2) break_minutes > tổng thời lượng ca. 3) (Edge) tạo ca chồng giờ cho cùng nhân viên.
- **Dữ liệu test:** Khoảng giờ ngược; break quá lớn; ca giao thoa.
- **Kết quả mong đợi:** 422 cho dữ liệu sai; cảnh báo/chặn ca chồng giờ tùy rule.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-016 — Cô lập ca làm việc theo clinic (RLS)
- **Function:** HR-008
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B đều có ca.
- **Bước thực hiện:** 1) Admin clinic A list shift. 2) Thử GET/PATCH shift của clinic B.
- **Dữ liệu test:** Shift clinic A vs B.
- **Kết quả mong đợi:** Chỉ thấy shift clinic A; truy cập shift clinic B → 404/403 (RLS).
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-017 — Tạo template lịch ca tuần (Recurring schedule happy path)
- **Function:** HR-009
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập Clinic Admin; có nhân viên.
- **Bước thực hiện:** 1) POST recurring_schedule (user_id, day_of_week, start_time, end_time) cho T2–T6.
- **Dữ liệu test:** day_of_week 1–5, 08:00–17:00.
- **Kết quả mong đợi:** 201, template lưu đúng theo từng ngày trong tuần, gắn `clinic_id`.
- **Coverage hiện tại:** COVERED (cần xác minh test file — TASK-014).

### TC-HR-018 — Validate recurring schedule trùng/sai (negative)
- **Function:** HR-009
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Đã có template cho thứ 2.
- **Bước thực hiện:** 1) Thêm template trùng day_of_week + giờ chồng. 2) end_time < start_time.
- **Dữ liệu test:** Template trùng/ngược giờ.
- **Kết quả mong đợi:** 422/409; không tạo template trùng âm thầm.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-019 — Cron generate shift từ template (happy path)
- **Function:** HR-010
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có recurring_schedule cho ngày mai.
- **Bước thực hiện:** 1) Chạy job daily generate shifts cho ngày mai. 2) GET shift ngày mai.
- **Dữ liệu test:** Template T3 → ngày mai là T3.
- **Kết quả mong đợi:** Shift được tạo đúng từ template cho ngày mai; idempotent (chạy 2 lần không tạo trùng).
- **Coverage hiện tại:** COVERED (cần xác minh test file — TASK-014).

### TC-HR-020 — Manual override per-day sau khi generate (edge)
- **Function:** HR-010
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Shift đã được generate từ template.
- **Bước thực hiện:** 1) Sửa thủ công 1 shift của ngày. 2) Chạy lại job generate.
- **Dữ liệu test:** Shift đã override.
- **Kết quả mong đợi:** Override per-day được giữ; job không ghi đè shift đã chỉnh tay.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-021 — Calendar week view hiển thị ca (happy path)
- **Function:** HR-011
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI
- **Tiền điều kiện:** Có shift trong tuần.
- **Bước thực hiện:** 1) Mở /hr/shifts FullCalendar week view. 2) Kiểm tra color-code theo role. 3) (admin) drag-drop reschedule.
- **Dữ liệu test:** Ca nhiều role trong tuần.
- **Kết quả mong đợi:** Hiển thị grid tuần đúng, color theo role; chỉ admin drag-drop được.
- **Coverage hiện tại:** MISSING (status TODO — TASK-022).

### TC-HR-022 — Drag để reschedule ca (happy path, Phase 2)
- **Function:** HR-012
- **Loại:** Happy path
- **Ưu tiên:** P3
- **Layer:** Manual/UI
- **Tiền điều kiện:** Manager đăng nhập; có shift.
- **Bước thực hiện:** 1) Kéo shift sang slot khác. 2) Confirm dialog.
- **Dữ liệu test:** Shift cần đổi giờ.
- **Kết quả mong đợi:** Reschedule thành công sau confirm; audit reschedule event.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa hiện thực).

### TC-HR-023 — Check-in chấm công (happy path)
- **Function:** HR-013
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập nhân viên; có scheduled shift trong ngày.
- **Bước thực hiện:** 1) Click 'Check In' (hoặc scan QR).
- **Dữ liệu test:** Check-in 08:00, shift.start=08:00.
- **Kết quả mong đợi:** Ghi timestamp check-in, so với shift.start → mark on-time; gắn nhân viên + `clinic_id`.
- **Coverage hiện tại:** COVERED (cần xác minh test file — TASK-014).

### TC-HR-024 — Check-in trùng / không có ca (negative)
- **Function:** HR-013
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã check-in trong ngày.
- **Bước thực hiện:** 1) Check-in lần 2 cùng ngày. 2) Check-in khi không có shift.
- **Dữ liệu test:** Trạng thái chấm công không hợp lệ.
- **Kết quả mong đợi:** 409/422; không tạo bản ghi check-in trùng.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-025 — Permission attendance.manage / cô lập clinic (security + RLS)
- **Function:** HR-013
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token các role; clinic A và B có dữ liệu chấm công.
- **Bước thực hiện:** 1) Check-in không token → 401. 2) Quản lý chấm công người khác mà không có `attendance.manage` → 403. 3) Truy cập bản ghi chấm công clinic B.
- **Dữ liệu test:** Token thiếu quyền; bản ghi clinic B.
- **Kết quả mong đợi:** 401/403 đúng; không truy cập được dữ liệu clinic B (RLS).
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-026 — Check-out & tính tổng giờ làm (happy path)
- **Function:** HR-014
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã check-in.
- **Bước thực hiện:** 1) Cuối ca click 'Check Out'.
- **Dữ liệu test:** Check-in 08:00, check-out 17:00, break_minutes=60.
- **Kết quả mong đợi:** Tổng giờ làm = check_out − check_in − break_minutes = 8h.
- **Coverage hiện tại:** COVERED (cần xác minh test file — TASK-014).

### TC-HR-027 — Check-out khi chưa check-in (negative)
- **Function:** HR-014
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Chưa check-in trong ngày.
- **Bước thực hiện:** 1) Click 'Check Out'.
- **Dữ liệu test:** Không có bản ghi check-in.
- **Kết quả mong đợi:** 409/422; không tạo bản ghi check-out mồ côi.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-028 — Tính OT khi vượt giờ scheduled (happy path)
- **Function:** HR-015
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có OT rate config (1.5x ngày thường, 2x cuối tuần).
- **Bước thực hiện:** 1) Check-in/out với actual_hours > scheduled_hours ngày thường.
- **Dữ liệu test:** Scheduled 8h, actual 10h → OT 2h × 1.5.
- **Kết quả mong đợi:** OT = (actual − scheduled) × rate đúng theo config; ngày thường 1.5x.
- **Coverage hiện tại:** COVERED (cần xác minh test file — TASK-014).

### TC-HR-029 — OT cuối tuần & không OT khi đủ giờ (edge)
- **Function:** HR-015
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** OT rate config.
- **Bước thực hiện:** 1) OT vào cuối tuần (rate 2x). 2) actual_hours = scheduled_hours (không OT). 3) actual < scheduled.
- **Dữ liệu test:** Ngày T7/CN; đúng giờ; thiếu giờ.
- **Kết quả mong đợi:** Cuối tuần 2x; đủ/thiếu giờ → OT=0; không âm.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-030 — Đánh dấu đi muộn / về sớm (happy path)
- **Function:** HR-016
- **Loại:** Happy path / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Shift 08:00–17:00, threshold 10 phút.
- **Bước thực hiện:** 1) Check-in 08:15 (muộn). 2) Check-out 16:45 (sớm). 3) Check-in 08:08 (trong threshold).
- **Dữ liệu test:** Lệch giờ quanh ngưỡng 10 phút.
- **Kết quả mong đợi:** 08:15 → mark late; 16:45 → mark early; 08:08 → on-time (trong threshold).
- **Coverage hiện tại:** COVERED (cần xác minh test file — TASK-014).

### TC-HR-031 — Late/early biên threshold chính xác (edge)
- **Function:** HR-016
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** threshold = 10 phút.
- **Bước thực hiện:** 1) Check-in đúng 08:10 (biên). 2) Check-in 08:11.
- **Dữ liệu test:** Đúng biên threshold.
- **Kết quả mong đợi:** Quy tắc biên nhất quán (vd <=10p on-time, >10p late); không nhập nhằng.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-032 — Nhân viên gửi đơn nghỉ phép (happy path)
- **Function:** HR-017
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập nhân viên.
- **Bước thực hiện:** 1) POST /hr/leave/new (type, date_from, date_to, reason, attachment).
- **Dữ liệu test:** type=annual, 2 ngày, lý do hợp lệ, file đính kèm.
- **Kết quả mong đợi:** 201, status=PENDING, gắn đúng nhân viên + `clinic_id`; số ngày tính đúng.
- **Coverage hiện tại:** COVERED (cần xác minh test file — TASK-014).

### TC-HR-033 — Validate đơn nghỉ phép (negative)
- **Function:** HR-017
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Unit / Integration
- **Tiền điều kiện:** Đăng nhập nhân viên.
- **Bước thực hiện:** 1) date_to < date_from. 2) Trùng khoảng với đơn đã có. 3) Thiếu type.
- **Dữ liệu test:** Khoảng ngày ngược; khoảng trùng; payload thiếu.
- **Kết quả mong đợi:** 422/409; không tạo đơn.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-034 — Nhân viên chỉ thấy đơn của mình (security)
- **Function:** HR-017
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** 2 nhân viên, mỗi người có đơn nghỉ riêng.
- **Bước thực hiện:** 1) NV X GET đơn của mình. 2) NV X thử GET đơn của NV Y theo ID.
- **Dữ liệu test:** ID đơn người khác.
- **Kết quả mong đợi:** X chỉ thấy đơn của X; truy cập đơn Y → 403/404.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-035 — Manager duyệt đơn nghỉ phép (happy path)
- **Function:** HR-018
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Manager (có `leave.approve`); đơn PENDING tồn tại.
- **Bước thực hiện:** 1) Approve đơn + ghi chú.
- **Dữ liệu test:** Đơn PENDING.
- **Kết quả mong đợi:** 200, status=APPROVED, lưu người duyệt + thời điểm; notify user; audit.
- **Coverage hiện tại:** COVERED (cần xác minh test file — TASK-014).

### TC-HR-036 — Reject & duyệt lại đơn đã xử lý (negative)
- **Function:** HR-018
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn PENDING và đơn APPROVED.
- **Bước thực hiện:** 1) Reject đơn PENDING + ghi chú. 2) Approve lại đơn đã APPROVED.
- **Dữ liệu test:** Đơn ở trạng thái cuối.
- **Kết quả mong đợi:** Reject → REJECTED + ghi chú; xử lý đơn đã final → 409/422 (chống double-process).
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-037 — Chỉ Manager có leave.approve được duyệt (security)
- **Function:** HR-018
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token nhân viên thường (không có `leave.approve`).
- **Bước thực hiện:** 1) Approve bằng token thường → 403. 2) Không token → 401. 3) Duyệt đơn của clinic khác (RLS).
- **Dữ liệu test:** Đơn PENDING; đơn clinic B.
- **Kết quả mong đợi:** 401/403; không duyệt được đơn clinic khác (RLS); trạng thái đơn không đổi.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-038 — Trừ quota leave balance khi approve (happy path)
- **Function:** HR-019
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** NV có quota annual 12 ngày.
- **Bước thực hiện:** 1) Approve đơn annual 2 ngày. 2) GET /hr/leave/me.
- **Dữ liệu test:** Quota 12, đơn 2 ngày.
- **Kết quả mong đợi:** Balance còn 10 ngày; chỉ trừ khi approve (không trừ lúc PENDING).
- **Coverage hiện tại:** COVERED (cần xác minh test file — TASK-014).

### TC-HR-039 — Vượt quota & reset cuối năm (edge)
- **Function:** HR-019
- **Loại:** Edge / Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** NV còn 1 ngày annual.
- **Bước thực hiện:** 1) Đơn annual 3 ngày → approve. 2) Mô phỏng reset cuối năm.
- **Dữ liệu test:** Quota gần hết; mốc cuối năm.
- **Kết quả mong đợi:** Approve vượt quota → cảnh báo/chặn theo rule; reset quota về default đầu năm mới.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-040 — Báo cáo chấm công tháng (happy path)
- **Function:** HR-020
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có dữ liệu attendance + leave trong tháng.
- **Bước thực hiện:** 1) GET /reports/attendance theo tháng. 2) Export Excel.
- **Dữ liệu test:** 1 NV: 20 ngày công, 2 late, 1 OT, 1 absent, 2 leave.
- **Kết quả mong đợi:** Bảng NV × ngày hiện check-in/out + late/early/OT/absent; export Excel hợp lệ phục vụ payroll.
- **Coverage hiện tại:** MISSING (status TODO — TASK-015).

### TC-HR-041 — Cô lập báo cáo chấm công theo clinic (RLS)
- **Function:** HR-020
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B đều có dữ liệu chấm công.
- **Bước thực hiện:** 1) Admin clinic A GET báo cáo tháng.
- **Dữ liệu test:** Nhân viên 2 clinic.
- **Kết quả mong đợi:** Chỉ tổng hợp clinic A; không lẫn clinic B (RLS).
- **Coverage hiện tại:** MISSING (status TODO).

### TC-HR-042 — Export attendance/leave sang phần mềm lương (happy path, Phase 3)
- **Function:** HR-021
- **Loại:** Happy path
- **Ưu tiên:** P3
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có dữ liệu chấm công + leave; cấu hình tích hợp MISA/Fast.
- **Bước thực hiện:** 1) Gọi API export attendance+leave theo format đối tác.
- **Dữ liệu test:** Tháng có đủ dữ liệu.
- **Kết quả mong đợi:** File/payload export đúng schema phần mềm lương; map field chính xác.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 3, chưa hiện thực).

### TC-HR-043 — Nhân viên kiêm nhiều role (Multi-role happy path)
- **Function:** HR-022
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập Clinic Admin; có role doctor + receptionist.
- **Bước thực hiện:** 1) Tạo/sửa user gán 2 role qua user_role M2M (checkbox UI). 2) User login.
- **Dữ liệu test:** User có role doctor + receptionist.
- **Kết quả mong đợi:** User có quyền hợp nhất (union) của cả 2 role; cả 2 hiển thị đúng.
- **Coverage hiện tại:** COVERED (cần xác minh test file — status DONE, TASK-004).

### TC-HR-044 — Gỡ 1 role, role còn lại vẫn hiệu lực (edge)
- **Function:** HR-022
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User có 2 role.
- **Bước thực hiện:** 1) Gỡ role doctor, giữ receptionist. 2) User gọi API cần quyền doctor.
- **Dữ liệu test:** Quyền chỉ thuộc role doctor.
- **Kết quả mong đợi:** Mất quyền của role doctor (403), giữ quyền receptionist.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-045 — Chỉ admin gán/gỡ role — chống leo thang đặc quyền (security)
- **Function:** HR-022
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token non-admin.
- **Bước thực hiện:** 1) Tự gán thêm role cho mình bằng token non-admin → 403. 2) Không token → 401.
- **Dữ liệu test:** Payload gán role admin cho chính mình.
- **Kết quả mong đợi:** 403/401; không thay đổi role — chống privilege escalation.
- **Coverage hiện tại:** COVERED (cần xác minh test file).

### TC-HR-046 — Cô lập đa phòng khám toàn module HR (RLS, xuyên suốt)
- **Function:** HR (xuyên suốt — HR-001..022)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 tenant clinic A & B, mỗi clinic có user/shift/recurring/attendance/leave riêng.
- **Bước thực hiện:** 1) Với context clinic A, gọi lần lượt các endpoint list/detail HR. 2) Thử truy cập bằng ID thuộc clinic B. 3) Kiểm tra session var `app.current_clinic_id` không bị rò qua connection pool.
- **Dữ liệu test:** Cặp bản ghi tương ứng ở 2 clinic.
- **Kết quả mong đợi:** Mọi truy vấn chỉ trả dữ liệu clinic A; ID clinic B → 404/403; PostgreSQL RLS chặn ở tầng DB kể cả khi bỏ filter ở tầng app.
- **Coverage hiện tại:** PARTIAL — RLS dùng cơ chế core chung; cần xác minh test RLS riêng cho từng bảng HR (user, shift, recurring_schedule, attendance, leave_request).

### TC-HR-047 — Reset/rollback session RLS giữa các request (RLS, xuyên suốt)
- **Function:** HR (xuyên suốt)
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Connection pool dùng lại; request clinic A rồi clinic B liên tiếp.
- **Bước thực hiện:** 1) Request clinic A set `app.current_clinic_id`. 2) Request kế tiếp clinic B trên cùng connection.
- **Dữ liệu test:** Hai request khác clinic dùng pool.
- **Kết quả mong đợi:** Context được reset đúng mỗi request; không rò dữ liệu clinic A sang request clinic B.
- **Coverage hiện tại:** PARTIAL — cần xác minh test middleware tenancy/RLS context.

### TC-HR-048 — Không token → 401 toàn bộ endpoint HR (auth, xuyên suốt)
- **Function:** HR (xuyên suốt)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token / token hết hạn.
- **Bước thực hiện:** 1) Gọi từng nhóm endpoint HR không token. 2) Gọi với token hết hạn.
- **Dữ liệu test:** Token rỗng; token expired.
- **Kết quả mong đợi:** 401 toàn bộ; không lộ dữ liệu.
- **Coverage hiện tại:** PARTIAL — dùng dependency auth core; cần xác minh phủ cho từng endpoint HR.

### TC-HR-049 — Ma trận phân quyền HR theo role (auth, xuyên suốt)
- **Function:** HR (xuyên suốt)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token các role: nhân viên thường, Manager, Clinic Admin.
- **Bước thực hiện:** 1) Đối chiếu cột `role` nguồn: CRUD user/password/role = Clinic Admin; shift CRUD = Admin/Manager; check-in/out & leave request = All; leave approval = Manager (`leave.approve`); attendance manage = `attendance.manage`. 2) Gọi endpoint bằng role không đủ quyền.
- **Dữ liệu test:** Bộ token theo role.
- **Kết quả mong đợi:** Role đủ quyền → thành công; thiếu quyền → 403; khớp ma trận role/permission nguồn.
- **Coverage hiện tại:** PARTIAL — cần xác minh test phân quyền chi tiết từng endpoint HR.

### TC-HR-050 — Audit log hành động nhạy cảm HR (xuyên suốt)
- **Function:** HR (xuyên suốt — HR-001/004/005/018/022)
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin/Manager thực hiện thao tác nhạy cảm.
- **Bước thực hiện:** 1) Disable user, reset password, gán role, duyệt nghỉ. 2) Kiểm tra audit log.
- **Dữ liệu test:** Các action: disable, reset_password, role_change, leave_approve.
- **Kết quả mong đợi:** Mỗi action ghi audit (actor, target, time, clinic_id); không thiếu sót.
- **Coverage hiện tại:** PARTIAL — audit dùng cơ chế core; cần xác minh phủ cho action HR.

### TC-HR-051 — Chấm công offline-first (Tauri) đồng bộ khi online (xuyên suốt)
- **Function:** HR (xuyên suốt — HR-013/014)
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (Tauri/Manual)
- **Tiền điều kiện:** App Tauri offline; nhân viên check-in/out khi mất mạng.
- **Bước thực hiện:** 1) Check-in/out offline. 2) Khôi phục mạng → đồng bộ lên server.
- **Dữ liệu test:** Bản ghi chấm công tạo offline.
- **Kết quả mong đợi:** Lưu local khi offline, sync đúng timestamp khi online, không mất bản ghi.
- **Coverage hiện tại:** PARTIAL — phụ thuộc cơ chế offline-sync core; cần xác minh test sync cho attendance.

### TC-HR-052 — Resolve conflict chấm công khi sync (xuyên suốt)
- **Function:** HR (xuyên suốt — HR-013/014)
- **Loại:** Edge / Negative
- **Ưu tiên:** P3
- **Layer:** E2E (Tauri/Manual)
- **Tiền điều kiện:** Bản ghi chấm công vừa offline vừa có bản online cùng ngày.
- **Bước thực hiện:** 1) Tạo xung đột check-in offline + online. 2) Sync.
- **Dữ liệu test:** Hai bản ghi mâu thuẫn.
- **Kết quả mong đợi:** Conflict được resolve theo rule (vd last-write hoặc giữ bản đầu), không tạo trùng, có thông báo.
- **Coverage hiện tại:** PARTIAL — cần xác minh rule conflict resolution thực tế.

---

### Phụ lục — Quy ước & lưu ý kiểm thử

- **Quy ước Coverage:** COVERED = function `✅ DONE` ở nguồn, kỳ vọng có test (chưa map được file thực tế → "cần xác minh test file"). MISSING = function `⬜ TODO` hoặc `💡 IDEA` (chưa hiện thực / chưa test). PARTIAL = case xuyên suốt RLS/auth/audit/offline dựa cơ chế core dùng chung, cần xác minh phủ riêng cho bảng/endpoint HR.
- **Function DONE (COVERED):** HR-008, HR-009, HR-010, HR-013, HR-014, HR-015, HR-016, HR-017, HR-018, HR-019, HR-022 (chủ yếu thuộc TASK-014; HR-022 thuộc TASK-004).
- **Function TODO/IDEA (MISSING):** HR-001..HR-007 (TASK-006/027), HR-011 (TASK-022), HR-012 (IDEA), HR-020 (TASK-015), HR-021 (IDEA, Phase 3).
- **Cần xác minh khi truy cập được `clinic-cms-merge`:**
  - Map đường dẫn module HR thực tế (vd `app/modules/hr/...`, `app/modules/users/...`) + endpoint chính xác (path/method có thể khác giả định trong catalog).
  - Map test file thực tế trong `tests/` cho từng TC COVERED; cập nhật cột Coverage thành `COVERED (path::test)`.
  - Xác nhận rule nghiệp vụ: công thức giờ làm (check_out − check_in − break_minutes), OT rate (1.5x/2x), threshold late/early (10p), quota annual leave (12 ngày), độ phức tạp temp password (12 chars), format license number theo Bộ Y tế.
- **Đa phòng khám (bắt buộc trước release):** TC-HR-046/047 (RLS) là kiểm thử bắt buộc. Mọi bảng HR phải có `clinic_id` + RLS policy theo `app.current_clinic_id`.
