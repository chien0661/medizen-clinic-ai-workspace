# MediZen — Landing Page Design Spec

**Cập nhật**: 2026-05-01 (v1 — concept design + mockup HTML)
**Mục tiêu**: Trang giới thiệu sản phẩm + đăng ký dùng thử cho phòng khám đa khoa VN
**URL dự kiến**: https://medizen.vn (hoặc https://app.medizen.vn/landing)

> ## 📦 Mockup deliverable (TASK-028)
>
> **File**: [landing-mockup.html](landing-mockup.html) — 694 dòng, single-file HTML/CSS/JS self-contained
>
> Render đủ **12 sections** theo spec dưới với:
> - Design tokens MediZen Modern (Indigo `#6366F1` / Slate / Emerald + Plus Jakarta Sans + Inter)
> - Responsive 3 breakpoints (desktop / tablet 1024px / mobile 640px)
> - Vietnamese copy đầy đủ diacritics (vi default, en toggle visual)
> - FAQ accordion, billing toggle (monthly/yearly), scroll-triggered reveal animations
> - Sticky topbar với CTAs, signup form (mock submit)
>
> **Cách dùng**:
> 1. Mở trực tiếp trong browser để xem design.
> 2. Screenshot từng section → paste vào Stitch project mới làm visual reference khi iterate.
> 3. Dùng làm baseline khi FE engineer code phase implementation (subroute `/welcome` trong `clinic-cms-web`).

> Tài liệu này mô tả **thiết kế concept** cho landing page MediZen. Không phải HTML/code — là spec để designer/dev triển khai. Cross-reference với [README.md](README.md) (design system tokens) và [MENU_AND_SCREENS.md](MENU_AND_SCREENS.md) (app screens dùng làm preview).

---

## 1. Tổng quan & nguyên tắc thiết kế

### 1.1 Personality

| Tính cách | Mức độ |
|---|---|
| **Chuyên nghiệp y khoa** | ████████░░ 80% — phải tin cậy được vì khách là phòng khám |
| **Hiện đại / công nghệ** | █████████░ 90% — nhấn mạnh "thoát khỏi giấy bút thời 2010" |
| **Thân thiện / dễ hiểu** | █████████░ 85% — không jargon kỹ thuật, ngôn ngữ đời thường |
| **Sáng tạo / vui mắt** | ███████░░░ 70% — illustration nhẹ nhàng, không quá nghiêm túc |
| **Tập trung action** | █████████░ 90% — mỗi section đều có CTA rõ |

**Tagline đề xuất**: 
> *"Quản lý phòng khám đa khoa — từ tiếp nhận đến cấp thuốc, gói gọn 1 phần mềm"*
> 
> Dưới tagline: *"Xoá sổ giấy bút, không lo mất hồ sơ, kê đơn thấy ngay tồn kho. MediZen giúp 200+ phòng khám VN tiết kiệm 4 giờ làm việc mỗi ngày."*

### 1.2 Design system mở rộng cho landing

Kế thừa Cura Modern (xem [README.md](README.md)) + bổ sung cho marketing:

| Token | App (MediZen Modern) | Landing extension |
|---|---|---|
| **Primary** | Indigo `#6366F1` | + Gradient `linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #6366F1 100%)` cho hero/CTA |
| **Accent** | — | Coral `#FB7185` (highlight pain points) + Mint `#34D399` (highlight wins) |
| **Background** | Slate-50 `#F8FAFC` | + Mesh gradient indigo-violet-pink (subtle 3% opacity) cho hero bg |
| **Heading font** | Plus Jakarta Sans 700 | + Display font 56-72px cho hero h1 |
| **Body font** | Inter 400/500 | + Inter 18-20px body landing (cao hơn app 16px) |
| **Spacing** | 24px gutter | + 96-128px section padding (rộng rãi marketing) |
| **Roundness** | 12px cards | + 24px feature cards · 16px screenshots · 9999px CTA |
| **Shadows** | Soft ambient indigo-tint | + Glow shadow `0 20px 60px rgba(99,102,241,0.25)` cho hero CTA + screenshots |

### 1.3 Visual elements khác biệt

- **Mesh gradient backgrounds** ở hero, problem section, final CTA
- **Floating UI screenshots** (Stitch screens xoay nhẹ 3-5°) thay vì static
- **Animated illustrations** SVG đơn giản (không phải video nặng)
- **Pulse / hover effects** trên CTA + feature card
- **Scroll-triggered animations** (fade-up, parallax shift) — không quá lố
- **Dark mode support** (toggle ở footer)

---

## 2. Cấu trúc trang (12 sections)

```
┌──────────────────────────────────────────────┐
│ §0  Sticky topbar + nav                       │ ← always visible
├──────────────────────────────────────────────┤
│ §1  HERO — headline + subhead + CTA + mock   │ ← above fold
├──────────────────────────────────────────────┤
│ §2  Social proof bar — logo phòng khám        │
├──────────────────────────────────────────────┤
│ §3  PROBLEM — 6 pain points truyền thống     │ ← "tại sao bạn cần"
├──────────────────────────────────────────────┤
│ §4  SOLUTION — 6 feature highlight            │ ← "MediZen giải quyết"
├──────────────────────────────────────────────┤
│ §5  COMPARISON table — Truyền thống vs MediZen│
├──────────────────────────────────────────────┤
│ §6  WORKFLOW animation — 1 ngày phòng khám   │ ← interactive
├──────────────────────────────────────────────┤
│ §7  USE CASES — 3 personas (chủ PK / BS / NV)│
├──────────────────────────────────────────────┤
│ §8  PRICING — 3 tier (Starter / Pro / Ent.)  │
├──────────────────────────────────────────────┤
│ §9  TESTIMONIALS — 3 quote cards              │
├──────────────────────────────────────────────┤
│ §10 FAQ — 8 câu hỏi accordion                 │
├──────────────────────────────────────────────┤
│ §11 FINAL CTA — gradient bg + signup form     │ ← conversion
├──────────────────────────────────────────────┤
│ §12 FOOTER — links + social + legal           │
└──────────────────────────────────────────────┘
```

Tổng chiều dài ước tính: **5500-6500px** (page-height) trên desktop 1920×1080.

---

## 3. §0 — Sticky topbar + Navigation (64px)

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ [Logo MediZen]   Tính năng  Báo giá  Khách hàng  Tài liệu      [Đăng nhập] [⚡Dùng thử]│
└────────────────────────────────────────────────────────────────────────────────────┘
   gradient                                                          secondary  primary CTA
