# Test Case Catalog — INT · Tích hợp ngoài (Integration)

**Nguồn:** function_list_data.py (group INT) + clinic_management_function_list.md + system_design/SaaS.
**Phạm vi:** 20 functions.  **Tổng test case:** 52.  **Ngày:** 2026-05-30.

> **Bối cảnh hệ thống:** Clinic CMS là SaaS multi-tenant (FastAPI + PostgreSQL RLS + Redis + Tauri offline). Nhóm INT là các tích hợp với dịch vụ/thiết bị bên ngoài: nhà cung cấp Email/SMS, cổng thanh toán (VietQR/VNPay/MoMo), hóa đơn điện tử, reCAPTCHA, Analytics, Sentry, lưu trữ S3, Zalo OA, master data (ICD-10/địa giới/thuốc), Lab/PACS/BHYT và thiết bị Tauri (máy in POS, máy quét mã, đầu đọc thẻ CCCD).
>
> **Tình trạng nguồn (status):** chỉ **INT-012** (ICD-10 master data) và **INT-019** (Barcode scanner) ở trạng thái **DONE**. 8 function ở **TODO** (INT-001, 003, 007, 008, 009, 010, 013, 018). 10 function còn lại ở **IDEA** (Phase 2/3, chưa lên kế hoạch triển khai: INT-002, 004, 005, 006, 011, 014, 015, 016, 017, 020).
>
> **Quy ước Coverage (suy ra từ status nguồn + đối chiếu code/test):**
> - Không truy cập được mã nguồn tích hợp tại `E:/MyProject/clinic-cms-merge/app` (submodule rỗng/không đọc được trong sandbox) và không tìm thấy file test tương ứng trong `tests/`. Do đó Coverage được suy ra từ cột `status` nguồn và **cần xác minh test file** khi mã merge khả dụng.
> - **DONE** → đánh **PARTIAL** (chức năng đã hiện thực nhưng chưa xác nhận có test tự động) — cần xác minh test file.
> - **TODO** / **IDEA** → đánh **MISSING** (chưa hiện thực, chưa có test).
>
> **Nguyên tắc chung cho nhóm INT:**
> - Mọi callback/webhook từ cổng ngoài (VNPay/MoMo) PHẢI xác thực chữ ký (signature/checksum) → có case Security chống giả mạo + idempotency (gửi trùng).
> - Mọi credential/cấu hình tích hợp (SMS brandname, S3 bucket prefix, API key, OA token) gắn theo clinic là dữ liệu domain → có case cô lập tenant (RLS).
> - Endpoint quản trị/cấu hình tích hợp yêu cầu quyền → có case 401 (chưa đăng nhập) / 403 (sai vai trò).
> - Tài liệu/tệp bệnh nhân trên S3 dùng presigned URL TTL 1h, encryption at rest → có case URL hết hạn + cô lập tệp giữa các clinic.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| INT-001 | Email provider (SES/SendGrid/Postmark) | TODO | TC-INT-001, TC-INT-002, TC-INT-003 | MISSING |
| INT-002 | SMS provider (Stringee/Twilio VN) | IDEA | TC-INT-004, TC-INT-005 | MISSING |
| INT-003 | VietQR generator | TODO | TC-INT-006, TC-INT-007, TC-INT-008 | MISSING |
| INT-004 | VNPay webhook | IDEA | TC-INT-009, TC-INT-010, TC-INT-011, TC-INT-012 | MISSING |
| INT-005 | MoMo webhook | IDEA | TC-INT-013, TC-INT-014 | MISSING |
| INT-006 | E-invoice (VNPT/Viettel) | IDEA | TC-INT-015, TC-INT-016 | MISSING |
| INT-007 | reCAPTCHA | TODO | TC-INT-017, TC-INT-018, TC-INT-019 | MISSING |
| INT-008 | Google Analytics (landing) | TODO | TC-INT-020, TC-INT-021 | MISSING |
| INT-009 | Sentry error tracking | TODO | TC-INT-022, TC-INT-023 | MISSING |
| INT-010 | S3-compatible storage | TODO | TC-INT-024, TC-INT-025, TC-INT-026, TC-INT-027 | MISSING |
| INT-011 | Zalo OA Push | IDEA | TC-INT-028, TC-INT-029 | MISSING |
| INT-012 | ICD-10 master data | DONE | TC-INT-030, TC-INT-031, TC-INT-032 | PARTIAL |
| INT-013 | VN address API | TODO | TC-INT-033, TC-INT-034, TC-INT-035 | MISSING |
| INT-014 | Drug master data | IDEA | TC-INT-036, TC-INT-037 | MISSING |
| INT-015 | Lab system integration (HL7/FHIR) | IDEA | TC-INT-038, TC-INT-039, TC-INT-040 | MISSING |
| INT-016 | Imaging system (PACS/DICOM) | IDEA | TC-INT-041, TC-INT-042 | MISSING |
| INT-017 | National Health Insurance API (BHYT) | IDEA | TC-INT-043, TC-INT-044 | MISSING |
| INT-018 | POS printer driver (ESC/POS) | TODO | TC-INT-045, TC-INT-046 | MISSING |
| INT-019 | Barcode scanner (Tauri) | DONE | TC-INT-047, TC-INT-048, TC-INT-049 | PARTIAL |
| INT-020 | Card reader (Tauri, CMND/CCCD) | IDEA | TC-INT-050, TC-INT-051, TC-INT-052 | MISSING |

