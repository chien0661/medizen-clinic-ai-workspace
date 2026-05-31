# TASK-044 — Handoff: Review → Test

**Date**: 2026-05-01
**Reviewer**: Code Review Agent
**Branch**: `feature/task-044-role-dashboards` (worktree `clinic-cms-web-w4a`)
**Decision**: **APPROVED with NOTES** (proceed to test, follow-ups tracked separately)

---

## Verification Run (independent)

| Check | Result |
|---|---|
| `npm test -- --run` | PASS (572/572, 55 files) |
| `npm run type-check` | PASS (0 errors) |
| `npm run lint` | PASS (0 warnings) |

---

## Checklist Results

### A. Per-dashboard structure ✅

- **Reception** ✅ — 4 KPI cards (`kpi-waiting`, `kpi-registered-today`, `kpi-walkin-vs-appt`, `kpi-upcoming-appointments`), queue mini-board (top 5), today's appointments table, `btn-new-walkin` quick action.
- **Nurse** ✅ — 3 KPI cards, sticky alert panel (red border, allergy/abnormal vitals), Recharts BarChart for departments, vitals history table.
- **Pharmacy** ✅ — 4 KPI cards, low-stock BarChart, pending prescriptions table (urgent/normal priority), `btn-inventory` + `btn-handle-expiry` quick actions, low-stock alert banner.
- **Admin** ✅ — 6 KPI cards (revenue today/week/month + new/return patients + pending invoices), revenue 30d LineChart, dept PieChart, activity feed, feature flags panel.

Spec called for **4** Admin KPIs — implementation delivers **6** (richer, no concern).

### B. Recharts theming ✅

- Bar charts use `#6366f1` (Nurse dept) and `#f59e0b` (Pharmacy stock) — matches spec.
- Line chart (Admin revenue) uses `#6366f1` indigo-500 stroke — ✅.
- Pie chart palette: indigo / emerald / amber / red / violet / slate — semantic + matches Indigo/Emerald/Amber/Red palette.
- CartesianGrid uses `#e2e8f0` (slate-200) — Slate palette ✅.
- Tooltip default styling (no custom override). ⚠️ Minor — could add Slate background for full theming consistency, not blocker.

### C. Mock data quality ✅

- Vietnamese realistic: BN names (Nguyễn Thị Hương, Trần Văn Minh, Lê Thị Mai…), medication names (Paracetamol, Amoxicillin, Omeprazole, Metformin, Atorvastatin), staff names with role prefix (BS./ĐD./Dược sĩ).
- Placeholder pattern: `useQuery({ queryFn: async () => MOCK_X, placeholderData: MOCK_X })` — easy to swap with real API by replacing `queryFn`.
- Empty state ✅ for queue, appointments, vitals, pending Rx, activity feed (each renders `t("…empty")` text).
- Loading state ⚠️ — relies on `placeholderData` so dashboards render immediately; no skeleton/spinner state. Acceptable for MVP+ but consider skeleton in follow-up.

### D. Permission guards ⚠️ (NOTE — coordination needed)

- 4 routes correctly wrapped in `<RequirePermission>` with `fallback={common:forbidden}`.
- `RequirePermission` component logic verified — checks `user.permissions.includes(perm)`.
- ❌ **Permission strings do NOT exist in BE seed** (`alembic/versions/0007_seed_permissions_and_roles.py`) — `reception.dashboard.view`, `nurse.dashboard.view`, `pharmacy.dashboard.view`, `admin.dashboard.view` are all NEW perms not yet seeded.
- ⚠️ **Convention mismatch**: existing perms use 2-level dotted form (`pharmacy.view`, `admin.access`, `visit.read`, `shift.manage`) — new perms use 3-level (`<role>.dashboard.view`). Either is fine, but BE seed must be updated to add these (or perm strings must be aligned with existing 2-level convention, e.g., `dashboard.reception.view`).
- ✅ FE-side gate works correctly; will silently render `forbidden` until BE seed updated.

### E. i18n vi/en ✅

- Namespace `dashboards` (plural) registered in `src/lib/i18n.ts` alongside existing `dashboard` (singular, TASK-024). Coexistence is OK — naming is slightly confusing but no collision.
- Vietnamese natural and clinically appropriate (BN, ĐK, BS., ĐD., Sàng lọc, Sinh hiệu, Tồn kho, BHYT, Đa vai trò).
- en/vi key parity ✅ — same structure 4 sub-namespaces, ~80 keys each.
- Translation keys match component usage ✅ (spot-checked all 4 pages).

### F. Multi-role landing coordination ✅

