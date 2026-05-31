# FE Audit Report — TASK-032

**Date**: 2026-05-01
**Auditor**: FE Audit Agent
**Codebase**: clinic-cms-web (Tauri 2 + React 18 + Vite + TypeScript + Tailwind)
**Compared against**: MediZen Modern design (45 Stitch screens) + function list v1.3

---

## Executive Summary

- **Design system completely off-spec.** Current Tailwind palette is "VISSoft blue" (`#1a6bac`) with Segoe UI font and no radius tokens. MediZen Modern requires Indigo `#6366F1`, Slate `#0F172A`, Plus Jakarta Sans + Inter, and 12/8/6 px radii. Brand string in Login is still `CURA`. Net effect: zero visual conformance with the 45 Stitch screens.
- **Multi-clinic per account (AUTH-018..022) not implemented at all.** Login form still requires `clinic_code` (single-tenant assumption), no post-login "Chọn phòng khám" screen, no Clinic Switcher in topbar, no Profile "Phòng khám của tôi" tab. AuthStore stores a single `clinicId/clinicCode`, no list of accessible clinics, no switch flow.
- **Multi-role merge sidebar (RBAC-015..018) absent.** Sidebar is a flat `NAV_ITEMS` list filtered by individual permissions, with no per-role section dividers, no role chip in avatar, no `applied_role` concept.
- **Cmd+K palette (NAV-001..008) does not exist.** No global keyboard handler, no command palette modal, no sub-mode prefixes, no recent items. Only NAV-008 (breadcrumb) is partially achievable via `react-router`, but no breadcrumb component exists either.
- **Phase D screens largely missing or stubbed.** Forgot password, Patient Profile (8 tabs + AI card + 3-col), Queue Kanban (5-column state machine), BHYT Report tab, Profile multi-tab, Invoice History, AR Aging, full Notifications page, and 4 of the Pharmacy sub-pages (Catalog/PO/Stocktake wizard/Expiry processing) are either absent or implemented as basic single-table CRUD.

---

## Gap Inventory

### A.1 — Design system tokens

- **Current state**:
  - `clinic-cms-web/tailwind.config.js` lines 10–28: only one custom color group `brand` (VISSoft blue `#1a6bac`/`#155788`/`#104364`). No `slate`, `emerald`, `amber`, `red`, `sky` overrides — relies on Tailwind defaults. No `borderRadius` extension. `fontFamily.sans` set to `"Segoe UI", system-ui, ...` — neither Plus Jakarta Sans nor Inter.
  - No `theme.ts` or design-token file in `src/`. `src/styles.css` not inspected but no token export found via grep.
  - All shell components use `text-brand-*` / `bg-brand-*` directly (e.g. `Sidebar.tsx:401,450`, `Topbar.tsx:134`, `LoginPage.tsx:223,236,271,276,377,401`).
  - Login still says brand "CURA" (`LoginPage.tsx:236, 276, 452`).
- **Spec requires**: Indigo `#6366F1` primary, Slate `#0F172A` secondary, Emerald `#10B981`, Amber `#F59E0B`, Red `#EF4444`, Sky `#0EA5E9`, surface white, page bg slate-50, border slate-200. Plus Jakarta Sans (700/600) for headings + Inter (400/500) for body. Roundness: 12px cards / 8px inputs / 6px chips. Spacing 4 px baseline / 24 px gutter. Brand "MediZen".
- **Gap**: CRITICAL
- **Effort**: Medium (token rewrite is surgical, but every `bg-brand-*` / `text-brand-*` reference across the app needs touching for visual parity)
- **Files to touch**: `tailwind.config.js`, `src/styles.css`, `index.html` (font preconnect/link), `src/components/shell/Sidebar.tsx`, `src/components/shell/Topbar.tsx`, `src/pages/auth/LoginPage.tsx`, every page using `brand` token (~40+ files via codebase grep on `brand-`).

### A.2 — App shell layout

- **Current state**:
  - `src/components/shell/AppShell.tsx` (23 lines): `flex h-screen` with `Sidebar` + (`Topbar` + `<Outlet/>`). Page bg `bg-gray-50 dark:bg-gray-900`.
  - `Topbar.tsx`: `h-14` (56 px ✓), contents = clinic-name placeholder ("Clinic CMS" hard-coded line 79) + `OnlineStatusIndicator` + `NotificationsPanel` + language switcher + theme toggle + avatar dropdown. **No Cmd+K search input. No clinic switcher dropdown.**
  - `Sidebar.tsx`: width `w-60` collapsed→`w-16` (240/64 px ✓), bg `bg-gray-900` (slate-900-ish, NOT Indigo accent), uses `text-brand-400` for logo and `bg-brand-500` for active item. Logo is a `Shield` icon + text "Clinic CMS". Static `NAV_ITEMS` array (lines 68–368), no per-role grouping.