---

## 2. Chi tiết Test Cases

### TC-INT-001 — Email provider: gửi email theo template qua SES thành công
- **Function:** INT-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + mock SES
- **Tiền điều kiện:** Cấu hình SES (region, sender đã verify); có template (vd: welcome, otp, invoice).
- **Bước thực hiện:** 1) Gọi `send_email(to, template, vars)`. 2) Wrapper render template với biến. 3) Gọi SES API.
- **Dữ liệu test:** `to=user@example.com`, template=welcome, vars={name}.
- **Kết quả mong đợi:** SES nhận message; trả `message_id`; ghi log gửi `SENT`.
- **Coverage hiện tại:** MISSING (status TODO; chưa có endpoint/test — cần xác minh test file khi merge khả dụng).

### TC-INT-002 — Email provider: SES lỗi → fallback Postmark/SendGrid
- **Function:** INT-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + mock providers
- **Tiền điều kiện:** Mock SES trả lỗi 5xx; cấu hình fallback provider.
- **Bước thực hiện:** 1) Gọi gửi email khi SES fail. 2) Wrapper bắt lỗi, chuyển sang Postmark/SendGrid.
- **Dữ liệu test:** SES trả lỗi tạm thời.
- **Kết quả mong đợi:** Email gửi thành công qua fallback; log ghi provider thực dùng; không mất thông báo.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-003 — Email provider: địa chỉ email không hợp lệ bị từ chối
- **Function:** INT-001
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Wrapper send_email có validate.
- **Bước thực hiện:** 1) Gọi gửi với email sai định dạng.
- **Dữ liệu test:** `to="abc@@"`, `to=""`.
- **Kết quả mong đợi:** Trả lỗi validate trước khi gọi provider; không tốn quota.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-004 — SMS provider: gửi SMS qua Stringee/Twilio VN với brandname
- **Function:** INT-002
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + mock SMS gateway
- **Tiền điều kiện:** Cấu hình provider + brandname đã đăng ký Bộ TTTT.
- **Bước thực hiện:** 1) Gọi gửi SMS OTP/nhắc lịch. 2) Gateway nhận với brandname đúng.
- **Dữ liệu test:** SĐT `09xxxxxxxx`, nội dung OTP.
- **Kết quả mong đợi:** Gateway nhận; trả `request_id`; log `SENT`.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-005 — SMS provider: cấu hình SMS của clinic A không lộ sang clinic B (RLS)
- **Function:** INT-002
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** Clinic A và B có cấu hình SMS riêng (brandname/credential).
- **Bước thực hiện:** 1) Context clinic A. 2) Truy vấn cấu hình SMS.
- **Dữ liệu test:** 2 tenant.
- **Kết quả mong đợi:** Chỉ thấy cấu hình của A; không truy cập credential của B (RLS chặn).
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-006 — VietQR: sinh chuỗi VietQR động + render QR PNG
- **Function:** INT-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Cấu hình tài khoản nhận (bank, account) của clinic.
- **Bước thực hiện:** 1) Gọi generate với {bank, account, amount, content}. 2) Tạo chuỗi VietQR theo chuẩn EMVCo. 3) Render PNG.
- **Dữ liệu test:** amount=500000, content="HD123".
- **Kết quả mong đợi:** Chuỗi VietQR hợp lệ (CRC đúng); PNG quét được bằng app ngân hàng ra đúng số tiền/nội dung.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-007 — VietQR: checksum CRC của chuỗi đúng chuẩn (toàn vẹn)
- **Function:** INT-003
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Hàm sinh VietQR.
- **Bước thực hiện:** 1) Sinh chuỗi. 2) Tính lại CRC-16/CCITT trên payload.
- **Dữ liệu test:** nhiều bộ {amount, content} khác nhau.
- **Kết quả mong đợi:** 4 ký tự CRC cuối khớp tính toán độc lập; không sai định dạng.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-008 — VietQR: amount/content không hợp lệ bị từ chối
- **Function:** INT-003
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Hàm sinh VietQR có validate.
- **Bước thực hiện:** 1) Gọi với amount âm/0; content vượt độ dài/ký tự cấm.
- **Dữ liệu test:** amount=-1, content quá dài.
- **Kết quả mong đợi:** Trả lỗi validate; không sinh QR.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-009 — VNPay webhook: IPN hợp lệ → mark paid + gia hạn subscription
- **Function:** INT-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) + mock IPN
- **Tiền điều kiện:** Có invoice subscription `PENDING`, cấu hình `vnp_HashSecret`.
- **Bước thực hiện:** 1) POST /webhook/vnpay với chữ ký hợp lệ + `vnp_ResponseCode=00`. 2) Verify signature → match invoice_id. 3) Mark paid + extend subscription.
- **Dữ liệu test:** IPN thành công khớp invoice.
- **Kết quả mong đợi:** Invoice → `PAID`, subscription gia hạn; trả `{RspCode:'00'}`.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-010 — VNPay webhook: chữ ký sai bị từ chối (chống giả mạo)
- **Function:** INT-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Endpoint webhook hoạt động.
- **Bước thực hiện:** 1) Gửi IPN với `vnp_SecureHash` sai / sửa amount sau khi ký.
- **Dữ liệu test:** hash giả mạo.
- **Kết quả mong đợi:** Từ chối `{RspCode:'97', Invalid Checksum}`; KHÔNG mark paid.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-011 — VNPay webhook: IPN gửi trùng (idempotency)
- **Function:** INT-004
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Invoice đã `PAID` từ IPN trước.
- **Bước thực hiện:** 1) Gửi lại IPN thành công cùng `vnp_TxnRef`.
- **Dữ liệu test:** IPN trùng.
- **Kết quả mong đợi:** Không gia hạn đôi/không cộng đôi; trả `{RspCode:'02', already confirmed}`.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-012 — VNPay webhook: IPN không khớp invoice_id
- **Function:** INT-004
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Endpoint hoạt động.
- **Bước thực hiện:** 1) Gửi IPN với `vnp_TxnRef` không tồn tại.
- **Dữ liệu test:** invoice_id sai.
- **Kết quả mong đợi:** Trả `{RspCode:'01', Order not found}`; không thay đổi dữ liệu.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-013 — MoMo webhook: callback hợp lệ cập nhật thanh toán
- **Function:** INT-005
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx) + mock MoMo
- **Tiền điều kiện:** Giao dịch MoMo `PENDING`.
- **Bước thực hiện:** 1) Nhận callback `resultCode=0` với chữ ký HMAC-SHA256 đúng. 2) Cập nhật invoice.
- **Dữ liệu test:** callback thành công.
- **Kết quả mong đợi:** Invoice → `PAID`; giao dịch `SUCCESS`.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-014 — MoMo webhook: chữ ký sai bị từ chối
- **Function:** INT-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Giao dịch `PENDING`.
- **Bước thực hiện:** 1) Gửi callback sai `signature`.
- **Dữ liệu test:** signature giả mạo.
- **Kết quả mong đợi:** Từ chối (400/401); không cập nhật invoice.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-015 — E-invoice: phát hành hóa đơn điện tử ký số gửi CQT (VNPT/Viettel)
- **Function:** INT-006
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + mock provider HĐĐT
- **Tiền điều kiện:** Cấu hình HĐĐT + chứng thư số; có invoice đã thanh toán.
- **Bước thực hiện:** 1) Phát hành HĐĐT. 2) Ký số. 3) Gửi CQT.
- **Dữ liệu test:** invoice hợp lệ.
- **Kết quả mong đợi:** Nhận mã CQT + mã tra cứu; trạng thái `ISSUED`.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-016 — E-invoice: chứng thư số hết hạn → chặn phát hành
- **Function:** INT-006
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Chứng thư số hết hạn.
- **Bước thực hiện:** 1) Cố phát hành HĐĐT.
- **Dữ liệu test:** cert expired.
- **Kết quả mong đợi:** Từ chối "chứng thư số hết hạn"; không gửi CQT.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-017 — reCAPTCHA: signup với token hợp lệ được chấp nhận
- **Function:** INT-007
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx) + mock Google verify
- **Tiền điều kiện:** Cấu hình site key + secret key.
- **Bước thực hiện:** 1) Submit form signup kèm `g-recaptcha-response`. 2) BE gọi Google verify. 3) score/success đạt ngưỡng.
- **Dữ liệu test:** token hợp lệ.
- **Kết quả mong đợi:** Verify pass → cho phép tiếp tục signup.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-018 — reCAPTCHA: token thiếu/không hợp lệ bị chặn (chống bot)
- **Function:** INT-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Endpoint signup bật reCAPTCHA.
- **Bước thực hiện:** 1) Submit không có token / token giả / đã dùng.
- **Dữ liệu test:** token rỗng, token sai.
- **Kết quả mong đợi:** Từ chối signup (400/403); không tạo tài khoản.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-019 — reCAPTCHA: score thấp (nghi bot) bị từ chối
- **Function:** INT-007
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx) + mock verify
- **Tiền điều kiện:** reCAPTCHA v3 có threshold.
- **Bước thực hiện:** 1) Mock Google trả `success=true` nhưng `score=0.1`.
- **Dữ liệu test:** score dưới ngưỡng.
- **Kết quả mong đợi:** Từ chối hoặc yêu cầu thử thách bổ sung; không qua signup.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-020 — Google Analytics: bắn event funnel trên landing page
- **Function:** INT-008
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI + mock GA4
- **Tiền điều kiện:** GA4 measurement id cấu hình trên landing.
- **Bước thực hiện:** 1) Mở landing (pageview). 2) Bắt đầu signup (signup_start). 3) Hoàn tất (signup_complete). 4) Gửi contact (contact_submit).
- **Dữ liệu test:** luồng signup mẫu.
- **Kết quả mong đợi:** 4 event gửi đúng tên/tham số (kiểm qua network/GA debug).
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-021 — Google Analytics: không bắn event khi user từ chối cookie/consent
- **Function:** INT-008
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI
- **Tiền điều kiện:** Có banner consent.
- **Bước thực hiện:** 1) Từ chối analytics cookie. 2) Duyệt landing.
- **Dữ liệu test:** consent = denied.
- **Kết quả mong đợi:** GA không gửi event (tôn trọng consent mode).
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-022 — Sentry: bắt unhandled exception và gửi lên dashboard
- **Function:** INT-009
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (FE+BE) + mock Sentry
- **Tiền điều kiện:** Sentry SDK init với DSN.
- **Bước thực hiện:** 1) Gây lỗi unhandled ở BE. 2) SDK capture + gửi sự kiện.
- **Dữ liệu test:** exception cố ý.
- **Kết quả mong đợi:** Sentry nhận event có stacktrace + môi trường; alert khi error rate cao.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-023 — Sentry: scrub dữ liệu nhạy cảm (PII) trước khi gửi
- **Function:** INT-009
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Unit/Integration
- **Tiền điều kiện:** Cấu hình `before_send`/data scrubbing.
- **Bước thực hiện:** 1) Gây lỗi có chứa thông tin BN/token trong payload.
- **Dữ liệu test:** payload có PII (CCCD, password, token).
- **Kết quả mong đợi:** Event gửi đi đã che/loại PII; không lộ dữ liệu y tế lên Sentry.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-024 — S3: upload tài liệu BN + sinh presigned URL TTL 1h
- **Function:** INT-010
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + MinIO/S3 test
- **Tiền điều kiện:** Cấu hình bucket per environment; encryption at rest bật.
- **Bước thực hiện:** 1) Upload file vào prefix theo tenant. 2) Sinh presigned URL TTL 1h.
- **Dữ liệu test:** PDF kết quả XN.
- **Kết quả mong đợi:** File lưu đúng bucket/prefix; presigned URL tải được trong 1h; object mã hóa at rest.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-025 — S3: presigned URL hết hạn không truy cập được
- **Function:** INT-010
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đã sinh presigned URL TTL 1h.
- **Bước thực hiện:** 1) Truy cập URL sau khi quá TTL.
- **Dữ liệu test:** URL expired.
- **Kết quả mong đợi:** 403 / AccessDenied; không tải được tệp.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-026 — S3: tệp của clinic A không truy cập từ clinic B (cô lập tenant)
- **Function:** INT-010
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS) + storage prefix
- **Tiền điều kiện:** Tệp lưu theo prefix tenant `clinic_{id}/...`.
- **Bước thực hiện:** 1) Context clinic B yêu cầu presigned URL cho object key của A.
- **Dữ liệu test:** object key thuộc A.
- **Kết quả mong đợi:** Từ chối cấp URL (403/404); không sinh URL chéo tenant.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-027 — S3: provider lỗi → trả lỗi rõ ràng, không treo request
- **Function:** INT-010
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Mock S3 trả 5xx/timeout.
- **Bước thực hiện:** 1) Upload khi storage lỗi.
- **Dữ liệu test:** S3 timeout.
- **Kết quả mong đợi:** Trả lỗi có ý nghĩa (5xx/retryable); không lưu metadata mồ côi.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-028 — Zalo OA Push: gửi thông báo ZNS theo template duyệt
- **Function:** INT-011
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB) + mock Zalo API
- **Tiền điều kiện:** OA xác thực, `template_id` duyệt, có `access_token`.
- **Bước thực hiện:** 1) Gửi ZNS nhắc lịch với tham số.
- **Dữ liệu test:** template nhắc lịch.
- **Kết quả mong đợi:** Trả `msg_id`; log gửi thành công.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 3, chưa triển khai).

