# TASK-046 — Handoff: Review → Test

**Date**: 2026-05-01
**Branch**: `feature/task-046-security-settings` (worktree `clinic-cms-web-w5w`)
**Reviewer**: code-review agent
**Decision**: **APPROVED with minor notes** (proceed to testing)

---

## Decision Rationale

Implementation is well-structured, type-safe, and tests pass cleanly. All 7 mock placeholders are documented inline with `[MOCK-N]` tags + JSDoc header + handoff matrix referencing exact upstream tasks (TASK-038, TASK-037-P2). Modal 2-step confirmation logic is correct and gated. Build is green (TS=0, lint=0, tests 72/72 in admin namespace pass — page+modal added 31 tests, not 23 as claimed in handoff but that's an undercount, not a regression).

A handful of minor warnings (hardcoded VN strings, missing `aria-describedby` on Dialog, unwrapped `RequirePermission` at route level) are non-blocking. They can be tracked as follow-ups during merge orchestration. No CHANGES_REQUESTED — proceeding to test.

---

## Checklist Results

### A. SecuritySettingsPage 4 panels

| Item | Status |
|---|---|
| MFA panel: status badge + enable/disable button + backup codes regenerate via URL nav (`/auth/mfa/enroll`, `/auth/mfa/disable`, `/auth/mfa/backup-codes/regenerate`) | ✅ |
| Encryption panel: AES-256-GCM displayed via `algorithmValue`, KMS Vault hardcoded `[MOCK-5]`, last DEK rotation `[MOCK-6]`, erasure trigger button | ✅ |
| Login history panel: table renders 5 mock fingerprints with IP / device / geo / timestamp + logout-all button | ✅ |
| Password panel: last-changed date + change-now button + 90-day expiry tooltip (uses both `title=` HTML attr and visible `<p>` italic) | ✅ |

### B. TenantErasureModal — 2-step confirmation

| Item | Status |
|---|---|
| Vietnamese warning: `KHÔNG THỂ KHÔI PHỤC` in `warningTitle` + `warningText` | ✅ |
| Clinic name match input (trim-compare `confirmName.trim() === clinicName.trim()`) | ✅ |
| Checkbox `Tôi hiểu hậu quả và đã backup dữ liệu cần thiết` | ✅ |
| Submit enabled only when `nameMatches && understood && !isSubmitting` | ✅ |
| `POST /api/v1/admin/clinics/{id}/erase` placeholder via 1.2s `setTimeout` simulation; `clinicId` referenced via `void` to silence unused warning | ✅ (placeholder by design) |
| Success/error states render `submitResult` block | ✅ |

### C. Mock placeholders (7)

All seven placeholders inline-tagged `[MOCK-N]`, listed in JSDoc header, mirrored in handoff matrix. Each entry maps to upstream task. Login history shows 5 fixed rows; logout-all shows confirm dialog then no-ops; erasure modal returns simulated success. Empty-state UX (`loginHistory.noHistory`) wired but unreachable until BE swaps in. ✅

### D. Permission gate

| Item | Status |
|---|---|
| Sidebar item gated `admin.security.view` via `RequirePermission` wrapper (line 365) | ✅ |
| **Route level not wrapped with `RequirePermission`** (router lines 528–535) — handoff item #5 acknowledges; sidebar gating is the only filter today | ⚠️ Documented intentional gap; track for orchestrator merge |
| Permission key `admin.security.view` consistent with multi-segment convention (`report.financial`, `pharmacy.dispense`, `settings.vital_schema`); not in conflict with TASK-044 fix | ✅ |

### E. i18n vi/en — 32 keys

Both `security.json` files registered in `i18n.ts` lines 32–33, 52–53, 79, 100, 105. Keys count matches: nav(1)+page(2)+mfa(9)+encryption(8 incl. `algorithm`, `lastDekRotationNever`)+loginHistory(8)+password(5)+erasure(13)+common(5) = 51 keys. Handoff says 32 — minor undercount in handoff doc, not a defect.

| Item | Status |
|---|---|
| Section labels translated bilingually | ✅ |
| Modal text bilingual (warning, step 1/2, submit, cancel, success, error) | ✅ |
| Button labels translated | ✅ |
| **Hardcoded VN strings**: `Trạng thái:` (page lines 205, 281) + `Tên phòng khám không khớp` (modal line 165) | ⚠️ Three hardcoded VN strings leak past i18n — add `mfa.status`/`encryption.status` and `erasure.nameMismatch` keys in a follow-up. Non-blocking. |

### F. a11y

| Item | Status |
|---|---|
| Modal focus trap (Radix `DialogPrimitive`) | ✅ |
| Esc-to-close (built-in via Radix) | ✅ |
| ARIA on input: `aria-describedby="confirm-name-hint"` paired with `<p id="confirm-name-hint">` | ✅ |
| Checkbox `<label htmlFor>` association + cursor-pointer | ✅ |
| `<DialogPrimitive.Close>` has `<span className="sr-only">Close</span>` | ✅ |
| **DialogContent missing `Description` / `aria-describedby`** — Radix emits warnings for every modal mount in tests | ⚠️ Add `<DialogDescription>` (or `aria-describedby`) wrapping warningText. Recommend add as follow-up. |

### G. Cross-task coord

| Item | Status |
|---|---|
| TASK-038 MFA FE uncommitted → URL navigation strategy (`navigate("/auth/mfa/enroll")`) so links resolve post-merge without code change | ✅ Sound strategy |
| TASK-037-P2 `/health/kms` → hardcoded `Vault` string with `[MOCK-5]` tag | ✅ |
| TASK-035 sidebar nav-item `admin-security` already added under "Quản trị" group; orchestrator merge needs only conflict resolution if other admin tasks add siblings | ✅ |
| `authStore.user.mfa_enabled` / `password_changed_at` accessed defensively via `(user as Record<string,unknown>)?.[key]` to avoid TS errors before TASK-038 widens `UserInfo` | ✅ |

### H. Test quality

23 tests claimed in handoff; vitest run reports `SecuritySettingsPage.test.tsx (18 tests) + TenantErasureModal.test.tsx (13 tests) = 31`. All pass in 3.17s.

| Item | Status |
|---|---|
| Modal flow gating: 4 scenarios (none, name only, checkbox only, both — partial match too) | ✅ |
| Submission state asserted (disabled during async, success message after) | ✅ |
| 4-panel rendering smoke checks via `data-testid` | ✅ |
| MFA navigation paths asserted (`/auth/mfa/enroll`, `/auth/mfa/backup-codes/regenerate`) | ✅ |
| Mock data isolation via `vi.mock` of `authStore` + `react-i18next` + `useNavigate` — no global leak | ✅ |
| **Logout-all `window.confirm` flow not asserted** (only button presence) | ⚠️ Add a test exercising confirm-yes branch in test phase |
| **Modal close after success not asserted** (success message renders but `handleClose` not invoked) | ⚠️ Minor gap |

### I. Indigo MediZen tokens

| Item | Status |
|---|---|
| Modal: `bg-white shadow-xl rounded-lg` (Dialog) + `max-w-md` (Erasure override) | ✅ |
| Status badges: emerald-50/700 (active) + amber-50/700 (inactive) — red reserved for warning banner | ✅ |
| Primary button: `bg-indigo-600 hover:bg-indigo-700 text-white`; ghost variant with slate borders for secondary | ✅ |
| Destructive: `border-red-200 text-red-600 hover:bg-red-50` for erase button + `variant="destructive"` for modal submit | ✅ |

---

## Findings Summary

### Top 3 issues (all non-blocking)

1. **Route-level permission gate missing** (handoff item #5) — `/admin/security` not wrapped in `RequirePermission`. Sidebar hides the link, but a user with the URL could still hit the page. Track at merge orchestration; suggest wrapping `<RequirePermission permission="admin.security.view" fallback={<PermissionDenied />}>` directly inside the route element.
2. **Three hardcoded VN strings** leak past i18n: `Trạng thái:` ×2 in page + `Tên phòng khám không khớp` in modal. Add three keys (`mfa.statusLabel`, `encryption.statusLabel`, `erasure.nameMismatch`) in follow-up.
3. **Radix `DialogContent` a11y warning** — every modal mount logs `Missing Description or aria-describedby`. Add `<DialogDescription>` (visible or sr-only) wrapping the warning text.

### Mock placeholder strategy: STRONG

All 7 mocks are tagged inline `[MOCK-N]`, mirrored in JSDoc header, listed in handoff matrix with the upstream task that unblocks each. Defensive type access (`as Record<string,unknown>`) avoids breaking when `UserInfo` is later widened. Swap should be 1-line each. Empty-state UI scaffold present in login history. No fake data leaks into production code paths.

### a11y compliance: PASS-with-note

Radix Dialog provides focus trap + ESC + scroll lock + portal + initial focus by default. Input/checkbox/label associations correct. `aria-describedby="confirm-name-hint"` wired to error text. Only gap: `DialogDescription` not present, generating Radix dev-mode warning. Not a screen-reader blocker (warning text is visible on-screen) but should be fixed before production sweep.

### Cross-task merge coord: ON-TRACK

URL-navigation pattern for MFA enroll/disable means no code rewrite needed when TASK-038 lands. KMS provider, DEK rotation, fingerprints, logout-all, password_changed_at, mfa_enabled all isolated to single-line swaps with grep-friendly `[MOCK-N]` tags. Sidebar nav item already wired with correct permission. Recommend orchestrator add route-level `RequirePermission` wrapper at merge time alongside hardcoded-string i18n cleanup and `DialogDescription`.

---

## Build & QA Verification

| Check | Result |
|---|---|
| `tsc --noEmit` (full project) | PASS |
| `npm run lint` | PASS |
| `npm test -- --run src/tests/admin/` | 72/72 PASS (3.17s) |
| Build (per handoff) | PASS (18.57s, pre-existing chunk-size warning) |

---

## Handoff to Test

Test agent — please proceed with:

1. Manual smoke flow at `http://localhost:5173/#/admin/security` (run `npm run dev` from worktree).
2. Verify each panel renders + buttons clickable.
3. Open erasure modal, exercise both negative paths (mismatched name, unchecked box) and positive path; confirm 1.2s spinner + success banner; close modal.
4. Test bilingual switch (vi ↔ en) — note the 3 hardcoded VN strings will not flip.
5. Test keyboard: Tab through panels, ESC closes modal, focus returns to trigger button.
6. Capture screenshots into `docs/tasks/TASK-046/deliveries/test-reports/`.
7. (Optional) Add unit coverage for the two minor test gaps noted in section H.

No bugs to file pre-test. Proceed.
