# Test Case Catalog — RPT · Báo cáo & Thống kê

**Nguồn:** function_list_data.py (group RPT) + clinic_management_function_list.md + system_design §14 (Module Reporting) / BA §1312.
**Phạm vi:** 18 functions (RPT-001 … RPT-018).  **Tổng test case:** 54.  **Ngày:** 2026-05-30.

> ### Ghi chú nguồn & coverage
> - 18 function RPT trích từ `function_list_data.py` (dòng 1223–1274) và bảng `clinic_management_function_list.md` (dòng 414–431).
> - **Status (nguồn):** trong function_list.md cột status, RPT-001…RPT-016 = ⬜ (TODO), RPT-017/RPT-018 = 💡 (ý tưởng/backlog v3). Phase: RPT-001…015 = v1, RPT-016/017 = v2, RPT-018 = v3.
> - **default_role:** đa số `Admin`; RPT-008 = `Pharmacist`; RPT-013 = `All`.
> - **Đối chiếu code thực tế:** submodule `E:/MyProject/clinic-cms` chưa được khởi tạo (uninitialized — git status hiển thị `M ../clinic-cms`); không tìm thấy module `reporting`/`reports` đã ship, cũng không có test báo cáo trong thư mục `tests`, và không có catalog cũ TASK-001..TASK-051 đề cập RPT. system_design §1632 xếp Reporting vào "Sprint 14" (tương lai).
> - ⇒ **Coverage hiện tại của TẤT CẢ test case = MISSING** (chưa có code, chưa có test). Catalog này là đặc tả test định hướng cho khi triển khai.
>
> ### Giả định kiến trúc & nghiệp vụ (theo PROJECT.md + system_design §14)
> - FastAPI + PostgreSQL Row-Level Security (RLS) đa tenant theo `clinic_id`; RBAC theo permission; Redis cache (báo cáo hay dùng có thể cache — phase sau); offline qua Tauri.
> - Báo cáo là **read-only, pull-based on-demand** (v1 KHÔNG có dashboard real-time).
> - Permission: `report.view` (xem báo cáo vận hành), `report.financial` (báo cáo tài chính/doanh thu/công nợ — chỉ Admin/owner). RPT-008 (thuốc sắp hết hạn) thuộc quyền dược (Pharmacist).
> - Quy tắc tính: **Doanh thu = tổng invoice trạng thái `paid`** (loại draft/void; refund trừ net); **Công nợ = invoice có `balance > 0`** (snapshot); thống kê visit chỉ tính lượt **completed**.
> - Mọi báo cáo hỗ trợ filter `from`/`to`; group_by `day|week|month` khi áp dụng; export CSV/PDF.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| RPT-001 | Doanh thu theo ngày/tuần/tháng (Line chart + KPI) | TODO (⬜ v1) | TC-RPT-001, TC-RPT-002, TC-RPT-003 | MISSING |
| RPT-002 | Doanh thu theo bác sĩ (breakdown per doctor) | TODO (⬜ v1) | TC-RPT-004, TC-RPT-005 | MISSING |
| RPT-003 | Doanh thu theo phương thức (Cash/Card/QR/BHYT) | TODO (⬜ v1) | TC-RPT-006, TC-RPT-007 | MISSING |
| RPT-004 | Số visit theo specialty (chuyên khoa) | TODO (⬜ v1) | TC-RPT-008, TC-RPT-009 | MISSING |
| RPT-005 | Top thuốc dùng (Top N theo doanh thu/số lượng) | TODO (⬜ v1) | TC-RPT-010, TC-RPT-011 | MISSING |
| RPT-006 | Thuốc ít dùng (gợi ý ngừng nhập) | TODO (⬜ v1) | TC-RPT-012, TC-RPT-013 | MISSING |
| RPT-007 | Tồn kho theo giá vốn (tổng giá trị tồn kho) | TODO (⬜ v1) | TC-RPT-014, TC-RPT-015 | MISSING |
| RPT-008 | Thuốc sắp hết hạn (list 30/60/90 ngày) | TODO (⬜ v1) | TC-RPT-016, TC-RPT-017, TC-RPT-018 | MISSING |
| RPT-009 | No-show rate (tỷ lệ vắng hẹn) | TODO (⬜ v1) | TC-RPT-019, TC-RPT-020 | MISSING |
| RPT-010 | Demographic BN (tuổi/giới/tỉnh) | TODO (⬜ v1) | TC-RPT-021, TC-RPT-022 | MISSING |
| RPT-011 | Visit duration (thời gian khám TB) | TODO (⬜ v1) | TC-RPT-023, TC-RPT-024 | MISSING |
| RPT-012 | Wait time (thời gian chờ TB) | TODO (⬜ v1) | TC-RPT-025, TC-RPT-026 | MISSING |
| RPT-013 | Custom date range (filter mọi report) | TODO (⬜ v1) | TC-RPT-027, TC-RPT-028, TC-RPT-029, TC-RPT-030 | MISSING |
| RPT-014 | Export CSV (mọi report) | TODO (⬜ v1) | TC-RPT-031, TC-RPT-032, TC-RPT-033, TC-RPT-034 | MISSING |
| RPT-015 | Export PDF (report có letterhead) | TODO (⬜ v1) | TC-RPT-035, TC-RPT-036, TC-RPT-037 | MISSING |
| RPT-016 | Scheduled email reports (tự động tuần/tháng) | TODO (⬜ v2) | TC-RPT-038, TC-RPT-039, TC-RPT-040, TC-RPT-041, TC-RPT-042 | MISSING |
| RPT-017 | Patient retention (tỷ lệ BN quay lại) | IDEA (💡 v2) | TC-RPT-043, TC-RPT-044, TC-RPT-045 | MISSING |
| RPT-018 | Clinical KPIs (outcome lâm sàng) | IDEA (💡 v3) | TC-RPT-046, TC-RPT-047, TC-RPT-048 | MISSING |
| (xuyên suốt) | Bảo mật & RLS chung cho mọi report | — | TC-RPT-049, TC-RPT-050, TC-RPT-051, TC-RPT-052, TC-RPT-053, TC-RPT-054 | MISSING |

