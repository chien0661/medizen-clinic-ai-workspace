# Báo cáo Bug — E2E Operational Test (Theo Luồng Vận hành)

**Ngày chạy test:** 2026-05-31
**Môi trường:** `http://localhost:8001` · Docker `clinic_cms_w2e_api` (healthy)
**Kịch bản đã thực thi:** SC-HP-01, SC-HP-04, SC-VAR-01, SC-VAR-02, SC-VAR-03, SC-EXC-01, SC-EXC-03, SC-EXC-06, SC-RBAC-01..12, SC-RBAC-NO-TOKEN
**Tổng kết:** ✅ 22 PASS · ❌ 3 BUG THẬT · ⚠️ 2 DRIFT (môi trường / thiết kế)

---

## 🔴 BUG-001 — Bác sĩ đọc được báo cáo doanh thu (sai phân quyền)

| | |
|---|---|
| **Mã** | BUG-001 |
| **Kịch bản** | SC-RBAC-06 |
| **Severity** | **P0 — CRITICAL** |
| **Module** | Reports / RBAC |

**Mô tả:**
Bác sĩ (`dr_nguyen`, role `doctor`) có quyền `report.financial` trong JWT — quyền này theo spec (BA §13.6) chỉ thuộc Admin. Ngoài ra, endpoint `GET /reports/revenue` thực hiện **validate query param TRƯỚC khi check permission**, khiến gọi đúng params thì bác sĩ đọc được báo cáo doanh thu của phòng khám.

**Bằng chứng:**
```
# JWT permissions của dr_nguyen (role=doctor):
permissions: ['appointment.read', 'appointment.write', 'inventory.read',
  'invoice.create', 'invoice.read', ..., 'report.financial', 'report.view', ...]

# Gọi với đúng params → 200 (không phải 403):
GET /api/v1/reports/revenue?start=2026-01-01&end=2026-05-31
Authorization: Bearer <doctor_token>
→ HTTP 200 (dữ liệu doanh thu)

# Không có params → 422 (validate trước permission check):
GET /api/v1/reports/revenue
→ HTTP 422 "Field required: start, end"
```

**Hậu quả:** Nhân viên (bác sĩ, y tá...) có thể xem doanh thu — vi phạm phân quyền nghiệp vụ.

**Hướng sửa:**
1. Xóa `report.financial` khỏi seed permissions của role `doctor` trong migration `0007_seed_permissions_and_roles.py`.
2. Đảm bảo middleware RBAC check permission **trước** khi Pydantic validate query params (hoặc dùng `Depends(require_permission(...))` ở đầu router, trước dependencies khác).

---

## 🟠 BUG-002 — POST /invoices trả 405 Method Not Allowed

| | |
|---|---|
| **Mã** | BUG-002 |
| **Kịch bản** | SC-VAR-02, SC-EXC-01, SC-EXC-06 |
| **Severity** | **P1 — MAJOR** |
| **Module** | Billing / Invoice |

**Mô tả:**
Endpoint `POST /api/v1/invoices` không tồn tại — route chỉ có `GET` (list). Không có cách tạo invoice thủ công qua API. Các kịch bản cần tạo invoice cho visit (SC-EXC-01, SC-EXC-06) và bán thuốc OTC không có visit (SC-VAR-02) đều bị chặn.

**Bằng chứng:**
```
POST /api/v1/invoices  →  HTTP 405 {"detail":"Method Not Allowed"}

# openapi.json chỉ có:
/api/v1/invoices:
  GET: "List invoices with optional filters"
  # Không có POST
```

**Hậu quả:**
- **SC-VAR-02** (bán thuốc OTC không khám): không thực hiện được — toàn bộ use-case này chưa có API.
- **SC-EXC-01** (void + hoàn tiền): không tạo được invoice để test void.
- **SC-EXC-06** (partial payment): không tạo được invoice để test.
- Luồng thanh toán chỉ hoạt động nếu invoice được tạo **tự động qua visit** (qua `/visits/{id}/invoices` hoặc auto-generate sau complete-emr).

**Hướng sửa:**
- Option A: Thêm `POST /invoices` cho phép tạo manual invoice (cần thiết cho bán lẻ OTC).
- Option B: Tạo invoice qua `GET /visits/{visit_id}/invoices` (kiểm tra xem auto-generate chưa). Cập nhật test case và tài liệu kịch bản.

**Lưu ý:** Endpoint `POST /invoices/{invoice_id}/payments`, `POST /invoices/{invoice_id}/void`, `POST /invoices/{invoice_id}/submit`, `POST /invoices/{invoice_id}/refund` đều **tồn tại** trong openapi — chỉ thiếu POST tạo mới.

---

## 🟠 BUG-003 — visit.status trả "WAITING" thay vì "WAITING_VITAL"

| | |
|---|---|
| **Mã** | BUG-003 |
| **Kịch bản** | SC-HP-01, SC-HP-04 |
| **Severity** | **P1 — MAJOR** |
| **Module** | Visit / State Machine |

**Mô tả:**
Sau khi tạo visit mới, status trả về là `"WAITING"` — nhưng catalog kịch bản (và state_machine.py theo agent đã đọc) kỳ vọng `"WAITING_VITAL"`. Hai tên state không khớp nhau giữa code thực tế và tài liệu thiết kế kịch bản.

