# TASK-038 B.15-B.17 — Code Review Report: PII Lifecycle + Right to Erasure

**From**: Code Review
**To**: Test
**Date**: 2026-05-01
**Branch**: `feature/task-038-b15-pii-lifecycle` (worktree `clinic-cms-w5x`)
**Decision**: **APPROVED with follow-ups**

---

## Summary

Implementation correctly realises the 2-step Right-to-Erasure flow (NFR-032/040, Nghị định 13) and the 7-year retention archival cron. Code quality is strong, security invariants are well-enforced, and test coverage at 28/28 is appropriate for the surface area. Two non-blocking follow-ups are required (one is already documented; one is newly identified during review). Crypto-shred TODOs are correctly scoped and clearly tracked.

---

## A. Migration `0028_pii_archive_table` — APPROVED with merge note

| Item | Status | Note |
|------|--------|------|
| Schema correctness (`patient_archive` + `last_accessed_at`) | OK | Indexes (clinic_id, archived_at, partial on `last_accessed_at WHERE is_deleted=FALSE`) appropriate |
| `down_revision` chain | WARNING | `down_revision = "0021_multi_clinic_account"` — confirmed as B.5-B.7 / B.8-B.14 / B.1-B.4 each picked `0021`-`0027` in sibling worktrees. Renumber at merge unavoidable. |
| Rollback path | OK | Idempotent UNINSTALL (DELETE permission, DROP indexes, DROP table, DROP column). Safe. |
| Permission seed convention | OK | `patient.erase` matches 2-level dotted convention; `ON CONFLICT DO NOTHING` for re-run safety. |
| `UniqueConstraint` on `original_patient_id` | OK | Prevents double-archival of same patient. |

**Required at merge**: Rename file + `revision`/`down_revision` to slot after merged head of TASK-037 P2 + TASK-035 + TASK-036 + TASK-045. Per impl handoff, candidate is `0030_pii_archive_table` (down_revision=`0029_xxx`).

---

## B. Erasure 2-step flow — APPROVED