### TC-INT-029 — Zalo OA Push: access_token hết hạn → tự refresh rồi gửi
- **Function:** INT-011
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Token hết hạn, có refresh_token.
- **Bước thực hiện:** 1) Gửi ZNS khi token hết hạn → hệ thống refresh → gửi lại.
- **Dữ liệu test:** token expired.
- **Kết quả mong đợi:** Refresh + gửi thành công; cập nhật token mới.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 3, chưa triển khai).

### TC-INT-030 — ICD-10 master data: tra cứu/autocomplete mã chẩn đoán
- **Function:** INT-012
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Catalog ICD-10 VN-translated đã seed (DIAG-004).
- **Bước thực hiện:** 1) Gọi API search ICD-10 theo từ khóa (tiếng Việt/mã).
- **Dữ liệu test:** keyword "tăng huyết áp", mã "I10".
- **Kết quả mong đợi:** Trả đúng mã + tên VN; phân trang; tìm theo cả mã và tên.
- **Coverage hiện tại:** PARTIAL (status DONE — chức năng đã hiện thực; cần xác minh test file tra cứu/seed).

### TC-INT-031 — ICD-10 master data: dữ liệu seed là master dùng chung mọi tenant (read-only)
- **Function:** INT-012
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** Catalog ICD-10 là dữ liệu hệ thống (không gắn clinic_id).
- **Bước thực hiện:** 1) Truy vấn từ context clinic A và clinic B.
- **Dữ liệu test:** 2 tenant.
- **Kết quả mong đợi:** Cả hai đọc được cùng danh mục master (không bị RLS chặn); không clinic nào sửa được catalog.
- **Coverage hiện tại:** PARTIAL (status DONE — cần xác minh test phân quyền master data).

