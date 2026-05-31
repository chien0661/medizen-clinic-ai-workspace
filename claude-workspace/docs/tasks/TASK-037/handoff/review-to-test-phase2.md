# TASK-037 Phase 2 — Code Review Report (Review → Test handoff)

**Date**: 2026-05-02
**Reviewer**: Code Review Agent
**Branch**: `feature/task-037-phase2-encryption` (worktree `clinic-cms-w3a`)
**Implementation handoff**: `docs/tasks/TASK-037/handoff/impl-to-review-phase2.md`
**Decision**: **CHANGES_REQUESTED** (1 BLOCKER, 3 HIGH, 5 MEDIUM, 2 LOW)

---

## A. Envelope crypto correctness

| Item | Status | Notes |
|---|---|---|
| AES-256-GCM with random 12-byte IV per encrypt | ✅ | `os.urandom(12)` per call (`envelope.py:166`); 96-bit IV is the NIST-recommended length for GCM. |
| Auth tag captured & verified on decrypt | ✅ | `cryptography`'s `AESGCM.encrypt/decrypt` appends/validates the 16-byte tag implicitly; `InvalidTag` raised on tamper. |
| Wire format documented | ✅ | Header docstring `IV(12) || ciphertext+auth_tag` is clear and matches both prod path (`envelope.py`) and the LocalDevKMS DEK-wrap path. |
| KEK never persisted to DB | ✅ | Only `dek_encrypted_by_kek` and `audit_dek_encrypted_by_kek` are stored in `tenant_key_metadata`. KEK lives in env (LocalDev) or Vault. |
| Per-tenant DEK isolation | ✅ | `test_tenant_isolation` + `test_wrong_dek_raises` verify cross-tenant decrypt fails with `InvalidTag`. |
| Side-channel timing | ✅ | `cryptography` library uses constant-time GCM; HMAC token compare uses `hmac.compare_digest`. |

## B. DEK lifecycle

| Item | Status | Notes |
|---|---|---|
| `mint_dek_for_tenant` generates 256-bit random DEKs | ✅ | `os.urandom(32)` × 2 (data + audit). `ON CONFLICT DO NOTHING` makes it idempotent. |
| KEK wrapping per provider | ✅ | LocalDev: AES-256-GCM with 32-byte KEK from env. Vault: Transit `aes256-gcm96`. |
| Cache TTL/eviction | ⚠️ | **MEDIUM-1**: 5-minute TTL is fine, but `_put_cache` FIFO eviction when `_MAX_ENTRIES=256` reached uses `next(iter(_dek_cache))` which is **insertion-order**, not access-order — pure FIFO, not LRU as the docstring claims. For ≤256 tenants this is academic; flag for the docstring fix. |
| DEK rotation | ⚠️ | **MEDIUM-2**: `key_version` column exists, `rotated_at` exists, but **no rotation function is implemented**. Out-of-scope per handoff but rotation is a NIST 800-57 requirement for AES-256 within 5 years; raise as a follow-up TASK with a hard deadline rather than just a "flagged". |
| Plaintext DEK wipe | ⚠️ | `del data_dek_plain` after wrap is best-effort only — Python may have copies in interpreter buffers. Acceptable; document the limitation. |

## C. EncryptedString TypeDecorator

| Item | Status | Notes |
|---|---|---|
| `process_bind_param` reads `current_clinic_id` | ✅ | Raises `RuntimeError` when ContextVar is unset (anti-silent-bypass). |
| `process_result_value` reads same ContextVar | ✅ | Same guard, applied symmetrically. |
| ContextVar empty in background jobs | ❌ | **HIGH-1**: Arq workers do **not** automatically set `current_clinic_id`. Any background job that reads/writes a Patient/User row will hit `RuntimeError: ... ContextVar is not set`. Audit Arq job code (`app/modules/notifications/`, future scheduled tasks) must set the var per-task or the job crashes. **Add an integration test** that runs through an Arq context, or document a `with_tenant_context(tenant_id)` helper. |
| NULL passthrough | ✅ | Both bind and result return None on None — verified by `test_patient_null_pii_remains_null`. |
| Bytes round-trip | ✅ | `bytes(value)` cast in `process_result_value` handles asyncpg memoryview/bytes both. |
| `cache_ok = True` correctness | ✅ | Type instance has no dialect state — runtime keying via ContextVar is safe. |
| Sync DB engine for DEK load | ⚠️ | **MEDIUM-3**: `_load_deks_sync` creates a fresh `sa.create_engine(...)` per cache miss, then disposes it. A long-lived process-level engine would be much cheaper (every cache miss currently does TCP + auth handshake). Replace with a lazy module-level singleton engine, or import `psycopg2` cursor directly. |