- **Spec requires**: Topbar 56 px with logo, ⌘K search input, 🔔 notifications, clinic switcher dropdown, avatar with role chip. Sidebar 240 px Indigo accent, per-role section dividers.
- **Gap**: MAJOR (geometry correct; content + visual treatment wrong)
- **Effort**: Medium
- **Files to touch**: `Topbar.tsx`, `Sidebar.tsx`, `AppShell.tsx`, new `ClinicSwitcher.tsx`, new `CommandPalette.tsx` integration point.

### A.3 — Multi-clinic per account UX (AUTH-018..022)

- **Current state**:
  - `LoginPage.tsx` line 87–92: Zod schema requires `clinic_code: z.string().min(1)`. UI renders Clinic Code field (lines 316–340) with `Building2` icon. The login `POST /api/v1/auth/login` body (lines 145–149) sends `username + password + clinic_code`. This is the OLD single-tenant pattern.
  - `LoginPage.tsx` lines 379–380: "Forgot password" is a `<button>` with no `onClick` handler — dead UI.
  - `authStore.ts` lines 27–52: `AuthState` has scalar `clinicId` + `clinicCode`. No `clinics: Clinic[]`, no `setActiveClinic`, no `defaultClinicId`.
  - No "Chọn phòng khám" screen exists anywhere in `src/pages/auth/` (only `LoginPage` + `ChangePasswordPage`).
  - `Topbar.tsx` lines 73–81: clinic display is hard-coded literal "Clinic CMS" with comment `Clinic name will be resolved from clinic_id in TASK-018`. No clinic switcher dropdown.
  - `/profile` route in `router/index.tsx:533–537` is a `PlaceholderPage name="Profile"` — no Profile page exists, let alone the 5-tab variant with "Phòng khám của tôi".
- **Spec requires**: Login = email + password only (no clinic_code). Post-login: if `clinics.length > 1` and no default, render Clinic-Selector screen. Topbar clinic switcher dropdown 240 px with role chip + "Hiện tại" + footer. Profile page tab "Phòng khám của tôi" with radio set-default. Last-active clinic remembered (Tauri local store).
- **Gap**: CRITICAL
- **Effort**: Large (touches login flow, auth store, router guards, topbar, profile, query cache invalidation on switch)
- **Files to touch**: `LoginPage.tsx`, new `ClinicSelectorPage.tsx`, `authStore.ts`, `Topbar.tsx`, new `components/shell/ClinicSwitcher.tsx`, new `pages/profile/ProfilePage.tsx`, `router/index.tsx`, `lib/apiClient.ts` (active-clinic header), `lib/secureStore.ts` (last-active key).

### A.4 — Multi-role merge sidebar (RBAC-015..018)

- **Current state**:
  - `Sidebar.tsx` lines 68–368: a single static `NAV_ITEMS` array with sub-items, gated only by `RequirePermission permission=...` per item (line 413, 441, 465). There is no role-aware grouping, no `─── Bác sĩ ───` / `─── Quản trị ───` dividers.
  - `authStore.ts` `UserInfo` has `roles: string[] + permissions: string[]` but no logic anywhere uses `roles` to compose sidebar sections — only `permissions[]` are consulted (e.g. `RequirePermission`).
  - No role-switcher exists (good — matches spec), but also no role-grouped UI.
  - No avatar role chip in `Topbar.tsx`. Avatar shows initials only (line 134–137).
  - No `applied_role` concept anywhere — search returned no matches for "applied_role".
- **Spec requires**: Merge sidebar showing UNION of modules across all user roles, with section dividers per role. Avatar shows multi-role chip ("+2") with hover to see role list. Audit logs include `applied_role` (BE concern, but FE may need to send the active section context).
- **Gap**: MAJOR
- **Effort**: Small-Medium (sidebar refactor to group nav by role-membership; topbar avatar enhancement)
- **Files to touch**: `Sidebar.tsx`, `Topbar.tsx`, new `lib/rbac.ts` (role→nav-section mapping), `authStore.ts` (expose role list).