**Tổng hợp coverage theo function:** COVERED = 0 · PARTIAL = 0 · MISSING = 18.

---

## 2. Chi tiết Test Cases

### TC-RPT-001 — Doanh thu theo ngày (happy path)
- **Function:** RPT-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập role Admin clinic A; clinic A có ≥3 invoice `paid` ngày 2026-05-29.
- **Bước thực hiện:** 1) GET `/api/v1/reports/revenue?group_by=day&from=2026-05-29&to=2026-05-29`. 2) Đọc body.
- **Dữ liệu test:** 3 invoice paid: 200.000 / 350.000 / 150.000 VND.
- **Kết quả mong đợi:** HTTP 200; `summary.total = 700000`; `breakdown` 1 bucket `2026-05-29` = 700000; shape `{ summary:{total,count}, breakdown:[{period,amount}], currency:"VND" }`.
- **Coverage hiện tại:** MISSING

### TC-RPT-002 — Doanh thu group_by tuần/tháng (happy path)
- **Function:** RPT-001
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice paid rải trên 2 tháng.
- **Bước thực hiện:** 1) Gọi `group_by=month&from=2026-04-01&to=2026-05-31`. 2) Lặp `group_by=week`.
- **Dữ liệu test:** tháng 4 = 1.000.000, tháng 5 = 2.000.000.
- **Kết quả mong đợi:** HTTP 200; month trả 2 bucket (2026-04, 2026-05), tổng 3.000.000; số bucket week khớp số tuần có dữ liệu; nhãn period ISO chuẩn.
- **Coverage hiện tại:** MISSING

### TC-RPT-003 — Chỉ tính invoice paid, loại draft/void, trừ refund (edge nghiệp vụ)
- **Function:** RPT-001
- **Loại:** Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Range chứa invoice paid/draft/void/refund.
- **Bước thực hiện:** 1) Gọi revenue cho range chứa tất cả.
- **Dữ liệu test:** paid 500k, draft 200k, void 100k, refund -150k.
- **Kết quả mong đợi:** HTTP 200; `total = 350000` (500k − 150k); draft & void không tính.
- **Coverage hiện tại:** MISSING

### TC-RPT-004 — Doanh thu theo bác sĩ (happy path)
- **Function:** RPT-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** ≥2 bác sĩ có invoice paid gắn `doctor_id`.
- **Bước thực hiện:** 1) GET `/api/v1/reports/revenue?breakdown_by=doctor&from=...&to=...`.
- **Dữ liệu test:** BS1 600k, BS2 400k.
- **Kết quả mong đợi:** HTTP 200; 2 nhóm (BS1=600k, BS2=400k); tổng nhóm = tổng toàn cục 1.000.000; mỗi nhóm có `doctor_id`+`doctor_name`.
- **Coverage hiện tại:** MISSING

### TC-RPT-005 — Doanh thu theo bác sĩ khi invoice không gắn bác sĩ (edge)
- **Function:** RPT-002
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có invoice paid `doctor_id = null` (vd bán thuốc trực tiếp).
- **Bước thực hiện:** 1) Gọi breakdown_by=doctor.
- **Dữ liệu test:** BS1 300k, không-bác-sĩ 200k.
- **Kết quả mong đợi:** HTTP 200; nhóm "Không xác định/Khác" = 200k; tổng = 500k; không rớt bản ghi (no data loss).
- **Coverage hiện tại:** MISSING

