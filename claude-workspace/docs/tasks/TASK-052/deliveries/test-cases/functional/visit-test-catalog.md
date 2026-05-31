# Test Case Catalog — VISIT · Lượt khám (Visit/Encounter)

**Nguồn:** function_list_data.py (group VISIT) + clinic_management_function_list.md + system_design/BA + code thực tế `clinic-cms-merge/app/modules/visits`.
**Phạm vi:** 14 functions (VIS-001 … VIS-014).  **Tổng test case:** 46.  **Ngày:** 2026-05-30.

> **Ghi chú nền tảng (áp dụng chung):**
> - Endpoint base: `/visits` (router `app/modules/visits/router.py`).
> - Endpoints đã ship: `POST /visits` (visit.create), `GET /visits` (visit.read), `GET /visits/{id}` (visit.read), `POST /visits/call-next` (visit.consult), `PATCH /visits/{id}/status` (visit.update), `POST /visits/{id}/reassign` (visit.reassign), `GET /visits/{id}/events` (visit.read), `PATCH /visits/{id}` (visit.update).
> - State machine (`state_machine.py`, enum `VisitStatus`): `WAITING_VITAL → {VITAL_DONE, NO_SHOW, CANCELLED}`; `VITAL_DONE → {IN_CONSULTATION, CANCELLED}`; `IN_CONSULTATION → {PAUSED, WAITING_PHARMACY, WAITING_PAYMENT, COMPLETED}`; `PAUSED → {IN_CONSULTATION, CANCELLED}`; `WAITING_PHARMACY → {WAITING_PAYMENT, COMPLETED}`; `WAITING_PAYMENT → {COMPLETED}`; `COMPLETED / NO_SHOW / CANCELLED` = terminal (không transition).
> - Mọi endpoint yêu cầu JWT hợp lệ → tất cả TC có quyền đều phải kiểm 401 (chưa auth) + 403 (thiếu permission) ở mức group (xem TC-VIS-SEC-01/02).
> - Dữ liệu domain (visit, patient, doctor) chịu RLS theo `clinic_id` → kiểm cô lập tenant (xem TC-VIS-RLS-01).
> - Test hiện có trong repo: `tests/unit/test_state_machine.py` (5 test), `tests/unit/test_visit_number.py`. CHƯA có integration/e2e cho visit ⇒ phần lớn API path đánh giá PARTIAL/MISSING.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| VIS-001 | Tạo visit (walk-in / từ appointment) | ✅ DONE | TC-VIS-001-01, TC-VIS-001-02, TC-VIS-001-03, TC-VIS-001-04, TC-VIS-001-05 | PARTIAL |
| VIS-002 | Auto-gen visit_number | ✅ DONE | TC-VIS-002-01, TC-VIS-002-02, TC-VIS-002-03 | PARTIAL |
| VIS-003 | Visit state machine | ✅ DONE | TC-VIS-003-01, TC-VIS-003-02, TC-VIS-003-03, TC-VIS-003-04 | COVERED |
| VIS-004 | NO_SHOW status | ✅ DONE | TC-VIS-004-01, TC-VIS-004-02 | PARTIAL |
| VIS-005 | CANCELLED status | ✅ DONE | TC-VIS-005-01, TC-VIS-005-02, TC-VIS-005-03 | PARTIAL |
| VIS-006 | PAUSED status | ✅ DONE | TC-VIS-006-01, TC-VIS-006-02 | PARTIAL |
| VIS-007 | Resume visit | ✅ DONE | TC-VIS-007-01, TC-VIS-007-02 | PARTIAL |
| VIS-008 | Lịch sử visit của BN | ✅ DONE | TC-VIS-008-01, TC-VIS-008-02, TC-VIS-008-03 | PARTIAL |
| VIS-009 | Visit doctor assignment | ✅ DONE | TC-VIS-009-01, TC-VIS-009-02 | PARTIAL |
| VIS-010 | Reassign doctor | ✅ DONE | TC-VIS-010-01, TC-VIS-010-02, TC-VIS-010-03 | PARTIAL |
| VIS-011 | Visit reason (free text) | ✅ DONE | TC-VIS-011-01, TC-VIS-011-02 | PARTIAL |
| VIS-012 | Concurrent call-next safe | ✅ DONE | TC-VIS-012-01, TC-VIS-012-02, TC-VIS-012-03 | PARTIAL |
| VIS-013 | Visit completion auto-trigger | ✅ DONE | TC-VIS-013-01, TC-VIS-013-02, TC-VIS-013-03 | PARTIAL |
| VIS-014 | Tài liệu đính kèm visit | ⬜ TODO (storage) | TC-VIS-014-01, TC-VIS-014-02 | MISSING |
| (group) | Bảo mật & cô lập tenant | — | TC-VIS-SEC-01, TC-VIS-SEC-02, TC-VIS-RLS-01 | PARTIAL |

