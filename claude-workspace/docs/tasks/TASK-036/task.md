---
id: TASK-036
type: feature
title: Cmd+K Quick Search (NAV-001..008) — BE search API + FE palette + breadcrumb + global shortcuts
status: DONE
priority: Medium
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
completed: 2026-05-01
branch: feature/task-036-cmdk-search
jira_key: ""
tags: [search, ux, command-palette, keyboard, nav]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/MENU_AND_SCREENS.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/2542650746708884228"
  confluence: ""
  jira_ticket: ""
  other:
    - "../../../docs/clinic_management_function_list.md"
    - "../TASK-032/deliveries/final-specs/audit-report.md"
---

# TASK-036: Cmd+K Quick Search + global shortcuts

## Description

Build cross-entity command palette opened by `Cmd+K`/`Ctrl+K`: search BN / Thuốc / Inv / Rx / LK with sub-mode prefixes, fuzzy + unaccent matching, permission-aware union, recent items, keyboard nav. Add breadcrumb component (NAV-008) and shortcut cheatsheet (NAV-007).

## Requirements

### BE (clinic-cms)

- [x] **B.1** Migration: enable `pg_trgm` + `unaccent` Postgres extensions
- [x] **B.2** Indexes: trigram on `patient.full_name`, `patient.phone`, `patient.id_number`, `medicine.name`, `medicine.active_ingredient`
- [x] **B.3** New `app/modules/search/` module with permission-aware multi-table query
- [x] **B.4** Endpoint `GET /api/v1/search?q=X&mode=bn|thuoc|inv|rx|lk&limit=20` returns union with type tag + score
- [x] **B.5** Permission filter: only return entities user has read perm for
- [x] **B.6** Typo-tolerance via trigram similarity ≥0.3 + unaccent
- [x] **B.7** Recency boost (recent edits + recent visits weighted higher)

### FE (clinic-cms-web)

- [x] **F.1** New `components/shell/CommandPalette.tsx` — modal overlay, search input, result groups by type
- [x] **F.2** New `hooks/useGlobalShortcuts.ts` — Cmd/Ctrl+K opens palette, ? opens shortcut cheatsheet, Esc closes
- [x] **F.3** Sub-mode prefix parsing: `/bn`, `/thuoc`, `/inv`, `/rx`, `/lk` → set search mode
- [x] **F.4** Result group rendering: BN (avatar + name + age), Thuốc (name + stock chip), Tính năng (route + breadcrumb)
- [x] **F.5** Keyboard navigation: ↑/↓ select, Enter open, Tab switch group
- [x] **F.6** Recent items: persist last 10 selections in Tauri secureStore `RECENT_SEARCH_ITEMS`
- [x] **F.7** New `components/shell/Breadcrumb.tsx` — auto-generated from route definitions (NAV-008)
- [x] **F.8** New `components/shell/ShortcutCheatsheet.tsx` — modal listing shortcuts (NAV-007)
- [x] **F.9** Mount `CommandPalette` + `useGlobalShortcuts` provider at `AppShell.tsx` level
- [x] **F.10** New `modules/search/api.ts` — search query hook with React-Query
- [x] **F.11** i18n: `commandPalette.*` namespace

## Acceptance Criteria

- [x] `Cmd+K` opens palette globally; `Esc` closes
- [x] Search "ngu" matches "Nguyễn" (unaccent + trigram)
- [x] Sub-mode `/bn` filters to patients only; `/thuoc` to medicines
- [x] User without `medicine.read` perm: search results don't include medicines
- [x] Recent items persist across sessions
- [x] Breadcrumb shows on every non-dashboard route
- [x] `?` opens shortcut cheatsheet
- [x] BE search latency p95 <300ms with 10K patients + 5K medicines fixture
- [x] FE + BE tests pass (646/646 FE, 22 BE)

## Dependencies

- Blocked by: TASK-041 (medicine + inventory modules must exist for `/thuoc /inv` modes), TASK-033 (multi-clinic perm scoping), TASK-039 (palette visual)
- Blocks: none

## Effort

**Medium** (2 days).

## Risk

LOW (read-only search; trigram extensions are well-tested in Postgres).

## Notes

- Discovery via TASK-032 BE audit B.4 + FE audit A.6.
- Consider `cmdk` library for FE (used by Vercel, Linear) vs roll-own.

---

## Completion Notes (2026-05-01)

**Status**: DONE — all acceptance criteria met, tests passing.

**Test Verification**:
- FE: 646/646 tests pass (67 task-specific)
- TypeScript: clean (tsc --noEmit)
- ESLint: clean
- BE: 22 tests (15 unit + 7 integration)

**Fixes Applied** (fix-mode, 2026-05-01):
1. Breadcrumb Link: replaced raw `<a href>` with React Router `<Link>` (SPA nav)
2. Rate limit: added `@limiter.limit("30/minute")` on `/api/v1/search`
3. Exception handling: replaced bare `except Exception` with scoped `(SQLAlchemyError, AttributeError)` + logging
4. ShortcutCheatsheet: added 11 render + closure tests

**Critical Dependencies & Deferred Items**:
- ⚠️ **Migration chain conflict**: 0027 (TASK-036) + 0025 (TASK-037 P2) both target 0021 → requires orchestrator rebase
- ⚠️ **Trigram vs encryption**: 3 GIN indexes on patient columns will become invalid post-TASK-037 merge. Strategy (b) HMAC side columns deferred to TASK-037 coordination
- ✓ **Delivery**: See [Functional Design](deliveries/final-specs/cmd-k-search-functional-design.md)
