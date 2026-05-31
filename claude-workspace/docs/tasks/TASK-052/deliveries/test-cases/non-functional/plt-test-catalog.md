# Test Case Catalog — PLT · Quản trị Nền tảng (Platform admin / Super Admin)

**Nguồn:** function_list_data.py (group PLT) + clinic_management_function_list.md + clinic_management_saas_platform_model.md + clinic_management_system_design.md.
**Phạm vi:** 24 functions (PLT-001 → PLT-024).  **Tổng test case:** 60.  **Ngày:** 2026-05-30.

> **Bối cảnh nghiệp vụ (SaaS model §2, §6):** Lớp **Super Admin / Platform Operator** quản lý mọi clinic ở mức **metadata + subscription**, KHÔNG đọc PHI (patient/visit/Rx). Schema tách biệt vật lý: `platform_user` (không có `clinic_id`) vs `user` (gắn 1 clinic). Permission catalog `platform.*` không chứa `patient.read`. Cross-tenant trả 404 (không 403, tránh leak existence — system_design §). RLS bypass chỉ qua role `BYPASSRLS` ở Platform Console.
>
> **Lưu ý truy cập mã nguồn:** Toàn bộ group PLT có `status = TODO/IDEA` trong cả `function_list_data.py` lẫn `clinic_management_function_list.md` (PLT: 0 DONE / 22 TODO + 2 phase-2). Backend mã thực tế (`clinic-cms-merge/app/modules`) **không tìm thấy module platform/admin tương ứng** và thư mục test không có test file PLT. Do đó **Coverage = MISSING** cho toàn bộ — đây là spec test cho chức năng **chưa triển khai**. Khi TASK-026/TASK-027/TASK-030 hoàn thành cần map lại sang test file thật.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| PLT-001 | Platform user CRUD | TODO (TASK-026) | TC-PLT-001, TC-PLT-002, TC-PLT-003, TC-PLT-004 | MISSING |
| PLT-002 | Platform role CRUD (support/sales/finance/devops) | TODO (TASK-026) | TC-PLT-005, TC-PLT-006, TC-PLT-007 | MISSING |
| PLT-003 | Clinic list + filter | TODO (TASK-030) | TC-PLT-008, TC-PLT-009, TC-PLT-010 | MISSING |
| PLT-004 | Clinic detail panel (no PHI) | TODO (TASK-030) | TC-PLT-011, TC-PLT-012 | MISSING |
| PLT-005 | Tạo clinic + admin (3-step wizard) | TODO (TASK-030) | TC-PLT-013, TC-PLT-014, TC-PLT-015 | MISSING |
| PLT-006 | Convert trial → paid | TODO (TASK-030) | TC-PLT-016, TC-PLT-017 | MISSING |
| PLT-007 | Renew subscription | TODO (TASK-030) | TC-PLT-018 | MISSING |
| PLT-008 | Suspend clinic | TODO (TASK-030) | TC-PLT-019, TC-PLT-020, TC-PLT-021 | MISSING |
| PLT-009 | Reactivate clinic | TODO (TASK-030) | TC-PLT-022 | MISSING |
| PLT-010 | Archive clinic | TODO (TASK-030) | TC-PLT-023, TC-PLT-024 | MISSING |
| PLT-011 | Reset clinic admin password | TODO (TASK-030) | TC-PLT-025, TC-PLT-026 | MISSING |
| PLT-012 | Lead management | TODO (TASK-030) | TC-PLT-027, TC-PLT-028 | MISSING |
| PLT-013 | Convert lead → clinic | TODO (TASK-030) | TC-PLT-029 | MISSING |
| PLT-014 | Platform metrics dashboard (MRR/ARR/churn) | TODO (TASK-030) | TC-PLT-030, TC-PLT-031 | MISSING |
| PLT-015 | Subscription expiring view | TODO (TASK-030) | TC-PLT-032, TC-PLT-033 | MISSING |
| PLT-016 | Cross-clinic audit log (forensic) | TODO (TASK-030) | TC-PLT-034, TC-PLT-035 | MISSING |
| PLT-017 | System config (rate limits / feature flags) | TODO (TASK-030) | TC-PLT-036, TC-PLT-037 | MISSING |
| PLT-018 | Feature flag UI | TODO (TASK-030) | TC-PLT-038, TC-PLT-039 | MISSING |
| PLT-019 | PHI access prohibited | TODO (TASK-026) | TC-PLT-040, TC-PLT-041, TC-PLT-042, TC-PLT-043 | MISSING |
| PLT-020 | Impersonate clinic (Phase 2) | IDEA (v2) | TC-PLT-044, TC-PLT-045 | MISSING |
| PLT-021 | Data export per clinic | TODO (TASK-030) | TC-PLT-046, TC-PLT-047 | MISSING |
| PLT-022 | Internal notes | TODO (TASK-030) | TC-PLT-048, TC-PLT-049 | MISSING |
| PLT-023 | Activity feed platform-wide | TODO (TASK-030) | TC-PLT-050, TC-PLT-051 | MISSING |
| PLT-024 | Email super admin team | TODO (TASK-027) | TC-PLT-052, TC-PLT-053 | MISSING |

