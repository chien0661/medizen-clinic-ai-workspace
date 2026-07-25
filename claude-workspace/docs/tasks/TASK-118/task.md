---
id: TASK-118
type: bug
title: "[Medium] UX: giá dịch vụ 0đ trong dropdown (M-13) + dashboard bác sĩ 403 spam (M-14) + card lịch hiện UUID (M-16)"
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-25
updated: 2026-07-25
branch: "fix/TASK-118-fe-ux-cluster"
tags: [frontend, ux, medium, e2e-finding]
affected-repos: [clinic-cms-web]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (M-13, M-14, M-16)"
    - "docs/tasks/TASK-118/handoff/implementation-to-review.md"
    - "docs/tasks/TASK-118/handoff/review-to-implementation.md"
    - "docs/tasks/TASK-118/handoff/review-report.md"
---

# TASK-118: [Medium] UX cluster FE (M-13 + M-14 + M-16)

**Nguồn:** E2E TASK-095, M-13/14/16 (FE-only → gộp 1 task).

## M-13 — Dropdown chọn dịch vụ hiển thị 0đ, giá thật chỉ hiện sau khi thêm
- Picker "Thêm dịch vụ" mọi dịch vụ = 0đ; sau khi thêm row hiện 200.000. Fix: hiện đơn giá thật trong danh sách tìm.
- File: doctor exam / services (CLS) picker.

## M-14 — Dashboard bác sĩ gọi endpoint không được phép → 403/400 mỗi lần load
- dr_nguyen: `/reports/revenue`→403 (cần report.financial) dù vẫn hiện card Doanh thu; `/shifts`→403; `/attendance/me`→400 (chưa gắn HR). Fix: chỉ gọi/hiện dữ liệu role truy cập được (ẩn card theo quyền).
- File: doctor dashboard page.

## M-16 — Card lịch hẹn hiện UUID cắt ngắn thay vì tên bệnh nhân
- Mọi card chỉ có UUID ('f7ff6af4...'); không tên. Fix: hiện tên (+ mã) bệnh nhân như queue board.
- File: appointments list/card.

## Acceptance Criteria
- [x] Dropdown dịch vụ hiện đơn giá thật.
- [x] Dashboard bác sĩ không gọi/hiện card ngoài quyền (không 403/400 spam).
- [x] Card lịch hẹn hiện tên bệnh nhân.
- [x] Unit test/UI cho các thay đổi; type-check/lint sạch.

## Progress Checklist
- [x] Implementation | [x] Review (APPROVED — M-14 shifts gated on `shift.manage` in 3c97a11) | [x] Testing | [x] Documentation

Documentation Completed: 2026-07-25
- Final spec: `docs/tasks/TASK-118/deliveries/final-specs/fe-ux-cluster-fix.md`

## Testing Completed (2026-07-25)
21/21 vitest passed (`ServicesTab.test.tsx`, `AttendanceWidget.test.tsx`,
`MainDashboardPage.test.tsx`, `AppointmentPage.test.tsx` — the 4 test files
touched by the fix commits) + clean `type-check` (`tsc --noEmit`, exit 0). No
Docker; ran directly in worktree `_fix118-web` (`node_modules` already newer
than lockfile, no `npm ci` needed). Confirmed: service price shown in picker
(not 0đ); shifts query (`hrApi.myShifts`) does NOT fire without
`shift.manage` and DOES fire with it; revenue KPI/chart hidden without
`report.financial`; appointment card shows patient name (+ code) with UUID
fallback. See `docs/tasks/TASK-118/deliveries/test-reports/test-report.md`.

## Blockers
Không. (FE-only.)
