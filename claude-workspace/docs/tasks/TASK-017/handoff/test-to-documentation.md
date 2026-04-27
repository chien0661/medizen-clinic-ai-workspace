# Handoff: TASK-017 → Documentation Agent

**From**: Test Agent
**To**: Documentation Agent
**Status**: DOCUMENTING
**Date**: 2026-04-27
**Branch**: `feature/TASK-017-fe-shell` (HEAD `c545481` + 2 new test files added by Test Agent, uncommitted)

---

## Summary

All Phase A tests PASSED (**169/169**). Frontend foundation is fully validated within the host-runtime test envelope (Tauri APIs mocked). Coverage exceeds project thresholds: **85.34% lines / 80.11% branches / 77.41% functions**. TypeScript compiles cleanly (0 errors), ESLint passes with `--max-warnings 0`.

Phase B (Tauri-runtime integration) and Phase C (build + Lighthouse) are deferred to CI per the original review handoff and remain out-of-scope for documentation gating.

---

## Test Results

| Check | Result |
|---|---|
| `npm test -- --run` | **169/169 PASS** (18 files) |
| `npx tsc --noEmit` | 0 errors |
| `npm run lint` | 0 warnings |
| Coverage (Statements / Branches / Functions / Lines) | 85.34% / 80.11% / 77.41% / 85.34% |

**Test report:** `docs/tasks/TASK-017/deliveries/test-reports/test-report.md`

---

## What changed during testing

### New test files created by Test Agent

1. **`clinic-cms-web/src/tests/shell/vi-locale-diacritics.test.ts`** (24 tests)
   - Byte-exact diacritic assertions on auth / shell / validation namespaces
   - Mojibake guard (no `?` or U+FFFD replacement chars)
   - vi/en divergence sanity (no fallback leak)
   - **Purpose:** regression backstop for M2 (vi-locale UTF-8 mangling) — should fail loudly if mojibake recurs

### Renamed file (orphan fix)

2. **`clinic-cms-web/src/tests/shell/authStore.persistence.test.ts` → `…persistence.test.tsx`** (3 tests)
   - The original `.ts` file (untracked, found at start of test phase) contained JSX and would not parse. Renaming to `.tsx` is the standard TS+JSX fix.
   - Content unchanged. Adds an integration scenario combining `authStore.loadFromStorage` + `RequirePermission` gating — useful backstop for the AC "Doctor không thấy menu Pharmacy/Admin sau restart".

These two changes are uncommitted on the working tree at handoff time. Documentation Agent should NOT block on them; they are test artifacts. Either commit them as part of the "test" commit, or include them in the docs commit if your project bundles test+docs.

---

## What documentation needs to cover

Per `.claude/skills/complete-task/` Phase 4:

1. **Functional design document** — primary deliverable
   - Path: `docs/tasks/TASK-017/deliveries/final-specs/[feature-name]-functional-design.md`
   - Template: `docs/templates/specs/functional-design-template.md` (Vietnamese, natural-language)
   - Scope: Auth flow (login / change password / lockout / refresh), App Shell (sidebar / topbar / user menu), Design system primitives, i18n vi/en, theming, error boundary, permission filtering. Should supersede prior detail-design references.

2. **API specs delivery** — `docs/tasks/TASK-017/deliveries/api-specs/`
   - This task consumes BE auth APIs (TASK-003) and Tauri IPC commands (TASK-016). FE itself exposes no HTTP API.
   - Document the FE↔BE auth contract assumptions: login request/response shape (with `password_expired` flag noted as ambiguous — see "Open contract issue" below), refresh contract, error code handling (401/423/429).
   - Document the FE↔Rust IPC commands consumed: `secure_store_get`/`set`/`delete`, `health_check`, `get_app_config`, `get_pending_changes_count`. (These are TASK-016 deliverables — reference, do not redefine.)

3. **Architecture / configuration / troubleshooting docs** (if maintained at the workspace level, update them)
   - State management decisions (Zustand for auth + clinic context; TanStack Query for server cache)
   - Token storage path: Tauri secure store wrapper at `lib/secureStore.ts`; current backend is plaintext-but-honest (`secure_store.rs` emits a warning) — flagged as pre-production technical debt
   - i18n bootstrap and locale layout (`src/locales/{vi,en}/{auth,common,shell,validation}.json`)
   - Theming via Zustand `settingsStore` + Tailwind dark mode

4. **No SQL scripts** for this task — pure FE.

5. **No test cases** delivery — tests live in source repo (`clinic-cms-web/src/tests/shell/*`). Reference the test report instead.

---

## Files relevant to documentation scope

### Frontend (TASK-017 deliverables)
- `clinic-cms-web/src/lib/{apiClient,secureStore,i18n,format,utils}.ts`
- `clinic-cms-web/src/stores/{authStore,settingsStore,networkStore}.ts`
- `clinic-cms-web/src/components/auth/{RequireAuth,RequirePermission}.tsx`
- `clinic-cms-web/src/components/error/ErrorBoundary.tsx`
- `clinic-cms-web/src/components/shell/{AppShell,Sidebar,Topbar}.tsx`
- `clinic-cms-web/src/pages/auth/{LoginPage,ChangePasswordPage}.tsx`
- `clinic-cms-web/src/router/index.tsx`
- `clinic-cms-web/src/locales/{vi,en}/*.json`

### Backend (Tauri — TASK-016 deliverables, referenced only)
- `clinic-cms-web/src-tauri/src/secure_store.rs`
- `clinic-cms-web/src-tauri/src/lib.rs`
- `clinic-cms-web/src-tauri/capabilities/default.json`

---

## Open / known issues for documentation to flag

1. **`password_expired` API contract gap** — TASK-003 spec is ambiguous about whether the BE returns `password_expired` on the login response `user` object. FE handles its absence gracefully (forced `/change-password` redirect simply never fires). Documentation should:
   - Note this as a known FE/BE contract risk.
   - Recommend BE returns `password_expired` (boolean, default false) in the `LoginResponse.data.user` object.
   - Defer final resolution to Phase B integration testing.

2. **`secure_store.rs` is plaintext** — emits a runtime warning. Pre-production. Should be replaced by `keyring` crate before any non-dev deployment. Documentation should call this out as a release blocker for production.

3. **Topbar clinic name hardcoded** — `Topbar.tsx` shows literal "Clinic CMS"; will be wired from clinic context in TASK-018. Documentation should note this is a known stub.

4. **Phase B / C deferred** — see test report for full list.

---

## What is NOT in scope for documentation

- The two test files added/renamed by Test Agent are test artifacts, not feature code. Mention them in the "Testing" section of the functional design but do not document them as user-facing features.
- Sync engine / database (`sync/*`) was committed in TASK-016 and is referenced here only via the existing `network-store` integration; not a TASK-017 deliverable.

---

## Quality gate confirmation

| Gate (PROJECT.md `Quality Gates`) | Threshold | Actual | ✓/✗ |
|---|---|---|---|
| Required Test Pass Rate | 100% | 100% (169/169) | ✓ |
| Unit Tests Required | true | covered | ✓ |
| Integration Tests Required | true | covered (within Phase A envelope) | ✓ |
| E2E Tests Required | false | n/a (Phase B deferred regardless) | n/a |
| Coverage (new code) | ≥ 80% lines | 85.34% lines | ✓ |
| Build Must Pass Before Review | true | tsc 0 / lint 0 | ✓ |

All gates green. Proceed with Phase 4 documentation.
