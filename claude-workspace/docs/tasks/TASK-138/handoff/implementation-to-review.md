# Handoff: TASK-138 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW

## Summary

Implemented both TASK-138 extensions on top of the TASK-128 payroll engine and TASK-127 attendance/shift data, per `docs/tasks/TASK-138/refs/implementation-plan.md`:

1. **Two new pay types** on `staff_profile.pay_type`: `per_session` (lương theo buổi — `session_rate × attendance_worked_days` from the TASK-127 `AttendanceDay` grid, half-day = 0.5, no grid data = 0 buổi) and `per_shift` (lương theo ca — `shift_rate × completed_shifts`, only `Shift.status='completed'`). Neither earns overtime.
2. **Per-staff commission override**: `commission_rule.staff_id` (nullable FK) lets a clinic configure a rate for one staff member that overrides the clinic-wide rate for that service_type/medicine; resolve order is staff-specific → clinic-wide → none.

Both repos (`clinic-cms`, `clinic-cms-web`) were changed, on feature branch `feature/TASK-138-payroll-session-shift`, worktrees `_feat138-be` / `_feat138-web`.

## Files Changed

### Backend (`_feat138-be`, commit `16061b4`)

- `alembic/versions/0077_payroll_session_shift_staff_commission.py` (new): widens `staff_profile.pay_type` String(10)→String(20); adds `staff_profile.session_rate`/`shift_rate` Numeric(15,2); adds `commission_rule.staff_id` (nullable FK → `staff_profile.id`, ON DELETE CASCADE) + `ix_commission_rule_staff_id`; drops and recreates the two 0073 partial unique indexes with a `COALESCE(staff_id, zero-uuid)` dimension so a clinic-wide rule and per-staff overrides coexist without violating uniqueness. Downgrade reverses all of the above. **Verified** against a throwaway Postgres container: full `alembic upgrade head` from scratch (0001→0077), `downgrade -1`, re-`upgrade head`, and inspected the resulting `\d` / `pg_indexes` output — matches the design exactly (see Test Results).
- `app/modules/hr/models/staff_profile.py`: `pay_type` → `String(20)`; added `session_rate`, `shift_rate` columns + docstring update.
- `app/modules/hr/models/commission_rule.py`: added `staff_id` column + docstring (LOCKED DECISIONS + uniqueness doc updated for migration 0077).
- `app/modules/hr/schemas/staff_schemas.py`: `PayType` literal now `monthly | hourly | per_session | per_shift`; `session_rate`/`shift_rate` added to Create/Update/Response.
- `app/modules/hr/schemas/hr_schemas.py`: `TimesheetEntry.completed_shifts`; `Payslip.session_rate`/`shift_rate`/`completed_shifts`; `CommissionRuleCreate`/`Response` gain `staff_id`.
- `app/modules/hr/services/timesheet_service.py`: added `completed_shifts` aggregate (count of `Shift.status='completed'` per staff in the period).
- `app/modules/hr/services/payroll_service.py`:
  - `_compute_one` gains `per_session`/`per_shift` branches (guard: rate ≤ 0 → `None`, same convention as existing monthly/hourly); OT forced to 0 for both; `worked_days` for `per_session` always uses the raw attendance-grid count (never the legacy Shift/TimeLog fallback — per locked decision, "no grid data → 0 buổi").
  - `_empty_slip` updated to compute the same `worked_days`/rate fields for commission-only `per_session` staff.
  - **Fixed a latent bug this migration would have introduced**: `_compute_and_record_clawback`'s rate-loading query now explicitly filters `CommissionRule.staff_id.is_(None)` — without this, a per-staff override row for the same `service_type_id` would silently overwrite the clinic-wide rate in the claw-back dict (plain dict assignment, last-wins), corrupting claw-back amounts. Claw-back intentionally stays on the clinic-wide rate only (per implementation-plan.md "Risks").