## D. 19 columns encrypted

| Layer | task.md target | Implemented | Status |
|---|---|---|---|
| Patient | 8 | 11 (adds `ward`, `district`, `province`) | ✅ Broader than spec — appropriate for Tier-3 PII per Nghị định 13. |
| User | 4 | 4 | ✅ |
| Clinic | 4 | 4 | ✅ |
| BHYT card | TASK-034 dep | Deferred | ✅ Acknowledged in migration comment + handoff. |
| Visit SOAP (TASK-042 / Wave 2-D) | not in inventory | not encrypted | ⚠️ **MEDIUM-4** — `visit_soap.{subjective, objective, assessment, plan}` + `visit_diagnosis.notes` are explicit PHI per review F1 of Wave 2-D. Add to encryption inventory **before** TASK-042 lands or it ships plaintext PHI. Open follow-up task `TASK-037-Phase2b-SOAP-encryption`. |
| Audit `applied_role` (Wave 3-B) | non-PII | not encrypted | ✅ Correctly excluded — categorical role label is not PII. Verified absent from `_PII_COLUMNS` in migration 0025. |

## E. Crypto-shred procedure

| Item | Status | Notes |
|---|---|---|
| `shredded_at` set | ✅ | `tenant_keys.crypto_shred_tenant` writes timestamp atomically with DEK overwrite. |
| Both DEK blobs zeroed | ✅ | Single UPDATE writes `:zeros` (`bytes(48)`) to both columns. |
| In-process cache evicted | ✅ | `invalidate_tenant_cache` called inside the shred. |
| Cascade soft-delete clinic + users + patients | ✅ | Three UPDATE statements in same tx. |
| Idempotent (double-shred guard) | ✅ | `PermissionError` raised if `shredded_at IS NOT NULL` (verified by test). |
| Audit log entry "tenant.crypto_shred" before destruction | ✅ | Raw SQL INSERT bypasses audit listener (avoids chicken-and-egg with encrypted audit fields). No PII in payload. |
| Two-step Redis token confirmation | ✅ | 10-min TTL, HMAC `compare_digest`, consumed once, bound to tenant_id. |
| 9 crypto-shred tests | ✅ | Cover shred, double-shred, lookup miss, cascade for clinic + users + patients, cache eviction, decrypt-after-shred. |

## F. Audit envelope coordination with Phase 1 — **CRITICAL**

| Item | Status | Notes |
|---|---|---|
| Hash chain (Phase 1) computes over canonical JSON of audit row | ✅ | `fn_audit_row_data_json` builds JSONB from 13 columns including `old_data`/`new_data`. |
| Storage of PII in audit_log | ✅ | Patient + User models have `__audit_exclude__` listing all encrypted PII columns → audit listener writes `"***"` (not ciphertext, not plaintext). Clinic is **not** `__auditable__`, so no concern there. |
| **Hash-vs-encryption interaction** | ✅ | **Option A is realised, but indirectly**: PII is *redacted to* `"***"` *before* JSONB write, so the hash is computed over the redacted-plaintext JSON. There is no encrypted ciphertext stored in `audit_log.old_data/new_data` at all. This is cleaner than Option A (hash plaintext / store ciphertext) — there is no decrypt step needed for the verifier. |
| `encrypt_for_audit` / `decrypt_from_audit` / audit-DEK | ❌ | **HIGH-2 — DEAD CODE / MISLEADING SECURITY CLAIM**: The handoff's "Audit envelope" section claims the audit-DEK is "used by the audit log event listener." It is NOT. `encrypt_for_audit` is implemented but called from **zero** production code paths (verified by grep). The audit-DEK is minted, wrapped, and zeroed-on-shred but never used. Two options: (a) **delete** the audit-DEK plumbing as YAGNI and document that PII redaction is the strategy; or (b) **wire it up** by changing `_redact` in `app/core/audit.py` to encrypt-instead-of-redact for PII fields and adding a `decrypt_audit_payload` helper for the verifier. Option (a) is simpler and safer; option (b) lets compliance reads still see PII history. **Pick one explicitly before merge.** |
| Phase 1 verifier compat | ✅ | `chain_verifier` reads stored JSONB which already has `"***"` placeholder — hash chain stays consistent regardless of Option A/B above (since payloads are identical for verifier and writer). |

## G. Migration 0025 quality

