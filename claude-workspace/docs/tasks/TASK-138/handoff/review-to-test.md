# Handoff: TASK-138 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED (after fix round 1)
**Branch**: `feature/TASK-138-payroll-session-shift`
**Commits**: BE `3feacf2` (`_feat138-be`) · FE `21866ce` (`_feat138-web`)
**Full report**: `docs/tasks/TASK-138/handoff/review-report.md` (see the "Re-review (fix round 1)" section)

## Summary

Two payroll extensions on the TASK-128 engine: pay types `per_session` (session_rate ×
attendance-grid days, half=0.5) and `per_shift` (shift_rate × `Shift.status='completed'`), neither
earning OT; and per-staff commission overrides via a nullable `commission_rule.staff_id` resolving
staff-specific → clinic-wide → none. Round 1 raised one blocking item (unvalidated cross-tenant
`staff_id` on create) and two Majors (claw-back rate asymmetry + its missing coverage); all three are
closed in `3feacf2`. Unit coverage is strong (40 new BE tests, 14 new FE tests, zero new failures in
either suite), but **there is no integration or E2E coverage for any TASK-138 path** — that is the
main gap this phase must close.

## State at approval

- BE unit: **1117 passed, 12 failed** — the 12 are the known pre-existing dev set (verified by
  `diff`-ing sorted failure lists against the round-1 run: identical). Zero new failures.
- FE: **1257 passed, 3 failed** (QueuePage ×2 + ForgotPasswordPage ×1, all pre-existing). `tsc` and
  `eslint` clean. FE untouched in fix round 1.
- `ruff` clean on all changed files (the 142 errors in `tests/unit` are pre-existing — same 142 on
  clean `dev`).
