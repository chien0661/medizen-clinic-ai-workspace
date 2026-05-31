# TASK-040 — Review → Test Handoff

**Date:** 2026-05-01
**Reviewer:** Code Review Agent
**Branch:** `feature/task-040-phase-d-screens` (worktree `clinic-cms-web-w2c`)
**Decision:** **CHANGES_REQUESTED** ⚠️ (gate-able to APPROVED — see "Test gating note")

---

## Summary

Implementation delivers 7/8 screens, 5 routes, +19 tests, 566/566 passing, lint+TS clean. Token compliance is solid (TASK-039 inheritance verified). However, two screens fall short of stated acceptance criteria: PatientDetail has 5 of 8 tabs as `DevPlaceholder` (criterion: "all 8 tabs functional, no stub"); ForgotPasswordPage is a 2-step flow (form → success), not the 3-step flow (email → OTP → reset) that 3 Stitch refs `quen-mat-khau-1/2/3` describe and that the handoff itself claims. Both are recoverable as scoped follow-ups; tests can proceed in parallel if PM/PO confirms scope re-cut.

---

## A. Per-màn Conformance (3 deep-dives)

### A.1 ForgotPasswordPage — ⚠️ PARTIAL

| Aspect | Status | Notes |
|--------|--------|-------|
| Centered card 400px | ✅ | `max-w-[400px]` |
| Vietnamese copy | ✅ | Natural; not machine-translated |
| Indigo + Plus Jakarta brand | ✅ | `bg-indigo-600`, MediZen logo |
| `/forgot-password` route | ✅ | Public, lazy-loaded, Suspense fallback |
| LoginPage hand-off | ✅ | `LoginPage.tsx:377` `navigate("/forgot-password")` wired |
| 3-step flow (email → OTP → reset) | ❌ | Only 2 states (form → success). Stitch refs 2/3/4 require OTP step + new-password step. Handoff text says "3-step flow" but code implements 2 states |
| Email-enumeration safety | ✅ | 404 + network errors silently coerced to success — good security posture |

**Gap:** Either (a) descope to "1-step request-link flow" with PM blessing and update handoff to remove the "3-step" claim, or (b) implement OTP + reset-password steps as `quen-mat-khau-2` / `quen-mat-khau-3` Stitch refs intend.

### A.2 PatientDetailPage — ⚠️ PARTIAL (layout ✅, content gaps)

| Aspect | Status | Notes |
|--------|--------|-------|
| 3-col layout 280/720/380 | ✅ (with caveat) | Left `w-[280px]`, middle `flex-1 min-w-0`, right `w-[380px]`. Middle is fluid not 720 fixed — better for responsive but spec said 720. Acceptable |
| 8 tabs rendered | ✅ | Overview, Info, Guardian, Visits, Prescriptions, Invoices, Vitals, BHYT |
| 8 tabs functional | ❌ | Visits, Prescriptions, Invoices, Vitals, BHYT all render `DevPlaceholder` (5/8 stubs). Acceptance criterion explicitly stated "no stub placeholders" |
| AI gợi ý card | ✅ | Indigo gradient, Brain icon, Beta badge, disclaimer |
| Allergies/chronic alert card | ✅ | Conditionally renders if data present |
| Edit-mode (info tab) | ✅ | `useMutation` w/ `patientApi.update` |
| Token compliance | ✅ | `rounded-xl` (cards), indigo accents, `font-display` available |

**Gap:** 5 of 8 tabs are stub. BHYT gating to TASK-034 is acceptable, but Visits/Prescriptions/Invoices/Vitals were promised as "real implementations" in task.md S.2. **Recommend:** flag as known partial, file follow-up TASK-040-B for the four content tabs (data already exists in BE — `visitApi.list({patient_id})`, `prescriptionApi.list({patient_id})`, etc.).

### A.3 ARAgingReportPage — ✅ CONFORM

