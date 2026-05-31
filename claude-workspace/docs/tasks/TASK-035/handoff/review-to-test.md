# TASK-035 — Code Review → Test Handoff

**Date**: 2026-05-01
**Reviewer**: Code Review Agent
**Branches**: BE `feature/task-035-multi-role` (worktree `clinic-cms-w3b`) / FE `feature/task-035-multi-role-fe` (worktree `clinic-cms-web-w3b`)
**Decision**: **CHANGES_REQUESTED** (4 medium issues + 2 acceptance-criteria gaps; cross-cutting collisions OK)
**Source**: `../handoff/impl-to-review.md` (note: lives under root `docs/tasks/TASK-035/` not `claude-workspace/docs/tasks/`).

---

## Decision Summary

| Item | State |
|---|---|
| BE migration `0026_audit_applied_role` | OK |
| BE audit listener captures `applied_role` | OK with style nit |
| BE SoD framework + 2 endpoints applied | OK (1 deferred — stocktake) |
| BE `/users/{id}/roles` includes `assigned_at` | OK |
| FE Sidebar multi-role grouping | OK |
| FE Topbar role chip + `+N` badge | OK |
| FE applied_role context indicator (F.5/F.6) | MISSING — gap |
| FE multi-role default landing (F.7) | MISSING — gap |
| Cross-cutting (audit hash chain, encryption, TASK-040, TASK-033) | Acknowledged + handled |
| Test coverage breakdown | Light on negative paths |

Implementation is functionally solid; the migration / listener / SoD / sidebar / topbar are correct. **Two acceptance criteria from the task are not implemented on FE** and **negative SoD integration tests are absent**, hence CHANGES_REQUESTED before testing phase.

---

## A. Migration `0026_audit_applied_role` — OK

- `revision = "0026_audit_applied_role"`, `down_revision = "0021_multi_clinic_account"` (verified — `0021` head exists with parent `65fc9ae59ba5`). Linear chain valid.
- Adds `audit_log.applied_role VARCHAR(50) NULL` + composite index `(applied_role, created_at)` for compliance queries.
- Both upgrade + downgrade reversible.
- **Conflict with Wave 2-A (TASK-037)**: confirmed additive — `0022` adds `prev_hash/row_hash/chain_seq`; `0026` adds `applied_role`. Different columns, no overlap. Order does not strictly matter at the DDL level, but per impl handoff Note 3 the recommended order is **0026 before 0022** so that `fn_audit_row_data_json()` (created in 0022) can be authored to include `applied_role` from day 1. **Verified**: TASK-037 phase-1 fix-mode addendum already placed a `TODO Wave 3-B merge` comment in `fn_audit_row_data_json()` to add `applied_role` once both branches merge. Merge plan documented on both sides.

⚠ **Merge-time follow-up (must not be lost)**: after both branches land, a new migration must re-create `fn_audit_row_data_json()` to include `applied_role` in the canonical JSON, then re-backfill `row_hash`. Tracked in TASK-037 handoff §"applied_role hash gap deferred + tracked".

## B. Audit listener `app/core/audit.py` — OK with nit

