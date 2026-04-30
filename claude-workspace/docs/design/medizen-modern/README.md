# MediZen — Modern · Design Documentation

Tài liệu design hoàn chỉnh cho phiên bản **"MediZen — Modern"** — một bản UI hiện đại, role-aware cho hệ thống quản lý phòng khám đa khoa MediZen.

**Stitch project (NEW — TASK-029/031)**: https://stitch.withgoogle.com/projects/2542650746708884228 — **45/47 màn canonical ✓** (~96%) với MediZen Modern design system (clean, không còn "Cura" branding)
**Stitch project (OLD — deprecated)**: https://stitch.withgoogle.com/projects/5572301228665717471
**Cập nhật**: 2026-05-01 (TASK-031 partial DONE — 45/47 canonical, 2 màn `blocked-stitch-api` (Billing AR aging + Notifications), 12 duplicates cần cleanup manual. Xem [MEDIZEN_FRESH_PROJECT.md](MEDIZEN_FRESH_PROJECT.md))

---

## 📁 Cấu trúc thư mục này

| File | Mục đích |
|---|---|
| [README.md](README.md) | Index (file này) |
| [SITEMAP.md](SITEMAP.md) | Sitemap toàn hệ thống + ma trận quyền theo vai trò + flow path BN |
| [MENU_AND_SCREENS.md](MENU_AND_SCREENS.md) | **Sườn menu chi tiết theo role + spec từng màn hình** — gồm pre-login flow, app shell, sidebar mỗi role, screen catalog 40+ màn |
| [MULTI_ROLE_UX.md](MULTI_ROLE_UX.md) | UX pattern cho user kiêm 2-3 vai trò (merge sidebar) |
| [ACTION_FLOWS.md](ACTION_FLOWS.md) | 7 flow nghiệp vụ chi tiết step-by-step (tiếp nhận, đo vital, EMR, cấp thuốc, ...) |
| [TAB_MATRIX.md](TAB_MATRIX.md) | Spec tất cả tab của EMR (6) + Cấu hình (8) + Báo cáo (6) — input cho generation Phase C |
| [LANDING_PAGE.md](LANDING_PAGE.md) | **Thiết kế landing page** — 12 sections (hero · problem · solution · comparison · workflow · pricing · testimonials · FAQ · signup form · footer) + animations + form spec + SEO + A/B test ideas |
| [landing-mockup.html](landing-mockup.html) | **Mockup landing page (TASK-028)** — single-file HTML high-fidelity, 694 dòng, render đủ 12 sections theo `LANDING_PAGE.md`, design tokens MediZen Modern, responsive 3 breakpoints, FAQ accordion + scroll reveal animations. Mở trực tiếp trong browser hoặc paste vào Stitch project làm reference. |
| [SECURITY.md](SECURITY.md) | **Security & sensitive data spec** — Phân loại 4-tier · PII inventory ~30 cols · 3 lớp encryption · Per-tenant key + crypto-shred · PII lifecycle · Audit hash chain · Anomaly detection · Threat model STRIDE · Compliance HIPAA + Nghị định 13 |
| [MEDIZEN_FRESH_PROJECT.md](MEDIZEN_FRESH_PROJECT.md) | **Canonical screen ID mapping** cho fresh Stitch project `2542650746708884228` — 45/47 canonical ✓ + 2 blocked-stitch-api + 12 duplicates cleanup notes |

---

## 🎨 Design system "MediZen Modern"

| Token | Giá trị |
|---|---|
| **Primary** | Indigo `#6366F1` |
| **Secondary** | Slate `#0F172A` |
| **Tertiary (status OK)** | Emerald `#10B981` |
| **Warning** | Amber `#F59E0B` |
| **Danger** | Red `#EF4444` |
| **Info** | Sky `#0EA5E9` |
| **Surface** | White `#FFFFFF` |
| **Page bg** | Slate-50 `#F8FAFC` |
| **Border** | Slate-200 `#E2E8F0` |
| **Heading font** | Plus Jakarta Sans (700 / 600) |
| **Body font** | Inter (400 / 500) |
| **Roundness** | 12px (cards) / 8px (inputs) / 6px (chips) |
| **Spacing unit** | 4px baseline · 24px gutter |

Chi tiết design tokens xem trong **Stitch design system asset** `assets/12787757101558093729`.

---

## 🗂️ 45 màn canonical (project mới `2542650746708884228`)

> Bảng dưới list canonical screen IDs. Xem chi tiết và 12 duplicates cần cleanup trong [MEDIZEN_FRESH_PROJECT.md](MEDIZEN_FRESH_PROJECT.md).

