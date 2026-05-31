# Kịch bản vận hành — Luồng khám chuẩn (Happy Path đầy đủ 6 vai trò)

**Mục đích:** test E2E theo luồng vận hành thực tế của phòng khám, mỗi bước do ĐÚNG vai trò/tài khoản demo thực hiện đúng nhiệm vụ, bàn giao trạng thái hợp lệ giữa các vai trò theo state machine Visit.
**Số kịch bản:** 5.  **Ngày:** 2026-05-31.

> **Bối cảnh chung (áp dụng mọi kịch bản):**
> - Clinic DEMO (seed_demo_data.py). Mọi request `/api/v1/*` cần JWT (thiếu token → 401 trước routing). Mỗi vai trò đăng nhập riêng qua `POST /api/v1/auth/login {username,password}` lấy access token và dùng đúng token đó cho các bước của mình.
> - **State machine Visit thực tế** (từ catalog VIS-003 / `state_machine.py`): `WAITING_VITAL → {VITAL_DONE, NO_SHOW, CANCELLED}`; `VITAL_DONE → {IN_CONSULTATION, CANCELLED}`; `IN_CONSULTATION → {PAUSED, WAITING_PHARMACY, WAITING_PAYMENT, COMPLETED}`; `PAUSED → {IN_CONSULTATION, CANCELLED}`; `WAITING_PHARMACY → {WAITING_PAYMENT, COMPLETED}`; `WAITING_PAYMENT → {COMPLETED}`. Terminal: COMPLETED / NO_SHOW / CANCELLED. (Tên trạng thái BA gốc WAITING/IN_PROGRESS/AWAITING_PAYMENT ánh xạ tương ứng WAITING_VITAL/IN_CONSULTATION/WAITING_PAYMENT.)
> - **Endpoint visit đã ship** (router `/visits`): `POST /visits`, `GET /visits`, `GET /visits/{id}`, `POST /visits/call-next`, `PATCH /visits/{id}/status`, `POST /visits/{id}/reassign`, `GET /visits/{id}/events`, `PATCH /visits/{id}`.
> - **Endpoint pharmacy đã ship** (TASK-012): `GET /pharmacy/queue`, `GET /pharmacy/dispense/{rx_id}`, `POST /pharmacy/dispense/{rx_id}`. Permission `pharmacy.dispense`, có rule chống tự cấp đơn do chính mình kê.
> - **Endpoint patient đã ship**: `GET /patients/search?q=&type=phone|name|code|all` (`patient.read`), `POST /patients` (`patient.write`).
> - Endpoint cho prescription (RX-*) và invoice/payment (BILL-*) là GỢI Ý theo BA + System Design — các module này trong nguồn function-list còn TODO; cần đối chiếu route thực tế trước khi tự động hoá.
> - Hàng đợi: 1 queue/clinic, sort `priority DESC, is_returning_patient DESC, created_at ASC` (BA §4.6). Mọi thao tác bị RLS giới hạn trong clinic DEMO.

## Danh sách kịch bản
| Mã | Tên kịch bản | Vai trò tham gia | Ưu tiên |
|---|---|---|---|
| SC-HP-01 | Khám tổng quát đầy đủ có kê đơn + cấp thuốc nội viện (FEFO) | Lễ tân → Y tá → Bác sĩ → Thu ngân → Dược sĩ | P0 |
| SC-HP-02 | Khám có chỉ định dịch vụ kỹ thuật (xét nghiệm/siêu âm) + tính tiền dịch vụ | Lễ tân → Y tá → Bác sĩ → Thu ngân → Dược sĩ | P0 |
| SC-HP-03 | Bác sĩ được pre-assign từ lễ tân, "gọi BN tiếp theo" lấy đúng visit của mình | Lễ tân → Y tá → Bác sĩ → Thu ngân → Dược sĩ | P0 |
| SC-HP-04 | Ca ưu tiên (priority=5, thai sản/người già) vượt hàng đợi đúng thứ tự | Lễ tân → Y tá → Bác sĩ → Thu ngân → Dược sĩ | P0 |
| SC-HP-05 | Khám kết hợp dịch vụ + thuốc, thanh toán multi-payment (tiền mặt + chuyển khoản) | Lễ tân → Y tá → Bác sĩ → Thu ngân → Dược sĩ | P1 |

