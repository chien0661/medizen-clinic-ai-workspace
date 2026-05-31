# Test Case Catalog — BILL · Thanh toán & Hóa đơn

**Nguồn:** function_list_data.py (group BILL, dòng 1076–1148) + clinic_management_function_list.md (dòng 355–377) + system_design/BA.
**Phạm vi:** 23 functions (BILL-001 … BILL-023).  **Tổng test case:** 78.  **Ngày:** 2026-05-30.

> **Ghi chú nguồn & coverage:** Tại thời điểm soạn, **toàn bộ** function BILL trong nguồn ở trạng thái **TODO** (BILL-001…BILL-019, phase v1, TASK-013) hoặc **IDEA** (BILL-020…BILL-023, phase v2). Module thanh toán/hóa đơn **chưa được ship** trong `clinic-cms-merge/app` và **không có** test file BILL trong `clinic-cms-merge/tests` hay trong các catalog TASK-001…TASK-051. Do đó coverage hiện tại của tất cả test case là **MISSING** — đây là bộ test case "to-build" làm chuẩn nghiệm thu cho TASK-013 khi triển khai. Khi code được ship, cập nhật cột Coverage và điền `test_file::test_name`.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| BILL-001 | Auto-gen invoice (visit COMPLETED + medicine DISPENSED) | ⬜ TODO | TC-BILL-001, TC-BILL-002, TC-BILL-003, TC-BILL-004 | MISSING |
| BILL-002 | Auto-gen invoice number (HD-2026-04-30-0001) | ⬜ TODO | TC-BILL-005, TC-BILL-006, TC-BILL-007 | MISSING |
| BILL-003 | Manual invoice (tạo HĐ ngoài visit / bán lẻ) | ⬜ TODO | TC-BILL-008, TC-BILL-009, TC-BILL-010 | MISSING |
| BILL-004 | Add/remove line item (sửa HĐ trước ISSUED) | ⬜ TODO | TC-BILL-011, TC-BILL-012, TC-BILL-013, TC-BILL-014 | MISSING |
| BILL-005 | Multi-payment method (Cash + QR + Card cùng 1 HĐ) | ⬜ TODO | TC-BILL-015, TC-BILL-016, TC-BILL-017, TC-BILL-018 | MISSING |
| BILL-006 | Cash payment (auto-tính tiền thừa) | ⬜ TODO | TC-BILL-019, TC-BILL-020, TC-BILL-021 | MISSING |
| BILL-007 | Card payment (manual entry số tham chiếu) | ⬜ TODO | TC-BILL-022, TC-BILL-023 | MISSING |
| BILL-008 | QR payment (VietQR + verify) | ⬜ TODO | TC-BILL-024, TC-BILL-025, TC-BILL-026 | MISSING |
| BILL-009 | Bank transfer (manual entry số tham chiếu) | ⬜ TODO | TC-BILL-027, TC-BILL-028 | MISSING |
| BILL-010 | BHYT (phần BHYT chi trả + phần BN trả) | ⬜ TODO | TC-BILL-029, TC-BILL-030, TC-BILL-031, TC-BILL-032 | MISSING |
| BILL-011 | Discount % hoặc số tiền | ⬜ TODO | TC-BILL-033, TC-BILL-034, TC-BILL-035, TC-BILL-036 | MISSING |
| BILL-012 | VAT (tính theo config) | ⬜ TODO | TC-BILL-037, TC-BILL-038, TC-BILL-039 | MISSING |
| BILL-013 | Partial payment (thanh toán một phần) | ⬜ TODO | TC-BILL-040, TC-BILL-041, TC-BILL-042 | MISSING |
| BILL-014 | Outstanding balance (theo dõi nợ) | ⬜ TODO | TC-BILL-043, TC-BILL-044, TC-BILL-045 | MISSING |
| BILL-015 | Void invoice (huỷ HĐ với lý do, admin) | ⬜ TODO | TC-BILL-046, TC-BILL-047, TC-BILL-048, TC-BILL-049, TC-BILL-050 | MISSING |
| BILL-016 | Void → reverse stock (trả medicine về kho) | ⬜ TODO | TC-BILL-051, TC-BILL-052, TC-BILL-053 | MISSING |
| BILL-017 | Refund (full hoặc partial, admin) | ⬜ TODO | TC-BILL-054, TC-BILL-055, TC-BILL-056, TC-BILL-057 | MISSING |
| BILL-018 | In hóa đơn POS (58/80mm thermal) | ⬜ TODO | TC-BILL-058, TC-BILL-059 | MISSING |
| BILL-019 | In hóa đơn A4 (letterhead + watermark) | ⬜ TODO | TC-BILL-060, TC-BILL-061, TC-BILL-062 | MISSING |
| BILL-020 | Email hóa đơn (gửi PDF qua email) | 💡 IDEA (v2) | TC-BILL-063, TC-BILL-064 | MISSING |
| BILL-021 | Loyalty program (tích điểm + giảm giá) | 💡 IDEA (v2) | TC-BILL-065, TC-BILL-066, TC-BILL-067 | MISSING |
| BILL-022 | Promotion code (mã giảm giá) | 💡 IDEA (v2) | TC-BILL-068, TC-BILL-069, TC-BILL-070, TC-BILL-071 | MISSING |
| BILL-023 | E-invoice (tích hợp VNPT/Viettel) | 💡 IDEA (v2) | TC-BILL-072, TC-BILL-073, TC-BILL-074 | MISSING |
| _Bao trùm group_ | RLS cô lập clinic / Auth chung | — | TC-BILL-075, TC-BILL-076, TC-BILL-077, TC-BILL-078 | MISSING |

**Tổng kết coverage:** COVERED = 0 · PARTIAL = 0 · MISSING = 23 functions.

