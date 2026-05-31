# BE Audit Report — TASK-032

**Date**: 2026-05-01
**Auditor**: BE Audit Agent
**Codebase**: `clinic-cms` (FastAPI 0.115 + Postgres + Redis + Arq, Python 3.11)
**Compared against**: function list v1.3 + `docs/design/medizen-modern/SECURITY.md`
**Focus areas**: AUTH-018..022, CFG-017, RX-016, NAV-001..008, RBAC-015..018, NFR-005..046

---

## Executive Summary

- **Multi-clinic per account architecture is entirely missing.** `User` is hard-bound to a single `clinic_id` via `BaseEntity.TenantMixin` (FK NOT NULL). Login still demands a `clinic_code` parameter. No `account_clinic_role` pivot, no `select-clinic` endpoint, no JWT rotation on switch. This is the largest single gap and blocks AUTH-018..022, NAV-002, RBAC-017, RBAC-018.
- **No BHYT toggle anywhere.** `Clinic` model and `clinic_settings` schema have zero `bhyt_enabled` field, no feature-flag middleware, no `bhyt:*` permissions seeded. Scope of CFG-017 = full new feature.
- **Six entire modules referenced in the brief don't exist:** `services`, `prescriptions/medicines`, `inventory`, `billing/invoices`, `reports`, `notifications`. The brief's claim that these were built in TASK-001..016 is incorrect — only `auth, users, admin, audit, patients, appointments, visits, vitals, hr` exist on disk. RX-016 stock-chip, AR-aging, full-page notifications, PO/stocktake/expired endpoints — all impossible to evaluate because the host modules were never implemented.
- **Cross-table Cmd+K search API does not exist.** Only `/api/v1/patients/search` exists (single entity, name/phone/code only — no fuzzy/trigram, no permission-aware multi-entity union).
- **CRITICAL security gaps**: zero column-level encryption (no `cryptography`/`Fernet`/`pgcrypto` import, no envelope/DEK/KEK code), audit log has **no hash chain** (no `prev_hash` column, no SHA256 chain, no verifier), no anomaly-detection cron, no PII lifecycle job, JWT is HS256 with default `change-me-in-production` secret allowed by `Field(min_length=8)`. Bcrypt cost 12 — verified OK.

Estimated overall completion of v1.3 spec: **~25%** (foundation + 9 of ~25 modules); **~10%** of new design-phase additions (NFR security depth + multi-clinic + new APIs).

---

## Gap Inventory

### B.1 — Multi-clinic per account schema (AUTH-018..022)

- **Current state**:
  - `app/modules/users/models/user.py` (lines 14, 25-50): `User` extends `BaseEntity`, which via `TenantMixin` (`app/core/base_model.py:66-74`) forces `clinic_id: UUID NOT NULL FK→clinic.id`. One user row = one clinic. Email is `nullable=True` and **NOT** unique-globally; the `username` is the auth identity, scoped to clinic.
  - Login (`app/modules/auth/services/auth_service.py:51-176`) requires `clinic_code` in the request (line 78), looks up clinic, then loads user by `(clinic_id, username)` pair. Failure paths go through `_get_clinic_by_code` first.
  - JWT (`app/core/security.py:49-103`) embeds `clinic_id` once at issuance. There is no `active_clinic_id` claim because there is no concept of multiple memberships.
  - Auth routes (`app/modules/auth/api/routes.py:47-180`): only `/login`, `/refresh`, `/logout`, `/change-password`. No `/auth/clinics`, no `POST /auth/select-clinic`, no `PATCH /auth/clinics/{id}/default`.
  - No `account_clinic_role` (or `user_clinic_role`) pivot table anywhere — verified by grepping all of `app/` and `alembic/versions/` for `account_clinic|user_clinic|active_clinic|select.clinic`. Only matches are `clinic_role_exists` (an error string) and `Clinic.code` lookups.
  - Migrations through `0016_create_clinic_settings.py` show single-tenant `user.clinic_id` FK only.
  - Login response (`auth_service.login` returns lines 167-176) returns a single `user` object with `roles + permissions` arrays — no `clinics: [{id, name, role, is_default}]` array.
