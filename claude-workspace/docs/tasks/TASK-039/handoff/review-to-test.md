---
task: TASK-039
handoff: review → test
date: 2026-05-01
author: code-review agent
status: APPROVED-WITH-MINOR-FIXES
decision: APPROVED
---

# TASK-039 Code Review Report — MediZen Design System Port

## Decision

**APPROVED** — ready for Test phase.

Two minor cosmetic findings logged below (one CSS-syntax bug, one comment-hygiene gap). Neither blocks test phase; recommend implementation agent fix in a follow-up commit before merging, but they do not affect runtime correctness for tested screens.

---

## A. Token correctness — `tailwind.config.js`

| Item | Status | Notes |
|---|---|---|
| `darkMode: 'class'` | OK | Line 3 |
| Indigo full scale 50–900 (+ 950) | OK | Lines 13–25; `500: '#6366f1'` matches spec |
| Slate full scale 50–900 (+ 950) | OK | Lines 27–39 |
| Emerald, Amber, Red, Sky scales | OK | Lines 41–95; all 50–950 |
| `surface` tokens (white/bg/border) | OK | Lines 97–101 |
| `borderRadius` card 12px / input 8px / chip 6px | OK | Lines 107–111 |
| `fontFamily.display: ['"Plus Jakarta Sans"', 'sans-serif']` | OK | Line 104 |
| `fontFamily.sans: ['Inter', 'system-ui', ...]` | OK | Line 105 |
| Spacing baseline 4px / gutter 24px | OK | Lines 112–115 |
| `@tailwindcss/forms` plugin retained | OK | Line 120 |