---

## 2. Chi tiết Test Cases

### TC-BILL-001 — Auto-gen invoice khi visit COMPLETED + medicine DISPENSED
- **Function:** BILL-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tồn tại visit ở trạng thái COMPLETED, đơn thuốc đã DISPENSED, services của visit đã ghi nhận; user có permission `billing.create`.
- **Bước thực hiện:** 1) Chuyển visit sang COMPLETED và dispense thuốc. 2) Hệ thống trigger tạo invoice tự động (hoặc gọi endpoint generate). 3) Đọc invoice vừa tạo.
- **Dữ liệu test:** Visit có 1 dịch vụ khám (200.000đ) + 2 dòng thuốc đã dispense.
- **Kết quả mong đợi:** HTTP 201; invoice tạo với status=DRAFT/ISSUED theo cấu hình; line items gồm dịch vụ + thuốc khớp đơn; subtotal đúng tổng; `clinic_id` = clinic hiện tại; audit `invoice.created` ghi nhận.
- **Coverage hiện tại:** MISSING

### TC-BILL-002 — Không auto-gen khi visit chưa COMPLETED
- **Function:** BILL-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit ở trạng thái IN_PROGRESS, thuốc chưa DISPENSED.
- **Bước thực hiện:** 1) Trigger auto-gen invoice. 2) Kiểm tra kết quả.
- **Dữ liệu test:** Visit IN_PROGRESS.
- **Kết quả mong đợi:** Không tạo invoice; HTTP 409/422 với message điều kiện chưa thỏa; không có audit `invoice.created`.
- **Coverage hiện tại:** MISSING

### TC-BILL-003 — Không tạo trùng invoice cho cùng một visit
- **Function:** BILL-001
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit đã có invoice auto-gen.
- **Bước thực hiện:** 1) Trigger auto-gen lần 2 cho cùng visit.
- **Dữ liệu test:** Visit COMPLETED đã có invoice.
- **Kết quả mong đợi:** Hệ thống idempotent — trả về invoice cũ hoặc HTTP 409 "invoice đã tồn tại"; không tạo bản ghi trùng.
- **Coverage hiện tại:** MISSING

### TC-BILL-004 — Auto-gen invoice yêu cầu auth + permission
- **Function:** BILL-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Có endpoint tạo invoice.
- **Bước thực hiện:** 1) Gọi endpoint không kèm token → kỳ vọng 401. 2) Gọi với user thiếu `billing.create` → kỳ vọng 403.
- **Dữ liệu test:** Token rỗng; token role không có quyền billing.
- **Kết quả mong đợi:** 401 khi chưa auth; 403 khi thiếu permission; không tạo invoice.
- **Coverage hiện tại:** MISSING

### TC-BILL-005 — Sinh số hóa đơn đúng định dạng & tuần tự
- **Function:** BILL-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Cấu hình prefix mặc định `HD`; clinic chưa có hóa đơn trong ngày.
- **Bước thực hiện:** 1) Tạo 3 hóa đơn liên tiếp trong cùng ngày. 2) Đọc invoice_number của từng hóa đơn.
- **Dữ liệu test:** Ngày 2026-04-30.
- **Kết quả mong đợi:** Số lần lượt `HD-2026-04-30-0001`, `…-0002`, `…-0003`; không trùng, không nhảy số.
- **Coverage hiện tại:** MISSING

### TC-BILL-006 — Prefix tuỳ chỉnh theo clinic config
- **Function:** BILL-002
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic cấu hình prefix riêng (vd `INV`).
- **Bước thực hiện:** 1) Tạo hóa đơn. 2) Kiểm tra invoice_number.
- **Dữ liệu test:** prefix=INV.
- **Kết quả mong đợi:** Số có dạng `INV-2026-04-30-0001`.
- **Coverage hiện tại:** MISSING

### TC-BILL-007 — Đếm số reset & cô lập theo từng clinic/ngày (concurrency)
- **Function:** BILL-002
- **Loại:** Edge / Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hai clinic A và B cùng tạo hóa đơn trong ngày; tạo song song nhiều request.
- **Bước thực hiện:** 1) Clinic A tạo 2 HĐ, clinic B tạo 2 HĐ. 2) Tạo đồng thời N request trong clinic A. 3) Đọc các số.
- **Dữ liệu test:** 2 clinic, 10 request song song.
- **Kết quả mong đợi:** Mỗi clinic có chuỗi số riêng bắt đầu từ 0001; không trùng số trong cùng clinic dù chạy song song (lock/sequence per clinic); clinic A không nhìn thấy số của clinic B.
- **Coverage hiện tại:** MISSING

### TC-BILL-008 — Tạo hóa đơn thủ công (bán lẻ ngoài visit)
- **Function:** BILL-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Receptionist có `billing.create`; có sản phẩm/thuốc trong kho.
- **Bước thực hiện:** 1) POST tạo invoice thủ công với 2 line item bán lẻ. 2) Đọc invoice.
- **Dữ liệu test:** 2 dòng thuốc, không gắn visit_id.
- **Kết quả mong đợi:** HTTP 201; invoice `visit_id=null`; subtotal đúng; status=DRAFT.
- **Coverage hiện tại:** MISSING

### TC-BILL-009 — Tạo HĐ thủ công với line item rỗng/giá âm bị từ chối
- **Function:** BILL-003
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Có endpoint.
- **Bước thực hiện:** 1) POST không line item. 2) POST line item số lượng 0 hoặc đơn giá âm.
- **Dữ liệu test:** items=[]; qty=0; unit_price=-1.
- **Kết quả mong đợi:** HTTP 422 validation; không tạo invoice.
- **Coverage hiện tại:** MISSING

