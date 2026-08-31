# Follow-up Cluster — TASK-146 (2026-09-01)

**Status**: PENDING (5 items: all pre-existing or deferred by design, none block TASK-146 DONE)

All items referenced in `TASK-146/handoff/test-to-documentation.md`, `TASK-146/handoff/review-report.md`, and `TASK-146/deliveries/test-reports/test-report.md`.

---

## PRE-EXISTING BUGS (high-priority, not introduced by TASK-146)

### BUG-146-01 — `fn_next_visit_number` truncates past 999, making clinic unable to create visits after 1000/day

**Severity:** MEDIUM (high impact, low likelihood — see "Real-world exposure")  
**Status:** OPEN — confirmed pre-existing on `dev` and `main`, not a TASK-146 regression  
**Found by:** Test Agent (TASK-146 Stage C, E2E environment build-out) + independent re-discovery by second Test Agent instance  
**File:** `clinic-cms/alembic/versions/0010_create_visits.py` (function `fn_next_visit_number`)  
**Caller:** `app/modules/visits/services/visit_service.py:43` (`generate_visit_number()`)

**Issue:**

```sql
RETURN to_char(p_date, 'YYYYMMDD') || '-' || lpad(v_seq::text, 3, '0');
--                                                  ^^^^ truncates at 3 chars
```

PostgreSQL's `lpad` truncates (does not error) when input exceeds target length:
- Visit 999: `lpad('999', 3, '0')` = `'999'` ✓
- Visit 1000: `lpad('1000', 3, '0')` = `'100'` ✗ (collision with visit 100)
- Visit 1234: `lpad('1234', 3, '0')` = `'123'` ✗ (collision with visit 123)

From visit 1000 onward, the unique index `uq_visit_clinic_date_number` rejects inserts, and every visit creation returns **500 INTERNAL_SERVER_ERROR** until the calendar date rolls over.

**Why caught now:**

E2E seeding ran 11 tests + 55-visit fixture + multiple C2 scenario runs = 999+ visits for the DEMO clinic on 2026-08-31. Once past visit 999, every subsequent visit creation failed with 500 until a fresh database was restored.

**Real-world exposure:** A single clinic must perform 1000+ visits in one calendar day to trigger this (far beyond realistic), but it is reachable in:
- Bulk/imported data scenarios
- Load testing
- Shared demo tenants
- Future multi-site tenants mapped to a single `clinic_id`

This is exactly how it was found — automated E2E seeding, which is well within the use case of a system test suite.

**Suggested fix:**

Do not truncate — pad to a minimum width without imposing a maximum:

```sql
-- Option A — pad only while it fits, never truncate
RETURN to_char(p_date, 'YYYYMMDD') || '-' ||
       CASE WHEN v_seq < 1000 THEN lpad(v_seq::text, 3, '0') ELSE v_seq::text END;

-- Option B — to_char with a fixed mask (does not truncate; FM strips padding blanks)
RETURN to_char(p_date, 'YYYYMMDD') || '-' || to_char(v_seq, 'FM000');
```

Both keep today's `-001 … -999` format byte-identical (no data migration needed).

**Worth verifying:** Similar `lpad` pattern may exist in invoice/prescription number generators (migrations 0053, 0068). Check if they truncate or pad correctly.

**Worktree:** `clinic-cms` (backend)  
**Effort:** 30 minutes (fix + migration + test)

---

### BUG-146-04 — No UI action anywhere moves a prescription from `draft` to `pending` — pharmacy dispensing unreachable

**Severity:** HIGH (pre-existing, blocks workflow clinic-wide)  
**Status:** OPEN — confirmed pre-existing on `dev`; zero call sites for `doctorApi.submitPrescription` in codebase  
**Found by:** Test Agent (TASK-146 Stage C, while authoring E2E spec)  
**File:** `clinic-cms-web/src/modules/doctor/PrescriptionTab.tsx` (save logic); `clinic-cms-web/src/components/doctor/api.ts:196` (unused export)

**Issue:**

The doctor's prescribing screen can create and save a prescription via `saveMutation` (`POST /prescriptions` → status `draft`), but there is **no UI element anywhere** that calls `doctorApi.submitPrescription` (`POST /prescriptions/{id}/submit`, draft → pending).

