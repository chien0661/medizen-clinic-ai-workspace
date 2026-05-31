# Kịch bản vận hành — Phân quyền chéo (Negative — phải bị 403)

**Mục đích:** test E2E theo luồng vận hành thực tế, mỗi bước do ĐÚNG vai trò/tài khoản thực hiện, bàn giao trạng thái giữa các vai trò. Nhóm này tập trung vào các thao tác mà một vai trò KHÔNG có quyền cố thực hiện → hệ thống PHẢI từ chối với HTTP 403 (Forbidden), dựa chặt trên ma trận quyền BA §13.6. Có thêm case RLS đa tenant (clinic A đọc/ghi dữ liệu clinic B).
**Số kịch bản:** 13. **Ngày:** 2026-05-31.

---

## Quy ước chung

- **Tiền đề xác thực:** Mọi tài khoản ĐÃ đăng nhập hợp lệ (`POST /api/v1/auth/login` → 200, có JWT). Vì vậy lỗi mong đợi là **403 Forbidden** (đã xác thực nhưng thiếu quyền), KHÔNG phải 401 (thiếu/sai token).
- **Phân biệt 401 vs 403:**
  - Thiếu/hết hạn/sai JWT → **401 Unauthorized** (chặn trước routing).
  - JWT hợp lệ nhưng role không có permission tương ứng → **403 Forbidden**.
  - RLS đa tenant: tài khoản clinic A truy vấn bản ghi clinic B → **404 Not Found** (row bị RLS lọc, coi như không tồn tại) hoặc **403** tùy endpoint; xem chi tiết từng case.
- **Body lỗi mong đợi:** `{ "detail": ..., "error_code": "FORBIDDEN" }` (hoặc tương đương theo chuẩn hệ thống); mã quyền thiếu được ghi rõ ở từng case.
- **Nguyên tắc kiểm chứng quyền (no side-effect):** Sau khi nhận 403, thao tác KHÔNG được tạo/sửa/xóa bất kỳ bản ghi nào; kiểm tra lại bằng tài khoản admin để xác nhận dữ liệu không đổi và audit ghi nhận attempt bị từ chối (DENIED).
- **Mẫu tự động hóa khuyến nghị:** mỗi case chạy 1 request bằng tài khoản THIẾU quyền (kỳ vọng 403/404) + 1 request đối chứng bằng tài khoản CÓ quyền (kỳ vọng 2xx) để chứng minh lỗi do phân quyền chứ không phải route hỏng.

---

## Danh sách kịch bản
| Mã | Tên kịch bản | Vai trò tham gia | Ưu tiên |
|---|---|---|---|
| SC-RBAC-01 | Lễ tân kê đơn thuốc (thiếu prescription.write) | Lễ tân (recept_anh) → đối chứng Admin | P0 |
| SC-RBAC-02 | Y tá kê đơn thuốc (thiếu prescription.write) | Y tá (nurse_lan) → đối chứng Admin | P0 |
| SC-RBAC-03 | Y tá cấp phát thuốc (thiếu pharmacy.dispense) | Y tá (nurse_lan) → đối chứng Dược sĩ/Admin | P0 |
| SC-RBAC-04 | Dược sĩ tạo/sửa visit (thiếu visit.write) | Dược sĩ (pharm_cuong) → đối chứng Admin | P0 |
| SC-RBAC-05 | Dược sĩ nhập sinh hiệu (thiếu vital.write) | Dược sĩ (pharm_cuong) → đối chứng Admin | P1 |
| SC-RBAC-06 | Thu ngân void hóa đơn (thiếu invoice.void) | Thu ngân (cashier_em) → đối chứng Admin | P0 |
| SC-RBAC-07 | Lễ tân void hóa đơn (thiếu invoice.void) | Lễ tân (recept_anh) → đối chứng Admin | P0 |
| SC-RBAC-08 | Bác sĩ quản lý user (thiếu user.manage) | Bác sĩ (dr_nguyen) → đối chứng Admin | P0 |
| SC-RBAC-09 | Bác sĩ xem báo cáo tài chính (thiếu report.financial) | Bác sĩ (dr_nguyen) → đối chứng Admin | P1 |
| SC-RBAC-10 | Non-admin sửa cấu hình phòng khám (thiếu settings.clinic) | Lễ tân/Y tá/Dược sĩ/Thu ngân/Bác sĩ → đối chứng Admin | P0 |
| SC-RBAC-11 | Dược sĩ tạo hóa đơn (thiếu invoice.create) | Dược sĩ (pharm_cuong) → đối chứng Lễ tân/Admin | P1 |
| SC-RBAC-12 | Thu ngân quản lý danh mục kho (thiếu inventory.manage_catalog) | Thu ngân (cashier_em) negative + Dược sĩ positive | P1 |
| SC-RBAC-13 | RLS đa tenant — clinic A đọc/ghi dữ liệu clinic B | Admin clinic A vs clinic B | P0 |

