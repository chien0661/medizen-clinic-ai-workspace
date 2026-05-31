# Test Case Catalog — RX · Kê đơn (Prescription)

**Nguồn:** function_list_data.py (group RX, dòng 777-854) + clinic_management_function_list.md (dòng 263-278) + system_design/BA (state machine đơn, reserve stock, RBAC self-approve).
**Phạm vi:** 16 functions (RX-001 … RX-016).  **Tổng test case:** 58.  **Ngày:** 2026-05-30.

> **Ghi chú coverage:** Trong nguồn, toàn bộ function RX ở trạng thái ⬜ TODO (v1: TASK-011/012/005) hoặc 💡 IDEA (v2: RX-007, RX-008, RX-010, RX-014). Chưa có function nào DONE. Tại phiên soạn không truy cập được code/test thực tế trong repo `clinic-cms-merge` (kênh output gián đoạn), nên mọi Coverage gán **MISSING** — đây là đặc tả test mục tiêu (target spec). Test Engineer cần đối chiếu lại `clinic-cms-merge/app/modules` + `clinic-cms-merge/tests` khi tooling ổn định để nâng TC lên COVERED/PARTIAL.
>
> **State machine đơn thuốc (từ BA/system_design):** DRAFT/CREATED → (visit COMPLETED) → đơn internal route sang pharmacy queue + RESERVE stock → DISPENSED (convert reserved → out, trừ thật) ; nhánh huỷ: trước dispense → CANCELLED (release reservation), sau dispense không cancel được (chỉ refund qua billing). Edit: trước dispense doctor được edit; sau dispense chỉ admin có perm `rx.amend` (tạo amendment). External item: không route pharmacy, không reserve, không vào invoice.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| RX-001 | Tạo đơn thuốc (multi-medicine) | ⬜ TODO (v1, TASK-011) | TC-RX-001, TC-RX-002, TC-RX-003, TC-RX-004, TC-RX-005, TC-RX-006 | MISSING |
| RX-002 | Auto-gen Rx number (fn_next_rx_number) | ⬜ TODO (v1, TASK-011) | TC-RX-007, TC-RX-008, TC-RX-009 | MISSING |
| RX-003 | Internal vs External (is_internal) | ⬜ TODO (v1, TASK-011) | TC-RX-010, TC-RX-011, TC-RX-012 | MISSING |
| RX-004 | Liều dùng (sáng/trưa/chiều/tối + trước/sau ăn) | ⬜ TODO (v1, TASK-011) | TC-RX-013, TC-RX-014, TC-RX-015 | MISSING |
| RX-005 | Số ngày → auto qty | ⬜ TODO (v1, TASK-011) | TC-RX-016, TC-RX-017, TC-RX-018 | MISSING |
| RX-006 | Cảnh báo dị ứng (match allergens) | ⬜ TODO (v1, TASK-011) | TC-RX-019, TC-RX-020, TC-RX-021 | MISSING |
| RX-007 | Drug interaction warning | 💡 IDEA (v2) | TC-RX-022, TC-RX-023 | MISSING |
| RX-008 | Drug-condition warning | 💡 IDEA (v2) | TC-RX-024, TC-RX-025 | MISSING |
| RX-009 | In đơn thuốc (A5/A4/80mm) | ⬜ TODO (v1, TASK-011) | TC-RX-026, TC-RX-027, TC-RX-028 | MISSING |
| RX-010 | QR code in đơn (verify) | 💡 IDEA (v2) | TC-RX-029, TC-RX-030 | MISSING |
| RX-011 | Edit đơn (trước dispense / amend) | ⬜ TODO (v1, TASK-011) | TC-RX-031, TC-RX-032, TC-RX-033, TC-RX-034, TC-RX-035, TC-RX-036 | MISSING |
| RX-012 | Cancel đơn (trước dispense) | ⬜ TODO (v1, TASK-011) | TC-RX-037, TC-RX-038, TC-RX-039, TC-RX-040 | MISSING |
| RX-013 | Lịch sử đơn của BN | ⬜ TODO (v1, TASK-005) | TC-RX-041, TC-RX-042, TC-RX-043, TC-RX-044 | MISSING |
| RX-014 | Đơn template (save & reuse) | 💡 IDEA (v2) | TC-RX-045, TC-RX-046, TC-RX-047 | MISSING |
| RX-015 | Reserve stock (đơn internal) | ⬜ TODO (v1, TASK-012) | TC-RX-048, TC-RX-049, TC-RX-050, TC-RX-051, TC-RX-052, TC-RX-053 | MISSING |
| RX-016 | Hiển thị stock thuốc khi kê đơn | ⬜ TODO (v1, TASK-011) | TC-RX-054, TC-RX-055, TC-RX-056, TC-RX-057, TC-RX-058 | MISSING |

