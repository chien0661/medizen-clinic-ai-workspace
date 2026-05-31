# Test Case Catalog — SUB · Gói thuê bao (Subscription lifecycle)

**Nguồn:** function_list_data.py (group SUB — "Subscription & Billing, provider side") + clinic_management_function_list.md + system_design / SaaS platform model.
**Phạm vi:** 25 functions (SUB-001 → SUB-025).  **Tổng test case:** 71.  **Ngày:** 2026-05-30.

> **Bối cảnh group SUB:** Đây là vòng đời thuê bao ở **phía nhà cung cấp (provider/super admin)** quản lý từng **clinic (tenant)**: loại thuê bao (trial/paid), chu kỳ thanh toán, grace period, state machine `pending → active → grace → expired → suspended → archived`, `SubscriptionGuard` middleware gate API theo trạng thái, read-only mode, audit event, gia hạn/convert/upgrade/suspend/reactivate/archive thủ công bởi Super Admin, auto-export + hard delete sau 90 ngày, reminder cron, và dashboard metrics (MRR/ARR/churn). SUB-022..025 là **Phase 2 / IDEA** (auto-renew payment, e-invoice, tiers, free tier).
>
> **Ghi chú coverage:** Toàn bộ 25 function có `status = ⬜ TODO` (SUB-001..021) hoặc `💡 IDEA` (SUB-022..025) — chưa triển khai (thuộc TASK-026/028/030/006, một số v2 chưa có task). Repo mã nguồn `E:/MyProject/clinic-cms-merge/app` và thư mục `tests` **không truy cập được** trong môi trường soạn catalog này (Bash/Glob trả rỗng), nên Coverage được suy ra từ cột status nguồn = **MISSING** và đánh dấu **"cần xác minh test file"** khi mã được hiện thực. Catalog đóng vai trò đặc tả test (test design) đi trước implementation.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| SUB-001 | Subscription type (trial / paid) | TODO | TC-SUB-001, TC-SUB-002 | MISSING |
| SUB-002 | Billing cycle (monthly / yearly / perpetual) | TODO | TC-SUB-003, TC-SUB-004 | MISSING |
| SUB-003 | Trial 14 ngày default (auto self-signup) | TODO | TC-SUB-005, TC-SUB-006 | MISSING |
| SUB-004 | Grace period 7d/14d/0d theo cycle | TODO | TC-SUB-007, TC-SUB-008 | MISSING |
| SUB-005 | Subscription state machine | TODO | TC-SUB-009, TC-SUB-010, TC-SUB-011 | MISSING |
| SUB-006 | SubscriptionGuard middleware | TODO | TC-SUB-012, TC-SUB-013, TC-SUB-014 | MISSING |
| SUB-007 | Behavior matrix per status | TODO | TC-SUB-015, TC-SUB-016 | MISSING |
| SUB-008 | Read-only mode khi expired | TODO | TC-SUB-017, TC-SUB-018 | MISSING |
| SUB-009 | Banner cảnh báo trial/grace (UI) | TODO | TC-SUB-019, TC-SUB-020 | MISSING |
| SUB-010 | Subscription event audit | TODO | TC-SUB-021, TC-SUB-022 | MISSING |
| SUB-011 | Renewal manual (super admin) | TODO | TC-SUB-023, TC-SUB-024, TC-SUB-025 | MISSING |
| SUB-012 | Convert trial → paid | TODO | TC-SUB-026, TC-SUB-027 | MISSING |
| SUB-013 | Upgrade plan (đổi cycle) | TODO | TC-SUB-028, TC-SUB-029 | MISSING |
| SUB-014 | Suspend clinic | TODO | TC-SUB-030, TC-SUB-031, TC-SUB-032 | MISSING |
| SUB-015 | Reactivate clinic | TODO | TC-SUB-033, TC-SUB-034 | MISSING |
| SUB-016 | Archive clinic (giữ data 90d) | TODO | TC-SUB-035, TC-SUB-036 | MISSING |
| SUB-017 | Auto export trước hard delete | TODO | TC-SUB-037, TC-SUB-038, TC-SUB-039 | MISSING |
| SUB-018 | Hard delete sau 90d (cron) | TODO | TC-SUB-040, TC-SUB-041, TC-SUB-042 | MISSING |
| SUB-019 | Reminder D-14/-7/-3/-1/0 | TODO | TC-SUB-043, TC-SUB-044 | MISSING |
| SUB-020 | Daily reminder trong grace | TODO | TC-SUB-045, TC-SUB-046 | MISSING |
| SUB-021 | Subscription metrics dashboard (MRR/ARR/churn) | TODO | TC-SUB-047, TC-SUB-048, TC-SUB-049 | MISSING |
| SUB-022 | Auto-renew payment integration (VNPay/MoMo) | IDEA (v2) | TC-SUB-050, TC-SUB-051, TC-SUB-052 | MISSING |
| SUB-023 | E-invoice integration (VNPT/Viettel) | IDEA (v2) | TC-SUB-053, TC-SUB-054 | MISSING |
| SUB-024 | Subscription tiers (Basic/Pro/Enterprise) | IDEA (v2) | TC-SUB-055, TC-SUB-056 | MISSING |
| SUB-025 | Free tier vĩnh viễn (siêu hạn chế) | IDEA (v2) | TC-SUB-057, TC-SUB-058 | MISSING |

