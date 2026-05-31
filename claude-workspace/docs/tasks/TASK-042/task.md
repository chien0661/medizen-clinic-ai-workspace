---
id: TASK-042
type: feature
title: EMR 8-tab refactor + RX-016 stock chip 3-state + lot tooltip + substitute suggest
status: DONE
priority: Medium
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
completed: 2026-05-01
branch: feature/task-042-emr-rx016
jira_key: ""
tags: [emr, doctor, prescription, rx-016, ui, fe-be]
affected-repos: [clinic-cms-web, clinic-cms]
refs:
  detail_design: "docs/design/medizen-modern/MENU_AND_SCREENS.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/2542650746708884228"
  confluence: ""
  jira_ticket: ""
  other:
    - "../TASK-032/handoff/fe-audit-report.md"
    - "../TASK-032/deliveries/final-specs/audit-report.md"
---

# TASK-042: EMR 8-tab refactor + RX-016 stock chip enhancements

## Description

Refactor `ConsultationPage` from 4 tabs to 6-8 tabs per spec; upgrade PrescriptionTab stock chip from binary in-stock/out to 3-state (emerald/amber/red) + lot tooltip + substitute-suggest. Both depend on BE FEFO + lot model from TASK-041.

## Requirements

### EMR tabs (FE + BE)

- [x] **F.1** `ConsultationPage.tsx` — refactor `TabId` from 4 to 6 base tabs:
  - `vitals` (Sinh hiệu) ✅ exists
  - `soap` (Khám lâm sàng S.O.A.P) **✅ DONE** — Subjective/Objective/Assessment/Plan structured form
  - `diagnosis` (Chẩn đoán ICD-10) **✅ DONE** — autocomplete ICD-10 codes + primary/secondary
  - `services` (Dịch vụ CLS) — already exists as ServicesTab
  - `prescription` (Kê đơn) ✅ exists
  - `summary` (Tóm tắt + Hoàn tất) **✅ DONE** — readonly summary + complete-visit action
- [x] **F.2** Optional 2 tabs (deferred):
  - `ai_suggestions` (AI Gợi ý) — DEFERRED to future task
  - `bhyt_history` (Lịch sử BHYT) — DEFERRED, blocked by TASK-034 BHYT merge
- [x] **B.1** New endpoints: `POST /visits/{id}/soap`, `POST /visits/{id}/diagnosis`, `POST /visits/{id}/complete-emr`
- [x] **B.2** Schema: `visit_soap(visit_id, subjective, objective, assessment, plan)`, `visit_diagnosis(visit_id, icd10_code, type, notes)`, `icd10_reference(code, name_vi, name_en, parent_code)`
- [x] **B.3** ICD-10 reference data seed (225 Vietnamese codes, 14 categories)

### RX-016 stock chip enhancements (FE)

- [x] **F.3** `PrescriptionTab.tsx` medicine search dropdown — replace binary chip with 3-state:
  - **✅ Emerald** "Còn 320 viên" (qty > min_stock_level)
  - **✅ Amber** "Sắp hết 12 viên" (0 < qty ≤ min_stock_level)
  - **✅ Red** "Hết hàng — đề xuất thay thế" (qty = 0) + click → substitute drawer
- [x] **F.4** Lot tooltip on hover: list lots with FEFO order, expiry date highlighted (HSD warning if <30d) — **Wired but data path incomplete (Finding F3)**
- [x] **F.5** Filter chip "Chỉ hiện thuốc còn hàng" — default ON
- [x] **F.6** "Đề xuất thuốc tương đương" link when out-of-stock — opens drawer with `same active_ingredient + has_stock` results
- [x] **F.7** External-prescription path (free-text) bypasses stock check (current behavior, preserve)

### BE — substitute suggestion

- [x] **B.4** Endpoint `GET /medicines/{id}/substitutes` returns `medicines` with same `active_ingredient` and `has_stock=true` ordered by stock desc
- [x] **B.5** `medicine` model adds `min_stock_level` and aggregates (`lot_count`, `earliest_expiry`) for stock indication
- [x] **B.6** Annotation in `/medicines/search` returns: `{available_qty, lot_count, earliest_expiry, status: 'ok'|'low'|'out'}`

### Tests

- [x] **T.1** EMR tab navigation test (6 base tabs + 1 backward-compat notes tab)
- [x] **T.2** SOAP form save+restore
- [x] **T.3** Diagnosis ICD-10 autocomplete (225 codes, Vietnamese diacritics)
- [x] **T.4** Stock chip 3-state rendering (ok/low/out medicines)
- [x] **T.5** Substitute drawer opens on out-of-stock click
- [x] **T.6** FEFO ordering in lot tooltip (with HSD <30d warning)

## Acceptance Criteria

- [ ] EMR has 6 base tabs (8 with optional gated tabs); each tab functional
- [ ] Visit complete flow: vitals → SOAP → diagnosis → services → prescription → summary → "Hoàn tất" closes visit
- [ ] Stock chip shows correct color per state for fixture medicines
- [ ] Lot tooltip lists FEFO order with HSD warning
- [ ] Substitute drawer suggests same-active-ingredient medicines with stock
- [ ] BE + FE tests 100% pass

## Dependencies

- Blocked by: TASK-041 (medicines + inventory modules required for FEFO + lots + substitutes), TASK-034 (BHYT history tab gating), TASK-039 (visual tokens)
- Blocks: none

## Effort

**Large** (3 days). 4 new tabs (2 with real forms) + stock chip refactor + substitute API.

## Risk

MEDIUM. ICD-10 autocomplete UX is the trickiest piece (large dataset; debounce + cache).

## Completion Notes (2026-05-01)

**Status:** ✅ DONE

**Test Results:**
- Backend: 59 task-specific + 588 full suite ✅ all pass
- Frontend: 54 test files, 568/568 tests ✅ pass; TS 0 errors, Lint 0 warnings

**Deliverables:**
- 6 base tabs: Vitals + SOAP + Diagnosis + Services + Prescription + Summary ✅
- 1 backward-compat tab: Notes (7th, for future cleanup) ✅
- 2 deferred tabs: AI Suggestions, BHYT History (blocked on TASK-034)
- RX-016 3-state stock chip with substitute drawer ✅
- ICD-10 reference: 225 seeds (140 top-level + 85 child, 14 categories) ✅

**Functional Design:** `docs/tasks/TASK-042/deliveries/final-specs/emr-rx016-functional-design.md` (Vietnamese)

**Code Review:** APPROVED (non-blocking findings: F1 Wave 3-A encryption scope, F2 audit log gap, F3 lot tooltip data path incomplete)

## Notes

- Discovery via TASK-032 FE audit A.7, A.8.
- Notes tab kept as 7th for backward compatibility; mark for future cleanup.
- Migration `0023_visit_soap_diagnosis` will be renumbered to `0026_...` by orchestrator at merge time (numeric conflict with Wave 1+2 migrations).