```

| Vùng | Mô tả |
|---|---|
| **Logo (left)** | "MediZen" Plus Jakarta Sans 700, 24px, gradient text indigo→violet. Click → scroll to top. |
| **Nav links (center)** | "Tính năng" (anchor §4), "Báo giá" (§8), "Khách hàng" (§9), "Tài liệu" (link external docs). Hover underline emerald. |
| **CTA (right)** | "Đăng nhập" ghost button + "⚡ Dùng thử miễn phí" gradient button (44px height, pill shape) |
| **Behavior** | Khi scroll qua hero (~600px) → topbar thêm shadow + bg `#FFFFFF/95` blur 12px (glassmorphism) |
| **Mobile** | Hamburger menu < 768px, drawer slide từ phải |

---

## 4. §1 — HERO Section (90vh, ~900px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Background: mesh gradient indigo→violet→pink subtle 3% + floating particles    │
│                                                                                  │
│  ┌─────────────────────────────┐  ┌──────────────────────────────────┐         │
│  │ Chip: ⚡ MỚI: BHYT bật/tắt   │  │                                  │         │
│  │      cho PK tự trả          │  │                                  │         │
│  │                              │  │                                  │         │
│  │ Quản lý phòng khám           │  │   [Floating UI screenshot:        │         │
│  │ đa khoa — gói gọn            │  │    Dashboard MediZen, xoay        │         │
│  │ trong 1 phần mềm.            │  │    nhẹ 5°, glow shadow]           │         │
│  │                              │  │                                  │         │
│  │ MediZen giúp 200+ phòng      │  │   [Stat overlay floating:        │         │
│  │ khám VN xoá sổ giấy bút,    │  │    "₫85M doanh thu tuần ↑12%"]   │         │
│  │ tiết kiệm 4h/ngày, không   │  │                                  │         │
│  │ lo mất hồ sơ.                │  │   [Notification toast floating:  │         │
│  │                              │  │    "✓ Đã hoàn tất khám LK-..."]  │         │
│  │ ┌────────────────┐           │  │                                  │         │
│  │ │ ⚡ Dùng thử    │           │  │                                  │         │
│  │ │   30 ngày     │           │  │                                  │         │
│  │ │   miễn phí ▶  │           │  │                                  │         │
│  │ └────────────────┘           │  │                                  │         │
│  │ [Xem demo 2 phút →]          │  │                                  │         │
│  │                              │  │                                  │         │
│  │ ✓ Không cần thẻ tín dụng    │  │                                  │         │
│  │ ✓ Hỗ trợ setup miễn phí    │  │                                  │         │
│  │ ✓ Hủy bất cứ lúc nào        │  │                                  │         │
│  └─────────────────────────────┘  └──────────────────────────────────┘         │
│         50% width                            50% width                          │
│                                                                                  │
│         [↓ Cuộn để khám phá]                                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Specs

| Element | Giá trị |
|---|---|
| **Height** | 90vh (~900px desktop) — không full 100vh để hint scroll |
| **Background** | Mesh gradient SVG (indigo `#6366F1` → violet `#8B5CF6` → pink `#EC4899`) opacity 3-5% + 12 floating particle dots animation slow drift |
| **H1 typography** | Plus Jakarta Sans 700, 64px desktop / 40px mobile, letter-spacing -0.03em, line-height 1.1, gradient text indigo→violet |
| **Subhead** | Inter 400, 20px, slate-600, max-width 480px |
| **Primary CTA** | Gradient indigo→violet, 56px height, pill shape (28px radius), white text 18px semibold, glow shadow `0 20px 60px rgba(99,102,241,0.4)`, hover scale 1.03 + shadow tăng |
| **Secondary CTA** | "Xem demo 2 phút →" ghost text, slate-700, hover indigo, mở modal video YouTube |
| **Trust signals** | 3 dòng "✓ ..." emerald check, 14px slate-600 |
| **Screenshot mockup** | Stitch screen `e1e5cfeb40ce4de49b9be9e922fc3ab2` (Dashboard Quản trị) export PNG, xoay 5° clockwise, perspective transform, glow shadow indigo |
| **Floating overlays** | 2-3 small UI snippets (KPI card "₫85.4M", notification toast "✓ Hoàn tất", chip "BS. An đang khám") — float với `translateY` animation 6s loop |
| **Chip "MỚI"** | Chip emerald-100 bg + emerald-700 text, "⚡ MỚI: BHYT bật/tắt..." link tới blog post |

### Annotation

> **Tại sao gradient hero?** Phòng khám VN đang quen với UI flat đơn điệu của các phần mềm cũ (ezClinic, Medisoft). Gradient + glow tạo cảm giác "thế hệ mới", tách biệt với competitors. Nhưng giữ subtle (5% opacity) — không lòe loẹt.
> 
> **Tại sao screenshot xoay 5°?** Floating screenshot góc xiên nhẹ là pattern Stripe / Linear / Vercel — gợi cảm giác "sản phẩm thật, đang chạy". Static thẳng góc cảm giác mockup chết.

---

## 5. §2 — Social Proof Bar (120px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ─────────────────────────────────────────────────────────────────────────────   │
│      Được tin dùng bởi 200+ phòng khám đa khoa trên toàn quốc                   │
│                                                                                  │
│  [Logo PK 1] [Logo PK 2] [Logo PK 3] [Logo PK 4] [Logo PK 5] [Logo PK 6] →     │ ← carousel slow auto-scroll
│                                                                                  │
│ ─────────────────────────────────────────────────────────────────────────────   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

| Element | Giá trị |
|---|---|
| **Caption** | Inter 14px slate-500 letter-spacing 0.05em uppercase |
| **Logos** | 6-8 logo phòng khám partner, grayscale, opacity 60%, hover full color |
| **Animation** | Auto-scroll horizontal infinite loop 30s, pause on hover |
| **Mobile** | Static grid 2×3 |

> **Annotation**: Social proof càng sớm trên page càng tốt cho conversion (Cialdini). Đặt ngay sau hero, trước khi user "hoài nghi".

---

