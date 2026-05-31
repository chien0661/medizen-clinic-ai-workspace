# Kịch bản vận hành — Luồng ngoại lệ & Hủy

**Mục đích:** test E2E theo luồng vận hành thực tế của phòng khám, mỗi bước do ĐÚNG vai trò/tài khoản demo thực hiện, bàn giao trạng thái hợp lệ giữa các vai trò theo state machine. Nhóm này tập trung vào các nhánh NGOẠI LỆ và HỦY: hủy hóa đơn + hoàn tiền, hủy visit + hoàn tồn thuốc reserve, no-show, thiếu tồn khi cấp phát, sửa đơn sau khám, thanh toán nhiều đợt, giảm giá hóa đơn, đo lại sinh hiệu.

**Số kịch bản:** 8. **Ngày:** 2026-05-31.

> Ghi chú truy vết: mã function (VIS-, VTL-, RX-, BILL-, PHRM-, RBAC-, APPT-, AUDIT-) liên kết về catalog functional/non-functional tại `E:/MyProject/clinic-cms-workspace/claude-workspace/docs/tasks/TASK-052/deliveries/test-cases`. Các endpoint là "gợi ý" theo system design (FastAPI `/api/v1/*`); kiểm thử cần đối chiếu lại OpenAPI thực tế khi chạy.
>
> Quy ước chung mọi kịch bản:
> - Mọi request `/api/v1/*` cần JWT hợp lệ (thiếu token → **401 trước routing**).
> - RLS đa tenant: mọi truy vấn/ghi bị giới hạn trong `clinic_id` của tài khoản đăng nhập (clinic DEMO). Tài khoản clinic khác không thấy/không sửa được dữ liệu DEMO → 404/403.
> - **State machine Visit (enum `VisitStatus` thực tế trong `state_machine.py`):** `WAITING_VITAL → {VITAL_DONE, NO_SHOW, CANCELLED}`; `VITAL_DONE → {IN_CONSULTATION, CANCELLED}`; `IN_CONSULTATION → {PAUSED, WAITING_PHARMACY, WAITING_PAYMENT, COMPLETED}`; `PAUSED → {IN_CONSULTATION, CANCELLED}`; `WAITING_PHARMACY → {WAITING_PAYMENT, COMPLETED}`; `WAITING_PAYMENT → {COMPLETED}`. Các trạng thái `COMPLETED / NO_SHOW / CANCELLED` là **terminal** (không transition ra). Brief vận hành dùng tên rút gọn (WAITING≈WAITING_VITAL, IN_PROGRESS≈IN_CONSULTATION, AWAITING_PAYMENT≈WAITING_PAYMENT); kịch bản dưới ưu tiên enum thực tế.
> - **State machine Invoice (theo bill-test-catalog):** DRAFT → ISSUED → {PARTIALLY_PAID} → PAID; nhánh VOIDED (BILL-015) + REFUNDED (BILL-017). Sửa line item chỉ khi DRAFT (BILL-004), khóa khi ISSUED/PAID.
> - Quyền theo BA §13.6 (ma trận RBAC).
>
> ⚠️ **DRIFT/GAP thực tế đã phát hiện (api-mapping v2, ảnh hưởng tới expected của nhóm này):**
> - **BILL-016 (Void → reverse stock):** hiện void hóa đơn **KHÔNG tự hoàn thuốc về kho** → SC-EXC-01 đánh dấu assertion hoàn-kho là **kỳ vọng đúng nghiệp vụ nhưng có thể FAIL trên build hiện tại** (xác nhận khi chạy).
> - **PHRM-005 (Partial dispense):** logic dispense từng bị ghi nhận "all-or-nothing"; catalog phrm đánh PHRM-005 COVERED@TASK-012 → SC-EXC-04 cần kiểm chứng kỹ partial có thực sự cho phép hay bị chặn cả đơn.
> - **VITAL/VTL module CHƯA ship** trong `clinic-cms-merge` (không có file `*vital*`, không có `WAITING_VITAL`/`VITAL_DONE` thực thi đầy đủ) → SC-EXC-08 là forward-looking (nghiệm thu khi TASK-009 implement).
> - **RX-006 (cảnh báo dị ứng)** và **BILL-012 (VAT theo config, hiện hardcode 0)** là GAP/DRIFT — không phải trọng tâm nhóm này nhưng ghi nhận để không kỳ vọng sai.

## Danh sách kịch bản

