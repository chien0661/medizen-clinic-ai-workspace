# Test Case Catalog — AUTH · Xác thực & Phiên đăng nhập

**Nguồn:** function_list_data.py (group AUTH) + clinic_management_function_list.md + system_design/BA.
**Phạm vi:** 22 functions (AUTH-001 … AUTH-022).  **Tổng test case:** 74.  **Ngày:** 2026-05-30.

> Ghi chú trạng thái nguồn: ✅ = DONE, 🔄 = IN_PROGRESS, ⬜ = TODO, 💡 = IDEA (chưa lên kế hoạch).
> Quy ước Coverage: COVERED = đã có hành vi ship + có thể kiểm chứng (test thực tế hoặc endpoint live); PARTIAL = một phần đã có (BE done, FE/flow chưa, hoặc thiếu nhánh edge); MISSING = chưa ship / chưa có test.
> Lưu ý độ tin cậy: trong phiên soạn này kênh thực thi tool bị gián đoạn nên KHÔNG đối chiếu được trực tiếp file test trong `clinic-cms-merge/tests` và mã nguồn `clinic-cms-merge/app`. Cột "Coverage hiện tại" suy ra từ cột Status nguồn + mô tả nghiệp vụ; các mục đánh dấu "(cần xác minh test file)" phải được Test Engineer kiểm chứng lại khi môi trường ổn định.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| AUTH-001 | Đăng nhập email/password (không cần clinic_code) | 🔄 IN_PROGRESS | TC-AUTH-001, TC-AUTH-002, TC-AUTH-003, TC-AUTH-004, TC-AUTH-005, TC-AUTH-006 | PARTIAL |
| AUTH-002 | Refresh token (rolling) | ✅ DONE | TC-AUTH-007, TC-AUTH-008, TC-AUTH-009, TC-AUTH-010 | COVERED |
| AUTH-003 | Logout (revoke refresh token) | ✅ DONE | TC-AUTH-011, TC-AUTH-012, TC-AUTH-013 | COVERED |
| AUTH-004 | Đổi mật khẩu | ✅ DONE | TC-AUTH-014, TC-AUTH-015, TC-AUTH-016, TC-AUTH-017 | COVERED |
| AUTH-005 | Forced change password | ✅ DONE | TC-AUTH-018, TC-AUTH-019, TC-AUTH-020 | COVERED |
| AUTH-006 | Account lockout (5 lần fail / 30p) | ✅ DONE | TC-AUTH-021, TC-AUTH-022, TC-AUTH-023, TC-AUTH-024 | COVERED |
| AUTH-007 | Rate limit login per IP | ✅ DONE | TC-AUTH-025, TC-AUTH-026, TC-AUTH-027 | COVERED |
| AUTH-008 | Reset password (admin generate) | ⬜ TODO | TC-AUTH-028, TC-AUTH-029, TC-AUTH-030, TC-AUTH-031 | MISSING |
| AUTH-009 | Forgot password (self-service email) | ⬜ TODO | TC-AUTH-032, TC-AUTH-033, TC-AUTH-034, TC-AUTH-035 | MISSING |
| AUTH-010 | MFA TOTP | 💡 IDEA | TC-AUTH-036, TC-AUTH-037, TC-AUTH-038 | MISSING |
| AUTH-011 | MFA bắt buộc cho super admin | 💡 IDEA | TC-AUTH-039, TC-AUTH-040 | MISSING |
| AUTH-012 | Session timeout (30p inactive) | ✅ DONE | TC-AUTH-041, TC-AUTH-042, TC-AUTH-043 | COVERED |
| AUTH-013 | Show password toggle | ✅ DONE | TC-AUTH-044 | COVERED |
| AUTH-014 | Remember me (Tauri secure storage) | ✅ DONE | TC-AUTH-045, TC-AUTH-046 | PARTIAL |
| AUTH-015 | Last login tracking | ✅ DONE | TC-AUTH-047, TC-AUTH-048 | COVERED |
| AUTH-016 | IP whitelist (super admin) | 💡 IDEA | TC-AUTH-049, TC-AUTH-050 | MISSING |
| AUTH-017 | Re-authentication trước action nguy hiểm | 💡 IDEA | TC-AUTH-051, TC-AUTH-052 | MISSING |
| AUTH-018 | Account ↔ Multi-clinic mapping (pivot) | ⬜ TODO | TC-AUTH-053, TC-AUTH-054, TC-AUTH-055, TC-AUTH-056, TC-AUTH-057 | MISSING |
| AUTH-019 | Default clinic per account | ⬜ TODO | TC-AUTH-058, TC-AUTH-059, TC-AUTH-060 | MISSING |
| AUTH-020 | Auto-resolve clinic post-login | ⬜ TODO | TC-AUTH-061, TC-AUTH-062, TC-AUTH-063, TC-AUTH-064, TC-AUTH-065 | MISSING |
| AUTH-021 | Switch-clinic flow + JWT reset | ⬜ TODO | TC-AUTH-066, TC-AUTH-067, TC-AUTH-068, TC-AUTH-069, TC-AUTH-070, TC-AUTH-071 | MISSING |
| AUTH-022 | Last-active clinic remembered | ⬜ TODO | TC-AUTH-072, TC-AUTH-073, TC-AUTH-074 | MISSING |