### TC-INT-032 — ICD-10 master data: từ khóa không khớp trả rỗng (không lỗi)
- **Function:** INT-012
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Catalog đã seed.
- **Bước thực hiện:** 1) Search keyword vô nghĩa.
- **Dữ liệu test:** "zzzz".
- **Kết quả mong đợi:** Trả danh sách rỗng, HTTP 200; không lỗi.
- **Coverage hiện tại:** PARTIAL (status DONE — cần xác minh test file).

### TC-INT-033 — VN address API: autocomplete cascade tỉnh → quận → phường
- **Function:** INT-013
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + cache
- **Tiền điều kiện:** Dữ liệu địa giới cache locally từ provinces.open-api.vn.
- **Bước thực hiện:** 1) Chọn tỉnh → load quận. 2) Chọn quận → load phường.
- **Dữ liệu test:** "Hà Nội" → "Cầu Giấy" → "Dịch Vọng".
- **Kết quả mong đợi:** Mỗi cấp trả đúng danh sách con; cascade hoạt động.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-034 — VN address API: dùng cache local khi API public down
- **Function:** INT-013
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã cache dữ liệu; mock API public lỗi.
- **Bước thực hiện:** 1) Gọi autocomplete khi API ngoài không phản hồi.
- **Dữ liệu test:** API public timeout.
- **Kết quả mong đợi:** Vẫn trả dữ liệu từ cache local; không lỗi cho người dùng.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-035 — VN address API: tỉnh/quận không tồn tại trả rỗng
- **Function:** INT-013
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Dữ liệu địa giới sẵn.
- **Bước thực hiện:** 1) Truy vấn quận của tỉnh không tồn tại.
- **Dữ liệu test:** province_code sai.
- **Kết quả mong đợi:** Trả rỗng, HTTP 200; không lỗi.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-036 — Drug master data: tra cứu thuốc theo hoạt chất/hàm lượng
- **Function:** INT-014
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Master DB thuốc VN đã import (Cục QL Dược).
- **Bước thực hiện:** 1) Search thuốc theo tên/hoạt chất.
- **Dữ liệu test:** "Paracetamol 500mg".
- **Kết quả mong đợi:** Trả thuốc với active_ingredient + dạng + hàm lượng.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-037 — Drug master data: cảnh báo tương tác thuốc
- **Function:** INT-014
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** DB có dữ liệu tương tác.
- **Bước thực hiện:** 1) Thêm 2 thuốc có tương tác vào đơn.
- **Dữ liệu test:** cặp thuốc tương tác chống chỉ định.
- **Kết quả mong đợi:** Hệ thống cảnh báo tương tác; yêu cầu xác nhận.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-038 — Lab integration: nhận kết quả XN qua HL7/FHIR vào visit
- **Function:** INT-015
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + mock lab partner
- **Tiền điều kiện:** Có chỉ định XN với `order_id`; cấu hình kênh HL7/FHIR với lab (Medlatec/Diag).
- **Bước thực hiện:** 1) Lab gửi message HL7 ORU/FHIR DiagnosticReport. 2) Parse, map theo order_id. 3) Auto-pull vào visit.
- **Dữ liệu test:** message kết quả hợp lệ.
- **Kết quả mong đợi:** Kết quả gắn đúng chỉ định/BN trong visit; trạng thái → `RESULTED`.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 3, chưa triển khai).