### A.5 — BHYT toggle wiring (CFG-017)

- **Current state**:
  - **Zero references** to `bhyt`, `BHYT`, `bhyt_enabled`, or `clinic.bhyt_enabled` anywhere in `clinic-cms-web/src/` (case-insensitive grep returned no files). No feature flag store, no conditional rendering for any of the 11 UI areas.
  - `SettingsPage.tsx` lines 1–24: Settings has 7 tabs (`general | operatingHours | appointment | queue | inventory | prescription | billing`) — no BHYT tab.
  - `RolesPage` exists; no `BhytConfigPage`. No `/admin/bhyt` route.
  - Reports module has 5 reports (revenue, inventory, doctor performance, visit volume, prescriptions) — no BHYT funnel/sync tab.
  - `InvoiceListPage`, `PendingDispensePage`, `PrescriptionTab`, `PatientRegisterPage` all render unconditionally — no BHYT gating logic visible.
- **Spec requires**: Feature flag `clinic.bhyt_enabled` (default OFF) gates 11 UI areas: Cấu hình BHYT screen, Báo cáo BHYT tab, Tích hợp VSS tab, Bảng giá BHYT column, Tiếp nhận BHYT field, Kê đơn BHYT line, CLS BHYT chỉ định, Hoá đơn BHYT line, plus 3 more. Confirm modal on toggle.
- **Gap**: CRITICAL (entire feature surface area missing)
- **Effort**: Medium-Large (also requires BE flag + middleware; FE must add feature-flag store + 11 conditional renders + new BHYT settings tab + new Report-BHYT tab)
- **Files to touch**: new `stores/featureFlagsStore.ts` or extend `settingsStore.ts`, new `pages/admin/BhytConfigPage.tsx`, new `pages/reports/BhytReportPage.tsx`, `SettingsPage.tsx`, `Sidebar.tsx`, `PatientRegisterPage.tsx`, `PrescriptionTab.tsx`, `InvoiceListPage.tsx`/`InvoiceDetailPage.tsx`, `ServicesPage.tsx` (price column), `MedicinesPage.tsx`, integration page (does not exist yet).

### A.6 — Cmd+K palette (NAV-001..008)

- **Current state**:
  - Grep for `cmd\+k|command.*palette|Ctrl\+K|quickSearch|CommandMenu` returned only `MainDashboardPage.tsx` (which contains a `Search` icon import for a quick-action card) and a test file. **No global keyboard handler, no `<CommandPalette>` modal exists.**
  - No `cmdk` or `kbar` dependency in `package.json` (not directly verified, but no usage found in source).
  - No breadcrumb component anywhere — function list says NAV-008 marked ✅ but FE has no breadcrumb.
- **Spec requires**: Modal palette opened by `Cmd+K`/`Ctrl+K`, search input, sub-modes `/bn /thuoc /inv /rx /lk`, result groups (BN / Thuốc / Tính năng), keyboard nav (↑/↓/Enter), recent items pin, shortcuts cheatsheet on `?`.
- **Gap**: CRITICAL
- **Effort**: Medium
- **Files to touch**: new `components/shell/CommandPalette.tsx`, new `hooks/useGlobalShortcuts.ts`, new `modules/search/api.ts`, `AppShell.tsx`, new `components/shell/Breadcrumb.tsx`.

### A.7 — Stock chip in prescription (RX-016)

- **Current state**:
  - `src/components/doctor/PrescriptionTab.tsx` lines 138–168: search dropdown DOES show a stock indicator per medicine. Uses `med.in_stock` boolean → either green check `"Còn {qty} {unit}"` (line 152–155) or red X `"Hết hàng"` (line 156–161). Stock warning shown when `qty > available` (line 188–191, 274–278).
  - **Missing pieces vs spec**:
    - No "amber/sắp hết" intermediate state (below min reorder threshold) — only binary in-stock/out-of-stock.
    - No HSD (expiry) warning visible (no FEFO/lot info exposed in UI).
    - No tooltip on hover with breakdown by lot.
    - No "Chỉ hiện thuốc còn hàng" filter chip (default ON).
    - No "Đề xuất thuốc tương đương" button when out of stock.
    - "External" type not explicitly excluded from chip (free-text path bypasses, OK).
  - Real-time inventory: relies on `searchMedicines(q)` returning `available` field — staleTime 30s (line 78). Acceptable but not "real-time".
