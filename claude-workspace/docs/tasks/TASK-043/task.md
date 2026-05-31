---
id: TASK-043
type: audit
title: FE Stitch conformance audit — clinic-cms-web vs 63 màn HTML reference + E2E test
status: IN_PROGRESS
priority: High
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
branch: ""
jira_key: ""
tags: [audit, fe, conformance, stitch, ui, e2e]
affected-repos: [clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/2542650746708884228"
  confluence: ""
  jira_ticket: ""
  other:
    - "../TASK-032/handoff/fe-audit-report.md"
    - "../TASK-039/deliveries/final-specs/design-system-port-functional-design.md"
    - "../TASK-040/task.md"
    - "../../design/medizen-modern/html-export/index.html"
    - "../../design/medizen-modern/html-export/EXPORT_REPORT.md"
---

# TASK-043: FE Stitch conformance audit + E2E test

## Description

Sau khi 63 màn MediZen Modern UI đã được export thành HTML reference (`docs/design/medizen-modern/html-export/`), task này:

1. **Audit FE thực tế** (`clinic-cms-web` repo) so với 63 màn reference — sinh báo cáo gap per-màn
2. **Sau audit** chạy E2E test toàn hệ thống để verify slice 1 + Wave 1 + Wave 2 (đã DONE phần) không break

## Mục đích

- Identify tất cả màn FE còn thiếu / sai / partial so với MediZen Modern spec
- Categorize theo CRITICAL / MAJOR / MINOR
- Cross-reference với TASK-040 (Phase D screens) đã ship 7/8 màn để tránh trùng
- Output làm input cho follow-up sub-task (nếu cần)

## Requirements

### Phase 1 — FE conformance audit

- [ ] **A.1** Inventory: 63 màn reference (đã có `EXPORT_REPORT.md`)
- [ ] **A.2** Inventory: 47 spec màn theo MediZen Modern (TAB_MATRIX + MENU_AND_SCREENS)
- [ ] **A.3** Inventory: tất cả routes hiện có trong `src/router/index.tsx`
- [ ] **A.4** Match map: ref_html_file ↔ react_route ↔ spec_screen — table 3 chiều
- [ ] **A.5** Per-màn gap analysis:
  - CONFORM ✅: FE component matches reference layout + components + Indigo tokens
  - PARTIAL ⚠️: existed but differs (geometry, missing element, wrong copy)
  - MISSING ❌: route doesn't exist or PlaceholderPage stub
  - DUPLICATE-REF: 2+ HTML refs map to 1 FE component (e.g. variant tabs)
- [ ] **A.6** Visual conformance: token usage check (Indigo `#6366F1`, Plus Jakarta Sans, radii 12/8/6)
- [ ] **A.7** Vietnamese copy check: i18n keys vs reference HTML strings

### Phase 2 — E2E test

- [ ] **B.1** Bring up BE container (`clinic-cms-merge` worktree on `main` — has all 16 modules)
- [ ] **B.2** Apply latest migrations (alembic upgrade head)
- [ ] **B.3** Bring up FE dev server (use `feature/task-039-design-system` baseline + uncommitted Wave work optional)
- [ ] **B.4** Run Playwright smoke + regression suite
- [ ] **B.5** Visual smoke (login + 5-10 key pages)
- [ ] **B.6** Compare E2E result vs prior baseline (`docs/tasks/TASK-032/deliveries/test-reports/e2e-slice-final-2026-05-01.md`)

## Acceptance Criteria

- [ ] Báo cáo conformance đầy đủ trong `deliveries/final-specs/conformance-audit-report.md`
- [ ] Per-màn status (63 màn × 4 categories)
- [ ] CRITICAL màn missing được prioritized với recommend follow-up task
- [ ] E2E test report ở `deliveries/test-reports/e2e-2026-05-01.md`
- [ ] No new regressions vs baseline

## Related Files

- **Reference**: `docs/design/medizen-modern/html-export/screens/*.html` (63 files)
- **Index**: `docs/design/medizen-modern/html-export/index.html` (grouped browser)
- **FE source**: `../../clinic-cms-web/src/`
- **Output**: `deliveries/final-specs/conformance-audit-report.md` + `deliveries/test-reports/e2e-2026-05-01.md`

## Notes

- Audit là READ-ONLY — không edit FE code
- E2E phase reuses pattern từ TASK-032 final E2E (Docker + alembic + Playwright)
- Coordinate với TASK-040 Phase D screens (Wave 2-C đang chạy) — tránh duplicate findings