Confirmed:
```bash
$ grep -rn "submitPrescription" clinic-cms-web/src/
src/modules/doctor/api.ts:196:  submitPrescription: (prescriptionId: string): Promise<Prescription> =>
# Zero other matches — function defined but never called
```

**Consequences:**

1. **Pharmacy dispensing workflow is unreachable.** `dispense_service.dispense` requires `prescription.status == "pending"`:
   ```python
   raise BusinessRuleError(
       f"Không thể cấp phát đơn thuốc ở trạng thái '{prescription.status}' "
       "(yêu cầu 'pending' — bác sĩ phải gửi đơn trước khi cấp phát).", ...)
   ```
   The pending-dispense queue never receives any items through the running UI.

2. **Patient history will never show an active prescription.** TASK-146's D-1 rule excludes `draft` from history. A prescription can only appear in history if it reaches `pending` or higher, or if it's `cancelled`. Through the running UI, neither path is reachable for a new prescription, so the workflow breaks.

**Evidence it's pre-existing:**

- `src/modules/doctor/api.ts` has a **zero-line diff** against `dev` (code reviewer confirmed independently)
- TASK-145's own approved regression spec (`cancel-adjust-flow.spec.ts`) hits the same wall and works around it by calling `POST /prescriptions/{id}/submit` directly via API, because no UI element exists

**Suggested fix (follow-up task):**

Either:
- Add an explicit "Gửi đơn" / finalize button in `PrescriptionTab.tsx` that calls `doctorApi.submitPrescription` after save, or
- Make `saveMutation` call `submit` automatically (e.g., on leaving the tab, or via a "Lưu & gửi đơn" variant)

Maintain a true `draft` save for in-progress work if needed; the constraint is that **some UI path must exist** to move from `draft` to `pending`.

**Workaround in this task:** TASK-146's E2E spec (`visit-correction-full-flow.spec.ts`) uses direct API calls to `POST /prescriptions/{id}/submit` after the UI save (C2 scenario and AC7 fixture), documented inline. This allowed the task to verify history rendering against realistically-shaped records without depending on UI that doesn't exist yet.

**Worktree:** `clinic-cms-web`  
**Effort:** 1–2 hours (UI button + wiring, test)  
**Impact on clinic:** Blocks pharmacy dispensing entirely through the running UI.

---

### BUG-146-05 — `_pull_lines_from_visit` error masking and logging — pre-existing on production

**Severity:** MEDIUM (masks real error, unhelpful 500 messages)  
**Status:** OPEN — pre-existing on `dev` and `main`, currently running on production  
**Found by:** Manager (independent verification run, freshly-seeded database)  
**File:** `clinic-cms/app/modules/billing/services/invoice_service.py:206`  
**Trigger:** `POST /api/v1/invoices/{id}/submit` on a freshly-seeded database (rare timing)

**Issue:**

```python
try:
    sp = await db.begin_nested()          # ← first statement inside try
    vs_result = await db.execute(text("SELECT vs.id, ..."))
    ...
    await sp.commit()
except Exception as exc:
    await sp.rollback()                   # ← dies here if begin_nested() threw
    log.debug("visit_service_not_available", error=str(exc))
```

If `db.begin_nested()` throws (session already in error state from prior operation), `sp` is never assigned → `sp.rollback()` raises `UnboundLocalError: cannot access local variable 'sp'`.

**Two consequences:**

