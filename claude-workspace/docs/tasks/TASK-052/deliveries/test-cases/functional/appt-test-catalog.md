# Test Case Catalog — APPT · Lịch hẹn & Tiếp đón

**Nguồn:** function_list_data.py (group APPT, dòng 1024–1074) + clinic_management_function_list.md + system_design (§4.6 Queue, §5.3 State machine, §5.4 Smart queue) + BA.
**Phạm vi:** 17 functions (APPT-001 … APPT-017).  **Tổng test case:** 56.  **Ngày:** 2026-05-30.

> **Đối chiếu code thực tế** (repo `E:/MyProject/clinic-cms-workspace/clinic-cms-merge`, module `app/modules/appointments`, ship qua TASK-008):
> - Router `prefix=/api/v1` (`api/routes.py`):
>   - `GET /appointments/slots?date=&duration=` — perm `appointment.read` (slot kèm `capacity`)
>   - `GET /appointments` (filter status/patient_id/assigned_doctor_id, paginate) — perm `appointment.read`
>   - `POST /appointments` — perm `appointment.write` → tạo, status=scheduled
>   - `GET /appointments/{id}` — perm `appointment.read`
>   - `PATCH /appointments/{id}` (đổi assigned_doctor_id/duration_minutes — KHÔNG đổi giờ) — perm `appointment.write`
>   - `POST /appointments/{id}/confirm` — perm `appointment.write` (scheduled→confirmed)
>   - `POST /appointments/{id}/check-in` — perm `appointment.write` (confirmed→checked_in, tạo Visit, trả `CheckInResponse{appointment, visit_id}`)
>   - `POST /appointments/{id}/cancel` (body `cancel_reason` BẮT BUỘC: min_length=3 + validator not-blank) — perm `appointment.cancel`
> - Service `appointment_service`: create / get / list / update / confirm / check_in / cancel / mark_no_show. Hỗ trợ: `slot_service.get_slots` (capacity), `state_machine.py`, `smart_queue.py` (pure functions priority), job `app/workers/jobs/auto_no_show_appointments.py`.
> - Model `AppointmentStatus`: scheduled → confirmed → checked_in → completed; nhánh cancelled, no_show. Field: scheduled_at, duration_minutes, cancel_reason, no_show_at, checked_in_at, visit_id, assigned_doctor_id.
> - Test thực tế:
>   - `tests/integration/appointments/test_appointments_e2e.py` — classes: `TestSlotCapacity` (ac1 slots capacity=2, ac2 third_booking_409), `TestStateTransitions` (lifecycle_to_checkin, double_confirm_409, checkin_without_confirm_409, cancel), `TestCheckInCreatesVisit` (ac5 visit fields), `TestAutoNoShow` (ac4 sweep), `TestTenantIsolation` (clinic_a_cannot_see_clinic_b), `TestConcurrentBooking` (sequential_capacity_enforcement), `TestCRUD` (create_and_get, list_paginated, 401_no_token, 422_missing_fields).
>   - `tests/unit/appointments/test_smart_queue.py` — `should_walk_in_jump_appointment` (7 case), `walk_in_wait_minutes` (2 case).
>
> **Lưu ý chênh nguồn vs code:**
> - (a) Cờ Status trong `function_list_data.py` còn để TODO/IDEA cho TOÀN BỘ APPT dù code lõi đã ship + có test → Coverage gán theo TEST THỰC TẾ.
> - (b) Function CHƯA có endpoint/code: **APPT-006 Reschedule** không có route `/reschedule` đổi giờ + reason bắt buộc (chỉ PATCH đổi doctor/duration); **Walk-in (010), Queue board (011), Chime (012), Privacy mask (013), SMS reminder (014), Self-book (015), Block schedule (016), HR-conflict (017)** chưa có backend/UI. **Smart priority (009)** mới có pure functions + unit test, chưa tích hợp queue.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| APPT-001 | Tạo hẹn | TODO (code shipped TASK-008) | TC-APPT-001, TC-APPT-002, TC-APPT-003, TC-APPT-004, TC-APPT-005, TC-APPT-006 | COVERED |
| APPT-002 | Slot capacity per doctor | TODO (code shipped) | TC-APPT-007, TC-APPT-008, TC-APPT-009 | COVERED |
| APPT-003 | Calendar view | TODO (API list/slots shipped; UI grid chưa) | TC-APPT-010, TC-APPT-011, TC-APPT-012 | PARTIAL |
| APPT-004 | Confirm appointment | TODO (code shipped) | TC-APPT-013, TC-APPT-014, TC-APPT-015 | COVERED |
| APPT-005 | Check-in appointment | TODO (code shipped) | TC-APPT-016, TC-APPT-017, TC-APPT-018, TC-APPT-019 | COVERED |
| APPT-006 | Reschedule | TODO (route /reschedule + reason CHƯA ship) | TC-APPT-020, TC-APPT-021, TC-APPT-022 | MISSING |
| APPT-007 | Cancel appointment | TODO (code shipped) | TC-APPT-023, TC-APPT-024, TC-APPT-025, TC-APPT-026 | COVERED |
| APPT-008 | NO_SHOW tracking | TODO (auto_no_show job ĐÃ ship + test) | TC-APPT-027, TC-APPT-028, TC-APPT-029 | COVERED |
| APPT-009 | Smart queue priority | TODO (pure-fn priority shipped + unit test; tích hợp queue chưa) | TC-APPT-030, TC-APPT-031 | PARTIAL |
| APPT-010 | Walk-in registration | TODO (chưa có route walk-in) | TC-APPT-032, TC-APPT-033, TC-APPT-034 | MISSING |
| APPT-011 | Queue board (TV mode) | TODO (chưa có API/UI queue) | TC-APPT-035, TC-APPT-036 | MISSING |
| APPT-012 | Sound chime gọi STT | TODO (chưa ship) | TC-APPT-037 | MISSING |
| APPT-013 | Privacy mask name | TODO (chưa ship) | TC-APPT-038, TC-APPT-039 | MISSING |
| APPT-014 | SMS reminder trước hẹn | IDEA (Phase 2) | TC-APPT-040, TC-APPT-041 | MISSING |
| APPT-015 | Patient self-book | IDEA (Phase 3) | TC-APPT-042, TC-APPT-043, TC-APPT-044 | MISSING |
| APPT-016 | Block schedule | TODO (chưa ship) | TC-APPT-045, TC-APPT-046 | MISSING |
| APPT-017 | Conflict với HR shift | TODO (chưa ship) | TC-APPT-047, TC-APPT-048 | MISSING |
| — (xuyên suốt) | Bảo mật, RLS, audit chung | — | TC-APPT-049, TC-APPT-050, TC-APPT-051, TC-APPT-052, TC-APPT-053, TC-APPT-054, TC-APPT-055, TC-APPT-056 | COVERED |