---

## Chi tiết

### SC-RBAC-01 — Lễ tân kê đơn thuốc (thiếu prescription.write)
- **Mục tiêu:** Xác nhận Lễ tân KHÔNG thể tạo đơn thuốc; chỉ Admin/Doctor có `prescription.write`.
- **Vai trò & tài khoản:** Lễ tân — `recept_anh` / `Recept@1234`; đối chứng Admin — `admin` / `Demo@1234`.
- **Tiền điều kiện:** Có 1 visit IN_PROGRESS (do dr_nguyen mở) để có visit_id hợp lệ; danh mục thuốc có sẵn (paracetamol). Lễ tân đã đăng nhập.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Login | POST /api/v1/auth/login | 200, JWT role=receptionist | Có token |
| 2 | Lễ tân (recept_anh) | Cố tạo đơn thuốc cho visit | POST /api/v1/visits/{visit_id}/prescriptions | **403 Forbidden**, error_code=FORBIDDEN, thiếu `prescription.write` | Không tạo đơn |
| 3 | Admin (admin) | Kiểm chứng không có đơn mới | GET /api/v1/visits/{visit_id}/prescriptions | 200, danh sách rỗng | Dữ liệu nguyên vẹn |

- **Kết quả cuối:** Visit giữ nguyên IN_PROGRESS, không có Prescription, không reserve tồn kho in_house.
- **Điểm kiểm chứng:** HTTP=403; không có row Prescription/PrescriptionItem; tồn kho thuốc không đổi (no StockMovement RESERVE); audit DENIED actor=recept_anh, permission=prescription.write; clinic_id trong audit khớp clinic của recept_anh (RLS).
- **Liên kết function:** TC-RBAC-002 (mỗi role có đúng tập permission BA §13.5 — receptionist KHÔNG có prescription.create), TC-RBAC-006 (pattern 401/403/200 cho endpoint cần quyền) trong rbac-test-catalog.md; RX-* (rx-test-catalog.md).

---

### SC-RBAC-02 — Y tá kê đơn thuốc (thiếu prescription.write)
- **Mục tiêu:** Y tá có `vital.write`/`service.perform` nhưng KHÔNG có `prescription.write`.
- **Vai trò & tài khoản:** Y tá — `nurse_lan` / `Nurse@1234`; đối chứng Admin — `admin` / `Demo@1234`.
- **Tiền điều kiện:** Visit IN_PROGRESS hợp lệ; thuốc trong danh mục. Y tá đã đăng nhập.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Y tá (nurse_lan) | Login | POST /api/v1/auth/login | 200, JWT role=nurse | Có token |
| 2 | Y tá (nurse_lan) | Cố tạo/sửa đơn thuốc | POST /api/v1/visits/{visit_id}/prescriptions | **403 Forbidden**, thiếu `prescription.write` | Không tạo đơn |
| 3 | Admin (admin) | Kiểm chứng | GET /api/v1/visits/{visit_id}/prescriptions | 200, không có đơn mới | Dữ liệu nguyên vẹn |

- **Kết quả cuối:** Không có Prescription mới, tồn kho không đổi.
- **Điểm kiểm chứng:** HTTP=403; no side-effect; audit DENIED actor=nurse_lan, permission=prescription.write.
- **Liên kết function:** RBAC-* (rbac-test-catalog.md — Nurse thiếu prescription.write), RX-* (rx-test-catalog.md).

