# Báo cáo Bug — E2E Playwright (Luồng Vận hành Theo Vai trò)

**Ngày test:** 2026-05-31
**Tool:** MCP Playwright → FE http://localhost:1420 + BE http://localhost:8001
**Tester:** Claude E2E Agent (Playwright MCP)
**Kịch bản thực thi:** SC-HP-01, SC-HP-03, SC-HP-04, SC-EXC-01, SC-RBAC-06 + kiểm tra phát sinh
**Tổng:** ✅ 8 PASS · 🔴 2 BUG P0 · 🟠 5 BUG P1 · 🟡 3 BUG P2

---

## 🔴 BUG-001 — P0 CRITICAL: Bác sĩ xem được báo cáo doanh thu

| Trường | Giá trị |
|---|---|
| **Kịch bản** | SC-RBAC-06 |
| **Severity** | P0 — vi phạm phân quyền nghiệp vụ |
| **Ảnh hưởng** | Toàn bộ bác sĩ có role `doctor` |

**Mô tả:**
Bác sĩ đăng nhập → vào `/reports/revenue` → trang "Báo cáo doanh thu" hiển thị hoàn toàn, không bị chặn. Theo BA §13.6, quyền `report.financial` **chỉ thuộc Admin**.

**Root cause (đã xác nhận qua API):**
Seed data migration `0007_seed_permissions_and_roles.py` nhầm cấp `report.financial` + `report.view` cho role `doctor`. JWT của dr_nguyen chứa:
```json
"permissions": [..., "report.financial", "report.view", ...]
```

**Bằng chứng:**
- Screenshot: `screenshots/bug-rbac-06-doctor-sees-revenue.png`
- API: `GET /reports/revenue?start=2026-01-01&end=2026-05-31` với token doctor → HTTP 200

**Hướng sửa:**
1. Xóa `report.financial` (và `report.view` nếu không cần) khỏi seed permissions của role `doctor`
2. Bổ sung guard `require_permission("report.financial")` trên `/reports/revenue` endpoint
3. FE cần kiểm tra permission trước khi hiển thị nav item "Báo cáo" cho doctor

---

## 🔴 BUG-002 — P0 CRITICAL: Nhập sinh hiệu thất bại (HTTP 500)

| Trường | Giá trị |
|---|---|
| **Kịch bản** | SC-HP-01 Bước 2 (vitals) |
| **Severity** | P0 — chặn toàn bộ luồng khám |
| **Endpoint** | `POST /api/v1/visits/{id}/vitals` |

**Mô tả:**
Bác sĩ điền đầy đủ sinh hiệu (HA tâm thu, HA tâm trương, nhiệt độ, mạch, SpO2, cân nặng, chiều cao) rồi nhấn "Lưu sinh hiệu" → server trả **HTTP 500**, UI vẫn hiển thị "Chưa có dữ liệu sinh hiệu", **không có thông báo lỗi cho người dùng**.

**Bằng chứng (console browser):**
```
[ERROR] Failed to load resource: the server responded with a status of 500 (Internal Server Error)
@ http://localhost:1420/api/v1/visits/927f2aa9-bfba-4616-885e-8ca1794ef188/vitals:0
```

**Hậu quả:**
- Luồng SC-HP-01 bị chặn hoàn toàn tại bước nhập sinh hiệu
- Người dùng không biết có lỗi → nhập lại nhiều lần vô ích
- Cần điều tra log BE để tìm nguyên nhân 500 (có thể liên quan payload format hoặc vitals schema migration)

**Hướng sửa:**
1. Điều tra server log: `docker logs --tail 100 clinic_cms_w2e_api | grep -A5 ERROR`
2. FE phải hiện thông báo lỗi khi API trả 500 (hiện đang nuốt lỗi silently)
3. Kiểm tra payload format: API kỳ vọng `{"values": {...}}` hay `{"pulse": ..., "systolic_bp": ...}`

---

## 🟠 BUG-003 — P1 MAJOR: Doctor queue hiển thị UUID thay vì tên bệnh nhân

| Trường | Giá trị |
|---|---|
| **Kịch bản** | SC-HP-01 Bước 3 (bác sĩ gọi BN) |
| **Severity** | P1 — UI không dùng được |
| **Màn hình** | `/doctor/queue` |

**Mô tả:**
Mỗi card bệnh nhân trong hàng đợi bác sĩ hiển thị UUID thô thay vì tên BN:
```
BN E2E 1780165413    ← Visit #20260530-014, patient name OK (trường hợp may mắn)
3d618281-a1d1-41d7-872b-f6af98362c82  ← UUID thay vì tên
```

