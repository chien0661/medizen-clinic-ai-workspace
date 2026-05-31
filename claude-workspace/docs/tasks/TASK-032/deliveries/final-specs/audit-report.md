# Audit Report — TASK-032 (Phase C synthesis)

**Date**: 2026-05-01
**Synthesizer**: TASK-032 Manager
**Inputs**:
- `handoff/fe-audit-report.md` (FE audit — clinic-cms-web)
- `handoff/be-audit-report.md` (BE audit — clinic-cms)
**Compared against**: MediZen Modern design (45 Stitch screens, TASK-027/029/031) + function list v1.3 + SECURITY.md NFR-024..046

---

## Executive Summary (must-read)

**Convergence status: ~25%.** Code shipped through TASK-001..026 represents an MVP-level single-clinic foundation. The design phase (TASK-027..031) introduced major architectural shifts that the codebase has not absorbed. Specifically:

1. **Multi-clinic per account is not implemented** in either FE or BE. The single-tenant assumption is baked into `BaseEntity.TenantMixin`, the JWT shape, the Redis cache key, the AuthStore, the Login form, and ~50 call sites that read `current_clinic_id`. **This is the largest single gap and blocks ~half of the other gaps.**

2. **BE audit branch mismatch — CORRECTED 2026-05-01**: Initial BE audit reported 6 modules missing (`services`, `prescriptions/medicines`, `inventory`, `billing`, `reports`, `notifications`). **Investigation revealed the audit was run against branch `feature/task-006-settings`**, which legitimately doesn't have those modules. The modules **DO exist** on later feature branches (verified on `feature/task-015-reports`: billing, inventory, notifications, prescriptions, pharmacy, reports — all present). **Action**: TASK-041 scope reduced from "fresh build" (10-15 days) to "branch consolidation/merge into a unified main + integration testing" (2-5 days). See TASK-041 task.md updated scope.

3. **Critical security gaps**:
   - **JWT_SECRET default `change-me-in-production` accepted in any environment** — fail-fast validator missing.
   - **Audit log has no hash chain** — superuser can rewrite history undetected (compliance violation: BYT 7-year audit retention).
   - **All PII (Patient name/phone/CCCD/address/allergies) stored plaintext.** No envelope encryption, no per-tenant DEK, no master KEK, no `pgcrypto` extension.
   - No anomaly detection, no 2FA, no PII lifecycle/crypto-shred.

4. **Design system off-spec.** FE Tailwind tokens are "VISSoft blue" with Segoe UI font and no radius tokens. Brand string is still "CURA" / "Clinic CMS". Zero visual conformance with the 45 Stitch screens.

5. **45 Stitch screens not ported.** FE Phase D screens missing or stubbed: ForgotPassword, PatientDetail (8-tab + AI + 3-col), QueueKanban (5-col), BHYT report tab, Profile (5-tab), AR-Aging, Notifications full-page, Pharmacy 4-sub (Catalog/PO/Stocktake/Expiry).

---

## Gap inventory — consolidated