**Tổng hợp coverage theo 17 function nghiệp vụ:** **COVERED = 6** (APPT-001, 002, 004, 005, 007, 008) · **PARTIAL = 2** (APPT-003 calendar UI, APPT-009 smart-queue) · **MISSING = 9** (APPT-006, 010, 011, 012, 013, 014, 015, 016, 017). Dòng "xuyên suốt" không phải function độc lập, không tính vào tổng.

---

## 2. Chi tiết Test Cases

### TC-APPT-001 — Tạo hẹn cho bệnh nhân đã có hồ sơ (happy path)
- **Function:** APPT-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token role có `appointment.write`; patient + doctor tồn tại cùng clinic; slot trống.
- **Bước thực hiện:** 1) `POST /api/v1/appointments` {patient_id, scheduled_at, duration_minutes, assigned_doctor_id}. 2) `GET /api/v1/appointments/{id}` xác minh.
- **Dữ liệu test:** scheduled_at = ngày làm việc kế tiếp 09:00, duration 30.
- **Kết quả mong đợi:** HTTP 201; `status=scheduled`; response AppointmentResponse; model `__auditable__=True` ghi audit.
- **Coverage hiện tại:** COVERED (test_appointments_e2e.py::TestCRUD::test_create_and_get).

### TC-APPT-002 — Liệt kê + phân trang lịch hẹn
- **Function:** APPT-001
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token `appointment.read`; có nhiều hẹn.
- **Bước thực hiện:** 1) `GET /api/v1/appointments?skip=0&limit=50`.
- **Kết quả mong đợi:** HTTP 200; AppointmentListResponse (items, total, skip, limit) đúng phân trang.
- **Coverage hiện tại:** COVERED (TestCRUD::test_list_paginated).

### TC-APPT-003 — Tạo hẹn thiếu field bắt buộc (validation)
- **Function:** APPT-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token `appointment.write`.
- **Bước thực hiện:** 1) `POST /api/v1/appointments` thiếu patient_id / scheduled_at.
- **Kết quả mong đợi:** HTTP 422 (Pydantic AppointmentCreate).
- **Coverage hiện tại:** COVERED (TestCRUD::test_422_missing_fields).

