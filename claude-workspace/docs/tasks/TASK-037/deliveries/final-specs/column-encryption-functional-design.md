---
id: column-encryption-phase2
type: functional-design
title: Column Encryption — Thiết kế chức năng (Phase 2)
status: DONE
completed: 2026-05-01
test_count: 50
all_pass: true
scope: Phase 2 (column encryption DEK/KEK + crypto-shred); Phase 1 (hash chain) DONE earlier
phase: 2
---

# Tiêu đề: Mã hóa Column Level — Thiết kế chức năng (Phase 2)

**TASK**: TASK-037 Phase 2  
**Ngày hoàn thành**: 2026-05-01  
**Trạng thái**: DONE  
**Số test**: 50/50 PASS  
**Chi nhánh**: `feature/task-037-phase2-encryption` (worktree `clinic-cms-w3a`)

---

## Mục đích

Thực thi NFR-024 (PII Column Encryption at Rest) + NFR-025 (Crypto-Shred) — mã hóa 19 cột PII ở mức cơ sở dữ liệu bằng cách sử dụng **per-tenant Data Encryption Keys (DEK)** được bảo vệ bởi **master Key Encryption Key (KEK)** trong Vault (production) hoặc `pgcrypto` (local-dev). Cung cấp thủ tục crypto-shred để vĩnh viễn xóa khóa khi thuê bao bị yêu cầu xóa dữ liệu.

---

## Phạm vi

### Mã hóa
- **19 cột PII được mã hóa**:
  - **Patient** (11 cột): `full_name`, `phone`, `email`, `id_number`, `address_line`, `ward`, `district`, `province`, `allergies`, `chronic_conditions`, `notes`
  - **User** (4 cột): `full_name`, `email`, `phone`, `license_number`
  - **Clinic** (4 cột): `tax_code`, `email`, `phone`, `address`

### Crypto-shred
- Xóa vĩnh viễn DEK của thuê bao → ciphertext không thể khôi phục
- Cascade soft-delete: clinic + users + patients
- Hai bước: phát hành token + xác nhận với HMAC

### Loại trừ
- **Audit-DEK**: YAGNI'd post-review fix — chiến lược redaction (`"***"` literals) được sử dụng thay thế
- **DEK rotation**: Deferred — column `key_version` + `rotated_at` tồn tại nhưng chức năng rotation không được triển khai
- **Backfill >1M hàng offline**: Tác vụ ops riêng biệt

---

## Kiến trúc

### Luồng khóa (Key Hierarchy)

```
┌─────────────────┐
│  KEK            │
│  (Master Key)   │
│  • Vault Transit│
│    (prod)       │
│  • pgcrypto     │
│    (local-dev)  │
└────────┬────────┘
         │ wraps
         ▼
┌─────────────────────────────────┐
│  tenant_key_metadata            │
│  ┌─────────────────────────────┐│
│  │ tenant_id: UUID             ││
│  │ dek_encrypted_by_kek: BYTEA ││  Data-DEK (AES-256 32 bytes)
│  │ key_version: INT            ││  wrapped by KEK
│  │ created_at: TIMESTAMPTZ     ││
│  │ rotated_at: TIMESTAMPTZ     ││
│  │ shredded_at: TIMESTAMPTZ    ││  NULL until crypto-shred
│  └─────────────────────────────┘│
└─────────────────────────────────┘
         │ unwrap
         ▼
┌─────────────────────────────────────┐
│  In-Process DEK Cache (LRU)         │
│  tenant_id → data_dek_plaintext     │
│  TTL: 5 phút, Max 100 entries       │
│  Policy: LRU eviction (not FIFO)    │
└─────────────────────────────────────┘
         │ decrypt PII
         ▼
┌──────────────────────────────────────┐
│  EncryptedString TypeDecorator       │
│  • process_bind_param()              │
│    - đọc current_clinic_id ContextVar│
│    - AES-256-GCM encrypt             │
│    - return BYTEA                    │
│  • process_result_value()            │
│    - đọc current_clinic_id ContextVar│
│    - AES-256-GCM decrypt             │
│    - return plaintext string         │
└──────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│  PII Columns (19 total)          │
│  Storage: BYTEA (ciphertext)     │
│  ORM type: EncryptedString       │
│  Plaintext returned to app layer │
└──────────────────────────────────┘
```

### Mô tả thành phần

