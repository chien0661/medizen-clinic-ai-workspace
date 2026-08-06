# Test Cases: TASK-138 — Payroll per_session/per_shift + per-staff commission

**Test Agent** | **Date:** 2026-08-07
**Branch:** `feature/TASK-138-payroll-session-shift` — BE `cebf0bd`, FE `4bf1b55`

Legend: **Actual** = observed result of executing the scenario against the branch code. All scenarios executed; none skipped unless noted in the Skipped section of the test report.

## A. BE Unit Regression (full suite, Docker `clinic_e2e-api` image)

| ID | Mô tả | Steps | Expected | Actual | Verdict |
|----|-------|-------|----------|--------|---------|
| BE-U1 | Full BE unit suite regression | `pytest tests/unit -q` inside Docker | Only the 12 documented pre-existing failures (email templates, erasure, feature_flags, medicine_stock×4, rls_helpers×2, tenancy_middleware×3); all TASK-138 unit tests (per_session/per_shift, resolve-rate, clinic-scope validation, claw-back symmetry, rate/source m4 tests) pass | 1133 passed, 12 failed — failing test IDs match the pre-existing list exactly (verified by diff) | PASS |

## B. FE Unit Regression (full suite, vitest)

| ID | Mô tả | Steps | Expected | Actual | Verdict |
|----|-------|-------|----------|--------|---------|
| FE-U1 | Full FE unit suite regression | `npx vitest run --silent` on host | Only the 4 documented pre-existing failures (AttendanceWidget "M-14" date-flaky, QueuePage×2, ForgotPasswordPage×1) | 1260 passed, 4 failed — failing test names match the pre-existing list exactly (`ForgotPasswordPage > handles 404 gracefully`, `QueuePage > shows empty state`, `QueuePage > renders a visit card`, `AttendanceWidget > M-14`) | PASS |

## C. DB Integration — Payroll Engine (disposable Postgres, alembic 0001→0077)