### TC-RPT-006 — Doanh thu theo phương thức thanh toán (happy path)
- **Function:** RPT-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice paid với phương thức Cash/Card/QR/BHYT.
- **Bước thực hiện:** 1) GET `/api/v1/reports/revenue?breakdown_by=payment_method`.
- **Dữ liệu test:** Cash 300k, Card 250k, QR 200k, BHYT 250k.
- **Kết quả mong đợi:** HTTP 200; 4 nhóm đúng số; tổng = 1.000.000.
- **Coverage hiện tại:** MISSING

### TC-RPT-007 — Thanh toán hỗn hợp (split payment) phân bổ đúng (edge)
- **Function:** RPT-003
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 1 invoice trả 1 phần Cash + 1 phần Card.
- **Bước thực hiện:** 1) Gọi breakdown_by=payment_method.
- **Dữ liệu test:** invoice 500k = Cash 300k + Card 200k.
- **Kết quả mong đợi:** HTTP 200; Cash += 300k, Card += 200k; tổng các phương thức = tổng doanh thu (không đếm trùng invoice).
- **Coverage hiện tại:** MISSING

### TC-RPT-008 — Số visit theo chuyên khoa (happy path)
- **Function:** RPT-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Visit completed thuộc nhiều specialty.
- **Bước thực hiện:** 1) GET `/api/v1/reports/visits?group_by=specialty&from=...&to=...`.
- **Dữ liệu test:** Nội 5, Nhi 3, Da liễu 2.
- **Kết quả mong đợi:** HTTP 200; 3 nhóm số đúng; `total_visits = 10`.
- **Coverage hiện tại:** MISSING

### TC-RPT-009 — Số visit chỉ tính completed, loại cancelled/no_show (edge state machine)
- **Function:** RPT-004
- **Loại:** Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit ở nhiều trạng thái.
- **Bước thực hiện:** 1) Gọi visits by specialty.
- **Dữ liệu test:** 7 completed, 2 cancelled, 1 no_show, 1 in_progress.
- **Kết quả mong đợi:** HTTP 200; `total_visits = 7`; các trạng thái khác không gộp vào.
- **Coverage hiện tại:** MISSING

### TC-RPT-010 — Top N thuốc dùng nhiều (happy path)
- **Function:** RPT-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có dữ liệu dispense/bán thuốc.
- **Bước thực hiện:** 1) GET `/api/v1/reports/top-medicines?metric=quantity&limit=5`. 2) Lặp `metric=revenue`.
- **Dữ liệu test:** 8 thuốc với qty/revenue khác nhau.
- **Kết quả mong đợi:** HTTP 200; trả đúng 5 dòng, sắp xếp giảm dần theo metric; với `metric=revenue` thứ tự đổi đúng theo doanh thu.
- **Coverage hiện tại:** MISSING

### TC-RPT-011 — Top thuốc với limit không hợp lệ (negative)
- **Function:** RPT-005
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập Admin.
- **Bước thực hiện:** 1) Gọi `limit=0` rồi `limit=-3` rồi `limit=abc`.
- **Dữ liệu test:** limit biên/không hợp lệ.
- **Kết quả mong đợi:** HTTP 422 cho limit ≤ 0 và không phải số nguyên; thông báo validation rõ ràng.
- **Coverage hiện tại:** MISSING

### TC-RPT-012 — Thuốc ít dùng (happy path)
- **Function:** RPT-006
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có thuốc dùng nhiều và thuốc dùng ít trong range.
- **Bước thực hiện:** 1) GET `/api/v1/reports/least-used-medicines?limit=5`.
- **Dữ liệu test:** thuốc A qty 1, B qty 2, C qty 100.
- **Kết quả mong đợi:** HTTP 200; sắp xếp tăng dần theo qty; A và B đứng đầu; C không nằm trong top ít dùng.
- **Coverage hiện tại:** MISSING

### TC-RPT-013 — Thuốc chưa từng dùng (qty=0) trong kỳ (edge)
- **Function:** RPT-006
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có thuốc trong danh mục nhưng không phát sinh trong range.
- **Bước thực hiện:** 1) Gọi least-used trong range.
- **Dữ liệu test:** thuốc X qty=0 trong range.
- **Kết quả mong đợi:** HTTP 200; thuốc X xuất hiện với qty=0 (gợi ý ngừng nhập), không bị loại do thiếu giao dịch.
- **Coverage hiện tại:** MISSING