| Thành phần | Vai trò | Triển khai |
|-----------|--------|-----------|
| **KEK (Key Encryption Key)** | Bảo vệ tất cả DEKs; nằm trong Vault hoặc env var | `kms_client.py` factory → `LocalDevKMSClient` hoặc `VaultKMSClient` |
| **Data-DEK** | Mã hóa 19 cột PII; per-tenant; random 32 bytes | `tenant_keys.mint_dek_for_tenant()` → lưu trữ wrapped trong `tenant_key_metadata.dek_encrypted_by_kek` |
| **LRU Cache** | Unwrap DEK từ DB; 5-min TTL; max 100 entries; `OrderedDict`-backed | `envelope._dek_cache` + `_get_cache()` / `_put_cache()` với `move_to_end()` LRU promote |
| **EncryptedString** | SQLAlchemy TypeDecorator; transparent encrypt/decrypt | `types.py` — `process_bind_param()` (encrypt) + `process_result_value()` (decrypt) |
| **with_tenant_context** | Context manager để set `current_clinic_id` ContextVar cho Arq workers | `app/core/tenancy.py` — sử dụng bởi `auto_no_show_appointments.py`, `appointment_reminder.py` |

---

## Schema

### Bảng `tenant_key_metadata`

```sql
CREATE TABLE tenant_key_metadata (
    tenant_id              UUID PRIMARY KEY REFERENCES clinic(id) ON DELETE CASCADE,
    dek_encrypted_by_kek   BYTEA NOT NULL,    -- Data-DEK wrapped by master KEK
    key_version            INTEGER NOT NULL DEFAULT 1,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    rotated_at             TIMESTAMPTZ,       -- NULL until first rotation
    shredded_at            TIMESTAMPTZ        -- NULL until crypto-shred; DEK blobs become zeros
);

CREATE INDEX ix_tenant_key_metadata_tenant_version 
    ON tenant_key_metadata (tenant_id, key_version);
```

**Không có audit-DEK column**: YAGNI post-review fix.

### 19 cột PII được thay đổi sang BYTEA

Tất cả các cột được chuyển đổi từ VARCHAR → BYTEA và được ánh xạ đến `EncryptedString`:

**Patient** (11 cột):
```python
full_name = Column(EncryptedString)
phone = Column(EncryptedString)
email = Column(EncryptedString)
id_number = Column(EncryptedString)
address_line = Column(EncryptedString)
ward = Column(EncryptedString)
district = Column(EncryptedString)
province = Column(EncryptedString)
allergies = Column(EncryptedString)
chronic_conditions = Column(EncryptedString)
notes = Column(EncryptedString)
```

**User** (4 cột):
```python
full_name = Column(EncryptedString)
email = Column(EncryptedString)
phone = Column(EncryptedString)
license_number = Column(EncryptedString)
```

**Clinic** (4 cột):
```python
tax_code = Column(EncryptedString)
email = Column(EncryptedString)
phone = Column(EncryptedString)
address = Column(EncryptedString)
```

---

## Migration `0025_column_encryption_envelope`

### Chuỗi revision
```
0021_multi_clinic_account (parent)
    ↓
0025_column_encryption_envelope (new)
```

### Các bước migration

1. **Tạo `tenant_key_metadata` + chỉ số**
   - Tạo bảng schema như trên
   - Tạo composite index trên `(tenant_id, key_version)`

2. **Mint DEKs cho tất cả các clinic hiện tại**
   - Lặp qua tất cả các hàng `clinic` hiện tại
   - Gọi `mint_dek_for_tenant(clinic_id)` → tạo random 32-byte DEK, wrap bằng KEK, INSERT vào `tenant_key_metadata`
   - Sử dụng `ON CONFLICT DO NOTHING` để idempotent

3. **Kiểm tra trước cấp độ hoạt động (pg_stat_activity)**
   - Query `pg_stat_activity` để kiểm tra xem có kết nối hoạt động nào khác ngoài chính quá trình migration không
   - Nếu tìm thấy, raise `RuntimeError` — yêu cầu cửa sổ bảo trì (không có lưu lượng ứng dụng)

4. **Drop GIN/trigram indexes** (không tương thích với BYTEA)
   - `DROP INDEX IF EXISTS gix_patient_name_trgm`
   - `DROP INDEX IF EXISTS gix_patient_phone_trgm`
   - `DROP INDEX IF EXISTS gix_patient_name_search`

5. **ALTER 19 cột sang BYTEA**
   - `ALTER TABLE patient ALTER COLUMN full_name TYPE BYTEA`
   - `ALTER TABLE patient ALTER COLUMN phone TYPE BYTEA`
   - (... cần lặp cho 11 + 4 + 4 = 19 cột)

