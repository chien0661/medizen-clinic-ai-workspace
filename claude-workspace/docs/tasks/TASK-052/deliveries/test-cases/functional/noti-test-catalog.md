# Test Case Catalog — NOTI · Thông báo

**Nguồn:** function_list_data.py (group NOTI, 15 dòng `f("NOTI", …)`) + clinic_management_function_list.md §17 (NOTI-001…NOTI-015) + clinic_management_system_design.md §16.1 (model Notification), §17 (API), §19.3 (Notification job) + đối chiếu repo `../clinic-cms-merge`.
**Phạm vi:** 15 functions (NOTI-001 … NOTI-015).  **Tổng test case:** 43.  **Ngày:** 2026-05-30.

> **Ghi chú nguồn & coverage (đọc trước):**
> - Theo function_list §17, **chỉ NOTI-013** (Tauri desktop notification, TASK-016) ở trạng thái ✅ DONE. Các function in-app (NOTI-001..006, TASK-015), email/cron (NOTI-007..009, NOTI-015, TASK-027/028) ở trạng thái ⬜ TODO. SMS/Zalo/Web-push/User-preference (NOTI-010..012, NOTI-014) ở trạng thái 💡 IDEA (Phase v2/v3).
> - Repo backend main-worktree `../clinic-cms-merge` tại thời điểm soạn **không grep ra module `notifications`** (worktree đang ở nhánh khác / chưa checkout module này) → không xác nhận được endpoint/permission đã ship. Vì vậy Coverage gán **MISSING** cho toàn bộ backend NOTI, **PARTIAL** cho NOTI-013 (đã có phần Tauri FE qua TASK-016 nhưng chưa thấy test backend tương ứng).
> - API tham chiếu trong system_design §17: `GET /api/v1/notifications?unread_only=true`, `POST /api/v1/notifications/{id}/read`, `POST /api/v1/notifications/mark-all-read`. Model `Notification(BaseEntity)` bảng `notification` (§16.1, migration `0013_create_notifications.py`). Notification job (§19.3) tạo notif cho pharmacist & admin. Scheduler (§19.x) `cron(appointment_reminders, minute=0)` chạy mỗi giờ (T-24h, T-2h).
> - Mọi entity NOTI mang `clinic_id` → RLS theo `app.current_clinic_id` (PROJECT.md §Multi-tenancy). Các TC chạm dữ liệu domain đều có case cô lập clinic.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| NOTI-001 | In-app notification (bell icon + dropdown) | ⬜ TODO (TASK-015) | TC-NOTI-001, TC-NOTI-002, TC-NOTI-003, TC-NOTI-004 | MISSING |
| NOTI-002 | Mark as read | ⬜ TODO (TASK-015) | TC-NOTI-005, TC-NOTI-006, TC-NOTI-007 | MISSING |
| NOTI-003 | Mark all as read (bulk) | ⬜ TODO (TASK-015) | TC-NOTI-008, TC-NOTI-009 | MISSING |
| NOTI-004 | Notification categories (Info/Warning/Critical/Success) | ⬜ TODO (TASK-015) | TC-NOTI-010, TC-NOTI-011 | MISSING |
| NOTI-005 | Visit completion notify → cashier | ⬜ TODO (TASK-015) | TC-NOTI-012, TC-NOTI-013 | MISSING |
| NOTI-006 | Stock low alert → pharmacist | ⬜ TODO (TASK-015) | TC-NOTI-014, TC-NOTI-015, TC-NOTI-016 | MISSING |
| NOTI-007 | Subscription expiring → clinic admin | ⬜ TODO (TASK-028) | TC-NOTI-017, TC-NOTI-018 | MISSING |
| NOTI-008 | Email transactional (verify/reset/reminder) | ⬜ TODO (TASK-027) | TC-NOTI-019, TC-NOTI-020, TC-NOTI-021 | MISSING |
| NOTI-009 | Email templates (Vi/En, brand-themed) | ⬜ TODO (TASK-027) | TC-NOTI-022, TC-NOTI-023, TC-NOTI-024 | MISSING |
| NOTI-010 | SMS notifications (appointment reminder, OTP) | 💡 IDEA v2 (TASK-027) | TC-NOTI-025, TC-NOTI-026, TC-NOTI-027 | MISSING |
| NOTI-011 | Zalo OA push (Phase 3) | 💡 IDEA v3 | TC-NOTI-028, TC-NOTI-029 | MISSING |
| NOTI-012 | Push notification (web, Browser Push API) | 💡 IDEA v2 | TC-NOTI-030, TC-NOTI-031 | MISSING |
| NOTI-013 | Tauri desktop notification (native OS) | ✅ DONE (TASK-016) | TC-NOTI-032, TC-NOTI-033, TC-NOTI-034 | PARTIAL |
| NOTI-014 | User preference (tắt theo loại notification) | 💡 IDEA v2 | TC-NOTI-035, TC-NOTI-036, TC-NOTI-037 | MISSING |
| NOTI-015 | Reminder schedule cron (daily cron gửi reminder) | ⬜ TODO (TASK-028) | TC-NOTI-038, TC-NOTI-039, TC-NOTI-040, TC-NOTI-041, TC-NOTI-042, TC-NOTI-043 | MISSING |

