---
task: TASK-034
from: review
to: test
date: 2026-05-01
status: APPROVED_WITH_NOTES
decision: APPROVED
---

# TASK-034 Code Review → Test Handoff

**Decision: APPROVED** (proceed to testing). Two ⚠️ items should be fixed during the test cycle (i18n parity gaps + audit logging) but are not blocking. Architectural design is sound; rescue fixes are correct.

---

## A. Migration `0024_bhyt_toggle` ✅

- ✅ Schema: `clinic.bhyt_enabled BOOLEAN NOT NULL DEFAULT false` + `clinic.bhyt_facility_code VARCHAR(50) NULL` — matches B.1 exactly.
- ✅ `down_revision = "65fc9ae59ba5"` confirmed (rescue fix verified). Linear single head: `0024 → 65fc9ae59ba5 → (d07d8bfed696 + 0020b)`.
- ✅ Permission INSERT uses correct columns `(code, description, category)` with `ON CONFLICT (code) DO NOTHING` — idempotent. Rescue cleanup of `id`/`updated_at` confirmed.
- ✅ Rollback drops index → drops columns → deletes seeded permissions by code. Will not cascade to `role_permission`. Safe.
- ✅ Index `ix_clinic_bhyt_enabled` for fast flag lookups.
- ⚠️ Revision ID `"0024"` (not hash) follows pre-existing convention; alembic accepts but reduces collision safety in concurrent branches. Not a blocker — same convention as 0001-0020.

## B. `feature_flags.py` primitive ✅

- ✅ `require_feature("bhyt")` returns 404 when flag OFF; 401 when no clinic context.
- ✅ Reads `current_clinic_id` ContextVar (forward-compatible with TASK-033 multi-clinic JWT).
- ✅ Redis cache `clinic:flags:{clinic_id}:{flag}` 5-min TTL with graceful degradation on Redis failure.
- ✅ `invalidate_feature_flag_cache(clinic_id, flag=None)` supports per-flag and pattern delete.
- ✅ Unknown flag returns False (warns); clinic not found returns False (fail-safe).

## C. RBAC permission filter ⚠️