6. **Re-encrypt dữ liệu hiện tại** (6 bảng: patient, user, clinic)
   - Cho mỗi hàng:
     ```python
     plaintext = row[col_name]  # đọc từ VARCHAR cũ (được decode cơ sở dữ liệu)
     dek_plain = _load_deks_sync()[row.clinic_id]  # unwrap DEK bằng KEK
     ciphertext = encrypt_pii(plaintext, dek_plain)
     UPDATE [table] SET [col] = ciphertext WHERE id = row.id
     ```
   - Batch: 1000 hàng mỗi lô để tránh khóa toàn bộ bảng
   - Guard double-encrypt: kiểm tra xem giá trị có phải là valid UTF-8 không → nếu không, bỏ qua (đã mã hóa trước đó)

**Lưu ý: `ENCODE(col, 'base64')` thay vì `CONVERT_FROM(col, 'UTF8')`**:
- asyncpg thực thi UTF-8 strict validation trên BYTEA values được ghi bởi ứng dụng đang chạy
- Base64 encoding tránh được vấn đề này bằng cách đọc chuỗi base64, sau đó Python `base64.b64decode()`

### Downgrade
- `NotImplementedError` — không có đường dẫn downgrade được triển khai
- Khôi phục từ backup trước migration

---

## KMS Providers

### LocalDevKMSClient
- **Khi nào sử dụng**: Phát triển cục bộ, CI, testing (default)
- **KEK**: `LOCAL_DEV_MASTER_KEY` environment variable (mặc định: 32 bytes 0x00)
- **Sơ đồ**: AES-256-GCM wrap DEK 32 bytes → IV(12) || ciphertext(32) || auth_tag(16) = 60 bytes
- **Sức khỏe**: Luôn bình thường (`.is_healthy()` → True)

### VaultKMSClient
- **Khi nào sử dụng**: Production — yêu cầu Vault đang chạy
- **KEK**: Vault Transit key `clinic-cms-master` (aes256-gcm96)
- **Endpoint**: `VAULT_ADDR` + `VAULT_TOKEN` (từ env)
- **Sức khỏe**: Gọi `/v1/sys/health` → 200 OK → bình thường; ngược lại unhealthy
- **Fail-fast**: Nếu `KMS_PROVIDER=vault` nhưng Vault không thể tiếp cận, `RuntimeError` được raise tại startup

### Factory: `get_kms_client()`
```python
def get_kms_client() -> KMSClient:
    if KMS_PROVIDER == "local-dev":
        return LocalDevKMSClient(LOCAL_DEV_MASTER_KEY)
    elif KMS_PROVIDER == "vault":
        return VaultKMSClient(VAULT_ADDR, VAULT_TOKEN, VAULT_TRANSIT_KEY_NAME)
    else:
        raise ValueError(f"Unknown KMS_PROVIDER: {KMS_PROVIDER}")
```

---

## EncryptedString TypeDecorator

### Tổng quan

`EncryptedString` là SQLAlchemy `TypeDecorator` tự động mã hóa/giải mã các giá trị PII khi chúng được liên kết hoặc trả về từ cơ sở dữ liệu.

```python
class EncryptedString(TypeDecorator):
    impl = LargeBinary  # cơ sở dữ liệu lưu trữ BYTEA
    cache_ok = True     # không có trạng thái dialect per-instance
```

### Dòng chảy process_bind_param() (Encrypt)
1. **Đầu vào**: `value` (plaintext str hoặc None)
2. **Nếu None**: trả về None (NULL được lưu giữ)
3. **Đọc ContextVar**: `current_clinic_id.get()` → clinic_id
4. **Nếu ContextVar không đặt**: raise `RuntimeError` (ngăn chặn silent bypass)
5. **Unwrap DEK**: `_load_deks_sync()[clinic_id]` → plaintext DEK
6. **Mã hóa**: `encrypt_pii(value, dek_plaintext)` → AES-256-GCM → BYTEA
7. **Trả về**: BYTEA ciphertext

### Dòng chảy process_result_value() (Decrypt)
1. **Đầu vào**: `value` (BYTEA từ asyncpg, hoặc memoryview, hoặc None)
2. **Nếu None**: trả về None
3. **Đọc ContextVar**: `current_clinic_id.get()` → clinic_id
4. **Nếu ContextVar không đặt**: raise `RuntimeError`
5. **Unwrap DEK**: `_load_deks_sync()[clinic_id]`
6. **Giải mã**: `decrypt_pii(bytes(value), dek_plaintext)` → plaintext str
7. **Trả về**: plaintext string cho lớp ứng dụng

### with_tenant_context() Helper

Để hỗ trợ Arq workers (không tự động set `current_clinic_id`):

```python
@contextmanager
def with_tenant_context(clinic_id: UUID, user_id: UUID | None = None):
    """
    Context manager để đặt current_clinic_id (và tùy chọn user_id).
    
    Sử dụng:
        with with_tenant_context(clinic_id=my_clinic_id):
            # EncryptedString.bind() sẽ hoạt động ở đây
            patient = session.query(Patient).get(id)
    """
    token_clinic = current_clinic_id.set(clinic_id)
    token_user = None
    if user_id is not None:
        token_user = current_user_id.set(user_id)
    try:
        yield
    finally:
        current_clinic_id.reset(token_clinic)
        if token_user is not None:
            current_user_id.reset(token_user)
```

