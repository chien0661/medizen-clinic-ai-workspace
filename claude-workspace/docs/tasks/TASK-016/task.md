---
id: TASK-016
type: feature
title: Tauri Foundation — Shell + Offline Sync Engine + Hardware Integration
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-04-26
updated: 2026-04-27
testing_completed: 2026-04-27
documentation_completed: 2026-04-27
branch: "feature/TASK-016-tauri-foundation"
tags: [tauri, frontend, offline, hardware, sprint-15, foundation]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#20-offline-sync"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#16-offline-strategy-tauri-client"
---

# TASK-016: Tauri Foundation — Shell + Offline Sync Engine + Hardware Integration

## Description

**FE platform foundation only** — Tauri 2.x (Rust + React) shell, local SQLite cache + sync engine (push/pull/conflict resolution), UUIDv7 client-side, optimistic lock qua `version`, Tauri plugin: secure storage (JWT), POS printer (ESC/POS), barcode scanner (HID).

UI per-module được tách thành các task riêng:
- TASK-017: Auth + App Shell + Design System + i18n
- TASK-018: Reception (Patient + Walk-in + Appointment + Queue)
- TASK-019: Doctor (Visit + Vitals + Service + Prescription)
- TASK-020: Pharmacy (Dispense + Inventory)
- TASK-021: Billing (Invoice + Payment + POS Print)
- TASK-022: HR (Schedule + Attendance + Leave)
- TASK-023: Admin (Users + Roles + Settings + Onboarding)
- TASK-024: Dashboard + Reports + Notifications

## Requirements

- [ ] Tauri shell + React (Vite) trong `clinic-cms-web/` (parallel folder, NOT clinic-cms/desktop/)
- [ ] Local SQLite schema mirror các bảng cần offline (theo §16.1 BA — Patient, Visit, Vitals, Appointment, VisitService, Prescription, TimeLog)
- [ ] Mỗi table local có cols: `sync_status` (synced/pending_create/pending_update/pending_delete), `sync_attempted_at`, `sync_error`, `server_version`
- [ ] Sync engine (Rust hoặc TS):
  - Push: gửi pending changes batch 50 lên server (POST/PATCH/DELETE)
  - Pull: `GET /api/v1/sync/changes?since=<iso>` apply local
  - Conflict 409: last-write-wins cho non-critical, manual resolve cho critical (Prescription/Invoice)
  - UUIDv7 client-side (avoid ID collision)
- [ ] Server endpoint `GET /api/v1/sync/changes` trả changes per entity since timestamp
- [ ] Hardware integration via Tauri plugin:
  - POS printer ESC/POS — in invoice + prescription + label thuốc
  - Barcode scanner (HID input) — scan medicine code, patient code
- [ ] **Sample minimal screen** validate foundation works end-to-end (chỉ /health check + login dummy + trang trống "Hello clinic-cms")
- [ ] Offline indicator UI primitive (icon trạng thái online/offline + pending sync count) — reusable component
- [ ] Hot reload Tauri dev mode + production build pipeline

## Acceptance Criteria

- [ ] Tauri dev mode: `pnpm tauri dev` start app + connect tới API local
- [ ] Local SQLite mirror schema cho 7 entity offline (patient/visit/vitals/appointment/visit_service/prescription/time_log) tạo được
- [ ] Sync engine demo: tạo dummy entity offline → online → sync push thành công, server nhận đúng
- [ ] Conflict version 409: trigger từ test → modal generic xuất hiện với 3 button (keep_local/take_server/merge)
- [ ] Tauri plugin POS printer: print 1 dòng test "HELLO CLINIC" qua ESC/POS thành công (test với printer thật hoặc emulator)
- [ ] Tauri plugin barcode scanner: HID input → callback nhận string đúng
- [ ] Build Tauri: Windows `.msi` + macOS `.dmg` + Linux `.AppImage` đều OK trong CI
- [ ] Foundation đủ để TASK-017..024 build trên (verified bằng smoke implement Login screen với foundation primitives)

## Progress Checklist

- [x] Implementation
- [x] Code Review (iteration 1: CHANGES_REQUESTED → iteration 2: APPROVED)
- [x] Testing (73/73 tests pass — 2026-04-27)
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms-web/` (Tauri app — separate repo parallel to clinic-cms/ BE)
- **Reference UI**: `E:\MyProject\clinic-cms-workspace\docs\clinic_cms_mockup.html`

## Timestamps

- **Created**: 2026-04-26
- **Implementation Completed (iteration 2 / FIX MODE)**: 2026-04-27

## Notes

Inventory deduction (reserve/dispense) yêu cầu online — không offline được vì sẽ gây oversell. Foundation phải expose `useOnlineStatus()` hook để TASK-020 (Pharmacy) block UI khi offline.

Phase sau: BluetoothLE blood pressure monitor, CCCD reader.

## Blockers

- TASK-001 (backend foundation đã chạy cần API contract stable cho sync endpoint TASK-015)
