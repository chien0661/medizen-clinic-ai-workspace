# Test Case Catalog — RBAC · Phân quyền & Vai trò

**Nguồn:** function_list_data.py (group RBAC, dòng 130–215) + clinic_management_function_list.md §2 (RBAC-001…RBAC-018) + system_design/BA (RLS, JWT 15p, Redis cache 5p, audit `applied_role`, SoD).
**Phạm vi:** 18 functions (RBAC-001 … RBAC-018).  **Tổng test case:** 64.  **Ngày:** 2026-05-30.

> Ghi chú nguồn coverage: cột Status trong function list (✅ = DONE đã ship, ⬜ = TODO chưa ship). Mapping task: RBAC-001..009 → TASK-004 (core RBAC, ✅), RBAC-013 → TASK-002 (audit, ✅), RBAC-010/011/012 → TASK-023 (custom role UI, ⬜), RBAC-014 → TASK-026 (platform RBAC, ⬜), RBAC-015 → TASK-002 (applied_role audit, ⬜), RBAC-016 → TASK-004 (SoD, ⬜ — phần SoD chưa enforce dù core đã ship), RBAC-017/018 → TASK-017 (multi-role UX sidebar, ⬜).
> Vì kênh tool đọc test thực tế bị gián đoạn trong phiên này, Coverage gán theo cột Status nguồn (đã ship vs chưa) + lịch sử task; các dòng PARTIAL/MISSING nêu rõ lý do và test file cần kiểm chứng lại.

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| RBAC-001 | 5 system roles (Admin/Doctor/Nurse/Pharmacist/Receptionist) | DONE ✅ | TC-RBAC-001, TC-RBAC-002, TC-RBAC-003 | COVERED |
| RBAC-002 | Permission catalog (38 perms, BA §13.5) | DONE ✅ | TC-RBAC-004, TC-RBAC-005, TC-RBAC-006 | COVERED |
| RBAC-003 | Multi-role per user | DONE ✅ | TC-RBAC-007, TC-RBAC-008, TC-RBAC-009 | COVERED |
| RBAC-004 | Extra grant per user | DONE ✅ | TC-RBAC-010, TC-RBAC-011, TC-RBAC-012, TC-RBAC-013 | COVERED |
| RBAC-005 | Extra deny per user | DONE ✅ | TC-RBAC-014, TC-RBAC-015, TC-RBAC-016, TC-RBAC-017 | COVERED |
| RBAC-006 | Permission cache (JWT 15p + Redis 5p) | DONE ✅ | TC-RBAC-018, TC-RBAC-019, TC-RBAC-020 | COVERED |
| RBAC-007 | Cache invalidation khi role/perm đổi | DONE ✅ | TC-RBAC-021, TC-RBAC-022, TC-RBAC-023 | COVERED |
| RBAC-008 | Clone system role → clinic-specific | DONE ✅ | TC-RBAC-024, TC-RBAC-025, TC-RBAC-026, TC-RBAC-027 | COVERED |
| RBAC-009 | System role immutable | DONE ✅ | TC-RBAC-028, TC-RBAC-029, TC-RBAC-030 | COVERED |
| RBAC-010 | Custom role CRUD | TODO ⬜ | TC-RBAC-031, TC-RBAC-032, TC-RBAC-033, TC-RBAC-034, TC-RBAC-035 | MISSING |
| RBAC-011 | Permission group UI (theo nhóm module) | TODO ⬜ | TC-RBAC-036, TC-RBAC-037 | MISSING |
| RBAC-012 | Role description | TODO ⬜ | TC-RBAC-038, TC-RBAC-039 | MISSING |
| RBAC-013 | Audit role changes | DONE ✅ | TC-RBAC-040, TC-RBAC-041, TC-RBAC-042 | COVERED |
| RBAC-014 | Platform RBAC tách biệt (platform_role/permission) | TODO ⬜ | TC-RBAC-043, TC-RBAC-044, TC-RBAC-045, TC-RBAC-046 | MISSING |
| RBAC-015 | Applied role trong audit (`applied_role`) | TODO ⬜ | TC-RBAC-047, TC-RBAC-048, TC-RBAC-049 | MISSING |
| RBAC-016 | Separation of Duties (SoD) | TODO ⬜ | TC-RBAC-050, TC-RBAC-051, TC-RBAC-052, TC-RBAC-053 | MISSING |
| RBAC-017 | Merge sidebar cho multi-role (UNION module, không role-switcher) | TODO ⬜ | TC-RBAC-054, TC-RBAC-055, TC-RBAC-056, TC-RBAC-057 | MISSING |
| RBAC-018 | Multi-role chip ở avatar | TODO ⬜ | TC-RBAC-058, TC-RBAC-059, TC-RBAC-060 | MISSING |