## 6. §3 — PROBLEM Section: 6 nỗi đau truyền thống (~700px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│         Quản lý phòng khám bằng giấy bút                                        │
│              gặp 6 vấn đề lớn                                                    │
│                                                                                  │
│  Bạn có thấy mình trong những tình huống này?                                   │
│                                                                                  │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                        │
│  │ 🗂                │ │ ⏱                │ │ 💊                │                        │
│  │ Mất hồ sơ BN  │ │ Mất 2h/ngày  │ │ Kê đơn không  │                        │
│  │ khi đổi nhân   │ │ cho hoá đơn   │ │ biết tồn kho  │                        │
│  │ viên hoặc cháy│ │ tay viết      │ │ → bán chỗ hết │                        │
│  │ phòng         │ │               │ │ thuốc         │                        │
│  │               │ │               │ │               │                        │
│  │ → 70% PK gặp  │ │ → 4h thừa     │ │ → 15% đơn  │                        │
│  │   ít nhất 1   │ │   mỗi tuần    │ │   bán hụt     │                        │
│  │   lần         │ │               │ │               │                        │
│  └───────────────┘ └───────────────┘ └───────────────┘                        │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐                        │
│  │ 🛡             │ │ 📊                │ │ 🤝                │                        │
│  │ BHYT cấu hình│ │ Không có báo  │ │ NV kiêm        │                        │
│  │ rối, sai mức  │ │ cáo doanh thu │ │ nhiều việc    │                        │
│  │ → BHXH từ    │ │ → quyết định  │ │ → dẫm chân    │                        │
│  │   chối       │ │   theo cảm    │ │   nhau         │                        │
│  │               │ │   tính        │ │               │                        │
│  │ → 222 đơn từ │ │               │ │ → 30% lỗi     │                        │
│  │   chối/tháng  │ │               │ │   giao tiếp   │                        │
│  └───────────────┘ └───────────────┘ └───────────────┘                        │
│                                                                                  │
│  Nghe quen không? Bạn không cô đơn — 85% PK đa khoa nhỏ ở VN                   │
│  cũng đang vật lộn với những vấn đề này.                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6 pain points chi tiết

| # | Icon | Vấn đề | Stat | Ảnh hưởng |
|---|---|---|---|---|
| 1 | 🗂 | Mất hồ sơ BN khi đổi NV / cháy / mất sổ | 70% PK gặp ít nhất 1 lần | Mất uy tín · BN mất lịch sử khám |
| 2 | ⏱ | Mất 2h/ngày cho hoá đơn tay + cộng dồn cuối ngày | 4h thừa/tuần / NV | Lễ tân quá tải · sai số |
| 3 | 💊 | Kê đơn không biết tồn kho → BS kê thuốc đã hết, BN đến quầy mới biết | 15% đơn bán hụt | BN bực · BS phải sửa đơn |
| 4 | 🛡 | BHYT cấu hình rối, sai mức hưởng → BHXH từ chối | ~222 đơn từ chối/tháng cho PK trung | Mất doanh thu · audit phức tạp |
| 5 | 📊 | Không có báo cáo thật → chủ PK quyết định theo cảm tính | Không có data | Tăng trưởng chậm · không scale được |
| 6 | 🤝 | NV kiêm nhiều việc nhưng phần mềm cũ chỉ cho 1 role/user → phải tạo tài khoản giả | 30% lỗi giao tiếp | Người làm cũng mệt, người quản lý cũng đau đầu |

### Specs

| Element | Giá trị |
|---|---|
| **Layout** | Grid 3 cột × 2 hàng, gap 32px, max-width 1200px |
| **Card** | White bg, border 1px slate-200, radius 16px, padding 32px, hover lift -4px |
| **Icon** | 48px, color coral `#FB7185` (highlight nỗi đau) |
| **H3 title** | Plus Jakarta Sans 600, 20px slate-900 |
| **Stat highlight** | Coral chip "→ 70%..." nhỏ ở dưới |
| **Animation** | Stagger fade-up khi scroll vào view, delay 100ms mỗi card |
| **Background** | Linear gradient slate-50 → white (bottom) — visual transition |

> **Annotation**: Các nỗi đau phải **cụ thể**, không generic. "Mất hồ sơ" generic; "70% PK gặp ít nhất 1 lần" cụ thể. Số liệu nên kèm nguồn (tooltip ⓘ link tới whitepaper / khảo sát).

---

