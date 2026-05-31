# Kịch bản vận hành — Biến thể nghiệp vụ

**Mục đích:** test E2E theo luồng vận hành thực tế của phòng khám, mỗi bước do ĐÚNG vai trò/tài khoản demo thực hiện đúng nhiệm vụ, bàn giao trạng thái hợp lệ giữa các vai trò theo state machine Visit.
**Số kịch bản:** 7.  **Ngày:** 2026-05-31.

> **Ngữ cảnh chung:** Clinic CMS (FastAPI + PostgreSQL RLS + Redis; FE Tauri/React). Mọi request `/api/v1/*` cần JWT (thiếu token → 401 trước routing). Clinic demo: `DEMO`. RLS giới hạn mọi thao tác trong clinic của tài khoản đăng nhập.
>
> **State machine Visit thực tế** (theo `visit-test-catalog.md` §nền tảng / `state_machine.py`, enum `VisitStatus`):
> `WAITING_VITAL → {VITAL_DONE, NO_SHOW, CANCELLED}`; `VITAL_DONE → {IN_CONSULTATION, CANCELLED}`; `IN_CONSULTATION → {PAUSED, WAITING_PHARMACY, WAITING_PAYMENT, COMPLETED}`; `PAUSED → {IN_CONSULTATION, CANCELLED}`; `WAITING_PHARMACY → {WAITING_PAYMENT, COMPLETED}`; `WAITING_PAYMENT → {COMPLETED}`; `COMPLETED / NO_SHOW / CANCELLED` = terminal.
> (Lưu ý: tên trạng thái BA dùng WAITING/IN_PROGRESS/AWAITING_PAYMENT ≈ WAITING_VITAL/IN_CONSULTATION/WAITING_PAYMENT trong code.)
>
> **Endpoint Visit đã ship** (`app/modules/visits/router.py`, base `/api/v1`): `POST /visits` (visit.create), `GET /visits`, `GET /visits/{id}`, `POST /visits/call-next` (visit.consult — gọi BN tiếp theo), `PATCH /visits/{id}/status` (visit.update — chuyển trạng thái), `POST /visits/{id}/reassign`, `GET /visits/{id}/events`, `PATCH /visits/{id}`.
> **Endpoint Pharmacy đã ship** (TASK-012): `GET /pharmacy/queue`, `GET /pharmacy/dispense/{rx_id}` (chi tiết + gợi ý lô FEFO), `POST /pharmacy/dispense/{rx_id}` (xác nhận cấp), `POST /pharmacy/dispense/{rx_id}/reverse`, `GET /pharmacy/dispense/{rx_id}/history`. Permission `pharmacy.dispense`; có rule chống tự cấp đơn do chính mình kê.
>
> **Tài khoản demo** (seed_demo_data.py): `admin/Demo@1234`; bác sĩ `dr_nguyen,dr_le,dr_tran,dr_pham,dr_hoang/Doctor@1234`; y tá `nurse_lan,nurse_huong,nurse_linh/Nurse@1234`; lễ tân `recept_anh,recept_binh/Recept@1234`; dược sĩ `pharm_cuong,pharm_dung/Pharm@1234`; thu ngân `cashier_em/Cashier@1234`.
>
> **Queue rule (BA §4.6):** 1 queue/clinic, sort `priority DESC, is_returning_patient DESC, created_at ASC`.

## Danh sách kịch bản
| Mã | Tên kịch bản | Vai trò tham gia | Ưu tiên |
|---|---|---|---|
| SC-VAR-01 | Tái khám — BN có hồ sơ, lễ tân tìm theo SĐT, bác sĩ xem lịch sử khám/đơn cũ | Lễ tân → Y tá → Bác sĩ → Thu ngân → Dược sĩ | P0 |
| SC-VAR-02 | Chỉ mua thuốc (không khám) — bán thuốc lẻ (manual invoice) | Dược sĩ → Thu ngân | P0 |
| SC-VAR-03 | Cấp cứu — priority cao vọt lên đầu hàng đợi, bác sĩ gọi ngay | Lễ tân → Bác sĩ → Y tá → Thu ngân → Dược sĩ | P0 |
| SC-VAR-04 | Khám nhiều chuyên khoa trong 1 lần đến (reassign giữa 2 bác sĩ) | Lễ tân → Y tá → Bác sĩ A → Bác sĩ B → Thu ngân → Dược sĩ | P1 |
| SC-VAR-05 | Walk-in vs có lịch hẹn — appointment check-in → visit | Lễ tân → Y tá → Bác sĩ → Thu ngân | P1 |
| SC-VAR-06 | Đơn thuốc kê ngoại viện (is_internal=false) — BN tự mua ngoài, không trừ tồn | Lễ tân → Y tá → Bác sĩ → Thu ngân | P1 |
| SC-VAR-07 | Phân quyền chéo trên các biến thể (403/RLS/401) | Dược sĩ, Y tá, Lễ tân, Admin, cross-tenant | P0 |

