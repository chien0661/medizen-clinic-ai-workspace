# Review Report — TASK-051

**From**: Code Review Agent
**Reviewed**: 2026-05-04
**Branch**: `feature/TASK-051-ui-typography-i18n-print` (3 commits on top of `main`)
**Decision**: **APPROVED**

## Summary

The implementation cleanly delivers all 3 locked-scope areas (i18n default-to-vi, surgical typography nudge on 7 listed pages, 4 new native print templates following TASK-047 pattern). All Locked Decisions are honored. No new lint/type-check/test regressions. Wiring stubs for `PrintableLabOrder` and `PrintableMedicalSummary` are clearly bounded and produce empty-but-functional preview/print output rather than crashes — acceptable as documented MINOR follow-up items pending TASK-041 BE merge.

## Branch Verification

| Check | Result |
|---|---|
| Commits on branch (`git log main..HEAD`) | 3 commits, all conventional `feat(...)` prefix |
| `Co-Authored-By` / "Generated with" attribution | NONE found |
| Files outside `src/` | NONE — all 21 files in `src/` |
| BE files (`*.py`) | NONE |
| Other repos (`clinic-cms`, `clinic-cms-merge`, `clinic-cms-landing`) | NONE |
| Stash preserved (NOT popped) | `stash@{0}: WIP before TASK-051 (preserved for user)` exists |

## Quality Gates

| Gate | Result | Baseline (main) | Delta |
|---|---|---|---|
| `npm test` | **830/830 passed** (78 files, 17.9s) | 799 | +31 new tests |
| `npm run type-check` | 3 pre-existing errors (Sidebar.tsx ×2 + LoginPage.tsx ×1) | 3 | **0 new** |
| `npm run lint` | 16 pre-existing errors (Sidebar.tsx ×2, VssIntegrationConfigPage ×6, VssSyncLogPage ×8) | 16 | **0 new** |
| Vite build | Succeeds (TS errors above only block `npm run build`) | matches baseline | unchanged |

## Locked Decisions Compliance

| Decision | Followed? | Evidence |
|---|---|---|
| POS 80mm = `window.print()` + `@page { size: 80mm auto }` | YES | `PrintablePaymentReceipt.tsx:71` `@page { size: 80mm auto; margin: 4mm }`. No Tauri printer plugin, no ESC/POS raw. |
| ESC/POS raw OUT OF SCOPE | YES | No raw escape codes anywhere in diff. |
| i18n default `lng: "vi"` + `detection.order: ["localStorage"]` | YES | `src/lib/i18n.ts:119` `fallbackLng: "vi"` unchanged; `:125` order is `["localStorage"]` only. `LanguageDetector` still wired (line 64). |
| Typography surgical xs→sm / sm→base on listed 7 pages, no root font-size change | YES | All diffs in 7 pages are pure className swaps; `tailwind.config.ts` and `index.css` untouched. |
| Branch from main with prior WIP stashed (NOT popped) | YES | Branch created from main; stash present. |
| Repo scope `clinic-cms-web` only | YES | All 21 files inside `clinic-cms-web/src/`. |
| Phase 1 + Phase 2 in single PR (full scope C) | YES | All 3 areas (A i18n + B typography + C 4 print templates) in 3 cohesive commits. |

## Findings by Severity

### CRITICAL
*None.*

### MAJOR
*None.*

### MINOR

1. **Wiring stub: `PrintableLabOrder` opens with empty items list from PatientDetailPage**
   - File: `src/pages/patients/PatientDetailPage.tsx:870-880`
   - Behavior: clicking "In phiếu chỉ định" opens modal with `items: []`. Preview shows `Không có xét nghiệm` clearly, and printable shows `Danh sách xét nghiệm (0 chỉ định)` with empty tbody.
   - Why MINOR: User can still see they have nothing to print before hitting Print. No crash. Implementation handoff and task notes both flag this as awaiting TASK-041 BE / Lab Orders tab — design decision, not bug. Not misleading because the empty state is explicitly visible in preview before print.
   - Follow-up (post-merge, NOT blocking this task): once TASK-041 BE merges with lab-orders endpoint and a `LabOrdersTab` is added on PatientDetailPage, replace the stub wiring with a real per-order print trigger inside that tab. Track as a separate task.