- ✅ `current_applied_role` ContextVar imported from `app.core.tenancy`.
- ✅ Both `write_audit` (async) and `_write_audit_sync` read `applied_role` and pass it to `AuditLog(...)` constructor — verified at lines 183/200 and 283/295.
- ✅ Model `AuditLog.applied_role` field declared `Mapped[str | None]` matches DB column.
- ⚠ **Style nit (non-blocking)**: `app/core/tenancy.py:219` uses `if 'claims' in dir():` to test whether the JWT path was taken. Functionally correct (Python's `dir()` with no args returns local names) but unconventional. Prefer `if 'claims' in locals():` or — cleaner — initialize `claims: dict | None = None` above the auth branches and check `if claims is not None`. Not a bug; readability only.

## C. SoD framework `app/core/sod.py` — OK with caveats

- ✅ `check_no_self_approval(record, record_creator_field)` — service-layer inline helper with HTTP 403 + structured `{code: SOD_VIOLATION, message, field}` detail.
- ✅ `make_sod_dep(get_record, ...)` — FastAPI dep factory for endpoints with literal `record_id` path param.
- ⚠ `require_no_self_approval(...)` defined but raises `NotImplementedError` — dead code. Either implement properly or delete. Mild API confusion: docstring at top suggests this is the public entry point, but only `check_no_self_approval` and `make_sod_dep` are used.
- **Endpoints applied**:
  1. ✅ `add_payment` (billing/services/payment_service.py:88) — `await check_no_self_approval(invoice, "created_by")` after `_get_invoice_for_update` (correctly inside the row-locked tx).
  2. ✅ `dispense_prescription` (pharmacy/api/routes.py:127–129) — loads Prescription via `db.get`, checks SoD before dispense.
  3. ❌ `stocktake_approve` — **DEFERRED**, no endpoint exists in codebase. Acceptable per impl handoff §"Note on stocktake_approve".

⚠ **Negative integration tests for SoD missing.** Unit tests cover the helper logic (8/8 PASS) but no integration test asserts:
- `POST /api/v1/invoices/{id}/payments` returns 403 with `code=SOD_VIOLATION` when current user equals `invoice.created_by`.
- `POST /api/v1/pharmacy/dispense/{id}` returns 403 when current user equals `prescription.created_by`.

These should be added before testing phase signs off — ACs explicitly require "test verifies 403".

## D. `/users/{id}/roles` schema — OK

- ✅ `UserRoleResponse` schema (`user_schemas.py:114`) adds `assigned_at: datetime | None = None` (optional for backward compat).
- ✅ `list_user_roles` route handler (routes.py:200) joins `UserRole` + `Role`, populates `assigned_at=ur.assigned_at`.
- ✅ `assign_role` route also populates `assigned_at=ur.assigned_at`.
- ✅ 4 schema-builder tests verify presence + serialization.
- ⚠ Tests are pure schema/builder; no end-to-end test calling the actual endpoint with auth. Acceptable for this task scope.

## E. FE Sidebar refactor — OK

- ✅ `src/lib/rbac.ts` — `ROLE_NAV_SECTIONS`, `groupNavByRole`, `isMultiRole`, `getPrimaryRole`, `getAllNavSections` all clean + typed.
- ✅ Sidebar single-role renders default `NAV_ITEMS` order (no dividers) — `data-testid="sidebar-single-role"` exposed.
- ✅ Sidebar multi-role: shared (dashboard, notifications, settings) at top, then per-role sections wrapped in `<div data-testid="role-section-{role}">` with `RoleDivider` before each.
- ✅ `RoleDivider` returns null when collapsed (correct UX).
- ✅ 6 tests: 3 single-role (testid, no dividers, sidebar-single-role), 3 multi-role (testid, role-section-doctor, role-section-admin, dividers count ≥2).
- **Conflict with TASK-040 Phase D**: TASK-040 (pharmacy stocktake/expiry) added page routes only, **no new top-level nav items in Sidebar**. Existing `pharmacy` section subItems unchanged in TASK-040 branch. **No merge collision**.

## F. FE Topbar role chip — OK

- ✅ Avatar button renders initials + `topbar-primary-role-chip` (translated label) + `topbar-multi-role-badge` (`+N` where N = `roles.length - 1`).
- ✅ Multi-role dropdown header lists all roles in `topbar-roles-list` block with translated labels.
- ✅ `data-testid` attributes match impl handoff.
- ✅ 6 tests cover single (3) / multi (2) / no-roles (1).
- **Conflict with TASK-033 ClinicSwitcher**: ClinicSwitcher rendered in `<div className="flex-1 min-w-0">` taking left-side flex space; right-side controls (notifications, lang, theme, role chip) in a separate flex group with `gap-2`. Avatar button has `gap-1.5`. **No overlap** — visually independent. Order: [ClinicSwitcher] [OnlineStatus] [Notifications] [Lang] [Theme] [Avatar+RoleChip+Badge]. Acceptable.

## G. FE applied_role context indicator — ❌ NOT IMPLEMENTED

Task requirements F.5/F.6 ask:
- Sidebar nav click sets `applied_role` in store
- `X-Applied-Role` header sent on outgoing requests

**Search of FE code found zero references** to `appliedRole`, `applied_role`, or `X-Applied-Role` outside the rbac.ts comment. The BE listener correctly **reads** the header (tenancy.py:216) and falls back to first JWT role, so audit log capture **does work end-to-end** as long as the FE is happy with the JWT-fallback default. But the explicit user-controlled "I'm acting as role X right now" affordance is missing.

**Recommendation**: Either
1. Implement: add `appliedRole` to `authStore`, set it on nav click within a role section, add an axios interceptor to inject `X-Applied-Role`, OR
2. Document in handoff that F.5/F.6 are **deferred** with explicit acceptance — currently the spec suggests this is in scope.

## H. Multi-role default landing — ❌ NOT IMPLEMENTED

Requirement F.7: `/dashboard/multi-role` route or fallback. Search found no such route. Multi-role users land on the existing `/dashboard`. This may be acceptable as the "fallback to /dashboard" branch of the spec, but the impl handoff is silent. **Document expected behavior** in test cases.

## I. i18n `shell.roles.*` — OK

- vi: 7 role labels (admin, doctor, receptionist, pharmacist, nurse, accountant, hr_manager) + `unknown`, `assignedAt`, `rolesLabel`, `primaryRole`, `moreRoles`.
- en: identical key set.
- Both files synchronized — no key drift.

## J. Test coverage breakdown

- **BE: 15/15 PASS**
  - `test_sod.py` — 8 (TestCheckNoSelfApproval ×6 + TestMakeSodDep ×2)
  - `test_audit_applied_role.py` — 3 (sync capture, sync none, async capture)
  - `test_user_roles_endpoint.py` — 4 (schema ×3 + builder ×1)
- **FE: 580/580 PASS** (53 test files), TS clean, lint clean.
  - Sidebar-multi-role — 6
  - Topbar-role-chip — 6
  - Other 568 are pre-existing (TASK-017..033) + regression coverage retained.
- ⚠ **Negative integration tests missing** for SoD on real endpoints (see §C). Recommend test agent add at least 2 e2e scenarios.

## K. Cross-cutting collisions — Reviewed

| Wave / Task | Shared resource | State |
|---|---|---|
| Wave 2-A TASK-037 (hash chain) | `audit_log` table | ✅ Additive only. TASK-037 has TODO comment for `applied_role` — merge follow-up migration required (see §A). |
| Wave 3-A column encryption | `applied_role` text | ✅ Not PII, must NOT be encrypted. Implementation stores plain VARCHAR — correct. |
| Wave 2-C / TASK-040 (pharmacy stocktake/expiry) | Sidebar pharmacy nav-items | ✅ TASK-040 added page routes only; no nav-item additions. No `ROLE_NAV_SECTIONS` change needed at merge. |
| TASK-033 (ClinicSwitcher) | Topbar layout | ✅ Coexists. Order: ClinicSwitcher (left) → controls + Avatar (right). No overlap. |

## Required Changes Before Testing Phase

1. **Add SoD integration tests** for `add_payment` (creator-vs-payer 403) and `dispense_prescription` (creator-vs-dispenser 403). Acceptance criteria explicitly require these.
2. **Decide F.5/F.6 (applied_role context indicator)**: implement OR document deferral with rationale + follow-up task ID.
3. **Decide F.7 (multi-role landing)**: implement `/dashboard/multi-role` OR document that "fall back to `/dashboard`" is the chosen behavior.
4. **Cleanup**: delete or implement the dead `require_no_self_approval(...)` function in `sod.py` (currently raises `NotImplementedError`).

## Optional / Style

- **tenancy.py:219** — replace `'claims' in dir()` with `'claims' in locals()` or initialize `claims = None` upfront.
- **Topbar hover popover with `assigned_at`** — currently dropdown lists role names only (impl handoff §Known Gap #2). Consider follow-up enhancement once user roles API is wired into a hook.

## Sign-off

- BE migration / listener / SoD framework / endpoints / schema: **APPROVED** subject to integration tests (§C) and dead-code cleanup (§C).
- FE Sidebar / Topbar / i18n: **APPROVED**.
- FE F.5/F.6/F.7: **NOT IMPLEMENTED** — must be resolved (implement or document deferral) before testing phase signs the task DONE.

→ **Returning to Implementation** for items 1–4 above. Re-submit when complete.