### TC-RPT-014 — Tồn kho theo giá vốn (happy path)
- **Function:** RPT-007
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có tồn kho nhiều thuốc với giá vốn (cost) khác nhau.
- **Bước thực hiện:** 1) GET `/api/v1/reports/inventory-value`.
- **Dữ liệu test:** A: 10 × 5.000; B: 20 × 3.000.
- **Kết quả mong đợi:** HTTP 200; `total_value = 110000` (50.000 + 60.000); mỗi dòng có `medicine_id, qty, unit_cost, line_value`.
- **Coverage hiện tại:** MISSING

### TC-RPT-015 — Tồn kho rỗng / qty âm chặn (edge)
- **Function:** RPT-007
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có thuốc tồn 0; không có thuốc tồn âm (bất biến kho).
- **Bước thực hiện:** 1) Gọi inventory-value.
- **Dữ liệu test:** thuốc tồn 0.
- **Kết quả mong đợi:** HTTP 200; thuốc tồn 0 → line_value 0; tổng không bao gồm giá trị âm; không có qty âm.
- **Coverage hiện tại:** MISSING

### TC-RPT-016 — Thuốc sắp hết hạn 30/60/90 ngày (happy path)
- **Function:** RPT-008
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập role `Pharmacist`; có lô thuốc với expiry khác nhau (mốc tham chiếu 2026-05-30).
- **Bước thực hiện:** 1) GET `/api/v1/reports/expiring-medicines?window=30`. 2) Lặp window=60, 90.
- **Dữ liệu test:** lô hết hạn sau 20 / 45 / 80 / 200 ngày.
- **Kết quả mong đợi:** HTTP 200; window=30 trả lô 20 ngày; window=60 trả 20+45; window=90 trả 20+45+80; lô 200 ngày không xuất hiện.
- **Coverage hiện tại:** MISSING

### TC-RPT-017 — Lô đã hết hạn (expiry < hôm nay) (edge)
- **Function:** RPT-008
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có lô đã quá hạn.
- **Bước thực hiện:** 1) Gọi expiring-medicines.
- **Dữ liệu test:** lô hết hạn từ 5 ngày trước.
- **Kết quả mong đợi:** HTTP 200; lô quá hạn được đánh dấu `expired=true` (hoặc days_left âm) và vẫn liệt kê để cảnh báo thu hồi.
- **Coverage hiện tại:** MISSING

### TC-RPT-018 — Quyền dược: Admin tài chính KHÔNG mặc nhiên có quyền này nếu thiếu permission kho (security)
- **Function:** RPT-008
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User có `report.financial` nhưng KHÔNG có quyền kho/dược.
- **Bước thực hiện:** 1) GET `/api/v1/reports/expiring-medicines`.
- **Dữ liệu test:** token thiếu quyền dược.
- **Kết quả mong đợi:** HTTP 403 (báo cáo này gắn quyền dược, không phải tài chính).
- **Coverage hiện tại:** MISSING

### TC-RPT-019 — No-show rate (happy path)
- **Function:** RPT-009
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lịch hẹn có cả đến khám và no_show trong range.
- **Bước thực hiện:** 1) GET `/api/v1/reports/no-show-rate?from=...&to=...`.
- **Dữ liệu test:** 20 hẹn, 4 no_show.
- **Kết quả mong đợi:** HTTP 200; `rate = 0.20` (20%); `total_appointments=20`, `no_show=4`.
- **Coverage hiện tại:** MISSING

### TC-RPT-020 — No-show rate khi không có lịch hẹn (edge chia 0)
- **Function:** RPT-009
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Range không có lịch hẹn.
- **Bước thực hiện:** 1) Gọi no-show-rate range rỗng.
- **Dữ liệu test:** 0 hẹn.
- **Kết quả mong đợi:** HTTP 200; `rate = 0` hoặc `null` (không lỗi chia 0); `total_appointments = 0`.
- **Coverage hiện tại:** MISSING

### TC-RPT-021 — Demographic BN theo tuổi/giới/tỉnh (happy path)
- **Function:** RPT-010
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Bệnh nhân đủ trường giới tính, ngày sinh, tỉnh.
- **Bước thực hiện:** 1) GET `/api/v1/reports/demographics?dimension=age`. 2) Lặp dimension=gender, province.
- **Dữ liệu test:** 100 BN nhiều nhóm tuổi/giới/tỉnh.
- **Kết quả mong đợi:** HTTP 200; mỗi dimension trả phân nhóm với count; tổng các nhóm = 100; nhóm tuổi theo bins chuẩn (0-17, 18-39, 40-59, 60+).
- **Coverage hiện tại:** MISSING

### TC-RPT-022 — Demographic với BN thiếu dữ liệu (null) (edge)
- **Function:** RPT-010
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có BN thiếu ngày sinh / tỉnh.
- **Bước thực hiện:** 1) Gọi demographics.
- **Dữ liệu test:** 5 BN thiếu DOB, 3 BN thiếu tỉnh.
- **Kết quả mong đợi:** HTTP 200; nhóm "Không xác định" gom các bản ghi null; tổng vẫn = tổng BN (không rớt).
- **Coverage hiện tại:** MISSING