- LoginPage redirect logic NOT modified by TASK-044 (verified line 169–176 unchanged) — sends to `/dashboard` (singular, MainDashboardPage). ✅ per scope.
- `/dashboards/multi-role` route NOT added — deferred to TASK-035 Wave 3-B per handoff §5.
- 4 new routes do NOT collide with existing `/dashboard` (singular) — different paths.

### G. Test quality ✅

- 25 tests / 5 files (5 + 5 + 5 + 6 + 4):
  - Render assertions ✅
  - KPI testid assertions ✅ (4/3/4/6 cards verified individually)
  - Empty state ⚠️ — shallow (Reception "empty queue" test asserts container present but doesn't actually empty data; placeholderData always shows MOCK). Acceptable — placeholderData design decision means empty branch is hard to exercise without overriding `useQuery` directly.
  - route-guard.test.tsx ✅ — 4 tests confirm `RequirePermission` shows `common:forbidden` when permission missing.
- Mocks isolated per file (no shared state) ✅.

### H. Cross-cutting ✅ / ⚠️

- TASK-040 routes: `/dashboards/multi-role` placeholder vs TASK-044 4 new routes — no collision (different paths) ✅.
- TASK-035 Sidebar grouping: TASK-044 did NOT add nav items in `Sidebar.tsx` — pages reachable only via direct URL. ⚠️ **Merge-time follow-up**: Wave 3-B `ROLE_NAV_SECTIONS` must add 4 dashboard entries per role. Document this in test report so doc agent flags it.
- TASK-039 design tokens ✅ — `tailwind.config.js` confirms Indigo `#6366f1` + Plus Jakarta Sans; pages use `bg-indigo-500`, `text-indigo-600`, `bg-emerald-100`, etc.

### I. Performance + accessibility ⚠️

- Recharts re-render: no `React.memo` on KpiCard or chart sections. Charts re-render on every parent render. ⚠️ Minor — dashboards are not heavy lists, refetchInterval 30–60s. Optimize in follow-up if needed.
- ARIA labels: ❌ no `aria-label` / `role` attributes on KPI cards, chart titles, or quick action buttons. Existing MainDashboardPage (TASK-024) also lacks them — TASK-044 is **consistent** with existing baseline. **Defer to dedicated A11y task.**
- Keyboard nav: `<button>` elements used for actions ✅ — natively keyboard-accessible. Pharmacy `kpi-low-stock` has `onClick` on a `<div>` ⚠️ — not keyboard-accessible. Should be `<button>` or have `role="button" tabIndex={0}` + keydown handler. **Minor finding.**

### J. Deferred decisions ✅ (handoff documents clearly)

Handoff §"Decisions Deferred" lists 6 items honestly: BE adapter layer, nurse vitals endpoint, dispense-history endpoint, feature flag endpoint, multi-role route, walk-in route. All flagged with proper context. ✅

---

## Summary of Findings

| # | Severity | Finding | Action |
|---|---|---|---|
| F1 | ⚠️ MEDIUM | 4 new permission strings (`<role>.dashboard.view`) not in BE seed | **Follow-up task**: BE seed migration to add 4 perms; verify naming convention with team (3-level vs existing 2-level) |
| F2 | ⚠️ LOW | TASK-035 Sidebar `ROLE_NAV_SECTIONS` doesn't list new dashboards | **Merge-time coord**: Wave 3-B must add nav entries when merging |
| F3 | ⚠️ LOW | Pharmacy `kpi-low-stock` `<div>` with `onClick` — not keyboard accessible | Convert to `<button>` or add `role/tabIndex/onKeyDown` |
| F4 | ℹ️ INFO | No ARIA labels on KPI cards / chart titles | Consistent w/ MainDashboardPage; defer to A11y task |
| F5 | ℹ️ INFO | No skeleton/loading state — relies on `placeholderData` only | Acceptable for MVP+; optional polish |
| F6 | ℹ️ INFO | KpiCard duplicated locally in each of 4 pages | Consider extracting to `components/dashboard/KpiCard.tsx` (mirrors MainDashboardPage pattern — duplication is intentional but DRY opportunity) |

**No BLOCKING issues.** All quality gates pass. Mock data and i18n are production-ready. Deferred items honestly documented.

---

## Decision

**APPROVED — proceed to Test phase.**

Test agent should:
1. Verify 4 dashboards render in browser (manual smoke).
2. Verify route guard fallback shows when test user lacks `<role>.dashboard.view`.
3. Verify Recharts render correctly with mock data (no console errors).
4. Verify i18n switch vi↔en works on all 4 pages.
5. Document F1 (BE seed) + F2 (Sidebar) as follow-up tasks in test report.
6. Spot-check F3 (pharmacy keyboard) — minor fix optional.