**Bằng chứng:** Screenshot `screenshots/bug-doctor-queue-uuid-instead-of-name.png`

**Hướng sửa:** FE component `DoctorQueueCard` dùng sai field — cần dùng `patient.full_name` thay vì `patient.id` hoặc `patient_id`.

---

## 🟠 BUG-004 — P1 MAJOR: Hàng đợi ô nhiễm nghiêm trọng bởi test data cũ

| Trường | Giá trị |
|---|---|
| **Kịch bản** | SC-HP-01, SC-HP-04, SC-VAR-03 |
| **Severity** | P1 — cản trở vận hành demo/staging |
| **Màn hình** | `/queue` |

**Mô tả:**
Hàng đợi khám chứa **73 visit "Chờ khám"** và **24 visit "Đang khám"** tồn đọng từ các lần chạy regression/smoke test (từ 2026-05-18, 05-29, 05-30). Không có cơ chế tự dọn, không có UI để admin clear queue. Visit cũ nhất từ `2026-05-03` vẫn "Đang khám".

**Bằng chứng:** Screenshot `screenshots/bug-queue-pollution-73-visits.png`

**Hướng sửa:**
1. Thêm script seed cleanup hoặc migration để reset visit status cũ
2. Xem xét tính năng admin "Archive stale visits" (visit >7 ngày không hoàn tất)
3. Demo environment cần có cron job auto-cancel visit quá hạn

---

## 🟠 BUG-005 — P1 MAJOR: Dashboard bác sĩ gọi API ngoài quyền → 403 floods

| Trường | Giá trị |
|---|---|
| **Kịch bản** | Login dr_nguyen, dashboard |
| **Severity** | P1 — hiệu năng + noise |
| **Màn hình** | `/dashboard` |

**Mô tả:**
Ngay sau khi bác sĩ đăng nhập vào dashboard, FE gọi liên tục (mỗi vài giây) các API **ngoài quyền** của bác sĩ:
```
GET /api/v1/reports/revenue?start=...&end=...&granularity=daily → 403 (lặp 6+ lần/session)
GET /api/v1/shifts?from=...&to=... → 403 (lặp 3+ lần/session)
```

**Hậu quả:** Console 100+ errors, tạo tải vô ích lên server, khó debug log thật.

**Hướng sửa:**
- Dashboard component check permission trước khi gọi API: `if (hasPermission("report.financial")) fetchRevenue()`
- Widget "Ca trực" và "Doanh thu" không nên render cho doctor

---

## 🟠 BUG-006 — P1 MAJOR: Danh sách hóa đơn hiển thị UUID thay vì số hóa đơn

| Trường | Giá trị |
|---|---|
| **Kịch bản** | SC-EXC-01 Bước 4 |
| **Severity** | P1 — UI không đọc được |
| **Màn hình** | `/billing/invoices` |

**Mô tả:**
Cột "Số hóa đơn" trong danh sách hiển thị UUID rút gọn (vd `60a8b5fe…`) thay vì số hóa đơn có nghĩa (vd `INV-2026-001`). Nhiều hóa đơn draft 0₫ từ test cũ không có invoice number.

**Hướng sửa:**
- Nếu `invoice_number` là NULL → hiển thị `"Chờ phát hành"` thay vì UUID
- FE component InvoiceList dùng field `invoice_number` (không fallback sang `id`)

---

## 🟠 BUG-007 — P1 MAJOR: Trùng số điện thoại bệnh nhân trong DB

| Trường | Giá trị |
|---|---|
| **Kịch bản** | SC-VAR-01 (tìm BN theo SĐT) |
| **Severity** | P1 — vi phạm data integrity |
| **Màn hình** | `/patients` |

**Mô tả:** Trang bệnh nhân có ít nhất 6 cặp BN trùng SĐT:
| SĐT | BN 1 | BN 2 |
|---|---|---|
| 0922150072 | BN0022 Nguyễn Thị Ánh Hồng | BN0023 Duplicate Phone Patient |
| 0923118653 | BN0026 Nguyễn Thị Ánh Hồng | BN0027 Duplicate Phone Patient |
| 0923761866 | BN0030 Nguyễn Thị Ánh Hồng | BN0031 Duplicate Phone Patient |
| 0924863963 | BN0034 Nguyễn Thị Ánh Hồng | BN0035 Duplicate Phone Patient |
| 0987654321 | BN0019 Đỗ Văn CHiển | BN0020 Nguyễn Văn E2E Test |

**Hậu quả:** SC-VAR-01 (tìm BN theo SĐT) sẽ trả 2+ kết quả → lễ tân không biết chọn BN nào.