---

### SC-RBAC-03 — Y tá cấp phát thuốc (thiếu pharmacy.dispense)
- **Mục tiêu:** Chỉ Admin/Pharmacist có `pharmacy.dispense`; Y tá bị từ chối.
- **Vai trò & tài khoản:** Y tá — `nurse_lan` / `Nurse@1234`; đối chứng Dược sĩ — `pharm_cuong` / `Pharm@1234`.
- **Tiền điều kiện:** Có 1 đơn thuốc in_house đã reserve (do dr_nguyen kê) đang ở hàng đợi cấp phát; batch có tồn để FEFO.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Y tá (nurse_lan) | Login | POST /api/v1/auth/login | 200, JWT role=nurse | Có token |
| 2 | Y tá (nurse_lan) | Cố thực hiện cấp phát (trừ tồn) | POST /api/v1/prescriptions/{id}/dispense | **403 Forbidden**, thiếu `pharmacy.dispense` | Không cấp phát |
| 3 | Dược sĩ (pharm_cuong) | Đối chứng cấp phát hợp lệ | POST /api/v1/prescriptions/{id}/dispense | 200, StockMovement OUT theo FEFO | Đơn DISPENSED |
| 4 | Admin (admin) | Kiểm chứng tồn kho sau bước 2 | GET /api/v1/inventory/batches/{batch_id} | on_hand chỉ giảm do bước 3, không do bước 2 | Tồn nhất quán |

- **Kết quả cuối:** Sau bước 2 KHÔNG có StockMovement OUT/DISPENSE từ y tá; chỉ dược sĩ mới trừ được tồn.
- **Điểm kiểm chứng:** HTTP=403 ở bước cấp phát của y tá; bước đối chứng dược sĩ 200; on_hand/reserved chỉ biến động do dược sĩ; audit DENIED actor=nurse_lan, permission=pharmacy.dispense.
- **Liên kết function:** TC-RBAC-002 (pharmacist mới có pharmacy.dispense; nurse không), TC-RBAC-006 (401/403/200) trong rbac-test-catalog.md; PHRM-* (phrm-test-catalog.md).

---

### SC-RBAC-04 — Dược sĩ tạo/sửa visit (thiếu visit.write)
- **Mục tiêu:** Dược sĩ KHÔNG có `visit.write`/`patient.write`; chỉ đọc (`patient.read`).
- **Vai trò & tài khoản:** Dược sĩ — `pharm_cuong` / `Pharm@1234`; đối chứng Admin — `admin`.
- **Tiền điều kiện:** Có bệnh nhân hợp lệ trong clinic DEMO. Dược sĩ đã đăng nhập.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Dược sĩ (pharm_cuong) | Login | POST /api/v1/auth/login | 200, JWT role=pharmacist | Có token |
| 2 | Dược sĩ (pharm_cuong) | Tra cứu BN (đọc — được phép) | GET /api/v1/patients?phone=... | 200 (patient.read OK) | Có patient_id |
| 3 | Dược sĩ (pharm_cuong) | Cố tạo visit | POST /api/v1/visits | **403 Forbidden**, thiếu `visit.write` | Không tạo visit |
| 4 | Dược sĩ (pharm_cuong) | Cố cập nhật visit | PATCH /api/v1/visits/{visit_id} | **403 Forbidden**, thiếu `visit.write` | Không sửa visit |
| 5 | Admin (admin) | Kiểm chứng số visit | GET /api/v1/visits?patient_id=... | 200, không có visit mới | Dữ liệu nguyên vẹn |

- **Kết quả cuối:** Không có Visit mới/được sửa; hàng đợi không thay đổi.
- **Điểm kiểm chứng:** patient.read trả 200 (xác nhận quyền đọc đúng); tạo/sửa visit trả 403; no side-effect; audit DENIED permission=visit.write.
- **Liên kết function:** RBAC-* (rbac-test-catalog.md — Pharmacist thiếu visit.write), VISIT-* (visit-test-catalog.md), PATIENT-* (patient-test-catalog.md — patient.read OK).