### 🔐 Auth & Onboarding (3)
- Đăng nhập — `10fa1b88fcb14939b196120c068b4359`
- Chọn phòng khám (multi-clinic) — `a24a76fa86c34ab4bd29280e3f8a673d`
- Quên mật khẩu — `e7d8a31dfb64457dbb1065168111ae01`

### 🏠 Dashboards per-role (5) + Multi-role (1)
- Dashboard Lễ tân — `08884cb4dda34c2a94b0d0859ead80c3`
- Dashboard Điều dưỡng — `2048c96803b942ce9a327a6b8fb5eca8`
- Dashboard Bác sĩ — `a1da59d6c00e4a0186408c134d0a7bc1`
- Dashboard Dược sĩ — `e22f743e588d476a935e06e6a7bead0d`
- Dashboard Quản trị — `0107aedca56b4e86a10034239dbee630`
- **Dashboard Multi-role (Tổng quan)** — `18ed36db80964e6c9f32ac367163cb6f`

### 🏥 Clinical workflow (4) + 1 bonus
- Tiếp nhận & Đăng ký BN — `c192150a9ca44949b2ae7bff71268055`
- Lịch hẹn (calendar tuần) — `d4a26b27a53f4627a759d4a47be5ef64`
- *(bonus)* Quản lý lịch hẹn (list/management view) — `f9728dac61f44dbd9118ff79e2819f0b`
- Phòng chờ Kanban (5 cột state machine) — `b29cce2159544b148ca95def7ffd36ac`
- Kho thuốc & Cấp phát — `d1f07ac3a95d447f89a9324dd6dad740`

### 🩺 EMR — Chi tiết lượt khám (6 tab)
- EMR Tab 1 — Sinh hiệu — `7099e99ae3f54df7a109f9c1b1e2de3c`
- EMR Tab 2 — Khám LS (S.O.A.P) — `b65f72edaff34c588183ec43bcfa4020`
- EMR Tab 3 — Chẩn đoán — `f7a8a34921584dc8a40fb8d690b975b4`
- EMR Tab 4 — Kê đơn thuốc (stock chip RX-016) — `e09e91adb049450ebb842dfe3a84339b`
- EMR Tab 5 — Cận lâm sàng (CLS) — `1c8dc9a45b4646ca93b743e76cb7fd5c`
- EMR Tab 6 — Tóm tắt & Hoàn tất — `1ffdbfe6457a4b0bbc1319f338b16656`

### 👤 Patient Master (2)
- Danh sách Bệnh nhân — `4e751f21216f4d57914c09e909ebeeef`
- Hồ sơ BN — Lê Hà Vy (3-col, 8 tabs, AI gợi ý) — `2d438ac0dfb04bdc83e41ec0b29bc7d9`

### 💰 Billing (2/3 — 1 blocked)
- Thanh toán Hoá đơn — `6c560c9159bd492a93f81a040fc081ff`
- Lịch sử hoá đơn — `e4089713951341d18ca200d33e2bbc66`
- ⚠️ **Công nợ AR aging** — blocked-stitch-api

### 💊 Pharmacy (5)
- Kho thuốc & Cấp phát — `d1f07ac3a95d447f89a9324dd6dad740`
- Danh mục thuốc — `59d0a9320fd84fd2a281cff113657d95`
- Tạo phiếu nhập kho (PO) — `3cb03ffce4ea4f739cbe1f82576b349b`
- Kiểm kê thực tế (3-step wizard) — `8ed40f5e4cf54108adf4fe0d59b0048d`
- Xử lý hết hạn (30/60/90d) — `9c07546bdc214e499f3af5db011b2249`

### ⚙️ Cấu hình hệ thống (8 section)
- Phòng khám & Chi nhánh (toggle BHYT default OFF) — `cf5b5eaa419a469591f378d8756dc1c4`
- Vai trò & Phân quyền (RBAC) — `db783faa5ee44d5fa7a4495c4640151a`
- Ca trực & Giờ làm — `c37cf2c381c44368aed26bc6f03c9116`
- Bảng giá dịch vụ — `149093160f354daaa28ba80046bc8f19`
- BHYT (mức hưởng + DM) — `1a8f4df42c844078ba28ad915ccc87e8`
- Tích hợp (VSS/HL7/DICOM/SMS) — `9b5d4a26e1ff42368a64721ef9d1c95e`
- Audit log — `c13abb5084b946e7ae1ba3ae56c32df2`
- Bảo mật & Mã hoá (PII inventory + Anomaly + Hash chain) — `c8547b82621c4c0ca4abb8a4e3a2f149`