---

## 2. Chi tiết Test Cases

### TC-SUB-001 — Tạo subscription loại trial / paid đúng type
- **Function:** SUB-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic mới được tạo; chưa có subscription.
- **Bước thực hiện:** 1) Tạo subscription type=`trial`. 2) Tạo (clinic khác) subscription type=`paid`.
- **Dữ liệu test:** `{type:"trial"}`, `{type:"paid"}`.
- **Kết quả mong đợi:** Subscription lưu đúng `type`; trial set trial defaults (xem SUB-003); paid yêu cầu cycle + period_end.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-002 — Type không hợp lệ bị từ chối
- **Function:** SUB-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Tạo subscription type=`free`/giá trị lạ.
- **Dữ liệu test:** `type:"abc"`.
- **Kết quả mong đợi:** HTTP 422 — chỉ chấp nhận enum {trial, paid}.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-003 — Billing cycle monthly/yearly/perpetual set period_end đúng
- **Function:** SUB-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Subscription paid.
- **Bước thực hiện:** 1) Set cycle=monthly → period_end = start+1 tháng. 2) yearly → +1 năm. 3) perpetual → không có period_end (vĩnh viễn).
- **Dữ liệu test:** 3 cycle.
- **Kết quả mong đợi:** period_end tính đúng theo cycle; perpetual không hết hạn / không gắn grace.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-004 — Cycle không hợp lệ bị từ chối
- **Function:** SUB-002
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Tạo subscription cycle=`weekly`.
- **Dữ liệu test:** cycle ngoài enum.
- **Kết quả mong đợi:** HTTP 422 — enum {monthly, yearly, perpetual}.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-005 — Self-signup tự set trial 14 ngày
- **Function:** SUB-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Luồng self-signup tạo clinic mới.
- **Bước thực hiện:** 1) Đăng ký clinic mới qua self-signup. 2) GET subscription.
- **Dữ liệu test:** signup mới.
- **Kết quả mong đợi:** type=`trial`, status=`active`, trial_end = now + 14 ngày (default), tự động không cần thao tác admin.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-006 — Trial hết 14 ngày → vào grace/expired theo state machine
- **Function:** SUB-003
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Trial đến ngày trial_end (grace trial = 0d theo SUB-004).
- **Bước thực hiện:** 1) Chạy cron lifecycle tại trial_end.
- **Dữ liệu test:** trial_end = hôm nay.
- **Kết quả mong đợi:** Trial cycle có grace=0d → chuyển thẳng `expired` (đúng SUB-004); access bị giới hạn theo behavior matrix.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-007 — Grace period đúng theo cycle (monthly=7d, yearly=14d, trial=0d)
- **Function:** SUB-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Subscription paid monthly/yearly và trial, đều quá period_end.
- **Bước thực hiện:** 1) Chạy cron tại period_end cho từng cycle. 2) Kiểm tra status + grace_end.
- **Dữ liệu test:** monthly, yearly, trial.
- **Kết quả mong đợi:** monthly → grace 7 ngày; yearly → grace 14 ngày; trial → 0 ngày (vào expired ngay).
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-008 — Hết grace → chuyển expired
- **Function:** SUB-004
- **Loại:** Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Monthly subscription đang `grace`, quá 7 ngày.
- **Bước thực hiện:** 1) Chạy cron tại grace_end+1.
- **Dữ liệu test:** day 8 của grace.
- **Kết quả mong đợi:** status chuyển `expired`; truy cập read-only/chặn theo behavior matrix.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-009 — State machine: các transition hợp lệ
- **Function:** SUB-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Subscription tồn tại.
- **Bước thực hiện:** 1) Lần lượt kích: `pending → active`, `active → grace`, `grace → active` (sau renew), `grace → expired`, `active → suspended`, `suspended → active`, `expired → archived`, `suspended → archived`.
- **Dữ liệu test:** ma trận transition `pending → active → grace → expired → suspended → archived`.
- **Kết quả mong đợi:** Mỗi transition hợp lệ thành công, status cập nhật đúng, ghi audit event (SUB-010).
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-010 — State machine: chặn transition không hợp lệ
- **Function:** SUB-005
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Subscription `archived`.
- **Bước thực hiện:** 1) Thử transition `archived → active` trực tiếp. 2) Thử `pending → expired`.
- **Dữ liệu test:** transition ngoài đồ thị hợp lệ.
- **Kết quả mong đợi:** HTTP 409 — transition không hợp lệ; status giữ nguyên.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-011 — Transition cô lập theo clinic (RLS)
- **Function:** SUB-005
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B đều có subscription; thao tác từ context clinic.
- **Bước thực hiện:** 1) Trong context clinic B, thử đọc/đổi subscription của A.
- **Dữ liệu test:** subscription_id của A.
- **Kết quả mong đợi:** Không thấy/không sửa được subscription của A (RLS theo clinic_id); chỉ Super Admin (provider scope) mới thao tác cross-clinic.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-012 — SubscriptionGuard cho phép request khi active
- **Function:** SUB-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic có subscription `active`.
- **Bước thực hiện:** 1) Gọi API nghiệp vụ (GET + POST).
- **Dữ liệu test:** request thường.
- **Kết quả mong đợi:** Guard cho qua; request xử lý bình thường.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-013 — SubscriptionGuard chặn khi suspended/expired theo matrix
- **Function:** SUB-006
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic `expired` (read-only) và `suspended` (block).
- **Bước thực hiện:** 1) Gọi POST khi expired. 2) Gọi mọi method khi suspended.
- **Dữ liệu test:** POST/GET ở mỗi status.
- **Kết quả mong đợi:** expired → POST/PATCH/DELETE bị chặn (402/403), GET cho qua; suspended → mọi request bị chặn với thông báo trạng thái thuê bao.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-014 — Guard kiểm tra mỗi request (không bị bypass bởi cache cũ)
- **Function:** SUB-006
- **Loại:** Edge / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + Redis
- **Tiền điều kiện:** Subscription vừa bị suspend trong khi user đang có session.
- **Bước thực hiện:** 1) Suspend clinic. 2) User gửi request ngay sau đó.
- **Dữ liệu test:** thay đổi status giữa phiên.
- **Kết quả mong đợi:** Request kế tiếp bị guard chặn (status đọc realtime / cache invalidate); không bypass.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-015 — Behavior matrix định nghĩa GET/POST allowed đúng từng status
- **Function:** SUB-007
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic ở mỗi status: active, grace, expired, suspended, archived.
- **Bước thực hiện:** 1) Với mỗi status, gọi GET và POST, ghi nhận allow/deny.
- **Dữ liệu test:** ma trận status × method.
- **Kết quả mong đợi:** Khớp đúng matrix: active=full; grace=full (kèm cảnh báo); expired=read-only; suspended=block; archived=block.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-016 — Matrix nhất quán giữa nhiều endpoint nghiệp vụ
- **Function:** SUB-007
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic `expired`.
- **Bước thực hiện:** 1) Thử POST ở nhiều module (patient, appointment, billing).
- **Dữ liệu test:** nhiều endpoint write.
- **Kết quả mong đợi:** Tất cả write bị chặn nhất quán; không có endpoint "lọt".
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-017 — Read-only mode khi expired: cho GET, chặn POST/PATCH/DELETE
- **Function:** SUB-008
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic `expired`.
- **Bước thực hiện:** 1) GET dữ liệu. 2) POST/PATCH/DELETE.
- **Dữ liệu test:** mỗi HTTP method.
- **Kết quả mong đợi:** GET 200; POST/PATCH/DELETE bị chặn 402/403 với thông báo cần gia hạn.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-018 — Read-only vẫn cho phép xuất/đọc dữ liệu để gia hạn/export
- **Function:** SUB-008
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic `expired`.
- **Bước thực hiện:** 1) GET báo cáo/export dữ liệu.
- **Dữ liệu test:** read/export.
- **Kết quả mong đợi:** Cho phép đọc & export (không mất dữ liệu); chỉ chặn ghi.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-019 — Banner cảnh báo hiển thị đúng ở trial/grace
- **Function:** SUB-009
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Manual/UI (hoặc API trả banner state)
- **Tiền điều kiện:** Clinic ở trial (còn N ngày) và ở grace.
- **Bước thực hiện:** 1) Mở clinic app/đọc endpoint banner. 2) Kiểm tra nội dung + số ngày còn lại.
- **Dữ liệu test:** trial còn 5 ngày; grace ngày 2.
- **Kết quả mong đợi:** Top banner hiển thị cảnh báo trial/grace với số ngày còn lại đúng.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-020 — Không hiển thị banner khi active bình thường
- **Function:** SUB-009
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI
- **Tiền điều kiện:** Clinic `active`, còn xa period_end.
- **Bước thực hiện:** 1) Mở clinic app.
- **Dữ liệu test:** active dài hạn.
- **Kết quả mong đợi:** Không có banner cảnh báo gây nhiễu.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-021 — Mọi thay đổi subscription ghi clinic_subscription_event
- **Function:** SUB-010
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Subscription tồn tại.
- **Bước thực hiện:** 1) Thực hiện renew, convert, suspend, reactivate. 2) Query bảng `clinic_subscription_event`.
- **Dữ liệu test:** chuỗi thao tác.
- **Kết quả mong đợi:** Mỗi thay đổi sinh 1 event với loại, actor, before/after status, timestamp, reason (nếu có).
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-022 — Audit event cô lập theo clinic (RLS)
- **Function:** SUB-010
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Hai clinic có event riêng.
- **Bước thực hiện:** 1) Trong context clinic B, query subscription event.
- **Dữ liệu test:** so với A.
- **Kết quả mong đợi:** Clinic B chỉ thấy event của B; Super Admin thấy toàn bộ (provider scope).
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-023 — Super Admin gia hạn thủ công kèm lý do
- **Function:** SUB-011
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Subscription đang grace/expired; đăng nhập Super Admin.
- **Bước thực hiện:** 1) Submit form renewal (period_end mới + lý do). 2) GET subscription.
- **Dữ liệu test:** `{period_end:"+1 tháng", reason:"thanh toán offline"}`.
- **Kết quả mong đợi:** period_end gia hạn; status về `active`; event renewal ghi kèm reason + actor.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-024 — Renewal thiếu lý do bị từ chối
- **Function:** SUB-011
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Super Admin.
- **Bước thực hiện:** 1) Submit renewal không có reason.
- **Dữ liệu test:** reason rỗng.
- **Kết quả mong đợi:** HTTP 422 — bắt buộc lý do (audit requirement).
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-025 — Chỉ Super Admin được gia hạn (401/403)
- **Function:** SUB-011
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Gọi renewal với role Clinic Admin. 2) Gọi không token.
- **Dữ liệu test:** token clinic admin; không token.
- **Kết quả mong đợi:** 403 với clinic admin; 401 khi không token.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-026 — Convert trial → paid (sales-led, super admin)
- **Function:** SUB-012
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic đang `trial`; Super Admin tại `/admin/clinics/:id`.
- **Bước thực hiện:** 1) Click Convert → form chọn cycle + period_end + amount. 2) Submit. 3) GET subscription.
- **Dữ liệu test:** `{cycle:"yearly", period_end, amount}`.
- **Kết quả mong đợi:** type chuyển `paid`, cycle/period_end/amount set đúng, status `active`; event convert ghi nhận.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-027 — Convert khi không phải trial bị từ chối
- **Function:** SUB-012
- **Loại:** Negative / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic đã `paid`.
- **Bước thực hiện:** 1) Gọi convert trial→paid.
- **Dữ liệu test:** subscription paid.
- **Kết quả mong đợi:** HTTP 409 — chỉ convert được từ trial.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-028 — Upgrade plan đổi cycle monthly → yearly
- **Function:** SUB-013
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic paid monthly; Super Admin.
- **Bước thực hiện:** 1) Upgrade sang yearly. 2) GET subscription.
- **Dữ liệu test:** monthly→yearly.
- **Kết quả mong đợi:** cycle=yearly; period_end + grace tính lại theo yearly (14d); event ghi nhận.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-029 — Chỉ Super Admin upgrade (403)
- **Function:** SUB-013
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Role Clinic Admin.
- **Bước thực hiện:** 1) Gọi upgrade. 2) không token.
- **Dữ liệu test:** token clinic admin; không token.
- **Kết quả mong đợi:** 403 với clinic admin; 401 không token.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-030 — Suspend clinic thủ công kèm reason + visible toggle
- **Function:** SUB-014
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic `active`; Super Admin.
- **Bước thực hiện:** 1) Suspend với reason + visible toggle. 2) User của clinic thử truy cập.
- **Dữ liệu test:** `{reason:"vi phạm điều khoản", visible:true}`.
- **Kết quả mong đợi:** status=`suspended`; mọi request nghiệp vụ bị chặn; event ghi reason + actor; toggle visible quyết định clinic có thấy lý do hay không.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-031 — Suspend thiếu reason bị từ chối
- **Function:** SUB-014
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Super Admin.
- **Bước thực hiện:** 1) Suspend không reason.
- **Dữ liệu test:** reason rỗng.
- **Kết quả mong đợi:** HTTP 422 — bắt buộc reason.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-032 — Chỉ Super Admin suspend (403/401)
- **Function:** SUB-014
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Suspend với role thường. 2) không token.
- **Dữ liệu test:** token clinic admin; không token.
- **Kết quả mong đợi:** 403 với clinic admin; 401 không token.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-033 — Reactivate clinic từ suspended → active
- **Function:** SUB-015
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic `suspended`; Super Admin.
- **Bước thực hiện:** 1) Reactivate. 2) User clinic truy cập lại.
- **Dữ liệu test:** suspended clinic.
- **Kết quả mong đợi:** status=`active`; truy cập khôi phục đầy đủ; event reactivate ghi nhận; dữ liệu nguyên vẹn.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-034 — Reactivate khi không ở suspended bị từ chối
- **Function:** SUB-015
- **Loại:** Negative / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic `active`/`archived`.
- **Bước thực hiện:** 1) Gọi reactivate.
- **Dữ liệu test:** status không phải suspended.
- **Kết quả mong đợi:** HTTP 409 — transition không hợp lệ (chỉ suspended → active).
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-035 — Archive clinic giữ data 90 ngày
- **Function:** SUB-016
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic expired/suspended; Super Admin.
- **Bước thực hiện:** 1) Archive. 2) GET subscription + kiểm tra retention deadline.
- **Dữ liệu test:** archive clinic.
- **Kết quả mong đợi:** status=`archived`; access bị chặn; data giữ nguyên với hạn xóa = archived_at + 90 ngày; event ghi nhận.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-036 — Archive cô lập đúng clinic, không ảnh hưởng clinic khác (RLS)
- **Function:** SUB-016
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B active.
- **Bước thực hiện:** 1) Archive A. 2) Kiểm tra B.
- **Dữ liệu test:** A archived, B giữ.
- **Kết quả mong đợi:** Chỉ A bị archive/chặn; B hoạt động bình thường, dữ liệu B không bị động.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-037 — Auto export trước hard delete + email link (30d trước xóa)
- **Function:** SUB-017
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + cron
- **Tiền điều kiện:** Clinic `archived` đạt mốc 60 ngày (30 ngày trước hard delete tại 90d).
- **Bước thực hiện:** 1) Chạy cron/trigger admin export final. 2) Kiểm tra file export + email.
- **Dữ liệu test:** clinic có dữ liệu nghiệp vụ.
- **Kết quả mong đợi:** Sinh gói export đầy đủ; gửi email kèm link tải (hiệu lực hợp lý); event ghi nhận.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-038 — Export chỉ chứa dữ liệu của clinic đó (RLS)
- **Function:** SUB-017
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Nhiều clinic có dữ liệu.
- **Bước thực hiện:** 1) Export clinic A. 2) Kiểm tra nội dung.
- **Dữ liệu test:** so với clinic khác.
- **Kết quả mong đợi:** Export chỉ chứa dữ liệu clinic A (scoped to clinic_id), không rò rỉ dữ liệu clinic khác.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-039 — Export trigger thủ công từ admin panel (SUB-017)
- **Function:** SUB-017
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Super Admin tại admin panel.
- **Bước thực hiện:** 1) Trigger export thủ công cho clinic archived.
- **Dữ liệu test:** clinic archived.
- **Kết quả mong đợi:** Export khởi chạy; trạng thái job theo dõi được; chỉ Super Admin trigger được (403 với role khác).
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-040 — Hard delete vĩnh viễn data archived sau 90 ngày (cron)
- **Function:** SUB-018
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + cron
- **Tiền điều kiện:** Clinic `archived` đúng 90 ngày; đã auto export (SUB-017).
- **Bước thực hiện:** 1) Chạy cron hard delete. 2) Kiểm tra dữ liệu clinic.
- **Dữ liệu test:** archived_at = now-90d.
- **Kết quả mong đợi:** Dữ liệu nghiệp vụ bị xóa vĩnh viễn; audit/event giữ theo yêu cầu pháp lý; event hard_delete ghi nhận.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-041 — Không hard delete khi chưa đủ 90 ngày
- **Function:** SUB-018
- **Loại:** Negative / Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + cron
- **Tiền điều kiện:** Clinic archived 60 ngày.
- **Bước thực hiện:** 1) Chạy cron hard delete.
- **Dữ liệu test:** archived_at = now-60d.
- **Kết quả mong đợi:** Dữ liệu vẫn còn; chưa xóa.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-042 — Hard delete cô lập đúng clinic (RLS), không xóa nhầm
- **Function:** SUB-018
- **Loại:** Security (RLS)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + cron
- **Tiền điều kiện:** Clinic A archived 90d; Clinic B active.
- **Bước thực hiện:** 1) Chạy cron. 2) Kiểm tra B.
- **Dữ liệu test:** A xóa, B giữ.
- **Kết quả mong đợi:** Chỉ dữ liệu A bị xóa; dữ liệu B nguyên vẹn (delete scoped to clinic_id).
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-043 — Reminder gửi đúng mốc D-14/-7/-3/-1/0
- **Function:** SUB-019
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + cron
- **Tiền điều kiện:** Subscription có period_end xác định.
- **Bước thực hiện:** 1) Chạy cron reminder tại từng mốc 14/7/3/1/0 ngày trước hết hạn.
- **Dữ liệu test:** period_end tương ứng các mốc.
- **Kết quả mong đợi:** Mỗi mốc gửi đúng 1 email + in-app banner; không gửi sai mốc/trùng.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-044 — Không gửi reminder cho perpetual / clinic archived
- **Function:** SUB-019
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB) + cron
- **Tiền điều kiện:** Clinic cycle=perpetual và clinic archived.
- **Bước thực hiện:** 1) Chạy cron reminder.
- **Dữ liệu test:** perpetual; archived.
- **Kết quả mong đợi:** Không gửi reminder (perpetual không hết hạn; archived ngoài luồng).
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-045 — Daily reminder trong grace, banner đỏ dần
- **Function:** SUB-020
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + cron
- **Tiền điều kiện:** Clinic đang `grace`.
- **Bước thực hiện:** 1) Chạy cron mỗi ngày trong grace. 2) Kiểm tra banner severity.
- **Dữ liệu test:** grace day 1..7.
- **Kết quả mong đợi:** Gửi reminder hằng ngày; banner tăng mức cảnh báo (đỏ dần) theo số ngày còn lại.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-046 — Dừng daily reminder khi grace kết thúc hoặc đã gia hạn
- **Function:** SUB-020
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB) + cron
- **Tiền điều kiện:** Clinic đã renew (về active) hoặc hết grace (expired).
- **Bước thực hiện:** 1) Chạy cron sau khi renew. 2) Chạy cron sau khi expired.
- **Dữ liệu test:** trạng thái thoát grace.
- **Kết quả mong đợi:** Ngừng gửi daily grace reminder khi không còn ở grace.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-047 — Dashboard metrics tính đúng MRR/ARR/churn/conversion
- **Function:** SUB-021
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có dữ liệu subscription nhiều clinic; Super Admin.
- **Bước thực hiện:** 1) GET `/admin/dashboard` metrics.
- **Dữ liệu test:** tập subscription mẫu (active/trial/churned).
- **Kết quả mong đợi:** MRR, ARR, churn rate, conversion rate tính đúng theo công thức trên dữ liệu mẫu.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-048 — Dashboard chỉ Super Admin truy cập (403/401)
- **Function:** SUB-021
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Role Clinic Admin.
- **Bước thực hiện:** 1) GET dashboard metrics. 2) không token.
- **Dữ liệu test:** token clinic admin; không token.
- **Kết quả mong đợi:** 403 với clinic admin; 401 không token (metrics cross-clinic, provider-only).
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-049 — Metrics tổng hợp toàn provider (không bị RLS lọc nhầm)
- **Function:** SUB-021
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Nhiều clinic; Super Admin (provider scope).
- **Bước thực hiện:** 1) GET dashboard.
- **Dữ liệu test:** dữ liệu nhiều clinic.
- **Kết quả mong đợi:** Metrics tổng hợp toàn bộ clinic (provider scope) — đây là endpoint provider-level, không bị RLS theo một clinic; xác nhận con số tổng hợp đầy đủ.
- **Coverage hiện tại:** MISSING — cần xác minh test file.