---

## 2. Chi tiết Test Cases

### TC-RX-001 — Tạo đơn thuốc multi-medicine thành công
- **Function:** RX-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor đăng nhập clinic A; tồn tại visit/encounter đang mở của BN clinic A; ≥2 thuốc active trong catalog clinic A.
- **Bước thực hiện:** 1) POST `/api/v1/prescriptions` với encounter_id, patient_id, 2 items (medicine_id, dose, schedule sáng/trưa/chiều/tối, timing, days, is_internal, note). 2) Đọc response. 3) GET lại đơn.
- **Dữ liệu test:** Paracetamol 500mg (sáng 1 + tối 1, sau ăn, 5 ngày, internal), Amoxicillin 500mg (sáng 1 + chiều 1, 7 ngày, internal).
- **Kết quả mong đợi:** HTTP 201; đơn status DRAFT/CREATED; trả 2 line items đủ liều/schedule; sinh rx_number (RX-002); audit `prescription.created`; tổng tiền chỉ tính internal items.
- **Coverage hiện tại:** MISSING

### TC-RX-002 — Tạo đơn với items rỗng → từ chối
- **Function:** RX-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Doctor đăng nhập.
- **Bước thực hiện:** 1) POST `/api/v1/prescriptions` với `items: []`.
- **Dữ liệu test:** mảng items rỗng.
- **Kết quả mong đợi:** HTTP 422; yêu cầu ≥1 thuốc; không tạo record; không tiêu thụ rx_number sequence.
- **Coverage hiện tại:** MISSING

### TC-RX-003 — Tạo đơn với medicine_id không tồn tại
- **Function:** RX-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor đăng nhập clinic A.
- **Bước thực hiện:** 1) POST đơn với 1 item có medicine_id không tồn tại trong catalog clinic A.
- **Dữ liệu test:** medicine_id = UUID ngẫu nhiên.
- **Kết quả mong đợi:** HTTP 404/422; không tạo đơn.
- **Coverage hiện tại:** MISSING

### TC-RX-004 — Tạo đơn khi chưa auth → 401
- **Function:** RX-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi token.
- **Bước thực hiện:** 1) POST `/api/v1/prescriptions` không kèm Authorization.
- **Dữ liệu test:** payload đơn hợp lệ.
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING

### TC-RX-005 — Tạo đơn bởi role không có quyền kê đơn → 403
- **Function:** RX-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập Receptionist/Cashier (không có permission `prescription.create`).
- **Bước thực hiện:** 1) POST `/api/v1/prescriptions` với token role không hợp lệ.
- **Dữ liệu test:** payload đơn hợp lệ.
- **Kết quả mong đợi:** HTTP 403; không tạo đơn.
- **Coverage hiện tại:** MISSING

### TC-RX-006 — Cô lập clinic (RLS) khi tạo/đọc đơn
- **Function:** RX-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor clinic A; tồn tại BN & encounter thuộc clinic B.
- **Bước thực hiện:** 1) Doctor A POST đơn tham chiếu patient/encounter clinic B. 2) Doctor A GET đơn của clinic B.
- **Dữ liệu test:** patient_id/encounter_id thuộc clinic B.
- **Kết quả mong đợi:** Tạo bị từ chối 404/403; GET trả 404 (RLS ẩn dữ liệu clinic khác); không leak.
- **Coverage hiện tại:** MISSING

