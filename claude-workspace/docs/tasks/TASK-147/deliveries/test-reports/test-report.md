# TASK-147 — Báo cáo test

**Ngày**: 2026-09-04
**Người test**: claude-main
**Code under test**: `clinic-cms-web` commit `a644ac3` (branch `dev`), BE `_dev-be` branch `dev` (`a4b5478`)

## Môi trường

Stack E2E isolated, build từ chính worktree `_dev-be` / `_dev-web`:

```
docker compose -p clinic_e2e -f docker-compose.e2e.yml up -d --build
```

| Thành phần | Địa chỉ |
|---|---|
| API | http://127.0.0.1:8010 |
| UI (vite build + serve) | http://127.0.0.1:5180 |
| Postgres / Redis | 5455 / 6395 |

**Bắt buộc dùng `127.0.0.1`, không dùng `localhost`.** Trên máy này `localhost`
phân giải ra IPv6 `::1` trước, mà port mapping của Docker chỉ nghe IPv4:

- Python `urllib` → treo đủ 8s rồi `TimeoutError` (cùng lúc `curl` trả về 0.27s
  vì curl tự fallback sang IPv4).
- Trình duyệt → `net::ERR_CONNECTION_RESET`.

Kéo theo: image UI bake `VITE_API_URL=http://localhost:8010` lúc build nên phải
build lại với `--build-arg VITE_API_URL=http://127.0.0.1:8010`, và origin
`http://127.0.0.1:5180` không nằm trong `CORS_ORIGINS` của
`docker-compose.e2e.yml` → thêm qua file override `docker-compose.e2e.cors.yml`
(không sửa file gốc).

---

## 1. E2E tầng API — toàn luồng khám bệnh

Script: [`../test-cases/e2e_clinical_flow.py`](../test-cases/e2e_clinical_flow.py)
Mỗi bước gọi bằng đúng role thật (`recept_anh`, `dr_nguyen`, `pharm_cuong`, `cashier_em`).

```
python -X utf8 docs/tasks/TASK-147/deliveries/test-cases/e2e_clinical_flow.py
```

**Kết quả: 21 PASS / 0 FAIL / 0 INFO**

| Bước | Nội dung | Kết quả |
|---|---|---|
| 0 | Đăng nhập 5 role | PASS |
| 1a/1b | Lễ tân tạo bệnh nhân + lượt khám (`WAITING`) | PASS |
| 2 | Bác sĩ bắt đầu khám → `IN_PROGRESS` | PASS |
| 3 | Chọn thuốc còn tồn (Spironolactone 25mg, tồn 150) | PASS |
| 4a/4b | Kê đơn nội viện → đơn `draft`, item `in_house`, PIB `reserved` | PASS |
| **5** | **Cấp phát khi đơn `draft` → bị chặn 400 `BUSINESS_RULE_VIOLATION`** | PASS |
| **6** | **Hàng đợi Chờ cấp phát KHÔNG chứa đơn `draft`** | PASS |
| **7** | **Bác sĩ gửi đơn → `pending`** ← mắt xích TASK-147 | PASS |
| **8** | **Hàng đợi BÂY GIỜ chứa đơn** (BN + BS + SL giữ đúng) | PASS |
| 9a/9b | Dược sĩ cấp phát → đơn `dispensed` | PASS |
| 9c | Tồn kho giảm 148 → 146 | PASS |
| 9d | `stock_movement`: `prescription_out -2  98->96` | PASS |
| 10 | `complete-emr` → `AWAITING_PAYMENT` | PASS |
| 11a-c | Hóa đơn `draft` → `issued` → thu 4.800đ | PASS |
| 12a/12b | Không còn blocker → lượt khám tự đóng `COMPLETED` | PASS |

Bước 5 và 6 là hai guard của TASK-142 — vẫn giữ nguyên hiệu lực sau khi vá,
đúng chủ đích: fix của TASK-147 **thêm bước gửi đơn**, không nới guard.