- **Spec requires**: AUTH-018 pivot `account_clinic_role(account_id, clinic_id, roles[], is_default, granted_at, granted_by)`; AUTH-019 default-clinic flag; AUTH-020 auto-resolve post-login (1 → auto, default → load, multiple no default → return list); AUTH-021 switch-clinic flow + JWT revoke + reissue with new `clinic_id+roles+perms`; AUTH-022 last-active clinic in Redis `user:last_clinic:{uid}`.
- **Gap**: **CRITICAL**
- **Effort**: **Large** (multi-week)
- **Files to touch**: new model `app/modules/users/models/account_clinic_role.py`; rewrite `User` to drop `TenantMixin` (or split User → Account + ClinicMembership); new Alembic migration to backfill pivot from existing user rows + add `account.email UNIQUE`; new auth endpoints in `auth/api/routes.py`; rewrite `auth_service.login` + `refresh` to support clinic-list response and clinic-selection flow; extend JWT claims + `TenancyMiddleware` (`app/core/tenancy.py:118-220`) to handle `active_clinic_id` claim; rewrite `rbac_service.get_user_effective_permissions` to filter by `(user_id, active_clinic_id)`; Redis cache key needs to include `clinic_id`.
- **Migration risk**: **HIGH** — touches every existing user row, every JWT in flight, every RBAC query (Redis cache key `user:perms:{user_id}` is wrong shape for multi-clinic), and every `current_clinic_id` call site (~50+ usages across modules).

---

### B.2 — BHYT toggle (CFG-017)

- **Current state**:
  - `Clinic` model (`app/modules/users/models/clinic.py:16-39`): no `bhyt_enabled` column. Has `code, name, specialty, address, phone, email, tax_code, is_active, settings (JSONB)`. No insurance / BHYT-related field.
  - `ClinicSettings` JSONB schema (`app/modules/admin/schemas/settings_schemas.py`) groups: `operating_hours, appointment, queue, inventory, prescription, billing, specialty`. No `bhyt` group, no `insurance` group.
  - `app/modules/admin/services/default_settings.py:77-118` — defaults dict has no BHYT key.
  - No middleware or dependency that gates `/bhyt/*`, `/integrations/vss/*`, `/reports/bhyt/*`. Those route prefixes do not exist (verified — no `bhyt` matches in `app/`).
  - `bhyt:read` / `bhyt:write` permissions are NOT seeded (no matches in `0007_seed_permissions_and_roles.py`).
- **Spec requires**: CFG-017 — `clinic.bhyt_enabled BOOLEAN DEFAULT FALSE`; when OFF, hide all BHYT routes (404), strip BHYT permissions from effective set, hide BHYT columns/fields; when ON, require Mã cơ sở KCB.
- **Gap**: **MAJOR** (blocks BHYT module + all reports/integrations downstream)
- **Effort**: **Small** for the flag + middleware; **Large** if you also have to build the BHYT module itself (out of TASK-032 scope).
- **Files to touch**: Alembic migration to add `clinic.bhyt_enabled BOOLEAN NOT NULL DEFAULT false` + `clinic.bhyt_facility_code VARCHAR(50)`; update `Clinic` model; new dependency `app/core/feature_flags.py` returning 404 for disabled features; adjust `rbac_service.get_user_effective_permissions` to short-circuit `bhyt:*` perms when flag OFF; add seed BHYT permissions; settings schema additions.
- **Migration risk**: **LOW** (additive boolean default false)

---

### B.3 — Stock chip API (RX-016)

- **Current state**:
  - There is **no** `medicines` or `inventory` or `prescriptions` module. Verified: `ls app/modules/` returns only `admin, appointments, audit, auth, hr, patients, users, visits, vitals`.
  - No `GET /medicines/{id}/stock-summary` or any medicine endpoint. No `PrescriptionItem`, no `InventoryLot`, no `StockMovement` models exist.