### TC-BILL-010 — Tạo HĐ thủ công yêu cầu quyền
- **Function:** BILL-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Không token → 401. 2) Role không có `billing.create` → 403.
- **Dữ liệu test:** Token thiếu quyền.
- **Kết quả mong đợi:** 401 / 403 tương ứng.
- **Coverage hiện tại:** MISSING

### TC-BILL-011 — Thêm line item vào HĐ ở trạng thái DRAFT
- **Function:** BILL-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice DRAFT (chưa ISSUED).
- **Bước thực hiện:** 1) Thêm 1 line item. 2) Đọc lại invoice.
- **Dữ liệu test:** 1 dịch vụ 150.000đ.
- **Kết quả mong đợi:** HTTP 200; line item được thêm; subtotal/total tính lại đúng; audit ghi nhận.
- **Coverage hiện tại:** MISSING

### TC-BILL-012 — Xoá line item khỏi HĐ DRAFT
- **Function:** BILL-004
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice DRAFT có ≥2 line item.
- **Bước thực hiện:** 1) Xoá 1 line item. 2) Đọc invoice.
- **Dữ liệu test:** Xoá line đầu tiên.
- **Kết quả mong đợi:** HTTP 200; line item bị xoá; total giảm tương ứng.
- **Coverage hiện tại:** MISSING

### TC-BILL-013 — Không cho sửa line item khi HĐ đã ISSUED/PAID
- **Function:** BILL-004
- **Loại:** Negative (state machine)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice ở trạng thái ISSUED (hoặc PAID).
- **Bước thực hiện:** 1) Thử add/remove line item.
- **Dữ liệu test:** Invoice ISSUED.
- **Kết quả mong đợi:** HTTP 409/422 "không thể sửa hóa đơn đã phát hành"; line items không đổi.
- **Coverage hiện tại:** MISSING

### TC-BILL-014 — Sửa line item yêu cầu quyền
- **Function:** BILL-004
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Invoice DRAFT.
- **Bước thực hiện:** 1) Không token → 401. 2) Thiếu `billing.update` → 403.
- **Dữ liệu test:** Token thiếu quyền.
- **Kết quả mong đợi:** 401 / 403.
- **Coverage hiện tại:** MISSING

### TC-BILL-015 — Thanh toán nhiều phương thức trên cùng một hóa đơn
- **Function:** BILL-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice ISSUED total = 1.000.000đ.
- **Bước thực hiện:** 1) Ghi nhận payment Cash 400.000 + Card 300.000 + QR 300.000. 2) Đọc invoice.
- **Dữ liệu test:** 3 payment record.
- **Kết quả mong đợi:** HTTP 200/201; 3 bản ghi payment; tổng đã trả = total; invoice chuyển PAID; audit cho từng payment.
- **Coverage hiện tại:** MISSING

### TC-BILL-016 — Tổng các phương thức vượt quá total bị từ chối
- **Function:** BILL-005
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice total = 1.000.000đ.
- **Bước thực hiện:** 1) Ghi nhận Cash 700.000 + Card 500.000 (= 1.200.000 > total, trong khi không phải cash thừa).
- **Dữ liệu test:** Card overpay.
- **Kết quả mong đợi:** HTTP 422 — chỉ cash mới được phép thừa (auto-tính tiền thừa); phương thức không phải cash không được vượt số còn nợ.
- **Coverage hiện tại:** MISSING

### TC-BILL-017 — Multi-payment cộng dồn với partial trước đó
- **Function:** BILL-005
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice đã có partial 300.000 (PARTIALLY_PAID).
- **Bước thực hiện:** 1) Ghi nhận thêm Cash 400.000 + QR 300.000.
- **Dữ liệu test:** Tổng còn nợ 700.000.
- **Kết quả mong đợi:** Tổng đã trả = total; invoice PAID; outstanding = 0.
- **Coverage hiện tại:** MISSING

### TC-BILL-018 — Multi-payment yêu cầu quyền
- **Function:** BILL-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Không token → 401. 2) Thiếu `billing.payment` → 403.
- **Dữ liệu test:** Token thiếu quyền.
- **Kết quả mong đợi:** 401 / 403.
- **Coverage hiện tại:** MISSING

### TC-BILL-019 — Thanh toán tiền mặt auto-tính tiền thừa
- **Function:** BILL-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice ISSUED total = 850.000đ.
- **Bước thực hiện:** 1) Nhập tiền khách đưa 1.000.000. 2) Đọc kết quả.
- **Dữ liệu test:** amount_tendered=1.000.000.
- **Kết quả mong đợi:** HTTP 200; change_due = 150.000; payment ghi nhận = 850.000; invoice PAID.
- **Coverage hiện tại:** MISSING

### TC-BILL-020 — Tiền mặt đưa thiếu → ghi nhận partial, không tính tiền thừa
- **Function:** BILL-006
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice total = 850.000đ.
- **Bước thực hiện:** 1) Nhập tiền đưa 500.000.
- **Dữ liệu test:** amount_tendered=500.000.
- **Kết quả mong đợi:** change_due=0; payment=500.000; invoice PARTIALLY_PAID; outstanding=350.000.
- **Coverage hiện tại:** MISSING

### TC-BILL-021 — Tiền mặt số tiền 0 / âm bị từ chối
- **Function:** BILL-006
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Invoice ISSUED.
- **Bước thực hiện:** 1) Nhập amount=0 hoặc -100.
- **Dữ liệu test:** amount<=0.
- **Kết quả mong đợi:** HTTP 422; không ghi payment.
- **Coverage hiện tại:** MISSING