---

### SC-RBAC-05 — Dược sĩ nhập sinh hiệu (thiếu vital.write)
- **Mục tiêu:** Dược sĩ KHÔNG có `vital.write`.
- **Vai trò & tài khoản:** Dược sĩ — `pharm_cuong` / `Pharm@1234`; đối chứng Admin — `admin`.
- **Tiền điều kiện:** Visit WAITING hợp lệ. Dược sĩ đã đăng nhập.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Dược sĩ (pharm_cuong) | Login | POST /api/v1/auth/login | 200, JWT role=pharmacist | Có token |
| 2 | Dược sĩ (pharm_cuong) | Cố nhập sinh hiệu | POST /api/v1/visits/{visit_id}/vitals | **403 Forbidden**, thiếu `vital.write` | Không tạo vitals |
| 3 | Admin (admin) | Kiểm chứng | GET /api/v1/visits/{visit_id}/vitals | 200, không có bản ghi mới | Dữ liệu nguyên vẹn |

- **Kết quả cuối:** Không có VisitVitals mới; visit giữ nguyên WAITING, is_returning_patient không đổi.
- **Điểm kiểm chứng:** HTTP=403; no VisitVitals row; audit DENIED permission=vital.write.
- **Liên kết function:** RBAC-* (rbac-test-catalog.md — Pharmacist thiếu vital.write), VITAL-* (vital-test-catalog.md).

---

### SC-RBAC-06 — Thu ngân void hóa đơn (thiếu invoice.void)
- **Mục tiêu:** Thu ngân có `invoice.create` nhưng KHÔNG có `invoice.void` (chỉ Admin).
- **Vai trò & tài khoản:** Thu ngân — `cashier_em` / `Cashier@1234`; đối chứng Admin — `admin`.
- **Tiền điều kiện:** Có 1 Invoice ISSUED/PAID hợp lệ trong clinic DEMO.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Thu ngân (cashier_em) | Login | POST /api/v1/auth/login | 200, JWT role=cashier | Có token |
| 2 | Thu ngân (cashier_em) | Cố void hóa đơn | POST /api/v1/invoices/{invoice_id}/void | **403 Forbidden**, thiếu `invoice.void` | Hóa đơn giữ nguyên |
| 3 | Admin (admin) | Kiểm chứng trạng thái hóa đơn | GET /api/v1/invoices/{invoice_id} | 200, status KHÁC VOIDED | Hóa đơn nguyên vẹn |

- **Kết quả cuối:** Invoice giữ nguyên trạng thái, không có bút toán hoàn/đảo.
- **Điểm kiểm chứng:** HTTP=403; invoice.status không đổi; không phát sinh Payment/reversal; audit DENIED actor=cashier_em, permission=invoice.void.
- **Liên kết function:** TC-RBAC-014 (extra-deny/role không có perm → 403), TC-RBAC-006 (401/403/200) trong rbac-test-catalog.md; BILL-* (bill-test-catalog.md — void hóa đơn).

---

### SC-RBAC-07 — Lễ tân void hóa đơn (thiếu invoice.void)
- **Mục tiêu:** Lễ tân có `invoice.create` nhưng KHÔNG có `invoice.void`.
- **Vai trò & tài khoản:** Lễ tân — `recept_anh` / `Recept@1234`; đối chứng Admin — `admin`.
- **Tiền điều kiện:** Có 1 Invoice ISSUED/PAID hợp lệ.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Login | POST /api/v1/auth/login | 200, JWT role=receptionist | Có token |
| 2 | Lễ tân (recept_anh) | Cố void hóa đơn | POST /api/v1/invoices/{invoice_id}/void | **403 Forbidden**, thiếu `invoice.void` | Hóa đơn giữ nguyên |
| 3 | Admin (admin) | Kiểm chứng | GET /api/v1/invoices/{invoice_id} | 200, status KHÁC VOIDED | Hóa đơn nguyên vẹn |

- **Kết quả cuối:** Invoice không bị void.
- **Điểm kiểm chứng:** HTTP=403; status không đổi; audit DENIED actor=recept_anh, permission=invoice.void.
- **Liên kết function:** RBAC-* (rbac-test-catalog.md — Receptionist thiếu invoice.void), BILL-* (bill-test-catalog.md).