**Tổng kết coverage theo function:** COVERED = 9 · PARTIAL = 2 · MISSING = 11.

---

## 2. Chi tiết Test Cases

### AUTH-001 — Đăng nhập email/password

#### TC-AUTH-001 — Login thành công với email + password hợp lệ (single clinic)
- **Function:** AUTH-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) / E2E (httpx)
- **Tiền điều kiện:** Tồn tại account `nurse1@clinicA.vn` mật khẩu đúng, account chỉ map 1 clinic trong `account_clinic_role`, `must_change_password=false`, account active.
- **Bước thực hiện:** 1) POST `/auth/login` body `{email, password}` (KHÔNG có clinic_code). 2) Đọc response.
- **Dữ liệu test:** email=`nurse1@clinicA.vn`, password=`Valid@123`.
- **Kết quả mong đợi:** HTTP 200. Response chứa `access_token` (TTL 15p), `refresh_token` (TTL 7d), `user` info, `clinics[]` (1 phần tử). JWT decode chứa `account_id` + `clinic_id` (clinic duy nhất) + `roles[]` + `permissions[]`. Audit ghi `login.success`. Redis set `user:perms:{uid}:{clinic_id}` TTL 5p. `failed_login_count` reset về 0.
- **Coverage hiện tại:** PARTIAL — BE login đã ship nhưng đang migrate khỏi `clinic_code` (status 🔄). Cần xác minh test file ở `clinic-cms-merge/tests` đã cập nhật shape không-clinic_code.

#### TC-AUTH-002 — Login sai mật khẩu
- **Function:** AUTH-001
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) / E2E (httpx)
- **Tiền điều kiện:** Account tồn tại, đang ở `failed_login_count < 4`.
- **Bước thực hiện:** 1) POST `/auth/login` với password sai. 2) Đọc response + DB.
- **Dữ liệu test:** email=`nurse1@clinicA.vn`, password=`WrongPass`.
- **Kết quả mong đợi:** HTTP 401, message chung chung (không tiết lộ "email tồn tại"). `failed_login_count` tăng +1. Audit `login.failed`. KHÔNG trả token.
- **Coverage hiện tại:** PARTIAL — (cần xác minh test file).

#### TC-AUTH-003 — Login với email không tồn tại
- **Function:** AUTH-001
- **Loại:** Negative / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Email không có trong hệ thống.
- **Bước thực hiện:** 1) POST `/auth/login` email lạ.
- **Dữ liệu test:** email=`ghost@nowhere.vn`, password=`Whatever1`.
- **Kết quả mong đợi:** HTTP 401 với cùng message như sai password (chống user enumeration). Thời gian phản hồi tương đương case sai password (chống timing attack).
- **Coverage hiện tại:** PARTIAL — (cần xác minh test file).

#### TC-AUTH-004 — Login khi account bị khoá (locked)
- **Function:** AUTH-001
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account đang trong trạng thái lockout (xem AUTH-006), `locked_until > now()`.
- **Bước thực hiện:** 1) POST `/auth/login` với password ĐÚNG.
- **Dữ liệu test:** account đã lock, password đúng.
- **Kết quả mong đợi:** HTTP 423 (Locked) hoặc 401 kèm mã lỗi `account_locked` + thời gian còn lại. KHÔNG cấp token dù password đúng.
- **Coverage hiện tại:** PARTIAL — (cần xác minh test file).

#### TC-AUTH-005 — Login account bị vô hiệu hoá / không thuộc clinic nào
- **Function:** AUTH-001
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account tồn tại, password đúng, nhưng `is_active=false` HOẶC không có row nào trong `account_clinic_role` (đã bị revoke khỏi mọi clinic).
- **Bước thực hiện:** 1) POST `/auth/login` password đúng.
- **Dữ liệu test:** account `revoked@x.vn`.
- **Kết quả mong đợi:** HTTP 403 — không thể vào hệ thống vì không còn clinic context; message rõ ràng. KHÔNG cấp token có `clinic_id` null.
- **Coverage hiện tại:** MISSING — phụ thuộc AUTH-018/020 (TODO).

#### TC-AUTH-006 — Validate input login (email format, field rỗng)
- **Function:** AUTH-001
- **Loại:** Negative / Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx) / Manual-UI (vitest)
- **Tiền điều kiện:** Không.
- **Bước thực hiện:** 1) POST `/auth/login` thiếu `password`; 2) gửi `email` sai định dạng.
- **Dữ liệu test:** `{email:"abc", password:""}`.
- **Kết quả mong đợi:** HTTP 422 validation error, không chạm DB. UI hiện lỗi inline.
- **Coverage hiện tại:** PARTIAL — (cần xác minh test file).

---

### AUTH-002 — Refresh token (rolling)

#### TC-AUTH-007 — Refresh token hợp lệ sinh access + refresh mới
- **Function:** AUTH-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) / E2E (httpx)
- **Tiền điều kiện:** Có `refresh_token` còn hạn, chưa revoke.
- **Bước thực hiện:** 1) POST `/auth/refresh` body `{refresh_token}`. 2) Lưu access + refresh mới.
- **Dữ liệu test:** refresh_token còn hạn.
- **Kết quả mong đợi:** HTTP 200, trả `access_token` mới (TTL 15p) + `refresh_token` mới. Refresh CŨ bị revoke (rolling). Claims giữ nguyên `clinic_id`/`roles`.
- **Coverage hiện tại:** COVERED — status ✅ DONE (cần xác minh test file).

