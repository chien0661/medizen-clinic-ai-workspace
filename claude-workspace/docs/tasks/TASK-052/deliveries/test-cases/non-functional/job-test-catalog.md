# Test Case Catalog — JOB · Tác vụ nền (Background Jobs / Arq)

**Nguồn:** function_list_data.py (group JOB) + clinic_management_function_list.md (mục 21 — "JOB — Background Jobs (Arq)") + system_design/SaaS.
**Phạm vi:** 14 functions (JOB-001 … JOB-014).  **Tổng test case:** 32.  **Ngày:** 2026-05-30.

> **Bối cảnh kiến trúc (rút từ nguồn):** Các JOB chạy bằng **Arq** (Redis-backed async task queue) trong worker riêng, không phải HTTP endpoint. Phần lớn là **cron** (định kỳ) hoặc **async task** kích hoạt theo sự kiện. Vì chạy ở tầng System, kiểm thử chủ yếu ở **Layer Integration (real DB + Redis)** bằng cách gọi trực tiếp hàm job; không có request người dùng nên **không áp dụng case 401/403 cấp endpoint** — thay vào đó nhấn mạnh **idempotency**, **deduplicate**, và **cô lập tenant theo clinic (RLS)** vì job quét toàn bộ clinic.
>
> **Quy ước RLS cho job đa-tenant:** Các job lifecycle subscription (JOB-001/002/003/004/005) thao tác ở phạm vi **platform** trên bảng `clinic` (theo `clinic.status`, `current_period_end`, `grace_started_at`, `archived_at`) — không bị giới hạn RLS clinic, nhưng mọi thông báo/email sinh ra phải gắn đúng `clinic_id`. Các job domain (JOB-006 shift, JOB-007 stock, JOB-008 expiry, JOB-009 no-show, JOB-013 birthday) **phải lặp theo từng clinic và set RLS GUC** `app.current_clinic_id` trước truy vấn, không rò rỉ dữ liệu chéo clinic.
>
> **Coverage:** Repo `clinic-cms-merge/app` và thư mục `app/` + `tests/` **không truy cập được** từ phiên soạn này → coverage được **suy ra từ cột status nguồn**:
> - `DONE`: JOB-006 (TASK-014), JOB-010 (TASK-004) → đánh giá **PARTIAL — cần xác minh test file** (đã hiện thực nhưng chưa kiểm chứng được test tự động cho nhánh job).
> - `TODO` (TASK-028): JOB-001..005, 007, 008, 009, 011 → **MISSING**.
> - `IDEA` (v2/v3, chưa lên kế hoạch): JOB-012, JOB-013, JOB-014 → **MISSING** (chưa hiện thực).

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| JOB-001 | Subscription expiration check (cron mỗi giờ) | TODO | TC-JOB-001, TC-JOB-001b, TC-JOB-001c | MISSING |
| JOB-002 | Grace transition (active → grace) | TODO | TC-JOB-002, TC-JOB-002b | MISSING |
| JOB-003 | Expired transition (grace → expired) | TODO | TC-JOB-003, TC-JOB-003b | MISSING |
| JOB-004 | Reminder dispatch (D-14/-7/-3/-1/0 + grace daily) | TODO | TC-JOB-004, TC-JOB-004b, TC-JOB-004c | MISSING |
| JOB-005 | Hard delete archived (90 ngày sau archive) | TODO | TC-JOB-005, TC-JOB-005b | MISSING |
| JOB-006 | Recurring shift generation | DONE | TC-JOB-006, TC-JOB-006b, TC-JOB-006c | PARTIAL |
| JOB-007 | Stock alert generation (daily, min_stock) | TODO | TC-JOB-007, TC-JOB-007b | MISSING |
| JOB-008 | Expiry alert generation (30/60/90 ngày) | TODO | TC-JOB-008, TC-JOB-008b | MISSING |
| JOB-009 | NO_SHOW marker (30p sau giờ hẹn) | TODO | TC-JOB-009, TC-JOB-009b, TC-JOB-009c | MISSING |
| JOB-010 | Refresh permission cache (async, RBAC-007) | DONE | TC-JOB-010, TC-JOB-010b | PARTIAL |
| JOB-011 | Daily backup (pg_dump → S3) | TODO | TC-JOB-011, TC-JOB-011b, TC-JOB-011c | MISSING |
| JOB-012 | Weekly report email | IDEA (v2) | TC-JOB-012 | MISSING |
| JOB-013 | Patient birthday SMS | IDEA (v3) | TC-JOB-013, TC-JOB-013b | MISSING |
| JOB-014 | Audit log retention (archive → xoá > 365d) | IDEA (v2) | TC-JOB-014, TC-JOB-014b | MISSING |

