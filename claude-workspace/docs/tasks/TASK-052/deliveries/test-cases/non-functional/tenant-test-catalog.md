# Test Case Catalog — TENANT · Đăng ký & Onboarding phòng khám (Multi-tenant)

**Nguồn:** function_list_data.py (group TENANT, mã `TENT-xxx`) + clinic_management_function_list.md (§3) + system_design (§3.2/3.3 RLS, §15.3 Tenant Onboarding).
**Phạm vi:** 14 functions.  **Tổng test case:** 38.  **Ngày:** 2026-05-30.

> **LƯU Ý PHẠM VI (đã đối chiếu nguồn):** Group TENANT trong function list là **"Đăng ký & Onboarding phòng khám"** — luồng self-signup, email verification, sales-led tạo clinic, lead/contact, first-time wizard. Mã function là `TENT-001..014`. Cơ chế cô lập dữ liệu RLS được hiện thực ở tầng nền (`TenantMixin.clinic_id` + RLS policy `tenant_isolation` + session var `app.current_clinic_id`) và được tham chiếu như **tiền đề kiểm thử** cho mọi case onboarding (mỗi clinic mới phải bị cô lập), chứ không phải các function riêng của group này.

> **TRẠNG THÁI NGUỒN:** Bảng tổng hợp function list ghi `TENANT | 14 | 0 | 14` → **0/14 DONE, 14/14 TODO**. Tất cả TENT-xxx có `status=TODO` (TASK-006 / TASK-026 / TASK-029).

> **ĐỐI CHIẾU CODE/TEST THỰC TẾ:** Repo merge ở `E:/MyProject/clinic-cms-workspace/clinic-cms-merge` (KHÔNG phải `E:/MyProject/clinic-cms-merge`). Đã đối chiếu code + test thật:
> - **Onboarding wizard ĐÃ hiện thực** (khác spec function list): `app/modules/admin/services/onboarding_service.py` (start/get_state/submit_info/submit_users/submit_shifts/submit_inventory_csv/submit_services/skip_step/complete) + routes `/api/v1/onboarding/*` gated bằng permission `clinic.onboard`. Wizard là 6 step (info→users→shifts→inventory-csv→services→complete), KHÔNG phải 4 step / KHÔNG có self-signup public.
> - **Tạo clinic + uniqueness code:** `app/modules/admin/services/clinic_service.py::create_clinic` raise `ConflictError` nếu trùng `Clinic.code` (check `select(Clinic).where(Clinic.code==code)`).
> - **RLS cms_app role (BYPASSRLS=false):** `tests/integration/patients/test_rls_isolation_cms_app_role.py` — policy `USING ((clinic_id IS NULL) OR (clinic_id::text = current_setting('app.current_clinic_id', true)))`, skip nếu role có bypassrls; migration `alembic/versions/0003_setup_rls_policies.py` + `0004_create_app_role.py`.
> - **Settings/prefix:** `clinic_settings` (migration 0016) chứa `billing.invoice_prefix`, specialty preset vital_fields.
> - **Test có sẵn:** `tests/integration/admin/test_admin_e2e.py` — onboarding happy path/resume/skip/403, create_clinic 201/403, specialty preset (general=7 field, pediatric có head_circumference), `test_tenant_isolation_settings`, `test_settings_update_without_permission_403`.
> - **CHƯA hiện thực** (đúng status TODO nguồn): self-signup public form, email verification + token TTL/single-use, invite resend + rate limit, lead form, convert lead, reCAPTCHA → các TC tương ứng = MISSING.

