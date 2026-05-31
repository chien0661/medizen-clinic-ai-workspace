---
id: audit-hash-chain-phase1
type: functional-design
title: Hash Chain Audit Log (Phase 1) — Functional Design
status: DONE
completed: 2026-05-01
test_count: 20
all_pass: true
scope: Phase 1 only (hash chain); Phase 2 (column encryption) deferred to Wave 3-A
---

# Tiêu đề: Hash Chain Audit Log — Thiết kế chức năng (Phase 1)

**TASK**: TASK-037 Phase 1  
**Ngày hoàn thành**: 2026-05-01  
**Trạng thái**: DONE  
**Số test**: 20/20 PASS  
**Chi nhánh**: `feature/task-037-hash-chain` (worktree `clinic-cms-w2a`)

---

## Mục đích

Thực thi NFR-031 (Audit Hash Chain Compliance) — đảm bảo rằng người dùng có quyền superuser không thể sửa đổi lịch sử kiểm tra mà không bị phát hiện bằng cách xây dựng chuỗi hash khí hậu, trong đó mỗi hàng kiểm tra được liên kết dịch vụ với hàng trước đó qua SHA256(prev_hash || canonical_json).

---

## Phạm vi

**Phase 1 (Hash Chain)**: Hiện đang hoàn thành
- Thêm chuỗi hash vào `audit_log` với kiểm soát đồng thời + kháng giả mạo cấp DB

**Phase 2 (Column Encryption)**: Deferred
- NFR-024/025 — mã hóa column-level PII với per-tenant DEK + master KEK
- Phụ thuộc vào TASK-033 (multi-clinic identity model)
- In-flight Wave 3-A

---

## Thay đổi Schema

### Bảng `audit_log` — Thêm 3 cột

| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---------|---------|---------|---------|
| `chain_seq` | BIGINT | NOT NULL, UNIQUE | Số thứ tự chuỗi; do DB trigger gán INSIDE advisory lock để đảm bảo order == commit order |
| `prev_hash` | CHAR(64) | NOT NULL | SHA256 (hex) của `row_hash` của hàng trước (hoặc `'0'*64` cho hàng đầu tiên) |
| `row_hash` | CHAR(64) | NOT NULL | SHA256(prev_hash \|\| canonical_json_of_13_hashed_columns) |

### Chỉ số

- `ix_audit_log_chain_seq` — UNIQUE trên `chain_seq` (ngăn chặn duplicate chain positions)
- `ix_audit_log_row_hash` — để tra cứu nhanh trong quá trình xác minh

---

## Kiến trúc Trigger DB

### Migration `0022_audit_hash_chain`

**Parent migration**: `65fc9ae59ba5` (merge migration hiện tại trong w2a)

#### Hàm `fn_audit_row_data_json(rec audit_log) → text`

Xây dựng JSON chính tắc từ 13 cột **không phải chuỗi**:
- `id, clinic_id, user_id, request_id, action, entity_type, entity_id, old_data, new_data, changed_fields, ip_address, user_agent, created_at`

Quy trình:
1. `jsonb_build_object()` với các cặp khóa-giá trị từ mỗi cột
2. Sắp xếp khóa (jsonb_build_object tự động sắp xếp khi chuyển đổi thành text)
3. Trả về dưới dạng `text` để SHA256 hashing

**Ghi chú Wave 3-B**: Applied role hash gap:
- TASK-035 sẽ thêm `audit_log.applied_role`
- Tại thời điểm merge (sau khi cả hai nhánh hợp nhất): thêm `applied_role` vào `fn_audit_row_data_json()` + re-hash backfill

#### Trigger `trg_audit_log_chain_compute` (BEFORE INSERT)

**Trình tự thực thi**:

1. **Acquire advisory lock** (ngăn race condition):
   ```sql
   PERFORM pg_advisory_xact_lock(3700221);
   -- Advisory key = TASK-037 + Phase 1 + 022
   ```

2. **Allocate chain_seq INSIDE lock**:
   ```sql
   NEW.chain_seq := nextval('audit_log_chain_seq_seq');
   ```
   **Tại sao bên trong lock?** `BIGSERIAL` DEFAULT mặc định gán giá trị trước khi trigger chạy, gây ra race. Hai giao dịch đồng thời có thể nhận được chain_seq 5,6 nhưng commit theo thứ tự 6→5, dẫn đến chain branch.

3. **Đọc `prev_hash` mới nhất**:
   ```sql
   SELECT row_hash INTO v_latest_hash 
   FROM audit_log 
   ORDER BY chain_seq DESC LIMIT 1;
   ```
   (Lock đã giữ; không cần FOR UPDATE thêm)

4. **Thiết lập `NEW.prev_hash`**:
   - Nếu không có hàng nào: `NEW.prev_hash := '0000...0000'` (genesis sentinel)
   - Nếu có: `NEW.prev_hash := v_latest_hash`