### TC-BILL-022 — Thanh toán thẻ với số tham chiếu thủ công
- **Function:** BILL-007
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice ISSUED.
- **Bước thực hiện:** 1) Ghi nhận payment method=CARD, reference="AUTH123456". 2) Đọc payment.
- **Dữ liệu test:** reference number.
- **Kết quả mong đợi:** HTTP 200; payment lưu method=CARD + reference; invoice PAID/PARTIALLY_PAID theo số tiền.
- **Coverage hiện tại:** MISSING

### TC-BILL-023 — Thanh toán thẻ thiếu số tham chiếu bị từ chối
- **Function:** BILL-007
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Invoice ISSUED.
- **Bước thực hiện:** 1) Ghi payment CARD không reference.
- **Dữ liệu test:** reference rỗng.
- **Kết quả mong đợi:** HTTP 422 yêu cầu số tham chiếu.
- **Coverage hiện tại:** MISSING

### TC-BILL-024 — Sinh QR VietQR cho hóa đơn
- **Function:** BILL-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic cấu hình tài khoản nhận VietQR; invoice ISSUED.
- **Bước thực hiện:** 1) Gọi endpoint tạo QR cho invoice. 2) Đọc payload QR.
- **Dữ liệu test:** total=500.000.
- **Kết quả mong đợi:** HTTP 200; chuỗi VietQR đúng chuẩn (số tài khoản, số tiền, nội dung = invoice_number).
- **Coverage hiện tại:** MISSING

### TC-BILL-025 — Verify thanh toán QR cập nhật trạng thái
- **Function:** BILL-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã sinh QR; nhận callback/verify thanh toán thành công.
- **Bước thực hiện:** 1) Gọi verify với mã giao dịch khớp. 2) Đọc invoice.
- **Dữ liệu test:** txn_id hợp lệ, amount khớp.
- **Kết quả mong đợi:** payment QR ghi nhận; invoice PAID.
- **Coverage hiện tại:** MISSING

### TC-BILL-026 — Verify QR với số tiền không khớp bị từ chối
- **Function:** BILL-008
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã sinh QR cho 500.000.
- **Bước thực hiện:** 1) Verify với amount=300.000.
- **Dữ liệu test:** amount lệch.
- **Kết quả mong đợi:** Không tự động mark PAID; ghi partial hoặc reject + cảnh báo; không sai lệch sổ.
- **Coverage hiện tại:** MISSING

### TC-BILL-027 — Chuyển khoản ngân hàng với số tham chiếu
- **Function:** BILL-009
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice ISSUED.
- **Bước thực hiện:** 1) Ghi payment BANK_TRANSFER + reference. 2) Đọc payment.
- **Dữ liệu test:** reference="FT2026..."
- **Kết quả mong đợi:** HTTP 200; payment lưu method=BANK_TRANSFER; invoice cập nhật.
- **Coverage hiện tại:** MISSING

### TC-BILL-028 — Chuyển khoản thiếu reference bị từ chối
- **Function:** BILL-009
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Invoice ISSUED.
- **Bước thực hiện:** 1) Ghi payment BANK_TRANSFER không reference.
- **Dữ liệu test:** reference rỗng.
- **Kết quả mong đợi:** HTTP 422.
- **Coverage hiện tại:** MISSING

### TC-BILL-029 — Tách phần BHYT chi trả và phần bệnh nhân trả
- **Function:** BILL-010
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Bệnh nhân có thẻ BHYT mức hưởng 80%; invoice total = 1.000.000đ với dịch vụ được BHYT chi trả.
- **Bước thực hiện:** 1) Áp dụng BHYT. 2) Đọc breakdown.
- **Dữ liệu test:** mức hưởng 80%.
- **Kết quả mong đợi:** insurance_covered = 800.000; patient_payable = 200.000; tổng = total; ghi nhận đúng nguồn chi trả.
- **Coverage hiện tại:** MISSING

### TC-BILL-030 — BHYT chỉ áp dụng cho dịch vụ trong danh mục được hưởng
- **Function:** BILL-010
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice gồm 1 dịch vụ BHYT + 1 dịch vụ ngoài danh mục.
- **Bước thực hiện:** 1) Áp dụng BHYT. 2) Kiểm tra phần chi trả.
- **Dữ liệu test:** 1 covered + 1 non-covered.
- **Kết quả mong đợi:** Chỉ phần covered được BHYT chi trả; dịch vụ ngoài danh mục do BN trả 100%.
- **Coverage hiện tại:** MISSING

### TC-BILL-031 — BHYT với thẻ hết hạn / sai thông tin bị từ chối
- **Function:** BILL-010
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thẻ BHYT hết hạn.
- **Bước thực hiện:** 1) Áp dụng BHYT với thẻ expired.
- **Dữ liệu test:** expiry < ngày hiện tại.
- **Kết quả mong đợi:** HTTP 422; không áp dụng chi trả BHYT; BN trả 100%.
- **Coverage hiện tại:** MISSING

### TC-BILL-032 — BHYT yêu cầu quyền & cô lập clinic
- **Function:** BILL-010
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice clinic A.
- **Bước thực hiện:** 1) Không token → 401. 2) User clinic B áp BHYT lên invoice clinic A → kỳ vọng 404/403.
- **Dữ liệu test:** Cross-clinic.
- **Kết quả mong đợi:** 401; clinic B không thấy/không sửa được invoice clinic A (RLS).
- **Coverage hiện tại:** MISSING

### TC-BILL-033 — Discount theo phần trăm
- **Function:** BILL-011
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice subtotal = 1.000.000đ; user có quyền discount.
- **Bước thực hiện:** 1) Áp discount 10%. 2) Đọc total.
- **Dữ liệu test:** discount_percent=10.
- **Kết quả mong đợi:** discount_amount=100.000; total=900.000 (trước VAT theo thứ tự cấu hình).
- **Coverage hiện tại:** MISSING