Bước 9d kiểm ở tầng DB vì **không có endpoint nào expose `stock_movement`**
(`/inventory/movements` → 404; route thật không tồn tại). Script chạy
`docker exec clinic_e2e_postgres psql` để đọc bảng, tự chuyển INFO nếu không gọi
được docker.

---

## 2. E2E tầng UI — phần code TASK-147 thực sự sửa

Fix của TASK-147 là **FE-only**, nên E2E API ở trên không chạm tới nó. Hai nhánh
code được lái thật bằng browser (Playwright).

### 2.1 Nhánh A — nút "Gửi đơn thuốc" ở tab Kê đơn

`PrescriptionTab.tsx`. Vào bằng `dr_nguyen`, lượt khám `20260904-005`, đơn `draft`.

| Kiểm tra | Kết quả |
|---|---|
| Thanh action có đủ: In đơn thuốc / Hủy đơn thuốc / Lưu đơn thuốc / **Gửi đơn thuốc** | PASS — ảnh `task147-01-send-button.png` |
| Bấm → hộp confirm "Gửi đơn thuốc sang nhà thuốc? Sau khi gửi, đơn không sửa được nữa — muốn kê lại phải hủy đơn." | PASS |
| Sau khi xác nhận: đơn → `pending` (API xác nhận) | PASS |
| Nút "Gửi đơn thuốc" biến mất, banner `pendingBanner` hiện lên | PASS |
| `dr_nguyen` gọi `/pharmacy/pending-dispense` → 403 | PASS (RBAC đúng — bác sĩ không có `pharmacy.dispense`) |

### 2.2 Hàng đợi nhà thuốc + cấp phát bằng UI

`PendingDispensePage`. Vào bằng `pharm_cuong`, `#/pharmacy/pending`.

| Kiểm tra | Kết quả |
|---|---|
| Hàng đợi hiện "Chờ cấp phát (1)" với đúng bệnh nhân | PASS — ảnh `task147-02-pharmacy-queue.png` |
| Modal chi tiết: Spironolactone 25mg, 1 viên x 2 lần/ngày, 2 viên, Nhà thuốc, "Đã đặt lô" | PASS |
| Xác nhận cấp phát → hàng đợi về "Chờ cấp phát (0)" | PASS |
| Đơn → `dispensed`; `stock_movement`: `prescription_out -3 → 96->94` | PASS |

Trước khi vá, màn này **rỗng vĩnh viễn** vì `list_pending` lọc `status='pending'`
mà không đơn nào rời được `draft`.

### 2.3 Nhánh B — nút "Cấp phát thuốc" ở Khu làm việc (đúng lỗi user báo)

`ClinicalWorkspacePage.tsx`. Dựng lại chính xác kịch bản lỗi: lượt khám
`20260904-006` ở `AWAITING_PAYMENT`, đơn thuốc **vẫn `draft`** (bác sĩ chưa gửi),
vào bằng `admin` (có cả `prescription.write` và `pharmacy.dispense`).

| Kiểm tra | Kết quả |
|---|---|
| Panel quyết toán hiện chip "Chờ cấp phát" + nút "Cấp phát thuốc" | PASS — ảnh `task147-03-workspace-before.png` |
| Bấm → confirm → **không có toast lỗi `BUSINESS_RULE_VIOLATION`** | PASS |
| Đơn `draft` → auto-submit → `dispensed`; chip đổi "Đã cấp phát" | PASS |
| `stock_movement`: `prescription_out -3  94->91` | PASS |
| Blocker "Còn 1 thuốc nhà thuốc chưa cấp phát" biến mất, chỉ còn blocker hóa đơn | PASS |
| Bấm "Tạo hóa đơn & thu tiền mặt" → lượt khám `COMPLETED` | PASS |

Đây chính là request đã sinh ra lỗi ban đầu. Trước khi vá, bước này trả về:

```
BUSINESS_RULE_VIOLATION — Không thể cấp phát đơn thuốc ở trạng thái 'draft'
(yêu cầu 'pending' — bác sĩ phải gửi đơn trước khi cấp phát).
```