---

### SC-RBAC-08 — Bác sĩ quản lý user (thiếu user.manage)
- **Mục tiêu:** Chỉ Admin có `user.manage`; Bác sĩ bị từ chối.
- **Vai trò & tài khoản:** Bác sĩ — `dr_nguyen` / `Doctor@1234`; đối chứng Admin — `admin`.
- **Tiền điều kiện:** Bác sĩ đã đăng nhập; clinic DEMO có sẵn user khác (dr_le).
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Bác sĩ (dr_nguyen) | Login | POST /api/v1/auth/login | 200, JWT role=doctor | Có token |
| 2 | Bác sĩ (dr_nguyen) | Cố tạo user mới | POST /api/v1/users | **403 Forbidden**, thiếu `user.manage` | Không tạo user |
| 3 | Bác sĩ (dr_nguyen) | Cố đổi role user khác | PATCH /api/v1/users/{user_id} | **403 Forbidden**, thiếu `user.manage` | Không sửa user |
| 4 | Admin (admin) | Kiểm chứng danh sách user | GET /api/v1/users | 200, không có user mới, role dr_le không đổi | Dữ liệu nguyên vẹn |

- **Kết quả cuối:** Không có User mới/được sửa; phân quyền giữ nguyên.
- **Điểm kiểm chứng:** HTTP=403 ở cả tạo và sửa; no User/role change; audit DENIED permission=user.manage.
- **Liên kết function:** RBAC-* (rbac-test-catalog.md — Doctor thiếu user.manage), HR-* (hr-test-catalog.md — quản lý nhân sự/user).

---

### SC-RBAC-09 — Bác sĩ xem báo cáo tài chính (thiếu report.financial)
- **Mục tiêu:** Chỉ Admin có `report.financial`; Bác sĩ bị từ chối.
- **Vai trò & tài khoản:** Bác sĩ — `dr_nguyen` / `Doctor@1234`; đối chứng Admin — `admin`.
- **Tiền điều kiện:** Đã có doanh thu/hóa đơn để báo cáo có dữ liệu. Bác sĩ đã đăng nhập.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Bác sĩ (dr_nguyen) | Login | POST /api/v1/auth/login | 200, JWT role=doctor | Có token |
| 2 | Bác sĩ (dr_nguyen) | Cố xem báo cáo doanh thu | GET /api/v1/reports/financial | **403 Forbidden**, thiếu `report.financial` | Không xem được |
| 3 | Admin (admin) | Đối chứng endpoint hoạt động đúng | GET /api/v1/reports/financial | 200, trả số liệu | Endpoint OK với admin |

- **Kết quả cuối:** Bác sĩ không truy cập được dữ liệu tài chính.
- **Điểm kiểm chứng:** HTTP=403 với dr_nguyen; HTTP=200 với admin (đối chứng chứng minh lỗi do quyền, không phải route); audit DENIED permission=report.financial.
- **Liên kết function:** TC-RBAC-010 (extra-grant report.read — chứng minh report bị gate bởi permission), TC-RBAC-006 (401/403/200) trong rbac-test-catalog.md; RPT-* (rpt-test-catalog.md).

---