### TC-RPT-023 — Visit duration trung bình (happy path)
- **Function:** RPT-011
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit completed có timestamp bắt đầu & kết thúc khám.
- **Bước thực hiện:** 1) GET `/api/v1/reports/visit-duration?from=...&to=...`.
- **Dữ liệu test:** 3 visit: 10, 20, 30 phút.
- **Kết quả mong đợi:** HTTP 200; `avg_minutes = 20`; có thể kèm median/percentile nếu spec yêu cầu.
- **Coverage hiện tại:** MISSING

### TC-RPT-024 — Visit duration loại visit chưa kết thúc (edge)
- **Function:** RPT-011
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có visit in_progress (chưa có thời điểm kết thúc).
- **Bước thực hiện:** 1) Gọi visit-duration.
- **Dữ liệu test:** 2 completed + 1 in_progress.
- **Kết quả mong đợi:** HTTP 200; chỉ tính 2 visit completed vào trung bình; in_progress bị loại; không tính khoảng âm/quá lớn.
- **Coverage hiện tại:** MISSING

### TC-RPT-025 — Wait time trung bình (happy path)
- **Function:** RPT-012
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit có timestamp check-in & bắt đầu khám.
- **Bước thực hiện:** 1) GET `/api/v1/reports/wait-time?from=...&to=...`.
- **Dữ liệu test:** chờ 5, 15, 25 phút.
- **Kết quả mong đợi:** HTTP 200; `avg_wait_minutes = 15`.
- **Coverage hiện tại:** MISSING

### TC-RPT-026 — Wait time bất thường (check-in sau khi bắt đầu khám) (edge)
- **Function:** RPT-012
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có bản ghi dữ liệu lệch (start < check-in).
- **Bước thực hiện:** 1) Gọi wait-time.
- **Dữ liệu test:** 1 bản ghi wait âm + 2 bản ghi hợp lệ.
- **Kết quả mong đợi:** HTTP 200; bản ghi wait âm bị loại hoặc clamp về 0 (không kéo trung bình âm); kết quả ổn định.
- **Coverage hiện tại:** MISSING

### TC-RPT-027 — Custom date range áp cho mọi report (happy path)
- **Function:** RPT-013
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Có dữ liệu trải nhiều ngày.
- **Bước thực hiện:** 1) Gọi revenue/visits/no-show với cùng `from`/`to` tùy chỉnh.
- **Dữ liệu test:** range 2026-05-01..2026-05-15.
- **Kết quả mong đợi:** HTTP 200; mọi report chỉ lấy dữ liệu trong [from, to] (bao gồm 2 đầu mút theo spec); không lẫn dữ liệu ngoài range.
- **Coverage hiện tại:** MISSING

### TC-RPT-028 — from > to (negative validation)
- **Function:** RPT-013
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập Admin.
- **Bước thực hiện:** 1) Gọi report với `from=2026-05-31&to=2026-05-01`.
- **Dữ liệu test:** from > to.
- **Kết quả mong đợi:** HTTP 422; message "from must be before to".
- **Coverage hiện tại:** MISSING

### TC-RPT-029 — Định dạng ngày sai (negative)
- **Function:** RPT-013
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập Admin.
- **Bước thực hiện:** 1) Gọi `from=31-05-2026` (sai ISO).
- **Dữ liệu test:** date sai format.
- **Kết quả mong đợi:** HTTP 422 lỗi parse date.
- **Coverage hiện tại:** MISSING

### TC-RPT-030 — Range rỗng / mặc định khi thiếu tham số (edge)
- **Function:** RPT-013
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập Admin.
- **Bước thực hiện:** 1) Gọi report không truyền from/to. 2) Gọi range tương lai không có dữ liệu.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 200; thiếu tham số → áp range mặc định theo spec (vd 30 ngày gần nhất); range không dữ liệu → trả tổng 0 / breakdown rỗng.
- **Coverage hiện tại:** MISSING

### TC-RPT-031 — Export CSV doanh thu (happy path)
- **Function:** RPT-014
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Có dữ liệu doanh thu; Admin có `report.financial`.
- **Bước thực hiện:** 1) GET `/api/v1/reports/revenue/export?format=csv&from=...&to=...`.
- **Dữ liệu test:** breakdown 3 ngày.
- **Kết quả mong đợi:** HTTP 200; `Content-Type: text/csv`; header `Content-Disposition: attachment; filename=*.csv`; body có dòng header + 3 dòng dữ liệu; số liệu khớp report JSON.
- **Coverage hiện tại:** MISSING

