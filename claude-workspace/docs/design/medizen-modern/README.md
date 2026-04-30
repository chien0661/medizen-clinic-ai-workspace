# MediZen — Modern · Design Documentation

Tài liệu design hoàn chỉnh cho phiên bản **"MediZen — Modern"** — một bản UI hiện đại, role-aware cho hệ thống quản lý phòng khám đa khoa MediZen.

**Stitch project**: https://stitch.withgoogle.com/projects/5572301228665717471
**Cập nhật**: 2026-04-30 (Phase B + C done — 32 màn)

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

## 🗂️ 32 màn (Stitch — đã đủ)

### 🔐 Auth (1)
- Đăng nhập — `e98de272bc7249f39f9a233c7adb17f2`

### 🏠 Dashboards per-role (5) + Multi-role (1)
- Dashboard Lễ tân — `e8ec8790c76f4a04b42400c78f3e934a`
- Dashboard Điều dưỡng — `416445275b17462e87c4dd6f29d42106`
- Dashboard Bác sĩ — `ccc8e77578684bd98a03a7d4344f70ff`
- Dashboard Dược sĩ — `0d856e6c35484cd2bffc967b23ce8268`
- Dashboard Quản trị — `e1e5cfeb40ce4de49b9be9e922fc3ab2`
- **Dashboard Multi-role (BS + Quản trị)** — `308fffe2883f4c1cad7e7441120158b9` ← Phase B

### 🏥 Clinical workflow (3)
- Tiếp nhận & Đăng ký BN — `8c84c7e3270d4b729d83d1c5d4f60992`
- Lịch hẹn (calendar tuần) — `2e1591c3fd534046932aaf2969fd571b`
- Kho thuốc & Cấp phát — `434d73b9387947328139f56dfad5309f`

### 🩺 EMR — Chi tiết lượt khám (6 tab)
- EMR Tab 1 — Sinh hiệu — `acef698641904014bf33326dcdd90813`
- EMR Tab 2 — Khám LS (S.O.A.P) — `c12bf23adc844cfc8b3d4f632111b501`
- EMR Tab 3 — Chẩn đoán — `fbb61911b4f0496392836546150d2cb9`
- EMR Tab 4 — Kê đơn thuốc — `7e32e3c8c27043dfae12c8409a1acc2a`
- EMR Tab 5 — Cận lâm sàng (CLS) — `b8f84b4034da4ebda2040f1260a01a0a`
- EMR Tab 6 — Tóm tắt & Hoàn tất — `41e3a324001a4c469864e4538ad5539a`

### 💰 Billing (1)
- Thanh toán hoá đơn — `43971b42ba2b4043a89e8aa32261ec16`

### ⚙️ Cấu hình hệ thống (8 section)
- Phòng khám & Chi nhánh — `5f5f1093c7114782aaf063043443395d`
- Vai trò & Phân quyền (RBAC) — `1cb79779d2f145efb13f3d1223f70fc0`
- Ca trực & Giờ làm — `31b1b71d30bd4de88048648db5ab158f`
- Bảng giá dịch vụ — `7c43ae65ba4346fea4685212f222866b`
- BHYT (mức hưởng + DM) — `7ff9fe5bc8d541ecb7844f8965ddbf2b`
- Tích hợp (VSS/HL7/DICOM/SMS) — `1d6fc53966d541c4abb1f3c6949fc20f`
- Audit log — `e7735b5a24944273b631b514409be668`
- Bảo mật & Mã hoá — `b15b501502274b55999bc61ac70f5045`

### 📊 Báo cáo & Thống kê (6 tab)
- Tab Tổng quan — `d86ddd116f614b41b7f6536af01f86dc`
- Tab Tài chính — `e471372c45ce42da827ce03c7f14559c`
- Tab Lâm sàng — `eb2d066147e2472180010db35b66333e`
- Tab Vận hành — `9431a116c63b4045a9798698d0826d41`
- Tab Dược — `6b235c69f8e047c7a5798990e9665c81`
- Tab BHYT — `12334fcf1bec408a80075ea361164ad4`

### ⚠ Duplicate (cần xoá khỏi project Stitch)
- `283a28fda61c4785973ee139f668a00b` — Kho thuốc V2 (bản retry cũ)
- `4da3b971f72b410a8a44f6ed76149b18` — Kho thuốc V3 incomplete (no screenshot)
- `692bb83d5b254461ad1abdef1ae7b0f3` — Dashboard Đa vai trò (auto-retry sinh từ TASK-027 batch 1)
- `a83fc3556c1f438eb070d7708e017902` — Dashboard Đa vai trò v3 (auto-retry sinh từ TASK-027 batch 1)

→ 4 duplicate này là tác phẩm phụ của Stitch khi MCP timeout. Chỉ giữ 1 canonical multi-role (`308fffe2`) và 1 canonical Kho thuốc (`434d73b9`).

---

## 🚀 Cách sử dụng tài liệu này

### Cho **Designer** xem mock:
1. Mở [Stitch project](https://stitch.withgoogle.com/projects/5572301228665717471)
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
