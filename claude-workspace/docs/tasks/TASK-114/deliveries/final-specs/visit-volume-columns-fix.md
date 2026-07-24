# TASK-114: Visit-Volume Report Columns Fix

**Status:** DONE  
**Severity:** Medium (M-17 + M-18, E2E finding TASK-095)  
**Affected Systems:** Reports (Frontend)  
**Repos:** clinic-cms-web  

---

## Bug Summary

The Visit-Volume report on the Frontend displayed an inconsistent total:
- **M-17:** The table was missing the "Đang khám" (IN_PROGRESS) column, even though the data was available and present in the CSV export.
- **M-18:** The Total column included visits in AWAITING_PAYMENT status, but that status had no corresponding column in the table or CSV, causing: Total (21) ≠ Sum of visible columns (19).

**Repro:**
1. View Visit Volume report
2. Observe: Total=21, but visible columns (COMPLETED=3 + WAITING=8 + CANCELLED=1 + NO_SHOW=0) sum to 12
3. Missing column: IN_PROGRESS (7) in the table; CSV has it
4. Missing case: AWAITING_PAYMENT (2) — counted in Total but no column anywhere

---

## Root Cause

**M-17:** The adapter (`getVisitVolume()`) already tracked `in_progress` field from backend status, but the UI table (`VisitVolumePage.tsx`) never rendered a column for it.

**M-18:** The adapter's status switch statement lacked a `case "AWAITING_PAYMENT"`, so that count was never captured in any field, but the loop still added it to `total` unconditionally. Result: Total included unmapped status counts.

---

## Fix Design

**Complete the adapter and expose all status columns.**

1. Add `awaiting_payment: number` field to `VisitVolumePoint` type
2. Update adapter switch to handle all 6 known backend statuses (WAITING, IN_PROGRESS, AWAITING_PAYMENT, COMPLETED, CANCELLED, NO_SHOW)
3. Add table columns and CSV export for the two previously missing statuses
4. By construction: Σ(columns) == Total

---

## Changes

### Frontend (clinic-cms-web)

**Branch:** `fix/TASK-114-visit-volume-columns` (base `origin/dev` @ 0dfb3eb)  
**Commit:** `c86fb4d`

#### Modified Files

- `src/modules/reports/types.ts`
  - `VisitVolumePoint` gains: `awaiting_payment: number`

- `src/modules/reports/api.ts` (`getVisitVolume`)
  - Initialize `awaiting_payment: 0` per period
  - Added `case "AWAITING_PAYMENT": point.awaiting_payment = r.count; break;`
  - All 6 known backend statuses now have explicit cases (no implicit fallthrough)

- `src/pages/reports/VisitVolumePage.tsx`
  - Added two table columns:
    - "Đang khám" (IN_PROGRESS): `in_progress` field
    - "Chờ thanh toán" (AWAITING_PAYMENT): `awaiting_payment` field
  - Each column has header + row cells

- `src/modules/reports/helpers.ts` (`exportVisitVolumeCsv`)
  - Added "Chờ thanh toán" column to CSV export (matches table)
  - CSV now sums to Total

- `src/locales/{vi,en}/reports.json`
  - Added key: `reports.visitVolume.inProgress` (English + Vietnamese labels)
  - Added key: `reports.visitVolume.awaitingPayment` (English + Vietnamese labels)
  - `inProgress` key already existed but was unused on-screen before

#### Tests Added

- `src/tests/reports/visitVolumeApi.test.ts` (new, 3 tests):
  1. `test_getVisitVolume_reproduces_e2e_numbers` — Reproduces exact E2E numbers (Total=21, COMPLETED=3, WAITING=8, IN_PROGRESS=7, CANCELLED=1, NO_SHOW=0, AWAITING_PAYMENT=2), asserts Σcolumns == total
  2. `test_getVisitVolume_all_statuses_have_column` — Feeds one row per known backend status; asserts every status lands in a mapped field (no orphan counts)
  3. `test_getVisitVolume_handles_lowercase_status` — Case-insensitivity check (backend may emit lowercase statuses)

#### Updated Test Files

- `src/tests/reports/helpers.test.ts`
  - Updated mock fixtures with new `awaiting_payment` field (type now requires it)

---

## Testing

**Environment:** Frontend-only, no Docker needed  
**Test command:** `npx vitest run src/tests/reports` + `npm run type-check`  
**Test results:** ✅ 31/31 passed

- New tests: 3 passed (`visitVolumeApi.test.ts`)
- Full report test suite: 7 files, 31 total tests (28 pre-existing + 3 new)
- `npm run type-check` — clean, no type errors
- `npm run lint` — 18 pre-existing problems in unrelated files (`VitalsPage`, `VssIntegration*`, `TemplateRenderer`, `TemplateRenderer`); nothing in `reports/` — no new lint breakage

---

## API Behavior

### GET /api/v1/reports/visit-volume

**No backend change.** The endpoint already emits all 6 status rows; the fix is purely frontend consumption.

Frontend now receives and maps:
- WAITING → `waiting: count`
- IN_PROGRESS → `in_progress: count` (was silently ignored; now displayed)
- AWAITING_PAYMENT → `awaiting_payment: count` (was missing; now displayed)
- COMPLETED → `completed: count`
- CANCELLED → `cancelled: count`
- NO_SHOW → `no_show: count`

---

## UI Changes

**Visit-Volume report table — added two columns:**

| Status | Label (VI) | Field |
|--------|------------|-------|
| IN_PROGRESS | Đang khám | `in_progress` |
| AWAITING_PAYMENT | Chờ thanh toán | `awaiting_payment` |

**Column order (left to right):**
1. Hoàn thành (COMPLETED)
2. Đang khám (IN_PROGRESS) [NEW]
3. Chờ khám (WAITING)
4. Chờ thanh toán (AWAITING_PAYMENT) [NEW]
5. Đã hủy (CANCELLED)
6. Không đến (NO_SHOW)

**Formula:** Σ(all 6 columns) = Total

**CSV export:** Also updated to include both new columns in same order.

---

## Acceptance Criteria Met

- [x] Table shows all 6 status columns (including IN_PROGRESS + AWAITING_PAYMENT)
- [x] Σ(columns) == Total (both UI and CSV)
- [x] Unit test: all statuses mapped, exact E2E numbers verified
- [x] No regressions in other report pages

---

## Data Consistency Guarantees

- **Complete mapping:** Every backend status has a UI column; no orphan counts
- **Sum verification:** Constructor (`getVisitVolume`) enforces `total` calculation matches column initialization order
- **Type safety:** Field missing → TypeScript compilation fails (caught in tests)

---

## Out of Scope

Chart (Recharts line/legend) was intentionally left unchanged per bug report scope (table columns + total reconciliation, not trend visualization).

---

## Deployment Notes

- Frontend-only change (no backend migration or API update required)
- No breaking changes to existing columns or structure
- Safe to deploy independently
