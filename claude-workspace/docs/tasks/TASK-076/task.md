---
id: TASK-076
type: feature
title: Configurable dosage-form (dạng bào chế) master-data category + dynamic medicine dropdown
status: DONE
priority: High
assigned: None
created: 2026-06-02
updated: 2026-06-02
branch: "feature/TASK-076-dosage-form-category (FE + BE)"
jira_key: ""
tags: [frontend, backend, master-data, inventory, medicines, e2e]
affected-repos: [clinic-cms-web, clinic-cms]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-076: Danh mục "Dạng bào chế" cấu hình động + E2E

## Description

Biến `medicine.dosage_form` từ **enum cứng** (8 giá trị trong code) thành **danh mục master-data quản lý được (CRUD)**: màn admin riêng để thêm/sửa/xóa dạng bào chế; dropdown ở form thuốc lấy options từ danh mục này. Kèm E2E test trên local dev.

## Design

- `medicine.dosage_form` giữ String (lưu `code`) — không FK, tránh migration dữ liệu thuốc.
- Bảng `dosage_form` có `clinic_id` NULLABLE: 8 default hệ thống (`clinic_id=NULL`, `is_system=true`) hiển thị cho mọi clinic qua RLS (`apply_rls_with_tenant_isolation` cho phép NULL); clinic tự thêm dạng riêng. Không sửa/xóa được row hệ thống (403).
- Nhãn dropdown lấy từ `name` (DB), value = `code`.
- Permission: `dosage_form.read` (admin/doctor/nurse/pharmacist/receptionist), `dosage_form.manage` (admin).

## Acceptance Criteria

- [x] Màn `/admin/dosage-forms` CRUD; 8 default hệ thống read-only; dạng tùy chỉnh có sửa/xóa
- [x] Dropdown dạng bào chế ở form thuốc lấy từ danh mục (label=name, value=code)
- [x] Không sửa/xóa được dạng hệ thống (BE 403)
- [x] Tenant isolation + permission đúng
- [x] E2E local pass

## Progress Checklist

- [x] Implementation (BE + FE)
- [x] Code Review (self-review; mirror vital-definitions pattern)
- [x] Testing (unit + API E2E + browser E2E)
- [x] Documentation

## Result Summary

- BE `feature/TASK-076-dosage-form-category`: `405ebfd` — model/schema/service/routes + migration `0038_create_dosage_form` (table + RLS + perms + 8 seed).
- FE `feature/TASK-076-dosage-form-category`: `79f7183` — DosageFormsPage CRUD, adminDosageFormsApi, dynamic medicine dropdown, sidebar nav + route, vi/en i18n, tests.
- Verify: BE pyflakes/ast clean; FE `tsc` clean; DosageFormsPage 12/12, MedicinesPage.tags 4/4, admin 42/42.
- **E2E (docker py3.11 + FE :1420 + Playwright)**: migration applied (8 seeds verified in DB); API E2E list8→create201→list9→patch200→delete-system-403→delete-custom-204→list8; browser E2E login→create "Gel bôi ngoài da" via UI→appears as custom row w/ edit/delete→medicine dropdown includes it. See `deliveries/test-reports/test-report.md`.

## Timestamps

- **Created**: 2026-06-02
- **Implementation Completed**: 2026-06-02
- **Testing Completed**: 2026-06-02
- **Documentation Completed**: 2026-06-02

## Notes

- Demo data dùng vài code dạng bào chế ngoài 8 default (effervescent, eye_drop, infusion, ointment, powder, solution) → bảng thuốc hiển thị fallback theo code; muốn map đẹp thì bổ sung các dạng này vào danh mục.
- BE local cần Python 3.11 → E2E chạy qua docker-compose (`docker/`). Lưu ý: `docker/docker-start.sh` có lỗi cú pháp line 49 (pre-existing) — đã bypass bằng cách chạy uvicorn trực tiếp; nên báo team sửa.

## Blockers

None
