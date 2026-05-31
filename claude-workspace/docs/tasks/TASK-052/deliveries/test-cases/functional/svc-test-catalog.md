# Test Case Catalog — SVC · Dịch vụ kỹ thuật

**Nguồn:** function_list_data.py (group SVC, dòng 729–773) + clinic_management_function_list.md (SVC-001…SVC-009) + system_design/BA.
**Phạm vi:** 9 functions (SVC-001 … SVC-009).  **Tổng test case:** 47.  **Ngày:** 2026-05-30.

> Ghi chú nguồn: Cột Status lấy từ `function_list_data.py` (nguồn ưu tiên). Trong file `.py`, tất cả 9
> function SVC đều ở trạng thái **TODO** (riêng SVC-005 = IDEA, v2). Bảng trong
> `clinic_management_function_list.md` hiển thị SVC-009 = ✅ do dùng chung cơ chế audit của TASK-002,
> nhưng phần nghiệp vụ price-history riêng của service vẫn TODO trong nguồn `.py` → ghi PARTIAL.
> Thư mục `clinic-cms-merge/app/modules` và `clinic-cms-merge/tests` không truy cập được trong phiên
> này nên Coverage gán theo Status nguồn + suy luận; cần đối chiếu lại test thực tế khi truy cập được.

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| SVC-001 | Service catalog CRUD | ⬜ TODO | TC-SVC-001, TC-SVC-002, TC-SVC-003, TC-SVC-004, TC-SVC-005, TC-SVC-006 | MISSING |
| SVC-002 | Service phân loại | ⬜ TODO | TC-SVC-007, TC-SVC-008, TC-SVC-009 | MISSING |
| SVC-003 | Multi-price (BHYT vs trực tiếp) | ⬜ TODO | TC-SVC-010, TC-SVC-011, TC-SVC-012, TC-SVC-013 | MISSING |
| SVC-004 | Service-doctor mapping | ⬜ TODO | TC-SVC-014, TC-SVC-015, TC-SVC-016, TC-SVC-017 | MISSING |
| SVC-005 | Service packages (v2) | 💡 IDEA | TC-SVC-018, TC-SVC-019, TC-SVC-020 | MISSING |
| SVC-006 | Add service vào visit | ⬜ TODO | TC-SVC-021, TC-SVC-022, TC-SVC-023, TC-SVC-024, TC-SVC-025, TC-SVC-026 | MISSING |
| SVC-007 | VisitService tracking | ⬜ TODO | TC-SVC-027, TC-SVC-028, TC-SVC-029, TC-SVC-030, TC-SVC-031, TC-SVC-032 | MISSING |
| SVC-008 | Service revenue report | ⬜ TODO | TC-SVC-033, TC-SVC-034, TC-SVC-035, TC-SVC-036, TC-SVC-037 | MISSING |
| SVC-009 | Service price history | ⬜ TODO (md: ✅ qua TASK-002) | TC-SVC-038, TC-SVC-039, TC-SVC-040, TC-SVC-041, TC-SVC-042 | PARTIAL |

**Tổng kết coverage theo function:** COVERED = 0, PARTIAL = 1 (SVC-009), MISSING = 8 (tổng 9).

---

## 2. Chi tiết Test Cases

### TC-SVC-001 — Tạo service hợp lệ (catalog CRUD)
- **Function:** SVC-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập user role Clinic Admin có permission `service:create`.
- **Bước thực hiện:** 1) POST `/api/v1/services` {code, name, category, base_price, duration_minutes, requires_doctor, active=true}. 2) GET lại detail.
- **Dữ liệu test:** {code:"XQ01", name:"Chụp X-quang ngực", category:"XQUANG", base_price:150000, duration_minutes:15, requires_doctor:true}.
- **Kết quả mong đợi:** HTTP 201; response chứa id, clinic_id = clinic hiện tại, active=true; `created_at`/`created_by` set; audit "service.created".
- **Coverage hiện tại:** MISSING (function TODO; chưa xác nhận test thực tế).

### TC-SVC-002 — Tạo service trùng code trong cùng clinic
- **Function:** SVC-001
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã tồn tại service code "XQ01" trong clinic hiện tại.
- **Bước thực hiện:** 1) POST `/api/v1/services` với code trùng.
- **Dữ liệu test:** code="XQ01".
- **Kết quả mong đợi:** HTTP 409/422 — vi phạm unique (clinic_id, code); không tạo bản ghi.
- **Coverage hiện tại:** MISSING.