- **Spec requires**: Three-state chip (emerald "Còn 320 viên" / amber "Còn 12 viên" below min / red "Hết hàng — đề xuất thay thế") + lot tooltip with FEFO + HSD + filter chip + substitute-suggestion link.
- **Gap**: MAJOR (basics present; spec depth missing)
- **Effort**: Small-Medium
- **Files to touch**: `PrescriptionTab.tsx`, `modules/doctor/types.ts` (add `min_stock_level`, `lots[]` to Medicine type), `modules/doctor/api.ts`.

### A.8 — EMR tabs count

- **Current state**:
  - `src/pages/doctor/ConsultationPage.tsx` lines 33, 179–183: `TabId = "vitals" | "services" | "prescription" | "notes"` — **4 tabs only**: Sinh hiệu / Dịch vụ / Kê đơn / Ghi chú. Tab components in `components/doctor/`: `VitalsTab`, `ServicesTab`, `PrescriptionTab`, `NotesTab`.
  - PatientDetailPage has 7 history tabs (info / guardian / visits / prescriptions / invoices / vitals / audit) — those are patient-master tabs, NOT EMR-visit tabs (different page).
- **Spec requires**: EMR detail = 6 tabs per `MENU_AND_SCREENS.md` (Sinh hiệu, Khám LS S.O.A.P, Chẩn đoán, Kê đơn, CLS, Tóm tắt). Audit prompt mentions 8 tabs (adds "Tổng quan" + "AI gợi ý" or "Lịch sử BHYT").
- **Gap**: CRITICAL — current 4 tabs missing: Khám lâm sàng (S.O.A.P), Chẩn đoán (ICD-10), Cận lâm sàng (CLS / lab orders), Tóm tắt & Hoàn tất, plus optional Tổng quan + AI Gợi ý + Lịch sử BHYT.
- **Effort**: Large (each new tab is a real form with API wiring)
- **Files to touch**: `ConsultationPage.tsx`, new `components/doctor/SoapTab.tsx`, `DiagnosisTab.tsx`, `LabOrdersTab.tsx`, `SummaryTab.tsx`, `AiSuggestionsTab.tsx` (optional), `BhytHistoryTab.tsx` (gated), corresponding `modules/doctor/api.ts` extensions.

### A.9 — Phase D screens missing/incomplete

| # | Screen | Current FE state | Gap |
|---|---|---|---|
| 1 | Quên mật khẩu (forgot password) | "Forgot password" button in `LoginPage.tsx:375–381` has no `onClick`. No `/forgot-password` route. No `ForgotPasswordPage.tsx`. | CRITICAL — missing entirely |
| 2 | Danh sách Bệnh nhân (master list) | `PatientListPage.tsx` exists (search + table). No dedicated filter chips (gender/age/last-visit), no pagination UI (`limit:50` hard-cap), no advanced filter panel. | MINOR — basic list works; spec depth missing |
| 3 | Hồ sơ BN chi tiết (8 tabs + AI + 3-col) | `PatientDetailPage.tsx` has 7 tabs but 4 are STUBs (`HISTORY_TABS = ["visits","prescriptions","invoices","vitals"]` line 20 — all rendered as placeholder). Single column layout, no AI gợi ý card, no 3-col layout. | MAJOR — exists but wrong design + 4 stubs |
| 4 | Phòng chờ Kanban (5 cột state machine) | `QueueBoardPage.tsx` shows 3 columns: WAITING / IN_PROGRESS / AWAITING_PAYMENT. Spec wants 5-column state machine. | MAJOR — geometry wrong |
| 5 | Báo cáo BHYT tab | Not present. Reports module has 5 tabs, no BHYT funnel chart. | CRITICAL (gated by CFG-017 anyway) |
| 6 | Profile cá nhân (5 tabs) | `/profile` route uses `PlaceholderPage` (`router/index.tsx:533–537`). | CRITICAL — missing entirely |
| 7 | Billing — Lịch sử hoá đơn | `InvoiceListPage.tsx` exists with status filter + search. Acceptable as invoice history list, but no dedicated "by patient timeline" view. | MINOR |
| 8 | Billing — Công nợ AR aging | Grep for "aging\|0-30\|31-60\|AR" returned nothing. No `ARAgingPage`, no buckets. | CRITICAL — missing entirely |
| 9 | Notifications full page | `NotificationsPage.tsx` (231 lines) exists with type/severity/read filters + mark-read mutation. Missing: bulk actions, pagination, date range filter. | MINOR |
| 10 | Pharmacy 4 sub | Existing: `PendingDispensePage`, `SubstituteBatchPage`, `InventoryPage`, `AdjustmentsPage`, `PurchaseInPage`. Spec wants: Danh mục thuốc (admin/medicines exists), Nhập kho PO (PurchaseInPage exists), Kiểm kê wizard 3-step, Xử lý hết hạn 30/60/90d. **Missing**: 3-step stocktake wizard, expiry-disposal screen. `AdjustmentsPage` is single-form, not a wizard. No expiry view. | MAJOR — 2 of 4 missing/wrong shape |