**Áp dụng tại**:
- `app/workers/jobs/auto_no_show_appointments.py` (lặp clinic, cập nhật appointment)
- `app/workers/jobs/appointment_reminder.py` (lặp clinic, đọc appointment)
- `app/workers/jobs/password_rotation.py` (merge-time coordination, Wave 1-B)

---

## Quy trình Crypto-Shred

### Tổng quan hai bước
1. **Phát hành token**: `issue_crypto_shred_token(tenant_id)` → Redis token 10 phút TTL
2. **Xác nhận shred**: `crypto_shred_tenant(tenant_id, token, db)` → HMAC verify + xóa DEK

### Bước 1: `issue_crypto_shred_token(tenant_id: UUID) → str`

```python
# Generative random 32-byte token
shred_token = secrets.token_urlsafe(32)

# Store in Redis with TTL
redis_key = f"crypto_shred:{tenant_id}"
redis_client.setex(redis_key, 600, shred_token)  # 10 phút

return shred_token  # Return to calling service (API)
```

- **TTL**: 10 phút (user phải xác nhận nhanh chóng)
- **Trả về**: Token URL-safe để gửi qua API

### Bước 2: `crypto_shred_tenant(tenant_id: UUID, token: str, db: AsyncSession)`

```python
async def crypto_shred_tenant(tenant_id: UUID, token: str, db: AsyncSession):
    # 1. Xác thực token
    redis_key = f"crypto_shred:{tenant_id}"
    stored_token = redis_client.get(redis_key)
    if stored_token is None:
        raise ValueError("Token expired or not found")
    if not hmac.compare_digest(token, stored_token):
        raise PermissionError("Invalid token (HMAC mismatch)")
    
    # 2. Viết audit log "tenant.crypto_shred" (trước khi xóa DEK)
    # Raw SQL để tránh chicken-and-egg với encrypted audit fields
    await db.execute(
        text("""
        INSERT INTO audit_log (clinic_id, action, entity_type, entity_id)
        VALUES (:clinic_id, 'CRYPTO_SHRED', 'tenant', :tenant_id)
        """),
        {"clinic_id": tenant_id, "tenant_id": tenant_id}
    )
    
    # 3. Zero DEK blobs + set shredded_at
    await db.execute(
        text("""
        UPDATE tenant_key_metadata
        SET dek_encrypted_by_kek = :zeros,
            shredded_at = now()
        WHERE tenant_id = :tenant_id
            AND shredded_at IS NULL  -- Guard against double-shred
        """),
        {"tenant_id": tenant_id, "zeros": bytes(48)}  # 48 = 32 DEK + 16 padding
    )
    if db.get_affected_rows() == 0:
        raise PermissionError(f"Tenant {tenant_id} already shredded or not found")
    
    # 4. Evict từ LRU cache
    invalidate_tenant_cache(tenant_id)
    
    # 5. Cascade soft-delete
    await db.execute(
        text("UPDATE clinic SET deleted_at = now() WHERE id = :tenant_id"),
        {"tenant_id": tenant_id}
    )
    await db.execute(
        text("UPDATE user SET deleted_at = now() WHERE clinic_id = :tenant_id"),
        {"tenant_id": tenant_id}
    )
    await db.execute(
        text("UPDATE patient SET deleted_at = now() WHERE clinic_id = :tenant_id"),
        {"tenant_id": tenant_id}
    )
    
    # 6. Xóa token Redis (consumed once)
    redis_client.delete(redis_key)
    
    await db.commit()
```

### Hiệu ứng sau crypto-shred
- **DEK không thể khôi phục**: ciphertext BYTEA là permanent irrevocable (kếtquả toán học — không có key)
- **Clinic + Users + Patients soft-deleted** (`deleted_at IS NOT NULL`)
- **Cache invalidated**: Bất kỳ lần đọc/ghi nào từ worker sẽ miss cache; DEK load từ DB sẽ fail (hàng không tồn tại hoặc `shredded_at IS NOT NULL` check)
- **Audit trail immutable** (Phase 1 hash chain): "tenant.crypto_shred" event được ghi trước khi xóa DEK; không thể xóa từ audit_log (chain breaks)

---

## Endpoint Sức khỏe

### GET /health/kms