#### TC-AUTH-008 — Refresh với token đã revoke (rolling reuse)
- **Function:** AUTH-002
- **Loại:** Negative / Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã refresh 1 lần → token cũ đã revoke.
- **Bước thực hiện:** 1) Gọi `/auth/refresh` lại bằng refresh_token CŨ.
- **Dữ liệu test:** refresh_token đã dùng.
- **Kết quả mong đợi:** HTTP 401. Phát hiện reuse → (best practice) revoke toàn bộ token family của user. Audit cảnh báo.
- **Coverage hiện tại:** COVERED/PARTIAL — refresh đã ship; nhánh reuse-detection cần xác minh test file.

#### TC-AUTH-009 — Refresh với token hết hạn
- **Function:** AUTH-002
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** refresh_token quá 7 ngày.
- **Bước thực hiện:** 1) POST `/auth/refresh`.
- **Dữ liệu test:** token expired.
- **Kết quả mong đợi:** HTTP 401, FE force logout + redirect `/login`.
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

#### TC-AUTH-010 — Refresh với token rác / chữ ký sai
- **Function:** AUTH-002
- **Loại:** Negative / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Không.
- **Bước thực hiện:** 1) POST `/auth/refresh` với chuỗi sai chữ ký JWT.
- **Dữ liệu test:** `refresh_token="aaa.bbb.ccc"`.
- **Kết quả mong đợi:** HTTP 401, không leak chi tiết lỗi crypto.
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

---

### AUTH-003 — Logout

#### TC-AUTH-011 — Logout revoke refresh token thành công
- **Function:** AUTH-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) / E2E (httpx)
- **Tiền điều kiện:** User đã login, có refresh_token hợp lệ.
- **Bước thực hiện:** 1) POST `/auth/logout` body `{refresh_token}` kèm access token header. 2) Thử refresh lại bằng token vừa logout.
- **Dữ liệu test:** token đang hoạt động.
- **Kết quả mong đợi:** HTTP 200/204. Token vào blacklist Redis (TTL = remaining lifetime). Audit `logout`. Bước refresh sau đó → 401.
- **Coverage hiện tại:** COVERED — ✅ DONE (cần xác minh test file).

#### TC-AUTH-012 — Logout khi chưa auth (thiếu token)
- **Function:** AUTH-003
- **Loại:** Negative / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Không gửi Authorization header.
- **Bước thực hiện:** 1) POST `/auth/logout` không token.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

#### TC-AUTH-013 — Logout idempotent (token đã revoke)
- **Function:** AUTH-003
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Token đã được logout trước đó.
- **Bước thực hiện:** 1) Logout lại token cũ.
- **Dữ liệu test:** token đã blacklist.
- **Kết quả mong đợi:** HTTP 200/204 (idempotent, không lỗi server) hoặc 401 nhất quán; không 500.
- **Coverage hiện tại:** PARTIAL — (cần xác minh test file).

---

### AUTH-004 — Đổi mật khẩu

#### TC-AUTH-014 — Đổi mật khẩu thành công + revoke mọi session
- **Function:** AUTH-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User đã login, biết current password.
- **Bước thực hiện:** 1) POST `/auth/change-password` `{current_password, new_password, confirm}`. 2) Thử dùng refresh_token cũ trên device khác.
- **Dữ liệu test:** new=`NewP@ss9`.
- **Kết quả mong đợi:** HTTP 200. `password_hash` cập nhật (bcrypt), `password_changed_at=now()`. TẤT CẢ refresh token bị revoke (force re-login mọi device). Audit event. Refresh cũ → 401.
- **Coverage hiện tại:** COVERED — ✅ DONE (cần xác minh test file).

#### TC-AUTH-015 — Đổi mật khẩu với current password sai
- **Function:** AUTH-004
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User đã login.
- **Bước thực hiện:** 1) POST với `current_password` sai.
- **Dữ liệu test:** current=`Wrong1`.
- **Kết quả mong đợi:** HTTP 400/401, password KHÔNG đổi.
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

#### TC-AUTH-016 — New password vi phạm complexity / trùng password cũ
- **Function:** AUTH-004
- **Loại:** Negative / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User đã login.
- **Bước thực hiện:** 1) new=`abc` (yếu); 2) new = current password.
- **Dữ liệu test:** new yếu / new trùng cũ.
- **Kết quả mong đợi:** HTTP 422/400 — yêu cầu min 8 ký tự + 1 hoa + 1 số + 1 ký tự đặc biệt; không cho phép trùng password cũ.
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

#### TC-AUTH-017 — Đổi mật khẩu khi chưa auth (401)
- **Function:** AUTH-004
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) POST `/auth/change-password` không Authorization.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

---

### AUTH-005 — Forced change password

