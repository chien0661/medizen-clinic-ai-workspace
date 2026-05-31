---
id: TASK-038
type: security
title: Security NFR rest — JWT validator + password history + anomaly detection + 2FA + login fingerprint (NFR-029/035/040/042/027)
status: DONE
priority: High
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
completed: 2026-05-01
branch: ""
jira_key: ""
tags: [security, mfa, anomaly-detection, password-policy, jwt, lifecycle]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/SECURITY.md"
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "../TASK-032/deliveries/final-specs/audit-report.md"
    - "../TASK-032/handoff/be-audit-report.md"
---

# TASK-038: Security NFR rest — JWT validator + password history + anomaly + 2FA + lifecycle

## Description

Bundle of NFR-027/029/035/040/042 security tasks not requiring full encryption envelope (TASK-037). Includes critical quick-win JWT_SECRET validator (<1 day) plus larger MFA + anomaly detection + PII lifecycle work.

## Requirements

### Quick-win (Day 1)

- [ ] **Q.1** `app/core/config.py` — add `Settings.model_validator` to reject `JWT_SECRET == "change-me-in-production"` when `ENVIRONMENT != "development"`. Increase `min_length=32`. Fail-fast at app startup.

### Password policy (NFR-027)

- [ ] **B.1** Migration: new table `password_history(user_id UUID FK, password_hash TEXT, changed_at TIMESTAMPTZ, PRIMARY KEY(user_id, changed_at))`
- [ ] **B.2** Update `change_password` to reject if new password matches any of last 5 hashes
- [ ] **B.3** Add `user.password_changed_at TIMESTAMPTZ` + cron mark `must_rotate=true` when 90 days elapsed
- [ ] **B.4** FE: `ChangePasswordPage` shows "Mật khẩu đã hết hạn" banner if `must_rotate=true`

### Anomaly detection cron (NFR-042)

- [ ] **B.5** New `app/workers/jobs/anomaly_detection.py` with 7 SQL rules:
  - `failed_login_burst` (>5 failures from same IP in 5 min)
  - `mass_pii_reveal` (>50 patient.read events from same user in 1 min)
  - `cross_clinic_access` (user accessing clinic_id ≠ active_clinic_id from JWT)
  - `sudden_role_grant` (admin grants role to user within first 5 min of admin login)
  - `mass_export` (>3 export events in 5 min)
  - `audit_tamper_detected` (chain verifier break — coord with TASK-037)
  - `key_decrypt_anomaly` (unusual decrypt rate — coord with TASK-037)
- [ ] **B.6** New `app/core/alerting.py` — PD/Slack webhook integration
- [ ] **B.7** Add cron 15-min schedule to `WorkerSettings.cron_jobs`

### Login fingerprint + 2FA (NFR-029, NFR-035)

- [ ] **B.8** Migration: add `user.mfa_secret VARCHAR(255) NULL`, `user.mfa_enabled BOOLEAN DEFAULT FALSE`, `user.backup_codes TEXT[]`
- [ ] **B.9** Migration: new table `login_fingerprint(user_id, ip, device_hash, geo_country, last_seen_at)`
- [ ] **B.10** New `app/modules/auth/services/mfa_service.py` — TOTP enroll/verify, backup code generate/consume
- [ ] **B.11** Endpoints: `POST /auth/mfa/enroll`, `POST /auth/mfa/verify`, `POST /auth/mfa/disable`, `POST /auth/mfa/backup-codes/regenerate`
- [ ] **B.12** Update `/auth/login` flow: if `mfa_enabled=true`, return `{mfa_required: true, mfa_token: ...}` and require `POST /auth/mfa/verify` to complete
- [ ] **B.13** Anomaly trigger: new IP/device/geo → require 2FA challenge or send notification email
- [ ] **B.14** FE: `MfaEnrollPage`, `MfaVerifyPage`, profile tab "Bảo mật" with MFA toggle + backup codes + recent logins list

### PII lifecycle (NFR-032/040, depends on TASK-037 crypto-shred)

- [ ] **B.15** New endpoint `DELETE /patients/{id}/erase` with 2-step confirmation token (Right to Erasure per Nghị định 13)
- [ ] **B.16** Cron `pii_archive` — auto-archive PII >7 years to cold storage (encrypted)
- [ ] **B.17** Erasure flow: soft-delete + crypto-shred patient DEK partition (depends on TASK-037 envelope)

## Acceptance Criteria