```
Request:
  GET /health/kms

Response (200 OK):
{
  "status": "ok",
  "provider": "local-dev"
}

Response (503 Service Unavailable):
{
  "status": "unhealthy",
  "provider": "vault",
  "error": "Failed to reach Vault at https://vault.internal:8200"
}
```

**Triển khai**: `app/main.py` → gọi `get_kms_client().is_healthy()`

---

## Tương tác giữa Hash Chain (Phase 1) và Mã hóa (Phase 2)

### Chiến lược tái đắc: Redaction to `"***"` Literals

**Yếu tố quan trọng**: PII được **loại trừ khỏi audit_log** nhằm trách các field được mã hóa được lưu trữ trong `old_data`/`new_data`.

**Triển khai**:
1. Model Patient + User có `__audit_exclude__` attribute:
   ```python
   class Patient(Base):
       __auditable__ = True
       __audit_exclude__ = [
           "full_name", "phone", "email", "id_number",
           "address_line", "ward", "district", "province",
           "allergies", "chronic_conditions", "notes"
       ]
   ```

2. Audit listener (`app/core/audit.py`) — `_redact()` helper:
   ```python
   def _redact(key: str, model_class) -> str:
       if key in getattr(model_class, '__audit_exclude__', []):
           return "***"
       return original_value
   ```

3. Kết quả `audit_log.old_data` / `audit_log.new_data` là JSONB chứa literals `"***"`:
   ```json
   {
     "id": "3fa85f64-...",
     "full_name": "***",
     "phone": "***",
     "email": "***",
     "created_at": "2026-05-01T..."
   }
   ```

4. **Hash chain (Phase 1) tính toán trên JSON redacted-plaintext này** → hash không thay đổi
5. **Verifier không cần decrypt bất kỳ cái gì** — PII được redacted ở thời điểm ghi, không bao giờ lưu trữ trong audit_log ciphertext

**Tại sao này tốt hơn Audit-DEK plumbing?**
- Đơn giản: 1 DEK thay vì 2
- Rõ ràng: redaction xảy ra ở lớp audit, không phải crypto
- YAGNI: không có mã giải mã audit cần thiết cho compliance reads

---

## Bảng Coverage: 19 cột PII Được Mã hóa

| Bảng | Cột | Loại | Nhạy cảm |
|------|------|------|----------|
| patient | full_name | EncryptedString | Tier-2 PII (định danh chủ yếu) |
| patient | phone | EncryptedString | Tier-2 PII |
| patient | email | EncryptedString | Tier-2 PII |
| patient | id_number | EncryptedString | Tier-3 PII (định danh quốc gia) |
| patient | address_line | EncryptedString | Tier-2 PII |
| patient | ward | EncryptedString | Tier-2 PII (Nghị định 13) |
| patient | district | EncryptedString | Tier-2 PII (Nghị định 13) |
| patient | province | EncryptedString | Tier-2 PII (Nghị định 13) |
| patient | allergies | EncryptedString | Tier-3 PHI (y tế) |
| patient | chronic_conditions | EncryptedString | Tier-3 PHI (y tế) |
| patient | notes | EncryptedString | Tier-3 PHI (lâm sàng) |
| user | full_name | EncryptedString | Tier-2 PII |
| user | email | EncryptedString | Tier-2 PII |
| user | phone | EncryptedString | Tier-2 PII |
| user | license_number | EncryptedString | Tier-3 PII (chuyên môn) |
| clinic | tax_code | EncryptedString | Tier-3 PII (định danh tổ chức — Nghị định 13) |
| clinic | email | EncryptedString | Tier-2 PII |
| clinic | phone | EncryptedString | Tier-2 PII |
| clinic | address | EncryptedString | Tier-2 PII |

**Tổng cộng: 19 cột**

**Xác minh**: `TestPIIColumnCoverageStatic.test_total_encrypted_pii_column_count` khẳng định 19

---

## Coverage Kiểm tra

### Kiểm tra đơn vị (15 + 13 + 2 + 4 = 34 cái)