---

## Chi tiết

### SC-VAR-01 — Tái khám (BN đã có hồ sơ, lễ tân tìm theo SĐT, bác sĩ xem lịch sử)
- **Mục tiêu:** Xác nhận luồng tái khám: lễ tân KHÔNG tạo BN mới mà tìm hồ sơ cũ qua SĐT → tạo visit mới; bác sĩ truy cập được lịch sử khám và đơn thuốc lần trước trước khi kê đơn mới. **Khác biệt so với luồng chuẩn:** bước 1 là tra cứu + tái dùng hồ sơ (không tạo BN), thêm bước bác sĩ xem tiền sử (VIS-008).
- **Vai trò & tài khoản:**
  - Lễ tân: `recept_anh / Recept@1234`
  - Y tá: `nurse_lan / Nurse@1234`
  - Bác sĩ: `dr_nguyen / Doctor@1234`
  - Thu ngân: `cashier_em / Cashier@1234`
  - Dược sĩ: `pharm_cuong / Pharm@1234`
- **Tiền điều kiện:**
  - Tồn tại 1 BN cũ (vd `patient_code` có sẵn, có SĐT) với ÍT NHẤT 1 visit lịch sử `COMPLETED` kèm 1 đơn thuốc cũ (đã dispense).
  - Tồn kho thuốc nội viện dương cho thuốc sẽ kê lại.
  - Bác sĩ `dr_nguyen` đang trong ca trực.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Tra cứu BN theo SĐT | GET /api/v1/patients?search=<sđt> | 200, trả đúng BN cũ (1 kết quả), KHÔNG tạo trùng | Đã xác định BN tái khám |
| 2 | Lễ tân (recept_anh) | Tạo visit mới cho BN cũ, pre-assign dr_nguyen | POST /api/v1/visits {patient_id, doctor_id, type:"WALK_IN"} | 201, status=WAITING_VITAL, doctor_id=dr_nguyen, có visit_number | Visit chờ đo sinh hiệu |
| 3 | Y tá (nurse_lan) | Gọi BN, nhập sinh hiệu; chuyển trạng thái | POST /api/v1/visits/{id}/vitals; PATCH /api/v1/visits/{id}/status {status:VITAL_DONE} | 201 vitals lưu; status=VITAL_DONE; is_returning_patient=true | BN quay lại ghế chờ khám |
| 4 | Bác sĩ (dr_nguyen) | Xem lịch sử khám của BN | GET /api/v1/patients/{id}/visits?status=COMPLETED (hoặc /visits?patient_id=) | 200, thấy visit cũ + chẩn đoán | Có ngữ cảnh tiền sử |
| 5 | Bác sĩ (dr_nguyen) | Xem đơn thuốc lần trước | GET /api/v1/prescriptions?patient_id=… | 200, thấy đơn cũ + thuốc | Tham chiếu kê đơn mới |
| 6 | Bác sĩ (dr_nguyen) | Gọi BN tiếp theo (ưu tiên visit assigned cho mình) | POST /api/v1/visits/call-next | status=IN_CONSULTATION, doctor_id=dr_nguyen | Đang khám |
| 7 | Bác sĩ (dr_nguyen) | Chọn service + kê đơn nội viện (is_internal=true, reserve tồn) | POST /api/v1/visits/{id}/services; POST /api/v1/prescriptions | 201, đơn items reserve tồn | Đơn sẵn cho dược |
| 8 | Bác sĩ (dr_nguyen) | Hoàn tất khám → chờ dược | PATCH /api/v1/visits/{id}/status {status:WAITING_PHARMACY} | status=WAITING_PHARMACY | Bàn giao dược/thu ngân |
| 9 | Thu ngân (cashier_em) | Lập invoice (auto pull service + đơn nội viện) | POST /api/v1/invoices {visit_id} | 201, invoice gồm service + thuốc | Chờ thanh toán |
| 10 | Thu ngân (cashier_em) | Thu tiền | POST /api/v1/invoices/{id}/payments | 200, invoice PAID | Cho phép dispense |
| 11 | Dược sĩ (pharm_cuong) | Xem hàng đợi → cấp phát theo FEFO | GET /api/v1/pharmacy/queue; POST /api/v1/pharmacy/dispense/{rx_id} | StockMovement OUT trừ tồn theo lô sớm hết hạn | status→WAITING_PAYMENT/COMPLETED |
| 12 | Thu ngân (cashier_em) | Đóng visit | PATCH /api/v1/visits/{id}/status {status:COMPLETED} | status=COMPLETED | BN ra về |

