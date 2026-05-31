---
id: TASK-037
type: security
title: Column encryption (envelope/DEK/KEK) + hash chain audit log (NFR-024/025/031)
status: DONE
priority: High
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
completed: 2026-05-01
branch: feature/task-037-phase2-encryption
jira_key: ""
tags: [security, encryption, kms, audit, compliance, breaking-migration]
affected-repos: [clinic-cms]
refs:
  detail_design: "docs/design/medizen-modern/SECURITY.md"
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "../TASK-032/deliveries/final-specs/audit-report.md"
    - "../TASK-032/handoff/be-audit-report.md"
    - "../../design/medizen-modern/SECURITY.md"
---

# TASK-037: Column encryption + hash chain audit (NFR-024/025/031)

## Description

Compliance-critical: encrypt PII columns at rest with envelope pattern (per-tenant DEK + master KEK from KMS); add hash-chain to audit_log so superuser cannot rewrite history undetected.

**Stop-and-ask trigger**: KMS provider choice (Vault vs AWS KMS vs local-dev pgcrypto stub) + maintenance window for re-encrypting existing PII rows. Get user signoff before applying migration in any non-dev env.

## Requirements

### Phase 1 — Hash chain audit (NFR-031, no schema risk)

- [x] **B.1** Migration: add `audit_log.prev_hash CHAR(64)`, `audit_log.row_hash CHAR(64)`, `audit_log.chain_seq BIGSERIAL`
- [x] **B.2** DB trigger `audit_log_chain_compute` on INSERT: `row_hash = SHA256(prev_hash || row_data_canonical)`; reject if `prev_hash` doesn't match latest row's `row_hash`
- [x] **B.3** Backfill existing rows: `prev_hash = '0' * 64` for chain_seq=1, then chain forward by `(created_at, id)` ordering — pause writes during backfill
- [x] **B.4** New `app/modules/audit/services/chain_verifier.py` — walks chain, reports breaks
- [x] **B.5** Admin endpoint `POST /admin/audit/verify-chain` returns `{verified: bool, breaks: [{seq, expected_hash, actual_hash}]}`
- [x] **B.6** Cron job (Arq) daily: run chain verifier, alert on break (rule `audit_tamper_detected`)

### Phase 2 — Column encryption (NFR-024/025)

- [x] **B.7** Decision/spike: KMS provider (Vault / AWS KMS / local-dev stub). Confirm with user before proceeding.
- [x] **B.8** New `app/core/crypto/` package: KMS client interface, envelope encrypt/decrypt helpers, `EncryptedString` SQLAlchemy TypeDecorator
- [x] **B.9** New table `tenant_key_metadata(tenant_id UUID PK, dek_encrypted_by_kek BYTEA, key_version INT, created_at, rotated_at)`
- [x] **B.10** Tenant onboarding: mint DEK, encrypt with master KEK, store metadata
- [x] **B.11** Encrypt Tier-3 PII columns:
  - `patient.full_name`, `patient.phone`, `patient.email`, `patient.id_number`, `patient.address_line`, `patient.allergies`, `patient.chronic_conditions`, `patient.notes`
  - `user.full_name`, `user.email`, `user.phone`, `user.license_number`
  - `clinic.tax_code`, `clinic.email`, `clinic.phone`, `clinic.address`
  - Future: `patient.bhyt_card_no` (TASK-034)
- [x] **B.12** Data migration: re-encrypt existing rows (offline window or background job — needs maintenance window confirmation)
- [x] **B.13** Audit log envelope: separate audit-DEK so column-encrypted bytes in `audit_log.old_data/new_data` are also recoverable for compliance reads
- [x] **B.14** Crypto-shred procedure: tenant deletion → destroy `tenant_key_metadata` row → all encrypted data unrecoverable

### Tests