---

## Chi tiết

### SC-HP-01 — Khám tổng quát đầy đủ có kê đơn + cấp thuốc nội viện (FEFO)
- **Mục tiêu:** chạy trọn luồng khám chuẩn (BA §4.5): lễ tân tiếp nhận → y tá đo sinh hiệu → bác sĩ khám + kê đơn thuốc nội viện (reserve tồn) → thu ngân lập hóa đơn + thu tiền → dược sĩ cấp phát theo FEFO → visit COMPLETED.
- **Vai trò & tài khoản:**
  - Lễ tân: `recept_anh / Recept@1234`
  - Y tá: `nurse_lan / Nurse@1234`
  - Bác sĩ: `dr_nguyen / Doctor@1234`
  - Thu ngân: `cashier_em / Cashier@1234`
  - Dược sĩ: `pharm_cuong / Pharm@1234`
- **Tiền điều kiện:**
  - BN đã tồn tại trong clinic DEMO (tra cứu theo SĐT) hoặc cho phép tạo mới.
  - ≥1 thuốc nội viện (internal) còn tồn kho với ≥2 lô (batch) khác hạn dùng để kiểm chứng FEFO.
  - `dr_nguyen` đang trong ca trực.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Đăng nhập lấy token | POST /api/v1/auth/login | 200, access_token (role receptionist) | — |
| 2 | Lễ tân (recept_anh) | Tra cứu BN theo SĐT; nếu không có thì tạo mới | GET /api/v1/patients/search?q=&lt;phone&gt;&type=phone · POST /api/v1/patients | 200 danh sách / 201 patient_code sinh tự động | Có patient_id |
| 3 | Lễ tân (recept_anh) | Tạo visit walk-in (priority=0, chưa assign bác sĩ) | POST /api/v1/visits {type:WALK_IN} | 201, visit.status=WAITING_VITAL, visit_number đúng format | Visit WAITING_VITAL vào hàng đợi → Y tá |
| 4 | Y tá (nurse_lan) | Login + xem hàng đợi, gọi BN đo sinh hiệu | POST /api/v1/auth/login · GET /api/v1/visits?status=WAITING_VITAL | 200, visit hiển thị đúng thứ tự queue | — |
| 5 | Y tá (nurse_lan) | Nhập sinh hiệu (mạch, HA, nhiệt độ, cân nặng) qua dynamic form | POST /api/v1/visits/{id}/vitals (VTL) | 201, VisitVitals lưu; visit chuyển VITAL_DONE | BN quay lại ghế chờ, is_returning_patient=true → Bác sĩ |
| 6 | Bác sĩ (dr_nguyen) | Login + "Gọi BN tiếp theo" | POST /api/v1/auth/login · POST /api/v1/visits/call-next | 200, trả visit của BN; visit.status=IN_CONSULTATION, doctor_id=dr_nguyen | Visit IN_CONSULTATION |
| 7 | Bác sĩ (dr_nguyen) | Chọn dịch vụ "Khám tổng quát" đã thực hiện | POST /api/v1/visits/{id}/services (SVC-006) | 201, VisitService gắn vào visit với giá | — |
| 8 | Bác sĩ (dr_nguyen) | Tạo đơn thuốc + item nội viện (is_internal=true → reserve tồn) | POST /api/v1/prescriptions (RX-001/015) | 201, đơn DRAFT, rx_number; tồn khả dụng giảm (reserved) | Đơn thuốc gắn visit |
| 9 | Bác sĩ (dr_nguyen) | Finalize đơn + "Hoàn tất khám" (có thuốc nội viện → route pharmacy) | PATCH /api/v1/visits/{id}/status {status:WAITING_PHARMACY} | 200, visit.status=WAITING_PHARMACY; đơn vào pharmacy queue | Visit WAITING_PHARMACY → Dược sĩ + Thu ngân |
| 10 | Thu ngân (cashier_em) | Login + lập hóa đơn (auto pull VisitService + Rx internal) | POST /api/v1/auth/login · POST /api/v1/invoices (BILL-001) | 201, invoice gồm dòng khám + dòng thuốc, total đúng | Invoice chưa thanh toán |
| 11 | Thu ngân (cashier_em) | Thu tiền mặt 1 lần | POST /api/v1/invoices/{id}/payments (BILL-006) | 201, payment=total, invoice PAID, tiền thừa=0 | Invoice PAID |
| 12 | Dược sĩ (pharm_cuong) | Login + xem hàng đợi cấp phát | POST /api/v1/auth/login · GET /api/v1/pharmacy/queue (PHRM-001) | 200, đơn của visit này xuất hiện | — |
| 13 | Dược sĩ (pharm_cuong) | Xem gợi ý FEFO + cấp phát (chọn lô hạn gần nhất, trừ tồn) | GET /api/v1/pharmacy/dispense/{rx_id} · POST /api/v1/pharmacy/dispense/{rx_id} (PHRM-002/003/006) | 200, StockMovement (DISPENSE) tạo; tồn thực giảm; reserved giải phóng | Đơn DISPENSED |
| 14 | Hệ thống / Thu ngân | Visit chuyển COMPLETED khi đã PAID + đã cấp phát | (auto) GET /api/v1/visits/{id} (VIS-013) | 200, visit.status=COMPLETED | BN ra về |