### TC-INT-039 — Lab integration: message sai/không map được order
- **Function:** INT-015
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Kênh tích hợp hoạt động.
- **Bước thực hiện:** 1) Gửi message thiếu segment / order_id không tồn tại.
- **Dữ liệu test:** message lỗi.
- **Kết quả mong đợi:** Không ghi kết quả; đưa vào hàng đợi lỗi/log để xử lý thủ công.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 3, chưa triển khai).

### TC-INT-040 — Lab integration: kết quả không lẫn giữa các clinic (RLS)
- **Function:** INT-015
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** 2 clinic dùng cùng lab partner.
- **Bước thực hiện:** 1) Kết quả về cho order của clinic A. 2) Context clinic B truy vấn.
- **Dữ liệu test:** 2 tenant.
- **Kết quả mong đợi:** Kết quả chỉ thuộc clinic A; B không truy cập được (RLS).
- **Coverage hiện tại:** MISSING (status IDEA — Phase 3, chưa triển khai).

### TC-INT-041 — PACS: hiển thị ảnh DICOM (XQuang/CT) trong visit
- **Function:** INT-016
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB) + mock PACS
- **Tiền điều kiện:** Cấu hình PACS; có chỉ định CĐHA.
- **Bước thực hiện:** 1) Nhận tham chiếu study DICOM. 2) Embed DICOM viewer trong visit.
- **Dữ liệu test:** study DICOM mẫu.
- **Kết quả mong đợi:** Viewer hiển thị đúng study/series gắn đúng BN.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 3, chưa triển khai).