2. **Wiring stub: `PrintableMedicalSummary` opens with empty visits/prescriptions/lab_results arrays**
   - File: `src/pages/patients/PatientDetailPage.tsx:849-867`
   - Behavior: passes `visits: []`, `prescriptions: []`, `lab_results: []` to the modal. Patient demographics (full_name, code, phone, DOB, gender, blood_type, allergies, chronic_conditions, address) are real and rendered.
   - Why MINOR: `PrintableMedicalSummary` handles empty arrays gracefully via `Chưa có lịch sử khám` / `Chưa có đơn thuốc` empty messages and conditionally hides the lab-results section when empty. Output is valid (a printable summary with patient demographics + medical alerts) — just less complete than the eventual full-data variant.
   - Follow-up (post-merge, NOT blocking): wire this from a shared page-level query collecting visits + prescriptions + lab_results once those queries exist outside their respective sub-tabs.

3. **`printTypes.ts` location and duplication risk vs TASK-047**
   - File: `src/components/billing/printTypes.ts` (note: handoff said `src/types/printTypes.ts` — actual location is `src/components/billing/`. Minor handoff doc inaccuracy, code itself is fine.)
   - Issue: `ClinicInfo` and `PatientInfo` interfaces defined here. TASK-047's `PrintableInvoice.tsx` (un-merged branch `feature/TASK-047-print-receipts`) defines its own copies of these types. When both branches eventually land on main there will be parallel definitions.
   - Why MINOR / pragmatic: the alternative — importing from a still-WIP branch — would couple TASK-051 to TASK-047 merge order and was correctly rejected. Both branches are isolated and either branch can adapt at merge time.
   - Follow-up: at TASK-047 OR TASK-051 merge time (whichever lands second), reconcile to a single canonical location, e.g. `src/types/print.ts` or extend the existing `printTypes.ts`. Add this to the integration checklist.