## 2. Chi tiết Test Cases

### TC-JOB-001 — Quét hết hạn: chuyển clinic active → grace (happy path)
- **Function:** JOB-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB + Redis)
- **Tiền điều kiện:** Có clinic `status='active'` với `current_period_end < now()`.
- **Bước thực hiện:** 1) Seed clinic hết hạn. 2) Chạy job `subscription_expiration_check`. 3) Đọc lại trạng thái clinic + bảng `subscription_event`.
- **Dữ liệu test:** clinic A: current_period_end = now() − 1h, status='active'.
- **Kết quả mong đợi:** clinic A → `status='grace'`, `grace_started_at` được set; INSERT 1 `subscription_event` 'grace_started'.
- **Coverage hiện tại:** MISSING — JOB-001 status=TODO (TASK-028); cần xác minh test file khi hiện thực.

### TC-JOB-001b — Idempotent: chạy lại không chuyển trạng thái lần nữa (edge)
- **Function:** JOB-001
- **Loại:** Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB + Redis)
- **Tiền điều kiện:** clinic đã ở `status='grace'` từ lần chạy trước.
- **Bước thực hiện:** 1) Chạy job lần 1 (chuyển grace). 2) Chạy job lần 2 ngay sau. 3) Đếm số `subscription_event`.
- **Dữ liệu test:** cùng clinic A.
- **Kết quả mong đợi:** Lần 2 không đổi trạng thái, không tạo event trùng (idempotent qua status check như mô tả nguồn).
- **Coverage hiện tại:** MISSING.

### TC-JOB-001c — Không chuyển clinic còn hạn (negative)
- **Function:** JOB-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic `status='active'`, `current_period_end > now()`.
- **Bước thực hiện:** Chạy job; kiểm tra clinic.
- **Dữ liệu test:** current_period_end = now() + 5 ngày.
- **Kết quả mong đợi:** clinic giữ `active`; không tạo event.
- **Coverage hiện tại:** MISSING.

### TC-JOB-002 — Grace transition kích hoạt reminder + banner (happy path)
- **Function:** JOB-002
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB + Redis)
- **Tiền điều kiện:** clinic vừa được JOB-001 chuyển sang grace.
- **Bước thực hiện:** 1) Trigger nhánh grace (trong JOB-001). 2) Kiểm tra event + email reminder + cờ banner activation.
- **Dữ liệu test:** clinic A vào grace.
- **Kết quả mong đợi:** `clinic.status='grace'`; INSERT event 'grace_started'; email reminder được đẩy hàng đợi; banner activation bật cho clinic A.
- **Coverage hiện tại:** MISSING — JOB-002 status=TODO; cần xác minh test file.

### TC-JOB-002b — Email/banner gắn đúng clinic_id (security/RLS)
- **Function:** JOB-002
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 clinic cùng vào grace.
- **Bước thực hiện:** Chạy nhánh grace; đối chiếu người nhận email + banner.
- **Dữ liệu test:** clinic A & B.
- **Kết quả mong đợi:** Mỗi email/banner gắn đúng `clinic_id`; không gửi nhắc của A tới admin của B.
- **Coverage hiện tại:** MISSING.

### TC-JOB-003 — Expired transition: grace → expired sau N ngày (happy path)
- **Function:** JOB-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic `status='grace'`, `grace_started_at + grace_period_days < now()`.
- **Bước thực hiện:** 1) Seed clinic quá grace. 2) Chạy job. 3) Kiểm tra trạng thái + event + cờ chặn POST.
- **Dữ liệu test:** grace_period_days=7, grace_started_at = now() − 8 ngày.
- **Kết quả mong đợi:** clinic → `status='expired'`; INSERT event 'expired'; banner đỏ bật; ghi/đặt cờ block thao tác POST.
- **Coverage hiện tại:** MISSING — JOB-003 status=TODO; cần xác minh test file.

