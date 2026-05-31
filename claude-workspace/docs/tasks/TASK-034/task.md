---
id: TASK-034
type: feature
title: BHYT toggle wiring (CFG-017) — feature flag primitive + 11 UI gates + BhytConfigPage + BhytReportPage
status: DONE
priority: High
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
completed: 2026-05-01
branch: feature/task-034-bhyt-toggle
jira_key: ""
tags: [bhyt, feature-flag, multi-area, ux, cfg-017]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/TAB_MATRIX.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/2542650746708884228"
  confluence: ""
  jira_ticket: ""
  other:
    - "../../../docs/clinic_management_function_list.md"
    - "../TASK-032/deliveries/final-specs/audit-report.md"
    - "../TASK-032/handoff/fe-audit-report.md"
    - "../TASK-032/handoff/be-audit-report.md"
---

# TASK-034: BHYT toggle wiring (CFG-017)

## Description

Implement `clinic.bhyt_enabled` feature flag and gate 11 UI areas + BE endpoints accordingly. Build feature-flag primitive `app/core/feature_flags.py` reusable for future toggles (telehealth, emergency, etc.). Default OFF for new clinics; existing clinics may opt-in.

## Requirements

### BE (clinic-cms)

- [ ] **B.1** Migration: add `clinic.bhyt_enabled BOOLEAN NOT NULL DEFAULT false` + `clinic.bhyt_facility_code VARCHAR(50) NULL`
- [ ] **B.2** Update `Clinic` model + `ClinicSettings` schema to include `bhyt` group (mã cơ sở KCB, ngày hết hạn, etc.)
- [ ] **B.3** New `app/core/feature_flags.py` — `Depends(require_feature("bhyt"))` returns 404 when flag OFF
- [ ] **B.4** Apply feature gate to all `/bhyt/*`, `/integrations/vss/*`, `/reports/bhyt/*` route groups
- [ ] **B.5** Update `rbac_service.get_user_effective_permissions` to short-circuit `bhyt:*` perms when flag OFF
- [ ] **B.6** Seed permissions `bhyt:read`, `bhyt:write`, `bhyt:config`, `bhyt:reports` in migration
- [ ] **B.7** Settings endpoints to enable/disable + validate `bhyt_facility_code` (regex 5 digits + 4 letters)

### FE (clinic-cms-web)

- [ ] **F.1** New `stores/featureFlagsStore.ts` hydrated from login response `clinic.feature_flags.bhyt_enabled`
- [ ] **F.2** New `pages/admin/BhytConfigPage.tsx` — settings tab with facility code input + enable toggle + confirm modal
- [ ] **F.3** New `pages/reports/BhytReportPage.tsx` — funnel + sync status (gated)
- [ ] **F.4** Gate 11 UI areas with `useFeatureFlag('bhyt')`:
  - Settings tab "BHYT" (hide if OFF)
  - Reports tab "BHYT" (hide if OFF)
  - Integrations tab "VSS" (hide if OFF)
  - ServicesPage "BHYT price" column (hide if OFF)
  - PatientRegisterPage "BHYT card" field (hide if OFF)
  - PrescriptionTab "BHYT line" (hide if OFF)
  - LabOrdersTab "BHYT chỉ định" (hide if OFF)
  - InvoiceDetailPage "BHYT line" (hide if OFF)
  - Sidebar nav item "BHYT" (hide if OFF)
  - Patient profile tab "Lịch sử BHYT" (hide if OFF)
  - MedicinesPage "Có BHYT" filter (hide if OFF)
- [ ] **F.5** Confirm modal on toggle change ("Bật/Tắt sẽ ẩn/hiện 11 khu vực — xác nhận?")
- [ ] **F.6** i18n vi/en keys for `bhyt.*` namespace

## Acceptance Criteria

- [x] Default new clinic: `bhyt_enabled=false`; all 11 UI areas hidden; all `/bhyt/*` endpoints return 404
- [x] Toggle ON via settings → 11 areas appear after page reload (or live via subscription)
- [x] Toggle OFF with existing BHYT data → confirm modal warns "Dữ liệu BHYT vẫn lưu, chỉ ẩn UI"
- [x] BE endpoint test: `GET /bhyt/...` returns 404 when flag OFF, 200 (with auth) when flag ON
- [x] BE permission test: user with `bhyt:read` cannot access endpoint when flag OFF
- [x] FE conditional rendering tested for all 11 areas (10/11 wired; Gate #7 LabOrdersTab DEFERRED — component does not exist, depends TASK-033/041)
- [x] FE: tests pass; BE: tests pass

## Dependencies

- Blocked by: TASK-033 (multi-clinic — clinic.bhyt_enabled is per-tenant), TASK-039 (BhytConfigPage uses MediZen tokens), TASK-041 (Rx/Invoice consumers must exist for line gating to be testable)
- Blocks: none

## Effort

**Medium-Large** (2 days). Flag primitive small; 11 UI gates mechanical.

## Risk

LOW (additive flag with default OFF). Existing single-clinic deploy is unaffected (defaults preserve current behavior — no BHYT visible).

## Notes

- Discovery via TASK-032 BE audit B.2 + FE audit A.5.
- See `docs/design/medizen-modern/TAB_MATRIX.md` for the canonical 11 UI areas list.

## Completion Notes (2026-05-01)

DONE. 10/11 UI gates wired; Gate #7 (LabOrdersTab) deferred pending TASK-033/041.
33 BE tests + 547 FE tests passing. i18n parity fixed (4 keys added post-review).

Functional design: [deliveries/final-specs/bhyt-toggle-functional-design.md](deliveries/final-specs/bhyt-toggle-functional-design.md)

Deferred follow-ups:
- Gate #7 LabOrdersTab wire (TASK-033/041 dependency)
- Audit log on PATCH /settings/bhyt (Finding 2)
- User-perm cache invalidation on toggle (Finding 3)
- VssSyncPanel extraction to IntegrationsPage (Wave 3 pragma)
