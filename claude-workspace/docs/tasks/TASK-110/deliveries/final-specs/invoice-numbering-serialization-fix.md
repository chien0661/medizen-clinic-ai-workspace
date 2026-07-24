# TASK-110: Invoice Numbering Serialization — M-20 Fix

**Date:** 2026-07-24  
**Status:** DONE  
**Test Coverage:** 40/40 passed (concurrency suite)  
**Migration:** 0068 (alembic single head)

---

## Problem Summary

### M-20: Race Condition in Invoice Number Assignment (500 + Duplicate Numbers)
- **Issue:** Two invoices submitted concurrently received the same sequence number (e.g., both `INV-...-008`), causing one to fail with 500 (unique index violation) while the other succeeded
- **Root Cause:** `fn_next_invoice_number()` used `SELECT MAX(seq)+1` without row-level locking; concurrent transactions computed the same `+1` value, violating the unique constraint on `(clinic_id, invoice_date, seq)`
- **Impact:** 
  - Dropped invoices (one 500s, rolls back to draft with empty seq)
  - Data inconsistency (duplicate seq in audit trail if rollback does not fully clean up)
  - Operator friction (common in multi-cashier environments; requires manual recovery)

---

## Solution Design

### Counter Table + ON CONFLICT (Atomic Increment)
- **Change:** Introduce `invoice_number_counter` table with atomic `INSERT ... ON CONFLICT DO UPDATE SET seq = seq + 1 RETURNING seq` pattern
- **Mechanism:** Row lock held for duration of transaction; concurrent callers wait for preceding txn to commit, then increment the counter uniquely
- **Pattern:** Mirrors the proven visit numbering implementation (`fn_next_visit_number()` in TASK-094, alembic 0010)

**New Table: `invoice_number_counter`**
```sql
CREATE TABLE invoice_number_counter (
    clinic_id UUID NOT NULL,
    invoice_date DATE NOT NULL,
    last_seq INT NOT NULL DEFAULT 0,
    PRIMARY KEY (clinic_id, invoice_date)
);
```

**Function Rewrite:**
```sql
-- Old (unsafe): SELECT MAX(seq)+1 from invoices where clinic_id=... and invoice_date=...
-- New (safe):
INSERT INTO invoice_number_counter (clinic_id, invoice_date, last_seq)
VALUES ($1, $2, 1)
ON CONFLICT (clinic_id, invoice_date) DO UPDATE SET last_seq = last_seq + 1
RETURNING last_seq;
```

---

## Implementation Details

**Migration:** `alembic/versions/0068_invoice_number_counter.py` (new, additive)

**Changes:**
1. Create `invoice_number_counter` table
2. Seed counter from `MAX(seq)` per clinic+date for backward compatibility (no gap in sequence on rollout)
3. Rewrite `fn_next_invoice_number(clinic_id, invoice_date)` to use `INSERT ... ON CONFLICT ... RETURNING last_seq`
4. Update `invoice_service.py` to call the new function (no signature change; result now guaranteed unique per request)

**Files:**
- `alembic/versions/0068_invoice_number_counter.py` (new migration)
- `app/modules/billing/services/invoice_service.py` (function call unchanged; result now safe under concurrency)

**Alembic State:**
- **Current Head:** `0068` (single head, no divergence)
- **Downgrade:** Restores pre-0068 function verbatim; counter table dropped
- **Upgrade:** Idempotent; safe to re-run (ON CONFLICT ensures no errors on re-seed)

---

## Testing

**Test Environment:** Isolated Docker stack `v110` (api 9967 / pg 5467 / redis 6449), migrated to alembic head 0068

**Concurrency Test Cases:**
1. **2-Way Concurrent Submit:** Two invoices submitted in parallel → both receive distinct numbers, both return 200 (no 500)
2. **5-Way Concurrent Submit:** Five invoices in parallel → all distinct, all 200
3. **Sequential Monotonic:** Submits in sequence → numbers strictly increasing (no skips or reuse)
4. **Migration Rollback Cycle:** `alembic downgrade -1` → `alembic upgrade head` → single head 0068, clean

**Results:** **40/40 passed** ✓
- 2-way concurrent → distinct numbers ✓
- 5-way concurrent → distinct numbers, all 200 ✓
- Sequential monotonic ✓
- Migration clean (downgrade/upgrade cycle) ✓

**Code Quality:**
- `ruff check` on migration → 0 errors (import order fixed)
- `mypy` on modified files → 0 errors
- No new linting errors in test files

**Full Test Suite Context:** 1080 tests passed across integration/unit suites; 5 pre-existing failures in unrelated modules (email templates, erasure, feature_flags, test_rls_helpers) — confirmed absent from this fix's scope

---

## Backward Compatibility

**No Data Loss:** Seeding reads existing `MAX(seq)` from invoices table; on first counter increment, the new value = prior max + 1 (no gap)

**Sequence Continuity:** If last invoice seq was 42 on clinic 2024-07-24, the counter seeds to 42; next invoice gets 43 (seamless transition)

**Downgrade Safe:** Dropping counter table on downgrade does not affect invoices table; existing issued invoices retain their seq numbers; only future issues will revert to unsafe MAX-scan (not recommended, but no corruption)

---

## Deployment Notes

- **Prerequisites:** 
  - Alembic migration 0068 must run before any concurrent invoice submissions
  - Single downtime window if required (migration is fast; counter seed is single SELECT MAX + INSERT batch)
- **Rollout Strategy:**
  - Deploy migration first (idempotent)
  - Verify alembic heads = 0068 (single head)
  - Deploy updated service code (function call unchanged; safe parallel with migration)
- **Monitoring:** Watch for any 409 or IntegrityError in logs (should be zero post-fix; any occurrence is a sign of a bug in the counter function)

---

## Performance Impact

- **Minimal:** One additional ON CONFLICT row on invoice submit; lock held only for the counter row (sub-millisecond), not the entire invoices table
- **Scalability:** Per clinic+date granularity; no global lock; supports unlimited concurrent submits
- **Migration Time:** O(clinics * distinct_invoice_dates); typically < 1 second on production data

---

## References

- **Branch:** `fix/TASK-110-invoice-number-serialize` (commit `699c7aa`)
- **Test Report:** `docs/tasks/TASK-110/deliveries/test-reports/test-report.md`
- **Source E2E Finding:** TASK-095 (M-20)
- **Precedent Pattern:** TASK-094 (visit numbering, alembic 0010, visit_number_counter table)
- **Alembic Migration:** `alembic/versions/0068_invoice_number_counter.py`
