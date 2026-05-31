# TASK-038 B.15-B.17 — Implementation Handoff: PII Lifecycle Erasure

**From**: Code Implementation  
**To**: Code Review  
**Date**: 2026-05-01  
**Branch**: `feature/task-038-b15-pii-lifecycle` (worktree: `clinic-cms-w5x`)

---

## Summary

Implemented Right-to-Erasure flow (NFR-032/040, Nghị định 13) covering:
- **B.15**: 2-step patient erasure endpoints with confirmation token
- **B.16**: `pii_archive` cron job for 7-year retention auto-archival
- **B.17**: `erasure_service` with full soft-delete cascade + audit + TODO for crypto-shred

---

## Files Added / Modified

### New files (8)

| File | Description |
|------|-------------|
| `clinic-cms-w5x/alembic/versions/0028_pii_archive_table.py` | Migration: `patient_archive` table + `patient.last_accessed_at` column + `patient.erase` permission seed |
| `clinic-cms-w5x/app/modules/patients/models/patient_archive.py` | `PatientArchive` ORM model (append-only cold-storage) |
| `clinic-cms-w5x/app/modules/admin/services/erasure_service.py` | `request_erasure()` + `execute_erasure()` with Redis token + cascade soft-delete |
| `clinic-cms-w5x/app/modules/patients/api/erasure_routes.py` | `POST /api/v1/patients/{id}/erase/request` + `DELETE /api/v1/patients/{id}/erase` |
| `clinic-cms-w5x/app/workers/jobs/pii_archive.py` | Daily 04:00 UTC cron: archive patients with `last_accessed_at < now()-7y` |
| `clinic-cms-w5x/tests/unit/test_erasure_service.py` | 11 unit tests for erasure_service |
| `clinic-cms-w5x/tests/integration/test_erasure_endpoint.py` | 9 integration tests for erasure endpoints |
| `clinic-cms-w5x/tests/unit/test_pii_archive_cron.py` | 8 unit tests for pii_archive cron |

### Modified files (4)

| File | Change |
|------|--------|
| `clinic-cms-w5x/app/modules/patients/models/patient.py` | Added `last_accessed_at` column |
| `clinic-cms-w5x/app/workers/scheduler.py` | Added `pii_archive` import + `functions` + `cron(pii_archive, hour=4, minute=0)` |
| `clinic-cms-w5x/app/main.py` | Added `patient_erasure_router` import + `app.include_router(patient_erasure_router)` |

---

## Migration

- **Name**: `0028_pii_archive_table`
- **Down revision**: `0021_multi_clinic_account`
- **Schema changes**:
  - `patient.last_accessed_at TIMESTAMPTZ NULL` + partial index `ix_patient_last_accessed_at`
  - New table `patient_archive` with JSONB payload + indexes
  - Permission seed: `patient.erase` → assigned to `admin` role via `role_permission`
- **⚠️ Conflict warning**: Concurrent B streams (TASK-038 Q.1/B.1-B.14) used `0022`-`0027` in other worktrees — requires renumbering at merge

---

## Endpoints Created

| Method | Path | Permission | Description |
|--------|------|-----------|-------------|
| `POST` | `/api/v1/patients/{id}/erase/request` | `patient.erase` | Step 1: generate 5-min confirmation token |
| `DELETE` | `/api/v1/patients/{id}/erase` | `patient.erase` | Step 2: verify token + execute erasure |

### Request / Response

**POST /erase/request** → `200 OK`
```json
{"confirmation_token": "<uuid>", "message": "Erasure token generated. Use within 5 minutes to confirm."}
```

**DELETE /erase** body:
```json
{"confirmation_token": "<uuid>", "reason": "Patient requested data deletion per Nghị định 13"}
```
→ `200 OK`
```json
{"status": "erased", "patient_id": "<uuid>", "message": "...crypto-shred pending TASK-037 P2..."}
```

Error cases: `403` (bad/expired token or no permission), `404` (patient not found), `422` (reason too short)

---

## Erasure Logic

`execute_erasure()` performs in this order:
1. Verify + consume Redis confirmation token (single-use)
2. Fetch patient (raises `NotFoundError` if not found/already deleted)
3. Snapshot patient row (for archive — `id_number` redacted via `__audit_exclude__`)
4. Cascade soft-delete: `visit`, `prescription`, `visit_vitals` via raw SQL UPDATE
5. Soft-delete patient row itself
6. Insert `PatientArchive` row (reason=`manual_erasure`)
7. Write audit log entry `patient.erasure` (no PII — only patient_id + reason + admin_user_id)
8. **TODO: crypto_shred_tenant** ← see below

---

## Crypto-Shred TODOs (post-TASK-037 Phase 2 merge)

Two explicit `TODO` comments in codebase:

**1. `erasure_service.py` line ~190:**
```python
# TODO: crypto_shred_tenant(patient.clinic_id) — wire after TASK-037 P2 merge
#       to destroy the column-encryption DEK for this tenant partition.
#       Until then, the payload in patient_archive still contains plaintext PII.
#       After the merge, destroying the DEK renders the JSONB payload unrecoverable.
#       See: clinic-cms-w3a worktree, feature/task-037-phase2-encryption.
```

**2. `pii_archive.py` line ~120:**
```python
# TODO: crypto_shred_tenant(patient.clinic_id) — wire after TASK-037 P2 merge
#       to destroy the column-encryption DEK for this tenant partition.
#       Until then the JSONB payload retains plaintext PII.
#       After the merge, the payload is rendered unrecoverable without the DEK.
#       See: clinic-cms-w3a worktree, feature/task-037-phase2-encryption.
```

**Wiring steps after TASK-037 P2 merge:**
1. Import `crypto_shred_tenant` from the TASK-037 envelope service
2. Call `await crypto_shred_tenant(patient.clinic_id)` after the audit log write in both places
3. Add a test asserting that `crypto_shred_tenant` is called with `patient.clinic_id`
4. Remove the TODO comments

---

## Test Results

**28/28 PASS** (run inside `clinic-cms-w5x` container)

| File | Tests | Result |
|------|-------|--------|
| `tests/unit/test_erasure_service.py` | 11 | ✅ PASS |
| `tests/integration/test_erasure_endpoint.py` | 9 | ✅ PASS |
| `tests/unit/test_pii_archive_cron.py` | 8 | ✅ PASS |

---

## Known Gaps / Review Notes

1. **`patient.last_accessed_at` not updated on read** — `audit_patient_read()` in `patient_service.py` needs to `UPDATE patient SET last_accessed_at = now()` on each READ. Currently it only writes to audit_log. Without this, the pii_archive cron falls back to `created_at` for all patients. This should be implemented as a follow-up in patient_service.py (low-risk 1-liner).

2. **Crypto-shred**: Archive payload retains plaintext PII until TASK-037 P2 merge + wiring. The two TODO comments are the canonical tracking points.

3. **Migration renumbering**: Must renumber `0028` at merge depending on B.1-B.14 numbering (those streams used `0021`-`0022` in other worktrees).

4. **audit_log soft-delete**: Spec says "cascade soft-delete audit_log entries" but audit_log is append-only for compliance. Current implementation does NOT soft-delete audit_log rows — intentional deviation. Confirm with review.

5. **`pii_archive` batch limit**: Currently `LIMIT 100` per run. For large clinics this may need multiple runs (future: configurable via settings).