> **Quy tắc nền tảng liên quan (từ system_design):**
> - **Atomic onboarding transaction** (§15.3 / TENT-003): INSERT clinic (status=pending) → clone 5 system role → INSERT user admin → INSERT subscription_event → sinh email_verify_token; rollback nếu bất kỳ bước nào fail.
> - **email_verify_token**: UUID, TTL 24h, single-use; dùng lại → 410 Gone; hết hạn → 410 (TENT-002, TENT-011, TENT-012).
> - **clinic.code UNIQUE global** (không scope theo clinic_id) vì dùng khi login (TENT-013).
> - **RLS** (§3.2/3.3): mọi bảng nghiệp vụ có `clinic_id`, policy `USING (clinic_id::text = current_setting('app.current_clinic_id', true))`; vai trò admin migration dùng BYPASSRLS riêng — ứng dụng KHÔNG chạy bằng bypass.
> - **reCAPTCHA v3** score < 0.5 → reject trên /signup và /contact (TENT-014).
> - **Rate limit** resend verify: 3 lần/giờ/email (TENT-012).

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| TENT-001 | Self-signup form (form công khai landing) | TODO | TC-TENT-001, TC-TENT-002, TC-TENT-003 | MISSING |
| TENT-002 | Email verification (gửi + click link) | TODO | TC-TENT-004, TC-TENT-005, TC-TENT-006 | MISSING |
| TENT-003 | Tạo clinic + admin user (atomic transaction) | TODO | TC-TENT-007, TC-TENT-008, TC-TENT-009 | PARTIAL |
| TENT-004 | Clone system roles cho clinic mới (5 role) | TODO | TC-TENT-010, TC-TENT-011 | PARTIAL |
| TENT-005 | First-time login wizard (sau lần login đầu) | TODO | TC-TENT-012, TC-TENT-013 | COVERED |
| TENT-006 | Chọn vital preset (5 preset specialty) | TODO | TC-TENT-014, TC-TENT-015 | COVERED |
| TENT-007 | Cấu hình prefix code (invoice/patient/visit + VAT) | TODO | TC-TENT-016, TC-TENT-017 | PARTIAL |
| TENT-008 | Lead form (Liên hệ tư vấn) → notify super admin | TODO | TC-TENT-018, TC-TENT-019 | MISSING |
| TENT-009 | Sales-led tạo clinic (super admin manual) | TODO | TC-TENT-020, TC-TENT-021, TC-TENT-022 | COVERED |
| TENT-010 | Convert lead → clinic (one-click pre-fill) | TODO | TC-TENT-023, TC-TENT-024 | MISSING |
| TENT-011 | Email verify token TTL 24h (single-use) | TODO | TC-TENT-025, TC-TENT-026, TC-TENT-027 | MISSING |
| TENT-012 | Invite resend (gửi lại email + rate limit) | TODO | TC-TENT-028, TC-TENT-029, TC-TENT-030 | MISSING |
| TENT-013 | Clinic code uniqueness (UNIQUE global) | TODO | TC-TENT-031, TC-TENT-032, TC-TENT-033 | PARTIAL |
| TENT-014 | reCAPTCHA on signup (chống bot spam) | TODO | TC-TENT-034, TC-TENT-035, TC-TENT-036 | MISSING |
| — (xuyên suốt) | Cô lập tenant/RLS cho clinic mới tạo | (nền tảng, ĐÃ test) | TC-TENT-037, TC-TENT-038 | COVERED |

**Tổng kết Coverage:** COVERED = 5 (TENT-005, 006, 009, + 2 case nền tảng RLS) · PARTIAL = 4 (TENT-003, 004, 007, 013) · MISSING = 6 (TENT-001, 002, 008, 010, 011, 012, 014 — các luồng public signup/email/lead/recaptcha chưa hiện thực).

> **Ghi chú đối sánh spec vs code:** Function list mô tả luồng **self-signup public + email verify** (TASK-006/026/029) nhưng codebase merge hiện thực theo hướng **admin/sales-led tạo clinic + onboarding wizard nội bộ** (gated `clinic.onboard`). Do đó các function "public-facing" (signup/email/lead/recaptcha) MISSING, còn phần "tạo clinic + wizard + preset + uniqueness + RLS" đã có code/test ở mức tương ứng. Coverage trên đếm theo function nguồn (14 + 1 dòng nền tảng); để khớp ràng buộc schema (covered+partial+missing=14 function nguồn) tính: COVERED=3 function nguồn (TENT-005/006/009), PARTIAL=4 (TENT-003/004/007/013), MISSING=7 (TENT-001/002/008/010/011/012/014); 2 case RLS nền tảng (TC-037/038) COVERED nhưng không gắn function nguồn nên không tính vào 14.

## 2. Chi tiết Test Cases