| ID | Area | FE gap | BE gap | Severity | Effort | Cluster |
|----|------|--------|--------|----------|--------|---------|
| **G-01** | Multi-clinic per account (AUTH-018..022) | A.3: login has clinic_code field, no ClinicSelector, no Topbar switcher, no Profile multi-clinic tab, AuthStore single-tenant | B.1: User has FK clinic_id NOT NULL, no account_clinic_role pivot, no /auth/select-clinic, JWT single clinic claim | **CRITICAL** | Large | **TASK-033** |
| **G-02** | BHYT toggle (CFG-017) | A.5: zero references to bhyt anywhere; 11 UI areas missing gates; no BhytConfigPage; no BhytReportPage | B.2: no `clinic.bhyt_enabled` column, no feature-flag middleware, no bhyt:* permissions seeded | **MAJOR** (CRITICAL on FE side as missing surface) | Medium-Large | **TASK-034** |
| **G-03** | Multi-role merge sidebar (RBAC-015..018) | A.4: flat NAV_ITEMS no role grouping, no avatar role chip, no applied_role | B.5: union perms ✓ already done; missing `applied_role` audit column, no SoD framework, role-listing missing assigned_at | MAJOR | Small-Medium | **TASK-035** |
| **G-04** | Cmd+K palette + global search (NAV-001..008) | A.6: no CommandPalette modal, no global keyboard handler, no Breadcrumb component | B.4: only `/patients/search` exists (single entity), no fuzzy/trigram, no permission-aware union, no `/api/v1/search` | **CRITICAL** | Medium | **TASK-036** |
| **G-05** | Column encryption + hash chain audit (NFR-024/025/031) | n/a | B.6a: zero encryption code, all PII plaintext; B.6b: audit_log no prev_hash/row_hash/chain_seq, no verifier | **CRITICAL** (compliance) | Large | **TASK-037** |
| **G-06** | Anomaly detection + PII lifecycle + 2FA (NFR-029/035/040/042) | n/a | B.6c: no anomaly cron; B.6d: no PII lifecycle/crypto-shred; B.6f: JWT default secret risk; B.6g: no MFA; B.6e: no password history/rotation | MAJOR + CRITICAL (JWT secret) | Medium-Large | **TASK-038** |
| **G-07** | Design system port + brand rename | A.1: tokens off-spec (no Indigo/Slate/Emerald, no radii, wrong fonts); brand "CURA" / "Clinic CMS" still everywhere; A.2: Sidebar bg slate-900 not Indigo accent | n/a | **CRITICAL** (visual conformance) | Medium | **TASK-039** |
| **G-08** | Phase D screens port | A.9: 8 screens missing/stubbed (ForgotPassword, PatientDetail 8-tab+3col, QueueKanban 5-col, BhytReport, Profile 5-tab, ARAging, Notifications full, Pharmacy stocktake+expiry); A.10: i18n vi/en gaps for 45 screens | n/a (FE-only) | MAJOR (CRITICAL for individual missing screens) | Large | **TASK-040** |
| **G-09** | Missing host modules (medicines, inventory, billing, notifications, reports, services) | n/a | B.3: no medicines/inventory/prescriptions modules; B.7: no notifications module; B.8: no billing/reports modules; B.9: no inventory PO/stocktake/expired | **CRITICAL** (blocks RX-016, AR-aging, NOTI-*, MED-*, INV-*) | Very Large | **TASK-041** |
| **G-10** | EMR 8-tab refactor + RX-016 stock chip enhancement | A.7: stock chip 2-state only (no amber/sắp hết, no HSD warning, no tooltip lots, no substitute button); A.8: only 4 tabs (need 6-8 incl SOAP/Diagnosis/CLS/Summary/AI/BHYT history) | dependent on TASK-041 medicine module FEFO + lot model | MAJOR | Large | **TASK-042** |

---

## Dependency graph

```
              TASK-033 (Multi-clinic)            TASK-039 (Design system)
                       │                                  │
            ┌──────────┼─────────┬──────────┐    ┌────────┼──────────┬─────────┐
            ▼          ▼         ▼          ▼    │        ▼          ▼         ▼
       TASK-035   TASK-037   TASK-041   TASK-038 │    TASK-040    TASK-034   TASK-035
       (Multi-   (Encrypt   (Missing   (Anomaly  │    (Phase D    (BHYT      (Multi-role
        role)     +chain)    modules)   +MFA)    │     screens)   toggle)     UX)
                       │         │                │                │
                       └────┬────┘                │                │
                            ▼                     │                │
                       TASK-038                   │                │
                       (NFR rest)                 │                │
                                                  │                │
                            TASK-041 ─────► TASK-042 (EMR + RX-016)
                                       └─► TASK-036 (Cmd+K search)
                                       └─► TASK-034 (BHYT — needs Rx/Invoice consumers)
```

**Critical-path order**:
1. **TASK-033 (Multi-clinic foundation)** — blocks RBAC cache key, every endpoint's `current_clinic_id`, JWT shape. Do first or commit to single-clinic forever.
2. **TASK-037 (Encryption + hash chain)** — depends on per-tenant identity (TASK-033) but partial NFRs (JWT validator, password history) can ship in parallel.
3. **TASK-041 (Missing host modules)** — unblocks RX-016, AR-aging, notifications, BHYT consumers, Cmd+K search.
4. **TASK-039 (Design system port)** — independent; can run in parallel with all BE work.
5. **TASK-040 + TASK-034 + TASK-035 + TASK-036 + TASK-042** — depend on combinations of the above.
6. **TASK-038 (Anomaly + MFA + lifecycle)** — independent except PII lifecycle which depends on TASK-037 crypto-shred.

---

## Cross-cutting findings (carried from FE+BE audits)

1. **Single-tenant assumption is baked in deep.** Touches: BaseEntity TenantMixin, Redis cache key `user:perms:{user_id}`, JWT `clinic_id` claim, TenancyMiddleware ContextVar, `require_permission`, AuthStore scalar `clinicId/clinicCode`, all React-Query keys. TASK-033 is not "add a table" — it's a contract change for every downstream endpoint.