- **Kết quả cuối:** Visit=COMPLETED, Invoice=PAID, đơn thuốc=DISPENSED. Sinh ra: VisitVitals, VisitService, Prescription, Invoice + Payment, StockMovement (RESERVE → DISPENSE), audit log cho từng hành động ghi dữ liệu.
- **Điểm kiểm chứng (assertions):**
  - State machine: WAITING_VITAL → VITAL_DONE → IN_CONSULTATION → WAITING_PHARMACY → (WAITING_PAYMENT/COMPLETED), không nhảy cóc; không transition ra khỏi terminal.
  - `doctor_id` của visit = id `dr_nguyen` sau call-next.
  - `is_returning_patient` = true sau khi nhập sinh hiệu.
  - Tổng tiền hóa đơn = giá dịch vụ khám + giá thuốc nội viện; sau payment `amount_paid = total`, `balance = 0`.
  - FEFO: lô được trừ là lô có `expiry_date` gần nhất còn đủ số lượng; tồn khả dụng giảm từ bước reserve, tồn thực giảm khi dispense; không âm kho (atomic, PHRM-006).
  - RLS: mọi bản ghi (patient, visit, invoice, stock) thuộc clinic DEMO; token vai trò ở clinic khác truy cập visit này → 404/403.
  - Audit: mỗi bước (visit create, vitals, status change, invoice, payment, dispense) tạo audit log với đúng actor.
- **Liên kết function:** AUTH (login), PAT-* (search/create), VIS-001 (create), VIS-003 (state machine), VTL-* (vitals), VIS-012 (call-next), SVC-006 (add service), RX-001/RX-015 (đơn + reserve), VIS-013 (completion auto-trigger), BILL-001/BILL-006 (invoice + cash payment), PHRM-001/002/003/006 (queue + dispense FEFO + atomic), RBAC-* (ma trận quyền), TENANT (RLS), AUDIT.

---