- ✅ `_apply_feature_flag_gates` strips `bhyt:*`, `vss:*`, `report.bhyt.*` when flag OFF.
- ✅ Skips DB lookup when no BHYT perms in set (fast path).
- ✅ Reuses `_cache_get_flag` / `_cache_set_flag` from feature_flags module — single source of truth for cache.
- ⚠️ **Stale-cache window**: `get_user_effective_permissions` caches the **post-gate** result at `user:perms:{user_id}` for 5 min. PATCH `/settings/bhyt` invalidates `clinic:flags:*` but **not** `user:perms:*`. After toggle, users with cached perms keep stale set up to 5 min. Mitigation: `require_feature` is the primary endpoint gate so impact is cosmetic (perm check returns False but endpoint already 404's). Recommend: add `invalidate_user_cache` loop for clinic users on toggle (follow-up).

## D. Settings endpoint ✅ / ⚠️

- ✅ `PATCH /api/v1/settings/bhyt {enabled, facility_code}` enforced via `Depends(require_permission("bhyt:config"))`.
- ✅ Pydantic validates `^[0-9]{5}[A-Z]{4}$` and requires `facility_code` when `enabled=True`; auto-clears when disabling.
- ✅ Triggers `invalidate_feature_flag_cache(clinic_id, "bhyt")`.
- ⚠️ **No audit log entry**: only `log.info("bhyt_settings_updated", ...)` to structlog. `app.core.audit.audit_write` exists and other settings should be writing to `audit_log` table for SECURITY/compliance traceability of feature toggles. Recommend follow-up to call `audit_write` with `action="settings.bhyt.toggle"`, `entity_type="clinic"`, `old_data`/`new_data`.
- ✅ GET endpoint deliberately not feature-gated (needed to bootstrap toggle UI).

## E. UI Gates (sampled 5 deeply)

| # | Area | Status | Notes |
|---|------|--------|-------|
| 1 | Settings tab "BHYT" | ✅ | Parent `RequirePermission permission="settings.clinic"` enforces admin perm; tab itself flag-gated via dynamic TABS array. BhytConfigPage doesn't add inner `bhyt:config` perm guard — relies on BE enforcement. Acceptable. |
| 5 | PatientRegisterPage BHYT card field | ✅ | `{bhytEnabled && (<div data-testid="bhyt-card-field">...)}` clean conditional render. |
| 8 | InvoiceDetailPage BHYT line | ✅ | Column header + cells gated symmetrically. Cell renders "—" placeholder (no monetary value), so total recalc is N/A — invoice grand_total is unaffected. |
| 9 | Sidebar nav | ✅ | Dynamic injection of `reports-bhyt` sub-item under Reports group when flag ON. Idempotent (`alreadyHasBhyt` check). Sub-item carries `permission: "bhyt:reports"`. Note: the spec called for "hide nav item entirely"; impl folds gates #2 + #9 into one location (sub-item under Reports). Acceptable trade-off, documented. |
| 10 | PatientDetail BHYT history tab | ✅ | DevPlaceholder ("BHYT History — BE integration pending"). Coordination with TASK-040 confirmed in handoff. |

## F. Gate #3 placement (VSS into BhytReportPage) ✅

- ✅ Pragma decision documented: keeps integrations folder small until full Integrations page exists.
- ✅ VSS panel co-located with BHYT funnel chart; both gated by route + `useFeatureFlag('bhyt')` self-gate.
- ⚠️ Trade-off (recorded for future): when standalone `IntegrationsPage` is built (likely TASK-040+ for VSS production integration), the `VssSyncPanel` component should be extracted from `BhytReportPage.tsx` into `pages/integrations/VssIntegrationPage.tsx`. Track as merge-time follow-up.

## G. Gate #7 LabOrdersTab (DEFERRED) ✅

- ✅ Component does not exist in current FE. Properly identified as blocked by TASK-033/041.
- ✅ Documented in handoff and `task.md` dependencies. Track as merge-time follow-up: when `LabOrdersTab` is created, wrap BHYT chỉ định block with `bhytEnabled && (...)`.

## H. i18n parity ⚠️

vi/en parity verified for the new BHYT namespace + nav keys per rescue fix. **However, four orphan keys consumed by gated UI are missing locale entries:**

| Key | Used in | vi | en |
|-----|---------|-----|-----|
| `services.columns.bhytPrice` | ServicesPage gate #4 | ✅ | ❌ missing |
| `medicines.filterBhyt` | MedicinesPage gate #11 | ✅ | ❌ missing |
| `billing:invoiceDetail.lines.bhytLine` | InvoiceDetailPage gate #8 | ❌ missing | ❌ missing |
| `doctor:prescription.bhytLine` + `bhytLineHint` | PrescriptionTab gate #6 | ❌ missing | ❌ missing |

Behavior: i18n falls back to printing the raw key → user sees `services.columns.bhytPrice` literal. **Fix during test cycle**: add the four keys to vi/en `admin.json`, `billing.json`, and `doctor.json` (also requires registering `billing` and `doctor` namespaces if not already loaded). Not blocking review since affected text is conditional on flag ON + flag is OFF by default.

## I. Test quality ✅

- ✅ BE 33/33: `test_feature_flags.py` (10) covers cache hit/miss, unknown flag, missing clinic context, 401/404 paths. `test_bhyt_settings.py` (5) covers Pydantic validation + 5 RBAC strip scenarios incl. cache. `test_bhyt_endpoints_gated.py` (10) covers 404-when-OFF + 200-when-ON + auth requirements.
- ✅ FE 547/547 (full suite ran clean — gate-specific tests covered in BhytConfigPage + BhytReportPage suites).
- ✅ **Negative tests present**: flag OFF behavior is the dominant test case across all three BE files. Good coverage.
- 💡 Gap (not blocking): no test exercises **the toggle transition** (flag OFF → PATCH ON → endpoint becomes 200 in same request flow). Recommend adding one e2e or integration test for the cache-invalidation correctness.

## J. Cross-cutting collisions ⚠️

- ⚠️ **Wave 3-A column encryption**: `bhyt_facility_code` is an organisational identifier (not personal PII), but VSS facility codes may be considered sensitive per Vietnamese health-insurance regulation. **Flag for SECURITY.md review** during Wave 3-A encryption planning — decide whether to include `clinic.bhyt_facility_code` in Tier-3 encrypted columns. Action: add to Wave 3-A discovery checklist.
- ⚠️ **Wave 3-B Sidebar refactor**: BHYT sub-item is currently injected under Reports group via dynamic `effectiveNavItems` mapping. When sidebar is refactored to role-grouped layout, ensure injection logic is preserved and BHYT placement is reconsidered (could move under a new Insurance/Integrations group). Track as merge-time follow-up.
- ✅ **TASK-033 multi-clinic**: forward-compatible — `current_clinic_id` ContextVar is the same name; flag column is per-clinic.

---

## Summary of Review Findings

| Severity | Count | Items |
|----------|-------|-------|
| ❌ Blocker | 0 | — |
| ⚠️ Should fix | 4 | i18n parity gaps (4 keys) · audit log entry on settings PATCH · stale user perm cache on toggle · alembic revision ID convention (cosmetic) |
| 💡 Nice-to-have | 2 | Toggle-transition e2e test · VSS panel extraction at IntegrationsPage time |

## Action Items for Test Phase

1. **i18n fix (must-do)**: Add four missing keys (`bhytPrice`, `filterBhyt`, `bhytLine`, `bhytLineHint`) to vi/en `admin.json`, `billing.json`, `doctor.json`. Verify keys render in both locales when flag ON.
2. **Audit logging (recommended)**: Wrap `update_bhyt_settings` body to call `app.core.audit.audit_write(action="settings.bhyt.toggle", entity_type="clinic", entity_id=clinic_id, old_data, new_data)`.
3. **Test scenarios for tester**:
   - Flag OFF default — visit each of the 10 wired UI areas, confirm BHYT element absent.
   - Flag toggle ON → reload → confirm 10 areas appear.
   - Flag toggle ON → call `/api/v1/bhyt/funnel` → 200; toggle OFF → 404.
   - Confirm modal: flow for both enable and disable transitions; data-preserved warning on disable.
   - Facility code regex validation — UI rejects `1234ABCD` (4 digits), `01234abcd` (lowercase), accepts `01234ABCD`.
   - Permission strip: user with `bhyt:read` cannot reach `/bhyt/funnel` when flag OFF (returns 404).
   - i18n: switch to en and revisit each gate to confirm missing keys are filled.
4. **Cache invalidation**: After PATCH, BE returns updated state but other concurrent users keep cached perms ~5 min. Document in test report (acceptable per design, primary gate is endpoint-level).