**Tổng hợp coverage theo function:** COVERED = 1 (VIS-003) · PARTIAL = 12 · MISSING = 1 (VIS-014).

---

## 2. Chi tiết Test Cases

### TC-VIS-001-01 — Tạo visit walk-in thành công
- **Function:** VIS-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User role Receptionist+ có perm `visit.create`; tồn tại patient + doctor trong clinic.
- **Bước thực hiện:** 1) `POST /visits` với `{patient_id, doctor_id, type:"WALK_IN", reason:"Đau đầu"}`. 2) Đọc response.
- **Dữ liệu test:** patient_id, doctor_id hợp lệ cùng clinic.
- **Kết quả mong đợi:** HTTP 201; `status=WAITING_VITAL`; có `visit_number` đúng format; `type=WALK_IN`; audit `visit.create`.
- **Coverage hiện tại:** MISSING (chưa có integration/e2e cho create_visit).

### TC-VIS-001-02 — Tạo visit từ appointment
- **Function:** VIS-001
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Tồn tại appointment SCHEDULED.
- **Bước thực hiện:** 1) `POST /visits` với `{patient_id, doctor_id, type:"APPOINTMENT", appointment_id}`.
- **Dữ liệu test:** appointment_id hợp lệ.
- **Kết quả mong đợi:** HTTP 201; visit kế thừa thông tin từ appointment; appointment chuyển trạng thái đã check-in (liên kết).
- **Coverage hiện tại:** MISSING.

### TC-VIS-001-03 — Tạo visit với patient_id không tồn tại
- **Function:** VIS-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Auth hợp lệ.
- **Bước thực hiện:** 1) `POST /visits` với `patient_id` random UUID.
- **Dữ liệu test:** UUID không tồn tại.
- **Kết quả mong đợi:** HTTP 404 (hoặc 422); không tạo visit; không sinh visit_number.
- **Coverage hiện tại:** MISSING.

### TC-VIS-001-04 — Tạo visit thiếu trường bắt buộc
- **Function:** VIS-001
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Auth hợp lệ.
- **Bước thực hiện:** 1) `POST /visits` thiếu `patient_id`.
- **Dữ liệu test:** payload thiếu field.
- **Kết quả mong đợi:** HTTP 422 (pydantic validation).
- **Coverage hiện tại:** MISSING.

### TC-VIS-001-05 — Tạo visit không có quyền
- **Function:** VIS-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User KHÔNG có `visit.create` (vd role chỉ đọc).
- **Bước thực hiện:** 1) `POST /visits` payload hợp lệ.
- **Dữ liệu test:** token role thiếu perm.
- **Kết quả mong đợi:** HTTP 403.
- **Coverage hiện tại:** MISSING.

### TC-VIS-002-01 — visit_number đúng format & reset hàng ngày
- **Function:** VIS-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** DB function `fn_next_visit_number(clinic_id, date)` đã migrate.
- **Bước thực hiện:** 1) Sinh số cho ngày D, clinic A nhiều lần. 2) Sinh số cho ngày D+1.
- **Dữ liệu test:** prefix default 'KB'.
- **Kết quả mong đợi:** Format `KB-2026-04-30-0001`; STT tăng tuần tự trong ngày; reset về 0001 sang ngày mới.
- **Coverage hiện tại:** PARTIAL (`tests/unit/test_visit_number.py` cover logic format; xác nhận reset/sequence ở DB cần integration).

