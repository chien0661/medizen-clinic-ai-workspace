# Handoff: TASK-080 → Code Review

**From**: Code Implementation Agent
**To**: Code Review Agent
**Status**: IN_REVIEW
**Date**: 2026-06-16

---

## Summary

Rewrote `PrintablePrescription.tsx` from the old "Phiếu Khám Bệnh" table layout (TASK-047) to the new "ĐƠN THUỐC" dotted-line format matching `refs/prescription-template-sample.png`. Added a configurable `prescription_template` settings group in the BE (stored in JSONB — no migration needed), added `user.title` column (Alembic migration 0042), created a settings panel in `SettingsPage`, and fixed BUG-077-004 by routing the "In đơn thuốc" button in `PrescriptionTab` through `PrintPrescriptionModal`.

---

## Commit SHAs

### `clinic-cms` (backend) — branch `feature/TASK-080-prescription-template`
- `44088a8` — `feat(prescription-template): add PrescriptionTemplateSettings schema, user.title column and migration (TASK-080)`
- `25d4bb9` — `fix(prescription-template): fix ruff lint issues in migration and user schemas (TASK-080)`

### `clinic-cms-web` (frontend) — branch `feature/TASK-080-prescription-template`
- `dbc13f0` — `feat(prescription-template): rewrite PrintablePrescription to ĐƠN THUỐC layout (TASK-080)`
- `44e19fe` — `feat(prescription-template): add prescription template config panel in SettingsPage (TASK-080)`
- `bc7a63f` — `feat(prescription-template): add user title field and i18n keys for prescription template (TASK-080)`
- `7ba90b7` — `fix(prescription-template): wire PrintPrescriptionModal in PrescriptionTab, fix BUG-077-004 print path (TASK-080)`

---

## Files Changed

### Backend (`clinic-cms`)

| File | Change |
|------|--------|
| `app/modules/admin/schemas/settings_schemas.py` | Added `PrescriptionTemplateSettings` Pydantic model (12 fields, validation: paper_size pattern A4\|A5, min_medicine_rows ge=1 le=20). Added `prescription_template: PrescriptionTemplateSettings` to `ClinicSettingsResponse`. Added `prescription_template: dict[str, Any] | None = None` to `ClinicSettingsPatchRequest`. |
| `app/modules/admin/services/default_settings.py` | Added `prescription_template` key to `get_default_settings()` return dict with all 12 default values matching the sample image (pediatric clinic). |
| `app/modules/users/models/user.py` | Added `title: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)` after `specialty_subfield`. NOT added to `__audit_exclude__` — title is not PII. |
| `app/modules/users/schemas/user_schemas.py` | Added `title: str | None = Field(default=None, max_length=100)` to `UserCreate`, `UserUpdate`; added `title: str | None` to `UserResponse`. Removed unused `EmailStr` import (ruff fix). |
| `alembic/versions/0042_add_user_title.py` | New migration: `ALTER TABLE user ADD COLUMN title VARCHAR(100)` (nullable). `down_revision = "0041_add_vital_field_status"`. |
| `tests/unit/test_prescription_template_settings.py` | New unit tests: 7 tests covering `PrescriptionTemplateSettings` defaults, valid/invalid paper sizes, min_medicine_rows bounds, custom values, and `get_default_settings()` integration. |

### Frontend (`clinic-cms-web`)

| File | Change |
|------|--------|
| `src/components/doctor/PrintablePrescription.tsx` | Full rewrite: new `VisitInfo` interface (added `doctor_title`, `diagnosis`, `weight`, `gender`, `address`, `date_of_birth`), new `Props` with `config?: PrescriptionTemplateConfig`, new "ĐƠN THUỐC" layout: left header, centered title, patient block (DOB+weight+gender inline), numbered dotted medicine rows padded to `min_medicine_rows`, `*`-prefixed advice/followup text, right-aligned signature with Vietnamese weekday date, footer lines. Dynamic `@page size` from config. |
| `src/components/doctor/PrintPrescriptionModal.tsx` | Updated to load `prescription_template` from clinic settings, build config from it (fallback to clinic info if missing), pass `config` prop to `PrintablePrescription`. UI label changed to "In Đơn Thuốc". |
| `src/components/doctor/PrescriptionTab.tsx` | Replaced `printMutation` + dangerouslySetInnerHTML preview with `PrintPrescriptionModal` component. Fixes BUG-077-004: print button now opens modal with full template. |
| `src/pages/admin/SettingsPage.tsx` | Added `PrescriptionTemplateTab` component with form fields for all 12 config fields (header, paper size, min rows, toggles, advice, followup, footer lines, signature). Added `"prescriptionTemplate"` to `BASE_TABS`. |
| `src/modules/admin/types.ts` | Added `PrescriptionTemplateConfig` interface. Added `prescription_template?: PrescriptionTemplateConfig` to `ClinicSettings`. Added `title?: string | null` to `AdminUser` and `AdminUserUpdate`. |
| `src/pages/admin/UsersPage.tsx` | Added `title` field to `editUserSchema` and Edit User modal form. |
| `src/locales/vi/admin.json` | Added `users.form.title`, `users.form.titlePlaceholder`, `settings.tabs.prescriptionTemplate`, `settings.prescriptionTemplate.*` (13 keys). |
| `src/locales/en/admin.json` | Same keys in English. |
| `src/tests/doctor/PrintablePrescription.test.tsx` | Rewrote all 20 tests to match new ĐƠN THUỐC layout. Tests cover: config-based header, title, patient fields (name/DOB/weight/gender/address/diagnosis), medicine items (active/excluded-deleted), advice/followup, signature label/doctor, footer, default config fallback, show_weight=false, show_diagnosis=false. |