### TC-SUB-050 — [v2] Auto-renew qua webhook VNPay/MoMo thành công
- **Function:** SUB-022
- **Loại:** Happy path
- **Ưu tiên:** P1 (Phase 2)
- **Layer:** Integration (real DB) + mock gateway
- **Tiền điều kiện:** Auto-renew bật; payment token hợp lệ; subscription đến period_end.
- **Bước thực hiện:** 1) Cron auto-renew gọi gateway. 2) Nhận webhook success.
- **Dữ liệu test:** sandbox VNPay/MoMo.
- **Kết quả mong đợi:** Charge thành công; period_end gia hạn; status active; event ghi nhận.
- **Coverage hiện tại:** MISSING — cần xác minh test file (IDEA/v2, chưa có task).

### TC-SUB-051 — [v2] Webhook auto-renew xác thực chữ ký + idempotent
- **Function:** SUB-022
- **Loại:** Security / Edge
- **Ưu tiên:** P1 (Phase 2)
- **Layer:** E2E (httpx) + mock webhook
- **Tiền điều kiện:** Webhook endpoint cấu hình secret.
- **Bước thực hiện:** 1) Gửi webhook chữ ký sai. 2) Gửi webhook hợp lệ 2 lần cùng id.
- **Dữ liệu test:** payload giả mạo; payload trùng.
- **Kết quả mong đợi:** Chữ ký sai → 400/401, không đổi trạng thái; webhook trùng xử lý idempotent (không gia hạn nhiều lần).
- **Coverage hiện tại:** MISSING — cần xác minh test file (IDEA/v2).