### TC-TENT-001 — Self-signup 3-step tạo clinic ở trạng thái pending_email_verification
- **Function:** TENT-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) + Integration (real DB)
- **Tiền điều kiện:** Trang /signup public (không auth); email/clinic_code chưa tồn tại.
- **Bước thực hiện:** 1) Điền step 1 (clinic info), step 2 (owner account), step 3 (confirm + tick ToS + reCAPTCHA). 2) POST /onboarding/signup. 3) Kiểm tra DB.
- **Dữ liệu test:** `{name:"PK Test", code:"PKTEST", specialty:"general", province:"HCM", owner:{name,email:"owner@pk.vn",password,phone}}`.
- **Kết quả mong đợi:** Tạo clinic `status=pending_email_verification`; gửi email verify; HTTP 201/200; response không lộ password hash.
- **Coverage hiện tại:** MISSING (TODO; cần xác minh test file khi codebase khả dụng).

### TC-TENT-002 — Thiếu/không hợp lệ trường bắt buộc bị validate
- **Function:** TENT-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration / E2E
- **Tiền điều kiện:** Endpoint signup sẵn sàng.
- **Bước thực hiện:** 1) POST signup thiếu email / password yếu / chưa tick ToS.
- **Dữ liệu test:** payload thiếu trường; password < policy.
- **Kết quả mong đợi:** HTTP 422 với lỗi từng trường; không tạo clinic.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-003 — Submit không cần auth (endpoint public)
- **Function:** TENT-001
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi Authorization header.
- **Bước thực hiện:** 1) POST /onboarding/signup không token hợp lệ.
- **Dữ liệu test:** request không auth.
- **Kết quả mong đợi:** Cho phép (endpoint public) — KHÔNG trả 401; nhưng vẫn enforce reCAPTCHA + rate limit.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-004 — Click link verify kích hoạt clinic + bắt đầu trial 14 ngày
- **Function:** TENT-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã signup; có email_verify_token hợp lệ, chưa dùng, chưa hết hạn.
- **Bước thực hiện:** 1) POST /onboarding/verify với token. 2) Kiểm tra clinic.
- **Dữ liệu test:** token UUID hợp lệ.
- **Kết quả mong đợi:** `clinic.status=active`, `trial_started_at=now()`, `current_period_end=now()+14d`; redirect /login với clinic_code prefilled; token đánh dấu used_at.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-005 — Verify với token không tồn tại bị từ chối
- **Function:** TENT-002
- **Loại:** Negative / Security
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** Token rác/không có trong DB.
- **Bước thực hiện:** 1) POST verify token không hợp lệ.
- **Dữ liệu test:** token ngẫu nhiên.
- **Kết quả mong đợi:** HTTP 400/404; clinic không đổi trạng thái.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-006 — Gửi email verify thành công sau signup
- **Function:** TENT-002
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (mock mailer)
- **Tiền điều kiện:** Signup hoàn tất.
- **Bước thực hiện:** 1) Theo dõi mailer. 2) Kiểm tra nội dung link /verify-email?token=xxx.
- **Dữ liệu test:** email owner.
- **Kết quả mong đợi:** Email gửi tới đúng owner, chứa token đúng định dạng và TTL.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-007 — Tạo clinic + admin trong 1 transaction atomic
- **Function:** TENT-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** DB sạch cho email/code test.
- **Bước thực hiện:** 1) Chạy luồng signup. 2) Kiểm tra clinic + 5 role clone + user admin + subscription_event + token đều tồn tại.
- **Dữ liệu test:** payload signup hợp lệ.
- **Kết quả mong đợi:** Đủ 5 thực thể; user admin có `must_change_password=false`; clinic `subscription_type=trial`.
- **Coverage hiện tại:** PARTIAL — `tests/integration/admin/test_admin_e2e.py::test_create_clinic_returns_201` tạo clinic qua admin route (KHÔNG qua self-signup; không kiểm subscription_event/token/email vì luồng public chưa hiện thực). `clinic_service.create_clinic` không sinh email_verify_token.

### TC-TENT-008 — Rollback toàn bộ khi 1 bước transaction fail
- **Function:** TENT-003
- **Loại:** Edge / Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Mô phỏng lỗi ở bước clone role hoặc insert user.
- **Bước thực hiện:** 1) Kích hoạt lỗi giữa transaction. 2) Kiểm tra DB.
- **Dữ liệu test:** điều kiện gây lỗi (vd vi phạm constraint).
- **Kết quả mong đợi:** Rollback toàn bộ — không có clinic/role/user/token mồ côi.
- **Coverage hiện tại:** MISSING (chưa có test rollback-on-failure cho luồng tạo clinic; cần bổ sung).

