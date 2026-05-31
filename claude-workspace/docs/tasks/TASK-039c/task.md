---
id: TASK-039c
type: feature
title: MediZen logo SVG + favicon + Tauri icon — TASK-039 F.8/F.9 follow-up
status: IN_PROGRESS
priority: Low
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
branch: feature/task-039c-logo-favicon
jira_key: ""
tags: [fe, design-system, branding, asset, tauri]
affected-repos: [clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/MEDIZEN_FRESH_PROJECT.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/2542650746708884228"
  confluence: ""
  jira_ticket: ""
  other:
    - "../TASK-039/task.md"
    - "../TASK-039b/task.md"
---

# TASK-039c: MediZen logo + favicon + Tauri icon

## Description

TASK-039 F.8 (logo SVG) + F.9 (favicon + Tauri icon config) deferred to follow-up. This task implements them.

## Requirements

- [ ] **F.1** Design + create MediZen logo SVG (Indigo + medical cross + clean modern look). Replace `Shield` icon currently used in `Sidebar.tsx`/`Topbar.tsx`/`LoginPage.tsx`.
- [ ] **F.2** Create favicon.ico (multi-resolution: 16x16, 32x32, 48x48) for browser tab + bookmark
- [ ] **F.3** Create PNG icons for Tauri at multiple sizes (16, 32, 64, 128, 256, 512, 1024 px)
- [ ] **F.4** Update `src-tauri/tauri.conf.json` icon paths
- [ ] **F.5** Update `index.html` link rel=icon
- [ ] **F.6** Replace Shield icon usages with logo SVG component (LoginPage + Sidebar + Topbar)
- [ ] **F.7** Add logo to public/ directory + import path standardization

## Acceptance Criteria

- [ ] Logo SVG rendered correctly at all sizes (16x16 → 512x512)
- [ ] Browser tab shows MediZen favicon (test in Chrome/Firefox)
- [ ] Tauri app icon updated (build + verify)
- [ ] No Shield icon imports remaining in Sidebar/Topbar/LoginPage
- [ ] FE tests pass; 0 TS; 0 lint; build PASS

## Dependencies

- Blocked by: TASK-039 ✅ (design tokens for color choice)
- Coordinates: TASK-039b (component primitives — no overlap)

## Effort

**Small** (1d). Asset creation + path update.

## Risk

LOW (asset replacement only).