| Mã | Tên kịch bản | Vai trò tham gia | Ưu tiên |
|---|---|---|---|
| SC-EXC-01 | Hủy hóa đơn đã thu tiền + hoàn tiền (chỉ Admin có `invoice.void`) | Lễ tân → Thu ngân → Admin | P0 |
| SC-EXC-02 | Hủy visit giữa chừng (IN_CONSULTATION → CANCELLED) + hoàn lại tồn thuốc đã reserve | Lễ tân → Y tá → Bác sĩ → Admin | P0 |
| SC-EXC-03 | Bệnh nhân no-show (có lịch hẹn nhưng không đến) | Lễ tân | P1 |
| SC-EXC-04 | Thuốc hết tồn / không đủ batch khi Dược sĩ cấp phát → xử lý cấp phát thiếu | Bác sĩ → Thu ngân → Dược sĩ | P0 |
| SC-EXC-05 | Sửa đơn thuốc sau khi Bác sĩ hoàn tất khám nhưng TRƯỚC khi cấp phát | Bác sĩ → Dược sĩ | P1 |
| SC-EXC-06 | Thanh toán nhiều đợt: trả thiếu (partial) → trả tiếp đến khi đủ | Bác sĩ → Thu ngân | P0 |
| SC-EXC-07 | Điều chỉnh / giảm giá hóa đơn (discount) trước khi thu tiền | Bác sĩ → Thu ngân → Admin | P1 |
| SC-EXC-08 | Đo lại sinh hiệu — 1 visit nhiều lần đo (re-vital) | Lễ tân → Y tá → Bác sĩ | P1 |

---

## Chi tiết

### SC-EXC-01 — Hủy hóa đơn đã thu tiền + hoàn tiền (chỉ Admin có `invoice.void`)

- **Mục tiêu:** Sau khi hóa đơn đã ở trạng thái PAID (đã thu tiền), xác minh CHỈ Admin (`invoice.void`) mới void được hóa đơn; các vai trò khác (Lễ tân, Thu ngân) bị 403. Khi void thành công, hệ thống tạo bản ghi hoàn tiền (refund) và ghi audit.
- **Vai trò & tài khoản:**
  - Lễ tân — `recept_anh / Recept@1234` (chuẩn bị visit; thử void → 403).
  - Thu ngân — `cashier_em / Cashier@1234` (lập invoice, thu tiền; thử void → 403).
  - Admin — `admin / Demo@1234` (void invoice + hoàn tiền).
- **Tiền điều kiện:**
  - BN đã có sẵn (vd `patient_code` BN-DEMO-001) hoặc tạo mới.
  - 1 visit DEMO đã đi hết luồng tới WAITING_PAYMENT (AWAITING_PAYMENT theo brief), có ≥1 VisitService (vd "Khám tổng quát").
  - Bảng giá dịch vụ có sẵn để invoice tính được total.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Chuẩn bị visit ở trạng thái WAITING_PAYMENT có dịch vụ | POST /api/v1/visits → ... → visit.status=WAITING_PAYMENT | 201/200; visit.status=WAITING_PAYMENT | Visit sẵn sàng lập hóa đơn |
| 2 | Thu ngân (cashier_em) | Lập invoice (auto pull VisitService) | POST /api/v1/invoices {visit_id} | 201; invoice.status=UNPAID; total>0 | Invoice chờ thu tiền |
| 3 | Thu ngân (cashier_em) | Thu đủ tiền (1 lần) | POST /api/v1/invoices/{id}/payments {amount=total, payment_method="cash"} | 201; invoice.status=PAID; paid_amount=total | Hóa đơn đã thanh toán |
| 4 | Thu ngân (cashier_em) | THỬ void hóa đơn (không có quyền) | POST /api/v1/invoices/{id}/void | **403 Forbidden** (thiếu `invoice.void`) | Hóa đơn vẫn PAID, không đổi |
| 5 | Lễ tân (recept_anh) | THỬ void hóa đơn (không có quyền) | POST /api/v1/invoices/{id}/void | **403 Forbidden** | Hóa đơn vẫn PAID |
| 6 | Admin (admin) | Void hóa đơn + ghi lý do | POST /api/v1/invoices/{id}/void {reason} | 200; invoice.status=VOIDED; tạo refund record | Hóa đơn bị hủy, phát sinh hoàn tiền |
| 7 | Admin (admin) | Kiểm tra audit + refund | GET /api/v1/invoices/{id} ; GET /api/v1/audit-logs?entity=invoice&id={id} | invoice.status=VOIDED; audit có action=invoice.void; refund.amount=total | Hoàn tất, chờ ra về |

- **Kết quả cuối:** Invoice.status = VOIDED; phát sinh bản ghi refund/credit note với số tiền = số đã thu; audit log ghi người void (admin) + lý do.
- **Điểm kiểm chứng (assertions):**
  - Bước 4 & 5: HTTP 403, body chỉ ra thiếu permission `invoice.void`; invoice KHÔNG đổi trạng thái.
  - Bước 6: invoice.status=VOIDED; tổng refund = tổng đã thanh toán (paid_amount); không cho void lần 2 (idempotent/409).
  - Audit log: 1 record `invoice.void` actor=admin, có `reason`, timestamp; không sửa/ẩn được record cũ.
  - RLS: admin clinic khác gọi void invoice DEMO → 404 (không thấy).
  - Số tiền: sau void, balance về 0 hoặc phát sinh credit dương đúng bằng paid_amount.
  - (Cần xác nhận functional design) Hành vi của visit sau void — có quay lại WAITING_PAYMENT hay không — ghi assertion mở.
