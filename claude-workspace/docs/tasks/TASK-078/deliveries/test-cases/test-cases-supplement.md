# TASK-078 — Test Cases Bổ sung (Supplement)

**Ngày tạo:** 2026-06-10  
**Phạm vi:** Các luồng chưa được bao phủ trong lần test đầu (bỏ BHYT)  
**Trạng thái:** Chưa chạy — cần review trước khi execute

---

## GROUP A — Hủy visit / Cancel

### TC-31: Lễ tân hủy visit đang WAITING

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **Tiền điều kiện** | Có visit trạng thái WAITING |
| **Input** | Mở visit → click "Hủy lượt khám" → nhập lý do: "Bệnh nhân rời đi" |
| **API** | `POST /api/v1/visits/{id}/cancel` với `cancel_reason` |
| **Mong muốn** | Visit → CANCELLED, lý do được lưu, không còn trong hàng chờ |
| **Tình huống** | Happy path — cancel early |

---

### TC-32: Bác sĩ hủy visit đang IN_PROGRESS

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor |
| **Tiền điều kiện** | Visit đang IN_PROGRESS (bác sĩ đã bắt đầu khám) |
| **Input** | Trong trang khám → "Hủy lượt khám" → lý do: "Bệnh nhân từ chối khám" |
| **Mong muốn** | Visit → CANCELLED, trả về hàng chờ trống, không tạo hóa đơn |
| **Tình huống** | Cancel mid-flow |

---

### TC-33: Hủy visit khi đã AWAITING_PAYMENT (sau khi bác sĩ hoàn thành)

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist hoặc Admin |
| **Tiền điều kiện** | Visit trạng thái AWAITING_PAYMENT, chưa có hóa đơn |
| **Input** | Hủy với lý do: "Bệnh nhân không thanh toán, rời đi" |
| **Mong muốn** | Visit → CANCELLED; nếu đã có HĐ DRAFT → HĐ cũng bị void |
| **Biên giới** | Nếu HĐ đã ISSUED → không cho hủy, yêu cầu void HĐ trước |
| **Tình huống** | Late cancel — edge case phổ biến |

---

## GROUP B — Void Invoice / Hoàn tiền

### TC-34: Thu ngân void hóa đơn DRAFT

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Cashier |
| **Tiền điều kiện** | HĐ trạng thái DRAFT (chưa phát hành) |
| **Input** | Mở HĐ → "Hủy hóa đơn" / "Void" |
| **API** | `DELETE /api/v1/billing/invoices/{id}` hoặc `POST /void` |
| **Mong muốn** | HĐ bị xóa hoặc chuyển VOID, visit quay lại AWAITING_PAYMENT |
| **Tình huống** | Happy path — sai số tiền, cần tạo lại |

---

### TC-35: Void hóa đơn ISSUED trước khi thu tiền

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Cashier |
| **Tiền điều kiện** | HĐ trạng thái ISSUED (đã phát hành, chưa PAID) |
| **Input** | Click "Void hóa đơn" → nhập lý do |
| **Mong muốn** | HĐ → VOID, visit vẫn ở AWAITING_PAYMENT (có thể tạo HĐ mới) |
| **Negative** | Không cho void HĐ đã PAID — phải tạo credit note |
| **Tình huống** | Sửa lỗi sau khi phát hành |

---

## GROUP C — Tái khám / Lịch sử bệnh nhân

### TC-36: Bác sĩ xem lịch sử khám cũ của bệnh nhân

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor |
| **Tiền điều kiện** | BN đã có ít nhất 1 lượt khám trước đó (completed) |
| **Input** | Trong trang khám → tab "Lịch sử" hoặc `#/patients/{id}` |
| **Mong muốn** | Hiển thị danh sách lượt khám cũ, click vào xem được SOAP + chẩn đoán + đơn thuốc |
| **Tình huống** | Read-only history view |

---

### TC-37: Lễ tân tạo lượt tái khám (follow-up)

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **Tiền điều kiện** | BN đã có lượt khám trước COMPLETED |
| **Input** | Tạo walk-in visit với `is_returning=true`, `is_follow_up=true` |
| **Mong muốn** | Visit tạo đúng flag, hiển thị badge "Tái khám" trong hàng chờ |
| **Verify** | API response có `is_returning=true`, `is_follow_up=true` |
| **Tình huống** | Returning patient |

---

## GROUP D — Đặt lịch hẹn (Appointment)