#### TC-AUTH-018 — User must_change_password bị redirect tới /change-password
- **Function:** AUTH-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) / Manual-UI (vitest)
- **Tiền điều kiện:** Account `must_change_password=true` (mới tạo / sau reset).
- **Bước thực hiện:** 1) Login bằng temp password OK. 2) Gọi 1 API nghiệp vụ bất kỳ.
- **Dữ liệu test:** account temp.
- **Kết quả mong đợi:** Mọi request (ngoài change-password) bị middleware chặn/redirect; FE chuyển màn `/change-password`.
- **Coverage hiện tại:** COVERED — ✅ DONE (cần xác minh test file).

#### TC-AUTH-019 — Đổi password lần đầu (không cần current) thành công
- **Function:** AUTH-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** `must_change_password=true`.
- **Bước thực hiện:** 1) POST đổi password chỉ `{new_password, confirm}`.
- **Dữ liệu test:** new=`First@123`.
- **Kết quả mong đợi:** HTTP 200, `must_change_password=false`, audit `forced_password_change_completed`, sau đó truy cập app bình thường.
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

#### TC-AUTH-020 — Cố bypass forced change (gọi API khác trước khi đổi)
- **Function:** AUTH-005
- **Loại:** Security / Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** `must_change_password=true`.
- **Bước thực hiện:** 1) Dùng token gọi thẳng API nghiệp vụ (bỏ qua FE redirect).
- **Dữ liệu test:** token của account temp.
- **Kết quả mong đợi:** HTTP 403 từ middleware (server-side enforcement, không chỉ FE).
- **Coverage hiện tại:** PARTIAL — cần xác minh enforcement ở BE middleware (test file).

---

### AUTH-006 — Account lockout

#### TC-AUTH-021 — Khoá account sau 5 lần fail liên tiếp
- **Function:** AUTH-006
- **Loại:** Happy path (security control)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account active, `failed_login_count=0`.
- **Bước thực hiện:** 1) Gọi login sai 5 lần. 2) Lần 6 gọi password ĐÚNG.
- **Dữ liệu test:** 5x sai → 1x đúng.
- **Kết quả mong đợi:** Sau lần 5: account locked, `locked_until = now()+30p`. Lần 6 (đúng) → 423/401 `account_locked`.
- **Coverage hiện tại:** COVERED — ✅ DONE (cần xác minh test file).

#### TC-AUTH-022 — Auto-unlock sau khi hết thời gian lock
- **Function:** AUTH-006
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account đang locked, `locked_until` đã qua (giả lập thời gian / set DB).
- **Bước thực hiện:** 1) Login password đúng sau khi hết lock.
- **Dữ liệu test:** locked_until in past.
- **Kết quả mong đợi:** HTTP 200, login OK, `failed_login_count` reset 0.
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

#### TC-AUTH-023 — Login đúng giữa chừng reset bộ đếm fail
- **Function:** AUTH-006
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** `failed_login_count=3`.
- **Bước thực hiện:** 1) Login đúng. 2) Kiểm tra counter.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Login OK, `failed_login_count` về 0 (không tích luỹ sang phiên sau).
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

#### TC-AUTH-024 — Counter per-account, không ảnh hưởng account khác
- **Function:** AUTH-006
- **Loại:** Edge / Security
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 account A, B.
- **Bước thực hiện:** 1) Fail A 5 lần (lock A). 2) Login B đúng.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** A bị lock, B login bình thường.
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

---

### AUTH-007 — Rate limit login per IP

#### TC-AUTH-025 — Rate limit theo IP khi vượt ngưỡng
- **Function:** AUTH-007
- **Loại:** Happy path (security control)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) / E2E (httpx)
- **Tiền điều kiện:** Cấu hình rate limit (vd N req/phút/IP).
- **Bước thực hiện:** 1) Gửi login dồn dập từ cùng IP vượt ngưỡng.
- **Dữ liệu test:** burst requests.
- **Kết quả mong đợi:** HTTP 429 Too Many Requests + header `Retry-After`.
- **Coverage hiện tại:** COVERED — ✅ DONE (cần xác minh test file).

#### TC-AUTH-026 — Rate limit reset sau cửa sổ thời gian
- **Function:** AUTH-007
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã bị 429.
- **Bước thực hiện:** 1) Chờ hết cửa sổ. 2) Login lại.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Login chấp nhận lại (HTTP 200/401 tuỳ credentials).
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

#### TC-AUTH-027 — Rate limit cô lập theo IP (IP khác không bị chặn)
- **Function:** AUTH-007
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** IP1 đã bị 429.
- **Bước thực hiện:** 1) Login từ IP2 (X-Forwarded-For khác).
- **Dữ liệu test:** —
- **Kết quả mong đợi:** IP2 không bị chặn.
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

---

### AUTH-008 — Reset password (admin generate)

#### TC-AUTH-028 — Clinic Admin reset password sinh temp + bật must_change
- **Function:** AUTH-008
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin clinic A đăng nhập, nhân viên X thuộc clinic A.
- **Bước thực hiện:** 1) POST `/admin/users/{id}/reset-password`. 2) Đọc response.
- **Dữ liệu test:** user X.
- **Kết quả mong đợi:** HTTP 200, trả temp password (hoặc gửi qua kênh an toàn). `must_change_password=true`. Revoke session hiện có của X. Audit `admin_password_reset` (actor=admin).
- **Coverage hiện tại:** MISSING — status ⬜ TODO (TASK-006 chưa ship).

