# Handoff: TASK-128 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW

## Summary

Implemented payroll commission (thủ thuật % theo `service_type` + thuốc % doanh thu), KPI bonus (theo mức đạt doanh số), and automatic claw-back (void/refund of a locked period writes a negative adjustment to the next period), layered on top of the existing base/OT payroll engine (0058). Added a new `/hr/commission-kpi` config page and extended `PayrollPage.tsx`'s breakdown.

## Files Changed

### Backend (`_feat128-be`, branch `feature/TASK-128`)
- `alembic/versions/0073_payroll_commission_kpi.py`: new — `commission_rule`, `kpi_target`, `payroll_adjustment` tables + RLS + grants. `down_revision="0072"`, confirmed single head (`alembic heads` → `0073 (head)`).
- `app/modules/hr/models/commission_rule.py`, `kpi_target.py`, `payroll_adjustment.py`: new models.
- `app/modules/hr/models/__init__.py`: registered the 3 new models.
- `app/modules/hr/services/commission_service.py`: new — `aggregate_commission` (pure) + `compute_commission` (DB-orchestrating: `visit_service` join `visit`→`doctor_id` grouped by `service_type_id`, `prescription_item` join `prescription`→`doctor_id`; maps doctor `user.id`→`staff_profile.id`).
- `app/modules/hr/services/kpi_service.py`: new — `compute_bonus` (pure, linear achievement-ratio formula) + `compute_kpi_bonuses`.
- `app/modules/hr/services/commission_config_service.py`: new — CRUD for commission_rule/kpi_target.
- `app/modules/hr/services/payroll_service.py`: modified — added `_empty_slip`, `_apply_commission_kpi_clawback`, `aggregate_clawback` (all pure), `is_period_posted`, `next_period`, `_get_clawback_totals`, `record_invoice_clawback`; `compute_payroll` now layers commission/KPI/claw-back onto every payslip and includes commission-only staff (`_empty_slip`); `post_payroll_to_expense` now marks the period's adjustments `applied=true`. `_compute_one` itself is **unchanged** (existing unit tests untouched).
- `app/modules/billing/services/invoice_service.py`: modified — `void_invoice`/`refund_invoice` now call `payroll_service.record_invoice_clawback` (best-effort, mirrors the existing `_release_pharmacy_reservations`/`_undispense_dispensed_items` try/except pattern).
- `app/modules/hr/schemas/hr_schemas.py`: modified — `Payslip` gets 4 new fields (`procedure_commission`, `medicine_commission`, `kpi_bonus`, `clawback_adjustment`); added `CommissionRule*`/`KpiTarget*` schemas.
- `app/modules/hr/api/routes.py`: modified — added `/hr/commission-rules` + `/hr/kpi-targets` CRUD (all gated `payroll.manage`).
- `tests/unit/test_commission_service.py`, `test_kpi_service.py`, `test_payroll_commission_kpi_clawback.py`: new unit tests (pure logic).

### Frontend (`_feat128-web`, branch `feature/TASK-128`)
- `src/modules/hr/types.ts`: extended `Payslip`; added `CommissionRule*`/`KpiTarget*` types.
- `src/modules/hr/api.ts`: added commission-rules + kpi-targets CRUD calls.
- `src/pages/hr/PayrollPage.tsx`: added 4 breakdown columns (CK thủ thuật/CK thuốc/KPI/Điều chỉnh) + a link to the new config page.
- `src/pages/hr/CommissionKpiConfigPage.tsx`: new page — service-type rate table, medicine rate card, KPI target table (month picker + CRUD modals, reuses `StaffPicker`).
- `src/router/index.tsx`, `src/components/shell/Sidebar.tsx`: new route `/hr/commission-kpi` + sidebar entry (`payroll.manage`).
- `src/locales/vi/hr.json`, `src/locales/en/hr.json`: added `nav.commissionKpi`.
- `src/tests/hr/CommissionKpiConfigPage.test.tsx`, `PayrollPage.test.tsx`: new FE tests.

## Migration