### SC-HP-02 — Khám có chỉ định dịch vụ kỹ thuật (xét nghiệm/siêu âm) + tính tiền dịch vụ
- **Mục tiêu:** kiểm chứng luồng có chỉ định dịch vụ kỹ thuật do y tá thực hiện (service.perform), hóa đơn auto-pull phí dịch vụ; ca không kê thuốc nội viện (đi thẳng WAITING_PAYMENT, không qua pharmacy).
- **Vai trò & tài khoản:**
  - Lễ tân: `recept_anh / Recept@1234`
  - Y tá: `nurse_huong / Nurse@1234`
  - Bác sĩ: `dr_le / Doctor@1234`
  - Thu ngân: `cashier_em / Cashier@1234`
  - Dược sĩ: `pharm_cuong / Pharm@1234` (chỉ kiểm tra hàng đợi cấp phát rỗng cho visit này)
- **Tiền điều kiện:**
  - Catalog dịch vụ có ≥2 dịch vụ kỹ thuật (vd "Xét nghiệm máu", "Siêu âm ổ bụng") với đơn giá cấu hình sẵn.
  - BN tồn tại hoặc tạo mới.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Login + tạo visit walk-in | POST /api/v1/auth/login · POST /api/v1/visits | 201, visit.status=WAITING_VITAL | Visit WAITING_VITAL → Y tá |
| 2 | Y tá (nurse_huong) | Login + nhập sinh hiệu | POST /api/v1/auth/login · POST /api/v1/visits/{id}/vitals | 201, vitals lưu; visit VITAL_DONE | is_returning_patient=true → Bác sĩ |
| 3 | Bác sĩ (dr_le) | Login + gọi BN tiếp theo | POST /api/v1/visits/call-next | 200, visit IN_CONSULTATION, doctor_id=dr_le | Visit IN_CONSULTATION |
| 4 | Bác sĩ (dr_le) | Chỉ định dịch vụ "Xét nghiệm máu" + "Siêu âm ổ bụng" | POST /api/v1/visits/{id}/services (SVC-006) | 201 mỗi dịch vụ, VisitService với giá | Có chỉ định kỹ thuật |
| 5 | Y tá (nurse_huong) | Thực hiện dịch vụ kỹ thuật (service.perform) + đánh dấu hoàn thành | PATCH /api/v1/visits/{id}/services/{svcId} (SVC-007) | 200, VisitService.status=DONE | Dịch vụ đã thực hiện |
| 6 | Bác sĩ (dr_le) | Kết luận + "Hoàn tất khám" (không thuốc nội viện) | PATCH /api/v1/visits/{id}/status {status:WAITING_PAYMENT} | 200, visit.status=WAITING_PAYMENT | Visit WAITING_PAYMENT → Thu ngân |
| 7 | Thu ngân (cashier_em) | Login + lập hóa đơn (auto pull VisitService) | POST /api/v1/invoices | 201, invoice gồm 2 dòng dịch vụ kỹ thuật, total = tổng giá dịch vụ | Invoice chưa thanh toán |
| 8 | Thu ngân (cashier_em) | Thu tiền | POST /api/v1/invoices/{id}/payments | 201, invoice PAID | Invoice PAID |
| 9 | Dược sĩ (pharm_cuong) | Kiểm tra hàng đợi cấp phát (rỗng cho visit này) | GET /api/v1/pharmacy/queue | 200, không có đơn nội viện cho visit này | — |
| 10 | Hệ thống | Visit → COMPLETED (đã PAID, không cần cấp phát) | GET /api/v1/visits/{id} | 200, visit.status=COMPLETED | BN ra về |

- **Kết quả cuối:** Visit=COMPLETED, Invoice=PAID gồm phí dịch vụ kỹ thuật; KHÔNG có StockMovement (không có thuốc nội viện).
- **Điểm kiểm chứng (assertions):**
  - Hóa đơn auto-pull đúng các VisitService DONE; total = tổng đơn giá cấu hình của dịch vụ.
  - Y tá có quyền `service.perform`; nếu dùng token dược sĩ (`pharm_cuong`) gọi perform → **403** (kiểm chứng phân quyền chéo: pharmacist không có service.perform).
  - Không sinh StockMovement; tồn kho thuốc không đổi.
  - State machine: IN_CONSULTATION → WAITING_PAYMENT → COMPLETED (bỏ qua WAITING_PHARMACY vì không có thuốc nội viện). RLS: dịch vụ + hóa đơn thuộc clinic DEMO.
