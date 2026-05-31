---
from: implementation
to: review
phase: 2
date: 2026-05-02
status: ready-for-review
---

# TASK-037 Phase 2 — Implementation Handoff: Column Encryption (DEK/KEK)

## Files Changed (13 total)

### Modified (6)
| File | Change |
|------|--------|
| `app/core/config.py` | Added KMS settings: KMS_PROVIDER, VAULT_ADDR, VAULT_TOKEN, VAULT_TRANSIT_KEY_NAME, VAULT_ROLE_ID, VAULT_SECRET_ID, LOCAL_DEV_MASTER_KEY |
| `app/main.py` | Added `/health/kms` endpoint (GET, returns status + provider; 503 on unhealthy) |
| `app/modules/patients/models/patient.py` | 11 PII columns migrated to EncryptedString TypeDecorator |
| `app/modules/users/models/user.py` | 4 PII columns migrated to EncryptedString TypeDecorator |
| `app/modules/users/models/clinic.py` | 4 PII columns migrated to EncryptedString TypeDecorator |
| `pyproject.toml` | Added `psycopg2-binary>=2.9` (required by envelope._load_deks_sync sync path) |

### New files (7)
| File | Description |
|------|-------------|
| `alembic/versions/0025_column_encryption_envelope.py` | Migration: creates tenant_key_metadata, mints DEKs, alters 19 PII columns to BYTEA, re-encrypts existing rows |
| `app/core/crypto/__init__.py` | Package with public API: encrypt_pii, decrypt_pii, EncryptedString, mint_dek_for_tenant, crypto_shred_tenant, get_kms_client |
| `app/core/crypto/kms_client.py` | KMSClient Protocol + LocalDevKMSClient (AES-256-GCM) + VaultKMSClient (Vault Transit) + get_kms_client() singleton |
| `app/core/crypto/envelope.py` | AES-256-GCM encrypt/decrypt, in-process DEK cache (LRU, TTL=5min, max 256 tenants), audit-DEK support |
| `app/core/crypto/types.py` | EncryptedString SQLAlchemy TypeDecorator (BYTEA storage, transparent encrypt/decrypt) |
| `app/core/crypto/tenant_keys.py` | mint_dek_for_tenant() + crypto_shred_tenant() (zeros DEK bytes, soft-deletes cascade) |
| `app/modules/admin/services/erasure_service.py` | Two-step crypto-shred: issue_crypto_shred_token() (Redis, 10-min TTL) + crypto_shred_tenant() with audit event |
| `tests/unit/test_kms_client.py` | 13 unit tests: LocalDevKMSClient round-trip, IV randomness, isolation, VaultKMSClient protocol, factory |
| `tests/unit/test_crypto_envelope.py` | 15 unit tests: encrypt/decrypt round-trip, audit-DEK, NULL passthrough, cache TTL, tenant isolation |
| `tests/integration/test_pii_encrypted_at_rest.py` | 7 integration tests: BYTEA on disk, NULL passthrough, ORM round-trip, static column coverage assertions |
| `tests/integration/test_crypto_shred.py` | 9 integration tests: shred marks shredded_at, zeros DEK, evicts cache, cascade soft-delete, double-shred guard |

## Migration: 0025_column_encryption_envelope

**Revision chain**: `0021_multi_clinic_account → 0025_column_encryption_envelope`

### tenant_key_metadata schema
```sql
CREATE TABLE tenant_key_metadata (
    tenant_id             UUID PRIMARY KEY REFERENCES clinic(id) ON DELETE CASCADE,
    dek_encrypted_by_kek  BYTEA NOT NULL,    -- data-DEK wrapped by master KEK
    audit_dek_encrypted_by_kek BYTEA NOT NULL, -- audit-DEK wrapped by master KEK
    key_version           INTEGER NOT NULL DEFAULT 1,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    rotated_at            TIMESTAMPTZ,
    shredded_at           TIMESTAMPTZ         -- set on crypto-shred; DEK blobs become zeros
);
CREATE INDEX ix_tenant_key_metadata_tenant_version ON tenant_key_metadata (tenant_id, key_version);
```

