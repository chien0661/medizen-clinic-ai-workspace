# Test Case Catalog — PHRM · Nhà thuốc & Cấp phát

**Nguồn:** function_list_data.py (group PHRM, dòng 950–1015) + clinic_management_function_list.md (mục 12) + business_analysis (rule self-dispense, dòng 207) + TASK-012 (Inventory & Pharmacy module — deliveries/api-specs + test-report) + BUG-014 (TASK-049).
**Phạm vi:** 13 functions (PHRM-001 … PHRM-013).  **Tổng test case:** 48.  **Ngày:** 2026-05-30.

> **Endpoint thực tế** (TASK-012 api-spec, base `/api/v1`):
> - `GET  /pharmacy/queue` — hàng đợi đơn chờ cấp (PHRM-001)
> - `GET  /pharmacy/dispense/{rx_id}` — chi tiết cấp phát + gợi ý lô FEFO (PHRM-002/003/007/008)
> - `POST /pharmacy/dispense/{rx_id}` — xác nhận cấp phát (PHRM-002/004/005/006/011)
> - `POST /pharmacy/dispense/{rx_id}/reverse` — hoàn cấp phát (PHRM-012)
> - `GET  /pharmacy/dispense/{rx_id}/history` — lịch sử/audit cấp phát (PHRM-009)
> - Permission: `pharmacy.dispense`; rule chống tự cấp đơn do chính mình kê (BA self-approve).
>
> **Trạng thái nguồn vs thực tế:** function_list_data ghi PHRM-001..008/011/012 = ⬜ TODO, PHRM-009 = ✅ DONE, PHRM-010/013 = 💡 IDEA. NHƯNG TASK-012 (test-report 2026-04-15) cho thấy module Inventory+Pharmacy đã ship và 14 test PHRM PASS (queue, lot+FEFO, multi-lot, partial, atomic decrement, expiry/insufficient warning, audit, auto-invoice, reverse, RLS, permission, self-dispense prevention). BUG-014 (TASK-049, RESOLVED) xác nhận BE dispense flow + trừ kho + audit chạy đúng end-to-end. Vì vậy Coverage dưới đây gán theo **bằng chứng test thực tế của TASK-012** (ưu tiên hơn cột Status nguồn vốn đã lỗi thời).
> **Lưu ý:** repo backend `../clinic-cms-merge` KHÔNG tồn tại trên đĩa từ môi trường agent này (mọi path trả "No such file or directory"); coverage dựa trên TASK-012 deliverables thay vì đọc trực tiếp test file. Test mới nên đối chiếu lại với suite TASK-012 để tránh trùng và bổ sung các edge còn thiếu (concurrency, double-reverse, expired-lot hard block).

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| PHRM-001 | Pending dispense queue | ⬜ TODO (thực tế DONE @TASK-012) | TC-PHRM-001, TC-PHRM-002, TC-PHRM-003, TC-PHRM-004 | COVERED |
| PHRM-002 | Dispense screen (confirm + chọn lô) | ⬜ TODO (thực tế DONE @TASK-012/049) | TC-PHRM-005, TC-PHRM-006, TC-PHRM-007, TC-PHRM-008, TC-PHRM-009 | COVERED |
| PHRM-003 | Lot selection (FEFO suggested, override) | ⬜ TODO (thực tế DONE @TASK-012) | TC-PHRM-010, TC-PHRM-011, TC-PHRM-012, TC-PHRM-013 | PARTIAL |
| PHRM-004 | Multi-lot dispense | ⬜ TODO (thực tế DONE @TASK-012) | TC-PHRM-014, TC-PHRM-015, TC-PHRM-016 | PARTIAL |
| PHRM-005 | Partial dispense (out of stock) | ⬜ TODO (thực tế DONE @TASK-012) | TC-PHRM-017, TC-PHRM-018, TC-PHRM-019 | COVERED |
| PHRM-006 | Stock auto-decrement (atomic) | ⬜ TODO (thực tế DONE @TASK-012) | TC-PHRM-020, TC-PHRM-021, TC-PHRM-022, TC-PHRM-023 | PARTIAL |
| PHRM-007 | Cảnh báo HSD lô | ⬜ TODO (thực tế DONE @TASK-012) | TC-PHRM-024, TC-PHRM-025, TC-PHRM-026 | PARTIAL |
| PHRM-008 | Cảnh báo thiếu hàng | ⬜ TODO (thực tế DONE @TASK-012) | TC-PHRM-027, TC-PHRM-028 | COVERED |
| PHRM-009 | Dispense audit | ✅ DONE | TC-PHRM-029, TC-PHRM-030, TC-PHRM-031, TC-PHRM-032 | COVERED |
| PHRM-010 | In nhãn thuốc (POS printer) | 💡 IDEA (v2) | TC-PHRM-033, TC-PHRM-034 | MISSING |
| PHRM-011 | Auto add to invoice | ⬜ TODO (thực tế DONE @TASK-012/013) | TC-PHRM-035, TC-PHRM-036, TC-PHRM-037, TC-PHRM-038 | PARTIAL |
| PHRM-012 | Reverse dispense (hoàn tồn kho) | ⬜ TODO (thực tế DONE @TASK-012) | TC-PHRM-039, TC-PHRM-040, TC-PHRM-041, TC-PHRM-042, TC-PHRM-043 | PARTIAL |
| PHRM-013 | Substitute confirm (DS đề xuất, BS duyệt) | 💡 IDEA (v2) | TC-PHRM-044, TC-PHRM-045, TC-PHRM-046, TC-PHRM-047, TC-PHRM-048 | MISSING |