### TC-RX-007 — Sinh rx_number đúng định dạng RX-YYYY-MM-DD-NNNN
- **Function:** RX-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor đăng nhập; ngày hệ thống 2026-04-30; chưa có đơn trong ngày của clinic A.
- **Bước thực hiện:** 1) Tạo đơn đầu tiên trong ngày. 2) Kiểm tra rx_number.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** rx_number = `RX-2026-04-30-0001` (đúng nguồn); khớp regex `RX-\d{4}-\d{2}-\d{2}-\d{4}`.
- **Coverage hiện tại:** MISSING

### TC-RX-008 — Sequence tăng dần trong ngày & reset sang ngày mới
- **Function:** RX-002
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có `RX-2026-04-30-0001`.
- **Bước thực hiện:** 1) Tạo đơn 2 cùng ngày. 2) Giả lập ngày 2026-05-01, tạo đơn.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Đơn 2 = `...0002`; ngày mới reset = `RX-2026-05-01-0001` (fn_next_rx_number reset hàng ngày).
- **Coverage hiện tại:** MISSING

### TC-RX-009 — rx_number độc lập per-clinic & không trùng khi concurrency
- **Function:** RX-002
- **Loại:** Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và clinic B cùng tạo đơn ngày 2026-04-30.
- **Bước thực hiện:** 1) Tạo song song 2 đơn trong clinic A. 2) Clinic B tạo đơn cùng ngày.
- **Dữ liệu test:** 2 request đồng thời (fn_next_rx_number lock).
- **Kết quả mong đợi:** Không trùng số trong cùng clinic; clinic B có sequence riêng (`...0001`); ràng buộc unique (clinic_id, rx_number) giữ vững.
- **Coverage hiện tại:** MISSING

### TC-RX-010 — Item Internal route pharmacy + tính tiền + reserve
- **Function:** RX-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor đăng nhập; thuốc có trong kho clinic; visit chuyển COMPLETED.
- **Bước thực hiện:** 1) Tạo đơn với item `is_internal=true`. 2) Đưa visit về COMPLETED. 3) Kiểm tra pharmacy queue, invoice, reservation.
- **Dữ liệu test:** 1 item internal.
- **Kết quả mong đợi:** HTTP 201; khi COMPLETED → item vào pharmacy queue + cộng vào invoice + tạo reservation (RX-015).
- **Coverage hiện tại:** MISSING

### TC-RX-011 — Item External không route pharmacy, không invoice, không reserve
- **Function:** RX-003
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor đăng nhập; visit COMPLETED.
- **Bước thực hiện:** 1) Tạo đơn với item `is_internal=false`. 2) COMPLETED visit. 3) Kiểm tra pharmacy queue/invoice/stock.
- **Dữ liệu test:** 1 item external.
- **Kết quả mong đợi:** HTTP 201; không vào pharmacy queue, không vào invoice, không reservation; stock không đổi.
- **Coverage hiện tại:** MISSING

### TC-RX-012 — Đơn hỗn hợp internal + external
- **Function:** RX-003
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc internal có tồn kho; visit COMPLETED.
- **Bước thực hiện:** 1) Tạo đơn 2 items: 1 internal + 1 external. 2) COMPLETED.
- **Dữ liệu test:** mixed.
- **Kết quả mong đợi:** Chỉ item internal vào pharmacy queue + invoice + reserve; item external chỉ ghi đơn; tổng tiền = chỉ internal.
- **Coverage hiện tại:** MISSING

### TC-RX-013 — Liều dùng sáng/trưa/chiều/tối + thời điểm ăn render chuẩn
- **Function:** RX-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor đăng nhập.
- **Bước thực hiện:** 1) Tạo item schedule sáng=1, tối=1, timing=`after_meal`. 2) GET đơn.
- **Dữ liệu test:** Sáng 1 + Tối 1, sau ăn.
- **Kết quả mong đợi:** HTTP 201; lưu đủ 4 buổi (chỉ sáng/tối active) + timing; render text chuẩn `Sáng 1 viên + Tối 1 viên, sau ăn`.
- **Coverage hiện tại:** MISSING

### TC-RX-014 — Liều không hợp lệ (toàn 0 hoặc âm) → từ chối
- **Function:** RX-004
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Doctor đăng nhập.
- **Bước thực hiện:** 1) Tạo item tất cả buổi = 0; 2) Tạo item buổi âm.
- **Dữ liệu test:** all-zero; negative dose.
- **Kết quả mong đợi:** HTTP 422; báo phải có ≥1 buổi với liều > 0.
- **Coverage hiện tại:** MISSING