- **Liên kết function:** VIS-001, VTL-*, VIS-012 (call-next), SVC-006 (add service vào visit), SVC-007 (VisitService tracking/perform), VIS-003, BILL-001/BILL-006, PHRM-001 (queue rỗng), RBAC-* (service.perform 403 cho pharmacist), TENANT (RLS).

---

### SC-HP-03 — Bác sĩ được pre-assign từ lễ tân, "gọi BN tiếp theo" lấy đúng visit của mình
- **Mục tiêu:** kiểm chứng quy tắc call-next ưu tiên visit đã assigned cho bác sĩ hiện tại trước visit chưa assign. Lễ tân pre-assign `dr_tran`; có thêm 1 visit "mồi" chưa assign tạo trước để chứng minh bác sĩ vẫn lấy đúng visit của mình.
- **Vai trò & tài khoản:**
  - Lễ tân: `recept_binh / Recept@1234`
  - Y tá: `nurse_linh / Nurse@1234`
  - Bác sĩ: `dr_tran / Doctor@1234`
  - Thu ngân: `cashier_em / Cashier@1234`
  - Dược sĩ: `pharm_dung / Pharm@1234`
- **Tiền điều kiện:**
  - 1 visit "mồi" đã ở WAITING_VITAL, chưa assign bác sĩ, created_at sớm hơn (chứng minh assigned được ưu tiên hơn unassigned ở cùng priority).
  - Thuốc nội viện còn tồn cho ca có kê đơn.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_binh) | Login + tạo visit pre-assign `dr_tran`, priority=0 | POST /api/v1/auth/login · POST /api/v1/visits {assigned_doctor_id:dr_tran} | 201, visit.status=WAITING_VITAL, doctor_id=dr_tran | Visit WAITING_VITAL (assigned) → Y tá |
| 2 | Y tá (nurse_linh) | Login + nhập sinh hiệu | POST /api/v1/visits/{id}/vitals | 201, vitals lưu; visit VITAL_DONE | is_returning_patient=true → Bác sĩ |
| 3 | Bác sĩ (dr_tran) | Login + "Gọi BN tiếp theo" | POST /api/v1/visits/call-next | 200, trả ĐÚNG visit assigned cho dr_tran (KHÔNG phải visit mồi unassigned) | Visit IN_CONSULTATION, doctor_id=dr_tran |
| 4 | Bác sĩ (dr_tran) | Khám + chọn dịch vụ + kê đơn nội viện | POST /api/v1/visits/{id}/services · POST /api/v1/prescriptions | 201, dịch vụ + đơn thuốc reserve tồn | — |
| 5 | Bác sĩ (dr_tran) | Hoàn tất khám (route pharmacy) | PATCH /api/v1/visits/{id}/status {status:WAITING_PHARMACY} | 200, visit.status=WAITING_PHARMACY | → Thu ngân + Dược sĩ |
| 6 | Thu ngân (cashier_em) | Login + lập hóa đơn + thu tiền | POST /api/v1/invoices · POST /api/v1/invoices/{id}/payments | 201/201, invoice PAID | → Dược sĩ |
| 7 | Dược sĩ (pharm_dung) | Cấp phát FEFO | GET + POST /api/v1/pharmacy/dispense/{rx_id} | 200, StockMovement DISPENSE | Đơn DISPENSED |
| 8 | Hệ thống | Visit → COMPLETED | GET /api/v1/visits/{id} | 200, COMPLETED | BN ra về |