- **Liên kết function:** BILL-015 (void invoice, admin), BILL-016 (void→reverse stock — DRIFT), BILL-017 (refund full/partial, admin), BILL-005/006 (payment), BILL-001/003 (tạo invoice), RBAC (gate `invoice.void` chỉ admin), AUDIT (audit log).

---

### SC-EXC-02 — Hủy visit giữa chừng (IN_CONSULTATION → CANCELLED) + hoàn lại tồn thuốc đã reserve

- **Mục tiêu:** Visit đang IN_CONSULTATION (brief: IN_PROGRESS), bác sĩ đã kê đơn thuốc in-house (đã reserve trừ tồn khả dụng). Hủy visit phải chuyển CANCELLED và HOÀN LẠI số tồn đã reserve (release reservation), không tạo invoice / hủy invoice nháp nếu có. Lưu ý state machine thực: CANCELLED hợp lệ từ WAITING_VITAL/VITAL_DONE/IN_CONSULTATION/PAUSED — KHÔNG từ WAITING_PHARMACY/WAITING_PAYMENT/COMPLETED.
- **Vai trò & tài khoản:**
  - Lễ tân — `recept_anh / Recept@1234` (tạo visit).
  - Y tá — `nurse_lan / Nurse@1234` (đo sinh hiệu).
  - Bác sĩ — `dr_nguyen / Doctor@1234` (gọi BN, kê đơn in-house → reserve tồn).
  - Admin — `admin / Demo@1234` (hủy visit; hoặc xác nhận quyền hủy theo policy).
- **Tiền điều kiện:**
  - Thuốc in-house (vd Paracetamol 500mg) có tồn khả dụng ban đầu = Q0 (vd 100 viên), có batch FEFO.
  - Ca trực của dr_nguyen mở.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Tạo visit | POST /api/v1/visits | 201; visit.status=WAITING_VITAL | Vào hàng đợi |
| 2 | Y tá (nurse_lan) | Đo sinh hiệu | POST /api/v1/visits/{id}/vitals | 201; vitals lưu; visit.status=VITAL_DONE | BN quay ghế chờ (is_returning_patient=true) |
| 3 | Bác sĩ (dr_nguyen) | Gọi BN tiếp theo | POST /api/v1/visits/next (hoặc /visits/{id}/start) | 200; visit.status=IN_CONSULTATION; doctor_id=dr_nguyen | Đang khám |
| 4 | Bác sĩ (dr_nguyen) | Kê đơn in-house (vd 20 viên Paracetamol) | POST /api/v1/visits/{id}/prescriptions | 201; reserved_qty=20; tồn khả dụng = Q0-20 | Đơn đã reserve tồn |
| 5 | Bác sĩ (dr_nguyen) / Admin (admin) | Hủy visit giữa chừng + lý do | POST /api/v1/visits/{id}/cancel {cancel_reason} (bắt buộc, min 3 ký tự) | 200; visit.status=CANCELLED | Kích hoạt rollback |
| 6 | Admin (admin) | Kiểm tra tồn được release | GET /api/v1/inventory/items/{drug} | tồn khả dụng = Q0 (đã hoàn 20); reserved=0 | Tồn về như cũ |
| 7 | Admin (admin) | Kiểm tra không có invoice phát sinh / invoice nháp bị hủy | GET /api/v1/invoices?visit_id={id} | rỗng hoặc invoice.status=VOIDED | Đóng visit |

- **Kết quả cuối:** Visit.status=CANCELLED; reservation thuốc được release hoàn toàn (available về Q0, reserved=0); KHÔNG có StockMovement loại "dispense" (vì chưa cấp phát); audit ghi cancel + reason. Không phát sinh doanh thu.
- **Điểm kiểm chứng (assertions):**
  - Sau bước 4: tồn khả dụng giảm đúng 20; physical_qty chưa đổi (mới reserve, chưa xuất kho).
  - Sau bước 5–6: tồn khả dụng = Q0; reserved=0; có bản ghi release reservation (hoặc StockMovement reverse) nếu hệ thống ghi chuyển động.
  - Không thể hủy visit đã COMPLETED/terminal (CANCELLED chỉ từ WAITING_VITAL/VITAL_DONE/IN_CONSULTATION/PAUSED); thử hủy từ WAITING_PHARMACY/WAITING_PAYMENT/COMPLETED → 409 (invalid transition).
  - RLS: admin clinic khác không hủy được visit DEMO → 404.
- **Liên kết function:** VIS-005 (CANCELLED status), VIS-003 (state machine), RX-001 (tạo đơn), RX-015 (reserve stock đơn internal), RX-012 (cancel đơn trước dispense → release), PHRM-012 (reverse dispense / hoàn tồn kho), PHRM-006 (stock decrement atomic), AUDIT.