### TC-JOB-003b — Không expire clinic còn trong grace (edge biên)
- **Function:** JOB-003
- **Loại:** Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic grace, `grace_started_at + grace_period_days >= now()`.
- **Bước thực hiện:** Chạy job tại mốc biên (đúng = chưa quá).
- **Dữ liệu test:** grace_period_days=7, grace_started_at = now() − 7 ngày (đúng ngưỡng).
- **Kết quả mong đợi:** clinic vẫn `grace`; quy tắc biên rõ (chỉ expire khi < now()); không expire sớm.
- **Coverage hiện tại:** MISSING.

### TC-JOB-004 — Reminder dispatch đúng lịch D-14/-7/-3/-1/0 (happy path)
- **Function:** JOB-004
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB + Redis)
- **Tiền điều kiện:** Cron daily 8h; clinic có `expires_at − now()` rơi đúng mốc nhắc.
- **Bước thực hiện:** 1) Seed clinic với expires_at = now() + 7 ngày. 2) Chạy job. 3) Kiểm tra email + in-app notification.
- **Dữ liệu test:** clinic ở mốc D-7.
- **Kết quả mong đợi:** Gửi 1 email + tạo 1 in-app notification cho clinic ở mốc D-7; clinic không khớp mốc không bị nhắc.
- **Coverage hiện tại:** MISSING — JOB-004 status=TODO; cần xác minh test file.

### TC-JOB-004b — Deduplicate qua sent_at: không nhắc trùng trong ngày (edge)
- **Function:** JOB-004
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic đã được nhắc mốc D-7 hôm nay (`sent_at` set).
- **Bước thực hiện:** Chạy job lần 2 cùng ngày.
- **Dữ liệu test:** sent_at = hôm nay.
- **Kết quả mong đợi:** Không gửi lại (deduplicate qua sent_at như mô tả nguồn).
- **Coverage hiện tại:** MISSING.

### TC-JOB-004c — Nhắc grace daily đúng từng clinic (security/RLS)
- **Function:** JOB-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Nhiều clinic ở grace cần nhắc daily.
- **Bước thực hiện:** Chạy job; đối chiếu người nhận từng clinic.
- **Dữ liệu test:** clinic A & B đều grace.
- **Kết quả mong đợi:** Mỗi clinic nhận nhắc của chính mình, email/notification gắn đúng `clinic_id`; không chéo.
- **Coverage hiện tại:** MISSING.

### TC-JOB-005 — Hard delete clinic archived quá 90 ngày + audit snapshot (happy path)
- **Function:** JOB-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic có `archived_at + 90d < now()`.
- **Bước thực hiện:** 1) Seed clinic archived cũ. 2) Chạy job. 3) Kiểm tra dữ liệu CASCADE bị xoá + audit 'hard_deleted'.
- **Dữ liệu test:** archived_at = now() − 91 ngày.
- **Kết quả mong đợi:** clinic bị DELETE CASCADE; ghi audit cuối 'hard_deleted' kèm snapshot trước khi xoá.
- **Coverage hiện tại:** MISSING — JOB-005 status=TODO; cần xác minh test file.

### TC-JOB-005b — Không xoá clinic archived chưa đủ 90 ngày (negative)
- **Function:** JOB-005
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic archived < 90 ngày.
- **Bước thực hiện:** Chạy job; kiểm tra clinic còn tồn tại.
- **Dữ liệu test:** archived_at = now() − 30 ngày.
- **Kết quả mong đợi:** Không xoá; dữ liệu giữ nguyên (tránh mất dữ liệu sớm — đặc biệt nguy hiểm vì CASCADE).
- **Coverage hiện tại:** MISSING.