### TC-VIS-002-02 — Prefix tuỳ chỉnh per clinic
- **Function:** VIS-002
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic B có setting prefix = 'PK'.
- **Bước thực hiện:** 1) Tạo visit clinic B.
- **Dữ liệu test:** clinic setting prefix khác default.
- **Kết quả mong đợi:** visit_number dùng prefix 'PK'.
- **Coverage hiện tại:** MISSING.

### TC-VIS-002-03 — Sinh số đồng thời race-safe
- **Function:** VIS-002
- **Loại:** Edge (concurrency)
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** DB function dùng row lock.
- **Bước thực hiện:** 1) Gọi đồng thời N lần `fn_next_visit_number` cùng clinic+ngày.
- **Dữ liệu test:** N=10 concurrent.
- **Kết quả mong đợi:** N số khác nhau, không trùng STT, không gap-lỗi.
- **Coverage hiện tại:** MISSING.

### TC-VIS-003-01 — Transition hợp lệ được chấp nhận
- **Function:** VIS-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit
- **Tiền điều kiện:** Module state_machine import được.
- **Bước thực hiện:** 1) Kiểm `WAITING_VITAL → VITAL_DONE`, `VITAL_DONE → IN_CONSULTATION`, `IN_CONSULTATION → COMPLETED` đều được phép.
- **Dữ liệu test:** cặp state hợp lệ trong ALLOWED_TRANSITIONS.
- **Kết quả mong đợi:** Không raise lỗi; transition pass.
- **Coverage hiện tại:** COVERED (`test_state_machine.py::test_pause_resume_cycle` và các test transition).

### TC-VIS-003-02 — Transition không hợp lệ bị từ chối
- **Function:** VIS-003
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Unit
- **Tiền điều kiện:** -
- **Bước thực hiện:** 1) Thử `WAITING_VITAL → COMPLETED` (skip state).
- **Dữ liệu test:** cặp state không có trong ALLOWED_TRANSITIONS.
- **Kết quả mong đợi:** Raise lỗi transition không hợp lệ.
- **Coverage hiện tại:** COVERED (`test_state_machine.py::test_invalid_transition_raises`).

### TC-VIS-003-03 — Các terminal state không có transition ra
- **Function:** VIS-003
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** -
- **Bước thực hiện:** 1) Kiểm `COMPLETED`, `NO_SHOW`, `CANCELLED` đều có tập transition rỗng.
- **Dữ liệu test:** 3 terminal state.
- **Kết quả mong đợi:** Mọi transition từ terminal state bị từ chối.
- **Coverage hiện tại:** COVERED (`test_state_machine.py::test_all_terminal_states_have_no_transitions`, `test_completed_is_terminal`).

### TC-VIS-003-04 — Guard quyền theo transition (chỉ doctor set COMPLETED)
- **Function:** VIS-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User non-doctor có `visit.update` nhưng không phải doctor của visit.
- **Bước thực hiện:** 1) `PATCH /visits/{id}/status` đặt `COMPLETED` bởi non-doctor.
- **Dữ liệu test:** visit IN_CONSULTATION.
- **Kết quả mong đợi:** HTTP 403 (guard nghiệp vụ: chỉ doctor được COMPLETED).
- **Coverage hiện tại:** MISSING (guard quyền theo vai trong service chưa có e2e).

### TC-VIS-004-01 — Đánh dấu NO_SHOW thủ công
- **Function:** VIS-004
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit `WAITING_VITAL`; user perm `visit.update`.
- **Bước thực hiện:** 1) `PATCH /visits/{id}/status` `{status:"NO_SHOW"}`.
- **Dữ liệu test:** visit chưa khám.
- **Kết quả mong đợi:** HTTP 200; `status=NO_SHOW`; KHÔNG tạo invoice; ghi visit_event.
- **Coverage hiện tại:** PARTIAL (transition cho phép đã cover unit; side-effect "không tạo invoice" cần e2e).