---

### SC-EXC-03 — Bệnh nhân no-show (có lịch hẹn nhưng không đến)

- **Mục tiêu:** Có lịch hẹn (Appointment) nhưng BN không đến trong khung giờ; Lễ tân/hệ thống đánh dấu no-show. Không tạo visit, không reserve, không phát sinh doanh thu; lịch hẹn chuyển NO_SHOW và giải phóng slot.
- **Vai trò & tài khoản:**
  - Lễ tân — `recept_anh / Recept@1234` (tạo appointment, sau đó đánh dấu no-show, đặt lại lịch).
- **Tiền điều kiện:**
  - BN có sẵn; bác sĩ dr_le có lịch trống.
  - Appointment được đặt cho thời điểm trong quá khứ gần (đã qua giờ hẹn) hoặc dùng cơ chế đánh dấu thủ công.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Tạo lịch hẹn cho BN với dr_le | POST /api/v1/appointments {patient_id, doctor_id, scheduled_at} | 201; appointment.status=SCHEDULED/CONFIRMED | Slot đã đặt |
| 2 | Lễ tân (recept_anh) | Qua giờ hẹn, BN không đến → đánh dấu no-show | POST /api/v1/appointments/{id}/no-show (hoặc PATCH status=NO_SHOW) | 200; appointment.status=NO_SHOW | Đóng lịch hẹn |
| 3 | Lễ tân (recept_anh) | Kiểm tra không có visit phát sinh | GET /api/v1/visits?appointment_id={id} | rỗng (không có visit) | Không vào hàng đợi |
| 4 | Lễ tân (recept_anh) | (Tùy chọn) Đặt lại lịch mới | POST /api/v1/appointments | 201; lịch mới SCHEDULED | Slot cũ đã giải phóng |

- **Kết quả cuối:** Appointment.status=NO_SHOW; không có Visit/Invoice/StockMovement; slot lịch được giải phóng để đặt lại; audit ghi đánh dấu no-show.
- **Điểm kiểm chứng (assertions):**
  - Không có bản ghi Visit liên kết appointment.
  - Không thể đánh dấu NO_SHOW cho appointment đã CANCELLED hoặc đã có visit COMPLETED → 409.
  - Báo cáo/thống kê đếm no-show tăng 1 (nếu có metric).
  - RLS: lễ tân clinic khác không thấy/không đổi appointment DEMO → 404.
- **Liên kết function:** APPT-001 (tạo hẹn), APPT-008 (NO_SHOW tracking — có job `auto_no_show_appointments`), APPT-007 (cancel — để so sánh nhánh), VIS-004 (NO_SHOW status visit, nếu visit đã tạo), AUDIT. (Lưu ý: APPT-006 Reschedule là GAP — chưa có route đổi giờ.)

---

### SC-EXC-04 — Thuốc hết tồn / không đủ batch khi Dược sĩ cấp phát → xử lý cấp phát thiếu

- **Mục tiêu:** Đơn yêu cầu N viên nhưng tổng tồn các batch < N (hoặc batch FEFO không đủ). Dược sĩ không thể dispense đủ; hệ thống chặn over-dispense, cho phép cấp phát một phần (partial) hoặc báo thiếu để xử lý, không trừ âm tồn.
- **Vai trò & tài khoản:**
  - Bác sĩ — `dr_nguyen / Doctor@1234` (kê đơn N viên, hoàn tất khám).
  - Thu ngân — `cashier_em / Cashier@1234` (thu tiền để vào hàng đợi cấp phát).
  - Dược sĩ — `pharm_cuong / Pharm@1234` (cấp phát theo FEFO; gặp thiếu tồn).
- **Tiền điều kiện:**
  - Thuốc in-house có tổng tồn khả dụng cố tình thấp hơn đơn (vd đơn 50 viên, tổng tồn 30 viên trên 2 batch).
  - Visit đã WAITING_PAYMENT (hoặc WAITING_PHARMACY) có prescription in-house.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Bác sĩ (dr_nguyen) | Kê đơn 50 viên thuốc in-house, hoàn tất khám | POST /api/v1/visits/{id}/prescriptions ; POST /visits/{id}/complete | 201; visit.status=WAITING_PHARMACY (rồi WAITING_PAYMENT) | Chờ thu tiền |