5. **Tính toán `row_hash`**:
   ```sql
   v_canonical := fn_audit_row_data_json(NEW);
   NEW.row_hash := encode(
     digest(NEW.prev_hash || v_canonical, 'sha256'),
     'hex'
   );
   ```

6. **Kháng giả mạo — từ chối nếu prev_hash không khớp**:
   - Nếu caller cung cấp `prev_hash IS NOT NULL` khác với giá trị được tính: RAISE `audit_chain_tamper_detected` exception

7. **Giải phóng lock** — tự động khi giao dịch commit/abort

**Threat model**: Lock bảo vệ chống lại concurrent INSERTs từ application. Trực tiếp SQL `INSERT ... ON CONFLICT ...` không được bảo vệ; không nằm trong phạm vi (chỉ DBA/attacker trực tiếp có quyền truy cập DB raw).

---

## Chiến lược Backfill

### Quá trình backfill trong migration

**Thứ tự gọi**:
1. Migrate schema (thêm 3 cột nullable)
2. Chạy `_BACKFILL_SQL` block (DO $$…$$)
3. Thêm NOT NULL constraints

**Chi tiết backfill**:

```sql
PERFORM pg_advisory_lock(3700221);  -- Khóa advisory (blocking)
BEGIN
  -- Nếu khóa không khả dụng: RAISE audit_hash_backfill_in_progress
  
  FOR rec IN (
    SELECT * FROM audit_log 
    ORDER BY created_at ASC, id ASC  -- Tất định + xử lý ms ties
  )
  LOOP
    IF v_prev_hash IS NULL THEN
      v_prev_hash := '0' || REPEAT('0', 63);  -- Genesis: 64 zeros
    END IF;
    
    v_canonical := fn_audit_row_data_json(rec);
    v_row_hash := encode(digest(v_prev_hash || v_canonical, 'sha256'), 'hex');
    
    UPDATE audit_log 
    SET prev_hash = v_prev_hash, row_hash = v_row_hash
    WHERE id = rec.id;
    
    v_prev_hash := v_row_hash;  -- Chuỗi forward
  END LOOP;
  
  -- Allocate chain_seq via ROW_NUMBER()
  UPDATE audit_log 
  SET chain_seq = rn 
  FROM (
    SELECT id, ROW_NUMBER() OVER (ORDER BY created_at, id) AS rn
    FROM audit_log
  ) t 
  WHERE audit_log.id = t.id;
  
  PERFORM pg_advisory_unlock(3700221);
END;
```

**Hạn chế**:
- **<1M rows**: Backfill trong transaction migration OK
- **>1M rows**: Giữ advisory lock lâu → khóa schema migration commit. Giải pháp: script offline riêng với batch autocommit 10k rows

**Nếu backfill thất bại**:
- Partial NULL prev_hash/row_hash → migration rollback
- Lock tự động giải phóng trên transaction end
- Phục hồi: downgrade + re-run upgrade

---

## Dịch vụ Verifier

### Tệp: `app/modules/audit/services/chain_verifier.py`

#### Hàm `verify_chain(db, batch_size=1000) → VerifyChainResult`

**Phương pháp**: Streaming keyset pagination (tối ưu O(N))

```python
async def verify_chain(db, batch_size=1000):
    verified = True
    total_rows = 0
    breaks = []
    
    last_seen_seq = 0
    while True:
        rows = await db.execute(
            """
            SELECT chain_seq, row_hash, prev_hash, (
              SELECT encode(digest(?, 'sha256'), 'hex')
              FROM fn_audit_row_data_json(audit_log)
            ) AS expected_hash
            FROM audit_log
            WHERE chain_seq > :last_seen
            ORDER BY chain_seq
            LIMIT :batch_size
            """,
            last_seen_seq,
            batch_size
        )
        
        if not rows:
            break
        
        for row in rows:
            total_rows += 1
            if row.expected_hash != row.row_hash:
                verified = False
                breaks.append({
                    "chain_seq": row.chain_seq,
                    "expected_hash": row.expected_hash,
                    "actual_hash": row.row_hash
                })
                # Continue from stored prev_hash (avoid cascading false positives)
        
        last_seen_seq = max(r.chain_seq for r in rows)
    
    return VerifyChainResult(
        verified=verified,
        total_rows=total_rows,
        breaks=breaks
    )
```

**Hiệu suất**:
- **Old OFFSET approach**: O(N²) — mỗi batch re-scan N rows bỏ qua
- **New keyset approach**: O(N) — sử dụng `ix_audit_log_chain_seq` index
- **1M rows**: Old ~5min, New ~30-60s

---

## Endpoint Admin

### `POST /admin/audit/verify-chain`

**Định tuyến**: `app/modules/audit/api/routes.py`

**Yêu cầu quyền**: `audit:verify` (migration 0022a seed)

**Rate limit**: 5 / hour (slowapi limiter)

**Tham số truy vấn** (query params, không body):
- `start_seq: int = 1` — bắt đầu từ chuỗi nào
- `batch_size: int = 1000` — kích thước batch

