---
id: TASK-114
type: bug
title: "[Medium] Report Visit-volume: thiếu cột 'Đang khám' + Total tính cả AWAITING_PAYMENT không map cột"
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-25
updated: 2026-07-25
branch: "fix/TASK-114-visit-volume-columns"
tags: [reports, frontend, data-integrity, medium, e2e-finding]
affected-repos: [clinic-cms-web]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (M-17, M-18)"
---

# TASK-114: [Medium] Visit-volume report cột/tổng không khớp (M-17 + M-18)

**Nguồn:** E2E TASK-095, M-17 + M-18 (cùng màn/adapter → gộp). FE only.

## M-17 — Bảng trên màn thiếu cột "Đang khám" (IN_PROGRESS) → tổng không khớp
- Total=21 nhưng chỉ 4 cột (Hoàn thành 3 + Chờ khám 8 + Đã hủy 1 + Không đến 0 = 12); cột "Đang khám"(7) không có trên màn (CSV có). Người dùng thấy 21 nhưng chỉ giải thích 12.
- File: `src/pages/reports/VisitVolumePage.tsx`, `src/modules/reports/api.ts`.

## M-18 — Total tính cả AWAITING_PAYMENT nhưng không map cột nào (kể cả CSV)
- Total=21 nhưng cột CSV (8+7+3+1+0=19) thiếu 2 = AWAITING_PAYMENT. Switch adapter không có case AWAITING_PAYMENT nhưng vẫn `total += count`.
- File: `src/modules/reports/api.ts` (`getVisitVolume`).

## Acceptance Criteria
- [x] Bảng trên màn có đủ cột status (gồm "Đang khám" IN_PROGRESS + AWAITING_PAYMENT) → tổng các cột == Total, cả UI lẫn CSV.
- [x] Unit test adapter: mọi status có case + tổng khớp.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Documentation Completed
Documentation Completed: 2026-07-25 — Final specs in `docs/tasks/TASK-114/deliveries/final-specs/visit-volume-columns-fix.md`

## Testing — 2026-07-25 (PASSED -> DOCUMENTING)
31/31 vitest tests passed (`src/tests/reports`) + clean type-check, in
worktree `_fix114-web` (no Docker). Sigma(columns)==Total confirmed with the
exact E2E repro numbers (Total=21 incl. IN_PROGRESS=7 + AWAITING_PAYMENT=2);
adapter covers all 6 known statuses. See `handoff/test-to-documentation.md`
and `deliveries/test-reports/test-report.md`.

## Blockers
Không. (FE-only, không cần Docker cho unit test.)

## Implementation Summary (2026-07-25)
Branch `fix/TASK-114-visit-volume-columns` (base `origin/dev` @ `0dfb3eb`), pushed. Commit `c86fb4d`.
See `docs/tasks/TASK-114/handoff/implementation-to-review.md` for details.