- `app/modules/hr/services/commission_service.py`: added `resolve_service_type_rate`/`resolve_medicine_rate` (pure functions, staff-specific → clinic-wide → `None`); `_load_rates` now returns a `_RateMaps` dataclass split into clinic-wide + per-staff maps; `aggregate_commission` takes optional `staff_service_type_rates`/`staff_medicine_rates` params (default `{}`, fully backward compatible); **the medicine loop no longer short-circuits when `medicine_rate` is falsy** — previously `if medicine_rate: ...` skipped the whole loop, which would have hidden a staff-specific medicine rate configured without any clinic-wide one.
- `app/modules/hr/services/commission_config_service.py`: `create_commission_rule` accepts optional `staff_id` (duplicate pre-check now scoped by `staff_id` too, mirroring the partial-index's NULL-safe uniqueness); `list_commission_rules` accepts an optional `staff_id` filter (default: return everything, general + overrides).
- `app/modules/hr/api/routes.py`: `GET /hr/commission-rules` gains optional `?staff_id=` query param; `POST /hr/commission-rules` passes `body.staff_id` through.
- Tests: `tests/unit/test_payroll_logic.py` (+18 tests: per_session/per_shift happy path, half-day, no-grid-data=0, zero-rate=None, no-OT, allowance/late-penalty still apply, monthly/hourly regression unaffected by new rate fields), `tests/unit/test_payroll_commission_kpi_clawback.py` (+1 test for `_empty_slip` per_session), `tests/unit/test_commission_service.py` (+13 tests: `resolve_service_type_rate`/`resolve_medicine_rate` precedence, `aggregate_commission` with per-staff overrides, regression without overrides, medicine override without a clinic-wide rate).

### Frontend (`_feat138-web`, commit `21866ce`)

- `src/modules/hr/types.ts`: `PayType` → 4 values; `SalaryConfig`/`StaffProfile`/`StaffProfileCreate` gain `session_rate`/`shift_rate`; `TimesheetEntry.completed_shifts`; `Payslip.session_rate`/`shift_rate`/`completed_shifts`; `CommissionRule(Create).staff_id`.
- `src/modules/hr/api.ts`: `listCommissionRules` accepts an optional `{ staff_id }` filter.
- `src/pages/hr/StaffFormPage.tsx`: pay_type select adds "Theo buổi (ngày công)" / "Theo ca" with their own rate inputs; overtime multiplier field hidden for both (no OT); a short inline hint per pay type ("buổi" = attendance grid tick; "ca" = only completed shifts).
- `src/pages/hr/PayrollPage.tsx`: `PAY_TYPE_LABEL` hardcoded map replaced with i18n keys (`hr:payroll.payType.*`, both `vi`/`en`); the "Công / Giờ" column now renders `"N buổi × đơn giá"` / `"N ca × đơn giá"` for the two new pay types (traceable breakdown per AC), unchanged for monthly/hourly.
- `src/pages/hr/CommissionKpiConfigPage.tsx`: new "Chiết khấu riêng theo nhân sự" section (`data-testid="staff-commission-section"`) — a `StaffPicker` (from `staff_profile`, not `user` list, per locked decision) selects a staff, then a table shows each service_type's override rate next to the clinic-wide fallback rate, plus a medicine override row; create/edit reuses the existing rate modal (now passing `staff_id` through); a delete action reverts to the fallback. **Fixed a latent bug**: the general table/medicine card now filter to `staff_id == null` rules only — the list endpoint returns both clinic-wide and per-staff rows now, and without this filter a per-staff override for the same service_type would have silently replaced what the general table shows.
- `src/locales/{vi,en}/hr.json`: new `payroll.payType.*` (4 keys) + `payroll.unitBreakdown.*` (3 keys) — verified present in both files by the existing generic key-parity test (`i18n-hr.test.ts`) plus 2 new targeted assertions.
- Tests: `src/tests/hr/StaffFormPage.test.tsx` (new file, 5 tests — no test existed for this page before), `src/tests/hr/PayrollPage.test.tsx` (+3), `src/tests/hr/CommissionKpiConfigPage.test.tsx` (+4), `src/tests/hr/i18n-hr.test.ts` (+2).

## Test Results

**Backend** (`docker run --rm -e ENVIRONMENT=development -v .../_feat138-be:/work -w /work clinic_e2e-api python -m pytest tests/unit -q`):
- **1109 passed, 12 failed** — the 12 failures are pre-existing on clean `dev` (verified by running the identical command against `_dev-be`: same 12 failures, 1084 passed there). All 25 new/modified TASK-138 tests pass; **zero new failures**.
- `ruff check` clean on all changed BE files (2 issues found and fixed during implementation: a `B008`-style Query-in-default noqa comment, an unused test variable).
- `mypy app/modules/hr` — 0 new errors (pre-existing errors are all in unrelated `app/core/*` files, missing third-party stubs).
- Migration verified end-to-end against a throwaway Postgres container (not the shared `clinic_e2e_postgres`, to avoid disturbing that stack): fresh `alembic upgrade head` (0001→0077) succeeds, `downgrade -1` succeeds, re-`upgrade head` succeeds; inspected `\d staff_profile`/`\d commission_rule`/`pg_indexes` — schema matches the design exactly (column widths, new columns, new FK, both rebuilt partial unique indexes with the COALESCE sentinel).

**Frontend** (`npx vitest run`):
- **1257 passed, 3 failed** (full suite) — the 3 failures (`QueuePage` × 2, `ForgotPasswordPage` × 1) are pre-existing on clean `dev` (verified: identical 3 failures, 1243 passed there). Zero new failures. (The 4th pre-existing flaky failure mentioned in the task brief, `AttendanceWidget`, didn't trigger in either run.)
- `npm run type-check` (`tsc --noEmit`) — clean, no errors.
- `eslint` on all changed files — clean.

## Areas for Review Focus

1. **`per_session` worked_days semantics** (`payroll_service.py` line ~88): I deliberately made `per_session` use the raw attendance-grid count even when `has_attendance_data` is `False` (i.e., it never falls back to the legacy Shift/TimeLog-derived count), per the locked decision "per_session bắt buộc dùng attendance grid; không có dữ liệu grid → 0 công". Worth double-checking this reading of the plan is what's intended — the alternative (falling back like monthly does) would let a `per_session` staff earn from stale Shift data instead of the attendance grid, which seemed wrong given the plan's explicit wording.
2. **Claw-back rate-loading fix** (`payroll_service.py::_compute_and_record_clawback`): added `CommissionRule.staff_id.is_(None)` to the existing rate query. This wasn't called out as a required change in the implementation plan, but without it the migration would silently corrupt claw-back amounts once any per-staff override existed (dict assignment overwrite). Please double check the reasoning holds.
3. **Commission medicine-loop short-circuit removal** (`commission_service.py::aggregate_commission`): previously `if medicine_rate: for ...` skipped the whole loop when no clinic-wide medicine rate existed; changed to iterate unconditionally and resolve per-row, since a staff-specific medicine rate can exist without a clinic-wide one. Confirmed via `test_aggregate_commission_medicine_staff_override_applies_without_general_rate` — please sanity-check this doesn't change any other existing call site's expectations (only one call site, `compute_commission`, already updated).
4. **CommissionKpiConfigPage general-table filtering fix**: added `staff_id == null` filters to `rulesByServiceType`/`medicineRule` — this was necessary once the list endpoint started returning per-staff rows too, but is a change to previously-existing (TASK-128) code, not purely additive. Worth confirming this is the right call vs. e.g. having the BE only ever return clinic-wide rules from the unfiltered list (I chose "list returns everything, FE filters" per the plan's explicit wording: "list trả cả rule chung + rule riêng").
5. **Migration 0077**: reviewed by me end-to-end (upgrade/downgrade/re-upgrade against a real, disposable Postgres) but a second pair of eyes on the `COALESCE(staff_id, zero-uuid)` partial-index rebuild would be valuable given how easy it is to get NULL-handling in partial unique indexes subtly wrong.
6. **FE test workaround**: discovered that `fireEvent.click()` on a `type="submit"` button does not reliably propagate into the form's `submit` event in this project's jsdom test environment (confirmed via direct debugging — the button is correctly `type="submit"` and DOM-associated with its form, but `handleSubmit` never fires on click; `fireEvent.submit(form)` directly does fire it). Used `fireEvent.submit(form)` in the two new tests that need to submit a form (`CommissionKpiConfigPage.test.tsx`, `StaffFormPage.test.tsx`). This is a pre-existing test-environment quirk, not something I changed, but flagging it since it may affect how future form-submission tests should be written for this project — might be worth a note in project test guidelines.

## Deviations from the Plan

- **Payslip breakdown scope** (task.md AC: "tỷ lệ commission áp dụng (riêng hay chung)"): I did *not* add a "rate source" (staff-specific vs. clinic-wide) indicator to the `Payslip` schema/response. The authoritative `implementation-plan.md` doesn't call for this in its Components/Steps sections (only `session_rate`/`shift_rate`/`completed_shifts` are listed as new payslip fields), and the existing `procedure_commission`/`medicine_commission` totals already give the traceable commission *amount* per TASK-128. Adding a rate-source flag would be a straightforward follow-up if the reviewer/user wants it, but I treated the plan's explicit field list as authoritative over the higher-level AC wording, per the task instructions ("follow this plan exactly").
- Everything else follows the implementation plan's Components/Steps/Locked-decisions sections as written; no other deviations.

## Not Done (explicitly out of scope per the plan)

- Integration/E2E tests against a live Postgres+Redis stack — the task's own test instructions scoped BE verification to `pytest tests/unit -q` in Docker; I additionally verified the migration against a disposable Postgres container (see Test Results) but did not write `tests/integration/*` coverage. PROJECT.md's general quality gate calls for integration tests on DB-backed logic; flagging this gap explicitly in case the Test Agent phase should pick it up (the existing TASK-128 commission/payroll integration coverage in `tests/integration/test_hr_*` was not extended for the new per_session/per_shift/per-staff-override paths).

---

## Fix round 1 (review CHANGES_REQUESTED → addressed)

**Reviewed**: `docs/tasks/TASK-138/handoff/review-report.md` + `review-to-implementation.md` (decision: CHANGES_REQUESTED, 1 blocking).
**New commit**: BE `3feacf2` (`_feat138-be`). No FE files needed changes this round (all findings were backend-only) — FE hr test suite re-run as a sanity check (see Test Results below), unchanged commit `21866ce`.

### R1 [BLOCKING] — `staff_id` accepted with no clinic-scope validation → **Fixed**

`commission_config_service.create_commission_rule` now checks, before the duplicate pre-check, that `staff_id` (when provided) resolves to a non-deleted `staff_profile` row in the caller's own `clinic_id` — exact mirror of `staff_service._assert_account_in_clinic`. Raises `NotFoundError` (→ 404, existing `AppException` handler) instead of letting a bad/foreign UUID reach the FK and raise `IntegrityError` (→ unhandled 500). The `CommissionRuleUpdate` path doesn't need the same check — `staff_id` isn't a field on it (confirmed immutable-after-creation by the review itself).

Tests (`tests/unit/test_commission_config_service.py`, new file, 4 tests, mocked `AsyncSession` — DB-orchestrating CRUD, not pure logic, mirrors the existing `_mock_db_with_savepoint` pattern):
- `test_create_rule_rejects_staff_id_from_another_clinic` — clinic-scoped query returns no row → `NotFoundError`, rejected before the duplicate check ever runs.
- `test_create_rule_rejects_nonexistent_staff_id` — same code path, framed for the "doesn't exist at all" case (mechanically identical query/result to the cross-clinic case, which is the correct behavior: this check can't and shouldn't distinguish "foreign tenant" from "unknown").
- `test_create_rule_accepts_staff_id_in_same_clinic` — valid staff_id resolves, rule created with it, exactly 2 `db.execute` calls (existence check + duplicate check).
- `test_create_rule_without_staff_id_skips_the_scope_check` — regression: `staff_id=None` (clinic-wide rule, TASK-128 behavior) must not trigger the new query at all (1 `db.execute` call, not 2).

### M1/M2 [MAJOR — user decision confirmed] — Claw-back must use the per-staff override rate → **Fixed**

User decision (relayed by coordinator): claw-back reverses commission "theo tỷ lệ riêng đã áp" (at the same rate that was applied when earned) — staff override first, clinic-wide fallback, identical precedence to earning.

Reworked `payroll_service.aggregate_clawback` (pure function): added optional `doctor_to_staff`, `staff_service_type_rates`, `staff_medicine_rates` params (default `None` → treated as `{}`), and it now calls `commission_service.resolve_service_type_rate` / `resolve_medicine_rate` per line instead of doing a flat dict lookup. Because the new params default to empty, every pre-existing call/test with no per-staff data is byte-for-byte unchanged (verified: all 5 original `test_aggregate_clawback_*` tests still pass with zero edits).

Reworked `payroll_service._compute_and_record_clawback` (the DB-orchestrating caller):
- `doctor_to_staff` is now resolved *before* computing claw-back amounts (from the visit doctor + every medicine line's prescriber), so it's available for rate resolution — and reused as-is for the final `PayrollAdjustment.staff_id` mapping step, removing what was a second, duplicate query.
- Replaced the hand-rolled `staff_id IS NULL`-filtered `CommissionRule` query (my round-1 fix, which correctly protected the clinic-wide map from being overwritten but couldn't see per-staff rows at all) with `commission_service.load_rate_maps(db, clinic_id)` — promoted from `_load_rates`/`_RateMaps` to a public `load_rate_maps`/`RateMaps` since it's now shared between `compute_commission` (grants) and claw-back (reverses), guaranteeing both paths always resolve from the identical rate maps. The clinic-wide map inside `RateMaps` still only ever contains `staff_id IS NULL` rows — the earlier protection is preserved structurally, not by a separate filter I could have let drift out of sync.

Tests (`tests/unit/test_payroll_commission_kpi_clawback.py`, +4, all pure — no DB):
- `test_clawback_and_earning_symmetry_at_staff_override_rate` — runs the identical override configuration (15% override vs. 10% clinic-wide) through both `aggregate_commission` (earn) and `aggregate_clawback` (reverse); asserts both land on 15%, directly demonstrating the fix's core guarantee.
- `test_aggregate_clawback_doctor_without_override_uses_clinic_wide_rate` — regression: no override configured → still the clinic-wide 10%.
- `test_aggregate_clawback_mixed_batch_override_and_general_doctor` — the exact "mixed refund batch" scenario: two prescribing doctors on the same invoice's medicine lines, one overridden (20%) one not (5% clinic-wide fallback) — each resolves independently, no blending.
- `test_aggregate_clawback_unmapped_doctor_falls_back_to_clinic_wide_rate` — a doctor not resolvable to any `staff_profile` (not in `doctor_to_staff`) has no `staff_id` to look an override up with, so it can't accidentally pick up *another* staff member's override — must land on the clinic-wide rate.

Note: this closes M1 as a code fix now that the ambiguous plan wording ("Claw-back không đổi") has an explicit user decision overriding it. M2 ("no test coverage for the claw-back rate-query fix") is addressed at the pure-function level (where the actual resolve logic lives, per the 4 tests above); the DB-orchestration wiring in `_compute_and_record_clawback` itself (query construction, candidate-doctor-id gathering) remains integration-test territory — carried forward with the pre-existing M5 (no integration coverage for any TASK-138 path), not newly introduced by this fix.

### m1 [MINOR] — Docstring overclaims allowance/bonus/penalty are monthly/hourly-only → **Fixed**

`payroll_service.py` module docstring reworded: "Overtime applies to monthly/hourly only ...; allowance, attendance bonus and late penalty apply to ALL FOUR pay types." Matches the code (lines ~122-125) and the existing `test_per_shift_allowance_and_late_penalty_still_apply` test — no code change, docstring only.

### m2 [MINOR] — Migration 0077 downgrade fails when per-staff overrides exist → **Fixed**

Reordered `downgrade()`: per-staff `commission_rule` rows (`staff_id IS NOT NULL`) are now deleted, and the `staff_id` column dropped, *before* the old (no-`staff_id`) 0073 unique indexes are recreated. Previously the recreate step ran first and aborted with a duplicate-key error the instant a clinic-wide rule and a per-staff override shared a `service_type_id` — which is the whole point of this migration, so it would have hit on any DB that actually used the feature. Documented as a second, separate data-loss caveat in the migration's module docstring (distinct from the pre-existing `pay_type`-narrowing caveat) — downgrading after the feature has been used discards override rows by necessity (nowhere for them to live pre-0077).

**Re-verified end-to-end against a fresh, disposable Postgres container** (not the shared `clinic_e2e_postgres`): full `alembic upgrade head` (0001→0077) from scratch, then manually seeded the exact collision scenario — one clinic, one staff, one service_type, a clinic-wide `commission_rule` (10%) AND a per-staff override for the *same* service_type (15%) — then ran `alembic downgrade -1`. **Downgrade now succeeds** (previously this exact data would have aborted it); verified post-downgrade: `staff_id` column gone, both old partial unique indexes (`uq_commission_rule_clinic_service_type`, `uq_commission_rule_clinic_medicine`) present with their original (no-staff_id) definitions, `staff_profile.pay_type` back to `varchar(10)`, and exactly the clinic-wide rule (10%) survived — the override row was correctly discarded. Re-ran `alembic upgrade head` afterward — succeeds cleanly.

### n1 [NIT] — Overlong line in `_compute_one` → **Fixed**

Wrapped the 118-char `worked_days = ...` line across 4 lines. Cosmetic only, no behavior change.

### n2, n3, m3, m4, m5 — **Skipped**, with reasons

- **n2** (`PayrollPage.tsx` `PAY_TYPE_LABEL_FALLBACK` duplicates the `vi` locale strings): the review's own text says "harmless" and only reachable if the `hr` i18n namespace fails to load entirely. It's a defensive fallback, not a hardcoded map replacing the i18n path — removing it would mean a raw enum value (`"per_session"`) renders to the user if that namespace ever fails to load, which is strictly worse. Skipped: fixing it trades a safety net for no real benefit.
- **n3** (0%-rate asymmetry between procedure and medicine commission in `aggregate_commission`): the review explicitly concludes "This is pre-existing TASK-128 semantics faithfully preserved by the rewrite, not a new bug... noted only so it isn't discovered later as a regression." No action requested, none taken.
- **m3** (i18n keys for the new "Chiết khấu riêng theo nhân sự" section / StaffFormPage labels): the review's own conclusion is "matches their file's convention... Treat as i18n debt to fold into whichever pass converts these two pages" — not a cheap/local fix (both files have zero `useTranslation` calls today; converting ~12+ strings mid-feature would be a larger, separate i18n pass, not a fix-round item). Skipped per the review's own recommendation.
- **m4** (AC "tỷ lệ commission áp dụng (riêng hay chung)" not surfaced on the payslip): the review frames this as needing a user decision (accept the deviation, or open a follow-up), not a code defect — no fix requested from me. Skipped pending that decision; unchanged from the original handoff's documented deviation.
- **m5** (no integration/E2E coverage for the new payroll/commission paths): explicitly "hand to the Test Agent" per the review. Skipped — matches the "Not Done" section above, unchanged.

### Test Results (fix round 1)

**Backend** (same command as before, `docker run --rm -e ENVIRONMENT=development -v .../_feat138-be:/work -w /work clinic_e2e-api python -m pytest tests/unit -q`):
- **1117 passed, 12 failed** — identical 12 pre-existing failures (verified unchanged from before this fix round). +8 new tests (4 clinic-scope, 4 claw-back rate resolution) all pass. **Zero new failures.**
- `ruff check` on all changed/new files (`app/modules/hr`, the 3 touched test files, the migration) — clean.
- `mypy app/modules/hr` — same 0 new errors (pre-existing errors confined to unrelated `app/core/*` files).
- Migration re-verified end-to-end including the specific downgrade-order bug scenario (see m2 above) against a second disposable Postgres container.

**Frontend**: no FE files changed this round. Ran `npx vitest run src/tests/hr --silent` as a sanity check — **94 passed, 0 failed** (including the previously-flaky `AttendanceWidget` suite, which triggered clean this run). FE commit remains `21866ce`.

---

## Fix round 2 (m4) — payslip commission rate/source traceability

**Trigger**: task.md is now `IN_TESTING` (review re-approved everything else); m4 was escalated separately — task.md AC line ~49 requires the payslip breakdown to be traceable to "tỷ lệ commission áp dụng (riêng hay chung)" (which rate applied — per-staff override or clinic-wide). See the m4 discussion in `review-report.md` ("Re-review (fix round 1)" section, "Skips" subsection) and `review-to-test.md` ("Known open items").

**New commits**: BE `cebf0bd` (`_feat138-be`, on top of `3feacf2`). FE `4bf1b55` (`_feat138-web`, on top of `21866ce`).

### What changed

**BE** — extended the existing commission engine additively, no restructuring:

- `commission_service.StaffCommission` gained two booleans, `procedure_used_override` / `medicine_used_override`, set inside `aggregate_commission`'s existing accumulation loop (same loop, same iteration, just also checking which rule matched).
- Two new pure companion functions, `resolve_service_type_rate_with_source` / `resolve_medicine_rate_with_source`, mirror the existing `resolve_service_type_rate` / `resolve_medicine_rate` but additionally return `"staff_override"` or `"clinic_default"`. Added as separate functions rather than changing the originals' `Decimal | None` signature, which other callers (`payroll_service.aggregate_clawback`) and existing tests depend on — `aggregate_clawback` is untouched by this fix, on purpose (see below).
- `payroll_service._commission_rate_and_source(revenue, commission, used_override)` (new, pure) derives the payslip's `rate_percent` as `commission / revenue * 100` — exact when only one rate contributed to a component (the common case: one `service_type`, or medicine's single flat rate per doctor), and a fair revenue-weighted blend in the rare case where one staff earned procedure commission across multiple `service_type`s resolving to *different* rates in the same period. No revenue at all → `(None, None)` (nothing was "applied," matches the existing zero/absent-commission display convention).
- `_apply_commission_kpi_clawback` gained four optional keyword-only params (`procedure_rate_percent`, `procedure_rate_source`, `medicine_rate_percent`, `medicine_rate_source`, all defaulting to `None`) and now always writes them onto the slip dict. `compute_payroll` computes them via `_commission_rate_and_source` from the same `StaffCommission` the existing amounts already come from.
- `Payslip` schema (`hr_schemas.py`): added the four fields above, typed `float | None` / `Literal["staff_override","clinic_default"] | None`.

**Claw-back deliberately got no matching rate/source field.** `PayrollAdjustment` (and its period sum in `_get_clawback_totals`) stores no per-row rate — adding one would mean a new column and restructuring the claw-back write path, which is out of scope for "minimal" and wasn't asked for. Consistency is preserved differently: claw-back already resolves through the *identical* `resolve_service_type_rate`/`resolve_medicine_rate` precedence as earning (fix round 1), so there is nothing for a claw-back-specific annotation to contradict — it would either restate the same information with extra plumbing, or (worse) risk showing a stale/wrong rate for an adjustment that could span a different period's configuration than the current payslip's. Flagging this interpretation explicitly in case the reviewer disagrees and wants a follow-up.

**FE** — `PayrollPage.tsx`: the procedure/medicine commission cells now render a small badge under the amount — `"15% · tỷ lệ riêng"` (override, amber) or `"5% · tỷ lệ chung"` (default, gray) — via a new `RateBadge` component reading the four new `Payslip` fields (added to `types.ts`, plus a new `CommissionRateSource` type). No badge when the component earned nothing (`ratePercent == null`, which also covers payslips from before this fix that don't have the fields at all — `undefined == null` is `true` in JS). Two new i18n keys, `hr:payroll.rateSource.{staffOverride,clinicDefault}`, added to **both** `vi` ("tỷ lệ riêng" / "tỷ lệ chung", per the coordinator's suggested wording) and `en` ("custom rate" / "standard rate").

### Tests

BE (+17 total):
- `test_commission_service.py` (+11): `resolve_service_type_rate_with_source` / `resolve_medicine_rate_with_source` (override / clinic-default / unconfigured, ×2 functions = 6 tests), plus `aggregate_commission`'s `used_override` tracking (procedure override=true, procedure regression=false without override, medicine override=true, unmapped-doctor has nothing to mismark = 4 tests), for 10 — plus fixed a pre-existing latent bug in my own edit (see "Note" below) that would have orphaned an assertion.
- `test_payroll_commission_kpi_clawback.py` (+6): `_commission_rate_and_source` (override, clinic-default, no-revenue→None, multi-service-type blend = 4), `_apply_commission_kpi_clawback`'s new fields (stores them; defaults to None when omitted = 2).

FE (+4): `PayrollPage.test.tsx` — override badge renders with "15%"/"tỷ lệ riêng", clinic-default badge renders with "5%"/"tỷ lệ chung", no badge when `rate_percent` is `null` (zero-revenue case), no crash/no badge for a payslip missing the new fields entirely (back-compat with round-1-shaped fixtures).

**Note (self-caught, not a reviewer finding)**: while inserting the new `test_commission_service.py` test block, an editing mistake split an existing test's two-assertion body across a section boundary, silently orphaning its second assertion (`assert result.by_staff[staff_b]...`) into the next function and causing a `NameError` at test time. Caught by running the suite before considering the change done; fixed by restoring the assertion to its original test and re-running to green. Mentioning it because it's exactly the kind of self-inflicted bug that only running the full affected test file (rather than assuming the edit landed as intended) catches.

### Test results (fix round 2)

**Backend** (same Docker command as before): **1133 passed, 12 failed** — identical pre-existing 12 (verified unchanged). +16 new tests vs. the prior 1117, all passing. **Zero new failures.** `ruff check` on all changed files — clean. `mypy app/modules/hr` — same 0 new errors.

**Frontend**: `npx vitest run src/tests/hr/PayrollPage.test.tsx` — **10/10 passed** (6 existing + 4 new). Full `npx vitest run src/tests/hr --silent` — **97 passed, 1 failed**: `AttendanceWidget`'s `"M-14: DOES call hrApi.myShifts"` — this is the documented pre-existing **date-dependent flaky test** from the original task brief ("flaky theo ngày"), unrelated to payroll/commission code (confirmed by re-running it in isolation: fails consistently today regardless of retries, and touches attendance-shift fetching, not this fix's files). `npm run type-check` and `eslint` on all changed files — clean.

### Status

`task.md` left at `IN_TESTING` as instructed — not modified.