**Hướng sửa:**
1. Thêm UNIQUE constraint trên `patient.phone` per clinic (nếu chưa có)
2. Dọn dữ liệu test trùng trong môi trường demo
3. FE cảnh báo khi tìm thấy >1 BN cùng SĐT

---

## 🟡 BUG-008 — P2 MINOR: [useSync] Tauri SQL lỗi liên tục trong browser mode

| Trường | Giá trị |
|---|---|
| **Kịch bản** | Mọi kịch bản |
| **Severity** | P2 — noisy, không crash |

**Mô tả:**
Khi chạy FE ở browser (không phải Tauri desktop), hook `useSync` cố load Tauri SQL plugin và fail mỗi ~2 giây:
```
[ERROR] [useSync] Sync error: Error: Failed to load Tauri SQL plugin.
Ensure app is running in Tauri context.
```
Tạo ra 50-80 error/session, che khuất lỗi thật trong console.

**Hướng sửa:** `useSync` cần guard: `if (!window.__TAURI__) return; // Skip sync in browser mode`

---

## 🟡 BUG-009 — P2: Demo data không có invoice đã thanh toán

| Trường | Giá trị |
|---|---|
| **Kịch bản** | SC-EXC-01 (void invoice) |
| **Severity** | P2 — giới hạn khả năng test |

**Mô tả:**
Filter "Đã thanh toán" và "Đã phát hành" trong `/billing/invoices` đều trả "Không có hóa đơn nào". `seed_demo_data.py` không tạo invoice ở các trạng thái cuối (PAID, ISSUED). Không thể test SC-EXC-01 (void + hoàn tiền) qua UI.

**Hướng sửa:** Bổ sung vào `seed_demo_data.py` một số invoice ISSUED + PAID để demo flow thanh toán hoàn chỉnh.

---

## 🟡 BUG-010 — P2: Bệnh nhân thiếu thông tin (ngày sinh, SĐT null)

| Trường | Giá trị |
|---|---|
| **Severity** | P2 — data quality |

**Mô tả:**
- BN0019 (`Đỗ Văn CHiển`): ngày sinh = `"1999"` (thiếu tháng+ngày)
- BN0021 (`chiển`): SĐT = `"—"` (null), tên viết thường không chuẩn
- Nhiều BN tên = `"Bệnh Nhân Smoke Test"` — không đại diện nghiệp vụ thực

**Hướng sửa:** Cải thiện validation khi nhập BN (ngày sinh phải đủ định dạng DD/MM/YYYY) và dọn lại seed data.

---

## ✅ Kết quả PASS

| Kịch bản | Bước | Kết quả |
|---|---|---|
| SC-HP-01 | B1: Tạo visit walk-in (lễ tân) | ✅ Toast "Tạo lượt khám thành công! Số 20260530-028" |
| SC-HP-01 | B2: Visit xuất hiện cột "Đăng ký" trong queue board | ✅ Count=1 |
| SC-HP-01 | B3: Bác sĩ "Gọi BN tiếp theo" → vào consultation | ✅ Redirect đúng `/doctor/visits/{id}` |
| SC-HP-01 | B4: Tìm kiếm thuốc trong tab Kê đơn | ✅ Trả đúng kết quả (Paracetamol × 4) |
| SC-HP-01 | B5: Thêm thuốc vào đơn + lưu | ✅ Đơn thuốc lưu thành công, xuất hiện nút "In đơn thuốc" |
| SC-HP-04 | Priority=5 lưu đúng | ✅ Visit tạo với priority=5 |
| SC-HP-04 | Queue sort priority DESC | ✅ Visit priority cao đứng đầu |
| SC-VAR-01 | Tìm BN theo SĐT (1 kết quả) | ✅ Cho BN mới tạo (không trùng SĐT) |

---

## Tổng kết

| Severity | Số bug | Bug IDs |
|---|---|---|
| 🔴 P0 Critical | 2 | BUG-001 (quyền doctor sai), BUG-002 (vitals 500) |
| 🟠 P1 Major | 5 | BUG-003 (UUID queue), BUG-004 (queue pollution), BUG-005 (dashboard 403), BUG-006 (UUID invoice), BUG-007 (duplicate phone) |
| 🟡 P2 Minor | 3 | BUG-008 (Tauri sync), BUG-009 (no paid invoice), BUG-010 (bad demo data) |

**Ưu tiên sửa ngay (block release):**
1. **BUG-001** — Fix seed permissions doctor (xóa `report.financial`)
2. **BUG-002** — Điều tra 500 lỗi POST /vitals + fix FE hiển thị lỗi
3. **BUG-003** — Fix FE component doctor queue hiển thị đúng tên BN

**Screenshots:** `docs/tasks/TASK-052/deliveries/test-reports/screenshots/`