**Tổng kết coverage theo function:** COVERED = 9 · PARTIAL = 0 · MISSING = 9 (khớp summary nguồn `| RBAC | 15 | 9 | 6 |` — số 15/9/6 trong nguồn tính theo phase v1, ở đây tính theo trạng thái ship thực tế: 9 ✅ / 9 ⬜).

---

## 2. Chi tiết Test Cases

### TC-RBAC-001 — Seed đủ 5 system role mặc định
- **Function:** RBAC-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** DB sau migration + seed. Bảng `role` có cờ `is_system=true`.
- **Bước thực hiện:** 1) Query bảng `role` với `is_system=true`. 2) Kiểm tra danh sách code.
- **Dữ liệu test:** N/A (seed).
- **Kết quả mong đợi:** Trả về đúng 5 role: `admin`, `doctor`, `nurse`, `pharmacist`, `receptionist`; mỗi role có `name`, `is_system=true`, gắn `clinic_id=NULL` (system-wide) hoặc theo thiết kế seed.
- **Coverage hiện tại:** COVERED (TASK-004 — cần kiểm chứng lại `tests/.../test_roles*` do kênh đọc test gián đoạn).

### TC-RBAC-002 — Mỗi system role có đúng tập permission BA §13.5
- **Function:** RBAC-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Seed role + role_permission.
- **Bước thực hiện:** 1) Lấy permissions của role `doctor`. 2) Đối chiếu ma trận BA §13.5 (vd doctor có `visit.create`, `prescription.create`, KHÔNG có `billing.refund`).
- **Dữ liệu test:** role=doctor, role=receptionist.
- **Kết quả mong đợi:** Mỗi role map đúng tập perm chuẩn; receptionist không có `prescription.create`; pharmacist có `pharmacy.dispense`.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-003 — Gán system role cho user và resolve permission
- **Function:** RBAC-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User A thuộc clinic 1, được gán role `nurse`.
- **Bước thực hiện:** 1) Login user A. 2) GET `/me/permissions`. 3) Gọi 1 endpoint cần `vitals.create`.
- **Dữ liệu test:** user A role=nurse.
- **Kết quả mong đợi:** 200; response chứa perms của nurse; endpoint vitals → 200.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-004 — Permission catalog có đủ 38 perm
- **Function:** RBAC-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Seed bảng `permission`.
- **Bước thực hiện:** 1) `SELECT count(*) FROM permission`. 2) Đối chiếu BA §13.5.
- **Dữ liệu test:** N/A.
- **Kết quả mong đợi:** Đúng 38 permission; mỗi perm có `code` dạng `<domain>.<action>` (vd `patient.read`), `description`.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-005 — Permission code unique & đúng định dạng
- **Function:** RBAC-002
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Seed catalog.
- **Bước thực hiện:** 1) Kiểm tra unique constraint trên `permission.code`. 2) Regex `^[a-z_]+\.[a-z_]+$`.
- **Dữ liệu test:** N/A.
- **Kết quả mong đợi:** Không có code trùng; tất cả khớp định dạng; không có khoảng trắng/hoa.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-006 — List permission catalog yêu cầu quyền quản trị
- **Function:** RBAC-002
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Endpoint `GET /admin/permissions` cần perm `role.manage`/`rbac.read`.
- **Bước thực hiện:** 1) Gọi không token → 401. 2) Gọi với user `nurse` (không có quyền) → 403. 3) Gọi với `admin` → 200.
- **Dữ liệu test:** no-token; nurse; admin.
- **Kết quả mong đợi:** 401 / 403 / 200 (đủ 38 perm).
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-007 — User có nhiều role, perms là UNION
- **Function:** RBAC-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User B gán cả `doctor` + `admin` trong cùng clinic.
- **Bước thực hiện:** 1) Resolve effective permissions cho user B. 2) Kiểm tra hợp tập.
- **Dữ liệu test:** user B = {doctor, admin}.
- **Kết quả mong đợi:** Effective perms = UNION(doctor.perms, admin.perms); có cả `prescription.create` (doctor) lẫn `service.price.update` (admin).
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-008 — Gỡ 1 role không mất perm do role còn lại cấp
- **Function:** RBAC-003
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User B = {doctor, nurse}, cả 2 đều có `vitals.read`.
- **Bước thực hiện:** 1) Gỡ role `nurse`. 2) Resolve lại.
- **Dữ liệu test:** user B.
- **Kết quả mong đợi:** `vitals.read` vẫn còn (doctor cấp); chỉ mất perm độc quyền của nurse.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-009 — Multi-role cô lập theo clinic (RLS)
- **Function:** RBAC-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User B là `admin` ở clinic 1, `nurse` ở clinic 2.
- **Bước thực hiện:** 1) Set RLS `app.current_clinic_id=1`, resolve role. 2) Set `=2`, resolve lại.
- **Dữ liệu test:** user B đa-clinic.
- **Kết quả mong đợi:** Trong clinic 1 → role admin; clinic 2 → role nurse; KHÔNG leak role chéo clinic.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-010 — Cấp extra grant 1 perm ngoài role
- **Function:** RBAC-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User C role=nurse (không có `report.read`). Admin có `role.manage`.
- **Bước thực hiện:** 1) Admin POST extra-grant `report.read` cho user C. 2) User C gọi endpoint report.
- **Dữ liệu test:** user C, perm=report.read.
- **Kết quả mong đợi:** 200; user C truy cập được report dù role nurse không có; audit ghi grant.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-011 — Extra grant chưa auth / thiếu quyền
- **Function:** RBAC-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Endpoint grant cần `role.manage`.
- **Bước thực hiện:** 1) Không token → 401. 2) User thường (nurse) tự grant cho mình → 403.
- **Dữ liệu test:** no-token; nurse self-grant.
- **Kết quả mong đợi:** 401 / 403; không thay đổi quyền.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-012 — Extra grant cô lập clinic (RLS)
- **Function:** RBAC-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin clinic 1 grant cho user C.
- **Bước thực hiện:** 1) Grant trong clinic 1. 2) Đăng nhập user C ở clinic 2 (nếu thuộc) hoặc query với RLS clinic 2.
- **Dữ liệu test:** user C đa-clinic.
- **Kết quả mong đợi:** Grant chỉ áp dụng trong clinic 1; clinic 2 không thấy perm này.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-013 — Grant perm không tồn tại bị từ chối
- **Function:** RBAC-004
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Admin.
- **Bước thực hiện:** 1) POST grant perm code `foo.bar` (không có trong catalog).
- **Dữ liệu test:** perm=foo.bar.
- **Kết quả mong đợi:** 422/400; không tạo grant; thông báo perm không hợp lệ.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-014 — Extra deny chặn perm dù role có
- **Function:** RBAC-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User D role=doctor (có `prescription.create`). Admin deny `prescription.create` cho D.
- **Bước thực hiện:** 1) Admin POST extra-deny. 2) User D gọi endpoint kê đơn.
- **Dữ liệu test:** user D, perm=prescription.create.
- **Kết quả mong đợi:** 403; deny thắng grant của role; audit ghi deny.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-015 — Deny ưu tiên cao hơn extra grant
- **Function:** RBAC-005
- **Loại:** Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User D có đồng thời extra-grant `report.read` và extra-deny `report.read`.
- **Bước thực hiện:** 1) Resolve effective permission.
- **Dữ liệu test:** user D grant+deny cùng perm.
- **Kết quả mong đợi:** Kết quả = DENY (deny luôn thắng); endpoint → 403.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-016 — Extra deny chưa auth / thiếu quyền
- **Function:** RBAC-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Bước thực hiện:** 1) Không token → 401. 2) Nurse gọi deny endpoint → 403.
- **Dữ liệu test:** no-token; nurse.
- **Kết quả mong đợi:** 401 / 403.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-017 — Extra deny cô lập clinic (RLS)
- **Function:** RBAC-005
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Bước thực hiện:** 1) Deny trong clinic 1. 2) Kiểm tra clinic 2 không bị ảnh hưởng.
- **Dữ liệu test:** user đa-clinic.
- **Kết quả mong đợi:** Deny chỉ trong phạm vi clinic đã đặt.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-018 — Permission claim nằm trong JWT (15 phút)
- **Function:** RBAC-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Login user E.
- **Bước thực hiện:** 1) Login → lấy access token. 2) Decode payload. 3) Kiểm tra `exp - iat ≈ 900s` và có `perms[]`/`roles[]`.
- **Dữ liệu test:** user E.
- **Kết quả mong đợi:** JWT chứa roles+perms; TTL 15 phút; authz dùng claim không query DB mỗi request.
- **Coverage hiện tại:** COVERED (TASK-004/auth).