---

## 3. Unit test

| Việc | Kết quả |
|---|---|
| `PrescriptionTab-submit.test.tsx` (mới, 5 test) | 5/5 pass |
| Cùng 5 test chạy trên code CHƯA vá | **fail** — xác nhận test bắt được lỗi |
| 11 file test liên quan (`PrescriptionTab-*`, `ConsultationPage`, `PendingDispensePage`, `PrintPrescription*`), chạy từng file | pass hết |
| `eslint` 2 file sửa | sạch |

---

## 4. Hạn chế / việc chưa làm được

1. **`tsc --noEmit` chưa chạy được.** OOM: `Fatal error ... Fatal process out of
   memory: Zone`. Nguyên nhân đo được: máy hết commit charge —
   `CommitLimit 49.1 GB / CommitFree 0.3 GB` (RAM vật lý vẫn còn 7.7 GB trống).
   31 tiến trình `python` chiếm 11.1 GB, `vmmem` 7.1 GB, 14 `java` 6.2 GB.
   Cùng nguyên nhân này làm `vitest run` full suite và `docker build` fail
   (`VirtualAlloc failed with errno=1455` = `ERROR_COMMITMENT_LIMIT`).
   Docker Desktop tự restart giữa phiên, sau đó CommitFree lên 4.6 GB và build
   mới thành công.
2. **Full vitest suite chưa chạy**, chỉ chạy được từng file. Khi ép nhiều file
   test vào cùng một thread (`--poolOptions.threads.singleThread=true`) thì
   `PrescriptionTab-dosage-unit` fail do nhiễm state chéo giữa các file — đã đối
   chiếu bằng `git stash`, lỗi này **có sẵn trước** TASK-147.
3. **`ClinicalWorkspacePage` vẫn chưa có unit test** trong repo. Nhánh B (§2.3)
   hiện chỉ được phủ bởi E2E UI ở trên, không có unit test.
4. Đơn thuốc của lượt khám `20260904-007` còn ở `draft` trong DB E2E (dùng để
   chụp ảnh §2.1), cố ý để lại.

## Kết luận

Luồng khám bệnh chạy trọn vòng ở cả tầng API (21/21) và tầng UI (3 nhánh, gồm
đúng kịch bản lỗi user báo). Guard của TASK-142 còn nguyên hiệu lực. Chưa
typecheck được toàn bộ project — xem §4.1.


---

## 5. Chạy lại sau khi release lên `main` (2026-09-05)

Sau khi merge `dev` → `main` (`c9906a2`, đã push). Kiểm `git diff origin/dev -- src/`
trên worktree `_main-web` → **rỗng**, tức source trên `main` giống hệt `dev`, nên
container UI đang chạy chính là code đã lên prod.

| Hạng mục | Kết quả |
|---|---|
| E2E API toàn luồng (lượt khám `20260905-001`) | **21 PASS / 0 FAIL** — tồn 141→139, `stock_movement -2  91->89` |
| UI nhánh A — nút "Gửi đơn thuốc" (`20260905-002`) | PASS — đơn → `pending`, nút biến mất, banner hiện |
| UI — hàng đợi nhà thuốc + cấp phát | PASS — "Chờ cấp phát (1)" → (0), `stock_movement -2  89->87` |
| UI nhánh B — nút "Cấp phát thuốc" ở Khu làm việc (`20260905-003`, đơn còn `draft`) | PASS — auto-submit → `dispensed`, chip "Đã cấp phát", **không có** `BUSINESS_RULE_VIOLATION`, blocker biến mất |

Cả 2 đơn UI đều `dispensed`, kế toán kho liên tục và khớp: `91→89→87→84`.

Guard TASK-142 vẫn nguyên hiệu lực (bước 5 và 6 của E2E API).

§4 (hạn chế) không đổi: **`tsc --noEmit` vẫn chưa chạy được**, và
`ClinicalWorkspacePage` vẫn chưa có unit test.