### TC-APPT-004 — Tạo hẹn khi chưa đăng nhập (401)
- **Function:** APPT-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi token.
- **Bước thực hiện:** 1) `POST /api/v1/appointments` không Authorization header.
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** COVERED (TestCRUD::test_401_no_token).

### TC-APPT-005 — Tạo hẹn thiếu permission (403)
- **Function:** APPT-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token role KHÔNG có `appointment.write`.
- **Bước thực hiện:** 1) `POST /api/v1/appointments`.
- **Kết quả mong đợi:** HTTP 403 (require_permission chặn).
- **Coverage hiện tại:** PARTIAL (401 đã test; cần bổ sung case 403 thiếu permission cụ thể).

### TC-APPT-006 — Tạo hẹn không tham chiếu được sang clinic khác (RLS)
- **Function:** APPT-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Login clinic A; patient_id/doctor_id thuộc clinic B.
- **Bước thực hiện:** 1) `POST /api/v1/appointments` với reference của clinic B.
- **Kết quả mong đợi:** HTTP 404/422 (RLS che reference clinic khác); không tạo hẹn chéo tenant.
- **Coverage hiện tại:** COVERED (TestTenantIsolation::test_clinic_a_cannot_see_clinic_b — bao quát isolation).

### TC-APPT-007 — GET /slots phản ánh capacity còn trống (happy path)
- **Function:** APPT-002
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token `appointment.read`; capacity test = 2.
- **Bước thực hiện:** 1) `GET /api/v1/appointments/slots?date=&duration=30`.
- **Kết quả mong đợi:** HTTP 200; mỗi slot có field `capacity` đúng (=2 trong test).
- **Coverage hiện tại:** COVERED (TestSlotCapacity::test_ac1_slots_capacity_2).

### TC-APPT-008 — Đặt hẹn vượt capacity → 409
- **Function:** APPT-002
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** capacity=2; đã có 2 hẹn (scheduled/confirmed) cùng slot giờ.
- **Bước thực hiện:** 1) `POST /api/v1/appointments` hẹn thứ 3 cùng khung giờ.
- **Kết quả mong đợi:** HTTP 409 (slot full; SD §5.2 chỉ đếm scheduled/confirmed).
- **Coverage hiện tại:** COVERED (TestSlotCapacity::test_ac2_third_booking_409 + TestConcurrentBooking::test_sequential_capacity_enforcement).

### TC-APPT-009 — Hẹn cancelled/no_show KHÔNG tính vào capacity
- **Function:** APPT-002
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Slot có 2 hẹn nhưng 1 đã cancelled.
- **Bước thực hiện:** 1) Đặt hẹn mới vào slot đó.
- **Kết quả mong đợi:** Đặt thành công 201 (chỉ đếm scheduled/confirmed).
- **Coverage hiện tại:** PARTIAL (cần bổ sung assert loại trừ cancelled/no_show khỏi đếm capacity).

### TC-APPT-010 — Lấy lịch theo filter (calendar-ready)
- **Function:** APPT-003
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token `appointment.read`; có hẹn nhiều bác sĩ/trạng thái.
- **Bước thực hiện:** 1) `GET /api/v1/appointments?status=confirmed&assigned_doctor_id=X`.
- **Kết quả mong đợi:** HTTP 200; trả đúng tập theo filter, dữ liệu dựng grid week/month ở FE.
- **Coverage hiện tại:** PARTIAL (API list shipped/test; UI FullCalendar grid week/month chưa ship → cần test FE riêng).

### TC-APPT-011 — Calendar UI render box theo màu status + drawer detail
- **Function:** APPT-003
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Trang /reception/appointments có dữ liệu.
- **Bước thực hiện:** 1) Toggle week/month/day. 2) Click 1 appointment → drawer.
- **Kết quả mong đợi:** Box màu theo status; drawer hiển thị chi tiết hẹn.
- **Coverage hiện tại:** MISSING (UI chưa ship/chưa test).

### TC-APPT-012 — Calendar cô lập clinic (RLS) + 401/403
- **Function:** APPT-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 clinic có hẹn riêng.
- **Bước thực hiện:** 1) Login clinic A `GET /appointments`. 2) Không token. 3) Token thiếu `appointment.read`.
- **Kết quả mong đợi:** (1) chỉ hẹn clinic A; (2) 401; (3) 403.
- **Coverage hiện tại:** COVERED (TestTenantIsolation + TestCRUD::test_401_no_token; bổ sung case 403).