### TC-RX-015 — Timing không thuộc enum cho phép
- **Function:** RX-004
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Doctor đăng nhập.
- **Bước thực hiện:** 1) Tạo item với timing=`midnight`.
- **Dữ liệu test:** timing ngoài {before_meal, after_meal}.
- **Kết quả mong đợi:** HTTP 422.
- **Coverage hiện tại:** MISSING

### TC-RX-016 — Auto-tính qty = (số buổi) × số ngày × liều
- **Function:** RX-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit
- **Tiền điều kiện:** Hàm tính qty có sẵn.
- **Bước thực hiện:** 1) Tính với Sáng+Tối (2 buổi), 1 viên/buổi, 5 ngày.
- **Dữ liệu test:** 2 × 5 × 1 = 10.
- **Kết quả mong đợi:** qty = 10 (đúng ví dụ nguồn).
- **Coverage hiện tại:** MISSING

### TC-RX-017 — Liều lẻ/làm tròn theo đóng gói
- **Function:** RX-005
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Tính với Sáng 0.5 + Tối 0.5, 3 ngày.
- **Dữ liệu test:** (0.5+0.5) × 3 = 3.
- **Kết quả mong đợi:** qty = 3.
- **Coverage hiện tại:** MISSING

### TC-RX-018 — Override qty thủ công (kê dư)
- **Function:** RX-005
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor đăng nhập.
- **Bước thực hiện:** 1) Tạo item với qty override khác giá trị auto.
- **Dữ liệu test:** auto=10, override=14.
- **Kết quả mong đợi:** Lưu qty=14; đánh dấu manual override; không bị auto ghi đè.
- **Coverage hiện tại:** MISSING

### TC-RX-019 — Cảnh báo dị ứng khi kê thuốc trùng allergens của BN
- **Function:** RX-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN có allergies chứa hoạt chất Penicillin; kê Amoxicillin (allergen penicillin).
- **Bước thực hiện:** 1) Tạo/preview đơn với Amoxicillin.
- **Dữ liệu test:** allergy = Penicillin.
- **Kết quả mong đợi:** Response trả cảnh báo dị ứng (warning, không hard-block — cho override kèm lý do); nếu override → audit override event.
- **Coverage hiện tại:** MISSING

### TC-RX-020 — Không cảnh báo khi thuốc an toàn
- **Function:** RX-006
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN dị ứng Penicillin; kê Paracetamol.
- **Bước thực hiện:** 1) Preview đơn Paracetamol.
- **Dữ liệu test:** allergy = Penicillin, drug = Paracetamol.
- **Kết quả mong đợi:** Không có cảnh báo dị ứng.
- **Coverage hiện tại:** MISSING

### TC-RX-021 — Match allergy chỉ đọc hồ sơ BN clinic hiện tại (RLS)
- **Function:** RX-006
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor clinic A.
- **Bước thực hiện:** 1) Đảm bảo cross-check allergy chỉ đọc allergies của BN thuộc clinic A.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Không đọc allergy của BN clinic khác; kết quả chính xác theo clinic context.
- **Coverage hiện tại:** MISSING

### TC-RX-022 — Cảnh báo tương tác thuốc trong đơn (v2)
- **Function:** RX-007
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có master data drug_interaction; kê 2 thuốc tương tác mức major.
- **Bước thực hiện:** 1) Preview đơn 2 thuốc tương tác.
- **Dữ liệu test:** Paracetamol + Warfarin (major).
- **Kết quả mong đợi:** Trả cảnh báo interaction kèm severity; mức major → block require override.
- **Coverage hiện tại:** MISSING

### TC-RX-023 — Không cảnh báo khi không có tương tác (v2)
- **Function:** RX-007
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Kê 2 thuốc không có record interaction.
- **Bước thực hiện:** 1) Preview đơn.
- **Dữ liệu test:** cặp thuốc an toàn.
- **Kết quả mong đợi:** Không cảnh báo interaction.
- **Coverage hiện tại:** MISSING