**Tổng kết coverage:** COVERED = 5 (PHRM-001, 002, 005, 008, 009) · PARTIAL = 6 (PHRM-003, 004, 006, 007, 011, 012) · MISSING = 2 (PHRM-010, 013).

---

## 2. Chi tiết Test Cases

### TC-PHRM-001 — Lấy hàng đợi đơn chờ cấp phát (happy path)
- **Function:** PHRM-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) / E2E (httpx)
- **Tiền điều kiện:** Đăng nhập Pharmacist (perm `pharmacy.dispense`), clinic A có ≥2 đơn trạng thái NEW.
- **Bước thực hiện:** 1) GET `/api/v1/pharmacy/queue`. 2) Đọc response.
- **Dữ liệu test:** 2 đơn từ 2 lần khám.
- **Kết quả mong đợi:** 200; list có visit + BN + doctor + số thuốc + total + status + thời gian; đủ 2 đơn NEW.
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#1 "Pending dispense queue" PASS).

### TC-PHRM-002 — Lọc queue theo trạng thái New/Partial/Done today (edge)
- **Function:** PHRM-001
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Có đơn NEW, PARTIAL và DISPENSED trong ngày.
- **Bước thực hiện:** 1) GET `/pharmacy/queue?status=partial`. 2) GET `?status=done_today`.
- **Dữ liệu test:** 3 đơn 3 trạng thái.
- **Kết quả mong đợi:** 200; mỗi filter chỉ trả đúng nhóm trạng thái; đơn ngoài filter không lọt.
- **Coverage hiện tại:** PARTIAL (queue đã test nhưng chưa rõ test riêng từng filter status).

### TC-PHRM-003 — Truy cập queue chưa đăng nhập (security 401)
- **Function:** PHRM-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi Authorization.
- **Bước thực hiện:** 1) GET `/pharmacy/queue` không token.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** 401 Unauthorized.
- **Coverage hiện tại:** PARTIAL (permission check có test ở mức 403; 401 chưa nêu riêng).

### TC-PHRM-004 — Cô lập clinic trên queue (security/RLS)
- **Function:** PHRM-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn NEW thuộc clinic A; user context clinic B (Pharmacist).
- **Bước thực hiện:** 1) GET queue trong context clinic B. 2) GET `/pharmacy/dispense/{rx_id}` của đơn clinic A.
- **Dữ liệu test:** rx_id của clinic A.
- **Kết quả mong đợi:** Queue clinic B không chứa đơn clinic A (RLS); GET chi tiết đơn clinic A trả 404/403.
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#12 "RLS isolation (dispense)" PASS).

### TC-PHRM-005 — Mở chi tiết & xác nhận cấp phát đơn (happy path)
- **Function:** PHRM-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) / E2E
- **Tiền điều kiện:** Pharmacist; đơn NEW 2 item, tồn đủ.
- **Bước thực hiện:** 1) GET `/pharmacy/dispense/{rx_id}` (chi tiết item + lô FEFO). 2) POST `/pharmacy/dispense/{rx_id}` với map item→lô→qty.
- **Dữ liệu test:** 2 item, mỗi item 1 lô đủ.
- **Kết quả mong đợi:** 200; rx.status=DISPENSED, dispensed_at, dispensed_by; trừ kho + ghi audit + add invoice (atomic).
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#2 "Dispense with lot selection" PASS; BUG-014 xác nhận flow end-to-end).