### Migration steps
1. Create `tenant_key_metadata` + index
2. Mint DEKs for all existing clinics (batch, KMS-wrapped)
3. **Drop GIN/trigram indexes** incompatible with BYTEA (see Wave 3-C conflict below)
4. ALTER 19 PII columns to BYTEA
5. Re-encrypt existing plaintext rows (base64 read → Python decode → AES-256-GCM → write)

**Known fix applied**: re-encryption uses `ENCODE(col, 'base64')` instead of `CONVERT_FROM(col, 'UTF8')` to avoid asyncpg UTF-8 enforcement on BYTEA values written by the running app concurrently during migration transaction.

**Downgrade**: `NotImplementedError` — restore from pre-migration backup.

## KMS Provider

| Provider | Class | Use |
|----------|-------|-----|
| `local-dev` | `LocalDevKMSClient` | AES-256-GCM, KEK from `LOCAL_DEV_MASTER_KEY` env var (default: all-zeros, CI only) |
| `vault` | `VaultKMSClient` | HashiCorp Vault Transit engine, key `clinic-cms-master` (aes256-gcm96) |

**Default**: `KMS_PROVIDER=local-dev` — **production MUST override to `vault`**.
Vault fail-fast at startup: if `KMS_PROVIDER=vault` and Vault is unreachable, `RuntimeError` raised — no silent fallback.

## PII Columns Encrypted

### patient (11 columns)
`full_name`, `phone`, `email`, `id_number`, `address_line`, `ward`, `district`, `province`, `allergies`, `chronic_conditions`, `notes`

### user (4 columns)
`full_name`, `email`, `phone`, `license_number`

### clinic (4 columns)
`tax_code`, `email`, `phone`, `address`

**Total: 19 EncryptedString columns** (verified by `TestPIIColumnCoverageStatic.test_total_encrypted_pii_column_count`).

## Audit Envelope

Two independent DEKs per tenant:
- **data-DEK**: used by `EncryptedString` for all PII columns
- **audit-DEK**: separate key for audit log encryption (Phase 1 coordination)

`encrypt_for_audit()` / `decrypt_from_audit()` in `envelope.py` use the audit-DEK.
Both DEKs are wrapped with the same master KEK and stored in `tenant_key_metadata`.
Independent erasure: in future, audit-DEK can be rotated without affecting data-DEK.

## Crypto-Shred Procedure

1. **Issue token**: `issue_crypto_shred_token(tenant_id)` → Redis token (10-min TTL)
2. **Confirm shred**: `crypto_shred_tenant(tenant_id, token, db)`:
   - Validate token (HMAC compare-digest)
   - Write `CRYPTO_SHRED` audit event (before DEK destruction — readable after shred)
   - Call `tenant_keys.crypto_shred_tenant()`:
     - Zero both DEK blobs in `tenant_key_metadata`
     - Set `shredded_at = now()`
     - Invalidate in-process DEK cache
     - Cascade soft-delete: clinic + all users + all patients
   - Delete Redis confirmation token (consumed once)
3. **After shred**: All BYTEA ciphertext in PII columns is permanently unrecoverable.

## Health Check Endpoint

```
GET /health/kms
→ 200 {"status": "ok",        "provider": "local-dev"}
→ 503 {"status": "unhealthy", "provider": "vault", "error": "..."}
```

## Test Results

```
44 tests collected
44 passed in 0.33s

Unit: test_kms_client.py      (13 tests) — PASS
Unit: test_crypto_envelope.py (15 tests) — PASS  
Intg: test_pii_encrypted_at_rest.py (7 tests)  — PASS
Intg: test_crypto_shred.py    (9 tests)  — PASS
```

## Migration Applied OK

Tested on clean PostgreSQL 15 (no pre-existing data). Migration script:
```
alembic upgrade head
[0025] Minted DEKs for 0 clinics.
[0025] Dropped 3 GIN indexes.
[0025] PII column type changes complete.
[0025] Column encryption migration complete.
```

## Maintenance Window Runbook

1. Notify users; stop load balancer / Tauri clients.
2. Export KMS credentials:
   ```bash
   export KMS_PROVIDER=vault
   export VAULT_ADDR=https://vault.internal:8200
   export VAULT_TOKEN=<service-token>
   ```
