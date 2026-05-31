# Review — Bộ kịch bản vận hành theo vai trò (TASK-052)

**Ngày review:** 2026-05-31
**Phạm vi:** 4 file trong `deliveries/test-cases/scenarios/` (happy-path, variants, exceptions, cross-role-denial) — tổng 33 kịch bản.
**Đối chiếu:** schema BE thực tế trong `clinic-cms-merge` (`app/modules/billing/schemas/invoice_schemas.py`, `app/modules/visits/schemas/visit_schemas.py`) + route grep `app/modules/billing/api/`, `app/modules/visits/api/`.
**Kết luận:** Bộ kịch bản **đạt chất lượng tốt**; nghiệp vụ/luồng/vai trò chính xác. Chỉ cần đồng bộ một số **payload field** cho khớp BE trước khi tự động hóa (tránh lỗi 422).

---

## 1. Đánh giá tổng thể

| Tiêu chí | Nhận xét |
|---|---|
| Cấu trúc | 33 KB / 4 nhóm (Happy 5, Variants 7, Exceptions 8, RBAC-denial 13); mã `SC-*`, ưu tiên P0/P1/P2 rõ ràng |
| Mapping vai trò→tài khoản | Khớp `seed_demo_data.py` (admin, dr_*, nurse_*, recept_*, pharm_*, cashier_em) ✓ |
| State machine | Dùng đúng enum thực tế `WAITING_VITAL → VITAL_DONE → IN_CONSULTATION → {WAITING_PHARMACY/WAITING_PAYMENT} → COMPLETED`, không dùng tên BA rút gọn ✓ |
| Assertion | Mỗi KB có điểm kiểm chứng + RLS đa tenant + 403 phân quyền chéo + truy vết function (VIS/RX/BILL/PHRM/RBAC...) ✓ |
| Tự nhận GAP | Doc tự cảnh báo drift đã biết (BILL-016 void chưa hoàn kho, VAT hardcode 0, VTL chưa ship, RX-006 chưa check dị ứng) + ghi rõ "endpoint là GỢI Ý, phải đối chiếu OpenAPI" ✓ |

---

## 2. Sai lệch payload/field cần sửa (đã verify với schema BE)

| # | Vị trí kịch bản | Doc đang ghi | BE thực tế (verified) |
|---|---|---|---|
| 1 | Mọi bước thanh toán: SC-HP-01 #11, SC-HP-05 #8–9, SC-EXC-01 #3, SC-EXC-06 #3–5 | `{method: CASH/CARD/BANK_TRANSFER}` | field là **`payment_method`**; giá trị **lowercase**: `cash/card/transfer/momo/vnpay/other`. `BANK_TRANSFER` → **`transfer`** (`invoice_schemas.py:80-91`) |
| 2 | SC-EXC-02 #5 (hủy visit) | `POST /visits/{id}/cancel {reason}` | field bắt buộc **`cancel_reason`** (min_length=3, không blank) — không phải `reason` (`visit_schemas.py:79-87`) |
| 3 | SC-EXC-07 (giảm giá) | `{discount_percent: 10/50}` | schema dùng **`discount_amount`** + bắt buộc **`discount_reason`** khi amount>0; **không thấy** field `discount_percent` (`invoice_schemas.py:25-41`) |
| 4 | Void HĐ: SC-EXC-01 #6, SC-RBAC-06/07 | `{reason}` | ✓ ĐÚNG — void dùng `reason`; refund dùng `reason` (`invoice_schemas.py:96,130,134`) |

> Ghi chú: billing module CÓ route POST hóa đơn/payment/void (`app/modules/billing/api/routes.py`). Không có route con `vitals`/`invoice` dưới `app/modules/visits/api/` → vitals nằm ở module riêng, invoice ở `/billing`. Các path `POST /visits/{id}/vitals`, `POST /invoices` trong doc đúng tinh thần "gợi ý" — chốt path thật từ OpenAPI trước khi tự động hóa.

---

## 3. Phát hiện thêm (drift FE↔BE, ngoài phạm vi doc — nên mở bug)

- **Queue status drift:** kịch bản query `GET /visits?status=WAITING_VITAL` (đúng enum). Nhưng FE `clinic-cms-web/src/pages/doctor/QueuePage.tsx` query `status=WAITING` và `IN_PROGRESS` (tên cũ). Nếu BE chỉ chấp nhận enum mới (`WAITING_VITAL`/`IN_CONSULTATION`) → **hàng đợi bác sĩ có thể rỗng**. → Cần verify BE có map alias WAITING→WAITING_VITAL không; nếu không, sửa FE.
- **Encoding script E2E:** `scripts/e2e_final_v2.py` in tiếng Việt ra stdout → `UnicodeEncodeError (cp1252)` trên Windows khi chạy `python ...> file`. Cần set `PYTHONIOENCODING=utf-8` hoặc `sys.stdout.reconfigure(encoding="utf-8")` trước khi chạy lại bộ E2E.

---

## 4. Khuyến nghị

1. **Đồng bộ payload field** (mục 2.1–2.3) trong 4 file scenarios cho khớp BE — ưu tiên trước khi tự động hóa để tránh 422 giả.
2. **Verify queue-status drift** (mục 3) — quyết định sửa FE hay BE map alias.
3. **Fix encoding** script E2E trước lần chạy `e2e_final_v2.py` kế tiếp.
4. Giữ nguyên các assertion GAP (BILL-016, VAT, VTL, RX-006) — đúng là kỳ vọng nghiệp vụ, để FAIL→ghi bug khi chạy, KHÔNG sửa expected.

**Trạng thái:** Kịch bản APPROVED về mặt nghiệp vụ; cần 1 vòng đồng bộ field + verify drift trước khi dùng làm đầu vào tự động hóa.
