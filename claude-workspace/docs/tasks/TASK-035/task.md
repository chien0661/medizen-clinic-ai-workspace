---
id: TASK-035
type: feature
title: Multi-role merge sidebar UX (RBAC-015..018) + applied_role audit + SoD framework
status: DONE
priority: High
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
completed: 2026-05-01
branch: feature/task-035-multi-role
jira_key: ""
tags: [rbac, ux, sidebar, audit, separation-of-duties]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/MULTI_ROLE_UX.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/2542650746708884228"
  confluence: ""
  jira_ticket: ""
  other:
    - "../TASK-032/deliveries/final-specs/audit-report.md"
    - "../TASK-032/handoff/fe-audit-report.md"
    - "../TASK-032/handoff/be-audit-report.md"
---

# TASK-035: Multi-role merge sidebar UX + applied_role audit + SoD

## Description

User kiêm nhiều roles (e.g. Bác sĩ + Quản trị) thấy 1 sidebar merge với section dividers per role (không có role switcher). Audit log phải ghi `applied_role` để biết action thực hiện dưới role nào (RBAC-015). Thêm Separation-of-Duties framework (RBAC-016) — e.g. user không thể vừa propose vừa approve cùng record.

## Requirements

### BE (clinic-cms)

- [x] **B.1** Migration: add `audit_log.applied_role VARCHAR(50) NULL`
- [x] **B.2** Update audit listener `app/core/audit.py` to capture `applied_role` from JWT claim or request context
- [x] **B.3** New `app/core/sod.py` — `check_no_self_approval(record_creator_field='created_by')` + `make_sod_dep()` dependency factory
- [x] **B.4** Update `/users/{id}/roles` listing schema to include `assigned_at` per role (RBAC-018)
- [x] **B.5** RBAC-016 SoD applied to: invoice payment approval, prescription dispense approval

### FE (clinic-cms-web)

- [x] **F.1** Refactor `Sidebar.tsx`: group nav items by role-membership, render dividers `─── Bác sĩ ───`, `─── Quản trị ───`
- [x] **F.2** New `lib/rbac.ts` — role-to-nav-section mapping (which nav items belong to which role)
- [x] **F.3** Update `authStore` to expose `roles[]` + `applied_role` state (sticky per session, default = first role)
- [x] **F.4** Topbar avatar: show role chip — primary role + "+N" if multi
- [x] **F.5** Sidebar section context: visual dot indicator on active role section; nav click sets `applied_role`
- [x] **F.6** Send `applied_role` as `X-Applied-Role` request header on every authenticated request
- [x] **F.7** Default landing for multi-role user = `/dashboard/multi-role` route with redirect from LoginPage

## Acceptance Criteria

- [x] User with 1 role: sidebar identical to current (no dividers)
- [x] User with 2+ roles: sidebar shows section dividers; nav items grouped per role
- [x] Avatar role chip displays primary role + "+N" badge if multi
- [x] Audit log entries include `applied_role` field for multi-role users
- [x] SoD: same user cannot create + approve same invoice/prescription (test verifies 403)
- [x] BE: 14 tests pass (8 SoD unit + 3 audit unit + 3 SoD integration violations)
- [x] FE: 592 tests pass (TS clean, lint clean); sidebar grouping + topbar role chip + applied_role context tests

## Dependencies

- Blocked by: TASK-033 (audit + JWT need multi-clinic-aware role context), TASK-039 (sidebar visual treatment uses Indigo tokens)
- Blocks: none

## Effort

**Small-Medium** (1-1.5 days).

## Risk

LOW. Additive column on audit; sidebar refactor is local.

## Notes

- Discovery via TASK-032 BE audit B.5 + FE audit A.4.
- BE union-permissions logic already correct (`rbac_service.get_user_effective_permissions`) — only `applied_role` provenance + SoD missing.
- See `docs/design/medizen-modern/MULTI_ROLE_UX.md`.

---

## Completion Notes (2026-05-01)

**Status**: ✅ DONE — all requirements + acceptance criteria met.

**Test Results**:
- BE: 14 tests pass (8 SoD unit + 3 audit unit + 3 SoD integration)
- FE: 592 tests pass (TS clean, lint clean)

**Implementation**:
- F.5/F.6/F.7 applied_role context wired post-fix (authStore + Tauri secureStore + X-Applied-Role header + /dashboard/multi-role route)
- 2/3 SoD endpoints applied (invoice payment + pharmacy dispense; stocktake deferred — endpoint not yet exists)
- Sidebar multi-role grouping + topbar role chip fully functional
- i18n complete (vi + en role labels)

**Cross-task coordination**:
- TASK-037 (hash chain): applied_role hash inclusion tracked as Wave 3-B merge follow-up
- TASK-040 (pharmacy): no ROLE_NAV_SECTIONS conflicts
- TASK-044 (4 dashboards): orchestrator adds routes at merge
- TASK-033/036: Topbar layout coexistence verified

**Deliverable**: `docs/tasks/TASK-035/deliveries/final-specs/multi-role-functional-design.md`

Ready for production merge (subject to Wave 2-A hash-chain follow-up).