| Aspect | Status | Notes |
|--------|--------|-------|
| Buckets 0-30/31-60/61-90/>90 | ✅ | All four buckets in summary cards + chart + table |
| Recharts visualization | ✅ | `BarChart` w/ Cell colors per bucket |
| Indigo + amber + orange + red | ✅ | `BUCKET_COLORS` matches spec (indigo for 0-30, escalating to red >90) |
| Per-patient breakdown | ✅ | Searchable table |
| Export CSV | ✅ | BE-first w/ client-side fallback. Includes UTF-8 BOM (`﻿`) — good for Vietnamese in Excel |
| Permission gate | ✅ | `RequirePermission permission="report.financial"` |
| Mock fallback | ✅ | 5 sample patients, plausible amounts |
| Vietnamese formatCurrency | ✅ | `formatCurrency(value)` |
| Tabular nums | ✅ | `tabular-nums` on monetary cells |

---

## B. Token Compliance — ✅ CONFORM

`tailwind.config.js` (TASK-039 baseline):
- `indigo.500 = #6366f1` ✅, `slate`, `emerald`, `amber`, `red`, `sky` palettes ✅
- `fontFamily.display = ['"Plus Jakarta Sans"', ...]` ✅
- `fontFamily.sans = ['Inter', ...]` ✅ (no more Segoe UI)
- `borderRadius.card = 12px`, `input = 8px`, `chip = 6px` ✅
- `index.html` line 9: Google Fonts preload comment present (verify actual `<link>` tag in test phase)

**Spot-check usage in new screens:** all 7 use `bg-indigo-600`, `rounded-xl`, no `brand-*` leakage. ✅

---

## C. i18n — ✅ CONFORM (with one anomaly)

- `vi/auth.json` `forgotPassword.*` (16 keys) — natural Vietnamese ✅
- `vi/profile.json` (new namespace, 26 keys) — registered in `i18n.ts` ✅
- `vi/pharmacy.json` `stocktake.*`, `expiry.*` (~78 lines) — copy is natural ✅
- `vi/reports.json` `arAging.*` (~26 keys) ✅
- `vi/reception.json` `queue.kanban.*` (~20 keys) ✅
- en parity claimed — spot-checked `en/auth.json` matches ✅

⚠️ Minor: `forgotPassword.errors.networkFallback` = "Không kết nối được BE — hiển thị mock thành công" exposes "BE/mock" terminology to end-user via `toast.warning`. Should be user-facing copy (e.g. "Tạm thời không kết nối được. Vui lòng thử lại sau."). Non-blocking.

---

## D. Routing + Nav — ✅ CONFORM

- 5 new routes wired in `router/index.tsx` (lines 217, 372, 380, 575, 626) ✅
- `/forgot-password` is public route (outside `RequireAuth`), `/profile` + 3 pharmacy/report routes inside `AppShell` with `RequireAuth` ✅
- Sidebar pharmacy submenu adds `pharmacy-stocktake` (`/pharmacy/stocktake`) + `pharmacy-expiry` (`/pharmacy/expiry`) at lines 180-191 ✅
- LoginPage `forgotPassword` button now wired (`LoginPage.tsx:377`) ✅
- ProfilePage stub does NOT break login redirect — `/profile` is a normal child route under `AppShell`, no special redirect logic ✅
- ⚠️ `ARAgingReportPage` route: not added to Sidebar nav (only router). Users will need direct URL or breadcrumb until billing nav-section created. Track as MINOR.

---

## E. State Management — ✅ CONFORM

- All new screens use `@tanstack/react-query` (`useQuery`, `useMutation`) — consistent with codebase patterns ✅
- 404/network failures coerced to mock fallback inside `queryFn` (AR Aging) or `mutationFn` (Stocktake, Expiry) — graceful, no toast spam, no crash ✅
- Stocktake `submit` always shows success toast (success path AND mock fallback). Mock path silences error from real fetch — acceptable for pre-BE state ✅
- No orphaned mutations or stale cache observed ✅