### TC-VIS-004-02 — NO_SHOW từ state không hợp lệ
- **Function:** VIS-004
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit đã `IN_CONSULTATION`.
- **Bước thực hiện:** 1) `PATCH .../status` `{status:"NO_SHOW"}`.
- **Dữ liệu test:** visit đang khám.
- **Kết quả mong đợi:** HTTP 409/422 (transition không hợp lệ; NO_SHOW chỉ từ WAITING_VITAL).
- **Coverage hiện tại:** PARTIAL (logic transition cover unit; HTTP cần e2e).

### TC-VIS-005-01 — Hủy visit có lý do
- **Function:** VIS-005
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit chưa COMPLETED; perm `visit.update`.
- **Bước thực hiện:** 1) `PATCH .../status` `{status:"CANCELLED", reason:"BN xin về"}`.
- **Dữ liệu test:** lý do hủy hợp lệ.
- **Kết quả mong đợi:** HTTP 200; `status=CANCELLED`; lưu cancelled_by/at/reason; KHÔNG tạo invoice.
- **Coverage hiện tại:** PARTIAL (transition cover unit; field cancelled_* + no-invoice cần e2e).

### TC-VIS-005-02 — Hủy visit thiếu lý do bắt buộc
- **Function:** VIS-005
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit hợp lệ.
- **Bước thực hiện:** 1) `PATCH .../status` `{status:"CANCELLED"}` không kèm reason.
- **Dữ liệu test:** payload thiếu reason.
- **Kết quả mong đợi:** HTTP 422 (reason bắt buộc khi CANCELLED).
- **Coverage hiện tại:** MISSING.

### TC-VIS-005-03 — Hủy visit từ appointment → khôi phục appointment
- **Function:** VIS-005
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit tạo từ appointment.
- **Bước thực hiện:** 1) Hủy visit. 2) Kiểm appointment.
- **Dữ liệu test:** visit type APPOINTMENT.
- **Kết quả mong đợi:** appointment quay về `SCHEDULED`.
- **Coverage hiện tại:** MISSING.

### TC-VIS-006-01 — Tạm dừng visit khi đang khám
- **Function:** VIS-006
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit `IN_CONSULTATION`; user là doctor.
- **Bước thực hiện:** 1) `PATCH .../status` `{status:"PAUSED", pause_reason:"Đi XN"}`.
- **Dữ liệu test:** visit đang khám.
- **Kết quả mong đợi:** HTTP 200; `status=PAUSED`; lưu pause_reason + timestamp; ra khỏi queue active.
- **Coverage hiện tại:** PARTIAL (cycle pause/resume cover unit; side-effect queue cần e2e).

### TC-VIS-006-02 — PAUSED chỉ cho phép từ IN_CONSULTATION
- **Function:** VIS-006
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit `WAITING_VITAL`.
- **Bước thực hiện:** 1) `PATCH .../status` `{status:"PAUSED"}`.
- **Dữ liệu test:** visit chưa vào khám.
- **Kết quả mong đợi:** HTTP 409/422 (transition không hợp lệ).
- **Coverage hiện tại:** PARTIAL (logic transition cover unit).

### TC-VIS-007-01 — Resume visit về IN_CONSULTATION
- **Function:** VIS-007
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit `PAUSED`; user là doctor.
- **Bước thực hiện:** 1) `PATCH .../status` `{status:"IN_CONSULTATION"}`.
- **Dữ liệu test:** visit đang pause.
- **Kết quả mong đợi:** HTTP 200; `status=IN_CONSULTATION`; ghi resume timestamp; dữ liệu vital/diag/rx đã lưu giữ nguyên.
- **Coverage hiện tại:** PARTIAL (`test_state_machine.py::test_pause_resume_cycle` cover transition; timestamp/data-retention cần e2e).

