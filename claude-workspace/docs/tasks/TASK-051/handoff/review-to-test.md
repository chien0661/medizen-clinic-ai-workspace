# Handoff: TASK-051 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary

Code review passed with no CRITICAL / MAJOR findings. Implementation honors all 7 Locked Decisions, all quality gates match baseline (830/830 tests pass, 0 new lint or type-check errors), branch is clean (3 conventional commits, no Co-Authored-By, all files in `clinic-cms-web/src/`, stash preserved). 5 MINOR items documented in `review-report.md` are all known scope-bounded items (wiring stubs awaiting TASK-041 BE, type duplication with un-merged TASK-047 branch, theoretical multi-modal CSS edge case, handoff doc path inaccuracy) and do not block testing.

## Key Findings (MINOR — for awareness, not blockers)

- **Lab Order modal opens with empty items list** when triggered from PatientDetailPage (no LabOrdersTab on main yet). Preview clearly shows "Không có xét nghiệm" / `(0 chỉ định)` — no crash, but tester should verify behavior is acceptable as a stub UI before TASK-041 BE merge.
- **Medical Summary modal opens with empty visits / prescriptions / lab_results arrays** (data fetched only in sub-tabs, no shared page-level query). Patient demographics + alerts render correctly. Empty sections show graceful Vietnamese empty-state messages.
- **`printTypes.ts` lives at `src/components/billing/printTypes.ts`** (handoff doc said `src/types/`). Not a code issue, just a doc inaccuracy.
- **Print CSS uses global `body > *:not(#X-print-root)` selector** scoped to `@media print`. Works correctly in normal flow (one print modal open at a time). Not reachable to break via UI.
- **PatientDetailPage TABS duplicate-bug fix** removed pre-existing dead `audit` and `bhyt_history` keys from a duplicated `const TABS` (those keys were never in the `Tab` union). Conditional `activeTab === "bhyt_history"` retargeted to `activeTab === "bhyt"`. Verify BHYT history tab still reachable when `bhyt` feature flag is on.

## Quality Gate Numbers

| Gate | Result | Delta vs baseline |
|---|---|---|
| Unit tests | 830/830 passed | +31 new |
| Type-check errors | 3 pre-existing (Sidebar.tsx, LoginPage.tsx) | 0 new |
| Lint errors | 16 pre-existing (Sidebar.tsx, VssIntegrationConfigPage, VssSyncLogPage) | 0 new |

## Focus Areas for Testing

### Area A — i18n default to Vietnamese
- **TC-A1**: Fresh install / first launch on a machine whose `navigator.language` is `en-US`:
  - Clear `localStorage.removeItem("app.language")` in DevTools.
  - Hard-reload `/`.
  - **Expected**: app renders in Vietnamese (e.g. menu shows `Trang chủ`, not `Home`).
- **TC-A2**: Manually switch to English via the language picker:
  - Click language picker → choose `en`.
  - Reload page.
  - **Expected**: app stays in English, `localStorage.app.language === "en"` persists.
- **TC-A3**: Switch back to Vietnamese:
  - Click language picker → choose `vi`.
  - Reload page.
  - **Expected**: app stays in Vietnamese.

### Area B — Typography on 7 pages
For each of the 7 modified pages, verify (manual visual smoke):
- `MainDashboardPage` — KPI cards readable, headings legible
- `PatientListPage` — search input, list rows, age/code text
- `PatientDetailPage` — left panel, alerts, tab content (overview, info, vitals)
- `QueueBoardPage` — 5-column board, visit cards (especially `chief_complaint` truncate behavior)
- `InvoiceDetailPage` — payment rows, totals
- `PendingDispensePage` — auto-refresh header, modal grid
- `ARAgingReportPage` — summary cards, chart heading, table
- **Expected**: no layout breakage, no horizontal overflow, no clipped text, dark mode still works.

### Area C — 4 print templates (the heart of the testing)
For each template (VisitSlip A5, LabOrder A5, PaymentReceipt POS 80mm, MedicalSummary A4):

1. **Trigger flow**:
   - VisitSlip: QueueBoardPage → printer icon on a WAITING or registered visit card.
   - LabOrder: PatientDetailPage header → "In phiếu chỉ định" button.
   - PaymentReceipt: InvoiceDetailPage with at least one paid (non-voided) payment → printer icon in the payment row's actions cell.
   - MedicalSummary: PatientDetailPage header → "In bệnh án" button.

2. **Preview modal verification**:
   - Modal opens with patient + visit/payment data populated.
   - Vietnamese labels everywhere, no English mixing.
   - Close button (X) and the Print button both work.

3. **Print preview verification (browser native print preview)**:
   - Click the "In phiếu/đơn (size)" button.
   - In the browser's print preview dialog:
     - **Page size dropdown**: A5 for VisitSlip and LabOrder; A4 for MedicalSummary; ~80mm/Receipt size or "Custom 80mm" for PaymentReceipt.
     - **Visible content**: ONLY the printable content. No app shell, no sidebar, no modal chrome, no preview-modal text — just clinic header → title → data → footer.
     - **Logo**: if clinic settings have `logo_url` set, logo appears at top.
   - Cancel out — no actual print needed for QA.

4. **Empty-state behavior** (LabOrder + MedicalSummary):
   - LabOrder triggered with no items: preview shows `Không có xét nghiệm`, printable shows `Danh sách xét nghiệm (0 chỉ định)` with table headers but no rows. Should NOT crash.
   - MedicalSummary on a patient with no visits/prescriptions: empty-state messages `Chưa có lịch sử khám` / `Chưa có đơn thuốc` appear in print. lab_results section entirely hidden.

5. **Page-break behavior** (smoke):
   - For MedicalSummary: open on a patient with many visits (if available) — verify each visit row stays on one page (no row split across pages).
   - For LabOrder: same with many test items (when data is wired in future).

### Area D — Regression
- **BHYT tab**: with `bhyt` feature flag enabled, navigate to PatientDetailPage → click "Lịch sử BHYT" tab → confirm stub content (`detail.bhytHistoryStub`) renders. Verify `data-testid="bhyt-history-tab"` is in DOM when the bhyt tab is active and flag is on.
- **All 78 existing test files**: should continue to pass (already verified by review run — 830/830).

### Area E — Locked Decisions verification (sanity check)
- Open DevTools → Application → Local Storage → confirm key is `app.language`.
- View `src/lib/i18n.ts` (or compiled bundle) → confirm `detection.order = ["localStorage"]` (no `"navigator"`).
- View any `Printable*.tsx` rendered in DOM → check the `<style>` tag → confirm `@page { size: ... }` directive matches the declared size for that template.

## Out-of-scope reminders

- Do NOT test Tauri shell printing — POS 80mm uses `window.print()` (browser native), not `tauri-plugin-printer`.
- Do NOT test ESC/POS raw command output — explicitly OUT OF SCOPE per Locked Decisions.
- Do NOT modify any source files. If a bug is found, file a bug report under `docs/tasks/TASK-051/bugs/` and request CHANGES_REQUESTED back to Code Implementation Agent.

## Reference

Full review details: `docs/tasks/TASK-051/handoff/review-report.md`.