### TC-SVC-003 — Cập nhật service (đổi giá, thời lượng)
- **Function:** SVC-001
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tồn tại service; user có `service:update`.
- **Bước thực hiện:** 1) PATCH `/api/v1/services/{id}` đổi base_price, duration_minutes. 2) GET detail.
- **Dữ liệu test:** base_price=170000, duration_minutes=20.
- **Kết quả mong đợi:** HTTP 200; field cập nhật đúng; `updated_at/updated_by` đổi; audit "service.updated".
- **Coverage hiện tại:** MISSING.

### TC-SVC-004 — Soft-delete service (active=false)
- **Function:** SVC-001
- **Loại:** Happy path / business rule
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Service active.
- **Bước thực hiện:** 1) DELETE `/api/v1/services/{id}` (hoặc PATCH active=false). 2) GET list mặc định.
- **Dữ liệu test:** id service active.
- **Kết quả mong đợi:** HTTP 200; active=false (soft-delete, không xóa cứng); không xuất hiện trong picker chỉ định; lịch sử bảo toàn.
- **Coverage hiện tại:** MISSING.

### TC-SVC-005 — Validate dữ liệu bắt buộc / giá âm
- **Function:** SVC-001
- **Loại:** Negative / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User có quyền tạo.
- **Bước thực hiện:** 1) POST thiếu `name`. 2) POST `base_price` < 0. 3) POST `duration_minutes` âm.
- **Dữ liệu test:** base_price=-1; duration_minutes=-5.
- **Kết quả mong đợi:** HTTP 422 với message theo từng field; không lưu.
- **Coverage hiện tại:** MISSING.

### TC-SVC-006 — Catalog CRUD — quyền & cô lập clinic (RLS)
- **Function:** SVC-001
- **Loại:** Security (auth + RLS)
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Service X thuộc clinic A; user clinic B; user thiếu permission.
- **Bước thực hiện:** 1) POST tạo service không token. 2) POST tạo bằng user thiếu `service:create`. 3) GET/PATCH service clinic A bằng user clinic B.
- **Dữ liệu test:** id service clinic A.
- **Kết quả mong đợi:** (1) 401; (2) 403; (3) 404 do RLS che giấu (không sửa/đọc được dữ liệu clinic A).
- **Coverage hiện tại:** MISSING.

### TC-SVC-007 — Lọc danh sách theo category
- **Function:** SVC-002
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có service thuộc nhiều category (KHAM, XET_NGHIEM, THU_THUAT, SIEU_AM, XQUANG, KHAC).
- **Bước thực hiện:** 1) GET `/api/v1/services?category=XQUANG`.
- **Dữ liệu test:** category=XQUANG.
- **Kết quả mong đợi:** HTTP 200; chỉ trả service category XQUANG của clinic hiện tại.
- **Coverage hiện tại:** MISSING.

### TC-SVC-008 — Category không hợp lệ (ngoài enum)
- **Function:** SVC-002
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User có quyền tạo service.
- **Bước thực hiện:** 1) POST service với category="ABC_KHONG_TON_TAI".
- **Dữ liệu test:** category sai enum.
- **Kết quả mong đợi:** HTTP 422 — category phải thuộc enum cho phép.
- **Coverage hiện tại:** MISSING.

### TC-SVC-009 — Tổng hợp số lượng service theo từng category
- **Function:** SVC-002
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có service phân bổ nhiều category, bao gồm category rỗng.
- **Bước thực hiện:** 1) GET danh sách + group theo category.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Đếm đúng theo category; category không có service trả 0; chỉ tính clinic hiện tại.
- **Coverage hiện tại:** MISSING.

### TC-SVC-010 — Thiết lập 2 mức giá (BHYT & trực tiếp)
- **Function:** SVC-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tồn tại service; user có `service:update`.
- **Bước thực hiện:** 1) PATCH `/api/v1/services/{id}` {price_bhyt, price_direct}. 2) GET detail.
- **Dữ liệu test:** price_bhyt=80000, price_direct=150000.
- **Kết quả mong đợi:** HTTP 200; cả 2 mức giá lưu đúng; audit thay đổi giá (liên kết SVC-009).
- **Coverage hiện tại:** MISSING.