- **Spec requires**: RX-016 — real-time stock chip in Rx form: `{available_qty, lot_count, earliest_expiry, status: ok|low|out}` per medicine, FEFO-aware, with substitute suggestion.
- **Gap**: **CRITICAL — endpoint missing entirely** (the entire host module is missing)
- **Effort**: **Large** (depends on TASK-011/012 inventory module being delivered first)
- **Files to touch**: new `app/modules/medicines/`, `app/modules/inventory/` (lots, movements, FEFO query), `app/modules/prescriptions/` modules, plus migrations.
- **Migration risk**: **NONE for the API**, but huge for the host modules (new schema).

---

### B.4 — Cmd+K Global Search API (NAV-001..008)

- **Current state**:
  - The only search endpoint is `GET /api/v1/patients/search` (`app/modules/patients/api/routes.py:91-108`):
    - Single-entity (patients only).
    - `q` + `type ∈ {phone, name, code}` — no fuzzy/trigram/unaccent visible in route signature. (Service layer uses ILIKE per other code patterns; no `pg_trgm` extension setup visible in migrations.)
    - Permission gate: `patient.read` only — no cross-entity permission union.
  - No `/api/v1/search` global endpoint. No `/api/v1/search?q=...&mode=bn|thuoc|inv|rx|lk` route. No "recent items" persistence, no permission-filtered union across patients/medicines/invoices/prescriptions/visits.
- **Spec requires**: NAV-001 cross-entity command palette; NAV-003 `/bn` patient subsearch (fuzzy unaccent + trigram on name/code/phone/CCCD/BHYT); NAV-004 `/thuoc` medicine search with stock+price chip; NAV-005 feature/route fuzzy search with recency boost; NAV-008 breadcrumb (FE only — already ✅ per fn list).
- **Gap**: **MAJOR — endpoint missing entirely**
- **Effort**: **Medium** (one new module; depends on B.3 medicine module existing)
- **Files to touch**: new `app/modules/search/` module with permission-aware multi-table query; needs `pg_trgm` + `unaccent` extensions enabled in a new migration; index DDL for trigram on patient.full_name, patient.phone, patient.id_number, medicine.name, medicine.active_ingredient.
- **Migration risk**: **LOW** (extensions + indexes, no destructive changes)

---

### B.5 — Multi-role permissions union (RBAC-015..018)

- **Current state**:
  - `rbac_service.get_user_effective_permissions` (`app/modules/users/services/rbac_service.py:92-150`) **already correctly returns the union** of all role permissions ∪ extra_grants − extra_denies. JWT embedding (`auth_service.login:147-153`) sends `role_codes` (plural) and `permissions` (full effective set). This is **NOT an anti-pattern** — the data shape is correct.
  - HOWEVER:
    - **RBAC-015 (`applied_role` in audit)**: `AuditLog` model (`app/modules/audit/models/audit_log.py`) has no `applied_role` column. Multi-role users have no provenance of which role authorized a given action. NOT IMPLEMENTED.
    - **RBAC-016 (Separation of Duties)**: no SoD checks anywhere. `permissions.py:require_permission` does a single permission check; doesn't know about "user must not be both proposer and approver of same record".
    - **RBAC-017 (Merge sidebar)**: FE concern, but BE must surface enough info — currently login returns `roles: list[str]` and `permissions: list[str]`, which is sufficient. ✅ on BE side.
    - **RBAC-018 (Multi-role chip)**: needs `roles_with_grant_dates` — current `UserRoleResponse` has `assigned_at` per the model (`user_role.py:48-53`), but the listing endpoint `/users/{id}/roles` does not return it (see `users/api/routes.py:194-209`). Easy fix.
  - Cache key (`rbac_service.py:41-69`): `user:perms:{user_id}` — does NOT include clinic_id. Once multi-clinic (B.1) lands, this key shape causes cross-clinic permission leakage unless changed. **Flag this as a B.1 dependency.**