| ID | Mô tả | Steps | Expected | Actual | Verdict |
|----|-------|-------|----------|--------|---------|
| INT-01 | `per_session` full + half days | Seed staff `pay_type=per_session, session_rate=300000`; 20× `AttendanceDay(status=present)` + 3× `status=half` in 2026-08; run `compute_payroll` | `worked_days=21.5`, `base_earned=300000×21.5=6,450,000`, `overtime_pay=0` | worked_days=21.5, base_earned=6,450,000.0, overtime_pay=0.0 | PASS |
| INT-02 | `per_session` with NO attendance-grid data, non-zero legacy check-in count | Seed staff `per_session, session_rate=300000`, zero `AttendanceDay` rows, but 10× `TimeLog` check-ins (drives legacy `worked_shifts`) | Payslip pays **0** buổi/0 earned — must NOT fall back to the legacy TimeLog-derived count | worked_days=0.0, base_earned=0.0 despite legacy count=10 | PASS |
| INT-03 | `per_shift` counts only `completed` | Seed staff `per_shift, shift_rate=200000`; 5× `Shift(status=completed)` + 1× `cancelled` + 1× `scheduled` + 1× `on_leave` in-period | `completed_shifts=5`, `base_earned=1,000,000`, cancelled/scheduled/on_leave excluded | completed_shifts=5, base_earned=1,000,000.0 | PASS |
| INT-04 | Rate ≤ 0, no commission/KPI/adjustment | Staff `per_session, session_rate=0`, has attendance but no other pay component | Staff dropped off payroll entirely (no payslip row) | slip is None | PASS |
| INT-05 | Rate ≤ 0 but earns commission → `_empty_slip` | Staff `per_session, session_rate=0`, linked to a doctor user; 1 full + 1 half attendance day; clinic-wide 10% commission rule; one visit/service revenue 500,000 | Slip present via `_empty_slip`: `base_earned=0`, `worked_days=1.5` (from grid), `procedure_commission=50,000` | base_earned=0.0, worked_days=1.5, procedure_commission=50,000.0 | PASS |
| INT-06 | Allowance/attendance-bonus/late-penalty apply to new pay types; OT forced to 0 | Staff `per_shift`, `allowance=50000`, `ot_multiplier=2.0`, `attendance_bonus=20000`, `late_penalty=10000`; 3 completed shifts; 1 `TimeLog` with `late_minutes=15, ot_hours=3.0` | `overtime_pay=0` despite `ot_hours`+multiplier set; `allowance=50000` applied; `late_penalty_total=10000`; `attendance_bonus=0` (late disqualifies) | overtime_pay=0.0, allowance=50000.0, late_penalty_total=10000.0, attendance_bonus=0.0 | PASS |
| INT-07 | `monthly`/`hourly` regression, leftover `session_rate`/`shift_rate` populated but unused | Staff A `monthly, base_salary=13,000,000` with `session_rate=999999, shift_rate=999999` set; Staff B `hourly, hourly_rate=100000` with same leftover rates; B has 8h logged | A: `base_earned=13,000,000`; B: `base_earned=800,000` — both unaffected by the populated but-inapplicable rate fields | A base_earned=13,000,000.0; B base_earned=800,000.0 | PASS |
| INT-08 | Period boundaries (first/last day of month, next-month exclusion) | Staff `per_session, session_rate=100000`; attendance on 2026-08-01, 2026-08-31 (both present), and 2026-09-01 (present, next month) | `worked_days=2.0` — first+last day of the queried month counted, next-month day excluded | worked_days=2.0 | PASS |
| INT-09 | Per-staff commission override vs clinic-wide fallback + payslip traceability (m4) | Clinic-wide service_type rule 10%; staff_a override 15% on same service_type; staff_a and staff_b (no override) each generate 1,000,000 revenue via a real visit+visit_service | staff_a: `procedure_commission=150,000`, `procedure_rate_percent=15.0`, `procedure_rate_source=staff_override`; staff_b: `procedure_commission=100,000`, `procedure_rate_source=clinic_default` | Exactly as expected for both staff | PASS |
| INT-10 | Claw-back symmetry at override rate + mixed batch | Clinic-wide service 10%/medicine 5%; staff_a override service 15%/medicine 20%; one invoice: 1,000,000 service (doctor A) + 100,000 medicine (prescriber A) + 100,000 medicine (prescriber B, no override); July payroll posted; call `record_invoice_clawback` (void/refund equivalent) | staff_a clawed back **-170,000** (15%+20%, override rate — not clinic-wide 10%/5%); staff_b clawed back **-5,000** (clinic-wide medicine rate, independent of staff_a) | staff_a=-170000.00, staff_b=-5000.00 | PASS |
| INT-11 | Claw-back idempotency / no `PendingRollbackError` | Call `record_invoice_clawback` a second time for the same invoice, then `db.commit()` | 0 new rows created, no exception, outer commit succeeds | created=0, commit succeeded | PASS |
| INT-12 | Claw-back: period not posted | Invoice for an unposted month → `record_invoice_clawback` | 0 adjustments, early return, no crash | created=0 | PASS |
| INT-13 | Claw-back: unmapped doctor (no `staff_profile` at all) | Doctor user with zero linked `staff_profile` rows; posted period; invoice with that doctor's service revenue | 0 adjustments (no `staff_id` to attribute to), `clawback_unmapped_doctor` code path hit, no crash | created=0, no exception | PASS |
| INT-14 | TASK-128 regression — zero per-staff rules | Clinic with only a clinic-wide 10% service rule (no overrides anywhere); posted period; invoice void | Claw-back amount **byte-identical** to pre-TASK-138 behavior: `-100,000` (10% of 1,000,000) | -100000.00 | PASS |
| INT-15 | Staff without login account (`user_id=NULL`) — full `per_session` flow | Nurse `staff_profile` with `user_id=NULL`, `pay_type=per_session, session_rate=250000`; 2 full + 1 half attendance day | `worked_days=2.5`, `base_earned=625,000`, appears on payroll normally | worked_days=2.5, base_earned=625,000.0 | PASS |

## D. Migration 0077 — Real Data