- Alembic single head: `0077` → `0076` (dev's head), no collision.

## Focus areas for testing

### 1. Payroll engine against live Postgres (highest priority — no integration coverage exists)

`tests/integration/test_hr_*` was never extended for the new paths. Cover, with real
`attendance_day` / `shift` rows rather than mocked timesheet dicts:
- `per_session`: full days, **half-days (0.5)** — confirm 21 present + 2 half = 21.5 buổi end to end.
- `per_session` with **no attendance-grid data at all** → must pay **0**, and specifically must **not**
  fall back to the legacy Shift/TimeLog `worked_shifts` count even when that count is non-zero. This
  is a deliberate locked decision and the most likely thing to be "helpfully" broken later.
- `per_shift`: only `status='completed'` counts; seed `cancelled` / `scheduled` / `on_leave` shifts in
  the same period and confirm they are excluded.
- Rate ≤ 0 or NULL on either new type → staff drops off payroll (`None` slip), **unless** they have
  commission/KPI/adjustment, in which case `_empty_slip` must still list them (per_session's buổi count
  sourced from the grid).
- Allowance / attendance bonus / late penalty **do** apply to both new pay types; overtime is **0** for
  both even with `ot_multiplier` set and OT hours logged.
- Regression: `monthly` and `hourly` staff produce identical payslips to `dev` with `session_rate` /
  `shift_rate` populated but unused.
- Period boundaries: shifts/attendance on the first and last day of the month.

### 2. Claw-back symmetry E2E (reworked in fix round 1 — highest regression risk)

The rework changed real DB-orchestration wiring in `_compute_and_record_clawback` that unit tests
cannot reach (candidate-doctor gathering, `load_rate_maps` call, query ordering):
- **Symmetry**: configure a per-staff override (e.g. 15%) over a clinic-wide rate (10%), earn
  commission in a period, **post the period**, then void/refund the invoice → the claw-back adjustment
  must be exactly the 15% amount, not 10%. Assert the posted `PayrollAdjustment` value.
- **Mixed batch**: one invoice with medicine lines from two prescribers, only one holding an override →
  each clawed back at their own rate, no blending.
- **TASK-128 regression**: a clinic with **zero** per-staff rules must produce byte-identical claw-back
  amounts to `dev`. Worth running the existing TASK-128 claw-back integration tests unchanged.
- **Unmapped doctor**: a doctor with no `staff_profile` → clinic-wide rate, `clawback_unmapped_doctor`
  warning logged, no crash.
- **Period not posted** → still no claw-back (early return unchanged).
- Savepoint isolation: a failure inside claw-back must not turn the caller's void/refund commit into a
  `PendingRollbackError`.

### 3. Migration 0077 on real data

- Upgrade against a **restored copy of production-like data** (not just an empty DB): confirm the
  `pay_type` String(10)→String(20) widening on a table with existing rows, and that both rebuilt
  partial unique indexes accept an existing clinic-wide rule.
- Insert a clinic-wide rule **and** a per-staff override for the same `(clinic_id, service_type_id)` →
  both must coexist; a second override for the *same* staff must be rejected (409, not 500).
- **Downgrade with that collision data present** — this exact scenario aborted before the fix. Confirm
  it now succeeds, that override rows are discarded while the clinic-wide rate survives, and that
  re-upgrading afterwards works.

### 4. API surface / RBAC / tenancy

- `POST /hr/commission-rules` with a `staff_id` from **another clinic** → **404**, no row written.
  Same for a non-existent UUID → 404, **not 500**. (Unit-tested with a mocked session; needs a real
  two-clinic DB assertion.)
- `staff_id=None` (clinic-wide rule) path unchanged — no extra query, no validation error.
- Confirm `staff_id` cannot be changed via `PATCH` (not in the schema — verify the API ignores/rejects
  it rather than silently accepting).
- All four commission-rule endpoints still require `payroll.manage`; staff CRUD still `staff.manage`.
  Verify a user without `payroll.manage` gets 403.
- `GET /hr/commission-rules?staff_id=` returns only that staff's overrides; unfiltered returns
  clinic-wide + all overrides, and **never** another clinic's rows.
- Deleting a per-staff override → that staff reverts to the clinic-wide rate on the next payroll run.

### 5. Frontend flows

- **StaffFormPage**: create and edit staff on all four pay types; confirm the correct rate input shows,
  the OT-multiplier field is hidden for `per_session`/`per_shift`, and switching pay type then saving
  persists the right field. Check no stale `session_rate` is sent when switching back to `monthly`.
- **PayrollPage**: `"22 buổi × 300,000đ"` / `"18 ca × 200,000đ"` breakdown renders; monthly still shows
  `"26 công"` and hourly `"160h"` (regression); pay-type labels resolve from i18n in **both** vi and en
  — switch language and confirm no raw `per_session` enum leaks through.
- **CommissionKpiConfigPage**: the general table must show **only** clinic-wide rates once per-staff
  overrides exist (this filter was a fix — regression-test it explicitly); the per-staff section shows
  override next to the clinic-wide fallback, "Chưa cấu hình chung" when only an override exists, and
  delete reverts to fallback. The staff picker must list staff **without user accounts** (nurses) —
  they are configurable even though automatic commission won't reach them.
- Staff-without-account end-to-end: attendance ticking → `per_session` payroll for a nurse with
  `user_id = NULL`, driven entirely by admin.

## Known open items (not defects — do not re-file as bugs)

- **⚠️ m4 — open acceptance-criteria gap needing a user decision.** `task.md:49` requires the payslip
  breakdown to be traceable to *which* commission rate applied (per-staff vs clinic-wide). The
  `Payslip` schema gained `session_rate` / `shift_rate` / `completed_shifts` but **no rate-source
  indicator**. The implementer treated the plan's explicit field list as authoritative over the
  higher-level AC, which I accepted — but the user must either accept the deviation or open a
  follow-up before TASK-138 closes. **Please surface this in the test report so it doesn't close
  silently.**
- **m3 — i18n debt.** The new "Chiết khấu riêng theo nhân sự" section and the new StaffFormPage labels
  are hardcoded Vietnamese. Both pages have zero `useTranslation` today, so this matches their existing
  convention; folded into the pending i18n pass for these two pages. The 7 keys that *were* added are
  correctly present in both `vi` and `en`. Not a bug — do not file.
- **n3 — informational.** In `aggregate_commission`, a 0% *procedure* rate records revenue with 0
  commission while a 0% *medicine* rate skips the row entirely. Pre-existing TASK-128 semantics,
  faithfully preserved. Noted so it isn't mistaken for a new regression.
- **Test-environment quirk** (from the implementer, confirmed reasonable): `fireEvent.click()` on a
  `type="submit"` button does not reliably fire `handleSubmit` in this project's jsdom setup; use
  `fireEvent.submit(form)`. Worth adding to the project test guidelines.