### TC-INT-042 — PACS: truy cập ảnh yêu cầu phiên hợp lệ (Security)
- **Function:** INT-016
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Ảnh DICOM truy cập qua URL có kiểm soát.
- **Bước thực hiện:** 1) Truy cập ảnh không có phiên/quyền hợp lệ.
- **Dữ liệu test:** request ẩn danh / sai tenant.
- **Kết quả mong đợi:** 401/403; không lộ ảnh y tế.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 3, chưa triển khai).

### TC-INT-043 — BHYT API: verify thẻ BHYT real-time hợp lệ
- **Function:** INT-017
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + mock cổng BHXH
- **Tiền điều kiện:** Cấu hình credential BHXH VN.
- **Bước thực hiện:** 1) Gửi mã thẻ + thông tin BN. 2) Nhận trạng thái thẻ, mức hưởng, nơi ĐKKCB.
- **Dữ liệu test:** thẻ còn hạn.
- **Kết quả mong đợi:** Trả thông tin thẻ hợp lệ; lưu vào hồ sơ.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 3, chưa triển khai).

### TC-INT-044 — BHYT API: thẻ hết hạn/không hợp lệ
- **Function:** INT-017
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Mã thẻ hết hạn/sai.
- **Bước thực hiện:** 1) Verify thẻ.
- **Dữ liệu test:** thẻ hết hạn.
- **Kết quả mong đợi:** Trả trạng thái không hợp lệ + lý do; không áp mức hưởng.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 3, chưa triển khai).