1. **Original error is completely masked.** The real exception (`exc`) never appears in logs; only the `UnboundLocalError` is seen — a cryptic Python error with no business meaning.
2. **Logging is wrong.** Even when the code "works" (doesn't hit the UnboundLocalError), it logs at `debug` level with a pre-judged label `"visit_service_not_available"` (guessing the cause), which:
   - Is not shown in default log levels, hiding the real problem
   - Misnames most real causes (DB connection issues, data constraint violations, etc.)

Same pattern appears in the `sp2` block immediately below (for in-house medicines).

**Evidence it's pre-existing:**

- No diff to this area in TASK-146 (invoice_service.py only added `_apply_patient_filter` to list/count; submit path untouched)
- Condition reproduced on freshly-seeded database in independent verification run (fresh state somehow triggers the timing)
- Not reliably reproduced (happened once, then not again with same DB data), suggesting a session-state race condition

**Suggested fix:**

Initialize `sp = None` or move `begin_nested()` outside try, so rollback can check existence. Raise log level to `warning` and remove the pre-judged label:

```python
sp = await db.begin_nested()
try:
    vs_result = await db.execute(text("SELECT vs.id, ..."))
    ...
    await sp.commit()
except Exception as exc:
    await sp.rollback()
    log.warning("pull_visit_service_lines_failed", error=str(exc), exc_info=True)
```

Apply to both `sp` and `sp2` blocks.

**Related:** This is likely the root cause of the "E2E spec fails on fresh database" observation (see "Spec DB-State Sensitivity" below).

**Worktree:** `clinic-cms`  
**Effort:** 30 minutes (fix + test)

---

### BUG-146-02 — TASK-145's regression spec asserts stale banner text (low-priority test debt)

**Severity:** LOW (cosmetic, test-only, pre-existing)  
**Status:** OPEN — affects test pass rate but not product behavior  
**Found by:** Test Agent (TASK-146 AC8 regression run)  
**File:** `clinic-cms-web/e2e/regression/cancel-adjust-flow.spec.ts:616` (TASK-145, unmodified by TASK-146)

**Issue:**

Test assertion:
```ts
await expect(page.getByText(/đã được cấp phát nên không thể sửa hoặc hủy trực tiếp/))
  .toBeVisible(...)
```

Looks for `"không thể sửa hoặc hủy trực tiếp"`. Actual banner text today is `"không sửa hoặc hủy trực tiếp được"` (wording changed; `"thể"` dropped, `"được"` moved).

This was changed in commit `229d32c` (Aug 30, on `dev`, before TASK-146 branched):
```
fix(doctor): point dispensed banner at pharmacy undispense
```

Which reworded `src/locales/vi/doctor.json`'s `dispensedBanner` key, but the spec's regex was never updated to match. **The underlying feature is correct** — a dispensed prescription still shows a named next step — only the exact wording moved.

**Suggested fix (one-line):**

Update the regex to match current copy:
```ts
await expect(page.getByText(/đã được cấp phát nên không sửa hoặc hủy trực tiếp/))
  .toBeVisible(...)
```

Left unfixed here since it belongs to TASK-145's file and is out of this task's scope. Flagging for whoever owns that spec next.

**Impact:** Makes AC8 regression run report 1 failure out of 20 in `cancel-adjust-flow.spec.ts` (all other tests pass). Not a TASK-146 defect.

**Worktree:** `clinic-cms-web`  
**Effort:** < 2 minutes (one-line fix)

---

## DEFERRED ENHANCEMENTS (by design, not urgent)

### D-2.1 — Show actor (username) on cancelled/voided records — deferred to follow-up task

**Decision:** TASK-146 D-2 decided to show `cancelled_at` + `cancel_reason` but **not the actor** (person who cancelled).

**Why deferred:**

The actor **does exist** in the database:
- `AuditedMixin.updated_by` on all entities (set by all three cancel/void paths: `prescription_service.cancel`, `invoice_service.void_invoice`, `invoice_service.refund_invoice`)
- TASK-145 audit logs also record actor + timestamp for the transition

Displaying the actor's **name** (not just UUID) requires:
1. Add `updated_by` to response schemas (additive, no model change)
2. Call `GET /users/{id}` for each cancelled record, which needs `user.manage` permission

The patient chart UI currently lacks `user.manage` permission, so a receptionist viewing a patient's chart would see bare UUIDs for actor names, not readable names.

**Suggestion for follow-up task:**

- Add `updated_by` to `PrescriptionResponse` and `InvoiceSummaryResponse` (backend)
- Request `user.manage` permission for the patient chart UI (or call a new lightweight `/users/{id}/name-only` endpoint if user.manage is too broad)
- Render actor username on the cancelled-record rows

**Impact:** Patient chart shows who cancelled each record, improving audit trail readability.

**Worktree:** Both `clinic-cms` and `clinic-cms-web`  
**Effort:** 2–3 hours (schemas, permission audit, FE changes)

---

### D-2.2 — Show cancel reason at the visit level (not just prescription/invoice level)

**Observation:** During TASK-146's audit (A1 section), it was noted that a **CANCELLED visit** can show the "Đã huỷ" status badge but never shows **why** or **when**.

TASK-146's scope was prescription/invoice cancellation only, so this was deferred. But the principle is the same as B1/B2 (show the full story of what happened):

| Type | Hiển thị hiện tại | Cần hiển thị |
|------|-------------------|-------------|
| Cancelled prescription | Lý do + thời điểm (TASK-146) | ✓ |
| Voided/refunded invoice | Lý do + thời điểm (TASK-146) | ✓ |
| Cancelled visit | Chỉ badge "Đã huỷ" | ✗ (lý do + thời điểm) |

**Suggestion for follow-up task:**

Extend the D-1/D-2 pattern to visits: add `cancel_reason` and `cancelled_at` columns to `Visit` model (or use existing audit log), then display them on the VisitsTab when a visit is cancelled.

**Impact:** Clinic staff can fully understand the visit history.

**Worktree:** Both `clinic-cms` and `clinic-cms-web`  
**Effort:** 3–4 hours (model change, migration if needed, FE rendering)

---

## SPEC MAINTAINABILITY ISSUE

### E2E Spec DB-State Sensitive (not a bug, but a maintainability concern)

**Observation:** During independent verification (Manager run on fresh database):

| Run | Condition | Result |
|-----|-----------|--------|
| 1 | DB freshly seeded | **FAIL** — 500 on `POST /invoices/{id}/submit` (likely BUG-146-05); 5 pass, 5 don't run |
| 2 | Rerun same test file in isolation | **PASS** — 2/2 (31s) |
| 3 | Full file, DB already warm from prior runs | **PASS** — 11/11 (1.5 min) |

**Root cause:** Likely BUG-146-05 (error masking on fresh DB state) + possibly other session-state assumptions in the test fixture.

**Why it matters:**

A test suite that only passes on a "warm" database does not protect CI if CI runs on a fresh database. This is a maintainability debt, not a feature defect.

**Suggestion for follow-up task:**

After fixing BUG-146-05:
1. Rerun the E2E spec on a freshly-seeded database to confirm it now passes 11/11
2. If any tests still fail, add database normalization fixtures (e.g., idempotent seed re-runs between test phases)
3. Document the spec's database state requirements in a comment at the top of the file

**Worktree:** `clinic-cms-web`  
**Effort:** 1–2 hours (investigation + fixture design)

---

## Summary Table

| Item | Type | Severity | Status | Blocker for TASK-146 DONE? |
|------|------|----------|--------|---------------------------|
| BUG-146-01 | Pre-existing bug | MEDIUM | OPEN | **NO** — not in TASK-146 diff |
| BUG-146-02 | Test debt | LOW | OPEN | **NO** — pre-existing test, not in TASK-146 diff |
| BUG-146-04 | Workflow gap | HIGH | OPEN | **NO** — pre-existing, workaround applied in E2E spec |
| BUG-146-05 | Error masking | MEDIUM | OPEN | **NO** — pre-existing on main/production |
| D-2.1 Actor display | Enhancement | MEDIUM | DEFERRED | **NO** — by design, documented in task.md |
| D-2.2 Visit cancel reason | Enhancement | LOW | DEFERRED | **NO** — out of task scope (visit-level, not prescription/invoice) |
| E2E spec DB sensitivity | Maintainability | MEDIUM | PENDING | **NO** — affects test reliability, not feature behavior |

---

## Next Steps

1. **Immediate (blocking CI):** Fix BUG-146-05 (error masking)
2. **High priority:** Fix BUG-146-04 (workflow gap — pharmacy dispensing blocked)
3. **Medium priority:** Fix BUG-146-01 (truncation bug, reachable in bulk/test scenarios)
4. **Low priority:** Fix BUG-146-02 (test text drift)
5. **Follow-up tasks:** D-2.1 (actor display), D-2.2 (visit cancel reason), E2E spec DB robustness

