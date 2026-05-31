# TASK-045 — Thiết kế chức năng VSS BHYT Integration

| Trường        | Giá trị                                        |
|---------------|------------------------------------------------|
| Task ID       | TASK-045                                       |
| Tiêu đề       | VSS BHYT Integration (BE + FE, 2 màn hình)    |
| Ngày hoàn thành | 2026-05-01                                  |
| Trạng thái    | DONE                                           |
| Nhánh         | feature/task-045-vss-integration               |
| Tác giả       | Code Implementation Agent                     |

---

## Mục đích

TASK-045 triển khai tích hợp VSS (Vietnam Social Security) cho hệ thống BHYT (Bảo hiểm y tế). Phạm vi v1 bao gồm 3 integration requirements:

- **INT-001** — Kiểm tra thẻ BHYT (eligibility check): Xác minh thẻ BHYT của bệnh nhân có còn hiệu lực không trước khi khám.
- **INT-002** — Nộp hồ sơ thanh toán BHYT (submit claim): Gửi hồ sơ thanh toán lên VSS sau khi hoàn tất lượt khám.
- **INT-003** — Lịch sử đồng bộ (sync log): Theo dõi toàn bộ lịch sử giao tiếp với VSS theo từng phòng khám.

---

## Phạm vi

### Trong phạm vi v1

- Mock VSS client (không gọi VSS thật) — đủ để FE tích hợp end-to-end.
- 4 endpoints BE (eligibility-check, submit-claim, sync-log, status).
- 2 trang FE admin (VssIntegrationConfigPage, VssSyncLogPage).
- Schema migration `0029_vss_sync_log` với RLS theo clinic_id.
- Test coverage: 22 unit BE + 15 integration BE + 581 FE Vitest.

### Ngoài phạm vi v1 (deferred)

- Gọi HTTP thật đến API VSS (v2 real client).
- Mã hóa PII trong payload JSONB (TASK-037 P2).
- Seeding permission `vss:read`/`vss:sync` (post-TASK-034).
- Idempotency cho submit-claim (v2).

---

## Schema Migration `0029_vss_sync_log`

### Bảng `vss_sync_log`

| Cột                | Kiểu              | Mô tả                                                 |
|--------------------|-------------------|-------------------------------------------------------|
| `id`               | UUID (PK)         | Khóa chính, gen_random_uuid()                        |
| `clinic_id`        | UUID (FK→clinic)  | Phòng khám sở hữu bản ghi, NOT NULL                  |
| `sync_type`        | TEXT + CHECK      | Loại đồng bộ: check_eligibility / submit_claim / pull_status |
| `request_payload`  | JSONB             | Dữ liệu gửi đi (card_no, full_name, dob, visit_id)  |
| `response_payload` | JSONB             | Kết quả trả về từ VSS                                |
| `status`           | TEXT + CHECK      | Trạng thái: pending / success / failed / timeout     |
| `error_message`    | TEXT (nullable)   | Thông báo lỗi khi status = failed/timeout            |
| `synced_at`        | TIMESTAMPTZ       | Thời điểm gọi API, server_default=now()              |
| `synced_by`        | UUID (FK→user)    | Người dùng thực hiện đồng bộ (nullable)              |

### RLS (Row Level Security)

```sql
ALTER TABLE vss_sync_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE vss_sync_log FORCE ROW LEVEL SECURITY;
CREATE POLICY vss_sync_log_clinic_isolation
    ON vss_sync_log
    USING (clinic_id = current_setting('app.current_clinic_id')::uuid);
```

Pattern nhất quán với toàn bộ project. Belt-and-braces: endpoint cũng filter `WHERE clinic_id = ?` để đảm bảo không lộ dữ liệu dù RLS bị bypass bởi superuser role trong dev.

### Index

```sql
CREATE INDEX ix_vss_sync_log_clinic_synced_at
    ON vss_sync_log (clinic_id, synced_at DESC);
```

Tối ưu cho query list sync-log theo clinic, sắp xếp mới nhất trước.

---

## VssClient Adapter

### v1 Mock (hiện tại)

File: `app/integrations/vss/client.py`