- **Kết quả cuối:** Visit mới = `COMPLETED`; Invoice = `PAID`; sinh StockMovement (OUT) cho thuốc nội viện; KHÔNG phát sinh BN trùng; audit log đủ các bước.
- **Điểm kiểm chứng (assertions):**
  - Số bản ghi `patient` không tăng (tái dùng hồ sơ cũ — PAT-search).
  - Bác sĩ truy cập được ≥1 visit cũ `COMPLETED` (VIS-008) và đơn cũ của ĐÚNG BN.
  - `is_returning_patient=true` sau khi đo sinh hiệu; visit xếp trước visit thường cùng priority trong queue.
  - Tồn kho sau dispense = tồn trước − SL cấp; lô chọn là lô hạn dùng sớm nhất (FEFO — PHRM-003).
  - RLS: tài khoản clinic khác query lịch sử/visit của BN này → 404/empty (TC-VIS-RLS-01).
- **Liên kết function:** PAT-001/003, VIS-001/008/009, VITAL (VTL), RX-001/003, VIS-003 (state), PHRM-001/003/006, BILL-001/003 → catalog `functional/patient-`, `visit-`, `vital-`, `rx-`, `phrm-`, `bill-test-catalog.md`.

---

### SC-VAR-02 — Chỉ mua thuốc (không khám) — bán thuốc lẻ
- **Mục tiêu:** Khách mua thuốc lẻ KHÔNG qua bác sĩ, KHÔNG có visit khám/chẩn đoán; dược sĩ + thu ngân lập hóa đơn thủ công (manual invoice — BILL-003 "tạo HĐ ngoài visit / bán lẻ") và trừ tồn theo FEFO. **Khác biệt so với luồng chuẩn:** BỎ HOÀN TOÀN bước lễ tân tạo visit + y tá + bác sĩ + kê đơn theo chẩn đoán; không có VisitService.
- **Vai trò & tài khoản:**
  - Dược sĩ: `pharm_cuong / Pharm@1234`
  - Thu ngân: `cashier_em / Cashier@1234`
  - (tùy chọn) Lễ tân `recept_anh / Recept@1234` chỉ để tạo nhanh hồ sơ khách vãng lai nếu cần xuất hóa đơn ghi tên KH.
- **Tiền điều kiện:** Thuốc bán lẻ có tồn kho dương ≥ số lượng bán, có ≥2 lô khác hạn dùng để kiểm chứng FEFO.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Thu ngân (cashier_em) | Lập hóa đơn bán lẻ thủ công (manual invoice, không visit) | POST /api/v1/invoices {items:[{medicine_id, qty}]} (BILL-003) | 201, invoice DRAFT/ISSUED, visit_id=null | Chờ thu tiền |
| 2 | Thu ngân (cashier_em) | Thu tiền | POST /api/v1/invoices/{id}/payments | 200, invoice PAID, tổng = đơn giá × SL | Đã thanh toán |
| 3 | Dược sĩ (pharm_cuong) | Giao thuốc, trừ tồn theo FEFO | POST /api/v1/pharmacy/dispense/{rx_id} hoặc xuất kho theo invoice | StockMovement OUT, lô sớm hết hạn trước | Hoàn tất bán lẻ |

- **Kết quả cuối:** Không có Visit khám nào được tạo; Invoice = `PAID` (visit_id=null); tồn kho giảm đúng SL; StockMovement OUT.
- **Điểm kiểm chứng (assertions):**
  - KHÔNG tồn tại bản ghi Visit cho giao dịch này (invoice.visit_id=null — BILL-003 manual).
  - Tồn kho giảm đúng số bán; lô trừ trước = hạn dùng sớm nhất (FEFO).
  - Tổng invoice = Σ(đơn giá × SL); thuế/giảm giá (nếu cấu hình) áp đúng.
  - Quyền: pharmacist có `pharmacy.dispense`; thu ngân có `invoice.create`. Dược sĩ KHÔNG tự tạo invoice nếu thiếu `invoice.create` → 403 (xem SC-VAR-07).
  - RLS: invoice + phiếu xuất chỉ thấy trong clinic DEMO.
- **Liên kết function:** BILL-003 (manual/bán lẻ), BILL-payment, PHRM-006 (auto-decrement), PHRM-003 (FEFO), RBAC (pharmacy/invoice perms) → `bill-`, `phrm-`, `rbac-test-catalog.md`.
- **Lưu ý dò endpoint:** xác nhận lại trong system design + `app/` cơ chế "bán lẻ thuốc": có thể là manual invoice (BILL-003) kèm xuất kho, hoặc luồng OTC riêng — đề BA gọi là OTC nhưng catalog hiện chỉ thấy BILL-003 manual invoice.

---

