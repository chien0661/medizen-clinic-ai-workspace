# Test Case Catalog — Clinic CMS (TASK-052)

**Phạm vi:** 461 function trên 26 group (19 functional + 7 non-functional/NFR), nguồn `scripts/function_list_data.py`.
**Thuộc:** TASK-052 — Bộ test case catalog tổng cho Clinic CMS.
**Ngày phát hành:** 2026-05-30.

> **Cách đếm số liệu (đếm thực tế từ từng catalog trên đĩa):**
> - **#Functions** = số dòng ma trận truy vết bắt đầu bằng `| <PREFIX>-<số>` (prefix-agnostic, gồm cả các tiền tố viết tắt).
> - **#TestCases** = số heading test case (`### TC-` / `#### TC-`).
> - **COVERED / PARTIAL / MISSING** = đếm theo cột Coverage trên các dòng ma trận.
>
> **Cột Coverage là ước lượng** suy ra từ status nguồn (`function_list_data.py`) đối chiếu với test đã viết — **không** phản ánh test đã chạy pass thực tế. Nhiều catalog ghi rõ "(cần xác minh test file)": **Test Engineer phải xác minh lại** trực tiếp với file test (`clinic-cms-merge/tests`) và mã nguồn (`clinic-cms-merge/app`) trước khi chốt.
>
> **Lưu ý tiền tố ma trận:** một số group dùng tiền tố viết tắt khác mã group (PATIENT→`PAT`, VISIT→`VIS`, VITAL→`VTL`, TENANT→`TEN`/`TENT` lẫn lộn). Số liệu dưới đây đã đếm prefix-agnostic nên không bị sót. Tuy nhiên việc trộn tiền tố trong file TENANT cần được chuẩn hóa.

---

## Functional Catalogs (19)

| Group | File | #Functions | #TestCases | COVERED | PARTIAL | MISSING |
|-------|------|-----------:|-----------:|--------:|--------:|--------:|
| AUTH | [functional/auth-test-catalog.md](functional/auth-test-catalog.md) | 22 | 74 | 9 | 2 | 11 |
| RBAC | [functional/rbac-test-catalog.md](functional/rbac-test-catalog.md) | 18 | 60 | 10 | 0 | 8 |
| PATIENT | [functional/patient-test-catalog.md](functional/patient-test-catalog.md) | 22 | 64 | 12 | 7 | 3 |
| APPT | [functional/appt-test-catalog.md](functional/appt-test-catalog.md) | 17 | 56 | 6 | 2 | 9 |
| VISIT | [functional/visit-test-catalog.md](functional/visit-test-catalog.md) | 14 | 42 | 1 | 12 | 1 |
| VITAL | [functional/vital-test-catalog.md](functional/vital-test-catalog.md) | 14 | 46 | 0 | 0 | 14 |
| SVC | [functional/svc-test-catalog.md](functional/svc-test-catalog.md) | 9 | 42 | 0 | 1 | 8 |
| MED | [functional/med-test-catalog.md](functional/med-test-catalog.md) | 18 | 60 | 0 | 0 | 18 |
| RX | [functional/rx-test-catalog.md](functional/rx-test-catalog.md) | 16 | 58 | 0 | 0 | 16 |
| PHRM | [functional/phrm-test-catalog.md](functional/phrm-test-catalog.md) | 13 | 48 | 5 | 6 | 2 |
| BILL | [functional/bill-test-catalog.md](functional/bill-test-catalog.md) | 23 | 78 | 0 | 0 | 23 |
| HR | [functional/hr-test-catalog.md](functional/hr-test-catalog.md) | 22 | 52 | 11 | 0 | 11 |
| RPT | [functional/rpt-test-catalog.md](functional/rpt-test-catalog.md) | 18 | 54 | 0 | 0 | 18 |
| NOTI | [functional/noti-test-catalog.md](functional/noti-test-catalog.md) | 15 | 43 | 0 | 1 | 14 |
| CFG | [functional/cfg-test-catalog.md](functional/cfg-test-catalog.md) | 17 | 58 | 0 | 11 | 6 |
| DATA | [functional/data-test-catalog.md](functional/data-test-catalog.md) | 11 | 42 | 0 | 2 | 9 |
| DIAG | [functional/diag-test-catalog.md](functional/diag-test-catalog.md) | 9 | 31 | 0 | 0 | 9 |
| NAV | [functional/nav-test-catalog.md](functional/nav-test-catalog.md) | 8 | 27 | 0 | 1 | 7 |
| THEME | [functional/theme-test-catalog.md](functional/theme-test-catalog.md) | 3 | 16 | 0 | 3 | 0 |
| **Cộng functional** | | **289** | **951** | **54** | **48** | **187** |

