# TASK-053 — UI/UX Audit: FE (clinic-cms-web) đối chiếu MediZen Modern/Pro

> **Ngày**: 2026-05-30 · **FE**: `clinic-cms-web` @ `main` (Vite dev `:1420`) · **BE**: `clinic-cms-merge` (API `:8001`, alembic `0036_super_admin`)
> **Phương pháp**: đối chiếu route/màn hình đã implement với design spec `docs/design/medizen-modern/` (SITEMAP, MENU_AND_SCREENS, TAB_MATRIX, MULTI_ROLE_UX, ACTION_FLOWS) + `medizen-pro/` (DESIGN, SCREENS). Trạng thái: **ĐẠT** / **THIẾU** / **LỆCH**.
> **Lưu ý**: phần này dựa trên đọc code (static). Screenshot runtime sẽ bổ sung ở bước sau (Playwright).

---

## 1. Tổng quan kết quả

| Chiều đánh giá | Kết quả | Ghi chú |
|---|---|---|
| Route coverage | ✅ ~95% | 55/57 route có implement; 2 placeholder (Security settings, AR route lệch chỗ) |
| Stitch screens (Phase B+C) | ✅ ~90% | 32/32 màn Phase B+C xong; Phase D (~16 màn) route đã có |
| EMR tab matrix | ⚠️ 6/6 + 1 extra | 6 tab spec + tab "notes" giữ lại cho backward-compat (TASK-042). **Cần verify thứ tự tab Kê đơn vs CLS** |
| Patient detail tabs | ✅ 8/8 | overview·info·guardian·visits·prescriptions·invoices·vitals·bhyt |
| Settings tabs | ⚠️ ~90% | 7+1 tab; **BHYT & Security** thiếu route tường minh |
| Reports tabs | ⚠️ ~60% | Revenue + BHYT routed; Financial/Clinical/Operational/Pharmacy under-routed (spec = 6 tab/1 trang vs impl = 7 route rời) |
| Profile tabs | ✅ ~95% | 5 tab; "info"/"notifications" còn stub |
| Sidebar multi-role | ✅ ~90% | `groupNavByRole()` + multi-role dashboard có; cần verify divider |
| Typography | ✅ 100% | base 15px, Inter body + Sora display, tabular-nums (khớp TASK-051) |
| i18n | ✅ 100% | vi default + en; 32 file locale |
| Color palette | ✅ 100% | Teal primary + semantic + dark mode CSS vars |
| Loading/Empty/Error | ✅ ~85% | React Query + `PendingBEState` + empty placeholders |
| Responsive | ⚠️ desktop-first | Tailwind grid; không có mobile-specific (đúng spec ≥1440px) |
| Permissions/Guards | ✅ 100% | `RequireAuth` + `RequirePermission` |
| Printing/Export | ✅ ~85% | Print modal Rx/Invoice/Lab/Summary (TASK-047/051) |

---

## 2. Route inventory (55/57 route có implement)

Router: `src/router/index.tsx` (~720 dòng). Page components: `src/pages/**`.

**Auth (public)**: `/login` · `/forgot-password` · `/change-password` · `/auth/select-clinic` · `/auth/mfa/verify` · `/auth/mfa/enroll` — tất cả ✅.
**Dashboard**: `/` → `/dashboard` (role-aware) · `/dashboard/multi-role` ✅.
**Onboarding**: `/onboarding` (ngoài AppShell) ✅.
**Patients/Reception**: `/patients` · `/patients/new` · `/patients/:id` (8 tab) · `/patients/merge` · `/appointments` · `/queue` · `/reception`→`/patients` ✅.
**Doctor/EMR**: `/doctor`→`/doctor/queue` · `/doctor/queue` · `/doctor/visits/:id` (7 tab) · `/doctor/dashboard` ✅.
**Pharmacy**: `/pharmacy/pending` · `/substitute` · `/inventory` · `/adjustments` · `/purchase-in` · `/stocktake` · `/expiry` ✅.
**Billing**: `/billing`→`/billing/invoices` · `/billing/invoices` · `/billing/invoices/:id` · `/billing/invoice/new[/:visit_id]` ✅.
**HR**: `/hr/schedule` · `/recurring` · `/shift-templates` · `/leave/new` · `/leave/approve` · `/me/timelog` · `/attendance/export` ✅.
**Admin**: `/admin/users` · `/users/:id/extra-permissions` · `/roles` · `/settings` (7+1 tab) · `/vitals` · `/services` · `/medicines` · `/audit` · `/integrations/vss` · `/integrations/vss/log` ✅.
**Reports**: `/reports/revenue` · `/inventory` · `/doctor-performance` · `/visit-volume` · `/prescriptions` · `/ar-aging` · `/bhyt` ✅.
**Khác**: `/profile` (5 tab) · `/notifications` · `/settings` (PlaceholderPage) · `*`→`/dashboard`.

---

## 3. Gap matrix — các điểm THIẾU / LỆCH (cần action)