### TC-JOB-006 — Sinh shift cho ngày mai từ recurring template (happy path)
- **Function:** JOB-006
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có `recurring_schedule` cho clinic; cron daily 23:00.
- **Bước thực hiện:** 1) Seed template cho thứ tương ứng ngày mai. 2) Chạy job. 3) Kiểm tra shift ngày mai.
- **Dữ liệu test:** template thứ tương ứng ngày mai.
- **Kết quả mong đợi:** Sinh đúng shift cho ngày mai theo template.
- **Coverage hiện tại:** PARTIAL — JOB-006 status=DONE (TASK-014), đã hiện thực nhưng **cần xác minh test file** (không truy cập được tests trong phiên này).

### TC-JOB-006b — Skip khi đã có shift manual cho ngày mai (edge)
- **Function:** JOB-006
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã tồn tại shift tạo thủ công cho ngày mai.
- **Bước thực hiện:** Chạy job; kiểm tra không ghi đè/không trùng.
- **Dữ liệu test:** shift manual sẵn có.
- **Kết quả mong đợi:** Bỏ qua sinh tự động cho ca đã có manual (như mô tả nguồn "Skip nếu đã có shift manual").
- **Coverage hiện tại:** PARTIAL — cần xác minh test file.

### TC-JOB-006c — Sinh shift cô lập theo clinic (security/RLS)
- **Function:** JOB-006
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 clinic có template riêng.
- **Bước thực hiện:** Chạy job theo từng clinic (set RLS GUC); đối chiếu shift sinh ra.
- **Dữ liệu test:** clinic A & B.
- **Kết quả mong đợi:** Shift mỗi clinic chỉ từ template của clinic đó; không tạo chéo.
- **Coverage hiện tại:** PARTIAL — cần xác minh test file (đặc biệt nhánh RLS).

### TC-JOB-007 — Cảnh báo tồn kho dưới min_stock (happy path)
- **Function:** JOB-007
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có medicine với `current_stock < min_stock`; cron daily.
- **Bước thực hiện:** 1) Seed thuốc tồn thấp. 2) Chạy job. 3) Kiểm tra notification cho pharmacist + admin clinic.
- **Dữ liệu test:** current_stock=2, min_stock=5.
- **Kết quả mong đợi:** Tạo notification gửi pharmacist + admin của clinic chứa thuốc.
- **Coverage hiện tại:** MISSING — JOB-007 status=TODO; cần xác minh test file.

### TC-JOB-007b — Cảnh báo tồn kho cô lập theo clinic (security/RLS)
- **Function:** JOB-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc tồn thấp ở clinic A, đủ ở clinic B.
- **Bước thực hiện:** Chạy job; đối chiếu notification.
- **Dữ liệu test:** clinic A thấp, clinic B đủ.
- **Kết quả mong đợi:** Chỉ pharmacist/admin clinic A nhận; không trộn kho/notification chéo clinic.
- **Coverage hiện tại:** MISSING.

### TC-JOB-008 — Cảnh báo lô cận hạn 30/60/90 ngày (happy path)
- **Function:** JOB-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có lot với expiry rơi vào mốc 30/60/90 ngày; cron daily.
- **Bước thực hiện:** 1) Seed lô HSD trong 30 ngày. 2) Chạy job. 3) Kiểm tra notification + badge UI.
- **Dữ liệu test:** lot expiry = now() + 30 ngày.
- **Kết quả mong đợi:** Tạo notification cận hạn + cập nhật badge UI cho clinic chứa lô.
- **Coverage hiện tại:** MISSING — JOB-008 status=TODO; cần xác minh test file.

### TC-JOB-008b — Không cảnh báo lô ngoài ngưỡng & cô lập clinic (negative/RLS)
- **Function:** JOB-008
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lô HSD còn 120 ngày (ngoài mốc) ở clinic A; lô cận hạn ở clinic B.
- **Bước thực hiện:** Chạy job.
- **Dữ liệu test:** lô A 120 ngày, lô B 30 ngày.
- **Kết quả mong đợi:** Không cảnh báo lô A; chỉ clinic B nhận; không rò rỉ chéo.
- **Coverage hiện tại:** MISSING.