**Tổng kết coverage theo function:** COVERED 0 · PARTIAL 1 (NOTI-013) · MISSING 14.

---

## 2. Chi tiết Test Cases

### TC-NOTI-001 — Lấy danh sách thông báo in-app của chính user (phân trang)
- **Function:** NOTI-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User đã đăng nhập, có ≥ 25 notification trong clinic A.
- **Bước thực hiện:** 1) `GET /api/v1/notifications`. 2) `GET /api/v1/notifications?unread_only=true`.
- **Dữ liệu test:** 25 notification (15 chưa đọc).
- **Kết quả mong đợi:** HTTP 200; danh sách sắp xếp `created_at` DESC; field shape gồm `id, category, title, body, link, is_read, created_at`; `unread_only=true` chỉ trả 15 mục chưa đọc; chỉ trả notification của user hiện tại.
- **Coverage hiện tại:** MISSING

### TC-NOTI-002 — Danh sách thông báo yêu cầu xác thực (401)
- **Function:** NOTI-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi header Authorization.
- **Bước thực hiện:** 1) `GET /api/v1/notifications` không token.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401 Unauthorized.
- **Coverage hiện tại:** MISSING

### TC-NOTI-003 — User không xem được thông báo của user khác (cùng clinic)
- **Function:** NOTI-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** U1, U2 cùng clinic A; U2 có notification riêng.
- **Bước thực hiện:** 1) Đăng nhập U1, `GET /api/v1/notifications`.
- **Dữ liệu test:** notification recipient = U2.
- **Kết quả mong đợi:** HTTP 200; danh sách KHÔNG chứa notification của U2 (lọc theo recipient/user hiện tại).
- **Coverage hiện tại:** MISSING

### TC-NOTI-004 — Thông báo cô lập theo clinic (RLS)
- **Function:** NOTI-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Cùng 1 account thuộc clinic A và B; có notification ở clinic A.
- **Bước thực hiện:** 1) Set session `app.current_clinic_id = B`, truy vấn notification của A.
- **Dữ liệu test:** notification clinic_id = A.
- **Kết quả mong đợi:** Session clinic B KHÔNG thấy bản ghi (RLS chặn); chỉ context clinic A đọc được.
- **Coverage hiện tại:** MISSING

### TC-NOTI-005 — Đánh dấu một thông báo đã đọc
- **Function:** NOTI-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User có notification N (`is_read=false`).
- **Bước thực hiện:** 1) `POST /api/v1/notifications/{N}/read`. 2) Truy vấn DB.
- **Dữ liệu test:** N.is_read=false.
- **Kết quả mong đợi:** HTTP 200; `is_read=true` (+ `read_at` nếu có); số chưa đọc giảm 1.
- **Coverage hiện tại:** MISSING

### TC-NOTI-006 — Mark-as-read trên id không tồn tại (404)
- **Function:** NOTI-002
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User đã auth.
- **Bước thực hiện:** 1) `POST /api/v1/notifications/{uuid-ngẫu-nhiên}/read`.
- **Dữ liệu test:** id không tồn tại.
- **Kết quả mong đợi:** HTTP 404 Not Found.
- **Coverage hiện tại:** MISSING