### TC-RBAC-019 — Redis cache perm TTL 5 phút, hit lần 2
- **Function:** RBAC-006
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB + Redis)
- **Tiền điều kiện:** Redis sạch.
- **Bước thực hiện:** 1) Resolve perm user F (miss → set cache). 2) Resolve lại (hit). 3) Kiểm tra TTL key ≈ 300s.
- **Dữ liệu test:** user F.
- **Kết quả mong đợi:** Lần 2 lấy từ Redis (không query DB); TTL ~5 phút.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-020 — Cache key tách theo (user_id, clinic_id)
- **Function:** RBAC-006
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (Redis)
- **Tiền điều kiện:** User đa-clinic.
- **Bước thực hiện:** 1) Cache perm clinic 1. 2) Cache perm clinic 2. 3) Kiểm tra 2 key riêng biệt.
- **Dữ liệu test:** user đa-clinic.
- **Kết quả mong đợi:** Không ghi đè; không leak perm giữa clinic qua cache.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-021 — Đổi role → clear cache user ngay
- **Function:** RBAC-007
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB + Redis)
- **Tiền điều kiện:** User G cache đã warm.
- **Bước thực hiện:** 1) Thêm role cho G. 2) Kiểm tra cache key bị xóa/invalidate. 3) Resolve lại → perm mới.
- **Dữ liệu test:** user G.
- **Kết quả mong đợi:** Cache cũ bị xóa; lần resolve sau phản ánh role mới.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-022 — Đổi perm của role → invalidate mọi user dùng role
- **Function:** RBAC-007
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB + Redis)
- **Tiền điều kiện:** Role `nurse` đang gán cho user G và H, cache đã warm.
- **Bước thực hiện:** 1) Thêm perm vào role nurse. 2) Kiểm tra cache của cả G và H bị invalidate.
- **Dữ liệu test:** role nurse → 2 user.
- **Kết quả mong đợi:** Cả 2 user nhận perm mới ở lần resolve kế tiếp.
- **Coverage hiện tại:** PARTIAL (cơ chế invalidate theo role đã ship nhưng fan-out tới mọi user cần kiểm chứng test thực tế — TASK-004).