### TC-SUB-052 — [v2] Auto-renew thất bại → rơi vào grace/dunning
- **Function:** SUB-022
- **Loại:** Negative / Edge
- **Ưu tiên:** P2 (Phase 2)
- **Layer:** Integration (real DB) + mock gateway
- **Tiền điều kiện:** Auto-renew bật; gateway decline.
- **Bước thực hiện:** 1) Cron auto-renew, gateway trả fail.
- **Dữ liệu test:** thẻ decline.
- **Kết quả mong đợi:** Không gia hạn; subscription vào grace theo cycle; gửi reminder; không tạo subscription "mồ côi".
- **Coverage hiện tại:** MISSING — cần xác minh test file (IDEA/v2).

### TC-SUB-053 — [v2] Xuất hóa đơn điện tử cho clinic (VNPT/Viettel)
- **Function:** SUB-023
- **Loại:** Happy path
- **Ưu tiên:** P2 (Phase 2)
- **Layer:** Integration (real DB) + mock e-invoice provider
- **Tiền điều kiện:** Clinic paid; cấu hình e-invoice provider.
- **Bước thực hiện:** 1) Phát hành e-invoice cho kỳ thanh toán. 2) Kiểm tra trạng thái phát hành.
- **Dữ liệu test:** thông tin xuất hóa đơn clinic.
- **Kết quả mong đợi:** E-invoice phát hành thành công qua VNPT/Viettel; lưu mã/đường dẫn hóa đơn; gắn với clinic + kỳ.
- **Coverage hiện tại:** MISSING — cần xác minh test file (IDEA/v2).

