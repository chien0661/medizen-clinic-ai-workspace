# Code Review Report — TASK-138

**Task**: Payroll — thêm kiểu tính lương theo buổi / theo ca + chiết khấu cấu hình theo từng nhân sự
**Reviewer**: Code Review Agent
**Date**: 2026-08-06
**Branch**: `feature/TASK-138-payroll-session-shift`
**Commits reviewed**: BE `16061b4` → `3feacf2` (`_feat138-be`), FE `21866ce` (`_feat138-web`)
**Decision**: **APPROVED** (fix round 1 — see "Re-review" at the bottom)

> **Round 1 decision was CHANGES_REQUESTED** (1 blocking item, R1 below). Fix round 1 landed as BE
> commit `3feacf2`; R1 is resolved, both MAJORs are closed, and the review now **APPROVES**.
> Everything between here and the "Re-review (fix round 1)" section is the original round-1 record,
> kept unedited for traceability — read the re-review section for current status.

---

## ⛔ Required changes (blocking)

### R1 — `commission_rule.staff_id` is accepted without any clinic-scope validation

**Where**: `app/modules/hr/api/routes.py:1013-1027` → `app/modules/hr/services/commission_config_service.py:48-100`

`POST /api/v1/hr/commission-rules` takes `body.staff_id` (new in TASK-138) and passes it straight
into the `CommissionRule` row. Nothing checks that the referenced `staff_profile` exists, is not
soft-deleted, or **belongs to the caller's clinic**. There is no `IntegrityError` handler registered
either (`app/core/exceptions.py:136-139` registers only `AppException` + a catch-all 500 handler).

Two concrete failures:

1. **Cross-tenant write.** A `payroll.manage` user in clinic A can POST a `staff_id` belonging to
   clinic B's `staff_profile`. The FK passes (Postgres RI checks bypass RLS), so clinic A ends up
   holding a rule row pointing at another tenant's staff. It never resolves to a payout (the
   `doctor_to_staff` map in `commission_service.compute_commission` is clinic-scoped, so the override
   silently never applies) — but it is a persisted cross-tenant reference, and the FK's
   `ON DELETE CASCADE` makes clinic B's data lifecycle able to touch clinic A's rows.
2. **500 on bad input.** A `staff_id` that does not exist at all raises `IntegrityError` on flush →
   the catch-all handler returns HTTP 500 instead of a 404/422.

**Why it matters**: this is the one new user-supplied FK the task adds, on a multi-tenant table, and
tenant-boundary enforcement on writes is a hard project constraint. The project already has the exact
pattern to copy: `staff_service._assert_account_in_clinic` (used for `user_id` on staff create).

**Suggested fix** (in `commission_config_service.create_commission_rule`, before the duplicate
pre-check):

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

Plus one unit/integration test asserting a foreign / non-existent `staff_id` is rejected.

**Note**: the same gap pre-exists on `create_kpi_target` (`commission_config_service.py:176`),
`shift_service.create_shift`, and the attendance write paths — all TASK-127/128 code. I am **not**
asking TASK-138 to fix those; a module-wide hardening follow-up is recommended separately (see M1).
But the field this task introduces should not extend the pattern.

---

## Verification performed

| Check | Command | Result |
|---|---|---|
| BE unit tests | `docker run --rm -v _feat138-be:/work -w /work clinic_e2e-api python -m pytest tests/unit -q` | **1109 passed, 12 failed in 66.5s** |
| BE lint | `ruff check app/modules/hr tests/unit/test_payroll_logic.py tests/unit/test_commission_service.py` | **All checks passed** |
| FE tests | `npx vitest run --silent` | **1257 passed, 3 failed** (135 files) |
| FE type-check | `npx tsc --noEmit` | **clean (exit 0)** |
| FE lint | `eslint` on all 5 changed source files | **clean (exit 0)** |
| Alembic chain | grep over `alembic/versions/` | **single head**: `0077.down_revision = "0076"`, `0076` is dev's head, nothing else points at `0076` or `0077`, no numbering collision |

**BE failure list** (all 12 are the known pre-existing set on clean `dev` — none in `hr`/payroll/commission):
`integrations/test_email.py::test_all_templates_render_in_both_langs`,
`test_erasure_service.py::test_last_accessed_at_updated_on_read`,
`test_feature_flags.py::test_get_flag_value_returns_false_for_unknown_flag`,
`test_medicine_stock_status.py` ×4, `test_rls_helpers.py` ×2, `test_tenancy_middleware.py` ×3.
→ **Zero new BE failures.** All 32 new TASK-138 unit tests pass.