| 2 | Thu ngân (cashier_em) | Lập invoice + thu đủ tiền | POST /api/v1/invoices ; POST /invoices/{id}/payments | invoice.status=PAID | Vào hàng đợi cấp phát |
| 3 | Dược sĩ (pharm_cuong) | Xem hàng đợi cấp phát | GET /api/v1/pharmacy/dispense-queue | thấy đơn 50 viên; cảnh báo tồn 30 | Chuẩn bị cấp phát |
| 4 | Dược sĩ (pharm_cuong) | THỬ cấp phát đủ 50 viên | POST /api/v1/pharmacy/dispense {qty=50} | **400/409 Insufficient stock** (chặn over-dispense) | Tồn không bị trừ âm |
| 5 | Dược sĩ (pharm_cuong) | Cấp phát một phần 30 viên theo FEFO (batch hết hạn gần trước) | POST /api/v1/pharmacy/dispense {qty=30, batches=[FEFO]} | 200; dispensed=30; còn thiếu 20; StockMovement -30 | Cấp phát thiếu, chờ bổ sung |
| 6 | Dược sĩ (pharm_cuong) | Kiểm tra trạng thái đơn còn thiếu | GET /api/v1/visits/{id}/prescriptions | dispensed_qty=30; remaining=20; status=PARTIALLY_DISPENSED | Ghi nhận thiếu |

- **Kết quả cuối:** Đơn ở trạng thái PARTIALLY_DISPENSED (cấp phát 30/50); StockMovement loại dispense = 30; tồn khả dụng về 0 cho batch FEFO đã dùng; không có chuyển động trừ âm; visit CHƯA COMPLETED cho tới khi giải quyết phần thiếu (hoặc đóng đơn theo policy). Audit ghi partial dispense.
- **Điểm kiểm chứng (assertions):**
  - Bước 4: dispense vượt tồn bị từ chối, KHÔNG tạo StockMovement, tồn không đổi.
  - Bước 5: StockMovement trừ đúng số khả dụng; FEFO chọn batch hết hạn sớm trước; không trừ batch xa hạn khi còn batch gần hạn.
  - Tồn physical sau cấp phát = physical_trước − 30; không bao giờ < 0.
  - Visit không tự chuyển COMPLETED khi còn thiếu thuốc.
  - RLS: dược sĩ clinic khác không thấy hàng đợi DEMO.
- **Liên kết function:** PHRM-005 (partial dispense / out of stock — kiểm chứng all-or-nothing vs partial), PHRM-008 (cảnh báo thiếu hàng), PHRM-003 (lot selection FEFO), PHRM-004 (multi-lot dispense), PHRM-006 (stock auto-decrement atomic, không âm), PHRM-002 (dispense confirm), RX-015 (reserve), BILL-013 (partial), AUDIT (PHRM-009 dispense audit).

---

### SC-EXC-05 — Sửa đơn thuốc sau khi Bác sĩ hoàn tất khám nhưng TRƯỚC khi cấp phát

- **Mục tiêu:** Bác sĩ hoàn tất khám (visit WAITING_PHARMACY/WAITING_PAYMENT) rồi cần sửa đơn (đổi liều / thêm-bớt thuốc) trước khi dược sĩ cấp phát. Việc sửa phải điều chỉnh reservation tồn tương ứng và đồng bộ lại invoice (nếu invoice đã lập với in-house items) trước khi PAID/cấp phát.
- **Vai trò & tài khoản:**
  - Bác sĩ — `dr_nguyen / Doctor@1234` (kê đơn ban đầu, sau đó sửa đơn).
  - Dược sĩ — `pharm_cuong / Pharm@1234` (xác nhận đơn đã đổi khi cấp phát).
  - (Negative) Y tá — `nurse_lan / Nurse@1234` (thử sửa đơn → 403, không có `prescription.write`).
- **Tiền điều kiện:**
  - Thuốc A (in-house) tồn Q0=100; thuốc B (in-house) tồn=100.
  - Visit đã IN_CONSULTATION của dr_nguyen.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Bác sĩ (dr_nguyen) | Kê đơn ban đầu: A=30 viên | POST /api/v1/visits/{id}/prescriptions | 201; reserve A=30 (available A=70) | Đơn v1 |
| 2 | Bác sĩ (dr_nguyen) | Hoàn tất khám | POST /api/v1/visits/{id}/complete | visit.status=WAITING_PHARMACY/WAITING_PAYMENT | Chờ thu tiền |
| 3 | Y tá (nurse_lan) | THỬ sửa đơn (không có quyền) | PATCH /api/v1/visits/{id}/prescriptions/{rxId} | **403 Forbidden** (thiếu `prescription.write`) | Đơn không đổi |
| 4 | Bác sĩ (dr_nguyen) | Sửa đơn TRƯỚC cấp phát: giảm A xuống 20, thêm B=10 | PUT/PATCH /api/v1/visits/{id}/prescriptions/{rxId} ; POST thêm dòng B | 200; reserve A=20 (available A=80), reserve B=10 (available B=90) | Đơn v2 |
| 5 | Bác sĩ (dr_nguyen) | Kiểm tra reservation cập nhật | GET /api/v1/inventory/items/A,B | A reserved=20, B reserved=10 | Tồn reserve đúng đơn mới |
| 6 | Dược sĩ (pharm_cuong) | Cấp phát theo đơn v2 (A=20, B=10) | POST /api/v1/pharmacy/dispense | 200; dispensed A=20, B=10; StockMovement đúng | Khớp đơn đã sửa |