| Method              | Mô tả                              | Return type           |
|---------------------|------------------------------------|-----------------------|
| `check_eligibility` | Kiểm tra thẻ BHYT                  | `VssEligibilityResult` |
| `submit_claim`      | Nộp hồ sơ thanh toán               | `VssClaimResult`      |
| `get_status`        | Lấy trạng thái hồ sơ              | `VssStatusResult`     |
| `ping`              | Health-check kết nối VSS          | `bool`                |

Tất cả result class có `.to_dict()` và `.raw` (chứa flag `mock: true`).

Module-level singleton: `vss_client = VssClient()`

### v2 TODO (real HTTP)

Mỗi method có comment `TODO v2: <HTTP method> <URL>` để dễ tra. Config đã sẵn sàng:
- `settings.VSS_API_URL` — base URL
- `settings.VSS_API_KEY` — API key (giá trị placeholder "CHANGE-ME-VSS-API-KEY")

---

## Endpoints (4)

Prefix: `/api/v1/integrations/vss`  
Router file: `app/modules/integrations/vss/api/routes.py`

### POST `/eligibility-check`

- **Permission**: `vss:read`
- **Request**: `{ patient_bhyt_card_no: str (10-20 ký tự), full_name?: str, dob?: str (ISO8601) }`
- **Response**: `{ data: EligibilityData, log_id: UUID }`
- **Flow**: Validate → _create_log(pending) → vss_client.check_eligibility → _update_log(success/failed) → commit → return
- **Lỗi**: 422 nếu card_no quá ngắn, dob sai format; 500 nếu VSS client raises.

### POST `/submit-claim`

- **Permission**: `vss:sync`
- **Request**: `{ visit_id: UUID }`
- **Response**: `{ data: ClaimData { claim_id, status }, log_id: UUID }`
- **Lưu ý v1**: Không idempotent — cùng visit_id submit 2 lần tạo 2 log rows + 2 claim IDs khác nhau. Expected v1; v2 cần dedup.

### GET `/sync-log`

- **Permission**: `vss:read`
- **Query params**: `from`, `to` (ISO8601 datetime), `sync_type`, `status`, `page` (≥1), `page_size` (1-100, default 20)
- **Response**: `{ items: [...], total: int, page: int, page_size: int }`
- **Filter**: Kết hợp RLS (theo context var) + explicit WHERE clinic_id = ? (belt-and-braces)

### GET `/status`

- **Permission**: `vss:read`
- **Response**: `{ connected: bool, message: str }`
- **Đặc điểm**: Luôn trả 200 — bắt mọi exception, trả `connected: false` + message. Phù hợp cho FE polling.

---

## FE Pages

Repo: `clinic-cms-web-w5v`, branch `feature/task-045-vss-integration-fe`

### VssIntegrationConfigPage

- **Route**: `/admin/integrations/vss`
- **Chức năng**: Hiển thị trạng thái kết nối VSS, form cấu hình (API URL, API Key ẩn với eye-toggle, facility code), nút "Lưu" và "Kiểm tra kết nối".
- **Token**: indigo-50/100/600/700, emerald-500, red-500 (MediZen design system)
- **i18n**: namespace `vss`, Vietnamese-first

### VssSyncLogPage

- **Route**: `/admin/integrations/vss/log`
- **Chức năng**: Bộ lọc (from/to/type/status), bảng danh sách với badges màu (success=emerald, failed=red, pending=amber, timeout=orange), modal chi tiết với JSON viewer có thể mở/đóng, phân trang (chỉ hiện khi total > page_size).
- **data-testid**: Coverage tốt — dễ viết test E2E.
- **Date format**: `toLocaleString('vi-VN')`

---

## Stub Strategy (4 TODOs)

Tất cả 4 stub đều có inline TODO rõ ràng và interface production đã code sẵn sau stub.

| # | Stub | Khi nào thay | File |
|---|------|-------------|------|
| 1 | `require_feature_stub("bhyt")` → `require_feature("bhyt")` | Post-TASK-034 merge | `routes.py` |
| 2 | `const bhytEnabled = true` → `useFeatureFlag('bhyt')` | Post-TASK-034 merge | 2 FE pages |
| 3 | VSS mock client → real httpx | v2 | `client.py` |
| 4 | `vss:read`/`vss:sync` permissions chưa seed | Post-TASK-034 migration | `routes.py` header comment |