| Item | Status | Note |
|------|--------|------|
| Token generation (UUID4, 5-min Redis TTL, single-use delete) | OK | `_TOKEN_TTL_SECONDS=300`, `r.delete(key)` after verification = single-use. |
| Token scoping per `patient_id` | OK | Key `erase:confirm:{patient_id}` — token cannot be reused across patients. |
| Token cross-admin replay | ACCEPTABLE | Stored payload includes `admin_user_id` but `_verify_and_consume_token` does NOT check it. This is intentional — any admin holding `patient.erase` permission can confirm any open token. Recommend hardening (see Follow-ups #2). Non-blocking because `patient.erase` is admin-only and audit captures actual executor. |
| `reason` validation (5-500 chars) | OK | Enforced via Pydantic `min_length=5, max_length=500`. |
| Audit log content (no PII) | OK | Only `patient_id`, `admin_user_id`, `reason`, `erased_at`. Verified by unit test `test_execute_writes_audit_log_no_pii`. |
| Error semantics | OK | 403 (token), 404 (not found / already deleted), 422 (reason too short). |
| Idempotent re-request | OK | `request_erasure` overwrites prior token — fresh 5-min window. |

---

## C. Crypto-shred TODOs — APPROVED

| Item | Status |
|------|--------|
| TODO comment in `erasure_service.py` line 197 | OK — quote-accurate, references `clinic-cms-w3a` worktree |
| TODO comment in `pii_archive.py` line 159 | OK — same pattern |
| Wiring instructions in handoff (4-step procedure) | OK — clear, includes test assertion to add |
| Path call: `crypto_shred_tenant(patient.clinic_id)` after audit write | OK — correct order (audit must commit before DEK destruction so audit row remains forensically retrievable) |

**Verified**: When TASK-037 P2 merges, the integration is single-line + import in two locations + one new test. Low effort, well-isolated.

---

## D. `pii_archive` cron — APPROVED with documented gap

| Item | Status | Note |
|------|--------|------|
| Schedule: `cron(pii_archive, hour=4, minute=0)` | OK | Registered in `WorkerSettings.cron_jobs` (line 66). |
| Filter logic | OK | `last_accessed_at < cutoff OR (last_accessed_at IS NULL AND created_at < cutoff)` — correct fallback. |
| Per-patient mini-transaction | OK | Failure isolation per patient — single failure does not abort batch. |
| Race guard | OK | Re-fetches patient inside `db.begin()` and re-checks `is_deleted` + last access date. |
| `_BATCH_SIZE=100` per run | ACCEPTABLE | For very large clinics, multiple cron runs needed; flagged in handoff for future config. |
| Audit insert via raw SQL with f-string for `new_data` | MINOR | UUID/ISO-string interpolation is safe (cannot break JSON), but `json.dumps(...)` would be cleaner. Non-blocking. |
| **`patient.last_accessed_at` not updated on read** | KNOWN GAP | `audit_patient_read()` in `patient_service.py:300-327` writes audit but does NOT update `last_accessed_at`. Cron silently falls back to `created_at` for ALL patients until this is fixed. |

**Severity of last_accessed_at gap**: MEDIUM. Functional impact today is zero (no patient is older than 7 years in any deployed clinic), but production correctness depends on fix landing before the first dataset crosses the 7-year mark. Recommended fix (1-line UPDATE in `audit_patient_read`) is documented in handoff. Track as follow-up TASK or B.18.

---

## E. Cascade soft-delete — APPROVED

| Item | Status | Note |
|------|--------|------|
| Tables cascaded: `visit`, `prescription`, `visit_vitals` | OK | Order is correct (children before parent, but actual order doesn't matter for soft-delete since FK isn't enforced — only `is_deleted` flag is set). |
| `visit_vitals` join via `visit.patient_id` | OK | UPDATE...FROM idiom correct. |
| **`audit_log` NOT cascaded** | CORRECT (intentional deviation from spec) | Spec wording "cascade soft-delete audit_log" was ambiguous. The `audit_log` table has DB-level `BEFORE UPDATE/DELETE` triggers that RAISE EXCEPTION (verified in `0002_create_audit_log.py:75`). Soft-deleting audit rows would FAIL at the trigger anyway. The implementation correctly preserves audit history for BYT 7-year compliance. |
| `patient.deleted_by`, `deleted_at` set on cascade rows | OK | Same admin_user_id and timestamp propagated to all child rows. |

**Audit log cascade verdict**: ACCEPTABLE (and correct). The deviation from spec wording is intentional and forced by both regulatory compliance (BYT 7-year audit retention) and DB triggers. The patient row is soft-deleted, but the audit trail (including the new `patient.erasure` event) remains queryable for compliance audits. No change requested.

---

## F. Permission seeding — APPROVED

| Item | Status |
|------|--------|
| `patient.erase` permission code (2-level dotted) | OK |
| Assigned to `admin` role only | OK |
| Idempotent `ON CONFLICT DO NOTHING` | OK |

---

## G. Test quality — APPROVED

| Test file | Tests | Coverage notes |
|-----------|-------|----------------|
| `test_erasure_service.py` (11) | OK | Token scoping, single-use, expired/missing/wrong/corrupted token, NotFound on already-deleted + nonexistent, audit no-PII assertion. |
| `test_erasure_endpoint.py` (9) | OK | 403 on non-admin, 200 path, 422 short reason, expired/wrong token via service-side ForbiddenError. |
| `test_pii_archive_cron.py` (8) | OK | Old patient archived, recent untouched, NULL+old created_at archived, already-deleted skipped, cron summary dict shape. |

**Suggested additions for Test phase** (non-blocking):
1. Integration test: full happy-path through `/erase/request` → `/erase` against a real test DB to verify cascade SQL semantics (currently mocked).
2. Test asserting `audit_log` row created by erasure cannot be UPDATE/DELETE'd (verifies trigger guard interaction).
3. Cron run with mixed candidates (some old, some recent, some already deleted) to verify counters.

---

## H. Compliance items (Nghị định 13) — APPROVED

| Item | Status |
|------|--------|
| Right to Erasure (Điều 16) | OK — 2-step admin confirmation; ≤30-day SLA achievable (immediate execution). |
| Audit trail preserved (admin action logged even after PII erased) | OK |
| Reason captured (admin must justify) | OK — Pydantic enforces 5-500 char reason in audit log. |

---

## I. Cross-task coordination

| Coord item | Status | Action |
|------------|--------|--------|
| TASK-037 P2 crypto-shred wiring | TRACKED | Two TODOs + 4-step wiring procedure in handoff. Clear and testable. |
| TASK-035 audit `applied_role` | NOT WIRED | This worktree predates TASK-035 merge. At merge, `write_audit("patient.erasure", ...)` will automatically pick up `applied_role` from middleware ContextVar (if TASK-035 instruments it that way). No code change required here. |
| Migration renumber across TASK-037 P2 / TASK-035 / TASK-036 / TASK-045 | TRACKED | Documented in impl handoff. |
| `audit_actions.py` constants | MINOR GAP | `patient.erasure` and `patient.pii_archive` not added to `audit_actions.py`. Recommend Test or Doc phase add them to prevent string drift (same lesson learned from B.5-B.7). |

---

## Follow-ups (non-blocking, track separately)

1. **`last_accessed_at` not updated on read** (MEDIUM): 1-liner in `audit_patient_read()` to `UPDATE patient SET last_accessed_at = now() WHERE id = :id`. Without this, cron archives based on `created_at`, which may incorrectly archive long-tenured but actively-accessed patients once data ages 7+ years. Track as B.18 or new TASK.
2. **Admin-binding of confirmation token** (LOW): Currently any admin with `patient.erase` can confirm any open token (e.g., admin A requests, admin B confirms). Stored payload already has `admin_user_id` — just check it in `_verify_and_consume_token`. Hardening only.
3. **`audit_actions.py` constants** (LOW): Add `PATIENT_ERASURE = "patient.erasure"` and `PATIENT_PII_ARCHIVE = "patient.pii_archive"` to prevent drift.
4. **`json.dumps` instead of f-string** in `pii_archive.py:183` (cosmetic): Safe today (UUID/ISO can't break out of JSON), but cleaner.

---

## Decision

**APPROVED** for handoff to Test. None of the follow-ups block testing. The implementation is production-quality modulo TASK-037 P2 wiring (already TODO-tracked) and the 1-liner `last_accessed_at` fix (functionally invisible until the first patient row turns 7 years old).