### TC-VIS-007-02 — Tính tổng thời lượng visit qua pause/resume
- **Function:** VIS-007
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit trải qua pause + resume nhiều lần.
- **Bước thực hiện:** 1) Pause/resume 2 vòng. 2) Đọc visit_events.
- **Dữ liệu test:** chuỗi event timestamps.
- **Kết quả mong đợi:** Có đủ cặp pause/resume timestamps để tính total duration.
- **Coverage hiện tại:** MISSING.

### TC-VIS-008-01 — Liệt kê lịch sử visit của BN (sort desc)
- **Function:** VIS-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** BN có ≥2 visit; perm `visit.read`.
- **Bước thực hiện:** 1) `GET /visits?patient_id=...`.
- **Dữ liệu test:** patient có nhiều visit.
- **Kết quả mong đợi:** HTTP 200; PaginatedResponse; sort `created_at` desc; mỗi item có date/doctor/diagnosis/status.
- **Coverage hiện tại:** MISSING.

### TC-VIS-008-02 — Lấy visit detail
- **Function:** VIS-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit tồn tại.
- **Bước thực hiện:** 1) `GET /visits/{id}`.
- **Dữ liệu test:** visit_id hợp lệ.
- **Kết quả mong đợi:** HTTP 200; VisitDetailResponse đầy đủ.
- **Coverage hiện tại:** MISSING.

### TC-VIS-008-03 — Phân trang & filter status/doctor
- **Function:** VIS-008
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Nhiều visit đa trạng thái.
- **Bước thực hiện:** 1) `GET /visits?status=COMPLETED&doctor_id=...&page=1&page_size=20`.
- **Dữ liệu test:** page_size hợp lệ (1..100).
- **Kết quả mong đợi:** HTTP 200; chỉ visit COMPLETED của doctor đó; tôn trọng page_size; page_size>100 → 422.
- **Coverage hiện tại:** MISSING.

### TC-VIS-009-01 — Gán bác sĩ khi tạo visit
- **Function:** VIS-009
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Doctor available.
- **Bước thực hiện:** 1) `POST /visits` kèm doctor_id. 2) Đọc visit.
- **Dữ liệu test:** doctor_id hợp lệ.
- **Kết quả mong đợi:** HTTP 201; visit.doctor_id đúng; ghi audit assignment.
- **Coverage hiện tại:** MISSING.

### TC-VIS-009-02 — Tạo visit không chỉ định bác sĩ (bác sĩ trực)
- **Function:** VIS-009
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** -
- **Bước thực hiện:** 1) `POST /visits` không có doctor_id.
- **Dữ liệu test:** payload thiếu doctor_id (cho phép).
- **Kết quả mong đợi:** HTTP 201; visit chờ call-next gán doctor sau.
- **Coverage hiện tại:** MISSING.

### TC-VIS-010-01 — Reassign bác sĩ giữa visit
- **Function:** VIS-010
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User perm `visit.reassign`; visit chưa COMPLETED.
- **Bước thực hiện:** 1) `POST /visits/{id}/reassign` `{new_doctor_id, reason}`.
- **Dữ liệu test:** new_doctor_id hợp lệ.
- **Kết quả mong đợi:** HTTP 200; visit.doctor_id cập nhật; INSERT visit_event `reassigned`; notify new doctor.
- **Coverage hiện tại:** MISSING.

### TC-VIS-010-02 — Reassign thiếu quyền visit.reassign
- **Function:** VIS-010
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User chỉ có `visit.update`, KHÔNG có `visit.reassign`.
- **Bước thực hiện:** 1) `POST /visits/{id}/reassign`.
- **Dữ liệu test:** token thiếu perm.
- **Kết quả mong đợi:** HTTP 403.
- **Coverage hiện tại:** MISSING.

### TC-VIS-010-03 — Reassign visit đã COMPLETED
- **Function:** VIS-010
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit `COMPLETED`.
- **Bước thực hiện:** 1) `POST /visits/{id}/reassign`.
- **Dữ liệu test:** visit terminal.
- **Kết quả mong đợi:** HTTP 409 (không reassign visit đã đóng).
- **Coverage hiện tại:** MISSING.