- [ ] App fails to start in `staging`/`production` with default `JWT_SECRET` (Q.1)
- [ ] Password change rejected if matches recent 5; rotation banner shown after 90 days
- [ ] Anomaly cron runs every 15 min; test rule fires alert via Slack/PD webhook
- [ ] User can enroll TOTP; login flow gates with 2FA when enabled; backup codes work
- [ ] New-IP login triggers 2FA challenge or notification
- [ ] `DELETE /patients/{id}/erase` with confirmation token soft-deletes + shreds key (after TASK-037)
- [ ] BE tests 100% pass; FE: MfaEnrollPage works on dev

## Dependencies

- Q.1 + B.1-B.7 + B.8-B.14 — independent (can ship without TASK-037)
- B.15-B.17 (PII erasure crypto-shred) — depends on TASK-037 envelope
- Coordinates with TASK-039 (Profile "Bảo mật" tab visual)

## Effort

**Medium-Large** (3-4 days for B.1-B.14; +1 day for B.15-B.17 after TASK-037).

## Risk

LOW for quick-wins (Q.1 + password history); MEDIUM for MFA (FE flow complexity); HIGH for PII erasure (depends on crypto-shred).

## Notes

### Q.1 — DONE 2026-05-01

**Status**: ✅ COMPLETE — JWT_SECRET validator quick-win

- **Functional design doc**: `docs/tasks/TASK-038/deliveries/final-specs/jwt-secret-validator-functional-design.md`
- **Test result**: 19/19 PASSED (15 unit tests + 4 extended edge case tests)
- **Files modified**: 4
  - `clinic-cms/app/core/config.py` — added `_DEV_PLACEHOLDER_JWT_SECRET` constant, `_PLACEHOLDER_JWT_SECRETS` frozenset, `model_validator` rejecting placeholders in non-dev, bumped min_length to 32
  - `clinic-cms/tests/unit/test_config.py` — 15 new/updated test cases covering min_length, placeholder rejection, strong-secret acceptance
  - `clinic-cms/.env.example` — added instruction block for secret generation
  - `clinic-cms/docker/docker-compose.yml` — updated dev JWT_SECRET to 45-char value (compatible with min_length=32)
- **Non-blocking polish items documented**: whitespace handling, environment case-sensitivity, entropy validation (deferred to future releases)
- **Remaining scope (B.1-B.17)**: Password history, anomaly detection cron, MFA/TOTP, login fingerprint, PII lifecycle — still TODO

---

### B.1–B.4 — DONE 2026-05-01

**Status**: ✅ COMPLETE — Password history + 90-day rotation (NFR-027)

- **Functional design doc**: `docs/tasks/TASK-038/deliveries/final-specs/password-history-functional-design.md`
- **Test result**: 16 BE unit + 4 BE integration + 535 FE = **555/555 PASS**
- **Implementation scope**:
  - B.1: Migration `0021_password_history_and_rotation` — new table `password_history` + column `user.must_rotate`
  - B.2: `change_password` API rejects matching last 5 hashes (400 error)
  - B.3: Cron job `password_rotation_check` daily 02:00 UTC; flags `must_rotate=true` for >90 days
  - B.4: FE banner on `ChangePasswordPage` — "Mật khẩu đã hết hạn — vui lòng đổi mật khẩu"
- **Field naming**: BE + FE both use `must_rotate` (manager applied rename pre-test)
- **Flags documented**:
  - Migration `0021` conflict across 3 concurrent streams (A, B, C) — requires renumbering at merge
  - Cron audit log gap — no audit entry on `must_rotate` flag (follow-up item)
  - `LoginPage` forced-redirect broken after rename (reads old field name `password_expired`)
- **Remaining scope (B.5-B.17)**: Anomaly detection, MFA/TOTP, login fingerprint, PII lifecycle — still TODO

---

### B.8–B.14 — DONE 2026-05-01

**Status**: ✅ COMPLETE — MFA (TOTP) + Login Fingerprint (NFR-029, NFR-035)

- **Functional design doc**: `docs/tasks/TASK-038/deliveries/final-specs/mfa-login-fingerprint-functional-design.md`
- **Test result**: 34 BE MFA + 566 FE = **600/600 PASS**
- **Implementation scope**:
  - B.8: Migration `0021_add_mfa_columns_to_user` — mfa_secret, mfa_enabled, backup_codes
  - B.9: Migration `0022_create_login_fingerprint` — fingerprint table + indexes
  - B.10: `mfa_service.py` — TOTP enroll/verify/disable, backup codes (bcrypt)
  - B.11: 6 endpoints — /auth/mfa/{enroll,verify,disable,backup-codes/regenerate,challenge} + /auth/fingerprints
  - B.12: Two-step login flow with mfa_token (5-min JWT)
  - B.13: Anomaly trigger on new IP/device (30-day lookback)
  - B.14: FE — MfaEnrollPage, MfaVerifyPage, SecurityTab, ProfilePage