**Lưu ý FE**: Sau khi thay stub #2, cần move tất cả `useState` ABOVE `if (!bhytEnabled) return <NotEnabledFallback />` để tránh vi phạm Rules of Hooks. Áp dụng cho cả `VssIntegrationConfigPage` và `VssSyncLogPage`.

---

## Test Coverage

| Layer        | Số test | Ghi chú                                                             |
|--------------|---------|---------------------------------------------------------------------|
| BE unit      | 22      | 12 VssClient + 10 VssSyncLog (incl. test F3-1: vss failure → FAILED) |
| BE integration | 15    | 13 gốc + 2 từ review F3 (vss-failure + RLS cross-tenant)            |
| FE Vitest    | 581     | i18n parity, render, form, modal, pagination                        |
| **Tổng BE**  | **37**  | Tất cả PASS                                                         |

### 2 test thêm từ review (F3)

**Test 1** (`test_vss_sync_log.py::TestVssServiceCheckEligibility::test_check_eligibility_vss_failure_marks_log_failed`):
Monkeypatch `vss_client.check_eligibility` raise `httpx.NetworkError` → assert log entry `status='failed'`, `error_message` chứa "VSS unreachable", `flush` gọi ≥2 lần.

**Test 2** (`test_vss_endpoints.py::TestSyncLogRlsCrossTenantIsolation::test_sync_log_rls_blocks_cross_tenant`):
2 clinic A và B với 1 sync_log entry mỗi → GET /sync-log với X-Clinic-Id tương ứng → assert disjoint IDs, không cross-contamination.

---

## Cross-Task Coordination (CRITICAL)

### TASK-034 (BHYT Feature Flag) — REQUIRED trước khi đưa lên production

1. BE: Thay `require_feature_stub("bhyt")` → `require_feature("bhyt")` trong `routes.py`
2. FE: Thay `const bhytEnabled = true` → `useFeatureFlag('bhyt')` trong 2 pages **VÀ** move `useState` lên trên `if (!bhytEnabled)` early return
3. DB: Seed `vss:read` và `vss:sync` permissions trong migration của TASK-034 (hoặc migration mới)

> **Warning**: Cho đến khi TASK-034 land và permissions được seed, mọi endpoint VSS đều trả 403.

### TASK-037 P2 (PII Encryption)

`vss_sync_log.request_payload` và `response_payload` chứa PII nhạy cảm:
- `request_payload`: card_no (số thẻ BHYT), full_name, dob
- `response_payload`: full_name, dob, insurer_code, coverage_from/to

Cần xử lý một trong ba phương án: (a) encrypt at column level, (b) redact trước khi lưu, (c) TTL purge. Đánh dấu cho TASK-037 P2 security review.

### TASK-038 B.15-B.17 (Parallel Migration Conflict)

Migration `0029_vss_sync_log` hiện có `down_revision="65fc9ae59ba5"` (head hiện tại). Nếu TASK-038 B.15-B.17 land trước và tạo migration với cùng head, sẽ cần:
```
alembic revision --rev-id 0030_vss_sync_log ...
```
Restamp `down_revision` của 0029 thành revision mới của TASK-038. Trivial — re-run alembic trong CI.

### TASK-035 (Sidebar Role-based Nav)

Nav items VSS đã đặt trong group `key:"admin"` với `permission:"vss:read"`. Sẽ hoạt động tự động sau khi TASK-035 land với `ROLE_NAV_SECTIONS`. Verify lại sau khi merge.

---

## Quyết định Hoãn (Deferred Decisions)

| Vấn đề | Mô tả | Thời điểm quyết định |
|--------|-------|----------------------|
| Idempotent submit-claim | Thêm unique constraint `(clinic_id, visit_id, sync_type='submit_claim', status='success')` hoặc idempotency-key header | v2 real client |
| PII encryption `sync_log` | Encrypt JSONB columns hoặc redact-before-write hoặc TTL purge | TASK-037 P2 |
| Real VSS HTTP | Thay mock bằng httpx.AsyncClient thật | v2 |
| VssClient DI | Chuyển từ singleton sang dependency-injected để test dễ hơn | v2 |