### TC-PHRM-006 — Thiếu quyền `pharmacy.dispense` (security 403)
- **Function:** PHRM-002
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User role Receptionist (không có `pharmacy.dispense`).
- **Bước thực hiện:** 1) POST `/pharmacy/dispense/{rx_id}`.
- **Dữ liệu test:** đơn NEW hợp lệ.
- **Kết quả mong đợi:** 403; tồn kho không đổi; không tạo dispense record.
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#13 "Permission check (pharmacy.dispense)" PASS).

### TC-PHRM-007 — Người kê đơn không được tự cấp phát (business rule self-approve, 403)
- **Function:** PHRM-002
- **Loại:** Negative (business rule)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) / E2E
- **Tiền điều kiện:** User X vừa kê đơn (RX) vừa có quyền Pharmacist; đơn do chính X kê.
- **Bước thực hiện:** 1) Đăng nhập X. 2) POST `/pharmacy/dispense/{rx_id}` cho đơn X kê.
- **Dữ liệu test:** rx.prescriber_id == current_user (BA dòng 207: nút 'Phát đơn' bị disabled, BE check 403).
- **Kết quả mong đợi:** 403 "Không thể tự duyệt — cần DS khác duyệt"; đơn vẫn NEW; không trừ kho.
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#14 "Self-dispense prevention" PASS).

### TC-PHRM-008 — Cấp lại đơn đã DISPENSED (negative, state/idempotency)
- **Function:** PHRM-002
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đơn đã DISPENSED.
- **Bước thực hiện:** 1) POST `/pharmacy/dispense/{rx_id}` lần 2.
- **Dữ liệu test:** đơn đã dispensed.
- **Kết quả mong đợi:** 409 Conflict (hoặc 422); KHÔNG trừ kho lần 2; trạng thái không đổi.
- **Coverage hiện tại:** PARTIAL (happy dispense đã test; state-guard chống dispense lần 2 chưa nêu riêng).

### TC-PHRM-009 — Confirm dispense chưa đăng nhập (security 401)
- **Function:** PHRM-002
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token.
- **Bước thực hiện:** 1) POST `/pharmacy/dispense/{rx_id}` không Authorization.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** 401.
- **Coverage hiện tại:** PARTIAL (auth bắt buộc cho mọi endpoint nhưng 401 chưa test riêng cho POST dispense).

### TC-PHRM-010 — Gợi ý lô theo FEFO (happy path)
- **Function:** PHRM-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Thuốc có 3 lô HSD khác nhau, đều còn tồn.
- **Bước thực hiện:** 1) GET `/pharmacy/dispense/{rx_id}` đọc lô gợi ý mặc định.
- **Dữ liệu test:** lô A (HSD 2026-06), B (2026-09), C (2027-01).
- **Kết quả mong đợi:** Lô mặc định = HSD sớm nhất còn đủ qty (FEFO = lô A); danh sách lô sắp HSD tăng dần.
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#3 "FEFO auto-suggestion" PASS).

### TC-PHRM-011 — Override lô thủ công khác FEFO (edge)
- **Function:** PHRM-003
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Như TC-PHRM-010; DS chủ động chọn lô C thay lô A.
- **Bước thực hiện:** 1) POST dispense với lot_id = lô C.
- **Dữ liệu test:** lô C còn đủ tồn.
- **Kết quả mong đợi:** 200; cho phép override; trừ kho đúng lô C; audit ghi lô được chọn (không phải FEFO mặc định).
- **Coverage hiện tại:** PARTIAL (FEFO suggestion đã test; nhánh override thủ công chưa nêu riêng).

### TC-PHRM-012 — Loại lô hết HSD khỏi gợi ý + chặn cấp (negative)
- **Function:** PHRM-003
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lô A đã quá HSD, lô B còn hạn.
- **Bước thực hiện:** 1) GET gợi ý lô. 2) Cố POST dispense lô A.
- **Dữ liệu test:** lô A HSD < today.
- **Kết quả mong đợi:** Lô A không là gợi ý mặc định; nếu cố cấp lô hết hạn → 422 (hoặc cảnh báo cứng). Lưu ý: detail PHRM-007 nói DS vẫn dispense được lô gần hết hạn — cần làm rõ ranh giới "gần hết hạn" vs "đã hết hạn".
- **Coverage hiện tại:** PARTIAL (expiry warning đã test ở PHRM-007; chặn cứng lô đã hết hạn chưa xác nhận).