| # | Màn hình | Route hiện tại | Spec ref | Status | Chi tiết |
|---|---|---|---|---|---|
| G1 | **Bảo mật & Mã hoá** (settings) | (không có route) | TAB_MATRIX §B.7 | **THIẾU** | Spec yêu cầu section "Bảo mật & Mã hoá" trong Cấu hình; không tìm thấy route/component. *(Lưu ý: TASK-046 có làm security settings panels — cần verify đã wire route chưa)* |
| G2 | **BHYT config** (mức hưởng + DM) | (không có route tường minh) | TAB_MATRIX §B.4 | **THIẾU** | `BhytConfigPage` tồn tại nhưng chưa expose route; nên `/admin/bhyt` hoặc `/admin/settings?tab=bhyt` |
| G3 | **Công nợ BN (AR aging)** | `/reports/ar-aging` | MENU_AND_SCREENS §D7.3 | **LỆCH** | Spec đặt ở module Billing (`/billing/ar`); impl đặt ở Reports |
| G4 | **Tích hợp** (HL7/DICOM/SMS/Webhook) | chỉ `/admin/integrations/vss` | TAB_MATRIX §B.5 | **LỆCH** | Spec liệt kê nhiều tab tích hợp; impl chỉ có VSS + log |
| G5 | **Reports tab structure** | 7 route rời | TAB_MATRIX §C | **LỆCH** | Spec = 1 trang Báo cáo / 6 tab (Tổng quan·Tài chính·Lâm sàng·Vận hành·Dược·BHYT). Impl = route rời, thiếu trang hub tab. Cần chốt: consolidate hay spec outdated |
| G6 | **EMR tab order** (Kê đơn vs CLS) | `/doctor/visits/:id` | TAB_MATRIX §A | **LỆCH?** | Code có cả `prescription` (Pill) + `services` (Flask) tab; thứ tự Tab4 "Kê đơn" vs Tab5 "CLS" cần verify khớp spec |
| G7 | **EMR tab "notes"** (thứ 7) | `/doctor/visits/:id#notes` | TASK-042 | **LỆCH (chủ ý)** | Spec 6 tab; impl giữ tab 7 backward-compat theo quyết định TASK-042 — chấp nhận được, ghi nhận |
| G8 | **Profile "info" + "notifications"** | `/profile` | MENU_AND_SCREENS §D10 | **LỆCH (stub)** | Tab tồn tại nhưng nội dung còn stub |
| G9 | **Settings root** | `/settings` | — | **THIẾU (placeholder)** | `/settings` render `PlaceholderPage` (chưa chi tiết) |
| G10 | Multi-role edge cases | (global) | MULTI_ROLE_UX §5 | **THIẾU** | Soft-logout khi mất role giữa phiên, indicator "NEW" role mới, collapsible group — chưa thấy trong code |

> Các màn còn lại trong spec (Auth, Dashboard role-aware, Patient detail 8 tab, Pharmacy 6 màn, Billing core, HR, RBAC, Audit, Command palette, Clinic switcher, Notifications) → **ĐẠT**.

---

## 4. Design-system observations

- **Typography** ✅: base 15px / leading-6, Inter (body) + Sora (display, `font-display`), `.tnum` tabular-nums. Khớp DESIGN.md + TASK-051.
- **i18n** ✅: 32 namespace `src/locales/{vi,en}/`, vi default. Mọi module chính có file dịch.
- **Color** ✅: brand teal `600:#00685f` (spec primary-600), semantic emerald/amber/rose/sky, dark mode `class` + CSS vars. Legacy indigo còn giữ cho giai đoạn rollout.
- **Components** ✅: bộ ui mới (`field`, `form-grid`, `form-section`, `segmented-control`, `sticky-form-actions`, `textarea`) — chuẩn hoá form layout theo DESIGN §6.
- **States** ⚠️ ~85%: React Query `isLoading/isError`, `PendingBEState`, `DevPlaceholder` cho feature đang dev, empty `py-12 text-center`. Chưa exhaustive.
- **Feature flag BHYT** ⚠️ ~85%: `useFeatureFlag` + gating ở dashboard/reports/settings. **Chưa verify đầy đủ** gating ở EMR (Tab4/5/6), Billing (phân bổ BHYT), Patient register (field số thẻ).

---

## 5. Khuyến nghị (tách follow-up — KHÔNG implement trong task này)

1. **[G1/G2]** Wire route cho Security settings + BHYT config (verify TASK-046 đã làm panel chưa) → follow-up FE.
2. **[G5]** Chốt với user: Reports gom về 1 trang 6 tab hay giữ 7 route rời (cập nhật spec nếu giữ).
3. **[G6]** Verify thứ tự EMR tab Kê đơn/CLS khớp TAB_MATRIX (chỉ cần đổi order nếu lệch).
4. **[G3]** Cân nhắc thêm alias `/billing/ar` → ARAgingReportPage.
5. **[G4]** Tích hợp: ghi rõ HL7/DICOM/SMS là backlog (chưa có BE) — xem functional-audit.md.
6. **[G8/G9]** Hoàn thiện Profile info/notifications + Settings root.
7. **[G10]** Multi-role soft-logout + role-change indicator (UX edge case).
8. **Runtime verify**: chụp screenshot từng màn qua Playwright để xác nhận visual khớp Stitch design (bước kế tiếp của task này).

---

*Nguồn dữ liệu: Explore agent đọc `src/router/index.tsx`, `src/pages/**`, `src/components/shell/Sidebar.tsx`, `src/lib/rbac.ts`, `src/locales/**`, `tailwind.config.js`, `src/styles.css` + design spec. Cần verify runtime ở bước screenshot.*