| Test | Tệp | Chi tiết |
|------|-----|---------|
| `TestEncryptRoundTrip` | `test_crypto_envelope.py` | Encrypt → decrypt → plaintext khớp |
| `TestAuditDekAbsent` | `test_crypto_envelope.py` | Confirm audit-DEK plumbing removed (YAGNI fix) |
| `TestDekCache.test_get_cache_on_miss_loads_from_db` | `test_crypto_envelope.py` | Cache miss → _load_deks_sync() → hit |
| `TestDekCache.test_cache_respects_ttl` | `test_crypto_envelope.py` | Entry hết hạn sau 5 phút |
| `TestDekCache.test_lru_promotes_on_hit` | `test_crypto_envelope.py` | Access promote entry (LRU, không FIFO) |
| `TestDekCache.test_lru_evicts_least_recently_used` | `test_crypto_envelope.py` | Eviction removes least recent entry |
| `TestEncryptedStringContextGuard.test_raises_without_context_on_bind` | `test_crypto_envelope.py` | bind() raises RuntimeError nếu ContextVar unset |
| `TestEncryptedStringContextGuard.test_raises_without_context_on_result` | `test_crypto_envelope.py` | result() raises RuntimeError nếu ContextVar unset |
| `TestWithTenantContext.test_sets_and_resets_clinic_id` | `test_crypto_envelope.py` | Context manager sets + resets clinic_id |
| `TestWithTenantContext.test_sets_and_resets_user_id` | `test_crypto_envelope.py` | user_id cũng được set/reset |
| `TestWithTenantContext.test_resets_on_exception` | `test_crypto_envelope.py` | ContextVar reset ngay cả trên lỗi |
| `TestWithTenantContext.test_encrypted_string_works_inside_context` | `test_crypto_envelope.py` | EncryptedString bind works inside context |
| `TestLocalDevKMSClient.*` (13 cái) | `test_kms_client.py` | LocalDev encrypt/decrypt round-trip, IV randomness, isolation, Vault protocol shape, factory |

### Kiểm tra tích hợp (7 + 9 = 16 cái)

| Test | Tệp | Chi tiết |
|------|-----|---------|
| `TestPatientPIIEncryptedAtRest.test_patient_full_name_is_bytea_on_disk` | `test_pii_encrypted_at_rest.py` | Disk storage is BYTEA not readable text |
| `TestPatientPIIEncryptedAtRest.test_patient_null_pii_remains_null` | `test_pii_encrypted_at_rest.py` | NULL → NULL preserved |
| `TestEncryptedStringOrmRoundTrip.test_orm_read_returns_plaintext` | `test_pii_encrypted_at_rest.py` | ORM returns plaintext despite disk BYTEA |
| `TestPIIColumnCoverageStatic.test_patient_pii_columns_encrypted` | `test_pii_encrypted_at_rest.py` | Patient 11 columns mapped to EncryptedString |
| `TestPIIColumnCoverageStatic.test_user_pii_columns_encrypted` | `test_pii_encrypted_at_rest.py` | User 4 columns |
| `TestPIIColumnCoverageStatic.test_clinic_pii_columns_encrypted` | `test_pii_encrypted_at_rest.py` | Clinic 4 columns |
| `TestPIIColumnCoverageStatic.test_total_encrypted_pii_column_count` | `test_pii_encrypted_at_rest.py` | assert 19 total |
| `TestCryptoShred.*` (9 cái) | `test_crypto_shred.py` | Shred marks shredded_at, zeros DEK, evicts cache, cascade soft-delete, double-shred guard, lookup miss, clinic/users/patients cascade |

**Tổng: 50/50 PASS**

---

## Tác vụ điều phối hợp tại thời điểm merge

### CRITICAL: Wave 2-E (TASK-034 / BHYT)

**Khi nào**: TASK-034 merge sau TASK-037

**Vấn đề**: `clinic` model được sửa đổi trong cả hai branch:
- TASK-037 thêm `tax_code`, `email`, `phone`, `address` → EncryptedString
- TASK-034 thêm `bhyt_enabled`, `bhyt_facility_code`

**Hành động**:
1. **Rebase TASK-034 lên nhánh này** (TASK-037 Phase 2)
2. **`bhyt_facility_code` PHẢI là EncryptedString**
   - Nghị định 13 Tier-3 PII (định danh cơ sở y tế — nhạy cảm như `tax_code`)
   - Thêm vào `clinic.py` model: `bhyt_facility_code = Column(EncryptedString)`
3. **`bhyt_enabled` remains plaintext** (boolean flag, không PII)
4. **Tạo migration `0028_bhyt_facility_code_encrypted` tại thời điểm merge**:
   ```python
   def upgrade():
       op.alter_column('clinic', 'bhyt_facility_code', type_=BYTEA)
       # Re-encrypt existing non-null values (if any)
       ...
   ```
5. **Xác minh**: `SELECT bhyt_facility_code FROM clinic LIMIT 1` trả về BYTEA trên psql; ORM trả về plaintext

### HIGH: Wave 1-B (password_rotation.py / Arq job)

**Khi nào**: TASK-038 password rotation merges (Wave 1-B)

**Vấn đề**: `password_rotation.py` cập nhật cột `user` (có `email`, `phone`, `full_name` mã hóa)

**File**: `app/workers/jobs/password_rotation.py` (chưa có trong worktree này)