### TC-RX-024 — Cảnh báo chống chỉ định với bệnh nền (v2)
- **Function:** RX-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN chronic_conditions = suy thận; kê NSAIDs (contraindication suy thận).
- **Bước thực hiện:** 1) Preview đơn.
- **Dữ liệu test:** condition vs drug contraindication.
- **Kết quả mong đợi:** Trả cảnh báo drug-condition.
- **Coverage hiện tại:** MISSING

### TC-RX-025 — Không cảnh báo khi không có chống chỉ định (v2)
- **Function:** RX-008
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN không có bệnh nền liên quan.
- **Bước thực hiện:** 1) Preview đơn.
- **Dữ liệu test:** drug an toàn với condition.
- **Kết quả mong đợi:** Không cảnh báo.
- **Coverage hiện tại:** MISSING

### TC-RX-026 — In đơn thuốc layout A5 đủ trường pháp lý
- **Function:** RX-009
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đơn đã tạo; user có quyền in.
- **Bước thực hiện:** 1) GET `/api/v1/prescriptions/{id}/print?size=A5`.
- **Dữ liệu test:** size=A5.
- **Kết quả mong đợi:** HTTP 200; PDF/HTML chứa tên+địa chỉ clinic, BN (tên/tuổi/giới/mã), chẩn đoán, danh sách thuốc + liều/cách dùng/số lượng, lời dặn, ngày tái khám, chữ ký BS + SCC.
- **Coverage hiện tại:** MISSING

### TC-RX-027 — In đơn layout A4 và in nhiệt 80mm
- **Function:** RX-009
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đơn đã tạo.
- **Bước thực hiện:** 1) GET print size=A4. 2) GET print size=80mm (máy in nhiệt).
- **Dữ liệu test:** size=A4; size=80mm.
- **Kết quả mong đợi:** HTTP 200 cả hai; layout đúng khổ.
- **Coverage hiện tại:** MISSING

### TC-RX-028 — In đơn không thuộc clinic → 404 (RLS)
- **Function:** RX-009
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User clinic A; đơn thuộc clinic B.
- **Bước thực hiện:** 1) GET print đơn clinic B.
- **Dữ liệu test:** id đơn clinic B.
- **Kết quả mong đợi:** HTTP 404; không leak nội dung.
- **Coverage hiện tại:** MISSING

### TC-RX-029 — In QR code verify đơn (v2)
- **Function:** RX-010
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đơn đã tạo.
- **Bước thực hiện:** 1) In đơn có QR (rx_id + signature). 2) Gọi endpoint verify với scan token.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Bản in chứa QR; verify (cần auth scan token) trả chi tiết đơn hợp lệ.
- **Coverage hiện tại:** MISSING

### TC-RX-030 — Verify QR đơn bị tamper/sai chữ ký (v2)
- **Function:** RX-010
- **Loại:** Security
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Gọi verify với QR token bị sửa hoặc thiếu auth scan token.
- **Dữ liệu test:** payload QR tamper / không auth.
- **Kết quả mong đợi:** HTTP 400/401/404; báo không hợp lệ; chống làm giả đơn.
- **Coverage hiện tại:** MISSING

### TC-RX-031 — Doctor edit đơn ở trạng thái trước dispense
- **Function:** RX-011
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn DRAFT/CREATED (chưa DISPENSED).
- **Bước thực hiện:** 1) PATCH đơn: đổi liều item 1, add item mới, remove item 2. 2) GET lại.
- **Dữ liệu test:** sửa liều + add/remove item.
- **Kết quả mong đợi:** HTTP 200; thay đổi lưu đúng; audit `prescription.updated`; reservation cập nhật tương ứng (RX-015).
- **Coverage hiện tại:** MISSING

### TC-RX-032 — Doctor không edit được đơn đã DISPENSED → 409
- **Function:** RX-011
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn ở trạng thái DISPENSED; user là doctor (không có `rx.amend`).
- **Bước thực hiện:** 1) PATCH đơn đã phát.
- **Dữ liệu test:** đổi liều.
- **Kết quả mong đợi:** HTTP 409/403; từ chối; state không đổi.
- **Coverage hiện tại:** MISSING