| Item | Status | Notes |
|---|---|---|
| Rescue Bug 1 — GIN drop ordering | ✅ | Now drops 3 GIN/trigram indexes **before** ALTER TYPE (previously failed with "cannot drop type because index depends"). |
| Rescue Bug 2 — `ENCODE base64` for asyncpg BYTEA read | ✅ | `SELECT ENCODE(col, 'base64')` + Python `base64.b64decode` avoids asyncpg's strict UTF-8 enforcement on raw BYTEA. |
| Rescue Bug 3 — `psycopg2-binary` dep | ✅ | Added to pyproject.toml; required because `_load_deks_sync` uses sync engine. |
| Backfill batches of 1000 | ✅ | LIMIT/OFFSET; double-encryption guard via UTF-8 decode probe. |
| Hard cutover (no shadow column) | ✅ | User accepted ~30 min downtime per task notes. |
| Downgrade | ✅ | `NotImplementedError` is the correct stance — explicit DB restore documented. |
| Migration parent revision | ⚠️ | **LOW-1**: `down_revision = "0021_multi_clinic_account"` skips revision IDs 0022–0024. If the hash-chain Phase 1 lives at `0022_audit_hash_chain`, this will not chain correctly when both branches merge. Verify `alembic history` is linear in the merge commit; if not, add a merge migration. |
| Re-encrypt non-default `clinic_col` for clinic table | ✅ | Special case `if table == "clinic": clinic_col = "id"` is correct. |
| Concurrent-write hazard during ALTER + backfill | ⚠️ | **MEDIUM-5**: Migration assumes app traffic is stopped. The backfill's "skip if not valid UTF-8" guard partially defends against double-encryption, but if the running app inserts a value that *coincidentally* decodes as valid UTF-8, it will be re-encrypted, yielding `IV || enc(IV||cipher)`. The runbook's step 1 ("stop load balancer") is the real guard — add a hard fail-fast assertion (e.g., check `pg_stat_activity` for active app sessions) before the data step. |

## H. Performance

| Item | Status | Notes |
|---|---|---|
| DEK cache hit rate | ⚠️ | **MEDIUM-6**: No measurement. With 5-minute TTL and `_load_deks_sync` paying ~5–20 ms per miss (engine create + Vault round-trip), cold-start per worker on every patient list call is non-trivial. Recommend: instrument `_get_deks` with structlog miss-count + benchmark before/after on `GET /patients` p95. |
| Per-PII-column overhead | ⚠️ | AES-GCM is ~1 µs per short string on modern x86; serializing 11 PII fields per Patient row at 1k rows/page is ~10 ms — likely well within the NFR budget (<20% regression on patient list p95) but not measured. |
| Recommended benchmark | ⚠️ | **Required by acceptance criterion** ("No performance regression >20% on patient list endpoint p95"). Test agent must run a before/after benchmark on the migrated DB and document it in `deliveries/test-reports/`. |

## I. Security risks

| Item | Status | Notes |
|---|---|---|
| LocalDev provider unsafe in prod | ✅ | Default `KMS_PROVIDER=local-dev` logs `kms.local_dev_mode` warning; production runbook step 5 sets `KMS_PROVIDER=vault`. Recommend: assert `settings.ENVIRONMENT != "production" or settings.KMS_PROVIDER == "vault"` at startup to fail-closed. **LOW-2**. |
| Vault fail-fast at startup | ✅ | `RuntimeError` on unhealthy Vault — no silent fallback. |
| KEK rotation | ⚠️ | Out-of-scope. Vault Transit supports key versioning with auto-rewrap; document the operational procedure even if not coded. |
| `LOCAL_DEV_MASTER_KEY` default `"00"*32` | ⚠️ | All-zeros KEK in CI is acceptable for tests; ensure `.env.example` and Docker compose for staging override it explicitly. |

## J. Cross-cutting collisions — **CRITICAL**

| Wave | Collision | Resolution |
|---|---|---|
| **Wave 2-E (TASK-034 BHYT)** | `clinic.py` modified by both: this branch encrypts `tax_code/email/phone/address`; TASK-034 adds `bhyt_enabled`/`bhyt_facility_code`. | ❌ **HIGH-3 — Merge collision**: Take both column sets at merge. **`bhyt_facility_code` is Tier-3 PII** under Nghị định 13 (links a clinic to a healthcare facility identifier — same sensitivity as `tax_code`) — **must also use `EncryptedString`** in TASK-034. `bhyt_enabled` (boolean) stays plaintext. Add a follow-up migration `0026_bhyt_columns_encrypted` after both branches merge. Document this in the merge runbook. |
| **Wave 3-C (TASK-040 Cmd+K search)** | Migration 0025 **permanently drops** 3 GIN/trigram indexes on `patient.full_name/phone/id_number`. | ❌ **BLOCKER for Wave 3-C**: server-side trigram on encrypted BYTEA is fundamentally impossible. Wave 3-C MUST switch strategy to one of: (a) **searchable encryption** — store HMAC-SHA256 of plaintext under a per-tenant search-key as a side column with a btree/hash index (allows exact + prefix match only, no fuzzy); (b) **ORM-side decrypt-then-filter** with patient_code/DOB pre-filter to bound the candidate set (acceptable up to ~10k patients/clinic); (c) **plaintext-only fields** for search (patient_code already exists; not encrypting it is the design choice). Recommend (a) for `phone` and `id_number` (exact match) + (b) for `full_name` (fuzzy needed). Document this trade-off in TASK-040's design before merge. |
| **Wave 2-D (TASK-042 EMR SOAP)** | `visit_soap.{subjective,objective,assessment,plan}` + `visit_diagnosis.notes` are PHI. | See D above — open `TASK-037-Phase2b` follow-up. |
| **Wave 3-B (TASK-035 multi-role)** | `audit_log.applied_role` non-PII. | ✅ Correctly excluded. Verify Phase 1 hash chain is updated to include `applied_role` in `fn_audit_row_data_json` after Wave 3-B merges (already noted in Phase 1 review as HIGH-2 follow-up). |