---

## Test Results

### Frontend (vitest)
- **PrintablePrescription.test.tsx**: 20/20 ✅
- **PrescriptionTab-stock.test.tsx**: 7/7 ✅ (unchanged, confirmed passing)
- **All TASK-080 tests**: 20/20 pass
- Pre-existing failures (NOT caused by TASK-080): `secureStore.test.ts` (TASK-079 localStorage change), `ConsultationPage.test.tsx`, `useSync.test.ts` — 9 failures total, pre-existing on base branch.

### Backend (pytest unit)
- **test_prescription_template_settings.py**: 7/7 ✅
- **All unit tests**: 928 passed, 2 pre-existing failures in `test_rls_helpers.py` (unrelated to TASK-080)

### Lint
- **BE ruff**: all TASK-080 files pass cleanly
- **FE eslint**: all TASK-080 files pass cleanly (pre-existing errors in `VssSyncLogPage.tsx` unrelated)
- **FE TypeScript**: `tsc --noEmit` passes with 0 errors

---

## Review Focus Areas

### 1. TASK-079 base coupling — weight/diagnosis fields
The `VisitInfo` interface now includes `weight`, `gender`, `address`, `date_of_birth`, `doctor_title`, `diagnosis`. These must be populated by callers (`PrintPrescriptionModal`, anywhere else that uses `PrintablePrescription`). Currently `PrintPrescriptionModal.tsx` accepts a `visit?: VisitInfo` prop and forwards it. The billing `PrintPrescriptionModal` is a different component (uses `doctorApi.printPrescription` for HTML server-side rendering) — not deduplicated per plan, as they serve different flows (consultation vs invoice).

Review: are all `VisitInfo` optional fields being passed correctly from `PrescriptionTab` → `PrintPrescriptionModal`? (Currently PrescriptionTab passes no patient/visit info to the modal — see the IIFE in the new code. This is acceptable for draft prescriptions, but reviewer should note this as a gap for the test agent.)

### 2. user.title migration — Alembic revision chain
Migration `0042` has `down_revision = "0041_add_vital_field_status"`. Reviewer should verify the revision chain is unbroken. The migration has NOT been applied to the docker container yet (needs `alembic upgrade head` after merge).

### 3. PrescriptionTemplateSettings in ClinicSettingsResponse
The BE now includes `prescription_template: PrescriptionTemplateSettings` in `ClinicSettingsResponse`. For existing clinics in the DB that don't have this key in their JSONB blob, the Pydantic model applies defaults automatically via `model_validator`. Reviewer should confirm the settings service correctly handles the case where `prescription_template` is absent from the stored JSONB.

### 4. BUG-077-004 partial fix
The `PrescriptionTab` now opens `PrintPrescriptionModal` after saving. However, for completed visits (post-consultation), the print path goes through `billing/PrintPrescriptionModal.tsx` (server-side HTML via `doctorApi.printPrescription`). The "ĐƠN THUỐC" template is only used through the React component path. A full fix for completed visits would need to either: (a) also pass `config` to the billing modal's HTML print path, or (b) switch billing modal to use the React template too. This gap is documented for the Test Agent.

### 5. Diagnosis source ambiguity
`VisitInfo.diagnosis` is provided as an optional field. In practice, it should be populated from `DiagnosisListResponse.items[0].icd10_code + name_vi`. Currently the PrintablePrescription component falls back to `visit.chief_complaint` when `diagnosis` is null — this is the intended behavior per the implementation plan.

---

## Assumptions / Deviations

1. **PrescriptionTab print flow**: builds a synthetic `Prescription` object from draft items to pass to `PrintPrescriptionModal` rather than re-fetching from the API. This is correct because the prescription may not be finalized/submitted yet.
2. **Billing PrintPrescriptionModal**: not merged/deduped — the two modals serve different flows (server HTML vs React component). Documented as a gap.
3. **SettingsPage tab name**: `"prescriptionTemplate"` in camelCase (not snake_case) to be consistent with other tabs in the existing BASE_TABS array.
4. **footer_lines in settings panel**: stored as multi-line textarea (one line per footer entry) for simplicity. The save handler splits by `\n` and trims.