### TC-SUB-054 — [v2] Lỗi provider e-invoice được xử lý an toàn
- **Function:** SUB-023
- **Loại:** Negative / Edge
- **Ưu tiên:** P2 (Phase 2)
- **Layer:** Integration (real DB) + mock provider
- **Tiền điều kiện:** Provider e-invoice trả lỗi/timeout.
- **Bước thực hiện:** 1) Phát hành e-invoice khi provider lỗi.
- **Dữ liệu test:** mô phỏng lỗi provider.
- **Kết quả mong đợi:** Đánh dấu phát hành thất bại; có cơ chế retry; không double-issue; thông báo admin.
- **Coverage hiện tại:** MISSING — cần xác minh test file (IDEA/v2).

### TC-SUB-055 — [v2] Subscription tiers Basic/Pro/Enterprise giới hạn theo tier
- **Function:** SUB-024
- **Loại:** Happy path
- **Ưu tiên:** P2 (Phase 2)
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Tier được định nghĩa với limit khác nhau.
- **Bước thực hiện:** 1) Gán clinic vào từng tier. 2) Kiểm tra limit áp dụng.
- **Dữ liệu test:** Basic/Pro/Enterprise.
- **Kết quả mong đợi:** Limit (users/locations/...) áp đúng theo tier; nâng tier nới limit.
- **Coverage hiện tại:** MISSING — cần xác minh test file (IDEA/v2).