---

## F. Accessibility — ⚠️ PARTIAL

| Area | Status | Notes |
|------|--------|-------|
| ForgotPasswordPage `aria-invalid` | ✅ | On Email input |
| ForgotPasswordPage `aria-hidden` on icons | ✅ | Mail, Loader2, ArrowLeft |
| PatientDetailPage back button | ✅ | `aria-label="Go back"` |
| NotificationsPage row-checkbox `aria-label` | ✅ | `"Select notification"` (line 317) |
| NotificationsPage actions `aria-label` | ✅ | `"Mark read"`, `t("panel.dismiss")` |
| ExpiryProcessingPage select-all checkbox | ❌ | Plain `<input type="checkbox">` line 305 — no `aria-label` |
| ExpiryProcessingPage row checkbox | ❌ | No `aria-label` line 339 |
| StocktakePage modal/wizard focus trap | ❌ | Wizard is page-level (no modal), but Step transitions don't focus the next heading. ExpiryProcessing's `ConfirmModal` likewise has no focus trap (no `useEffect` to focus first interactive on open, no Esc-to-close) |
| Kanban column keyboard nav | ⚠️ | QueueBoardPage has no drag-drop yet (deferred), so this is moot. Cards are not focusable — minor regression risk if drag-drop ships later |
| ProfilePage tab role/aria | ⚠️ | Tab `<button>` lacks `role="tab"` / `aria-selected`. Same pattern in PatientDetailPage tabs. Pre-existing in codebase but worth tracking |

**Required for APPROVED:** add `aria-label="Chọn lô"` / `aria-label="Chọn tất cả"` to two ExpiryProcessing checkboxes, and either add focus trap to ConfirmModal or document deferred. Other items are pre-existing; not blocking.

---

## G. Test Quality — ✅ CONFORM (with one note)

- 19 new tests across 4 files; all pass; no flaky markers
- Mock isolation: each test file uses `vi.mock()` for i18n, react-router, sonner, api clients; `beforeEach(vi.clearAllMocks)` ✅
- ForgotPasswordPage: 5 tests (smoke, empty validation, golden path, 404 graceful, back button) ✅
- StocktakePage: 5 tests (smoke, step1 content, step1→2, step2→3, back nav) ✅
- ExpiryProcessingPage: 5 tests (smoke, title, 30/60/90 tabs, switch, default) ✅
- ARAgingReportPage: 4 tests (smoke, title, mock fallback, patient render) ✅
- No snapshot tests (good — explicit assertions instead) ✅

⚠️ Coverage gap: no test for **PatientDetailPage 8-tab navigation** (the largest refactor in the task) and no test for **NotificationsPage bulk-selection / pagination** (key new feature). Recommend test agent extend coverage in IN_TESTING phase.

---

## H. Cross-cutting Collisions