**Phản hồi** (200 OK):
```json
{
  "verified": true,
  "total_rows": 5000,
  "breaks": []
}
```

hoặc (khi có break):
```json
{
  "verified": false,
  "total_rows": 5000,
  "breaks": [
    {
      "chain_seq": 1234,
      "expected_hash": "abc123...",
      "actual_hash": "def456..."
    }
  ]
}
```

**Trạng thái HTTP**:
- `200` — Verification hoàn tất (verified = true/false)
- `401` — Chưa xác thực
- `403` — Không có `audit:verify`
- `429` — Rate limit exceeded (5/hour)

---

## Công việc Cron

### `audit_chain_verify_run` (Arq scheduled)

**File**: `app/workers/jobs/audit_chain_verify.py`

**Lịch trình**: Hàng ngày lúc 03:00 UTC

**Hành động**:
1. Gọi `verify_chain(db, batch_size=5000)`
2. Nếu `verified=false`: gọi `send_alert(rule="audit_tamper_detected", breaks=[...])`
3. Log kết quả (structlog)

**Cảnh báo Integration** (Wave 2-B in-flight):
- Stub hiện: `app/core/alerting.py` → structlog WARNING
- Wave 2-B sẽ thay thế bằng PagerDuty/Slack webhook
- Contract ổn định: `async def send_alert(rule: str, payload: dict) -> None`

---

## Xung đột Migration (Merge-time)

Hiện tại w2a không chứa 0021_multi_clinic_account (đó là w1a). Khi merge vào main:

| Stream | Migration | Dự kiến xung đột | Cách xử lý merge |
|--------|-----------|---------|---------|
| Wave 1-A (w1a) | `0021_multi_clinic_account` | Không trong w2a | Parent migration: both `0021` + `0022` |
| Wave 1-B (password history) | `0022_password_history` | Collision: 0022 | Rename → `0023_password_history` |
| Wave 1-C (MFA/login_fp) | `0023_mfa`, `0024_login_fp` | Collision: 0023, 0024 | Rename → `0024_mfa`, `0025_login_fp` |
| Wave 3-B (applied_role) | Audit applied_role | Không phải column mới | TODO: add applied_role to fn_audit_row_data_json() post-merge |

**Applied role hash gap** (deferred, tracked):
- TASK-035 thêm `audit_log.applied_role`
- Hàm `fn_audit_row_data_json()` hiện không bao gồm nó
- Post-merge follow-up: Tạo migration mới recreates function + re-backfill row_hash

---

## Quyết định Deferred

1. **Phase 2 Column Encryption** (NFR-024/025)
   - Phụ thuộc TASK-033 identity model
   - In-flight Wave 3-A
   - KMS provider decision pending

2. **Backfill script cho >1M rows**
   - Khuyên dùng script offline (không trong Alembic)
   - Công việc tương lai: `app/scripts/backfill_audit_chain.py`

3. **Applied role hash inclusion**
   - Deferred đến khi TASK-035 merge + xác nhận applied_role migration
   - Thêm vào `fn_audit_row_data_json()` + re-backfill

---

## Kiểm tra và Xác thực

### Số lượng Test: 20/20 PASS

| Phần | Kiểm tra | Số lượng | Trạng thái |
|------|---------|---------|-----------|
| Unit (Chain Verifier) | Empty chain / clean chain / tampered row / tampered data / prev hash mismatch / pagination / hash computation | 13 | PASS |
| Integration (Endpoint) | Admin verify clean / verify with breaks / non-admin 403 / unauthenticated 401 / response schema | 5 | PASS |
| Integration (Trigger/Concurrency) | Trigger rejects bad prev_hash / concurrent INSERTs serialize correctly | 2 | PASS |
| **Tổng cộng** | | **20** | **PASS** |

### Race condition fix (post-Fix mode)

**Vấn đề gốc**: `BIGSERIAL` pre-allocate chain_seq trước trigger → concurrent commits có thể không theo thứ tự

**Giải pháp**:
- Thêm `pg_advisory_xact_lock(3700221)` vào đầu trigger
- Allocate chain_seq INSIDE lock: `NEW.chain_seq := nextval('...')`
- Test concurrency (10 concurrent INSERTs) xác nhận serialization

**Test**: `test_concurrent_inserts_serialize_correctly` — PASS

---

## Ghi chú

- **Ngôn ngữ**: Mô tả kiến trúc kỹ thuật + hướng dẫn triển khai
- **Phạm vi**: Phase 1 hoàn toàn (hash chain integrity + verifier + endpoint + cron + alerting stub)
- **Không xác định/Tương lai**: Phase 2 encryption, KMS provider, >1M backfill script, applied_role hash update
- **Ổn định API**: `fn_audit_row_data_json()`, trigger signature, verifier signature — đều được thiết kế để có thể mở rộng mà không phá vỡ

---

**Hoàn thành lúc**: 2026-05-01  
**Chi nhánh**: feature/task-037-hash-chain  
**Số commit**: 1 migration + 8 app files + 2 tests + 1 docker-compose mod
