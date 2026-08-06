# Handoff: TASK-138 → Code Implementation Agent

**From**: Code Review Agent
**To**: Code Implementation Agent
**Status**: IN_REVIEW (unchanged — resubmit on the same branch)
**Decision**: CHANGES_REQUESTED
**Full report**: `docs/tasks/TASK-138/handoff/review-report.md`

## Summary

The feature is well built and well tested — 32 new BE unit tests and 14 new FE tests all pass, zero new
failures in either suite, lint/type-check clean, migration chain single-headed at 0077→0076, and both
"latent bug fixes" you flagged (claw-back `staff_id IS NULL`, medicine-loop per-row resolve) are correct
and I have written up why. One blocking gap: the new `staff_id` field on the commission-rule create
endpoint accepts any UUID with no clinic-scope validation.

## Required Changes (blocking)

**R1 — validate `staff_id` belongs to the caller's clinic**
`app/modules/hr/services/commission_config_service.py:48-100` (called from `app/modules/hr/api/routes.py:1013-1027`)

`create_commission_rule` writes `body.staff_id` straight into the row. Nothing verifies the
`staff_profile` exists, is not soft-deleted, or is in this clinic. Result: (a) a clinic A admin can
persist a rule referencing clinic B's staff — the FK passes because Postgres RI checks bypass RLS;
(b) a non-existent UUID raises `IntegrityError` on flush and, with no `IntegrityError` handler
registered (`app/core/exceptions.py:136-139`), returns HTTP 500 instead of 404/422.

Fix — mirror the existing `staff_service._assert_account_in_clinic` pattern, before the duplicate
pre-check:

```python
if staff_id is not None:
    exists = (await db.execute(
        select(StaffProfile.id).where(
            StaffProfile.id == staff_id,
            StaffProfile.clinic_id == clinic_id,
            StaffProfile.is_deleted.is_(False),
        )
    )).scalars().first()
    if exists is None:
        raise NotFoundError("Không tìm thấy nhân sự trong phòng khám này.")
```

Add one test covering a non-existent `staff_id` (and, if convenient, a foreign-clinic one).

Note: `create_kpi_target`, `shift_service.create_shift` and the attendance write paths have the same
gap from TASK-127/128. **Do not fix those here** — they belong in a separate hardening task. Only the
field this task introduces needs the check.

## Cheap wins — optional, welcome in the same pass

- **m1** `app/modules/hr/services/payroll_service.py:14-16` — the module docstring says
  "Overtime, allowance, attendance bonus and late penalty apply to monthly/hourly only". Only overtime
  is. Lines 122-125 apply allowance/attendance_bonus/late_penalty to all four pay types, and your own
  `test_per_shift_allowance_and_late_penalty_still_apply` asserts that. Reword.
- **m2** `alembic/versions/0077_*.py:109-127` — `downgrade()` recreates the two 0073 unique indexes
  *before* dropping `staff_id`, so on any DB that actually has per-staff overrides the
  `CREATE UNIQUE INDEX` aborts with a duplicate key. Drop the column first (or delete override rows
  first) and mention it in the docstring alongside the existing `pay_type` warning.
- **n1** `payroll_service.py:88` is 118 chars vs the project's `line-length = 100` (ruff passes only
  because `E501` is in `ignore`).

## Answers to your "Areas for Review Focus"

1. **`per_session` never falling back to the legacy count** — correct reading, keep it. Falling back
   would pay per_session staff from stale Shift/TimeLog data, contradicting locked decision #1.
2. **Claw-back `staff_id IS NULL` filter** — reasoning holds, the fix is necessary; without it the
   `for r in rates_result` dict assignment would let an override overwrite the clinic-wide rate for
   *every* doctor. Two follow-ups recorded, neither blocking: it has no test (M2), and staff with an
   override now earn at the override rate but get clawed back at the clinic-wide rate (M1 — a spec
   ambiguity in the plan's "Risks" wording that needs a user decision, not a code change from you now).
3. **Medicine-loop short-circuit removal** — verified behaviour-identical with no overrides configured
   (falsy general rate → every row skipped, as before) and required for a staff-only medicine rate.
   `compute_commission` is the only call site and is updated. No action.
4. **`CommissionKpiConfigPage` `staff_id == null` filters** — the right call, and required once the
   list endpoint returns override rows; `Map.set` last-wins would otherwise show an override in the
   clinic-wide table. `== null` correctly catches `undefined` too. No action.
5. **Migration 0077 COALESCE rebuild** — reviewed against 0073's original DDL: upgrade is correct, the
   recreated indexes are byte-identical on downgrade, and the zero-UUID sentinel folds NULL into one
   bucket per clinic/service_type exactly like 0044's `_NULL_CLINIC_SENTINEL`. Your
   `CommissionRule.staff_id == staff_id` pre-check correctly compiles to `IS NULL` for `None`, matching
   the index. Only the downgrade *ordering* needs attention (m2).
6. **`fireEvent.submit` workaround** — fine, no objection. Worth a line in the project test guidelines.

## Deviations I am escalating rather than rejecting

- **AC "tỷ lệ commission áp dụng (riêng hay chung)"** (task.md:49) is genuinely unmet — no rate-source
  indicator on the payslip. Your precedence argument (plan's explicit field list over the higher-level
  AC) is the right call, so I am not requiring it, but the user needs to accept it or open a follow-up.
- **i18n**: the plan asked for "labels config per-staff" locale keys; the new
  `CommissionKpiConfigPage` section and `StaffFormPage` labels are hardcoded Vietnamese. Both files have
  zero `useTranslation` today, so this matches their convention — folded into the i18n debt, not required
  here. The 7 keys you did add are correctly present in both `vi` and `en`.