#### TC-AUTH-029 — Reset password khi chưa auth (401)
- **Function:** AUTH-008
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) POST reset không Authorization.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-030 — Reset password thiếu quyền admin (403)
- **Function:** AUTH-008
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User thường (không phải admin) đăng nhập.
- **Bước thực hiện:** 1) POST reset cho user khác.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 403 (thiếu permission).
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-031 — Admin clinic A KHÔNG reset được user clinic B (RLS / cô lập clinic)
- **Function:** AUTH-008
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin clinic A; user Y chỉ thuộc clinic B.
- **Bước thực hiện:** 1) Admin A POST reset cho user Y.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 403/404 — không thấy/không thao tác được user ngoài clinic context (RLS chặn).
- **Coverage hiện tại:** MISSING.

---

### AUTH-009 — Forgot password (self-service email)

#### TC-AUTH-032 — Yêu cầu reset gửi email link
- **Function:** AUTH-009
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Email tồn tại.
- **Bước thực hiện:** 1) POST `/auth/forgot-password` `{email}`.
- **Dữ liệu test:** email hợp lệ.
- **Kết quả mong đợi:** HTTP 200 (luôn 200 chống enumeration). Sinh reset token (hết hạn ngắn, 1 lần dùng), gửi email link.
- **Coverage hiện tại:** MISSING — status ⬜ TODO (TASK-027).

#### TC-AUTH-033 — Forgot password với email không tồn tại (chống enumeration)
- **Function:** AUTH-009
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Email không tồn tại.
- **Bước thực hiện:** 1) POST forgot-password.
- **Dữ liệu test:** email lạ.
- **Kết quả mong đợi:** HTTP 200 với cùng message (không tiết lộ tồn tại), không gửi email.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-034 — Đặt lại password qua token hợp lệ
- **Function:** AUTH-009
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có reset token còn hạn.
- **Bước thực hiện:** 1) POST `/auth/reset-password` `{token, new_password}`.
- **Dữ liệu test:** token hợp lệ.
- **Kết quả mong đợi:** HTTP 200, password đổi, token vô hiệu hoá sau dùng, revoke session cũ.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-035 — Reset token hết hạn / đã dùng / sai
- **Function:** AUTH-009
- **Loại:** Negative / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Token expired hoặc đã dùng.
- **Bước thực hiện:** 1) POST reset-password với token đó.
- **Dữ liệu test:** token cũ.
- **Kết quả mong đợi:** HTTP 400/410, password không đổi.
- **Coverage hiện tại:** MISSING.

---

### AUTH-010 — MFA TOTP

#### TC-AUTH-036 — Bật MFA: sinh secret + QR + verify mã đầu tiên
- **Function:** AUTH-010
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User đã login.
- **Bước thực hiện:** 1) POST `/auth/mfa/setup` → nhận secret/otpauth URI. 2) POST `/auth/mfa/verify` với mã TOTP hợp lệ.
- **Dữ liệu test:** TOTP code đúng (sinh từ secret).
- **Kết quả mong đợi:** HTTP 200, MFA enabled, trả recovery codes.
- **Coverage hiện tại:** MISSING — status 💡 IDEA (chưa lên kế hoạch).

#### TC-AUTH-037 — Login yêu cầu nhập mã TOTP khi MFA bật
- **Function:** AUTH-010
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account đã bật MFA.
- **Bước thực hiện:** 1) Login email+password → bước challenge MFA. 2) Nhập TOTP đúng.
- **Dữ liệu test:** TOTP đúng.
- **Kết quả mong đợi:** Bước 1 trả `mfa_required=true` (chưa cấp full token); bước 2 cấp token.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-038 — TOTP sai / hết hiệu lực (window)
- **Function:** AUTH-010
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** MFA bật.
- **Bước thực hiện:** 1) Nhập TOTP sai / mã ngoài time window.
- **Dữ liệu test:** code sai.
- **Kết quả mong đợi:** HTTP 401, không cấp token; có thể đếm vào lockout.
- **Coverage hiện tại:** MISSING.

---

### AUTH-011 — MFA bắt buộc cho super admin

#### TC-AUTH-039 — Super admin chưa bật MFA bị buộc thiết lập trước khi vào
- **Function:** AUTH-011
- **Loại:** Happy path / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account super admin, MFA chưa bật.
- **Bước thực hiện:** 1) Login super admin.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Buộc enroll MFA trước khi cấp full quyền platform.
- **Coverage hiện tại:** MISSING — status 💡 IDEA.

#### TC-AUTH-040 — Super admin login bỏ qua MFA bị chặn (403)
- **Function:** AUTH-011
- **Loại:** Security / Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Super admin MFA bật.
- **Bước thực hiện:** 1) Cố lấy token platform không qua MFA.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 403/401 — không thể truy cập platform admin nếu thiếu MFA.
- **Coverage hiện tại:** MISSING.

---

### AUTH-012 — Session timeout