### TC-TENT-009 — Password admin được hash, không lưu plaintext
- **Function:** TENT-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration
- **Tiền điều kiện:** Signup với password do user đặt.
- **Bước thực hiện:** 1) Tạo clinic. 2) Đọc bản ghi user.
- **Dữ liệu test:** password rõ.
- **Kết quả mong đợi:** Cột password lưu hash (bcrypt/argon2), không plaintext; response không trả hash.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-010 — Clinic mới auto-clone đúng 5 system role
- **Function:** TENT-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có 5 system role template (Admin/Doctor/Nurse/Pharmacist/Receptionist).
- **Bước thực hiện:** 1) Tạo clinic. 2) Truy vấn role theo clinic_id mới.
- **Dữ liệu test:** clinic mới.
- **Kết quả mong đợi:** 5 role với `clinic_id=new`, `is_system=false`; permission mappings copy đầy đủ.
- **Coverage hiện tại:** PARTIAL — RBAC seed system role tồn tại (`alembic 0006_setup_rbac`, `0007_seed_permissions_and_roles`; `rbac_service`), nhưng chưa thấy test xác nhận create_clinic auto-clone đúng 5 role per-clinic; cần bổ sung assert role-count theo clinic mới.

### TC-TENT-011 — Custom role của clinic này không ảnh hưởng template hệ thống
- **Function:** TENT-004
- **Loại:** Security / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A đã clone role.
- **Bước thực hiện:** 1) Sửa permission role clone của A. 2) Kiểm tra system template + role của clinic B.
- **Dữ liệu test:** thay đổi permission ở A.
- **Kết quả mong đợi:** Template và clinic B không đổi (cô lập copy).
- **Coverage hiện tại:** MISSING (chưa có test cô lập custom-role giữa các clinic; cần bổ sung).

### TC-TENT-012 — Onboarding wizard chạy đủ luồng start→info→...→complete
- **Function:** TENT-005
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration / E2E (httpx)
- **Tiền điều kiện:** Clinic mới, có permission `clinic.onboard`; bảng `clinic_onboarding_state`.
- **Bước thực hiện:** 1) POST /onboarding/start. 2) GET /onboarding/state. 3) POST /onboarding/info → users → shifts → inventory-csv → services. 4) POST /onboarding/complete.
- **Dữ liệu test:** payload từng step.
- **Kết quả mong đợi:** State tiến đúng thứ tự; complete đánh dấu hoàn tất. (Lưu ý: code thực tế là 6 step nội bộ, không phải 4 step như spec.)
- **Coverage hiện tại:** COVERED — `tests/integration/admin/test_admin_e2e.py::test_onboarding_start`, `::test_onboarding_state_after_start`, `::test_onboarding_info_step`, `::test_onboarding_complete`, `::test_onboarding_inventory_csv_dry_run`.

### TC-TENT-013 — Resume wizard từ giữa chừng + skip step
- **Function:** TENT-005
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration / E2E
- **Tiền điều kiện:** Wizard đã hoàn tất vài step.
- **Bước thực hiện:** 1) Start, làm 2 step. 2) GET state → tiếp từ step 3. 3) Skip 1 step.
- **Dữ liệu test:** state dở dang.
- **Kết quả mong đợi:** State trả `current_step`/`completed_steps` đúng; skip advance không hoàn thành step đó.
- **Coverage hiện tại:** COVERED — `::test_onboarding_resume_from_middle` (+ skip qua `skip_step`/route).

### TC-TENT-014 — Specialty preset sinh đúng bộ vital field
- **Function:** TENT-006
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic với specialty preset (general / pediatric).
- **Bước thực hiện:** 1) Tạo/cấu hình clinic preset general. 2) Đọc vital fields. 3) Lặp với pediatric.
- **Dữ liệu test:** preset general & pediatric.
- **Kết quả mong đợi:** general = 7 field (bp_systolic/bp_diastolic/pulse/temperature/weight/height/spo2); pediatric có thêm `head_circumference`.
- **Coverage hiện tại:** COVERED — `::test_general_specialty_has_7_vital_fields`, `::test_pediatric_specialty_has_head_circumference`.

### TC-TENT-015 — Cô lập vital schema/settings theo clinic
- **Function:** TENT-006
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B có settings/preset khác nhau.
- **Bước thực hiện:** 1) Đọc settings/preset ở context clinic B.
- **Dữ liệu test:** settings A và B.
- **Kết quả mong đợi:** B chỉ thấy của B (RLS theo clinic_id).
- **Coverage hiện tại:** COVERED — `::test_tenant_isolation_settings` (đối chiếu cô lập settings giữa 2 clinic).