> Các TC bổ sung security/edge dùng chung: TC-PLT-054 → TC-PLT-060 (xem §2 cuối).

---

## 2. Chi tiết Test Cases

### TC-PLT-001 — Tạo platform user mới thành công
- **Function:** PLT-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập `super_admin` tại `/admin/users`.
- **Bước thực hiện:** 1) POST tạo platform_user với full_name, email, password, role=support, mfa_enabled=false. 2) Kiểm tra bản ghi `platform_user`.
- **Dữ liệu test:** `{ full_name: "NV Support", email: "sup@cura.io", password: "Str0ng!Pass", role: "support" }`
- **Kết quả mong đợi:** HTTP 201; bản ghi `platform_user` tồn tại; **không có cột `clinic_id`**; password lưu dạng hash; audit log ghi.
- **Coverage hiện tại:** MISSING (PLT-001 status TODO — TASK-026 chưa triển khai)

### TC-PLT-002 — Cập nhật platform user (bật MFA + ip_whitelist)
- **Function:** PLT-001
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tồn tại platform_user.
- **Bước thực hiện:** 1) PUT cập nhật mfa_enabled=true, ip_whitelist=["1.2.3.4"]. 2) Kiểm tra DB.
- **Dữ liệu test:** `{ mfa_enabled: true, ip_whitelist: ["1.2.3.4"] }`
- **Kết quả mong đợi:** HTTP 200; field cập nhật đúng; `ip_whitelist` lưu dạng JSON hợp lệ.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-003 — Tạo platform user với email trùng (negative)
- **Function:** PLT-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có platform_user email "sup@cura.io".
- **Bước thực hiện:** 1) POST tạo platform_user trùng email.
- **Dữ liệu test:** `{ email: "sup@cura.io", ... }`
- **Kết quả mong đợi:** HTTP 409 (hoặc 422); không tạo bản ghi trùng.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-004 — Clinic admin không truy cập được /admin/users (403)
- **Function:** PLT-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập role clinic (JWT audience = clinic).
- **Bước thực hiện:** 1) Gọi API platform user CRUD bằng clinic JWT.
- **Dữ liệu test:** Clinic JWT.
- **Kết quả mong đợi:** HTTP 403 (audience mismatch); không thao tác.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-005 — Gán đúng quyền cho 5 system platform role
- **Function:** PLT-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit
- **Tiền điều kiện:** Seed 5 role: super_admin, support, sales, finance, devops.
- **Bước thực hiện:** 1) Đọc permission catalog mỗi role. 2) Verify: super_admin=all; support=read clinic+audit; sales=lead+clinic.create; finance=billing read+invoice; devops=system config.
- **Dữ liệu test:** 5 role định nghĩa.
- **Kết quả mong đợi:** Mỗi role có đúng tập permission như spec; không role nào có `patient.read`.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-006 — Role finance KHÔNG suspend được clinic (negative quyền)
- **Function:** PLT-002
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập platform_user role=finance.
- **Bước thực hiện:** 1) Gọi API `platform.clinic.suspend`.
- **Dữ liệu test:** finance JWT.
- **Kết quả mong đợi:** HTTP 403; clinic không bị suspend.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-007 — Role sales tạo được clinic nhưng không xem audit log (edge quyền)
- **Function:** PLT-002
- **Loại:** Edge / Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** platform_user role=sales.
- **Bước thực hiện:** 1) POST tạo clinic → cho phép. 2) GET cross-clinic audit log → bị chặn.
- **Dữ liệu test:** sales JWT.
- **Kết quả mong đợi:** Tạo clinic 201; audit log 403.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-008 — Liệt kê toàn bộ clinic với filter status
- **Function:** PLT-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin; tồn tại clinic ở nhiều status.
- **Bước thực hiện:** 1) GET /admin/clinics?status=active&subscription_type=paid. 2) Kiểm tra danh sách + pagination + sort.
- **Dữ liệu test:** Filter `status=active`.
- **Kết quả mong đợi:** HTTP 200; trả đúng clinic active; có pagination metadata; super_admin thấy clinic của **mọi** tenant (bypass RLS hợp lệ).
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-009 — Filter + search kết hợp trả rỗng (edge)
- **Function:** PLT-003
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin.
- **Bước thực hiện:** 1) GET với filter không khớp clinic nào (specialty="nonexistent").
- **Dữ liệu test:** `specialty=nonexistent`.
- **Kết quả mong đợi:** HTTP 200; danh sách rỗng; total=0; không lỗi.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-010 — Cô lập: clinic user không gọi được API list-all-clinics (403)
- **Function:** PLT-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Clinic JWT (không phải platform).
- **Bước thực hiện:** 1) GET /admin/clinics bằng clinic JWT.
- **Dữ liệu test:** Clinic JWT.
- **Kết quả mong đợi:** HTTP 403; không liệt kê clinic khác (chống rò rỉ cross-tenant).
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-011 — Xem chi tiết clinic: metadata + counts, KHÔNG PHI
- **Function:** PLT-004
- **Loại:** Happy path / Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin; clinic có patient/visit data.
- **Bước thực hiện:** 1) GET /admin/clinics/:id. 2) Verify panel: status badge, subscription (plan/expires/countdown), stats (count user/patient/visit), action panel.
- **Dữ liệu test:** clinic_id hợp lệ.
- **Kết quả mong đợi:** HTTP 200; có **count** patient/visit nhưng **KHÔNG** trả tên BN / chi tiết visit / Rx.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-012 — Chi tiết clinic không tồn tại trả 404 (negative)
- **Function:** PLT-004
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** super_admin.
- **Bước thực hiện:** 1) GET /admin/clinics/<uuid-không-tồn-tại>.
- **Dữ liệu test:** UUID random.
- **Kết quả mong đợi:** HTTP 404.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-013 — Wizard tạo clinic + admin (atomic transaction)
- **Function:** PLT-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin.
- **Bước thực hiện:** 1) Step1 clinic info, Step2 subscription (paid/monthly), Step3 admin user. 2) Submit → kiểm tra clinic + admin user tạo trong **1 transaction** + trả temp password 1 lần.
- **Dữ liệu test:** clinic + subscription + admin email.
- **Kết quả mong đợi:** HTTP 201; clinic + clinic admin user tồn tại; temp password trả về đúng 1 lần; created_via=sales-led; audit log.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-014 — Rollback khi tạo admin user lỗi (atomicity, negative)
- **Function:** PLT-005
- **Loại:** Negative / Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin; Step3 admin email trùng/sai → ép lỗi tại bước cuối.
- **Bước thực hiện:** 1) Submit wizard với admin email lỗi. 2) Kiểm tra DB.
- **Dữ liệu test:** admin_email không hợp lệ.
- **Kết quả mong đợi:** HTTP 4xx; **clinic KHÔNG được tạo** (rollback toàn bộ transaction); không có bản ghi mồ côi.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-015 — Validation từng step của wizard (negative)
- **Function:** PLT-005
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin.
- **Bước thực hiện:** 1) Submit thiếu tên clinic / subscription_type sai / billing_cycle không hợp lệ.
- **Dữ liệu test:** `{ name: "", subscription_type: "x" }`
- **Kết quả mong đợi:** HTTP 422 với chi tiết lỗi từng field.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-016 — Convert trial → paid (chọn cycle + period_end + amount)
- **Function:** PLT-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic đang trial; super_admin/sales.
- **Bước thực hiện:** 1) Mở form Convert → chọn cycle=yearly, period_end, amount. 2) Submit → gọi SUB-012.
- **Dữ liệu test:** `{ billing_cycle: "yearly", current_period_end: "2027-05-30", amount: 12000000 }`
- **Kết quả mong đợi:** HTTP 200; subscription_type=paid; billing_cycle=yearly; current_period_end cập nhật; clinic_subscription_event ghi; audit log.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-017 — Convert clinic không phải trial (negative)
- **Function:** PLT-006
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic đã paid.
- **Bước thực hiện:** 1) Gọi Convert trên clinic đã paid.
- **Dữ liệu test:** clinic paid.
- **Kết quả mong đợi:** HTTP 409 / lỗi nghiệp vụ; không đổi state.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-018 — Manual renewal entry cập nhật current_period_end
- **Function:** PLT-007
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic paid; super_admin/finance.
- **Bước thực hiện:** 1) Nhập renewal (verify chuyển khoản) → cập nhật current_period_end (SUB-011).
- **Dữ liệu test:** `{ current_period_end: "+1 cycle" }`
- **Kết quả mong đợi:** HTTP 200; period_end gia hạn đúng cycle; event renewal ghi; audit log.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-019 — Suspend clinic với lý do bắt buộc
- **Function:** PLT-008
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic active; super_admin (perm `platform.clinic.suspend`).
- **Bước thực hiện:** 1) Suspend với reason + suspended_reason_visible. 2) Kiểm tra status + clinic_subscription_event.
- **Dữ liệu test:** `{ reason: "vi phạm ToS", suspended_reason_visible: true }`
- **Kết quả mong đợi:** HTTP 200; status=suspended; suspended_reason lưu; event type=suspended ghi; audit log.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-020 — Suspend không có lý do bị từ chối (negative)
- **Function:** PLT-008
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic active.
- **Bước thực hiện:** 1) Suspend với reason rỗng.
- **Dữ liệu test:** `{ reason: "" }`
- **Kết quả mong đợi:** HTTP 422; clinic vẫn active.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-021 — Clinic bị suspend: login + API trả 423 Locked
- **Function:** PLT-008
- **Loại:** Security / Edge
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** clinic status=suspended.
- **Bước thực hiện:** 1) Clinic user thử login. 2) Thử gọi API nghiệp vụ.
- **Dữ liệu test:** clinic user của clinic suspended.
- **Kết quả mong đợi:** HTTP 423 Locked (cả login lẫn API); login screen hiện lý do nếu suspended_reason_visible=true.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-022 — Reactivate clinic từ suspended → active
- **Function:** PLT-009
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic suspended.
- **Bước thực hiện:** 1) Reactivate (SUB-015). 2) Clinic user login lại.
- **Dữ liệu test:** clinic_id suspended.
- **Kết quả mong đợi:** HTTP 200; status=active; clinic user login OK; event ghi; audit log.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-023 — Archive clinic (đóng tài khoản)
- **Function:** PLT-010
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic active/suspended.
- **Bước thực hiện:** 1) Archive (SUB-016) → kiểm tra status=archived + trigger data export (PLT-021).
- **Dữ liệu test:** clinic_id.
- **Kết quả mong đợi:** HTTP 200; status=archived; clinic không login được; data export được trigger; audit log.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-024 — Archive là trạng thái cuối, không thao tác tiếp (edge)
- **Function:** PLT-010
- **Loại:** Edge / Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic archived.
- **Bước thực hiện:** 1) Thử renew/suspend trên clinic archived.
- **Dữ liệu test:** clinic archived.
- **Kết quả mong đợi:** HTTP 409; state không đổi.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-025 — Reset clinic admin password sinh temp password + notify
- **Function:** PLT-011
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic có admin user; super_admin/support.
- **Bước thực hiện:** 1) POST /platform/clinics/:id/reset-admin-password. 2) Kiểm tra temp password mới + audit + notify.
- **Dữ liệu test:** clinic_id.
- **Kết quả mong đợi:** HTTP 200; temp password sinh (hash lưu, hiện 1 lần); audit log; email/notify gửi clinic admin.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-026 — Reset password không truy cập được PHI (security)
- **Function:** PLT-011
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin.
- **Bước thực hiện:** 1) Reset admin password. 2) Verify response không chứa dữ liệu BN.
- **Dữ liệu test:** clinic_id.
- **Kết quả mong đợi:** Response chỉ chứa temp password + metadata; không PHI.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-027 — Liệt kê + filter lead từ landing
- **Function:** PLT-012
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin/sales; có lead.
- **Bước thực hiện:** 1) GET /admin/leads?status=new. 2) Click → drawer detail.
- **Dữ liệu test:** `status=new`.
- **Kết quả mong đợi:** HTTP 200; danh sách lead đúng filter; detail trả đầy đủ.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-028 — Lead management cấm clinic user (403)
- **Function:** PLT-012
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Clinic JWT.
- **Bước thực hiện:** 1) GET /admin/leads bằng clinic JWT.
- **Dữ liệu test:** Clinic JWT.
- **Kết quả mong đợi:** HTTP 403.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-029 — Convert lead → clinic (pre-fill wizard)
- **Function:** PLT-013
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** lead tồn tại; super_admin/sales.
- **Bước thực hiện:** 1) One-click convert (TENT-010) → wizard pre-fill từ lead. 2) Submit → clinic tạo + lead chuyển status=converted.
- **Dữ liệu test:** lead_id.
- **Kết quả mong đợi:** HTTP 201; clinic tạo; lead.status=converted; liên kết lead↔clinic.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-030 — Dashboard metrics tính đúng MRR/ARR/churn
- **Function:** PLT-014
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin; có dữ liệu subscription.
- **Bước thực hiện:** 1) GET /admin/dashboard (SUB-021). 2) Verify MRR, ARR, churn, conversion.
- **Dữ liệu test:** Seed: 3 clinic paid monthly + 1 churned.
- **Kết quả mong đợi:** HTTP 200; MRR=tổng monthly; ARR=MRR*12; churn rate đúng công thức.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-031 — Dashboard với 0 clinic (edge chia cho 0)
- **Function:** PLT-014
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Không có clinic paid.
- **Bước thực hiện:** 1) Tính churn/conversion khi mẫu số = 0.
- **Dữ liệu test:** 0 clinic.
- **Kết quả mong đợi:** Không lỗi chia 0; trả 0 hoặc null hợp lý.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-032 — View subscription sắp hết hạn (14 ngày, sort asc)
- **Function:** PLT-015
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin; clinic có expires trong & ngoài 14 ngày.
- **Bước thực hiện:** 1) GET /admin/subscriptions/expiring. 2) Verify chỉ clinic ≤14 ngày, sort asc, highlight theo độ gần.
- **Dữ liệu test:** clinic expires +5d, +13d, +30d.
- **Kết quả mong đợi:** HTTP 200; chỉ +5d & +13d; sort tăng dần.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-033 — Boundary đúng 14 ngày (edge)
- **Function:** PLT-015
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic expires đúng +14d và +15d.
- **Bước thực hiện:** 1) GET expiring view.
- **Dữ liệu test:** +14d, +15d.
- **Kết quả mong đợi:** +14d xuất hiện; +15d không (boundary inclusive 14).
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-034 — Cross-clinic audit log forensic search
- **Function:** PLT-016
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin/support (AUDIT-009); có audit data nhiều clinic.
- **Bước thực hiện:** 1) Search audit theo clinic_id/user/action/time range.
- **Dữ liệu test:** filter clinic A + action=login.
- **Kết quả mong đợi:** HTTP 200; trả audit của mọi clinic theo filter (super admin bypass RLS hợp lệ); read-only.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-035 — Audit log không hiển thị nội dung PHI (security)
- **Function:** PLT-016
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Audit có entry patient.read.
- **Bước thực hiện:** 1) Super admin xem audit entry liên quan patient.
- **Dữ liệu test:** audit entry entity_type=patient.
- **Kết quả mong đợi:** Chỉ metadata (entity_id, action, actor); KHÔNG hiện old_data/new_data chứa PHI cho platform_user.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-036 — Cập nhật system config (rate limits)
- **Function:** PLT-017
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin/devops.
- **Bước thực hiện:** 1) PUT /admin/system/config rate_limits per endpoint + JWT rotation. 2) Verify áp dụng.
- **Dữ liệu test:** `{ rate_limits: { "/login": "5/min" } }`
- **Kết quả mong đợi:** HTTP 200; config lưu; rate limit mới có hiệu lực; audit log.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-037 — Chỉ devops/super_admin sửa config (403)
- **Function:** PLT-017
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** platform_user role=sales.
- **Bước thực hiện:** 1) PUT system config bằng sales JWT.
- **Dữ liệu test:** sales JWT.
- **Kết quả mong đợi:** HTTP 403.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-038 — Feature flag toggle per clinic
- **Function:** PLT-018
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin; flag 'new_billing_v2'.
- **Bước thực hiện:** 1) Toggle flag ON cho clinic A. 2) Backend check flag → enable cho A, disable clinic B.
- **Dữ liệu test:** `{ flag: "new_billing_v2", clinic: A, enabled: true }`
- **Kết quả mong đợi:** HTTP 200; clinic A có flag, clinic B không (cô lập per-clinic).
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-039 — Feature flag global override (edge)
- **Function:** PLT-018
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** flag global=ON, per-clinic A=OFF.
- **Bước thực hiện:** 1) Resolve flag cho clinic A.
- **Dữ liệu test:** global ON, clinic A OFF.
- **Kết quả mong đợi:** Per-clinic override thắng global (clinic A=OFF) — theo precedence rule.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-040 — Platform JWT gọi /patients/:id bị chặn 403 (PHI prohibited)
- **Function:** PLT-019
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** super_admin platform JWT.
- **Bước thực hiện:** 1) GET /patients/:id bằng platform JWT.
- **Dữ liệu test:** platform JWT + patient_id.
- **Kết quả mong đợi:** HTTP 403 (audience mismatch); defense at multiple levels.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-041 — platform_user schema không có clinic_id (structural)
- **Function:** PLT-019
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Unit
- **Tiền điều kiện:** Schema platform_user.
- **Bước thực hiện:** 1) Introspect bảng platform_user.
- **Dữ liệu test:** Schema metadata.
- **Kết quả mong đợi:** Không có cột clinic_id; tách biệt vật lý với bảng `user`.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-042 — Permission catalog platform.* không chứa patient.read
- **Function:** PLT-019
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Unit
- **Tiền điều kiện:** Permission catalog.
- **Bước thực hiện:** 1) Liệt kê permission của mọi platform role.
- **Dữ liệu test:** Catalog.
- **Kết quả mong đợi:** Không permission nào = patient.read / visit.read / prescription.read.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-043 — Platform JWT gọi visit/prescription detail bị chặn (PHI)
- **Function:** PLT-019
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** platform JWT.
- **Bước thực hiện:** 1) GET /visits/:id và /prescriptions/:id bằng platform JWT.
- **Dữ liệu test:** platform JWT.
- **Kết quả mong đợi:** HTTP 403 cả hai; không rò rỉ PHI.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-044 — Impersonate flow cần clinic approve (Phase 2)
- **Function:** PLT-020
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** super_admin; clinic admin online (Phase 2 feature).
- **Bước thực hiện:** 1) Super admin 'Request support access' → notify clinic admin → clinic 'Allow 1h' → super admin nhận temp clinic JWT.
- **Dữ liệu test:** clinic_id.
- **Kết quả mong đợi:** Không cấp clinic JWT nếu chưa approve; JWT có TTL 1h; mọi action gắn nhãn 'impersonating' trong audit.
- **Coverage hiện tại:** MISSING (IDEA / Phase 2 — chưa triển khai)