### TC-RX-033 — Admin có perm rx.amend tạo amendment sau dispense
- **Function:** RX-011
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn DISPENSED; user admin có permission `rx.amend`.
- **Bước thực hiện:** 1) POST/PATCH amend đơn với lý do.
- **Dữ liệu test:** đổi liều + reason.
- **Kết quả mong đợi:** HTTP 200; tạo bản amendment ghi rõ thay đổi (before/after); audit chặt chẽ; bản gốc giữ nguyên.
- **Coverage hiện tại:** MISSING

### TC-RX-034 — Edit đơn khi chưa auth → 401
- **Function:** RX-011
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) PATCH đơn không kèm token.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING

### TC-RX-035 — Edit đơn bởi role không có quyền → 403
- **Function:** RX-011
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đăng nhập role không có `prescription.update`/`rx.amend`.
- **Bước thực hiện:** 1) PATCH đơn.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 403.
- **Coverage hiện tại:** MISSING

### TC-RX-036 — Edit đơn cross-clinic → 404 (RLS)
- **Function:** RX-011
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor clinic A; đơn clinic B.
- **Bước thực hiện:** 1) PATCH đơn clinic B.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 404; không sửa được.
- **Coverage hiện tại:** MISSING

### TC-RX-037 — Cancel đơn trước dispense + release reservation
- **Function:** RX-012
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn DRAFT/CREATED có reservation; lý do bắt buộc.
- **Bước thực hiện:** 1) POST `/api/v1/prescriptions/{id}/cancel` kèm reason. 2) Kiểm tra reservation.
- **Dữ liệu test:** reason="Bệnh nhân từ chối".
- **Kết quả mong đợi:** HTTP 200; status CANCELLED; reservation release → available_qty phục hồi; audit `prescription.cancelled`.
- **Coverage hiện tại:** MISSING

### TC-RX-038 — Cancel thiếu lý do → từ chối
- **Function:** RX-012
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đơn trước dispense.
- **Bước thực hiện:** 1) POST cancel không kèm reason.
- **Dữ liệu test:** reason rỗng.
- **Kết quả mong đợi:** HTTP 422; lý do bắt buộc; không cancel.
- **Coverage hiện tại:** MISSING

### TC-RX-039 — Không cancel đơn đã DISPENSED → 409
- **Function:** RX-012
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn DISPENSED.
- **Bước thực hiện:** 1) POST cancel.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 409; không cancel; gợi ý refund qua billing.
- **Coverage hiện tại:** MISSING

### TC-RX-040 — Cancel đơn cross-clinic → 404 (RLS)
- **Function:** RX-012
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor clinic A; đơn clinic B.
- **Bước thực hiện:** 1) POST cancel đơn clinic B.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 404.
- **Coverage hiện tại:** MISSING

### TC-RX-041 — Lịch sử đơn của BN sort by date desc
- **Function:** RX-013
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN clinic A có ≥3 đơn ở các thời điểm khác nhau.
- **Bước thực hiện:** 1) GET `/api/v1/patients/{id}/prescriptions`.
- **Dữ liệu test:** 3 đơn.
- **Kết quả mong đợi:** HTTP 200; danh sách 3 đơn giảm dần theo ngày; mỗi row có rx_number, doctor, diagnosis, số thuốc, total, status.
- **Coverage hiện tại:** MISSING

### TC-RX-042 — Phân trang lịch sử đơn
- **Function:** RX-013
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN có >page_size đơn.
- **Bước thực hiện:** 1) GET page=1&size=10. 2) GET page=2.
- **Dữ liệu test:** size=10, 15 đơn.
- **Kết quả mong đợi:** Trang 1 = 10, trang 2 = 5; total=15; không trùng.
- **Coverage hiện tại:** MISSING

### TC-RX-043 — Lịch sử đơn khi chưa auth → 401
- **Function:** RX-013
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) GET lịch sử đơn BN.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING

### TC-RX-044 — Lịch sử đơn BN của clinic khác → 404 (RLS)
- **Function:** RX-013
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor clinic A; BN thuộc clinic B.
- **Bước thực hiện:** 1) GET lịch sử đơn của BN clinic B.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 404; không trả đơn nào.
- **Coverage hiện tại:** MISSING