| Risk | Severity | Notes |
|------|----------|-------|
| Sidebar nav additions vs Wave 3-B Sidebar refactor (multi-role grouped) | ⚠️ MEDIUM | New `pharmacy-stocktake`/`pharmacy-expiry` sub-items added to flat `subItems` array. Wave 3-B will likely re-shape into role-grouped sections (`─── Dược sĩ ───` divider per audit §4.4). The two new items are well-formed `NavItem` objects with proper `permission`+`labelKey` so re-grouping is mechanical. **No merge conflict expected** unless TASK-029/Wave 3-B changes the `NavItem` interface |
| ProfilePage tabs vs TASK-033 ProfilePage commit | ⚠️ HIGH | Audit §4.15 says TASK-033 already started ProfilePage skeleton for "Phòng khám của tôi". This branch creates `src/pages/profile/ProfilePage.tsx` from scratch with stub for that tab. **Likely merge conflict** when TASK-033 lands. The handoff acknowledges this (S.4 PARTIAL) — coordinate merge order: this branch first, then TASK-033 fills the stub |
| BHYT history tab in PatientDetail vs TASK-034 | ✅ LOW | BHYT tab uses `DevPlaceholder` with `t("detail.stubs.bhyt")` key. Clean handoff to TASK-034 — no collision risk |
| QueueBoardPage 5-min heuristic for "Đăng ký" vs "Chờ khám" | ⚠️ MEDIUM | Code splits `WAITING` by 5-min `created_at` delta. This is a UI heuristic not a BE state. If TASK-041 adds explicit `REGISTERED` status, this needs to be replaced. **Confirm w/ PM** before testing locks it as canonical behavior |
| `ARAgingReportPage` BE coupling | ✅ LOW | Pure UI w/ mock fallback. TASK-041 BE will replace `MOCK_DATA` cleanly |
| ProfilePage stub tabs (security/notifications/activity) | ⚠️ LOW | These are not gated by another task — they're pure tech debt. Recommend filing TASK-040-C to flesh out 4 tabs before demo |

---

## Test Gating Note

If PM accepts re-scoping ForgotPassword to 1-step flow + accepts PatientDetail 4-tab partial:
→ Status flips to **APPROVED**, proceed to IN_TESTING.

If PM requires full 3-step ForgotPassword + 4 functional content tabs in PatientDetail:
→ Status remains **CHANGES_REQUESTED**, return to IN_PROGRESS.

In either case, test agent can proceed on the 5 fully-conformant screens (S.3, S.5, S.6, S.7, S.8) plus smoke-test of S.1, S.2, S.4 stubs.

---

## Action Items Before Test Phase Approval

1. **PM decision:** ForgotPassword scope (1-step accepted vs 3-step required)
2. **PM decision:** PatientDetail 4 stub tabs accepted as known partial vs blocking
3. **Fix:** add `aria-label` to ExpiryProcessingPage select-all + row checkboxes (5-min change)
4. **Fix:** rewrite `forgotPassword.errors.networkFallback` Vietnamese copy to remove "BE/mock" terminology
5. **Coordination:** confirm merge order with TASK-033 owner re: ProfilePage skeleton
6. **Coordination:** confirm 5-min `WAITING` split heuristic (Đăng ký vs Chờ khám) with PM/PO
7. **Track:** file follow-up tasks for (a) PatientDetail content tabs, (b) ProfilePage 4 stub tabs, (c) ARAging in Sidebar nav

---

## Conformance Ratings vs Stitch Refs

| ID  | Screen                       | Rating | Notes |
|-----|------------------------------|--------|-------|
| S.1 | ForgotPasswordPage           | 60%    | Layout + tokens ✅; missing OTP + reset steps |
| S.2 | PatientDetailPage 8-tab      | 70%    | Layout + tokens + 3 functional tabs ✅; 5 stubs ❌ |
| S.3 | QueueBoardPage 5-col Kanban  | 90%    | All 5 cols, audio chime, fullscreen ✅; drag-drop deferred (acceptable) |
| S.4 | ProfilePage 5-tab            | 35%    | Tab shell + Info tab only; 4 stubs |
| S.5 | ARAgingReportPage            | 95%    | Full conformance |
| S.6 | NotificationsPage enhanced   | 90%    | Bulk + pagination + date filter all working; missing test coverage |
| S.7 | StocktakePage 3-step wizard  | 90%    | All 3 steps, variance highlight, print + new flow |
| S.8 | ExpiryProcessingPage         | 85%    | Working w/ mock; aria-label gaps in checkboxes |

**Average conformance:** ~77% — strong delivery for a multi-screen sprint, but two screens (S.1, S.4) fall short of the task.md acceptance bar.

---

*Review conducted READ-ONLY on `feature/task-040-phase-d-screens` worktree. Files inspected: 11 source + 4 test + 3 i18n + tailwind config + router. No code modifications.*