### TC-PHRM-013 — Gợi ý lô cô lập clinic (security/RLS)
- **Function:** PHRM-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lô của thuốc có ở cả clinic A & B; user context clinic B.
- **Bước thực hiện:** 1) GET gợi ý lô trong context clinic B.
- **Dữ liệu test:** lot của clinic A.
- **Kết quả mong đợi:** Chỉ trả lô của clinic B; lô clinic A không xuất hiện (RLS).
- **Coverage hiện tại:** PARTIAL (RLS dispense đã test tổng quát; riêng gợi ý lô cross-tenant chưa nêu rõ).

### TC-PHRM-014 — Cấp 1 dòng thuốc từ nhiều lô (happy path)
- **Function:** PHRM-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Item cần 30; lô A còn 20, lô B còn 50.
- **Bước thực hiện:** 1) POST dispense phân bổ lô A:20 + lô B:10.
- **Dữ liệu test:** tổng phân bổ = 30 = số kê.
- **Kết quả mong đợi:** 200; trừ lô A 20, lô B 10; dispense record 2 dòng lot; 2 stock_movement type=OUT.
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#4 "Multi-lot dispense" PASS).

### TC-PHRM-015 — Tổng phân bổ multi-lot ≠ số kê (negative)
- **Function:** PHRM-004
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Item cần 30; phân bổ lô A:20 + lô B:5 (=25), và case 35.
- **Bước thực hiện:** 1) POST dispense tổng 25; 2) POST tổng 35.
- **Dữ liệu test:** tổng < và > số kê.
- **Kết quả mong đợi:** 422 cả hai; không trừ kho lô nào (atomic); message nêu tổng không khớp.
- **Coverage hiện tại:** PARTIAL (multi-lot happy đã test; validate tổng lệch chưa nêu riêng).

### TC-PHRM-016 — Một lô vượt tồn trong multi-lot → rollback (edge)
- **Function:** PHRM-004
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lô A còn 20 nhưng phân bổ 25; lô B đủ.
- **Bước thực hiện:** 1) POST dispense phân bổ vượt tồn lô A.
- **Dữ liệu test:** allocation > on_hand lô A.
- **Kết quả mong đợi:** 422; transaction rollback — cả lô A & B không bị trừ.
- **Coverage hiện tại:** PARTIAL (atomic decrement đã test; nhánh rollback khi 1 lô fail trong multi-lot nên xác nhận thêm).

### TC-PHRM-017 — Cấp một phần đơn khi thiếu hàng (happy path)
- **Function:** PHRM-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn 2 thuốc; thuốc B hết hàng hoàn toàn, thuốc A đủ.
- **Bước thực hiện:** 1) POST dispense chỉ thuốc A, đánh dấu B còn nợ.
- **Dữ liệu test:** A dispensed, B remaining.
- **Kết quả mong đợi:** 200; rx.status=PARTIAL; thuốc B đánh dấu nợ; audit + (notify doctor).
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#5 "Partial dispense" PASS).

### TC-PHRM-018 — Cấp tiếp phần còn nợ sau partial (edge)
- **Function:** PHRM-005
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đơn PARTIAL; kho đã nhập thêm thuốc B.
- **Bước thực hiện:** 1) POST dispense phần còn nợ (thuốc B).
- **Dữ liệu test:** B đủ tồn mới.
- **Kết quả mong đợi:** 200; rx.status → DISPENSED; tổng cấp đủ; các dispense record liên kết cùng đơn.
- **Coverage hiện tại:** PARTIAL (partial state đã test; vòng "cấp nốt phần nợ" chưa nêu riêng).

### TC-PHRM-019 — Partial dispense vượt số kê (negative)
- **Function:** PHRM-005
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Item kê 30, đã cấp 10, remaining 20.
- **Bước thực hiện:** 1) POST cấp thêm 25 (> remaining).
- **Dữ liệu test:** qty=25.
- **Kết quả mong đợi:** 422; không trừ kho; không cho cấp vượt số kê.
- **Coverage hiện tại:** PARTIAL (chưa xác nhận guard vượt số kê).

### TC-PHRM-020 — Trừ tồn kho atomic đúng lô (happy path)
- **Function:** PHRM-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lô A on_hand=50.
- **Bước thực hiện:** 1) POST dispense 15 từ lô A. 2) Đọc lại tồn + stock_movement.
- **Dữ liệu test:** qty=15.
- **Kết quả mong đợi:** on_hand lô A=35; stock_movement type=OUT (-15) tham chiếu rx; rx.status=DISPENSED — tất cả trong 1 transaction.
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#6 "Stock decrement (atomic)" PASS).