### TC-RX-045 — Lưu đơn thành template để dùng lại (v2)
- **Function:** RX-014
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor đăng nhập.
- **Bước thực hiện:** 1) POST tạo template từ đơn hiện tại với tên + items. 2) GET list template.
- **Dữ liệu test:** name="Cảm cúm thông thường" (Paracetamol + Vitamin C + Bromhexin).
- **Kết quả mong đợi:** HTTP 201; template lưu danh sách thuốc/liều; xuất hiện trong list (riêng hoặc chia sẻ trong clinic).
- **Coverage hiện tại:** MISSING

### TC-RX-046 — Áp template 1-click vào visit (v2)
- **Function:** RX-014
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã có template.
- **Bước thực hiện:** 1) Tạo đơn từ template_id cho visit.
- **Dữ liệu test:** template_id.
- **Kết quả mong đợi:** Đơn mới prefill đúng thuốc/liều của template; vẫn validate stock (RX-016) và allergy (RX-006).
- **Coverage hiện tại:** MISSING

### TC-RX-047 — Template private không hiện cho clinic/user khác (RLS, v2)
- **Function:** RX-014
- **Loại:** Security
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Template private tạo bởi doctor X ở clinic A.
- **Bước thực hiện:** 1) Doctor clinic B list template. 2) Doctor Y (cùng clinic A nhưng template private) list.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Clinic B không thấy; template private chỉ chủ sở hữu thấy; áp dụng cross-clinic → 404.
- **Coverage hiện tại:** MISSING

### TC-RX-048 — Reserve stock khi đơn internal được tạo (visit COMPLETED)
- **Function:** RX-015
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc on_hand=100, available=100; đơn internal qty=15; visit COMPLETED.
- **Bước thực hiện:** 1) Đưa visit về COMPLETED. 2) Kiểm tra stock_movement & available_qty.
- **Dữ liệu test:** reserve 15.
- **Kết quả mong đợi:** Tạo stock_movement type=`RESERVED`; available_qty = 85; on_hand vẫn 100 (chưa trừ thật); không vào pharmacy out cho tới khi DISPENSED.
- **Coverage hiện tại:** MISSING

### TC-RX-049 — Reserve vượt tồn khả dụng → từ chối (chống oversell)
- **Function:** RX-015
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** available_qty = 10.
- **Bước thực hiện:** 1) Tạo đơn internal qty=20 → COMPLETED.
- **Dữ liệu test:** reserve 20 > 10.
- **Kết quả mong đợi:** HTTP 409/422 thiếu tồn; không tạo reservation; available không đổi. (Theo Database Error Handling Protocol: đây là ràng buộc nghiệp vụ kho, không phải bug query — không tự ý nới lỏng.)
- **Coverage hiện tại:** MISSING

### TC-RX-050 — Edit đơn tăng qty → reserve thêm phần chênh
- **Function:** RX-015
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn internal đang reserve 10; available còn 50.
- **Bước thực hiện:** 1) Edit qty 10 → 25.
- **Dữ liệu test:** delta +15.
- **Kết quả mong đợi:** reserved tăng thêm 15; available giảm 15; nếu vượt tồn → 409.
- **Coverage hiện tại:** MISSING

### TC-RX-051 — Cancel đơn → release reservation
- **Function:** RX-015
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn internal reserve 15.
- **Bước thực hiện:** 1) Cancel đơn. 2) Kiểm tra stock.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** stock_movement release; available phục hồi +15; on_hand không đổi.
- **Coverage hiện tại:** MISSING

### TC-RX-052 — Reserve đồng thời nhiều đơn (race, không oversell)
- **Function:** RX-015
- **Loại:** Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** available_qty = 10.
- **Bước thực hiện:** 1) 2 đơn song song mỗi đơn reserve 8 (COMPLETED đồng thời).
- **Dữ liệu test:** 8 + 8 > 10.
- **Kết quả mong đợi:** Chỉ 1 đơn reserve thành công; đơn kia 409; tổng reserved ≤ 10 (row lock/atomic, không oversell).
- **Coverage hiện tại:** MISSING