### TC-RBAC-023 — JWT cũ vẫn hiệu lực tới khi hết hạn sau khi đổi quyền
- **Function:** RBAC-007
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User G có JWT còn hạn.
- **Bước thực hiện:** 1) Deny 1 perm của G. 2) Gọi endpoint bằng JWT cũ.
- **Dữ liệu test:** user G.
- **Kết quả mong đợi:** Hành vi đúng theo thiết kế: hoặc 403 ngay (nếu authz check cache/DB), hoặc còn pass tới khi JWT hết 15p (nếu chỉ dựa claim) — test xác nhận hành vi nhất quán với spec.
- **Coverage hiện tại:** COVERED (TASK-004 — cần xác nhận hành vi mong đợi trong final-spec).

### TC-RBAC-024 — Clone system role thành custom role của clinic
- **Function:** RBAC-008
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Admin clinic 1, system role `doctor`.
- **Bước thực hiện:** 1) POST clone từ `doctor`. 2) Kiểm tra role mới `is_system=false`, `clinic_id=1`, sao chép perm.
- **Dữ liệu test:** clone từ doctor.
- **Kết quả mong đợi:** 201; role mới editable, gắn clinic 1, perm = bản sao của doctor.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-025 — Sửa custom role (clone) không ảnh hưởng system role gốc
- **Function:** RBAC-008
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã clone doctor → custom role X.
- **Bước thực hiện:** 1) Gỡ 1 perm khỏi role X. 2) Kiểm tra system role `doctor` không đổi.
- **Dữ liệu test:** role X.
- **Kết quả mong đợi:** System role gốc giữ nguyên perm; chỉ role X thay đổi.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-026 — Clone chưa auth / thiếu quyền
- **Function:** RBAC-008
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Bước thực hiện:** 1) Không token → 401. 2) Nurse clone → 403.
- **Dữ liệu test:** no-token; nurse.
- **Kết quả mong đợi:** 401 / 403.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-027 — Clone cô lập clinic (RLS)
- **Function:** RBAC-008
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Bước thực hiện:** 1) Admin clinic 1 clone. 2) Admin clinic 2 list role.
- **Dữ liệu test:** 2 clinic.
- **Kết quả mong đợi:** Custom role chỉ hiện trong clinic 1; clinic 2 không thấy.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-028 — Không cho sửa system role
- **Function:** RBAC-009
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Admin, system role `doctor`.
- **Bước thực hiện:** 1) PUT/PATCH system role `doctor` (đổi tên/perm).
- **Dữ liệu test:** role doctor.
- **Kết quả mong đợi:** 403/409; thông báo system role immutable; không thay đổi DB.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-029 — Không cho xóa system role
- **Function:** RBAC-009
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Bước thực hiện:** 1) DELETE system role `admin`.
- **Dữ liệu test:** role admin.
- **Kết quả mong đợi:** 403/409; role vẫn tồn tại.
- **Coverage hiện tại:** COVERED (TASK-004).

