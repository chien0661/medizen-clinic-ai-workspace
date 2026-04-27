---
id: TASK-006
type: feature
title: Clinic Settings + Tenant Onboarding Wizard
status: TODO
priority: Medium
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [tenant, onboarding, settings, sprint-3]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#5-module-tenancy--audit"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#1513-tenant-onboarding-flow"
    - "../../../../docs/clinic_management_business_analysis.md#152-settings-per-clinic"
---

# TASK-006: Clinic Settings + Tenant Onboarding Wizard

## Description

Module admin: tạo clinic mới, wizard onboarding 6 bước (chọn specialty → load preset, info clinic, tạo users, shift template, import inventory CSV optional, service catalog từ template). Settings JSONB per-clinic (operating_hours, appointment, queue, inventory, prescription, billing, specialty).

## Requirements

- [ ] Bảng `clinic_settings` (JSONB, key-value structure theo §15.2 BA)
- [ ] Endpoints admin: `POST /api/v1/admin/clinics`, `GET/PATCH /api/v1/admin/clinics/{id}`, `GET/PATCH /api/v1/clinics/me/settings`
- [ ] Onboarding wizard endpoints: `POST /api/v1/onboarding/start`, `POST /api/v1/onboarding/{step}` (specialty, info, users, shifts, inventory-csv, services)
- [ ] Specialty preset loader: clone `system_vital_preset` + service template → records của clinic mới
- [ ] CSV import inventory: validate, dry-run, commit
- [ ] Settings schema validation (Pydantic) cho từng nhóm key
- [ ] Default values cho mọi setting key (fallback nếu chưa set)

## Acceptance Criteria

- [ ] Tạo clinic mới + admin user + chọn specialty "general" → vital_field_definition của clinic có 6 fields (BP systolic, BP diastolic, pulse, temp, weight, height, SpO2)
- [ ] Tạo clinic specialty "pediatric" → có thêm `head_circumference`
- [ ] Update setting `appointment.slot_duration_minutes = 20` → mọi appointment endpoint dùng giá trị 20
- [ ] CSV import 1000 dòng inventory < 30s
- [ ] Onboarding step có thể skip + resume

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/app/modules/admin/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Onboarding chạy được offline (dùng Tauri client). Settings cache Redis 5 min để giảm DB load.

## Blockers

- TASK-004, TASK-005