### TC-SUB-056 — [v2] Vượt limit của tier bị chặn
- **Function:** SUB-024
- **Loại:** Negative / Edge
- **Ưu tiên:** P2 (Phase 2)
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic ở Basic, đạt limit.
- **Bước thực hiện:** 1) Tạo vượt limit Basic.
- **Dữ liệu test:** vượt quota tier.
- **Kết quả mong đợi:** HTTP 402/403 — gợi ý nâng tier; không tạo vượt limit.
- **Coverage hiện tại:** MISSING — cần xác minh test file (IDEA/v2).

### TC-SUB-057 — [v2] Free tier vĩnh viễn (siêu hạn chế) hoạt động không hết hạn
- **Function:** SUB-025
- **Loại:** Happy path
- **Ưu tiên:** P2 (Phase 2)
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic gán Free tier.
- **Bước thực hiện:** 1) Sử dụng tính năng cơ bản lâu dài. 2) Chạy cron lifecycle.
- **Dữ liệu test:** free tier limit tối thiểu.
- **Kết quả mong đợi:** Không hết hạn (perpetual free); chỉ cho phép tính năng/limit cực hạn chế.
- **Coverage hiện tại:** MISSING — cần xác minh test file (IDEA/v2).

### TC-SUB-058 — [v2] Free tier chặn tính năng/limit vượt mức
- **Function:** SUB-025
- **Loại:** Negative / Edge
- **Ưu tiên:** P2 (Phase 2)
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic Free tier đạt limit.
- **Bước thực hiện:** 1) Thử dùng tính năng ngoài free tier / vượt limit.
- **Dữ liệu test:** vượt giới hạn free.
- **Kết quả mong đợi:** Bị chặn với upgrade prompt; không cho dùng tính năng trả phí.
- **Coverage hiện tại:** MISSING — cần xác minh test file (IDEA/v2).