### SC-RBAC-10 — Non-admin sửa cấu hình phòng khám (thiếu settings.clinic)
- **Mục tiêu:** Bất kỳ vai trò non-admin nào cố sửa cấu hình phòng khám đều bị từ chối; chỉ Admin có `settings.clinic`.
- **Vai trò & tài khoản:** Lễ tân (recept_anh), Y tá (nurse_lan), Dược sĩ (pharm_cuong), Thu ngân (cashier_em), Bác sĩ (dr_nguyen) — lặp cho từng tài khoản; đối chứng Admin — `admin`.
- **Tiền điều kiện:** Mỗi tài khoản đã đăng nhập; cấu hình phòng khám tồn tại.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Cố sửa cấu hình clinic | PATCH /api/v1/clinic/settings | **403 Forbidden**, thiếu `settings.clinic` | Cấu hình giữ nguyên |
| 2 | Y tá (nurse_lan) | Cố sửa cấu hình clinic | PATCH /api/v1/clinic/settings | **403 Forbidden** | Cấu hình giữ nguyên |
| 3 | Dược sĩ (pharm_cuong) | Cố sửa cấu hình clinic | PATCH /api/v1/clinic/settings | **403 Forbidden** | Cấu hình giữ nguyên |
| 4 | Thu ngân (cashier_em) | Cố sửa cấu hình clinic | PATCH /api/v1/clinic/settings | **403 Forbidden** | Cấu hình giữ nguyên |
| 5 | Bác sĩ (dr_nguyen) | Cố sửa cấu hình clinic | PATCH /api/v1/clinic/settings | **403 Forbidden** | Cấu hình giữ nguyên |
| 6 | Admin (admin) | Kiểm chứng cấu hình không đổi + đối chứng sửa được | GET/PATCH /api/v1/clinic/settings | GET 200 giá trị nguyên vẹn; PATCH 200 (admin có quyền) | Dữ liệu đúng |

- **Kết quả cuối:** Cấu hình phòng khám không bị thay đổi bởi bất kỳ non-admin nào; chỉ admin sửa được.
- **Điểm kiểm chứng:** HTTP=403 cho cả 5 role non-admin; cấu hình không đổi sau các bước 1–5; audit DENIED permission=settings.clinic cho từng actor.
- **Liên kết function:** TC-CFG-023/025 (cấu hình clinic: validate + auth/permission/RLS, có nhánh 403), TENT-021 (TC-TENT — settings_update_without_permission_403 đã COVERED) trong cfg-test-catalog.md / tenant-test-catalog.md; TC-RBAC-006 (401/403/200) trong rbac-test-catalog.md.

---

### SC-RBAC-11 — Dược sĩ tạo hóa đơn (thiếu invoice.create)
- **Mục tiêu:** `invoice.create` chỉ thuộc Admin/Receptionist; Dược sĩ bị từ chối.
- **Vai trò & tài khoản:** Dược sĩ — `pharm_cuong` / `Pharm@1234`; đối chứng Lễ tân — `recept_anh` / `Recept@1234`.
- **Tiền điều kiện:** Có 1 visit AWAITING_PAYMENT (đã có VisitService/Prescription in_house) để lập hóa đơn.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Dược sĩ (pharm_cuong) | Login | POST /api/v1/auth/login | 200, JWT role=pharmacist | Có token |
| 2 | Dược sĩ (pharm_cuong) | Cố lập hóa đơn cho visit | POST /api/v1/invoices (visit_id=...) | **403 Forbidden**, thiếu `invoice.create` | Không tạo hóa đơn |
| 3 | Lễ tân (recept_anh) | Đối chứng lập hóa đơn hợp lệ | POST /api/v1/invoices (visit_id=...) | 201, invoice tạo từ VisitService + Prescription in_house | Có Invoice |
| 4 | Admin (admin) | Kiểm chứng | GET /api/v1/invoices?visit_id=... | 200, chỉ có hóa đơn do lễ tân tạo | Dữ liệu đúng |

- **Kết quả cuối:** Dược sĩ không tạo được hóa đơn; lễ tân tạo được (xác nhận ma trận đúng cả 2 chiều).
- **Điểm kiểm chứng:** HTTP=403 cho pharm_cuong; HTTP=201 cho recept_anh; no Invoice row từ dược sĩ; audit DENIED permission=invoice.create.
- **Liên kết function:** RBAC-* (rbac-test-catalog.md — Pharmacist thiếu invoice.create), BILL-* (bill-test-catalog.md).

---

