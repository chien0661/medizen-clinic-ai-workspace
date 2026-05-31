# Thiết Kế Chức Năng: PII Lifecycle & Right to Erasure

**TASK-038 B.15-B.17 — Functional Design Document**

| Trường | Giá trị |
|--------|---------|
| Task | TASK-038 B.15, B.16, B.17 |
| Phiên bản | 1.0 |
| Trạng thái | DONE |
| Ngày hoàn thành | 2026-05-01 |
| Tác giả | Code Implementation + Documentation Agent |
| NFR liên quan | NFR-032, NFR-040 (Right to Erasure — Nghị định 13 / PDPD) |
| Worktree | `clinic-cms-w5x` |
| Branch | `feature/task-038-b15-pii-lifecycle` |

---

## Mục Đích

Hệ thống phải đảm bảo quyền được xóa dữ liệu cá nhân (Right to Erasure) theo **Điều 16 Nghị định 13/2023/NĐ-CP** (Bảo vệ dữ liệu cá nhân — PDPD) và tương đương GDPR Article 17.

**Hai cơ chế:**

1. **B.15-B.17 Manual Erasure** — Xóa chủ động khi bệnh nhân yêu cầu (2-step admin confirmation flow).
2. **B.16 PII Archive Cron** — Tự động lưu trữ lạnh (cold storage) sau 7 năm không truy cập.

---

## Schema Migration `0028_pii_archive_table`

**File**: `alembic/versions/0028_pii_archive_table.py`

> Lưu ý: Số hiệu `0028` là số tạm thời trong worktree. Khi merge sẽ đổi số theo vị trí trong chuỗi migration chính (TBD bởi orchestrator — xem phần Cross-task Coordination).

### Bảng mới: `patient_archive`

```sql
CREATE TABLE patient_archive (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_patient_id UUID NOT NULL UNIQUE,   -- UniqueConstraint: ngăn double-archival
    clinic_id           UUID NOT NULL,
    payload             JSONB NOT NULL,          -- Snapshot PII tại thời điểm xóa
    archive_reason      VARCHAR(50) NOT NULL,    -- "manual_erasure" | "retention_exceeded"
    archived_by         UUID,                    -- NULL = system actor (cron)
    archived_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_patient_archive_original UNIQUE (original_patient_id)
);

CREATE INDEX ix_patient_archive_clinic_id ON patient_archive (clinic_id);
CREATE INDEX ix_patient_archive_archived_at ON patient_archive (archived_at);
```

### Cột mới trên bảng `patient`

```sql
ALTER TABLE patient ADD COLUMN last_accessed_at TIMESTAMPTZ;

CREATE INDEX ix_patient_last_accessed_at
  ON patient (last_accessed_at)
  WHERE is_deleted = FALSE;
```

`last_accessed_at` được cập nhật mỗi khi bệnh nhân được đọc qua `audit_patient_read()`. Cron dùng cột này để xác định bệnh nhân nào đã quá 7 năm không truy cập.

### Permission seed

```sql
INSERT INTO permission (code, description)
VALUES ('patient.erase', 'Right to Erasure — xóa bệnh nhân theo yêu cầu')
ON CONFLICT DO NOTHING;

INSERT INTO role_permission (role_id, permission_id)
SELECT r.id, p.id FROM role r, permission p
WHERE r.name = 'admin' AND p.code = 'patient.erase'
ON CONFLICT DO NOTHING;
```

---

## Endpoints

### POST `/patients/{id}/erase/request`

**Mục đích**: Bước 1 — Admin yêu cầu xóa, hệ thống sinh confirmation token.

| Trường | Giá trị |
|--------|---------|
| Method | POST |
| Path | `/api/v1/patients/{patient_id}/erase/request` |
| Permission | `patient.erase` (admin only) |
| Response 200 | `{"confirmation_token": "<uuid4>", "message": "..."}` |
| TTL token | 300 giây (5 phút) |

**Logic**:
- Sinh UUID4 token.
- Lưu Redis key `erase:confirm:{patient_id}` với payload `{token, admin_user_id}` và TTL=300s.
- Ghi đè token cũ nếu admin gọi lại (idempotent re-request).
- Trả token về caller để dùng trong bước 2.

---

### DELETE `/patients/{id}/erase`

**Mục đích**: Bước 2 — Admin xác nhận xóa bằng token + lý do.

| Trường | Giá trị |
|--------|---------|
| Method | DELETE |
| Path | `/api/v1/patients/{patient_id}/erase` |
| Permission | `patient.erase` (admin only) |
| Body | `{"confirmation_token": "<uuid4>", "reason": "<5-500 ký tự>"}` |
| Response 200 | `{"status": "erased", "patient_id": "..."}` |
| Response 403 | Token expired / missing / wrong / wrong admin |
| Response 404 | Patient not found / already erased |
| Response 422 | reason quá ngắn (< 5 ký tự) |