- **Spec requires**: RBAC-015..018 as above.
- **Gap**: union itself = **MINOR** (already done); applied_role + SoD = **MAJOR**
- **Effort**: **Medium**
- **Files to touch**: add `applied_role` column to `audit_log` (migration + model + service); SoD framework in `app/core/permissions.py` (e.g. `require_no_self_approval(record_creator_field=...)`); update `/users/{id}/roles` listing schema to include `assigned_at`; rework Redis cache key when B.1 lands.
- **Migration risk**: **LOW** (additive column)

---

### B.6 — Security NFR-005..046

This is multi-finding — broken into sub-areas.

#### B.6a — NFR-024 / NFR-025 Column-level encryption + per-tenant DEK + master KEK

- **Current state**: **ZERO encryption code.** Grep across `app/` for `EncryptedString|pgp_sym_encrypt|Fernet|cryptography\.|envelope|crypto.shred|AES|kek|dek|master.key` returns **no results**. PII columns stored as plain `String`/`Text`:
  - `Patient.full_name`, `phone`, `email`, `id_number` (CCCD), `address_line`, `ward`, `district`, `province`, `allergies`, `chronic_conditions`, `notes` — all plaintext (`app/modules/patients/models/patient.py:33-60`).
  - `User.full_name`, `email`, `phone`, `license_number` — plaintext (`app/modules/users/models/user.py:31-50`).
  - `Clinic.tax_code`, `email`, `phone`, `address` — plaintext.
  - No BHYT card field exists yet (see B.2) but spec calls it Tier 3 PII requiring envelope.
  - `pyproject.toml` deps: `python-jose[cryptography]>=3.3` is listed (cryptography is transitive dep) but `cryptography` is not directly used by app code. `pgcrypto` extension not enabled in any migration.
- **Spec requires**: NFR-024 AES-256 column-level on Tier-3 fields with envelope (per-field DEK random, DEK encrypted by per-tenant master KEK in KMS); NFR-025 per-tenant key isolation, crypto-shred on tenant deletion.
- **Gap**: **CRITICAL** — no encryption at rest beyond whatever the storage backend provides.
- **Effort**: **Large** (requires KMS choice — Vault vs AWS KMS; SQLAlchemy TypeDecorator; migration to encrypt existing rows)
- **Files to touch**: new `app/core/crypto/` package (KMS client, envelope helpers, `EncryptedString` SQLAlchemy type); new `tenant_key_metadata` table; tenant onboarding service to mint DEK; data-migration to re-encrypt existing rows.
- **Migration risk**: **HIGH** (touches every PII row; data corruption risk; needs offline maintenance window)

#### B.6b — NFR-031/§7.1 Hash-chain audit log

- **Current state**: `app/modules/audit/models/audit_log.py:24-85` — `AuditLog` has fields `id, clinic_id, user_id, request_id, action, entity_type, entity_id, old_data, new_data, changed_fields, ip_address, user_agent, created_at`. **No `prev_hash`, no `row_hash`, no `chain_seq`.** No verifier function. No DB trigger for chain computation. Migration `0002_create_audit_log.py` enforces append-only via `BEFORE UPDATE/DELETE → RAISE EXCEPTION` triggers, which is good for tamper-evidence at the "no row mutation" level, but does not detect **insertion** of forged rows or row deletion via `TRUNCATE`/superuser bypass.
- **Spec requires**: §7.1 each row `hash = SHA256(prev_hash || row_data)`; verifier service that walks chain and reports breaks (NFR-044); alert rule `audit_tamper_detected`.
- **Gap**: **CRITICAL** (compliance — BYT 7-year audit retention requires tamper evidence)
- **Effort**: **Medium**
- **Files to touch**: migration to add `prev_hash`, `row_hash`, `chain_seq` columns + composite index; insert trigger to compute chain server-side OR in `audit.py` write path; new `app/modules/audit/services/chain_verifier.py`; admin endpoint `POST /admin/audit/verify-chain`.
- **Migration risk**: **MEDIUM** (existing rows need backfill — chain can be initialized from `created_at, id` ordering; risk = pause writes during backfill)

