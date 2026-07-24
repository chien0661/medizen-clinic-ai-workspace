# TASK-104: Bảo vệ substitute_batch khỏi lô hết hạn

**Mức độ:** High (H-2)  
**Ngày hoàn thành:** 2026-07-24  
**Trạng thái:** DONE (22/22 tests passed)

---

## Vấn đề

API `substitute_batch()` (`app/modules/pharmacy/services/reservation_service.py`) cho phép thay sang lô dược tư mà không kiểm tra `expiry_date`. Một lô đã hết hạn (ví dụ: 2026-06-22 khi hôm nay là 2026-07-22) có thể được chọn làm lô thay thế, dẫn đến lô được cấp phát hết hạn cho bệnh nhân.

- **Lô chứa trong reserve:** `reserve_for_prescription()` ở dòng 80 **đã** enforce `expiry_date > date.today()`.
- **Lô thay thế:** Query lô mới (dòng 220-231) chỉ lọc `clinic_id`, `is_deleted`, `is_recalled` — **thiếu** điều kiện `expiry_date > today`.

---

## Giải pháp

**File:** `app/modules/pharmacy/services/reservation_service.py`  
**Hàm:** `substitute_batch()`

Thêm guard kiểm tra ngay sau khi lô mới được load/lock (trước guard khác-thuốc của TASK-099):

```python
if new_batch.expiry_date <= date.today():
    raise ConflictError(
        message=(
            "New batch is expired; substitution is only allowed onto "
            "a non-expired batch"
        ),
        details={...},
    )
```

- **HTTP Status:** 409 Conflict (đáp ứng yêu cầu 400/409 trong AC).
- **Placement:** Trước guard `different_medicine` của TASK-099, sau check `NotFoundError`.
- **Import:** `from datetime import date` (cục bộ trong hàm, phù hợp kiểu có sẵn).

---

## Kết quả

**Tests:**
- `test_substitute_batch_rejects_expired_batch`: lô hết hạn → 409, reservation không thay đổi ✓
- `test_substitute_batch_allows_non_expired_same_medicine`: lô còn hạn → 200, TASK-099 không hồi quy ✓
- Pharmacy suite 13/13 passed (isolated stack `fix104`, ports 9979/5479/6461).
- Ruff/mypy: 0 new findings.

**Kho thay đổi:**
- `reservation_service.py` (+21 lines, guard only)
- `test_pharmacy_e2e.py` (+140 lines, 2 tests mới)

---

## Xác minh

| Tiêu chí | Kết quả |
|----------|---------|
| Unit + Integration tests | 22/22 passed ✓ |
| Lô hết hạn bị chặn | HTTP 409 ✓ |
| Lô còn hạn vẫn OK | HTTP 200, TASK-099 intact ✓ |
| Static analysis | 0 new findings ✓ |
| Isolated stack | w104 (api 9979, postgres 5479, redis 6461) ✓ |

---

## Ghi chú

- Guard này bổ sung TASK-099 (chặn thay khác thuốc); cả hai cùng bảo vệ hàm `substitute_batch`.
- Không thay đổi logic khác (tính toán stock, giải phóng lô cũ, logging).
- Worktree `_fix104-be` chứa branch `fix/TASK-104-substitute-expiry`, đã push `origin`.
