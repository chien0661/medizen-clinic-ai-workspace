---
id: TASK-094
type: feature
title: Fix prescription printing (default template + diagnosis) & add usage / dosage-unit fields
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-18
updated: 2026-07-22
branch: "feature/TASK-094-rx-print-and-prescribing"
jira_key: ""
tags: [prescription, printing, print-template, doctor, pharmacy]
affected-repos: [clinic-cms-web, clinic-cms]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-094/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-094: Fix prescription printing (default template + diagnosis) & add usage / dosage-unit fields

## Description

Several defects and gaps in the **prescription printing** and **prescribing** flow, reported from clinical use:

1. **Trường chẩn đoán in sai** — the diagnosis (Chẩn đoán) field, when dragged onto a print template, shows the wrong value (or nothing). The exam flow saves the diagnosis correctly into `visit.diagnosis`, but every print path reads the wrong source.
2. **Mẫu in mặc định bị bỏ qua** — a clinic can design a prescription template in `/admin/print-templates` and mark it default, but printing an prescription **from the doctor consultation screen** still uses the built-in system layout. Only the billing/visit-detail print path honors the default template.
3. **Thiếu option ẩn/hiện từng trường trên khung giấy in** — the template builder can show/hide sub-fields inside blocks, but not individually placed fields (e.g. the diagnosis field).
4. **Thiếu trường "cách dùng"** — prescribing has no structured usage-timing field (uống trước ăn / sau ăn / …); it only exists as free-text hints inside the single `dosage` field.
5. **Đơn vị liều chưa theo dạng thuốc** — the dosage/quantity unit does not follow the medicine's dosage form (viên→viên, gói→gói, lọ→ml, …); it is free-text defaulted from `base_unit`.

> Scope note: the legacy server-side HTML print endpoint (`GET /api/v1/prescriptions/{id}/print`) is stale and unused by the React print flow — do **not** invest there; it may be deprecated separately.

## Requirements

### A. Diagnosis prints correctly (BUG)
- [ ] Custom-template callers must populate the `visit.diagnosis` field key from the real `visit.diagnosis`, not `visit.notes`:
  - `clinic-cms-web/src/components/billing/PrintPrescriptionModal.tsx` (~line 258)
  - `clinic-cms-web/src/components/doctor/PrintExamFormModal.tsx` (~line 183)
- [ ] `VisitInfo`-based callers must pass `diagnosis` through (the `VisitInfo` type already declares it — `PrintablePrescription.tsx:27`):
  - `clinic-cms-web/src/components/doctor/PrescriptionTab.tsx` (~lines 1052-1060)
  - `clinic-cms-web/src/pages/visits/VisitDetailPage.tsx` (~lines 477-482)
- [ ] Confirm `DiagnosisTab.tsx` continues to save into `visit.diagnosis` (currently correct — verify no regression).

### B. Doctor prescription print honors the saved default template (BUG)
- [ ] `clinic-cms-web/src/components/doctor/PrintPrescriptionModal.tsx` (opened from `PrescriptionTab.tsx:1062` "In đơn thuốc") must select the clinic's default `prescription` template the same way `billing/PrintPrescriptionModal.tsx` does (find `is_default && !is_system` → `is_default` → fallback to built-in `PrintablePrescription`), and render via `TemplateRenderer` when one exists.
- [ ] Reuse the existing default-selection logic rather than duplicating it (extract a shared helper/hook if practical).

### C. Per-field show/hide on the print template builder (FEATURE)
- [ ] Add a per-field visibility toggle for individually placed fields on the template canvas (e.g. a `hidden` flag on `LayoutElement` in `printTemplates.ts`), surfaced in `PrintTemplatesPage.tsx`, so a placed field (e.g. `visit.diagnosis`) can be hidden without deleting it.
- [ ] `TemplateRenderer.tsx` must skip hidden fields when rendering.

### D. Structured "cách dùng" (usage timing) field (FEATURE)
- [ ] Add a usage-timing field to the prescription item across the stack:
  - Backend model `clinic-cms/app/modules/prescriptions/models/prescription_item.py`
  - Backend schemas `prescription_schemas.py` (`PrescriptionItemCreate/Update/Response`)
  - Alembic migration (sequential `NNNN_*.py`)
  - Frontend types `clinic-cms-web/src/modules/doctor/types.ts` (`PrescriptionItem` + `PrescriptionItemCreate`)
  - Prescribing UI `PrescriptionTab.tsx` (a select/combobox with common values: uống trước ăn, uống sau ăn, uống trong khi ăn, trước khi ngủ, …; free-text still allowed)
  - Print template field catalog (`FIELD_CATALOG.prescription` in `printTemplates.ts`) + built-in `PrintablePrescription` layout
- [ ] Decide field name (suggest `usage_instruction` / `meal_timing`) and whether it's an enum + free-text — record the decision in the final spec.

### E. Dosage unit follows the medicine's dosage form (FEATURE)
- [ ] The quantity/dosage unit shown when prescribing should be driven by the medicine's dosage form, not free-typed. Note (from investigation): the `DosageForm` catalog (`DosageFormsPage.tsx`) currently has **no unit column** — the only per-medicine unit is `Medicine.base_unit`. Choose an approach and document it:
  - (Preferred) add a display/base `unit` column to `DosageForm` and map medicine → dosage_form → unit; or
  - derive from `Medicine.base_unit` where dosage form maps 1:1 (e.g. lọ→ml requires an explicit mapping, so a unit column is likely required).