### TC-INT-045 — POS printer: in phiếu/biên lai qua ESC/POS (USB)
- **Function:** INT-018
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Manual/UI (Tauri) + mock driver
- **Tiền điều kiện:** Máy in POS kết nối USB (Epson TM-T82/Xprinter/Bixolon); cấu hình layout.
- **Bước thực hiện:** 1) Tạo lệnh in biên lai. 2) Tauri Rust gửi ESC/POS commands qua USB.
- **Dữ liệu test:** biên lai thanh toán.
- **Kết quả mong đợi:** In ra đúng layout (logo, dòng tiền, QR); cắt giấy đúng.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-046 — POS printer: máy in không kết nối/hết giấy → báo lỗi rõ ràng
- **Function:** INT-018
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Manual/UI (Tauri)
- **Tiền điều kiện:** Máy in ngắt kết nối hoặc hết giấy.
- **Bước thực hiện:** 1) Gửi lệnh in.
- **Dữ liệu test:** máy in offline.
- **Kết quả mong đợi:** Thông báo lỗi rõ (không treo UI); cho phép thử lại sau khi khắc phục.
- **Coverage hiện tại:** MISSING (status TODO — cần xác minh test file).

### TC-INT-047 — Barcode scanner: quét mã tự điền vào ô input (Tauri HID)
- **Function:** INT-019
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Manual/UI (Tauri) + E2E
- **Tiền điều kiện:** Scanner USB HID emulate keyboard; con trỏ ở ô tìm kiếm mã BN/mẫu.
- **Bước thực hiện:** 1) Quét mã barcode. 2) Scanner gửi ký tự như bàn phím + Enter.
- **Dữ liệu test:** barcode mã BN.
- **Kết quả mong đợi:** Ô input tự điền đúng mã; trigger tìm kiếm.
- **Coverage hiện tại:** PARTIAL (status DONE — chức năng đã hiện thực; cần xác minh test E2E/manual scan).

