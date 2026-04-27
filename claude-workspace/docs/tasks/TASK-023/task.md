---
id: TASK-023
type: feature
title: FE — Admin (Users + Roles + Clinic Settings + Vital Schema Editor + Onboarding Wizard)
status: TODO
priority: Medium
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [frontend, admin, settings, onboarding, sprint-16]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#5-module-tenancy--audit"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#13-module-auth--rbac"
    - "../../../../docs/clinic_management_business_analysis.md#1513-tenant-onboarding-flow"
    - "../../../../docs/clinic_management_business_analysis.md#152-settings-per-clinic"
---

# TASK-023: FE — Admin Module (Users + Roles + Settings + Onboarding Wizard)

## Description

UI cho admin: quản lý user của clinic, role + permission matrix editor, clinic settings forms theo nhóm (general/operating_hours/appointment/queue/inventory/prescription/billing), vital schema editor (manage VitalFieldDefinition), service catalog editor, 6-step onboarding wizard cho clinic mới.

## Requirements

- [ ] **User management** (`/admin/users`)
  - List: username, full_name, email, roles (chip), is_active, last_login_at
  - Action: create | edit | reset password | lock/unlock | assign roles
  - Filter by role, status
  - Bulk action: deactivate selected
- [ ] **Role & Permission matrix** (`/admin/roles`)
  - Left: list roles (Admin/Doctor/Nurse/Pharmacist/Receptionist + custom)
  - Right: matrix permission × roles checkbox grid
  - Highlighted: system roles (không xóa được)
  - User extra permissions (`/admin/users/:id/extra-permissions`): grant/deny override
- [ ] **Clinic settings form** (`/admin/settings`)
  - Tabs theo nhóm:
    1. **General** — name, address, phone, email, tax_code, logo upload
    2. **Operating hours** — table 7 ngày: open/close time
    3. **Appointment** — slot_duration, buffer, no_show, advance_booking_days
    4. **Queue** — require_vitals_before_consultation toggle
    5. **Inventory** — near_expiry_days, low_stock_alert toggle
    6. **Prescription** — print_mode (all/external_only/ask)
    7. **Billing** — discount_threshold_require_reason
  - Save → API PATCH `/clinics/me/settings`
- [ ] **Vital schema editor** (`/admin/vitals`)
  - Table fields: key, label, data_type, unit, min/max, warning_min/max, is_required, is_active, sort_order
  - Add field form (key validation: snake_case, unique)
  - Edit field: label/unit/range OK; key/data_type DISABLED (theo §7.3 BA evolution rules)
  - Disable field (soft hide): `is_active=false`, dữ liệu cũ vẫn xem
  - Reorder via drag handle (sort_order)
  - "Reset to specialty preset" (cảnh báo: ghi đè custom)
  - Version history viewer (xem snapshot từng version)
- [ ] **Service catalog editor** (`/admin/services`)
  - CRUD: code, name, category, default_price, duration_minutes, sort_order, is_active
  - Bulk import CSV
- [ ] **Medicine catalog editor** (`/admin/medicines`)
  - CRUD medicine clinic-level (system-level read-only)
  - Bulk import CSV
- [ ] **Audit log viewer** (`/admin/audit`)
  - Filter: entity_type, entity_id, user, action, date range
  - Detail drawer: old_data / new_data diff (JSON viewer)
- [ ] **Onboarding wizard** (`/onboarding`, hiện khi clinic mới + admin lần đầu login)
  - Step 1: Specialty (general/dental/pediatric/obstetric/dermatology) → preview vitals + service preset
  - Step 2: Clinic info (name, address, phone, hours)
  - Step 3: Tạo users (bác sĩ, y tá, lễ tân, dược sĩ) — multi-row
  - Step 4: Shift template (ca sáng, ca chiều)
  - Step 5: Inventory CSV upload (optional, có template download)
  - Step 6: Service catalog (từ template hoặc tự nhập)
  - "Skip & resume later" available
  - Progress indicator + back/next

## Acceptance Criteria

- [ ] Tạo user mới với role Doctor + extra_grant `invoice.void` → user login thấy được button Void invoice
- [ ] Sửa permission matrix uncheck `prescription.write` cho Doctor → save → user Doctor reload thấy menu Prescription disabled
- [ ] Edit clinic settings appointment.slot_duration = 20 → calendar booking ở TASK-018 reflect đúng
- [ ] Vital editor: rename label "Huyết áp tâm thu" giữ key=systolic_bp → save → tạo version mới, dữ liệu cũ vẫn xem được label cũ
- [ ] Vital editor: thử rename key → field disabled với message "Tạo field mới thay vì rename"
- [ ] Onboarding clinic mới specialty=pediatric → vital_field_definition seed sẵn 5 fields chuẩn
- [ ] Audit log filter "patient.update" trong tuần → list đúng records
- [ ] CSV inventory 1000 rows import < 30s, hiện progress bar

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/desktop/src/modules/admin/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Onboarding wizard nên save state mỗi step → user đóng app vẫn resume được. Logo upload: lưu vào S3 hoặc local Tauri filesystem.

## Blockers

- TASK-017, TASK-004 (RBAC API), TASK-006 (Settings/Onboarding API), TASK-009 (Vitals API)