### SC-VAR-03 — Cấp cứu (priority cao vọt lên đầu hàng đợi)
- **Mục tiêu:** Lễ tân tạo visit cấp cứu priority cao (vd 10); visit này phải đứng ĐẦU queue bất chấp các visit thường/ưu tiên tạo trước; bác sĩ "gọi BN tiếp theo" (call-next) lấy ngay ca cấp cứu. **Khác biệt so với luồng chuẩn:** thứ tự queue ưu tiên cao + đo sinh hiệu SAU khi bác sĩ tiếp nhận (đảo bước đo vitals).
- **Vai trò & tài khoản:**
  - Lễ tân: `recept_anh / Recept@1234`
  - Bác sĩ: `dr_nguyen / Doctor@1234`
  - Y tá: `nurse_lan / Nurse@1234`
  - Thu ngân: `cashier_em / Cashier@1234`
  - Dược sĩ: `pharm_cuong / Pharm@1234`
- **Tiền điều kiện:** Trong queue đã có ≥2 visit thường (priority=0) và ≥1 visit ưu tiên (priority=5) đang WAITING_VITAL.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Tạo visit cấp cứu priority cao | POST /api/v1/visits {patient_id, priority:10} | 201, status=WAITING_VITAL, priority=10 | Vào queue ở đầu |
| 2 | Lễ tân (recept_anh) | Xem queue xác nhận thứ tự | GET /api/v1/visits?status=WAITING_VITAL (hoặc /queue) | Visit cấp cứu đứng #1 (priority DESC) | Sẵn cho bác sĩ |
| 3 | Bác sĩ (dr_nguyen) | Gọi BN tiếp theo | POST /api/v1/visits/call-next | Trả đúng visit cấp cứu; status=IN_CONSULTATION | Đang xử trí cấp cứu |
| 4 | Y tá (nurse_lan) | Đo sinh hiệu tại chỗ (sau tiếp nhận) | POST /api/v1/visits/{id}/vitals | 201, vitals lưu | Hỗ trợ bác sĩ |
| 5 | Bác sĩ (dr_nguyen) | Service + kê đơn + hoàn tất | POST services; POST /prescriptions; PATCH /status {WAITING_PHARMACY hoặc WAITING_PAYMENT} | chuyển trạng thái hợp lệ | Bàn giao dược/thu ngân |
| 6 | Thu ngân (cashier_em) | Invoice + thu tiền | POST /api/v1/invoices; POST payments | invoice PAID | Cho dispense |
| 7 | Dược sĩ (pharm_cuong) | Cấp phát FEFO | POST /api/v1/pharmacy/dispense/{rx_id} | trừ tồn | status→COMPLETED |

- **Kết quả cuối:** Visit cấp cứu `COMPLETED` trước các visit tạo trước nó; queue trả đúng thứ tự ưu tiên.
- **Điểm kiểm chứng (assertions):**
  - Queue trả visit priority=10 ở vị trí #1 dù created_at muộn nhất.
  - `POST /visits/call-next` trả ĐÚNG visit cấp cứu (priority DESC > is_returning_patient DESC > created_at ASC).
  - State chuyển hợp lệ WAITING_VITAL→IN_CONSULTATION (VIS-003); call-next an toàn khi đồng thời (VIS-012).
  - RLS: visit cấp cứu không xuất hiện trong queue của clinic khác.
- **Liên kết function:** VIS-001 (priority), VIS-012 (call-next concurrent), VIS-003 (state), VITAL, RX, PHRM-001/003/006, BILL-001 → `visit-`, `vital-`, `rx-`, `phrm-`, `bill-test-catalog.md`.

---

### SC-VAR-04 — Khám nhiều chuyên khoa trong 1 lần đến (reassign giữa 2 bác sĩ)
- **Mục tiêu:** Trong 1 visit, BN được 2 bác sĩ khác chuyên khoa cùng tham gia; sau khi bác sĩ A khám xong, dùng reassign (VIS-010) chuyển bác sĩ B tiếp tục cùng visit; mỗi bác sĩ thêm service/đơn của mình; 1 invoice gộp toàn bộ. **Khác biệt so với luồng chuẩn:** nhiều VisitService/đơn từ nhiều doctor trên CÙNG 1 visit + dùng `POST /visits/{id}/reassign`.
- **Vai trò & tài khoản:**
  - Lễ tân: `recept_anh / Recept@1234`
  - Y tá: `nurse_lan / Nurse@1234`
  - Bác sĩ A (chuyên khoa 1): `dr_nguyen / Doctor@1234`
  - Bác sĩ B (chuyên khoa 2): `dr_le / Doctor@1234`
  - Thu ngân: `cashier_em / Cashier@1234`
  - Dược sĩ: `pharm_cuong / Pharm@1234`