#### TC-AUTH-041 — Auto-logout sau 30 phút không hoạt động
- **Function:** AUTH-012
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx) / Manual-UI (vitest)
- **Tiền điều kiện:** User login, cấu hình timeout 30p.
- **Bước thực hiện:** 1) Không hoạt động > 30p (hoặc access token 15p hết hạn + không refresh). 2) Gọi API.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401, FE redirect `/login` với thông báo phiên hết hạn.
- **Coverage hiện tại:** COVERED — ✅ DONE (cần xác minh test file).

#### TC-AUTH-042 — Hoạt động trong ngưỡng reset đồng hồ timeout
- **Function:** AUTH-012
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual-UI (vitest)
- **Tiền điều kiện:** User login.
- **Bước thực hiện:** 1) Thao tác đều đặn < 30p giữa các lần.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Không bị auto-logout; refresh token tự gia hạn access.
- **Coverage hiện tại:** PARTIAL — (cần xác minh test FE/idle-timer).

#### TC-AUTH-043 — Access token expired nhưng refresh còn hạn → silent refresh
- **Function:** AUTH-012
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Access hết hạn (15p), refresh còn hạn.
- **Bước thực hiện:** 1) Gọi API → 401 → FE interceptor refresh → retry.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Request cuối thành công, không buộc user re-login.
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

---

### AUTH-013 — Show password toggle

#### TC-AUTH-044 — Toggle hiện/ẩn mật khẩu trên form login
- **Function:** AUTH-013
- **Loại:** Happy path (UI)
- **Ưu tiên:** P2
- **Layer:** Manual-UI (vitest)
- **Tiền điều kiện:** Mở màn login.
- **Bước thực hiện:** 1) Nhập password. 2) Click icon Eye → kiểm tra `type=text`. 3) Click EyeOff → `type=password`.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Trạng thái input đổi đúng; mặc định ẩn.
- **Coverage hiện tại:** COVERED — ✅ DONE (TASK-017) (cần xác minh vitest).

---

### AUTH-014 — Remember me (Tauri secure storage)

#### TC-AUTH-045 — Tick remember me lưu credential vào Tauri secure storage
- **Function:** AUTH-014
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual-UI (vitest) / E2E Tauri
- **Tiền điều kiện:** Desktop Tauri.
- **Bước thực hiện:** 1) Login có tick "Remember me". 2) Mở lại app.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Email (và/hoặc token an toàn) prefilled từ secure storage, KHÔNG lưu plaintext password.
- **Coverage hiện tại:** PARTIAL — UI ship (TASK-017) nhưng cơ chế secure-storage cần xác minh; rủi ro lưu nhạy cảm.

#### TC-AUTH-046 — Không tick remember me → không lưu credential
- **Function:** AUTH-014
- **Loại:** Security / Negative
- **Ưu tiên:** P2
- **Layer:** Manual-UI (vitest)
- **Tiền điều kiện:** Desktop Tauri.
- **Bước thực hiện:** 1) Login không tick. 2) Mở lại app.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Không có credential lưu lại; form trống.
- **Coverage hiện tại:** PARTIAL — (cần xác minh).

---

### AUTH-015 — Last login tracking

#### TC-AUTH-047 — Cập nhật last_login_at sau login thành công
- **Function:** AUTH-015
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account login OK.
- **Bước thực hiện:** 1) Login. 2) Đọc field last_login (DB / profile API).
- **Dữ liệu test:** —
- **Kết quả mong đợi:** `last_login_at` cập nhật về now(); giá trị cũ hiển thị cho user ("đăng nhập lần cuối").
- **Coverage hiện tại:** COVERED — ✅ DONE (cần xác minh test file).

#### TC-AUTH-048 — Login fail KHÔNG cập nhật last_login_at
- **Function:** AUTH-015
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Login sai password. 2) Kiểm tra last_login_at.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** `last_login_at` không đổi (chỉ ghi khi thành công).
- **Coverage hiện tại:** COVERED — (cần xác minh test file).

---

### AUTH-016 — IP whitelist (super admin)

#### TC-AUTH-049 — Super admin login từ IP trong whitelist OK
- **Function:** AUTH-016
- **Loại:** Happy path / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Cấu hình whitelist IP cho super admin.
- **Bước thực hiện:** 1) Login từ IP whitelisted.
- **Dữ liệu test:** IP hợp lệ.
- **Kết quả mong đợi:** Login OK.
- **Coverage hiện tại:** MISSING — status 💡 IDEA.

#### TC-AUTH-050 — Super admin login từ IP ngoài whitelist bị chặn
- **Function:** AUTH-016
- **Loại:** Security / Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Whitelist cấu hình.
- **Bước thực hiện:** 1) Login super admin từ IP lạ.
- **Dữ liệu test:** IP không whitelist.
- **Kết quả mong đợi:** HTTP 403, audit cảnh báo; user thường không bị ảnh hưởng.
- **Coverage hiện tại:** MISSING.

---

### AUTH-017 — Re-authentication trước action nguy hiểm

#### TC-AUTH-051 — Action nhạy cảm yêu cầu nhập lại password
- **Function:** AUTH-017
- **Loại:** Happy path / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User đã login.
- **Bước thực hiện:** 1) Gọi action nhạy cảm (vd xoá dữ liệu/đổi cấu hình bảo mật) → server yêu cầu re-auth. 2) Cung cấp password đúng.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Action chỉ thực thi sau khi re-auth thành công (step-up token / xác nhận password).
- **Coverage hiện tại:** MISSING — status 💡 IDEA.