### TC-PHRM-021 — Trừ kho vượt tồn (negative)
- **Function:** PHRM-006
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lô A on_hand=10.
- **Bước thực hiện:** 1) POST dispense 15 từ lô A.
- **Dữ liệu test:** qty=15 > 10.
- **Kết quả mong đợi:** 422; on_hand không âm, giữ 10; không tạo movement.
- **Coverage hiện tại:** PARTIAL (insufficient-stock warning đã test ở PHRM-008; hard block trừ âm ở mức commit nên xác nhận thêm).

### TC-PHRM-022 — Trừ kho an toàn khi cấp đồng thời (edge — concurrency)
- **Function:** PHRM-006
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lô A on_hand=10; 2 request dispense 8 cùng lúc.
- **Bước thực hiện:** 1) Gửi 2 POST song song trên cùng lô.
- **Dữ liệu test:** 2 × qty=8.
- **Kết quả mong đợi:** Chỉ 1 thành công (on_hand=2); request còn lại 422/409; không over-sell (row lock/optimistic).
- **Coverage hiện tại:** MISSING (TASK-012 không có test concurrency).

### TC-PHRM-023 — Trừ kho cô lập clinic (security/RLS)
- **Function:** PHRM-006
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lô cùng product có ở clinic A & B; user clinic B dispense, truyền lot_id của clinic A.
- **Bước thực hiện:** 1) POST dispense lot_id clinic A trong context clinic B.
- **Dữ liệu test:** lot_id clinic A.
- **Kết quả mong đợi:** Không trừ tồn clinic A; lot clinic A trả 404/403; chỉ thao tác trên lô clinic B.
- **Coverage hiện tại:** PARTIAL (RLS dispense tổng quát đã test; trừ-kho cross-tenant cụ thể nên xác nhận thêm).

### TC-PHRM-024 — Hiển thị "còn N ngày HSD" khi chọn lô (happy path)
- **Function:** PHRM-007
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) / Manual-UI
- **Tiền điều kiện:** Lô HSD = today + 47 ngày.
- **Bước thực hiện:** 1) GET `/pharmacy/dispense/{rx_id}` đọc field cảnh báo HSD.
- **Dữ liệu test:** HSD = 2026-07-16.
- **Kết quả mong đợi:** Trả days_to_expiry=47; UI hiện "Hết hạn 2026-07-16 (còn 47 ngày)".
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#7 "Expiry warning" PASS).

### TC-PHRM-025 — Phân tầng cảnh báo HSD <30 (vàng) / <7 (đỏ) (edge)
- **Function:** PHRM-007
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) / Manual-UI
- **Tiền điều kiện:** 2 lô HSD = today+20 và today+5.
- **Bước thực hiện:** 1) GET chi tiết, đọc cờ mức cảnh báo từng lô.
- **Dữ liệu test:** days_to_expiry=20 và 5.
- **Kết quả mong đợi:** Lô 20 ngày → cờ "warning/vàng"; lô 5 ngày → cờ "danger/đỏ"; cả 2 vẫn cấp được (theo detail).
- **Coverage hiện tại:** PARTIAL (có warning nhưng ngưỡng 30/7 phân tầng chưa xác nhận riêng).

### TC-PHRM-026 — Lô đã hết hạn (negative)
- **Function:** PHRM-007
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Lô HSD < today.
- **Bước thực hiện:** 1) GET chi tiết; 2) cố POST dispense lô hết hạn.
- **Dữ liệu test:** HSD = 2026-05-01.
- **Kết quả mong đợi:** Hiển thị cờ "hết hạn"; hành vi cấp tùy chính sách compliance (block 422 hoặc cho phép có cảnh báo cứng) — phải nhất quán & có log. Cần làm rõ với BA.
- **Coverage hiện tại:** PARTIAL (warning đã test; nhánh "đã hết hạn" cụ thể chưa rõ).

### TC-PHRM-027 — Cảnh báo thiếu hàng "Chỉ còn X, cần Y" (happy path)
- **Function:** PHRM-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Item kê 30; tổng tồn mọi lô = 20.
- **Bước thực hiện:** 1) GET `/pharmacy/dispense/{rx_id}` đọc shortage info.
- **Dữ liệu test:** available=20, needed=30.
- **Kết quả mong đợi:** Trả shortage (available=20, needed=30, shortage=10); UI banner đỏ "Chỉ còn 20 viên, đơn cần 30"; gợi ý chia lô/partial.
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#8 "Insufficient stock warning" PASS).