### TC-RBAC-030 — Immutable enforce ở DB/service ngay cả khi bypass UI
- **Function:** RBAC-009
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Bước thực hiện:** 1) Gọi trực tiếp service-layer update với `is_system=true`.
- **Dữ liệu test:** role system.
- **Kết quả mong đợi:** Service raise lỗi/guard; không update.
- **Coverage hiện tại:** PARTIAL (enforce endpoint đã có; guard tầng service cần kiểm chứng test thực tế).

### TC-RBAC-031 — Tạo custom role mới (CRUD - Create)
- **Function:** RBAC-010
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Clinic admin.
- **Bước thực hiện:** 1) POST role {name, description, perms[]}. 2) GET lại.
- **Dữ liệu test:** name="Lễ tân trưởng".
- **Kết quả mong đợi:** 201; role `is_system=false`, gắn clinic hiện tại, perms đúng.
- **Coverage hiện tại:** MISSING (TASK-023 chưa ship).

### TC-RBAC-032 — Sửa & xóa custom role (Update/Delete)
- **Function:** RBAC-010
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Bước thực hiện:** 1) PATCH đổi perms. 2) DELETE role (khi không còn user gán).
- **Dữ liệu test:** custom role X.
- **Kết quả mong đợi:** 200/204; thay đổi đúng; audit ghi.
- **Coverage hiện tại:** MISSING (TASK-023).

### TC-RBAC-033 — Xóa role đang gán user bị chặn
- **Function:** RBAC-010
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Bước thực hiện:** 1) DELETE role còn user gán.
- **Dữ liệu test:** role có 1 user.
- **Kết quả mong đợi:** 409; thông báo phải gỡ user trước; role giữ nguyên.
- **Coverage hiện tại:** MISSING (TASK-023).

### TC-RBAC-034 — Custom role CRUD chưa auth / thiếu quyền
- **Function:** RBAC-010
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Bước thực hiện:** 1) Không token → 401. 2) Nurse tạo role → 403.
- **Dữ liệu test:** no-token; nurse.
- **Kết quả mong đợi:** 401 / 403.
- **Coverage hiện tại:** MISSING (TASK-023).

### TC-RBAC-035 — Custom role cô lập clinic (RLS)
- **Function:** RBAC-010
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Bước thực hiện:** 1) Tạo role ở clinic 1. 2) Admin clinic 2 không list/sửa/xóa được.
- **Dữ liệu test:** 2 clinic.
- **Kết quả mong đợi:** Role chỉ thuộc clinic 1; clinic 2 truy cập → 404/403.
- **Coverage hiện tại:** MISSING (TASK-023).

