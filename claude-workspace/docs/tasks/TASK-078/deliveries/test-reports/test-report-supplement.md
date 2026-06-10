# Test Report Supplement — TASK-078 (14 TC Bổ Sung)

**Ngày thực hiện:** 2026-06-10  
**Phạm vi:** 14 TC bổ sung từ `test-cases-supplement.md` (bỏ BHYT)  
**Môi trường:** FE localhost:1420 | BE Docker localhost:8002  

---

## Tóm tắt

| Hạng mục | Số lượng |
|----------|---------|
| Tổng TC bổ sung | 14 |
| PASS | 14 |
| FAIL | 0 |
| Gap phát hiện | 2 (FE thiếu, BE OK) |

---

## Kết quả chi tiết

### Group A — Cancel visit

| TC | Mô tả | Kết quả | Ghi chú |
|----|-------|---------|---------|
| TC-31 | Cancel WAITING visit | ✅ PASS | HTTP 200, status→CANCELLED, cancel_reason lưu đúng |
| TC-32 | Cancel IN_PROGRESS visit | ✅ PASS | HTTP 200, status→CANCELLED |
| TC-33 | Cancel AWAITING_PAYMENT visit | ✅ PASS | HTTP 200, status→CANCELLED |

**FE Gap (BUG-S-001):** Không có cancel button trong ConsultationPage hoặc QueuePage. BE endpoint `/visits/{id}/cancel` hoạt động đúng nhưng FE chưa expose cho user.

---

### Group B — Void Invoice

| TC | Mô tả | Kết quả | Ghi chú |
|----|-------|---------|---------|
| TC-34 | Void DRAFT invoice | ✅ PASS | BE trả HTTP 400: "Cannot void invoice with status 'draft'. Only {'partially_paid', 'issued'} can be voided." FE đúng — không show void button cho DRAFT. |
| TC-35 | Void ISSUED invoice | ✅ PASS | DRAFT→add line→submit (ISSUED)→void. Status chuyển thành "void". FE hiển thị "Đã hủy". |

---

### Group C — Tái khám / Lịch sử BN

| TC | Mô tả | Kết quả | Ghi chú |
|----|-------|---------|---------|
| TC-36 | Xem lịch sử khám BN | ✅ PASS | Tab "Lịch sử khám" trong PatientDetailPage hiển thị danh sách visit cũ (số phiếu, ngày, trạng thái, bác sĩ). |
| TC-37 | Tạo tái khám (is_returning=true) | ✅ PASS | Visit tạo với is_returning=true, is_follow_up=true. Badge "Tái khám" hiển thị trong QueueBoardPage. |

---

### Group D — Appointment

| TC | Mô tả | Kết quả | Ghi chú |
|----|-------|---------|---------|
| TC-38 | Tạo appointment | ✅ PASS | BE: POST /appointments → scheduled. Lưu ý: field là `scheduled_at` (ISO datetime+TZ), không phải appointment_date+time tách rời. |
| TC-39 | Confirm appointment | ✅ PASS | POST /appointments/{id}/confirm → confirmed |
| TC-40 | Check-in → tạo visit | ✅ PASS | POST /appointments/{id}/check-in → checked_in + visit_id trả về |
| TC-41 | Hủy appointment (no-show) | ✅ PASS | POST /appointments/{id}/cancel với cancel_reason → cancelled |

**FE Gap (BUG-S-002):** AppointmentPage chỉ hiển thị calendar/booking slots. Không có UI quản lý appointment (confirm, check-in, cancel). FE có note "Beta — đang chờ tích hợp BE (TASK-008)". BE đầy đủ.

---

### Group E — Concurrent

| TC | Mô tả | Kết quả | Ghi chú |
|----|-------|---------|---------|
| TC-42 | 3 concurrent call-next requests | ✅ PASS | Mỗi request nhận 1 visit khác nhau (68c21d09, 21e1b57a, 17b72927). SELECT...FOR UPDATE SKIP LOCKED hoạt động đúng — không có race condition/duplicate. |

---

### Group F — Pharmacy Inventory

| TC | Mô tả | Kết quả | Ghi chú |
|----|-------|---------|---------|
| TC-43 | Kê đơn in_house → pharmacy queue | ✅ PASS | 19 đơn in_house trong pending-dispense queue. FE hiển thị "Quá giờ (19)", nút "Cấp phát" đúng. |
| TC-44 | Filter "Sắp hết" tồn kho | ✅ PASS | Filter hoạt động, trả "Không có mặt hàng nào" khi không có thuốc gần hết — đúng với tồn kho hiện tại (tất cả > reorder_min). |

---

## Gaps phát hiện (không block BE, cần FE)

### BUG-S-001 — Thiếu cancel visit button trên FE

| Thuộc tính | Nội dung |
|-----------|---------|
| **Severity** | Medium |
| **Repo** | `clinic-cms-web` (Frontend) |
| **Mô tả** | BE endpoint `POST /visits/{id}/cancel` hoạt động đúng (HTTP 200, trả CANCELLED). FE không có button "Hủy lượt khám" trong ConsultationPage (`#/doctor/visits/:id`) hoặc QueuePage. Lễ tân/bác sĩ không thể hủy visit qua UI. |
| **Workaround** | Gọi API trực tiếp |
| **Đề xuất fix** | Thêm nút "Hủy lượt khám" trong ConsultationPage (tab header) với modal nhập lý do. |

---

### BUG-S-002 — Appointment management UI chưa hoàn chỉnh

| Thuộc tính | Nội dung |
|-----------|---------|
| **Severity** | Medium |
| **Repo** | `clinic-cms-web` (Frontend) |
| **Mô tả** | AppointmentPage chỉ hiển thị calendar booking slots. Không có UI để: confirm, check-in, cancel appointment. FE có note "Beta — đang chờ tích hợp BE (TASK-008)". BE đã có đầy đủ 4 endpoints. |
| **Workaround** | Gọi API trực tiếp |
| **Đề xuất fix** | Implement TASK-008 — appointment management list view với actions. |

---

## Tổng kết coverage

| Nhóm | BE | FE | Kết quả |
|------|----|----|---------|
| Cancel visit | ✅ Full | ❌ Thiếu button | PASS (BE), Gap (FE) |
| Void invoice | ✅ Full | ✅ Full | PASS |
| Tái khám / Lịch sử | ✅ Full | ✅ Full | PASS |
| Appointment | ✅ Full | ⚠️ Beta/stub | PASS (BE), Gap (FE) |
| Concurrent call-next | ✅ Full | ✅ Full | PASS |
| Pharmacy inventory | ✅ Full | ✅ Full | PASS |

**Kết luận:** BE coverage 100% cho tất cả 14 scenarios. FE có 2 gaps (cancel visit button, appointment management UI) — cả 2 đều có ticket tồn đọng (TASK-008).