---

## Luồng 2-Step Erasure + Token Binding (Post-Fix)

```
Admin A                         System (Redis)              DB
  │                                  │                       │
  ├─ POST /erase/request ──────────► │                       │
  │                                  │ SET erase:confirm:PID │
  │                                  │ {token, admin_user_id=A, TTL=300s}
  │ ◄── {confirmation_token} ────────│                       │
  │                                  │                       │
  │  [Admin A giữ token, gọi DELETE] │                       │
  │                                  │                       │
  ├─ DELETE /erase {token, reason} ─►│                       │
  │                           verify: token match? ✓          │
  │                           verify: admin_user_id == A? ✓   │
  │                           GET erase:confirm:PID ──────────│
  │                                  │ DEL key (single-use)   │
  │                                  │           ────────────►│ cascade soft-delete
  │                                  │                       │ insert patient_archive
  │                                  │                       │ write audit_log
  │ ◄── {status: "erased"} ──────────│                       │
```

**Token binding** (fix post-review finding #2): `_verify_and_consume_token()` kiểm tra `stored.admin_user_id == executing_admin_user_id`. Admin B không thể dùng token của Admin A.

---

## Cascade Soft-Delete

Khi xóa bệnh nhân, hệ thống soft-delete theo thứ tự (không phụ thuộc FK constraint):

| Bảng | Điều kiện |
|------|-----------|
| `visit_vitals` | `visit_id IN (SELECT id FROM visit WHERE patient_id = :id)` |
| `prescription` | `patient_id = :id` |
| `visit` | `patient_id = :id` |
| `patient` | `id = :id` |

Các row được set `is_deleted=TRUE`, `deleted_at=now()`, `deleted_by=admin_user_id`.

**audit_log KHÔNG soft-delete** — Đây là hành vi đúng theo thiết kế:
- Bảng `audit_log` có trigger DB-level `BEFORE UPDATE/DELETE RAISE EXCEPTION` (bất khả xâm phạm).
- BYT yêu cầu giữ audit log 7 năm (không được xóa).
- Row `patient.erasure` trong audit log tồn tại vĩnh viễn để chứng minh compliance.

---

## Audit Log — Bảo Tồn Theo BYT 7-Năm

Mỗi thao tác erasure ghi 1 audit event:

```json
{
  "action": "patient.erasure",
  "entity_type": "Patient",
  "entity_id": "<patient_id>",
  "new_data": {
    "patient_id": "<uuid>",
    "admin_user_id": "<uuid>",
    "reason": "<reason text>",
    "erased_at": "<iso timestamp>"
  }
}
```

**Không có PII** trong `new_data` — không có tên, số điện thoại, CCCD, địa chỉ.

Trigger DB `BEFORE UPDATE/DELETE RAISE EXCEPTION` trên `audit_log` đảm bảo không ai có thể xóa audit row sau khi ghi.

---

## PII Archive Cron (B.16)

**Schedule**: `cron(pii_archive, hour=4, minute=0)` — hàng ngày 04:00 UTC.

**Logic**:
```sql
SELECT id FROM patient
WHERE is_deleted = FALSE
  AND (
      last_accessed_at < :cutoff          -- đã truy cập nhưng đã qua 7 năm
      OR (last_accessed_at IS NULL AND created_at < :cutoff)  -- chưa bao giờ truy cập
  )
ORDER BY last_accessed_at NULLS FIRST
LIMIT 100;                                -- _BATCH_SIZE=100
```

`cutoff = now() - 7 năm (2555 ngày)`

**Per-patient mini-transaction**: Mỗi bệnh nhân xử lý trong transaction độc lập — lỗi 1 bệnh nhân không abort toàn batch.

**Race guard**: Re-fetch patient trong `db.begin()` để kiểm tra `is_deleted` + `last_accessed_at` lần nữa trước khi archive.

**Audit event** mỗi patient được archive:
```json
{
  "action": "patient.pii_archive",
  "entity_type": "Patient",
  "new_data": {
    "patient_id": "<uuid>",
    "reason": "retention_exceeded",
    "cutoff": "<iso timestamp>"
  }
}
```

**Kết quả trả về** (monitoring):
```json
{
  "archived": 5,
  "skipped": 0,
  "errors": 0,
  "cutoff": "2019-05-01T04:00:00+00:00",
  "run_at": "2026-05-01T04:00:00+00:00"
}
```

---

## last_accessed_at Cập Nhật Khi Đọc (Post-Fix)

**Fix post-review finding #1**: `audit_patient_read()` trong `patient_service.py` nay cập nhật `patient.last_accessed_at = datetime.now(UTC)` sau mỗi lần đọc.

```python
# patient_service.py — audit_patient_read()
patient = await session.get(Patient, patient_id)
if patient and not patient.is_deleted:
    patient.last_accessed_at = datetime.now(UTC)
    await session.flush([patient])
await session.commit()
```

**Tầm quan trọng**: Nếu không có fix này, cron sẽ fallback về `created_at` cho tất cả bệnh nhân — có thể archive những bệnh nhân đang active khi data đủ 7 năm tuổi.

---

## audit_actions Constants

**Fix post-review finding #3**: Thêm constants vào `app/core/audit_actions.py`:

```python
PATIENT_ERASURE = "patient.erasure"           # erasure_service.py
PATIENT_PII_ARCHIVE = "patient.pii_archive"   # pii_archive.py
```

Cả hai file dùng import từ constants thay vì hardcode string — ngăn string drift như bài học từ B.5-B.7.

---

## Crypto-Shred TODOs (Post-TASK-037 P2 Merge)

Sau khi TASK-037 Phase 2 merge, cần wire 4 bước:

**Bước 1**: `erasure_service.py` — sau audit write:
```python
from app.core.encryption import crypto_shred_tenant
await crypto_shred_tenant(patient.clinic_id)
```

**Bước 2**: `pii_archive.py` — sau soft-delete:
```python
from app.core.encryption import crypto_shred_tenant
await crypto_shred_tenant(patient.clinic_id)
```

**Bước 3**: Import path từ `clinic-cms-w3a` worktree (`feature/task-037-phase2-encryption`).

**Bước 4**: Thêm test assertion:
```python
mock_crypto_shred.assert_called_once_with(patient.clinic_id)
```

**Lý do thứ tự**: Audit phải commit trước DEK destruction — để audit row forensically retrievable ngay cả khi payload bị render unrecoverable.

Hiện tại (trước TASK-037 P2 merge): payload trong `patient_archive.payload` vẫn chứa plaintext PII. Sau khi DEK bị destroy, payload không thể recover được ngay cả khi DB row còn tồn tại.

---

## Test Coverage: 31/31 PASS

| File test | Số test | Mô tả |
|-----------|---------|-------|
| `tests/unit/test_erasure_service.py` | 14 | Token gen, valid erasure, bad/expired/wrong token, not found, admin-binding (2 mới), last_accessed_at update (1 mới) |
| `tests/integration/test_erasure_endpoint.py` | 9 | HTTP 200/403/422, service mock, permission guard |
| `tests/unit/test_pii_archive_cron.py` | 8 | Old patient archived, recent untouched, NULL+old created_at, already-deleted skip, summary counters |
| **Tổng** | **31** | **31/31 PASS** |

---

## Cross-Task Coordination

### TASK-037 P2 Crypto-Shred

- Wiring đơn giản: 1-line import + 1 call tại 2 site + 1 test assertion mỗi site.
- TODO comments với 4-step procedure đã được ghi trong cả 2 file.
- Không blocking test/doc phase — functional hoàn chỉnh không có crypto-shred.

### TASK-035 applied_role

- `write_audit("patient.erasure", ...)` sẽ tự động pick up `applied_role` từ middleware ContextVar khi TASK-035 merge.
- Không cần code change trong TASK-038 worktree.

### Migration Renumber Khi Merge

- Migration `0028_pii_archive_table` (`down_revision = "0021_multi_clinic_account"`) sẽ cần đổi số.
- Candidate: `0030_pii_archive_table` (sau TASK-037 P2 `0028` + TASK-035 `0029`).
- Cần orchestrator xác định vị trí final khi merge tất cả feature branches.

---

## Danh Sách File Được Tạo/Sửa

### File mới

- `app/modules/admin/services/erasure_service.py` — 2-step erasure logic
- `app/modules/patients/models/patient_archive.py` — PatientArchive ORM model
- `app/modules/patients/api/erasure_routes.py` — 2 endpoints
- `app/workers/jobs/pii_archive.py` — daily cron job
- `alembic/versions/0028_pii_archive_table.py` — schema migration
- `tests/unit/test_erasure_service.py` — 14 unit tests
- `tests/integration/test_erasure_endpoint.py` — 9 integration tests
- `tests/unit/test_pii_archive_cron.py` — 8 cron tests

### File sửa

- `app/core/audit_actions.py` — thêm `PATIENT_ERASURE`, `PATIENT_PII_ARCHIVE`
- `app/modules/patients/services/patient_service.py` — `audit_patient_read()` cập nhật `last_accessed_at`
- `app/modules/admin/services/erasure_service.py` — admin-binding check trong `_verify_and_consume_token()`, dùng `PATIENT_ERASURE` constant
- `app/workers/jobs/pii_archive.py` — dùng `PATIENT_PII_ARCHIVE` constant + `json.dumps()`
