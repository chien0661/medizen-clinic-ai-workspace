# Code Review Report — TASK-139

**Task**: Payroll — xuất bảng lương Excel + phiếu lương PDF từng nhân viên
**Reviewer**: Code Review Agent
**Date**: 2026-08-07
**Branch**: `feature/TASK-139-payroll-export` (branched from `feature/TASK-138-payroll-session-shift`)
**Commits reviewed**: BE `fd020da` (`_feat139-be`), FE `d59942f` (`_feat139-web`) — diffed against the TASK-138 base (`cebf0bd` / `4bf1b55`)
**Decision**: **APPROVED** → IN_TESTING

Findings: **1 Major** (systemic, non-blocking — follow-up required) · **5 Minor** · **1 Nit**.
Nothing blocking. The feature is additive (BE diff is +638 lines across 4 files, all new code paths),
correctly reuses the existing compute engine and export/print infrastructure, and is well tested.

---

## Verification performed

| Check | Command | Result |
|---|---|---|
| BE unit tests | `docker run --rm -v _feat139-be:/work -w /work clinic_e2e-api python -m pytest tests/unit -q` | **1146 passed, 12 failed in 67.0s** |
| BE lint | `ruff check app/modules/hr tests/unit/test_payroll_export.py tests/integration/test_payroll_export_e2e.py` | **All checks passed** |
| FE tests | `npx vitest run --silent` | **1282 passed, 3 failed** (138 files) |
| i18n vi/en parity | flattened-key set diff over `vi/hr.json` vs `en/hr.json` | **vi-only: none · en-only: none**; 39 `payroll.payslip.*` keys in both |
| Header injection | direct `build_xlsx_response` + `h11` probe | see m1 — reachable, but blocked at the h11 layer |
| Shared e2e DB pollution | live `psql` against `clinic_e2e_postgres` | **leak confirmed** — see M1 |

**BE failure list**: the same 12 pre-existing failures as TASK-138 (`test_email` ×1,
`test_erasure_service` ×1, `test_feature_flags` ×1, `test_medicine_stock_status` ×4,
`test_rls_helpers` ×2, `test_tenancy_middleware` ×3) — none in hr/payroll/export. **Zero new failures**;
the 13 new `test_payroll_export.py` tests pass.

**FE failure list**: `QueuePage` ×2 + `ForgotPasswordPage` ×1 — the documented pre-existing set.
**Zero new failures**; the 21 new tests pass.

---

## Focus-area rulings

### 1. Data correctness — no drift ✅

`export_payroll_xlsx` (`payroll_service.py:495-517`) calls `compute_payroll(db, clinic_id, month)` —
the *same* function `GET /hr/payroll` uses — and feeds its `payslips` straight into
`build_payroll_export_rows`. There is no second query or duplicated arithmetic that could drift.
`test_export_monthly_staff_matches_payroll_computation` asserts export cells against the payroll API
response for the same period.