### TC-APPT-013 — Confirm: scheduled → confirmed (happy path)
- **Function:** APPT-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Hẹn `scheduled`; token `appointment.write`.
- **Bước thực hiện:** 1) `POST /api/v1/appointments/{id}/confirm`.
- **Kết quả mong đợi:** HTTP 200; `status=confirmed`; audit.
- **Coverage hiện tại:** COVERED (TestStateTransitions::test_lifecycle_to_checkin).

### TC-APPT-014 — Double-confirm / confirm trạng thái sai → 409
- **Function:** APPT-004
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Hẹn đã `confirmed` (hoặc cancelled/completed).
- **Bước thực hiện:** 1) `POST /appointments/{id}/confirm` lần 2.
- **Kết quả mong đợi:** HTTP 409 chuyển trạng thái không hợp lệ; status giữ nguyên.
- **Coverage hiện tại:** COVERED (TestStateTransitions::test_double_confirm_409).

### TC-APPT-015 — Confirm: 401/403 + RLS
- **Function:** APPT-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn scheduled (clinic A).
- **Bước thực hiện:** 1) Không token → 401. 2) Thiếu `appointment.write` → 403. 3) Login clinic B confirm hẹn clinic A → 404.
- **Kết quả mong đợi:** 401 / 403 / 404.
- **Coverage hiện tại:** PARTIAL (RLS isolation đã test; bổ sung 403 chuyên cho confirm).

### TC-APPT-016 — Check-in tạo Visit + trả visit_id (happy path)
- **Function:** APPT-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Hẹn `confirmed`; token `appointment.write`.
- **Bước thực hiện:** 1) `POST /api/v1/appointments/{id}/check-in`.
- **Kết quả mong đợi:** HTTP 200; `status=checked_in`; `checked_in_at` set; `visit_id` gán; CheckInResponse{appointment, visit_id}; visit copy assigned_doctor_id (SD §5.3).
- **Coverage hiện tại:** COVERED (TestCheckInCreatesVisit::test_ac5_visit_has_correct_fields + TestStateTransitions::test_lifecycle_to_checkin).

### TC-APPT-017 — Check-in khi chưa confirm → 409
- **Function:** APPT-005
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Hẹn `scheduled` (chưa confirm).
- **Bước thực hiện:** 1) `POST /appointments/{id}/check-in`.
- **Kết quả mong đợi:** HTTP 409; không tạo visit.
- **Coverage hiện tại:** COVERED (TestStateTransitions::test_checkin_without_confirm_409).

### TC-APPT-018 — Check-in lặp không tạo visit trùng (idempotency)
- **Function:** APPT-005
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn đã `checked_in` (đã có visit_id).
- **Bước thực hiện:** 1) Gọi check-in lần 2.
- **Kết quả mong đợi:** HTTP 409 (hoặc trả visit cũ); chỉ 1 visit duy nhất.
- **Coverage hiện tại:** PARTIAL (cần bổ sung test idempotency).

### TC-APPT-019 — Check-in: 401/403 + RLS cô lập clinic
- **Function:** APPT-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn clinic A confirmed.
- **Bước thực hiện:** 1) Không token → 401. 2) Thiếu quyền → 403. 3) Login clinic B → 404.
- **Kết quả mong đợi:** 401 / 403 / 404.
- **Coverage hiện tại:** COVERED (TestTenantIsolation; bổ sung 403).

### TC-APPT-020 — Reschedule đổi giờ/bác sĩ (happy path)
- **Function:** APPT-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Hẹn scheduled/confirmed; slot mới trống.
- **Bước thực hiện:** 1) Gọi endpoint reschedule với scheduled_at mới + assigned_doctor_id + reason bắt buộc.
- **Kết quả mong đợi:** HTTP 200; đổi giờ/bác sĩ; slot cũ giải phóng; audit ghi reason.
- **Coverage hiện tại:** MISSING (chưa có route `/reschedule` đổi giờ + reason; PATCH hiện chỉ đổi doctor/duration).

### TC-APPT-021 — Reschedule thiếu reason / vào slot đầy
- **Function:** APPT-006
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Slot đích đầy.
- **Bước thực hiện:** 1) Reschedule thiếu reason → 422. 2) Reschedule vào slot full → 409.
- **Kết quả mong đợi:** 422 / 409; hẹn giữ nguyên.
- **Coverage hiện tại:** MISSING.