2. **Encryption + audit chain are coupled.** `audit_log.old_data/new_data` JSONB stores PII verbatim. Once column encryption (TASK-037) lands, the audit listener writes encrypted bytes, defeating the audit purpose. Audit envelope key (separate from data envelope per SECURITY.md §2.2.2) must be designed alongside, not after.

3. **No feature-flag primitive exists.** TASK-034 (BHYT toggle) is the canary — build a generic `app/core/feature_flags.py` once (e.g. `Depends(require_feature("bhyt"))`) so TASK-038 (anomaly toggles), future telehealth/emergency gates can reuse.

4. **No global keyboard layer on FE.** TASK-036 (CommandPalette), shortcut cheatsheet, future `Esc-to-close`/`Ctrl+S` all need a single `useGlobalShortcuts` hook + provider mounted at AppShell level.

5. **Brand identity drift.** Code references "CURA" + "Clinic CMS" + "VISSoft blue" simultaneously. New spec calls for "MediZen" + Indigo. Global rename + asset swap needed alongside token migration (TASK-039).

6. **The brief overstates BE completeness.** 6 modules don't exist that brief assumes. Before scheduling TASK-041, **verify with PM** whether TASK-011..015 should be retroactively re-opened or whether TASK-041 is a new build. This is a schedule/scope question for the user.

---

## Security risk highlights (escalate now)

| Risk | Severity | Reference |
|------|----------|-----------|
| `JWT_SECRET` default `change-me-in-production` accepted in any env | **CRITICAL** | TASK-038 (B.6f) |
| Audit log has no hash chain — superuser can rewrite history undetected | **CRITICAL** | TASK-037 (B.6b) |
| All PII (patient name/phone/CCCD/address/allergies) stored plaintext | **CRITICAL** | TASK-037 (B.6a) |
| No anomaly detection — mass_pii_reveal, cross_clinic_access never alerted | **HIGH** | TASK-038 (B.6c) |
| RLS bypass possible if app DB role is superuser (only WARNED) | **HIGH** | observed in `db_security.py:46-60` |
| No 2FA option for clinic admins | **MEDIUM** | TASK-038 (B.6g) |
| No PII redaction in structlog (NFR-030) — phones/emails logged verbatim | **MEDIUM** | not implemented |

**Action**: TASK-038 must include a startup `JWT_SECRET` validator as a quick-win first commit, independent of the larger MFA/anomaly work. Land in <1 day.

---

## Sub-task list (10 sub-tasks)

| Task ID | Title | Repos | Effort | Priority | Depends on | Stop-and-ask? |
|---------|-------|-------|--------|----------|------------|---------------|
| TASK-033 | Multi-clinic per account (AUTH-018..022) — schema migration + auth flow + JWT shape + RBAC cache | clinic-cms, clinic-cms-web | Large (3-5 days) | **Highest** | none | **YES** — schema migration of existing user rows; JWT contract change |
| TASK-034 | BHYT toggle wiring (CFG-017) — feature flag primitive + 11 UI gates + BhytConfigPage + BhytReportPage | clinic-cms, clinic-cms-web | Medium-Large (2 days) | High | TASK-033, TASK-039, TASK-041 | No |
| TASK-035 | Multi-role merge sidebar UX (RBAC-015..018) + applied_role audit + SoD framework | clinic-cms, clinic-cms-web | Small-Medium (1 day) | High | TASK-033 | No |
| TASK-036 | Cmd+K Quick Search (NAV-001..008) — BE search API + FE palette + breadcrumb + global shortcuts | clinic-cms, clinic-cms-web | Medium (2 days) | Medium | TASK-041 (medicine module), TASK-039 | No |
| TASK-037 | Security NFR depth — column encryption + envelope/DEK/KEK + hash chain audit + PII lifecycle | clinic-cms | Large (5-7 days) | **Highest** (compliance) | TASK-033 | **YES** — KMS provider choice + data migration to encrypt existing rows |
| TASK-038 | Security NFR rest — JWT validator + password history + anomaly detection + 2FA + login fingerprint | clinic-cms | Medium-Large (3-4 days) | High | partial: JWT validator independent | Partial — 2FA is additive (no), but anomaly cron rules need user signoff |
| TASK-039 | MediZen Modern design system port — Tailwind tokens + Indigo brand + fonts + brand rename "CURA"→"MediZen" | clinic-cms-web | Medium (2-3 days) | **Highest** (visual blocker) | none | No |
| TASK-040 | Phase D screens port — ForgotPassword + PatientDetail 8-tab + QueueKanban 5-col + Profile 5-tab + ARAging + Notifications full + Pharmacy 2 sub | clinic-cms-web | Large (5-7 days) | Medium | TASK-039, TASK-033, TASK-041 | No |
| TASK-041 | Branch consolidation — merge medicines/inventory/billing/notifications/prescriptions/reports/pharmacy from feature branches | clinic-cms | **Medium** (2-5 days, revised from "Very Large") | High | TASK-033 (multi-clinic foundation) — order: merge feature branches first, then refactor for multi-clinic | YES — merge strategy + conflict resolution; verify all modules align with v1.3 fn list |
| TASK-042 | EMR 8-tab refactor + RX-016 stock chip 3-state + lot tooltip + substitute suggest | clinic-cms-web (+ BE small) | Large (3 days) | Medium | TASK-041 (medicine FEFO), TASK-034 (BHYT history tab) | No |