Tokens spec **fully compliant**. Explicit hex values (vs. Tailwind defaults) is a sound canonical-source decision (per impl deviation #1).

---

## B. Brand rename completeness

| Check | Result |
|---|---|
| `brand-` references in `src/` | 0 OK |
| `CURA` literal in `src/` | 0 OK |
| `Clinic CMS` in TS/TSX UI text | 0 OK (Sidebar L404, Topbar L78, LoginPage L236/275 all "MediZen") |
| `index.html` `<title>MediZen</title>` | OK (line 8) |
| `<meta description>` says "MediZen Desktop Client" | OK (line 7) |
| Google Fonts preconnect + Plus Jakarta Sans 600/700 + Inter 400/500 link | OK (lines 10–15) |

Remaining `Clinic CMS` references (all expected non-UI strings):
- `src/locales/{vi,en}/common.json` `appName` — i18n strings, deferred per task (warn for TASK-040).
- `src/tests/shell/i18n.test.ts` — asserts current i18n key value, must update with i18n strings.
- `src/lib/apiClient.ts:2` — JSDoc comment (handoff acknowledged).
- `src/lib/i18n.ts:2` — JSDoc comment, **NOT mentioned in handoff** ⚠️ (cosmetic only).

---

## C. Codemod safety — sample audit

Spot-checked 8 files: `button.tsx`, `input.tsx`, `dialog.tsx`, `checkbox.tsx`, `LoginPage.tsx`, `Sidebar.tsx`, `PurchaseInPage.tsx`, `PatientRegisterPage.tsx`.

| Check | Result |
|---|---|
| Replacements all have valid suffix (no `indigo-` followed by space/empty) | OK — grep for `(bg\|text\|border\|...)-indigo-\s` returns 0 |
| Dark-mode variants intact (e.g. `dark:bg-brand-700` → `dark:bg-indigo-700`) | OK — `dark:.*-brand-` returns 0; spot-checked `NotificationsPanel.tsx`, `AttendanceWidget.tsx`, `VisitVolumePage.tsx` |
| `accent-brand-*` second-pass complete | OK — 5/5 places now `accent-indigo-500` (`AddLineModal`, `AddPaymentModal`, `OnboardingPage` x2, `ExtraPermissionsPage`) |
| `button.tsx` variants render correctly | OK — `bg-indigo-500 hover:bg-indigo-600 active:bg-indigo-700` clean |
| Highest-replacement file `PatientRegisterPage.tsx` (18 hits) | OK — opens cleanly, no malformed classes |

**No broken codemod output detected.**

---

## D. Token export quality — `src/lib/tokens.ts`

| Check | Result |
|---|---|
| Exports `colors`, `chartColors`, `borderRadius`, `spacing`, `fontFamily` | OK |
| `as const` on all literals — TypeScript-strict-friendly | OK |
| Default export bundles all 5 token groups | OK |
| Hex values match `tailwind.config.js` 1:1 | OK |
| `chartColors.grid: slate-200` matches `stroke="#e2e8f0"` used in chart files | OK |
| JSDoc comments explain purpose | OK |

Clean module. Type-safe, importable as named or default.

---

## E. Recharts theming

Sampled `PrescriptionAnalyticsPage.tsx` (line 29: `PIE_COLORS = ["#6366f1", "#10b981", "#ef4444"]`) and `RevenueReportPage.tsx` (line 139: `Bar fill="#6366f1"`, line 140: `Bar fill="#10b981"`).

| Check | Result |
|---|---|
| Primary series uses indigo-500 `#6366f1` | OK |
| Secondary series uses emerald-500 `#10b981` | OK (was violet `#8b5cf6`) |
| Grid stroke `#e2e8f0` (slate-200) | OK across 7 chart locations (`MainDashboardPage`, `VisitVolumePage`, `RevenueReportPage`, `PrescriptionAnalyticsPage`, `DoctorPerformancePage` etc.) |

Violet → emerald migration is **justified** per MediZen palette (no violet token defined). Recommend Test phase verify visual contrast on stacked-bar charts where two series sit adjacent (indigo + emerald has good chromatic separation).

**Note**: chart files use hardcoded hex strings rather than importing from `tokens.ts`. Acceptable for now (spec doesn't require import refactor) but flagged as future hygiene improvement.

---

## F. Build / test integrity

| Check | Result |
|---|---|
| Build PASS (21.46s) | OK |
| Build warnings | 1 pre-existing chunk-size warning (1,108 kB) — unrelated to TASK-039 |
| Tests 547/547 PASS | OK |
| New tests `design-tokens.test.ts` (18) | OK — assertions concrete (e.g. `expect(colors.indigo[500]).toBe("#6366f1")`); not over-broad snapshot |
| No new test snapshots introduced | OK |

---

## G. Spec deviations — reviewer verdict

1. **Sidebar `bg-slate-900` (vs `bg-indigo-900`)** — APPROVED. `MEDIZEN_FRESH_PROJECT.md` does not specify a sidebar bg color explicitly; slate-900 is a reasonable dark neutral that lets indigo accents (`text-indigo-400` icon, future `bg-indigo-500` active states) pop. Documented in handoff. Test phase should screenshot Sidebar against any available Stitch reference and flag if mismatch.

2. **i18n strings NOT touched** — APPROVED. Per task constraint. Recommend creating sub-task in TASK-040 i18n expansion: rename `appName` `"Clinic CMS"` → `"MediZen"` in both locale JSONs + update `tests/shell/i18n.test.ts` assertion.

3. **Recharts violet → emerald** — APPROVED. Spec-compliant; Test should visually confirm legibility on `RevenueReportPage` stacked bars + `PrescriptionAnalyticsPage` pie segments.

---

## H. Out-of-scope items

| Item | Status |
|---|---|
| F.8 logo asset replacement (Shield → MediZen SVG) | DEFERRED — agent confirmed; task.md should mark F.8 as separate sub-task |
| F.9 favicon + Tauri icon | DEFERRED — `src-tauri/tauri.conf.json` window title may still say "Clinic CMS"; flagged for follow-up |
| F.11 component restyle (radius/shadow application on Button/Input/Card/Modal/Toast/Badge) | DEFERRED — confirmed; task.md acceptance criteria should be updated to mark F.11 explicitly out-of-scope or split into TASK-039b |
| T.1 Playwright visual regression | DEFERRED — separate scope per impl brief; Test phase will run smoke tests instead |
| T.2 Dark mode parity test | Not seen as new test in `design-tokens.test.ts`; Test phase should manually toggle dark mode on Login + Dashboard + Sidebar |

**Recommendation**: Update `task.md` Acceptance Criteria to clarify F.8/F.9/F.11/T.1/T.2 are explicit sub-tasks, OR split into TASK-039b before closing this task. Otherwise the "match Stitch screen visually" criterion remains technically open.

---

## Findings — minor fixes (non-blocking)

### Finding 1 — `src/styles.css` line 21: invalid CSS quote in dark variable ⚠️

```css
.dark {
  ...
  --color-brand: '#818cf8';  /* indigo-400 — INVALID: hex must NOT be quoted */
}
```

The light-mode value (line 12) is correctly unquoted: `--color-brand: #6366f1;`. The dark-mode value uses single quotes which makes it a string `'#818cf8'`, not a color. Browsers will fail to apply this when used as `color: var(--color-brand)`.

**Fix**: remove single quotes → `--color-brand: #818cf8;`

**Impact**: Low — `--color-brand` doesn't appear to be `var()`-referenced anywhere in current code. But it's a latent bug if anyone uses it later. Recommend fix before test phase.

### Finding 2 — `src/lib/i18n.ts` line 2: stray "Clinic CMS" in JSDoc ⚠️

```ts
/**
 * i18next configuration for Clinic CMS.
```

Handoff acknowledged `apiClient.ts` comment but missed this one. Two-line cosmetic fix.

**Impact**: None on runtime; comment hygiene only. Bundle into Finding 1's commit.

---

## Recommended pre-test follow-up commit

```
fix(design-system): unquote dark mode --color-brand var; sync i18n.ts comment

- src/styles.css: remove single quotes around #818cf8
- src/lib/i18n.ts: "Clinic CMS" → "MediZen" in JSDoc (cosmetic)
```

Both are 1-line edits. Implementation agent can ship this as a tiny patch before test agent picks up, OR test agent can flag during smoke test if dark-mode `--color-brand` is exercised.

---

## Test phase entry checklist

Test agent should verify:

1. ✅ Login page renders with MediZen text + Indigo button + Plus Jakarta Sans heading + Inter body
2. ✅ MainDashboardPage charts render with indigo primary + emerald secondary; grid stroke is slate-200 not pre-existing `#f0f0f0`
3. ✅ Sidebar shows `bg-slate-900` with indigo-400 Shield icon and "MediZen" label (not "Clinic CMS")
4. ✅ Topbar shows "MediZen" clinic name (line 78)
5. ✅ Dark-mode toggle on Login + Dashboard + Sidebar — no broken color contrast
6. ✅ Browser tab title says "MediZen" (index.html title)
7. ✅ Google Fonts loaded (DevTools Network → fonts.gstatic.com requests succeed)
8. ⚠️ If Finding 1 not patched: confirm no console warnings about invalid `--color-brand` in dark mode

---

## Summary table

| Category | Status |
|---|---|
| A. Tokens | OK |
| B. Brand rename | OK (2 cosmetic comment misses) |
| C. Codemod safety | OK |
| D. tokens.ts quality | OK |
| E. Recharts theming | OK |
| F. Build / tests | OK |
| G. Spec deviations | OK (all justified) |
| H. Out-of-scope | OK (DEFERRED items flagged for task.md update) |

**Decision: APPROVED → proceed to Test phase.**