| ID | Mô tả | Steps | Expected | Actual | Verdict |
|----|-------|-------|----------|--------|---------|
| MIG-01 | Fresh upgrade 0001→0077 | `alembic upgrade head` on empty disposable Postgres | All 77 migrations apply cleanly; `staff_profile.pay_type` widened to `VARCHAR(20)`; `session_rate`/`shift_rate` added; `commission_rule.staff_id` + FK + `ix_commission_rule_staff_id` added; both partial unique indexes rebuilt with `COALESCE(staff_id, zero-uuid)` | Confirmed via `\d staff_profile`, `\d commission_rule`, `pg_indexes` — matches design exactly | PASS |
| MIG-02 | Collision data coexistence | Insert clinic-wide service_type rule (10%) + per-staff override (15%) on the SAME `(clinic_id, service_type_id)`; same for medicine (5% / 20%) | Both rows coexist without violating the rebuilt partial unique indexes | 4 rows inserted successfully | PASS |
| MIG-03 | Downgrade with collision data present | `alembic downgrade -1` on the DB from MIG-02 (no `per_session`/`per_shift` staff rows present) | Downgrade succeeds (previously aborted pre-fix-round-1's m2 fix); per-staff override rows discarded; clinic-wide rows survive; old 0073 indexes restored; `pay_type` narrowed back to `VARCHAR(10)` | Downgrade succeeded; surviving rows: service_type 10%, medicine 5% (overrides gone); `uq_commission_rule_clinic_service_type`/`_medicine` present, no `staff_id` column | PASS |
| MIG-04 | Re-upgrade after downgrade | `alembic upgrade head` again on the DB from MIG-03 | Succeeds cleanly, schema matches MIG-01 again | Succeeded | PASS |
| MIG-05 (informational, not a bug) | Downgrade with `per_session`/`per_shift` staff data present | `alembic downgrade -1` on a DB where staff rows hold `pay_type='per_session'` (11 chars) | Fails with `StringDataRightTruncationError` on the `pay_type` narrowing step — **this is the migration's own documented, accepted behavior** ("will fail... expected, since those values have nowhere to fit in the old schema") | Failed exactly as documented | PASS (matches spec; not filed as a bug) |

## E. API Surface / RBAC / Tenancy (real Postgres + Redis, httpx against `app.main:app`)

| ID | Mô tả | Steps | Expected | Actual | Verdict |
|----|-------|-------|----------|--------|---------|
| API-01 | Create rule with valid same-clinic `staff_id` | `POST /hr/commission-rules` with `staff_id` = a staff in the caller's clinic | 201, response echoes `staff_id` | 201, staff_id matches | PASS |
| API-02 | Create rule with cross-clinic `staff_id` | `POST` with a `staff_id` belonging to a different clinic | 404 (not 500); no row written | 404; DB row count for that staff_id = 0 | PASS |
| API-03 | Create rule with non-existent `staff_id` | `POST` with a random UUID | 404 (not 500) | 404 | PASS |
| API-04 | Create clinic-wide rule (`staff_id=None`) unaffected | `POST` with `staff_id: null` | 201, `staff_id: null`, no extra validation query triggered | 201, staff_id null | PASS |
| API-05 | Staff without login account is a valid override target | `POST` with `staff_id` = a nurse `staff_profile` (`user_id=NULL`) | 201, accepted like any other staff | 201, staff_id matches nurse | PASS |
| API-06 | `staff_id` immutable via PATCH | `PATCH` an existing rule with `{"rate_percent": 18, "staff_id": <other>}` | 200; `rate_percent` updated; `staff_id` **unchanged** (field not on `CommissionRuleUpdate` schema) | 200; rate_percent=18; staff_id unchanged | PASS |
| API-07 | Delete override reverts staff to clinic-wide | Create clinic-wide + override on same service_type; `DELETE` the override; `GET ?staff_id=<staff>` | Filtered list empty after delete (staff reverts to fallback on next payroll run) | Empty list after delete | PASS |
| API-08 | `GET ?staff_id=` filter + tenant isolation | Clinic A has 1 clinic-wide + 1 override rule; `GET ?staff_id=<staff>` vs unfiltered vs Clinic B's view | Filtered → 1 row (the override); unfiltered → 2 rows; Clinic B → 0 rows (never sees A's data) | Filtered=1, unfiltered=2, clinic B=0 | PASS |
| API-09 | RBAC — `payroll.manage` required | Login as a `receptionist` (no `payroll.manage`); call all 4 commission-rule endpoints (GET/POST/PATCH/DELETE) | 403 on every endpoint | 403 on all 4 | PASS |

## F. Business Rule — Staff Without Login Account

| ID | Mô tả | Steps | Expected | Actual | Verdict |
|----|-------|-------|----------|--------|---------|
| BR-01 | Nurse (`user_id=NULL`) configured for `per_session` pay, produces correct payslip (DB-engine level) | Same as INT-15 | worked_days=2.5, base_earned=625,000, on payroll | Matches | PASS |
| BR-02 | Nurse (`user_id=NULL`) selectable as a per-staff commission override target (API level) | Same as API-05 | 201, accepted | Matches | PASS |
| BR-03 | Automatic commission remains doctor-account-only (unchanged TASK-128 limit) | Confirmed by design: `aggregate_commission`/`compute_commission` resolve recipients via `staff_profile.user_id` — a staff with `user_id=NULL` never appears as a commission recipient automatically; nurses use `payroll_adjustment` (TASK-128, untouched) | No regression — this task does not change recipient attribution, only the rate resolved for an already-attributed recipient | Confirmed via code (commission_service module docstring, unchanged locked decision) + no `_load_rates`/`aggregate_commission` recipient-side code path touched | PASS |

## G. FE-Specific (covered by FE unit suite, see B — no additional Playwright E2E; see test report "Skipped")

FE behavior (StaffFormPage pay-type selects, PayrollPage breakdown/badges, CommissionKpiConfigPage per-staff section) is covered by the 21 new/modified FE unit tests already included in the FE-U1 full-suite run (`StaffFormPage.test.tsx`, `PayrollPage.test.tsx`, `CommissionKpiConfigPage.test.tsx`, `i18n-hr.test.ts`) — all pass, zero new failures. No separate row added here to avoid double-counting; see test-report.md §"FE" for the itemized list.

---

**Total scenarios:** 15 (DB-integration) + 9 (API) + 3 (business rule, 2 of which cross-reference DB/API) + 5 (migration) + 2 (full-suite regressions) = **34 distinct scenarios**, all PASS.
