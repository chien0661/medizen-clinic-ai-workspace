# TASK-042 EMR + RX-016 — Implementation → Review Handoff

**Date:** 2026-05-01
**From:** Code Implementation (Rescue/Finalize agent)
**To:** Code Review

---

## Summary

TASK-042 implements the 6-tab EMR consultation page (SOAP + ICD-10 diagnosis + summary) and RX-016 prescription stock enhancements. The predecessor agent stalled mid unused-imports cleanup; this agent completed all cleanup, fixed TS/lint/test issues, and verified tests.

---

## Scope Delivered

### Tabs Implemented (6/8 base target, 2 deferred)

| Tab | Status | Component |
|-----|--------|-----------|
| Vitals | Existing (pre-042) | `VitalsTab.tsx` |
| SOAP | NEW | `SoapTab.tsx` — 4-field S.O.A.P auto-save on blur |
| Diagnosis | NEW | `DiagnosisTab.tsx` — ICD-10 autocomplete + chips |
| Services | Existing (pre-042) | `ServicesTab.tsx` |
| Prescription | Enhanced (RX-016) | `PrescriptionTab.tsx` — 3-state chip + lot tooltip + substitute drawer |
| Summary | NEW | `SummaryTab.tsx` — readonly aggregate + "Hoàn tất khám" button |
| Notes | Kept (backward compat) | `NotesTab.tsx` — existing, preserved as 7th tab |
| AI Suggestions | DEFERRED | — future task |
| BHYT History | DEFERRED | — blocked on TASK-034 merge |

### BE Files (19 dirty)

**New (untracked):**
- `alembic/versions/0023_visit_soap_diagnosis.py` — migration for 3 new tables + 225 ICD-10 seeds
- `app/modules/visits/api/emr_routes.py` — SOAP/diagnosis/complete/ICD-10 endpoints
- `app/modules/visits/models/visit_soap.py`
- `app/modules/visits/models/visit_diagnosis.py`
- `app/modules/visits/models/icd10_reference.py`
- `app/modules/visits/schemas/emr_schemas.py`
- `app/modules/visits/services/emr_service.py`
- `tests/unit/test_icd10_search.py` (8 tests)
- `tests/unit/test_visit_soap_endpoint.py` (5 tests)
- `tests/unit/test_medicine_stock_status.py` (15 tests)
- `tests/unit/test_medicine_substitutes.py` (8 tests)
- `tests/unit/test_visit_complete_endpoint.py` (11 tests)
- `tests/unit/test_visit_diagnosis_endpoint.py` (12 tests)
- `tests/integration/test_emr_full_flow.py` (integration, not run in unit suite)

**Modified:**
- `app/main.py` — router registration for emr_routes
- `app/modules/prescriptions/api/routes.py` — RX-016 stock/substitute endpoints
- `app/modules/prescriptions/schemas/prescription_schemas.py` — StockStatus, LotInfo, SubstituteResult types
- `app/modules/prescriptions/services/medicine_search_service.py` — min_stock_level 3-state logic
- `app/modules/visits/models/__init__.py` — re-exports for new models

### FE Files (14 dirty)

**New (untracked):**
- `src/components/doctor/SoapTab.tsx`
- `src/components/doctor/DiagnosisTab.tsx`
- `src/components/doctor/SummaryTab.tsx`
- `src/tests/doctor/SoapTab.test.tsx`
- `src/tests/doctor/DiagnosisTab.test.tsx`
- `src/tests/doctor/SummaryTab.test.tsx`
- `src/tests/doctor/PrescriptionTab-stock.test.tsx`

**Modified:**
- `src/components/doctor/PrescriptionTab.tsx` — RX-016 enhancements
- `src/pages/doctor/ConsultationPage.tsx` — 6-tab refactor
- `src/modules/doctor/api.ts` — new EMR API calls
- `src/modules/doctor/types.ts` — new EMR types
- `src/locales/en/doctor.json` — i18n keys
- `src/locales/vi/doctor.json` — i18n keys
- `src/tests/doctor/ConsultationPage.test.tsx` — updated for 6-tab layout

---

## Migration

- **Name:** `0023_visit_soap_diagnosis`
- **Revision:** `0023`
- **Down-revision:** `65fc9ae59ba5` (merge migration in w2d worktree)
- **Tables:** `visit_soap`, `visit_diagnosis`, `icd10_reference`
- **ICD-10 seed:** 225 codes (Vietnamese MOH subset)
- **Also:** adds `min_stock_level` column to `inventory_item`
- **Apply status:** Not applied (container port conflict; unit tests run via file copy into existing container; all 59 TASK-042 unit tests pass)

---

## Test Results

### BE Unit Tests (TASK-042 new tests)
```
59 passed in 0.77s
```
Breakdown: 8 icd10_search + 5 soap_endpoint + 15 medicine_stock_status + 8 medicine_substitutes + 11 visit_complete + 12 visit_diagnosis = 59

Full suite (excluding pre-existing HR failure): **588 passed**
Pre-existing failure: `test_hr_service_logic.py::TestCheckInRejectsOtherUsersShiftId` — unrelated to TASK-042

### FE Tests
- TypeScript (`tsc --noEmit`): **0 errors**
- ESLint (`--max-warnings 0`): **0 warnings**
- Vitest: **568/568 passed** (54 test files)

---

## RX-016 Enhancements Applied

- 3-state stock chip: emerald (ok) / amber (low) / red (out)
- Lot tooltip on hover (FEFO order, expiry warning <30d)
- Filter chip "Chỉ hiện thuốc còn hàng" — default ON, passes `in_stock_only=true` to API
- Substitute drawer when out-of-stock chip clicked
- `min_stock_level` threshold for low/ok determination

---

## Cleanup Done (This Agent)

- Removed unused `useRef` import from `PrescriptionTab.tsx`
- Removed unused `Heart` import from `SummaryTab.tsx`
- Removed unused `useQueryClient` from `ConsultationPage.tsx`
- Fixed `SoapTab.tsx`: `null` → `undefined` for optional SOAP fields (TS2322)
- Removed unused `diagnosisWithItems` fixture from `DiagnosisTab.test.tsx` (TS6133)
- Fixed `useEffect` missing dependency `activeTab` in `ConsultationPage.tsx`
- Fixed i18n mock in 4 test files: `fallback ?? key` → `key` (tests use translation keys for assertions)
- Updated `ConsultationPage.test.tsx`: replaced stale `"visit.completeBtn"` assertions with 6-tab assertions

---

## Deferred Decisions

| Item | Decision | Reference |
|------|----------|-----------|
| BHYT history tab | Blocked on TASK-034 BHYT merge | TASK-034 |
| AI suggestions tab | Deferred to future task | Post-042 |
| Notes tab removal | Kept for backward compat (7th tab, not visible by default) | TASK-042 decision |
| Migration apply in isolation | Requires free container ports — use w2d compose after main compose down | Ops |