### TC-BILL-034 — Discount theo số tiền tuyệt đối
- **Function:** BILL-011
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice subtotal = 1.000.000đ.
- **Bước thực hiện:** 1) Áp discount 150.000đ.
- **Dữ liệu test:** discount_amount=150.000.
- **Kết quả mong đợi:** total=850.000.
- **Coverage hiện tại:** MISSING

### TC-BILL-035 — Discount vượt subtotal / âm bị từ chối
- **Function:** BILL-011
- **Loại:** Negative / Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** subtotal=1.000.000.
- **Bước thực hiện:** 1) discount 120% hoặc 1.200.000đ. 2) discount âm.
- **Dữ liệu test:** percent>100; amount>subtotal; amount<0.
- **Kết quả mong đợi:** HTTP 422; total không bao giờ âm.
- **Coverage hiện tại:** MISSING

### TC-BILL-036 — Discount vượt ngưỡng yêu cầu quyền cao hơn (Receptionist+)
- **Function:** BILL-011
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Cấu hình ngưỡng discount tối đa cho Receptionist; vai trò "Receptionist+" mới được vượt ngưỡng.
- **Bước thực hiện:** 1) Không token → 401. 2) Receptionist thường áp discount vượt ngưỡng → 403. 3) Role có quyền → 200.
- **Dữ liệu test:** discount > ngưỡng.
- **Kết quả mong đợi:** 401/403 đúng vai trò; chỉ Receptionist+ được phép.
- **Coverage hiện tại:** MISSING

### TC-BILL-037 — Tính VAT theo config
- **Function:** BILL-012
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic cấu hình VAT=8%; invoice subtotal sau discount = 900.000.
- **Bước thực hiện:** 1) Tính total. 2) Đọc breakdown.
- **Dữ liệu test:** vat_rate=8%.
- **Kết quả mong đợi:** vat_amount=72.000; total=972.000.
- **Coverage hiện tại:** MISSING

### TC-BILL-038 — VAT=0 / không cấu hình
- **Function:** BILL-012
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic không bật VAT.
- **Bước thực hiện:** 1) Tính total.
- **Dữ liệu test:** vat_rate=0.
- **Kết quả mong đợi:** vat_amount=0; total=subtotal sau discount.
- **Coverage hiện tại:** MISSING

### TC-BILL-039 — Làm tròn VAT đúng quy tắc tiền tệ VND
- **Function:** BILL-012
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** subtotal lẻ tạo VAT có phần thập phân.
- **Bước thực hiện:** 1) Tính VAT cho subtotal=333.333.
- **Dữ liệu test:** vat=8% → 26.666,64.
- **Kết quả mong đợi:** Làm tròn về VND theo quy tắc cấu hình (không sai lệch tổng); không tạo phần lẻ thập phân trong VND.
- **Coverage hiện tại:** MISSING

### TC-BILL-040 — Ghi nhận thanh toán một phần
- **Function:** BILL-013
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice ISSUED total=1.000.000.
- **Bước thực hiện:** 1) Ghi payment 600.000. 2) Đọc invoice.
- **Dữ liệu test:** amount=600.000.
- **Kết quả mong đợi:** invoice PARTIALLY_PAID; paid=600.000; outstanding=400.000.
- **Coverage hiện tại:** MISSING

### TC-BILL-041 — Partial nối tiếp đến khi PAID
- **Function:** BILL-013
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice PARTIALLY_PAID còn nợ 400.000.
- **Bước thực hiện:** 1) Ghi tiếp 400.000.
- **Dữ liệu test:** amount=400.000.
- **Kết quả mong đợi:** invoice PAID; outstanding=0.
- **Coverage hiện tại:** MISSING

### TC-BILL-042 — Partial vượt số còn nợ (non-cash) bị từ chối
- **Function:** BILL-013
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Còn nợ 400.000.
- **Bước thực hiện:** 1) Ghi payment thẻ 500.000.
- **Dữ liệu test:** amount>outstanding (non-cash).
- **Kết quả mong đợi:** HTTP 422 (chỉ tiền mặt được thừa).
- **Coverage hiện tại:** MISSING

### TC-BILL-043 — Theo dõi công nợ chưa thanh toán
- **Function:** BILL-014
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có nhiều invoice với trạng thái khác nhau.
- **Bước thực hiện:** 1) Gọi endpoint outstanding balance theo bệnh nhân/clinic. 2) Đọc kết quả.
- **Dữ liệu test:** 3 invoice: 1 PAID, 1 PARTIALLY_PAID (nợ 400.000), 1 ISSUED (nợ 1.000.000).
- **Kết quả mong đợi:** Tổng công nợ = 1.400.000; danh sách invoice còn nợ đúng.
- **Coverage hiện tại:** MISSING

### TC-BILL-044 — Công nợ không tính invoice đã VOID
- **Function:** BILL-014
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có 1 invoice VOID.
- **Bước thực hiện:** 1) Gọi outstanding balance.
- **Dữ liệu test:** Invoice VOID không tính nợ.
- **Kết quả mong đợi:** Invoice VOID bị loại khỏi công nợ.
- **Coverage hiện tại:** MISSING

### TC-BILL-045 — Công nợ cô lập theo clinic (RLS)
- **Function:** BILL-014
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B đều có công nợ.
- **Bước thực hiện:** 1) User clinic A gọi outstanding balance.
- **Dữ liệu test:** 2 clinic.
- **Kết quả mong đợi:** Chỉ thấy công nợ clinic A; không lẫn dữ liệu clinic B.
- **Coverage hiện tại:** MISSING