## 7. §4 — SOLUTION Section: 6 tính năng nổi bật (~900px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│         MediZen giải quyết tất cả những điều đó                                 │
│                                                                                  │
│  Phần mềm thiết kế bởi người làm y tế VN, hiểu đặc thù phòng khám đa khoa nhỏ.│
│                                                                                  │
│  ╔══════════════════╗  ┌──────────────────────────────┐                      │
│  ║ 🩺                  ║  │                              │                      │
│  ║ Khám bệnh số     ║  │  [Screenshot EMR Tab Kê đơn  │                      │
│  ║ 1-stop            ║  │   với stock chip 320 viên]   │                      │
│  ║                    ║  │                              │                      │
│  ║ Sinh hiệu →      ║  │  [Annotation arrow:         │                      │
│  ║ Khám LS →        ║  │   "Real-time stock — không   │                      │
│  ║ Chẩn đoán →      ║  │    còn cảnh kê đơn xong       │                      │
│  ║ Kê đơn (thấy     ║  │    BN không lấy được thuốc"]  │                      │
│  ║ tồn kho!) →      ║  │                              │                      │
│  ║ CLS →            ║  │                              │                      │
│  ║ Tóm tắt          ║  │                              │                      │
│  ║                    ║  │                              │                      │
│  ║ → 6 tab gọn       ║  │                              │                      │
│  ║   1 màn hình      ║  │                              │                      │
│  ╚══════════════════╝  └──────────────────────────────┘                      │
│       40% width                  60% width — alternating each row              │
│                                                                                  │
│  ┌──────────────────────────────┐  ╔══════════════════╗                      │
│  │  [Screenshot Multi-role      │  ║ 👥                  ║                      │
│  │   Dashboard với 2 cột BS+QT] │  ║ 1 user            ║                      │
│  │                              │  ║ kiêm nhiều role   ║                      │
│  │  [Annotation:                │  ║                    ║                      │
│  │   "Bác sĩ kiêm Quản trị?    │  ║ Sidebar gộp tự    ║                      │
│  │    1 sidebar, không cần      │  ║ động — không cần  ║                      │
│  │    chuyển tài khoản"]        │  ║ chuyển vai trò.   ║                      │
│  │                              │  ║                    ║                      │
│  │                              │  ║ → 85% PK đa khoa  ║                      │
│  │                              │  ║   nhỏ cần case này║                      │
│  └──────────────────────────────┘  ╚══════════════════╝                      │
│                                                                                  │
│  ╔══════════════════╗  ┌──────────────────────────────┐                      │
│  ║ 🛡                  ║  │  [Screenshot Cấu hình →     │                      │
│  ║ BHYT bật/tắt     ║  │   Phòng khám với toggle BHYT]│                      │
│  ║ 1 click           ║  │                              │                      │
│  ║                    ║  │  [Annotation:                │                      │
│  ║ PK tự trả?        ║  │   "Tắt BHYT → ẩn 11 vùng UI │                      │
│  ║ Tắt — toàn bộ UI ║  │    không cần. Chỉ tập trung  │                      │
│  ║ BHYT ẩn.         ║  │    vào dịch vụ tự trả."]    │                      │
│  ║ Sau này có HD?    ║  │                              │                      │
│  ║ Bật — UI tự       ║  │                              │                      │
│  ║ hiện trở lại.    ║  │                              │                      │
│  ╚══════════════════╝  └──────────────────────────────┘                      │
│                                                                                  │
│  + 3 features còn lại (multi-clinic, cmd-K search, báo cáo realtime, ...)      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6 features highlighted

| # | Icon | Feature | Pain solved | Screenshot Stitch ID |
|---|---|---|---|---|
| 1 | 🩺 | **EMR 6 tab gọn 1 màn** — Sinh hiệu / Khám LS / Chẩn đoán / Kê đơn (thấy tồn kho real-time) / CLS / Tóm tắt | #3 (kê đơn không biết tồn kho) | `7e32e3c8` (Tab Kê đơn) |
| 2 | 👥 | **Multi-role merge sidebar** — 1 user kiêm BS + Quản trị, không cần chuyển tài khoản | #6 (NV kiêm việc) | `308fffe2` (Multi-role Dashboard) |
| 3 | 🛡 | **BHYT bật/tắt** — PK tự trả tắt 1 click, ẩn 11 vùng UI BHYT | #4 (BHYT rối) | `5f5f1093` (Cấu hình PK) |
| 4 | 🏥 | **1 tài khoản, nhiều phòng khám** — Bác sĩ thường khám 2-3 chỗ, MediZen cho login 1 lần, switch nhanh | (gross efficiency) | `e8ec8790` (Dashboard) + future clinic switcher |
| 5 | ⌘K | **Tìm kiếm nhanh Ctrl+K** — Bệnh nhân, thuốc, tính năng — gõ và Enter, không cần chuột | (gross efficiency) | future Cmd+K palette mock |
| 6 | 📊 | **Báo cáo realtime 6 tab** — Tài chính, Lâm sàng, Vận hành, Dược, BHYT — tự cập nhật 24/7 | #5 (không có báo cáo) | `e471372c` (Báo cáo Tài chính) |

### Specs

| Element | Giá trị |
|---|---|
| **Layout** | Alternating 2-column rows (text trái / image phải / text phải / image trái...) |
| **Image cards** | Stitch screenshot real export, bo radius 16px, glow shadow, decorative blob behind |
| **Annotation arrows** | SVG arrow indigo, hand-drawn style, dẫn từ feature tới UI element cụ thể |
| **Text cards** | Border-left 4px indigo, padding 32px, h2 + body + bullet stat |
| **Background** | White (clean) — contrast với problem section's slate |
| **Animation** | Mỗi row fade-up khi scroll vào · screenshot có hover tilt 3D nhẹ |

> **Annotation**: Pattern alternating text/image là cổ điển nhưng hiệu quả. Mỗi feature kể 1 mini-story: vấn đề → giải pháp → screenshot bằng chứng.

---

## 8. §5 — COMPARISON Table: Truyền thống vs MediZen (~600px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                  Cách bạn đang làm vs Cách MediZen làm                          │
│                                                                                  │
│  ┌─────────────────────────────┬───────────────────────────────────┐          │
│  │                              │ ❌ Truyền thống      │ ✓ MediZen │          │
│  │                              │ (giấy bút / Excel) │             │          │
│  ├─────────────────────────────┼─────────────────────┼───────────┤          │
│  │ Lưu hồ sơ BN                 │ Sổ giấy + Excel     │ Cloud +    │          │
│  │                              │ (mất là mất hết)    │ backup auto│          │
│  ├─────────────────────────────┼─────────────────────┼───────────┤          │
│  │ Tìm BN cũ                   │ 5-10 phút lật sổ     │ <1s gõ tên │          │
│  ├─────────────────────────────┼─────────────────────┼───────────┤          │
│  │ Kê đơn biết tồn kho?        │ Không — phải hỏi DS  │ Có — chip  │          │
│  │                              │                     │ stock chip │          │
│  ├─────────────────────────────┼─────────────────────┼───────────┤          │
│  │ Báo cáo doanh thu            │ Cộng tay cuối tháng │ Realtime   │          │
│  │                              │ (3-5h)             │ tự cập nhật│          │
│  ├─────────────────────────────┼─────────────────────┼───────────┤          │
│  │ BHYT phù hợp PK tự trả?     │ Phải tự lờ đi      │ Toggle 1   │          │
│  │                              │ những trường BHYT  │ click ẩn   │          │
│  ├─────────────────────────────┼─────────────────────┼───────────┤          │
│  │ NV kiêm 2-3 vai trò          │ Phải tạo nhiều     │ 1 account  │          │
│  │                              │ tài khoản, đăng    │ multi-role │          │
│  │                              │ xuất / đăng nhập   │ sidebar gộp│          │
│  ├─────────────────────────────┼─────────────────────┼───────────┤          │
│  │ Tích hợp BHXH (VSS)         │ Manual nhập web    │ Auto sync  │          │
│  │                              │ BHXH mỗi ngày      │ mỗi giờ    │          │
│  ├─────────────────────────────┼─────────────────────┼───────────┤          │
│  │ Audit trail (truy vết)      │ Không có            │ 7 năm log  │          │
│  ├─────────────────────────────┼─────────────────────┼───────────┤          │
│  │ Hỗ trợ làm việc offline      │ Có (giấy)          │ Có (Tauri  │          │
│  │                              │                     │ SQLite)    │          │
│  ├─────────────────────────────┼─────────────────────┼───────────┤          │
│  │ Chi phí hàng tháng           │ ~5M VNĐ in giấy +  │ Từ 1.5M    │          │
│  │                              │ phí nhân sự cộng   │ VNĐ        │          │
│  │                              │ sổ                  │            │          │
│  └─────────────────────────────┴─────────────────────┴───────────┘          │
│                                                                                  │
│        Tiết kiệm trung bình ₫3.5M/tháng cho phòng khám 5-10 nhân sự            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Specs

| Element | Giá trị |
|---|---|
| **Layout** | Centered table max-width 960px |
| **Header row** | Sticky on scroll, indigo bg, white text, 56px height |
| **Cell traditional** | Coral-50 bg, slate-700 text, ❌ icon prefix |
| **Cell MediZen** | Mint-50 bg, slate-900 text, ✓ icon prefix emerald |
| **Hover row** | Highlight slate-50 |
| **Bottom callout** | Centered text 24px slate-700, "Tiết kiệm trung bình ₫3.5M/tháng" |

> **Annotation**: Comparison table là format sales-friendly nhất, dễ scan. Quan trọng: KHÔNG bash competitor có tên (chỉ "truyền thống" / "giấy bút") — tránh kiện cáo + giữ thái độ chuyên nghiệp.

---

## 9. §6 — WORKFLOW Animation: 1 ngày phòng khám (~700px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│              1 ngày làm việc với MediZen — bấm để xem                           │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │                                                                        │    │
│  │  [● ━━━━━━━━━━━━━━ ] 30% → 09:30 BN check-in                           │    │
│  │                                                                        │    │
│  │  [Animation panel — scrubber controls + autoplay]                     │    │
│  │  Step 1: Lễ tân search BN cũ (gõ "ha vy") → result <1s                │    │
│  │  Step 2: Click "Tạo lượt khám" → BN vào queue                         │    │
│  │  Step 3: ĐD đo sinh hiệu → push sang BS                              │    │
│  │  Step 4: BS khám 6 tab (highlight Tab Kê đơn với stock chip)          │    │
│  │  Step 5: BS hoàn tất → đẩy đơn sang DS + hoá đơn sang Lễ tân          │    │
│  │  Step 6: DS phát thuốc · Lễ tân thu tiền                             │    │
│  │  Step 7: BN ra về + auto SMS nhắc tái khám                           │    │
│  │                                                                        │    │
│  │  [Step indicator: ① ② ③ ❹ ⑤ ⑥ ⑦ — số 4 đang highlight]              │    │
│  │  [Pause | ▶ Play | ⏩ Speed 1x/2x]                                    │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  Tổng thời gian: ~22 phút từ check-in đến BN ra về                             │
│  (so với 45-60 phút với phương pháp truyền thống)                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Specs

| Element | Giá trị |
|---|---|
| **Container** | Centered max-width 1100px, white bg, border 1px slate-200, radius 24px, padding 48px |
| **Animation type** | Lottie hoặc CSS keyframe — không video heavy. 7 steps, mỗi step 8-12s |
| **Step indicator** | Pill-shape progress với 7 dots, active dot indigo + scale 1.2 |
| **Controls** | Pause/Play, speed 1x/2x, scrubber drag |
| **Behavior** | Autoplay khi scroll vào view 50%, pause khi scroll ra |
| **Mobile** | Static screenshots stacked (animation tốn data) |

> **Annotation**: Animation phải kể được câu chuyện end-to-end mà text không thể. Highlight "stock chip" và "đẩy đơn DS+hoá đơn" — 2 USP unique. Cuối có timing "22 phút vs 45-60 phút" — số cụ thể bán hàng.

---

## 10. §7 — USE CASES: 3 personas (~600px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                      MediZen dành cho ai?                                        │
│                                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                         │
│  │ 👨‍⚕                │  │ 🏥                │  │ 👩‍💼                │                         │
│  │              │  │              │  │              │                         │
│  │ Bác sĩ chủ  │  │ Quản lý     │  │ Nhân viên   │                         │
│  │ phòng khám   │  │ phòng khám  │  │ y tế         │                         │
│  │              │  │              │  │              │                         │
│  │ "Tôi vừa    │  │ "Tôi cần    │  │ "Mỗi ngày    │                         │
│  │ khám bệnh,   │  │ thấy số liệu│  │ tôi phải    │                         │
│  │ vừa quản    │  │ thật để ra  │  │ làm 3 việc:  │                         │
│  │ lý PK,       │  │ quyết định." │  │ tiếp nhận,  │                         │
│  │ không có     │  │              │  │ thanh toán,  │                         │
│  │ thời gian   │  │              │  │ tư vấn..."   │                         │
│  │ học cái       │  │              │  │              │                         │
│  │ phức tạp."  │  │              │  │              │                         │
│  │              │  │              │  │              │                         │
│  │ MediZen:    │  │ MediZen:    │  │ MediZen:    │                         │
│  │ • EMR 6 tab │  │ • 6 tab BC  │  │ • 1 user     │                         │
│  │   gọn        │  │   realtime   │  │   nhiều role │                         │
│  │ • Multi-role│  │ • Audit log  │  │ • Cmd+K     │                         │
│  │   sidebar    │  │   7 năm      │  │   search     │                         │
│  │ • 1 click   │  │ • Multi-PK   │  │ • Auto      │                         │
│  │   hoàn tất   │  │   chuỗi      │  │   chuyển     │                         │
│  │   khám       │  │              │  │   khâu       │                         │
│  └──────────────┘  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Specs

| Element | Giá trị |
|---|---|
| **Layout** | 3 column equal width, gap 32px |
| **Card** | White bg, border 1px slate-200, radius 24px, padding 40px |
| **Persona icon** | 64px emoji or illustration, indigo gradient circle bg |
| **Quote** | Italic, slate-600, 18px, line-height 1.6 |
| **Bullet list** | 3-4 bullet với checkmark emerald |
| **Hover** | Lift -8px + shadow tăng + border indigo |

---

## 11. §8 — PRICING (~700px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                 Báo giá đơn giản, không ràng buộc                               │
│                                                                                  │
│  Hủy bất cứ lúc nào · Không cần thẻ tín dụng · Hỗ trợ setup miễn phí           │
│                                                                                  │
│       Toggle: [Tháng] [● Năm — tiết kiệm 20%]                                   │
│                                                                                  │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────┐                       │
│  │ Starter       │  │  ⭐ Pro          │  │ Enterprise   │                       │
│  │              │  │   PHỔ BIẾN       │  │              │                       │
│  │ 1.5M /tháng │  │   3.5M /tháng    │  │ Liên hệ      │                       │
│  │ ₫18M /năm   │  │   ₫42M /năm     │  │              │                       │
│  │              │  │                  │  │              │                       │
│  │ Cho PK nhỏ   │  │ Cho PK đa khoa  │  │ Cho chuỗi PK │                       │
│  │ 1-5 NV       │  │ 5-20 NV         │  │ 20+ NV       │                       │
│  │              │  │                  │  │              │                       │
│  │ ✓ 5 user     │  │ ✓ 20 user       │  │ ✓ Unlimited  │                       │
│  │ ✓ 500 BN/th  │  │ ✓ Unlimited BN  │  │ ✓ Unlimited  │                       │
│  │ ✓ EMR 6 tab │  │ ✓ EMR 6 tab     │  │ ✓ EMR 6 tab │                       │
│  │ ✓ 1 chi      │  │ ✓ 3 chi nhánh  │  │ ✓ Multi-     │                       │
│  │   nhánh      │  │ ✓ BHYT        │  │   chuỗi      │                       │
│  │ — BHYT      │  │ ✓ HL7/DICOM   │  │ ✓ On-prem    │                       │
│  │ — Tích hợp │  │ ✓ Báo cáo full │  │ ✓ Dedicated  │                       │
│  │   ngoài      │  │ ✓ API public   │  │   support    │                       │
│  │              │  │                  │  │ ✓ SLA 99.9%  │                       │
│  │ [Bắt đầu]   │  │ [Dùng thử ⚡]   │  │ [Liên hệ]   │                       │
│  └──────────────┘  └─────────────────┘  └──────────────┘                       │
│                          ↑ scale 1.05                                            │
│                                                                                  │
│  Giảm 30% cho PK đăng ký trong tháng 5/2026 — Mã: KICKOFF30                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Specs

| Element | Giá trị |
|---|---|
| **Toggle Tháng/Năm** | Pill toggle indigo, default "Năm" với chip "tiết kiệm 20%" emerald |
| **Pro card highlight** | Scale 1.05, border 2px indigo, shadow indigo glow, badge "⭐ PHỔ BIẾN" trên top |
| **Price** | Plus Jakarta Sans 700, 48px, indigo gradient text |
| **CTA** | Pro = primary indigo, Starter/Enterprise = ghost outline |
| **Promo banner** | Bottom centered, emerald-50 bg, 16px copy, button "Áp dụng" |

> **Annotation**: 3-tier với middle highlighted là "decoy effect" pricing — đẩy user về Pro. Toggle Năm/Tháng default "Năm" giúp tăng LTV. Promo code tạo urgency.

---

## 12. §9 — TESTIMONIALS (~500px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│           Khách hàng nói gì về MediZen                                          │
│                                                                                  │
│  ┌──────────────────────────┐  ┌──────────────────────────┐                   │
│  │ "Trước khi dùng MediZen, │  │ "Tôi từng dùng 3 phần    │                   │
│  │ tôi mất 2h mỗi sáng để   │  │ mềm khác nhau. MediZen   │                   │
│  │ cộng sổ. Giờ chỉ cần    │  │ là phần mềm đầu tiên     │                   │
│  │ liếc dashboard 10 giây." │  │ hiểu được phòng khám    │                   │
│  │                          │  │ đa khoa nhỏ ở VN."       │                   │
│  │ — BS. Nguyễn Văn Hoàng   │  │ — DS. Trần Thị Mai       │                   │
│  │   Chủ PK Hồng Đức        │  │   Quản lý CN Đa khoa Lan │                   │
│  │   ⭐⭐⭐⭐⭐                │  │   ⭐⭐⭐⭐⭐                │                   │
│  └──────────────────────────┘  └──────────────────────────┘                   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────┐                      │
│  │ "Setup chỉ mất 1 buổi. Team support nhiệt tình,      │                     │
│  │ video hướng dẫn đầy đủ. Không cần BS nào học IT."    │                     │
│  │ — Lễ tân Lan, PK Sài Gòn Plaza  ⭐⭐⭐⭐⭐                │                     │
│  └──────────────────────────────────────────────────────┘                      │
│                                                                                  │
│  Đánh giá trung bình ⭐⭐⭐⭐⭐ 4.8/5 từ 287 phòng khám                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Specs

| Element | Giá trị |
|---|---|
| **Layout** | Masonry-like 2 cards trên + 1 card lớn dưới |
| **Card** | White bg, border 1px slate-200, radius 24px, padding 32px |
| **Quote mark** | SVG decorative quote 64px indigo-100 ở top-left card |
| **Avatar** | 48px circle với name + role |
| **Rating** | 5 stars amber, inline với role |
| **Aggregate stat** | Center bottom, "⭐⭐⭐⭐⭐ 4.8/5 từ 287 phòng khám" 24px |

> **Annotation**: 3 testimonial từ 3 personas khác nhau (BS / DS / Lễ tân) — show MediZen phục vụ cả team, không chỉ chủ PK.

---

## 13. §10 — FAQ (~500px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                     Câu hỏi thường gặp                                          │
│                                                                                  │
│  ▸ MediZen có hỗ trợ kết nối BHXH (VSS) không?                                  │
│  ▸ Tôi có thể chuyển dữ liệu từ phần mềm cũ sang MediZen?                      │
│  ▸ Phòng khám của tôi không nhận BHYT, có dùng được không?                     │
│  ▸ Setup mất bao lâu?                                                            │
│  ▾ Phần mềm chạy offline khi mất mạng được không?                               │
│      Có. MediZen có Tauri SQLite mirror lưu BN gần nhất + lượt khám            │
│      đang dở. Khi mất mạng, bạn vẫn xem được hồ sơ + nhập note. Khi             │
│      kết nối lại, hệ thống auto sync (last-write-wins). Hợp lý cho tình         │
│      huống ở vùng cao hoặc mạng không ổn.                                        │
│  ▸ Bảo mật dữ liệu như thế nào?                                                  │
│  ▸ Tôi có chuỗi 3 phòng khám, MediZen có hỗ trợ?                               │
│  ▸ Hủy gói dùng thử có mất phí không?                                            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 8 FAQ chính

1. **MediZen có hỗ trợ BHXH (VSS) không?** → "Có, gói Pro trở lên. Auto sync mỗi giờ. Tab BHYT trong báo cáo + module BHYT trong cấu hình."
2. **Chuyển dữ liệu từ phần mềm cũ?** → "Có. Hỗ trợ import CSV cho Patient/Service/Medicine. Team support có thể migrate giúp ezClinic, Medisoft."
3. **PK không nhận BHYT?** → "OK luôn. Dùng feature flag BHYT bật/tắt — tắt là toàn bộ UI BHYT ẩn."
4. **Setup mất bao lâu?** → "Trung bình 1 ngày. Wizard 5 bước. Team support call hỗ trợ remote."
5. **Offline khi mất mạng?** → (xem trên)
6. **Bảo mật?** → "TLS 1.3, AES-256 at-rest, audit log immutable 7 năm, tuân thủ Nghị định 13/2023."
7. **Chuỗi nhiều PK?** → "Có. Gói Enterprise. 1 account login → switch giữa các PK."
8. **Hủy gói dùng thử?** → "Không mất phí. Không cần thẻ tín dụng để dùng thử."

### Specs

| Element | Giá trị |
|---|---|
| **Accordion** | Mỗi câu một row, click → expand. Max 1 mở cùng lúc (auto close khác) |
| **Icon** | ▸ slate-400 closed, ▾ indigo open |
| **Content** | Inter 16px slate-700, line-height 1.7 |
| **Animation** | Smooth height transition 200ms ease |

---

## 14. §11 — FINAL CTA + Signup form (~600px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Background: gradient indigo→violet→pink full bleed                              │
│                                                                                  │
│              Sẵn sàng xoá sổ giấy bút?                                          │
│                                                                                  │
│       Dùng thử miễn phí 30 ngày. Không cần thẻ tín dụng.                        │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐             │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐    │             │
│  │  │ 👤 Họ và tên *           │  │ 📞 Số điện thoại *      │    │             │
│  │  │ [Nguyễn Văn A      ]    │  │ [0987 xxx xxx       ]   │    │             │
│  │  └─────────────────────────┘  └─────────────────────────┘    │             │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐    │             │
│  │  │ 📧 Email *               │  │ 🏥 Tên phòng khám *      │    │             │
│  │  │ [hoangan@hongduc.vn ]    │  │ [Phòng khám ABC    ]    │    │             │
│  │  └─────────────────────────┘  └─────────────────────────┘    │             │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐    │             │
│  │  │ 📍 Tỉnh/Thành * ▾        │  │ 👥 Số nhân viên ▾        │    │             │
│  │  │ [TP. Hồ Chí Minh]        │  │ [5-10 NV       ]         │    │             │
│  │  └─────────────────────────┘  └─────────────────────────┘    │             │
│  │  ┌──────────────────────────────────────────────────────┐    │             │
│  │  │ 💬 Chuyên khoa chính (multiselect)                    │    │             │
│  │  │ [☑Đa khoa ☑Sản ☐Nhi ☐Da liễu ☐Răng hàm mặt ☐Khác]    │    │             │
│  │  └──────────────────────────────────────────────────────┘    │             │
│  │                                                                │             │
│  │  ☑ Tôi đồng ý với [Điều khoản dịch vụ] và [Chính sách bảo mật]│           │
│  │  ☐ Đăng ký nhận tin tức MediZen (1-2 email/tháng)            │             │
│  │                                                                │             │
│  │  ┌────────────────────────────────────────────────────┐      │             │
│  │  │   ⚡ Bắt đầu dùng thử 30 ngày miễn phí ▶          │      │             │
│  │  └────────────────────────────────────────────────────┘      │             │
│  │                                                                │             │
│  │  Hoặc gọi hotline: 1900-xxx-xxx (8h-21h, 7 ngày/tuần)        │             │
│  └──────────────────────────────────────────────────────────────┘             │
│                                                                                  │
│   Bạn không phải mua. Không cần thẻ. Không lo bị spam.                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Form fields chi tiết

| Field | Type | Required | Validation | Notes |
|---|---|---|---|---|
| Họ và tên | text | ✓ | ≥3 ký tự | autocomplete="name" |
| Số điện thoại | tel | ✓ | VN phone regex (+84 / 0[3-9]) | autoformat 0987 654 321 |
| Email | email | ✓ | RFC 5322 + check disposable domain | autocomplete="email" — gửi link verify |
| Tên phòng khám | text | ✓ | ≥3 ký tự | dùng để generate `clinic_code` ban đầu |
| Tỉnh/Thành | dropdown | ✓ | 63 tỉnh thành VN | autocomplete city |
| Số nhân viên | dropdown | ✓ | 1-5 / 5-10 / 10-20 / 20-50 / 50+ | dùng để gợi ý gói |
| Chuyên khoa | multi-checkbox | optional | — | gợi ý template vital schema sau |
| Đồng ý ToS | checkbox | ✓ | must check | block submit nếu chưa |
| Newsletter | checkbox | optional | — | default unchecked |

### Form behavior

| Behavior | Detail |
|---|---|
| **Real-time validation** | Validate per field on blur (turn red border + error text dưới input) |
| **Submit button state** | Disabled khi form invalid · Loading spinner khi đang submit · Success state "✓ Đã gửi! Kiểm tra email" |
| **Backend** | POST `/api/landing/signup` → tạo `lead` record + gửi email verify + Slack notify sales |
| **Anti-spam** | hCaptcha invisible · honeypot field · rate limit 5/giờ/IP |
| **After submit** | Show success modal "Tuyệt vời! Email đã gửi tới [email]. Click link kích hoạt." + button "Mở Gmail" / "Mở Outlook" |
| **A/B test** | Test variant: form rút gọn (chỉ Email + Phone + Tên PK) vs full form |

### Specs

| Element | Giá trị |
|---|---|
| **Background** | Gradient mesh indigo→violet→pink full opacity, slight grain texture overlay |
| **Container** | Centered max-width 720px, white card bg, border-radius 32px, padding 56px, glow shadow |
| **Heading** | Plus Jakarta Sans 700, 48px white, drop shadow nhẹ |
| **Subhead** | Inter 18px white-90 |
| **Inputs** | 48px height, white bg, border 1px slate-200, radius 12px, focus indigo ring 2px |
| **Submit CTA** | Full-width, gradient indigo→violet, 56px height, pill shape, glow shadow heavy |
| **Trust footer** | "Bạn không phải mua..." 14px white-70 |

> **Annotation**: Form dài 7 fields có thể giảm conversion. A/B test variant ngắn (3 field) vs đầy đủ. Hotline số trực tiếp giúp người không quen submit form.

---

## 15. §12 — Footer (~400px)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Background: Slate-900                                                            │
│                                                                                  │
│ ┌──────────┐ Sản phẩm    Tài nguyên    Công ty    Liên hệ                      │
│ │ Logo     │ Tính năng   Tài liệu       Về chúng    1900-xxx-xxx                │
│ │ MediZen  │ Báo giá     Blog           tôi          hello@medizen.vn            │
│ │ gradient │ So sánh     API docs       Tuyển dụng  [Facebook][YouTube][Zalo]   │
│ └──────────┘ Bảo mật     Status page    Đối tác                                  │
│                                                                                  │
│ "MediZen — Hệ thống quản lý phòng khám đa khoa hàng đầu VN.                    │
│  Sản phẩm bởi công ty TNHH VISSoft, MST: xxx, địa chỉ: xxx."                   │
│                                                                                  │
│ ──────────────────────────────────────────────────────────────────────────      │
│ © 2026 VISSoft · Điều khoản · Bảo mật · Cookie · Sitemap         🌙 Dark mode  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Specs

| Element | Giá trị |
|---|---|
| **Background** | Slate-900 with subtle indigo gradient at top edge |
| **Layout** | 5-column: Logo + 4 link groups |
| **Links** | Inter 14px slate-300 hover white |
| **Social icons** | 32px slate-400 hover indigo |
| **Bottom row** | Slate-500, separated by divider |
| **Dark mode toggle** | Sun/Moon icon, switch theme global |

---

## 16. Animations & Micro-interactions

| Animation | Trigger | Detail | Performance |
|---|---|---|---|
| **Hero CTA pulse** | On mount | Subtle box-shadow pulse 2s loop | CSS only |
| **Hero floating elements** | Always | translateY 6s ease-in-out infinite | CSS keyframe |
| **Scroll fade-up** | IntersectionObserver | Cards fade-up 600ms khi vào view 30% | Framer Motion |
| **Number counter** | Scroll vào §2 | Stat numbers count from 0 → final value 1.5s | Custom JS |
| **Workflow animation** | §6 visible | Lottie 7 steps autoplay, scrubber control | Lottie player |
| **Hover card lift** | Hover feature card | translateY -4px + shadow tăng 200ms | CSS transition |
| **Hover screenshot tilt** | Hover screenshot | rotateX 5° rotateY -5° 3D | CSS transform |
| **Form input focus** | Focus | Border indigo + ring 2px outer glow | CSS focus-visible |
| **Submit success** | API response 200 | Confetti SVG burst + modal slide-up | canvas-confetti |
| **Smooth scroll** | Click anchor link | scroll-behavior: smooth | CSS |

> **Performance budget**: Total JS bundle <200KB gzipped (Framer Motion + Lottie + form). Lighthouse Performance >85. CLS <0.1. LCP <2.5s.

---

## 17. Responsive breakpoints

| Breakpoint | Width | Layout adjust |
|---|---|---|
| **Mobile** | <768px | All sections single column · Hero h1 40px · Form full width · Hamburger menu · Skip workflow animation (static) |
| **Tablet** | 768-1024px | 2-column grids · Hero stack vertical (text top, screenshot bottom) · Topbar visible nav |
| **Desktop** | 1024-1440px | Full 3-column · Hero side-by-side · Padding 96px |
| **Wide** | >1440px | Max-width 1440px content · Padding tăng 128px · Larger hero text 72px |

---

## 18. SEO + Metadata

| Tag | Giá trị |
|---|---|
| **Title** | "MediZen — Phần mềm quản lý phòng khám đa khoa #1 VN" (≤60 ký tự) |
| **Description** | "Quản lý phòng khám từ tiếp nhận đến cấp thuốc. EMR 6 tab, BHYT bật/tắt, multi-role, báo cáo realtime. Dùng thử 30 ngày miễn phí." (≤160 ký tự) |
| **OG image** | 1200×630 dashboard screenshot với logo + tagline |
| **Twitter card** | summary_large_image |
| **Schema.org** | SoftwareApplication + AggregateRating + FAQPage + Organization |
| **Canonical** | `https://medizen.vn/` |
| **Sitemap** | /sitemap.xml với 12 URL chính |
| **Robots** | Allow all · disallow /api · /admin |
| **hreflang** | vi (default) + en |

---

## 19. Image illustrations checklist

Cần thiết kế / tạo các illustration sau (dùng vector SVG, có thể outsource Dribbble / Storyset):

| # | Illustration | Vị trí | Style |
|---|---|---|---|
| 1 | Hero dashboard mockup | §1 hero | Stitch screenshot Stitch ID `e1e5cfeb` xoay 5° + glow |
| 2 | 6 floating UI snippets | §1 hero | Mini cards (KPI / notification / chip) layered |
| 3 | 6 pain icons | §3 problems | Coral 48px outline icons |
| 4 | 6 feature screenshots | §4 solutions | Stitch screen exports với annotation arrows |
| 5 | Workflow steps illustration | §6 | 7-step Lottie animation |
| 6 | 3 persona illustrations | §7 | Storyset-style flat illustration với indigo accent |
| 7 | Pricing tier icons | §8 | Geometric badges |
| 8 | Testimonial avatars | §9 | Real photos hoặc generated avatar (this-person-does-not-exist) |
| 9 | FAQ icon decorative | §10 | Single SVG ? mark |
| 10 | Final CTA mesh gradient | §11 | Procedural mesh gradient SVG |

**Image format**:
- SVG cho icons + illustrations
- WebP cho screenshots (fallback PNG)
- AVIF cho hero image (fallback WebP)
- Lazy load tất cả below-fold

---

## 20. Conversion tracking

Track 6 events qua Google Analytics 4 + Mixpanel:

| Event | Trigger | Property |
|---|---|---|
| `landing_view` | Page load | utm_source, utm_medium, utm_campaign |
| `cta_click` | Click bất kỳ CTA button | location (hero/pricing/final), variant |
| `form_start` | Focus first form field | — |
| `form_submit` | Form submit success | num_fields_filled, plan_inferred |
| `signup_complete` | After email verify | clinic_size, province |
| `demo_video_play` | Click "Xem demo 2 phút" | duration_watched |

**Funnel**:
```
landing_view → cta_click (40%) → form_start (60%) → form_submit (45%) → signup_complete (70%)
                                                                        = ~7.5% end-to-end conversion
```

Target: ≥5% landing→signup_complete cho organic, ≥8% cho paid traffic.

---

## 21. A/B test ideas

Tests đề xuất chạy lần lượt sau v1 launch:

| Test # | Hypothesis | Variant A | Variant B |
|---|---|---|---|
| T1 | Form ngắn convert tốt hơn | Full 7-field form | Mini 3-field (Email + Phone + PK name) |
| T2 | Hotline số đẩy convert | Hotline ở footer | Hotline + chat widget Zalo nổi |
| T3 | Pricing toggle default | "Tháng" default | "Năm" default |
| T4 | Hero CTA copy | "Dùng thử 30 ngày miễn phí" | "Bắt đầu miễn phí ngay" |
| T5 | Social proof số | "200+ phòng khám" | "287 phòng khám đang dùng" (cụ thể hơn) |

---

## 22. Việc cần làm tiếp

| Phase | Việc | Dependency |
|---|---|---|
| **Design v1** | Wireframe Figma 12 sections | This doc |
| **Design v2** | Hi-fi mockup + components | Wireframe approved |
| **Stitch generate** | Sinh screen landing trên Stitch (1 màn full-page) | Hi-fi |
| **Frontend dev** | Implement với Next.js + Tailwind + Framer Motion | Hi-fi handoff |
| **Backend dev** | API `/api/landing/signup` + email verify flow | Frontend skeleton |
| **Content** | Việt hoá tất cả copy + viết blog post launch | Design parallel |
| **Illustration** | Outsource Storyset hoặc tự design SVG | Design parallel |
| **SEO** | Setup GA4 + Mixpanel + Search Console | Pre-launch |
| **Launch** | Soft launch (private link) → public launch + PR | All above |

**Timeline ước tính**: 4-6 tuần từ đây tới public launch.

---

## 23. Inspiration references

Tham khảo các landing đẹp/hiệu quả tương đương:

| Site | Học gì |
|---|---|
| stripe.com | Hero animation + screenshot floating |
| linear.app | Gradient + dark mode + micro-interaction |
| vercel.com | Spacing + typography + product illustration |
| notion.so | Use case section + persona |
| figma.com | Workflow animation + community section |
| bizflyserver.com | Bản local — pricing + FAQ tiếng Việt |

→ MediZen lấy **80% Stripe-Linear style** + **20% local touch** (tiếng Việt + giá VNĐ + hotline + Zalo).

---

**Cross-references**:
- [README.md](README.md) — design system tokens chính
- [MENU_AND_SCREENS.md](MENU_AND_SCREENS.md) — app screens dùng làm preview
- [TAB_MATRIX.md](TAB_MATRIX.md) — chi tiết EMR/Settings/Reports nếu landing cần preview deep
- Stitch project: https://stitch.withgoogle.com/projects/5572301228665717471 — lấy screenshot

**Status**: v1 concept ✓ — sẵn sàng cho Figma wireframe + Stitch generate full-page landing screen.