### TC-JOB-009 — Đánh dấu NO_SHOW sau 30 phút chưa check-in (happy path)
- **Function:** JOB-009
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB + Redis)
- **Tiền điều kiện:** Appointment `status='SCHEDULED'`, `start_time + 30p < now()`; cron mỗi 5 phút.
- **Bước thực hiện:** 1) Seed appointment quá 30p chưa check-in. 2) Chạy job. 3) Kiểm tra trạng thái.
- **Dữ liệu test:** start_time = now() − 31 phút, status=SCHEDULED.
- **Kết quả mong đợi:** Appointment → `status='NO_SHOW'`.
- **Coverage hiện tại:** MISSING — JOB-009 status=TODO; cần xác minh test file.

### TC-JOB-009b — Không đánh dấu khi chưa quá 30p hoặc đã check-in (negative/edge)
- **Function:** JOB-009
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Appointment mới quá 10p, hoặc đã `CHECKED_IN`.
- **Bước thực hiện:** Chạy job.
- **Dữ liệu test:** (a) start_time = now() − 10p SCHEDULED; (b) status=CHECKED_IN.
- **Kết quả mong đợi:** Cả hai giữ nguyên; không bị NO_SHOW oan.
- **Coverage hiện tại:** MISSING.

### TC-JOB-009c — NO_SHOW cô lập theo clinic (security/RLS)
- **Function:** JOB-009
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Appointment quá hạn ở 2 clinic.
- **Bước thực hiện:** Chạy job; đối chiếu cập nhật.
- **Dữ liệu test:** clinic A & B.
- **Kết quả mong đợi:** Mỗi clinic chỉ cập nhật appointment của mình; set RLS GUC theo từng clinic; không sửa chéo.
- **Coverage hiện tại:** MISSING.

### TC-JOB-010 — Refresh permission cache khi role/perm đổi (happy path)
- **Function:** JOB-010
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB + Redis)
- **Tiền điều kiện:** Async task (RBAC-007) trigger khi role/permission thay đổi.
- **Bước thực hiện:** 1) Đổi quyền của role. 2) Enqueue/chạy task refresh cache. 3) Kiểm tra cache permission đã cập nhật.
- **Dữ liệu test:** thêm 1 permission cho role.
- **Kết quả mong đợi:** Cache permission của các user thuộc role được làm mới, phản ánh quyền mới.
- **Coverage hiện tại:** PARTIAL — JOB-010 status=DONE (TASK-004, RBAC-007), đã hiện thực nhưng **cần xác minh test file**.

### TC-JOB-010b — Cache cũ bị invalidate, không còn quyền đã thu hồi (security)
- **Function:** JOB-010
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB + Redis)
- **Tiền điều kiện:** Đã thu hồi 1 permission của role.
- **Bước thực hiện:** Thu hồi quyền → chạy refresh → kiểm tra check-permission.
- **Dữ liệu test:** revoke 1 permission.
- **Kết quả mong đợi:** User không còn vượt quyền với permission đã thu hồi; cache cũ không cho qua.
- **Coverage hiện tại:** PARTIAL — cần xác minh test file.

### TC-JOB-011 — Daily backup: pg_dump full → S3 mã hoá (happy path)
- **Function:** JOB-011
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + Manual (xác minh S3)
- **Tiền điều kiện:** Cron daily 2:00; cấu hình S3 + encryption (mock/localstack).
- **Bước thực hiện:** 1) Chạy job backup. 2) Kiểm tra artifact upload S3 + metadata + mã hoá.
- **Dữ liệu test:** DB có dữ liệu mẫu.
- **Kết quả mong đợi:** Tạo dump full, upload S3 với encryption thành công; metadata ghi nhận.
- **Coverage hiện tại:** MISSING — JOB-011 status=TODO; cần xác minh test file.

### TC-JOB-011b — Retention 30 ngày: xoay vòng bản backup cũ (edge)
- **Function:** JOB-011
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (mock S3)
- **Tiền điều kiện:** Có > 30 bản backup.
- **Bước thực hiện:** Chạy job nhiều lần vượt 30; kiểm tra danh sách bản giữ.
- **Dữ liệu test:** 31 bản.
- **Kết quả mong đợi:** Giữ đúng 30 bản gần nhất; bản cũ hơn 30 ngày bị xoá (retention).
- **Coverage hiện tại:** MISSING.