### TC-TENT-016 — Lưu prefix code + VAT vào clinic.settings
- **Function:** TENT-007
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Step 3 wizard.
- **Bước thực hiện:** 1) Nhập prefix HD/BN/KB + VAT 5%. 2) Submit. 3) Đọc lại.
- **Dữ liệu test:** `{invoice_prefix:"HD", patient_prefix:"BN", visit_prefix:"KB", vat:5}`.
- **Kết quả mong đợi:** Lưu vào `clinic.settings` JSONB; preview sinh đúng `HD-2026-..-0001`.
- **Coverage hiện tại:** PARTIAL — settings group `billing.invoice_prefix` tồn tại (migration 0016 + `test_get_settings_returns_all_groups`, `test_settings_update_preserves_other_fields`); chưa có test riêng cho prefix BN/KB + preview format.

### TC-TENT-017 — VAT ngoài khoảng 0-15% bị từ chối
- **Function:** TENT-007
- **Loại:** Negative / Edge
- **Ưu tiên:** P2
- **Layer:** Integration
- **Tiền điều kiện:** Slider VAT 0-15%.
- **Bước thực hiện:** 1) Gửi VAT = 20% qua API.
- **Dữ liệu test:** vat=20.
- **Kết quả mong đợi:** HTTP 422; không lưu.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-018 — Lead form public tạo lead status=new + notify super admin
- **Function:** TENT-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Trang /contact public.
- **Bước thực hiện:** 1) Submit form lead. 2) POST /api/v1/leads. 3) Kiểm tra lead + notify.
- **Dữ liệu test:** `{name,email,phone,clinic_name,scale,features[],message}`.
- **Kết quả mong đợi:** INSERT lead `status=new`; gửi email + dashboard cho super admin.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-019 — Lead form không yêu cầu auth nhưng có reCAPTCHA
- **Function:** TENT-008
- **Loại:** Security
- **Ưu tiên:** P2
- **Layer:** E2E
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) POST lead không auth, reCAPTCHA score thấp.
- **Dữ liệu test:** request bot-like.
- **Kết quả mong đợi:** Endpoint public (không 401) nhưng reject khi reCAPTCHA fail.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-020 — Super admin sales-led tạo clinic + admin (atomic)
- **Function:** TENT-009
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập super admin (platform role).
- **Bước thực hiện:** 1) POST tạo clinic qua admin route với name/code/specialty/contact. 2) Kiểm tra response 201 + bản ghi.
- **Dữ liệu test:** clinic name + unique code (+ tax_code optional). (Lưu ý: code hiện thực tạo clinic, chưa gắn subscription/password 12 ký tự như spec sales-led.)
- **Kết quả mong đợi:** HTTP 201; clinic tạo với code unique; `clinic_service.create_clinic` thành công.
- **Coverage hiện tại:** COVERED — `tests/integration/admin/test_admin_e2e.py::test_create_clinic_returns_201`. (Phần subscription + auto-gen password + show-once: MISSING — chưa hiện thực.)

### TC-TENT-021 — Non-super-admin không được tạo clinic (403)
- **Function:** TENT-009
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User clinic-side (không platform permission).
- **Bước thực hiện:** 1) Gọi POST tạo clinic bằng token thiếu permission.
- **Dữ liệu test:** token clinic admin thường (không quyền tạo clinic).
- **Kết quả mong đợi:** HTTP 403; không tạo clinic.
- **Coverage hiện tại:** COVERED — `::test_create_clinic_without_permission_403` (+ `::test_onboarding_without_permission_403`, `::test_settings_update_without_permission_403`).

### TC-TENT-022 — Gọi endpoint admin không auth trả 401
- **Function:** TENT-009
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) POST tạo clinic không Authorization header.
- **Dữ liệu test:** request không auth.
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** PARTIAL — 401 enforce chung qua auth middleware (cover gián tiếp bởi suite auth `test_auth_*`); chưa có assert 401 riêng cho route tạo clinic — nên bổ sung.