### TC-PHRM-028 — Đủ hàng thì không cảnh báo (negative/đối chứng)
- **Function:** PHRM-008
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Item kê 30, tồn 100.
- **Bước thực hiện:** 1) GET chi tiết item.
- **Dữ liệu test:** available=100.
- **Kết quả mong đợi:** Không có cờ shortage; cho cấp đủ.
- **Coverage hiện tại:** PARTIAL (warning case đã test; case đối chứng không-cảnh-báo chưa nêu riêng).

### TC-PHRM-029 — Ghi audit khi cấp phát (happy path)
- **Function:** PHRM-009
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Cơ chế audit (TASK-002) chạy; Pharmacist cấp 1 đơn.
- **Bước thực hiện:** 1) POST dispense. 2) GET `/pharmacy/dispense/{rx_id}/history` hoặc query audit_log.
- **Dữ liệu test:** 1 đơn, 1 lô.
- **Kết quả mong đợi:** Audit record ghi who, when, rx_id, medicine, lot, qty, clinic_id; append-only.
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#9 "Dispense audit log" PASS; PHRM-009 nguồn = DONE).

### TC-PHRM-030 — Audit ghi đủ chi tiết khi multi-lot (edge)
- **Function:** PHRM-009
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Cấp 1 item từ 2 lô.
- **Bước thực hiện:** 1) POST multi-lot dispense. 2) Đọc audit/history.
- **Dữ liệu test:** lô A:20 + lô B:10.
- **Kết quả mong đợi:** Audit phản ánh cả 2 lô với qty tương ứng (không gộp mất chi tiết lô).
- **Coverage hiện tại:** PARTIAL (audit + multi-lot đều test riêng; giao của 2 chưa nêu rõ).

### TC-PHRM-031 — Audit/history cô lập clinic (security/RLS)
- **Function:** PHRM-009
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Audit dispense của clinic A; user context clinic B.
- **Bước thực hiện:** 1) GET `/pharmacy/dispense/{rx_id}/history` cho rx clinic A trong context clinic B.
- **Dữ liệu test:** rx_id clinic A.
- **Kết quả mong đợi:** 404/403; không trả audit clinic A (RLS trên audit_log).
- **Coverage hiện tại:** PARTIAL (RLS tổng quát đã test; riêng history cross-tenant nên xác nhận).

### TC-PHRM-032 — Xem history thiếu quyền / chưa auth (security 401/403)
- **Function:** PHRM-009
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) Không token; (b) user không có quyền xem.
- **Bước thực hiện:** 1) GET history cả 2 trường hợp.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** (a) 401; (b) 403.
- **Coverage hiện tại:** PARTIAL (permission có test; 401/403 riêng cho history chưa nêu).

### TC-PHRM-033 — In nhãn thuốc cho từng item (happy path) [v2]
- **Function:** PHRM-010
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI + E2E
- **Tiền điều kiện:** Đơn đã DISPENSED; máy in POS thermal cấu hình.
- **Bước thực hiện:** 1) Trigger in nhãn cho từng item.
- **Dữ liệu test:** đơn 2 item.
- **Kết quả mong đợi:** Mỗi item 1 nhãn 50×30mm gồm tên BN + tên thuốc + liều dùng + cách dùng + ngày cấp.
- **Coverage hiện tại:** MISSING (💡 IDEA v2, chưa làm).

### TC-PHRM-034 — In nhãn cho item chưa cấp (negative) [v2]
- **Function:** PHRM-010
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đơn còn NEW/PARTIAL.
- **Bước thực hiện:** 1) Trigger in nhãn cho item chưa cấp.
- **Dữ liệu test:** item chưa dispensed.
- **Kết quả mong đợi:** Chặn/422 — chỉ in nhãn cho item đã cấp.
- **Coverage hiện tại:** MISSING (💡 IDEA v2).

### TC-PHRM-035 — Tự thêm thuốc nội viện vào draft invoice (happy path)
- **Function:** PHRM-011
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn có thuốc bán nội viện; visit có draft invoice.
- **Bước thực hiện:** 1) POST dispense. 2) Đọc draft invoice của visit.
- **Dữ liệu test:** thuốc nội viện unit_price=X, qty=10.
- **Kết quả mong đợi:** 200; invoice thêm line (medicine_id, qty=10, unit_price=X, thành tiền=10X); tham chiếu dispense.
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#10 "Auto-add to invoice" PASS; PHRM-011 thuộc TASK-013).

