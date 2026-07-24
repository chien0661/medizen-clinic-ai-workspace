# TASK-114 — Implementation → Review Handoff

**Repo:** clinic-cms-web (frontend)
**Worktree:** `F:/MyProject/clinic-cms-workspace/_fix114-web` (left in place for review)
**Branch:** `fix/TASK-114-visit-volume-columns` (base `origin/dev` @ `0dfb3eb`)
**Commit:** `c86fb4d` — pushed to `origin/fix/TASK-114-visit-volume-columns`
**PR compare:** https://github.com/chien0661/medizen-clinic-web/pull/new/fix/TASK-114-visit-volume-columns

## Root cause

- `VisitVolumePoint` / `getVisitVolume()` in `src/modules/reports/api.ts` already tracked
  `in_progress` (mapped from BE status `IN_PROGRESS`), but the on-screen table in
  `src/pages/reports/VisitVolumePage.tsx` never rendered a column for it — CSV had it
  (M-17), the screen didn't.
- The BE also emits an `AWAITING_PAYMENT` status row whose `count` was folded into
  `total` (`point.total += r.count` runs unconditionally) but the adapter's `switch`
  had no `case "AWAITING_PAYMENT"`, so that count wasn't captured in any field —
  `total` (21) ≠ Σ mapped columns (19) in both UI and CSV (M-18).

## Fix

- `src/modules/reports/types.ts`: added `awaiting_payment: number` to `VisitVolumePoint`.
- `src/modules/reports/api.ts` (`getVisitVolume`): initialize `awaiting_payment: 0` per
  period and added `case "AWAITING_PAYMENT": point.awaiting_payment = r.count; break;`.
  All 6 known BE statuses (`WAITING`, `IN_PROGRESS`, `AWAITING_PAYMENT`, `COMPLETED`,
  `CANCELLED`, `NO_SHOW`) now have a case → Σcolumns == total by construction.
- `src/pages/reports/VisitVolumePage.tsx`: added two table columns — "Đang khám"
  (`in_progress`) and "Chờ thanh toán" (`awaiting_payment`) — header + row cells.
- `src/modules/reports/helpers.ts` (`exportVisitVolumeCsv`): added "Chờ thanh toán"
  column so CSV also sums to Total.
- `src/locales/{vi,en}/reports.json`: added `visitVolume.awaitingPayment` key
  (`inProgress` key already existed, was just unused on screen before).
- Test data fixture in `src/tests/reports/helpers.test.ts` updated with the new
  `awaiting_payment` field (type now requires it).

Chart (Recharts lines/legend) was left as-is — out of scope per the bug report, which
is about the table columns and Total reconciliation, not the trend chart.

## Tests added

`src/tests/reports/visitVolumeApi.test.ts` (new) — 3 tests, mocks `api.get`:
1. Reproduces the exact E2E numbers (Total=21, Hoàn thành=3, Chờ khám=8, Đang khám=7,
   Đã hủy=1, Không đến=0, AWAITING_PAYMENT=2) and asserts Σcolumns == total.
2. Feeds one row per known BE status and asserts every one lands in a column
   (no status silently inflates `total` without a matching field).
3. Case-insensitivity check (`awaiting_payment` lowercase from BE still maps).

## Verification results (RAW)

- `npx vitest run src/tests/reports` → **7 test files, 31 tests passed** (3 new,
  28 pre-existing, none broken).
- `npm run type-check` → clean, no errors.
- `npm run lint` → **18 pre-existing problems (17 errors, 1 warning)**, all in files
  untouched by this change (`VitalsPage.tsx`, `VssIntegrationConfigPage.tsx`,
  `VssSyncLogPage.tsx`, `TemplateRenderer.tsx` — conditional-hooks and an unused
  eslint-disable directive, unrelated to reports). Confirmed via `git status --short`
  that none of the 8 changed/added files appear in the lint output — no new lint
  breakage introduced by this fix.

## Files changed

```
M src/locales/en/reports.json
M src/locales/vi/reports.json
M src/modules/reports/api.ts
M src/modules/reports/helpers.ts
M src/modules/reports/types.ts
M src/pages/reports/VisitVolumePage.tsx
M src/tests/reports/helpers.test.ts
?? src/tests/reports/visitVolumeApi.test.ts
```

## Next step

Code Review Agent: review diff on branch `fix/TASK-114-visit-volume-columns`
(worktree left at `_fix114-web`). No Docker/BE needed — FE-only, adapter-level fix
verified via mocked `api.get`.