- **Tiền điều kiện:** Hai bác sĩ khác chuyên khoa đều có ca trực; có service thuộc 2 chuyên khoa khác nhau trong catalog.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Tạo visit (assign A hoặc để trống) | POST /api/v1/visits {patient_id} | 201, WAITING_VITAL | Chờ sinh hiệu |
| 2 | Y tá (nurse_lan) | Đo sinh hiệu, chuyển VITAL_DONE | POST /vitals; PATCH /status {VITAL_DONE} | 201; VITAL_DONE | is_returning_patient=true |
| 3 | Bác sĩ A (dr_nguyen) | Gọi BN, khám CK1, thêm service + đơn CK1 | POST /visits/call-next; POST /services; POST /prescriptions | IN_CONSULTATION, VisitService(doctor=A) | Chuyển tiếp B |
| 4 | Bác sĩ A (dr_nguyen) | Reassign bác sĩ B (chuyển chuyên khoa) | POST /api/v1/visits/{id}/reassign {doctor_id:dr_le} | visit vẫn IN_CONSULTATION, doctor_id=dr_le; sự kiện reassign | Bàn giao B |
| 5 | Bác sĩ B (dr_le) | Tiếp tục cùng visit, thêm service + đơn CK2 | POST /api/v1/visits/{id}/services; POST /prescriptions | VisitService(doctor=B) gắn cùng visit | Tổng hợp dịch vụ |
| 6 | Bác sĩ B (dr_le) | Hoàn tất khám | PATCH /api/v1/visits/{id}/status {WAITING_PHARMACY/WAITING_PAYMENT} | chuyển trạng thái | Thu ngân |
| 7 | Thu ngân (cashier_em) | 1 invoice gộp service A+B + đơn nội viện | POST /api/v1/invoices {visit_id} | 201, gồm cả 2 chuyên khoa | PAID sau payment |
| 8 | Thu ngân (cashier_em) | Thu tiền | POST payments | PAID | Cho dispense |
| 9 | Dược sĩ (pharm_cuong) | Cấp phát toàn bộ đơn nội viện | POST /api/v1/pharmacy/dispense/{rx_id} | trừ tồn | status→COMPLETED |

- **Kết quả cuối:** 1 Visit `COMPLETED` chứa VisitService/đơn của ≥2 bác sĩ; 1 Invoice gộp `PAID`; có sự kiện reassign trong `GET /visits/{id}/events`.
- **Điểm kiểm chứng (assertions):**
  - Cùng 1 visit_id có VisitService với doctor_id khác nhau (A và B).
  - Reassign (VIS-010) ghi nhận lịch sử chuyển bác sĩ; doctor_id hiện tại = dr_le sau bước 4.
  - Invoice tổng = Σ tất cả service + thuốc nội viện của cả hai bác sĩ (KHÔNG tạo 2 invoice).
  - State machine không chuyển sang WAITING_PAYMENT cho tới khi bác sĩ cuối hoàn tất (VIS-003).
  - RLS: cả A và B cùng clinic DEMO; bác sĩ clinic khác → 403/404 khi truy cập visit.
- **Liên kết function:** VIS-001/009/010 (assignment, reassign), VIS-003 (state), VIS-013 (completion), RX, BILL-001 (auto-invoice gộp), PHRM → `visit-`, `rx-`, `bill-`, `phrm-test-catalog.md`.

---

### SC-VAR-05 — Walk-in vs có lịch hẹn (appointment check-in → visit)
- **Mục tiêu:** So sánh 2 đường vào visit: (A) BN có lịch hẹn → lễ tân check-in appointment để sinh visit (VIS-001 "tạo visit từ appointment"); (B) BN walk-in → lễ tân tạo visit trực tiếp. Cả hai cùng vào 1 queue. **Khác biệt so với luồng chuẩn:** nguồn tạo visit (appointment vs trực tiếp) + liên kết appointment_id + đồng bộ trạng thái appointment.
- **Vai trò & tài khoản:**
  - Lễ tân: `recept_anh / Recept@1234`
  - Y tá: `nurse_lan / Nurse@1234`
  - Bác sĩ: `dr_nguyen / Doctor@1234`
  - Thu ngân: `cashier_em / Cashier@1234`