### TC-RX-053 — Reservation tôn trọng RLS clinic
- **Function:** RX-015
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Kho riêng từng clinic.
- **Bước thực hiện:** 1) Đơn clinic A reserve chỉ trừ kho clinic A.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Kho clinic B không bị ảnh hưởng; stock_movement gắn đúng clinic_id.
- **Coverage hiện tại:** MISSING

### TC-RX-054 — Hiển thị tồn khả dụng + chip màu theo ngưỡng min_stock
- **Function:** RX-016
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Doctor đăng nhập; thuốc A available=320 (>min), thuốc B available=12 (<min), thuốc C available=0.
- **Bước thực hiện:** 1) GET search/list thuốc trong form kê đơn (EMR Tab Kê đơn).
- **Dữ liệu test:** A=320, B=12, C=0.
- **Kết quả mong đợi:** HTTP 200; A chip emerald "Còn 320 viên ✓"; B chip amber "Còn 12 viên ⚠"; C chip red "Hết hàng ✕"; available = inventory.available_qty - reserved.
- **Coverage hiện tại:** MISSING

### TC-RX-055 — Tooltip breakdown theo lô FEFO (HSD)
- **Function:** RX-016
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Thuốc có ≥2 lô khác HSD.
- **Bước thực hiện:** 1) Hover card thuốc → xem tooltip.
- **Dữ liệu test:** Lô 240425 (HSD 04/2027) 200v; Lô 240310 (HSD 03/2027) 120v.
- **Kết quả mong đợi:** Tooltip hiện breakdown theo lô sắp xếp FEFO (HSD sớm trước).
- **Coverage hiện tại:** MISSING

### TC-RX-056 — Kê quá tồn → banner cảnh báo + nút đề xuất thay thế
- **Function:** RX-016
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Thuốc available=12; BS nhập qty=20.
- **Bước thực hiện:** 1) Nhập qty vượt tồn.
- **Dữ liệu test:** qty 20 > 12.
- **Kết quả mong đợi:** Banner "Vượt tồn kho — chỉ kê được 12 viên" + button "Đề xuất thuốc tương đương" (gọi MED-013 substitute).
- **Coverage hiện tại:** MISSING

### TC-RX-057 — Filter "Chỉ hiện thuốc còn hàng" default ON; External không hiển thị stock
- **Function:** RX-016
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Có thuốc hết hàng và thuốc external.
- **Bước thực hiện:** 1) Mở autocomplete search (default filter ON). 2) Chọn thuốc external.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** Mặc định ẩn thuốc hết hàng (toggle OFF để hiện); thuốc External chỉ hiện "Mua ngoài", không chip stock.
- **Coverage hiện tại:** MISSING

### TC-RX-058 — Stock chỉ của clinic hiện tại (RLS) + chưa auth → 401
- **Function:** RX-016
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + E2E (httpx)
- **Tiền điều kiện:** Doctor clinic A; clinic B có tồn khác.
- **Bước thực hiện:** 1) GET list thuốc kê đơn (auth clinic A). 2) GET list không token.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** (1) Chỉ trả tồn kho clinic A, không leak số liệu clinic B; (2) không token → HTTP 401.
- **Coverage hiện tại:** MISSING

---

## 3. Tổng kết coverage

- **Tổng function:** 16 (RX-001 … RX-016).
- **Tổng test case:** 58.
- **COVERED:** 0 · **PARTIAL:** 0 · **MISSING:** 16.
- **Lý do:** Toàn bộ RX trong nguồn ở trạng thái ⬜ TODO (v1: TASK-011/012/005) hoặc 💡 IDEA (v2: RX-007/008/010/014). Chưa xác minh được test tự động PASS trong `clinic-cms-merge` tại phiên này. Catalog đóng vai trò đặc tả test mục tiêu; cần đối chiếu repo merge (modules prescription + inventory/pharmacy + tests) để nâng lên COVERED/PARTIAL.
- **Trọng tâm rủi ro:** RX-015 (reserve/release stock — oversell, race condition, edit-delta) và RX-002 (rx_number unique per-clinic/per-day, concurrency) là rủi ro P0 cao nhất, cần test trước. State machine edit/cancel theo trạng thái DISPENSED (RX-011/RX-012) và quyền `rx.amend` cũng cần phủ kỹ negative.