### TC-VIS-011-01 — Cập nhật lý do khám
- **Function:** VIS-011
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit chưa COMPLETED; perm `visit.update`.
- **Bước thực hiện:** 1) `PATCH /visits/{id}` `{reason:"Sốt 38°C 2 ngày"}`.
- **Dữ liệu test:** reason ≤ 500 chars.
- **Kết quả mong đợi:** HTTP 200; visit.reason cập nhật.
- **Coverage hiện tại:** MISSING.

### TC-VIS-011-02 — Lý do vượt 500 ký tự
- **Function:** VIS-011
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** -
- **Bước thực hiện:** 1) `PATCH /visits/{id}` reason 501 ký tự.
- **Dữ liệu test:** chuỗi 501 ký tự.
- **Kết quả mong đợi:** HTTP 422 (giới hạn 500).
- **Coverage hiện tại:** MISSING.

### TC-VIS-012-01 — Call-next lấy visit kế tiếp
- **Function:** VIS-012
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Có visit `VITAL_DONE` trong queue; user perm `visit.consult`.
- **Bước thực hiện:** 1) `POST /visits/call-next`.
- **Dữ liệu test:** queue có ≥1 visit chờ.
- **Kết quả mong đợi:** HTTP 200; visit gán doctor hiện tại; `status=IN_CONSULTATION`.
- **Coverage hiện tại:** MISSING.

### TC-VIS-012-02 — Hai doctor gọi call-next đồng thời (SKIP LOCKED)
- **Function:** VIS-012
- **Loại:** Edge (concurrency)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** ≥2 visit chờ; 2 phiên doctor.
- **Bước thực hiện:** 1) Gọi `call-next` đồng thời từ 2 doctor.
- **Dữ liệu test:** 2 visit khác nhau trong queue.
- **Kết quả mong đợi:** 2 visit KHÁC NHAU được trả; không race; không lỗi (SELECT FOR UPDATE SKIP LOCKED).
- **Coverage hiện tại:** MISSING (logic concurrency chưa có test).

### TC-VIS-012-03 — Call-next khi queue rỗng
- **Function:** VIS-012
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không có visit chờ.
- **Bước thực hiện:** 1) `POST /visits/call-next`.
- **Dữ liệu test:** queue rỗng.
- **Kết quả mong đợi:** HTTP 404/204 (không có visit để gọi).
- **Coverage hiện tại:** MISSING.

### TC-VIS-013-01 — Hoàn tất visit tạo draft invoice + route Rx
- **Function:** VIS-013
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit `IN_CONSULTATION` có services + medicines internal; user là doctor.
- **Bước thực hiện:** 1) `PATCH .../status` `{status:"COMPLETED"}`. 2) Kiểm invoice + pharmacy queue.
- **Dữ liệu test:** visit có dịch vụ + đơn thuốc.
- **Kết quả mong đợi:** HTTP 200; `status=COMPLETED`, `completed_at` set; tạo draft invoice với services+medicines; route Rx internal sang pharmacy; notify pharmacist+cashier. Atomic (rollback nếu 1 bước fail).
- **Coverage hiện tại:** MISSING.

### TC-VIS-013-02 — Visit COMPLETED không thể edit
- **Function:** VIS-013
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit `COMPLETED`; user thường (không `visit.reopen`).
- **Bước thực hiện:** 1) `PATCH /visits/{id}` đổi reason. 2) `PATCH .../status` đổi state.
- **Dữ liệu test:** visit terminal.
- **Kết quả mong đợi:** HTTP 409 (immutable sau COMPLETED).
- **Coverage hiện tại:** PARTIAL (terminal state cover unit; HTTP guard cần e2e).

### TC-VIS-013-03 — Admin reopen visit với quyền visit.reopen
- **Function:** VIS-013
- **Loại:** Edge / Security
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Admin có perm `visit.reopen`; visit `COMPLETED`.
- **Bước thực hiện:** 1) Reopen visit.
- **Dữ liệu test:** token admin có perm.
- **Kết quả mong đợi:** HTTP 200; visit chuyển khỏi COMPLETED; ghi audit reopen. (Nếu chưa ship endpoint reopen → ghi nhận gap.)
- **Coverage hiện tại:** MISSING.