- **Kết quả cuối:** Đơn phản ánh phiên bản đã sửa (A=20, B=10); reservation tồn được điều chỉnh (trả lại 10 viên A, reserve mới 10 viên B); dược sĩ cấp phát đúng đơn mới; audit ghi sửa đơn (ai sửa, đổi gì); nếu invoice đã lập với in-house cũ → invoice được cập nhật lại trước khi PAID.
- **Điểm kiểm chứng (assertions):**
  - Reservation thay đổi đúng: giảm A từ 30→20 phải release 10 viên A về available; thêm B reserve 10.
  - KHÔNG cho sửa đơn SAU khi đã dispense dòng tương ứng (chỉ sửa khi chưa cấp phát) → 409 nếu vi phạm.
  - Bước 3: Y tá / Lễ tân / Dược sĩ KHÔNG sửa được đơn (`prescription.write` chỉ Admin + Doctor) → 403.
  - Invoice (nếu đã tạo) reflect đúng số tiền thuốc in-house sau sửa; không cho PAID với total lệch.
  - RLS: bác sĩ clinic khác không sửa được đơn DEMO → 404.
- **Liên kết function:** RX-011 (edit đơn trước dispense / amend), RX-015 (reserve stock — điều chỉnh reserve khi sửa), RX-012 (cancel đơn trước dispense), RX-001 (tạo đơn), RBAC (`prescription.write` chỉ Admin+Doctor), PHRM-011 (auto add to invoice — đồng bộ giá), PHRM-002/005 (dispense theo đơn đã sửa), AUDIT.

---

### SC-EXC-06 — Thanh toán nhiều đợt: trả thiếu (partial) → trả tiếp đến khi đủ

- **Mục tiêu:** Hóa đơn được thanh toán làm nhiều đợt (multi-payment). Lần 1 trả thiếu → invoice PARTIALLY_PAID; lần 2 trả phần còn lại → PAID. Xác minh tổng paid và remaining đúng, không cho thu vượt tổng.
- **Vai trò & tài khoản:**
  - Bác sĩ — `dr_nguyen / Doctor@1234` (đưa visit tới WAITING_PAYMENT).
  - Thu ngân — `cashier_em / Cashier@1234` (thu nhiều đợt).
- **Tiền điều kiện:**
  - Visit WAITING_PAYMENT có dịch vụ tổng tiền vd 500.000đ.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Bác sĩ (dr_nguyen) | Hoàn tất khám (đã có dịch vụ) | POST /api/v1/visits/{id}/complete | visit.status=WAITING_PAYMENT | Chờ thu tiền |
| 2 | Thu ngân (cashier_em) | Lập invoice | POST /api/v1/invoices {visit_id} | 201; invoice.total=500.000; status=UNPAID | Chờ thanh toán |
| 3 | Thu ngân (cashier_em) | Thu đợt 1: 200.000 (CASH) | POST /api/v1/invoices/{id}/payments {amount=200000, payment_method="cash"} | 201; paid=200.000; remaining=300.000; status=PARTIALLY_PAID | Còn nợ |
| 4 | Thu ngân (cashier_em) | THỬ thu vượt: 400.000 (còn nợ 300.000) | POST /api/v1/invoices/{id}/payments {amount=400000, payment_method="cash"} | **400/409 Overpayment** (chặn thu vượt) | Không nhận dư |
| 5 | Thu ngân (cashier_em) | Thu đợt 2 đúng phần còn lại: 300.000 (CARD) | POST /api/v1/invoices/{id}/payments {amount=300000, payment_method="card"} | 201; paid=500.000; remaining=0; status=PAID | Đã đủ |
| 6 | Thu ngân (cashier_em) | Kiểm tra danh sách payment | GET /api/v1/invoices/{id}/payments | 2 bản ghi (200k CASH + 300k CARD) | Đối soát |

- **Kết quả cuối:** Invoice.status=PAID; có 2 Payment records (tổng = total); remaining=0; visit có thể tiến tới cấp phát/COMPLETED. Audit/payment log đầy đủ.
- **Điểm kiểm chứng (assertions):**
  - Sau đợt 1: status=PARTIALLY_PAID; remaining = total − 200.000 chính xác.
  - Bước 4: thu vượt remaining bị từ chối, KHÔNG tạo payment.
  - Sau đợt 2: paid_total = total đúng đến đồng; status=PAID; không cho thanh toán thêm trên hóa đơn PAID → 409.
  - Mỗi payment lưu method riêng (CASH/CARD); tổng cộng khớp.
  - RLS: thu ngân clinic khác không thấy invoice DEMO.
- **Liên kết function:** BILL-013 (partial payment), BILL-005 (multi-payment method — guard tổng vượt total, xem TC-BILL-016), BILL-014 (outstanding balance / theo dõi nợ), BILL-006/007/008/009 (cash/card/QR/bank), AUDIT.

---

### SC-EXC-07 — Điều chỉnh / giảm giá hóa đơn (discount) trước khi thu tiền