### SC-RBAC-12 — Thu ngân quản lý danh mục kho (kiểm tra inventory.manage_catalog)
- **Mục tiêu:** `inventory.manage_catalog` chỉ thuộc Admin/Pharmacist. Thu ngân bị từ chối (negative chính); đối chứng Dược sĩ được phép (positive control).
- **Vai trò & tài khoản:** Thu ngân — `cashier_em` / `Cashier@1234` (negative); Dược sĩ — `pharm_cuong` / `Pharm@1234` (đối chứng).
- **Tiền điều kiện:** Danh mục kho/sản phẩm tồn tại. Cả hai tài khoản đã đăng nhập.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Thu ngân (cashier_em) | Cố tạo/sửa sản phẩm danh mục kho | POST /api/v1/inventory/products | **403 Forbidden**, thiếu `inventory.manage_catalog` | Danh mục giữ nguyên |
| 2 | Thu ngân (cashier_em) | Cố nhập batch | POST /api/v1/inventory/batches | **403 Forbidden** | Tồn kho không đổi |
| 3 | Dược sĩ (pharm_cuong) | Tạo sản phẩm (đối chứng quyền) | POST /api/v1/inventory/products | 201 (pharmacist có quyền) | Có sản phẩm mới (cleanup sau test) |
| 4 | Admin (admin) | Kiểm chứng | GET /api/v1/inventory/products | 200, không có sản phẩm do cashier tạo | Dữ liệu đúng |

- **Kết quả cuối:** Cashier không tạo được mục danh mục; pharmacist tạo được (xác nhận ma trận đúng cả 2 chiều).
- **Điểm kiểm chứng:** HTTP=403 cho cashier_em; HTTP=201 cho pharm_cuong; audit DENIED permission=inventory.manage_catalog cho cashier_em; no side-effect từ cashier.
- **Liên kết function:** RBAC-* (rbac-test-catalog.md — Cashier thiếu inventory.manage_catalog), MED-* (med-test-catalog.md — danh mục thuốc/kho), PHRM-* (phrm-test-catalog.md).

---

### SC-RBAC-13 — RLS đa tenant — clinic A đọc/ghi dữ liệu clinic B
- **Mục tiêu:** Xác nhận Row-Level Security cô lập dữ liệu theo clinic: tài khoản clinic A KHÔNG thấy/không thao tác được bản ghi clinic B (kể cả khi có đúng permission trong clinic của mình).
- **Vai trò & tài khoản:** Admin clinic A (DEMO) — `admin` / `Demo@1234`; cần 1 tài khoản admin clinic B (seed phụ) và biết trước `patient_id_B`, `visit_id_B`, `invoice_id_B` thuộc clinic B.
- **Tiền điều kiện:** Tồn tại ít nhất 2 clinic (A=DEMO, B=clinic phụ) với dữ liệu riêng.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Admin clinic A (admin) | Login clinic A | POST /api/v1/auth/login | 200, JWT clinic_id=A | Có token clinic A |
| 2 | Admin clinic A (admin) | Cố đọc BN clinic B theo id | GET /api/v1/patients/{patient_id_B} | **404 Not Found** (RLS lọc, coi như không tồn tại) | Không lộ dữ liệu B |
| 3 | Admin clinic A (admin) | Liệt kê BN (kiểm tra không lẫn) | GET /api/v1/patients | 200, CHỈ có BN clinic A | Cô lập danh sách |
| 4 | Admin clinic A (admin) | Cố sửa visit clinic B | PATCH /api/v1/visits/{visit_id_B} | **404 Not Found** (hoặc 403) | Không sửa được B |
| 5 | Admin clinic A (admin) | Cố void hóa đơn clinic B | POST /api/v1/invoices/{invoice_id_B}/void | **404 Not Found** (hoặc 403) | Hóa đơn B nguyên vẹn |
| 6 | Admin clinic B | Kiểm chứng dữ liệu B không đổi | GET /api/v1/invoices/{invoice_id_B} | 200 (trong clinic B), status không đổi | Dữ liệu B nguyên vẹn |