### TC-RPT-032 — Export CSV mã hóa UTF-8 BOM cho tiếng Việt (edge)
- **Function:** RPT-014
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Dữ liệu có ký tự tiếng Việt (tên bác sĩ/thuốc có dấu).
- **Bước thực hiện:** 1) Export CSV, mở bằng Excel.
- **Dữ liệu test:** "Nguyễn Thị Hồng", "Paracetamol 500mg".
- **Kết quả mong đợi:** File có BOM UTF-8; Excel hiển thị tiếng Việt không lỗi font; dấu phẩy trong tên được escape/quote đúng.
- **Coverage hiện tại:** MISSING

### TC-RPT-033 — Export CSV dữ liệu rỗng (edge)
- **Function:** RPT-014
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Range không có dữ liệu.
- **Bước thực hiện:** 1) Export CSV range rỗng.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 200; CSV chỉ có dòng header (không lỗi); không 500.
- **Coverage hiện tại:** MISSING

### TC-RPT-034 — Export CSV báo cáo tài chính thiếu quyền (security 403)
- **Function:** RPT-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User có `report.view` nhưng KHÔNG có `report.financial`.
- **Bước thực hiện:** 1) GET export CSV của revenue.
- **Dữ liệu test:** token thiếu quyền tài chính.
- **Kết quả mong đợi:** HTTP 403; không tải được dữ liệu tài chính (kiểm soát quyền cả ở endpoint export, không chỉ ở view).
- **Coverage hiện tại:** MISSING

### TC-RPT-035 — Export PDF có letterhead (happy path)
- **Function:** RPT-015
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A đã cấu hình logo/tên/địa chỉ (letterhead).
- **Bước thực hiện:** 1) GET `/api/v1/reports/revenue/export?format=pdf`.
- **Dữ liệu test:** breakdown nhiều dòng.
- **Kết quả mong đợi:** HTTP 200; `Content-Type: application/pdf`; PDF mở được, có header logo + tên clinic + khoảng thời gian + bảng dữ liệu; số liệu khớp report.
- **Coverage hiện tại:** MISSING

### TC-RPT-036 — Export PDF dùng đúng letterhead của clinic hiện tại (security/RLS)
- **Function:** RPT-015
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B đều có letterhead khác nhau.
- **Bước thực hiện:** 1) Admin clinic A export PDF.
- **Dữ liệu test:** logo/tên A vs B.
- **Kết quả mong đợi:** PDF dùng letterhead của A; tuyệt đối không dùng/lộ branding hoặc dữ liệu của B.
- **Coverage hiện tại:** MISSING

### TC-RPT-037 — Export PDF báo cáo lớn (edge hiệu năng)
- **Function:** RPT-015
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Báo cáo có hàng nghìn dòng.
- **Bước thực hiện:** 1) Export PDF range 1 năm.
- **Dữ liệu test:** ~5000 dòng.
- **Kết quả mong đợi:** HTTP 200; PDF phân trang đúng; phản hồi trong ngưỡng timeout (hoặc xử lý async/job nếu vượt ngưỡng); không OOM.
- **Coverage hiện tại:** MISSING

### TC-RPT-038 — Tạo lịch gửi email báo cáo tuần (happy path)
- **Function:** RPT-016
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Admin; SMTP cấu hình; phase v2.
- **Bước thực hiện:** 1) POST `/api/v1/reports/schedules` `{report_type:"revenue", frequency:"weekly", recipients:[...], day_of_week:1}`.
- **Dữ liệu test:** email hợp lệ.
- **Kết quả mong đợi:** HTTP 201; lịch được tạo với `next_run_at` đúng; trả về schedule_id.
- **Coverage hiện tại:** MISSING

### TC-RPT-039 — Job chạy đúng lịch và gửi email (integration)
- **Function:** RPT-016
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có schedule đến hạn; mock SMTP.
- **Bước thực hiện:** 1) Trigger scheduler job. 2) Kiểm tra email gửi.
- **Dữ liệu test:** schedule weekly đến hạn.
- **Kết quả mong đợi:** Email gửi tới đúng recipients, đính kèm báo cáo (PDF/CSV); `last_run_at` cập nhật; `next_run_at` dời sang kỳ tiếp.
- **Coverage hiện tại:** MISSING

### TC-RPT-040 — Email không hợp lệ khi tạo lịch (negative)
- **Function:** RPT-016
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Admin.
- **Bước thực hiện:** 1) POST schedule với `recipients:["not-an-email"]`.
- **Dữ liệu test:** email sai định dạng.
- **Kết quả mong đợi:** HTTP 422; lỗi validation email.
- **Coverage hiện tại:** MISSING