## K. Test quality

| Item | Status | Notes |
|---|---|---|
| Coverage breadth | ✅ | 44 tests: round-trip (15), KMS (13), at-rest (7), shred (9). |
| Negative tests — wrong tenant decrypt fails | ✅ | `test_wrong_dek_raises`, `test_data_dek_ciphertext_not_readable_by_audit_dek`. |
| Concurrency — concurrent encrypt/decrypt | ❌ | **MEDIUM-7**: No test exercises two concurrent tasks encrypting/decrypting different tenants on the same worker (cache contention is technically GIL-safe but eviction race is untested). Add `test_concurrent_tenants_no_cross_contamination`. |
| `EncryptedString` raises when ContextVar empty | ⚠️ | Not directly asserted in tests. Add unit test `test_encrypted_string_raises_without_context`. |
| Migration backfill double-encrypt guard | ⚠️ | The UTF-8 decode probe is logic-tested only by inspection; add a fixture-driven test for partial-migration replay. |
| Real Vault integration test | ⚠️ | Only protocol-shape test exists. CI doesn't run against a live Vault. Acceptable for unit/integration suites but staging must validate. |

---

## Summary of issues

| ID | Severity | Issue | Owner |
|---|---|---|---|
| F-2 | **HIGH** | Audit-DEK is dead code; security claim in handoff is misleading. Pick "delete YAGNI" or "wire into audit listener" before merge. | Implementation |
| C-1 | **HIGH** | Background jobs (Arq) will crash on PII access — `current_clinic_id` not set. Add helper + tests. | Implementation |
| J-Wave3C | **BLOCKER** | Wave 3-C trigram search is now impossible on encrypted columns; must redesign search strategy before TASK-040 merges. | Wave 3-C / Manager |
| J-Wave2E | **HIGH** | `bhyt_facility_code` (Tier-3) needs encryption; coordinate merge order. | TASK-034 |
| D-Wave2D | **MEDIUM** | Visit SOAP / diagnosis-notes (PHI) need encryption inventory entry — open follow-up task. | Manager |
| B-1 | MEDIUM | Cache claims LRU but is FIFO — docstring fix. | Implementation |
| B-2 | MEDIUM | DEK rotation function missing; open follow-up TASK with deadline. | Manager |
| C-3 | MEDIUM | `_load_deks_sync` creates a fresh engine per cache miss — performance fix. | Implementation |
| G-Mig | MEDIUM | Backfill double-encrypt hazard during concurrent writes — add fail-fast assertion. | Implementation |
| H-1 | MEDIUM | No DEK cache hit-rate / patient-list p95 benchmark. | Test |
| K-1 | MEDIUM | No concurrent-tenant cache test. | Test |
| G-1 | LOW | Verify alembic history is linear after Phase 1 merge. | Implementation |
| I-1 | LOW | Add `ENVIRONMENT==prod ⇒ KMS_PROVIDER==vault` startup assertion. | Implementation |

## Decision: **CHANGES_REQUESTED**

**Must-fix before test phase**:
1. Resolve **F-2** (audit-DEK YAGNI vs wire-up) — decision + code change
2. Resolve **C-1** (Arq tenant-context helper + test)
3. Document **J-Wave3C** strategy in TASK-040 design (blocks Wave 3-C, not this task)
4. Open follow-up tasks for **J-Wave2E** (bhyt_facility_code) and **D-Wave2D** (SOAP)

**Test phase deliverables required**:
- Performance benchmark on patient list p95 (acceptance criterion)
- Crypto-shred end-to-end smoke test on dev DB
- Vault provider integration smoke test (staging only OK)
- Concurrent tenant test (K-1)