Money and counts are appended as raw `int`/`float`, never pre-formatted strings, so Excel stores them
as real numbers (task.md's accounting requirement). `None` renders as `""` (blank) rather than a
misleading `0` — `test_monthly_hourly_blank_session_and_shift_rate` and
`test_no_commission_this_period_blank_rate_and_source` cover this.

Header/row alignment verified by hand: **27 headers, 27 row elements**, in matching order — and
`test_headers_and_row_length_match` guards it.

### 2. Security ✅ (one input-validation gap, m1)

- **RBAC**: `dependencies=[Depends(require_permission("payroll.manage"))]` — same permission as every
  other payroll endpoint. `test_export_requires_payroll_manage_permission` proves a receptionist gets
  403, `test_export_requires_auth` proves 401/403 unauthenticated.
- **Tenant scoping**: `clinic_id` comes from `_clinic_id()` (tenancy middleware), never from a
  client-supplied parameter, and `compute_payroll` is clinic-scoped throughout (verified in the
  TASK-138 review). One clinic cannot export another's payroll.
- **PII**: the export exposes exactly the fields the payroll screen already shows (staff_code,
  full_name, salary breakdown) — no phone/DOB/address, no `user` join. Nothing beyond the screen.
- **Formula injection**: `build_xlsx_response` runs every cell through `_neutralize()`, so a staff
  name like `=cmd|...` is written as text. Inherited from the shared helper — correct by reuse.
- **Content-Disposition**: the filename is `bang_luong_<month>` — ASCII-safe, so the UTF-8
  `filename*` concern the plan raised does not apply. But `month` is unvalidated — see **m1**.

### 3. Route path `/api/v1/payroll/export` — **consistent enough, do NOT move** ✅

I enumerated every path on this router (`prefix="/api/v1"`). The module already runs two conventions
side by side, and the deciding fact is that **every existing export endpoint is un-prefixed**:

```
/staff/export   /attendance/export   /leave-requests/export
/recurring-schedules/export   /shift-templates/export      ← all 5 existing exports
/hr/payroll   /hr/timesheet   /hr/commission-rules  ← the newer TASK-128/138 additions
```

So `/payroll/export` matches the **export-endpoint** convention exactly, even though it differs from
its immediate `/hr/payroll` siblings. Combined with task.md specifying the path literally, there is no
case for changing it. No routing collision (`/payroll/export` vs `/hr/payroll` are distinct), and RBAC
is dependency-based, not path-based, so nothing about the prefix weakens authorization. **Closed — no
action.**

### 4. Frontend ✅

- **No second fetch**: `PayrollPage` passes the already-fetched row object
  (`<PrintPayslipModal payslip={printingSlip} …>`), and `PrintablePayslip` renders purely from that
  prop. Zero chance of the printed slip disagreeing with the on-screen row. (`PrintPayslipModal` does
  fetch clinic settings for the letterhead — that is header chrome, not payslip data, and matches
  `PrintVisitSlipModal`.)
- **Legacy pay types**: session/shift rows are gated on `!= null`, so monthly/hourly payslips omit them
  entirely instead of showing a misleading `0` — exactly what the plan asked for. `worked_days` vs
  `total_hours` vs `completed_shifts` are each shown only for the pay types where they mean something.
- **i18n**: full vi/en parity verified programmatically (no key on either side lacks a counterpart).
  No hardcoded Vietnamese text in either new component — a targeted grep for Vietnamese-diacritic text
  nodes outside `t()` returned nothing. The one literal, `DEFAULT_CLINIC.clinic_name = "Phòng Khám"`,
  matches `PrintableInvoice`/`PrintablePaymentReceipt`/`PrintablePrescription` verbatim — established
  convention, not a finding.
- **Staff with no account**: `staff_code`/`full_name` come off the payslip, never through a `user`
  join; `test_export_includes_staff_without_user_account` covers the Excel side.
- `tfoot` colSpan correctly bumped 13→14 for the new column.

### 5. Shared e2e DB — **leak confirmed**, see M1 below.

---

## Findings

### MAJOR

**M1 — Integration-test fixture leaks rows into the shared `clinic_e2e_postgres`**
`tests/integration/test_payroll_export_e2e.py:120-133` (the `px_ctx` teardown)
*Non-blocking for TASK-139 — systemic, pre-existing pattern. Follow-up required.*

Per CLAUDE.md's Database Error Handling Protocol I am reporting diagnostics only and have **not**
cleaned or modified anything.

**Evidence (live query against `clinic_e2e_postgres`, user `cms`, which has `BYPASSRLS` so the counts
are complete):**

```
alembic_head:            0077
clinic  WHERE code LIKE 'PX%'        →  5 rows   (2026-08-07 14:47:39 … 14:47:45)
"user"  WHERE username LIKE 'px_%'   → 10 rows
staff_profile for those clinics      →  0 rows   ← cleaned OK
user_role for those users            →  0 rows   ← cleaned OK
account_clinic_role for those users  →  0 rows   ← cleaned OK
```

Five leaked clinics = exactly one per `px_ctx`-using test (5 of the 6 tests), all from a single run.
So the teardown **partially** succeeded: `staff_profile`, `user_role` and `account_clinic_role` were
removed, but the final two statements — `DELETE FROM "user" WHERE clinic_id = :cid` and
`DELETE FROM clinic WHERE id = :cid` — did not take effect.

**Strongest lead for the implementer** (deliberately not asserted as fact — needs investigation):
every seeding write is wrapped in `with_tenant_context(clinic_id)`, but the teardown DELETEs are not,
and `"user"` / `staff_profile` / `user_role` all have `relrowsecurity = t` **and
`relforcerowsecurity = t`** (FORCE RLS applies even to the table owner). Whether a DELETE sees rows
therefore depends on the tenant GUC being set. `clinic` has no RLS, so its DELETE failing suggests the
whole teardown transaction (single `commit()` at the end) aborted — most likely on a FK from a child
row — which would surface as a pytest **teardown ERROR**, reported separately from "6 passed".

**Suggested investigation** (not a prescription):
1. Re-run `pytest tests/integration/test_payroll_export_e2e.py -q` and read the full summary line —
   confirm whether errors accompanied the 6 passes. The handoff reports "6/6 passed", which may have
   omitted teardown errors.
2. Check `psql` for the actual failure by running the teardown statements manually with and without
   the tenant context set, observing the reported row counts.
3. Decide the fix: wrap teardown in `with_tenant_context`, and/or delete in strict reverse-FK order
   with the clinic last.

**Why this is not blocking TASK-139**: the shared DB already holds **1,731 clinics and 2,410 users**
accumulated since 2026-07-30 across many test files (ATH 126, VAL 96, INV 84, PHA 60, …), all using
this same fixture shape. TASK-139 copied the established project pattern and contributed 5 of those
1,731. Fixing it properly is a repo-wide fixture change that warrants its own task; holding this
feature hostage to it would be disproportionate. **But it should not be waved through either** — please
raise the follow-up task, and have the implementer complete step 1 above, since the accuracy of their
own "6/6 passed" claim is in question.

### MINOR

**m1 — `month` query param is unvalidated and now reaches an HTTP response header**
`app/modules/hr/api/routes.py:986` → `payroll_service.py:516`

`month` is `Query(..., description="YYYY-MM")` with no pattern, and `timesheet_service.month_window`
parses only `month[:4]` and `month[5:7]`, ignoring any trailing garbage. I verified this directly:

```
'2026-08'                  -> ACCEPTED
'2026-08ABC'               -> ACCEPTED
'2026-08\r\nX-Injected: 1' -> ACCEPTED
'2026-08/../../etc'        -> ACCEPTED
```

TASK-139 is the first code to interpolate `month` into a response header
(`filename=f"bang_luong_{month}"`). I confirmed the CRLF survives Starlette untouched:

```
raw_headers: [(b'content-disposition',
  b'attachment; filename=bang_luong_2026-08\r\nX-Injected: pwned.xlsx')]
```

**However, this is not exploitable as response splitting on this stack** — I checked h11 (0.16.0),
which rejects the value (`LocalProtocolError: Illegal header value`). So the realistic impact is an
unhandled **500** on a malformed `month`, plus silently mis-named/mis-titled files for benign garbage
like `2026-08ABC`. Given the endpoint requires `payroll.manage`, this is a robustness issue rather
than a security hole — hence Minor, not Major.

*Fix*: one line — `month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="YYYY-MM")`.
The `pattern=` idiom is already used across `app/modules/admin/schemas/*`. Note the loose parsing is
pre-existing on all 5 sibling `month`/`period` endpoints, so tightening `month_window` itself would be
the broader fix.

**m2 — The `Tỷ lệ HH (%)` export columns can be a blended rate, not a configured one**
`payroll_service.py` (`_commission_rate_and_source`, added in TASK-138 `cebf0bd`)

The percentage is *derived* as `commission / revenue * 100`. For a staff who earned across multiple
service types at different rates, that is a revenue-weighted **blend** — a number that matches no
configured rule. The source commit documents this honestly, but the Excel header
("Tỷ lệ HH thủ thuật (%)") does not, and accounting will reasonably read it as "the configured rate".

**m3 — `Nguồn tỷ lệ` is "any override", not "all override"**
`commission_service.py:234, 248` — `sc.procedure_used_override = True` is set (never cleared) as soon
as *one* row resolves through an override. A staff who earned across three service types with an
override on only one is exported as **"Riêng"** for the whole aggregate.

Together m2+m3 mean a mixed-rate staff row is directionally right but not literally reconcilable.
Worth a footnote on the sheet or an explicit note in `deliveries/final-specs/`, and worth calling out
to the user since this is accounting output.

**m4 — The "cross-tenant isolation" integration test is weaker than its name**
`tests/integration/test_payroll_export_e2e.py:283-304`

`test_export_is_clinic_scoped` seeds staff in **one** clinic and asserts `names == ["Chỉ Clinic Này"]`.
It never creates a second clinic with staff in the same period, so it cannot actually fail the way a
tenancy regression would manifest. Strengthen by seeding a second clinic + staff for the same month
and asserting that name is absent.

**m5 — Unknown `rate_source` values silently blank out**
`payroll_service.py` — `_RATE_SOURCE_LABEL.get(procedure_rate_source or "", "")`. Any value other than
`staff_override`/`clinic_default` renders as an empty cell rather than surfacing the raw value. The
sibling `_PAY_TYPE_LABEL` lookup does the opposite and falls back to the raw value (covered by
`test_unknown_pay_type_falls_back_to_raw_value`). Prefer the same fallback for consistency.

### NIT

**n1** — A `per_shift` staff on an `_empty_slip` (commission-only, so `shift_rate` is `None`) renders
**no** count row at all in `PrintablePayslip`: `worked_days` is suppressed for `per_shift`
(`PrintablePayslip.tsx:71`), and the `completed_shifts` row is gated on `shift_rate != null`
(`:98-101`). Arguably correct — there is no salary basis — but it is an untested edge.

---

## Process observation (not a finding against TASK-139)

TASK-138 gained commit `cebf0bd` ("expose applied commission rate + source on the payslip") **after** I
approved that branch and moved it to IN_TESTING. That commit is TASK-139's review base, so its ~356
lines sit outside this task's diff and have not been through a review gate. I read it while reviewing
the export columns that consume it, and it looks sound — the original `resolve_service_type_rate` /
`resolve_medicine_rate` are left untouched, with `resolve_*_with_source` companions added, which
preserves the earn/claw-back symmetry guarantee I verified in the TASK-138 re-review. It also closes
**m4 from the TASK-138 report** (the open AC I escalated), which is good news.

Flagging it because the workflow allows post-approval commits to bypass review: TASK-138 is now in
testing with code no reviewer signed off on, and m2/m3 above originate there, not here.

---

## Recommended follow-ups (none block this task)

1. **Task**: fix the integration-test fixture teardown repo-wide and clean the shared e2e DB
   (1,731 clinics / 2,410 users). Start with the diagnostics in M1.
2. **Task or fold into TASK-139 testing**: `pattern=` validation on `month`/`period` params (m1).
3. **Decision needed from user**: how to present blended commission rates in the accounting export
   (m2/m3) — footnote, extra column, or accept as-is with a note in final-specs.
4. Re-review coverage for TASK-138 `cebf0bd` if the workflow requires every commit to be gated.