### TC-RBAC-036 — Hiển thị permission theo nhóm module
- **Function:** RBAC-011
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Màn hình quản lý role.
- **Bước thực hiện:** 1) Mở form edit role. 2) Kiểm tra perm group thành Patient/Visit/Pharmacy/Billing/...
- **Dữ liệu test:** catalog 38 perm.
- **Kết quả mong đợi:** Perm nhóm theo domain, có header/collapse; chọn cả nhóm.
- **Coverage hiện tại:** MISSING (TASK-023).

### TC-RBAC-037 — Group hiển thị đúng khi catalog đổi
- **Function:** RBAC-011
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Bước thực hiện:** 1) Thêm perm domain mới. 2) Render lại UI.
- **Dữ liệu test:** perm domain mới.
- **Kết quả mong đợi:** Nhóm mới xuất hiện; không vỡ layout.
- **Coverage hiện tại:** MISSING (TASK-023).

### TC-RBAC-038 — Role có mô tả khi nào dùng
- **Function:** RBAC-012
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Bước thực hiện:** 1) Tạo/sửa role với `description`. 2) GET trả về description.
- **Dữ liệu test:** description text.
- **Kết quả mong đợi:** Field `description` lưu & trả về; hiển thị trong list role.
- **Coverage hiện tại:** MISSING (TASK-023).

### TC-RBAC-039 — Description tùy chọn / giới hạn độ dài
- **Function:** RBAC-012
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Bước thực hiện:** 1) Tạo role không description → OK. 2) Description quá dài → 422.
- **Dữ liệu test:** "" và 2000 ký tự.
- **Kết quả mong đợi:** Cho phép rỗng; vượt giới hạn → 422.
- **Coverage hiện tại:** MISSING (TASK-023).

### TC-RBAC-040 — Mọi thay đổi role/perm ghi audit
- **Function:** RBAC-013
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Audit log bật.
- **Bước thực hiện:** 1) Gán role cho user. 2) Query audit log.
- **Dữ liệu test:** assign role.
- **Kết quả mong đợi:** Audit có event `role.assign` với actor, target user, role, timestamp, clinic_id.
- **Coverage hiện tại:** COVERED (TASK-002).

### TC-RBAC-041 — Audit ghi grant/deny/clone/revoke
- **Function:** RBAC-013
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Bước thực hiện:** 1) Thực hiện extra-grant, extra-deny, clone, revoke role. 2) Kiểm tra mỗi action có 1 bản ghi audit.
- **Dữ liệu test:** 4 action.
- **Kết quả mong đợi:** Đủ 4 audit event đúng loại.
- **Coverage hiện tại:** COVERED (TASK-002).

### TC-RBAC-042 — Audit role-change cô lập clinic (RLS)
- **Function:** RBAC-013
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Bước thực hiện:** 1) Đổi role trong clinic 1. 2) Admin clinic 2 đọc audit.
- **Dữ liệu test:** 2 clinic.
- **Kết quả mong đợi:** Audit event chỉ thấy trong clinic 1.
- **Coverage hiện tại:** COVERED (TASK-002).

### TC-RBAC-043 — Platform role/permission tách bảng riêng
- **Function:** RBAC-014
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có bảng `platform_role`, `platform_permission`, `platform_user_role`.
- **Bước thực hiện:** 1) Query catalog platform perm.
- **Dữ liệu test:** N/A.
- **Kết quả mong đợi:** Catalog chứa `platform.clinic.create`, `platform.clinic.suspend`, `platform.subscription.update`, `platform.audit.read`...; tách hoàn toàn khỏi clinic RBAC.
- **Coverage hiện tại:** MISSING (TASK-026 chưa ship).

### TC-RBAC-044 — Không thể grant clinic-perm cho platform user (bảo vệ PHI)
- **Function:** RBAC-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Bước thực hiện:** 1) Cố gán `patient.read` (clinic perm) cho platform_user.
- **Dữ liệu test:** platform_user, perm=patient.read.
- **Kết quả mong đợi:** Bị từ chối ở tầng DB/service (FK/constraint hoặc validation); vật lý không thể; bảo vệ PHI.
- **Coverage hiện tại:** MISSING (TASK-026).