### TC-RPT-041 — Idempotency: job lỗi giữa chừng không gửi trùng (edge)
- **Function:** RPT-016
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** SMTP fail lần 1 rồi thành công lần 2.
- **Bước thực hiện:** 1) Job retry sau lỗi SMTP.
- **Dữ liệu test:** SMTP transient error.
- **Kết quả mong đợi:** Email chỉ gửi đúng 1 lần cho 1 kỳ (không double-send); retry an toàn; log audit lần gửi.
- **Coverage hiện tại:** MISSING

### TC-RPT-042 — Lịch chỉ áp trong clinic của người tạo (security/RLS)
- **Function:** RPT-016
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin A tạo schedule; Admin B liệt kê schedules.
- **Bước thực hiện:** 1) GET `/api/v1/reports/schedules` bởi Admin B.
- **Dữ liệu test:** schedule của clinic A.
- **Kết quả mong đợi:** Admin B không thấy schedule của A; báo cáo gửi chứa dữ liệu của đúng clinic sở hữu schedule.
- **Coverage hiện tại:** MISSING

### TC-RPT-043 — Patient retention rate (happy path)
- **Function:** RPT-017
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có BN khám nhiều lần và BN khám 1 lần (phase v2/backlog).
- **Bước thực hiện:** 1) GET `/api/v1/reports/patient-retention?from=...&to=...`.
- **Dữ liệu test:** 10 BN, 4 BN quay lại trong kỳ.
- **Kết quả mong đợi:** HTTP 200; `retention_rate = 0.40`; định nghĩa "quay lại" theo spec (≥2 visit trong cửa sổ thời gian).
- **Coverage hiện tại:** MISSING

### TC-RPT-044 — Retention khi BN mới hoàn toàn (edge)
- **Function:** RPT-017
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tất cả BN đều khám lần đầu trong kỳ.
- **Bước thực hiện:** 1) Gọi retention.
- **Dữ liệu test:** 10 BN mới, 0 quay lại.
- **Kết quả mong đợi:** HTTP 200; `retention_rate = 0`; không lỗi chia 0.
- **Coverage hiện tại:** MISSING

### TC-RPT-045 — Retention cô lập clinic (security/RLS)
- **Function:** RPT-017
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN cùng SĐT khám ở cả clinic A và B (đa tenant).
- **Bước thực hiện:** 1) Admin A gọi retention.
- **Dữ liệu test:** BN P khám 1 lần ở A, 1 lần ở B.
- **Kết quả mong đợi:** Retention của A chỉ tính visit tại A → P là BN một-lần với A (không gộp visit của B vào).
- **Coverage hiện tại:** MISSING

### TC-RPT-046 — Clinical KPI / outcome lâm sàng (happy path)
- **Function:** RPT-018
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có dữ liệu chẩn đoán/kết quả điều trị (phase v3/backlog).
- **Bước thực hiện:** 1) GET `/api/v1/reports/clinical-kpis?from=...&to=...`.
- **Dữ liệu test:** tập visit có outcome.
- **Kết quả mong đợi:** HTTP 200; trả các KPI lâm sàng theo spec (vd top chẩn đoán, tỷ lệ tái khám theo bệnh); shape ổn định.
- **Coverage hiện tại:** MISSING

### TC-RPT-047 — Clinical KPI khi thiếu dữ liệu outcome (edge)
- **Function:** RPT-018
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit chưa ghi outcome/chẩn đoán.
- **Bước thực hiện:** 1) Gọi clinical-kpis.
- **Dữ liệu test:** visit thiếu diagnosis.
- **Kết quả mong đợi:** HTTP 200; KPI bỏ qua bản ghi thiếu hoặc gom "Không xác định"; không 500; có chú thích độ phủ dữ liệu nếu spec yêu cầu.
- **Coverage hiện tại:** MISSING

### TC-RPT-048 — Clinical KPI bảo mật dữ liệu lâm sàng nhạy cảm (security)
- **Function:** RPT-018
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User chỉ có `report.view` (không quyền lâm sàng); và RLS clinic.
- **Bước thực hiện:** 1) Gọi clinical-kpis bằng user không đủ quyền; 2) Admin A thử lấy KPI clinic B.
- **Dữ liệu test:** token thiếu quyền; ép clinic_id=B.
- **Kết quả mong đợi:** Thiếu quyền → 403; ép clinic khác → 403/tự lọc về clinic của mình; KPI là dữ liệu tổng hợp, không lộ PII bệnh nhân cá nhân ngoài clinic.
- **Coverage hiện tại:** MISSING

---