### TC-SVC-011 — Áp giá theo loại bệnh nhân khi tạo hóa đơn
- **Function:** SVC-003
- **Loại:** Happy path / business rule (tiền)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Service có price_bhyt và price_direct; có 2 bệnh nhân (BHYT / dịch vụ).
- **Bước thực hiện:** 1) Chỉ định service cho BN BHYT → tính tiền. 2) Chỉ định cho BN dịch vụ → tính tiền.
- **Dữ liệu test:** patient_type=BHYT vs DIRECT.
- **Kết quả mong đợi:** BN BHYT áp price_bhyt; BN dịch vụ áp price_direct; số tiền snapshot vào VisitService.
- **Coverage hiện tại:** MISSING.

### TC-SVC-012 — Giá âm / một trong hai mức giá để trống
- **Function:** SVC-003
- **Loại:** Negative / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User có quyền sửa giá.
- **Bước thực hiện:** 1) PATCH price_bhyt < 0. 2) PATCH chỉ set 1 mức giá.
- **Dữ liệu test:** price_bhyt=-1; price_direct=null.
- **Kết quả mong đợi:** 422 với giá âm; xác nhận quy tắc nghiệp vụ khi thiếu 1 mức (fallback hay bắt buộc cả hai).
- **Coverage hiện tại:** MISSING.

### TC-SVC-013 — Multi-price — quyền sửa giá
- **Function:** SVC-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User thiếu permission sửa service/giá.
- **Bước thực hiện:** 1) PATCH giá không token. 2) PATCH giá với user thiếu quyền. 3) PATCH service clinic A bằng user clinic B.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** 401 / 403 / 404 (RLS).
- **Coverage hiện tại:** MISSING.

### TC-SVC-014 — Gán doctor đủ điều kiện thực hiện service
- **Function:** SVC-004
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tồn tại service + doctor; user Clinic Admin có quyền.
- **Bước thực hiện:** 1) POST `/api/v1/services/{id}/doctors` {doctor_id}. 2) GET danh sách doctor của service.
- **Dữ liệu test:** doctor_id hợp lệ.
- **Kết quả mong đợi:** HTTP 201; pivot service_doctor tạo đúng; gắn clinic hiện tại.
- **Coverage hiện tại:** MISSING.

### TC-SVC-015 — Chỉ định service cho doctor KHÔNG có trong mapping
- **Function:** SVC-004
- **Loại:** Negative / business rule
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Service có mapping doctor (mapping không rỗng); doctor X không nằm trong mapping.
- **Bước thực hiện:** 1) Tạo VisitService với doctor X thực hiện service đó.
- **Dữ liệu test:** doctor X ngoài mapping.
- **Kết quả mong đợi:** HTTP 422/409 — doctor không đủ điều kiện thực hiện service.
- **Coverage hiện tại:** MISSING.

### TC-SVC-016 — Mapping rỗng → mọi doctor đều thực hiện được
- **Function:** SVC-004
- **Loại:** Edge / business rule
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Service KHÔNG có dòng mapping nào.
- **Bước thực hiện:** 1) Chỉ định service cho doctor bất kỳ.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Cho phép (mapping trống = không giới hạn); tạo VisitService thành công.
- **Coverage hiện tại:** MISSING.

### TC-SVC-017 — Service-doctor mapping — quyền & cô lập clinic
- **Function:** SVC-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Service/doctor thuộc clinic A.
- **Bước thực hiện:** 1) POST mapping không token. 2) POST với user thiếu quyền. 3) Gán doctor clinic B vào service clinic A.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** 401 / 403 / 404 (RLS); không cho cross-clinic mapping.
- **Coverage hiện tại:** MISSING.

### TC-SVC-018 — Tạo gói dịch vụ gồm nhiều service con (v2)
- **Function:** SVC-005
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tồn tại ≥2 service active; user Clinic Admin có quyền tạo package.
- **Bước thực hiện:** 1) POST `/api/v1/service-packages` {name, items:[service_id...], package_price}. 2) GET detail.
- **Dữ liệu test:** gói "Khám tổng quát" gồm 3 service.
- **Kết quả mong đợi:** HTTP 201; gói chứa đủ service con; package_price (có thể chiết khấu so với tổng lẻ) lưu đúng.
- **Coverage hiện tại:** MISSING (function IDEA/v2 — chưa triển khai).