### TC-INT-048 — Barcode scanner: mã không hợp lệ/không tồn tại
- **Function:** INT-019
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Manual/UI (Tauri)
- **Tiền điều kiện:** Scanner hoạt động.
- **Bước thực hiện:** 1) Quét mã rác/không khớp dữ liệu.
- **Dữ liệu test:** mã không tồn tại.
- **Kết quả mong đợi:** Thông báo "không tìm thấy"; không crash; cho quét lại.
- **Coverage hiện tại:** PARTIAL (status DONE — cần xác minh test file).

### TC-INT-049 — Barcode scanner: focus tự nhiên vào input đang active
- **Function:** INT-019
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (Tauri)
- **Tiền điều kiện:** Có nhiều ô nhập trên màn hình.
- **Bước thực hiện:** 1) Đặt focus ô A. 2) Quét → ký tự vào ô A. 3) Đổi focus ô B, quét lại.
- **Dữ liệu test:** 2 lần quét, 2 ô.
- **Kết quả mong đợi:** Ký tự luôn vào ô đang focus; không nhảy lung tung.
- **Coverage hiện tại:** PARTIAL (status DONE — cần xác minh test file).

### TC-INT-050 — Card reader: đọc chip CCCD → fill form đăng ký
- **Function:** INT-020
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI (Tauri) + mock card reader
- **Tiền điều kiện:** Đầu đọc thẻ CCCD chip kết nối; thẻ hợp lệ.
- **Bước thực hiện:** 1) Đặt CCCD vào đầu đọc. 2) Tauri đọc thông tin từ chip. 3) Tự điền form (họ tên, ngày sinh, số CCCD, địa chỉ).
- **Dữ liệu test:** thẻ CCCD mẫu.
- **Kết quả mong đợi:** Form điền đúng thông tin từ chip; giảm nhập tay.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-051 — Card reader: thẻ lỗi/không đọc được chip
- **Function:** INT-020
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Manual/UI (Tauri)
- **Tiền điều kiện:** Đầu đọc hoạt động; thẻ hỏng/đặt sai.
- **Bước thực hiện:** 1) Đọc thẻ lỗi.
- **Dữ liệu test:** thẻ không đọc được.
- **Kết quả mong đợi:** Báo lỗi rõ; cho phép nhập tay thay thế; không crash.
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).

### TC-INT-052 — Card reader: dữ liệu CCCD chỉ lưu vào hồ sơ của clinic hiện tại (RLS)
- **Function:** INT-020
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** Người dùng đang ở context clinic A.
- **Bước thực hiện:** 1) Đọc CCCD → tạo/cập nhật hồ sơ BN.
- **Dữ liệu test:** thẻ CCCD; context clinic A.
- **Kết quả mong đợi:** Hồ sơ BN gắn đúng `clinic_id` A; clinic B không thấy (RLS).
- **Coverage hiện tại:** MISSING (status IDEA — Phase 2, chưa triển khai).