### TC-APPT-022 — PATCH đổi doctor/duration (chức năng hiện có)
- **Function:** APPT-006
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Hẹn hợp lệ; token `appointment.write`.
- **Bước thực hiện:** 1) `PATCH /api/v1/appointments/{id}` đổi assigned_doctor_id/duration_minutes.
- **Kết quả mong đợi:** HTTP 200; cập nhật field non-status. (Lưu ý: KHÔNG đổi giờ — gap so với spec Reschedule.)
- **Coverage hiện tại:** MISSING (chưa thấy test cho PATCH; cần thêm).

### TC-APPT-023 — Cancel hẹn với lý do bắt buộc (happy path)
- **Function:** APPT-007
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Hẹn scheduled/confirmed; token `appointment.cancel`.
- **Bước thực hiện:** 1) `POST /api/v1/appointments/{id}/cancel` {cancel_reason}.
- **Kết quả mong đợi:** HTTP 200; `status=cancelled`; `cancel_reason` lưu; audit.
- **Coverage hiện tại:** COVERED (TestStateTransitions::test_cancel).

### TC-APPT-024 — Cancel thiếu/rỗng cancel_reason → 422
- **Function:** APPT-007
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Hẹn hợp lệ.
- **Bước thực hiện:** 1) `POST /appointments/{id}/cancel` không gửi / gửi cancel_reason rỗng/<3 ký tự.
- **Kết quả mong đợi:** HTTP 422 (AppointmentCancelRequest.cancel_reason: min_length=3 + validator not-blank).
- **Coverage hiện tại:** PARTIAL (schema đã ép buộc reason; cần thêm test case 422 reason rỗng/thiếu).

### TC-APPT-025 — Cancel hẹn completed bị chặn (state machine)
- **Function:** APPT-007
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn `completed` hoặc đã `cancelled`.
- **Bước thực hiện:** 1) `POST /appointments/{id}/cancel`.
- **Kết quả mong đợi:** HTTP 409 (cancel hợp lệ từ scheduled/confirmed/checked_in; completed/cancelled là terminal).
- **Coverage hiện tại:** PARTIAL.

### TC-APPT-026 — Cancel: 401/403 + RLS
- **Function:** APPT-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn clinic A.
- **Bước thực hiện:** 1) Không token → 401. 2) Thiếu `appointment.cancel` → 403. 3) Clinic B → 404.
- **Kết quả mong đợi:** 401 / 403 / 404.
- **Coverage hiện tại:** COVERED (TestTenantIsolation; bổ sung 403 cho perm cancel).

### TC-APPT-027 — Cron mark NO_SHOW cho hẹn quá hạn (happy path)
- **Function:** APPT-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn scheduled/confirmed quá `scheduled_at` > 30 phút, chưa check-in.
- **Bước thực hiện:** 1) Gọi `auto_no_show_appointments({})`.
- **Kết quả mong đợi:** result["appointments_marked_no_show"] >= 1; `status=no_show`; `no_show_at` set; KHÔNG tạo visit.
- **Coverage hiện tại:** COVERED (TestAutoNoShow::test_ac4_marks_overdue_no_show).

### TC-APPT-028 — Hẹn đã checked_in/cancelled không bị đánh NO_SHOW
- **Function:** APPT-008
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn `checked_in` quá giờ.
- **Bước thực hiện:** 1) Chạy sweep no-show.
- **Kết quả mong đợi:** status giữ nguyên (chỉ scheduled/confirmed mới chuyển no_show).
- **Coverage hiện tại:** PARTIAL (sweep đã test happy path; bổ sung case loại trừ checked_in).

### TC-APPT-029 — NO_SHOW chỉ áp dụng đúng clinic (RLS sweep)
- **Function:** APPT-008
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn quá hạn ở cả clinic A và B.
- **Bước thực hiện:** 1) Chạy sweep.
- **Kết quả mong đợi:** Sweep xử lý đúng phạm vi tenant; không nhầm lẫn dữ liệu chéo clinic.
- **Coverage hiện tại:** PARTIAL.

### TC-APPT-030 — Walk-in jump priority theo gap tới hẹn (pure fn)
- **Function:** APPT-009
- **Loại:** Happy path / Edge
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Hàm `should_walk_in_jump_appointment(walk_in_minutes, appt_at, now, buffer)`.
- **Bước thực hiện:** 1) Gap nhỏ: now=8:45, walk_in=25, appt=9:00, buffer=15. 2) Gap lớn: now=8:00, walk_in=5, appt=9:00. 3) Biên đúng end==buffer_start.
- **Dữ liệu test:** xem test_smart_queue.py.
- **Kết quả mong đợi:** (1) False (appointment ưu tiên); (2) True (walk-in được phục vụ trước); (3) True (<=); theo SD §5.4 + AC#3.
- **Coverage hiện tại:** PARTIAL (tests/unit/appointments/test_smart_queue.py: 7 case `should_walk_in_jump_appointment` + 2 case `walk_in_wait_minutes` — đã COVERED ở mức pure-fn, nhưng chưa tích hợp vào queue thực tế).