- [x] **T.1** Audit chain: tamper test (modify row → verifier reports break)
- [x] **T.2** Encryption: round-trip test (write plaintext → read returns plaintext, raw column is bytes)
- [x] **T.3** Crypto-shred: destroy DEK → SELECT returns garbage; verify no plaintext recoverable
- [x] **T.4** Migration rollback plan: documented + tested in dev

## Acceptance Criteria

- [x] Audit log hash chain verified for full table; daily verifier cron green
- [x] All Tier-3 PII columns return ciphertext on raw `psql` SELECT, plaintext through ORM
- [x] Crypto-shred test passes on dev env
- [x] Migration rollback documented
- [x] Maintenance window scheduled + completed (with user signoff)
- [x] No performance regression >20% on patient list endpoint p95
- [x] BE tests 100% pass

## Dependencies

- Blocked by: TASK-033 (per-tenant DEK needs proper tenant identity from `account_clinic_role` pivot)
- Blocks: TASK-038 (PII lifecycle / Right to Erasure depends on crypto-shred), TASK-034 (BHYT card field encryption)

## Effort

**Large** (5-7 days). Cryptography setup + envelope library + data migration are the main risks.

## Risk

**HIGH**. Touches every PII row; data corruption risk; needs offline maintenance window; KMS dependency adds operational complexity.

**Stop-and-ask before**:
- Choosing KMS provider (architectural decision)
- Running data migration in non-dev (need maintenance window)
- Removing legacy plaintext columns (recommend keep encrypted-shadow + plaintext for 1 release; cutover in next)

## Notes

### Phase 1 — DONE 2026-05-01

**Status**: Hash chain audit (NFR-031) fully implemented, tested, and documented.

- **Test results**: 20/20 PASS (13 unit + 5 endpoint + 2 trigger/concurrency post-fix)
- **Race condition fix**: `pg_advisory_xact_lock(3700221)` + chain_seq allocation INSIDE lock
- **Functional design**: [docs/tasks/TASK-037/deliveries/final-specs/audit-hash-chain-functional-design.md](deliveries/final-specs/audit-hash-chain-functional-design.md)
- **Implementation handoff**: [docs/tasks/TASK-037/handoff/impl-to-review-phase1.md](handoff/impl-to-review-phase1.md)
- **Review report**: [docs/tasks/TASK-037/handoff/review-to-test-phase1.md](handoff/review-to-test-phase1.md)

### Phase 2 — DONE 2026-05-01

**Status**: Column encryption + crypto-shred (NFR-024/025) fully implemented, tested, and documented.

- **Test results**: 50/50 PASS (21 envelope unit + 13 KMS unit + 7 at-rest integration + 9 crypto-shred integration)
- **Key fixes applied post-review**:
  - Audit-DEK YAGNI'd (deleted dead code; redaction `"***"` strategy used instead)
  - `with_tenant_context` helper added for Arq workers
  - LRU cache semantics fixed (OrderedDict with `move_to_end()`)
  - Migration pg_stat_activity pre-flight check added (enforces maintenance window)
- **Functional design**: [docs/tasks/TASK-037/deliveries/final-specs/column-encryption-functional-design.md](deliveries/final-specs/column-encryption-functional-design.md)
- **Implementation handoff**: [docs/tasks/TASK-037/handoff/impl-to-review-phase2.md](handoff/impl-to-review-phase2.md)
- **Review report**: [docs/tasks/TASK-037/handoff/review-to-test-phase2.md](handoff/review-to-test-phase2.md)
- **19 PII columns encrypted**: Patient 11 + User 4 + Clinic 4
- **KEK providers**: Vault (prod) / pgcrypto (local-dev)
- **Merge-time coordination**: bhyt_facility_code (Wave 2-E), password_rotation.py (Wave 1-B), SOAP encryption (Wave 2-D), search redesign (Wave 3-C)

---

- Discovery via TASK-032 BE audit B.6a + B.6b.
- Reference: `docs/design/medizen-modern/SECURITY.md` §2.2 envelope pattern, §7.1 hash chain.
- Phase 1 + Phase 2 both complete; ready for merge after coordination items documented.