### TC-SVC-019 — Chỉ định cả gói vào visit → bung VisitService con
- **Function:** SVC-005
- **Loại:** Happy path / business rule
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Gói active; visit đang mở.
- **Bước thực hiện:** 1) Chỉ định gói vào visit. 2) Kiểm tra số VisitService con tạo ra.
- **Dữ liệu test:** gói 3 service.
- **Kết quả mong đợi:** Tạo đủ 3 VisitService con; tổng tiền theo package_price; mỗi dòng track status riêng.
- **Coverage hiện tại:** MISSING.

### TC-SVC-020 — Gói chứa service inactive / khác clinic
- **Function:** SVC-005
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 1 service inactive; 1 service clinic khác.
- **Bước thực hiện:** 1) POST gói tham chiếu các service không hợp lệ.
- **Dữ liệu test:** service_id inactive; service_id clinic khác.
- **Kết quả mong đợi:** HTTP 422/404 — từ chối thêm service không hợp lệ vào gói.
- **Coverage hiện tại:** MISSING.

### TC-SVC-021 — Doctor chỉ định service trong visit (tạo VisitService)
- **Function:** SVC-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit đang mở; service active; user role Doctor có `visit_service:create`.
- **Bước thực hiện:** 1) POST `/api/v1/visits/{id}/services` {service_id, performing_doctor_id}. 2) GET danh sách VisitService.
- **Dữ liệu test:** service_id active.
- **Kết quả mong đợi:** HTTP 201; VisitService gồm visit_id, service_id, price snapshot, doctor, status=ordered; gắn đúng clinic; audit.
- **Coverage hiện tại:** MISSING.

### TC-SVC-022 — Chỉ định service inactive
- **Function:** SVC-006
- **Loại:** Negative / business rule
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Service ở active=false.
- **Bước thực hiện:** 1) POST VisitService với service inactive.
- **Dữ liệu test:** service_id inactive.
- **Kết quả mong đợi:** HTTP 422 — không cho chỉ định service đã ngừng dùng.
- **Coverage hiện tại:** MISSING.

### TC-SVC-023 — Snapshot giá tại thời điểm chỉ định
- **Function:** SVC-006
- **Loại:** Edge / business rule (tiền)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Service có base_price ban đầu.
- **Bước thực hiện:** 1) Chỉ định service vào visit. 2) Đổi giá service. 3) Kiểm tra price trong VisitService.
- **Dữ liệu test:** giá trước=150000, sau đổi=200000.
- **Kết quả mong đợi:** VisitService giữ giá snapshot 150000, không bị thay đổi khi giá catalog đổi sau đó.
- **Coverage hiện tại:** MISSING.

### TC-SVC-024 — Validate doctor mapping khi chỉ định (liên kết SVC-004)
- **Function:** SVC-006
- **Loại:** Negative / business rule
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Service có mapping doctor; doctor được chọn không nằm trong mapping.
- **Bước thực hiện:** 1) POST VisitService với doctor ngoài mapping.
- **Dữ liệu test:** doctor không đủ điều kiện.
- **Kết quả mong đợi:** HTTP 422/409 — chặn theo service-doctor mapping.
- **Coverage hiện tại:** MISSING.

### TC-SVC-025 — Chỉ định service vào visit đã đóng
- **Function:** SVC-006
- **Loại:** Negative / state machine
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit ở trạng thái đóng/hoàn tất.
- **Bước thực hiện:** 1) POST VisitService vào visit đã đóng.
- **Dữ liệu test:** visit_id đã đóng.
- **Kết quả mong đợi:** HTTP 409 — không thêm chỉ định vào visit đã đóng.
- **Coverage hiện tại:** MISSING.

### TC-SVC-026 — Chỉ định service — chưa auth / thiếu quyền / clinic chéo
- **Function:** SVC-006
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit thuộc clinic A.
- **Bước thực hiện:** 1) POST không token. 2) POST user thiếu `visit_service:create`. 3) POST user clinic B vào visit clinic A.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** 401 / 403 / 404 (RLS).
- **Coverage hiện tại:** MISSING.

### TC-SVC-027 — Danh sách VisitService theo visit
- **Function:** SVC-007
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit có ≥2 VisitService với trạng thái khác nhau.
- **Bước thực hiện:** 1) GET `/api/v1/visits/{id}/services`.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 200; trả đủ dòng kèm status; chỉ của visit và clinic hiện tại.
- **Coverage hiện tại:** MISSING.