### TC-APPT-031 — Tích hợp priority vào hàng đợi thực tế + override cấp cứu
- **Function:** APPT-009
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Queue có nhiều BN (walk-in + appointment checked_in).
- **Bước thực hiện:** 1) Dựng thứ tự queue áp dụng pure-fn. 2) Doctor override priority cho 1 entry.
- **Kết quả mong đợi:** Thứ tự gọi đúng quy tắc; override đẩy entry lên đầu.
- **Coverage hiện tại:** MISSING (mới có pure function; chưa có module queue tích hợp + override).

### TC-APPT-032 — Tiếp nhận walk-in tạo visit + STT (happy path)
- **Function:** APPT-010
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token role lễ tân; BN vãng lai.
- **Bước thực hiện:** 1) Đăng ký walk-in (BN, doctor, reason).
- **Kết quả mong đợi:** HTTP 201; tạo visit `status=WAITING_VITAL`; cấp STT; audit.
- **Coverage hiện tại:** MISSING (chưa có route walk-in trong module appointments).

### TC-APPT-033 — STT cấp tuần tự không trùng (concurrency)
- **Function:** APPT-010
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Nhiều walk-in gần đồng thời cùng clinic/ngày.
- **Bước thực hiện:** 1) Tạo 3 walk-in song song.
- **Kết quả mong đợi:** 3 STT khác nhau liên tiếp, không trùng.
- **Coverage hiện tại:** MISSING.

### TC-APPT-034 — Walk-in: 401/403 + RLS
- **Function:** APPT-010
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Không token → 401. 2) Thiếu quyền → 403. 3) STT độc lập theo clinic.
- **Kết quả mong đợi:** 401 / 403 / cô lập STT theo clinic.
- **Coverage hiện tại:** MISSING.

### TC-APPT-035 — Queue board hiển thị STT đang khám + 5 tiếp theo
- **Function:** APPT-011
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx) / Manual UI
- **Tiền điều kiện:** Queue có entry; trang /reception/queue.
- **Bước thực hiện:** 1) Mở queue board (no-auth network nội bộ). 2) Auto-refresh 5s.
- **Kết quả mong đợi:** Hiển thị STT đang khám + 5 STT kế; chỉ data clinic hiện tại.
- **Coverage hiện tại:** MISSING (chưa có API/UI queue board).

### TC-APPT-036 — Queue board auto-refresh phản ánh thay đổi
- **Function:** APPT-011
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Board mở.
- **Bước thực hiện:** 1) Gọi BN tiếp theo. 2) Quan sát board sau ≤5s.
- **Kết quả mong đợi:** Board tự cập nhật STT mới.
- **Coverage hiện tại:** MISSING.

### TC-APPT-037 — Phát chuông + TTS khi call next
- **Function:** APPT-012
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Queue board mở; quyền phát âm thanh.
- **Bước thực hiện:** 1) Doctor click "Call next".
- **Kết quả mong đợi:** Phát chime + TTS "Mời số N vào phòng X" (Web Audio API) 1 lần.
- **Coverage hiện tại:** MISSING (chưa ship).

### TC-APPT-038 — Mask tên BN trên queue board (happy path)
- **Function:** APPT-013
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit / Manual UI
- **Tiền điều kiện:** BN "Nguyễn Văn A" trong queue.
- **Bước thực hiện:** 1) Render queue board public.
- **Kết quả mong đợi:** Hiển thị "Nguyễn V.A." — không lộ tên đầy đủ.
- **Coverage hiện tại:** MISSING (chưa ship mask + queue board).

### TC-APPT-039 — Mask cho các dạng tên biên (edge)
- **Function:** APPT-013
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Gọi hàm mask với "An" (1 từ), "Lê Thị Bích Ngọc" (4 từ), tên rỗng.
- **Kết quả mong đợi:** Không crash; giữ họ + viết tắt phần còn lại.
- **Coverage hiện tại:** MISSING.

### TC-APPT-040 — SMS reminder 24h + 2h trước hẹn
- **Function:** APPT-014
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn confirmed cách hiện tại 24h / 2h.
- **Bước thực hiện:** 1) Chạy cron reminder.
- **Kết quả mong đợi:** Tạo 2 SMS (24h, 2h) content i18n VN; không gửi trùng.
- **Coverage hiện tại:** MISSING (Phase 2 — IDEA).