4. **Print-CSS uses global `body > *:not(#X-print-root)` selector inside `@media print`**
   - Files: all 4 `Printable*.tsx` components.
   - Pattern: `body > *:not(#visit-slip-print-root) { display: none !important; }` (and analogues for the 3 other print roots).
   - Why MINOR: scoped to `@media print`, so no leak in screen view. CSS is hot-mounted per modal, so on a normal "click print icon → window.print()" flow only one Printable component is in the DOM at a time and the rule works correctly. Theoretical bug if two print modals were ever open simultaneously (each rule hides the other's root) — but that's not reachable through the current UI.
   - Follow-up (optional): if a future feature opens multiple print modals concurrently, refactor to compose the print roots (e.g. `body > *:not([data-print-root])` plus `data-print-root` attribute on each printable). Not required now.

5. **Handoff doc inaccuracy — `printTypes.ts` path**
   - The implementation-to-review handoff mentions `src/types/printTypes.ts` but the file actually lives at `src/components/billing/printTypes.ts`. Cosmetic doc issue only; code itself is consistent.

### Observations (no severity, FYI)

- **PatientDetailPage TABS fix**: implementation removed a duplicate `const TABS` declaration that referenced invalid `Tab` keys (`audit`, `bhyt_history` were not in the `Tab` union on `main`). The kept declaration matches the union (`overview | info | guardian | visits | prescriptions | invoices | vitals | bhyt`). The `activeTab === "bhyt_history"` conditional was correctly retargeted to `activeTab === "bhyt"`. No tests reference `bhyt-history-tab` testid (verified by grep), so no test regression. This is a real improvement that unblocks the vite build — would otherwise have been a separate bug-fix task.
- **i18n locale parity**: no locale JSON files (`src/locales/vi/*.json`, `src/locales/en/*.json`) were modified — print components use hardcoded Vietnamese strings, which is consistent with the locked decision's intent (Vietnamese-first user base). Acceptable.
- **Security**: grep across all new files (`src/components/{visit,lab,billing}/Print*.tsx`, `src/components/billing/printTypes.ts`, 4 test files) found zero `console.log`, `TODO`, `password`, `secret`, `api[_-]key`, hardcoded `http(s)://` URLs.
- **Test coverage**: 4 new test files (52 `it(...)` matches by grep, 31 net new tests as reported, due to `describe`/setup also matching). Each component has tests for: render-without-crash, visible content with full props, fallback when minimal props, print CSS class presence (`@media print` matcher), aria-hidden wrapper. Coverage is meaningful, not just for-the-numbers.

## Spot-check Detail

- **`src/lib/i18n.ts`** — diff is exactly 2 line changes (comment + array). `LanguageDetector` import + `.use(LanguageDetector)` chain still in place. `fallbackLng: "vi"` unchanged. ✓
- **`src/pages/dashboard/MainDashboardPage.tsx`** — 8 className swaps, all xs→sm or sm→base on body labels/loader/error/heading text. Zero logic edits. ✓
- **`src/pages/queue/QueueBoardPage.tsx`** — 5 className swaps + new optional `onPrint` prop on `VisitCard` + new `printVisit` state + modal render at bottom. Print icon wired only on `registered` and `waiting` columns (per spec — only WAITING/registered get phieu khám). ✓
- **`src/pages/reports/ARAgingReportPage.tsx`** — 7 className swaps, no logic changes. ✓
- **`src/pages/patients/PatientDetailPage.tsx`** — typography swaps + duplicate-TABS fix + `Print*Modal` wiring. TABS fix is a net positive (vite build was blocked before). ✓
- **`src/components/visit/PrintableVisitSlip.tsx`** — `@page { size: A5; margin: 8mm }`, scoped print CSS, `page-break-avoid` on sections, hidden in screen view via `@media screen { display: none }`, props-driven (no internal data fetching). ✓
- **`src/components/lab/PrintableLabOrder.tsx`** — `@page { size: A5; margin: 8mm }`, table with `page-break-inside: avoid` per row, ✓ Vietnamese labels (`Phiếu Chỉ Định Cận Lâm Sàng`, `Bác sĩ chỉ định`, etc.). Empty items list renders `(0 chỉ định)` heading + empty tbody (functional, no crash).
- **`src/components/billing/PrintablePaymentReceipt.tsx`** — `@page { size: 80mm auto; margin: 4mm }` (matches Locked Decision exactly). 72mm content width, monospace font, divider lines, large amount block, payment method label map covers `cash/card/transfer/momo/vnpay/other`. ✓
- **`src/components/visit/PrintableMedicalSummary.tsx`** — `@page { size: A4; margin: 12mm }`, indigo accent border-left on section headings, alerts box for allergies/chronic, slices visits to first 10 / prescriptions to first 5 / lab_results to first 10 (sane defaults to keep page count bounded). Empty-state messages for visits and prescriptions; lab_results section conditionally hidden when empty. ✓
- **All 4 modal wrappers** — use `print:hidden` Tailwind class on the screen-only modal, render `<PrintableXxx>` alongside, fetch clinic settings via `adminSettingsApi.get()` with 5min staleTime + retry: 0 (correct fail-fast for this UX), `handlePrint = () => window.print()`. ✓

## Decision: APPROVED

Status update: `IN_REVIEW` → `IN_TESTING`. Handoff to Test Agent will be written to `docs/tasks/TASK-051/handoff/review-to-test.md`.

## Focus Areas for Test Agent

- **Manual smoke**: open the 7 modified pages (Dashboard, PatientList, PatientDetail, QueueBoard, InvoiceDetail, PendingDispense, ARAging) — confirm typography is readable and no layout breakage in dense screens.
- **i18n smoke**: clear localStorage `app.language`, force-reload on a machine/browser whose `navigator.language` is `en-US` — confirm app comes up in Vietnamese; manually switch to en in language picker — confirm persists across refresh.
- **Print smoke (each of 4 templates)**:
  1. Open the trigger UI (printer icon / "In ..." button).
  2. In the preview modal, click the "In ... (size)" button → browser print preview opens.
  3. Verify page size is correct (A5 / A4 / 80mm) in the print preview's paper-size dropdown.
  4. Verify only the printable content is visible in print preview (no app shell, no modal chrome).
  5. Verify Vietnamese labels and clinic header / patient info / data render correctly.
- **Empty-state print smoke**:
  - Lab Order from PatientDetailPage with no lab orders: confirm preview shows "Không có xét nghiệm" and printable shows `(0 chỉ định)` with no row data — should NOT crash, should NOT show garbled output.
  - Medical Summary with empty sub-tabs: confirm `Chưa có lịch sử khám` / `Chưa có đơn thuốc` render in print, lab-results section is hidden.
- **Regression**: ensure the BHYT history tab is reachable (when `bhyt` feature flag is on) and renders the stub message under the renamed `bhyt` tab id.