### TC-SVC-028 — Chuyển status ordered → in_progress → done
- **Function:** SVC-007
- **Loại:** Happy path / state machine
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** VisitService ở status=ordered.
- **Bước thực hiện:** 1) PATCH status=in_progress. 2) PATCH status=done.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 200 mỗi bước; transition hợp lệ; ghi mốc thời gian; khi done → billable; audit.
- **Coverage hiện tại:** MISSING.

### TC-SVC-029 — Transition không hợp lệ (ordered → done bỏ bước)
- **Function:** SVC-007
- **Loại:** Negative / state machine
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** VisitService=ordered.
- **Bước thực hiện:** 1) PATCH status=done trực tiếp (nếu yêu cầu tuần tự).
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 409 invalid transition; status không đổi.
- **Coverage hiện tại:** MISSING.

### TC-SVC-030 — Cancel VisitService chưa thực hiện
- **Function:** SVC-007
- **Loại:** Happy path / business rule
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** VisitService=ordered, chưa thu tiền.
- **Bước thực hiện:** 1) PATCH status=cancelled {reason}.
- **Dữ liệu test:** reason "BN từ chối".
- **Kết quả mong đợi:** HTTP 200; status=cancelled; không tính tiền; audit kèm lý do.
- **Coverage hiện tại:** MISSING.

### TC-SVC-031 — Cancel VisitService đã thu tiền (cần hoàn)
- **Function:** SVC-007
- **Loại:** Negative / business rule (tiền)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** VisitService=done và đã thu tiền.
- **Bước thực hiện:** 1) PATCH status=cancelled.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Yêu cầu nghiệp vụ hoàn tiền (refund/void) thay vì hủy thẳng; nếu cho phép phải tạo bút toán hoàn; không xóa lịch sử.
- **Coverage hiện tại:** MISSING.

### TC-SVC-032 — VisitService tracking — cô lập clinic & quyền
- **Function:** SVC-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** VisitService thuộc clinic A.
- **Bước thực hiện:** 1) GET/PATCH không token. 2) PATCH thiếu quyền. 3) PATCH VisitService clinic A bằng user clinic B.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** 401 / 403 / 404 (RLS).
- **Coverage hiện tại:** MISSING.

### TC-SVC-033 — Báo cáo doanh thu theo service trong kỳ
- **Function:** SVC-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có VisitService done có thu tiền trong khoảng ngày.
- **Bước thực hiện:** 1) GET `/api/v1/reports/services?from=...&to=...`.
- **Dữ liệu test:** khoảng 30 ngày.
- **Kết quả mong đợi:** HTTP 200; số lượt + doanh thu theo service đúng; chỉ tính clinic hiện tại; loại VisitService cancelled.
- **Coverage hiện tại:** MISSING.

### TC-SVC-034 — Báo cáo doanh thu nhóm theo category + top service
- **Function:** SVC-008
- **Loại:** Happy path / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Dữ liệu nhiều category.
- **Bước thực hiện:** 1) GET `?group_by=category`. 2) Lấy top N service.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Tổng doanh thu khớp tổng các category; top service xếp đúng theo doanh thu.
- **Coverage hiện tại:** MISSING.

### TC-SVC-035 — Báo cáo với khoảng thời gian rỗng / không có dữ liệu
- **Function:** SVC-008
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Không có VisitService trong khoảng chọn.
- **Bước thực hiện:** 1) GET báo cáo khoảng ngày tương lai.
- **Dữ liệu test:** from/to ở tương lai.
- **Kết quả mong đợi:** HTTP 200; trả tổng = 0, danh sách rỗng (không lỗi).
- **Coverage hiện tại:** MISSING.

### TC-SVC-036 — Báo cáo doanh thu — cô lập clinic (RLS)
- **Function:** SVC-008
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B đều có dữ liệu doanh thu.
- **Bước thực hiện:** 1) User clinic B gọi báo cáo.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Chỉ số liệu clinic B; không lộ doanh thu clinic A.
- **Coverage hiện tại:** MISSING.

### TC-SVC-037 — Báo cáo doanh thu — chưa auth / thiếu quyền
- **Function:** SVC-008
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User thiếu `report:service:read`.
- **Bước thực hiện:** 1) GET báo cáo không token. 2) GET với user thiếu quyền.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** 401 / 403.
- **Coverage hiện tại:** MISSING.