### TC-NOTI-007 — Không mark-as-read được thông báo của user khác
- **Function:** NOTI-002
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** U1 đăng nhập; notification N thuộc U2.
- **Bước thực hiện:** 1) U1 `POST /api/v1/notifications/{N}/read`.
- **Dữ liệu test:** N.recipient = U2.
- **Kết quả mong đợi:** HTTP 404 (hoặc 403); N giữ nguyên `is_read=false`.
- **Coverage hiện tại:** MISSING

### TC-NOTI-008 — Đánh dấu tất cả đã đọc (bulk)
- **Function:** NOTI-003
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User có 4 notification chưa đọc.
- **Bước thực hiện:** 1) `POST /api/v1/notifications/mark-all-read`. 2) `GET /api/v1/notifications?unread_only=true`.
- **Dữ liệu test:** 4 unread.
- **Kết quả mong đợi:** HTTP 200; tất cả `is_read=true`; danh sách unread rỗng; chỉ ảnh hưởng notification của user hiện tại trong clinic hiện tại.
- **Coverage hiện tại:** MISSING

### TC-NOTI-009 — Mark-all-read không ảnh hưởng user/clinic khác (RLS + isolation)
- **Function:** NOTI-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** U1 và U2 (cùng clinic A) đều có unread; clinic B có unread.
- **Bước thực hiện:** 1) U1 `POST /api/v1/notifications/mark-all-read`. 2) Kiểm tra unread của U2 và của clinic B.
- **Dữ liệu test:** unread của U1, U2, clinic B.
- **Kết quả mong đợi:** Chỉ unread của U1 về 0; U2 và clinic B giữ nguyên.
- **Coverage hiện tại:** MISSING

### TC-NOTI-010 — Thông báo gắn đúng category (Info/Warning/Critical/Success)
- **Function:** NOTI-004
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hệ thống tạo 4 notification mỗi loại category.
- **Bước thực hiện:** 1) `GET /api/v1/notifications` và đọc field `category`.
- **Dữ liệu test:** category ∈ {info, warning, critical, success}.
- **Kết quả mong đợi:** HTTP 200; mỗi notification trả đúng `category` đã tạo; FE map đúng màu/icon.
- **Coverage hiện tại:** MISSING

### TC-NOTI-011 — Category không hợp lệ bị từ chối
- **Function:** NOTI-004
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Gọi hàm/schema tạo notification.
- **Bước thực hiện:** 1) Tạo notification với `category="purple"`.
- **Dữ liệu test:** category ngoài enum.
- **Kết quả mong đợi:** Lỗi validation (ValueError/422); không tạo bản ghi.
- **Coverage hiện tại:** MISSING

### TC-NOTI-012 — Hoàn tất visit phát sinh thông báo cho thu ngân
- **Function:** NOTI-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit ở trạng thái IN_CONSULTATION; có user role cashier/receptionist trong clinic.
- **Bước thực hiện:** 1) Chuyển visit → COMPLETED (trigger VIS-013). 2) Truy vấn notification của cashier.
- **Dữ liệu test:** 1 visit hoàn tất.
- **Kết quả mong đợi:** Tạo notification `category=info`, recipient = (các) cashier của clinic, link tới draft invoice; gắn đúng `clinic_id`.
- **Coverage hiện tại:** MISSING

### TC-NOTI-013 — Visit-completion notify không rò sang clinic khác (RLS)
- **Function:** NOTI-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B đều có cashier; visit hoàn tất ở clinic A.
- **Bước thực hiện:** 1) Hoàn tất visit clinic A. 2) Kiểm tra cashier clinic B.
- **Dữ liệu test:** visit clinic A.
- **Kết quả mong đợi:** Chỉ cashier clinic A nhận; cashier clinic B không có notification mới.
- **Coverage hiện tại:** MISSING

### TC-NOTI-014 — Tồn kho dưới min phát cảnh báo cho dược sĩ
- **Function:** NOTI-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc M có `min_stock`; sau khi cấp phát/điều chỉnh, tồn < min.
- **Bước thực hiện:** 1) Trigger giảm tồn kho M xuống dưới min (PHRM-006/MED-004). 2) Truy vấn notification của pharmacist & admin (Notification job §19.3).
- **Dữ liệu test:** M tồn = min - 1.
- **Kết quả mong đợi:** Tạo notification `category=warning` cho pharmacist + admin của clinic; nội dung nêu tên thuốc + số tồn.
- **Coverage hiện tại:** MISSING

