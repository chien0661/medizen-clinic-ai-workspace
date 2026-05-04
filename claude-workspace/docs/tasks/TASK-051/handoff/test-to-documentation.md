# Handoff: TASK-051 → Documentation Agent

**From**: Test Agent
**To**: Documentation Agent
**Status**: DOCUMENTING
**Date**: 2026-05-04

## Summary

All tests PASSED (838/838). No new type-check errors, no new lint errors, Vite build succeeds. Implementation is ready for documentation.

## Test Results

| Metric | Value |
|---|---|
| Total tests | 838 |
| Passed | 838 |
| Failed | 0 |
| New tests added by test agent | 8 (i18n regression) |
| Coverage: `src/lib/i18n.ts` | 100% |
| Type-check new errors | 0 |
| Lint new errors | 0 |

**Full test report**: `docs/tasks/TASK-051/deliveries/test-reports/test-report.md`

## What Was Implemented

### Area A — i18n
- `src/lib/i18n.ts`: `detection.order` changed from `["localStorage", "navigator"]` to `["localStorage"]` only. App always defaults to Vietnamese (`fallbackLng: "vi"`) when no explicit user preference is stored.

### Area B — Typography (7 pages)
Surgical `text-xs → text-sm` and `text-sm → text-base` swaps on body content of:
- `MainDashboardPage.tsx`
- `PatientListPage.tsx`
- `PatientDetailPage.tsx` (+ pre-existing duplicate TABS bug fix)
- `QueueBoardPage.tsx`
- `InvoiceDetailPage.tsx`
- `PendingDispensePage.tsx`
- `ARAgingReportPage.tsx`

### Area C — 4 Print Templates
New components (all follow TASK-047 `window.print()` + `@media print` CSS pattern):

| Template | Paper | Component | Modal | Trigger |
|---|---|---|---|---|
| Phiếu khám (Visit Slip) | A5 | `PrintableVisitSlip` | `PrintVisitSlipModal` | QueueBoardPage printer icon (WAITING/registered cards) |
| Phiếu chỉ định CLS (Lab Order) | A5 | `PrintableLabOrder` | `PrintLabOrderModal` | PatientDetailPage "In phiếu chỉ định" button |
| Phiếu thu (Payment Receipt) | POS 80mm | `PrintablePaymentReceipt` | `PrintPaymentReceiptModal` | InvoiceDetailPage printer icon on payment rows |
| Bệnh án tóm tắt (Medical Summary) | A4 | `PrintableMedicalSummary` | `PrintMedicalSummaryModal` | PatientDetailPage "In bệnh án" button |

Shared types: `src/components/billing/printTypes.ts` (`ClinicInfo`, `PatientInfo` interfaces).

## Known Gaps (MINOR — not blocking documentation)

1. **`Print*Modal` wrappers have no unit tests** — modal wrappers are thin (~140 LOC each); `window.print()` confirmed by code inspection but not automated. Note for future test cycle.
2. **New print component directories excluded from vitest coverage include list** — per `vite.config.ts`, coverage only measures `src/lib/`, `src/stores/`, `src/sync/`, specific components. Print component directories not included. Adding them to coverage include is a follow-up improvement, not blocking.
3. **LabOrder and MedicalSummary wired with stub data** — PatientDetailPage passes `items: []` to LabOrder and `visits: [], prescriptions: [], lab_results: []` to MedicalSummary pending TASK-041 BE merge. Both components render graceful empty-state Vietnamese messages (no crash). Documented MINOR in review-report.md.

## New Test File Created

- `src/tests/lib/i18n-default-language.test.ts` — 8 tests covering i18n detection order, fallback language, TC-A2 / TC-A3 scenarios.

## Documentation Scope Suggestions

- User guide: how to trigger each print template (where to click, what modal shows)
- Technical doc: print architecture overview (window.print() + @media print + @page size CSS pattern, following TASK-047)
- i18n behavior: how default Vietnamese works, how user language switch persists
- Typography changes: which pages changed and what font sizes are used
- Known limitations: LabOrder and MedicalSummary show empty-state pending TASK-041 BE data wiring
- Future work: add Print*Modal unit tests; add print component dirs to coverage include; ESC/POS raw (out of scope, separate task if needed)