**FE failures**: `QueuePage` ×2 + 1 other — the documented pre-existing set; `AttendanceWidget` did
not trigger this run. → **Zero new FE failures.** All 14 new TASK-138 FE tests pass.

Migration was NOT re-run against a live Postgres by this review (the implementer reports a verified
fresh upgrade → downgrade → re-upgrade cycle against a disposable container); it was reviewed by
reading against migration 0073's original index DDL — see N1.

---

## Findings

### MAJOR

**M1 — Claw-back applies the clinic-wide rate to staff who earned at a per-staff override rate**
`app/modules/hr/services/payroll_service.py:513-533`
*Non-blocking — matches the authoritative plan; needs a user decision + follow-up task.*

The `staff_id.is_(None)` filter the implementer added is **correct and necessary** as written: without
it, the `for r in rates_result` loop (line 529-533) does plain dict assignment keyed only by
`service_type_id`, so a per-staff override row would non-deterministically overwrite the clinic-wide
rate and corrupt claw-back amounts for *every* doctor. Good catch, and it preserves TASK-128 behavior
byte-for-byte for clinics with no per-staff rules (verified: with zero override rows the query returns
the identical row set as before).

The residual gap is a **spec** gap, not a code defect: `aggregate_clawback` receives flat rate maps and
resolves the doctor from `visit_doctor_id` *after* the rates are loaded, so it structurally cannot apply
a per-staff rate without refactoring. Consequence: if Dr. A earns commission at an override rate of 15%
while the clinic-wide rate is 10%, voiding a posted invoice claws back only 10% — Dr. A keeps the 5%
difference (and the mirror case over-claws). Real money, in exactly the scenario this task creates.

`implementation-plan.md` "Risks" says *"Claw-back (TASK-128) không đổi — chỉ điểm resolve rate thay đổi"*,
which the implementer read as "claw-back out of scope". That reading is defensible and I am not blocking
on it, but the wording is ambiguous enough that it should go back to the user.

*Action*: document the limitation in `deliveries/final-specs/`, and raise a follow-up task to either
(a) thread per-staff resolution through `aggregate_clawback`, or (b) get an explicit user sign-off that
claw-back stays on the clinic-wide rate.

**M2 — Claw-back `staff_id IS NULL` fix has no test coverage**
`app/modules/hr/services/payroll_service.py:519-526`

The medicine-loop fix (finding below) is covered by
`test_aggregate_commission_medicine_staff_override_applies_without_general_rate`; the claw-back rate-query
fix is not covered by anything. It lives in a DB-orchestrating function, so a unit test would need
mocking or an integration test. Given it silently guards a money-corrupting bug, it should not be
regression-unprotected.

*Action*: Test Agent should add an integration case — post a period, configure a per-staff override for
the same service_type as a clinic-wide rule, void an invoice, assert the claw-back amount uses the
clinic-wide rate and is not doubled/overwritten.

### MINOR

**m1 — `payroll_service` module docstring now states something the code does not do**
`app/modules/hr/services/payroll_service.py:14-16`

> "Overtime, allowance, attendance bonus and late penalty apply to monthly/hourly only"

Only **overtime** is monthly/hourly-only. Lines 122-125 apply `allowance`, `attendance_bonus` and
`late_penalty_total` to *all four* pay types, and
`test_per_shift_allowance_and_late_penalty_still_apply` asserts exactly that (correctly, per the plan:
*"allowance/attendance_bonus/late_penalty giữ nguyên logic"*). The docstring is the first thing the next
maintainer reads on a payroll engine — fix the sentence to say "Overtime applies to monthly/hourly only;
allowance, attendance bonus and late penalty apply to all pay types."

**m2 — Migration 0077 downgrade fails on any DB that used the feature**
`alembic/versions/0077_payroll_session_shift_staff_commission.py:109-127`

`downgrade()` recreates `uq_commission_rule_clinic_service_type` / `uq_commission_rule_clinic_medicine`
(lines 116-125) **before** dropping the `staff_id` column (line 127). If any per-staff overrides exist,
those rows collapse into the same uniqueness bucket as the clinic-wide rule and `CREATE UNIQUE INDEX`
aborts with a duplicate-key error mid-downgrade. The docstring warns about the `pay_type` narrowing but
not about this.