**Hành động tại merge**:
```python
# TRƯỚC (không hoạt động):
for clinic_id in active_clinics:
    users = session.query(User).filter_by(clinic_id=clinic_id).all()
    # EncryptedString bind fail — ContextVar không đặt

# AFTER (với fix):
from app.core.tenancy import with_tenant_context

for clinic_id in active_clinics:
    with with_tenant_context(clinic_id):
        users = session.query(User).filter_by(clinic_id=clinic_id).all()
        # EncryptedString bind OK
        for user in users:
            user.password_last_changed = now()
        session.commit()
```

**Owner**: Wave 1-B implementer hoặc orchestrator

### MEDIUM: Wave 2-D (SOAP / Diagnosis Notes / TASK-037-Phase2b)

**Khi nào**: Trước khi TASK-042 (EMR) bắt đầu

**Phát hiện**: `visit_soap.{subjective, objective, assessment, plan}` và `visit_diagnosis.notes` là **PHI rõ ràng** (ghi chép y tế lâm sàng)

**Hành động**:
1. **Mở follow-up task**: `TASK-037-Phase2b-SOAP-Encryption`
2. **Inventory**: Thêm 5 cột SOAP vào bảng coverage TASK-037-Phase2b
3. **Timeline**: Hành động trước khi TASK-042 bắt đầu triển khai

**Owner**: Manager / orchestrator

---

## Search Post-Encryption (Wave 3-C follow-up)

### Vấn đề

Sau khi TASK-037 P2 mã hóa `full_name`, `phone`, `id_number` thành BYTEA:
- GIN trigram indexes (`gix_patient_name_trgm`, `gix_patient_phone_trgm`, `gix_patient_name_search`) bị drop trong migration `0031_column_encryption_envelope`.
- DB-side `similarity()`, `ILIKE`, `plainto_tsquery()` trên BYTEA columns → không khả thi.
- TASK-036 Cmd+K search bị broken với các columns này (xem `search_service.py` post-merge TODOs).

### Chiến lược được áp dụng: App-layer decrypt-then-filter

**Triển khai** (commit trên `main` sau T3 final merge):

```python
# Bước 1: Load lên đến MAX_CANDIDATES (500) patients gần nhất theo clinic_id
stmt = select(Patient).where(
    Patient.clinic_id == clinic_id,
    Patient.is_deleted.is_(False),
).order_by(Patient.created_at.desc()).limit(MAX_CANDIDATES)

# Bước 2: ORM auto-decrypt via EncryptedString TypeDecorator
# (current_clinic_id ContextVar đã set bởi TenancyMiddleware)
candidates = (await session.execute(stmt)).scalars().all()

# Bước 3: Python-side substring match với Vietnamese normalization
def _normalize_vi(s: str) -> str:
    """Lowercase + strip diacritics (unaccent) via unicodedata."""
    nfd = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

for p in candidates:
    if q_norm in _normalize_vi(p.full_name or ""):
        matches.append(p)
```

**Phạm vi thay đổi**:
- `app/modules/patients/services/patient_service.py` — thêm `_normalize_vi()` helper + rewrite `search_patients()` với decrypt-then-filter
- `app/modules/search/services/search_service.py` — `_search_patients()` dùng candidate scan 200 rows (palette UX)
- `app/modules/patients/api/routes.py` — mở rộng `type` param pattern: `phone|name|code|id_number|all`
- `tests/unit/test_patient_decrypt_filter.py` — 18 unit tests
- `tests/integration/test_patient_search_endpoint.py` — 7 integration tests

### Hiệu năng

| Điều kiện | Thời gian ước tính |
|-----------|-------------------|
| 200 candidates × decrypt (warm DEK cache) | ~2–10 ms |
| 500 candidates × decrypt (warm DEK cache) | ~5–50 ms |
| DEK cache miss (cold start) | +10–50 ms lần đầu |

Benchmark thực tế phụ thuộc vào CPU và network latency đến DB container.
Target: 500 rows < 500 ms (acceptable cho non-palette search).

**search_type modes**:
- `name`: Vietnamese unaccent + lowercase substring match trên `full_name`
- `phone`: exact substring trên `phone`
- `id_number`: exact substring trên `id_number`
- `code`: DB-side exact match trên `patient_code` (plaintext — no candidate scan)
- `all`: union across name + phone + id_number + code

### Tối ưu tương lai (v2)

**HMAC searchable side columns** (blind-index pattern):
```
patient.full_name_search_token  VARCHAR   -- HMAC(normalize_vi(full_name), tenant_search_key)
```
- Deterministic: `HMAC(q_norm, key) = stored_token` → exact match có thể dùng DB index
- Prefix-safe: hash first N chars → prefix search
- Requires: per-tenant `search_key` (separate from DEK), migration backfill, index rebuild
- Estimate: 1–2 sprint effort; recommended khi clinic size > 10 K patients

