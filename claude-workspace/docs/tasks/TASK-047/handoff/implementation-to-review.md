# Handoff: TASK-047 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW
**Branch**: `feature/TASK-047-print-receipts` (repo: `clinic-cms-web`)
**Commit**: `391c09b`

---

## Summary

Implemented native browser print (`window.print()` + CSS `@media print`) for invoices (A4) and prescriptions/phiếu khám (A5) in the FE desktop app. Two new print-only components and one wrapper modal were created; existing `PrintModal.tsx` was rewritten to use the A4 layout instead of the old 80mm thermal receipt template.

---

## Files Changed

### New files
- `src/components/billing/PrintableInvoice.tsx` — A4 invoice print-only component. Clinic info header, patient box, line items table with page-break-inside:avoid, subtotal/VAT/total summary, payment method, signature lines, footer.
- `src/components/doctor/PrintablePrescription.tsx` — A5 prescription print-only component. Clinic header, patient info, visit details, medication table, doctor notes, signature line.
- `src/components/doctor/PrintPrescriptionModal.tsx` — Screen-only modal wrapper for prescription print. Shows preview summary + "In phiếu (A5)" button → `window.print()`. Fetches clinic settings via `adminSettingsApi`.
- `src/tests/billing/PrintableInvoice.test.tsx` — 9 unit tests for PrintableInvoice.
- `src/tests/doctor/PrintablePrescription.test.tsx` — 12 unit tests for PrintablePrescription.

### Modified files
- `src/components/billing/PrintModal.tsx` — Rewritten: now uses `PrintableInvoice` (A4) instead of the old 80mm thermal `LocalReceiptTemplate`. Also loads clinic settings via `adminSettingsApi`. Added optional `patient` prop.
- `src/pages/patients/PatientDetailPage.tsx` — TASK-047 additions:
  - Import `Printer` icon, `PrintPrescriptionModal`, `PrintModal`, `billingApi`, `Invoice` type.
  - `PrescriptionsTab`: now accepts `patient?: PatientRecord` prop; added `useState<Prescription | null>(null)` for active print; added "In phiếu" button per row; renders `PrintPrescriptionModal` when triggered.
  - `InvoicesTab`: now accepts `patient?: PatientRecord` prop; added `useState<Invoice | null>(null)` for active print; added "In hóa đơn" button per row; `handlePrintInvoice` fetches full invoice via `billingApi.getInvoice()` with fallback from summary. Renders `PrintModal` when triggered.
  - Call sites updated: `<PrescriptionsTab patient={patient}>` and `<InvoicesTab patient={patient}>`.
- `src/modules/admin/api.ts` — Pre-existing uncommitted change (carried from main branch per user decision). Not touched by this task.

---

## Architecture Decisions Made

1. **Print DOM approach**: Print-only components are rendered as siblings to the modal backdrop. They use `display:none` on screen and become visible only during `@media print`. The `body > *:not(#print-root)` rule hides all other DOM. This avoids iframes and keeps the component tree simple.

2. **Clinic info**: Loaded via `adminSettingsApi.get()` with `retry:0` and `staleTime: 5min`. Falls back to default values (`"Phòng Khám"`, empty strings) if the API is unavailable — print still works.

3. **Patient info**: Passed as optional props from `PatientDetailPage` (where the patient object is already loaded). No additional API call needed.

4. **Invoice in InvoicesTab**: Clicking "In hóa đơn" on an InvoiceSummary row calls `billingApi.getInvoice()` to get full lines + payments. If that call fails, a minimal Invoice is constructed from the summary so the modal still opens (without line items).

5. **Prescription print from PatientDetailPage**: Uses the full `Prescription` object (already loaded by the list query which returns full prescriptions including `items[]`). No additional fetch needed.

6. **Doctor's ConsultationPage prescription print** (existing `PrescriptionTab.tsx`): NOT changed — that uses the BE `/print` endpoint returning HTML. Different flow, different context.

7. **`PrintPrescriptionModal` vs `PrintModal`**: Kept separate to allow A4 vs A5 page sizing independently. The `@page` CSS block in each component specifies the correct paper size.

---

## Test Results

- **New unit tests**: 21/21 passed
  - `PrintableInvoice.test.tsx`: 9 tests — clinic name, invoice number, patient info, line items, discount reason, payment method label, signature lines, address/tax code, NHÁP fallback, no-clinic-prop fallback
  - `PrintablePrescription.test.tsx`: 12 tests — clinic name, patient name/code, visit number, chief complaint, active items, deleted items exclusion, dosage, doctor notes, doctor name in signature, signature title, no-clinic-prop fallback, "Phiếu Khám Bệnh" title
- **Full regression suite**: 799/799 passed (up from 778, added 21 new)
- **TypeScript**: 0 new errors (3 pre-existing errors in `Sidebar.tsx` and `LoginPage.tsx`, not related to this task)
- **ESLint**: 0 errors in changed files (16 pre-existing errors in unrelated files)

---

## Areas for Review Focus

1. **Print CSS `body > *:not(#print-root)` approach** — Review if this robustly hides Tauri's webview chrome (sidebar, topbar). Alternative: use `visibility:hidden` on body + `visibility:visible` on printable. Either approach is valid; current choice avoids potential stacking context issues.

2. **Two `id="print-root"` / `id="prescription-print-root"** — If both `PrintModal` and `PrintPrescriptionModal` are open simultaneously (unlikely in practice but technically possible if two state vars are set), there'd be two `#print-root` elements. Since modals are mutually exclusive in usage, this is acceptable but worth noting.

3. **`handlePrintInvoice` in InvoicesTab is async** — The `onClick` handler is `async` and calls `billingApi.getInvoice()`. There's no loading spinner while the fetch is in-flight. For review: is a brief loading state needed? Current behavior: button click triggers fetch, modal opens when data arrives. UX is acceptable but could be improved.

4. **`PatientRecord` type alias** — Added `import type { PatientUpdateRequest, Patient as PatientRecord }` to avoid collision with the `Patient` type from `doctor/types.ts` which is also imported. Review that this alias is clear.

5. **`Invoice` fallback in `handlePrintInvoice`** — When `billingApi.getInvoice()` fails, the fallback Invoice has `lines: []` and `payments: []`. The PrintableInvoice will render an empty line items table. This is acceptable fallback behavior.

---

## Open Questions for Review Agent

1. **Header repetition on multi-page invoices**: The task spec says "header lặp lại trên mỗi trang" for multi-page invoices. Current implementation uses `<thead>` in the HTML table which browsers should repeat on page break — but this is browser-dependent. Should we add explicit `thead { display: table-header-group }` CSS? (Minor UX, not a blocker.)

2. **Logo rendering**: `logo_url` is always `null` in the current admin API mapping (hardcoded). The template has the `<img>` branch for when it's set. No action needed now, but flagging for awareness.

3. **`InvoiceSummary.visit_id`** is included in the invoice row but the prescription list doesn't have a `visit_id` exposed in the `Prescription` type from `PatientDetailPage` context. We pass `visit?: VisitInfo` as optional to `PrintPrescriptionModal`, and since the list view doesn't load visit details per prescription, `visit` will be `undefined` — the visit section is skipped gracefully.