### TC-NOTI-015 — Không phát cảnh báo trùng lặp khi tồn vẫn dưới min
- **Function:** NOTI-006
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có cảnh báo low-stock cho M trong ngày; tồn tiếp tục giảm nhưng vẫn dưới min.
- **Bước thực hiện:** 1) Lần cấp phát kế tiếp giảm tồn thêm. 2) Đếm notification low-stock của M.
- **Dữ liệu test:** M giảm 2 lần liên tiếp dưới min.
- **Kết quả mong đợi:** Không tạo notification trùng (khử trùng theo `medicine_id + ngày` hoặc tới khi tồn vượt min rồi lại tụt).
- **Coverage hiện tại:** MISSING

### TC-NOTI-016 — Tồn vượt lại trên min thì lần xuống dưới sau mới cảnh báo lại
- **Function:** NOTI-006
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** M từng dưới min → nhập kho lên trên min.
- **Bước thực hiện:** 1) Nhập kho M lên > min. 2) Cấp phát kéo tồn xuống < min lại.
- **Dữ liệu test:** chu kỳ tồn min→over→min.
- **Kết quả mong đợi:** Phát sinh notification low-stock mới (reset trạng thái cảnh báo).
- **Coverage hiện tại:** MISSING

### TC-NOTI-017 — Sắp hết hạn subscription gửi thông báo cho clinic admin
- **Function:** NOTI-007
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic có subscription hết hạn trong cửa sổ D-14/-7/-3/-1/0 (SUB-019).
- **Bước thực hiện:** 1) Chạy cron reminder subscription. 2) Truy vấn notification của clinic admin.
- **Dữ liệu test:** subscription expiry = today + 7.
- **Kết quả mong đợi:** Tạo in-app notification `category=warning/critical` + (nếu cấu hình) email cho admin clinic; nội dung nêu ngày hết hạn.
- **Coverage hiện tại:** MISSING

### TC-NOTI-018 — Subscription notify chỉ gửi đúng clinic (isolation)
- **Function:** NOTI-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A sắp hết hạn, clinic B còn hạn.
- **Bước thực hiện:** 1) Chạy cron. 2) Kiểm tra admin clinic B.
- **Dữ liệu test:** A expiring, B active.
- **Kết quả mong đợi:** Chỉ admin clinic A nhận; admin clinic B không có notification.
- **Coverage hiện tại:** MISSING

### TC-NOTI-019 — Gửi email transactional (verify/reset) thành công
- **Function:** NOTI-008
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, mock SMTP provider)
- **Tiền điều kiện:** Provider email được mock; user có email hợp lệ.
- **Bước thực hiện:** 1) Trigger gửi email verify (TENT-002) hoặc reset password (AUTH-009).
- **Dữ liệu test:** email hợp lệ + link token TTL 24h.
- **Kết quả mong đợi:** Provider được gọi đúng 1 lần với template + token; ghi nhận trạng thái gửi; không lộ token trong audit log (PII redaction).
- **Coverage hiện tại:** MISSING

### TC-NOTI-020 — Email đến địa chỉ không hợp lệ → fail có kiểm soát
- **Function:** NOTI-008
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Email rỗng/sai định dạng.
- **Bước thực hiện:** 1) Trigger gửi email.
- **Dữ liệu test:** email="abc@".
- **Kết quả mong đợi:** Không gọi provider; ghi log `failed` + lý do; không raise 500 phá luồng chính.
- **Coverage hiện tại:** MISSING

### TC-NOTI-021 — Provider email lỗi (5xx/timeout) được bắt và đưa vào retry
- **Function:** NOTI-008
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB, mock provider lỗi)
- **Tiền điều kiện:** Mock provider ném timeout.
- **Bước thực hiện:** 1) Trigger gửi email qua Arq job.
- **Dữ liệu test:** provider timeout.
- **Kết quả mong đợi:** Job đánh dấu thất bại + retry theo cấu hình Arq; không crash worker.
- **Coverage hiện tại:** MISSING

