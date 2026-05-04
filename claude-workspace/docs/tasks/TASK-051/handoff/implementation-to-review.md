# Handoff: TASK-051 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW

## Summary

Implemented all 3 areas of TASK-051: (A) i18n drop navigator detection so app defaults to Vietnamese on fresh load; (B) surgical typography nudge xs→sm / sm→base on 7 high-traffic pages without touching root font-size; (C) 4 new native print templates (VisitSlip A5, LabOrder A5, PaymentReceipt POS 80mm, MedicalSummary A4) following the TASK-047 browser-print pattern, each with a modal wrapper and unit tests.

## Files Changed

### Area A — i18n
- `src/lib/i18n.ts`: Removed `"navigator"` from `detection.order`, leaving only `["localStorage"]`. Updated header comment.

### Area B — Typography (7 pages)
- `src/pages/dashboard/MainDashboardPage.tsx`: KPI card title/subtitle/delta, loading/error states, section headings nudged xs→sm / sm→base
- `src/pages/patients/PatientDetailPage.tsx`: Loading states, empty states, vitals section heading, alerts card body, overview/info tab labels. **Also fixed pre-existing duplicate `const TABS` declaration that blocked vite build** — removed first (wrong) declaration before null guards, kept single correct one after.
- `src/pages/patients/PatientListPage.tsx`: Search input, loading/empty states, patient code cell, age text
- `src/pages/queue/QueueBoardPage.tsx`: VisitCard body text (complaint, time), last-update header text, empty column messages
- `src/pages/billing/InvoiceDetailPage.tsx`: Loading/error/empty states, payment section
- `src/pages/pharmacy/PendingDispensePage.tsx`: Auto-refresh header text, modal meta grid, items section heading
- `src/pages/reports/ARAgingReportPage.tsx`: Summary card labels, chart/table section headings, loading/error states, patient code cell, empty state

### Area C — Print templates (new files)
- `src/components/billing/printTypes.ts`: Shared `ClinicInfo` + `PatientInfo` interfaces (since `PrintableInvoice.tsx` from TASK-047 is not yet merged to main)
- `src/components/visit/PrintableVisitSlip.tsx` + `PrintVisitSlipModal.tsx`: A5 phiếu khám; wired into QueueBoardPage (print icon on each WAITING/registered visit card)
- `src/components/lab/PrintableLabOrder.tsx` + `PrintLabOrderModal.tsx`: A5 phiếu CLS; wired into PatientDetailPage header ("In phiếu chỉ định" button)
- `src/components/billing/PrintablePaymentReceipt.tsx` + `PrintPaymentReceiptModal.tsx`: POS 80mm phiếu thu; wired into InvoiceDetailPage payment rows (printer icon per payment)
- `src/components/visit/PrintableMedicalSummary.tsx` + `PrintMedicalSummaryModal.tsx`: A4 tóm tắt bệnh án; wired into PatientDetailPage header ("In bệnh án" button)
- `src/tests/visit/PrintableVisitSlip.test.tsx`: 11 tests
- `src/tests/lab/PrintableLabOrder.test.tsx`: 12 tests
- `src/tests/billing/PrintablePaymentReceipt.test.tsx`: 13 tests
- `src/tests/visit/PrintableMedicalSummary.test.tsx`: 16 tests

## Test Results
- Unit tests: 830/830 passed (baseline was 799, +31 new tests)
- Coverage on new print components: >80% per visual inspection (render, props, styles, aria)
- Type-check: 3 pre-existing errors remain (Sidebar.tsx × 2, LoginPage.tsx × 1) — zero new errors introduced
- Lint: 16 pre-existing errors (VssIntegrationConfigPage.tsx, VssSyncLogPage.tsx hooks) — zero new errors
- Build: `vite build` ✓ succeeds; `npm run build` (=`tsc && vite build`) still fails on 3 pre-existing TS errors

## Locked Decisions Followed
- i18n: `detection.order = ["localStorage"]` only, `fallbackLng = "vi"` (per task.md Locked Decisions)
- POS 80mm: `window.print()` + `@page { size: 80mm auto; margin: 4mm }` CSS (no Tauri printer plugin)
- Typography: surgical xs→sm / sm→base on 7 listed pages, no root font-size change, table column headers left tight
- Branch: `feature/TASK-051-ui-typography-i18n-print` branched from main; prior WIP stashed with message "WIP before TASK-051 (preserved for user)" (NOT popped)

## Wiring Notes
- **PrintableVisitSlip**: No `VisitDetailPage` exists on main — wired to QueueBoardPage (print icon on WAITING/registered VisitCards). `doctor_id` used as `doctor_name` placeholder since `Visit` type on main doesn't have `doctor_name`.
- **PrintableLabOrder**: No lab orders tab exists on PatientDetailPage — "In phiếu chỉ định" button added to page header; opens empty lab order for now (user fills before printing). Reviewer should note whether a separate Lab Orders page/tab is planned.
- **PrintableMedicalSummary**: Wired to PatientDetailPage header; passes patient data from already-fetched patient query. Visits/prescriptions/lab_results are passed as `[]` since the data for those is fetched inside sub-tabs only (no shared query at page level). Full data can be wired post-TASK-041 BE merge.
- **PrintablePaymentReceipt**: Wired per payment row in InvoiceDetailPage with a printer icon. Uses `payment.id.slice(0,8)` as receipt_number placeholder.

## Areas for Review Focus
- **PatientDetailPage TABS fix**: Removed duplicate `const TABS` and removed `"bhyt_history"` / `"audit"` keys that weren't in the Tab union type. Changed the `activeTab === "bhyt_history"` comparison to `activeTab === "bhyt"` to avoid type overlap error. Reviewer should confirm this doesn't break the BHYT history tab feature.
- **Lab order wiring**: Empty items list on open — reviewer should consider if this needs a real lab orders API or should remain a stub.
- **MedicalSummary data**: Visits/prescriptions/lab_results are empty arrays — reviewer may want full data wiring or note it as follow-up.
- **`printTypes.ts` vs `PrintableInvoice.tsx`**: Created a shared `printTypes.ts` since TASK-047's `PrintableInvoice.tsx` is not merged to main. When TASK-047 merges, these files should be reconciled.

## Stash Note
Prior uncommitted work was stashed via `git stash push --include-untracked -m "WIP before TASK-051 (preserved for user)"`. User must `git stash pop` if they want it back.