- **Kết quả cuối:** Dữ liệu clinic B hoàn toàn không bị clinic A đọc/sửa; danh sách clinic A không rò rỉ bản ghi clinic B.
- **Điểm kiểm chứng:** Đọc theo id cross-tenant → 404 (không 200, không lộ tồn tại); list không chứa row clinic B; mọi thao tác ghi cross-tenant → 404/403, no side-effect; bản ghi clinic B xác nhận không đổi khi admin B kiểm tra; audit ghi attempt cross-tenant với clinic_id mismatch.
- **Liên kết function:** TC-TENT-037 (cô lập RLS clinic mới khỏi clinic khác — đã COVERED bởi test_rls_isolation_cms_app_role.py), TC-TENT-038 (app role rolbypassrls=false), TC-RBAC-009/012/035/042 (cô lập RBAC/audit theo clinic — non-functional/tenant-test-catalog.md + functional/rbac-test-catalog.md). Cũng đối chiếu CFG-021/023/025 (prefix/cấu hình cô lập RLS) trong cfg-test-catalog.md.

---

## Ghi chú truy vết & vận hành test

- **Đồng bộ payload BE (2026-05-31, theo `handoff/scenario-review.md`):** các bước negative ở nhóm này gọi void/create nên payload ít bị ảnh hưởng — void HĐ dùng field `reason` (đúng). Khi đối chứng positive có thanh toán/hủy/discount: payment dùng `payment_method` (lowercase), hủy visit dùng `cancel_reason`, discount dùng `discount_amount`+`discount_reason`.
- Toàn bộ kịch bản nhóm này là **negative phân quyền** → tiêu chí PASS = nhận đúng **403** (hoặc **404** cho cross-tenant theo cơ chế RLS) VÀ không phát sinh side-effect.
- Catalog function tham chiếu (tên file & prefix đã đối chiếu trực tiếp trong `deliveries/test-cases/`):
  - `functional/rbac-test-catalog.md` — prefix `RBAC-` (RBAC-001..040 bao trùm toàn bộ permission matrix; RBAC-002 Receptionist kê đơn bị chặn, RBAC-003 Nurse cấp phát bị chặn, RBAC-004 Cashier void bị chặn — chính là backbone của nhóm negative này).
  - `functional/rx-test-catalog.md` (RX-*), `bill-test-catalog.md` (BILL-*), `phrm-test-catalog.md` (PHRM-*), `visit-test-catalog.md` (VISIT-*), `vital-test-catalog.md` (VITAL-*), `patient-test-catalog.md` (PATIENT-*), `cfg-test-catalog.md` (CFG- settings.clinic), `rpt-test-catalog.md` (RPT- report.financial), `med-test-catalog.md` (MED- danh mục thuốc/kho), `hr-test-catalog.md` (HR- user.manage).
  - `non-functional/tenant-test-catalog.md` — prefix `TENANT-` (TENANT-001.. cross-clinic RLS denial) cho kịch bản SC-RBAC-13.
- **Test case 403 đã tồn tại trong catalog** (tái sử dụng pattern): TC-RBAC-006, TC-RBAC-011, TC-RBAC-014, TC-RBAC-016, TC-RBAC-026, TC-RBAC-034, TC-RBAC-045 (đều có nhánh "user thiếu quyền → 403"); TC-RBAC-050/051 (SoD self-approve → 403, hiện MISSING/chưa ship); TC-TENT-021 (tạo clinic không quyền → 403, đã COVERED). Các case của nhóm SC-RBAC này mở rộng pattern đó sang đúng cặp (vai trò demo cụ thể × permission BA §13.6).
- **Lưu ý ma trận quyền:** Theo TC-RBAC-002 mỗi system role map đúng tập permission BA §13.5/§13.6 (vd receptionist KHÔNG có prescription.create; pharmacist có pharmacy.dispense). SC-RBAC-09 (bác sĩ xem report.financial) vẫn đúng vì doctor không có quyền report; nếu cấu hình cho Cashier xem report thì kiểm tra riêng theo catalog.
- **Trạng thái catalog:** rbac-test-catalog.md COVERED đầy đủ RBAC-001..009 + 013 (core RBAC + audit, TASK-004/002); tenant-test-catalog.md có TC-TENT-037/038 RLS COVERED (test_rls_isolation_cms_app_role.py). Endpoint trong cột "API/Endpoint gợi ý" là gợi ý chuẩn REST `/api/v1/*`; cần khớp lại với `clinic_management_system_design.md` trước khi tự động hóa (đặc biệt route void hóa đơn, dispense, reports/financial, clinic/settings, inventory).