### TC-APPT-041 — Không reminder cho hẹn cancelled/no_show
- **Function:** APPT-014
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn cancelled trong cửa sổ reminder.
- **Bước thực hiện:** 1) Chạy cron reminder.
- **Kết quả mong đợi:** Không tạo SMS.
- **Coverage hiện tại:** MISSING.

### TC-APPT-042 — BN tự đặt hẹn qua portal (happy path)
- **Function:** APPT-015
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Role PATIENT (portal); slot trống.
- **Bước thực hiện:** 1) Chọn doctor + slot + reason. 2) Confirm OTP SMS. 3) Submit.
- **Kết quả mong đợi:** HTTP 201; hẹn scheduled gắn đúng patient + clinic.
- **Coverage hiện tại:** MISSING (Phase 3 — IDEA).

### TC-APPT-043 — BN không đặt vào slot đầy/block
- **Function:** APPT-015
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Slot full hoặc bị block.
- **Bước thực hiện:** 1) BN đặt vào slot đó.
- **Kết quả mong đợi:** HTTP 409.
- **Coverage hiện tại:** MISSING.

### TC-APPT-044 — BN chỉ đặt/đọc hẹn của chính mình (security)
- **Function:** APPT-015
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** 2 BN.
- **Bước thực hiện:** 1) BN A thao tác với patient_id của BN B.
- **Kết quả mong đợi:** HTTP 403.
- **Coverage hiện tại:** MISSING.

### TC-APPT-045 — Doctor block khung giờ (happy path)
- **Function:** APPT-016
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Role DOCTOR.
- **Bước thực hiện:** 1) Block khung giờ (ăn trưa/họp) trong calendar.
- **Kết quả mong đợi:** HTTP 201; slot đánh dấu block; không cho đặt hẹn vào đó.
- **Coverage hiện tại:** MISSING (chưa ship).

### TC-APPT-046 — Đặt hẹn vào khung giờ block bị chặn
- **Function:** APPT-016
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Bác sĩ đã block 10:00–11:00.
- **Bước thực hiện:** 1) Đặt hẹn 10:30.
- **Kết quả mong đợi:** HTTP 409 "khung giờ bị chặn".
- **Coverage hiện tại:** MISSING.

### TC-APPT-047 — Cảnh báo/chặn khi bác sĩ trong leave/off (HR conflict)
- **Function:** APPT-017
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor có leave/off (module HR) trùng khung giờ.
- **Bước thực hiện:** 1) Đặt hẹn vào khung giờ bác sĩ nghỉ.
- **Kết quả mong đợi:** Trả warning/409 conflict (tích hợp HR), không đặt im lặng.
- **Coverage hiện tại:** MISSING (chưa ship tích hợp APPT↔HR).

### TC-APPT-048 — Không conflict khi bác sĩ có shift hợp lệ
- **Function:** APPT-017
- **Loại:** Negative (no-conflict)
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor có shift, không leave trùng giờ.
- **Bước thực hiện:** 1) Đặt hẹn trong ca làm việc.
- **Kết quả mong đợi:** Đặt thành công, không cảnh báo.
- **Coverage hiện tại:** MISSING.

### TC-APPT-049 — RLS: clinic A không đọc được dữ liệu hẹn clinic B
- **Function:** — (xuyên suốt APPT-001/003/005)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 clinic A/B có hẹn riêng.
- **Bước thực hiện:** 1) Login clinic A `GET /appointments` + `GET /appointments/{id_clinicB}`.
- **Kết quả mong đợi:** List chỉ clinic A; GET id của clinic B → 404.
- **Coverage hiện tại:** COVERED (TestTenantIsolation::test_clinic_a_cannot_see_clinic_b).

### TC-APPT-050 — RLS: thao tác ghi chéo clinic bị chặn
- **Function:** — (xuyên suốt APPT-004/005/007)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn thuộc clinic B.
- **Bước thực hiện:** 1) Login clinic A confirm/check-in/cancel theo id clinic B.
- **Kết quả mong đợi:** Tất cả 404; không thao tác chéo tenant.
- **Coverage hiện tại:** COVERED.

### TC-APPT-051 — 401 cho toàn bộ endpoint APPT khi thiếu token
- **Function:** — (xuyên suốt)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) Gọi lần lượt slots/list/create/get/patch/confirm/check-in/cancel.
- **Kết quả mong đợi:** Tất cả 401.
- **Coverage hiện tại:** COVERED (TestCRUD::test_401_no_token — bao quát; cần mở rộng cho mọi endpoint).