### TC-TENT-023 — Convert lead → clinic pre-fill thông tin + cập nhật lead
- **Function:** TENT-010
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lead status=new tồn tại.
- **Bước thực hiện:** 1) Click 'Convert sang clinic'. 2) Wizard pre-fill từ lead. 3) Điền subscription + tax. 4) Tạo.
- **Dữ liệu test:** lead id hợp lệ.
- **Kết quả mong đợi:** Tạo clinic thành công; `lead.status='converted'`, `lead.converted_clinic_id` link đúng.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-024 — Convert lead đã converted bị chặn (idempotent)
- **Function:** TENT-010
- **Loại:** Negative / Edge
- **Ưu tiên:** P2
- **Layer:** Integration
- **Tiền điều kiện:** Lead đã `status=converted`.
- **Bước thực hiện:** 1) Convert lại lead đó.
- **Dữ liệu test:** lead converted.
- **Kết quả mong đợi:** Bị từ chối (409/400); không tạo clinic trùng.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-025 — Token verify hợp lệ trong 24h dùng được 1 lần
- **Function:** TENT-011
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Token mới sinh, chưa dùng.
- **Bước thực hiện:** 1) Verify với token. 2) Kiểm tra used_at.
- **Dữ liệu test:** token TTL 24h.
- **Kết quả mong đợi:** Verify thành công; `used_at=now()`.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-026 — Token dùng lại lần 2 trả 410 Gone
- **Function:** TENT-011
- **Loại:** Negative / Security
- **Ưu tiên:** P0
- **Layer:** Integration
- **Tiền điều kiện:** Token đã có used_at.
- **Bước thực hiện:** 1) Verify lại cùng token.
- **Dữ liệu test:** token đã dùng.
- **Kết quả mong đợi:** HTTP 410 'Token đã được sử dụng'.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-027 — Token hết hạn (>24h) trả 410
- **Function:** TENT-011
- **Loại:** Edge / Security
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** Token có expires_at < now().
- **Bước thực hiện:** 1) Verify token hết hạn.
- **Dữ liệu test:** token quá hạn.
- **Kết quả mong đợi:** HTTP 410 'Token đã hết hạn — gửi lại email'.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-028 — Resend verify sinh token mới, vô hiệu token cũ
- **Function:** TENT-012
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** Đã có token cũ chưa dùng.
- **Bước thực hiện:** 1) POST /onboarding/resend-verify với email. 2) Kiểm tra token cũ + mới.
- **Dữ liệu test:** email đã signup.
- **Kết quả mong đợi:** Token cũ invalidate; token mới gửi qua email; audit resend_verify.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-029 — Rate limit resend 3 lần/giờ/email
- **Function:** TENT-012
- **Loại:** Security / Edge
- **Ưu tiên:** P1
- **Layer:** Integration / E2E
- **Tiền điều kiện:** Đã resend 3 lần trong 1 giờ.
- **Bước thực hiện:** 1) Gọi resend lần thứ 4.
- **Dữ liệu test:** cùng email, 4 lần liên tiếp.
- **Kết quả mong đợi:** HTTP 429; không gửi email thứ 4.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-030 — Resend cho email không tồn tại không lộ thông tin
- **Function:** TENT-012
- **Loại:** Security
- **Ưu tiên:** P2
- **Layer:** Integration
- **Tiền điều kiện:** Email chưa từng signup.
- **Bước thực hiện:** 1) Resend với email lạ.
- **Dữ liệu test:** email không tồn tại.
- **Kết quả mong đợi:** Phản hồi trung lập (không tiết lộ email tồn tại hay không); không gửi token.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-031 — clinic.code phải duy nhất toàn hệ thống
- **Function:** TENT-013
- **Loại:** Negative / Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã tồn tại clinic code "PKTEST".
- **Bước thực hiện:** 1) Signup/tạo clinic mới cùng code "PKTEST".
- **Dữ liệu test:** code trùng.
- **Kết quả mong đợi:** Bị từ chối ở API + DB UNIQUE constraint (global, không scope clinic_id); HTTP 409.
- **Coverage hiện tại:** PARTIAL — `clinic_service.create_clinic` raise `ConflictError` khi `Clinic.code` trùng (logic có thật), nhưng chưa thấy test e2e khẳng định 409 cho code trùng; nên bổ sung `test_create_clinic_duplicate_code_409`.