### TC-JOB-011c — Backup thất bại được notify (negative)
- **Function:** JOB-011
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (mock S3 lỗi)
- **Tiền điều kiện:** S3 không ghi được (lỗi quyền/mạng).
- **Bước thực hiện:** Chạy job với đích lỗi.
- **Dữ liệu test:** S3 endpoint lỗi.
- **Kết quả mong đợi:** Job báo fail, gửi notify (như mô tả "Notify nếu fail"); không đánh dấu success giả.
- **Coverage hiện tại:** MISSING.

### TC-JOB-012 — Weekly report email gửi admin clinic (happy path)
- **Function:** JOB-012
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Phase 2; cron T2 8h; có dữ liệu tuần (doanh thu, visit, top service, alerts).
- **Bước thực hiện:** 1) Seed dữ liệu tuần cho clinic. 2) Chạy job. 3) Kiểm tra email summary.
- **Dữ liệu test:** 1 tuần dữ liệu clinic A.
- **Kết quả mong đợi:** Gửi summary tuần (doanh thu, visit count, top service, alerts) tới đúng admin clinic A; nội dung cô lập theo clinic.
- **Coverage hiện tại:** MISSING — JOB-012 status=IDEA (v2), chưa hiện thực.

### TC-JOB-013 — Birthday SMS + voucher cho bệnh nhân sinh nhật hôm nay (happy path)
- **Function:** JOB-013
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Phase 3; cron daily; patient có `dob` = today (bỏ qua năm).
- **Bước thực hiện:** 1) Seed bệnh nhân sinh nhật hôm nay. 2) Chạy job. 3) Kiểm tra SMS + voucher.
- **Dữ liệu test:** dob ngày-tháng = hôm nay.
- **Kết quả mong đợi:** Gửi SMS chúc mừng kèm voucher khám miễn phí; so khớp ngày-tháng (không so năm).
- **Coverage hiện tại:** MISSING — JOB-013 status=IDEA (v3), chưa hiện thực.

### TC-JOB-013b — Birthday SMS cô lập theo clinic (security/RLS)
- **Function:** JOB-013
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Bệnh nhân sinh nhật hôm nay ở 2 clinic.
- **Bước thực hiện:** Chạy job; đối chiếu người nhận.
- **Dữ liệu test:** clinic A & B.
- **Kết quả mong đợi:** SMS dùng đúng voucher/cấu hình của clinic bệnh nhân; không gửi voucher clinic A cho bệnh nhân clinic B.
- **Coverage hiện tại:** MISSING.

### TC-JOB-014 — Audit log retention: archive S3 rồi xoá > 365 ngày (happy path)
- **Function:** JOB-014
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB + mock S3)
- **Tiền điều kiện:** Phase 2; cron monthly; có `audit_log` cũ hơn 365 ngày (config).
- **Bước thực hiện:** 1) Seed audit cũ + mới. 2) Chạy job. 3) Kiểm tra archive S3 + xoá bản nóng cũ.
- **Dữ liệu test:** audit 400 ngày trước + audit 100 ngày trước.
- **Kết quả mong đợi:** Audit > 365 ngày được archive S3 trước, sau đó xoá khỏi DB; audit mới giữ nguyên (giảm DB size).
- **Coverage hiện tại:** MISSING — JOB-014 status=IDEA (v2), chưa hiện thực.

### TC-JOB-014b — Không xoá khi archive thất bại (negative — bảo toàn dữ liệu)
- **Function:** JOB-014
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (mock S3 lỗi)
- **Tiền điều kiện:** Archive S3 lỗi.
- **Bước thực hiện:** Chạy job với S3 lỗi.
- **Dữ liệu test:** audit cũ + S3 down.
- **Kết quả mong đợi:** KHÔNG xoá audit khỏi DB khi archive chưa thành công (tránh mất audit vĩnh viễn); báo lỗi để retry.
- **Coverage hiện tại:** MISSING.