### TC-RBAC-045 — Platform endpoint chưa auth / thiếu platform perm
- **Function:** RBAC-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Bước thực hiện:** 1) Gọi `/platform/clinics` không token → 401. 2) Clinic admin (không phải platform) gọi → 403.
- **Dữ liệu test:** no-token; clinic admin.
- **Kết quả mong đợi:** 401 / 403.
- **Coverage hiện tại:** MISSING (TASK-026).

### TC-RBAC-046 — Platform user không truy cập dữ liệu clinic (RLS)
- **Function:** RBAC-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Bước thực hiện:** 1) Platform user thử query bảng `patient`.
- **Dữ liệu test:** platform_user.
- **Kết quả mong đợi:** Không có context clinic → RLS chặn; 0 row / 403; không leak PHI.
- **Coverage hiện tại:** MISSING (TASK-026).

### TC-RBAC-047 — Audit ghi `applied_role` đúng role đang dùng
- **Function:** RBAC-015
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User kiêm BS+QT (doctor+admin).
- **Bước thực hiện:** 1) User sửa giá DV (admin action). 2) Kiểm tra audit `applied_role=admin`. 3) User kê đơn (doctor action). 4) Kiểm tra `applied_role=doctor`.
- **Dữ liệu test:** user multi-role.
- **Kết quả mong đợi:** Mỗi audit ghi đúng `applied_role` theo permission dùng để authorize action.
- **Coverage hiện tại:** MISSING (TASK-002 — phần applied_role ⬜).

### TC-RBAC-048 — applied_role với user đơn role
- **Function:** RBAC-015
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Bước thực hiện:** 1) User chỉ role nurse thực hiện action.
- **Dữ liệu test:** user single-role.
- **Kết quả mong đợi:** `applied_role=nurse`; luôn có giá trị (không null).
- **Coverage hiện tại:** MISSING (TASK-002).

### TC-RBAC-049 — applied_role khi quyền đến từ extra-grant (không thuộc role)
- **Function:** RBAC-015
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Bước thực hiện:** 1) Action chỉ được phép nhờ extra-grant.
- **Dữ liệu test:** user có extra-grant.
- **Kết quả mong đợi:** `applied_role` ghi giá trị hợp lệ theo spec (vd `extra_grant`/role chứa hoặc đánh dấu nguồn); không null.
- **Coverage hiện tại:** MISSING (TASK-002).

### TC-RBAC-050 — SoD: user BS+DS không tự duyệt đơn của chính mình
- **Function:** RBAC-016
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User kiêm doctor+pharmacist; tự tạo đơn thuốc.
- **Bước thực hiện:** 1) User tạo prescription. 2) Cùng user gọi duyệt/cấp phát đơn đó.
- **Dữ liệu test:** user doctor+pharmacist, đơn tự tạo.
- **Kết quả mong đợi:** 403; BE chặn self-approve; thông báo SoD.
- **Coverage hiện tại:** MISSING (TASK-004 — phần SoD ⬜).

### TC-RBAC-051 — SoD: người tạo đề xuất giá không self-approve
- **Function:** RBAC-016
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Bước thực hiện:** 1) User tạo đề xuất đổi giá DV. 2) Cùng user approve.
- **Dữ liệu test:** user tạo+approve.
- **Kết quả mong đợi:** 403; cần người khác approve.
- **Coverage hiện tại:** MISSING (TASK-004).

### TC-RBAC-052 — SoD: người khác duyệt thì hợp lệ
- **Function:** RBAC-016
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Bước thực hiện:** 1) User A tạo đề xuất. 2) User B (đủ quyền, khác A) approve.
- **Dữ liệu test:** A tạo, B duyệt.
- **Kết quả mong đợi:** 200; duyệt thành công; audit ghi A=creator, B=approver.
- **Coverage hiện tại:** MISSING (TASK-004).

### TC-RBAC-053 — SoD: UI disabled + tooltip cho action bị cấm self-approve
- **Function:** RBAC-016
- **Loại:** Manual/UI (vitest)
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Bước thực hiện:** 1) User mở đơn do chính mình tạo. 2) Kiểm tra nút duyệt.
- **Dữ liệu test:** đơn self.
- **Kết quả mong đợi:** Nút approve disabled + tooltip giải thích SoD.
- **Coverage hiện tại:** MISSING (TASK-004).

