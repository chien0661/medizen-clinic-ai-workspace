# TASK-092 — Implementation → Review Handoff

**Date:** 2026-07-20
**From:** Code Implementation Agent
**To:** Code Review Agent
**Branches:** `feature/TASK-092-superadmin-system-config` (both `clinic-cms` and `clinic-cms-web`, created from `origin/main`)

---

## What was built

Per the locked-in scope in `docs/tasks/TASK-092/refs/implementation-plan.md`, plus a handful of
audit-driven quick-win bug fixes found while reviewing the existing Super Admin screens
("rà soát" — the user's explicit request).

### 1. Backend — platform-wide `system_config` (new)

- **Migration**: `alembic/versions/0061_superadmin_system_config.py` — new `system_config` table.
  Singleton, non-tenant (**no** `clinic_id`, **no** RLS — access is gated purely by the existing
  `is_superuser` JWT-claim guard already used by every other `/superadmin/*` route). PK is
  `section` (String(50)); one JSONB `data` column per section. Seeds 4 rows:
  `feature_defaults`, `security_policy`, `email`, `system_info`.
- **Model**: `app/modules/superadmin/models.py::SystemConfig`. Deliberately **not** `__auditable__`
  — see the docstring for the reasoning (secrets live nested inside the JSONB `data` column
  alongside non-secret fields, so column-level audit redaction can't protect just the secret
  without hiding the whole section's audit trail).
- **Schemas**: `app/modules/superadmin/schemas.py` — `FeatureDefaultsSection`, `SecurityPolicySection`,
  `EmailConfigSection` (write, includes `smtp_password`) / `EmailConfigResponse` (read, masks it as
  `smtp_password_is_set: bool`), `SystemInfoSection`, `SystemConfigResponse` (all 4 + `environment`
  + `app_version`, read-only).
- **Service**: `app/modules/superadmin/service.py` — `get_system_config`, `get_feature_defaults`,
  `update_system_config(section, patch, updated_by)`. Merge semantics: `None` in the patch means
  "leave unchanged" (`exclude_unset` at the route layer + `{**current, **{k:v for k,v in patch if v
  is not None}}` merge) — same pattern as the existing `ClinicSettings._deep_merge`.
- **Routes**: `GET /superadmin/system-config`, `PUT /superadmin/system-config/{section}`. The PUT
  validates the body against the section's schema dynamically (can't use a typed route parameter
  since the schema depends on the `section` path segment), so `ValidationError` is caught manually
  and converted to a 422 — FastAPI does NOT do this automatically for a manually-called
  `model_validate()`.
- **Feature-flag wiring**: `app/core/features.py::_platform_default` is a new tier-3 fallback in
  `get_effective_features`/`get_single_feature`, inserted between the existing tier-2
  (`Clinic.bhyt_enabled` legacy column) and the hardcoded `FEATURE_REGISTRY` default. **Caveat for
  reviewers**: the legacy `bhyt_enabled` column on `Clinic` means changing the `bhyt` platform
  default will NOT affect any clinic's effective `bhyt` feature (tier 2 always shadows tier 3 for
  that one key) — this is pre-existing behavior, not something this task changed, but it's
  non-obvious and worth a second pair of eyes. The `hr` key has no such legacy column, so it's the
  one that actually exercises the new tier-3 path (see the test using `hr` instead of `bhyt`,
  documented inline).
- **Audit-fix**: `GET /superadmin/clinics` previously returned the *entire* clinic table with no
  `skip`/`limit` at all (a real gap — every other cross-tenant list endpoint in this module is
  paginated). Now takes `search`/`skip`/`limit` and returns `{items, total, skip, limit}`. This
  is a breaking response-shape change for any FE caller expecting a bare array — see FE section
  below for how each call site was updated.
- **Analytics**: `app/modules/superadmin/analytics.py` gained `avg_monthly_visits`, which was
  documented in the TASK-071 spec but missing from the implementation — found during the audit,
  fixed as a quick win.

### 2. Frontend — System Config page + nav reorg + audit fixes