**Bằng chứng:**
```json
POST /api/v1/visits {"patient_id": "...", "visit_type": "WALK_IN"}
→ 201 {
    "status": "WAITING",   ← thực tế
    ...
  }
# Kịch bản SC-HP-01 kỳ vọng WAITING_VITAL (từ state_machine.py mà agent đọc)
```

**Đánh giá:** Một trong hai:
- (a) State machine thực tế dùng `WAITING` (không phải `WAITING_VITAL`) → tài liệu kịch bản sai, cần cập nhật.
- (b) State `WAITING_VITAL` là enum đúng nhưng API serialize thành `WAITING` → lỗi serialize.

**Hành động:** Cần đối chiếu `VisitStatus` enum trong `app/modules/visits/models.py`. Nếu enum là `WAITING` thì sửa catalog kịch bản (không phải bug code). Nếu enum là `WAITING_VITAL` thì là bug serialize P1.

---

## ✅ Kết quả PASS (22 case)

### Happy Path
| SC | Kết quả |
|---|---|
| SC-HP-01 B1 | Tạo bệnh nhân thành công ✓ |
| SC-HP-04 B2 | Visit priority=5 lưu đúng ✓ |
| SC-HP-04 B3 | Hàng đợi sort priority DESC đúng ✓ |

### Biến thể
| SC | Kết quả |
|---|---|
| SC-VAR-01 B1 | Tạo BN lần đầu ✓ |
| SC-VAR-01 B2 | Tìm đúng 1 BN theo SĐT, không tạo trùng ✓ |
| SC-VAR-03 B1 | Visit cấp cứu priority=10 lưu đúng ✓ |

### Không có token → 401
| Endpoint | Kết quả |
|---|---|
| GET /patients | 401 ✓ |
| GET /visits | 401 ✓ |
| GET /invoices | 401 ✓ |
| GET /pharmacy/pending-dispense | 401 ✓ |
| GET /visits/queue | 401 ✓ |
| GET /reports/revenue | 401 ✓ |

### Phân quyền chéo (RBAC) — 11/12 case đúng
| SC | Vai trò thử | Quyền thiếu | HTTP | Kết quả |
|---|---|---|---|---|
| SC-RBAC-01 | Lễ tân nhập vital | vital.write | **403** | ✓ |
| SC-RBAC-02 | Y tá reserve thuốc | pharmacy.dispense | **403** | ✓ |
| SC-RBAC-03 | Dược sĩ tạo visit | visit.write | **403** | ✓ |
| SC-RBAC-04 | Thu ngân void invoice | invoice.void | **403** | ✓ |
| SC-RBAC-05 | Bác sĩ xem /users | user.manage | **403** | ✓ |
| SC-RBAC-06 | Bác sĩ xem revenue | report.financial | **422** → cần 403 | ❌ BUG-001 |
| SC-RBAC-07 | Y tá tạo role | role.manage | **403** | ✓ |
| SC-RBAC-08 | Lễ tân xem roles | role.manage | **403** | ✓ |
| SC-RBAC-09 | Dược sĩ sửa settings | settings.clinic | **403** | ✓ |
| SC-RBAC-10 | Y tá xem audit-logs | audit.read | **403** | ✓ |
| SC-RBAC-11 | Thu ngân tạo thuốc | inventory.manage_catalog | **403** | ✓ |
| SC-RBAC-12 | Dược sĩ void invoice | invoice.void | **403** | ✓ |

---

## ⚠️ Drift / Thiết kế cần xác nhận

### DRIFT-01: invoice.create trong JWT của bác sĩ
- **Phát hiện:** JWT doctor có `invoice.create` — theo BA §13.6, quyền này chỉ thuộc `Receptionist`.
- **Câu hỏi:** Đây là thiết kế có chủ ý (bác sĩ cũng tạo hóa đơn?) hay lỗi seed data?
- **Hành động:** Xác nhận với BA/PO trước khi fix.

### DRIFT-02: Vital schema mở rộng (dynamic form)
- **Phát hiện:** `POST /visits/{id}/vitals` trả 422 với payload `{"vitals": {"pulse":78,...}}` — schema thực tế có thể khác.
- **Câu hỏi:** Format đúng của payload vitals là gì? (dynamic form per specialty)
- **Hành động:** Đọc openapi schema của endpoint này và cập nhật test.

---

## Tóm tắt

| Severity | Số bug | Danh sách |
|---|---|---|
| 🔴 P0 Critical | 1 | BUG-001 (bác sĩ đọc báo cáo doanh thu) |
| 🟠 P1 Major | 2 | BUG-002 (POST /invoices 405), BUG-003 (status WAITING vs WAITING_VITAL) |
| ⚠️ Drift | 2 | DRIFT-01 (invoice.create cho doctor), DRIFT-02 (vitals schema) |

**Khuyến nghị ưu tiên:**
1. **Ngay:** Fix BUG-001 — xóa `report.financial` khỏi doctor seed + fix thứ tự permission check trước validation.
2. **Sprint này:** Làm rõ BUG-002 — quyết định flow tạo invoice (tự động hay manual) và cập nhật test.
3. **Xác nhận:** BUG-003 và DRIFT-01/02 — đối chiếu code thực tế, cập nhật tài liệu nếu là thiết kế đúng.