### A.10 — i18n vi/en completeness

- **Current state**: `src/locales/vi/` has 13 namespaces totalling **1827 lines** (admin 477, billing 197, hr 173, doctor 168, pharmacy 208, reception 221, reports 115, dashboard 34, notifications 42, auth 48, shell 31, common 23, validation 7).
  - `vi/auth.json`: only login + change-password keys. **No keys for**: forgot password, OTP, clinic-selector screen.
  - `vi/shell.json`: only nav labels for 8 modules + topbar/sidebar generics. **No keys for**: cmd-k palette, clinic switcher, breadcrumb, role chip.
  - `vi/dashboard.json`: only 34 lines — likely only the original main-dashboard KPIs. **No multi-role variants** keys for 5 role dashboards.
  - No namespace files for: `profile.json`, `commandPalette.json`, `clinicSwitcher.json`, `bhyt.json`, `forgotPassword.json`, `clinicSelector.json`.
- **Spec requires**: 45 Stitch screens worth of strings (≥40% expansion needed).
- **Gap**: MAJOR
- **Effort**: Medium (mechanical but scope is large)
- **Files to touch**: all `locales/vi/*.json` + parallel `locales/en/*.json` + new namespace files.

---

## Cross-cutting findings

1. **Brand identity drift**: Code references "CURA" + "Clinic CMS" + "VISSoft blue" simultaneously. The new spec calls for "MediZen" branding with Indigo accent. A global rename pass + asset swap is needed alongside token migration (A.1).
2. **`PlaceholderPage` surface**: `/settings`, `/profile` routes (router/index.tsx:524–538) silently fall back to placeholder. These never tripped a 404 test and never showed up as gaps — they should become real pages or be explicitly removed.
3. **AuthStore single-tenant assumption is leaking everywhere**: scalar `clinicId/clinicCode` is referenced by `Topbar.tsx:37`, `setClinicContext`, secureStore TOKEN_KEYS. A multi-clinic refactor will ripple through API client (need `X-Active-Clinic` header), all React-Query keys (must include clinic_id for cache isolation), and the Tauri-side secure store.
4. **No feature-flag infrastructure**: `settingsStore.ts` only holds `theme + language`. Adding BHYT toggle (A.5), telehealth, emergency, etc. will need a generic `featureFlagsStore` hydrated from `GET /clinics/{id}/settings` post-login.
5. **No global keyboard layer**: `CommandPalette` (A.6), shortcuts cheatsheet (NAV-007), and any future `Esc-to-close` / `Ctrl+S` handlers all need a single `useGlobalShortcuts` hook + provider mounted at `AppShell` level.
6. **EMR vs Patient-detail tab confusion**: The 7-tab `PatientDetailPage` is patient-master oriented (Info, Guardian, History). The 4-tab `ConsultationPage` is the per-visit EMR. Spec calls for 8 tabs on the EMR side; these are different pages and should not be conflated.
7. **Recharts already a dependency**: dashboards use Recharts (Bar, Line). Reusable for AR Aging buckets, BHYT funnel, etc.
8. **React-Query everywhere — good foundation**: cache invalidation for clinic switch (AUTH-021) can be done with one `queryClient.clear()` call, but every page must remember to scope keys.
9. **Tauri secureStore present but underused for multi-clinic**: TOKEN_KEYS only knows ACCESS/REFRESH/USER/CLINIC_ID/CLINIC_CODE. Need `LAST_ACTIVE_CLINIC`, `RECENT_SEARCH_ITEMS`, `FEATURE_FLAGS_CACHE`.
10. **Dark mode is class-based already** (`darkMode: 'class'`) — token rewrite must keep dark variants for every new color. None of the 45 Stitch screens have been audited for dark variants.