- [ ] Apply the resolved unit in `PrescriptionTab.tsx` (replace the hard-coded `"viên"` / raw `base_unit` default) and on the printed output.

## Acceptance Criteria

- [ ] Printing a prescription **from the doctor consultation** ("In đơn thuốc") uses the clinic's default prescription template when one is set; falls back to the built-in layout only when none exists — identical behavior to the billing path.
- [ ] A prescription whose visit has a saved diagnosis prints that exact diagnosis text in the diagnosis field on **all** paths (doctor modal, billing modal, exam form, visit detail) — never the visit notes or chief complaint.
- [ ] On the template builder, a placed field can be toggled hidden and the hidden field does not appear on the printed/preview output; toggling it back restores it.
- [ ] When prescribing, the doctor can set a structured "cách dùng" value per medicine (before/after meal, etc.); it is saved, reloaded on edit, and printed.
- [ ] The dosage/quantity unit reflects the medicine's dosage form (viên→viên, gói→gói, lọ→ml, …) both in the prescribing UI and on the printout.
- [ ] Backend: new fields covered by Alembic migration + updated schemas; DB-backed integration test for create/read of the new usage field; unit follows dosage form.
- [ ] No regression in `PrintablePrescription.test.tsx`, `PrescriptionTab-stock.test.tsx`, `ExamTab.test.tsx`, `SummaryTab.test.tsx`; `ruff`/`mypy` and `tsc`/`eslint` clean.

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing (BUG-094-001, BUG-094-002 fixed + re-verified live, all pass)
- [x] Documentation (completed 2026-07-22: functional design + API specs)

## Related Files

- **Input Specs**: `docs/tasks/TASK-094/refs/` *(DetailDesign, SRS, implementation-plan)*
- **Code**: (feature branch)
- **Tests**: `docs/tasks/TASK-094/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-094/handoff/`
- **Test Report**: `docs/tasks/TASK-094/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-094/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-094/deliveries/final-specs/`

### Key source references (from code investigation)

**Print template system** — `clinic-cms-web/src/lib/printTemplates.ts` (`TemplateType`, `FIELD_CATALOG.prescription`, `BLOCK_CATALOG`), `src/components/print/TemplateRenderer.tsx`, `src/pages/admin/PrintTemplatesPage.tsx`.
**Prescription print paths** — `src/components/doctor/PrintPrescriptionModal.tsx` (ignores default template — BUG), `src/components/doctor/PrintablePrescription.tsx` (built-in layout, reads `visit.diagnosis` at line 107), `src/components/billing/PrintPrescriptionModal.tsx` (honors default template; diagnosis-from-notes BUG line 258), `src/components/doctor/PrintExamFormModal.tsx` (diagnosis-from-notes BUG line 183).
**Prescribing** — `src/components/doctor/PrescriptionTab.tsx` (dosage presets, unit default), `src/modules/doctor/types.ts` (`PrescriptionItem` 354-373, `Medicine` 306-309).
**Dosage forms / units** — `src/pages/admin/DosageFormsPage.tsx` (no unit column), `src/pages/admin/MedicinesPage.tsx`; backend `clinic-cms/app/modules/inventory/models/medicine.py` (`dosage_form`, `dosage_form_id`, `base_unit`).
**Backend prescriptions** — `clinic-cms/app/modules/prescriptions/models/prescription_item.py`, `schemas/prescription_schemas.py`, `api/routes.py` (`/prescriptions/{id}/print` — legacy/stale), `app/modules/visits/models/visit.py:96` (`Visit.diagnosis`), `DiagnosisTab.tsx:102` (save).

## Timestamps

- **Created**: 2026-07-18
- **Started**: 2026-07-22 (Phase 1 implementation, /complete-task)
- **Implementation Completed**: 2026-07-22
- **Documentation Completed**: 2026-07-22

## Notes

- Bugs (A, B) and features (C, D, E) are bundled per the reporter's single request. If the team prefers, A+B can be split into a `BUG-` task and C/D/E kept as the feature — flag during `/task-plan`.
- D and E both touch the prescription item schema + prescribing UI + print field catalog; sequence them together to avoid two migrations.
- E likely requires a new `unit` column on `DosageForm` (viên→viên is identity, but lọ→ml is not derivable from the form name) — confirm the data-model decision before implementation and capture it in `final-specs/`.
- The `built-in` `PrintablePrescription` also has its own visibility config in `admin/types.ts` (`PrescriptionTemplateConfig`: `show_diagnosis`, `show_weight`, …) set on clinic Settings — keep consistent with the new drag/drop per-field toggle (C).

## Blockers

None — BUG-094-001 and BUG-094-002 fixed (commit `79210c4`) and re-verified live in re-test iteration 2. Known accepted limitation (cashier role lacks `prescription.print`, still 403s on template read) is explicitly out of scope, documented in the test report, not a blocker.