### TC-PHRM-036 — Thuốc ngoại (không bán nội viện) không vào invoice (negative)
- **Function:** PHRM-011
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Item đánh dấu external/không chargeable.
- **Bước thực hiện:** 1) POST dispense item ngoại.
- **Dữ liệu test:** is_internal=false.
- **Kết quả mong đợi:** 200 cấp được nhưng KHÔNG thêm line invoice.
- **Coverage hiện tại:** PARTIAL (auto-add đã test; nhánh loại trừ thuốc ngoại chưa nêu riêng).

### TC-PHRM-037 — Auto-add khi visit chưa có draft invoice (edge)
- **Function:** PHRM-011
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit chưa có draft invoice.
- **Bước thực hiện:** 1) POST dispense thuốc nội viện.
- **Dữ liệu test:** không tồn tại invoice.
- **Kết quả mong đợi:** Tạo mới draft invoice rồi thêm line (hoặc lỗi rõ ràng theo design); không tạo orphan line.
- **Coverage hiện tại:** PARTIAL (chưa xác nhận nhánh thiếu invoice).

### TC-PHRM-038 — Invoice cô lập clinic (security/RLS)
- **Function:** PHRM-011
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Visit/invoice thuộc clinic A; thao tác context clinic B.
- **Bước thực hiện:** 1) Dispense gắn invoice cross-tenant.
- **Dữ liệu test:** invoice_id clinic A.
- **Kết quả mong đợi:** Không thêm được line vào invoice clinic A; 404/403 (RLS).
- **Coverage hiện tại:** PARTIAL (RLS chung đã test; riêng auto-invoice cross-tenant chưa nêu).

### TC-PHRM-039 — Hoàn tồn kho khi reverse đơn đã cấp (happy path)
- **Function:** PHRM-012
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn DISPENSED, đã trừ lô A 15 (on_hand=35).
- **Bước thực hiện:** 1) POST `/pharmacy/dispense/{rx_id}/reverse`. 2) Đọc lại tồn lô A + invoice.
- **Dữ liệu test:** reverse toàn bộ.
- **Kết quả mong đợi:** 200; on_hand lô A=50; stock_movement type=RETURN (+15) về lô gốc; rx → reversed/cancelled; remove items khỏi invoice; audit reverse.
- **Coverage hiện tại:** COVERED (TASK-012 PHRM#11 "Reverse dispense" PASS).

### TC-PHRM-040 — Reverse đơn chưa cấp (negative)
- **Function:** PHRM-012
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đơn còn NEW.
- **Bước thực hiện:** 1) POST reverse.
- **Dữ liệu test:** đơn NEW.
- **Kết quả mong đợi:** 409/422 — không có gì để hoàn; tồn không đổi.
- **Coverage hiện tại:** PARTIAL (reverse happy đã test; guard reverse-khi-chưa-cấp chưa nêu riêng).

### TC-PHRM-041 — Reverse hai lần (edge — idempotency)
- **Function:** PHRM-012
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn đã reversed.
- **Bước thực hiện:** 1) POST reverse lần 2.
- **Dữ liệu test:** đơn reversed.
- **Kết quả mong đợi:** 409; KHÔNG cộng tồn lần 2 (tránh inflate kho).
- **Coverage hiện tại:** MISSING (TASK-012 không nêu double-reverse).

### TC-PHRM-042 — Reverse gỡ line khỏi invoice (edge — liên đới BILL)
- **Function:** PHRM-012
- **Loại:** Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đơn DISPENSED đã auto-add line vào draft invoice.
- **Bước thực hiện:** 1) POST reverse. 2) Đọc invoice.
- **Dữ liệu test:** invoice còn draft / invoice đã chốt.
- **Kết quả mong đợi:** Invoice draft → line bị gỡ; invoice đã thanh toán → chặn reverse hoặc yêu cầu refund (theo design); không để tồn-tiền lệch.
- **Coverage hiện tại:** PARTIAL (reverse có "remove items khỏi invoice" trong detail nhưng nhánh invoice-đã-chốt chưa xác nhận).