---

## Quyết định hoãn lại

| Quyết định | Lý do |
|----------|-------|
| **DEK rotation** | Column `key_version` + `rotated_at` tồn tại nhưng không có hàm rotation. NIST 800-57 yêu cầu rotation AES-256 trong 5 năm. Follow-up task riêng biệt với deadline cứng. |
| **>1M hàng backfill offline** | Migration hiện tại batch 1000 với `LIMIT/OFFSET`. Cho dữ liệu lớn (>1M hàng), off-peak script riêng biệt được khuyến nghị. Tác vụ ops riêng biệt. |
| **Performance baseline** | Benchmark patient-list endpoint p95 (trước/sau) được khuyến nghị. Test agent chạy tại testing phase. |
| **HMAC blind-index search** | App-layer decrypt-then-filter (MAX_CANDIDATES=500) đủ cho clinic <10K patients. HMAC side columns deferred v2. |

---

## Tệp được sửa đổi / Tệp mới

### Sửa đổi (6)
- `app/core/config.py` — Thêm cài đặt KMS
- `app/main.py` — Endpoint `/health/kms`
- `app/modules/patients/models/patient.py` — 11 cột EncryptedString
- `app/modules/users/models/user.py` — 4 cột EncryptedString
- `app/modules/users/models/clinic.py` — 4 cột EncryptedString
- `pyproject.toml` — Dep `psycopg2-binary`

### Mới (7)
- `alembic/versions/0025_column_encryption_envelope.py` — Migration
- `app/core/crypto/__init__.py` — Public API
- `app/core/crypto/kms_client.py` — KMS providers
- `app/core/crypto/envelope.py` — AES-256-GCM + LRU cache
- `app/core/crypto/types.py` — EncryptedString TypeDecorator
- `app/core/crypto/tenant_keys.py` — Mint DEK + crypto-shred
- `app/core/tenancy.py` — with_tenant_context helper
- `app/modules/admin/services/erasure_service.py` — Token issue + shred confirm

### Kiểm tra (8 tệp mới)
- `tests/unit/test_crypto_envelope.py` — 21 unit tests
- `tests/unit/test_kms_client.py` — 13 unit tests
- `tests/integration/test_pii_encrypted_at_rest.py` — 7 integration tests
- `tests/integration/test_crypto_shred.py` — 9 integration tests

---

## Trạng thái kiểm tra cuối cùng

**Ngày**: 2026-05-01  
**Docker**: `clinic-cms-w3a` container  
**Lệnh**:
```bash
python -m pytest \
  tests/unit/test_crypto_envelope.py \
  tests/unit/test_kms_client.py \
  tests/integration/test_pii_encrypted_at_rest.py \
  tests/integration/test_crypto_shred.py \
  -v --tb=short
```

**Kết quả**:
```
============================== 50 passed in 0.87s ==============================
```

**Phân tích**:
- ✅ 21 envelope tests (15 crypto + 8 context + 2 LRU) PASS
- ✅ 13 KMS client tests (LocalDev + Vault protocol + factory) PASS
- ✅ 7 at-rest integration tests (BYTEA storage + NULL + ORM round-trip + column count) PASS
- ✅ 9 crypto-shred tests (shred + zeros + cache evict + cascade + double-guard) PASS

---

## Kết luận

TASK-037 Phase 1 + Phase 2 đã hoàn thành:

- **Phase 1 (Hash Chain)**: 20 tests PASS — chuỗi hash kiểm tra được bảo vệ chống giả mạo cơ sở dữ liệu
- **Phase 2 (Column Encryption)**: 50 tests PASS — 19 cột PII mã hóa per-tenant DEK + crypto-shred

**Triển khai**:
- AES-256-GCM với IV ngẫu nhiên 12 byte + auth tag 16 byte
- Per-tenant DEK (32 byte) wrapped bằng KEK trong Vault (prod) / pgcrypto (dev)
- LRU cache (5-min TTL, 100 entry max, OrderedDict-backed)
- EncryptedString TypeDecorator transparent encrypt/decrypt
- with_tenant_context() helper cho Arq workers
- Crypto-shred hai bước (token 10-min TTL + HMAC confirm) → DEK zeros → cascade soft-delete
- Redaction audit `"***"` (không audit-DEK plumbing)

**Tác vụ điều phối hợp tại merge**:
1. **Wave 2-E**: bhyt_facility_code → EncryptedString (Tier-3 PII)
2. **Wave 1-B**: password_rotation.py → with_tenant_context wrapper
3. **Wave 2-D**: Mở TASK-037-Phase2b cho SOAP encryption
4. **Wave 3-C**: Thiết kế lại chiến lược search (GIN index dropped)