### TC-RBAC-054 — Sidebar hiển thị UNION module của mọi role
- **Function:** RBAC-017
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** User kiêm doctor+admin.
- **Bước thực hiện:** 1) Login. 2) Kiểm tra sidebar.
- **Dữ liệu test:** user multi-role.
- **Kết quả mong đợi:** Sidebar = UNION module của tất cả role; KHÔNG có role-switcher.
- **Coverage hiện tại:** MISSING (TASK-017).

### TC-RBAC-055 — Group label phân tách theo role
- **Function:** RBAC-017
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Bước thực hiện:** 1) Render sidebar multi-role.
- **Dữ liệu test:** doctor+admin.
- **Kết quả mong đợi:** Có nhãn nhóm "─── Bác sĩ ───" / "─── Quản trị ───".
- **Coverage hiện tại:** MISSING (TASK-017).

### TC-RBAC-056 — User đơn role không thấy module ngoài quyền
- **Function:** RBAC-017
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Manual/UI (vitest)
- **Bước thực hiện:** 1) Login nurse. 2) Kiểm tra sidebar không có module admin.
- **Dữ liệu test:** nurse.
- **Kết quả mong đợi:** Chỉ module nurse có quyền; truy cập trực tiếp URL admin → 403 (BE).
- **Coverage hiện tại:** MISSING (TASK-017).

### TC-RBAC-057 — Sidebar cập nhật khi role đổi (sau switch-clinic/grant)
- **Function:** RBAC-017
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Bước thực hiện:** 1) Switch clinic (role khác). 2) Kiểm tra sidebar render lại.
- **Dữ liệu test:** user đa-clinic.
- **Kết quả mong đợi:** Sidebar khớp role của clinic mới; cache FE clear.
- **Coverage hiện tại:** MISSING (TASK-017).

### TC-RBAC-058 — Chip hiển thị tất cả role hiện hành ở avatar
- **Function:** RBAC-018
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** User 3 role.
- **Bước thực hiện:** 1) Login. 2) Kiểm tra footer sidebar + topbar avatar badge.
- **Dữ liệu test:** user 3 role.
- **Kết quả mong đợi:** Hiển thị role + badge "+2".
- **Coverage hiện tại:** MISSING (TASK-017).

### TC-RBAC-059 — Hover badge thấy full list + ngày được cấp
- **Function:** RBAC-018
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Bước thực hiện:** 1) Hover badge "+2".
- **Dữ liệu test:** user multi-role có granted_at.
- **Kết quả mong đợi:** Tooltip liệt kê đủ role + ngày cấp.
- **Coverage hiện tại:** MISSING (TASK-017).

### TC-RBAC-060 — User đơn role không có badge "+N"
- **Function:** RBAC-018
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Bước thực hiện:** 1) Login nurse (1 role).
- **Dữ liệu test:** nurse.
- **Kết quả mong đợi:** Chỉ 1 chip, không badge "+N".
- **Coverage hiện tại:** MISSING (TASK-017).

---

## Phụ lục — Ghi chú coverage & rủi ro

- **Đã ship (COVERED, TASK-004/TASK-002):** RBAC-001..009 (core role/permission/cache/clone/immutable) + RBAC-013 (audit role change). Cần đối chiếu lại file test thực tế trong `clinic-cms-merge/tests` (kênh đọc test bị gián đoạn trong phiên soạn này) để xác nhận từng `test_*`.
- **PARTIAL:** TC-RBAC-022 (fan-out invalidate theo role tới mọi user), TC-RBAC-030 (guard immutable tầng service) — cơ chế có nhưng cần test khẳng định.
- **MISSING (chưa ship):** RBAC-010/011/012 (custom role CRUD + UI, TASK-023), RBAC-014 (platform RBAC, TASK-026), RBAC-015 (applied_role, TASK-002 phần ⬜), RBAC-016 (SoD enforce, TASK-004 phần ⬜), RBAC-017/018 (multi-role sidebar UX, TASK-017).
- **Rủi ro lớn nhất:** SoD (RBAC-016) và Platform RBAC tách biệt (RBAC-014) là nhóm bảo mật P0 nhưng chưa ship — thiếu chúng cho phép self-approve và nguy cơ platform user chạm PHI; ưu tiên hàng đầu khi các task này vào pha test.