### TC-TENT-032 — Real-time check availability khi gõ code
- **Function:** TENT-013
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** E2E / Manual UI
- **Tiền điều kiện:** Form signup.
- **Bước thực hiện:** 1) Gõ code đã tồn tại → check; 2) gõ code mới → check.
- **Dữ liệu test:** code tồn tại và code mới.
- **Kết quả mong đợi:** API check trả 'taken' cho code tồn tại, 'available' cho code mới.
- **Coverage hiện tại:** MISSING (endpoint real-time availability cho self-signup chưa hiện thực).

### TC-TENT-033 — Code uniqueness an toàn race-condition khi 2 signup đồng thời
- **Function:** TENT-013
- **Loại:** Edge / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hai request signup cùng code gần như đồng thời.
- **Bước thực hiện:** 1) Gửi song song 2 signup cùng code.
- **Dữ liệu test:** cùng code, 2 luồng.
- **Kết quả mong đợi:** Đúng 1 thành công, 1 bị DB UNIQUE chặn (không tạo 2 clinic cùng code).
- **Coverage hiện tại:** MISSING (chưa có test concurrency cho clinic.code; check hiện là select-then-insert, nên xác minh có UNIQUE constraint DB chống race).

### TC-TENT-034 — reCAPTCHA score thấp bị reject trên /signup
- **Function:** TENT-014
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration / E2E
- **Tiền điều kiện:** reCAPTCHA v3 bật, verify score.
- **Bước thực hiện:** 1) Signup với token reCAPTCHA score < 0.5.
- **Dữ liệu test:** mock score 0.3.
- **Kết quả mong đợi:** Reject (HTTP 400/403); không tạo clinic.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-035 — reCAPTCHA score cao cho phép signup
- **Function:** TENT-014
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration
- **Tiền điều kiện:** reCAPTCHA bật.
- **Bước thực hiện:** 1) Signup với score >= 0.5.
- **Dữ liệu test:** mock score 0.9.
- **Kết quả mong đợi:** Cho phép tiếp tục luồng signup.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-036 — Thiếu/sai reCAPTCHA token bị chặn
- **Function:** TENT-014
- **Loại:** Negative / Security
- **Ưu tiên:** P1
- **Layer:** Integration / E2E
- **Tiền điều kiện:** reCAPTCHA bắt buộc.
- **Bước thực hiện:** 1) Signup không có / sai reCAPTCHA token.
- **Dữ liệu test:** token rỗng/sai.
- **Kết quả mong đợi:** Reject (HTTP 400); không tạo clinic.
- **Coverage hiện tại:** MISSING (cần xác minh test file).

### TC-TENT-037 — Dữ liệu clinic mới bị cô lập RLS khỏi clinic khác
- **Function:** — (nền tảng, áp cho mọi clinic onboard)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Onboard 2 clinic A và B; mỗi clinic có dữ liệu nghiệp vụ.
- **Bước thực hiện:** 1) SET `app.current_clinic_id=A`. 2) SELECT bảng nghiệp vụ. 3) Kiểm tra không thấy dữ liệu B.
- **Dữ liệu test:** dữ liệu A và B.
- **Kết quả mong đợi:** Policy `USING ((clinic_id IS NULL) OR (clinic_id::text = current_setting('app.current_clinic_id', true)))` chỉ trả dữ liệu A; 0 bản ghi B.
- **Coverage hiện tại:** COVERED — `tests/integration/patients/test_rls_isolation_cms_app_role.py` (seed clinic A/B + patient, SET ROLE cms_app + SET LOCAL app.current_clinic_id, assert không thấy dữ liệu clinic khác). Migration `alembic 0003_setup_rls_policies`.

### TC-TENT-038 — Ứng dụng không chạy bằng vai trò BYPASSRLS
- **Function:** — (nền tảng)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Vai trò DB của app khác vai trò migration/admin.
- **Bước thực hiện:** 1) Kiểm tra `rolbypassrls=false` cho role app. 2) Thử SELECT chéo clinic không set context.
- **Dữ liệu test:** vai trò DB app + dữ liệu nhiều clinic.
- **Kết quả mong đợi:** Role `cms_app` có `rolbypassrls=false`; RLS được enforce (test skip nếu role bị bypass).
- **Coverage hiện tại:** COVERED — `test_rls_isolation_cms_app_role.py` query `SELECT rolname, rolbypassrls FROM pg_roles WHERE rolname='cms_app'` và pytest.skip nếu bypassrls=true; migration `alembic 0004_create_app_role`. (Fail-safe khi không set context: nên bổ sung assert trả rỗng.)