- **Kết quả cuối:** Visit của BN assigned = COMPLETED; visit "mồi" unassigned vẫn còn WAITING_VITAL (chứng minh không bị bác sĩ này lấy nhầm).
- **Điểm kiểm chứng (assertions):**
  - Call-next của `dr_tran` trả visit có `doctor_id = dr_tran`, KHÔNG trả visit mồi unassigned dù mồi tạo trước.
  - Sau khi assigned visit xử lý xong, nếu `dr_tran` call-next lần nữa mới nhận visit mồi (kiểm chứng phụ).
  - State machine + hóa đơn + FEFO đúng như SC-HP-01.
  - RLS: chỉ visit clinic DEMO trong queue của bác sĩ.
- **Liên kết function:** VIS-001 (create), VIS-009 (doctor assignment / pre-assign), VIS-012 (call-next ưu tiên assigned), VTL-*, SVC-006, RX-001/015, VIS-003, BILL-001/006, PHRM-002/006, RBAC-*, TENANT.

---

### SC-HP-04 — Ca ưu tiên (priority=5, thai sản/người già) vượt hàng đợi đúng thứ tự
- **Mục tiêu:** kiểm chứng quy tắc hàng đợi BA §4.6 — visit priority cao hơn được gọi trước dù tạo sau. Lễ tân tạo trước 1 visit thường (priority=0), sau đó tạo 1 visit ưu tiên (priority=5); bác sĩ call-next phải nhận visit ưu tiên trước.
- **Vai trò & tài khoản:**
  - Lễ tân: `recept_anh / Recept@1234`
  - Y tá: `nurse_lan / Nurse@1234`
  - Bác sĩ: `dr_pham / Doctor@1234`
  - Thu ngân: `cashier_em / Cashier@1234`
  - Dược sĩ: `pharm_cuong / Pharm@1234`
- **Tiền điều kiện:**
  - Kiểm soát hàng đợi bằng 2 visit tạo trong test để thứ tự rõ ràng.
  - 2 BN: BN-thường và BN-ưu-tiên (sản phụ / người cao tuổi).
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Login + tạo visit BN-thường priority=0 (tạo TRƯỚC) | POST /api/v1/visits {priority:0} | 201, visit_A WAITING_VITAL | A vào queue |
| 2 | Lễ tân (recept_anh) | Tạo visit BN-ưu-tiên priority=5 (tạo SAU) | POST /api/v1/visits {priority:5} | 201, visit_B WAITING_VITAL | B vào queue |
| 3 | Lễ tân (recept_anh) | Xem hàng đợi | GET /api/v1/visits?status=WAITING_VITAL (sort queue) | 200, thứ tự: B (priority 5) đứng TRƯỚC A (priority 0) | Thứ tự queue đúng |
| 4 | Y tá (nurse_lan) | Login + nhập sinh hiệu cho BN-ưu-tiên B | POST /api/v1/visits/{B}/vitals | 201, vitals lưu; B VITAL_DONE | B is_returning_patient=true → Bác sĩ |
| 5 | Bác sĩ (dr_pham) | Login + "Gọi BN tiếp theo" | POST /api/v1/visits/call-next | 200, trả ĐÚNG visit_B (ưu tiên), KHÔNG phải A | visit_B IN_CONSULTATION |
| 6 | Bác sĩ (dr_pham) | Khám B + chọn dịch vụ + kê đơn nội viện | POST /api/v1/visits/{B}/services · POST /api/v1/prescriptions | 201, dịch vụ + đơn reserve tồn | — |
| 7 | Bác sĩ (dr_pham) | Hoàn tất khám B | PATCH /api/v1/visits/{B}/status {status:WAITING_PHARMACY} | 200, visit_B WAITING_PHARMACY | → Thu ngân + Dược sĩ |
| 8 | Thu ngân (cashier_em) | Lập hóa đơn + thu tiền cho B | POST /api/v1/invoices · POST /api/v1/invoices/{id}/payments | invoice PAID | → Dược sĩ |
| 9 | Dược sĩ (pharm_cuong) | Cấp phát FEFO cho B | GET + POST /api/v1/pharmacy/dispense/{rx_id} | 200, StockMovement DISPENSE | Đơn DISPENSED |
| 10 | Hệ thống | visit_B → COMPLETED; visit_A vẫn WAITING_VITAL | GET /api/v1/visits | 200, B COMPLETED, A còn WAITING_VITAL đầu queue | A chờ lượt kế |