### TC-NOTI-022 — Render email template đa ngôn ngữ (vi/en)
- **Function:** NOTI-009
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Template verify có bản vi và en.
- **Bước thực hiện:** 1) Render với `locale=vi`. 2) Render với `locale=en`.
- **Dữ liệu test:** context `{user_name, clinic_name, link}`.
- **Kết quả mong đợi:** Nội dung đúng ngôn ngữ; placeholder được thay; brand (logo/tên clinic) chèn đúng.
- **Coverage hiện tại:** MISSING

### TC-NOTI-023 — Render template thiếu placeholder không vỡ
- **Function:** NOTI-009
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Template chứa `{appointment_time}` nhưng context thiếu key.
- **Bước thực hiện:** 1) Render thiếu key.
- **Dữ liệu test:** context thiếu `appointment_time`.
- **Kết quả mong đợi:** Xử lý an toàn (chuỗi rỗng hoặc lỗi rõ ràng, không 500/không lộ raw template).
- **Coverage hiện tại:** MISSING

### TC-NOTI-024 — Locale không hỗ trợ fallback về mặc định
- **Function:** NOTI-009
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Template có vi/en; yêu cầu `locale=fr`.
- **Bước thực hiện:** 1) Render với `locale=fr`.
- **Dữ liệu test:** locale ngoài danh sách.
- **Kết quả mong đợi:** Fallback về `vi` (default theo CFG-012) hoặc `en`; không lỗi.
- **Coverage hiện tại:** MISSING

### TC-NOTI-025 — Gửi SMS nhắc lịch hẹn thành công (v2)
- **Function:** NOTI-010
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB, mock SMS provider)
- **Tiền điều kiện:** Tính năng v2 bật; bệnh nhân có SĐT hợp lệ; provider SMS mock.
- **Bước thực hiện:** 1) Trigger SMS reminder cho appointment. 2) Kiểm tra log gửi.
- **Dữ liệu test:** SĐT VN hợp lệ.
- **Kết quả mong đợi:** Provider gọi 1 lần với nội dung render; log `status=sent`. (Khi tính năng chưa ship → đánh dấu skip/xfail.)
- **Coverage hiện tại:** MISSING

### TC-NOTI-026 — SMS tới SĐT không hợp lệ → fail
- **Function:** NOTI-010
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** SĐT sai định dạng.
- **Bước thực hiện:** 1) Trigger SMS.
- **Dữ liệu test:** SĐT="abc".
- **Kết quả mong đợi:** Không gọi provider; log `failed, error=invalid_recipient`.
- **Coverage hiện tại:** MISSING

### TC-NOTI-027 — SMS OTP có TTL và rate-limit
- **Function:** NOTI-010
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB + Redis)
- **Tiền điều kiện:** Luồng OTP qua SMS.
- **Bước thực hiện:** 1) Yêu cầu OTP nhiều lần liên tiếp. 2) Dùng OTP sau khi hết TTL.
- **Dữ liệu test:** spam request + OTP quá hạn.
- **Kết quả mong đợi:** Bị rate-limit sau N lần; OTP hết hạn bị từ chối; không gửi lại OTP cũ.
- **Coverage hiện tại:** MISSING

### TC-NOTI-028 — Push qua Zalo OA thành công (v3)
- **Function:** NOTI-011
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (mock Zalo API)
- **Tiền điều kiện:** Clinic cấu hình Zalo OA token; user có Zalo user_id; tính năng v3 bật.
- **Bước thực hiện:** 1) Trigger push Zalo cho nhắc lịch.
- **Dữ liệu test:** template Zalo.
- **Kết quả mong đợi:** Gọi Zalo API mock đúng payload; log `channel=zalo, status=sent`. (Chưa ship → skip/xfail.)
- **Coverage hiện tại:** MISSING

### TC-NOTI-029 — Zalo token sai/hết hạn → fail có kiểm soát
- **Function:** NOTI-011
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (mock Zalo API lỗi)
- **Tiền điều kiện:** Token Zalo OA hết hạn.
- **Bước thực hiện:** 1) Trigger push.
- **Dữ liệu test:** token invalid.
- **Kết quả mong đợi:** Log `failed`; không retry vô hạn; cảnh báo admin cấu hình lại OA.
- **Coverage hiện tại:** MISSING