### TC-38: Lễ tân tạo appointment cho bệnh nhân

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **URL** | `#/appointments` → "Đặt lịch mới" |
| **Input** | BN: Trần Thị TC78, Bác sĩ: dr_nguyen, Ngày: ngày mai, Giờ: 09:00, Lý do: Tái khám |
| **Mong muốn** | Appointment tạo thành công, trạng thái SCHEDULED, hiển thị trong lịch |
| **Tình huống** | Happy path |

---

### TC-39: BN check-in từ appointment đã đặt

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **Tiền điều kiện** | Appointment trạng thái SCHEDULED |
| **Input** | Tìm appointment → click "Check-in" |
| **Mong muốn** | Appointment → CHECKED_IN, tạo visit WAITING gắn với appointment |
| **Verify** | Visit có `appointment_id` không null |
| **Tình huống** | Happy path check-in |

---

### TC-40: Convert appointment → visit (qua trang khám)

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor |
| **Tiền điều kiện** | BN đã check-in, visit WAITING từ appointment |
| **Input** | Bác sĩ bắt đầu khám từ queue |
| **Mong muốn** | Luồng khám bình thường; visit detail hiển thị "Đến từ lịch hẹn" |
| **Tình huống** | Appointment → visit full flow |

---

### TC-41: Hủy appointment (no-show)

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **Tiền điều kiện** | Appointment SCHEDULED, BN không đến |
| **Input** | Mở appointment → "Hủy" → lý do: "Bệnh nhân không đến (no-show)" |
| **Mong muốn** | Appointment → CANCELLED hoặc NO_SHOW, không tạo visit |
| **Tình huống** | No-show — xảy ra ~20% lịch hẹn thực tế |

---

## GROUP E — Concurrent / Race Condition

### TC-42: 2 bác sĩ cùng gọi "Gọi bệnh nhân tiếp theo"

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor A + Doctor B (2 session song song) |
| **Tiền điều kiện** | Có đúng 1 BN đang WAITING trong hàng chờ |
| **Input** | Dr A và Dr B đều click "Gọi bệnh nhân tiếp theo" gần như cùng lúc |
| **API** | `POST /api/v1/visits/call-next` (atomic) |
| **Mong muốn** | Chỉ 1 bác sĩ nhận được BN (HTTP 200), bác sĩ còn lại nhận `{"reason": "no_waiting_visits"}` |
| **Cơ chế** | `SELECT ... FOR UPDATE SKIP LOCKED` hoặc optimistic lock |
| **Tình huống** | Race condition — critical cho phòng khám đông BN |

---

## GROUP F — Tồn kho thuốc

### TC-43: Kê đơn thuốc in_house khi đủ tồn kho

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor |
| **Tiền điều kiện** | Có thuốc trong kho với `dispense_source='in_house'`, tồn kho > 0 |
| **Input** | Kê đơn với `dispense_source='in_house'` |
| **Mong muốn** | Đơn lưu thành công, dược sĩ thấy đơn trong pending queue |
| **So sánh** | Khác với TC-15 (external) — in_house đưa vào queue phát thuốc của dược sĩ |
| **Tình huống** | Happy path — kho nội bộ |

---

### TC-44: Cảnh báo khi thuốc gần hết / hết tồn kho

| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor (kê đơn) + Admin (quản lý kho) |
| **Tiền điều kiện** | Có thuốc với tồn kho = 0 hoặc < ngưỡng cảnh báo |
| **Input** | Bác sĩ thêm thuốc hết kho vào đơn |
| **Mong muốn** | Hệ thống cảnh báo "Thuốc X hiện không đủ tồn kho" — không block kê đơn nhưng warn |
| **Admin view** | Trang quản lý kho hiển thị danh sách thuốc sắp hết |
| **Tình huống** | Stock alert |

---

## Tóm tắt

| Group | TC | Độ ưu tiên | Ghi chú |
|-------|-----|-----------|---------|
| A — Cancel visit | TC-31, 32, 33 | 🔴 Cao | Xảy ra hàng ngày, ảnh hưởng hàng chờ |
| B — Void invoice | TC-34, 35 | 🔴 Cao | Sai hóa đơn phổ biến |
| C — Tái khám | TC-36, 37 | 🟡 Trung bình | ~60% lượt khám thực tế là BN cũ |
| D — Appointment | TC-38, 39, 40, 41 | 🟡 Trung bình | 40-60% lượt đến từ lịch hẹn |
| E — Concurrent | TC-42 | 🟡 Trung bình | Cần môi trường 2 session song song |
| F — Tồn kho | TC-43, 44 | 🟠 Thấp hơn | Phụ thuộc có nhập kho demo không |

**Tổng bổ sung: 14 TC**  
**Tổng cộng sau bổ sung: 33 + 14 = 47 TC** (bỏ BHYT)