- **Kết quả cuối:** visit_B (ưu tiên) hoàn tất trọn luồng → COMPLETED; visit_A (thường) vẫn WAITING_VITAL, chứng minh ưu tiên vượt hàng đợi.
- **Điểm kiểm chứng (assertions):**
  - GET queue trả thứ tự `priority DESC` → B trước A dù A.created_at < B.created_at.
  - Call-next của bác sĩ trả visit_B trước (priority cao hơn), không trả A.
  - Sau khi xử lý B, A vẫn nguyên trạng WAITING_VITAL (không bị bỏ qua/huỷ).
  - State machine, hóa đơn, FEFO đúng. RLS: cả A và B đều thuộc clinic DEMO.
- **Liên kết function:** VIS-001 (create), VIS-003, VIS-012 (call-next theo priority/queue sort), VTL-*, SVC-006, RX-001/015, BILL-001/006, PHRM-002/006, TENANT.

---

### SC-HP-05 — Khám kết hợp dịch vụ + thuốc, thanh toán multi-payment (tiền mặt + chuyển khoản)
- **Mục tiêu:** kiểm chứng ca có cả dịch vụ kỹ thuật lẫn thuốc nội viện, hóa đơn auto-pull cả hai loại dòng, và thu tiền nhiều lần (multi/split payment) đến khi đủ total mới PAID; sau đó cấp phát thuốc và đóng visit.
- **Vai trò & tài khoản:**
  - Lễ tân: `recept_binh / Recept@1234`
  - Y tá: `nurse_huong / Nurse@1234`
  - Bác sĩ: `dr_hoang / Doctor@1234`
  - Thu ngân: `cashier_em / Cashier@1234`
  - Dược sĩ: `pharm_dung / Pharm@1234`
- **Tiền điều kiện:**
  - Catalog có dịch vụ kỹ thuật + thuốc nội viện còn tồn (≥2 lô để FEFO).
  - BN tồn tại hoặc tạo mới.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_binh) | Login + tạo visit walk-in | POST /api/v1/visits | 201, visit WAITING_VITAL | → Y tá |
| 2 | Y tá (nurse_huong) | Login + nhập sinh hiệu | POST /api/v1/visits/{id}/vitals | 201, vitals lưu; visit VITAL_DONE | is_returning_patient=true → Bác sĩ |
| 3 | Bác sĩ (dr_hoang) | Login + gọi BN tiếp theo | POST /api/v1/visits/call-next | 200, visit IN_CONSULTATION, doctor_id=dr_hoang | — |
| 4 | Bác sĩ (dr_hoang) | Chỉ định dịch vụ kỹ thuật + kê đơn thuốc nội viện | POST /api/v1/visits/{id}/services · POST /api/v1/prescriptions | 201, VisitService + Rx item reserve tồn | — |
| 5 | Y tá (nurse_huong) | Thực hiện dịch vụ kỹ thuật | PATCH /api/v1/visits/{id}/services/{svcId} | 200, VisitService DONE | — |
| 6 | Bác sĩ (dr_hoang) | Finalize đơn + hoàn tất khám (route pharmacy) | PATCH /api/v1/visits/{id}/status {status:WAITING_PHARMACY} | 200, visit WAITING_PHARMACY | → Thu ngân + Dược sĩ |
| 7 | Thu ngân (cashier_em) | Login + lập hóa đơn (auto-pull dịch vụ + thuốc) | POST /api/v1/invoices | 201, invoice gồm dòng dịch vụ + dòng thuốc, total đúng | Invoice chưa thanh toán |
| 8 | Thu ngân (cashier_em) | Thu lần 1 — tiền mặt (1 phần total) | POST /api/v1/invoices/{id}/payments {payment_method:"cash", amount:...} | 201, invoice PARTIALLY_PAID, balance > 0 | Còn nợ |
| 9 | Thu ngân (cashier_em) | Thu lần 2 — chuyển khoản (phần còn lại) | POST /api/v1/invoices/{id}/payments {payment_method:"bank_transfer", amount:...} | 201, tổng 2 payment = total, invoice PAID, balance=0 | Invoice PAID → Dược sĩ |
| 10 | Dược sĩ (pharm_dung) | Xem hàng đợi + cấp phát FEFO | GET /api/v1/pharmacy/queue · POST /api/v1/pharmacy/dispense/{rx_id} | 200, StockMovement DISPENSE; tồn giảm; reserved giải phóng | Đơn DISPENSED |
| 11 | Hệ thống | Visit → COMPLETED | GET /api/v1/visits/{id} | 200, COMPLETED | BN ra về |