---

## Non-functional Catalogs (7)

| Group | File | #Functions | #TestCases | COVERED | PARTIAL | MISSING |
|-------|------|-----------:|-----------:|--------:|--------:|--------:|
| NFR | [non-functional/nfr-test-catalog.md](non-functional/nfr-test-catalog.md) | 46 | 78 | 5 | 8 | 34 |
| TENANT | [non-functional/tenant-test-catalog.md](non-functional/tenant-test-catalog.md) | 14 | 38 | 3 | 4 | 7 |
| AUDIT | [non-functional/audit-test-catalog.md](non-functional/audit-test-catalog.md) | 15 | 40 | 9 | 0 | 6 |
| JOB | [non-functional/job-test-catalog.md](non-functional/job-test-catalog.md) | 14 | 32 | 0 | 2 | 12 |
| INT | [non-functional/int-test-catalog.md](non-functional/int-test-catalog.md) | 20 | 52 | 0 | 2 | 18 |
| SUB | [non-functional/sub-test-catalog.md](non-functional/sub-test-catalog.md) | 25 | 58 | 0 | 0 | 25 |
| PLT | [non-functional/plt-test-catalog.md](non-functional/plt-test-catalog.md) | 24 | 60 | 0 | 0 | 24 |
| **Cộng non-functional** | | **175** | **358** | **17** | **16** | **126** |

---

## TỔNG

| Chỉ số | Giá trị |
|--------|--------:|
| Tổng #Functions (đếm thực tế từ ma trận) | **464** |
| Tổng #TestCases | **1.281** |
| COVERED | **87** |
| PARTIAL | **68** |
| MISSING | **306** |
| **% COVERED** | **18.8%** |

*(% COVERED = 87 / 464. Nguồn danh nghĩa 461 function; phép đếm ma trận trả 464 — chênh ~3 dòng do vài function tách hàng phụ và tiền tố trộn trong file TENANT. Độ phủ thấp vì bộ catalog mới ở giai đoạn liệt kê khung test: phần lớn function vẫn MISSING/PARTIAL, chưa hoàn thiện viết case + chưa đối chiếu file test thực tế.)*

---

## Gap ưu tiên xử lý

### MISSING cao nhất — chưa có test case (ưu tiên viết mới)

| Hạng | Group | MISSING | Ghi chú |
|------|-------|--------:|---------|
| 1 | NFR (non-functional) | 34 | Hiệu năng/bảo mật/khả dụng — khối lượng lớn nhất |
| 2 | SUB (non-functional) | 25 | Gói thuê bao/tính phí — rủi ro doanh thu, P0 |
| 3 | PLT (non-functional) | 24 | Nền tảng/quản trị hệ thống |
| 4 | BILL (functional) | 23 | Hóa đơn/thanh toán — rủi ro tài chính, P0 |
| 5 | INT (non-functional) | 18 | Tích hợp ngoài (cổng thanh toán, SMS, lab) |
| 6 | MED / RPT (functional) | 18 mỗi nhóm | Danh mục thuốc & báo cáo — chưa có case nào |
| 7 | RX (functional) | 16 | Kê đơn — an toàn thuốc, P0 |
| 8 | VITAL / NOTI (functional) | 14 mỗi nhóm | Sinh hiệu (TODO v1) & thông báo |
| 9 | JOB (non-functional) | 12 | Job nền/scheduler |
| 10 | AUTH / HR (functional) | 11 mỗi nhóm | Xác thực multi-clinic & nhân sự |