### TC-SVC-038 — Ghi nhận lịch sử thay đổi giá khi đổi giá service
- **Function:** SVC-009
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Service có giá hiện hành; user có quyền sửa giá.
- **Bước thực hiện:** 1) PATCH đổi giá service. 2) GET `/api/v1/services/{id}/price-history`.
- **Dữ liệu test:** old=150000, new=200000, reason="Điều chỉnh 2026".
- **Kết quả mong đợi:** HTTP 200; tạo 1 bản ghi price_history {service_id, old_price, new_price, changed_by, changed_at, reason}.
- **Coverage hiện tại:** PARTIAL (cơ chế audit chung đã có qua TASK-002; phần price-history riêng của service chưa xác nhận DONE trong nguồn `.py`).

### TC-SVC-039 — Nhiều lần đổi giá tạo nhiều bản ghi theo thứ tự thời gian
- **Function:** SVC-009
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Service được đổi giá ≥3 lần.
- **Bước thực hiện:** 1) Đổi giá 3 lần. 2) GET price-history.
- **Dữ liệu test:** 3 mức giá khác nhau.
- **Kết quả mong đợi:** 3 bản ghi, sắp xếp theo changed_at; old_price của bản sau = new_price của bản trước.
- **Coverage hiện tại:** PARTIAL.

### TC-SVC-040 — Đổi giá không thay đổi giá trị (không tạo bản ghi thừa)
- **Function:** SVC-009
- **Loại:** Edge / business rule
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Service giá hiện hành 150000.
- **Bước thực hiện:** 1) PATCH giá = 150000 (không đổi).
- **Dữ liệu test:** new_price = old_price.
- **Kết quả mong đợi:** Không tạo bản ghi price_history (hoặc theo quy tắc nghiệp vụ rõ ràng); không nhiễu audit.
- **Coverage hiện tại:** MISSING.

### TC-SVC-041 — Price history — cô lập clinic (RLS)
- **Function:** SVC-009
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Service và lịch sử giá thuộc clinic A.
- **Bước thực hiện:** 1) User clinic B GET price-history của service clinic A.
- **Dữ liệu test:** id service clinic A.
- **Kết quả mong đợi:** 404 (RLS) — không lộ lịch sử giá clinic khác.
- **Coverage hiện tại:** PARTIAL.

### TC-SVC-042 — Price history — chưa auth / thiếu quyền
- **Function:** SVC-009
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User thiếu quyền xem lịch sử giá.
- **Bước thực hiện:** 1) GET price-history không token. 2) GET với user thiếu quyền.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** 401 / 403.
- **Coverage hiện tại:** PARTIAL.

---

## 3. Ghi chú & rủi ro

- **Status nguồn:** Toàn bộ 9 function SVC ở trạng thái TODO trong `function_list_data.py` (SVC-005 = IDEA/v2).
  Do đó hầu hết Coverage là MISSING; chỉ SVC-009 đạt PARTIAL nhờ kế thừa cơ chế audit chung TASK-002.
  Không tìm thấy test SVC trong `clinic-cms-merge/tests` và không có catalog SVC cũ trong `docs/tasks`
  (TASK-001…TASK-051) — phù hợp với việc nhóm dịch vụ kỹ thuật chưa được implement (dự kiến TASK-010/015).
- **Khu vực rủi ro cao nhất:**
  (1) Snapshot giá khi chỉ định (TC-SVC-023) và áp giá theo loại BN BHYT/trực tiếp (TC-SVC-011) — đụng tiền.
  (2) State machine VisitService ordered→in_progress→done→cancelled (SVC-007) — transition trái phép & hoàn tiền.
  (3) Service-doctor mapping (SVC-004) — quy tắc "mapping rỗng = mọi doctor" dễ gây hiểu nhầm khi test.
- **RLS:** mọi function chạm dữ liệu domain đã có case cô lập clinic; cần xác nhận policy RLS bật trên các
  bảng services, service_doctor, visit_services, service_packages, service_price_history khi implement.
- **Cần làm lại khi truy cập được merge repo:** đối chiếu endpoint path thực tế và bổ sung Coverage nếu
  có test đã ship (hiện `clinic-cms-merge/app/modules` và `/tests` không đọc được trong phiên này).