- **Kết quả cuối:** Visit=COMPLETED, Invoice=PAID với 2 bản ghi Payment (CASH + BANK_TRANSFER), đơn thuốc=DISPENSED, StockMovement DISPENSE.
- **Điểm kiểm chứng (assertions):**
  - Hóa đơn auto-pull đủ cả dòng dịch vụ kỹ thuật (DONE) lẫn dòng thuốc nội viện; total = tổng đúng.
  - Sau payment 1: status=PARTIALLY_PAID, `balance = total - payment1`; sau payment 2: `sum(payments) = total`, balance=0, status=PAID.
  - FEFO + không âm kho; reserved giải phóng khi dispense.
  - State machine đúng; RLS: tất cả bản ghi thuộc clinic DEMO.
  - Phân quyền chéo: `invoice.void` chỉ Admin — nếu `cashier_em` gọi void hóa đơn → **403** (kiểm chứng phụ).
- **Liên kết function:** VIS-001, VTL-*, VIS-012, SVC-006/007 (perform), RX-001/015, VIS-003, BILL-001 (auto-pull), BILL-005 (multi-payment), BILL-013 (partial payment), BILL-015 (void — case 403), PHRM-001/002/006 (queue + dispense FEFO), RBAC-*, TENANT, AUDIT.

> **Đồng bộ payload BE (2026-05-31, theo `handoff/scenario-review.md`):** mọi bước "Thu tiền / POST payments" ở SC-HP-01..05 dùng field `payment_method` với giá trị lowercase `cash|card|transfer|momo|vnpay|other` (KHÔNG phải `method:CASH/BANK_TRANSFER`; `BANK_TRANSFER`→`transfer`) — theo `invoice_schemas.py`.

---

## Ghi chú truy vết
- Catalog function gốc: `E:/MyProject/clinic-cms-workspace/claude-workspace/docs/tasks/TASK-052/deliveries/test-cases/functional/` (visit=VIS, vital=VTL, svc=SVC, rx=RX, bill=BILL, phrm=PHRM, patient=PAT, rbac=RBAC) và `/non-functional/` (tenant=RLS, audit).
- **Trạng thái module (theo catalog):** Visit (VIS) & Patient (PAT) & Pharmacy (PHRM) đã ship; Vital (VTL), Service (SVC), Prescription (RX), Billing (BILL) phần lớn TODO trong nguồn function-list → endpoint RX/BILL/vitals là GỢI Ý theo BA + System Design, cần đối chiếu route thực tế (`app/modules/*`) trước khi tự động hoá.
- State machine dùng tên thực tế: WAITING_VITAL / VITAL_DONE / IN_CONSULTATION / PAUSED / WAITING_PHARMACY / WAITING_PAYMENT / COMPLETED (xem VIS-003).
- Endpoint pharmacy chuẩn (TASK-012): `GET /pharmacy/queue`, `GET|POST /pharmacy/dispense/{rx_id}`.
