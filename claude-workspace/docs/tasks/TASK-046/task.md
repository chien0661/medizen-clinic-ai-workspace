---
id: TASK-046
type: feature
title: Bảo mật Settings Page — MFA, Mã hoá, Lịch sử đăng nhập, Đổi mật khẩu + TenantErasureModal
status: DONE
priority: High
assigned: ""
created: 2026-04-26
updated: 2026-05-01
completed: 2026-05-01
branch: "feature/task-046-security-settings"
jira_key: ""
tags: [admin-security, settings, encryption, mfa, frontend, task-046]
affected-repos: [clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-046: Bảo mật Settings Page — MFA, Mã hoá, Lịch sử đăng nhập, Đổi mật khẩu + TenantErasureModal

## Description

Xây dựng trang bảo mật & mã hoá (Security & Encryption Settings) cho quản trị viên hệ thống, cung cấp giao diện quản lý 4 khía cạnh bảo mật:
1. **Xác thực 2 lớp (MFA)**: Toggle enable/disable, regenerate backup codes
2. **Mã hoá dữ liệu**: AES-256-GCM status, KMS provider, DEK rotation tracking, trigger erasure
3. **Lịch sử đăng nhập**: 10 phiên gần nhất (IP, device, geo, timestamp), logout-all button
4. **Đổi mật khẩu**: Lần đổi gần nhất, change-now button, 90-day expiry tooltip

Hỗ trợ xoá dữ liệu phòng khám vĩnh viễn (crypto-shred) thông qua modal xác nhận 2 bước:
- Step 1: Nhập tên phòng khám để xác nhận danh tính
- Step 2: Tick checkbox xác nhận hậu quả

## Requirements (Acceptance Criteria)

### A. SecuritySettingsPage (4 panels)

- [ ] MFA panel: status badge + enable/disable button + backup codes regenerate via URL nav (`/auth/mfa/enroll`, `/auth/mfa/disable`, `/auth/mfa/backup-codes/regenerate`)
- [ ] Encryption panel: AES-256-GCM displayed via `algorithmValue`, KMS Vault hardcoded `[MOCK-5]`, last DEK rotation `[MOCK-6]`, erasure trigger button
- [ ] Login history panel: table renders 5 mock fingerprints with IP / device / geo / timestamp + logout-all button
- [ ] Password panel: last-changed date + change-now button + 90-day expiry tooltip (uses both `title=` HTML attr and visible `<p>` italic)
- [ ] Page title: "Bảo mật & Mã hoá" + subtitle: "Quản lý xác thực, mã hoá dữ liệu và lịch sử truy cập"

### B. TenantErasureModal — 2-step confirmation

- [ ] Vietnamese warning: `KHÔNG THỂ KHÔI PHỤC` in `warningTitle` + `warningText`
- [ ] Clinic name match input (trim-compare `confirmName.trim() === clinicName.trim()`)
- [ ] Checkbox `Tôi hiểu hậu quả và đã backup dữ liệu cần thiết`
- [ ] Submit enabled only when `nameMatches && understood && !isSubmitting`
- [ ] `POST /api/v1/admin/clinics/{id}/erase` placeholder via 1.2s `setTimeout` simulation
- [ ] Success/error states render `submitResult` block
- [ ] `<DialogDescription>` wrapping warning text (Radix UI a11y requirement)

### C. Mock placeholders (7 documented)

- [ ] All seven placeholders inline-tagged `[MOCK-N]`, listed in JSDoc header, mirrored in handoff matrix
- [ ] Each entry maps to upstream task (TASK-038, TASK-037-P2)
- [ ] Empty-state UX (`loginHistory.noHistory`) wired but unreachable until BE swaps in

### D. Permission gate

- [ ] Route `/admin/security` wrapped with `<RequirePermission permission="admin.security.view">`
- [ ] Sidebar item gated `admin.security.view` via `RequirePermission` wrapper
- [ ] Permission key `admin.security.view` consistent with multi-segment convention

### E. i18n vi/en — 55 keys

- [ ] Both `security.json` files registered in `i18n.ts`
- [ ] Section labels translated bilingually
- [ ] Modal text bilingual (warning, step 1/2, submit, cancel, success, error)
- [ ] Button labels translated
- [ ] NO hardcoded VN strings (all replaced with i18n keys)

### F. a11y compliance

- [ ] Modal focus trap (Radix `DialogPrimitive`)
- [ ] Esc-to-close (built-in via Radix)
- [ ] ARIA on input: `aria-describedby="confirm-name-hint"` paired with error text `<p id="confirm-name-hint">`
- [ ] Checkbox `<label htmlFor>` association + cursor-pointer
- [ ] `<DialogDescription>` present wrapping warning text (fixes Radix dev warning)

### G. Cross-task coord

- [ ] TASK-038 MFA FE uncommitted → URL navigation strategy (`navigate("/auth/mfa/enroll")`) so links resolve post-merge without code change
- [ ] TASK-037-P2 `/health/kms` → hardcoded `Vault` string with `[MOCK-5]` tag
- [ ] TASK-035 sidebar nav-item `admin-security` already added under "Quản trị" group
- [ ] `authStore.user.mfa_enabled` / `password_changed_at` accessed defensively via `(user as Record<string,unknown>)?.[key]` to avoid TS errors before TASK-038 widens `UserInfo`

### H. Test quality

- [ ] 31 tests (18 page + 13 modal) all passing
- [ ] Modal flow gating: 4 scenarios (none, name only, checkbox only, both)
- [ ] Submission state asserted (disabled during async, success message after)
- [ ] 4-panel rendering smoke checks via `data-testid`
- [ ] MFA navigation paths asserted
- [ ] Mock data isolation via `vi.mock` of `authStore` + `react-i18next` + `useNavigate`

### I. Build verification

- [ ] `tsc --noEmit` = 0 errors
- [ ] `npm run lint` = 0 warnings
- [ ] `npm test -- --run` = 578 tests passing

## Implementation Notes

### Files created

- `src/pages/admin/SecuritySettingsPage.tsx` (374 lines)
- `src/components/admin/TenantErasureModal.tsx` (233 lines)
- `src/locales/vi/security.json` (80 lines, 55 keys)
- `src/locales/en/security.json` (80 lines, 55 keys)
- `src/tests/admin/SecuritySettingsPage.test.tsx` (280 lines, 18 tests)
- `src/tests/admin/TenantErasureModal.test.tsx` (355 lines, 13 tests)

### Files modified

- `src/router/index.tsx` — Added `/admin/security` route + `RequirePermission` import + guard
- `src/components/shell/Sidebar.tsx` — Added nav item `admin-security`
- `src/lib/i18n.ts` — Registered `security` namespace
- `src/pages/admin/SecuritySettingsPage.tsx` — Fixed hardcoded strings (line 205, 281) → i18n keys
- `src/components/admin/TenantErasureModal.tsx` — Fixed hardcoded string (line 165) + added `DialogDescription`

## Completion Notes (2026-05-01)

✅ **All acceptance criteria met.**

### Fixes applied (3)

1. **Route guard** — Wrapped `/admin/security` route with `<RequirePermission permission="admin.security.view">` in `src/router/index.tsx`
2. **i18n hardcoded strings** — Replaced 3 VN strings with i18n keys:
   - `mfa.status` — "Trạng thái:" (line 205)
   - `encryption.status` — "Trạng thái:" (line 281)
   - `erasure.nameMismatch` — "Tên phòng khám không khớp" (line 165)
3. **DialogDescription** — Added `<DialogDescription>` wrapping warning text in TenantErasureModal (fixes Radix a11y warning)

### Test results

- **TypeScript**: 0 errors ✅
- **ESLint**: 0 warnings ✅
- **Tests**: 578 passed (31 in TASK-046 namespace) ✅

### Deliverables

- **Functional Design**: [`docs/tasks/TASK-046/deliveries/final-specs/security-settings-functional-design.md`](./deliveries/final-specs/security-settings-functional-design.md)
- **Review Report**: [`docs/tasks/TASK-046/handoff/review-to-test.md`](./handoff/review-to-test.md)

### Status

**DONE** — Ready for QA testing + merge orchestration (TASK-035, TASK-038, TASK-037-P2 coordination)

---

## Related tasks

- **Upstream**: TASK-038 (MFA FE pages), TASK-037-P2 (Health Check, Erase endpoint, KMS provider), TASK-035 (Sidebar nav)
- **Parallel**: TASK-040+ (other admin settings)

## Labels

`admin-security`, `encryption`, `mfa`, `settings`, `frontend`, `task-046`, `completed`