### TC-BILL-046 — Huỷ hóa đơn có lý do (admin)
- **Function:** BILL-015
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice ISSUED; user role Admin.
- **Bước thực hiện:** 1) Void invoice với reason. 2) Đọc invoice.
- **Dữ liệu test:** reason="Nhập sai dịch vụ".
- **Kết quả mong đợi:** HTTP 200; status=VOID; void_reason lưu lại; void_by + void_at ghi nhận; audit `invoice.voided`.
- **Coverage hiện tại:** MISSING

### TC-BILL-047 — Void thiếu lý do bị từ chối
- **Function:** BILL-015
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Invoice ISSUED, Admin.
- **Bước thực hiện:** 1) Void không reason.
- **Dữ liệu test:** reason rỗng.
- **Kết quả mong đợi:** HTTP 422 yêu cầu lý do.
- **Coverage hiện tại:** MISSING

### TC-BILL-048 — Không cho void invoice đã PAID/đã VOID (state machine)
- **Function:** BILL-015
- **Loại:** Negative / Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice ở PAID hoặc đã VOID.
- **Bước thực hiện:** 1) Void invoice PAID. 2) Void invoice đã VOID.
- **Dữ liệu test:** state không hợp lệ.
- **Kết quả mong đợi:** HTTP 409 — PAID phải qua refund, không void trực tiếp; VOID không thể void lại.
- **Coverage hiện tại:** MISSING

### TC-BILL-049 — Void chỉ dành cho Admin
- **Function:** BILL-015
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Invoice ISSUED.
- **Bước thực hiện:** 1) Không token → 401. 2) Receptionist void → 403. 3) Admin void → 200.
- **Dữ liệu test:** Role thường vs Admin.
- **Kết quả mong đợi:** 401/403/200 đúng vai trò.
- **Coverage hiện tại:** MISSING

### TC-BILL-050 — Void cô lập clinic (RLS)
- **Function:** BILL-015
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice thuộc clinic A.
- **Bước thực hiện:** 1) Admin clinic B void invoice clinic A.
- **Dữ liệu test:** Cross-clinic.
- **Kết quả mong đợi:** 404/403; invoice clinic A không bị thay đổi.
- **Coverage hiện tại:** MISSING

### TC-BILL-051 — Void hoàn trả thuốc về kho
- **Function:** BILL-016
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice ISSUED có 2 dòng thuốc đã trừ kho (lot/batch xác định).
- **Bước thực hiện:** 1) Void invoice. 2) Đọc tồn kho từng lot.
- **Dữ liệu test:** thuốc A -10, thuốc B -5 lúc dispense.
- **Kết quả mong đợi:** Sau void, tồn kho A +10, B +5 (trả đúng lot); ghi stock movement loại REVERSAL liên kết invoice; audit kho.
- **Coverage hiện tại:** MISSING

### TC-BILL-052 — Void HĐ không có thuốc không tạo movement kho
- **Function:** BILL-016
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice chỉ có dịch vụ khám.
- **Bước thực hiện:** 1) Void.
- **Dữ liệu test:** không line thuốc.
- **Kết quả mong đợi:** Void thành công; không có stock movement.
- **Coverage hiện tại:** MISSING

### TC-BILL-053 — Reverse stock atomic với void (rollback nếu lỗi)
- **Function:** BILL-016
- **Loại:** Edge / Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Mô phỏng lỗi khi cập nhật kho giữa chừng.
- **Bước thực hiện:** 1) Void với inject lỗi ở bước reverse stock.
- **Dữ liệu test:** lỗi DB giả lập.
- **Kết quả mong đợi:** Transaction rollback toàn bộ — invoice KHÔNG chuyển VOID nếu kho chưa được trả; không có trạng thái nửa vời.
- **Coverage hiện tại:** MISSING

### TC-BILL-054 — Hoàn tiền toàn phần (admin)
- **Function:** BILL-017
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice PAID total=1.000.000; Admin.
- **Bước thực hiện:** 1) Refund full với reason. 2) Đọc invoice.
- **Dữ liệu test:** refund_amount=1.000.000.
- **Kết quả mong đợi:** HTTP 200; refund record=1.000.000; invoice REFUNDED; audit `invoice.refunded`.
- **Coverage hiện tại:** MISSING

### TC-BILL-055 — Hoàn tiền một phần
- **Function:** BILL-017
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice PAID total=1.000.000.
- **Bước thực hiện:** 1) Refund 300.000.
- **Dữ liệu test:** partial refund.
- **Kết quả mong đợi:** refund=300.000; invoice PARTIALLY_REFUNDED; net thu = 700.000.
- **Coverage hiện tại:** MISSING

### TC-BILL-056 — Refund vượt số đã thanh toán bị từ chối
- **Function:** BILL-017
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Invoice PAID 1.000.000, đã refund 300.000.
- **Bước thực hiện:** 1) Refund thêm 800.000 (tổng refund > paid).
- **Dữ liệu test:** refund vượt.
- **Kết quả mong đợi:** HTTP 422; tổng refund không vượt tổng đã thu.
- **Coverage hiện tại:** MISSING

### TC-BILL-057 — Refund chỉ dành cho Admin + RLS
- **Function:** BILL-017
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** Invoice PAID clinic A.
- **Bước thực hiện:** 1) Không token → 401. 2) Receptionist → 403. 3) Admin clinic B refund invoice clinic A → 404/403.
- **Dữ liệu test:** Role + cross-clinic.
- **Kết quả mong đợi:** 401/403; clinic B không refund được invoice clinic A.
- **Coverage hiện tại:** MISSING

