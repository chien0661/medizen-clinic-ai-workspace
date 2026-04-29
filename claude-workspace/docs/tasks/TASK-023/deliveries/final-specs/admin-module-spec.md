# TASK-023 Admin Module — Functional Design

## Module: FE Admin (Users + Roles + Clinic Settings + Vital Schema Editor + Onboarding Wizard)

**Branch:** `feature/task-023-fe-admin`  
**Commit:** e56b93d  
**Date:** 2026-04-27  
**Status:** DONE

---

## Pages Delivered

| Route | Component | BE Status | Permission |
|---|---|---|---|
| `/admin/users` | UsersPage | REAL (TASK-004) | user.manage |
| `/admin/roles` | RolesPage | REAL (TASK-004) | role.manage |
| `/admin/users/:id/extra-permissions` | ExtraPermissionsPage | REAL (TASK-004) | user.manage |
| `/admin/settings` | SettingsPage | STUB (TASK-006) | settings.clinic |
| `/admin/vitals` | VitalsPage | STUB (TASK-009) | settings.vital_schema |
| `/admin/services` | ServicesPage | REAL (TASK-010) | service.catalog.manage |
| `/admin/medicines` | MedicinesPage | STUB (TASK-012) | medicine.manage |
| `/admin/audit` | AuditPage | STUB (audit endpoint TBD) | audit.read |
| `/onboarding` | OnboardingPage | STUB (TASK-006) | (any admin) |

---

## Architecture

- `src/modules/admin/types.ts` — TypeScript interfaces matching TASK-004/006/009/010/012 Pydantic schemas
- `src/modules/admin/api.ts` — API client (real + mock layers with TODO markers)
- `src/modules/admin/mockData.ts` — Demo data for stub pages
- `src/pages/admin/*.tsx` — 9 page components
- `src/locales/{vi,en}/admin.json` — Full bilingual i18n (Vietnamese + English)
- `src/tests/admin/admin.test.tsx` — 41 tests (i18n, mock API, Zod validation, AC traceability)

---

## Stub Map

| Page | Stub Reason | Unblock By |
|---|---|---|
| SettingsPage | TASK-006 BE not merged to main | TASK-006 merge |
| VitalsPage | TASK-009 in progress | TASK-009 complete |
| MedicinesPage | TASK-012 in progress | TASK-012 complete |
| AuditPage | Audit endpoint not confirmed on demo BE | BE team confirm endpoint |
| OnboardingPage | TASK-006 BE not merged | TASK-006 merge + re-seed |

All stub pages display Beta badge and note explaining deferral.

---

## AC Verification

| AC | Status | Notes |
|---|---|---|
| AC1: user + extra_grant invoice.void | PASS | ExtraPermissionsPage grant/deny editor implemented |
| AC2: uncheck prescription.write → role save | PASS | RolesPage matrix checkbox grid saves permissions |
| AC3: slot_duration=20 reflects calendar | DEFERRED | Requires TASK-018 FE + real BE integration |
| AC4: vital rename label → new version | PASS | VitalsPage label edit + version increment tested |
| AC5: vital rename key disabled | PASS | Key field disabled in edit mode with hint message |
| AC6: pediatric → 5 preset vitals | DEFERRED | Requires TASK-006 BE real onboarding |
| AC7: audit filter patient.update | PASS | AuditPage filter + mock returns correct records |
| AC8: CSV 1000 rows < 30s | DEFERRED | Requires real BE + performance test setup |