### 📊 Báo cáo & Thống kê (6 tab)
- Tab Tổng quan — `0edb38245675437a9b9eeca7b5cdf91c`
- Tab Tài chính — `af50d7704ee34c6d9589438b51ac1e0e`
- Tab Lâm sàng — `7673357fad4b4c468b4eefa51d100f98`
- Tab Vận hành — `e3fdaab8c9514a0291c2e1ee0c7945bd`
- Tab Dược — `b98d3d7a78c643d69f7474d71f2d926b`
- Tab BHYT (funnel duyệt + top từ chối + sync VSS) — `0b6214575af0401a8f8b96402e3c0d70`

### 🪟 Modals & Popovers (2)
- ⌘K Quick Search Palette (mode `/bn /thuoc /inv /rx /lk`) — `3812ba7a5ff8430890011daceafd3343`
- Clinic Switcher Dropdown — `af58042597394694a83eebec6c3d5ff1`

### 👤 Profile Multi-tab (1)
- Profile cá nhân — BS. An (5 tabs với "Phòng khám của tôi" + 3 PK card + radio default) — `18d1ec870224423c8b50717aeb957bd3`

### 🔔 Notifications (0/1 — blocked)
- ⚠️ **Trung tâm Thông báo** — blocked-stitch-api

### ⚠ Cleanup pending — 12 duplicates trong project mới
Xem [MEDIZEN_FRESH_PROJECT.md §3](MEDIZEN_FRESH_PROJECT.md#3-cleanup-notes--12-duplicates-trong-project-mới-cần-xoá-thủ-công) — danh sách 12 IDs cần xoá manual qua Stitch UI (Auth dups: 2 · Patient: 4 · Queue: 2 · Settings: 2 · Reports: 1 · Modals: 1).

---

## 🚀 Cách sử dụng tài liệu này

### Cho **Designer** xem mock:
1. Mở [Stitch project (NEW MediZen Modern 45/47)](https://stitch.withgoogle.com/projects/2542650746708884228)
2. Đọc [SITEMAP.md](SITEMAP.md) để hiểu cấu trúc tổng thể
3. Đọc [TAB_MATRIX.md](TAB_MATRIX.md) cho spec từng tab

### Cho **PO/BA** review nghiệp vụ:
1. Đọc [ACTION_FLOWS.md](ACTION_FLOWS.md) để check flow nghiệp vụ
2. Đọc [SITEMAP.md](SITEMAP.md#2-ma-trận-hiển-thị-module-theo-vai-trò) ma trận quyền
3. Confirm với team y tế xem flow có đúng thực tế không

### Cho **FE Developer** implement:
1. Đọc [MULTI_ROLE_UX.md](MULTI_ROLE_UX.md#7-implementation-hint-cho-fe-clinic-cms-web) implementation hints
2. Lấy design tokens từ Stitch design system → port sang `tailwind.config.js`
3. Generate component skeleton từ Stitch HTML → React/Tailwind

### Cho **BE Developer** đảm bảo permission:
1. Đọc [SITEMAP.md](SITEMAP.md#2-ma-trận-hiển-thị-module-theo-vai-trò) ma trận quyền
2. Map mỗi cell với permission code trong `app/modules/users/`
3. Đảm bảo route gating trên FastAPI khớp với UI hide/disable

---

## 🚩 Feature flags

| Flag | Default | Mô tả | Vùng UI ảnh hưởng |
|---|---|---|---|
| `clinic.bhyt_enabled` | **OFF** | Bật/tắt mọi tính năng liên quan BHYT | Cấu hình BHYT · tab Báo cáo BHYT · tab VSS trong Tích hợp · cột BHYT trong Bảng giá · ô BHYT trong Tiếp nhận · dòng BHYT trong Kê đơn/CLS/Hoá đơn — xem [TAB_MATRIX.md §Feature flag](TAB_MATRIX.md#feature-flag-toàn-cục-bhyt-bậttắt) |
| `clinic.emergency_enabled` | ON | Cho phép luồng Cấp cứu (red queue, FAST registration) | Triage button trong Tiếp nhận · queue badge "Cấp cứu" |
| `clinic.telehealth_enabled` | OFF | Tương lai — đang reserve | Khi ON sẽ hiện thêm Lịch hẹn online + EMR remote |

Toggle ở **Cấu hình → Phòng khám → Tab Thông tin → Section "Tính năng"**. Quản trị có quyền sửa.

---

## 📌 Liên quan

- [PROJECT.md](../../../PROJECT.md) — Workspace config (RBAC, tech stack)
- [docs/tasks/](../../tasks/) — Task tracking
- [Project Stitch gốc "MediZen SaaS Platform Architecture"](https://stitch.withgoogle.com/projects/5851786557170020581) — phiên bản trước (giữ làm reference)