The upgrade side is correct — I verified the recreated DDL is byte-identical to 0073's original
(`0073_*.py:101-110`), the `COALESCE(staff_id, '00000000-...'::uuid)` sentinel correctly folds NULL into
a single bucket per clinic/service_type (mirroring 0044's `_NULL_CLINIC_SENTINEL`), and
`commission_config_service`'s pre-check `CommissionRule.staff_id == staff_id` compiles to `IS NULL` for
`None`, matching the index's bucketing.

*Fix*: drop the `staff_id` column first, or `DELETE FROM commission_rule WHERE staff_id IS NOT NULL`
before recreating the indexes, and say so in the docstring.

**m3 — Plan's "labels config per-staff" i18n keys were not added**
`src/pages/hr/CommissionKpiConfigPage.tsx:358-478`, `src/pages/hr/StaffFormPage.tsx:199-266`

`implementation-plan.md` lists `src/locales/{vi,en}/hr.json` as needing *"Key mới cho 2 kiểu lương,
labels config per-staff"*. Only the pay-type + unit-breakdown keys landed (7 keys, correctly present in
**both** `vi` and `en`, guarded by the generic parity test plus 2 new targeted assertions — verified).
The ~12 strings in the new "Chiết khấu riêng theo nhân sự" section and the new StaffFormPage labels/hints
are hardcoded Vietnamese.

Mitigating: both files contain **zero** `useTranslation` calls today (pre-existing debt the
2026-08-06 i18n pass did not reach), so the new strings match their file's convention and partially
i18n-ising one section would be worse. No hardcoded `TASK-xxx` strings leaked into any UI text (checked).
Treat as i18n debt to fold into whichever pass converts these two pages.

**m4 — AC "tỷ lệ commission áp dụng (riêng hay chung)" is not surfaced on the payslip**

`task.md` AC line 49 asks the payslip breakdown to be traceable down to *which* commission rate applied
(per-staff vs clinic-wide). The `Payslip` schema gained `session_rate`/`shift_rate`/`completed_shifts`
but no rate-source indicator. The implementer flagged this deviation and justified it from the plan's
explicit field list, which is the right call on precedence — but the AC in `task.md` is still literally
unmet, so it needs an explicit user decision (accept, or follow-up task) before the task is closed.

**m5 — No integration coverage for any of the new paths**

`tests/integration/test_hr_*` was not extended for `per_session`/`per_shift` payroll or per-staff
override resolution. Unit coverage is genuinely strong (32 new BE tests: per_session happy path,
half-day 0.5, no-grid-data→0, zero/None rate→None slip, no-OT, allowance+late-penalty still apply,
monthly/hourly regression with the new fields populated, `_empty_slip` per_session, and 13 commission
resolve/precedence tests including "override without any clinic-wide rate"). PROJECT.md's quality gate
still expects integration coverage for DB-backed logic — hand to the Test Agent.

### NIT

**n1** — `payroll_service.py:88` is 118 chars; project `line-length = 100` (ruff, but `E501` is in
`ignore`, so lint passes). Wrap it.

**n2** — `PayrollPage.tsx:31-36` `PAY_TYPE_LABEL_FALLBACK` duplicates the `vi` locale values verbatim
and is only reachable if the `hr` namespace fails to load. Harmless, but it re-introduces the hardcoded
map the change was meant to remove.

**n3** — Rate-of-zero asymmetry in `commission_service.aggregate_commission`
(`commission_service.py:151-172`): a `0%` **procedure** rate creates a bucket with revenue and 0
commission (`if rate is None: continue`), whereas a `0%` **medicine** rate skips the row entirely
(`if not rate: continue`). This is pre-existing TASK-128 semantics faithfully preserved by the rewrite,
not a new bug — noted only so it isn't "discovered" later as a regression.

---

## What I verified as correct (no action)

- **`per_session` semantics** (`payroll_service.py:83-88, 99-102`): `session_rate ×
  attendance_worked_days`, deliberately never falling back to the legacy Shift/TimeLog count. This
  matches locked decision #1 ("bắt buộc dùng attendance grid; không có dữ liệu grid → 0 công") and the
  alternative would pay per_session staff from stale Shift data. The implementer's reading is correct.
  Half-days flow through untouched (0.5 per tick), tested at 21.5.