### TC-RPT-049 — Truy cập mọi endpoint report khi chưa đăng nhập (security 401 — xuyên suốt)
- **Function:** RPT-001..RPT-018 (chung)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi header Authorization.
- **Bước thực hiện:** 1) Lặp GET tất cả endpoint `/api/v1/reports/*` không token.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Mọi endpoint trả HTTP 401 Unauthorized; không endpoint nào rò rỉ dữ liệu.
- **Coverage hiện tại:** MISSING

### TC-RPT-050 — Thiếu permission report.view (security 403 — xuyên suốt)
- **Function:** RPT-001..RPT-018 (chung)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập role không có `report.view` (vd receptionist/nurse).
- **Bước thực hiện:** 1) GET các report vận hành.
- **Dữ liệu test:** token thiếu report.view.
- **Kết quả mong đợi:** HTTP 403 trên mọi report yêu cầu report.view.
- **Coverage hiện tại:** MISSING

### TC-RPT-051 — Thiếu permission report.financial cho báo cáo tài chính (security 403 — xuyên suốt)
- **Function:** RPT-001, RPT-002, RPT-003, RPT-007 (tài chính)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User có `report.view` nhưng KHÔNG có `report.financial`.
- **Bước thực hiện:** 1) GET revenue / revenue-by-doctor / revenue-by-method / inventory-value.
- **Dữ liệu test:** token thiếu report.financial.
- **Kết quả mong đợi:** HTTP 403; các báo cáo tài chính bị chặn dù có report.view.
- **Coverage hiện tại:** MISSING

### TC-RPT-052 — Cô lập clinic (RLS) cho mọi report dữ liệu domain (security — xuyên suốt)
- **Function:** RPT-001..RPT-013, RPT-017, RPT-018 (chung)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin clinic A; clinic B có dữ liệu doanh thu/visit/kho/BN.
- **Bước thực hiện:** 1) Admin A gọi từng report. 2) Thử ép `clinic_id=B` (query param/body).
- **Dữ liệu test:** A: dữ liệu nhỏ; B: dữ liệu lớn dễ phân biệt.
- **Kết quả mong đợi:** Chỉ trả dữ liệu clinic A; ép clinic_id=B → HTTP 403 hoặc RLS tự lọc về A; không bao giờ trả số liệu/PII của B.
- **Coverage hiện tại:** MISSING

### TC-RPT-053 — Người dùng đa clinic chỉ xem báo cáo clinic đang active (security)
- **Function:** RPT-001..RPT-018 (chung)
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User thuộc cả clinic A và C; phiên đang active tại A.
- **Bước thực hiện:** 1) Gọi report (theo clinic active A). 2) Chuyển context sang C rồi gọi lại.
- **Dữ liệu test:** dữ liệu A và C khác nhau.
- **Kết quả mong đợi:** Báo cáo phản ánh đúng clinic active hiện tại; chuyển context → dữ liệu đổi tương ứng; không trộn lẫn A và C.
- **Coverage hiện tại:** MISSING

### TC-RPT-054 — Cache Redis không rò rỉ dữ liệu giữa các clinic (security/edge)
- **Function:** RPT-001..RPT-013 (báo cáo có thể cache)
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Bật cache; clinic A và B cùng tham số report.
- **Bước thực hiện:** 1) Admin A gọi report (ghi cache). 2) Admin B gọi report cùng params.
- **Dữ liệu test:** cùng from/to/group_by; dữ liệu A ≠ B.
- **Kết quả mong đợi:** Cache key có chứa `clinic_id`; Admin B nhận dữ liệu của B (không nhận cached của A); invalidation đúng khi dữ liệu thay đổi.
- **Coverage hiện tại:** MISSING

---

## 3. Khuyến nghị triển khai test (khi code RPT sẵn sàng)
- **P0 trước:** happy path mỗi report tài chính/visit (001, 004, 006, 008, 010, 016/inventory, 019, 027, 031); nghiệp vụ tính toán (003 paid-only, 009 completed-only, 016 cửa sổ hết hạn, 020 chia-0, 026 wait âm); và toàn bộ security/RLS chung (049–054).
- **Layer ưu tiên:** Integration (real DB) cho logic aggregation, state machine và RLS/cache; E2E (httpx) cho auth/validation/export headers; vitest cho render biểu đồ + bảng (RPT-001 KPI/line chart).
- **Dữ liệu seed:** fixture đa clinic (A, B, C); invoice ở nhiều trạng thái (paid/draft/void/refund) và split payment; visit nhiều trạng thái (completed/cancelled/no_show/in_progress) có timestamp check-in/start/end; lô thuốc nhiều mốc hết hạn; BN thiếu DOB/tỉnh để test nhánh null.
- **Quyền:** kiểm tra cả 2 lớp (view + financial) và phân biệt quyền dược cho RPT-008; mọi endpoint export phải tái kiểm tra quyền (không chỉ endpoint view).