- **New page**: `src/pages/superadmin/SuperAdminSystemConfigPage.tsx` — 4 tabs (feature defaults /
  security policy / email / system info), each its own `react-hook-form` + `zod` form, saved
  independently via `superAdminSystemConfigApi.update(section, patch)`. Each tab sends its **full**
  section state back on save (not a true field-level diff) — safe because the BE merge is
  idempotent for untouched fields (they're just resubmitted unchanged). The one exception: the SMTP
  password field is never pre-filled and is only included in the PUT body when the admin actually
  types something new — leaving it blank omits the key entirely so the BE's "`None` = unchanged"
  merge preserves whatever secret is already stored.
- **Sidebar reorg**: `src/components/shell/Sidebar.tsx` — `SUPERADMIN_NAV_ITEMS` (flat list) became
  `SUPERADMIN_NAV_GROUPS` (3 headed sections), matching the plan exactly:
  - **Quản lý hệ thống**: Tổng quan, Phòng khám, Thống kê, Audit Logs
  - **Tài khoản & Người dùng**: Tài khoản (the existing combined accounts+users screen)
  - **Cấu hình hệ thống**: Cấu hình hệ thống (new)

  All pre-existing `data-testid`s were preserved unchanged (`nav-superadmin-dashboard`, `-clinics`,
  `-analytics`, `-accounts`, `-audit`); a new `nav-superadmin-system-config` and per-group
  `superadmin-group-{key}` testids were added. Grep across the FE test suite confirmed no test
  references these testids by exact match other than `Sidebar.tsx` itself, so this was safe.
- **Route**: `/superadmin/system-config` added to `src/router/index.tsx`, lazy-loaded, wrapped in
  `RequireSuperuser` like every other Super Admin route.
- **`modules/superadmin/{types,api}.ts`**: added the system-config types/API client; also fixed
  `SuperAdminClinicListResponse` and `SuperAdminAuditLogListResponse` to include `total`/`skip`/`limit`
  (additive, non-breaking) and added `SuperAdminClinicListParams`.
- **Audit fix #1 — `SuperAdminClinicsPage.tsx`**: converted from loading the entire clinic table
  client-side (filtering/paginating in JS) to real server-side pagination + search, matching the
  BE fix. Note: the `filterStatus` (active/inactive) dropdown is now applied client-side **within
  the current page only**, since the BE list endpoint has no `is_active` query param — a
  known/documented limitation, not a regression (previously this filter worked across the whole
  unpaginated table; now it only filters what's on the current page). Flagged for reviewer
  judgment on whether a follow-up BE param is worth it.
- **Audit fix #2 — `SuperAdminAuditLogsPage.tsx`**: pagination previously *estimated* the total via
  a page-size heuristic (`skip + logs.length` vs `skip + pageSize + 1`) because the API response was
  believed to have no total — it does (`service.list_audit_logs` always returned `total`, the FE
  type just didn't declare it). Now uses the real `data.total`.
- **Truncation-avoidance fix**: 4 other call sites (`SuperAdminDashboardPage`,
  `SuperAdminAnalyticsPage`, `SuperAdminAuditLogsPage`'s clinic-filter dropdown, and 2 spots in
  `SuperAdminAccountsPage`) call `superAdminClinicsApi.list()` to populate a clinic **picker**
  dropdown, not a paginated table. Since the BE now defaults to `limit=50`, these were all updated
  to explicitly request `limit: 500` so a platform with >50 clinics doesn't silently truncate the
  dropdown options.

### 3. Deliberate scope decisions (see task.md Notes + implementation-plan.md)

- "Tài khoản" and "Người dùng" are **one screen**, not two — locked in at planning, not a decision
  made mid-implementation.
- No i18n was added for the new page — every existing Super Admin screen (TASK-070/071) uses
  hardcoded Vietnamese strings, not i18next. Followed the same convention for consistency.

---

## Test evidence

- **BE**: `tests/integration/test_superadmin_system_config_e2e.py` (new, 13 tests) — RBAC (403 for
  non-superuser, 401/403 unauthenticated), GET defaults-filled, `smtp_password` never echoed
  plaintext, partial-update semantics (untouched fields keep their value, not reset to schema
  defaults), 404 for unknown section, 422 for invalid enum, feature-defaults reconciliation with a
  freshly-created clinic (using `hr` not `bhyt` — see caveat above), clinics pagination + search.
  All 13 pass against the real dev Postgres (no mocks, per PROJECT.md Override #4).
- **BE full suite**: 1742 passed, 30 failed. Diffed against an `origin/main` baseline via
  `git stash` — all 30 failures are pre-existing (RLS isolation, auth lockout/MFA, RBAC seed
  integrity, email template rendering, erasure-service last-accessed-at) and unrelated to this
  task's changes; none touch `superadmin` or `system_config`.
- **FE**: new `src/tests/superadmin/SuperAdminSystemConfigPage.test.tsx` (6 tests) — loading state,
  tab switching, saving feature_defaults with a toggled checkbox (asserts the exact PUT body), the
  email tab's masked-password hint in both states, and the write-only password omission behavior.
  All pass.
- **FE full suite**: 1075 passed, 3 failed across 2 files (`ForgotPasswordPage`, `QueuePage`).
  Confirmed pre-existing via `git stash` baseline (same 2 files / 3 tests fail identically without
  this branch's changes) — unrelated to Super Admin.
- **Type-check/lint**: `tsc --noEmit` clean; `eslint` clean (`--max-warnings 0`) on every touched
  file.

## Not done / explicitly out of scope for this handoff

- Branches have **not** been pushed to origin yet, and no PR has been opened — carried over from
  earlier in this session, blocked on the user's choice between manual PR links vs setting up
  `gh auth login`/`GITHUB_TOKEN`. Not a code-review blocker, just a process step still pending.
- `maintenance_mode` and password-policy fields are stored and returned by the API but **not yet
  enforced anywhere** (no middleware gate, no wiring into the password-validation flow) — this was
  flagged as an explicit risk/optional-scope item in the implementation plan ("Phase 4 — Enforce"),
  deliberately deferred rather than silently dropped. Config is fully save/load-able; enforcement
  is a reasonable follow-up task.
- `SuperAdminClinicsPage`'s active/inactive filter is now page-scoped rather than table-wide (see
  Audit fix #1 above) — a minor UX regression traded for the bigger fix (no more loading the whole
  table). Reviewer judgment call on whether this needs a BE `is_active` query param follow-up.