- **`per_shift` semantics** (`timesheet_service.py:104-107`): `SUM(CASE WHEN status='completed')`,
  grouped by `staff_id`, filtered on `clinic_id` + `is_deleted` + the period window — clinic-scoped,
  matches locked decision #2, cancelled/scheduled shifts excluded.
- **Rate ≤ 0 → `None` slip** for both new types (`payroll_service.py:57-60`), identical convention to
  monthly/hourly; `_empty_slip` then still carries the commission-only staff, with per_session's
  "buổi" count sourced from the grid.
- **Commission resolve precedence**: `resolve_service_type_rate` / `resolve_medicine_rate` are pure,
  correctly ordered (staff → clinic-wide → None), and `aggregate_commission`'s new params default to
  `{}` so every pre-TASK-138 call site is byte-for-byte unchanged. `_load_rates` splits maps correctly
  and stays clinic-scoped.
- **Medicine-loop fix**: removing the `if medicine_rate:` short-circuit in favour of a per-row
  `if not rate: continue` is behaviour-identical when no overrides exist (falsy general rate → every
  row skipped, same as before) and is required for a staff-only medicine rate to work. Covered by test.
- **Staff-without-accounts constraint**: everything keys on `staff_id`; `CommissionRule.staff_id` FKs
  `staff_profile.id`, never `user.id`. FE `StaffPicker` sources from `useStaff` → `hrApi.listStaff`
  (i.e. `staff_profile`), not the user list — locked decision #5 satisfied. The UI note about automatic
  commission requiring a linked doctor account is present (`CommissionKpiConfigPage.tsx:379-383`).
- **RBAC**: all four commission-rule endpoints keep `Depends(require_permission("payroll.manage"))`;
  staff CRUD keeps `staff.manage`. Unchanged.
- **Audit**: `CommissionRule.__auditable__` and `StaffProfile.__auditable__` intact; `session_rate` /
  `shift_rate` are the same class of salary data as the already-audited `base_salary` / `hourly_rate`,
  so no new `__audit_exclude__` is warranted.
- **Schema immutability**: `staff_id` is on `CommissionRuleCreate` but deliberately absent from
  `CommissionRuleUpdate` — an override cannot be silently re-pointed at another staff member.
- **FE fallback display**: `CommissionKpiConfigPage`'s `staff_id == null` filters on
  `rulesByServiceType` / `medicineRule` (lines 207 and 210) are **required**, not cosmetic — the unfiltered
  list endpoint now returns override rows, and `Map.set` last-wins would have shown an override in the
  clinic-wide table. `== null` correctly catches both `null` and `undefined`. The `invalidateRules`
  prefix key correctly invalidates the per-staff query too.
- **FE breakdown math**: per_session renders `worked_days` (grid count), per_shift renders
  `completed_shifts` — the right field for each; monthly/hourly rendering paths untouched and covered by
  an explicit regression test (`26 công`).
- No secrets, no `console.log`, no `TODO`/`FIXME`, no commented-out code in the diff.

---

## Re-review scope

Only **R1** blocks. On re-submission I need: the clinic-scope check on `staff_id` + a test for it.
Fixing m1 (docstring) and m2 (downgrade order) in the same pass would be cheap and welcome but is not
required. M1/M2/m3/m4/m5 should be carried forward as follow-ups rather than gating this branch.

---

# Re-review (fix round 1)

**Date**: 2026-08-07
**Commit re-reviewed**: BE `3feacf2` (`git diff 16061b4..3feacf2` — 6 files, +357/−56). FE unchanged at `21866ce`.
**Verdict**: ✅ **APPROVED** → status IN_TESTING

Targeted re-review of the fixes only. Everything cleared in round 1 was not re-examined.

## R1 [BLOCKING] — Fixed and verified ✅

`commission_config_service.py:60-76` now runs a clinic-scoped existence check before the duplicate
pre-check: `StaffProfile.id == staff_id AND clinic_id == clinic_id AND is_deleted IS FALSE`, raising
`NotFoundError` (→ 404 via the registered `AppException` handler) instead of letting a bad UUID reach
the FK and surface as an unhandled 500. Exactly the `_assert_account_in_clinic` pattern I asked for.