- **Mục tiêu:** Áp dụng giảm giá (discount %/số tiền) lên hóa đơn UNPAID làm total giảm; xác minh ai có quyền chỉnh giá, total tái tính đúng, và sau khi PAID không cho đổi giá. Discount lớn/vượt ngưỡng cần Admin duyệt.
- **Vai trò & tài khoản:**
  - Bác sĩ — `dr_nguyen / Doctor@1234` (đưa visit tới WAITING_PAYMENT).
  - Thu ngân — `cashier_em / Cashier@1234` (lập invoice, áp discount trong ngưỡng cho phép).
  - Admin — `admin / Demo@1234` (duyệt discount vượt ngưỡng / điều chỉnh tài chính).
- **Tiền điều kiện:**
  - Visit WAITING_PAYMENT có dịch vụ tổng 1.000.000đ.
  - Cấu hình ngưỡng discount (vd non-admin ≤10%, vượt cần Admin) — đối chiếu settings.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Bác sĩ (dr_nguyen) | Hoàn tất khám | POST /api/v1/visits/{id}/complete | visit.status=WAITING_PAYMENT | Chờ thu tiền |
| 2 | Thu ngân (cashier_em) | Lập invoice | POST /api/v1/invoices | invoice.total=1.000.000; status=UNPAID | Chờ áp giá |
| 3 | Thu ngân (cashier_em) | Áp discount 100.000 (10% của 1.000.000, trong ngưỡng) | PATCH /api/v1/invoices/{id} {discount_amount=100000, discount_reason="..."} | 200; discount=100.000; total=900.000 | Giá điều chỉnh |
| 4 | Thu ngân (cashier_em) | THỬ áp discount 500.000 (50%, vượt ngưỡng) | PATCH /api/v1/invoices/{id} {discount_amount=500000, discount_reason="..."} | **403/422 Requires approval** | Cần Admin |
| 5 | Admin (admin) | Duyệt/áp discount 500.000 kèm lý do | PATCH /api/v1/invoices/{id} {discount_amount=500000, discount_reason="...", approved_by=admin} | 200; total=500.000; audit ghi approver | Giá đặc biệt |
| 6 | Thu ngân (cashier_em) | Thu tiền theo total mới | POST /api/v1/invoices/{id}/payments {amount=500000, payment_method="cash"} | invoice.status=PAID | Thanh toán |
| 7 | Thu ngân (cashier_em) | THỬ đổi discount sau khi PAID | PATCH /api/v1/invoices/{id} {discount_amount=0} | **409 Locked** (không sửa khi PAID) | Khóa giá |

- **Kết quả cuối:** Invoice.total phản ánh đúng discount đã duyệt; payment thu theo total mới; audit ghi rõ discount + người duyệt; hóa đơn PAID khóa không cho chỉnh giá.
- **Điểm kiểm chứng (assertions):**
  - Total tái tính chính xác: total = subtotal − discount; không âm.
  - Discount vượt ngưỡng do non-admin → bị chặn (403/422), chỉ Admin duyệt được; audit lưu approver + reason.
  - Sau PAID: mọi chỉnh giá → 409 (immutable).
  - Báo cáo tài chính (`report.financial` chỉ Admin) phản ánh đúng discount; non-admin gọi report.financial → 403.
  - RLS: clinic khác không chỉnh được invoice DEMO.
- **Liên kết function:** BILL-011 (discount % hoặc số tiền), BILL-012 (VAT theo config — lưu ý DRIFT hardcode 0), BILL-004 (sửa line item chỉ khi DRAFT — khóa sau ISSUED/PAID), RBAC (`report.financial` chỉ Admin), AUDIT.

---

### SC-EXC-08 — Đo lại sinh hiệu — 1 visit nhiều lần đo (re-vital)

- **Mục tiêu:** Trong cùng 1 visit, y tá đo sinh hiệu lần 1, sau đó đo lại lần 2 (vd huyết áp cao bất thường cần đo lại). Hệ thống lưu nhiều bản ghi VisitVitals (lịch sử) hoặc cập nhật bản mới nhất; bác sĩ thấy dữ liệu mới nhất. Dược sĩ/Lễ tân không có `vital.write`.
- **Vai trò & tài khoản:**
  - Lễ tân — `recept_anh / Recept@1234` (tạo visit).
  - Y tá — `nurse_lan / Nurse@1234` (đo lần 1 và đo lại lần 2).
  - Bác sĩ — `dr_nguyen / Doctor@1234` (xem vitals mới nhất khi khám).
  - (Negative) Dược sĩ — `pharm_cuong / Pharm@1234` (thử ghi vitals → 403).
- **Tiền điều kiện:**
  - Dynamic vital form đã cấu hình (BP, mạch, nhiệt độ, SpO2...).
  - BN có sẵn.
- **Các bước (bảng):**