### TC-BILL-058 — In hóa đơn POS khổ 80mm
- **Function:** BILL-018
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Invoice PAID; máy in nhiệt 80mm cấu hình.
- **Bước thực hiện:** 1) Render template POS 80mm. 2) Kiểm tra layout.
- **Dữ liệu test:** invoice có 3 line.
- **Kết quả mong đợi:** Bố cục vừa 80mm; có tên clinic, số HĐ, line items, total, phương thức TT, tiền thừa; không tràn lề.
- **Coverage hiện tại:** MISSING

### TC-BILL-059 — In POS khổ 58mm
- **Function:** BILL-018
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Cấu hình 58mm.
- **Bước thực hiện:** 1) Render template 58mm.
- **Dữ liệu test:** invoice dài (nhiều line).
- **Kết quả mong đợi:** Layout co đúng 58mm; chữ không bị cắt; phân trang/cuộn hợp lý.
- **Coverage hiện tại:** MISSING

### TC-BILL-060 — In hóa đơn A4 có letterhead
- **Function:** BILL-019
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Invoice ISSUED/PAID.
- **Bước thực hiện:** 1) Render template A4. 2) Kiểm tra.
- **Dữ liệu test:** invoice đầy đủ thông tin.
- **Kết quả mong đợi:** A4 có letterhead clinic (logo, tên, địa chỉ, MST), bảng line items, VAT, total, chữ ký.
- **Coverage hiện tại:** MISSING

### TC-BILL-061 — Watermark "Đã thanh toán" khi PAID
- **Function:** BILL-019
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Invoice PAID.
- **Bước thực hiện:** 1) Render A4.
- **Dữ liệu test:** status=PAID.
- **Kết quả mong đợi:** Hiển thị watermark "Đã thanh toán"; với invoice chưa PAID thì KHÔNG có watermark này.
- **Coverage hiện tại:** MISSING

### TC-BILL-062 — In A4 cho invoice VOID hiển thị trạng thái huỷ
- **Function:** BILL-019
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Invoice VOID.
- **Bước thực hiện:** 1) Render A4.
- **Dữ liệu test:** status=VOID.
- **Kết quả mong đợi:** Hiển thị rõ "ĐÃ HUỶ" + lý do; không hiển thị watermark "Đã thanh toán".
- **Coverage hiện tại:** MISSING

### TC-BILL-063 — Gửi hóa đơn PDF qua email (v2)
- **Function:** BILL-020
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Bệnh nhân có email; SMTP cấu hình; (v2 — chưa lên kế hoạch triển khai).
- **Bước thực hiện:** 1) Gọi endpoint email invoice. 2) Kiểm tra hàng đợi gửi.
- **Dữ liệu test:** email hợp lệ.
- **Kết quả mong đợi:** HTTP 202; job email tạo với PDF đính kèm; audit gửi email.
- **Coverage hiện tại:** MISSING

### TC-BILL-064 — Email invoice với địa chỉ rỗng/sai bị từ chối (v2)
- **Function:** BILL-020
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Bệnh nhân không email.
- **Bước thực hiện:** 1) Gửi email.
- **Dữ liệu test:** email rỗng/sai format.
- **Kết quả mong đợi:** HTTP 422; không tạo job.
- **Coverage hiện tại:** MISSING

### TC-BILL-065 — Tích điểm loyalty khi thanh toán (v2)
- **Function:** BILL-021
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Bật loyalty; tỉ lệ 1 điểm/10.000đ; (v2).
- **Bước thực hiện:** 1) Thanh toán invoice 1.000.000. 2) Đọc điểm BN.
- **Dữ liệu test:** total=1.000.000.
- **Kết quả mong đợi:** +100 điểm cho bệnh nhân; lịch sử điểm ghi nhận.
- **Coverage hiện tại:** MISSING

### TC-BILL-066 — Dùng điểm để giảm giá (v2)
- **Function:** BILL-021
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN có 500 điểm; quy đổi 1 điểm=1.000đ.
- **Bước thực hiện:** 1) Áp 200 điểm lên invoice.
- **Dữ liệu test:** redeem 200 điểm.
- **Kết quả mong đợi:** Giảm 200.000đ; trừ 200 điểm; số dư điểm=300.
- **Coverage hiện tại:** MISSING

### TC-BILL-067 — Dùng điểm vượt số dư bị từ chối (v2)
- **Function:** BILL-021
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** BN có 100 điểm.
- **Bước thực hiện:** 1) Redeem 200 điểm.
- **Dữ liệu test:** redeem > số dư.
- **Kết quả mong đợi:** HTTP 422; số dư điểm không âm.
- **Coverage hiện tại:** MISSING

### TC-BILL-068 — Áp mã khuyến mãi hợp lệ (v2)
- **Function:** BILL-022
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Mã "SALE10" giảm 10%, còn hiệu lực, còn lượt; (v2).
- **Bước thực hiện:** 1) Áp mã lên invoice 1.000.000.
- **Dữ liệu test:** code=SALE10.
- **Kết quả mong đợi:** Giảm 100.000; lượt dùng mã -1.
- **Coverage hiện tại:** MISSING

### TC-BILL-069 — Mã khuyến mãi hết hạn / hết lượt bị từ chối (v2)
- **Function:** BILL-022
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Mã expired hoặc hết lượt.
- **Bước thực hiện:** 1) Áp mã.
- **Dữ liệu test:** code expired.
- **Kết quả mong đợi:** HTTP 422; không áp giảm.
- **Coverage hiện tại:** MISSING

### TC-BILL-070 — Không áp 2 lần cùng 1 mã trên 1 invoice (v2)
- **Function:** BILL-022
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Mã đã áp 1 lần.
- **Bước thực hiện:** 1) Áp lại cùng mã.
- **Dữ liệu test:** duplicate apply.
- **Kết quả mong đợi:** HTTP 409; chỉ giảm 1 lần.
- **Coverage hiện tại:** MISSING