#### TC-AUTH-052 — Re-auth với password sai chặn action
- **Function:** AUTH-017
- **Loại:** Negative / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đang ở bước re-auth.
- **Bước thực hiện:** 1) Nhập password sai.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401, action KHÔNG thực thi.
- **Coverage hiện tại:** MISSING.

---

### AUTH-018 — Account ↔ Multi-clinic mapping (pivot account_clinic_role)

#### TC-AUTH-053 — Mời user đã tồn tại vào clinic chỉ thêm row pivot (không tạo account mới)
- **Function:** AUTH-018
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account `dr@x.vn` đã tồn tại (email unique global), đang thuộc clinic A. Admin clinic B mời email này.
- **Bước thực hiện:** 1) Admin B POST invite `dr@x.vn` với roles[].
- **Dữ liệu test:** email đã tồn tại.
- **Kết quả mong đợi:** Thêm 1 row `account_clinic_role(account_id, clinic_id=B, roles[], granted_at, granted_by)`. KHÔNG tạo account mới. Account vẫn giữ mapping clinic A.
- **Coverage hiện tại:** MISSING — status ⬜ TODO (TASK-006).

#### TC-AUTH-054 — Mời email chưa tồn tại tạo account + row pivot
- **Function:** AUTH-018
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Email chưa tồn tại.
- **Bước thực hiện:** 1) Admin invite email mới.
- **Dữ liệu test:** email mới.
- **Kết quả mong đợi:** Tạo account (temp password, must_change_password=true) + 1 row pivot cho clinic hiện tại.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-055 — Revoke account khỏi 1 clinic không xoá account
- **Function:** AUTH-018
- **Loại:** Happy path / Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account thuộc clinic A và B.
- **Bước thực hiện:** 1) Admin A revoke account khỏi clinic A. 2) Account login.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Row pivot clinic A bị xoá; account vẫn tồn tại, vẫn login được và chỉ thấy clinic B. JWT clinic A không còn cấp được.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-056 — Quản lý mapping thiếu quyền (403) / chưa auth (401)
- **Function:** AUTH-018
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User thường / không token.
- **Bước thực hiện:** 1) Không token → invite (401). 2) User thường → invite (403).
- **Dữ liệu test:** —
- **Kết quả mong đợi:** 401 và 403 tương ứng.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-057 — Admin clinic A KHÔNG sửa được mapping của clinic B (cô lập clinic / RLS)
- **Function:** AUTH-018
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin A; mapping của clinic B.
- **Bước thực hiện:** 1) Admin A cố revoke/sửa row pivot clinic B.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 403/404 — RLS chặn thao tác ngoài clinic context.
- **Coverage hiện tại:** MISSING.

---

### AUTH-019 — Default clinic per account

#### TC-AUTH-058 — Đặt clinic mặc định (is_default=true) trong Profile
- **Function:** AUTH-019
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account thuộc nhiều clinic.
- **Bước thực hiện:** 1) PATCH profile set default clinic = B.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Row pivot clinic B `is_default=true`, các row khác `is_default=false` (chỉ 1 default).
- **Coverage hiện tại:** MISSING — status ⬜ TODO (TASK-006).

#### TC-AUTH-059 — Login auto-load context theo default clinic
- **Function:** AUTH-019
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có default clinic, chưa có last-active.
- **Bước thực hiện:** 1) Login.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** JWT `clinic_id` = default clinic, vào thẳng dashboard (không hỏi chọn clinic).
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-060 — Chỉ tồn tại 1 default tại một thời điểm (ràng buộc)
- **Function:** AUTH-019
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Default đang là A.
- **Bước thực hiện:** 1) Set default = C.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** A `is_default` về false, C true; không tồn tại 2 default.
- **Coverage hiện tại:** MISSING.

---

### AUTH-020 — Auto-resolve clinic post-login

#### TC-AUTH-061 — Chỉ 1 clinic → auto select, vào thẳng dashboard
- **Function:** AUTH-020
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account có đúng 1 row pivot.
- **Bước thực hiện:** 1) Login.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Token gắn clinic duy nhất; FE không hiện màn chọn clinic.
- **Coverage hiện tại:** MISSING — status ⬜ TODO (TASK-006).

#### TC-AUTH-062 — Có default → load default clinic
- **Function:** AUTH-020
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Nhiều clinic, có default.
- **Bước thực hiện:** 1) Login.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Token gắn default clinic, vào thẳng dashboard.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-063 — Nhiều clinic không default → trả list để chọn (chưa cấp clinic_id)
- **Function:** AUTH-020
- **Loại:** Happy path / Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) / E2E (httpx)
- **Tiền điều kiện:** ≥2 clinic, không default, không last-active.
- **Bước thực hiện:** 1) Login. 2) Đọc response.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Response trả `clinics[]` (kèm role mỗi clinic), FE hiện màn "Chọn phòng khám". Token tạm chưa có clinic context đầy đủ cho đến khi user chọn.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-064 — Last-active override default khi cả hai cùng tồn tại
- **Function:** AUTH-020
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có default = A và last-active = C.
- **Bước thực hiện:** 1) Login.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Context load = C (last-active thắng default — theo AUTH-022).
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-065 — Resolve chỉ trả clinic user thực sự có quyền (cô lập)
- **Function:** AUTH-020
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account map clinic A, B (không C).
- **Bước thực hiện:** 1) Login. 2) Kiểm tra clinics[].
- **Dữ liệu test:** —
- **Kết quả mong đợi:** clinics[] chỉ chứa A, B; không lộ clinic C. Không thể ép token sang clinic ngoài pivot.
- **Coverage hiện tại:** MISSING.