### TC-NOTI-030 — Đăng ký Web Push subscription (v2)
- **Function:** NOTI-012
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Browser hỗ trợ Push API; user cấp quyền.
- **Bước thực hiện:** 1) `POST` đăng ký push subscription (endpoint + keys). 2) Tạo notification → đẩy push.
- **Dữ liệu test:** subscription object hợp lệ.
- **Kết quả mong đợi:** Lưu subscription gắn user/clinic; notification mới được đẩy tới đúng subscription. (Chưa ship → skip/xfail.)
- **Coverage hiện tại:** MISSING

### TC-NOTI-031 — Web Push subscription yêu cầu xác thực (401)
- **Function:** NOTI-012
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) `POST` đăng ký push không auth.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING

### TC-NOTI-032 — Hiển thị native OS notification (Tauri) khi có notification mới
- **Function:** NOTI-013
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Manual/UI (vitest + Tauri plugin)
- **Tiền điều kiện:** App Tauri đã cấp quyền notification OS (TASK-016).
- **Bước thực hiện:** 1) Nhận notification mới (poll/sync). 2) Quan sát native toast OS.
- **Dữ liệu test:** 1 notification mới.
- **Kết quả mong đợi:** Hiện native OS notification với title/body; click mở app tới link liên quan.
- **Coverage hiện tại:** PARTIAL (TASK-016 đã ship phần Tauri foundation/IPC — xem `TASK-016/deliveries/api-specs/tauri-ipc-commands.md`; chưa thấy test tự động backend↔Tauri cho luồng notification cụ thể).

### TC-NOTI-033 — Không bật native notification khi OS chặn quyền
- **Function:** NOTI-013
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Quyền notification OS bị từ chối.
- **Bước thực hiện:** 1) Nhận notification mới.
- **Dữ liệu test:** permission denied.
- **Kết quả mong đợi:** Không crash; fallback hiển thị in-app badge/toast trong app; gợi ý người dùng bật quyền.
- **Coverage hiện tại:** PARTIAL

### TC-NOTI-034 — Click native notification điều hướng đúng deep-link
- **Function:** NOTI-013
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI
- **Tiền điều kiện:** Notification có `link` (vd `/billing/invoice/{id}`).
- **Bước thực hiện:** 1) Click native notification.
- **Dữ liệu test:** notification link tới invoice.
- **Kết quả mong đợi:** App focus + điều hướng tới đúng route; đánh dấu đã đọc.
- **Coverage hiện tại:** PARTIAL

### TC-NOTI-035 — Cập nhật tùy chọn nhận thông báo theo loại (v2)
- **Function:** NOTI-014
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User đã auth; tính năng v2 bật.
- **Bước thực hiện:** 1) `PUT` preferences `{low_stock:false, visit_complete:true, subscription:true}`. 2) `GET` lại.
- **Dữ liệu test:** preferences theo loại.
- **Kết quả mong đợi:** HTTP 200; lưu đúng từng loại; GET trả đúng; áp dụng cho user/clinic hiện tại. (Chưa ship → skip/xfail.)
- **Coverage hiện tại:** MISSING

### TC-NOTI-036 — Tắt loại low-stock → không nhận thông báo low-stock
- **Function:** NOTI-014
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Pharmacist đặt `low_stock=false`.
- **Bước thực hiện:** 1) Trigger sự kiện low-stock (NOTI-006). 2) Kiểm tra notification của pharmacist.
- **Dữ liệu test:** preference low_stock off.
- **Kết quả mong đợi:** Không tạo in-app notification low-stock cho pharmacist này; các loại khác vẫn nhận.
- **Coverage hiện tại:** MISSING

### TC-NOTI-037 — Preferences yêu cầu xác thực (401)
- **Function:** NOTI-014
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) `GET/PUT` preferences không auth.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING

### TC-NOTI-038 — Cron reminder chọn đúng appointment trong cửa sổ T-24h
- **Function:** NOTI-015
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có appointment trong cửa sổ T-24h (23–25h tới) và 1 cái T-48h; scheduler `cron(appointment_reminders, minute=0)` (system_design §19).
- **Bước thực hiện:** 1) Chạy job `appointment_reminders`.
- **Dữ liệu test:** 2 appointment.
- **Kết quả mong đợi:** Chỉ appointment trong cửa sổ T-24h được enqueue gửi reminder; cái T-48h bỏ qua.
- **Coverage hiện tại:** MISSING