### TC-BILL-071 — Mã khuyến mãi cô lập theo clinic (RLS) (v2)
- **Function:** BILL-022
- **Loại:** Security (RLS)
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Mã thuộc clinic A.
- **Bước thực hiện:** 1) User clinic B áp mã của clinic A.
- **Dữ liệu test:** cross-clinic code.
- **Kết quả mong đợi:** HTTP 404/422; clinic B không dùng được mã clinic A.
- **Coverage hiện tại:** MISSING

### TC-BILL-072 — Phát hành hóa đơn điện tử qua nhà cung cấp (v2)
- **Function:** BILL-023
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tích hợp VNPT/Viettel cấu hình; invoice PAID; (v2).
- **Bước thực hiện:** 1) Phát hành e-invoice. 2) Đọc mã tra cứu.
- **Dữ liệu test:** provider=VNPT.
- **Kết quả mong đợi:** HTTP 200/202; nhận mã tra cứu + trạng thái "đã phát hành"; lưu link/PDF; audit e-invoice.
- **Coverage hiện tại:** MISSING

### TC-BILL-073 — E-invoice xử lý lỗi nhà cung cấp (timeout/từ chối) (v2)
- **Function:** BILL-023
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Provider trả lỗi.
- **Bước thực hiện:** 1) Phát hành khi provider lỗi.
- **Dữ liệu test:** mock 5xx/timeout.
- **Kết quả mong đợi:** Không mark "đã phát hành"; trạng thái "lỗi/chờ thử lại"; có cơ chế retry; không sai lệch dữ liệu.
- **Coverage hiện tại:** MISSING

### TC-BILL-074 — Không phát hành e-invoice cho HĐ VOID (v2)
- **Function:** BILL-023
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Invoice VOID.
- **Bước thực hiện:** 1) Phát hành e-invoice.
- **Dữ liệu test:** status=VOID.
- **Kết quả mong đợi:** HTTP 409; chỉ HĐ hợp lệ (ISSUED/PAID) mới được phát hành.
- **Coverage hiện tại:** MISSING

### TC-BILL-075 — Bao trùm: mọi endpoint BILL chặn truy cập chưa auth (401)
- **Function:** Bao trùm group (BILL-001…023)
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Liệt kê toàn bộ endpoint billing/payment/invoice.
- **Bước thực hiện:** 1) Gọi từng endpoint không token (GET/POST/PATCH/DELETE).
- **Dữ liệu test:** Không Authorization header.
- **Kết quả mong đợi:** Tất cả trả 401; không rò rỉ dữ liệu.
- **Coverage hiện tại:** MISSING

### TC-BILL-076 — Bao trùm: phân quyền theo permission billing.*
- **Function:** Bao trùm group
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User thiếu các permission `billing.create/update/payment/void/refund`.
- **Bước thực hiện:** 1) Gọi từng endpoint tương ứng.
- **Dữ liệu test:** Token thiếu từng quyền.
- **Kết quả mong đợi:** Trả 403 đúng từng permission; thao tác không thực thi.
- **Coverage hiện tại:** MISSING

### TC-BILL-077 — Bao trùm: cô lập dữ liệu hóa đơn giữa các clinic (RLS)
- **Function:** Bao trùm group
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B đều có invoice/payment.
- **Bước thực hiện:** 1) User clinic A list/get/sửa invoice của clinic B (GET list, GET by id, PATCH, void, refund).
- **Dữ liệu test:** invoice_id của clinic B.
- **Kết quả mong đợi:** List chỉ trả invoice clinic A; truy cập theo id của clinic B trả 404; RLS chặn mọi thao tác chéo clinic.
- **Coverage hiện tại:** MISSING

### TC-BILL-078 — Bao trùm: ghi audit cho mọi thao tác tài chính
- **Function:** Bao trùm group
- **Loại:** Security / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hệ audit hoạt động.
- **Bước thực hiện:** 1) Thực hiện create/issue/payment/void/refund. 2) Truy vấn audit log.
- **Dữ liệu test:** Một chuỗi thao tác đầy đủ.
- **Kết quả mong đợi:** Mỗi thao tác sinh audit entry (actor, clinic_id, invoice_id, before/after khi áp dụng); không thiếu sự kiện tài chính nào.
- **Coverage hiện tại:** MISSING

---

## 3. Ghi chú & rủi ro

- **Trạng thái nguồn:** 100% function BILL ở mức TODO/IDEA — module **chưa ship**. Bộ test case này là chuẩn nghiệm thu cho TASK-013 (v1: BILL-001…019) và backlog v2 (BILL-020…023).
- **State machine hóa đơn (suy ra từ BA/nghiệp vụ):** DRAFT → ISSUED → (PARTIALLY_PAID) → PAID → (PARTIALLY_REFUNDED/REFUNDED); nhánh VOID chỉ từ DRAFT/ISSUED (HĐ PAID phải dùng refund). Khi code chốt enum chính thức, đồng bộ lại tên trạng thái trong các TC liên quan (TC-BILL-013/040/041/046/048/054/055).
- **Rủi ro lớn nhất:** Các quy tắc tiền/kho cần tính atomic — đặc biệt BILL-016 (void → reverse stock, TC-BILL-053) và sinh số HĐ song song (TC-BILL-007); sai sót gây lệch sổ quỹ và tồn kho. RLS cô lập clinic phải được kiểm thử cho mọi endpoint tài chính (TC-BILL-077).
- **Hạn chế khi soạn:** Không xác minh được endpoint/permission thực tế trong `clinic-cms-merge/app` do lỗi xuất kết quả tool trong phiên; tên permission (`billing.*`) và tên state là giả định hợp lý theo BA/function_list — cần đối chiếu lại với code khi TASK-013 triển khai.