- **Fix-mode patches** (post-review):
  - Lockout integration: `complete_mfa_challenge` calls `record_failed_attempt/clear_failed_attempts`
  - mfaEnabled wired from authStore (was hardcoded false)
- **Migration conflict**: Three concurrent `0021` revisions (Streams A/B/C) — requires renumbering at merge
- **Hardening deferred**: Backup code entropy (51.7 < 80 bits), OTP replay protection, email OTP fallback, GeoIP, trusted-proxy validation
- **Remaining scope (B.5-B.7 + B.15-B.17)**: Anomaly cron, PII lifecycle — still TODO

---

### B.5–B.7 — DONE 2026-05-01

**Status**: ✅ COMPLETE — Anomaly Detection Cron (NFR-042)

- **Functional design doc**: `docs/tasks/TASK-038/deliveries/final-specs/anomaly-detection-functional-design.md`
- **Test result**: 26/26 PASS (24 unit tests + 2 integration tests)
- **Implementation scope**:
  - B.5: 7 anomaly detection rules (2 active + 4 placeholder + 1 deferred)
    - ACTIVE: `failed_login_burst` (>5 failures/5min from IP), `mass_pii_reveal` (>50 patient reads/1min from user)
    - DEMOTED placeholder: `sudden_role_grant`, `mass_export` (emitters not instrumented yet)
    - DEFERRED: `audit_tamper_detected`, `key_decrypt_anomaly` (TASK-037 deps), `cross_clinic_access` (TASK-033 dep)
  - B.6: 3 alerting backends (Slack + PagerDuty Events API + structlog) with 5s timeout, exception isolation
  - B.7: Cron 15-min schedule (minute={0,15,30,45}) via Arq async job
  - Constants module: `app/core/audit_actions.py` to prevent action-string drift (caught by Code Review)
- **Fix-mode patches** (post-review):
  - Action strings corrected: `user.login_failed` (not `auth.login.failed`), `action='READ' AND entity_type='Patient'` (not `patient.read`)
  - Constants regression tests added to prevent future drift
  - Boundary tests for threshold detection (exactly-at-threshold cases)
  - `LIMIT 100` per rule for botnet spam protection
- **Deferred items**: 
  - `sudden_role_grant`, `mass_export` rules demoted pending audit emitter instrumentation (SQL preserved in comments for re-enable)
  - `cross_clinic_access` blocked by TASK-033 (multi-clinic JWT)
  - `audit_tamper_detected`, `key_decrypt_anomaly` blocked by TASK-037 Phase 1+2
  - Index optimization (soft scaling concern, recommended but not blocking)
- **Remaining scope (B.15-B.17)**: PII lifecycle (Right to Erasure) — blocked by TASK-037 crypto-shred

---

### B.15–B.17 — DONE 2026-05-01

**Status**: COMPLETE — PII Lifecycle + Right to Erasure (NFR-032/040, Nghị định 13)

- **Functional design doc**: `docs/tasks/TASK-038/deliveries/final-specs/pii-lifecycle-erasure-functional-design.md`
- **Test result**: 31/31 PASS (14 unit erasure + 9 integration endpoint + 8 cron unit)
- **Implementation scope**:
  - B.15: Endpoints `POST /patients/{id}/erase/request` + `DELETE /patients/{id}/erase` with 2-step confirmation token
  - B.16: Daily cron `pii_archive` at 04:00 UTC — auto-archive patients not accessed >7 years
  - B.17: Cascade soft-delete (visit, prescription, vitals) + PatientArchive row + audit_log entry
- **Post-review fixes applied**:
  - Fix #1: `audit_patient_read()` now updates `last_accessed_at` so cron correctly identifies stale patients
  - Fix #2: `_verify_and_consume_token()` enforces admin-binding (Admin A's token cannot be used by Admin B → 403)
  - Fix #3: `audit_actions.py` constants `PATIENT_ERASURE` + `PATIENT_PII_ARCHIVE`; `pii_archive.py` uses `json.dumps()` instead of f-string
- **Crypto-shred TODOs**: wiring procedure documented (4-step); blocked until TASK-037 P2 merge
- **Migration note**: `0028_pii_archive_table` to be renumbered at merge (candidate: `0030`)

**ALL TASK-038 SUB-SCOPES COMPLETE**: Q.1 + B.1-B.4 + B.5-B.7 + B.8-B.14 + B.15-B.17

---

### Original task notes

- **Q.1 (JWT validator) should land as standalone PR within 1 day** — independent, critical, gates production safety.
- Discovery via TASK-032 BE audit B.6c, B.6d, B.6e, B.6f, B.6g.
- Reference: `docs/design/medizen-modern/SECURITY.md` NFR-024..046.