### TC-NOTI-039 — Không nhắc trùng (dùng `reminder_sent_at`)
- **Function:** NOTI-015
- **Loại:** Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Appointment đã có `reminder_sent_at` set (đã nhắc T-24h).
- **Bước thực hiện:** 1) Chạy lại cron.
- **Dữ liệu test:** appointment đã nhắc.
- **Kết quả mong đợi:** KHÔNG gửi lần 2 (khử trùng theo `reminder_sent_at` — field có trong model, system_design dòng `reminder_sent_at`).
- **Coverage hiện tại:** MISSING

### TC-NOTI-040 — Bỏ qua appointment đã hủy / NO_SHOW / đã check-in
- **Function:** NOTI-015
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Appointment trong cửa sổ T-24h nhưng `status` ∈ {CANCELLED, NO_SHOW, đã check-in}.
- **Bước thực hiện:** 1) Chạy cron.
- **Dữ liệu test:** appointment cancelled.
- **Kết quả mong đợi:** Không enqueue reminder cho các trạng thái này.
- **Coverage hiện tại:** MISSING

### TC-NOTI-041 — Cron chạy đa clinic không lẫn dữ liệu (RLS/scoping)
- **Function:** NOTI-015
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B đều có appointment cần nhắc.
- **Bước thực hiện:** 1) Chạy cron toàn hệ thống.
- **Dữ liệu test:** appointment A, B.
- **Kết quả mong đợi:** Mỗi reminder/notification gắn đúng `clinic_id`, dùng template + thông tin clinic đúng; không lẫn người nhận giữa A và B.
- **Coverage hiện tại:** MISSING

### TC-NOTI-042 — Cron idempotent khi chạy lặp trong cùng giờ
- **Function:** NOTI-015
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Cron chạy mỗi giờ (`minute=0`); job có thể bị trigger 2 lần do retry.
- **Bước thực hiện:** 1) Chạy job 2 lần liên tiếp cho cùng tập appointment.
- **Dữ liệu test:** cùng tập appointment.
- **Kết quả mong đợi:** Tổng số reminder gửi = số appointment (không nhân đôi), nhờ `reminder_sent_at`.
- **Coverage hiện tại:** MISSING

### TC-NOTI-043 — Reminder T-2h gửi độc lập với T-24h
- **Function:** NOTI-015
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Appointment đã được nhắc T-24h; nay vào cửa sổ T-2h.
- **Bước thực hiện:** 1) Chạy cron khi appointment trong cửa sổ T-2h.
- **Dữ liệu test:** appointment T-2h, đã nhắc T-24h.
- **Kết quả mong đợi:** Gửi reminder T-2h (mốc nhắc khác T-24h được theo dõi riêng); không bị chặn nhầm bởi khử trùng T-24h.
- **Coverage hiện tại:** MISSING

---

## 3. Ghi chú & khuyến nghị
- **Khi backend module `notifications` được merge vào `../clinic-cms-merge`:** map từng TC sang endpoint thật (`app/modules/notifications/api/routes.py`), permission code thật (qua `require_permission`), và liên kết file test trong `clinic-cms/tests/integration/` để chuyển Coverage MISSING → COVERED/PARTIAL. Đối chiếu migration `0013_create_notifications.py`.
- **NOTI-013** đã có nền tảng Tauri (TASK-016) — cần bổ sung test tự động cho luồng push native (vitest mock plugin notification) để nâng từ PARTIAL → COVERED.
- **NOTI-010/011/012/014** là IDEA (v2/v3) — TC giữ ở dạng skip/xfail cho tới khi tính năng được lên kế hoạch; vẫn liệt kê để đảm bảo bao phủ 100% function của group.
- Mọi TC liên quan quyền đã có case 401 (chưa auth); các sự kiện hệ thống (visit/stock/subscription/cron) không gọi qua route người dùng nên dùng case isolation/RLS thay cho 403. Các TC chạm dữ liệu domain đều có case cô lập clinic (RLS).