**Update path independently verified as safe** (I did not take this on the implementer's word):
- `hr_schemas.CommissionRuleUpdate` has only `rate_percent` and `is_active` — no `staff_id`.
- `commission_config_service.update_commission_rule` has no `staff_id` parameter and mutates only
  those two fields; its row lookup is clinic-scoped (`CommissionRule.clinic_id == clinic_id`).

So `staff_id` is genuinely immutable after creation and there is no second unvalidated write path.
**R1 is fully closed — not partially closed.**

Coverage: `tests/unit/test_commission_config_service.py` (new, 4 tests) — foreign clinic → rejected,
non-existent → rejected, valid same-clinic → accepted, and a regression asserting `staff_id=None`
issues only **1** `db.execute` (the new check is skipped entirely for clinic-wide rules). The tests
also assert rejection happens *before* the duplicate pre-check. The file's docstring is honest that a
mocked session cannot truly distinguish "foreign tenant" from "unknown" — the real guarantee is the
`clinic_id` predicate, which I verified by reading. Integration coverage carried to the Test Agent.

## M1 + M2 [MAJOR] — Claw-back rework: correct ✅

Per the user decision relayed by the coordinator (claw-back reverses at the same rate it was earned at).

**Precedence is provably identical to the earning path** — the claw-back does not reimplement
resolution, it calls the *same* pure functions with the same argument order:
- service: `commission_service.resolve_service_type_rate(staff_id, service_type_id, staff_service_type_rates, service_type_rates)`
- medicine: `commission_service.resolve_medicine_rate(staff_id, staff_medicine_rates, medicine_rate)` + `if not rate: continue`

`aggregate_commission` uses byte-identical calls. Divergence is now structurally impossible rather
than maintained by hand.

**`doctor_to_staff` construction matches the earn path exactly** — `payroll_service.py:583-593` filters
`clinic_id`, `is_deleted IS FALSE`, `user_id IN (...)`; `commission_service.py:281-285` uses the same
three predicates. No `employment_status` drift between them. Still clinic-scoped. `staff_id` is
resolved once outside the service-line loop (all service lines share one visit doctor) and per-row
inside the medicine loop (each line has its own prescriber) — both correct.

**`load_rate_maps` promotion did not change earn-path behavior** — verified line by line: the diff is a
pure rename (`_load_rates`→`load_rate_maps`, `_RateMaps`→`RateMaps`) plus a docstring. The row query,
the split loop and the returned maps are unchanged, and `compute_commission` is the only other caller.

**TASK-128 regression safety re-derived by hand, not assumed.** With no per-staff rows configured
(`doctor_to_staff`/override maps empty or non-matching):
- service: `resolve_*` falls straight through to `general_rates.get(service_type_id)`, then
  `if rate is None: continue` — identical to the old `service_type_rates.get(...)` lookup.
- medicine: old code short-circuited the whole loop on a falsy `medicine_rate`; new code resolves to
  that same falsy value per row and `continue`s each one — same result set, same amounts.
All 5 original `test_aggregate_clawback_*` tests still pass **unedited**, which is the strongest
available evidence of byte-for-byte preservation.

**The round-1 dict-overwrite hazard is now prevented structurally**, not by a filter that could drift:
`RateMaps.service_type_rates` only ever receives `staff_id IS NULL` rows because `load_rate_maps`
splits on `r.staff_id is not None` at load time. Dropping the explicit `staff_id.is_(None)` WHERE
clause is therefore safe — I checked this specifically, since removing a guard I had just approved is
exactly the kind of change that silently reintroduces a bug.

**The symmetry test is meaningful, not tautological** (M2 closed): 
`test_clawback_and_earning_symmetry_at_staff_override_rate` feeds one override configuration
(15% override vs 10% clinic-wide) through `aggregate_commission` *and* `aggregate_clawback`
independently and asserts both land on 150,000 — it would fail if either side regressed to the
clinic-wide rate. Plus three genuinely distinct edge cases: no-override fallback, a mixed batch where
two prescribers on one invoice resolve to *different* rates (20% vs 5% — no blending), and an unmapped
doctor who correctly cannot pick up another staff member's 99% override.

Observation, not a finding: `load_rate_maps` and the staff query now run before the
`if not clawback_by_doctor: return 0` early exit, so a void/refund that claws back nothing costs one
extra query. In exchange the previous duplicate staff query is gone, so the net query count is equal
or better on the path that matters. Fine on this rare, savepoint-wrapped path.

## m1, m2, n1 — Fixed and verified ✅

- **m1** — `payroll_service.py:14-17` now reads "Overtime applies to monthly/hourly only …; allowance,
  attendance bonus and late penalty apply to ALL FOUR pay types." Matches lines 122-125 and the test.
- **m2** — `0077:129-136` reordered: `DELETE FROM commission_rule WHERE staff_id IS NOT NULL`, then
  drop index, then drop column, and only *then* recreate the two 0073 indexes. The duplicate-key abort
  is gone, and the recreated DDL is still byte-identical to 0073's original. The data-loss consequence
  (override rows discarded on downgrade — unavoidable, they have nowhere to live pre-0077) is
  documented as a distinct caveat in the module docstring alongside the `pay_type` one. Good.
- **n1** — the 118-char line is wrapped across 4 lines; no behavior change.

## Skips (n2, n3, m3, m4, m5) — 4 accepted, 1 escalated

- **n2** — **Accepted.** The argument is better than my finding: `PAY_TYPE_LABEL_FALLBACK` is only
  reachable if the `hr` namespace fails to load, and deleting it would render a raw `per_session` enum
  to the user in that case. Keeping a safety net beats cosmetic tidiness. Withdrawn.
- **n3** — **Accepted.** I explicitly requested no action; it was recorded so the pre-existing
  TASK-128 semantics aren't later mistaken for a regression.
- **m3** (i18n debt) — **Accepted as carried-forward debt.** Matches my own recommendation. Both pages
  still have zero `useTranslation`; converting ~12 strings mid-feature would be a worse change than
  the debt. Must be picked up by whichever pass converts `CommissionKpiConfigPage` /`StaffFormPage`.
  The 7 keys that were added remain correctly present in both `vi` and `en`.
- **m4** (payslip rate-source indicator) — **⚠️ ESCALATED, still open.** The skip reasoning is correct
  — this needs a user decision, not a code change — but no decision has come back. The coordinator
  relayed a user decision on claw-back only. `task.md:49` AC ("tỷ lệ commission áp dụng — riêng hay
  chung") is therefore **still literally unmet**. This does not block code review (the code matches the
  authoritative plan, which omits the field), but it **must not close silently**: the user has to
  either accept the deviation or open a follow-up task before TASK-138 is marked DONE. Flagged again in
  `review-to-test.md` so it survives into the testing and documentation phases.
- **m5** (integration coverage) — **Accepted, and now higher priority.** The claw-back rework changed
  real DB-orchestration wiring in `_compute_and_record_clawback` (candidate-doctor gathering, query
  ordering) that unit tests cannot reach. Headline item for the Test Agent.

## Verification performed (fix round 1)

| Check | Result |
|---|---|
| BE unit tests (same Docker command) | **1117 passed, 12 failed in 39.0s** |
| Failure-list comparison vs round 1 | `diff` of the two sorted `FAILED` lists → **identical, 12 each** |
| New tests | +8 vs round 1 (1109→1117), all passing: 4 clinic-scope + 4 claw-back rate resolution |
| `ruff check` on changed files (`app/modules/hr`, migration 0077, 4 test files) | **All checks passed** |
| `ruff` claim cross-check | `tests/unit` shows 142 errors — confirmed **pre-existing**: identical 142 on the clean `_dev-be` worktree, none in TASK-138 files |
| Leftover `CommissionRule` import in `payroll_service` | grep → none; import cleanly removed |

**Zero new failures.** The 12 remaining are the same known pre-existing dev set (email templates,
erasure, feature flags, medicine_stock ×4, rls_helpers ×2, tenancy_middleware ×3) — none in
hr/payroll/commission.

Not re-run by me: FE suite (no FE files changed this round) and the live-Postgres migration cycle
(the implementer reports re-verifying it against a disposable container, this time seeding the exact
clinic-wide + per-staff collision that used to abort the downgrade; the reordered DDL is correct on
inspection). Both are covered by the testing focus list in `review-to-test.md`.

## Final tally

| Severity | Round 1 | Now |
|---|---|---|
| Blocking | 1 (R1) | **0** — fixed |
| Major | 2 (M1, M2) | **0** — both closed by the claw-back rework |
| Minor | 5 | 2 open: **m3** (i18n debt, carried forward), **m4** (⚠️ open AC — needs user decision) |
| Nit | 3 | 0 — n1 fixed, n2 withdrawn, n3 informational |

Nothing blocking remains. **APPROVED → IN_TESTING.**