`0073_payroll_commission_kpi.py`, `down_revision="0072"`. Confirmed single head both via `alembic heads` (static, no DB) and via a full `alembic upgrade head` run from scratch against an ephemeral Postgres (see Test Results) — chain resolves cleanly to `0073 (head)`.

## Commission / KPI / Claw-back Approach

- **Procedure commission**: `visit_service` (status != 'cancelled') joined to `visit` (for `doctor_id`) and `service` (for `service_type_id`), revenue = `quantity*unit_price - discount_amount`, grouped by `(doctor_id, service_type_id)`, rate from `commission_rule(rule_type='service_type')` keyed on `service_type_id`. Recipient = **`visit.doctor_id`** (locked decision — NOT `performed_by_user_id`).
- **Medicine commission**: `prescription_item` (unit_price not null) joined to `prescription` (status != 'cancelled'), revenue = `quantity*unit_price`, grouped by `doctor_id` (= `prescription.doctor_id`, the prescribing doctor — used directly, since the model already carries it; did not need to go through `visit.doctor_id` as the plan's phrasing suggested), one clinic-wide rate from `commission_rule(rule_type='medicine')`.
- **Doctor → staff mapping**: bulk query `staff_profile.user_id IN (doctor_ids)` → `{user_id: staff_id}`. Unmapped doctors are **skipped** from payroll (never crash) and surfaced via `CommissionResult.unmapped_doctors` + a `commission.unmapped_doctors` warning log — no dedicated "unmapped" UI/endpoint was built (documented as a known gap in the functional design).
- **KPI**: `bonus = bonus_amount * min(1, actual_revenue / revenue_target)` — linear achievement ratio, capped at 100%, 0 if target/revenue <= 0. `actual_revenue` = the same commission-eligible revenue computed above (not all doctor revenue) — a deliberate v1 simplification to avoid a second revenue query; documented as a known limitation.
- **Claw-back**: `record_invoice_clawback(db, clinic_id, invoice, reason)` — resolves the invoice's visit (`doctor_id`, `visit_date`), checks `is_period_posted` (the only "lock" signal: existence of the `Expense(category='salary', ...)` row `post_payroll_to_expense` writes), and if locked, re-aggregates the invoice's own `invoice_line` rows (join `visit_service`/`prescription_item`) through the *current* rate config to get the commission that invoice generated, then writes a negative `payroll_adjustment` per affected staff for `next_period(source_period)`. Idempotent via a pre-insert existence check + a DB partial-unique index on `(clinic_id, staff_id, source_ref)`. Wrapped in try/except — never blocks void/refund (mirrors existing `_release_pharmacy_reservations` pattern in `invoice_service.py`).

## Test Commands + Results

All commands run via ephemeral `docker run --rm` against `docker-api:latest` (BE, host has Python 3.10 but project requires 3.11) / local `node`/`npm` (FE, host has Node 20) — **no w2e-port stack touched**.

**BE unit tests** (pure logic, no DB):
```
docker run --rm -v "<worktree>:/app" -w /app docker-api:latest python -m pytest tests/unit -q
```
→ **1053 passed**, 12 failed (all in `test_email.py`, `test_erasure_service.py`, `test_feature_flags.py`, `test_medicine_stock_status.py`, `test_rls_helpers.py`, `test_tenancy_middleware.py` — verified **pre-existing** on the unmodified branch via `git stash -u` + re-run: identical 12 failures, 1029 passed baseline vs 1053 now — TASK-128 added 24 new passing tests, zero regressions, zero new failures).

**BE lint**: `ruff check` on all new/changed files → all clean.

**BE migration** (ephemeral Postgres 15-alpine, isolated Docker network, no published ports):
- `alembic upgrade head` from scratch (0001→0073): succeeds, no errors.
- Re-run `alembic upgrade head`: idempotent no-op (exit 0).
- `alembic downgrade -1` then `alembic upgrade head`: both succeed (0073 downgrade/upgrade round-trip clean).
- Inspected `commission_rule`/`kpi_target`/`payroll_adjustment` via `\d` — columns, FKs, CHECK constraints, partial unique indexes, and `FORCE ROW LEVEL SECURITY` policies all present as designed.
- `python -c "from app.main import app"` → imports cleanly, 35 routes registered.

**BE real-DB smoke test** (ad-hoc script, deleted after use — not part of the deliverable): seeded a minimal clinic/user/staff_profile/visit/service_type/service/visit_service/prescription/prescription_item/commission_rule/kpi_target via raw SQL against the ephemeral Postgres, then called `commission_service.compute_commission` and `kpi_service.compute_kpi_bonuses` directly (production code, real asyncpg connection). Result: procedure commission 100,000 (10% of 1,000,000), medicine commission 2,500 (5% of 50,000), KPI bonus 1,000,000 (revenue 1,050,000 ≥ target 500,000 → full bonus) — all matched expected values exactly. This exercises the raw SQL joins that the pure-logic unit tests can't reach.

**FE type-check**: `npx tsc --noEmit` → clean.
**FE lint**: `npx eslint` on new/changed files → clean (one `react-hooks/exhaustive-deps` warning fixed during implementation).
**FE tests**: `npx vitest run` → **1153 passed**, 3 failed (`doctor/QueuePage.test.tsx` ×2, `auth/ForgotPasswordPage.test.tsx` ×1 — verified pre-existing via `git stash -u` + re-run: identical 3 failures on the unmodified branch, unrelated to HR/payroll). TASK-128 added 10 new passing tests (`CommissionKpiConfigPage.test.tsx`, `PayrollPage.test.tsx`), zero regressions.

**Not run this session** (documented as unverified, with reason):
- `tests/integration/test_alembic.py` and the rest of `tests/integration/` (require the project's own persistent dev DB with baseline data — not the ephemeral one used above, and out of scope to stand up a second full stack here). The migration itself was independently verified via the ephemeral Postgres run above.
- End-to-end billing void/refund → claw-back through the actual `invoice_service.void_invoice`/`refund_invoice` HTTP path (would need a full invoice/payment fixture chain). The claw-back **aggregation logic** (`aggregate_clawback`) is unit-tested in isolation; the join SQL mirrors patterns already used elsewhere in `invoice_service.py` and was reviewed manually.
- FE Playwright E2E for the new page/columns.

## Decisions

- Doctor→staff mapping uses `staff_profile.user_id` (nullable) exactly per the locked plan; `performed_by_user_id` was not touched.
- KPI revenue scope = commission-eligible revenue only (see functional design §8.1/limitations) — a deliberate simplification, flagged for review since it means an unconfigured `service_type` rate silently excludes that revenue from KPI too.
- Claw-back recomputes commission using **current** rates, not a snapshot from the original payroll run — flagged as a known limitation (functional design §8.3, BR-010).
- `payroll_adjustment.applied` is bookkeeping only; `compute_payroll` always sums by `apply_period` regardless, to keep it a pure function of current data.
- A staff member with no `base_salary`/`hourly_rate` but non-zero commission/KPI/claw-back now gets a payslip (`_empty_slip`) instead of being silently dropped — this is a behavior change from the pre-TASK-128 payroll engine, called out explicitly since it could surprise anyone expecting the old "no salary basis = not on payroll" invariant to hold universally.

## Blockers

None. Both worktree branches pushed (see below).

## Confirm

- No changes to `main` or the w2e stack (ports 9999/5434/5436/6380/6382) — all verification used ephemeral, unpublished-port Docker containers/networks that were torn down after use.
- `feature/TASK-128` pushed in both `_feat128-be` and `_feat128-web`.
- NOT merged to `dev` — left for manager/reviewer to coordinate.

## Areas for Review Focus

1. KPI-revenue-scope simplification (§ Decisions) — confirm acceptable for v1 or needs a separate revenue query.
2. Claw-back "current rate" recompute (BR-010) — confirm acceptable or needs rate snapshotting.
3. `_empty_slip` behavior change (commission-only staff now appear on payroll) — confirm this is desired, not a regression.
4. Unmapped-doctor commission (no dedicated UI/endpoint, log-only) — confirm acceptable for v1.