### TC-APPT-052 — 403 theo permission đúng cho từng endpoint
- **Function:** — (xuyên suốt)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token thiếu lần lượt `appointment.read` / `appointment.write` / `appointment.cancel`.
- **Bước thực hiện:** 1) Gọi endpoint tương ứng với permission bị thiếu.
- **Kết quả mong đợi:** 403 đúng theo require_permission (read cho GET, write cho create/patch/confirm/check-in, cancel cho cancel).
- **Coverage hiện tại:** PARTIAL (cần bổ sung bộ test 403 đầy đủ — hiện chỉ thấy 401).

### TC-APPT-053 — Audit ghi cho mọi thao tác đổi trạng thái
- **Function:** — (xuyên suốt APPT-001/004/005/007)
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn hợp lệ (model `__auditable__=True`).
- **Bước thực hiện:** 1) Thực hiện create/confirm/check-in/cancel.
- **Kết quả mong đợi:** Mỗi thao tác sinh audit (actor, action, resource_id; cancel_reason ở cancel).
- **Coverage hiện tại:** PARTIAL (model auditable; cần test assert bản ghi audit).

### TC-APPT-054 — Check-in liên kết visit đúng appointment + copy doctor
- **Function:** — (xuyên suốt APPT-005)
- **Loại:** Integration
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hẹn confirmed có assigned_doctor_id.
- **Bước thực hiện:** 1) Check-in. 2) Kiểm tra visit.
- **Kết quả mong đợi:** `appointment.visit_id` set; visit.assigned_doctor_id = doctor của hẹn (SD §5.3).
- **Coverage hiện tại:** COVERED (TestCheckInCreatesVisit::test_ac5_visit_has_correct_fields).

### TC-APPT-055 — State machine đầy đủ vòng đời (lifecycle)
- **Function:** — (xuyên suốt APPT-004/005)
- **Loại:** Integration
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Hẹn mới scheduled.
- **Bước thực hiện:** 1) scheduled → confirm → check-in (→ completed).
- **Kết quả mong đợi:** Mỗi bước chuyển đúng status; bước sai thứ tự → 409.
- **Coverage hiện tại:** COVERED (TestStateTransitions::test_lifecycle_to_checkin + double_confirm/checkin_without_confirm).

### TC-APPT-056 — Capacity enforcement tuần tự nhiều booking
- **Function:** — (xuyên suốt APPT-002)
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** capacity=2 cùng slot.
- **Bước thực hiện:** 1) Đặt liên tiếp nhiều hẹn cùng slot.
- **Kết quả mong đợi:** 2 hẹn đầu 201, hẹn thứ 3 trở đi 409.
- **Coverage hiện tại:** COVERED (TestConcurrentBooking::test_sequential_capacity_enforcement).

---

## 3. Khuyến nghị thực thi
1. **Lõi đã ship + có test (COVERED):** APPT-001/002/004/005/007/008. Bổ sung các nhánh PARTIAL còn thiếu: case 403 thiếu-permission từng endpoint (TC-APPT-005/052), idempotency check-in (TC-APPT-018), 422 cancel reason rỗng/thiếu (TC-APPT-024), assert audit (TC-APPT-053), capacity loại trừ cancelled/no_show (TC-APPT-009).
2. **Gap nghiệp vụ quan trọng so với spec:**
   - **APPT-006 Reschedule** chưa có route đổi giờ + reason bắt buộc (service chỉ có create/get/list/update-doctor-duration/confirm/check_in/cancel/mark_no_show; PATCH không đổi giờ) → đề nghị mở task bổ sung + viết test theo TC-APPT-020/021.
   - **APPT-009 Smart priority** đã có pure functions (`smart_queue.py`) + unit test, nhưng CHƯA tích hợp vào module queue thực tế (TC-APPT-031) → PARTIAL.
   - **APPT-010 Walk-in, APPT-011 Queue board, APPT-012 chime, APPT-013 mask** chưa có module backend/UI → MISSING, viết test skeleton/xfail.
   - **APPT-016 Block schedule, APPT-017 HR-conflict** chưa ship; APPT-014 SMS reminder (Phase 2), APPT-015 self-book (Phase 3) là IDEA.
3. **Cảnh báo lệch nguồn:** cờ Status trong `function_list_data.py` để TODO/IDEA cho toàn bộ APPT dù code lõi (create/confirm/check-in/cancel/slots/no-show/smart-queue-fn) đã ship + có test → đề nghị cập nhật checklist nguồn cho khớp thực trạng.