**Total estimated effort**: 35-50 days for solo dev at full focus (~2-3 months realistic). Aligns with original task estimate (27-39 days) but adjusted upward for TASK-041 (not in original — discovered during BE audit).

---

## Acceptance criteria for TASK-032 close

Per `task.md`:
- [x] Báo cáo audit FE + BE đầy đủ (≥30 gaps documented) — **DONE** (10 clusters, ~55 individual gap items across FE+BE reports)
- [x] Tối thiểu 6 sub-tasks (TASK-033..038) — **DONE** (10 sub-tasks created: TASK-033..042)
- [x] Mỗi sub-task có rõ priority + estimated effort + dependencies — **DONE** (table above + per-task task.md)
- [ ] Sub-tasks complete được ít nhất 50% — **PENDING Phase D** (paused for user decision)
- [ ] Codebase post-implementation pass — **PENDING Phase D**
- [ ] Documentation cập nhật — **PENDING Phase D**

---

## Recommendation to user (decision needed before Phase D)

Three choices for Phase D execution:

### Option 1 — **Critical-path sequential** (recommended)
Run sub-tasks in dependency order, gating each through full `/complete-task` workflow:
```
TASK-039 (design system, parallel-startable) ║
                                              ║
TASK-033 (multi-clinic) → TASK-037 (encryption) → TASK-041 (host modules)
                                                       ↓
                                                   TASK-034 + TASK-036 + TASK-042
                                                       ↓
                                                   TASK-040 (Phase D screens)
                                                       ↓
                                                   TASK-035 + TASK-038 (in parallel)
```
**Pro**: respects dependencies, lowest churn risk.
**Con**: ~10 weeks calendar time before all sub-tasks done.

### Option 2 — **Parallel tracks** (if multiple devs)
Track A (BE foundation): TASK-033 → TASK-037 → TASK-041
Track B (FE design): TASK-039 → TASK-040
Track C (security additive): TASK-038 (JWT validator first as <1 day quick-win)
Then converge on TASK-034/035/036/042.
**Pro**: ~6 weeks calendar.
**Con**: requires sync points; not feasible solo.

### Option 3 — **Slice and ship MVP+** (pragmatic)
Pick top 3 sub-tasks user cares about, run full /complete-task on each, defer rest:
- e.g. TASK-039 (visual conformance — quickest user-visible win)
- TASK-038 partial (JWT secret validator + password history — security quick-wins, ~1 day)
- TASK-033 (multi-clinic — unblocks everything else later)
Defer TASK-037/041 to a separate quarter if not blocked by go-live compliance.
**Pro**: real shippable progress in 1-2 weeks.
**Con**: TASK-032 acceptance criterion "≥50% sub-tasks complete" not met → close as PARTIAL or re-scope.

---

**Decision points for user** (please confirm before Phase D starts):

1. **Which option (1/2/3)?**
2. **TASK-041 scope confirmation** — modules exist on feature branches (task-010..015). Confirm strategy: (a) full merge to main first then run TASK-033 refactor on top, OR (b) refactor each feature branch for multi-clinic individually then merge.
3. **KMS choice for TASK-037** — Vault, AWS KMS, or local-dev pgcrypto stub for now?
4. **Maintenance window for encryption migration** — ok to take ~30 min downtime to re-encrypt PII rows, or need online migration strategy?
5. **JWT secret validator** — ok to land as standalone <1 day commit immediately, ahead of TASK-038?

---

**End of audit-report.md (Phase C synthesis)**
