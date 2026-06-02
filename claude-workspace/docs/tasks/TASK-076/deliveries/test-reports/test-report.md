# Test Report — TASK-076 (Dosage-form category)

**Date**: 2026-06-02

## Unit / static
- BE: `pyflakes` + `ast.parse` clean on model/schema/service/routes/migration. Model imports & maps correctly (`clinic_id` nullable override verified).
- FE: `tsc --noEmit` clean. Tests (run individually — full vitest suite OOMs on this machine):
  - `DosageFormsPage.test.tsx` 12/12 ✅
  - `MedicinesPage.tags.test.tsx` 4/4 ✅
  - `admin.test.tsx` 42/42 ✅

## Migration (docker, Postgres 15, py3.11)
- `alembic upgrade head`: `0037_create_entity_tags -> 0038_create_dosage_form` applied cleanly.
- DB verify: 8 system defaults seeded (clinic_id NULL, is_system=t): tablet/Viên nén, capsule/Viên nang, syrup/Siro, injection/Tiêm, cream/Kem bôi, drops/Thuốc nhỏ, inhaler/Xịt hít, other/Khác.
- Permissions `dosage_form.read` + `dosage_form.manage` created.

## API E2E (admin@DEMO clinic, BE :8001)
| Step | Expected | Result |
|------|----------|--------|
| GET /dosage-forms | 8 | ✅ 8 |
| POST /dosage-forms (gel) | 201, is_system=false, clinic-scoped | ✅ |
| GET /dosage-forms | 9 | ✅ 9 |
| PATCH custom | 200 | ✅ |
| DELETE system row | 403 (blocked) | ✅ 403 |
| DELETE custom | 204 | ✅ |
| GET /dosage-forms | 8 | ✅ 8 |

## Browser E2E (Playwright, FE :1420 → BE :8001)
- Login admin/Demo@1234 → `/admin/dosage-forms`: 8 system defaults shown, all "Hệ thống", NO edit/delete actions ✅.
- Sidebar nav "Danh mục dạng bào chế" present under Quản trị ✅.
- Create via UI: code `gel`, name `Gel bôi ngoài da` (Vietnamese UTF-8) → new row shows "Tùy chỉnh" + edit/delete actions ✅.
- `/admin/medicines` → "Thêm thuốc" modal → dosage-form dropdown lists the category incl. `gel → "Gel bôi ngoài da"` ✅. Table maps code→name (Viên nén, Kem bôi, Tiêm, Xịt hít...).
- Console: only Tauri SQL-plugin browser-mode warnings (expected); no feature errors.

## Notes
- `docker/docker-start.sh` has a pre-existing bash syntax error at line 49 (demo-seed block); bypassed by running migrations + uvicorn directly. Recommend the team fix it.
- Demo medicines use some dosage codes outside the 8 seeds (effervescent, eye_drop, infusion, ointment, powder, solution) → displayed via code fallback. Add them to the category for clean labels.