### TC-PHRM-043 — Reverse thiếu quyền / chưa auth / cross-tenant (security 401/403/404)
- **Function:** PHRM-012
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) không token; (b) user không có quyền reverse; (c) rx của clinic khác.
- **Bước thực hiện:** 1) POST reverse cho cả 3 trường hợp.
- **Dữ liệu test:** rx_id hợp lệ / cross-tenant.
- **Kết quả mong đợi:** (a) 401; (b) 403; (c) 404/403; tồn không đổi mọi case.
- **Coverage hiện tại:** PARTIAL (permission + RLS có test chung; bộ 401/403/404 riêng cho reverse chưa đầy đủ).

### TC-PHRM-044 — DS đề xuất thuốc thay thế (happy path) [v2]
- **Function:** PHRM-013
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đơn có item hết hàng; DS đề xuất thuốc cùng hoạt chất.
- **Bước thực hiện:** 1) POST đề xuất substitution (item gốc + thuốc thay thế + lý do).
- **Dữ liệu test:** product_orig, product_sub cùng hoạt chất.
- **Kết quả mong đợi:** 201; substitution request `pending_doctor_approval`; chưa trừ kho; notify bác sĩ.
- **Coverage hiện tại:** MISSING (💡 IDEA v2).

### TC-PHRM-045 — Bác sĩ duyệt/từ chối đề xuất (happy path/state) [v2]
- **Function:** PHRM-013
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Có substitution request pending; user role Doctor.
- **Bước thực hiện:** 1) POST approve; 2) (case khác) POST reject.
- **Dữ liệu test:** request_id pending.
- **Kết quả mong đợi:** approve → request `approved`, đơn amend ghi rõ substitution, sẵn sàng dispense; reject → `rejected`, đơn giữ nguyên; audit chặt.
- **Coverage hiện tại:** MISSING (💡 IDEA v2).

### TC-PHRM-046 — DS tự duyệt đề xuất của mình (security/business 403) [v2]
- **Function:** PHRM-013
- **Loại:** Security (self-approve rule)
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** DS X tạo substitution request; X cố tự approve.
- **Bước thực hiện:** 1) X POST approve chính request của mình.
- **Dữ liệu test:** requester == approver.
- **Kết quả mong đợi:** 403 — phải do người khác (bác sĩ) duyệt (BA self-approve rule).
- **Coverage hiện tại:** MISSING (💡 IDEA v2).

### TC-PHRM-047 — Cấp thuốc thay thế khi chưa duyệt (negative/state) [v2]
- **Function:** PHRM-013
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Substitution request còn `pending_doctor_approval`.
- **Bước thực hiện:** 1) POST dispense thuốc thay thế khi chưa duyệt.
- **Dữ liệu test:** request pending.
- **Kết quả mong đợi:** 422/409 — không cho cấp thuốc thay thế khi chưa được duyệt.
- **Coverage hiện tại:** MISSING (💡 IDEA v2).

### TC-PHRM-048 — Substitution chưa auth / thiếu quyền (security 401/403) [v2]
- **Function:** PHRM-013
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) không token; (b) user không có quyền đề xuất/duyệt.
- **Bước thực hiện:** 1) POST đề xuất / approve cho cả 2 trường hợp.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** (a) 401; (b) 403.
- **Coverage hiện tại:** MISSING (💡 IDEA v2).

---

## 3. Ghi chú & rủi ro

- **Coverage dựa trên TASK-012 deliverables, không phải đọc trực tiếp test file:** Repo backend `../clinic-cms-merge` không truy cập được từ môi trường này (mọi path "No such file or directory"), và function_list_data.py vẫn ghi PHRM = ⬜ TODO (lỗi thời). Bằng chứng tin cậy nhất là TASK-012 test-report (47/47 PASS, 14 case PHRM) + BUG-014 RESOLVED. Trước khi đóng catalog, reviewer nên chạy lại suite TASK-012 trên repo backend hiện hành để xác nhận các case COVERED chưa bị regression.
- **Gap thực sự cần bổ sung (đang MISSING dù module đã ship):** TC-PHRM-022 (concurrency over-sell), TC-PHRM-041 (double-reverse idempotency), và toàn bộ PHRM-010/013 (v2 chưa làm). Đây là rủi ro tiền/kho cao nhất.
- **Điểm cần làm rõ với BA:** ranh giới "lô gần hết hạn (vẫn cấp, có cảnh báo)" vs "lô đã hết hạn (block?)" — TC-PHRM-012/026; và hành vi reverse khi invoice đã thanh toán — TC-PHRM-042.
- **Self-approve rule** (BA dòng 207): người kê đơn không được tự cấp phát chính đơn mình kê — đã được test (TC-PHRM-007 COVERED) và lặp lại cho substitution (TC-PHRM-046, v2).