| # | Vai trò (tài khoản) | Hành động | API/Endpoint gợi ý | Kết quả mong đợi | Bàn giao trạng thái |
|---|---|---|---|---|---|
| 1 | Lễ tân (recept_anh) | Tạo visit | POST /api/v1/visits | 201; visit.status=WAITING_VITAL | Vào hàng đợi |
| 2 | Y tá (nurse_lan) | Đo lần 1: BP 160/100, mạch 95 | POST /api/v1/visits/{id}/vitals | 201; vitals#1 lưu; measured_at=t1; visit.status=VITAL_DONE | BN quay ghế chờ (is_returning_patient=true) |
| 3 | Dược sĩ (pharm_cuong) | THỬ ghi vitals (không có quyền) | POST /api/v1/visits/{id}/vitals | **403 Forbidden** (thiếu `vital.write`) | Không ảnh hưởng |
| 4 | Y tá (nurse_lan) | Đo LẠI lần 2: BP 135/85, mạch 80 | POST /api/v1/visits/{id}/vitals (hoặc PUT) | 201/200; vitals#2 lưu; measured_at=t2>t1 | Có 2 lần đo |
| 5 | Y tá (nurse_lan) | Xem lịch sử đo của visit | GET /api/v1/visits/{id}/vitals | trả 2 bản ghi (hoặc latest + history) | Đối chiếu |
| 6 | Bác sĩ (dr_nguyen) | Gọi BN, xem vitals mới nhất | POST /visits/next ; GET /visits/{id}/vitals?latest=true | visit.status=IN_CONSULTATION; thấy BP 135/85 (lần 2) | Khám với dữ liệu mới |

- **Kết quả cuối:** Visit có ≥2 bản ghi VisitVitals theo thời gian (hoặc 1 latest + history); bác sĩ thấy số đo mới nhất; trạng thái visit không bị reset bởi đo lại (vẫn theo state machine bình thường); audit ghi 2 lần đo bởi nurse_lan.
- **Điểm kiểm chứng (assertions):**
  - Hai bản ghi vitals tồn tại với measured_at khác nhau (t2 > t1) HOẶC latest cập nhật + giữ history; không mất dữ liệu lần 1.
  - Bước 3: 403 cho pharmacist; không tạo bản ghi vitals.
  - Bác sĩ khi gọi BN nhận đúng số đo mới nhất.
  - Lễ tân (`recept_anh`) cũng KHÔNG có `vital.write` (theo ma trận) → thử POST vitals → 403 (assertion phụ tùy chọn).
  - RLS: y tá clinic khác không ghi vitals cho visit DEMO → 404.
- **Liên kết function:** VTL-013 (vital input by nurse — nurse fill, doctor verify), VTL-002 (dynamic field schema JSONB), VTL-008 (schema versioning — không phá visit cũ), VTL-014 (alert thresholds — BP 160/100 cảnh báo), VIS-003 (state machine: WAITING_VITAL/VITAL_DONE), RBAC (`vital.write` chỉ Admin/Doctor/Nurse), AUDIT. ⚠️ Module VTL chưa ship → forward-looking.

---

## Ghi chú truy vết & cần xác nhận khi chạy

- **Đồng bộ payload BE (2026-05-31, theo `handoff/scenario-review.md`):**
  - Payment: field `payment_method` (lowercase `cash|card|transfer|momo|vnpay|other`), KHÔNG phải `method=CASH`.
  - Hủy visit: field bắt buộc `cancel_reason` (min 3 ký tự), KHÔNG phải `reason`.
  - Discount: schema BE dùng `discount_amount` + `discount_reason` (bắt buộc khi amount>0); KHÔNG có `discount_percent` — đã đổi sang số tiền tuyệt đối. ⚠️ Lưu ý discount trong `invoice_schemas.py` ở cấp **line item**; nếu BE chưa hỗ trợ discount cấp invoice thì map sang line discount khi tự động hóa.
  - Void / Refund: field `reason` (đã đúng, giữ nguyên).
- Endpoint là gợi ý dựa trên BA §4.5/§4.6 + ma trận RBAC §13.6; cần đối chiếu OpenAPI thực tế (đặc biệt: tên route void/cancel/no-show/discount, cơ chế reservation release, partial dispense, multi-payment overpay guard).
- Các quy tắc tài chính cần xác nhận với functional design: hành vi của visit sau khi void invoice đã PAID (có quay lại WAITING_PAYMENT không), ngưỡng discount theo vai trò, và trạng thái đơn khi cấp phát thiếu (PARTIALLY_DISPENSED vs giữ chờ).
- Mã function (VIS-/RX-/BILL-/PHRM-/RBAC-/APPT-/AUDIT-) đặt theo quy ước để truy vết về catalog functional/non-functional cùng TASK-052; khi catalog functional sẵn sàng cần map lại đúng số hiệu.
- Mọi kịch bản đều có ít nhất 1 assertion RLS đa tenant và (với case quyền) 1 assertion 403 phân quyền chéo theo BA §13.6.