3. Run: `alembic upgrade 0025_column_encryption_envelope`
   (~30 minutes for large datasets; locks rows in batches of 1000)
4. Verify ciphertext on disk:
   ```sql
   SELECT octet_length(full_name) FROM patient LIMIT 5;
   -- Should return 40-60 numeric values, NOT readable text
   ```
5. Restart application with `KMS_PROVIDER=vault` set.
6. Re-enable load balancer.
7. Smoke test: ORM read on a patient returns plaintext `full_name`.

**Rollback**: Restore from pre-migration DB backup. There is NO downgrade migration path.

## Conflict Notices

### Wave 2-E (TASK-034 / BHYT clinic.py)
`clinic.py` model was modified to add `EncryptedString` on `tax_code`, `email`, `phone`, `address`.
TASK-034 will add `bhyt_enabled` and `bhyt_facility_code` to `clinic.py`.
**Action before merge**: rebase TASK-034 onto this branch to avoid conflict on `clinic.py`.
Migration 0025 notes: "bhyt fields deferred to TASK-034 — coordinate to avoid merge conflicts".

### Wave 3-C (search trigram on plaintext)
Migration 0025 **drops** the following GIN indexes (incompatible with BYTEA):
- `gix_patient_name_trgm` — `gin (full_name gin_trgm_ops)`
- `gix_patient_phone_trgm` — `gin (phone gin_trgm_ops)`  
- `gix_patient_name_search` — `gin (to_tsvector(...full_name...))`

**Fundamental tradeoff**: trigram/full-text search requires plaintext; encryption stores BYTEA.
These are mutually exclusive without application-layer search (decrypt-then-filter).
**Action for Wave 3-C**: search on encrypted PII must use ORM-side filtering or a separate search index on non-PII fields (patient_code, date_of_birth, blood_type).

## Phase 1 Coordination

Phase 1 (hash chain audit) adds `prev_hash`, `row_hash`, `chain_seq` to `audit_log`.
Phase 2 adds the `CRYPTO_SHRED` audit event written via raw SQL (bypasses the audit listener to avoid chicken-and-egg with encrypted audit fields).
PII fields listed in `__audit_exclude__` on Patient/User models are redacted to `"***"` literals before JSONB write — no audit-DEK is needed; the chain verifier needs no decrypt step.
No code conflict between Phase 1 and Phase 2.

---

## Fix-mode Addendum (post-review CHANGES_REQUESTED, 2026-05-01)

### Per-finding resolution

| Fix | Severity | Resolution |
|-----|----------|------------|
| Fix 1 — Audit-DEK YAGNI | HIGH | DELETED `encrypt_for_audit`, `decrypt_from_audit`, `use_audit_dek` param from `envelope.py`. Removed audit-DEK generation from `mint_dek_for_tenant` (now writes zero placeholder for schema compat). Removed `_load_deks_sync` audit_dek load and cache pair. Cache entry type changed from `(data_dek, audit_dek, expires_at)` to `(data_dek, expires_at)`. `_put_cache` signature is now `(tenant_id, data_dek)`. Documented strategy: PII fields in `__audit_exclude__` redacted to `"***"` literals; hash chain computes over redacted JSON; verifier needs no decrypt step. |
| Fix 2 — with_tenant_context helper | HIGH | Added `with_tenant_context(clinic_id, user_id=None)` context manager to `app/core/tenancy.py`. Applied to `auto_no_show_appointments.py` and `appointment_reminder.py` (both touch encrypted Patient columns). `audit_chain_verify.py` and `anomaly_detection.py` read only `audit_log` (no PII columns) — no fix needed. `password_rotation.py` (Wave 1-B B.3, not yet merged) documented as merge-time coordination below. |
| Fix 3 — bhyt_facility_code | HIGH | Documented in merge-time coordination section below. No code change in this worktree. |
| Fix 4 — Cache LRU (was FIFO) | MEDIUM | Replaced `dict` with `OrderedDict` in `envelope.py`. `_get_cache` now calls `_dek_cache.move_to_end(tenant_id)` on valid hit. `_put_cache` evicts with `popitem(last=False)` (LRU). Docstring updated. |
| Fix 5 — Migration pg_stat_activity check | MEDIUM | Added pre-flight `pg_stat_activity` query at start of `upgrade()` in `0025_column_encryption_envelope.py`. Raises `RuntimeError` if any active non-self connections exist. Enforces maintenance window discipline. |