---

## Recommended cluster sub-tasks

Group the 30+ gaps into 7 sub-tasks (FE-only; BE counterparts are a separate audit):

### Cluster 1 — TASK-039 (proposed): Design system token port + brand rename
**Scope**: A.1 (tokens) + cross-cutting #1 (brand). Rewrite `tailwind.config.js` with full MediZen palette + radii + fonts. Add `index.html` font links (Plus Jakarta Sans 600/700 + Inter 400/500). Replace every `brand-*` Tailwind class with new Indigo equivalents (codemod). Rename "CURA" / "Clinic CMS" → "MediZen". Update `Sidebar` background to Indigo accent.
**Effort**: Medium · **Priority**: Highest (blocks visual conformance for all other work)

### Cluster 2 — TASK-033 (proposed): Multi-clinic per account (AUTH-018..022)
**Scope**: A.3 + cross-cutting #3. Remove `clinic_code` from Login. Build `ClinicSelectorPage`. Refactor `authStore` to hold `clinics: Clinic[]` + `activeClinicId`. Build `ClinicSwitcher` topbar dropdown. Build `ProfilePage` skeleton with "Phòng khám của tôi" tab. Wire `apiClient` to send `X-Active-Clinic`. Clear React-Query cache on switch. Persist last-active in Tauri secure store.
**Effort**: Large · **Priority**: Highest (FE blocked until BE multi-clinic ready)

### Cluster 3 — TASK-035 (proposed): Multi-role merge sidebar + role chip
**Scope**: A.4. Refactor `Sidebar.tsx` to group nav-items by role-section with dividers. Add multi-role chip to `Topbar` avatar with hover popover. Add `applied_role` context indicator (which section the user is currently acting under).
**Effort**: Small · **Priority**: High

### Cluster 4 — TASK-034 (proposed): BHYT toggle wiring (CFG-017)
**Scope**: A.5 + cross-cutting #4. Add `featureFlagsStore`. Wire 11 UI conditional renders (Settings tab, Reports tab, integrations tab, price column, reception field, Rx line, lab orders, invoice line + 3 more). Build new `BhytConfigPage` and `BhytReportPage`. Add confirm modal for toggle.
**Effort**: Medium-Large · **Priority**: High (depends on Cluster 1 + BE flag)

### Cluster 5 — TASK-036 (proposed): Cmd+K Quick Search + global shortcuts (NAV-001..008)
**Scope**: A.6 + cross-cutting #5. Build `CommandPalette` modal, `useGlobalShortcuts` provider, sub-mode router (`/bn /thuoc /inv /rx /lk`), recent-items persistence, breadcrumb component, shortcut cheatsheet modal.
**Effort**: Medium · **Priority**: Medium

### Cluster 6 — TASK-040 (proposed): Phase D screen port (8 screens)
**Scope**: A.9 (#1, #3, #4, #6, #8) + the missing screens. Build: ForgotPasswordPage, refactor PatientDetailPage to 8-tab + 3-col + AI card, refactor QueueBoardPage to 5-column Kanban, real ProfilePage 5-tab, ARAgingReportPage, complete NotificationsPage with bulk + pagination, Pharmacy Stocktake 3-step wizard, Pharmacy Expiry-disposal screen.
**Effort**: Large · **Priority**: Medium (after Clusters 1–4)

### Cluster 7 — TASK-042 (proposed): EMR 8-tab refactor + RX-016 stock chip enhancements
**Scope**: A.7 + A.8. Refactor `ConsultationPage` to 8 tabs (add SoapTab, DiagnosisTab, LabOrdersTab, SummaryTab, AiSuggestionsTab, BhytHistoryTab). Upgrade PrescriptionTab stock chip to 3-state amber/red/green + lot tooltip + filter chip + substitute-suggest button.
**Effort**: Large · **Priority**: Medium (depends on BE EMR endpoints + Cluster 4 BHYT for tab gating)

### Cluster 8 — TASK-043 (proposed, optional): i18n expansion + en parity
**Scope**: A.10. Add namespaces for profile, commandPalette, clinicSwitcher, bhyt, forgotPassword, clinicSelector. Backfill keys for 45 Stitch screens. Mirror in `en/`.
**Effort**: Medium · **Priority**: Low (can be incremental per cluster)

---

**End of FE Audit Report**