- **Tiền điều kiện:** Tồn tại 1 appointment trạng thái booked/confirmed cho hôm nay (BN-có-hẹn, bác sĩ dr_nguyen); 1 BN khác để walk-in.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Check-in lịch hẹn → sinh visit | POST /api/v1/appointments/{id}/check-in (hoặc POST /visits {appointment_id}) | 201, visit WAITING_VITAL gắn appointment_id; appointment→checked_in | Visit-A vào queue |
| 2 | Lễ tân (recept_anh) | Tạo visit walk-in cho BN khác | POST /api/v1/visits {patient_id, type:"WALK_IN"} | 201, WAITING_VITAL, appointment_id=null | Visit-B vào queue |
| 3 | Lễ tân (recept_anh) | Xem queue | GET /api/v1/visits?status=WAITING_VITAL | Cả 2 visit cùng queue, sort theo rule | Sẵn cho y tá |
| 4 | Y tá (nurse_lan) | Đo sinh hiệu cả 2 → VITAL_DONE | POST /vitals (×2); PATCH /status | 201 mỗi visit | returning=true |
| 5 | Bác sĩ (dr_nguyen) | Gọi BN tiếp theo (ưu tiên assigned) | POST /api/v1/visits/call-next | Trả visit theo thứ tự queue | Khám tuần tự |
| 6 | Bác sĩ (dr_nguyen) | Khám + hoàn tất từng visit | PATCH /status {WAITING_PAYMENT} | mỗi visit WAITING_PAYMENT | Thu ngân |
| 7 | Thu ngân (cashier_em) | Invoice + thu tiền từng visit; đóng visit | POST invoices; POST payments; PATCH /status {COMPLETED} | PAID; COMPLETED | Hoàn tất |

- **Kết quả cuối:** 2 Visit COMPLETED; Visit-A có `appointment_id` liên kết và appointment chuyển checked_in/completed; Visit-B `appointment_id=null`.
- **Điểm kiểm chứng (assertions):**
  - Check-in tạo ĐÚNG 1 visit gắn appointment_id; trạng thái appointment cập nhật (không còn booked).
  - Walk-in visit không có appointment_id (VIS-001 phân biệt WALK_IN vs từ appointment).
  - Không thể check-in trùng cùng appointment 2 lần (idempotency → 409/400).
  - Cả 2 visit cùng xuất hiện trong 1 queue/clinic theo đúng sort rule.
  - RLS: appointment + visit chỉ thuộc clinic DEMO.
- **Liên kết function:** APPT-001 (tạo hẹn), APPT-010 (walk-in — lưu ý catalog ghi chưa ship backend/UI), VIS-001 (tạo visit từ appointment/walk-in), VIS-003, BILL-001 → `appt-`, `visit-`, `bill-test-catalog.md`.
- **Lưu ý dò endpoint:** `appt-test-catalog.md` ghi APPT-010 (Walk-in), APPT-011 (Queue board) "chưa có backend/UI" và APPT-006 (Reschedule) thiếu route. Cần xác nhận đường check-in thực tế: có thể là `POST /visits {appointment_id}` (VIS-001) thay vì route `/appointments/{id}/check-in` riêng.

---

### SC-VAR-06 — Đơn thuốc kê ngoại viện (is_internal=false) — BN tự mua ngoài, không trừ tồn
- **Mục tiêu:** Bác sĩ kê đơn NGOẠI VIỆN (RX-003 Internal vs External, cờ `is_internal=false`) — BN tự mua ngoài; đơn này KHÔNG reserve/trừ tồn kho và KHÔNG vào hàng đợi cấp phát của dược sĩ; invoice chỉ tính tiền khám/dịch vụ, không tính thuốc external. **Khác biệt so với luồng chuẩn:** đơn external → bỏ qua bước dược sĩ + không StockMovement; visit đi thẳng tới WAITING_PAYMENT (không qua WAITING_PHARMACY).
- **Vai trò & tài khoản:**
  - Lễ tân: `recept_anh / Recept@1234`
  - Y tá: `nurse_lan / Nurse@1234`
  - Bác sĩ: `dr_nguyen / Doctor@1234`
  - Thu ngân: `cashier_em / Cashier@1234`
- **Tiền điều kiện:** Catalog có thuốc cho phép kê; ghi nhận tồn kho thuốc đó TRƯỚC để so sánh (phải KHÔNG đổi sau kịch bản).
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Tạo visit | POST /api/v1/visits {patient_id} | 201, WAITING_VITAL | Chờ sinh hiệu |
| 2 | Y tá (nurse_lan) | Đo sinh hiệu → VITAL_DONE | POST /vitals; PATCH /status {VITAL_DONE} | 201; VITAL_DONE | returning=true |
| 3 | Bác sĩ (dr_nguyen) | Gọi BN, khám | POST /visits/call-next | IN_CONSULTATION | Đang khám |
| 4 | Bác sĩ (dr_nguyen) | Kê đơn NGOẠI VIỆN (is_internal=false) | POST /api/v1/prescriptions {is_internal:false, items} | 201, đơn external, KHÔNG reserve tồn | Đơn không qua dược |
| 5 | Bác sĩ (dr_nguyen) | Hoàn tất khám → thẳng tới thu ngân | PATCH /api/v1/visits/{id}/status {status:WAITING_PAYMENT} | WAITING_PAYMENT (KHÔNG qua WAITING_PHARMACY) | Thu ngân |
| 6 | Thu ngân (cashier_em) | Lập invoice (chỉ service, không thuốc external) | POST /api/v1/invoices {visit_id} | 201, invoice KHÔNG có dòng thuốc external | Chờ thanh toán |
| 7 | Thu ngân (cashier_em) | Thu tiền + đóng visit | POST payments; PATCH /status {COMPLETED} | PAID; COMPLETED (không cần dispense) | BN ra về |