---

### AUTH-021 — Switch-clinic flow + JWT reset

#### TC-AUTH-066 — Switch clinic sinh JWT mới với roles/perms của clinic đích
- **Function:** AUTH-021
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) / E2E (httpx)
- **Tiền điều kiện:** Account thuộc clinic A (đang active) và B với RBAC khác nhau.
- **Bước thực hiện:** 1) POST `/auth/switch-clinic` `{clinic_id=B}`. 2) Decode JWT mới.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 200, JWT mới `clinic_id=B` + `roles`/`perms` của B. JWT cũ (clinic A) bị revoke. Redis perm cache cho B set mới.
- **Coverage hiện tại:** MISSING — status ⬜ TODO.

#### TC-AUTH-067 — Switch sang clinic user KHÔNG có quyền bị chặn
- **Function:** AUTH-021
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account không có row pivot clinic Z.
- **Bước thực hiện:** 1) POST switch-clinic clinic_id=Z.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 403, không cấp token clinic Z.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-068 — Switch khi chưa auth (401)
- **Function:** AUTH-021
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) POST switch-clinic không Authorization.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-069 — JWT cũ vô hiệu sau switch (không truy cập data clinic A nữa)
- **Function:** AUTH-021
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã switch A→B.
- **Bước thực hiện:** 1) Dùng JWT cũ (clinic A) gọi API.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401 (token revoke), tránh leak data clinic cũ.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-070 — Sau switch, dữ liệu trả về thuộc đúng clinic đích (cô lập RLS)
- **Function:** AUTH-021
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã switch sang B.
- **Bước thực hiện:** 1) Gọi 1 API list dữ liệu domain (vd patients).
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Chỉ trả dữ liệu clinic B; không có bản ghi clinic A. RLS lọc theo `clinic_id` trong token mới.
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-071 — FE clear cache (zustand + react-query) sau switch
- **Function:** AUTH-021
- **Loại:** Security / Edge (UI)
- **Ưu tiên:** P1
- **Layer:** Manual-UI (vitest)
- **Tiền điều kiện:** Đang ở clinic A có cache.
- **Bước thực hiện:** 1) Switch sang B.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Cache cũ bị clear; không hiển thị tàn dư dữ liệu clinic A.
- **Coverage hiện tại:** MISSING.

---

### AUTH-022 — Last-active clinic remembered

#### TC-AUTH-072 — Ghi nhớ last-active clinic sau khi dùng/switch
- **Function:** AUTH-022
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Account đa clinic; vừa switch sang C.
- **Bước thực hiện:** 1) Switch C. 2) Kiểm tra Redis `user:last_clinic:{uid}` + Tauri local storage.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Lưu C là last-active (Redis + local).
- **Coverage hiện tại:** MISSING — status ⬜ TODO.

#### TC-AUTH-073 — Login sau auto chọn last-active (override default)
- **Function:** AUTH-022
- **Loại:** Happy path / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** last-active = C, default = A.
- **Bước thực hiện:** 1) Login lại.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Context = C (override default A).
- **Coverage hiện tại:** MISSING.

#### TC-AUTH-074 — Last-active trỏ clinic đã bị revoke → fallback default/list
- **Function:** AUTH-022
- **Loại:** Edge / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** last-active = D nhưng account đã bị revoke khỏi D.
- **Bước thực hiện:** 1) Login.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Bỏ qua last-active không hợp lệ → fallback default; nếu không có → trả list chọn clinic. KHÔNG cấp token clinic D.
- **Coverage hiện tại:** MISSING.

---

## 3. Khuyến nghị ưu tiên kiểm thử

1. **P0 trước tiên (đã ship hoặc đang migrate):** AUTH-001 (migrate khỏi clinic_code — verify lại login shape mới), AUTH-002, AUTH-003, AUTH-004, AUTH-006, AUTH-007.
2. **P0 multi-clinic (chưa ship — chuẩn bị test trước cho TASK-006):** AUTH-018, AUTH-020, AUTH-021 (đặc biệt cô lập RLS sau switch: TC-AUTH-070, revoke JWT cũ: TC-AUTH-069).
3. **Bảo mật xuyên suốt:** mọi endpoint yêu cầu quyền đều có case 401 (chưa auth) + 403 (thiếu permission); mọi thao tác chạm dữ liệu/clinic có case cô lập RLS.
4. **Cần xác minh lại bằng môi trường ổn định:** đối chiếu các TC gắn nhãn "(cần xác minh test file)" với `clinic-cms-merge/tests` và catalog TASK-003/006/017 để chốt Coverage chính xác.