### TC-PLT-045 — Impersonate không approve thì không truy cập (negative, Phase 2)
- **Function:** PLT-020
- **Loại:** Negative / Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Request gửi nhưng clinic chưa approve.
- **Bước thực hiện:** 1) Super admin thử dùng quyền clinic khi chưa được approve.
- **Dữ liệu test:** pending request.
- **Kết quả mong đợi:** HTTP 403; không có JWT clinic.
- **Coverage hiện tại:** MISSING (IDEA / Phase 2)

### TC-PLT-046 — Data export per clinic khi archive
- **Function:** PLT-021
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** clinic chuẩn bị archive.
- **Bước thực hiện:** 1) Archive trigger export (SUB-017). 2) Kiểm tra file export sinh ra.
- **Dữ liệu test:** clinic_id.
- **Kết quả mong đợi:** Export job tạo; file chứa dữ liệu đúng clinic đó; audit log.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-047 — Export chỉ chứa dữ liệu 1 clinic (cô lập, security)
- **Function:** PLT-021
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 clinic A,B có data.
- **Bước thực hiện:** 1) Export clinic A. 2) Kiểm tra nội dung.
- **Dữ liệu test:** clinic A.
- **Kết quả mong đợi:** File chỉ chứa data clinic A; KHÔNG lẫn dữ liệu clinic B (RLS/scope enforced).
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-048 — Tạo/đọc internal note về clinic
- **Function:** PLT-022
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin.
- **Bước thực hiện:** 1) PUT clinic.internal_notes. 2) GET clinic detail → note hiển thị cho super admin.
- **Dữ liệu test:** `{ internal_notes: "Khách quen, đã deposit 5tr" }`
- **Kết quả mong đợi:** HTTP 200; note lưu & hiển thị cho super admin.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-049 — Internal note KHÔNG lộ ra clinic user (security)
- **Function:** PLT-022
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** clinic có internal_notes.
- **Bước thực hiện:** 1) Clinic admin GET thông tin clinic của mình.
- **Dữ liệu test:** Clinic JWT.
- **Kết quả mong đợi:** Response KHÔNG chứa field internal_notes (chỉ super admin xem được).
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-050 — Activity feed platform-wide hiển thị 20 event gần nhất
- **Function:** PLT-023
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin; có events signup/convert/churn.
- **Bước thực hiện:** 1) GET activity feed. 2) Verify 20 event mới nhất, click → navigate clinic detail.
- **Dữ liệu test:** 25 events.
- **Kết quả mong đợi:** HTTP 200; đúng 20 event sort desc theo thời gian; link tới clinic.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-051 — Activity feed cấm clinic user (403)
- **Function:** PLT-023
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Clinic JWT.
- **Bước thực hiện:** 1) GET activity feed bằng clinic JWT.
- **Dữ liệu test:** Clinic JWT.
- **Kết quả mong đợi:** HTTP 403 (không lộ event của clinic khác).
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-052 — Email super admin team khi có event quan trọng
- **Function:** PLT-024
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Cấu hình team email.
- **Bước thực hiện:** 1) Trigger event clinic signup / payment failed. 2) Verify email gửi tới team.
- **Dữ liệu test:** event payment_failed.
- **Kết quả mong đợi:** Email gửi đúng team với context; lead urgent gửi ngay.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-053 — Event thường được gom vào daily digest (edge anti-spam)
- **Function:** PLT-024
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Nhiều event loại thường trong ngày.
- **Bước thực hiện:** 1) Trigger 10 event thường.
- **Dữ liệu test:** 10 normal events.
- **Kết quả mong đợi:** Không gửi 10 email rời; gom vào 1 daily digest.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-054 — Truy cập bất kỳ API platform khi chưa đăng nhập (401)
- **Function:** PLT-001..PLT-024 (chung)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) Gọi đại diện mỗi nhóm endpoint /admin/* không kèm Authorization.
- **Dữ liệu test:** Header rỗng.
- **Kết quả mong đợi:** HTTP 401 đồng nhất; không thao tác.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-055 — Token clinic (sai audience) gọi API platform (403)
- **Function:** PLT-001..PLT-024 (chung)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Clinic JWT hợp lệ nhưng sai audience.
- **Bước thực hiện:** 1) Gọi /admin/* bằng clinic JWT.
- **Dữ liệu test:** Clinic JWT.
- **Kết quả mong đợi:** HTTP 403 audience mismatch toàn bộ endpoint platform.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-056 — Cô lập cross-tenant: super admin set session clinic → chỉ thấy clinic đó
- **Function:** PLT-003, PLT-004, PLT-016, PLT-021 (RLS)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 clinic A,B; mô phỏng session clinic-scope.
- **Bước thực hiện:** 1) Set `app.current_clinic_id`=A. 2) Query bảng có clinic_id.
- **Dữ liệu test:** clinic A,B.
- **Kết quả mong đợi:** Chỉ trả dữ liệu A; clinic B bị RLS chặn; truy cập trực tiếp record B trả 404 (không 403).
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-057 — IP whitelist chặn platform_user ngoài dải cho phép (security)
- **Function:** PLT-001
- **Loại:** Security / Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** platform_user có ip_whitelist.
- **Bước thực hiện:** 1) Login từ IP ngoài whitelist.
- **Dữ liệu test:** IP không nằm trong whitelist.
- **Kết quả mong đợi:** Bị từ chối (403/401); login từ IP trong whitelist OK.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-058 — MFA bắt buộc cho platform_user có mfa_enabled (security)
- **Function:** PLT-001
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** platform_user mfa_enabled=true.
- **Bước thực hiện:** 1) Login chỉ password (không OTP).
- **Dữ liệu test:** Đúng password, thiếu OTP.
- **Kết quả mong đợi:** Yêu cầu OTP; chưa cấp token đầy đủ cho đến khi pass MFA.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-059 — Mọi hành động super admin đều ghi audit log (security)
- **Function:** PLT-005, PLT-008, PLT-011, PLT-017 (chung)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** super_admin.
- **Bước thực hiện:** 1) Thực hiện create clinic / suspend / reset password / sửa config. 2) Truy vấn audit log.
- **Dữ liệu test:** Chuỗi hành động.
- **Kết quả mong đợi:** Mỗi hành động có audit record: actor, action, target, timestamp, ip; bất biến (UPDATE/DELETE bị trigger chặn).
- **Coverage hiện tại:** MISSING (status TODO)

### TC-PLT-060 — Rate limit endpoint nhạy cảm (reset password, login) (security)
- **Function:** PLT-011, PLT-017
- **Loại:** Security / Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Rate limit cấu hình.
- **Bước thực hiện:** 1) Gọi reset-admin-password / login vượt ngưỡng liên tục.
- **Dữ liệu test:** N+1 request trong cửa sổ.
- **Kết quả mong đợi:** HTTP 429 sau khi vượt ngưỡng.
- **Coverage hiện tại:** MISSING (status TODO)

---

## 3. Ghi chú tổng hợp
- **100% function PLT (24/24)** được phủ ≥1 happy path; thêm Negative/Edge/Security cho các function trọng yếu (CRUD, suspend, wizard, PHI-prohibited, RLS).
- TC liên quan quyền có case **401** (TC-PLT-054) và **403** (TC-PLT-004, 006, 010, 028, 037, 040, 043, 049, 051, 055).
- TC đụng dữ liệu domain có case **cô lập clinic / RLS** (TC-PLT-008, 047, 056) — đặc biệt nhấn mạnh super admin chỉ xem metadata, không PHI.
- **PHI-prohibited (PLT-019)** là nhóm bảo mật cốt lõi: 4 lớp phòng thủ (schema không clinic_id, permission catalog, JWT audience, API 403) — TC-PLT-040..043.
- **Coverage = MISSING toàn bộ 60 TC** vì group PLT có status TODO/IDEA (PLT: 0 DONE / 22 TODO / 2 v2) và không tìm thấy module/test backend tương ứng trong `clinic-cms-merge`. Đây là **spec test cho chức năng chưa triển khai**; cần map sang test thật khi TASK-026 (PLT-001/002/019/024), TASK-027, TASK-030 hoàn thành.