- **Kết quả cuối:** Visit `COMPLETED` mà KHÔNG qua dược sĩ; tồn kho KHÔNG đổi; đơn external có thể in cho BN mua ngoài.
- **Điểm kiểm chứng (assertions):**
  - Tồn kho thuốc external = tồn ban đầu (không reserve, không StockMovement — RX-003).
  - Đơn external KHÔNG xuất hiện trong `GET /pharmacy/queue` (PHRM-001).
  - Invoice KHÔNG chứa dòng thuốc external (chỉ tiền khám/dịch vụ — BILL-001).
  - Visit chuyển COMPLETED qua nhánh IN_CONSULTATION→WAITING_PAYMENT→COMPLETED (không WAITING_PHARMACY).
  - RLS: visit + đơn chỉ thuộc clinic DEMO.
- **Liên kết function:** RX-003 (internal vs external), RX-001, VIS-001/003/013, PHRM-001 (queue loại trừ external), BILL-001 → `rx-`, `visit-`, `phrm-`, `bill-test-catalog.md`.

---

### SC-VAR-07 — Phân quyền chéo trên các biến thể (403 / RLS / 401) — case bảo mật
- **Mục tiêu:** Kiểm chứng ma trận quyền (BA §13.6 / RBAC-002) và RLS đa tenant áp đúng trên các biến thể: vai trò sai KHÔNG thực hiện được hành động ngoài quyền (403); tài khoản clinic khác KHÔNG thấy/sửa dữ liệu (404/empty); thiếu token → 401. Tái dùng pattern TC-VIS-SEC-01/02 + TC-VIS-RLS-01.
- **Vai trò & tài khoản:**
  - Dược sĩ: `pharm_cuong / Pharm@1234` (không có visit.create, invoice.create, prescription.write)
  - Y tá: `nurse_lan / Nurse@1234` (không có prescription.write, invoice.create, invoice.void)
  - Lễ tân: `recept_anh / Recept@1234` (không có invoice.void, pharmacy.dispense, vital.write)
  - Admin: `admin / Demo@1234` (đối chứng được phép)
  - (Đa tenant) một tài khoản thuộc clinic KHÁC clinic DEMO (nếu seed có), hoặc admin clinic khác.