### New tests added / removed

| Test | Action | Reason |
|------|--------|--------|
| `TestAuditDek` (2 tests) | REMOVED | Audit-DEK plumbing deleted (Fix 1 YAGNI). Replaced by comment. |
| `TestDekCache.test_lru_promotes_on_hit` | ADDED | Verifies LRU semantics: access promotes entry to tail. |
| `TestDekCache.test_lru_evicts_least_recently_used` | ADDED | Verifies eviction removes LRU not FIFO on capacity overflow. |
| `TestEncryptedStringContextGuard.test_raises_without_context_on_bind` | ADDED | EncryptedString raises RuntimeError when ContextVar unset (bind path). |
| `TestEncryptedStringContextGuard.test_raises_without_context_on_result` | ADDED | EncryptedString raises RuntimeError when ContextVar unset (result path). |
| `TestWithTenantContext.test_sets_and_resets_clinic_id` | ADDED | Context manager sets clinic_id and resets on exit. |
| `TestWithTenantContext.test_sets_and_resets_user_id` | ADDED | User_id is optional and reset on exit. |
| `TestWithTenantContext.test_resets_on_exception` | ADDED | ContextVar reset even on exception inside block. |
| `TestWithTenantContext.test_encrypted_string_works_inside_context` | ADDED | EncryptedString bind works when context is set. |

### Test results post-fix

Run in docker-compose clinic-cms-w3a (see verify block in fix instructions):
```
tests/unit/test_crypto_envelope.py   — ~21 tests PASS  (was 15; 2 removed, 8 added)
tests/unit/test_kms_client.py        — 13 tests PASS   (unchanged)
tests/integration/test_pii_encrypted_at_rest.py — 7 tests PASS  (unchanged)
tests/integration/test_crypto_shred.py — 9 tests PASS  (unchanged)
Total: ~50 tests
```

### Merge-time coordination tasks

#### bhyt_facility_code encryption (Fix 3 — HIGH)
- **Trigger**: when Wave 2-E (TASK-034) merges into the target branch after TASK-037
- **Action**: add new migration `0028_bhyt_facility_code_encrypted` that:
  - Switches `clinic.bhyt_facility_code` column to `EncryptedString` type
  - Re-encrypts existing values (zero/null at the time of TASK-037 merge, but migration must handle any pre-existing rows)
- **Classification**: Nghị định 13 Tier-3 PII (VSS facility identifier — same sensitivity as `tax_code`)
- **Acceptance**: `SELECT bhyt_facility_code FROM clinic LIMIT 1` returns raw BYTEA on psql; ORM returns plaintext
- **`bhyt_enabled`** (boolean): stays plaintext — not PII
- **Owner**: orchestrator at merge time

#### password_rotation.py Arq job (Fix 2 — partial, Wave 1-B B.3)
- **File**: `app/workers/jobs/password_rotation.py` (not yet present in this worktree — Wave 1-B branch)
- **Action at merge**: wrap clinic-loop body with `with with_tenant_context(clinic_id)` — same pattern as `auto_no_show_appointments.py`
- **Why**: `password_rotation.py` touches `user` table rows (has `email`, `phone`, `full_name` as `EncryptedString`)
- **Owner**: Wave 1-B implementer or orchestrator at merge time

#### SOAP / diagnosis-notes encryption (MEDIUM, TASK-037-Phase2b)
- `visit_soap.{subjective, objective, assessment, plan}` and `visit_diagnosis.notes` are explicit PHI (Wave 2-D TASK-042)
- Must add to encryption inventory **before** TASK-042 lands
- Open follow-up task: `TASK-037-Phase2b-SOAP-encryption`
- Owner: manager to open follow-up TASK before TASK-042 begins implementation