**Top cần xử lý ngay (P0):** BILL (MISSING 23 — tài chính), SUB (25 — doanh thu), RX (16 — an toàn thuốc), INT (18 — cổng thanh toán). Đây là các nhóm vừa MISSING cao vừa thuộc rủi ro tiền/an toàn dữ liệu.

### Function v1 (DONE) đã có nhưng test còn PARTIAL — bổ sung trước

Function đã ship/DONE nhưng test chỉ phủ một phần (BE done, FE/flow chưa, hoặc thiếu nhánh negative/edge/permission/đa tenant). Ưu tiên nâng PARTIAL→COVERED trước khi viết mới cho MISSING:

| Group | PARTIAL | Hành động đề xuất |
|-------|--------:|-------------------|
| VISIT | 12 | Hầu hết function DONE nhưng đang PARTIAL — hoàn thiện state machine, NO_SHOW/CANCELLED, auto-gen visit_number |
| CFG | 11 | Function cấu hình DONE nhưng thiếu negative/permission case |
| NFR | 8 | Bổ sung ngưỡng tải/độ trễ cụ thể cho function đã ship |
| PATIENT | 7 | Bổ sung sửa/soft-delete, trùng hồ sơ, validate |
| PHRM | 6 | Bổ sung xuất/nhập kho, lô/hạn dùng, tồn âm |
| TENANT | 4 | Bổ sung cách ly dữ liệu chéo cho function đã có |
| AUDIT / THEME | 3 mỗi nhóm | Bổ sung edge cho function đã DONE |

> **Đề nghị Test Engineer:** ưu tiên xác minh & hoàn thiện các dòng PARTIAL trên function đã DONE (VISIT 12, CFG 11, NFR 8, PATIENT 7, PHRM 6) — nếu test thực tế đã đủ thì nâng COVERED; nếu thiếu thì viết bổ sung theo P0 → P1. Đồng thời chuẩn hóa tiền tố ma trận của TENANT (TEN/TENT trộn) và đối chiếu lại 464 vs 461 với `function_list_data.py`.

---

## Quy ước

### Mã test case
- Định dạng: `TC-<GROUP>-NNN` (NNN số thứ tự), ví dụ `TC-AUTH-001`, `TC-BILL-014`. Một số group có hậu tố nhánh `-NN` (ví dụ `TC-VIS-001-02`).
- `<GROUP>` là mã/tiền tố nhóm chức năng (xem cột Group; lưu ý các tiền tố viết tắt PAT/VIS/VTL/TEN/TENT).

### Layer test
- **UNIT** — kiểm thử hàm/logic đơn lẻ, mock phụ thuộc.
- **API / INTEGRATION** — kiểm thử endpoint, service, DB thật, tích hợp giữa module.
- **E2E / UI** — kiểm thử luồng người dùng end-to-end qua giao diện (Playwright/httpx).
- **NFR** — phi chức năng: hiệu năng, bảo mật, tải, cách ly tenant, audit.

### Ưu tiên
- **P0** — critical: ảnh hưởng tiền / dữ liệu bệnh nhân / cách ly tenant / bảo mật; phải pass trước release.
- **P1** — quan trọng: luồng nghiệp vụ chính, cần phủ sớm.
- **P2** — bổ trợ: edge case, tiện ích, giao diện thứ yếu.

### Ý nghĩa Coverage
- **COVERED** — đã có hành vi ship + kiểm chứng được (test thực tế hoặc endpoint live), không phát hiện gap.
- **PARTIAL** — một phần đã có (BE done nhưng FE/flow chưa, hoặc thiếu nhánh edge/negative/permission/đa tenant); cần bổ sung.
- **MISSING** — chưa ship / chưa có test case nào; cần viết mới.

> Cột Coverage là ước lượng từ status nguồn đối chiếu test; Test Engineer cần xác minh lại trực tiếp với file test trước khi chốt độ phủ.