- **Tiền điều kiện:** Có sẵn 1 visit ở WAITING_PAYMENT, 1 invoice PAID, 1 đơn nội viện chờ dispense trong clinic DEMO (tái dùng output từ SC-VAR-01/03).
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động (bị cấm) | API/Endpoint | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Dược sĩ (pharm_cuong) | Tạo visit | POST /api/v1/visits | 403 (thiếu visit.create) | Không side-effect |
| 2 | Dược sĩ (pharm_cuong) | Tự lập invoice | POST /api/v1/invoices | 403 (thiếu invoice.create) | Không side-effect |
| 3 | Y tá (nurse_lan) | Kê đơn thuốc | POST /api/v1/prescriptions | 403 (thiếu prescription.write) | Không side-effect |
| 4 | Y tá (nurse_lan) | Lập invoice | POST /api/v1/invoices | 403 (thiếu invoice.create) | Không side-effect |
| 5 | Lễ tân (recept_anh) | Nhập sinh hiệu | POST /api/v1/visits/{id}/vitals | 403 (thiếu vital.write) | Không side-effect |
| 6 | Lễ tân (recept_anh) | Hủy (void) invoice | POST /api/v1/invoices/{id}/void | 403 (thiếu invoice.void) | Không side-effect |
| 7 | Lễ tân (recept_anh) | Cấp phát thuốc | POST /api/v1/pharmacy/dispense/{rx_id} | 403 (thiếu pharmacy.dispense) | Không side-effect |
| 8 | Dược sĩ (pharm_cuong) | Tự cấp đơn do CHÍNH MÌNH kê | POST /api/v1/pharmacy/dispense/{rx_id} | 403/422 (rule self-dispense prevention) | Không side-effect |
| 9 | Admin (admin) | Void invoice (đối chứng) | POST /api/v1/invoices/{id}/void | 200/204, invoice VOID | Sinh audit void |
| 10 | Tài khoản clinic khác | Đọc visit/invoice của clinic DEMO | GET /api/v1/visits/{id} | 404/empty (RLS chặn) | Không lộ dữ liệu |
| 11 | (không token) | Gọi bất kỳ endpoint /api/v1/* | GET /api/v1/visits | 401 trước routing | Chặn tầng auth |

- **Kết quả cuối:** Mọi hành động ngoài quyền bị 403; tự cấp đơn của mình bị chặn; truy cập chéo tenant bị RLS chặn (404/empty); request thiếu JWT bị 401; chỉ admin void được invoice.
- **Điểm kiểm chứng (assertions):**
  - Mỗi dòng "bị cấm" trả đúng 403/422, KHÔNG side-effect (visit/invoice/stock không đổi).
  - Self-dispense prevention (BA): dược sĩ không tự cấp đơn do chính mình kê (PHRM rule).
  - Đối chứng admin void: invoice→VOID, sinh audit log void + lý do.
  - RLS: GET cross-tenant trả 404 hoặc list rỗng, KHÔNG lộ dữ liệu clinic khác (TC-VIS-RLS-01, TENANT).
  - Thiếu token → 401 (KHÔNG phải 403), xác nhận chặn ở tầng auth TRƯỚC phân quyền (TC-VIS-SEC-01).
- **Liên kết function:** RBAC-001/002 (roles, permission catalog), VIS-SEC/RLS (TC-VIS-SEC-01/02, TC-VIS-RLS-01), PHRM (self-dispense), BILL (void), TENANT/TENT (cô lập tenant), AUTH (401) → `rbac-`, `visit-`, `phrm-`, `bill-test-catalog.md`, `non-functional/tenant-test-catalog.md`, `auth-test-catalog.md`.

---

## Truy vết function
Các mã function liên kết ánh xạ tới catalog tại:
`E:/MyProject/clinic-cms-workspace/claude-workspace/docs/tasks/TASK-052/deliveries/test-cases/functional` và `/non-functional`.

| Prefix dùng trong scenarios | Catalog file | Ghi chú |
|---|---|---|
| PAT- | functional/patient-test-catalog.md | PAT-001..022 (PATIENT) |
| VIS- | functional/visit-test-catalog.md | VIS-001..014 |
| VTL/VITAL | functional/vital-test-catalog.md | đo sinh hiệu |
| RX- | functional/rx-test-catalog.md | RX-001..016, RX-003 = internal vs external |
| PHRM- | functional/phrm-test-catalog.md | PHRM-001..013, FEFO/dispense/reverse |
| BILL- | functional/bill-test-catalog.md | BILL-001 auto-invoice, BILL-003 manual/bán lẻ |
| APPT- | functional/appt-test-catalog.md | APPT-001 tạo hẹn, APPT-010 walk-in (chưa ship đủ) |
| RBAC- | functional/rbac-test-catalog.md | RBAC-001 roles, RBAC-002 permission catalog |
| AUTH- | functional/auth-test-catalog.md | 401/JWT |
| TENT-/TENANT | non-functional/tenant-test-catalog.md | cô lập tenant (RLS) |

> **Đồng bộ payload BE (2026-05-31, theo `handoff/scenario-review.md`):** mọi bước "thu tiền / POST payments" dùng field `payment_method` (lowercase `cash|card|transfer|momo|vnpay|other`); hủy visit dùng `cancel_reason` (min 3 ký tự); void/refund dùng `reason`; discount dùng `discount_amount` + `discount_reason` (không có `discount_percent`).
>
> **Lưu ý dò endpoint / chốt trước khi chạy:**
> 1. **Bán thuốc lẻ (SC-VAR-02):** catalog hiện chỉ có BILL-003 "manual invoice / bán lẻ" — KHÔNG có route OTC riêng. Xác nhận cơ chế xuất kho gắn manual invoice trong `app/`.
> 2. **Appointment check-in (SC-VAR-05):** APPT-010 (Walk-in) và queue board ghi "chưa có backend/UI"; check-in có thể đi qua `POST /visits {appointment_id}` (VIS-001) thay vì route `/appointments/{id}/check-in`. Xác nhận trong `app/modules/appointments`.
> 3. **Đơn ngoại viện (SC-VAR-06):** dùng cờ `is_internal=false` (RX-003), KHÔNG phải field `type=EXTERNAL`. RX module catalog ghi TODO (chưa ship hết) → cần đối chiếu code TASK-011.
> 4. **Vitals endpoint:** catalog visit liệt kê endpoint visit; endpoint nhập sinh hiệu cụ thể cần lấy từ `vital-test-catalog.md` / module vitals.
> 5. Hậu tố số mã function (vd VIS-001) cần map chính xác với từng catalog khi viết test thực thi.
