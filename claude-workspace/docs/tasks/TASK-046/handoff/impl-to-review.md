# TASK-046 — Handoff: Implementation → Review

**Date**: 2026-05-01  
**Branch**: `feature/task-046-security-settings` (worktree: `clinic-cms-web-w5w`)  
**Status**: Implementation complete — ready for code review

---

## Files Added (6 files)

| # | File | Description |
|---|------|-------------|
| 1 | `src/pages/admin/SecuritySettingsPage.tsx` | Main page — 4 panels |
| 2 | `src/components/admin/TenantErasureModal.tsx` | 2-step erasure confirmation modal |
| 3 | `src/locales/vi/security.json` | Vietnamese i18n (32 keys) |
| 4 | `src/locales/en/security.json` | English i18n (32 keys) |
| 5 | `src/tests/admin/SecuritySettingsPage.test.tsx` | Page tests (12 tests) |
| 6 | `src/tests/admin/TenantErasureModal.test.tsx` | Modal tests (11 tests) |

## Files Modified (3 files)

| File | Change |
|------|--------|
| `src/router/index.tsx` | Added `/admin/security` route + lazy import |
| `src/components/shell/Sidebar.tsx` | Added `admin-security` nav item + `ShieldCheck` import |
| `src/lib/i18n.ts` | Registered `security` namespace for vi + en |

---

## Routes Added (1)

| Route | Component | Permission |
|-------|-----------|------------|
| `/admin/security` | `SecuritySettingsPage` | `admin.security.view` (placeholder) |

---

## i18n Keys (32 keys per locale = 64 total)

Namespace: `security`

Sections:
- `nav.*` — 1 key (sidebar label)
- `page.*` — 2 keys (title, subtitle)
- `mfa.*` — 9 keys
- `encryption.*` — 8 keys
- `loginHistory.*` — 8 keys (includes `columns.*`)
- `password.*` — 5 keys
- `erasure.*` — 12 keys
- `common.*` — 5 keys

---

## Tests Added (23 tests across 2 files)

| File | Count | Coverage |
|------|-------|----------|
| `SecuritySettingsPage.test.tsx` | 12 | render, all 4 panels, MFA navigation, encryption KMS, erasure modal trigger, login history table, logout-all, password navigation |
| `TenantErasureModal.test.tsx` | 11 | open/closed state, warning banner, submit disabled (3 scenarios), submit enabled (full match), name mismatch hint, submission state, success message |

---

## Mock Placeholder List (7 mocks — connect at merge time)

| ID | Location | What | Blocked by |
|----|----------|------|------------|
| MOCK-1 | `SecuritySettingsPage.tsx:135` | `authStore.user.mfa_enabled` — always `false` (field not in `UserInfo`) | TASK-038 MFA FE merge |
| MOCK-2 | `SecuritySettingsPage.tsx:278` | `authStore.user.password_changed_at` — field not in `UserInfo` | TASK-038 MFA FE merge |
| MOCK-3 | `SecuritySettingsPage.tsx:47` | `GET /api/v1/auth/fingerprints` — hardcoded 5 rows | TASK-038 fingerprints endpoint |
| MOCK-4 | `SecuritySettingsPage.tsx:337` | `POST /api/v1/auth/sessions/logout-others` — no-op placeholder | TASK-038 |
| MOCK-5 | `SecuritySettingsPage.tsx:192`, `TenantErasureModal.tsx:64` | Vault KMS hardcoded / clinic name hardcoded | TASK-037-P2 `/health/kms` + `/clinics/me` |
| MOCK-6 | `SecuritySettingsPage.tsx:55` | DEK rotation date — hardcoded `2026-04-01` | TASK-037-P2 KMS rotation API |
| MOCK-7 | `SecuritySettingsPage.tsx:58` | Backup codes last generated — hardcoded `2026-03-15` | TASK-038 backup codes API |

---

## Merge-Time Integration TODOs

1. **TASK-038 MFA FE** — After merge:
   - Add `mfa_enabled: boolean` and `password_changed_at: string | null` to `UserInfo` in `authStore.ts`
   - Remove placeholder casts in `SecuritySettingsPage.tsx` (lines 135, 278)
   - Confirm `/auth/mfa/enroll`, `/auth/mfa/disable`, `/auth/mfa/backup-codes/regenerate` routes exist

2. **TASK-037-P2 Health Check** — After merge:
   - Replace hardcoded `"Vault"` with `GET /health/kms` response
   - Replace hardcoded DEK rotation date with actual API data

3. **TASK-038 Fingerprints** — After merge:
   - Replace `MOCK_FINGERPRINTS` array with `useQuery(() => api.get('/api/v1/auth/fingerprints'))`
   - Replace logout-all no-op with `api.post('/api/v1/auth/sessions/logout-others')`

4. **Clinic Name / Erasure** — After `/clinics/me` endpoint available:
   - Replace hardcoded `"Phòng khám MediZen"` with actual clinic name from store
   - Connect `TenantErasureModal` `handleSubmit` to `api.post('/api/v1/admin/clinics/{id}/erase')`

5. **Permission gating** — `admin.security.view` permission is referenced in `Sidebar.tsx` nav item but `RequirePermission` wrapper is NOT applied at route level yet — add to router if strict gating needed.

---

## Build & QA Status

| Check | Status |
|-------|--------|
| `tsc --noEmit` | PASS (0 errors) |
| `npm run lint` | PASS (0 warnings) |
| `npm test -- --run` | PASS (578/578 tests, 52 test files) |
| `npm run build` | PASS (built in 18.57s; chunk size warning pre-existing) |