#### B.6c — NFR-042 Anomaly detection cron

- **Current state**: `app/workers/scheduler.py:25-32` — Arq has only `noop` + `generate_recurring_shifts` cron. No anomaly detection job. No rules engine. No paging integration.
- **Spec requires**: NFR-042 — 15-minute job with 7 rules: `failed_login_burst, mass_pii_reveal, cross_clinic_access, sudden_role_grant, mass_export, audit_tamper_detected, key_decrypt_anomaly` → PD/Slack alert.
- **Gap**: **MAJOR**
- **Effort**: **Medium**
- **Files to touch**: new `app/workers/jobs/anomaly_detection.py` (7 SQL rules over `audit_log`); new `app/core/alerting.py` (PD/Slack webhook); add cron to `WorkerSettings.cron_jobs`.
- **Migration risk**: **NONE** (read-only over audit_log)

#### B.6d — NFR-032 / §3.3 PII lifecycle + crypto-shred

- **Current state**: No tenant deletion flow that destroys per-tenant DEK (DEK doesn't exist — see B.6a). No 7-year auto-archive cron. No "Right to Erasure" endpoint per Nghị định 13. Soft-delete exists but no hard-delete + key-shred sequence. No cold-storage encryption setup.
- **Spec requires**: NFR-032 patient erasure → soft delete + crypto-shred + audit + 2-step confirm; §3.3 crypto-shred procedure.
- **Gap**: **MAJOR**
- **Effort**: **Medium** (depends on B.6a)
- **Files to touch**: new `app/modules/admin/services/erasure_service.py`, new `app/workers/jobs/pii_archive.py`, endpoint `DELETE /patients/{id}/erase` with 2-step confirmation token.
- **Migration risk**: **LOW** for endpoint; **HIGH** for actually shredding production data.

#### B.6e — NFR-027 Bcrypt cost 12

- **Current state**: `app/core/security.py:23-30` — `_BCRYPT_ROUNDS = 12`, `bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)`. **CORRECT** — meets spec. Note: spec asks for "cost ≥12" plus "history of 5 last passwords" + "rotation 90 days". History/rotation NOT implemented (`change_password` at `auth_service.py:326-360` overwrites without history).
- **Spec requires**: NFR-027 cost ≥12 ✅; pepper optional; history 5; 90-day rotation.
- **Gap**: cost = ✅; history + rotation = **MINOR**
- **Effort**: **Small**
- **Files to touch**: new `password_history` table + check in `change_password`; cron to mark `password_changed_at + 90d > now → must_rotate=true`.
- **Migration risk**: **LOW**

#### B.6f — NFR-005 / NFR-040 / NFR-042 (Secret management, JWT)

- **Current state**:
  - `app/core/config.py:21` — `JWT_SECRET: str = Field(default="change-me-in-production", min_length=8)`. The default IS `"change-me-in-production"` and `min_length=8` would accept it as valid. **No startup check** that the secret is not the default in non-dev environments.
  - `JWT_ALGORITHM: str = "HS256"` — symmetric. Spec NFR-028 wants RS256 + JWKS rotation (v2). Acceptable for v1.
  - No Vault/AWS Secrets Manager integration. `.env` file consumption only.
  - TLS/HSTS — not enforced at app level (deployment concern).
- **Gap**: default-secret risk = **CRITICAL** in production; secret manager integration = **MINOR (v2)**.
- **Effort**: **Small** for the fail-fast check.
- **Files to touch**: add `Settings.model_validator` to reject default `JWT_SECRET` when `ENVIRONMENT != "development"`.
- **Migration risk**: **NONE**

#### B.6g — NFR-029/NFR-035 Login anomaly + 2FA

- **Current state**: `app/modules/auth/services/lockout_service.py` exists for failed-attempt lockout (good). But:
  - No device fingerprint, no IP-change detection (NFR-029).
  - No 2FA / MFA at all — `User` model has no `mfa_secret`, `backup_codes` columns. No `/auth/mfa/*` routes.
  - No geo-anomaly trigger.
- **Gap**: 2FA infrastructure absent = **MAJOR** (spec lists at NFR-029/§4.2 columns + NFR-024 lists `MFA secret` as Tier-3).
- **Effort**: **Large** (TOTP + backup codes + UI flow)
- **Files to touch**: new `app/modules/auth/services/mfa_service.py`, columns on user, new endpoints.
- **Migration risk**: **LOW** (additive)

---

### B.7 — Notifications full-page API

- **Current state**: There is **no `notifications` module**. `ls app/modules/` confirms absence. No `GET /notifications`, no `POST /notifications/mark-read`, no `notification` table.
- **Spec requires**: NOTI-001..007 — bell icon dropdown + full-page list with `?type=&date=&unread=` filters, bulk mark-read, categories Info/Warning/Critical/Success, visit-completion notify, low-stock alert, subscription-expiring alert.
- **Gap**: **CRITICAL — module missing entirely** (was supposedly TASK-015, not delivered)
- **Effort**: **Medium**
- **Files to touch**: new `app/modules/notifications/` (model + routes + service + Arq job for fan-out).
- **Migration risk**: **NONE** (new tables only)

---

### B.8 — AR Aging report API

- **Current state**: No `app/modules/reports/` and no `app/modules/billing/` modules. No `Invoice`, `Payment`, `AccountReceivable` model. No `GET /reports/ar-aging` endpoint.
- **Spec requires**: AR aging buckets 0-30 / 31-60 / 61-90 / >90 by clinic, per-patient breakdown.
- **Gap**: **CRITICAL — module missing entirely** (depends on billing module that doesn't exist)
- **Effort**: **Large** (depends on billing module being built first)
- **Files to touch**: new `app/modules/billing/`, `app/modules/reports/`.
- **Migration risk**: **NONE** for reports; new schema for billing.

---

### B.9 — Pharmacy sub-features API (PO / Stocktake / Expired)

- **Current state**: No `app/modules/inventory/` exists. The function-list mentions MED-008 FEFO suggestion + MED-010 Stock adjustment as TASK-012 (`docs/clinic_management_function_list.md:293,295`) but neither is implemented. No `purchase_order`, `stocktake_session`, `inventory_disposal` tables exist.
- **Spec requires**: `POST /inventory/po`, `POST /inventory/stocktake` (3-step wizard backend), `GET /inventory/expired?days=` + `POST /inventory/expired/disposal`.
- **Gap**: **CRITICAL — module missing entirely**
- **Effort**: **Large**
- **Files to touch**: new `app/modules/inventory/` with full CRUD for PO, lots, stocktake sessions, disposal records.
- **Migration risk**: **NONE** (greenfield)

---

## Cross-cutting findings

1. **The brief overstates BE completeness.** It lists modules through "billing, HR, reports, notifications" as built. On disk only `auth, users, admin (clinic+settings+onboarding), audit, patients, appointments, visits, vitals, hr` exist. Six of the named modules don't exist at all. Many gaps in B.3, B.7, B.8, B.9 are not "wrong shape" but "module missing entirely" — verify TASK-011..015 status before scheduling fixes.
2. **Single-tenant assumption is baked in deep.** `BaseEntity → TenantMixin → clinic_id NOT NULL FK` is on every business entity. The Redis cache key `user:perms:{user_id}` (no clinic), the JWT shape (single `clinic_id`), the middleware ContextVar (`current_clinic_id` set once per request), and `require_permission` all assume a fixed clinic. Adding multi-clinic (B.1) is not just a new table — it touches the contract of every downstream endpoint.
3. **Encryption + audit chain are coupled.** `audit_log.old_data/new_data` JSONB stores PII verbatim (just with `password_hash → "***"`). Once column encryption (B.6a) lands, the audit listener's `_model_to_dict` (`app/core/audit.py:117-135`) will write encrypted bytes, defeating its purpose. The audit envelope key (SECURITY.md §2.2.2 — separate "audit-specific envelope key") must be designed alongside B.6a, not after.
4. **No feature flags primitive.** B.2 (BHYT toggle) is the canary — there is currently no generic feature-flag dependency. Building a small `app/core/feature_flags.py` once (e.g. `Depends(require_feature("bhyt"))`) avoids duplicating the pattern for each future toggle (NAV-006 recents, NFR-029 fingerprinting, etc.).
5. **JWT default secret + HS256 + dev-mode unsigned tokens.** `tenancy.py:62-80` accepts unsigned JWT in development env — fine. But config default `change-me-in-production` is never validated against env. Combined with `min_length=8` (a "p@ssw0rd" is acceptable!) this is a foot-gun for the first prod deploy.

---

## Security risk highlights (escalate now)

| Risk | Severity | Reference |
|---|---|---|
| `JWT_SECRET` default value `change-me-in-production` accepted in any env | **CRITICAL** | B.6f |
| Audit log has no hash chain — superuser can rewrite history undetected | **CRITICAL** | B.6b |
| All PII (patient name, phone, CCCD, address, allergies) stored plaintext in DB | **CRITICAL** | B.6a |
| No anomaly detection — mass_pii_reveal / cross_clinic_access never alerted | **HIGH** | B.6c |
| RLS bypass possible if app DB role is superuser (only WARNED, not blocked — see `db_security.py:46-60`) | **HIGH** | observed |
| No 2FA option for clinic admins | **MEDIUM** | B.6g |
| No PII redaction in structlog (NFR-030) — phones/emails logged verbatim if developers add log statements | **MEDIUM** | not implemented |

---

## Recommended cluster sub-tasks

Ordered by dependency — earlier clusters unlock later ones.

**Cluster 1 — Multi-clinic foundation (blocks ALL future work touching auth/RBAC)**
Scope: B.1 (AUTH-018..022). Schema migration + auth flow rewrite + JWT shape change + RBAC cache key change. Largest single risk — do first or commit to single-clinic forever.

**Cluster 2 — Security hardening, phase 1 (no schema change)**
Scope: B.6f (JWT secret validator), B.6b (audit hash chain), B.6e (password history+rotation), partial B.6c (anomaly detection without crypto-related rules). Can land in parallel with Cluster 1 because it's mostly additive columns + new code.

**Cluster 3 — Encryption envelope + crypto-shred**
Scope: B.6a (column encryption + KMS), B.6d (PII lifecycle + Right to Erasure), update audit envelope (per cross-cutting #3). Depends on Cluster 1 (per-tenant DEK needs proper "tenant" identity model).

**Cluster 4 — Missing host modules (services, prescriptions/medicines, inventory, billing, notifications, reports)**
Scope: build the modules referenced in B.3, B.7, B.8, B.9. This is genuinely TASK-011..015 scope rather than TASK-032 — flag back to PM that the brief's claim "BE built in TASK-001..016" needs ground-truthing. Can be split per module.

**Cluster 5 — BHYT toggle + feature flag primitive**
Scope: B.2. Build `app/core/feature_flags.py` first, then apply to BHYT. Add seed permissions. Trivially small once Cluster 4's billing/prescription modules exist (they're the consumers).

**Cluster 6 — Cmd+K global search**
Scope: B.4 (NAV-001..005). Requires `pg_trgm + unaccent` extensions, indexes on patient/medicine columns, permission-aware union query. Depends on Cluster 4 (medicine module needs to exist).

**Cluster 7 — Multi-role UX completeness**
Scope: B.5 (RBAC-015 applied_role audit + RBAC-016 SoD framework + RBAC-018 grant-date in role listing). Small. Depends on Cluster 1 (audit + JWT need multi-clinic-aware role context).

**Cluster 8 — 2FA / MFA + login anomaly fingerprinting**
Scope: B.6g (NFR-029, NFR-035 portion). Independent from others; can be scheduled whenever capacity allows.