### TC-VIS-014-01 — Upload tài liệu đính kèm visit
- **Function:** VIS-014
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** S3 storage wired (TASK-007 Phase). User là doctor.
- **Bước thực hiện:** 1) Request presigned URL. 2) Upload file. 3) Liên kết vào visit với type.
- **Dữ liệu test:** file lab_result PDF; type ∈ {lab_result,xray,ct_scan,mri,ekg,other}.
- **Kết quả mong đợi:** HTTP 201; document gắn visit; preview inline.
- **Coverage hiện tại:** MISSING (VIS-014 TODO — storage chưa ship; chỉ placeholder).

### TC-VIS-014-02 — Upload type không hợp lệ
- **Function:** VIS-014
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Như trên.
- **Bước thực hiện:** 1) Liên kết document type không nằm trong enum.
- **Dữ liệu test:** type="virus".
- **Kết quả mong đợi:** HTTP 422.
- **Coverage hiện tại:** MISSING (TODO).

### TC-VIS-SEC-01 — Truy cập endpoint visit khi chưa auth (401)
- **Function:** (group VISIT — toàn bộ endpoint)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi JWT.
- **Bước thực hiện:** 1) Gọi lần lượt `POST /visits`, `GET /visits`, `GET /visits/{id}`, `POST /visits/call-next`, `PATCH /visits/{id}/status`, `POST /visits/{id}/reassign`, `GET /visits/{id}/events`, `PATCH /visits/{id}` không header Authorization.
- **Dữ liệu test:** request không token.
- **Kết quả mong đợi:** Tất cả trả HTTP 401.
- **Coverage hiện tại:** MISSING.

### TC-VIS-SEC-02 — Truy cập với token thiếu permission (403)
- **Function:** (group VISIT — kiểm `require_permission`)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token role tối thiểu, không có perm visit.*.
- **Bước thực hiện:** 1) Gọi mỗi endpoint với token thiếu perm tương ứng (create/read/consult/update/reassign).
- **Dữ liệu test:** token role thiếu.
- **Kết quả mong đợi:** Tất cả trả HTTP 403.
- **Coverage hiện tại:** MISSING.

### TC-VIS-RLS-01 — Cô lập visit theo clinic (RLS)
- **Function:** (group VISIT — RLS theo clinic_id)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 clinic A & B, mỗi clinic có visit riêng; RLS policy bật.
- **Bước thực hiện:** 1) User clinic A `GET /visits` → chỉ thấy visit A. 2) User clinic A `GET /visits/{id_của_B}`. 3) User A thử `PATCH .../status` trên visit B.
- **Dữ liệu test:** visit_id thuộc clinic B.
- **Kết quả mong đợi:** Bước1 không có visit B; Bước2 → 404 (RLS ẩn); Bước3 → 404/403; không rò rỉ cross-tenant.
- **Coverage hiện tại:** PARTIAL (mẫu RLS có tại `tests/integration/test_rls_isolation.py` cho module khác; chưa có case cụ thể cho visit).

---

## 3. Khoảng trống & rủi ro chính (gap analysis)

- **Toàn bộ tầng API visit chưa có integration/e2e test** — chỉ unit cho state_machine (5 test) + visit_number. Mọi endpoint (`create`, `list`, `call-next`, `status`, `reassign`, `events`, `update`) đang MISSING ở mức HTTP.
- **VIS-012 concurrency (SKIP LOCKED)** và **VIS-002 race-safe số** là rủi ro cao nhất (mất tiền/sai số/race) nhưng chưa có test concurrency.
- **VIS-013 auto-trigger** (draft invoice + route Rx, atomic) là điểm tích hợp tiền/kho/đơn thuốc — bắt buộc integration test rollback.
- **VIS-014** TODO do storage chưa wire → để MISSING, cần re-test khi S3 sẵn sàng.
- Guard quyền theo vai trong state machine (chỉ doctor được COMPLETED) chưa có test e2e.