---

## 3. Ghi chú tổng hợp Coverage

- **25/25 function chưa triển khai:** SUB-001..021 = `⬜ TODO` (TASK-026 / 028 / 030 / 006), SUB-022..025 = `💡 IDEA` (v2, chưa gán task). Không có test file thực tế để đối chiếu trong môi trường hiện tại (repo `clinic-cms-merge/app` và `tests` không truy cập được — Bash/Glob trả rỗng).
- **COVERED: 0 · PARTIAL: 0 · MISSING: 25.**
- **Nhóm ưu tiên P0 khi implement (đề xuất thứ tự test trước):** state machine (SUB-005), SubscriptionGuard + behavior matrix + read-only (SUB-006/007/008), trial/grace lifecycle (SUB-003/004), audit event (SUB-010), suspend/reactivate/archive (SUB-014/015/016), auto-export + hard delete 90d (SUB-017/018), renewal/convert thủ công (SUB-011/012), dashboard quyền (SUB-021).
- **RLS / cô lập clinic:** mọi case đụng dữ liệu domain hoặc subscription per-clinic đã kèm case cô lập theo `clinic_id` (TC-SUB-011, -022, -036, -038, -042). Lưu ý SUB-021 dashboard là **provider-level** (tổng hợp cross-clinic) nên không bị RLS theo một clinic — đã có TC-SUB-049 xác nhận.
- **Quyền:** mọi thao tác Super Admin (renewal, convert, upgrade, suspend, dashboard, export trigger) đều có case 401 (không token) + 403 (role không đủ): TC-SUB-025, -029, -032, -039, -048.
- Khi TASK-026/028/030 hoàn tất, cập nhật cột Coverage thành COVERED kèm `test_file::test_name` cho từng TC và xóa nhãn "cần xác minh test file".
